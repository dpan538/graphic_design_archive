#!/usr/bin/env python3
"""Bind final task-temp cleanup evidence into the partial Phase 2B package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, NoReturn


ROOT = Path(__file__).resolve().parents[3]


class RefreshError(RuntimeError):
    """A final-audit refresh invariant failure."""


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise RefreshError(f"DUPLICATE_JSON_KEY:{key}")
        value[key] = item
    return value


def reject_constant(value: str) -> NoReturn:
    raise RefreshError(f"UNSUPPORTED_JSON_CONSTANT:{value}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_object, parse_constant=reject_constant)
    if not isinstance(value, dict):
        raise RefreshError("JSON_NOT_OBJECT")
    return value


def tsv(path: Path, header: list[str], rows: list[list[Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def render_required_tsv(output: Path) -> None:
    reconcile = read_json(output / "evidence" / "reconcile.json")
    authority = reconcile.get("artifactAuthorityLedger")
    if not isinstance(authority, dict) or len(authority) != 5:
        raise RefreshError("ARTIFACT_AUTHORITY_LEDGER_INVALID")
    values = sorted(authority.values(), key=lambda value: value["path"])
    population = [value for value in values if value.get("populationInput") is True]
    if len(population) != 1 or population[0].get("sha256") != "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48":
        raise RefreshError("CANONICAL_INPUT_LEDGER_INVALID")
    tsv(output / "02_ARTIFACT_AUTHORITY_LEDGER.tsv", ["path", "bytes", "sha256", "authority_role", "population_input", "reconciliation_only", "integrity_only"], [[value["path"], value["bytes"], value["sha256"], value["authorityRole"], str(value["populationInput"]).lower(), str(value["reconciliationOnly"]).lower(), str(value["integrityOnly"]).lower()] for value in values])
    mapping = read_json(ROOT / "database" / "data-migrations" / "v48-to-v49" / "mapping-v1.json")
    rules = mapping.get("rules")
    if not isinstance(rules, list) or not rules:
        raise RefreshError("MAPPING_RULES_INVALID")
    columns = ["rule_id", "source_pattern", "source_type", "input_cardinality", "target", "transform_version", "null_policy", "missing_policy", "array_order_policy", "duplicate_policy", "delimiter_policy", "vocabulary_mapping", "unknown_invalid_disposition", "public_internal_exposure", "provenance_target", "round_trip_query", "raw_snapshot_only"]
    mapping_keys = {"rule_id": "ruleId", "source_pattern": "sourcePattern", "source_type": "sourceType", "input_cardinality": "inputCardinality", "target": "target", "transform_version": "transformVersion", "null_policy": "nullPolicy", "missing_policy": "missingPolicy", "array_order_policy": "arrayOrderPolicy", "duplicate_policy": "duplicatePolicy", "delimiter_policy": "delimiterPolicy", "vocabulary_mapping": "vocabularyMapping", "unknown_invalid_disposition": "unknownInvalidDisposition", "public_internal_exposure": "exposure", "provenance_target": "provenanceTarget", "round_trip_query": "roundTripQuery", "raw_snapshot_only": "rawSnapshotOnly"}
    tsv(output / "03_FIELD_MAPPING_MATRIX.tsv", columns, [[rule.get(mapping_keys[column], "") for column in columns] for rule in rules])


def manifest_and_checksums(output: Path) -> None:
    files = []
    for path in sorted(output.rglob("*")):
        if not path.is_file() or path.name in {"MANIFEST.json", "CHECKSUMS.sha256"}:
            continue
        files.append({"path": path.relative_to(output).as_posix(), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    manifest = {
        "schema": "gda-v49-phase2b-performance-block-audit-manifest/v1",
        "phase": "v49-phase2b-performance-blocked-recovery",
        "status": "PARTIAL_PERFORMANCE_BLOCKED",
        "implementationBaseCommit": "86ba95cae9ecf12e58fcabb8170c9020e151b386",
        "expectedSchemaSha256": "4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105",
        "candidateJsonSha256": "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48",
        "files": files,
        "checksumScope": "all audit-package files except CHECKSUMS.sha256; MANIFEST.json is included in CHECKSUMS but not self-hashed here",
    }
    (output / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    paths = sorted(path for path in output.rglob("*") if path.is_file() and path.name != "CHECKSUMS.sha256")
    (output / "CHECKSUMS.sha256").write_text("\n".join(f"{sha256_file(path)}  {path.relative_to(output).as_posix()}" for path in paths) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--temp-cleanup", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if not (output / "17_PHASE2B_GATE_RECEIPT.md").is_file() or "PARTIAL_PERFORMANCE_BLOCKED" not in (output / "17_PHASE2B_GATE_RECEIPT.md").read_text(encoding="utf-8"):
        raise RefreshError("PARTIAL_GATE_MISSING")
    cleanup = read_json(args.temp_cleanup.resolve())
    if cleanup.get("status") != "PASS" or cleanup.get("cacheRetained") is not True or cleanup.get("stageTempVerifiedAbsent") is not True or cleanup.get("recoveryBackupVerifiedAbsent") is not True:
        raise RefreshError("TASK_TEMP_CLEANUP_INVALID")
    render_required_tsv(output)
    (output / "21_TASK_TEMP_FINALIZATION_RECEIPT.md").write_text("# Task-temp finalization\n\n```json\n" + json.dumps(cleanup, sort_keys=True, indent=2) + "\n```\n\nThe removable task-local checkpoint roots were deleted only after their evidence had been copied into this audit package. The verified external staging cache remains retained and is not a Git artifact.\n", encoding="utf-8")
    manifest_and_checksums(output)
    print(json.dumps({"status": "PASS", "files": len([p for p in output.rglob('*') if p.is_file()])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RefreshError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
