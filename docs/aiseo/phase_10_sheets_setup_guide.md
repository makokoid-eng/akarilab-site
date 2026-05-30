# Phase 10 — 売上管理 Sheets セットアップ手順

## 目的

Phase 10 設計に従って Google Sheets を作成し、Phase 9 cron からの自動転記を受けられる状態にする。

設計: `phase_10_sales_tracker_design.md`

---

## ① Google Sheets を新規作成

[https://sheets.google.com/](https://sheets.google.com/) → 「空白」をクリック

ファイル名を「**AkariLab 売上管理（Phase 10）**」などに変更。

## ② 4 シートを作る + 列名コピペ

下部のシートタブを 4 つに増やす。それぞれ以下の列名を A1 行にコピペ：

### Sheet 1: `sales_log`

```
date	channel	slug	product_name	quantity	price	revenue	payment_date	referrer_channel	note
```

→ G2セル以降に `=E2*F2` の数式を入れる（売上自動計算）

### Sheet 2: `clicks_log`

```
week	slug	from	channel	clicks	synced_at
```

→ ここは触らない（cron が自動で書き込む）

### Sheet 3: `cvr_summary`

ヘッダ：
```
slug	month	clicks_total	sales_count	revenue_total	cvr_percent
```

数式の例（A2: `brain-1on1`、B2: `2026-06` を入れたあとに）：

| C2（clicks_total）| `=SUMIFS(clicks_log!E:E, clicks_log!B:B, A2)` |
| D2（sales_count）| `=SUMIFS(sales_log!E:E, sales_log!C:C, A2, sales_log!A:A, ">="&DATE(YEAR(B2&"-01"),MONTH(B2&"-01"),1), sales_log!A:A, "<"&EDATE(DATE(YEAR(B2&"-01"),MONTH(B2&"-01"),1),1))` |
| E2（revenue_total）| 同様に sales_log!G:G で SUMIFS |
| F2（cvr_percent）| `=IFERROR(D2/C2*100, 0)` |

→ 数式は最初の1行だけ書いて、下方向にコピーすればOK。

### Sheet 4: `monthly_summary`

ピボットテーブルでも、自由配置の集計表でもOK。

例：
- 行: 月（A列）
- 列: channel（B列以降）
- 値: revenue 合計

→ 挿入 → ピボットテーブル → データソース `sales_log!A:J`

## ③ Service Account を「編集者」で共有

Sheets 右上の「**共有**」ボタン：

- メールアドレス: `akarilab-ga4-reader@akarilab.iam.gserviceaccount.com`
- 役割: **編集者**
- 「通知メールを送信する」のチェックは外す（送れないので）

→ 「送信」

## ④ Google Cloud で Sheets API を有効化

[https://console.cloud.google.com/apis/library/sheets.googleapis.com?project=akarilab](https://console.cloud.google.com/apis/library/sheets.googleapis.com?project=akarilab) を開く → 「**有効にする**」

## ⑤ Sheets ID を取得

ブラウザの URL を見る：

```
https://docs.google.com/spreadsheets/d/【ここの長い文字列】/edit#gid=0
```

`/d/` と `/edit` の間にある長い文字列が **Sheets ID**。コピー。

## ⑥ GitHub Secrets に登録

[https://github.com/makokoid-eng/akarilab-site/settings/secrets/actions](https://github.com/makokoid-eng/akarilab-site/settings/secrets/actions) → 「**New repository secret**」

- Name: `SALES_TRACKER_SHEET_ID`
- Value: ⑤でコピーした Sheets ID

## ⑦ 動作確認（workflow_dispatch）

[https://github.com/makokoid-eng/akarilab-site/actions/workflows/redirect-metrics.yml](https://github.com/makokoid-eng/akarilab-site/actions/workflows/redirect-metrics.yml) → 「**Run workflow**」

実行後、ログで `Sync clicks to sales tracker sheet` ステップを確認：
- `header set: [...]` または `sheet 'clicks_log' created, header set`
- `N 行追加`

成功したら Sheets を開いて `clicks_log` シートにデータが入っていることを確認。

---

## 運用フロー

### 毎日 / 不定期
- 売上が発生したら `sales_log` シートに 1 行追加（手入力）

### 毎週月曜 09:00 JST（自動）
- cron が GA4 から `redirect_click` を集計
- `clicks_log` シートに追記
- `cvr_summary` シートが SUMIFS で自動更新（数式が走る）

### 月初確認
- `cvr_summary` を見て「先月のCVR」を slug 別に確認
- CVR < 1% の slug は note 側の貼り方を疑う
- CVR > 5% の slug は流入を増やす施策を考える

---

## トラブルシューティング

| 症状 | 対処 |
|---|---|
| `Permission denied` | ③ で SA を「編集者」で共有しているか確認 |
| `Sheets API has not been enabled` | ④ で API 有効化を確認 |
| `Range not found` | シート名が `clicks_log` と完全一致しているか（半角・大文字小文字） |
| `clicks_log` に何も入らない | GA4 にイベントがまだ無い可能性（中継ページを実際に踏んでから24時間待つ）|

---

## 履歴

- 2026-05-30: Phase 10 初版（akarilab-site/docs/aiseo/phase_10_sales_tracker_design.md と同時）
