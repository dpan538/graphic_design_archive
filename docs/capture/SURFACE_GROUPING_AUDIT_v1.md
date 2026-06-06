# Surface Grouping Audit v1

Date: 2026-06-01

This audit proposes group candidates before the next broad coverage pass. It does not mutate public surfaces. Groups are archive organization units: they decide where loose leaves, support packets, child cards, appendices, and bookmarks should attach.

## Summary

- Candidate groups: 553
- Candidate memberships: 8132

## Group Types

- `folder_cell_decade`: 302
- `same_source_collection`: 152
- `same_series_stem`: 57
- `same_title_within_source`: 42

## Recommended Actions

- `canonical_main_with_source_register`: 323
- `review_only`: 107
- `canonical_main_with_support_children`: 93
- `support_packet_cluster`: 25
- `compound_main_candidate`: 5

## Coverage Gap Flags

- `coverage_ready`: 430
- `needs_text`: 47
- `multi_region_review`: 44
- `needs_image`: 34
- `needs_rights`: 29

## Confidence

- `medium`: 446
- `low`: 65
- `high`: 42

## High-Value Next Groups

- GRP0370 | same_source_collection | 15 members | canonical_main_with_support_children | needs_image;needs_text;needs_rights;multi_region_review | The Search for Human Resources in Germany
- GRP0480 | same_source_collection | 11 members | compound_main_candidate | needs_image;needs_text | Untitled (Green Goat)
- GRP0075 | folder_cell_decade | 6 members | compound_main_candidate | needs_image;needs_text | アートディレクター入門 : 広告を魅せる人たちがいる
- GRP0463 | same_source_collection | 6 members | compound_main_candidate | needs_image;needs_text | アートディレクター入門 : 広告を魅せる人たちがいる
- GRP0368 | same_source_collection | 4 members | compound_main_candidate | needs_image;needs_text;needs_rights;multi_region_review | The Centenary of the Omnibus
- GRP0306 | same_series_stem | 2 members | support_packet_cluster | needs_image;needs_text;needs_rights;multi_region_review | Exhibition Poster
- GRP0356 | same_series_stem | 2 members | review_only | needs_image;needs_text | Travel Shop Post Early
- GRP0372 | same_source_collection | 2 members | support_packet_cluster | needs_image;needs_text;needs_rights | Dwan Gallery Poster
- GRP0481 | same_source_collection | 2 members | support_packet_cluster | needs_image;needs_text | Untitled (Fuera de caja proof)
- GRP0551 | same_title_within_source | 2 members | review_only | needs_image;needs_text | Travel Shop Post Early
- GRP0241 | folder_cell_decade | 11 members | canonical_main_with_source_register | needs_text | شادیهای زندگی ما (لوگو).jpg
- GRP0163 | folder_cell_decade | 8 members | canonical_main_with_source_register | needs_text | "Cuba Libre: A Musical Celebration" flyer and poster
- GRP0401 | same_source_collection | 8 members | compound_main_candidate | needs_text | Untitled Illustration (Taranaki Herald, 21 July 1904)
- GRP0405 | same_source_collection | 6 members | canonical_main_with_source_register | needs_text | Summer City poster, Pacific Island Festival
- GRP0484 | same_source_collection | 4 members | canonical_main_with_source_register | needs_text | A Cuba, con el fusil en la mano
- GRP0324 | same_series_stem | 3 members | support_packet_cluster | needs_text | Untitled Illustration (Taranaki Herald, 21 July 1904)
- GRP0336 | same_series_stem | 3 members | support_packet_cluster | needs_text | Commercial Art Techniques
- GRP0479 | same_source_collection | 3 members | support_packet_cluster | needs_text;multi_region_review | Tāhae 250 poster
- GRP0538 | same_title_within_source | 3 members | support_packet_cluster | needs_text | Commercial Art Techniques
- GRP0308 | same_series_stem | 2 members | review_only | needs_text | Civic Theatre, Queen Street, Auckland Central, 2016
- GRP0310 | same_series_stem | 2 members | review_only | needs_text | Infinity Within
- GRP0320 | same_series_stem | 2 members | review_only | needs_text | Summer City poster (main)
- GRP0321 | same_series_stem | 2 members | support_packet_cluster | needs_text | Untitled Illustration (Observer, 27 September 1902) grouped records, 1902
- GRP0322 | same_series_stem | 2 members | support_packet_cluster | needs_text | Untitled Illustration (Otago Witness, 26 August 1903)
- GRP0323 | same_series_stem | 2 members | support_packet_cluster | needs_text | Untitled Illustration (Otago Witness, 20 December 1879) grouped records, 1879

## Use In Next Coverage Pass

The 1970-2026 pass should use these groups as targets. New records should first try to attach to a group by source identifier, title stem, source collection, series/campaign/event, or folder-cell decade. Only records that cannot responsibly attach should create new groups.

Group-level gaps should drive capture queries:

- `needs_image`: search IIIF, source viewer, Commons/open image, or local collection image endpoints.
- `needs_text`: search catalogue essays, collection notes, OCR pages, exhibition text, or institutional context.
- `needs_rights`: search item-level rights, source policy, IIIF manifest rights, or access statements.
- `multi_region_review`: do not collapse into a single national narrative without evidence.
