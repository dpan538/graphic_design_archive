# Reproducibility

The clean-worktree reproduction rebuilds the semantic and census artifacts from the same frozen source/database inputs and compares byte-level or canonical hashes. Performance timings are explicitly excluded from byte-identity requirements.

| Artifact gate | Match | Receipt |
| --- | --- | --- |
| COMPOSITION_REGISTRY_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| EXPORT_CENSUS_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| FROZEN_AUTHORITY_INPUT_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| GRAPH_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| HYDRATED_PAYLOAD_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| INDEPENDENT_VERIFICATION_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| PAIR_CENSUS_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| PRODUCTION_READ_MODEL_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| PUBLIC_REMOTE_REF_MAP_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| STATE_CENSUS_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| TRANSITION_CENSUS_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| VOCABULARY_CENSUS_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |
| WORKFLOW_CENSUS_HASH_MATCH | true | docs/audits/v49-exploration-full-space-closure-round1/raw/final-gate-evidence.json |

`REPRODUCIBILITY_VERIFICATION=PASS`

`SOURCE_SHA=8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e`

`SOURCE_TREE_SHA=86c2ed7771034f6d3f0f2e10e7a37aeec0552c71`

`POST_MIGRATION_HARDENED_FINAL_CODE_SHA=4df6a01eceab7e0fa53685d21601180d3e8fb67b`

`DATABASE_SNAPSHOT=v49:ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e`

## Authorized unpublished-branch LFS migration

The eight original Round 16A commits were preserved in a verified standalone Git bundle before the narrowly scoped LFS conversion. Checkpoint order, messages, authorship, timestamps, and phase boundaries remain one-to-one mapped. Only `.gitattributes` and the two authorized independent-verifier audit paths differ at the Git-tree layer; hydrated payload SHA-256 values remain identical.

`HISTORY_REWRITTEN=true`

`UNPUBLISHED_ROUND16A_HISTORY_REWRITTEN=true`

`PUBLIC_EXISTING_HISTORY_REWRITTEN=false`

`ORIGIN_MAIN_REWRITTEN=false`

`ORIGINAL_LINEAGE_BUNDLE_SHA256=edcf9d0e18e3e004c9f8b475b2b2fc91f89e396b21231e9fcbff3243b1983b3c`

The reproduction must match vocabulary, pair census, graph, canonical composition registry, state census, transition census, workflow census, and export census. Independent verification is rerun in the reproduction worktree. Any absent or false match keeps Round 16A open.

Sources: `docs/audits/v49-exploration-full-space-closure-round1/raw/reproducibility-verification.json` and `docs/audits/v49-exploration-full-space-closure-round1/raw/authorized-lfs-migration-receipt.json`.
