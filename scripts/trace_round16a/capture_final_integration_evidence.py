#!/usr/bin/env python3
"""Capture verified post-push Git fields for the final Round 16A receipt.

Run this only after the final research-branch push.  Round 16A is intentionally
left on its review branch; ``origin/main`` and the rollback tag must remain
unpublished/unchanged.  Write outside the repository (normally under ``/tmp``) so the
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


def ls_remote_ref(repo: Path, ref: str) -> str | None:
    output = git(repo, "ls-remote", "--refs", "origin", ref)
    rows = [line.split() for line in output.splitlines() if line.strip()]
    if not rows:
        return None
    if len(rows) != 1 or len(rows[0]) != 2 or rows[0][1] != ref:
        raise ValueError(f"ROUND16A_REMOTE_REF_AMBIGUOUS:{ref}:{rows}")
    return rows[0][0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument(
        "--integration-mode",
        choices=("review-branch",),
        help="Publish and verify only the research branch; leave origin/main unchanged.",
    )
    parser.add_argument(
        "--closed",
        choices=("true", "false"),
        help="Legacy main-integration expectation; use --integration-mode review-branch.",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    output = args.output.resolve()
    if output == repo or repo in output.parents:
        raise ValueError("ROUND16A_FINAL_INTEGRATION_OUTPUT_MUST_BE_OUTSIDE_REPOSITORY")
    if not output.parent.is_dir():
        raise FileNotFoundError(f"ROUND16A_FINAL_INTEGRATION_OUTPUT_PARENT_MISSING:{output.parent}")

    if args.integration_mode is None and args.closed is None:
        parser.error("one of --integration-mode or legacy --closed is required")
    if args.integration_mode is not None and args.closed is not None:
        parser.error("--integration-mode and --closed are mutually exclusive")
    expected_closed = args.closed == "true"
    integration_mode = args.integration_mode or "legacy-review-branch"
    local_sha = git(repo, "rev-parse", "HEAD")
    current_branch = git(repo, "branch", "--show-current")
    remote_branch_sha = ls_remote_ref(repo, f"refs/heads/{BRANCH}")
    remote_main_sha = ls_remote_ref(repo, "refs/heads/main")
    remote_rollback_tag_sha = ls_remote_ref(repo, f"refs/tags/{ROLLBACK_TAG}")
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
    logged_force_push = bool(re.search(
        r"(?i)git\s+push\b[^\n]*(?:--force(?:-with-lease|-if-includes)?|-f\b|--mirror\b|(?:^|\s)\+\S+)",
        event_commands,
    ))
    logged_unauthorized_history_rewrite = bool(
        re.search(
            r"(?i)git\s+(?:rebase\b|commit\b[^\n]*--amend|reset\b|lfs\s+migrate\b|"
            r"filter-repo\b|filter-branch\b|update-ref\b|branch\b[^\n]*(?:-f\b|--force\b)|"
            r"checkout\b[^\n]*-B\b|switch\b[^\n]*-C\b)",
            event_commands,
        )
    )

    failures: list[str] = []
    if current_branch != BRANCH:
        failures.append("BRANCH_MISMATCH")
    if local_sha != remote_branch_sha:
        failures.append("REMOTE_BRANCH_SHA_MISMATCH")
    if remote_rollback_tag_sha is not None:
        failures.append("ROLLBACK_TAG_WAS_PUSHED")
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
    expected_history_receipt = {
        "HISTORY_REWRITTEN": True,
        "UNPUBLISHED_ROUND16A_HISTORY_REWRITTEN": True,
        "PUBLIC_EXISTING_HISTORY_REWRITTEN": False,
        "ORIGIN_MAIN_REWRITTEN": False,
    }
    for key, expected in expected_history_receipt.items():
        if gate_receipt.get(key) is not expected:
            failures.append(f"{key}_GATE_MISMATCH")
    if logged_unauthorized_history_rewrite:
        failures.append("UNAUTHORIZED_HISTORY_REWRITE_COMMAND_DETECTED")
    main_fast_forward_completed = remote_main_sha == local_sha
    if expected_closed:
        failures.append("ROUND16A_REVIEW_BRANCH_MUST_REMAIN_OPEN")
    if main_fast_forward_completed:
        failures.append("ROUND16A_REVIEW_BRANCH_MAIN_WAS_FAST_FORWARDED")
    if remote_main_sha != SOURCE_SHA:
        failures.append("ROUND16A_REVIEW_BRANCH_MAIN_CHANGED")

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
        "HISTORY_REWRITTEN": True,
        "UNPUBLISHED_ROUND16A_HISTORY_REWRITTEN": True,
        "PUBLIC_EXISTING_HISTORY_REWRITTEN": False,
        "ORIGIN_MAIN_REWRITTEN": False,
    }
    document = {
        "schema_version": "trace-round16a-final-integration-evidence/v2",
        "status": "PASS" if not failures else "FAIL",
        "integration_mode": integration_mode,
        "main_integration_expected": False,
        "remote_rollback_tag_present": remote_rollback_tag_sha is not None,
        "receipt": receipt,
        "validation_failures": failures,
    }
    output.write_text(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": document["status"], "output": str(output), "validation_failure_count": len(failures)}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
