"""Tests for scripts/post-validation/."""

from __future__ import annotations

from pathlib import Path

from conftest import cover_check, frontmatter_check, size_check
from PIL import Image

UNSPLASH_FM = """\
cover:
  image: "images/abc123-unsplash.jpg"
  alt: "test alt"
  credit:
    photographer: "Jane Doe"
    photographer_url: "https://unsplash.com/@jane"
    photo_url: "https://unsplash.com/photos/test-abc123"
images: ["images/abc123-unsplash.jpg"]
"""

GOOD_POST = f"""\
---
title: "Test post"
date: 2025-01-01
slug: "test-slug"
{UNSPLASH_FM}
categories: ["海外職場"]
---

Body content here.

{{{{< footer >}}}}
"""


def wrap(fm_body: str, body: str | None = None) -> str:
    if body is None:
        body = f"Content.\n\n{{{{< footer >}}}}"
    return f"---\n{fm_body}\n---\n\n{body}"


class TestCoverCheck:
    def test_good_unsplash_cover_passes(self):
        assert cover_check.check(wrap(f"title: x\ndate: 2025-01-01\nslug: s\n{UNSPLASH_FM}")) == []

    def test_root_image_rejected(self):
        text = wrap('title: x\ndate: 2025-01-01\nslug: s\nimage: "images/x.jpg"')
        assert any("root image:" in e for e in cover_check.check(text))

    def test_missing_alt_rejected(self):
        fm = UNSPLASH_FM.replace('  alt: "test alt"\n', "")
        assert any("cover.alt" in e for e in cover_check.check(wrap(fm)))

    def test_generic_unsplash_url_rejected(self):
        fm = UNSPLASH_FM.replace(
            '    photo_url: "https://unsplash.com/photos/test-abc123"',
            '    photo_url: "https://unsplash.com"',
        )
        assert any("photo_url" in e for e in cover_check.check(wrap(fm)))

    def test_cover_not_in_images_rejected(self):
        fm = UNSPLASH_FM.replace(
            'images: ["images/abc123-unsplash.jpg"]',
            "images: []",
        )
        assert any("images:" in e for e in cover_check.check(wrap(fm)))


class TestFrontmatterCheck:
    def test_good_post_passes(self):
        assert frontmatter_check.check(GOOD_POST, "test-slug") == []

    def test_missing_title_rejected(self):
        text = GOOD_POST.replace('title: "Test post"\n', "")
        assert any("title" in e for e in frontmatter_check.check(text, "test-slug"))

    def test_slug_mismatch_rejected(self):
        assert any("slug must match" in e for e in frontmatter_check.check(GOOD_POST, "wrong-dir"))

    def test_missing_footer_rejected(self):
        text = GOOD_POST.replace("{{< footer >}}", "")
        assert any("footer" in e for e in frontmatter_check.check(text, "test-slug"))

    def test_landing_page_without_footer_passes(self):
        text = wrap(
            'title: "List"\ndate: 2018-01-02\nslug: "2018-01-02-ec-post-list"\n'
            'cover:\n  image: "images/x.jpg"\n  alt: "x"\nimages: ["images/x.jpg"]',
            body=f"{{{{< categorized-posts >}}}}",
        )
        assert frontmatter_check.check(text, "2018-01-02-ec-post-list") == []

    def test_draft_without_cover_passes(self):
        text = wrap(
            'title: "Draft"\ndate: 2025-01-01\nslug: "draft-post"\ndraft: true',
            body=f"No cover.\n\n{{{{< footer >}}}}",
        )
        assert frontmatter_check.check(text, "draft-post") == []

    def test_published_without_cover_rejected(self):
        text = wrap(
            'title: "Pub"\ndate: 2025-01-01\nslug: "pub-post"',
            body=f"No cover.\n\n{{{{< footer >}}}}",
        )
        assert any("cover.image" in e for e in frontmatter_check.check(text, "pub-post"))

    def test_unquoted_title_passes(self):
        text = GOOD_POST.replace('title: "Test post"', "title: 中文標題 without quotes")
        assert not any("title" in e for e in frontmatter_check.check(text, "test-slug"))


class TestImageSizeCheck:
    def test_soft_warn_large_inline(self, tmp_path: Path):
        img = tmp_path / "big.jpg"
        Image.new("RGB", (2500, 1200), color="red").save(img, quality=95)
        info = size_check.read_image_info(img)
        assert info is not None
        warnings, errors = size_check.check_info(info, "inline")
        assert warnings
        assert not errors

    def test_hard_error_oversized(self, tmp_path: Path):
        img = tmp_path / "huge.jpg"
        Image.new("RGB", (4500, 3000), color="blue").save(img, quality=95)
        info = size_check.read_image_info(img)
        assert info is not None
        warnings, errors = size_check.check_info(info, "cover")
        assert errors
        assert any("hard limit" in e for e in errors)

    def test_optimize_reduces_file(self, tmp_path: Path):
        img = tmp_path / "big.jpg"
        Image.new("RGB", (3000, 2000), color="green").save(img, quality=95)
        before = img.stat().st_size
        changed, _ = size_check.optimize_image(img, "inline")
        assert changed
        assert img.stat().st_size < before
        info = size_check.read_image_info(img)
        assert info is not None
        assert info.long_edge <= size_check.OPTIMIZE_INLINE_LONG_EDGE
