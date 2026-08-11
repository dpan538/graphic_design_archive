#!/usr/bin/env python3
"""Normalize a PostgreSQL schema-only dump and emit its SHA-256."""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import sys


IGNORED_PREFIXES = (
    "--",
    "SET ",
    "SELECT pg_catalog.set_config",
    "\\restrict ",
    "\\unrestrict ",
)


def normalize(text: str) -> bytes:
    lines: list[str] = []
    blank = False
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw.rstrip()
        if line.startswith(IGNORED_PREFIXES):
            continue
        line = re.sub(r"^\\connect\s+\S+\s*$", "", line)
        if not line:
            if lines and not blank:
                lines.append("")
            blank = True
            continue
        blank = False
        lines.append(line)
    while lines and not lines[-1]:
        lines.pop()
    return ("\n".join(lines) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dump", type=pathlib.Path)
    parser.add_argument("--write-normalized", type=pathlib.Path)
    args = parser.parse_args()
    source = args.dump.read_text(encoding="utf-8")
    normalized = normalize(source)
    if args.write_normalized:
        args.write_normalized.write_bytes(normalized)
    print(hashlib.sha256(normalized).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
