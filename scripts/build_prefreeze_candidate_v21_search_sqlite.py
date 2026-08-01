#!/usr/bin/env python3
"""Build synchronized v21 preprocessed search and accepted TRACE index."""

from __future__ import annotations

import csv
import os
import sqlite3
from pathlib import Path

import build_prefreeze_candidate_v9_search_sqlite as v9


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"
VERSION = os.environ.get("PREFREEZE_CANDIDATE_VERSION", "v21").strip()


def relabel_csv(path: Path) -> None:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    if not rows:
        return
    for row in rows:
        for key, value in row.items():
            row[key] = (value or "").replace(
                "candidate v9", f"candidate {VERSION}"
            )
    v9.write_csv(path, list(rows[0]), rows)


def finalize_database(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            drop view if exists active_objects_current;
            create view active_objects_current as select * from active_objects_v9;
            drop view if exists trace_accepted_objects_current;
            create view trace_accepted_objects_current as
              select * from trace_accepted_objects_v9;
            drop view if exists metadata_supported_objects_current;
            create view metadata_supported_objects_current as
              select * from metadata_supported_objects_v9;
            drop view if exists searchable_review_documents_current;
            create view searchable_review_documents_current as
              select * from searchable_review_documents_v9;
            drop view if exists authority_review_objects_current;
            create view authority_review_objects_current as
              select * from authority_review_objects_v9;
            """
        )
        conn.execute(
            "update schema_meta set value=? where key='schema_version'",
            (f"prefreeze_candidate_{VERSION}_sqlite_v1",),
        )
        conn.execute(
            "update schema_meta set value=? where key='candidate_status'",
            (f"prefreeze_candidate_{VERSION}",),
        )
        for stem in (
            "active_objects",
            "trace_accepted_objects",
            "metadata_supported_objects",
            "searchable_review_documents",
            "authority_review_objects",
        ):
            conn.execute(f"drop view if exists {stem}_{VERSION}")
            conn.execute(
                f"create view {stem}_{VERSION} as "
                f"select * from {stem}_current"
            )
        conn.commit()
    finally:
        conn.close()


def batch(name: str, stem: str) -> dict[str, Path | str]:
    return {
        "batch": name,
        "records": DATA / f"{stem}_records.csv",
        "quality": DATA / f"{stem}_quality.csv",
        "nodes": DATA / f"{stem}_trace_nodes.csv",
        "edges": DATA / f"{stem}_trace_edges.csv",
    }


def main() -> None:
    v9.INPUT = (
        ROOT
        / "generated"
        / f"public_surfaces_prefreeze_candidate_{VERSION}.json"
    )
    v9.OUTPUT = DATA / f"prefreeze_candidate_{VERSION}.sqlite"
    v9.BASE_GATE = (
        DATA / f"prefreeze_candidate_{VERSION}_base_database_gate.csv"
    )
    v9.GATE = DATA / f"prefreeze_candidate_{VERSION}_search_gate.csv"
    v9.BENCHMARK = (
        DATA / f"prefreeze_candidate_{VERSION}_search_benchmark.csv"
    )
    v9.REPORT = DOCS / f"PREFREEZE_CANDIDATE_{VERSION}_SEARCH_TRACE.md"
    v9.CAPTURE_BATCHES = v9.CAPTURE_BATCHES + (
        batch(
            "vam_sparse_year_v2",
            "capture_batch_trace_first_vam_sparse_year_2026_v2",
        ),
        batch(
            "vam_sparse_year_v3",
            "capture_batch_trace_first_vam_sparse_year_2026_v3",
        ),
        batch(
            "commons_sparse_geo_year_v2",
            "capture_batch_trace_first_sparse_geo_year_2026_v2",
        ),
        batch(
            "aic_modern_api_growth_v1",
            "capture_batch_trace_first_modern_api_growth_2026_v1",
        ),
        batch(
            "vam_modern_year_filtered_v1",
            "capture_batch_trace_first_vam_modern_growth_2026_v1",
        ),
        batch(
            "mda_object_growth_v1",
            "capture_batch_trace_first_mda_growth_2026_v1",
        ),
        batch(
            "spc_pacific_brochures_v1",
            "capture_batch_trace_first_spc_brochures_2026_v1",
        ),
        batch(
            "spc_policy_briefs_v1",
            "capture_batch_trace_first_spc_policy_briefs_2026_v1",
        ),
        batch(
            "spc_manuals_v1",
            "capture_batch_trace_first_spc_manuals_2026_v1",
        ),
        batch(
            "chile_larrea_v1",
            "capture_batch_trace_first_chile_larrea_2026_v1",
        ),
        batch(
            "chile_daniel_gleiser_v2",
            "capture_batch_trace_first_chile_daniel_gleiser_2026_v2",
        ),
        batch(
            "chile_carlos_sagredo_v2",
            "capture_batch_trace_first_chile_carlos_sagredo_2026_v2",
        ),
        batch(
            "historical_design_aic_v1",
            "capture_batch_trace_first_historical_design_aic_2026_v1",
        ),
        batch(
            "contemporary_studio_aic_v1",
            "capture_batch_trace_first_contemporary_studio_aic_2026_v1",
        ),
        batch(
            "contemporary_cooperhewitt_v1",
            "capture_batch_trace_first_contemporary_cooperhewitt_2026_v1",
        ),
        batch(
            "yale_contemporary_posters_v1",
            "capture_batch_trace_first_yale_contemporary_posters_2026_v1",
        ),
        batch(
            "yale_contemporary_design_objects_v2",
            "capture_batch_trace_first_yale_contemporary_design_2026_v2",
        ),
        batch(
            "national_library_norway_posters_v1",
            "capture_batch_trace_first_national_library_norway_posters_2026_v1",
        ),
        batch(
            "national_library_norway_posters_v2_pages_31_51",
            "capture_batch_trace_first_national_library_norway_posters_2026_v2",
        ),
        batch(
            "digital_commonwealth_original_missing_years_v1",
            "capture_batch_trace_first_digital_commonwealth_missing_years_2026_v1",
        ),
        batch(
            "loc_original_missing_years_v1",
            "capture_batch_trace_first_loc_missing_years_2026_v1",
        ),
        batch(
            "gallica_original_remaining_years_v1",
            "capture_batch_trace_first_gallica_remaining_years_2026_v1",
        ),
        batch(
            "contemporary_aic_growth_v2",
            "capture_batch_trace_first_contemporary_aic_growth_2026_v2",
        ),
        batch(
            "yale_contemporary_product_design_v3",
            "capture_batch_trace_first_yale_contemporary_product_design_2026_v3",
        ),
        batch(
            "digitaltmuseum_nk_posters_review_v1",
            "capture_batch_trace_first_digitaltmuseum_nk_posters_2026_v1",
        ),
        batch(
            "met_contemporary_design_review_v1",
            "capture_batch_trace_first_met_contemporary_design_2026_v1",
        ),
        batch(
            "moma_contemporary_design_review_v1",
            "capture_batch_moma_contemporary_design_review_2026_v1",
        ),
    )
    v9.EXTRA_TRACE_FILES = v9.EXTRA_TRACE_FILES + (
        (
            DATA
            / "capture_batch_trace_enrich_loc_legacy_2026_v2_trace_nodes.csv",
            DATA
            / "capture_batch_trace_enrich_loc_legacy_2026_v2_trace_edges.csv",
        ),
        (
            DATA / "prefreeze_candidate_v13_geo_trace_nodes.csv",
            DATA / "prefreeze_candidate_v13_geo_trace_edges.csv",
        ),
        (
            DATA
            / "prefreeze_candidate_v15_contemporary_cleanup_trace_nodes.csv",
            DATA
            / "prefreeze_candidate_v15_contemporary_cleanup_trace_edges.csv",
        ),
        (
            DATA / "prefreeze_candidate_v16_trace_growth_source_nodes.csv",
            DATA / "prefreeze_candidate_v16_trace_growth_source_edges.csv",
        ),
        (
            DATA / "prefreeze_candidate_v17_geo_trace_nodes.csv",
            DATA / "prefreeze_candidate_v17_geo_trace_edges.csv",
        ),
        (
            DATA / "prefreeze_candidate_v18_p0_trace_nodes.csv",
            DATA / "prefreeze_candidate_v18_p0_trace_edges.csv",
        ),
        (
            DATA / "prefreeze_candidate_v19_trace_nodes.csv",
            DATA / "prefreeze_candidate_v19_trace_edges.csv",
        ),
        (
            DATA / "prefreeze_candidate_v22_marginal_trace_nodes.csv",
            DATA / "prefreeze_candidate_v22_marginal_trace_edges.csv",
        ),
        (
            DATA / "prefreeze_candidate_v25_gallica_trace_nodes.csv",
            DATA / "prefreeze_candidate_v25_gallica_trace_edges.csv",
        ),
        (
            DATA / "prefreeze_candidate_v26_wellcome_trace_nodes.csv",
            DATA / "prefreeze_candidate_v26_wellcome_trace_edges.csv",
        ),
        (
            DATA / "prefreeze_candidate_v36_wellcome_trace_nodes.csv",
            DATA / "prefreeze_candidate_v36_wellcome_trace_edges.csv",
        ),
        (
            DATA / "prefreeze_candidate_v37_source_root_nodes.csv",
            DATA / "prefreeze_candidate_v37_source_root_edges.csv",
        ),
        (
            DATA / "prefreeze_candidate_v40_gallica_1810_trace_nodes.csv",
            DATA / "prefreeze_candidate_v40_gallica_1810_trace_edges.csv",
        ),
        (
            DATA / "prefreeze_candidate_v42_loc_direct_reattach_trace_nodes.csv",
            DATA / "prefreeze_candidate_v42_loc_direct_reattach_trace_edges.csv",
        ),
        (
            DATA / "prefreeze_candidate_v43_loc_verified_batch_trace_nodes.csv",
            DATA / "prefreeze_candidate_v43_loc_verified_batch_trace_edges.csv",
        ),
        (
            DATA / "capture_batch_trace_first_gallica_1804_1817_2026_v1_trace_nodes.csv",
            DATA / "capture_batch_trace_first_gallica_1804_1817_2026_v1_trace_edges.csv",
        ),
        (
            DATA / "prefreeze_candidate_v46_loc_duplicate_resolution_trace_nodes.csv",
            DATA / "prefreeze_candidate_v46_loc_duplicate_resolution_trace_edges.csv",
        ),
    )
    phase = os.environ.get("PREFREEZE_SEARCH_PHASE", "").strip().casefold()
    if phase == "configure":
        return
    if phase == "base":
        v9.base.INPUT = v9.INPUT
        v9.base.OUTPUT = v9.OUTPUT
        v9.base.GATE = v9.BASE_GATE
        v9.base.REPORT = v9.REPORT
        v9.base.CAPTURE_BATCHES = v9.CAPTURE_BATCHES
        v9.base.main()
        return
    v9.main()
    finalize_database(v9.OUTPUT)
    relabel_csv(v9.GATE)
    report = v9.REPORT.read_text(encoding="utf-8")
    report = report.replace(
        "Prefreeze candidate v9 synchronized search and TRACE",
        f"Prefreeze candidate {VERSION} synchronized search and TRACE",
    ).replace("candidate v9", f"candidate {VERSION}")
    report += (
        f"\n## {VERSION} additions\n\n"
        "- Strict Chile Oficina Larrea and Pacific policy/manual objects are "
        "synchronized with the active object index.\n"
        "- Daniel Gleiser single-poster records are synchronized when present "
        "in the selected candidate; Carlos Sagredo groups stay count-isolated.\n"
        "- v18 geography/TRACE repairs and v19 TRACE repairs are included in "
        "the evidence graph without changing their decision boundaries.\n"
        "- v22 marginal provenance and contextual branches are searchable, "
        "but remain auxiliary and do not promote unlinked objects.\n"
        "- v25 Gallica publisher-place repairs use explicit official OAI "
        "dc:publisher evidence; uncertain and provider-derived geography "
        "remains unresolved.\n"
        "- v26 Wellcome TRACE repairs use official production.places; title "
        "and subject geography cannot override production evidence.\n"
        "- AIC historical and contemporary design, Cooper Hewitt contemporary "
        "objects, Yale contemporary posters, and Yale contemporary design "
        "objects are synchronized with the active object and TRACE indexes.\n"
        "- National Library of Norway poster records are synchronized only when "
        "the record itself supplies exact year, explicit object geography, "
        "poster carrier, image route, and accepted TRACE.\n"
        "- Digital Commonwealth missing-year repairs cite the original Boston "
        "Public Library record and IIIF manifest; Wikimedia remains only a "
        "discovery lead and is not used as the descriptive source.\n"
        "- Met contemporary search candidates remain count-isolated because "
        "none passed exact-year, object-country, and carrier gates together; "
        "their audit is preserved outside active search.\n"
        "- MoMA contemporary design review objects remain count-isolated "
        "because object geography is undocumented, but their metadata is "
        "available in the review search layer.\n"
        "- Wikimedia Commons is retained as record or image host where needed; "
        "descriptive authority follows the role-separated source provenance "
        "stored on the candidate object.\n"
        "- Provider, collection, item record, object, place, type, and year "
        "remain distinct queryable nodes.\n"
        "- Held Chile records with broad years remain outside active search; "
        "they stay available only in capture audit CSVs.\n"
        "- Unlinked records stay explicitly marked and no influence edge is "
        "generated.\n"
    )
    v9.REPORT.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
