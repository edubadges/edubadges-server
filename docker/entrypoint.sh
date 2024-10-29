#!/bin/bash
set -e
set -x

# Run migrations
echo "Running migrations"
python ./manage.py migrate

# Reset (-c) and Seed the database
echo "Seeding the database"
python ./manage.py seed -c

# Run the server
echo "Starting the server"
# python -m http.server 8000
python ./manage.py runserver --verbosity 2 0.0.0.0:8000
