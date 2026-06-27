"""Pure helpers for Medium legacy redirect tooling (testable without Playwright)."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

BANNER_MARKERS = ("請點此閱讀最新版本", "最新版本已移至自架部落格", "本文已搬家至自架部落格")
DEFAULT_BANNER_MARKER = BANNER_MARKERS[0]
LEGACY_BODY_PATTERNS = (
    "最新版本已移至自架部落格",
    "本文已搬家至自架部落格",
    "**本文已搬家",
)

CANONICAL_RE = re.compile(
    r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
CANONICAL_RE_ALT = re.compile(
    r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']',
    re.IGNORECASE,
)
TITLE_TAG_RE = re.compile(r"<title[^>]*>([^<]+)</title>", re.IGNORECASE)
CANONICAL_JSON_RE = re.compile(
    r'"canonicalUrl"\s*:\s*"((?:\\.|[^"\\])*)"',
    re.IGNORECASE,
)


def normalize_blog_url(url: str) -> str:
    """Fix common URL typos (en-dash in path) and ensure trailing slash."""
    cleaned = url.strip().replace("\u2013", "-").replace("\u2014", "-")
    if not cleaned.endswith("/"):
        cleaned += "/"
    return cleaned


def render_banner(medium_title: str, blog_url: str, template: str) -> str:
    return template.format(
        medium_title=medium_title,
        blog_url=normalize_blog_url(blog_url),
    ).strip()


def verify_blog_url(url: str) -> tuple[bool, int | None]:
    normalized = normalize_blog_url(url)
    request = Request(
        normalized,
        method="HEAD",
        headers={"User-Agent": "cloudarchitectec-medium-legacy/1.0"},
    )
    try:
        with urlopen(request, timeout=20) as response:
            return 200 <= response.status < 300, response.status
    except HTTPError as exc:
        if exc.code in (405, 501):
            with urlopen(
                Request(normalized, headers={"User-Agent": "cloudarchitectec-medium-legacy/1.0"}),
                timeout=20,
            ) as response:
                return 200 <= response.status < 300, response.status
        return False, exc.code
    except URLError:
        return False, None


def fetch_page_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": "cloudarchitectec-medium-legacy/1.0"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_canonical_url(html: str) -> str | None:
    for pattern in (CANONICAL_RE, CANONICAL_RE_ALT):
        match = pattern.search(html)
        if match:
            return match.group(1).strip()
    json_match = CANONICAL_JSON_RE.search(html)
    if json_match:
        return json.loads(f'"{json_match.group(1)}"').strip()
    return None


def canonical_matches(html: str, expected_blog_url: str) -> bool:
    found = parse_canonical_url(html)
    if not found:
        return False
    return normalize_blog_url(found) == normalize_blog_url(expected_blog_url)


def banner_present_in_html(html: str, marker: str = DEFAULT_BANNER_MARKER) -> bool:
    return marker in html


def title_matches(html: str, expected_title: str) -> bool:
    if not expected_title:
        return False
    title_match = TITLE_TAG_RE.search(html)
    if title_match:
        page_title = title_match.group(1).strip()
        if any(marker in page_title for marker in BANNER_MARKERS):
            return False
        if expected_title in page_title:
            return True
    return expected_title in html and not any(marker in html[:2000] for marker in BANNER_MARKERS[:2])


@dataclass
class PostReportRow:
    post_title: str
    medium_link: str
    blog_site_link: str
    status: str
    blog_url_ok: bool = False
    blog_http_status: int | None = None
    canonical_ok: bool = False
    canonical_found: str = ""
    banner_ok: bool = False
    title_ok: bool = False
    notes: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_csv_dict(self) -> dict[str, str]:
        data = asdict(self)
        return {key: str(value) for key, value in data.items()}


def write_report(rows: list[PostReportRow], csv_path: Path, json_path: Path | None = None) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].to_csv_dict().keys())
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_csv_dict())
    if json_path:
        json_path.write_text(
            json.dumps([asdict(r) for r in rows], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def overall_status(row: PostReportRow) -> str:
    if row.status == "failed":
        return "failed"
    checks = [row.blog_url_ok, row.canonical_ok, row.banner_ok, row.title_ok]
    if all(checks):
        return "ok"
    if any(checks):
        return "partial"
    return "failed"


def is_legacy_paragraph(text: str, medium_title: str, blog_title: str = "") -> bool:
    stripped = text.strip().strip("*").lstrip(">").strip()
    if not stripped:
        return False
    for pattern in LEGACY_BODY_PATTERNS:
        if pattern in stripped:
            return True
    if stripped.startswith("請點此閱讀最新版本"):
        return True
    normalized_medium = re.sub(r"\s+", "", medium_title)
    normalized_blog = re.sub(r"\s+", "", blog_title) if blog_title else ""
    normalized_stripped = re.sub(r"\s+", "", stripped)
    if normalized_stripped == normalized_medium:
        return True
    if normalized_blog and normalized_stripped == normalized_blog:
        return True
    return False
