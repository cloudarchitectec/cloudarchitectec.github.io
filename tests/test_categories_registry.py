"""Tests for scripts/categories_registry.py."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from conftest import load_repo_module

registry = load_repo_module("scripts/categories_registry.py")


class TestCategoriesRegistry:
    def test_load_allowed_includes_order_and_meta(self):
        allowed = registry.load_allowed_categories()
        assert "澳洲職場" in allowed
        assert "EC" in allowed

    def test_load_display_order_matches_yaml(self):
        order = registry.load_display_order()
        assert order[0] == "澳洲職場"
        assert "EC" not in order

    def test_rejects_invalid_registry(self, tmp_path: Path):
        path = tmp_path / "categories.yaml"
        path.write_text("order: not-a-list\nmeta: []\n", encoding="utf-8")
        with pytest.raises(ValueError):
            registry.load_display_order(path)

    def test_round_trip_custom_registry(self, tmp_path: Path):
        path = tmp_path / "categories.yaml"
        path.write_text(
            yaml.safe_dump(
                {"order": ["投資理財", "澳洲職場"], "meta": ["EC"]},
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        assert registry.load_display_order(path) == ["投資理財", "澳洲職場"]
        assert registry.load_allowed_categories(path) == frozenset(
            {"投資理財", "澳洲職場", "EC"}
        )
