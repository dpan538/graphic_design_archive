# Full fresh B

Destination B is independent of A: empty database, no reused schema/data/temporary table, no manual SQL, same official runner and canonical Candidate binding.

Full projection B independently produced 15,923 objects / 47,982 memberships in 7,235.528 ms with the same content digest as A.

Canonical Full Fresh B started separately from `template0`, used a separate runtime directory, and committed the same formal replay/import. COPY and durable insert row counts were 3,957,270 and 3,829,784; total wall time was 126.126139 seconds. The verifier returned PASS with schema drift zero. `FULL_FRESH_B_15923_47982=PASS` and `FRESH_REPLAY_COUNT=2`.
