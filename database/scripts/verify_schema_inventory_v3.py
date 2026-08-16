#!/usr/bin/env python3
"""Verify the additive v3 schema inventory without altering historical inventory."""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "database/schema-manifest-v3.json"


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    files = manifest["managedFiles"]
    missing = [path for path in files if not (ROOT / path).is_file()]
    if missing:
        print("SCHEMA_INVENTORY_V3=FAIL missing=" + ",".join(missing))
        return 1
    lines = []
    for path in files:
        digest = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        lines.append(f"{digest}  {path}\\n")
    actual = hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()
    expected = manifest["managedFilesDigest"]
    if actual != expected:
        print(f"SCHEMA_INVENTORY_V3=FAIL expected={expected} actual={actual}")
        return 1
    required = {
        "database/migrations/009_read_api_core.sql",
        "database/migrations/010_release_projection_snapshot.sql",
        "database/functions/016_release_projection_snapshot_v3.sql",
        "database/roles/003_read_api_core_grants.sql",
        "database/roles/004_release_projection_snapshot_grants.sql",
        "database/tests/005_release_projection_snapshot.sql",
    }
    if not required.issubset(files):
        print("SCHEMA_INVENTORY_V3=FAIL required-entry-missing")
        return 1
    print(f"SCHEMA_INVENTORY_V3=PASS files={len(files)} digest={actual}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
