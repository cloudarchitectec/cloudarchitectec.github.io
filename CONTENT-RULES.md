# Content rules

Read this file before creating or editing a post. It is a concise index for
humans; the scripts and tests linked below are authoritative.

| Area | Rule | Check / command | Enforcement |
| --- | --- | --- | --- |
| Post bundle | Use `content/posts/{slug}/index.md`; bundle image paths are relative (`images/file.jpg`). | `scripts/py scripts/check-posts.py --post SLUG` | Blocks invalid posts. |
| Front matter | `title`, `date`, and a folder-matching `slug` are required. Use exactly one allowed category; `episodeseries`, if present, is non-empty. | `scripts/post-validation/frontmatter-check.py` | Blocks invalid posts. |
| Draft and cover | Published posts require `cover.image`; a cover needs descriptive alt text and must appear in `images:`. | `scripts/check-posts.py` | Blocks invalid posts. |
| Unsplash | A `*-unsplash.jpg` cover requires photographer, profile URL, and the specific photo URL in `cover.credit`. | `scripts/check-posts.py` | Blocks invalid posts. |
| Images | Referenced bundle images must exist. Avoid absolute image paths, duplicate cover images in the body, double extensions, and filename-like alt text. | `scripts/check-posts.py` | Missing files and double extensions block; alt text is warned. |
| Image quality | Hard limit: 4,000px / 2MB. Covers target 1,600px / 800KB; inline images target 2,000px / 500KB. Use baseline JPEG. | `scripts/check-posts.py`; `scripts/optimize-post-images.py --post SLUG --fix-progressive --apply` | Hard limit blocks; quality issues warn. |
| Video | Publish short, metadata-stripped H.264/AAC MP4 files only. Do not leave source `.MOV` files in a Hugo page bundle. Inline players must match the article text-column width. | [Video publishing guide](VIDEO-PUBLISHING.md) | Manual review before embedding. |
| Footer | Do not add `{{< footer >}}`; the layout renders it. | `scripts/check-posts.py` | Blocks invalid posts. |
| English and spacing | Use British English and the repository's zh-TW / Latin / number spacing rules. Do not use markdown bold for isolated numbers, amounts, or English words. | `scripts/py scripts/check-spelling.py --fix --post SLUG` | Auto-fix where safe; then review output. |
| AUD amounts | In posts dated 2026-09-06 or later, write each AUD amount as `$535 澳幣（約 10,700 台幣）`. Confirm the exchange-rate assumption manually; the checker never guesses it. | `scripts/py scripts/check-spelling.py --strict --post SLUG` | Blocks local checks, pre-commit, PR validation, and deployment. |
| Generated index | `docs/POSTS-INDEX.md` lists published posts only; drafts are intentionally excluded. Do not edit it by hand. | `scripts/py scripts/gen-posts-index.py --check` | Blocks pre-commit and CI when stale. |

## Required review sequence

```bash
scripts/py scripts/check-spelling.py --fix --post SLUG
scripts/py scripts/check-spelling.py --strict --post SLUG
scripts/py scripts/check-posts.py --post SLUG
scripts/py scripts/gen-posts-index.py
./scripts/dev-check.sh --post SLUG
```

For a visual review of a draft, use:

```bash
hugo server -D --buildFuture
```
