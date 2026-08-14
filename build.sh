#!/usr/bin/env bash
# Render build script (native Python runtime)
# Prefer Docker deploy (Dockerfile) so LibreOffice is available for .doc conversion.
set -o errexit
set -o pipefail

echo "==> Optional system packages (LibreOffice for .doc → .docx)"
# Native Render Python builds usually cannot apt-install. This path helps
# Docker / privileged Linux hosts that still invoke build.sh.
if command -v apt-get >/dev/null 2>&1 && [ "$(id -u)" -eq 0 ]; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
    libreoffice-writer-nogui fonts-dejavu-core fonts-liberation \
    || echo "WARNING: LibreOffice install failed — upload .docx files instead of .doc"
  rm -rf /var/lib/apt/lists/* || true
  (soffice --version || libreoffice --version || echo "LibreOffice binary not on PATH")
else
  echo "Skipping apt LibreOffice install (no root/apt). Use Docker image or upload .docx."
fi

echo "==> Installing dependencies"
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Collecting static files"
python manage.py collectstatic --noinput

echo "==> Applying database migrations"
python manage.py migrate --noinput

echo "==> Ensuring critical schema columns (discussion / past papers)"
python manage.py ensure_schema

echo "==> Verifying critical models / columns"
python - <<'PY'
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

issues = []
try:
    from courses.models import (
        PastPaper,
        Resource,
        CourseCategory,
        DiscussionBoard,
        DiscussionPost,
        DiscussionReply,
    )

    list(PastPaper.objects.values_list("id", "answer_pdf")[:1])
    list(Resource.objects.values_list("id", "file")[:1])
    list(CourseCategory.objects.values_list("id", "name")[:1])
    list(DiscussionBoard.objects.values_list("id", "slug")[:1])
    list(DiscussionPost.objects.values_list("id", "video_solution_url")[:1])
    list(DiscussionReply.objects.values_list("id", "video_solution_url", "updated_at")[:1])
    print("Model checks OK")
except Exception as exc:
    issues.append(str(exc))
    print("Model check FAILED:", exc)

if issues:
    raise SystemExit("Build verification failed — migrations may be incomplete.")
print("Build complete.")
PY
