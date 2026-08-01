#!/usr/bin/env python3
"""Independently audit generated TRACE v48 visualization assets and boundaries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "public" / "data" / "trace-v48"
DB = ROOT / "data" / "prefreeze_candidate_v48.sqlite"
CANDIDATE_JSON = ROOT / "generated" / "public_surfaces_prefreeze_candidate_v48.json"
EXPECTED_DB_SHA256 = "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e"
EXPECTED_CANDIDATE_JSON_SHA256 = "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def check(name: str, condition: bool, actual: Any, expected: Any, rows: list[dict[str, Any]]) -> None:
    rows.append({
        "name": name,
        "status": "PASS" if condition else "FAIL",
        "actual": actual,
        "expected": expected,
    })


def main() -> None:
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    atlas = json.loads((OUT / "atlas.json").read_text(encoding="utf-8"))
    auxiliary = json.loads((OUT / "auxiliary.json").read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []

    database_sha = sha256(DB)
    candidate_sha = sha256(CANDIDATE_JSON)
    check("frozen_database_sha256", database_sha == EXPECTED_DB_SHA256, database_sha, EXPECTED_DB_SHA256, rows)
    check("frozen_candidate_json_sha256", candidate_sha == EXPECTED_CANDIDATE_JSON_SHA256, candidate_sha, EXPECTED_CANDIDATE_JSON_SHA256, rows)
    check("manifest_database_sha256", manifest.get("sourceDatabaseSha256") == database_sha, manifest.get("sourceDatabaseSha256"), database_sha, rows)
    check("manifest_candidate_json_sha256", manifest.get("sourceCandidateJsonSha256") == candidate_sha, manifest.get("sourceCandidateJsonSha256"), candidate_sha, rows)
    check("generator_gate", manifest.get("gate") == "PASS", manifest.get("gate"), "PASS", rows)
    check("generator_failures", manifest.get("failures") == [], manifest.get("failures"), [], rows)

    counts = atlas.get("counts") or {}
    expected_counts = {
        "activeObjects": 15_923,
        "reviewObjects": 4_425,
        "auxiliaryObjects": 11,
        "influenceEdges": 0,
    }
    for key, expected in expected_counts.items():
        check(f"count_{key}", counts.get(key) == expected, counts.get(key), expected, rows)

    matrix_total = sum(sum(region.get("counts") or []) for region in atlas.get("regionMatrix") or [])
    check("atlas_matrix_total", matrix_total == 15_923, matrix_total, 15_923, rows)
    check("atlas_marks_budget", atlas.get("atlasMarks", 10**9) <= 360, atlas.get("atlasMarks"), "<=360", rows)
    policy = atlas.get("policy") or {}
    expected_policy = {
        "activeDefault": True,
        "auxiliaryCountEligible": False,
        "reviewMixedWithActive": False,
        "influenceInferred": False,
        "mediumGroupsAreDisplayFiltersOnly": True,
    }
    for key, expected in expected_policy.items():
        check(f"policy_{key}", policy.get(key) is expected, policy.get(key), expected, rows)

    auxiliary_items = auxiliary.get("items") or []
    auxiliary_influence_edges = sum(
        1
        for item in auxiliary_items
        for edge in item.get("edges") or []
        if edge.get("label") == "influenced_by"
    )
    auxiliary_eligible = sum(1 for item in auxiliary_items if (item.get("object") or {}).get("countEligible") is not False)
    check("auxiliary_top_level_count_eligible", auxiliary.get("countEligible") is False, auxiliary.get("countEligible"), False, rows)
    check("auxiliary_item_count", len(auxiliary_items) == 11, len(auxiliary_items), 11, rows)
    check("auxiliary_item_count_eligible", auxiliary_eligible == 0, auxiliary_eligible, 0, rows)
    check("auxiliary_influence_edges", auxiliary_influence_edges == 0, auxiliary_influence_edges, 0, rows)

    declared_assets = manifest.get("assets") or []
    missing = []
    mismatched = []
    for asset in declared_assets:
        path = OUT / asset["path"]
        if not path.is_file():
            missing.append(asset["path"])
            continue
        actual_size = path.stat().st_size
        actual_sha = sha256(path)
        if actual_size != asset.get("bytes") or actual_sha != asset.get("sha256"):
            mismatched.append({"path": asset["path"], "bytes": actual_size, "sha256": actual_sha})
    check("declared_asset_count", len(declared_assets) == 580, len(declared_assets), 580, rows)
    check("declared_assets_present", not missing, missing, [], rows)
    check("declared_asset_hashes", not mismatched, mismatched, [], rows)

    failures = [row for row in rows if row["status"] != "PASS"]
    report = {
        "version": "v48",
        "gate": "PASS" if not failures else "HOLD",
        "checks": len(rows),
        "passed": len(rows) - len(failures),
        "failed": len(failures),
        "results": rows,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
