#!/usr/bin/env python3
"""Profile the v49 release builder without changing its database semantics.

The caller supplies a fresh, already-replayed database.  This program loads
the deterministic scale fixture, runs the repository-standard ANALYZE set,
captures an expanded plan for the publishable-assignment SQL, then runs the
unchanged v5 builder with nested auto_explain enabled.  It never retries and
never changes statement timeouts or resource settings.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path


ANALYZE_SQL = """
ANALYZE raw.legacy_surface_ledger;
ANALYZE research.corpus_membership;
ANALYZE provenance.canonical_assignment;
ANALYZE provenance.assignment_folder_membership;
ANALYZE provenance.assignment_review_decision;
ANALYZE provenance.assignment_decision_evidence;
"""


EXPANDED_SELECTION_SQL = r"""
EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS, SUMMARY, VERBOSE, FORMAT JSON)
WITH current_assignment AS MATERIALIZED (
  SELECT a.canonical_assignment_id, a.assignment_kind, a.status,
    a.supersedes_assignment_id
  FROM provenance.canonical_assignment a
  WHERE a.assignment_kind='folder_membership'
    AND a.status='accepted'
    AND NOT EXISTS (
      SELECT 1 FROM provenance.canonical_assignment newer
      WHERE newer.supersedes_assignment_id=a.canonical_assignment_id
    )
), effective_decision AS MATERIALIZED (
  SELECT d.assignment_review_decision_id, d.canonical_assignment_id,
    encode(sha256(convert_to(jsonb_build_object(
      'decision',jsonb_build_array(d.assignment_review_decision_id,
        d.canonical_assignment_id,d.outcome,d.supersedes_decision_id),
      'supports',jsonb_agg(jsonb_build_array(e.evidence_item_id,e.evidence_role)
        ORDER BY e.evidence_item_id,e.evidence_role)
    )::text,'UTF8')),'hex')::core.sha256_hex AS decision_snapshot_sha256
  FROM provenance.assignment_review_decision d
  JOIN current_assignment a ON a.canonical_assignment_id=d.canonical_assignment_id
  JOIN provenance.assignment_decision_evidence e
    ON e.assignment_review_decision_id=d.assignment_review_decision_id
   AND e.evidence_role='supports'
  WHERE d.outcome='accept'
    AND NOT EXISTS (
      SELECT 1 FROM provenance.assignment_review_decision newer
      WHERE newer.supersedes_decision_id=d.assignment_review_decision_id
    )
  GROUP BY d.assignment_review_decision_id,d.canonical_assignment_id,
    d.outcome,d.supersedes_decision_id
), assignment_snapshot AS MATERIALIZED (
  SELECT a.canonical_assignment_id,
    encode(sha256(convert_to(jsonb_build_object(
      'assignment',jsonb_build_array(a.canonical_assignment_id,a.assignment_kind,
        a.status,a.supersedes_assignment_id),
      'memberships',jsonb_agg(jsonb_build_array(fm.folder_id,fm.archive_object_id,
        fm.membership_role,fm.member_ordinal)
        ORDER BY fm.folder_id,fm.membership_role,fm.member_ordinal,fm.archive_object_id)
    )::text,'UTF8')),'hex')::core.sha256_hex AS assignment_snapshot_sha256
  FROM current_assignment a
  JOIN provenance.assignment_folder_membership fm
    ON fm.canonical_assignment_id=a.canonical_assignment_id
  GROUP BY a.canonical_assignment_id,a.assignment_kind,a.status,a.supersedes_assignment_id
)
SELECT fm.folder_id,fm.archive_object_id,a.canonical_assignment_id,
  fm.membership_role,fm.member_ordinal,d.assignment_review_decision_id,
  s.assignment_snapshot_sha256,d.decision_snapshot_sha256
FROM current_assignment a
JOIN provenance.assignment_folder_membership fm
  ON fm.canonical_assignment_id=a.canonical_assignment_id
JOIN effective_decision d ON d.canonical_assignment_id=a.canonical_assignment_id
JOIN assignment_snapshot s ON s.canonical_assignment_id=a.canonical_assignment_id
JOIN raw.legacy_surface_ledger l ON l.archive_object_id=fm.archive_object_id
  AND l.migration_batch_id='a0000000-0000-4000-8000-000000000003'
  AND l.import_disposition='accounted'
JOIN research.corpus_membership cm ON cm.archive_object_id=fm.archive_object_id
  AND cm.corpus_version_id='a4000000-0000-4000-8000-000000000002'
  AND cm.disposition='eligible';
"""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(command: list[str], *, env: dict[str, str] | None = None) -> tuple[subprocess.CompletedProcess[str], float]:
    started = time.monotonic()
    result = subprocess.run(command, text=True, capture_output=True, env=env)
    return result, round((time.monotonic() - started) * 1000, 3)


def psql_base(args: argparse.Namespace) -> list[str]:
    return [
        args.psql, "-X", "-v", "ON_ERROR_STOP=1", "-h", args.host,
        "-p", args.port, "-d", args.database,
    ]


def require_ok(result: subprocess.CompletedProcess[str], label: str) -> None:
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed ({result.returncode}): {result.stderr}")


def scalar_json(args: argparse.Namespace, sql: str) -> dict[str, object]:
    result, _ = run(psql_base(args) + ["-Atq", "-c", sql])
    require_ok(result, "resource snapshot")
    return json.loads(result.stdout.strip())


def resource_snapshot(args: argparse.Namespace) -> dict[str, object]:
    return scalar_json(args, """
      SELECT jsonb_build_object(
        'capturedAt',clock_timestamp(),
        'database',current_database(),
        'otherDatabaseSessions',(SELECT count(*) FROM pg_stat_activity
          WHERE datname=current_database() AND pid<>pg_backend_pid()),
        'activeWriters',(SELECT count(*) FROM pg_stat_activity
          WHERE datname=current_database() AND pid<>pg_backend_pid()
            AND state='active' AND query !~* '^\\s*(select|show|explain)'),
        'xactCommit',xact_commit,'xactRollback',xact_rollback,
        'blksRead',blks_read,'blksHit',blks_hit,
        'tempFiles',temp_files,'tempBytes',temp_bytes,
        'walLsn',pg_current_wal_lsn()::text,
        'settings',jsonb_build_object(
          'serverVersion',current_setting('server_version'),
          'sharedBuffers',current_setting('shared_buffers'),
          'workMem',current_setting('work_mem'),
          'maintenanceWorkMem',current_setting('maintenance_work_mem'),
          'effectiveCacheSize',current_setting('effective_cache_size'),
          'jit',current_setting('jit'),
          'trackIoTiming',current_setting('track_io_timing'),
          'maxParallelWorkersPerGather',current_setting('max_parallel_workers_per_gather')))
      FROM pg_stat_database WHERE datname=current_database();
    """)


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
    parser.add_argument("--auto-explain-min-ms", default="1")
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    if args.objects not in {32, 1000, 2000, 4000, 8000, 15923}:
        parser.error("unauthorized scale")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    fixture = args.repo / "database/fixtures/phase2s_scale_snapshot.sql"
    before = resource_snapshot(args)

    fixture_result, fixture_ms = run(psql_base(args) + [
        "-v", f"object_count={args.objects}",
        "-v", f"membership_count={args.memberships}",
        "-v", f"scale_tag={args.tag}",
        "-c", "BEGIN", "-f", str(fixture), "-c", "COMMIT",
    ])
    require_ok(fixture_result, "fixture")

    analyze_result, analyze_ms = run(psql_base(args) + ["-Atq", "-c", ANALYZE_SQL])
    require_ok(analyze_result, "analyze")

    plan_result, selection_plan_ms = run(psql_base(args) + ["-Atq", "-c", EXPANDED_SELECTION_SQL])
    require_ok(plan_result, "expanded selection plan")
    selection_plan = json.loads(plan_result.stdout.strip())[0]
    selection_plan_bytes = (json.dumps(selection_plan, sort_keys=True, indent=2) + "\n").encode()
    (args.output_dir / "expanded-selection.plan.json").write_bytes(selection_plan_bytes)

    auto_commands = [
        "LOAD 'auto_explain'",
        "SET client_min_messages=log",
        "SET track_io_timing=on",
        f"SET auto_explain.log_min_duration={args.auto_explain_min_ms}",
        "SET auto_explain.log_nested_statements=on",
        "SET auto_explain.log_analyze=on",
        "SET auto_explain.log_buffers=on",
        "SET auto_explain.log_wal=on",
        "SET auto_explain.log_timing=on",
        "SET auto_explain.log_verbose=on",
        "SET auto_explain.log_format=json",
        r"\timing on",
    ]
    builder_command = psql_base(args)
    for command in auto_commands:
        builder_command.extend(["-c", command])
    builder_command.extend([
        "-v", f"object_count={args.objects}",
        "-v", f"membership_count={args.memberships}",
        "-v", f"scale_tag={args.tag}",
        "-v", f"release_id={args.release_id}",
        "-v", f"event_id={args.event_id}",
        "-v", f"candidate_event_id={args.candidate_event_id}",
        "-f", str(args.repo / "database/tests/009_release_projection_snapshot_performance_scale.sql"),
    ])
    builder_result, builder_ms = run(builder_command, env=os.environ.copy())
    (args.output_dir / "builder.stdout.txt").write_text(builder_result.stdout)
    (args.output_dir / "builder.auto-explain.log").write_text(builder_result.stderr)
    require_ok(builder_result, "instrumented builder")

    after = resource_snapshot(args)
    summary = {
        "format": "v49-db-closure-profile-v1",
        "database": args.database,
        "objects": args.objects,
        "memberships": args.memberships,
        "fixtureWallMs": fixture_ms,
        "analyzeWallMs": analyze_ms,
        "expandedSelectionWallMs": selection_plan_ms,
        "expandedSelectionExecutionMs": selection_plan.get("Execution Time"),
        "instrumentedBuilderWallMs": builder_ms,
        "fixtureStdoutSha256": sha256(fixture_result.stdout.encode()),
        "fixtureStderrSha256": sha256(fixture_result.stderr.encode()),
        "analyzeStdoutSha256": sha256(analyze_result.stdout.encode()),
        "analyzeStderrSha256": sha256(analyze_result.stderr.encode()),
        "expandedSelectionPlanSha256": sha256(selection_plan_bytes),
        "builderStdoutSha256": sha256(builder_result.stdout.encode()),
        "builderAutoExplainSha256": sha256(builder_result.stderr.encode()),
        "resourceBefore": before,
        "resourceAfter": after,
    }
    (args.output_dir / "profile-summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
