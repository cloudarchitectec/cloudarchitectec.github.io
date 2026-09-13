"""Rendered-output checks not already covered by verify-build.sh."""

from __future__ import annotations

import re
from pathlib import Path

from conftest import load_repo_module

check_internal_links = load_repo_module("scripts/check-internal-links.py")
BASE_URL = "https://cloudarchitectec.com"
COVER_POST = Path("posts/2026-06-17-retirement-plan/index.html")


def meta_content(html: str, attribute: str, value: str) -> str | None:
    patterns = [
        rf'<meta[^>]+{attribute}=["\']?{re.escape(value)}["\']?[^>]+content=["\']?([^"\'\s>]+)',
        rf'<meta[^>]+content=["\']?([^"\'\s>]+)["\']?[^>]+{attribute}=["\']?{re.escape(value)}["\']?',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def test_rendered_links_resolve_and_external_urls_are_well_formed(built_site: Path):
    assert not check_internal_links.scan_public(built_site, limit=20)
    _, malformed, external_count = check_internal_links.scan_links(built_site, limit=20)
    assert not malformed and external_count > 0


def test_cover_social_images_resolve_to_the_post_bundle(built_site: Path):
    html = (built_site / COVER_POST).read_text(encoding="utf-8")
    urls = [
        meta_content(html, "property", "og:image"),
        meta_content(html, "name", "twitter:image"),
    ]
    json_ld = re.search(r'"image"\s*:\s*"([^"]+)"', html)
    assert json_ld is not None
    urls.append(json_ld.group(1))
    assert all(url and url.startswith(f"{BASE_URL}/posts/") for url in urls)
    assert len(set(urls)) == 1
    output_path = built_site / urls[0].removeprefix(f"{BASE_URL}/")
    assert output_path.is_file()
