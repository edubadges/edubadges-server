#!/bin/bash
set -e

mkdir -p mediafiles/uploads/badges/
cp uploads/badges/*.png mediafiles/uploads/badges/

# Run migrations
#echo "Running migrations"
#python ./manage.py migrate

#echo "Seeding the database"
#python ./manage.py seed

exec "$@"
