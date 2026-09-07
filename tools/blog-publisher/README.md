# Hugo blog post publisher

Interactive CLI for turning a Markdown draft into a validated Hugo page bundle
with an Unsplash cover image.

## Set up

Run commands from the repository root:

```bash
bash scripts/ensure-venv.sh
```

Add an [Unsplash API](https://unsplash.com/developers) access key to the
repository-root `.env` file:

```dotenv
UNSPLASH_ACCESS_KEY=your_key_here
```

Never commit the repository-root `.env` file or a real access key. Keep only
placeholder values in public documentation.

The shared root [`requirements.txt`](../../requirements.txt) contains the
publisher's Python dependencies; there is no separate environment for this
tool.

## Publish a draft

1. Put the draft in `tools/blog-publisher/input/`. This directory is ignored by
   Git.
2. Pass only its filename to the publisher:

   ```bash
   scripts/py tools/blog-publisher/pre-publish-post.py your-post.md
   ```

3. Review the generated page bundle under `content/posts/{slug}/` and the
   validation output.

The draft may start with YAML front matter. Supported fields are `title`,
`slug`, `categories`, `tags`, and `episodeseries`; the body remains regular
Markdown. The CLI prompts for the publication date and defaults it to today.
Any `date` in the draft front matter is ignored. The CLI constructs the default
folder slug as `{date}-{bare-slug}`.

Do not add `{{< footer >}}` to the draft. The site layout renders the post
footer, and the publisher removes that legacy shortcode if it is present.

## What the publisher does

The interactive flow:

- confirms the date and slug;
- requires one category from [`data/categories.yaml`](../../data/categories.yaml);
- confirms tags and an optional series from
  [`data/episodeseries.json`](../../data/episodeseries.json);
- downloads an Unsplash cover, records its credit and required alt text, and
  normalizes progressive JPEGs to baseline encoding;
- optionally removes a redundant leading heading so list excerpts start with
  prose;
- writes `content/posts/{slug}/index.md` and
  `content/posts/{slug}/images/{photo-id}-unsplash.jpg`;
- runs the spelling fixer, regenerates
  [`docs/POSTS-INDEX.md`](../../docs/POSTS-INDEX.md), and validates the new post
  with `scripts/check-posts.py --post`;
- starts `hugo server` when port 1313 is free.

The cover is required for successful post validation. A failed cover download
can be retried once with another Unsplash URL.

Publishing directly replaces an existing post directory only after an explicit
confirmation. If validation fails, the generated files remain in place so the
reported problems can be fixed.

To publish without starting Hugo:

```bash
scripts/py tools/blog-publisher/pre-publish-post.py your-post.md --no-hugo
```

For the complete local gate before opening a PR, run:

```bash
./scripts/dev-check.sh --full
```

## Minimal input example

```yaml
---
title: "Example post"
slug: "example-post"
tags: ["example"]
---

Write the post body here.
```

The date is selected in the prompt. For example, choosing `2026-01-15`
produces `content/posts/2026-01-15-example-post/` and a matching `slug` in the
generated front matter.

## Image maintenance

The publisher normalizes every downloaded progressive JPEG. To repair existing
post covers in bulk, run:

```bash
scripts/py scripts/optimize-post-images.py --fix-progressive --apply
```
