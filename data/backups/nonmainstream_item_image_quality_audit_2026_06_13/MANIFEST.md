# Non-mainstream item/image quality audit input backup

Date: 2026-06-13

Purpose:

- Preserve an audit recovery anchor for the two input CSVs used by the
  non-mainstream item/image capture quality audit before producing derived
  triage files.
- The source CSVs were not mutated. Because both inputs are already
  Git-tracked and include raw-like third-party source URLs, this manifest keeps
  hashes and line counts instead of committing duplicate copies of the same
  payload.

Input recovery anchors:

- `data/capture_batch_nonmainstream_item_image_2026_records.csv`
  - Lines: 588
  - SHA-256: `22fcd9689e533eacdbc9f1ffd8a37ee09c4ae0ee6a0a27a45e2d0d78058638d7`
- `data/capture_batch_nonmainstream_item_image_2026_source_summary.csv`
  - Lines: 582
  - SHA-256: `802cd9d8f963ef820fda49598297fbf97d4e1fc2c2ee3d5381a3d15db5d6d64a`

Boundary:

- No image binaries were downloaded.
- No IMG01/IMG03 rights state was assigned.
- No generated public surface or frontend payload was rebuilt.
