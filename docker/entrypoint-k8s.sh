#!/bin/bash
set -e

mkdir -p mediafiles/uploads/badges/
mkdir -p mediafiles/uploads/issuers/
mkdir -p mediafiles/uploads/institution/
cp uploads/badges/*.png mediafiles/uploads/badges/
cp uploads/issuers/surf.png mediafiles/uploads/issuers/
cp uploads/institution/surf.png mediafiles/uploads/institution/

exec "$@"
