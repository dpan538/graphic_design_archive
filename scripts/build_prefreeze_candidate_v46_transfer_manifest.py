#!/usr/bin/env python3
"""Create a non-mutating, checksumed draft of the future v46 transfer.

The draft is an audit instrument only.  It never stages, commits, uploads, or
copies data.  A later clean-release run must regenerate it and compare hashes
before any batch enters the main repository.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "generated" / "prefreeze_candidate_v46_transfer_manifest_draft.json"
OUT_CSV = ROOT / "data" / "prefreeze_candidate_v46_transfer_manifest_draft.csv"
LFS_THRESHOLD_BYTES = 25 * 1024 * 1024

# A small selected bundle rather than a recursive directory export. The frozen
# SQLite database is included as a LFS snapshot because its identical rebuild
# depends on historical TRACE batch evidence; it never supersedes the candidate
# JSON as canonical data. Raw captures remain research working material.
BATCHES = {
    "A_reproducibility_contract": [
        ".gitattributes",
        "scripts/build_prefreeze_candidate_v46_loc_duplicate_resolution.py",
        "scripts/build_prefreeze_candidate_v46_transfer_manifest.py",
        "scripts/audit_prefreeze_candidate_v46_trace_topology.py",
        "scripts/audit_prefreeze_candidate_v46_trace_atlas.py",
        "scripts/build_prefreeze_candidate_v9_search_sqlite.py",
        "scripts/build_prefreeze_candidate_v21_search_sqlite.py",
        "docs/capture/PREFREEZE_CANDIDATE_v46_TRANSFER_PRECHECK.md",
        "docs/capture/PREFREEZE_CANDIDATE_V46_FROZEN.md",
        "docs/capture/PREFREEZE_CANDIDATE_v46_TRACE_TOPOLOGY.md",
        "docs/capture/PREFREEZE_CANDIDATE_V46_TRACE_ATLAS.md",
        "docs/capture/PREFREEZE_CANDIDATE_v46_SEARCH_TRACE.md",
        "docs/handoff/DESIGN_REFINEMENT_PROMPT_v1.md",
    ],
    "B_active_candidate_payload": [
        "generated/public_surfaces_prefreeze_candidate_v46.json",
    ],
    "C_frozen_search_database": [
        "data/prefreeze_candidate_v46.sqlite",
    ],
    "D_review_and_visual_query_layer": [
        "generated/prefreeze_candidate_v46_object_geography_review_hold.json",
        "generated/prefreeze_candidate_v46_duplicate_representation_review_hold.json",
        "generated/prefreeze_candidate_v46_trace_atlas_manifest.json",
        "data/prefreeze_candidate_v46_summary.csv",
        "data/prefreeze_candidate_v46_base_database_gate.csv",
        "data/prefreeze_candidate_v46_search_gate.csv",
        "data/prefreeze_candidate_v46_search_benchmark.csv",
        "data/prefreeze_candidate_v46_sample_200_audit.csv",
        "data/prefreeze_candidate_v46_trace_topology_summary.csv",
        "data/prefreeze_candidate_v46_trace_topology_audit.csv",
        "data/prefreeze_candidate_v46_trace_atlas_summary.csv",
        "data/prefreeze_candidate_v46_trace_atlas_edge_roles.csv",
        "data/prefreeze_candidate_v46_trace_atlas_geo_decades.csv",
        "data/prefreeze_candidate_v46_trace_atlas_source_geography.csv",
        "data/prefreeze_candidate_v46_loc_duplicate_resolution_decisions.csv",
    ],
}


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> None:
    files: list[dict[str, object]] = []
    missing: list[str] = []
    for batch, relative_paths in BATCHES.items():
        for relative_path in relative_paths:
            path = ROOT / relative_path
            if not path.is_file():
                missing.append(relative_path)
                continue
            size = path.stat().st_size
            files.append(
                {
                    "batch": batch,
                    "path": relative_path,
                    "bytes": size,
                    "sha256": digest(path),
                    "transfer_class": "git_lfs_required" if size > LFS_THRESHOLD_BYTES else "regular_git",
                    "canonical_role": (
                        "active_candidate" if batch == "B_active_candidate_payload"
                        else "frozen_query_snapshot" if batch == "C_frozen_search_database"
                        else "review_or_validation" if batch == "D_review_and_visual_query_layer"
                        else "reproducibility"
                    ),
                }
            )
    if missing:
        raise SystemExit("Manifest input missing: " + ", ".join(missing))

    total_bytes = sum(int(item["bytes"]) for item in files)
    payload = {
        "version": "v46",
        "state": "draft_only_no_stage_no_upload",
        "active_count": 15921,
        "release_hold": "20,000 active-object target has not been reached",
        "excluded": [
            "data/capture_batch_*_raw (research raw cache)",
            "obsolete candidate versions and generated previews",
        ],
        "verification_before_transfer": [
            "Regenerate this manifest in a clean worktree.",
            "Compare every selected SHA-256 exactly.",
            "Verify the search gate, topology audit, and 200-object audit match this version.",
            "Do not proceed if review layers leak into active counts.",
        ],
        "files": files,
        "totals": {
            "files": len(files),
            "bytes": total_bytes,
            "git_lfs_files": sum(item["transfer_class"] == "git_lfs_required" for item in files),
        },
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["batch", "path", "bytes", "sha256", "transfer_class", "canonical_role"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(files)
    print(json.dumps(payload["totals"], ensure_ascii=False))


if __name__ == "__main__":
    main()
