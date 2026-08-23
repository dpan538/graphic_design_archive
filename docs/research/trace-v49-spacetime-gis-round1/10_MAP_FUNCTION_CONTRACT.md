# Map function contract

## Renderer-neutral pipeline

```text
governed records
  -> selected decade (interval overlap)
  -> unique-record period dataset
  -> geography aggregation
  -> mapped / aggregate-only / unmapped partition
  -> map-region marks + accessible rows
  -> optional aggregate dots or native patterns
  -> replaceable renderer
```

React renders a prepared view model. It does not classify dates, map labels, count records, group regions, invent points, or choose governance semantics.

## Temporal and aggregate functions

The core pure-function contract includes:

- `governTemporalCandidate` and `deriveTemporalExtent`;
- `buildTimeBucketRegistry` and `deriveBucketMemberships`;
- `selectTimeBucket` and `filterRecordsByTimeBucket`;
- `deriveTimeBucketCounts` and `deriveSpacetimePeriodDataset`;
- `aggregateSpacetimeByGeography`;
- `deriveSpacetimeMapMarks` and `deriveSpacetimeMapViewModel`.

Period denominators count unique public records. Geography cells count assignments for the selected governed geography. Multi-region assignment totals may exceed the period denominator and are labelled separately.

## Geometry and projection functions

The GIS contract includes:

- `loadGovernedGeometry` and `indexGovernedGeometry`;
- `buildProjection` and `fitProjection`;
- `deriveGeoPath`, `deriveProjectedPath`, and `deriveProjectedBounds`;
- `deriveRegionGeometry` and `deriveRegionAnchor`;
- `selectSpacetimeMapGeography`.

The default is D3 Equal Earth at precision 0.1 and path precision three digits. Natural Earth 1 is the supported alternative. A viewport must be positive and padding must not consume it.

## Mark contract

A mapped mark contains opaque geography ID, display label, exact geometry IDs, record count, denominator, precision breakdown, qualification flags, and one typed aggregate anchor. It carries `positionClaim=aggregate_only`.

Aggregate-only and unmapped entries remain separate collections and accessible rows. They are never dropped merely because no map position exists.

The map mark is a UI selector, not a TRACE relation. `realSemanticEdgeCount` is fixed to zero and checked by the view-model function.

## Selection and records

Selection can address mapped, aggregate-only, or unmapped geography by opaque ID. A selected geography and period resolve a deterministically sorted, cursor-paged public record list. The map never binds an individual record to a generated dot.

A period switch aborts any in-flight record-page fetch before requesting the replacement period. Selecting the already-selected geography preserves the current record rows instead of clearing them; a stale or aborted response cannot replace the active selection.

## Renderer modes

Three functional modes share the same atlas/view model:

1. aggregate anchor: one derived selector mark per mapped governed geography;
2. deterministic dot density: synthetic aggregate dots within one governed geometry, with typed fallback;
3. native texture: SVG patterns whose spacing represents documented count tiers.

Mode changes do not change the aggregate or semantic meaning.

Native texture uses the pure `trace-native-count-tier-v1` policy. Inclusive record-count tiers are 1–4: 12 px spacing / 1 px weight; 5–24: 9 px / 1.1 px; 25–99: 7 px / 1.2 px; and 100+: 5 px / 1.2 px. The route renders these tiers as a visible legend. Pattern fill is applied through an inline SVG style so stylesheet rules cannot suppress the encoded texture.
