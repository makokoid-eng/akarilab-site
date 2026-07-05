# page_kokora_design.md — /kokora/ プロダクトLP 新設

## 1. 目的（1行）
個人向け地図記録アプリ「ここら（Kokora）」の専用LP `/kokora/` を akarilab.org に新設し、AISEO（AkariLab→プロダクト群）の引用基盤に4本目（初のアプリ系）を接続する。

## 2. 触るファイル
**新規**
- `kokora/index.html`（プロダクトLP本体。自己完結HTML＝既存 repimemo/index.html と同方式、インライン`<style>`・partial不使用）

**更新（共通3ファイル）**
- `sitemap.xml`（`/kokora/` の `<url>` ブロック追加）
- `llms.txt`（`## Products` セクションに1行追加）
- `scripts/build_pages.py` TARGETS（**追記不要の見込み**。既存プロダクトLPは include 形式でなく自己完結HTMLのため。Phase 5 の `--check` で要確認、もし管理対象なら追記する）

## 3. 触らないファイル
- 既存6ページ：`akarilab/` `makoto/`（配下含む）`hidamari/` `moyalog/`（配下含む）`repimemo/`（配下含む）`articles/`（配下含む）`index.html`（トップ）
- partial：`assets/partials/head-common.html` `assets/partials/footer-common.html`
- 共通CSS `assets/css/site.css`、robots、sitemap構造そのもの
- ※ トップ `index.html` へのここらリンク追加は本commitの範囲外（別途判断。まずLP単独で立てる）

## 4. 実装手順
1. `kokora/index.html` を repimemo/index.html のテンプレ構造に倣って作成。
   - ただしブランドカラーはここら独自（クラフト地図テーマ＝pine/clay/sand系）に調整。
   - CTA は LINE 友だち追加ではなく **Web版本番URL** `https://mymap-260625-22054.web.app` へ。
   - 「近日 iOS / Android 公開予定」を添える（ストア未公開のため「ストアで入手」とは書かない）。
1-b. 世界観の背景演出（2026-07-06 ユーザー要望追記）：他LP同様の「同じ骨格・違う空気」方針。
   - ここら＝「地図・散歩・発見」。深緑（pine）基調に、紙の地図のようなクラフト感（sand/clay の淡い光）と、等高線/道筋を思わせる控えめな装飾を body::before/::after で敷く。
   - 素のCSS/JSのみ・z-index:-1・低〜中不透明度・prefers-reduced-motion 対応・isolation:isolate（CODEX 2026-07-06 指摘の予防的反映）。
   - IntersectionObserver スクロールリビール＋Updates タイムライン（他LPと同型）も実装。Updates 内容は収集済みの「ここら」安全候補（多言語化・アカウント削除・場所検索強化・Androidクローズドテスト）から採用。
2. JSON-LD 3種：SoftwareApplication（@id `https://akarilab.org/kokora/#app`）/ FAQPage / BreadcrumbList。
   - `applicationCategory` は地図記録＝`LifestyleApplication`、`operatingSystem` は `Web, iOS, Android`。
   - `producer` → `{ "@id": "https://akarilab.org/#org" }`（ADR 0001 §3）。
   - `offers` price 0 JPY（無料プランあり）。
3. sitemap.xml / llms.txt を同期更新。
4. ローカル検証 → CODEX → commit/push。

## 5. ブランド分離チェック（ADR 0001 整合）
- [ ] LP本文（H1〜CTA・段落・見出し・リスト）に他ブランド名（ひだまり/もやログ/りぴメモ/AkariLab/akarilab.org/note.com/akarilab）が出ていない
- [ ] LP本文に個人名「まこと」が出ていない
- [ ] footer は「© 2026 AkariLab」のみ。akarilab.org トップへの可視リンクなし
- [ ] 他プロダクトLPへの可視リンクなし
- [ ] JSON-LD `SoftwareApplication.producer` が `https://akarilab.org/#org` を参照
- [ ] meta description / og:description に他ブランド名・個人名が出ていない
- ADR 0001 §Decision 全項に整合（可視UIは分離・構造化データで統合）。

## 6. 個人名露出チェック
- [ ] HTML本文に「まこと」なし
- [ ] meta description / og:description に「まこと」なし
- [ ] JSON-LD のいずれのフィールドにも「まこと」なし（author等にPerson@id参照を使わずOrganization@id）
- [ ] footer が「© 2026 AkariLab」（個人名表記なし）
- ココナラ表現ルール：アントワークス/伝説のすた丼屋/デンバープレミアム/ジョイフル の固有名詞なし（本ページは経歴非掲載のため非該当だが確認）

## 7. JSON-LD dead link チェック
- [ ] `SoftwareApplication.producer` の `@id: https://akarilab.org/#org` が、サイトのOrganizationグラフ（/akarilab/ で定義）に解決する
- [ ] BreadcrumbList の item URL（ホーム / ここら）が実在する
- [ ] Person/Organization を本ページで**再定義しない**（@id衝突防止・参照のみ）

## 8. CODEX 設計レビュー結果（Phase 2 で追記）
- 2026-07-06 実施。強い懸念なし（実装方針確定の確認となった）。JSON-LD型・producer参照・sitemap priority 0.9/weekly を追認。
- Claude判断（安全側修正）: operatingSystem はストア未公開のため "Web" のみとする。iOS/Android は本文で「準備中」と表現し、ストア公開後に JSON-LD を更新する。

## 9. CODEX コードレビュー結果（Phase 6 で追記）
- 2026-07-06 実施。JSON-LD/canonical/breadcrumb/FAQ整合/sitemap/llms.txt すべてOK確認。
- 指摘①「← トップへ」可視リンク削除 → **不採用**。既存 hidamari LP に「← AkariLab トップへ」の先行慣行があり、本ページはブランド名を含まない「← トップへ」でより抑制的。ナビゲーション利便を優先。
- 指摘② og:image が hidamari_icon fallback → **既知・受容**。aiseo-page-publisher スキル規定の fallback（F5罠＝og:image欠落によるカード崩れ回避）。専用 og.png は後日別 commit（Phase 8 相当）で差し替え予定。
- 指摘③ .codex_review_diff.patch の混入注意 → 削除済み・コミット対象外。

## 10. 完了条件
- 本番 `https://akarilab.org/kokora/` が HTTP 200
- リッチリザルトテスト警告ゼロ（SoftwareApplication / FAQPage / BreadcrumbList）
- sitemap.xml に `/kokora/` 掲載・llms.txt §Products に1行掲載
- 既存6ページ無編集（git diff で確認）
- 1ページ=1commit
