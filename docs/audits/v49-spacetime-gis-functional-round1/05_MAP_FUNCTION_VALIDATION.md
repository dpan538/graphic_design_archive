# Map-function validation

## Standalone function result

The functional foundation implements the required renderer-neutral stages: period selection/filtering, geography aggregation, mapping-state partition, map-mark derivation, geography selection, deterministic record-page selection, D3 projection/path derivation, aggregate-anchor derivation, dot generation, and native-pattern generation.

| Requirement | Checkpoint status |
| --- | --- |
| Spacetime map view model | Implemented; standalone invariants pass |
| Period filter | Implemented with interval overlap |
| Region aggregation | Implemented; explicit denominator |
| Region selection | Implemented for mapped/aggregate-only/unmapped |
| Record list | Implemented as deterministic cursor page |
| Hand-authored geography paths | 0 |
| Manual object coordinates | 0 |
| Real semantic edges | 0 |
| Density determinism | PASS |
| Native pattern determinism | PASS |
| Pure-function adversaries | PASS (10) |
| Full cohort / 23 periods / 373 cells | PASS |

The renderer consumes an atlas DTO; it does not count or govern records. Multi-geometry anchor selection uses the largest projected-area component and never duplicates record units across geometries.

## Functional route contract

The unlinked/noindex route provides period dropdown and previous/next controls, three renderer modes, mapped geography selection/deselection, fit/reset, explicit denominator/mapped/unmapped/held-excluded counts, accessible geography rows, and paged public record links. Geometry is a stable one-time asset.

Period changes abort an in-flight record fetch before replacement loading begins. Re-selecting the active geography preserves its existing record rows instead of clearing them, and aborted/stale responses cannot supersede the active selection. Native texture mode uses the pure `trace-native-count-tier-v1` policy, presents all four tiers in a visible legend, and applies pattern fill via inline SVG style so CSS cannot hide it.

## Integrated evidence

The exact three-resource API/build guard passes with zero generic-provider, Search, SQLite, and client-record-index references. Typechecks, production build, Context/Search/Read Platform/TRACE regressions, and whitespace QA pass. The functional benchmark passes: period-switch P95 37.940 ms, map-view-model P95 37.122 ms, functional SVG 1,533,363 bytes, and 264 DOM elements.

Route-specific client attribution is 55,936 raw / 18,766 gzip JavaScript bytes plus 7,361 CSS bytes; the shared Link chunk is excluded and full record-index references are zero. Final rebuild parity passes.

Permanent stress inputs are in `docs/research/trace-v49-spacetime-gis-round1/17_PATHOLOGICAL_SAMPLE_REGISTER.tsv`.
