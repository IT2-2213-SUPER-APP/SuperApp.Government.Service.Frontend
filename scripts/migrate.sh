#!/usr/bin/env bash

set -e

poetry run python manage.py makemigrations
poetry run python manage.py migrate
