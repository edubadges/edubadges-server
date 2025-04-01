#!/bin/bash
set -e

#source /env/bin/activate

# Run migrations
echo "Running migrations"
python ./manage.py migrate

echo "Seeding the database"
python ./manage.py seed

MyGuniWorkers="${GUNI_WORKERS:-1}"

gunicorn --bind :8000 --workers $MyGuniWorkers wsgi:application
