#!/usr/bin/env bash
set -euo pipefail

# Safer Postgres reset script using .env variables.
# - Drops and recreates the database
# - Applies migrations
# - Optional createsuperuser
#
# Requires either:
#   - Local PostgreSQL client (dropdb/createdb), or
#   - Docker Compose with the 'postgres' service (psql run inside container)

PROJECT_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." &> /dev/null && pwd)
cd "$PROJECT_ROOT"

if [[ ! -f .env ]]; then
  echo ".env not found in project root. Aborting." >&2
  exit 1
fi

# Load only required vars from .env (do not echo them)
while IFS='=' read -r key value; do
  case "$key" in
    POSTGRES_DB|POSTGRES_USER|POSTGRES_PASSWORD|POSTGRES_HOST|POSTGRES_PORT)
      export "$key"="$value"
      ;;
    *) ;;
  esac
done < <(grep -E '^(POSTGRES_DB|POSTGRES_USER|POSTGRES_PASSWORD|POSTGRES_HOST|POSTGRES_PORT)=' .env)

: "${POSTGRES_DB:?POSTGRES_DB missing in .env}"
: "${POSTGRES_USER:?POSTGRES_USER missing in .env}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD missing in .env}"
: "${POSTGRES_HOST:=localhost}"
: "${POSTGRES_PORT:=5432}"

read -p "This will DROP and RECREATE the database '${POSTGRES_DB}'. Type the database name to confirm: " CONFIRM
if [[ "$CONFIRM" != "$POSTGRES_DB" ]]; then
  echo "Confirmation mismatch. Aborting."
  exit 1
fi

use_local_client=false
if command -v dropdb >/dev/null 2>&1 && command -v createdb >/dev/null 2>&1; then
  use_local_client=true
fi

if $use_local_client; then
  echo "Dropping database via local client..."
  PGPASSWORD="$POSTGRES_PASSWORD" dropdb --if-exists -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" "$POSTGRES_DB" || true
  echo "Creating database via local client..."
  PGPASSWORD="$POSTGRES_PASSWORD" createdb -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" "$POSTGRES_DB"
else
  # Fallback to docker compose exec inside 'postgres' service
  if command -v docker >/dev/null 2>&1 && (docker compose version >/dev/null 2>&1 || docker-compose version >/dev/null 2>&1); then
    echo "Dropping/Recreating database inside docker compose postgres service..."
    # choose compose command
    if docker compose version >/dev/null 2>&1; then
      DCMD=(docker compose)
    else
      DCMD=(docker-compose)
    fi
    # Terminate connections, drop and recreate
    "${DCMD[@]}" exec -T postgres sh -lc "psql -U \"$POSTGRES_USER\" -d postgres -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${POSTGRES_DB}'; DROP DATABASE IF EXISTS \"${POSTGRES_DB}\"; CREATE DATABASE \"${POSTGRES_DB}\" OWNER \"${POSTGRES_USER}\";\""
  else
    echo "Neither local Postgres client nor docker compose detected. Install psql client or run Postgres via docker compose." >&2
    exit 1
  fi
fi

echo "Applying migrations..."
poetry run python manage.py migrate

read -p "Create superuser now? (y/N): " CREATE_SU
if [[ "$CREATE_SU" == "y" || "$CREATE_SU" == "Y" ]]; then
  poetry run python manage.py createsuperuser
fi

echo "Reset complete."
