# Commons open authority-weighted expansion resume anchor

Date: 2026-06-13

Purpose:

- Record recovery anchors before resuming
  `scripts/run_commons_open_authority_weighted_expansion_2026_v1.py`.
- The current run is a partial 300-row checkpoint toward the 5,000-row target.
- This manifest records hashes and line counts only; it does not duplicate
  tracked CSV or report files.

Pre-resume files:

| File | Lines | SHA-256 |
| --- | ---: | --- |
| `data/capture_batch_commons_open_authority_weighted_expansion_2026_v1_records.csv` | 301 | `316cfd8e1a5febe609c8d31d27c1ac611c4d98e55450a28a35be248505f47cce` |
| `data/capture_batch_commons_open_authority_weighted_expansion_2026_v1_source_summary.csv` | 277 | `93db973e9f171cb6f777df03dfd1d0b88e61e0734f055f1a3a1d4f59ebcd23c3` |
| `data/commons_open_authority_weighted_expansion_2026_v1_quality.csv` | 74 | `b6bbb59573b21f444ef352b616dae7b29f0536e007069eba0c73612d214ff4d3` |
| `data/commons_open_authority_weighted_expansion_2026_v1_query_state.csv` | 227 | `f79dd9e2d17f2d6c646af377cffec7a6b121a40e300550bc4d6b383e24eb064e` |
| `data/capture_runs/capture_run_manifest_v1.csv` | 44 | `3ebb78b2f7897fec019222de8e99ad60c324e7b75090f0616fca8c61959cd7f3` |
| `docs/capture/COMMONS_OPEN_AUTHORITY_WEIGHTED_EXPANSION_2026_v1.md` | 102 | `ea9638ea19b1cc0942bd85d9a5ef42a7e1d3b4f46c3bcc403ff2301c82ae046b` |

Pre-resume anomaly:

- `data/commons_open_authority_weighted_expansion_2026_v1_query_state.csv`
  contains state rows beyond the currently checkpointed records CSV.
- The runner now ignores completed state entries whose `rows_after` value is
  greater than the saved record count and writes outputs after every query that
  adds rows.

Boundary:

- Resume should fetch Commons metadata only.
- No image binaries, thumbnails, screenshots, raw API payload dumps, cookies,
  browser state, or local image files should be saved.
- IMG03 remains limited to Commons open-license extmetadata.
