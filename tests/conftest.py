"""Shared test fixtures for Hugo post validation."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

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
