"""Spellcheck amount spacing — Arabic 萬 amounts stay spaced."""

from __future__ import annotations

from conftest import load_repo_module

spellcheck = load_repo_module(
    ".cursor/skills/ec-blog-spellcheck/scripts/check-spelling.py"
)


def _zh_fix(text: str) -> str:
    changes: list = []
    text = spellcheck.apply_zh_fixes(text, fix=True, changes=changes)
    text = spellcheck.apply_currency_zh(text, fix=True, changes=changes)
    text = spellcheck.apply_cjk_latin_spacing(text, fix=True, changes=changes)
    text = spellcheck.apply_zh_fixes_after_spacing(text, fix=True, changes=changes)
    return spellcheck.apply_chinese_amount_format(text, fix=True, changes=changes)


class TestAmountSpacing:
    def test_adds_space_before_wan(self):
        assert "22.5 萬澳幣" in _zh_fix("22.5萬澳幣")
        assert "9.3 萬澳幣" in _zh_fix("9.3萬澳幣")

    def test_adds_spaces_around_yue_taiwan(self):
        assert "約 450 萬台幣" in _zh_fix("約450萬台幣")
        assert "約 186 萬台幣" in _zh_fix("(約186萬台幣)")

    def test_does_not_compact_spaced_amounts(self):
        original = "22.5 萬澳幣 (約 450 萬台幣)"
        assert _zh_fix(original) == original

    def test_colloquial_wan_stays_compact(self):
        assert "澳幣六萬五" in _zh_fix("澳幣 6 萬 5")
        assert "五萬六台幣" in _zh_fix("5 萬 6 台幣")
