#!/usr/bin/env python3
"""Report possible consecutive image groups. Never modify posts."""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / 'content/posts'
GALLERY = re.compile(r'{{<\s*gallery\b.*?{{<\s*/gallery\s*>}}', re.S)
IMAGE = re.compile(r'!\[([^\]]*)\]\((images/[^)]+)\)|{{<\s*figure\b[^>]*?\bsrc=["\']([^"\']+)["\'][^>]*>}}')
CAPTION = re.compile(r'^\s*\*[^*\n]+\*\s*$')


def report(path):
    text = path.read_text(encoding='utf-8')
    body = text.split('---', 2)[2] if text.startswith('---') else text
    body = GALLERY.sub(lambda m: '\n[existing gallery]\n' + '\n' * m.group().count('\n'), body)
    items = list(IMAGE.finditer(body))
    groups = []
    current = []
    for item in items:
        if current:
            gap = body[current[-1].end():item.start()].strip()
            if gap and not CAPTION.fullmatch(gap):
                if len(current) > 1:
                    groups.append(current)
                current = []
        current.append(item)
    if len(current) > 1:
        groups.append(current)
    offset = text[:text.find(body)].count('\n') if body in text else text.split('---', 2)[1].count('\n') + 2
    for group in groups:
        line = offset + body[:group[0].start()].count('\n') + 1
        print(f'{path.parent.name}:{line} — {len(group)} consecutive images' + (' (ask how to split)' if len(group) > 4 else ''))
        for item in group:
            print('  ' + (item.group(2) or item.group(3)))
    return len(groups)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--post', help='Post slug; omit for all posts')
    args = parser.parse_args()
    paths = [POSTS / args.post / 'index.md'] if args.post else sorted(POSTS.glob('*/index.md'))
    if any(not path.is_file() for path in paths):
        parser.error('post not found')
    total = sum(report(path) for path in paths)
    print(f'{total} candidate groups; manual review required; no files changed.')


if __name__ == '__main__':
    main()
