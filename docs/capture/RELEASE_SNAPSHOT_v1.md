# Release Snapshot v1

Scope: consolidated read-only release-health snapshot. Object-level image metrics count repeated views/photos of one source object once.

## Gate Summary

- archive_active_public_sources: 7298 · pass (Distinct public-surface source names; release target=2000.)
- release_source_coverage_rate: 364.90 · pass (Minimum release source coverage=80%.)
- object_source_visible_rate: 96.68 · pass (Minimum object source-visible=96%.)
- object_verified_open_rate: 80.92 · fail (Minimum object verified-open=85%.)
- object_weighted_publication_grade_rate: 81.39 · fail (Object-level max image weight per object; repeated photos are not double-counted.)
- object_img04_rate: 2.82 · pass (Maximum object IMG04 target=10%.)
- year_2026_surface_rate: 0.51 · pass (Warning if more than 25% of public surfaces date to 2026.)
- post_2026_or_error_count: 0 · pass (Future year date sanity check.)

## Core Metrics

- public_surfaces: 8636 (Generated public surfaces.)
- archive_active_public_sources: 7298 (Distinct public-surface source names; release target=2000.)
- release_source_coverage_rate: 364.90 (Minimum release source coverage=80%.)
- surface_source_visible_rate: 96.51 (Surface-level IMG01/IMG02/IMG03.)
- surface_verified_open_rate: 80.72 (Surface-level reviewed IMG03.)
- object_count: 8615 (Object-level grouping; repeated views/photos count once.)
- object_source_visible_rate: 96.68 (Minimum object source-visible=96%.)
- object_verified_open_rate: 80.92 (Minimum object verified-open=85%.)
- object_weighted_publication_grade_rate: 81.39 (Object-level max image weight per object; repeated photos are not double-counted.)
- object_img04_rate: 2.82 (Maximum object IMG04 target=10%.)
- main_sheet_count: 8379 (publicationRole=main_sheet.)
- sub_or_support_surface_count: 257 (All surfaces not marked as main_sheet.)
- independent_text_sheet_count: 242 (templateId=sheet.text.v0.)
- dossier_text_page_count: 8622 (text_page entries inside researchDossiers pageSequence.)
- dossier_sub_card_appendix_count: 2208 (sub_sheet/card/appendix entries inside researchDossiers pageSequence.)
- year_2026_surface_rate: 0.51 (Warning if more than 25% of public surfaces date to 2026.)
- post_2026_or_error_count: 0 (Future year date sanity check.)
- undated_or_unparsed_count: 748 (Missing/unparsed public surface dates.)

## Main Sheets by Period

- 1930_1970: main=2347, surfaces=2452, IMG04=43
- 1970_2000: main=2292, surfaces=2322, IMG04=22
- 2000_2026: main=1466, surfaces=1491, IMG04=38
- pre_1930: main=1575, surfaces=1623, IMG04=10
- undated_or_unparsed: main=699, surfaces=748, IMG04=145

## Region Distribution

- Unresolved region: surfaces=3613, main=3526, visible=3524, open=3129, IMG04=81
- Mexico: surfaces=492, main=490, visible=485, open=480, IMG04=6
- Indonesia: surfaces=479, main=476, visible=475, open=471, IMG04=4
- Argentina: surfaces=425, main=423, visible=424, open=344, IMG04=1
- Brazil: surfaces=334, main=331, visible=330, open=328, IMG04=4
- France: surfaces=297, main=290, visible=294, open=264, IMG04=1
- Colombia: surfaces=291, main=291, visible=288, open=147, IMG04=3
- United States: surfaces=278, main=254, visible=261, open=136, IMG04=5
- Aotearoa New Zealand: surfaces=186, main=152, visible=182, open=73, IMG04=3
- Iran: surfaces=160, main=159, visible=159, open=154, IMG04=1
- Italy: surfaces=142, main=140, visible=140, open=140, IMG04=0
- United Kingdom: surfaces=129, main=118, visible=112, open=64, IMG04=11
- Georgia: surfaces=122, main=122, visible=121, open=93, IMG04=1
- Peru: surfaces=110, main=110, visible=109, open=87, IMG04=1
- Chile: surfaces=99, main=98, visible=96, open=85, IMG04=3
- Ukraine: surfaces=99, main=95, visible=97, open=92, IMG04=2
- Australia: surfaces=89, main=87, visible=83, open=33, IMG04=6
- Iraq: surfaces=79, main=79, visible=78, open=75, IMG04=1
- Philippines: surfaces=79, main=75, visible=75, open=67, IMG04=4
- India: surfaces=77, main=73, visible=69, open=64, IMG04=8
- Nigeria: surfaces=73, main=73, visible=67, open=64, IMG04=6
- Bangladesh: surfaces=58, main=58, visible=57, open=55, IMG04=1
- South Africa: surfaces=57, main=49, visible=41, open=9, IMG04=16
- Taiwan: surfaces=56, main=54, visible=55, open=40, IMG04=1
- Germany: surfaces=54, main=53, visible=52, open=43, IMG04=1

## Failed Gates

- object_verified_open_rate: 80.92 (Minimum object verified-open=85%.)
- object_weighted_publication_grade_rate: 81.39 (Object-level max image weight per object; repeated photos are not double-counted.)
