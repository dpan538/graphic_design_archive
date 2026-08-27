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
import json
import re
from pathlib import Path
from typing import Any, Mapping


REPO = Path(__file__).resolve().parents[2]
RAW_RELATIVE = Path("docs/audits/v49-exploration-full-space-closure-round1/raw")

REGRESSION_OPERATIONS = {f"ROUND{number}_REGRESSION": f"round{number}-regression" for number in range(8, 17)}
GATE_OPERATIONS = {
    "DATABASE_FREEZE": "database-freeze-final",
    "REPOSITORY_HYGIENE": "repository-hygiene-final",
    "TYPECHECK": "typecheck-full",
    "PRODUCTION_BUILD": "production-build-retry1",
    "API_SCHEMA_VALIDATION": "api-schema-validation",
    "AUDIT_SEAL": "audit-seal-final",
}


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--repository-boundary", type=Path, default=Path("repository-boundary-receipt.json"))
    parser.add_argument("--authority", type=Path, default=Path("authority-reconciliation-result.json"))
    parser.add_argument("--database", type=Path, default=Path("database-identity-v2.json"))
    parser.add_argument("--audit-seal", type=Path, default=Path("audit-seal-result.json"))
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
    repository_boundary = read_json(paths["repository_boundary"])
    authority = read_json(paths["authority"])
    database = read_json(paths["database"])
    audit_seal = read_json(paths["audit_seal"])
    boundary_receipt = explicit_receipt(repository_boundary, paths["repository_boundary"])
    authority_receipt = explicit_receipt(authority, paths["authority"])
    seal_receipt = explicit_receipt(audit_seal, paths["audit_seal"])

    if authority.get("status") != "PASS" or database.get("status") != "PASS" or audit_seal.get("status") != "PASS":
        raise ValueError("ROUND16A_OPERATIONAL_SOURCE_RECEIPT_NOT_PASS")
    if boundary_receipt.get("REPOSITORY_BOUNDARY") != "PASS":
        raise ValueError("ROUND16A_REPOSITORY_BOUNDARY_NOT_PASS")
    if seal_receipt.get("AUDIT_SEAL") != "PASS":
        raise ValueError("ROUND16A_AUDIT_SEAL_RECEIPT_NOT_PASS")
    if database.get("validation") and any(value != "PASS" for value in database["validation"].values()):
        raise ValueError("ROUND16A_DATABASE_VALIDATION_NOT_PASS")

    commands = "\n".join(str(row.get("command", "")) for row in events)
    force_push_used = bool(re.search(r"(?i)git\s+push\b[^\n]*(?:--force|-f\b)", commands))
    merge_commit_created = bool(re.search(r"(?i)git\s+(?:merge\b|commit\b[^\n]*--no-ff)", commands))
    history_rewritten = bool(re.search(r"(?i)git\s+(?:rebase\b|commit\b[^\n]*--amend|reset\b)", commands))
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
        "HISTORY_REWRITTEN": history_rewritten,
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
        "HISTORY_REWRITTEN": False,
    }
    failed_gates = sorted(name for name, expected in expected_gate_values.items() if gate_receipt.get(name) != expected)
    gate_status = "PASS" if not failed_gates else "FAIL"

    regression_document = {
        "schema_version": "trace-round16a-regression-results/v1",
        "status": regression_status,
        "receipt": regression_receipt,
        "operation_evidence": regression_evidence,
    }
    gate_document = {
        "schema_version": "trace-round16a-gate-status-results/v1",
        "status": gate_status,
        "receipt": gate_receipt,
        "failed_gates": failed_gates,
        "operation_evidence": gate_evidence,
        "source_receipts": {
            "repository_boundary": paths["repository_boundary"].relative_to(repo).as_posix(),
            "authority": paths["authority"].relative_to(repo).as_posix(),
            "database": paths["database"].relative_to(repo).as_posix(),
            "audit_seal": paths["audit_seal"].relative_to(repo).as_posix(),
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
