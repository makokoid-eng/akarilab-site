#!/usr/bin/env python3
"""setup_sales_tracker.py

Phase 10 の Google Sheets を全自動でセットアップする。

【やること】
1. user OAuth で認証
2. 新規 Sheets を作成 or 既存を再利用
3. 5 シート (sales_log / clicks_log / cvr_summary / monthly_summary / 商品マスタ) を準備
4. 各シートに日本語ヘッダ列・数式を埋込
5. 「商品マスタ」シートに data/sales_products.yml の内容を投入
6. sales_log に**ドロップダウン**と VLOOKUP 自動入力を仕込む
7. Service Account を「編集者」として共有
8. Sheets ID を scripts/.sales_tracker_id.txt に保存

【UX】
- 列名は全部日本語
- 販売チャネル・商品スラグ・流入チャネルは**ドロップダウン**
- 商品スラグを選ぶと商品名と標準単価が**VLOOKUPで自動入力**
- 件数だけ手入力すれば売上が自動計算

【実行】
    $env:GA4_CLIENT_SECRETS = "C:\\Users\\user\\Downloads\\client_secret_XXX.json"
    $env:SALES_TRACKER_SA_EMAIL = "akarilab-ga4-reader@akarilab.iam.gserviceaccount.com"
    python scripts/setup_sales_tracker.py

【冪等】
- scripts/.sales_tracker_id.txt があれば既存 Sheets を再利用
- 既存シートタブはスキップ、未作成なら追加
- ヘッダ・数式・データ入力規則は毎回上書き
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
TOKEN_PATH = REPO_ROOT / "scripts" / ".sales_tracker_token.json"
SHEET_ID_FILE = REPO_ROOT / "scripts" / ".sales_tracker_id.txt"
PRODUCTS_YML = REPO_ROOT / "data" / "sales_products.yml"

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_TITLE = "AkariLab 売上管理（Phase 10）"

# 販売チャネルの選択肢（ドロップダウン）
CHANNEL_OPTIONS = ["brain", "coconala", "note", "hidamari", "moyalog", "repimemo", "other"]
# 流入チャネル（GA4 channel と合わせる）
REFERRER_CHANNEL_OPTIONS = ["note", "cocon", "akari", "x", "other"]

SHEET_DEFS = {
    "sales_log": {
        "header": [
            "日付", "販売チャネル", "商品スラグ", "商品名", "件数",
            "単価", "売上", "入金日", "流入チャネル", "メモ",
        ],
        # D列: 商品名（VLOOKUP）, F列: 単価（VLOOKUP）, G列: 売上（件数×単価）
        "formula_columns": {
            "D": "=IF(C{row}=\"\",\"\",IFERROR(VLOOKUP(C{row},商品マスタ!A:C,2,FALSE),\"\"))",
            "F": "=IF(C{row}=\"\",\"\",IFERROR(VLOOKUP(C{row},商品マスタ!A:C,3,FALSE),\"\"))",
            "G": "=IF(OR(E{row}=\"\",F{row}=\"\"),\"\",E{row}*F{row})",
        },
    },
    "clicks_log": {
        # 英語のまま（cron が書き込む、プログラム側都合）
        "header": ["week", "slug", "from", "channel", "clicks", "synced_at"],
        "formula_columns": {},
    },
    "cvr_summary": {
        "header": ["商品スラグ", "月", "クリック数", "販売数", "売上合計", "CVR_%"],
        "formula_columns": {
            "C": "=IF(A{row}=\"\",\"\",SUMIFS(clicks_log!E:E,clicks_log!B:B,A{row}))",
            "D": "=IF(A{row}=\"\",\"\",SUMIFS(sales_log!E:E,sales_log!C:C,A{row},sales_log!A:A,\">=\"&DATE(VALUE(LEFT(B{row},4)),VALUE(RIGHT(B{row},2)),1),sales_log!A:A,\"<\"&EDATE(DATE(VALUE(LEFT(B{row},4)),VALUE(RIGHT(B{row},2)),1),1)))",
            "E": "=IF(A{row}=\"\",\"\",SUMIFS(sales_log!G:G,sales_log!C:C,A{row},sales_log!A:A,\">=\"&DATE(VALUE(LEFT(B{row},4)),VALUE(RIGHT(B{row},2)),1),sales_log!A:A,\"<\"&EDATE(DATE(VALUE(LEFT(B{row},4)),VALUE(RIGHT(B{row},2)),1),1)))",
            "F": "=IF(C{row}=\"\",\"\",IFERROR(D{row}/C{row}*100,0))",
        },
    },
    "monthly_summary": {
        "header": ["月", "販売チャネル", "売上", "販売数"],
        "formula_columns": {},
    },
    "商品マスタ": {
        "header": ["商品スラグ", "商品名", "標準単価"],
        "formula_columns": {},
        # データは投入関数で別途
    },
}

# データ入力規則を入れる列（sheet_name -> [(col_letter, options_or_range)]）
# range="商品マスタ!A2:A" のような形式で、商品マスタ から動的取得も可
DATA_VALIDATIONS = {
    "sales_log": [
        ("B", "list", CHANNEL_OPTIONS),  # 販売チャネル
        ("C", "range", "商品マスタ!$A$2:$A$50"),  # 商品スラグ
        ("I", "list", REFERRER_CHANNEL_OPTIONS),  # 流入チャネル
    ],
}


def load_products() -> list[dict]:
    data = yaml.safe_load(PRODUCTS_YML.read_text(encoding="utf-8"))
    return data["products"]


def get_credentials(client_secrets_path: str):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if TOKEN_PATH.is_file():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
            if not creds.has_scopes(SCOPES):
                print("  → スコープ不一致、再認証します")
                creds = None
        except Exception:
            creds = None

    if not creds or not creds.valid:
        need_new_flow = True
        if creds and creds.expired and creds.refresh_token and creds.has_scopes(SCOPES):
            try:
                creds.refresh(Request())
                need_new_flow = False
            except Exception as exc:
                print(f"  → refresh 失敗 ({exc.__class__.__name__})、新規認証に切り替え")
                creds = None

        if need_new_flow:
            print("  → OAuth flow 起動（ブラウザで承認）")
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
            creds = flow.run_local_server(port=0, open_browser=True)
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
        print(f"  → トークン保存: {TOKEN_PATH.relative_to(REPO_ROOT)}")
    return creds


def create_or_open_sheet(sheets_service) -> str:
    if SHEET_ID_FILE.is_file():
        sheet_id = SHEET_ID_FILE.read_text(encoding="utf-8").strip()
        try:
            sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            print(f"  → 既存 Sheets 検出: {sheet_id[:12]}...")
            return sheet_id
        except Exception:
            print(f"  → .sales_tracker_id.txt は古い、新規作成")

    body = {"properties": {"title": SHEET_TITLE}}
    result = sheets_service.spreadsheets().create(body=body, fields="spreadsheetId").execute()
    sheet_id = result["spreadsheetId"]
    SHEET_ID_FILE.write_text(sheet_id, encoding="utf-8")
    print(f"  → 新規 Sheets 作成: {sheet_id}")
    return sheet_id


def get_sheet_id_by_title(sheets_service, spreadsheet_id: str, title: str) -> int | None:
    meta = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for s in meta["sheets"]:
        if s["properties"]["title"] == title:
            return s["properties"]["sheetId"]
    return None


def ensure_sheets_and_headers(sheets_service, spreadsheet_id: str) -> None:
    meta = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    existing_titles = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}

    add_requests = [
        {"addSheet": {"properties": {"title": name}}}
        for name in SHEET_DEFS
        if name not in existing_titles
    ]
    if add_requests:
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body={"requests": add_requests}
        ).execute()
        print(f"  → {len(add_requests)} シート追加")
        meta = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        existing_titles = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}

    # 標準の "Sheet1" を削除
    if "Sheet1" in existing_titles and len(existing_titles) > len(SHEET_DEFS):
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [{"deleteSheet": {"sheetId": existing_titles["Sheet1"]}}]},
        ).execute()
        print(f"  → デフォルト Sheet1 削除")

    for name, definition in SHEET_DEFS.items():
        header = definition["header"]
        last_col = chr(ord("A") + len(header) - 1)
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{name}!A1:{last_col}1",
            valueInputOption="USER_ENTERED",
            body={"values": [header]},
        ).execute()
        print(f"  → {name} ヘッダ設定 ({len(header)} 列)")

        for col, template in definition["formula_columns"].items():
            values = [[template.format(row=row)] for row in range(2, 102)]
            sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{name}!{col}2:{col}101",
                valueInputOption="USER_ENTERED",
                body={"values": values},
            ).execute()
            print(f"     {col}列に数式 (100行)")


def populate_product_master(sheets_service, spreadsheet_id: str) -> None:
    products = load_products()
    rows = [[p["slug"], p["name"], p["standard_price"]] for p in products]
    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"商品マスタ!A2:C{len(rows) + 1}",
        valueInputOption="USER_ENTERED",
        body={"values": rows},
    ).execute()
    print(f"  → 商品マスタ に {len(rows)} 商品を投入")


def apply_data_validations(sheets_service, spreadsheet_id: str) -> None:
    """各シートにドロップダウン（データ入力規則）を設定。"""
    requests = []
    for sheet_name, rules in DATA_VALIDATIONS.items():
        sheet_id = get_sheet_id_by_title(sheets_service, spreadsheet_id, sheet_name)
        if sheet_id is None:
            continue
        for col, kind, value in rules:
            col_idx = ord(col) - ord("A")
            if kind == "list":
                rule = {
                    "condition": {
                        "type": "ONE_OF_LIST",
                        "values": [{"userEnteredValue": v} for v in value],
                    },
                    "showCustomUi": True,
                    "strict": False,
                }
            elif kind == "range":
                rule = {
                    "condition": {
                        "type": "ONE_OF_RANGE",
                        "values": [{"userEnteredValue": "=" + value}],
                    },
                    "showCustomUi": True,
                    "strict": False,
                }
            else:
                continue
            requests.append(
                {
                    "setDataValidation": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 1,  # 2行目から
                            "endRowIndex": 101,
                            "startColumnIndex": col_idx,
                            "endColumnIndex": col_idx + 1,
                        },
                        "rule": rule,
                    }
                }
            )

    if requests:
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body={"requests": requests}
        ).execute()
        print(f"  → データ入力規則 (ドロップダウン) {len(requests)} 件設定")


def share_with_sa(drive_service, spreadsheet_id: str, sa_email: str) -> None:
    perms = drive_service.permissions().list(
        fileId=spreadsheet_id,
        fields="permissions(id,emailAddress,role)",
    ).execute()
    for p in perms.get("permissions", []):
        if p.get("emailAddress") == sa_email and p.get("role") in ("writer", "owner"):
            print(f"  → 既に共有済み ({p['role']})、スキップ")
            return
    drive_service.permissions().create(
        fileId=spreadsheet_id,
        body={"type": "user", "role": "writer", "emailAddress": sa_email},
        sendNotificationEmail=False,
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
    if not PRODUCTS_YML.is_file():
        print(f"ERROR: products yml not found: {PRODUCTS_YML}", file=sys.stderr)
        return 2

    try:
        from googleapiclient.discovery import build
    except ImportError:
        print(
            "ERROR: missing packages. Run: pip install google-api-python-client google-auth-oauthlib",
            file=sys.stderr,
        )
        return 2

    print("[認証] OAuth flow")
    creds = get_credentials(client_secrets)
    sheets_service = build("sheets", "v4", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    print("[1/5] Sheets 作成 or 検出")
    spreadsheet_id = create_or_open_sheet(sheets_service)

    print("[2/5] 5 シート + 日本語ヘッダ + 数式 セットアップ")
    ensure_sheets_and_headers(sheets_service, spreadsheet_id)

    print("[3/5] 商品マスタ にデータ投入")
    populate_product_master(sheets_service, spreadsheet_id)

    print("[4/5] ドロップダウン (データ入力規則) 設定")
    apply_data_validations(sheets_service, spreadsheet_id)

    print(f"[5/5] SA 共有: {sa_email}")
    share_with_sa(drive_service, spreadsheet_id, sa_email)

    print()
    print("=" * 60)
    print(f"Sheets URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
    print("=" * 60)
    print()
    print("【sales_log の使い方】")
    print("  1. 日付（列A）に売上日を入力")
    print("  2. 販売チャネル（列B）はドロップダウンから選択")
    print("  3. 商品スラグ（列C）はドロップダウンから選択")
    print("     → 商品名（D）と単価（F）が自動で入る")
    print("  4. 件数（列E）を入力 → 売上（G）が自動計算")
    print("  5. 入金日（H）と流入チャネル（I）とメモ（J）を入力")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
