# note-draft.py 設計メモ

## 目的
akarilab.org に新記事を出した後、note.com に同じ記事を「下書き」として自動アップロードする。

## なぜ Playwright か
note には公式 API がない。Cookie 認証で REST を叩く案もあるが、エンドポイントは未公開で仕様変更リスクが高い。Playwright のブラウザ自動化が一番安定。

## セキュリティ
- 認証情報は環境変数のみ（NOTE_EMAIL / NOTE_PASSWORD）
- cookie は `~/.note-session.json` にローカル保存。リポにコミットしない（.gitignore に追加要）
- スクショや HTML ダンプにパスワードが入らないよう注意

## 失敗時のフォールバック
- スクリーンショット保存
- Markdown を stdout に吐いて人間が手動コピー可能に
- 1日1記事までの自主規制

## 利用規約リスク
- note 利用規約での「自動化」の扱いはグレー
- アカウント停止リスクは小さい（中速・低頻度なら）
- 警告メールが来たら即停止

## 次のステップ（実装計画）
1. ローカルで `pip install playwright && playwright install chromium`
2. note 編集画面の DOM 構造を手動調査（selector を決める）
3. 雛形の TODO を埋めて1記事で smoke test
4. cron 化（毎日 01:00 JST、akarilab.org 最新記事を pull して投入）
