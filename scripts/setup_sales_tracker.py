#!/usr/bin/env python3
"""setup_sales_tracker.py

Phase 10 の Google Sheets を全自動でセットアップする。

【やること】
1. user OAuth で認証
2. 新規 Sheets「AkariLab 売上管理（Phase 10）」を作成
3. 4 シート (sales_log / clicks_log / cvr_summary / monthly_summary) を作成
4. 各シートにヘッダ列・数式を埋め込み
5. Service Account を「編集者」として共有（Drive API）
6. Sheets ID を scripts/.sales_tracker_id.txt に保存（gitignore対象）
7. オプションで `gh secret set` を呼んで Secrets 登録

【前提】
- pip install google-analytics-admin google-auth-oauthlib google-api-python-client
- Phase 9 で作った OAuth クライアントJSONを流用可能
- Google Sheets API + Drive API が GCP で有効化されていること（後述）

【Sheets API + Drive API 有効化】
    gcloud services enable sheets.googleapis.com drive.googleapis.com --project=akarilab

【実行】
    $env:GA4_CLIENT_SECRETS = "C:\\Users\\user\\Downloads\\client_secret_XXX.json"
    $env:SALES_TRACKER_SA_EMAIL = "akarilab-ga4-reader@akarilab.iam.gserviceaccount.com"
    python scripts/setup_sales_tracker.py
    # Sheets ID を控えてから:
    gh secret set SALES_TRACKER_SHEET_ID -R makokoid-eng/akarilab-site

【冪等】
- scripts/.sales_tracker_id.txt が既にあれば、既存 Sheets を更新（再作成しない）
- 既にあるシートタブはスキップ、未作成なら追加
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
TOKEN_PATH = REPO_ROOT / "scripts" / ".ga4_token.json"  # 既存 Phase 9 のトークンを流用
SHEET_ID_FILE = REPO_ROOT / "scripts" / ".sales_tracker_id.txt"

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_TITLE = "AkariLab 売上管理（Phase 10）"

SHEET_DEFS = {
    "sales_log": {
        "header": [
            "date", "channel", "slug", "product_name", "quantity",
            "price", "revenue", "payment_date", "referrer_channel", "note",
        ],
        # G列に売上自動計算（quantity * price）の数式を2-100行まで仕込む
        "formula_columns": {"G": "=IF(E{row}=\"\",\"\",E{row}*F{row})"},
    },
    "clicks_log": {
        "header": ["week", "slug", "from", "channel", "clicks", "synced_at"],
        "formula_columns": {},
    },
    "cvr_summary": {
        "header": [
            "slug", "month", "clicks_total", "sales_count",
            "revenue_total", "cvr_percent",
        ],
        # C,D,E,F に SUMIFS と CVR 計算（最初の20行）
        "formula_columns": {
            "C": "=IF(A{row}=\"\",\"\",SUMIFS(clicks_log!E:E, clicks_log!B:B, A{row}))",
            "D": "=IF(A{row}=\"\",\"\",SUMIFS(sales_log!E:E, sales_log!C:C, A{row}, sales_log!A:A, \">=\"&DATE(VALUE(LEFT(B{row},4)),VALUE(RIGHT(B{row},2)),1), sales_log!A:A, \"<\"&EDATE(DATE(VALUE(LEFT(B{row},4)),VALUE(RIGHT(B{row},2)),1),1)))",
            "E": "=IF(A{row}=\"\",\"\",SUMIFS(sales_log!G:G, sales_log!C:C, A{row}, sales_log!A:A, \">=\"&DATE(VALUE(LEFT(B{row},4)),VALUE(RIGHT(B{row},2)),1), sales_log!A:A, \"<\"&EDATE(DATE(VALUE(LEFT(B{row},4)),VALUE(RIGHT(B{row},2)),1),1)))",
            "F": "=IF(C{row}=\"\",\"\",IFERROR(D{row}/C{row}*100, 0))",
        },
    },
    "monthly_summary": {
        "header": ["month", "channel", "revenue", "sales_count"],
        # 注釈: ピボットテーブルは手動で作る方が柔軟なので、ここでは行ヘッダのみ
        "formula_columns": {},
    },
}


def get_credentials(client_secrets_path: str):
    """Phase 9 と同じトークンキャッシュを共用。"""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if TOKEN_PATH.is_file():
        try:
            # 既存トークンのスコープを確認、Phase 10 のスコープが足りなければ再認証
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
            if not creds.has_scopes(SCOPES):
                creds = None
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token and creds.has_scopes(SCOPES):
            creds.refresh(Request())
        else:
            print("  → OAuth flow 起動（ブラウザで承認）")
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
            creds = flow.run_local_server(port=0, open_browser=True)
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
        print(f"  → トークン保存: {TOKEN_PATH.relative_to(REPO_ROOT)}")
    return creds


def create_or_open_sheet(sheets_service, drive_service) -> str:
    if SHEET_ID_FILE.is_file():
        sheet_id = SHEET_ID_FILE.read_text(encoding="utf-8").strip()
        try:
            sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            print(f"  → 既存 Sheets 検出: {sheet_id[:12]}...")
            return sheet_id
        except Exception:
            print(f"  → .sales_tracker_id.txt は古い、新規作成")

    body = {"properties": {"title": SHEET_TITLE}}
    result = sheets_service.spreadsheets().create(
        body=body,
        fields="spreadsheetId",
    ).execute()
    sheet_id = result["spreadsheetId"]
    SHEET_ID_FILE.write_text(sheet_id, encoding="utf-8")
    print(f"  → 新規 Sheets 作成: {sheet_id}")
    return sheet_id


def ensure_sheets_and_headers(sheets_service, sheet_id: str) -> None:
    """4シートが揃っていなければ追加、ヘッダと数式を埋める。"""
    meta = sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    existing_titles = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}

    # シート追加（既存なら skip）
    add_requests = []
    for name in SHEET_DEFS:
        if name not in existing_titles:
            add_requests.append({"addSheet": {"properties": {"title": name}}})

    if add_requests:
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": add_requests},
        ).execute()
        print(f"  → {len(add_requests)} シート追加: {[r['addSheet']['properties']['title'] for r in add_requests]}")
        # 再取得
        meta = sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        existing_titles = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}

    # デフォルト Sheet1 を削除（残っていれば、4 シート以上の状態で）
    default_title = "Sheet1"
    if default_title in existing_titles and len(existing_titles) > len(SHEET_DEFS):
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": [{"deleteSheet": {"sheetId": existing_titles[default_title]}}]},
        ).execute()
        print(f"  → デフォルト Sheet1 削除")

    # 各シートにヘッダと数式
    for name, definition in SHEET_DEFS.items():
        header = definition["header"]
        sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"{name}!A1:{chr(ord('A') + len(header) - 1)}1",
            valueInputOption="USER_ENTERED",
            body={"values": [header]},
        ).execute()
        print(f"  → {name} ヘッダ設定 ({len(header)} 列)")

        # 数式列を 2-50 行に埋める（cvr_summary は手入力で slug/month を入れる前提なので、空欄なら空欄）
        formula_columns = definition["formula_columns"]
        for col, template in formula_columns.items():
            values = []
            for row in range(2, 52):
                values.append([template.format(row=row)])
            sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f"{name}!{col}2:{col}51",
                valueInputOption="USER_ENTERED",
                body={"values": values},
            ).execute()
            print(f"     {col}列に数式 (50行)")


def share_with_sa(drive_service, sheet_id: str, sa_email: str) -> None:
    """Service Account に「編集者」権限を付与（既存なら skip）。"""
    perms = drive_service.permissions().list(
        fileId=sheet_id,
        fields="permissions(id,emailAddress,role)",
        supportsAllDrives=False,
    ).execute()
    for p in perms.get("permissions", []):
        if p.get("emailAddress") == sa_email:
            if p.get("role") in ("writer", "owner"):
                print(f"  → 既に共有済み ({p['role']})、スキップ")
                return
    drive_service.permissions().create(
        fileId=sheet_id,
        body={"type": "user", "role": "writer", "emailAddress": sa_email},
        sendNotificationEmail=False,
        supportsAllDrives=False,
    ).execute()
    print(f"  → SA 共有完了: {sa_email} (writer)")


def main() -> int:
    client_secrets = os.environ.get("GA4_CLIENT_SECRETS", "").strip()
    sa_email = os.environ.get("SALES_TRACKER_SA_EMAIL", "").strip()

    if not client_secrets:
        print("ERROR: GA4_CLIENT_SECRETS env var required", file=sys.stderr)
        return 2
    if not Path(client_secrets).is_file():
        print(f"ERROR: client secrets file not found: {client_secrets}", file=sys.stderr)
        return 2
    if not sa_email:
        print("ERROR: SALES_TRACKER_SA_EMAIL env var required", file=sys.stderr)
        return 2

    try:
        from googleapiclient.discovery import build
    except ImportError:
        print(
            "ERROR: missing packages. Run: pip install google-api-python-client google-auth-oauthlib",
            file=sys.stderr,
        )
        return 2

    print("[認証] OAuth flow (Phase 9 トークン流用、スコープ不足なら再認証)")
    creds = get_credentials(client_secrets)
    sheets_service = build("sheets", "v4", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    print("[1/3] Sheets 作成 or 検出")
    sheet_id = create_or_open_sheet(sheets_service, drive_service)

    print("[2/3] 4 シート + ヘッダ + 数式 セットアップ")
    ensure_sheets_and_headers(sheets_service, sheet_id)

    print(f"[3/3] Service Account 共有: {sa_email}")
    share_with_sa(drive_service, sheet_id, sa_email)

    print()
    print("=" * 50)
    print(f"Sheets ID: {sheet_id}")
    print(f"Sheets URL: https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
    print("=" * 50)
    print()
    print("次のステップ:")
    print(f"  1. gcloud services enable sheets.googleapis.com drive.googleapis.com --project=akarilab")
    print(f"  2. gh secret set SALES_TRACKER_SHEET_ID -R makokoid-eng/akarilab-site -b \"{sheet_id}\"")
    print(f"  3. https://github.com/makokoid-eng/akarilab-site/actions/workflows/redirect-metrics.yml で workflow_dispatch")
    return 0


if __name__ == "__main__":
    sys.exit(main())
