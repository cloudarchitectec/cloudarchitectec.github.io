#!/usr/bin/env python3
"""
Automates the creation of Hugo blog posts from markdown files with Unsplash images.
"""

import re
import click
import requests
import shutil
import warnings
from datetime import datetime
from pathlib import Path
from slugify import slugify
from PIL import Image
import json

# Suppress urllib3 warning on macOS
warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL 1.1.1+')

# Configuration
CATEGORIES = ["投資理財", "旅行紀錄", "海外職場", "澳洲生活"]
SLUG_MAX_LENGTH = 75

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
INPUT_DIR = SCRIPT_DIR.parent / "input"
OUTPUT_DIR = SCRIPT_DIR.parent / "output"
HUGO_CONTENT_DIR = PROJECT_ROOT / "content" / "posts"


def get_unsplash_image_from_url(photo_url):
    """Extract image info from Unsplash photo URL and get download link."""
    
    # Extract photo ID from URL
    photo_id_match = re.search(r'/photos/.*?([a-zA-Z0-9_-]{11})/?(?:\?|$)', photo_url)
    if not photo_id_match:
        click.echo(f"❌ Could not extract photo ID from URL: {photo_url}")
        return None
    
    photo_id = photo_id_match.group(1)
    click.echo(f"📷 Extracted photo ID: {photo_id}")
    
    # Unsplash direct download URL (no API key needed)
    download_url = f"https://unsplash.com/photos/{photo_id}/download"
    
    try:
        # Get the actual download URL from redirect
        response = requests.head(download_url, timeout=10, allow_redirects=True)
        response.raise_for_status()
        actual_download_url = response.url if response.history else download_url
        
        # Try to get photographer and alt text from the page
        click.echo("🔍 Extracting photographer info...")
        page_response = requests.get(photo_url, timeout=10)
        page_content = page_response.text
        
        # Extract photographer username and name
        username_match = re.search(r'"username":"([^"]*)"', page_content)
        name_match = re.search(r'"name":"([^"]*)"', page_content)
        
        # Extract alt description
        alt_match = re.search(r'"alt_description":"([^"]*)"', page_content)
        description_match = re.search(r'"description":"([^"]*)"', page_content)
        
        # Use extracted info or fallbacks
        username = username_match.group(1) if username_match else "photographer"
        photographer_name = name_match.group(1) if name_match else username
        
        # Create simple alt text from photo description
        if alt_match and alt_match.group(1):
            full_alt = alt_match.group(1)
            # Extract 1-2 key words from alt text
            words = re.findall(r'\b[a-zA-Z]{3,}\b', full_alt.lower())
            alt_text = " ".join(words[:2]) if words else "image"
        elif description_match and description_match.group(1):
            full_desc = description_match.group(1)
            words = re.findall(r'\b[a-zA-Z]{3,}\b', full_desc.lower())
            alt_text = " ".join(words[:2]) if words else "image"
        else:
            alt_text = "image"
        
        image_info = {
            "download_url": actual_download_url,
            "alt_description": alt_text,
            "photographer": photographer_name,
            "photographer_url": f"https://unsplash.com/@{username}",
            "photo_url": photo_url
        }
        
        click.echo(f"✅ Alt text: '{alt_text}'")
        click.echo(f"👨‍💻 Photographer: {photographer_name} (@{username})")
        return image_info
        
    except requests.RequestException as e:
        click.echo(f"❌ Error accessing Unsplash: {e}")
        return None
    except Exception as e:
        click.echo(f"⚠️  Could not extract metadata, using defaults: {e}")
        # Fallback with basic info
        return {
            "download_url": f"https://unsplash.com/photos/{photo_id}/download",
            "alt_description": "image",
            "photographer": "Unsplash",
            "photographer_url": "https://unsplash.com",
            "photo_url": photo_url
        }


def create_meaningful_filename(description_or_url):
    """Create a meaningful filename for the image."""
    
    click.echo(f"🔧 Creating filename from: {description_or_url}")
    
    # If it's a URL, extract photo ID only
    if description_or_url.startswith('http'):
        photo_id_match = re.search(r'/photos/.*?([a-zA-Z0-9_-]{11})/?(?:\?|$)', description_or_url)
        if photo_id_match:
            photo_id = photo_id_match.group(1)
            filename = f"{photo_id}.jpg"
            click.echo(f"📝 Extracted photo ID '{photo_id}' → filename: {filename}")
            return filename
        else:
            click.echo(f"❌ Could not extract photo ID from URL")
            return "unsplash-photo.jpg"
    else:
        # Clean and simplify description
        keywords = re.sub(r'[^\w\s-]', '', description_or_url.lower())
        keywords = re.sub(r'\s+', '-', keywords.strip())
        keywords = keywords[:30]  # Limit length
        filename = f"{keywords}.jpg"
        click.echo(f"📝 Created filename from keywords: {filename}")
        return filename


def extract_title_from_content(content):
    """Extract the first heading from markdown content."""
    lines = content.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('# '):
            return line[2:].strip()
        elif line.startswith('## '):
            return line[3:].strip()
        elif line.startswith('### '):
            return line[4:].strip()
    
    # If no heading found, use first non-empty line
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            return line[:50] + "..." if len(line) > 50 else line
    
    return "Untitled Post"


def download_image(image_info, output_path):
    """Download and save an image."""
    click.echo(f"⬇️  Downloading from: {image_info['download_url']}")
    click.echo(f"💾 Saving to: {output_path}")
    
    try:
        response = requests.get(image_info["download_url"], timeout=30)
        response.raise_for_status()
        
        click.echo(f"📦 Downloaded {len(response.content)} bytes")
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        # Verify image is valid
        with Image.open(output_path) as img:
            img.verify()
        
        click.echo(f"✅ Image verified and saved successfully")
        return True
        
    except Exception as e:
        click.echo(f"❌ Error downloading image: {e}")
        if output_path.exists():
            output_path.unlink()
            click.echo(f"🗑️  Cleaned up failed download")
        return False


def generate_front_matter(title, slug, categories, tags, image_filename, image_info):
    """Generate Hugo front matter."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    if image_filename:
        front_matter = f"""---
title: "{title}"
date: {today}
slug: "{slug}"
image: "images/{image_filename}"
images: ['images/{image_filename}']
categories: {json.dumps(categories, ensure_ascii=False)}
tags: {json.dumps(tags, ensure_ascii=False)}
---"""
    else:
        front_matter = f"""---
title: "{title}"
date: {today}
slug: "{slug}"
categories: {json.dumps(categories, ensure_ascii=False)}
tags: {json.dumps(tags, ensure_ascii=False)}
---"""
    
    return front_matter


def create_post_content(content, image_filename, image_info):
    """Create the complete post content with image and attribution."""
    image_section = ""
    if image_info:
        alt_text = image_info["alt_description"]
        photographer = image_info["photographer"]
        photographer_url = image_info["photographer_url"]
        
        image_section = f"""![{alt_text}](images/{image_filename})Photo by [{photographer}]({photographer_url}) on [Unsplash](https://unsplash.com)

"""
    
    # Add footer at the end
    full_content = content.strip()
    if not full_content.endswith("{{< footer >}}"):
        full_content += "\n\n{{< footer >}}"
    
    return image_section + full_content


@click.command()
@click.option('--input-file', '-i', default='source.md', help='Input markdown file name')
@click.option('--auto-copy', '-c', is_flag=True, help='Automatically copy to Hugo content directory')
def main(input_file, auto_copy):
    """Hugo Blog Post Generator CLI Tool"""
    
    click.echo("🚀 Hugo Blog Post Generator")
    click.echo("=" * 40)
    
    # Check input file
    input_path = INPUT_DIR / input_file
    if not input_path.exists():
        click.echo(f"❌ Input file not found: {input_path}")
        click.echo(f"Please create the file: {input_path}")
        return
    
    # Read content
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        click.echo(f"❌ Error reading input file: {e}")
        return
    
    if not content.strip():
        click.echo("❌ Input file is empty")
        return
    
    # Extract title
    extracted_title = extract_title_from_content(content)
    click.echo(f"📝 Extracted title: {extracted_title}")
    
    # Get user inputs
    title = click.prompt("Blog post title", default=extracted_title).strip()
    
    # Get simple slug title from user
    today = datetime.now().strftime("%Y-%m-%d")
    slug_title = click.prompt("Enter slug title (e.g., 'ai-discussion')", default="").strip()
    
    if slug_title:
        # Use user input for slug
        slug = f"{today}-{slug_title}"[:SLUG_MAX_LENGTH]
    else:
        # Fallback to auto-generated slug from title
        title_slug = slugify(title, max_length=SLUG_MAX_LENGTH-len(today)-1)
        slug = f"{today}-{title_slug}"[:SLUG_MAX_LENGTH]
        click.echo(f"💡 Using auto-generated slug: {slug}")
    
    # Categories selection
    click.echo("\n📂 Available categories:")
    for i, cat in enumerate(CATEGORIES, 1):
        click.echo(f"  {i}. {cat}")
    
    category_input = click.prompt("Select category number(s) (comma-separated)", type=str)
    try:
        category_indices = [int(x.strip()) - 1 for x in category_input.split(',')]
        selected_categories = [CATEGORIES[i] for i in category_indices if 0 <= i < len(CATEGORIES)]
    except (ValueError, IndexError):
        click.echo("❌ Invalid category selection. Using first category.")
        selected_categories = [CATEGORIES[0]]
    
    # Tags input
    tags_input = click.prompt("Enter tags (comma-separated)", default="").strip()
    tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()] if tags_input else []
    
    # Image handling
    click.echo("\n🖼️  Image Processing:")
    image_info = None
    image_filename = None
    
    unsplash_url = click.prompt("Unsplash photo URL (or press Enter to skip)", default="").strip()
    
    if unsplash_url:
        image_info = get_unsplash_image_from_url(unsplash_url)
        
        if image_info:
            image_filename = create_meaningful_filename(unsplash_url)
            click.echo(f"📝 Generated filename: {image_filename}")
        else:
            click.echo("❌ Could not process Unsplash URL")
    else:
        click.echo("⏭️  Skipping image (no URL provided)")
    
    # Create output structure
    click.echo(f"\n📁 Creating output structure:")
    post_dir = OUTPUT_DIR / slug
    post_dir.mkdir(exist_ok=True)
    click.echo(f"✅ Created post directory: {post_dir}")
    
    images_dir = post_dir / "images"
    images_dir.mkdir(exist_ok=True)
    click.echo(f"✅ Created images directory: {images_dir}")
    
    # Download image if available
    if image_info and image_filename:
        image_path = images_dir / image_filename
        click.echo(f"\n📥 Image Download:")
        if download_image(image_info, image_path):
            click.echo(f"✅ Image saved: {image_path}")
        else:
            click.echo("❌ Image download failed, proceeding without image")
            image_info = None
            image_filename = None
    else:
        click.echo("⏭️  No image to download")
    
    # Generate post content
    click.echo(f"\n📝 Generating content:")
    click.echo(f"🔧 Image filename for front matter: {image_filename}")
    click.echo(f"🔧 Image info available: {image_info is not None}")
    
    front_matter = generate_front_matter(title, slug, selected_categories, tags, image_filename, image_info)
    post_content = create_post_content(content, image_filename, image_info)
    
    full_post = f"{front_matter}\n\n{post_content}"
    
    # Save to output
    index_path = post_dir / "index.md"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(full_post)
    
    click.echo(f"✅ Post created: {index_path}")
    
    # Auto-copy to Hugo directory
    if auto_copy:
        hugo_post_dir = HUGO_CONTENT_DIR / slug
        try:
            if hugo_post_dir.exists():
                shutil.rmtree(hugo_post_dir)
            shutil.copytree(post_dir, hugo_post_dir)
            click.echo(f"✅ Copied to Hugo directory: {hugo_post_dir}")
        except Exception as e:
            click.echo(f"❌ Error copying to Hugo directory: {e}")
    else:
        click.echo(f"\n📋 To publish, copy the output to:")
        click.echo(f"   {HUGO_CONTENT_DIR / slug}")
    
    click.echo("\n🎉 Blog post generation completed!")


if __name__ == '__main__':
    main()