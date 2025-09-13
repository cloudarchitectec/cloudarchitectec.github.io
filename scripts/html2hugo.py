import sys
from pathlib import Path
import re
import shutil
from bs4 import BeautifulSoup
import html2text
import logging
import yaml
from datetime import datetime
import requests
from urllib.parse import urljoin, urlparse

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def extract_date_and_first_word(filename):
    """Extract date and first word after hyphen from filename"""
    # Remove the .html extension first
    filename = Path(filename).stem
    # Fix the regex pattern to properly handle the filename format
    pattern = r'(\d{4}-\d{2}-\d{2})(?:_-(\w+))?'  # Fixed the closing parenthesis
    match = re.match(pattern, filename)
    
    if not match:
        logging.error(f"Could not extract date from filename: {filename}")
        return None, None
        
    date = match.group(1)
    first_word = match.group(2) if match.group(2) else 'post'
    
    # Validate the date and use current date if invalid
    try:
        parsed_date = datetime.strptime(date, '%Y-%m-%d')
        # Check if it's a placeholder date (year 2000 or before 1900)
        if parsed_date.year <= 2000:
            current_date = datetime.now().strftime('%Y-%m-%d')
            logging.warning(f"Invalid/placeholder date {date} found, using current date: {current_date}")
            date = current_date
    except ValueError:
        current_date = datetime.now().strftime('%Y-%m-%d')
        logging.warning(f"Invalid date format {date}, using current date: {current_date}")
        date = current_date
    
    if first_word:
        # Remove special characters and convert to lowercase
        first_word = re.sub(r'[^a-zA-Z0-9]', '', first_word).lower()
        logging.info(f"Extracted date: {date}, first word: {first_word}")
        return date, first_word
    return date, 'post'

def download_image(img_url, output_dir):
    """Download image and return local path"""
    try:
        original_url = img_url
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Handle different URL formats
        if 'unsplash.com' in img_url:
            # Extract photo ID from various Unsplash URL formats
            if '/photos/' in img_url:
                photo_id = img_url.split('/photos/')[-1].split('/')[0].split('?')[0]
            elif 'photo-' in img_url:
                photo_id = img_url.split('photo-')[-1].split('?')[0]
            else:
                # Try to extract from the end of the URL
                photo_id = img_url.rstrip('/').split('/')[-1].split('?')[0]
            
            # Use Unsplash download URL
            download_url = f'https://unsplash.com/photos/{photo_id}/download?force=true'
            img_name = f'unsplash-{photo_id}.jpg'
        elif 'medium.com' in img_url:
            # Handle Medium CDN images
            parsed = urlparse(img_url)
            path_parts = parsed.path.split('/')
            if len(path_parts) > 1:
                img_name = f'medium-{path_parts[-1]}.jpg'
            else:
                img_name = 'medium-image.jpg'
            download_url = img_url
        else:
            # Generic handling
            parsed = urlparse(img_url)
            img_name = parsed.path.split('/')[-1] or 'image.jpg'
            if not img_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                img_name += '.jpg'
            download_url = img_url
        
        # Ensure images directory exists
        images_dir = output_dir / 'images'
        images_dir.mkdir(parents=True, exist_ok=True)
        img_path = images_dir / img_name
        
        # Download image
        response = requests.get(download_url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(img_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logging.info(f"Downloaded image: {img_name}")
        return f'images/{img_name}'
        
    except Exception as e:
        logging.error(f"Failed to download image {img_url}: {e}")
        # Return a placeholder or skip the image
        return None

def process_html(input_file, output_dir):
    """Process HTML file and convert to markdown"""
    # Extract date and first_word from filename
    date, first_word = extract_date_and_first_word(input_file.name)
    if not date:
        logging.error(f"Invalid filename format: {input_file.name}")
        return False
    
    # Use the original HTML filename (without extension) as the folder name
    folder_name = input_file.stem
    post_dir = output_dir / folder_name
    post_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Read HTML content
        with open(input_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract metadata
        title = soup.title.string if soup.title else ''
        # Extract subtitle from meta
        subtitle = ''
        meta_desc = soup.find('meta', attrs={'property': 'og:description'}) or soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            subtitle = meta_desc.get('content', '')
        # Extract alias (old URL)
        alias = ''
        canonical = soup.find('link', rel='canonical') or soup.find('meta', attrs={'property': 'og:url'})
        if canonical:
            alias = canonical.get('href', '') if canonical.name == 'link' else canonical.get('content', '')
        # Extract tags
        tags = []
        tag_metas = soup.find_all('meta', attrs={'property': 'article:tag'})
        for tag_meta in tag_metas:
            tag = tag_meta.get('content', '').strip()
            if tag:
                tags.append(tag)
        # Slug from filename
        slug = re.sub(r'[^a-zA-Z0-9-]', '', folder_name).lower()
        
        # Find main content section
        content = soup.find('section', attrs={'data-field': 'body'})
        if not content:
            content = soup.find('article', class_='h-entry')
        
        if content:
            # Enhanced HTML cleanup
            # Remove unnecessary attributes
            for tag in content.find_all(True):
                allowed_attrs = ['src', 'href', 'alt']
                attrs = dict(tag.attrs)
                for attr in attrs:
                    if attr not in allowed_attrs:
                        del tag[attr]
                # Remove empty links
                if tag.name == 'a' and not tag.get('href'):
                    tag.decompose()
                # Remove duplicate titles or empty elements
                if tag.name in ['h1', 'h2'] and tag.get_text().strip() == title.strip():
                    tag.decompose()
            
            # Process images before conversion
            images = []
            featured_image = ''
            for img in content.find_all('img'):
                if img.get('src'):
                    local_path = download_image(img['src'], post_dir)
                    if local_path:  # Only proceed if download was successful
                        img['src'] = local_path
                        images.append(local_path)
                        # Set featured image (first successful download)
                        if not featured_image:
                            featured_image = local_path
                    else:
                        # Remove the img tag if download failed
                        img.decompose()
            
            # Configure html2text
            h2t = html2text.HTML2Text()
            h2t.body_width = 0  # Disable line wrapping
            h2t.ignore_links = False
            h2t.ignore_images = False
            h2t.ignore_emphasis = False
            h2t.ignore_tables = False
            markdown_content = h2t.handle(str(content))
            
            # Clean up the markdown content
            # Remove layout suffixes from image paths in markdown
            markdown_content = re.sub(r'(images/[^)]+)#layout\w+', r'\1', markdown_content)
            
            # Write markdown file - always named index.md
            output_file = post_dir / "index.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('---\n')
                f.write(f'title: "{title}"\n')
                f.write(f'date: {date}T00:00:00Z\n')
                if alias:
                    f.write(f'alias: ["{alias}"]\n')
                if tags:
                    f.write(f'tags: {tags}\n')
                f.write(f'slug: "{slug}"\n')
                if subtitle:
                    f.write(f'subtitle: "{subtitle}"\n')
                if featured_image:
                    f.write(f'image: "{featured_image}"\n')
                if images:
                    f.write(f'images: {images}\n')
                f.write('---\n\n')
                f.write(markdown_content)
            
            return True
        else:
            logging.error("Could not find main content section")
            return False
            
    except Exception as e:
        logging.error(f"Error processing {input_file}: {str(e)}")
        logging.exception("Stack trace:")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python html2hugo.py <source_folder> <target_folder>")
        sys.exit(1)
    
    source_dir = Path(sys.argv[1])
    target_dir = Path(sys.argv[2])
    
    setup_logging()
    
    if not source_dir.exists():
        logging.error(f"Source directory does not exist: {source_dir}")
        sys.exit(1)
    
    for html_file in source_dir.glob("*.html"):
        if process_html(html_file, target_dir):
            logging.info(f"Successfully processed: {html_file.name}")
        else:
            logging.warning(f"Failed to process: {html_file.name}")

if __name__ == "__main__":
    main()
