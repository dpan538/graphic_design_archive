# Pre-freeze Public Rebuild Exclusion v1

Scope: non-destructive P0 exclusion table for future public-surface rebuilds. It does not delete capture records, mutate rights states, download images, or rebuild frontend payloads.

## Summary

- p0_exclusion_rows: 3554 (Distinct source_file + capture_id rows excluded from future public-surface rebuilds.)
- skipped_p0_rows_without_rebuild_key: 0 (P0 queue rows without source_file or capture_id; not actionable for rebuild exclusion.)
- source_files_with_exclusions: 30 (Capture record files affected by the exclusion list.)

## Action Counts

- card_or_appendix_reclass_review: 2930
- date_or_span_reclass_review: 579
- recent_stamp_event_reclassification: 40
- duplicate_visual_variant_review: 5

## Top Source Files

- capture_batch_commons_open_category_tree_image_2026_v1_records.csv: 1361
- capture_batch_nonmainstream_item_image_2026_records.csv: 587
- capture_batch_commons_open_authority_weighted_expansion_2026_v1_records.csv: 429
- capture_batch_commons_open_release_gate_expansion_2026_records.csv: 262
- capture_batch_commons_open_region_balance_image_2026_v2_records.csv: 171
- capture_batch_commons_open_region_balance_image_2026_v3_records.csv: 155
- capture_batch_cooperhewitt_graphql_image_ready_1830_2026_records.csv: 148
- capture_batch_nonmainstream_source_profiles_1990_2026_records.csv: 127
- capture_batch_commons_open_controlled_expansion_2026_v1_records.csv: 111
- capture_batch_commons_open_global_south_image_2026_records.csv: 106
- capture_batch_digitalnz_postwar_image_ready_1945_2026_records.csv: 23
- capture_batch_commons_open_publication_category_tree_2026_v1_records.csv: 10
- capture_batch_noncanonical_exact_sources_1970_2000_records.csv: 8
- capture_batch_wikimedia_commons_image_ready_1830_1970_records.csv: 7
- capture_batch_edge_wordpress_1970_2026_records.csv: 5

## Rebuild Rule

- `scripts/rebuild_public_surfaces_from_records.py` reads this exclusion table when present.
- A matching `source_file + capture_id` row is skipped before dedupe and surface generation.
- The raw capture row remains available for audit, card/support review, or later manual reinstatement.
- Candidate duplicate-image deltas are merged only when `data/prefreeze_candidate_exclusion_delta_v1.csv` exists.
