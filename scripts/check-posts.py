#!/usr/bin/env python3
"""Validate Hugo posts: cover images and front matter conventions.

Rules live in scripts/post-validation/cover-check.py and frontmatter-check.py.

Usage:
  python3 scripts/check-posts.py              # full repo (CI; uses git index paths)
  python3 scripts/check-posts.py --post SLUG  # single post
  python3 scripts/check-posts.py --staged     # git staged posts (pre-commit)
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
POSTS_DIR = REPO_ROOT / "content" / "posts"
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


def git_dir_name(path: str) -> str | None:
    parts = Path(path).parts
    if len(parts) >= 3 and parts[0] == "content" and parts[1] == "posts":
        return parts[2]
    return None


def list_post_entries_from_git() -> list[tuple[Path, str]]:
    """List post index.md files using git index paths (case-sensitive, matches Linux CI)."""
    result = subprocess.run(
        ["git", "ls-files", "--", "content/posts/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print("❌ git ls-files failed; cannot validate posts without git index paths")
        return []

    entries: list[tuple[Path, str]] = []
    seen: set[str] = set()
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line.endswith("/index.md"):
            continue
        dir_name = git_dir_name(line)
        if dir_name is None or dir_name in seen:
            continue
        seen.add(dir_name)
        entries.append((REPO_ROOT / line, dir_name))

    return sorted(entries, key=lambda item: item[1])


def resolve_post_path(arg: str) -> tuple[Path, str]:
    path = Path(arg)
    if path.is_file():
        resolved = path.resolve()
        try:
            rel = resolved.relative_to(REPO_ROOT.resolve())
            dir_name = git_dir_name(str(rel))
            if dir_name is not None:
                return resolved, dir_name
        except ValueError:
            pass
        return resolved, resolved.parent.name

    candidate = POSTS_DIR / arg / "index.md"
    if candidate.is_file():
        return candidate.resolve(), arg

    candidate = POSTS_DIR / arg
    if candidate.is_file():
        return candidate.resolve(), Path(arg).stem

    raise FileNotFoundError(f"Post not found: {arg}")


def get_staged_post_entries() -> list[tuple[Path, str]]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    entries: list[tuple[Path, str]] = []
    seen: set[str] = set()
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line.startswith("content/posts/"):
            continue
        dir_name = git_dir_name(line)
        if dir_name is None or dir_name in seen:
            continue
        md_file = POSTS_DIR / dir_name / "index.md"
        if not md_file.is_file():
            continue
        seen.add(dir_name)
        entries.append((md_file, dir_name))
    return sorted(entries, key=lambda item: item[1])


def validate_post(md_file: Path, dir_name: str) -> tuple[list[str], list[str], bool]:
    """Return (errors, warnings, has_image_refs)."""
    text = md_file.read_text(encoding="utf-8", errors="replace")
    post_dir = md_file.parent
    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(frontmatter_check.check(text, dir_name))
    errors.extend(cover_check.check(text))

    size_warnings, size_errors = size_check.check_post_images(
        md_file, text, cover_check.extract_image_paths
    )
    warnings.extend(size_warnings)
    errors.extend(size_errors)

    has_refs = bool(cover_check.extract_image_paths(text)) or (post_dir / "images").exists()
    if has_refs:
        for path in cover_check.check_bundle_images(md_file):
            errors.append(f"missing bundle image: {path}")

    return errors, warnings, has_refs


def run_checks(
    entries: list[tuple[Path, str]],
    post_dirs_for_double_ext: list[Path] | None,
    label: str,
) -> int:
    format_failures: list[tuple[str, list[str]]] = []
    warn_items: list[tuple[str, str]] = []
    checked_with_images = 0

    double_errors = cover_check.check_double_extensions(POSTS_DIR, post_dirs_for_double_ext)
    if double_errors:
        print("❌ Double image extension violations:")
        for err in double_errors:
            print(f"  {err}")
        return 1

    for md_file, dir_name in entries:
        errors, warnings, has_refs = validate_post(md_file, dir_name)
        if has_refs:
            checked_with_images += 1
        for w in warnings:
            warn_items.append((dir_name, w))
        if errors:
            format_failures.append((dir_name, errors))

    if label == "single":
        print(f"Checked post: {entries[0][1]}")
    elif label == "staged":
        print(f"Checked {len(entries)} staged post(s) ({checked_with_images} with image refs)")
    else:
        print(f"Checked {len(entries)} posts ({checked_with_images} with image refs)")

    if warn_items:
        print(f"⚠️  {len(warn_items)} image size warning(s):")
        for slug, msg in warn_items:
            print(f"  {slug}: {msg}")

    if format_failures:
        print(f"❌ {len(format_failures)} post(s) with validation errors:")
        for slug, errors in format_failures:
            print(f"  {slug}:")
            for err in errors:
                print(f"    - {err}")
        return 1

    if warn_items:
        print("✅ All post validation checks passed (with size warnings above)")
    else:
        print("✅ All post validation checks passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Hugo post rules")
    parser.add_argument(
        "--post",
        metavar="SLUG_OR_PATH",
        help="Check a single post (slug dir name or path to index.md)",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Check posts with staged changes under content/posts/",
    )
    args = parser.parse_args()

    if args.post and args.staged:
        print("❌ Use only one of --post or --staged")
        return 1

    if args.post:
        try:
            md_file, dir_name = resolve_post_path(args.post)
        except FileNotFoundError as exc:
            print(f"❌ {exc}")
            return 1
        return run_checks([(md_file, dir_name)], [md_file.parent], "single")

    if args.staged:
        entries = get_staged_post_entries()
        if not entries:
            print("No staged post changes under content/posts/")
            return 0
        post_dirs = [md_file.parent for md_file, _ in entries]
        return run_checks(entries, post_dirs, "staged")

    entries = list_post_entries_from_git()
    if not entries:
        print("❌ No posts found via git ls-files under content/posts/")
        return 1
    return run_checks(entries, None, "all")


if __name__ == "__main__":
    sys.exit(main())
