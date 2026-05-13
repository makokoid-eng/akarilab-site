# Phase 3 設計: 既存ページの JSON-LD 強化＋/hidamari/ 移設

## 目的

既存 `/` と `/hidamari.html` を Organization グラフに接続し、`/hidamari.html` を `/hidamari/index.html` に移設して将来のサブパス拡張に揃える。AI 検索エンジンの引用基盤に既存ページを取り込む。

## 触るファイル

### 新規

- `hidamari/index.html` — 既存 `hidamari.html` の本文・スタイル・画像参照を引き継いだ移設先。SoftwareApplication / BreadcrumbList JSON-LD を追加。
- `assets/partials/jsonld/software-application-hidamari.html` — SoftwareApplication ひだまり JSON-LD partial（`producer` / `publisher` を `https://akarilab.org/#org` に向ける）
- `docs/aiseo/phase_3_design.md` — 本ファイル

### 更新

- `index.html` — `</head>` 直前に Organization 参照（`{"@type":"Organization","@id":"https://akarilab.org/#org"}` の短縮参照）／ItemList（プロダクト3件）／BreadcrumbList（ホーム position 1）の3つの JSON-LD を追加。本文・スタイルは触らない。
- `hidamari.html` — meta refresh で `/hidamari/` にリダイレクト、本文は最小限の移設案内のみ、JSON-LD なし、`noindex` 付与。
- `tokushoho.html` / `billing-policy.html` / `terms-of-service.html` / `privacy-policy.html` — `</head>` 直前に BreadcrumbList JSON-LD のみ追加（ホーム → 該当規約ページ）。本文・スタイルは触らない。
- `sitemap.xml` — `/hidamari.html` を `/hidamari/` に置換（lastmod を 2026-05-13 に、priority 0.9 維持）
- `llms.txt` — `/hidamari.html` を `/hidamari/` に置換
- `scripts/build_pages.py` — `TARGETS` リスト末尾に `hidamari/index.html` を追加

## 触らないファイル

- `akarilab/` 配下（Phase 2 完了済）
- `makoto/` 配下（Phase 2 完了済）
- `assets/css/` / `assets/logo/` / `assets/partials/{head,footer}-common.html`
- `assets/partials/jsonld/organization.html` / `assets/partials/jsonld/person.html`
- `robots.txt` / `.nojekyll` / `CNAME`
- `.github/workflows/aiseo-check.yml`
- `scripts/aiseo_check_alt.py` / `scripts/aiseo_check_sitemap.py`
- 他リポすべて（hidamari/moyalog/repimemo/makochinta1-poster/akarilab-note）

## 実装手順

1. SoftwareApplication ひだまり partial を `assets/partials/jsonld/software-application-hidamari.html` に作成
2. `hidamari/index.html` を作成：既存 `hidamari.html` の本文・スタイル・画像参照をそのまま引き継ぎ、`<title>` / `<meta description>` / `og:url` / `canonical` を `/hidamari/` に更新、SoftwareApplication partial を include、BreadcrumbList を直書き
3. 既存 `hidamari.html` を meta refresh + 移設案内のみに置換（JSON-LD なし、`noindex`）
4. 既存 `index.html` の `</head>` 直前に Organization 短縮参照／ItemList／BreadcrumbList の3 JSON-LD を追加（既存 `<style>` ブロック・本文には触らない）
5. 規約4ページの `</head>` 直前に BreadcrumbList JSON-LD のみ追加（既存 `<style>` ブロック・本文には触らない）
6. `sitemap.xml` の `/hidamari.html` を `/hidamari/` に置換、lastmod を 2026-05-13 に
7. `llms.txt` の `/hidamari.html` を `/hidamari/` に置換
8. `scripts/build_pages.py` の `TARGETS` 末尾に `hidamari/index.html` を追加
9. ローカルで以下を実行し、すべて exit 0 を確認：
   - `python scripts/build_pages.py --check`
   - `python scripts/aiseo_check_alt.py`
   - `python scripts/aiseo_check_sitemap.py`
10. CODEX 設計レビュー（メインエージェント側）→ 反映
11. CODEX コードレビュー（メインエージェント側）→ 反映
12. commit（メインエージェント側で実施）

## グラフ設計

### SoftwareApplication ひだまり

- `@id`: `https://akarilab.org/hidamari/#app`
- 一次定義ページ: `/hidamari/index.html`
- `producer` / `publisher`: `{ "@id": "https://akarilab.org/#org" }`（短縮参照）
- `applicationCategory`: `EducationalApplication`
- `operatingSystem`: `LINE`
- `audience.educationalRole`: `student`
- `featureList`: つまずき遡行 / 答えを教えないソクラテス対話 / 先生選択（そうま・かいと）/ 実力チェック診断
- `url`: `https://akarilab.org/hidamari/`

### Organization 短縮参照（index.html）

`/akarilab/` でフル定義した Organization を、`/` でも短縮参照だけ置く。これにより `/` を入口にしたクローラがグラフ中心ノードへ即座に到達できる。

```jsonld
{ "@context": "https://schema.org", "@type": "Organization", "@id": "https://akarilab.org/#org" }
```

### ItemList（index.html、プロダクト一覧）

`/`（AkariLab トップ）に表示されている3プロダクト（ひだまり／もやログ／りぴメモ）を ItemList で表現。各 item は SoftwareApplication 相当の URL を指す。Phase 4 で moyalog/repimemo の LP が新設されたら、この ItemList の item 値を `/moyalog/` `/repimemo/` に差し替える（本フェーズでは現行の lin.ee URL のまま）。

### BreadcrumbList（各ページ）

- `/` （index.html）: ホーム position 1 のみ（最上位）
- `/hidamari/` (hidamari/index.html): ホーム → ひだまり
- 規約4ページ: ホーム → 該当規約ページ

## meta refresh による旧 URL 退避

GH Pages では server-side リダイレクトが使えないため、meta refresh で代替する。

```html
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="0; url=/hidamari/">
<link rel="canonical" href="https://akarilab.org/hidamari/">
<title>移設しました — ひだまり | AkariLab</title>
<meta name="robots" content="noindex">
</head>
<body>
<p>このページは <a href="/hidamari/">https://akarilab.org/hidamari/</a> に移設しました。</p>
</body>
</html>
```

- `noindex` を付けて Sitemap からも除外（sitemap.xml の `/hidamari.html` は `/hidamari/` に置換）
- 既存被リンク（外部 SNS／note 記事内リンク）からの流入は meta refresh で 0 秒遷移
- canonical を `/hidamari/` に向けることで重複コンテンツ評価を新 URL に集約

## ココナラ表現ルール厳守

本フェーズで触る既存 `index.html` には既に「外食チェーンで21年現場に立ち続けている店長／エリアマネージャー」という表現が含まれているが、これは「触らないファイル」範囲（既存本文）なので Phase 3 の編集対象外。本フェーズで追加する JSON-LD には会社名・店舗ブランド名は一切含めない。

## ブランド分離チェック

- `index.html` の ItemList はプロダクト名と URL のみ並列、各プロダクトの世界観文言を持ち込まない（既存本文の product-card desc は触らない）
- `/hidamari/index.html` 本文は既存 `hidamari.html` のひだまり世界観を完全に保つ（もやログ・りぴメモ並列言及は許容範囲、設計md L31 準拠：サブパス配置と JSON-LD 接続は趣旨を破らない）
- `/hidamari/index.html` の footer に既存の「もやログ」リンク（`https://makokoid-eng.github.io/moyalog-site/`）が残っている → これは既存 hidamari.html を引き継ぐため Phase 3 範囲では維持。Phase 4 の moyalog LP 公開時に `/moyalog/` への張り替えを検討。

## 個人名露出チェック

- 既存 `index.html` の「外食チェーンで21年現場に立ち続けている店長／エリアマネージャー」は職務カテゴリ表現で個人名「まこと」露出ではない（既存本文・触らない）
- 本フェーズで追加する JSON-LD（Organization 短縮参照／ItemList／BreadcrumbList／SoftwareApplication）に個人名「まこと」は含めない
- 移設後の `/hidamari/index.html` 本文も既存 hidamari.html を引き継ぐため個人名露出なし
- meta refresh 用の `hidamari.html` 退避ページにも個人名なし
- 規約4ページに追加する BreadcrumbList にも個人名なし

## JSON-LD dead link チェック

- `index.html` の Organization 短縮参照 `https://akarilab.org/#org` → `/akarilab/index.html` の Organization フル定義（`@id` 一致）に到達 ✓
- `index.html` の ItemList の3 item URL：
  - `https://akarilab.org/hidamari/` → 本フェーズで新設 ✓
  - `https://lin.ee/q1k7v8F`（もやログ）→ 外部・実在 ✓
  - `https://lin.ee/HbV7Ehv`（りぴメモ）→ 外部・実在 ✓
- `/hidamari/` の SoftwareApplication.producer / publisher `https://akarilab.org/#org` → `/akarilab/` の Organization に到達 ✓
- 各ページの BreadcrumbList の item URL がすべて実在（ホーム `/` ／規約4ページ ／ `/hidamari/`）✓
- og:image は当面 `/assets/logo/hidamari_icon_256.png` を使用（実ファイル存在）

## CODEX 設計レビュー結果

未実施（メインエージェント側で本設計md を CODEX に渡してレビュー予定）。

## CODEX コードレビュー結果

未実施（メインエージェント側で実装後 CODEX に渡してレビュー予定）。

## 完了条件

- `hidamari/index.html` が新規作成済み（既存 hidamari.html の本文・スタイル・画像参照を引き継ぎ、JSON-LD 2種を追加）
- `hidamari.html` が meta refresh + 移設案内のみに置換済み（JSON-LD なし、noindex）
- `index.html` の `</head>` 直前に Organization 短縮参照／ItemList／BreadcrumbList の3 JSON-LD が追加済み（本文・スタイル無変更）
- 規約4ページの `</head>` 直前に BreadcrumbList JSON-LD が追加済み（本文・スタイル無変更）
- `sitemap.xml` から `/hidamari.html` が消え `/hidamari/` に置換済み、lastmod 2026-05-13
- `llms.txt` から `/hidamari.html` が消え `/hidamari/` に置換済み
- `scripts/build_pages.py` の TARGETS 末尾に `hidamari/index.html` 追加済み
- 以下3スクリプトすべて exit 0：
  - `python scripts/build_pages.py --check`
  - `python scripts/aiseo_check_alt.py`
  - `python scripts/aiseo_check_sitemap.py`
- 個人名「まこと」が新規・既存編集ファイルに露出ゼロ（grep でゼロ確認）
- CODEX レビューの「強い懸念」がゼロ件 or 全件 ADR 化されている
