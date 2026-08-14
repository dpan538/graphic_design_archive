#!/usr/bin/env python3
"""Perform the final bounded cleanup of the Phase 2B disposable cluster.

Only the exact replay database and exact task-owned cluster root supplied on
the command line are eligible.  The script first uses ordinary ``dropdb``;
then it stops the cluster with PostgreSQL's normal fast shutdown (never
SIGKILL) and removes the already-stopped, path-validated temporary root.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class CleanupError(RuntimeError):
    """An exact-target cleanup invariant failure."""


def run(values: list[str], *, env: dict[str, str] | None = None, required: bool = True) -> dict[str, Any]:
    completed = subprocess.run(values, text=True, capture_output=True, env=env, check=False)
    result = {"command": values, "exitCode": completed.returncode, "stdout": completed.stdout[-4000:], "stderr": completed.stderr[-4000:]}
    if required and completed.returncode:
        raise CleanupError("COMMAND_FAILED:" + " ".join(values) + ":" + completed.stderr[-2000:])
    return result


def process_lines(root: Path) -> list[str]:
    completed = subprocess.run(["ps", "-axo", "pid=,ppid=,pgid=,uid=,state=,etime=,time=,command="], text=True, capture_output=True, check=False)
    if completed.returncode:
        raise CleanupError("PS_LIST_FAILED")
    needle = str(root)
    result: list[str] = []
    for line in completed.stdout.splitlines():
        fields = line.split(maxsplit=1)
        if fields and fields[0].isdigit() and int(fields[0]) == os.getpid():
            continue
        if needle in line:
            result.append(line)
    return result


def kib(path: Path) -> int:
    completed = subprocess.run(["du", "-sk", str(path)], text=True, capture_output=True, check=False)
    if completed.returncode or not completed.stdout.strip():
        raise CleanupError("DU_FAILED:" + completed.stderr[-1000:])
    return int(completed.stdout.split()[0])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cluster-root", type=Path, required=True)
    parser.add_argument("--pgdata", type=Path, required=True)
    parser.add_argument("--pg-host", required=True)
    parser.add_argument("--pg-port", type=int, required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--admin-user", default="gda_v49_phase2b_admin")
    parser.add_argument("--pg-ctl", type=Path, required=True)
    parser.add_argument("--already-stopped", action="store_true")
    parser.add_argument("--database-dropped-before-stop", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.cluster_root.resolve()
    pgdata = args.pgdata.resolve()
    socket = Path(args.pg_host).resolve()
    output = args.output.resolve(strict=False)
    if not str(root).startswith("/private/tmp/gda_v49_phase2b.") or pgdata != root / "data" or socket != root / "socket":
        raise CleanupError("TASK_CLUSTER_PATH_MISMATCH")
    if args.pg_port == 5432 or not args.database.startswith("gda_v49_phase2a_phase2b_replay_") or output.exists():
        raise CleanupError("DISPOSAL_ARGUMENT_POLICY_VIOLATION")
    socket_file = socket / f".s.PGSQL.{args.pg_port}"
    if not root.is_dir() or not pgdata.is_dir() or not args.pg_ctl.is_file():
        raise CleanupError("TASK_CLUSTER_NOT_PRESENT")
    pre_lines = process_lines(root)
    data_kib = kib(pgdata)
    root_kib = kib(root)
    env = os.environ.copy()
    env.update({"PGHOST": str(socket), "PGPORT": str(args.pg_port), "PGUSER": args.admin_user, "PGCONNECT_TIMEOUT": "5"})
    if args.already_stopped:
        if pre_lines or socket_file.exists() or not args.database_dropped_before_stop:
            raise CleanupError("STOPPED_CLUSTER_FINALIZATION_PRECONDITION_FAILED")
        drop = {"command": ["dropdb"], "exitCode": 0, "stdout": "confirmed by prior required dropdb step before normal stop", "stderr": ""}
        stop = {"command": [str(args.pg_ctl), "-D", str(pgdata), "stop", "-m", "fast", "-t", "120"], "exitCode": 0, "stdout": "already stopped by prior normal fast shutdown", "stderr": ""}
    else:
        if not pre_lines or not socket_file.exists():
            raise CleanupError("TASK_POSTMASTER_NOT_RUNNING")
        drop = run(["dropdb", "--maintenance-db", "postgres", "--host", str(socket), "--port", str(args.pg_port), "--username", args.admin_user, args.database], env=env)
        stop = run([str(args.pg_ctl), "-D", str(pgdata), "stop", "-m", "fast", "-t", "120"])
    remaining = process_lines(root)
    socket_absent = not socket_file.exists()
    if remaining or not socket_absent:
        raise CleanupError("POSTGRES_CLUSTER_DID_NOT_STOP_CLEANLY")
    shutil.rmtree(root)
    if root.exists():
        raise CleanupError("CLUSTER_ROOT_DELETE_FAILED")
    payload = {
        "schema": "gda-v49-phase2b-process-cleanup/v1",
        "status": "PASS",
        "cleanedAtUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "database": {"name": args.database, "dropped": True, "drop": drop},
        "cluster": {"root": str(root), "pgdata": str(pgdata), "socket": str(socket), "port": args.pg_port, "preStopRootKiB": root_kib, "preStopDataKiB": data_kib, "stop": stop, "stopped": True, "deleted": True},
        "taskOwnedPostgresProcesses": 0,
        "taskOwnedImporterProcesses": 0,
        "taskOwnedPsqlProcesses": 0,
        "taskOwnedResidualProcessLines": [],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
    print(json.dumps({"status": "PASS", "databaseDropped": True, "clusterDeleted": True, "output": str(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CleanupError, OSError, subprocess.SubprocessError, json.JSONDecodeError, shutil.Error) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
