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
                # "document" = user opened URL in tab / iframe navigation that triggers download
                # Allow server-side fetchers (Office Online, empty dest from some tools)
                if fetch_dest in ("document",):
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

        return response
