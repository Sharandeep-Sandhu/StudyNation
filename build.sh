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

echo "==> Verifying critical models / columns"
python - <<'PY'
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import connection

issues = []
try:
    from courses.models import PastPaper, Resource, CourseCategory

    # Touch fields that must exist after migrations 0020–0023
    list(PastPaper.objects.values_list("id", "answer_pdf")[:1])
    list(Resource.objects.values_list("id", "file")[:1])
    list(CourseCategory.objects.values_list("id", "name")[:1])
    print("Model checks OK")
except Exception as exc:
    issues.append(str(exc))
    print("Model check FAILED:", exc)

if issues:
    raise SystemExit("Build verification failed — migrations may be incomplete.")
print("Build complete.")
PY
