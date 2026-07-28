"""Allowlist HTML sanitizer for question/blog content (XSS mitigation).

Keeps equation <img> tags and basic formatting; strips scripts/event handlers.
Uses only the Python standard library (no extra dependency).
"""
from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urlparse

from django.utils.safestring import mark_safe

# Tags allowed in rich question/explanation content
_ALLOWED_TAGS = {
    "p",
    "br",
    "b",
    "strong",
    "i",
    "em",
    "u",
    "sub",
    "sup",
    "span",
    "div",
    "ul",
    "ol",
    "li",
    "img",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "hr",
    "code",
    "pre",
    "blockquote",
    "h1",
    "h2",
    "h3",
    "h4",
}

# Attributes allowed per tag (others stripped)
_ALLOWED_ATTRS = {
    "img": {"src", "alt", "class", "width", "height", "style"},
    "span": {"class", "style"},
    "div": {"class", "style"},
    "p": {"class", "style"},
    "td": {"colspan", "rowspan", "class", "style"},
    "th": {"colspan", "rowspan", "class", "style"},
    "table": {"class", "style"},
    "a": {"href", "title", "rel", "target"},
    "*": {"class"},
}

# Style properties that are relatively safe for math/equation layout
_SAFE_STYLE_RE = re.compile(
    r"^(?:"
    r"color|background(?:-color)?|font-(?:size|weight|style|family)|"
    r"text-align|vertical-align|display|margin(?:-(?:top|right|bottom|left))?|"
    r"padding(?:-(?:top|right|bottom|left))?|width|height|max-width|max-height|"
    r"line-height|border(?:-(?:top|right|bottom|left|radius|color|style|width))?|"
    r"white-space|overflow|float|clear|position|top|left|right|bottom"
    r")\s*:",
    re.I,
)


def _safe_src(value: str) -> str | None:
    """Allow relative media paths and http(s) image URLs only."""
    if not value:
        return None
    value = value.strip()
    if value.startswith("//"):
        return None
    parsed = urlparse(value)
    if parsed.scheme in ("", "http", "https"):
        # Block javascript: and data: except images sometimes use data: — block data for safety
        if parsed.scheme == "" and not value.lower().startswith("javascript:"):
            return value
        if parsed.scheme in ("http", "https"):
            return value
    return None


def _clean_style(style: str) -> str:
    parts = []
    for decl in style.split(";"):
        decl = decl.strip()
        if not decl:
            continue
        if _SAFE_STYLE_RE.match(decl) and "expression" not in decl.lower() and "url(" not in decl.lower():
            parts.append(decl)
    return "; ".join(parts)


def _escape_attr(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


class _AllowlistSanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._out: list[str] = []
        self._skip_depth = 0  # drop content of script/style/etc.

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if self._skip_depth:
            self._skip_depth += 1
            return
        if tag in ("script", "style", "iframe", "object", "embed", "link", "meta"):
            self._skip_depth = 1
            return
        if tag not in _ALLOWED_TAGS:
            return
        allowed = _ALLOWED_ATTRS.get(tag, set()) | _ALLOWED_ATTRS.get("*", set())
        cleaned = []
        for name, value in attrs:
            if not name or name.lower().startswith("on"):
                continue
            name = name.lower()
            if name not in allowed:
                continue
            value = value or ""
            if name == "src":
                value = _safe_src(value)
                if value is None:
                    continue
            elif name == "href":
                if value.strip().lower().startswith(("javascript:", "vbscript:", "data:")):
                    continue
            elif name == "style":
                value = _clean_style(value)
                if not value:
                    continue
            cleaned.append(f'{name}="{_escape_attr(value)}"')
        attr_str = (" " + " ".join(cleaned)) if cleaned else ""
        if tag == "br":
            self._out.append("<br>")
        elif tag == "hr":
            self._out.append("<hr>")
        elif tag == "img":
            # img must have src
            if any(a.startswith("src=") for a in cleaned):
                self._out.append(f"<img{attr_str}>")
        else:
            self._out.append(f"<{tag}{attr_str}>")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self._skip_depth:
            self._skip_depth -= 1
            return
        if tag in _ALLOWED_TAGS and tag not in ("br", "hr", "img"):
            self._out.append(f"</{tag}>")

    def handle_data(self, data):
        if self._skip_depth:
            return
        self._out.append(
            data.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )

    def handle_entityref(self, name):
        if self._skip_depth:
            return
        self._out.append(f"&{name};")

    def handle_charref(self, name):
        if self._skip_depth:
            return
        self._out.append(f"&#{name};")

    def get_html(self) -> str:
        return "".join(self._out)


def sanitize_html(value: str | None) -> str:
    """Return sanitized HTML string (not marked safe)."""
    if not value:
        return ""
    text = str(value)
    # Fast path: plain text without tags
    if "<" not in text and ">" not in text:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>\n")
        )
    parser = _AllowlistSanitizer()
    try:
        parser.feed(text)
        parser.close()
    except Exception:
        # On parse failure, escape everything
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>\n")
        )
    return parser.get_html()


def safe_html(value: str | None):
    """Sanitize then mark_safe for Django templates."""
    return mark_safe(sanitize_html(value))
