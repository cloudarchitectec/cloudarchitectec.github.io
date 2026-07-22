"""Search smoke tests — real-keystroke Playwright checks on /search.

Search is PaperMod's fastsearch.js + fuse, tuned via [params.fuseOpts] in hugo.toml.
Two things make naive automation lie here, so don't "simplify" this file:

1. fastsearch binds ``sInput.onkeyup``. ``locator.fill()`` sets .value without
   dispatching key events, so the handler never runs and every query looks like a
   zero-result miss.
2. ``press_sequentially`` is not enough **for CJK**. Playwright has no key mapping
   for 雲/端/…, so it falls back to CDP ``Input.insertText``, which fires ``input``
   only — no keydown/keyup. Verified 2026-07-22: typing 雲端 that way yields
   ``events=['input','input']`` and 0 results; one real ``press("End")`` afterwards
   yields 28. ASCII queries are unaffected, which is why an English-only test
   would happily pass while Chinese looked broken. Real users are fine — IME
   composition does fire keyup. Hence ``_commit()`` below.
3. The index is fetched inside a ``window.onload`` handler, i.e. *after* the load
   event. Typing before that resolves silently no-ops (``if (fuse)`` guard).

Covers the C26 slim-index work (500-rune content cap + tags key) and guards the
C32 removal of the dead chinese-search.js layer.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

SEARCH_PAGE = "/search/"

# Queries that must return hits. Chosen to exercise different fuseOpts keys.
CHINESE_QUERIES = [
    "雲端",    # common in titles
    "澳洲",    # common in titles + content
    "轉職",    # career corpus
    "面試",    # deeper in content, not just titles
]
ENGLISH_QUERIES = ["AWS", "DevOps"]

# Present only in a post's `tags`, never in its title/summary/content. Proves the
# `tags` key added to fuseOpts in C26 is actually being searched.
TAG_ONLY_QUERY = "軟體工程師"


def open_search(page: Page) -> None:
    """Load /search and wait until fuse has its index, so typing can't no-op."""
    page.goto(SEARCH_PAGE)
    page.wait_for_load_state("networkidle")
    expect(page.locator("#searchInput")).to_be_visible()


def search_for(page: Page, query: str):
    """Type `query` and return the results locator."""
    box = page.locator("#searchInput")
    box.click()
    box.press_sequentially(query, delay=40)
    # Fire one guaranteed keyup so fastsearch's onkeyup runs — see note 2 in the
    # module docstring. "End" only moves the caret, it can't alter the query.
    box.press("End")
    return page.locator("#searchResults li")


class TestSearch:
    @pytest.mark.parametrize("query", CHINESE_QUERIES)
    def test_chinese_query_returns_results(self, page: Page, query: str):
        open_search(page)
        results = search_for(page, query)
        expect(results.first).to_be_visible(timeout=10_000)
        assert results.count() > 0, f"no results for Chinese query {query!r}"

    @pytest.mark.parametrize("query", ENGLISH_QUERIES)
    def test_english_query_returns_results(self, page: Page, query: str):
        open_search(page)
        results = search_for(page, query)
        expect(results.first).to_be_visible(timeout=10_000)
        assert results.count() > 0, f"no results for English query {query!r}"

    def test_tag_only_query_matches(self, page: Page):
        """C26 added `tags` to fuseOpts.keys — a tag-only term must still match."""
        open_search(page)
        results = search_for(page, TAG_ONLY_QUERY)
        expect(results.first).to_be_visible(timeout=10_000)
        assert results.count() > 0, (
            f"{TAG_ONLY_QUERY!r} appears only in tags — fuseOpts.keys lost `tags`?"
        )

    def test_results_link_to_real_posts(self, page: Page):
        open_search(page)
        results = search_for(page, "雲端")
        expect(results.first).to_be_visible(timeout=10_000)
        href = results.first.locator("a").get_attribute("href")
        assert href and "/posts/" in href, f"result link looks wrong: {href!r}"
        page.goto(href)
        expect(page.locator("h1").first).to_be_visible()

    def test_nonsense_query_returns_nothing(self, page: Page):
        """Guards against a threshold regression that matches everything."""
        open_search(page)
        results = search_for(page, "zzzqqqxxvv")
        page.wait_for_timeout(500)
        assert results.count() == 0, "nonsense query should return no results"

    def test_no_dead_search_layer(self, page: Page):
        """C32: chinese-search.js was deleted. It also injected CSS that
        out-specified PaperMod's overlay anchor rule — make sure neither returns."""
        open_search(page)
        html = page.content()
        assert "chinese-search" not in html
        assert "search-result-title" not in html
