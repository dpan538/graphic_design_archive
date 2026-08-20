#!/usr/bin/env python3
"""Reduce auto_explain profile directories to a comparable stage ledger."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


STAGES = [
    "fixture_input_preparation",
    "canonical_assignment_load",
    "assignment_supersession_current_leaf",
    "reverse_index_construction",
    "release_projection_build",
    "chunk_digest_calculation",
    "final_digest_reduction",
    "validation_reconciliation",
    "index_creation_or_maintenance_and_plpgsql_overhead",
    "analyze",
    "sealing_finalization",
    "transaction_commit",
]


def extract_plans(path: Path) -> list[dict[str, Any]]:
    payload = path.read_text(encoding="utf-8")
    decoder = json.JSONDecoder()
    offset = 0
    plans: list[dict[str, Any]] = []
    while True:
        start = payload.find("{", offset)
        if start < 0:
            break
        try:
            value, end = decoder.raw_decode(payload, start)
        except json.JSONDecodeError:
            offset = start + 1
            continue
        if isinstance(value, dict) and "Query Text" in value and "Plan" in value:
            plans.append(value)
        offset = end
    return plans


def classify(query: str) -> str | None:
    normalized = " ".join(query.split())
    if normalized.startswith("CREATE TEMPORARY TABLE gda_v5_expected_memberships"):
        return "reverse_index_construction"
    if "gda_v5_effective_decisions" in normalized and normalized.startswith("CREATE TEMPORARY TABLE"):
        return "assignment_supersession_current_leaf"
    if normalized.startswith("EXISTS (SELECT 1 FROM gda_v5_effective_decisions"):
        return "assignment_supersession_current_leaf"
    if "gda_v5_expected_memberships" in normalized and "folder_publication_metadata" in normalized:
        return "validation_reconciliation"
    if normalized.startswith("CREATE TEMPORARY TABLE gda_v5_expected_objects"):
        return "canonical_assignment_load"
    if normalized.startswith("INSERT INTO gda_v5_component_rows") or normalized.startswith("WITH chunks AS"):
        return "chunk_digest_calculation"
    if normalized.startswith("INSERT INTO release.research_launch_component_manifest_v3"):
        return "final_digest_reduction"
    if normalized.startswith("(SELECT count(*) FROM gda_v5_expected_objects)"):
        return "validation_reconciliation"
    if normalized.startswith("INSERT INTO release.research_launch_protocol_v5"):
        return "sealing_finalization"
    if normalized.startswith("INSERT INTO release.research_launch_build_receipt_v3"):
        return "sealing_finalization"
    if normalized.startswith("UPDATE release.research_release SET release_state='candidate'"):
        return "sealing_finalization"
    if normalized.startswith("INSERT INTO release.research_"):
        return "release_projection_build"
    return None


def nodes(plan: dict[str, Any]) -> list[dict[str, Any]]:
    result = [plan]
    for child in plan.get("Plans", []):
        result.extend(nodes(child))
    return result


def blank_stage() -> dict[str, Any]:
    return {
        "durationMs": 0.0, "rowsIn": 0, "rowsOut": 0, "queryCount": 0,
        "repeatedScans": 0, "tempBytes": 0, "tempReadBlocks": 0,
        "tempWrittenBlocks": 0, "sharedReadBlocks": 0, "sharedHitBlocks": 0,
        "walBytes": 0, "loops": 0, "plannerNodeTypes": [], "fingerprints": [],
    }


def add_plan(stage: dict[str, Any], item: dict[str, Any]) -> None:
    plan = item["Plan"]
    all_nodes = nodes(plan)
    query = " ".join(item["Query Text"].split())
    fingerprint = hashlib.sha256(query.encode()).hexdigest()
    stage["durationMs"] += float(plan.get("Actual Total Time", 0))
    root_rows = int(plan.get("Actual Rows", 0))
    if root_rows == 0 and plan.get("Operation") == "Insert" and plan.get("Plans"):
        root_rows = int(plan["Plans"][0].get("Actual Rows", 0))
    stage["rowsIn"] += root_rows
    stage["rowsOut"] += root_rows
    stage["queryCount"] += 1
    stage["tempReadBlocks"] += int(plan.get("Temp Read Blocks", 0))
    stage["tempWrittenBlocks"] += int(plan.get("Temp Written Blocks", 0))
    stage["sharedReadBlocks"] += int(plan.get("Shared Read Blocks", 0))
    stage["sharedHitBlocks"] += int(plan.get("Shared Hit Blocks", 0))
    stage["walBytes"] += int(plan.get("WAL Bytes", 0))
    stage["loops"] += int(plan.get("Actual Loops", 0))
    stage["repeatedScans"] += sum(int(node.get("Actual Loops", 0)) > 1 for node in all_nodes)
    stage["plannerNodeTypes"] = sorted(set(stage["plannerNodeTypes"]) | {str(node.get("Node Type")) for node in all_nodes})
    stage["fingerprints"].append({"sha256": fingerprint, "query": query[:240]})


def profile(root: Path, scale: int) -> dict[str, Any]:
    profile_root = root / f"stage-{scale}"
    summary = json.loads((profile_root / "profile-summary.json").read_text(encoding="utf-8"))
    plans = extract_plans(profile_root / "builder.auto-explain.log")
    stages = {name: blank_stage() for name in STAGES}
    stages["fixture_input_preparation"]["durationMs"] = float(summary["fixtureWallMs"])
    stages["fixture_input_preparation"]["rowsIn"] = scale
    stages["fixture_input_preparation"]["rowsOut"] = int(summary["memberships"])
    stages["fixture_input_preparation"]["queryCount"] = 1
    stages["analyze"]["durationMs"] = float(summary["analyzeWallMs"])
    stages["analyze"]["queryCount"] = 6
    outer_ms = 0.0
    classified_ms = 0.0
    for item in plans:
        normalized = " ".join(item["Query Text"].split())
        if normalized.startswith("SELECT release.build_research_launch_snapshot_v5("):
            outer_ms = float(item["Plan"].get("Actual Total Time", 0))
            continue
        stage_name = classify(item["Query Text"])
        if stage_name:
            add_plan(stages[stage_name], item)
            classified_ms += float(item["Plan"].get("Actual Total Time", 0))
    residual = max(0.0, outer_ms - classified_ms)
    residual_stage = stages["index_creation_or_maintenance_and_plpgsql_overhead"]
    residual_stage["durationMs"] = residual
    residual_stage["queryCount"] = 2
    residual_stage["rowsIn"] = int(summary["memberships"])
    residual_stage["rowsOut"] = int(summary["memberships"])
    residual_stage["note"] = "outer builder time minus all classified nested statements; includes two temporary indexes, advisory locks, trigger time, and PL/pgSQL scalar overhead"
    stdout = (profile_root / "builder.stdout.txt").read_text(encoding="utf-8")
    commit = re.search(r"COMMIT\s+Time: ([0-9.]+) ms", stdout)
    stages["transaction_commit"]["durationMs"] = float(commit.group(1)) if commit else 0.0
    stages["transaction_commit"]["queryCount"] = 1
    for value in stages.values():
        value["durationMs"] = round(float(value["durationMs"]), 3)
        value["tempBytes"] = value["tempWrittenBlocks"] * 8192
    return {
        "scale": scale,
        "memberships": int(summary["memberships"]),
        "instrumentedBuilderWallMs": float(summary["instrumentedBuilderWallMs"]),
        "outerBuilderPlanMs": round(outer_ms, 3),
        "stages": stages,
        "resourceBefore": summary["resourceBefore"],
        "resourceAfter": summary["resourceAfter"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-root", required=True, type=Path)
    parser.add_argument("--after-root", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-csv", required=True, type=Path)
    args = parser.parse_args()
    payload: dict[str, Any] = {"format": "gda-v49-db-closure-stage-comparison/v1", "baseline": {}, "after": {}}
    for label, root in (("baseline", args.baseline_root), ("after", args.after_root)):
        for scale in (32, 1000, 2000):
            payload[label][str(scale)] = profile(root, scale)
    rows: list[dict[str, Any]] = []
    for stage in STAGES:
        row: dict[str, Any] = {"stage": stage}
        for label in ("baseline", "after"):
            for scale in (32, 1000, 2000):
                row[f"{label}_{scale}_ms"] = payload[label][str(scale)]["stages"][stage]["durationMs"]
        for label in ("baseline", "after"):
            one = float(row[f"{label}_1000_ms"])
            two = float(row[f"{label}_2000_ms"])
            row[f"{label}_ratio_1k_2k"] = round(two / one, 9) if one else None
            row[f"{label}_exponent_1k_2k"] = round(math.log(two / one, 2), 9) if one and two else None
            measured = payload[label]["2000"]
            total = (
                measured["stages"]["fixture_input_preparation"]["durationMs"]
                + measured["stages"]["analyze"]["durationMs"]
                + measured["instrumentedBuilderWallMs"]
            )
            row[f"{label}_percent_2k"] = round(two * 100 / total, 6) if total else None
        rows.append(row)
    payload["stageComparison"] = rows
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    with args.output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
