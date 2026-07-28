#!/bin/sh
set -e

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Render (and most PaaS) inject PORT; default 8000 for local Docker
PORT="${PORT:-8000}"

echo "Starting application on port ${PORT}..."
if [ "$#" -eq 0 ]; then
  exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT}" --workers 2 --timeout 120
else
  exec "$@"
fi
