# Phase 2 設計: /akarilab/ + Organization JSON-LD + /makoto/ プロフィール

## 目的

AkariLab を schema.org グラフの中心ノード（Organization）として一次定義し、運営者プロフィール（Person）を /makoto/ サブパスに深掘り経路として設置する。AI 検索エンジンが「AkariLab とは」と聞かれて引用する第一候補ページを作る。

## 触るファイル

### 新規

- `akarilab/index.html` — ブランドの一次定義ページ（Organization JSON-LD）
- `makoto/index.html` — 運営者の名刺ページ（Person JSON-LD、1段落プロフ）
- `makoto/profile/index.html` — 経歴詳細＋FAQPage
- `makoto/timeline/index.html` — AI 利用タイムライン（dl/dt 形式）
- `makoto/contact/index.html` — 連絡導線（ProfilePage JSON-LD、sameAs）
- `assets/partials/jsonld/organization.html` — Organization JSON-LD テンプレ
- `assets/partials/jsonld/person.html` — Person JSON-LD テンプレ
- BreadcrumbList は各ページに直書き（partial 化せず、ページ別に position と name が異なるため）
- `assets/og.png` — AkariLab 共通 OGP 画像（1200x630、200KB 以下）。Phase 2 では未配置のため、og:image は当面 `/assets/logo/hidamari_icon_256.png` を fallback 参照。Phase 4（LP 画像追加）または Phase 3 で正式画像を作成して差し替え。
- `docs/aiseo/phase_2_design.md` — 本ファイル
- `scripts/build_pages.py` の `TARGETS` リストへ上記5ページを追加

### 更新

- `sitemap.xml` — 上記5ページを追加（priority: /akarilab/=0.9、/makoto/=0.8、/makoto/profile/=0.7、/makoto/timeline/=0.6、/makoto/contact/=0.6）
- `llms.txt` — 「Future」セクションから /akarilab/ /makoto/ を上に昇格

## 触らないファイル

- 既存6ページ（index.html / hidamari.html / 規約4枚）— Phase 3 で扱う
- 既存 partial（head-common / footer-common / site.css）— 内容の変更なし、include 利用のみ
- post_to_x.py / text-generator / note-poster — Phase 6/7 で扱う

## 実装手順

1. `assets/og.png` 配置（既存 hidamari OG 画像の流用 or 簡易作成）
2. JSON-LD partial 3 種を作成（organization / person / breadcrumb）
3. /akarilab/index.html を作成（Organization 一次定義、ブランド説明、プロダクト一覧、運営者プロフリンク）
4. /makoto/index.html を作成（Person 一次定義、1段落プロフ、4サブページへの導線）
5. /makoto/profile/ /timeline/ /contact/ を作成
6. `scripts/build_pages.py` の TARGETS に5ページを追加
7. `sitemap.xml` / `llms.txt` を更新
8. ローカルで `build_pages.py --check` / `aiseo_check_alt.py` / `aiseo_check_sitemap.py` を実行
9. CODEX コードレビュー
10. commit

## グラフ設計

### Organization（中心ノード）

- `@id`: `https://akarilab.org/#org`
- 一次定義ページ: `/akarilab/index.html`（Organization JSON-LD を `<head>` に配置）
- founder: `https://akarilab.org/makoto/#person`
- sameAs: note / IG / GitHub（X 4 アカウントは Phase 7B の bio 設計確定後に sameAs に追加。それまでは未確認 URL を sameAs に入れない）
- url: `https://akarilab.org/`
- logo: 専用ロゴ未作成のため Phase 2 では JSON-LD に `logo` フィールドを含めない。ロゴ作成後 Phase 3 以降で追加。

### Person（深掘りノード）

- `@id`: `https://akarilab.org/makoto/#person`
- 一次定義ページ: `/makoto/index.html`（Person JSON-LD を `<head>` に配置）
- jobTitle: 「店舗運営マネージャー / 個人開発者」
- description: 「外食業で21年の現場経験を持ち、店長賞を3年連続受賞（2022地方店舗賞・2023優秀店長賞・2024最優秀店長賞）。並行して AkariLab を運営し、LINE Bot 群を個人開発している。」
- award: 3冠の賞名のみ（会社名なし）
- knowsAbout: LINE Bot 設計 / 店舗運営 / 外食業オペレーション / 教育AI / 個人開発 / Cloud Functions / Firestore / 業務改善
- sameAs: GitHub のみ（ココナラURLは確定後 Phase 2 着手時に追加）
- `Person.founder` は入れない（schema.org 仕様上不自然、CODEX 設計レビュー指摘 4 反映）

### BreadcrumbList

- /makoto/ 配下の各ページに配置：「ホーム > まこと > （該当ページ）」
- /akarilab/ には：「ホーム > AkariLab」

### FAQPage

- /makoto/profile/ に FAQPage を配置（5問）：
  1. 現職は？ → 「外食チェーンで店舗運営マネージャー（4店舗統括）」
  2. 副業の規定は？ → 「会社規定上クリア。詳細は応相談」
  3. コードはいつから書いている？ → 「2025年8月 LINE Bot Echo、2025年10月 初 Git push、それ以前は ChatGPT 利用のみ」
  4. 資格は？ → 「（公開可資格があれば。なければ『特に対外公開資格なし』）」 ← Phase 2 着手時にユーザー確認
  5. 業務改善相談はいくら？ → 「ココナラで30分5,000円。詳細は /makoto/contact/」

### ProfilePage

- /makoto/contact/ に ProfilePage JSON-LD（mainEntity = #person）

## 各ページのコンテンツ方針（淡々具体トーン）

### /akarilab/index.html

```
H1: AkariLab

リード（150字以内）:
現場の「困った」から生まれた、LINE Bot 群を運営するブランド。
ひだまり・もやログ・りぴメモという3本の独立したプロダクトを、
それぞれ独自の世界観で運営している。
note ではメディア「AkariLab」を並行して書いている。

提供プロダクト（カード3枚 + メディア1枚）:
- ひだまり（学習 Bot、開発中、akarilab.org/hidamari.html）
- もやログ（感情ログ Bot、lin.ee/q1k7v8F）
- りぴメモ（接客メモ Bot、lin.ee/HbV7Ehv）
- AkariLab note（メディア、note.com/akarilab）

運営者:
ブランドの設計と実装はまこと（→ akarilab.org/makoto/）が行う。
```

注意：もやログ／りぴメモのリンクは「ブランド分離」と矛盾しないか？
→ /akarilab/ は AkariLab ブランド一次定義ページなので、提供プロダクトの一覧表示は妥当（ブランド分離ルールは個別 LP・SNS 本文での相互言及禁止）。ただし可視リンクのテキストはプロダクト名のみ、各プロダクトの世界観を引きずる文言を避ける。

### /makoto/index.html

```
H1: まこと

1段落プロフ（500字以内）:
店舗運営の現場で21年、いまは店舗運営マネージャー（4店舗統括）として働いている。
店長賞を3年連続受賞（2022 地方店舗賞・2023 優秀店長賞・2024 最優秀店長賞）。
2024年夏に生成 AI を本格的に使い始めて、2025年10月に最初のコードを Git に保存した。
2026年5月時点で AkariLab というブランドを運営し、LINE Bot を5本並行で動かしている。
このページは、その記録を集めた個人ハブの入口。

サブページ:
- 経歴の事実塊 → /makoto/profile/
- AI 利用タイムライン → /makoto/timeline/
- 連絡先 → /makoto/contact/

書いているもの:
note メディア「AkariLab」（note.com/akarilab）に、開発と運用の記録を書いている。
2026-05-17 から連載「触り始めて9ヶ月の記録」が始まる。
```

### /makoto/profile/index.html

```
H1: 経歴

事実箇条書き（1文1事実）:
- 店舗運営21年（外食業）
- 店長賞 地方店舗賞（2022）
- 店長賞 優秀店長賞（2023）
- 店長賞 最優秀店長賞（2024）
- 現職: 店舗運営マネージャー（4店舗統括・年商4億6,000万円規模）
- 個人開発: AkariLab（LINE Bot 群、note メディア）

担当領域:
- LINE Bot 設計
- 店舗 QSC オペレーション
- 業務改善（KPI 集計・面談記録・マニュアル）
- 教育 AI（ひだまり）
- 感情ログ（もやログ）
- 接客メモ（りぴメモ）

FAQ:
（5問の Q&A、上記グラフ設計参照）

迷いを隠さない一文:
店舗運営とコードを並行して回せている期間がいつまで続くかは、まだ決まっていない。
```

### /makoto/timeline/index.html

```
H1: タイムライン

説明:
生成 AI に触れ始めてから、AkariLab を運営するまでの主要な日付を時系列で並べた。

dl/dt:
- 2023-02 ChatGPT に最初に触れた（記憶として残る最初の操作）
- 2024-08-29 台風で熊本のホテルに足止めされた日に、生成 AI という言葉を概念として知った（DaiGoのAIチャンネル）
- 2024-09-03 業務で ChatGPT を本格的に使い始めた（Excel 関数を書かせるところから）
- 2025-08-26 LINE Bot が Echo を返した
- 2025-10-06 食改善 Bot を公開
- 2025-10-30 Git に最初のコードを保存、Cloud Run への自動公開も同日に動かした
- 2026-04 note AkariLab 運用開始
- 2026-05-13 AkariLab 個人ハブ /makoto/ 設置（このページ）
- 2026-05-17 連載「触り始めて9ヶ月の記録」第1話公開
```

### /makoto/contact/index.html

```
H1: 連絡先

業務改善 LINE Bot 30分相談（ココナラ）:
- 5,000円
- 「現場で動く Bot」の話だけ。机上のシステムはお断りすることがある
- リンク（ココナラ正式 URL を Phase 2 着手時に確定）

その他の窓口:
- AkariLab note: https://note.com/akarilab
- Instagram: https://www.instagram.com/akarilab_jp/
- GitHub: https://github.com/makokoid-eng

連絡が向いていない人:
- 最短で結果を出したい人
- ノウハウだけを求めている人
- 「とにかく作って」型の依頼
```

## ココナラ表現ルール厳守

全ページで以下を厳守（coconala_profile.md §表現ルール 1-5）：

1. 「得意です」「お任せください」のような自己評価/勧誘語は含めない
2. AI っぽい言い回し（〜だけじゃない／〜ではなく／一緒に〜／最短で／確実に）は含めない
3. アントワークス・デンバープレミアム・伝説のすた丼屋・ジョイフルなど固有名詞は出さない
4. 「店舗運営21年」「店長賞3冠」「最優秀店長賞」など職務経歴書ベースの公開情報レベルは出して OK
5. AkariLab トーン（淡々・誠実）を保つ

## ブランド分離チェック

- /akarilab/index.html はブランド一次定義ページなので、提供プロダクト3つを並列言及する（ブランド分離ルールの趣旨に違反しない＝LP・SNS 本文ではない）
- /makoto/ 配下では「AkariLab で何をしているか」の文脈で 3 プロダクトに言及する。ただし各プロダクトの「世界観」（もやログのケア感、りぴメモの夜職向け表現）を /makoto/ で持ち込まない
- /makoto/contact/ では業務改善相談（B2B）の文脈で AkariLab プロダクトを「並行運営している」程度に触れる、深入りしない

## 個人名露出チェック

- /makoto/ 配下のページ本文に「まこと」と表記する（このフェーズでの初出）
- /akarilab/ 配下では「運営者: まこと（→ /makoto/）」とリンク添えで言及する
- /akarilab/ 本文に経歴詳細を書かない（経歴は /makoto/profile/ に集約）
- 既存6ページ（index.html / hidamari.html / 規約4枚）には個人名を出さない（Phase 3 で再確認）

## JSON-LD dead link チェック

- /akarilab/ の Organization.founder が `https://akarilab.org/makoto/#person` を参照 → /makoto/index.html に Person JSON-LD（@id 一致）が存在
- /makoto/ の Person ノードに sameAs を入れる場合、URL の到達確認（GitHub プロフィールの実在）
- /makoto/contact/ の ProfilePage.mainEntity が #person を参照 → 同上
- BreadcrumbList の itemListElement の URL が実在する
- og:image が `assets/og.png` を指す → 実ファイル存在
- logo URL が `assets/logo/akarilab.png` または代替先を指す → 実ファイル存在

## ユーザー確認済み事項（2026-05-13）

1. **AkariLab 共通ロゴ**：このセッションで生成（AI 画像生成 or 手描きスキャン）、`assets/logo/akarilab.png` に配置。
2. **OGP 画像**：このセッションで AI 画像生成、`assets/og.png` に配置（1200x630, 200KB 以下）。AkariLab トーン（feedback_akarilab_image_style 準拠：泥臭く、水彩/祈り系を避ける）。
3. **ココナラ URL**：既存 `index.html:363` の `https://coconala.com/services/4214161`（サービス URL）を `/makoto/contact/` 本文の可視リンクとして使用。`Person.sameAs` には入れない（サービス URL は同一人物プロフィールとは別物のため、schema.org 仕様上不適切）。
4. **FAQ 4問目「資格は？」**：「対外公開資格は特になし。現場で積んだ見識とコードで仕事をしている」で送る。Person.hasCredential は配置しない。

## CODEX 設計レビュー結果

（実装前にレビュー依頼後、ここに反映状況を追記）

## CODEX コードレビュー結果

（実装完了後、ここに反映状況を追記）

## 完了条件

- 新規ページ5本が main にマージ済み（/akarilab/index.html / /makoto/index.html / /makoto/profile/index.html / /makoto/timeline/index.html / /makoto/contact/index.html）
- 各ページに Organization / Person / FAQPage / BreadcrumbList / ProfilePage の適切な JSON-LD が配置されている
- `build_pages.py --check` が冪等動作（TARGETS 5本登録済）
- aiseo_check_alt.py / aiseo_check_sitemap.py が OK
- aiseo-check.yml が main で全件 green（JSON-LD warning が dangling 参照ゼロを示す）
- Google リッチリザルトテスト（https://search.google.com/test/rich-results）で Organization / Person / FAQPage / BreadcrumbList / ProfilePage の警告ゼロ
- 個人名「まこと」が /makoto/ ハブ外（既存6ページ、新規 /akarilab/ 本文）に出ていない
- ココナラ表現ルール違反ゼロ
- CODEX レビューの「強い懸念」がゼロ件 or 全件 ADR 化されている
