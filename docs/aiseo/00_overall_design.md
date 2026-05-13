# AISEO 構築計画 — AkariLab を AI 引用ハブにする

## Context

### なぜ今やるのか

現在、まこと運営の各プロダクト（ひだまり／もやログ／りぴメモ／AkariLab／makochinta1）はそれぞれ独立して動いており、AI 検索エンジン（ChatGPT Search／Perplexity／Gemini／Claude）から見ると「同じ運営者の連携した活動」として認識されない状態にある。akarilab.org は GitHub Pages で稼働しているがブランドハブ止まりで、JSON-LD 構造化データはゼロ、moyalog/repimemo は LP 自体が無い、SNS 自動投稿には著者署名が無く、4 アカウント分離が強すぎて上位の AkariLab レイヤーが AI から見えない。

### 何を狙うか

「AkariLab」と各プロダクト名・連載名・「触り始めて9ヶ月の記録」等で検索したときに、AI 回答エンジンが「AkariLab → プロダクト群 → note 記事連載 → 運営者プロフィール」を構造として引用できる状態を作る。時間経過とともに、新しいnote記事・LP更新・SNS発信が積み重なって AkariLab というブランド名が AI 回答内で一次情報源として固定化されることを目指す。

### 期待する最終状態

- 「AkariLab とは」と聞かれたら akarilab.org が引用される
- 「ひだまり LINE Bot」と聞かれたら akarilab.org/hidamari/ と関連 note 記事が引用される
- 「触り始めて9ヶ月の記録 連載」と聞かれたら note とミラー（akarilab.org/articles/ai-9months/）が引用される
- 深掘り（「AkariLab を運営しているのは誰」）された場合のみ、akarilab.org/makoto/ から運営者プロフィールに到達できる

### ユーザー決定事項（2026-05-13 確定）

1. AISEO の対象は「個人ブランド／プロダクト／メディアの全部を同時に組む」
2. 優先 AI エンジンは ChatGPT／Perplexity／Gemini／Claude の 4 つすべて
3. 個人ハブは akarilab.org/makoto/ サブパスに新設
4. もやログ／りぴメモは本格 LP（画像／導線／体験談付き）を新規作成
5. CODEX レビューを各フェーズの設計 md とコード両方に毎回入れる
6. **対外署名は全て「AkariLab」名義に統一**、個人名「まこと」は /makoto/ ハブ内でのみ露出

### 重要な制約

- ブランド分離ルール（feedback_brand_isolation_moyalog_repimemo）：もやログ／りぴメモ／ひだまり の SNS 本文・LP 本文には他プロダクト名・他ブランド名を出さない。akarilab.org サブパス配置と JSON-LD 接続は趣旨を破らない（UI 上は分離維持）。
- AkariLab 記事ブランドトーン：太字マーカー禁止、人物名匿名化、開発者用語禁止、淡々具体（feedback_akarilab_*）。
- ココナラプロフィール表現ルール：「アントワークス／伝説のすた丼屋／デンバープレミアム／ジョイフル」固有名詞は出さない（coconala_profile.md §表現ルール）。「店舗運営21年」「店長賞3冠」までは公開可。
- りぴメモ industry 伏線モード期間（2026-05-16〜2026-07-10）：プロダクト訴求禁止。LP 自体は維持するが X→LP 誘導は外す。
- note 非公式 API 制約：og:description / JSON-LD 書込は不可、note 本文末尾の構造化フッターブロックで補う。

---

## 全体アーキテクチャ

```
akarilab.org （GitHub Pages, makokoid-eng/akarilab-site）
│
├─ /                          既存 index.html 改修（Organization JSON-LD 追加）
│
├─ /akarilab/                 ★新設・ブランドの一次定義ページ
│   └─ Organization JSON-LD（@id: https://akarilab.org/#org）
│      founder → /makoto/#person、sameAs（X×4 / note / IG / GitHub）
│
├─ /makoto/                   ★新設・運営者プロフィール（深掘り経路）
│   ├─ index.html              名前・現職・受賞・1段落プロフ
│   ├─ profile/index.html      経歴詳細＋FAQPage
│   ├─ timeline/index.html     AI 利用タイムライン（dl/dt 年表）
│   └─ contact/index.html      ココナラ／X／note の sameAs
│   ※ Person JSON-LD（@id: https://akarilab.org/makoto/#person）
│   ※ AkariLab founder として Organization から参照される
│
├─ /hidamari/                 既存 hidamari.html を /hidamari/index.html へ移設
│   └─ SoftwareApplication JSON-LD（producer → /#org）
│
├─ /moyalog/   ★新設・本格LP    SoftwareApplication JSON-LD（producer → /#org）
├─ /repimemo/  ★新設・本格LP    SoftwareApplication JSON-LD（producer → /#org）
│
├─ /articles/                 ★新設・note 記事ハブ
│   ├─ index.html              全主要記事の ItemList
│   └─ ai-9months/             連載「触り始めて9ヶ月の記録」
│       ├─ index.html           連載親 Article + hasPart
│       └─ {slug}.html          個別ミラー（要約500字 + JSON-LD + note 原文リンク）
│
├─ /assets/
│   ├─ css/site.css            共通CSS（既存 :root 統合）
│   └─ partials/               HTML include 用フラグメント
│
├─ /sitemap.xml               ★新設
├─ /robots.txt                ★新設・AI クローラ allowlist
├─ /llms.txt                  ★新設・AI 向けサイトマップ
└─ /.nojekyll                 ★新設・GH Pages の Jekyll 抑止

──────────────────────────────────────────────
連携先（外側）
──────────────────────────────────────────────
note.com/akarilab
  └─ 各記事末尾に AkariLab 署名フッター（個人名は出さない）
     ┌→ akarilab.org/articles/{slug}/
     └→ akarilab.org/  /  akarilab.org/{product}/

X 4 アカウント
  ├─ @waveblasttaiyo （AkariLab メイン、bio に akarilab.org/）
  ├─ @makochinta1     （AkariLab note 拡散、bio に akarilab.org/articles/）
  ├─ @moyalog         （bio に lin.ee | akarilab.org/moyalog/）
  └─ @repimemo        （bio に lin.ee | akarilab.org/repimemo/）

LINE 3 アカウント、GitHub: makokoid-eng、ココナラ /users/{id}、IG @akarilab_jp
```

### 設計の核

- **グラフの中心ノード = `https://akarilab.org/#org`（Organization=AkariLab）**
- Person /makoto/#person は Organization.founder として接続するが、対外署名・SNS bio・note フッターには露出させない。
- SoftwareApplication（プロダクト3）、Article（連載・個別記事ミラー）はすべて producer/publisher を `/#org` に向ける。
- ブランド分離は「弱い接続（同一ドメイン下サブパス配置）」と「強い接続（@id 参照グラフ）」で担保。LP 本文には他ブランド名・個人名を出さない。

---

## フェーズ一覧

| # | 名前 | サイズ | 依存 |
|---|---|---|---|
| 0 | この設計 md 確定 + 全体 CODEX レビュー | 1-2h | なし |
| 1 | サイト基盤整備（partial / CSS 統合 / robots / sitemap / llms.txt / .nojekyll / canonical 方針 / ADR 0001） | 3h | Phase 0 |
| 2 | /akarilab/ ＋ Organization JSON-LD ＋ /makoto/ 個人プロフィール（深掘り経路） | 4h | Phase 1 |
| 3 | 既存ページの JSON-LD 強化＋/hidamari/ 移設 | 3h | Phase 2 |
| 4 | /moyalog/ /repimemo/ 本格 LP 新設（画像最適化チェック含む） | 5h | Phase 2, 3 |
| 5 | /articles/ 連載ハブ＋個別要約ハブ（連載開始 2026-05-17 同期） | 4h | Phase 2 |
| 6 | text-generator フッター挿入 + note-poster 投稿前フッター検査 + 関連リンク機構 | 3h | Phase 5 |
| 7A | 4 アカウント post_to_x.py の User-Agent 改修（1行差分のみ） | 1h | Phase 2 |
| 7B | X bio 設計書とブランド別反映（手動適用） | 1h | Phase 4 |
| 8 | 引用モニタ拡張（既存 check_llm_citations.py に AISEO クエリ追加、月次 cron に乗せる） | 1h | Phase 2, 5 |

各フェーズ＝「設計 md → 実装 → 動作確認 → CODEX レビュー」で1単位。フェーズ完了ごとに plan ディレクトリに `phase_N_design.md` を残す。

### phase_N_design.md 固定テンプレ

各フェーズの設計 md は以下の節を必ず含む（CODEX レビューの一貫性確保）：

1. 目的（1行）
2. 触るファイル（既存／新規それぞれ列挙）
3. 触らないファイル（明示）
4. 実装手順
5. ブランド分離チェック（LP 本文・SNS 本文に他ブランド名・個人名が混入していないか）
6. 個人名露出チェック（/makoto/ ハブ外で「まこと」が出ていないか、Article / LP / SNS / note フッターでの不出を含む）
7. JSON-LD dead link チェック（@id 参照の網羅、logo 実存、sameAs の実在 URL 限定）
8. CODEX 設計レビュー結果（指摘＋反映状況）
9. CODEX コードレビュー結果（指摘＋反映状況）
10. 完了条件

### 全フェーズ共通の完了条件

- CODEX レビューの「強い懸念」がゼロ件 or 全件 ADR 化されている（Phase 0 だけでなく全 Phase）

---

## CODEX レビューの組み込み方

各フェーズで 2 回 CODEX を呼ぶ：

1. **設計 md レビュー**：`phase_N_design.md` を書いた直後、実装に入る前に `codex-review` スキルで観点抜けを潰す。
2. **コードレビュー**：実装完了後、コミット前に `codex-review` で観点漏れを潰す。

CODEX には毎フェーズ共通で以下を必ず確認させる：

- AkariLab ブランドトーン（太字マーカー禁止／人物名匿名化／開発者用語禁止／淡々具体）が新規 HTML 本文で破られていないか
- ブランド分離ルール（もやログ／りぴメモ／ひだまり相互言及禁止）が新規ページ本文で破られていないか
- ココナラ表現ルール（アントワークス・伝説のすた丼屋・デンバープレミアム・ジョイフル等の固有名詞 NG）に違反していないか
- 対外署名が「AkariLab」名義に統一され、個人名「まこと」が /makoto/ ハブ外で露出していないか
- @id 参照の dead link がグラフ全体でゼロか
- 触らないと宣言した既存ファイル（text-generator/note-poster/post_to_x の指定行以外）が本当に触られていないか

各フェーズ固有の観点はフェーズ詳細に記載。

---

## フェーズ詳細

### Phase 0：設計 md 確定 + 全体 CODEX レビュー

**目的**：この plan ファイルを `akarilab-site/docs/aiseo/00_overall_design.md` として固定し、CODEX に観点抜けを潰させる。

**触るファイル（新規）**：
- `C:/Users/user/akarilab-site/docs/aiseo/00_overall_design.md`（この plan を反映）
- `C:/Users/user/akarilab-site/docs/aiseo/decisions/`（ADR 置き場、空ディレクトリ）

**完了条件**：
- 00_overall_design.md が main にマージ済み
- CODEX レビューの「強い懸念」がゼロ件 or 全件 ADR 化されている

---

### Phase 1：サイト基盤整備

**目的**：以降のページ追加でベタ HTML が増殖しないための土台を作る。AI クローラに「クロール歓迎」を明示する。

**触るファイル**：
- 新規 `C:/Users/user/akarilab-site/scripts/build_pages.py`（partial 置換のみのワンファイルビルド）
- 新規 `C:/Users/user/akarilab-site/assets/css/site.css`（既存 `:root` を統合）
- 新規 `C:/Users/user/akarilab-site/assets/partials/head-common.html`
- 新規 `C:/Users/user/akarilab-site/assets/partials/footer-common.html`
- 新規 `C:/Users/user/akarilab-site/assets/partials/jsonld/`（テンプレ集）
- 新規 `C:/Users/user/akarilab-site/sitemap.xml`
- 新規 `C:/Users/user/akarilab-site/robots.txt`
- 新規 `C:/Users/user/akarilab-site/llms.txt`
- 新規 `C:/Users/user/akarilab-site/.nojekyll`
- 新規 `C:/Users/user/akarilab-site/.github/workflows/aiseo-check.yml`
- 既存 `index.html`／`hidamari.html`／規約系4枚を `<!-- include: -->` 形式に書き換え（見た目変えない）

**robots.txt 方針**：
```
User-agent: *
Allow: /

User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

Sitemap: https://akarilab.org/sitemap.xml
```

**llms.txt 方針**（簡易サイトマップ＋ブランド注記）：
```
# AkariLab

> 現場の「困った」から生まれた LINE Bot 群を運営するブランド。
> 個別プロダクト（ひだまり／もやログ／りぴメモ）はそれぞれ独立した世界観で運営される。

## Brand
- /                    AkariLab トップ
- /akarilab/           ブランド一次定義
- /makoto/             運営者プロフィール（深掘り）

## Products
- /hidamari/           ひだまり（学習 Bot）
- /moyalog/            もやログ（感情ログ Bot）
- /repimemo/           りぴメモ（接客メモ Bot）

## Articles
- /articles/           note 記事ハブ
- /articles/ai-9months/  連載「触り始めて9ヶ月の記録」
```

**CI ワークフロー**（aiseo-check.yml）：
- partial 適用差分が無いことを検証（`build_pages.py --dry-run`）
- HTML5 バリデーション（html5validator）
- JSON-LD スキーマ検証（pyld + jsonschema）+ @id 参照先存在チェック
- 内部リンク全数走査（lychee）、外部はレート制限
- 画像 alt 未設定検出（pyquery）
- sitemap.xml と実ファイルパスの突合

**追加方針**：
- ADR `decisions/0001-brand-isolation-vs-aiseo-aggregation.md` を本フェーズで commit 含める（Phase 0 で先行作成済）
- canonical / noindex 方針を明文化：
  - 規約系4ページ（tokushoho/billing-policy/terms-of-service/privacy-policy）：canonical = 自 URL、noindex なし
  - 将来の Article 要約ハブ（Phase 5）：canonical を**自 URL（akarilab.org/articles/...）**にする。`isBasedOn` で note 原文を参照するが、canonical は note にしない（要約ハブはオリジナル要約コンテンツとして扱う、Phase 5 で再確認）
- AI クローラ allowlist は流動的なため、本フェーズの CODEX レビュー時に 2026-05 時点の最新動向を必ず確認（GPTBot / ClaudeBot / PerplexityBot / Google-Extended / CCBot / Bytespider / Applebot-Extended など）

**CODEX 固有観点**：
- partial 置換スクリプトで XSS/不正 HTML が生成されないか
- robots.txt の AI クローラ allowlist 抜け漏れ（2026-05 時点の最新）
- llms.txt の最新仕様（2026-05 時点）整合性、llms-full.txt の要否（初期は llms.txt のみで十分）
- canonical / noindex 方針が規約ページ・将来のミラーで適切か

**完了条件**：
- `build_pages.py` が冪等（連続2回実行で diff ゼロ）
- 既存6ページが見た目変化ゼロでデプロイ済み
- /sitemap.xml /robots.txt /llms.txt が 200
- aiseo-check.yml が main で全件 green

---

### Phase 2：/akarilab/ ＋ Organization JSON-LD ＋ /makoto/ 個人プロフィール

**目的**：グラフの中心ノード Organization を一次定義し、深掘り経路として Person を /makoto/ に置く。Organization が producer/publisher としてあらゆる SoftwareApplication / Article から参照される起点になる。

**触るファイル（新規）**：
- `C:/Users/user/akarilab-site/akarilab/index.html`（Organization 一次定義）
- `C:/Users/user/akarilab-site/makoto/index.html`
- `C:/Users/user/akarilab-site/makoto/profile/index.html`（FAQPage 含む）
- `C:/Users/user/akarilab-site/makoto/timeline/index.html`
- `C:/Users/user/akarilab-site/makoto/contact/index.html`
- `C:/Users/user/akarilab-site/assets/partials/jsonld/organization.html.tmpl`
- `C:/Users/user/akarilab-site/assets/partials/jsonld/person.html.tmpl`
- `C:/Users/user/akarilab-site/assets/partials/jsonld/faq.html.tmpl`

**Organization JSON-LD（akarilab.org/akarilab/）**：
```jsonld
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://akarilab.org/#org",
  "name": "AkariLab",
  "url": "https://akarilab.org/",
  "logo": "https://akarilab.org/assets/logo/akarilab.png",
  "description": "現場の「困った」から生まれた LINE Bot 群を運営するブランド。",
  "founder": { "@id": "https://akarilab.org/makoto/#person" },
  "sameAs": [
    "https://note.com/akarilab",
    "https://x.com/waveblasttaiyo",
    "https://x.com/makochinta1",
    "https://x.com/moyalog",
    "https://x.com/repimemo",
    "https://www.instagram.com/akarilab_jp/",
    "https://github.com/makokoid-eng"
  ]
}
```

**Person JSON-LD（akarilab.org/makoto/）**：
```jsonld
{
  "@context": "https://schema.org",
  "@type": "Person",
  "@id": "https://akarilab.org/makoto/#person",
  "name": "まこと",
  "url": "https://akarilab.org/makoto/",
  "jobTitle": "店舗運営マネージャー / 個人開発者",
  "description": "外食業で21年の現場経験を持ち、店長賞を3年連続受賞（2022地方店舗賞・2023優秀店長賞・2024最優秀店長賞）。並行して AkariLab を運営し、LINE Bot 群を個人開発している。",
  "knowsAbout": ["LINE Bot 設計", "店舗運営", "外食業オペレーション", "教育AI", "個人開発", "Cloud Functions", "Firestore", "業務改善"],
  "award": ["店長賞 地方店舗賞 (2022)", "店長賞 優秀店長賞 (2023)", "店長賞 最優秀店長賞 (2024)"],
  "sameAs": [
    "https://github.com/makokoid-eng"
  ]
}
```

注：
- `Person.founder` は schema.org 仕様上不自然（Organization 側の `Organization.founder → Person@id` だけで founder 関係は十分表現される）。Person 側には置かない。
- `sameAs` には**実在・公開済みの URL のみ**を入れる。ココナラ正式 URL は確定後に追加（Phase 2 着手時に `coconala_profile.md` を確認し、確定 URL があれば追加、無ければ未掲載）。
- Person.name = "まこと" の露出範囲：**akarilab.org/makoto/ 配下のページ本文・Person JSON-LD のみ**に限定。Article / LP / SNS bio / note 記事フッター・meta description・og:description には出さない（Phase 各完了条件で機械検査）。

**ココナラ表現ルール厳守**：
- jobTitle に「アントワークス エリアマネージャー」と書かず、「店舗運営マネージャー」にぼかす（coconala_profile.md §表現ルール準拠）
- `worksFor.name` には会社名を入れない、`description` に業界カテゴリのみ
- `award` の会社名は伏せ、賞名のみ

**/makoto/ ページ構成（淡々トーン例）**：
```
まこと
店舗運営の現場で21年、いまは AkariLab で LINE Bot 群を運営している。
2024年夏に生成 AI を本格的に使い始めて、2025年10月に最初のコードを Git に保存した。
2026年5月時点で LINE Bot を5本並行運営している。

経歴は /makoto/profile/、AI 利用タイムラインは /makoto/timeline/、連絡先は /makoto/contact/ に置いてある。
```

**CODEX 固有観点**：
- Person.jobTitle / award / worksFor がココナラ表現ルール（固有企業名 NG）の範囲内か
- Organization.sameAs に過不足ないか
- AkariLab 署名統一方針との整合（Person ノードを Organization の founder として裏に置く構造）
- FAQPage の Q&A が「AI が引用したくなる粒度」になっているか

**完了条件**：
- /akarilab/ /makoto/ 全4ページ 200
- Google Rich Results Test で Organization・Person・FAQPage・BreadcrumbList の警告ゼロ
- @id 参照の dead link ゼロ

---

### Phase 3：既存ページの JSON-LD 強化＋/hidamari/ 移設

**目的**：既存 / と /hidamari.html を Organization グラフに接続する。

**触るファイル**：
- 既存 `C:/Users/user/akarilab-site/index.html` 改修（Organization 参照 + ItemList JSON-LD 追加）
- 既存 `C:/Users/user/akarilab-site/hidamari.html` を新規 `/hidamari/index.html` へ移設、旧パスは meta refresh で代替（GH Pages の制約上）
- 既存規約4枚に BreadcrumbList のみ追加

**SoftwareApplication ひだまり JSON-LD**：
```jsonld
{
  "@type": "SoftwareApplication",
  "@id": "https://akarilab.org/hidamari/#app",
  "name": "ひだまり",
  "applicationCategory": "EducationalApplication",
  "operatingSystem": "LINE",
  "description": "算数・数学が苦手な小中学生のための、つまずき遡行型 AI 家庭教師 LINE Bot。",
  "producer": { "@id": "https://akarilab.org/#org" },
  "publisher": { "@id": "https://akarilab.org/#org" },
  "url": "https://akarilab.org/hidamari/",
  "featureList": ["つまずき遡行", "答えを教えないソクラテス対話", "先生選択（そうま・かいと）", "実力チェック診断"],
  "audience": { "@type": "EducationalAudience", "educationalRole": "student" }
}
```

**CODEX 固有観点**：
- meta refresh による旧 URL 退避が SEO/AISEO に与える影響
- 旧 /hidamari.html がどこで被リンクされているかの調査範囲

**完了条件**：
- 旧 URL アクセスで2秒以内に新 URL へ遷移
- 全6ページに最低1つの JSON-LD ノード（BreadcrumbList 含む）
- グラフ全体の @id 参照が全て解決

---

### Phase 4：/moyalog/ /repimemo/ 本格 LP 新設

**目的**：もやログ／りぴメモを LINE 登録 URL だけ持つ広告から実 LP に格上げし、Organization から producer 経由で接続。LP 本文では AkariLab／個人名／他ブランド名を一切出さない（フッターのみ © 2026 AkariLab）。

**触るファイル（新規）**：
- `C:/Users/user/akarilab-site/moyalog/index.html`
- `C:/Users/user/akarilab-site/moyalog/features/index.html`
- `C:/Users/user/akarilab-site/moyalog/voices/index.html`（体験談）
- `C:/Users/user/akarilab-site/moyalog/assets/og.png`
- `C:/Users/user/akarilab-site/repimemo/index.html`（個人モード主役、伏線期間中の構成）
- `C:/Users/user/akarilab-site/repimemo/store/index.html`（店舗モードは退避、伏線明け 2026-07-11 で index 昇格）
- `C:/Users/user/akarilab-site/repimemo/voices/index.html`
- `C:/Users/user/akarilab-site/repimemo/assets/og.png`

**ブランド分離の運用**：
- LP 本文（H1〜CTA）には AkariLab／個人名／他プロダクト名を一切書かない
- footer に「© 2026 AkariLab」のみ（akarilab.org への可視リンクは置かない）
- JSON-LD で `SoftwareApplication.producer = {@id: "https://akarilab.org/#org"}` で接続（人間 UI には出ず、AI クローラだけが拾う）
- もやログ LP からりぴメモ LP への可視リンク禁止、その逆も禁止

**SoftwareApplication もやログ JSON-LD**：
```jsonld
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "@id": "https://akarilab.org/moyalog/#app",
  "name": "もやログ",
  "applicationCategory": "LifestyleApplication",
  "operatingSystem": "LINE",
  "url": "https://akarilab.org/moyalog/",
  "description": "気持ちをそのまま置いていける LINE Bot。タップ1回で今の気分を記録、自分のパターンが見えてくる。",
  "producer": { "@id": "https://akarilab.org/#org" },
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "JPY" },
  "potentialAction": {
    "@type": "SubscribeAction",
    "target": "https://lin.ee/q1k7v8F"
  }
}
```

並列で `FAQPage`（FAQ セクション）と `Review[]`（体験談）を別ブロックで配置。Review.reviewRating は入れない（評価語禁止）、reviewBody のみ。

**りぴメモ industry 伏線期間（2026-05-16〜2026-07-10）の運用**：
- LP は個人モードを index に置き、店舗モードは /store/ サブパスに退避
- X 伏線投稿は LP に誘導しない（既存ルール）。bio リンクで bio 経由のみ到達
- 伏線明けに index と /store/ を入れ替え、repimemo-post-drafter の industry モード終了と同期

**体験談編集ルール**（hidamari-usage-collector / repimemo-usage-collector 出力を素材に）：
- ユーザー識別情報を出さない（LINE userId、店舗名、本名、地域、年齢）
- 性別・職業・年代は本人申告がある場合のみ「30代女性」「夜職スタッフ」程度
- 引用は語尾のみ調整、原文 DM 由来は明示
- 評価語のみの体験談は採用しない（具体的行動・心の動きが入っているもののみ）

**画像最適化チェック（Phase 4 必須）**：
- 全画像 WebP 配信（フォールバックで PNG/JPG 並列保持）
- `<img>` に `width` / `height` 属性必須（Core Web Vitals CLS 防止）
- `loading="lazy"` をファーストビュー以外の画像に付与
- alt 属性必須（CI で機械検査、Phase 1 の aiseo-check.yml 範囲内）
- og.png は 1200x630、ファイルサイズ 200KB 以下を目安

**CODEX 固有観点**：
- LP 本文に AkariLab／個人名／他ブランド名が露出していないか
- voices/ 体験談に identifying information が含まれていないか
- りぴメモ伏線期間の運用切替トリガが design にあるか
- LP 本文のトーンがプロモ口調になっていないか（「最高」「ぜひ」「変わる」NG）
- 画像最適化チェック項目を全て満たしているか

**完了条件**：
- 両 LP が 200、リッチリザルトテスト OK
- LINE 登録 URL からの流入計測（UTM 付与済み）
- 既存 index.html の両カードからのリンクが新 LP に張り替え済み
- 画像最適化チェック全項目クリア

---

### Phase 5：/articles/ 連載ハブ＋個別要約ハブ

**目的**：note 記事のうち主要なもの、特に 2026-05-17 開始の連載「触り始めて9ヶ月の記録」を Article 構造化し、Organization グラフに接続。

**呼称の整理**：「ミラー」ではなく「**要約ハブ**」と呼ぶ。目的は note 記事の全文転載ではなく、AI 引用補助のための JSON-LD 付き要約ページ。

**触るファイル（新規）**：
- `C:/Users/user/akarilab-site/articles/index.html`（全主要記事 ItemList）
- `C:/Users/user/akarilab-site/articles/ai-9months/index.html`（連載親 + hasPart）
- `C:/Users/user/akarilab-site/articles/ai-9months/{slug}.html` × 連載記事数
- 新規 `C:/Users/user/akarilab-site/scripts/sync_note_articles.py`（note URL リスト→ミラー HTML 生成）
- 新規 `C:/Users/user/akarilab-site/data/articles.yml`（記事メタの単一情報源：slug, title, note_url, published, summary, series）

**運用フロー（二経路、RSS fallback 必須）**：
1. 経路 A：note-poster が投稿成功 → `note_post_success_{date}.json` を出力（既存）
2. 経路 B（fallback）：note.com/akarilab/rss を取得して articles.yml に未掲載記事を追記
3. `sync_note_articles.py` が両経路を走査して articles.yml 更新（経路 A が落ちても経路 B で復旧可能）
4. `build_pages.py` が articles.yml から {slug}.html を再生成
5. main にコミット → GH Pages 反映

**要約ハブ本文方針（全文転載ゼロ、Phase 5 必須）**：
- 全文転載しない、要約500字 + JSON-LD + note 原文へのリンクのみ
- 有料記事は「タイトル + 公開日 + 1段落要約のみ」に固定、本文要素は転載しない
- `mainEntityOfPage` を note URL に固定（正規 URL は note 側）
- `isBasedOn` を note URL に設定（参照元の明示）
- 要約ハブ自身の canonical は**自 URL（akarilab.org/articles/...）**にする：要約ハブは「note 記事を要約したオリジナル要約コンテンツ」として独立した存在。重複コンテンツ判定は本文を要約のみに留めることで回避（全文転載ゼロが前提）

**設計書での明記事項**：
- 要約ハブの目的は「AI 引用補助ページ」であって正規記事ではない（人間読者には note 原文を読んでもらう）
- 連載 Phase 1 の有料記事については本文要素を一切ミラーしない（タイトル + 公開日 + 1段落要約のみ）

**Article 個別記事 JSON-LD**：
```jsonld
{
  "@type": "Article",
  "@id": "https://akarilab.org/articles/ai-9months/{slug}/#article",
  "headline": "{{title}}",
  "datePublished": "{{published}}",
  "author": { "@id": "https://akarilab.org/#org" },
  "publisher": { "@id": "https://akarilab.org/#org" },
  "isPartOf": { "@id": "https://akarilab.org/articles/ai-9months/#series" },
  "isBasedOn": "{{note_url}}",
  "mainEntityOfPage": "{{note_url}}",
  "abstract": "{{summary}}"
}
```

author/publisher を Organization にすることで、AkariLab 署名統一方針と整合。

**CODEX 固有観点**：
- 有料記事の要約ハブが「タイトル + 公開日 + 1段落要約のみ」に留まっているか（本文要素ゼロを機械検査）
- 要約ハブのコンテンツ量が「薄いコンテンツ」判定に触れないか（500字 + JSON-LD + 関連リンクで密度確保）
- articles.yml と note-poster ログ・RSS の同期で二重起票が起きないか
- canonical 方針（要約ハブは自 URL、`mainEntityOfPage` は note URL、`isBasedOn` は note URL）が整合しているか

**完了条件**：
- 連載親＋連載開始時点の個別記事が全て 200
- sync_note_articles.py を Cron で毎日1回回す運用が確立、note-poster ログと RSS の二経路が両方稼働
- リッチリザルトテストで Article + BreadcrumbList が両方 OK
- 要約ハブ全件で「全文転載ゼロ」を機械検査クリア（note 原文との重複率が一定以下）

---

### Phase 6：text-generator フッター挿入＋note-poster 関連リンク機構

**目的**：note 記事本文側に AkariLab 署名フッター＋関連リンクを毎回確実に挿入。個人名「まこと」は出さない。

**触るファイル**：
- 既存 `C:/Users/user/.claude/skills/text-generator/SKILL.md` 改修：「## 構造化フッターブロック」セクションを追加
- 既存 `C:/Users/user/.claude/skills/note-poster/SKILL.md` 改修：**投稿前のフッター存在検査を必須化**（フッターが本文に含まれない記事は note 投稿を中断、エラー出力）
- 既存 `C:/Users/user/.claude/skills/note-poster/scripts/note_poster.py` 改修：投稿前フッター検査ロジック追加、投稿成功時に `note_post_success_{date}.json` 出力（Phase 5 同期用）

**フッターブロック仕様**：

```
---
書き手：AkariLab
LINE Bot を中心に、現場の「困った」から生まれた小さな道具を作っているブランドです。
ブランド一覧は [akarilab.org](https://akarilab.org/) 、note 記事のまとめは [akarilab.org/articles/](https://akarilab.org/articles/) に置いています。

この記事の関連：
- [タイトルA](URL) — 1行要約
- [タイトルB](URL) — 1行要約
- [タイトルC](URL) — 1行要約
```

連載記事のときだけ、このブロックの上に「連載」専用ブロックを追加：

```
連載「触り始めて9ヶ月の記録」第N話
公開日：YYYY-MM-DD
連載目次は [akarilab.org/articles/ai-9months/](https://akarilab.org/articles/ai-9months/)
```

**関連記事3本の自動選定ロジック**：
1. 同シリーズ続編（articles-meta.md の published 順で前1本）
2. 同テーマの過去記事（topics タグ重なり最大）
3. 起点エピソード共通の過去記事（story_category 一致）
- 同日素材は除外（feedback_articles_meta_check 準拠）

**AkariLab トーン適合**：
- フッターも太字マーカー禁止、淡々と並べる
- 「ぜひ」「合わせて」「読んでみて」勧誘語禁止
- リンクテキストは記事タイトルそのまま

**CODEX 固有観点**：
- フッターが AkariLab トーン（太字 NG・開発者用語 NG・淡々）違反していないか
- prev/next 自動選択ロジックで使い回しパターンが出ないか
- 個人名「まこと」が混入していないか
- text-generator の品質ルール（800-1200 字目安）にフッターを含めるか別カウントにするか

**完了条件**：
- text-generator 出力 article_*.md に常にフッターが含まれる
- note-poster 投稿成功率がフェーズ前と変わらない（リグレッションなし）
- 1記事を実投稿して note 上で関連リンクが押せることを目視確認

---

### Phase 7A：4 アカウント post_to_x.py の User-Agent 改修

**目的**：4 ブランドの X 自動投稿の User-Agent を akarilab.org サブパスに統一する（1行差分のみ、Phase 2 完了直後に独立実施可能）。

**触るファイル**：
- 既存 `C:/Users/user/hidamari/scripts/post_to_x.py` 該当行：UA を `+https://akarilab.org/hidamari/` に
- 既存 `C:/Users/user/moyalog/scripts/post_to_x.py` 該当行：UA を `+https://akarilab.org/moyalog/` に
- 既存 `C:/Users/user/repimemo/scripts/post_to_x.py` 該当行：UA を `+https://akarilab.org/repimemo/` に
- 既存 `C:/Users/user/makochinta1-poster/scripts/post_to_x.py` 該当行：UA を `+https://akarilab.org/articles/` に

**CODEX 固有観点**：
- 4 UA 変更が tweepy 経由で副作用（Rate Limit 観測値）を起こさないか
- UA 文字列に typo / 旧 URL の混入がないか
- UA 1行変更でもコードレビューを必ず1回入れる

**完了条件**：
- 4 スクリプトの diff が UA 行のみ
- 翌日の自動投稿が 4 アカウント全部で成功
- Rate Limit 観測値が前日と同レンジ

---

### Phase 7B：X bio 設計書とブランド別反映（手動適用）

**目的**：4 アカウントの bio・固定ツイート・IG キャプションの仕様を設計書に明文化、ブランド別の反映は手動で実施。Phase 4 完了（moyalog/repimemo LP 公開）後に着手することで、bio に書く URL が実存することを保証。

**触るファイル**：
- 新規 `C:/Users/user/akarilab-site/docs/aiseo/x_account_bio_spec.md`（bio 仕様書）

**bio 仕様（要点）**：
- `@waveblasttaiyo` (AkariLab メイン)：bio 末尾に `akarilab.org/`、固定ツイートに akarilab.org トップ
- `@makochinta1` (note 拡散)：bio に「AkariLab の note 記事の告知。https://akarilab.org/articles/」、個人名は出さない
- `@moyalog`：bio 末尾に `lin.ee/q1k7v8F | akarilab.org/moyalog/`（ブランド名・他ブランド名は出さない）
- `@repimemo`：bio 末尾に `lin.ee/HbV7Ehv | akarilab.org/repimemo/`、伏線期間中は同じ

**Instagram キャプション（@akarilab_jp）**：
末尾に固定シグネチャ：
```
---
AkariLab
https://akarilab.org/
```

**CODEX 固有観点**：
- bio 変更指示文が個人名露出禁則を破っていないか
- @waveblasttaiyo と @makochinta1 の役割分担（両方が AkariLab を主にする設計）の妥当性
- bio に書く URL（akarilab.org/moyalog/ など）が実際にデプロイ済みであることを Phase 4 完了確認で担保

**完了条件**：
- bio 設計書がコミット済み
- 4 アカウントの bio が設計書通りに更新済み（X 側で目視確認）
- IG キャプション固定シグネチャが次回投稿から有効

---

### Phase 8：引用モニタ拡張（AISEO クエリを既存 cron に乗せる）

**目的**：手動の引用検知運用を完全に排除する。既存 `akarilab-note/scripts/check_llm_citations.py` の `QUERIES` リストに AISEO 計画用クエリを追加し、月初 cron で AkariLab ブランド・運営者・連載・コンサル導線の引用状況を自動ログ化する。

**触るファイル**：
- 既存 `C:/Users/user/akarilab-note/scripts/check_llm_citations.py`：`QUERIES` リストに4エントリ追加
- 触らない：`.github/workflows/check-llm-citations.yml`（クエリ拡張のみで cron 構造は無変更）、`docs/llm_citation_log.md`（自動追記される）

**追加クエリ**（`QUERIES` 末尾に append）：
```python
{
    "query": "AkariLab",
    "brand": "AkariLab",
    "expected_domains": ["akarilab.org", "note.com/akarilab"],
},
{
    "query": "AkariLab 運営者",
    "brand": "AkariLab (founder)",
    "expected_domains": ["akarilab.org/makoto", "akarilab.org"],
},
{
    "query": "触り始めて9ヶ月の記録",
    "brand": "連載",
    "expected_domains": ["note.com/akarilab", "akarilab.org/articles/ai-9months"],
},
{
    "query": "業務改善 LINE Bot 相談",
    "brand": "コンサル導線",
    "expected_domains": ["coconala.com", "akarilab.org/makoto"],
},
```

**着手タイミング**：
- Phase 2 完了（/akarilab/ /makoto/ デプロイ済）後にクエリ「AkariLab」「AkariLab 運営者」「業務改善 LINE Bot 相談」を追加
- Phase 5 完了（/articles/ai-9months/ デプロイ済）後にクエリ「触り始めて9ヶ月の記録」を追加
- 2 段階に分けるのは、期待ドメインが実在しない段階で追加するとログが「miss」だらけになって判定ノイズになるため

**CODEX 固有観点**：
- 追加クエリの `expected_domains` リストに過不足ないか（特に lin.ee / note.com の表記揺れ）
- 既存 3 ブランドクエリとのキーワード衝突がないか（例：「AkariLab」と「ひだまり LINE Bot」のレスポンス重複）
- API レート制限を超えない（クエリ数が 3 → 7 に増えるため、エンジン別の月12回 → 月28回相当）

**完了条件**：
- 追加クエリが QUERIES に入っており、ローカル `python scripts/check_llm_citations.py --dry-run` で動作確認済
- 次月初 cron 実行後、`llm_citation_log.md` に 7 ブランド × 4 エンジン = 28 行のログが追記されている
- 期待ドメインヒット率 0% でも仕組み正常動作扱い（AISEO 累積効果が出るのを待つフェーズ）

---

## 累積効果設計（時間経過で効いてくる）

### 3ヶ月／6ヶ月／12ヶ月後の目標状態

| 時期 | 検索クエリ | 期待引用元 |
|---|---|---|
| 3ヶ月後（2026-08） | 「AkariLab とは」 | akarilab.org/ + /akarilab/ |
| 3ヶ月後 | 「触り始めて9ヶ月の記録 第1話」 | note 記事 + /articles/ai-9months/ |
| 6ヶ月後（2026-11） | 「ひだまり LINE Bot 評判」 | /hidamari/ + 関連 note 記事3-5本 |
| 6ヶ月後 | 「もやログ 使い方」 | /moyalog/ + FAQ |
| 6ヶ月後 | 「44歳から個人開発」 | 連載第1話 + 関連 note 記事 |
| 12ヶ月後（2027-05） | 「業務改善 LINE Bot 相談」 | ココナラ + /makoto/ + 関連記事 |
| 12ヶ月後 | 「AkariLab 運営者」 | /makoto/ + /akarilab/ |
| 12ヶ月後 | 「りぴメモ 接客」 | /repimemo/（個人＋店舗両モード） |

### 月次運用タスク

| タスク | 頻度 | 担当 |
|---|---|---|
| note 新記事追加 | 週2-3本 | text-generator + note-poster（既存） |
| /articles/ 索引更新 | 月1（自動） | sync_note_articles.py（Phase 5 で新設） |
| /makoto/timeline/ 追記 | 主要イベント発生時 | 手動 |
| LP 体験談追加 | 月1（条件満たすものがあれば） | usage-collector → 編集 → LP 反映 |
| FAQ 拡充 | 質問が3件以上溜まったら | 手動 |
| sameAs 追加 | 新規 SNS アカウント開設時 | 手動、JSON-LD 更新 |
| 構造化データ検証 | 月1 | Google リッチリザルトテスト手動 |
| 4 エンジン引用検知 | 月1（自動） | `akarilab-note/scripts/check_llm_citations.py` を GitHub Actions 月初 cron 実行（既存） |

### 効果測定方法

**既存自動化**：`akarilab-note/scripts/check_llm_citations.py` が月初 1 日 09:00 JST に GitHub Actions cron で自動実行。3 ブランド × 4 エンジン = 12 チェックを `akarilab-note/docs/llm_citation_log.md` に追記。API キー未取得エンジンは `skipped` 記録（後日 secrets 追加で自動稼働）。

**Phase 8 で拡張**：本 AISEO 計画で監視したい以下のクエリを既存 `QUERIES` リストに追加（Phase 2 と Phase 5 完了後に着手）：

```python
# Phase 8 で QUERIES に追加するエントリ
{
    "query": "AkariLab",
    "brand": "AkariLab",
    "expected_domains": ["akarilab.org", "note.com/akarilab"],
},
{
    "query": "AkariLab 運営者",
    "brand": "AkariLab (founder)",
    "expected_domains": ["akarilab.org/makoto", "akarilab.org"],
},
{
    "query": "触り始めて9ヶ月の記録",
    "brand": "連載",
    "expected_domains": ["note.com/akarilab", "akarilab.org/articles/ai-9months"],
},
{
    "query": "業務改善 LINE Bot 相談",
    "brand": "コンサル導線",
    "expected_domains": ["coconala.com", "akarilab.org/makoto"],
},
```

ハルシネーション検出時（fact_check_status が `possible_issue`、または期待ドメインに akarilab.org が含まれず外部サイトのみが引用された場合）は /makoto/ /akarilab/ の事実塊を補強（より明確な定義文を追加、年表を密にする）。手動運用は不要（ログを月1で読むだけ）。

---

## リスクと対処

| # | リスク | 影響 | 対処 |
|---|---|---|---|
| R1 | note 非公式 API 仕様変更で note-poster が失敗 → Phase 5 のミラー同期も連鎖停止 | 高 | sync_note_articles.py を note-poster ログだけでなく note.com/akarilab の RSS（/rss）からも fallback 取得できる二経路設計にする |
| R2 | Person スキーマの jobTitle や award が個人特定リスクになる | 中 | jobTitle は「店舗運営マネージャー」にぼかす。worksFor.name は入れない。award は賞名のみ。Phase 0 / Phase 2 の CODEX レビューで再確認 |
| R3 | もやログ／りぴメモ LP が akarilab.org サブパス配置されることで AI が「同一運営」と判定 → ブランド分離ルールと表面上は矛盾 | 中 | ブランド分離ルールは「SNS 発信本文・LP 本文での相互言及禁止」であり、「同一運営者の不可視化」ではない。ADR `decisions/0001-brand-isolation-vs-aiseo-aggregation.md` で明文化 |
| R4 | Article ミラーが Google 重複コンテンツ判定を受ける | 中 | mainEntityOfPage を note URL に固定、ミラー本文は要約500字 + リンクのみ（全文転載しない）。Phase 5 CODEX レビュー必須 |
| R5 | llms.txt は仕様流動的、対応エンジン限定的 | 低 | コストゼロで実装、ただし単独効果に依存しない。robots.txt allowlist と Organization JSON-LD が本命 |
| R6 | GitHub Pages が Jekyll を勝手に走らせて partial の `<!-- include -->` を誤処理 | 低 | リポジトリルートに `.nojekyll` ファイルを置く（Phase 1 含む） |
| R7 | text-generator のフッター追加で本文文字数が増え、品質ルール 800-1200 字を超える | 低 | フッターは品質ルール検査の対象外と明示（Phase 6 SKILL.md 改修で明記） |
| R8 | AkariLab 署名統一で「個人開発者の物語」のフックが弱くなる | 中 | /makoto/ ハブと連載「触り始めて9ヶ月の記録」内でのみ個人を出す。深掘りユーザーだけが個人名に到達する設計で両立 |

---

## 残決定事項（Phase 0-8 の各着手前にユーザー確認）

| # | 残課題 | デフォルト案 | 確定タイミング |
|---|---|---|---|
| D1 | Person.jobTitle に「店舗運営マネージャー」表記でぼかす案で OK か | OK（ココナラ表現ルール準拠） | Phase 2 着手前 |
| D2 | 旧 /hidamari.html の扱い（meta refresh で /hidamari/ に統一、最低6ヶ月は旧 URL 残す） | meta refresh、Sitemap から除外 | Phase 3 着手前 |
| D3 | Article ミラー本文量（要約500字 + JSON-LD + リンクのみ） | 要約のみ | Phase 5 着手前 |
| D4 | 連載 Phase 1 有料記事のミラー方針（タイトル + 要約のみで全文非掲載） | タイトル + 公開日 + 1段落要約のみ | Phase 5 着手前 |
| D5 | @waveblasttaiyo / @makochinta1 の役割分担（両方 AkariLab メイン、片方は記事拡散特化） | @waveblasttaiyo＝AkariLab トップ誘導、@makochinta1＝記事拡散 + /articles/ 誘導 | Phase 7 着手前 |

---

## Verification（フェーズ単位の検証手順）

### 各フェーズ共通

1. ローカルで `python scripts/build_pages.py` を実行、エラーゼロを確認
2. ローカルで `python -m http.server` でプレビュー、見た目崩れがないことを目視確認
3. main へ push、GitHub Actions の aiseo-check.yml が green を確認
4. 本番 URL（https://akarilab.org/...）で 200 と JSON-LD 含有を curl で確認
5. Google リッチリザルトテスト（https://search.google.com/test/rich-results）で警告ゼロを確認
6. codex-review スキルで設計 md とコード両方をレビュー、強い懸念ゼロを確認

### Phase 5 / 6 の追加検証

- text-generator で 1 記事を生成、フッターが期待通り入っているか目視
- note-poster で実投稿、note 上で関連リンクが押せて目的ページに飛ぶか確認
- sync_note_articles.py が note 投稿成功ログを正しく拾い articles.yml に追記するか確認

### Phase 7 の追加検証

- 翌朝の 4 アカウント自動投稿が全部成功（GitHub Actions の post_to_x.yml ログ確認）
- X API の Rate Limit 観測値が前日と同レンジか確認

### 4 エンジン引用検知（自動・月次）

**手動運用は行わない**。既存 `akarilab-note/scripts/check_llm_citations.py` が月初 cron で自動実行され、結果は `akarilab-note/docs/llm_citation_log.md` に追記される。Phase 8 で本 AISEO 計画用のクエリ（AkariLab / AkariLab 運営者 / 触り始めて9ヶ月の記録 / 業務改善 LINE Bot 相談）を QUERIES に追加することで、AISEO の累積効果が自動的にログ化される。

月1 の手動作業は次のみ：
1. `akarilab-note/docs/llm_citation_log.md` の最新月分を読む（5 分）
2. 期待ドメインヒット率が前月より低下した場合、当該クエリのファクト塊を補強する（必要時のみ）

---

## 主要参照ファイル

実装着手時に必ず読むべきファイル：

- `C:/Users/user/akarilab-site/index.html`（既存トーン・CSS の参照元）
- `C:/Users/user/akarilab-site/hidamari.html`（LP 構造の既存テンプレ）
- `C:/Users/user/coconala-prep/coconala_profile.md`（Person 素材の正本、表現ルール §4-5）
- `C:/Users/user/.claude/skills/text-generator/SKILL.md`（フッター挿入対象）
- `C:/Users/user/.claude/skills/note-poster/scripts/note_poster.py`（投稿ログ出力追加対象）
- `C:/Users/user/akarilab-note/docs/articles-meta.md`（関連記事リンク自動選定の素材）
- `C:/Users/user/akarilab-strategy/00_briefing.md`（ブランド構造の正本）

---

## 次に動くもの

Phase 0 は完了状態：
- 本ファイル `docs/aiseo/00_overall_design.md` 設置済
- ADR `decisions/0001-brand-isolation-vs-aiseo-aggregation.md` 設置済
- CODEX 全体設計レビュー実行済（指摘 7 点を本ファイルに反映済）
- 月次引用検知の自動化方針を Phase 8 として定義済

次アクション：
1. ユーザーが本ファイル + ADR 0001 を確認、Phase 1 着手の許可を出す
2. Phase 1 設計 md `docs/aiseo/phase_1_design.md` を書く
3. CODEX に Phase 1 設計レビューを依頼（codex-review スキル経由）
4. レビュー反映後、Phase 1 実装着手（partial / CSS / robots / sitemap / llms.txt / .nojekyll / CI）

---

## Phase 0 CODEX レビュー結果（2026-05-13）

CODEX の総評：**Phase 0 承認、ただし7点を設計書に反映**。本文に反映済み。下表は対応一覧。

| # | CODEX 指摘 | 反映先 | 状態 |
|---|---|---|---|
| 1 | Person.name の露出範囲を完了条件に明記、Article / LP / SNS / note フッターに出さない | Phase 2 Person JSON-LD 直下「注」／phase_N_design.md テンプレ §6 | 反映済 |
| 2 | jobTitle は「店舗運営マネージャー / 個人開発者」程度、企業文脈を出さない | Phase 2 Person JSON-LD（既定値）／ココナラ表現ルール §3 | 反映済 |
| 3 | ADR `0001-brand-isolation-vs-aiseo-aggregation.md` を Phase 1 で追加 | `decisions/0001-brand-isolation-vs-aiseo-aggregation.md` 作成済（2026-05-13） | 反映済 |
| 4 | `Person.founder` は schema.org 的に不自然、削除 | Phase 2 Person JSON-LD から削除済 | 反映済 |
| 5 | `mainEntityOfPage` を note URL にする方針は良いが、ミラーには `isBasedOn` を併記し、ミラー＝「要約ハブ」と呼び替え | Phase 5 で呼称統一・`isBasedOn` 残し方明記 | 反映済 |
| 6 | `sameAs` は実在 URL のみ、ココナラ `{id}` は確定後に追加 | Phase 2 Person JSON-LD 直下「注」 | 反映済 |
| 7 | logo の実ファイル存在チェックを CI 必須化 | Phase 1 aiseo-check.yml の検査項目に追加（実装は Phase 1 で） | 設計反映済、実装は Phase 1 |
| 8 | RSS fallback を必須化（note-poster 失敗時の同期維持） | Phase 5 運用フローを「二経路、RSS fallback 必須」に修正 | 反映済 |
| 9 | Phase 5 完了条件に「全文転載ゼロ」を追加 | Phase 5 完了条件＋有料記事の固定仕様（タイトル+公開日+1段落要約のみ） | 反映済 |
| 10 | Phase 6 で note フッター存在検査を投稿前必須に | Phase 6 触るファイル `note-poster` SKILL.md / note_poster.py 改修明記 | 反映済 |
| 11 | Phase 7 を 7A（UA 変更）と 7B（bio 手動反映）に分割 | フェーズ一覧と Phase 7 セクションを 7A / 7B に分割 | 反映済 |
| 12 | 全フェーズ完了条件に「CODEX 強い懸念ゼロ or ADR 化」を追加 | フェーズ一覧直下「全フェーズ共通の完了条件」 | 反映済 |
| 13 | phase_N_design.md 固定テンプレを設計書に追加 | フェーズ一覧直下「phase_N_design.md 固定テンプレ」10項目 | 反映済 |
| 14 | Phase 1 に canonical / noindex 方針を明文化、AI クローラ allowlist 最新確認を追加 | Phase 1「追加方針」「CODEX 固有観点」に反映 | 反映済 |
| 15 | Phase 4 に画像最適化チェック（WebP / width-height / lazy / alt / og.png サイズ）を追加 | Phase 4「画像最適化チェック」セクション新設 | 反映済 |
| 16 | Phase 5 要約ハブの canonical 方針（自 URL、`mainEntityOfPage` は note URL、`isBasedOn` は note URL）を明記 | Phase 5「要約ハブ本文方針」に反映 | 反映済 |
| 17 | llms-full.txt は初期不要、llms.txt のみで十分 | Phase 1 CODEX 固有観点に明記 | 反映済 |

未反映・将来検討：
- 画像 sitemap（Phase 4 の LP 画像が増えた後に検討、本設計書では言及のみ）
- hreflang（日本語サイト単独なので将来英語ページ作成時まで保留）

## Phase 0 完了条件達成状況

- [x] `docs/aiseo/00_overall_design.md` が作成済
- [x] `docs/aiseo/decisions/0001-brand-isolation-vs-aiseo-aggregation.md` が作成済
- [x] CODEX レビューの「強い懸念」がゼロ件（17項目すべて反映済 or 将来検討に整理）
- [ ] main にマージ済み（ユーザー承認後に commit / push）
