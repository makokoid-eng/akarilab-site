# AGENTS.md — akarilab-site

このリポジトリは `akarilab.org` の実体です。GitHub Pages が `main` をそのまま配信します。
**push した瞬間に本番が変わります。** ステージング環境はありません。

作業を始める前に、下の「壊すと外からしか見えない壊れ方をするもの」を必ず読んでください。

---

## 1. 壊すと外からしか見えない壊れ方をするもの

サイト内のリンクチェックでは**絶対に検出できない**依存があります。
外部システムがサイト内のURLを直接指しているためです。

台帳: **`data/external_refs.yml`**
検査: **`scripts/check_external_refs.py`**（CI `aiseo-check` の fail 系で毎回実行）

### 決済後の着地先（最重要）

Stripe の決済リンク6本は、決済完了後にこの2ページへリダイレクトします。

```
makoto/services/grant-portal/thanks/     ← 助成金ポータル 2プラン
makoto/services/attendance-ocr/thanks/   ← 勤怠OCR 4プラン
```

このどちらかを消す・動かす・改名すると、
**サイト内はリンク切れゼロのまま、決済を完了した顧客だけが 404 に落ちます。**
課金は成立しているのに、案内が出ない状態です。

動かすときの順番は必ずこれです。逆にすると、その間に決済した人が着地先を失います。

```
1. Stripe の after_completion.redirect.url を新URLへ変更
2. 新URLが公開されていることを確認
3. そのあとで古いパスを動かす
```

### 決済リンクそのもの

サイトに貼ってある `https://buy.stripe.com/...` を書き換えると、
別プランに課金されるか、決済できなくなります。目視では気づけません。
台帳と実ファイルの一致を CI が検証します。追加・変更したら台帳も更新してください。

---

## 2. 助成金ポータル本番は「非公開」です

```
https://akari-josei-portal.akarilab.chatgpt.site
```

これは ChatGPT Sites の **Private Site** で、全パスがサインイン必須です。
**客向けページから直リンクしてはいけません。** 開いた人はサインイン画面で止まります。

過去にこれで営業導線が死にました。「公開ポータルを見る」というラベルで
非公開URLへリンクしていて、申し込み前の社労士がそこで離脱していました。

例外は `/owner/` だけです（robots.txt で Disallow 済みの運用ページ）。
CI がこの混入を検出します。

代わりに使うのは公開デモです。

```
makoto/services/grant-portal/demo/
makoto/services/attendance-ocr/demo/
```

---

## 3. 公開デモページを触るときの制約

`docs/demo-pages.md` に仕様と設計判断があります。以下は絶対に崩さないでください。

1. **外部通信を入れない** — `fetch` / `XMLHttpRequest` を使わない
2. **本番を参照しない** — D1 / R2 / 本番API を呼ばない
3. **実データを載せない** — 会社名・氏名・書類・打刻はすべて架空
4. **断定しない** — 助成金は受給可否を、OCRは読み取り精度を保証しない

**1〜3が崩れると、これは「営業用デモ」ではなく「認証の抜け穴」になります。**

表示する件数（「5件に要確認」など）は、必ずスクリプト内のデータと突き合わせてください。
本文とデータが食い違ったまま公開された前例があります。

---

## 4. 自動生成されるもの

手で編集しないでください。生成元を直して、生成スクリプトを通します。

| 生成物 | 生成元 | スクリプト |
| --- | --- | --- |
| `r/<slug>/index.html` | `data/redirects.yml` | `scripts/build_redirects.py` |
| partial include を含むページ | `assets/partials/` | `scripts/build_pages.py` |

---

## 5. コミット前に走らせるもの

```bash
python scripts/check_external_refs.py     # 外部参照（決済リンクの着地先）
python scripts/build_pages.py --check     # partial include の整合
```

どちらも CI と同じ検査です。手元で通しておくと、push してから気づく事故が減ります。

---

## 6. 作業まわりの注意

- **`git add .` / `git add -A` を安易に使わないこと。** 作業ツリーに未コミットの変更が
  溜まっていることがあります。変更したファイルを明示的に指定してください。
- Windows 環境では改行コードの warning が出ますが、`core.autocrlf` の正常動作です。
- GitKraken など git クライアントが `.git/index.lock` を残すことがあります。
  「Another git process seems to be running」が出たら、クライアントを終了してから
  ロックファイルを消してください。

---

## 7. 関連ドキュメント

| ファイル | 内容 |
| --- | --- |
| `docs/demo-pages.md` | 公開デモ・サンクスページの仕様と設計判断、Stripe遷移先の変更記録 |
| `data/external_refs.yml` | 外部システムが指しているパスの台帳 |
| `docs/aiseo/` | AISEO の設計と Phase 計画 |
