#!/usr/bin/env python3
"""Unit tests for build_mapping helpers (run standalone; avoids Hugo test fixtures)."""

from __future__ import annotations

import unittest
from datetime import date
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
import build_mapping as bm  # noqa: E402
import update_medium_posts as ump  # noqa: E402


class BuildMappingTests(unittest.TestCase):
    def test_normalize_title_strips_emoji_and_colon_spacing(self):
        medium = "兩個女生的紐西蘭自駕滑雪行 🇳🇿: 2024.09.05–09.06 滑完雪就是要泡湯！"
        hugo = "兩個女生的紐西蘭自駕滑雪行: 2024.09.05–09.06 滑完雪就是要泡湯！療癒的 Rotorua 行程"
        self.assertIn(bm.normalize_title(medium), bm.normalize_title(hugo))

    def test_title_signature_extracts_episode_date(self):
        title = "太平洋小島上的大冒險：2025.04.26 Vanuatu Day 8 高級度假村午餐"
        self.assertEqual(bm.title_signature(title), "2025.04.26")

    def test_match_posts_uses_manual_override(self):
        medium = [
            bm.MediumPost(
                medium_id="38002a6cc46d",
                medium_url="https://medium.com/p/38002a6cc46d",
                medium_title="倖存者日記",
                published_at=date(2025, 6, 22),
            )
        ]
        hugo = [
            bm.HugoPost(
                slug="2025-06-22-layoff",
                blog_url="https://cloudarchitectec.com/posts/2025-06-22-layoff/",
                title="倖存者日記 Q2",
                published_at=date(2025, 6, 22),
                draft=False,
            )
        ]
        rows = bm.match_posts(medium, hugo, bm.load_manual_overrides(), True)
        self.assertEqual(rows[0]["blog_slug"], "2025-06-22-layoff")


    def test_render_banner_uses_medium_title(self):
        banner = ump.make_banner(
            "倖存者日記：沒想到 2025 年還有續集？",
            "https://cloudarchitectec.com/posts/2025-06-22-layoff/",
        )
        self.assertTrue(banner.startswith("> 請點此閱讀最新版本："))
        self.assertIn("倖存者日記", banner)
        self.assertNotIn("**", banner)
        self.assertIn("cloudarchitectec.com/posts/2025-06-22-layoff/", banner)


if __name__ == "__main__":
    unittest.main()
