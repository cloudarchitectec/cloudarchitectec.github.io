#!/usr/bin/env python3
"""Build Medium RSS ↔ Hugo post mapping for legacy redirect tooling."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"
PROJECT_ROOT = SCRIPT_DIR.parent.parent
HUGO_POSTS_DIR = PROJECT_ROOT / "content" / "posts"
DEFAULT_RSS_URL = "https://medium.com/feed/@cloudarchitectec"
DEFAULT_BASE_URL = "https://cloudarchitectec.com"
DEFAULT_OUTPUT = OUTPUT_DIR / "medium-mapping.json"
DEFAULT_ARCHIVE_CACHE = OUTPUT_DIR / "medium-archive-cache.json"
MANUAL_OVERRIDES = SCRIPT_DIR / "manual_overrides.json"

TITLE_SUFFIXES = (
    "| 澳洲雲端架構師 EC",
    "| 澳洲雲端架構師 EC (Cloud Architect EC)",
    " | 澳洲雲端架構師 EC",
)

BANNER_MARKER = "最新版本已移至自架部落格"
EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E0-\U0001F1FF"
    "]+",
    flags=re.UNICODE,
)


@dataclass
class MediumPost:
    medium_id: str
    medium_url: str
    medium_title: str
    published_at: date | None


@dataclass
class HugoPost:
    slug: str
    blog_url: str
    title: str
    published_at: date
    draft: bool


def normalize_title(title: str) -> str:
    text = title.strip()
    for suffix in TITLE_SUFFIXES:
        if text.endswith(suffix):
            text = text[: -len(suffix)].strip()
    text = EMOJI_RE.sub("", text)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s*:\s*", ":", text)
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[「」『』\"'“”‘’（）()【】\[\]…~～!！?？:：,，.。、·\-—–|｜]", "", text)
    return text.lower()


def title_signature(title: str) -> str:
    """Extract stable date/day fragment for episodic series titles."""
    text = EMOJI_RE.sub("", title)
    match = re.search(r"(20\d{2}\.\d{2}\.\d{2}(?:–\d{2}\.\d{2})?|Day\s*\d+)", text, re.I)
    if match:
        return re.sub(r"\s+", "", match.group(1)).lower()
    match = re.search(r"(20\d{2}\.\d{2}\.\d{2})", text)
    if match:
        return match.group(1)
    return ""


def parse_hugo_date(raw: str) -> date:
    raw = raw.strip().strip('"').strip("'")
    if "T" in raw:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    return date.fromisoformat(raw[:10])


def load_hugo_posts(base_url: str) -> list[HugoPost]:
    posts: list[HugoPost] = []
    for index_path in sorted(HUGO_POSTS_DIR.glob("*/index.md")):
        text = index_path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        parts = text.split("---", 2)
        if len(parts) < 3:
            continue
        fm = parts[1]
        title_match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', fm, re.M)
        date_match = re.search(r"^date:\s*(.+)$", fm, re.M)
        slug_match = re.search(r'^slug:\s*["\']?(.+?)["\']?\s*$', fm, re.M)
        draft_match = re.search(r"^draft:\s*true\s*$", fm, re.M | re.I)
        if not title_match or not date_match:
            continue
        slug = slug_match.group(1).strip() if slug_match else index_path.parent.name
        title = title_match.group(1).strip()
        published_at = parse_hugo_date(date_match.group(1))
        posts.append(
            HugoPost(
                slug=slug,
                blog_url=f"{base_url.rstrip('/')}/posts/{slug}/",
                title=title,
                published_at=published_at,
                draft=bool(draft_match),
            )
        )
    return posts


def extract_medium_id(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if path.startswith("/p/"):
        return path.split("/")[2]
    slug_part = path.rsplit("/", 1)[-1]
    if "-" in slug_part:
        return slug_part.rsplit("-", 1)[-1]
    return slug_part


def fetch_medium_posts_rss(rss_url: str) -> list[MediumPost]:
    request = Request(
        rss_url,
        headers={"User-Agent": "cloudarchitectec-medium-legacy-mapping/1.0"},
    )
    with urlopen(request, timeout=60) as response:
        xml_text = response.read()
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        raise RuntimeError("RSS feed missing channel element")
    posts: list[MediumPost] = []
    for item in channel.findall("item"):
        title_el = item.find("title")
        link_el = item.find("link")
        pub_el = item.find("pubDate")
        guid_el = item.find("guid")
        if title_el is None or title_el.text is None:
            continue
        medium_url = ""
        if link_el is not None and link_el.text:
            medium_url = link_el.text.strip()
        elif guid_el is not None and guid_el.text:
            medium_url = guid_el.text.strip()
        if not medium_url:
            continue
        published_at = (
            parsedate_to_datetime(pub_el.text).date()
            if pub_el is not None and pub_el.text
            else None
        )
        medium_id = extract_medium_id(medium_url)
        posts.append(
            MediumPost(
                medium_id=medium_id,
                medium_url=medium_url.split("?")[0],
                medium_title=title_el.text.strip(),
                published_at=published_at,
            )
        )
    return posts


def load_archive_cache(path: Path) -> list[MediumPost]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    posts: list[MediumPost] = []
    for story in data.get("stories", []):
        medium_id = story.get("medium_id") or extract_medium_id(story.get("medium_url", ""))
        posts.append(
            MediumPost(
                medium_id=medium_id,
                medium_url=story["medium_url"].split("?")[0],
                medium_title=story.get("medium_title", ""),
                published_at=None,
            )
        )
    return posts


def merge_medium_posts(*sources: list[MediumPost]) -> list[MediumPost]:
    merged: dict[str, MediumPost] = {}
    for source in sources:
        for post in source:
            existing = merged.get(post.medium_id)
            if existing is None:
                merged[post.medium_id] = post
                continue
            merged[post.medium_id] = MediumPost(
                medium_id=post.medium_id,
                medium_url=post.medium_url or existing.medium_url,
                medium_title=post.medium_title or existing.medium_title,
                published_at=post.published_at or existing.published_at,
            )
    return list(merged.values())


def load_manual_overrides() -> dict[str, dict]:
    if not MANUAL_OVERRIDES.exists():
        return {}
    data = json.loads(MANUAL_OVERRIDES.read_text(encoding="utf-8"))
    return {entry["medium_id"]: entry for entry in data.get("overrides", [])}


def pick_hugo_match(medium: MediumPost, candidates: list[HugoPost]) -> HugoPost | None:
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    sig = title_signature(medium.medium_title)
    if sig:
        sig_matches = [c for c in candidates if title_signature(c.title) == sig]
        if len(sig_matches) == 1:
            return sig_matches[0]

    if medium.published_at:
        dated = sorted(
            candidates,
            key=lambda c: abs((c.published_at - medium.published_at).days),
        )
        if abs((dated[0].published_at - medium.published_at).days) <= 1:
            return dated[0]
    return sorted(candidates, key=lambda c: c.published_at, reverse=True)[0]


def match_posts(
    medium_posts: list[MediumPost],
    hugo_posts: list[HugoPost],
    overrides: dict[str, dict],
    auto_approve_title_only: bool,
) -> list[dict]:
    published_hugo = [p for p in hugo_posts if not p.draft]
    by_norm_title: dict[str, list[HugoPost]] = {}
    for post in published_hugo:
        by_norm_title.setdefault(normalize_title(post.title), []).append(post)

    rows: list[dict] = []
    for medium in sorted(medium_posts, key=lambda p: p.medium_title):
        override = overrides.get(medium.medium_id)
        if override:
            hugo = next((p for p in published_hugo if p.slug == override["blog_slug"]), None)
            rows.append(
                {
                    "medium_id": medium.medium_id,
                    "medium_url": medium.medium_url,
                    "medium_title": medium.medium_title,
                    "medium_published_at": medium.published_at.isoformat() if medium.published_at else "",
                    "blog_slug": override["blog_slug"],
                    "blog_url": override.get("blog_url")
                    or f"{DEFAULT_BASE_URL.rstrip('/')}/posts/{override['blog_slug']}/",
                    "blog_title": hugo.title if hugo else override.get("blog_title", ""),
                    "match_confidence": "manual",
                    "status": "pending",
                }
            )
            continue

        norm = normalize_title(medium.medium_title)
        candidates = by_norm_title.get(norm, [])
        exact_date = []
        if medium.published_at:
            exact_date = [
                c for c in candidates if abs((c.published_at - medium.published_at).days) <= 1
            ]

        if len(exact_date) == 1:
            hugo = exact_date[0]
            confidence = "exact"
        elif candidates:
            hugo = pick_hugo_match(medium, candidates)
            confidence = "exact" if hugo and normalize_title(hugo.title) == norm else "title_only"
        else:
            rows.append(
                {
                    "medium_id": medium.medium_id,
                    "medium_url": medium.medium_url,
                    "medium_title": medium.medium_title,
                    "medium_published_at": medium.published_at.isoformat() if medium.published_at else "",
                    "blog_slug": "",
                    "blog_url": "",
                    "blog_title": "",
                    "match_confidence": "unmatched",
                    "status": "needs_review",
                }
            )
            continue

        if hugo is None:
            rows.append(
                {
                    "medium_id": medium.medium_id,
                    "medium_url": medium.medium_url,
                    "medium_title": medium.medium_title,
                    "medium_published_at": medium.published_at.isoformat() if medium.published_at else "",
                    "blog_slug": "",
                    "blog_url": "",
                    "blog_title": "",
                    "match_confidence": "unmatched",
                    "status": "needs_review",
                }
            )
            continue

        if confidence == "exact":
            status = "pending"
        elif auto_approve_title_only and normalize_title(hugo.title) == norm:
            status = "pending"
        else:
            status = "needs_review"

        rows.append(
            {
                "medium_id": medium.medium_id,
                "medium_url": medium.medium_url,
                "medium_title": medium.medium_title,
                "medium_published_at": medium.published_at.isoformat() if medium.published_at else "",
                "blog_slug": hugo.slug,
                "blog_url": hugo.blog_url,
                "blog_title": hugo.title,
                "match_confidence": confidence,
                "status": status,
            }
        )
    return rows


def print_summary(rows: list[dict]) -> None:
    counts: dict[str, int] = {}
    for row in rows:
        key = row["match_confidence"]
        counts[key] = counts.get(key, 0) + 1
    print(f"Medium stories: {len(rows)}")
    for key in ("exact", "manual", "title_only", "unmatched"):
        if counts.get(key):
            print(f"  {key}: {counts[key]}")
    pending = sum(1 for r in rows if r["status"] == "pending")
    needs_review = [r for r in rows if r["status"] == "needs_review"]
    print(f"  ready (pending): {pending}")
    if needs_review:
        print(f"  needs_review: {len(needs_review)}")
        for row in needs_review[:20]:
            print(f"    - {row['medium_id']}: {row['medium_title']}")
        if len(needs_review) > 20:
            print(f"    ... and {len(needs_review) - 20} more")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Medium ↔ Hugo mapping JSON")
    parser.add_argument("--rss-url", default=DEFAULT_RSS_URL)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--archive-cache", type=Path, default=DEFAULT_ARCHIVE_CACHE)
    parser.add_argument(
        "--auto-approve-title-only",
        action="store_true",
        default=True,
        help="Mark title-only matches as pending when normalized titles match (default: on)",
    )
    args = parser.parse_args()

    rss_posts = fetch_medium_posts_rss(args.rss_url)
    cache_posts = load_archive_cache(args.archive_cache)
    medium_posts = merge_medium_posts(cache_posts, rss_posts)
    if not medium_posts:
        print("No Medium stories found. Run update_medium_posts.py --list-stories first.")
        return 1

    hugo_posts = load_hugo_posts(args.base_url)
    overrides = load_manual_overrides()
    rows = match_posts(medium_posts, hugo_posts, overrides, args.auto_approve_title_only)

    payload = {
        "generated_at": datetime.now().isoformat(),
        "rss_url": args.rss_url,
        "archive_cache": str(args.archive_cache),
        "base_url": args.base_url,
        "banner_marker": BANNER_MARKER,
        "posts": rows,
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print_summary(rows)
    print(f"\nWrote {args.output}")
    if len(medium_posts) < 50:
        print(
            "\nNote: Medium RSS returns only the latest 10 stories. "
            "For all ~110 posts, run:\n"
            "  python3 tools/medium-legacy/update_medium_posts.py --login\n"
            "  python3 tools/medium-legacy/update_medium_posts.py --list-stories\n"
            "  python3 tools/medium-legacy/build_mapping.py"
        )
    unmatched = sum(1 for r in rows if r["match_confidence"] == "unmatched")
    return 1 if unmatched else 0


if __name__ == "__main__":
    sys.exit(main())
