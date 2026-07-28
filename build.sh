#!/usr/bin/env bash
# Render build script (native Python runtime)
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput
