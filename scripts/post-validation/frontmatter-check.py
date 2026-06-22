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

FOOTER_LEGACY = re.compile(r"\{\{<\s*footer\s*>\}\}")

# Internal taxonomy for related-post matching (not shown on post pages).
ALLOWED_CATEGORIES = frozenset({
    "EC",
    "零基礎轉職澳洲工程師",
    "海外職場",
    "澳洲生活",
    "投資理財",
    "旅行紀錄",
})


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


def get_fm_categories(fm: str) -> list[str]:
    """Parse categories: [\"a\", \"b\"] from front matter."""
    for line in fm.splitlines():
        m = re.match(r"^\s*categories:\s*\[(.*)\]\s*$", line)
        if not m:
            continue
        inner = m.group(1)
        values = re.findall(r'"([^"]+)"', inner)
        if not values:
            values = re.findall(r"'([^']+)'", inner)
        return values
    return []


def check_categories(fm: str) -> list[str]:
    errors: list[str] = []
    categories = get_fm_categories(fm)
    if not categories:
        errors.append(
            "required front matter missing: categories "
            f"(allowed: {', '.join(sorted(ALLOWED_CATEGORIES))})"
        )
        return errors
    if len(categories) != 1:
        errors.append(
            f"categories must contain exactly one value (found {len(categories)}: {categories!r})"
        )
        return errors
    category = categories[0]
    if category not in ALLOWED_CATEGORIES:
        allowed = ", ".join(sorted(ALLOWED_CATEGORIES))
        errors.append(f"unknown category: {category!r} (allowed: {allowed})")
    return errors


def get_fm_episodeseries(fm: str) -> list[str]:
    """Parse episodeseries: [\"a\"] from front matter."""
    for line in fm.splitlines():
        m = re.match(r'^\s*episodeseries:\s*\[(.*)\]\s*$', line)
        if not m:
            continue
        inner = m.group(1)
        values = re.findall(r'"([^"]+)"', inner)
        if not values:
            values = re.findall(r"'([^']+)'", inner)
        return values
    return []


def check_episodeseries(fm: str) -> list[str]:
    """episodeseries is optional; if present it must be a non-empty array."""
    errors: list[str] = []
    if "episodeseries:" not in fm:
        return errors
    values = get_fm_episodeseries(fm)
    if not values:
        errors.append(
            "episodeseries must be a non-empty array when set (omit the field for non-series posts)"
        )
    return errors



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

    errors.extend(check_categories(fm))
    errors.extend(check_episodeseries(fm))

    body_stripped = body.rstrip()
    if FOOTER_LEGACY.search(body_stripped):
        errors.append(
            "remove {{< footer >}} from body — post footer renders from layouts/partials/post-footer.html"
        )

    if not is_draft(fm):
        cover = parse_cover(fm)
        if not str(cover.get("image") or "").strip():
            errors.append("published post requires cover.image (or set draft: true)")

    return errors
