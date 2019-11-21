#!/bin/bash
/usr/bin/printenv | /usr/bin/sed 's/^\(.*\)$/export \1/g' > /root/.profile
