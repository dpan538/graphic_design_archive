#!/usr/bin/env python3
"""Verify no-op replay and same-batch conflicting-binding denial.

Run only after one committed Phase 2B import.  The harness performs no direct
SQL writes: it invokes the production importer twice and captures complete
read-only verifier reports before and after both probes.  The first invocation
must be the documented deterministic no-op.  The second invokes the same
``existing_batch`` comparison with an in-memory conflicting mapping binding;
it must fail before a population transaction is opened.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
IMPORTER = ROOT / "database/data-migrations/v48-to-v49/import.py"
VERIFIER = ROOT / "database/data-migrations/v48-to-v49/verify.py"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False)


def import_command(args: argparse.Namespace, *extra: str) -> list[str]:
    return [
        sys.executable, str(IMPORTER), "--stage-dir", str(args.stage_dir),
        "--pg-host", args.pg_host, "--pg-port", str(args.pg_port),
        "--database", args.database, "--admin-user", args.admin_user, *extra,
    ]


def verify_command(args: argparse.Namespace, output: Path) -> list[str]:
    return [
        sys.executable, str(VERIFIER), "--pg-host", args.pg_host,
        "--pg-port", str(args.pg_port), "--database", args.database,
        "--admin-user", args.admin_user, "--output", str(output),
    ]


def select_conflicting_hash(stage_dir: Path) -> str:
    manifest = json.loads((stage_dir / "staging-manifest.json").read_text(encoding="utf-8"))
    current = manifest["mapping"]["sha256"]
    candidate = "0" * 64
    if candidate == current:
        candidate = "f" * 64
    return candidate


def comparable(report: dict[str, object]) -> dict[str, object]:
    return {
        "status": report["status"],
        "schemaShaBefore": report["schemaShaBefore"],
        "schemaShaAfter": report["schemaShaAfter"],
        "schemaDrift": report["schemaDrift"],
        "countVectorSha256": report["countVectorSha256"],
        "stableKeySetSha256": report["stableKeySetSha256"],
        "normalizedContentSha256": report["normalizedContentSha256"],
        "metrics": report["metrics"],
        "countVector": report["countVector"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-dir", type=Path, required=True)
    parser.add_argument("--pg-host", required=True)
    parser.add_argument("--pg-port", type=int, required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--admin-user", default="gda_v49_phase2b_admin")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.pg_port == 5432 or not args.pg_host.startswith("/") or not args.database.startswith("gda_v49_phase2a_"):
        raise RuntimeError("DISPOSABLE_CONNECTION_POLICY_VIOLATION")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    before_path = args.output.parent / (args.output.stem + ".before.json")
    after_path = args.output.parent / (args.output.stem + ".after.json")
    for path in (before_path, after_path):
        path.unlink(missing_ok=True)
    before_run = run(verify_command(args, before_path))
    if before_run.returncode:
        raise RuntimeError("IDEMPOTENCY_BEFORE_VERIFY_FAILED:" + before_run.stderr[-2000:])
    before = json.loads(before_path.read_text(encoding="utf-8"))

    noop = run(import_command(args))
    if noop.returncode or '"status": "IDEMPOTENT_NOOP"' not in noop.stdout:
        raise RuntimeError("IDEMPOTENT_NOOP_FAILED:" + noop.stdout[-1000:] + noop.stderr[-2000:])

    collision_hash = select_conflicting_hash(args.stage_dir)
    collision = run(import_command(args, "--test-batch-mapping-sha", collision_hash))
    if collision.returncode == 0 or "BATCH_ID_REUSE_HASH_MISMATCH" not in collision.stderr:
        raise RuntimeError("BATCH_MAPPING_COLLISION_NOT_DENIED:" + collision.stdout[-1000:] + collision.stderr[-2000:])

    after_run = run(verify_command(args, after_path))
    if after_run.returncode:
        raise RuntimeError("IDEMPOTENCY_AFTER_VERIFY_FAILED:" + after_run.stderr[-2000:])
    after = json.loads(after_path.read_text(encoding="utf-8"))
    if comparable(before) != comparable(after):
        raise RuntimeError("IDEMPOTENCY_OR_COLLISION_CHANGED_CONTENT")

    payload = {
        "status": "PASS",
        "database": args.database,
        "idempotentReplay": True,
        "sameBatchDifferentMappingDenied": True,
        "partialImportResidue": 0,
        "currentPointerAdvanced": False,
        "releaseSealed": False,
        "before": comparable(before),
        "after": comparable(after),
        "noopStdout": noop.stdout.strip(),
        "collisionError": "BATCH_ID_REUSE_HASH_MISMATCH",
    }
    args.output.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "idempotentReplay": True, "sameBatchDifferentMappingDenied": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, json.JSONDecodeError, KeyError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
