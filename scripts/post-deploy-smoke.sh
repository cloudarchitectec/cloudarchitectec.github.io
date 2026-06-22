#!/usr/bin/env bash
# Post-deploy smoke against live production site.
# Usage: BASE_URL=https://cloudarchitectec.com ./scripts/post-deploy-smoke.sh

set -euo pipefail

BASE_URL="${BASE_URL:-https://cloudarchitectec.com}"
BASE_URL="${BASE_URL%/}"

curl_check() {
  local url="$1"
  local needle="${2:-}"
  echo "Checking ${url}"
  body="$(curl -fsSL --retry 5 --retry-delay 10 --retry-all-errors "${url}")"
  if [ -n "$needle" ] && ! echo "$body" | grep -qF "$needle"; then
    echo "❌ Expected content not found at ${url}: ${needle}"
    exit 1
  fi
  echo "✅ ${url}"
}

echo "=== POST-DEPLOY SMOKE (${BASE_URL}) ==="

curl_check "${BASE_URL}/" "Cloud Architect EC"
curl_check "${BASE_URL}/index.xml" "<rss"
curl_check "${BASE_URL}/sitemap.xml" "2025-10-04-goodbye-medium"
curl_check "${BASE_URL}/robots.txt" "Sitemap:"
curl_check "${BASE_URL}/posts/2025-10-04-goodbye-medium/" "掰掰 Medium"
curl_check "${BASE_URL}/search/" "searchInput"

echo "=== POST-DEPLOY SMOKE DONE ==="
