# Before/after query plans

The raw baseline and final 1k/2k `auto_explain` plans are tree-contained. The decisive diagnostic comparison is:

| field | baseline 2k | optimized 2k |
|---|---:|---:|
| parity duration | 963.142 ms | 4.562 ms |
| rows removed by join filter | 6,002,671 | 0 |
| inner rows/heap fetches | 6,002,675 | 6,107 |
| temp spill | 0 | 0 |

The final raw plan fingerprint retains the complete ordinal join. It records zero rows removed by filter, zero spill, and the expected bounded inner cardinality. `BEFORE_AFTER_INTERNAL_PLAN=PASS`.
