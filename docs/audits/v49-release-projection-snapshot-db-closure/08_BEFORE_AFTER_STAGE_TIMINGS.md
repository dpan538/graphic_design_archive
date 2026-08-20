# Before/after stage timings

`raw/final/stage-comparison.csv` contains 32/1k/2k duration, ratio, exponent, 2k share, rows, query counts, repeated scans, temp blocks/bytes, buffers, WAL, loops, node types, and fingerprints for every requested stage. `raw/final/stage-comparison.json` retains the full machine-readable records.

The final instrumented builder wall values were 74.270 ms (32), 410.634 ms (1k), and 825.498 ms (2k). The decisive `validation_reconciliation` stage changed from baseline 243.863/969.992 ms at 1k/2k (exponent 1.991902; 20.229% of baseline 2k) to 6.685/10.871 ms (exponent 0.701485; 0.271% of final 2k). Final profiles recorded zero temp bytes, zero other database sessions, and zero active writers at both resource snapshots.

The six-table repository-standard ANALYZE stage was 29.018/31.327 ms at 1k/2k. Transaction commit was 4.831/6.801 ms; its noisy exponent was not a hotspot and occupied 0.169% of the 2k staged total.
