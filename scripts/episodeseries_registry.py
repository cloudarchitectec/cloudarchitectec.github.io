"""Canonical episode-series list for the blog converter and human reference."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = REPO_ROOT / "data" / "episodeseries.json"


def load_series_list(path: Path | None = None) -> list[str]:
    """Return sorted unique series names from the registry file."""
    registry = path or DEFAULT_REGISTRY_PATH
    if not registry.is_file():
        return []

    data = json.loads(registry.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{registry} must contain a JSON array of series names")

    names: list[str] = []
    seen: set[str] = set()
    for item in data:
        if not isinstance(item, str):
            continue
        name = item.strip()
        if not name or name in seen:
            continue
        seen.add(name)
        names.append(name)

    return sorted(names)


def save_series_list(names: list[str], path: Path | None = None) -> None:
    """Persist sorted unique series names to the registry file."""
    registry = path or DEFAULT_REGISTRY_PATH
    unique = sorted({name.strip() for name in names if name and name.strip()})
    registry.write_text(
        json.dumps(unique, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def register_series(name: str, path: Path | None = None) -> bool:
    """Add a series name if missing. Returns True when the registry file changed."""
    cleaned = name.strip()
    if not cleaned:
        return False

    registry = path or DEFAULT_REGISTRY_PATH
    names = load_series_list(registry)
    if cleaned in names:
        return False

    names.append(cleaned)
    save_series_list(names, registry)
    return True
