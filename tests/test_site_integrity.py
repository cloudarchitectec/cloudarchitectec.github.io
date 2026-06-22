"""Built-site integrity: sitemap depth, domain hygiene, future-post leakage."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import pytest

from conftest import frontmatter_check

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTENT_POSTS = REPO_ROOT / "content/posts"
BASE_URL = "https://cloudarchitectec.com/"


def published_post_slugs() -> list[str]:
    slugs: list[str] = []
    for md in sorted(CONTENT_POSTS.glob("*/index.md")):
        fm, _ = frontmatter_check.split_post(md.read_text(encoding="utf-8"))
        if frontmatter_check.is_draft(fm):
            continue
        slugs.append(md.parent.name)
    return slugs


def future_post_slugs() -> list[str]:
    now = datetime.now(timezone.utc)
    slugs: list[str] = []
    for md in sorted(CONTENT_POSTS.glob("*/index.md")):
        fm, _ = frontmatter_check.split_post(md.read_text(encoding="utf-8"))
        if frontmatter_check.is_draft(fm):
            continue
        raw = frontmatter_check.get_fm_scalar(fm, "date") or frontmatter_check.get_fm_scalar(
            fm, "publishDate"
        )
        if not raw:
            continue
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if dt > now:
            slugs.append(md.parent.name)
    return slugs


def sitemap_locs(built_site: Path) -> list[str]:
    text = (built_site / "sitemap.xml").read_text(encoding="utf-8")
    root = ET.fromstring(text)
    return [el.text for el in root.iter() if el.tag.endswith("loc") and el.text]


class TestSiteIntegrity:
    def test_sitemap_url_count_matches_published_posts(self, built_site):
        locs = sitemap_locs(built_site)
        published = len(published_post_slugs())
        post_urls = [loc for loc in locs if "/posts/" in loc]
        assert len(post_urls) >= published, (
            f"sitemap has {len(post_urls)} post URLs but {published} published posts exist"
        )

    def test_sitemap_uses_production_domain(self, built_site):
        locs = sitemap_locs(built_site)
        assert locs, "sitemap should contain URLs"
        bad = [loc for loc in locs if "github.io" in loc or not loc.startswith(BASE_URL)]
        assert not bad, f"sitemap contains non-production URLs: {bad[:5]}"

    def test_no_future_posts_in_public(self, built_site):
        public_posts = built_site / "posts"
        for slug in future_post_slugs():
            assert not (public_posts / slug).exists(), (
                f"future-dated post {slug} should not be published (buildFuture=false)"
            )
