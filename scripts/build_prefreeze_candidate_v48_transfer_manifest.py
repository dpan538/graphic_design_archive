#!/usr/bin/env python3
"""Build the selected, checksumed v48 main-transfer manifest."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "generated" / "prefreeze_candidate_v48_transfer_manifest.json"
OUT_CSV = ROOT / "data" / "prefreeze_candidate_v48_transfer_manifest.csv"
LFS_THRESHOLD = 25 * 1024 * 1024


def relevant_files() -> dict[str, list[str]]:
    aic_raw = sorted(str(path.relative_to(ROOT)) for path in (ROOT / "data/capture_batch_trace_first_aic_geographic_balance_v47_raw").glob("*.json"))
    loc_raw = sorted(str(path.relative_to(ROOT)) for path in (ROOT / "data/prefreeze_candidate_v48_loc_geo_repair_raw").glob("*.json"))
    if len(aic_raw) != 12:
        raise SystemExit(f"Expected 12 committed v47 AIC evidence payloads, got {len(aic_raw)}")
    if len(loc_raw) != 18:
        raise SystemExit(f"Expected 18 committed v48 LOC evidence payloads, got {len(loc_raw)}")
    return {
        "A_reproducibility_and_freeze_contract": [
            ".gitattributes",
            "scripts/run_trace_first_aic_geographic_balance_v47.py",
            "scripts/build_prefreeze_candidate_v47_aic_balance.py",
            "scripts/build_prefreeze_candidate_v47_search_sqlite.py",
            "scripts/repair_prefreeze_candidate_v48_loc_geography.py",
            "scripts/build_prefreeze_candidate_v48_loc_geo_repair.py",
            "scripts/build_prefreeze_candidate_v48_search_sqlite.py",
            "scripts/audit_prefreeze_candidate_v48_freeze.py",
            "scripts/build_prefreeze_candidate_v48_transfer_manifest.py",
            "docs/capture/PREFREEZE_CANDIDATE_v47_AIC_TRACE_ADJUNCT.md",
            "docs/capture/PREFREEZE_CANDIDATE_v47_SEARCH_TRACE.md",
            "docs/capture/PREFREEZE_CANDIDATE_v48_SEARCH_TRACE.md",
            "docs/capture/PREFREEZE_CANDIDATE_V48_FROZEN.md",
        ],
        "B_canonical_v48_candidate_payload": [
            "generated/public_surfaces_prefreeze_candidate_v48.json",
        ],
        "C_frozen_v48_search_database": [
            "data/prefreeze_candidate_v48.sqlite",
        ],
        "D_evidence_and_validation": [
            "generated/prefreeze_candidate_v47_aic_trace_adjuncts.json",
            "data/capture_batch_trace_first_aic_geographic_balance_v47_quality.csv",
            "data/capture_batch_trace_first_aic_geographic_balance_v47_records.csv",
            "data/capture_batch_trace_first_aic_geographic_balance_v47_summary.csv",
            "data/capture_batch_trace_first_aic_geographic_balance_v47_trace_adjunct_edges.csv",
            "data/capture_batch_trace_first_aic_geographic_balance_v47_trace_adjunct_nodes.csv",
            "data/capture_batch_trace_first_aic_geographic_balance_v47_trace_adjunct_records.csv",
            "data/capture_batch_trace_first_aic_geographic_balance_v47_trace_edges.csv",
            "data/capture_batch_trace_first_aic_geographic_balance_v47_trace_nodes.csv",
            "data/prefreeze_candidate_v47_sample_200_audit.csv",
            "data/prefreeze_candidate_v47_search_benchmark.csv",
            "data/prefreeze_candidate_v47_search_gate.csv",
            "data/prefreeze_candidate_v47_summary.csv",
            "data/prefreeze_candidate_v48_loc_geo_repairs.csv",
            "data/prefreeze_candidate_v48_loc_geo_trace_edges.csv",
            "data/prefreeze_candidate_v48_loc_geo_trace_nodes.csv",
            "data/prefreeze_candidate_v48_sample_200_audit.csv",
            "data/prefreeze_candidate_v48_search_gate.csv",
            "data/prefreeze_candidate_v48_summary.csv",
            "data/prefreeze_candidate_v48_freeze_gate.csv",
            *aic_raw,
            *loc_raw,
        ],
    }


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            value.update(block)
    return value.hexdigest()


def main() -> None:
    rows: list[dict[str, object]] = []
    missing: list[str] = []
    batches = relevant_files()
    for batch, paths in batches.items():
        if len(paths) != len(set(paths)):
            raise SystemExit(f"Duplicate manifest path in {batch}")
        for relative in paths:
            path = ROOT / relative
            if not path.is_file():
                missing.append(relative)
                continue
            size = path.stat().st_size
            rows.append({
                "batch": batch,
                "path": relative,
                "bytes": size,
                "sha256": digest(path),
                "lfs_status": "required" if size > LFS_THRESHOLD else "regular_git",
                "role": (
                    "canonical_candidate" if batch.startswith("B_")
                    else "frozen_query_snapshot" if batch.startswith("C_")
                    else "evidence_or_validation" if batch.startswith("D_")
                    else "reproducibility_and_contract"
                ),
            })
    if missing:
        raise SystemExit("Missing manifest inputs: " + ", ".join(missing))
    lfs_paths = {row["path"] for row in rows if row["lfs_status"] == "required"}
    expected_lfs = {
        "generated/public_surfaces_prefreeze_candidate_v48.json",
        "data/prefreeze_candidate_v48.sqlite",
    }
    if lfs_paths != expected_lfs:
        raise SystemExit(f"Unexpected LFS classification: {sorted(lfs_paths)}")
    payload = {
        "version": "v48",
        "freezeDate": "2026-08-01",
        "sourceDataCommit": "1d919fb",
        "state": "candidate_frozen_for_trace_visualization_not_official_release",
        "activeObjectCount": 15_923,
        "remainingToMinimum20000": 4_077,
        "qualityGates": {"passed": 55, "held": 0},
        "isolatedNotCounted": {
            "authorityUncertainReview": 4_425,
            "traceAuxiliaryPhotoPrint": 11,
            "traceAuxiliaryPromotions": 0,
            "influenceEdges": 0,
        },
        "excluded": [
            "uncommitted DigitalNZ, Cooper Hewitt, Smithsonian, Norway and LOC discovery probes",
            "generated/public_surfaces_prefreeze_candidate_v47.json and data/prefreeze_candidate_v47.sqlite derived intermediates",
            "older candidate versions, disposable caches, screenshots and unrelated frontend work",
        ],
        "transferStopRule": "Push and remotely verify each ordered batch before starting the next; never force-push or rewrite history.",
        "files": rows,
        "totals": {
            "files": len(rows),
            "bytes": sum(int(row["bytes"]) for row in rows),
            "lfsFiles": sum(row["lfs_status"] == "required" for row in rows),
        },
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with OUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["batch", "path", "bytes", "sha256", "lfs_status", "role"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(payload["totals"]))


if __name__ == "__main__":
    main()
