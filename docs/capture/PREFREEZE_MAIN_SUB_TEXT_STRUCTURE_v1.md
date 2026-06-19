# Prefreeze Main/Sub/Text Structure Audit v1

Scope: candidate payload structure audit after pre-freeze cleaning overrides. It evaluates distribution, not historical correctness.

## Summary

- surfaces: 16175 (Candidate surfaces scanned.)
- research_dossiers: 16175 (Research dossiers generated.)
- main_sheet_review_rows: 13728 (Main sheets with thin text or no subsheet relation.)
- main_with_compound_children: 9 (Main sheets with compoundChildren.)
- main_with_compound_children_gt2: 9 (Main sheets with more than two child records.)
- main_with_compound_children_gt5: 4 (Main sheets with more than five child records.)
- main_dossiers_with_subsheet_pages_gt2: 0 (Dossier page sequences with more than two subsheet pages.)
- main_dossiers_with_text_pages_gt5: 0 (Dossier page sequences with more than five text pages.)
- surface_type:sheet: 14231 (Surface type distribution.)
- surface_type:card: 1944 (Surface type distribution.)
- publication_role:main_sheet: 13737 (Publication role distribution.)
- publication_role:card: 1943 (Publication role distribution.)
- publication_role:support_packet_appendix_text: 489 (Publication role distribution.)
- publication_role:thin_visual_support_packet: 3 (Publication role distribution.)
- publication_role:: 2 (Publication role distribution.)
- publication_role:merge_candidate_support_packet: 1 (Publication role distribution.)
- dossier_anchor:main_sheet: 13739 (Research dossier anchor distribution.)
- dossier_anchor:card: 1944 (Research dossier anchor distribution.)
- dossier_anchor:subsheet: 492 (Research dossier anchor distribution.)
- dossier_page:text_page: 14231 (Research dossier page type distribution.)
- dossier_page:main_sheet: 13739 (Research dossier page type distribution.)
- dossier_page:appendix: 3089 (Research dossier page type distribution.)
- dossier_page:card: 1944 (Research dossier page type distribution.)
- dossier_page:subsheet: 492 (Research dossier page type distribution.)
- dossier_page:child_source_record: 131 (Research dossier page type distribution.)

## Period Counts

- pre_1850: main 474, sub 8, card 4, text 482, appendix 96
- 1850_1899: main 1298, sub 65, card 47, text 1365, appendix 268
- 1900_1913: main 771, sub 57, card 22, text 828, appendix 180
- 1914_1945: main 3601, sub 91, card 107, text 3692, appendix 788
- 1946_1969: main 2190, sub 92, card 64, text 2282, appendix 473
- 1970_1989: main 2869, sub 64, card 128, text 2933, appendix 645
- 1990_1999: main 810, sub 16, card 53, text 826, appendix 180
- 2000_2009: main 768, sub 32, card 152, text 800, appendix 178
- 2010_2019: main 633, sub 19, card 523, text 652, appendix 170
- 2020_2026: main 320, sub 7, card 815, text 327, appendix 94
- undated: main 3, sub 41, card 29, text 44, appendix 17

## Interpretation

- `main_sheet_review_rows` marks main sheets that are thin or have no visible subsheet relation; it is a review queue, not an automatic downgrade list.
- `compoundChildren` is currently the only explicit intra-main relation available in the payload; most dossiers are still single-anchor records.
- Text pages are generated one per sheet-level surface, so high text-page count does not yet mean editorial depth. The reading-length review queue is more meaningful.
