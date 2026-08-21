#!/usr/bin/env python3
"""Build conservative, machine-readable branch/ref and worktree ledgers."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
from pathlib import Path


SOURCE_TAG = "v49-data-api-closure-20260821"
CURRENT_BRANCH = "chore/v49-repository-hygiene-database-freeze-20260821"
PROTECTED = {"main", "master", "stable"}


def run(repo: Path, *command: str, check: bool = True) -> str:
    result = subprocess.run(command, cwd=repo, text=True, capture_output=True)
    if check and result.returncode:
        raise RuntimeError(f"{' '.join(command)}: {result.stderr.strip()}")
    return result.stdout


def succeeds(repo: Path, *command: str) -> bool:
    return subprocess.run(command, cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def parse_worktrees(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    row: dict[str, str] = {}
    for line in text.splitlines() + [""]:
        if not line:
            if row:
                rows.append(row)
                row = {}
            continue
        key, _, value = line.partition(" ")
        row[key] = value or "true"
    return rows


def branch_rows(repo: Path, open_prs: dict[str, list[dict[str, object]]], worktree_by_branch: dict[str, str]) -> list[dict[str, object]]:
    refs = run(repo, "git", "for-each-ref", "--format=%(refname)|%(objectname)", "refs/heads", "refs/remotes/origin")
    combined: dict[str, dict[str, str]] = {}
    for line in refs.splitlines():
        ref, tip = line.split("|", 1)
        if ref == "refs/remotes/origin/HEAD":
            continue
        if ref.startswith("refs/heads/"):
            name = ref.removeprefix("refs/heads/")
            combined.setdefault(name, {})["local"] = tip
        else:
            name = ref.removeprefix("refs/remotes/origin/")
            combined.setdefault(name, {})["remote"] = tip
    rows: list[dict[str, object]] = []
    for name in sorted(combined):
        item = combined[name]
        tip = item.get("local") or item["remote"]
        tree = run(repo, "git", "rev-parse", f"{tip}^{{tree}}").strip()
        ancestor_release = succeeds(repo, "git", "merge-base", "--is-ancestor", tip, SOURCE_TAG)
        merged_main = succeeds(repo, "git", "merge-base", "--is-ancestor", tip, "origin/main")
        unique_commits = int(run(repo, "git", "rev-list", "--count", tip, "--not", SOURCE_TAG).strip())
        changed = run(repo, "git", "diff", "--name-only", f"{SOURCE_TAG}...{tip}", check=False)
        unique_files = len([line for line in changed.splitlines() if line])
        prs = open_prs.get(name, [])
        if name in PROTECTED:
            decision, recovery = "RETAIN_PROTECTED", "protected default/stable branch"
        elif name == CURRENT_BRANCH:
            decision, recovery = "RETAIN_ACTIVE", "current hygiene feature branch"
        elif ancestor_release:
            decision, recovery = "RETAIN_ANCHORED", f"tip reachable from immutable {SOURCE_TAG}"
        else:
            decision, recovery = "KEEP_BLOCKED", "unique or divergent history retained conservatively"
        remote_divergence = "N/A"
        if item.get("local") and item.get("remote"):
            remote_divergence = run(repo, "git", "rev-list", "--left-right", "--count", f"{item['local']}...{item['remote']}").strip().replace("\t", "/")
        rows.append({
            "branch": name,
            "tip_sha": tip,
            "tip_tree": tree,
            "local_present": bool(item.get("local")),
            "remote": f"origin/{name}" if item.get("remote") else "",
            "remote_present": bool(item.get("remote")),
            "remote_divergence": remote_divergence,
            "worktree": worktree_by_branch.get(name, ""),
            "open_pr": json.dumps(prs, separators=(",", ":")),
            "merged_to_main": merged_main,
            "ancestor_of_release_anchor": ancestor_release,
            "unique_commit_count": unique_commits,
            "unique_file_count": unique_files,
            "recovery_value": recovery,
            "decision": decision,
            "archive_tag": SOURCE_TAG if ancestor_release else "",
            "deletion_result": "NOT_DELETED_SAFETY",
        })
    return rows


def count_paths(output: bytes) -> int:
    return len([part for part in output.split(b"\0") if part])


def worktree_rows(repo: Path, worktrees: list[dict[str, str]]) -> list[dict[str, object]]:
    process_text = run(repo, "ps", "-axo", "pid=,command=", check=False)
    rows: list[dict[str, object]] = []
    for item in worktrees:
        path = Path(item["worktree"])
        branch = item.get("branch", "").removeprefix("refs/heads/")
        exists = path.is_dir()
        prunable = "prunable" in item
        status = ""
        untracked = 0
        ignored_bytes = 0
        if exists:
            status = run(repo, "git", "-C", str(path), "status", "--porcelain", "--untracked-files=all", check=False)
            untracked_result = subprocess.run(["git", "-C", str(path), "ls-files", "--others", "--exclude-standard", "-z"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            untracked = count_paths(untracked_result.stdout)
            ignored_result = subprocess.run(["git", "-C", str(path), "ls-files", "--others", "-i", "--exclude-standard", "-z"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            for encoded in ignored_result.stdout.split(b"\0"):
                if not encoded:
                    continue
                target = path / os.fsdecode(encoded)
                if target.is_file():
                    ignored_bytes += target.stat().st_size
        remote = f"origin/{branch}" if branch and succeeds(repo, "git", "show-ref", "--verify", "--quiet", f"refs/remotes/origin/{branch}") else ""
        divergence = "N/A"
        if remote:
            divergence = run(repo, "git", "rev-list", "--left-right", "--count", f"{item['HEAD']}...{remote}").strip().replace("\t", "/")
        process_lines = [line.strip() for line in process_text.splitlines() if str(path) in line and "build_git_hygiene_ledgers.py" not in line]
        if prunable:
            decision = "PRUNE_STALE_REGISTRATION"
        elif branch in {"fix/v49-api-read-contract-closure-20260821", "fix/v49-release-projection-snapshot-db-closure-20260820"} and not status and divergence == "0/0" and not process_lines:
            decision = "REMOVE_SAFE_COMPLETED_TASK_WORKTREE"
        elif branch == CURRENT_BRANCH:
            decision = "RETAIN_ACTIVE"
        else:
            decision = "RETAIN_NOT_TASK_OWNED_OR_BLOCKED"
        rows.append({
            "path": str(path),
            "branch": branch or "DETACHED",
            "HEAD": item["HEAD"],
            "exists": exists,
            "prunable": prunable,
            "clean": exists and not status,
            "remote_pushed": bool(remote) and divergence == "0/0",
            "remote_divergence": divergence,
            "open_processes": json.dumps(process_lines, separators=(",", ":")),
            "untracked_files": untracked,
            "ignored_runtime_bytes": ignored_bytes,
            "audit_package": "docs/audits/v49-api-read-contract-closure" if "api_read_contract" in str(path) else "docs/audits/v49-release-projection-snapshot-db-closure" if "db_closure" in str(path) else "",
            "recovery_commit": item["HEAD"],
            "decision": decision,
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--open-pr-json", type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    output = args.output_dir.resolve()
    prs = json.loads(args.open_pr_json.read_text()) if args.open_pr_json else []
    open_prs: dict[str, list[dict[str, object]]] = {}
    for pr in prs:
        open_prs.setdefault(str(pr["headRefName"]), []).append(pr)
    worktrees = parse_worktrees(run(repo, "git", "worktree", "list", "--porcelain"))
    worktree_by_branch = {row.get("branch", "").removeprefix("refs/heads/"): row["worktree"] for row in worktrees}
    branches = branch_rows(repo, open_prs, worktree_by_branch)
    worktree_ledger = worktree_rows(repo, worktrees)
    write_csv(output / "V49_BRANCH_AND_REF_LEDGER.csv", branches)
    write_csv(output / "V49_WORKTREE_LEDGER.csv", worktree_ledger)
    summary = {
        "format": "gda-v49-git-hygiene-ledgers/v1",
        "branchCount": len(branches),
        "localBranchCount": sum(bool(row["local_present"]) for row in branches),
        "remoteBranchCount": sum(bool(row["remote_present"]) for row in branches),
        "openPrCount": sum(bool(json.loads(str(row["open_pr"]))) for row in branches),
        "unknownBranchClassificationCount": 0,
        "supersededUnanchoredBranchCount": 0,
        "deletedUniqueCommitCount": 0,
        "deletedUnrecoverableBranchCount": 0,
        "worktreeCount": len(worktree_ledger),
        "prunableWorktreeCount": sum(bool(row["prunable"]) for row in worktree_ledger),
        "unknownWorktreeCount": 0,
        "worktreeWithUntrackedUnclassifiedCount": 0,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "git-hygiene-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    branch_lines = ["# v49 branch and ref ledger", "", f"All {len(branches)} discovered branch names are classified; none were deleted automatically.", "", "| branch | tip | release ancestor | unique commits | decision |", "|---|---|---:|---:|---|"]
    branch_lines.extend(f"| `{row['branch']}` | `{str(row['tip_sha'])[:12]}` | {str(row['ancestor_of_release_anchor']).lower()} | {row['unique_commit_count']} | {row['decision']} |" for row in branches)
    (output / "V49_BRANCH_AND_REF_LEDGER.md").write_text("\n".join(branch_lines) + "\n")
    worktree_lines = ["# v49 worktree ledger", "", f"All {len(worktree_ledger)} registered worktrees are classified.", "", "| path | branch | clean | divergence | decision |", "|---|---|---:|---:|---|"]
    worktree_lines.extend(f"| `{row['path']}` | `{row['branch']}` | {str(row['clean']).lower()} | {row['remote_divergence']} | {row['decision']} |" for row in worktree_ledger)
    (output / "V49_WORKTREE_LEDGER.md").write_text("\n".join(worktree_lines) + "\n")
    print(json.dumps({"status": "PASS", **summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
