"""Equation PNG markup for display.

PNGs are pre-normalized so the main glyph line is ~28px (see docx parser
enhance). Display uses height:auto so simple and multi-line formulas keep
the same character size — only total box height grows for fractions.
"""
from __future__ import annotations

import re

_EQ_IMG_RE = re.compile(r"<img\b(?P<attrs>[^>]*?)>", re.IGNORECASE)
_SRC_RE = re.compile(r'\bsrc\s*=\s*"([^"]+)"', re.IGNORECASE)
_CLASS_RE = re.compile(r'\bclass\s*=\s*"([^"]*)"', re.IGNORECASE)
_EQ_WRAP_RE = re.compile(
    r'<span\b[^>]*\beq-math\b[^>]*>\s*(?P<img><img\b[^>]*>)\s*</span>',
    re.IGNORECASE,
)

# height:auto — natural size after glyph-normalized PNGs
_EQ_STYLE = (
    "height:auto!important;"
    "max-height:48px!important;"
    "width:auto!important;"
    "max-width:min(96vw,720px)!important;"
    "display:inline-block!important;"
    "vertical-align:middle!important;"
    "object-fit:contain!important;"
    "margin:2px 4px!important;"
    "padding:0!important;"
    "border:0!important;"
    "background:transparent!important;"
)


def _is_equation_img(attrs: str, src: str) -> bool:
    if "question_equations" in (src or ""):
        return True
    classes = ""
    m = _CLASS_RE.search(attrs or "")
    if m:
        classes = m.group(1).lower()
    return any(c in classes for c in ("eq-inline", "eq-math-img", "eq-math"))


def _img_tag(src: str) -> str:
    return (
        f'<img src="{src}" alt="" class="eq-math-img" '
        f'style="{_EQ_STYLE}" decoding="async" loading="lazy" />'
    )


def wrap_equation_images(html: str | None, *, large: bool | None = None) -> str:
    if not html or "<img" not in html.lower():
        return html or ""
    text = str(html)
    text = _EQ_WRAP_RE.sub(lambda m: m.group("img"), text)

    def repl(match: re.Match) -> str:
        attrs = match.group("attrs") or ""
        src_m = _SRC_RE.search(attrs)
        src = src_m.group(1) if src_m else ""
        if not src or not _is_equation_img(attrs, src):
            return match.group(0)
        return _img_tag(src)

    return _EQ_IMG_RE.sub(repl, text)


def equation_img_html(url: str, *, large: bool = False) -> str:
    return _img_tag((url or "").strip())
