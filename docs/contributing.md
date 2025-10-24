# Contributing

## Setup
- Use Python 3.11.14 via pyenv
- Install dependencies with Poetry: `poetry install`
- Copy `.env.example` to `.env` and configure
- Start Postgres: `docker compose up -d postgres`

## Commands
- Format: `bash scripts/format.sh` or `bash scripts/format.sh check`
- Tests: `poetry run pytest -q`
- Run: `poetry run python manage.py runserver`
- Celery: `poetry run celery -A config worker -l info` and `poetry run celery -A config beat -l info`
- Reset DB: `bash scripts/reset.sh`

## Style
- Black + isort (black profile)
- Keep endpoints RESTful; prefer nested routes for child resources
- Avoid committing migrations churn; generate stable migrations per feature

## Branching
- Feature branches: `feat/<area>-<short-desc>`
- Bugfix branches: `fix/<area>-<short-desc>`

## PRs
- Include concise description, screenshots (if UI), and test plan
- Ensure `scripts/format.sh check` and tests pass
