# Changed files

## Inventory status

`CHANGED_FILE_INVENTORY_STATUS=PASS`

The normal Git/LFS source-to-worktree comparison confirmed the following task-owned inventory and zero protected-path changes.

## Project direction

- `PROJECT_LOG.md`

## Validation route

- `frontend/src/app/trace/context-canvas/page.tsx`
- `frontend/src/app/trace/context-canvas/page.module.css`

## Server-only real-data projection

- `frontend/src/features/trace-v49/context/realdata/project.server.ts`
- `frontend/src/features/trace-v49/context/realdata/source-index.server.ts`
- `frontend/src/features/trace-v49/context/realdata/types.ts`

## Shared Context Canvas core

- `frontend/src/features/trace-v49/context/canvas/ContextCanvas.module.css`
- `frontend/src/features/trace-v49/context/canvas/ContextCanvas.tsx`
- `frontend/src/features/trace-v49/context/canvas/ContextCanvasConnections.tsx`
- `frontend/src/features/trace-v49/context/canvas/ContextCanvasInspector.tsx`
- `frontend/src/features/trace-v49/context/canvas/ContextCanvasNode.tsx`
- `frontend/src/features/trace-v49/context/canvas/ContextEntityPalette.tsx`
- `frontend/src/features/trace-v49/context/canvas/connections.ts`
- `frontend/src/features/trace-v49/context/canvas/display-label.ts`
- `frontend/src/features/trace-v49/context/canvas/export-png.ts`
- `frontend/src/features/trace-v49/context/canvas/fixture.ts`
- `frontend/src/features/trace-v49/context/canvas/index.ts`
- `frontend/src/features/trace-v49/context/canvas/layout.ts`
- `frontend/src/features/trace-v49/context/canvas/reducer.ts`
- `frontend/src/features/trace-v49/context/canvas/types.ts`

## Verification code

- `frontend/scripts/verify-context-canvas-v49.mjs`
- `frontend/scripts/verify-context-canvas-realdata-v49.mjs`

## Research package

- the 12 required files under `docs/research/trace-v49-context-canvas-realdata-round2/`.

## Audit package

- `docs/audits/v49-context-canvas-realdata-round2/00_EXECUTIVE_RECEIPT.md`
- `docs/audits/v49-context-canvas-realdata-round2/01_VALIDATION.md`
- `docs/audits/v49-context-canvas-realdata-round2/02_DATA_RECONCILIATION.md`
- `docs/audits/v49-context-canvas-realdata-round2/03_PROTECTED_BOUNDARY_CHECK.md`
- `docs/audits/v49-context-canvas-realdata-round2/04_CHANGED_FILES.md`
- `docs/audits/v49-context-canvas-realdata-round2/raw/all-object-failures.tsv`
- `docs/audits/v49-context-canvas-realdata-round2/raw/all-object-validation-summary.json`
- `docs/audits/v49-context-canvas-realdata-round2/raw/client-bundle-guard.json`
- `docs/audits/v49-context-canvas-realdata-round2/raw/context-workload-distribution.tsv`
- `docs/audits/v49-context-canvas-realdata-round2/raw/determinism-checksums.json`
- `docs/audits/v49-context-canvas-realdata-round2/raw/export-validation-summary.json`
- `docs/audits/v49-context-canvas-realdata-round2/raw/label-shape-distribution.tsv`
- `docs/audits/v49-context-canvas-realdata-round2/raw/layout-validation-summary.json`
- `docs/audits/v49-context-canvas-realdata-round2/raw/loader-performance-summary.json`
- `docs/audits/v49-context-canvas-realdata-round2/raw/lookup-security-summary.json`
- `docs/audits/v49-context-canvas-realdata-round2/raw/payload-distribution.tsv`
- `docs/audits/v49-context-canvas-realdata-round2/raw/performance-summary.json`
- `docs/audits/v49-context-canvas-realdata-round2/raw/gate-summary.txt`;
- `docs/audits/v49-context-canvas-realdata-round2/raw/protected-boundary.txt`;
- `docs/audits/v49-context-canvas-realdata-round2/MANIFEST.tsv` and `SHA256SUMS.txt` after final review.

## Expected exclusions

The final change set must not contain a database, migration, canonical release input, API contract, Search implementation/index, current `/trace` route, legacy v48 TRACE surface, Spacetime or Exploration implementation, global shell, full-corpus validation dump, candidate-label dump, held row, UUID/URL payload, or dependency manifest/lockfile change.

`MANIFEST.tsv` and `SHA256SUMS.txt` seal the five static documents and 14 sanitized raw evidence files after final review.
