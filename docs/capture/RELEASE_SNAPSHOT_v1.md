# Release Snapshot v1

Scope: consolidated read-only release-health snapshot. Object-level image metrics count repeated views/photos of one source object once.

## Gate Summary

- archive_active_public_sources: 6499 · pass (Distinct public-surface source names; release target=2000.)
- release_source_coverage_rate: 324.95 · pass (Minimum release source coverage=80%.)
- object_source_visible_rate: 96.34 · pass (Minimum object source-visible=96%.)
- object_verified_open_rate: 78.96 · fail (Minimum object verified-open=85%.)
- object_weighted_publication_grade_rate: 80.51 · fail (Object-level max image weight per object; repeated photos are not double-counted.)
- object_img04_rate: 3.11 · pass (Maximum object IMG04 target=10%.)
- year_2026_surface_rate: 0.51 · pass (Warning if more than 25% of public surfaces date to 2026.)
- post_2026_or_error_count: 0 · pass (Future year date sanity check.)

## Core Metrics

- public_surfaces: 7836 (Generated public surfaces.)
- archive_active_public_sources: 6499 (Distinct public-surface source names; release target=2000.)
- release_source_coverage_rate: 324.95 (Minimum release source coverage=80%.)
- surface_source_visible_rate: 96.16 (Surface-level IMG01/IMG02/IMG03.)
- surface_verified_open_rate: 78.75 (Surface-level reviewed IMG03.)
- object_count: 7815 (Object-level grouping; repeated views/photos count once.)
- object_source_visible_rate: 96.34 (Minimum object source-visible=96%.)
- object_verified_open_rate: 78.96 (Minimum object verified-open=85%.)
- object_weighted_publication_grade_rate: 80.51 (Object-level max image weight per object; repeated photos are not double-counted.)
- object_img04_rate: 3.11 (Maximum object IMG04 target=10%.)
- main_sheet_count: 7582 (publicationRole=main_sheet.)
- sub_or_support_surface_count: 254 (All surfaces not marked as main_sheet.)
- independent_text_sheet_count: 242 (templateId=sheet.text.v0.)
- dossier_text_page_count: 7822 (text_page entries inside researchDossiers pageSequence.)
- dossier_sub_card_appendix_count: 2048 (sub_sheet/card/appendix entries inside researchDossiers pageSequence.)
- year_2026_surface_rate: 0.51 (Warning if more than 25% of public surfaces date to 2026.)
- post_2026_or_error_count: 0 (Future year date sanity check.)
- undated_or_unparsed_count: 748 (Missing/unparsed public surface dates.)

## Main Sheets by Period

- 1930_1970: main=2213, surfaces=2318, IMG04=43
- 1970_2000: main=2167, surfaces=2197, IMG04=22
- 2000_2026: main=1018, surfaces=1040, IMG04=38
- pre_1930: main=1485, surfaces=1533, IMG04=10
- undated_or_unparsed: main=699, surfaces=748, IMG04=145

## Region Distribution

- Unresolved region: surfaces=4603, main=4446, visible=4441, open=3750, IMG04=151
- Mexico: surfaces=494, main=492, visible=487, open=481, IMG04=6
- Latin America: surfaces=427, main=427, visible=406, open=222, IMG04=21
- Argentina: surfaces=425, main=423, visible=424, open=344, IMG04=1
- Brazil: surfaces=334, main=331, visible=330, open=328, IMG04=4
- United States: surfaces=309, main=285, visible=287, open=149, IMG04=10
- France: surfaces=306, main=299, visible=303, open=266, IMG04=1
- Italy: surfaces=142, main=140, visible=140, open=140, IMG04=0
- United Kingdom: surfaces=136, main=125, visible=119, open=68, IMG04=11
- Chile: surfaces=99, main=98, visible=96, open=85, IMG04=3
- Australia: surfaces=95, main=92, visible=88, open=36, IMG04=7
- India: surfaces=74, main=70, visible=66, open=61, IMG04=8
- Germany: surfaces=61, main=60, visible=59, open=48, IMG04=1
- South Africa: surfaces=58, main=50, visible=42, open=10, IMG04=16
- China: surfaces=53, main=48, visible=49, open=44, IMG04=3
- Turkey: surfaces=44, main=44, visible=44, open=40, IMG04=0
- Egypt: surfaces=40, main=40, visible=39, open=23, IMG04=1
- Japan: surfaces=34, main=19, visible=24, open=18, IMG04=10
- Russia: surfaces=26, main=19, visible=19, open=17, IMG04=0
- Palestine: surfaces=24, main=23, visible=24, open=19, IMG04=0
- Uruguay: surfaces=20, main=20, visible=19, open=0, IMG04=1
- Switzerland: surfaces=11, main=11, visible=10, open=8, IMG04=1
- Cuba: surfaces=6, main=6, visible=5, open=4, IMG04=1
- Netherlands: surfaces=6, main=6, visible=6, open=3, IMG04=0
- Poland: surfaces=6, main=6, visible=5, open=5, IMG04=1

## Failed Gates

- object_verified_open_rate: 78.96 (Minimum object verified-open=85%.)
- object_weighted_publication_grade_rate: 80.51 (Object-level max image weight per object; repeated photos are not double-counted.)
