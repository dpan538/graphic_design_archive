# Commons Open Source Cleaning Audit 2026 v1

Scope: recent Commons open-source expansion batches only. This audit generates review queues and does not modify source records.

## Summary

- Records audited: 6286
- Release-ready records: 6286 (100.00% if total else 0)
- Duplicate/review records: 0
- Duplicate source keys inside new batches: 0
- Duplicate image URLs inside new batches: 0

## Status Distribution

- release_ready: 6286

## Authority Distribution

- commons_open_file_with_extra_source: 3675
- structured_catalog_source_link: 1567
- institutional_or_education_context: 1023
- commons_platform_only: 21

## Object Family Distribution

- postage_stamp: 4167
- poster: 576
- advertising: 478
- film_poster: 403
- book_cover: 229
- label_packaging: 136
- magazine_cover: 91
- political_poster: 67
- typography_identity: 66
- travel_poster: 42
- brochure_pamphlet: 31

## Period Distribution

- 2000_2026: 2249
- pre_1940: 1647
- 1940_1970: 1359
- 1970_2000: 1031

## Top Review Reasons

- platform_only_authority: 21

## Boundary

- This audit does not download images or raw API payloads.
- It does not create a cleaned `*_records.csv`; this avoids accidental double-counting by rebuild scripts.
- `release_ready` means the row passes automated metadata, rights, duplicate, object-family, and authority-shape checks. It is still a source-linked Commons record and remains reviewable.
