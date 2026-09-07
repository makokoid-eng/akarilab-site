#!/usr/bin/env python3
"""setup_ga4_key_events.py

PURPOSE
  GA4 の「キーイベント」（旧コンバージョン）を Admin API で登録する。

  背景（2026-09-07 の実測）
    GA4 プロパティ akarilab.org のキーイベントは、GA4 が最初から用意する
    `purchase` の1件だけだった。実際には redirect_click（外部サービスへの
    リンククリック）が毎日飛んでいるのに、どれもキーイベントになっていない。
    そのため GA4 上では「キーイベント 0」と表示され続け、
    どの記事・どのチャネルから申し込みに近い行動が起きたのかが分からない。

  なぜ purchase を消さないか
    GA4 の既定キーイベントで、外しても得はない。Stripe 決済を将来 GA4 に
    送る余地も残る。ここでは触らない。

【前提】
  - サービスアカウントが対象プロパティに **編集者** ロールで参加していること
    （Viewer では list はできるが create はできない）
  - 環境変数:
      GA4_PROPERTY_ID         — 9桁数字
      GA4_SERVICE_ACCOUNT_KEY — JSON 文字列（鍵ファイルの中身そのもの）

【実行】
    pip install google-analytics-admin
    $env:GA4_PROPERTY_ID = "539463635"          # akarilab.org
    $env:GA4_SERVICE_ACCOUNT_KEY = (Get-Content path\to\key.json -Raw)

    python scripts/setup_ga4_key_events.py            # dry-run（何もしない。差分を出すだけ）
    python scripts/setup_ga4_key_events.py --apply    # 実際に登録する

【冪等】
  - 既に同名のキーイベントがあればスキップする
  - 登録済みイベントの削除はしない（消すのは GA4 の画面から手で）

【注意】
  キーイベントは「登録した時点以降」のデータにしか付かない。
  過去にさかのぼって数え直されることはない。だから早く入れるほど得をする。
"""
from __future__ import annotations

import json
import os
import sys

# 登録するキーイベント。
#   name        … GA4 に送っているイベント名（コード側と一致していること）
#   why         … なぜこれをキーイベントにするのか。後から読む人のために必ず書く
KEY_EVENTS = [
    {
        "name": "redirect_click",
        "why": (
            "/r/** の計測用リダイレクトを通って外部サービス（Brain・ココナラ・"
            "LINE Bot 等）へ出ていったクリック。当サイトで一番申し込みに近い行動。"
        ),
    },
]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    apply_changes = "--apply" in sys.argv

    property_id = os.environ.get("GA4_PROPERTY_ID", "").strip()
    sa_key = os.environ.get("GA4_SERVICE_ACCOUNT_KEY", "").strip()
    if not property_id or not sa_key:
        print(
            "ERROR: GA4_PROPERTY_ID / GA4_SERVICE_ACCOUNT_KEY env vars required",
            file=sys.stderr,
        )
        return 2

    try:
        from google.analytics.admin import AnalyticsAdminServiceClient
        from google.analytics.admin_v1beta.types import KeyEvent
        from google.oauth2 import service_account
    except ImportError as exc:
        print(
            "ERROR: missing package. Run: pip install google-analytics-admin",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc

    credentials = service_account.Credentials.from_service_account_info(
        json.loads(sa_key)
    )
    client = AnalyticsAdminServiceClient(credentials=credentials)
    parent = f"properties/{property_id}"

    existing = {ke.event_name for ke in client.list_key_events(parent=parent)}
    print(f"既存のキーイベント: {', '.join(sorted(existing)) or '(なし)'}")

    to_create = [e for e in KEY_EVENTS if e["name"] not in existing]
    skipped = [e["name"] for e in KEY_EVENTS if e["name"] in existing]

    if not to_create:
        print("追加するものはありません（すべて登録済み）")
        return 0

    print("")
    print(f"追加対象 {len(to_create)} 件:")
    for e in to_create:
        print(f"  + {e['name']}")
        print(f"      理由: {e['why']}")

    if not apply_changes:
        print("")
        print("dry-run のため何も変更していません。実行するには --apply を付けてください。")
        return 0

    created = []
    for e in to_create:
        ke = KeyEvent(
            event_name=e["name"],
            counting_method=KeyEvent.CountingMethod.ONCE_PER_SESSION,
        )
        result = client.create_key_event(parent=parent, key_event=ke)
        created.append(result.event_name)

    print("")
    print(f"登録しました ({len(created)}): {', '.join(created)}")
    if skipped:
        print(f"スキップ ({len(skipped)}): {', '.join(skipped)}")
    print("")
    print("※ キーイベントは登録時点以降のデータにのみ適用されます。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
