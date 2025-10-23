#!/bin/bash

set -e

# REMOVE OLD DATABASE
echo removing old db...
rm db.sqlite3

# REMOVE OLD MIGRATIONS
echo removing old migrations...
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc"  -delete

# MAKE MIGRATIONS
echo making migrations...
poetry run python manage.py makemigrations users submissions comments messaging
poetry run python manage.py migrate
