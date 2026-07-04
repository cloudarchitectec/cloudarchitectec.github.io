#!/usr/bin/env python3
"""Export a CSV worklist for manual Medium legacy updates."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from medium_legacy_utils import normalize_blog_url

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"
DEFAULT_MAPPING = OUTPUT_DIR / "medium-mapping.json"
DEFAULT_ARCHIVE_CACHE = OUTPUT_DIR / "medium-archive-cache.json"
DEFAULT_OUTPUT = OUTPUT_DIR / "medium-manual-worklist.csv"
MEDIUM_ID_RE = re.compile(r"^[a-f0-9]{8,}$")


def load_rows(mapping_path: Path) -> list[dict]:
    payload = json.loads(mapping_path.read_text(encoding="utf-8"))
    return payload.get("posts", [])


def is_actionable(row: dict) -> bool:
    medium_id = row.get("medium_id", "")
    blog_url = row.get("blog_url", "").strip()
    if not blog_url or not MEDIUM_ID_RE.match(medium_id):
        return False
    return True


def to_worklist_row(row: dict) -> dict[str, str]:
    medium_id = row["medium_id"]
    medium_url = row.get("medium_url", "").strip()
    if not medium_url:
        medium_url = f"https://medium.com/p/{medium_id}"
    return {
        "story_name": row.get("medium_title", "").strip(),
        "medium_link": medium_url.split("?")[0],
        "ec_site_link": normalize_blog_url(row["blog_url"]),
        "medium_settings_link": f"https://medium.com/p/{medium_id}/settings",
    }


def export_worklist(
    mapping_path: Path,
    output_path: Path,
    *,
    include_done: bool,
) -> int:
    rows = load_rows(mapping_path)
    actionable = [row for row in rows if is_actionable(row)]
    if not include_done:
        actionable = [row for row in actionable if row.get("status") != "done"]

    actionable.sort(
        key=lambda row: row.get("medium_published_at", "") or "",
        reverse=True,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ("story_name", "medium_link", "ec_site_link", "medium_settings_link")
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in actionable:
            writer.writerow(to_worklist_row(row))

    return len(actionable)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export manual Medium redirect worklist CSV")
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--include-done",
        action="store_true",
        help="Include posts already marked done in medium-mapping.json",
    )
    args = parser.parse_args()

    if not args.mapping.exists():
        print(f"Missing mapping: {args.mapping}")
        print("Run: python3 tools/medium-legacy/update_medium_posts.py --list-stories")
        print("Then: python3 tools/medium-legacy/build_mapping.py")
        return 1

    count = export_worklist(args.mapping, args.output, include_done=args.include_done)
    print(f"Wrote {count} rows -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
