#!/bin/bash
set -e

# Collect static
echo "Collect static files into STATIC_ROOT"
python manage.py collectstatic --noinput

exec "$@"
