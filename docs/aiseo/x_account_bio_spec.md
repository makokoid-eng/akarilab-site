# X / Instagram bio 仕様書（AISEO Phase 7B）

本書は AkariLab が運用する 4 つの X アカウントと AkariLab ブランド Instagram アカウントの bio・固定ツイート・キャプション末尾の仕様を定義する。設計の正本は `docs/aiseo/00_overall_design.md` の「### Phase 7B」。

## 適用日

- moyalog / repimemo / @waveblasttaiyo の bio：2026-05-13 以降、即時適用可能（対応 LP・トップが既に稼働）
- @makochinta1 の bio：2026-05-13 以降、即時適用可能
- @makochinta1 の固定ツイート（連載インデックス案内）：2026-05-17 以降、連載第1話公開を待って適用
- Instagram キャプション固定シグネチャ：次回投稿から有効

bio・固定ツイートの反映は X / Instagram の管理画面から手動で実施する。本書はその指示書。

---

## 4 X アカウントの bio 仕様

### @waveblasttaiyo（AkariLab メイン）

- **役割**：AkariLab ブランドのトップ誘導。3 プロダクト（ひだまり / もやログ / りぴメモ）と運営者ハブをまとめる入口。
- **bio 末尾に含める URL**：`akarilab.org/`
- **固定ツイート**：akarilab.org トップへのリンク。AkariLab とは何か（個人開発の3プロダクトを束ねるブランド）を1ツイートで説明し、akarilab.org/ を貼る。
- **bio 本文の禁則**：
  - 個人名「まこと」を出さない
  - 個人名露出を避けるため、運営者ハブへの誘導は akarilab.org トップ経由に限定（bio に /makoto/ を直接書かない）
- **その他のリンク**：3 プロダクトの個別 URL は bio に並べない。akarilab.org/ をハブ起点とする。

### @makochinta1（AkariLab note 拡散）

- **役割**：AkariLab の note 記事の告知拡散。連載「触り始めて9ヶ月の記録」のインデックス誘導。
- **bio 本文に明記**：「AkariLab の note 記事の告知」
- **bio 末尾に含める URL**：`akarilab.org/articles/`
- **固定ツイート**：連載「触り始めて9ヶ月の記録」インデックス（akarilab.org/articles/ai-9months/）。連載第1話公開（2026-05-17）以降に切り替える。それ以前はトップ akarilab.org/articles/ を案内する暫定ピン留めで運用。
- **bio 本文の禁則**：
  - 個人名「まこと」を出さない
  - 「個人開発者」「44歳」など個人特定につながる属性を bio に書かない（連載本文・/makoto/ ハブで開示する）

### @moyalog

- **役割**：もやログ単独の世界観で発信する LINE Bot プロダクトアカウント。
- **bio 末尾に含める URL**：`lin.ee/q1k7v8F | akarilab.org/moyalog/`
- **固定ツイート**：もやログ単独の世界観で構成。プロダクト紹介またはユーザー文脈の代表ツイート。
- **bio 本文の禁則**（feedback_brand_isolation_moyalog_repimemo 厳守）：
  - 個人名を出さない
  - 他ブランド名（ひだまり / りぴメモ / AkariLab）を出さない
  - 「3 プロダクトのひとつ」「個人開発」など同一運営者の存在を示唆する文言を出さない
- **URL に akarilab.org サブパスを含める根拠**：ADR 0001 を参照。同一ドメイン配置は AI クローラ向けの「同一運営」シグナルだが、人間 UI 上での主露出は lin.ee URL とプロダクト名「もやログ」であり、bio 本文での相互言及禁止というブランド分離の趣旨は守られる。

### @repimemo

- **役割**：りぴメモ単独の世界観で発信。個人ツール訴求モード（individual）と店舗ハブ伏線モード（industry）の二面プロダクト構造に対応。
- **bio 末尾に含める URL**：`lin.ee/HbV7Ehv | akarilab.org/repimemo/`
- **伏線期間中（2026-05-16〜2026-07-10）の扱い**：
  - bio の URL は同じ（lin.ee と akarilab.org/repimemo/ を残す）
  - ただし伏線投稿の本文に LP リンク（lin.ee / akarilab.org/repimemo/）を貼らない。X→LP の誘導は伏線期間中は外す。
  - bio リンク経由の能動的アクセスは許容（bio から LP へ辿る人は意図して辿っている）
- **固定ツイート**：伏線期間中はプロダクト訴求を含まない、業界課題提起の代表ツイートを置く。期間明け（2026-07-11 以降）に店舗ハブ訴求の固定ツイートに切り替える。
- **bio 本文の禁則**（feedback_brand_isolation_moyalog_repimemo 厳守）：
  - 個人名を出さない
  - 他ブランド名（ひだまり / もやログ / AkariLab）を出さない
  - 伏線期間中は bio 本文でも店舗ハブ機能の具体仕様を書かない（投稿側で伏線を張る役割を奪わない）

---

## Instagram キャプション（@akarilab_jp）

すべての投稿キャプション末尾に固定シグネチャを入れる。

```
---
AkariLab
https://akarilab.org/
```

**本文の禁則**：
- 個人名は出さない
- キャプション本文では各プロダクトの世界観を保つ（AkariLab 署名は末尾シグネチャに集約）

---

## 適用手順

### X 4 アカウント（手動適用）

1. 各 X アカウントにログイン
2. プロフィール編集画面を開く
3. 本書の該当アカウント節に従って bio 本文・末尾 URL を更新
4. プロフィールを保存
5. 固定ツイートが必要なアカウント（@waveblasttaiyo / @makochinta1 / @moyalog / @repimemo）は、該当ツイートを作成または既存ツイートからピン留め
6. @makochinta1 の連載インデックス固定ツイートは 2026-05-17（連載第1話公開日）以降に切り替え

### Instagram @akarilab_jp（次回投稿から）

1. AkariLab IG 投稿パイプライン（generate_slides.py / generate_reel.py 系）でキャプション末尾に固定シグネチャを含めるよう運用ルールを揃える
2. 既存投稿の遡及適用は不要（次回投稿以降から）

---

## 検証

### 適用直後の手動チェック

1. 各 X アカウントの bio をスクショ撮影し、本書の仕様と突合
2. 固定ツイートに含めた URL を curl 等で叩き、HTTP 200 が返ることを確認
   - `akarilab.org/`
   - `akarilab.org/articles/`
   - `akarilab.org/articles/ai-9months/`（2026-05-17 以降）
   - `akarilab.org/moyalog/`
   - `akarilab.org/repimemo/`
   - `lin.ee/q1k7v8F`（もやログ LINE）
   - `lin.ee/HbV7Ehv`（りぴメモ LINE）
3. Instagram の次回投稿後、キャプション末尾に固定シグネチャが含まれていることを目視確認

### 月次の自動観測

- Phase 8 で拡張する `akarilab-note/scripts/check_llm_citations.py` の月初 cron が「AkariLab」「AkariLab 運営者」クエリを叩いた際、結果に X bio リンク（akarilab.org / akarilab.org/articles/ / akarilab.org/moyalog/ / akarilab.org/repimemo/）が含まれるか観察
- 期待ドメインヒット率は累積効果待ち（3〜6 ヶ月で改善）

---

## ADR 0001 整合性チェック

ブランド分離ルール（feedback_brand_isolation_moyalog_repimemo）と本仕様の両立は ADR 0001（`decisions/0001-brand-isolation-vs-aiseo-aggregation.md`）の「可視 UI では分離、構造化データでは統合」の枠組みで成立する。

- **bio 本文での相互言及禁止は維持**：@moyalog / @repimemo の bio 本文に他ブランド名・個人名を一切書かない
- **同一ドメインサブパス配置は許容**：bio 末尾 URL に `akarilab.org/moyalog/` `akarilab.org/repimemo/` を含めることは、AI クローラに対する「同一運営」シグナルとして機能するが、人間 UI 上の主露出は lin.ee URL とプロダクト名であり、世界観混線を起こさない
- **AkariLab 名の主露出は @waveblasttaiyo / @makochinta1 に限定**：個人ハブ・AkariLab ブランド名の露出経路は AkariLab 系 2 アカウントが担い、@moyalog / @repimemo は世界観独立を保つ
- **個人名「まこと」は 4 X アカウント・IG キャプションすべてで出さない**：個人名の主露出は akarilab.org/makoto/ ハブと連載「触り始めて9ヶ月の記録」本文に限定

---

## 将来課題

- **もやログ／りぴメモ専用 IG アカウントの整備**：現状、両プロダクトの IG アカウントの開設状況は未確認。開設済みまたは将来開設する場合、本書に各アカウントの専用シグネチャ仕様を追記する。シグネチャは AkariLab 名を含めず、それぞれのプロダクト名と LP URL（lin.ee / akarilab.org/{brand}/）のみで構成する設計を想定。
- **固定ツイートの定期更新ルール**：固定ツイートの内容は月次〜四半期で見直す運用を想定。明示的な更新サイクルは未定義のため、Phase 8 引用モニタの観測結果を見ながら更新タイミングを決める。
- **X → IG の相互誘導**：現状の bio には他媒体（IG / note）への直接リンクは含めていない。AI クローラ向け sameAs は JSON-LD で接続済み（akarilab.org トップ）のため、bio 物理量を増やす必要は低いが、人間 UI 観点で必要になれば再検討。
- **連載第1話公開後の @makochinta1 固定ツイート切替の自動リマインド**：2026-05-17 を過ぎた時点で固定ツイート切替を行ったか確認するチェック手順は未整備。手動失念リスクあり。
