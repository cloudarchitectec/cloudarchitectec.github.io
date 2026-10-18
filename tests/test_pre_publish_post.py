"""Critical behaviour of the local blog-publishing helper."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

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


def test_front_matter_preserves_concise_description():
    description = "這是一段用於文章列表、搜尋與社群分享的簡短文章摘要。"
    front_matter = publisher.generate_front_matter(
        "Title", "2025-01-01-slug", "2025-01-01", ["澳洲職場"], ["tag"],
        "cover-unsplash.jpg", [], description=description,
    )
    assert f"description: {publisher.json.dumps(description, ensure_ascii=False)}" in front_matter


def test_copy_referenced_input_images_only_copies_images_used_by_draft(tmp_path: Path):
    input_dir = tmp_path / "input"
    images_dir = tmp_path / "post" / "images"
    input_dir.mkdir()
    images_dir.mkdir(parents=True)
    (input_dir / "used.jpeg").write_bytes(b"photo")
    (input_dir / "unused.jpeg").write_bytes(b"other photo")

    copied = publisher.copy_referenced_input_images(
        input_dir / "draft.md",
        images_dir,
        '{{< figure src="images/used.jpeg" alt="A photo" >}}',
    )

    assert copied == ["used.jpeg"]
    assert (images_dir / "used.jpeg").read_bytes() == b"photo"
    assert not (images_dir / "unused.jpeg").exists()


def test_copy_referenced_input_images_includes_explicit_local_cover(tmp_path: Path):
    input_dir = tmp_path / "input"
    images_dir = tmp_path / "post" / "images"
    input_dir.mkdir()
    images_dir.mkdir(parents=True)
    (input_dir / "cover.jpeg").write_bytes(b"cover")

    copied = publisher.copy_referenced_input_images(
        input_dir / "draft.md",
        images_dir,
        "Post body without an image reference.",
        extra_filenames={"cover.jpeg"},
    )

    assert copied == ["cover.jpeg"]
    assert (images_dir / "cover.jpeg").read_bytes() == b"cover"


def test_resolve_local_cover_image_requires_a_local_supported_file(tmp_path: Path):
    input_file = tmp_path / "draft.md"
    (tmp_path / "cover.webp").write_bytes(b"image")

    assert publisher.resolve_local_cover_image(input_file, "cover.webp") == tmp_path / "cover.webp"
    for filename in ("../cover.webp", str(tmp_path / "cover.webp"), "cover.svg", "missing.jpg"):
        try:
            publisher.resolve_local_cover_image(input_file, filename)
        except (ValueError, FileNotFoundError):
            continue
        raise AssertionError(f"Invalid local cover was accepted: {filename}")


def test_cli_uses_selected_local_cover_without_unsplash(tmp_path: Path, monkeypatch):
    input_dir = tmp_path / "input"
    posts_dir = tmp_path / "posts"
    input_dir.mkdir()
    (input_dir / "cover.jpg").write_bytes(b"local cover")
    (input_dir / "draft.md").write_text(
        '---\ntitle: "Local cover post"\nslug: "local-cover-post"\n'
        'categories: ["旅行紀錄"]\ntags: ["travel"]\n---\nPost body.\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(publisher, "INPUT_DIR", input_dir)
    monkeypatch.setattr(publisher, "HUGO_CONTENT_DIR", posts_dir)
    monkeypatch.setattr(
        publisher.click,
        "prompt",
        lambda prompt, default=None, **kwargs: (
            "2025-01-01" if prompt.startswith("📅") else default
        ),
    )
    monkeypatch.setattr(publisher, "prompt_category", lambda categories, tags: ["旅行紀錄"])
    monkeypatch.setattr(publisher, "prompt_tags", lambda tags: tags)
    monkeypatch.setattr(publisher, "prompt_episode_series", lambda series, title: None)
    monkeypatch.setattr(publisher, "confirm_replace_post_dir", lambda path: True)
    monkeypatch.setattr(
        publisher,
        "acquire_unsplash_cover",
        lambda images_dir: (_ for _ in ()).throw(AssertionError("Unsplash flow should be skipped")),
    )
    monkeypatch.setattr(publisher, "optimize_post_images", lambda post_dir: True)
    monkeypatch.setattr(publisher, "run_spellcheck_fix", lambda slug: None)
    monkeypatch.setattr(publisher, "validate_post", lambda post_dir: True)
    monkeypatch.setattr(publisher.subprocess, "run", lambda *args, **kwargs: None)

    result = CliRunner().invoke(
        publisher.main,
        [
            "draft.md",
            "--no-hugo",
            "--cover-image",
            "cover.jpg",
            "--cover-alt",
            "Local image",
        ],
    )

    assert result.exit_code == 0, result.output
    post = posts_dir / "2025-01-01-local-cover-post" / "index.md"
    assert 'image: "images/cover.jpg"' in post.read_text(encoding="utf-8")
    assert 'alt: "Local image"' in post.read_text(encoding="utf-8")
    assert (post.parent / "images" / "cover.jpg").read_bytes() == b"local cover"


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
