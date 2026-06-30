"""Browser smoke tests — visible content on key pages (Playwright)."""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

from conftest import assert_element_fits_viewport, assert_no_horizontal_overflow

DATE_ONLY = re.compile(r"^\d{4}年\d{1,2}月\d{1,2}日$")
TAG_PAGE = "/tags/devops-工程師/"
PAGINATED_TAG_PAGE = "/tags/旅遊/page/2/"
CATEGORY_PAGE = "/categories/旅行紀錄/"
STABLE_POST = "/posts/2025-10-04-goodbye-medium/"
RELATED_POST = "/posts/2026-06-17-retirement-plan/"
PE_POST = "/posts/2025-11-14-pe-1-pe-or-not/"
CV_PAGE_CAREER_ZH = "/portfolio/career-zh/"
CV_PAGE_CAREER_EN = "/portfolio/career-en/"
CV_PAGE_STORY = "/portfolio/story/"
CONSULTATION_PAGE = "/consultation/"


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

    def test_related_posts_on_investment_post(self, page: Page):
        page.goto(RELATED_POST)
        related = page.locator(".related-posts")
        expect(related).to_be_visible()
        expect(related.locator(".related-posts-heading")).to_have_text("延伸閱讀")
        assert related.locator(".related-posts-list a").count() >= 1

    def test_series_nav_on_pe_post(self, page: Page):
        page.goto(PE_POST)
        nav = page.locator(".series-nav")
        expect(nav).to_be_visible()
        expect(nav.locator(".series-nav-heading")).to_have_text("我要升官加薪系列")
        assert nav.locator(".series-nav-list li").count() == 4

    def test_series_nav_recent_on_long_series(self, page: Page):
        page.goto("/posts/2024-08-10-2025-europe-summary/")
        nav = page.locator(".series-nav")
        expect(nav).to_be_visible()
        expect(nav.locator(".series-nav-heading")).to_have_text("一個女生的歐洲獨旅系列")
        assert nav.locator(".series-nav-recent li").count() == 3
        expect(nav.locator(".series-nav-all-link")).to_have_text("點此前往全系列 (共 17 篇)")

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

    def test_cv_page_shows_resume_content(self, page: Page):
        page.goto(CV_PAGE_CAREER_ZH)
        expect(page.locator(".cv-hero-cover .entry-cover img")).to_be_visible()
        expect(page.locator("h1.post-title")).to_have_text("大家好，我是 EC")
        expect(page.get_by_text("從台灣英文系到成功移民澳洲")).to_be_visible()
        expect(page.locator("a.ec-pill.ec-pill--active")).to_have_text("職涯重點")
        expect(page.get_by_role("heading", name="工作經歷")).to_be_visible()
        expect(page.get_by_text("Shell Energy Australia")).to_be_visible()
        expect(page.locator(".cv-tags li")).to_have_count(12)

        page.goto(CV_PAGE_STORY)
        expect(page.locator("a.ec-pill.ec-pill--active")).to_have_text("背景故事")
        expect(page.get_by_role("heading", name="個人經歷")).to_be_visible()

        page.goto(CV_PAGE_CAREER_EN)
        expect(page.locator("a.ec-pill.ec-pill--active")).to_have_text("職涯重點 (英文版)")
        expect(page.get_by_role("heading", name="Experience")).to_be_visible()

    def test_consultation_page_shows_content(self, page: Page):
        page.goto(CONSULTATION_PAGE)
        expect(page.locator("h1.consultation-hero__title")).to_have_text(
            "澳洲雲端架構師 EC 線上職涯諮詢"
        )
        expect(page.locator(".consultation-testimonial-grid .consultation-testimonial-card")).to_have_count(6)
        expect(page.get_by_role("link", name="預約諮詢").first).to_be_visible()
        expect(page.locator("details.consultation-more summary")).to_be_visible()

    def test_consultation_old_post_alias_redirects(self, page: Page):
        page.goto("/posts/2018-01-03-ec-consultation/")
        expect(page).to_have_url(re.compile(r"/consultation/?$"))
        expect(page.locator("h1.consultation-hero__title")).to_be_visible()


class TestMobileUiSmoke:
    def test_desktop_menu_visible_without_toggle(self, page: Page):
        page.goto("/")
        expect(page.locator("#menu").get_by_role("link", name="搜尋")).to_be_visible()
        expect(page.locator(".menu-toggle")).not_to_be_visible()

    def test_mobile_menu_closed_hides_links(self, mobile_page: Page):
        mobile_page.goto("/")
        expect(mobile_page.locator(".menu-toggle")).to_be_visible()
        expect(mobile_page.locator("#menu").get_by_role("link", name="搜尋")).not_to_be_visible()

    def test_mobile_menu_open_shows_links(self, mobile_page: Page):
        mobile_page.goto("/")
        toggle = mobile_page.locator(".menu-toggle")
        toggle.click()
        expect(toggle).to_have_attribute("aria-expanded", "true")
        expect(mobile_page.locator("#menu").get_by_role("link", name="搜尋")).to_be_visible()
        expect(mobile_page.locator("#menu").get_by_role("link", name="請EC喝咖啡 ☕️")).to_be_visible()

    def test_mobile_home_no_horizontal_overflow(self, mobile_page: Page):
        mobile_page.goto("/")
        assert_no_horizontal_overflow(mobile_page)

    def test_mobile_stable_post_no_horizontal_overflow(self, mobile_page: Page):
        mobile_page.goto(STABLE_POST)
        assert_no_horizontal_overflow(mobile_page)

    def test_mobile_mailerlite_footer_fits_viewport(self, mobile_page: Page):
        mobile_page.goto(STABLE_POST)
        expect(mobile_page.locator(".post-footer-cta-form input.form-control")).to_be_visible()
        expect(mobile_page.locator(".post-footer-cta-form button.primary")).to_be_visible()
        expect(mobile_page.locator(".post-footer-cta-coffee-btn")).to_be_visible()
        assert_element_fits_viewport(mobile_page, ".post-footer-cta-form input.form-control")
        assert_element_fits_viewport(mobile_page, ".post-footer-cta-form button.primary")
        assert_element_fits_viewport(mobile_page, ".post-footer-cta-coffee-btn")

    def test_mobile_waline_wrapper_visible(self, mobile_page: Page):
        mobile_page.goto(STABLE_POST)
        expect(mobile_page.locator(".comments-section")).to_be_visible()
        expect(mobile_page.locator("#waline")).to_be_attached()
        assert_no_horizontal_overflow(mobile_page)

    @pytest.mark.network
    def test_mobile_waline_panel_loads(self, mobile_page: Page):
        mobile_page.goto(STABLE_POST)
        try:
            mobile_page.wait_for_selector(
                "#waline .wl-panel, #waline .wl-editor",
                timeout=10_000,
            )
        except Exception:
            pytest.skip("Waline CDN widget did not load in time")
        expect(mobile_page.locator("#waline .wl-btn.primary")).to_be_visible()
        assert_no_horizontal_overflow(mobile_page)
