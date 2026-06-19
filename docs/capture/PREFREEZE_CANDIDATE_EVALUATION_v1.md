# Prefreeze Candidate Evaluation v1

Scope: candidate public-surface payload generated from all local capture records after P0 pre-freeze exclusions. Official payload and frontend mirrors are unchanged.

## Gate Summary

- candidate_active_public_sources: 14997 · fail (Distinct sourceName values; target=20000.)
- candidate_release_source_coverage_rate: 74.98 · fail (Candidate source-name coverage against 20,000 final target.)
- candidate_object_source_visible_rate: 98.92 · fail (Gate target=99%.)
- candidate_object_verified_open_rate: 95.29 · pass (Gate target=95%.)
- candidate_object_weighted_publication_grade_rate: 97.26 · pass (Object-level max image weight; repeated photos count once.)
- candidate_object_img04_rate: 0.82 · pass (Gate max=10%.)
- candidate_2025_2026_surface_rate: 1.58 · pass (High 2025/2026 share is suspicious and should be audited for date leakage.)

## Core Metrics

- candidate_public_surfaces: 16175 (Candidate payload only; official payload unchanged.)
- candidate_active_public_sources: 14997 (Distinct sourceName values; target=20000.)
- candidate_release_source_coverage_rate: 74.98 (Candidate source-name coverage against 20,000 final target.)
- candidate_surface_source_visible_rate: 98.88 (Surface-level IMG01/IMG02/IMG03.)
- candidate_surface_verified_open_rate: 95.25 (Surface-level IMG03 with rightsReviewed=true.)
- candidate_object_count: 16167 (Object-level grouping; repeated photos/views count once.)
- candidate_object_source_visible_rate: 98.92 (Gate target=99%.)
- candidate_object_verified_open_rate: 95.29 (Gate target=95%.)
- candidate_object_weighted_publication_grade_rate: 97.26 (Object-level max image weight; repeated photos count once.)
- candidate_object_img04_rate: 0.82 (Gate max=10%.)
- candidate_period_surface_balance_rate: 100.00 (Average surface fill against period targets.)
- candidate_region_surface_balance_rate: 91.71 (Average surface fill against regional targets.)
- candidate_strict_distribution_adjusted_source_coverage_rate: 74.98 (min(source coverage, period balance, region balance).)
- candidate_2025_2026_surface_rate: 1.58 (High 2025/2026 share is suspicious and should be audited for date leakage.)
- candidate_independent_studio_school_platform_2005_2025_count: 189 (Heuristic count for contemporary studios, schools, platforms, festivals, and collectives.)

## Sheet Structure

- main_sheet_count: 13737 (publicationRole=main_sheet.)
- sub_or_support_surface_count: 2438 (All non-main public surfaces.)
- independent_text_sheet_count: 94 (templateId=sheet.text.v0.)
- rich_text_surface_count_ge1200_chars: 16173 (Reading/support text >= 1200 chars.)
- weak_text_main_sheet_count: 0 (Main sheets with weak source/generated text.)
- research_dossier_count: 16175 (Dossier anchors in candidate payload.)
- dossier_text_page_count: 14231 (text_page entries in researchDossiers.)
- dossier_sub_card_appendix_count: 5164 (sub_sheet/card/appendix/child_source_record entries.)
- dossiers_with_more_than_two_support_pages: 20 (Research packets with >2 sub/card/appendix/child pages.)
- dossiers_with_more_than_five_text_pages: 0 (Research packets with >5 text pages.)

## Weakest 5-Year Buckets

- 1835-1839: surfaces=27, main=25, open=26
- 1855-1859: surfaces=39, main=35, open=38
- 1840-1844: surfaces=67, main=62, open=66
- undated_or_unparsed: surfaces=73, main=3, open=1
- 1875-1879: surfaces=78, main=68, open=78
- 1860-1864: surfaces=89, main=78, open=88
- 1850-1854: surfaces=96, main=89, open=96
- 1865-1869: surfaces=106, main=101, open=105
- 1870-1874: surfaces=108, main=101, open=108
- 1830-1834: surfaces=141, main=137, open=141
- 1890-1894: surfaces=197, main=182, open=194
- 1880-1884: surfaces=203, main=173, open=194

## Heaviest 5-Year Buckets

- 1970-1974: surfaces=1303, dominant_source=Georgia State University Library Digital Collections / CONTENTdm (9)
- 1975-1979: surfaces=1103, dominant_source=Georgia State University Library Digital Collections / CONTENTdm (10)
- 1940-1944: surfaces=957, dominant_source=Wikimedia Commons (30)
- 2020-2024: surfaces=887, dominant_source=DigitalNZ (10)
- 1935-1939: surfaces=859, dominant_source=Library of Congress loc.gov API (23)
- 2015-2019: surfaces=636, dominant_source=Internet Archive / text and periodical collections (16)
- 1965-1969: surfaces=613, dominant_source=Wellcome Collection Catalogue API (15)
- 1930-1934: surfaces=596, dominant_source=Gallica / BnF APIs (27)
- 2005-2009: surfaces=590, dominant_source=DigitalNZ (6)
- 1950-1954: surfaces=566, dominant_source=Wellcome Collection Catalogue API (11)
- 2010-2014: surfaces=539, dominant_source=DigitalNZ (19)
- 1945-1949: surfaces=474, dominant_source=Wellcome Collection Catalogue API (13)

## Weakest Regions By Surface Count

- Brunei: surfaces=1, visible=1, open=1
- Puerto Rico: surfaces=1, visible=1, open=0
- Vanuatu: surfaces=1, visible=1, open=1
- Tonga: surfaces=2, visible=2, open=2
- Kiribati: surfaces=3, visible=3, open=3
- Togo: surfaces=3, visible=3, open=3
- Mali: surfaces=4, visible=4, open=4
- Oman: surfaces=4, visible=4, open=4
- Rwanda: surfaces=5, visible=5, open=5
- Samoa: surfaces=5, visible=5, open=5
- Fiji: surfaces=6, visible=6, open=6
- Timor-Leste: surfaces=6, visible=6, open=6

## Review Warnings

- year_2025_2026_high_share: count=255, rate=1.58% (2025-2026 should be inspected for capture-date leakage and weak contemporary research value.)
- post_2026_or_error: count=0, rate=0.00% (Future dates are release blockers.)
- post_2010_stamp_like: count=5, rate=0.03% (Recent commemorative stamp-like rows should be reduced unless design relevance is strong.)
- event_photo_like: count=63, rate=0.39% (Event/photo memory material should usually become card/support material, not design-object main sheets.)

## Failed Gates

- candidate_active_public_sources: 14997 (Distinct sourceName values; target=20000.)
- candidate_release_source_coverage_rate: 74.98 (Candidate source-name coverage against 20,000 final target.)
- candidate_object_source_visible_rate: 98.92 (Gate target=99%.)

## Safety

- No image files were downloaded.
- IMG01/IMG03 were not upgraded by heuristic, LLM, TOS, or platform signals.
- Candidate metrics are for deciding the next cleaning/rebuild focus; they are not a release promotion.
