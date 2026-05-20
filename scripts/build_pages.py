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
# include 形式で書かれた新規ページは Phase 単位で追記する。
TARGETS: list[str] = [
    # Phase 2: AkariLab Organization と /makoto/ プロフィール 5 ページ
    "akarilab/index.html",
    "makoto/index.html",
    "makoto/profile/index.html",
    "makoto/timeline/index.html",
    "makoto/contact/index.html",
    # Phase 2 追補 (2026-05-20): /makoto/services/ 提供サービス集約ハブ
    "makoto/services/index.html",
    # Phase 3: ひだまり LP の /hidamari/ 移設
    "hidamari/index.html",
    # Phase 4: もやログ・りぴメモ本格 LP
    "moyalog/index.html",
    "moyalog/voices/index.html",
    "repimemo/index.html",
    "repimemo/store/index.html",
    "repimemo/voices/index.html",
    # Phase 5: /articles/ 連載ハブ
    "articles/index.html",
    "articles/ai-9months/index.html",
    # Phase 6: note エクスポート一括移行（2026-05-15）
    # 連載 14話（drafts/2026-05-13/dev-log-NN.md 順）
    # 第1話=44歳台風, 第2話=3時11分, ..., 第14話=9ヶ月後の手紙
    "articles/ai-9months/44歳台風のホテルで生成AIという言葉を初めて聞いた夜/index.html",
    "articles/ai-9months/3時11分コードを書く前にやっていたこと/index.html",
    "articles/ai-9months/23時41分AIに内省を手伝ってもらった夜/index.html",
    "articles/ai-9months/10時23分整えログにアプリ進めなきゃが紛れていた春/index.html",
    "articles/ai-9months/転職と開発が同じスレッドで重なっていた夏/index.html",
    "articles/ai-9months/8月26日LINEBotがechoを返した夜/index.html",
    "articles/ai-9months/食改善Botが動いた10月ようやく開発者の道具を揃えた/index.html",
    "articles/ai-9months/17時38分初めてのgitcommitそれから22時間クラウドは動かなかった/index.html",
    "articles/ai-9months/9時9分から22時44分まで20回pushを繰り返した日/index.html",
    "articles/ai-9months/1月26日AIが嘘をつかないようにコードを書いた日/index.html",
    "articles/ai-9months/18時58分21年の現場をコードに翻訳し始めた/index.html",
    "articles/ai-9months/18日間で4つのプロダクトを立ち上げた4月/index.html",
    "articles/ai-9months/17時43分フォームからLINEまで初めて自動で流れた日/index.html",
    "articles/ai-9months/9ヶ月後の自分が台風の夜の自分に書く手紙/index.html",
    # 雑記 48 本（XML 出現順、YYYY/MM/{guid}/index.html）
    "articles/2026/04/1年半前の4行が今夜のスキルになった/index.html",
    "articles/2026/04/2本目はタグを入れるために書いている/index.html",
    "articles/2026/04/AkariLabのこと｜今日とあの日を同じページで編む/index.html",
    "articles/2026/04/2日目で仕組みの面倒に気づいた/index.html",
    "articles/2026/04/騙されたと思ってスキルを6本書いた夜/index.html",
    "articles/2026/04/月1万円のジムに飛び込んだ夜/index.html",
    "articles/2026/04/Codexに叱られる夜40代未経験がLINEBotを作る/index.html",
    "articles/2026/04/もやログが降臨した夜/index.html",
    "articles/2026/04/行きつけのKISSATENで話を聞く側に立てるようになった日/index.html",
    "articles/2026/04/亡き母への手紙/index.html",
    "articles/2026/04/初日記の夜人生を変える宣言を書いた/index.html",
    "articles/2026/04/21時のロフトで歌を歌っていた自分に気づいた夜/index.html",
    "articles/2026/04/月1万円のジムに飛び込んだ日不安を書き残していた（続編）/index.html",
    "articles/2026/04/夜風の橋の上で別れを手放した/index.html",
    "articles/2026/04/バリューランタンを描いた夜中心に子どもがいた/index.html",
    "articles/2026/04/元カノと最後にご飯を食べた日達成と別れが同居していた/index.html",
    "articles/2026/04/初マラソンを完走した日心拍に余裕があった/index.html",
    "articles/2026/04/復縁したい気持ちをその時じゃないと書いた3月の夜/index.html",
    "articles/2026/04/他の親が書いてくれた声を最初の画面に置いた日/index.html",
    "articles/2026/04/AIと数時間話せるんだからもっと踏ん張れと書いた夜/index.html",
    "articles/2026/04/嫌いだったSNSを自動化で消した夜/index.html",
    "articles/2026/04/動画投稿がうまくできなかったなーと書いた深夜/index.html",
    "articles/2026/04/ふらっと柳川へ行って温泉に2回入った夜/index.html",
    "articles/2026/04/ジムで限界まで追い込んで家の鍵をなくして詰んだ夜/index.html",
    "articles/2026/04/一年半の関係を執着で潰した話半年後に気づいていまやっと書ける/index.html",
    "articles/2026/04/あれ早く終わってると書いた瞑想2日目の夜/index.html",
    "articles/2026/04/習字のマインドフルネスとある店長にWDEPを渡した日/index.html",
    "articles/2026/05/感情フォーカスセラピーって知ってるかと自分に書いた日/index.html",
    "articles/2026/05/5ヶ月前の自分がGPTに一行だけ送っていた/index.html",
    "articles/2026/05/海で20分書いた日駐車位置を間違えた/index.html",
    "articles/2026/05/息子の手を握って自分の心を守ってくれと願った夜/index.html",
    "articles/2026/05/書くことが続かない店長に行動日記から渡した/index.html",
    "articles/2026/05/PCを開かなかった土曜の夜/index.html",
    "articles/2026/05/自分を整え周りも整えると書けた4月の最終日/index.html",
    "articles/2026/05/未完成のまま渡した3日後にひだまりのなぜが出た/index.html",
    "articles/2026/05/40日ぶりに走った日/index.html",
    "articles/2026/05/未完成のひだまりを誰かの家庭に渡したい/index.html",
    "articles/2026/05/騙されたと思って継続と書いた夜から評価しないAIを設計するまで/index.html",
    "articles/2026/05/70万超えた福岡店の夜から面接で余白がないと歪むと言うまで/index.html",
    "articles/2026/05/自転車15キロをAIに任せた深夜から誕生日に自分で筋トレ回数を増やすまで/index.html",
    "articles/2026/05/一緒にいて心地よいと書いた1月の夜から焦りがない安心に至る1年/index.html",
    "articles/2026/05/2時間で2店舗のシフトが終わった夜から整える日に切り替えるまで/index.html",
    "articles/2026/05/AIに金銭不安をほどいてもらった夜から自分の価値観でアプリを退会するまで/index.html",
    "articles/2026/05/神戸を抜いたと書いた夜から会社が事故りにくくなると書く今へ/index.html",
    "articles/2026/05/職場でサンタクロースになった夜から行きつけのカフェで涙が溢れた日まで/index.html",
    "articles/2026/05/5時半の始発と誕生日の朝の解釈/index.html",
    "articles/2026/05/23時52分元カノを大切な存在と書いた夜/index.html",
]

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


# include / include-end の片割れ残存検出用（CODEX コードレビュー指摘 4 反映）。
# 冪等性のため include / include-end マーカー自体は render 後も残る仕様なので、
# 「マーカーが残っているか」ではなく「ペアが揃っているか（数と名前の一致）」で判定する。
INCLUDE_START_PATTERN = re.compile(r"<!--\s*include:\s*([^\s]+)\s*-->")
INCLUDE_END_PATTERN = re.compile(r"<!--\s*include-end:\s*([^\s]+)\s*-->")


def assert_no_unprocessed_marker(rendered: str, source_path: Path) -> None:
    """include / include-end のペアが揃っているか確認。

    片割れだけの marker（include だけで include-end が無い等）や、
    両方あるが partial 名が一致しないケースを fail とする。
    冪等性のため両者ペアで残っているのは正常。
    """
    starts = sorted(INCLUDE_START_PATTERN.findall(rendered))
    ends = sorted(INCLUDE_END_PATTERN.findall(rendered))
    if starts != ends:
        raise RuntimeError(
            f"include / include-end mismatch in {source_path}: "
            f"include={starts}, include-end={ends}"
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
