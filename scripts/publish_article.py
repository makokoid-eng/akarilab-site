#!/usr/bin/env python3
"""publish_article.py

text-generator が作った Markdown 本文 + nano-banana-image が作ったアイキャッチを、
akarilab.org/articles/ 配下に 1 記事 HTML として公開するスクリプト。

スキル: ~/.claude/skills/akarilab-article-publisher/SKILL.md

最小実装範囲（2026-05-21 雑記 10 本一括公開で必要な機能）：
- 雑記カテゴリ（`articles/{YYYY}/{MM}/{slug}/index.html`）
- Markdown -> HTML 変換（h1/h2/h3/p/ul/ol/li/blockquote/a/img/hr）
- cover-image を `img/` にコピー、alt=記事タイトル
- articles/index.html の ItemList と HTML 一覧に 1 エントリ追加
- sitemap.xml と llms.txt に追記
- build_pages.py の TARGETS に追記
- `<strong>` `<em>` 混入時の警告（feedback_akarilab_no_bold_marker §2）

冪等性は build_pages.py 側に任せる。本スクリプトは「未掲載なら追加、既存なら警告のみ」。
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_INDEX = REPO_ROOT / "articles" / "index.html"
SITEMAP = REPO_ROOT / "sitemap.xml"
LLMS = REPO_ROOT / "llms.txt"
BUILD_PAGES = REPO_ROOT / "scripts" / "build_pages.py"

# slug 生成で除去する記号
SLUG_REMOVE_CHARS = "、。「」『』！？・,!?〜～「」　 \"'()（）【】［］[]{}<>「」｜|/\\:;.…―—-_"

SITE_BASE = "https://akarilab.org"


# ---------------- slug ----------------

def slugify(title: str) -> str:
    """記号除去 + 40字切り詰めで slug を生成。"""
    s = title
    for ch in SLUG_REMOVE_CHARS:
        s = s.replace(ch, "")
    s = s.strip()
    return s[:40]


def resolve_slug(title: str, year: str, month: str, override: str | None, suffix: str | None) -> str:
    base = override or slugify(title)
    if suffix:
        base = f"{base}{suffix}"
    target_dir = REPO_ROOT / "articles" / year / month
    candidate = base
    n = 2
    while (target_dir / candidate / "index.html").exists():
        candidate = f"{base}-{n}"
        n += 1
    return candidate


# ---------------- Markdown -> HTML ----------------

INLINE_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
INLINE_BOLD = re.compile(r"\*\*([^*]+)\*\*")
INLINE_EM = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")


def render_inline(text: str, warnings: list[str]) -> str:
    """インライン要素のレンダリング。strong/em は警告のみ。"""
    if INLINE_BOLD.search(text):
        warnings.append("**bold** marker detected (akarilab-writing-style §2 違反)")
    if INLINE_EM.search(text):
        warnings.append("*em* marker detected")
    # 太字・斜体は警告だけ出して、マーカー自体は本文から外す（strong に変換しない）
    text = INLINE_BOLD.sub(r"\1", text)
    text = INLINE_EM.sub(r"\1", text)
    # リンク
    text = INLINE_LINK.sub(r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    return text


def md_to_html(md: str, title: str) -> tuple[str, list[str]]:
    """Markdown を HTML に変換。返り値: (html, warnings)

    対応: # h1 (本文側では出さない、title は引数で別途差す)
          ## h2, ### h3, --- hr, p, ul/ol, blockquote
    """
    warnings: list[str] = []
    lines = md.replace("\r\n", "\n").split("\n")
    html_parts: list[str] = []
    para_buf: list[str] = []
    list_buf: list[str] = []
    list_type: str | None = None  # "ul" or "ol"
    in_blockquote = False
    bq_buf: list[str] = []

    def flush_para() -> None:
        nonlocal para_buf
        if para_buf:
            joined = " ".join(para_buf).strip()
            if joined:
                html_parts.append(f"<p>{render_inline(joined, warnings)}</p>")
            para_buf = []

    def flush_list() -> None:
        nonlocal list_buf, list_type
        if list_buf and list_type:
            html_parts.append(f"<{list_type}>")
            for item in list_buf:
                html_parts.append(f"<li>{render_inline(item, warnings)}</li>")
            html_parts.append(f"</{list_type}>")
            list_buf = []
            list_type = None

    def flush_blockquote() -> None:
        nonlocal bq_buf, in_blockquote
        if bq_buf:
            inner = " ".join(bq_buf).strip()
            html_parts.append(f"<blockquote><p>{render_inline(inner, warnings)}</p></blockquote>")
            bq_buf = []
        in_blockquote = False

    def flush_all() -> None:
        flush_para()
        flush_list()
        flush_blockquote()

    skipped_h1 = False
    for raw in lines:
        line = raw.rstrip()

        # H1 はタイトルとして外で扱う。本文 1 回だけスキップ
        if not skipped_h1 and line.startswith("# ") and not line.startswith("## "):
            skipped_h1 = True
            continue

        if not line.strip():
            flush_all()
            continue

        if line.startswith("## ") and not line.startswith("### "):
            flush_all()
            html_parts.append(f"<h2>{render_inline(line[3:].strip(), warnings)}</h2>")
            continue
        if line.startswith("### "):
            flush_all()
            html_parts.append(f"<h3>{render_inline(line[4:].strip(), warnings)}</h3>")
            continue
        if line.strip() in ("---", "***", "___"):
            flush_all()
            html_parts.append("<hr>")
            continue
        m = re.match(r"^[-*]\s+(.+)$", line)
        if m:
            if list_type and list_type != "ul":
                flush_list()
            list_type = "ul"
            flush_para()
            flush_blockquote()
            list_buf.append(m.group(1))
            continue
        m = re.match(r"^\d+\.\s+(.+)$", line)
        if m:
            if list_type and list_type != "ol":
                flush_list()
            list_type = "ol"
            flush_para()
            flush_blockquote()
            list_buf.append(m.group(1))
            continue
        m = re.match(r"^>\s?(.*)$", line)
        if m:
            flush_para()
            flush_list()
            in_blockquote = True
            bq_buf.append(m.group(1))
            continue

        # ハッシュタグ行（行頭 #タグ #タグ ...）は本文末尾の慣例 <p># ...</p> 化
        if re.match(r"^#\S", line) and not line.startswith("# "):
            # 連続するタグ行を 1 つの <p> にまとめる: 既に直前 para_buf がタグ列でなければ flush
            para_buf.append(line)
            continue

        # 通常段落
        if list_buf:
            flush_list()
        if in_blockquote:
            flush_blockquote()
        para_buf.append(line)

    flush_all()
    return "\n".join(html_parts), warnings


# ---------------- HTML テンプレ ----------------

TEMPLATE = '''<!DOCTYPE html>
<html lang="ja">
<head>
<!-- include: assets/partials/head-common.html -->
<!--
  共通 head パーシャル（新規ページ用、Phase 2 以降に使用）
  ページ固有の <title> / <meta name="description"> / og:* / canonical は
  include 外で各ページが個別に書く。
  既存 index.html では Google Fonts は使われていない（system font 指定）ため
  preconnect / Google Fonts は本 partial に含めない。導入時に追記する。
-->
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="generator" content="akarilab-site (build_pages.py)">
<link rel="stylesheet" href="/assets/css/site.css">

<!-- include-end: assets/partials/head-common.html -->
<title>{title} — AkariLab</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{title} — AkariLab">
<meta property="og:description" content="{description}">
<meta property="og:type" content="article">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/logo/hidamari_icon_32.png">
<link rel="apple-touch-icon" sizes="256x256" href="/assets/logo/hidamari_icon_256.png">
<script type="application/ld+json">
{article_jsonld}
</script>
<script type="application/ld+json">
{breadcrumb_jsonld}
</script>
</head>
<body>
<nav class="header"><a href="https://akarilab.org/articles/">← 記事へ</a></nav>

<article class="article-body">
<h1>{title}</h1>
<p class="article-meta">{pubdate}{note_meta}</p>

<figure><img alt="{title_attr}" src="img/{cover_filename}"><figcaption></figcaption></figure>
{body_html}

</article>

<!-- include: assets/partials/footer-common.html -->
<!--
  共通 footer パーシャル（新規ページ用、Phase 2 以降に使用）

  方針（CODEX コードレビュー指摘2点目反映）:
    AkariLab サイト全体で使える中立フッター。ブランド横断リンク（個別プロダクト LP への可視リンク）は
    含めない。各プロダクト LP（Phase 4 の moyalog/repimemo/hidamari 等）は必要に応じて専用フッターを
    別途用意する。これによりブランド分離ルール（feedback_brand_isolation_moyalog_repimemo）に
    抵触しない。
-->
<footer>
  <div class="links">
    <a href="https://www.instagram.com/akarilab_jp/">Instagram</a>
    <a href="https://note.com/akarilab">note</a>
  </div>
  <div class="links" style="margin-bottom: 8px;">
    <a href="/terms-of-service.html">利用規約</a>
    <a href="/privacy-policy.html">プライバシーポリシー</a>
    <a href="/billing-policy.html">課金・解約ポリシー</a>
    <a href="/tokushoho.html">特定商取引法に基づく表記</a>
  </div>
  <p>&copy; 2026 AkariLab</p>
</footer>

<!-- include-end: assets/partials/footer-common.html -->
</body>
</html>
'''


def make_description(body_md: str) -> str:
    """本文先頭から description 用 120 字を抽出。"""
    text = body_md
    text = re.sub(r"^#.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^##.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[#>\-\*\d\.]+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 120:
        text = text[:120] + "…"
    return text


def build_article_jsonld(title: str, canonical: str, pubdate: str, description: str, note_url: str | None, key: str | None) -> str:
    same_as = []
    if note_url:
        same_as.append(note_url)
    elif key:
        same_as.append(f"https://note.com/akarilab/n/{key}")
    same_as_str = ", ".join(f'"{u}"' for u in same_as)
    return (
        '{\n'
        '  "@context": "https://schema.org",\n'
        '  "@type": "Article",\n'
        f'  "@id": "{canonical}#article",\n'
        f'  "headline": "{escape_json(title)}",\n'
        f'  "datePublished": "{pubdate}T09:00:00+09:00",\n'
        '  "author": { "@id": "https://akarilab.org/#org" },\n'
        '  "publisher": { "@id": "https://akarilab.org/#org" },\n'
        f'  "mainEntityOfPage": "{canonical}",\n'
        f'  "sameAs": [{same_as_str}],\n'
        f'  "abstract": "{escape_json(description)}"\n'
        '}'
    )


def build_breadcrumb_jsonld(title: str, canonical: str) -> str:
    return (
        '{\n'
        '  "@context": "https://schema.org",\n'
        '  "@type": "BreadcrumbList",\n'
        '  "itemListElement": [\n'
        '    { "@type": "ListItem", "position": 1, "name": "ホーム", "item": "https://akarilab.org/" },\n'
        '    { "@type": "ListItem", "position": 2, "name": "記事", "item": "https://akarilab.org/articles/" },\n'
        f'    {{ "@type": "ListItem", "position": 3, "name": "{escape_json(title)}", "item": "{canonical}" }}\n'
        '  ]\n'
        '}'
    )


def escape_json(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


# ---------------- ハブ更新 ----------------

ITEMLIST_RE = re.compile(
    r'(\{ "@type": "ListItem", "position": (\d+), "name": "[^"]+", "url": "[^"]+" \})'
)


def update_articles_index(title: str, url_path: str, pubdate: str, year_month: str) -> None:
    content = ARTICLES_INDEX.read_text(encoding="utf-8")

    # 1) ItemList position の最大値を求めて position+1 で末尾追加
    positions = [int(m.group(2)) for m in ITEMLIST_RE.finditer(content)]
    next_pos = (max(positions) + 1) if positions else 1
    new_item = (
        f'    {{ "@type": "ListItem", "position": {next_pos}, '
        f'"name": "{escape_json(title)}", "url": "https://akarilab.org{url_path}" }}'
    )
    # 末尾 `]` の手前に新規エントリを挿入する。最後の ListItem 行の直後にカンマ + 改行 + 新行
    # 最後にマッチした ListItem 行末尾を見つけて、その後ろに ", \n{new_item}" を入れる
    matches = list(ITEMLIST_RE.finditer(content))
    if not matches:
        raise RuntimeError("ItemList entry not found in articles/index.html")
    last = matches[-1]
    insert_pos = last.end()
    content = content[:insert_pos] + ",\n" + new_item + content[insert_pos:]

    # 2) HTML 一覧（<h3 class="section-subtitle">{年月}</h3> 直後の <ul> 先頭）に <li> 追加
    h3_marker = f'<h3 class="section-subtitle">{year_month}</h3>'
    if h3_marker not in content:
        # 該当月セクションがない -> 「単発記事」セクション内の最初の <h3 ...> の直前に新設
        section_anchor = '<h2 class="section-title">単発記事</h2>'
        if section_anchor not in content:
            raise RuntimeError("単発記事 section not found in articles/index.html")
        new_block = (
            f'  <h3 class="section-subtitle">{year_month}</h3>\n'
            f'  <ul>\n'
            f'    <li><a href="{url_path}">{title}</a> — {pubdate}</li>\n'
            f'  </ul>\n'
        )
        # section 直後（次の </section> ではなく <h3 既存があればその上に）
        idx = content.find(section_anchor) + len(section_anchor)
        content = content[:idx] + "\n" + new_block + content[idx:]
    else:
        # 既存月セクションの <ul> 先頭に追加
        idx = content.find(h3_marker)
        ul_start = content.find("<ul>", idx)
        if ul_start == -1:
            raise RuntimeError(f"<ul> not found after {h3_marker}")
        ul_open_end = ul_start + len("<ul>")
        new_li = f'\n    <li><a href="{url_path}">{title}</a> — {pubdate}</li>'
        content = content[:ul_open_end] + new_li + content[ul_open_end:]

    ARTICLES_INDEX.write_text(content, encoding="utf-8")


def update_sitemap(url_path: str, pubdate: str) -> None:
    content = SITEMAP.read_text(encoding="utf-8")
    encoded = urllib.parse.quote(url_path, safe="/:-._~")
    loc = f"{SITE_BASE}{encoded}"
    if loc in content:
        return  # 既存
    block = (
        f'  <url>\n'
        f'    <loc>{loc}</loc>\n'
        f'    <lastmod>{pubdate}</lastmod>\n'
        f'    <changefreq>monthly</changefreq>\n'
        f'    <priority>0.6</priority>\n'
        f'  </url>\n'
    )
    content = content.replace("</urlset>", block + "</urlset>")
    SITEMAP.write_text(content, encoding="utf-8")


def update_llms(url_path: str, title: str, year_month: str) -> None:
    content = LLMS.read_text(encoding="utf-8")
    new_line = f"- {url_path}   {title}"
    if new_line in content:
        return
    header = f"### 単発記事（{year_month}）"
    if header in content:
        # ヘッダの直後（次の空行までのリスト末尾）に追加
        idx = content.find(header)
        # ヘッダ直下の最初のリストブロック末尾を探す
        section_start = idx + len(header)
        # 次のヘッダ or ファイル末尾までの間で、最後の "- " 行を見つけて、その後ろに追加
        rest = content[section_start:]
        next_header = re.search(r"\n### |\n## |\n# ", rest)
        end_offset = section_start + (next_header.start() if next_header else len(rest))
        section = content[section_start:end_offset]
        # section 内の最後の "- " 行を見つける
        lines = section.split("\n")
        last_dash_idx = -1
        for i, ln in enumerate(lines):
            if ln.startswith("- "):
                last_dash_idx = i
        if last_dash_idx >= 0:
            lines.insert(last_dash_idx + 1, new_line)
            new_section = "\n".join(lines)
            content = content[:section_start] + new_section + content[end_offset:]
        else:
            # リスト無し -> ヘッダ直後に挿入
            content = content[:section_start] + "\n" + new_line + "\n" + content[section_start:]
    else:
        # ヘッダ自体を新設（「### 単発記事（YYYY-MM）」を最初の「### 単発記事（」ブロックの直前に）
        m = re.search(r"### 単発記事（", content)
        if m:
            insert_pos = m.start()
            block = f"### 単発記事（{year_month}）\n{new_line}\n\n"
            content = content[:insert_pos] + block + content[insert_pos:]
        else:
            # 末尾追加
            content = content.rstrip() + f"\n\n### 単発記事（{year_month}）\n{new_line}\n"
    LLMS.write_text(content, encoding="utf-8")


def update_build_pages_targets(rel_path: str) -> None:
    content = BUILD_PAGES.read_text(encoding="utf-8")
    quoted = f'    "{rel_path}",'
    if quoted in content:
        return
    # 最後の "articles/2026/..." 行の直後に追加（雑記グループ末尾）
    lines = content.split("\n")
    last_articles_idx = -1
    for i, ln in enumerate(lines):
        if ln.startswith('    "articles/2026/'):
            last_articles_idx = i
    if last_articles_idx < 0:
        # フォールバック: TARGETS 配列末尾 `]` 直前
        end_idx = -1
        for i, ln in enumerate(lines):
            if ln.startswith("]") and end_idx == -1 and i > 0:
                end_idx = i
        if end_idx < 0:
            raise RuntimeError("could not locate TARGETS list end in build_pages.py")
        lines.insert(end_idx, quoted)
    else:
        lines.insert(last_articles_idx + 1, quoted)
    BUILD_PAGES.write_text("\n".join(lines), encoding="utf-8")


# ---------------- メイン ----------------

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--markdown", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--category", required=True, choices=["misc", "series"])
    parser.add_argument("--pubdate", required=True, help="YYYY-MM-DD")
    parser.add_argument("--cover-image", required=True)
    parser.add_argument("--note-url", default=None, help="完成 note URL（n/xxx 形式）。省略可")
    parser.add_argument("--note-key", default=None, help="note 編集 key（未公開時の推測 URL 用）")
    parser.add_argument("--description", default=None)
    parser.add_argument("--slug", default=None)
    parser.add_argument("--slug-suffix", default=None, help="衝突回避用のサフィックス。例: -01")
    args = parser.parse_args(argv)

    md_path = Path(args.markdown)
    img_path = Path(args.cover_image)
    if not md_path.is_file():
        print(f"ERROR: markdown not found: {md_path}", file=sys.stderr)
        return 2
    if not img_path.is_file():
        print(f"ERROR: cover image not found: {img_path}", file=sys.stderr)
        return 2

    try:
        date = datetime.strptime(args.pubdate, "%Y-%m-%d")
    except ValueError:
        print(f"ERROR: invalid pubdate: {args.pubdate}", file=sys.stderr)
        return 2

    if args.category != "misc":
        print("ERROR: only --category misc is implemented in this script run", file=sys.stderr)
        return 2

    year = f"{date.year:04d}"
    month = f"{date.month:02d}"
    year_month = f"{year}-{month}"

    slug = resolve_slug(args.title, year, month, args.slug, args.slug_suffix)
    rel_dir = f"articles/{year}/{month}/{slug}"
    out_dir = REPO_ROOT / rel_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "img").mkdir(parents=True, exist_ok=True)

    # Markdown 読み込み + 変換
    md = md_path.read_text(encoding="utf-8")
    body_html, warnings = md_to_html(md, args.title)
    if warnings:
        for w in warnings:
            print(f"WARN [{slug}]: {w}", file=sys.stderr)

    # description
    description = args.description or make_description(md)

    # 画像コピー
    cover_filename = img_path.name
    shutil.copy2(img_path, out_dir / "img" / cover_filename)

    # URL / canonical
    url_path = f"/{rel_dir}/"
    canonical = f"{SITE_BASE}{urllib.parse.quote(url_path, safe='/:-._~')}"
    og_image = f"{canonical}img/{urllib.parse.quote(cover_filename, safe='/:-._~')}"

    note_meta = ""
    if args.note_url:
        note_meta = f' · <a href="{args.note_url}" target="_blank" rel="noopener">note 掲載版</a>'
    elif args.note_key:
        note_url_guess = f"https://note.com/akarilab/n/{args.note_key}"
        note_meta = f' · <a href="{note_url_guess}" target="_blank" rel="noopener">note 掲載版</a>'

    article_jsonld = build_article_jsonld(
        args.title, canonical, args.pubdate, description, args.note_url, args.note_key
    )
    breadcrumb_jsonld = build_breadcrumb_jsonld(args.title, canonical)

    html = TEMPLATE.format(
        title=args.title,
        title_attr=args.title.replace('"', '&quot;'),
        description=description.replace('"', '&quot;'),
        canonical=canonical,
        og_image=og_image,
        pubdate=args.pubdate,
        note_meta=note_meta,
        cover_filename=urllib.parse.quote(cover_filename, safe='/:-._~'),
        body_html=body_html,
        article_jsonld=article_jsonld,
        breadcrumb_jsonld=breadcrumb_jsonld,
    )

    (out_dir / "index.html").write_text(html, encoding="utf-8")

    # ハブ・sitemap・llms・build_pages 更新
    update_articles_index(args.title, url_path, args.pubdate, year_month)
    update_sitemap(url_path, args.pubdate)
    update_llms(url_path, args.title, year_month)
    update_build_pages_targets(f"{rel_dir}/index.html")

    print(f"OK: {slug} -> {canonical}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
