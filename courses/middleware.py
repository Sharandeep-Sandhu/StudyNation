"""View-only media: block forced downloads of office files and prefer inline display."""

from django.http import HttpResponse


class InlineMediaMiddleware:
    """
    - Prefer Content-Disposition: inline for media (view, not Save As attachment)
    - Block direct browser navigation to Office files (.ppt/.pptx/etc.) which
      would otherwise auto-download because browsers cannot display them.
    """

    PROTECTED_PREFIXES = (
        "/media/blog_images/",
        "/media/blog_media/",
        "/media/resources/",
        "/media/course_thumbnails/",
        "/media/discussion_images/",
        "/media/question_equations/",
    )

    # Opening these as a top-level document forces a download in browsers.
    OFFICE_EXTS = (".ppt", ".pptx", ".pps", ".ppsx", ".doc", ".docx", ".xls", ".xlsx")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = (request.path or "").lower()

        if any(path.startswith(p) for p in self.PROTECTED_PREFIXES):
            # Block top-level navigation to Office files (prevents auto-download UI)
            if path.endswith(self.OFFICE_EXTS):
                fetch_dest = (request.headers.get("Sec-Fetch-Dest") or "").lower()
                fetch_mode = (request.headers.get("Sec-Fetch-Mode") or "").lower()
                # "document" / navigate = user opened URL in a tab
                # Empty Sec-Fetch-* on older browsers: treat GET without range as navigate
                is_navigation = fetch_dest in ("document",) or fetch_mode == "navigate"
                if not fetch_dest and not fetch_mode and request.method == "GET":
                    # Heuristic: Accept prefers HTML → likely address-bar navigation
                    accept = (request.headers.get("Accept") or "").lower()
                    if "text/html" in accept:
                        is_navigation = True
                if is_navigation:
                    return HttpResponse(
                        "Downloading this file is not allowed. "
                        "Open the blog or resources page to view content online.",
                        status=403,
                        content_type="text/plain; charset=utf-8",
                    )

        response = self.get_response(request)

        if any((request.path or "").startswith(p) for p in self.PROTECTED_PREFIXES):
            response["Content-Disposition"] = "inline"
            response["X-Content-Type-Options"] = "nosniff"
            response["X-Frame-Options"] = "SAMEORIGIN"
            # Discourage caching of sensitive media by shared proxies
            if "Cache-Control" not in response:
                response["Cache-Control"] = "private, max-age=3600"

        return response
