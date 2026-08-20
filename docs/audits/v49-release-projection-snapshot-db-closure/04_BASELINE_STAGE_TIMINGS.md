# Baseline stage timings

The checkpoint was replayed in fresh databases at 32, 1k, and 2k using the same PostgreSQL instance, configuration, fixture path, arguments, transaction boundary, ANALYZE set, and one writer. Gate runs were not cache-prewarmed substitutes. Raw gate JSON and nested `auto_explain` logs are under `raw/baseline/`.

Controlled builder results were 57.049 ms (32), 579.777 ms (1k), and 1510.551 ms (2k), yielding exponent 1.3818. The prior 1.725873519 checkpoint result did not reproduce under the corrected single-writer ledger; its larger regression is attributed to the same quadratic parity query amplified by the prior two-writer resource violation.

The complete stage table is generated as `raw/final/stage-comparison.csv`.
