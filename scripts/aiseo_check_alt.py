#!/usr/bin/env python3
"""aiseo_check_alt.py

画像 alt 属性検査。
- 全 HTML ファイルの <img> を走査
- alt 属性が無い、または空文字（alt=""）なら fail
- decorative image（aria-hidden="true"）は除外

Phase 1: 既存6ページ + Phase 2 以降の新規ページに対して fail で止める検査。
"""
from __future__ import annotations

import sys
from pathlib import Path

from bs4 import BeautifulSoup

REPO_ROOT = Path(__file__).resolve().parent.parent
EXCLUDED_TOP_DIRS = {"assets", "docs", "scripts", ".github", ".git"}


def find_html_targets() -> list[Path]:
    targets: list[Path] = []
    for path in REPO_ROOT.rglob("*.html"):
        rel = path.relative_to(REPO_ROOT)
        if rel.parts[0] in EXCLUDED_TOP_DIRS:
            continue
        targets.append(path)
    return sorted(targets)


def main() -> int:
    failures: list[tuple[Path, str]] = []
    for path in find_html_targets():
        html = path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "html.parser")
        for img in soup.find_all("img"):
            if img.get("aria-hidden") == "true":
                continue
            alt = img.get("alt")
            if alt is None:
                failures.append((path, f"img missing alt: src={img.get('src')}"))
            elif alt.strip() == "":
                failures.append((path, f"img empty alt: src={img.get('src')}"))

    rel = lambda p: p.relative_to(REPO_ROOT)
    if failures:
        print(f"FAIL: {len(failures)} image alt issues")
        for path, msg in failures:
            print(f"  {rel(path)}: {msg}")
        return 1

    print("OK: all <img> elements have non-empty alt (or aria-hidden)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
