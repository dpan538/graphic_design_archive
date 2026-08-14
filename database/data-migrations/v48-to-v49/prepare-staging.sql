-- Phase 2B only: transient staging relations for the deterministic Candidate
-- bundle.  They are intentionally all-text: decoding and casting is explicit
-- in load.sql, and no staging relation survives the caller transaction.
\set ON_ERROR_STOP on

CREATE TEMP TABLE gda_stage_source_assets (
  source_asset_id text, authority text, logical_name_json_b64 text, sha256 text,
  byte_length text, raw_bytes_b64 text, media_type_json_b64 text, received_at text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_mapping_versions (
  mapping_version_id text, version_token_json_b64 text, specification_sha256 text,
  parser_version_json_b64 text, delimiter_policy text, created_at text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_migration_batches (
  migration_batch_id text, batch_token_json_b64 text, canonical_input_asset_id text,
  mapping_version_id text, input_sha256 text, started_at text, completed_at text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_source_records (
  source_record_id text, record_ordinal text, legacy_source_record_id_json_b64 text,
  raw_value_b64 text, raw_fingerprint text, parsed_projection_b64 text, semantic_sha256 text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_field_literals (
  field_literal_id text, source_record_id text, json_pointer_json_b64 text,
  occurrence_ordinal text, raw_value_b64 text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_entities (
  entity_id text, entity_kind text, lifecycle_state text, created_at text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_archive_objects (
  archive_object_id text, operational_semantics_version_json_b64 text,
  preferred_label_json_b64 text, legacy_surface_ledger_id text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_surface_ledgers (
  legacy_surface_ledger_id text, source_record_id text, canonical_input_asset_id text,
  input_ordinal text, surface_id_json_b64 text, legacy_source_record_id_json_b64 text,
  source_fingerprint text, import_disposition text, archive_object_id text,
  reason_code_json_b64 text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_object_source_links (
  archive_object_id text, source_record_id text, source_role text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_legacy_identities (
  legacy_identity_id text, identity_kind text, namespace_json_b64 text,
  legacy_id_json_b64 text, created_at text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_folders (
  folder_id text, folder_token_json_b64 text, label_json_b64 text, created_at text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_folder_assignments (
  canonical_assignment_id text, assignment_kind text, status text, created_at text,
  folder_id text, archive_object_id text, membership_role text, member_ordinal text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_legacy_resolutions (
  legacy_identity_resolution_id text, legacy_identity_id text, resolution_state text,
  target_archive_object_id text, target_source_record_id text, target_trace_node_id text,
  effective_from text, reason_code_json_b64 text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_trace_nodes (
  trace_node_id text, canonical_key_json_b64 text, label_json_b64 text, entity_id text,
  node_type_json_b64 text, created_at text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_object_trace_nodes (
  archive_object_id text, trace_node_id text, node_role_json_b64 text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_corpora (
  corpus_id text, corpus_token_json_b64 text, label_json_b64 text, created_at text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_corpus_versions (
  corpus_version_id text, corpus_id text, version_token_json_b64 text,
  policy_version_json_b64 text, policy_sha256 text, population_frame_json_b64 text,
  created_at text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_corpus_memberships (
  corpus_version_id text, archive_object_id text, disposition text,
  reason_code_json_b64 text, decided_by_json_b64 text, decided_at text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_held_deltas (
  fail_closed_delta_id text, migration_batch_id text, source_record_id text,
  expected_classification_json_b64 text, actual_literal_json_b64 text,
  reason_code_json_b64 text, disposition text, recorded_at text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_visual_references (
  external_visual_reference_id text, source_asset_id text, source_record_id text,
  pointer_json_b64 text, occurrence_ordinal text, reference_fingerprint text, created_at text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_visual_bridges (
  object_visual_reference_id text, archive_object_id text, external_visual_reference_id text,
  reference_role text, ordinal text, acceptance_state text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_visual_locators (
  visual_locator_id text, external_visual_reference_id text, locator_role text,
  source_asset_id text, source_record_id text, pointer_json_b64 text,
  occurrence_ordinal text, visibility text, raw_locator_json_b64 text,
  locator_fingerprint text, created_at text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_visual_dispositions (
  legacy_surface_ledger_id text, source_fingerprint text, visual_reference_count text,
  locator_occurrence_count text, disposition_set_sha256 text, classified_at text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_visual_classifications (
  legacy_surface_ledger_id text, disposition text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_rights_observations (
  rights_observation_id text, external_visual_reference_id text, evidence_state text,
  observed_wording_json_b64 text, observed_at text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_rights_assessments (
  rights_assessment_id text, external_visual_reference_id text, assessed_state text,
  reviewer_actor_json_b64 text, rationale_json_b64 text, assessed_at text,
  rights_observation_id text, evidence_role text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_policy_evaluations (
  provider_policy_evaluation_id text, object_visual_reference_id text,
  evaluated_state text, evaluator_actor_json_b64 text, evaluated_at text
) ON COMMIT DROP;
CREATE TEMP TABLE gda_stage_delivery_assessments (
  delivery_assessment_id text, object_visual_reference_id text, delivery_mode text,
  reason_code text, assessor_actor_json_b64 text, assessed_at text,
  rights_assessment_id text, rights_evidence_role text,
  provider_policy_evaluation_id text
) ON COMMIT DROP;
