# Analytics (GA4 + homepage stats)

Two layers: **live GA4 tag** on production pages, and **cached stats** in `data/analytics.json` for the homepage `{{< analytics-stats >}}` widget.

## GA4 tag (traffic measurement)

| Item | Value |
|------|-------|
| Measurement ID | `G-F5Z4F1PYEE` (`hugo.toml` `[params.googleAnalytics]`) |
| Partial | `layouts/partials/google_analytics.html` |
| Loaded when | `hugo.IsProduction` or `params.env = "production"` (CI sets `HUGO_ENV=production` on deploy) |
| Local `hugo server` | GA4 **off** by default (`params.env = "development"`) |

### Verify GA4 is collecting

1. [GA4](https://analytics.google.com/) → **Realtime**
2. Open `https://cloudarchitectec.com/` in a private window
3. Confirm an active user / page view within ~30 seconds

### Verify Measurement ID

GA4 Admin → **Data streams** → web stream → ID must be `G-F5Z4F1PYEE`.

## Homepage stats widget (`data/analytics.json`)

| Item | Detail |
|------|--------|
| Source | GA4 Data API via `.github/workflows/scripts/update_analytics.py` |
| Display | `layouts/shortcodes/analytics-stats.html` on home page |
| Refresh | Deploy CI only — every push to `main`, plus manual **Deploy Blog** runs. Fetched into the build tree, **never committed**. No cron: the figures are cumulative since 2023-01-01, so drift between deploys is invisible |
| Failure | Analytics step failure **blocks deploy** (no silent stale stats) |
| Committed copy | `data/analytics.json` in git is a snapshot for local `hugo server`; it goes stale between edits. Refresh locally with `python3 .github/workflows/scripts/update_analytics.py` (needs the two env vars below) |

### GitHub secrets (CI only)

| Secret | Purpose |
|--------|---------|
| `GOOGLE_SERVICE_ACCOUNT_KEY` | Service account JSON with GA4 Data API access |
| `GOOGLE_ANALYTICS_PROPERTY_ID` | Numeric GA4 property ID (not the `G-` measurement ID) |

Service account needs **Viewer** on the GA4 property. Enable **Google Analytics Data API** in Google Cloud.

### Manual refresh

Actions → **Deploy Blog** → Run workflow. That re-fetches GA4 and redeploys with fresh stats.

If the workflow fails, check secrets and service account permissions above.

## Related workflows

| Workflow | Role |
|----------|------|
| [`.github/workflows/blog-deployment.yml`](../.github/workflows/blog-deployment.yml) | Sole analytics refresher: fetches GA4 before the Hugo build (push to `main`, weekly cron, manual). Failure blocks deploy |
| [`.github/actions/update-analytics`](../.github/actions/update-analytics/action.yml) | Composite action doing the fetch. **Fetch-only** — the old commit step was removed so analytics never lands on `main` |

See also [TESTING.md](TESTING.md) for validation tiers.
