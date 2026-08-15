#!/usr/bin/env python3
"""Fail closed when a committed audit package references absent evidence.

The verifier deliberately treats a package manifest, its checksum ledger, and
the Git index as one release unit.  It is intended for *new* audit packages;
it does not rewrite or reinterpret historical package manifests.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


class VerificationError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not value or value == ".":
        raise VerificationError(f"UNSAFE_RELATIVE_PATH:{value}")
    return path


def git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=cwd, text=True, capture_output=True, check=False
    )


def parse_checksums(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw:
            continue
        try:
            digest, name = raw.split("  ", 1)
        except ValueError as error:
            raise VerificationError(f"CHECKSUM_FORMAT_LINE_{line_number}") from error
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise VerificationError(f"CHECKSUM_DIGEST_LINE_{line_number}")
        name = str(safe_relative(name))
        if name in entries:
            raise VerificationError(f"DUPLICATE_CHECKSUM_PATH:{name}")
        entries[name] = digest
    if not entries:
        raise VerificationError("EMPTY_CHECKSUM_LEDGER")
    return entries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--require-index", action="store_true")
    args = parser.parse_args()

    package = args.package.resolve()
    repo = Path(
        git("rev-parse", "--show-toplevel", cwd=package).stdout.strip()
    ).resolve()
    if not package.is_dir() or not str(package).startswith(str(repo) + os.sep):
        raise VerificationError("PACKAGE_NOT_IN_REPOSITORY")

    manifest_path = package / "MANIFEST.json"
    checksums_path = package / "CHECKSUMS.sha256"
    if not manifest_path.is_file() or not checksums_path.is_file():
        raise VerificationError("PACKAGE_METADATA_MISSING")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise VerificationError("MANIFEST_FILES_MISSING")

    manifest_entries: dict[str, dict[str, object]] = {}
    for entry in files:
        if not isinstance(entry, dict):
            raise VerificationError("MANIFEST_ENTRY_INVALID")
        name = entry.get("path")
        digest = entry.get("sha256")
        size = entry.get("bytes")
        if not isinstance(name, str) or not isinstance(digest, str) or not isinstance(size, int):
            raise VerificationError("MANIFEST_ENTRY_FIELDS_INVALID")
        name = str(safe_relative(name))
        if name in manifest_entries:
            raise VerificationError(f"DUPLICATE_MANIFEST_PATH:{name}")
        manifest_entries[name] = {"sha256": digest, "bytes": size}

    checksum_entries = parse_checksums(checksums_path)
    expected_checksum_paths = set(manifest_entries) | {"MANIFEST.json"}
    if set(checksum_entries) != expected_checksum_paths:
        missing = sorted(expected_checksum_paths - set(checksum_entries))
        extra = sorted(set(checksum_entries) - expected_checksum_paths)
        raise VerificationError(f"CHECKSUM_SCOPE_MISMATCH:missing={missing}:extra={extra}")

    package_relative = package.relative_to(repo)
    checked_paths = sorted(expected_checksum_paths)
    repo_paths = {name: str(package_relative / name) for name in checked_paths}
    ignored_check = subprocess.run(
        ["git", "check-ignore", "--no-index", "-z", "--stdin"], cwd=repo,
        input=("\0".join(repo_paths.values()) + "\0").encode("utf-8"), capture_output=True, check=False,
    )
    if ignored_check.returncode not in (0, 1):
        raise VerificationError("GIT_IGNORE_BATCH_CHECK_FAILED")
    ignored_paths = {item.decode("utf-8") for item in ignored_check.stdout.split(b"\0") if item}
    if ignored_paths:
        raise VerificationError("AUDIT_ARTIFACT_IGNORED:" + ",".join(sorted(ignored_paths)))
    tracked_paths: set[str] = set()
    if args.require_index:
        indexed = subprocess.run(
            ["git", "ls-files", "-z", "--", str(package_relative)], cwd=repo,
            capture_output=True, check=False,
        )
        if indexed.returncode:
            raise VerificationError("GIT_INDEX_BATCH_CHECK_FAILED")
        tracked_paths = {item.decode("utf-8") for item in indexed.stdout.split(b"\0") if item}
    for name in checked_paths:
        artifact = package / name
        if not artifact.is_file() or artifact.is_symlink():
            raise VerificationError(f"ARTIFACT_MISSING_OR_SPECIAL:{name}")
        actual = sha256(artifact)
        if actual != checksum_entries[name]:
            raise VerificationError(f"CHECKSUM_MISMATCH:{name}")
        if name in manifest_entries:
            expected = manifest_entries[name]
            if actual != expected["sha256"] or artifact.stat().st_size != expected["bytes"]:
                raise VerificationError(f"MANIFEST_BINDING_MISMATCH:{name}")

        if args.require_index and repo_paths[name] not in tracked_paths:
            raise VerificationError(f"AUDIT_ARTIFACT_NOT_IN_INDEX:{repo_paths[name]}")

    result = {
        "status": "PASS",
        "package": str(package_relative),
        "manifestFileCount": len(manifest_entries),
        "checksumFileCount": len(checksum_entries),
        "indexRequired": args.require_index,
        "ignoredEvidenceRejected": True,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, json.JSONDecodeError) as error:
        print(f"AUDIT_PACKAGE_SELF_CONTAINED=FAIL:{error}", file=sys.stderr)
        raise SystemExit(2)
