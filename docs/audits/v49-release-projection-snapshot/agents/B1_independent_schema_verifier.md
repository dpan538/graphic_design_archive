# B1 — Independent schema, atomicity, and audit-package verifier

## Scope and method

- Auditor: B1, Queue B independent read-only verifier.
- Baseline commit: `3e666b5265ebe7b41ea0c98531b35761ff0d9485`.
- Implementation inspected in the isolated Phase 2C-S worktree.  This report
  does **not** attest to database execution: Queue B was prohibited from
  starting PostgreSQL, npm, Next, TypeScript, a browser, or a generator.
- This report writes only itself.  It did not edit SQL, scripts, historical
  audit files, Git state, or application code, and it made no commit.

## Paths inspected

| Area | Paths |
|---|---|
| Additive schema | `database/migrations/010_release_projection_snapshot.sql` |
| v3 builder/lifecycle/guards | `database/functions/016_release_projection_snapshot_v3.sql` |
| Publisher and reader grants | `database/roles/004_release_projection_snapshot_grants.sql`, `database/roles/002_database_grants.sql`, `database/roles/003_read_api_core_grants.sql` |
| Replay/hash/inventory | `database/scripts/replay.sh`, `database/scripts/schema_hash.sh`, `database/schema-manifest.json` |
| Fixture and focused test | `database/fixtures/phase2s_32_snapshot.sql`, `database/tests/005_release_projection_snapshot.sql`, `database/scripts/run-phase2s-snapshot.sh` |
| Historical lifecycle/constraints for comparison | `database/migrations/001_foundation.sql`, `database/migrations/002_raw_core_provenance.sql`, `database/migrations/004_release_audit.sql`, `database/migrations/007_release_copy_integrity.sql`, `database/migrations/009_read_api_core.sql`, `database/functions/002_mutation_guards.sql`, `database/functions/003_release_and_cas.sql`, `database/functions/005_projection_builders.sql`, `database/functions/008_projection_builders_v2.sql`, `database/functions/009_projection_inventory_builders.sql`, `database/functions/014_release_copy_guards.sql` |
| Audit package | `docs/audits/v49-release-projection-snapshot/` |

## Commands actually run

```text
git status --short
git diff --name-only
git diff -- database/scripts/replay.sh database/scripts/schema_hash.sh
git ls-files database/migrations database/functions database/roles database/tests database/scripts
git rev-parse HEAD; git branch --show-current
find / rg / sed / wc limited to the inspected paths above
```

No PostgreSQL, npm, Next, TypeScript, browser, importer, staging, production
database, full migration, or full Seal/CAS suite was run by B1.

## Additive-boundary result

`git diff --name-only` showed modifications only to the forward replay/hash
scripts plus new `010`, `016`, `004`, fixture, focused test, runner, and the
new audit directory.  It showed no modification to migrations `001`–`009`,
historical function files, historical roles files, historical tests, frontend,
adapter, or API-route files.

The proposed v3 table family is structurally on the right path: folder type,
folder, object-level membership, normalized surface presentation/credit/
citation/search, corpus/TRACE availability, component manifest, build
receipt, validation, and manifest are distinct release-owned rows.  In
particular, the membership table has the requested same-release folder and
object composite foreign keys, role/ordinal uniqueness, and the two required
indexes.  The builder requires a caller-owned serializable transaction,
obtains a per-release advisory transaction lock, uses set-based inserts, and
the v3 validation/seal functions recompute from release-owned rows rather
than joining working tables after build.

Those positive static observations are **not** an execution PASS and do not
override the findings below.

## Findings

### P0-1 — public eligibility is not part of the v3 object source selection

`release.build_research_launch_snapshot_v3` copies
`release.research_release_object` from every
`raw.legacy_surface_ledger` row whose `import_disposition = 'accounted'`.
It neither joins `research.corpus_membership` nor requires
`membership_disposition = 'eligible'`, and it does not create an equivalent
release-owned eligibility snapshot.  It then creates surface presentation,
search documents, and public folder members from those copied objects.

The fixture makes its held sentinel a `legacy_surface_ledger` `held` row, so
it cannot detect an accounted source object that is held/excluded by the
canonical corpus policy.  Such an object could be published through the
presentation/search/member projections, contrary to the requirement that
held or excluded objects never enter a public member.  The builder must bind
its source selection and its bidirectional object/member parity to an
explicit eligible public corpus selection (and record all other
dispositions) before this phase can close.

### P1-1 — schema inventory is still stale

`database/schema-manifest.json` remains the old
`v49.phase2a-schema-manifest/v1`; it stops at migration `008` and its stable
file list omits replayed `009`, the new migration/function/roles/test, and
their hashes.  Updating `replay.sh` alone does not meet the required complete
schema inventory.  A new forward inventory/manifest must enumerate the full
effective replay order, including `009`, reader grants, v3 SQL, roles, and
tests, without rewriting historical receipts.

### P1-2 — legacy lifecycle remains publisher-callable for a v3 release

The new grants revoke the listed old piecemeal builder functions, but
`002_database_grants.sql` still grants the publisher `close_research_candidate`,
`validate_research_release`, and `seal_research_release`.  These legacy
functions use the historical canonical-reading validation path.  The v3
release path must explicitly prevent/revoke legacy candidate/validate/seal
entrypoints for releases bearing a v3 receipt, or prove an equivalent
release-version dispatch denial.  Merely having a new v3 function name is
not an enforceable production path boundary.

### P1-3 — required source accounting and test coverage are incomplete

The builder's double `EXCEPT` checks cover release objects and folder
membership only.  It does not record named disposition counts for proposed,
rejected, held, and excluded source rows, nor demonstrate source/copy parity
for surface presentation, credits, citations, search, corpus summary, and
TRACE availability.

The current focused test covers the 32-object happy path, proposed-held
fixture exclusion, one post-build/post-seal mutation denial, five injected
fault points, one API-reader projection denial, and a folder-label drift.
It does **not** yet cover the required cross-release FKs, missing
folder/object, rejected/superseded/wrong-kind sources, tuple mismatch,
duplicate/ordinal/role constraints, missing metadata, a second builder,
legacy-builder post-receipt denial, component/manifest tamper, two-session
serializable concurrency, or the 8,000/15,923-object performance ladder.
These gaps make the required P1=0 closure unavailable even if the first
P0 is corrected.

### P1-4 — audit package is not yet self-contained

At inspection time the new audit directory contained the Queue A reports
only.  It had no manifest, checksum file, command/test transcripts,
replay/hash receipts, or explicit candidate-tree self-containment result.
This is a release-evidence gap, not permission to fabricate execution
results.  Populate the additive package with non-ignored committed evidence,
then verify every manifest path and checksum against the candidate Git tree.

### P2-1 — source-content identity is narrower than the specified receipt

The stored `source_snapshot_sha256` currently hashes asset/batch/mapping and
policy identifiers but not a separately recorded sorted list of the selected
source-component hashes.  The component manifest does bind copied release
content, but the source side should be made explicit so the build receipt can
explain both source selection and copied components without relying on an
implementation inference.

## Independent result

```text
HISTORICAL_MIGRATIONS_001_009_EDITED=false
HISTORICAL_FUNCTIONS_EDITED=false
HISTORICAL_ROLES_OR_TESTS_EDITED=false
V3_STATIC_SCHEMA_DIRECTION=true
V3_RUNTIME_EXECUTION_VERIFIED=false
PUBLIC_ELIGIBILITY_P0_CONFIRMED=true
SCHEMA_INVENTORY_COMPLETE=false
LEGACY_LIFECYCLE_V3_DENIAL_VERIFIED=false
REQUIRED_CONCURRENCY_AND_PERFORMANCE_TESTS_VERIFIED=false
AUDIT_PACKAGE_TREE_SELF_CONTAINED=UNVERIFIED
AUDIT_CHECKSUM_MATCH=UNVERIFIED
P0_COUNT=1
P1_COUNT=4
P2_COUNT=1
PHASE_STATUS=PARTIAL_CHECKPOINT_REQUIRED
```

The phase cannot claim `RELEASE_PROJECTION_SNAPSHOT_CLOSED` while P0-1 is
present.  After a forward-only eligibility/projection correction and focused
database evidence, B1 should be re-run against the final candidate tree;
this report must remain additive rather than being rewritten to conceal the
current findings.

---

## Addendum — final-tree forward corrections and remaining partial gates

This addendum is intentionally appended; it does not alter the original
findings above.  It is a second bounded, read-only review of the current
uncommitted Phase 2C-S candidate.  B1 again did not start PostgreSQL, npm,
Next, TypeScript, a browser, or a generator.

### Additional command actually run

```text
python3 database/scripts/verify_schema_inventory_v3.py
git status --short; git diff --name-only; git diff --stat
sed -n / rg -n limited to 010, 016, 004, phase2s fixture/test,
schema-manifest-v3.json, and verify_schema_inventory_v3.py
```

The inventory verifier is read-only and returned:

```text
SCHEMA_INVENTORY_V3=PASS files=38
digest=22d1299906997cc989b5a78517eb29c6445da9f5373db21014ed2a1576a40a88
```

### P0-1 recovery verified statically

The original eligibility P0 is addressed in the new candidate tree:

1. `research.launch_snapshot_policy_v3` now pins a
   `public_corpus_version_id`.
2. The v3 builder selects public release objects by joining that exact corpus
   version with `research.corpus_membership.disposition = 'eligible'`; the
   object-level bidirectional `EXCEPT` parity uses the same predicate.
3. Folder metadata validation also applies the same eligible-corpus filter.
   Folder members can only reference those copied release objects and their
   same-release presentation row.
4. The fixture now makes its held sentinel deliberately **accounted** in the
   legacy ledger but `held` in the pinned corpus.  The focused SQL asserts it
   is absent from public objects and records the held count.
5. `release.research_launch_source_disposition_count_v3` stores named source
   disposition counts for corpus membership and folder assignments.  These
   counts enter `source_snapshot_sha256`; its trigger makes them immutable
   after the single-use build receipt.

This is the required fail-closed public eligibility boundary: an accounted
row is not by itself public.  `PUBLIC_ELIGIBILITY_P0_CONFIRMED=false`.

### Legacy lifecycle isolation verified statically

`004_release_projection_snapshot_grants.sql` now revokes publisher EXECUTE
on `close_research_candidate`, `validate_research_release`, and
`seal_research_release`, in addition to revoking the piecemeal construction
functions.  It grants the publisher only the versioned v3 build, validate,
and seal entrypoints.  This prevents the historical canonical-reading
lifecycle from becoming an alternate production path for a v3 release while
leaving historical files unchanged.

`LEGACY_LIFECYCLE_V3_DENIAL_STATIC=true`.

### Forward schema inventory verified

The historical `database/schema-manifest.json` is still byte-preserved.
The new `database/schema-manifest-v3.json` is additive and lists migrations
001 through 010, functions 001 through 016, roles 001 through 004, the
existing reader grants, v3 replay/hash runner, fixture, and focused test.
The supplied read-only verifier confirms the live file digest above and
explicitly requires entries for 009, 010, 016, 003/004 grants, and test 005.

`SCHEMA_INVENTORY_COMPLETE_STATIC=true`.

### Remaining P1 gates — intentionally not completed in this checkpoint

1. **Concurrent serializable builder test.** No two-session test is present
   or evidenced that demonstrates either a wholly pre-write snapshot or a
   `40001` rollback when a concurrent writer changes folder membership.
2. **Performance ladder.** The runner executes fresh replay and the
   32-object focused test only.  It does not execute or evidence the required
   one-time 8,000-object and 15,923-object/47,982-membership set-based
   builders within their budgets.  Per the phase stop rule, these were not
   substituted with estimates or unbounded waits.
3. **Full negative constraint matrix.** The focused test still lacks direct
   evidence for all specified cross-release/missing-reference, rejected /
   superseded / wrong-kind, duplicate/ordinal/role, second-builder,
   legacy-builder-after-receipt, and manifest-tamper cases.  Existing table
   constraints and guards are directionally correct, but a static read is not
   a substitute for the mandated negative execution matrix.
4. **Final audit-package self-containment.** At this addendum's inspection
   point the audit directory did not yet contain its final manifest, checksums
   and execution transcripts.  B1 therefore cannot certify package-tree
   self-containment or checksum coverage until those artifacts have been
   written and checked against the Git candidate tree.

### Addendum verdict

```text
HISTORICAL_MIGRATIONS_001_009_EDITED=false
HISTORICAL_FUNCTIONS_EDITED=false
HISTORICAL_ROLES_OR_TESTS_EDITED=false
PUBLIC_ELIGIBILITY_P0_CONFIRMED=false
LEGACY_LIFECYCLE_V3_DENIAL_STATIC=true
SCHEMA_INVENTORY_V3_VERIFIER_EXIT=0
SCHEMA_INVENTORY_COMPLETE_STATIC=true
CONCURRENT_SNAPSHOT_TEST_VERIFIED=false
PERFORMANCE_8000_VERIFIED=false
PERFORMANCE_15923_47982_VERIFIED=false
FULL_NEGATIVE_MATRIX_VERIFIED=false
AUDIT_PACKAGE_TREE_SELF_CONTAINED=UNVERIFIED_AT_ADDENDUM_TIME
P0_COUNT=0
P1_COUNT=4
P2_COUNT=1
PHASE_STATUS=PARTIAL_CHECKPOINTED
```

The authorized forward model is no longer blocked by the original public
eligibility P0.  The phase nevertheless remains a partial checkpoint until
the four P1 gates above have actual database/audit evidence; no static source
review should be promoted to a full snapshot-closure PASS.
