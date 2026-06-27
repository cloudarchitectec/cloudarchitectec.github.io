"""Spellcheck emphasis hygiene — **bold** vs 「」 in Chinese prose."""

from __future__ import annotations

from conftest import load_repo_module

spellcheck = load_repo_module(
    ".cursor/skills/ec-blog-spellcheck/scripts/check-spelling.py"
)


def _emphasis_fix(text: str) -> str:
    changes: list = []
    flags: list = []
    return spellcheck.apply_emphasis_hygiene(text, fix=True, changes=changes, flags=flags)


class TestEmphasisHygiene:
    def test_unwraps_english_and_amounts(self):
        assert _emphasis_fix("一間 **house** 的頭期款") == "一間 house 的頭期款"
        assert _emphasis_fix("在 **Brisbane** 要 **12.9 年**") == "在 Brisbane 要 12.9 年"
        assert (
            _emphasis_fix("**22.5 萬澳幣 (約 450 萬台幣)**")
            == "22.5 萬澳幣 (約 450 萬台幣)"
        )
        assert _emphasis_fix("**20% 的頭期款**") == "20% 的頭期款"

    def test_short_keyword_unwrapped_not_guillemet(self):
        assert _emphasis_fix("改用**家庭收入**當基準") == "改用家庭收入當基準"

    def test_rhetorical_bold_becomes_guillemets(self):
        assert (
            _emphasis_fix("而是：**要怎麼存出二十幾萬澳幣現金？**")
            == "而是：「要怎麼存出二十幾萬澳幣現金？」"
        )
        assert (
            _emphasis_fix("連 **入場券（頭期款）** 都還在存")
            == "連「入場券（頭期款）」都還在存"
        )
