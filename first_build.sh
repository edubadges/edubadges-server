#!/bin/bash

# Build the two containers
# Images are automatically fetched, if necessary, from docker hub
docker-compose build

# Start a new web container to run migrations
# Use --rm to remove the container when the command completes
docker-compose up -d
docker-compose run --rm web python /var/badgr/code/manage.py migrate

docker cp ./badgr-server/config/nginx/certs/ web:/var/badgr/code/cert

echo "Waiting for DB to start up..."
TEST=$( docker inspect --format "{{.State.Health.Status}}" db )
until [ "$TEST" = "healthy" ];
do
  echo "Waiting for database connection..."
  sleep 2
  TEST=$( docker inspect --format "{{.State.Health.Status}}" db )
done

docker-compose exec web python /var/badgr/code/manage.py dist
docker-compose exec web python /var/badgr/code/manage.py migrate
docker-compose exec web python /var/badgr/code/manage.py collectstatic --noinput