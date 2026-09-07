"""Spellcheck — Chinese amount spacing and emphasis hygiene."""

from __future__ import annotations

from types import SimpleNamespace

from conftest import load_repo_module

spellcheck = load_repo_module("scripts/check-spelling.py")


def _zh_amount_fix(text: str) -> str:
    changes: list = []
    text = spellcheck.apply_zh_fixes(text, fix=True, changes=changes)
    text = spellcheck.apply_currency_zh(text, fix=True, changes=changes)
    text = spellcheck.apply_cjk_latin_spacing(text, fix=True, changes=changes)
    text = spellcheck.apply_zh_fixes_after_spacing(text, fix=True, changes=changes)
    return spellcheck.apply_chinese_amount_format(text, fix=True, changes=changes)


def _emphasis_fix(text: str) -> str:
    changes: list = []
    flags: list = []
    return spellcheck.apply_emphasis_hygiene(text, fix=True, changes=changes, flags=flags)


class TestAmountSpacing:
    def test_adds_space_before_wan(self):
        assert "22.5 萬澳幣" in _zh_amount_fix("22.5萬澳幣")
        assert "9.3 萬澳幣" in _zh_amount_fix("9.3萬澳幣")

    def test_adds_spaces_around_yue_taiwan(self):
        assert "約 450 萬台幣" in _zh_amount_fix("約450萬台幣")
        assert "約 186 萬台幣" in _zh_amount_fix("(約186萬台幣)")

    def test_does_not_compact_spaced_amounts(self):
        original = "22.5 萬澳幣 (約 450 萬台幣)"
        assert _zh_amount_fix(original) == original

    def test_colloquial_wan_stays_compact(self):
        assert "澳幣六萬五" in _zh_amount_fix("澳幣 6 萬 5")
        assert "五萬六台幣" in _zh_amount_fix("5 萬 6 台幣")

    def test_preserves_grammatical_mu_di_de(self):
        assert _zh_amount_fix("以放鬆為目的的旅行") == "以放鬆為目的的旅行"


class TestAudTwdEquivalents:
    def test_aud_amount_requires_twd_equivalent(self):
        flags = spellcheck.find_aud_twd_equivalent_flags("住宿是 $535 澳幣。")
        assert len(flags) == 1
        assert flags[0].text == "$535 澳幣"

    def test_aud_amount_with_twd_equivalent_passes(self):
        flags = spellcheck.find_aud_twd_equivalent_flags(
            "住宿是 $535 澳幣（約 10,700 台幣）。"
        )
        assert flags == []

    def test_aud_prefix_form_requires_twd_equivalent(self):
        flags = spellcheck.find_aud_twd_equivalent_flags("住宿是澳幣 $535。")
        assert len(flags) == 1

    def test_rule_applies_only_from_adoption_date(self):
        assert not spellcheck.requires_aud_twd_equivalent("date: 2026-08-22\n")
        assert spellcheck.requires_aud_twd_equivalent("date: 2026-09-06\n")

    def test_strict_mode_ignores_legacy_but_blocks_new_style_issues(self, tmp_path):
        change = spellcheck.Change(line=1, before="traveling", after="travelling", lang="en")
        legacy = spellcheck.FileResult(path=tmp_path / "legacy.md", changes=[change])
        current = spellcheck.FileResult(
            path=tmp_path / "current.md", changes=[change], enforce_content_style=True
        )
        assert not spellcheck.has_strict_content_style_violations([legacy])
        assert spellcheck.has_strict_content_style_violations([current])


class TestStagedFileCollection:
    def test_collects_staged_post_index(self, monkeypatch):
        monkeypatch.setattr(
            spellcheck.subprocess,
            "run",
            lambda *args, **kwargs: SimpleNamespace(
                stdout="content/posts/2026-09-06-example/index.md\n"
            ),
        )
        files = spellcheck.collect_staged_files()
        assert files == [
            spellcheck.REPO_ROOT / "content/posts/2026-09-06-example/index.md"
        ]


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
