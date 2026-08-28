#!/usr/bin/env python3
"""Record and verify every current LFS pointer and hydrated source payload."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess


LFS_ROW = re.compile(r"^([0-9a-f]{64})\s+[-*]\s+(.+)$")
OID_LINE = re.compile(r"^oid sha256:([0-9a-f]{64})$", re.MULTILINE)
SIZE_LINE = re.compile(r"^size ([0-9]+)$", re.MULTILINE)


def run(repo: Path, *argv: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(argv, cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    manifest_path = args.manifest if args.manifest.is_absolute() else repo / args.manifest
    summary_path = args.summary if args.summary.is_absolute() else repo / args.summary
    listed = run(repo, "git", "lfs", "ls-files", "--long")
    if listed.returncode:
        raise SystemExit(listed.stderr.decode("utf-8", "replace"))
    rows: list[dict[str, object]] = []
    failures: list[str] = []
    for line in listed.stdout.decode("utf-8", "replace").splitlines():
        match = LFS_ROW.match(line)
        if not match:
            failures.append(f"UNPARSEABLE_LFS_ROW:{line}")
            continue
        listed_oid, relative = match.groups()
        pointer = run(repo, "git", "show", f"HEAD:{relative}")
        if pointer.returncode:
            failures.append(f"HEAD_POINTER_MISSING:{relative}")
            continue
        pointer_text = pointer.stdout.decode("utf-8", "replace")
        oid_match = OID_LINE.search(pointer_text)
        size_match = SIZE_LINE.search(pointer_text)
        canonical = pointer_text.startswith("version https://git-lfs.github.com/spec/v1\n") and bool(oid_match and size_match)
        pointer_oid = oid_match.group(1) if oid_match else ""
        pointer_size = int(size_match.group(1)) if size_match else -1
        hydrated = repo / relative
        hydrated_exists = hydrated.is_file()
        hydrated_bytes = hydrated.stat().st_size if hydrated_exists else -1
        hydrated_sha = sha256(hydrated) if hydrated_exists else "MISSING"
        hash_match = pointer_oid == hydrated_sha == listed_oid
        size_match_value = pointer_size == hydrated_bytes
        head_blob = run(repo, "git", "rev-parse", f"HEAD:{relative}").stdout.decode().strip()
        if not canonical:
            failures.append(f"NONCANONICAL_POINTER:{relative}")
        if not hash_match:
            failures.append(f"HYDRATED_HASH_MISMATCH:{relative}")
        if not size_match_value:
            failures.append(f"HYDRATED_SIZE_MISMATCH:{relative}")
        rows.append(
            {
                "path": relative,
                "head_pointer_blob_oid": head_blob,
                "lfs_oid_sha256": pointer_oid,
                "pointer_size": pointer_size,
                "hydrated_bytes": hydrated_bytes,
                "hydrated_sha256": hydrated_sha,
                "canonical_pointer": str(canonical).lower(),
                "payload_hash_match": str(hash_match).lower(),
                "payload_size_match": str(size_match_value).lower(),
            }
        )
    rows.sort(key=lambda row: str(row["path"]))
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO(newline="")
    fieldnames = [
        "path", "head_pointer_blob_oid", "lfs_oid_sha256", "pointer_size", "hydrated_bytes",
        "hydrated_sha256", "canonical_pointer", "payload_hash_match", "payload_size_match",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, dialect="excel-tab", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    manifest_path.write_text(buffer.getvalue(), encoding="utf-8")
    lfs_fsck = run(repo, "git", "lfs", "fsck")
    if lfs_fsck.returncode:
        failures.append("GIT_LFS_FSCK_FAIL")
    summary = {
        "schema_version": "trace-round16b-source-lfs-verification/v1",
        "current_lfs_path_count": len(rows),
        "canonical_pointer_count": sum(row["canonical_pointer"] == "true" for row in rows),
        "hydrated_hash_match_count": sum(row["payload_hash_match"] == "true" for row in rows),
        "hydrated_size_match_count": sum(row["payload_size_match"] == "true" for row in rows),
        "total_hydrated_bytes": sum(int(row["hydrated_bytes"]) for row in rows),
        "git_lfs_fsck": "PASS" if lfs_fsck.returncode == 0 else "FAIL",
        "manifest_path": str(manifest_path.relative_to(repo)),
        "manifest_sha256": sha256(manifest_path),
        "failure_codes": failures,
        "status": "PASS" if not failures else "FAIL",
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": summary["status"], "path_count": len(rows), "failure_count": len(failures)}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
