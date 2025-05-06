#!/bin/sh
cd /opt/edubadges-server/code/
source ../edubadges_venv/bin/activate
./manage.py delete_direct_awards
deactivate
