"""Minimal shared loaders for the high-value validation tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
POST_VALIDATION_DIR = SCRIPTS_DIR / "post-validation"


def load_repo_module(relative_path: str):
    """Load a repository Python module by a path relative to the root."""
    path = REPO_ROOT / relative_path
    module_name = f"repo_{path.as_posix().replace('/', '_').replace('-', '_').replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_check_module(filename: str):
    return load_repo_module(f"scripts/post-validation/{filename}")


cover_check = load_check_module("cover-check.py")
frontmatter_check = load_check_module("frontmatter-check.py")
size_check = load_check_module("image-size-check.py")


@pytest.fixture(scope="session")
def built_site():
    """Build once only for tests that inspect rendered production output."""
    hugo_site = load_repo_module("tests/hugo_site.py")
    return hugo_site.ensure_built_site()
