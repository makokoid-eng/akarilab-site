# implementation-notes（仕様外の判断・変更の記録）

2026-07-07 00:10 Stripe直接決済（page_stripe_payment_design.md）実装中の仕様外判断2件：
1. scripts/build_redirects.py の ALLOWED_CATEGORIES に "stripe" を追加。設計mdは /r/stripe-consult/ 新設のみ想定していたが、カテゴリのバリデーションで弾かれたため。redirect-monitor 側は category を集計軸にしているだけなので影響なしと判断（推測。次回の週次レポートで stripe カテゴリが出力されるか要確認）。
2. tokushoho.html への追記は、設計mdの「決済手段の一文追記」ではなく「相談・受託サービスに関する表記」の独立節＋導入文への案内文を追加。既存ページの冒頭が「ひだまり」専用の表記と宣言しており、一文追記だと適用範囲が矛盾するため。

2026-07-10 10:45 redirect-metrics.yml に TLS証明書期限チェックを追加（ユーザー依頼。demo.akarilab.org 証明書発行停止事故の再発検知が目的）。仕様外判断3件：
1. 実装場所は collect_redirect_metrics.py 内ではなく workflow の独立ステップ（bash+openssl）にした。GA4集計と関心が別で、Python側の失敗と分離できるため。
2. 警告閾値は残り14日未満。GitHub Pages / Let's Encrypt は通常30日前に自動更新するので、14日を切っていれば「自動更新が壊れている」と判断できる（推測含む。実際の更新タイミングは今後の週次レポートで観察）。
3. 対象ドメインは akarilab.org / demo.akarilab.org の2つ。他ブランド（hidamari等）はパス運用でドメインを持たないため対象外。新ドメイン追加時は workflow の for ループに足す。

2026-07-10 現在時刻不明（検証修正エージェント） makoto/services/index.html カード7（Brain AI実用例20選）の価格矛盾を解決。検証指摘が2件で相互矛盾（指摘1「仕様上980円が正、可視テキスト4,980円を直せ」vs 指摘2「JSON-LD の "980" は "4980" からの桁落ち誤編集、戻せ」）。リポジトリ内の証拠（data/sales_products.yml standard_price:4980、index.html:749、makoto/profile/index.html 2箇所、docs/aiseo/page_services_design.md:147 すべて4,980円）から、指摘2の桁落ち診断が正しいと判断し、JSON-LD offers.price を "4980" に復元、可視テキスト「4,980円（買い切り）」は維持した。タスク仕様文中の「7 Brain 980円」も同じ桁落ちの伝播と解釈（推測）。実売価格が本当に980円へ変更されていた場合は逆修正が必要。
