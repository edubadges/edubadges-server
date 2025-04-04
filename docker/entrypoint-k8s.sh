#!/bin/bash
set -e

mkdir -p mediafiles/uploads/badges/
cp uploads/badges/*.png mediafiles/uploads/badges/
cp uploads/issuers/surf.png mediafiles/uploads/issuers/
cp uploads/institution/surf.png mediafiles/uploads/institution/

# Run migrations
#echo "Running migrations"
#python ./manage.py migrate

#echo "Seeding the database"
#python ./manage.py seed

exec "$@"
