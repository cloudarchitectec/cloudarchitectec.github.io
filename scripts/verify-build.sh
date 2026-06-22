#!/usr/bin/env bash
# Post-build checks for Hugo output. Used by PR CI and deploy workflow.
# Usage: PUBLIC_DIR=public ./scripts/verify-build.sh

set -euo pipefail

PUBLIC_DIR="${PUBLIC_DIR:-public}"

echo "=== POST-BUILD CHECKS (${PUBLIC_DIR}) ==="

[ -f "${PUBLIC_DIR}/CNAME" ] && echo "✅ CNAME present" \
  || (echo "❌ CNAME missing from ${PUBLIC_DIR}/" && exit 1)

if command -v xmllint &>/dev/null; then
  xmllint --noout "${PUBLIC_DIR}/index.xml" && echo "✅ RSS valid" \
    || (echo "❌ RSS invalid" && exit 1)
fi

grep -q 'media:content' "${PUBLIC_DIR}/index.xml" \
  && grep -q '/posts/.*/images/' "${PUBLIC_DIR}/index.xml" \
  && echo "✅ RSS has cover media:content with post bundle URLs" \
  || (echo "❌ RSS missing media:content — check layouts/_default/rss.xml" && exit 1)

grep -rl "@waline/client" "${PUBLIC_DIR}/posts/"*/index.html | head -1 | grep -q . \
  && echo "✅ Waline embed present in posts" \
  || (echo "❌ Waline embed not found — check comments = true in hugo.toml" && exit 1)

grep -rl "comments.cloudarchitectec.com" "${PUBLIC_DIR}/posts/"*/index.html | head -1 | grep -q . \
  && echo "✅ Comment server URL present in posts" \
  || (echo "❌ Comment server URL not found" && exit 1)

grep -rl "zh-TW" "${PUBLIC_DIR}/posts/"*/index.html | head -1 | grep -q . \
  && echo "✅ Waline zh-TW locale present in posts" \
  || (echo "❌ Waline zh-TW locale not found" && exit 1)

grep -rl 'post-footer-cta' "${PUBLIC_DIR}/posts/"*/index.html | head -1 | grep -q . \
  && echo "✅ MailerLite post footer present in posts" \
  || (echo "❌ Post footer CTA not found — check partials/post-footer.html" && exit 1)

grep -rl 'dashboard.mailerlite.com/jsonp/2459287/forms/190870271382520893/subscribe' "${PUBLIC_DIR}/posts/"*/index.html | head -1 | grep -q . \
  && echo "✅ MailerLite subscribe action present in posts" \
  || (echo "❌ MailerLite subscribe action not found" && exit 1)

grep -rl "related-posts" "${PUBLIC_DIR}/posts/"*/index.html | head -1 | grep -q . \
  && echo "✅ Related posts block present in built posts" \
  || (echo "❌ Related posts block missing — check layouts/partials/related_posts.html" && exit 1)

grep -rl "我要升官加薪系列" "${PUBLIC_DIR}/posts/2025-11-14-pe-1-pe-or-not/index.html" | grep -q . \
  && echo "✅ Series nav present on episodic post" \
  || (echo "❌ Series nav missing on PE post — check layouts/partials/series_nav.html" && exit 1)

EPISODE_TERM="${PUBLIC_DIR}/episodeseries/我要升官加薪/index.html"
[ -f "$EPISODE_TERM" ] || (echo "❌ Episode series term page missing: $EPISODE_TERM" && exit 1)
echo "✅ Episode series taxonomy term page built"

TAG_LIST="${PUBLIC_DIR}/tags/devops-工程師/index.html"
[ -f "$TAG_LIST" ] || (echo "❌ Tag list page not built: $TAG_LIST" && exit 1)

grep -q 'entry-header' "$TAG_LIST" \
  && echo "✅ Tag list page has entry-header (post titles)" \
  || (echo "❌ Tag list missing entry-header — check layouts/_default/list.html" && exit 1)

grep -q 'post-meta-enhanced' "$TAG_LIST" && grep -qv 'entry-header' "$TAG_LIST" \
  && (echo "❌ Tag list has orphan post-meta-enhanced without titles" && exit 1) \
  || echo "✅ Tag list layout OK"

if grep -rE 'src=\\?"?images/' "${PUBLIC_DIR}/posts/"*/index.html; then
  echo "❌ Unresolved image src in built HTML (PaperMod could not resolve bundle resource)"
  exit 1
fi
echo "✅ All post images resolved in built HTML"

SITEMAP="${PUBLIC_DIR}/sitemap.xml"
[ -f "$SITEMAP" ] || (echo "❌ sitemap.xml missing from ${PUBLIC_DIR}/" && exit 1)
if command -v xmllint &>/dev/null; then
  xmllint --noout "$SITEMAP" && echo "✅ sitemap.xml valid" \
    || (echo "❌ sitemap.xml invalid" && exit 1)
fi
grep -q '2025-10-04-goodbye-medium' "$SITEMAP" \
  && echo "✅ sitemap contains stable post slug" \
  || (echo "❌ sitemap missing stable post slug" && exit 1)

ROBOTS="${PUBLIC_DIR}/robots.txt"
[ -f "$ROBOTS" ] || (echo "❌ robots.txt missing from ${PUBLIC_DIR}/" && exit 1)
grep -qi 'Sitemap:' "$ROBOTS" \
  && echo "✅ robots.txt references sitemap" \
  || (echo "❌ robots.txt missing Sitemap directive" && exit 1)

PUBLIC_DIR="${PUBLIC_DIR}" python3 <<'PY'
from pathlib import Path
import os
import re
import sys

content = Path("content/posts")
public = Path(os.environ["PUBLIC_DIR"]) / "posts"
leaked = []
for md in sorted(content.glob("*/index.md")):
    text = md.read_text(encoding="utf-8")
    if re.search(r"^draft:\s*true\s*$", text, re.MULTILINE):
        slug = md.parent.name
        if (public / slug).exists():
            leaked.append(slug)
if leaked:
    print("❌ Draft posts leaked into public/:", ", ".join(leaked[:10]))
    if len(leaked) > 10:
        print(f"   ... and {len(leaked) - 10} more")
    sys.exit(1)
print("✅ No draft posts in public/")
PY

HTTP_HITS="$(grep -rE '(src|href)=\\?"http://' "${PUBLIC_DIR}" --include='*.html' --include='*.xml' 2>/dev/null || true)"
if [ -n "$HTTP_HITS" ]; then
  FILTERED="$(echo "$HTTP_HITS" | grep -vE \
    'googletagmanager\.com|google-analytics\.com|googleapis\.com|gstatic\.com|dashboard\.mailerlite\.com|donate\.stripe\.com|unpkg\.com|comments\.cloudarchitectec\.com|www\.w3\.org|schema\.org|xmlns|purl\.org|search\.yahoo\.com|creativecommons\.org|opensource\.org|gohugo\.io|github\.com/adityatelange|threads\.com|linkedin\.com|unsplash\.com|twitter\.com|facebook\.com' || true)"
  if [ -n "$FILTERED" ]; then
    echo "❌ Insecure http:// asset references in built output:"
    echo "$FILTERED" | head -20
    exit 1
  fi
fi
echo "✅ No unexpected http:// asset references"

echo "=== CHECKS DONE ==="
