# Pair explosion and performance

## Pair-explosion decision

The 7,995 public objects admit 31,956,015 possible unordered pairs. Folder membership produces 43,891,194 raw pair events and 28,008,976 exact unique pairs sharing at least one container, a support rate of 0.876485. The raw-event to unique-pair ratio is 1.56704.

`CURATORIAL_PAIR_EXPLOSION_RISK=HIGH`

| Materialization form | Estimated bytes |
| --- | ---: |
| Dense float64 matrix | 511,360,200 |
| Dense uint8 matrix | 63,920,025 |
| Upper triangle, uint8 | 31,956,015 |
| Upper triangle, uint64 | 255,648,120 |
| Upper triangle, 16-byte record | 511,296,240 |
| Raw events, uint64 | 351,129,552 |
| Raw events, 16-byte record | 702,259,104 |
| Folder bitset payload used by analysis | 118,000 |

No full pair matrix or pair-row artifact is committed. The future recommendation is a precomputed aggregate index plus on-demand object fanout.

## Authoritative Exploration benchmark

The final benchmark uses three timing iterations. P95 timings are:

| Stage | P95 ms | Isolation |
| --- | ---: | --- |
| Normalized public-record load | 2,245.159 | governed artifact validation and normalized load |
| Source inventory | 1,188.695 | streamed source/candidate aggregate census |
| Curatorial index and co-membership | 1,562.024 | full curatorial analysis |
| Folder inverted-index construction | 76.792 | isolated folder scan, adjacency, masks, digest |
| Co-membership core | 72.069 | isolated bitset fanout core |
| Missingness end to end | 339.578 | normalization, vector, census, hashes |
| Missingness normalization | 260.853 | record validation and ordering |
| Missingness object-vector build | 10.226 | vector construction only |
| Missingness aggregate census | 10.526 | counters and 19 observed intersections |
| Cross-dimensional normalization/index | 421.461 | normalized dimension index |
| One-dimensional frequency | 94.252 | 3,364 values |
| Two-dimensional observed cells | 170.648 | 6,146 cells |
| Three-dimensional observed cells | 76.627 | 2,399 cells |
| Source concentration | 15.029 | global and supported subset diagnostics |
| Four-family concentration | 40.153 | source, decade, geography, curated container |

The deterministic benchmark payload SHA is `c809ee903e630ef537276625c99a16ad26c9c762687e3a22ae9ddf8f5e7b6ecf`. Timings and memory measurements are explicitly excluded from deterministic analysis hashes.

## Memory semantics

`EXPLORATION_ANALYSIS_PEAK_HEAP_BYTES=149142324` is the Python `tracemalloc` peak from a dedicated one-iteration warm-process replay. It measures Python-traced allocations and excludes pre-trace/native allocations.

`EXPLORATION_ANALYSIS_PEAK_RSS_BYTES=446955520` is the process-lifetime resident-set high-water mark from `getrusage`. It is not interchangeable with the Python heap figure.

The seven research TSVs occupy 7,825,204 raw bytes and 822,238 bytes with deterministic gzip level 9 and timestamp zero. Output projection took 772.341 ms. No normalized object row, object vector, pair row, or full source corpus enters a client bundle.
