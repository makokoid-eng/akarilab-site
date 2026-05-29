#!/usr/bin/env python3
"""setup_ga4_full.py

GA4 Admin API を user OAuth (自前の OAuth client) で叩いて、
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
- GCP で OAuth クライアントID（デスクトップアプリ）を作成し、JSON DL 済
- 実行ユーザー (makokoid@gmail.com) が当該 GA4 プロパティの管理者
- pip install google-analytics-admin google-auth-oauthlib

【実行手順】

  $env:GA4_CLIENT_SECRETS = "C:\\Users\\user\\Downloads\\client_secret_XXX.json"
  $env:GA4_PROPERTY_ID = "539463635"
  $env:GA4_SERVICE_ACCOUNT_EMAIL = "akarilab-ga4-reader@akarilab.iam.gserviceaccount.com"
  python scripts/setup_ga4_full.py

ブラウザが開いて Google ログインを促されるので makokoid@gmail.com で承認。
「このアプリは Google で確認されていません」と出たら「詳細」→「（アプリ名）に移動」で続行
（OAuth 同意画面がテスト中ステータスのため。テストユーザーに自分が入っていれば問題ない）。

【トークンの再利用】
初回 OAuth 後、scripts/.ga4_token.json にトークンを保存（gitignore 対象）。
2回目以降はブラウザを開かずに再利用される。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

DIMENSIONS = [
    {"parameter_name": "slug", "display_name": "slug", "description": "リダイレクト識別子"},
    {"parameter_name": "from", "display_name": "from", "description": "流入元記事スラグ"},
    {"parameter_name": "from_valid", "display_name": "from_valid", "description": "正規表現マッチ可否"},
    {"parameter_name": "channel", "display_name": "channel", "description": "流入チャネル note/cocon/akari等"},
    {"parameter_name": "dest_domain", "display_name": "dest_domain", "description": "行き先ドメイン"},
    {"parameter_name": "category", "display_name": "category", "description": "brain/coconala/line_bot"},
]

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/analytics.edit",
    "https://www.googleapis.com/auth/analytics.manage.users",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
TOKEN_PATH = REPO_ROOT / "scripts" / ".ga4_token.json"


def get_credentials(client_secrets_path: str):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if TOKEN_PATH.is_file():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_path, SCOPES
            )
            creds = flow.run_local_server(port=0, open_browser=True)
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
        print(f"  → トークン保存: {TOKEN_PATH.relative_to(REPO_ROOT)}")
    return creds


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    property_id = os.environ.get("GA4_PROPERTY_ID", "").strip()
    sa_email = os.environ.get("GA4_SERVICE_ACCOUNT_EMAIL", "").strip()
    client_secrets = os.environ.get("GA4_CLIENT_SECRETS", "").strip()
    if not property_id:
        print("ERROR: GA4_PROPERTY_ID env var required", file=sys.stderr)
        return 2
    if not sa_email:
        print("ERROR: GA4_SERVICE_ACCOUNT_EMAIL env var required", file=sys.stderr)
        return 2
    if not client_secrets:
        print("ERROR: GA4_CLIENT_SECRETS env var required (OAuth client JSON path)", file=sys.stderr)
        return 2
    if not Path(client_secrets).is_file():
        print(f"ERROR: client secrets file not found: {client_secrets}", file=sys.stderr)
        return 2

    try:
        from google.analytics.admin import AnalyticsAdminServiceClient
        from google.analytics.admin_v1beta.types import (
            AccessBinding,
            CreateAccessBindingRequest,
            CustomDimension,
        )
    except ImportError as exc:
        print(
            "ERROR: missing package. Run: pip install google-analytics-admin google-auth-oauthlib",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc

    print("[認証] OAuth flow を起動します（初回はブラウザが開く）...")
    credentials = get_credentials(client_secrets)
    client = AnalyticsAdminServiceClient(credentials=credentials)
    parent = f"properties/{property_id}"

    print(f"[1/2] サービスアカウント追加: {sa_email} → properties/{property_id} (viewer)")

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
