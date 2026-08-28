#!/usr/bin/env python3
"""Capture and verify the immutable Round 16B bootstrap and recovery state."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import platform
from pathlib import Path
import subprocess
from typing import Any


SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
MAIN_SHA = "8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e"
SOURCE_REF = "refs/heads/codex/trace-v49-exploration-full-space-closure-round1"
WORK_BRANCH = "codex/trace-v49-exploration-higher-order-association-closure-round16b"
WORK_REF = f"refs/heads/{WORK_BRANCH}"
ROLLBACK_REF = "refs/tags/rollback/trace-v49-exploration-higher-order-association-closure-round16b-source"
EXPECTED_LFS_RULES = [
    "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/large/** filter=lfs diff=lfs merge=lfs -text",
    "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/search-shards/** filter=lfs diff=lfs merge=lfs -text",
    "frontend/generated/trace-exploration-v2-higher-order/*.json filter=lfs diff=lfs merge=lfs -text",
]


def run(repo: Path, *argv: str, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        argv,
        cwd=repo,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def text(result: subprocess.CompletedProcess[bytes]) -> str:
    return result.stdout.decode("utf-8", "replace").strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_remote_map(raw: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        object_id, ref = line.split("\t", 1)
        mapping[ref] = object_id
    return mapping


def scan_blobs(repo: Path) -> dict[str, Any]:
    objects = run(repo, "git", "rev-list", "--objects", "HEAD")
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
    maximum = {"bytes": 0, "object_sha": "", "path": ""}
    over_limit: list[dict[str, Any]] = []
    blob_count = 0
    for line in checked.stdout.decode("utf-8", "surrogateescape").splitlines():
        parts = line.split(" ", 3)
        if len(parts) < 3 or parts[1] != "blob":
            continue
        blob_count += 1
        size = int(parts[2])
        path = parts[3] if len(parts) == 4 else ""
        if size > maximum["bytes"]:
            maximum = {"bytes": size, "object_sha": parts[0], "path": path}
        if size >= 100_000_000:
            over_limit.append({"bytes": size, "object_sha": parts[0], "path": path})
    return {
        "reachable_blob_count": blob_count,
        "ordinary_blob_ge_100000000_count": len(over_limit),
        "ordinary_blob_ge_100000000": over_limit,
        "maximum_reachable_ordinary_blob": maximum,
    }


def command_version(repo: Path, *argv: str) -> dict[str, Any]:
    result = run(repo, *argv)
    return {
        "argv": list(argv),
        "exit_code": result.returncode,
        "stdout": text(result),
        "stderr": result.stderr.decode("utf-8", "replace").strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--restore-repo", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--initial-publication-receipt", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    bundle = args.bundle.resolve()
    restore = args.restore_repo.resolve()
    initial_publication_path = args.initial_publication_receipt.resolve()
    initial_publication = json.loads(initial_publication_path.read_text(encoding="utf-8"))
    output_dir = args.output_dir if args.output_dir.is_absolute() else repo / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    captured_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    failures: list[str] = []

    head = text(run(repo, "git", "rev-parse", "HEAD"))
    head_tree = text(run(repo, "git", "rev-parse", "HEAD^{tree}"))
    source_tree = text(run(repo, "git", "rev-parse", f"{SOURCE_SHA}^{{tree}}"))
    branch = text(run(repo, "git", "branch", "--show-current"))
    status_lines = text(run(repo, "git", "status", "--porcelain=v1", "--untracked-files=all")).splitlines()
    logger_owned_prefixes = (
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/commands/",
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/execution-events.jsonl",
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/command-ledger.tsv",
        "docs/research/trace-v49-exploration-higher-order-association-closure-round16b/00_LIVE_EXECUTION_LOG.md",
    )
    non_logger_status = [
        line
        for line in status_lines
        if not any(line[3:].startswith(prefix) for prefix in logger_owned_prefixes)
    ]
    source_ancestor = run(repo, "git", "merge-base", "--is-ancestor", SOURCE_SHA, head).returncode == 0
    remote_result = run(repo, "git", "ls-remote", "--refs", "origin")
    remote_map = parse_remote_map(text(remote_result)) if remote_result.returncode == 0 else {}
    remote_ref_path = output_dir / "source-remote-ref-map.tsv"
    remote_ref_path.write_text(
        "object_sha\tref\n" + "".join(f"{oid}\t{ref}\n" for ref, oid in sorted(remote_map.items())),
        encoding="utf-8",
    )

    bundle_verify = run(repo, "git", "bundle", "verify", str(bundle))
    bundle_hash = sha256(bundle) if bundle.is_file() else "MISSING"
    restore_head = text(run(restore, "git", "rev-parse", "HEAD"))
    restore_tree = text(run(restore, "git", "rev-parse", "HEAD^{tree}"))
    restore_count = text(run(restore, "git", "rev-list", "--count", "HEAD"))
    restore_status = text(run(restore, "git", "status", "--porcelain=v1"))
    restore_fsck = run(restore, "git", "fsck", "--full", "--strict", "--no-dangling")
    lfs_fsck = run(repo, "git", "lfs", "fsck")
    lfs_rows = [row for row in text(run(repo, "git", "lfs", "ls-files", "--all", "--long")).splitlines() if row]
    blob_scan = scan_blobs(repo)
    attributes = (repo / ".gitattributes").read_text(encoding="utf-8").splitlines()

    checks = {
        "head_matches_expected_governance_commit": head == args.expected_head,
        "authorized_source_is_ancestor": source_ancestor,
        "source_tree_matches_authorized_source": source_tree == SOURCE_TREE,
        "work_branch_exact": branch == WORK_BRANCH,
        "worktree_clean_except_current_logger_outputs": not non_logger_status,
        "remote_query_pass": remote_result.returncode == 0,
        "remote_source_exact": remote_map.get(SOURCE_REF) == SOURCE_SHA,
        "remote_main_exact": remote_map.get("refs/heads/main") == MAIN_SHA,
        "remote_work_branch_matches_expected_governance_commit": remote_map.get(WORK_REF) == args.expected_head,
        "remote_rollback_tag_absent": ROLLBACK_REF not in remote_map,
        "initial_publication_receipt_pass": initial_publication.get("status") == "PASS",
        "initial_remote_work_branch_was_absent": initial_publication.get("remote_branch_before") == "ABSENT",
        "initial_publication_head_exact": initial_publication.get("local_head_sha") == args.expected_head,
        "initial_publication_used_no_force": initial_publication.get("receipt", {}).get("FORCE_PUSH_USED") is False,
        "bundle_exists": bundle.is_file(),
        "bundle_verify_pass": bundle_verify.returncode == 0,
        "restore_head_exact": restore_head == SOURCE_SHA,
        "restore_tree_exact": restore_tree == SOURCE_TREE,
        "restore_commit_count_positive": restore_count.isdigit() and int(restore_count) > 0,
        "restore_worktree_clean": restore_status == "",
        "restore_git_fsck_pass": restore_fsck.returncode == 0,
        "source_lfs_fsck_pass": lfs_fsck.returncode == 0,
        "source_ordinary_blob_limit_pass": blob_scan["ordinary_blob_ge_100000000_count"] == 0,
        "round16b_lfs_rules_present": all(rule in attributes for rule in EXPECTED_LFS_RULES),
    }
    failures.extend(key for key, passed in checks.items() if not passed)

    environment = {
        "schema_version": "trace-round16b-environment/v1",
        "captured_at_utc": captured_at,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python_runtime": platform.python_version(),
        "commands": {
            "git": command_version(repo, "git", "--version"),
            "git_lfs": command_version(repo, "git", "lfs", "version"),
            "node": command_version(repo, "node", "--version"),
            "npm": command_version(repo, "npm", "--version"),
            "postgresql": command_version(repo, "psql", "--version"),
            "sw_vers": command_version(repo, "sw_vers"),
        },
        "source_sha": SOURCE_SHA,
        "source_tree": SOURCE_TREE,
        "captured_head_sha": head,
        "captured_head_tree": head_tree,
        "work_branch": WORK_BRANCH,
    }
    write_json(output_dir / "environment.json", environment)
    write_json(
        output_dir / "large-object-preflight.json",
        {
            "schema_version": "trace-round16b-large-object-preflight/v1",
            "captured_at_utc": captured_at,
            "source_sha": SOURCE_SHA,
            "lfs_tracked_version_row_count": len(lfs_rows),
            "lfs_fsck": "PASS" if lfs_fsck.returncode == 0 else "FAIL",
            **blob_scan,
            "status": "PASS" if checks["source_lfs_fsck_pass"] and checks["source_ordinary_blob_limit_pass"] else "FAIL",
        },
    )
    receipt = {
        "schema_version": "trace-round16b-bootstrap-recovery/v1",
        "captured_at_utc": captured_at,
        "source_sha": SOURCE_SHA,
        "source_tree": SOURCE_TREE,
        "captured_head_sha": head,
        "captured_head_tree": head_tree,
        "expected_origin_main_sha": MAIN_SHA,
        "work_branch": WORK_BRANCH,
        "remote_ref_count": len(remote_map),
        "remote_ref_map_path": str(remote_ref_path.relative_to(repo)),
        "remote_ref_map_sha256": sha256(remote_ref_path),
        "initial_publication_receipt": {
            "path": str(initial_publication_path),
            "sha256": sha256(initial_publication_path),
            "status": initial_publication.get("status"),
            "remote_branch_before": initial_publication.get("remote_branch_before"),
            "remote_branch_after": initial_publication.get("remote_branch_after"),
        },
        "bundle": {
            "path": str(bundle),
            "bytes": bundle.stat().st_size if bundle.is_file() else 0,
            "sha256": bundle_hash,
            "verify_exit_code": bundle_verify.returncode,
            "complete_history_declared": b"complete history" in bundle_verify.stdout,
        },
        "restore_drill": {
            "path": str(restore),
            "head_sha": restore_head,
            "tree_sha": restore_tree,
            "commit_count": int(restore_count) if restore_count.isdigit() else 0,
            "worktree_clean": restore_status == "",
            "git_fsck": "PASS" if restore_fsck.returncode == 0 else "FAIL",
        },
        "checks": checks,
        "failure_codes": failures,
        "status": "PASS" if not failures else "FAIL",
        "receipt": {
            "SOURCE_SHA": SOURCE_SHA,
            "SOURCE_TREE": SOURCE_TREE,
            "REMOTE_MAIN_SHA": remote_map.get("refs/heads/main", "ABSENT"),
            "REMOTE_SOURCE_SHA": remote_map.get(SOURCE_REF, "ABSENT"),
            "WORK_BRANCH_REMOTE_BEFORE": remote_map.get(WORK_REF, "ABSENT"),
            "ROLLBACK_TAG_REMOTE_BEFORE": remote_map.get(ROLLBACK_REF, "ABSENT"),
            "BUNDLE_SHA256": bundle_hash,
            "RESTORE_DRILL": "PASS" if restore_fsck.returncode == 0 and restore_status == "" else "FAIL",
        },
    }
    write_json(output_dir / "source-recovery-receipt.json", receipt)
    print(json.dumps({"status": receipt["status"], "failure_count": len(failures), "outputs": 4}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
