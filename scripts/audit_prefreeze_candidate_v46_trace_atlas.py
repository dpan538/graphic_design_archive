#!/usr/bin/env python3
"""Build audited, aggregate-only data for the prefreeze v46 TRACE atlas.

This is deliberately not a force-layout exporter.  The active TRACE graph has
enough evidence nodes and edges that rendering every point at once would turn
the atlas into an unreadable density field.  The outputs instead retain the
three safe, queryable views needed by the product:

* object lineage, expanded only after an object is selected;
* object geography by decade; and
* source-family to object-geography distribution.

No geographic co-occurrence or temporal adjacency is promoted to an historical
influence claim.  The report explicitly records the separately-evidenced
``influenced_by`` count so the UI can keep that layer absent until such evidence
exists.
"""

from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
GENERATED = ROOT / "generated"
DOCS = ROOT / "docs" / "capture"
VERSION = "v46"
DB = DATA / f"prefreeze_candidate_{VERSION}.sqlite"
SUMMARY = DATA / f"prefreeze_candidate_{VERSION}_trace_atlas_summary.csv"
EDGE_ROLES = DATA / f"prefreeze_candidate_{VERSION}_trace_atlas_edge_roles.csv"
GEO_DECADES = DATA / f"prefreeze_candidate_{VERSION}_trace_atlas_geo_decades.csv"
SOURCE_GEO = DATA / f"prefreeze_candidate_{VERSION}_trace_atlas_source_geography.csv"
MANIFEST = GENERATED / f"prefreeze_candidate_{VERSION}_trace_atlas_manifest.json"
REPORT = DOCS / f"PREFREEZE_CANDIDATE_{VERSION.upper()}_TRACE_ATLAS.md"


def rows(conn: sqlite3.Connection, query: str, params: tuple[object, ...] = ()) -> list[dict[str, object]]:
    return [dict(row) for row in conn.execute(query, params)]


def scalar(conn: sqlite3.Connection, query: str) -> int:
    value = conn.execute(query).fetchone()[0]
    return int(value or 0)


def write_csv(path: Path, fieldnames: list[str], data: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(data)


def main() -> None:
    if not DB.exists():
        raise SystemExit(f"Missing synchronized TRACE database: {DB}")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    active = scalar(conn, "select count(*) from active_objects_v46")
    accepted = scalar(conn, "select count(*) from trace_accepted_objects_v46")
    all_nodes = scalar(conn, "select count(*) from trace_nodes")
    all_edges = scalar(conn, "select count(*) from trace_edges")
    active_edges = scalar(
        conn,
        """
        with active_edges as (
          select distinct ote.edge_id
          from object_trace_edges ote
          join active_objects_v46 a on a.surface_id = ote.surface_id
        ) select count(*) from active_edges
        """,
    )
    active_nodes = scalar(
        conn,
        """
        with active_edges as (
          select distinct ote.edge_id
          from object_trace_edges ote
          join active_objects_v46 a on a.surface_id = ote.surface_id
        ), active_nodes as (
          select t.subject_node_id as node_id from trace_edges t join active_edges a on a.edge_id = t.edge_id
          union
          select t.object_node_id from trace_edges t join active_edges a on a.edge_id = t.edge_id
        ) select count(*) from active_nodes
        """,
    )
    geography_regions = scalar(conn, "select count(distinct region) from active_objects_v46")
    decades = scalar(conn, "select count(distinct (date_start / 10) * 10) from active_objects_v46")
    source_families = scalar(conn, "select count(distinct source_name) from active_objects_v46")
    historical_influence = scalar(conn, "select count(*) from trace_edges where edge_label = 'influenced_by'")

    role_by_label = {
        "documented_by": ("source evidence", "lineage"),
        "associated_with_place": ("object geography", "lineage"),
        "created_by": ("attribution", "lineage"),
        "associated_with_year": ("object chronology", "lineage"),
        "part_of_series": ("object structure", "lineage"),
        "part_of_collection": ("object structure", "lineage"),
        "issued_by": ("publication relation", "lineage"),
        "circulated_in": ("circulation relation", "lineage"),
        "influenced_by": ("historical relation", "only when evidence is explicit"),
    }
    active_edge_rows = rows(
        conn,
        """
        with active_edges as (
          select distinct ote.edge_id
          from object_trace_edges ote join active_objects_v46 a on a.surface_id = ote.surface_id
        )
        select t.edge_label, count(*) as edge_count
        from trace_edges t join active_edges ae on ae.edge_id = t.edge_id
        group by t.edge_label order by edge_count desc, t.edge_label
        """,
    )
    edge_rows: list[dict[str, object]] = []
    for row in active_edge_rows:
        label = str(row["edge_label"])
        role, atlas_policy = role_by_label.get(label, ("descriptive or contextual metadata", "context only"))
        edge_rows.append(
            {
                "edge_label": label,
                "active_edge_count": row["edge_count"],
                "semantic_role": role,
                "atlas_policy": atlas_policy,
            }
        )
    write_csv(EDGE_ROLES, ["edge_label", "active_edge_count", "semantic_role", "atlas_policy"], edge_rows)

    geo_rows = rows(
        conn,
        """
        select (date_start / 10) * 10 as decade, region, count(*) as object_count,
               count(distinct source_name) as source_family_count
        from active_objects_v46
        group by decade, region
        order by decade, object_count desc, region
        """,
    )
    write_csv(GEO_DECADES, ["decade", "region", "object_count", "source_family_count"], geo_rows)

    source_geo_rows = rows(
        conn,
        """
        select source_name, region, count(*) as object_count,
               min(date_start) as first_year, max(date_start) as last_year
        from active_objects_v46
        group by source_name, region
        order by object_count desc, source_name, region
        """,
    )
    write_csv(SOURCE_GEO, ["source_name", "region", "object_count", "first_year", "last_year"], source_geo_rows)

    metrics = [
        ("candidate_version", VERSION),
        ("active_objects", active),
        ("accepted_trace_objects", accepted),
        ("full_trace_nodes", all_nodes),
        ("full_trace_edges", all_edges),
        ("active_trace_subgraph_nodes", active_nodes),
        ("active_trace_subgraph_edges", active_edges),
        ("object_regions", geography_regions),
        ("decade_bins", decades),
        ("source_families", source_families),
        ("historical_influence_edges", historical_influence),
        ("full_client_graph_allowed", "no"),
        ("object_lineage_expand_limit", 200),
    ]
    write_csv(SUMMARY, ["metric", "value"], [{"metric": key, "value": value} for key, value in metrics])

    payload = {
        "version": VERSION,
        "scope": "active accepted TRACE only",
        "semantics": {
            "documented_lineage": "May be drawn as an evidence-return path.",
            "geotime": "Shows object-place and object-year aggregation, not causality.",
            "historical_influence": "May render only explicit influenced_by edges with direct evidence.",
        },
        "views": {
            "object_lineage": {"mode": "on-demand", "max_nodes": 200, "source": "SQLite adjacency query"},
            "geo_time": {"mode": "aggregate", "file": GEO_DECADES.name, "rows": len(geo_rows)},
            "source_geography": {"mode": "aggregate", "file": SOURCE_GEO.name, "rows": len(source_geo_rows)},
        },
        "metrics": dict(metrics),
        "files": [SUMMARY.name, EDGE_ROLES.name, GEO_DECADES.name, SOURCE_GEO.name],
    }
    MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report_lines = [
        f"# Prefreeze candidate {VERSION} TRACE atlas",
        "",
        "## Current evidence base",
        "",
        f"- active objects: {active:,}",
        f"- accepted TRACE objects: {accepted:,}",
        f"- active TRACE subgraph: {active_nodes:,} nodes / {active_edges:,} edges",
        f"- full stored TRACE graph: {all_nodes:,} nodes / {all_edges:,} edges",
        f"- object geography: {geography_regions} regions across {decades} decade bins and {source_families} source families",
        f"- evidence-backed historical `influenced_by` edges: {historical_influence}",
        "",
        "## Product decision",
        "",
        "A single browser force graph of every TRACE point is not an acceptable primary visualisation: it would be dense, slow, and would obscure the evidentiary difference between source lineage, metadata context, and historical relations.",
        "",
        "Use three connected views instead:",
        "",
        "1. **Object lineage explorer** — expand one selected object upward to its source root and downward to justified structural nodes. Cap an expansion at 200 nodes; always expose evidence URLs and edge labels.",
        "2. **Geo–time atlas** — render the `region × decade` aggregate as a map, heatmap, or flowing timeline. It may indicate concentration, absence, co-location, or chronological sequence only.",
        "3. **Source–geography matrix** — render source-family to object-geography counts to expose institutional concentration and counterweight gaps without assigning a source's location to the object.",
        "",
        "## Semantic guardrails",
        "",
        "- `documented_by`, object place, creator, year, collection, and series relations can be used in a lineage view only with their current evidence labels.",
        "- Geographic proximity, shared collection, and decade co-occurrence must use neutral language such as `co-located`, `concurrent`, or `shared source context`; none may display as influence arrows.",
        "- Historical arrows remain disabled because the active TRACE contains zero `influenced_by` evidence edges. Introducing arrows before direct evidence would manufacture history rather than reveal it.",
        "- An uncertain authority or review-only object must remain outside all primary atlas aggregates until it passes the active-layer gate.",
        "",
        "## Implementation boundary",
        "",
        "The web client should receive small aggregate CSV/JSON payloads and retrieve selected-object adjacency from a query endpoint or pre-chunked object bundle. The 400 MB SQLite search database and full 97k-node graph are build/research artifacts, not browser payloads.",
        "",
        "## Generated inputs",
        "",
        f"- `{SUMMARY.name}`",
        f"- `{EDGE_ROLES.name}`",
        f"- `{GEO_DECADES.name}`",
        f"- `{SOURCE_GEO.name}`",
        f"- `{MANIFEST.name}`",
    ]
    REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    conn.close()
    print(json.dumps({"active_objects": active, "active_nodes": active_nodes, "active_edges": active_edges, "geo_decade_rows": len(geo_rows), "source_geo_rows": len(source_geo_rows), "influence_edges": historical_influence}, ensure_ascii=False))


if __name__ == "__main__":
    main()
