# Test Group 3 — Association, Composition, Tree, and Invariant Correctness

Status: **PASS**

Test cases: 17

Failures: 0

Database snapshot: `v49-api-contract-fresh-c:ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e`

Read-model hash: `1abdeda493eed7871e0b1a5f1d7412be6bc6203068ac20e9547a32b6c5b473e9`

| Test case | Status | Duration (ms) |
|---|---:|---:|
| Every direct pair passes | PASS | 0.048 |
| Every skip-one pair passes | PASS | 0.161 |
| Failed associations cannot enter product output | PASS | 0.020 |
| Hard negatives cannot enter product output | PASS | 0.010 |
| Input order does not alter semantic output | PASS | 0.037 |
| Generic pair orientation does not alter association meaning | PASS | 0.011 |
| Duplicate association input does not duplicate output | PASS | 0.015 |
| Irrelevant metadata cannot change semantic output | PASS | 0.081 |
| Same input yields the same semantic hash | PASS | 0.015 |
| Presentation changes preserve semantic hash | PASS | 0.059 |
| Tree labels exactly match active vocabulary | PASS | 0.166 |
| Tree associations match selected compositions | PASS | 0.069 |
| No typed relation is emitted | PASS | 0.018 |
| No causal relation is emitted | PASS | 0.011 |
| No directional relation is emitted | PASS | 0.010 |
| Context cannot override a failed association | PASS | 0.013 |
| Spacetime cannot override a failed association | PASS | 0.011 |
