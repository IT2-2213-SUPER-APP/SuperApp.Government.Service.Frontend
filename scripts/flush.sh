#!/usr/bin/env bash
set -euo pipefail

# DEPRECATED: This script previously reset SQLite and migrations.
# The project now uses Postgres. Please use scripts/reset.sh instead.

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
RESET_SCRIPT="$SCRIPT_DIR/reset.sh"

if [[ -x "$RESET_SCRIPT" ]]; then
  echo "[flush.sh] Deprecated. Delegating to reset.sh..."
  exec "$RESET_SCRIPT"
else
  echo "[flush.sh] Deprecated. Please run: bash scripts/reset.sh" >&2
  exit 1
fi
