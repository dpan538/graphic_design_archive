# Phase 2B-P root-cause analysis

## Receipt scope

```text
ROOT_CAUSE_IDENTIFIED=true
ROOT_CAUSE_CONSTRAINTS=rights.rights_assessment_one_current_leaf,rights.delivery_assessment_validation,rights.delivery_rights_validation,rights.delivery_policy_validation
P1_BOUNDED_DIAGNOSTIC_COMPLETE=true
P3_GO_GATE_PASSED_BY_THIS_EVIDENCE=false
FULL_REPLAY_AUTHORIZED_BY_THIS_EVIDENCE=false
```

This receipt identifies the concrete deferred-trigger paths that made the old
monolithic `SET CONSTRAINTS ALL IMMEDIATE` unbounded. It combines the static
constraint/index audit with rollback-only, schema-qualified P1 probes before
and after the forward remediation. The evidence is sufficient to identify the
root cause and the mechanism that removes it. It is not a substitute for the
stratified staging scale ladder or the Phase P3 Go/No-Go gate.

## Finding

Four schema-qualified constraints account for the two reproduced P0 execution
shapes:

| Constraint | Trigger table | Trigger function path | Pre-fix expensive operation | Estimated replay events |
|---|---|---|---|---:|
| `rights.rights_assessment_one_current_leaf` | `rights.rights_assessment` | `rights.enforce_one_current_history_leaf()` -> `rights.assessment_subject_key(uuid)` | For each inserted assessment, scan `rights.rights_assessment` and call the subject-key SQL function for candidate rows. | 15,788 |
| `rights.delivery_assessment_validation` | `rights.delivery_assessment` | `rights.enforce_delivery_assessment()` -> `rights.validate_one_delivery_assessment(uuid)` -> `rights.subject_applies_to_delivery(...)` | Re-enumerate the global current-assessment set to prove delivery completeness. | 15,788 |
| `rights.delivery_rights_validation` | `rights.delivery_rights_assessment` | `rights.enforce_delivery_assessment()` -> `rights.validate_one_delivery_assessment(uuid)` -> `rights.subject_applies_to_delivery(...)` | Repeat the same completeness proof for every inserted link row. | 15,788 |
| `rights.delivery_policy_validation` | `rights.delivery_policy_evaluation` | `rights.enforce_delivery_assessment()` -> `rights.validate_one_delivery_assessment(uuid)` -> `rights.subject_applies_to_delivery(...)` | Repeat the same completeness proof for every inserted policy row. | 15,788 |

The four constraints therefore contribute an estimated 63,152 deferred row
events. They are a subset of the approximately 523,536 user/FK events queued
by the complete replay; 523,536 is a static estimate rather than a PostgreSQL
catalog invariant.

For the fixed population size `N = 15,788`:

- the one-current-leaf branch presents approximately `N * N = 249,260,944`
  assessment candidates to its function predicate;
- the three delivery validation constraints present approximately
  `3 * N * N = 747,782,832` assessment candidates to the completeness path;
- the two paths together therefore expose approximately 997,043,776 candidate
  examinations before accounting for the helper functions' own joins.

This is an event-amplified whole-table scan, not a lock wait. The prior Fresh A
snapshot recorded no blockers and no wait event while the backend was active
inside `SET CONSTRAINTS ALL IMMEDIATE`.

## Missing access paths in the base schema

The Phase 2A base schema gives each typed assessment-subject table a primary
key led by `rights_assessment_id`. It did not provide the reverse lookup needed
to start from a subject target and find that target's assessment history:

| Base-schema table | Missing reverse key | Forward index |
|---|---|---|
| `rights.rights_assessment_provider_object` | `(provider_object_id, rights_assessment_id)` | `rights_assessment_provider_object_target_idx` |
| `rights.rights_assessment_visual_reference` | `(external_visual_reference_id, rights_assessment_id)` | `rights_assessment_visual_reference_target_idx` |
| `rights.rights_assessment_representation` | `(digital_representation_id, rights_assessment_id)` | `rights_assessment_representation_target_idx` |
| `rights.rights_assessment_locator` | `(visual_locator_id, rights_assessment_id)` | `rights_assessment_locator_target_idx` |

The current population exercises the visual-reference path. The other three
indexes preserve the same bounded lookup for the remaining legal
`rights_subject_kind` variants instead of baking the current population mix
into the invariant implementation.

The base leaf function hid the target equality behind
`rights.assessment_subject_key(x.rights_assessment_id)`, so PostgreSQL could not
turn it into a target-led typed-table probe. The base delivery validator also
started its missing-link proof from all current rows of
`rights.rights_assessment`, then invoked
`rights.subject_applies_to_delivery(...)`. `ANALYZE` alone cannot turn either
opaque function predicate into the missing target access path.

## Pre-fix bounded evidence

### One-current-leaf probe

Both runs used the exact named constraint
`rights.rights_assessment_one_current_leaf`, a valid closed synthetic fixture,
and transaction rollback.

| Objects/assessments | Named-constraint seconds | WAL bytes | Assessment rows | Typed-subject rows |
|---:|---:|---:|---:|---:|
| 50 | 1.000482 | 65,536 | 50 | 50 |
| 250 | 60.978052 | 6,048 | 250 | 250 |

The scale multiplier is 5 and the elapsed multiplier is approximately
60.9487. The two-point diagnostic exponent is:

```text
log(60.978052 / 1.000482) / log(250 / 50) = 2.5537065
```

Thus the measured pre-fix exponent is approximately 2.55. The associated
plans show a sequential scan of `rights.rights_assessment` with the
`rights.assessment_subject_key(...)` equality predicate, removing 49 rows per
event at scale 50 and 249 rows per event at scale 250. This directly
reproduces the static whole-table-scan diagnosis.

### Delivery validation probe

The pre-fix scale-50 delivery fixture timed each schema-qualified constraint
independently:

| Named constraint | Seconds | WAL bytes |
|---|---:|---:|
| `rights.delivery_assessment_validation` | 3.489642 | 8,192 |
| `rights.delivery_rights_validation` | 1.582924 | 0 |
| `rights.delivery_policy_validation` | 1.429160 | 0 |
| **Three-group total** | **6.501726** | **8,192** |

The three timings demonstrate that the repeated work is not confined to the
parent-table trigger. Changes to the delivery, rights-link, and policy-link
tables all invoke `rights.enforce_delivery_assessment()` and therefore the same
global completeness validator.

## Forward remediation mechanism

The forward-only migration
`database/data-migrations/v48-to-v49/001_performance_remediation.sql` leaves the
Phase 2A DDL unchanged and does all of the following:

1. adds the four target-led indexes listed above;
2. replaces only the implementation of
   `rights.enforce_one_current_history_leaf()` so the rights-assessment branch
   resolves the typed target once and selects the matching typed table
   explicitly;
3. replaces only the implementation of
   `rights.validate_one_delivery_assessment(uuid)` so its applicability set is
   assembled with target-led, set-based branches and then compared with the
   linked assessments;
4. preserves the four constraint triggers, their deferred timing, the
   `v_count <> 1` leaf invariant, delivery completeness checks, and the
   original violation outcomes.

No trigger is disabled, no constraint is removed or weakened, no `NOT VALID`
state is introduced, and the fix does not change the imported data semantics.
Independent Queue B review and the required negative tests remain separate
acceptance obligations.

## Post-fix bounded evidence

The same rollback-only diagnostic fixtures timed the same four named
constraints after applying the forward remediation:

| Scale | `rights.rights_assessment_one_current_leaf` seconds | `rights.delivery_assessment_validation` seconds | `rights.delivery_rights_validation` seconds | `rights.delivery_policy_validation` seconds | Delivery three-group total seconds |
|---:|---:|---:|---:|---:|---:|
| 50 | 0.015495 | 0.449280 | 0.661508 | 0.375984 | 1.486772 |
| 250 | 0.260143 | 3.493091 | 2.574741 | 4.416219 | 10.484051 |
| 1,000 | 0.200152 | 5.893404 | 5.167927 | 4.477189 | 15.538520 |

The one-current-leaf time fell from 1.000482 to 0.015495 seconds at scale 50
and from 60.978052 to 0.260143 seconds at scale 250. Each post-fix named group
also completed at scale 1,000; the largest observed individual group was
5.893404 seconds. The small, non-monotonic leaf timings are consistent with
planner/cache noise at sub-second duration and must not be fitted as the P3
scale curve.

These results isolate the repaired execution paths. They do not establish a
full-import wall clock, staging I/O cost, or a 15,923-object projection.

## Independent pre-constraint Fresh A blocker

The old Fresh A transaction began at
`2026-08-13T04:08:17.156611Z`. Its final
`SET CONSTRAINTS ALL IMMEDIATE` began at
`2026-08-13T05:41:07.649169Z`. The elapsed time before entering deferred
validation was therefore:

```text
2026-08-13T05:41:07.649169Z - 2026-08-13T04:08:17.156611Z
= 5,570.492558 seconds
= 5,570.49 seconds
= 92.84 minutes
```

That pre-constraint time by itself exceeds the new 90-minute full-replay
budget. Consequently, repairing the four deferred constraints cannot by
itself authorize Fresh A. P2/P3 must also demonstrate bounded staging
verification, COPY/insert, `ANALYZE`, digest/parity, and all named-group time.

## Evidence boundary: root cause is identified; P3 is not passed

`ROOT_CAUSE_IDENTIFIED=true` is supported by the following closed chain:

1. static catalog-source analysis maps the exact four constraints to their
   tables and trigger/function paths;
2. the replay row counts quantify 63,152 implicated trigger events and the two
   whole-table candidate estimates;
3. the pre-fix named leaf probe reproduces the scan and a 50-to-250 exponent of
   approximately 2.55;
4. the pre-fix delivery probe measures all three repeated trigger entry points;
5. the same named constraints, on the same bounded fixtures, complete after
   the target indexes and set-based rewrites are applied.

The P1 probes are targeted synthetic diagnostics. They are **not** the required
content-addressed, stratified, closure-complete staging ladder of
`50 -> 250 -> 1,000 -> 4,000 -> 8,000`. This receipt contains no 4,000- or
8,000-object result, no largest-three-rung fit, no complete 8,000-object
45-minute result, no defensible full-population projection below 90 minutes,
and no Queue B P0 clearance. It also does not prove the full data parity,
logical digest, permissions, rollback, or public-boundary conditions.

Accordingly:

```text
ROOT_CAUSE_IDENTIFIED=true
FULL_REPLAY_AUTHORIZED_BY_P1=false
PERFORMANCE_GO_GATE_ESTABLISHED_BY_P1=false
```

Fresh A may begin only after the separate P2 scale ladder and P3 Go gate meet
every stated threshold. The post-fix P1 measurements must not be copied into
the P3 result as though they were staging-scale acceptance runs.

## Evidence inventory and reproducible checks

Primary evidence:

- `docs/audits/v49-phase2b-performance/agents/A1_CONSTRAINT_DEPENDENCY_INDEX_AUDIT.md`
- `docs/audits/v49-phase2b-performance/agents/A2_IMPORTER_TRANSACTION_PATH_AUDIT.md`
- `docs/audits/v49-phase2b-performance/evidence/P1_RIGHTS_LEAF_PRE_FIX_50.log`
- `docs/audits/v49-phase2b-performance/evidence/P1_RIGHTS_LEAF_PRE_FIX_250.log`
- `docs/audits/v49-phase2b-performance/evidence/P1_RIGHTS_LEAF_POST_FIX_50.log`
- `docs/audits/v49-phase2b-performance/evidence/P1_RIGHTS_LEAF_POST_FIX_250.log`
- `docs/audits/v49-phase2b-performance/evidence/P1_RIGHTS_LEAF_POST_FIX_1000.log`
- `docs/audits/v49-phase2b-performance/evidence/P1_DELIVERY_PRE_FIX_50.log`
- `docs/audits/v49-phase2b-performance/evidence/P1_DELIVERY_POST_FIX_50.log`
- `docs/audits/v49-phase2b-performance/evidence/P1_DELIVERY_POST_FIX_250.log`
- `docs/audits/v49-phase2b-performance/evidence/P1_DELIVERY_POST_FIX_1000.log`
- `docs/audits/v49-phase2b-migration/18_PERFORMANCE_BLOCK_RECEIPT.md`
- `database/data-migrations/v48-to-v49/001_performance_remediation.sql`

Read-only extraction commands:

```bash
rg -n '^\\s*[0-9]+\\s+\\|' \
  docs/audits/v49-phase2b-performance/evidence/P1_*.log

rg -n \
  'rights_assessment_one_current_leaf|delivery_(assessment|rights|policy)_validation|enforce_one_current_history_leaf|validate_one_delivery_assessment|assessment_subject_key|subject_applies_to_delivery' \
  database/functions database/migrations \
  database/data-migrations/v48-to-v49/001_performance_remediation.sql

rg -n 'xactStartUtc|queryStartUtc|SET CONSTRAINTS ALL IMMEDIATE' \
  docs/audits/v49-phase2b-migration/18_PERFORMANCE_BLOCK_RECEIPT.md
```
