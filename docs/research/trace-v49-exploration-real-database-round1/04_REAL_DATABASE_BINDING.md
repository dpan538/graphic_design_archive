# Real database binding

The materialized read model is deterministic and derived from `data/prefreeze_candidate_v48.sqlite`, the Phase 2B public eligibility ledger, Search, Context, Spacetime, frozen Round 14 evidence, and the Round 15 Python engine. It carries all source IDs and hashes. Refresh policy: rebuild only after an explicitly governed database/projection release, then rerun all five test groups. The frozen database is never mutated.

Database snapshot: `v49-api-contract-fresh-c:ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e`

Source commit: `aca7b9627ca42776d966f96ce4bd03db1f296ae3`

Read-model hash: `1abdeda493eed7871e0b1a5f1d7412be6bc6203068ac20e9547a32b6c5b473e9`

The product boundary is evidence-governed generic association. It does not emit typed, causal, directional, hierarchical, temporal, or quantitative historical relations. Fixtures are test inputs only and are never a production fallback.
