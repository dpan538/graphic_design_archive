#!/usr/bin/env python3
"""Read-only OS/PostgreSQL sampler for one task-owned importer session."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MIGRATOR = "gda_v49_phase2a_migrator"


class MonitorError(RuntimeError):
    pass


def cpu_seconds(value: str) -> float:
    parts = value.strip().split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    except ValueError as error:
        raise MonitorError("PS_CPU_TIME_INVALID:" + value) from error
    raise MonitorError("PS_CPU_TIME_INVALID:" + value)


def tree_usage(root: Path) -> tuple[int, int, int]:
    logical = 0
    allocated = 0
    files = 0
    pending = [root]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    pending.append(Path(entry.path))
                elif entry.is_file(follow_symlinks=False):
                    stat = entry.stat(follow_symlinks=False)
                    logical += stat.st_size
                    allocated += getattr(stat, "st_blocks", 0) * 512
                    files += 1
    return logical, allocated, files


def pg_environment(args: argparse.Namespace) -> dict[str, str]:
    value = os.environ.copy()
    value.update({
        "PGHOST": args.pg_host,
        "PGPORT": str(args.pg_port),
        "PGDATABASE": args.database,
        "PGUSER": args.admin_user,
    })
    return value


def database_sample(args: argparse.Namespace) -> dict[str, Any]:
    sql = """
SELECT jsonb_build_object(
  'databaseBytes', pg_database_size(current_database()),
  'locksNotGranted', (SELECT count(*) FROM pg_locks WHERE NOT granted),
  'databaseStats', (SELECT jsonb_build_object(
    'tempBytes',temp_bytes,'tempFiles',temp_files,
    'blkReadTime',blk_read_time,'blkWriteTime',blk_write_time,
    'activeTime',active_time,'sessionTime',session_time,
    'tupInserted',tup_inserted,'tupUpdated',tup_updated,'tupDeleted',tup_deleted
  ) FROM pg_stat_database WHERE datname=current_database()),
  'migratorBackends', (SELECT COALESCE(jsonb_agg(jsonb_build_object(
    'pid',pid,'state',state,'waitEventType',wait_event_type,'waitEvent',wait_event,
    'xactAgeSeconds',extract(epoch FROM (clock_timestamp()-xact_start)),
    'queryAgeSeconds',extract(epoch FROM (clock_timestamp()-query_start)),
    'query',left(regexp_replace(query,E'[[:space:]]+',' ','g'),500)
  ) ORDER BY pid),'[]'::jsonb) FROM pg_stat_activity
    WHERE datname=current_database() AND usename='gda_v49_phase2a_migrator'),
  'copyProgress', (SELECT COALESCE(jsonb_agg(jsonb_build_object(
    'pid',pid,'command',command,'type',type,'bytesProcessed',bytes_processed,
    'bytesTotal',bytes_total,'tuplesProcessed',tuples_processed,
    'tuplesExcluded',tuples_excluded
  ) ORDER BY pid),'[]'::jsonb) FROM pg_stat_progress_copy)
)::text;
"""
    result = subprocess.run(
        [args.psql, "-X", "-Atq", "-v", "ON_ERROR_STOP=1", "-c", sql],
        text=True, capture_output=True, check=False, env=pg_environment(args),
    )
    if result.returncode:
        raise MonitorError("MONITOR_QUERY_FAILED:" + result.stderr[-2000:])
    return json.loads(result.stdout.strip())


def process_sample(pid: int) -> dict[str, Any] | None:
    result = subprocess.run(
        ["ps", "-p", str(pid), "-o", "pid=,time=,utime=,stime=,rss=,%cpu=,state="],
        text=True, capture_output=True, check=False,
    )
    if result.returncode or not result.stdout.strip():
        return None
    parts = result.stdout.split()
    if len(parts) < 7:
        return {"pid": pid, "raw": result.stdout.strip(), "parseError": True}
    return {
        "pid": int(parts[0]),
        "cpuSeconds": cpu_seconds(parts[1]),
        "userCpuSeconds": cpu_seconds(parts[2]),
        "systemCpuSeconds": cpu_seconds(parts[3]),
        "rssBytes": int(parts[4]) * 1024,
        "instantCpuPercent": float(parts[5]),
        "state": parts[6],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pg-host", required=True)
    parser.add_argument("--pg-port", type=int, required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--admin-user", default="gda_v49_phase2b_admin")
    parser.add_argument("--psql", default="psql")
    parser.add_argument("--pgdata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--interval-seconds", type=float, default=5.0)
    parser.add_argument("--max-seconds", type=float, default=5400.0)
    args = parser.parse_args()
    if (
        args.pg_port == 5432 or not args.pg_host.startswith("/")
        or not args.database.startswith("gda_v49_phase2a_")
        or not 1 <= args.interval_seconds <= 30
        or not 60 <= args.max_seconds <= 7200
    ):
        raise MonitorError("MONITOR_CONNECTION_OR_INTERVAL_POLICY")
    pgdata = args.pgdata.resolve()
    output = args.output.resolve()
    summary_path = args.summary.resolve()
    if (
        not pgdata.is_dir() or "gda_v49_phase2b_perf_" not in str(pgdata)
        or not output.parent.is_dir() or not summary_path.parent.is_dir()
    ):
        raise MonitorError("MONITOR_PATH_POLICY")

    started = time.monotonic()
    seen_writer = False
    absent_after_writer = 0
    samples = 0
    max_logical = 0
    max_allocated = 0
    max_database = 0
    max_rss = 0
    max_cpu = 0.0
    with output.open("w", encoding="utf-8") as handle:
        while time.monotonic() - started <= args.max_seconds:
            captured_at = datetime.now(timezone.utc).isoformat()
            database = database_sample(args)
            logical, allocated, file_count = tree_usage(pgdata)
            backends = database["migratorBackends"]
            processes = []
            for backend in backends:
                process = process_sample(int(backend["pid"]))
                if process is not None:
                    processes.append(process)
            writer_now = any(
                backend.get("xactAgeSeconds") is not None and any(
                    token in (backend.get("query") or "")
                    for token in ("gda_stage_", "INSERT INTO", "SET CONSTRAINTS", "ANALYZE ")
                )
                for backend in backends
            )
            seen_writer = seen_writer or writer_now
            absent_after_writer = (
                absent_after_writer + 1 if seen_writer and not backends else 0
            )
            record = {
                "capturedAtUtc": captured_at,
                "elapsedSeconds": round(time.monotonic() - started, 6),
                "pgdataLogicalBytes": logical,
                "pgdataAllocatedBytes": allocated,
                "pgdataFileCount": file_count,
                "database": database,
                "backendProcesses": processes,
                "writerObserved": seen_writer,
            }
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            handle.flush()
            samples += 1
            max_logical = max(max_logical, logical)
            max_allocated = max(max_allocated, allocated)
            max_database = max(max_database, int(database["databaseBytes"]))
            for process in processes:
                max_rss = max(max_rss, int(process.get("rssBytes", 0)))
                max_cpu = max(max_cpu, float(process.get("cpuSeconds", 0)))
            if absent_after_writer >= 3:
                break
            time.sleep(args.interval_seconds)

    summary = {
        "status": "PASS" if seen_writer and absent_after_writer >= 3 else "INCOMPLETE",
        "schema": "gda-v49-phase2b-performance-monitor/v1",
        "database": args.database,
        "sampleIntervalSeconds": args.interval_seconds,
        "sampleCount": samples,
        "writerObserved": seen_writer,
        "writerExitObserved": absent_after_writer >= 3,
        "wallSeconds": round(time.monotonic() - started, 6),
        "peakPgdataLogicalBytes": max_logical,
        "peakPgdataAllocatedBytes": max_allocated,
        "peakDatabaseBytes": max_database,
        "peakBackendRssBytes": max_rss,
        "maxBackendCumulativeCpuSeconds": round(max_cpu, 6),
        "sampleLog": str(output),
    }
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["status"] == "PASS" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (MonitorError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, sort_keys=True))
        raise SystemExit(2)
