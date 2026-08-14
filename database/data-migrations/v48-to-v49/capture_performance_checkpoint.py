#!/usr/bin/env python3
"""Capture immutable, read-only evidence for a Phase 2B performance stop.

This utility deliberately does not invoke the extractor, importer, replay
runner, reconciliation tool, or any data-changing SQL.  It resolves the
active replay backend from the task-owned socket/database, captures its
process and PostgreSQL state, and writes a new JSON checkpoint atomically by
requiring that the target path does not already exist.
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
MIGRATION_DIR = Path(__file__).resolve().parent
EXPECTED_SCHEMA = "4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105"
EXPECTED_CANDIDATE = "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48"
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
    "verify_recovery_checkpoint.py",
    "capture_performance_checkpoint.py",
)


class CheckpointError(RuntimeError):
    """A receipt-worthy performance checkpoint failure."""


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CheckpointError(f"DUPLICATE_JSON_KEY:{key}")
        result[key] = value
    return result


def reject_constant(value: str) -> NoReturn:
    raise CheckpointError(f"UNSUPPORTED_JSON_CONSTANT:{value}")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=strict_object,
            parse_constant=reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CheckpointError(f"JSON_READ_FAILED:{path}") from exc
    if not isinstance(value, dict):
        raise CheckpointError(f"JSON_NOT_OBJECT:{path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def command(command: list[str], *, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(command, text=True, capture_output=True, env=env, check=False)
    if completed.returncode:
        raise CheckpointError("COMMAND_FAILED:" + " ".join(command) + ":" + completed.stderr[-2000:])
    return completed.stdout.rstrip()


def db_environment(args: argparse.Namespace) -> dict[str, str]:
    result = os.environ.copy()
    result.update({
        "PGHOST": args.pg_host,
        "PGPORT": str(args.pg_port),
        "PGDATABASE": args.database,
        "PGUSER": args.admin_user,
        "PGCONNECT_TIMEOUT": "5",
    })
    return result


def psql_json(args: argparse.Namespace) -> dict[str, Any]:
    sql = """
BEGIN READ ONLY;
WITH target AS (
  SELECT pid, datname, usename, application_name, state, wait_event_type,
         wait_event, backend_start, xact_start, query_start, state_change,
         query
  FROM pg_catalog.pg_stat_activity
  WHERE datname = current_database()
    AND backend_type = 'client backend'
    AND query LIKE 'SET CONSTRAINTS ALL IMMEDIATE%'
    AND pid <> pg_backend_pid()
  ORDER BY query_start
)
SELECT jsonb_build_object(
  'targets', COALESCE(jsonb_agg(jsonb_build_object(
    'pid', pid, 'database', datname, 'user', usename,
    'applicationName', application_name, 'state', state,
    'waitEventType', COALESCE(wait_event_type, 'none'),
    'waitEvent', COALESCE(wait_event, 'none'),
    'backendStartUtc', to_char(backend_start AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
    'xactStartUtc', to_char(xact_start AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
    'queryStartUtc', to_char(query_start AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
    'stateChangeUtc', to_char(state_change AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
    'query', query,
    'blockingPids', pg_catalog.pg_blocking_pids(pid)
  ) ORDER BY pid), '[]'::jsonb)
) FROM target;
WITH target AS (
  SELECT pid FROM pg_catalog.pg_stat_activity
  WHERE datname = current_database()
    AND backend_type = 'client backend'
    AND query LIKE 'SET CONSTRAINTS ALL IMMEDIATE%'
    AND pid <> pg_backend_pid()
)
SELECT jsonb_build_object(
  'locks', COALESCE((SELECT jsonb_agg(jsonb_build_object(
    'locktype', locktype, 'mode', mode, 'granted', granted,
    'relation', relation::regclass::text, 'transactionid', transactionid::text
  ) ORDER BY locktype, mode, granted)
  FROM pg_catalog.pg_locks WHERE pid = (SELECT pid FROM target)), '[]'::jsonb),
  'clusterLocksGranted', (SELECT count(*) FROM pg_catalog.pg_locks WHERE granted),
  'clusterLocksWaiting', (SELECT count(*) FROM pg_catalog.pg_locks WHERE NOT granted)
);
SELECT jsonb_build_object(
  'database', datname, 'numBackends', numbackends, 'xactCommit', xact_commit,
  'xactRollback', xact_rollback, 'blksRead', blks_read, 'blksHit', blks_hit,
  'tempFiles', temp_files, 'tempBytes', temp_bytes,
  'statsResetUtc', CASE WHEN stats_reset IS NULL THEN NULL ELSE to_char(stats_reset AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"') END
) FROM pg_catalog.pg_stat_database WHERE datname = current_database();
COMMIT;
"""
    output = command(["psql", "-X", "-Atq", "-v", "ON_ERROR_STOP=1", "-c", sql], env=db_environment(args))
    lines = [line for line in output.splitlines() if line]
    if len(lines) != 3:
        raise CheckpointError(f"PSQL_OUTPUT_INVALID:{len(lines)}")
    target, locks, stats = [json.loads(line, object_pairs_hook=strict_object, parse_constant=reject_constant) for line in lines]
    if not isinstance(target, dict) or not isinstance(locks, dict) or not isinstance(stats, dict):
        raise CheckpointError("PSQL_JSON_INVALID")
    targets = target.get("targets")
    if not isinstance(targets, list) or len(targets) != 1 or not isinstance(targets[0], dict):
        raise CheckpointError(f"TASK_BACKEND_RESOLUTION_INVALID:{targets!r}")
    if targets[0].get("database") != args.database:
        raise CheckpointError("TASK_BACKEND_DATABASE_MISMATCH")
    return {"backend": targets[0], "locks": locks, "statistics": stats}


def process_line(pid: int) -> dict[str, Any]:
    text = command(["ps", "-o", "pid=,ppid=,pgid=,uid=,state=,etime=,time=,%cpu=,%mem=,command=", "-p", str(pid)])
    if not text:
        raise CheckpointError(f"PROCESS_NOT_RUNNING:{pid}")
    return {"pid": pid, "ps": text}


def task_processes() -> list[str]:
    text = command(["ps", "-axo", "pid=,ppid=,pgid=,uid=,state=,etime=,time=,%cpu=,%mem=,command="])
    needles = (
        "gda_v49_phase2b.0rUT9y",
        "gda_v49_phase2b_stage_final.eVALvR",
        "database/data-migrations/v48-to-v49/run-rehearsal.sh",
        "database/data-migrations/v48-to-v49/import.py",
    )
    return [line for line in text.splitlines() if any(needle in line for needle in needles)]


def tail_descriptor(path: Path, lines: int = 80) -> dict[str, Any]:
    if not path.is_file():
        raise CheckpointError(f"LOG_MISSING:{path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": sha256_file(path),
        "tail": "\n".join(text.splitlines()[-lines:]),
    }


def disk_kib(path: Path) -> int:
    return int(command(["du", "-sk", str(path.resolve())]).split()[0])


def git_snapshot() -> dict[str, Any]:
    return {
        "head": command(["git", "rev-parse", "HEAD"], env=None),
        "branch": command(["git", "branch", "--show-current"], env=None),
        "statusPorcelainV1": command(["git", "status", "--porcelain=v1", "-uall"], env=None).splitlines(),
        "diffStat": command(["git", "diff", "--stat"], env=None).splitlines(),
        "cachedDiffStat": command(["git", "diff", "--cached", "--stat"], env=None).splitlines(),
        "untrackedAllowlist": command(["git", "ls-files", "--others", "--exclude-standard"], env=None).splitlines(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-dir", type=Path, required=True)
    parser.add_argument("--failure-report", type=Path, required=True)
    parser.add_argument("--recovery-checkpoint", type=Path, required=True)
    parser.add_argument("--server-log", type=Path, required=True)
    parser.add_argument("--runtime-log", type=Path, required=True)
    parser.add_argument("--pg-host", required=True)
    parser.add_argument("--pg-port", type=int, required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--admin-user", default="gda_v49_phase2b_admin")
    parser.add_argument("--pgdata", type=Path, required=True)
    parser.add_argument("--postmaster-pid", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stage = args.stage_dir.resolve()
    pgdata = args.pgdata.resolve()
    socket = Path(args.pg_host).resolve()
    if args.pg_port == 5432 or not str(stage).startswith("/private/tmp/"):
        raise CheckpointError("DISPOSABLE_PATH_POLICY_VIOLATION")
    if not str(pgdata).startswith("/private/tmp/gda_v49_phase2b.") or not str(socket).startswith("/private/tmp/gda_v49_phase2b."):
        raise CheckpointError("TASK_OWNERSHIP_PATH_POLICY_VIOLATION")
    socket_path = socket / f".s.PGSQL.{args.pg_port}"
    if not socket_path.exists():
        raise CheckpointError("TASK_SOCKET_MISSING")
    activity = psql_json(args)
    backend_pid = int(activity["backend"]["pid"])
    backend = process_line(backend_pid)
    postmaster = process_line(args.postmaster_pid)
    if str(pgdata) not in postmaster["ps"] or str(socket) not in postmaster["ps"]:
        raise CheckpointError("POSTMASTER_OWNERSHIP_MISMATCH")
    manifest_path = stage / "staging-manifest.json"
    manifest = read_json(manifest_path)
    descriptors = manifest.get("files")
    if not isinstance(descriptors, dict) or len(descriptors) != 35:
        raise CheckpointError("STAGING_DESCRIPTOR_COUNT_INVALID")
    implementation: dict[str, str] = {}
    for relative in IMPLEMENTATION_FILES:
        path = MIGRATION_DIR / relative
        if not path.is_file():
            raise CheckpointError(f"IMPLEMENTATION_FILE_MISSING:{relative}")
        implementation[relative] = sha256_file(path)
    failure = args.failure_report.resolve()
    recovery = args.recovery_checkpoint.resolve()
    payload = {
        "schema": "gda-v49-phase2b-performance-checkpoint/v1",
        "status": "PERFORMANCE_BLOCKED_LIVE_SNAPSHOT",
        "capturedAtUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "expectedSchemaSha256": EXPECTED_SCHEMA,
        "candidateJsonSha256": EXPECTED_CANDIDATE,
        "postgres": {
            "pgdataRealpath": str(pgdata), "socketRealpath": str(socket),
            "socketPath": str(socket_path), "port": args.pg_port,
            "database": args.database, "postmaster": postmaster,
            "backend": backend, "activity": activity,
        },
        "taskOwnedProcessLines": task_processes(),
        "temporaryDiskKiB": {"stage": disk_kib(stage), "pgdata": disk_kib(pgdata)},
        "staging": {
            "realpath": str(stage), "manifest": {
                "path": str(manifest_path), "bytes": manifest_path.stat().st_size,
                "sha256": sha256_file(manifest_path),
            },
            "descriptorCount": len(descriptors), "declaredDescriptors": descriptors,
        },
        "failureReport": {"path": str(failure), "bytes": failure.stat().st_size, "sha256": sha256_file(failure)},
        "recoveryCheckpoint": {"path": str(recovery), "bytes": recovery.stat().st_size, "sha256": sha256_file(recovery)},
        "serverLog": tail_descriptor(args.server_log.resolve()),
        "runtimeLog": tail_descriptor(args.runtime_log.resolve()),
        "implementationSha256": implementation,
        "git": git_snapshot(),
    }
    if args.output.exists():
        raise CheckpointError(f"OUTPUT_ALREADY_EXISTS:{args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
    print(json.dumps({
        "status": payload["status"], "backendPid": backend_pid,
        "backendState": activity["backend"]["state"],
        "descriptorCount": len(descriptors), "output": str(args.output),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CheckpointError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
