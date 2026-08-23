# Exploration Field handoff

## Status

`EXPLORATION_FIELD=OPEN_ENDED_DATA_MINING`

Round 4 adds no Exploration implementation files, scoring model, similarity algorithm, ambient-factor model, seed template, probability model, or pixel-grid field.

## Unranked future factors observed during Spacetime auditing

The following may be useful as future descriptive factors. They are not implemented, weighted, ranked, or treated as similarity evidence:

- rare geography × decade intersections;
- temporal concentration by governed geography;
- geographic concentration within a selected decade;
- aggregate-only or unmapped prevalence;
- precision-mix patterns by geography/period;
- multi-region assignment incidence;
- long temporal ranges spanning many buckets;
- geometry/pathological rendering class (tiny or multipart), solely for UI quality control.

These factors must retain the same denominators and missingness visibility as Spacetime. They must not infer influence, importance, causality, exact location, or relevance from cartographic position.

## Handoff boundary

Any later Exploration work should consume public governed Spacetime DTOs or a separately governed derived table, not private source rows or client-side access to the full record index. The Spacetime map remains a selector, not a similarity graph.
