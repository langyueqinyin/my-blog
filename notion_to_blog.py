#!/usr/bin/env python3
"""notion_to_blog.py — 把 Notion 导出的 .md 文件转换为博客格式并 git push。

用法：
    python3 notion_to_blog.py <notion导出的.md文件>
    python3 notion_to_blog.py           # 不传参数则交互式输入路径
"""

import re
import sys
import subprocess
from datetime import date
from pathlib import Path

BLOG_ROOT = Path(__file__).parent
CONTENT_ROOT = BLOG_ROOT / "src" / "content"

COLLECTIONS = [
    ("essay",      "同人作品 / Fan Fiction"),
    ("fiction",    "原创作品 / Fiction"),
    ("nonfiction", "非虚构 / Non-Fiction"),
    ("bits",       "其他 / Misc"),
]

# Notion 在文件名末尾附加的 32 位十六进制 hash
NOTION_HASH_RE = re.compile(r'\s+[0-9a-f]{32}$', re.IGNORECASE)


# ── 文件名处理 ─────────────────────────────────────────────────────────────

def strip_notion_hash(stem: str) -> str:
    return NOTION_HASH_RE.sub('', stem).strip()


# ── 内容清理 ───────────────────────────────────────────────────────────────

def clean_notion_content(text: str) -> str:
    """去除 Notion 导出文件中的 metadata 块和多余格式。"""
    lines = text.splitlines()

    # 1. 如果已有 frontmatter（---），整块去掉
    if lines and lines[0].strip() == '---':
        end = next(
            (i for i, l in enumerate(lines[1:], 1) if l.strip() == '---'),
            None
        )
        if end is not None:
            lines = lines[end + 1:]

    # 2. 去掉开头空行
    while lines and not lines[0].strip():
        lines.pop(0)

    return '\n'.join(lines).strip()


def maybe_strip_leading_h1(content: str, title: str) -> tuple[str, bool]:
    """如果正文第一行是与标题重复的 H1，去掉它，返回 (新内容, 是否去掉了)。"""
    lines = content.splitlines()
    if not lines:
        return content, False
    first = lines[0]
    if first.startswith('# '):
        h1_text = first[2:].strip()
        if h1_text == title:
            new_content = '\n'.join(lines[1:]).lstrip('\n')
            return new_content, True
    return content, False


# ── Slug 生成 ──────────────────────────────────────────────────────────────

def to_kebab(s: str) -> str:
    """把字符串转为 kebab-case（中文字符保留）。"""
    s = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', s)
    s = re.sub(r'[\s_]+', '-', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-').lower()


# ── Frontmatter 构建 ───────────────────────────────────────────────────────

def build_frontmatter(*, title, date_str, slug, tags_raw, categories_raw, draft) -> str:
    def yaml_str(s):
        # 如含特殊字符则用双引号包裹
        return f'"{s}"'

    def yaml_str_list(raw: str) -> str:
        items = [t.strip() for t in raw.split(',') if t.strip()]
        return '[' + ', '.join(yaml_str(i) for i in items) + ']'

    lines = ['---']
    lines.append(f'title: {yaml_str(title)}')
    lines.append(f'date: {date_str}')
    if slug:
        lines.append(f'slug: {yaml_str(slug)}')
    lines.append(f'tags: {yaml_str_list(tags_raw) if tags_raw else "[]"}')
    lines.append(f'categories: {yaml_str_list(categories_raw) if categories_raw else "[]"}')
    lines.append(f'draft: {str(draft).lower()}')
    lines.append('---')
    return '\n'.join(lines)


# ── 输出文件名 ─────────────────────────────────────────────────────────────

def next_output_path(dest_dir: Path) -> Path:
    """在目标目录里找下一个可用的数字编号文件名。"""
    dest_dir.mkdir(parents=True, exist_ok=True)
    existing_nums = [
        int(f.stem) for f in dest_dir.glob('[0-9]*.md') if f.stem.isdigit()
    ]
    next_num = (max(existing_nums) + 1) if existing_nums else 1
    return dest_dir / f"{next_num:03d}.md"


# ── 交互 helpers ───────────────────────────────────────────────────────────

def ask(prompt: str, default: str = '') -> str:
    hint = f' [{default}]' if default else ''
    val = input(f'{prompt}{hint}: ').strip()
    return val if val else default


def choose_collection() -> str:
    print('\n目标 collection：')
    for i, (col, label) in enumerate(COLLECTIONS, 1):
        print(f'  {i}) {label}  ({col})')
    while True:
        choice = input('选择 [1-4]: ').strip()
        if choice.isdigit() and 1 <= int(choice) <= len(COLLECTIONS):
            return COLLECTIONS[int(choice) - 1][0]
        print('请输入 1 到 4 之间的数字')


# ── Git ────────────────────────────────────────────────────────────────────

def git_push(file_path: Path, commit_msg: str):
    try:
        subprocess.run(['git', 'add', str(file_path)], cwd=BLOG_ROOT, check=True)
        subprocess.run(['git', 'commit', '-m', commit_msg], cwd=BLOG_ROOT, check=True)
        result = subprocess.run(['git', 'push'], cwd=BLOG_ROOT, check=True)
        print('✓ git push 完成')
    except subprocess.CalledProcessError as e:
        print(f'✗ git 操作失败：{e}')


# ── 主流程 ─────────────────────────────────────────────────────────────────

def main():
    # 1. 获取源文件
    if len(sys.argv) >= 2:
        src_path_str = sys.argv[1]
    else:
        src_path_str = input('Notion 导出文件路径：').strip().strip('"\'')

    src = Path(src_path_str).expanduser().resolve()
    if not src.exists():
        print(f'✗ 文件不存在：{src}')
        sys.exit(1)

    # 2. 从文件名提取标题
    raw_title = strip_notion_hash(src.stem)
    print(f'\n检测到标题：{raw_title}')
    title = ask('标题（回车确认）', raw_title)

    # 3. 读取并清理内容
    text = src.read_text(encoding='utf-8')
    content = clean_notion_content(text)

    # 去掉与标题重复的首行 H1
    content, stripped_h1 = maybe_strip_leading_h1(content, title)
    if stripped_h1:
        print('已自动去除正文开头的重复 H1 标题行')

    # 4. 日期
    today = date.today().isoformat()
    date_str = ask(f'日期', today)

    # 5. 其他 frontmatter 字段
    tags_raw      = ask('标签（逗号分隔，留空跳过）')
    categories_raw = ask('分类（逗号分隔，如 fanfiction,Chulu,大雨将至，留空跳过）')

    # 6. Slug
    slug_default = to_kebab(raw_title)[:60]
    slug = ask('slug（留空使用自动生成）', slug_default)

    # 7. Draft
    draft_ans = ask('设为草稿？(y/n)', 'n').lower()
    draft = draft_ans == 'y'

    # 8. Collection
    collection = choose_collection()

    # 9. 写文件
    dest_dir  = CONTENT_ROOT / collection
    out_path  = next_output_path(dest_dir)
    fm        = build_frontmatter(
        title=title,
        date_str=date_str,
        slug=slug,
        tags_raw=tags_raw,
        categories_raw=categories_raw,
        draft=draft,
    )
    out_path.write_text(fm + '\n\n' + content + '\n', encoding='utf-8')
    print(f'\n✓ 已写入：{out_path.relative_to(BLOG_ROOT)}')

    # 10. Git push
    do_push = ask('\ngit push？(y/n)', 'y').lower()
    if do_push == 'y':
        default_msg = f'feat: add {title}'
        commit_msg = ask('commit 信息', default_msg)
        git_push(out_path, commit_msg)

    print('\n完成！')


if __name__ == '__main__':
    main()
