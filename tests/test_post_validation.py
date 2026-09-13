"""Core guardrails for published Hugo post bundles."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from conftest import cover_check, frontmatter_check, size_check

UNSPLASH_FM = '''cover:
  image: "images/abc123-unsplash.jpg"
  alt: "A descriptive cover image"
  credit:
    photographer: "Jane Doe"
    photographer_url: "https://unsplash.com/@jane"
    photo_url: "https://unsplash.com/photos/test-abc123"
images: ["images/abc123-unsplash.jpg"]'''

GOOD_POST = f'''---
title: "Test post"
date: 2025-01-01
slug: "test-slug"
{UNSPLASH_FM}
categories: ["澳洲職場"]
---

Body content here.
'''


def wrap(front_matter: str, body: str = "Content.") -> str:
    return f"---\n{front_matter}\n---\n\n{body}"


def test_valid_published_post_passes_all_core_rules():
    assert frontmatter_check.check(GOOD_POST, "test-slug") == []
    assert cover_check.check(GOOD_POST) == []


@pytest.mark.parametrize(
    ("text", "directory", "expected"),
    [
        (GOOD_POST.replace('title: "Test post"\n', ""), "test-slug", "title"),
        (GOOD_POST, "wrong-slug", "slug must match"),
        (GOOD_POST.replace('categories: ["澳洲職場"]\n', ""), "test-slug", "categories"),
        (wrap('title: "Published"\ndate: 2025-01-01\nslug: "published"'), "published", "cover.image"),
    ],
)
def test_required_post_metadata_is_enforced(text: str, directory: str, expected: str):
    assert any(expected in error for error in frontmatter_check.check(text, directory))


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (GOOD_POST.replace('  alt: "A descriptive cover image"\n', ""), "cover.alt"),
        (GOOD_POST.replace('images: ["images/abc123-unsplash.jpg"]', "images: []"), "images:"),
        (GOOD_POST.replace('https://unsplash.com/photos/test-abc123', 'https://unsplash.com'), "photo_url"),
    ],
)
def test_cover_attribution_and_reference_are_enforced(text: str, expected: str):
    assert any(expected in error for error in cover_check.check(text))


def test_bundle_images_handle_captions_modifiers_and_orphans(tmp_path: Path):
    images = tmp_path / "images"
    images.mkdir()
    for name in ("cover.jpg", "inline.jpg", "orphan.jpg"):
        (images / name).write_bytes(b"image")
    post = tmp_path / "index.md"
    post.write_text(
        wrap(
            'title: "x"\nimages: ["images/cover.jpg"]',
            '![inline](images/inline.jpg#portrait "caption")',
        ),
        encoding="utf-8",
    )
    assert cover_check.extract_image_paths(post.read_text(encoding="utf-8")) == ["images/inline.jpg"]
    assert cover_check.find_orphan_images(post) == ["images/orphan.jpg"]


def test_image_hard_limit_and_cover_encoding_are_checked(tmp_path: Path):
    oversized = tmp_path / "oversized.jpg"
    Image.new("RGB", (4500, 3000), color="blue").save(oversized, quality=90)
    info = size_check.read_image_info(oversized)
    assert info is not None
    _, errors = size_check.check_info(info, "cover")
    assert any("hard limit" in error for error in errors)

    progressive = tmp_path / "progressive.jpg"
    Image.new("RGB", (800, 600), color="red").save(progressive, progressive=True)
    changed, _ = size_check.normalize_jpeg_baseline(progressive)
    assert changed and not size_check.is_progressive_jpeg(progressive)
