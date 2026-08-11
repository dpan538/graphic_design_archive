# Runtime-cleanup gate receipt

- Baseline commit: `f75ded85000749beb4735fbbddcce99e9395b0b2`
- C1 implementation receipt: **PASS_STATIC_SCOPE**
- C2 archive/bulk/QA/safe-delete receipt: **PASS**
- C3 independent verifier: **PASS_STATIC_SCOPE**
- Final verifier result: 38 checks passed / 0 failed

## Required cleanup gates

```text
QWEN_RUNTIME_IMPORTS=0
ACTIVE_ASSISTANT_ROUTES=0
MODEL_RUNTIME_PRODUCTION_IMPORTS=0
DORMANT_BULK_ROUTE_GENERATORS=0
DETERMINISTIC_SEARCH_PRESERVED=true
A4_VISUAL_COMPONENTS_PRESERVED=true
AI_RUNTIME_RETIRED=true
BULK_ROUTE_REGRESSION_BLOCKED=true
SAFE_DELETE_EXECUTED=docs/.DS_Store
DEFERRED_CLEANUP_COUNT=9
CLEANUP_GATE=PASS_STATIC_SCOPE
```

`BULK_ROUTE_REGRESSION_BLOCKED=true` means the committed deterministic verifier fails if `allFolderParams` or `allSurfaceParams` returns. It does not claim that `/contents`, Folder Reader, active low-cardinality generation or all static-data producers have been refactored; those remain explicit deferred scopes.

## Preservation gates

| Boundary | Evidence | Result |
|---|---|---|
| Deterministic Search | one client import, one `searchArchiveSurfaces(trimmed, 30)` call, full `/search` route/link; client and full route baseline blobs preserved where required | PASS |
| A4 system | four locked component/pagination hashes equal baseline | PASS |
| Historical AI evidence | 7/7 archived files match original baseline bytes/hashes; 4/4 JSON parse | PASS |
| QA images | 60 tracked/filesystem images; exact path+content fingerprint; image diff 0 | PASS |
| Frozen/data boundary | frozen assets and non-probe generated/data/Search/TRACE/QA-image paths absent from cleanup diff | PASS |
| Protected dirty main | HEAD, tracked/untracked fingerprints, counts and staged=0 equal baseline | PASS |
| Dependency graph | root-lock parity; retained identity drift 0; model refs 0 | PASS |
| Residual process | task-owned npm/Next/tsc/Qwen/generator processes 0 | PASS |

## TypeScript boundary

```text
TSC_NOT_RUN=toolchain_absent
NEXT_BUILD_RUN=false
NEXT_DEV_RUN=false
BROWSER_RUN=false
```

The user allowed, but did not require, one bounded TypeScript run. Neither a system `tsc`, a bundled TypeScript runtime nor `frontend/node_modules/.bin/tsc` exists. Installing a compiler would have violated the no-install boundary, so no compile result is claimed. Static source, import, package, route and hash gates remain independently auditable.

## Reproduction

```text
python3 scripts/verify_v49_runtime_cleanup.py
git diff --check
```

The verifier is pure Python standard library, network-free, read-only and stdout-only. Its internal `ps` call may report `EXTERNAL_REQUIRED` in a sandbox; the process gate then requires the separately sanitized process receipt rather than silently passing.

## Non-actions

No cleanup outside the explicit C1/C2 scopes was performed. In particular, no frozen asset, QA image, legacy payload, Search/TRACE asset, direct data consumer/producer, `/contents`, Folder Reader, protected-main path or `HOLD_UNKNOWN` path was deleted or rewritten.
