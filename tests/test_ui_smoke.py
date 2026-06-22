"""Browser smoke tests — visible content on key pages (Playwright)."""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

DATE_ONLY = re.compile(r"^\d{4}年\d{1,2}月\d{1,2}日$")
TAG_PAGE = "/tags/devops-工程師/"
PAGINATED_TAG_PAGE = "/tags/旅遊/page/2/"
CATEGORY_PAGE = "/categories/旅行紀錄/"
STABLE_POST = "/posts/2025-10-04-goodbye-medium/"


def visible_non_empty_text(page: Page, selector: str, limit: int = 10) -> list[str]:
    texts: list[str] = []
    loc = page.locator(selector)
    for i in range(min(loc.count(), limit)):
        el = loc.nth(i)
        if not el.is_visible():
            continue
        text = el.inner_text().strip()
        if text:
            texts.append(text)
    return texts


class TestUiSmoke:
    def test_home_shows_post_titles(self, page: Page):
        page.goto("/")
        titles = visible_non_empty_text(
            page,
            ".enhanced-post-entry .post-title, main .post-title",
        )
        assert titles, "home page should show at least one visible post title"

    def test_tag_page_shows_titles(self, page: Page):
        page.goto(TAG_PAGE)
        headers = page.locator(".entry-header h2, .tag-entry h2")
        visible_titles: list[str] = []
        for i in range(headers.count()):
            header = headers.nth(i)
            if not header.is_visible():
                continue
            text = header.inner_text().strip()
            if text and not DATE_ONLY.match(text):
                visible_titles.append(text)
        assert len(visible_titles) >= 5, (
            "tag page should show at least five visible post titles, not dates only"
        )

    def test_stable_post_footer(self, page: Page):
        page.goto(STABLE_POST)
        expect(page.locator("h1.post-title")).to_be_visible()
        expect(page.locator(".post-footer-cta")).to_be_visible()
        expect(page.get_by_text("訂閱 EC 部落格")).to_be_visible()

    def test_tags_index_has_links(self, page: Page):
        page.goto("/tags/")
        links = page.locator("ul.terms-tags a")
        assert links.count() >= 5, "tags index should list multiple tag links"
        expect(links.first).to_be_visible()

    def test_search_page_input_visible(self, page: Page):
        page.goto("/search/")
        expect(page.locator("#searchInput")).to_be_visible()

    def test_paginated_tag_page_shows_titles(self, page: Page):
        page.goto(PAGINATED_TAG_PAGE)
        headers = page.locator(".entry-header h2")
        visible = sum(
            1
            for i in range(headers.count())
            if headers.nth(i).is_visible() and headers.nth(i).inner_text().strip()
        )
        assert visible >= 5, "paginated tag page should show visible post titles"

    def test_category_page_loads_with_content(self, page: Page):
        page.goto(CATEGORY_PAGE)
        expect(page.locator("h1")).to_be_visible()
        assert page.locator(".entry-header").count() >= 3
