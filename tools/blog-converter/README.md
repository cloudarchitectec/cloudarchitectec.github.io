# Hugo Blog Post Generator

A EC CLI tool to automate blog post creation with Unsplash images.

## Quick Setup

1. **Install dependencies:**
   ```bash
   cd tools/blog-converter
   pip3 install -r requirements.txt
   ```

2. **Add Unsplash API key** to repo-root `.env`:
   ```
   UNSPLASH_ACCESS_KEY=your_key_here
   ```

3. **Browse [Unsplash](https://unsplash.com)**, copy the photo URL for the cover hero.

## Post rules enforced (matches `scripts/check-posts.py`)

| Rule | Converter behaviour |
|------|---------------------|
| `cover.image` + `cover.alt` + `cover.credit` | Generated for Unsplash heroes (`{photoId}-unsplash.jpg`) |
| `images:` includes cover path | All bundle JPEGs/PNGs listed in `images:` |
| Baseline JPEG | Normalized after every Unsplash download |
| Cover size limits | Warns/errors via `image-size-check.py` after download |
| No `{{< footer >}}` | Stripped if present; footer is layout-driven |
| `slug` matches directory | Slug `{date}-{file-stem}` used for folder name |
| Published posts need cover | Warns if you skip cover — use `draft: true` for bootcamp drafts |
| Validation before copy | Runs `scripts/check-posts.py --post` automatically |

See [`TESTING.md`](../../TESTING.md) for the full validation tiers.

## How to Use

1. **Put your blog content in:** `tools/blog-converter/input/source.md` 
   - Just plain text with markdown
   - Make sure there's a heading (# or ## or ###) for the title

2. **Run the script:**
   ```bash
   python3 tools/blog-converter/automated_blog_converter.py {file_name}.md
   ```

3. **Answer the prompts:**
   - **Title:** Usually auto-detected from your first heading
   - **Slug title:** Enter simple slug like "ai-discussion" → becomes "2025-10-12-ai-discussion"
   - **Categories:** Pick numbers (you can select multiple with commas):
     ```
     1. 投資理財
     2. 旅行紀錄  
     3. 海外職場
     4. 澳洲生活
     ```
   - **Tags:** Type whatever, comma-separated
   - **Unsplash URL:** Required for published posts (cover.image). Press `n` only for drafts — add `draft: true` manually before publishing.

4. **Check output:** `tools/blog-converter/output/2025-10-12-your-slug/`
   - `index.md` - Your complete blog post (ready to publish)
   - `images/PHOTO_ID.jpg` - Downloaded image

5. **Publish:**
   - Copy to Hugo content folder or use `-c` flag (runs post validation automatically)

**Post footer:** Subscribe + coffee CTAs render from `layouts/partials/post-footer.html` via `single.html`. Do **not** add `{{< footer >}}` to generated posts.

## Cover JPEG encoding (baseline vs progressive)

Unsplash CDN downloads may arrive as **progressive JPEG** (`file … progressive` in terminal). Browsers render both; this repo standardizes on **baseline** for consistency and tooling compatibility.

**On every new cover download**, `automated_blog_converter.py` calls `normalize_jpeg_baseline()` after save.

**Rules:**

| Rule | Detail |
|------|--------|
| Cover format | Baseline JPEG (`progressive=False`, quality 85) |
| When | Immediately after Unsplash download |
| Check | `check-posts.py` warns if cover is still progressive |
| Bulk fix existing | `python3 scripts/optimize-post-images.py --fix-progressive --apply` |

```bash
# Preview progressive JPEGs in post bundles
python3 scripts/optimize-post-images.py --fix-progressive --dry-run

# Re-encode all progressive JPEGs as baseline
python3 scripts/optimize-post-images.py --fix-progressive --apply
```

Verify one file: `file content/posts/{slug}/images/*.jpg` — should say **baseline**, not **progressive**.

## Command Options

```bash
# Auto-copy to Hugo content folder (saves manual copying)
cd tools/blog-converter

# Both together
python3 automated_blog_converter.py 2025-nz-trip-snowboarding.md -c 
```

## Variables You Can Tweak

Edit `automated_blog_converter.py` to customize:

```python
# Line ~18: Your categories (add/remove as needed)
CATEGORIES = ["投資理財", "旅行紀錄", "海外職場", "澳洲生活"]

# Line ~19: Maximum slug length 
SLUG_MAX_LENGTH = 75

# Lines ~130-135: Image filename pattern
def create_meaningful_filename(search_keywords):
    # Currently: "laptop-coffee.jpg" from "laptop coffee"
    # Modify this function to change naming
```


## Folder Structure

```
tools/blog-converter/
├── README.md        # This file
├── automated_blog_converter.py    # Main CLI script
├── requirements.txt     # Dependencies
├── input/           # Put your .md files here
│   └── source.md    # Default input file
└── output/          # Generated posts appear here
    └── 2025-10-12-slug/
        ├── index.md
        └── images/
            └── image.jpg
```

## What It Does

✅ Reads your markdown file  
✅ Extracts title from first heading  
✅ Generates date-based slug (2025-10-12-title)  
✅ Downloads your chosen image from Unsplash (no signup needed!)  
✅ Saves cover JPEG as **baseline** encoding (auto after Unsplash download)  
✅ Extracts real photographer info and creates simple alt text  
✅ Creates clean image filename (just the photo ID)  
✅ Generates Hugo front matter (ready to publish)  
✅ Adds image with proper photographer attribution  
✅ Strips legacy `{{< footer >}}` if present (post footer is layout-driven — see README)  
✅ Validates output via `scripts/check-posts.py` before copy  
✅ Creates proper folder structure  