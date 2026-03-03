#!/usr/bin/env python3
"""
hexo → astro-whono migration script
Routes posts to essay / fiction / nonfiction / bits by top-level category.
"""

import os
import re
import sys
from pathlib import Path

HEXO_POSTS = Path.home() / 'hexo' / 'source' / '_posts'
DEST_BASE   = Path(__file__).parent / 'src' / 'content'

ROUTES = {
    'fanfiction':  DEST_BASE / 'essay',
    'fiction':     DEST_BASE / 'fiction',
    'Non-fiction': DEST_BASE / 'nonfiction',
}
BITS_DIR = DEST_BASE / 'bits'

KEEP_FIELDS = {'title', 'date', 'tags', 'categories', 'updated', 'description',
               'slug', 'draft', 'archive', 'cover', 'badge'}

FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)

def fix_typos(text: str) -> str:
    """Fix known frontmatter field typos from the hexo source."""
    # post 167: 'ategories:' → 'categories:'
    text = re.sub(r'^ategories:', 'categories:', text, flags=re.MULTILINE)
    return text

def parse_frontmatter(raw: str) -> tuple[dict, str]:
    """Return (fields_dict, body). Values are raw YAML strings."""
    m = FRONTMATTER_RE.match(raw)
    if not m:
        return {}, raw
    fm_block = m.group(1)
    body = raw[m.end():]
    fields: dict[str, str] = {}
    current_key = None
    current_val_lines: list[str] = []

    for line in fm_block.splitlines():
        key_match = re.match(r'^(\w+):\s*(.*)', line)
        if key_match:
            if current_key:
                fields[current_key] = '\n'.join(current_val_lines).strip()
            current_key = key_match.group(1)
            current_val_lines = [key_match.group(2)]
        else:
            current_val_lines.append(line)
    if current_key:
        fields[current_key] = '\n'.join(current_val_lines).strip()
    return fields, body

def parse_yaml_array(val: str) -> list[str]:
    """Parse '[a, b, c]' or '- a\n- b' into a list of strings."""
    val = val.strip()
    if val.startswith('[') and val.endswith(']'):
        inner = val[1:-1]
        items = [item.strip().strip('"').strip("'") for item in inner.split(',')]
        return [i for i in items if i]
    lines = [l.lstrip('- ').strip() for l in val.splitlines() if l.strip().startswith('-')]
    return lines

def make_slug(permalink: str) -> str | None:
    """Convert hexo permalink (e.g. '35308b_19dcaf9') to kebab-case slug."""
    if not permalink:
        return None
    slug = permalink.replace('_', '-').lower()
    if re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', slug):
        return slug
    return None

def yaml_str(val: str) -> str:
    """Wrap a string value in YAML double quotes, escaping internal quotes."""
    escaped = val.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'

def build_frontmatter(fields: dict, categories: list[str]) -> str:
    lines = ['---']

    title = fields.get('title', '').strip().strip('"').strip("'")
    lines.append(f'title: {yaml_str(title)}')

    date = fields.get('date', '').strip()
    if date:
        lines.append(f'date: {date}')

    updated = fields.get('updated', '').strip()
    if updated:
        lines.append(f'updated: {updated}')

    if categories:
        cats_str = ', '.join(yaml_str(c) for c in categories)
        lines.append(f'categories: [{cats_str}]')

    tags_raw = fields.get('tags', '').strip()
    if tags_raw and tags_raw not in ('[]', ''):
        tags = parse_yaml_array(tags_raw)
        if tags:
            tags_str = ', '.join(yaml_str(t) for t in tags)
            lines.append(f'tags: [{tags_str}]')
        else:
            lines.append('tags: []')
    else:
        lines.append('tags: []')

    permalink = fields.get('permalink', '').strip()
    slug = make_slug(permalink)
    if slug:
        lines.append(f'slug: {slug}')

    lines.append('---')
    return '\n'.join(lines) + '\n'

def dest_filename(src_name: str, dest_dir: Path, used: set[str]) -> Path:
    """Generate output filename from the numeric prefix of the source file."""
    stem = Path(src_name).stem          # e.g. '167 大雨将至 番外：...'
    num_match = re.match(r'^(\d+)', stem)
    base = num_match.group(1) if num_match else re.sub(r'[^\w-]', '-', stem)[:40]
    candidate = f'{base}.md'
    if candidate not in used:
        used.add(candidate)
        return dest_dir / candidate
    # fallback: append suffix
    i = 2
    while True:
        candidate = f'{base}-{i}.md'
        if candidate not in used:
            used.add(candidate)
            return dest_dir / candidate
        i += 1

def migrate():
    # Ensure dest dirs exist
    for d in [*ROUTES.values(), BITS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    posts = sorted(p for p in HEXO_POSTS.iterdir() if p.suffix == '.md')
    used_names: dict[Path, set[str]] = {d: set() for d in [*ROUTES.values(), BITS_DIR]}
    stats = {'essay': 0, 'fiction': 0, 'nonfiction': 0, 'bits': 0, 'errors': 0}

    for src in posts:
        try:
            raw = src.read_text(encoding='utf-8')
            raw = fix_typos(raw)
            fields, body = parse_frontmatter(raw)

            categories = parse_yaml_array(fields.get('categories', ''))
            top = categories[0] if categories else ''

            dest_dir = ROUTES.get(top, BITS_DIR)
            collection = {
                DEST_BASE / 'essay':      'essay',
                DEST_BASE / 'fiction':    'fiction',
                DEST_BASE / 'nonfiction': 'nonfiction',
                BITS_DIR:                 'bits',
            }[dest_dir]

            fm = build_frontmatter(fields, categories)
            dest_path = dest_filename(src.name, dest_dir, used_names[dest_dir])
            dest_path.write_text(fm + body, encoding='utf-8')
            stats[collection] += 1

        except Exception as e:
            print(f'ERROR: {src.name}: {e}', file=sys.stderr)
            stats['errors'] += 1

    print('Migration complete:')
    for k, v in stats.items():
        print(f'  {k}: {v}')

if __name__ == '__main__':
    migrate()
