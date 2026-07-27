"""
Word (.doc / .docx) question-bank importer.

Parses past-paper style Word documents shaped like:

    1. Question text ...
    (a) option text   (b) option text
    (c) option text   (d) option text
    ...
    Answer Sheet
    1  2  3  ...
    b  c  c  ...

Equations in these banks are almost always embedded as:
  - WMF/EMF OLE previews (MS Equation Editor / MathType), and/or
  - DrawingML images (a:blip), and/or
  - Native Word OMML math (m:oMath)

This importer keeps equations **as-is** by:
  1. Walking each paragraph in document order
  2. Inserting position markers where equations/images sit
  3. Converting WMF/EMF → PNG (LibreOffice if available, else Windows
     System.Drawing — so Windows servers work without LibreOffice)
  4. Splicing inline HTML <img class="eq-inline"> tags into question text
     and options so they render on the site without manual re-typing
  5. Also converting OMML → LaTeX ($...$) via pandoc when available
"""
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor

from django import forms

# ---------------------------------------------------------------------------
# Some older LibreOffice/OpenOffice.org builds write .docx packages using
# pre-standard "purl.oclc.org/ooxml/..." namespace URIs. Rewrite them so
# python-docx can open the file.
# ---------------------------------------------------------------------------
_OOXML_NS_SPECIAL_CASES = [
    (
        "http://purl.oclc.org/ooxml/officeDocument/relationships/extendedProperties",
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties",
    ),
    (
        "http://purl.oclc.org/ooxml/officeDocument/extendedProperties",
        "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties",
    ),
]
_OOXML_NS_GENERAL_RE = re.compile(r"http://purl\.oclc\.org/ooxml/([A-Za-z][\w-]*)/")
_OOXML_NS_GENERAL_REPL = r"http://schemas.openxmlformats.org/\1/2006/"


def _rewrite_ooxml_namespace_text(text):
    for old, new in _OOXML_NS_SPECIAL_CASES:
        text = text.replace(old, new)
    return _OOXML_NS_GENERAL_RE.sub(_OOXML_NS_GENERAL_REPL, text)


def normalize_ooxml_namespaces(src_path, dst_path):
    """
    Copies src_path (a .docx package) to dst_path, rewriting old
    'purl.oclc.org/ooxml' namespaces into standard OOXML ones.
    """
    changed = False
    with zipfile.ZipFile(src_path, "r") as zin:
        names = zin.namelist()
        with zipfile.ZipFile(dst_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for name in names:
                data = zin.read(name)
                if name.endswith(".xml") or name.endswith(".rels"):
                    try:
                        text = data.decode("utf-8")
                    except UnicodeDecodeError:
                        zout.writestr(name, data)
                        continue
                    if "purl.oclc.org/ooxml" in text:
                        data = _rewrite_ooxml_namespace_text(text).encode("utf-8")
                        changed = True
                zout.writestr(name, data)
    return changed


try:
    import docx
    from docx.oxml.ns import qn
except ImportError:  # pragma: no cover
    docx = None
    qn = None

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

OPTION_RE = re.compile(r"\(([a-eA-E])\)\s*")
QUESTION_NUM_RE = re.compile(r"^\s*(\d+)[\.\)]\s+")
ANSWER_HEADING_RE = re.compile(r"answer\s*(sheet|key)", re.IGNORECASE)

VML_NS = "urn:schemas-microsoft-com:vml"
VML_IMAGEDATA_TAG = f"{{{VML_NS}}}imagedata"

MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
OMATH_TAG = f"{{{MATH_NS}}}oMath"
OMATHPARA_TAG = f"{{{MATH_NS}}}oMathPara"

# Placeholders (control chars — never collide with real document text)
_OMATH_PLACEHOLDER_RE = re.compile("\x02OMATH(omatheq\\d+)\x02")
_IMG_PLACEHOLDER_RE = re.compile("\x02IMGRID(rId[^\\x02]+)\x02")

_BATCH_MARKER_RE = re.compile(
    r"OMATHMARKERSTART(omatheq\d+)OMATHMARKEREND\s*\\[\(\[](.*?)\\[\)\]]", re.DOTALL
)

# Inline equation image HTML — size controlled by global CSS (.eq-inline)
# so formulas match surrounding body text (no giant padded chips).
_EQ_IMG_HTML = (
    '<img src="{url}" alt="equation" class="eq-inline" loading="lazy" '
    'decoding="async" />'
)

# Readable size band after conversion — keep close to body text (~16–20px).
# Slightly larger source pixels stay sharp when CSS scales to ~1.15–1.7em.
_EQ_MIN_HEIGHT_PX = 36
_EQ_MIN_WIDTH_PX = 48
_EQ_TARGET_HEIGHT_PX = 56    # ~ matches 1.4em at 16px root
_EQ_MAX_HEIGHT_PX = 96
_EQ_MAX_WIDTH_PX = 480
_CONVERT_BATCH_SIZE = 150
_ENHANCE_WORKERS = min(8, (os.cpu_count() or 4))


# ---------------------------------------------------------------------------
# Paragraph walking — preserve equation order inside the sentence
# ---------------------------------------------------------------------------

def _find_omath_nodes(paragraph_elem):
    return [c for c in paragraph_elem if c.tag in (OMATHPARA_TAG, OMATH_TAG)]


def _rids_from_element(elem):
    """
    Collect image relationship ids from DrawingML blips and VML imagedata.
    Prefer DrawingML (a:blip) when both exist on the same node — they are
    almost always the same equation graphic stored twice.
    """
    if elem is None:
        return []
    blip_rids = []
    for blip in elem.findall(".//" + qn("a:blip")):
        rid = blip.get(qn("r:embed")) or blip.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
        )
        if rid and rid not in blip_rids:
            blip_rids.append(rid)
    if blip_rids:
        return blip_rids
    vml_rids = []
    for imgdata in elem.findall(".//" + VML_IMAGEDATA_TAG):
        rid = imgdata.get(qn("r:id")) or imgdata.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        )
        if rid and rid not in vml_rids:
            vml_rids.append(rid)
    return vml_rids


def _run_text_with_image_placeholders(run_elem):
    """
    Walk a <w:r> in order so text and embedded equation images keep their
    relative positions (e.g. 'The last digit in [EQ] is').
    """
    parts = []
    for child in run_elem:
        tag = child.tag
        if tag == qn("w:t"):
            parts.append(child.text or "")
        elif tag == qn("w:tab"):
            parts.append("\t")
        elif tag == qn("w:br"):
            parts.append(" ")
        elif tag in (qn("w:drawing"), qn("w:pict"), qn("w:object")):
            for rid in _rids_from_element(child):
                parts.append(f"\x02IMGRID{rid}\x02")
        else:
            # Nested content (e.g. smart tags) — still look for images/text
            for t in child.findall(".//" + qn("w:t")):
                parts.append(t.text or "")
            for rid in _rids_from_element(child):
                parts.append(f"\x02IMGRID{rid}\x02")
    return "".join(parts)


def _paragraph_text_with_placeholders(paragraph, omath_registry):
    """
    Like paragraph.text, but:
      - OMML equations → \x02OMATH{key}\x02
      - DrawingML / VML / OLE equation images → \x02IMGRID{rId}\x02
    so later passes can turn them into LaTeX or inline <img> tags.
    """
    parts = []
    seen_img = set()
    for child in paragraph._p:
        tag = child.tag
        if tag in (OMATH_TAG, OMATHPARA_TAG):
            key = f"omatheq{len(omath_registry)}"
            omath_registry.append((key, copy.deepcopy(child)))
            parts.append(f"\x02OMATH{key}\x02")
        elif tag == qn("w:r"):
            chunk = _run_text_with_image_placeholders(child)
            parts.append(chunk)
            for rid in _IMG_PLACEHOLDER_RE.findall(chunk):
                seen_img.add(rid)
        elif tag == qn("w:hyperlink"):
            for r in child.findall(qn("w:r")):
                parts.append(_run_text_with_image_placeholders(r))
        else:
            # Fallback: any images sitting outside runs
            for rid in _rids_from_element(child):
                if rid not in seen_img:
                    parts.append(f"\x02IMGRID{rid}\x02")
                    seen_img.add(rid)
    text = "".join(parts)
    # Identical back-to-back markers (same rId twice) → keep one
    text = _dedupe_adjacent_img_placeholders(text)
    return text


def _dedupe_adjacent_img_placeholders(text):
    """Collapse consecutive identical IMGRID markers (VML + Drawing pair)."""
    while True:
        new = re.sub(r"(\x02IMGRID(rId[^\x02]+)\x02)\1+", r"\1", text)
        if new == text:
            break
        text = new
    return text


# ---------------------------------------------------------------------------
# OMML → LaTeX (pandoc)
# ---------------------------------------------------------------------------

def _render_omath_batch_to_latex(omath_registry, work_dir):
    latex_by_key = {}
    if not omath_registry or not shutil.which("pandoc"):
        # Fallback: extract plain math text from m:t so something remains
        for key, node in omath_registry:
            texts = []
            for t in node.findall(f".//{{{MATH_NS}}}t"):
                if t.text:
                    texts.append(t.text)
            joined = "".join(texts).strip()
            if joined:
                latex_by_key[key] = joined
        return latex_by_key

    doc = docx.Document()
    for p in list(doc.paragraphs):
        p._p.getparent().remove(p._p)
    for key, node in omath_registry:
        doc.add_paragraph(f"OMATHMARKERSTART{key}OMATHMARKEREND")
        eq_p = doc.add_paragraph()
        eq_p._p.append(copy.deepcopy(node))

    batch_path = os.path.join(work_dir, "omath_batch.docx")
    doc.save(batch_path)

    try:
        result = subprocess.run(
            ["pandoc", batch_path, "-t", "latex"],
            capture_output=True, text=True, timeout=60, check=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        # plain-text fallback
        for key, node in omath_registry:
            texts = []
            for t in node.findall(f".//{{{MATH_NS}}}t"):
                if t.text:
                    texts.append(t.text)
            joined = "".join(texts).strip()
            if joined:
                latex_by_key[key] = joined
        return latex_by_key

    for key, latex in _BATCH_MARKER_RE.findall(result.stdout):
        latex = latex.strip()
        if latex:
            latex_by_key[key] = latex
    return latex_by_key


def _substitute_placeholders(text, latex_by_key, rid_to_url):
    """Replace OMATH + IMGRID markers with LaTeX / inline equation images."""
    if not text:
        return text

    def omath_repl(m):
        latex = latex_by_key.get(m.group(1))
        if latex:
            # Already looks like LaTeX command / has specials
            return f"${latex}$"
        return ""

    def img_repl(m):
        rid = m.group(1)
        url = rid_to_url.get(rid)
        if url:
            return _EQ_IMG_HTML.format(url=url)
        return ""

    text = _OMATH_PLACEHOLDER_RE.sub(omath_repl, text)
    text = _IMG_PLACEHOLDER_RE.sub(img_repl, text)
    # Clean leftover control chars / messy whitespace around images
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\s+(?=<img)", " ", text)
    text = re.sub(r"(?<=>)\s+", " ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Document / image conversion helpers
# ---------------------------------------------------------------------------

def _has_numbering(paragraph):
    pPr = paragraph._p.pPr
    return pPr is not None and pPr.numPr is not None


def _soffice_available():
    return shutil.which("soffice") is not None or shutil.which("soffice.exe") is not None


def _soffice_bin():
    return shutil.which("soffice") or shutil.which("soffice.exe")


def _soffice_convert_document(src_path, target_ext, outdir):
    """Convert a whole document (e.g. legacy .doc -> .docx) via headless LibreOffice."""
    soffice = _soffice_bin()
    if not soffice:
        return None
    try:
        subprocess.run(
            [soffice, "--headless", "--norestore", "--convert-to", target_ext,
             "--outdir", outdir, src_path],
            check=True, timeout=120, capture_output=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None
    base = os.path.splitext(os.path.basename(src_path))[0]
    out_path = os.path.join(outdir, f"{base}.{target_ext}")
    return out_path if os.path.exists(out_path) else None


def _batch_convert_images_soffice(paths, target_ext, outdir):
    mapping = {}
    soffice = _soffice_bin()
    if not paths or not soffice:
        return mapping
    for i in range(0, len(paths), _CONVERT_BATCH_SIZE):
        chunk = paths[i:i + _CONVERT_BATCH_SIZE]
        try:
            subprocess.run(
                [soffice, "--headless", "--norestore", "--convert-to", target_ext,
                 "--outdir", outdir] + chunk,
                check=True, timeout=300, capture_output=True,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            continue
        for p in chunk:
            base = os.path.splitext(os.path.basename(p))[0]
            out_path = os.path.join(outdir, f"{base}.{target_ext}")
            if os.path.exists(out_path):
                mapping[p] = out_path
    return mapping


def _batch_convert_images_windows_gdi(paths, outdir):
    """
    Fast batch WMF/EMF → PNG via a **single** PowerShell process.

    Previous approach launched PowerShell dozens of times and rasterized
    page-sized bitmaps at 3–4× — that made Word uploads hang for minutes.
    """
    mapping = {}
    if not paths or sys.platform != "win32":
        return mapping

    pairs = []
    for src in paths:
        base = os.path.splitext(os.path.basename(src))[0]
        dst = os.path.join(outdir, f"{base}.png")
        if os.path.exists(dst) and os.path.getsize(dst) > 0:
            mapping[src] = dst
            continue
        pairs.append((src, dst))
    if not pairs:
        return mapping

    list_path = os.path.join(outdir, "_wmf_jobs.tsv")
    script_path = os.path.join(outdir, "_wmf_convert.ps1")
    with open(list_path, "w", encoding="utf-8") as fh:
        for src, dst in pairs:
            fh.write(f"{src}\t{dst}\n")

    script = r'''
Add-Type -AssemblyName System.Drawing
$ErrorActionPreference = 'Continue'
$listPath = $args[0]
$ok = 0
Get-Content -LiteralPath $listPath -Encoding UTF8 | ForEach-Object {
  if (-not $_) { return }
  $parts = $_.Split("`t")
  if ($parts.Count -lt 2) { return }
  $src = $parts[0]
  $dst = $parts[1]
  try {
    $srcImg = [System.Drawing.Image]::FromFile($src)
    $nw = [Math]::Max(1, $srcImg.Width)
    $nh = [Math]::Max(1, $srcImg.Height)
    $scale = 2
    if ($nw -le 80 -and $nh -le 80) { $scale = 4 }
    elseif ($nw -gt 350 -or $nh -gt 350) { $scale = 1 }
    $w = [Math]::Max(1, [int]($nw * $scale))
    $h = [Math]::Max(1, [int]($nh * $scale))
    $maxSide = 900
    if ($w -gt $maxSide -or $h -gt $maxSide) {
      $r = $maxSide / [Math]::Max($w, $h)
      $w = [Math]::Max(1, [int]($w * $r))
      $h = [Math]::Max(1, [int]($h * $r))
    }
    $bmp = New-Object System.Drawing.Bitmap $w, $h
    $bmp.SetResolution(144, 144)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.Clear([System.Drawing.Color]::White)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.DrawImage($srcImg, 0, 0, $w, $h)
    $bmp.Save($dst, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bmp.Dispose(); $srcImg.Dispose()
    $ok++
  } catch { }
}
Write-Output $ok
'''
    with open(script_path, "w", encoding="utf-8") as fh:
        fh.write(script)

    try:
        timeout = min(480, max(60, 30 + int(len(pairs) * 0.15)))
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                script_path,
                list_path,
            ],
            check=False,
            timeout=timeout,
            capture_output=True,
            text=True,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    for src, dst in pairs:
        if os.path.exists(dst) and os.path.getsize(dst) > 0:
            mapping[src] = dst
    return mapping


def _batch_convert_images(paths, target_ext, outdir):
    """Convert many WMF/EMF images to PNG (deduped paths, single PS batch)."""
    if not paths:
        return {}
    unique = list(dict.fromkeys(paths))
    mapping = _batch_convert_images_soffice(unique, target_ext, outdir)
    remaining = [p for p in unique if p not in mapping]
    if remaining and target_ext.lower() == "png":
        mapping.update(_batch_convert_images_windows_gdi(remaining, outdir))
    return mapping


def _enhance_equation_pngs_parallel(paths):
    """Crop/resize many PNGs in parallel."""
    paths = [p for p in dict.fromkeys(paths) if p and os.path.exists(p)]
    if not paths:
        return
    if len(paths) == 1:
        _enhance_equation_png(paths[0])
        return
    workers = min(_ENHANCE_WORKERS, len(paths))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(_enhance_equation_png, paths))


def _enhance_equation_png(path, padding=12):
    """
    Crop whitespace and fit equation PNGs into a readable size band.

    WMF rasters are either tiny (~40px) or huge page canvases. We:
      1. Flatten onto white
      2. Threshold-crop near-white margins (more reliable than RGB diff)
      3. Scale so height sits around ~110px (clear next to body text)
      4. Light contrast/sharpen so thin strokes stay visible
    """
    try:
        from PIL import Image, ImageEnhance, ImageOps, ImageFilter
    except ImportError:
        return
    try:
        im = Image.open(path)
        if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
            bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
            im = Image.alpha_composite(bg, im.convert("RGBA")).convert("RGB")
        else:
            im = im.convert("RGB")

        # Threshold crop: keep anything darker than near-white
        gray = im.convert("L")
        mask = gray.point(lambda p: 255 if p < 248 else 0)
        # Dilate slightly so thin strokes aren't clipped
        mask = mask.filter(ImageFilter.MaxFilter(3))
        bbox = mask.getbbox()
        if bbox:
            left, top, right, bottom = bbox
            left = max(0, left - padding)
            top = max(0, top - padding)
            right = min(im.width, right + padding)
            bottom = min(im.height, bottom + padding)
            im = im.crop((left, top, right, bottom))

        w, h = im.size
        if w < 2 or h < 2:
            return

        # Fit into readable band (not microscopic, not a full page)
        if h < _EQ_MIN_HEIGHT_PX or w < _EQ_MIN_WIDTH_PX:
            scale = max(
                _EQ_TARGET_HEIGHT_PX / max(h, 1),
                _EQ_MIN_WIDTH_PX / max(w, 1),
            )
            scale = min(max(scale, 1.5), 10.0)
            im = im.resize(
                (max(1, int(w * scale)), max(1, int(h * scale))),
                Image.Resampling.LANCZOS,
            )
        else:
            # Downscale oversized canvases while keeping sharpness
            scale = 1.0
            if h > _EQ_TARGET_HEIGHT_PX:
                scale = min(scale, _EQ_TARGET_HEIGHT_PX / h)
            if w * scale > _EQ_MAX_WIDTH_PX:
                scale = min(scale, _EQ_MAX_WIDTH_PX / w)
            if h * scale > _EQ_MAX_HEIGHT_PX:
                scale = min(scale, _EQ_MAX_HEIGHT_PX / h)
            if scale < 0.999:
                im = im.resize(
                    (max(1, int(w * scale)), max(1, int(h * scale))),
                    Image.Resampling.LANCZOS,
                )

        im = ImageEnhance.Contrast(im).enhance(1.25)
        im = ImageEnhance.Sharpness(im).enhance(1.35)
        im = ImageOps.expand(im, border=8, fill=(255, 255, 255))
        im.save(path, format="PNG", optimize=True)
    except Exception:
        pass


def _autocrop_png(path, padding=10):
    """Back-compat name used by the import pipeline."""
    _enhance_equation_png(path, padding=padding)

def _save_image_blob(blob, ext, media_subdir):
    """Save raw image bytes to MEDIA; return public URL."""
    ext = (ext or "png").lstrip(".").lower()
    if ext in ("wmf", "emf"):
        # Should have been converted already — store as-is only as last resort
        pass
    fname = f"{media_subdir}/{uuid.uuid4().hex}.{ext}"
    saved_name = default_storage.save(fname, ContentFile(blob))
    try:
        return default_storage.url(saved_name)
    except Exception:
        return saved_name


_ANSWER_LETTER_RE = re.compile(r"([a-eA-E])")


def _normalize_answer_token(ans: str) -> str:
    """Turn 'c', 'C.', ' c ', 'a,b' into a clean lowercase letter key."""
    if not ans:
        return ""
    ans = ans.strip().lower()
    # multi-select e.g. "a,b" or "a b"
    letters = _ANSWER_LETTER_RE.findall(ans)
    if not letters:
        return ""
    # de-dupe preserve order
    seen = []
    for L in letters:
        if L not in seen:
            seen.append(L)
    return ",".join(seen)


def _fix_answer_number_row(cells):
    """
    Force sequential numbering on answer-sheet number rows.

    Word tables often typo the last cell of a block (e.g. 61–69 then 61
    instead of 70). For a standard 1..10 grid we renumber from the first
    digit so keys line up with the answer row beneath.
    """
    vals = [c.strip() for c in cells]
    digit_idxs = [i for i, v in enumerate(vals) if v.isdigit()]
    if len(digit_idxs) < 2:
        return vals
    start = int(vals[digit_idxs[0]])
    for j, i in enumerate(digit_idxs):
        vals[i] = str(start + j)
    return vals


def _parse_answer_sheet_tables(document):
    """
    Parse classic past-paper Answer Sheet tables:

        1  2  3  … 10
        c  d  c  … b
        11 12 … 20
        d  a  … b
    """
    answers = {}
    for table in document.tables:
        rows = table.rows
        i = 0
        while i + 1 < len(rows):
            raw_nums = [c.text.strip() for c in rows[i].cells]
            if not any(n.isdigit() for n in raw_nums):
                i += 1
                continue
            num_cells = _fix_answer_number_row(raw_nums)
            ans_cells = [c.text.strip() for c in rows[i + 1].cells]
            for num, ans in zip(num_cells, ans_cells):
                if not num.isdigit():
                    continue
                letter = _normalize_answer_token(ans)
                if not letter:
                    continue
                # Do not silently overwrite a different key for the same Q
                if num in answers and answers[num] != letter:
                    # Prefer the first mapping; sequential fix should prevent this
                    continue
                answers[num] = letter
            i += 2
    return answers


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def parse_docx_questions(uploaded_file, media_subdir="question_equations"):
    """
    Parse an uploaded .doc/.docx and return row-dicts with:
      - question_text / option_a..d containing inline equation <img> tags
        and/or $LaTeX$ where OMML conversion succeeded
      - equation_images: list of MEDIA URLs (same images, for review UI)
    """
    if docx is None:
        raise forms.ValidationError(
            "The 'python-docx' package isn't installed on the server. "
            "Run: pip install python-docx"
        )

    work_dir = tempfile.mkdtemp(prefix="docx_import_")
    try:
        src_name = uploaded_file.name
        src_path = os.path.join(work_dir, os.path.basename(src_name))
        with open(src_path, "wb") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        docx_path = src_path
        if src_name.lower().endswith(".doc"):
            converted = _soffice_convert_document(src_path, "docx", work_dir)
            if not converted:
                raise forms.ValidationError(
                    "Couldn't convert this legacy .doc file (LibreOffice "
                    "unavailable or conversion failed). Please open it in "
                    "Word → Save As → .docx and re-upload. "
                    "Tip: your sample files include .docx versions."
                )
            docx_path = converted

        normalized_path = os.path.join(
            work_dir, "normalized_" + os.path.basename(docx_path)
        )
        try:
            normalize_ooxml_namespaces(docx_path, normalized_path)
            docx_path = normalized_path
        except (zipfile.BadZipFile, OSError):
            pass

        try:
            document = docx.Document(docx_path)
        except Exception as first_error:
            renorm_dir = os.path.join(work_dir, "renormalized")
            os.makedirs(renorm_dir, exist_ok=True)
            renormalized = _soffice_convert_document(docx_path, "docx", renorm_dir)
            if renormalized:
                try:
                    document = docx.Document(renormalized)
                    docx_path = renormalized
                except Exception:
                    raise forms.ValidationError(
                        f"Couldn't read this Word file: {first_error}"
                    )
            else:
                raise forms.ValidationError(
                    f"Couldn't read this Word file: {first_error}"
                )

        # ---- 1. Collect every image part (WMF/EMF/PNG/JPG/…) ----
        # De-dupe by content hash so identical equation blobs convert once.
        image_dir = os.path.join(work_dir, "equations")
        os.makedirs(image_dir, exist_ok=True)

        rid_to_src = {}          # rid → local source path (any format)
        rid_to_ext = {}
        need_convert = []       # unique paths that are wmf/emf
        blob_hash_to_path = {}  # md5 → path (dedupe)

        for rel_id, rel in document.part.rels.items():
            if "image" not in rel.reltype:
                continue
            try:
                target = rel.target_part
                ext = (target.partname.ext or "").lower().lstrip(".")
                blob = target.blob
            except Exception:
                continue
            if not blob:
                continue
            digest = hashlib.md5(blob).hexdigest()
            if digest in blob_hash_to_path:
                src_img_path = blob_hash_to_path[digest]
            else:
                src_img_path = os.path.join(
                    image_dir, f"{digest}.{ext or 'bin'}"
                )
                with open(src_img_path, "wb") as f:
                    f.write(blob)
                blob_hash_to_path[digest] = src_img_path
                if ext in ("wmf", "emf"):
                    need_convert.append(src_img_path)
            rid_to_src[rel_id] = src_img_path
            rid_to_ext[rel_id] = ext or "bin"

        converted_map = _batch_convert_images(need_convert, "png", image_dir)
        # Parallel crop/resize (major speedup vs sequential PIL)
        _enhance_equation_pngs_parallel(list(converted_map.values()))

        # rid → final local PNG/image path ready to upload
        rid_to_local = {}
        for rid, src in rid_to_src.items():
            if src in converted_map:
                rid_to_local[rid] = converted_map[src]
            elif rid_to_ext.get(rid) in ("png", "jpg", "jpeg", "gif", "webp", "bmp"):
                rid_to_local[rid] = src
            # else: unconverted wmf left out (will skip that marker)

        # ---- 2. Walk paragraphs → questions (with inline placeholders) ----
        questions = []
        current = None
        omath_registry = []

        def start_question(num_hint=None):
            nonlocal current
            current = {
                "question_text": "",
                "options": {},
                "image_rids": [],
                "question_number": num_hint or str(len(questions) + 1),
            }
            questions.append(current)

        for p in document.paragraphs:
            raw_text = _paragraph_text_with_placeholders(p, omath_registry).strip()

            if ANSWER_HEADING_RE.search(
                re.sub(r"\x02(?:OMATH|IMGRID)[^\x02]+\x02", "", raw_text)
            ):
                break

            plain_for_num = _IMG_PLACEHOLDER_RE.sub("", _OMATH_PLACEHOLDER_RE.sub("", raw_text))
            explicit_num = QUESTION_NUM_RE.match(plain_for_num)
            is_new_q = _has_numbering(p) or bool(explicit_num)

            rids_here = _IMG_PLACEHOLDER_RE.findall(raw_text)

            if not raw_text and not rids_here:
                continue

            text = raw_text
            if explicit_num:
                # Strip leading "1." from the plain prefix only
                text = QUESTION_NUM_RE.sub("", text, count=1)

            if is_new_q:
                num_hint = explicit_num.group(1) if explicit_num else None
                start_question(num_hint)
                current["question_text"] = text
                current["image_rids"].extend(rids_here)
                continue

            if current is None:
                continue

            # Option detection on text with placeholders preserved
            plain_opts = text  # OPTION_RE works on the text; placeholders stay in segments
            matches = list(OPTION_RE.finditer(plain_opts))
            if matches:
                for idx, m in enumerate(matches):
                    letter = m.group(1).lower()
                    start = m.end()
                    end = matches[idx + 1].start() if idx + 1 < len(matches) else len(plain_opts)
                    opt_text = plain_opts[start:end].strip(" \t")
                    # Merge if option already started on a previous line
                    if letter in current["options"] and current["options"][letter]:
                        current["options"][letter] = (
                            f"{current['options'][letter]} {opt_text}".strip()
                        )
                    else:
                        current["options"][letter] = opt_text
            elif text:
                current["question_text"] = (
                    f"{current['question_text']} {text}".strip()
                    if current["question_text"]
                    else text
                )
            current["image_rids"].extend(rids_here)

        # ---- 3. Answer Sheet table ----
        answers = _parse_answer_sheet_tables(document)

        # ---- 3b. OMML → LaTeX ----
        latex_by_key = _render_omath_batch_to_latex(omath_registry, work_dir)

        # ---- 4. Upload images & build rid → URL map (used by all questions) ----
        # Same local file (content-hash dedupe) → one MEDIA write, shared URL.
        rid_to_url = {}
        path_to_url = {}
        for rid, local_path in rid_to_local.items():
            if local_path in path_to_url:
                rid_to_url[rid] = path_to_url[local_path]
                continue
            ext = os.path.splitext(local_path)[1].lstrip(".") or "png"
            try:
                with open(local_path, "rb") as fh:
                    blob = fh.read()
                if not blob:
                    continue
                url = _save_image_blob(blob, ext, media_subdir)
                path_to_url[local_path] = url
                rid_to_url[rid] = url
            except OSError:
                continue

        # ---- 5. Assemble output rows with equations inlined ----
        rows_out = []
        for position, q in enumerate(questions, start=1):
            qnum = q["question_number"] or str(position)

            # Unique equation URLs for this question (review UI + equation_images field)
            saved_urls = []
            seen = set()
            for rid in q["image_rids"]:
                url = rid_to_url.get(rid)
                if url and url not in seen:
                    seen.add(url)
                    saved_urls.append(url)
            # Also pick up any rids only present as placeholders in text
            for rid in _IMG_PLACEHOLDER_RE.findall(
                q["question_text"] + " " + " ".join(q["options"].values())
            ):
                url = rid_to_url.get(rid)
                if url and url not in seen:
                    seen.add(url)
                    saved_urls.append(url)

            options = q["options"]
            # Match answer key by question_number; fall back to 1-based position
            answer_letters = answers.get(str(qnum), "") or answers.get(str(position), "")
            answer_letters = _normalize_answer_token(answer_letters)
            is_multi = "," in answer_letters
            if options:
                question_type = "multiple_choice" if is_multi else "single_choice"
            else:
                question_type = "structured"

            q_text = _substitute_placeholders(
                q["question_text"].strip(), latex_by_key, rid_to_url
            )
            # If equation images exist but none made it into the text (edge case),
            # append them so the equation is never dropped.
            if saved_urls and "<img " not in q_text and "$" not in q_text:
                q_text = (
                    q_text
                    + " "
                    + " ".join(_EQ_IMG_HTML.format(url=u) for u in saved_urls)
                ).strip()

            row = {
                "question_text": q_text,
                "question_type": question_type,
                "option_a": _substitute_placeholders(
                    options.get("a", ""), latex_by_key, rid_to_url
                ),
                "option_b": _substitute_placeholders(
                    options.get("b", ""), latex_by_key, rid_to_url
                ),
                "option_c": _substitute_placeholders(
                    options.get("c", ""), latex_by_key, rid_to_url
                ),
                "option_d": _substitute_placeholders(
                    options.get("d", ""), latex_by_key, rid_to_url
                ),
                "correct_answer": answer_letters.upper(),
                "marks": 1,
                "explanation": _substitute_placeholders(
                    f"Option (e): {options['e']}" if "e" in options else "",
                    latex_by_key,
                    rid_to_url,
                ),
                "topic": "",
                "paper_code": "",
                "year": None,
                "season": "",
                "zone": "",
                "question_number": qnum,
                "equation_images": saved_urls,
            }
            rows_out.append(row)

        if not rows_out:
            raise forms.ValidationError(
                "No questions were found in this Word file. Expected numbered "
                "questions (1. …) with options like (a) (b) (c) (d)."
            )

        return rows_out
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
