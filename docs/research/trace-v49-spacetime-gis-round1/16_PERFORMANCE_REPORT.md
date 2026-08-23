# Spacetime performance report

## Measurement environment

The committed GIS benchmark evidence was produced on Darwin arm64 with Node v22.21.0 at a 1440×800 viewport and 24 px padding. Values are local engineering measurements, not service-level guarantees.

## Geometry and projection

| Workload | P50 | P95 | P99 | Max |
| --- | ---: | ---: | ---: | ---: |
| 50m JSON parse | 12.977 ms | 13.897 ms | 15.532 ms | 15.532 ms |
| 50m Equal Earth fit | 30.905 ms | 36.130 ms | 36.694 ms | 36.694 ms |
| 50m Equal Earth path generation | 129.830 ms | 142.181 ms | 142.181 ms | 142.181 ms |
| 50m Natural Earth 1 fit | 24.254 ms | 26.763 ms | 27.122 ms | 27.122 ms |
| 50m Natural Earth 1 path generation | 116.788 ms | 137.379 ms | 137.379 ms | 137.379 ms |

The 50m Equal Earth world path strings total 1,553,980 bytes. The static geometry is 2,134,794 raw / 785,828 gzip bytes. The route pays decode/projection/path generation once per geometry load rather than once per period switch.

## Dot fields and texture

Worst measured single field P95 in the fixed workload is 63.875 ms (USA, 500 records). The five-field workload is 90.652 ms P50 and 100.706 ms P95. The actual maximum cohort cell (United Kingdom, 1980s, 1,630 records) is 4.051 ms P50 and 4.301 ms P95 because the bounded field produces 60 dots and an aggregate-anchor remainder. Native generation of 100 SVG patterns is 0.251 ms P50, 0.350 ms P95, and 0.723 ms P99.

The functional route should prepare projected geometry once and compute only the active renderer. Tiny shapes use O(1)-like anchor fallback after bounded candidate work; candidate tests and dots are capped.

## Context runtime comparison

Context cold module import plus first lookup is 479.590 ms. Integrity validation/index construction is 427.094 ms, warm selected-record lookup P95 is 0.004 ms, and runtime heap delta is 18,296,176 bytes. This confirms once-per-process validation rather than per-request reconstruction.

## Integrated functional benchmark

The production read-model/function harness exercised all 23 periods over 460 timed lookups/switches.

| Metric | P50 | P95 | P99 | Max |
| --- | ---: | ---: | ---: | ---: |
| Warm atlas reader lookup | 0.281 ms | 0.940 ms | 1.051 ms | 1.278 ms |
| Geometry load + validation | 12.583 ms | 13.606 ms | 13.910 ms | 13.910 ms |
| Equal Earth fit | 27.709 ms | 32.364 ms | 41.555 ms | 41.555 ms |
| All 242 path generation | 76.956 ms | 91.781 ms | 91.781 ms | 91.781 ms |
| Period switch derivation | 9.903 ms | 37.940 ms | 40.676 ms | 48.709 ms |
| Map view-model derivation | 9.667 ms | 37.122 ms | 39.759 ms | 47.801 ms |

The Spacetime reader cold load is 422.977 ms, builds its validated indexes once, and adds 26,747,856 heap bytes. The default atlas is 21,238 JSON bytes with denominator 1,898, 19 mapped marks, three aggregate-only rows, zero display-unmapped rows, and 22 accessible rows. The functional SVG is 1,533,363 bytes with 264 DOM elements and zero hand-authored paths/object coordinates.

## Route bundle attribution

The final built-route attribution is 55,936 raw JavaScript bytes: 30,457 bytes in the route page chunk plus 25,479 bytes in the GIS/D3 chunk. Their combined gzip size is 18,766 bytes. The shared Link chunk is excluded from the delta; route CSS is 7,361 bytes. Next reports the dynamic route as 18.8 kB with a 125 kB first load. Static analysis finds zero client references to the full record-index artifact.

This basis is explicit so the number can be reproduced. It attributes the route-specific functional implementation, not the native pattern helper in isolation; the helper's current source size is 5,456 raw / 1,605 gzip bytes.

The final integrated API built-output guard, typechecks, production build, Context/Search/Read Platform/TRACE regressions, bundle parity, and whitespace QA pass.
