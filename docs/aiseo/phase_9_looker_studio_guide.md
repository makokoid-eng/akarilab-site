# Phase 9 — Looker Studio 固定ダッシュボード セットアップ手順

## 目的

GA4 の `redirect_click` イベントを **Looker Studio**（旧 Googleデータポータル、無料）で固定ダッシュボード化する。毎回 GA4 探索を作り直す手間を消し、「記事×商品×チャネル」のクリック分布を1画面で常時把握。

設計: `phase_9_redirects_design.md`
承認プラン: `~/.claude/plans/cryptic-sniffing-cerf.md`

## 前提

- GA4 プロパティ `akarilab.org` (G-K6N7W00YYP, Property ID 539463635) 稼働中
- カスタムディメンション 6件登録済（slug / from / from_valid / channel / dest_domain / category）
- ユーザー（makokoid@gmail.com）が GA4 管理者

---

## ① Looker Studio にログイン

https://lookerstudio.google.com/ を開く → makokoid@gmail.com でログイン

## ② 新規レポート作成

- 画面左上「**+ 空のレポート**」をクリック
- データのコネクタを選択：「**Google アナリティクス**」を選ぶ
- アカウント → プロパティ → `akarilab.org` を選択 → 「追加」

## ③ レポート名を変更

画面上部「無題のレポート」をクリック → `Phase 9 redirect-click ダッシュボード` などに改名

---

## 推奨ダッシュボード構成（4セクション）

### セクション 1: KPI スコアカード（横並び 4 枚）

ページ上部に並べる：

| カード | 指標 | 設定 |
|---|---|---|
| 今週の総クリック | イベント数 (event_count) | フィルタ: イベント名 = redirect_click、期間=今週 |
| 今週のユニーククリック | ユーザー数 (totalUsers) | 同上 |
| from_valid 率 | from_valid=true の割合 | カスタム指標：`count(from='unknown') / count(*)` の反転 |
| 異常 slug 数 | クリック0の slug 数 | スカードに condition |

### セクション 2: slug × チャネル マトリクス（テーブル）

- データ範囲: 過去 7 日
- ディメンション（行）: `customEvent:slug`
- ディメンション（列ピボット）: `customEvent:channel`
- 指標: イベント数
- ソート: イベント数 降順

→ 「どの商品が、どのチャネルから、何回クリックされたか」が1表で見える

### セクション 3: 記事ランキング（バーチャート）

- 指標: イベント数（redirect_click）
- ディメンション: `customEvent:from`
- 期間: 過去 7 日 / 過去 30 日 を切替できるコントロールを上に置く
- 並び: 多い順 上位 20

→ 「どの記事がよく送客しているか」が一目で見える

### セクション 4: 日次推移（時系列グラフ）

- 指標: イベント数
- ディメンション: 日付
- ブレイクダウン: `customEvent:slug`（折れ線複数本）
- 期間: 過去 30 日

→ 「いつから飛び始めたか・伸びている slug はどれか」が見える

### セクション 5: 時間帯×曜日 ヒートマップ（配信タイミング最適化用）

- 指標: イベント数（redirect_click）
- ディメンション 1: 時間（hour）
- ディメンション 2: 曜日（day_of_week）
- 表示: ヒートマップ（背景色濃淡）

→ 「何曜日の何時に踏まれやすいか」が見える。note 自動投稿の時刻最適化に直結。

---

## フィルタ設定（全ページ共通）

ページ右クリック → 「ページ プロパティ」→ フィルタ追加：

- フィルタ名: `redirect_click のみ`
- 条件: `event_name` 一致 `redirect_click`

これで全ページが redirect_click データだけになる。

---

## 共有設定

- 右上「**共有**」→ 「設定」→ 「リンクを取得した全員が閲覧可能」を OFF（個人用のため）
- 自分だけのダッシュボードとしてブックマーク

---

## アクセス方法（運用時）

1. https://lookerstudio.google.com/ を開く
2. 自分の作ったレポートを開く
3. 右上の更新ボタンで最新データに反映

→ 通常はGA4のデータが**12〜24時間遅れ**で反映されるので、リアルタイム性は GA4 リアルタイムに譲る。Looker Studio は「日次以上の集計を見るツール」と割り切る。

---

## トラブルシューティング

| 症状 | 対処 |
|---|---|
| カスタムディメンションが選択肢に出ない | データソース編集 → カスタムフィールドで `customEvent:slug` などを手動で追加 |
| データが空 | データ取得まで24時間ラグあり。redirect_click を10回くらい踏んでから24h後に再確認 |
| 時間帯ディメンションが取れない | GA4 拡張計測ON か確認、hour ディメンションは標準で取れる |

---

## 自動化との関係

- Looker Studio = **可視化（人が見る）**
- redirect-metrics workflow = **集計＋異常検知（GitHub Issue で起票）**
- redirect-monitor スキル = **チャットで要約（質問応答）**

役割分担：
- **常時見たい**: Looker Studio
- **月曜の定期報告**: redirect-metrics workflow（Issue）
- **質問応答**: redirect-monitor スキル

---

## 履歴

- 2026-05-29: Phase 9 ダッシュボード設計初版
