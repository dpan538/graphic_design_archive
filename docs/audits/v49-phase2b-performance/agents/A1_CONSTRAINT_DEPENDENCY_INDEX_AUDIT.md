# A1 constraint, dependency, and index audit

## Receipt

```text
AGENT=A1
QUEUE=A_READ_ONLY_DIAGNOSTIC
REVIEWED_HEAD=6b918dd2ebd9af6f9a8fca6edbe6bbbf7de41320
REVIEW_MODE=STATIC_READ_ONLY
POSTGRES_STARTED=false
POSTGRES_CONNECTED=false
EXTRACTOR_STARTED=false
IMPORTER_STARTED=false
BUILD_STARTED=false
CORE_IMPLEMENTATION_CHANGED=false
USER_CONSTRAINT_TRIGGER_COUNT=135
DEFERRABLE_FK_COUNT=1
FK_COUNT=473
MULTI_TABLE_FK_SCC_COUNT=1
ACTIVE_REPLAY_CONSTRAINT_TRIGGER_COUNT=27
ESTIMATED_ACTIVE_DEFERRED_EVENT_COUNT=523536
STATIC_ROOT_CAUSE_CONFIDENCE=HIGH
STATIC_ROOT_CAUSE_CONSTRAINTS=rights.rights_assessment_one_current_leaf,rights.delivery_assessment_validation,rights.delivery_rights_validation,rights.delivery_policy_validation
STATIC_ROOT_CAUSE_FUNCTIONS=rights.enforce_one_current_history_leaf(),rights.validate_one_delivery_assessment(uuid)
STATIC_ROOT_CAUSE_SUPPORT_FUNCTIONS=rights.assessment_subject_key(uuid),rights.subject_applies_to_delivery(...)
STATIC_ROOT_CAUSE_TABLE=rights.rights_assessment
STATIC_ROOT_CAUSE_MISSING_ACCESS_PATH=rights.rights_assessment_visual_reference(external_visual_reference_id,rights_assessment_id)
```

This is a static diagnosis, not the P1 runtime `EXPLAIN (ANALYZE, BUFFERS)`
receipt. The controller must confirm the named constraint on a bounded fixture
before setting the phase-wide `ROOT_CAUSE_IDENTIFIED=true` gate. The static
evidence is nevertheless specific and strong enough to make
`rights.rights_assessment_one_current_leaf` the first isolated probe.

## Executive finding

The performance block is not explained by the one deferred FK. Two active
deferred validation paths perform whole-table rights-assessment scans. The
first is a row-level constraint trigger that scans the table for every imported
rights assessment:

```sql
-- database/functions/006_normative_closure.sql:572-576
SELECT count(*) INTO v_count FROM rights.rights_assessment x
WHERE rights.assessment_subject_key(x.rights_assessment_id)
  = rights.assessment_subject_key(NEW.rights_assessment_id)
  AND NOT EXISTS (
    SELECT 1 FROM rights.rights_assessment n
    WHERE n.supersedes_rights_assessment_id=x.rights_assessment_id
  );
```

`rights.assessment_subject_key()` is a `STABLE` PL/pgSQL function which first
looks up the assessment row and then looks up one of four typed subject tables
(`database/functions/001_deferred_constraints.sql:1026-1045`). It is not an
immutable expression that can be indexed, and the predicate does not expose a
typed target column to the planner. Therefore each of the 15,788 queued
`rights_assessment_one_current_leaf` events examines 15,788 assessment rows.
That is 249,260,944 candidate-row comparisons before accounting for the nested
SQL calls. If the executor evaluates both subject-key calls per candidate row,
the expression can cause roughly 498,521,888 subject-key calls, each containing
one or two indexed SQL lookups. This is deterministic quadratic work.

The imported subject type is `external_visual_reference`. Its typed bridge has
only a primary key on `rights_assessment_id`; there is no reverse index on
`external_visual_reference_id` (`database/migrations/003_research_rights.sql:
701-723`). By contrast the sibling one-current checks for policy and delivery
use directly searchable `object_visual_reference_id` predicates and have
indexes beginning with that column (`provider_policy_evaluation_reference_idx`
at lines 756-757 and `delivery_assessment_reference_idx` at lines 828-829).

This precisely distinguishes the pathological branch from the other three
branches of `rights.enforce_one_current_history_leaf()`.

There is a second deterministic quadratic path later in the same deferred
queue. `rights.validate_one_delivery_assessment()` proves completeness by
searching for any applicable current rights assessment that was not linked to
the delivery (`database/functions/001_deferred_constraints.sql:1949-1975`).
The query starts at the entire `rights.rights_assessment` table and calls
`rights.subject_applies_to_delivery()` for each candidate. That helper performs
fresh bridge/reference SQL lookups (`database/functions/001_deferred_constraints.sql:
1419-1457`), so the planner cannot turn the predicate into an indexed target
lookup.

The parent delivery row, its rights bridge, and its policy bridge each queue a
separate call to the same full validator. Thus 15,788 deliveries produce
47,364 executions of the whole-table completeness query. Against 15,788
assessments, that is 747,782,832 candidate-row examinations. Valid data does
not short-circuit the outer `EXISTS`: it must prove that no applicable current
assessment is unlinked, so it scans through the non-applicable rows. The three
specific active constraints are:

```text
rights.delivery_assessment_validation
rights.delivery_rights_validation
rights.delivery_policy_validation
```

The earlier assessment-current-leaf path is the likely first quadratic event
encountered in insertion-order deferred processing, but the prior monolithic
receipt cannot prove the exact event cursor. Both quadratic paths must be
remediated before a full replay; fixing only the first will expose the second.

## Scope and authoritative inputs

The audit read:

- all eight `database/migrations/*.sql` files;
- all fifteen `database/functions/*.sql` files;
- the Phase 2A replay-derived constraint inventory
  `docs/audits/v49-phase2a-schema/02_TABLE_CONSTRAINT_MATRIX.tsv`;
- the exact load order in `database/data-migrations/v48-to-v49/load.sql`;
- the small frozen `staging-manifest.json` (not the TSV/JSONL payloads);
- the prior performance receipt and live/rollback evidence.

The frozen payload was not parsed, rehashed, changed, or regenerated. Counts
below come from the already-bound staging manifest and the loader's fixed
parity assertions.

## Complete deferred-constraint inventory

### Counts

The replay-derived Phase 2A matrix contains:

| Kind | Count | Deferral result |
|---|---:|---|
| user constraint triggers | 135 | all deferrable, initially deferred |
| foreign keys | 473 | 1 deferrable/initially deferred; 472 immediate |
| primary keys | 223 | immediate |
| unique constraints | 134 | immediate |
| standalone unique indexes | 4 | immediate |

The only explicitly deferrable FK is
`core.archive_object.archive_object_surface_ledger_fk` on
`created_from_surface_ledger_id -> raw.legacy_surface_ledger
(legacy_surface_ledger_id)` (`database/migrations/002_raw_core_provenance.sql:
166-170`). All remaining deferred work is row-level constraint-trigger work.

### All 135 user constraint triggers, grouped by trigger function

Every name below was extracted from all `database/functions/*.sql`; the counts
sum to 135.

| Trigger function | Count | Constraint-trigger names |
|---|---:|---|
| `raw.enforce_migration_batch_authority` | 1 | `migration_batch_authority_exact` |
| `raw.enforce_legacy_surface_lineage` | 1 | `legacy_surface_lineage_exact` |
| `raw.enforce_archive_object_surface_reciprocal` | 1 | `archive_object_surface_reciprocal` |
| `core.enforce_legacy_identity_resolution` | 2 | `legacy_identity_resolution_exact`, `legacy_identity_split_exact` |
| `core.enforce_entity_subtype` | 7 | `entity_subtype_from_entity`, `entity_subtype_from_archive_object`, `entity_subtype_from_agent`, `entity_subtype_from_place`, `entity_subtype_from_concept`, `entity_subtype_from_collection`, `entity_subtype_from_temporal_extent` |
| `provenance.enforce_assertion_shape` | 12 | `assertion_shape_from_assertion`, `assertion_shape_from_subject`, `assertion_shape_from_source_record_subject`, `assertion_shape_from_trace_node_subject`, `assertion_shape_from_representation_subject`, `assertion_shape_from_literal`, `assertion_shape_from_entity_value`, `assertion_shape_from_source_record_value`, `assertion_shape_from_trace_node_value`, `assertion_shape_from_folder_value`, `assertion_shape_from_representation_value`, `assertion_shape_from_identity_value` |
| `provenance.enforce_accepted_assertion` | 4 | `accepted_assertion_from_assertion`, `accepted_assertion_from_evidence`, `accepted_assertion_from_decision`, `accepted_assertion_from_decision_evidence` |
| `provenance.enforce_assignment_shape_and_support` | 17 | `assignment_shape_from_assignment`, `assignment_shape_from_entity_name`, `assignment_shape_from_source_record`, `assignment_shape_from_agent_credit`, `assignment_shape_from_medium`, `assignment_shape_from_type`, `assignment_shape_from_subject`, `assignment_shape_from_collection`, `assignment_shape_from_temporal`, `assignment_shape_from_place`, `assignment_shape_from_folder`, `assignment_shape_from_tree`, `assignment_shape_from_representation`, `assignment_shape_from_identity`, `assignment_support_from_assertion`, `assignment_support_from_decision`, `assignment_support_from_decision_evidence` |
| `provenance.enforce_assignments_for_assertion` | 1 | `assignment_support_from_assertion_status` |
| `provenance.enforce_predicate_registry_fanout` | 1 | `predicate_registry_fanout` |
| `provenance.enforce_provenance_supersession_parent` | 6 | `source_version_supersession_parent`, `evidence_supersession_parent`, `assertion_supersession_parent`, `assignment_supersession_parent`, `assignment_decision_supersession_parent`, `assertion_decision_supersession_parent` |
| `provenance.enforce_one_current_review_decision` | 2 | `assertion_one_current_decision`, `assignment_one_current_decision` |
| `research.enforce_claim_acceptance` | 4 | `claim_acceptance_from_revision`, `claim_acceptance_from_evidence`, `claim_acceptance_from_decision`, `claim_acceptance_from_decision_evidence` |
| `research.enforce_one_current_claim_decision` | 1 | `claim_one_current_decision` |
| `research.enforce_relation_endpoint_shape` | 2 | `relation_endpoint_shape_from_parent`, `relation_endpoint_shape_from_entity` |
| `research.enforce_semantic_relation_acceptance` | 4 | `semantic_relation_acceptance_from_relation`, `semantic_relation_acceptance_from_claim`, `semantic_relation_acceptance_from_decision`, `semantic_relation_acceptance_from_decision_evidence` |
| `research.enforce_relations_for_type` | 1 | `semantic_relation_acceptance_from_type` |
| `research.enforce_one_current_relation_decision` | 1 | `relation_one_current_decision` |
| `research.enforce_relations_for_claim_revision` | 2 | `semantic_relation_acceptance_from_claim_revision`, `semantic_relation_acceptance_from_claim_evidence` |
| `research.enforce_relations_for_endpoint` | 1 | `semantic_relation_acceptance_from_endpoint_target` |
| `research.enforce_research_supersession_parent` | 3 | `claim_revision_supersession_parent`, `semantic_relation_supersession_parent`, `relation_decision_supersession_parent` |
| `research.enforce_epistemic_registry_fanout` | 1 | `epistemic_registry_fanout` |
| `rights.enforce_rights_observation_shape` | 5 | `rights_observation_shape_from_parent`, `rights_observation_shape_from_provider_object`, `rights_observation_shape_from_reference`, `rights_observation_shape_from_representation`, `rights_observation_shape_from_locator` |
| `rights.enforce_rights_assessment` | 6 | `rights_assessment_from_assessment`, `rights_assessment_from_provider_object`, `rights_assessment_from_reference`, `rights_assessment_from_representation`, `rights_assessment_from_locator`, `rights_assessment_from_observation_bridge` |
| `rights.enforce_provider_policy_evaluation` | 2 | `provider_policy_evaluation_from_parent`, `provider_policy_evaluation_from_version` |
| `rights.enforce_takedown_scope_shape` | 7 | `takedown_scope_shape_from_parent`, `takedown_scope_shape_from_visual`, `takedown_scope_shape_from_provider`, `takedown_scope_shape_from_provider_object`, `takedown_scope_shape_from_representation`, `takedown_scope_shape_from_locator`, `takedown_scope_shape_from_bridge` |
| `rights.enforce_takedown_event_scope` | 2 | `takedown_event_has_scope_from_event`, `takedown_event_has_scope_from_scope` |
| `rights.enforce_takedown_override` | 1 | `takedown_override_cannot_weaken_event` |
| `rights.enforce_delivery_assessment` | 4 | `delivery_assessment_validation`, `delivery_rights_validation`, `delivery_policy_validation`, `delivery_locator_validation` |
| `rights.enforce_rights_supersession_parent` | 6 | `rights_observation_supersession_parent`, `rights_assessment_supersession_parent`, `policy_evaluation_supersession_parent`, `delivery_supersession_parent`, `locator_supersession_parent`, `takedown_override_supersession_parent` |
| `rights.enforce_one_current_history_leaf` | 4 | `rights_assessment_one_current_leaf`, `policy_evaluation_one_current_leaf`, `delivery_assessment_one_current_leaf`, `attribution_bundle_one_current_leaf` |
| `rights.enforce_delivery_rule_pair` | 1 | `delivery_rule_pair` |
| `rights.enforce_object_visual_reference_decision` | 2 | `object_visual_reference_decision_from_bridge`, `object_visual_reference_decision_from_history` |
| `rights.enforce_object_visual_reference_decision_parent` | 1 | `object_visual_reference_decision_parent` |
| `workflow.enforce_review_case_subtype` | 7 | `review_case_exact_subtype_parent`, `review_case_exact_subtype_assertion`, `review_case_exact_subtype_assignment`, `review_case_exact_subtype_claim`, `review_case_exact_subtype_relation`, `review_case_exact_subtype_relation_type`, `review_case_exact_subtype_rights` |
| `audit.enforce_decision_event_subtype` | 12 | `decision_event_exact_subtype_parent`, `decision_event_exact_subtype_assertion`, `decision_event_exact_subtype_assignment`, `decision_event_exact_subtype_claim`, `decision_event_exact_subtype_relation`, `decision_event_exact_subtype_observation`, `decision_event_exact_subtype_assessment`, `decision_event_exact_subtype_policy`, `decision_event_exact_subtype_delivery`, `decision_event_exact_subtype_attribution`, `decision_event_exact_subtype_takedown`, `decision_event_exact_subtype_visual_bridge` |

### Which triggers are active in this replay

The loader inserts into 33 durable tables. Seventeen of those tables queue 27
distinct user constraint triggers. With the fixed row counts, the final
`SET CONSTRAINTS ALL IMMEDIATE` has approximately 523,536 user/FK row events
to drain:

| Named checkpoint family | Rows/events | Active constraints |
|---|---:|---|
| raw/core reciprocal + subtype + deferred FK | 79,616 | `migration_batch_authority_exact`; `entity_subtype_from_entity`; `entity_subtype_from_archive_object`; `archive_object_surface_reciprocal`; `legacy_surface_lineage_exact`; `archive_object_surface_ledger_fk` |
| folder assignment exact shape/history | 143,946 | `assignment_shape_from_assignment`; `assignment_shape_from_folder`; `assignment_supersession_parent` |
| visual bridge + locator history | 31,578 | `object_visual_reference_decision_from_bridge`; `locator_supersession_parent` |
| rights observation shape/history | 47,364 | `rights_observation_shape_from_parent`; `rights_observation_shape_from_reference`; `rights_observation_supersession_parent` |
| rights assessment shape/history/current leaf | 78,940 | `rights_assessment_from_assessment`; `rights_assessment_from_reference`; `rights_assessment_from_observation_bridge`; `rights_assessment_supersession_parent`; `rights_assessment_one_current_leaf` |
| provider policy validation/history/current leaf | 47,364 | `provider_policy_evaluation_from_parent`; `policy_evaluation_supersession_parent`; `policy_evaluation_one_current_leaf` |
| delivery validation/history/current leaf/rule | 94,728 | `delivery_assessment_validation`; `delivery_rights_validation`; `delivery_policy_validation`; `delivery_supersession_parent`; `delivery_assessment_one_current_leaf`; `delivery_rule_pair` |

The estimate assumes one deferred RI check for each of the 15,923 inserted
archive objects. Internal RI trigger implementation can create a different
catalog-event count, so runtime instrumentation should report both the static
estimate and the actual named-group timing rather than treating 523,536 as a
catalog invariant.

## Dependency direction and strongly connected components

The 473-FK child-to-parent graph covers 223 project tables. Static Tarjan SCC
analysis finds exactly one multi-table SCC:

```text
{ core.archive_object, raw.legacy_surface_ledger }
```

Its edges are:

- `core.archive_object.created_from_surface_ledger_id` ->
  `raw.legacy_surface_ledger.legacy_surface_ledger_id` (the sole deferred FK);
- `raw.legacy_surface_ledger.archive_object_id` ->
  `core.archive_object.archive_object_id` (immediate FK).

This is the only load-order cycle that genuinely requires deferred treatment.
The importer resolves the immediate direction by inserting the archive object
before its ledger row, while deferring the reciprocal FK until both exist.

Twenty tables have self-referential history edges:

```text
core.legacy_identity_resolution
provenance.assertion
provenance.assertion_review_decision
provenance.assignment_review_decision
provenance.canonical_assignment
provenance.evidence_item
provenance.source_version
raw.fail_closed_delta
research.claim_review_decision
research.claim_revision
research.relation_review_decision
research.semantic_relation
rights.attribution_bundle
rights.delivery_assessment
rights.object_visual_reference_review_decision
rights.provider_policy_evaluation
rights.rights_assessment
rights.rights_observation
rights.takedown_override
rights.visual_locator
```

For this migration all imported `supersedes_*` values are null, so these
self-edges do not require a cyclic load. The remaining intentionally deferred
families enforce exact parent/typed-child shape or evidence completeness. They
are semantic completion barriers, not FK SCCs, and can be fired as named groups
immediately after their last dependency is loaded.

## FK and index coverage

### Whole schema

All 473 referenced-side column sets are backed by a primary/unique constraint
or eligible unique index; PostgreSQL could not create the FK otherwise. A
static leading-column audit across 223 PKs, 134 unique constraints, and 108
explicit indexes found:

```text
FK_CHILD_SIDE_COVERED=274/473
FK_CHILD_SIDE_NOT_COVERED=199/473
```

Child-side indexes are not required for inserting valid children: an insert RI
check probes the indexed referenced side. Missing child indexes matter for
parent update/delete checks, operational joins, and trigger queries. Therefore
the 199 omissions do not explain the current insert-only deferred-FK stage by
themselves, and adding hundreds of speculative indexes is not recommended.

### Replay-active tables

The active loader path contains 63 FKs:

```text
ACTIVE_FK_CHILD_SIDE_COVERED=40/63
ACTIVE_FK_CHILD_SIDE_NOT_COVERED=23/63
```

The exact 23 child-side omissions are:

| Child table | Child columns | Referenced table/columns | Current replay relevance |
|---|---|---|---|
| `core.archive_object` | `created_from_surface_ledger_id` | `raw.legacy_surface_ledger(legacy_surface_ledger_id)` | deferred RI child path; index advisable for reciprocal diagnostics/deletes, not the insert lookup |
| `provenance.assignment_folder_membership` | `archive_object_id` | `core.archive_object(archive_object_id)` | 47,982 rows; useful reverse membership path |
| `provenance.canonical_assignment` | `supersedes_assignment_id` | self PK | imported null |
| `raw.fail_closed_delta` | `field_literal_id` | `raw.field_literal(field_literal_id)` | imported null |
| `raw.fail_closed_delta` | `resolved_by_delta_id` | self PK | imported null |
| `raw.legacy_surface_ledger` | `(canonical_input_asset_id, source_record_id)` | `raw.source_record(source_asset_id, source_record_id)` | parent unique index handles insert check |
| `raw.migration_batch` | `(canonical_input_asset_id, input_sha256)` | `raw.source_asset(source_asset_id, sha256)` | one row; parent unique index handles insert check |
| `research.corpus_membership` | `evidence_item_id` | `provenance.evidence_item(evidence_item_id)` | imported null |
| `research.trace_node` | `evidence_item_id` | `provenance.evidence_item(evidence_item_id)` | imported null |
| `rights.delivery_assessment` | `attribution_bundle_id` | `rights.attribution_bundle(attribution_bundle_id)` | imported null |
| `rights.delivery_policy_evaluation` | `provider_policy_evaluation_id` | `rights.provider_policy_evaluation(provider_policy_evaluation_id)` | 15,788 rows; reverse operational path |
| `rights.delivery_rights_assessment` | `rights_assessment_id` | `rights.rights_assessment(rights_assessment_id)` | 15,788 rows; reverse operational path |
| `rights.external_visual_reference` | `source_record_id` | `raw.source_record(source_record_id)` | composite `(source_asset_id,source_record_id)` is indexed, but not this singleton order |
| `rights.legacy_visual_surface_classification` | `evidence_item_id` | `provenance.evidence_item(evidence_item_id)` | imported null |
| `rights.object_visual_reference` | `evidence_item_id` | `provenance.evidence_item(evidence_item_id)` | imported null |
| `rights.rights_assessment_visual_reference` | `external_visual_reference_id` | `rights.external_visual_reference(external_visual_reference_id)` | **P0 access-path gap used by offending logical invariant** |
| `rights.rights_observation_visual_reference` | `external_visual_reference_id` | `rights.external_visual_reference(external_visual_reference_id)` | 15,788 rows; subject-history reverse path |
| `rights.rights_observation` | `evidence_item_id` | `provenance.evidence_item(evidence_item_id)` | imported null |
| `rights.visual_locator` | `source_asset_id` | `raw.source_asset(source_asset_id)` | composite reference index is ordered by external reference, not source |
| `rights.visual_locator` | `(source_asset_id, source_record_id)` | `raw.source_record(source_asset_id,source_record_id)` | 15,790 rows; lineage reverse path |
| `rights.visual_locator` | `source_evidence_item_id` | `provenance.evidence_item(evidence_item_id)` | imported null |
| `rights.visual_locator` | `source_record_id` | `raw.source_record(source_record_id)` | 15,790 rows; lineage reverse path |
| `rights.visual_locator` | `supersedes_visual_locator_id` | self PK | imported null; future history path |

The P0 gap is narrower than generic FK coverage: the current invariant needs a
fast lookup from typed subject target to assessment history. None of the four
assessment subject subtype tables has a reverse target index:

```text
rights.rights_assessment_provider_object(provider_object_id, rights_assessment_id)
rights.rights_assessment_visual_reference(external_visual_reference_id, rights_assessment_id)
rights.rights_assessment_representation(digital_representation_id, rights_assessment_id)
rights.rights_assessment_locator(visual_locator_id, rights_assessment_id)
```

The first, third, and fourth protect future subject kinds; the second is the
one exercised 15,788 times now.

## Complexity and risk matrix

| Priority | Constraint/function | Static plan shape | Expected events | Complexity | Finding |
|---|---|---|---:|---|---|
| P0 | `rights.rights_assessment_one_current_leaf` / `rights.enforce_one_current_history_leaf` | full scan of `rights_assessment`; per-row SQL subject-key function | 15,788 | Theta(N^2) | first high-confidence root-cause path; 249,260,944 candidates |
| P0 | `delivery_assessment_validation`, `delivery_rights_validation`, `delivery_policy_validation` / `rights.validate_one_delivery_assessment` | repeated whole-table assessment completeness scan; per-row `subject_applies_to_delivery` SQL | 47,364 | Theta(N^2) | second high-confidence root-cause path; 747,782,832 candidates |
| P1 | `assignment_shape_from_assignment` + `assignment_shape_from_folder` / `provenance.validate_one_assignment` | 13 subtype PK probes plus status/support probes per event | 95,964 | Theta(N), high constant | isolate and time; semantics are indexed by subtype PK |
| P1 | all active groups | no explicit `ANALYZE` between bulk insert and final validation | 523,536 | planner-dependent | run targeted `ANALYZE` inside the transaction before named groups |
| P1 | monolithic `SET CONSTRAINTS ALL IMMEDIATE` | all 27 active trigger names plus RI work are opaque | 523,536 | aggregate | split into schema-qualified groups and retain final ALL omission check |
| P2 | `policy_evaluation_one_current_leaf` | equality on indexed `object_visual_reference_id`; unique supersedes lookup | 15,788 | Theta(N log N) / near-linear | not the quadratic branch |
| P2 | `delivery_assessment_one_current_leaf` | equality on indexed `object_visual_reference_id`; unique supersedes lookup | 15,788 | Theta(N log N) / near-linear | not the quadratic branch |
| P2 | object-visual decision constraint | indexed bridge decision lookup; no decisions in this population | 15,788 | near-linear | low risk |
| P2 | deferred archive/ledger FK and reciprocal triggers | referenced PK/unique probes; predicates restricted by row ID | 47,769 trigger/RI events plus subtype work | near-linear | true SCC, but not scan explosion |

Both whole-table rights branches remain quadratic even after `ANALYZE`;
statistics cannot make the opaque `assessment_subject_key(x.id)` or
`subject_applies_to_delivery(...)` predicates into typed target lookups.
`ANALYZE` is still needed for the remaining groups.

## Required forward-only remediation shape

The Phase 2A files are frozen. A safe forward migration should:

1. add the four reverse typed-subject indexes above, at minimum the visual
   reference index exercised by this population;
2. `CREATE OR REPLACE FUNCTION rights.enforce_one_current_history_leaf()` in
   the forward migration so the `rights_assessment` branch:
   - resolves `NEW.subject_kind` and its target once;
   - selects the matching typed child table explicitly;
   - joins that child table to `rights.rights_assessment` by PK;
   - filters on the target column using its new reverse index;
   - retains the exact existing `NOT EXISTS` supersession-leaf predicate;
   - retains the exact `v_count <> 1` exception and message;
3. leave all four constraint triggers enabled, deferrable, and initially
   deferred;
4. avoid an expression index on `assessment_subject_key()`: it queries other
   tables and is `STABLE`, not immutable, so such an index is neither legal nor
   semantically maintainable;
5. rewrite the completeness arm in
   `rights.validate_one_delivery_assessment()` as a typed, set-based candidate
   relation which starts from the delivery's bridge/reference/provider and its
   qualified locator/representation IDs, uses the four new reverse indexes to
   enumerate only applicable current assessments, and anti-joins
   `rights.delivery_rights_assessment` for the one delivery ID; retain the same
   `DELIVERY_REQUIRES_APPLICABLE_RIGHTS_ASSESSMENT` failure condition;
6. keep the parent, rights-bridge, and policy-bridge constraint triggers. The
   direct indexed query makes their repeated checks bounded without weakening
   change coverage; do not suppress events with unsafe transaction-local
   memoization;
7. run targeted `ANALYZE` on the loaded active tables before the first named
   validation group.

This changes only the access path and equivalent query formulation. It does
not weaken the one-current-leaf invariant, remove evidence checks, alter data
semantics, or split the transaction.

## Candidate schema-qualified named groups

These groups preserve one transaction and make progress/timeout boundaries
observable. Each group should be timed independently; after all groups, the
loader must still execute one `SET CONSTRAINTS ALL IMMEDIATE` as an omission
check.

1. `raw_core_cycle`

   ```sql
   SET CONSTRAINTS
     raw.migration_batch_authority_exact,
     core.archive_object_surface_ledger_fk,
     raw.legacy_surface_lineage_exact,
     core.archive_object_surface_reciprocal,
     core.entity_subtype_from_entity,
     core.entity_subtype_from_archive_object
   IMMEDIATE;
   ```

2. `folder_assignment_shape`

   ```sql
   SET CONSTRAINTS
     provenance.assignment_shape_from_assignment,
     provenance.assignment_shape_from_folder,
     provenance.assignment_supersession_parent
   IMMEDIATE;
   ```

3. `visual_bridge_and_locator`

   ```sql
   SET CONSTRAINTS
     rights.object_visual_reference_decision_from_bridge,
     rights.locator_supersession_parent
   IMMEDIATE;
   ```

4. `rights_observation`

   ```sql
   SET CONSTRAINTS
     rights.rights_observation_shape_from_parent,
     rights.rights_observation_shape_from_reference,
     rights.rights_observation_supersession_parent
   IMMEDIATE;
   ```

5. `rights_assessment_shape_support`

   ```sql
   SET CONSTRAINTS
     rights.rights_assessment_from_assessment,
     rights.rights_assessment_from_reference,
     rights.rights_assessment_from_observation_bridge,
     rights.rights_assessment_supersession_parent
   IMMEDIATE;
   ```

6. `rights_assessment_current_leaf` (isolate this constraint by itself)

   ```sql
   SET CONSTRAINTS rights.rights_assessment_one_current_leaf IMMEDIATE;
   ```

7. `provider_policy`

   ```sql
   SET CONSTRAINTS
     rights.provider_policy_evaluation_from_parent,
     rights.policy_evaluation_supersession_parent,
     rights.policy_evaluation_one_current_leaf
   IMMEDIATE;
   ```

8. `delivery_parent_validation` (isolate the second P0 by source)

   ```sql
   SET CONSTRAINTS rights.delivery_assessment_validation IMMEDIATE;
   ```

9. `delivery_rights_validation`

   ```sql
   SET CONSTRAINTS rights.delivery_rights_validation IMMEDIATE;
   ```

10. `delivery_policy_validation`

   ```sql
   SET CONSTRAINTS rights.delivery_policy_validation IMMEDIATE;
   ```

11. `delivery_history_and_rule`

   ```sql
   SET CONSTRAINTS
     rights.delivery_supersession_parent,
     rights.delivery_assessment_one_current_leaf,
     rights.delivery_rule_pair
   IMMEDIATE;
   ```

12. final omission check

   ```sql
   SET CONSTRAINTS ALL IMMEDIATE;
   ```

Before adopting the spelling in production code, P1 should query
`pg_trigger`, `pg_constraint`, `pg_class`, and `pg_namespace` in the disposable
cluster to prove that each schema-qualified name resolves exactly once. This
is especially important because constraint-trigger names are table-schema
qualified even when their trigger function lives in a different schema (for
example `core.archive_object_surface_reciprocal` calls a `raw` function).

## Runtime confirmation requested from P1/P2

The main agent should collect the following on the 50-object closed fixture,
then repeat on the scale ladder:

1. time each named group above and record event-source row counts;
2. execute `EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS, SUMMARY)` for equivalents
   of both the current rights-assessment leaf query and delivery completeness
   query, and for both direct typed-join replacements;
3. prove both current plans have sequential scan/function filters and both
   fixed plans use reverse typed-subject indexes;
4. enable function statistics if available and capture call counts for
   `rights.assessment_subject_key` and
   `rights.enforce_one_current_history_leaf`;
5. record `pg_stat_user_tables`, `pg_stat_user_indexes`, temp bytes, buffers,
   WAL, and cold/warm state around the isolated constraint;
6. verify the fixed function raises the same violation on duplicate current
   leaves and accepts the same valid single-leaf history;
7. rerun the bounded affected failure suite because a trigger-function path is
   changing.

The expected signature is decisive: both pre-fix isolated groups should grow
quadratically, while the direct typed joins plus reverse indexes should produce
near-linear scale curves.

## Reproducible read-only commands

Representative commands used in this audit:

```text
git status --short --branch
git rev-parse HEAD
rg -n '^CREATE CONSTRAINT TRIGGER ' database/functions
rg -n 'DEFERRABLE|SET CONSTRAINTS' database/migrations database/functions database/data-migrations/v48-to-v49/load.sql
perl -0777 -ne '<extract trigger name, ON table, EXECUTE FUNCTION>' database/functions/*.sql
awk -F '\t' '<count control_kind values>' docs/audits/v49-phase2a-schema/02_TABLE_CONSTRAINT_MATRIX.tsv
python3 -c '<stdlib TSV + SQL index leading-column coverage audit>'
python3 -c '<stdlib Tarjan SCC over all FOREIGN_KEY rows>'
python3 -c '<intersect load.sql INSERT targets with constraint-trigger tables>'
sed -n '<bounded ranges>' database/functions/001_deferred_constraints.sql database/functions/006_normative_closure.sql database/functions/012_controlled_write_closure.sql database/functions/015_final_integrity_closure.sql
sed -n '<bounded ranges>' database/migrations/*.sql database/data-migrations/v48-to-v49/load.sql
sed -n '<bounded ranges>' docs/audits/v49-phase2b-migration/18_PERFORMANCE_BLOCK_RECEIPT.md docs/audits/v49-phase2b-migration/evidence/performance-live.json
```

No command opened a PostgreSQL socket, started a server, ran a migration,
started an importer, or read the multi-gigabyte staging payload.

## A1 disposition

```text
A1_STATUS=PASS_WITH_P0_ROOT_CAUSE_CANDIDATE
STATIC_ROOT_CAUSE_IDENTIFIED=true
ROOT_CAUSE_RUNTIME_CONFIRMED=false
PRIMARY_CONSTRAINTS=rights.rights_assessment_one_current_leaf,rights.delivery_assessment_validation,rights.delivery_rights_validation,rights.delivery_policy_validation
PRIMARY_FUNCTIONS=rights.enforce_one_current_history_leaf(),rights.validate_one_delivery_assessment(uuid)
PRIMARY_COMPLEXITY=THETA_N_SQUARED_FOR_BOTH_PATHS
PRIMARY_FIX_REQUIRES_FORWARD_MIGRATION=true
CONSTRAINT_WEAKENING_RECOMMENDED=false
TRIGGER_DISABLE_RECOMMENDED=false
SINGLE_TRANSACTION_PRESERVED=true
FULL_REPLAY_AUTHORIZATION_RECOMMENDED=false
NEXT_GATE=ISOLATED_NAMED_CONSTRAINT_SCALE_CONFIRMATION
```
