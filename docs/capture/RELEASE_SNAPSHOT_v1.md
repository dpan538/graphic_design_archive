# Release Snapshot v1

Scope: consolidated read-only release-health snapshot. Object-level image metrics count repeated views/photos of one source object once.

## Gate Summary

- archive_active_public_sources: 12342 · pass (Distinct public-surface source names; release target=2000.)
- release_source_coverage_rate: 617.10 · pass (Minimum release source coverage=80%.)
- object_source_visible_rate: 97.91 · pass (Minimum object source-visible=96%.)
- object_verified_open_rate: 87.96 · pass (Minimum object verified-open=85%.)
- object_weighted_publication_grade_rate: 84.57 · fail (Object-level max image weight per object; repeated photos are not double-counted.)
- object_img04_rate: 1.78 · pass (Maximum object IMG04 target=10%.)
- year_2026_surface_rate: 0.39 · pass (Warning if more than 25% of public surfaces date to 2026.)
- post_2026_or_error_count: 0 · pass (Future year date sanity check.)

## Core Metrics

- public_surfaces: 13680 (Generated public surfaces.)
- archive_active_public_sources: 12342 (Distinct public-surface source names; release target=2000.)
- release_source_coverage_rate: 617.10 (Minimum release source coverage=80%.)
- surface_source_visible_rate: 97.80 (Surface-level IMG01/IMG02/IMG03.)
- surface_verified_open_rate: 87.83 (Surface-level reviewed IMG03.)
- object_count: 13659 (Object-level grouping; repeated views/photos count once.)
- object_source_visible_rate: 97.91 (Minimum object source-visible=96%.)
- object_verified_open_rate: 87.96 (Minimum object verified-open=85%.)
- object_weighted_publication_grade_rate: 84.57 (Object-level max image weight per object; repeated photos are not double-counted.)
- object_img04_rate: 1.78 (Maximum object IMG04 target=10%.)
- main_sheet_count: 13419 (publicationRole=main_sheet.)
- sub_or_support_surface_count: 261 (All surfaces not marked as main_sheet.)
- independent_text_sheet_count: 242 (templateId=sheet.text.v0.)
- dossier_text_page_count: 13666 (text_page entries inside researchDossiers pageSequence.)
- dossier_sub_card_appendix_count: 3247 (sub_sheet/card/appendix entries inside researchDossiers pageSequence.)
- year_2026_surface_rate: 0.39 (Warning if more than 25% of public surfaces date to 2026.)
- post_2026_or_error_count: 0 (Future year date sanity check.)
- undated_or_unparsed_count: 748 (Missing/unparsed public surface dates.)

## Main Sheets by Period

- 1930_1970: main=3614, surfaces=3719, IMG04=43
- 1970_2000: main=3180, surfaces=3210, IMG04=22
- 2000_2026: main=3516, surfaces=3545, IMG04=38
- pre_1930: main=2410, surfaces=2458, IMG04=10
- undated_or_unparsed: main=699, surfaces=748, IMG04=145

## Region Distribution

- Unresolved region: surfaces=3945, main=3858, visible=3856, open=3461, IMG04=81
- Indonesia: surfaces=1079, main=1076, visible=1075, open=1071, IMG04=4
- Mexico: surfaces=561, main=559, visible=554, open=549, IMG04=6
- Brazil: surfaces=486, main=483, visible=482, open=480, IMG04=4
- Argentina: surfaces=435, main=433, visible=434, open=354, IMG04=1
- Iran: surfaces=406, main=405, visible=405, open=400, IMG04=1
- India: surfaces=356, main=352, visible=348, open=343, IMG04=8
- Aotearoa New Zealand: surfaces=338, main=304, visible=334, open=225, IMG04=3
- Colombia: surfaces=334, main=334, visible=331, open=190, IMG04=3
- Kazakhstan: surfaces=327, main=327, visible=326, open=321, IMG04=1
- Bolivia: surfaces=310, main=310, visible=310, open=303, IMG04=0
- Iraq: surfaces=301, main=301, visible=300, open=297, IMG04=1
- France: surfaces=298, main=291, visible=295, open=265, IMG04=1
- Algeria: surfaces=291, main=291, visible=289, open=284, IMG04=2
- United States: surfaces=279, main=255, visible=262, open=137, IMG04=5
- Ukraine: surfaces=228, main=224, visible=226, open=221, IMG04=2
- Philippines: surfaces=227, main=221, visible=223, open=215, IMG04=4
- China: surfaces=207, main=202, visible=203, open=199, IMG04=3
- Australia: surfaces=194, main=192, visible=188, open=138, IMG04=6
- Peru: surfaces=155, main=155, visible=154, open=132, IMG04=1
- Turkey: surfaces=148, main=147, visible=148, open=144, IMG04=0
- Romania: surfaces=147, main=147, visible=145, open=134, IMG04=1
- South Africa: surfaces=143, main=135, visible=127, open=95, IMG04=16
- Italy: surfaces=142, main=140, visible=140, open=140, IMG04=0
- Korean Peninsula: surfaces=135, main=130, visible=132, open=130, IMG04=3

## Failed Gates

- object_weighted_publication_grade_rate: 84.57 (Object-level max image weight per object; repeated photos are not double-counted.)
