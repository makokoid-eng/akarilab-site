#!/usr/bin/env python3
"""
PURPOSE
  akarilab.org の全ページに GA4 タグ（gtag.js）が「ちょうど1つ」入っている状態を CI で守る。

  背景（2026-09-07 の実測）
    GA4 プロパティ akarilab.org はデータを受信していたが、104URL 中 19URL、
    リポジトリ全体では 166 HTML 中 25 HTML にタグが入っていなかった。
    抜けていたのは /kokora/ /hidamari/ /moyalog/ /repimemo/ と
    /makoto/services/** ── つまり「見る → 申し込む」の導線がまるごと未計測だった。
    原因は、assets/partials/head-common.html を include して生成したページには
    タグが入るのに対し、手書きで作ったページには誰も貼らなかったこと。
    人が気をつける話にすると必ずまた抜けるので、CI で止める。

  何を見るか
    1. 計測すべきページに gtag.js が無い        → fail
    2. 同じページに gtag.js が2つ以上ある       → fail（イベントの二重計上になる）
    3. 測定IDが EXPECTED_ID 以外               → fail（別プロパティへの誤送信）
    4. gtag.js が </head> より後ろにある        → fail（読み込み前の離脱を取りこぼす）

  計測しないもの（意図的な除外。増やすときは必ず理由を書くこと）
    assets/partials/**  ページではなく HTML 断片。include 元で1回入ればよい
    owner/**            運用者本人だけが使う内部ポータル。自分の訪問を数えない
    hidamari.html       /hidamari/ へ転送するだけの旧URL。noindex で本文を持たない

  ⚠ /r/** は「リダイレクトするページ」だが、除外してはいけない。
    転送前に redirect_click イベントを送るのが目的のページで、タグが抜けると
    どの外部リンクが押されたかが丸ごと分からなくなる。だから http-equiv="refresh"
    を持つことを理由にした自動スキップは実装しない（一度そうしかけて、
    51 ページの計測が検査対象から外れることに気づいた）。

使い方
  python scripts/check_ga4_tag.py          # 検査（CI 用。異常があれば exit 1）
  python scripts/check_ga4_tag.py --list   # 現状の一覧を出すだけ（exit 0）

出力
  異常があれば1行1件で標準出力に出し、終了コード 1 を返す。
"""
import re
import sys
from pathlib import Path

# akarilab.org の GA4 測定ID。プロパティを変えるときはここだけ直す。
EXPECTED_ID = "G-K6N7W00YYP"

REPO_ROOT = Path(__file__).resolve().parent.parent

# 除外パス（REPO_ROOT からの相対、前方一致）
EXCLUDE_PREFIXES = (
    "assets/partials/",
    "owner/",
    ".git/",
    "node_modules/",
    "docs/",
)

# 除外ファイル（1件ずつ、理由つき）
EXCLUDE_FILES = {
    "hidamari.html": "/hidamari/ へ転送するだけの旧URL。noindex で本文を持たない",
}

GTAG_SRC_RE = re.compile(
    r"""<script[^>]+src=["']https://www\.googletagmanager\.com/gtag/js\?id=([A-Z0-9\-]+)["']""",
    re.I,
)


def is_excluded(rel_path: str) -> bool:
    """検査対象外か。除外理由は EXCLUDE_PREFIXES / EXCLUDE_FILES のコメントを参照。"""
    return rel_path.startswith(EXCLUDE_PREFIXES) or rel_path in EXCLUDE_FILES


def check_file(path: Path):
    """
    1ファイルを検査する。

    引数 : path … 検査する HTML ファイルの絶対パス
    戻り値: (status, ids) のタプル
            status … 'ok' / 'missing' / 'duplicate' / 'wrong_id' / 'after_head'
            ids    … 見つかった測定IDのリスト
    """
    text = path.read_text(encoding="utf-8", errors="replace")

    matches = list(GTAG_SRC_RE.finditer(text))
    ids = [m.group(1) for m in matches]

    if not matches:
        return "missing", []
    if len(matches) > 1:
        return "duplicate", ids
    if ids[0] != EXPECTED_ID:
        return "wrong_id", ids

    head_end = text.lower().find("</head>")
    if head_end != -1 and matches[0].start() > head_end:
        return "after_head", ids

    return "ok", ids


def main() -> int:
    list_only = "--list" in sys.argv

    problems = []
    counts = {"ok": 0, "excluded": 0}

    for path in sorted(REPO_ROOT.rglob("*.html")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if is_excluded(rel):
            counts["excluded"] += 1
            continue

        status, ids = check_file(path)

        if status == "ok":
            counts["ok"] += 1
            if list_only:
                print(f"  ok  {rel}")
            continue

        message = {
            "missing": "GA4 タグ（gtag.js）が無い",
            "duplicate": f"GA4 タグが {len(ids)} 個ある（二重計上になる）",
            "wrong_id": f"測定IDが {EXPECTED_ID} ではない（別プロパティへ送信される）",
            "after_head": "GA4 タグが </head> より後ろにある",
        }[status]
        problems.append(f"{rel}: {message}")

    print(
        f"GA4 タグ検査: 正常 {counts['ok']} / "
        f"除外 {counts['excluded']} / 異常 {len(problems)}"
    )

    if problems:
        print("")
        for p in problems:
            print(f"::error::{p}")
        print("")
        print("直し方: assets/partials/head-common.html と同じ GA4 スニペットを")
        print("        該当ページの <head> 内（viewport の直後）に入れる。")
        print("        意図的に計測しないページなら scripts/check_ga4_tag.py の")
        print("        EXCLUDE_PREFIXES に理由つきで追記する。")
        return 1 if not list_only else 0

    print("GA4 タグ検査: 異常なし")
    return 0


if __name__ == "__main__":
    sys.exit(main())
