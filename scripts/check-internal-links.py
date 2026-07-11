#!/usr/bin/env python3
"""Scan built HTML under public/ for broken internal links and malformed external URLs (no network)."""

from __future__ import annotations

import argparse
import re
import sys
from html import unescape
from pathlib import Path
from urllib.parse import unquote, urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
LINK_ATTR_RE = re.compile(
    r'(?:href|src)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s"\'=<>`]+))',
    re.IGNORECASE,
)
SKIP_PREFIXES = ("mailto:", "tel:", "javascript:", "data:")
INVALID_URL_CHARS = ("{", "}", "(", ")", ";")
TEMPLATE_LEAK_CHARS = ("{", "}")
STATIC_EXTENSIONS = {
    ".html",
    ".xml",
    ".css",
    ".js",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".json",
    ".txt",
    ".map",
}


def should_skip_internal(raw: str) -> bool:
    raw = raw.strip()
    if not raw or raw.startswith("#"):
        return True
    if raw.startswith(SKIP_PREFIXES):
        return True
    if any(ch in raw for ch in INVALID_URL_CHARS):
        return True
    parsed = urlparse(raw)
    if parsed.scheme in ("http", "https"):
        return True
    return False


def looks_like_path(raw: str) -> bool:
    if raw.startswith(("/", "./", "../")):
        return True
    if re.search(r"\.[a-z0-9]{2,5}(?:[?#]|$)", raw, re.IGNORECASE):
        return True
    return False


def is_external_url(raw: str) -> bool:
    raw = unescape(raw.strip())
    if not raw or raw.startswith("#") or raw.startswith(SKIP_PREFIXES):
        return False
    if raw.startswith("//"):
        return True
    parsed = urlparse(raw)
    return parsed.scheme in ("http", "https")


def external_url_error(raw: str) -> str | None:
    decoded = unescape(raw.strip())
    if not is_external_url(decoded):
        return None
    if any(ch in decoded for ch in TEMPLATE_LEAK_CHARS):
        return "template or invalid characters"
    if " " in decoded:
        return "contains whitespace"
    parsed = urlparse(decoded if not decoded.startswith("//") else f"https:{decoded}")
    if not parsed.netloc:
        return "missing host"
    return None


def resolve_target(page: Path, public_dir: Path, raw: str) -> Path | None:
    raw = unquote(raw.strip())
    if should_skip_internal(raw):
        return None

    # Strip URL fragment / query before resolving the path — browsers resolve the
    # document by path and apply #fragment / ?query afterwards (e.g. "/#newsletter"
    # is the home page, not a file named "#newsletter").
    raw = raw.split("#", 1)[0].split("?", 1)[0]
    if not raw:
        return None

    public_dir = public_dir.resolve()
    page = page.resolve()

    if raw.startswith("/"):
        target = public_dir / raw.lstrip("/")
    else:
        target = (page.parent / raw).resolve()
        try:
            target.relative_to(public_dir)
        except ValueError:
            return None

    if target.is_dir():
        return target / "index.html"
    if target.suffix in STATIC_EXTENSIONS or target.is_file():
        return target
    if (target / "index.html").is_file():
        return target / "index.html"
    for ext in (".html", ""):
        candidate = Path(str(target) + ext) if ext else target
        if candidate.is_file():
            return candidate
    return target


def target_exists(target: Path | None) -> bool:
    if target is None:
        return True
    return target.is_file()


def scan_links(
    public_dir: Path,
    limit: int = 20,
) -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str]], int]:
    """Return (broken internal links, malformed external URLs, unique external URL count)."""
    broken: list[tuple[str, str, str]] = []
    bad_external: list[tuple[str, str, str]] = []
    external_urls: set[str] = set()
    html_files = sorted(public_dir.rglob("*.html"))
    for page in html_files:
        text = page.read_text(encoding="utf-8", errors="replace")
        rel_page = page.relative_to(public_dir).as_posix()
        for match in LINK_ATTR_RE.finditer(text):
            raw = match.group(1) or match.group(2) or match.group(3)
            if not raw:
                continue

            ext_err = external_url_error(raw)
            if ext_err is not None:
                bad_external.append((rel_page, raw, ext_err))
                if len(bad_external) >= limit:
                    return broken, bad_external, len(external_urls)
                continue

            if is_external_url(raw):
                external_urls.add(unescape(raw.strip()))
                continue

            if should_skip_internal(raw) or not looks_like_path(raw):
                continue
            target = resolve_target(page, public_dir, raw)
            if target_exists(target):
                continue
            broken.append((rel_page, raw, str(target.relative_to(public_dir))))
            if len(broken) >= limit:
                return broken, bad_external, len(external_urls)
    return broken, bad_external, len(external_urls)


def scan_public(public_dir: Path, limit: int = 20) -> list[tuple[str, str, str]]:
    """Backward-compatible: broken internal links only."""
    broken, _, _ = scan_links(public_dir, limit=limit)
    return broken


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check internal and external links in Hugo public/ output (no network)",
    )
    parser.add_argument(
        "--public-dir",
        type=Path,
        default=REPO_ROOT / "public",
        help="Hugo output directory (default: public)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Stop after this many issues per category (default: 20)",
    )
    parser.add_argument(
        "--list-external",
        action="store_true",
        help="Print unique external http(s) URLs found in built HTML",
    )
    args = parser.parse_args()
    public_dir = args.public_dir.resolve()
    if not public_dir.is_dir():
        print(f"public dir not found: {public_dir}", file=sys.stderr)
        return 1

    broken, bad_external, external_count = scan_links(public_dir, limit=args.limit)

    if args.list_external:
        urls: set[str] = set()
        for page in sorted(public_dir.rglob("*.html")):
            text = page.read_text(encoding="utf-8", errors="replace")
            for match in LINK_ATTR_RE.finditer(text):
                raw = match.group(1) or match.group(2) or match.group(3)
                if raw and is_external_url(raw) and external_url_error(raw) is None:
                    urls.add(unescape(raw.strip()))
        for url in sorted(urls):
            print(url)
        print(f"({len(urls)} unique external URLs)", file=sys.stderr)
        return 0

    exit_code = 0
    if broken:
        exit_code = 1
        print(f"❌ {len(broken)} broken internal link(s):", file=sys.stderr)
        for page, raw, target in broken:
            print(f"  {page}: {raw} -> {target}", file=sys.stderr)
    else:
        print(f"✅ Internal links OK ({public_dir})")

    if bad_external:
        exit_code = 1
        print(f"❌ {len(bad_external)} malformed external URL(s):", file=sys.stderr)
        for page, raw, reason in bad_external:
            print(f"  {page}: {raw} ({reason})", file=sys.stderr)
    else:
        print(f"✅ External URL format OK ({external_count} unique http(s) URLs scanned)")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
