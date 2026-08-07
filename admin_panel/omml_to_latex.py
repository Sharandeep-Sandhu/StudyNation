"""Convert Office Math ML (OMML) XML nodes to LaTeX strings.

Used by the Word importer so questions are stored as plain text + $LaTeX$
and rendered with KaTeX (not equation PNGs).
"""
from __future__ import annotations

import re
from xml.etree import ElementTree as ET

MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M = f"{{{MATH_NS}}}"
W = f"{{{W_NS}}}"

# Common unicode → LaTeX
_CHAR_MAP = {
    "α": r"\alpha",
    "β": r"\beta",
    "γ": r"\gamma",
    "δ": r"\delta",
    "ε": r"\varepsilon",
    "ζ": r"\zeta",
    "η": r"\eta",
    "θ": r"\theta",
    "ϑ": r"\vartheta",
    "ι": r"\iota",
    "κ": r"\kappa",
    "λ": r"\lambda",
    "μ": r"\mu",
    "ν": r"\nu",
    "ξ": r"\xi",
    "π": r"\pi",
    "ρ": r"\rho",
    "σ": r"\sigma",
    "τ": r"\tau",
    "υ": r"\upsilon",
    "φ": r"\varphi",
    "ϕ": r"\phi",
    "χ": r"\chi",
    "ψ": r"\psi",
    "ω": r"\omega",
    "Α": r"A",
    "Β": r"B",
    "Γ": r"\Gamma",
    "Δ": r"\Delta",
    "Θ": r"\Theta",
    "Λ": r"\Lambda",
    "Ξ": r"\Xi",
    "Π": r"\Pi",
    "Σ": r"\Sigma",
    "Υ": r"\Upsilon",
    "Φ": r"\Phi",
    "Ψ": r"\Psi",
    "Ω": r"\Omega",
    "∞": r"\infty",
    "∂": r"\partial",
    "∇": r"\nabla",
    "±": r"\pm",
    "∓": r"\mp",
    "×": r"\times",
    "÷": r"\div",
    "·": r"\cdot",
    "∗": r"\ast",
    "∘": r"\circ",
    "≤": r"\leq",
    "≥": r"\geq",
    "≠": r"\neq",
    "≈": r"\approx",
    "≡": r"\equiv",
    "∼": r"\sim",
    "∝": r"\propto",
    "∈": r"\in",
    "∉": r"\notin",
    "⊂": r"\subset",
    "⊆": r"\subseteq",
    "∪": r"\cup",
    "∩": r"\cap",
    "∅": r"\emptyset",
    "→": r"\rightarrow",
    "←": r"\leftarrow",
    "↔": r"\leftrightarrow",
    "⇒": r"\Rightarrow",
    "⇐": r"\Leftarrow",
    "⇔": r"\Leftrightarrow",
    "∴": r"\therefore",
    "∵": r"\because",
    "∠": r"\angle",
    "⊥": r"\perp",
    "∥": r"\parallel",
    "°": r"^\circ",
    "′": r"'",
    "″": r"''",
    "√": r"\sqrt{}",
    "∑": r"\sum",
    "∏": r"\prod",
    "∫": r"\int",
    "∬": r"\iint",
    "∮": r"\oint",
    "…": r"\ldots",
    "⋯": r"\cdots",
    "−": r"-",
    "–": r"-",
    "—": r"-",
    "≤": r"\leq",
    "≥": r"\geq",
    "≪": r"\ll",
    "≫": r"\gg",
    "⊕": r"\oplus",
    "⊗": r"\otimes",
    "∧": r"\wedge",
    "∨": r"\vee",
    "¬": r"\neg",
    "∀": r"\forall",
    "∃": r"\exists",
    "ℝ": r"\mathbb{R}",
    "ℕ": r"\mathbb{N}",
    "ℤ": r"\mathbb{Z}",
    "ℚ": r"\mathbb{Q}",
    "ℂ": r"\mathbb{C}",
}

_ACCENT = {
    "dot": r"\dot",
    "ddot": r"\ddot",
    "hat": r"\hat",
    "check": r"\check",
    "tilde": r"\tilde",
    "bar": r"\bar",
    "vec": r"\vec",
    "acute": r"\acute",
    "grave": r"\grave",
    "breve": r"\breve",
}


def _local(tag: str) -> str:
    if not tag:
        return ""
    if tag.startswith("{"):
        return tag.rsplit("}", 1)[-1]
    return tag


def _text_of(elem) -> str:
    if elem is None:
        return ""
    parts = []
    for t in elem.iter(f"{M}t"):
        if t.text:
            parts.append(t.text)
    # also w:t sometimes
    for t in elem.iter(f"{W}t"):
        if t.text:
            parts.append(t.text)
    return "".join(parts)


def _escape_text(s: str) -> str:
    out = []
    for ch in s:
        if ch in _CHAR_MAP:
            out.append(_CHAR_MAP[ch] + " ")
        elif ch in r"\{}$&#^_%~":
            # LaTeX specials
            if ch == "\\":
                out.append(r"\backslash ")
            elif ch == "{":
                out.append(r"\{")
            elif ch == "}":
                out.append(r"\}")
            elif ch == "$":
                out.append(r"\$")
            elif ch == "&":
                out.append(r"\&")
            elif ch == "#":
                out.append(r"\#")
            elif ch == "%":
                out.append(r"\%")
            elif ch == "_":
                out.append(r"\_")
            elif ch == "^":
                out.append(r"\hat{}")
            elif ch == "~":
                out.append(r"\sim ")
            else:
                out.append(ch)
        else:
            out.append(ch)
    return "".join(out)


def _brace(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return "{}"
    # already single token
    if re.fullmatch(r"\\[a-zA-Z]+|\\[^\s]|[A-Za-z0-9]", s):
        return s
    return "{" + s + "}"


def omml_node_to_latex(node) -> str:
    """Convert an m:oMath / m:oMathPara element (or ElementTree node) to LaTeX."""
    if node is None:
        return ""
    # Accept lxml-ish or ElementTree; work with tag + children
    tag = _local(getattr(node, "tag", "") or "")
    if tag == "oMathPara":
        # paragraph of math — join children
        bits = []
        for child in list(node):
            if _local(child.tag) in ("oMath", "oMathPara"):
                bits.append(omml_node_to_latex(child))
            else:
                bits.append(_convert_element(child))
        return " ".join(b for b in bits if b).strip()
    if tag == "oMath":
        return _convert_children(node).strip()
    return _convert_element(node).strip()


def _convert_children(elem) -> str:
    parts = []
    for child in list(elem):
        parts.append(_convert_element(child))
    return "".join(parts)


def _first(elem, *names):
    for name in names:
        found = elem.find(f"{M}{name}")
        if found is not None:
            return found
    return None


def _convert_element(elem) -> str:
    if elem is None:
        return ""
    tag = _local(elem.tag)

    if tag in ("r",):  # run
        return _convert_run(elem)
    if tag == "t":
        return _escape_text(elem.text or "")
    if tag == "sSub":
        base = _convert_element(_first(elem, "e"))
        sub = _convert_element(_first(elem, "sub"))
        return f"{_brace(base)}_{_brace(sub)}"
    if tag == "sSup":
        base = _convert_element(_first(elem, "e"))
        sup = _convert_element(_first(elem, "sup"))
        return f"{_brace(base)}^{_brace(sup)}"
    if tag == "sSubSup":
        base = _convert_element(_first(elem, "e"))
        sub = _convert_element(_first(elem, "sub"))
        sup = _convert_element(_first(elem, "sup"))
        return f"{_brace(base)}_{_brace(sub)}^{_brace(sup)}"
    if tag == "f":  # fraction
        num = _convert_element(_first(elem, "num"))
        den = _convert_element(_first(elem, "den"))
        return rf"\frac{{{num.strip()}}}{{{den.strip()}}}"
    if tag == "rad":  # radical
        deg = _first(elem, "deg")
        e = _convert_element(_first(elem, "e"))
        if deg is not None and _convert_element(deg).strip():
            d = _convert_element(deg).strip()
            return rf"\sqrt[{d}]{{{e.strip()}}}"
        return rf"\sqrt{{{e.strip()}}}"
    if tag == "nary":
        return _convert_nary(elem)
    if tag == "d":  # delimiter
        return _convert_delim(elem)
    if tag == "acc":
        return _convert_acc(elem)
    if tag == "bar":
        e = _convert_element(_first(elem, "e"))
        return rf"\overline{{{e.strip()}}}"
    if tag == "box" or tag == "borderBox":
        return _convert_element(_first(elem, "e"))
    if tag == "groupChr":
        e = _convert_element(_first(elem, "e"))
        return e
    if tag == "func":
        name = _convert_element(_first(elem, "fName")).strip() or "f"
        e = _convert_element(_first(elem, "e"))
        # fName often is \sin etc already as text
        name_l = name.replace(" ", "")
        if not name_l.startswith("\\") and re.fullmatch(r"[a-zA-Z]+", name_l):
            name_l = "\\" + name_l
        return f"{name_l}{_brace(e)}"
    if tag == "limLow":
        e = _convert_element(_first(elem, "e"))
        lim = _convert_element(_first(elem, "lim"))
        return rf"\underset{{{lim.strip()}}}{{{e.strip()}}}"
    if tag == "limUpp":
        e = _convert_element(_first(elem, "e"))
        lim = _convert_element(_first(elem, "lim"))
        return rf"\overset{{{lim.strip()}}}{{{e.strip()}}}"
    if tag == "m":  # matrix
        return _convert_matrix(elem)
    if tag == "eqArr":
        rows = []
        for e in elem.findall(f"{M}e"):
            rows.append(_convert_element(e).strip())
        body = r" \\ ".join(rows)
        return r"\begin{aligned}" + body + r"\end{aligned}"
    if tag in ("oMath", "oMathPara"):
        return omml_node_to_latex(elem)
    if tag in ("e", "num", "den", "sub", "sup", "deg", "lim", "fName"):
        return _convert_children(elem)
    if tag in ("ctrlPr", "rPr", "argPr", "sSubPr", "sSupPr", "fPr", "radPr",
               "naryPr", "dPr", "accPr", "barPr", "funcPr", "mPr", "mrPr",
               "eqArrPr", "limLowPr", "limUppPr", "groupChrPr", "boxPr"):
        return ""
    # Generic: walk children / text
    if list(elem):
        return _convert_children(elem)
    return _escape_text(elem.text or "")


def _convert_run(elem) -> str:
    # m:t inside run
    texts = []
    for t in elem.findall(f"{M}t"):
        texts.append(_escape_text(t.text or ""))
    if texts:
        return "".join(texts)
    return _convert_children(elem)


def _convert_nary(elem) -> str:
    pr = _first(elem, "naryPr")
    char = "∫"
    if pr is not None:
        ch = pr.find(f"{M}chr")
        if ch is not None:
            char = ch.get(f"{M}val") or ch.get("val") or char
    op_map = {
        "∫": r"\int",
        "∬": r"\iint",
        "∭": r"\iiint",
        "∮": r"\oint",
        "∑": r"\sum",
        "∏": r"\prod",
        "⋃": r"\bigcup",
        "⋂": r"\bigcap",
    }
    op = op_map.get(char, r"\int")
    sub = _convert_element(_first(elem, "sub")).strip()
    sup = _convert_element(_first(elem, "sup")).strip()
    e = _convert_element(_first(elem, "e")).strip()
    out = op
    if sub:
        out += f"_{_brace(sub)}"
    if sup:
        out += f"^{_brace(sup)}"
    if e:
        out += f" {_brace(e)}" if not e.startswith("\\") else f" {e}"
    return out


def _convert_delim(elem) -> str:
    pr = _first(elem, "dPr")
    left, right = "(", ")"
    if pr is not None:
        beg = pr.find(f"{M}begChr")
        end = pr.find(f"{M}endChr")
        if beg is not None:
            left = beg.get(f"{M}val") or beg.get("val") or left
        if end is not None:
            right = end.get(f"{M}val") or end.get("val") or right
    body = _convert_element(_first(elem, "e")).strip()
    # multi e children
    es = elem.findall(f"{M}e")
    if len(es) > 1:
        body = r" \\ ".join(_convert_element(e).strip() for e in es)

    def _delim(c: str, side: str) -> str:
        if c in ("(", ")", "[", "]", "|", ".", ""):
            return c if c else "."
        if c == "{":
            return r"\{"
        if c == "}":
            return r"\}"
        if c in ("‖", "∥"):
            return r"\|"
        if c == "⟨":
            return r"\langle"
        if c == "⟩":
            return r"\rangle"
        if c == "⌊":
            return r"\lfloor"
        if c == "⌋":
            return r"\rfloor"
        if c == "⌈":
            return r"\lceil"
        if c == "⌉":
            return r"\rceil"
        return c

    l = _delim(left, "l")
    r = _delim(right, "r")
    return rf"\left{l} {body} \right{r}"


def _convert_acc(elem) -> str:
    pr = _first(elem, "accPr")
    chr_val = "̂"
    if pr is not None:
        ch = pr.find(f"{M}chr")
        if ch is not None:
            chr_val = ch.get(f"{M}val") or ch.get("val") or chr_val
    e = _convert_element(_first(elem, "e")).strip()
    acc_map = {
        "̂": r"\hat",
        "^": r"\hat",
        "̃": r"\tilde",
        "~": r"\tilde",
        "̄": r"\bar",
        "̅": r"\overline",
        "̇": r"\dot",
        "̈": r"\ddot",
        "⃗": r"\vec",
        "→": r"\vec",
    }
    cmd = acc_map.get(chr_val, r"\hat")
    if cmd == r"\overline":
        return rf"\overline{{{e}}}"
    return rf"{cmd}{{{e}}}"


def _convert_matrix(elem) -> str:
    rows = []
    for mr in elem.findall(f"{M}mr"):
        cells = [_convert_element(e).strip() for e in mr.findall(f"{M}e")]
        rows.append(" & ".join(cells))
    body = r" \\ ".join(rows)
    return r"\begin{matrix}" + body + r"\end{matrix}"


def clean_latex(latex: str) -> str:
    """Tidy pandoc / converter output for KaTeX."""
    if not latex:
        return ""
    s = latex.strip()
    # Strip outer \( \) or $ $ if pandoc wrapped
    s = re.sub(r"^\\\((.*)\\\)$", r"\1", s, flags=re.S)
    s = re.sub(r"^\\\[(.*)\\\]$", r"\1", s, flags=re.S)
    s = re.sub(r"^\$\$(.*)\$\$$", r"\1", s, flags=re.S)
    s = re.sub(r"^\$(.*)\$$", r"\1", s, flags=re.S)
    # pandoc artifacts
    s = s.replace(r"\passthrough{\lstinline!", "")
    s = re.sub(r"\\protect\s*", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    # trailing punctuation outside math sometimes sticks
    return s


def wrap_inline_math(latex: str) -> str:
    latex = clean_latex(latex)
    if not latex:
        return ""
    # Avoid nested $
    latex = latex.replace("$", r"\$")
    return f"${latex}$"
