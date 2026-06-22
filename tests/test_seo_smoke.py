"""SEO meta smoke on built HTML — canonical URLs and social cover tags."""

from __future__ import annotations

import re
from pathlib import Path

STABLE_POST = Path("posts/2025-10-04-goodbye-medium/index.html")
COVER_POST = Path("posts/2026-06-17-retirement-plan/index.html")
HOME = Path("index.html")
BASE = "https://cloudarchitectec.com"


def extract_meta(html: str, attr: str, value: str) -> str | None:
    patterns = [
        rf'<link[^>]+{attr}=["\']?{re.escape(value)}["\']?[^>]+href=["\']?([^"\'\s>]+)',
        rf'<link[^>]+href=["\']?([^"\'\s>]+)[^>]+{attr}=["\']?{re.escape(value)}["\']?',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def extract_title(html: str) -> str | None:
    match = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
    return match.group(1).strip() if match else None


class TestSeoSmoke:
    def test_stable_post_has_canonical_and_title(self, built_site):
        html = (built_site / STABLE_POST).read_text(encoding="utf-8")
        canonical = extract_meta(html, "rel", "canonical")
        assert canonical == f"{BASE}/posts/2025-10-04-goodbye-medium/"
        title = extract_title(html)
        assert title and "Medium" in title

    def test_cover_post_has_social_image(self, built_site):
        html = (built_site / COVER_POST).read_text(encoding="utf-8")
        assert re.search(
            r'property=["\']?og:image["\']?[^>]+content=["\']?[^"\'\s>]+cEukkv42O40-unsplash',
            html,
            re.IGNORECASE,
        ) or re.search(
            r'name=["\']?twitter:image["\']?[^>]+content=["\']?[^"\'\s>]+cEukkv42O40-unsplash',
            html,
            re.IGNORECASE,
        ), "cover post should expose og:image or twitter:image"

    def test_home_has_canonical(self, built_site):
        html = (built_site / HOME).read_text(encoding="utf-8")
        canonical = extract_meta(html, "rel", "canonical")
        assert canonical in (f"{BASE}/", BASE)
