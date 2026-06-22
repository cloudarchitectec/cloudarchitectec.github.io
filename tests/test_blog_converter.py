"""Tests for tools/blog-converter/automated_blog_converter.py episode_series flow."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

REPO_ROOT = Path(__file__).resolve().parents[1]
CONVERTER_PATH = REPO_ROOT / "tools" / "blog-converter" / "automated_blog_converter.py"
REGISTRY_PATH = REPO_ROOT / "scripts" / "episodeseries_registry.py"


def load_converter():
    spec = importlib.util.spec_from_file_location("blog_converter", CONVERTER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {CONVERTER_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_registry_module():
    spec = importlib.util.spec_from_file_location("episodeseries_registry", REGISTRY_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {REGISTRY_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


converter = load_converter()


@pytest.fixture
def registry_tmp(tmp_path: Path, monkeypatch):
    list_file = tmp_path / "episodeseries.json"
    list_file.write_text(
        json.dumps(["我要升官加薪", "好想要退休"], ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    reg = load_registry_module()
    monkeypatch.setattr(reg, "DEFAULT_REGISTRY_PATH", list_file)
    monkeypatch.setattr(converter, "load_episodeseries_registry", lambda: reg)
    return list_file, reg


class TestInferEpisodeSeries:
    def test_bracket_title(self):
        assert converter.infer_episode_series("[我要升官加薪] 第一集") == "我要升官加薪"

    def test_fire_prefix(self):
        assert converter.infer_episode_series("好想要退休：計畫") == "好想要退休"

    def test_unrelated_title(self):
        assert converter.infer_episode_series("隨便一篇單篇") == ""


class TestGenerateFrontMatterEpisodeSeries:
    def test_omits_when_none(self):
        fm = converter.generate_front_matter(
            "Title",
            "2025-01-01-slug",
            "2025-01-01",
            ["海外職場"],
            ["tag"],
            None,
            [],
            episode_series=None,
        )
        assert "episodeseries" not in fm

    def test_includes_when_set(self):
        fm = converter.generate_front_matter(
            "Title",
            "2025-01-01-slug",
            "2025-01-01",
            ["海外職場"],
            ["tag"],
            None,
            [],
            episode_series="我要升官加薪",
        )
        assert 'episodeseries: ["我要升官加薪"]' in fm


class TestPromptEpisodeSeries:
    def test_uses_existing_without_prompt(self, registry_tmp):
        assert converter.prompt_episode_series("好想要退休", "任意標題") == "好想要退休"

    def test_skip_when_not_series(self, monkeypatch):
        monkeypatch.setattr(converter.click, "confirm", lambda *a, **k: False)
        assert converter.prompt_episode_series("", "單篇標題") is None

    def test_picks_existing_series_by_number(self, registry_tmp, monkeypatch):
        monkeypatch.setattr(converter.click, "confirm", lambda *a, **k: True)
        monkeypatch.setattr(converter.click, "prompt", lambda *a, **k: "2")
        assert converter.prompt_episode_series("", "單篇") == "我要升官加薪"

    def test_inferred_series_defaults_to_matching_number(self, registry_tmp, monkeypatch):
        monkeypatch.setattr(converter.click, "confirm", lambda *a, **k: True)
        prompts: list[str] = []

        def capture_prompt(*args, **kwargs):
            prompts.append(kwargs.get("default"))
            return kwargs.get("default") or "2"

        monkeypatch.setattr(converter.click, "prompt", capture_prompt)
        assert (
            converter.prompt_episode_series("", "[我要升官加薪] 第一集")
            == "我要升官加薪"
        )
        assert prompts[0] == "2"

    def test_new_series_name_registers_in_list(self, registry_tmp, monkeypatch):
        list_file, reg = registry_tmp
        monkeypatch.setattr(converter.click, "confirm", lambda *a, **k: True)
        monkeypatch.setattr(converter.click, "prompt", lambda *a, **k: "全新系列")
        assert converter.prompt_episode_series("", "單篇") == "全新系列"
        assert "全新系列" in reg.load_series_list(list_file)

    def test_new_series_via_zero_option(self, registry_tmp, monkeypatch):
        list_file, reg = registry_tmp
        monkeypatch.setattr(converter.click, "confirm", lambda *a, **k: True)
        prompts = iter(["0", "全新系列"])
        monkeypatch.setattr(converter.click, "prompt", lambda *a, **k: next(prompts))
        assert converter.prompt_episode_series("", "單篇") == "全新系列"
        assert "全新系列" in reg.load_series_list(list_file)
