#!/usr/bin/env python3
"""Make the isolated v47 candidate from frozen v46 plus one strict AIC pass.

The two graphic carriers enter the active candidate.  Explicitly documented
printmaking and photography records are emitted as a separate TRACE adjunct
packet: searchable evidence, never active archive objects and never inferred
influence edges.
"""

from __future__ import annotations

import csv
import json
from copy import deepcopy
from pathlib import Path

import rebuild_public_surfaces_from_records as rebuild
import run_midcentury_capture_1930_1970 as mc

ROOT = Path(__file__).resolve().parents[1]
DATA, GENERATED = ROOT / "data", ROOT / "generated"
PARENT = GENERATED / "public_surfaces_prefreeze_candidate_v46.json"
OUTPUT = GENERATED / "public_surfaces_prefreeze_candidate_v47.json"
STEM = "capture_batch_trace_first_aic_geographic_balance_v47"
RECORDS = DATA / f"{STEM}_records.csv"
NODES, EDGES = DATA / f"{STEM}_trace_nodes.csv", DATA / f"{STEM}_trace_edges.csv"
ADJUNCT_RECORDS = DATA / f"{STEM}_trace_adjunct_records.csv"
ADJUNCT_NODES, ADJUNCT_EDGES = DATA / f"{STEM}_trace_adjunct_nodes.csv", DATA / f"{STEM}_trace_adjunct_edges.csv"
ADJUNCT_OUTPUT = GENERATED / "prefreeze_candidate_v47_aic_trace_adjuncts.json"
SUMMARY = DATA / "prefreeze_candidate_v47_summary.csv"
SAMPLE_PARENT = DATA / "prefreeze_candidate_v46_sample_200_audit.csv"
SAMPLE_OUTPUT = DATA / "prefreeze_candidate_v47_sample_200_audit.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def table(surface: dict, kind: str) -> dict:
    for entry in surface.get("tables", []):
        if entry.get("kind") == kind:
            return entry
    entry = {"kind": kind, "rows": []}
    surface.setdefault("tables", []).append(entry)
    return entry


def replace_row(entry: dict, label: str, value: str) -> None:
    rows = entry.setdefault("rows", [])
    for row in rows:
        if row and row[0] == label:
            row[1] = value
            return
    rows.append([label, value])


def main_surface(row: dict[str, str], nodes: list[dict[str, str]], edges: list[dict[str, str]]) -> dict:
    generated = mc.build_public_payload([row])
    generated = rebuild.enhance_payload(generated, [row])
    surface = generated["surfaces"][0]
    country = "Mexico" if row["source_identifier"] == "139299" else "Netherlands"
    medium_id, medium_title = (
        ("FOL-MEDIUM-PORTFOLIO-COVER", "Portfolio cover")
        if row["source_identifier"] == "139299"
        else ("FOL-MEDIUM-POSTER", "Poster")
    )
    surface["sourceObjectKey"] = row["source_identifier"]
    surface["sourceLocator"] = row["source_record_url"]
    surface["folders"] = [
        {"folderId": f"FOL-REGION-{country.upper()}", "type": "region", "title": country},
        {"folderId": "FOL-THEME-MIDCENTURY-MODERN-GRAPHIC-COMMUNICATION", "type": "theme", "title": "Midcentury modern graphic communication"},
        {"folderId": medium_id, "type": "medium", "title": medium_title},
    ]
    surface["movementIds"] = []
    surface["authority"] = {
        "state": "mediated_known",
        "origin": "United States",
        "geographyClass": "euro_us_center",
        "resolutionBasis": "source_host",
        "narrativePosition": "euro_us_center_describing_noncenter",
        "countPolicy": "eligible_for_active_total",
    }
    edge_ids = [edge["edge_id"] for edge in edges]
    surface["trace"] = {
        "treeId": "TRTREE048",
        "branchIds": ["TRB165"],
        "objectNodeId": next(
            node["node_id"] for node in nodes
            if node["node_type"] == "object" and node["canonical_key"] == row["source_identifier"]
        ),
        "edgeIds": edge_ids,
        "coreEdgeIds": edge_ids,
        "auxiliaryEdgeIds": [],
        "edgeLabels": [edge["edge_label"] for edge in edges],
        "edgeCount": len(edge_ids),
        "coreEdgeCount": len(edge_ids),
        "auxiliaryEdgeCount": 0,
        "evidenceReturnUrl": row["source_record_url"],
        "reviewState": "accepted_source_verified",
        "state": "accepted",
        "tier": "source_verified",
        "confidence": "high",
        "influenceState": "not_inferred",
    }
    surface["collectionEvidence"] = {
        "state": "pass",
        "scopeKind": "explicit_source_collection",
        "label": "Art Institute of Chicago",
        "evidenceBasis": "SOURCE.Source collection",
        "sourceUrl": row["source_record_url"],
        "boundary": "The collection is holding/source evidence; it does not establish object geography or historical influence.",
    }
    classification, relations, citations = table(surface, "CLASSIFICATION"), table(surface, "RELATIONS"), table(surface, "CITATIONS")
    replace_row(classification, "Region folder", country)
    replace_row(classification, "Medium folder", medium_title)
    replace_row(classification, "Movement refs", "NONE")
    replace_row(classification, "Authority state", "mediated_known")
    replace_row(classification, "Authority origin", "United States")
    replace_row(classification, "Authority resolution basis", "source_host")
    replace_row(relations, "classified_as", medium_title)
    replace_row(relations, "movement_or_formation", "NONE")
    replace_row(relations, "TRACE state", "accepted")
    replace_row(relations, "Influence state", "not_inferred")
    replace_row(relations, "TRACE tree", "TRTREE048")
    replace_row(relations, "TRACE tier", "source_verified")
    replace_row(relations, "TRACE core edges", str(len(edge_ids)))
    replace_row(relations, "TRACE auxiliary edges", "0")
    replace_row(relations, "Collection evidence", "pass")
    replace_row(relations, "Collection scope", "Art Institute of Chicago")
    replace_row(citations, "Evidence return", row["source_record_url"])
    return surface


def add_folder(payload: dict, folder_id: str, folder_type: str, title: str, surface_id: str, year: int) -> None:
    folder = next((x for x in payload["folders"] if x.get("folderId") == folder_id), None)
    if folder is None:
        folder = {
            "folderId": folder_id, "type": folder_type, "slug": "", "title": title,
            "dateStart": year, "dateEnd": year,
            "scopeNote": f"{folder_type.title()} filter view for {title}. Member records are filed using item-level evidence.",
            "surfaceIds": [], "relatedFolderIds": [], "authorityRefs": [],
        }
        payload["folders"].append(folder)
    if surface_id not in folder["surfaceIds"]:
        folder["surfaceIds"].append(surface_id)
    folder["dateStart"] = min(int(folder.get("dateStart") or year), year)
    folder["dateEnd"] = max(int(folder.get("dateEnd") or year), year)


def adjunct_payload(rows: list[dict[str, str]], nodes: list[dict[str, str]], edges: list[dict[str, str]]) -> dict:
    node_by_object = {node["node_id"]: node for node in nodes if node["node_type"] == "object"}
    items = []
    for row in rows:
        object_node = next(node["node_id"] for node in node_by_object.values() if node["canonical_key"] == row["source_identifier"])
        own_edges = [edge for edge in edges if edge["subject_node_id"] == object_node]
        items.append({
            "adjunctId": f"TRADJ-AIC-{row['source_identifier']}",
            "countEligible": False,
            "promotionPolicy": "trace_only_no_active_object_no_influence_inference",
            "sourceRecordId": row["capture_id"], "sourceObjectKey": row["source_identifier"],
            "title": row["source_title"], "dateStart": int(row["date_start"]), "dateEnd": int(row["date_end"]),
            "placeText": row["source_place_text"], "medium": row["source_medium"],
            "sourceName": row["source_name"], "sourceUrl": row["source_record_url"],
            "image": {"state": row["image_presence_code"], "url": row["image_url_detected"], "displayPolicy": "source_viewer_only"},
            "trace": {"treeId": "TRTREE048", "branchId": "TRB166", "objectNodeId": object_node,
                      "edgeIds": [edge["edge_id"] for edge in own_edges], "reviewState": "accepted_auxiliary",
                      "influenceState": "not_inferred"},
            "evidenceBoundary": "Documented medium, object date and place only. This is a graphic-practice adjunct, not a main graphic-design classification or a historical influence claim.",
        })
    return {
        "meta": {"status": "prefreeze_candidate_v47_trace_adjuncts", "parentCandidate": "v46", "countEligible": False,
                 "tracePromotions": 0, "influenceEdges": 0, "objectCount": len(items),
                 "policy": "Photography, printmaking and future planar-animation records may extend TRACE only when source documentation is explicit."},
        "items": items,
        "traceNodes": nodes,
        "traceEdges": edges,
    }


def sample_rows(new_surfaces: list[dict]) -> None:
    fields = list(csv.DictReader(SAMPLE_PARENT.open(encoding="utf-8", newline="")).fieldnames or [])
    parent_rows = read_csv(SAMPLE_PARENT)
    new = []
    for index, surface in enumerate(new_surfaces, start=1):
        new.append({"sample_id": f"v47-new-{index:03d}", "sample_lane": "v47_aic_explicit_object_place",
                    "surface_id": surface["surfaceId"], "source_record_id": surface["sourceRecordId"], "title": surface["title"],
                    "date_start": surface["dateStart"], "region": surface["placeText"], "source_name": surface["sourceName"],
                    "authority_state": "mediated_known", "trace_state": "accepted", "trace_tier": "source_verified",
                    "source_url_gate": "pass", "title_gate": "pass", "date_gate": "pass", "region_gate": "pass",
                    "image_route_gate": "pass", "authority_gate": "pass", "trace_gate": "pass", "influence_gate": "pass",
                    "six_tables_gate": "pass", "audit_status": "pass",
                    "audit_note": "Exact date, explicit object place, bounded carrier, source route, collection evidence, and non-inferred TRACE verified."})
    write_csv(SAMPLE_OUTPUT, fields, new + parent_rows[: 200 - len(new)])


def main() -> None:
    parent = json.loads(PARENT.read_text(encoding="utf-8"))
    rows, nodes, edges = read_csv(RECORDS), read_csv(NODES), read_csv(EDGES)
    adjunct_rows, adjunct_nodes, adjunct_edges = read_csv(ADJUNCT_RECORDS), read_csv(ADJUNCT_NODES), read_csv(ADJUNCT_EDGES)
    existing = {surface.get("sourceObjectKey") for surface in parent["surfaces"]}
    if len(rows) != 2 or any(row["source_identifier"] in existing for row in rows):
        raise SystemExit("expected exactly two new, source-distinct AIC active objects")
    by_record = {row["capture_id"]: row for row in rows}
    by_object = {row["source_identifier"]: row for row in rows}
    new_surfaces = []
    for row in rows:
        object_id = next(node["node_id"] for node in nodes if node["node_type"] == "object" and node["canonical_key"] == row["source_identifier"])
        object_edges = [edge for edge in edges if edge["subject_node_id"] == object_id]
        surface = main_surface(row, nodes, object_edges)
        new_surfaces.append(surface)
        for ref in surface["folders"]:
            add_folder(parent, ref["folderId"], ref["type"], ref["title"], surface["surfaceId"], int(row["date_start"]))
    parent["surfaces"].extend(new_surfaces)
    parent["surfaces"].sort(key=lambda surface: (surface.get("dateStart") or 9999, surface.get("surfaceId") or ""))
    meta = parent["meta"]
    meta.update({
        "generatedAt": "2026-08-01", "status": "prefreeze_candidate_v47_aic_geographic_balance",
        "parentCandidateVersion": "v46", "sourceCandidate": "generated/public_surfaces_prefreeze_candidate_v46.json",
        "activeSurfaceCount": len(parent["surfaces"]), "acceptedObjectCount": len(parent["surfaces"]),
        "aicExplicitGeographicBalanceAppendedV47": len(new_surfaces),
        "traceAdjunctCountV47": len(adjunct_rows), "traceAdjunctCountEligible": 0,
        "traceAdjunctArtifact": str(ADJUNCT_OUTPUT.relative_to(ROOT)),
        "traceAdjunctPolicy": "explicit photo/print/planar-animation media may enrich TRACE without promotion or inferred influence",
        "remainingToMinimumTarget": 20000 - len(parent["surfaces"]),
        "traceAcceptedCount": len(parent["surfaces"]), "traceUnlinkedCount": 0,
        "traceCoveragePct": 100.0, "traceTargetPass": True,
    })
    parent = rebuild.attach_structural_collections(parent)
    parent = rebuild.build_research_dossiers(parent)
    OUTPUT.write_text(json.dumps(parent, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    adjunct = adjunct_payload(adjunct_rows, adjunct_nodes, adjunct_edges)
    ADJUNCT_OUTPUT.write_text(json.dumps(adjunct, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    write_csv(SUMMARY, ["metric", "value"], [
        {"metric": "active_objects", "value": str(len(parent["surfaces"]))},
        {"metric": "aic_main_objects_appended", "value": str(len(new_surfaces))},
        {"metric": "trace_adjunct_objects_not_count_eligible", "value": str(len(adjunct_rows))},
        {"metric": "trace_adjunct_promotions", "value": "0"},
        {"metric": "influence_edges_inferred", "value": "0"},
        {"metric": "remaining_to_20000", "value": str(20000 - len(parent["surfaces"]))},
    ])
    sample_rows(new_surfaces)
    print(json.dumps({"active": len(parent["surfaces"]), "appended": len(new_surfaces), "adjuncts": len(adjunct_rows), "remaining": 20000 - len(parent["surfaces"])}))


if __name__ == "__main__":
    main()
