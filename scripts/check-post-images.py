#!/usr/bin/env python3
"""Verify post image references resolve to page bundle files.

Deduplicates refs from front matter (image, images:) and inline markdown
before comparing to files on disk. Raw string counts without dedup produce
false positives when the same filename appears in multiple places.

Also validates cover/hero and Unsplash attribution format (C8-S5).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

POSTS_DIR = Path(__file__).resolve().parent.parent / "content" / "posts"
MD_IMG = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
DOUBLE_EXT_SUFFIXES = (".jpeg.jpg", ".png.jpg")
DOUBLE_EXT_REF = re.compile(r"\.(?:jpeg\.jpg|png\.jpg)")
UNSPLASH_INLINE = re.compile(r"^\s*Photo by ", re.IGNORECASE)
BAD_UTM = re.compile(r"utm_source=(?:medium|unsplash)", re.IGNORECASE)


def split_post(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text
    return parts[1], parts[2]


def get_fm_value(fm: str, key: str) -> str | None:
    for line in fm.splitlines():
        m = re.match(rf'^\s*{re.escape(key)}:\s*"(.*)"\s*$', line)
        if m:
            return m.group(1)
        m = re.match(rf"^\s*{re.escape(key)}:\s*'(.*)'\s*$", line)
        if m:
            return m.group(1)
    return None


def get_fm_nested(fm: str, key: str) -> str | None:
    for line in fm.splitlines():
        m = re.match(rf'^\s*{re.escape(key)}:\s*"(.*)"\s*$', line)
        if m:
            return m.group(1)
    return None


def parse_cover(fm: str) -> dict[str, str | dict[str, str]]:
    if not re.search(r"^\s*cover:\s*$", fm, re.MULTILINE):
        return {}
    return {
        "image": get_fm_nested(fm, "image") or "",
        "alt": get_fm_nested(fm, "alt") or "",
        "credit": {
            "photographer": get_fm_nested(fm, "photographer") or "",
            "photographer_url": get_fm_nested(fm, "photographer_url") or "",
            "photo_url": get_fm_nested(fm, "photo_url") or "",
        },
    }


def extract_image_paths(text: str) -> list[str]:
    paths: list[str] = []
    in_fm = False
    fm_key: str | None = None
    in_cover = False

    for line in text.splitlines():
        if line.strip() == "---":
            in_fm = not in_fm
            fm_key = None
            in_cover = False
            continue

        if not in_fm:
            for match in MD_IMG.finditer(line):
                paths.append(match.group(1).strip())
            continue

        if re.match(r"^\s*cover:\s*$", line):
            in_cover = True
            continue

        if in_cover and re.match(r'^\s+image:\s*"(.*)"\s*$', line):
            m = re.match(r'^\s+image:\s*"(.*)"\s*$', line)
            if m:
                paths.append(m.group(1).strip())
            continue

        if in_cover and line.strip() and not line.startswith("  "):
            in_cover = False

        if re.match(r"^\s*images\s*:\s*", line):
            fm_key = "images"
            val = line.split(":", 1)[1].strip().strip('"').strip("'")
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


def fm_declares_hero_images(fm: str) -> bool:
    """True when front matter images: lists bundle paths (not empty placeholders)."""
    for line in fm.splitlines():
        m = re.match(r'^\s*images\s*:\s*\[(.+)\]\s*$', line)
        if m and re.search(r"images/[^'\"\s]", m.group(1)):
            return True
        m = re.match(r'^\s*-\s+"?(images/[^"\']+)"?\s*$', line)
        if m and m.group(1).strip():
            return True
    return bool(parse_cover(fm).get("image"))


def check_post_format(md_file: Path) -> list[str]:
    """Return format violations for cover/hero and Unsplash rules."""
    text = md_file.read_text(encoding="utf-8", errors="replace")
    fm, body = split_post(text)
    errors: list[str] = []

    if "/images/" in text:
        errors.append("absolute /images/ path found (use images/...)")

    if BAD_UTM.search(text):
        errors.append("utm_source=medium or utm_source=unsplash found (UTM is added at render time)")

    if re.search(r"^image:\s*", fm, re.MULTILINE):
        errors.append("root image: field present (use cover.image only)")

    cover = parse_cover(fm)
    cover_image = str(cover.get("image") or "")

    if fm_declares_hero_images(fm) and not cover_image:
        errors.append("front matter declares images but cover.image is missing")

    if cover_image:
        if not str(cover.get("alt") or "").strip():
            errors.append("cover.image set but cover.alt is missing or empty")

    if cover_image.endswith("-unsplash.jpg"):
        credit = cover.get("credit") or {}
        if not isinstance(credit, dict):
            credit = {}
        required = ("photographer", "photographer_url", "photo_url")
        if not all(str(credit.get(k) or "").strip() for k in required):
            errors.append("Unsplash cover (*-unsplash.jpg) requires cover.credit block")
        elif str(credit.get("photo_url") or "").strip() in ("https://unsplash.com", "http://unsplash.com"):
            errors.append("new Unsplash post requires specific photo_url (not generic unsplash.com)")

    cover_norm = normalize_path(cover_image)
    for line in body.splitlines():
        match = MD_IMG.search(line)
        if not match:
            continue
        body_norm = normalize_path(match.group(1))
        if cover_norm and body_norm and cover_norm == body_norm:
            errors.append("duplicate hero: body image matches cover.image")
        break

    for line in body.lstrip("\n").splitlines()[:10]:
        if UNSPLASH_INLINE.match(line):
            errors.append("inline Unsplash credit in body (use cover.credit)")
            break

    return errors


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


def check_posts(posts_dir: Path = POSTS_DIR, only: Path | None = None) -> int:
    failures: list[tuple[str, list[str]]] = []
    format_failures: list[tuple[str, list[str]]] = []
    checked = 0

    md_files = [only] if only else sorted(posts_dir.rglob("index.md"))

    for md_file in md_files:
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
            fmt_errors = check_post_format(md_file)
            if fmt_errors:
                format_failures.append((post_dir.name, fmt_errors))
            continue

        checked += 1
        if missing:
            failures.append((post_dir.name, missing))

        fmt_errors = check_post_format(md_file)
        if fmt_errors:
            format_failures.append((post_dir.name, fmt_errors))

    if only:
        print(f"Checked post: {only.parent.name}")
    else:
        print(f"Checked {checked} posts with image references")

    exit_code = 0

    if failures:
        exit_code = 1
        print(f"❌ {len(failures)} post(s) with missing bundle images:")
        for slug, missing in failures:
            print(f"  {slug}:")
            for path in missing:
                print(f"    - {path}")

    if format_failures:
        exit_code = 1
        print(f"❌ {len(format_failures)} post(s) with image format violations:")
        for slug, errors in format_failures:
            print(f"  {slug}:")
            for err in errors:
                print(f"    - {err}")

    if exit_code == 0:
        print("✅ All post image references resolve to page bundle files")
        print("✅ All post image format checks passed")

    return exit_code


def resolve_post_path(arg: str) -> Path:
    path = Path(arg)
    if path.is_file():
        return path.resolve()
    candidate = POSTS_DIR / arg / "index.md"
    if candidate.is_file():
        return candidate.resolve()
    candidate = POSTS_DIR / arg
    if candidate.is_file():
        return candidate.resolve()
    raise FileNotFoundError(f"Post not found: {arg}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify post image paths and format")
    parser.add_argument(
        "--post",
        metavar="SLUG_OR_PATH",
        help="Check a single post (slug dir name or path to index.md)",
    )
    args = parser.parse_args()

    only: Path | None = None
    if args.post:
        try:
            only = resolve_post_path(args.post)
        except FileNotFoundError as exc:
            print(f"❌ {exc}")
            return 1

    exit_code = check_double_extensions()
    if exit_code != 0:
        return exit_code
    return check_posts(only=only)


if __name__ == "__main__":
    sys.exit(main())
