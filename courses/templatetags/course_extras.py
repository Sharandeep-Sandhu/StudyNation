from django import template

from courses.math_content import render_chat_math, sanitize_math_content

register = template.Library()


@register.filter(name="chat_math")
def chat_math(value):
    """Clean and HTML-escape chat/post text so MathJax can render formulas."""
    return render_chat_math(value)


@register.filter(name="sanitize_math")
def sanitize_math(value):
    """Return cleaned plain text (for edit forms / previews)."""
    return sanitize_math_content(value)


@register.filter
def split_once(value, sep=":"):
    """
    Split 'value' on the first occurrence of 'sep' and return a tuple-like
    list: [before, after]. If 'sep' is not present, returns [value, ''].
    Usage: {{ line|split_once:":" }} -> use with |first / |last, or
    better, use the dedicated module_title / module_desc filters below.
    """
    if sep in value:
        before, after = value.split(sep, 1)
        return [before.strip(), after.strip()]
    return [value.strip(), ""]


@register.filter
def module_title(value, sep=":"):
    """Return the part before the first ':' (e.g. 'Module 1')."""
    if sep in value:
        return value.split(sep, 1)[0].strip()
    return value.strip()


@register.filter
def module_desc(value, sep=":"):
    """Return the part after the first ':' (e.g. 'Introduction and Fundamentals')."""
    if sep in value:
        return value.split(sep, 1)[1].strip()
    return ""
