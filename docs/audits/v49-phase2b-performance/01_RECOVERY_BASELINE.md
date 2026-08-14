# Recovery baseline

P0 completed without opening PostgreSQL or modifying the frozen staging cache.

```text
SOURCE_RECOVERY_REF=origin/recovery/v49-phase2b-performance-checkpoint-20260814
SOURCE_RECOVERY_SHA=6b918dd2ebd9af6f9a8fca6edbe6bbbf7de41320
PHASE2B_IMPLEMENTATION_COMMIT=222e06b59ca9c9a4a323853bec4ffa89a3ae0299
PHASE2A_BASE_COMMIT=86ba95cae9ecf12e58fcabb8170c9020e151b386
WORK_BRANCH=refactor/v49-phase2b-performance
WORKTREE=/private/tmp/modern_GD_history_v49_phase2b_performance
INITIAL_REMOTE_DIVERGENCE=0/0
INITIAL_WORKTREE_CLEAN=true
STABLE_BRANCH_TOUCHED=false
PROTECTED_MAIN_TOUCHED=false
EXTRACTOR_RERUN=false
```

The source ref was fetched successfully from `github.com:dpan538/graphic_design_archive`
before the worktree was created.  Both `222e06b` and `86ba95c` are ancestors of
the recovery SHA.  The pre-existing stable worktree was read only; it was
already checked out on the recovery branch when this task began and was not
altered to force the documented stable-branch expectation.

## Frozen staging binding

The cache at
`/Users/jarlgiovanni/Library/Caches/gda_v49_phase2b/staging-20260814` was read
once by the P0 descriptor verifier.  No Candidate extraction or semantic
reconciliation was repeated.

```text
STAGING_DESCRIPTOR_VERIFIED=35/35
STAGING_TOTAL_DESCRIPTOR_BYTES=4866714086
STAGING_MANIFEST_SHA256=01ac60c705f7450c6668a91ee6a3d2842c3b0258a4ecd85139611bf916681322
STAGING_ATTESTATION_SHA256=11742e9afc577d976ea097540326c2697937290635735ad9d4466efce1758bcc
STAGING_ATTESTATION_WALL_SECONDS=55.702648
STAGING_ATTESTATION_CPU_SECONDS=4.462954
CANDIDATE_SHA256=b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48
BASE_SCHEMA_HASH=4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105
STAGING_REUSED=true
```

The 37-file Phase 2A schema manifest binding passed, as did its historical
audit verification.  All 51 entries in the inherited Phase 2B checksum file
verified.  The bound recovery receipt reports `status=PASS`, eleven inherited
failure probes, zero residue and the same Candidate/schema hashes.

## Protected main start fingerprint

The exact inherited sorted-line fingerprint algorithm was reused.  The start
fingerprint happened to match the original baseline; later external changes,
if any, will be reported and never repaired.

```text
PROTECTED_MAIN_HEAD=7ef26d66b6ad671fdcc5e11bfa831699a39426bc
PROTECTED_MAIN_BRANCH=main
PROTECTED_MAIN_TRACKED_COUNT=59
PROTECTED_MAIN_TRACKED_SHA256=022f7387810c044d00254833c33c81d9f2c1205f15776e7b4407585ce4149c82
PROTECTED_MAIN_STAGED_COUNT=0
PROTECTED_MAIN_STAGED_SHA256=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
PROTECTED_MAIN_UNTRACKED_COUNT=10937
PROTECTED_MAIN_UNTRACKED_SHA256=c1c1c00968cadf25a549cd6776fe05676c1f7029dfa92759e26afea4adfc4730
```

## Process and legacy-path baseline

A read-only process scan at `2026-08-14T13:18Z` found no matching PostgreSQL,
extractor or importer process.  Four similarly named `/private/tmp` paths were
created before this task (two empty directories and two historical sample text
files); they are not treated as task-owned residue and were left untouched.

Evidence:

- `evidence/P0_STAGING_ATTESTATION.json`
- `evidence/P0_PHASE2A_HISTORICAL_AUDIT.json`
- `evidence/P0_SCHEMA_MANIFEST_BINDING.json`
- `evidence/P0_INHERITED_AUDIT_CHECKSUMS.txt`
- `evidence/P0_PROTECTED_MAIN_START.json`
