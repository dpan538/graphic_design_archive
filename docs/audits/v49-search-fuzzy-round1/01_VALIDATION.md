# Validation Evidence

Date: 2026-08-23 (Australia/Brisbane)

## Automated gates

| Gate | Command | Result |
|---|---|---|
| clean install | `npm ci` | PASS; 145 packages installed |
| typecheck | `npx tsc --noEmit` | PASS |
| production build | `npm run build` | PASS; 46/46 static pages, `/search` 113 kB first-load JS |
| existing API contract | `npm run test:read-platform` | PASS; `READ_PLATFORM_CONTRACT=PASS DIRECT_DATA_COUPLING=0` |
| search invariants | `npm run test:search-v49` | PASS; 14 checks, 7,995 documents |
| index manifest/checksum | `npm run verify:search-v49-index` | PASS |
| benchmark | `npm run benchmark:search-v49` | PASS; 271 queries |
| deterministic rebuild | two builds inside benchmark | PASS; checksum file unchanged |
| existing TRACE verifier | `npm run verify:trace-visualization` | PASS; 23 checks, search document count 7,995 |
| patch whitespace | `git diff --check` | PASS |

One sandboxed build attempt could not reach the repository's existing Google Fonts dependency. The authorized network-enabled rerun completed successfully. This was not a search code failure.

## Search invariant coverage

| Invariant | Evidence |
|---|---|
| SEARCH-INV-001 deterministic order | repeated rank arrays equal |
| SEARCH-INV-002 display preserved | `Almanach d'Haïti` and Bauhaus display assertions |
| SEARCH-INV-003 held/private exclusion | real held stable ID absent; count gates |
| SEARCH-INV-004 no TRACE relation | archive-only hit type; TRACE unchanged |
| SEARCH-INV-005 bounded typo | release/query/token/edit maxima; OSA tests |
| SEARCH-INV-006 exact ID priority | stable-ID reason/score assertion |
| SEARCH-INV-007 exact title priority | exact score and browser reason |
| SEARCH-INV-008 alternate label distinction | `NOT_SUPPORTED_BY_DATA`, never synthesized |
| SEARCH-INV-009 pagination relevance order | two cursor pages with no duplicate IDs |
| SEARCH-INV-010 release/index match | exact-pair mismatch rejected |
| SEARCH-INV-011 scripts preserved | no cross-script folding/transliteration |
| SEARCH-INV-012 empty vs error | separate browser states and repository errors |
| SEARCH-INV-013 no source mutation | normalized channels stored only in derived artifact |
| SEARCH-INV-014 no AI/network model call | source/dependency gates |

## Real-browser acceptance

Browser: Codex in-app Chromium, production Next build on localhost.

| Scenario | Result | Observed evidence |
|---|---|---|
| desktop initial state | PASS | labelled search, 7,995 scope copy, disabled empty submit |
| keyboard-only submit | PASS | Enter changed URL and returned exact title |
| exact query | PASS | `Bauhaus: Art as Life`, rank 1, `Exact title · score 29000` |
| prefix query | PASS | `bauhaus`, 3 results, title-prefix reason |
| typo query | PASS | `bauhuas`, 3 Bauhaus results, spelling-correction reason |
| multi-token out-of-order | PASS | `life bauhaus`, expected record rank 1, all-query-words reason |
| real CJK substring | PASS | `子宫`, one result, `SURF-MDA2026V2R0448` |
| empty/no-result | PASS | `zzqxjv nonexistent`, explicit no-public-match state, zero rows |
| load more | PASS | `poster`: 25 → 50 rows; 50 unique hrefs; next page remains available |
| back/forward | PASS | URL/input/results restored for no-result and `poster` states |
| refresh | PASS | `/search?q=poster` restored input and 25 results |
| mobile 390×844 | PASS | mobile menu state, 390 px document width, no horizontal overflow |
| result links | PASS | standard links with stable surface routes |
| console | PASS | no warning/error entries after corrected searches |
| API failure | PASS | browser visibly rendered `Search failed: … Try again.` as a distinct alert during fault-path verification |

The browser pass found and caused correction of two issues: an illegal invocation from storing browser `fetch` unbound, and unreliable implicit Enter submission. Both are covered by the final production build and browser rerun.

## Benchmark reproducibility

The TSV includes the required old/new top ten, ranks, success fields, timings, categories, split, expected public record IDs, and notes. The held-out quality aggregate excludes ambiguous-short manual stress cases. All 25 failure candidates were title-inspected and classified separately.
