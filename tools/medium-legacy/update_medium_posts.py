#!/usr/bin/env python3
"""Medium legacy tooling: login, list stories, optional banner, manual worklist export."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, sync_playwright

from medium_legacy_utils import (
    BANNER_MARKERS,
    DEFAULT_BANNER_MARKER,
    PostReportRow,
    banner_present_in_html,
    canonical_matches,
    fetch_page_html,
    is_legacy_paragraph,
    normalize_blog_url,
    overall_status,
    parse_canonical_url,
    render_banner,
    title_matches,
    verify_blog_url,
    write_report,
)

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"
DEFAULT_MAPPING = OUTPUT_DIR / "medium-mapping.json"
DEFAULT_SESSION = SCRIPT_DIR / ".medium-session.json"
DEFAULT_PROFILE_DIR = SCRIPT_DIR / ".medium-chrome-profile"
DEFAULT_ERRORS = OUTPUT_DIR / "medium-update-errors.json"
DEFAULT_ARCHIVE_CACHE = OUTPUT_DIR / "medium-archive-cache.json"
DEFAULT_REPORT_CSV = OUTPUT_DIR / "medium-verify-report.csv"
DEFAULT_REPORT_JSON = OUTPUT_DIR / "medium-verify-report.json"
BANNER_TEMPLATE = SCRIPT_DIR / "banner-template.md"
PROFILE_URL = "https://medium.com/@cloudarchitectec"
STORIES_URL = "https://medium.com/me/stories"
DEFAULT_CHANNEL = "chrome"
POST_ID_RE = re.compile(r"/(?:p|@[^/]+/[^/]+-)([a-f0-9]{8,})")
BROWSER_INSTALL_HINT = (
    "Playwright browser is not installed for this Python environment.\n"
    "For bundled Chromium:\n"
    "  playwright install chromium\n"
    "Recommended: use installed Google Chrome (default --channel chrome).\n"
    "If Chrome is missing, install Google Chrome or run with --channel chromium\n"
    "after: python3 tools/medium-legacy/update_medium_posts.py --install-browser"
)
CLOUDFLARE_HINT = (
    "Cloudflare blocked automated login (common with bundled Chromium).\n"
    "Try one of these:\n"
    "  1. python3 tools/medium-legacy/update_medium_posts.py --login\n"
    "     (uses your installed Google Chrome, not 'Chrome for Testing')\n"
    "  2. python3 tools/medium-legacy/update_medium_posts.py --login-codegen\n"
    "     (opens real Chrome via Playwright codegen — best for Cloudflare)\n"
    "  3. Log in with email on medium.com instead of 'Continue with Google'\n"
    "  4. Complete the Cloudflare checkbox, wait for redirect, then press Enter"
)


def install_chromium_browser() -> None:
    print("Installing Playwright Chromium (one-time setup)...")
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    print("Chromium installed.")


def launch_kwargs(*, channel: str, headed: bool) -> dict:
    kwargs: dict = {
        "headless": not headed,
        "args": ["--disable-blink-features=AutomationControlled"],
    }
    if channel:
        kwargs["channel"] = channel
    return kwargs


def launch_browser(playwright, *, channel: str, headed: bool):
    try:
        return playwright.chromium.launch(**launch_kwargs(channel=channel, headed=headed))
    except PlaywrightError as exc:
        message = str(exc)
        if "Executable doesn't exist" in message:
            print(BROWSER_INSTALL_HINT, file=sys.stderr)
            raise SystemExit(1) from exc
        if channel == "chrome":
            print("Google Chrome not found; falling back to bundled Chromium.", file=sys.stderr)
            print(CLOUDFLARE_HINT, file=sys.stderr)
            return launch_browser(playwright, channel="", headed=headed)
        raise


def _wait_for_medium_ready(page: Page, *, expect: str | None = None, timeout_ms: int = 45_000) -> bool:
    """Wait until Cloudflare / login interstitials clear."""
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        title = page.title().lower()
        if "just a moment" in title or "checking your browser" in title:
            page.wait_for_timeout(1500)
            continue
        if not _ensure_logged_in(page):
            page.wait_for_timeout(1500)
            continue
        if expect and not page.get_by_text(expect, exact=False).count():
            page.wait_for_timeout(1000)
            continue
        return True
    return False


def open_stories_context(
    playwright,
    *,
    channel: str,
    headed: bool,
    session_path: Path | None,
    profile_dir: Path,
):
    """Use the same Chrome profile as --login (more reliable for /me/stories than storage_state)."""
    viewport = {"width": 1400, "height": 1200}
    if profile_dir.exists() and any(profile_dir.iterdir()):
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            **launch_kwargs(channel=channel, headed=headed),
            viewport=viewport,
            locale="zh-TW",
        )
        return None, context
    return open_automation_context(
        playwright,
        channel=channel,
        headed=headed,
        session_path=session_path,
        profile_dir=profile_dir,
    )


def open_automation_context(
    playwright,
    *,
    channel: str,
    headed: bool,
    session_path: Path | None,
    profile_dir: Path,
):
    """Open Chrome for automation. Prefer codegen session; fall back to persistent profile."""
    viewport = {"width": 1400, "height": 1200}
    if session_path and session_path.exists():
        browser = launch_browser(playwright, channel=channel, headed=headed)
        context = browser.new_context(storage_state=str(session_path), viewport=viewport)
        return browser, context

    if profile_dir.exists() and any(profile_dir.iterdir()):
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            **launch_kwargs(channel=channel, headed=headed),
            viewport=viewport,
            locale="zh-TW",
        )
        return None, context

    browser = launch_browser(playwright, channel=channel, headed=headed)
    return browser, browser.new_context(viewport=viewport)


STORY_LINK_JS = """() => {
  const seen = new Set();
  const out = [];
  for (const a of document.querySelectorAll('a[href]')) {
    const href = a.href.split('?')[0].replace(/\\/$/, '');
    if (!href.includes('medium.com')) continue;
    if (/\\/(edit|stats|settings|import|new-story|followers|following|about|writers)(\\/|$)/.test(href)) continue;
    if (href.includes('following-feed') || href.includes('/me/')) continue;
    const isOwnStory = /@cloudarchitectec\\/[^/]+-[a-f0-9]{8,}$/.test(href)
      || /medium\\.com\\/p\\/[a-f0-9]{8,}$/.test(href);
    if (!isOwnStory) continue;
    const match = href.match(/([a-f0-9]{8,})$/);
    if (!match) continue;
    const id = match[1];
    if (seen.has(id)) continue;
    const text = (a.innerText || '').trim().split('\\n').map(s => s.trim()).find(Boolean) || '';
    if (!text || text.length < 4) continue;
    if (['Follow', 'Following', 'Get app', 'Sign in'].includes(text)) continue;
    seen.add(id);
    out.push({ href, text, id });
  }
  return out;
}"""


def login_and_save_session(
    session_path: Path,
    profile_dir: Path,
    *,
    channel: str,
) -> None:
    """Log in using a persistent Chrome profile (passes Cloudflare more reliably)."""
    profile_dir.mkdir(parents=True, exist_ok=True)
    print(CLOUDFLARE_HINT)
    print("\nOpening Medium in Google Chrome...")
    print("Tip: use **email sign-in** on medium.com if Google OAuth shows Cloudflare.\n")

    with sync_playwright() as playwright:
        try:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                **launch_kwargs(channel=channel, headed=True),
                viewport={"width": 1280, "height": 900},
                locale="zh-TW",
            )
        except PlaywrightError as exc:
            if channel == "chrome" and "Executable doesn't exist" in str(exc):
                print("Google Chrome not found. Install Chrome or use --login-codegen.", file=sys.stderr)
                raise SystemExit(1) from exc
            raise

        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://medium.com/", wait_until="domcontentloaded", timeout=120_000)
        print("1. Sign in to Medium (email login recommended if Google is blocked).")
        print("2. Pass any Cloudflare check and confirm you can open:")
        print(f"   {STORIES_URL}")
        input("3. Press Enter here when logged in ... ")
        page.goto(STORIES_URL, wait_until="domcontentloaded", timeout=120_000)
        page.wait_for_timeout(2000)
        if "signin" in page.url or "login" in page.url:
            print("Still on a login page — session not saved. Try --login-codegen.", file=sys.stderr)
            context.close()
            raise SystemExit(1)
        context.storage_state(path=str(session_path))
        context.close()
    print(f"Saved session to {session_path}")


def login_via_codegen(session_path: Path, *, channel: str) -> None:
    """Open real Chrome via `playwright codegen`; user logs in, then closes the window."""
    print("Launching Playwright codegen (real Chrome).")
    print("1. Log in to Medium and pass Cloudflare if shown.")
    print("2. Close the browser window when finished.")
    print(f"3. Session will be saved to {session_path}\n")
    cmd = [
        sys.executable,
        "-m",
        "playwright",
        "codegen",
        "https://medium.com/me/stories",
        f"--save-storage={session_path}",
    ]
    if channel:
        cmd.extend(["--channel", channel])
    subprocess.run(cmd, check=True)
    if not session_path.exists():
        print("No session file created. Did you close the browser after logging in?", file=sys.stderr)
        raise SystemExit(1)
    print(f"Saved session to {session_path}")


def load_mapping(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_mapping(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_banner_template() -> str:
    return BANNER_TEMPLATE.read_text(encoding="utf-8")


def make_banner(medium_title: str, blog_url: str) -> str:
    return render_banner(medium_title, blog_url, load_banner_template())


def public_medium_url(row: dict) -> str:
    url = row.get("medium_url", "")
    if url:
        return url.split("?")[0]
    return f"https://medium.com/p/{row['medium_id']}"


def extract_post_id(url: str) -> str:
    match = POST_ID_RE.search(url)
    if match:
        return match.group(1)
    return url.rstrip("/").rsplit("-", 1)[-1]



def list_stories(
    session_path: Path,
    output_path: Path,
    *,
    headed: bool,
    channel: str,
) -> int:
    stories: dict[str, dict] = {}
    with sync_playwright() as playwright:
        browser, context = open_stories_context(
            playwright,
            channel=channel,
            headed=headed,
            session_path=session_path if session_path.exists() else None,
            profile_dir=DEFAULT_PROFILE_DIR,
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(PROFILE_URL, wait_until="domcontentloaded", timeout=120_000)
        if not _wait_for_medium_ready(page, timeout_ms=60_000):
            print("Profile page did not load — run --login first.", file=sys.stderr)
        page.wait_for_timeout(3000)

        last_count = 0
        stagnant_rounds = 0
        for _ in range(80):
            items = page.evaluate(STORY_LINK_JS)
            for item in items:
                post_id = item.get("id", "")
                href = item.get("href", "")
                title = item.get("text", "").strip()
                if len(post_id) < 8:
                    continue
                stories[post_id] = {
                    "medium_id": post_id,
                    "medium_url": href,
                    "medium_title": title,
                }
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.keyboard.press("PageDown")
            page.wait_for_timeout(2000)
            if len(stories) == last_count:
                stagnant_rounds += 1
                if stagnant_rounds >= 4:
                    break
            else:
                stagnant_rounds = 0
            last_count = len(stories)

        if session_path and stories:
            context.storage_state(path=str(session_path))
            print(f"  refreshed session -> {session_path}")
        if browser:
            browser.close()
        else:
            context.close()

    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "profile_url": PROFILE_URL,
        "count": len(stories),
        "stories": list(stories.values()),
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Listed {len(stories)} stories -> {output_path}")
    return len(stories)


def _ensure_logged_in(page: Page) -> bool:
    title = page.title().lower()
    if "just a moment" in title or "checking your browser" in title:
        return False
    return "signin" not in page.url and "login" not in page.url


def fix_title_field(page: Page, medium_title: str) -> bool:
    """Restore Medium story title if banner text was typed into the title field."""
    selectors = (
        "h3.graf--title",
        '[data-testid="editorTitleParagraph"]',
        "article h1",
        "h1.graf--title",
    )
    for selector in selectors:
        locator = page.locator(selector).first
        if not locator.count():
            continue
        current = locator.inner_text().strip()
        if current == medium_title:
            return False
        if any(marker in current for marker in BANNER_MARKERS) or current != medium_title:
            locator.click()
            page.keyboard.press("Meta+A")
            page.keyboard.type(medium_title)
            print(f"  title restored -> {medium_title[:40]}...")
            return True

    title_box = page.locator('[contenteditable="true"]').first
    if title_box.count():
        current = title_box.inner_text().strip()
        if current != medium_title and (
            any(marker in current for marker in BANNER_MARKERS) or len(current) > len(medium_title) + 10
        ):
            title_box.click()
            page.keyboard.press("Meta+A")
            page.keyboard.type(medium_title)
            print(f"  title restored (fallback) -> {medium_title[:40]}...")
            return True
    return False


def cleanup_legacy_paragraphs(page: Page, medium_title: str, blog_title: str) -> bool:
    """Remove old banner lines and duplicate title paragraphs from the body."""
    removed = False
    selectors = (
        "article p.graf--p",
        "article [data-testid='editorParagraphText']",
        "article div.graf--p",
    )
    for selector in selectors:
        paragraphs = page.locator(selector)
        count = paragraphs.count()
        if count == 0:
            continue
        for index in range(count - 1, -1, -1):
            para = paragraphs.nth(index)
            text = para.inner_text().strip()
            if not is_legacy_paragraph(text, medium_title, blog_title):
                continue
            para.click()
            page.keyboard.press("Meta+A")
            page.keyboard.press("Backspace")
            removed = True
            page.wait_for_timeout(300)
        if removed:
            print("  removed legacy banner/duplicate paragraphs")
            return True
    return removed


def insert_body_banner(page: Page, banner: str) -> bool:
    """Insert blockquote banner as first body paragraph (not in title field)."""
    article = page.locator("article").first
    if article.count() and DEFAULT_BANNER_MARKER in article.inner_text():
        print("  banner already present")
        return False

    title_box = page.locator('[contenteditable="true"]').first
    if title_box.count():
        title_box.scroll_into_view_if_needed()
        title_box.click()
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(300)
        page.keyboard.press("Home")
        page.keyboard.type(banner)
        page.keyboard.press("Enter")
        print("  banner inserted in body (after title)")
        return True

    body_selectors = (
        "article p.graf--p",
        "article [data-testid='editorParagraphText']",
    )
    for selector in body_selectors:
        body = page.locator(selector).first
        if not body.count():
            continue
        body.scroll_into_view_if_needed()
        body.click(force=True)
        page.keyboard.press("Home")
        page.keyboard.type(banner)
        page.keyboard.press("Enter")
        print("  banner inserted in body")
        return True
    return False


def verify_post_update(row: dict) -> PostReportRow:
    """Validate blog URL, canonical tag, banner, and title on the public Medium page."""
    medium_title = row.get("medium_title", "")
    blog_url = normalize_blog_url(row["blog_url"])
    medium_link = public_medium_url(row)

    blog_ok, http_status = verify_blog_url(blog_url)
    notes: list[str] = []

    canonical_ok = False
    canonical_found = ""
    banner_ok = False
    title_ok = False

    try:
        html = fetch_page_html(medium_link)
        canonical_found = parse_canonical_url(html) or ""
        canonical_ok = canonical_matches(html, blog_url)
        banner_ok = banner_present_in_html(html)
        title_ok = title_matches(html, medium_title)
        if not canonical_ok:
            notes.append(f"canonical mismatch (found: {canonical_found or 'none'})")
        if not banner_ok:
            notes.append("banner marker missing on public page")
        if not title_ok:
            notes.append("medium title not found on public page")
    except (HTTPError, URLError, TimeoutError) as exc:
        notes.append(f"fetch failed: {exc}")

    if not blog_ok:
        notes.append(f"blog URL HTTP {http_status}")

    report = PostReportRow(
        post_title=medium_title,
        medium_link=medium_link,
        blog_site_link=blog_url,
        status="verified",
        blog_url_ok=blog_ok,
        blog_http_status=http_status,
        canonical_ok=canonical_ok,
        canonical_found=canonical_found,
        banner_ok=banner_ok,
        title_ok=title_ok,
        notes="; ".join(notes),
    )
    report.status = overall_status(report)
    return report


def prepend_banner(
    page: Page,
    banner: str,
    medium_title: str,
    blog_title: str,
    dry_run: bool,
) -> bool:
    page.wait_for_timeout(1500)
    if dry_run:
        print("  [dry-run] fix title, cleanup legacy, insert body banner")
        return True

    changed = False
    if fix_title_field(page, medium_title):
        changed = True
    if cleanup_legacy_paragraphs(page, medium_title, blog_title):
        changed = True
    if insert_body_banner(page, banner):
        changed = True
    return changed


def publish_changes(page: Page, dry_run: bool) -> None:
    if dry_run:
        return
    publish_selectors = [
        'button:has-text("Publish")',
        'button:has-text("Save")',
        'button:has-text("Save and publish")',
        'button[data-action="publish"]',
    ]
    for selector in publish_selectors:
        locator = page.locator(selector).first
        if locator.count() and locator.is_visible():
            locator.click()
            page.wait_for_timeout(1500)
            confirm = page.locator('button:has-text("Publish now")').first
            if confirm.count() and confirm.is_visible():
                confirm.click()
            page.wait_for_timeout(2000)
            return


def update_post(
    page: Page,
    row: dict,
    dry_run: bool,
    *,
    skip_url_check: bool,
    verify_only: bool,
) -> tuple[bool, str | None, PostReportRow | None]:
    medium_id = row["medium_id"]
    blog_url = normalize_blog_url(row["blog_url"])
    row["blog_url"] = blog_url
    medium_title = row.get("medium_title", "")
    blog_title = row.get("blog_title", "")

    if verify_only:
        report = verify_post_update(row)
        print(f"  verify: blog={report.blog_url_ok} canonical={report.canonical_ok} banner={report.banner_ok} title={report.title_ok}")
        return True, None, report

    if not blog_url:
        return False, "missing blog_url", None

    if not skip_url_check and not dry_run:
        ok, status = verify_blog_url(blog_url)
        if not ok:
            return False, f"blog URL not reachable ({status}): {blog_url}", None

    changed = False

    edit_url = f"https://medium.com/p/{medium_id}/edit"
    page.goto(edit_url, wait_until="domcontentloaded", timeout=120_000)
    page.wait_for_timeout(2500)

    if not _ensure_logged_in(page):
        return False, "session expired; run --login", None

    banner = make_banner(medium_title, blog_url)
    if prepend_banner(page, banner, medium_title, blog_title, dry_run):
        changed = True
        if not dry_run:
            publish_changes(page, dry_run)

    if not changed and not dry_run:
        report = verify_post_update(row)
        return True, "already up to date", report

    report = None if dry_run else verify_post_update(row)
    if report:
        print(
            f"  verify: blog={report.blog_url_ok} canonical={report.canonical_ok} "
            f"banner={report.banner_ok} title={report.title_ok} -> {report.status}"
        )
    return True, None, report


def update_posts(
    mapping_path: Path,
    session_path: Path,
    errors_path: Path,
    report_csv: Path,
    report_json: Path,
    *,
    dry_run: bool,
    headed: bool,
    limit: int | None,
    throttle_seconds: float,
    medium_ids: list[str] | None,
    channel: str,
    force: bool,
    skip_url_check: bool,
    verify_only: bool,
) -> int:
    payload = load_mapping(mapping_path)
    rows = payload.get("posts", [])
    if medium_ids:
        wanted = set(medium_ids)
        targets = [r for r in rows if r["medium_id"] in wanted and r.get("blog_url")]
    elif verify_only:
        targets = [r for r in rows if r.get("blog_url")]
    else:
        targets = [
            r
            for r in rows
            if r.get("blog_url")
            and (force or r.get("status") in {"pending", "needs_review"})
        ]
    if limit is not None:
        targets = targets[:limit]

    if not targets:
        print("No posts to update. Use --ids or --force to re-process.")
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not verify_only and not session_path.exists() and not dry_run:
        print(f"Missing session file: {session_path}\nRun: python3 {Path(__file__).name} --login")
        return 1

    errors: list[dict] = []
    reports: list[PostReportRow] = []
    updated = 0
    use_headed = headed or (not dry_run and not verify_only)

    def process_row(page: Page | None, row: dict) -> None:
        nonlocal updated
        title = row.get("medium_title", row["medium_id"])
        print(f"[{len(reports) + 1}/{len(targets)}] {title}")
        try:
            if verify_only and page is None:
                report = verify_post_update(row)
                reports.append(report)
                print(
                    f"  verify: blog={report.blog_url_ok} canonical={report.canonical_ok} "
                    f"banner={report.banner_ok} title={report.title_ok} -> {report.status}"
                )
                return

            ok, err, report = update_post(
                page,
                row,
                dry_run,
                skip_url_check=skip_url_check,
                verify_only=False,
            )
            if report:
                reports.append(report)
            if err == "already up to date":
                print("  skipped (already up to date)")
                row["status"] = "done"
            elif ok:
                print("  updated")
                row["status"] = "done" if (report and report.status == "ok") else "partial"
                row["updated_at"] = datetime.now(timezone.utc).isoformat()
                updated += 1
            else:
                print(f"  failed: {err}")
                errors.append({"medium_id": row["medium_id"], "error": err})
                reports.append(
                    PostReportRow(
                        post_title=title,
                        medium_link=public_medium_url(row),
                        blog_site_link=normalize_blog_url(row["blog_url"]),
                        status="failed",
                        notes=err or "",
                    )
                )
        except Exception as exc:  # noqa: BLE001
            print(f"  error: {exc}")
            errors.append({"medium_id": row["medium_id"], "error": str(exc)})
            reports.append(
                PostReportRow(
                    post_title=title,
                    medium_link=public_medium_url(row),
                    blog_site_link=normalize_blog_url(row.get("blog_url", "")),
                    status="failed",
                    notes=str(exc),
                )
            )

    if verify_only:
        for row in targets:
            process_row(None, row)
    else:
        with sync_playwright() as playwright:
            browser, context = open_automation_context(
                playwright,
                channel=channel,
                headed=use_headed,
                session_path=session_path if session_path.exists() else None,
                profile_dir=DEFAULT_PROFILE_DIR,
            )
            page = context.pages[0] if context.pages else context.new_page()

            for index, row in enumerate(targets, start=1):
                process_row(page, row)
                if session_path.exists() and not dry_run:
                    context.storage_state(path=str(session_path))
                if index < len(targets):
                    time.sleep(throttle_seconds)

            if browser:
                browser.close()
            else:
                context.close()

    if reports:
        write_report(reports, report_csv, report_json)
        print(f"Report: {report_csv}")
        if report_json:
            print(f"Report: {report_json}")

    if not dry_run and not verify_only:
        save_mapping(mapping_path, payload)
    if errors:
        errors_path.write_text(json.dumps(errors, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {len(errors)} errors -> {errors_path}")
    print(f"Updated {updated} / {len(targets)} posts")
    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Update Medium legacy posts via Playwright")
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    parser.add_argument("--session", type=Path, default=DEFAULT_SESSION)
    parser.add_argument("--errors", type=Path, default=DEFAULT_ERRORS)
    parser.add_argument("--archive-cache", type=Path, default=DEFAULT_ARCHIVE_CACHE)
    parser.add_argument(
        "--login-codegen",
        action="store_true",
        help="Save session via Playwright codegen (recommended login)",
    )
    parser.add_argument(
        "--login",
        action="store_true",
        help="Legacy login via Chrome profile (often blocked by Cloudflare)",
    )
    parser.add_argument("--list-stories", action="store_true", help="List all stories from /me/stories")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--headed", action="store_true", help="Show browser window (recommended)")
    parser.add_argument(
        "--channel",
        default=DEFAULT_CHANNEL,
        help="Browser channel: chrome (default, real Google Chrome) or chromium",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--throttle", type=float, default=12.0, help="Seconds between posts")
    parser.add_argument("--ids", nargs="*", help="Only update these Medium post IDs")
    parser.add_argument(
        "--install-browser",
        action="store_true",
        help="Download Playwright Chromium, then exit",
    )
    parser.add_argument("--force", action="store_true", help="Re-process posts already marked done")
    parser.add_argument("--skip-url-check", action="store_true", help="Skip blog URL reachability check")
    parser.add_argument("--verify-only", action="store_true", help="Verify public pages only (no edits)")
    parser.add_argument("--report-csv", type=Path, default=DEFAULT_REPORT_CSV)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    args = parser.parse_args()

    channel = "" if args.channel == "chromium" else args.channel

    if args.install_browser:
        install_chromium_browser()
        return 0

    if args.login_codegen:
        login_via_codegen(args.session, channel=channel)
        return 0

    if args.login:
        login_and_save_session(args.session, DEFAULT_PROFILE_DIR, channel=channel)
        return 0
    if args.list_stories:
        if not args.session.exists():
            print(f"Missing session: {args.session}. Run --login or --login-codegen first.")
            return 1
        count = list_stories(
            args.session,
            args.archive_cache,
            headed=True,
            channel=channel,
        )
        return 0 if count else 1

    return update_posts(
        args.mapping,
        args.session,
        args.errors,
        args.report_csv,
        args.report_json,
        dry_run=args.dry_run,
        headed=args.headed,
        limit=args.limit,
        throttle_seconds=args.throttle,
        medium_ids=args.ids,
        channel=channel,
        force=args.force,
        skip_url_check=args.skip_url_check,
        verify_only=args.verify_only,
    )


if __name__ == "__main__":
    sys.exit(main())
