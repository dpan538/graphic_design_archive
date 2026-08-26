# Test Group 1 — Real Data, Four Categories, and Vocabulary Authenticity

Status: **PASS**

Test cases: 14

Failures: 0

Database snapshot: `v49-api-contract-fresh-c:ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e`

Read-model hash: `1abdeda493eed7871e0b1a5f1d7412be6bc6203068ac20e9547a32b6c5b473e9`

| Test case | Status | Duration (ms) |
|---|---:|---:|
| Exactly four canonical categories are returned | PASS | 0.432 |
| Every category resolves to approved source records | PASS | 0.050 |
| Every visible vocabulary item has real source attestation | PASS | 0.031 |
| Every visible vocabulary item has academic support | PASS | 0.055 |
| No fixture-only term appears in a product response | PASS | 0.820 |
| No invented or model-generated term appears | PASS | 0.395 |
| No held object appears | PASS | 2.087 |
| Every archive object reference resolves | PASS | 0.061 |
| Every Context reference resolves | PASS | 0.034 |
| Every Spacetime reference resolves | PASS | 0.024 |
| Archive, Context, Spacetime, and Exploration use one snapshot | PASS | 0.011 |
| Category counts match the direct database-derived read model | PASS | 0.012 |
| Vocabulary counts reconcile by category | PASS | 0.023 |
| Association counts reconcile by category | PASS | 0.016 |
