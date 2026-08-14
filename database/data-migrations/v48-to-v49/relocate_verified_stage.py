#!/usr/bin/env python3
"""Move a verified Phase 2B staging bundle out of task-local /private/tmp.

The script accepts one exact source and one exact non-Git cache destination.
It rehashes every manifest descriptor before and after relocation, refuses an
existing destination, and never removes the source until the destination is
fully verified.  On the expected same APFS volume it uses atomic ``rename``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NoReturn


class RelocationError(RuntimeError):
    """A safe-staging relocation invariant failure."""


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RelocationError(f"DUPLICATE_JSON_KEY:{key}")
        result[key] = value
    return result


def reject_constant(value: str) -> NoReturn:
    raise RelocationError(f"UNSUPPORTED_JSON_CONSTANT:{value}")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_object, parse_constant=reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RelocationError(f"JSON_READ_FAILED:{path}") from exc
    if not isinstance(value, dict):
        raise RelocationError(f"JSON_NOT_OBJECT:{path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def kib(path: Path) -> int:
    return int(shutil.disk_usage(path).used // 1024) if False else sum(item.stat().st_size for item in path.rglob("*") if item.is_file()) // 1024


def descriptors(root: Path) -> dict[str, Any]:
    manifest_path = root / "staging-manifest.json"
    manifest = read_json(manifest_path)
    files = manifest.get("files")
    if not isinstance(files, dict) or len(files) != 35:
        raise RelocationError("STAGING_DESCRIPTOR_COUNT_INVALID")
    values: dict[str, dict[str, Any]] = {}
    for relative, descriptor in sorted(files.items()):
        if not isinstance(relative, str) or not isinstance(descriptor, dict):
            raise RelocationError("STAGING_DESCRIPTOR_INVALID")
        source = root / relative
        expected_bytes = descriptor.get("bytes")
        expected_sha = descriptor.get("sha256")
        if not isinstance(expected_bytes, int) or not isinstance(expected_sha, str) or not source.is_file():
            raise RelocationError(f"STAGING_DESCRIPTOR_INVALID:{relative}")
        actual_bytes = source.stat().st_size
        actual_sha = sha256_file(source)
        if actual_bytes != expected_bytes or actual_sha != expected_sha:
            raise RelocationError(f"STAGING_DESCRIPTOR_MISMATCH:{relative}")
        values[relative] = {"bytes": actual_bytes, "sha256": actual_sha}
    return {
        "realpath": str(root.resolve()), "manifestSha256": sha256_file(manifest_path),
        "descriptorCount": len(values), "descriptorRehash": "PASS", "descriptors": values,
        "contentBytes": sum(value["bytes"] for value in values.values()),
        "treeKiB": kib(root),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.resolve()
    destination = args.destination.resolve(strict=False)
    output = args.output.resolve(strict=False)
    if not str(source).startswith("/private/tmp/gda_v49_phase2b_"):
        raise RelocationError("SOURCE_PATH_NOT_TASK_OWNED_TEMP")
    if not str(destination).startswith("/Users/jarlgiovanni/Library/Caches/gda_v49_phase2b/"):
        raise RelocationError("DESTINATION_NOT_APPROVED_STABLE_CACHE")
    if not source.is_dir() or destination.exists() or output.exists():
        raise RelocationError("RELOCATION_TARGET_STATE_INVALID")
    before = descriptors(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if os.stat(source).st_dev == os.stat(destination.parent).st_dev:
        os.rename(source, destination)
        method = "atomic_rename_same_filesystem"
    else:
        shutil.copytree(source, destination, copy_function=shutil.copy2)
        after_copy = descriptors(destination)
        if after_copy["descriptors"] != before["descriptors"] or after_copy["manifestSha256"] != before["manifestSha256"]:
            raise RelocationError("CROSS_FILESYSTEM_COPY_DESCRIPTOR_MISMATCH")
        shutil.rmtree(source)
        method = "copy_verify_then_remove_cross_filesystem"
    after = descriptors(destination)
    if after["descriptors"] != before["descriptors"] or after["manifestSha256"] != before["manifestSha256"]:
        raise RelocationError("POST_MOVE_DESCRIPTOR_MISMATCH")
    if source.exists():
        raise RelocationError("SOURCE_STILL_PRESENT_AFTER_MOVE")
    payload = {
        "schema": "gda-v49-phase2b-staging-relocation/v1",
        "status": "PASS",
        "movedAtUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "method": method,
        "before": before,
        "after": after,
        "sourceVerifiedAbsent": True,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
    print(json.dumps({
        "status": "PASS", "method": method, "descriptorCount": after["descriptorCount"],
        "destination": str(destination), "output": str(output),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RelocationError, OSError, shutil.Error, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
