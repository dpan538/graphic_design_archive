# Checkpoint 013: clean-reproduction preflight correction

Authorized parent: `76d826100df3a23fce1765ca62245eb348bff1c3`.

The first detached Checkpoint 012 checkout exposed a real reproducibility defect before final reproduction began. The v50 manifest requires twelve race logs for each of the governed `gda_v50_round16b_2317` and `gda_v50_round16b_2318` evidence directories, but the repository's global `*.log` ignore rule had excluded all twenty-four payloads. Only the two `CHECKSUMS.sha256` ledgers were tracked. The complete local worktree masked the omission; a clean checkout could not satisfy the manifest preflight and therefore could not run the governed v50 replay.

This checkpoint corrects only that checkout boundary. Two exact `.gitignore` exceptions make the existing 2317 and 2318 race logs trackable. No broader log family is unignored. No database, semantic artifact, source review, closure flag, application behavior, remote tag, or public branch history is altered.

Every one of the twenty-four logs matches its committed checksum entry. Each directory's checksum-ledger SHA-256 is `595efb06ae1508b3f2cf952e3d0f1af2e9bd70b12bd4fcde93a530b3b70442ab`. The files total 3,830 bytes, the largest is 411 bytes, and the canonical path-plus-payload set SHA-256 is `a4e0ddc0366b9a5504ae655b2b3807eccb2ee1e0ddd08a88bc2a567359a4e787`. All twenty-four paths resolve in the candidate Git index, and `verify_v50_round16b_manifest.py --preflight` passes with twelve managed v50 files.

The complete ordinary-publication chain through Checkpoint 012 was also imported: sixteen receipts, zero chain failures, and Checkpoint 012 receipt SHA-256 `9116447efd5b86c8d82e5f38698bede1451dff58bf979534e716dbb0bcfd8bab`.

This is not the final reproduction receipt. After this additive checkpoint is ordinary-published, a new detached worktree must be created from its exact remote-equal SHA. The deterministic builders, independent verifiers, fresh v50 PostgreSQL replay, frontend/API/build/HTTP/load/memory/export gates, repository integrity checks, reachable-blob proof, and final audit seal must all run from or against that corrected clean authority.

```text
CHECKPOINT013_PURPOSE=CLEAN_REPRODUCTION_PREFLIGHT_CORRECTION
AUTHORIZED_PARENT_SHA=76d826100df3a23fce1765ca62245eb348bff1c3
REQUIRED_V50_RACE_LOG_COUNT=24
CHECKSUM_VERIFICATION=PASS_24_OF_24
CANDIDATE_INDEX_VERIFICATION=PASS_24_OF_24
V50_MANIFEST_PREFLIGHT=PASS
FINAL_CLEAN_REPRODUCTION=PENDING_POST_PUBLICATION

PAIR_ASSOCIATION_CLOSURE=false
HIGHER_ORDER_ASSOCIATION_CLOSURE=false
GLOBAL_COMPOSITION_COHERENCE_CLOSURE=false
PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE=false
COMPUTATIONAL_SPACE_CLOSURE=false
FUNCTION3_CLOSURE=false

FORCE_PUSH_USED=false
HISTORY_REWRITTEN=false
ROLLBACK_TAG_PUSHED=false
DEPLOYMENT_PERFORMED=false
PRODUCTION_ACTIVATION_PERFORMED=false
```
