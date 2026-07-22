"""docs/POSTS-INDEX.md must stay in sync with content/posts/.

The index is a generated map (scripts/gen-posts-index.py) that lets humans and
AI locate a post without scanning every bundle. If a post is added or edited
without regenerating, this test fails — run: python3 scripts/gen-posts-index.py
"""

from __future__ import annotations

from conftest import REPO_ROOT, load_repo_module

gen = load_repo_module("scripts/gen-posts-index.py")


class TestPostsIndex:
    def test_index_file_exists(self):
        assert (REPO_ROOT / "docs" / "POSTS-INDEX.md").exists(), (
            "docs/POSTS-INDEX.md missing — run: python3 scripts/gen-posts-index.py"
        )

    def test_index_is_up_to_date(self):
        expected = gen.render(gen.collect_posts())
        actual = (REPO_ROOT / "docs" / "POSTS-INDEX.md").read_text(encoding="utf-8")
        assert actual == expected, (
            "docs/POSTS-INDEX.md is stale — run: python3 scripts/gen-posts-index.py"
        )

    def test_every_published_post_indexed(self):
        indexed = {p["folder"] for p in gen.collect_posts()}
        drafts = 0
        published = 0
        for index_md in (REPO_ROOT / "content" / "posts").glob("*/index.md"):
            meta, _ = gen.split_frontmatter(index_md.read_text(encoding="utf-8"))
            if meta.get("draft") is True:
                drafts += 1
                continue
            published += 1
            assert f"content/posts/{index_md.parent.name}" in indexed
        assert published > 0
        assert drafts >= 0
