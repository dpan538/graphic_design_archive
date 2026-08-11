# v49 Phase 1D — Reversible runtime-cleanup executive receipt

- Cleanup baseline: `f75ded85000749beb4735fbbddcce99e9395b0b2`
- Worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Branch: `refactor/v49-data-platform`
- Result: **PASS_STATIC_SCOPE**
- Rights/machine decision input: immutable first-stage commit; cleanup did not alter its gate
- PostgreSQL/API/data/frozen-asset implementation: **NOT PERFORMED**

## Outcome

The active browser-local Qwen assistant was removed without deleting deterministic archive Search. The retired route, event, memory, retrieval, adapter, assistant UI and dedicated CSS no longer exist in production source. `@huggingface/transformers` and its now-unreachable model subtree were removed with one successful package-lock-only, ignore-scripts update. Retained package versions, resolved URLs and integrity values did not drift.

Seven historical probe runners/results were moved byte-identically into a read-only, non-authoritative archive. Only the two dormant high-cardinality static-param helpers were removed; low-cardinality folder-type generation and the A4 visual system remain. The 60 QA images are byte-identical, with a new evidence-governance README/schema. The sole approved ignored file, `docs/.DS_Store`, was deleted after exact size/hash/status verification.

## Measured gates

```text
AI_RUNTIME_RETIRED=true
QWEN_RUNTIME_IMPORTS=0
ACTIVE_ASSISTANT_ROUTES=0
MODEL_RUNTIME_PRODUCTION_IMPORTS=0
BULK_ROUTE_REGRESSION_BLOCKED=true
DORMANT_BULK_ROUTE_GENERATORS=0
DETERMINISTIC_SEARCH_PRESERVED=true
A4_VISUAL_COMPONENTS_PRESERVED=true
ARCHIVED_PROBE_FILE_COUNT=7
ARCHIVED_PROBE_BYTES_PRESERVED=true
QA_IMAGE_COUNT=60
QA_IMAGES_UNCHANGED=true
SAFE_DELETE_EXECUTED=docs/.DS_Store
OTHER_UNTRACKED_DELETED=0
DEFERRED_CLEANUP_COUNT=9
TSC_NOT_RUN=toolchain_absent
CLEANUP_STAGE=PASS_STATIC_SCOPE
```

`DEFERRED_CLEANUP_COUNT` counts nine non-overlapping action-ledger scopes, not a sum of their overlapping file populations. They are enumerated in `01_DEFERRED_CLEANUP_LEDGER.md`.

## Dependency result

| Measure | Result |
|---|---:|
| Baseline/current lock package entries | 218 / 176 |
| Removed package entries | 42 |
| Added package entries | 0 |
| Retained package `version`/`resolved`/`integrity` drift | 0 |
| Transformers refs in package/lock | 0 / 0 |
| `node_modules` created | 0 |

The initial sandboxed package-lock command failed with `EPERM` before writing. The identical escalated command then completed once, with `--package-lock-only --ignore-scripts --no-audit --no-fund`; no dependency tree or lifecycle script was installed or executed.

## Verification

C1 and C2 supplied separate implementation receipts. C3, which did not participate in either patch, implemented a pure-standard-library, read-only verifier and returned final exit 0 with 38 passed checks and zero failures. Its first two orchestration attempts are disclosed in its receipt and are not represented as PASS. The final auditable result verifies source references, package identity, deterministic Search, route cardinality, A4 hashes, archived-byte parity, QA fingerprint, safe-delete absence, changed-file allowlist, frozen/data exclusion, protected-main fingerprints and `git diff --check`.

No TypeScript compiler exists in the isolated worktree or bundled runtime. The permitted bounded TypeScript check was therefore not run; no `npx`, dependency install or second lock update was used to manufacture the toolchain. This receipt makes no build, browser, layout or runtime-interaction claim.

## Explicitly not cleaned

The 90.9 MB legacy payload placements, 35 direct data-coupling files, `/contents`, Folder Reader, Search/TRACE assets, ten duplicate QA blobs, 186 effective `HOLD_UNKNOWN` paths, 10,937 protected-main untracked paths, all frozen v48 assets, and every item without proved recovery remain untouched.

## Actions explicitly not performed

No Next dev/build/start, browser, screenshot, TypeScript compile, npm dependency install, PostgreSQL, Docker, migration, API/adapter implementation, data import/export/regeneration, image download, full frontend coupling cleanup, frozen/QA-image/dirty-main mutation, PR, merge, deploy, force operation or destructive broad cleanup was performed.
