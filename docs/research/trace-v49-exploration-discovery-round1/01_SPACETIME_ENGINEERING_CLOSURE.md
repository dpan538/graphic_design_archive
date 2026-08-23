# Spacetime engineering closure

## Frozen contract

The round preserves the existing `recorded_region_context` and `recorded_date_context` governance. It changes runtime engineering only: geometry lifecycle, projection/path caching, stale-request isolation, renderer preparation, deterministic export, and browser behavior. The public runtime continues to consume the committed `trace-spacetime-v1` projection and its checksum-bound Natural Earth 50m geometry.

`SPACETIME_ENGINEERING_LOGIC_FROZEN=true`

## Runtime dependency closure

The three release-pinned resources remain periods, period atlas, and geography records. The exhaustive API harness reports:

| Metric | Result |
| --- | ---: |
| API endpoints | 3 |
| Periods / governed geographies | 23 / 93 |
| Public / held exclusion | 7,995 / 7,928 excluded |
| Nonzero / mapped nonzero cells | 373 / 351 |
| Matrix requests / pages | 2,200 / 2,173 |
| Generator imports reachable from public runtime | 0 |
| Forbidden source imports reachable from public runtime | 0 |
| SQLite runtime dependency | false |
| Search runtime imports | 0 |
| Client record-artifact references | 0 |

Geometry source loading is checksum-verified and single-flight. A successful source entry retains decoded geometry and its ID index once. Projection cache identity includes projection ID, viewport dimensions, padding, geometry artifact SHA, and projection precision. Cached paths are bounded by an eviction policy; semantic state is never cached in CSS or DOM identity.

## Race and cursor behavior

Request epochs isolate atlas and record requests. A newer period invalidates older atlas work, aborts incompatible record work, and prevents stale responses from committing even if the simulated transport ignores abort. Record page accumulation binds projection SHA, period, geography, and cursor identity. Cross-period and cross-geography appends fail closed. Selecting the same geography preserves an already-loaded record page; after an error it can explicitly retry.

The runtime harness passes:

```text
SPACETIME_RAPID_PERIOD_SWITCH=PASS
SPACETIME_STALE_RESPONSE_GUARD=PASS
SPACETIME_CURSOR_ISOLATION=PASS
```

## Full-cube renderer validation

All 23 periods were traversed twice through independent renderer caches. Results:

| Validation | Result |
| --- | ---: |
| Nonzero period-geography cells | 373 |
| Mapped dot-field cells | 351 |
| Multi-geometry aggregate-anchor-only cells | 14 |
| Dot reconciliation failures | 0 |
| Dot determinism failures | 0 |
| Dot containment failures | 0 |
| Native pattern ID collisions | 0 |
| Hostile near-boundary regression | PASS |
| Aggregate/density/texture semantic parity | PASS / PASS / PASS |

For every mapped density mark, `generatedDotCount + anchorRemainderCount = recordCount`. Dots retain `aggregate_only` position semantics; they are not object coordinates. Multi-geometry records use the typed aggregate-anchor strategy. Aggregate, density, and native-texture modes consume identical governed semantic state.

Deterministic export preparation covers base geometry, selected period, renderer mode, marks, legend metadata, denominators, and mapped/unmapped summaries. The serialized contract contains no internal UUID, held row, raw region field, observation ID, or object-coordinate claim.

## Local closure benchmark

The final documentation-pass benchmark separates cache lifecycle costs:

| Metric | P50 ms | P95 ms | P99 ms |
| --- | ---: | ---: | ---: |
| Geometry cold load | 37.197 | 63.796 | 63.796 |
| Geometry warm reuse | 0.001 | 0.001 | 0.030 |
| Projection/path cache miss | 120.429 | 136.414 | 136.414 |
| Projection/path cache hit | 0.002 | 0.002 | 0.003 |
| Period atlas lookup | 0.207 | 0.889 | 1.040 |
| Time switch | 0.246 | 0.978 | 1.234 |
| Map view-model | 0.009 | 0.039 | 0.064 |
| Aggregate mode | 0.030 | 0.036 | 0.106 |
| Warm density mode | 0.057 | 0.063 | 0.065 |
| Texture mode | 0.063 | 0.179 | 0.896 |
| Cold dot field | 12.107 | 12.565 | 12.589 |
| Record pagination | 0.148 | 0.172 | 0.227 |

Cold breakdown: geometry decode 15.635 ms, index 0.051 ms, and hash verification 1.236 ms. The functional SVG is 1,533,363 bytes with 264 DOM elements; the reader heap delta in this run is 27,538,872 bytes.

## Functional browser acceptance

`SPACETIME_BROWSER_FUNCTIONAL_ACCEPTANCE=PASS`

The production build was exercised through initial 1980s load; dropdown, previous, and next period controls; mapped United States selection; aggregate-only Global/transnational selection; unmapped Tokelau selection; 25-to-50 record paging; record navigation and return; all three renderer modes with identical table rows; tier legend; fit/reset; rapid period and geography changes; and server-loss error recovery. Invalid period, unknown geography, malformed cursor, and invalid release identity returned the expected errors. Console warning/error count was zero.

Keyboard acceptance is recorded precisely: geography selection is a native semantic button in the non-graphic accessible table, keyboard focus was verified, and activation behavior is covered by the runtime accessibility harness. The browser automation backend did not synthesize a native default Enter click; this is not recorded as an application defect or as synthetic proof that did not occur.

## Closure decision

All 16 named regressions pass: full frontend TypeScript, runtime TypeScript, Context projection, Context governance, Context API, Context runtime, Spacetime projection, Spacetime governance/full cohort, Spacetime GIS, Spacetime runtime, Spacetime API, Spacetime functional benchmark, Search index verification, Search regression, TRACE v49 preprogram, and Read Platform/API contract. Production build, synthetic Canvas, browser acceptance, Exploration verification, and artifact validation pass as additional gates.

Spacetime may now change only for final visual design, browser UX or accessibility defects, or genuine GIS/data defects. Governance is unchanged.
