#!/usr/bin/env python3
"""Independently audit the immutable inputs for the v48 candidate freeze."""

from __future__ import annotations

import csv
import json
import re
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
GENERATED = ROOT / "generated"
PAYLOAD = GENERATED / "public_surfaces_prefreeze_candidate_v48.json"
PARENT = GENERATED / "public_surfaces_prefreeze_candidate_v47.json"
DB = DATA / "prefreeze_candidate_v48.sqlite"
REPAIRS = DATA / "prefreeze_candidate_v48_loc_geo_repairs.csv"
REPAIR_RAW = DATA / "prefreeze_candidate_v48_loc_geo_repair_raw"
REPAIR_EDGES = DATA / "prefreeze_candidate_v48_loc_geo_trace_edges.csv"
SAMPLE = DATA / "prefreeze_candidate_v48_sample_200_audit.csv"
SAVED_SEARCH_GATE = DATA / "prefreeze_candidate_v48_search_gate.csv"
ADJUNCTS = GENERATED / "prefreeze_candidate_v47_aic_trace_adjuncts.json"
OUT = DATA / "prefreeze_candidate_v48_freeze_gate.csv"
ACTIVE = 15_923
TARGET = 20_000
AIC_IDS = {"AICTRACEV47R0001", "AICTRACEV47R0002"}
FILENAME_TITLE = re.compile(r"\.(?:jpe?g|png|webp|tiff?|gif|pdf)$", re.I)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def table_value(surface: dict, kind: str, label: str) -> str:
    for table in surface.get("tables") or []:
        if table.get("kind") != kind:
            continue
        for row in table.get("rows") or []:
            if len(row) >= 2 and row[0] == label:
                return str(row[1])
    return ""


def scalar(conn: sqlite3.Connection, query: str, params: tuple = ()) -> int:
    return int(conn.execute(query, params).fetchone()[0])


def main() -> None:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    parent = json.loads(PARENT.read_text(encoding="utf-8"))
    adjuncts = json.loads(ADJUNCTS.read_text(encoding="utf-8"))
    repairs = read_csv(REPAIRS)
    repair_edges = read_csv(REPAIR_EDGES)
    sample = read_csv(SAMPLE)
    saved_gate = read_csv(SAVED_SEARCH_GATE)
    surfaces = payload.get("surfaces") or []
    parent_surfaces = parent.get("surfaces") or []
    by_id = {surface.get("surfaceId"): surface for surface in surfaces}
    parent_by_id = {surface.get("surfaceId"): surface for surface in parent_surfaces}
    repair_by_id = {row["surface_id"]: row for row in repairs}
    repair_edge_by_subject = {row["subject_node_id"]: row for row in repair_edges}
    checks: list[tuple[str, object, object, str]] = []

    def check(name: str, value: object, requirement: object, note: str) -> None:
        checks.append((name, value, requirement, note))

    meta = payload.get("meta") or {}
    check("payload_status", meta.get("status"), "prefreeze_candidate_v48_loc_object_geography_repair", "Versioned candidate status")
    check("payload_parent_version", meta.get("parentCandidateVersion"), "v47", "v48 derives from the isolated v47 candidate")
    check("payload_official_release", str(meta.get("officialReleasePayload")).lower(), "false", "Candidate is not the official release layer")
    check("payload_active_count", len(surfaces), ACTIVE, "Exact active candidate count")
    check("payload_gap_to_20000", TARGET - len(surfaces), 4_077, "Quality gates are not relaxed to close the count gap")
    check("payload_unique_surface_ids", len(by_id), ACTIVE, "No duplicate surface IDs")
    check("payload_unique_source_record_ids", len({x.get('sourceRecordId') for x in surfaces}), ACTIVE, "No duplicate source record IDs")
    check("payload_unresolved_region_active", sum(x.get("placeText") == "Unresolved region" for x in surfaces), 0, "Object geography only")
    check("payload_authority_uncertain_active", sum((x.get("authority") or {}).get("state") == "uncertain" for x in surfaces), 0, "Authority hold does not leak into active layer")
    check("payload_trace_unlinked_active", sum((x.get("trace") or {}).get("state") != "accepted" for x in surfaces), 0, "Every active object has accepted TRACE state")
    check("payload_trace_missing_edge_ids", sum(not (x.get("trace") or {}).get("edgeIds") for x in surfaces), 0, "Accepted TRACE has indexed evidence edge IDs")
    check("payload_influenced_by_labels", sum("influenced_by" in ((x.get("trace") or {}).get("edgeLabels") or []) for x in surfaces), 0, "No inferred historical influence")
    check("payload_filename_extension_titles", sum(bool(FILENAME_TITLE.search(str(x.get("title") or "").strip())) for x in surfaces), 0, "Display titles are not filenames")
    check("parent_child_surface_set_delta", len(set(by_id) ^ set(parent_by_id)), 0, "v48 does not add or remove active objects")
    unchanged_core = sum(
        any(current.get(key) != parent_by_id[sid].get(key) for key in ("title", "dateStart", "dateEnd", "sourceUrl", "sourceObjectKey", "authority"))
        for sid, current in by_id.items()
    )
    check("parent_child_core_record_changes", unchanged_core, 0, "LOC geography and AIC display routing do not reclassify core records")
    changed_places = {sid for sid, current in by_id.items() if current.get("placeText") != parent_by_id[sid].get("placeText")}
    check("parent_child_place_changes", len(changed_places), 18, "Only the explicit LOC item.place repairs change geography")
    check("parent_child_place_change_scope", len(changed_places ^ set(repair_by_id)), 0, "Every geography change is declared in the repair CSV")

    raw_files = sorted(REPAIR_RAW.glob("*.json"))
    check("loc_repair_rows", len(repairs), 18, "Declared object-level LOC repairs")
    check("loc_repair_unique_surfaces", len(repair_by_id), 18, "One repair per active object")
    check("loc_repair_raw_files", len(raw_files), 18, "One saved official LOC response per repair")
    check("loc_repair_edges", len(repair_edges), 18, "One associated_with_place edge per repair")
    loc_evidence_failures = 0
    loc_scope_failures = 0
    for row in repairs:
        surface = by_id.get(row["surface_id"]) or {}
        raw_path = REPAIR_RAW / f"{row['source_object_key']}.json"
        raw = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.is_file() else {}
        official_places = {
            str(item.get("title") or "").strip()
            for item in ((raw.get("item") or {}).get("place") or [])
            if str(item.get("title") or "").strip()
        }
        trace = surface.get("trace") or {}
        edge = repair_edge_by_subject.get(trace.get("objectNodeId")) or {}
        if not (
            row["status"] == "pass_explicit_object_place"
            and row["evidence_field"] == "item.place[].title"
            and row["loc_place_raw"] in official_places
            and row["evidence_text"] == f"LOC item.place={row['loc_place_raw']}"
            and surface.get("placeText") == row["normalized_place_text"]
            and table_value(surface, "NORMALIZED", "Object geography evidence") == row["evidence_text"]
            and edge.get("edge_label") == "associated_with_place"
            and edge.get("evidence_field") == "item.place[].title"
            and edge.get("prohibited_inference_check") == "pass:explicit_object_place_not_influence"
        ):
            loc_evidence_failures += 1
        if not (
            row["country"] == "United States"
            and row["normalized_place_text"].startswith("United States")
            and row["loc_item_url"].startswith("https://www.loc.gov/pictures/item/")
            and "TRB167" in (trace.get("branchIds") or [])
        ):
            loc_scope_failures += 1
    check("loc_item_place_evidence_failures", loc_evidence_failures, 0, "No repository, creator-nationality or search-term geography substitutions")
    check("loc_repair_scope_failures", loc_scope_failures, 0, "Repair stays inside explicit LOC item.place evidence")

    aic_active = [x for x in surfaces if x.get("sourceRecordId") in AIC_IDS]
    aic_route_failures = 0
    for surface in aic_active:
        image = surface.get("image") or {}
        if not (
            image.get("state") == "IMG02"
            and image.get("hasImageFrame") is False
            and image.get("url") is None
            and image.get("displayMode") == "source_viewer_only"
            and image.get("sourceViewerUrl") == surface.get("sourceUrl")
            and "/iiif/" in str(image.get("evidenceImageUrl") or "")
            and table_value(surface, "CITATIONS", "Image display route") == surface.get("sourceUrl")
        ):
            aic_route_failures += 1
    check("aic_active_source_viewer_objects", len(aic_active), 2, "The two active AIC additions remain active")
    check("aic_active_unstable_display_route_failures", aic_route_failures, 0, "Cloudflare-blocked IIIF URLs are evidence only")

    adjunct_items = adjuncts.get("items") or []
    adjunct_edges = adjuncts.get("traceEdges") or []
    adjunct_failures = sum(
        not (
            item.get("countEligible") is False
            and item.get("dateStart") is not None
            and item.get("placeText")
            and item.get("medium")
            and str(item.get("sourceUrl") or "").startswith("https://www.artic.edu/artworks/")
            and (item.get("image") or {}).get("displayPolicy") == "source_viewer_only"
            and (item.get("trace") or {}).get("reviewState") == "accepted_auxiliary"
            and (item.get("trace") or {}).get("influenceState") == "not_inferred"
        )
        for item in adjunct_items
    )
    check("trace_adjunct_count", len(adjunct_items), 11, "Photography and printmaking auxiliary branch")
    check("trace_adjunct_evidence_failures", adjunct_failures, 0, "Auxiliary nodes retain source, medium, year and place")
    check("trace_adjunct_influence_edges", sum(x.get("edge_label") == "influenced_by" for x in adjunct_edges), 0, "Auxiliary relations never become historical influence")

    check("sample_rows", len(sample), 200, "Saved 200-object audit")
    check("sample_unique_ids", len({row.get('sample_id') for row in sample}), 200, "No duplicate sample rows")
    check("sample_failures", sum(row.get("audit_status") != "pass" for row in sample), 0, "All sampled objects pass")
    check("sample_loc_repair_rows", sum(row.get("sample_lane") == "v48_explicit_loc_item_place_repair" for row in sample), 18, "All 18 LOC repairs are forced into the sample")
    check("saved_search_gate_holds", sum(row.get("status") != "PASS" for row in saved_gate), 0, "Versioned saved search gate")

    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        check("sqlite_integrity", conn.execute("pragma integrity_check").fetchone()[0], "ok", "Frozen query snapshot integrity")
        schema_meta = dict(conn.execute("select key,value from schema_meta"))
        check("sqlite_schema_version", schema_meta.get("schema_version"), "prefreeze_candidate_v48_sqlite_v1", "SQLite version matches candidate")
        check("sqlite_source_payload", schema_meta.get("source_payload"), "generated/public_surfaces_prefreeze_candidate_v48.json", "SQLite points to the exact v48 payload")
        check("sqlite_active_objects", scalar(conn, "select count(*) from objects where count_eligible=1"), ACTIVE, "SQLite active count")
        check("sqlite_payload_id_delta", scalar(conn, "select count(*) from objects where count_eligible=1 and surface_id not in (%s)" % ",".join("?" * len(by_id)), tuple(by_id)), 0, "SQLite IDs are a subset of payload IDs")
        check("sqlite_unresolved_region_active", scalar(conn, "select count(*) from objects where count_eligible=1 and region='Unresolved region'"), 0, "Active unresolved geography")
        check("sqlite_authority_uncertain_active", scalar(conn, "select count(*) from objects where count_eligible=1 and authority_state='uncertain'"), 0, "Authority hold isolation")
        check("sqlite_authority_review_rows", scalar(conn, "select count(*) from authority_review_objects_current"), 4_425, "Authority review layer remains visible and separate")
        check("sqlite_authority_review_search_rows", scalar(conn, "select count(*) from search_documents where active_object=0 and authority_state='uncertain'"), 4_425, "Authority review layer remains searchable")
        check("sqlite_trace_unlinked_active", scalar(conn, "select count(*) from objects where count_eligible=1 and trace_state<>'accepted'"), 0, "Accepted active TRACE")
        check("sqlite_active_without_indexed_edges", scalar(conn, "select count(*) from objects o where o.count_eligible=1 and not exists (select 1 from object_trace_edges x where x.surface_id=o.surface_id)"), 0, "Every active object has indexed edge references")
        check("sqlite_influence_edges", scalar(conn, "select count(*) from trace_edges where edge_label='influenced_by'"), 0, "No inferred historical influence")
        check("sqlite_orphan_edge_subjects", scalar(conn, "select count(*) from trace_edges e left join trace_nodes n on n.node_id=e.subject_node_id where n.node_id is null"), 0, "TRACE subject endpoints resolve")
        check("sqlite_orphan_edge_objects", scalar(conn, "select count(*) from trace_edges e left join trace_nodes n on n.node_id=e.object_node_id where n.node_id is null"), 0, "TRACE object endpoints resolve")
        check("sqlite_broken_object_edge_refs", scalar(conn, "select count(*) from object_trace_edges x left join trace_edges e on e.edge_id=x.edge_id where e.edge_id is null"), 0, "Object-edge junctions resolve")
        check("sqlite_filename_extension_titles", scalar(conn, "select count(*) from objects where lower(title) glob '*.jpg' or lower(title) glob '*.jpeg' or lower(title) glob '*.png' or lower(title) glob '*.webp' or lower(title) glob '*.tif' or lower(title) glob '*.tiff' or lower(title) glob '*.gif' or lower(title) glob '*.pdf'"), 0, "No filenames exposed as display titles")
        check("sqlite_active_search_documents", scalar(conn, "select count(*) from search_documents where active_object=1"), ACTIVE, "One active search document per object")
        check("sqlite_active_search_mismatches", scalar(conn, "select count(*) from objects o join search_documents s on s.object_or_capture_id=o.surface_id and s.active_object=1 where s.title<>o.title or s.region<>o.region"), 0, "Search title and geography match objects")
        check("sqlite_trace_adjunct_documents", scalar(conn, "select count(*) from search_documents where document_type='trace_adjunct' and active_object=0"), 11, "Auxiliary TRACE stays count-isolated and searchable")
        check("sqlite_trace_adjunct_active_leak", scalar(conn, "select count(*) from search_documents where document_type='trace_adjunct' and active_object<>0"), 0, "Auxiliary TRACE never enters active count")
        check("sqlite_loc_repair_edges", scalar(conn, "select count(*) from trace_edges where branch_id='TRB167' and edge_label='associated_with_place'"), 18, "LOC geography repair edges")
        check("sqlite_aic_unstable_display_routes", scalar(conn, "select count(*) from objects where source_record_id in ('AICTRACEV47R0001','AICTRACEV47R0002') and image_url is not null"), 0, "AIC direct IIIF is absent from display fields")
    finally:
        conn.close()

    rows = [
        {
            "gate": name,
            "value": str(value),
            "requirement": str(requirement),
            "status": "PASS" if str(value) == str(requirement) else "HOLD",
            "note": note,
        }
        for name, value, requirement, note in checks
    ]
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["gate", "value", "requirement", "status", "note"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    holds = [row for row in rows if row["status"] != "PASS"]
    print(json.dumps({"gates": len(rows), "pass": len(rows) - len(holds), "hold": len(holds), "holds": [row["gate"] for row in holds]}))
    if holds:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
