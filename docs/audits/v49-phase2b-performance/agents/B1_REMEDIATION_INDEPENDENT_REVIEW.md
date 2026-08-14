# B1 independent remediation review

## Receipt

```text
AGENT=B1
QUEUE=B_INDEPENDENT_ACCEPTANCE
REVIEW_MODE=STATIC_READ_ONLY_WITH_EXISTING_RECEIPT_REVIEW
REVIEWED_HEAD=6b918dd2ebd9af6f9a8fca6edbe6bbbf7de41320
REMEDIATION_FILE=database/data-migrations/v48-to-v49/001_performance_remediation.sql
REMEDIATION_FILE_SHA256=558ac2c8e8bf36166290bf588035c8822f8ff17ae481e30ebff98a8dc6715e48
POSTGRES_STARTED=false
POSTGRES_CONNECTED=false
IMPORTER_STARTED=false
EXTRACTOR_STARTED=false
BUILD_STARTED=false
CORE_IMPLEMENTATION_CHANGED=false
REPORT_ONLY_WRITE=true
INITIAL_VERDICT=CONDITIONAL_PASS_NO_P0
INITIAL_P0_FINDING_COUNT=0
INITIAL_P1_INTEGRATION_FINDING_COUNT=2
INITIAL_P2_EVIDENCE_FINDING_COUNT=1
CONSTRAINTS_OR_TRIGGERS_REMOVED=0
CONSTRAINTS_OR_TRIGGERS_DISABLED=0
FUNCTION_SECURITY_WEAKENED=false
TRANSACTION_ATOMICITY_WEAKENED=false
FROZEN_PHASE2A_FILES_CHANGED=false
INITIAL_FULL_REPLAY_INTEGRATION_READY=false
```

The remediation SQL is a semantically sound, forward-only replacement for
the two quadratic validation paths.  I found no P0 code defect and no
constraint, trigger, role, privilege, Seal/CAS, rights, or transaction
weakening.  The four indexes match the typed access paths used by the new
queries.  Existing bounded receipts show that all named constraints return
success and roll back cleanly after the replacement.

The code review is therefore a pass.  Replay integration is not yet an
unconditional pass: the checked-in fresh-replay runner does not currently
apply the new forward migration, and the README still claims that this
directory does not replace functions.  In addition, the post-fix probe files'
standalone `EXPLAIN` statements still explain the old quadratic expressions,
not the new typed SQL.  Exact closing actions are listed below.

## Scope and evidence

I reviewed:

- `database/data-migrations/v48-to-v49/001_performance_remediation.sql` in
  full;
- the original `rights.enforce_one_current_history_leaf()` at
  `database/functions/006_normative_closure.sql:559-624`;
- the original `rights.validate_one_delivery_assessment(uuid)` at
  `database/functions/001_deferred_constraints.sql:1893-2144`;
- `rights.assessment_subject_key(uuid)`,
  `rights.enforce_rights_assessment()`, and
  `rights.subject_applies_to_delivery(...)` in the frozen deferred-constraint
  file;
- typed rights tables, bridge tables, delivery links, keys, and indexes in
  `database/migrations/003_research_rights.sql`;
- all six existing post-fix P1 receipts at scales 50, 250, and 1,000, plus the
  bounded pre-fix receipts;
- the current `run-rehearsal.sh`, migration README, and changed loader boundary
  to determine whether the forward migration is part of every fresh replay.

I did not start or connect to PostgreSQL and did not execute any importer,
extractor, build, or schema mutation.  Database execution evidence cited here
was generated earlier by the controller.

The frozen files are byte-identical to `HEAD`:

```text
database/functions/001_deferred_constraints.sql
  working tree: 52aedc965690785eebd0a9ec9aa921bcad23f201a65ab085b17efce3878d07f6
  HEAD:         52aedc965690785eebd0a9ec9aa921bcad23f201a65ab085b17efce3878d07f6
database/functions/006_normative_closure.sql
  working tree: 95a6fc5302b619459f9d4484473676563e41d79b299d830c8324da7ed49523a8
  HEAD:         95a6fc5302b619459f9d4484473676563e41d79b299d830c8324da7ed49523a8
```

This confirms the required forward-migration discipline at the source-file
level: neither frozen Phase 2A function file was edited in place.

## Findings requiring closure

### B1-P1-01 — fresh replay does not yet apply the forward migration

`database/data-migrations/v48-to-v49/run-rehearsal.sh` currently invokes:

1. `database/scripts/replay.sh` (the frozen Phase 2A chain),
2. `import.py`, and
3. `verify.py`.

Repository search found no invocation or reference to
`001_performance_remediation.sql`.  Thus a caller following the documented
reproduction path receives the old quadratic functions unless the controller
performs an undocumented manual step.  A manual diagnostic application is not
a deterministic Fresh A/Fresh B contract.

Close this finding before the scale ladder or any full replay is accepted by
making the fresh schema path apply the forward migration exactly once, after
the frozen Phase 2A replay and before population.  It must execute as the
schema owner (or an equivalently bounded owner), with `ON_ERROR_STOP`, in the
same code path for all scale fixtures and Fresh A/B.  Duplicate application
should fail rather than be silently ignored.  Capture its resulting schema
hash in the replay receipt.

This is an integration blocker, not a defect in the migration SQL itself.

### B1-P1-02 — population README contradicts the forward migration

`database/data-migrations/v48-to-v49/README.md` states that this directory
"does not modify ... functions" and describes the runner as replaying Phase 2A
and then immediately loading population.  The new forward migration correctly
replaces two functions, so that statement and reproduction sequence are now
stale.

Close this finding by documenting the forward-only function replacement, its
ordering, the preservation of the base schema hash, and the new deterministic
post-forward-migration schema hash.  Do not rewrite the historical Phase 2A
description or receipts.

### B1-P2-01 — post-fix `EXPLAIN` blocks still target legacy SQL

The named-constraint timings in the post-fix receipts are valid: they execute
the replacement functions through the unchanged constraint triggers.  But the
standalone `EXPLAIN (ANALYZE, BUFFERS, WAL, ...)` statements in
`p1_rights_leaf_probe.sql:65-75` and
`p1_delivery_validation_probe.sql:129-156` explicitly reproduce the old
`assessment_subject_key()` / whole-table `subject_applies_to_delivery()`
queries.  Consequently, `Seq Scan` nodes in the post-fix log EXPLAIN sections
are not execution plans for the remediated queries and must not be cited as
post-fix index-plan proof.

Close this evidence finding in P2/B2 by explaining the actual typed branch (or
an equivalent SQL extraction of it) with `ANALYZE, BUFFERS, WAL` and showing
the target-leading typed index used at meaningful scale.  The existing named
constraint wall-time receipts remain usable.

## Constraint and trigger preservation

The forward migration contains only:

- one explicit `BEGIN`/`COMMIT` transaction;
- four ordinary B-tree `CREATE INDEX` statements;
- `CREATE OR REPLACE FUNCTION` for the two identified functions.

It contains none of the following:

```text
ALTER TABLE ... DROP CONSTRAINT
DROP TRIGGER / DROP FUNCTION / DROP INDEX / DROP TABLE
DISABLE TRIGGER
session_replication_role
NOT VALID
ON CONFLICT DO NOTHING
ALTER DEFAULT PRIVILEGES / GRANT / REVOKE
SECURITY DEFINER
partial COMMIT
```

No constraint or trigger DDL is present.  Both replacements keep the exact
function identity, argument type, return type, PL/pgSQL language, and
`search_path=pg_catalog`.  Both remain ordinary invoker-security functions
with default PL/pgSQL volatility, matching the originals.  `CREATE OR REPLACE`
therefore preserves the existing function object ownership/ACL and all trigger
dependencies; it does not recreate or detach a trigger.

The migration does not touch release functions, Seal/CAS functions, public
views, roles, rights enums, delivery ranking, takedown logic, or append-only
guards.

## One-current-leaf equivalence

### Original semantic key

The original function identifies one rights-assessment subject through:

```text
assessment_subject_key(id) = subject_kind || ':' || typed_target_uuid
```

`rights.assessment_subject_key()` first reads `subject_kind`, then reads the
target from exactly one of the following typed tables:

| subject kind | typed table | target column |
|---|---|---|
| `provider_object` | `rights_assessment_provider_object` | `provider_object_id` |
| `external_visual_reference` | `rights_assessment_visual_reference` | `external_visual_reference_id` |
| `digital_representation` | `rights_assessment_representation` | `digital_representation_id` |
| `visual_locator` | `rights_assessment_locator` | `visual_locator_id` |

The replacement makes that same four-way dispatch explicit.  It obtains
`NEW`'s target from the corresponding typed table, scans that same table by
the target, joins assessment IDs to `rights.rights_assessment`, filters the
same `subject_kind`, and excludes rows superseded by any newer assessment.
The target plus explicit kind is exactly the original composite text key,
without the non-sargable function call.

The typed tables have `rights_assessment_id` primary keys, so the initial
`SELECT ... INTO v_target` returns at most one row.  If the typed row is absent,
the target remains null and the count is zero, causing the same
`RIGHTS_HISTORY_REQUIRES_ONE_CURRENT_LEAF` rejection.  If a malformed row has
the wrong typed table, the separate deferred
`RIGHTS_ASSESSMENT_EXACTLY_ONE_TYPED_SUBJECT_REQUIRED` invariant rejects the
transaction.  On every valid database state, the old and new leaf sets are
identical.

The supersession parent/time test at the top of the rights-assessment branch
is unchanged.  The provider-policy, delivery-assessment, and attribution
branches are byte-for-byte identical to the frozen implementation.  The final
`v_count <> 1` check and exception code/message are also unchanged.

Verdict: equivalent invariant, materially cheaper access path, no weakening.

## Delivery-completeness equivalence

The expensive original completeness proof evaluates
`rights.subject_applies_to_delivery()` for every rights assessment.  The
replacement constructs the same applicable-assessment set by starting from
one delivery and exposing typed equijoins:

| subject kind | original applicability rule | replacement path |
|---|---|---|
| `provider_object` | subject equals the provider object of the bridge's external reference | bridge -> external reference -> typed provider-object assessment |
| `external_visual_reference` | subject equals the bridge's external reference | bridge -> typed visual-reference assessment |
| `digital_representation` | delivery has a qualified locator represented by the subject for the bridge's external reference | delivery qualification -> locator representation (same external reference) -> typed representation assessment |
| `visual_locator` | delivery qualifies the subject locator and it belongs to the bridge's external reference | delivery qualification -> locator (same external reference) -> typed locator assessment |

The bridge and delivery IDs are identical to the variables passed to the
original helper.  Each branch joins back to `rights_assessment` and checks the
matching `subject_kind`, which is redundant for a valid typed shape but is
fail-closed for malformed intermediate states.  `UNION` is correct: the old
logic is a set-membership predicate per unique assessment, so duplicate
reachability paths must not create additional semantic rows.

The first validation arm still rejects any linked assessment that:

1. is not applicable to this delivery,
2. postdates the delivery decision, or
3. is no longer a current leaf.

The second validation arm still rejects any applicable current-leaf
assessment lacking a link to this delivery.  It intentionally does not add an
`assessed_at` predicate, matching the original completeness rule; the linked
validity arm remains responsible for postdating.

Everything after the rights-completeness block, from the rights cap through
policy completeness, attribution, takedown, fail-closed delivery rank, and
healthy typed locator requirements, is byte-for-byte identical to the frozen
function.  The preamble and future-assessment rejection are also identical.

Verdict: equivalent set semantics on valid states, fail-closed on invalid
typed shape, no rights/public-delivery policy change.

## Index review

Before remediation, all four typed assessment tables had a primary key whose
leading column was `rights_assessment_id`.  That supports assessment-to-target
lookup but cannot efficiently answer target-to-assessment lookup.  The new
indexes add precisely the missing reverse direction:

```text
rights.rights_assessment_provider_object
  (provider_object_id, rights_assessment_id)
rights.rights_assessment_visual_reference
  (external_visual_reference_id, rights_assessment_id)
rights.rights_assessment_representation
  (digital_representation_id, rights_assessment_id)
rights.rights_assessment_locator
  (visual_locator_id, rights_assessment_id)
```

The first column is the equality target used by both replacement functions;
the second is the join/output assessment ID.  This supports an index or
index-only scan and avoids heap-wide enumeration.  It also covers all four
schema-valid subject kinds rather than optimizing only the currently populated
external-reference kind.

The indexes are non-unique because multiple assessment history rows may
legitimately address the same subject.  They have no partial predicate, so
they cover current and superseded rows alike; current-leaf status remains a
constraint predicate, not an index-side semantic shortcut.  Ordinary index
creation (not `CONCURRENTLY`) is correct here because the forward migration is
required to be atomic and runs against a fresh empty schema before population.

Verdict: correct columns, direction, cardinality semantics, and transaction
form.

## Existing bounded runtime evidence

All cited probes finish with `ROLLBACK`; they do not create population residue.
The leaf constraint changed from deterministic superlinear behavior to a
bounded indexed path:

| scale | pre-fix named seconds | post-fix named seconds |
|---:|---:|---:|
| 50 | 1.000482 | 0.015495 |
| 250 | 60.978052 | 0.260143 |
| 1,000 | not run (bounded stop) | 0.200152 |

The pre-fix 50 -> 250 slope is approximately exponent 2.55.  The post-fix
1,000 event group completes in about 0.20 seconds.  The non-monotonic 250/1,000
pair is consistent with cache/setup noise at subsecond duration and must not
replace the formal P2 ladder.

The three delivery constraints also complete through their unchanged trigger
identities after the function replacement:

| named constraint | scale 50 pre | scale 50 post | scale 1,000 post |
|---|---:|---:|---:|
| `delivery_assessment_validation` | 3.489642 s | 0.449280 s | 5.893404 s |
| `delivery_rights_validation` | 1.582924 s | 0.661508 s | 5.167927 s |
| `delivery_policy_validation` | 1.429160 s | 0.375984 s | 4.477189 s |

At scale 1,000, each group remains under six seconds.  These results are
consistent with removal of the assessment-table cross product.  They prove
bounded trigger execution, not the P3 gate: the required stratified
50/250/1,000/4,000/8,000 fixture results, complete importer stages, digests,
and final `SET CONSTRAINTS ALL IMMEDIATE` omission check are outside B1's
static review.

## Load order and named constraints

The population loader retains its single transaction and calls
`SET CONSTRAINTS ALL DEFERRED` before inserting the reciprocal
`core.archive_object` / `raw.legacy_surface_ledger` SCC.  The durable rights
order is dependency-correct: visual reference/bridge/locator, observation and
typed observation, assessment and typed assessment/evidence, policy, delivery,
then delivery rights and policy links.

At the instant of this review, the loader still ends with only
`SET CONSTRAINTS ALL IMMEDIATE`; its in-progress instrumentation adds durable
insert/parity markers but no checked-in named constraint groups yet.  This
does not weaken atomicity or constraints, but it does not satisfy the requested
named-stage observability contract.  The controller must split validation into
schema-qualified named groups with timing checkpoints and retain one final
`SET CONSTRAINTS ALL IMMEDIATE` omission check.  This condition overlaps
B1-P1-01 because the instrumented path and the forward migration must be wired
into the same deterministic replay contract.

## Atomicity and privilege review

The forward migration is one transaction and has `\set ON_ERROR_STOP on`.
Any index or function-definition error aborts the entire migration.  No
concurrent index, partial commit, trigger suppression, replication-role
override, or deferred `NOT VALID` object appears.

The replacement functions preserve invoker security and the hardened
`pg_catalog` search path.  No `SET ROLE`, `RESET ROLE`, `GRANT`, or `REVOKE`
appears.  The new joins read the same rights tables already read by the
functions; no public-facing raw locator or source table is introduced.  The
loader's population transaction remains distinct from the schema-forward
migration, as it should: atomicity means each fresh population is one
all-or-nothing transaction, not that immutable schema creation and population
must be one transaction.

Verdict: no privilege expansion and no population-transaction weakening.

## B1 gate conclusion

```text
B1_CODE_REVIEW_PASS=true
B1_NO_P0=true
B1_CONSTRAINT_STRENGTH_PRESERVED=true
B1_TRIGGER_IDENTITY_PRESERVED=true
B1_TYPED_JOIN_EQUIVALENCE=true
B1_INDEX_DIRECTION_CORRECT=true
B1_FORWARD_MIGRATION_ATOMIC=true
B1_FROZEN_PHASE2A_FILES_UNCHANGED=true
B1_INITIAL_FULL_REPLAY_INTEGRATION_READY=false
```

No P0 finding prevents the controller from continuing remediation work or the
bounded scale ladder.  Before accepting P2/P3 and authorizing Fresh A, the
controller must close B1-P1-01, B1-P1-02, add named constraint-group
observability plus a final `ALL IMMEDIATE` check, and ensure B2 captures actual
post-fix plans.  A later B1 refresh may change
the closing `FULL_REPLAY_INTEGRATION_READY` to true without revisiting the already
accepted function semantics.

## Closing review refresh

This section is a later, independent closing pass over the completed replay
integration.  It supersedes only the provisional integration verdict above;
the original function-equivalence analysis and its evidence remain unchanged.
No database, importer, extractor, or build was started for this refresh.

### Closing receipt

```text
CLOSING_REVIEW_MODE=STATIC_READ_ONLY_WITH_EXISTING_PLAN_RECEIPTS
CLOSING_VERDICT=PASS_NO_P0_OR_P1
CLOSING_P0_FINDING_COUNT=0
CLOSING_P1_FINDING_COUNT=0
CLOSING_P2_SCOPE_NOTE_COUNT=2
B1_CODE_REVIEW_PASS=true
B1_CONSTRAINT_STRENGTH_PRESERVED=true
B1_TRIGGER_IDENTITY_PRESERVED=true
B1_TYPED_JOIN_EQUIVALENCE=true
B1_INDEX_DIRECTION_CORRECT=true
B1_FORWARD_MIGRATION_ATOMIC=true
B1_FRESH_RUNNER_APPLIES_FORWARD_MIGRATION=true
B1_ATTESTATION_REUSE_PATH_REVIEWED=true
B1_RUNTIME_SQL_OUTSIDE_STAGING=true
B1_IMPORT_STREAMING=true
B1_ATOMIC_SINGLE_POPULATION_TRANSACTION=true
B1_TARGETED_ANALYZE_COUNT=17
B1_NAMED_CONSTRAINT_GROUP_COUNT=11
B1_FINAL_ALL_OMISSION_CHECK=true
B1_DYNAMIC_TARGET_INDEX_COVERAGE=1/4
B1_DYNAMIC_TARGET_INDEX=rights.rights_assessment_visual_reference_target_idx
B1_STATIC_TARGET_INDEX_COVERAGE=4/4
B1_FROZEN_PHASE2A_FILES_UNCHANGED=true
FULL_REPLAY_INTEGRATION_READY=true
FULL_REPLAY_AUTHORIZED=false
P3_GO_GATE_PASSED=false
```

The reviewed closing inputs and hashes were:

```text
run-rehearsal.sh
  af65a1f9759a7e74dd43f91de3ad65fc318dc5f4093bd8aa394efe95ceae27a4
README.md
  17f126dcb976e65b74f4b7932be3d30b3defe0c5c1a29cd1fbacf157d164a443
load.sql
  446ed05badeb6ee2c8d62abbe95b54c9a92f3968cc84bfbede5885063518fa5c
import.py
  d37915a81551a048d8bc47d99775ae9083b5f4ff75fd42718b146b8cc1fc03d8
P1_RIGHTS_LEAF_POST_FIX_PLAN_1000.log
  c6751c23bbd957a5330c1a2800ff5ab96ec6d9750a44af7165f5a0d5c83e272e
P1_DELIVERY_POST_FIX_PLAN_1000.log
  185899544f85ce56ec42db3f41377a19a771107f7be856da239995d5fc3e7234
```

Shell syntax for `run-rehearsal.sh` and Python compilation of `import.py`
passed in read-only checks.  A static loader scan found 17 `ANALYZE`
statements, 11 named business constraint groups, one separately timed final
`ALL` group, exactly one `SET CONSTRAINTS ALL IMMEDIATE`, and no trigger
disable, replication-role override, `NOT VALID`, conflict swallowing, or
commit inside `load.sql`.

### Closure of B1-P1-01 — deterministic forward application

`run-rehearsal.sh` now implements one fixed fresh-schema sequence:

1. run the frozen `database/scripts/replay.sh` Phase 2A chain;
2. connect as the disposable admin and `SET ROLE
   gda_v49_phase2a_schema_owner`;
3. apply `001_performance_remediation.sql` with `ON_ERROR_STOP`;
4. invoke `import.py` with the immutable staging attestation, task-owned
   runtime directory, streamed log, timing receipt, and 1,200-second
   per-statement constraint ceiling;
5. invoke `verify.py` against the remediated schema.

The forward migration itself retains its explicit `BEGIN`/`COMMIT`, so a
failed index or function replacement cannot leave a partially remediated
schema.  It is not hidden in or copied into a frozen Phase 2A file.  The
importer then checks the exact deterministic remediated schema hash before any
population write and checks it again after commit.

The previous P1 integration blocker is closed.

### Closure of B1-P1-02 — documentation contract

The README now distinguishes:

- the unchanged frozen Phase 2A schema and base hash;
- the separate forward-only Phase 2B-P function/index migration;
- the distinct deterministic remediated schema hash;
- content-addressed staging-attestation reuse;
- task-owned runtime SQL/log paths;
- named constraint groups and the final all-constraint omission check.

Its reproduction example now requires the staging attestation, runtime
directory, importer receipt, and verifier report.  It no longer claims that
the data-migration directory never replaces functions.

The previous P1 documentation blocker is closed.

### Loader integration and constraint observability

The durable insert order is unchanged except for observability and fixture-
parameterized parity counts.  It remains dependency-correct and retains all
canonical rows, including raw field literals.  Parity is checked before any
constraint group becomes immediate.

The following 17 populated tables receive targeted statistics before deferred
validation:

```text
raw.migration_batch
raw.legacy_surface_ledger
core.entity
core.archive_object
provenance.canonical_assignment
provenance.assignment_folder_membership
rights.object_visual_reference
rights.visual_locator
rights.rights_observation
rights.rights_observation_visual_reference
rights.rights_assessment
rights.rights_assessment_visual_reference
rights.rights_assessment_observation
rights.provider_policy_evaluation
rights.delivery_assessment
rights.delivery_rights_assessment
rights.delivery_policy_evaluation
```

The 11 business groups are schema-qualified and individually bounded by the
transaction-local constraint timeout:

| order | group | invariant boundary |
|---:|---|---|
| 1 | `raw_core_cycle` | migration authority, sole deferred FK, reciprocal ledger/object SCC, entity subtypes |
| 2 | `folder_assignment_shape` | assignment parent/subtype/supersession |
| 3 | `visual_bridge_and_locator` | visual bridge decision and locator history |
| 4 | `rights_observation` | observation typed shape and history |
| 5 | `rights_assessment_shape_support` | assessment typed shape, evidence, and supersession |
| 6 | `rights_assessment_current_leaf` | remediated one-current-leaf constraint |
| 7 | `provider_policy` | policy validation, supersession, and current leaf |
| 8 | `delivery_parent_validation` | remediated parent-row delivery validation |
| 9 | `delivery_rights_validation` | remediated rights-link delivery validation |
| 10 | `delivery_policy_validation` | remediated policy-link delivery validation |
| 11 | `delivery_history_and_rule` | delivery supersession/current leaf/rule pair |

Each group records start time/backend WAL position and emits an end marker with
wall seconds and WAL bytes.  Group 12 is deliberately not another selected
family: it is the required, separately timed
`final_all_omission_check`, implemented by one final
`SET CONSTRAINTS ALL IMMEDIATE`.  Therefore any unlisted deferrable constraint
still executes before commit.  No constraint is disabled, removed, marked
not-valid, or left deferred past commit.

The previous named-stage observability blocker is closed.

### Staging attestation and frozen-cache boundary

For the full frozen staging path, `require_stage()` completes before the first
PostgreSQL connection.  It still verifies the canonical Candidate, base
schema, implementation-base commit, extractor, mapping, semantic metrics,
35-file allowlist, bundle binding, mapping row, and fixed attestation identity.
The reusable attestation path then:

- canonicalizes and hashes the attestation payload against the fixed
  `11742e9a...` identity;
- binds the fixed staging manifest, Candidate hash, base schema, and exact
  resolved staging path;
- hashes the small staging manifest;
- checks all 35 descriptor names, manifest sizes/hashes, filesystem type,
  current size, and `mtime` not newer than the original verification.

It does not reread and rehash the 4.5 GB descriptor payload or repeat the
multi-million-row semantic occurrence scan.  Direct full hashing remains
available for bounded failure fixtures; fault injection is explicitly
incompatible with the inherited full-staging attestation.

Runtime SQL is created through `NamedTemporaryFile` inside the explicitly
supplied runtime directory and removed in `finally`.  The full runner restricts
that directory to `/private/tmp` or `/tmp` and forces its importer log into the
same scratch directory.  Before staging validation or any database connection,
the importer resolves both its log and optional receipt path, rejects either
the stage itself or any descendant of the frozen stage, and requires each
output parent directory to exist.  Thus runtime SQL, streamed logs, and
importer receipts cannot be created in the frozen cache through a
misconfigured importer invocation.

Controller condition: the separately supplied verifier-report path must also
remain task-owned and outside the frozen stage.  The audited runner does not
invent that path; its invocation contract requires the controller to provide
it explicitly.

### Streaming and population transaction

The importer performs only read-only ownership, schema-hash, and idempotency
checks before the writer session.  It then starts one `psql` process and one
session.  The generated runtime SQL has exactly one population `BEGIN`, with
the following inside it:

- transaction-local expected counts, fault setting, and constraint timeout;
- `SET ROLE` to the schema owner;
- creation of temporary staging/runtime helpers;
- all 28 `\copy` operations;
- every durable insert and parity assertion;
- targeted `ANALYZE`;
- all named constraint groups;
- the final all-constraint omission check;
- exactly one `COMMIT`.

Any COPY, insert, injected fault, parity failure, `ANALYZE`, or constraint
failure is covered by `ON_ERROR_STOP` and occurs before that one commit.  There
is no intermediate durable commit.  A post-commit marker is required before
the importer reports `COMMITTED`.

The child output is streamed line by line to both stdout and a flushed
task-owned log instead of being buffered until completion.  The receipt
captures backend PID, overall wall/child CPU, stage markers, and named-group
timings.  Runtime SQL is deleted on both success and failure.

Verdict: the modified importer retains a single atomic population transaction
and now provides the required live named-stage boundary.

### Closure of B1-P2-01 — actual post-fix plans

The replacement probe SQL now explains the actual typed branch rather than
the legacy `assessment_subject_key()` or whole-table
`subject_applies_to_delivery()` expressions.

At scale 1,000, the leaf plan contains:

```text
Node Type=Index Only Scan
Index Name=rights_assessment_visual_reference_target_idx
Shared Read Blocks=0
Temp Written Blocks=0
WAL Bytes=0
Execution Time=0.379 ms
```

It joins through the assessment primary key and checks current-leaf status
through the unique supersession index.  The unchanged named constraint also
completes successfully and the probe ends in `ROLLBACK`.

The delivery-completeness plan contains:

```text
Node Type=Index Only Scan
Index Name=rights_assessment_visual_reference_target_idx
Shared Read Blocks=0
Temp Written Blocks=0
WAL Bytes=0
Execution Time=0.129 ms
```

It starts from the delivery's object-visual-reference primary key, uses the
target-leading typed assessment index, joins assessment/current-leaf indexes,
and checks the delivery-rights primary key.  All three delivery named
constraints complete and the probe ends in `ROLLBACK`.

Dynamic scope limitation: both the frozen canonical population and these P1
fixtures contain `external_visual_reference` assessments.  Therefore the
runtime plans dynamically exercise one of the four new indexes, not all four.
They do not claim dynamic coverage for:

```text
rights_assessment_provider_object_target_idx
rights_assessment_representation_target_idx
rights_assessment_locator_target_idx
```

B1's earlier static review established the correct leading target and joined
assessment ID for all four definitions and all four typed CASE/UNION branches.
The unexercised three are not on the canonical replay path, so their lack of
dynamic P1 coverage is a stated P2 scope limitation rather than a P0/P1
population blocker.  A future four-kind synthetic invariant suite may add
dynamic coverage without changing Fresh A/B semantics.

### Residual conditions and final B1 verdict

No residual P0 or P1 finding remains in B1's assigned integration scope.
`FULL_REPLAY_INTEGRATION_READY=true` means the implementation is ready for the
bounded scale/failure gates.  It does **not** authorize Fresh A and is not a
substitute for P3.

Before the controller can set `FULL_REPLAY_AUTHORIZED=true`, independent B2/B3
and the controller must still prove, at minimum:

- fixed-fixture rerun of all 11 failure cases for the changed importer path;
- successful ordered 50/250/1,000/4,000/8,000 stratified scale ladder;
- maximum-three-scale growth exponent and full-size projection within budget;
- counts, deterministic IDs, logical digest, roles/permissions, rollback, and
  zero-residue parity;
- no Queue B P0; and
- controller-supplied runtime, receipt, and verifier paths outside frozen
  staging.

Those are P2/P3 gates, not defects in the integrated remediation.  B1's final
closing verdict is:

```text
B1_CLOSING_REVIEW=PASS
B1_RESIDUAL_P0=NONE
B1_RESIDUAL_P1=NONE
FULL_REPLAY_INTEGRATION_READY=true
FULL_REPLAY_AUTHORIZED=false
```
