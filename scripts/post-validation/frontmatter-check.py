"""Front matter and body conventions for Hugo posts."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

_DIR = Path(__file__).resolve().parent


def _load_cover_check():
    path = _DIR / "cover-check.py"
    spec = importlib.util.spec_from_file_location("cover_check", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_cover = _load_cover_check()
parse_cover = _cover.parse_cover
split_post = _cover.split_post

FOOTER = re.compile(r"\{\{<\s*footer\s*>\}\}\s*$")
LANDING = re.compile(r"\{\{<\s*categorized-posts\s*>\}\}")


def get_fm_scalar(fm: str, key: str) -> str | None:
    for line in fm.splitlines():
        m = re.match(rf'^\s*{re.escape(key)}:\s*"(.*)"\s*$', line)
        if m:
            return m.group(1)
        m = re.match(rf"^\s*{re.escape(key)}:\s*'(.*)'\s*$", line)
        if m:
            return m.group(1)
        m = re.match(rf"^\s*{re.escape(key)}:\s*(.+?)\s*$", line)
        if m:
            val = m.group(1).strip()
            if val and not val.startswith(("[", "{")):
                return val
    return None


def is_draft(fm: str) -> bool:
    val = get_fm_scalar(fm, "draft")
    return val is not None and val.lower() == "true"


def check(text: str, dir_name: str) -> list[str]:
    """Return front matter and body convention violations."""
    fm, body = split_post(text)
    errors: list[str] = []

    for key in ("title", "date", "slug"):
        if not (get_fm_scalar(fm, key) or "").strip():
            errors.append(f"required front matter missing: {key}")

    slug = (get_fm_scalar(fm, "slug") or "").strip()
    if slug and slug != dir_name:
        errors.append(f"slug must match directory name (slug={slug!r}, dir={dir_name!r})")

    body_stripped = body.rstrip()
    if body_stripped and not FOOTER.search(body_stripped) and not LANDING.search(body_stripped):
        errors.append("body must end with {{< footer >}} (or use {{< categorized-posts >}} landing page)")

    if not is_draft(fm):
        cover = parse_cover(fm)
        if not str(cover.get("image") or "").strip():
            errors.append("published post requires cover.image (or set draft: true)")

    return errors
