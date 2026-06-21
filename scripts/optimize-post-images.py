#!/usr/bin/env python3
"""Resize/compress post bundle images that exceed soft size limits."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
POSTS_DIR = SCRIPTS_DIR.parent / "content" / "posts"
POST_VALIDATION_DIR = SCRIPTS_DIR / "post-validation"


def load_module(filename: str):
    path = POST_VALIDATION_DIR / filename
    module_name = f"post_validation_{path.stem.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


cover_check = load_module("cover-check.py")
size_check = load_module("image-size-check.py")


def iter_posts(only: Path | None = None):
    if only:
        candidate = only / "index.md" if only.is_dir() else only
        if candidate.is_file():
            yield candidate
        return
    yield from sorted(POSTS_DIR.rglob("index.md"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Optimize oversized post bundle images")
    parser.add_argument("--post", metavar="SLUG", help="Single post slug or path")
    parser.add_argument("--dry-run", action="store_true", help="Report only")
    parser.add_argument("--apply", action="store_true", help="Write optimized files")
    args = parser.parse_args()

    if args.dry_run == args.apply:
        print("Specify exactly one of --dry-run or --apply")
        return 1

    only: Path | None = None
    if args.post:
        p = Path(args.post)
        only = (POSTS_DIR / args.post) if not p.exists() else p

    changed = 0
    for md_file in iter_posts(only):
        text = md_file.read_text(encoding="utf-8", errors="replace")
        post_dir = md_file.parent
        for rel, role in size_check.get_referenced_image_paths(text, cover_check.extract_image_paths):
            path = post_dir / rel
            info = size_check.read_image_info(path)
            if info is None or not size_check.needs_optimize(info, role):
                continue
            if args.dry_run:
                print(
                    f"{post_dir.name}: would optimize {rel} ({role}) — "
                    f"{info.width}x{info.height}, {info.byte_size // 1024} KB"
                )
                changed += 1
            else:
                ok, msg = size_check.optimize_image(path, role)
                if ok:
                    print(f"{post_dir.name}: {rel} — {msg}")
                    changed += 1

    label = "Would optimize" if args.dry_run else "Optimized"
    print(f"\n{label} {changed} image(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
