#!/usr/bin/env bash
# Local validation wrapper — see TESTING.md for tier overview.
#
# Usage:
#   ./scripts/dev-check.sh              # check-posts + fast unit tests (~5s)
#   ./scripts/dev-check.sh --post SLUG  # single post rules only
#   ./scripts/dev-check.sh --quick      # same as default (explicit)
#   ./scripts/dev-check.sh --full       # CI gate: Hugo build, verify-build, all pytest (~60s)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if [[ -x "$REPO_ROOT/.venv/bin/python3" ]]; then
  PYTHON="$REPO_ROOT/.venv/bin/python3"
else
  PYTHON=python3
fi

usage() {
  cat <<'EOF'
Usage: ./scripts/dev-check.sh [OPTIONS]

Options:
  --post SLUG   Validate one post with check-posts.py
  --quick       Fast checks only (no Hugo build / browser smoke)
  --full        Full CI gate: Hugo build, verify-build.sh, all pytest
  -h, --help    Show this help
EOF
}

POST=""
QUICK=0
FULL=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --post)
      POST="${2:?--post requires a slug}"
      shift 2
      ;;
    --quick)
      QUICK=1
      shift
      ;;
    --full)
      FULL=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -n "$POST" ]]; then
  python3 scripts/check-posts.py --post "$POST"
  exit 0
fi

python3 scripts/check-posts.py
"$PYTHON" -m pip install -q -r requirements.txt 2>/dev/null || true

if [[ "$FULL" -eq 1 ]]; then
  if ! command -v hugo &>/dev/null; then
    echo "hugo not installed — required for --full" >&2
    exit 1
  fi
  output="$(hugo --gc --minify --cleanDestinationDir --printPathWarnings --logLevel warn 2>&1)"
  echo "$output"
  if echo "$output" | grep -qiE 'duplicate path|(^|[[:space:]])WARN:'; then
    echo "Hugo build warnings detected" >&2
    exit 1
  fi
  ./scripts/verify-build.sh
  export HUGO_SKIP_REBUILD=1
  "$PYTHON" -m playwright install chromium
  "$PYTHON" -m pytest tests/ -q
else
  "$PYTHON" -m pytest tests/test_post_validation.py tests/test_list_pages.py::TestListTemplateStructure -q
fi
