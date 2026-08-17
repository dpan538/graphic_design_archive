#!/usr/bin/env python3
"""Bounded Phase 2S-P profiler for a pre-created disposable PostgreSQL 16 DB.

The caller supplies only a Unix socket/port/database.  The harness loads a
deterministic fixture, runs ANALYZE, records JSON EXPLAIN for the source leaf
selection, then records the v5 builder wall time and canonical result digest.
It deliberately has no retry loop and never changes timeouts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path


def run(psql: str, host: str, port: str, database: str, sql: str) -> str:
    result = subprocess.run(
        [psql, "-X", "-v", "ON_ERROR_STOP=1", "-h", host, "-p", port, "-d", database, "-Atq", "-c", sql],
        check=True, text=True, capture_output=True,
    )
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--psql", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--objects", required=True, type=int)
    parser.add_argument("--memberships", required=True, type=int)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--candidate-event-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    fixture_path = args.repo / "database/fixtures/phase2s_scale_snapshot.sql"
    fixture_started = time.monotonic()
    fixture = subprocess.run(
        [args.psql, "-X", "-v", "ON_ERROR_STOP=1", "-h", args.host, "-p", args.port, "-d", args.database,
         "-v", f"object_count={args.objects}", "-v", f"membership_count={args.memberships}",
         "-v", f"scale_tag={args.tag}", "-c", "BEGIN", "-f", str(fixture_path), "-c", "COMMIT"],
        check=True, text=True, capture_output=True,
    )
    analyze_started = time.monotonic()
    run(args.psql, args.host, args.port, args.database, """
      ANALYZE raw.legacy_surface_ledger; ANALYZE research.corpus_membership;
      ANALYZE provenance.canonical_assignment; ANALYZE provenance.assignment_folder_membership;
      ANALYZE provenance.assignment_review_decision; ANALYZE provenance.assignment_decision_evidence;
    """)
    plan_sql = """
EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS, SUMMARY, FORMAT JSON)
SELECT * FROM release.research_launch_publishable_folder_assignments_v5(
  'a0000000-0000-4000-8000-000000000003',
  'a4000000-0000-4000-8000-000000000002');
"""
    plan_started = time.monotonic()
    plan_raw = run(args.psql, args.host, args.port, args.database, plan_sql)
    plan = json.loads(plan_raw)[0]
    plan_path = args.output.with_suffix(".plan.json")
    plan_path.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n")
    psql_file = args.repo / "database/tests/009_release_projection_snapshot_performance_scale.sql"
    env = os.environ.copy()
    command = [
        args.psql, "-X", "-v", "ON_ERROR_STOP=1", "-h", args.host, "-p", args.port, "-d", args.database,
        "-v", f"object_count={args.objects}", "-v", f"membership_count={args.memberships}",
        "-v", f"scale_tag={args.tag}", "-v", f"release_id={args.release_id}",
        "-v", f"event_id={args.event_id}", "-v", f"candidate_event_id={args.candidate_event_id}",
        "-f", str(psql_file),
    ]
    builder_started = time.monotonic()
    result = subprocess.run(command, text=True, capture_output=True, env=env)
    elapsed_ms = round((time.monotonic() - builder_started) * 1000, 3)
    payload = {
        "scale": args.objects,
        "membershipCount": args.memberships,
        "fixtureWallMs": round((analyze_started - fixture_started) * 1000, 3),
        "analyzeWallMs": round((plan_started - analyze_started) * 1000, 3),
        "profilePlanWallMs": round((builder_started - plan_started) * 1000, 3),
        "builderTransactionWallMs": elapsed_ms,
        "exitCode": result.returncode,
        "stdoutSha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
        "stderrSha256": hashlib.sha256(result.stderr.encode()).hexdigest(),
        "planSha256": hashlib.sha256(plan_path.read_bytes()).hexdigest(),
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    args.output.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
