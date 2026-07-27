"""Shared question-list pagination: default 20 per page + selectable size."""

from __future__ import annotations

from django.core.paginator import Paginator
from django.http import QueryDict

DEFAULT_PER_PAGE = 20
PER_PAGE_CHOICES = (10, 20, 25, 50, 100)


def parse_per_page(
    request,
    *,
    default: int = DEFAULT_PER_PAGE,
    allowed: tuple[int, ...] = PER_PAGE_CHOICES,
    allow_all: bool = True,
    total_count: int | None = None,
) -> tuple[int, str]:
    """
    Return (per_page_int, per_page_label).
    per_page_label is the raw GET value ("20" or "all") for template selects.
    """
    raw = (request.GET.get("per_page") or str(default)).strip().lower()
    if allow_all and raw == "all":
        n = max(total_count or 1, 1)
        # Cap "all" so a huge bank cannot freeze the page
        n = min(n, 2000)
        return n, "all"
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = default
    if value not in allowed:
        # Accept any positive size in a sensible range, else fall back
        if 1 <= value <= 500:
            return value, str(value)
        value = default
    return value, str(value)


def paginate(
    request,
    queryset,
    *,
    default: int = DEFAULT_PER_PAGE,
    allowed: tuple[int, ...] = PER_PAGE_CHOICES,
    allow_all: bool = True,
):
    """
    Paginate queryset from request.GET page / per_page.
    Returns (page_obj, per_page_label, per_page_choices).
    """
    total = None
    raw = (request.GET.get("per_page") or "").strip().lower()
    if allow_all and raw == "all":
        total = queryset.count()
    per_page, label = parse_per_page(
        request, default=default, allowed=allowed, allow_all=allow_all, total_count=total
    )
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(request.GET.get("page") or 1)
    return page_obj, label, list(allowed)


def query_string_without(request, *drop_keys: str) -> str:
    """Build GET query string excluding keys (e.g. page when changing per_page)."""
    q = request.GET.copy()
    for key in drop_keys:
        q.pop(key, None)
    return q.urlencode()


def pagination_context(request, page_obj, per_page_label: str, allowed=None) -> dict:
    """Extra context keys for list templates."""
    return {
        "page_obj": page_obj,
        "per_page": per_page_label,
        "per_page_choices": list(allowed or PER_PAGE_CHOICES),
        "pagination_qs": query_string_without(request, "page"),
        "filter_qs": query_string_without(request, "page", "per_page"),
    }
