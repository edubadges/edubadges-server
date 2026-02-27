#!/bin/bash
set -e

# Run migrations
echo "Running migrations"
python ./manage.py migrate

echo "Seeding the database"
python ./manage.py seed --check_first

# Run the server
echo "Starting the server"
# python -m http.server 8000   
python ./manage.py runserver --verbosity 2 0.0.0.0:8000
