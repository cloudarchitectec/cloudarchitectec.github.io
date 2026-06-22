#!/usr/bin/env python3
"""
Automates the creation of Hugo blog posts from markdown files with Unsplash images.
Emits cover.image / cover.alt / cover.credit front matter (no duplicate body hero).
Post footer (subscribe + coffee) is layout-driven — never appends {{< footer >}}.
Cover JPEGs are normalized to baseline encoding after Unsplash download.
Post rules enforced by scripts/post-validation/ — run scripts/check-posts.py --help.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

import click
import requests
from dotenv import load_dotenv
from PIL import Image

# Suppress urllib3 warning on macOS
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+")

# Configuration
CATEGORIES = ["海外職場", "投資理財", "旅行紀錄", "澳洲生活"]
SLUG_MAX_LENGTH = 75
IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".gif", ".webp"})

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
CHECK_SCRIPT = PROJECT_ROOT / "scripts" / "check-posts.py"
SIZE_CHECK_MODULE = PROJECT_ROOT / "scripts" / "post-validation" / "image-size-check.py"
EPISODESERIES_REGISTRY = PROJECT_ROOT / "scripts" / "episodeseries_registry.py"

load_dotenv(PROJECT_ROOT / ".env")
INPUT_DIR = SCRIPT_DIR / "input"
OUTPUT_DIR = SCRIPT_DIR / "output"
HUGO_CONTENT_DIR = PROJECT_ROOT / "content" / "posts"


def load_size_check_module():
    """Load shared image-size-check helpers (baseline JPEG normalization)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("image_size_check", SIZE_CHECK_MODULE)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {SIZE_CHECK_MODULE}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def normalize_downloaded_jpeg(image_path: Path) -> None:
    """Unsplash CDN may return progressive JPEG; re-save as baseline for repo consistency."""
    size_check = load_size_check_module()
    changed, msg = size_check.normalize_jpeg_baseline(image_path)
    if changed:
        click.echo(f"✅ Normalized JPEG encoding: {msg}")
    else:
        click.echo("✅ JPEG encoding: baseline")


def extract_unsplash_photo_id(url):
    """Extract Unsplash photo ID from URL."""
    match = re.search(r"([a-zA-Z0-9_-]{11})(?:\?|$)", url.strip())
    return match.group(1) if match else None


def clean_url(url: str) -> str:
    return url.strip().split("?")[0].split("#")[0]


def get_unsplash_access_key():
    """Return UNSPLASH_ACCESS_KEY from .env, or None if not set."""
    key = os.environ.get("UNSPLASH_ACCESS_KEY", "").strip()
    if not key:
        click.echo("❌ UNSPLASH_ACCESS_KEY not found. Add it to your .env file.")
    return key or None


def fetch_unsplash_photo_data(photo_id, access_key):
    """Call the Unsplash API and return the full photo JSON dict, or None on error."""
    url = f"https://api.unsplash.com/photos/{photo_id}"
    headers = {"Authorization": f"Client-ID {access_key}"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 401:
            click.echo("❌ Invalid Unsplash API key. Check UNSPLASH_ACCESS_KEY in your .env file.")
            return None
        if resp.status_code == 404:
            click.echo(f"❌ Photo '{photo_id}' not found via API.")
            return None
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        click.echo(f"❌ Unsplash API error: {e}")
        return None


def download_unsplash_image(photo_id, photo_url, output_path):
    """Download an Unsplash image via the official API.

    Returns (success: bool, metadata: dict | None).
    metadata keys: username, name, profile_url, photo_url
    """
    access_key = get_unsplash_access_key()
    if not access_key:
        click.echo("❌ No API key provided.")
        return False, None

    click.echo("🔍 Fetching photo info from Unsplash API...")
    data = fetch_unsplash_photo_data(photo_id, access_key)
    if not data:
        return False, None

    urls = data.get("urls", {})
    cdn_base = (urls.get("full") or urls.get("regular") or "").split("?")[0]
    if not cdn_base:
        click.echo("❌ Could not find image URL in API response.")
        return False, None

    download_url = f"{cdn_base}?q=85&w=1600&fit=crop&auto=format"
    click.echo(f"📥 Downloading from: {download_url}")

    try:
        img_resp = requests.get(download_url, timeout=60, allow_redirects=True)
        img_resp.raise_for_status()

        content_type = img_resp.headers.get("Content-Type", "").lower()
        if "image" not in content_type:
            click.echo(f"❌ Unexpected content type: {content_type}")
            return False, None

        with open(output_path, "wb") as f:
            f.write(img_resp.content)
        click.echo(f"✅ Downloaded {len(img_resp.content):,} bytes")

        normalize_downloaded_jpeg(output_path)

        try:
            with Image.open(output_path) as img:
                fmt = img.format
                img.verify()
            click.echo(f"✅ Image verified ({fmt})")
        except Exception as e:
            click.echo(f"❌ Image file is corrupt: {e}")
            os.remove(output_path)
            return False, None

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
        return True, metadata

    except Exception as e:
        click.echo(f"❌ Download error: {e}")
        return False, None


def extract_title_from_content(content):
    """Extract title from content."""
    lines = content.strip().split("\n")

    in_front_matter = False
    for line in lines:
        line = line.strip()
        if line == "---":
            in_front_matter = not in_front_matter
            continue
        if in_front_matter and line.startswith("title:"):
            return line[6:].strip().strip("\"'")

    for line in lines:
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()

    for line in lines:
        line = line.strip()
        if line and not line.startswith("#") and line != "---":
            return line[:60]

    return "Untitled Post"



def load_episodeseries_registry():
    """Load scripts/episodeseries_registry.py helpers."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("episodeseries_registry", EPISODESERIES_REGISTRY)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {EPISODESERIES_REGISTRY}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def infer_episode_series(title: str) -> str:
    """Suggest episode_series from title conventions."""
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
    """Show numbered registry list; pick existing or enter a new series name."""
    registry = load_episodeseries_registry()
    known = registry.load_series_list()

    click.echo(f"\n現有系列 (共 {len(known)} 個，來源: data/episodeseries.json):")
    for i, name in enumerate(known, 1):
        hint = " ← 建議" if suggested and name == suggested else ""
        click.echo(f"  {i}. {name}{hint}")
    click.echo("  0. 新增系列")

    default = ""
    if suggested:
        if suggested in known:
            default = str(known.index(suggested) + 1)
        else:
            default = suggested

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
    """Prompt until a non-empty new series name is provided."""
    while True:
        name = click.prompt(
            "請輸入新系列名稱",
            default=suggested or "",
        ).strip()
        if not name:
            click.echo("❌ 系列名稱不可為空，請重新輸入。")
            continue
        if name in known:
            click.echo(f"ℹ️  「{name}」已在列表中，直接使用。")
        return name


def prompt_episode_series(existing: str, title: str) -> str | None:
    """Resolve episode_series for output front matter.

    Uses existing front matter when present; otherwise asks whether the post
    belongs to a series before prompting from data/episodeseries.json.
    """
    registry = load_episodeseries_registry()

    if existing.strip():
        name = existing.strip()
        click.echo(f"✅ Found episodeseries: {name}")
        if registry.register_series(name):
            click.echo(f"✅ Added to episodeseries list: {name}")
        return name

    is_series = click.confirm("📚 是否為系列文？", default=False)
    if not is_series:
        click.echo("⏭️  非系列文 — 略過 episodeseries")
        return None

    suggested = infer_episode_series(title)
    name = choose_episode_series_from_registry(suggested)
    if registry.register_series(name):
        click.echo(f"✅ Added new series to data/episodeseries.json: {name}")
    return name


def extract_front_matter(content):
    """Extract categories and tags from front matter."""
    lines = content.strip().split("\n")
    categories = []
    tags = []
    episode_series = ""

    in_front_matter = False
    for line in lines:
        if line.strip() == "---":
            in_front_matter = not in_front_matter
            continue

        if in_front_matter:
            if line.startswith("categories:"):
                cats_str = line[11:].strip().strip("[]")
                categories = [c.strip().strip("\"'") for c in cats_str.split(",") if c.strip()]
            elif line.startswith("tags:"):
                tags_str = line[5:].strip().strip("[]")
                tags = [t.strip().strip("\"'") for t in tags_str.split(",") if t.strip()]
            elif line.startswith("episodeseries:"):
                inner = line.split(":", 1)[1].strip().strip("[]")
                parsed = [v.strip().strip("\"'") for v in inner.split(",") if v.strip()]
                episode_series = parsed[0] if parsed else ""

    return categories, tags, episode_series


def remove_front_matter(content):
    """Remove existing front matter from content."""
    lines = content.strip().split("\n")
    in_front_matter = False
    start_idx = 0

    for i, line in enumerate(lines):
        if line.strip() == "---":
            if not in_front_matter:
                in_front_matter = True
            else:
                start_idx = i + 1
                break

    return "\n".join(lines[start_idx:]).strip()


FOOTER_LEGACY = re.compile(r"\n?\{\{<\s*footer\s*>\}\}\s*")


def strip_legacy_footer_shortcode(content: str) -> str:
    """Remove deprecated {{< footer >}} — post footer is layout-driven (post-footer.html)."""
    return FOOTER_LEGACY.sub("", content).rstrip()


def build_cover_credit(metadata: dict) -> dict[str, str]:
    return {
        "photographer": metadata["name"],
        "photographer_url": metadata["profile_url"],
        "photo_url": metadata["photo_url"],
    }


def list_bundle_image_paths(images_dir: Path) -> list[str]:
    """Return sorted images/… paths for all files in the post bundle."""
    if not images_dir.is_dir():
        return []
    names = sorted(
        f.name
        for f in images_dir.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    )
    return [f"images/{name}" for name in names]


def warn_cover_image_size(image_path: Path) -> bool:
    """Print size-check warnings/errors for a downloaded cover. Returns False on hard errors."""
    size_check = load_size_check_module()
    info = size_check.read_image_info(image_path)
    if info is None:
        click.echo(f"⚠️  Could not read image metadata: {image_path.name}")
        return True
    warnings, errors = size_check.check_info(info, "cover")
    for warning in warnings:
        click.echo(f"⚠️  {warning}")
    for error in errors:
        click.echo(f"❌ {error}")
    return not errors


def generate_front_matter(
    title,
    slug,
    date,
    categories,
    tags,
    image_filename,
    images_list,
    alt_text=None,
    credit=None,
    episode_series=None,
):
    """Generate Hugo front matter with cover block when a hero image is set."""
    image_path = f"images/{image_filename}" if image_filename else ""
    if image_filename and image_path not in images_list:
        images_list = [image_path, *images_list]

    lines = [
        "---",
        f'title: "{title}"',
        f"date: {date}",
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


def find_existing_images(images_dir):
    """Find existing images in the images folder."""
    if not images_dir.exists():
        return []

    return sorted(
        f for f in images_dir.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    )


def validate_post(post_dir: Path) -> bool:
    """Run check-posts.py on a single post. Returns True if all checks pass."""
    if not CHECK_SCRIPT.is_file():
        click.echo(f"⚠️  Validation script not found: {CHECK_SCRIPT}")
        return True

    click.echo("\n🔍 Validating post format...")
    result = subprocess.run(
        [sys.executable, str(CHECK_SCRIPT), "--post", str(post_dir)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    output = (result.stdout or "") + (result.stderr or "")
    if output.strip():
        click.echo(output.rstrip())
    if result.returncode != 0:
        click.echo("❌ Post validation failed. Fix errors above before copying to Hugo.")
        return False
    return True


@click.command()
@click.argument("input_file", required=True)
@click.option(
    "--auto-copy",
    "-c",
    is_flag=True,
    help="Automatically copy to Hugo content directory",
    default=True,
)
@click.option("--no-hugo", is_flag=True, help="Do not start Hugo dev server", default=False)
def main(input_file, auto_copy, no_hugo):
    """Hugo Blog Post Generator — emits cover.image / cover.alt / cover.credit.

    INPUT_FILE: Name of the markdown file to process (e.g., sydney-moca.md)
    """

    click.echo("\n" + "=" * 60)
    click.echo("🚀 Hugo Blog Post Generator")
    click.echo("=" * 60)

    input_path = INPUT_DIR / input_file
    if not input_path.exists():
        click.echo(f"❌ Input file not found: {input_path}")
        sys.exit(1)

    try:
        content = input_path.read_text(encoding="utf-8")
    except Exception as e:
        click.echo(f"❌ Error reading file: {e}")
        sys.exit(1)

    if not content.strip():
        click.echo("❌ Input file is empty")
        sys.exit(1)

    extracted_title = extract_title_from_content(content)
    existing_categories, existing_tags, existing_episode_series = extract_front_matter(content)

    click.echo(f"\n📝 Extracted title: {extracted_title}")

    today = datetime.now().strftime("%Y-%m-%d")
    date_input = click.prompt("📅 Date (YYYY-MM-DD)", default=today).strip()

    file_slug = Path(input_file).stem
    slug = f"{date_input}-{file_slug}"[:SLUG_MAX_LENGTH]
    click.echo(f"📝 Generated slug: {slug}")

    if existing_categories:
        click.echo(f"✅ Found categories: {', '.join(existing_categories)}")
        selected_categories = existing_categories
    else:
        click.echo("\n📂 Available categories:")
        for i, cat in enumerate(CATEGORIES, 1):
            click.echo(f"  {i}. {cat}")

        category_input = click.prompt(
            "Select category number(s) (comma-separated)", default="1"
        ).strip()
        try:
            indices = [int(x.strip()) - 1 for x in category_input.split(",")]
            selected_categories = [CATEGORIES[i] for i in indices if 0 <= i < len(CATEGORIES)]
        except (ValueError, IndexError):
            selected_categories = [CATEGORIES[0]]

    if existing_tags:
        click.echo(f"✅ Found tags: {', '.join(existing_tags)}")
        tags = existing_tags
    else:
        tags_input = click.prompt("🏷️  Enter tags (comma-separated, optional)", default="").strip()
        tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []

    episode_series = prompt_episode_series(existing_episode_series, extracted_title)

    click.echo("\n📁 Creating output structure:")
    post_dir = OUTPUT_DIR / slug
    post_dir.mkdir(parents=True, exist_ok=True)
    images_dir = post_dir / "images"
    images_dir.mkdir(exist_ok=True)
    click.echo(f"✅ Created: {post_dir}")

    image_filename = None
    alt_text = None
    cover_credit = None

    click.echo("\n🖼️  Image handling:")
    add_image = click.prompt("Add a cover image from Unsplash? (y/n)", default="y").lower() == "y"

    if not add_image:
        click.echo(
            "⚠️  Published posts require cover.image — use draft: true for bootcamp drafts, "
            "or add a cover before running check-posts / publishing."
        )

    if add_image:
        unsplash_url = click.prompt("🔗 Paste Unsplash photo URL").strip()

        photo_id = extract_unsplash_photo_id(unsplash_url)
        if not photo_id:
            click.echo("❌ Invalid Unsplash URL format. Expected: https://unsplash.com/photos/XXXXX...")
            sys.exit(1)

        click.echo(f"✅ Photo ID: {photo_id}")

        image_filename = f"{photo_id}-unsplash.jpg"
        image_path = images_dir / image_filename

        click.echo("\n📥 Downloading image...")
        success, metadata = download_unsplash_image(photo_id, unsplash_url, image_path)
        if not success:
            click.echo("❌ Failed to download image")
            sys.exit(1)

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
    clean_content = strip_legacy_footer_shortcode(remove_front_matter(content))
    front_matter = generate_front_matter(
        extracted_title,
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

    final_content = f"{front_matter}\n\n{clean_content}".rstrip() + "\n"

    index_path = post_dir / "index.md"
    index_path.write_text(final_content, encoding="utf-8")
    click.echo(f"✅ Post created: {index_path}")

    existing_images = find_existing_images(images_dir)
    if existing_images:
        click.echo(f"\n🖼️  Found {len(existing_images)} image(s) in folder:")
        for img in existing_images:
            click.echo(f"   - {img.name}")

        inject_images = (
            click.prompt("Generate markdown links for these images? (y/n)", default="y").lower()
            == "y"
        )
        if inject_images:
            click.echo("\n📝 Image links (copy/paste into your post):")
            for img in existing_images:
                img_alt = click.prompt(f"Alt text for {img.name}", default=img.stem)
                click.echo(f"  ![{img_alt}](images/{img.name})")

    if not validate_post(post_dir):
        sys.exit(1)

    if auto_copy:
        hugo_post_dir = HUGO_CONTENT_DIR / slug
        try:
            if hugo_post_dir.exists():
                shutil.rmtree(hugo_post_dir)
            shutil.copytree(post_dir, hugo_post_dir)
            click.echo(f"✅ Copied to Hugo: {hugo_post_dir}")
        except Exception as e:
            click.echo(f"❌ Error copying: {e}")
            sys.exit(1)

    if not no_hugo and auto_copy:
        click.echo("\n🚀 Starting Hugo dev server...")
        try:
            os.chdir(PROJECT_ROOT)
            subprocess.Popen(
                ["hugo", "server"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            click.echo("✅ Hugo server started on http://localhost:1313")
            time.sleep(1)
        except Exception as e:
            click.echo(f"⚠️  Could not start Hugo: {e}")

    click.echo("\n" + "=" * 60)
    click.echo("🎉 Blog post generation completed!")
    click.echo("=" * 60)


if __name__ == "__main__":
    main()
