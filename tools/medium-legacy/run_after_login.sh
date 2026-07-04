#!/usr/bin/env bash
# Run after: python3 tools/medium-legacy/update_medium_posts.py --login
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
ML="tools/medium-legacy"
OUT="$ML/output"

mkdir -p "$OUT"

echo "=== 1. Session / profile check ==="
if [[ -f "$ML/.medium-session.json" ]]; then
  python3 -c "
import json
from pathlib import Path
p = Path('$ML/.medium-session.json')
d = json.loads(p.read_text())
print(f'  session: {len(d.get(\"cookies\", []))} cookies')
"
else
  echo "  WARN: no .medium-session.json — run --login first"
fi

echo ""
echo "=== 2. List Medium stories from public profile ==="
python3 "$ML/update_medium_posts.py" --list-stories

echo ""
echo "=== 3. Build Hugo mapping ==="
python3 "$ML/build_mapping.py" || true

echo ""
echo "=== 4. Export manual worklist ==="
python3 "$ML/export_manual_worklist.py"

echo ""
echo "=== 5. Summary ==="
python3 - <<'PY'
import csv
import json
from pathlib import Path

out = Path("tools/medium-legacy/output")
worklist = out / "medium-manual-worklist.csv"
archive = out / "medium-archive-cache.json"
mapping = out / "medium-mapping.json"

if archive.exists():
    print(f"  archive stories: {json.loads(archive.read_text()).get('count', 0)}")
if mapping.exists():
    posts = json.loads(mapping.read_text()).get("posts", [])
    matched = sum(1 for p in posts if p.get("blog_url"))
    print(f"  mapping: {len(posts)} total, {matched} with ec_site_link")
if worklist.exists():
    rows = list(csv.DictReader(worklist.open(encoding="utf-8")))
    print(f"  worklist: {len(rows)} rows")
    print(f"\n  -> {worklist.resolve()}")
PY
