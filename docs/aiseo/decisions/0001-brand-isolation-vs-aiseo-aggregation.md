# ADR 0001: ブランド分離ルールと AISEO 接続の両立

- 日付: 2026-05-13
- ステータス: Accepted
- 関連: 00_overall_design.md（Phase 4）、feedback_brand_isolation_moyalog_repimemo

## Context

ひだまり／もやログ／りぴメモは独立した世界観で運営される（feedback_brand_isolation_moyalog_repimemo）。一方で、AI 検索エンジン（ChatGPT/Perplexity/Gemini/Claude）に「同一運営者の連携した活動」として認識されないと、AkariLab ブランドの引用基盤が成立しない。両者が表面上は矛盾する。

## Decision

「可視 UI では分離、構造化データでは統合」のレイヤー分離で両立する。具体的に：

1. **LP 本文（H1〜CTA）には AkariLab／個人名／他プロダクト名を一切書かない**。各プロダクト LP は単独の世界観で完結させる。
2. **LP footer は「© 2026 AkariLab」のみ**置く。akarilab.org トップへの可視リンクは置かない（人間 UI では世界観混線を起こさない）。
3. **JSON-LD で `SoftwareApplication.producer = {@id: "https://akarilab.org/#org"}` で接続**する。人間 UI には出ず、AI クローラだけが拾う。
4. **同一ドメイン（akarilab.org サブパス配置）であることは AI クローラに「同一運営」を強く示唆する**。これは ブランド分離ルールの趣旨（人間読者の世界観保護）を破らない。
5. **もやログ LP からりぴメモ LP への可視リンクは置かない**。その逆も置かない。

## Rationale

- ブランド分離ルールの趣旨は「人間読者が各プロダクトの世界観で受け取れること」であり、「同一運営者の存在の不可視化」ではない。
- AI クローラは構造化データを優先的に読むため、JSON-LD レベルの接続は人間 UI に影響しない。
- footer の「© 2026 AkariLab」は法的な著作表記であり、ブランディング上の言及ではない。読者がそれを起点に他ブランドへ移動する導線にはならない。
- akarilab.org サブパス配置は AI が「同一運営」を判定する強いシグナルだが、人間 UI 上で各 LP が独立して見える限り、ブランド分離の趣旨は守られる。

## Consequences

- AI 回答エンジンは「AkariLab → 3 プロダクト」として引用できる。
- 人間読者にとって、もやログ LP・りぴメモ LP は AkariLab を意識しない世界観で見える。
- 将来「LP に開発者プロフィールを出したい」と判断したら、本 ADR を更新する。
- もやログ／りぴメモ独自ドメインを取得する場合、本 ADR の前提（同一ドメイン配置）が変わるため再検討必要。

## Enforcement

- CODEX レビュー各フェーズで以下を必ず確認：
  - LP 本文に AkariLab／個人名／他ブランド名・他プロダクト名が露出していないか
  - JSON-LD `SoftwareApplication.producer` が `https://akarilab.org/#org` を参照しているか
  - footer のテキストが「© 2026 AkariLab」のみであり、可視リンクが追加されていないか
- CI（aiseo-check.yml）の HTML パースで上記をスクリプト検査できる範囲を機械検査化（Phase 1 で実装）。
