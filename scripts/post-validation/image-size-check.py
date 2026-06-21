"""Image file size and dimension limits for Hugo post bundles.

Soft limits print warnings; hard limits fail validation (commit blocked).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None  # type: ignore

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".tif", ".tiff", ".bmp"}

# Soft = warn; hard = validation error
COVER_SOFT_LONG_EDGE = 1600
COVER_SOFT_BYTES = 800 * 1024
INLINE_SOFT_LONG_EDGE = 2000
INLINE_SOFT_BYTES = 500 * 1024
HARD_LONG_EDGE = 4000
HARD_BYTES = 2 * 1024 * 1024

# Targets when optimizing outliers
OPTIMIZE_COVER_LONG_EDGE = 1600
OPTIMIZE_INLINE_LONG_EDGE = 1600
JPEG_QUALITY = 85


@dataclass(frozen=True)
class ImageInfo:
    path: Path
    width: int
    height: int
    byte_size: int

    @property
    def long_edge(self) -> int:
        return max(self.width, self.height)


def is_image_path(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_SUFFIXES


def get_cover_path(text: str) -> str | None:
    if not text.startswith("---") or text.count("---") < 2:
        return None
    fm = text.split("---", 2)[1]
    m = re.search(r'^\s+image:\s*"(.*)"\s*$', fm, re.MULTILINE)
    return m.group(1).strip() if m else None


def get_referenced_image_paths(text: str, extract_image_paths) -> list[tuple[str, str]]:
    """Return (relative path, role) pairs: cover first, then inline."""
    seen: set[str] = set()
    out: list[tuple[str, str]] = []

    cover = get_cover_path(text)
    if cover and cover not in seen:
        seen.add(cover)
        out.append((cover, "cover"))

    for raw in extract_image_paths(text):
        rel = raw.strip()
        if not rel.startswith("images/") or rel in seen:
            continue
        seen.add(rel)
        if rel != cover:
            out.append((rel, "inline"))

    return out


def read_image_info(path: Path) -> ImageInfo | None:
    if not path.is_file() or not is_image_path(path):
        return None
    byte_size = path.stat().st_size
    if Image is None:
        return ImageInfo(path=path, width=0, height=0, byte_size=byte_size)
    try:
        with Image.open(path) as img:
            w, h = img.size
        return ImageInfo(path=path, width=w, height=h, byte_size=byte_size)
    except OSError:
        return None


def check_info(info: ImageInfo, role: str) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    rel = info.path.name
    soft_edge = COVER_SOFT_LONG_EDGE if role == "cover" else INLINE_SOFT_LONG_EDGE
    soft_bytes = COVER_SOFT_BYTES if role == "cover" else INLINE_SOFT_BYTES

    if info.long_edge > HARD_LONG_EDGE or info.byte_size > HARD_BYTES:
        errors.append(
            f"image too large ({role}): {rel} — "
            f"{info.width}x{info.height}, {info.byte_size // 1024} KB "
            f"(hard limit: {HARD_LONG_EDGE}px / {HARD_BYTES // 1024} KB)"
        )
    elif info.long_edge > soft_edge:
        warnings.append(
            f"image long edge ({role}): {rel} — {info.long_edge}px "
            f"(soft limit: {soft_edge}px)"
        )
    elif info.byte_size > soft_bytes:
        warnings.append(
            f"image file size ({role}): {rel} — {info.byte_size // 1024} KB "
            f"(soft limit: {soft_bytes // 1024} KB)"
        )

    if info.width and info.long_edge < 1200 and role == "cover":
        warnings.append(
            f"cover may look soft on desktop: {rel} — {info.width}x{info.height} "
            f"(recommended long edge >= 1200px)"
        )

    return warnings, errors


def check_post_images(
    md_file: Path,
    text: str,
    extract_image_paths,
) -> tuple[list[str], list[str]]:
    post_dir = md_file.parent
    warnings: list[str] = []
    errors: list[str] = []

    for rel, role in get_referenced_image_paths(text, extract_image_paths):
        path = post_dir / rel
        info = read_image_info(path)
        if info is None:
            continue
        w, e = check_info(info, role)
        warnings.extend(w)
        errors.extend(e)

    return warnings, errors


def needs_optimize(info: ImageInfo, role: str) -> bool:
    soft_edge = COVER_SOFT_LONG_EDGE if role == "cover" else INLINE_SOFT_LONG_EDGE
    soft_bytes = COVER_SOFT_BYTES if role == "cover" else INLINE_SOFT_BYTES
    return (
        info.long_edge > soft_edge
        or info.byte_size > soft_bytes
        or info.long_edge > HARD_LONG_EDGE
        or info.byte_size > HARD_BYTES
    )


def _resize(img: Image.Image, max_edge: int) -> Image.Image:
    w, h = img.size
    long_edge = max(w, h)
    if long_edge <= max_edge:
        return img
    scale = max_edge / long_edge
    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
    return img.resize(new_size, Image.Resampling.LANCZOS)


def _shrink_until_soft_bytes(img: Image.Image, max_edge: int, soft_bytes: int, *, as_png: bool) -> Image.Image:
    """Resize down if encoded size still exceeds soft byte limit."""
    from io import BytesIO

    resized = _resize(img, max_edge)
    for _ in range(4):
        bio = BytesIO()
        if as_png:
            resized.save(bio, format="PNG", optimize=True)
        else:
            resized.save(bio, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        if bio.tell() <= soft_bytes:
            break
        w, h = resized.size
        resized = resized.resize(
            (max(1, int(w * 0.85)), max(1, int(h * 0.85))),
            Image.Resampling.LANCZOS,
        )
    return resized


def optimize_image(path: Path, role: str) -> tuple[bool, str]:
    """Resize/compress image in place. Returns (changed, message)."""
    if Image is None:
        return False, "Pillow not installed"

    info = read_image_info(path)
    if info is None:
        return False, "unreadable"

    if not needs_optimize(info, role):
        return False, "ok"

    max_edge = OPTIMIZE_COVER_LONG_EDGE if role == "cover" else OPTIMIZE_INLINE_LONG_EDGE
    soft_bytes = COVER_SOFT_BYTES if role == "cover" else INLINE_SOFT_BYTES
    suffix = path.suffix.lower()
    as_png = suffix == ".png"

    with Image.open(path) as img:
        img.load()
        working = img
        if not as_png and working.mode not in ("RGB", "L"):
            working = working.convert("RGB")
        elif as_png and working.mode not in ("RGB", "RGBA", "P", "L"):
            working = working.convert("RGBA")

        before = info.byte_size
        resized = _shrink_until_soft_bytes(working, max_edge, soft_bytes, as_png=as_png)
        if as_png:
            resized.save(path, format="PNG", optimize=True)
        elif suffix == ".jpeg":
            resized.save(path, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        else:
            resized.save(path, format="JPEG", quality=JPEG_QUALITY, optimize=True)

        after = path.stat().st_size
        if after >= before and info.long_edge <= max_edge and before <= soft_bytes:
            return False, "ok"
        return True, (
            f"{info.width}x{info.height} {before // 1024}KB -> "
            f"{resized.size[0]}x{resized.size[1]} {after // 1024}KB"
        )
