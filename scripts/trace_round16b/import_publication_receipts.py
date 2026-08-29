#!/usr/bin/env python3
"""Validate and import prior external checkpoint-publication receipts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path


BRANCH = "codex/trace-v49-exploration-higher-order-association-closure-round16b"
MAIN_SHA = "8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    manifest_path = args.manifest.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    rows: list[dict[str, str]] = []
    previous_remote = "ABSENT"
    for index, source in enumerate(args.receipt, 1):
        source = source.resolve()
        payload = source.read_bytes()
        receipt = json.loads(payload)
        attempt_id = str(receipt.get("attempt_id", source.stem))
        target = output_dir / f"{index:03d}-{attempt_id}.json"
        target.write_bytes(payload)
        checks = {
            "status_pass": receipt.get("status") == "PASS",
            "branch_exact": receipt.get("branch") == BRANCH,
            "main_before_exact": receipt.get("remote_main_before") == MAIN_SHA,
            "main_after_exact": receipt.get("remote_main_after") == MAIN_SHA,
            "remote_chain_exact": receipt.get("remote_branch_before") == previous_remote,
            "remote_after_equals_local": receipt.get("remote_branch_after") == receipt.get("local_head_sha"),
            "force_push_false": receipt.get("receipt", {}).get("FORCE_PUSH_USED") is False,
            "history_rewritten_false": receipt.get("receipt", {}).get("HISTORY_REWRITTEN") is False,
            "rollback_tag_false": receipt.get("receipt", {}).get("ROLLBACK_TAG_PUSHED") is False,
            "deployment_false": receipt.get("receipt", {}).get("DEPLOYMENT_PERFORMED") is False,
            "unrelated_ref_difference_zero": receipt.get("unrelated_remote_ref_difference_count") == 0,
        }
        failures.extend(f"{attempt_id}:{key}" for key, passed in checks.items() if not passed)
        previous_remote = str(receipt.get("remote_branch_after", "ABSENT"))
        rows.append(
            {
                "ordinal": str(index),
                "attempt_id": attempt_id,
                "checkpoint_id": str(receipt.get("checkpoint_id", "")),
                "source_path": str(source),
                "copied_path": target.name,
                "sha256": sha256_bytes(payload),
                "local_head_sha": str(receipt.get("local_head_sha", "")),
                "remote_before_sha": str(receipt.get("remote_branch_before", "")),
                "remote_after_sha": str(receipt.get("remote_branch_after", "")),
                "remote_main_after_sha": str(receipt.get("remote_main_after", "")),
                "force_push_used": str(receipt.get("receipt", {}).get("FORCE_PUSH_USED")).lower(),
                "status": str(receipt.get("status", "")),
            }
        )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO(newline="")
    fieldnames = list(rows[0]) if rows else []
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, dialect="excel-tab", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    manifest_path.write_text(buffer.getvalue(), encoding="utf-8")
    print(json.dumps({"status": "PASS" if not failures else "FAIL", "receipt_count": len(rows), "failure_codes": failures}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
