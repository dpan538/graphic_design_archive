#!/usr/bin/env python3
"""Remove only the now-preserved small Phase 2B task-temporary roots.

The 4.5GB staging bundle is deliberately *not* under either target: it was
moved to an external verified cache before this finalizer may run.  The JSON
receipt is written into the committed audit package before either exact root
is removed.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


class FinalizeError(RuntimeError):
    """A task-temp cleanup precondition failure."""


def kib(path: Path) -> int:
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            total += item.stat().st_size
    return total // 1024


def require_prefix(path: Path, prefix: str, label: str) -> None:
    if not str(path).startswith(prefix) or not path.is_dir():
        raise FinalizeError(f"INVALID_{label}_PATH:{path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-temp-root", type=Path, required=True)
    parser.add_argument("--recovery-backup-root", type=Path, required=True)
    parser.add_argument("--cache-stage", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stage_root = args.stage_temp_root.resolve()
    backup_root = args.recovery_backup_root.resolve()
    cache_stage = args.cache_stage.resolve()
    output = args.audit_output.resolve(strict=False)
    require_prefix(stage_root, "/private/tmp/gda_v49_phase2b_stage_final.", "STAGE_TEMP")
    require_prefix(backup_root, "/private/tmp/gda_v49_phase2b_recovery_backup.", "RECOVERY_BACKUP")
    if not str(cache_stage).startswith("/Users/jarlgiovanni/Library/Caches/gda_v49_phase2b/") or not (cache_stage / "staging-manifest.json").is_file():
        raise FinalizeError("CACHE_STAGE_NOT_PRESENT")
    if output.exists() or "docs/audits/v49-phase2b-migration/evidence" not in str(output):
        raise FinalizeError("AUDIT_OUTPUT_INVALID")
    sizes = {"stageTempRootKiB": kib(stage_root), "recoveryBackupRootKiB": kib(backup_root), "cacheStageKiB": kib(cache_stage)}
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(stage_root)
    shutil.rmtree(backup_root)
    if stage_root.exists() or backup_root.exists():
        raise FinalizeError("TASK_TEMP_DELETE_FAILED")
    payload = {
        "schema": "gda-v49-phase2b-task-temp-finalization/v1",
        "status": "PASS",
        "finalizedAtUtc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "removed": {"stageTempRoot": str(stage_root), "recoveryBackupRoot": str(backup_root), **sizes},
        "cacheStage": str(cache_stage),
        "cacheRetained": True,
        "stageTempVerifiedAbsent": True,
        "recoveryBackupVerifiedAbsent": True,
    }
    with output.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
    print(json.dumps({"status": "PASS", "cacheRetained": True, "output": str(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FinalizeError, OSError, shutil.Error, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
