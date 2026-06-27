"""Tests for tools/blog-publisher/pre-publish-post.py episode_series flow."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import load_repo_module

publisher = load_repo_module("tools/blog-publisher/pre-publish-post.py")


@pytest.fixture
def registry_tmp(tmp_path: Path, monkeypatch):
    list_file = tmp_path / "episodeseries.json"
    list_file.write_text(
        json.dumps(["我要升官加薪", "好想要退休"], ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    reg = load_repo_module("scripts/episodeseries_registry.py")
    monkeypatch.setattr(reg, "DEFAULT_REGISTRY_PATH", list_file)
    monkeypatch.setattr(publisher, "load_episodeseries_registry", lambda: reg)
    return list_file, reg


class TestInferEpisodeSeries:
    def test_bracket_title(self):
        assert publisher.infer_episode_series("[我要升官加薪] 第一集") == "我要升官加薪"

    def test_fire_prefix(self):
        assert publisher.infer_episode_series("好想要退休：計畫") == "好想要退休"

    def test_unrelated_title(self):
        assert publisher.infer_episode_series("隨便一篇單篇") == ""


class TestGenerateFrontMatterEpisodeSeries:
    def test_omits_when_none(self):
        fm = publisher.generate_front_matter(
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
        fm = publisher.generate_front_matter(
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
        assert publisher.prompt_episode_series("好想要退休", "任意標題") == "好想要退休"

    def test_skip_when_not_series(self, monkeypatch):
        monkeypatch.setattr(publisher.click, "confirm", lambda *a, **k: False)
        assert publisher.prompt_episode_series("", "單篇標題") is None

    def test_picks_existing_series_by_number(self, registry_tmp, monkeypatch):
        monkeypatch.setattr(publisher.click, "confirm", lambda *a, **k: True)
        monkeypatch.setattr(publisher.click, "prompt", lambda *a, **k: "2")
        assert publisher.prompt_episode_series("", "單篇") == "我要升官加薪"

    def test_inferred_series_defaults_to_matching_number(self, registry_tmp, monkeypatch):
        monkeypatch.setattr(publisher.click, "confirm", lambda *a, **k: True)
        prompts: list[str] = []

        def capture_prompt(*args, **kwargs):
            prompts.append(kwargs.get("default"))
            return kwargs.get("default") or "2"

        monkeypatch.setattr(publisher.click, "prompt", capture_prompt)
        assert (
            publisher.prompt_episode_series("", "[我要升官加薪] 第一集")
            == "我要升官加薪"
        )
        assert prompts[0] == "2"

    def test_new_series_name_registers_in_list(self, registry_tmp, monkeypatch):
        list_file, reg = registry_tmp
        monkeypatch.setattr(publisher.click, "confirm", lambda *a, **k: True)
        monkeypatch.setattr(publisher.click, "prompt", lambda *a, **k: "全新系列")
        assert publisher.prompt_episode_series("", "單篇") == "全新系列"
        assert "全新系列" in reg.load_series_list(list_file)

    def test_new_series_via_zero_option(self, registry_tmp, monkeypatch):
        list_file, reg = registry_tmp
        monkeypatch.setattr(publisher.click, "confirm", lambda *a, **k: True)
        prompts = iter(["0", "全新系列"])
        monkeypatch.setattr(publisher.click, "prompt", lambda *a, **k: next(prompts))
        assert publisher.prompt_episode_series("", "單篇") == "全新系列"
        assert "全新系列" in reg.load_series_list(list_file)


class TestUnsplashErrors:
    def test_missing_api_key_message(self, monkeypatch, tmp_path: Path):
        monkeypatch.delenv("UNSPLASH_ACCESS_KEY", raising=False)
        ok, _, err = publisher.download_unsplash_image(
            "178j8tJrNlc",
            "https://unsplash.com/photos/x-178j8tJrNlc",
            tmp_path / "cover.jpg",
        )
        assert not ok
        assert "UNSPLASH_ACCESS_KEY" in err

    def test_fetch_photo_not_found_message(self, monkeypatch):
        class FakeResp:
            status_code = 404

        monkeypatch.setattr(
            publisher.requests,
            "get",
            lambda *a, **k: FakeResp(),
        )
        data, err = publisher.fetch_unsplash_photo_data("badphotoid1", "test-key")
        assert data is None
        assert "not found" in err.lower()
        assert "badphotoid1" in err


class TestAcquireUnsplashCover:
    def test_retries_then_succeeds(self, tmp_path: Path, monkeypatch):
        urls = iter(
            [
                "https://unsplash.com/photos/bad-aaaaaaaaaaa",
                "https://unsplash.com/photos/good-178j8tJrNlc",
            ]
        )

        def fake_prompt(*args, **kwargs):
            return next(urls)

        attempts: list[str] = []

        def fake_download(photo_id, photo_url, output_path):
            attempts.append(photo_id)
            if photo_id == "aaaaaaaaaaa":
                return False, None, "Photo not found on Unsplash (id: aaaaaaaaaaa)"
            output_path.write_bytes(b"fake")
            return True, {
                "username": "u",
                "name": "N",
                "profile_url": "https://unsplash.com/@u",
                "photo_url": photo_url,
            }, ""

        monkeypatch.setattr(publisher.click, "prompt", fake_prompt)
        monkeypatch.setattr(publisher, "download_unsplash_image", fake_download)

        filename, metadata, path = publisher.acquire_unsplash_cover(tmp_path)
        assert filename == "178j8tJrNlc-unsplash.jpg"
        assert metadata["name"] == "N"
        assert path == tmp_path / filename
        assert attempts == ["aaaaaaaaaaa", "178j8tJrNlc"]

    def test_exits_after_two_failures(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(
            publisher.click,
            "prompt",
            lambda *a, **k: "https://unsplash.com/photos/bad-aaaaaaaaaaa",
        )
        monkeypatch.setattr(
            publisher,
            "download_unsplash_image",
            lambda *a, **k: (False, None, "Photo not found on Unsplash (id: aaaaaaaaaaa)"),
        )
        with pytest.raises(SystemExit) as exc:
            publisher.acquire_unsplash_cover(tmp_path)
        assert exc.value.code == 1
