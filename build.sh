#!/usr/bin/env bash
# Render build script (native Python runtime)
set -o errexit
set -o pipefail

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
