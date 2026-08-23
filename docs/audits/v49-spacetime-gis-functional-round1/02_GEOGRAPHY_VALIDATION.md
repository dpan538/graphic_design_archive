# Geography validation

## Census

| Check | Value |
| --- | ---: |
| Typed assignments | 7,996 |
| Public-object coverage | 7,995 / 7,995 |
| Raw labels | 94 |
| Typed governed labels | 93 |
| Multi-region objects | 1 |
| Registry entries | 93 |
| Mapped / aggregate-only / unmapped / held entries | 81 / 11 / 1 / 0 |
| Mapped / aggregate-only / unmapped objects | 7,800 / 194 / 1 |
| Mapped geometry targets / missing targets | 84 / 0 |

Every typed label has a reviewed explicit decision. The one raw/typed discrepancy is preserved as a release diagnostic and does not create an object/city coordinate.

## Exceptional governance

- six city-level/subnational labels plus Hawaii remain aggregate-only without points;
- four broad/transnational labels remain aggregate-only;
- Tokelau is explicitly unmapped;
- five territory/map-unit decisions bind reviewed Natural Earth features;
- three transnational concepts use explicit multi-geometry mappings;
- ambiguous country label Georgia is explicitly reviewed as the country (`GEO`), not inferred as a U.S. state;
- public historical-status and unresolved-class counts are both zero.

The exact 93-row registry is `docs/research/trace-v49-spacetime-gis-round1/04_GEOGRAPHY_REGISTRY.tsv`; nonstandard/diagnostic decisions are in `05_GEOGRAPHY_EXCEPTION_REGISTER.tsv`.

## Identity/security

Public geography IDs are opaque release-pinned hashes. Private controlled-folder IDs are not emitted. The generator rejects private folder-pattern and UUID leakage. No fuzzy final match or external geocoder is used.

## Reconciliation

Mapped + aggregate-only + unmapped objects equals 7,995. Registry assignment counts sum to 7,996. The single multi-region record explains the one-assignment surplus. Aggregate-only/unmapped data remain visible in per-period counts and record pages.

The exhaustive governance verifier reports `SPACETIME_GEOGRAPHY_GOVERNANCE=PASS`, `SPACETIME_FULL_COHORT=PASS`, and 20/20 invariants. It tested all 7,995 public records, 7,928 held identities, 23 periods, and 373 nonempty period-region cells with zero aggregate failures and held exposures.

Sanitized evidence: `raw/spacetime-geography-summary.json`.
