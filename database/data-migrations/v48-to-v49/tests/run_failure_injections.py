#!/usr/bin/env python3
"""Fail-closed Phase 2B importer probes against one already-fresh test DB.

The harness never creates a cluster/database and never drops anything.  Each
importer failure is required to leave every project table empty; the caller
replays a new Phase 2A schema first and discards the explicit disposable DB
only after this report has been recorded.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
IMPORTER = ROOT / "database/data-migrations/v48-to-v49/import.py"
ADMIN = "gda_v49_phase2b_admin"


def env_for(args: argparse.Namespace, database: str) -> dict[str, str]:
    value = os.environ.copy()
    value.update({"PGHOST": args.pg_host, "PGPORT": str(args.pg_port), "PGDATABASE": database, "PGUSER": args.admin_user})
    return value


def psql(args: argparse.Namespace, database: str, sql: str) -> str:
    result = subprocess.run(
        ["psql", "-X", "-Atq", "-v", "ON_ERROR_STOP=1", "-c", sql],
        text=True, capture_output=True, env=env_for(args, database), check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr[-3000:])
    return result.stdout.strip()


def residue(args: argparse.Namespace, database: str) -> dict[str, int]:
    payload = psql(args, database, """
SELECT jsonb_object_agg(schemaname || '.' || tablename, row_count ORDER BY schemaname, tablename)::text
FROM (
  SELECT n.nspname AS schemaname, c.relname AS tablename,
    ((xpath('/row/count/text()', query_to_xml(format('SELECT count(*) FROM %I.%I', n.nspname, c.relname), false, true, '')))[1]::text)::bigint AS row_count
  FROM pg_catalog.pg_class c
  JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
  WHERE c.relkind='r' AND n.nspname = ANY (ARRAY['raw','core','provenance','research','rights','workflow','release','audit'])
) q;
""")
    return {key: int(value) for key, value in json.loads(payload).items()}


def assert_zero(args: argparse.Namespace, database: str, label: str) -> None:
    rows = residue(args, database)
    nonzero = {key: value for key, value in rows.items() if value}
    if nonzero:
        raise RuntimeError(f"PARTIAL_IMPORT_RESIDUE:{label}:{nonzero}")


def importer(args: argparse.Namespace, database: str, extra: list[str]) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable, str(IMPORTER), "--stage-dir", str(args.stage_dir),
        "--pg-host", args.pg_host, "--pg-port", str(args.pg_port),
        "--database", database, "--admin-user", args.admin_user,
    ] + extra
    return subprocess.run(command, text=True, capture_output=True, check=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-dir", type=Path, required=True)
    parser.add_argument("--pg-host", required=True)
    parser.add_argument("--pg-port", type=int, required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--admin-user", default=ADMIN)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.pg_port == 5432 or not args.pg_host.startswith("/") or not args.database.startswith("gda_v49_phase2a_"):
        raise SystemExit("DISPOSABLE_CONNECTION_POLICY_VIOLATION")

    probes: list[tuple[str, list[str], bool]] = [
        ("source_sha_mismatch", ["--expected-candidate", "0" * 64], False),
        ("schema_sha_mismatch", ["--expected-schema", "1" * 64], False),
        ("after_staging", ["--inject", "after_staging"], True),
        ("during_objects", ["--inject", "during_objects"], True),
        ("after_corpus", ["--inject", "after_corpus"], True),
        ("after_visual", ["--inject", "after_visual"], True),
        ("after_parity", ["--inject", "after_parity"], True),
        ("duplicate_surface_key", ["--fault", "duplicate_surface"], False),
        ("missing_surface", ["--fault", "missing_surface"], False),
        ("extra_surface", ["--fault", "extra_surface"], False),
        ("unknown_field_or_type_without_disposition", ["--fault", "unknown_field"], False),
    ]
    results: dict[str, dict[str, object]] = {}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for label, extra, runtime in probes:
        completed = importer(args, args.database, extra)
        if completed.returncode == 0:
            raise RuntimeError(f"FAILURE_PROBE_DID_NOT_FAIL:{label}")
        combined = completed.stdout + completed.stderr
        if runtime and label == "during_objects" and "PHASE2B_MID_OBJECT_SUBSET_ROWS=8000" not in combined:
            raise RuntimeError("MID_OBJECT_SUBSET_NOT_OBSERVED:" + combined[-4000:])
        assert_zero(args, args.database, label)
        results[label] = {
            "exitCode": completed.returncode,
            "runtime": runtime,
            "partialImportResidue": 0,
            "currentPointerAdvanced": False,
            "releaseSealed": False,
        }
        args.output.write_text(
            json.dumps({"status": "RUNNING", "database": args.database, "probes": results}, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    payload = {"status": "PASS", "database": args.database, "probes": results}
    args.output.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "probeCount": len(results), "partialImportResidue": 0}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
