#!/usr/bin/env python3
"""sync_note_articles.py

note 投稿の URL リストを取得して `data/articles.yml` を更新するスクリプト。

二経路（Phase 5 設計 R1 リスク対策）：
- 経路 A：note-poster の出力 `note_post_success_{date}.json` を走査
- 経路 B：note.com/akarilab の RSS（/rss）を取得して fallback

経路 A が落ちても経路 B で復旧可能。両者の重複は二重起票防止ロジックで除外。

設計：C:/Users/user/akarilab-site/docs/aiseo/phase_5_design.md

Usage:
    python scripts/sync_note_articles.py            # 通常実行（articles.yml 更新）
    python scripts/sync_note_articles.py --dry-run  # 何が変わるか stdout 出力、ファイル不変
    python scripts/sync_note_articles.py --no-rss   # 経路 B（RSS）skip、経路 A のみ
    python scripts/sync_note_articles.py --no-log   # 経路 A（note-poster ログ）skip、経路 B のみ

依存：
- Python 3.10+
- pyyaml（必須）
- requests（経路 B で使用、--no-rss 時は import を遅延し未インストールでも可）
"""
from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_YML = REPO_ROOT / "data" / "articles.yml"

# note-poster の投稿成功ログ置き場（akarilab-note リポ側）
NOTE_POSTER_LOG_DIR = Path("C:/Users/user/akarilab-note/data")
NOTE_POSTER_LOG_GLOB = "note_post_success_*.json"

# note RSS（経路 B）
NOTE_RSS_URL = "https://note.com/akarilab/rss"
RSS_TIMEOUT_SEC = 10

# プレースホルダー判定（この文字列を含む note_url は未確定 slot として扱う）
PLACEHOLDER_MARKER = "PLACEHOLDER"


def load_articles_yml() -> dict[str, Any]:
    """articles.yml を読み込む。存在しない・パース失敗で exit 2。"""
    if not ARTICLES_YML.is_file():
        print(f"ERROR: articles.yml not found at {ARTICLES_YML}", file=sys.stderr)
        sys.exit(2)
    try:
        with ARTICLES_YML.open(encoding="utf-8") as fp:
            data = yaml.safe_load(fp)
    except yaml.YAMLError as exc:
        print(f"ERROR: yaml parse failed: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, dict) or "series" not in data:
        print("ERROR: articles.yml must have top-level 'series' key", file=sys.stderr)
        sys.exit(2)
    return data


def is_placeholder(note_url: str | None) -> bool:
    """note_url が未確定（プレースホルダー）かどうか。"""
    if not note_url:
        return True
    return PLACEHOLDER_MARKER in note_url


def collect_note_poster_logs() -> list[dict[str, Any]]:
    """経路 A：note-poster の投稿成功ログを走査。

    各 JSON は最低限 {slug, note_url, published, summary, title} を持つ想定。
    キー欠落は warning で skip、致命エラーにはしない。
    """
    if not NOTE_POSTER_LOG_DIR.is_dir():
        print(
            f"WARN: note-poster log dir not found, skipping route A: {NOTE_POSTER_LOG_DIR}",
            file=sys.stderr,
        )
        return []
    records: list[dict[str, Any]] = []
    for log_path in sorted(NOTE_POSTER_LOG_DIR.glob(NOTE_POSTER_LOG_GLOB)):
        try:
            with log_path.open(encoding="utf-8") as fp:
                payload = json.load(fp)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"WARN: failed to read {log_path.name}: {exc}", file=sys.stderr)
            continue
        # 単一記事 or 複数記事リスト両対応
        if isinstance(payload, list):
            records.extend(p for p in payload if isinstance(p, dict))
        elif isinstance(payload, dict):
            records.append(payload)
        else:
            print(f"WARN: unexpected JSON shape in {log_path.name}, skipping", file=sys.stderr)
    return records


def fetch_rss_entries() -> list[dict[str, str]]:
    """経路 B：note RSS を取得して title / link / pubDate / description を抽出。

    取得失敗は warning で空リストを返す（致命エラーにしない）。
    """
    try:
        import requests  # 遅延 import（--no-rss なら不要）
    except ImportError:
        print(
            "WARN: requests not installed, skipping route B (RSS). Install: pip install requests",
            file=sys.stderr,
        )
        return []
    try:
        resp = requests.get(
            NOTE_RSS_URL,
            timeout=RSS_TIMEOUT_SEC,
            headers={"User-Agent": "akarilab-site-sync/1.0 (+https://akarilab.org/articles/)"},
        )
    except requests.RequestException as exc:
        print(f"WARN: RSS fetch failed: {exc}", file=sys.stderr)
        return []
    if resp.status_code != 200:
        print(f"WARN: RSS returned HTTP {resp.status_code}, skipping route B", file=sys.stderr)
        return []
    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError as exc:
        print(f"WARN: RSS parse failed: {exc}", file=sys.stderr)
        return []
    entries: list[dict[str, str]] = []
    # RSS 2.0：channel/item
    for item in root.iter("item"):
        entry = {
            "title": (item.findtext("title") or "").strip(),
            "link": (item.findtext("link") or "").strip(),
            "pubDate": (item.findtext("pubDate") or "").strip(),
            "description": (item.findtext("description") or "").strip(),
        }
        if entry["link"]:
            entries.append(entry)
    return entries


def parse_rss_pubdate(pubdate: str) -> str | None:
    """RFC 822 形式（RSS）→ ISO-8601 (YYYY-MM-DD) 変換。失敗で None。"""
    if not pubdate:
        return None
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            return datetime.strptime(pubdate, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def apply_route_a(
    series_data: dict[str, Any],
    log_records: list[dict[str, Any]],
) -> list[str]:
    """経路 A：note-poster ログから articles.yml を更新。変更内容のメッセージリストを返す。

    マッチング戦略：
    - log の slug が articles.yml の slot.slug と一致 → 上書き（プレースホルダーでなくても上書き）
    - log の note_url が articles.yml の slot.note_url と一致 → no-op（既に同期済み）
    """
    changes: list[str] = []
    for series_slug, series in series_data.items():
        articles = series.get("articles", []) or []
        for slot in articles:
            slot_slug = slot.get("slug")
            if not slot_slug:
                continue
            for rec in log_records:
                if rec.get("slug") != slot_slug:
                    continue
                # slug マッチ：URL / published / summary / title を確定
                old_url = slot.get("note_url", "")
                new_url = rec.get("note_url", old_url)
                if old_url != new_url and new_url:
                    changes.append(
                        f"[A] {series_slug}/{slot_slug}: note_url {old_url!r} -> {new_url!r}"
                    )
                    slot["note_url"] = new_url
                for key in ("published", "summary", "title"):
                    new_val = rec.get(key)
                    if new_val and slot.get(key) != new_val:
                        old_val = slot.get(key, "")
                        changes.append(
                            f"[A] {series_slug}/{slot_slug}: {key} updated"
                            f" ({len(str(old_val))} -> {len(str(new_val))} chars)"
                        )
                        slot[key] = new_val
                break
    return changes


def apply_route_b(
    series_data: dict[str, Any],
    rss_entries: list[dict[str, str]],
) -> list[str]:
    """経路 B：RSS で未確定 slot を埋める。確定済みは上書きしない（二重起票防止）。

    マッチング戦略：
    - slot.note_url がプレースホルダーで、かつ slot.match_title が
      RSS の title に部分一致するエントリ → 反映
    """
    changes: list[str] = []
    for series_slug, series in series_data.items():
        articles = series.get("articles", []) or []
        for slot in articles:
            if not is_placeholder(slot.get("note_url")):
                continue  # 既に確定済みなら経路 B では触らない
            match_title = (slot.get("match_title") or slot.get("title") or "").strip()
            if not match_title:
                continue
            for entry in rss_entries:
                if match_title and match_title in entry["title"]:
                    new_url = entry["link"]
                    new_published = parse_rss_pubdate(entry["pubDate"]) or slot.get("published")
                    changes.append(
                        f"[B] {series_slug}/{slot.get('slug')}: matched RSS"
                        f" title={entry['title']!r} -> note_url={new_url}"
                    )
                    slot["note_url"] = new_url
                    if new_published:
                        slot["published"] = new_published
                    if entry["title"] and entry["title"] != slot.get("title"):
                        slot["title"] = entry["title"]
                    # CODEX 指摘: RSS description を summary に反映（要約ハブとして機能させるため）
                    rss_desc = entry.get("description", "").strip()
                    if rss_desc:
                        # HTML タグを簡易除去（lxml/bs4 を新規依存にしないため正規表現で）
                        plain = re.sub(r"<[^>]+>", "", rss_desc).strip()
                        if plain and (is_placeholder_summary(slot.get("summary", "")) or len(plain) > len(slot.get("summary", ""))):
                            slot["summary"] = plain[:500]
                            changes.append(
                                f"[B] {series_slug}/{slot.get('slug')}: summary updated from RSS description ({len(plain)} chars)"
                            )
                    break
    return changes


def is_placeholder_summary(text: str) -> bool:
    """summary が「公開予定」「準備中」等の placeholder か判定。"""
    if not text:
        return True
    placeholders = ("公開予定", "準備中", "TBD", "PLACEHOLDER", "（")
    return any(p in text for p in placeholders)


def update_html_placeholders(series_data: dict[str, Any], html_dir: Path) -> list[str]:
    """articles.yml の確定値を articles/<series>/<slug>.html 内の placeholder へ反映。

    CODEX 指摘 1: sync 後に dev-log-01.html の isBasedOn / mainEntityOfPage が
    PLACEHOLDER のまま残らないようにする。

    対象 placeholder：
    - PLACEHOLDER_TBD_AFTER_PUBLISH の文字列を実 note_url に置換
    - JSON-LD の "abstract" 値が placeholder summary 文字列を含む場合は articles.yml の summary に置換

    abstract 置換は HTML 内の JSON-LD ブロック内の `"abstract": "..."` パターンを
    正規表現で慎重に置換（ブロック全体のパースはしない、最小差分）。
    """
    changes: list[str] = []
    for series_slug, series in series_data.items():
        articles = series.get("articles", []) or []
        for slot in articles:
            slot_slug = slot.get("slug")
            if not slot_slug:
                continue
            html_path = html_dir / series_slug / f"{slot_slug}.html"
            if not html_path.is_file():
                continue
            content = html_path.read_text(encoding="utf-8")
            new_content = content

            new_url = (slot.get("note_url") or "").strip()
            if new_url and not is_placeholder(new_url):
                if "PLACEHOLDER_TBD_AFTER_PUBLISH" in new_content:
                    new_content = new_content.replace(
                        "https://note.com/akarilab/n/PLACEHOLDER_TBD_AFTER_PUBLISH",
                        new_url,
                    )
                    new_content = new_content.replace(
                        "PLACEHOLDER_TBD_AFTER_PUBLISH",
                        new_url.split("/")[-1] if "/" in new_url else new_url,
                    )
                    changes.append(f"[HTML] {html_path.name}: PLACEHOLDER URL -> {new_url}")

            new_summary = (slot.get("summary") or "").strip()
            if new_summary and not is_placeholder_summary(new_summary):
                # JSON-LD 内の "abstract": "..." を置換（最小差分、シングル/マルチライン両対応）
                pattern = re.compile(r'("abstract"\s*:\s*")([^"\\]*(?:\\.[^"\\]*)*)(")', re.DOTALL)
                m = pattern.search(new_content)
                if m and (is_placeholder_summary(m.group(2)) or len(m.group(2)) < len(new_summary) // 2):
                    escaped = new_summary.replace("\\", "\\\\").replace('"', '\\"')
                    new_content = pattern.sub(rf'\g<1>{escaped}\g<3>', new_content, count=1)
                    changes.append(f"[HTML] {html_path.name}: abstract -> {len(new_summary)} chars")

            if new_content != content:
                html_path.write_text(new_content, encoding="utf-8")
    return changes


def write_articles_yml(data: dict[str, Any]) -> None:
    """articles.yml に書き戻す。先頭コメントは保持できないため、
    ヘッダコメントを再付与する（ファイル先頭に必ず付ける運用ルール）。"""
    header = (
        "# articles.yml — note 記事メタの単一情報源\n"
        "#\n"
        "# 自動更新：scripts/sync_note_articles.py が経路 A / 経路 B で上書き。\n"
        "# 構造とフィールドの意味は docs/aiseo/phase_5_design.md を参照。\n"
        "\n"
    )
    body = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, indent=2)
    ARTICLES_YML.write_text(header + body, encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="変更内容を stdout に出力、articles.yml は触らない",
    )
    parser.add_argument(
        "--no-rss",
        action="store_true",
        help="経路 B（RSS fallback）を skip",
    )
    parser.add_argument(
        "--no-log",
        action="store_true",
        help="経路 A（note-poster ログ）を skip",
    )
    args = parser.parse_args(argv)

    data = load_articles_yml()
    series_data = data.get("series") or {}
    if not isinstance(series_data, dict):
        print("ERROR: 'series' must be a mapping", file=sys.stderr)
        return 2

    all_changes: list[str] = []

    if args.no_log:
        print("INFO: route A skipped (--no-log)")
    else:
        log_records = collect_note_poster_logs()
        print(f"INFO: route A collected {len(log_records)} note-poster records")
        all_changes.extend(apply_route_a(series_data, log_records))

    if args.no_rss:
        print("INFO: route B skipped (--no-rss)")
    else:
        rss_entries = fetch_rss_entries()
        print(f"INFO: route B fetched {len(rss_entries)} RSS entries")
        all_changes.extend(apply_route_b(series_data, rss_entries))

    if not all_changes:
        print("OK: no changes (articles.yml is up to date)")
        return 0

    print(f"INFO: {len(all_changes)} changes detected")
    for msg in all_changes:
        print(f"  {msg}")

    if args.dry_run:
        print("dry-run: articles.yml not written")
        return 0

    write_articles_yml(data)
    print(f"OK: articles.yml updated ({ARTICLES_YML})")

    # CODEX 指摘 1 反映：articles.yml 更新後、対応 HTML の placeholder URL / abstract も更新
    html_changes = update_html_placeholders(series_data, REPO_ROOT / "articles")
    if html_changes:
        print(f"INFO: {len(html_changes)} HTML placeholders updated")
        for msg in html_changes:
            print(f"  {msg}")
    else:
        print("INFO: no HTML placeholder updates needed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
