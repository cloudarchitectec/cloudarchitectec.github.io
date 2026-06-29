"""Canonical category list for validation, blog converter, and Hugo display order."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = REPO_ROOT / "data" / "categories.yaml"


def _load_registry(path: Path | None = None) -> dict:
    registry = path or DEFAULT_REGISTRY_PATH
    if not registry.is_file():
        raise FileNotFoundError(f"Category registry missing: {registry}")

    data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{registry} must contain a YAML mapping")

    order = data.get("order") or []
    meta = data.get("meta") or []
    if not isinstance(order, list) or not isinstance(meta, list):
        raise ValueError(f"{registry} must define list fields: order, meta")

    return {"order": order, "meta": meta}


def load_display_order(path: Path | None = None) -> list[str]:
    """Return category display order for the ec-post-list page."""
    registry = _load_registry(path)
    names: list[str] = []
    seen: set[str] = set()
    for item in registry["order"]:
        if not isinstance(item, str):
            continue
        name = item.strip()
        if not name or name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names


def load_allowed_categories(path: Path | None = None) -> frozenset[str]:
    """Return all categories allowed in post front matter."""
    registry = _load_registry(path)
    names: set[str] = set()
    for key in ("order", "meta"):
        for item in registry[key]:
            if not isinstance(item, str):
                continue
            name = item.strip()
            if name:
                names.add(name)
    return frozenset(names)
