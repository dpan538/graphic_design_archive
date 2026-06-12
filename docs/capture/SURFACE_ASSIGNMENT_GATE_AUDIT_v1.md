# Surface Assignment Gate Audit v1

Date: 2026-06-01

Scope: capture records, before any public payload rebuild. This audit applies the hierarchy main sheet -> subsheet -> appendix/text sheet -> card/slip -> bookmark and uses linkage groups to suppress standalone thin or duplicated sheets.

## Summary

- Capture rows audited: 13879
- Rows requiring group/linkage review before standalone publication: 105

## Recommended Dispositions

- `main_sheet_candidate`: 12946
- `subsheet_visual`: 522
- `text_sheet_candidate`: 198
- `dedupe_child_record`: 60
- `appendix_or_text_sheet`: 55
- `subsheet_text_or_appendix_review`: 37
- `subsheet_group_child`: 22
- `subsheet_or_group_anchor_review`: 18
- `img00_rights_sheet_candidate`: 16
- `duplicate_image_review_packet`: 5

## Period Breakdown

- 1930_1970: main_sheet_candidate: 3540; subsheet_visual: 73; subsheet_text_or_appendix_review: 25; appendix_or_text_sheet: 24; img00_rights_sheet_candidate: 14; subsheet_group_child: 13; dedupe_child_record: 8; text_sheet_candidate: 8; subsheet_or_group_anchor_review: 8; duplicate_image_review_packet: 3
- 1970_2000: main_sheet_candidate: 3021; subsheet_visual: 261; text_sheet_candidate: 9; subsheet_or_group_anchor_review: 2; img00_rights_sheet_candidate: 1
- 2000_2026: main_sheet_candidate: 4014; text_sheet_candidate: 147; subsheet_visual: 74; dedupe_child_record: 19; appendix_or_text_sheet: 7; subsheet_text_or_appendix_review: 4; subsheet_or_group_anchor_review: 2; duplicate_image_review_packet: 2
- pre_1930: main_sheet_candidate: 2354; subsheet_visual: 104; dedupe_child_record: 30; appendix_or_text_sheet: 11; subsheet_group_child: 9; subsheet_or_group_anchor_review: 6; text_sheet_candidate: 6; subsheet_text_or_appendix_review: 5; img00_rights_sheet_candidate: 1
- undated_or_unparsed: text_sheet_candidate: 28; main_sheet_candidate: 17; appendix_or_text_sheet: 13; subsheet_visual: 10; dedupe_child_record: 3; subsheet_text_or_appendix_review: 3

## Image-State Breakdown

- IMG00: appendix_or_text_sheet: 18; img00_rights_sheet_candidate: 16; dedupe_child_record: 11; subsheet_text_or_appendix_review: 10; subsheet_or_group_anchor_review: 4
- IMG01: main_sheet_candidate: 27; subsheet_visual: 14; dedupe_child_record: 4; subsheet_or_group_anchor_review: 2
- IMG02: main_sheet_candidate: 1236; subsheet_visual: 107; dedupe_child_record: 15; subsheet_group_child: 14; subsheet_or_group_anchor_review: 3; duplicate_image_review_packet: 3
- IMG03: main_sheet_candidate: 11683; subsheet_visual: 401; dedupe_child_record: 11; subsheet_or_group_anchor_review: 3; duplicate_image_review_packet: 2
- IMG04: text_sheet_candidate: 198; appendix_or_text_sheet: 37; subsheet_text_or_appendix_review: 27; dedupe_child_record: 19; subsheet_group_child: 8; subsheet_or_group_anchor_review: 6

## Thin / Support Examples

- ECAP002 | subsheet_visual | score 96 | source text 0 | La Gismonda (Sarah Bernhardt)
- ECAP008 | appendix_or_text_sheet | score 80 | source text 0 | Barack Obama "Hope" Poster
- ECAP016 | subsheet_visual | score 96 | source text 0 | Yvette Guilbert
- ECAP017 | subsheet_visual | score 96 | source text 0 | Virgin and Child
- ECAP018 | subsheet_visual | score 96 | source text 0 | Poster for the Lembrée Gallery
- ECAP021 | subsheet_visual | score 96 | source text 0 | Bill Poster
- ECAP022 | subsheet_visual | score 96 | source text 0 | Masters of the Poster: Poster for Exhibition of Artistic Posters of Wilhelm Söborg
- ECAP023 | subsheet_visual | score 96 | source text 0 | May Belfort
- ECAP027 | subsheet_visual | score 90 | source text 0 | Zimbabwe.  One Enemy: Imperialism [verso]
- ECAP030 | subsheet_visual | score 90 | source text 0 | Political Poster Show 1977
- ECAP031 | subsheet_visual | score 90 | source text 0 | A nation that enslaves another cannot itself be free
- ECAP032 | appendix_or_text_sheet | score 80 | source text 0 | Self-Determination For The Irish People
- ECAP033 | subsheet_visual | score 90 | source text 0 | Victory to People's War
- ECAP034 | appendix_or_text_sheet | score 80 | source text 0 | Zimbabwe. One Enemy: Imperialism.
- ECAP035 | appendix_or_text_sheet | score 80 | source text 0 | Free World. Third World. Socialist World.
- ECAP036 | appendix_or_text_sheet | score 80 | source text 0 | A for africa
- ECAP037 | appendix_or_text_sheet | score 80 | source text 0 | Supporting An Army Of The People And For The People
- ECAP038 | appendix_or_text_sheet | score 80 | source text 0 | Support The Struggle Of The United Farm Workers
- ECAP039 | appendix_or_text_sheet | score 80 | source text 0 | In Support Of The Courageous Stand Made By Hull Prisoners
- ECAP040 | subsheet_visual | score 90 | source text 0 | Air India. Immingrant Labour.

## Group Review Examples

- ECAP001 | dedupe_child_record | SRLG0334 | same_entity_confirmed | Buy a Little Present for the Kaiser
- ECAP003 | dedupe_child_record | SRLG0325 | same_entity_confirmed | Zodiaque ("La Plume")
- ECAP004 | dedupe_child_record | SRLG0332 | same_entity_confirmed | To the Amputees—Join the Workforce
- ECAP005 | dedupe_child_record | SRLG0333 | same_entity_confirmed | Keep These Off the U.S.A.
- ECAP006 | dedupe_child_record | SRLG0326 | same_entity_confirmed | 1952 Exhibition Poster
- ECAP007 | dedupe_child_record | SRLG0328 | same_entity_confirmed | This Is the Enemy
- ECAP009 | dedupe_child_record | SRLG0335 | same_entity_confirmed | Invest in the Victory Liberty Loan
- ECAP010 | dedupe_child_record | SRLG0327 | same_entity_confirmed | An Attempt Using Unfit Means
- ECAP011 | dedupe_child_record | SRLG0331 | same_entity_confirmed | The Modern Poster
- ECAP012 | dedupe_child_record | SRLG0329 | same_entity_confirmed | Untitled
- ECAP013 | dedupe_child_record | SRLG0330 | same_entity_confirmed | Our One-Thousandth Blow
- ECAP014 | dedupe_child_record | SRLG0337 | same_entity_confirmed | No. 2 Spring
- ECAP015 | dedupe_child_record | SRLG0336 | same_entity_confirmed | Moulin Rouge, La Goulue
- ECAP019 | dedupe_child_record | SRLG0341 | same_entity_confirmed | May Milton
- ECAP020 | dedupe_child_record | SRLG0343 | same_entity_confirmed | Sculptress
- ECAP024 | dedupe_child_record | SRLG0213 | same_entity_confirmed | Street Advertising
- ECAP025 | dedupe_child_record | SRLG0212 | same_entity_confirmed | Perched upon a Bust of Pallas
- ECAP026 | dedupe_child_record | SRLG0362 | same_entity_confirmed | Piper at the Gates of Dawn
- ECAP028 | dedupe_child_record | SRLG0361 | same_entity_confirmed | There flows from Latin America
- ECAP029 | dedupe_child_record | SRLG0355 | same_entity_confirmed | Picture Posters

## Implementation Notes

- This is an audit layer, not a destructive migration.
- `dedupe_child_record` and `subsheet_group_child` should not receive independent main-sheet SEQ numbers until reviewed.
- `subsheet_visual` is the new home for many former thin main sheets.
- `main_sheet_candidate` still needs final rights, source-return, folder-membership, and research-unit checks.
- The next payload rebuild should consume this audit so cards, bookmarks, text pages, and AX appendices become real publication surfaces instead of visual labs.
