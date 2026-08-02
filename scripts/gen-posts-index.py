#!/usr/bin/env python3
"""Generate docs/POSTS-INDEX.md — a one-file map of every post.

Locate a post by title / category / tags / summary from the index instead of
globbing 200+ post bundles. The posts are the source of truth; this file is
derived. Regenerate after adding or editing posts:

    python3 scripts/gen-posts-index.py            # rewrite docs/POSTS-INDEX.md
    python3 scripts/gen-posts-index.py --check    # exit 1 if stale (CI/pre-commit)

Wired into scripts/dev-check.sh and tools/blog-publisher/pre-publish-post.py.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = REPO_ROOT / "content" / "posts"
OUTPUT = REPO_ROOT / "docs" / "POSTS-INDEX.md"

SUMMARY_MAX = 60  # chars (CJK-heavy, so keep short)

# Lines we skip when hunting for the first prose line of the body.
_SKIP_LINE = re.compile(
    r"^\s*("
    r"#"           # markdown heading
    r"|!\["        # image
    r"|<!--"       # html comment
    r"|\{\{"       # hugo shortcode
    r"|>\s*\["     # note/callout blockquote
    r"|---\s*$"    # hr
    r"|\|"         # table
    r")"
)
_MD_NOISE = re.compile(r"[*_`#>\[\]]")  # inline markdown to strip from summary

# Paired shortcodes ({{< outdated >}} … {{< /outdated >}}) wrap editorial notes,
# not the post's own opening — skip their inner lines too, or the summary becomes
# the notice instead of the article.
_SC_OPEN = re.compile(r"^\s*\{\{[<%]\s*(\w+)")
_SC_CLOSE = re.compile(r"^\s*\{\{[<%]\s*/\s*(\w+)")


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body). Tolerates a blank line before '---'."""
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return {}, text
    parts = stripped.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        meta = {}
    return (meta if isinstance(meta, dict) else {}), parts[2]


def extract_summary(body: str) -> str:
    # Only names that are actually closed somewhere open a block; a self-closing
    # shortcode ({{< figure >}}) must not swallow the rest of the post.
    paired = {m.group(1) for m in map(_SC_CLOSE.match, body.splitlines()) if m}
    open_shortcode: str | None = None
    for raw in body.splitlines():
        line = raw.strip()
        if open_shortcode:
            closing = _SC_CLOSE.match(line)
            if closing and closing.group(1) == open_shortcode:
                open_shortcode = None
            continue
        opening = _SC_OPEN.match(line)
        if opening and not _SC_CLOSE.match(line) and opening.group(1) in paired:
            open_shortcode = opening.group(1)
            continue
        if not line or _SKIP_LINE.match(line):
            continue
        clean = _MD_NOISE.sub("", line).strip()
        clean = re.sub(r"\s+", " ", clean).replace("|", "/")
        if not clean:
            continue
        if len(clean) > SUMMARY_MAX:
            clean = clean[:SUMMARY_MAX].rstrip() + "…"
        return clean
    return ""


def cell(value) -> str:
    """Flatten a scalar/list frontmatter value into a safe table cell."""
    if value is None:
        return ""
    if isinstance(value, list):
        value = ", ".join(str(v) for v in value)
    return str(value).replace("|", "/").replace("\n", " ").strip()


def collect_posts() -> list[dict]:
    posts = []
    for index_md in sorted(POSTS_DIR.glob("*/index.md")):
        meta, body = split_frontmatter(index_md.read_text(encoding="utf-8"))
        if meta.get("draft") is True:
            continue
        folder = index_md.parent.name
        section = cell(meta.get("categories"))
        series = cell(meta.get("episodeseries"))
        if series:
            section = f"{section} · 系列:{series}" if section else f"系列:{series}"
        posts.append(
            {
                "date": cell(meta.get("date")) or folder[:10],
                "title": cell(meta.get("title")) or folder,
                "section": section,
                "tags": cell(meta.get("tags")),
                "summary": extract_summary(body),
                "folder": f"content/posts/{folder}",
            }
        )
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def render(posts: list[dict]) -> str:
    lines = [
        "# Posts index",
        "",
        "> **Generated file — do not edit by hand.** Regenerate with "
        "`python3 scripts/gen-posts-index.py`.",
        ">",
        "> Purpose: locate a post by title / section / tags / summary from this "
        "one file instead of scanning `content/posts/`. Open the folder in the "
        "last column to read or edit the post.",
        "",
        f"**{len(posts)} published posts** (newest first).",
        "",
        "| Date | Title | Section | Tags | Summary | Folder |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for p in posts:
        lines.append(
            f"| {p['date']} | {p['title']} | {p['section']} | {p['tags']} "
            f"| {p['summary']} | {p['folder']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if docs/POSTS-INDEX.md is out of date (do not write).",
    )
    args = parser.parse_args()

    posts = collect_posts()
    content = render(posts)

    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != content:
            print(
                "docs/POSTS-INDEX.md is stale — run: python3 scripts/gen-posts-index.py",
                file=sys.stderr,
            )
            return 1
        print("docs/POSTS-INDEX.md is up to date.")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"✅ Wrote {OUTPUT.relative_to(REPO_ROOT)} ({len(posts)} posts)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
