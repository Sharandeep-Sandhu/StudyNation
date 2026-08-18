#!/bin/sh
set -e

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating superuser (if needed)..."
if [ "$CREATE_SUPERUSER" = "True" ]; then
  echo "Creating superuser with username: admin"
  DJANGO_SUPERUSER_PASSWORD="admin@admin" \
  python manage.py createsuperuser --noinput \
    --username "admin" \
    --email "admin@admin.com" || true
else
  echo "Skipping superuser creation"
fi

# Render (and most PaaS) inject PORT; default 8000 for local Docker
PORT="${PORT:-8000}"

echo "Starting application on port ${PORT}..."
if [ "$#" -eq 0 ]; then
  exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT}" --workers 2 --timeout 120
else
  exec "$@"
fi