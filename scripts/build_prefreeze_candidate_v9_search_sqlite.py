#!/usr/bin/env python3
"""Build synchronized v9 object, review, TRACE, and FTS layers."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from statistics import median
from typing import Any

import build_prefreeze_candidate_v4_sqlite as base
import build_prefreeze_candidate_v6_search_sqlite as v6search


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"
INPUT = ROOT / "generated" / "public_surfaces_prefreeze_candidate_v9.json"
OUTPUT = DATA / "prefreeze_candidate_v9.sqlite"
BASE_GATE = DATA / "prefreeze_candidate_v9_base_database_gate.csv"
GATE = DATA / "prefreeze_candidate_v9_search_gate.csv"
BENCHMARK = DATA / "prefreeze_candidate_v9_search_benchmark.csv"
REPORT = DOCS / "PREFREEZE_CANDIDATE_v9_SEARCH_TRACE.md"
AUTHORITY_REVIEW = (
    DATA / "prefreeze_candidate_v5_authority_uncertain_queue.csv"
)

CAPTURE_BATCHES = v6search.CAPTURE_BATCHES + (
    {
        "batch": "spc_pacific_v2",
        "records": DATA
        / "capture_batch_trace_first_spc_pacific_2026_v2_records.csv",
        "quality": DATA
        / "capture_batch_trace_first_spc_pacific_2026_v2_quality.csv",
        "nodes": DATA
        / "capture_batch_trace_first_spc_pacific_2026_v2_trace_nodes.csv",
        "edges": DATA
        / "capture_batch_trace_first_spc_pacific_2026_v2_trace_edges.csv",
    },
)

EXTRA_TRACE_FILES = (
    (
        DATA / "capture_batch_trace_enrich_vam_existing_2026_v1_trace_nodes.csv",
        DATA / "capture_batch_trace_enrich_vam_existing_2026_v1_trace_edges.csv",
    ),
    (
        DATA
        / "capture_batch_trace_enrich_commons_existing_2026_v1_trace_nodes.csv",
        DATA
        / "capture_batch_trace_enrich_commons_existing_2026_v1_trace_edges.csv",
    ),
    (
        DATA
        / "capture_batch_trace_associative_existing_2026_v1_trace_nodes.csv",
        DATA
        / "capture_batch_trace_associative_existing_2026_v1_trace_edges.csv",
    ),
    (
        DATA
        / "capture_batch_trace_geo_repair_existing_2026_v1_trace_nodes.csv",
        DATA
        / "capture_batch_trace_geo_repair_existing_2026_v1_trace_edges.csv",
    ),
)

GATE_FIELDS = ["gate", "value", "status", "requirement", "note"]
BENCHMARK_FIELDS = [
    "query",
    "iterations",
    "result_count",
    "min_ms",
    "median_ms",
    "p95_ms",
    "max_ms",
]


def clean(value: Any) -> str:
    return base.clean(value)


def read_csv(path: Path) -> list[dict[str, str]]:
    return base.read_csv(path)


def write_csv(
    path: Path, fields: list[str], rows: list[dict[str, Any]]
) -> None:
    base.write_csv(path, fields, rows)


def add_column(
    conn: sqlite3.Connection, table: str, name: str, definition: str
) -> None:
    columns = {
        str(row[1]) for row in conn.execute(f"pragma table_info({table})")
    }
    if name not in columns:
        conn.execute(
            f'alter table "{table}" add column "{name}" {definition}'
        )


def add_trace_files(conn: sqlite3.Connection) -> None:
    for nodes_path, edges_path in EXTRA_TRACE_FILES:
        conn.executemany(
            """
            insert or ignore into trace_nodes values (
              ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            [
                (
                    row["node_id"],
                    row["tree_id"],
                    row["node_type"],
                    row["label"],
                    row["canonical_key"],
                    row["region"],
                    row["source_url"],
                    row["evidence"],
                    row["evidence_status"],
                )
                for row in read_csv(nodes_path)
            ],
        )
        conn.executemany(
            """
            insert or ignore into trace_edges values (
              ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            [
                (
                    row["edge_id"],
                    row["tree_id"],
                    row["branch_id"],
                    row["subject_node_id"],
                    row["object_node_id"],
                    row["edge_label"],
                    row["evidence_url"],
                    row["evidence_text"],
                    row["evidence_field"],
                    row["confidence"],
                    row["review_state"],
                    row["prohibited_inference_check"],
                )
                for row in read_csv(edges_path)
            ],
        )


def synchronize_candidate(
    conn: sqlite3.Connection, payload: dict[str, Any]
) -> None:
    object_columns = (
        ("authority_state", "text not null default 'uncertain'"),
        ("authority_resolution_basis", "text not null default ''"),
        ("narrative_position", "text not null default ''"),
        ("trace_state", "text not null default 'unlinked'"),
        ("trace_tier", "text not null default 'unlinked'"),
        ("trace_confidence", "text not null default ''"),
        ("trace_core_edge_count", "integer not null default 0"),
        ("trace_auxiliary_edge_count", "integer not null default 0"),
        ("count_eligible", "integer not null default 0"),
    )
    for name, definition in object_columns:
        add_column(conn, "objects", name, definition)
    search_columns = (
        ("authority_state", "text not null default 'uncertain'"),
        ("trace_state", "text not null default 'unlinked'"),
        ("trace_tier", "text not null default 'unlinked'"),
    )
    for name, definition in search_columns:
        add_column(conn, "search_documents", name, definition)

    add_trace_files(conn)
    conn.executescript(
        """
        drop table if exists authority_review_objects_v9;
        create table authority_review_objects_v9 (
          review_id text primary key,
          surface_id text not null unique,
          source_record_id text not null,
          source_name text not null,
          source_host text not null,
          source_url text not null,
          title text not null,
          date_start integer,
          region text not null,
          authority_state text not null,
          authority_origin text not null,
          authority_geography_class text not null,
          authority_resolution_basis text not null,
          narrative_position text not null,
          trace_state text not null,
          review_route text not null,
          count_policy text not null
        );
        """
    )
    review_rows = read_csv(AUTHORITY_REVIEW)
    conn.executemany(
        """
        insert into authority_review_objects_v9 values (
          ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        """,
        [
            (
                row["review_id"],
                row["surface_id"],
                row["source_record_id"],
                row["source_name"],
                row["source_host"],
                row["source_url"],
                row["title"],
                int(row["date_start"]) if clean(row["date_start"]) else None,
                row["region"],
                row["authority_state"],
                row["authority_origin"],
                row["authority_geography_class"],
                row["authority_resolution_basis"],
                row["narrative_position"],
                row["trace_state"],
                row["review_route"],
                row["count_policy"],
            )
            for row in review_rows
        ],
    )
    conn.executemany(
        """
        insert into search_documents (
          search_doc_id, document_type, object_or_capture_id,
          title, body, region, source_name, date_start,
          quality_route, active_object,
          authority_state, trace_state, trace_tier
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                f"authority_review:{row['surface_id']}",
                "authority_uncertain_object",
                row["surface_id"],
                row["title"],
                "\n".join(
                    [
                        f"source_url: {row['source_url']}",
                        f"source_host: {row['source_host']}",
                        (
                            "authority_resolution_basis: "
                            f"{row['authority_resolution_basis']}"
                        ),
                        f"narrative_position: {row['narrative_position']}",
                        f"review_route: {row['review_route']}",
                        "authority_state: uncertain",
                        "trace_state: unlinked",
                        "trace_tier: unlinked",
                        "count_state: review",
                    ]
                ),
                row["region"],
                row["source_name"],
                int(row["date_start"]) if clean(row["date_start"]) else None,
                "authority_uncertain_hold",
                0,
                "uncertain",
                "unlinked",
                "unlinked",
            )
            for row in review_rows
        ],
    )
    object_updates = []
    trace_links = []
    for surface in payload.get("surfaces") or []:
        authority = (
            surface.get("authority")
            if isinstance(surface.get("authority"), dict)
            else {}
        )
        trace = (
            surface.get("trace")
            if isinstance(surface.get("trace"), dict)
            else {}
        )
        state = clean(authority.get("state"))
        accepted = bool(
            clean(trace.get("objectNodeId"))
            and int(trace.get("edgeCount") or 0) > 0
            and clean(trace.get("evidenceReturnUrl")).startswith(
                ("http://", "https://")
            )
        )
        trace_tier = clean(trace.get("tier")) or (
            "source_verified" if accepted else "unlinked"
        )
        object_updates.append(
            (
                state,
                clean(authority.get("resolutionBasis")),
                clean(authority.get("narrativePosition")),
                "accepted" if accepted else "unlinked",
                trace_tier,
                clean(trace.get("confidence")),
                int(
                    trace.get("coreEdgeCount")
                    or (trace.get("edgeCount") if accepted else 0)
                    or 0
                ),
                int(trace.get("auxiliaryEdgeCount") or 0),
                int(
                    state
                    in {
                        "resolved_origin",
                        "mediated_known",
                        "verified",
                        # A record directly verified against its named
                        # institutional item page is count-eligible, while
                        # its host geography still remains separate from the
                        # object's documented place.
                        "institutional_primary",
                    }
                ),
                clean(surface.get("surfaceId")),
            )
        )
        trace_links.extend(
            (
                clean(surface.get("surfaceId")),
                clean(edge_id),
            )
            for edge_id in trace.get("edgeIds") or []
            if clean(edge_id)
        )
    conn.executemany(
        """
        update objects
        set authority_state=?,
            authority_resolution_basis=?,
            narrative_position=?,
            trace_state=?,
            trace_tier=?,
            trace_confidence=?,
            trace_core_edge_count=?,
            trace_auxiliary_edge_count=?,
            count_eligible=?
        where surface_id=?
        """,
        object_updates,
    )
    existing_edges = {
        row[0] for row in conn.execute("select edge_id from trace_edges")
    }
    conn.executemany(
        "insert or ignore into object_trace_edges values (?, ?)",
        [
            (surface_id, edge_id)
            for surface_id, edge_id in trace_links
            if edge_id in existing_edges
        ],
    )
    conn.execute(
        """
        update search_documents
        set authority_state=coalesce((
              select authority_state from objects
              where surface_id=search_documents.object_or_capture_id
            ), authority_state),
            trace_state=coalesce((
              select trace_state from objects
              where surface_id=search_documents.object_or_capture_id
            ), trace_state),
            trace_tier=coalesce((
              select trace_tier from objects
              where surface_id=search_documents.object_or_capture_id
            ), trace_tier)
        where active_object=1
        """
    )
    conn.execute(
        """
        update search_documents
        set authority_state=case
              when exists (
                select 1 from capture_records c
                where c.capture_id=search_documents.object_or_capture_id
                  and trim(c.source_authority_origin)<>''
              ) then 'known_review_source'
              else 'uncertain'
            end,
            trace_state=case
              when exists (
                select 1 from capture_records c
                where c.capture_id=search_documents.object_or_capture_id
                  and trim(c.tree_id)<>''
              ) then 'context_linked'
              else 'unlinked'
            end,
            trace_tier=case
              when exists (
                select 1 from capture_records c
                where c.capture_id=search_documents.object_or_capture_id
                  and trim(c.tree_id)<>''
              ) then 'review_context'
              else 'unlinked'
            end
        where active_object=0
        """
    )
    conn.execute(
        """
        update search_documents
        set body=body
          || char(10) || 'authority_state: ' || authority_state
          || char(10) || 'trace_state: ' || trace_state
          || char(10) || 'trace_tier: ' || trace_tier
          || char(10) || 'count_state: '
             || case when active_object=1 then 'active' else 'review' end
        """
    )
    conn.execute(
        "insert into search_documents_fts(search_documents_fts) values('rebuild')"
    )
    conn.executescript(
        """
        drop view if exists active_objects_v9;
        create view active_objects_v9 as
        select * from objects where count_eligible=1;

        drop view if exists trace_accepted_objects_v9;
        create view trace_accepted_objects_v9 as
        select * from objects where trace_state='accepted';

        drop view if exists metadata_supported_objects_v9;
        create view metadata_supported_objects_v9 as
        select * from objects where trace_tier='metadata_supported';

        drop view if exists searchable_review_documents_v9;
        create view searchable_review_documents_v9 as
        select * from search_documents where active_object=0;

        create index if not exists objects_authority_state_v9_idx
          on objects(authority_state, count_eligible);
        create index if not exists objects_trace_tier_v9_idx
          on objects(trace_state, trace_tier);
        create index if not exists search_authority_trace_v9_idx
          on search_documents(active_object, authority_state, trace_state, trace_tier);
        create index if not exists trace_edges_label_object_v9_idx
          on trace_edges(edge_label, object_node_id, edge_id);
        create index if not exists object_trace_edges_reverse_v9_idx
          on object_trace_edges(edge_id, surface_id);
        create index if not exists authority_review_region_v9_idx
          on authority_review_objects_v9(region, date_start);
        """
    )
    conn.execute(
        """
        update schema_meta
        set value='prefreeze_candidate_v9_sqlite_v1'
        where key='schema_version'
        """
    )
    conn.execute(
        """
        update schema_meta
        set value='prefreeze_candidate_v9'
        where key='candidate_status'
        """
    )


def scalar(conn: sqlite3.Connection, sql: str) -> int:
    return int(conn.execute(sql).fetchone()[0])


def gates(
    conn: sqlite3.Connection, expected_active: int
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    metrics = {
        "active_objects": scalar(
            conn, "select count(*) from active_objects_v9"
        ),
        "authority_uncertain_active": scalar(
            conn,
            """
            select count(*) from objects
            where authority_state='uncertain' and count_eligible=1
            """,
        ),
        "trace_accepted_objects": scalar(
            conn, "select count(*) from trace_accepted_objects_v9"
        ),
        "metadata_supported_objects": scalar(
            conn, "select count(*) from metadata_supported_objects_v9"
        ),
        "trace_unlinked_objects": scalar(
            conn, "select count(*) from objects where trace_state='unlinked'"
        ),
        "review_documents": scalar(
            conn, "select count(*) from searchable_review_documents_v9"
        ),
        "authority_review_objects": scalar(
            conn, "select count(*) from authority_review_objects_v9"
        ),
        "search_documents": scalar(
            conn, "select count(*) from search_documents"
        ),
        "active_search_documents": scalar(
            conn,
            "select count(*) from search_documents where active_object=1",
        ),
        "trace_nodes": scalar(conn, "select count(*) from trace_nodes"),
        "trace_edges": scalar(conn, "select count(*) from trace_edges"),
        "object_trace_edges": scalar(
            conn, "select count(*) from object_trace_edges"
        ),
    }
    integrity = str(conn.execute("pragma integrity_check").fetchone()[0])
    accepted_incomplete = scalar(
        conn,
        """
        select count(*) from objects
        where trace_state='accepted'
          and (
            trace_object_node_id is null
            or trace_edge_count < 1
            or trace_evidence_url not like 'http%'
          )
        """,
    )
    accepted_without_links = scalar(
        conn,
        """
        select count(*) from objects o
        where o.trace_state='accepted'
          and not exists (
            select 1 from object_trace_edges e
            where e.surface_id=o.surface_id
          )
        """,
    )
    supported_unresolved = scalar(
        conn,
        """
        select count(*) from objects
        where trace_tier='metadata_supported'
          and region='Unresolved region'
        """,
    )
    supported_core_incomplete = scalar(
        conn,
        """
        select count(*) from objects
        where trace_tier='metadata_supported'
          and trace_core_edge_count < 3
        """,
    )
    influence_edges = scalar(
        conn,
        """
        select count(*) from trace_edges
        where edge_label='influenced_by'
        """,
    )
    qualified_spc_missing_active = scalar(
        conn,
        """
        select count(*) from capture_records
        where capture_batch='spc_pacific_v2'
          and quality_route='qualified_trace_object'
          and active_surface_id is null
        """,
    )
    filename_titles = scalar(
        conn,
        """
        select count(*) from objects
        where lower(title) glob '*.jpg'
           or lower(title) glob '*.jpeg'
           or lower(title) glob '*.png'
           or lower(title) glob '*.webp'
           or lower(title) glob '*.tif'
           or lower(title) glob '*.tiff'
        """,
    )
    active_without_search = scalar(
        conn,
        """
        select count(*) from objects o
        where not exists (
          select 1 from search_documents d
          where d.active_object=1
            and d.object_or_capture_id=o.surface_id
        )
        """,
    )
    authority_review_missing_search = scalar(
        conn,
        """
        select count(*) from authority_review_objects_v9 r
        where not exists (
          select 1 from search_documents d
          where d.search_doc_id='authority_review:' || r.surface_id
            and d.active_object=0
            and d.authority_state='uncertain'
        )
        """,
    )
    coverage_pct = (
        metrics["trace_accepted_objects"]
        / metrics["active_objects"]
        * 100
    )
    rows = [
        {
            "gate": "sqlite_integrity",
            "value": integrity,
            "status": "PASS" if integrity == "ok" else "HOLD",
            "requirement": "ok",
            "note": "SQLite pages and indexes are internally consistent.",
        },
        {
            "gate": "active_object_count",
            "value": metrics["active_objects"],
            "status": (
                "PASS"
                if metrics["active_objects"] == expected_active
                else "HOLD"
            ),
            "requirement": str(expected_active),
            "note": "Search count layer matches candidate v9.",
        },
        {
            "gate": "authority_uncertain_active_leak",
            "value": metrics["authority_uncertain_active"],
            "status": (
                "PASS"
                if metrics["authority_uncertain_active"] == 0
                else "HOLD"
            ),
            "requirement": "0",
            "note": "Uncertain authority remains outside the active total.",
        },
        {
            "gate": "authority_uncertain_review_objects",
            "value": metrics["authority_review_objects"],
            "status": (
                "PASS"
                if metrics["authority_review_objects"] == 4425
                else "HOLD"
            ),
            "requirement": "4425",
            "note": (
                "Previously isolated authority-uncertain objects remain "
                "available only through review search."
            ),
        },
        {
            "gate": "authority_uncertain_missing_search",
            "value": authority_review_missing_search,
            "status": (
                "PASS" if authority_review_missing_search == 0 else "HOLD"
            ),
            "requirement": "0",
            "note": "Every isolated authority object has a review document.",
        },
        {
            "gate": "trace_coverage_pct",
            "value": f"{coverage_pct:.2f}",
            "status": "PASS" if coverage_pct >= 90 else "HOLD",
            "requirement": ">=90.00",
            "note": "Accepted source-verified and metadata-supported TRACE.",
        },
        {
            "gate": "accepted_trace_contract_incomplete",
            "value": accepted_incomplete,
            "status": "PASS" if accepted_incomplete == 0 else "HOLD",
            "requirement": "0",
            "note": "Accepted TRACE requires node, edges, and return URL.",
        },
        {
            "gate": "accepted_trace_without_indexed_edges",
            "value": accepted_without_links,
            "status": "PASS" if accepted_without_links == 0 else "HOLD",
            "requirement": "0",
            "note": "Every accepted TRACE object reaches indexed edges.",
        },
        {
            "gate": "metadata_supported_unresolved_geography",
            "value": supported_unresolved,
            "status": "PASS" if supported_unresolved == 0 else "HOLD",
            "requirement": "0",
            "note": "Metadata-supported TRACE cannot replace missing geography.",
        },
        {
            "gate": "metadata_supported_core_edge_incomplete",
            "value": supported_core_incomplete,
            "status": (
                "PASS" if supported_core_incomplete == 0 else "HOLD"
            ),
            "requirement": "0",
            "note": "Metadata-supported objects require at least three core edges.",
        },
        {
            "gate": "influence_edges",
            "value": influence_edges,
            "status": "PASS" if influence_edges == 0 else "HOLD",
            "requirement": "0",
            "note": "Influence is never generated from association.",
        },
        {
            "gate": "qualified_spc_not_active",
            "value": qualified_spc_missing_active,
            "status": (
                "PASS" if qualified_spc_missing_active == 0 else "HOLD"
            ),
            "requirement": "0",
            "note": "All verified qualified SPC objects join candidate v9.",
        },
        {
            "gate": "filename_extension_titles",
            "value": filename_titles,
            "status": "PASS" if filename_titles == 0 else "HOLD",
            "requirement": "0",
            "note": "Display titles do not expose image filename suffixes.",
        },
        {
            "gate": "active_objects_without_search_document",
            "value": active_without_search,
            "status": "PASS" if active_without_search == 0 else "HOLD",
            "requirement": "0",
            "note": "Every active object is present in the preprocessed search.",
        },
        {
            "gate": "review_documents_searchable",
            "value": metrics["review_documents"],
            "status": (
                "PASS" if metrics["review_documents"] > 0 else "REVIEW"
            ),
            "requirement": ">0",
            "note": "Held context is searchable but count-isolated.",
        },
    ]
    return rows, metrics


def run_query_benchmark(
    conn: sqlite3.Connection, iterations: int = 100
) -> list[dict[str, Any]]:
    queries = [
        "poster",
        '"graphic design"',
        "Indonesia",
        "Pacific",
        "Vanuatu",
        "Kiribati",
        "creator",
        "material",
        "TRACE",
        "source_verified",
    ]
    rows: list[dict[str, Any]] = []
    for query in queries:
        timings: list[float] = []
        result_count = 0
        for _ in range(iterations):
            started = time.perf_counter()
            result_count = int(
                conn.execute(
                    """
                    select count(*) from search_documents_fts
                    where search_documents_fts match ?
                    """,
                    (query,),
                ).fetchone()[0]
            )
            timings.append((time.perf_counter() - started) * 1000)
        timings.sort()
        rows.append(
            {
                "query": query,
                "iterations": iterations,
                "result_count": result_count,
                "min_ms": f"{timings[0]:.3f}",
                "median_ms": f"{median(timings):.3f}",
                "p95_ms": f"{timings[int(iterations * 0.95) - 1]:.3f}",
                "max_ms": f"{timings[-1]:.3f}",
            }
        )
    return rows


def main() -> None:
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    expected_active = len(payload.get("surfaces") or [])

    base.INPUT = INPUT
    base.OUTPUT = OUTPUT
    base.GATE = BASE_GATE
    base.REPORT = REPORT
    base.CAPTURE_BATCHES = CAPTURE_BATCHES
    base.main()

    conn = sqlite3.connect(OUTPUT)
    try:
        synchronize_candidate(conn, payload)
        conn.commit()
        conn.execute("pragma optimize")
        conn.commit()
        gate_rows, metrics = gates(conn, expected_active)
        benchmark_rows = run_query_benchmark(conn)
    finally:
        conn.close()

    write_csv(GATE, GATE_FIELDS, gate_rows)
    write_csv(BENCHMARK, BENCHMARK_FIELDS, benchmark_rows)
    p95_max = max(float(row["p95_ms"]) for row in benchmark_rows)
    report = [
        "# Prefreeze candidate v9 synchronized search and TRACE",
        "",
        "Local prefreeze validation artifact; not the production database.",
        "",
        "## Layer counts",
        "",
    ]
    report.extend(f"- {key}: {value:,}" for key, value in metrics.items())
    report.extend(
        [
            "",
            "## Search benchmark",
            "",
            f"- Queries: {len(benchmark_rows)}",
            f"- Iterations per query: {benchmark_rows[0]['iterations']}",
            f"- Worst p95: {p95_max:.3f} ms",
            "",
            "## Gates",
            "",
        ]
    )
    report.extend(
        f"- {row['gate']}: {row['value']} — {row['status']}"
        for row in gate_rows
    )
    report.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Active objects and held capture context share one preprocessed FTS index but remain count-separated.",
            "- The 4,425 authority-uncertain objects are restored to review search and remain excluded from active totals.",
            "- TRACE tiers, core edges, auxiliary edges, and evidence-return URLs are stored with each active object.",
            "- High-probability association supports discovery; zero influence edges are generated.",
            "- Regional authority, object geography, and country self-authority remain separate.",
            "- PostgreSQL migration, transaction ingestion, backup/restore, and API load testing remain production work.",
            "",
        ]
    )
    REPORT.write_text("\n".join(report), encoding="utf-8")
    print(f"active_objects={metrics['active_objects']}")
    print(f"review_documents={metrics['review_documents']}")
    print(f"trace_accepted={metrics['trace_accepted_objects']}")
    print(f"metadata_supported={metrics['metadata_supported_objects']}")
    print(f"trace_nodes={metrics['trace_nodes']}")
    print(f"trace_edges={metrics['trace_edges']}")
    print(f"object_trace_edges={metrics['object_trace_edges']}")
    print(f"search_documents={metrics['search_documents']}")
    print(f"worst_p95_ms={p95_max:.3f}")
    print(
        "gate_holds="
        + str(sum(row["status"] == "HOLD" for row in gate_rows))
    )


if __name__ == "__main__":
    main()
