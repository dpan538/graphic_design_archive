# Commons Open Controlled Topoff Backup 2026-06-13

Purpose: preserve the controlled-expansion state before using it as a short
topoff lane for the long Commons open-source capture round.

Baseline before topoff:

- `data/capture_batch_commons_open_controlled_expansion_2026_v1_records.csv`
  - rows: 925
  - sha256 prefix: `65442860995db372`
- `data/capture_batch_commons_open_controlled_expansion_2026_v1_source_summary.csv`
  - rows: 925
  - sha256 prefix: `1985a353ebe3c629`
- `data/commons_open_controlled_expansion_2026_v1_quality.csv`
  - rows: 85
  - sha256 prefix: `5a484cf83db6855a`
- `data/commons_open_controlled_expansion_2026_v1_query_state.csv`
  - rows: 466
  - sha256 prefix: `ec16efa6f384018d`
- `docs/capture/COMMONS_OPEN_CONTROLLED_EXPANSION_2026_v1.md`
  - lines: 115
  - sha256 prefix: `8c8393e45ef08a07`

Boundary notes:

- Backup copies are source metadata/report files only.
- No image binaries, screenshots, raw API payloads, cookies, browser sessions,
  or local downloaded image files are included.
- Public surface rebuild is intentionally deferred until the final release-gate
  check for this long run.
