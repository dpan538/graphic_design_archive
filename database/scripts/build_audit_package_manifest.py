#!/usr/bin/env python3
"""Build a checksum manifest for a new additive audit package only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ALLOWED_PACKAGE = ROOT / "docs/audits/v49-phase2b-evidence-amendment"


class BuildError(RuntimeError):
    pass


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def ensure_not_ignored(relative: Path) -> None:
    result = subprocess.run(["git", "check-ignore", "--quiet", "--no-index", "--", str(relative)], cwd=ROOT, check=False)
    if result.returncode == 0:
        raise BuildError(f"AUDIT_ARTIFACT_IGNORED:{relative}")
    if result.returncode not in (0, 1):
        raise BuildError(f"GIT_IGNORE_CHECK_FAILED:{relative}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    args = parser.parse_args()
    package = args.package.resolve()
    if package != ALLOWED_PACKAGE or not package.is_dir():
        raise BuildError("PACKAGE_PATH_NOT_ALLOWED")
    manifest = package / "MANIFEST.json"
    checksums = package / "CHECKSUMS.sha256"
    paths = sorted(
        path for path in package.rglob("*")
        if path.is_file() and not path.is_symlink() and path not in (manifest, checksums)
    )
    if not paths:
        raise BuildError("PACKAGE_HAS_NO_ARTIFACTS")
    repo_paths = [str(path.relative_to(ROOT)) for path in paths]
    ignored_check = subprocess.run(
        ["git", "check-ignore", "--no-index", "-z", "--stdin"], cwd=ROOT,
        input=("\0".join(repo_paths) + "\0").encode("utf-8"), capture_output=True, check=False,
    )
    if ignored_check.returncode not in (0, 1):
        raise BuildError("GIT_IGNORE_BATCH_CHECK_FAILED")
    ignored = [item.decode("utf-8") for item in ignored_check.stdout.split(b"\0") if item]
    if ignored:
        raise BuildError("AUDIT_ARTIFACT_IGNORED:" + ",".join(sorted(ignored)))
    entries = []
    for path in paths:
        relative = path.relative_to(package)
        entries.append({"bytes": path.stat().st_size, "path": str(relative), "sha256": digest(path)})
    payload = {
        "schema": "gda-v49-phase2b-evidence-amendment-manifest/v1",
        "checksumScope": "all package files except CHECKSUMS.sha256; MANIFEST.json is included in CHECKSUMS and does not self-hash",
        "files": entries,
    }
    manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checksum_entries = [(digest(path), path.relative_to(package)) for path in paths]
    checksum_entries.append((digest(manifest), Path("MANIFEST.json")))
    checksums.write_text("".join(f"{value}  {relative}\n" for value, relative in checksum_entries), encoding="utf-8")
    print(json.dumps({"status": "PASS", "package": str(package.relative_to(ROOT)), "manifestFileCount": len(entries), "checksumFileCount": len(checksum_entries)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (BuildError, OSError, json.JSONDecodeError) as error:
        print(f"AUDIT_MANIFEST_BUILD=FAIL:{error}", file=sys.stderr)
        raise SystemExit(2)
