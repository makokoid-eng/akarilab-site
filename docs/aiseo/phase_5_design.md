# Phase 5 設計：/articles/ 連載ハブ＋個別要約ハブ

## 目的

note 記事のうち主要なもの、特に 2026-05-17 開始の連載「触り始めて9ヶ月の記録」を Article 構造化し、Organization グラフに接続する。本フェーズでは構造とテンプレを設置し、第1話の本番 note URL は 5/17 公開後に `sync_note_articles.py` が取り込む流れにする。

## 触るファイル

### 新規

- `articles/index.html` — 全主要記事 ItemList ハブ（連載カード＋BreadcrumbList）
- `articles/ai-9months/index.html` — 連載親 Article + hasPart（連載開始日 2026-05-17）
- `articles/ai-9months/dev-log-01.html` — 第1話プレースホルダー（要約 + JSON-LD + note 原文リンク。本番 URL 確定までは「公開予定」マーク付き）
- `scripts/sync_note_articles.py` — note URL リスト → 要約ハブ HTML 生成スクリプト（note-poster ログと note RSS の二経路）
- `data/articles.yml` — 記事メタの単一情報源（series / slug / title / note_url / published / summary / position）
- `docs/aiseo/phase_5_design.md` — 本ファイル

### 更新

- `sitemap.xml` — `/articles/`, `/articles/ai-9months/`, `/articles/ai-9months/dev-log-01.html` を追加
- `llms.txt` — `## Articles` セクションに `/articles/` `/articles/ai-9months/` を追加
- `scripts/build_pages.py` — `TARGETS` に articles ページ 3 件を追加

### 触らない

- 既存 6 ページ（`/`, `/akarilab/`, `/makoto/*`, `/hidamari/`）
- `moyalog/`, `repimemo/`, `akarilab/`, `makoto/`, `hidamari/` 配下
- `assets/`, `robots.txt`, `.nojekyll`
- `.github/workflows/aiseo-check.yml`（Phase 5 では JSON-LD warning → fail 昇格は別途検討、本フェーズでは触らない）
- 他リポすべて

## 要約ハブ方針（00_overall_design.md L487-492 準拠）

- 全文転載しない、要約 500 字 + JSON-LD + note 原文へのリンクのみ
- 有料記事は「タイトル + 公開日 + 1段落要約のみ」に固定
- canonical を**自 URL**にする（要約ハブはオリジナル要約コンテンツ）
- `mainEntityOfPage` を note URL に固定（重複コンテンツ判定回避）
- `isBasedOn` を note URL に設定（参照元の明示）

## 連載親 Article JSON-LD

`articles/ai-9months/index.html` に配置：

```jsonld
{
  "@type": "Article",
  "@id": "https://akarilab.org/articles/ai-9months/#series",
  "headline": "触り始めて9ヶ月の記録",
  "datePublished": "2026-05-17",
  "author": { "@id": "https://akarilab.org/#org" },
  "publisher": { "@id": "https://akarilab.org/#org" },
  "abstract": "44歳でほぼ未経験から個人開発を始めた人間が、最初の9ヶ月で何に触れて、何に詰まって、何を作ったかを時系列で残す連載。",
  "hasPart": [
    { "@type": "Article", "@id": "https://akarilab.org/articles/ai-9months/dev-log-01/#article" }
  ]
}
```

## 個別記事 Article JSON-LD（dev-log-01）

第1話の本番 note URL が未確定の段階では、`mainEntityOfPage` / `isBasedOn` を `https://note.com/akarilab/n/PLACEHOLDER_TBD_AFTER_PUBLISH` として、5/17 に `sync_note_articles.py` で更新する。

```jsonld
{
  "@type": "Article",
  "@id": "https://akarilab.org/articles/ai-9months/dev-log-01/#article",
  "headline": "（第1話、2026-05-17 公開予定）",
  "datePublished": "2026-05-17",
  "author": { "@id": "https://akarilab.org/#org" },
  "publisher": { "@id": "https://akarilab.org/#org" },
  "isPartOf": { "@id": "https://akarilab.org/articles/ai-9months/#series" },
  "isBasedOn": "https://note.com/akarilab/n/PLACEHOLDER_TBD_AFTER_PUBLISH",
  "mainEntityOfPage": "https://note.com/akarilab/n/PLACEHOLDER_TBD_AFTER_PUBLISH",
  "abstract": "（連載第1話。2026-05-17 公開予定。本番公開後に sync_note_articles.py が要約を取得して更新。）"
}
```

## sync_note_articles.py 仕様

### 入力
- `data/articles.yml`（単一情報源）
- 経路 A：`C:/Users/user/akarilab-note/data/note_post_success_{date}.json`（note-poster の投稿成功ログ）
- 経路 B（RSS fallback）：`https://note.com/akarilab/rss`

### 処理
1. `data/articles.yml` を読み込む
2. note-poster 出力（経路 A）を走査し、URL 確定済み記事を articles.yml に反映
3. RSS（経路 B）を取得し、未掲載記事をマッチング（記事タイトルでマッチ → 該当 slot の `note_url` / `published` / `summary` を更新）
4. articles.yml を上書き保存
5. 後段の `build_pages.py` が articles.yml から `articles/ai-9months/{slug}.html` を再生成（本フェーズでは要約 HTML テンプレを直書きで設置、自動再生成は次フェーズで対応）

### マッチング戦略
- 経路 A：JSON 内の `slug` または `note_url` が articles.yml の slot と一致 → 上書き
- 経路 B：RSS の `<title>` が articles.yml の slot の `match_title` と部分一致（プレースホルダー時）→ `note_url` / `published` を反映
- 二重起票防止：既に `note_url` がプレースホルダーでない slot は経路 B で上書きしない

### CLI
```
python scripts/sync_note_articles.py            # 通常実行（articles.yml 更新）
python scripts/sync_note_articles.py --dry-run  # 何が変わるか stdout 出力、ファイル不変
python scripts/sync_note_articles.py --no-rss   # RSS fallback を skip（note-poster ログのみ）
python scripts/sync_note_articles.py --no-log   # note-poster ログを skip（RSS のみ）
```

### 依存
- Python 3.10+
- 標準ライブラリ + `pyyaml`（必須） + `requests`（RSS fallback で使用、`--no-rss` 時は不要）

### エラーハンドリング
- `articles.yml` が存在しない → exit 2 with message
- note-poster ログディレクトリが存在しない → warning（経路 A skip）
- RSS 取得失敗（network / 4xx / 5xx）→ warning（経路 B skip）、続行
- yaml パースエラー → exit 2

## articles.yml 初期構造

```yaml
series:
  ai-9months:
    title: "触り始めて9ヶ月の記録"
    description: "44歳でほぼ未経験から個人開発を始めた人間が、最初の9ヶ月で何に触れて、何に詰まって、何を作ったかを時系列で残す連載。"
    started_at: "2026-05-17"
    articles:
      - slug: dev-log-01
        title: "（第1話、2026-05-17 公開予定）"
        match_title: "触り始めて9ヶ月の記録"
        published: "2026-05-17"
        note_url: "https://note.com/akarilab/n/PLACEHOLDER_TBD_AFTER_PUBLISH"
        summary: "（連載第1話。2026-05-17 公開予定。本番公開後に sync_note_articles.py が要約を取得して更新。）"
        position: 1
```

`match_title` は RSS fallback 用（プレースホルダー段階で部分一致でマッチさせる）。

## ページ構成

### articles/index.html
- H1：「note 記事のまとめ」
- リード：AkariLab メディア「note.com/akarilab」の主要記事を構造化して並べる
- 連載カード：「触り始めて9ヶ月の記録」（連載親へのリンク、開始日 2026-05-17）
- 単発記事セクションは空（Phase 8 以降で main の AkariLab note 記事を articles.yml に取り込む）
- ItemList JSON-LD（連載親を含む）
- BreadcrumbList JSON-LD（ホーム → 記事）
- footer は他のページと同じ（共通 footer-common.html include）

### articles/ai-9months/index.html
- H1：「触り始めて9ヶ月の記録」
- リード：連載趣旨（44歳・ほぼ未経験から始めた個人開発の9ヶ月）
- 各話リスト：第1話プレースホルダー（公開予定マーク付き）
- 連載親 Article JSON-LD（hasPart 含む）
- BreadcrumbList JSON-LD（ホーム → 記事 → 触り始めて9ヶ月の記録）

### articles/ai-9months/dev-log-01.html
- H1：「（第1話、2026-05-17 公開予定）」（プレースホルダー）
- 公開予定マーク：「公開予定：2026-05-17」「note 原文 URL：公開後に確定」
- 要約ブロック：プレースホルダー文（500字未満で OK、5/17 に sync_note_articles.py が差し替え）
- note 原文リンク（プレースホルダー時は disabled / placeholder URL）
- 個別記事 Article JSON-LD
- BreadcrumbList JSON-LD（ホーム → 記事 → 連載 → 第1話）

## トーン制約

- 太字マーカー禁止（feedback_akarilab_no_bold_marker）
- 評価語禁止（「ぜひ」「最高」「変わる」「合わせて」）
- 開発者用語禁止（要約は「2026年8月から始まった」など淡々と）
- AI 構文禁止（feedback_anti_ai_syntax）
- 個人名「まこと」露出ゼロ（連載は AkariLab メディアの連載として扱う）
- アントワークス／伝説のすた丼屋／デンバープレミアム／ジョイフル等の固有名詞ゼロ

## meta / canonical / OGP

- canonical：各ページの絶対 URL
- og:type：`article`（個別記事 dev-log-01.html・連載親）／`website`（articles/index.html）
- og:image：`https://akarilab.org/assets/logo/hidamari_icon_256.png` fallback（Phase 8 以降に専用 OGP 画像差し替え）
- twitter:card：`summary_large_image`

## ブランド分離チェック

- 3 ページの本文に「ひだまり」「もやログ」「りぴメモ」固有プロモ語ゼロ（連載タイトル文中の固有名詞は許容、誘導 CTA は無し）
- footer は共通 footer-common.html（akarilab.org 横断リンクは Instagram / note のみ）
- 個人名「まこと」露出ゼロ
- アントワークス／伝説のすた丼屋／デンバープレミアム／ジョイフル等の固有名詞ゼロ

## 個人名露出チェック

- grep "まこと" → 全 3 ページゼロ
- grep "アントワークス" → ゼロ
- grep "伝説のすた丼屋" → ゼロ

## JSON-LD dead link チェック

- すべての `author` / `publisher` が `https://akarilab.org/#org` を参照（実在）
- `isPartOf` の `@id` がすべて連載親 `https://akarilab.org/articles/ai-9months/#series` に解決
- BreadcrumbList の `item` URL がすべて実在
- og:image の `hidamari_icon_256.png` は assets/logo/ に実在

## CODEX 設計レビュー結果

本フェーズ設計は 00_overall_design.md「### Phase 5」を統合した形で進行。設計レビューは Phase 0 で済んでいる前提（00_overall_design.md の Phase 5 セクションが設計md相当）。本ファイルは実装後に CODEX コードレビューを別途受ける。

## CODEX コードレビュー結果

実装後に `codex-review` スキル経由でレビューを受ける枠（メインエージェント側で実施）。

## 完了条件

- `articles/index.html`, `articles/ai-9months/index.html`, `articles/ai-9months/dev-log-01.html` 設置済
- `scripts/sync_note_articles.py` 設置済（構文 OK、`--dry-run` でエラーなく動く）
- `data/articles.yml` 設置済（YAML パース OK）
- `sitemap.xml` / `llms.txt` / `build_pages.py` 更新済
- ローカル検証 5 件（build_pages.py --check / aiseo_check_alt.py / aiseo_check_sitemap.py / yaml safe_load / sync_note_articles.py 構文）すべて exit 0
- 個人名「まこと」露出ゼロ（grep）
- アントワークス／伝説のすた丼屋／デンバープレミアム／ジョイフル等の固有名詞ゼロ（grep）
- commit はメインエージェントが CODEX レビュー後に行う

## 第1話本番公開時の手動運用フロー（2026-05-17）

1. note 記事「触り始めて9ヶ月の記録（仮）」を note.com/akarilab で公開
2. note-poster の出力 `C:/Users/user/akarilab-note/data/note_post_success_2026-05-17.json` を確認（自動投稿経由なら自動生成、手動投稿の場合は本フローに RSS fallback で対応）
3. `cd C:/Users/user/akarilab-site && python scripts/sync_note_articles.py` を実行
   - 経路 A：note-poster ログから note URL を取得 → articles.yml の `note_url` を上書き
   - 経路 B（fallback）：RSS から取得 → match_title マッチで articles.yml 更新
4. `data/articles.yml` の `dev-log-01` slot が更新されたことを確認
5. （Phase 5 範囲外、Phase 6+ で自動化）articles.yml から `dev-log-01.html` を再生成。Phase 5 では本ファイルを手動で要約・URL を反映する
6. ローカル検証 5 件を再実行 → exit 0 を確認
7. main へ commit / push → GitHub Pages 反映
8. Google リッチリザルトテストで Article + BreadcrumbList の警告ゼロを確認
