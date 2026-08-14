# Phase 2B-P performance remediation

## Receipt

```text
REMEDIATION_STATUS=PASS
ROOT_CAUSE_IDENTIFIED=true
ROOT_CAUSE_CONSTRAINTS=rights.rights_assessment_one_current_leaf,rights.delivery_assessment_validation,rights.delivery_rights_validation,rights.delivery_policy_validation
FORWARD_MIGRATION=database/data-migrations/v48-to-v49/001_performance_remediation.sql
FORWARD_MIGRATION_SHA256=558ac2c8e8bf36166290bf588035c8822f8ff17ae481e30ebff98a8dc6715e48
BASE_SCHEMA_HASH=4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105
FINAL_SCHEMA_HASH=aa8cb0af7b61931e51f1f71ed2e4cf0d10b178669de16807871819b330742e8b
SCHEMA_HASH_DETERMINISTIC=true
CONSTRAINTS_DISABLED=false
CONSTRAINTS_REMOVED=false
NOT_VALID_LEFT_BEHIND=false
ATOMIC_SINGLE_TRANSACTION=true
STAGING_ATTESTATION_REUSED=true
EXTRACTOR_RERUN=false
UPDATED_CODE_FIXTURE_FAILURE_PROBES=11/11
B1_CLOSING_REVIEW=PASS_NO_P0_OR_P1
B2_CLOSING_REVIEW=GO_NO_P0_OR_P1
PERFORMANCE_BUDGET_MET=true
FULL_REPLAY_AUTHORIZED=true
PRODUCTION_DATABASE_TOUCHED=false
PRODUCTION_MIGRATION_EXECUTED=false
```

This remediation removes the two deterministic quadratic validation paths
that blocked the inherited Fresh A attempt.  It does so with one forward-only
schema migration, typed target-leading indexes, set-based validation, targeted
statistics, named constraint checkpoints, and content-addressed staging
attestation reuse.  It does not weaken a constraint or change canonical data
semantics.

The frozen Phase 2A DDL, function files, manifest, and base hash remain
unchanged.  The remediated schema has its own deterministic hash and was used
unchanged by the bounded ladder and both full replays.

## Root cause removed

The inherited loader queued roughly 523,536 deferred constraint events and
then exposed them through one opaque `SET CONSTRAINTS ALL IMMEDIATE` boundary.
Two rights paths contained global assessment scans.

### One-current-leaf path

`rights.rights_assessment_one_current_leaf` invokes
`rights.enforce_one_current_history_leaf()`.  The frozen implementation scanned
all `rights.rights_assessment` rows for every inserted assessment and evaluated
the non-sargable `rights.assessment_subject_key()` function on candidate rows.
For the canonical 15,788 assessments, the minimum candidate comparison count
was:

```text
15,788 * 15,788 = 249,260,944
```

The bounded pre-fix probe rose from 1.000482 seconds at 50 assessments to
60.978052 seconds at 250, an observed exponent of approximately 2.55.

### Delivery-completeness path

The three populated delivery triggers:

```text
rights.delivery_assessment_validation
rights.delivery_rights_validation
rights.delivery_policy_validation
```

all invoke `rights.validate_one_delivery_assessment(uuid)`.  Its frozen
completeness proof scanned the entire assessment table and called
`rights.subject_applies_to_delivery()` for each candidate.  Three event
families across 15,788 deliveries implied approximately 747,782,832 candidate
assessment examinations before nested helper queries.

The root cause was therefore the exact constraint/function/access-path pair,
not PostgreSQL generally, the sole deferred FK, or healthy CPU growth.

## Forward migration

`001_performance_remediation.sql` runs after every fresh replay of the frozen
Phase 2A chain and before population.  It is one `BEGIN`/`COMMIT` transaction
with `ON_ERROR_STOP` and contains only four indexes plus two
`CREATE OR REPLACE FUNCTION` definitions.

### Four reverse typed-subject indexes

| Index | Relation and columns | Purpose |
|---|---|---|
| `rights_assessment_provider_object_target_idx` | `rights.rights_assessment_provider_object(provider_object_id, rights_assessment_id)` | provider object -> assessment history |
| `rights_assessment_visual_reference_target_idx` | `rights.rights_assessment_visual_reference(external_visual_reference_id, rights_assessment_id)` | visual reference -> assessment history |
| `rights_assessment_representation_target_idx` | `rights.rights_assessment_representation(digital_representation_id, rights_assessment_id)` | representation -> assessment history |
| `rights_assessment_locator_target_idx` | `rights.rights_assessment_locator(visual_locator_id, rights_assessment_id)` | locator -> assessment history |

The existing primary keys begin with `rights_assessment_id`; they support the
forward lookup but not target-to-history lookup.  The new indexes expose the
missing direction without imposing uniqueness: multiple immutable history
rows may legitimately refer to the same target.

The canonical population uses the external-visual-reference kind.  Its direct
scale-1,000 plans use
`rights_assessment_visual_reference_target_idx` as an index-only scan.  The
leaf and delivery query executions were 0.379 ms and 0.129 ms respectively,
with zero shared reads, temp writes, and WAL in those explained statements.
The other three indexes have static 4/4 query-definition coverage but are not
misrepresented as dynamically exercised by this canonical population.

### Set-based one-current-leaf function

The replacement `rights.enforce_one_current_history_leaf()` dispatches on the
same four `subject_kind` values, obtains `NEW`'s typed UUID, and searches the
matching typed table through the new target-leading index.  It then joins by
assessment ID and retains the original current-leaf anti-join.

This is equivalent to the frozen key:

```text
subject_kind || ':' || typed_target_uuid
```

without evaluating a PL/pgSQL subject-key function across the whole assessment
table.  The supersession parent/time check, the provider-policy, delivery, and
attribution branches, the `v_count <> 1` invariant, SQLSTATE, and error message
remain unchanged.

### Set-based delivery-completeness function

The replacement `rights.validate_one_delivery_assessment(uuid)` constructs the
applicable assessment set from four typed equijoin branches:

| Subject | Indexed path from one delivery |
|---|---|
| provider object | bridge -> external reference -> provider object -> typed assessment |
| external visual reference | bridge -> typed assessment |
| digital representation | qualified locator -> locator representation for the same reference -> typed assessment |
| visual locator | qualified locator for the same reference -> typed assessment |

`UNION` preserves set semantics when a target is reachable through multiple
qualified paths.  The function still rejects a linked assessment that is
inapplicable, postdates the decision, or is superseded, and still rejects a
current applicable assessment that is not linked.  All subsequent rights-cap,
provider-policy, attribution, takedown, fail-closed mode, and healthy-locator
logic is byte-for-byte unchanged.

## Fresh replay integration

`run-rehearsal.sh` now has one deterministic order:

1. replay the immutable Phase 2A schema;
2. set the schema-owner role and apply the forward migration;
3. invoke the importer with the staging attestation and task-owned runtime
   paths;
4. verify the populated database against the remediated schema hash.

The replay code frozen for the P3 gate has ordered-list SHA-256:

```text
f39764c8ddc2c0ba54778502e23a8800e867e47214d961a2c8bc0749c606e910
```

No implementation changed between Fresh A and Fresh B.

## Named constraint groups and omission check

Before validation, the loader performs targeted `ANALYZE` on 17 populated
raw, core, provenance, and rights relations.  It then drains 11
schema-qualified business groups in dependency order:

| Order | Named group | Boundary |
|---:|---|---|
| 1 | `raw_core_cycle` | migration authority, reciprocal ledger/object SCC, entity subtypes, sole deferred FK |
| 2 | `folder_assignment_shape` | folder-assignment shape and supersession |
| 3 | `visual_bridge_and_locator` | visual bridge decision and locator history |
| 4 | `rights_observation` | observation typed shape and history |
| 5 | `rights_assessment_shape_support` | assessment typed shape, evidence, and supersession |
| 6 | `rights_assessment_current_leaf` | remediated assessment leaf invariant |
| 7 | `provider_policy` | policy validation, history, and current leaf |
| 8 | `delivery_parent_validation` | remediated delivery parent events |
| 9 | `delivery_rights_validation` | remediated delivery-rights link events |
| 10 | `delivery_policy_validation` | remediated delivery-policy link events |
| 11 | `delivery_history_and_rule` | delivery history/current leaf/rule pair |

Each group has a statement timeout, start checkpoint, wall duration, WAL
delta, and explicit end marker.  After all named groups, the loader still runs
one separately timed:

```sql
SET CONSTRAINTS ALL IMMEDIATE;
```

This final omission check is mandatory.  It guarantees that an unlisted
deferrable constraint cannot silently remain pending until commit.  At scale
8,000 it took 0.057805 seconds; in Fresh A and Fresh B it took 0.003559 and
0.000617 seconds.

## Content-addressed staging attestation

The single P0 full-content pass bound the frozen 35-file cache to:

```text
STAGING_MANIFEST_SHA256=01ac60c705f7450c6668a91ee6a3d2842c3b0258a4ecd85139611bf916681322
STAGING_ATTESTATION_SHA256=11742e9afc577d976ea097540326c2697937290635735ad9d4466efce1758bcc
CANDIDATE_SHA256=b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48
BASE_SCHEMA_SHA256=4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105
DESCRIPTOR_COUNT=35
```

Full replays reuse that attestation instead of rehashing approximately 4.5 GB
and semantically reparsing millions of occurrences.  Before any PostgreSQL
connection, the importer still validates the exact Candidate, base schema,
implementation-base commit, extractor and mapping identities, semantic
metrics, 35-file allowlist, bundle binding, attestation payload hash, resolved
stage path, descriptor size/hash bindings, filesystem type, current file size,
and modification time not newer than the original verification.

Runtime SQL is created only under the supplied task-owned runtime directory
and removed in `finally`.  Log and receipt paths are resolved before staging
validation or database connection, must have existing parents, and are
rejected if they point to the frozen staging directory or a descendant.  The
stable staging cache is neither regenerated nor modified; the Candidate
extractor is not rerun.

## Observability

The importer streams its single writer session to stdout and a flushed
task-owned log.  Persistent receipts include:

- exact PostgreSQL backend PID and commit marker;
- total importer wall and client CPU;
- COPY rows, bytes, wall, and WAL;
- durable-insert rows, wall, and WAL;
- parity and targeted-ANALYZE timing;
- all 11 named groups plus the final all-constraint check;
- before/after activity, locks, table/index statistics, I/O, WAL, and database
  size;
- backend statement CPU mapped to COPY, inserts, analyze, parity, and every
  constraint group; and
- five-second sampled backend RSS, database bytes, and PGDATA allocated and
  logical peaks for the decisive 1,000/4,000/8,000 ladder and full replays.

The backend CPU collector found all 12 constraint statements with no missing
or unmapped group.  The resource monitors observed the single writer and its
normal exit.  CPU growth, row progress, I/O, and named completion boundaries
are therefore measurable; CPU activity alone is not treated as progress.

## Atomicity, privileges, and unchanged invariants

The population writer uses one `psql` session and exactly one transaction.
Temporary staging creation, all 28 COPY operations, every durable insert,
parity, targeted ANALYZE, named validation, and final `ALL IMMEDIATE` occur
between one `BEGIN` and one `COMMIT`.  `ON_ERROR_STOP` converts COPY, insert,
fault-injection, parity, or constraint failures into rollback before commit.
There is no partial durable commit.

The remediation does not contain or use:

```text
DISABLE TRIGGER
session_replication_role=replica
NOT VALID
DROP CONSTRAINT / DROP TRIGGER
ON CONFLICT DO NOTHING
partial commit
raw-field omission
```

Both replacement functions retain invoker security, their original signatures
and return types, and `search_path=pg_catalog`.  `CREATE OR REPLACE` preserves
ownership, ACLs, and trigger dependencies.  No role, public view, Seal/CAS
function, append-only guard, rights enum, or delivery-rank policy is weakened.

Two fresh empty-schema executions produced the same final schema hash and
passed constraints, roles, Seal/CAS, serializable seal, unknown/inactive
relation negatives, and zero fixture residue.  Because the importer path
changed, all 11 failure cases were rerun on the fixed scale-50 fixture; all 11
failed at the expected point and left zero project-table, migration-batch,
pointer, or seal residue.  The inherited full-size 11-case suite was not
rerun.

## Deterministic schema hashes

| Schema state | SHA-256 | Evidence |
|---|---|---|
| frozen Phase 2A base | `4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105` | inherited manifest and every fresh base replay |
| forward-remediated | `aa8cb0af7b61931e51f1f71ed2e4cf0d10b178669de16807871819b330742e8b` | two empty-schema tests, decisive ladder, Fresh A, Fresh B |

The final hash is identical before and after every population transaction.
The base hash remains the frozen staging binding; the final hash represents
the explicit forward index/function delta.

## Independent acceptance

### B1 implementation review

B1 found no P0 or P1 issue in the completed integration:

```text
B1_CLOSING_REVIEW=PASS
B1_RESIDUAL_P0=NONE
B1_RESIDUAL_P1=NONE
FULL_REPLAY_INTEGRATION_READY=true
```

B1 confirmed semantic equivalence, 4/4 static index alignment, unchanged
constraint and trigger identities, deterministic forward application,
attestation/runtime boundaries, 17 targeted ANALYZE statements, 11 named
groups, final omission check, streaming, and the single population
transaction.  Dynamic P1 plan coverage is correctly limited to the one
subject kind present in the canonical population.

### B2 performance review

B2 independently accepted the monitored decisive ladder:

```text
B2_MONITORED_DECISIVE_SCALES=1000,4000,8000
B2_MONITORED_SCALE_RECEIPTS=3/3_PASS
B2_TOTAL_WALL_OLS_EXPONENT=0.750318118554367
B2_TOTAL_WALL_OLS_PROJECTION_15923_SECONDS=3530.5179820149265
B2_TOTAL_WALL_8000_ANCHORED_OLS_PROJECTION_15923_SECONDS=3982.552489738611
B2_SCALE_8000_TOTAL_SECONDS=2376.102825
B2_SCALE_8000_MAX_NAMED_GROUP_SECONDS=158.029628
B2_SCALE_8000_FINAL_ALL_SECONDS=0.057805
B2_RESIDUAL_P0=NONE
B2_RESIDUAL_P1=NONE
PERFORMANCE_BUDGET_MET=true
FULL_REPLAY_AUTHORIZED_BY_B2=true
```

At 8,000 objects, total replay took 39.601714 minutes, the slowest group took
2.633827 minutes, and count/digest/schema parity passed.  Backend CPU and peak
resource receipts exist for all three fitted scales.

## Full replay outcome under the remediated code freeze

Fresh A and Fresh B subsequently used the same code-freeze hash, schema,
mapping, staging, and single-transaction path:

| Replay | Controller wall s | Import wall s | Constraint sum s | Slowest group s | Commit/verifier | Input parity |
|---|---:|---:|---:|---:|---|---:|
| Fresh A | 2,981.42 | 2,140.160339 | 517.169478 | 149.547223 | PASS / PASS | 15,923 |
| Fresh B | 2,513.48 | 2,007.777488 | 668.211717 | 306.706418 | PASS / PASS | 15,923 |

Both remained below the 90-minute replay ceiling and the 20-minute per-group
ceiling.  Their count vector, normalized semantic digest, stable-key-set
digest, deterministic IDs, and schema hash match exactly.  Both contain one
migration batch and zero current pointers and sealed releases.

The post-Fresh-B population boundary receipt also passes: `api_reader` cannot
select raw locators or sources, cannot write archive objects, held locator
public leak count is zero, and zero positive rights produce zero remote-image
rows.

## Allowed and forbidden boundaries

The accepted remediation permits only the following replay behavior:

- replay the immutable Phase 2A chain into a fresh disposable database;
- apply this explicit forward migration as schema owner;
- reuse the exact bound staging attestation;
- create deterministic closure-complete performance fixtures derived from the
  frozen staging cache;
- run one writer and one atomic population transaction;
- use targeted ANALYZE, named constraint checkpoints, and the final all-
  constraint omission check; and
- run Fresh A then Fresh B only after the P3 Go gate.

The remediation does not authorize and did not perform:

- any trigger/constraint/FK, Seal/CAS, rights, or public-boundary weakening;
- Candidate re-extraction or staging modification;
- canonical backfill from SQLite, Search, TRACE, atlas, or catalog products;
- TRACE relation creation, positive-rights inflation, silent split/zip/drop,
  or omission of raw field literals;
- partial population commits or swallowed mapping conflicts;
- a production database connection or production migration;
- frontend, Next, browser, or production build work;
- protected-main or stable-branch changes;
- PR, merge, deployment, promotion, or production freeze; or
- a 20,000-object capacity rule.

Performance remediation and rehearsal success prove a disposable PostgreSQL
migration path.  They do not by themselves make the repository promotion-,
freeze-, or deployment-ready.

## Evidence index

- `03_ROOT_CAUSE_ANALYSIS.md`
- `02_CONSTRAINT_AND_INDEX_MATRIX.tsv`
- `agents/B1_REMEDIATION_INDEPENDENT_REVIEW.md`
- `agents/B2_SCALE_CURVE_DIGEST_INDEPENDENT_REVIEW.md`
- `evidence/P1_RIGHTS_LEAF_POST_FIX_PLAN_1000.log`
- `evidence/P1_DELIVERY_POST_FIX_PLAN_1000.log`
- `evidence/P2_FRESH_SCHEMA_TEST_RECEIPT.md`
- `evidence/P2_UPDATED_CODE_FAILURE_PROBES.json`
- `evidence/P2_SCALE_01000_MONITORED.json`
- `evidence/P2_SCALE_04000_MONITORED.json`
- `evidence/P2_SCALE_08000_MONITORED.json`
- `evidence/P2_SCALE_01000_BACKEND_CPU.json`
- `evidence/P2_SCALE_04000_BACKEND_CPU.json`
- `evidence/P2_SCALE_08000_BACKEND_CPU.json`
- `evidence/P2_SCALE_01000_MONITOR.json`
- `evidence/P2_SCALE_04000_MONITOR.json`
- `evidence/P2_SCALE_08000_MONITOR.json`
- `evidence/P3_REPLAY_CODE_FREEZE.sha256`
- `evidence/P4_FRESH_A_SUMMARY.json`
- `evidence/P5_FRESH_B_SUMMARY.json`
- `evidence/P5_PUBLIC_BOUNDARY_POPULATION.json`
