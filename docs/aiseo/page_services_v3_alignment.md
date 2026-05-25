# /makoto/services/ — 業務改善Bot 4段商品の追加 設計md

## 1. 目的（1行）

`/makoto/services/` 集約ハブに、新収入源プラン v3（[humming-foraging-nova.md](C:/Users/user/.claude/plans/humming-foraging-nova.md)）の業務改善Bot 4段商品（30分相談／診断レポート／PoC実装／保守付きBot改善）を反映し、ココナラ商品②の単発相談から月額保守までの導線を1ページで見せる。

## 2. 背景

- 既存 services hub には3商品（評価監査型診断 / LINE Bot 30分相談 / Brain ノウハウ）が ItemList JSON-LD で構造化済み
- プラン v3（CODEX 3回壁打ち済、2026-05-25 承認）で、LINE Bot 30分相談を**4段商品の入口**に位置付け
- ココナラ商品②本文は [coconala_description_v6.md](C:/Users/user/coconala-prep/coconala_description_v6.md) で3択誘導を追加済み
- ココナラ管理画面は1000字制限で詳細出せないため、**HP（akarilab.org）で4段商品の解説を補完**する役割

## 3. 触るファイル

### 既存（更新）
- `makoto/services/index.html` — ItemList 拡張（既存3件 + 業務改善Bot 4段商品の解説セクション追加、JSON-LD は LINE Bot 30分相談の hasPart として 4段商品を表現する案を検討）
- `sitemap.xml` — `/makoto/services/` の lastmod を 2026-05-26 に更新
- `llms.txt` — `## Brand` セクションの services 行の解説文を更新（業務改善Bot縦動線を含む旨）

### 既存（読むのみ・書き換えない）
- `makoto/profile/index.html` — FAQ Q5 の価格表記が古い場合は別タスクで更新
- `assets/partials/head-common.html` / `footer-common.html` — include のみ
- `assets/css/site.css` — 参照のみ

### 新規
- `docs/aiseo/page_services_v3_alignment.md`（本設計md）

## 4. 触らないファイル
- 既存の他 HTML（akarilab/、moyalog/、repimemo/、hidamari/、articles/ 配下、規約4枚、makoto/ 既存3枚＋トップ）
- `docs/aiseo/` 既存 page_services_design.md（初版は維持、本ファイルが追補）
- `scripts/build_pages.py` の TARGETS は変更不要（既存 services/index.html を更新するだけ）

## 5. 商品構成の整理

| # | 商品 | 価格 | 出品先 | services hub での扱い |
|---|---|---|---|---|
| 1 | 既存: 評価監査制度 型診断 | 通常6,000円 / モニター4,000円 | ココナラ 4227512 | 既存カード維持 |
| 2 | 既存: LINE Bot 30分相談 | 通常6,000円 / モニター4,000円 | ココナラ 4214161 | **既存カードを拡張**（4段導線の入口として位置付け） |
| 3 | 既存: Brain「AI実用例20選」 | 4,980円 | Brain | 既存カード維持 |
| 4 | **新規: 業務改善Bot診断レポート** | 10,000円 | ココナラ新規出品（M1で申請）| カード2の本文内で言及（独立カードは出品申請完了後） |
| 5 | **新規: PoC実装** | 80,000円 | ココナラ新規出品（M1で申請）| 同上 |
| 6 | **新規: 保守付きBot改善** | 初期50,000円＋月15,000円 | akarilab.org経由の個別契約（PoC後）| 同上 |

**判断**: 新規商品4-6 はココナラ出品申請完了まで独立 ItemList 要素にしない。**カード2「LINE Bot 30分相談」の本文内に「30分相談後の3つの選択肢」セクションを追加する形**で、出品前段階での導線を確立する。出品申請完了後に v3.1 設計md で ItemList 要素として正式追加。

## 6. 実装手順

1. 本設計md 起票（本ファイル）
2. **CODEX 設計レビュー**（§9 に結果追記）
3. `makoto/services/index.html` のカード2を拡張:
   - 価格表記の下に「30分相談後の選択肢」ulを追加（診断レポート/PoC/保守付き）
   - 本文末尾にショートテキストで「ココナラ商品ページからご購入後、30分の相談を経て、ご希望に応じて上記の選択肢に進めます」と記載
4. JSON-LD は ItemList 要素は触らず、カード2の Service.description を「30分ヒアリング相談（その後、診断レポート・PoC実装・保守付き改善の選択肢あり）」に微更新
5. `sitemap.xml` の lastmod 更新
6. `llms.txt` の services 行を「業務改善Bot縦動線（30分相談→診断→PoC→保守）も含む」に更新
7. `python scripts/build_pages.py --check` `aiseo_check_alt.py` `aiseo_check_sitemap.py` で exit 0 確認
8. **CODEX コードレビュー**（§10 に結果追記）
9. commit + push

## 7. ブランド分離チェック（ADR 0001 準拠）

- LP本文に他ブランド名は出さない（既存 services hub の方針維持、本追補でも変えない）
- 個人名露出範囲は `/makoto/` 配下のみ（本ページは該当配下、OK）
- 業種・社名は伏せる（カード2の本文で「外食・小売・サービス業の現場担当者・経営者」のように業種カテゴリで止める）
- AI構文（〜だけじゃない／〜ではなく等）混入なし、akarilab-writing-style + anti-ai-syntax で確認

## 8. JSON-LD 微更新案

```diff
 {
   "@type": "ListItem",
   "position": 2,
   "item": {
     "@type": "Service",
     "name": "中小企業の業務をLINE Botで改善｜30分ヒアリング相談",
     "url": "https://coconala.com/services/4214161",
-    "description": "LINE Bot を業務に組み込みたい中小企業向けに、ヒアリングから設計の入口までを30分で扱う。実装範囲・運用負荷・既存ツール連携の判断材料を提供。",
+    "description": "LINE Bot を業務に組み込みたい中小企業向けに、ヒアリングから設計の入口までを30分で扱う。実装範囲・運用負荷・既存ツール連携の判断材料を提供。相談後は希望に応じて、業務改善Bot診断レポート（10,000円）／PoC実装（80,000円・1週間〜）／保守付きBot改善（初期50,000円+月15,000円）の3つの選択肢に進める。",
     ...
   }
 }
```

ItemList の numberOfItems は 3 のまま維持（独立 ItemList 化は出品申請完了後）。

## 9. CODEX 設計レビュー結果（2026-05-26 実施）

### CODEX 評価
- **強い懸念なし**、v6 と HP 更新の整合取れている
- ItemList は3件のまま維持、新規3商品は出品申請完了前なので独立 Service 化しない方針を追認
- カード2「LINE Bot 30分相談」本文内に「相談後の3択」を追加する形でOK

### CODEX 提案の追加 HTML 文案（カード2 末尾に挿入）
```html
<ul>
  <li>相談後の選択肢：業務改善Bot診断レポート 10,000円</li>
  <li>PoC実装：80,000円・1週間〜</li>
  <li>保守付きBot改善：初期50,000円＋月15,000円</li>
</ul>
<p>30分相談で現状を整理したあと、ご希望に応じて診断レポート、PoC実装、保守付き改善へ進めます。</p>
```

### CODEX 提案の JSON-LD description 改訂（200字以内に圧縮）
本設計md §8 の diff 案は冗長だったため、CODEX 提案版に差し替え:
```json
"LINE Botを業務に組み込みたい中小企業向けの30分相談。導入前の判断材料を整理し、相談後は診断レポート、PoC実装、保守付きBot改善の3択へ進めます。"
```

### 更新対象3ファイル（CODEX 確認済み）
- `makoto/services/index.html`（カード2拡張 + JSON-LD description 更新）
- `sitemap.xml`（`/makoto/services/` の lastmod を `2026-05-26` に）
- `llms.txt`（services 行の解説文に「業務改善Bot縦動線」を反映）

## 10. CODEX コードレビュー結果（未実施・後で追記）

HTML 改修後、CODEX に diff を渡してレビュー。最低観点：
- HTML 構文（既存 services hub のスタイルに合致するか）
- aiseo_check_alt.py / aiseo_check_sitemap.py が exit 0
- JSON-LD バリデーションが通る
- 既存カード1/3 への副作用なし

## 11. 関連メモリ・参照

- [[project_business_improvement_bot_saas]] — 本プランの本拠地
- [[project_services_hub]] — services hub の v1（2026-05-20 commit 0053318）
- [[project_aiseo_construction]] — akarilab.org AISEO 8 フェーズ
- [[feedback_akarilab_no_dev_jargon]] — 開発者用語を持ち込まない（保守付き改善の説明で技術用語を出さない）
- [[feedback_articles_meta_check]] — 本ページは記事ではないため articles-meta.md 照合は不要
