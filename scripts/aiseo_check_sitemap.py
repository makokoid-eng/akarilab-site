#!/usr/bin/env python3
"""aiseo_check_sitemap.py

sitemap.xml の URL と実ファイルパスの整合を検査。
- sitemap.xml に列挙された URL が実ファイル（または index.html を持つディレクトリ）として存在するか
- 逆に、実ファイル（HTML）で sitemap に載っていないものを warning として表示（fail はしない）

Phase 1: 既存6ページのみ列挙、Phase 2 以降は各フェーズで追記。
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
SITEMAP = REPO_ROOT / "sitemap.xml"
EXCLUDED_TOP_DIRS = {"assets", "docs", "scripts", ".github", ".git"}
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
EXPECTED_SCHEME = "https"
EXPECTED_HOST = "akarilab.org"


def find_html_files() -> set[Path]:
    files: set[Path] = set()
    for path in REPO_ROOT.rglob("*.html"):
        rel = path.relative_to(REPO_ROOT)
        if rel.parts[0] in EXCLUDED_TOP_DIRS:
            continue
        files.add(path)
    return files


def url_to_local_path(url: str) -> Path | None:
    parsed = urlparse(url)
    path = parsed.path.lstrip("/")
    if path == "" or path.endswith("/"):
        candidate = REPO_ROOT / path / "index.html"
    else:
        candidate = REPO_ROOT / path
    return candidate


def main() -> int:
    if not SITEMAP.is_file():
        print(f"FAIL: sitemap.xml not found at {SITEMAP}")
        return 1

    tree = ET.parse(SITEMAP)
    root = tree.getroot()
    sitemap_urls: list[str] = []
    for url_elem in root.findall(f"{SITEMAP_NS}url"):
        loc = url_elem.find(f"{SITEMAP_NS}loc")
        if loc is not None and loc.text:
            sitemap_urls.append(loc.text.strip())

    failures: list[str] = []
    sitemap_paths: set[Path] = set()
    for url in sitemap_urls:
        parsed = urlparse(url)
        if parsed.scheme != EXPECTED_SCHEME:
            failures.append(f"URL scheme is not {EXPECTED_SCHEME}: {url}")
            continue
        if parsed.netloc != EXPECTED_HOST:
            failures.append(f"URL host is not {EXPECTED_HOST}: {url}")
            continue
        local = url_to_local_path(url)
        if local is None or not local.is_file():
            failures.append(f"URL in sitemap not found on disk: {url} -> {local}")
            continue
        sitemap_paths.add(local.resolve())

    if failures:
        print(f"FAIL: {len(failures)} sitemap URLs unresolved")
        for msg in failures:
            print(f"  {msg}")
        return 1

    html_files = {p.resolve() for p in find_html_files()}
    missing_in_sitemap = sorted(html_files - sitemap_paths)
    if missing_in_sitemap:
        print(f"WARN: {len(missing_in_sitemap)} HTML files not in sitemap (informational, not fail)")
        for path in missing_in_sitemap:
            print(f"  {path.relative_to(REPO_ROOT)}")

    print(f"OK: sitemap has {len(sitemap_urls)} entries, all resolved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
