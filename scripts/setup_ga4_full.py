#!/usr/bin/env python3
"""setup_ga4_full.py

GA4 Admin API を user OAuth (Application Default Credentials) で叩いて、
以下を一括実行する：

  1. サービスアカウント (GA4_SERVICE_ACCOUNT_EMAIL) を「閲覧者」として追加
     ※ ディメンション作成は本スクリプト自身が user 権限で行うので
        SA には最小権限の閲覧者だけ付与する
  2. カスタムディメンション 6件 (slug/from/from_valid/channel/dest_domain/category)
     をプロパティに登録

両方とも冪等。既存なら skip。

設計: docs/aiseo/phase_9_redirects_design.md
承認プラン: ~/.claude/plans/cryptic-sniffing-cerf.md

【前提】
- gcloud CLI インストール済 (https://cloud.google.com/sdk/docs/install)
- 実行ユーザー (makokoid@gmail.com) が当該GA4プロパティの管理者
- pip install google-analytics-admin

【セットアップ手順】

  1) gcloud で user OAuth (GA4 スコープ付き) で認証する：

     gcloud auth application-default login `
       --scopes="openid,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/analytics.edit,https://www.googleapis.com/auth/analytics.manage.users"

     ブラウザが開いて makokoid@gmail.com でログインを促されるので承認。
     credentials.json が ~/.config/gcloud/application_default_credentials.json に保存される。

  2) 環境変数を設定して実行：

     $env:GA4_PROPERTY_ID = "539463635"
     $env:GA4_SERVICE_ACCOUNT_EMAIL = "akarilab-ga4-reader@akarilab.iam.gserviceaccount.com"
     python scripts/setup_ga4_full.py
"""
from __future__ import annotations

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
    sa_email = os.environ.get("GA4_SERVICE_ACCOUNT_EMAIL", "").strip()
    if not property_id:
        print("ERROR: GA4_PROPERTY_ID env var required", file=sys.stderr)
        return 2
    if not sa_email:
        print("ERROR: GA4_SERVICE_ACCOUNT_EMAIL env var required", file=sys.stderr)
        return 2

    try:
        import google.auth
        from google.analytics.admin import AnalyticsAdminServiceClient
        from google.analytics.admin_v1beta.types import (
            AccessBinding,
            CreateAccessBindingRequest,
            CustomDimension,
        )
    except ImportError as exc:
        print(
            "ERROR: missing package. Run: pip install google-analytics-admin",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc

    credentials, _ = google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/analytics.edit",
            "https://www.googleapis.com/auth/analytics.manage.users",
        ]
    )
    client = AnalyticsAdminServiceClient(credentials=credentials)
    parent = f"properties/{property_id}"

    print(f"[1/2] サービスアカウント追加: {sa_email} → properties/{property_id} (viewer)")

    # 既存の access bindings を見て、既に SA が登録済みなら skip
    sa_already = False
    for binding in client.list_access_bindings(parent=parent):
        if binding.user == sa_email:
            sa_already = True
            print(f"  → 既に登録済み (roles={list(binding.roles)})、スキップ")
            break

    if not sa_already:
        try:
            request = CreateAccessBindingRequest(
                parent=parent,
                access_binding=AccessBinding(
                    user=sa_email,
                    roles=["predefinedRoles/viewer"],
                ),
            )
            result = client.create_access_binding(request=request)
            print(f"  → 追加完了: {result.name}")
        except Exception as exc:
            print(f"  → 失敗: {exc}", file=sys.stderr)
            return 2

    print(f"[2/2] カスタムディメンション登録: {len(DIMENSIONS)} 件")

    existing: dict[str, CustomDimension] = {}
    for cd in client.list_custom_dimensions(parent=parent):
        existing[cd.parameter_name] = cd

    created = []
    skipped = []
    for d in DIMENSIONS:
        pname = d["parameter_name"]
        if pname in existing:
            skipped.append(pname)
            continue
        cd = CustomDimension(
            parameter_name=pname,
            display_name=d["display_name"],
            description=d["description"],
            scope=CustomDimension.DimensionScope.EVENT,
        )
        try:
            result = client.create_custom_dimension(
                parent=parent, custom_dimension=cd
            )
            created.append(result.parameter_name)
            print(f"  → 作成: {pname}")
        except Exception as exc:
            print(f"  → {pname} 失敗: {exc}", file=sys.stderr)

    print()
    print(f"created ({len(created)}): {', '.join(created) if created else '(none)'}")
    print(f"skipped ({len(skipped)}): {', '.join(skipped) if skipped else '(none)'}")
    print()
    print("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
