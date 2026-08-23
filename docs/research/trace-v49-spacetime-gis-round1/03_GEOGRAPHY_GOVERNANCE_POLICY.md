# Geography governance policy

## Governed role

The geography role is `recorded_region_context`: a release-pinned record-region context. It is not automatically a creation, publication, subject, collection, travel, or diffusion location.

Policy version: `spacetime-geography-governance-v1`.

## Registry contract

Every distinct typed region label receives exactly one reviewed registry row. The registry records label identity/hash, opaque geography ID, display label, class, mapping state and decision, exact geometry target IDs, map and aggregate eligibility, representative-point policy, historical/transnational/broad flags, qualification, rationale, and review status.

Final mapping is controlled and explicit. Fuzzy matching and an external geocoder are prohibited. A later release with a new label must fail governance until that label receives an explicit decision.

## Classes and decisions

Supported classes are country, territory, subnational, broad region, transnational, historical, unresolved, and other. A class does not itself imply map eligibility.

| Decision | Meaning |
| --- | --- |
| `MAP_TO_ADMIN0` | Reviewed mapping to one pinned Admin-0 feature |
| `MAP_TO_MAP_UNIT` | Reviewed mapping to one pinned territory/map-unit feature |
| `MAP_TO_EXPLICIT_MULTI_GEOMETRY` | One governed aggregate explicitly references multiple pinned geometries |
| `AGGREGATE_WITHOUT_POINT` | Count/list remains visible; no map coordinate or polygon substitution |
| `DISPLAY_UNMAPPED` | Explicitly visible as unmapped; no parent-polity substitution |
| `HOLD` / `EXCLUDE` | Available governance outcomes, unused by public v1 rows |

The current registry has 81 mapped entries, 11 aggregate-only entries, and one unmapped entry. Tokelau is the explicit unmapped case because the pinned 50m asset lacks the required governed map-unit feature. It is not silently assigned to another polity.

Subnational labels without governed subnational geometry—including city-level displays—are aggregate-only. No city coordinate is guessed, geocoded, copied from a general gazetteer, or inferred from a title.

Broad and transnational entries without defensible geometry remain aggregate-only. China / Hong Kong, Israel / Palestine, and Korean Peninsula are the three reviewed explicit multi-geometry concepts. Their labels remain intact and are not normalized to one polity.

## Representative points

Any mapped single-geometry aggregate may derive an `AGGREGATE_LAYOUT_ANCHOR` by the versioned chain:

1. registered geometry exception, if one exists;
2. spherical geometry centroid when it lies inside the feature;
3. projected path centroid when its inverse lies inside;
4. Natural Earth label point;
5. deterministic projected interior grid.

Explicit multi-geometry concepts select the largest projected-area component as the anchor geometry, then apply the same derivation. This avoids multiplying a record count across every target. Every anchor carries geometry ID, artifact ID/version, derivation version/method, and `positionClaim=aggregate_only`.

No anchor is an archive-object coordinate.

## Political-boundary disclosure

The map uses Natural Earth Admin 0 Countries 5.1.1 and its documented de facto boundary convention. A feature's inclusion or depiction does not express archive endorsement of a geopolitical claim. The version, scale, source URL, public-domain terms, conversion parameters, and output checksum are committed with the asset.

## Invariants

The policy implements `ST-GIS-INV-001` through `ST-GIS-INV-020`, with particular emphasis on explicit decisions for every label, visible unmapped counts, held exclusion, deterministic aggregate derivation, no hand-authored geography paths, no object-coordinate inference, precision preservation, and zero map-derived TRACE semantic edges.
