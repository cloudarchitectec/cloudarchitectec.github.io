"""Editorial rules that can alter published prose."""

from __future__ import annotations

from conftest import load_repo_module

spellcheck = load_repo_module("scripts/check-spelling.py")


def amount_fix(text: str) -> str:
    changes: list = []
    text = spellcheck.apply_zh_fixes(text, fix=True, changes=changes)
    text = spellcheck.apply_currency_zh(text, fix=True, changes=changes)
    text = spellcheck.apply_cjk_latin_spacing(text, fix=True, changes=changes)
    text = spellcheck.apply_zh_fixes_after_spacing(text, fix=True, changes=changes)
    return spellcheck.apply_chinese_amount_format(text, fix=True, changes=changes)


def emphasis_fix(text: str) -> str:
    return spellcheck.apply_emphasis_hygiene(text, fix=True, changes=[], flags=[])


def test_amounts_are_spaced_without_breaking_colloquial_amounts():
    assert "22.5 萬澳幣" in amount_fix("22.5萬澳幣")
    assert "約 450 萬台幣" in amount_fix("約450萬台幣")
    assert "澳幣六萬五" in amount_fix("澳幣 6 萬 5")


def test_bold_amounts_and_english_are_unwrapped():
    assert emphasis_fix("一間 **house** 的頭期款") == "一間 house 的頭期款"
    assert emphasis_fix("**20% 的頭期款**") == "20% 的頭期款"


def test_rhetorical_bold_becomes_chinese_quotes():
    assert emphasis_fix("而是：**要怎麼存出二十幾萬澳幣現金？**") == "而是：「要怎麼存出二十幾萬澳幣現金？」"


def test_bold_list_labels_followed_by_full_width_colon_are_preserved():
    original = "1. **有收據不代表就會全額獲賠**：仍可能扣除折舊。"
    assert emphasis_fix(original) == original
