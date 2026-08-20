# Scale 32 / 1k / 2k

Final execution-tree builder values were 41.412 ms (32/128), 365.130 ms (1k/3,107), and 789.425 ms (2k/6,107). The 1k→2k ratio was 2.162038178 and exponent was 1.112391999.

Required gates remain 2k builder ≤75,000 ms and exponent ≤1.35. Fresh database clones, one writer, unchanged fixture generation, explicit ANALYZE, unchanged work_mem, and no retry/best-of selection are required. Raw receipts are under `raw/final/performance/`.

The authoritative 1k/2k pair used the repository-standard six-table ANALYZE state. An earlier non-ANALYZE diagnostic pair (1,818.126/6,331.871 ms) is retained and explicitly excluded because it violated that planner-state precondition; it was not used as a best-of result. `SCALE_32=PASS`, `SCALE_1000=PASS`, `SCALE_2000=PASS`, and both hard gates pass.
