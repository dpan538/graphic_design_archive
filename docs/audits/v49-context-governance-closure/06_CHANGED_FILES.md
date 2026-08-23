# Context governance closure changed-file inventory

`CHANGED_FILE_INVENTORY_STATUS=PASS`

The explicit task diff contains 79 task-owned files after the audit ledgers are added. No database, migration, canonical release, frozen historical API snapshot, Search implementation, Spacetime implementation, Exploration implementation, navigation, or final-design file is present.

## Project direction and additive API documentation

- `PROJECT_LOG.md`
- `docs/api/trace-context-v1-read-api.md`

## Research package

- `docs/research/trace-v49-context-governance-closure/00_EXECUTIVE_DECISION.md`
- `docs/research/trace-v49-context-governance-closure/01_CONTEXT_V1_SCOPE.md`
- `docs/research/trace-v49-context-governance-closure/02_CONTEXT_GOVERNANCE_POLICY.md`
- `docs/research/trace-v49-context-governance-closure/03_CONTEXT_FIELD_DECISION_MATRIX.tsv`
- `docs/research/trace-v49-context-governance-closure/04_CONTEXT_TERM_REGISTRY.tsv`
- `docs/research/trace-v49-context-governance-closure/05_CONTEXT_EXPLANATION_REGISTRY.tsv`
- `docs/research/trace-v49-context-governance-closure/06_MOVEMENT_GOVERNANCE_REGISTER.tsv`
- `docs/research/trace-v49-context-governance-closure/07_CONTEXT_EXCEPTION_REGISTER.tsv`
- `docs/research/trace-v49-context-governance-closure/08_TERM_COLLISION_AND_NORMALIZATION_REVIEW.tsv`
- `docs/research/trace-v49-context-governance-closure/09_CONTEXT_PUBLIC_PROJECTION_SPEC.md`
- `docs/research/trace-v49-context-governance-closure/10_CONTEXT_PUBLIC_API_CONTRACT.md`
- `docs/research/trace-v49-context-governance-closure/11_CONTEXT_CANVAS_GOVERNED_MODE.md`
- `docs/research/trace-v49-context-governance-closure/12_CONTEXT_METHOD_STATEMENT.md`
- `docs/research/trace-v49-context-governance-closure/13_CONTEXT_RED_TEAM.md`
- `docs/research/trace-v49-context-governance-closure/14_CONTEXT_FINAL_VALIDATION.md`
- `docs/research/trace-v49-context-governance-closure/15_CONTEXT_CLOSURE_DECISION.md`

## Governed projection

- `frontend/generated/trace-context-v1/CHECKSUMS.sha256`
- `frontend/generated/trace-context-v1/exception-register.json`
- `frontend/generated/trace-context-v1/explanation-registry.json`
- `frontend/generated/trace-context-v1/governance-policy.json`
- `frontend/generated/trace-context-v1/manifest.json`
- `frontend/generated/trace-context-v1/records.json`
- `frontend/generated/trace-context-v1/terms.json`

## Projection and verification scripts

- `frontend/package.json`
- `frontend/scripts/generate-trace-context-v1.mjs`
- `frontend/scripts/verify-context-api-v1.mjs`
- `frontend/scripts/verify-context-governance-v1.mjs`

## Governed read model and route

- `frontend/src/app/trace/context-canvas/page.tsx`
- `frontend/src/features/trace-v49/context/governed/canvas.ts`
- `frontend/src/features/trace-v49/context/governed/index.server.ts`
- `frontend/src/features/trace-v49/context/governed/reader.server.ts`
- `frontend/src/features/trace-v49/context/governed/types.ts`

## Shared Context Canvas core

- `frontend/src/features/trace-v49/context/canvas/ContextCanvas.module.css`
- `frontend/src/features/trace-v49/context/canvas/ContextCanvas.tsx`
- `frontend/src/features/trace-v49/context/canvas/ContextCanvasConnections.tsx`
- `frontend/src/features/trace-v49/context/canvas/ContextCanvasInspector.tsx`
- `frontend/src/features/trace-v49/context/canvas/ContextCanvasNode.tsx`
- `frontend/src/features/trace-v49/context/canvas/ContextCanvasToolbar.tsx`
- `frontend/src/features/trace-v49/context/canvas/ContextCanvasViewport.tsx`
- `frontend/src/features/trace-v49/context/canvas/ContextEntityPalette.tsx`
- `frontend/src/features/trace-v49/context/canvas/connections.ts`
- `frontend/src/features/trace-v49/context/canvas/export-png.ts`
- `frontend/src/features/trace-v49/context/canvas/index.ts`
- `frontend/src/features/trace-v49/context/canvas/layout.ts`
- `frontend/src/features/trace-v49/context/canvas/model.ts`
- `frontend/src/features/trace-v49/context/canvas/persistence.ts`
- `frontend/src/features/trace-v49/context/canvas/state.ts`
- `frontend/src/features/trace-v49/context/canvas/templates.ts`
- `frontend/src/features/trace-v49/context/canvas/types.ts`

## Read-platform integration

- `frontend/src/lib/read-platform/http-repository.ts`
- `frontend/src/lib/read-platform/repository.ts`
- `frontend/src/lib/read-platform/server/context-repository-provider.ts`
- `frontend/src/lib/read-platform/server/fixture.ts`
- `frontend/src/lib/read-platform/server/postgres-repository.ts`
- `frontend/src/lib/read-platform/server/provider.ts`
- `frontend/src/lib/read-platform/server/read-api-controller.ts`

## Audit package

- `docs/audits/v49-context-governance-closure/00_EXECUTIVE_RECEIPT.md`
- `docs/audits/v49-context-governance-closure/01_GOVERNANCE_VALIDATION.md`
- `docs/audits/v49-context-governance-closure/02_PUBLIC_PROJECTION_VALIDATION.md`
- `docs/audits/v49-context-governance-closure/03_API_VALIDATION.md`
- `docs/audits/v49-context-governance-closure/04_FULL_COHORT_VALIDATION.md`
- `docs/audits/v49-context-governance-closure/05_SECURITY_BOUNDARY.md`
- `docs/audits/v49-context-governance-closure/06_CHANGED_FILES.md`
- `docs/audits/v49-context-governance-closure/raw/CONTEXT_ASSIGNMENT_GOVERNANCE_SUMMARY.tsv`
- `docs/audits/v49-context-governance-closure/raw/CONTEXT_TERM_REGISTRY.tsv`
- `docs/audits/v49-context-governance-closure/raw/SPACETIME_REGION_HANDOFF.tsv`
- `docs/audits/v49-context-governance-closure/raw/context-governance-bundle-guard.json`
- `docs/audits/v49-context-governance-closure/raw/context-governance-census.tsv`
- `docs/audits/v49-context-governance-closure/raw/context-governance-explanation-examples.json`
- `docs/audits/v49-context-governance-closure/raw/context-governance-failures.tsv`
- `docs/audits/v49-context-governance-closure/raw/context-governance-full-cohort-summary.json`
- `docs/audits/v49-context-governance-closure/raw/context-governance-gate-summary.txt`
- `docs/audits/v49-context-governance-closure/raw/context-governance-invariants.tsv`
- `docs/audits/v49-context-governance-closure/raw/context-governance-performance.json`
- `docs/audits/v49-context-governance-closure/raw/context-governance-workload.tsv`
- `docs/audits/v49-context-governance-closure/MANIFEST.tsv`
- `docs/audits/v49-context-governance-closure/SHA256SUMS.txt`

## Protected-path result

```text
DATABASE_FILES_CHANGED=0
CANONICAL_RELEASE_CHANGED=false
SEARCH_FILES_CHANGED=0
SPACETIME_IMPLEMENTATION_FILES_ADDED=0
EXPLORATION_IMPLEMENTATION_FILES_ADDED=0
```

Files are staged by explicit path only. Broad staging commands are prohibited.
