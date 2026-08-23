# Deterministic dot-density method

## Semantics

A generated dot is an `AGGREGATE_DENSITY_MARK`. Its position is synthetic and `aggregate_only`; it is never an archive-object coordinate. Clicking/selecting a density field selects the governed geography and opens the matching record list, not a supposedly co-located record.

## Policy

Policy version: `trace-dot-density-grid-v1`.

| Setting | Value |
| --- | ---: |
| Dot unit | 1 record |
| Preferred spacing | 5 px |
| Minimum spacing | 2.5 px |
| Maximum dots per geography field | 2,000 |
| Maximum candidate tests | 250,000 |
| Tiny-geometry policy | Aggregate-anchor fallback |
| Multipart policy | Whole-geometry candidate pool |

The requested unit is globally one dot per record and does not silently change across geographies or periods. Geometry capacity remains an explicit constraint: the largest observed period/geography cell is 1,630 records, but the projected United Kingdom surface holds 60 governed grid positions at the bounded spacing policy. Those 60 dots represent 60 records and a typed aggregate anchor represents the remaining 1,570; the field still reconciles to all 1,630 records. The maximum period-level dot request is 1,898 records, while each geography field is capped at 2,000 generated dots.

## Deterministic algorithm

1. Project the governed polygon/multipolygon once and capture its rings and bounds.
2. Build the seed from policy version, release ID, time-bucket ID, geometry ID, and record count.
3. Derive deterministic X/Y grid phases with FNV-1a; no `Math.random` is used.
4. Test a projected grid at preferred spacing, then bounded smaller spacing when needed.
5. Retain points inside the projected polygon surface.
6. Assign each candidate a seed-derived score and stable tie-breakers; sort and take the target count.
7. Round output positions to three decimal places.
8. If geometry capacity or the budget cannot represent every record, attach the remainder to a typed aggregate-anchor fallback.

Same release, bucket, geometry, count, projection preparation, and policy produce byte-equivalent dots.

For explicit multi-geometry concepts, v1 uses one aggregate anchor rather than repeating a density field over every target; repetition would multiply the represented record count.

## Pathological behavior

The permanent register covers the largest cell, a tiny Vatican City geometry, multipart Fiji, explicit multi-geometry concepts, and broad/unmapped geography. The verifier checks every generated test dot is inside the governed feature and that fallback record counts reconcile.

## Benchmark

On the authoritative Darwin arm64 / Node 22.21.0 run, field-generation P95 values were 63.875 ms for USA/500, 19.346 ms for Australia/250, 7.264 ms for Japan/100, 14.709 ms for Fiji/25, and 0.007 ms for Vatican City/7 (typed fallback). The five-field workload measured 100.706 ms P95. The actual maximum cohort cell (United Kingdom, 1980s, 1,630 records) measured 4.301 ms P95 and produced 60 dots plus the reconciled anchor remainder.

These are local engineering measurements, not service-level guarantees. The final interactive route should cache projected geometry preparation and avoid generating density fields when aggregate or texture mode is active.
