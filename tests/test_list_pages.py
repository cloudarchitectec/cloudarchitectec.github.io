"""Regression tests for Hugo list pages (home, tags, sections).

Tag/section lists broke repeatedly when layouts/_default/list.html had mismatched
{{- end }} tags in the home-only block — the non-home else branch never rendered,
leaving only post-meta-enhanced date lines without titles.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
LIST_TEMPLATE = REPO_ROOT / "layouts" / "_default" / "list.html"
PUBLIC_DIR = REPO_ROOT / "public"
TAG_PAGE = PUBLIC_DIR / "tags" / "devops-工程師" / "index.html"
HOME_PAGE = PUBLIC_DIR / "index.html"

# Newest post on DevOps 工程師 tag page 1 (sorted by date descending).
SAMPLE_TAG_POST_TITLE = "大結局：沒有升官加薪，但我很好"


def hugo_available() -> bool:
    return shutil.which("hugo") is not None


@pytest.fixture(scope="module")
def built_site():
    if not hugo_available():
        pytest.skip("hugo not installed")
    result = subprocess.run(
        ["hugo", "--gc", "--minify", "--cleanDestinationDir"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"hugo build failed:\n{result.stdout}\n{result.stderr}")
    return PUBLIC_DIR


class TestListTemplateStructure:
    def test_home_summary_block_has_balanced_end_tags(self):
        """Catch the regression: {{- end }} must not appear inside post-summary div."""
        text = LIST_TEMPLATE.read_text(encoding="utf-8")
        assert "{{- if $.IsHome }}" in text
        assert "{{- else }}" in text

        # The broken pattern closed hideSummary before </div>, orphaning the else branch.
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
        # Non-home list item layout lives in the IsHome else branch (second {{- else }}).
        else_block = text.split("<!-- Original layout for non-home pages -->", 1)[1]
        assert 'class="entry-header"' in else_block
        assert ".Title }}" in else_block


class TestBuiltListPages:
    def test_tag_page_lists_post_titles(self, built_site):
        html = TAG_PAGE.read_text(encoding="utf-8")
        assert "tag-entry" in html or "entry-header" in html
        assert "entry-header" in html, "tag page missing entry-header — list template else branch broken"
        assert SAMPLE_TAG_POST_TITLE in html, (
            f"expected post title on tag page; check {TAG_PAGE.relative_to(REPO_ROOT)}"
        )
        assert html.count("entry-header") >= 5, "tag page should list multiple posts with titles"

    def test_tag_page_has_no_orphan_meta_without_titles(self, built_site):
        html = TAG_PAGE.read_text(encoding="utf-8")
        if "post-meta-enhanced" in html:
            assert "entry-header" in html, (
                "post-meta-enhanced without entry-header — home-block end tags are mis-nested"
            )
        assert '<article class="enhanced-post-entry"' not in html and "<article class=enhanced-post-entry" not in html, (
            "tag page must not use home-only enhanced article layout"
        )

    def test_home_page_uses_enhanced_list_with_titles(self, built_site):
        html = HOME_PAGE.read_text(encoding="utf-8")
        assert '<article class="enhanced-post-entry"' in html or "<article class=enhanced-post-entry" in html
        assert "post-title" in html
        assert "<a href=" in html

    def test_tag_page_has_clickable_entry_links(self, built_site):
        html = TAG_PAGE.read_text(encoding="utf-8")
        assert "entry-link" in html
