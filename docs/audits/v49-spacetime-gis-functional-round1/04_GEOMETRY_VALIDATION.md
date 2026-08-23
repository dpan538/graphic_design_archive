# Geometry validation

## Artifact pin

| Field | Value |
| --- | --- |
| Source | Natural Earth Admin 0 Countries |
| Version / scale | 5.1.1 / 50m |
| Feature count | 242 |
| Source SHA-256 | `3e458fc036ad0a66411f2c1e6cac49c5d7bfb81cb1123bc513b22511a2b7fdeb` |
| Output SHA-256 | `01a926cc82cda561692eeefcdde8d52310730c08919fd9f73e679c79a9fa718d` |
| Output raw / gzip bytes | 2,134,794 / 785,828 |
| License | Public domain |

The generated manifest documents source URL, de facto boundary policy, conversion tool/version/parameters, feature identity/order, retained fields, and timestamp.

## Standalone verifier

`SPACETIME_GIS=PASS`

The verifier checked:

- output checksum and byte count;
- exactly 242 allowed Polygon/MultiPolygon features;
- `feature.id === properties.admin0A3` and unique IDs;
- registry/artifact identity parity;
- 81 mapped registry entries and 84 target references;
- zero missing mapped targets;
- 242 nonempty Equal Earth paths;
- derived aggregate-only anchors for large, multipart, and tiny samples;
- deterministic, in-geometry density dots plus tiny fallback;
- deterministic native pattern definition;
- zero `Math.random` in GIS implementation;
- zero hand-authored geography paths and manual object coordinates.

Default projection is Equal Earth; Natural Earth 1 passed as the alternative. The exact benchmark matrix is `docs/research/trace-v49-spacetime-gis-round1/09_PROJECTION_BENCHMARK.tsv`.

Sanitized evidence: `raw/spacetime-geometry-summary.json` and `raw/spacetime-gis-benchmark-summary.json`.
