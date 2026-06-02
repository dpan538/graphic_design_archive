# Source Record Linkage Candidates v1

Date: 2026-06-01

Scope: capture records before final surface assignment. This file proposes grouping and de-duplication candidates; it does not merge records.

## Summary

- Capture rows scanned: 1378
- Linkage groups: 321
- Linkage memberships: 1076

## Linkage Types

- `same_series_stem_collection`: 85
- `same_title_within_source`: 81
- `same_source_record_url`: 46
- `same_source_identifier`: 41
- `same_collection_medium_place_decade`: 35
- `same_image_url`: 33

## Relation Labels

- `same_entity_confirmed`: 87
- `same_work_series_or_campaign`: 85
- `possibly_same_as`: 81
- `related_but_not_same`: 35
- `same_visual_item_different_capture`: 32
- `possible_placeholder_or_loader_reuse`: 1

## Recommended Actions

- `support_packet_or_compound_sheet_candidate`: 122
- `deduplicate_or_merge_source_records`: 87
- `canonical_main_with_child_text_appendix`: 79
- `review_duplicate_image_before_public_rebuild`: 33

## Coverage Gaps

- `coverage_ready`: 180
- `needs_image`: 96
- `needs_text`: 90
- `needs_rights_evidence`: 62
- `cross_period_review`: 12
- `multi_place_review`: 2

## High-Value Review Groups

- SRLG0036 | same_collection_medium_place_decade | 5 members | canonical_main_with_child_text_appendix | needs_image;needs_text;needs_rights_evidence | The Hour Approaches
- SRLG0046 | same_collection_medium_place_decade | 4 members | canonical_main_with_child_text_appendix | needs_image;needs_text;needs_rights_evidence | No. 2 Spring
- SRLG0045 | same_collection_medium_place_decade | 4 members | canonical_main_with_child_text_appendix | needs_image;needs_text;needs_rights_evidence | Keep These Off the U.S.A.
- SRLG0110 | same_image_url | 2 members | review_duplicate_image_before_public_rebuild | needs_image;needs_text;needs_rights_evidence | 1952 Exhibition Poster
- SRLG0111 | same_image_url | 2 members | review_duplicate_image_before_public_rebuild | needs_image;needs_text;needs_rights_evidence | An Attempt Using Unfit Means
- SRLG0116 | same_image_url | 2 members | review_duplicate_image_before_public_rebuild | needs_image;needs_text;needs_rights_evidence | Untitled
- SRLG0117 | same_image_url | 2 members | review_duplicate_image_before_public_rebuild | needs_image;needs_text;needs_rights_evidence | No. 2 Spring
- SRLG0118 | same_series_stem_collection | 2 members | support_packet_or_compound_sheet_candidate | needs_image;needs_text;needs_rights_evidence | An Attempt Using Unfit Means
- SRLG0120 | same_series_stem_collection | 2 members | support_packet_or_compound_sheet_candidate | needs_image;needs_text;needs_rights_evidence | 1952 Exhibition Poster
- SRLG0178 | same_source_identifier | 2 members | deduplicate_or_merge_source_records | needs_image;needs_text;needs_rights_evidence | 1952 Exhibition Poster
- SRLG0179 | same_source_identifier | 2 members | deduplicate_or_merge_source_records | needs_image;needs_text;needs_rights_evidence | An Attempt Using Unfit Means
- SRLG0181 | same_source_identifier | 2 members | deduplicate_or_merge_source_records | needs_image;needs_text;needs_rights_evidence | Untitled
- SRLG0189 | same_source_identifier | 2 members | deduplicate_or_merge_source_records | needs_image;needs_text;needs_rights_evidence | No. 2 Spring
- SRLG0238 | same_source_record_url | 2 members | deduplicate_or_merge_source_records | needs_image;needs_text;needs_rights_evidence | 1952 Exhibition Poster
- SRLG0239 | same_source_record_url | 2 members | deduplicate_or_merge_source_records | needs_image;needs_text;needs_rights_evidence | An Attempt Using Unfit Means
- SRLG0241 | same_source_record_url | 2 members | deduplicate_or_merge_source_records | needs_image;needs_text;needs_rights_evidence | Untitled
- SRLG0249 | same_source_record_url | 2 members | deduplicate_or_merge_source_records | needs_image;needs_text;needs_rights_evidence | No. 2 Spring
- SRLG0262 | same_title_within_source | 2 members | support_packet_or_compound_sheet_candidate | needs_image;needs_text;needs_rights_evidence | 1952 Exhibition Poster
- SRLG0263 | same_title_within_source | 2 members | support_packet_or_compound_sheet_candidate | needs_image;needs_text;needs_rights_evidence | An Attempt Using Unfit Means
- SRLG0269 | same_title_within_source | 2 members | support_packet_or_compound_sheet_candidate | needs_image;needs_text;needs_rights_evidence | No. 2 Spring
- SRLG0274 | same_title_within_source | 2 members | support_packet_or_compound_sheet_candidate | needs_image;needs_text;needs_rights_evidence | Untitled
- SRLG0106 | same_image_url | 2 members | review_duplicate_image_before_public_rebuild | needs_image;needs_text;needs_rights_evidence | The Modern Poster
- SRLG0109 | same_image_url | 2 members | review_duplicate_image_before_public_rebuild | needs_image;needs_text;needs_rights_evidence | Our One-Thousandth Blow
- SRLG0112 | same_image_url | 2 members | review_duplicate_image_before_public_rebuild | needs_image;needs_text;needs_rights_evidence | This Is the Enemy
- SRLG0113 | same_image_url | 2 members | review_duplicate_image_before_public_rebuild | needs_image;needs_text;needs_rights_evidence | Buy a Little Present for the Kaiser

## Interpretation

- `same_entity_confirmed` can support deduplication or one main sheet with source/register children.
- `same_visual_item_different_capture` must be checked before rebuild because it may be a true repeated visual item or an accidental repeated thumbnail.
- `same_work_series_or_campaign` is a good target for compound sheets, text pages, cards, and appendix grouping.
- Weak collection/medium/place clusters are planning aids, not evidence that records describe the same work.
