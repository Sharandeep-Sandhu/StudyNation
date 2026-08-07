"""Sanitize and prepare user chat / question text for KaTeX display.

Problems this solves:
  - Old MathLive inserts left literal ``#0`` / ``#1`` placeholders
  - LaTeX without ``$...$`` delimiters shows as raw code
  - Empty fences / doubled backslashes from broken editors
"""
from __future__ import annotations

import re

from django.utils.html import escape
from django.utils.safestring import mark_safe

# MathLive / broken editor leftovers
_PLACEHOLDER_RE = re.compile(
    r"(?:#\d+|\\placeholder(?:\[[^\]]*\])?\{[^}]*\})",
    re.IGNORECASE,
)
# Empty \left \right pairs left after placeholders were stripped
_EMPTY_FENCE_RE = re.compile(
    r"\\left\s*(\\[{(|.\|]|\\langle|\\lfloor|\\lceil|[\[({|.]?)\s*\\right\s*(\\[})|.\|]|\\rangle|\\rfloor|\\rceil|[\])}|.]?)",
)
_EMPTY_FRAC_RE = re.compile(r"\\frac\{\s*\}\{\s*\}")
_EMPTY_SQRT_RE = re.compile(r"\\sqrt(?:\[[^\]]*\])?\{\s*\}")
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
# Already has math delimiters
_HAS_MATH_DELIM_RE = re.compile(r"\$|\\\(|\\\[|\\begin\{")
# Looks like TeX commands
_HAS_TEX_CMD_RE = re.compile(r"\\[a-zA-Z]+|\\[{}^_]|\\left|\\right")


def sanitize_math_content(text: str | None) -> str:
    """Clean garbage placeholders and ensure LaTeX can be typeset."""
    if not text:
        return ""
    text = str(text).replace("\r\n", "\n").replace("\r", "\n")

    # Remove MathLive-style placeholders (#0, \placeholder{})
    text = _PLACEHOLDER_RE.sub("", text)

    # Collapse empty structures left behind
    text = _EMPTY_FRAC_RE.sub("", text)
    text = _EMPTY_SQRT_RE.sub("", text)
    # Simple empty left/right
    text = re.sub(r"\\left\s*([(\[{|.]|\\[{(|])\s*\\right\s*([)\]}|.]|\\[})|])", "", text)
    text = re.sub(r"\\left\\lfloor\s*\\right\\rfloor", "", text)
    text = re.sub(r"\\left\\lceil\s*\\right\\rceil", "", text)
    text = re.sub(r"\\left\\langle\s*\\right\\rangle", "", text)

    # Tidy braces left empty: {#0} already gone → {}
    text = re.sub(r"\{\s*\}", "", text)
    # Dangling ^ or _ with nothing after
    text = re.sub(r"\^(?!\{|[A-Za-z0-9\\])", "", text)
    text = re.sub(r"_(?!\{|[A-Za-z0-9\\])", "", text)
    text = re.sub(r"_\{\s*\}", "", text)

    text = _MULTI_SPACE_RE.sub(" ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    if not text:
        return ""

    # If there is TeX but no math delimiters, wrap so KaTeX can typeset it.
    if _HAS_TEX_CMD_RE.search(text) and not _HAS_MATH_DELIM_RE.search(text):
        if "\n" in text or "\\\\" in text or "\\begin" in text:
            text = f"$${text}$$"
        else:
            text = f"${text}$"

    return text


def render_chat_math(text: str | None) -> str:
    """HTML-safe string for templates; KaTeX typesets $...$ regions."""
    cleaned = sanitize_math_content(text)
    if not cleaned:
        return ""
    # Escape HTML, keep newlines as <br>
    # Preserve $...$ / $$...$$ for KaTeX auto-render
    safe = escape(cleaned).replace("\n", "<br>\n")
    return mark_safe(safe)
