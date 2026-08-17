#!/usr/bin/env python3
"""Build a self-contained manifest/checksum pair for an additive audit package."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--schema", required=True)
    args = parser.parse_args()
    package = args.package.resolve()
    repo = Path(subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=package, text=True,
        capture_output=True, check=True
    ).stdout.strip()).resolve()
    if not package.is_dir() or repo not in package.parents:
        raise SystemExit("PACKAGE_NOT_IN_REPOSITORY")
    manifest, checksums = package / "MANIFEST.json", package / "CHECKSUMS.sha256"
    files = sorted(path for path in package.rglob("*") if path.is_file()
                   and not path.is_symlink() and path not in (manifest, checksums))
    relative = [str(path.relative_to(package)) for path in files]
    ignored = subprocess.run(
        ["git", "check-ignore", "--no-index", "-z", "--stdin"], cwd=repo,
        input=("\0".join(str(path.relative_to(repo)) for path in files) + "\0").encode(),
        capture_output=True, check=False,
    )
    if ignored.returncode not in (0, 1) or ignored.stdout:
        raise SystemExit("AUDIT_ARTIFACT_IGNORED")
    entries = [{"path": name, "bytes": path.stat().st_size, "sha256": digest(path)}
               for name, path in zip(relative, files)]
    manifest.write_text(json.dumps({"schema": args.schema, "files": entries}, sort_keys=True, indent=2) + "\n")
    checksum_entries = [(digest(path), name) for name, path in zip(relative, files)]
    checksum_entries.append((digest(manifest), "MANIFEST.json"))
    checksums.write_text("".join(f"{value}  {name}\n" for value, name in checksum_entries))
    print(json.dumps({"manifestFileCount": len(entries), "checksumFileCount": len(checksum_entries), "status": "PASS"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
