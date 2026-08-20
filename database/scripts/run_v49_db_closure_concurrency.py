#!/usr/bin/env python3
"""Run the bounded v5 concurrency matrix in one controller process.

The harness opens multiple PostgreSQL sessions only for this dedicated test.
It never starts a second cluster or importer, and each builder invocation is a
single SQL transaction using the public publisher entry point.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def run(command: list[str], *, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, input=stdin, text=True, capture_output=True, timeout=150
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--psql", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if not args.host.startswith("/") or args.port == "5432":
        parser.error("isolated non-default Unix socket required")
    if not args.database.startswith("gda_v49_phase2a_"):
        parser.error("database prefix rejected")

    harness_started = time.monotonic()
    base = [
        args.psql, "-X", "-v", "ON_ERROR_STOP=1", "-h", args.host,
        "-p", args.port, "-d", args.database, "-Atq",
    ]
    fixture = run(base + [
        "-v", "object_count=32", "-v", "membership_count=128",
        "-v", "scale_tag=concurrency", "-c", "BEGIN",
        "-f", str(args.repo / "database/fixtures/phase2s_scale_snapshot.sql"),
        "-c", "COMMIT",
    ])
    if fixture.returncode:
        raise RuntimeError(f"fixture failed: {fixture.stderr}")

    setup_sql = r"""
BEGIN;
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.create_research_release('97000000-0000-4000-8000-000000000001','v49-concurrent-same','schema-v49.0','model-v49.0','97000000-0000-4000-8000-000000000002',repeat('1',64));
SELECT release.create_research_release('97000000-0000-4000-8000-000000000010','v49-concurrent-diff-a','schema-v49.0','model-v49.0','97000000-0000-4000-8000-000000000011',repeat('1',64));
SELECT release.create_research_release('97000000-0000-4000-8000-000000000020','v49-concurrent-diff-b','schema-v49.0','model-v49.0','97000000-0000-4000-8000-000000000021',repeat('1',64));
SELECT release.create_research_release('97000000-0000-4000-8000-000000000030','v49-concurrent-overlap','schema-v49.0','model-v49.0','97000000-0000-4000-8000-000000000031',repeat('1',64));
RESET SESSION AUTHORIZATION;
COMMIT;
"""
    setup = run(base, stdin=setup_sql)
    if setup.returncode:
        raise RuntimeError(f"release setup failed: {setup.stderr}")

    def builder_sql(release_id: str, event_id: str, event_sha: str) -> str:
        return f"""
BEGIN ISOLATION LEVEL SERIALIZABLE;
SET LOCAL statement_timeout='120s';
SET LOCAL lock_timeout='30s';
SET LOCAL application_name='gda_v49_concurrency_builder';
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
DO $body$
DECLARE v_state text := '00000'; v_message text;
BEGIN
  BEGIN
    PERFORM release.build_research_launch_snapshot_v5(
      '{release_id}','a0000000-0000-4000-8000-000000000003',
      'a8000000-0000-4000-8000-000000000010','{event_id}',repeat('{event_sha}',64));
  EXCEPTION WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS v_state=RETURNED_SQLSTATE,v_message=MESSAGE_TEXT;
  END;
  PERFORM set_config('gda.concurrency_state',v_state,false);
  PERFORM set_config('gda.concurrency_message',coalesce(v_message,''),false);
END
$body$;
RESET SESSION AUTHORIZATION;
COMMIT;
SELECT jsonb_build_object(
  'backendPid',pg_backend_pid(),
  'state',current_setting('gda.concurrency_state'),
  'message',nullif(current_setting('gda.concurrency_message'),''));
"""

    def builder(release_id: str, event_id: str, event_sha: str) -> dict[str, object]:
        result = run(base, stdin=builder_sql(release_id, event_id, event_sha))
        lines = [line for line in result.stdout.splitlines() if line.startswith("{")]
        payload = json.loads(lines[-1]) if lines else {
            "state": "HARNESS_ERROR", "message": result.stderr.strip()
        }
        payload["psqlExitCode"] = result.returncode
        return payload

    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=2) as pool:
        same = list(pool.map(
            lambda values: builder(*values),
            [
                ("97000000-0000-4000-8000-000000000001", "97000000-0000-4000-8000-000000000003", "2"),
                ("97000000-0000-4000-8000-000000000001", "97000000-0000-4000-8000-000000000004", "3"),
            ],
        ))
    same_ms = round((time.monotonic() - started) * 1000, 3)
    states = sorted(str(item["state"]) for item in same)
    same_state = run(base + ["-c", r"""
      SELECT jsonb_build_object(
        'releaseState',(SELECT release_state FROM release.research_release WHERE research_release_id='97000000-0000-4000-8000-000000000001'),
        'receiptCount',(SELECT count(*) FROM release.research_launch_build_receipt_v3 WHERE research_release_id='97000000-0000-4000-8000-000000000001'),
        'protocolCount',(SELECT count(*) FROM release.research_launch_protocol_v5 WHERE research_release_id='97000000-0000-4000-8000-000000000001'),
        'candidateEventCount',(SELECT count(*) FROM audit.research_release_event WHERE research_release_id='97000000-0000-4000-8000-000000000001' AND to_state='candidate'));
    """])
    same_db = json.loads(same_state.stdout.strip())
    same_pass = (
        states.count("00000") == 1
        and len(states) == 2
        and states[0] == "00000"
        and states[1] in {"40001", "55000"}
        and same_db == {
            "releaseState": "candidate", "receiptCount": 1,
            "protocolCount": 1, "candidateEventCount": 1,
        }
    )

    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=2) as pool:
        different = list(pool.map(
            lambda values: builder(*values),
            [
                ("97000000-0000-4000-8000-000000000010", "97000000-0000-4000-8000-000000000012", "4"),
                ("97000000-0000-4000-8000-000000000020", "97000000-0000-4000-8000-000000000022", "5"),
            ],
        ))
    different_ms = round((time.monotonic() - started) * 1000, 3)
    different_pass = all(item["state"] == "00000" for item in different)

    writer_sql = r"""
BEGIN ISOLATION LEVEL SERIALIZABLE;
SET LOCAL statement_timeout='120s';
SET LOCAL lock_timeout='30s';
SET LOCAL application_name='gda_v49_concurrency_writer';
SET ROLE gda_v49_phase2a_schema_owner;
INSERT INTO provenance.canonical_assignment VALUES(
  '97000000-0000-4000-8000-000000000040','folder_membership','accepted',NULL,'2026-08-20T00:00:00Z');
INSERT INTO provenance.assignment_folder_membership VALUES(
  '97000000-0000-4000-8000-000000000040','a8000000-0000-4000-8000-000000000004',
  'a2000000-0000-4000-8000-000001000001','concurrent_addition',999);
INSERT INTO provenance.assignment_review_decision VALUES(
  '97000000-0000-4000-8000-000000000041','97000000-0000-4000-8000-000000000040',
  'accept','concurrency-writer','committed after builder snapshot',NULL,'2026-08-20T00:00:00Z');
INSERT INTO provenance.assignment_decision_evidence VALUES(
  '97000000-0000-4000-8000-000000000041','a3000000-0000-4000-8000-000000000003','supports');
SELECT pg_sleep(3);
RESET ROLE;
COMMIT;
"""

    def wait_for_writer_barrier() -> dict[str, object]:
        deadline = time.monotonic() + 15
        barrier_sql = r"""
          SELECT jsonb_build_object(
            'backendPid',pid,'state',state,'waitEventType',wait_event_type,
            'waitEvent',wait_event,'applicationName',application_name)
          FROM pg_stat_activity
          WHERE datname=current_database()
            AND application_name='gda_v49_concurrency_writer'
            AND state='active'
            AND wait_event_type='Timeout'
            AND wait_event='PgSleep';
        """
        while time.monotonic() < deadline:
            observed = run(base + ["-c", barrier_sql])
            lines = [line for line in observed.stdout.splitlines() if line.startswith("{")]
            if observed.returncode == 0 and lines:
                return json.loads(lines[-1])
            time.sleep(0.05)
        raise RuntimeError("writer barrier not observed within 15 seconds")

    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=2) as pool:
        writer_future = pool.submit(run, base, stdin=writer_sql)
        writer_barrier = wait_for_writer_barrier()
        overlap_future = pool.submit(
            builder,
            "97000000-0000-4000-8000-000000000030",
            "97000000-0000-4000-8000-000000000032", "6",
        )
        writer_result = writer_future.result()
        overlap_result = overlap_future.result()
    overlap_ms = round((time.monotonic() - started) * 1000, 3)
    overlap_state = run(base + ["-c", r"""
      SELECT jsonb_build_object(
        'canonicalAdditionCount',(SELECT count(*) FROM provenance.canonical_assignment WHERE canonical_assignment_id='97000000-0000-4000-8000-000000000040'),
        'projectedMembershipCount',(SELECT count(*) FROM release.research_folder_membership_projection_v3 WHERE research_release_id='97000000-0000-4000-8000-000000000030'),
        'releaseState',(SELECT release_state FROM release.research_release WHERE research_release_id='97000000-0000-4000-8000-000000000030'),
        'receiptCount',(SELECT count(*) FROM release.research_launch_build_receipt_v3 WHERE research_release_id='97000000-0000-4000-8000-000000000030'));
    """])
    overlap_db = json.loads(overlap_state.stdout.strip())
    overlap_pass = (
        writer_result.returncode == 0
        and overlap_result["state"] in {"00000", "40001"}
        and (
            overlap_result["state"] == "40001"
            or overlap_db == {
                "canonicalAdditionCount": 1, "projectedMembershipCount": 128,
                "releaseState": "candidate", "receiptCount": 1,
            }
        )
    )

    payload = {
        "format": "v49-db-closure-concurrency-v1",
        "database": args.database,
        "controllerProcessCount": 1,
        "postgresSessionCountPeak": 2,
        "postgresSessionRoles": [
            "publisher-builder", "schema-owner-canonical-writer", "read-only-barrier"
        ],
        "timeouts": {
            "statementSeconds": 120,
            "lockSeconds": 30,
            "barrierSeconds": 15,
            "wholeHarnessSeconds": 300,
        },
        "sameRelease": {
            "results": same, "databaseState": same_db,
            "wallMs": same_ms, "pass": same_pass,
        },
        "differentRelease": {
            "results": different, "wallMs": different_ms,
            "pass": different_pass,
        },
        "canonicalWriterOverlap": {
            "writerBarrier": writer_barrier,
            "writerExitCode": writer_result.returncode,
            "writerStderr": writer_result.stderr,
            "builderResult": overlap_result,
            "databaseState": overlap_db,
            "acceptedOutcome": "serialization_failure_or_consistent_prestate",
            "wallMs": overlap_ms,
            "pass": overlap_pass,
        },
        "wholeHarnessMs": round((time.monotonic() - harness_started) * 1000, 3),
        "pass": same_pass and different_pass and overlap_pass,
    }
    if payload["wholeHarnessMs"] > 300000:
        payload["pass"] = False
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
