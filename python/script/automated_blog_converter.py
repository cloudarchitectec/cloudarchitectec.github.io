#!/usr/bin/env python3
"""
Automates the creation of Hugo blog posts from markdown files with Unsplash images.
"""

import re
import os
import click
import requests
import shutil
import warnings
from datetime import datetime
from pathlib import Path
from slugify import slugify
from PIL import Image
import json
from bs4 import BeautifulSoup

# Suppress urllib3 warning on macOS
warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL 1.1.1+')

# Configuration
CATEGORIES = ["海外職場", "投資理財", "旅行紀錄", "澳洲生活"]
SLUG_MAX_LENGTH = 75

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
INPUT_DIR = SCRIPT_DIR.parent / "input"
OUTPUT_DIR = SCRIPT_DIR.parent / "output"
HUGO_CONTENT_DIR = PROJECT_ROOT / "content" / "posts"


def get_unsplash_image_from_url(photo_url):
    """Extract image info from Unsplash photo URL and get download link."""
    
    click.echo("\n=== URL Processing Debug Info ===")
    click.echo(f"Input URL: {photo_url}")
    
    click.echo("\n=== URL Processing Debug Info ===")
    click.echo(f"Input URL: {photo_url}")
    
    # Extract photo ID and description from URL
    photo_id = None
    description = None
    
    # Clean up the URL first
    clean_url = photo_url.strip()
    if '?' in clean_url:
        clean_url = clean_url.split('?')[0]
    
    # Extract both description and ID
    parts = clean_url.split('/photos/')
    if len(parts) > 1:
        # Get everything after /photos/
        full_slug = parts[1].strip()
        
        # Find the last part which should be the ID
        if '-' in full_slug:
            # Format with description
            slug_parts = full_slug.split('-')
            potential_id = slug_parts[-1]
            if len(potential_id) == 11:  # Standard Unsplash ID length
                photo_id = potential_id
                # Join all parts except the last one to get description
                description = '-'.join(slug_parts[:-1])
        else:
            # Format without description
            if len(full_slug) == 11:  # Direct ID format
                photo_id = full_slug
    
    # If still no photo_id, try regex as fallback
    if not photo_id:
        patterns = [
            r'/photos/(?:.*?-)?([a-zA-Z0-9_-]{11})/?(?:\?|$)',  # Matches both formats
            r'([a-zA-Z0-9_-]{11})/?$'  # Just the ID at the end
        ]
        
        for pattern in patterns:
            match = re.search(pattern, clean_url)
            if match:
                photo_id = match.group(1)
                break
    
    if photo_id:
        click.echo(f"📷 Extracted photo ID: {photo_id}")
        
        # Process description for alt text if available
        if description:
            # Convert hyphens to spaces and clean up
            alt_text = description.replace('-', ' ').strip()
            # Take first few meaningful words
            words = re.findall(r'\b[a-zA-Z]{3,}\b', alt_text.lower())
            alt_text = ' '.join(words[:3]) if words else "image"  # Use up to 3 words
            click.echo(f"📝 Generated alt text from description: {alt_text}")
        else:
            alt_text = "image"
            click.echo("ℹ️ No description found in URL, using default alt text")
    
    if not photo_id:
        click.echo(f"❌ Could not extract photo ID from URL: {photo_url}")
        return None
    
    try:
        # Get the photographer info from the page
        response = requests.get(photo_url, timeout=10)
        response.raise_for_status()
        page_content = response.text
        
        # Extract photographer info
        username_match = re.search(r'"username":"([^"]*)"', page_content)
        name_match = re.search(r'"name":"([^"]*)"', page_content)
        username = username_match.group(1) if username_match else "photographer"
        photographer_name = name_match.group(1) if name_match else username
        
        # Try to get a better alt text from the page if available
        alt_match = re.search(r'"alt_description":"([^"]*)"', page_content)
        if alt_match and alt_match.group(1):
            page_alt_text = alt_match.group(1).lower()
            words = re.findall(r'\b[a-zA-Z]{3,}\b', page_alt_text)
            if words:
                alt_text = " ".join(words[:3])  # Use up to 3 words from page description
        
        # Create image info dictionary with clean URLs
        image_info = {
            "photo_id": photo_id,
            "download_url": f"https://images.unsplash.com/photo-{photo_id}?ixlib=rb-4.0.3&q=85&w=1400&fit=crop",
            "photo_url": photo_url,
            "alt_description": alt_text,
            "photographer": photographer_name,
            "photographer_url": f"https://unsplash.com/@{username}"
        }
        
        click.echo(f"✅ Alt text: '{alt_text}'")
        click.echo(f"👨‍💻 Photographer: {photographer_name} (@{username})")
        return image_info
        
    except Exception as e:
        click.echo(f"⚠️ Error getting metadata: {e}")
        # Return basic info if metadata fetch fails
        return {
            "photo_id": photo_id,
            "download_url": f"https://images.unsplash.com/photo-{photo_id}",
            "photo_url": photo_url,
            "alt_description": "image",
            "photographer": "Unsplash Photographer",
            "photographer_url": "https://unsplash.com"
        }
    
    try:
        # First try to get image metadata to get the best URL
        response = requests.get(photo_url, timeout=10)
        response.raise_for_status()
        page_content = response.text
        
        # Try to find the optimized image URL
        img_url_match = re.search(r'"regular":"([^"]+)"', page_content)
        actual_download_url = img_url_match.group(1) if img_url_match else download_url
        
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
    """Extract title from content, first trying front matter, then headings."""
    lines = content.strip().split('\n')
    
    # First try to get title from front matter
    in_front_matter = False
    for line in lines:
        line = line.strip()
        if line == '---':
            in_front_matter = not in_front_matter
            continue
        if in_front_matter and line.startswith('title:'):
            # Extract title, handling both quoted and unquoted titles
            title = line[6:].strip()
            if title.startswith('"') and title.endswith('"'):
                title = title[1:-1]
            elif title.startswith("'") and title.endswith("'"):
                title = title[1:-1]
            return title
    
    # If no title in front matter, try headings
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
        if line and not line.startswith('#') and line != '---':
            return line[:50] + "..." if len(line) > 50 else line
    
    return "Untitled Post"


def extract_categories_and_tags_from_content(content):
    """Extract categories and tags from front matter if they exist."""
    lines = content.strip().split('\n')
    
    in_front_matter = False
    existing_categories = []
    existing_tags = []
    
    for line in lines:
        line = line.strip()
        if line == '---':
            in_front_matter = not in_front_matter
            continue
        
        if in_front_matter:
            if line.startswith('categories:'):
                # Extract categories - handle both formats: ["cat1", "cat2"] or ["cat1","cat2"]
                categories_str = line[11:].strip()
                try:
                    existing_categories = json.loads(categories_str)
                except json.JSONDecodeError:
                    # Try to parse manually if json fails
                    categories_str = categories_str.strip('[]')
                    if categories_str:
                        existing_categories = [cat.strip().strip('"\'') for cat in categories_str.split(',')]
                
            elif line.startswith('tags:'):
                # Extract tags - handle both formats: ["tag1", "tag2"] or ["tag1","tag2"]
                tags_str = line[5:].strip()
                try:
                    existing_tags = json.loads(tags_str)
                except json.JSONDecodeError:
                    # Try to parse manually if json fails
                    tags_str = tags_str.strip('[]')
                    if tags_str:
                        existing_tags = [tag.strip().strip('"\'') for tag in tags_str.split(',')]
    
    return existing_categories, existing_tags


def download_image(image_info, output_path):
    """Download and save an image."""
    click.echo("\n=== Image Download Debug Info ===")
    click.echo("Image Info Dictionary:")
    for key, value in image_info.items():
        click.echo(f"  {key}: {value}")
    
    if 'photo_id' not in image_info:
        click.echo("❌ Error: photo_id missing from image_info dictionary")
        return False
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://unsplash.com/'
    }
    
    # Check if it's a premium photo using image_info
    if any(premium_indicator in image_info['photo_url'] 
           for premium_indicator in ['plus.unsplash.com', 'premium_photo']):
        click.echo("\n❌ This appears to be a premium Unsplash photo which cannot be downloaded for free.")
        click.echo("Please provide a URL to a free photo instead.")
        return None

    # Try to get the actual image URL from the photo page first
    try:
        click.echo("\nFetching image URL from photo page...")
        page_response = requests.get(image_info['photo_url'], headers=headers, timeout=30)
        page_content = page_response.text
        
        # Check response for premium indicators
        if 'premium_photo' in page_content or 'plus.unsplash.com' in page_content:
            click.echo("\n❌ This appears to be a premium Unsplash photo which cannot be downloaded for free.")
            click.echo("Please provide a URL to a free photo instead.")
            return None
        
        # Try multiple patterns to find the image URL
        patterns = [
            r'"regular":"(https://images\.unsplash\.com/photo-[^"]+)"',  # New pattern for regular size
            r'"url":"(https://images\.unsplash\.com/photo-[^"]+)"',
            r'srcSet="(https://images\.unsplash\.com/photo-[^?"]+)',
            r'<meta property="og:image" content="([^"]+)"',
            r'<img class="[^"]*" src="(https://images\.unsplash\.com/photo-[^"]+)"'  # Direct image src
        ]
        
        # Extract timestamp and photo ID pattern from the page
        timestamp_pattern = r'"uploadedAt":"([^"]+)"'
        timestamp_match = re.search(timestamp_pattern, page_content)
        timestamp = ""
        if timestamp_match:
            try:
                timestamp = datetime.fromisoformat(timestamp_match.group(1).replace('Z', '+00:00')).strftime('%s')
            except ValueError:
                pass

        found_url = None
        for pattern in patterns:
            matches = re.finditer(pattern, page_content)
            for match in matches:
                potential_url = match.group(1)
                if image_info['photo_id'] in potential_url:
                    found_url = potential_url
                    break
            if found_url:
                break
        
        if found_url:
            # Clean up the URL and add quality parameters
            base_url = found_url.split('?')[0]  # Remove any existing parameters
            url_formats = [
                f"{base_url}?q=85&w=1400&fit=crop&ixlib=rb-4.0.3",
                f"{base_url}?q=80&w=1000&auto=format&ixlib=rb-4.0.3",
                base_url  # Try the direct URL as well
            ]
            click.echo(f"Found direct image URL: {url_formats[0]}")
        else:
            # Try to extract download URL from photo page
            page_response = requests.get(image_info['photo_url'], headers=headers, timeout=30)
            soup = BeautifulSoup(page_response.text, 'html.parser')
            
            # Look for the download button or meta tags
            download_link = soup.find('a', {'data-test': 'photo-download'})
            if download_link and 'href' in download_link.attrs:
                url_formats = [download_link['href']]
                click.echo(f"Found download URL from page: {url_formats[0]}")
            else:
                # Fallback to constructed URLs
                url_formats = [
                    f"https://images.unsplash.com/photo-{image_info['photo_id']}?ixlib=rb-4.0.3&q=85&w=1400&fit=crop",
                    f"https://images.unsplash.com/photo-{image_info['photo_id']}?ixlib=rb-4.0.3&q=80&w=1000",
                    f"https://source.unsplash.com/{image_info['photo_id']}/1400x1000"
                ]
                click.echo("⚠️ Using constructed URLs")
    except Exception as e:
        click.echo(f"⚠️ Failed to fetch photo page, using fallback URLs: {e}")
        url_formats = [
            f"https://images.unsplash.com/photo-{image_info['photo_id']}?ixlib=rb-4.0.3&q=85&w=1400&fit=crop",
            f"https://source.unsplash.com/{image_info['photo_id']}/1400x1000"
        ]
    
    click.echo("\nTrying multiple URL formats:")
    for url in url_formats:
        try:
            click.echo(f"\nAttempting to download from: {url}")
            response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
            click.echo(f"Status Code: {response.status_code}")
            click.echo(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                # Check if we got an image
                content_type = response.headers.get('Content-Type', '').lower()
                if not ('image/' in content_type or content_type.endswith('jpeg') or content_type.endswith('jpg')):
                    click.echo(f"❌ Received non-image content type: {content_type}")
                    continue
                
                # Save the image
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                click.echo(f"📦 Downloaded {len(response.content)} bytes")
                
                # Verify the downloaded image
                try:
                    with Image.open(output_path) as img:
                        # Actually load the image to verify it
                        img.load()
                        img.verify()
                    click.echo("✅ Image verified successfully")
                    return True
                except Exception as e:
                    click.echo(f"❌ Downloaded file is not a valid image: {e}")
                    if os.path.exists(output_path):
                        os.remove(output_path)
            else:
                click.echo(f"❌ Failed with status code: {response.status_code}")
        
        except Exception as e:
            click.echo(f"❌ Error trying URL {url}: {str(e)}")
            click.echo(f"Error type: {type(e).__name__}")
            if os.path.exists(output_path):
                os.remove(output_path)
            continue
    
    click.echo("❌ Failed to download image from any URL")
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
image: ""
images: [""]
categories: {json.dumps(categories, ensure_ascii=False)}
tags: {json.dumps(tags, ensure_ascii=False)}
---"""
    
    return front_matter


def create_post_content(content, image_filename, image_info):
    """Create the complete post content with image and attribution."""
    # Image section temporarily disabled
    image_section = ""
    # if image_info:
    #     alt_text = image_info["alt_description"]
    #     photographer = image_info["photographer"]
    #     photographer_url = image_info["photographer_url"]
    #     
    #     # Updated image section format with newlines and centered image
    #     image_section = f"""
    # {{< figure
    #     src="images/{image_filename}"
    #     alt="{alt_text}"
    #     caption="Photo by [{photographer}]({photographer_url}) on [Unsplash](https://unsplash.com)"
    #     >}}
    # 
    # """
    
    # Add footer at the end
    full_content = content.strip()
    if not full_content.endswith("{{< footer >}}"):
        full_content += "\n\n{{< footer >}}"
    
    return image_section + full_content


@click.command()
@click.argument('input_file', required=True)
@click.option('--auto-copy', '-c', is_flag=True, help='Automatically copy to Hugo content directory')
def main(input_file, auto_copy):
    """Hugo Blog Post Generator CLI Tool.
    
    INPUT_FILE: Name of the markdown file to process (e.g., my-post.md)
    """
    
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
    
    # Extract existing categories and tags from front matter
    existing_categories, existing_tags = extract_categories_and_tags_from_content(content)
    
    # Get user inputs
    title = click.prompt("Blog post title", default=extracted_title).strip()
    
    # Combine today's date with input file name for slug
    today = datetime.now().strftime("%Y-%m-%d")
    file_slug = Path(input_file).stem  # Get filename without extension
    slug = f"{today}-{file_slug}"[:SLUG_MAX_LENGTH]
    click.echo(f"📝 Generated slug from date and filename: {slug}")
    
    # Categories selection with existing categories as default
    click.echo("\n📂 Available categories:")
    for i, cat in enumerate(CATEGORIES, 1):
        click.echo(f"  {i}. {cat}")
    
    # Show existing categories if found
    if existing_categories:
        click.echo(f"\n🔍 Found existing categories in file: {existing_categories}")
        # Find the indices of existing categories in the CATEGORIES list
        default_indices = []
        for cat in existing_categories:
            try:
                index = CATEGORIES.index(cat) + 1  # +1 because we show 1-based numbers
                default_indices.append(str(index))
            except ValueError:
                click.echo(f"⚠️  Category '{cat}' not found in available categories")
        
        default_category_str = ",".join(default_indices) if default_indices else "1"
        category_input = click.prompt("Select category number(s) (comma-separated)", 
                                    default=default_category_str, type=str)
    else:
        category_input = click.prompt("Select category number(s) (comma-separated)", type=str)
    
    try:
        category_indices = [int(x.strip()) - 1 for x in category_input.split(',')]
        selected_categories = [CATEGORIES[i] for i in category_indices if 0 <= i < len(CATEGORIES)]
    except (ValueError, IndexError):
        click.echo("❌ Invalid category selection. Using first category.")
        selected_categories = [CATEGORIES[0]]
    
    # Tags input with existing tags as default
    if existing_tags:
        click.echo(f"\n🏷️  Found existing tags in file: {existing_tags}")
        default_tags_str = ",".join(existing_tags)
        tags_input = click.prompt("Enter tags (comma-separated)", default=default_tags_str).strip()
    else:
        tags_input = click.prompt("Enter tags (comma-separated)", default="").strip()
    
    tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()] if tags_input else []
    
    # Skip image handling
    image_info = None
    image_filename = None
    
    # Create output structure
    click.echo(f"\n📁 Creating output structure:")
    post_dir = OUTPUT_DIR / slug
    post_dir.mkdir(exist_ok=True)
    click.echo(f"✅ Created post directory: {post_dir}")
    
    images_dir = post_dir / "images"
    images_dir.mkdir(exist_ok=True)
    click.echo(f"✅ Created images directory: {images_dir}")
    
    # Download image if available - temporarily disabled
    # if image_info and image_filename:
    #     image_path = images_dir / image_filename
    #     click.echo(f"\n📥 Image Download:")
    #     if download_image(image_info, image_path):
    #         click.echo(f"✅ Image saved: {image_path}")
    #     else:
    #         click.echo("❌ Image download failed, proceeding without image")
    #         image_info = None
    #         image_filename = None
    # else:
    #     click.echo("⏭️  No image to download")
    
    # Temporary: always set these to None to skip image processing
    image_info = None
    image_filename = None
    
    # Generate post content
    click.echo(f"\n📝 Generating content:")
    click.echo(f"🔧 Image filename for front matter: {image_filename}")
    click.echo(f"🔧 Image info available: {image_info is not None}")
    
    # Remove any existing front matter from content
    content_lines = content.strip().split('\n')
    while content_lines and content_lines[0].strip() == '---':
        # Find the end of the front matter
        for i, line in enumerate(content_lines[1:], 1):
            if line.strip() == '---':
                content_lines = content_lines[i+1:]  # Skip the front matter
                break
    content = '\n'.join(content_lines).strip()
    
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