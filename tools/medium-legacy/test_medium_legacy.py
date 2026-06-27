#!/usr/bin/env python3
"""Tests for medium_legacy_utils (no Playwright / Hugo fixtures)."""

from __future__ import annotations

import unittest
from pathlib import Path
import sys
import tempfile

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

import medium_legacy_utils as utils  # noqa: E402


class MediumLegacyUtilsTests(unittest.TestCase):
    def test_normalize_blog_url_fixes_en_dash(self):
        url = "https://cloudarchitectec.com/posts/2025\u201306\u201322-layoff"
        self.assertEqual(
            utils.normalize_blog_url(url),
            "https://cloudarchitectec.com/posts/2025-06-22-layoff/",
        )

    def test_render_banner_blockquote_format(self):
        banner = utils.render_banner(
            "倖存者日記：沒想到 2025 年還有續集？",
            "https://cloudarchitectec.com/posts/2025-06-22-layoff/",
            "> 請點此閱讀最新版本：[{medium_title}]({blog_url})",
        )
        self.assertTrue(banner.startswith("> 請點此閱讀最新版本："))
        self.assertIn("倖存者日記", banner)
        self.assertNotIn("**", banner)
        self.assertIn("2025-06-22-layoff", banner)

    def test_parse_canonical_url_from_link_tag(self):
        html = '<html><head><link rel="canonical" href="https://cloudarchitectec.com/posts/foo/"></head></html>'
        self.assertEqual(
            utils.parse_canonical_url(html),
            "https://cloudarchitectec.com/posts/foo/",
        )

    def test_parse_canonical_url_from_json_blob(self):
        html = '"canonicalUrl":"https:\\u002F\\u002Fcloudarchitectec.com\\u002Fposts\\u002Ffoo\\u002F"'
        self.assertEqual(
            utils.parse_canonical_url(html),
            "https://cloudarchitectec.com/posts/foo/",
        )

    def test_canonical_matches_normalizes_trailing_slash(self):
        html = '<link rel="canonical" href="https://cloudarchitectec.com/posts/foo">'
        self.assertTrue(
            utils.canonical_matches(html, "https://cloudarchitectec.com/posts/foo/")
        )

    def test_title_matches_rejects_banner_in_title_tag(self):
        html = (
            "<title>最新版本已移至自架部落格：[倖存者日記](url) | Medium</title>"
            "倖存者日記：沒想到 2025 年還有續集？"
        )
        self.assertFalse(
            utils.title_matches(html, "倖存者日記：沒想到 2025 年還有續集？當裁員成為澳洲科技業的新常態！")
        )

    def test_title_matches_accepts_clean_title_tag(self):
        html = "<title>倖存者日記：沒想到 2025 年還有續集？ | Medium</title>"
        self.assertTrue(
            utils.title_matches(html, "倖存者日記：沒想到 2025 年還有續集？")
        )
        self.assertTrue(
            utils.is_legacy_paragraph(
                "最新版本已移至自架部落格：[title](url)",
                "倖存者日記",
            )
        )
        self.assertTrue(
            utils.is_legacy_paragraph(
                "> 請點此閱讀最新版本：[倖存者日記 Q2](url)",
                "倖存者日記",
                "倖存者日記 Q2",
            )
        )
        self.assertFalse(
            utils.is_legacy_paragraph("這是正文開頭", "倖存者日記"),
        )

    def test_write_report_csv(self):
        row = utils.PostReportRow(
            post_title="Test",
            medium_link="https://medium.com/p/abc",
            blog_site_link="https://cloudarchitectec.com/posts/test/",
            status="ok",
            blog_url_ok=True,
            canonical_ok=True,
        )
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "report.csv"
            utils.write_report([row], csv_path)
            content = csv_path.read_text(encoding="utf-8")
            self.assertIn("post_title", content)
            self.assertIn("canonical_ok", content)
            self.assertIn("Test", content)

    def test_is_legacy_paragraph_detects_duplicate_title(self):
        medium = "倖存者日記：沒想到 2025 年還有續集？"
        blog = "倖存者日記：沒想到 2025 Q2 年還有續集？"
        self.assertTrue(utils.is_legacy_paragraph(blog, medium, blog))
        self.assertTrue(utils.is_legacy_paragraph(f"**{blog}**", medium, blog))

    def test_overall_status_partial_and_failed(self):
        partial = utils.PostReportRow(
            post_title="T",
            medium_link="m",
            blog_site_link="b",
            status="verified",
            blog_url_ok=True,
            canonical_ok=False,
            banner_ok=True,
            title_ok=True,
        )
        self.assertEqual(utils.overall_status(partial), "partial")
        failed = utils.PostReportRow(
            post_title="T",
            medium_link="m",
            blog_site_link="b",
            status="failed",
        )
        self.assertEqual(utils.overall_status(failed), "failed")


if __name__ == "__main__":
    unittest.main()
