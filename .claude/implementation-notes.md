# implementation-notes（仕様外の判断・変更の記録）

2026-07-07 00:10 Stripe直接決済（page_stripe_payment_design.md）実装中の仕様外判断2件：
1. scripts/build_redirects.py の ALLOWED_CATEGORIES に "stripe" を追加。設計mdは /r/stripe-consult/ 新設のみ想定していたが、カテゴリのバリデーションで弾かれたため。redirect-monitor 側は category を集計軸にしているだけなので影響なしと判断（推測。次回の週次レポートで stripe カテゴリが出力されるか要確認）。
2. tokushoho.html への追記は、設計mdの「決済手段の一文追記」ではなく「相談・受託サービスに関する表記」の独立節＋導入文への案内文を追加。既存ページの冒頭が「ひだまり」専用の表記と宣言しており、一文追記だと適用範囲が矛盾するため。
