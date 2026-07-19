# Hugo Blog Post Publisher

CLI tool to publish blog posts from pre-publish markdown with Unsplash cover images.

## Quick Setup

1. **Install dependencies:**
   ```bash
   cd tools/blog-publisher
   pip3 install -r requirements.txt
   ```

2. **Add Unsplash API key** to repo-root `.env`:
   ```
   UNSPLASH_ACCESS_KEY=your_key_here
   ```

3. **Browse [Unsplash](https://unsplash.com)**, copy the photo URL for the cover hero.

## Workflow

1. **Place your pre-publish markdown** at `tools/blog-publisher/input/your-post.md`
   - YAML front matter: `title`, `date`, `slug` (bare, no date prefix), `tags`, optional `categories`, optional `episodeseries`
   - Body: markdown (`##` sections, horizontal rules OK)
   - Do **not** add `{{< footer >}}` — footer is layout-driven

2. **Run the publisher**:
   ```bash
   cd tools/blog-publisher
   python3 pre-publish-post.py 2026-07-09-ai-interface-evolution.md
   ```

3. **Answer prompts:**
   - **Date** — defaults to today
   - **Slug** — defaults to `{date}-{bare-slug}` (matches folder name under `content/posts/`)
   - **Category** — pick one from allowed list (draft category pre-selected; Enter to accept)
   - **Tags** — confirm or edit (input tags shown as default)
   - **Series** — confirm input series or pick from registry
   - **Unsplash URL** + alt text — paste URL when prompted; one retry if download fails (`n` to skip)

4. **Output** is written directly to `content/posts/{slug}/`:
   - `index.md` — Hugo front matter + body (never `draft: true`)
   - `images/{photoId}-unsplash.jpg` — cover

There is **no** staging folder — output goes straight to `content/posts/`.

## Post rules enforced (matches `scripts/check-posts.py`)

| Rule | Publisher behaviour |
|------|---------------------|
| `cover.image` + `cover.alt` + `cover.credit` | Generated for Unsplash heroes (`{photoId}-unsplash.jpg`) |
| `images:` includes cover path | All bundle JPEGs/PNGs listed in `images:` |
| Baseline JPEG | Normalized after every Unsplash download |
| Cover size limits | Warns/errors via `image-size-check.py` after download |
| No `{{< footer >}}` | Stripped if present; footer is layout-driven |
| `slug` matches directory | Date-prefixed slug used for folder name |
| Published posts need cover | Validation fails if cover is skipped |
| Exactly one category | Picker enforces single selection from `data/categories.yaml` |
| Validation before finish | Runs `scripts/check-posts.py --post` on `content/posts/{slug}/` |

See [`TESTING.md`](../../TESTING.md) for the full validation tiers.

## Input front matter example

```yaml
---
title: "讀完《槓桿ETF投資法》：如果我還在台灣，我會買——但我不在"
date: 2026-06-18
slug: "leveraged-etf-taiwan-vs-australia"
tags: ["投資", "ETF", "澳洲理財"]
categories: []
---
```

Published output uses `slug: "2026-06-18-leveraged-etf-taiwan-vs-australia"` and a `cover:` block.

## Allowed categories

Canonical list in `data/categories.yaml` (`order` + `meta`). Validation loads via `scripts/categories_registry.py`.

Display order on the post-list page:

- 澳洲職場
- 投資理財
- 旅行紀錄
- 澳洲生活
- 轉職工程師日記

Meta only (not shown on post-list):

- EC

## Command options

```bash
# Publish post (starts Hugo dev server if port 1313 is free)
python3 tools/blog-publisher/pre-publish-post.py leveraged-etf-taiwan-vs-australia.md

# Skip Hugo auto-start
python3 tools/blog-publisher/pre-publish-post.py leveraged-etf-taiwan-vs-australia.md --no-hugo
```

## Cover JPEG encoding (baseline vs progressive)

Unsplash CDN downloads may arrive as **progressive JPEG**. This repo standardizes on **baseline** for consistency.

**On every new cover download**, `pre-publish-post.py` calls `normalize_jpeg_baseline()` after save.

Bulk fix existing covers:

```bash
python3 scripts/optimize-post-images.py --fix-progressive --apply
```

## Folder structure

```
tools/blog-publisher/
├── README.md
├── pre-publish-post.py
├── requirements.txt
└── input/              # Place pre-publish .md here
    └── your-post.md

content/posts/          # Output written here directly
└── 2026-06-18-your-slug/
    ├── index.md
    └── images/
        └── {photoId}-unsplash.jpg
```

**Post footer:** Subscribe + coffee CTAs render from `layouts/partials/post-footer.html`. Do **not** add `{{< footer >}}` to posts.
