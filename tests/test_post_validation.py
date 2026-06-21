"""Tests for scripts/post-validation/."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

from conftest import cover_check, frontmatter_check, size_check
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECK_POSTS_PATH = REPO_ROOT / "scripts" / "check-posts.py"


def load_check_posts():
    spec = importlib.util.spec_from_file_location("check_posts", CHECK_POSTS_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {CHECK_POSTS_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

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
"""


def wrap(fm_body: str, body: str | None = None) -> str:
    if body is None:
        body = "Content."
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

    def test_legacy_footer_shortcode_rejected(self):
        text = GOOD_POST + "\n\n{{{{< footer >}}}}"
        assert any("footer" in e for e in frontmatter_check.check(text, "test-slug"))

    def test_landing_page_passes(self):
        text = wrap(
            'title: "List"\ndate: 2018-01-02\nslug: "2018-01-02-ec-post-list"\n'
            'cover:\n  image: "images/x.jpg"\n  alt: "x"\nimages: ["images/x.jpg"]',
            body=f"{{{{< categorized-posts >}}}}",
        )
        assert frontmatter_check.check(text, "2018-01-02-ec-post-list") == []

    def test_draft_without_cover_passes(self):
        text = wrap(
            'title: "Draft"\ndate: 2025-01-01\nslug: "draft-post"\ndraft: true',
            body="No cover.",
        )
        assert frontmatter_check.check(text, "draft-post") == []

    def test_published_without_cover_rejected(self):
        text = wrap(
            'title: "Pub"\ndate: 2025-01-01\nslug: "pub-post"',
            body="No cover.",
        )
        assert any("cover.image" in e for e in frontmatter_check.check(text, "pub-post"))

    def test_unquoted_title_passes(self):
        text = GOOD_POST.replace('title: "Test post"', "title: 中文標題 without quotes")
        assert not any("title" in e for e in frontmatter_check.check(text, "test-slug"))


class TestCheckPostsGitPaths:
    def test_git_index_paths_match_slug_dirs(self):
        check_posts = load_check_posts()
        entries = check_posts.list_post_entries_from_git()
        assert entries

        git_dirs = subprocess.run(
            ["git", "ls-files", "--", "content/posts/"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        expected = sorted(
            {
                Path(line).parts[2]
                for line in git_dirs.stdout.splitlines()
                if line.endswith("/index.md")
            }
        )
        assert [dir_name for _, dir_name in entries] == expected

    def test_slug_mismatch_detected_with_git_dir_name(self):
        check_posts = load_check_posts()
        md_file, dir_name = check_posts.resolve_post_path("2019-08-19-coding-bootcamp-orientation")
        text = md_file.read_text(encoding="utf-8")
        assert dir_name == "2019-08-19-coding-bootcamp-orientation"
        assert frontmatter_check.check(text, dir_name) == []


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


class TestProgressiveJpeg:
    def test_is_progressive_jpeg_detects_encoding(self, tmp_path: Path):
        baseline = tmp_path / "baseline.jpg"
        progressive = tmp_path / "progressive.jpg"
        img = Image.new("RGB", (400, 300), color="red")
        img.save(baseline, format="JPEG", quality=85, progressive=False)
        img.save(progressive, format="JPEG", quality=85, progressive=True)
        assert not size_check.is_progressive_jpeg(baseline)
        assert size_check.is_progressive_jpeg(progressive)

    def test_normalize_jpeg_baseline_converts_progressive(self, tmp_path: Path):
        path = tmp_path / "cover.jpg"
        Image.new("RGB", (800, 600), color="blue").save(
            path, format="JPEG", quality=85, progressive=True
        )
        changed, msg = size_check.normalize_jpeg_baseline(path)
        assert changed
        assert "baseline" in msg
        assert not size_check.is_progressive_jpeg(path)

    def test_check_info_warns_progressive_cover(self, tmp_path: Path):
        path = tmp_path / "hero.jpg"
        Image.new("RGB", (1400, 900), color="orange").save(
            path, format="JPEG", quality=85, progressive=True
        )
        info = size_check.read_image_info(path)
        assert info is not None
        warnings, errors = size_check.check_info(info, "cover")
        assert not errors
        assert any("progressive JPEG" in w for w in warnings)
