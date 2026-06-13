# Commons Open Source Cleaning Audit 2026 v1

Scope: recent Commons open-source expansion batches only. This audit generates review queues and does not modify source records.

## Summary

- Records audited: 11051
- Release-ready records: 11039 (99.89% if total else 0)
- Duplicate/review records: 12
- Duplicate source keys inside new batches: 6
- Duplicate image URLs inside new batches: 3

## Status Distribution

- release_ready: 11039
- review_weak_graphic_evidence: 6
- quarantine_duplicate_review: 6

## Authority Distribution

- commons_open_file_with_extra_source: 6564
- institutional_or_education_context: 2276
- structured_catalog_source_link: 2156
- commons_platform_only: 55

## Object Family Distribution

- postage_stamp: 5590
- poster: 1971
- advertising: 1258
- label_packaging: 947
- film_poster: 489
- book_cover: 368
- brochure_pamphlet: 108
- political_poster: 101
- magazine_cover: 97
- typography_identity: 75
- travel_poster: 47

## Period Distribution

- 2000_2026: 3732
- pre_1940: 3509
- 1940_1970: 2223
- 1970_2000: 1587

## Top Review Reasons

- platform_only_authority: 55
- weak_graphic_or_event_photo_signal: 6
- duplicate_source_identifier_or_url: 6
- duplicate_image_url: 6

## Boundary

- This audit does not download images or raw API payloads.
- It does not create a cleaned `*_records.csv`; this avoids accidental double-counting by rebuild scripts.
- `release_ready` means the row passes automated metadata, rights, duplicate, object-family, and authority-shape checks. It is still a source-linked Commons record and remains reviewable.
