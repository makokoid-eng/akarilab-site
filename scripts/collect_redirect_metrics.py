#!/usr/bin/env python3
"""collect_redirect_metrics.py

GA4 Data API から redirect_click イベントを取得し、週次レポート（Markdown）を出力する。
異常検知は scripts/redirect_anomaly_rules.yml に従い、警告をレポートに含める。

設計: docs/aiseo/phase_9_redirects_design.md §自動観察

実行：
- GitHub Actions 月曜 09:00 JST cron（.github/workflows/redirect-metrics.yml）
- 手動実行: workflow_dispatch、もしくはローカルで以下：

    export GA4_PROPERTY_ID=123456789
    export GA4_SERVICE_ACCOUNT_KEY='{"type":"service_account",...}'
    python scripts/collect_redirect_metrics.py --days 7 --out docs/redirect-reports/2026-W22.md

出力：
- docs/redirect-reports/{YYYY-WW}.md にレポート保存
- 標準出力に同レポートを書き出し（GitHub Actions が gh issue create にパイプ）
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
REDIRECTS_YML = REPO_ROOT / "data" / "redirects.yml"
RULES_YML = REPO_ROOT / "scripts" / "redirect_anomaly_rules.yml"
REPORTS_DIR = REPO_ROOT / "docs" / "redirect-reports"

JST = timezone(timedelta(hours=9))


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def iso_week_label(d: datetime) -> str:
    iso = d.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def fetch_ga4_rows(property_id: str, sa_key_json: str, start_date: str, end_date: str) -> list[dict]:
    """GA4 Data API runReport を呼ぶ。

    Dimensions: customEvent:slug, customEvent:from, customEvent:from_valid,
                customEvent:channel, customEvent:dest_domain, customEvent:category, date
    Metrics: eventCount
    Filter: eventName = 'redirect_click'
    """
    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import (
            DateRange,
            Dimension,
            DimensionFilter,
            DimensionFilterExpression,
            Filter,
            Metric,
            RunReportRequest,
        )
        from google.oauth2 import service_account
    except ImportError as exc:
        raise RuntimeError(
            "Required packages not installed. Run: pip install google-analytics-data"
        ) from exc

    credentials = service_account.Credentials.from_service_account_info(
        json.loads(sa_key_json)
    )
    client = BetaAnalyticsDataClient(credentials=credentials)
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="customEvent:slug"),
            Dimension(name="customEvent:from"),
            Dimension(name="customEvent:from_valid"),
            Dimension(name="customEvent:channel"),
            Dimension(name="customEvent:dest_domain"),
            Dimension(name="customEvent:category"),
            Dimension(name="date"),
        ],
        metrics=[Metric(name="eventCount")],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimension_filter=DimensionFilterExpression(
            filter=Filter(
                field_name="eventName",
                string_filter=Filter.StringFilter(value="redirect_click"),
            )
        ),
        limit=10000,
    )
    response = client.run_report(request)
    rows: list[dict] = []
    for row in response.rows:
        rows.append(
            {
                "slug": row.dimension_values[0].value or "(none)",
                "from": row.dimension_values[1].value or "(none)",
                "from_valid": row.dimension_values[2].value or "(none)",
                "channel": row.dimension_values[3].value or "(none)",
                "dest_domain": row.dimension_values[4].value or "(none)",
                "category": row.dimension_values[5].value or "(none)",
                "date": row.dimension_values[6].value or "(none)",
                "clicks": int(row.metric_values[0].value or 0),
            }
        )
    return rows


def load_prev_week_clicks() -> dict[str, int]:
    """過去のレポート Markdown から「slug別合計クリック数」を回収する簡易ローダ。

    現状は厳密なパースを諦め、最新ファイルから '| slug | clicks |' 行を grep。
    実運用で精度が必要になったら、レポートと同時に JSON を吐く形に変更する。
    """
    if not REPORTS_DIR.is_dir():
        return {}
    candidates = sorted(REPORTS_DIR.glob("*.md"), reverse=True)
    if not candidates:
        return {}
    text = candidates[0].read_text(encoding="utf-8")
    result: dict[str, int] = {}
    for line in text.splitlines():
        if not line.startswith("| ") or " | " not in line:
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) >= 2 and cols[0] not in ("slug", "---"):
            try:
                result[cols[0]] = int(cols[1])
            except ValueError:
                continue
    return result


def aggregate(rows: list[dict]) -> dict:
    by_slug: dict[str, int] = {}
    by_slug_channel: dict[tuple[str, str], int] = {}
    by_from_valid: dict[str, int] = {"true": 0, "false": 0, "other": 0}
    by_channel: dict[str, int] = {}
    by_date: dict[str, int] = {}
    total = 0
    for r in rows:
        by_slug[r["slug"]] = by_slug.get(r["slug"], 0) + r["clicks"]
        key = (r["slug"], r["channel"])
        by_slug_channel[key] = by_slug_channel.get(key, 0) + r["clicks"]
        fv = r["from_valid"].lower()
        if fv == "true":
            by_from_valid["true"] += r["clicks"]
        elif fv == "false":
            by_from_valid["false"] += r["clicks"]
        else:
            by_from_valid["other"] += r["clicks"]
        by_channel[r["channel"]] = by_channel.get(r["channel"], 0) + r["clicks"]
        by_date[r["date"]] = by_date.get(r["date"], 0) + r["clicks"]
        total += r["clicks"]
    return {
        "total": total,
        "by_slug": by_slug,
        "by_slug_channel": by_slug_channel,
        "by_from_valid": by_from_valid,
        "by_channel": by_channel,
        "by_date": by_date,
    }


def detect_anomalies(
    agg: dict, rules: dict, prev_week_by_slug: dict[str, int], active_slugs: list[str]
) -> list[dict]:
    warnings: list[dict] = []
    r = rules.get("rules", {})

    # from_valid_low_ratio
    rule = r.get("from_valid_low_ratio", {})
    if rule.get("enabled"):
        total_valid = agg["by_from_valid"]["true"] + agg["by_from_valid"]["false"]
        if total_valid >= rule.get("min_samples", 10):
            invalid_ratio = (agg["by_from_valid"]["false"] / total_valid) * 100
            if invalid_ratio > rule.get("threshold_pct", 15):
                warnings.append(
                    {
                        "severity": rule.get("severity", "medium"),
                        "message": rule.get("message", "").format(
                            ratio_pct=f"{invalid_ratio:.1f}",
                            min_samples=rule.get("min_samples", 10),
                        ),
                    }
                )

    # week_over_week_drop（slug単位）
    rule = r.get("week_over_week_drop", {})
    if rule.get("enabled"):
        for slug, prev in prev_week_by_slug.items():
            if prev < rule.get("min_prev_clicks", 5):
                continue
            curr = agg["by_slug"].get(slug, 0)
            drop_pct = ((prev - curr) / prev) * 100 if prev else 0
            if drop_pct >= rule.get("drop_pct", 50):
                warnings.append(
                    {
                        "severity": rule.get("severity", "high"),
                        "message": f"slug={slug}: 前週 {prev} → 今週 {curr}. "
                        + rule.get("message", "").format(drop_pct=f"{drop_pct:.0f}"),
                    }
                )

    # channel_ctr_skew（note vs akari）
    rule = r.get("channel_ctr_skew", {})
    if rule.get("enabled"):
        for slug in active_slugs:
            note_c = agg["by_slug_channel"].get((slug, "note"), 0)
            akari_c = agg["by_slug_channel"].get((slug, "akari"), 0)
            total = note_c + akari_c
            if total < rule.get("min_total_clicks", 10):
                continue
            if akari_c > 0 and note_c / max(akari_c, 1) < rule.get("skew_ratio", 0.5):
                warnings.append(
                    {
                        "severity": rule.get("severity", "medium"),
                        "message": rule.get("message", "").format(
                            slug=slug, skew_ratio=rule.get("skew_ratio", 0.5)
                        )
                        + f"（note={note_c}, akari={akari_c}）",
                    }
                )

    # active_zero_this_week（info レベル）
    rule = r.get("active_zero_this_week", {})
    if rule.get("enabled"):
        zero_slugs = [s for s in active_slugs if agg["by_slug"].get(s, 0) == 0]
        if zero_slugs:
            warnings.append(
                {
                    "severity": rule.get("severity", "info"),
                    "message": f"今週クリック0: {', '.join(zero_slugs)}",
                }
            )

    return warnings


def render_report(
    week_label: str, period: str, agg: dict, warnings: list[dict], active_slugs: list[str]
) -> str:
    severity_emoji = {"high": "🔴", "medium": "🟡", "info": "ℹ️"}
    lines = [
        f"# Redirect Metrics Report — {week_label}",
        "",
        f"対象期間: {period}",
        f"総クリック数: **{agg['total']}**",
        "",
    ]
    if warnings:
        lines.append("## ⚠️ 異常検知")
        for w in warnings:
            emo = severity_emoji.get(w["severity"], "•")
            lines.append(f"- {emo} **[{w['severity']}]** {w['message']}")
        lines.append("")
    else:
        lines.append("## 異常検知")
        lines.append("- 警告なし")
        lines.append("")
    lines.append("## slug別 クリック数")
    lines.append("")
    lines.append("| slug | clicks |")
    lines.append("| --- | --- |")
    for slug in active_slugs:
        clicks = agg["by_slug"].get(slug, 0)
        lines.append(f"| {slug} | {clicks} |")
    lines.append("")
    lines.append("## channel × slug マトリクス")
    lines.append("")
    channels = sorted(agg["by_channel"].keys()) or ["(no data)"]
    header = "| slug | " + " | ".join(channels) + " | total |"
    sep = "| --- | " + " | ".join("---" for _ in channels) + " | --- |"
    lines.append(header)
    lines.append(sep)
    for slug in active_slugs:
        cells = [str(agg["by_slug_channel"].get((slug, ch), 0)) for ch in channels]
        total = sum(agg["by_slug_channel"].get((slug, ch), 0) for ch in channels)
        lines.append(f"| {slug} | " + " | ".join(cells) + f" | {total} |")
    lines.append("")
    lines.append("## from_valid 内訳")
    lines.append("")
    fv_total = sum(agg["by_from_valid"].values())
    lines.append(f"- true: {agg['by_from_valid']['true']}")
    lines.append(f"- false: {agg['by_from_valid']['false']}")
    if fv_total > 0:
        ratio = (agg["by_from_valid"]["false"] / fv_total) * 100
        lines.append(f"- 不正比率: {ratio:.1f}%")
    lines.append("")
    lines.append("## 日別推移")
    lines.append("")
    for date_str in sorted(agg["by_date"].keys()):
        lines.append(f"- {date_str}: {agg['by_date'][date_str]}")
    if not agg["by_date"]:
        lines.append("- データなし")
    lines.append("")
    lines.append("---")
    lines.append(
        "生成: collect_redirect_metrics.py / 設計: docs/aiseo/phase_9_redirects_design.md"
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--days", type=int, default=7, help="集計期間（日数、既定7）")
    parser.add_argument(
        "--out", type=str, default=None, help="レポート出力先（既定: docs/redirect-reports/{YYYY-WW}.md）"
    )
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="GA4 を叩かず、空データでレポートだけ生成（CI スモークテスト用）",
    )
    args = parser.parse_args(argv)

    property_id = os.environ.get("GA4_PROPERTY_ID", "").strip()
    sa_key = os.environ.get("GA4_SERVICE_ACCOUNT_KEY", "").strip()

    redirects = load_yaml(REDIRECTS_YML)
    active_slugs = [e["slug"] for e in redirects["redirects"] if e.get("active")]
    rules = load_yaml(RULES_YML)

    now = datetime.now(JST)
    end = now.date()
    start = end - timedelta(days=args.days)
    period = f"{start.isoformat()} 〜 {(end - timedelta(days=1)).isoformat()} (JST)"
    week_label = iso_week_label(now)

    if args.no_fetch:
        rows: list[dict] = []
    else:
        if not property_id or not sa_key:
            print(
                "ERROR: GA4_PROPERTY_ID / GA4_SERVICE_ACCOUNT_KEY env vars required",
                file=sys.stderr,
            )
            return 2
        try:
            rows = fetch_ga4_rows(
                property_id,
                sa_key,
                start.isoformat(),
                (end - timedelta(days=1)).isoformat(),
            )
        except Exception as exc:
            print(f"ERROR: GA4 fetch failed: {exc}", file=sys.stderr)
            return 2

    agg = aggregate(rows)
    prev_week_clicks = load_prev_week_clicks()
    warnings = detect_anomalies(agg, rules, prev_week_clicks, active_slugs)

    report = render_report(week_label, period, agg, warnings, active_slugs)

    if args.out:
        out_path = Path(args.out)
    else:
        out_path = REPORTS_DIR / f"{week_label}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(report)
    try:
        rel = out_path.resolve().relative_to(REPO_ROOT)
    except ValueError:
        rel = out_path
    print(f"\n(report saved: {rel})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
