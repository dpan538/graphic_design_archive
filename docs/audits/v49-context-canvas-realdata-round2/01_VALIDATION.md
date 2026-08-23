# Validation

All commands ran without a development server, localhost listener, browser automation, or screenshot workflow.

| Gate | Command or evidence | Result |
| --- | --- | --- |
| Clean install | `npm ci` | `PASS` |
| TypeScript | `npx tsc --noEmit --pretty false` | `PASS` |
| Runtime TypeScript | `npm run typecheck:runtime` | `PASS` |
| Synthetic Context Canvas | `node scripts/verify-context-canvas-v49.mjs` | `PASS` — 36 checks, 18 invariants |
| Real-data all-object validator | isolated `node scripts/verify-context-canvas-realdata-v49.mjs` | `PASS` — 7,995 objects, 31,980 template cases, zero failed objects, 18 invariants |
| Full-data determinism | two complete internal source-index/projection passes | `PASS` — every canonical checksum pair matched |
| TRACE preprogram | `node scripts/verify-trace-v49-preprogram.mjs` | `PASS` — 19 checks, 16 invariants |
| Search index | `npm run verify:search-v49-index` | `PASS` — 7,995 public documents, 7,928 held, frozen SHA unchanged |
| Search regression | `npm run test:search-v49` | `PASS` — 14 checks, 7,995 documents |
| Read platform/API | `npm run test:read-platform` and API checks | `PASS` |
| Page-by-key runtime | `node scripts/verify-page-by-key-module-contract.mjs` | `PASS` |
| Production build, attempt 1 | `npm run build` | transient late generated-output race after compilation and 47-page generation; `.next/export/500.html` rename returned `ENOENT` |
| Production build, attempt 2 | immediate clean retry of `npm run build` | `PASS` — 47 pages; `/trace/context-canvas` dynamic |
| Final sandboxed build attempt | `npm run build` with restricted network | environment-only Google Fonts `ENOTFOUND` |
| Final build acceptance | authorized network retry of `npm run build` | `PASS` — 47 pages; dynamic `/trace/context-canvas`, 14.5 kB / 117 kB first load |
| Client source/bundle guard | real-data verifier and production artifacts | `PASS` — 73 reachable client modules and 47 bundle files; zero forbidden matches |
| Patch hygiene | `git diff --check` | `PASS` |
| Protected paths | normal Git/LFS source-to-worktree comparison | `PASS` — zero protected changes |

Attempt 1 reached successful compilation and all 47-page generation before the late rename failure and is recorded transparently as a transient generated-output race. The restricted-network fonts failure is an environment condition. The authorized network retry is the final production-build acceptance result.

## Full-data verifier result

```text
OBJECTS_TESTED=7995
TEMPLATE_CASES=31980
FAILED_OBJECTS=0
HELD_LOOKUPS=7928
HELD_EXPOSED=0
REALDATA_INVARIANTS=18/18
SOURCE_MANIFEST_SHA256=c07de2b6531f5f17cd31f705b6e42443277bf837ce9e13225ae684001da17363
REAL_CONTEXT_REBUILD_DETERMINISTIC=true
REAL_CONTEXT_CHECKSUM_MATCH=true
REAL_CONTEXT_AGGREGATE_SHA256=499624075b99745c1eb95a8d6c2c1438eb7e74ca63222227b8bfb87fdaf38d76
EXPORT_PREPARATION_SHA256=3c88449337f52ece7be2b8bf282812fb2402b020f72ced7984a9a7c03ab410b9
ISOLATED_VERIFIER_EVIDENCE_FILE_COUNT=12
ISOLATED_VERIFIER_EVIDENCE_SHA256=9d4a3d1f5a739269a7dc6abfb0711717d75d30dc81ced4b03aa6d2cb63f03ca0
```

## Failure and security counters

```text
ENTITY_ID_COLLISION_COUNT=0
CONNECTION_ID_COLLISION_COUNT=0
DANGLING_CONNECTION_COUNT=0
AUTO_LAYOUT_COLLISION_COUNT=0
NODE_OUTSIDE_BOUNDS_COUNT=0
NONFINITE_POSITION_COUNT=0
INVALID_CONNECTOR_COUNT=0
ACCESSIBLE_ROW_MISMATCH_COUNT=0
DUPLICATE_ACCESSIBLE_ROW_COUNT=0
PERSISTENCE_KEY_COLLISION_COUNT=0
RECORD_SWITCH_STATE_LEAK_COUNT=0
EXPORT_PREPARATION_FAILURE_COUNT=0
INTERNAL_UUID_EXPOSURE_COUNT=0
NON_PROPOSED_CANDIDATE_COUNT=0
SOURCE_LABEL_MUTATION_COUNT=0
SAME_IDENTITY_CONFLICTING_LABEL_COUNT=0
UNDOCUMENTED_CONNECTION_CATEGORY_COUNT=0
VISIBLE_ENTITY_OUTSIDE_DATASET_COUNT=0
CLIENT_SOURCE_FORBIDDEN_MATCH_COUNT=0
CLIENT_BUNDLE_FORBIDDEN_MATCH_COUNT=0
PRODUCTION_DEFAULT_EXPOSURE=false
```

The sanitized validation summary contains a 28-key bug-class ledger. Twenty-five counters are zero. The three nonzero observation counters are expected: two valid control-bearing titles, 155 same-title/different-public-identity cases, and 23,024 display truncations with intact accessible source labels.

## Performance

```text
DATASET_DERIVATION_P50_MS=0.036
DATASET_DERIVATION_P95_MS=0.058
DATASET_DERIVATION_P99_MS=0.084
CANVAS_PURE_FUNCTION_P95_MS=0.458
COLD_REBUILD_A_MS=302.671
COLD_REBUILD_B_MS=305.578
WARM_SELECTED_RECORD_LOOKUP_P95_MS=0.035
SOURCE_INDEX_HEAP_DELTA_BYTES=425887128
```

## Sanitized evidence

The verifier emitted 12 aggregate machine-readable artifacts. `raw/gate-summary.txt` and `raw/protected-boundary.txt` add concise command and boundary receipts. The package contains no full SVG, raw candidate-label list, held row, internal UUID, URL, or complete 7,995-object dataset.

## Browser boundary

```text
LOCALHOST_PREVIEW=NOT_RUN_BY_REQUEST
BROWSER_INTERACTION_ACCEPTANCE=USER_REVIEW_PENDING
PNG_BROWSER_CONVERSION=USER_REVIEW_PENDING
```

SVG preparation is automated and passed; actual bitmap download is intentionally not represented as an automated browser pass.
