# Performance audit

## Reproducible GIS benchmark

Environment: Node v22.21.0, Darwin arm64, 1440×800 viewport, 24 px padding.

| Metric | P50 | P95 | P99 |
| --- | ---: | ---: | ---: |
| 50m geometry JSON parse | 12.977 ms | 13.897 ms | 15.532 ms |
| Equal Earth projection fit | 30.905 ms | 36.130 ms | 36.694 ms |
| Equal Earth path generation | 129.830 ms | 142.181 ms | 142.181 ms |
| Natural Earth 1 fit | 24.254 ms | 26.763 ms | 27.122 ms |
| Natural Earth 1 path generation | 116.788 ms | 137.379 ms | 137.379 ms |
| Fixed five-field dot workload | 90.652 ms | 100.706 ms | 101.140 ms |
| Actual max cell: UK/1980s/1,630 | 4.051 ms | 4.301 ms | 4.331 ms |
| Native 100-pattern generation | 0.251 ms | 0.350 ms | 0.723 ms |

The actual maximum cell produces 60 in-geometry dots and a typed aggregate-anchor remainder, representing all 1,630 records. Maximum period denominator/dot request is 1,898; per-field generated dots are capped at 2,000.

## Payload sizes

- geometry asset: 2,134,794 raw / 785,828 gzip bytes;
- Equal Earth world path strings: 1,553,980 bytes;
- geometry features: 242;
- period buckets: 23;
- aggregate cube cells: 373.

## Context runtime

Cold load 479.590 ms; validation/index 427.094 ms; warm lookup P95 0.004 ms; runtime heap delta 18,296,176 bytes.

## Pending integrated fields

The final integrated function harness reports geometry load/validate P95 13.606 ms, all-path generation P95 91.781 ms, period switch P95 37.940 ms, map-view-model P95 37.122 ms, functional SVG 1,533,363 bytes, 264 DOM elements, and a 26,747,856-byte reader heap delta. Final route-specific client attribution is 55,936 raw / 18,766 gzip JavaScript bytes (shared Link chunk excluded) plus 7,361 CSS bytes.

Sanitized integrated evidence: `raw/spacetime-functional-benchmark-summary.json`.
