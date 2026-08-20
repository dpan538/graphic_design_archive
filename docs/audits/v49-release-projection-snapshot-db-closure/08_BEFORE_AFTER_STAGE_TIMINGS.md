# Before/after stage timings

`raw/final/stage-comparison.csv` contains 32/1k/2k duration, ratio, exponent, 2k share, rows, query counts, repeated scans, temp blocks/bytes, buffers, WAL, loops, node types, and fingerprints for every requested stage. `raw/final/stage-comparison.json` retains the full machine-readable records.

Final values remain `FINAL_PENDING` until the frozen execution tree rerun.
