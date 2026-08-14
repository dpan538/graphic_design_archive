-- Phase 2B deterministic Candidate bundle loader.
--
-- Called only from import.py after prepare-staging.sql and psql \copy commands
-- have populated the gda_stage_* temporary relations.  This file owns no
-- durable schema objects and never changes Phase 2A DDL, functions, or roles.
\set ON_ERROR_STOP on

SET LOCAL TIME ZONE 'UTC';
SET CONSTRAINTS ALL DEFERRED;

SELECT clock_timestamp() AS phase2b_insert_started,
       pg_current_wal_lsn() AS phase2b_insert_wal_started
\gset
\echo PHASE2B_STAGE_BEGIN|DURABLE_INSERTS|:phase2b_insert_started|:phase2b_insert_wal_started

-- import.py creates two pg_temp helpers before SET ROLE.  That keeps staging
-- creation under the disposable-cluster administrator while all durable rows
-- below are written as the approved schema-owner migration role.

INSERT INTO raw.source_asset (
  source_asset_id, authority, logical_name, sha256, byte_length,
  raw_bytes, media_type, received_at
)
SELECT
  source_asset_id::uuid,
  authority::raw.asset_authority,
  pg_temp.gda_b64_json_scalar(logical_name_json_b64),
  sha256::core.sha256_hex,
  byte_length::bigint,
  decode(raw_bytes_b64, 'base64'),
  pg_temp.gda_b64_json_scalar(media_type_json_b64),
  received_at::timestamptz
FROM gda_stage_source_assets;

INSERT INTO raw.mapping_version (
  mapping_version_id, version_token, specification_sha256, parser_version,
  delimiter_policy, created_at
)
SELECT
  mapping_version_id::uuid,
  pg_temp.gda_b64_json_scalar(version_token_json_b64)::core.release_token,
  specification_sha256::core.sha256_hex,
  pg_temp.gda_b64_json_scalar(parser_version_json_b64),
  delimiter_policy,
  created_at::timestamptz
FROM gda_stage_mapping_versions;

INSERT INTO raw.migration_batch (
  migration_batch_id, batch_token, canonical_input_asset_id, mapping_version_id,
  input_sha256, started_at, completed_at
)
SELECT
  migration_batch_id::uuid,
  pg_temp.gda_b64_json_scalar(batch_token_json_b64)::core.release_token,
  canonical_input_asset_id::uuid,
  mapping_version_id::uuid,
  input_sha256::core.sha256_hex,
  started_at::timestamptz,
  completed_at::timestamptz
FROM gda_stage_migration_batches;

INSERT INTO raw.source_record (
  source_record_id, source_asset_id, record_ordinal, legacy_source_record_id,
  raw_value, raw_fingerprint, parsed_projection, parse_error_code
)
SELECT
  r.source_record_id::uuid,
  b.canonical_input_asset_id::uuid,
  r.record_ordinal::bigint,
  pg_temp.gda_b64_json_scalar(r.legacy_source_record_id_json_b64),
  decode(r.raw_value_b64, 'base64'),
  r.raw_fingerprint::core.sha256_hex,
  convert_from(decode(r.parsed_projection_b64, 'base64'), 'UTF8')::jsonb,
  NULL
FROM gda_stage_source_records r
CROSS JOIN gda_stage_migration_batches b;

INSERT INTO raw.field_literal (
  field_literal_id, source_record_id, json_pointer, occurrence_ordinal,
  raw_text, raw_bytes, byte_start, byte_end
)
SELECT
  field_literal_id::uuid, source_record_id::uuid,
  pg_temp.gda_b64_json_scalar(json_pointer_json_b64),
  occurrence_ordinal::integer,
  NULL, decode(raw_value_b64, 'base64'), NULL, NULL
FROM gda_stage_field_literals;

INSERT INTO core.entity (entity_id, entity_kind, lifecycle_state, created_at)
SELECT entity_id::uuid, entity_kind::core.entity_kind,
  lifecycle_state::core.lifecycle_state, created_at::timestamptz
FROM gda_stage_entities;

-- Deliberately load a nonzero deterministic first half of operational objects
-- before the ``during_objects`` fault point.  This is a real mid-object
-- rollback probe, not merely a checkpoint after an all-or-nothing INSERT.
INSERT INTO core.archive_object (
  archive_object_id, operational_semantics_version, preferred_label,
  created_from_surface_ledger_id
)
SELECT
  o.archive_object_id::uuid,
  pg_temp.gda_b64_json_scalar(operational_semantics_version_json_b64)::core.release_token,
  pg_temp.gda_b64_json_scalar(preferred_label_json_b64),
  o.legacy_surface_ledger_id::uuid
FROM gda_stage_archive_objects o
JOIN gda_stage_surface_ledgers l ON l.legacy_surface_ledger_id=o.legacy_surface_ledger_id
WHERE l.input_ordinal::bigint < 8000;

INSERT INTO raw.legacy_surface_ledger (
  legacy_surface_ledger_id, migration_batch_id, source_record_id,
  canonical_input_asset_id, input_ordinal, surface_id, legacy_source_record_id,
  source_fingerprint, import_disposition, archive_object_id, reason_code
)
SELECT
  l.legacy_surface_ledger_id::uuid,
  b.migration_batch_id::uuid,
  l.source_record_id::uuid,
  l.canonical_input_asset_id::uuid,
  l.input_ordinal::bigint,
  pg_temp.gda_b64_json_scalar(l.surface_id_json_b64),
  pg_temp.gda_b64_json_scalar(l.legacy_source_record_id_json_b64),
  l.source_fingerprint::core.sha256_hex,
  l.import_disposition::raw.import_disposition,
  l.archive_object_id::uuid,
  pg_temp.gda_b64_json_scalar(l.reason_code_json_b64)
FROM gda_stage_surface_ledgers l
CROSS JOIN gda_stage_migration_batches b
WHERE l.input_ordinal::bigint < 8000;

SELECT 'PHASE2B_MID_OBJECT_SUBSET_ROWS=' || count(*)::text
FROM core.archive_object;
SELECT pg_temp.gda_inject('during_objects');

INSERT INTO core.archive_object (
  archive_object_id, operational_semantics_version, preferred_label,
  created_from_surface_ledger_id
)
SELECT
  o.archive_object_id::uuid,
  pg_temp.gda_b64_json_scalar(o.operational_semantics_version_json_b64)::core.release_token,
  pg_temp.gda_b64_json_scalar(o.preferred_label_json_b64),
  o.legacy_surface_ledger_id::uuid
FROM gda_stage_archive_objects o
JOIN gda_stage_surface_ledgers l ON l.legacy_surface_ledger_id=o.legacy_surface_ledger_id
WHERE l.input_ordinal::bigint >= 8000;

INSERT INTO raw.legacy_surface_ledger (
  legacy_surface_ledger_id, migration_batch_id, source_record_id,
  canonical_input_asset_id, input_ordinal, surface_id, legacy_source_record_id,
  source_fingerprint, import_disposition, archive_object_id, reason_code
)
SELECT
  l.legacy_surface_ledger_id::uuid,
  b.migration_batch_id::uuid,
  l.source_record_id::uuid,
  l.canonical_input_asset_id::uuid,
  l.input_ordinal::bigint,
  pg_temp.gda_b64_json_scalar(l.surface_id_json_b64),
  pg_temp.gda_b64_json_scalar(l.legacy_source_record_id_json_b64),
  l.source_fingerprint::core.sha256_hex,
  l.import_disposition::raw.import_disposition,
  l.archive_object_id::uuid,
  pg_temp.gda_b64_json_scalar(l.reason_code_json_b64)
FROM gda_stage_surface_ledgers l
CROSS JOIN gda_stage_migration_batches b
WHERE l.input_ordinal::bigint >= 8000;

INSERT INTO provenance.object_source_record (
  archive_object_id, source_record_id, source_role
)
SELECT archive_object_id::uuid, source_record_id::uuid, source_role
FROM gda_stage_object_source_links;

INSERT INTO core.legacy_identity (
  legacy_identity_id, identity_kind, namespace, legacy_id, created_at
)
SELECT
  legacy_identity_id::uuid,
  identity_kind::core.legacy_identity_kind,
  pg_temp.gda_b64_json_scalar(namespace_json_b64),
  pg_temp.gda_b64_json_scalar(legacy_id_json_b64),
  created_at::timestamptz
FROM gda_stage_legacy_identities;

INSERT INTO research.folder (folder_id, folder_token, label, created_at)
SELECT folder_id::uuid,
  pg_temp.gda_b64_json_scalar(folder_token_json_b64)::core.release_token,
  pg_temp.gda_b64_json_scalar(label_json_b64), created_at::timestamptz
FROM gda_stage_folders;

INSERT INTO provenance.canonical_assignment (
  canonical_assignment_id, assignment_kind, status, supersedes_assignment_id,
  created_at
)
SELECT canonical_assignment_id::uuid,
  assignment_kind::provenance.assignment_kind,
  status::provenance.assertion_status,
  NULL, created_at::timestamptz
FROM gda_stage_folder_assignments;

INSERT INTO provenance.assignment_folder_membership (
  canonical_assignment_id, folder_id, archive_object_id, membership_role,
  member_ordinal
)
SELECT canonical_assignment_id::uuid, folder_id::uuid, archive_object_id::uuid,
  membership_role, member_ordinal::integer
FROM gda_stage_folder_assignments;

-- No core.legacy_identity_resolution is created in this no-release rehearsal:
-- Phase 2A correctly requires a release-pinned/evidence-governed resolution.
-- The legacy IDs remain exact raw identities, and object/source/trace roots are
-- linked through the surface ledger and research.object_trace_node below.

INSERT INTO research.trace_node (
  trace_node_id, canonical_key, label, created_at, entity_id, node_type,
  evidence_item_id
)
SELECT
  trace_node_id::uuid,
  pg_temp.gda_b64_json_scalar(canonical_key_json_b64),
  pg_temp.gda_b64_json_scalar(label_json_b64),
  created_at::timestamptz,
  entity_id::uuid,
  pg_temp.gda_b64_json_scalar(node_type_json_b64)::core.release_token,
  NULL
FROM gda_stage_trace_nodes;

INSERT INTO research.object_trace_node (
  archive_object_id, trace_node_id, node_role
)
SELECT archive_object_id::uuid, trace_node_id::uuid,
  pg_temp.gda_b64_json_scalar(node_role_json_b64)
FROM gda_stage_object_trace_nodes;

SELECT pg_temp.gda_inject('after_objects');

INSERT INTO research.corpus (corpus_id, corpus_token, label, created_at)
SELECT corpus_id::uuid,
  pg_temp.gda_b64_json_scalar(corpus_token_json_b64)::core.release_token,
  pg_temp.gda_b64_json_scalar(label_json_b64), created_at::timestamptz
FROM gda_stage_corpora;

INSERT INTO research.corpus_version (
  corpus_version_id, corpus_id, version_token, policy_version, policy_sha256,
  population_frame, created_at
)
SELECT
  corpus_version_id::uuid, corpus_id::uuid,
  pg_temp.gda_b64_json_scalar(version_token_json_b64)::core.release_token,
  pg_temp.gda_b64_json_scalar(policy_version_json_b64)::core.release_token,
  policy_sha256::core.sha256_hex,
  pg_temp.gda_b64_json_scalar(population_frame_json_b64),
  created_at::timestamptz
FROM gda_stage_corpus_versions;

INSERT INTO research.corpus_membership (
  corpus_version_id, archive_object_id, disposition, reason_code,
  evidence_item_id, decided_by, decided_at
)
SELECT
  corpus_version_id::uuid, archive_object_id::uuid,
  disposition::research.membership_disposition,
  pg_temp.gda_b64_json_scalar(reason_code_json_b64),
  NULL,
  pg_temp.gda_b64_json_scalar(decided_by_json_b64),
  decided_at::timestamptz
FROM gda_stage_corpus_memberships;

INSERT INTO raw.fail_closed_delta (
  fail_closed_delta_id, migration_batch_id, source_record_id, field_literal_id,
  expected_classification, actual_literal, reason_code, disposition,
  recorded_at, resolved_by_delta_id
)
SELECT
  fail_closed_delta_id::uuid, migration_batch_id::uuid, source_record_id::uuid,
  NULL,
  pg_temp.gda_b64_json_scalar(expected_classification_json_b64),
  pg_temp.gda_b64_json_scalar(actual_literal_json_b64),
  pg_temp.gda_b64_json_scalar(reason_code_json_b64),
  disposition::raw.delta_disposition, recorded_at::timestamptz, NULL
FROM gda_stage_held_deltas;

SELECT pg_temp.gda_inject('after_corpus');

INSERT INTO rights.external_visual_reference (
  external_visual_reference_id, source_asset_id, source_record_id,
  source_field_or_json_pointer, source_occurrence_ordinal, provider_object_id,
  reference_fingerprint, created_at
)
SELECT
  external_visual_reference_id::uuid, source_asset_id::uuid, source_record_id::uuid,
  pg_temp.gda_b64_json_scalar(pointer_json_b64), occurrence_ordinal::integer,
  NULL, reference_fingerprint::core.sha256_hex, created_at::timestamptz
FROM gda_stage_visual_references;

INSERT INTO rights.object_visual_reference (
  object_visual_reference_id, archive_object_id, external_visual_reference_id,
  reference_role, ordinal, acceptance_state, evidence_item_id
)
SELECT
  object_visual_reference_id::uuid, archive_object_id::uuid,
  external_visual_reference_id::uuid, reference_role::rights.reference_role,
  ordinal::integer, acceptance_state::provenance.assertion_status, NULL
FROM gda_stage_visual_bridges;

INSERT INTO rights.visual_locator (
  visual_locator_id, external_visual_reference_id, locator_role, source_asset_id,
  source_record_id, source_field_or_json_pointer, occurrence_ordinal,
  source_evidence_item_id, visibility, raw_locator, locator_fingerprint,
  supersedes_visual_locator_id, created_at
)
SELECT
  visual_locator_id::uuid, external_visual_reference_id::uuid,
  locator_role::rights.locator_role, source_asset_id::uuid, source_record_id::uuid,
  pg_temp.gda_b64_json_scalar(pointer_json_b64), occurrence_ordinal::integer,
  NULL, visibility::rights.locator_visibility,
  pg_temp.gda_b64_json_scalar(raw_locator_json_b64),
  locator_fingerprint::core.sha256_hex, NULL, created_at::timestamptz
FROM gda_stage_visual_locators;

INSERT INTO rights.rights_observation (
  rights_observation_id, subject_kind, evidence_state, evidence_item_id,
  observed_wording, observed_at, supersedes_rights_observation_id
)
SELECT
  rights_observation_id::uuid,
  'external_visual_reference'::rights.rights_subject_kind,
  evidence_state::rights.rights_evidence_state,
  NULL,
  pg_temp.gda_b64_json_scalar(observed_wording_json_b64),
  observed_at::timestamptz,
  NULL
FROM gda_stage_rights_observations;

INSERT INTO rights.rights_observation_visual_reference (
  rights_observation_id, external_visual_reference_id
)
SELECT rights_observation_id::uuid, external_visual_reference_id::uuid
FROM gda_stage_rights_observations;

INSERT INTO rights.rights_assessment (
  rights_assessment_id, subject_kind, assessed_state, reviewer_actor, rationale,
  assessed_at, supersedes_rights_assessment_id
)
SELECT
  rights_assessment_id::uuid,
  'external_visual_reference'::rights.rights_subject_kind,
  assessed_state::rights.rights_evidence_state,
  pg_temp.gda_b64_json_scalar(reviewer_actor_json_b64),
  pg_temp.gda_b64_json_scalar(rationale_json_b64),
  assessed_at::timestamptz,
  NULL
FROM gda_stage_rights_assessments;

INSERT INTO rights.rights_assessment_visual_reference (
  rights_assessment_id, external_visual_reference_id
)
SELECT rights_assessment_id::uuid, external_visual_reference_id::uuid
FROM gda_stage_rights_assessments;

INSERT INTO rights.rights_assessment_observation (
  rights_assessment_id, rights_observation_id, evidence_role
)
SELECT rights_assessment_id::uuid, rights_observation_id::uuid,
  evidence_role::provenance.evidence_role
FROM gda_stage_rights_assessments;

INSERT INTO rights.provider_policy_evaluation (
  provider_policy_evaluation_id, object_visual_reference_id, evaluated_state,
  evaluator_actor, evaluated_at, supersedes_provider_policy_evaluation_id
)
SELECT
  provider_policy_evaluation_id::uuid, object_visual_reference_id::uuid,
  evaluated_state::rights.policy_state,
  pg_temp.gda_b64_json_scalar(evaluator_actor_json_b64),
  evaluated_at::timestamptz,
  NULL
FROM gda_stage_policy_evaluations;

INSERT INTO rights.delivery_assessment (
  delivery_assessment_id, object_visual_reference_id, attribution_bundle_id,
  delivery_mode, reason_code, assessor_actor, assessed_at,
  supersedes_delivery_assessment_id, machine_reason_code
)
SELECT
  delivery_assessment_id::uuid, object_visual_reference_id::uuid, NULL,
  delivery_mode::rights.delivery_mode, reason_code::rights.delivery_rule_id,
  pg_temp.gda_b64_json_scalar(assessor_actor_json_b64), assessed_at::timestamptz,
  NULL, rights.machine_reason_for_rule(reason_code::rights.delivery_rule_id)
FROM gda_stage_delivery_assessments;

INSERT INTO rights.delivery_rights_assessment (
  delivery_assessment_id, rights_assessment_id, evidence_role
)
SELECT delivery_assessment_id::uuid, rights_assessment_id::uuid,
  rights_evidence_role::provenance.evidence_role
FROM gda_stage_delivery_assessments;

INSERT INTO rights.delivery_policy_evaluation (
  delivery_assessment_id, provider_policy_evaluation_id
)
SELECT delivery_assessment_id::uuid, provider_policy_evaluation_id::uuid
FROM gda_stage_delivery_assessments;

INSERT INTO rights.legacy_visual_surface_disposition (
  legacy_surface_ledger_id, source_fingerprint, visual_reference_count,
  locator_occurrence_count, disposition_set_sha256, classified_at
)
SELECT
  legacy_surface_ledger_id::uuid, source_fingerprint::core.sha256_hex,
  visual_reference_count::integer, locator_occurrence_count::integer,
  disposition_set_sha256::core.sha256_hex, classified_at::timestamptz
FROM gda_stage_visual_dispositions;

INSERT INTO rights.legacy_visual_surface_classification (
  legacy_surface_ledger_id, disposition, evidence_item_id
)
SELECT legacy_surface_ledger_id::uuid,
  disposition::rights.legacy_visual_disposition, NULL
FROM gda_stage_visual_classifications;

SELECT pg_temp.gda_inject('after_visual');

SELECT format(
  'PHASE2B_STAGE_END|DURABLE_INSERTS|wall_seconds=%s|wal_bytes=%s|rows=%s',
  extract(epoch FROM clock_timestamp()-:'phase2b_insert_started'::timestamptz),
  pg_wal_lsn_diff(pg_current_wal_lsn(), :'phase2b_insert_wal_started'::pg_lsn),
  (SELECT sum(row_count) FROM (VALUES
    ((SELECT count(*) FROM raw.source_asset)),
    ((SELECT count(*) FROM raw.mapping_version)),
    ((SELECT count(*) FROM raw.migration_batch)),
    ((SELECT count(*) FROM raw.source_record)),
    ((SELECT count(*) FROM raw.field_literal)),
    ((SELECT count(*) FROM core.entity)),
    ((SELECT count(*) FROM core.archive_object)),
    ((SELECT count(*) FROM raw.legacy_surface_ledger)),
    ((SELECT count(*) FROM provenance.object_source_record)),
    ((SELECT count(*) FROM provenance.assignment_folder_membership)),
    ((SELECT count(*) FROM research.trace_node)),
    ((SELECT count(*) FROM research.corpus_membership)),
    ((SELECT count(*) FROM raw.fail_closed_delta)),
    ((SELECT count(*) FROM rights.external_visual_reference)),
    ((SELECT count(*) FROM rights.object_visual_reference)),
    ((SELECT count(*) FROM rights.visual_locator)),
    ((SELECT count(*) FROM rights.rights_observation)),
    ((SELECT count(*) FROM rights.rights_assessment)),
    ((SELECT count(*) FROM rights.provider_policy_evaluation)),
    ((SELECT count(*) FROM rights.delivery_assessment))
  ) AS counts(row_count))
);

SELECT clock_timestamp() AS phase2b_parity_started,
       pg_current_wal_lsn() AS phase2b_parity_wal_started
\gset
\echo PHASE2B_STAGE_BEGIN|PARITY|:phase2b_parity_started|:phase2b_parity_wal_started

DO $parity$
DECLARE
  v_surfaces bigint;
  v_objects bigint;
  v_records bigint;
  v_links bigint;
  v_eligible bigint;
  v_held bigint;
  v_visual bigint;
  v_locators bigint;
  v_rights_assessments bigint;
  v_policy_evaluations bigint;
  v_delivery_assessments bigint;
  v_field_literals bigint;
  v_folders bigint;
  v_folder_assignments bigint;
  v_expected_surfaces bigint := current_setting('gda.phase2b.expected_surfaces')::bigint;
  v_expected_eligible bigint := current_setting('gda.phase2b.expected_eligible')::bigint;
  v_expected_held bigint := current_setting('gda.phase2b.expected_held')::bigint;
  v_expected_visual bigint := current_setting('gda.phase2b.expected_visual')::bigint;
  v_expected_locators bigint := current_setting('gda.phase2b.expected_locators')::bigint;
  v_expected_field_literals bigint := current_setting('gda.phase2b.expected_field_literals')::bigint;
  v_expected_folders bigint := current_setting('gda.phase2b.expected_folders')::bigint;
  v_expected_folder_assignments bigint := current_setting('gda.phase2b.expected_folder_assignments')::bigint;
BEGIN
  SELECT count(*) INTO v_surfaces FROM raw.legacy_surface_ledger;
  SELECT count(*) INTO v_objects FROM core.archive_object;
  SELECT count(*) INTO v_records FROM raw.source_record;
  SELECT count(*) INTO v_links FROM provenance.object_source_record;
  SELECT count(*) INTO v_eligible FROM research.corpus_membership
    WHERE disposition = 'eligible';
  SELECT count(*) INTO v_held FROM raw.fail_closed_delta
    WHERE disposition = 'held';
  SELECT count(*) INTO v_visual FROM rights.external_visual_reference;
  SELECT count(*) INTO v_locators FROM rights.visual_locator;
  SELECT count(*) INTO v_rights_assessments FROM rights.rights_assessment;
  SELECT count(*) INTO v_policy_evaluations FROM rights.provider_policy_evaluation;
  SELECT count(*) INTO v_delivery_assessments FROM rights.delivery_assessment;
  SELECT count(*) INTO v_field_literals FROM raw.field_literal;
  SELECT count(*) INTO v_folders FROM research.folder;
  SELECT count(*) INTO v_folder_assignments FROM provenance.assignment_folder_membership;
  IF v_surfaces <> v_expected_surfaces
     OR v_objects <> v_expected_surfaces
     OR v_records <> v_expected_surfaces
     OR v_links <> v_expected_surfaces
     OR v_eligible <> v_expected_eligible OR v_held <> v_expected_held
     OR v_visual <> v_expected_visual OR v_locators <> v_expected_locators
     OR v_rights_assessments <> v_expected_visual
     OR v_policy_evaluations <> v_expected_visual
     OR v_delivery_assessments <> v_expected_visual
     OR v_field_literals <> v_expected_field_literals
     OR v_field_literals <> (SELECT count(*) FROM gda_stage_field_literals)
     OR v_folders <> v_expected_folders
     OR v_folder_assignments <> v_expected_folder_assignments THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'PHASE2B_PARITY_ASSERTION_FAILED';
  END IF;
END
$parity$;

SELECT format(
  'PHASE2B_STAGE_END|PARITY|wall_seconds=%s|wal_bytes=%s|rows=%s',
  extract(epoch FROM clock_timestamp()-:'phase2b_parity_started'::timestamptz),
  pg_wal_lsn_diff(pg_current_wal_lsn(), :'phase2b_parity_wal_started'::pg_lsn),
  current_setting('gda.phase2b.expected_surfaces')
);

SELECT pg_temp.gda_inject('after_parity');

SELECT clock_timestamp() AS phase2b_analyze_started,
       pg_current_wal_lsn() AS phase2b_analyze_wal_started
\gset
\echo PHASE2B_STAGE_BEGIN|TARGETED_ANALYZE|:phase2b_analyze_started|:phase2b_analyze_wal_started
ANALYZE raw.migration_batch;
ANALYZE raw.legacy_surface_ledger;
ANALYZE core.entity;
ANALYZE core.archive_object;
ANALYZE provenance.canonical_assignment;
ANALYZE provenance.assignment_folder_membership;
ANALYZE rights.object_visual_reference;
ANALYZE rights.visual_locator;
ANALYZE rights.rights_observation;
ANALYZE rights.rights_observation_visual_reference;
ANALYZE rights.rights_assessment;
ANALYZE rights.rights_assessment_visual_reference;
ANALYZE rights.rights_assessment_observation;
ANALYZE rights.provider_policy_evaluation;
ANALYZE rights.delivery_assessment;
ANALYZE rights.delivery_rights_assessment;
ANALYZE rights.delivery_policy_evaluation;
SELECT format(
  'PHASE2B_STAGE_END|TARGETED_ANALYZE|wall_seconds=%s|wal_bytes=%s|rows=%s',
  extract(epoch FROM clock_timestamp()-:'phase2b_analyze_started'::timestamptz),
  pg_wal_lsn_diff(pg_current_wal_lsn(), :'phase2b_analyze_wal_started'::pg_lsn),
  current_setting('gda.phase2b.expected_surfaces')
);

-- Every populated constraint family receives a named, timed completion
-- boundary.  The final ALL is retained as a mandatory omission check.
SELECT set_config(
  'statement_timeout', current_setting('gda.phase2b.constraint_timeout'), true
);

SELECT clock_timestamp() AS phase2b_group_started,
       pg_current_wal_lsn() AS phase2b_group_wal_started \gset
\echo PHASE2B_CONSTRAINT_BEGIN|raw_core_cycle|:phase2b_group_started|:phase2b_group_wal_started
SET CONSTRAINTS
  raw.migration_batch_authority_exact,
  core.archive_object_surface_ledger_fk,
  raw.legacy_surface_lineage_exact,
  core.archive_object_surface_reciprocal,
  core.entity_subtype_from_entity,
  core.entity_subtype_from_archive_object
IMMEDIATE;
SELECT format(
  'PHASE2B_CONSTRAINT_END|raw_core_cycle|wall_seconds=%s|wal_bytes=%s',
  extract(epoch FROM clock_timestamp()-:'phase2b_group_started'::timestamptz),
  pg_wal_lsn_diff(pg_current_wal_lsn(), :'phase2b_group_wal_started'::pg_lsn)
);

SELECT clock_timestamp() AS phase2b_group_started,
       pg_current_wal_lsn() AS phase2b_group_wal_started \gset
\echo PHASE2B_CONSTRAINT_BEGIN|folder_assignment_shape|:phase2b_group_started|:phase2b_group_wal_started
SET CONSTRAINTS
  provenance.assignment_shape_from_assignment,
  provenance.assignment_shape_from_folder,
  provenance.assignment_supersession_parent
IMMEDIATE;
SELECT format(
  'PHASE2B_CONSTRAINT_END|folder_assignment_shape|wall_seconds=%s|wal_bytes=%s',
  extract(epoch FROM clock_timestamp()-:'phase2b_group_started'::timestamptz),
  pg_wal_lsn_diff(pg_current_wal_lsn(), :'phase2b_group_wal_started'::pg_lsn)
);

SELECT clock_timestamp() AS phase2b_group_started,
       pg_current_wal_lsn() AS phase2b_group_wal_started \gset
\echo PHASE2B_CONSTRAINT_BEGIN|visual_bridge_and_locator|:phase2b_group_started|:phase2b_group_wal_started
SET CONSTRAINTS
  rights.object_visual_reference_decision_from_bridge,
  rights.locator_supersession_parent
IMMEDIATE;
SELECT format(
  'PHASE2B_CONSTRAINT_END|visual_bridge_and_locator|wall_seconds=%s|wal_bytes=%s',
  extract(epoch FROM clock_timestamp()-:'phase2b_group_started'::timestamptz),
  pg_wal_lsn_diff(pg_current_wal_lsn(), :'phase2b_group_wal_started'::pg_lsn)
);

SELECT clock_timestamp() AS phase2b_group_started,
       pg_current_wal_lsn() AS phase2b_group_wal_started \gset
\echo PHASE2B_CONSTRAINT_BEGIN|rights_observation|:phase2b_group_started|:phase2b_group_wal_started
SET CONSTRAINTS
  rights.rights_observation_shape_from_parent,
  rights.rights_observation_shape_from_reference,
  rights.rights_observation_supersession_parent
IMMEDIATE;
SELECT format(
  'PHASE2B_CONSTRAINT_END|rights_observation|wall_seconds=%s|wal_bytes=%s',
  extract(epoch FROM clock_timestamp()-:'phase2b_group_started'::timestamptz),
  pg_wal_lsn_diff(pg_current_wal_lsn(), :'phase2b_group_wal_started'::pg_lsn)
);

SELECT clock_timestamp() AS phase2b_group_started,
       pg_current_wal_lsn() AS phase2b_group_wal_started \gset
\echo PHASE2B_CONSTRAINT_BEGIN|rights_assessment_shape_support|:phase2b_group_started|:phase2b_group_wal_started
SET CONSTRAINTS
  rights.rights_assessment_from_assessment,
  rights.rights_assessment_from_reference,
  rights.rights_assessment_from_observation_bridge,
  rights.rights_assessment_supersession_parent
IMMEDIATE;
SELECT format(
  'PHASE2B_CONSTRAINT_END|rights_assessment_shape_support|wall_seconds=%s|wal_bytes=%s',
  extract(epoch FROM clock_timestamp()-:'phase2b_group_started'::timestamptz),
  pg_wal_lsn_diff(pg_current_wal_lsn(), :'phase2b_group_wal_started'::pg_lsn)
);

SELECT clock_timestamp() AS phase2b_group_started,
       pg_current_wal_lsn() AS phase2b_group_wal_started \gset
\echo PHASE2B_CONSTRAINT_BEGIN|rights_assessment_current_leaf|:phase2b_group_started|:phase2b_group_wal_started
SET CONSTRAINTS rights.rights_assessment_one_current_leaf IMMEDIATE;
SELECT format(
  'PHASE2B_CONSTRAINT_END|rights_assessment_current_leaf|wall_seconds=%s|wal_bytes=%s',
  extract(epoch FROM clock_timestamp()-:'phase2b_group_started'::timestamptz),
  pg_wal_lsn_diff(pg_current_wal_lsn(), :'phase2b_group_wal_started'::pg_lsn)
);

SELECT clock_timestamp() AS phase2b_group_started,
       pg_current_wal_lsn() AS phase2b_group_wal_started \gset
\echo PHASE2B_CONSTRAINT_BEGIN|provider_policy|:phase2b_group_started|:phase2b_group_wal_started
SET CONSTRAINTS
  rights.provider_policy_evaluation_from_parent,
  rights.policy_evaluation_supersession_parent,
  rights.policy_evaluation_one_current_leaf
IMMEDIATE;
SELECT format(
  'PHASE2B_CONSTRAINT_END|provider_policy|wall_seconds=%s|wal_bytes=%s',
  extract(epoch FROM clock_timestamp()-:'phase2b_group_started'::timestamptz),
  pg_wal_lsn_diff(pg_current_wal_lsn(), :'phase2b_group_wal_started'::pg_lsn)
);

SELECT clock_timestamp() AS phase2b_group_started,
       pg_current_wal_lsn() AS phase2b_group_wal_started \gset
\echo PHASE2B_CONSTRAINT_BEGIN|delivery_parent_validation|:phase2b_group_started|:phase2b_group_wal_started
SET CONSTRAINTS rights.delivery_assessment_validation IMMEDIATE;
SELECT format(
  'PHASE2B_CONSTRAINT_END|delivery_parent_validation|wall_seconds=%s|wal_bytes=%s',
  extract(epoch FROM clock_timestamp()-:'phase2b_group_started'::timestamptz),
  pg_wal_lsn_diff(pg_current_wal_lsn(), :'phase2b_group_wal_started'::pg_lsn)
);

SELECT clock_timestamp() AS phase2b_group_started,
       pg_current_wal_lsn() AS phase2b_group_wal_started \gset
\echo PHASE2B_CONSTRAINT_BEGIN|delivery_rights_validation|:phase2b_group_started|:phase2b_group_wal_started
SET CONSTRAINTS rights.delivery_rights_validation IMMEDIATE;
SELECT format(
  'PHASE2B_CONSTRAINT_END|delivery_rights_validation|wall_seconds=%s|wal_bytes=%s',
  extract(epoch FROM clock_timestamp()-:'phase2b_group_started'::timestamptz),
  pg_wal_lsn_diff(pg_current_wal_lsn(), :'phase2b_group_wal_started'::pg_lsn)
);

SELECT clock_timestamp() AS phase2b_group_started,
       pg_current_wal_lsn() AS phase2b_group_wal_started \gset
\echo PHASE2B_CONSTRAINT_BEGIN|delivery_policy_validation|:phase2b_group_started|:phase2b_group_wal_started
SET CONSTRAINTS rights.delivery_policy_validation IMMEDIATE;
SELECT format(
  'PHASE2B_CONSTRAINT_END|delivery_policy_validation|wall_seconds=%s|wal_bytes=%s',
  extract(epoch FROM clock_timestamp()-:'phase2b_group_started'::timestamptz),
  pg_wal_lsn_diff(pg_current_wal_lsn(), :'phase2b_group_wal_started'::pg_lsn)
);

SELECT clock_timestamp() AS phase2b_group_started,
       pg_current_wal_lsn() AS phase2b_group_wal_started \gset
\echo PHASE2B_CONSTRAINT_BEGIN|delivery_history_and_rule|:phase2b_group_started|:phase2b_group_wal_started
SET CONSTRAINTS
  rights.delivery_supersession_parent,
  rights.delivery_assessment_one_current_leaf,
  rights.delivery_rule_pair
IMMEDIATE;
SELECT format(
  'PHASE2B_CONSTRAINT_END|delivery_history_and_rule|wall_seconds=%s|wal_bytes=%s',
  extract(epoch FROM clock_timestamp()-:'phase2b_group_started'::timestamptz),
  pg_wal_lsn_diff(pg_current_wal_lsn(), :'phase2b_group_wal_started'::pg_lsn)
);

SELECT clock_timestamp() AS phase2b_group_started,
       pg_current_wal_lsn() AS phase2b_group_wal_started \gset
\echo PHASE2B_CONSTRAINT_BEGIN|final_all_omission_check|:phase2b_group_started|:phase2b_group_wal_started
SET CONSTRAINTS ALL IMMEDIATE;
SELECT format(
  'PHASE2B_CONSTRAINT_END|final_all_omission_check|wall_seconds=%s|wal_bytes=%s',
  extract(epoch FROM clock_timestamp()-:'phase2b_group_started'::timestamptz),
  pg_wal_lsn_diff(pg_current_wal_lsn(), :'phase2b_group_wal_started'::pg_lsn)
);
