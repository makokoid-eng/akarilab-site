"""2026-05-21 記事01の重複slug (-1, -1-2) を削除し、-1-3 のみ残す。"""
import re
from pathlib import Path

ROOT = Path("C:/Users/user/akarilab-site")
PATTERNS = [
    "進みたいと伝えた夜-1/",
    "進みたいと伝えた夜-1-2/",
]
FILES = [
    "articles/index.html",
    "llms.txt",
    "scripts/build_pages.py",
]

for rel in FILES:
    p = ROOT / rel
    text = p.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    kept = []
    removed = 0
    for line in lines:
        if any(pat in line for pat in PATTERNS):
            removed += 1
            continue
        kept.append(line)
    p.write_text("".join(kept), encoding="utf-8")
    print(f"{rel}: removed {removed} lines")
