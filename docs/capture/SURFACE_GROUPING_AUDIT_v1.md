# Surface Grouping Audit v1

Date: 2026-06-01

This audit proposes group candidates before the next broad coverage pass. It does not mutate public surfaces. Groups are archive organization units: they decide where loose leaves, support packets, child cards, appendices, and bookmarks should attach.

## Summary

- Candidate groups: 257
- Candidate memberships: 1773

## Group Types

- `same_source_collection`: 97
- `folder_cell_decade`: 84
- `same_series_stem`: 44
- `same_title_within_source`: 32

## Recommended Actions

- `canonical_main_with_source_register`: 102
- `review_only`: 66
- `canonical_main_with_support_children`: 63
- `support_packet_cluster`: 23
- `compound_main_candidate`: 3

## Coverage Gap Flags

- `coverage_ready`: 168
- `multi_region_review`: 43
- `needs_text`: 34
- `needs_rights`: 25
- `needs_image`: 16

## Confidence

- `medium`: 205
- `high`: 32
- `low`: 20

## High-Value Next Groups

- GRP0133 | same_source_collection | 15 members | canonical_main_with_support_children | needs_image;needs_text;needs_rights;multi_region_review | The Search for Human Resources in Germany
- GRP0207 | same_source_collection | 11 members | compound_main_candidate | needs_image;needs_text | Untitled (Green Goat)
- GRP0131 | same_source_collection | 4 members | compound_main_candidate | needs_image;needs_text;needs_rights;multi_region_review | The Centenary of the Omnibus
- GRP0085 | same_series_stem | 2 members | support_packet_cluster | needs_image;needs_text;needs_rights;multi_region_review | Exhibition Poster
- GRP0126 | same_series_stem | 2 members | review_only | needs_image;needs_text | Travel Shop Post Early
- GRP0135 | same_source_collection | 2 members | support_packet_cluster | needs_image;needs_text;needs_rights | Dwan Gallery Poster
- GRP0208 | same_source_collection | 2 members | support_packet_cluster | needs_image;needs_text | Untitled (Fuera de caja proof)
- GRP0256 | same_title_within_source | 2 members | review_only | needs_image;needs_text | Travel Shop Post Early
- GRP0149 | same_source_collection | 8 members | compound_main_candidate | needs_text | Untitled Illustration (Taranaki Herald, 21 July 1904)
- GRP0043 | folder_cell_decade | 7 members | canonical_main_with_source_register | needs_text | Toiling Midgets: Sketches
- GRP0099 | same_series_stem | 3 members | support_packet_cluster | needs_text | Untitled Illustration (Taranaki Herald, 21 July 1904)
- GRP0111 | same_series_stem | 3 members | support_packet_cluster | needs_text | Commercial Art Techniques
- GRP0206 | same_source_collection | 3 members | support_packet_cluster | needs_text;multi_region_review | Tāhae 250 poster
- GRP0245 | same_title_within_source | 3 members | support_packet_cluster | needs_text | Commercial Art Techniques
- GRP0087 | same_series_stem | 2 members | review_only | needs_text | Infinity Within
- GRP0096 | same_series_stem | 2 members | support_packet_cluster | needs_text | Untitled Illustration (Observer, 27 September 1902) grouped records, 1902
- GRP0097 | same_series_stem | 2 members | support_packet_cluster | needs_text | Untitled Illustration (Otago Witness, 26 August 1903)
- GRP0098 | same_series_stem | 2 members | support_packet_cluster | needs_text | Untitled Illustration (Otago Witness, 20 December 1879) grouped records, 1879
- GRP0110 | same_series_stem | 2 members | canonical_main_with_support_children | needs_text;multi_region_review | Commercial art
- GRP0114 | same_series_stem | 2 members | support_packet_cluster | needs_text | graphic design
- GRP0117 | same_series_stem | 2 members | support_packet_cluster | needs_text | American guide week, Nov. 10-16 Take pride in your country : State by state the WPA Writers' Projects describe America to Americans /
- GRP0118 | same_series_stem | 2 members | support_packet_cluster | needs_text | WPA exhibition [of] Dorothy Loeb [and] Blanche Lazzell Federal Art Gallery, 77 Newbury St. Boston /
- GRP0123 | same_series_stem | 2 members | support_packet_cluster | needs_text | Poster, 'No More Hiroshimas'
- GRP0148 | same_source_collection | 2 members | support_packet_cluster | needs_text | Untitled Illustration (Otago Witness, 24 July 1880)
- GRP0183 | same_source_collection | 2 members | support_packet_cluster | needs_text | American guide week, Nov. 10-16 Take pride in your country : State by state the WPA Writers' Projects describe America to Americans /

## Use In Next Coverage Pass

The 1970-2026 pass should use these groups as targets. New records should first try to attach to a group by source identifier, title stem, source collection, series/campaign/event, or folder-cell decade. Only records that cannot responsibly attach should create new groups.

Group-level gaps should drive capture queries:

- `needs_image`: search IIIF, source viewer, Commons/open image, or local collection image endpoints.
- `needs_text`: search catalogue essays, collection notes, OCR pages, exhibition text, or institutional context.
- `needs_rights`: search item-level rights, source policy, IIIF manifest rights, or access statements.
- `multi_region_review`: do not collapse into a single national narrative without evidence.
