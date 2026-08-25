#!/usr/bin/env python3
"""Rebuild the v49 active-script ledgers from the merge index."""

from __future__ import annotations

import csv
import io
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
ALLOWLIST_DIR = ROOT / "docs/maintenance"
RELEASE_LEDGER = (
    ROOT
    / "docs/releases/v49/round11-round12-main-integration-20260825"
    / "05_ALLOWLIST_RECONCILIATION.tsv"
)
ROUND12_SHA = "fc11f033d2fcdbb98130879cdbd3e4a52890e5d2"
JSON_PATH = "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.json"
FIELDS = [
    "path",
    "category",
    "current_runtime_required",
    "current_api_required",
    "current_database_required",
    "current_ci_required",
    "retained_audit_role",
    "decision",
]


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout


def main() -> None:
    tracked = [line for line in git("ls-files", "scripts").splitlines() if line]
    source = json.loads(git("show", f"{ROUND12_SHA}:{JSON_PATH}"))
    source_rows = source["scripts"]
    source_by_path = {row["path"]: row for row in source_rows}

    duplicate_tracked = len(tracked) - len(set(tracked))
    duplicate_source = len(source_rows) - len(source_by_path)
    missing = sorted(set(tracked) - set(source_by_path))
    extra = sorted(set(source_by_path) - set(tracked))
    if duplicate_tracked or duplicate_source or missing or extra:
        raise SystemExit(
            "allowlist reconciliation failed: "
            f"duplicate_tracked={duplicate_tracked} duplicate_source={duplicate_source} "
            f"missing={missing} extra={extra}"
        )

    rows = [source_by_path[path] for path in sorted(tracked)]
    allowed_decisions = {"KEEP_ACTIVE", "DOCUMENTED_ALLOWLIST"}
    unknown = sum(
        1
        for row in rows
        if not row.get("category") or row.get("decision") not in allowed_decisions
    )
    if unknown:
        raise SystemExit(f"unknown classification count: {unknown}")

    payload = {
        "format": "gda-v49-active-script-allowlist/v1",
        "scriptCount": len(rows),
        "unknownClassificationCount": unknown,
        "scripts": rows,
    }
    (ALLOWLIST_DIR / "V49_ACTIVE_SCRIPT_ALLOWLIST.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )

    csv_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(csv_buffer, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row[field] for field in FIELDS})
    (ALLOWLIST_DIR / "V49_ACTIVE_SCRIPT_ALLOWLIST.csv").write_text(
        csv_buffer.getvalue(), encoding="utf-8"
    )

    markdown = """# v49 active script allowlist

All tracked files under `scripts/` are enumerated in the adjacent CSV and JSON ledgers. The allowlist is conservative: repository-maintenance and v49 API verification scripts remain executable current tooling; the remaining small research/capture scripts are retained only as provenance/reproduction methods for indexed audit evidence. They are not canonical inputs, database entry points, runtime dependencies, or authorization to recapture rights-sensitive material.

The immutable source anchor `v49-data-api-closure-20260821` preserves every original script and its historical inputs. A later v50 change may remove the provenance-only group after the dependent audit packages are independently repackaged; this v49 closure does not rewrite those packages or their historical checksums.

Machine fields include path, category, current runtime/API/database/CI use, retained audit role, and decision. There are no unclassified scripts.

Round 11–12 history coordination rebuilds all three ledgers from the final merge index. The final set includes every Round 10 grammar script, every Round 11 constraint-kernel script, and all Round 12 inquiry-engine scripts plus the shared cross-runtime fixture. Their classifications remain governed research/audit reproduction roles; no runtime, API, database, CI, or public Exploration activation is inferred by integration.
"""
    (ALLOWLIST_DIR / "V49_ACTIVE_SCRIPT_ALLOWLIST.md").write_text(
        markdown, encoding="utf-8"
    )

    RELEASE_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with RELEASE_LEDGER.open("w", encoding="utf-8", newline="") as handle:
        ledger_fields = [
            "metric",
            "value",
            "status",
            "evidence",
        ]
        ledger_writer = csv.DictWriter(
            handle, fieldnames=ledger_fields, delimiter="\t", lineterminator="\n"
        )
        ledger_writer.writeheader()
        metrics = [
            ("tracked_script_count", len(tracked), "PASS", "git ls-files scripts"),
            ("allowlist_row_count", len(rows), "PASS", JSON_PATH),
            ("declared_script_count", payload["scriptCount"], "PASS", JSON_PATH),
            ("missing_path_count", len(missing), "PASS", "tracked minus allowlisted"),
            ("extra_path_count", len(extra), "PASS", "allowlisted minus tracked"),
            (
                "duplicate_path_count",
                duplicate_tracked + duplicate_source,
                "PASS",
                "tracked and source path uniqueness",
            ),
            ("unknown_classification_count", unknown, "PASS", "category and decision fields"),
        ]
        for metric, value, status, evidence in metrics:
            ledger_writer.writerow(
                {
                    "metric": metric,
                    "value": value,
                    "status": status,
                    "evidence": evidence,
                }
            )

    print(f"ACTIVE_SCRIPT_ALLOWLIST_TRACKED_COUNT={len(tracked)}")
    print(f"ACTIVE_SCRIPT_ALLOWLIST_ROW_COUNT={len(rows)}")
    print(f"ACTIVE_SCRIPT_ALLOWLIST_DECLARED_COUNT={payload['scriptCount']}")
    print(f"ACTIVE_SCRIPT_ALLOWLIST_MISSING_COUNT={len(missing)}")
    print(f"ACTIVE_SCRIPT_ALLOWLIST_EXTRA_COUNT={len(extra)}")
    print(
        "ACTIVE_SCRIPT_ALLOWLIST_DUPLICATE_COUNT="
        f"{duplicate_tracked + duplicate_source}"
    )
    print(f"ACTIVE_SCRIPT_ALLOWLIST_UNKNOWN_CLASSIFICATION_COUNT={unknown}")


if __name__ == "__main__":
    main()
