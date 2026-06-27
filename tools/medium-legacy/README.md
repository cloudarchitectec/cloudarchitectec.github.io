# Medium legacy redirect tooling

Point legacy Medium stories at [cloudarchitectec.com](https://cloudarchitectec.com/) using a **manual hybrid** workflow.

## Your worklist CSV

**Path:** [`output/medium-manual-worklist.csv`](output/medium-manual-worklist.csv)

Columns: `story_name`, `medium_link`, `ec_site_link`, `medium_settings_link`

This file is **not gitignored** — it should appear in your file tree.

## Quick start

```bash
source .venv/bin/activate

# 1. Login (once)
python3 tools/medium-legacy/update_medium_posts.py --login

# 2. Build worklist
bash tools/medium-legacy/run_after_login.sh

# 3. Open output/medium-manual-worklist.csv and work through rows manually
```

### Per post (manual)

1. Open `medium_settings_link` → Advanced Settings → tick **originally published elsewhere**
2. Paste `ec_site_link` → save → **reload settings** to confirm it stuck

### Optional: banner via Playwright

```bash
python3 tools/medium-legacy/update_medium_posts.py --headed --ids {medium_id} --force
```

### Optional: verify public page

```bash
python3 tools/medium-legacy/update_medium_posts.py --verify-only --ids {medium_id}
# -> output/medium-verify-report.csv
```

## Scripts

| Script | Purpose |
|--------|---------|
| `update_medium_posts.py` | `--login`, `--list-stories`, banner update, `--verify-only` |
| `build_mapping.py` | Match Medium stories → Hugo slugs |
| `export_manual_worklist.py` | Write `output/medium-manual-worklist.csv` |
| `run_after_login.sh` | Full pipeline after login |

## Output folder

See [`output/README.md`](output/README.md). Generated caches are gitignored; **worklist CSV is kept**.

## Tests

```bash
python3 tools/medium-legacy/test_medium_legacy.py
python3 tools/medium-legacy/test_build_mapping.py
```
