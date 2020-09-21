#!/bin/sh

python manage.py flush --no-input
python manage.py migrate
python manage.py collectstatic --no-input --clear

. ../../../private/envvars

gunicorn --bind 0.0.0.0:8000 --workers 4 aasp.wsgi