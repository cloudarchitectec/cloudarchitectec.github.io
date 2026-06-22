"""Tests for scripts/episodeseries_registry.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import load_repo_module

registry = load_repo_module("scripts/episodeseries_registry.py")


class TestEpisodeSeriesRegistry:
    def test_load_empty_when_missing(self, tmp_path: Path):
        assert registry.load_series_list(tmp_path / "missing.json") == []

    def test_load_rejects_non_array(self, tmp_path: Path):
        path = tmp_path / "episodeseries.json"
        path.write_text('{"name": "x"}', encoding="utf-8")
        with pytest.raises(ValueError):
            registry.load_series_list(path)

    def test_save_and_load_sorted_unique(self, tmp_path: Path):
        path = tmp_path / "episodeseries.json"
        registry.save_series_list(["B 系列", "A 系列", "A 系列"], path)
        assert registry.load_series_list(path) == ["A 系列", "B 系列"]

    def test_register_series_appends_new_name(self, tmp_path: Path):
        path = tmp_path / "episodeseries.json"
        path.write_text(json.dumps(["既有系列"], ensure_ascii=False) + "\n", encoding="utf-8")

        added = registry.register_series("新系列", path)
        assert added is True
        assert registry.load_series_list(path) == ["新系列", "既有系列"]

    def test_register_series_noop_when_exists(self, tmp_path: Path):
        path = tmp_path / "episodeseries.json"
        path.write_text(json.dumps(["既有系列"], ensure_ascii=False) + "\n", encoding="utf-8")

        added = registry.register_series("既有系列", path)
        assert added is False
        assert registry.load_series_list(path) == ["既有系列"]
