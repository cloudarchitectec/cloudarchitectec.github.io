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


def extract_content(html: str, prop_attr: str, prop_value: str) -> str | None:
    """Return the content="" of a <meta {prop_attr}="{prop_value}"> tag."""
    patterns = [
        rf'<meta[^>]+{prop_attr}=["\']?{re.escape(prop_value)}["\']?[^>]+content=["\']?([^"\'\s>]+)',
        rf'<meta[^>]+content=["\']?([^"\'\s>]+)["\']?[^>]+{prop_attr}=["\']?{re.escape(prop_value)}["\']?',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def assert_social_image_resolves(built_site: Path, url: str, label: str) -> None:
    """A social-image URL must be an absolute bundle URL whose file exists on disk.

    Guards the class of bug where cover.image (a page-bundle path like
    "images/x.jpg") is resolved against the SITE ROOT, yielding
    https://site/images/x.jpg — a 404 that kills link-preview thumbnails on
    Threads/Facebook/X. Checking the built file exists catches ANY mis-resolved
    cover path, not just the site-root shape. See templates/_funcs/
    resolve-cover-image.html.
    """
    assert url and url.startswith(BASE + "/"), (
        f"{label} must be an absolute {BASE} URL, got: {url!r}"
    )
    rel = url[len(BASE) + 1 :]
    assert (built_site / rel).is_file(), (
        f"{label} points to {url} but {rel} does not exist in the build output "
        f"(would 404 for social crawlers)"
    )


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

    def test_cover_post_social_images_resolve(self, built_site):
        """og:image / twitter:image / JSON-LD image must be bundle URLs that
        actually exist on disk — a substring match on the filename is not
        enough (a site-root 404 path contains the same filename). Regression
        guard for the Threads/Facebook thumbnail bug."""
        html = (built_site / COVER_POST).read_text(encoding="utf-8")
        og = extract_content(html, "property", "og:image")
        tw = extract_content(html, "name", "twitter:image")
        assert og, "cover post must have og:image"
        assert tw, "cover post must have twitter:image"
        assert_social_image_resolves(built_site, og, "og:image")
        assert_social_image_resolves(built_site, tw, "twitter:image")

        # JSON-LD BlogPosting image (schema_json.html) must match, not 404.
        ld = re.search(r'"image"\s*:\s*"([^"]+)"', html)
        assert ld, "cover post JSON-LD must include an image"
        assert_social_image_resolves(built_site, ld.group(1), "JSON-LD image")

        # All three must agree — no split between a working og and a broken LD.
        assert og == tw == ld.group(1), (
            f"social images disagree: og={og} twitter={tw} jsonld={ld.group(1)}"
        )

    def test_home_has_canonical(self, built_site):
        html = (built_site / HOME).read_text(encoding="utf-8")
        canonical = extract_meta(html, "rel", "canonical")
        assert canonical in (f"{BASE}/", BASE)
