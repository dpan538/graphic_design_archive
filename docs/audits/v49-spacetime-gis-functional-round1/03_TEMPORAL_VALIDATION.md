# Temporal validation

## Corrected full-cohort result

| Precision | Count |
| --- | ---: |
| Year | 7,552 |
| Approximate | 305 |
| Day | 78 |
| Month | 27 |
| Range | 33 |
| Unknown | 0 |
| Total | 7,995 |

Coverage is 7,995 / 7,995; extent is 1800–2026 inclusive. The corrected exact-day/month-aware classifier supersedes provisional pre-audit counts.

## Bucket validation

- policy: 23 `DECADE` buckets;
- first/last: `[1800,1810)` / `[2020,2030)`;
- range policy: `INTERVAL_OVERLAP`;
- zero-count buckets: 0;
- default period: `SPT-PERIOD-1980-1990`, selected by greatest denominator then earliest start tie-break;
- every period satisfies mapped + unmapped = unique-record denominator;
- precision breakdown sums to each period denominator.

Ranges retain their source display, inclusive extent, `range` precision, and all overlapping period IDs. Qualified/approximate forms are not promoted to exact years. Day/month forms remain distinguishable in the public precision breakdown.

`SPACETIME_TEMPORAL_GOVERNANCE=PASS`. Ten pure-function adversaries cover ISO day, named day, year-month, approximate qualifiers, shortened-year approximate text, explicit range override, exact year, a cross-decade interval, and a reversed interval failure. Deterministic repeated view-model derivation also passes.

The exact bucket table is `docs/research/trace-v49-spacetime-gis-round1/07_TIME_BUCKET_REGISTRY.tsv`. Permanent earliest/latest/range/approximate/day/month samples are in `17_PATHOLOGICAL_SAMPLE_REGISTER.tsv`.

Sanitized evidence: `raw/spacetime-temporal-summary.json`.
