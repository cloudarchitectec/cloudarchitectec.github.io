"""Accessibility smoke with axe — serious/critical violations only."""

from __future__ import annotations

import pytest
from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import Page

from conftest import DESKTOP_VIEWPORT, MOBILE_VIEWPORT

ALLOWLIST_RULE_IDS = frozenset({"color-contrast"})  # PaperMod theme — track in plan Technical Debt

PAGES = (
    "/",
    "/posts/2025-10-04-goodbye-medium/",
    "/tags/devops-工程師/",
)

VIEWPORTS = {
    "desktop": DESKTOP_VIEWPORT,
    "mobile": MOBILE_VIEWPORT,
}


@pytest.mark.parametrize("path", PAGES)
@pytest.mark.parametrize("viewport_name", VIEWPORTS)
def test_no_serious_a11y_violations(
    page: Page,
    base_url: str,
    path: str,
    viewport_name: str,
):
    page.set_viewport_size(VIEWPORTS[viewport_name])
    page.goto(path)
    axe = Axe()
    results = axe.run(page)
    violations = results.response.get("violations", [])
    serious = [
        v
        for v in violations
        if v.get("impact") in ("serious", "critical")
        and v.get("id") not in ALLOWLIST_RULE_IDS
    ]
    if serious:
        summary = "; ".join(f"{v.get('id')} ({v.get('impact')})" for v in serious[:5])
        pytest.fail(
            f"a11y violations on {path} ({viewport_name}): {summary}"
        )
