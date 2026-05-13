# Phase 1 設計: サイト基盤整備

## 目的

以降のフェーズで増えるページのための共通基盤（partial / CSS / robots / sitemap / llms.txt / .nojekyll / canonical 方針 / CI）を整え、AI クローラに「クロール歓迎」を明示する。既存6ページの見た目は変えない。

## 触るファイル

### 新規

- `scripts/build_pages.py` — partial 置換のみのワンファイル Python（`<!-- include: assets/partials/xxx.html -->` を物理 include する単純置換）
- `assets/css/site.css` — 共通 CSS（`:root` 変数の共通部分のみ抽出。テーマ別の `--accent` 系は各ページが上書きする想定）
- `assets/partials/head-common.html` — meta charset / viewport / preconnect / Google Fonts
- `assets/partials/footer-common.html` — 共通フッター（規約4本＋AkariLab note リンクの既存形式踏襲）
- `assets/partials/jsonld/` — JSON-LD テンプレ集（Phase 2 以降に実装、空ディレクトリのみ）
- `sitemap.xml` — 既存6ページのみ列挙、新規ページは各 Phase で追記
- `robots.txt` — AI クローラ allowlist + sitemap 参照
- `llms.txt` — 簡易サイトマップ＋ブランド注記（既存ページ向け）
- `.nojekyll` — GH Pages の Jekyll 抑止
- `.github/workflows/aiseo-check.yml` — CI（HTML5 検証、リンクチェック、画像 alt 検査、JSON-LD 検証）
- `docs/aiseo/phase_1_design.md` — 本ファイル

### 既存

- 既存6ページ（index.html / hidamari.html / 規約系4枚）は **Phase 1 では一切編集しない**。partial 置換への移行は Phase 2 以降の新規ページから適用し、既存書き換えは「同等変換」が機械検証できる目処が立ってから段階的に進める。

## 触らないファイル

- `index.html` / `hidamari.html` / `tokushoho.html` / `billing-policy.html` / `terms-of-service.html` / `privacy-policy.html`：本フェーズでは見た目変えない、テキストも触らない
- `assets/logo/`：ロゴ素材は触らない
- `CNAME`：触らない

## 実装手順

1. `.nojekyll` 作成（空ファイル）
2. `robots.txt` 作成（下記方針）
3. `llms.txt` 作成（下記方針）
4. `sitemap.xml` 作成（既存6ページのみ列挙、`<lastmod>` は git のコミット日時から自動取得する案もあるが、Phase 1 は手書きで固定）
5. `assets/partials/head-common.html` / `assets/partials/footer-common.html` 作成（Phase 2 以降の新規ページ用テンプレ）
6. `assets/css/site.css` 作成（共通部分のみ、`:root` の共通変数のみ。テーマ別変数は各ページが上書き）
7. `scripts/build_pages.py` 作成（partial include 置換のみ、冪等動作）
8. `.github/workflows/aiseo-check.yml` 作成（HTML5 / リンクチェック / alt / JSON-LD）
9. CI を一度 main で走らせて green を確認

## robots.txt 方針

```
User-agent: *
Allow: /

# OpenAI（学習系）
User-agent: GPTBot
Allow: /

# OpenAI（ChatGPT 検索系・AISEO の本命）
User-agent: OAI-SearchBot
Allow: /

# Anthropic（学習系）
User-agent: ClaudeBot
Allow: /

# Anthropic（Claude 検索系・AISEO の本命）
User-agent: Claude-SearchBot
Allow: /

# Anthropic（Claude ユーザー要求型）
User-agent: Claude-User
Allow: /

# Perplexity
User-agent: PerplexityBot
Allow: /

# Google（生成 AI への学習許可）
User-agent: Google-Extended
Allow: /

# Common Crawl（多くの LLM の学習素材源）
User-agent: CCBot
Allow: /

# Apple（Apple Intelligence 学習許可）
User-agent: Applebot-Extended
Allow: /

# ByteDance（注：robots.txt 尊重に疑義あり、低信頼）
User-agent: Bytespider
Allow: /

Sitemap: https://akarilab.org/sitemap.xml
```

注：
- AISEO の目的は「学習許可」より「検索・回答で引用される」こと。検索系 bot（OAI-SearchBot / Claude-SearchBot / Claude-User / PerplexityBot）の明示が本命。
- Bytespider は robots.txt を尊重しないという報告があるため allowlist に入れる意味は薄いが、明示しておく。
- CODEX レビュー時に 2026-05 時点の最新動向を再確認する。

## llms.txt 方針

```
# AkariLab

> 現場の「困った」から生まれた LINE Bot 群を運営するブランド。
> 個別プロダクト（ひだまり／もやログ／りぴメモ）はそれぞれ独立した世界観で運営される。

## Brand
- /                    AkariLab トップ
- /hidamari.html       ひだまり（学習 Bot、開発中）

## Articles
- https://note.com/akarilab  note メディア

(Phase 2 以降で /akarilab/ /makoto/ /moyalog/ /repimemo/ /articles/ を追記)
```

llms-full.txt は初期不要、CODEX 7 で確認済（補強案 §17）。

## sitemap.xml 方針

Phase 1 時点では既存6ページのみ列挙：
- https://akarilab.org/
- https://akarilab.org/hidamari.html
- https://akarilab.org/tokushoho.html
- https://akarilab.org/billing-policy.html
- https://akarilab.org/terms-of-service.html
- https://akarilab.org/privacy-policy.html

`<priority>` / `<changefreq>` は Google で重視されないが、整理目的で付与。
Phase 2 以降の新規ページは各フェーズの完了条件に「sitemap.xml への追記」を含める。

### 将来課題（CODEX 設計レビュー反映）

`<lastmod>` は手書き固定だと更新漏れが起きる。Phase 2 以降のページが増えたタイミングで `build_pages.py` または別スクリプトに `lastmod` 自動生成（git の最終コミット日時から算出）を組み込む。Phase 1 では導入しない（範囲拡大を避けるため）。

## canonical / noindex 方針

- **規約系4ページ**：canonical = 自 URL、noindex なし
- **index.html / hidamari.html**：canonical = 自 URL、noindex なし
- **将来の Article 要約ハブ（Phase 5）**：canonical = 自 URL（akarilab.org/articles/...）。`mainEntityOfPage` と `isBasedOn` で note 原文を参照するが canonical 自体は自 URL（要約ハブは独立したオリジナル要約コンテンツ）
- **将来の moyalog/repimemo LP（Phase 4）**：canonical = 自 URL
- **noindex を付けるページは現時点ではゼロ**。将来 store サブパスの伏線退避ページなどで必要になれば該当 Phase で追加

### URL 移行時の手順（CODEX 設計レビュー反映）

`/hidamari.html` → `/hidamari/` の移行（Phase 3）では以下を**同一 commit で同時に実行**：
- 旧 URL に meta refresh（GH Pages の制約）または自 URL canonical だけ残す
- sitemap.xml の URL を新 URL に置換
- llms.txt の参照 URL を新 URL に置換
- robots.txt は影響なし
- 内部リンク（index.html などからのリンク）を新 URL に置換

## CI（aiseo-check.yml）方針

GitHub Actions on push（main / PR）で以下を実行。**Phase 1 では「fail で止める」検査と「warning で記録するだけ」検査を分け、段階導入する**（CODEX 設計レビュー反映）：

### Phase 1 から fail で止める検査

1. **HTML5 バリデーション**：`html5validator`（既存6枚＋新規ページ全て）
2. **内部リンクチェック**：`lychee --internal-only`（外部はレート制限のため Phase 1 では除外）
3. **画像 alt 検査**：`pyquery` または `bs4` で `<img>` 要素を全件走査、alt 属性なしを fail
4. **sitemap 整合**：sitemap.xml に列挙された URL と実ファイルパスの突合（規約4枚＋index＋hidamari）

### Phase 1 から warning（fail にしない、ログのみ）

5. **JSON-LD 検証**：`<script type="application/ld+json">` が**存在する場合のみ**、`pyld` で抽出 → `jsonschema` で必須フィールド検証 → @id 参照先存在チェック。Phase 1 時点では新規ページに JSON-LD が無いため検査対象ゼロ。Phase 2 以降で必須化。
6. **画像 width / height 属性**：既存6ページに付いていない可能性が高いため Phase 1 は warning。Phase 4（LP 画像追加）で必須化。
7. **og:image / og:type / Twitter Cards / canonical / meta description / favicon / logo 実在**：Phase 1 から検査対象に入れるが、既存ページの未設定は warning にとどめる。新規ページ（Phase 2 以降）は fail で止める。

### Phase 2 以降で必須化（fail に昇格）

- JSON-LD 検証（Phase 2 から）
- 画像 width/height（Phase 4 から）
- og 系メタ（Phase 2 から）

CI 失敗時は main へのマージブロック（GitHub の branch protection で設定、本フェーズの範囲外）。

## ブランド分離チェック

Phase 1 は既存ページを触らないため、ブランド分離違反のリスクは低い。ただし、新規追加ファイルで以下を確認：

- `llms.txt` 本文に「ひだまり」「もやログ」「りぴメモ」を並列言及してよいか確認：**llms.txt はメタ情報なので並列言及 OK**。LP 本文ではないので feedback_brand_isolation の対象外。
- `sitemap.xml` には URL のみ。ブランド分離違反なし。
- `robots.txt` / `.nojekyll` は影響なし。

## 個人名露出チェック

Phase 1 は個人名「まこと」を出すページを作らない。新規追加ファイル全てで「まこと」grep がゼロを確認する。

## JSON-LD dead link チェック

Phase 1 では JSON-LD ブロックは実装しない（テンプレディレクトリだけ用意）。CI の JSON-LD 検証は Phase 2 以降の実装に備えた整備のみ。

## build_pages.py 設計補足（CODEX 設計レビュー反映）

- **include パス制限**：repo root 配下のみ許可。`..`、絶対パス、外部 URL の include は禁止（path traversal 防止）。
- **エスケープ方針**：HTML エスケープはしない（テンプレ include なので）。入力ファイルは信頼済み partial のみに限定する。partial 以外のファイルは include 対象に含めない。
- **動作モード**：
  - 通常モード：partial を物理 include して上書き保存
  - `--dry-run`：何が変わるかだけ stdout に出力、ファイルは触らない
  - `--check`：CI 用、現状ファイルが build 結果と一致するか検証（不一致なら non-zero exit）
- **冪等性担保**：連続2回実行で diff ゼロ
- **既存6ページの自動上書き禁止**：Phase 1 では既存6ページを include 形式に変換しない。`build_pages.py` の処理対象リストは partial に依存する新規ページのみ（Phase 1 時点では処理対象ゼロ、空走行で OK）。

## og:image 方針（CODEX 設計レビュー反映）

- Phase 1 時点では AkariLab 共通 OGP 画像（akarilab.org/assets/og.png）は placeholder（既存の hidamari 寄り画像を流用 or 空）。
- Phase 2（/akarilab/）で正式な AkariLab ブランド OGP 画像を作成して差し替え。
- Phase 4（moyalog/repimemo LP）で各プロダクト専用 og.png を新規作成（1200x630、200KB 以下）。

## CODEX 設計レビュー結果

2026-05-13 実施。総評「Phase 1 設計は大筋 OK、ただし robots.txt と CI 範囲、canonical 方針は少し直した方が安全」。

| # | CODEX 指摘 | 反映先 | 状態 |
|---|---|---|---|
| 1 | `robots.txt` に `OAI-SearchBot` / `Claude-SearchBot` / `Claude-User` を追加（検索系 bot が AISEO の本命） | robots.txt 方針セクション全面改訂 | 反映済 |
| 2 | Bytespider に「低信頼」注記 | robots.txt 方針セクション末尾の注 | 反映済 |
| 3 | CI の JSON-LD 検査は「存在する場合のみ」、Phase 1 では fail にせず Phase 2 以降必須化 | CI セクションを「fail で止める / warning」に分割 | 反映済 |
| 4 | CI の画像 width/height 検査は Phase 4 まで warning | CI セクションに段階導入を明記 | 反映済 |
| 5 | CI から og:image / Twitter Cards / canonical / meta description / favicon を検査対象に入れる（既存は warning、新規は fail） | CI セクションに追加 | 反映済 |
| 6 | sitemap.xml の `lastmod` 自動化を将来課題として記録 | sitemap.xml セクションに「将来課題」追記 | 反映済 |
| 7 | `/hidamari.html` → `/hidamari/` 移行時の同時切替手順を明記 | canonical セクションに「URL 移行時の手順」追記 | 反映済 |
| 8 | build_pages.py に path traversal 防止と dry-run/check モード追加 | 「build_pages.py 設計補足」セクション新設 | 反映済 |
| 9 | og:image は Phase 1 では placeholder、Phase 2 で正式画像 | 「og:image 方針」セクション新設 | 反映済 |
| 10 | manifest.json / RSS / Cache-Control / hreflang は Phase 1 範囲外（後続 Phase） | 既に Phase 1 設計に含まれていない／hreflang は llms.txt セクション周辺で言及済 | OK（追加対応なし） |

## CODEX コードレビュー結果

2026-05-13 実施。総評「Phase 1 commit は『CI 対象範囲修正』と『footer のもやログリンク整理』を入れてからが安全」。指摘 7 項目、すべて反映または対応決定済。

| # | CODEX 指摘 | 対応 | 状態 |
|---|---|---|---|
| 1 | CI の HTML5 / lychee が `assets/partials/*.html` を拾うと HTML 断片で fail する | html5validator は `--blacklist assets docs scripts .github`、lychee は `--exclude-path assets/partials/ docs/ scripts/` を追加 | 反映済 |
| 2 | footer-common.html の「もやログ」可視リンクは将来 LP で誤 include したらブランド分離違反 | 「もやログ」リンクを削除、AkariLab サイト全体で使える中立フッター（規約4本＋note＋IG）に整理。Phase 4 LP では専用フッターを別途用意 | 反映済 |
| 3 | sitemap.xml の hidamari priority が 0.8 → ユーザー仕様 0.9 とブレ | hidamari priority を 0.9 に修正 | 反映済 |
| 4 | build_pages.py：Windows 絶対パス（`C:/foo`）拒否を追加 | `is_safe_partial_path` に `Path(rel_path).is_absolute()` チェック追加 | 反映済 |
| 5 | build_pages.py：未処理 include marker 残存検出を追加（include だけで include-end が無い等） | `assert_no_unprocessed_marker` 関数を新設、main の各 path 処理で呼ぶ | 反映済 |
| 6 | phase_1_design.md「新規ファイル 9 種」が実装の 13 種とズレ | 完了条件を 13 種に修正 | 反映済 |
| 7 | ChatGPT-User / Perplexity-User の追加（任意） | 設計書に「意図して未追加」と明記（user fetcher は robots.txt を尊重しない説明があるため必須ではない） | 反映済 |

備考：
- 「Phase 2 で TARGETS に最初のページを入れる時、壊れた marker の検査も活用」（CODEX 指摘）→ 対応 5 で実装済
- 「Phase 2 で JSON-LD を `jsonschema` か型別 validator に昇格」→ Phase 2 設計md で対応
- 「公開 HTML 対象リストをスクリプト化」→ Phase 2 で必要になったタイミングで `scripts/aiseo_targets.py` 等として切り出す（現状は CI workflow 内の bash で十分）

## ChatGPT-User / Perplexity-User の扱い（CODEX レビュー反映）

- `ChatGPT-User` と `Perplexity-User` は user fetcher（ユーザーの会話起点で個別 URL を取りに行く）であり、一般に robots.txt の allowlist を尊重しないと公式説明されている。
- そのため robots.txt に明示的に書く実利は薄い。本フェーズでは未追加とする。
- 将来、両社が user fetcher も robots.txt 尊重に変更した場合は追記する。

## 完了条件

新規ファイル 13 種が main にマージ済み：
- `.nojekyll`
- `robots.txt`
- `sitemap.xml`
- `llms.txt`
- `assets/css/site.css`
- `assets/partials/head-common.html`
- `assets/partials/footer-common.html`
- `assets/partials/jsonld/.gitkeep`
- `scripts/build_pages.py`
- `scripts/aiseo_check_alt.py`
- `scripts/aiseo_check_sitemap.py`
- `.github/workflows/aiseo-check.yml`
- `docs/aiseo/phase_1_design.md`

その他：
- 既存6ページの diff がゼロ（見た目変化なし、内容変化なし）
- `python scripts/build_pages.py --check` が冪等動作（TARGETS 空のため scanned 0 files で OK）
- `python scripts/build_pages.py --dry-run` が冪等動作
- `python scripts/aiseo_check_alt.py` が OK（既存6ページの全 `<img>` に alt あり）
- `python scripts/aiseo_check_sitemap.py` が OK（sitemap 6 entries all resolved）
- `https://akarilab.org/sitemap.xml` / `/robots.txt` / `/llms.txt` / `/.nojekyll` が GH Pages 反映後に 200 で返る
- aiseo-check.yml が main で全件 green
- CODEX レビューの「強い懸念」がゼロ件 or 全件 ADR 化されている（設計レビュー 10 項目／コードレビュー 7 項目すべて対応済）
