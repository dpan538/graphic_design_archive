from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB = ROOT / "db"

SEED_SQL = DB / "010_seed_data.sql"


TABLES = [
    ("historical_nodes", DATA / "historical_nodes.csv"),
    ("movements", DATA / "movements.csv"),
    ("media_technologies", DATA / "media_technologies.csv"),
    ("sources", DATA / "source_registry.csv"),
    ("search_vocabulary", DATA / "search_vocabulary.csv"),
    ("rights_strategies", DATA / "rights_strategy.csv"),
    ("regions", DATA / "regions.csv"),
    ("coverage_matrix", DATA / "coverage_matrix.csv"),
    ("regional_source_priorities", DATA / "regional_source_priorities.csv"),
    ("classification_axes", DATA / "classification_axes.csv"),
    ("geographies", DATA / "geographies.csv"),
    ("regional_movements", DATA / "regional_movements.csv"),
    ("regional_event_nodes", DATA / "regional_event_nodes.csv"),
    ("experimental_ingest_candidates", DATA / "experimental_ingest_shortlist.csv"),
    ("first_ingest_record_targets", DATA / "first_ingest_record_targets.csv"),
    ("first_ingest_target_verifications", DATA / "first_ingest_target_verifications.csv"),
    ("fallback_source_stubs", DATA / "fallback_source_stubs.csv"),
    ("source_redundancy_candidates", DATA / "source_redundancy_candidates.csv"),
    ("source_redundancy_triage", DATA / "source_redundancy_triage.csv"),
    ("recommended_six_target_ingest_sets", DATA / "recommended_six_target_ingest_sets.csv"),
    ("fallback_remediation_recommendations", DATA / "fallback_remediation_recommendations.csv"),
    ("fallback_remediation_projection", DATA / "fallback_remediation_projection.csv"),
    ("global_source_expansion_candidates", DATA / "global_source_expansion_candidates.csv"),
    ("first_production_low_friction_sources", DATA / "first_production_low_friction_sources.csv"),
    ("high_value_fragile_sources", DATA / "high_value_fragile_sources.csv"),
    ("remediation_source_verifications", DATA / "remediation_source_verifications.csv"),
    ("capture_batch_records", DATA / "capture_batch_001_records.csv"),
    ("capture_batch_cell_assignments", DATA / "capture_batch_001_cell_assignments.csv"),
    ("capture_batch_cell_summary", DATA / "capture_batch_001_cell_summary.csv"),
    ("capture_batch_next_generation_queue", DATA / "capture_batch_001_next_generation_queue.csv"),
]

PRIMARY_KEYS = {
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

INT_COLUMNS = {
    "date_start",
    "date_end",
    "event_date_start",
    "event_date_end",
    "target_record_count",
    "target_number",
    "ingest_order",
    "assigned_count",
    "img00_count",
    "img01_count",
    "img02_count",
    "img03_count",
    "img04_count",
    "minimum_next_capture_count",
}

DATE_COLUMNS = {
    "last_verified_date",
    "verified_at",
}

BOOLEAN_COLUMNS = {
    "preferred_for_query",
    "record_level_rights_required",
    "api_key_required",
    "protocol_sensitive",
    "manual_review_required",
    "source_record_required",
    "web_archive_relevant",
    "manual_rights_review_required",
    "source_terms_review_required",
    "local_copy_permitted",
    "fallback_required",
    "rights_review_required",
}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def sql_value(column: str, value: str) -> str:
    value = value.strip()
    if value == "":
        return "null"
    if column in INT_COLUMNS:
        return value if value.lstrip("-").isdigit() else "null"
    if column in DATE_COLUMNS:
        return sql_string(value)
    if column in BOOLEAN_COLUMNS:
        return "true" if value.lower() in {"yes", "true", "1"} else "false"
    return sql_string(value)


def body_from_row(row: dict[str, str], title_col: str) -> str:
    parts = []
    for key, value in row.items():
        if key == title_col or value == "":
            continue
        parts.append(f"{key}: {value}")
    return "\n".join(parts)


def facets_for(table: str, row: dict[str, str]) -> dict[str, str]:
    return {
        "seedTable": table,
        "priority": row.get("priority", ""),
        "rightsRiskLevel": row.get("rights_risk_level", ""),
        "sourceConfidence": row.get("source_confidence", ""),
        "termClass": row.get("term_class", ""),
        "groupType": row.get("group_type", ""),
        "geoType": row.get("geo_type", ""),
        "formationType": row.get("formation_type", ""),
        "eventType": row.get("event_type", ""),
        "imageZone": row.get("expected_image_zone", row.get("default_image_zone", row.get("image_presence_code", ""))),
        "recordPolicy": row.get("expected_record_policy", row.get("default_record_policy", "")),
        "displayPolicy": row.get("expected_display_policy", row.get("default_display_policy", "")),
        "dateStart": row.get("date_start", ""),
        "dateEnd": row.get("date_end", ""),
    }


def insert_statement(table: str, columns: list[str], row: dict[str, str]) -> str:
    quoted_cols = ", ".join(f'"{col}"' for col in columns)
    values = ", ".join(sql_value(col, row.get(col, "")) for col in columns)
    pk = PRIMARY_KEYS[table]
    updates = ", ".join(
        f'"{col}" = excluded."{col}"' for col in columns if col != pk
    )
    return (
        f'insert into {table} ({quoted_cols}) values ({values}) '
        f'on conflict ("{pk}") do update set {updates};'
    )


def search_doc_statement(table: str, row: dict[str, str]) -> str:
    pk = PRIMARY_KEYS[table]
    title_col = TITLE_COLUMNS[table]
    seed_id = row[pk]
    search_doc_id = f"{table}:{seed_id}"
    title = row[title_col]
    body = body_from_row(row, title_col)
    facets = json.dumps(facets_for(table, row), ensure_ascii=False)
    return (
        "insert into searchable_documents "
        "(search_doc_id, seed_table, seed_id, document_type, title, body, facets) "
        f"values ({sql_string(search_doc_id)}, {sql_string(table)}, {sql_string(seed_id)}, "
        f"{sql_string(table)}, {sql_string(title)}, {sql_string(body)}, "
        f"{sql_string(facets)}::jsonb) "
        "on conflict (search_doc_id) do update set "
        "seed_table = excluded.seed_table, "
        "seed_id = excluded.seed_id, "
        "document_type = excluded.document_type, "
        "title = excluded.title, "
        "body = excluded.body, "
        "facets = excluded.facets, "
        "updated_at = now();"
    )


def main() -> None:
    chunks = [
        "-- Seed data generated from data/*.csv.",
        "-- Regenerate with: python scripts/generate_postgres_seed_sql.py",
        "begin;",
    ]

    for table, path in TABLES:
        columns, rows = read_csv(path)
        chunks.append(f"\n-- {table}: {len(rows)} rows")
        for row in rows:
            chunks.append(insert_statement(table, columns, row))

    chunks.append("\n-- searchable_documents seed rows")
    for table, path in TABLES:
        _columns, rows = read_csv(path)
        for row in rows:
            chunks.append(search_doc_statement(table, row))

    chunks.append("commit;")
    SEED_SQL.write_text("\n".join(chunks) + "\n", encoding="utf-8")
    print(SEED_SQL)


if __name__ == "__main__":
    main()
