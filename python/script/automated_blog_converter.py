#!/usr/bin/env python3
"""
Automates the creation of Hugo blog posts from markdown files with Unsplash images.
Enhanced version with direct Unsplash URL input and proper image handling.
"""

import re
import os
import click
import requests
import shutil
import warnings
import subprocess
import time
from datetime import datetime
from pathlib import Path
from PIL import Image
import json
from dotenv import load_dotenv


# Suppress urllib3 warning on macOS
warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL 1.1.1+')

# Configuration
CATEGORIES = ["海外職場", "投資理財", "旅行紀錄", "澳洲生活"]
SLUG_MAX_LENGTH = 75

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Load .env from the project root
load_dotenv(PROJECT_ROOT / ".env")
INPUT_DIR = SCRIPT_DIR.parent / "input"
OUTPUT_DIR = SCRIPT_DIR.parent / "output"
HUGO_CONTENT_DIR = PROJECT_ROOT / "content" / "posts"


def extract_unsplash_photo_id(url):
    """Extract Unsplash photo ID from URL.
    
    Handles:
    - https://unsplash.com/photos/sydney-harbour-bridge-australia-ZsH1wHv2iTU
    - https://unsplash.com/photos/ZsH1wHv2iTU
    """
    match = re.search(r'([a-zA-Z0-9_-]{11})(?:\?|$)', url.strip())
    return match.group(1) if match else None


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

    Returns (success: bool, photographer_info: dict | None).
    """
    access_key = get_unsplash_access_key()
    if not access_key:
        click.echo("❌ No API key provided.")
        return False, None

    click.echo("🔍 Fetching photo info from Unsplash API...")
    data = fetch_unsplash_photo_data(photo_id, access_key)
    if not data:
        return False, None

    # Prefer the 'full' URL (up to original resolution), fall back to 'regular'
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

        # Verify integrity
        try:
            with Image.open(output_path) as img:
                fmt = img.format
                img.verify()
            click.echo(f"✅ Image verified ({fmt})")
        except Exception as e:
            click.echo(f"❌ Image file is corrupt: {e}")
            os.remove(output_path)
            return False, None

        # Extract photographer info from API response
        user = data.get("user", {})
        username = user.get("username", "photographer")
        name = user.get("name", username)
        photographer_info = {
            "username": username,
            "name": name,
            "profile_url": f"https://unsplash.com/@{username}",
        }
        return True, photographer_info

    except Exception as e:
        click.echo(f"❌ Download error: {e}")
        return False, None


def extract_title_from_content(content):
    """Extract title from content."""
    lines = content.strip().split('\n')
    
    # Try front matter first
    in_front_matter = False
    for line in lines:
        line = line.strip()
        if line == '---':
            in_front_matter = not in_front_matter
            continue
        if in_front_matter and line.startswith('title:'):
            title = line[6:].strip().strip('"\'')
            return title
    
    # Try headings
    for line in lines:
        line = line.strip()
        if line.startswith('# '):
            return line[2:].strip()
    
    # Use first non-empty line
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and line != '---':
            return line[:60]
    
    return "Untitled Post"


def extract_front_matter(content):
    """Extract categories and tags from front matter."""
    lines = content.strip().split('\n')
    categories = []
    tags = []
    
    in_front_matter = False
    for line in lines:
        if line.strip() == '---':
            in_front_matter = not in_front_matter
            continue
        
        if in_front_matter:
            if line.startswith('categories:'):
                cats_str = line[11:].strip().strip('[]')
                categories = [c.strip().strip('"\'') for c in cats_str.split(',') if c.strip()]
            elif line.startswith('tags:'):
                tags_str = line[5:].strip().strip('[]')
                tags = [t.strip().strip('"\'') for t in tags_str.split(',') if t.strip()]
    
    return categories, tags


def remove_front_matter(content):
    """Remove existing front matter from content."""
    lines = content.strip().split('\n')
    in_front_matter = False
    start_idx = 0
    
    for i, line in enumerate(lines):
        if line.strip() == '---':
            if not in_front_matter:
                in_front_matter = True
            else:
                start_idx = i + 1
                break
    
    return '\n'.join(lines[start_idx:]).strip()


def generate_front_matter(title, slug, categories, tags, image_filename):
    """Generate Hugo front matter."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    front_matter = f"""---
title: "{title}"
date: {today}
slug: "{slug}"
image: "{f'images/{image_filename}' if image_filename else ''}"
images: {json.dumps([f'images/{image_filename}'] if image_filename else [], ensure_ascii=False)}
categories: {json.dumps(categories, ensure_ascii=False)}
tags: {json.dumps(tags, ensure_ascii=False)}
---"""
    
    return front_matter


def generate_image_attribution(photographer_name, photographer_url, photo_url, image_filename):
    """Generate image attribution block in the desired format."""
    return f"""![landing](/images/{image_filename})

Photo by <a href="{photographer_url}?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">{photographer_name}</a> on <a href="{photo_url}?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>
"""


def find_existing_images(images_dir):
    """Find existing images in the images folder."""
    if not images_dir.exists():
        return []
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    images = [
        f for f in images_dir.iterdir() 
        if f.is_file() and f.suffix.lower() in image_extensions
    ]
    return sorted(images)


@click.command()
@click.argument('input_file', required=True)
@click.option('--auto-copy', '-c', is_flag=True, help='Automatically copy to Hugo content directory', default=True)
@click.option('--no-hugo', is_flag=True, help='Do not start Hugo dev server', default=False)
def main(input_file, auto_copy, no_hugo):
    """Hugo Blog Post Generator - Simplified Unsplash URL Version.
    
    INPUT_FILE: Name of the markdown file to process (e.g., sydney-moca.md)
    """
    
    click.echo("\n" + "="*60)
    click.echo("🚀 Hugo Blog Post Generator")
    click.echo("="*60)
    
    # Check input file
    input_path = INPUT_DIR / input_file
    if not input_path.exists():
        click.echo(f"❌ Input file not found: {input_path}")
        return
    
    # Read content
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        click.echo(f"❌ Error reading file: {e}")
        return
    
    if not content.strip():
        click.echo("❌ Input file is empty")
        return
    
    # Extract metadata
    extracted_title = extract_title_from_content(content)
    existing_categories, existing_tags = extract_front_matter(content)
    
    click.echo(f"\n📝 Extracted title: {extracted_title}")
    
    # Get date
    today = datetime.now().strftime("%Y-%m-%d")
    date_input = click.prompt("📅 Date (YYYY-MM-DD)", default=today).strip()
    
    # Generate slug
    file_slug = Path(input_file).stem
    slug = f"{date_input}-{file_slug}"[:SLUG_MAX_LENGTH]
    click.echo(f"📝 Generated slug: {slug}")
    
    # Categories
    if existing_categories:
        click.echo(f"✅ Found categories: {', '.join(existing_categories)}")
        selected_categories = existing_categories
    else:
        click.echo("\n📂 Available categories:")
        for i, cat in enumerate(CATEGORIES, 1):
            click.echo(f"  {i}. {cat}")
        
        category_input = click.prompt("Select category number(s) (comma-separated)", default="1").strip()
        try:
            indices = [int(x.strip()) - 1 for x in category_input.split(',')]
            selected_categories = [CATEGORIES[i] for i in indices if 0 <= i < len(CATEGORIES)]
        except (ValueError, IndexError):
            selected_categories = [CATEGORIES[0]]
    
    # Tags
    if existing_tags:
        click.echo(f"✅ Found tags: {', '.join(existing_tags)}")
        tags = existing_tags
    else:
        tags_input = click.prompt("🏷️  Enter tags (comma-separated, optional)", default="").strip()
        tags = [t.strip() for t in tags_input.split(',') if t.strip()] if tags_input else []
    
    # Create output structure
    click.echo(f"\n📁 Creating output structure:")
    post_dir = OUTPUT_DIR / slug
    post_dir.mkdir(parents=True, exist_ok=True)
    images_dir = post_dir / "images"
    images_dir.mkdir(exist_ok=True)
    click.echo(f"✅ Created: {post_dir}")
    
    # Image handling
    image_filename = None
    photographer_info = None
    image_attribution = ""
    
    click.echo("\n🖼️  Image handling:")
    add_image = click.prompt("Add a landing image from Unsplash? (y/n)", default="y").lower() == 'y'
    
    if add_image:
        unsplash_url = click.prompt("🔗 Paste Unsplash photo URL").strip()
        
        photo_id = extract_unsplash_photo_id(unsplash_url)
        if not photo_id:
            click.echo("❌ Invalid Unsplash URL format. Expected: https://unsplash.com/photos/XXXXX...")
            add_image = False
        else:
            click.echo(f"✅ Photo ID: {photo_id}")
            
            # Download image (also extracts photographer info from the same page fetch)
            image_filename = f"{photo_id}-unsplash.jpg"
            image_path = images_dir / image_filename

            click.echo(f"\n📥 Downloading image...")
            success, photographer_info = download_unsplash_image(photo_id, unsplash_url, image_path)
            if success:
                click.echo(f"✅ Image saved: {image_filename}")
                click.echo(f"✅ Photographer: {photographer_info['name']} (@{photographer_info['username']})")

                # Generate attribution
                image_attribution = generate_image_attribution(
                    photographer_info['name'],
                    photographer_info['profile_url'],
                    unsplash_url,
                    image_filename
                )
            else:
                click.echo("❌ Failed to download image")
                image_filename = None
    
    # Process content
    clean_content = remove_front_matter(content)
    front_matter = generate_front_matter(extracted_title, slug, selected_categories, tags, image_filename)
    
    # Create final post with image attribution at top
    if image_attribution:
        final_content = f"{front_matter}\n\n{image_attribution}\n{clean_content}"
    else:
        final_content = f"{front_matter}\n\n{clean_content}"
    
    # Add footer if not present
    if not final_content.strip().endswith("{{< footer >}}"):
        final_content += "\n\n{{< footer >}}"
    
    # Save post
    index_path = post_dir / "index.md"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    click.echo(f"✅ Post created: {index_path}")
    
    # Generate image links for other images
    existing_images = find_existing_images(images_dir)
    if existing_images:
        click.echo(f"\n🖼️  Found {len(existing_images)} other image(s) in folder:")
        for img in existing_images:
            click.echo(f"   - {img.name}")
        
        inject_images = click.prompt("Generate markdown links for these images? (y/n)", default="y").lower() == 'y'
        if inject_images:
            click.echo("\n📝 Image links (copy/paste into your post):")
            for img in existing_images:
                alt_text = click.prompt(f"Alt text for {img.name}", default=img.stem)
                link = f"![{alt_text}](images/{img.name})"
                click.echo(f"  {link}")
    
    # Copy to Hugo
    if auto_copy:
        hugo_post_dir = HUGO_CONTENT_DIR / slug
        try:
            if hugo_post_dir.exists():
                shutil.rmtree(hugo_post_dir)
            shutil.copytree(post_dir, hugo_post_dir)
            click.echo(f"✅ Copied to Hugo: {hugo_post_dir}")
        except Exception as e:
            click.echo(f"❌ Error copying: {e}")
            return
    
    # Start Hugo server
    if not no_hugo and auto_copy:
        click.echo("\n🚀 Starting Hugo dev server...")
        try:
            os.chdir(PROJECT_ROOT)
            subprocess.Popen(['hugo', 'server', '-D'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            click.echo("✅ Hugo server started on http://localhost:1313")
            time.sleep(1)
        except Exception as e:
            click.echo(f"⚠️  Could not start Hugo: {e}")
    
    click.echo("\n" + "="*60)
    click.echo("🎉 Blog post generation completed!")
    click.echo("="*60)


if __name__ == '__main__':
    main()