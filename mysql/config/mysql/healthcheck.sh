#!/bin/bash

export MYSQL_PWD=${MYSQL_PASSWORD}

mysqladmin --user=${MYSQL_USER} ping --silent
