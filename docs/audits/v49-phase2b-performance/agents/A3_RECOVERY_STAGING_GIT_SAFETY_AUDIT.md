# A3 recovery, staging, Git, and process safety audit

Queue A3 performed a read-only recovery audit before PostgreSQL work.  It did
not start or connect to PostgreSQL, run the extractor/importer/reconciliation,
run a failure probe, start Next/browser/build work, alter the staging cache, or
write either protected worktree.  The only A3 write is this report.

## Verdict

```text
A3_STATUS=PASS_WITH_BOUNDARY_WATCHPOINTS
INPUT_OR_CACHE_DRIFT_IDENTIFIED=false
RECOVERY_BASE_VERIFIED=true
RECOVERY_ANCESTRY_VERIFIED=true
RECOVERY_REMOTE_TRACKING_DIVERGENCE=0/0
PHASE2A_BASE_VERIFIED=true
STAGING_DESCRIPTOR_VERIFIED=35/35
STAGING_REUSED=true
EXTRACTOR_RERUN=false
INHERITED_FAILURE_PROBES_PASSED=11/11
FULL_SCALE_FAILURE_PROBES_RERUN=false
BASE_SCHEMA_HASH=4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105
SCHEMA_BINDING_VERIFIED=true
TASK_OWNED_ACTIVE_PROCESS_MATCHES_AT_P0=0
STABLE_BRANCH_TOUCHED_BY_A3=false
PROTECTED_MAIN_TOUCHED_BY_A3=false
```

No A3 finding requires `BLOCKED_INPUT_OR_CACHE_DRIFT`.  The two boundary
watchpoints are not input drift: the stable worktree path is presently parked
on the recovery branch rather than the stable branch, and prior D9 evidence
proves that the user-owned protected main fingerprint can change externally.
Neither path may be repaired, switched, cleaned, stashed, reset, or otherwise
changed by this task.

## 1. Recovery and branch topology

The isolated task worktree was clean when Queue A was dispatched and had this
topology:

```text
WORKTREE=/private/tmp/modern_GD_history_v49_phase2b_performance
WORK_BRANCH=refactor/v49-phase2b-performance
HEAD=6b918dd2ebd9af6f9a8fca6edbe6bbbf7de41320
UPSTREAM=origin/recovery/v49-phase2b-performance-checkpoint-20260814
UPSTREAM_LEFT_RIGHT=0/0
```

The exact parent chain is:

```text
6b918dd2ebd9af6f9a8fca6edbe6bbbf7de41320
  parent 222e06b59ca9c9a4a323853bec4ffa89a3ae0299
  subject docs: record v49 phase 2b migration receipts

222e06b59ca9c9a4a323853bec4ffa89a3ae0299
  parent 86ba95cae9ecf12e58fcabb8170c9020e151b386
  subject feat(data): add deterministic v48 to v49 migration rehearsal

86ba95cae9ecf12e58fcabb8170c9020e151b386
  subject docs: record v49 phase 2a schema receipts
```

`git merge-base --is-ancestor 86ba95c... origin/recovery/...` exited 0.
The local recovery ref and local remote-tracking recovery ref both resolve to
`6b918dd...`.  The new branch therefore starts directly from the required
recovery commit, not from the stable branch or protected main.

A live `git ls-remote` attempted by A3 was DNS-blocked by the child sandbox.
This does not contradict the already-fetched remote-tracking state, but the
primary controller should retain its successful fetch receipt as the authority
for the remote value.  A3's remote-divergence result is explicitly relative to
that fetched `origin/recovery/...` ref.

The initially clean worktree later showed task-owned, concurrent P0 additions
from the controller/other agents.  At `2026-08-14T13:22:04Z` these included the
staging verifier and P0 evidence/register files.  They are expected in-progress
work and do not alter the conclusion that the branch was born clean at
`6b918dd...`.  They must not be mistaken for recovery-base drift.

## 2. Phase 2A schema and stable boundary

Both local and remote-tracking stable refs resolve exactly to the fixed Phase
2A commit:

```text
refactor/v49-data-platform=86ba95cae9ecf12e58fcabb8170c9020e151b386
origin/refactor/v49-data-platform=86ba95cae9ecf12e58fcabb8170c9020e151b386
STABLE_REF_LEFT_RIGHT=0/0
```

There is no `86ba95c..6b918dd` diff under `database/migrations/`,
`database/functions/`, `database/roles/`, `database/views/`, or
`database/schema-manifest.json`.  The recovery commits add the Phase 2B
migration harness and receipts; they do not rewrite Phase 2A DDL.

Current controller evidence further proves:

```text
P0_PHASE2A_HISTORICAL_AUDIT.status=PASS
P0_PHASE2A_HISTORICAL_AUDIT.failures=[]
P0_PHASE2A_HISTORICAL_AUDIT.historicalChecksumEntriesChecked=22
P0_SCHEMA_MANIFEST_BINDING.status=PASS
P0_SCHEMA_MANIFEST_BINDING.stableFileCount=37
P0_SCHEMA_MANIFEST_BINDING.expectedStableFileCount=37
P0_SCHEMA_MANIFEST_BINDING.normalizedSchemaSha256=4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105
```

The live database schema-hash shell wrapper was deliberately not run: it needs
a PostgreSQL connection, which Queue A3 is forbidden to open.  The hash above
is instead bound through the intact Phase 2A historical package, the stable
37-file manifest, the recovery checkpoint, and the current staging
attestation.

Boundary watchpoint: the path
`/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform` is currently
clean but checked out on
`recovery/v49-phase2b-performance-checkpoint-20260814` at `6b918dd...`, not on
`refactor/v49-data-platform`.  This is inherited state.  The stable branch ref
itself remains at `86ba95c...`, and all current development is in the isolated
`/private/tmp` worktree.  Do not switch or otherwise touch the stable path.

## 3. Staging descriptor and binding chain

The retained cache path exists and contains one small manifest plus exactly the
35 descriptor payload names in the committed provenance:

```text
CACHE=/Users/jarlgiovanni/Library/Caches/gda_v49_phase2b/staging-20260814
DESCRIPTOR_COUNT=35
MANIFEST_BYTES=9444
MANIFEST_SHA256=01ac60c705f7450c6668a91ee6a3d2842c3b0258a4ecd85139611bf916681322
TOTAL_DESCRIPTOR_BYTES=4866714086
TREE_KIB=4752659
```

A3 did not hash the 4.5 GB payload.  It compared current names and file sizes
against `STAGING_PROVENANCE.json`; all 35 names were present, there were no
extra descriptor names, and every current byte size equalled its committed
descriptor.

The inherited descriptor-rehash proof is duplicated across two independent
checkpoint surfaces:

1. `evidence/staging-relocation.json` records an atomic same-filesystem rename
   at `2026-08-14T11:33:50Z`.  Both pre-move and post-move sides report 35
   descriptors, 4,866,714,086 content bytes, tree size 4,752,659 KiB,
   `descriptorRehash=PASS`, the same manifest SHA, and identical descriptor
   objects.  It also records the source path absent after verification.
2. `evidence/recovery-checkpoint.json` reports `status=PASS`,
   `descriptorRehash=PASS`, 35 descriptors, manifest SHA `01ac60...`, and
   aggregate descriptor-set SHA
   `e0602c4553039164440a3f638075461c78aa1fcab2572c75e2f3afea6c023f7f`.

The primary controller then performed the one authorized current content
binding.  A3 only read its result:

```text
P0_STAGING_ATTESTATION.status=PASS
P0_STAGING_ATTESTATION.verifiedAtUtc=2026-08-14T13:17:43.679313+00:00
P0_STAGING_ATTESTATION.descriptorCount=35
P0_STAGING_ATTESTATION.totalDescriptorBytes=4866714086
P0_STAGING_ATTESTATION.manifestSha256=01ac60c705f7450c6668a91ee6a3d2842c3b0258a4ecd85139611bf916681322
P0_STAGING_ATTESTATION.attestationSha256=11742e9afc577d976ea097540326c2697937290635735ad9d4466efce1758bcc
P0_STAGING_ATTESTATION.wallSeconds=55.702648
P0_STAGING_ATTESTATION.cpuSeconds=4.462954
```

The staging binding payload agrees across the manifest, committed provenance,
recovery checkpoint, and current P0 attestation:

```text
candidateSha256=b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48
extractorSha256=7bffa7d110dfcbabbcfb06bc971a72c27ede014e03571297e502950b642d4783
mappingSha256=6ca7b8658a12b680c2b9d6253c77be018ed98ecfd93174416eeb766f75465c70
implementationBaseCommit=86ba95cae9ecf12e58fcabb8170c9020e151b386
schemaNormalizedSha256=4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105
bundleBindingSha256=174bc9ef19293ebbb12feb0fc77ef45185bce489466d2005b04e26250e35742b
```

The bound staging metrics include 15,923 surfaces, 6,282,271 field
occurrences, 3,559,820 durable field literals, 47,982 folder assignments, and
15,790 visual locator occurrences.  These match the handoff semantics.

No extractor or reconciliation rerun is warranted.  The content-addressed P0
attestation is the reusable current binding; repeated multi-gigabyte rehashes
or semantic reparses before each fixture/replay would violate the bounded-run
design.

## 4. Frozen authority evidence inherited from Phase 2B

The old migration audit package is internally intact: running its checksum
file from the correct audit-package directory checked all 51 listed entries
successfully, including `MANIFEST.json`; no entry failed.  Its manifest status
remains honestly `PARTIAL_PERFORMANCE_BLOCKED`.

`evidence/reconcile.json` has `status=PASS` and records the fixed authority
ledger:

| Artifact | SHA-256 | Authority |
|---|---|---|
| Candidate JSON | `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48` | sole canonical population input |
| SQLite | `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e` | immutable reconciliation only |
| Transfer JSON | `865358db84c15d960b3535969a32521c0ffec177f7455d21db86cd131f787d5b` | transfer integrity only |
| Transfer CSV | `694a60657077bcab8888c4a4ef1daf6059706e544606d4862e46c57dcf6ddc18` | transfer integrity only |
| TRACE manifest | `1678e211023aa324078e0478f88670d2378b6dc5c398cc5c04722605038fee23` | legacy derived-product reconciliation only |

The same evidence records zero canonical rows or backfills from SQLite,
transfer artifacts, TRACE, or search.  A3 inherited these checks via the
content-addressed audit package; it did not independently rehash or parse the
large frozen assets.

## 5. Inherited failure probes and rollback

The committed machine-readable failure report is checksum-valid and reports
exactly eleven probes.  A3 mechanically confirmed:

```text
FAILURE_REPORT_STATUS=PASS
PROBE_COUNT=11
RUNTIME_PROBE_COUNT=5
ALL_EXPECTED_EXIT_2=true
ALL_PARTIAL_IMPORT_RESIDUE_ZERO=true
ALL_CURRENT_POINTER_ADVANCEMENT_FALSE=true
ALL_RELEASE_SEALED_FALSE=true
```

The probes are `source_sha_mismatch`, `schema_sha_mismatch`, `after_staging`,
`during_objects`, `after_corpus`, `after_visual`, `after_parity`,
`duplicate_surface_key`, `missing_surface`, `extra_surface`, and
`unknown_field_or_type_without_disposition`.

The recovery checkpoint independently records all eleven as complete,
`firstUnreliableProbe=null`, and `resumeFailureHarness=false`.  Its final
rollback snapshot reports 223 project tables, zero project rows, zero migration
batch rows, zero current pointers, zero sealed releases, and schema hash
`4ec9a764...`.

Inheritance condition: these 11/11 probes prove the recovery implementation
only.  If the importer or transaction path is modified, the user-mandated
fixed fixture (no more than 1,000 objects) must rerun all eleven cases.  The
full-size failure suite must not be rerun.

## 6. Protected main boundary

The controller's P0 start fingerprint is:

```text
PATH=/Users/jarlgiovanni/Desktop/modern_GD_history
BRANCH=main
HEAD=7ef26d66b6ad671fdcc5e11bfa831699a39426bc
TRACKED_COUNT=59
TRACKED_SHA256=022f7387810c044d00254833c33c81d9f2c1205f15776e7b4407585ce4149c82
STAGED_COUNT=0
STAGED_SHA256=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
UNTRACKED_COUNT=10937
UNTRACKED_SHA256=c1c1c00968cadf25a549cd6776fe05676c1f7029dfa92759e26afea4adfc4730
MATCHES_RECORDED_INITIAL=true
MAIN_VS_ORIGIN_MAIN_LEFT_RIGHT=0/5
```

The path is intentionally dirty and must remain read-only.  Historical D9
evidence is important: it observed an intervening external state with the same
HEAD/branch/counts but different tracked and untracked collection hashes.  The
subsequent receipt explicitly records
`PROTECTED_MAIN_FINGERPRINT_INVARIANT=false`,
`PROTECTED_MAIN_EXTERNAL_CHANGE_OBSERVED=true`, and controller writes zero.
The current P0 fingerprint matching the earlier baseline does not erase that
external-mutation history.

Accordingly, `PROTECTED_MAIN_UNCHANGED` for this run may be decided only by the
primary controller's end fingerprint compared with
`P0_PROTECTED_MAIN_START.json`.  A3 did not run checkout, reset, restore,
stash, clean, add, or any write command in this path.

## 7. Process and temporary-path scan

Inherited cleanup evidence records the prior database dropped, its cluster
normally stopped and deleted, and zero task-owned importer/PostgreSQL/psql
processes.  At approximately `2026-08-14T13:18Z`, A3 used an escalated,
read-only process-list scan filtered for `gda_v49_phase2b`, the isolated
Phase 2B worktree, and the v48-to-v49 importer/extractor paths.  The filter
returned no lines (grep exit 1):

```text
P0_TASK_PROCESS_MATCH_COUNT=0
```

Four similarly named filesystem entries predate this run and were left
untouched:

| Path | Type/size | Birth/mtime (AEST) | Classification |
|---|---|---|---|
| `/private/tmp/gda_v49_phase2b_backend_50121.sample.txt` | historical sample text, 256,854 bytes (252 KiB allocated) | 2026-08-14 01:44:03 | pre-existing; not current-task-owned |
| `/private/tmp/gda_v49_phase2b_importer_7349.sample` | historical sample text, 69,649 bytes (72 KiB allocated) | 2026-08-12 15:02:46 | pre-existing; not current-task-owned |
| `/private/tmp/gda_v49_phase2b_finalstage.EMpZEE` | empty directory, 0 KiB | born 2026-08-12 11:00:33; mtime 11:17:20 | pre-existing; ownership not assumed |
| `/private/tmp/gda_v49_phase2b_stage.kZmUs7` | empty directory, 0 KiB | born 2026-08-12 10:07:46; mtime 11:00:12 | pre-existing; ownership not assumed |

The sample headers describe historical PIDs 50121 and 7349; neither PID/path
appeared in the live filtered process scan.  These files/directories are not
active process residue and must not be deleted merely because their names
match the older task.  Final cleanup should remove only resources explicitly
created and tracked by the current controller.

## 8. Required watchpoints for later phases

1. Keep the stable worktree and protected main read-only; use only the isolated
   performance worktree for implementation.
2. Retain the controller's successful fetch evidence because A3's independent
   live remote query was network-blocked.
3. Reuse `P0_STAGING_ATTESTATION.json`; do not rehash/reparse the full cache at
   every scale point or replay.
4. If importer/transaction logic changes, run the bounded <=1,000-object
   eleven-case fixture suite before authorization; do not claim the inherited
   11/11 as proof of changed code.
5. If persistent schema changes are needed, add a forward migration and retain
   the Phase 2A files/hash unchanged.
6. Re-fingerprint protected main at close and report any difference without
   attempting repair.
7. Attribute and clean only current-run process/database/PGDATA resources; do
   not sweep pre-existing `/private/tmp` entries.

## Read-only evidence consulted

- `docs/audits/v49-phase2b-migration/01_INPUT_AND_SCHEMA_PIN_RECEIPT.md`
- `docs/audits/v49-phase2b-migration/05_STAGING_AND_TRANSACTION_RECEIPT.md`
- `docs/audits/v49-phase2b-migration/13_FAILURE_INJECTION_AND_ROLLBACK_RECEIPT.md`
- `docs/audits/v49-phase2b-migration/17_PHASE2B_GATE_RECEIPT.md`
- `docs/audits/v49-phase2b-migration/19_RECOVERY_RESUME_INSTRUCTIONS.md`
- `docs/audits/v49-phase2b-migration/20_GIT_AND_PROTECTED_MAIN_RECEIPT.md`
- `docs/audits/v49-phase2b-migration/24_RECOVERY_CORRECTIONS.md`
- `docs/audits/v49-phase2b-migration/STAGING_PROVENANCE.json`
- `docs/audits/v49-phase2b-migration/MANIFEST.json`
- `docs/audits/v49-phase2b-migration/CHECKSUMS.sha256`
- `docs/audits/v49-phase2b-migration/evidence/failure-injections.json`
- `docs/audits/v49-phase2b-migration/evidence/reconcile.json`
- `docs/audits/v49-phase2b-migration/evidence/recovery-checkpoint.json`
- `docs/audits/v49-phase2b-migration/evidence/staging-relocation.json`
- `docs/audits/v49-phase2b-migration/evidence/process-cleanup.json`
- `docs/audits/v49-phase2b-migration/agents/D9_INDEPENDENT_PERFORMANCE_FINAL_VERIFIER.md`
- `docs/audits/v49-phase2b-performance/evidence/P0_PHASE2A_HISTORICAL_AUDIT.json`
- `docs/audits/v49-phase2b-performance/evidence/P0_SCHEMA_MANIFEST_BINDING.json`
- `docs/audits/v49-phase2b-performance/evidence/P0_STAGING_ATTESTATION.json`
- `docs/audits/v49-phase2b-performance/evidence/P0_PROTECTED_MAIN_START.json`
