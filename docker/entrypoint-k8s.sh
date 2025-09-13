#!/bin/bash
set -e

# Only copy files to mediafiles if not using S3 storage
USE_S3_LOWER=$(echo "${USE_S3}" | tr '[:upper:]' '[:lower:]')
if [ "${USE_S3_LOWER}" != "true" ]; then
    echo "Setting up local file storage..."
    mkdir -p mediafiles/uploads/badges/
    mkdir -p mediafiles/uploads/issuers/
    mkdir -p mediafiles/uploads/institution/
    cp uploads/badges/*.png mediafiles/uploads/badges/
    cp uploads/issuers/surf.png mediafiles/uploads/issuers/
    cp uploads/institution/surf.png mediafiles/uploads/institution/
    echo "Local files copied to mediafiles/"
else
    echo "S3 storage is enabled. Initial images will be uploaded during seeding process."
fi

exec "$@"
