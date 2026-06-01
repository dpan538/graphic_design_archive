#!/usr/bin/env python3
"""Fail if generated archive files contain common API-token patterns."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEARCH_ROOTS = ("data", "docs", "generated", "frontend", "scripts")
PATTERNS = {
    "google_api_key": re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    "url_key_parameter": re.compile(r"(?i)(?:[?&;]|&#038;)key=[0-9A-Za-z_-]{20,}"),
    "github_token": re.compile(r"\bgh[pousr]_[0-9A-Za-z_]{30,}\b"),
    "openai_key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
}
SKIP_DIRS = {".git", "node_modules", ".next", "dist", "build"}


def iter_files() -> list[Path]:
    files: list[Path] = []
    for root_name in SEARCH_ROOTS:
        root = ROOT / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.is_file():
                files.append(path)
    return files


def main() -> int:
    findings: list[tuple[str, str, int]] = []
    for path in iter_files():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for name, pattern in PATTERNS.items():
                if pattern.search(line):
                    findings.append((str(path.relative_to(ROOT)), name, line_no))
    if findings:
        print("possible secret patterns detected:")
        for rel_path, name, line_no in findings:
            print(f"- {rel_path}:{line_no} ({name})")
        return 1
    print("no common secret patterns detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
