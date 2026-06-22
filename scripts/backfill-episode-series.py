#!/usr/bin/env python3
"""One-time backfill: set episodeseries on multi-part series posts only."""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = REPO_ROOT / "content" / "posts"


def split_post(text: str) -> tuple[str, str]:
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text
    return parts[1], parts[2]


def get_fm_scalar(fm: str, key: str) -> str | None:
    for line in fm.splitlines():
        m = re.match(rf'^\s*{re.escape(key)}:\s*"(.*)"\s*$', line)
        if m:
            return m.group(1)
        m = re.match(rf"^\s*{re.escape(key)}:\s*'(.*)'\s*$", line)
        if m:
            return m.group(1)
    return None


def get_fm_categories(fm: str) -> list[str]:
    for line in fm.splitlines():
        m = re.match(r'^\s*categories:\s*\[(.*)\]\s*$', line)
        if not m:
            continue
        inner = m.group(1)
        values = re.findall(r'"([^"]+)"', inner)
        if not values:
            values = re.findall(r"'([^']+)'", inner)
        return values
    return []


def detect_episodeseries(slug: str, title: str, category: str) -> str | None:
    bracket = re.match(r"^\[([^\]]+)\]", title)
    if bracket:
        return bracket.group(1)
    if title.startswith("好想要退休"):
        return "好想要退休"
    if title.startswith("零基礎轉職澳洲工程師") or category == "零基礎轉職澳洲工程師":
        return "零基礎轉職澳洲工程師"
    if re.search(r"ms-csa-[0-9]+$", slug):
        return "微軟雲端架構師 (Solution Architect) 職位解析"
    if "devops-interview" in slug:
        return "DevOps 面試紀錄"
    if "qld-first-home" in slug:
        return "QLD 首購房"
    if "vanuatu-day" in slug or slug == "2025-04-28-vanuatu-summary":
        return "萬那杜旅記"
    if "carnival-splendor" in slug:
        return "Carnival Splendor 郵輪"
    if re.search(r"nz-day[0-9]", slug) or slug == "2024-09-02-nz-summary":
        return "紐西蘭旅記"
    if "fiji-day" in slug:
        return "斐濟旅記"
    if title.startswith("一個女生的歐洲獨旅"):
        return "一個女生的歐洲獨旅"
    if "2025-mel-trip" in slug:
        return "2025 墨爾本澳網行"
    if "2025-nz-trip-snowboarding" in slug:
        return "2025 紐西蘭滑雪之旅"
    if "倖存者日記" in title and category == "海外職場":
        return "倖存者日記"
    return None


def set_episodeseries(text: str, value: str) -> str:
    fm, body = split_post(text)
    lines = fm.splitlines()
    kept: list[str] = []
    for line in lines:
        if line.strip().startswith("episodeseries:"):
            continue
        kept.append(line)

    insert_at = len(kept)
    for i, line in enumerate(kept):
        if line.startswith("tags:"):
            insert_at = i + 1
            break
    else:
        for i, line in enumerate(kept):
            if line.startswith("categories:"):
                insert_at = i + 1
                break

    kept.insert(insert_at, f'episodeseries: ["{value}"]')
    fm_block = "\n".join(kept)
    if not fm_block.endswith("\n"):
        fm_block += "\n"
    return f"---\n{fm_block}---{body}"


def remove_episodeseries(text: str) -> str:
    fm, body = split_post(text)
    lines = [ln for ln in fm.splitlines() if not ln.strip().startswith("episodeseries:")]
    fm_block = "\n".join(lines)
    if fm_block and not fm_block.endswith("\n"):
        fm_block += "\n"
    return f"---\n{fm_block}---{body}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing")
    args = parser.parse_args()

    stats: dict[str, list[str]] = defaultdict(list)
    updated = skipped = cleared = 0

    for path in sorted(POSTS_DIR.glob("*/index.md")):
        slug = path.parent.name
        text = path.read_text(encoding="utf-8")
        fm, _ = split_post(text)
        title = get_fm_scalar(fm, "title") or ""
        category = (get_fm_categories(fm) or [""])[0]
        existing = get_fm_scalar(fm, "episodeseries")
        detected = detect_episodeseries(slug, title, category)

        if detected:
            stats[detected].append(slug)
            if existing == detected:
                skipped += 1
                continue
            if existing and existing != detected:
                print(f"⚠️  {slug}: episodeseries {existing!r} → {detected!r}")
            new_text = set_episodeseries(text, detected)
            action = "update" if existing else "add"
        else:
            if existing:
                new_text = remove_episodeseries(text)
                cleared += 1
                print(f"🧹 {slug}: removed episodeseries {existing!r} (non-series)")
            else:
                skipped += 1
                continue
            action = "clear"

        if args.dry_run:
            print(f"[dry-run] {action} {slug} → {detected or '(omit)'}")
        else:
            path.write_text(new_text, encoding="utf-8")
        updated += 1

    print(f"\nSeries groups ({len(stats)}):")
    for label, slugs in sorted(stats.items(), key=lambda x: -len(x[1])):
        print(f"  {label}: {len(slugs)}")
    print(f"\n{'Would update' if args.dry_run else 'Updated'}: {updated}, skipped: {skipped}, cleared: {cleared}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
