"""Regression tests for Hugo list pages (home, tags, sections).

Tag/section lists broke repeatedly when layouts/_default/list.html had mismatched
{{- end }} tags in the home-only block — the non-home else branch never rendered,
leaving only post-meta-enhanced date lines without titles.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
LIST_TEMPLATE = REPO_ROOT / "layouts" / "_default" / "list.html"
TAG_PAGE = Path("tags") / "devops-工程師" / "index.html"
TAGS_INDEX = Path("tags") / "index.html"
POSTS_SECTION = Path("posts") / "index.html"
PAGINATED_TAG_PAGE = Path("tags") / "旅遊" / "page" / "2" / "index.html"
CATEGORY_PAGE = Path("categories") / "旅行紀錄" / "index.html"
SEARCH_PAGE = Path("search") / "index.html"
HOME_PAGE = Path("index.html")

SAMPLE_TAG_POST_TITLE = "下集：沒有升官加薪，但我很好"
SAMPLE_SECTION_POST_TITLE = "好想要退休！退休前的最後一堂課：比 FIRE 數字更重要的，其實是這件事"


class TestListTemplateStructure:
    def test_home_summary_block_has_balanced_end_tags(self):
        """Catch the regression: {{- end }} must not appear inside post-summary div."""
        text = LIST_TEMPLATE.read_text(encoding="utf-8")
        assert "{{- if $.IsHome }}" in text
        assert "{{- else }}" in text

        assert re.search(
            r'<div class="post-summary">\s*\n\s*\{\{[^}]+\}\}\s*\n\s*\{\{- end \}\}',
            text,
        ) is None, (
            "list.html has {{- end }} inside post-summary — tag/section lists will lose titles"
        )

    def test_paginator_range_is_closed_before_pagination(self):
        text = LIST_TEMPLATE.read_text(encoding="utf-8")
        assert "{{- end }}{{/* end range $paginator.Pages */}}" in text

    def test_non_home_branch_renders_entry_header(self):
        text = LIST_TEMPLATE.read_text(encoding="utf-8")
        else_block = text.split("<!-- Original layout for non-home pages -->", 1)[1]
        assert 'class="entry-header"' in else_block
        assert ".Title }}" in else_block


class TestBuiltListPages:
    def test_tag_page_lists_post_titles(self, built_site):
        html = (built_site / TAG_PAGE).read_text(encoding="utf-8")
        assert "tag-entry" in html or "entry-header" in html
        assert "entry-header" in html, "tag page missing entry-header — list template else branch broken"
        assert SAMPLE_TAG_POST_TITLE in html, (
            f"expected post title on tag page; check {TAG_PAGE}"
        )
        assert html.count("entry-header") >= 5, "tag page should list multiple posts with titles"

    def test_tag_page_has_no_orphan_meta_without_titles(self, built_site):
        html = (built_site / TAG_PAGE).read_text(encoding="utf-8")
        if "post-meta-enhanced" in html:
            assert "entry-header" in html, (
                "post-meta-enhanced without entry-header — home-block end tags are mis-nested"
            )
        assert '<article class="enhanced-post-entry"' not in html and "<article class=enhanced-post-entry" not in html, (
            "tag page must not use home-only enhanced article layout"
        )

    def test_home_page_uses_three_column_layout_with_titles(self, built_site):
        """Home page uses layouts/index.html, not list.html."""
        html = (built_site / HOME_PAGE).read_text(encoding="utf-8")
        assert "home-shell" in html, "home page should render the two-column home shell"
        assert '<article class=home-post-entry' in html or '<article class="home-post-entry"' in html
        assert "post-title" in html
        assert "<a href=" in html
        assert html.count("home-post-entry") >= 3, "home page should list multiple posts"

    def test_home_page_does_not_use_legacy_enhanced_entry(self, built_site):
        """Guards against layouts/_default/list.html's dead IsHome branch leaking back
        onto the home page (see layouts/index.html, which now owns the home route)."""
        html = (built_site / HOME_PAGE).read_text(encoding="utf-8")
        assert '<article class="enhanced-post-entry"' not in html and "<article class=enhanced-post-entry" not in html

    def test_tag_page_has_clickable_entry_links(self, built_site):
        html = (built_site / TAG_PAGE).read_text(encoding="utf-8")
        assert "entry-link" in html

    def test_tags_index_lists_tag_links(self, built_site):
        html = (built_site / TAGS_INDEX).read_text(encoding="utf-8")
        assert "terms-tags" in html, "tags index should use terms-tags list"
        assert html.count('href="/tags/') >= 5 or html.count("href=https://cloudarchitectec.com/tags/") >= 5, (
            "tags index should link to multiple tag pages"
        )
        assert "DevOps" in html or "devops" in html.lower()

    def test_posts_section_lists_titles(self, built_site):
        html = (built_site / POSTS_SECTION).read_text(encoding="utf-8")
        assert "entry-header" in html, "posts section list missing entry-header"
        assert SAMPLE_SECTION_POST_TITLE in html
        assert html.count("entry-header") >= 5, "posts section should list multiple posts with titles"

    def test_paginated_tag_page_lists_titles(self, built_site):
        page = built_site / PAGINATED_TAG_PAGE
        assert page.is_file(), f"paginated tag page not built: {PAGINATED_TAG_PAGE}"
        html = page.read_text(encoding="utf-8")
        assert "entry-header" in html
        assert html.count("entry-header") >= 5

    def test_category_page_lists_titles(self, built_site):
        page = built_site / CATEGORY_PAGE
        assert page.is_file(), f"category page not built: {CATEGORY_PAGE}"
        html = page.read_text(encoding="utf-8")
        assert "entry-header" in html
        assert html.count("entry-header") >= 3

    def test_search_page_has_input_and_script(self, built_site):
        html = (built_site / SEARCH_PAGE).read_text(encoding="utf-8")
        assert 'id="searchInput"' in html or "id=searchInput" in html
        # Search is PaperMod's fastsearch.js + fuse, tuned via [params.fuseOpts];
        # PaperMod concatenates fuse.js + fastsearch.js into one hashed bundle.
        assert "/assets/js/search." in html, "PaperMod search bundle missing from /search"
        assert 'id="searchResults"' in html or "id=searchResults" in html

    def test_search_index_is_slim(self, built_site):
        """index.json is capped at 500 runes of content per post — guard against
        regressing to a multi-megabyte full-content index."""
        index = built_site / "index.json"
        assert index.is_file(), "search index not built"
        size_kb = index.stat().st_size / 1024
        assert size_kb < 800, f"search index ballooned to {size_kb:.0f} KB (expected ~360 KB)"
