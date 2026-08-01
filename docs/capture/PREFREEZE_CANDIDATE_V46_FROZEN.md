# Prefreeze candidate v46 — frozen design-validation baseline

## State

- Freeze status: **frozen for design and interaction validation**
- Release status: **not a final public-release dataset**
- Active objects: 15,921
- Count distance to the 20,000 target: 4,079
- Chronology: no missing years from 1800 through 2029
- Active unresolved geography: 0
- Active uncertain authority: 0
- Accepted TRACE: 15,921 / 15,921
- Historical `influenced_by` evidence edges: 0
- Review layers, isolated from active count: 74 object-geography records and 1 duplicate-representation record

## Exact canonical payload

- `generated/public_surfaces_prefreeze_candidate_v46.json`
- SHA-256: `42515bce22514532a1651b5236100f6660a9f9ff12e9f3b2f889eb85d4ac182b`
- Candidate payload size: 190,039,480 bytes
- `data/prefreeze_candidate_v46.sqlite` is included as a separate LFS frozen query snapshot. It is not canonical data and cannot supersede the candidate JSON.

## Freeze guarantees

1. The candidate, review holds, TRACE topology audit, search gate, 200-object audit, and atlas aggregates are enumerated in `generated/prefreeze_candidate_v46_transfer_manifest_draft.json`.
2. The manifest contains the selected reproducibility, candidate, frozen-query, review, and validation files. The candidate JSON and frozen SQLite snapshot are the only LFS-classified files.
3. Raw capture caches, older candidate versions, design screenshots, and unrelated working-tree edits are excluded.
4. This freeze is a stable data reference for visual and interaction work. No design task may mutate, promote, or merge candidate/review data without opening a new data iteration and regenerating every gate.

## Transfer rule

The main-repository transfer is staged as A (reproducibility), B (LFS candidate payload), C (LFS frozen search database), D (review and validation), then E (clean retrieval receipt). Each completed batch must be pushed, fetched back, and SHA-256 verified before the next begins. A batch failure stops the sequence; no substitute file or broad directory upload is permitted.
