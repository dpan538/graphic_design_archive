# GIS geometry decision

## Decision

Use a release-pinned normalized Natural Earth **Admin 0 Countries 5.1.1, 50m** GeoJSON asset for `trace-spacetime-v1`.

| Property | Value |
| --- | --- |
| Artifact ID | `natural-earth-admin0-countries-5.1.1-50m` |
| Static path | `/trace-spacetime-v1/natural-earth-50m-admin0-v5.1.1.geojson` |
| Feature count | 242 |
| Output raw bytes | 2,134,794 |
| Output gzip bytes | 785,828 |
| Output SHA-256 | `01a926cc82cda561692eeefcdde8d52310730c08919fd9f73e679c79a9fa718d` |
| Feature identity | Natural Earth `ADM0_A3`; `NE_ID` retained as provenance |
| Coordinate precision | 5 decimal digits |
| License | Public domain |

The asset is committed, immutable, fetched once, and never requested from Natural Earth at runtime. Geometry does not repeat in period atlas responses.

## Scale comparison

The normalized 110m candidate contains 177 features, 10,654 coordinates, 279,027 raw bytes, and 101,118 gzip bytes. The selected 50m candidate contains 242 features, 99,613 coordinates, 2,134,794 raw bytes, and 785,828 gzip bytes.

At the 1440×800 benchmark viewport, 50m Equal Earth path generation measured 129.830 ms P50 and 142.181 ms P95, compared with 11.203/11.744 ms for 110m. The selected-region path samples increased materially: USA 88,551 versus 7,231 bytes, Japan 16,660 versus 1,250, and Fiji 4,203 versus 309. The additional feature coverage and region-selection detail justify the one-time asset cost for this full-screen research route.

10m was not adopted. The v1 world view does not justify its additional geometry/runtime cost.

## Existing World Atlas

The installed `world-atlas` 2.0.2 package is derived from Natural Earth 4.1.0. Its 50m topology is smaller (756,420 raw / 229,093 gzip bytes) and decodes quickly, but it is not the selected current release-pinned geometry authority.

Decision: `REPLACE_WITH_PINNED_NATURAL_EARTH_ARTIFACT`. Package retention is separately `LEGACY_AND_TEST_REFERENCE_ONLY`: `world-atlas` remains installed solely to preserve legacy/test compatibility because retained v48 code may still use it. New Spacetime mapping resolves only against the pinned 5.1.1 artifact.

## Conversion and validation

The normalizer strips unused properties, rounds coordinates to five digits, sorts features by `ADM0_A3`, and retains a documented minimal provenance/property set. The geometry manifest binds source URL/SHA, output SHA/bytes, conversion tool/version/parameters, feature count, license, and generated date.

The verifier checks checksum and byte count, feature count, unique identity, allowed geometry types, exact registry target resolution, 84 mapped target references, and zero missing targets.

## Projection decision

Equal Earth is the functional default because D3 documents it as equal-area; this supports cautious comparison of aggregate density across a world map. Natural Earth 1 is retained as the alternative and benchmarked, but D3 documents it as neither conformal nor equal-area.

The renderer receives paths only from `GeoJSON → D3 projection → geoPath`. Hand-authored SVG geography paths are prohibited.
