# Prefreeze Candidate Payload Build v1

Scope: sandbox candidate build for source and gate evaluation. It does not overwrite the official public payload or frontend data.

## Summary

- candidate_payload: generated/public_surfaces_prefreeze_candidate_v1.json (Local evaluation payload path.)
- input_files: 44 (All capture record CSV inputs discovered.)
- raw_input_rows: 19886 (Rows before P0 exclusion and dedupe.)
- skipped_by_p0_exclusion: 3554 (Rows blocked by pre-freeze cleaning gate.)
- rows_after_exclusion: 16332 (Rows eligible for global dedupe.)
- geo_overrides_applied: 4808 (Audited pre-freeze geography repairs applied in memory.)
- role_overrides_applied: 2245 (Audited pre-freeze card/subsheet demotions applied in memory.)
- deduped_candidate_rows: 16289 (Rows passed to payload builder.)
- dedupe_removed_rows: 43 (Duplicate rows removed before surface build.)
- candidate_surfaces: 16175 (Surfaces generated in candidate payload.)
- candidate_active_public_sources: 14997 (Distinct source names in candidate payload.)
- candidate_research_dossiers: 16175 (Generated research dossier anchors.)
- candidate_image_state:IMG00: 41 (Candidate surface image state distribution.)
- candidate_image_state:IMG01: 19 (Candidate surface image state distribution.)
- candidate_image_state:IMG02: 569 (Candidate surface image state distribution.)
- candidate_image_state:IMG03: 15406 (Candidate surface image state distribution.)
- candidate_image_state:IMG04: 140 (Candidate surface image state distribution.)

## Largest Included Capture Inputs

- capture_batch_commons_open_authority_weighted_expansion_2026_v1_records.csv: 4620
- capture_batch_commons_open_release_gate_expansion_2026_records.csv: 3838
- capture_batch_commons_open_category_tree_image_2026_v1_records.csv: 3176
- capture_batch_commons_open_global_south_image_2026_records.csv: 1274
- capture_batch_commons_open_controlled_expansion_2026_v1_records.csv: 818
- capture_batch_commons_open_region_balance_image_2026_v2_records.csv: 629
- capture_batch_commons_open_region_balance_image_2026_v3_records.csv: 342
- capture_batch_gallica_secondary_image_ready_1830_1970_records.csv: 121
- capture_batch_gallica_image_ready_1830_1970_records.csv: 120
- capture_batch_commons_open_contemporary_region_research_2026_records.csv: 116
- capture_batch_late_period_coverage_1970_2026_records.csv: 102
- capture_batch_wikimedia_commons_image_ready_1830_1970_records.csv: 97
- capture_batch_digitalnz_postwar_image_ready_1945_2026_records.csv: 94
- capture_batch_midcentury_1930_1970_records.csv: 92
- capture_batch_commons_open_period_balance_image_2026_records.csv: 87
- capture_batch_digitalnz_image_ready_1830_1970_records.csv: 80
- capture_batch_early_region_1830_1930_records.csv: 77
- capture_batch_image_ready_1931_1970_records.csv: 74
- capture_batch_midcentury_expansion_1931_1970_records.csv: 66
- capture_batch_edge_source_registry_context_1931_2026_records.csv: 61

## Safety

- No image files were downloaded.
- IMG01/IMG03 were not upgraded by heuristic, LLM, TOS, or platform signals.
- Impact/source priority remains an internal triage signal only.
