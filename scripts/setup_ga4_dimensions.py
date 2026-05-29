#!/usr/bin/env python3
"""setup_ga4_dimensions.py

GA4 のカスタムディメンション6件を Admin API で一括登録する（一回限り）。
冪等：既に同じ parameter_name が登録済みならスキップ。

設計: docs/aiseo/phase_9_redirects_design.md
承認プラン: ~/.claude/plans/cryptic-sniffing-cerf.md

【前提】
- GA4 サービスアカウントが対象プロパティに **編集者** ロールで参加していること
  （Viewer では list はできるが create はできない。
   作成後は Viewer に戻して構わない）
- 環境変数:
    GA4_PROPERTY_ID         — 9桁数字
    GA4_SERVICE_ACCOUNT_KEY — JSON 文字列（鍵ファイルの中身そのもの）

【実行】
    pip install google-analytics-admin
    $env:GA4_PROPERTY_ID = "123456789"
    $env:GA4_SERVICE_ACCOUNT_KEY = (Get-Content path\to\key.json -Raw)
    python scripts/setup_ga4_dimensions.py

    # GitHub Actions からも workflow_dispatch で起動可（同名 workflow を別途用意）

【冪等】
- 既存ディメンションは parameter_name で検出してスキップ
- 名前は同じでスコープが違うケースは警告だけ出して skip（手動で削除を依頼）
"""
from __future__ import annotations

import json
import os
import sys

DIMENSIONS = [
    {"parameter_name": "slug", "display_name": "slug", "description": "リダイレクト識別子"},
    {"parameter_name": "from", "display_name": "from", "description": "流入元記事スラグ"},
    {"parameter_name": "from_valid", "display_name": "from_valid", "description": "正規表現マッチ可否"},
    {"parameter_name": "channel", "display_name": "channel", "description": "流入チャネル note/cocon/akari等"},
    {"parameter_name": "dest_domain", "display_name": "dest_domain", "description": "行き先ドメイン"},
    {"parameter_name": "category", "display_name": "category", "description": "brain/coconala/line_bot"},
]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

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
        from google.analytics.admin_v1beta.types import CustomDimension
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

    # 既存の一覧
    existing: dict[str, CustomDimension] = {}
    for cd in client.list_custom_dimensions(parent=parent):
        existing[cd.parameter_name] = cd

    created = []
    skipped = []
    scope_warnings = []

    for d in DIMENSIONS:
        pname = d["parameter_name"]
        if pname in existing:
            existing_cd = existing[pname]
            if existing_cd.scope != CustomDimension.DimensionScope.EVENT:
                scope_warnings.append(
                    f"{pname}: 既存だが scope が {existing_cd.scope.name} (EVENT 期待)。"
                    " GA4 UI で削除してから再実行してください"
                )
            else:
                skipped.append(pname)
            continue
        cd = CustomDimension(
            parameter_name=pname,
            display_name=d["display_name"],
            description=d["description"],
            scope=CustomDimension.DimensionScope.EVENT,
        )
        result = client.create_custom_dimension(
            parent=parent, custom_dimension=cd
        )
        created.append(result.parameter_name)

    print(f"created ({len(created)}): {', '.join(created) if created else '(none)'}")
    print(f"skipped ({len(skipped)}): {', '.join(skipped) if skipped else '(none)'}")
    if scope_warnings:
        print("WARNINGS:")
        for w in scope_warnings:
            print(f"  - {w}")
    return 0 if not scope_warnings else 1


if __name__ == "__main__":
    sys.exit(main())
