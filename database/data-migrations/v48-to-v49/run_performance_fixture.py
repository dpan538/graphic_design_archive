#!/usr/bin/env python3
"""Run exactly one scale-ladder fixture in an already-created fresh database."""

from __future__ import annotations

import argparse
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
MIGRATION_DIR = Path(__file__).resolve().parent
FINAL_SCHEMA = "aa8cb0af7b61931e51f1f71ed2e4cf0d10b178669de16807871819b330742e8b"


class ScaleError(RuntimeError):
    pass


def env(args: argparse.Namespace, user: str) -> dict[str, str]:
    value = os.environ.copy()
    value.update({
        "PGHOST": args.pg_host, "PGPORT": str(args.pg_port),
        "PGDATABASE": args.database, "PGUSER": user,
    })
    return value


def run(
    command: list[str], *, environment: dict[str, str], stream: bool = False,
) -> subprocess.CompletedProcess[str]:
    if stream:
        process = subprocess.Popen(
            command, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, env=environment,
        )
        lines: list[str] = []
        assert process.stdout is not None
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            lines.append(line)
        code = process.wait()
        result = subprocess.CompletedProcess(command, code, "".join(lines), "")
    else:
        result = subprocess.run(
            command, text=True, capture_output=True,
            env=environment, check=False,
        )
    if result.returncode:
        raise ScaleError(
            "COMMAND_FAILED:" + " ".join(command[:3]) + "\n"
            + result.stdout[-4000:] + result.stderr[-4000:]
        )
    return result


def query(args: argparse.Namespace, sql: str) -> str:
    return run(
        ["psql", "-X", "-Atq", "-v", "ON_ERROR_STOP=1", "-c", sql],
        environment=env(args, args.admin_user),
    ).stdout.strip()


def stats(args: argparse.Namespace) -> dict[str, Any]:
    payload = query(args, """
SELECT jsonb_build_object(
  'capturedAt', clock_timestamp(),
  'postgresqlVersion', version(),
  'databaseBytes', pg_database_size(current_database()),
  'settings', (SELECT jsonb_object_agg(name, setting ORDER BY name)
    FROM pg_settings WHERE name=ANY(ARRAY[
      'fsync','synchronous_commit','full_page_writes','shared_buffers',
      'work_mem','maintenance_work_mem','max_wal_size','checkpoint_timeout',
      'track_io_timing','track_wal_io_timing','wal_compression'
    ])),
  'databaseStats', (SELECT to_jsonb(s)-'datid'-'datname'-'stats_reset'
    FROM pg_stat_database s WHERE datname=current_database()),
  'walStats', (SELECT to_jsonb(w)-'stats_reset' FROM pg_stat_wal w),
  'activeBackends', (SELECT count(*) FROM pg_stat_activity
    WHERE datname=current_database() AND pid<>pg_backend_pid()),
  'locksNotGranted', (SELECT count(*) FROM pg_locks WHERE NOT granted),
  'tableStats', (SELECT COALESCE(jsonb_agg(to_jsonb(x) ORDER BY x.relation),'[]')
    FROM (SELECT schemaname||'.'||relname AS relation,n_live_tup,n_dead_tup,
      seq_scan,idx_scan,n_tup_ins FROM pg_stat_user_tables) x),
  'indexStats', (SELECT COALESCE(jsonb_agg(to_jsonb(x) ORDER BY x.relation,x.index_name),'[]')
    FROM (SELECT schemaname||'.'||relname AS relation,indexrelname AS index_name,
      idx_scan,idx_tup_read,idx_tup_fetch FROM pg_stat_user_indexes) x),
  'ioStats', (SELECT COALESCE(jsonb_agg(to_jsonb(x) ORDER BY x.backend_type,x.object,x.context),'[]')
    FROM (SELECT backend_type,object,context,reads,reads*op_bytes AS read_bytes,
      read_time,writes,writes*op_bytes AS write_bytes,write_time,writebacks,
      extends,fsyncs FROM pg_stat_io) x)
)::text;
""")
    return json.loads(payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture-dir", type=Path, required=True)
    parser.add_argument("--pg-host", required=True)
    parser.add_argument("--pg-port", type=int, required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--admin-user", default="gda_v49_phase2b_admin")
    parser.add_argument("--runtime-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache-state", choices=("cold", "warm"), required=True)
    args = parser.parse_args()
    if args.pg_port == 5432 or not args.pg_host.startswith("/") or not args.database.startswith("gda_v49_phase2a_"):
        raise ScaleError("DISPOSABLE_CONNECTION_POLICY")
    fixture_dir = args.fixture_dir.resolve()
    runtime_dir = args.runtime_dir.resolve()
    runtime_dir.mkdir(parents=True, exist_ok=True)
    fixture_path = fixture_dir / "performance-fixture-manifest.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    scale = fixture["scale"]
    started = time.monotonic()
    before_usage = resource.getrusage(resource.RUSAGE_CHILDREN)

    run([str(ROOT / "database/scripts/replay.sh")], environment=env(args, args.admin_user), stream=True)
    run([
        "psql", "-X", "-q", "-v", "ON_ERROR_STOP=1",
        "-c", "SET ROLE gda_v49_phase2a_schema_owner",
        "-f", str(MIGRATION_DIR / "001_performance_remediation.sql"),
    ], environment=env(args, args.admin_user), stream=True)
    actual_schema = run(
        [str(ROOT / "database/scripts/schema_hash.sh")],
        environment=env(args, args.admin_user),
    ).stdout.strip()
    if actual_schema != FINAL_SCHEMA:
        raise ScaleError("FINAL_SCHEMA_HASH_MISMATCH:" + actual_schema)
    before = stats(args)

    import_receipt_path = runtime_dir / f"scale-{scale:05d}-import.json"
    verify_receipt_path = runtime_dir / f"scale-{scale:05d}-verify.json"
    run([
        sys.executable, str(MIGRATION_DIR / "import.py"),
        "--stage-dir", str(fixture_dir),
        "--performance-fixture-manifest", str(fixture_path),
        "--pg-host", args.pg_host, "--pg-port", str(args.pg_port),
        "--database", args.database, "--admin-user", args.admin_user,
        "--runtime-dir", str(runtime_dir),
        "--log", str(runtime_dir / f"scale-{scale:05d}-import.log"),
        "--receipt", str(import_receipt_path),
        "--constraint-timeout-seconds", "900",
    ], environment=env(args, args.admin_user), stream=True)
    run([
        sys.executable, str(MIGRATION_DIR / "verify.py"),
        "--pg-host", args.pg_host, "--pg-port", str(args.pg_port),
        "--database", args.database, "--admin-user", args.admin_user,
        "--expected-schema", FINAL_SCHEMA,
        "--performance-fixture-manifest", str(fixture_path),
        "--output", str(verify_receipt_path),
    ], environment=env(args, args.admin_user), stream=True)
    after = stats(args)
    import_receipt = json.loads(import_receipt_path.read_text(encoding="utf-8"))
    verify_receipt = json.loads(verify_receipt_path.read_text(encoding="utf-8"))
    after_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    result = {
        "status": "PASS",
        "schema": "gda-v49-phase2b-scale-result/v1",
        "scale": scale,
        "cacheState": args.cache_state,
        "fixtureManifestSha256": __import__("hashlib").sha256(fixture_path.read_bytes()).hexdigest(),
        "selectionSha256": fixture["selection"]["sha256"],
        "expected": fixture["expected"],
        "inputBytes": sum(fixture["files"][name]["bytes"] for name in fixture["files"] if name.endswith(".tsv") and name not in {"surface-row-ledger.tsv", "selected-objects.tsv"}),
        "schemaSha256": actual_schema,
        "wallSeconds": round(time.monotonic() - started, 6),
        "childUserCpuSeconds": round(after_usage.ru_utime-before_usage.ru_utime, 6),
        "childSystemCpuSeconds": round(after_usage.ru_stime-before_usage.ru_stime, 6),
        "statsBefore": before,
        "statsAfter": after,
        "databaseBytes": after["databaseBytes"],
        "import": import_receipt,
        "verify": verify_receipt,
    }
    args.output.resolve().write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": result["status"], "scale": scale,
        "wallSeconds": result["wallSeconds"],
        "importWallSeconds": import_receipt["wallSeconds"],
        "digest": verify_receipt["normalizedContentSha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ScaleError, OSError, KeyError, json.JSONDecodeError, subprocess.SubprocessError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
