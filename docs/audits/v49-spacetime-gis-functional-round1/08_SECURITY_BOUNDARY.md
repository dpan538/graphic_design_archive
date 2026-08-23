# Security and semantic-boundary validation

## Public boundary

| Invariant | Result |
| --- | ---: |
| Held objects exposed | 0 |
| Held rows projected | 0 |
| Internal UUID exposures | 0 |
| Private controlled-folder IDs emitted | 0 |
| Exact object-coordinate inferences | 0 |
| Silent historical-geography normalizations | 0 |
| Unmapped records hidden | 0 |
| Hand-authored geography paths | 0 |
| Manual object-coordinate table entries | 0 |
| Map-created TRACE semantic edges | 0 |

The generated server-only record index covers only public stable IDs. Round 4 raw evidence contains aggregate summaries and no record/index dump. Public DTOs expose only periods, one-period aggregates, and a bounded selected-geography record page.

## Runtime isolation

- Context public runtime does not reach SQLite, heavy reconciliation, eligibility-ledger parsing, or Search.
- Spacetime public runtime reads committed projection JSON and immutable geometry; it does not invoke an external geocoder or generation source.
- Exact Context and Spacetime resources are path-gated before the generic repository provider.
- API inputs reject duplicate/unknown parameters, invalid periods/geographies, oversized page sizes, malformed cursors, and mismatched release pairs.
- Projection-integrity failures fail closed with generic public errors.

The exact three-resource API build guard passes with endpoint count 3 and zero generic-provider, Search-runtime, SQLite, or client full-record-index references.

## Semantic isolation

Context remains semantically unchanged and has zero region Context nodes. Spacetime roles are recorded context, not exact creation claims. Aggregate anchors/dots have `positionClaim=aggregate_only`. Broad/unmapped geography remains in the numerical equivalent. Map marks never become relations.

## Cartographic disclosure

Natural Earth version/scale/source and boundary convention are disclosed. The archive does not endorse a geopolitical claim by using the dataset.

Final whole-repository regression, built-output guard, and git-boundary inventory pass.
