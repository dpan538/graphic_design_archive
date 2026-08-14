#!/usr/bin/env python3
"""Prove a cancelled Phase 2B replay left no durable data behind.

This recovery verifier is intentionally read-only.  It is separate from the
successful-replay verifier because a PostgreSQL autovacuum worker may be
cleaning dead tuples after cancellation; that internal worker is recorded but
is not confused with a live importer/client session.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NoReturn


ROOT = Path(__file__).resolve().parents[3]
EXPECTED_SCHEMA = "4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105"
EXPECTED_PROBES = {
    "source_sha_mismatch", "schema_sha_mismatch", "after_staging", "during_objects",
    "after_corpus", "after_visual", "after_parity", "duplicate_surface_key",
    "missing_surface", "extra_surface", "unknown_field_or_type_without_disposition",
}
PROJECT_SCHEMAS = ("raw", "core", "provenance", "research", "rights", "workflow", "release", "audit")


class RollbackError(RuntimeError):
    """A recovery checkpoint invariant failure."""


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RollbackError(f"DUPLICATE_JSON_KEY:{key}")
        result[key] = value
    return result


def reject_constant(value: str) -> NoReturn:
    raise RollbackError(f"UNSUPPORTED_JSON_CONSTANT:{value}")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_object, parse_constant=reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RollbackError(f"JSON_READ_FAILED:{path}") from exc
    if not isinstance(value, dict):
        raise RollbackError(f"JSON_NOT_OBJECT:{path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def command(values: list[str], *, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(values, text=True, capture_output=True, env=env, check=False)
    if completed.returncode:
        raise RollbackError("COMMAND_FAILED:" + " ".join(values) + ":" + completed.stderr[-2000:])
    return completed.stdout.rstrip()


def environment(args: argparse.Namespace) -> dict[str, str]:
    result = os.environ.copy()
    result.update({
        "PGHOST": args.pg_host, "PGPORT": str(args.pg_port), "PGDATABASE": args.database,
        "PGUSER": args.admin_user, "PGCONNECT_TIMEOUT": "5",
    })
    return result


def stage_rehash(stage: Path) -> dict[str, Any]:
    manifest_path = stage / "staging-manifest.json"
    manifest = read_json(manifest_path)
    files = manifest.get("files")
    if not isinstance(files, dict) or len(files) != 35:
        raise RollbackError("STAGING_DESCRIPTOR_COUNT_INVALID")
    descriptors: dict[str, dict[str, Any]] = {}
    for relative, descriptor in sorted(files.items()):
        if not isinstance(relative, str) or not isinstance(descriptor, dict):
            raise RollbackError("STAGING_DESCRIPTOR_INVALID")
        source = stage / relative
        if not source.is_file():
            raise RollbackError(f"STAGING_FILE_MISSING:{relative}")
        if source.stat().st_size != descriptor.get("bytes") or sha256_file(source) != descriptor.get("sha256"):
            raise RollbackError(f"STAGING_DESCRIPTOR_MISMATCH:{relative}")
        descriptors[relative] = {"bytes": source.stat().st_size, "sha256": descriptor["sha256"]}
    return {
        "path": str(stage), "manifestPath": str(manifest_path),
        "manifestSha256": sha256_file(manifest_path), "descriptorCount": len(descriptors),
        "descriptorRehash": "PASS", "descriptors": descriptors,
    }


def failure_evidence(path: Path) -> dict[str, Any]:
    report = read_json(path)
    probes = report.get("probes")
    if report.get("status") != "PASS" or not isinstance(probes, dict) or set(probes) != EXPECTED_PROBES:
        raise RollbackError("FAILURE_PROBE_REPORT_INVALID")
    for name, probe in probes.items():
        if not isinstance(probe, dict) or not isinstance(probe.get("exitCode"), int) or probe["exitCode"] == 0:
            raise RollbackError(f"FAILURE_PROBE_DID_NOT_FAIL:{name}")
        if probe.get("partialImportResidue") != 0 or probe.get("currentPointerAdvanced") is not False or probe.get("releaseSealed") is not False:
            raise RollbackError(f"FAILURE_PROBE_RESIDUE_INVALID:{name}")
    return {"path": str(path), "sha256": sha256_file(path), "probeCount": len(probes), "status": "PASS"}


def database_snapshot(args: argparse.Namespace) -> dict[str, Any]:
    schemas = ",".join("'" + schema + "'" for schema in PROJECT_SCHEMAS)
    sql = f"""
BEGIN READ ONLY;
WITH table_rows AS (
  SELECT n.nspname || '.' || c.relname AS table_name,
         ((xpath('/row/count/text()', query_to_xml(format('SELECT count(*) FROM %I.%I', n.nspname, c.relname), false, true, '')))[1]::text)::bigint AS row_count
  FROM pg_catalog.pg_class c
  JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
  WHERE c.relkind = 'r' AND n.nspname = ANY (ARRAY[{schemas}])
)
SELECT jsonb_build_object(
  'projectTableCount', (SELECT count(*) FROM table_rows),
  'projectTableTotalRows', (SELECT COALESCE(sum(row_count), 0) FROM table_rows),
  'nonZeroProjectTables', (SELECT COALESCE(jsonb_agg(table_name ORDER BY table_name) FILTER (WHERE row_count <> 0), '[]'::jsonb) FROM table_rows),
  'migrationBatchRows', (SELECT count(*) FROM raw.migration_batch),
  'researchCurrentPointers', (SELECT count(*) FROM release.research_current_pointer),
  'visualCurrentPointers', (SELECT count(*) FROM release.visual_current_pointer),
  'researchSealedReleases', (SELECT count(*) FROM release.research_release WHERE release_state = 'sealed'),
  'visualSealedReleases', (SELECT count(*) FROM release.visual_registry_release WHERE release_state = 'sealed'),
  'otherClientSessions', (SELECT COALESCE(jsonb_agg(jsonb_build_object('pid',pid,'user',usename,'state',state,'query',left(query,120)) ORDER BY pid), '[]'::jsonb) FROM pg_catalog.pg_stat_activity WHERE datname=current_database() AND pid <> pg_backend_pid() AND backend_type='client backend'),
  'otherNonClientBackends', (SELECT COALESCE(jsonb_agg(jsonb_build_object('pid',pid,'backendType',backend_type,'state',state,'query',left(query,120)) ORDER BY pid), '[]'::jsonb) FROM pg_catalog.pg_stat_activity WHERE datname=current_database() AND pid <> pg_backend_pid() AND backend_type <> 'client backend')
);
COMMIT;
"""
    output = command(["psql", "-X", "-Atq", "-v", "ON_ERROR_STOP=1", "-c", sql], env=environment(args))
    lines = [line for line in output.splitlines() if line]
    if len(lines) != 1:
        raise RollbackError(f"DATABASE_SNAPSHOT_OUTPUT_INVALID:{len(lines)}")
    data = json.loads(lines[0], object_pairs_hook=strict_object, parse_constant=reject_constant)
    if not isinstance(data, dict):
        raise RollbackError("DATABASE_SNAPSHOT_JSON_INVALID")
    for key in ("projectTableTotalRows", "migrationBatchRows", "researchCurrentPointers", "visualCurrentPointers", "researchSealedReleases", "visualSealedReleases"):
        if data.get(key) != 0:
            raise RollbackError(f"DURABLE_RESIDUE_PRESENT:{key}:{data.get(key)!r}")
    if data.get("nonZeroProjectTables") != [] or data.get("otherClientSessions") != []:
        raise RollbackError("DATABASE_ROLLBACK_INCOMPLETE")
    return data


def schema_hash(args: argparse.Namespace) -> str:
    actual = command([str(ROOT / "database/scripts/schema_hash.sh")], env=environment(args))
    if actual != EXPECTED_SCHEMA:
        raise RollbackError(f"SCHEMA_HASH_MISMATCH:{actual}")
    return actual


def forbidden_processes() -> list[str]:
    text = command(["ps", "-axo", "pid=,ppid=,pgid=,uid=,state=,etime=,time=,command="])
    needles = (
        "database/data-migrations/v48-to-v49/run-rehearsal.sh",
        "database/data-migrations/v48-to-v49/import.py",
        "runtime-import-gda_v49_phase2a_phase2b_replay_a.sql",
    )
    return [line for line in text.splitlines() if any(needle in line for needle in needles)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-dir", type=Path, required=True)
    parser.add_argument("--failure-report", type=Path, required=True)
    parser.add_argument("--pg-host", required=True)
    parser.add_argument("--pg-port", type=int, required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--admin-user", default="gda_v49_phase2b_admin")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stage = args.stage_dir.resolve()
    if args.pg_port == 5432 or not str(stage).startswith("/private/tmp/") or not Path(args.pg_host).resolve().as_posix().startswith("/private/tmp/gda_v49_phase2b."):
        raise RollbackError("DISPOSABLE_CONNECTION_POLICY_VIOLATION")
    payload = {
        "schema": "gda-v49-phase2b-performance-rollback/v1",
        "status": "PASS",
        "capturedAtUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "expectedSchemaSha256": EXPECTED_SCHEMA,
        "database": database_snapshot(args),
        "schemaSha256": schema_hash(args),
        "staging": stage_rehash(stage),
        "failure": failure_evidence(args.failure_report.resolve()),
        "forbiddenImportProcesses": forbidden_processes(),
    }
    if payload["forbiddenImportProcesses"]:
        raise RollbackError("ORPHAN_IMPORT_PROCESS_PRESENT")
    if args.output.exists():
        raise RollbackError(f"OUTPUT_ALREADY_EXISTS:{args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
    print(json.dumps({
        "status": payload["status"], "projectTableCount": payload["database"]["projectTableCount"],
        "projectTableTotalRows": payload["database"]["projectTableTotalRows"],
        "descriptorCount": payload["staging"]["descriptorCount"],
        "schemaSha256": payload["schemaSha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RollbackError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
