#!/usr/bin/env python3
"""build_redirects.py

中継ページ（akarilab.org/r/<slug>/index.html）を data/redirects.yml から自動生成する。
GA4 計測タグは assets/partials/head-common.html を inline 展開して埋め込む。

設計: docs/aiseo/phase_9_redirects_design.md
承認プラン: ~/.claude/plans/cryptic-sniffing-cerf.md

Usage:
    python scripts/build_redirects.py              # 通常モード（上書き保存、冪等）
    python scripts/build_redirects.py --dry-run    # 何が変わるか stdout に出す、ファイルは触らない
    python scripts/build_redirects.py --check      # CI 用、現状と build 結果が一致するか検証

CODEX レビュー反映:
- robots.txt に Disallow: /r/ は入れない（noindex を読めなくなる事故防止）
- ?from= は JS 側で正規表現サニタイズ、不正値は unknown
- GA4 には dest_url を送らない（slug/from/from_valid/channel/dest_domain/category のみ）
- build_pages.py には混ぜず、本スクリプトが head-common.html を inline 展開
- 公開後の slug は immutable（dest_url 変更時は新 slug を切る）
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
REDIRECTS_YML = REPO_ROOT / "data" / "redirects.yml"
HEAD_COMMON = REPO_ROOT / "assets" / "partials" / "head-common.html"
OUT_DIR = REPO_ROOT / "r"

REQUIRED_KEYS = {"slug", "dest_url", "label", "category", "dest_domain", "active"}
ALLOWED_CATEGORIES = {"brain", "coconala", "line_bot", "form"}


def load_redirects() -> list[dict]:
    if not REDIRECTS_YML.is_file():
        raise RuntimeError(f"not found: {REDIRECTS_YML.relative_to(REPO_ROOT)}")
    data = yaml.safe_load(REDIRECTS_YML.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "redirects" not in data:
        raise RuntimeError("redirects.yml must have top-level 'redirects:' key")
    entries = data["redirects"]
    if not isinstance(entries, list):
        raise RuntimeError("'redirects:' must be a list")
    seen_slugs: set[str] = set()
    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            raise RuntimeError(f"entry #{i} is not a mapping")
        missing = REQUIRED_KEYS - set(e.keys())
        if missing:
            raise RuntimeError(f"entry #{i} missing keys: {sorted(missing)}")
        slug = e["slug"]
        if not isinstance(slug, str) or not slug:
            raise RuntimeError(f"entry #{i} has invalid slug")
        if slug in seen_slugs:
            raise RuntimeError(f"duplicate slug: {slug}")
        seen_slugs.add(slug)
        # slug は a-z 0-9 - のみ許可（パス安全性）
        if not all(c.isalnum() or c == "-" for c in slug) or slug != slug.lower():
            raise RuntimeError(
                f"invalid slug '{slug}': use lower-case alphanumerics and hyphens only"
            )
        if e["category"] not in ALLOWED_CATEGORIES:
            raise RuntimeError(
                f"entry '{slug}' has invalid category: {e['category']!r}"
            )
        if not isinstance(e["dest_url"], str) or not e["dest_url"].startswith(
            ("https://", "http://")
        ):
            raise RuntimeError(f"entry '{slug}' has invalid dest_url")
        if not isinstance(e["active"], bool):
            raise RuntimeError(f"entry '{slug}' active must be bool")
    return entries


def load_head_common() -> str:
    if not HEAD_COMMON.is_file():
        raise RuntimeError(f"not found: {HEAD_COMMON.relative_to(REPO_ROOT)}")
    return HEAD_COMMON.read_text(encoding="utf-8").rstrip()


def js_string_literal(s: str) -> str:
    """JS 文字列リテラル内に安全に埋め込む（XSS / </script> 攻撃対策）。

    json.dumps は </ を \\u003c\\u002f にエスケープしないので追加処理する。
    """
    quoted = json.dumps(s, ensure_ascii=False)
    return quoted.replace("</", "<\\/")


def render_page(entry: dict, head_common_inlined: str) -> str:
    slug = entry["slug"]
    dest_url = entry["dest_url"]
    label = entry["label"]
    category = entry["category"]
    dest_domain = entry["dest_domain"]

    dest_html = html.escape(dest_url, quote=True)
    label_html = html.escape(label, quote=True)
    dest_js = js_string_literal(dest_url)
    slug_js = js_string_literal(slug)
    dest_domain_js = js_string_literal(dest_domain)
    category_js = js_string_literal(category)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex,nofollow">
<meta name="referrer" content="no-referrer-when-downgrade">
<title>移動中… — AkariLab</title>
<meta http-equiv="refresh" content="2;url={dest_html}">
<!-- head-common.html (inlined by scripts/build_redirects.py) -->
{head_common_inlined}
<!-- /head-common.html -->
<script>
(function() {{
  var FROM_RE = /^[a-z0-9][a-z0-9_-]{{0,80}}$/;
  var CH_WHITELIST = ['note','cocon','akari','x','other'];
  var qs = new URLSearchParams(window.location.search);
  var rawFrom = qs.get('from') || '';
  var rawCh = qs.get('ch') || '';
  var fromValid = FROM_RE.test(rawFrom);
  var from = fromValid ? rawFrom : 'unknown';
  var channel = CH_WHITELIST.indexOf(rawCh) >= 0 ? rawCh : 'unknown';
  var dest = {dest_js};
  var sent = false;
  function go() {{ if (sent) return; sent = true; window.location.replace(dest); }}
  setTimeout(go, 500);
  if (typeof gtag === 'function') {{
    gtag('event', 'redirect_click', {{
      slug: {slug_js},
      from: from,
      from_valid: fromValid,
      channel: channel,
      dest_domain: {dest_domain_js},
      category: {category_js},
      transport_type: 'beacon',
      event_callback: go
    }});
  }} else {{ go(); }}
}})();
</script>
</head>
<body>
<main style="font-family:sans-serif;padding:40px;text-align:center;">
  <p>移動中です…</p>
  <noscript><p>自動で移動しない場合は、<a href="{dest_html}" rel="nofollow noopener">こちらをクリック</a>してください。</p></noscript>
  <p style="color:#888;font-size:12px;margin-top:40px;">リンク先: {label_html}</p>
</main>
</body>
</html>
"""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    try:
        entries = load_redirects()
        head_common = load_head_common()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    changed: list[Path] = []
    skipped_inactive: list[str] = []
    for entry in entries:
        if not entry["active"]:
            skipped_inactive.append(entry["slug"])
            continue
        out_path = OUT_DIR / entry["slug"] / "index.html"
        rendered = render_page(entry, head_common)
        if out_path.is_file():
            current = out_path.read_text(encoding="utf-8")
            if current == rendered:
                continue
        changed.append(out_path)
        if not args.dry_run and not args.check:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(rendered, encoding="utf-8")

    def rel(p: Path) -> str:
        return str(p.relative_to(REPO_ROOT)).replace("\\", "/")

    if args.check:
        if changed:
            print(f"check FAILED: {len(changed)} files would change")
            for path in changed:
                print(f"  {rel(path)}")
            return 1
        print(f"check OK: {len(entries) - len(skipped_inactive)} active redirects, no changes")
        return 0

    if args.dry_run:
        print(f"dry-run: {len(changed)} files would change")
        for path in changed:
            print(f"  {rel(path)}")
        if skipped_inactive:
            print(f"skipped inactive: {', '.join(skipped_inactive)}")
        return 0

    print(f"build: {len(changed)} files updated")
    for path in changed:
        print(f"  {rel(path)}")
    if skipped_inactive:
        print(f"skipped inactive: {', '.join(skipped_inactive)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
