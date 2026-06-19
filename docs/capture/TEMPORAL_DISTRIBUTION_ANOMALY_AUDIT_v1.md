# Temporal Distribution Anomaly Audit v1

Scope: capture records only. This audit separates object-dated records from source-profile or source-page span records.

## Summary

- Capture records scanned: 19898
- Recent anomaly review rows: 1050
- 2025 all/object/span: 230 / 230 / 0
- 2026 all/object/span: 820 / 106 / 714

## Recent Anomaly Reasons

- access_year_as_object_year: 714
- long_span_record: 714
- recent_end_year_with_old_start: 714
- source_page_image_record_not_object_year: 587
- hero_or_page_image_not_item_final: 587
- recent_2025_object_review: 215
- coverage_target_span_not_object_year: 127
- source_profile_not_item_record: 127
- recent_2026_object_review: 106
- event_or_session_photo_review: 15

## Recent Anomaly Files

- capture_batch_nonmainstream_item_image_2026_records.csv: 587
- capture_batch_commons_open_authority_weighted_expansion_2026_v1_records.csv: 144
- capture_batch_nonmainstream_source_profiles_1990_2026_records.csv: 127
- capture_batch_commons_open_category_tree_image_2026_v1_records.csv: 55
- capture_batch_commons_open_region_balance_image_2026_v2_records.csv: 45
- capture_batch_edge_wordpress_1970_2026_records.csv: 23
- capture_batch_commons_open_region_balance_image_2026_v3_records.csv: 19
- capture_batch_commons_open_global_south_image_2026_records.csv: 14
- capture_batch_edge_rss_html_1970_2026_records.csv: 8
- capture_batch_independent_asia_1990_2026_records.csv: 6
- capture_batch_commons_open_release_gate_expansion_2026_records.csv: 5
- capture_batch_nonmainstream_region_1990_2026_records.csv: 4
- capture_batch_postwar_commons_open_image_1945_2026_records.csv: 4
- capture_batch_commons_open_contemporary_region_research_2026_records.csv: 3
- capture_batch_commons_open_controlled_expansion_2026_v1_records.csv: 3
- capture_batch_late_period_coverage_1970_2026_records.csv: 2
- capture_batch_digitalnz_postwar_image_ready_1945_2026_records.csv: 1

## 5-Year Gap / Overfull Priorities

- 1945-1949: object=547, share=0.739, priority=moderate_gap
- 1955-1959: object=388, share=0.524, priority=severe_gap
- 1960-1964: object=448, share=0.605, priority=moderate_gap
- 1980-1984: object=346, share=0.467, priority=severe_gap
- 1985-1989: object=378, share=0.511, priority=severe_gap
- 1990-1994: object=468, share=0.632, priority=moderate_gap
- 1995-1999: object=500, share=0.675, priority=moderate_gap
- 2000-2004: object=372, share=0.502, priority=severe_gap
- 2020-2024: object=1140, share=1.540, priority=recent_overfull_review
- 2025-2026: object=336, share=0.454, priority=severe_gap

## Interpretation

- A high 2026 count is not automatically contemporary design coverage. In current data, much of it is access-year or coverage-span metadata from source-profile/image-page records.
- Object-year coverage should use `object_dated_records`, not `all_records`, until span/profile records are normalized or excluded from object temporal metrics.
- 1980s, 1990s, 2000-2004, and late-1950s/early-1960s bins remain priority capture targets.
