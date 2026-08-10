#!/usr/bin/env python3
"""外部システムが直接指しているURLが壊れていないかを検証する。

PURPOSE
-------
目的:
    Stripe の決済リンクなど、サイトの外から直接URLで参照されているページが
    消えたり動いたりしていないかを CI で止める。

背景:
    2026-08-10、Stripe の決済リンク6本が、決済完了後に非公開サイトへ
    リダイレクトしていた。支払い直後の顧客がサインイン画面で止まっていた。
    遷移先を akarilab.org のサンクスページへ変更して解消したが、
    今度は「そのサンクスページを消したら決済直後の顧客が404に落ちる」
    という逆の依存が生まれた。

    この依存は内部リンクチェックでは検出できない。
    サイト内のどこからもリンクされていなくても、外部からは参照されているため。
    ドキュメントの注意書きは読まれないことがある。だからCIで落とす。

使い方:
    python scripts/check_external_refs.py            # 検証（CI用）
    python scripts/check_external_refs.py --list     # 台帳の内容を表示するだけ

    台帳: data/external_refs.yml

終了コード:
    0 = 問題なし
    1 = 台帳と実ファイルが食い違っている（CIを止める）
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = REPO_ROOT / "data" / "external_refs.yml"


def load_registry() -> dict:
    """台帳を読み込む。

    引数: なし
    出力: dict。locked_paths / stripe_links / forbidden_in_public_pages を含む。
    """
    if not REGISTRY.exists():
        print(f"ERROR: 台帳が見つかりません: {REGISTRY}", file=sys.stderr)
        sys.exit(1)
    with REGISTRY.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def check_locked_paths(registry: dict) -> list[str]:
    """台帳に載っているパスが実在するかを確認する。

    引数: registry - load_registry() の戻り値
    出力: エラーメッセージのリスト（空なら合格）
    """
    errors: list[str] = []
    for entry in registry.get("locked_paths") or []:
        path = entry.get("path", "")
        target = REPO_ROOT / path
        if target.exists():
            continue

        refs = entry.get("refs") or []
        ref_lines = "".join(
            f"\n        - {r.get('id')}  {r.get('note', '')}" for r in refs
        )
        errors.append(
            f"消えている、または移動した: {path}\n"
            f"    URL   : {entry.get('url')}\n"
            f"    参照元: {entry.get('used_by')}"
            + (f"{ref_lines}" if ref_lines else "")
            + f"\n    影響  : {entry.get('breaks_if_removed')}"
            f"\n    先にやること: {str(entry.get('before_changing', '')).strip()}"
        )
    return errors


def check_stripe_links(registry: dict) -> list[str]:
    """サイトに貼ってある決済リンクが台帳どおりかを確認する。

    2方向を見る。
      1. 台帳のURLが、載っているはずのページに実際に存在するか
      2. ページ内の buy.stripe.com のURLが、すべて台帳に載っているか
         （台帳にないURLは、書き換えか新規追加。どちらも人の確認が要る）

    引数: registry - load_registry() の戻り値
    出力: エラーメッセージのリスト（空なら合格）
    """
    errors: list[str] = []
    known: set[str] = set()
    expected: dict[str, list[str]] = {}

    for entry in registry.get("stripe_links") or []:
        url = entry.get("url", "")
        known.add(url)
        for page in entry.get("site_links") or []:
            expected.setdefault(page, []).append(url)

    # 1. 台帳が「あるはず」と言っているURLが、そのページに載っているか
    for page, urls in expected.items():
        target = REPO_ROOT / page
        if not target.exists():
            errors.append(f"決済リンクを載せるページが見つかりません: {page}")
            continue
        text = target.read_text(encoding="utf-8", errors="replace")
        for url in urls:
            if url not in text:
                plan = next(
                    (e.get("plan") for e in registry["stripe_links"] if e.get("url") == url),
                    "",
                )
                errors.append(
                    f"決済リンクが消えています: {page}\n"
                    f"    URL : {url}\n"
                    f"    プラン: {plan}"
                )

    # 2. ページに載っている buy.stripe.com が、すべて台帳にあるか
    pattern = re.compile(r"https://buy\.stripe\.com/[A-Za-z0-9]+")
    for html_path in sorted(REPO_ROOT.rglob("*.html")):
        if ".git" in html_path.parts:
            continue
        text = html_path.read_text(encoding="utf-8", errors="replace")
        for found in set(pattern.findall(text)):
            if found not in known:
                rel = html_path.relative_to(REPO_ROOT).as_posix()
                errors.append(
                    f"台帳にない決済リンクが使われています: {rel}\n"
                    f"    URL : {found}\n"
                    f"    対応: 正しいURLか確認し、正しければ data/external_refs.yml に追記する"
                )
    return errors


def check_forbidden(registry: dict) -> list[str]:
    """客向けページに、載せてはいけない文字列が混ざっていないかを確認する。

    引数: registry - load_registry() の戻り値
    出力: エラーメッセージのリスト（空なら合格）
    """
    errors: list[str] = []
    for rule in registry.get("forbidden_in_public_pages") or []:
        pattern = rule.get("pattern", "")
        allowed = set(rule.get("allowed_in") or [])
        for html_path in sorted(REPO_ROOT.rglob("*.html")):
            if ".git" in html_path.parts:
                continue
            rel = html_path.relative_to(REPO_ROOT).as_posix()
            if rel in allowed:
                continue
            text = html_path.read_text(encoding="utf-8", errors="replace")
            if pattern in text:
                errors.append(
                    f"客向けページに非公開URLが混ざっています: {rel}\n"
                    f"    文字列: {pattern}\n"
                    f"    理由  : {rule.get('reason')}"
                )
    return errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--list", action="store_true", help="台帳の内容を表示して終了")
    args = parser.parse_args(argv)

    registry = load_registry()

    if args.list:
        for entry in registry.get("locked_paths") or []:
            print(f"[locked] {entry.get('path')}")
            print(f"         {entry.get('used_by')}")
        for entry in registry.get("stripe_links") or []:
            print(f"[stripe] {entry.get('plan')}  {entry.get('url')}")
        return 0

    errors = (
        check_locked_paths(registry)
        + check_stripe_links(registry)
        + check_forbidden(registry)
    )

    if errors:
        print("=" * 68)
        print(" 外部参照チェックに失敗しました")
        print("=" * 68)
        for err in errors:
            print(f"\n  x {err}")
        print(
            "\n" + "-" * 68 + "\n"
            "  ここで止めているのは、サイト内のリンク切れではありません。\n"
            "  外部（Stripeの決済リンクなど）から直接来る人だけが壊れる種類の問題です。\n"
            "  内部リンクチェックでは検出できないため、台帳で管理しています。\n"
            "  台帳: data/external_refs.yml\n"
        )
        return 1

    n_locked = len(registry.get("locked_paths") or [])
    n_stripe = len(registry.get("stripe_links") or [])
    print(f"OK: 保護パス {n_locked}件、決済リンク {n_stripe}件、すべて健在です。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
