#!/usr/bin/env python3
"""Merge duplicated Commons representations of one live-verified LOC object.

The .jpg and .tif Commons files resolve to the same official LOC item.  v46
keeps one canonical object, preserves both display representations as evidence,
and isolates the duplicate representation outside the active count.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import build_additive_20k_candidate_v1 as additive
import build_prefreeze_candidate_v10_capture_expansion as v10
import build_prefreeze_candidate_v38_geography_hold_isolation as sample_tools
import build_prefreeze_candidate_v4 as v4
import build_prefreeze_candidate_v6_trace_expansion as v6
import rebuild_public_surfaces_from_records as rebuild


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
GENERATED = ROOT / "generated"
DOCS = ROOT / "docs" / "capture"
INPUT = GENERATED / "public_surfaces_prefreeze_candidate_v45.json"
GEO_REVIEW_INPUT = GENERATED / "prefreeze_candidate_v45_object_geography_review_hold.json"
OUTPUT = GENERATED / "public_surfaces_prefreeze_candidate_v46.json"
GEO_REVIEW = GENERATED / "prefreeze_candidate_v46_object_geography_review_hold.json"
DUPLICATE_REVIEW = GENERATED / "prefreeze_candidate_v46_duplicate_representation_review_hold.json"
VERIFICATION = DATA / "capture_batch_trace_first_loc_relay_verification_2026_v2_records.csv"
NODES = DATA / "prefreeze_candidate_v46_loc_duplicate_resolution_trace_nodes.csv"
EDGES = DATA / "prefreeze_candidate_v46_loc_duplicate_resolution_trace_edges.csv"
DECISIONS = DATA / "prefreeze_candidate_v46_loc_duplicate_resolution_decisions.csv"
SUMMARY = DATA / "prefreeze_candidate_v46_summary.csv"
SAMPLE = DATA / "prefreeze_candidate_v46_sample_200_audit.csv"
REPORT = DOCS / "PREFREEZE_CANDIDATE_v46_LOC_DUPLICATE_RESOLUTION.md"
TARGET = 20_000
CANONICAL_ID = "SURF-CGS2026R0740"
DUPLICATE_ID = "SURF-CGS2026R0741"
DIRECT_URL = "https://www.loc.gov/pictures/item/2016648591/"
SOURCE_ID = "2016648591"
BRANCH = "TRB127"
OLD_COMMONS_DOCUMENTED_BY_EDGE = "TRE-0C8A49CB473696"
NODE_FIELDS = ["node_id", "tree_id", "node_type", "label", "canonical_key", "region", "source_url", "evidence", "evidence_status"]
EDGE_FIELDS = ["edge_id", "tree_id", "branch_id", "subject_node_id", "object_node_id", "edge_label", "evidence_url", "evidence_text", "evidence_field", "confidence", "review_state", "prohibited_inference_check"]


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def stable(prefix: str, *values: Any) -> str:
    return prefix + hashlib.sha1("|".join(clean(value) for value in values).encode("utf-8")).hexdigest()[:14].upper()


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def qualified_rows() -> list[dict[str, str]]:
    with VERIFICATION.open(newline="", encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    qualified = [row for row in rows if row.get("status") == "qualified_direct_reattach" and clean(row.get("direct_url")) == DIRECT_URL]
    if {row["surface_id"] for row in qualified} != {CANONICAL_ID, DUPLICATE_ID}:
        raise RuntimeError("The live LOC duplicate verification evidence changed unexpectedly")
    return qualified


def main() -> None:
    parent = json.loads(INPUT.read_text(encoding="utf-8"))
    geo_review = json.loads(GEO_REVIEW_INPUT.read_text(encoding="utf-8"))
    verified = qualified_rows()
    active = json.loads(json.dumps(parent.get("surfaces") or [], ensure_ascii=False))
    by_id = {clean(surface.get("surfaceId")): surface for surface in active}
    canonical, duplicate = by_id.get(CANONICAL_ID), by_id.get(DUPLICATE_ID)
    if not canonical or not duplicate:
        raise RuntimeError("Expected both duplicate Commons representations in v45")
    if clean(canonical.get("title")) != clean(duplicate.get("title")) or canonical.get("dateStart") != duplicate.get("dateStart"):
        raise RuntimeError("The pair no longer represents one verified source object")
    raw_path = ROOT / next(row["raw_path"] for row in verified if row["surface_id"] == CANONICAL_ID)
    official = json.loads(raw_path.read_text(encoding="utf-8"))
    item = official.get("item") or {}
    if clean(item.get("url") or item.get("link")) != DIRECT_URL or clean(item.get("title")) != "Cuba-Chile, '74 : a benefit for Chilean refugees":
        raise RuntimeError("Raw official LOC record no longer matches the duplicate decision")
    old_canonical_url, old_duplicate_url = clean(canonical.get("sourceUrl")), clean(duplicate.get("sourceUrl"))
    canonical["title"] = clean(item.get("title")); canonical["sourceName"] = "Library of Congress loc.gov API"
    canonical["sourceUrl"] = DIRECT_URL; canonical["sourceObjectKey"] = SOURCE_ID; canonical["sourceDocumentUrl"] = DIRECT_URL
    v4.replace_or_append_table_row(canonical, "SOURCE", "Source name", "Library of Congress loc.gov API")
    v4.replace_or_append_table_row(canonical, "SOURCE", "Source identifier", SOURCE_ID)
    v4.replace_or_append_table_row(canonical, "SOURCE", "Source URL", DIRECT_URL)
    v4.replace_or_append_table_row(canonical, "SOURCE", "Record host", "Library of Congress")
    v4.replace_or_append_table_row(canonical, "SOURCE", "Descriptive source", "Library of Congress")
    v4.replace_or_append_table_row(canonical, "SOURCE", "Descriptive source role", "direct_institutional_record_verified")
    v4.replace_or_append_table_row(canonical, "SOURCE", "Secondary display host", old_canonical_url)
    v4.replace_or_append_table_row(canonical, "SOURCE", "Alternate media representation", old_duplicate_url)
    v4.replace_or_append_table_row(canonical, "SOURCE", "Direct record verification", "LOC JSON title/date checked: Cuba-Chile, '74 : a benefit for Chilean refugees | [1974]")
    v4.replace_or_append_table_row(canonical, "CITATIONS", "Source URL", DIRECT_URL)
    v4.replace_or_append_table_row(canonical, "CITATIONS", "Secondary host", old_canonical_url)
    v4.replace_or_append_table_row(canonical, "CITATIONS", "Alternate representation", old_duplicate_url)
    v4.replace_or_append_table_row(canonical, "CITATIONS", "Raw payload", str(raw_path.relative_to(ROOT)))
    v4.replace_or_append_table_row(canonical, "CITATIONS", "Evidence return", DIRECT_URL)
    trace = canonical.get("trace") or {}
    tree_id, object_node_id = clean(trace.get("treeId")), clean(trace.get("objectNodeId"))
    if not tree_id or not object_node_id:
        raise RuntimeError("Canonical object lacks existing TRACE root")
    source_node_id = stable("TRN-V46-LOC-", DIRECT_URL, SOURCE_ID); edge_id = stable("TRE-V46-LOC-", object_node_id, source_node_id, "documented_by")
    node = {"node_id": source_node_id, "tree_id": tree_id, "node_type": "source_record", "label": f"Library of Congress record: {SOURCE_ID}", "canonical_key": DIRECT_URL, "region": "", "source_url": DIRECT_URL, "evidence": "Live LOC item JSON; title=Cuba-Chile, '74 : a benefit for Chilean refugees; created_published=[1974]", "evidence_status": "live_direct_institutional_record_verified"}
    edge = {"edge_id": edge_id, "tree_id": tree_id, "branch_id": BRANCH, "subject_node_id": object_node_id, "object_node_id": source_node_id, "edge_label": "documented_by", "evidence_url": DIRECT_URL, "evidence_text": "Library of Congress object record verified against the two Commons representations' title and year.", "evidence_field": "live LOC item JSON title and created_published", "confidence": "high", "review_state": "accepted", "prohibited_inference_check": "pass"}
    # The retained Commons file is an alternate display representation, not a
    # second descriptive root. Keep its place/type evidence only; the direct
    # LOC item becomes the sole ``documented_by`` edge for this object.
    if OLD_COMMONS_DOCUMENTED_BY_EDGE not in set(trace.get("edgeIds") or []):
        raise RuntimeError("Expected original Commons documented_by edge is absent")
    trace["edgeIds"] = [value for value in trace.get("edgeIds", []) if value != OLD_COMMONS_DOCUMENTED_BY_EDGE] + [edge_id]
    trace["coreEdgeIds"] = [value for value in trace.get("coreEdgeIds", []) if value != OLD_COMMONS_DOCUMENTED_BY_EDGE] + [edge_id]
    trace["branchIds"] = sorted({*trace.get("branchIds", []), BRANCH}); trace["edgeLabels"] = sorted({*trace.get("edgeLabels", []), "documented_by"})
    trace.update({"edgeCount": len(trace["edgeIds"]), "coreEdgeCount": int(trace.get("coreEdgeCount") or 0) + 1, "evidenceReturnUrl": DIRECT_URL, "tier": "source_verified", "tierBasis": "live_loc_item_json_verified_title_and_date_duplicate_merged", "reviewState": "accepted_direct_institutional_reattachment", "state": "accepted", "influenceState": "not_inferred"})
    canonical["trace"] = trace
    canonical["authority"] = {"state": "institutional_primary", "origin": "United States", "geographyClass": "institutional_record_metadata_separate_from_object_geography", "geographyRole": "institutional_host_metadata_separate_from_object_geography", "objectGeographyBasis": "official LOC object place fields; existing Chile assignment retained", "resolutionBasis": "live_loc_item_json_verified_title_and_date", "narrativePosition": "institutional_primary_record_with_separate_object_geography", "countPolicy": "eligible_for_active_total"}
    v4.replace_or_append_table_row(canonical, "CLASSIFICATION", "Authority state", "institutional_primary")
    v4.replace_or_append_table_row(canonical, "RELATIONS", "TRACE direct source root", "documented_by")
    v4.replace_or_append_table_row(canonical, "RELATIONS", "TRACE tier", "source_verified")
    v4.replace_or_append_table_row(canonical, "RELATIONS", "Influence state", "not_inferred")
    active = [surface for surface in active if clean(surface.get("surfaceId")) != DUPLICATE_ID]
    result = {"meta": dict(parent.get("meta") or {}), "folderTypes": parent.get("folderTypes") or [], "folders": additive.build_folders(active), "surfaces": active}
    result = rebuild.normalize_public_folder_metadata(result); result = rebuild.attach_structural_collections(result); result = rebuild.build_research_dossiers(result)
    accepted = sum(v6.trace_state(surface) == "accepted" for surface in active); explicit = sum(clean((surface.get("trace") or {}).get("tier")) in {"source_verified", "metadata_supported"} for surface in active)
    result["meta"].update({"status": "prefreeze_candidate_v46_loc_duplicate_resolution", "candidatePayload": True, "officialReleasePayload": False, "sourceCandidate": str(INPUT.relative_to(ROOT)), "parentCandidateVersion": "v45", "activeSurfaceCount": len(active), "objectGeographyReviewHoldCount": len(geo_review.get("surfaces") or []), "objectGeographyReviewPayload": str(GEO_REVIEW.relative_to(ROOT)), "duplicateRepresentationReviewPayload": str(DUPLICATE_REVIEW.relative_to(ROOT)), "duplicateRepresentationHoldCount": 1, "locDirectDuplicateMergeV46": 1, "minimumTargetObjectCount": TARGET, "remainingToMinimumTarget": TARGET - len(active), "explicitTierCount": explicit, "remainingUntieredTraceCount": len(active) - explicit, "traceAcceptedCount": accepted, "traceUnlinkedCount": len(active) - accepted, "traceCoveragePct": round(accepted / len(active) * 100, 2), "traceInfluenceAutoPromotion": False, "noOfficialOverwrite": True, "qualityFirstCountPolicy": True})
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    geo_review["meta"] = {**dict(geo_review.get("meta") or {}), "sourceCandidate": str(INPUT.relative_to(ROOT)), "retainedByCandidate": "v46"}; GEO_REVIEW.write_text(json.dumps(geo_review, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    duplicate_copy = json.loads(json.dumps(duplicate, ensure_ascii=False)); duplicate_copy["reviewDisposition"] = {"state": "duplicate_representation_hold", "countEligible": False, "canonicalSurfaceId": CANONICAL_ID, "canonicalDirectRecord": DIRECT_URL, "reason": "The .tif and .jpg Commons files resolve to one LOC object; alternate representation is retained on the canonical record."}
    DUPLICATE_REVIEW.write_text(json.dumps({"meta": {"status": "prefreeze_candidate_v46_duplicate_representation_review_hold", "count": 1, "countEligible": False, "sourceCandidate": str(INPUT.relative_to(ROOT)), "boundary": "A verified alternate media representation is not a second object."}, "surfaces": [duplicate_copy]}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    write_csv(NODES, NODE_FIELDS, [node]); write_csv(EDGES, EDGE_FIELDS, [edge])
    decision = [{"canonical_surface_id": CANONICAL_ID, "held_surface_id": DUPLICATE_ID, "direct_source_url": DIRECT_URL, "official_source_identifier": SOURCE_ID, "canonical_secondary_host": old_canonical_url, "alternate_media_representation": old_duplicate_url, "removed_secondary_documented_by_edge": OLD_COMMONS_DOCUMENTED_BY_EDGE, "action": "merge_duplicate_representation_and_reattach_direct_loc_record", "raw_path": str(raw_path.relative_to(ROOT))}]
    write_csv(DECISIONS, list(decision[0]), decision)
    sample = [sample_tools.audit_row(canonical, "direct_source_duplicate_merge", 1)]; seen = {CANONICAL_ID, DUPLICATE_ID}
    for row in v10.sample_rows(active):
        if len(sample) >= 200: break
        if clean(row["surface_id"]) not in seen:
            sample.append(row); seen.add(clean(row["surface_id"]))
    supplements = sorted((surface for surface in active if clean(surface.get("surfaceId")) not in seen), key=lambda surface: clean(surface.get("surfaceId")))
    while len(sample) < 200 and supplements: sample.append(sample_tools.audit_row(supplements.pop(0), "active_completion", len(sample) + 1))
    if len(sample) != 200: raise RuntimeError(f"Expected exactly 200 audit rows, got {len(sample)}")
    for index, row in enumerate(sample, 1): row["sample_id"] = f"PF46S{index:03d}"
    write_csv(SAMPLE, v10.SAMPLE_FIELDS, sample); statuses = Counter(row["audit_status"] for row in sample)
    summary = {"parent_objects": len(parent.get("surfaces") or []), "duplicate_representations_merged": 1, "active_objects": len(active), "remaining_to_minimum_20000": TARGET - len(active), "explicit_tier": explicit, "trace_accepted": accepted, "trace_unlinked": len(active) - accepted, "trace_coverage_pct": f"{accepted / len(active) * 100:.2f}", "influence_edges": 0, "sample_pass": statuses["pass"], "sample_fail": statuses["fail"]}
    write_csv(SUMMARY, list(summary), [summary])
    REPORT.write_text("\n".join(["# Prefreeze candidate v46 LOC duplicate representation resolution", "", *[f"- {key.replace('_', ' ')}: {value}" for key, value in summary.items()], "", "## Boundary", "", "- One official LOC item, title and date verifies that the two Commons files are alternate representations of a single object.", "- The canonical record retains both Commons URLs as display evidence while its descriptive source and TRACE root move to the live official LOC item.", "- The removed representation is isolated in a count-ineligible review payload; no source, geography, authority or influence inference is created."]) + "\n", encoding="utf-8")
    for key, value in summary.items(): print(f"{key}={value}")


if __name__ == "__main__":
    main()
