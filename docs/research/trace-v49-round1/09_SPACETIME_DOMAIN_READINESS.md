# Spacetime Domain Readiness

Every public object has a raw date and raw region candidate, but v49 has zero normalized temporal/place assignments, zero coordinate rows, and zero registered exact object-place roles. Candidate coverage must not be described as exact map coverage.

## Temporal candidates

| Raw precision classification | Public objects | Denominator | Held excluded |
|---|---:|---:|---:|
| year | 7,552 | 7,995 | 7,928 |
| approximate | 344 | 7,995 | 7,928 |
| day | 66 | 7,995 | 7,928 |
| range | 33 | 7,995 | 7,928 |
| unknown | 0 | 7,995 | 7,928 |

The classification retains source uncertainty; it does not rewrite approximate/range labels into exact dates. Exact start-year and derived decade distributions are emitted in the protected `raw/spacetime-distributions.tsv`, with the precision distribution retained alongside them.

## Place roles and coordinates

The actual populated `authority_geography_role` vocabulary describes source/authority geography, not governed object place roles. Therefore the requested object roles have these normalized v49 counts:

| Governed object place role | Total/public | Coordinates | Decision |
|---|---:|---:|---|
| creation | 0 / 0 | 0 | not populated |
| publication | 0 / 0 | 0 | not populated |
| subject | 0 / 0 | 0 | not populated |
| collection | 0 / 0 | 0 | not populated |
| broad_region | 0 / 0 | 0 | raw region candidate cannot be silently assigned this role |

There are 94 distinct trimmed public raw region labels and 7,995 objects with a region candidate. The authority-role audit contains 14 named source/authority categories plus 3,305 `unregistered_object_region_role` rows. All 7,995 objects are coordinate-unmapped. The protected distribution includes exact trimmed raw label aggregates, but labels are explicitly not a governed normalization.

| Candidate coverage | Public count | Denominator | Unknown | Unmapped | Held excluded |
|---|---:|---:|---:|---:|---:|
| raw time | 7,995 | 7,995 | 0 | 0 | 7,928 |
| raw region/place | 7,995 | 7,995 | 0 raw labels | 7,995 coordinates | 7,928 |
| both raw time + raw region | 7,995 | 7,995 | 0 | 7,995 place mappings | 7,928 |
| time only | 0 | 7,995 | — | — | 7,928 |
| place only | 0 | 7,995 | — | — | 7,928 |
| neither | 0 | 7,995 | — | — | 7,928 |
| public normalized/projected spacetime | 0 | 7,995 | 7,995 | 7,995 | 7,928 |

## Required public semantics

A future read model must retain place role, place precision, coordinate provenance/derivation, coordinate evidence, time role, time precision, start/end, unknown, denominator, unmapped, and held-excluded counts. Authority geography must not be relabeled as creation/publication/subject geography just to improve coverage.

```text
SPACETIME_V1=SEMANTIC_REVIEW_REQUIRED
```
