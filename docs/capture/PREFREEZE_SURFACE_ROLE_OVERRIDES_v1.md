# Prefreeze Surface Role Overrides v1

Scope: reviewable card/subsheet demotion layer for candidate-only rebuilds. It preserves source visibility and rights evidence while reducing unsupported main-sheet claims.

## Summary

- context_review_rows: 2149 (Input context/event/photo review rows.)
- source_gap_review_rows: 181 (Input source-visible gap review rows.)
- decision_rows: 2330 (Total role decisions emitted.)
- override_rows: 2247 (Rows eligible for candidate rebuild role override.)
- decision:apply_card_demotion: 1943 (Decision type distribution.)
- decision:apply_subsheet_demotion: 304 (Decision type distribution.)
- decision:manual_review_only: 42 (Decision type distribution.)
- decision:manual_recapture_or_review: 41 (Decision type distribution.)
- role:card: 1943 (Surface role override distribution.)
- role:support_packet_appendix_text: 304 (Surface role override distribution.)
- review_class:weak_context_or_profile_image: 1899 (Review class distribution.)
- review_class:philatelic_or_stamp_like: 208 (Review class distribution.)
- review_class:text_only_item_or_collection: 96 (Review class distribution.)
- review_class:event_or_photo_language: 42 (Review class distribution.)
- review_class:image_missing_or_parser_gap: 41 (Review class distribution.)
- review_class:source_registry_context_page: 37 (Review class distribution.)
- review_class:registry_or_archive_landing_page: 7 (Review class distribution.)

## Guardrails

- No capture rows were deleted or edited.
- No image files were downloaded.
- IMG01/IMG03 rights states were not upgraded.
- Manual review classes are not emitted as overrides.
