from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB_PATH = DATA / "archive_seed.sqlite"


CSV_TABLES = {
    "historical_nodes": DATA / "historical_nodes.csv",
    "movements": DATA / "movements.csv",
    "media_technologies": DATA / "media_technologies.csv",
    "sources": DATA / "source_registry.csv",
    "search_vocabulary": DATA / "search_vocabulary.csv",
    "rights_strategies": DATA / "rights_strategy.csv",
    "regions": DATA / "regions.csv",
    "coverage_matrix": DATA / "coverage_matrix.csv",
    "regional_source_priorities": DATA / "regional_source_priorities.csv",
    "classification_axes": DATA / "classification_axes.csv",
    "geographies": DATA / "geographies.csv",
    "regional_movements": DATA / "regional_movements.csv",
    "regional_event_nodes": DATA / "regional_event_nodes.csv",
    "experimental_ingest_candidates": DATA / "experimental_ingest_shortlist.csv",
    "first_ingest_record_targets": DATA / "first_ingest_record_targets.csv",
    "first_ingest_target_verifications": DATA / "first_ingest_target_verifications.csv",
    "fallback_source_stubs": DATA / "fallback_source_stubs.csv",
    "source_redundancy_candidates": DATA / "source_redundancy_candidates.csv",
    "source_redundancy_triage": DATA / "source_redundancy_triage.csv",
    "recommended_six_target_ingest_sets": DATA / "recommended_six_target_ingest_sets.csv",
    "fallback_remediation_recommendations": DATA / "fallback_remediation_recommendations.csv",
    "fallback_remediation_projection": DATA / "fallback_remediation_projection.csv",
    "global_source_expansion_candidates": DATA / "global_source_expansion_candidates.csv",
    "first_production_low_friction_sources": DATA / "first_production_low_friction_sources.csv",
    "high_value_fragile_sources": DATA / "high_value_fragile_sources.csv",
    "remediation_source_verifications": DATA / "remediation_source_verifications.csv",
    "capture_batch_records": DATA / "capture_batch_001_records.csv",
    "capture_batch_cell_assignments": DATA / "capture_batch_001_cell_assignments.csv",
    "capture_batch_cell_summary": DATA / "capture_batch_001_cell_summary.csv",
    "capture_batch_next_generation_queue": DATA / "capture_batch_001_next_generation_queue.csv",
}


ID_COLUMNS = {
    "historical_nodes": "node_id",
    "movements": "movement_id",
    "media_technologies": "media_id",
    "sources": "source_id",
    "search_vocabulary": "term_id",
    "rights_strategies": "strategy_id",
    "regions": "region_id",
    "coverage_matrix": "coverage_id",
    "regional_source_priorities": "priority_id",
    "classification_axes": "axis_id",
    "geographies": "geo_id",
    "regional_movements": "regional_movement_id",
    "regional_event_nodes": "event_node_id",
    "experimental_ingest_candidates": "experimental_candidate_id",
    "first_ingest_record_targets": "first_target_id",
    "first_ingest_target_verifications": "verification_id",
    "fallback_source_stubs": "fallback_stub_id",
    "source_redundancy_candidates": "redundancy_candidate_id",
    "source_redundancy_triage": "triage_id",
    "recommended_six_target_ingest_sets": "recommended_set_id",
    "fallback_remediation_recommendations": "remediation_id",
    "fallback_remediation_projection": "projection_id",
    "global_source_expansion_candidates": "source_expansion_id",
    "first_production_low_friction_sources": "low_friction_id",
    "high_value_fragile_sources": "fragile_source_id",
    "remediation_source_verifications": "remediation_verification_id",
    "capture_batch_records": "capture_id",
    "capture_batch_cell_assignments": "capture_id",
    "capture_batch_cell_summary": "cell_id",
    "capture_batch_next_generation_queue": "queue_id",
}


TITLE_COLUMNS = {
    "historical_nodes": "node_name",
    "movements": "name",
    "media_technologies": "term",
    "sources": "name",
    "search_vocabulary": "term",
    "rights_strategies": "source_category",
    "regions": "region_name",
    "coverage_matrix": "coverage_id",
    "regional_source_priorities": "priority_id",
    "classification_axes": "axis_name",
    "geographies": "name",
    "regional_movements": "name",
    "regional_event_nodes": "event_name",
    "experimental_ingest_candidates": "candidate_name",
    "first_ingest_record_targets": "target_label",
    "first_ingest_target_verifications": "first_target_id",
    "fallback_source_stubs": "target_label",
    "source_redundancy_candidates": "candidate_label",
    "source_redundancy_triage": "probable_failed_target",
    "recommended_six_target_ingest_sets": "scope_cell_id",
    "fallback_remediation_recommendations": "original_target_label",
    "fallback_remediation_projection": "target_label",
    "global_source_expansion_candidates": "source_name",
    "first_production_low_friction_sources": "source_name",
    "high_value_fragile_sources": "source_name",
    "remediation_source_verifications": "source_title",
    "capture_batch_records": "source_title",
    "capture_batch_cell_assignments": "source_title",
    "capture_batch_cell_summary": "cell_name",
    "capture_batch_next_generation_queue": "cell_name",
}


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def create_table(conn: sqlite3.Connection, table: str, columns: list[str], id_col: str) -> None:
    col_defs = []
    for col in columns:
        col_type = "text"
        suffix = " primary key" if col == id_col else ""
        col_defs.append(f'"{col}" {col_type}{suffix}')
    conn.execute(f'drop table if exists "{table}"')
    conn.execute(f'create table "{table}" ({", ".join(col_defs)})')


def insert_rows(conn: sqlite3.Connection, table: str, columns: list[str], rows: list[dict[str, str]]) -> None:
    placeholders = ", ".join(["?"] * len(columns))
    quoted = ", ".join(f'"{col}"' for col in columns)
    sql = f'insert into "{table}" ({quoted}) values ({placeholders})'
    conn.executemany(sql, [[row.get(col, "") for col in columns] for row in rows])


def row_body(row: dict[str, str], title_col: str) -> str:
    parts = []
    for key, value in row.items():
        if key == title_col or not value:
            continue
        parts.append(f"{key}: {value}")
    return "\n".join(parts)


def build_search(conn: sqlite3.Connection) -> None:
    conn.execute("drop table if exists search_docs")
    conn.execute(
        """
        create table search_docs (
          search_doc_id text primary key,
          seed_table text not null,
          seed_id text not null,
          document_type text not null,
          title text not null,
          body text,
          facets_json text
        )
        """
    )
    conn.execute("drop table if exists search_docs_fts")
    conn.execute(
        """
        create virtual table search_docs_fts using fts5(
          title,
          body,
          content='search_docs',
          content_rowid='rowid'
        )
        """
    )

    for table, path in CSV_TABLES.items():
        columns, rows = read_rows(path)
        id_col = ID_COLUMNS[table]
        title_col = TITLE_COLUMNS[table]
        docs = []
        for row in rows:
            seed_id = row[id_col]
            title = row[title_col]
            facets = {
                "seed_table": table,
                "priority": row.get("priority", ""),
                "rights_risk_level": row.get("rights_risk_level", ""),
                "source_confidence": row.get("source_confidence", ""),
                "term_class": row.get("term_class", ""),
                "group_type": row.get("group_type", ""),
                "geo_type": row.get("geo_type", ""),
                "formation_type": row.get("formation_type", ""),
                "event_type": row.get("event_type", ""),
                "image_zone": row.get("expected_image_zone", row.get("image_presence_code", "")),
                "record_policy": row.get("expected_record_policy", ""),
                "display_policy": row.get("expected_display_policy", ""),
            }
            docs.append(
                (
                    f"{table}:{seed_id}",
                    table,
                    seed_id,
                    table,
                    title,
                    row_body(row, title_col),
                    json.dumps(facets, ensure_ascii=False),
                )
            )
        conn.executemany(
            """
            insert into search_docs (
              search_doc_id,
              seed_table,
              seed_id,
              document_type,
              title,
              body,
              facets_json
            ) values (?, ?, ?, ?, ?, ?, ?)
            """,
            docs,
        )

    conn.execute(
        """
        insert into search_docs_fts(rowid, title, body)
        select rowid, title, body from search_docs
        """
    )


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("pragma foreign_keys = on")
        for table, path in CSV_TABLES.items():
            columns, rows = read_rows(path)
            create_table(conn, table, columns, ID_COLUMNS[table])
            insert_rows(conn, table, columns, rows)
        build_search(conn)
        conn.commit()
    finally:
        conn.close()

    print(DB_PATH)


if __name__ == "__main__":
    main()
