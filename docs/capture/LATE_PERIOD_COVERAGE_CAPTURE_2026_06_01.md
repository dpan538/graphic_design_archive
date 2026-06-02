# Late Period Coverage Capture

Date: 2026-06-01

Scope: 1970-2026

Purpose:

- Begin the late-period coverage pass after the first group-candidate audit.
- Prioritize structural coverage across region/theme/medium/movement before
  fine enrichment.
- Add source-hosted image evidence and text/discourse records for contemporary
  poster, periodical, Indigenous, Aotearoa/Pacific, activist, web/interface, and
  self-published print cultures.

## Files

- Script: `scripts/run_late_period_coverage_capture_1970_2026.py`
- Records: `data/capture_batch_late_period_coverage_1970_2026_records.csv`
- Source summary:
  `data/capture_batch_late_period_coverage_1970_2026_source_summary.csv`
- Raw payload folder:
  `data/capture_batch_late_period_coverage_1970_2026_raw/`

## Capture Result

- Captured rows: 104
- Sources:
  - Internet Archive / text and periodical collections: 46
  - Te Papa Collections Online: 24
  - NAIDOC Poster Gallery: 23
  - Wikimedia Commons: 11
- Image states:
  - `IMG02`: 92
  - `IMG03`: 11
  - `IMG00`: 1
- Period split:
  - 1970-2000: 24
  - 2001-2026: 80

## Source Policy

- `IMG02` means source-hosted image/viewer evidence, not local ownership.
- `IMG03` is used only when the source layer exposes open-license metadata.
- `IMG00` remains a valid record state when source evidence exists but image
  display is withheld.

## Integrated Payload Result

After rebuilding public surfaces:

- Input rows after dedupe: 1196
- Public surfaces: 1095
- Folder views: 45
- Image-ready surfaces: 1002 / 1095, or 92%
- Image states:
  - `IMG03`: 394
  - `IMG02`: 571
  - `IMG01`: 37
  - `IMG00`: 40
  - `IMG04`: 53

Period image-ready audit:

- 1830-1929: 327 / 347, or 94.2%
- 1930-1970: 478 / 548, or 87.2%
- 1971-2000: 111 / 114, or 97.4%
- 2001-2026: 86 / 86, or 100.0%

Important reading:

- The period image-ready percentage is a renderability metric. It does not mean
  every image is open, locally reusable, or fully reviewed. Most late-period
  image records are source-hosted `IMG02` and must keep source return visible.

## Group Refresh

The surface grouping audit was regenerated after this capture:

- Candidate groups: 257
- Candidate memberships: 1773
- `coverage_ready`: 168
- `needs_text`: 34
- `needs_rights`: 25
- `needs_image`: 16

## Remaining Launch Gate

`scripts/audit_image_release_gate.py` reports:

- Overall image-ready coverage: 91.51%
- Minimum launch gate: 95%
- Main blockers are older/midcentury `IMG00`/`IMG04` records from AIC, V&A,
  Met, LoC, Getty, and Wellcome.

This means the late-period capture improved contemporary coverage, but the
global launch gate is still blocked by earlier and midcentury records.
