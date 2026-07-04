# Generated output

| File | Purpose |
|------|---------|
| **`medium-manual-worklist.csv`** | **Your manual spreadsheet** — open this for canonical updates |
| `medium-mapping.json` | Medium ↔ Hugo match (cache; gitignored) |
| `medium-archive-cache.json` | Story list from `--list-stories` (gitignored) |
| `medium-verify-report.csv` | Optional output from `--verify-only` (gitignored) |

Regenerate worklist:

```bash
bash tools/medium-legacy/run_after_login.sh
# or
python3 tools/medium-legacy/export_manual_worklist.py
```
