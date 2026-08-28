# Checkpoint 15: v50 manifest clean-checkout portability correction

## Outcome

The attempted final reproduction from the exact published Checkpoint 14 SHA `024935e8d0c36cf0c4724b1960c71f28afef6595` exposed a genuine portability defect in `database/scripts/verify_v50_round16b_manifest.py`. The native verifier and the first database-A replay both failed with `V50_RACE_COMMAND_OUTPUT_MISMATCH:gda_v50_round16b_2317` in the clean detached checkout `/private/tmp/gda_round16b_cp015_clean_repro_024935e8`.

This failure is preserved and fail-closed. It is not a failed historical evidence hash, a changed SQL schema, or a changed concurrency payload. The committed Checkpoint 011 test stdout correctly records the absolute directory beneath the historical test command's cwd. The old verifier instead built the expected historical stdout marker beneath the current checkout `ROOT`, so relocating the same committed bytes to a clean checkout made the comparison impossible to satisfy.

Checkpoint 15 makes a narrow additive correction to that verifier contract. Final clean reproduction is still pending and no reproduction `PASS` is claimed by this checkpoint.

## Correction boundary

Only two database paths differ from the Checkpoint 14 parent:

- `database/scripts/verify_v50_round16b_manifest.py`
- `database/schema-manifest-v50-round16b.json`

No SQL file changed. The Checkpoint 011 replay receipt and all governed race-evidence payloads remain unchanged. The normalized schema identity remains `1152a494e6b64595c9f9291c1d314a9434cb763c7f2a02512d2768e286f571b4`.

The corrected verifier now requires the command metadata cwd to:

- equal the cwd independently recorded in the command ledger;
- be a string;
- be absolute.

Current evidence files and checksum ledgers are still resolved beneath the current checkout root. Only the historical stdout marker is reconstructed beneath the verified historical command cwd. The marker must occur exactly once and must carry the expected database-specific evidence path and checksum. This preserves relocation portability without accepting arbitrary, relative, mismatched, or suffix-extended paths.

The verifier SHA-256 changed from `95d1a7a08b7877d8ac0e93817b19f90aca78d8da7397e59f2584ea9f2eeba72e` to `9a7897f21b943377ca868431463a94828be06627a5344f06956e1efa55ee1423`. The managed manifest SHA-256 changed from `bac907114133ea9b261fdff426434365f020ba92bd0e377b8b2d9629438319c3` to `5f11af95c21417846cd6a71b92173c2d265d5389365fcce08d8c1b7d5b456433` solely to pin the corrected verifier bytes.

## Working-tree verification

The corrected working tree passes the full v50 manifest verifier with 12 managed files, 126 frozen files, 40 v49 replay-prefix files, 35 tables, 28 functions, 26 views, and the unchanged normalized schema hash.

Two focused control sets also pass:

- five matcher controls accept the valid relocated and recorded absolute forms while rejecting a relative path, wrong database, and extra suffix;
- four historical-cwd controls validate both Checkpoint 011 replay records and reject a wrong metadata cwd for each.

The final mutation/restoration control command `1787943538046-cp015-v50-portability-adversarial-controls-final` separately passed a valid baseline, rejected all five adversarial cases (wrong metadata cwd, metadata/ledger cwd disagreement, wrong historical stdout evidence path, wrong database suffix, and wrong evidence checksum), then passed the restored baseline with zero governed-source mutations remaining.

These are working-tree correction checks, not the final clean-checkout result. Native verification from the exact published correction SHA remains required.

## Superseded database diagnostic

A temporary compatibility adapter allowed the database lane to continue far enough to diagnose the boundary and measure two fresh observational databases. That run combined the corrected verifier and long-lived provenance with SQL from the clean Checkpoint 14 checkout. It was therefore a hybrid-source run and cannot establish self-contained clean reproduction.

The two observational databases produced matching governed counts, zero reviewer-queue rows, zero fixture residue, and the same normalized schema hash. The adapter-backed run is nevertheless classified only as `SUPERSEDED_DIAGNOSTIC_ONLY`:

```text
CLEAN_SELF_CONTAINED_DATABASE_REPRODUCTION=false
SOURCE_NATIVE_MANIFEST_PREFLIGHT=false
REPRODUCTION_PASS_CLAIMED=false
```

The diagnostic receipt is independently checked for its disclosure boundary with 35 checks and zero failures. That does not convert it into an independent reproduction. The independent diagnostic actually ran `verify_cp015_database_diagnostic.py` at SHA-256 `60a3393009205eef0279b454f66a98232a75271b03de8dd38ef2f70bc12c2d66`; the current script is `fb0a2aa47de9247f09e4ff1feddaf77f5a27f3ff52e916be9a7cb9d115e2e79e`. The sole delta is removal of one unused `import re` line. Reinserting that line in memory reproduces the executed hash exactly, proving the cleanup changed neither behavior nor trust boundaries; both versions retain the same trust gaps. No executed-byte copy remains. The adapter was removed with the exact temporary cluster root, so the diagnostic cannot now be rerun.

The executed diagnostic verifier did not independently pin the adapter hash, check repository HEAD, or completely verify the race-map/checksum exact set and evidence-path boundary. Those trust gaps are tolerable only because the result is superseded observational evidence. They are not acceptable for, and must not be inherited by, the final native reproduction.

Both target databases and all race databases were dropped, the cluster stopped, PID 57865 and socket/lock/listener 59473 proved absent, and `/private/tmp/gda-v50-round16b-cp015-final` was removed.

## Interrupted logging and other diagnostics

Execution event sequence 1285 records a `STARTED` event at `2026-08-28T18:45:16Z` for `1787942716881-cp015-db-capture-superseded-diagnostic`. Transient `ENOSPC` then left only zero-byte stdout and stderr files: no finish event, metadata, or command-ledger row exists. The execution verifier must use an exact pinned exception for this interrupted ID. No completion or exit status may be fabricated.

The complete 22-event diagnostic ledger also preserves:

- the initially masked sandbox Git/LFS filter failure and later strict clean proof;
- exact removal of stale, user-owned, unattached System V IPC segment 65537 after creator-liveness proof;
- sandbox IPC inventory, Google Fonts DNS, loopback bind, process-list, and final Git/LFS refresh failures and their narrow corrections;
- the PostgreSQL `16.13` versus `16.13 (Homebrew)` assertion mismatch;
- an in-flight parallel command-log read;
- the failed HTTP-output move, launcher-directory, database-capture, and root-workdir path typos;
- the database test PATH omission of `rg`;
- the hybrid diagnostic's failed first launcher validation and its final supersession;
- the post-run unused-import cleanup, its exact nonbehavioral hash delta, and the unchanged trust gaps listed above.
- the sandbox-only post-staging `git lfs status` index-refresh failure and its narrowly escalated successful correction;
- the rejected stale-context documentation patch, which made no partial mutation before the exact-context append succeeded.
- the fail-closed audit-manifest attempt blocked by the sole ignored runtime lock and the exact lock removal before resealing.

Pre-launch typos have no invented command records. The scoped IPC deletion is explicitly nonrecoverable runtime-state removal; it changed no repository data and no unrelated segment.

## Downstream reconciliation

The v50 manifest hash is a governed semantic and recursive-gap input, so dependent artifacts were regenerated rather than left stale:

- v3 semantic independent verification passes 798 checks, SHA-256 `c7fefce80505461e651a62ce7a71e1b307201c37d24faa454412b6b38687959f`;
- the runtime read model remains `f1ae8a35895b27c15fb3d9b42828b8611633ee8ee7e2cbc825772b590304351b`;
- runtime independent verification remains `PASS` with 15 checks and 84 corruption controls, SHA-256 `4839c5bf5492762478e1562c203db0dffc4b62886e1689f6eb7d37e3af2c0c38`;
- recursive-gap primary and independent regeneration both report zero mismatches;
- the recursive input manifest now classifies the database manifest as `CHECKPOINT015_V50_MANIFEST_PORTABILITY_CORRECTION_BYTES` rather than unchanged Checkpoint 011 bytes.

The Checkpoint 14-base frontend lane passed its production build after the recorded DNS correction and generated 46 static pages. Production HTTP passed 1,168 of 1,168 cases after the recorded loopback correction. The reachable-blob scan of the Checkpoint 14 parent found no ordinary blob at or above GitHub's 100,000,000-byte enforced limit. All three are base-lane observations and must be rerun from the published correction SHA.

## Closure and governance boundary

This correction changes no association, evidence disposition, composition, state, transition, workflow, export, or historical conclusion.

```text
PAIR_ASSOCIATION_CLOSURE=false
HIGHER_ORDER_ASSOCIATION_CLOSURE=false
GLOBAL_COMPOSITION_COHERENCE_CLOSURE=false
PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE=false
COMPUTATIONAL_SPACE_CLOSURE=false
FUNCTION3_CLOSURE=false

FORCE_PUSH_USED=false
HISTORY_REWRITTEN=false
ROLLBACK_TAG_PUSHED=false
ORIGIN_MAIN_REWRITTEN=false
MAIN_UPDATED_OR_FAST_FORWARDED=false
DEPLOYMENT_PERFORMED=false
```

## Artifact identities at report time

| Artifact | SHA-256 |
|---|---|
| `database/scripts/verify_v50_round16b_manifest.py` | `9a7897f21b943377ca868431463a94828be06627a5344f06956e1efa55ee1423` |
| `database/schema-manifest-v50-round16b.json` | `5f11af95c21417846cd6a71b92173c2d265d5389365fcce08d8c1b7d5b456433` |
| `raw/parallel-diagnostic-event-ledger-checkpoint015.tsv` | `fd0fa9ee59a3413b7eebf049ac4ee7d923ba83b37d87a213d23d685df07b96ac` |
| `raw/database-reproduction-diagnostic-checkpoint015-superseded.json` | `354022a7f8994d21500397243269eb751d316be765b18c53726a152e4dc05656` |
| `raw/database-reproduction-diagnostic-independent-verification-checkpoint015-superseded.json` | `ef650fc0d11bf515f451b516d034b63368e4af38d9a6eb27892afa5757274ca9` |
| `raw/v3-semantic-contract-independent-verification.json` | `c7fefce80505461e651a62ce7a71e1b307201c37d24faa454412b6b38687959f` |
| `raw/recursive-gap-input-manifest-checkpoint012-v1.tsv` | `0aa96c5f4f3b95c7f356d1d3acb9c11aef7243db0c69136bb8232c8bdfd2cfce` |
| `raw/recursive-gap-closure-build-receipt-checkpoint012-v1.json` | `a63f9f3236b82eec088be726a24b6921f20595c82d64b5bac82ef547cef0798a` |
| `raw/recursive-gap-closure-independent-verification-checkpoint012-v1.json` | `c9b34b7ce83bcb62b1fb0be988d0f0dd5872fe32e3cf8050ef2f05c608030f1a` |
| `raw/v50-manifest-portability-correction-checkpoint015.json` | `6f983c9cbea338843010ae2ad94c9517e21dfa9cdf6c5f7f8c95f722f5906f8f` |
| `docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.json` | `392976fa3813f00ceaa3dd92b1227a57f2ce3658bbdd0fd37ad68d18cd5f9c70` |
| `scripts/trace_round16b/verify_execution_log.py` | `a0883d89ddfca5accd87a8a656cb1ab49479694b0d06a5af427217a7a389ead5` |
| `scripts/trace_round16b/verify_v50_round16b_manifest_portability_controls.py` | `ec75e41ae72ead3aa1dbff6e5e1bec2abb58256f0d26f1c10d8e398ea52b68d3` |

The report's own hash, Checkpoint 15 commit/tree, remote SHA, final local/remote SHA, final clean-worktree status, and native clean-reproduction statuses are intentionally pending. They cannot be truthfully known until this additive checkpoint is sealed and ordinarily published, followed by a new clean detached checkout from its exact remote-equal SHA.
