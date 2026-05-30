# Phase 10 設計 — 売上管理ツール（CVR算出）

## 背景

Phase 9（中継ページ+GA4）で「クリック数」は計測できるようになった。次は **CVR = 販売数 ÷ クリック数** を算出して、「note 側の貼り方が悪い」のか「行き先側の入口（売り文句・価格・LP）が悪い」のかを完全に切り分けたい。

そのために全チャネルの**販売実績を一元管理するスプレッドシート**と、**GA4 のクリック数を自動転記する同期スクリプト**を作る。

## 採用方式

**案B：Google Sheets + GA4 自動転記スクリプト**

- 売上情報そのもの（販売数・単価）は Google Sheets に**手入力**
- クリック数は GA4 から週次 cron で**自動転記**
- CVR は Sheets の `SUMIFS` 数式で自動計算
- リポには売上情報をコミットしない（秘匿）
- 既存 Phase 9 の Service Account（`akarilab-ga4-reader`）に Sheets API 権限を追加して認証一元化

## Sheets 構成（4 シート）

### Sheet 1: `sales_log`（手入力・売上ログ）

| 列 | 型 | 説明 |
|---|---|---|
| `date` | 日付 | 売上が立った日（YYYY-MM-DD） |
| `channel` | 文字列 | `brain` / `coconala` / `coconala_blog` / `note` / `hidamari` / `moyalog` / `repimemo` / `other` |
| `slug` | 文字列 | redirects.yml の slug と一致させる（例: `brain-1on1`, `coconala-line-shindan`）。中継URL を持たない直接販売の場合は `(none)` |
| `product_name` | 文字列 | 商品名（人間可読） |
| `quantity` | 整数 | 件数（通常 1） |
| `price` | 整数 | 単価（円） |
| `revenue` | 整数（計算列）| `=quantity * price` |
| `payment_date` | 日付 | 入金日（確定申告用） |
| `referrer_channel` | 文字列 | クリック元のチャネル（`note` / `x` / `akari` / `other`）。GA4 の `channel` と合わせる |
| `note` | 文字列 | 自由メモ |

### Sheet 2: `clicks_log`（自動転記・GA4 集計）

cron が週次で書き込む。`scripts/sync_clicks_to_sheets.py` の出力先。

| 列 | 型 | 説明 |
|---|---|---|
| `week` | 文字列 | ISO 週ラベル（YYYY-WW） |
| `slug` | 文字列 | redirects.yml の slug |
| `from` | 文字列 | 流入元記事スラグ |
| `channel` | 文字列 | `note` / `cocon` / `akari` / `x` / `other` / `unknown` |
| `clicks` | 整数 | クリック数 |
| `synced_at` | 日時 | 転記時刻（重複検知用） |

### Sheet 3: `cvr_summary`（自動計算・CVR算出）

SUMIFS で自動集計。スクリプトは触らない。

| 列 | 数式の例 |
|---|---|
| `slug` | 手動でslug一覧（または UNIQUE 関数）|
| `month` | 月（YYYY-MM）|
| `clicks_total` | `=SUMIFS(clicks_log!E:E, clicks_log!B:B, A2, ...)` |
| `sales_count` | `=SUMIFS(sales_log!E:E, sales_log!C:C, A2, ...)` |
| `revenue_total` | `=SUMIFS(sales_log!G:G, sales_log!C:C, A2, ...)` |
| `cvr_percent` | `=IFERROR(sales_count/clicks_total*100, 0)` |

### Sheet 4: `monthly_summary`（手動・グラフ用）

ピボットテーブル or 自由配置で、月別売上推移グラフを作る。チャネル別・slug別の比較。

## 同期スクリプト：`scripts/sync_clicks_to_sheets.py`

### 責務（最小）

1. GA4 Data API から直近1週間の `redirect_click` を取得
2. Google Sheets API で `clicks_log` シートを開く
3. 既存の `synced_at` 列を見て重複検知、未取得分だけ append
4. ログを stdout に出力

### 認証

- `GA4_SERVICE_ACCOUNT_KEY`（Phase 9 と同じ）
- 同じ SA に対して Sheets API を有効化し、対象 Sheets を「編集者」で共有
- 新しい環境変数: `SALES_TRACKER_SHEET_ID`（Sheets の URL から抽出）

### 実行

- Phase 9 の `redirect-metrics.yml` workflow の最後に追加ステップとして実行
- 週次月曜 09:00 JST
- 失敗してもメトリクスレポート生成は続行（dependent ではない）

## 触るファイル

### 新規

- `docs/aiseo/phase_10_sales_tracker_design.md`（本設計md）
- `scripts/sync_clicks_to_sheets.py`（同期スクリプト）
- `docs/aiseo/phase_10_sheets_setup_guide.md`（ユーザー手順書）

### 編集

- `.github/workflows/redirect-metrics.yml`（同期ステップ追加）

### 意図的に触らない

- `sales_log` / `cvr_summary` / `monthly_summary` のデータ（売上情報なのでリポに置かない）

## ユーザー手作業

1. 新規 Google Sheets を作成
2. 4 シート（`sales_log` / `clicks_log` / `cvr_summary` / `monthly_summary`）を作って列名を入れる
3. Service Account（`akarilab-ga4-reader@akarilab.iam.gserviceaccount.com`）を「編集者」で共有
4. GCP で Google Sheets API を有効化
5. Sheets ID（URL から抽出）を GitHub Secrets に `SALES_TRACKER_SHEET_ID` として登録
6. workflow_dispatch で手動初回実行 → 動作確認
7. 以降は週次cronで自動同期

## 想定リスクとカウンタ

| リスク | カウンタ |
|---|---|
| Sheets ID 漏洩 | URL は秘密扱い、Secrets 経由のみ |
| 同期失敗で sales_log が壊れる | スクリプトは clicks_log にしか書き込まない、sales_log は read-only |
| 重複行 | synced_at で検知、UPSERT ロジック |
| API クォータ | 週次1回呼び出しなので問題なし |
| 売上情報の改ざん | Sheets の編集履歴で追える |

## 履歴

- 2026-05-30: Phase 10 設計初版、Phase 9 と並列稼働開始
