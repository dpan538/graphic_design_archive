#!/usr/bin/env python3
"""Block new Round 16B ordinary blobs before they approach hosting limits."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


def run(repo: Path, *argv: str, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        argv,
        cwd=repo,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nul_paths(result: subprocess.CompletedProcess[bytes]) -> set[str]:
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", "replace"))
    return {item.decode("utf-8", "surrogateescape") for item in result.stdout.split(b"\0") if item}


def changed_paths(repo: Path, base_sha: str) -> set[str]:
    paths: set[str] = set()
    paths |= nul_paths(run(repo, "git", "diff", "--name-only", "-z", f"{base_sha}..HEAD"))
    paths |= nul_paths(run(repo, "git", "diff", "--name-only", "-z"))
    paths |= nul_paths(run(repo, "git", "diff", "--cached", "--name-only", "-z"))
    paths |= nul_paths(run(repo, "git", "ls-files", "--others", "--exclude-standard", "-z"))
    return paths


def lfs_filter(repo: Path, path: str) -> str:
    result = run(repo, "git", "check-attr", "filter", "--", path)
    if result.returncode:
        return "ERROR"
    line = result.stdout.decode("utf-8", "replace").strip()
    return line.rsplit(": ", 1)[-1] if line else "unspecified"


def committed_new_blobs(repo: Path, base_sha: str) -> list[dict[str, Any]]:
    objects = run(repo, "git", "rev-list", "--objects", f"{base_sha}..HEAD")
    if objects.returncode:
        raise RuntimeError(objects.stderr.decode("utf-8", "replace"))
    checked = run(
        repo,
        "git",
        "cat-file",
        "--batch-check=%(objectname) %(objecttype) %(objectsize) %(rest)",
        input_bytes=objects.stdout,
    )
    if checked.returncode:
        raise RuntimeError(checked.stderr.decode("utf-8", "replace"))
    rows: list[dict[str, Any]] = []
    for line in checked.stdout.decode("utf-8", "surrogateescape").splitlines():
        parts = line.split(" ", 3)
        if len(parts) >= 3 and parts[1] == "blob":
            rows.append(
                {
                    "object_sha": parts[0],
                    "bytes": int(parts[2]),
                    "path": parts[3] if len(parts) == 4 else "",
                }
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    policy_path = args.policy if args.policy.is_absolute() else repo / args.policy
    output_path = args.output if args.output.is_absolute() else repo / args.output
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    base_sha = str(policy["source_sha"])
    warning = int(policy["thresholds_bytes"]["warning"])
    lfs_required = int(policy["thresholds_bytes"]["lfs_required"])
    hard_block = int(policy["thresholds_bytes"]["ordinary_blob_hard_block"])
    hosting_limit = int(policy["thresholds_bytes"]["hosting_enforced_limit"])

    worktree_rows: list[dict[str, Any]] = []
    failures: list[str] = []
    warnings: list[str] = []
    for relative in sorted(changed_paths(repo, base_sha)):
        path = repo / relative
        if not path.is_file():
            continue
        size = path.stat().st_size
        filter_value = lfs_filter(repo, relative)
        row = {
            "path": relative,
            "hydrated_bytes": size,
            "sha256": sha256(path),
            "lfs_filter": filter_value,
            "warning_threshold_reached": size >= warning,
            "lfs_required_threshold_reached": size >= lfs_required,
        }
        worktree_rows.append(row)
        if size >= warning:
            warnings.append(f"LARGE_CHANGED_FILE:{relative}:{size}")
        if size >= lfs_required and filter_value != "lfs":
            failures.append(f"LFS_REQUIRED:{relative}:{size}")
        if size >= hosting_limit and filter_value != "lfs":
            failures.append(f"HOSTING_LIMIT_WORKTREE:{relative}:{size}")

    committed_rows = committed_new_blobs(repo, base_sha)
    for row in committed_rows:
        if int(row["bytes"]) >= hard_block:
            failures.append(
                f"NEW_ORDINARY_BLOB_HARD_BLOCK:{row['object_sha']}:{row['bytes']}:{row['path']}"
            )
        if int(row["bytes"]) >= hosting_limit:
            failures.append(
                f"NEW_ORDINARY_BLOB_HOSTING_LIMIT:{row['object_sha']}:{row['bytes']}:{row['path']}"
            )

    attributes = (repo / ".gitattributes").read_text(encoding="utf-8").splitlines()
    missing_rules = [rule for rule in policy["required_lfs_attribute_rules"] if rule not in attributes]
    failures.extend(f"MISSING_LFS_RULE:{rule}" for rule in missing_rules)
    result = {
        "schema_version": "trace-round16b-new-blob-policy-verification/v1",
        "source_sha": base_sha,
        "policy_path": str(policy_path.relative_to(repo)),
        "policy_sha256": sha256(policy_path),
        "thresholds_bytes": policy["thresholds_bytes"],
        "changed_file_count": len(worktree_rows),
        "changed_files": worktree_rows,
        "new_committed_blob_count": len(committed_rows),
        "maximum_new_committed_blob_bytes": max((int(row["bytes"]) for row in committed_rows), default=0),
        "warning_codes": sorted(set(warnings)),
        "failure_codes": sorted(set(failures)),
        "missing_lfs_rule_count": len(missing_rules),
        "status": "PASS" if not failures else "FAIL",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": result["status"],
                "failure_count": len(result["failure_codes"]),
                "warning_count": len(result["warning_codes"]),
                "maximum_new_committed_blob_bytes": result["maximum_new_committed_blob_bytes"],
            },
            sort_keys=True,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
