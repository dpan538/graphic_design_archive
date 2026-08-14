# B3 independent atomicity, boundary, and cleanup review

## Receipt

```text
AGENT=B3
QUEUE=B_INDEPENDENT_ACCEPTANCE
REVIEW_MODE=READ_ONLY_EXISTING_EVIDENCE_STATIC_CODE_GIT_FILESYSTEM_PROCESS_REVIEW
POSTGRES_STARTED=false
POSTGRES_CONNECTED=false
IMPORTER_STARTED=false
EXTRACTOR_STARTED=false
BUILD_STARTED=false
FROZEN_STAGING_SCANNED=false
CORE_IMPLEMENTATION_CHANGED=false
REPORT_ONLY_WRITE=true

B3_REVIEW_STATUS=PASS_SUBJECT_TO_FINAL_AUDIT_COMMIT_AND_PUSH
B3_P0_FINDING_COUNT=0
B3_P1_FINDING_COUNT=0
B3_P2_EVIDENCE_LIMITATION_COUNT=1
B3_ATOMIC_SINGLE_TRANSACTION=true
B3_UPDATED_PATH_FAILURE_PROBES=11/11
B3_FRESH_SCHEMA_TESTS=2/2_PASS
B3_FRESH_REPLAY_A=PASS
B3_FRESH_REPLAY_B=PASS
B3_REPLAY_DIGEST_MATCH=true
B3_PUBLIC_BOUNDARY=PASS
B3_GENERIC_EMPTY_SCHEMA_FIXTURE_ON_FULL_POPULATION=NOT_APPLICABLE_CARDINALITY_PRECONDITION
B3_GENERIC_FIXTURE_TRANSACTION_ROLLED_BACK=true
B3_TASK_OWNED_RESIDUAL_PROCESS_COUNT=0
B3_TASK_ROOT_PRESENT_AFTER_CLEANUP=false
B3_STAGING_RETAINED=true
B3_IMPLEMENTATION_COMMIT=302ddb9683e8b3ee06c34557d10fd72a65c2afaf
B3_FINAL_AUDIT_COMMIT_PUSH=PENDING_CONTROLLER_CLOSEOUT
B3_PROTECTED_MAIN_END_FINGERPRINT=PASS_MATCHES_START
```

No P0 or P1 correctness, atomicity, authorization, public-boundary, or
cleanup defect is present in the reviewed evidence. Fresh A and Fresh B are
two committed, verifier-PASS, full-population replays with identical complete
count vectors and all three logical digest dimensions. The population-specific
public probe covers every P5 condition requested for this zero-release,
zero-positive-rights population and passes. The generic Phase 2A release
fixture did not reach its public-view assertions on the populated database,
but its failure is an honest fixture-cardinality incompatibility, not evidence
of a leak; its transaction rolled back and created no persistent rows.

One P2 evidence limitation is retained rather than hidden: the controller
preserved a detailed human receipt for the two fresh empty-schema test-suite
runs, but deleted their raw temporary stdout after success. That is weaker
provenance than two retained machine logs. It is non-blocking here because the
receipt records both exit-zero final markers and hashes; the forward migration
does not alter role, release, Seal/CAS, or relation-test sources; the inherited
Phase 2A package is checksum-valid; multiple later fresh schema paths reproduce
the same final schema hash; and Fresh A/B independently exercise the resulting
schema and public grants.

The protected-main end fingerprint and database/process cleanup receipts were
subsequently persisted and match this independent inspection. The only item
still pending at closing refresh is the ordinary audit-package commit/push.
That is closeout bookkeeping, not a database acceptance exception. This
report must not be cited as proof of the final remote SHA until the
controller's final Git receipt supplies it.

## Review boundary and evidence

I performed no database connection. I reviewed repository files, persisted
JSON/Markdown receipts, Git metadata, the task scratch path, and one read-only
OS process snapshot. The primary inputs were:

- `evidence/P2_FRESH_SCHEMA_TEST_RECEIPT.md`;
- `evidence/P2_UPDATED_CODE_FAILURE_PROBES.json`;
- `evidence/P3_REPLAY_CODE_FREEZE.sha256`;
- all `P4_FRESH_A_*` and `P5_FRESH_B_*` JSON receipts;
- `evidence/P5_PUBLIC_BOUNDARY_POPULATION.json`;
- `evidence/P0_PHASE2A_HISTORICAL_AUDIT.json`,
  `evidence/P0_INHERITED_AUDIT_CHECKSUMS.txt`, and the immutable Phase 2A
  schema audit package;
- `import.py`, `load.sql`, `run-rehearsal.sh`, `verify.py`, the forward
  migration, `database/scripts/run_tests.sh`, and its four SQL suites; and
- Git/worktree metadata plus the exact task root and process table after
  controller cleanup.

Selected input receipt SHA-256 values at review time were:

| Evidence | SHA-256 |
|---|---|
| `P2_FRESH_SCHEMA_TEST_RECEIPT.md` | `a2c1a643c9967582164bbc1529a79d877ac434547edd70c43b82a204dafb206a` |
| `P2_UPDATED_CODE_FAILURE_PROBES.json` | `93f284944910e4ad713518a6e4ab7fa75372dd9e448c2331cea1c4bd555da2af` |
| `P3_REPLAY_CODE_FREEZE.sha256` | `3da0e5af84c8ca5e61f9995beca57c21fb88c3f678a351ce9433925a63d79f0a` |
| `P4_FRESH_A_IMPORT.json` | `fe55ed3158699a64d6777a50683c59d5d1daa8611ebc4f19ce2112b063c4eaa0` |
| `P4_FRESH_A_VERIFY.json` | `8f99f0806494baec749ae76ab120b845f3fc09d87be2470829982695cfb35d30` |
| `P4_FRESH_A_SUMMARY.json` | `910e6e29ff08cabca2e47ca22a2230918092344cb8d7508b4aa2633f5546d9cb` |
| `P5_FRESH_B_IMPORT.json` | `b3217017dd91b8fc6b3cce5e65befc796577c8ac78bae92efdacd7a1109ab729` |
| `P5_FRESH_B_VERIFY.json` | `8f99f0806494baec749ae76ab120b845f3fc09d87be2470829982695cfb35d30` |
| `P5_FRESH_B_SUMMARY.json` | `2bd008bf4d69f34e2b9d5e1c708bbb8fe43052b45cea0778e7161b2cb5fed025` |
| `P5_PUBLIC_BOUNDARY_POPULATION.json` | `95fc5b6a6f53886714a031675ab690182dc2da3b9f46b192c55b8b9e1e1b42f9` |
| `P6_PROCESS_CLEANUP.json` | `eaa6ad0a09587093efb59415dc643a9071ea37bbf7c1c673bb0aa51e057851e0` |
| `P6_PROTECTED_MAIN_END.json` | `f1c4781f6cd6ab269257b35f89718664c150b06c4630c2f3dd22b5a46e3548ad` |

The identical byte hash of the A/B verifier reports is an additional useful
cross-check: those reports contain the same full count vector, metrics,
integrity counters, schema before/after, public-boundary results, and logical
digests.

## Atomic population transaction

Static inspection and dynamic receipts agree on one transaction boundary:

1. `import.py` emits exactly one population `BEGIN` before staging setup and
   COPY.
2. Every COPY, durable insert, parity assertion, targeted `ANALYZE`, eleven
   named constraint groups, and the final `SET CONSTRAINTS ALL IMMEDIATE`
   occurs before the one population `COMMIT`.
3. `psql` runs with `ON_ERROR_STOP`; the importer accepts success only when
   return code is zero and the post-commit marker is observed.
4. The loader contains no partial commit, trigger disabling,
   `session_replication_role`, `NOT VALID`, or conflict swallowing.
5. Fresh A and B import receipts both report `status=COMMITTED`, return code
   zero, and `committedMarker=true`; their summaries independently report
   `transactionCommitted=true`.

The changed path was subjected to all eleven bounded failure cases on the
fixed scale-50 fixture. Every probe returned the intended failure marker and
reported:

```text
partialImportResidue=0
migrationBatchResidue=0
currentPointerResidue=0
sealedReleaseResidue=0
nonzeroProjectTables={}
```

This includes injected failures after staging, during objects, after corpus,
after visual, and after parity, plus schema/input/cardinality/unknown-field
negative paths. Thus the new transaction path has direct rollback evidence;
it does not rely only on the inherited 11/11 suite.

## Forward schema, roles, Seal/CAS, and fail-closed tests

The base schema remains
`4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105`.
Two fresh empty databases independently replayed that schema, applied the
forward remediation as the schema owner, produced final schema
`aa8cb0af7b61931e51f1f71ed2e4cf0d10b178669de16807871819b330742e8b`,
and ran `database/scripts/run_tests.sh` to exit zero. Both final markers were:

```text
CONSTRAINT_TESTS=PASS ROLE_TESTS=PASS RELEASE_TESTS=PASS TEST_FIXTURE_RESIDUE=0
```

That runner executes:

- constraint, unknown/inactive-relation, and fail-closed rights negatives;
- release Seal/CAS and post-seal mutation negatives;
- role and grant boundaries; and
- serializable sealing behavior,

then checks every project table for zero fixture residue. The two runs report
all four classes PASS with residue zero.

The raw stdout files were not retained. This is the single P2 evidence
limitation stated above. It does not become a P1 semantic finding because:

- the frozen Phase 2A audit manifest and 22 historical checksums validate;
- no file under Phase 2A migrations/functions/views/roles/tests or its
  replay/test runners differs in this worktree;
- the forward migration only adds four indexes and replaces the two targeted
  rights validation functions; it contains no grant, release, Seal/CAS, or
  semantic-relation DDL;
- multiple scale databases plus A/B reproduce the same final schema hash; and
- A/B public checks dynamically confirm the relevant deployed permissions.

## Fresh A/B identity and population parity

Fresh A completed in 2,981.42 controller seconds and Fresh B in 2,513.48
seconds, both below the 90-minute ceiling. Their constraint totals were
517.169478 and 668.211717 seconds. The slowest individual groups were
149.547223 seconds for A and 306.706418 seconds for B, both below the
20-minute full-replay ceiling; the final all-constraint checks completed in
0.003559 and 0.000617 seconds.

The following equality was independently recomputed from the persisted JSON,
not taken only from B's `replayDigestMatchFreshA` flag:

| Dimension | Fresh A | Fresh B | Equal |
|---|---|---|---|
| input parity | 15,923 | 15,923 | yes |
| schema SHA-256 | `aa8cb0af...e8b` | `aa8cb0af...e8b` | yes |
| count-vector SHA-256 | `92eda020...f66b` | `92eda020...f66b` | yes |
| normalized semantic SHA-256 | `a0fa7aae...478b9` | `a0fa7aae...478b9` | yes |
| stable-key-set SHA-256 | `9bf3491b...35a0` | `9bf3491b...35a0` | yes |
| replay-code-freeze SHA-256 | `f39764c8...e910` | `f39764c8...e910` | yes |

The complete A and B count-vector objects, metric objects, integrity objects,
public-boundary objects, semantic/stable row counts, and schema fields are
equal. Required full-population values are:

```text
INPUT_PARITY=15923
ARCHIVE_OBJECT_COUNT=15923
RESEARCH_ELIGIBLE_OBJECT_COUNT=7995
HELD_OBJECT_COUNT=7928
TRACE_ELIGIBLE_OBJECT_COUNT=0
FOLDER_MEMBERSHIP_COUNT=47982
VISUAL_BUNDLE_COUNT=15923
VISUAL_LOCATOR_OCCURRENCE_COUNT=15790
POSITIVE_RIGHTS_COVERAGE=0
MIGRATION_BATCH_COUNT=1
CURRENT_POINTER_COUNT=0
SEALED_RELEASE_COUNT=0
```

All twenty reported integrity-invariant counters are zero. The code-freeze
manifest was also rechecked against the live files: all eight listed files
match, including remediation, importer, loader, runner, verifier, mapping,
and both staging/runtime SQL definitions. No A/B implementation drift is
visible.

## Public boundary and generic-fixture interpretation

Both full verifiers ran as the actual `api_reader` role and report:

```text
apiCurrentRows=0
apiPixelRows=0
rawLocatorSelectDenied=1
rawSourceSelectDenied=1
archiveWriteDenied=1
```

The dedicated post-B population probe adds the required population-level
claims:

```text
HELD_LOCATOR_PUBLIC_LEAK_COUNT=0
API_REMOTE_IMAGE_ROWS=0
POSITIVE_RIGHTS=0
REMOTE_IMAGE_DECISIONS=0
PUBLIC_PIXEL_LOCATORS=0
API_READER_RAW_LOCATOR_SELECT_PRIVILEGE=false
API_READER_RAW_LOCATOR_ACTUAL_SELECT_DENIED=true
API_READER_RAW_SOURCE_ACTUAL_SELECT_DENIED=true
API_READER_ARCHIVE_WRITE_ACTUAL_ATTEMPT_DENIED=true
```

The probe also records socket-only isolation (`listen_addresses=''`, no inet
server address/port) and `productionDatabaseTouched=false`. This exactly
covers the requested P5 conditions for a rehearsal with no sealed release or
current pointer.

The generic `002_release_seal_cas.sql` fixture was authored for an empty
database and asserts that the *total* count of held ledger rows equals one.
On the correct full rehearsal population that count is already 7,928, so it
failed at the assertion `held migration row survives release build` before
reaching its later public-view assertions. The wrapper automatically rolled
back, and the population receipt records `persistentRowsCreated=0`.

Therefore it would be wrong to label that generic fixture `PASS` on Fresh B;
the honest status is `NOT_APPLICABLE_TO_POPULATED_CARDINALITY`. It would also
be wrong to turn this expected exact-count mismatch into a boundary failure.
The required public boundary is proved separately by the two full verifiers
and the population-specific probe. The generic fixture contributes only an
additional rollback observation in this context.

## Cleanup, production isolation, staging preservation, and Git

The controller reports normal drops for Fresh B and the diagnostic database,
followed by successful fast cluster shutdown. Before deletion, the exact task
root occupied 3,019,388 KiB and PGDATA 2,170,380 KiB. My later independent
filesystem inspection found all of these absent:

```text
/private/tmp/gda_v49_phase2b_perf_60423
/private/tmp/gda_v49_phase2b_perf_60423/pgdata
/private/tmp/gda_v49_phase2b_perf_60423/socket
/private/tmp/gda_v49_phase2b_perf_60423/runs
```

A read-only full process-table snapshot found zero commands matching the
exact task root, importer, extractor, rehearsal runner, or performance
monitor. Thus `TASK_OWNED_RESIDUAL_PROCESS_COUNT=0` at the independent
snapshot. No production connection is present in any receipt; the cluster was
Unix-socket-only on non-default port 60423. The stable staging directory still
exists at
`/Users/jarlgiovanni/Library/Caches/gda_v49_phase2b/staging-20260814`; I did
not rehash or scan it. Its inherited P0 attestation remains 35 descriptors,
4,866,714,086 bytes, manifest `01ac60c7...1322`, and attestation
`11742e9a...bcc`.

The work branch was correctly based directly on recovery SHA
`6b918dd2ebd9af6f9a8fca6edbe6bbbf7de41320`. The explicit implementation
allowlist was committed as
`302ddb9683e8b3ee06c34557d10fd72a65c2afaf`; its stat contains only the 15
expected remediation/importer/instrumentation files, and no frozen Phase 2A,
stable-worktree, or protected-main file. The remaining audit directory is
intentionally awaiting the second commit.

The protected-main end receipt exactly equals the start receipt on all bound
dimensions:

```text
HEAD=7ef26d66b6ad671fdcc5e11bfa831699a39426bc
TRACKED_COUNT=59
TRACKED_SHA256=022f7387810c044d00254833c33c81d9f2c1205f15776e7b4407585ce4149c82
STAGED_COUNT=0
STAGED_SHA256=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
UNTRACKED_COUNT=10937
UNTRACKED_SHA256=c1c1c00968cadf25a549cd6776fe05676c1f7029dfa92759e26afea4adfc4730
CONTROLLER_WRITES=0
```

Thus `PROTECTED_MAIN_UNCHANGED=true`, including the pre-existing externally
owned untracked set. Final audit commit, remote SHA, clean-worktree, and
post-push divergence are deliberately delegated to the controller's final Git
receipt because they cannot precede inclusion of this report.

## Independent verdict

Within the completed database and public-boundary scope:

```text
B3_ATOMICITY_REVIEW=PASS
B3_ROLES_PERMISSION_REVIEW=PASS
B3_SEAL_CAS_UNKNOWN_RELATION_REVIEW=PASS_WITH_P2_RAW_LOG_LIMITATION
B3_FRESH_A_B_IDENTITY_REVIEW=PASS
B3_PUBLIC_BOUNDARY_REVIEW=PASS
B3_DATABASE_PROCESS_CLEANUP_REVIEW=PASS
B3_PROTECTED_MAIN_REVIEW=PASS_UNCHANGED
B3_RESIDUAL_P0=NONE
B3_RESIDUAL_P1=NONE
```

The database evidence supports
`PHASE_STATUS=PERFORMANCE_REMEDIATED_AND_REHEARSAL_VERIFIED`,
`PHASE2B_REHEARSAL_COMPLETE=true`, and
`FRESH_POPULATION_REPLAY_COUNT=2`, provided the controller's final audit
commit/push closes the sole remaining bookkeeping item without a new P0/P1
discrepancy.
