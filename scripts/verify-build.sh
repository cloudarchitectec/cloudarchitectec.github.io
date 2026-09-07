#!/usr/bin/env bash
# Post-build checks for Hugo output. Used by PR CI and deploy workflow.
# Usage: PUBLIC_DIR=public ./scripts/verify-build.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=ensure-venv.sh
source "$SCRIPT_DIR/ensure-venv.sh"

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

grep -rl 'post-nudge--subscribe' "${PUBLIC_DIR}/posts/"*/index.html | head -1 | grep -q . \
  && echo "✅ Subscribe nudge present in posts" \
  || (echo "❌ Subscribe nudge not found — check partials/post-footer.html" && exit 1)

grep -q 'dashboard.mailerlite.com/jsonp/2459287/forms/190870271382520893/subscribe' "${PUBLIC_DIR}/index.html" \
  && echo "✅ MailerLite subscribe action present on homepage" \
  || (echo "❌ MailerLite subscribe action not found — check partials/home/newsletter.html" && exit 1)

grep -rl "related-posts" "${PUBLIC_DIR}/posts/"*/index.html | head -1 | grep -q . \
  && echo "✅ Related posts block present in built posts" \
  || (echo "❌ Related posts block missing — check layouts/partials/related_posts.html" && exit 1)

grep -rl "轉職工程師日記系列" "${PUBLIC_DIR}/posts/2019-08-29-how-to-position-yourself/index.html" | grep -q . \
  && echo "✅ Series nav present on episodic post" \
  || (echo "❌ Series nav missing on episodic post — check layouts/partials/series_nav.html" && exit 1)

EPISODE_TERM="${PUBLIC_DIR}/episodeseries/轉職工程師日記/index.html"
[ -f "$EPISODE_TERM" ] || (echo "❌ Episode series term page missing: $EPISODE_TERM" && exit 1)
echo "✅ Episode series taxonomy term page built"

PORTFOLIO_CAREER_ZH="${PUBLIC_DIR}/portfolio/career-zh/index.html"
PORTFOLIO_CAREER_EN="${PUBLIC_DIR}/portfolio/career-en/index.html"
PORTFOLIO_STORY="${PUBLIC_DIR}/portfolio/story/index.html"
PORTFOLIO_ROOT="${PUBLIC_DIR}/portfolio/index.html"

for page in "$PORTFOLIO_CAREER_ZH" "$PORTFOLIO_CAREER_EN" "$PORTFOLIO_STORY"; do
  [ -f "$page" ] || (echo "❌ Portfolio page missing: $page" && exit 1)
done
grep -q 'refresh' "$PORTFOLIO_ROOT" \
  && grep -q 'career-zh' "$PORTFOLIO_ROOT" \
  && echo "✅ Portfolio root redirects to career-zh" \
  || (echo "❌ Portfolio root missing redirect to career-zh" && exit 1)

grep -q 'cv-page' "$PORTFOLIO_CAREER_ZH" \
  && grep -q '大家好，我是 EC' "$PORTFOLIO_CAREER_ZH" \
  && grep -q 'Shell Energy Australia' "$PORTFOLIO_CAREER_ZH" \
  && grep -q 'cv-tags' "$PORTFOLIO_CAREER_ZH" \
  && grep -q '/consultation/' "$PORTFOLIO_CAREER_ZH" \
  && echo "✅ Portfolio career-zh page built" \
  || (echo "❌ Portfolio career-zh missing expected content" && exit 1)

grep -q '個人經歷' "$PORTFOLIO_STORY" \
  && grep -q '/consultation/' "$PORTFOLIO_STORY" \
  && echo "✅ Portfolio story page built" \
  || (echo "❌ Portfolio story missing expected content" && exit 1)

CONSULTATION_PAGE="${PUBLIC_DIR}/consultation/index.html"
[ -f "$CONSULTATION_PAGE" ] || (echo "❌ Consultation page missing: $CONSULTATION_PAGE" && exit 1)
grep -q 'consultation-hero' "$CONSULTATION_PAGE" \
  && grep -q 'consultation-testimonial-card' "$CONSULTATION_PAGE" \
  && grep -q 'Alison' "$CONSULTATION_PAGE" \
  && grep -q 'cal.com/cloudarchitectec/career-consultation' "$CONSULTATION_PAGE" \
  && echo "✅ Consultation landing page built" \
  || (echo "❌ Consultation page missing expected content" && exit 1)

CONSULTATION_ALIAS="${PUBLIC_DIR}/posts/2018-01-03-ec-consultation/index.html"
[ -f "$CONSULTATION_ALIAS" ] || (echo "❌ Consultation alias redirect missing" && exit 1)
grep -q 'consultation' "$CONSULTATION_ALIAS" \
  && echo "✅ Consultation alias redirect built" \
  || (echo "❌ Consultation alias redirect missing target" && exit 1)

grep -q '>Experience<' "$PORTFOLIO_CAREER_EN" \
  && echo "✅ Portfolio career-en page built" \
  || (echo "❌ Portfolio career-en missing expected content" && exit 1)

TAG_LIST="${PUBLIC_DIR}/tags/devops-工程師/index.html"
[ -f "$TAG_LIST" ] || (echo "❌ Tag list page not built: $TAG_LIST" && exit 1)

grep -q 'entry-header' "$TAG_LIST" \
  && echo "✅ Tag list page has entry-header (post titles)" \
  || (echo "❌ Tag list missing entry-header — check layouts/_default/list.html" && exit 1)

if grep -q 'post-meta-enhanced' "$TAG_LIST" && ! grep -q 'entry-header' "$TAG_LIST"; then
  echo "❌ Tag list has orphan post-meta-enhanced without titles"
  exit 1
else
  echo "✅ Tag list layout OK"
fi

if grep -rE '<img[^>]*[[:space:]]src=\\?"?images/' "${PUBLIC_DIR}/posts/"*/index.html; then
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

PUBLIC_DIR="${PUBLIC_DIR}" "$VENV_PYTHON" <<'PY'
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
    'googletagmanager\.com|google-analytics\.com|googleapis\.com|gstatic\.com|dashboard\.mailerlite\.com|donate\.stripe\.com|buy\.stripe\.com|unpkg\.com|comments\.cloudarchitectec\.com|www\.w3\.org|schema\.org|xmlns|purl\.org|search\.yahoo\.com|creativecommons\.org|opensource\.org|gohugo\.io|github\.com/adityatelange|threads\.com|linkedin\.com|unsplash\.com|twitter\.com|facebook\.com' || true)"
  if [ -n "$FILTERED" ]; then
    echo "❌ Insecure http:// asset references in built output:"
    echo "$FILTERED" | head -20
    exit 1
  fi
fi
echo "✅ No unexpected http:// asset references"

echo "=== CHECKS DONE ==="
