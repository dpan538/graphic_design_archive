#!/usr/bin/env python3
"""Ordinary-push one Round 16B checkpoint and preserve an external receipt."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import time
from typing import Any


SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
MAIN_SHA = "8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e"
BRANCH = "codex/trace-v49-exploration-higher-order-association-closure-round16b"
BRANCH_REF = f"refs/heads/{BRANCH}"
ROLLBACK_REF = "refs/tags/rollback/trace-v49-exploration-higher-order-association-closure-round16b-source"
PUSH_ARGV = ["git", "push", "origin", f"HEAD:{BRANCH_REF}"]


def run(repo: Path, *argv: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(argv, cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def out(result: subprocess.CompletedProcess[bytes]) -> str:
    return result.stdout.decode("utf-8", "replace").strip()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def remote_map(repo: Path) -> tuple[subprocess.CompletedProcess[bytes], dict[str, str]]:
    result = run(repo, "git", "ls-remote", "--refs", "origin")
    mapping: dict[str, str] = {}
    if result.returncode == 0:
        for line in result.stdout.decode("utf-8", "replace").splitlines():
            if line.strip():
                object_id, ref = line.split("\t", 1)
                mapping[ref] = object_id
    return result, mapping


def map_hash(mapping: dict[str, str]) -> str:
    material = "".join(f"{mapping[ref]}\t{ref}\n" for ref in sorted(mapping))
    return hashlib.sha256(material.encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--ledger-dir", type=Path, required=True)
    parser.add_argument("--checkpoint-id", required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    ledger = args.ledger_dir.resolve()
    ledger.mkdir(parents=True, exist_ok=True)
    attempt_id = f"{time.time_ns()}-{args.checkpoint_id.lower()}"
    receipt_path = ledger / f"{attempt_id}.json"
    stdout_path = ledger / f"{attempt_id}.stdout.log"
    stderr_path = ledger / f"{attempt_id}.stderr.log"
    started = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    failures: list[str] = []

    head = out(run(repo, "git", "rev-parse", "HEAD"))
    branch = out(run(repo, "git", "branch", "--show-current"))
    status = out(run(repo, "git", "status", "--porcelain=v1", "--untracked-files=all"))
    source_ancestor = run(repo, "git", "merge-base", "--is-ancestor", SOURCE_SHA, head).returncode == 0
    before_result, before = remote_map(repo)
    remote_before = before.get(BRANCH_REF)
    prior_tip_ancestor = True
    if remote_before:
        prior_tip_ancestor = run(repo, "git", "merge-base", "--is-ancestor", remote_before, head).returncode == 0
    preconditions = {
        "current_branch_exact": branch == BRANCH,
        "worktree_clean": status == "",
        "source_is_ancestor": source_ancestor,
        "remote_inventory_pass": before_result.returncode == 0,
        "remote_main_exact": before.get("refs/heads/main") == MAIN_SHA,
        "rollback_tag_absent": ROLLBACK_REF not in before,
        "remote_prior_tip_is_ancestor_or_absent": prior_tip_ancestor,
        "push_argv_has_no_force": all("force" not in value and not value.startswith("+") for value in PUSH_ARGV),
        "push_refspec_exact": PUSH_ARGV[-1] == f"HEAD:{BRANCH_REF}",
    }
    failures.extend(f"PRECONDITION:{key}" for key, passed in preconditions.items() if not passed)

    push = subprocess.CompletedProcess(PUSH_ARGV, 125, b"", b"push skipped because a precondition failed")
    if not failures:
        push = run(repo, *PUSH_ARGV)
    stdout_path.write_bytes(push.stdout)
    stderr_path.write_bytes(push.stderr)
    if push.returncode:
        failures.append(f"PUSH_EXIT_{push.returncode}")

    after_result, after = remote_map(repo)
    postconditions = {
        "remote_inventory_pass": after_result.returncode == 0,
        "remote_branch_equals_local_head": after.get(BRANCH_REF) == head,
        "remote_main_unchanged": after.get("refs/heads/main") == MAIN_SHA,
        "rollback_tag_absent": ROLLBACK_REF not in after,
    }
    failures.extend(f"POSTCONDITION:{key}" for key, passed in postconditions.items() if not passed)
    unrelated_differences: list[dict[str, str]] = []
    for ref in sorted(set(before) | set(after)):
        if ref == BRANCH_REF:
            continue
        if before.get(ref) != after.get(ref):
            unrelated_differences.append(
                {"ref": ref, "before": before.get(ref, "ABSENT"), "after": after.get(ref, "ABSENT")}
            )
    if unrelated_differences:
        failures.append("UNRELATED_REMOTE_REF_DIFFERENCE")

    receipt: dict[str, Any] = {
        "schema_version": "trace-round16b-checkpoint-publication/v1",
        "attempt_id": attempt_id,
        "checkpoint_id": args.checkpoint_id,
        "started_at_utc": started,
        "repo": str(repo),
        "branch": BRANCH,
        "branch_ref": BRANCH_REF,
        "source_sha": SOURCE_SHA,
        "local_head_sha": head,
        "push_argv": PUSH_ARGV,
        "push_exit_code": push.returncode,
        "push_stdout_path": str(stdout_path),
        "push_stdout_sha256": sha256_bytes(push.stdout),
        "push_stderr_path": str(stderr_path),
        "push_stderr_sha256": sha256_bytes(push.stderr),
        "preconditions": preconditions,
        "postconditions": postconditions,
        "remote_branch_before": remote_before or "ABSENT",
        "remote_branch_after": after.get(BRANCH_REF, "ABSENT"),
        "remote_main_before": before.get("refs/heads/main", "ABSENT"),
        "remote_main_after": after.get("refs/heads/main", "ABSENT"),
        "remote_ref_map_before_sha256": map_hash(before),
        "remote_ref_map_after_sha256": map_hash(after),
        "unrelated_remote_ref_differences": unrelated_differences,
        "unrelated_remote_ref_difference_count": len(unrelated_differences),
        "receipt": {
            "FINAL_LOCAL_SHA": head,
            "FINAL_REMOTE_SHA": after.get(BRANCH_REF, "ABSENT"),
            "REMOTE_MAIN_SHA": after.get("refs/heads/main", "ABSENT"),
            "WORKTREE_CLEAN": status == "",
            "FORCE_PUSH_USED": False,
            "HISTORY_REWRITTEN": False,
            "ROLLBACK_TAG_PUSHED": False,
            "DEPLOYMENT_PERFORMED": False,
        },
        "failure_codes": failures,
        "status": "PASS" if not failures else "FAIL",
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"receipt": str(receipt_path), "status": receipt["status"], "failure_count": len(failures)}))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
