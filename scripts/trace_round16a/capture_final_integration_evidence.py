#!/usr/bin/env python3
"""Capture verified post-push Git fields for the final Round 16A receipt.

Run this only after the final branch push and the conditional remote-main
fast-forward.  Write outside the repository (normally under ``/tmp``) so the
receipt can truthfully record a clean worktree and the final commit can refer
to itself without a commit-hash cycle.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SOURCE_SHA = "8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e"
BRANCH = "codex/trace-v49-exploration-full-space-closure-round1"
ROLLBACK_TAG = "rollback/trace-v49-exploration-full-space-closure-round1-source"


def git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=repo, check=False, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, encoding="utf-8",
    )
    if completed.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {completed.stderr.strip() or completed.stdout.strip()}")
    return completed.stdout.strip()


def read_gate_status(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    receipt = value.get("receipt") if isinstance(value, dict) else None
    if value.get("status") != "PASS" or not isinstance(receipt, dict):
        raise ValueError("ROUND16A_FINAL_INTEGRATION_GATE_STATUS_NOT_PASS")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--closed", choices=("true", "false"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    output = args.output.resolve()
    if output == repo or repo in output.parents:
        raise ValueError("ROUND16A_FINAL_INTEGRATION_OUTPUT_MUST_BE_OUTSIDE_REPOSITORY")
    if not output.parent.is_dir():
        raise FileNotFoundError(f"ROUND16A_FINAL_INTEGRATION_OUTPUT_PARENT_MISSING:{output.parent}")

    expected_closed = args.closed == "true"
    local_sha = git(repo, "rev-parse", "HEAD")
    current_branch = git(repo, "branch", "--show-current")
    remote_branch_sha = git(repo, "rev-parse", f"refs/remotes/origin/{BRANCH}")
    remote_main_sha = git(repo, "rev-parse", "refs/remotes/origin/main")
    rollback_target = git(repo, "rev-parse", f"refs/tags/{ROLLBACK_TAG}^{{commit}}")
    worktree_clean = git(repo, "status", "--porcelain=v1", "--untracked-files=all") == ""
    source_is_ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", SOURCE_SHA, local_sha], cwd=repo, check=False,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0
    merge_commit_count = int(git(repo, "rev-list", "--count", "--merges", f"{SOURCE_SHA}..{local_sha}"))
    gate_receipt = read_gate_status(repo / "docs/audits/v49-exploration-full-space-closure-round1/raw/gate-status-results.json")
    event_path = repo / "docs/audits/v49-exploration-full-space-closure-round1/raw/execution-events.jsonl"
    event_commands = "\n".join(
        str(json.loads(line).get("command", ""))
        for line in event_path.read_text(encoding="utf-8").splitlines() if line.strip()
    )
    logged_force_push = bool(re.search(r"(?i)git\s+push\b[^\n]*(?:--force|-f\b)", event_commands))
    logged_history_rewrite = bool(re.search(r"(?i)git\s+(?:rebase\b|commit\b[^\n]*--amend|reset\b)", event_commands))

    failures: list[str] = []
    if current_branch != BRANCH:
        failures.append("BRANCH_MISMATCH")
    if local_sha != remote_branch_sha:
        failures.append("REMOTE_BRANCH_SHA_MISMATCH")
    if rollback_target != SOURCE_SHA:
        failures.append("ROLLBACK_TAG_TARGET_MISMATCH")
    if not worktree_clean:
        failures.append("WORKTREE_DIRTY")
    if not source_is_ancestor:
        failures.append("SOURCE_NOT_ANCESTOR_OF_FINAL")
    if merge_commit_count:
        failures.append("MERGE_COMMIT_PRESENT")
    if gate_receipt.get("FORCE_PUSH_USED") is not False or logged_force_push:
        failures.append("FORCE_PUSH_GATE_NOT_FALSE")
    if gate_receipt.get("HISTORY_REWRITTEN") is not False or logged_history_rewrite:
        failures.append("HISTORY_REWRITTEN_GATE_NOT_FALSE")
    main_fast_forward_completed = remote_main_sha == local_sha
    if expected_closed and not main_fast_forward_completed:
        failures.append("CLOSED_ROUND_REMOTE_MAIN_NOT_FINAL")
    if not expected_closed and remote_main_sha != SOURCE_SHA:
        failures.append("OPEN_ROUND_REMOTE_MAIN_CHANGED")

    receipt = {
        "FINAL_LOCAL_SHA": local_sha,
        "FINAL_REMOTE_SHA": remote_branch_sha,
        "WORKTREE": str(repo),
        "WORKTREE_CLEAN": worktree_clean,
        "BRANCH": current_branch,
        "ROLLBACK_TAG": ROLLBACK_TAG,
        "ROLLBACK_TAG_TARGET": rollback_target,
        "MAIN_BEFORE_SHA": SOURCE_SHA,
        "MAIN_FAST_FORWARD_COMPLETED": main_fast_forward_completed,
        "MAIN_AFTER_SHA": remote_main_sha,
        "FORCE_PUSH_USED": gate_receipt.get("FORCE_PUSH_USED") is not False or logged_force_push,
        "MERGE_COMMIT_CREATED": merge_commit_count > 0,
        "HISTORY_REWRITTEN": not source_is_ancestor or gate_receipt.get("HISTORY_REWRITTEN") is not False or logged_history_rewrite,
    }
    document = {
        "schema_version": "trace-round16a-final-integration-evidence/v1",
        "status": "PASS" if not failures else "FAIL",
        "expected_closed": expected_closed,
        "receipt": receipt,
        "validation_failures": failures,
    }
    output.write_text(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": document["status"], "output": str(output), "validation_failure_count": len(failures)}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
