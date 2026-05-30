#!/usr/bin/env bash
set -euo pipefail

# Usage: scripts/quality.sh [--fix]
#   --fix  Apply black formatting in-place (default: check only)

FIX=false
for arg in "$@"; do
  [[ "$arg" == "--fix" ]] && FIX=true
done

TARGETS="backend/ main.py"

echo "=== Black ==="
if $FIX; then
  uv run black $TARGETS
else
  uv run black --check $TARGETS
fi

echo "=== Tests ==="
uv run pytest -q .

echo ""
echo "All checks passed."
