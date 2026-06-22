"""Shared test fixtures for post validation, Hugo builds, and UI smoke."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

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
    path = Path(__file__).resolve().parent.parent / "scripts" / script_name
    module_name = f"script_{path.stem.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


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
