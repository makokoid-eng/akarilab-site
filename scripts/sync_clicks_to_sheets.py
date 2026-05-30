#!/usr/bin/env python3
"""sync_clicks_to_sheets.py

GA4 Data API から直近1週間の redirect_click を取得し、
Google Sheets の `clicks_log` シートに append する。

設計: docs/aiseo/phase_10_sales_tracker_design.md
承認プラン: ~/.claude/plans/cryptic-sniffing-cerf.md

【前提】
- Service Account `akarilab-ga4-reader` に対して、対象 Sheets を「編集者」で共有
- Google Sheets API を有効化（GCP）

【環境変数】
- GA4_PROPERTY_ID: 9桁数字
- GA4_SERVICE_ACCOUNT_KEY: SA鍵 JSON 文字列
- SALES_TRACKER_SHEET_ID: Sheets ID（URL から抽出、英数記号の文字列）

【実行】
- ローカル: 環境変数セットして `python scripts/sync_clicks_to_sheets.py`
- CI: redirect-metrics workflow の最後のステップとして実行

【冪等】
- 既存の `clicks_log` シートを読み、(week, slug, from, channel) で重複検知
- 未取得分だけ append
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

JST = timezone(timedelta(hours=9))
SHEET_NAME = "clicks_log"
HEADER = ["week", "slug", "from", "channel", "clicks", "synced_at"]


def iso_week_label(d: datetime) -> str:
    iso = d.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def fetch_ga4_aggregated(property_id: str, sa_key_json: str, start: str, end: str) -> list[dict]:
    """GA4 から redirect_click を slug × from × channel で集計。"""
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        DateRange,
        Dimension,
        FilterExpression,
        Filter,
        Metric,
        RunReportRequest,
    )
    from google.oauth2 import service_account

    credentials = service_account.Credentials.from_service_account_info(
        json.loads(sa_key_json)
    )
    client = BetaAnalyticsDataClient(credentials=credentials)
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="customEvent:slug"),
            Dimension(name="customEvent:from"),
            Dimension(name="customEvent:channel"),
        ],
        metrics=[Metric(name="eventCount")],
        date_ranges=[DateRange(start_date=start, end_date=end)],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="eventName",
                string_filter=Filter.StringFilter(value="redirect_click"),
            )
        ),
        limit=10000,
    )
    response = client.run_report(request)
    rows = []
    for row in response.rows:
        rows.append({
            "slug": row.dimension_values[0].value or "(none)",
            "from": row.dimension_values[1].value or "(none)",
            "channel": row.dimension_values[2].value or "(none)",
            "clicks": int(row.metric_values[0].value or 0),
        })
    return rows


def get_sheets_service(sa_key_json: str):
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    credentials = service_account.Credentials.from_service_account_info(
        json.loads(sa_key_json),
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return build("sheets", "v4", credentials=credentials)


def read_existing(service, sheet_id: str) -> set[tuple]:
    """既存の clicks_log を読み、(week, slug, from, channel) のキーセットを返す。"""
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"{SHEET_NAME}!A2:F",
    ).execute()
    values = result.get("values", [])
    existing: set[tuple] = set()
    for row in values:
        if len(row) >= 4:
            existing.add((row[0], row[1], row[2], row[3]))
    return existing


def ensure_header(service, sheet_id: str) -> None:
    """ヘッダ行が無ければ追加。"""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"{SHEET_NAME}!A1:F1",
        ).execute()
        values = result.get("values", [])
        if not values or values[0] != HEADER:
            service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f"{SHEET_NAME}!A1:F1",
                valueInputOption="RAW",
                body={"values": [HEADER]},
            ).execute()
            print(f"  → header set: {HEADER}")
    except Exception as exc:
        # シートが存在しない場合は作る
        if "Unable to parse range" in str(exc):
            service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body={"requests": [{"addSheet": {"properties": {"title": SHEET_NAME}}}]},
            ).execute()
            service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f"{SHEET_NAME}!A1:F1",
                valueInputOption="RAW",
                body={"values": [HEADER]},
            ).execute()
            print(f"  → sheet '{SHEET_NAME}' created, header set")
        else:
            raise


def append_rows(service, sheet_id: str, rows: list[list]) -> None:
    if not rows:
        return
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=f"{SHEET_NAME}!A:F",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()


def main() -> int:
    property_id = os.environ.get("GA4_PROPERTY_ID", "").strip()
    sa_key = os.environ.get("GA4_SERVICE_ACCOUNT_KEY", "").strip()
    sheet_id = os.environ.get("SALES_TRACKER_SHEET_ID", "").strip()

    if not property_id:
        print("ERROR: GA4_PROPERTY_ID env var required", file=sys.stderr)
        return 2
    if not sa_key:
        print("ERROR: GA4_SERVICE_ACCOUNT_KEY env var required", file=sys.stderr)
        return 2
    if not sheet_id:
        print("ERROR: SALES_TRACKER_SHEET_ID env var required", file=sys.stderr)
        return 2

    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient  # noqa: F401
        from googleapiclient.discovery import build  # noqa: F401
    except ImportError:
        print(
            "ERROR: missing packages. Run: pip install google-analytics-data google-api-python-client google-auth",
            file=sys.stderr,
        )
        return 2

    now = datetime.now(JST)
    end_date = now.date() - timedelta(days=1)
    start_date = end_date - timedelta(days=6)
    week_label = iso_week_label(now - timedelta(days=now.weekday()))  # 月曜起点の週ラベル

    print(f"[1/3] GA4 取得: {start_date} 〜 {end_date} (week={week_label})")
    rows = fetch_ga4_aggregated(
        property_id, sa_key, start_date.isoformat(), end_date.isoformat()
    )
    print(f"  → {len(rows)} 行取得")

    print(f"[2/3] Sheets 既存読み込み (sheet_id={sheet_id[:8]}...)")
    service = get_sheets_service(sa_key)
    ensure_header(service, sheet_id)
    existing = read_existing(service, sheet_id)
    print(f"  → 既存 {len(existing)} 行")

    print("[3/3] 未登録分を append")
    synced_at = now.strftime("%Y-%m-%d %H:%M:%S")
    new_rows = []
    for r in rows:
        key = (week_label, r["slug"], r["from"], r["channel"])
        if key in existing:
            continue
        new_rows.append([
            week_label,
            r["slug"],
            r["from"],
            r["channel"],
            r["clicks"],
            synced_at,
        ])
    append_rows(service, sheet_id, new_rows)
    print(f"  → {len(new_rows)} 行追加")
    print()
    print(f"done. (week={week_label}, new={len(new_rows)}, skipped={len(rows) - len(new_rows)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
