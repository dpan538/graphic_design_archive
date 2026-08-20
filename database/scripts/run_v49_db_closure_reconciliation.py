#!/usr/bin/env python3
"""Reconcile two full fresh destinations against the attested Candidate ledger.

The staging ledger is an immutable, hash-attested projection of the sole v48
Candidate JSON input.  This verifier recomputes the Candidate hash, validates
the two relevant staging descriptor hashes, and compares every surface stable
ID and deterministic database UUID in both fresh destinations.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any


HEADER = [
    "input_ordinal", "surface_id", "legacy_surface_ledger_id",
    "source_record_id", "archive_object_id", "import_disposition",
    "reason_code", "corpus_disposition", "fail_closed_delta_id",
]


class ReconciliationError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def decode_json_b64(value: str) -> str:
    decoded = json.loads(base64.b64decode(value, validate=True).decode("utf-8"))
    if not isinstance(decoded, str):
        raise ReconciliationError("STAGING_SCALAR_NOT_STRING")
    return decoded


def write_tsv(path: Path, rows: list[dict[str, str]], header: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_source(stage: Path) -> dict[str, dict[str, str]]:
    row_path = stage / "surface-row-ledger.tsv"
    ledger_path = stage / "surface-ledgers.tsv"
    held_path = stage / "held-deltas.tsv"
    held_by_source: dict[str, str] = {}
    with held_path.open(encoding="utf-8", newline="") as handle:
        for held in csv.DictReader(handle, delimiter="\t"):
            source_record_id = held["source_record_id"]
            if source_record_id in held_by_source:
                raise ReconciliationError("SOURCE_HELD_DELTA_DUPLICATE:" + source_record_id)
            held_by_source[source_record_id] = held["fail_closed_delta_id"]
    by_ordinal: dict[str, dict[str, str]] = {}
    with row_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            ordinal = row["source_ordinal"]
            by_ordinal[ordinal] = {
                "input_ordinal": ordinal,
                "surface_id": row["surface_id_exact"],
                "source_record_id": row["raw_record_uuid"],
                "archive_object_id": row["archive_object_uuid"],
                "import_disposition": row["import_disposition"],
                "reason_code": row["workflow_reason"],
                "corpus_disposition": row["research_disposition"],
                "fail_closed_delta_id": held_by_source.get(row["raw_record_uuid"], ""),
            }
    if len(by_ordinal) != 15923:
        raise ReconciliationError(f"SOURCE_ROW_COUNT:{len(by_ordinal)}")
    with ledger_path.open(encoding="utf-8", newline="") as handle:
        for ledger in csv.DictReader(handle, delimiter="\t"):
            ordinal = ledger["input_ordinal"]
            if ordinal not in by_ordinal:
                raise ReconciliationError("SOURCE_LEDGER_ORDINAL_UNEXPECTED:" + ordinal)
            row = by_ordinal[ordinal]
            surface = decode_json_b64(ledger["surface_id_json_b64"])
            reason = decode_json_b64(ledger["reason_code_json_b64"])
            if (
                row["surface_id"] != surface
                or row["source_record_id"] != ledger["source_record_id"]
                or row["archive_object_id"] != ledger["archive_object_id"]
                or row["import_disposition"] != ledger["import_disposition"]
                or row["reason_code"] != reason
            ):
                raise ReconciliationError("SOURCE_LEDGER_CROSSCHECK:" + ordinal)
            row["legacy_surface_ledger_id"] = ledger["legacy_surface_ledger_id"]
    if any("legacy_surface_ledger_id" not in row for row in by_ordinal.values()):
        raise ReconciliationError("SOURCE_LEDGER_MISSING_ORDINAL")
    source = {row["surface_id"]: row for row in by_ordinal.values()}
    if len(source) != 15923:
        raise ReconciliationError("SOURCE_SURFACE_ID_DUPLICATE")
    return source


def query_rows(args: argparse.Namespace, database: str) -> list[dict[str, str]]:
    sql = r"""
SET ROLE gda_v49_phase2a_schema_owner;
COPY (
  SELECT l.input_ordinal::text,l.surface_id,l.legacy_surface_ledger_id::text,
    l.source_record_id::text,l.archive_object_id::text,l.import_disposition::text,
    l.reason_code,coalesce(
      cm.disposition::text,
      CASE WHEN d.fail_closed_delta_id IS NOT NULL THEN 'held' ELSE '' END
    ) AS corpus_disposition,
    coalesce(d.fail_closed_delta_id::text,'') AS fail_closed_delta_id
  FROM raw.legacy_surface_ledger l
  LEFT JOIN research.corpus_membership cm ON cm.archive_object_id=l.archive_object_id
  LEFT JOIN raw.fail_closed_delta d ON d.source_record_id=l.source_record_id
  ORDER BY l.input_ordinal
) TO STDOUT WITH (FORMAT csv,HEADER true,DELIMITER E'\t',NULL '');
"""
    env = os.environ.copy()
    env.update({
        "PGHOST": args.host, "PGPORT": args.port, "PGDATABASE": database,
        "PGUSER": args.admin_user,
    })
    result = subprocess.run(
        [args.psql, "-X", "-q", "-v", "ON_ERROR_STOP=1", "-c", sql],
        text=True, capture_output=True, env=env, timeout=180, check=False,
    )
    if result.returncode:
        raise ReconciliationError("DATABASE_QUERY_FAILED:" + result.stderr[-2000:])
    reader = csv.DictReader(result.stdout.splitlines(), delimiter="\t")
    if reader.fieldnames != HEADER:
        raise ReconciliationError("DATABASE_HEADER_MISMATCH:" + repr(reader.fieldnames))
    return list(reader)


def database_map(rows: list[dict[str, str]]) -> tuple[dict[str, dict[str, str]], list[dict[str, str]]]:
    mapped: dict[str, dict[str, str]] = {}
    duplicates: list[dict[str, str]] = []
    for row in rows:
        if row["surface_id"] in mapped:
            duplicates.append(row)
        else:
            mapped[row["surface_id"]] = row
    return mapped, duplicates


def metric_query(args: argparse.Namespace, database: str) -> dict[str, int]:
    sql = r"""
SET ROLE gda_v49_phase2a_schema_owner;
SELECT jsonb_build_object(
  'positiveRights',(SELECT count(*) FROM rights.rights_assessment WHERE assessed_state='permitted'),
  'remoteImageDecisions',(SELECT count(*) FROM rights.delivery_assessment WHERE delivery_mode='remote_image'),
  'publicPixelLocators',(SELECT count(*) FROM rights.visual_locator WHERE visibility='public_candidate'),
  'acceptedSemanticRelations',(SELECT count(*) FROM research.semantic_relation WHERE status='accepted'))::text;
"""
    env = os.environ.copy()
    env.update({"PGHOST": args.host, "PGPORT": args.port, "PGDATABASE": database, "PGUSER": args.admin_user})
    result = subprocess.run(
        [args.psql, "-X", "-Atq", "-v", "ON_ERROR_STOP=1", "-c", sql],
        text=True, capture_output=True, env=env, timeout=30, check=False,
    )
    if result.returncode:
        raise ReconciliationError("METRIC_QUERY_FAILED:" + result.stderr[-2000:])
    return {key: int(value) for key, value in json.loads(result.stdout.strip()).items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--psql", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True)
    parser.add_argument("--database-a", required=True)
    parser.add_argument("--database-b", required=True)
    parser.add_argument("--admin-user", required=True)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--stage", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    if not args.host.startswith("/") or args.port == "5432":
        parser.error("isolated non-default Unix socket required")
    if not all(name.startswith("gda_v49_phase2a_") for name in (args.database_a, args.database_b)):
        parser.error("database prefix rejected")

    manifest = json.loads((args.stage / "staging-manifest.json").read_text(encoding="utf-8"))
    candidate_sha = sha256_file(args.candidate)
    descriptor = manifest["files"]
    binding_pass = (
        candidate_sha == manifest["candidate"]["sha256"]
        and args.candidate.stat().st_size == manifest["candidate"]["bytes"]
        and sha256_file(args.stage / "surface-row-ledger.tsv") == descriptor["surface-row-ledger.tsv"]["sha256"]
        and sha256_file(args.stage / "surface-ledgers.tsv") == descriptor["surface-ledgers.tsv"]["sha256"]
    )
    if not binding_pass:
        raise ReconciliationError("CANDIDATE_STAGE_BINDING_MISMATCH")

    source = load_source(args.stage)
    rows_a = query_rows(args, args.database_a)
    rows_b = query_rows(args, args.database_b)
    map_a, duplicates_a = database_map(rows_a)
    map_b, duplicates_b = database_map(rows_b)
    source_ids, ids_a, ids_b = set(source), set(map_a), set(map_b)
    missing_a = [source[key] for key in sorted(source_ids - ids_a)]
    missing_b = [source[key] for key in sorted(source_ids - ids_b)]
    unexpected_a = [map_a[key] for key in sorted(ids_a - source_ids)]
    unexpected_b = [map_b[key] for key in sorted(ids_b - source_ids)]
    compare_fields = [key for key in HEADER if key != "surface_id"]
    mismatch_a = [
        {"surface_id": key, "fields": ",".join(field for field in compare_fields if source[key][field] != map_a[key][field])}
        for key in sorted(source_ids & ids_a)
        if any(source[key][field] != map_a[key][field] for field in compare_fields)
    ]
    mismatch_b = [
        {"surface_id": key, "fields": ",".join(field for field in compare_fields if source[key][field] != map_b[key][field])}
        for key in sorted(source_ids & ids_b)
        if any(source[key][field] != map_b[key][field] for field in compare_fields)
    ]
    remapped = [
        {"surface_id": key, "fields": ",".join(field for field in compare_fields if map_a[key][field] != map_b[key][field])}
        for key in sorted(ids_a & ids_b)
        if any(map_a[key][field] != map_b[key][field] for field in compare_fields)
    ]
    quarantined = [row for row in rows_a if row["corpus_disposition"] == "held"]
    metrics_a = metric_query(args, args.database_a)
    metrics_b = metric_query(args, args.database_b)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    source_rows = sorted(source.values(), key=lambda row: int(row["input_ordinal"]))
    write_tsv(args.output_dir / "candidate-derived-stable-ids.tsv", source_rows, HEADER)
    write_tsv(args.output_dir / "fresh-a-stable-ids.tsv", rows_a, HEADER)
    write_tsv(args.output_dir / "fresh-b-stable-ids.tsv", rows_b, HEADER)
    write_tsv(args.output_dir / "missing-a.tsv", missing_a, HEADER)
    write_tsv(args.output_dir / "missing-b.tsv", missing_b, HEADER)
    write_tsv(args.output_dir / "unexpected-a.tsv", unexpected_a, HEADER)
    write_tsv(args.output_dir / "unexpected-b.tsv", unexpected_b, HEADER)
    write_tsv(args.output_dir / "duplicate-a.tsv", duplicates_a, HEADER)
    write_tsv(args.output_dir / "duplicate-b.tsv", duplicates_b, HEADER)
    write_tsv(args.output_dir / "source-mismatch-a.tsv", mismatch_a, ["surface_id", "fields"])
    write_tsv(args.output_dir / "source-mismatch-b.tsv", mismatch_b, ["surface_id", "fields"])
    write_tsv(args.output_dir / "remapped-a-b.tsv", remapped, ["surface_id", "fields"])
    write_tsv(args.output_dir / "quarantined-stable-ids.tsv", quarantined, HEADER)

    manifest_metrics = manifest["metrics"]
    unexplained = sum(map(len, [missing_a, missing_b, unexpected_a, unexpected_b, duplicates_a, duplicates_b, mismatch_a, mismatch_b, remapped]))
    rights_widening = sum(metrics_a.values()) + sum(metrics_b.values())
    payload: dict[str, Any] = {
        "format": "gda-v49-db-closure-stable-id-reconciliation/v1",
        "candidateSha256": candidate_sha,
        "candidateStageBinding": "PASS",
        "sourceStableIdCount": len(source),
        "freshAStableIdCount": len(rows_a),
        "freshBStableIdCount": len(rows_b),
        "missingStableIdCount": len(missing_a) + len(missing_b),
        "unexpectedStableIdCount": len(unexpected_a) + len(unexpected_b),
        "duplicatedStableIdCount": len(duplicates_a) + len(duplicates_b),
        "remappedStableIdCount": len(remapped),
        "sourceMismatchCount": len(mismatch_a) + len(mismatch_b),
        "quarantinedStableIdCount": len(quarantined),
        "unexplainedDeltaCount": unexplained,
        "rightsWideningCount": rights_widening,
        "unknownRelationCoercionCount": metrics_a["acceptedSemanticRelations"] + metrics_b["acceptedSemanticRelations"],
        "silentDropCount": int(manifest_metrics["silentlyDroppedFields"]),
        "silentSplitCount": int(manifest_metrics["silentDelimiterSplits"]),
        "freshAMetrics": metrics_a,
        "freshBMetrics": metrics_b,
    }
    payload["status"] = "PASS" if (
        len(source) == len(rows_a) == len(rows_b) == 15923
        and len(quarantined) == 7928
        and payload["unexplainedDeltaCount"] == 0
        and payload["rightsWideningCount"] == 0
        and payload["unknownRelationCoercionCount"] == 0
        and payload["silentDropCount"] == 0
        and payload["silentSplitCount"] == 0
    ) else "FAIL"
    (args.output_dir / "reconciliation-summary.json").write_text(
        json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.SubprocessError, ReconciliationError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, sort_keys=True))
        raise SystemExit(2)
