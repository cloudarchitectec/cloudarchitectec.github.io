#!/usr/bin/env python3
"""Verify post image references resolve to page bundle files.

Deduplicates refs from front matter (image, images:) and inline markdown
before comparing to files on disk. Raw string counts without dedup produce
false positives when the same filename appears in multiple places.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

POSTS_DIR = Path(__file__).resolve().parent.parent / "content" / "posts"
MD_IMG = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
DOUBLE_EXT_SUFFIXES = (".jpeg.jpg", ".png.jpg")
DOUBLE_EXT_REF = re.compile(r"\.(?:jpeg\.jpg|png\.jpg)")


def extract_image_paths(text: str) -> list[str]:
    paths: list[str] = []
    in_fm = False
    fm_key: str | None = None

    for line in text.splitlines():
        if line.strip() == "---":
            in_fm = not in_fm
            fm_key = None
            continue

        if not in_fm:
            for match in MD_IMG.finditer(line):
                paths.append(match.group(1).strip())
            continue

        match = re.match(r"^\s*(image|images)\s*:\s*(.*)$", line)
        if match:
            fm_key = match.group(1)
            val = match.group(2).strip().strip('"').strip("'")
            if val and val != "[]" and not val.startswith("["):
                paths.append(val)
            continue

        if fm_key == "images" and re.match(r"^\s*-\s+", line):
            val = line.strip()[1:].strip().strip('"').strip("'")
            if val:
                paths.append(val)

    return paths


def normalize_path(raw: str) -> str | None:
    raw = raw.strip()
    if not raw or raw.startswith("http://") or raw.startswith("https://"):
        return None
    if raw.startswith("/images/"):
        return "images/" + Path(raw).name
    if raw.startswith("images/"):
        return raw
    return None


def check_double_extensions(posts_dir: Path = POSTS_DIR) -> int:
    """Fail if Medium-style double extensions remain (one-time migration complete)."""
    bad_files: list[str] = []
    bad_refs: list[tuple[str, str]] = []

    for images_dir in sorted(posts_dir.glob("*/images")):
        for path in sorted(images_dir.iterdir()):
            if path.is_file() and any(path.name.endswith(s) for s in DOUBLE_EXT_SUFFIXES):
                bad_files.append(str(path.relative_to(posts_dir.parent.parent)))

    for md_file in sorted(posts_dir.rglob("index.md")):
        if DOUBLE_EXT_REF.search(md_file.read_text(encoding="utf-8", errors="replace")):
            bad_refs.append((md_file.parent.name, str(md_file.relative_to(posts_dir.parent.parent))))

    if not bad_files and not bad_refs:
        return 0

    print("❌ Double image extensions found (.jpeg.jpg / .png.jpg):")
    for path in bad_files[:10]:
        print(f"  file: {path}")
    if len(bad_files) > 10:
        print(f"  ... and {len(bad_files) - 10} more files")
    for slug, path in bad_refs[:10]:
        print(f"  ref in: {path}")
    if len(bad_refs) > 10:
        print(f"  ... and {len(bad_refs) - 10} more posts")
    print("  Use .jpg for JPEG and .png for PNG (not .jpeg.jpg / .png.jpg).")
    return 1


def check_posts(posts_dir: Path = POSTS_DIR) -> int:
    failures: list[tuple[str, list[str]]] = []
    checked = 0

    for md_file in sorted(posts_dir.rglob("index.md")):
        post_dir = md_file.parent
        text = md_file.read_text(encoding="utf-8", errors="replace")
        seen: set[str] = set()
        missing: list[str] = []

        for raw in extract_image_paths(text):
            rel = normalize_path(raw)
            if not rel or rel in seen:
                continue
            seen.add(rel)
            if not (post_dir / rel).exists():
                missing.append(rel)

        if not seen and not (post_dir / "images").exists():
            continue

        checked += 1
        if missing:
            failures.append((post_dir.name, missing))

    print(f"Checked {checked} posts with image references")

    if failures:
        print(f"❌ {len(failures)} post(s) with missing bundle images:")
        for slug, missing in failures:
            print(f"  {slug}:")
            for path in missing:
                print(f"    - {path}")
        return 1

    print("✅ All post image references resolve to page bundle files")
    return 0


if __name__ == "__main__":
    exit_code = check_double_extensions()
    if exit_code != 0:
        sys.exit(exit_code)
    sys.exit(check_posts())
