# Reproducibility

The clean-worktree reproduction rebuilds the semantic and census artifacts from the same frozen source/database inputs and compares byte-level or canonical hashes. Performance timings are explicitly excluded from byte-identity requirements.

| Artifact gate | Match | Receipt |
| --- | --- | --- |
| COMPOSITION_REGISTRY_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| EXPORT_CENSUS_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| FROZEN_AUTHORITY_INPUT_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| GRAPH_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| INDEPENDENT_VERIFICATION_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| PAIR_CENSUS_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| PRODUCTION_READ_MODEL_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| STATE_CENSUS_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| TRANSITION_CENSUS_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| VOCABULARY_CENSUS_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| WORKFLOW_CENSUS_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |

`REPRODUCIBILITY_VERIFICATION=PASS`

`SOURCE_SHA=8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e`

`SOURCE_TREE_SHA=86c2ed7771034f6d3f0f2e10e7a37aeec0552c71`

`DATABASE_SNAPSHOT=v49:ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e`

The reproduction must match vocabulary, pair census, graph, canonical composition registry, state census, transition census, workflow census, and export census. Independent verification is rerun in the reproduction worktree. Any absent or false match keeps Round 16A open.

Source: `docs/audits/v49-exploration-full-space-closure-round1/raw/reproducibility-verification.json`.
