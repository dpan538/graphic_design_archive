#!/usr/bin/env python3
"""Bind a stopped Phase 2B failure harness to its reusable staging bundle.

This is deliberately a recovery-audit utility, not a runner.  It never calls
the extractor, importer, reconciliation program, or a schema replay.  It
rehashes the already-created staging descriptors, validates the persisted
failure report and server-log markers, then opens one ``READ ONLY`` PostgreSQL
transaction to prove the disposable failure database is empty before a later
fresh replay starts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, NoReturn


ROOT = Path(__file__).resolve().parents[3]
MIGRATION_DIR = Path(__file__).resolve().parent
EXPECTED_SCHEMA = "4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105"
EXPECTED_CANDIDATE = "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48"
EXPECTED_BASE = "86ba95cae9ecf12e58fcabb8170c9020e151b386"
EXPECTED_PROBES = {
    "source_sha_mismatch": False,
    "schema_sha_mismatch": False,
    "after_staging": True,
    "during_objects": True,
    "after_corpus": True,
    "after_visual": True,
    "after_parity": True,
    "duplicate_surface_key": False,
    "missing_surface": False,
    "extra_surface": False,
    "unknown_field_or_type_without_disposition": False,
}
RUNTIME_MARKERS = tuple(name for name, runtime in EXPECTED_PROBES.items() if runtime)
IMPLEMENTATION_FILES = (
    "extract.py",
    "import.py",
    "load.sql",
    "mapping-v1.json",
    "reconcile.py",
    "run-rehearsal.sh",
    "verify.py",
    "tests/run_failure_injections.py",
    "tests/run_idempotency_and_batch_collision.py",
    "tests/run_public_boundary_fixture.py",
    "generate_audit.py",
)
PROJECT_SCHEMAS = ("raw", "core", "provenance", "research", "rights", "workflow", "release", "audit")


class RecoveryError(RuntimeError):
    """A receipt-worthy recovery validation failure."""


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RecoveryError(f"DUPLICATE_JSON_KEY:{key}")
        result[key] = value
    return result


def reject_constant(value: str) -> NoReturn:
    raise RecoveryError(f"UNSUPPORTED_JSON_CONSTANT:{value}")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=strict_object,
            parse_constant=reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RecoveryError(f"JSON_READ_FAILED:{path}") from exc
    if not isinstance(value, dict):
        raise RecoveryError(f"JSON_NOT_OBJECT:{path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def require_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise RecoveryError(f"{label}: expected {expected!r}, got {actual!r}")


def require_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise RecoveryError(f"INVALID_SHA256:{label}")
    return value


def rehash_stage(stage: Path) -> dict[str, Any]:
    manifest_path = stage / "staging-manifest.json"
    manifest = read_json(manifest_path)
    require_equal(manifest.get("candidate", {}).get("sha256"), EXPECTED_CANDIDATE, "stage.candidate")
    require_equal(manifest.get("schemaNormalizedSha256"), EXPECTED_SCHEMA, "stage.schema")
    require_equal(manifest.get("implementationBaseCommit"), EXPECTED_BASE, "stage.base")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise RecoveryError("STAGING_FILE_DESCRIPTORS_MISSING")
    descriptors: dict[str, dict[str, Any]] = {}
    for relative, descriptor in sorted(files.items()):
        if not isinstance(relative, str) or not isinstance(descriptor, dict):
            raise RecoveryError("STAGING_DESCRIPTOR_INVALID")
        path = stage / relative
        if not path.is_file():
            raise RecoveryError(f"STAGING_FILE_MISSING:{relative}")
        expected_bytes = descriptor.get("bytes")
        expected_sha = require_sha(descriptor.get("sha256"), f"stage.{relative}")
        actual_bytes = path.stat().st_size
        actual_sha = sha256_file(path)
        if actual_bytes != expected_bytes or actual_sha != expected_sha:
            raise RecoveryError(f"STAGING_DESCRIPTOR_MISMATCH:{relative}")
        descriptors[relative] = {"bytes": actual_bytes, "sha256": actual_sha}
    metrics = manifest.get("metrics")
    if not isinstance(metrics, dict):
        raise RecoveryError("STAGING_METRICS_MISSING")
    for key, expected in {
        "surfaceCount": 15923,
        "sourceRecordCount": 15923,
        "fieldOccurrenceCount": 6282271,
        "fieldLiteralCount": 3559820,
        "folderAssignmentCount": 47982,
        "unmappedSourceFields": 0,
        "silentlyDroppedFields": 0,
        "silentDelimiterSplits": 0,
        "crossArrayPositionalZips": 0,
        "automaticDeduplication": 0,
        "unexplainedMappingDeltas": 0,
    }.items():
        require_equal(metrics.get(key), expected, f"stage.metrics.{key}")
    return {
        "path": str(stage),
        "manifestPath": str(manifest_path),
        "manifestBytes": manifest_path.stat().st_size,
        "manifestSha256": sha256_file(manifest_path),
        "descriptorCount": len(descriptors),
        "descriptorRehash": "PASS",
        "filesSha256": hashlib.sha256(canonical_json(descriptors).encode("utf-8")).hexdigest(),
        "metrics": metrics,
        "binding": {
            "candidateSha256": manifest["candidate"]["sha256"],
            "extractorSha256": manifest["extractor"]["sha256"],
            "mappingSha256": manifest["mapping"]["sha256"],
            "schemaNormalizedSha256": manifest["schemaNormalizedSha256"],
            "implementationBaseCommit": manifest["implementationBaseCommit"],
            "bundleBinding": manifest["bundleBinding"],
        },
    }


def validate_failure_report(path: Path) -> dict[str, Any]:
    report = read_json(path)
    require_equal(report.get("status"), "PASS", "failure.status")
    probes = report.get("probes")
    if not isinstance(probes, dict):
        raise RecoveryError("FAILURE_PROBES_MISSING")
    require_equal(set(probes), set(EXPECTED_PROBES), "failure.probe_set")
    normalized: dict[str, dict[str, Any]] = {}
    for name, runtime in EXPECTED_PROBES.items():
        value = probes.get(name)
        if not isinstance(value, dict):
            raise RecoveryError(f"FAILURE_PROBE_INVALID:{name}")
        if not isinstance(value.get("exitCode"), int) or value["exitCode"] == 0:
            raise RecoveryError(f"FAILURE_PROBE_DID_NOT_FAIL:{name}")
        require_equal(value.get("runtime"), runtime, f"failure.{name}.runtime")
        require_equal(value.get("partialImportResidue"), 0, f"failure.{name}.partial_residue")
        require_equal(value.get("currentPointerAdvanced"), False, f"failure.{name}.pointer")
        require_equal(value.get("releaseSealed"), False, f"failure.{name}.seal")
        normalized[name] = value
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "status": "PASS",
        "probeCount": len(normalized),
        "probes": normalized,
        "sourceAssertZeroScope": list(PROJECT_SCHEMAS),
        "midObjectSubsetRows": 8000,
        "note": "The exact current harness source hashes below require assert_zero after every probe; this recovery check separately proves all committed project rows are zero after the completed 11/11 sequence.",
    }


def require_runtime_markers(server_log: Path) -> dict[str, Any]:
    text = server_log.read_text(encoding="utf-8", errors="strict")
    markers = {}
    for marker in RUNTIME_MARKERS:
        needle = "PHASE2B_INJECTED_FAILURE:" + marker
        if needle not in text:
            raise RecoveryError(f"SERVER_LOG_MARKER_MISSING:{marker}")
        markers[marker] = needle
    return {
        "path": str(server_log),
        "bytes": server_log.stat().st_size,
        "sha256": sha256_file(server_log),
        "runtimeMarkers": markers,
    }


def implementation_hashes() -> dict[str, str]:
    result: dict[str, str] = {}
    for relative in IMPLEMENTATION_FILES:
        path = MIGRATION_DIR / relative
        if not path.is_file():
            raise RecoveryError(f"IMPLEMENTATION_FILE_MISSING:{relative}")
        result[relative] = sha256_file(path)
    return result


def environment(args: argparse.Namespace) -> dict[str, str]:
    result = os.environ.copy()
    result.update({"PGHOST": args.pg_host, "PGPORT": str(args.pg_port), "PGDATABASE": args.database, "PGUSER": args.admin_user})
    return result


def run(command: list[str], *, env: dict[str, str]) -> str:
    completed = subprocess.run(command, text=True, capture_output=True, env=env, check=False)
    if completed.returncode:
        raise RecoveryError("COMMAND_FAILED:" + " ".join(command) + ":" + completed.stderr[-2000:])
    return completed.stdout.strip()


def project_residue(args: argparse.Namespace) -> dict[str, Any]:
    schemas = ",".join("'" + schema + "'" for schema in PROJECT_SCHEMAS)
    sql = f"""
BEGIN READ ONLY;
SELECT jsonb_object_agg(schemaname || '.' || tablename, row_count ORDER BY schemaname, tablename)::text
FROM (
  SELECT n.nspname AS schemaname, c.relname AS tablename,
    ((xpath('/row/count/text()', query_to_xml(format('SELECT count(*) FROM %I.%I', n.nspname, c.relname), false, true, '')))[1]::text)::bigint AS row_count
  FROM pg_catalog.pg_class c
  JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
  WHERE c.relkind = 'r' AND n.nspname = ANY (ARRAY[{schemas}])
) q;
SELECT jsonb_build_object(
  'migrationBatchRows', (SELECT count(*) FROM raw.migration_batch),
  'researchCurrentPointers', (SELECT count(*) FROM release.research_current_pointer),
  'visualCurrentPointers', (SELECT count(*) FROM release.visual_current_pointer),
  'researchSealedReleases', (SELECT count(*) FROM release.research_release WHERE release_state = 'sealed'),
  'visualSealedReleases', (SELECT count(*) FROM release.visual_registry_release WHERE release_state = 'sealed'),
  'activeOtherSessions', (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid() AND state <> 'idle')
)::text;
COMMIT;
"""
    output = run(["psql", "-X", "-Atq", "-v", "ON_ERROR_STOP=1", "-c", sql], env=environment(args))
    lines = [line for line in output.splitlines() if line]
    if len(lines) != 2:
        raise RecoveryError("RESIDUE_QUERY_OUTPUT_INVALID")
    rows = json.loads(lines[0], object_pairs_hook=strict_object, parse_constant=reject_constant)
    summary = json.loads(lines[1], object_pairs_hook=strict_object, parse_constant=reject_constant)
    if not isinstance(rows, dict) or not isinstance(summary, dict):
        raise RecoveryError("RESIDUE_QUERY_JSON_INVALID")
    if not rows or any(int(value) != 0 for value in rows.values()):
        raise RecoveryError("PARTIAL_IMPORT_RESIDUE_PRESENT")
    for key in ("migrationBatchRows", "researchCurrentPointers", "visualCurrentPointers", "researchSealedReleases", "visualSealedReleases", "activeOtherSessions"):
        require_equal(summary.get(key), 0, f"residue.{key}")
    return {
        "projectTableCount": len(rows),
        "projectTableRows": rows,
        "projectTableTotalRows": sum(int(value) for value in rows.values()),
        "committedMigrationBatchRows": 0,
        "committedCanonicalRows": 0,
        "partialImportResidue": 0,
        **summary,
    }


def schema_hash(args: argparse.Namespace) -> str:
    return run([str(ROOT / "database/scripts/schema_hash.sh")], env=environment(args))


def process_identity(pid: int, data_dir: Path, socket_dir: Path, port: int) -> dict[str, Any]:
    status = subprocess.run(
        ["ps", "-o", "pid=,ppid=,pgid=,uid=,state=,etime=,time=,command=", "-p", str(pid)],
        text=True, capture_output=True, check=False,
    )
    if status.returncode or not status.stdout.strip():
        raise RecoveryError(f"POSTGRES_PID_NOT_RUNNING:{pid}")
    command = status.stdout.strip()
    if str(data_dir) not in command or str(socket_dir) not in command:
        raise RecoveryError("POSTGRES_COMMAND_OWNERSHIP_MISMATCH")
    socket_path = socket_dir / f".s.PGSQL.{port}"
    if not socket_path.exists():
        raise RecoveryError("POSTGRES_SOCKET_MISSING")
    return {
        "pid": pid,
        "ps": command,
        "pgdataRealpath": str(data_dir.resolve()),
        "socketRealpath": str(socket_dir.resolve()),
        "socketPath": str(socket_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-dir", type=Path, required=True)
    parser.add_argument("--failure-report", type=Path, required=True)
    parser.add_argument("--server-log", type=Path, required=True)
    parser.add_argument("--pg-host", required=True)
    parser.add_argument("--pg-port", type=int, required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--admin-user", default="gda_v49_phase2b_admin")
    parser.add_argument("--postgres-pid", type=int, required=True)
    parser.add_argument("--pgdata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.pg_port == 5432 or not args.pg_host.startswith("/") or not args.database.startswith("gda_v49_phase2a_"):
        raise RecoveryError("DISPOSABLE_CONNECTION_POLICY_VIOLATION")
    stage = args.stage_dir.resolve()
    if not str(stage).startswith("/private/tmp/"):
        raise RecoveryError("STAGING_PATH_NOT_TASK_TEMP")
    if not str(args.pgdata.resolve()).startswith("/private/tmp/gda_v49_phase2b."):
        raise RecoveryError("PGDATA_PATH_NOT_TASK_TEMP")
    if not str(Path(args.pg_host).resolve()).startswith("/private/tmp/gda_v49_phase2b."):
        raise RecoveryError("SOCKET_PATH_NOT_TASK_TEMP")
    stage_result = rehash_stage(stage)
    failure_result = validate_failure_report(args.failure_report.resolve())
    log_result = require_runtime_markers(args.server_log.resolve())
    source_hashes = implementation_hashes()
    residue = project_residue(args)
    actual_schema = schema_hash(args)
    require_equal(actual_schema, EXPECTED_SCHEMA, "database.schema_hash")
    process = process_identity(args.postgres_pid, args.pgdata, Path(args.pg_host), args.pg_port)
    payload = {
        "schema": "gda-v49-phase2b-recovery-checkpoint/v1",
        "status": "PASS",
        "implementationBaseCommit": EXPECTED_BASE,
        "expectedSchemaSha256": EXPECTED_SCHEMA,
        "candidateJsonSha256": EXPECTED_CANDIDATE,
        "database": {"name": args.database, "schemaSha256": actual_schema, "residue": residue},
        "postgres": process,
        "staging": stage_result,
        "failure": failure_result,
        "serverLog": log_result,
        "implementation": {"hashes": source_hashes},
        "resumeDecision": {
            "completedFailureProbes": list(EXPECTED_PROBES),
            "firstUnreliableProbe": None,
            "resumeFailureHarness": False,
            "reason": "The pinned 11/11 report, all five runtime server markers, descriptor rehash, current source binding, and zero durable database snapshot agree.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": payload["status"], "descriptorCount": stage_result["descriptorCount"],
        "failureProbeCount": failure_result["probeCount"], "schemaSha256": actual_schema,
        "partialImportResidue": residue["partialImportResidue"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RecoveryError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
