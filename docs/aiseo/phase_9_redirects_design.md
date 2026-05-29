# Phase 9 設計 — クリック計測「中継ページ+GA4」

## 背景

note・akarilab.org 記事から外部商品（Brain / ココナラ / LINE Bot）への導線を多数貼っているが、クリック数が計測できておらず、Brain 0部・ココナラ販売0という結果に対し「note側の置き方が悪い」のか「Brain側の入口（売り文句）が悪い」のかを切り分けできない。

本フェーズでは、GitHub Pages 静的サイトのまま「中継ページ＋GA4」方式で計測基盤を構築する。

承認プラン: `C:\Users\user\.claude\plans\cryptic-sniffing-cerf.md`

## 採用方式

- akarilab.org/r/<slug>/ という中継ページ（静的HTML）を 7枚自動生成
- 各中継ページが GA4 にクリックイベント送信→外部サイトへリダイレクト
- 流入元識別: `?from=<記事スラグ>&ch=<チャネル>` で記事×商品×チャネル単位の集計可

## 単一情報源

- リダイレクト定義: `data/redirects.yml`
- 生成: `scripts/build_redirects.py`
- 中継ページ出力先: `r/<slug>/index.html`
- 共通 GA4 タグ: `assets/partials/head-common.html` に gtag.js を埋め、build_redirects.py が inline 展開

## CODEX レビュー反映の重要事項

CODEX レビュー（2026-05-29）で指摘された5点を設計に反映した：

1. **robots.txt の `Disallow: /r/` は入れない**
   - Disallow すると Googlebot が中継ページ内の meta noindex を読めなくなる
   - 参考: https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag
   - → `meta robots="noindex,nofollow"` のみで制御、sitemap.xml/llms.txt にも載せない

2. **`?from=` を `^[a-z0-9][a-z0-9_-]{0,80}$` で正規化**
   - 不正値は `unknown` に倒し、`from_valid: false` を GA4 に送信
   - XSS / PII 混入を弾く
   - 同様に `?ch=` も `['note','cocon','akari','x','other']` のホワイトリストで正規化、`channel=unknown` フォールバック

3. **GA4 に `dest_url` を送らない**
   - 送るのは `slug` / `from` / `from_valid` / `channel` / `dest_domain` / `category` の6つのみ
   - 割引コード（`?discount_code=8b74` 等）は GA4 計測画面に出さない

4. **build_pages.py には混ぜない**
   - build_redirects.py が head-common.html を読んで inline 展開、独立完結
   - 既存 TARGETS は一切触らない

5. **公開後の slug は immutable**
   - dest_url を変えたい場合は新 slug を切る（GitHub Pages の CDN キャッシュで古い行き先に飛ぶ事故防止）
   - 旧 slug は `active: false` にして物理削除はしない

## 3段防衛

中継ページHTMLは以下の優先順でリダイレクトする：

1. GA4 イベント `redirect_click` 送信（`transport_type:'beacon'` + `event_callback`）
2. `setTimeout(go, 500)` — 500ms 経っても callback が来なければ強制リダイレクト（保険）
3. `<meta http-equiv="refresh" content="2;url=...">` — JS 無効時のフォールバック
4. `<noscript>` テキストリンク — 最終防衛

リダイレクトは `window.location.replace(dest)` で履歴を汚さない（戻るボタンで note に戻れる）。

## GA4 イベント仕様

- イベント名: `redirect_click`
- パラメータ:
  - `slug` (string) — 中継ページ識別子（例 `brain-1on1`）
  - `from` (string) — 流入元記事スラグ（正規化済、不正は `unknown`）
  - `from_valid` (bool) — 正規表現マッチ成否
  - `channel` (string) — ホワイトリスト一致値、不正は `unknown`
  - `dest_domain` (string) — 集計用ドメイン
  - `category` (string) — `brain` / `coconala` / `line_bot`
- GA4 カスタムディメンション登録: 上記6つ全て（スコープ=イベント）

## ファイル一覧

### 新規

- `data/redirects.yml` — リダイレクト定義（7エントリ）
- `scripts/build_redirects.py` — 中継ページ生成器
- `scripts/list_redirect_targets.py` — 既存リンク検出ユーティリティ（書き換えはしない）
- `r/<slug>/index.html` × 7 — 自動生成
- `docs/aiseo/phase_9_redirects_design.md` — 本設計md
- `docs/redirect-reports/.gitkeep` — 週次レポート保管
- `scripts/redirect_anomaly_rules.yml` — 異常検知閾値
- `scripts/collect_redirect_metrics.py` — 週次 GA4 集計
- `.github/workflows/redirect-metrics.yml` — 月曜09:00 JST cron
- `~/.claude/skills/redirect-monitor/SKILL.md` — チャット呼び出しスキル

### 編集

- `assets/partials/head-common.html` — gtag.js 4-5行追記

### 意図的に触らない

- `robots.txt`（Disallow:/r/ は入れない、CODEX指摘の反映）
- `sitemap.xml` / `llms.txt`（中継ページは載せない）
- `scripts/build_pages.py` の TARGETS（混ぜない、CODEX指摘の反映）

## スラグ命名規則

`<channel>-<product>-<variant?>` の2〜3階層。

| slug | channel | product | 想定 |
|---|---|---|---|
| brain-1on1 | brain | 1on1 | 1on1・報告書・朝礼 AI実用例20選 |
| brain-mendan-template | brain | mendan-template | 面談まわり3時間→1.5時間 |
| coconala-line-shindan | coconala | line-shindan | 30分相談（業務改善Bot化判定） |
| coconala-soshiki-shindan | coconala | soshiki-shindan | 30分相談（評価制度型診断） |
| coconala-poc-1week | coconala | poc-1week | 1週間 PoC |
| line-moyalog | line | moyalog | もやログ友だち追加 |
| line-hidamari | line | hidamari | ひだまり友だち追加 |

## 自動観察（並行構築）

- 週次 cron で GA4 Data API から `redirect_click` を取得
- 集計次元: `channel × slug × from × dest_domain × 日付`
- 異常検知4種:
  - 3週連続クリック0 → 導線機能不全警告
  - `from_valid=false` 比率15%超 → 命名規則崩壊
  - 前週比 -50% → 導線破壊の疑い
  - channel間CTR乖離 → 特定チャネルの貼り方再考
- 出力: GitHub Issue (label: `redirect-report`) + `docs/redirect-reports/{YYYY-WW}.md`
- スキル `redirect-monitor` 経由でチャットから「導線どう？」で呼べる

## 想定外操作の防御

- redirects.yml で `active: false` のエントリ → build_redirects.py は HTML を新規生成しない（既存ファイルは保持）
- 旧 slug の `r/<slug>/index.html` は物理削除しない（note 過去公開済記事から踏まれた時の 404 防止）
- 中継ページの `from` パラメータは絶対に `dest_url` へ引き継がない（クエリ汚染防止）
