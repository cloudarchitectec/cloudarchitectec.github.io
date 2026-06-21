"""Cover image, bundle paths, and Unsplash attribution rules for Hugo posts."""

from __future__ import annotations

import re
from pathlib import Path

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


def parse_images_list(fm: str) -> list[str]:
    paths: list[str] = []
    in_images = False
    for line in fm.splitlines():
        if re.match(r"^\s*images\s*:\s*\[\s*\]\s*$", line):
            return []
        m = re.match(r"^\s*images\s*:\s*\[(.+)\]\s*$", line)
        if m:
            inner = m.group(1)
            for part in re.findall(r'["\']([^"\']+)["\']', inner):
                paths.append(part.strip())
            return paths
        if re.match(r"^\s*images\s*:\s*$", line):
            in_images = True
            continue
        if in_images:
            m = re.match(r'^\s*-\s+"?([^"\']+)"?\s*$', line)
            if m:
                paths.append(m.group(1).strip())
            elif line.strip() and not line.startswith(" "):
                in_images = False
    return paths


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
    for line in fm.splitlines():
        m = re.match(r'^\s*images\s*:\s*\[(.+)\]\s*$', line)
        if m and re.search(r"images/[^'\"\s]", m.group(1)):
            return True
        m = re.match(r'^\s*-\s+"?(images/[^"\']+)"?\s*$', line)
        if m and m.group(1).strip():
            return True
    return bool(parse_cover(fm).get("image"))


def check(text: str) -> list[str]:
    """Return cover and bundle image format violations."""
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

        images_list = parse_images_list(fm)
        if cover_image not in images_list:
            errors.append("cover.image path must appear in images: array")

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


def check_double_extensions(posts_dir: Path, post_dirs: list[Path] | None = None) -> list[str]:
    """Return error messages for double-extension files or refs."""
    errors: list[str] = []
    bad_files: list[str] = []
    bad_refs: list[str] = []

    if post_dirs is not None:
        md_files = [d / "index.md" for d in post_dirs if (d / "index.md").is_file()]
        image_dirs = [d / "images" for d in post_dirs if (d / "images").is_dir()]
    else:
        md_files = sorted(posts_dir.rglob("index.md"))
        image_dirs = sorted(posts_dir.glob("*/images"))

    for images_dir in image_dirs:
        if not images_dir.is_dir():
            continue
        for path in sorted(images_dir.iterdir()):
            if path.is_file() and any(path.name.endswith(s) for s in DOUBLE_EXT_SUFFIXES):
                bad_files.append(str(path.relative_to(posts_dir.parent.parent)))

    for md_file in md_files:
        if DOUBLE_EXT_REF.search(md_file.read_text(encoding="utf-8", errors="replace")):
            bad_refs.append(str(md_file.relative_to(posts_dir.parent.parent)))

    if bad_files or bad_refs:
        errors.append("double image extensions found (.jpeg.jpg / .png.jpg)")
        for path in bad_files[:10]:
            errors.append(f"  file: {path}")
        for path in bad_refs[:10]:
            errors.append(f"  ref in: {path}")
        if len(bad_files) > 10:
            errors.append(f"  ... and {len(bad_files) - 10} more files")
        if len(bad_refs) > 10:
            errors.append(f"  ... and {len(bad_refs) - 10} more posts")

    return errors


def check_bundle_images(md_file: Path) -> list[str]:
    """Return missing bundle image paths for a post."""
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

    return missing
