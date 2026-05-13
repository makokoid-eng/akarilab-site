# Phase 4 設計：moyalog / repimemo 本格 LP 新設

## 目的

もやログ／りぴメモを LINE 登録 URL だけ持つ広告から実 LP に格上げし、Organization から producer 経由で接続。LP 本文では AkariLab／個人名／他ブランド名を一切出さず、JSON-LD だけで Organization に接続する（ADR 0001 準拠）。

## 触るファイル

### 新規

- `moyalog/index.html` — もやログ本格 LP（H1/リード/機能/シーン/体験談導線/FAQ/CTA）
- `moyalog/voices/index.html` — 体験談骨格（Review JSON-LD）
- `repimemo/index.html` — 個人モード LP（伏線期間中の主役）
- `repimemo/store/index.html` — 店舗モード LP（退避、伏線明け 2026-07-11 に index 昇格予定）
- `repimemo/voices/index.html` — 体験談骨格

### 更新

- `sitemap.xml` — 5 ページ追加（priority/changefreq/lastmod 付き）
- `llms.txt` — Products セクション新設、3 プロダクト並列言及
- `scripts/build_pages.py` — TARGETS に 5 ページ追加

### 触らない

- 既存 6 ページ
- akarilab/, makoto/, hidamari/ 配下
- assets/, robots.txt, .nojekyll, .github/, scripts/aiseo_check_*

## ブランド分離（ADR 0001 準拠）

- LP 本文（H1〜CTA）に AkariLab／個人名／他プロダクト名を一切書かない
- footer は「© 2026 AkariLab」のみ、akarilab.org トップへの可視リンクなし
- もやログ→りぴメモ・りぴメモ→もやログの可視リンクなし
- JSON-LD `SoftwareApplication.producer = {@id: "https://akarilab.org/#org"}` で Organization に接続（人間 UI には出ず、AI クローラだけが拾う）

## りぴメモ伏線モード遵守（2026-05-16〜2026-07-10）

- LP 本文がプロダクト訴求であること自体は許容（指示書通り）
- X→LP 誘導は伏線期間中は外す（Phase 7B 対応）
- repimemo/index.html の店舗色は弱める：「店舗の中で」「店舗単位」「店舗導入」「店舗で使う場合」などの表現を `/repimemo/store/` への導線に集約し、index 本文は個人キャスト向けのシーンに振る
- 伏線明け 2026-07-11 に repimemo/index.html と repimemo/store/index.html の主従を入れ替える（または store の内容を index に昇格）

## トーン制約

- 評価語禁止（「最高」「ぜひ」「変わる」「ノウハウ」）
- AI 構文禁止（「AじゃなくてB」「〜だけじゃない」「最短で」）
- 太字マーカー禁止
- 開発者用語禁止
- 体験談は具体的行動・心の動きが入っているもののみ採用、語尾調整のみ
- 「業界全体を変える」「業界課題を解決」など大上段の語彙禁止（feedback_repimemo_industry_quiet_audience 準拠）

## OGP 画像方針

- Phase 4 では各 LP の og:image を `https://akarilab.org/assets/logo/hidamari_icon_256.png` に fallback
- 専用 `og.png`（1200×630・200KB 以下）は **Phase 8 以降で作成して差し替え**（Phase 4 は LP 本体実装に集中）
- 専用 favicon / apple-touch-icon も同様に Phase 8 以降で各プロダクト専用に差し替え

## 画像最適化チェック（00_overall_design.md L186-194 準拠）

- `<img>` に width / height / alt 必須（CLS 防止）
- ファーストビュー以外は `loading="lazy"`
- 本フェーズで実装した 5 ページに `<img>` 要素は使わなかった（テキストベース LP のため）。Phase 8 以降の専用 og.png 作成・体験談画像追加時に検証スクリプトで実機械検査

## SoftwareApplication JSON-LD

| ノード | @id | 配置ページ | applicationCategory | offers.price |
|---|---|---|---|---|
| もやログ | `https://akarilab.org/moyalog/#app` | /moyalog/ | LifestyleApplication | "0" JPY |
| りぴメモ（個人） | `https://akarilab.org/repimemo/#app` | /repimemo/ | BusinessApplication | "0" JPY |
| りぴメモ（店舗） | `https://akarilab.org/repimemo/store/#app` | /repimemo/store/ | BusinessApplication | "TBD"（伏線期間中） |

すべて `producer` を `@id: https://akarilab.org/#org` に向ける。

## FAQPage / Review / BreadcrumbList JSON-LD

- moyalog/index.html, repimemo/index.html に FAQPage を並列配置
- Review JSON-LD は `reviewRating` を入れず `reviewBody` のみ（プロモ口調回避）
- BreadcrumbList は各ページに直書き（partial 化せず、ページ別に position と name が異なるため）

## ブランド分離チェック

- 5 ページの本文に AkariLab／個人名／他プロダクト名露出ゼロを grep で確認
- footer が「© 2026 AkariLab」のみ
- もやログ→りぴメモ・りぴメモ→もやログの可視リンクなし

## 個人名露出チェック

- grep "まこと" → 全 5 ページゼロ
- grep "アントワークス／伝説のすた丼屋／デンバープレミアム／ジョイフル" → ゼロ

## JSON-LD dead link チェック

- すべての SoftwareApplication.producer が `https://akarilab.org/#org` を参照（実在）
- BreadcrumbList の item URL が実在
- og:image の hidamari_icon_256.png は assets/logo/ に実在

## CODEX 設計レビュー結果

本フェーズ設計は 00_overall_design.md「### Phase 4」と ADR 0001 を統合した形で進行。設計レビューは Phase 0 で済んでいる前提（00_overall_design.md の Phase 4 セクションが設計md相当）。

## CODEX コードレビュー結果

2026-05-13 実施。指摘 2 点：

| # | CODEX 指摘 | 反映先 | 状態 |
|---|---|---|---|
| 1 | repimemo/index.html が個人モード主役になり切っていない、「店舗」「予約ハブ」「NG情報共有」「店舗導入」が本文に出ている → 伏線期間の趣旨と少しズレ | repimemo/index.html の hero/機能カード/使用シーン4 の店舗色表現を弱め、店舗向け導線は /repimemo/store/ に集約 | 反映済 |
| 2 | Phase 4 必須の専用 OGP 画像が未配置、各ページは hidamari_icon_256.png fallback のまま | OGP 画像方針セクションに「Phase 8 以降で作成して差し替え」と明記、Phase 4 は LP 本体実装に集中 | 反映済（fallback 運用と明記） |

## 完了条件

- 5 ページ（moyalog/index.html, moyalog/voices/index.html, repimemo/index.html, repimemo/store/index.html, repimemo/voices/index.html）が main にマージ済
- sitemap.xml / llms.txt / build_pages.py の TARGETS が更新済
- ローカル検証 3 件（build_pages.py --check / aiseo_check_alt.py / aiseo_check_sitemap.py）すべて exit 0
- ブランド分離・トーン制約・伏線期間遵守のチェックが grep でゼロ
- 個人名露出ゼロ
- CODEX レビューの「強い懸念」2 件を反映済
- og:image の専用画像作成は Phase 8 以降に持ち越し（本フェーズの完了条件には含めない）
