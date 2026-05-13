#!/usr/bin/env python3
"""build_pages.py

partial 置換のみのワンファイル静的ビルド。
HTML ファイル内の以下パターンを物理 include する：

    <!-- include: assets/partials/head-common.html -->
    ...（生成された内容）...
    <!-- include-end: assets/partials/head-common.html -->

include パスは repo root 配下のみ許可。`..`、絶対パス、外部 URL は禁止
（path traversal 防止）。冪等：連続2回実行で diff ゼロ。

処理対象は本ファイル内の TARGETS リストで管理する。
Phase 1 時点では空リスト（既存6ページは include 形式に変換しないため空走行で OK）。
新規ページを include 形式で書く場合は TARGETS にリポ root からの相対パスで追記する。

Usage:
    python scripts/build_pages.py              # 通常モード（partial を物理 include して上書き保存）
    python scripts/build_pages.py --dry-run    # 何が変わるかだけ stdout に出力、ファイルは触らない
    python scripts/build_pages.py --check      # CI 用、現状ファイルが build 結果と一致するか検証

設計：Phase 1（C:/Users/user/akarilab-site/docs/aiseo/phase_1_design.md）
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# リポ root（CNAME と同じディレクトリ）。スクリプトファイルの親ディレクトリの親。
REPO_ROOT = Path(__file__).resolve().parent.parent

# include のネスト深度上限（partial 内 include の暴走防止）
MAX_INCLUDE_DEPTH = 5

# 処理対象 HTML（リポ root からの相対パス）。
# Phase 1 時点では空。include 形式で書かれた新規ページは Phase 2 以降で追記する。
TARGETS: list[str] = []

# <!-- include: foo/bar.html --> ... <!-- include-end: foo/bar.html -->
PARTIAL_PATTERN = re.compile(
    r"(<!--\s*include:\s*([^\s\-][^\s]*)\s*-->)"
    r"(.*?)"
    r"(<!--\s*include-end:\s*\2\s*-->)",
    re.DOTALL,
)


def is_safe_partial_path(rel_path: str) -> bool:
    """`..`、絶対パス、外部 URL を禁止。repo root 配下のみ許可。

    POSIX 形式の先頭スラッシュ（`/foo`）と外部 URL は startswith で拒否。
    Windows 形式の絶対パス（`C:/foo` や `C:\\foo`）は Path.is_absolute() で拒否。
    """
    if rel_path.startswith(("/", "http://", "https://", "//")):
        return False
    if Path(rel_path).is_absolute():
        return False
    if ".." in Path(rel_path).parts:
        return False
    try:
        resolved = (REPO_ROOT / rel_path).resolve()
        resolved.relative_to(REPO_ROOT)
    except ValueError:
        return False
    return True


# 未処理 include マーカー残存検出用（CODEX コードレビュー指摘 4 反映）
UNPROCESSED_MARKER_PATTERN = re.compile(r"<!--\s*include(-end)?:")


def assert_no_unprocessed_marker(rendered: str, source_path: Path) -> None:
    """render 後の出力に処理されなかった include マーカーが残っていれば fail。

    片割れだけの marker（include だけで include-end が無い等）を見逃すのを防ぐ。
    """
    if UNPROCESSED_MARKER_PATTERN.search(rendered):
        raise RuntimeError(
            f"unprocessed include marker remains in {source_path}: "
            f"片方の include / include-end のみが残っているか、partial 名が一致していません"
        )


def load_partial(rel_path: str) -> str:
    if not is_safe_partial_path(rel_path):
        raise RuntimeError(f"unsafe include path: {rel_path}")
    target = REPO_ROOT / rel_path
    if not target.is_file():
        raise RuntimeError(f"partial not found: {rel_path}")
    return target.read_text(encoding="utf-8")


def render(html: str, depth: int = 0) -> str:
    if depth > MAX_INCLUDE_DEPTH:
        raise RuntimeError(f"include depth limit exceeded (>{MAX_INCLUDE_DEPTH})")

    def replace(match: re.Match) -> str:
        marker_start = match.group(1)
        partial_path = match.group(2)
        marker_end = match.group(4)
        partial_content = load_partial(partial_path)
        # ネスト解決
        rendered_partial = render(partial_content, depth + 1)
        return f"{marker_start}\n{rendered_partial}\n{marker_end}"

    return PARTIAL_PATTERN.sub(replace, html)


def resolve_targets() -> list[Path]:
    """TARGETS の相対パスを絶対パスへ解決。安全性チェック付き。"""
    resolved: list[Path] = []
    for rel in TARGETS:
        if not is_safe_partial_path(rel):
            raise RuntimeError(f"unsafe target path: {rel}")
        target = REPO_ROOT / rel
        if not target.is_file():
            raise RuntimeError(f"target not found: {rel}")
        resolved.append(target)
    return resolved


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="何が変わるかを stdout に出力、ファイルは触らない",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="CI 用：現状ファイルが build 結果と一致するか検証（不一致なら non-zero exit）",
    )
    args = parser.parse_args(argv)

    try:
        targets = resolve_targets()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    changed: list[Path] = []
    errors: list[tuple[Path, str]] = []

    for path in targets:
        try:
            original = path.read_text(encoding="utf-8")
            rendered = render(original)
            assert_no_unprocessed_marker(rendered, path)
        except Exception as exc:
            errors.append((path, str(exc)))
            continue
        if original != rendered:
            changed.append(path)
            if not args.dry_run and not args.check:
                path.write_text(rendered, encoding="utf-8")

    def rel(p: Path) -> Path:
        return p.relative_to(REPO_ROOT)

    for path, msg in errors:
        print(f"ERROR {rel(path)}: {msg}", file=sys.stderr)

    if errors:
        return 2

    if args.check:
        if changed:
            print(f"check FAILED: {len(changed)} files would change")
            for path in changed:
                print(f"  {rel(path)}")
            return 1
        print(f"check OK: scanned {len(targets)} files, no changes needed")
        return 0

    if args.dry_run:
        print(f"dry-run: {len(changed)} of {len(targets)} files would change")
        for path in changed:
            print(f"  {rel(path)}")
        return 0

    print(f"build: {len(changed)} of {len(targets)} files updated")
    for path in changed:
        print(f"  {rel(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
