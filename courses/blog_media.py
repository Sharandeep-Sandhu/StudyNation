"""Blog media helpers: MIME types and safe streaming for image/video/PDF."""

from __future__ import annotations

import mimetypes
import os
from pathlib import Path

from django.http import FileResponse, Http404


VIDEO_MIME = {
    ".mp4": "video/mp4",
    ".m4v": "video/mp4",
    ".webm": "video/webm",
    ".ogg": "video/ogg",
    ".ogv": "video/ogg",
    ".mov": "video/quicktime",
}

IMAGE_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".svg": "image/svg+xml",
}


def file_ext(name: str) -> str:
    return Path(name or "").suffix.lower()


def guess_blog_content_type(name: str) -> str:
    ext = file_ext(name)
    if ext in VIDEO_MIME:
        return VIDEO_MIME[ext]
    if ext in IMAGE_MIME:
        return IMAGE_MIME[ext]
    if ext == ".pdf":
        return "application/pdf"
    ctype, _ = mimetypes.guess_type(name or "")
    return ctype or "application/octet-stream"


def open_file_response(path: str, name: str, as_attachment: bool = False) -> FileResponse:
    if not path or not os.path.isfile(path):
        raise Http404("File not found")
    content_type = guess_blog_content_type(name or path)
    fh = open(path, "rb")
    response = FileResponse(fh, content_type=content_type)
    safe_name = os.path.basename(name or path).replace('"', "")
    disposition = "attachment" if as_attachment else "inline"
    response["Content-Disposition"] = f'{disposition}; filename="{safe_name}"'
    response["X-Content-Type-Options"] = "nosniff"
    response["X-Frame-Options"] = "SAMEORIGIN"
    response["Cache-Control"] = "private, max-age=3600"
    return response
