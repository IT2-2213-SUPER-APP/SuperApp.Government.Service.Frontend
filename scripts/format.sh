#!/usr/bin/env bash
set -euo pipefail

# Format Python code with Black.
# Usage:
#   scripts/format.sh            # format (fix) using pyproject.toml
#   scripts/format.sh check      # check only (no changes), shows diff
#   BLACK_ARGS="--fast" scripts/format.sh  # pass extra args to Black

MODE=${1:-fix}
EXTRA_ARGS=${BLACK_ARGS:-}

if [[ "${MODE}" == "check" ]]; then
  echo "Running Black in CHECK mode..."
  poetry run black --config pyproject.toml --check --diff ${EXTRA_ARGS} .
else
  echo "Running Black to format code..."
  poetry run black --config pyproject.toml ${EXTRA_ARGS} .
fi
