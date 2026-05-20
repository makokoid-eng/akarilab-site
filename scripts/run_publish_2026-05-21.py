#!/usr/bin/env python3
"""run_publish_2026-05-21.py

2026-05-21 雑記 10 本を一気に publish_article.py に流し込むラッパー。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DRAFTS = Path("C:/Users/user/akarilab-note/drafts/2026-05-21")
PUBDATE = "2026-05-21"
PUBLISH = REPO_ROOT / "scripts" / "publish_article.py"

ARTICLES = [
    # (md_basename, title, image_basename, note_key, slug_suffix)
    ("01_tencho_meeting.md",
     "手をぶつけても、その手を合わせて前に進みたいと伝えた夜",
     "article_image_2026-05-21_01.png", "nd57b08a4cf48", "-1"),
    ("02_tissue_observation.md",
     "二十人が受け取らなくても、その後ろに六人いるかもしれない",
     "article_image_2026-05-21_02.png", "n14f615f4f837", "-2"),
    ("03_shoudo_kekkai.md",
     "「意志が弱かった」で片付けなかった、決壊の日の記録",
     "article_image_2026-05-21_03.png", "n0d65447708c2", "-3"),
    ("04_naisei_uragotae.md",
     "朝の内省で感情の蓋が開いたまま、現場に出てしまった日",
     "article_image_2026-05-21_04.png", "n9bed25926b5a", "-4"),
    ("05_mac_hanbaagaa.md",
     "マクドナルドで、隣のご婦人にハンバーガー券を渡した日",
     "article_image_2026-05-21_05.png", "n892e2372d2b4", "-5"),
    ("06_iwanu_aiouen.md",
     "「大好き」を言わなかった夜、明日その人の面接試験が来る",
     "article_image_2026-05-21_06.png", "n1bed45675639", "-6"),
    ("07_uranai_mokuteki.md",
     "売れることを目的にせずに、有料の記事を置いた日",
     "article_image_2026-05-21_07.png", "n024da5c7f5ef", "-7"),
    ("08_hashireru_yasume.md",
     "走れる人には休め、歩けない人には歩け、と返した夜",
     "article_image_2026-05-21_08.png", "nba26f2d907ca", "-8"),
    ("09_houkou_tenkan.md",
     "「方向転換」という言葉が、焦りの逃げ場として出てきた昼",
     "article_image_2026-05-21_09.png", "n1f0ca8dd40be", "-9"),
    ("10_omoikomi_zure.md",
     "「野菜食べられない」と書きながら、ほうれん草を2束茹でていた夜",
     "article_image_2026-05-21_10.png", "ne13e91f3e5c5", "-10"),
]


def main() -> int:
    import io
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    failures: list[str] = []
    for md_name, title, img_name, note_key, slug_suffix in ARTICLES:
        md_path = DRAFTS / md_name
        img_path = DRAFTS / img_name
        cmd = [
            sys.executable,
            str(PUBLISH),
            "--markdown", str(md_path),
            "--title", title,
            "--category", "misc",
            "--pubdate", PUBDATE,
            "--cover-image", str(img_path),
            "--note-key", note_key,
            "--slug-suffix", slug_suffix,
        ]
        print(f"\n=== publish: {md_name} ===")
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        if result.returncode != 0:
            failures.append(md_name)

    if failures:
        print(f"\nFAILED: {len(failures)} items: {failures}", file=sys.stderr)
        return 1
    print(f"\nALL OK: {len(ARTICLES)} articles published")
    return 0


if __name__ == "__main__":
    sys.exit(main())
