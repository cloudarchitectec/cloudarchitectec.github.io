"""Shared test fixtures for post validation, Hugo builds, and UI smoke."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from playwright.sync_api import Page

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))
from hugo_site import (
    PUBLIC_DIR,
    ensure_built_site,
    start_static_server,
    STATIC_SERVER_PORT,
)

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
POST_VALIDATION_DIR = SCRIPTS_DIR / "post-validation"
REPO_ROOT = Path(__file__).resolve().parent.parent


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "network: tests that require external network access (e.g. Waline CDN)",
    )


def load_repo_module(relative_path: str):
    """Load any repo .py file by path relative to the repository root."""
    path = REPO_ROOT / relative_path
    module_name = f"repo_{path.as_posix().replace('/', '_').replace('-', '_').replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_check_module(filename: str):
    path = POST_VALIDATION_DIR / filename
    module_name = f"post_validation_{path.stem.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


cover_check = load_check_module("cover-check.py")
frontmatter_check = load_check_module("frontmatter-check.py")
size_check = load_check_module("image-size-check.py")


def load_script_module(script_name: str):
    """Load a top-level script from scripts/ as a module (for pytest wrappers)."""
    return load_repo_module(f"scripts/{script_name}")


@pytest.fixture(scope="session")
def built_site():
    try:
        return ensure_built_site()
    except RuntimeError as exc:
        if "hugo not installed" in str(exc):
            pytest.skip(str(exc))
        raise


@pytest.fixture(scope="session")
def static_site_url(built_site):
    proc = start_static_server(built_site, STATIC_SERVER_PORT)
    url = f"http://127.0.0.1:{STATIC_SERVER_PORT}"
    yield url
    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(scope="session")
def base_url(static_site_url):
    return static_site_url


MOBILE_VIEWPORT = {"width": 375, "height": 812}
DESKTOP_VIEWPORT = {"width": 1280, "height": 720}


@pytest.fixture
def mobile_page(page: Page) -> Page:
    page.set_viewport_size(MOBILE_VIEWPORT)
    return page


def assert_no_horizontal_overflow(page: Page, tolerance: int = 1) -> None:
    scroll_width = page.evaluate("document.documentElement.scrollWidth")
    viewport_width = page.viewport_size["width"]
    assert scroll_width <= viewport_width + tolerance, (
        f"horizontal overflow: scrollWidth={scroll_width}, viewport={viewport_width}"
    )


def assert_element_fits_viewport(page: Page, selector: str) -> None:
    box = page.locator(selector).first.bounding_box()
    viewport_width = page.viewport_size["width"]
    assert box is not None, f"no bounding box for {selector}"
    assert box["x"] >= 0, f"{selector} starts off-screen left (x={box['x']})"
    assert box["x"] + box["width"] <= viewport_width + 1, (
        f"{selector} overflows viewport (right edge={box['x'] + box['width']}, viewport={viewport_width})"
    )
