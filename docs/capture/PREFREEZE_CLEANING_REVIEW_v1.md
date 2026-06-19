# Prefreeze Cleaning Review v1

Scope: remaining source-visible and event/photo/context-image review queues for the pre-freeze candidate. No raw capture rows, official payloads, rights states, or image files were changed.

## Summary

- source_visible_gap_rows: 181 (IMG00/IMG04 rows requiring source-visible review.)
- context_image_review_rows: 2149 (Event/photo/context-image review rows.)
- source_gap_class:text_only_item_or_collection: 96 (Source-visible gap class.)
- source_gap_class:image_missing_or_parser_gap: 41 (Source-visible gap class.)
- source_gap_class:source_registry_context_page: 37 (Source-visible gap class.)
- source_gap_class:registry_or_archive_landing_page: 7 (Source-visible gap class.)
- context_class:weak_context_or_profile_image: 1899 (Context/image review class.)
- context_class:philatelic_or_stamp_like: 208 (Context/image review class.)
- context_class:event_or_photo_language: 42 (Context/image review class.)
- context_action:card_support_candidate: 1899 (Suggested event/context handling.)
- context_action:card_support_review: 208 (Suggested event/context handling.)
- context_action:manual_keep_or_card_review: 42 (Suggested event/context handling.)

## Reading

- Source-visible gap rows are mostly IMG04/IMG00 records; they should be recaptured, kept as text/context, or demoted to support rather than hidden to improve a metric.
- Event/photo/context-image rows are P1 review candidates. `manual_keep_or_card_review` means design language exists and the row should not be bulk-excluded.
- This audit does not perform image-state or rights upgrades.
