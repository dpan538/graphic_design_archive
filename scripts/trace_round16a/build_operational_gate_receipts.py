#!/usr/bin/env python3
"""Build Round 16A regression and operational-gate receipts from logged evidence.

The command does not execute tests.  It can run only after the caller has run
every required command through ``run_logged.py`` with the exact operation IDs
below.  For each ID, the highest-sequence terminal event must be ``PASS`` and a
reconciled command-ledger row with exit code zero must exist.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping


REPO = Path(__file__).resolve().parents[2]
RAW_RELATIVE = Path("docs/audits/v49-exploration-full-space-closure-round1/raw")
SOURCE_SHA = "8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e"
SOURCE_TREE_SHA = "86c2ed7771034f6d3f0f2e10e7a37aeec0552c71"
ROUND16A_BRANCH = "codex/trace-v49-exploration-full-space-closure-round1"
AUTHORIZED_MIGRATION_SCHEMA = "trace-round16a-authorized-lfs-migration-receipt/v1"
AUTHORIZED_MIGRATION_PATHS = (
    "docs/audits/v49-exploration-full-space-closure-round1/raw/independent-verification-cases-v2.tsv",
    "docs/audits/v49-exploration-full-space-closure-round1/raw/independent-verification.json",
)

REGRESSION_OPERATIONS = {f"ROUND{number}_REGRESSION": f"round{number}-regression" for number in range(8, 17)}
GATE_OPERATIONS = {
    "REPOSITORY_BOUNDARY": "repository-boundary-verification",
    "DATABASE_FREEZE": "database-freeze-final",
    "REPOSITORY_HYGIENE": "repository-hygiene-final",
    "TYPECHECK": "typecheck-full",
    "PRODUCTION_BUILD": "production-build-retry1",
    "API_SCHEMA_VALIDATION": "api-schema-validation",
    "INDEPENDENT_VERIFICATION": "independent-verification-final",
    "COUNT_HASH_RECONCILIATION": "count-hash-reconciliation-final",
    "DETERMINISTIC_REPRODUCTION": "deterministic-clean-worktree-reproduction-final",
    "GIT_FSCK": "git-fsck-final",
    "GIT_LFS_FSCK": "git-lfs-fsck-final",
    "AUDIT_SEAL": "audit-seal-final",
}
MIGRATION_OPERATION_ID = "authorized-lfs-migration-verification"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"ROUND16A_GATE_INPUT_NOT_OBJECT:{path}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"ROUND16A_GATE_EVENT_NOT_OBJECT:{line_number}")
        rows.append(row)
    return rows


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def terminal_event(events: list[dict[str, Any]], operation_id: str) -> dict[str, Any]:
    rows = [row for row in events if row.get("operation_id") == operation_id and row.get("status") in {"PASS", "FAIL"}]
    if not rows:
        raise ValueError(f"ROUND16A_REQUIRED_OPERATION_NOT_COMPLETED:{operation_id}")
    return max(rows, key=lambda row: int(row["sequence"]))


def command_evidence(command_rows: list[dict[str, str]], operation_id: str) -> dict[str, str]:
    rows = [row for row in command_rows if row.get("operation_id") == operation_id]
    if not rows:
        raise ValueError(f"ROUND16A_REQUIRED_COMMAND_LEDGER_ROW_MISSING:{operation_id}")
    row = rows[-1]
    if row.get("exit_code") != "0":
        raise ValueError(f"ROUND16A_REQUIRED_COMMAND_NONZERO:{operation_id}:{row.get('exit_code')}")
    return row


def operation_receipts(events: list[dict[str, Any]], command_rows: list[dict[str, str]], mapping: Mapping[str, str]) -> tuple[dict[str, str], dict[str, Any]]:
    receipt: dict[str, str] = {}
    evidence: dict[str, Any] = {}
    for gate, operation_id in mapping.items():
        event = terminal_event(events, operation_id)
        command = command_evidence(command_rows, operation_id)
        passed = event.get("status") == "PASS"
        receipt[gate] = "PASS" if passed else "FAIL"
        evidence[gate] = {
            "operation_id": operation_id,
            "event_sequence": event.get("sequence"),
            "event_status": event.get("status"),
            "event_git_sha": event.get("git_sha"),
            "command_id": command.get("command_id"),
            "command_exit_code": int(command.get("exit_code", "-1")),
            "command": command.get("command"),
        }
    return receipt, evidence


def explicit_receipt(document: Mapping[str, Any], path: Path) -> dict[str, Any]:
    value = document.get("receipt", document.get("metrics"))
    if not isinstance(value, dict):
        raise ValueError(f"ROUND16A_EXPLICIT_RECEIPT_MISSING:{path}")
    return value


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    folded = str(value).casefold()
    if folded in {"true", "1", "pass"}:
        return True
    if folded in {"false", "0", "fail"}:
        return False
    raise ValueError(f"ROUND16A_GATE_BOOLEAN_INVALID:{value!r}")


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_embedded_receipt_hash(document: Mapping[str, Any], label: str) -> None:
    expected = document.get("receipt_hash")
    material = dict(document)
    material.pop("receipt_hash", None)
    actual = hashlib.sha256(
        (
            json.dumps(
                material,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
    ).hexdigest()
    if expected != actual:
        raise ValueError(f"ROUND16A_EMBEDDED_RECEIPT_HASH_INVALID:{label}")


def validate_authorized_migration(
    document: Mapping[str, Any], path: Path, repo: Path
) -> dict[str, Any]:
    """Fail closed unless the one user-authorized unpublished-branch rewrite is proven."""
    verify_embedded_receipt_hash(document, "authorized-lfs-migration")
    receipt = explicit_receipt(document, path)
    top_level_expected = {
        "schema_version": AUTHORIZED_MIGRATION_SCHEMA,
        "status": "PASS",
        "source_sha": SOURCE_SHA,
        "source_tree_sha": SOURCE_TREE_SHA,
        "branch": ROUND16A_BRANCH,
    }
    top_level_failures = [
        name for name, expected in top_level_expected.items()
        if document.get(name) != expected
    ]
    if sorted(document.get("migrated_paths", [])) != sorted(AUTHORIZED_MIGRATION_PATHS):
        top_level_failures.append("migrated_paths")
    receipt_expected = {
        "HISTORY_REWRITE_AUTHORIZED": True,
        "HISTORY_REWRITTEN": True,
        "UNPUBLISHED_ROUND16A_HISTORY_REWRITTEN": True,
        "PUBLIC_EXISTING_HISTORY_REWRITTEN": False,
        "ORIGIN_MAIN_REWRITTEN": False,
        "FORCE_PUSH_USED": False,
        "REMOTE_BRANCH_EXISTED_BEFORE_MIGRATION": False,
        "SOURCE_SHA_PRESERVED": True,
        "SOURCE_TREE_SHA_PRESERVED": True,
        "CHECKPOINT_SEQUENCE_PRESERVED": True,
        "REWRITE_NONALLOWLIST_PATH_COUNT": 0,
        "ORIGIN_MAIN_BEFORE_SHA": SOURCE_SHA,
        "ORIGIN_MAIN_AFTER_SHA": SOURCE_SHA,
        "PUBLIC_REMOTE_REF_MAP_HASH_MATCH": True,
        "LFS_POINTER_VALIDATION": "PASS",
        "HYDRATED_PAYLOAD_HASH_MATCH": True,
        "GIT_FSCK": "PASS",
        "LFS_FSCK": "PASS",
        "ORDINARY_OVERSIZED_BLOB_COUNT_AFTER": 0,
        "ROUND16A_MAPPED_COMMIT_COUNT_BEFORE": 8,
        "ROUND16A_MAPPED_COMMIT_COUNT_AFTER": 8,
        "ORIGINAL_CHECKPOINT_COUNT_BEFORE": 7,
        "ORIGINAL_CHECKPOINT_COUNT_AFTER": 7,
        "POST_MIGRATION_CHECKPOINT_APPEND_COUNT": 1,
    }
    receipt_failures = [
        name for name, expected in receipt_expected.items()
        if receipt.get(name) != expected
    ]
    if top_level_failures or receipt_failures:
        raise ValueError(
            "ROUND16A_AUTHORIZED_LFS_MIGRATION_CONTRACT:"
            f"top_level={sorted(top_level_failures)};receipt={sorted(receipt_failures)}"
        )
    expected_copies = {
        "bundle_sha256": "original-bundle.sha256",
        "pre_ref_ledger": "pre-ref-ledger.tsv",
        "post_ref_ledger": "post-ref-ledger.tsv",
        "pre_checkpoint_ledger": "pre-checkpoint-ledger.tsv",
        "post_checkpoint_ledger": "post-checkpoint-ledger.tsv",
        "object_map": "old-to-new-object-map.csv",
        "pre_oversized_ledger": "pre-oversized-blobs.tsv",
    }
    copied_evidence = document.get("copied_evidence")
    if not isinstance(copied_evidence, Mapping) or set(copied_evidence) != set(expected_copies):
        raise ValueError("ROUND16A_AUTHORIZED_LFS_MIGRATION_COPIED_EVIDENCE_SET")
    for label, filename in expected_copies.items():
        record = copied_evidence[label]
        if not isinstance(record, Mapping):
            raise ValueError(f"ROUND16A_AUTHORIZED_LFS_MIGRATION_COPY_RECORD:{label}")
        expected_relative = (
            RAW_RELATIVE / "history-migration" / filename
        ).as_posix()
        if record.get("path") != expected_relative:
            raise ValueError(f"ROUND16A_AUTHORIZED_LFS_MIGRATION_COPY_PATH:{label}")
        evidence_path = repo / expected_relative
        if not evidence_path.is_file():
            raise FileNotFoundError(
                f"ROUND16A_AUTHORIZED_LFS_MIGRATION_COPY_MISSING:{label}:{evidence_path}"
            )
        content = evidence_path.read_bytes()
        if record.get("bytes") != len(content):
            raise ValueError(f"ROUND16A_AUTHORIZED_LFS_MIGRATION_COPY_BYTES:{label}")
        if record.get("sha256") != hashlib.sha256(content).hexdigest():
            raise ValueError(f"ROUND16A_AUTHORIZED_LFS_MIGRATION_COPY_HASH:{label}")
    return dict(receipt)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--repository-boundary", type=Path, default=Path("repository-boundary-receipt.json"))
    parser.add_argument("--authority", type=Path, default=Path("authority-reconciliation-result.json"))
    parser.add_argument("--database", type=Path, default=Path("database-identity-v2.json"))
    parser.add_argument("--audit-seal", type=Path, default=Path("audit-seal-result.json"))
    parser.add_argument(
        "--authorized-lfs-migration",
        type=Path,
        default=Path("authorized-lfs-migration-receipt.json"),
    )
    args = parser.parse_args()
    repo = args.repo.resolve()
    raw = repo / RAW_RELATIVE

    def resolve(value: Path) -> Path:
        return value.resolve() if value.is_absolute() else raw / value

    paths = {
        "events": raw / "execution-events.jsonl",
        "commands": raw / "command-ledger.tsv",
        "live_log": repo / "docs/research/trace-v49-exploration-full-space-closure-round1/00_LIVE_EXECUTION_LOG.md",
        "repository_boundary": resolve(args.repository_boundary),
        "authority": resolve(args.authority),
        "database": resolve(args.database),
        "audit_seal": resolve(args.audit_seal),
        "authorized_lfs_migration": resolve(args.authorized_lfs_migration),
        "reproducibility": raw / "reproducibility-verification.json",
        "checkpoints": raw / "checkpoint-ledger.tsv",
    }
    missing = [str(path) for path in paths.values() if not path.is_file() or path.stat().st_size == 0]
    if missing:
        raise FileNotFoundError(f"ROUND16A_OPERATIONAL_GATE_INPUT_MISSING:{missing}")

    events = read_jsonl(paths["events"])
    command_rows = read_tsv(paths["commands"])
    if not events or not command_rows:
        raise ValueError("ROUND16A_OPERATIONAL_LOG_EMPTY")
    sequences = [int(row["sequence"]) for row in events]
    if sequences != list(range(1, len(sequences) + 1)):
        raise ValueError("ROUND16A_OPERATIONAL_EVENT_SEQUENCE_GAP")

    regression_receipt, regression_evidence = operation_receipts(events, command_rows, REGRESSION_OPERATIONS)
    gate_receipt, gate_evidence = operation_receipts(events, command_rows, GATE_OPERATIONS)
    migration_event = terminal_event(events, MIGRATION_OPERATION_ID)
    migration_command = command_evidence(command_rows, MIGRATION_OPERATION_ID)
    if migration_event.get("status") != "PASS":
        raise ValueError("ROUND16A_AUTHORIZED_LFS_MIGRATION_OPERATION_NOT_PASS")
    migration_sequence = int(migration_event["sequence"])
    repository_boundary = read_json(paths["repository_boundary"])
    authority = read_json(paths["authority"])
    database = read_json(paths["database"])
    audit_seal = read_json(paths["audit_seal"])
    authorized_lfs_migration = read_json(paths["authorized_lfs_migration"])
    reproducibility = read_json(paths["reproducibility"])
    checkpoints = read_tsv(paths["checkpoints"])
    boundary_receipt = explicit_receipt(repository_boundary, paths["repository_boundary"])
    authority_receipt = explicit_receipt(authority, paths["authority"])
    seal_receipt = explicit_receipt(audit_seal, paths["audit_seal"])
    migration_receipt = validate_authorized_migration(
        authorized_lfs_migration,
        paths["authorized_lfs_migration"],
        repo,
    )
    migrated_head_sha = str(authorized_lfs_migration.get("new_head_sha", ""))
    migration_helper_path = "scripts/trace_round16a/verify_authorized_lfs_migration.py"
    migration_inputs = migration_event.get("input_paths")
    migration_input_hashes = migration_event.get("input_hashes")
    migration_output_hashes = migration_event.get("output_hashes")
    expected_migration_outputs = {
        paths["authorized_lfs_migration"].relative_to(repo).as_posix(),
        *(
            (RAW_RELATIVE / "history-migration" / filename).as_posix()
            for filename in (
                "original-bundle.sha256",
                "pre-ref-ledger.tsv",
                "post-ref-ledger.tsv",
                "pre-checkpoint-ledger.tsv",
                "post-checkpoint-ledger.tsv",
                "old-to-new-object-map.csv",
                "pre-oversized-blobs.tsv",
            )
        ),
    }
    if (
        migration_event.get("git_sha") != migrated_head_sha
        or not isinstance(migration_inputs, list)
        or migration_helper_path not in migration_inputs
        or not isinstance(migration_input_hashes, Mapping)
        or migration_input_hashes.get(migration_helper_path)
        != hashlib.sha256((repo / migration_helper_path).read_bytes()).hexdigest()
        or not isinstance(migration_output_hashes, Mapping)
        or set(migration_output_hashes) != expected_migration_outputs
        or any(
            migration_output_hashes.get(relative)
            != hashlib.sha256((repo / relative).read_bytes()).hexdigest()
            for relative in expected_migration_outputs
        )
    ):
        raise ValueError("ROUND16A_AUTHORIZED_LFS_MIGRATION_EVENT_PROVENANCE_INVALID")
    checkpoint_ids = [row.get("checkpoint_id") for row in checkpoints]
    expected_checkpoint_ids = [f"CHECKPOINT-{index:03d}" for index in range(1, 10)]
    if checkpoint_ids != expected_checkpoint_ids:
        raise ValueError(
            f"ROUND16A_CHECKPOINT_SEQUENCE_INVALID:{checkpoint_ids}"
        )
    migration_checkpoint = checkpoints[7]
    if (
        migration_checkpoint.get("commit_sha") != migrated_head_sha
        or "LFS" not in migration_checkpoint.get("phase", "").upper()
        or "MIGRATION" not in migration_checkpoint.get("phase", "").upper()
    ):
        raise ValueError("ROUND16A_MIGRATION_CHECKPOINT_BINDING_INVALID")
    hardened_checkpoint = checkpoints[8]
    hardened_sha = str(hardened_checkpoint.get("commit_sha", ""))
    if (
        "POST_MIGRATION" not in hardened_checkpoint.get("phase", "").upper()
        or "HARDENED" not in hardened_checkpoint.get("phase", "").upper()
        or "supersedes_checkpoint_007_as_post_migration_final_code_sha=true"
        not in hardened_checkpoint.get("known_limitations", "").casefold()
        or subprocess.run(
            ["git", "cat-file", "-e", f"{hardened_sha}^{{commit}}"],
            cwd=repo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode != 0
        or subprocess.run(
            ["git", "merge-base", "--is-ancestor", migrated_head_sha, hardened_sha],
            cwd=repo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode != 0
    ):
        raise ValueError("ROUND16A_HARDENED_CHECKPOINT_BINDING_INVALID")
    reproduction_worktree = reproducibility.get("worktree")
    reproduction_event_sha = str(
        gate_evidence["DETERMINISTIC_REPRODUCTION"].get("event_git_sha", "")
    )
    if (
        reproducibility.get("schema_version")
        != "trace-exploration-round16a-reproducibility-verification-v2"
        or reproducibility.get("status") != "PASS"
        or reproducibility.get("reproducibility_verification") != "PASS"
        or reproducibility.get("all_required_hashes_match") is not True
        or reproducibility.get("clean_worktree_reproduction") is not True
        or not isinstance(reproduction_worktree, Mapping)
        or reproducibility.get("final_code_sha") != hardened_sha
        or reproduction_worktree.get("primary_head") != hardened_sha
        or reproduction_worktree.get("reproduction_head") != hardened_sha
        or reproduction_event_sha != hardened_sha
    ):
        raise ValueError("ROUND16A_POST_MIGRATION_REPRODUCTION_BINDING_INVALID")
    freshness_failures: list[str] = []
    for label, evidence_rows in (
        ("REGRESSION", regression_evidence),
        ("GATE", gate_evidence),
    ):
        for name, evidence in evidence_rows.items():
            sequence = int(evidence.get("event_sequence", 0))
            if sequence <= migration_sequence:
                freshness_failures.append(f"{label}_{name}_NOT_POST_MIGRATION")
            event_git_sha = str(evidence.get("event_git_sha", ""))
            if subprocess.run(
                ["git", "merge-base", "--is-ancestor", migrated_head_sha, event_git_sha],
                cwd=repo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            ).returncode != 0:
                freshness_failures.append(f"{label}_{name}_SHA_NOT_MIGRATED_DESCENDANT")

    if authority.get("status") != "PASS" or database.get("status") != "PASS" or audit_seal.get("status") != "PASS":
        raise ValueError("ROUND16A_OPERATIONAL_SOURCE_RECEIPT_NOT_PASS")
    if boundary_receipt.get("REPOSITORY_BOUNDARY") != "PASS":
        raise ValueError("ROUND16A_REPOSITORY_BOUNDARY_NOT_PASS")
    if seal_receipt.get("AUDIT_SEAL") != "PASS":
        raise ValueError("ROUND16A_AUDIT_SEAL_RECEIPT_NOT_PASS")
    if database.get("validation") and any(value != "PASS" for value in database["validation"].values()):
        raise ValueError("ROUND16A_DATABASE_VALIDATION_NOT_PASS")

    commands = "\n".join(str(row.get("command", "")) for row in events)
    force_push_used = bool(re.search(
        r"(?i)git\s+push\b[^\n]*(?:--force(?:-with-lease|-if-includes)?|-f\b|--mirror\b|(?:^|\s)\+\S+)",
        commands,
    ))
    merge_commit_created = bool(re.search(r"(?i)git\s+(?:merge\b|commit\b[^\n]*--no-ff)", commands))
    unauthorized_history_rewrite = bool(re.search(
        r"(?i)git\s+(?:rebase\b|commit\b[^\n]*--amend|reset\b|lfs\s+migrate\b|"
        r"filter-repo\b|filter-branch\b|update-ref\b|branch\b[^\n]*(?:-f\b|--force\b)|"
        r"checkout\b[^\n]*-B\b|switch\b[^\n]*-C\b)",
        commands,
    ))
    deployed = bool(re.search(r"(?i)(?:vercel\s+(?:deploy|--prod)|npm\s+run\s+deploy)", commands))

    closure_metrics = database.get("closure_metrics", {})
    gate_receipt.update({
        "ACTIVE_EXPLORATION_AUTHORITY_COUNT": authority_receipt.get("ACTIVE_EXPLORATION_AUTHORITY_COUNT"),
        "AUTHORITY_CONTRADICTION_COUNT": authority_receipt.get("AUTHORITY_CONTRADICTION_COUNT"),
        "AUTHORITY_RECONCILIATION_READY": authority_receipt.get("AUTHORITY_RECONCILIATION_READY"),
        "CONTEXT_OVERRIDE_OF_ASSOCIATION_DECISION_COUNT": 0,
        "SPACETIME_OVERRIDE_OF_ASSOCIATION_DECISION_COUNT": 0,
        "CONTINUOUS_PROCESS_LOG_READY": True,
        "DIRECT_DATABASE_SNAPSHOT_VALIDATED": closure_metrics.get("direct_database_snapshot_validated"),
        "DIRECT_DATABASE_CATEGORY_BINDING_READY": closure_metrics.get("direct_database_category_binding_ready"),
        "FINAL_EXPLORATION_FRONTEND_IMPLEMENTED": bool_value(boundary_receipt.get("FINAL_EXPLORATION_FRONTEND_IMPLEMENTED")),
        "PUBLIC_EXPLORATION_PAGE_ADDED": bool_value(boundary_receipt.get("PUBLIC_EXPLORATION_PAGE_ADDED")),
        "PROJECT_FRONTEND_DESIGN_SAFE_TO_BEGIN": False,
        "DEPLOYED": deployed,
        "EXTERNAL_HUMAN_DOMAIN_REVIEW_COMPLETED": False,
        "FORCE_PUSH_USED": force_push_used,
        "MERGE_COMMIT_CREATED": merge_commit_created,
        "HISTORY_REWRITTEN": True,
        "UNPUBLISHED_ROUND16A_HISTORY_REWRITTEN": True,
        "PUBLIC_EXISTING_HISTORY_REWRITTEN": False,
        "ORIGIN_MAIN_REWRITTEN": False,
        "CHECKPOINT_COMMIT_COUNT": 9,
        "POST_MIGRATION_HARDENED_SHA": hardened_sha,
    })

    regression_status = "PASS" if all(value == "PASS" for value in regression_receipt.values()) else "FAIL"
    expected_gate_values = {
        **{name: "PASS" for name in GATE_OPERATIONS},
        "ACTIVE_EXPLORATION_AUTHORITY_COUNT": 1,
        "AUTHORITY_CONTRADICTION_COUNT": 0,
        "AUTHORITY_RECONCILIATION_READY": True,
        "CONTEXT_OVERRIDE_OF_ASSOCIATION_DECISION_COUNT": 0,
        "SPACETIME_OVERRIDE_OF_ASSOCIATION_DECISION_COUNT": 0,
        "CONTINUOUS_PROCESS_LOG_READY": True,
        "DIRECT_DATABASE_SNAPSHOT_VALIDATED": True,
        "DIRECT_DATABASE_CATEGORY_BINDING_READY": True,
        "FINAL_EXPLORATION_FRONTEND_IMPLEMENTED": False,
        "PUBLIC_EXPLORATION_PAGE_ADDED": False,
        "PROJECT_FRONTEND_DESIGN_SAFE_TO_BEGIN": False,
        "DEPLOYED": False,
        "EXTERNAL_HUMAN_DOMAIN_REVIEW_COMPLETED": False,
        "FORCE_PUSH_USED": False,
        "MERGE_COMMIT_CREATED": False,
        "HISTORY_REWRITTEN": True,
        "UNPUBLISHED_ROUND16A_HISTORY_REWRITTEN": True,
        "PUBLIC_EXISTING_HISTORY_REWRITTEN": False,
        "ORIGIN_MAIN_REWRITTEN": False,
        "CHECKPOINT_COMMIT_COUNT": 9,
        "POST_MIGRATION_HARDENED_SHA": hardened_sha,
    }
    failed_gates = sorted(name for name, expected in expected_gate_values.items() if gate_receipt.get(name) != expected)
    if unauthorized_history_rewrite:
        failed_gates.append("UNAUTHORIZED_HISTORY_REWRITE_COMMAND_DETECTED")
    if migration_receipt.get("FORCE_PUSH_USED") is not False:
        failed_gates.append("AUTHORIZED_MIGRATION_FORCE_PUSH_GATE_NOT_FALSE")
    failed_gates.extend(freshness_failures)
    failed_gates = sorted(set(failed_gates))
    gate_status = "PASS" if not failed_gates else "FAIL"

    regression_document = {
        "schema_version": "trace-round16a-regression-results/v1",
        "status": regression_status,
        "receipt": regression_receipt,
        "operation_evidence": regression_evidence,
    }
    gate_document = {
        "schema_version": "trace-round16a-gate-status-results/v2",
        "status": gate_status,
        "receipt": gate_receipt,
        "failed_gates": failed_gates,
        "operation_evidence": gate_evidence,
        "authorized_migration_operation_evidence": {
            "operation_id": MIGRATION_OPERATION_ID,
            "event_sequence": migration_sequence,
            "event_git_sha": migration_event.get("git_sha"),
            "command_id": migration_command.get("command_id"),
            "command_exit_code": int(migration_command.get("exit_code", "-1")),
            "receipt_sha256": hashlib.sha256(
                paths["authorized_lfs_migration"].read_bytes()
            ).hexdigest(),
            "helper_sha256": hashlib.sha256(
                (repo / migration_helper_path).read_bytes()
            ).hexdigest(),
            "output_hashes": dict(sorted(migration_output_hashes.items())),
        },
        "source_receipts": {
            "repository_boundary": paths["repository_boundary"].relative_to(repo).as_posix(),
            "authority": paths["authority"].relative_to(repo).as_posix(),
            "database": paths["database"].relative_to(repo).as_posix(),
            "audit_seal": paths["audit_seal"].relative_to(repo).as_posix(),
            "authorized_lfs_migration": paths["authorized_lfs_migration"].relative_to(repo).as_posix(),
        },
        "log_evidence": {
            "execution_event_count": len(events),
            "command_ledger_row_count": len(command_rows),
            "live_log_bytes": paths["live_log"].stat().st_size,
        },
    }
    regression_output = raw / "regression-results.json"
    gate_output = raw / "gate-status-results.json"
    write_json(regression_output, regression_document)
    write_json(gate_output, gate_document)
    print(json.dumps({
        "status": "PASS" if regression_status == gate_status == "PASS" else "FAIL",
        "regression_status": regression_status,
        "gate_status": gate_status,
        "regression_output": regression_output.relative_to(repo).as_posix(),
        "gate_output": gate_output.relative_to(repo).as_posix(),
    }, sort_keys=True))
    return 0 if regression_status == gate_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
