#!/usr/bin/env python3
"""Rerun the eleven importer failure paths on one fixed <=1,000 fixture."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


MIGRATION_DIR = Path(__file__).resolve().parent
FINAL_SCHEMA = "aa8cb0af7b61931e51f1f71ed2e4cf0d10b178669de16807871819b330742e8b"
BAD_SHA = "0" * 64


class ProbeError(RuntimeError):
    pass


def environment(args: argparse.Namespace, user: str) -> dict[str, str]:
    value = os.environ.copy()
    value.update({
        "PGHOST": args.pg_host, "PGPORT": str(args.pg_port),
        "PGDATABASE": args.database, "PGUSER": user,
    })
    return value


def query(args: argparse.Namespace, sql: str) -> str:
    result = subprocess.run(
        ["psql", "-X", "-Atq", "-v", "ON_ERROR_STOP=1", "-c", sql],
        text=True, capture_output=True,
        env=environment(args, args.admin_user), check=False,
    )
    if result.returncode:
        raise ProbeError("RESIDUE_QUERY_FAILED:" + result.stderr[-2000:])
    return result.stdout.strip()


def residue(args: argparse.Namespace) -> dict[str, Any]:
    relations = query(args, """
SELECT string_agg(format('%I.%I',schemaname,tablename), E'\n' ORDER BY schemaname,tablename)
FROM pg_tables WHERE schemaname=ANY(ARRAY[
  'raw','core','provenance','research','rights','workflow','release','audit'
]);
""").splitlines()
    union = " UNION ALL ".join(
        f"SELECT '{name}' AS relation,count(*)::bigint AS rows FROM {name}"
        for name in relations
    )
    counts = json.loads(query(
        args,
        "SET ROLE gda_v49_phase2a_schema_owner; "
        f"SELECT jsonb_object_agg(relation,rows ORDER BY relation)::text FROM ({union}) q;",
    ))
    nonzero = {name: int(count) for name, count in counts.items() if int(count) != 0}
    return {
        "nonzeroProjectTables": nonzero,
        "partialImportResidue": sum(nonzero.values()),
        "migrationBatchResidue": int(counts.get("raw.migration_batch", 0)),
        "currentPointerResidue": int(counts.get("release.research_current_pointer", 0))
        + int(counts.get("release.visual_current_pointer", 0)),
        "sealedReleaseResidue": int(query(args, """
SET ROLE gda_v49_phase2a_schema_owner;
SELECT (SELECT count(*) FROM release.research_release WHERE release_state='sealed')
     + (SELECT count(*) FROM release.visual_registry_release WHERE release_state='sealed');
""") or "0"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture-dir", type=Path, required=True)
    parser.add_argument("--pg-host", required=True)
    parser.add_argument("--pg-port", type=int, required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--admin-user", default="gda_v49_phase2b_admin")
    parser.add_argument("--runtime-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fixture_dir = args.fixture_dir.resolve()
    fixture = json.loads((fixture_dir / "performance-fixture-manifest.json").read_text(encoding="utf-8"))
    if fixture.get("scale", 1001) > 1000:
        raise ProbeError("FAILURE_FIXTURE_EXCEEDS_1000")
    runtime_dir = args.runtime_dir.resolve()
    runtime_dir.mkdir(parents=True, exist_ok=True)
    base = [
        sys.executable, str(MIGRATION_DIR / "import.py"),
        "--stage-dir", str(fixture_dir),
        "--performance-fixture-manifest", str(fixture_dir / "performance-fixture-manifest.json"),
        "--pg-host", args.pg_host, "--pg-port", str(args.pg_port),
        "--database", args.database, "--admin-user", args.admin_user,
        "--runtime-dir", str(runtime_dir),
        "--constraint-timeout-seconds", "900",
    ]
    probes = [
        ("duplicate_surface_key", ["--fault", "duplicate_surface"], "SURFACE_LEDGER_CARDINALITY_MISMATCH"),
        ("missing_surface", ["--fault", "missing_surface"], "SURFACE_LEDGER_CARDINALITY_MISMATCH"),
        ("extra_surface", ["--fault", "extra_surface"], "SURFACE_LEDGER_CARDINALITY_MISMATCH"),
        ("unknown_field_or_type_without_disposition", ["--fault", "unknown_field"], "FIELD_OCCURRENCE_UNDECLARED_RULE"),
        ("source_sha_mismatch", ["--expected-candidate", BAD_SHA], "PERFORMANCE_FIXTURE_SOURCE_BINDING"),
        ("schema_sha_mismatch", ["--expected-schema", BAD_SHA], "DATABASE_SCHEMA_SHA_MISMATCH"),
        ("after_staging", ["--inject", "after_staging"], "PHASE2B_INJECTED_FAILURE:after_staging"),
        ("during_objects", ["--inject", "during_objects"], "PHASE2B_INJECTED_FAILURE:during_objects"),
        ("after_corpus", ["--inject", "after_corpus"], "PHASE2B_INJECTED_FAILURE:after_corpus"),
        ("after_visual", ["--inject", "after_visual"], "PHASE2B_INJECTED_FAILURE:after_visual"),
        ("after_parity", ["--inject", "after_parity"], "PHASE2B_INJECTED_FAILURE:after_parity"),
    ]
    results: dict[str, Any] = {}
    for name, extra, marker in probes:
        command = base + extra + [
            "--log", str(runtime_dir / f"failure-{name}.log"),
            "--receipt", str(runtime_dir / f"failure-{name}.json"),
        ]
        result = subprocess.run(
            command, text=True, capture_output=True,
            env=environment(args, args.admin_user), check=False,
        )
        combined = result.stdout + result.stderr
        after = residue(args)
        passed = (
            result.returncode == 2 and marker in combined
            and after["partialImportResidue"] == 0
            and after["migrationBatchResidue"] == 0
            and after["currentPointerResidue"] == 0
            and after["sealedReleaseResidue"] == 0
        )
        results[name] = {
            "status": "PASS" if passed else "FAIL",
            "returnCode": result.returncode,
            "expectedMarker": marker,
            "markerObserved": marker in combined,
            "residue": after,
            "tail": combined[-4000:],
        }
        if not passed:
            raise ProbeError("FAILURE_PROBE_FAILED:" + name)
    report = {
        "status": "PASS", "probeCount": len(probes),
        "fixtureScale": fixture["scale"],
        "fullScaleFailureProbesRerun": False,
        "finalSchemaSha256": FINAL_SCHEMA,
        "probes": results,
    }
    args.output.resolve().write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "PASS", "probeCount": len(probes)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ProbeError, OSError, KeyError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
