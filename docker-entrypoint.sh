#!/bin/bash

./manage.py migrate
./manage.py seed
./manage.py runserver