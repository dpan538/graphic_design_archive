from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "db"
DATA = ROOT / "data"


REQUIRED_FILES = [
    DB / "001_initial_schema.sql",
    DB / "002_operational_skeleton.sql",
    DB / "003_read_models.sql",
    DB / "004_coverage_skeleton.sql",
    DB / "005_global_classification_skeleton.sql",
    DB / "006_publication_surface_skeleton.sql",
    DB / "007_authority_normalization_skeleton.sql",
    DB / "008_source_rights_policy_skeleton.sql",
    DB / "009_first_ingest_scope_skeleton.sql",
    DB / "011_ingest_contract_targets_skeleton.sql",
    DB / "012_deep_research_outputs_skeleton.sql",
    DB / "013_capture_batch_skeleton.sql",
    DB / "010_seed_data.sql",
    DB / "900_validation_queries.sql",
    DATA / "historical_nodes.csv",
    DATA / "movements.csv",
    DATA / "media_technologies.csv",
    DATA / "source_registry.csv",
    DATA / "search_vocabulary.csv",
    DATA / "rights_strategy.csv",
    DATA / "regions.csv",
    DATA / "coverage_matrix.csv",
    DATA / "regional_source_priorities.csv",
    DATA / "classification_axes.csv",
    DATA / "geographies.csv",
    DATA / "regional_movements.csv",
    DATA / "regional_event_nodes.csv",
    DATA / "experimental_ingest_shortlist.csv",
    DATA / "first_ingest_record_targets.csv",
    DATA / "first_ingest_target_verifications.csv",
    DATA / "fallback_source_stubs.csv",
    DATA / "source_redundancy_candidates.csv",
    DATA / "source_redundancy_triage.csv",
    DATA / "recommended_six_target_ingest_sets.csv",
    DATA / "fallback_remediation_recommendations.csv",
    DATA / "fallback_remediation_projection.csv",
    DATA / "global_source_expansion_candidates.csv",
    DATA / "first_production_low_friction_sources.csv",
    DATA / "high_value_fragile_sources.csv",
    DATA / "remediation_source_verifications.csv",
    DATA / "capture_batch_001_records.csv",
    DATA / "capture_batch_001_source_summary.csv",
    DATA / "capture_batch_001_cell_assignments.csv",
    DATA / "capture_batch_001_cell_summary.csv",
    DATA / "capture_batch_001_next_generation_queue.csv",
    DATA / "remediation_source_records_index.csv",
    DATA / "manual_source_records_index.csv",
    DATA / "archive_seed.sqlite",
]

EXPECTED_CSV_COUNTS = {
    "historical_nodes.csv": 15,
    "movements.csv": 38,
    "media_technologies.csv": 35,
    "source_registry.csv": 66,
    "search_vocabulary.csv": 200,
    "rights_strategy.csv": 10,
    "regions.csv": 15,
    "coverage_matrix.csv": 225,
    "regional_source_priorities.csv": 90,
    "classification_axes.csv": 10,
    "geographies.csv": 109,
    "regional_movements.csv": 89,
    "regional_event_nodes.csv": 63,
    "experimental_ingest_shortlist.csv": 39,
    "first_ingest_record_targets.csv": 48,
    "first_ingest_target_verifications.csv": 48,
    "fallback_source_stubs.csv": 18,
    "source_redundancy_candidates.csv": 90,
    "source_redundancy_triage.csv": 18,
    "recommended_six_target_ingest_sets.csv": 15,
    "fallback_remediation_recommendations.csv": 9,
    "fallback_remediation_projection.csv": 18,
    "global_source_expansion_candidates.csv": 84,
    "first_production_low_friction_sources.csv": 20,
    "high_value_fragile_sources.csv": 20,
    "remediation_source_verifications.csv": 10,
    "capture_batch_001_records.csv": 50,
    "capture_batch_001_source_summary.csv": 4,
    "capture_batch_001_cell_assignments.csv": 50,
    "capture_batch_001_cell_summary.csv": 22,
    "capture_batch_001_next_generation_queue.csv": 18,
    "remediation_source_records_index.csv": 8,
    "manual_source_records_index.csv": 30,
}

EXPECTED_SQLITE_COUNTS = {
    "historical_nodes": 15,
    "movements": 38,
    "media_technologies": 35,
    "sources": 66,
    "search_vocabulary": 200,
    "rights_strategies": 10,
    "regions": 15,
    "coverage_matrix": 225,
    "regional_source_priorities": 90,
    "classification_axes": 10,
    "geographies": 109,
    "regional_movements": 89,
    "regional_event_nodes": 63,
    "experimental_ingest_candidates": 39,
    "first_ingest_record_targets": 48,
    "first_ingest_target_verifications": 48,
    "fallback_source_stubs": 18,
    "source_redundancy_candidates": 90,
    "source_redundancy_triage": 18,
    "recommended_six_target_ingest_sets": 15,
    "fallback_remediation_recommendations": 9,
    "fallback_remediation_projection": 18,
    "global_source_expansion_candidates": 84,
    "first_production_low_friction_sources": 20,
    "high_value_fragile_sources": 20,
    "remediation_source_verifications": 10,
    "capture_batch_records": 50,
    "capture_batch_cell_assignments": 50,
    "capture_batch_cell_summary": 22,
    "capture_batch_next_generation_queue": 18,
    "search_docs": 1542,
}

REQUIRED_SQL_TOKENS = {
    "001_initial_schema.sql": [
        "create table if not exists entities",
        "create table if not exists source_records",
        "create table if not exists citations",
        "create table if not exists assertions",
        "create table if not exists classifications",
        "create table if not exists image_assets",
        "create table if not exists searchable_documents",
    ],
    "002_operational_skeleton.sql": [
        "create table if not exists source_terms_reviews",
        "create table if not exists rights_reviews",
        "create table if not exists ingestion_runs",
        "create table if not exists ingestion_events",
        "create table if not exists source_record_snapshots",
        "create table if not exists audit_log",
    ],
    "003_read_models.sql": [
        "create or replace view api_search_documents",
        "create or replace view api_source_registry",
        "create or replace view api_entity_detail_base",
        "create or replace view api_source_record_detail_base",
        "create or replace view api_regions",
        "create or replace view api_coverage_matrix",
        "create or replace view api_classification_axes",
        "create or replace view api_geographies",
        "create or replace view api_regional_movements",
        "create or replace view api_regional_event_nodes",
        "create or replace view api_publication_surfaces",
        "create or replace view api_publication_surface_pages",
        "create or replace view api_surface_table_rows",
        "create or replace view api_folder_views",
        "create or replace view api_folder_memberships",
        "create or replace view api_filing_registry_cards",
        "create or replace view api_filing_registry_members",
        "create or replace view api_sparse_cards",
        "create or replace view api_archive_bookmarks",
        "create or replace view api_evidence_bundles",
        "create or replace view api_evidence_bundle_items",
        "create or replace view api_external_identifier_status",
        "create or replace view api_authority_resolution_events",
        "create or replace view api_entity_appellations",
        "create or replace view api_geography_appellations",
        "create or replace view api_relation_predicate_rules",
        "create or replace view api_protocol_rights_reviews",
        "create or replace view api_source_policy_summary",
        "create or replace view api_source_terms_review_policy",
        "create or replace view api_experimental_ingest_candidates",
        "create or replace view api_source_record_relations",
        "create or replace view api_digital_representations",
        "create or replace view api_field_provenance",
        "create or replace view api_record_family_profiles",
        "create or replace view api_ingest_validation_rules",
        "create or replace view api_first_ingest_record_targets",
        "create or replace view api_first_ingest_target_verifications",
        "create or replace view api_fallback_source_stubs",
        "create or replace view api_source_redundancy_candidates",
        "create or replace view api_source_redundancy_triage",
        "create or replace view api_recommended_six_target_ingest_sets",
        "create or replace view api_fallback_remediation_recommendations",
        "create or replace view api_fallback_remediation_projection",
        "create or replace view api_global_source_expansion_candidates",
        "create or replace view api_first_production_low_friction_sources",
        "create or replace view api_high_value_fragile_sources",
        "create or replace view api_remediation_source_verifications",
        "create or replace view api_capture_batch_records",
        "create or replace view api_capture_batch_summary",
        "create or replace view api_capture_batch_cell_assignments",
        "create or replace view api_capture_batch_cell_summary",
        "create or replace view api_capture_batch_next_generation_queue",
    ],
    "004_coverage_skeleton.sql": [
        "create table if not exists regions",
        "create table if not exists coverage_matrix",
        "create table if not exists regional_source_priorities",
        "create table if not exists historical_events",
        "create table if not exists coverage_gap_notes",
    ],
    "005_global_classification_skeleton.sql": [
        "create table if not exists classification_axes",
        "create table if not exists geographies",
        "create table if not exists geography_aliases",
        "create table if not exists regional_movements",
        "create table if not exists regional_event_nodes",
        "create table if not exists normalized_dates",
        "create table if not exists entity_geographies",
        "create table if not exists source_record_geographies",
    ],
    "006_publication_surface_skeleton.sql": [
        "create type publication_surface_type",
        "create type sheet_tier",
        "create type image_zone_code",
        "create type surface_table_kind",
        "create type folder_view_type",
        "create table if not exists display_templates",
        "create table if not exists publication_surfaces",
        "create table if not exists publication_surface_pages",
        "create table if not exists surface_table_rows",
        "create table if not exists folder_views",
        "create table if not exists folder_memberships",
        "create table if not exists filing_registry_cards",
        "create table if not exists filing_registry_members",
        "create table if not exists sparse_cards",
        "create table if not exists archive_bookmarks",
    ],
    "007_authority_normalization_skeleton.sql": [
        "create type authority_match_status",
        "create type appellation_type",
        "create type mapping_relation",
        "create type evidence_mode",
        "create table if not exists evidence_bundles",
        "create table if not exists evidence_bundle_items",
        "create table if not exists authority_resolution_events",
        "create table if not exists entity_appellations",
        "create table if not exists geography_appellations",
        "alter table external_identifiers",
        "alter table relation_predicates",
        "alter table rights_reviews",
    ],
    "008_source_rights_policy_skeleton.sql": [
        "create type source_record_policy",
        "create type public_display_policy",
        "create type asset_origin",
        "create type terms_review_decision",
        "alter table sources",
        "alter table source_terms_reviews",
        "alter table rights_reviews",
        "alter table image_assets",
        "alter table ingestion_runs",
        "create table if not exists experimental_ingest_candidates",
    ],
    "009_first_ingest_scope_skeleton.sql": [
        "alter table regional_movements",
        "alter table regional_event_nodes",
        "alter table sources",
        "alter table search_vocabulary",
        "alter table experimental_ingest_candidates",
        "alter table source_records",
        "alter table rights_reviews",
        "alter table classifications",
    ],
    "011_ingest_contract_targets_skeleton.sql": [
        "create type digital_representation_type",
        "create type target_record_status",
        "create table if not exists source_record_relations",
        "create table if not exists digital_representations",
        "create table if not exists field_provenance",
        "create table if not exists record_family_profiles",
        "create table if not exists ingest_validation_rules",
        "create table if not exists first_ingest_record_targets",
        "create table if not exists first_ingest_target_verifications",
        "create table if not exists fallback_source_stubs",
    ],
    "012_deep_research_outputs_skeleton.sql": [
        "create table if not exists source_redundancy_candidates",
        "create table if not exists source_redundancy_triage",
        "create table if not exists recommended_six_target_ingest_sets",
        "create table if not exists fallback_remediation_recommendations",
        "create table if not exists fallback_remediation_projection",
        "create table if not exists global_source_expansion_candidates",
        "create table if not exists first_production_low_friction_sources",
        "create table if not exists high_value_fragile_sources",
        "create table if not exists remediation_source_verifications",
    ],
    "013_capture_batch_skeleton.sql": [
        "create table if not exists capture_batch_records",
        "create index if not exists capture_batch_records_source_idx",
        "create index if not exists capture_batch_records_direction_idx",
        "create table if not exists capture_batch_cell_assignments",
        "create table if not exists capture_batch_cell_summary",
        "create table if not exists capture_batch_next_generation_queue",
    ],
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def check_files() -> None:
    for path in REQUIRED_FILES:
        if not path.exists():
            fail(f"missing required file: {path.relative_to(ROOT)}")
    print("files: ok")


def check_csv_counts() -> None:
    for filename, expected in EXPECTED_CSV_COUNTS.items():
        path = DATA / filename
        with path.open(encoding="utf-8", newline="") as f:
            count = sum(1 for _ in csv.DictReader(f))
        if count != expected:
            fail(f"{filename} expected {expected} rows, got {count}")
    print("csv counts: ok")


def check_sqlite_counts() -> None:
    conn = sqlite3.connect(DATA / "archive_seed.sqlite")
    try:
        for table, expected in EXPECTED_SQLITE_COUNTS.items():
            count = conn.execute(f"select count(*) from {table}").fetchone()[0]
            if count != expected:
                fail(f"sqlite table {table} expected {expected} rows, got {count}")
    finally:
        conn.close()
    print("sqlite snapshot: ok")


def check_sql_tokens() -> None:
    for filename, tokens in REQUIRED_SQL_TOKENS.items():
        text = (DB / filename).read_text(encoding="utf-8").lower()
        for token in tokens:
            if token.lower() not in text:
                fail(f"{filename} missing token: {token}")
    print("sql skeleton tokens: ok")


def check_seed_sql() -> None:
    text = (DB / "010_seed_data.sql").read_text(encoding="utf-8")
    if text.count("insert into searchable_documents") != EXPECTED_SQLITE_COUNTS["search_docs"]:
        fail(
            "seed SQL does not contain "
            f"{EXPECTED_SQLITE_COUNTS['search_docs']} searchable_documents inserts"
        )
    for table in [
        "historical_nodes",
        "movements",
        "media_technologies",
        "sources",
        "search_vocabulary",
        "rights_strategies",
        "regions",
        "coverage_matrix",
        "regional_source_priorities",
        "classification_axes",
        "geographies",
        "regional_movements",
        "regional_event_nodes",
        "experimental_ingest_candidates",
        "first_ingest_record_targets",
        "first_ingest_target_verifications",
        "fallback_source_stubs",
        "source_redundancy_candidates",
        "source_redundancy_triage",
        "recommended_six_target_ingest_sets",
        "fallback_remediation_recommendations",
        "fallback_remediation_projection",
        "global_source_expansion_candidates",
        "first_production_low_friction_sources",
        "high_value_fragile_sources",
        "remediation_source_verifications",
        "capture_batch_records",
        "capture_batch_cell_assignments",
        "capture_batch_cell_summary",
        "capture_batch_next_generation_queue",
    ]:
        if f"insert into {table}" not in text:
            fail(f"seed SQL missing inserts for {table}")
    print("seed sql: ok")


def main() -> None:
    check_files()
    check_csv_counts()
    check_sqlite_counts()
    check_sql_tokens()
    check_seed_sql()
    print("database skeleton check passed")


if __name__ == "__main__":
    main()
