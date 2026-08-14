# D9 independent performance-block final verification

Verified at `2026-08-14T12:18:55Z` by an independent read-only verifier. This
review did not open a PostgreSQL connection and did not start PostgreSQL,
extractor, importer, reconciliation, or build processes. It did not modify the
protected main worktree, cache, frozen assets, Phase 2A files, or Git state.

## Result

```text
INDEPENDENT_VERIFIER_STATUS=FAIL
FAILURE_REASON=PROTECTED_MAIN_FINGERPRINT_CHANGED_AFTER_RECORDED_RECEIPT
PHASE2B_GATE_STATUS=PARTIAL_PERFORMANCE_BLOCKED
PHASE2B_PASS_CLAIM_PRESENT=false
```

The task-owned worktree and checkpoint evidence pass the checks below. The
independent verification cannot pass, however, because the protected dirty main
no longer has the exact tracked and untracked fingerprints recorded in the
performance-block package. Its HEAD, branch, and path counts are unchanged, but
the two collection SHA-256 values are not. No attempt was made to identify,
alter, restore, stash, or otherwise touch those user-owned changes.

## Git and scope checks

```text
RECOVERY_BRANCH=recovery/v49-phase2b-performance-checkpoint-20260814
RECOVERY_HEAD=222e06b59ca9c9a4a323853bec4ffa89a3ae0299
IMPLEMENTATION_BASE=86ba95cae9ecf12e58fcabb8170c9020e151b386
MERGE_BASE=86ba95cae9ecf12e58fcabb8170c9020e151b386
BASE_TO_HEAD_LEFT_RIGHT=0/1
STAGED_FILE_COUNT=56
STAGED_OUTSIDE_PHASE2B_ALLOWLIST=0
PHASE2A_OR_FROZEN_PATHS_TOUCHED=0
WORKTREE_STATUS=56 staged additions only; no unstaged or untracked target paths
```

The staged allowlist is limited to
`database/data-migrations/v48-to-v49/` and
`docs/audits/v49-phase2b-migration/`. No staged path is in Phase 2A migration,
roles, functions, views, frozen-data, frontend, generated-data, or historical
audit locations.

## Audit integrity checks (before this D9 receipt was written)

```text
CHECKSUMS_SHA256=PASS (49 checked entries)
MANIFEST_LISTED_FILES=48
AUDIT_NONSELF_FILES_ON_DISK=48
MANIFEST_UNLISTED_FILES=0
MANIFEST_STALE_LISTED_FILES=0
MANIFEST_ENTRY_HASH_OR_SIZE_MISMATCHES=0
MANIFEST_INCLUDED_IN_CHECKSUMS=true
CHECKSUMS_SELF_LISTED=false
```

`CHECKSUMS.sha256` deliberately checks `MANIFEST.json` but not itself; the
manifest deliberately inventories the 48 non-self audit files. This is a
coherent non-self-hashing design. This D9 file is intentionally outside that
pre-write verification snapshot. The controller must regenerate the manifest
and checksums after deciding whether to include this independent receipt.

## Performance-block and rollback evidence

```text
PHASE_STATUS=PARTIAL_PERFORMANCE_BLOCKED
PERFORMANCE_BLOCKING_STAGE=SET_CONSTRAINTS_ALL_IMMEDIATE
FAILURE_PROBES_STATUS=PASS
FAILURE_PROBES_PASSED=11/11
ALL_PROBES_EXPECTED_EXIT_2=true
ALL_PROBES_ZERO_RESIDUE_POINTERS_AND_SEALS=true
ROLLBACK_PROJECT_TABLE_COUNT=223
ROLLBACK_PROJECT_TABLE_ROWS=0
ROLLBACK_NONZERO_PROJECT_TABLES=0
ROLLBACK_MIGRATION_BATCH_ROWS=0
ROLLBACK_CURRENT_POINTERS=0
ROLLBACK_SEALED_RELEASES=0
ROLLBACK_SCHEMA_SHA256=4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105
```

The package contains only `PARTIAL_PERFORMANCE_BLOCKED` phase-status claims;
there is no successful Phase 2B population/replay claim. The persisted rollback
evidence, rather than a live database connection, was checked for the zero-row
and schema-pin facts above.

## Preserved staging and resource cleanup

```text
CACHE_STAGE_REALPATH=/Users/jarlgiovanni/Library/Caches/gda_v49_phase2b/staging-20260814
CACHE_STAGE_EXISTS=true
CACHE_MANIFEST_SHA256=01ac60c705f7450c6668a91ee6a3d2842c3b0258a4ecd85139611bf916681322
CACHE_MANIFEST_DESCRIPTOR_COUNT=35
RELOCATION_DESCRIPTOR_REHASH=PASS
RECOVERY_DESCRIPTOR_REHASH=PASS
CACHE_MANIFEST_MATCHES_RELOCATION_AND_RECOVERY=true
CLUSTER_TEMP_ROOT_ABSENT=true
STAGE_TEMP_ROOT_ABSENT=true
RECOVERY_BACKUP_ROOT_ABSENT=true
TASK_PROCESS_MATCH_COUNT=0
```

The 4.5 GB staging data was not rehashed during this review. Only the retained
small manifest and the pre-existing relocation/recovery descriptor evidence
were inspected, as required.

## Protected main read-only recheck

The current fingerprint was computed with the same `git diff --name-status`,
`git diff --cached --name-status`, `git ls-files --others --exclude-standard`,
sorted-line, trailing-newline SHA-256 algorithm implemented in the checkpoint
generator.

```text
PROTECTED_MAIN_HEAD_EXPECTED=7ef26d66b6ad671fdcc5e11bfa831699a39426bc
PROTECTED_MAIN_HEAD_CURRENT=7ef26d66b6ad671fdcc5e11bfa831699a39426bc
PROTECTED_MAIN_BRANCH_CURRENT=main
PROTECTED_MAIN_COUNTS_CURRENT=tracked:59 staged:0 untracked:10937
PROTECTED_MAIN_TRACKED_SHA256_EXPECTED=022f7387810c044d00254833c33c81d9f2c1205f15776e7b4407585ce4149c82
PROTECTED_MAIN_TRACKED_SHA256_CURRENT=0ea641a2aed91227b6b3f3ab3d85976520803a3efbaeb61b056d93a880b5867f
PROTECTED_MAIN_UNTRACKED_SHA256_EXPECTED=c1c1c00968cadf25a549cd6776fe05676c1f7029dfa92759e26afea4adfc4730
PROTECTED_MAIN_UNTRACKED_SHA256_CURRENT=34c9d5ab61511d9f1c948b4648a6891338564a66a3a1efb7f8f2017c1f32e75a
PROTECTED_MAIN_FINGERPRINT_UNCHANGED=false
```

## Commands used

```text
git merge-base 86ba95... HEAD
git rev-list --left-right --count 86ba95...HEAD
git status --porcelain=v1
git diff --cached --name-only
shasum -a 256 -c docs/audits/v49-phase2b-migration/CHECKSUMS.sha256
read-only JSON/manifest consistency checks with Python standard library
read-only protected-main Git fingerprint calculation with the generator's algorithm
ps ax -o pid=,pgid=,etime=,command= (task-token filter only)
```

No PostgreSQL command, socket connection, task harness, or cache-content
rehash was executed.
