# Spacetime runtime validation

## Static and API boundary

The public runtime reaches zero generator imports, zero forbidden source imports, zero SQLite dependency, zero Search runtime imports, and zero client record-artifact references. The release-pinned API retains three endpoints and passes the full 23-period/93-geography matrix: 2,200 requests and 2,173 pages across 373 nonzero cells, of which 351 are mapped.

The built-output API guard passes after the final production build. Public count is 7,995 and all 7,928 held objects remain excluded.

## Cache lifecycle

The runtime verifier proves:

- geometry is checksum-verified, fetched once, decoded once, and indexed once;
- concurrent first loads share one promise and consumer abort signals cannot cancel the shared source;
- failed loads are evicted and can recover;
- projection/path keys bind projection, viewport, padding, geometry SHA, and precision;
- path cache entries are bounded;
- projected bounds, areas, and anchors are populated lazily and cover the 84 required geometry IDs;
- warm source identity and warm prepared-projection identity are reused.

Local closure P95: geometry cold load 63.796 ms, warm reuse 0.001 ms, path miss 136.414 ms, path hit 0.002 ms, period atlas lookup 0.889 ms, time switch 0.978 ms, and map view-model 0.039 ms.

## Request and paging isolation

Rapid A-to-B-to-C period simulation commits only C even when older simulated requests ignore abort. Period changes invalidate record work. Record accumulation binds projection SHA, period, geography, and cursor; cross-period and cross-geography appends fail closed.

```text
SPACETIME_RAPID_PERIOD_SWITCH=PASS
SPACETIME_STALE_RESPONSE_GUARD=PASS
SPACETIME_CURSOR_ISOLATION=PASS
```

## Full-cube renderer and export

| Check | Result |
| --- | ---: |
| Periods / nonzero cells / mapped cells | 23 / 373 / 351 |
| Multi-geometry anchor-only cells | 14 |
| Reconciliation / determinism / containment failures | 0 / 0 / 0 |
| Native pattern collisions | 0 |
| Hostile boundary case | PASS |
| Aggregate/density/texture parity | PASS / PASS / PASS |
| Deterministic export preparation | PASS |
| Native texture hydration stability | PASS |

Export preparation includes governed base geometry, selected period, renderer state, marks, legend, denominators, and geography summary without UUIDs, held rows, raw region labels, observation identifiers, or object-coordinate claims.

## Browser acceptance

Production-browser testing passes period controls, mapped/aggregate-only/unmapped selection, paging, record navigation, all renderer modes, fit/reset, rapid period/geography changes, and network/API failures with zero console warnings/errors.

Keyboard evidence is intentionally precise: non-graphic geography selection uses native semantic buttons in the accessible table, focus was verified, and the runtime accessibility harness covers activation. The automation backend did not synthesize native default Enter activation; no unsupported synthetic browser claim is made.
