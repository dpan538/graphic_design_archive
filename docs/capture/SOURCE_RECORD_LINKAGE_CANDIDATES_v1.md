# Source Record Linkage Candidates v1

Date: 2026-06-01

Scope: capture records before final surface assignment. This file proposes grouping and de-duplication candidates; it does not merge records.

## Summary

- Capture rows scanned: 8035
- Linkage groups: 488
- Linkage memberships: 2566

## Linkage Types

- `same_collection_medium_place_decade`: 163
- `same_series_stem_collection`: 96
- `same_title_within_source`: 93
- `same_source_record_url`: 55
- `same_source_identifier`: 46
- `same_image_url`: 35

## Relation Labels

- `related_but_not_same`: 163
- `same_entity_confirmed`: 101
- `same_work_series_or_campaign`: 96
- `possibly_same_as`: 93
- `same_visual_item_different_capture`: 34
- `possible_placeholder_or_loader_reuse`: 1

## Recommended Actions

- `canonical_main_with_child_text_appendix`: 218
- `support_packet_or_compound_sheet_candidate`: 134
- `deduplicate_or_merge_source_records`: 101
- `review_duplicate_image_before_public_rebuild`: 35

## Coverage Gaps

- `coverage_ready`: 322
- `needs_image`: 101
- `needs_text`: 90
- `needs_rights_evidence`: 62
- `cross_period_review`: 28
- `multi_place_review`: 6

## High-Value Review Groups

- SRLG0123 | same_collection_medium_place_decade | 5 members | canonical_main_with_child_text_appendix | needs_image;needs_text;needs_rights_evidence | The Hour Approaches
- SRLG0153 | same_collection_medium_place_decade | 4 members | canonical_main_with_child_text_appendix | needs_image;needs_text;needs_rights_evidence | No. 2 Spring
- SRLG0152 | same_collection_medium_place_decade | 4 members | canonical_main_with_child_text_appendix | needs_image;needs_text;needs_rights_evidence | Keep These Off the U.S.A.
- SRLG0251 | same_image_url | 2 members | review_duplicate_image_before_public_rebuild | needs_image;needs_text;needs_rights_evidence | 1952 Exhibition Poster
- SRLG0252 | same_image_url | 2 members | review_duplicate_image_before_public_rebuild | needs_image;needs_text;needs_rights_evidence | An Attempt Using Unfit Means
- SRLG0257 | same_image_url | 2 members | review_duplicate_image_before_public_rebuild | needs_image;needs_text;needs_rights_evidence | Untitled
- SRLG0258 | same_image_url | 2 members | review_duplicate_image_before_public_rebuild | needs_image;needs_text;needs_rights_evidence | No. 2 Spring
- SRLG0260 | same_series_stem_collection | 2 members | support_packet_or_compound_sheet_candidate | needs_image;needs_text;needs_rights_evidence | An Attempt Using Unfit Means
- SRLG0262 | same_series_stem_collection | 2 members | support_packet_or_compound_sheet_candidate | needs_image;needs_text;needs_rights_evidence | 1952 Exhibition Poster
- SRLG0326 | same_source_identifier | 2 members | deduplicate_or_merge_source_records | needs_image;needs_text;needs_rights_evidence | 1952 Exhibition Poster
- SRLG0327 | same_source_identifier | 2 members | deduplicate_or_merge_source_records | needs_image;needs_text;needs_rights_evidence | An Attempt Using Unfit Means
- SRLG0329 | same_source_identifier | 2 members | deduplicate_or_merge_source_records | needs_image;needs_text;needs_rights_evidence | Untitled
- SRLG0337 | same_source_identifier | 2 members | deduplicate_or_merge_source_records | needs_image;needs_text;needs_rights_evidence | No. 2 Spring
- SRLG0397 | same_source_record_url | 2 members | deduplicate_or_merge_source_records | needs_image;needs_text;needs_rights_evidence | 1952 Exhibition Poster
- SRLG0398 | same_source_record_url | 2 members | deduplicate_or_merge_source_records | needs_image;needs_text;needs_rights_evidence | An Attempt Using Unfit Means
- SRLG0400 | same_source_record_url | 2 members | deduplicate_or_merge_source_records | needs_image;needs_text;needs_rights_evidence | Untitled
- SRLG0408 | same_source_record_url | 2 members | deduplicate_or_merge_source_records | needs_image;needs_text;needs_rights_evidence | No. 2 Spring
- SRLG0423 | same_title_within_source | 2 members | support_packet_or_compound_sheet_candidate | needs_image;needs_text;needs_rights_evidence | 1952 Exhibition Poster
- SRLG0424 | same_title_within_source | 2 members | support_packet_or_compound_sheet_candidate | needs_image;needs_text;needs_rights_evidence | An Attempt Using Unfit Means
- SRLG0430 | same_title_within_source | 2 members | support_packet_or_compound_sheet_candidate | needs_image;needs_text;needs_rights_evidence | No. 2 Spring
- SRLG0435 | same_title_within_source | 2 members | support_packet_or_compound_sheet_candidate | needs_image;needs_text;needs_rights_evidence | Untitled
- SRLG0247 | same_image_url | 2 members | review_duplicate_image_before_public_rebuild | needs_image;needs_text;needs_rights_evidence | The Modern Poster
- SRLG0250 | same_image_url | 2 members | review_duplicate_image_before_public_rebuild | needs_image;needs_text;needs_rights_evidence | Our One-Thousandth Blow
- SRLG0253 | same_image_url | 2 members | review_duplicate_image_before_public_rebuild | needs_image;needs_text;needs_rights_evidence | This Is the Enemy
- SRLG0254 | same_image_url | 2 members | review_duplicate_image_before_public_rebuild | needs_image;needs_text;needs_rights_evidence | Buy a Little Present for the Kaiser

## Interpretation

- `same_entity_confirmed` can support deduplication or one main sheet with source/register children.
- `same_visual_item_different_capture` must be checked before rebuild because it may be a true repeated visual item or an accidental repeated thumbnail.
- `same_work_series_or_campaign` is a good target for compound sheets, text pages, cards, and appendix grouping.
- Weak collection/medium/place clusters are planning aids, not evidence that records describe the same work.
