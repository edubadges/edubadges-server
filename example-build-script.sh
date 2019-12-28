#!/bin/bash

#############################################################################
# COLOURS AND MARKUP
#############################################################################

red='\033[0;31m'            # Red
green='\033[0;49;92m'       # Green
yellow='\033[0;49;93m'      # Yellow
white='\033[1;37m'          # White
grey='\033[1;49;30m'        # Grey
nc='\033[0m'                # No color

clear
cd /var/docker/edubadges/badgr-server/badgr

echo -e "${yellow}
# Cloning badgr-server code (branch develop)
#############################################################################${nc}"
git clone --single-branch -b develop https://github.com/edubadges/badgr-server
cd /var/docker/edubadges/badgr-server/badgr/badgr-server
git submodule init
git submodule update
sleep 5
echo -e "${green}Done....${nc}"

echo -e "${yellow}
# Copy local settings file (settings_local.py)
#############################################################################${nc}"
cp /var/docker/edubadges/badgr-server/config/badgr/settings_local.py /var/docker/edubadges/badgr-server/badgr/badgr-server/apps/mainsite/settings_local.py
echo -e "${green}
# Done... ${nc}"

echo -e "${yellow}
# Build the docker image AKA run first_build.sh
#############################################################################${nc}"
cd /var/docker/edubadges
sh first_build.sh
echo -e "${green}Done....${nc}"

echo -e "${yellow}
# Bring the docker container up
#############################################################################${nc}"
docker-compose up -d
docker ps -a
echo -e "${green}Ready!${nc}"