"""Critical behaviour of the local blog-publishing helper."""

from __future__ import annotations

from pathlib import Path

from conftest import load_repo_module

publisher = load_repo_module("tools/blog-publisher/pre-publish-post.py")


def test_series_detection_handles_known_and_unrelated_titles():
    assert publisher.infer_episode_series("[我要升官加薪] 第一集") == "我要升官加薪"
    assert publisher.infer_episode_series("單篇文章") == ""


def test_front_matter_contains_cover_credit_and_optional_series():
    front_matter = publisher.generate_front_matter(
        "Title", "2025-01-01-slug", "2025-01-01", ["澳洲職場"], ["tag"],
        "cover-unsplash.jpg", [], alt_text="Descriptive cover",
        credit={
            "photographer": "Jane", "photographer_url": "https://unsplash.com/@jane",
            "photo_url": "https://unsplash.com/photos/test-photo",
        }, episode_series="我要升官加薪",
    )
    assert 'image: "images/cover-unsplash.jpg"' in front_matter
    assert 'photographer: "Jane"' in front_matter
    assert 'episodeseries: ["我要升官加薪"]' in front_matter


def test_unsplash_alt_falls_back_to_page_url_slug():
    assert publisher.derive_alt_from_page_url(
        "https://unsplash.com/photos/fire-between-woman-and-boy-XI7lwAWzhZQ",
        "XI7lwAWzhZQ",
    ) == "fire between woman and boy"


def test_unsplash_download_requires_an_api_key(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("UNSPLASH_ACCESS_KEY", raising=False)
    ok, _, error = publisher.download_unsplash_image(
        "178j8tJrNlc", "https://unsplash.com/photos/x-178j8tJrNlc", tmp_path / "cover.jpg"
    )
    assert not ok and "UNSPLASH_ACCESS_KEY" in error


def test_cover_acquisition_retries_once_before_succeeding(tmp_path: Path, monkeypatch):
    urls = iter([
        "https://unsplash.com/photos/bad-aaaaaaaaaaa",
        "https://unsplash.com/photos/good-178j8tJrNlc",
    ])
    attempts: list[str] = []

    def fake_download(photo_id, photo_url, output_path):
        attempts.append(photo_id)
        if photo_id == "aaaaaaaaaaa":
            return False, None, "Photo not found"
        output_path.write_bytes(b"image")
        return True, {"name": "Jane", "username": "jane", "photo_url": photo_url}, ""

    monkeypatch.setattr(publisher.click, "prompt", lambda *args, **kwargs: next(urls))
    monkeypatch.setattr(publisher, "download_unsplash_image", fake_download)
    filename, metadata, path = publisher.acquire_unsplash_cover(tmp_path)
    assert (filename, metadata["name"], path.name, attempts) == (
        "178j8tJrNlc-unsplash.jpg", "Jane", "178j8tJrNlc-unsplash.jpg",
        ["aaaaaaaaaaa", "178j8tJrNlc"],
    )
