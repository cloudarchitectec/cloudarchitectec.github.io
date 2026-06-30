#!/usr/bin/env bash
# Create repo .venv and install requirements.txt (idempotent).
# Source from other scripts:  source scripts/ensure-venv.sh
# Or run directly:            bash scripts/ensure-venv.sh
#
# Optional: ENSURE_VENV_PLAYWRIGHT=1 installs Chromium for pytest-playwright.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export VENV_DIR="${VENV_DIR:-$REPO_ROOT/.venv}"
export VENV_PYTHON="$VENV_DIR/bin/python3"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Creating Python venv at $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

"$VENV_PYTHON" -m pip install -q --upgrade pip
"$VENV_PYTHON" -m pip install -q -r "$REPO_ROOT/requirements.txt"

if [[ "${ENSURE_VENV_PLAYWRIGHT:-0}" == "1" ]]; then
  if [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
    "$VENV_PYTHON" -m playwright install --with-deps chromium
  else
    "$VENV_PYTHON" -m playwright install chromium
  fi
fi
