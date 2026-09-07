# Blog video publishing guide

Read this guide before adding a video to a Hugo post bundle. It defines the
human-readable workflow; always inspect the actual source clip before making
changes.

## When to use a local video

Use a local video for a short moment that materially adds to the story, such as
a wild-animal sighting or a brief view that is difficult to describe in text.
For a long-form video, frequent uploads, or a file that exceeds the limits
below, use an external video host instead and embed or link to it.

Do not add a source `.MOV` to `content/posts/{slug}/images/` for publication.
Hugo copies all page-bundle resources to the built site, even if the video is
not yet embedded in the Markdown.

## Limits

| Item | Preferred | Discuss before exceeding |
| --- | --- | --- |
| Published video duration | 5–20 seconds | 30 seconds |
| Published MP4 file size | 5–8 MB | 10 MB; do not publish over 20 MB without choosing an external host |
| Published resolution | 1280×720 landscape, or 720×1280 portrait | 1920×1080 |
| Source clip retained locally | Keep outside the post bundle and Git history | 60 MB or 60 seconds; trim or use external hosting first |

These are performance limits, not a reason to artificially enhance or alter
the content of a personal video. Preserve the subject and duration unless the
author asks for an edit.

## Required output

- Use a descriptive, lowercase filename such as `dolphins.mp4`.
- Put only the publish-ready `.mp4` in
  `content/posts/{slug}/images/`.
- Use H.264 video in `yuv420p` and AAC audio in an MP4 container.
- Limit the long edge to 1280px by default and use `+faststart` so playback can
  begin before the whole file downloads.
- Remove GPS coordinates, device model, creation location, and other original
  metadata before publishing.
- Keep the original `.MOV` outside the Hugo post bundle and do not commit it.

## Conversion command

Run from the repository root. The quoted optional audio map is important in
zsh: it avoids treating `?` as a filename wildcard.

```bash
ffmpeg -y -hide_banner -loglevel warning \
  -i /path/to/source.MOV \
  -map 0:v:0 -map '0:a:0?' -map_metadata -1 \
  -vf 'scale=1280:-2:flags=lanczos,format=yuv420p' \
  -c:v libx264 -preset slow -b:v 5M -maxrate 5M -bufsize 10M \
  -movflags +faststart \
  -c:a aac -b:a 128k \
  content/posts/{slug}/images/descriptive-name.mp4
```

For a portrait source, use `scale=-2:1280` instead. If the result is above
10 MB, reduce the video bitrate gradually (for example, from `5M` to `4M`) or
trim the clip; do not silently lower the resolution below 720p.

## Verification and embedding

Inspect the published file before editing the post:

```bash
ffprobe -v error \
  -show_entries format=duration,size,bit_rate:stream=codec_name,codec_type,width,height \
  -of default=noprint_wrappers=1 \
  content/posts/{slug}/images/descriptive-name.mp4

strings content/posts/{slug}/images/descriptive-name.mp4 \
  | rg -i 'ISO6709|location|iPhone|Apple'
```

The second command must produce no output. Then use a plain HTML player in the
relevant paragraph. An inline video must match the full width of the article
text column (`width: 100%`); do not impose an arbitrary narrower maximum width.
The player must remain responsive on small screens. Do not enable autoplay,
loop, or preload of the full file:

```html
<video controls preload="metadata" playsinline style="width: 100%; height: auto;">
  <source src="images/descriptive-name.mp4" type="video/mp4">
  Your browser does not support embedded video.
</video>
```

Finally run the normal post checks and a Hugo build that includes drafts when
the post is still a draft:

```bash
scripts/py scripts/check-posts.py --post {slug}
hugo --buildFuture --buildDrafts
```
