#!/usr/bin/env python3
"""Aggregate PostgreSQL log_statement_stats for one importer backend PID."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


USAGE_RE = re.compile(
    r"!\s+([0-9.]+) s user, ([0-9.]+) s system, ([0-9.]+) s elapsed"
)
RSS_RE = re.compile(r"!\s+([0-9]+) kB max resident size")
BLOCK_RE = re.compile(r"!\s+([0-9]+)/([0-9]+) \[[0-9]+/[0-9]+\] filesystem blocks in/out")
LOG_HEADER_RE = re.compile(r"^\d{4}-\d{2}-\d{2} .* \[(\d+)\] LOG:")


class ParseError(RuntimeError):
    pass


def category(statement: str) -> tuple[str, str | None]:
    normalized = " ".join(statement.split())
    if normalized.startswith("COPY gda_stage_"):
        return "COPY", None
    if normalized.startswith("INSERT INTO "):
        return "DURABLE_INSERTS", None
    if "DO $parity$" in normalized:
        return "PARITY", None
    if normalized.startswith("ANALYZE "):
        return "TARGETED_ANALYZE", None
    if normalized == "SET CONSTRAINTS ALL DEFERRED;":
        return "OTHER", None
    if normalized.startswith("SET CONSTRAINTS"):
        groups = (
            ("final_all_omission_check", "SET CONSTRAINTS ALL IMMEDIATE"),
            ("raw_core_cycle", "migration_batch_authority_exact"),
            ("folder_assignment_shape", "assignment_shape_from_assignment"),
            ("visual_bridge_and_locator", "object_visual_reference_decision_from_bridge"),
            ("rights_observation", "rights_observation_shape_from_parent"),
            ("rights_assessment_shape_support", "rights_assessment_from_assessment"),
            ("rights_assessment_current_leaf", "rights_assessment_one_current_leaf"),
            ("provider_policy", "provider_policy_evaluation_from_parent"),
            ("delivery_parent_validation", "delivery_assessment_validation"),
            ("delivery_rights_validation", "delivery_rights_validation"),
            ("delivery_policy_validation", "delivery_policy_validation"),
            ("delivery_history_and_rule", "delivery_supersession_parent"),
        )
        for name, marker in groups:
            if marker in normalized:
                return "CONSTRAINTS", name
        return "CONSTRAINTS_UNMAPPED", None
    return "OTHER", None


def add_metric(target: dict[str, Any], record: dict[str, Any]) -> None:
    target["statementCount"] += 1
    target["userCpuSeconds"] += record["userCpuSeconds"]
    target["systemCpuSeconds"] += record["systemCpuSeconds"]
    target["cpuSeconds"] += record["cpuSeconds"]
    target["statementElapsedSeconds"] += record["statementElapsedSeconds"]
    target["filesystemBlocksIn"] += record["filesystemBlocksIn"]
    target["filesystemBlocksOut"] += record["filesystemBlocksOut"]
    target["maxResidentKiB"] = max(target["maxResidentKiB"], record["maxResidentKiB"])


def empty_metric() -> dict[str, Any]:
    return {
        "statementCount": 0,
        "userCpuSeconds": 0.0,
        "systemCpuSeconds": 0.0,
        "cpuSeconds": 0.0,
        "statementElapsedSeconds": 0.0,
        "filesystemBlocksIn": 0,
        "filesystemBlocksOut": 0,
        "maxResidentKiB": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--backend-pid", type=int, required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.backend_pid <= 1 or not args.database.startswith("gda_v49_phase2a_"):
        raise ParseError("CPU_PARSE_TARGET_POLICY")
    lines = args.log.resolve().read_text(encoding="utf-8", errors="strict").splitlines()
    starts = [
        index for index, line in enumerate(lines)
        if f"[{args.backend_pid}] LOG:  QUERY STATISTICS" in line
    ]
    if not starts:
        raise ParseError("NO_STATEMENT_STATS_FOR_BACKEND")
    records: list[dict[str, Any]] = []
    for start in starts:
        end = len(lines)
        for index in range(start + 1, len(lines)):
            match = LOG_HEADER_RE.match(lines[index])
            if match:
                end = index
                break
        block = lines[start:end]
        text = "\n".join(block)
        usage = USAGE_RE.search(text)
        rss = RSS_RE.search(text)
        blocks = BLOCK_RE.search(text)
        statement_index = next(
            (index for index, line in enumerate(block)
             if f"[{args.backend_pid}] STATEMENT:" in line),
            None,
        )
        if usage is None or rss is None or blocks is None or statement_index is None:
            raise ParseError(f"INCOMPLETE_STATEMENT_STATS_BLOCK:{start + 1}")
        first = block[statement_index].split("STATEMENT:", 1)[1]
        continuation = [
            line[1:] if line.startswith("\t") else line
            for line in block[statement_index + 1:]
        ]
        statement = "\n".join([first, *continuation]).strip()
        user = float(usage.group(1))
        system = float(usage.group(2))
        stage, constraint = category(statement)
        records.append({
            "stage": stage,
            "constraintGroup": constraint,
            "userCpuSeconds": user,
            "systemCpuSeconds": system,
            "cpuSeconds": user + system,
            "statementElapsedSeconds": float(usage.group(3)),
            "maxResidentKiB": int(rss.group(1)),
            "filesystemBlocksIn": int(blocks.group(1)),
            "filesystemBlocksOut": int(blocks.group(2)),
            "statementPrefix": " ".join(statement.split())[:240],
        })

    stages: dict[str, dict[str, Any]] = defaultdict(empty_metric)
    constraints: dict[str, dict[str, Any]] = defaultdict(empty_metric)
    total = empty_metric()
    for record in records:
        add_metric(total, record)
        add_metric(stages[record["stage"]], record)
        if record["constraintGroup"]:
            add_metric(constraints[record["constraintGroup"]], record)
    unmapped = [record for record in records if record["stage"] == "CONSTRAINTS_UNMAPPED"]
    required_groups = {
        "raw_core_cycle", "folder_assignment_shape", "visual_bridge_and_locator",
        "rights_observation", "rights_assessment_shape_support",
        "rights_assessment_current_leaf", "provider_policy",
        "delivery_parent_validation", "delivery_rights_validation",
        "delivery_policy_validation", "delivery_history_and_rule",
        "final_all_omission_check",
    }
    missing = sorted(required_groups - set(constraints))
    result = {
        "status": "PASS" if not unmapped and not missing else "FAIL",
        "schema": "gda-v49-phase2b-backend-statement-cpu/v1",
        "database": args.database,
        "backendPid": args.backend_pid,
        "statementStatsRecordCount": len(records),
        "total": total,
        "stages": dict(sorted(stages.items())),
        "constraintGroups": dict(sorted(constraints.items())),
        "unmappedConstraintStatements": unmapped,
        "missingConstraintGroups": missing,
    }
    args.output.resolve().write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print(json.dumps({
        "status": result["status"], "backendPid": args.backend_pid,
        "records": len(records), "cpuSeconds": total["cpuSeconds"],
    }, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ParseError, OSError, ValueError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, sort_keys=True))
        raise SystemExit(2)
