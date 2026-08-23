# Performance validation

## Exploration benchmark

The authoritative run uses three timing iterations and a separate one-iteration `tracemalloc` replay.

| Stage | P50 ms | P95 ms | P99 ms |
| --- | ---: | ---: | ---: |
| Source inventory | 1,187.788 | 1,188.695 | 1,188.776 |
| Curatorial index/co-membership | 1,542.917 | 1,562.024 | 1,563.722 |
| Folder inverted index | 75.204 | 76.792 | 76.934 |
| Co-membership core | 71.957 | 72.069 | 72.079 |
| Missingness end to end | 318.396 | 339.578 | 341.461 |
| Missingness normalization | 247.792 | 260.853 | 262.014 |
| Missingness vector build | 9.712 | 10.226 | 10.272 |
| Missingness census | 9.980 | 10.526 | 10.574 |
| Cross normalization/index | 405.092 | 421.461 | 422.916 |
| One-dimensional frequencies | 85.947 | 94.252 | 94.990 |
| Two-dimensional cells | 154.252 | 170.648 | 172.105 |
| Three-dimensional cells | 71.224 | 76.627 | 77.108 |
| Source concentration | 12.328 | 15.029 | 15.269 |
| Four-family concentration | 26.327 | 40.153 | 41.382 |

Total benchmark time is 25,117.727 ms; output projection is 772.341 ms. Deterministic payload SHA is `c809ee903e630ef537276625c99a16ad26c9c762687e3a22ae9ddf8f5e7b6ecf`.

`EXPLORATION_ANALYSIS_PEAK_HEAP_BYTES=149142324` is the Python-traced allocation peak from the dedicated replay. `PEAK_RSS_BYTES=446955520` is the process high-water resident set. These measurements are different and are reported separately. Timings and memory are excluded from deterministic hashes.

The seven TSVs total 7,825,204 raw / 822,238 deterministic-gzip bytes. No full pair matrix or normalized object vector is emitted.

## Spacetime closure benchmark

| Metric | P50 ms | P95 ms | P99 ms |
| --- | ---: | ---: | ---: |
| Geometry cold load | 37.197 | 63.796 | 63.796 |
| Geometry warm reuse | 0.001 | 0.001 | 0.030 |
| Path cache miss | 120.429 | 136.414 | 136.414 |
| Path cache hit | 0.002 | 0.002 | 0.003 |
| Period atlas lookup | 0.207 | 0.889 | 1.040 |
| Time switch | 0.246 | 0.978 | 1.234 |
| Map view-model | 0.009 | 0.039 | 0.064 |
| Warm density mode | 0.057 | 0.063 | 0.065 |
| Texture mode | 0.063 | 0.179 | 0.896 |
| Cold dot field | 12.107 | 12.565 | 12.589 |
| Record pagination | 0.148 | 0.172 | 0.227 |

The functional SVG is 1,533,363 bytes with 264 DOM elements. Reader heap delta is 27,538,872 bytes. These current cache-aware timings supersede Round 4 labels that combined uncached work.
