# page_works_design.md — 制作実績・デモ ハブ /works/

- 起票日: 2026-07-18
- content_type: 単発ハブ（制作実績インデックス）
- slug: works
- page_path: `/works/`

## 1. 目的（1行）
AkariLab の受託 Web 制作の実績・デモを一覧で示すハブページを新設し、第1弾として製造業B2B向けデモ（外部Vercel公開）へ誘導する。

## 2. 触るファイル
新規:
- `works/index.html`（本体、partial include 形式）
- `works/img/seizo-btob.jpg`（デモのサムネイル。デモ側 `img/hero.jpg` を流用コピー、alt 付与）

既存（更新）:
- `sitemap.xml`（`/works/` の `<url>` を1行追加）
- `llms.txt`（新セクション `## Works` を追加し1行）
- `scripts/build_pages.py`（`TARGETS` に `works/index.html` を1行追加）
- `docs/aiseo/page_works_design.md`（本ファイル。Phase 2 / 6 のレビュー結果を追記）

## 3. 触らないファイル
- 既存ページすべて（akarilab/ makoto/ hidamari/ moyalog/ repimemo/ kokora/ articles/ 配下、hidamari.html、各 r/ リダイレクト）
- `assets/partials/head-common.html` / `assets/partials/footer-common.html`（共通 partial は不変）
- `assets/css/site.css`（既存クラスのみ利用。ページ固有装飾は works/index.html 内の `<style>` に閉じ込める）
- 既存の /akarilab/ ハブへのナビ導線追加は今回スコープ外（既存ページ改修になるため）。導線は別途相談。

## 4. 実装手順
1. デモの `hero.jpg` を `works/img/seizo-btob.jpg` にコピー。
2. `works/index.html` を head-common / footer-common include 形式で作成。
   - hero（AkariLab の制作実績ハブとしての導入）
   - 実績カード1枚：製造業B2Bデモ。サムネ＋概要＋外部リンク（https://seizo-btob-demo.vercel.app、target=_blank rel=noopener）。
   - 「制作のご相談」への内部導線は /makoto/services/ か /makoto/contact/ へ（AkariLab の受託窓口）。
3. sitemap.xml / llms.txt / build_pages.py TARGETS を同期。
4. ローカル検証（build_pages --check / alt / sitemap）。
5. CODEX コードレビュー → commit + push。

## 5. ブランド分離チェック（ADR 0001 整合）
本ページは「AkariLab の受託制作実績」を示すハブであり、/akarilab/ ハブと同格の「AkariLab 主役 OK」カテゴリに属する（プロダクト LP のブランド分離対象ではない）。したがって:
- [ ] AkariLab 名の露出は OK（本ページの主語そのもの）
- [ ] 他プロダクト名（ひだまり/もやログ/りぴメモ/ここら）は本文に出さない（実績とは無関係）
- [ ] デモ内の架空企業名「丸誠精工」は他ブランドではなく、掲載対象そのものなので OK
- [ ] footer は共通 partial（© 2026 AkariLab）のまま
- [ ] JSON-LD の publisher は `https://akarilab.org/#org` を参照

## 6. 個人名露出チェック
本ページは /makoto/ 配下ではないため個人名は出さない:
- [ ] HTML 本文に「まこと」なし
- [ ] meta description / og:description に「まこと」なし
- [ ] JSON-LD のいずれのフィールドにも「まこと」なし（publisher は Organization@id 参照）
- [ ] ココナラ禁止固有名詞（アントワークス/伝説のすた丼屋/デンバープレミアム/ジョイフル）なし

## 7. JSON-LD dead link チェック
- CollectionPage.publisher → `{@id: "https://akarilab.org/#org"}`（/akarilab/ で定義済、グラフ内解決）
- ItemList の itemListElement は ListItem でラップ、item は外部 URL（Vercel デモ）を `url` で持つ WebSite。各 @id は付与するが item の @id は外部デモ自身の URL ベースなのでグラフ内 dead link 化しない。
- BreadcrumbList は絶対 URL のみ。

## 8. CODEX 設計レビュー結果（2026-07-18）
強い懸念2件・中懸念3件を反映して設計を確定:
- [反映] item の型を `CreativeWork` → `WebSite` に変更（外部デモは実体がWebサイト）
- [反映] ItemList は `itemListElement: [{ "@type": "ListItem", "position": 1, "item": {WebSite} }]` でラップ
- [反映] sitemap: `priority=0.7 / changefreq=monthly`（新設ハブ・更新頻度未知のため monthly）
- [反映] llms.txt に第4セクション `## Works` を新設（将来増える前提のコメント添え）
- [反映] og:image はデモサムネ `works/img/seizo-btob.jpg` を使用（SNS映え）
- [反映] デモ紹介文に「（架空）」表記を添える（実在企業誤認防止）
- [見送り] 外部リンク rel="nofollow": 自作デモなので PageRank を渡してよい判断。rel="noopener" のみ付与
- CollectionPage.publisher=#org 参照・個人名なし・触らないファイル宣言は「良い点」として承認

## 9. CODEX コードレビュー結果（2026-07-18）
強い懸念ゼロ。品質補強3点のうち2点を反映:
- [反映] JSON-LD の @id 補強: ItemList に `@id/name/numberOfItems`、WebSite に `@id/description`、BreadcrumbList に `@id/name` を付与（CODEX 修正案採用）
- [反映] 設計md §7 の「CreativeWork」表記を「WebSite」に統一
- [見送り] favicon を hidamari_icon → AkariLab 共通アイコンへ差し替え: 既存の /akarilab/ 含めサイト全ページが hidamari_icon で統一されており、専用 AkariLab アイコン資産も未整備。ここだけ変えると逆に不整合になるため見送り（サイト横断のアイコン整理として別途対応する話）。
- dead link なし・既存ページ未改変・sitemap/llms.txt/TARGETS 整合は「問題なし」として承認

## 10. 完了条件
- `https://akarilab.org/works/` が本番 200
- build_pages.py --check / aiseo_check_alt.py / aiseo_check_sitemap.py すべて exit 0
- sitemap.xml・llms.txt・TARGETS 同期済み
- リッチリザルトテスト警告ゼロ
- 外部デモリンクが有効（200）

## 11. 追補（2026-07-18）ジャンル別デモ集化
初版は製造業1件のみだったが、ユーザー要望で「ジャンル別デモ集」に拡張。
Vercel 上の既存デモ5件を調査（`vercel projects ls`）して外部リンクで集約した:
- 飲食: とんかつ ひなた亭 https://akarilab-demo-tonkatsu.vercel.app/
- 不動産: 海風不動産 https://okinawa-fudosan-demo.vercel.app/
- 製造: 丸誠精工 https://seizo-btob-demo.vercel.app/
- イベントLP: DOG DAYS PARK 2026 https://dog-event-lp.vercel.app/
- イベントLP: いぬ集会 in 秦野戸川公園 https://inusyukai-mock.vercel.app/

除外: 一宮自習室デモ（ichinomiya-jishushitsu-mock）。memory `ichinomiya-demo-not-linked` の
「Vercel公開は続けるが AkariLab とは紐づけない」方針に従い、本ハブに載せない。

変更点:
- body をジャンル別セクション（01飲食/02不動産/03製造/04イベントLP/05相談）に再構成
- カードはサムネなしのテキストカード（各デモの内部画像参照が不揃いで安定取得できないため、v1では画像なしで統一）。将来サムネ追加可
- JSON-LD ItemList を numberOfItems=5・ListItem×5(WebSite) に更新
- og:image は暫定で seizo-btob.jpg のまま（CODEX 指摘の任意改善: /works/ 汎用OG画像への差し替えは将来対応）
- CODEX コードレビュー: ブロッカーなし・commit OK
- sitemap.xml / llms.txt / TARGETS は初版で /works/ 追加済みのため変更なし
