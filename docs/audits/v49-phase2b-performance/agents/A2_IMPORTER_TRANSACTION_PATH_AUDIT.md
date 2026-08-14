# A2 importer and transaction-path audit

```text
AGENT=A2
QUEUE=Queue A / read-only diagnostics
AUDIT_RESULT=PASS_WITH_P0_PERFORMANCE_FINDINGS
DATABASE_STARTED=false
IMPORTER_STARTED=false
EXTRACTOR_STARTED=false
BUILD_STARTED=false
CORE_IMPLEMENTATION_CHANGED=false
REPORT_ONLY_CHANGE=true
```

## Scope and evidence boundary

This is a static review of the recovery-branch importer, staging verification,
load order, deferred-validation call chain, rollback behavior, and failure
injection harness. No PostgreSQL connection was opened and no Candidate,
staging, extractor, importer, browser, Next process, or build was started. The
only staging access was reading the small manifest and its existing descriptor
metadata; no staging payload was modified or regenerated.

The principal inspected sources were:

- `database/data-migrations/v48-to-v49/import.py`
- `database/data-migrations/v48-to-v49/{prepare-staging.sql,prepare-runtime.sql,load.sql,run-rehearsal.sh}`
- `database/data-migrations/v48-to-v49/tests/{run_failure_injections.py,run_idempotency_and_batch_collision.py}`
- `database/migrations/{002_raw_core_provenance.sql,003_research_rights.sql}`
- `database/functions/{001_deferred_constraints.sql,006_normative_closure.sql,012_controlled_write_closure.sql,015_final_integrity_closure.sql}`
- the persisted performance-block receipt and live checkpoint under
  `docs/audits/v49-phase2b-migration/`.

Dynamic attribution still belongs to P1: the controller must confirm the two
P0 query shapes below with a disposable cluster, named constraints,
`EXPLAIN (ANALYZE, BUFFERS, WAL)`, and scale data. The static complexity defects
themselves are unambiguous and must both be remediated before a full replay.

## Executive findings

| Priority | Finding | Static evidence | Required consequence |
|---|---|---|---|
| P0 | `rights.rights_assessment_one_current_leaf` is quadratic. Each of 15,788 deferred assessment-row events runs `rights.enforce_one_current_history_leaf()`, whose assessment branch scans all 15,788 assessments and computes a query-backed subject key for candidate rows. | `database/functions/006_normative_closure.sql:559-633`; helper at `database/functions/001_deferred_constraints.sql:1026-1045`; load count at `database/data-migrations/v48-to-v49/load.sql:337-362,456`. | Rewrite the assessment branch to select by typed subject columns, add reverse subject indexes in a forward migration, and prove indexed/set-based plans. |
| P0 | Three delivery constraint triggers contain a second quadratic completeness check. For every delivery event, `validate_one_delivery_assessment()` scans the complete assessment history and calls `subject_applies_to_delivery()` per candidate. The valid rehearsal has 15,788 events in each of three trigger families. | `database/functions/001_deferred_constraints.sql:1893-1978,2146-2171`; helper at `1419-1457`; load at `376-399`. | Rewrite completeness as a typed, indexed applicable-assessment set and compare that set to linked assessment IDs. Fix this together with the first P0; otherwise the next full run can merely move to a later quadratic blocker. |
| P0 | The old psql transaction had already spent about 5,570.49 seconds (92.84 minutes) before it entered final deferred validation. This alone exceeds the new 90-minute full-replay budget. | `docs/audits/v49-phase2b-migration/18_PERFORMANCE_BLOCK_RECEIPT.md:51-68`: xact start `04:08:17.156611Z`, final `SET CONSTRAINTS` query start `05:41:07.649169Z`. | Do not authorize Fresh A solely because constraint validation is fixed. The scale gate must also demonstrate bounded COPY/INSERT/parity time. |
| P1 | Every importer invocation re-hashes all 35 descriptors (4,866,714,086 bytes / 4.532 GiB) and then re-parses the 3.186 GB occurrence ledger plus 536 MB literal TSV and the surface ledger (another 3,726,798,741 bytes / 3.471 GiB). Total pre-database input reads are about 8.003 GiB, excluding Python parsing/base64/hash work. | `import.py:293-405`, especially `388-395`; semantic loop `148-276`; frozen manifest descriptors. | Consume a content-addressed, validator-version-bound attestation after the one authorized initial verification. Do not repeat the multi-million-line semantic pass for each scale rung, replay, or fault probe. |
| P1 | The importer writes and later deletes `runtime-import-<database>.sql` inside `args.stage_dir`. The retained staging cache is explicitly immutable in this phase. | `import.py:608-613`. | Write runtime SQL to a task-owned temporary directory outside staging, or pipe it to psql. Never create even short-lived files in the frozen cache. |
| P1 | The current runner rejects the retained cache path because it accepts only `/private/tmp/*` or `/tmp/*`. | `run-rehearsal.sh:13-16`. | Permit only the exact resolved approved cache prefix/path, with the bound attestation; do not broadly relax the path policy. |
| P1 | There is no named stage or live progress stream inside the psql run. The one long `SET CONSTRAINTS ALL IMMEDIATE` hides the active trigger/function. Python captures the child output until exit. | `import.py:279-285,546-565,608-615`; `load.sql:420-467`. | Split deferred validation into schema-qualified named groups, stream timestamped markers, set a group-specific `application_name`, and retain the final `SET CONSTRAINTS ALL IMMEDIATE` omission check. |
| P2 | All temporary staging tables are unindexed text tables and no targeted `ANALYZE` occurs before INSERT planning or deferred validation. | `prepare-staging.sql:1-121`; no `ANALYZE` in `load.sql`. | Add only plan-proven temporary indexes and targeted `ANALYZE`. This cannot repair the function-predicate quadratic scans by itself. |
| P2 | The rollback mechanism is atomic but operationally indirect: on a psql error the script stops, the connection closes, and PostgreSQL rolls the transaction back. There is no importer-owned stage timeout or cancellation receipt. | `import.py:546-565,608-615`; failure harness `run_failure_injections.py:83-118`. | Preserve this single-transaction behavior, add per-group statement timeouts and controller-visible backend/stage metadata, and re-run the 11 cases only on the bounded updated-code fixture. |

## Actual stage and transaction graph

```text
Python process (no DB yet)
  |
  +-- read strict staging manifest and immutable bindings
  +-- SHA-256 every one of 35 files                         ~4.532 GiB
  +-- parse surface-row-ledger.tsv                          15,923 rows
  +-- parse field-occurrence-ledger.jsonl                   6,282,271 rows
  +-- pair/decode/hash field-literals.tsv                   3,559,820 rows
  |                                                        +3.471 GiB reread
  +-- query DB owner
  +-- pg_dump/schema hash
  +-- existing batch ID/token lookup
  |
  `-- psql child (one session)
       BEGIN
       SET LOCAL gda.phase2b.inject
       SET ROLE schema_owner
       CREATE pg_temp staging tables/helpers
       28 x client-side \copy                              ~1.160 GiB
       after_staging injection
       load.sql
         raw source/mapping/batch/record/literal
         core entity -> archive object -> raw surface ledger cycle
         object/source + legacy identity + folder assignment
         trace + corpus + held delta
         visual reference/bridge/locator
         observation -> typed subject
         assessment -> typed subject -> observation bridge
         policy evaluation
         delivery -> rights link -> policy link
         visual disposition/classification
         parity scans
         after_parity injection
         SET CONSTRAINTS ALL IMMEDIATE                     opaque blocker
       COMMIT
```

The one-session and one-transaction boundary is real. `BEGIN` is generated at
`import.py:546-552`, all 28 `\copy` operations are appended at `554-558`,
`load.sql` is included at `562`, and `COMMIT` is the next command at `563`.
There is no `ON CONFLICT`, intermediate commit, trigger disable, replica role,
or row-skipping path.

## Staging verification and repeated-scan audit

### Strong bindings already present

Before opening PostgreSQL, `require_stage()` verifies the Candidate hash,
normalized base-schema hash, implementation base, checked-out extractor hash,
mapping hash, bundle-binding hash, fixed semantic metrics, exact 35-file
allowlist, descriptor sizes, and descriptor hashes (`import.py:293-405`). The
surface ledger verifier checks cardinality, contiguous ordinals, pointer
round-trip, and both ID uniqueness sets (`88-145`). The occurrence verifier
checks strict JSON keys, declared mapping rules, presence/type vocabulary,
deterministic field-literal UUIDs, exact occurrence/literal pairing, pointer
round-trips, raw-value hashes, final counts, and mapping-use counts
(`148-276`). These are meaningful fail-closed checks and should be retained.

### Why the current reuse path is not bounded

The descriptor loop at `import.py:388-391` reads all 4.532 GiB. Immediately
afterward, `validate_stage_occurrence_contract()` reopens the 3.186 GB JSONL
and 536 MB TSV and performs 6.28 million JSON parses, up to 3.56 million base64
decodes, UUIDv5 calculations, and SHA-256 calculations. The manifest shows:

```text
DESCRIPTOR_HASH_PASS_BYTES=4,866,714,086
EXTRA_SEMANTIC_PASS_BYTES=3,726,798,741
PRE_DATABASE_READ_BYTES_APPROX=8,593,512,827
PRE_DATABASE_READ_GIB_APPROX=8.003
COPY_INPUT_BYTES_APPROX=1,245,479,023
COPY_INPUT_GIB_APPROX=1.160
```

The live checkpoint's process lines also show the importer process had been
alive about 3 hours 29 minutes longer than its psql child. That delta covers
this pre-psql path (plus the small owner/schema/batch checks), so the static
scan duplication has material historical wall-time evidence; it is not merely
a theoretical concern.

### Safe attestation replacement

The performance path should accept an external, read-only attestation that is
bound to all of the following:

1. staging manifest SHA-256 and exact 35 descriptor `{name,bytes,sha256}` map;
2. Candidate, mapping, extractor, implementation-base, and base/final-schema
   hashes;
3. semantic-validator source SHA-256 and attestation schema version;
4. validated field occurrence/literal/mapping-use counts and surface identity
   counts;
5. approved resolved staging realpath and the P0 verification receipt hash.

Subsequent scale rungs and A/B may validate the small attestation and manifest
bindings without replaying the semantic parser. The one initial descriptor
binding remains authoritative. This is reuse of a content-addressed proof, not
weakening or skipping the original verification.

Runtime scripts, attestations, logs, and receipts must live outside the cache.
The current `runtime_sql = args.stage_dir / ...` (`import.py:608`) violates that
boundary even though the file is removed in `finally` (`610-613`).

## COPY and INSERT-order audit

### COPY path

`build_runtime_sql()` creates 28 text-only temporary tables and executes 28
client-side `\copy` operations in a fixed allowlisted order (`import.py:514-565`).
The seven manifest-only audit/reconciliation files are not copied into the
database. All durable casting and decoding is explicit in `load.sql`; COPY
itself creates no durable rows.

The staging tables have no keys, indexes, or statistics. The two archive-object
halves each join `gda_stage_archive_objects` to `gda_stage_surface_ledgers`
(`load.sql:92-103,130-141`), and both ledger halves rescan the ledger table
(`105-124,143-162`). At 15,923 rows these are secondary risks, but their plans
must be recorded. A temporary index on the shared ledger ID and a single
targeted `ANALYZE` are allowed only if the scale plans show benefit.

### Durable load order

The load order is semantically sound:

1. source asset -> mapping -> migration batch -> source records -> field
   literals (`load.sql:15-82`);
2. entity before archive-object subtype (`84-103`);
3. archive object before surface ledger only for the true reciprocal cycle;
   the `core.archive_object.created_from_surface_ledger_id` FK is the sole
   deferrable FK in the schema (`002_raw_core_provenance.sql:166-170`);
4. both sides of the archive/ledger cycle are complete before downstream links
   (`load.sql:105-168`);
5. folder before assignment parent before typed folder subtype (`181-203`);
6. rights parent tables before their typed subject/link tables
   (`load.sql:281-399`).

No reorder alone can solve the P0 scans. DAG ordering can reduce the number of
constraints that truly need to remain deferred, but the archive/ledger cycle
must continue to be deferred until both sides exist.

## Deferred-event inventory for this population

The schema contains only one deferrable FK; the bulk of the final queue is
row-level constraint triggers. Based on the fixed row counts and INSERTs, the
full population queues approximately 507,613 custom deferred trigger events
plus 15,923 events for `core.archive_object_surface_ledger_fk`, or about
523,536 deferred events in total.

| Proposed named group | Relevant schema-qualified constraints | Expected events | Static cost assessment |
|---|---|---:|---|
| raw/core reciprocal | `raw.migration_batch_authority_exact`; `raw.legacy_surface_lineage_exact`; `core.archive_object_surface_reciprocal`; `core.entity_subtype_from_entity`; `core.entity_subtype_from_archive_object`; `core.archive_object_surface_ledger_fk` | 79,616 | Indexed per-ID checks; true cycle. Expected near-linear, but measure. |
| folder assignments | `provenance.assignment_shape_from_assignment`; `provenance.assignment_shape_from_folder`; `provenance.assignment_supersession_parent` | 143,946 | `validate_one_assignment()` performs 13 subtype probes per shape event (`001_deferred_constraints.sql:422-520`). All probes use assignment-leading PKs, but PL/pgSQL/event overhead is large. |
| visual bridge/locator | `rights.object_visual_reference_decision_from_bridge`; `rights.locator_supersession_parent` | 31,578 | Per-ID or null-supersession checks; expected linear. |
| observation | `rights.rights_observation_shape_from_parent`; `rights.rights_observation_shape_from_reference`; `rights.rights_observation_supersession_parent` | 47,364 | Per-observation PK probes; expected linear. |
| assessment | `rights.rights_assessment_from_assessment`; `rights.rights_assessment_from_reference`; `rights.rights_assessment_from_observation_bridge`; `rights.rights_assessment_one_current_leaf`; `rights.rights_assessment_supersession_parent` | 78,940 | **P0 quadratic in `rights_assessment_one_current_leaf`.** Other checks are per-ID. |
| policy | `rights.provider_policy_evaluation_from_parent`; `rights.policy_evaluation_one_current_leaf`; `rights.policy_evaluation_supersession_parent` | 47,364 | Bridge index exists; expected near-linear after `ANALYZE`. |
| delivery | `rights.delivery_assessment_validation`; `rights.delivery_rights_validation`; `rights.delivery_policy_validation`; `rights.delivery_assessment_one_current_leaf`; `rights.delivery_supersession_parent`; `rights.delivery_rule_pair` | 94,728 | **P0 quadratic completeness query is executed by three trigger families.** Other checks are indexed/constant. |
| omission guard | `ALL` | normally zero remaining | Final `SET CONSTRAINTS ALL IMMEDIATE` must remain and be timed. |

The exact group membership must be generated from the live catalog during P1,
not copied blindly from this static list. Schema qualification is mandatory.

## P0 root-cause analysis

### P0-A: `rights_assessment_one_current_leaf`

The trigger is declared at `database/functions/006_normative_closure.sql:625-627`.
For each inserted `rights.rights_assessment`, its function executes:

```sql
SELECT count(*)
FROM rights.rights_assessment x
WHERE rights.assessment_subject_key(x.rights_assessment_id)
    = rights.assessment_subject_key(NEW.rights_assessment_id)
  AND NOT EXISTS (... newer ...);
```

This is at `006_normative_closure.sql:572-576`. There is no sargable subject
column in the predicate. `assessment_subject_key()` (`001_deferred_constraints.sql:1026-1045`)
first queries the assessment parent and then queries one of four typed subtype
tables. Consequently, every deferred parent-row event examines the whole
assessment table and invokes a query-backed helper for candidate rows.

With `N = 15,788`:

```text
DEFERRED_TRIGGER_INVOCATIONS=N=15,788
CANDIDATE_ROW_EXAMINATIONS=N^2=249,260,944
QUERY_BACKED_SUBJECT_HELPER_CALLS=at least N^2; potentially near 2*N^2
```

The typed subject tables have PKs on `rights_assessment_id`, but no reverse
indexes on `provider_object_id`, `external_visual_reference_id`,
`digital_representation_id`, or `visual_locator_id`
(`database/migrations/003_research_rights.sql:694-723`). An index alone cannot
make the current function predicate sargable; the function must also be
rewritten.

Because rights assessments are inserted before delivery rows
(`load.sql:337-399`), their deferred events are queued before the delivery
events. Trigger names on the assessment parent place
`rights_assessment_one_current_leaf` between the fast shape and supersession
checks. This is the strongest static attribution for the observed first
blocker inside the opaque final `SET CONSTRAINTS`.

### P0-B: delivery completeness fanout

`rights.delivery_assessment_validation`, `rights.delivery_rights_validation`,
and `rights.delivery_policy_validation` all call the same
`rights.validate_one_delivery_assessment()` function
(`001_deferred_constraints.sql:2146-2168`). The valid-completeness branch at
`1949-1974` starts from every row of `rights.rights_assessment` and filters by:

```sql
rights.subject_applies_to_delivery(
  a.subject_kind,
  COALESCE(typed_subject_ids...),
  v_bridge,
  v_id
)
```

`subject_applies_to_delivery()` (`1419-1457`) performs another bridge/reference
query for each call. In a valid replay, the `EXISTS` is looking for an
applicable current assessment that is *not* linked. None exists, so it cannot
exit on a positive match and must examine the candidate assessment set.

Each of the three populated trigger tables has 15,788 rows. The static upper
bound for the valid dataset is therefore:

```text
DELIVERY_VALIDATOR_INVOCATIONS=3*N=47,364
CANDIDATE_ROW_EXAMINATIONS=3*N^2=747,782,832
```

This is a second independent quadratic defect. It may not yet have been
reached in the cancelled run because P0-A's events precede it. Both must be
fixed before scale authorization.

## Semantics-preserving remediation design

Use a forward migration; do not edit the frozen Phase 2A files.

1. Add reverse indexes for every typed assessment subject, at minimum:
   `(external_visual_reference_id, rights_assessment_id)` for this population,
   plus corresponding provider-object, representation, and locator indexes so
   the invariant remains efficient for all legal subject kinds.
2. `CREATE OR REPLACE` the assessment branch of
   `rights.enforce_one_current_history_leaf()` so it:
   - resolves the NEW assessment's typed subject once;
   - branches on `NEW.subject_kind`;
   - counts current leaves by joining only the matching typed subtype table on
     its indexed subject column;
   - retains the exact supersession-parent/time checks and the requirement that
     the current-leaf count equal one.
3. Replace delivery's all-assessment function predicate with a set-returning or
   inline set-based applicable-assessment relation formed from four typed
   branches:
   - matching provider object for the bridge;
   - matching external visual reference;
   - representations admitted by this delivery's locator qualifications;
   - visual locators admitted by this delivery's qualifications.
   Compare that indexed set against `delivery_rights_assessment`; preserve the
   existing assessed-time, supersession, evidence-role, fail-closed cap,
   policy, attribution, takedown, and locator checks.
4. Run targeted `ANALYZE` on the rights parent, typed-subject, supersession,
   delivery-link, policy, and bridge tables immediately before their named
   constraint groups. Statistics improve plan selection but are not a
   substitute for steps 1-3.
5. Keep every constraint enabled and validated, keep one transaction, and end
   with `SET CONSTRAINTS ALL IMMEDIATE` as an omission check. Do not use
   `DISABLE TRIGGER`, `session_replication_role`, `NOT VALID`, partial commits,
   or conflict swallowing.

For dynamic proof, explain both the original-equivalent and remediated queries
on each scale rung. The expected repaired plan must start from the bridge's
typed subject/qualification set and use the new reverse indexes; a sequential
scan of all assessments inside each trigger invocation is a No-Go even if a
small fixture happens to finish.

## Named-stage observability requirements

The current Python `run()` uses `subprocess.run(..., capture_output=True)`
(`import.py:279-285`), so psql markers are unavailable to the controller until
the child exits. `load.sql` has checkpoints only for failure injection and
parity, not timings (`load.sql:126-128,231,279,418,420-467`).

The updated path should, without committing intermediate state:

1. stream psql stdout/stderr to a task-owned log and the controller;
2. emit `BEGIN/END` JSON or TSV markers with UTC timestamp, backend PID,
   application name, stage name, expected/actual row count, and elapsed time;
3. set a distinct `application_name` before COPY, each INSERT domain,
   `ANALYZE`, each named constraint group, parity, and final ALL check;
4. apply a local 20-minute statement timeout to each constraint group, with a
   tighter scale-rung timeout where appropriate; a timeout must abort the same
   transaction;
5. on small diagnostic fixtures, enable `track_functions = pl` and/or
   `auto_explain.log_nested_statements` as available, and capture function call
   counts/total time plus `EXPLAIN (ANALYZE, BUFFERS, WAL)` for equivalent
   underlying queries;
6. sample `pg_stat_activity`, blockers/locks, database I/O, table/index stats,
   temp bytes, and WAL LSN deltas from the controller's read-only monitor;
7. record cold/warm cache status and disk high-water mark.

The final all-constraints statement should normally have no queued events
after every named group. If it is not near-zero, treat that as an omitted group
or new dependency, not as harmless tail work.

## Atomicity, rollback, and failure injection

### What is already sound

- `BEGIN` precedes temp-table creation and COPY, and `COMMIT` follows
  `load.sql`; durable writes cannot commit independently.
- `ON_ERROR_STOP` is active. On a SQL error, psql exits; connection teardown
  rolls back the open transaction. `import.py` reports
  `IMPORT_TRANSACTION_ROLLED_BACK` (`608-615`).
- The five runtime injections cover after staging, a real 8,000-row mid-object
  point, after corpus, after visual, and after parity. Four pre-database faults
  and two binding-hash failures complete the inherited 11 cases
  (`tests/run_failure_injections.py:83-105`). Each probe verifies all project
  tables are zero before proceeding (`41-59,105`).
- The cancelled Fresh A is stronger evidence that an actual backend cancel at
  final deferred validation rolled back to zero residue.

### Gaps to close after code changes

- `after_objects` is an accepted importer injection value
  (`import.py:578`) but is not one of the persisted 11 probes. Do not expand the
  full-scale inherited suite merely for this; if useful, add it only as a
  bounded supplementary fixture check.
- Named groups change the transaction path. Re-run the required 11 cases on a
  deterministic fixture of at most 1,000 objects, including the same real
  mid-object assertion. Add a bounded failure after at least one named group
  has completed to show earlier validation does not create a commit boundary.
- A group statement timeout or `pg_cancel_backend` must yield an aborted
  transaction and a zero-residue receipt. Never continue the same transaction
  after a timeout.
- Keep backend PID, active named stage, cancel result, rollback duration, table
  residue, batch, pointers, and seals in the receipt.

## Scale-fixture compatibility gap

The production importer cannot consume the required `50 -> 250 -> 1,000 ->
4,000 -> 8,000` ladder unchanged:

- staging metrics and surface cardinality are hard-coded to the full 15,923
  (`import.py:88-145,347-370`);
- the mid-object cut is fixed at ordinal 8,000 (`load.sql:89-162`);
- parity constants are hard-coded (`load.sql:420-462`).

Do not weaken the full-population checks. Add an explicit fixture contract
whose expected counts and deterministic mid-object boundary are read from a
content-addressed fixture manifest. Full mode must still require the frozen
15,923 constants. The fixture builder must preserve closure and strata as
specified by the controller; simple head-N slicing is not acceptable.

## Go/No-Go advice to the controller

Fresh A must remain unauthorized until all of the following are true:

1. P1 attributes runtime to named constraints/functions and confirms the two
   P0 scans above;
2. the forward migration supplies typed reverse indexes and equivalent
   set-based validation without weakening any invariant;
3. the 8,000-object rung shows a maximum-three-rung exponent at or below the
   phase threshold, no named group over 15 minutes, and a full projection below
   90 minutes;
4. COPY/INSERT/parity time is also below the projection budget—the historical
   92.84-minute pre-constraint transaction is an independent No-Go signal;
5. the updated-code bounded 11-case fixture suite, counts/digests, roles,
   rollback, and final ALL omission check pass;
6. the importer no longer writes to the frozen staging directory and no longer
   repeats the 8.003 GiB semantic verification pass after the initial bound
   attestation.

Static conclusion:

```text
ROOT_CAUSE_CANDIDATE_1=rights.rights_assessment_one_current_leaf
ROOT_CAUSE_FUNCTION_1=rights.enforce_one_current_history_leaf()
ROOT_CAUSE_COMPLEXITY_1=O(N^2)
ROOT_CAUSE_CANDIDATE_2=rights.delivery_assessment_validation,rights.delivery_rights_validation,rights.delivery_policy_validation
ROOT_CAUSE_FUNCTION_2=rights.validate_one_delivery_assessment(uuid)
ROOT_CAUSE_COMPLEXITY_2=O(N^2) per trigger family
MISSING_INDEX_FAMILY=rights_assessment typed-subject reverse indexes
STATIC_ROOT_CAUSE_IDENTIFIED=true
DYNAMIC_ROOT_CAUSE_CONFIRMED=false
FULL_REPLAY_AUTHORIZED=false
CONSTRAINTS_DISABLED=false
ATOMIC_SINGLE_TRANSACTION=true
```
