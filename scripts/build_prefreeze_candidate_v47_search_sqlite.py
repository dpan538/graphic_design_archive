#!/usr/bin/env python3
"""Incrementally synchronize v47 against the frozen v46 SQLite baseline.

This avoids reviving removed historical build dependencies.  Only v47's two
active AIC objects and its explicitly non-counted print/photo TRACE adjuncts
are inserted.  The frozen v46 database is never modified.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA, GENERATED, DOCS = ROOT / "data", ROOT / "generated", ROOT / "docs" / "capture"
VERSION = "v47"
INPUT = GENERATED / "public_surfaces_prefreeze_candidate_v47.json"
BASELINE, OUTPUT = DATA / "prefreeze_candidate_v46.sqlite", DATA / "prefreeze_candidate_v47.sqlite"
GATE, BENCHMARK = DATA / "prefreeze_candidate_v47_search_gate.csv", DATA / "prefreeze_candidate_v47_search_benchmark.csv"
REPORT = DOCS / "PREFREEZE_CANDIDATE_v47_SEARCH_TRACE.md"
STEM = "capture_batch_trace_first_aic_geographic_balance_v47"
NODES, EDGES = DATA / f"{STEM}_trace_nodes.csv", DATA / f"{STEM}_trace_edges.csv"
ADJUNCT = GENERATED / "prefreeze_candidate_v47_aic_trace_adjuncts.json"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def doc_id(url: str) -> str:
    return "SRCDOC-" + hashlib.sha1(url.encode()).hexdigest()[:16].upper()


def add_trace(conn: sqlite3.Connection, nodes: list[dict[str, str]], edges: list[dict[str, str]]) -> None:
    conn.executemany("insert or ignore into trace_nodes values (?, ?, ?, ?, ?, ?, ?, ?, ?)", [
        (x["node_id"], x["tree_id"], x["node_type"], x["label"], x["canonical_key"], x["region"], x["source_url"], x["evidence"], x["evidence_status"]) for x in nodes
    ])
    conn.executemany("insert or ignore into trace_edges values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
        (x["edge_id"], x["tree_id"], x["branch_id"], x["subject_node_id"], x["object_node_id"], x["edge_label"], x["evidence_url"], x["evidence_text"], x["evidence_field"], x["confidence"], x["review_state"], x["prohibited_inference_check"]) for x in edges
    ])


def add_active_surface(conn: sqlite3.Connection, surface: dict) -> None:
    source_url = surface["sourceUrl"]; source_document_id = doc_id(source_url)
    conn.execute("insert or ignore into source_documents values (?, ?, ?, 0, 0)", (source_document_id, source_url, surface["sourceName"]))
    trace, authority, image, rights = surface["trace"], surface["authority"], surface.get("image", {}), surface.get("rights", {})
    conn.execute(
        """insert into objects values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (surface["surfaceId"], surface["sourceRecordId"], surface["sourceObjectKey"], "source_object_key", source_document_id, surface["sourceLocator"],
         surface["title"], surface.get("creator", ""), surface.get("dateText", ""), int(surface["dateStart"]), int(surface.get("dateEnd") or surface["dateStart"]),
         surface["placeText"], surface.get("medium", ""), surface.get("objectType", ""), surface["sourceName"], source_url, surface.get("descriptionSummary", ""),
         surface.get("sourceNotes", ""), surface.get("sourceSubjects", ""), image.get("state", "IMG00"), image.get("url"), rights.get("state", ""),
         authority.get("origin", ""), authority.get("geographyClass", ""), trace.get("treeId", ""), trace.get("objectNodeId", ""), int(trace.get("edgeCount") or 0), trace.get("evidenceReturnUrl", ""),
         authority.get("state", ""), authority.get("resolutionBasis", ""), authority.get("narrativePosition", ""), trace.get("state", ""), trace.get("tier", ""), trace.get("confidence", ""),
         int(trace.get("coreEdgeCount") or 0), int(trace.get("auxiliaryEdgeCount") or 0), 1)
    )
    conn.execute("update source_documents set object_count=object_count+1 where source_document_id=?", (source_document_id,))
    conn.executemany("insert into object_folder_refs values (?, ?, ?, ?)", [(surface["surfaceId"], x["folderId"], x["type"], x["title"]) for x in surface.get("folders", [])])
    metadata = []
    for entry in surface.get("tables", []):
        for order, row in enumerate(entry.get("rows", [])):
            metadata.append((surface["surfaceId"], entry["kind"], order, str(row[0]), str(row[1])))
    conn.executemany("insert into object_metadata_rows values (?, ?, ?, ?, ?)", metadata)
    body = "\n".join([surface["title"], surface.get("descriptionSummary", ""), surface.get("sourceDescription", ""), surface.get("historicalContextNote", ""), surface.get("classificationRationale", ""), surface.get("citationBasis", ""), f"authority_state: {authority['state']}", f"trace_state: {trace['state']}", f"trace_tier: {trace['tier']}", "count_state: active"])
    conn.execute("insert into search_documents values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (f"active:{surface['surfaceId']}", "active_object", surface["surfaceId"], surface["title"], body, surface["placeText"], surface["sourceName"], int(surface["dateStart"]), "active_candidate", 1, authority["state"], trace["state"], trace["tier"]))
    conn.executemany("insert into object_trace_edges values (?, ?)", [(surface["surfaceId"], x) for x in trace["edgeIds"]])


def add_adjunct_search(conn: sqlite3.Connection, adjunct: dict) -> None:
    for item in adjunct["items"]:
        trace = item["trace"]
        body = "\n".join([item["title"], item["medium"], item["evidenceBoundary"], f"source_url: {item['sourceUrl']}", "countEligible: false", "trace_state: accepted_auxiliary", "influence_state: not_inferred", "count_state: trace_adjunct"])
        conn.execute("insert into search_documents values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (f"trace_adjunct:{item['adjunctId']}", "trace_adjunct", item["adjunctId"], item["title"], body, item["placeText"], item["sourceName"], item["dateStart"], "trace_adjunct_not_count_eligible", 0, "mediated_known", "accepted_auxiliary", "auxiliary"))


def scalar(conn: sqlite3.Connection, sql: str) -> int:
    return int(conn.execute(sql).fetchone()[0])


def gate_rows(conn: sqlite3.Connection, active: int, adjunct_count: int) -> list[dict[str, object]]:
    values = {
        "sqlite_integrity": str(conn.execute("pragma integrity_check").fetchone()[0]),
        "active_object_count": scalar(conn, "select count(*) from objects where count_eligible=1"),
        "authority_uncertain_active_leak": scalar(conn, "select count(*) from objects where count_eligible=1 and authority_state='uncertain'"),
        "trace_unlinked_active": scalar(conn, "select count(*) from objects where count_eligible=1 and trace_state<>'accepted'"),
        "accepted_trace_without_indexed_edges": scalar(conn, "select count(*) from objects o where o.count_eligible=1 and not exists (select 1 from object_trace_edges e where e.surface_id=o.surface_id)"),
        "influence_edges": scalar(conn, "select count(*) from trace_edges where edge_label='influenced_by'"),
        "filename_extension_titles": scalar(conn, "select count(*) from objects where lower(title) glob '*.jpg' or lower(title) glob '*.jpeg' or lower(title) glob '*.png' or lower(title) glob '*.webp'"),
        "trace_adjunct_active_leak": scalar(conn, "select count(*) from search_documents where document_type='trace_adjunct' and active_object<>0"),
        "trace_adjunct_count": scalar(conn, "select count(*) from search_documents where document_type='trace_adjunct'"),
    }
    requirements = {"sqlite_integrity": "ok", "active_object_count": str(active), "authority_uncertain_active_leak": "0", "trace_unlinked_active": "0", "accepted_trace_without_indexed_edges": "0", "influence_edges": "0", "filename_extension_titles": "0", "trace_adjunct_active_leak": "0", "trace_adjunct_count": str(adjunct_count)}
    return [{"gate": key, "value": value, "status": "PASS" if str(value) == requirements[key] else "HOLD", "requirement": requirements[key], "note": "v47 incremental search and TRACE synchronization"} for key, value in values.items()]


def main() -> None:
    payload = json.loads(INPUT.read_text(encoding="utf-8")); adjunct = json.loads(ADJUNCT.read_text(encoding="utf-8"))
    if OUTPUT.exists(): OUTPUT.unlink()
    shutil.copy2(BASELINE, OUTPUT)
    main_surfaces = [x for x in payload["surfaces"] if str(x.get("sourceRecordId", "")).startswith("AICTRACEV47")]
    if len(main_surfaces) != 2 or len(adjunct["items"]) != 11: raise SystemExit("unexpected v47 additions")
    nodes, edges = read_csv(NODES), read_csv(EDGES)
    conn = sqlite3.connect(OUTPUT)
    try:
        add_trace(conn, nodes, edges); add_trace(conn, adjunct["traceNodes"], adjunct["traceEdges"])
        for surface in main_surfaces: add_active_surface(conn, surface)
        add_adjunct_search(conn, adjunct)
        conn.execute("insert into search_documents_fts(search_documents_fts) values('rebuild')")
        conn.execute("update schema_meta set value=? where key='active_object_count'", (str(len(payload["surfaces"])),))
        conn.execute("update schema_meta set value=? where key='candidate_status'", ("prefreeze_candidate_v47",))
        conn.execute("update schema_meta set value=? where key='schema_version'", ("prefreeze_candidate_v47_sqlite_v1",))
        conn.execute("update schema_meta set value=? where key='source_payload'", (str(INPUT.relative_to(ROOT)),))
        conn.executescript("""
        drop view if exists active_objects_current; create view active_objects_current as select * from objects where count_eligible=1;
        drop view if exists trace_accepted_objects_current; create view trace_accepted_objects_current as select * from objects where trace_state='accepted';
        drop view if exists metadata_supported_objects_current; create view metadata_supported_objects_current as select * from objects where trace_tier='metadata_supported';
        drop view if exists searchable_review_documents_current; create view searchable_review_documents_current as select * from search_documents where active_object=0;
        """)
        rows = gate_rows(conn, len(payload["surfaces"]), len(adjunct["items"])); conn.commit()
        bench = []
        for query in ("poster", "photography", "lithograph", "Mexico", "TRACE"):
            count = scalar(conn, "select count(*) from search_documents_fts where search_documents_fts match ?",) if False else int(conn.execute("select count(*) from search_documents_fts where search_documents_fts match ?", (query,)).fetchone()[0])
            bench.append({"query": query, "result_count": count})
    finally:
        conn.close()
    write_csv(GATE, ["gate", "value", "status", "requirement", "note"], rows)
    write_csv(BENCHMARK, ["query", "result_count"], bench)
    REPORT.write_text("\n".join(["# Prefreeze candidate v47 incremental search and TRACE", "", "- v46 SQLite copied without mutation; v47 is an isolated incremental database.", f"- Active objects: {len(payload['surfaces']):,}.", f"- Main AIC objects: {len(main_surfaces)}.", f"- Photography/print TRACE adjuncts: {len(adjunct['items'])}; count eligible: 0; inferred influence: 0.", "", "## Gates", ""] + [f"- {x['gate']}: {x['value']} — {x['status']}" for x in rows]) + "\n", encoding="utf-8")
    print(json.dumps({"active": len(payload["surfaces"]), "adjuncts": len(adjunct["items"]), "gates_pass": sum(x["status"] == "PASS" for x in rows), "gates": len(rows)}))


if __name__ == "__main__": main()
