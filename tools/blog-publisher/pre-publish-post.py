#!/usr/bin/env python3
"""
Features:
- Reads pre-publish `.md` from `tools/blog-publisher/input/` only (filename, no absolute paths)
- Writes directly to `content/posts/{slug}/` (`index.md` + `images/`) — no staging folder
- Interactive prompts: date, slug, category, tags, episodeseries
- Category picker: exactly one from `data/categories.yaml` (via frontmatter-check)
- Tag-based category hint (e.g. 投資/ETF → 投資理財)
- Episode series: pick from registry or add new (`data/episodeseries.json`)
- Unsplash cover: download via API (`UNSPLASH_ACCESS_KEY` in repo `.env`), baseline JPEG normalize, size check
- Front matter: `cover.image` / `cover.alt` / `cover.credit`, `images:` list (always published — never `draft: true`)
- Strips legacy `{{< footer >}}` (footer is layout-driven)
- Validates output with `scripts/check-posts.py --post` before finish
- Optional Hugo dev server on port 1313 after publish (`--no-hugo` to skip)
- Confirms before overwriting an existing post folder
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

import click
import requests
import yaml
from dotenv import load_dotenv
from PIL import Image

warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+")

SLUG_MAX_LENGTH = 75
IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".gif", ".webp"})
DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")
HUGO_DEFAULT_PORT = 1313

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
CHECK_SCRIPT = PROJECT_ROOT / "scripts" / "check-posts.py"
SIZE_CHECK_MODULE = PROJECT_ROOT / "scripts" / "post-validation" / "image-size-check.py"
FRONTMATTER_CHECK = PROJECT_ROOT / "scripts" / "post-validation" / "frontmatter-check.py"
EPISODESERIES_REGISTRY = PROJECT_ROOT / "scripts" / "episodeseries_registry.py"

load_dotenv(PROJECT_ROOT / ".env")
INPUT_DIR = SCRIPT_DIR / "input"
HUGO_CONTENT_DIR = PROJECT_ROOT / "content" / "posts"

FOOTER_LEGACY = re.compile(r"\n?\{\{<\s*footer\s*>\}\}\s*")

INVESTMENT_TAG_HINTS = frozenset({"投資", "ETF", "理財", "FIRE", "退休", "澳洲理財"})


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def allowed_categories() -> list[str]:
    """Single source of truth: data/categories.yaml."""
    fm = _load_module("frontmatter_check", FRONTMATTER_CHECK)
    return sorted(fm.ALLOWED_CATEGORIES)


def load_size_check_module():
    return _load_module("image_size_check", SIZE_CHECK_MODULE)


def load_episodeseries_registry():
    return _load_module("episodeseries_registry", EPISODESERIES_REGISTRY)


def resolve_input_path(input_file: str) -> Path:
    """Resolve input path under tools/blog-publisher/input/ only."""
    candidate = Path(input_file)
    if candidate.is_absolute() or ".." in candidate.parts:
        click.echo("❌ Input must be a filename under tools/blog-publisher/input/ (not an absolute path).")
        sys.exit(1)
    path = INPUT_DIR / candidate.name
    if not path.exists():
        click.echo(f"❌ Input file not found: {path}")
        click.echo(f"   Place your pre-publish markdown at: {INPUT_DIR}/")
        sys.exit(1)
    return path


def split_post(content: str) -> tuple[dict, str]:
    """Parse YAML front matter and body (supports multi-line arrays)."""
    text = content.strip()
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    raw_fm = parts[1]
    try:
        fm = yaml.safe_load(raw_fm) or {}
    except yaml.YAMLError as exc:
        click.echo(f"❌ Invalid YAML front matter: {exc}")
        sys.exit(1)
    if not isinstance(fm, dict):
        click.echo("❌ Front matter must be a YAML mapping.")
        sys.exit(1)
    body = parts[2].lstrip("\n")
    return fm, body


def fm_string_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return []


def fm_scalar(value) -> str:
    if value is None:
        return ""
    return str(value).strip().strip("\"'")


def strip_date_prefix(slug_part: str) -> str:
    return DATE_PREFIX_RE.sub("", slug_part.strip())


def bare_slug_from_draft(fm: dict, file_stem: str) -> str:
    raw = fm_scalar(fm.get("slug"))
    if raw:
        return strip_date_prefix(raw)
    return strip_date_prefix(file_stem)


def compose_final_slug(post_date: str, bare: str) -> str:
    bare = bare.strip().strip("/")
    if not bare:
        bare = "untitled"
    return f"{post_date}-{bare}"[:SLUG_MAX_LENGTH]


def title_from_draft(fm: dict, body: str) -> str:
    title = fm_scalar(fm.get("title"))
    if title:
        return title
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    for line in body.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line[:60]
    return "Untitled Post"


def today_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def strip_legacy_footer_shortcode(content: str) -> str:
    return FOOTER_LEGACY.sub("", content).rstrip()


def normalize_downloaded_jpeg(image_path: Path) -> None:
    size_check = load_size_check_module()
    changed, msg = size_check.normalize_jpeg_baseline(image_path)
    if changed:
        click.echo(f"✅ Normalized JPEG encoding: {msg}")
    else:
        click.echo("✅ JPEG encoding: baseline")


def extract_unsplash_photo_id(url: str) -> str | None:
    match = re.search(r"([a-zA-Z0-9_-]{11})(?:\?|$)", url.strip())
    return match.group(1) if match else None


def clean_url(url: str) -> str:
    return url.strip().split("?")[0].split("#")[0]


COVER_DOWNLOAD_MAX_ATTEMPTS = 2


def get_unsplash_access_key() -> str | None:
    key = os.environ.get("UNSPLASH_ACCESS_KEY", "").strip()
    return key or None


def fetch_unsplash_photo_data(photo_id: str, access_key: str) -> tuple[dict | None, str]:
    url = f"https://api.unsplash.com/photos/{photo_id}"
    headers = {"Authorization": f"Client-ID {access_key}"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 401:
            return None, (
                "Unsplash API key rejected — check UNSPLASH_ACCESS_KEY in repo-root .env"
            )
        if resp.status_code == 404:
            return None, (
                f"Photo not found on Unsplash (id: {photo_id}) — "
                "check the URL or pick another photo"
            )
        if resp.status_code >= 400:
            return None, f"Unsplash API returned HTTP {resp.status_code} for photo {photo_id}"
        resp.raise_for_status()
        return resp.json(), ""
    except requests.RequestException as exc:
        return None, f"Could not reach Unsplash API: {exc}"
    except ValueError as exc:
        return None, f"Unsplash API returned invalid JSON: {exc}"


def download_unsplash_image(
    photo_id: str, photo_url: str, output_path: Path
) -> tuple[bool, dict | None, str]:
    access_key = get_unsplash_access_key()
    if not access_key:
        return False, None, (
            "UNSPLASH_ACCESS_KEY not set — add it to repo-root .env "
            "(get a free key at unsplash.com/developers)"
        )

    click.echo("🔍 Fetching photo info from Unsplash API...")
    data, api_error = fetch_unsplash_photo_data(photo_id, access_key)
    if not data:
        return False, None, api_error

    urls = data.get("urls", {})
    cdn_base = (urls.get("full") or urls.get("regular") or "").split("?")[0]
    if not cdn_base:
        return False, None, "Unsplash API response had no downloadable image URL"

    download_url = f"{cdn_base}?q=85&w=1600&fit=crop&auto=format"
    click.echo(f"📥 Downloading from: {download_url}")

    try:
        img_resp = requests.get(download_url, timeout=60, allow_redirects=True)
        if img_resp.status_code >= 400:
            return False, None, (
                f"Image CDN returned HTTP {img_resp.status_code} — try another photo"
            )
        img_resp.raise_for_status()

        content_type = img_resp.headers.get("Content-Type", "").lower()
        if "image" not in content_type:
            return False, None, (
                f"CDN response is not an image (Content-Type: {content_type or 'unknown'})"
            )

        with open(output_path, "wb") as f:
            f.write(img_resp.content)
        click.echo(f"✅ Downloaded {len(img_resp.content):,} bytes")

        try:
            normalize_downloaded_jpeg(output_path)
        except Exception as exc:
            if output_path.exists():
                output_path.unlink()
            return False, None, f"Could not normalize JPEG: {exc}"

        try:
            with Image.open(output_path) as img:
                fmt = img.format
                img.verify()
        except Exception as exc:
            if output_path.exists():
                output_path.unlink()
            return False, None, f"Downloaded file is not a valid image: {exc}"

        click.echo(f"✅ Image verified ({fmt})")

        user = data.get("user", {})
        username = user.get("username", "photographer")
        name = user.get("name", username)
        links = data.get("links", {})
        page_url = clean_url(links.get("html") or photo_url or f"https://unsplash.com/photos/{photo_id}")

        metadata = {
            "username": username,
            "name": name,
            "profile_url": f"https://unsplash.com/@{username}",
            "photo_url": page_url,
        }
        return True, metadata, ""

    except requests.RequestException as exc:
        if output_path.exists():
            output_path.unlink()
        return False, None, f"Image download failed (network): {exc}"
    except OSError as exc:
        if output_path.exists():
            output_path.unlink()
        return False, None, f"Could not save image to {output_path.name}: {exc}"


def prompt_unsplash_cover_url(*, retry: bool = False, last_error: str = "") -> str | None:
    """Return Unsplash page URL, or None if user explicitly skips/aborts."""
    if not retry:
        click.echo("\n🖼️  Cover image (Unsplash)")
    elif last_error:
        click.echo(f"\n❌ {last_error}")
        click.echo("🔄 Try another Unsplash photo URL.")

    skip_label = "n to abort" if retry else "n to skip"
    prompt_label = (
        f"🔗 Paste another photo URL ({skip_label})"
        if retry
        else f"🔗 Paste photo URL ({skip_label})"
    )

    while True:
        raw = click.prompt(prompt_label, default="").strip()
        if raw.lower() in ("n", "no"):
            if retry:
                click.echo("❌ Aborted — no cover image.")
            else:
                click.echo(
                    "⚠️  Published posts require cover.image — "
                    "check-posts validation will fail without a cover."
                )
            return None
        if not raw:
            click.echo(f"❌ Paste an Unsplash URL, or {skip_label}.")
            continue
        if extract_unsplash_photo_id(raw):
            return raw
        click.echo(
            "❌ Not a valid Unsplash photo URL — "
            "expected: https://unsplash.com/photos/photo-name-XXXXXXXXXXX"
        )


def acquire_unsplash_cover(
    images_dir: Path,
) -> tuple[str | None, dict | None, Path | None]:
    """Download cover with up to COVER_DOWNLOAD_MAX_ATTEMPTS tries. Returns (filename, metadata, path)."""
    last_error = ""
    for attempt in range(1, COVER_DOWNLOAD_MAX_ATTEMPTS + 1):
        unsplash_url = prompt_unsplash_cover_url(
            retry=attempt > 1,
            last_error=last_error,
        )
        if not unsplash_url:
            return None, None, None

        photo_id = extract_unsplash_photo_id(unsplash_url)
        click.echo(f"✅ Photo ID: {photo_id}")
        image_filename = f"{photo_id}-unsplash.jpg"
        image_path = images_dir / image_filename

        click.echo("\n📥 Downloading image...")
        success, metadata, error = download_unsplash_image(photo_id, unsplash_url, image_path)
        if success:
            return image_filename, metadata, image_path

        last_error = error or "Unknown download error"
        if attempt < COVER_DOWNLOAD_MAX_ATTEMPTS:
            click.echo(f"⚠️  Attempt {attempt}/{COVER_DOWNLOAD_MAX_ATTEMPTS} failed.")
            continue

        click.echo(f"❌ {last_error}")
        click.echo(
            f"❌ Cover download failed after {COVER_DOWNLOAD_MAX_ATTEMPTS} attempts. "
            "Check your Unsplash URL and UNSPLASH_ACCESS_KEY in .env."
        )
        sys.exit(1)

    return None, None, None


def infer_episode_series(title: str) -> str:
    title = title.strip()
    bracket = re.match(r"^\[([^\]]+)\]", title)
    if bracket:
        return bracket.group(1)
    if title.startswith("好想要退休"):
        return "好想要退休"
    if title.startswith("零基礎轉職澳洲工程師"):
        return "零基礎轉職澳洲工程師"
    if title.startswith("一個女生的歐洲獨旅"):
        return "一個女生的歐洲獨旅"
    if "倖存者日記" in title:
        return "倖存者日記"
    return ""


def choose_episode_series_from_registry(suggested: str) -> str:
    registry = load_episodeseries_registry()
    known = registry.load_series_list()

    click.echo(f"\n現有系列 (共 {len(known)} 個，來源: data/episodeseries.json):")
    for i, name in enumerate(known, 1):
        hint = " ← 建議" if suggested and name == suggested else ""
        click.echo(f"  {i}. {name}{hint}")
    click.echo("  0. 新增系列")

    default = ""
    if suggested:
        default = str(known.index(suggested) + 1) if suggested in known else suggested

    while True:
        raw = click.prompt("選擇編號或輸入新系列名稱", default=default).strip()
        if not raw:
            click.echo("❌ 請選擇編號或輸入系列名稱。")
            continue
        if raw.isdigit():
            choice = int(raw)
            if choice == 0:
                return prompt_new_episode_series_name(suggested, known)
            if 1 <= choice <= len(known):
                return known[choice - 1]
            click.echo(f"❌ 無效編號，請輸入 0–{len(known)}。")
            continue
        return raw


def prompt_new_episode_series_name(suggested: str, known: list[str]) -> str:
    while True:
        name = click.prompt("請輸入新系列名稱", default=suggested or "").strip()
        if not name:
            click.echo("❌ 系列名稱不可為空，請重新輸入。")
            continue
        if name in known:
            click.echo(f"ℹ️  「{name}」已在列表中，直接使用。")
        return name


def prompt_episode_series(draft_series: str, title: str) -> str | None:
    registry = load_episodeseries_registry()
    draft_series = draft_series.strip()

    if draft_series:
        click.echo(f"📚 草稿系列: {draft_series}")
        if click.confirm("使用草稿的系列設定？", default=True):
            if registry.register_series(draft_series):
                click.echo(f"✅ Added to episodeseries list: {draft_series}")
            return draft_series
        click.echo("重新選擇系列…")

    if not click.confirm("📚 是否為系列文？", default=False):
        click.echo("⏭️  非系列文 — 略過 episodeseries")
        return None

    suggested = infer_episode_series(title)
    name = choose_episode_series_from_registry(suggested)
    if registry.register_series(name):
        click.echo(f"✅ Added new series to data/episodeseries.json: {name}")
    return name


def suggest_category_from_tags(tags: list[str]) -> str | None:
    for tag in tags:
        if tag in INVESTMENT_TAG_HINTS or any(h in tag for h in INVESTMENT_TAG_HINTS):
            return "投資理財"
    return None


def prompt_category(draft_categories: list[str], tags: list[str]) -> list[str]:
    """Always show picker; draft category is default when valid. Exactly one category."""
    cats = allowed_categories()
    draft_cat = draft_categories[0] if len(draft_categories) == 1 else ""
    if len(draft_categories) > 1:
        click.echo(f"⚠️  草稿有多個分類 {draft_categories!r} — check-posts 只允許一個，請重新選擇。")
        draft_cat = ""

    tag_hint = suggest_category_from_tags(tags)
    if tag_hint and tag_hint in cats and not draft_cat:
        click.echo(f"💡 依標籤建議分類: {tag_hint}")

    click.echo("\n📂 選擇分類 (必填，只能選一個):")
    for i, cat in enumerate(cats, 1):
        hints = []
        if draft_cat and cat == draft_cat:
            hints.append("草稿")
        if tag_hint and cat == tag_hint and cat != draft_cat:
            hints.append("建議")
        hint = f" ← {', '.join(hints)}" if hints else ""
        click.echo(f"  {i}. {cat}{hint}")

    default_num = ""
    if draft_cat and draft_cat in cats:
        default_num = str(cats.index(draft_cat) + 1)
    elif tag_hint and tag_hint in cats:
        default_num = str(cats.index(tag_hint) + 1)

    while True:
        raw = click.prompt("選擇編號", default=default_num).strip()
        if not raw.isdigit():
            click.echo("❌ 請輸入編號。")
            continue
        idx = int(raw) - 1
        if 0 <= idx < len(cats):
            chosen = cats[idx]
            break
        click.echo(f"❌ 無效編號，請輸入 1–{len(cats)}。")

    if draft_cat and draft_cat not in cats:
        click.echo(f"⚠️  草稿分類 {draft_cat!r} 不在允許清單中，已改用 {chosen!r}")

    return [chosen]


def prompt_tags(draft_tags: list[str]) -> list[str]:
    default = ", ".join(draft_tags)
    if draft_tags:
        click.echo(f"🏷️  草稿標籤: {', '.join(draft_tags)}")
    while True:
        raw = click.prompt("標籤 (逗號分隔，可留空)", default=default).strip()
        tags = [t.strip() for t in raw.split(",") if t.strip()]
        if tags or not raw:
            return tags
        click.echo("❌ 請輸入至少一個標籤，或保留空白。")


def build_cover_credit(metadata: dict) -> dict[str, str]:
    return {
        "photographer": metadata["name"],
        "photographer_url": metadata["profile_url"],
        "photo_url": metadata["photo_url"],
    }


def list_bundle_image_paths(images_dir: Path) -> list[str]:
    if not images_dir.is_dir():
        return []
    names = sorted(
        f.name for f in images_dir.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    )
    return [f"images/{name}" for name in names]


def warn_cover_image_size(image_path: Path) -> bool:
    size_check = load_size_check_module()
    info = size_check.read_image_info(image_path)
    if info is None:
        click.echo(f"⚠️  Could not read image metadata: {image_path.name}")
        return True
    warnings_list, errors = size_check.check_info(info, "cover")
    for warning in warnings_list:
        click.echo(f"⚠️  {warning}")
    for error in errors:
        click.echo(f"❌ {error}")
    return not errors


def generate_front_matter(
    title: str,
    slug: str,
    post_date: str,
    categories: list[str],
    tags: list[str],
    image_filename: str | None,
    images_list: list[str],
    *,
    alt_text: str | None = None,
    credit: dict | None = None,
    episode_series: str | None = None,
) -> str:
    if image_filename:
        image_path = f"images/{image_filename}"
        if image_path not in images_list:
            images_list = [image_path, *images_list]
    else:
        image_path = ""

    lines = [
        "---",
        f'title: "{title}"',
        f"date: {post_date}",
        f'slug: "{slug}"',
    ]

    if image_filename:
        lines.extend(
            [
                "cover:",
                f'  image: "{image_path}"',
                f'  alt: {json.dumps(alt_text or "", ensure_ascii=False)}',
            ]
        )
        if credit:
            lines.extend(
                [
                    "  credit:",
                    f'    photographer: {json.dumps(credit["photographer"], ensure_ascii=False)}',
                    f'    photographer_url: "{credit["photographer_url"]}"',
                    f'    photo_url: "{credit["photo_url"]}"',
                ]
            )

    block = [
        f"images: {json.dumps(images_list, ensure_ascii=False)}",
        f"categories: {json.dumps(categories, ensure_ascii=False)}",
        f"tags: {json.dumps(tags, ensure_ascii=False)}",
    ]
    if episode_series:
        block.append(f"episodeseries: {json.dumps([episode_series], ensure_ascii=False)}")
    block.append("---")
    lines.extend(block)
    return "\n".join(lines)


def confirm_replace_post_dir(post_dir: Path) -> bool:
    if not post_dir.exists():
        return True
    click.echo(f"\n⚠️  Post folder already exists: {post_dir}")
    return click.confirm("覆寫現有資料夾？（index.md 與 images/ 將被取代）", default=False)


def validate_post(post_dir: Path) -> bool:
    if not CHECK_SCRIPT.is_file():
        click.echo(f"⚠️  Validation script not found: {CHECK_SCRIPT}")
        return True

    slug = post_dir.name
    click.echo("\n🔍 Validating post format...")
    result = subprocess.run(
        [sys.executable, str(CHECK_SCRIPT), "--post", slug],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    output = (result.stdout or "") + (result.stderr or "")
    if output.strip():
        click.echo(output.rstrip())
    if result.returncode != 0:
        click.echo("❌ Post validation failed. Fix errors above.")
        return False
    return True


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def maybe_start_hugo_server() -> None:
    if is_port_in_use(HUGO_DEFAULT_PORT):
        click.echo(f"ℹ️  Hugo already running on http://localhost:{HUGO_DEFAULT_PORT} — skipping start")
        return
    click.echo("\n🚀 Starting Hugo dev server...")
    try:
        os.chdir(PROJECT_ROOT)
        subprocess.Popen(
            ["hugo", "server"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        click.echo(f"✅ Hugo server started on http://localhost:{HUGO_DEFAULT_PORT}")
        time.sleep(1)
    except Exception as exc:
        click.echo(f"⚠️  Could not start Hugo: {exc}")


@click.command()
@click.argument("input_file", required=True)
@click.option("--no-hugo", is_flag=True, help="Do not start Hugo dev server after publish.")
def main(input_file: str, no_hugo: bool) -> None:
    """Publish a Hugo post from pre-publish markdown in tools/blog-publisher/input/.

    INPUT_FILE: Markdown filename (e.g. leveraged-etf-taiwan-vs-australia.md)
    """

    click.echo("\n" + "=" * 60)
    click.echo("🚀 Hugo Blog Post Publisher")
    click.echo("=" * 60)

    input_path = resolve_input_path(input_file)

    try:
        content = input_path.read_text(encoding="utf-8")
    except Exception as exc:
        click.echo(f"❌ Error reading file: {exc}")
        sys.exit(1)

    if not content.strip():
        click.echo("❌ Input file is empty")
        sys.exit(1)

    fm, body = split_post(content)
    title = title_from_draft(fm, body)
    draft_categories = fm_string_list(fm.get("categories"))
    draft_tags = fm_string_list(fm.get("tags"))
    draft_episode_series = fm_string_list(fm.get("episodeseries"))
    draft_episode = draft_episode_series[0] if draft_episode_series else ""

    click.echo(f"\n📝 Title: {title}")

    date_input = click.prompt("📅 Date (YYYY-MM-DD)", default=today_date()).strip()

    bare = bare_slug_from_draft(fm, input_path.stem)
    slug = compose_final_slug(date_input, bare)
    slug_override = click.prompt("📝 Slug (folder name)", default=slug).strip()
    if slug_override:
        slug = slug_override[:SLUG_MAX_LENGTH]
    click.echo(f"📁 Output: content/posts/{slug}/")

    selected_categories = prompt_category(draft_categories, draft_tags)
    tags = prompt_tags(draft_tags)
    episode_series = prompt_episode_series(draft_episode, title)

    post_dir = HUGO_CONTENT_DIR / slug
    if not confirm_replace_post_dir(post_dir):
        click.echo("❌ Aborted — existing post folder kept.")
        sys.exit(1)

    if post_dir.exists():
        shutil.rmtree(post_dir)
    images_dir = post_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    click.echo(f"✅ Created: {post_dir}")

    image_filename = None
    alt_text = None
    cover_credit = None

    image_filename, metadata, image_path = acquire_unsplash_cover(images_dir)

    if image_filename and metadata and image_path:
        click.echo(f"✅ Image saved: {image_filename}")
        click.echo(f"✅ Photographer: {metadata['name']} (@{metadata['username']})")

        cover_credit = build_cover_credit(metadata)
        click.echo("\n📋 Cover credit (rendered by cover.html):")
        click.echo(f"   Photographer: {cover_credit['photographer']}")
        click.echo(f"   Profile: {cover_credit['photographer_url']}")
        click.echo(f"   Photo: {cover_credit['photo_url']}")

        while True:
            alt_text = click.prompt("🖼️  Alt text for cover image (required)", default="").strip()
            if alt_text:
                break
            click.echo("❌ Alt text is required when adding a cover image.")

        if not warn_cover_image_size(image_path):
            sys.exit(1)

    images_list = list_bundle_image_paths(images_dir)
    clean_body = strip_legacy_footer_shortcode(body)
    front_matter = generate_front_matter(
        title,
        slug,
        date_input,
        selected_categories,
        tags,
        image_filename,
        images_list,
        alt_text=alt_text,
        credit=cover_credit,
        episode_series=episode_series,
    )

    index_path = post_dir / "index.md"
    index_path.write_text(f"{front_matter}\n\n{clean_body}".rstrip() + "\n", encoding="utf-8")
    click.echo(f"✅ Post written: {index_path}")

    if not validate_post(post_dir):
        sys.exit(1)

    if not no_hugo:
        maybe_start_hugo_server()

    click.echo("\n" + "=" * 60)
    click.echo("🎉 Blog post generation completed!")
    click.echo("=" * 60)


if __name__ == "__main__":
    main()
