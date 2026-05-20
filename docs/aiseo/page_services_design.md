# /makoto/services/ — 提供サービス集約ハブ 設計md

## 1. 目的（1行）

「まこと」が現在ココナラと BrAIN で公開している支援サービスを 1 ページに集約し、AISEO（LLM 引用）と直接導線の両方を確立する。

## 2. 触るファイル

### 既存（読むのみ・書き換えない）

- `makoto/index.html`（トーンの参照／このスキルでは編集しない。リンク追加は別タスク）
- `makoto/profile/index.html`（FAQ にある「業務改善LINE Bot 30分相談：5,000円」表現の参照／別タスクで価格更新）
- `assets/partials/head-common.html`（include のみ）
- `assets/partials/footer-common.html`（include のみ）
- `assets/css/site.css`（参照のみ）

### 新規

- `makoto/services/index.html`（本ページ HTML、include 形式）
- `docs/aiseo/page_services_design.md`（本設計md）

### 更新

- `sitemap.xml`（`/makoto/services/` の `<url>` ブロック1件追加）
- `llms.txt`（`## Brand` セクションに `/makoto/services/` の1行追加）
- `scripts/build_pages.py`（`TARGETS` リストに `makoto/services/index.html` 追加、Phase 2 セクション末尾に Phase 2 追補としてコメント付き）

## 3. 触らないファイル

- 既存の他 HTML（akarilab/、moyalog/、repimemo/、hidamari/、articles/ 配下、規約4枚、makoto/ 既存3枚＋トップ）
- `assets/partials/` 既存3ファイル
- `assets/css/site.css`
- `docs/aiseo/` 既存 phase_1〜5 設計md・decisions/
- `scripts/aiseo_check_*.py`

## 4. 実装手順

1. 本設計md 起票（本ファイル）
2. CODEX 設計レビュー（§8 に結果追記）
3. `makoto/services/index.html` を include 形式で作成
   - head/footer は partial include、JSON-LD は本ファイル内に直書き
   - JSON-LD は `BreadcrumbList` ＋ `ItemList`（itemListElement に Service 型を3件）
4. `sitemap.xml` `/makoto/services/` 追加（priority 0.7 / changefreq monthly / lastmod 2026-05-20）
5. `llms.txt` `## Brand` 末尾に `- /makoto/services/  運営者の提供サービス一覧（ココナラ／BrAIN）` 追加
6. `scripts/build_pages.py` の TARGETS に Phase 2 セクション末尾コメント付きで追記
7. `python scripts/build_pages.py --check` `aiseo_check_alt.py` `aiseo_check_sitemap.py` で exit 0 確認
8. CODEX コードレビュー（§9 に結果追記）
9. commit + push

## 5. ブランド分離チェック（ADR 0001 準拠）

本ページは `/makoto/` 配下なので、ADR 0001 上の「個人名・全ブランド名 OK」例外ゾーン。それでも以下を機械的に確認：

- [x] LP 本文に「ひだまり／もやログ／りぴメモ／AkariLab」が出てよい（/makoto/ 配下のため）
- [x] 個人名「まこと」は出てよい（/makoto/ 配下のため）
- [x] footer は共通 partial（`© 2026 AkariLab`、akarilab.org への可視リンクなし、各プロダクトの可視リンクなし）
- [x] meta description / og:description に「まこと」表記 OK
- [x] JSON-LD `Service.provider` は `https://akarilab.org/makoto/#person` を参照（Person@id、Organization ではない。サービス提供主体は個人）
- [x] ItemList の publisher / about は不要（個人のサービス一覧であり、組織のページ目録ではない）

## 6. 個人名露出チェック

`/makoto/services/` は /makoto/ 配下のため個人名露出 OK。ココナラ表現ルール（個人名と無関係でも常時遵守）：

- [x] 「アントワークス」「伝説のすた丼屋」「デンバープレミアム」「ジョイフル」固有名詞なし
- [x] jobTitle 等の経歴情報は「店舗運営マネージャー」相当にぼかす（プロフィール既存の `jobTitle: 店舗運営マネージャー / 個人開発者` と整合）
- [x] 受賞表記は賞名のみ、会社名は伏せる（既存 profile と同じ「店長賞 地方店舗賞 (2022)」等）
- [x] サービス本文では「店舗運営マネージャー」「複数店舗統括」「外食業」までで止め、勤務先社名は出さない

## 7. JSON-LD dead link チェック

本ページに含める JSON-LD の @id 参照先：

- `Service.provider` → `https://akarilab.org/makoto/#person`
  - 解決先: `makoto/index.html` `Person` JSON-LD（@id 一致）✓
  - 解決先: `makoto/profile/index.html` `Person` JSON-LD（@id 一致）✓
- `BreadcrumbList.itemListElement` の item URL
  - `https://akarilab.org/` → `index.html` ✓
  - `https://akarilab.org/makoto/` → `makoto/index.html` ✓
  - `https://akarilab.org/makoto/services/` → 本ページ（self-reference）✓

外部 URL（dead link 候補）：

- `https://coconala.com/services/4227512` → 出品 ID（公開済み・要 Phase 5 後に curl -I で 200 確認）
- `https://coconala.com/services/4214161` → 出品 ID（公開済み・要 Phase 5 後に curl -I で 200 確認）
- `https://brain-market.com/u/akarilab/a/bzgjM5QjMgoTZsNWa0JXY` → BrAIN ノウハウ（公開済み・要 Phase 5 後に curl -I で 200 確認）

外部 URL の死活は Phase 7 push 後の本番検証で改めて curl -I 確認する。

## 8. CODEX 設計レビュー結果

- 結論: 実装可、強い懸念なし
- 観点1（ItemList+Service 妥当性）: OK。ただし `ListItem` 自体を Service にせず、`ListItem.item` に Service を入れる形が読みやすい → 本設計のとおりこの形で実装する
- 観点2（Service.provider = Person@id）: OK。Organization にすると「AkariLab が直接販売しているサービス」に寄りすぎるため Person@id が適切
- 観点3（ADR 0001 整合）: OK。/makoto/ 配下なので個人名・AkariLab・ココナラ・BrAIN を出して問題なし
- 観点4（個人名露出）: OK
- 観点5（sitemap 0.7/monthly）: OK。価格や出品内容が変わる可能性があるため yearly より monthly が妥当
- 観点6（触らないファイル）: OK。partial・CSS を触らない方針も安全
- 観点7（AkariLab トーン）: OK
- 観点8（ココナラ表現ルール）: OK。「店舗運営マネージャー」「外食業」「複数店舗統括」までに留める方針を維持
- 注意点（観点7由来）: 既存 `makoto/profile/index.html` の「5,000円」表記は別 commit で必須対応 → §10 完了条件にはせず付録に「別タスク」として残す（本設計とおり）

## 9. CODEX コードレビュー結果

- 結論: 強い懸念0、中懸念0、commit してよい内容
- 観点1〜9 すべてOK（JSON-LD 妥当 / Person@id 参照解決 / BreadcrumbList 構造正 / ADR 0001 整合 / sameAs 安全 / sitemap・llms.txt・build_pages.py の追記範囲妥当 / 既存6ページ・partial・CSS 未編集）
- 外部URL 3件（coconala.com/services/4227512 / coconala.com/services/4214161 / brain-market.com/u/akarilab/a/bzgjM5QjMgoTZsNWa0JXY）の死活確認: curl -I で全件 200
- 別タスク再確認: makoto/profile/index.html の「5,000円」表記更新は本 commit のブロッカーではない（設計md 付録に記録済）

## 10. 完了条件

- [ ] 本番 `https://akarilab.org/makoto/services/` が HTTP 200
- [ ] 本番 HTML に `application/ld+json` ブロック2件以上含有（BreadcrumbList ＋ ItemList）
- [ ] リッチリザルトテスト警告ゼロ（手動目視、Phase 7 直後）
- [ ] sitemap.xml に `/makoto/services/` の `<url>` ブロック存在
- [ ] llms.txt `## Brand` セクションに 1 行追加済
- [ ] build_pages.py TARGETS に `makoto/services/index.html` 含有
- [ ] `python scripts/build_pages.py --check` `aiseo_check_alt.py` `aiseo_check_sitemap.py` すべて exit 0
- [ ] 外部 URL 3件（ココナラ×2、BrAIN×1）が 200 / 3xx で生きている

---

## 付録: 掲載サービス3件（本文・JSON-LD の source of truth）

### A. ココナラ：組織監査制度の型診断

- 正式タイトル: 「現役マネジャーが組織の評価監査制度を型診断します」
- URL: https://coconala.com/services/4227512
- 価格: 4,000円（基本料金）
- 提供時間: 30分（ビデオチャット面談）＋ A4 1〜2枚 PDF レポート
- カテゴリ: コンサルティング・士業 / 業務改善・BPRコンサル
- 一言（120字）: 監査表を回しているのに現場の質が変わらない組織向けに、3層連携メソッド（自己評価×ピア観察×本部監査）をベースに「型」を診断する。質問票10問でA4 1〜2枚のPDFレポートと30分面談を提供。

### B. ココナラ：中小企業の業務をLINE Botで改善 30分ヒアリング相談

- 正式タイトル: 「中小企業の業務をLINE Botで改善｜30分ヒアリング相談」
- URL: https://coconala.com/services/4214161
- 価格: 通常 6,000円 / モニター 4,000円
- 提供時間: 30分（ビデオチャット）
- カテゴリ: コンサルティング・士業 / 業務改善
- 一言（120字）: LINE Bot を業務に組み込みたい中小企業向けに、ヒアリングから設計の入口までを30分で扱う。実装範囲・運用負荷・既存ツール連携の判断材料を提供。

### C. BrAIN：店舗運営20年マネージャーのAI実用例20選

- 正式タイトル: 「1on1・報告書・朝礼が半分の時間で動く 店舗運営20年マネージャーのAI実用例20選」
- URL: https://brain-market.com/u/akarilab/a/bzgjM5QjMgoTZsNWa0JXY
- 価格: 4,980円（買い切り）
- 形式: BrAIN ノウハウ（テキスト）
- 一言（120字）: 1on1・報告書・朝礼の時間を半減させた、店舗運営マネージャーの AI 実用例20件＋プロンプト集10個。人事・育成／数値・分析／コミュニケーション／戦略・意思決定の4カテゴリ各5例。

## 付録: 既存ページに残るギャップ（別タスク）

- `makoto/profile/index.html` の FAQ「業務改善LINE Bot 30分相談：5,000円」は最新の通常6,000円・モニター4,000円と齟齬。サービス追加・価格改定を反映する別 commit が必要（本スキル範囲外）。
- `makoto/index.html` 「このハブの中身」リストに `/makoto/services/` リンクを追加する別 commit が必要（既存ページ改修のため本スキル範囲外）。
