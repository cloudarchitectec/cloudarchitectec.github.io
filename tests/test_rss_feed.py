"""RSS feed checks — standard index.xml and MailerLite index-mailerlite.xml."""

from __future__ import annotations

import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RSS_PATH = REPO_ROOT / "public" / "index.xml"
MAILERLITE_RSS_PATH = REPO_ROOT / "public" / "index-mailerlite.xml"
NS = {
    "media": "http://search.yahoo.com/mrss/",
    "content": "http://purl.org/rss/1.0/modules/content/",
}


def hugo_available() -> bool:
    return shutil.which("hugo") is not None


@pytest.fixture(scope="module")
def built_feeds():
    if not hugo_available():
        pytest.skip("hugo not installed")
    result = subprocess.run(
        ["hugo", "--gc", "--minify", "--cleanDestinationDir"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"hugo build failed:\n{result.stdout}\n{result.stderr}")
    return {
        "standard": RSS_PATH.read_text(encoding="utf-8"),
        "mailerlite": MAILERLITE_RSS_PATH.read_text(encoding="utf-8"),
    }


def item_for_slug(rss_text: str, slug: str) -> ET.Element | None:
    root = ET.fromstring(rss_text)
    channel = root.find("channel")
    assert channel is not None
    for item in channel.findall("item"):
        link = item.findtext("link") or ""
        if slug in link:
            return item
    return None


def first_img_src(description: str) -> str | None:
    match = re.search(r'src="([^"]+)"', description)
    return match.group(1) if match else None


class TestStandardRss:
    def test_retirement_post_has_media_content_for_cover(self, built_feeds):
        """Standard feed exposes cover.image as media:content for feed readers."""
        item = item_for_slug(built_feeds["standard"], "2026-06-17-retirement-plan")
        assert item is not None, "retirement-plan item missing from index.xml"
        media = item.find("media:content", NS)
        assert media is not None, "expected media:content for cover.image post"
        url = media.get("url") or ""
        assert "cEukkv42O40-unsplash" in url, f"unexpected cover URL: {url}"
        assert "/posts/2026-06-17-retirement-plan/" in url, f"cover must be post bundle URL, got: {url}"
        assert url.startswith("http"), url

    def test_standard_feed_does_not_inject_cover_into_description(self, built_feeds):
        """index.xml stays clean — no hero img in excerpt."""
        item = item_for_slug(built_feeds["standard"], "2026-06-17-retirement-plan")
        assert item is not None
        desc = item.findtext("description") or ""
        assert first_img_src(desc) is None


class TestMailerLiteRss:
    def test_mailerlite_feed_exists(self, built_feeds):
        assert "index-mailerlite" in built_feeds["mailerlite"]

    def test_retirement_cover_is_first_img_with_absolute_url(self, built_feeds):
        """MailerLite reads first body-style img — cover after first paragraph, with dimensions."""
        item = item_for_slug(built_feeds["mailerlite"], "2026-06-17-retirement-plan")
        assert item is not None
        desc = item.findtext("description") or ""
        src = first_img_src(desc)
        assert src is not None, "expected cover img in MailerLite description"
        assert src.startswith("https://cloudarchitectec.com/posts/2026-06-17-retirement-plan/images/")
        assert "cEukkv42O40-unsplash" in src
        assert "width=" in desc and "height=" in desc
        assert desc.index("<p>") < desc.index("<img"), "cover img should follow opening paragraph text"

    def test_sydney_cover_precedes_body_images(self, built_feeds):
        """Cover hero should appear before inline spirits.jpg in MailerLite feed."""
        item = item_for_slug(built_feeds["mailerlite"], "2026-05-17-sydney-mca")
        assert item is not None
        desc = item.findtext("description") or ""
        src = first_img_src(desc)
        assert src is not None
        assert "ZsH1wHv2iTU-unsplash" in src, f"expected cover hero first, got: {src}"
        assert "spirits.jpg" not in desc[: desc.index("<img") + 1], "spirits must not precede cover"

    def test_posts_with_cover_have_media_content(self, built_feeds):
        for slug in ("2026-06-17-retirement-plan", "2026-05-17-sydney-mca"):
            item = item_for_slug(built_feeds["mailerlite"], slug)
            assert item is not None, slug
            assert item.find("media:content", NS) is not None, slug
