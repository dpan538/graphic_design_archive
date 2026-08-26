# Test Group 4 — API Contract, State Safety, and Failure Handling

Status: **PASS**

Test cases: 21

Failures: 0

Database snapshot: `v49-api-contract-fresh-c:ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e`

Read-model hash: `1abdeda493eed7871e0b1a5f1d7412be6bc6203068ac20e9547a32b6c5b473e9`

| Test case | Status | Duration (ms) |
|---|---:|---:|
| Every documented endpoint is present in OpenAPI | PASS | 0.017 |
| Every schema and generated example has its required fields | PASS | 1.723 |
| Category endpoint returns exactly four categories | PASS | 2.456 |
| Invalid category returns INVALID_CATEGORY | PASS | 0.458 |
| Invalid vocabulary returns INVALID_VOCABULARY | PASS | 0.228 |
| Invalid association returns INVALID_ASSOCIATION | PASS | 0.285 |
| Invalid action returns INVALID_ACTION | PASS | 0.500 |
| Unavailable action returns ACTION_NOT_AVAILABLE | PASS | 0.561 |
| Stale state returns STALE_EXPLORATION_STATE | PASS | 0.204 |
| Snapshot mismatch returns STATE_DATABASE_VERSION_MISMATCH | PASS | 0.223 |
| Sparse vocabulary state has a documented error | PASS | 0.012 |
| Sparse association state has a documented error | PASS | 0.007 |
| Mismatched export has NO_EXPORTABLE_COMPOSITION | PASS | 0.457 |
| Excessive node request is bounded | PASS | 0.169 |
| Expansion depth is bounded by governed transitions | PASS | 0.152 |
| Invalid export preset is rejected | PASS | 0.163 |
| Held-data access is explicitly blocked | PASS | 0.103 |
| Malformed text cannot inject SVG markup | PASS | 0.206 |
| Repeated identical requests are idempotent | PASS | 2.404 |
| Concurrent reads do not mutate semantic state | PASS | 18.512 |
| Expected failures never return an unexplained 500 | PASS | 0.722 |
