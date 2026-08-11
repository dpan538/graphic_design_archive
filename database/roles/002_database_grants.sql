\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

REVOKE ALL ON DATABASE :"database_name" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"database_name" TO
  gda_v49_phase2a_migrator,
  gda_v49_phase2a_ingest_writer,
  gda_v49_phase2a_reviewer,
  gda_v49_phase2a_publisher,
  gda_v49_phase2a_api_reader,
  gda_v49_phase2a_auditor;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA raw, core, provenance, research, rights, workflow,
  release, audit, api_v1 FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA raw, core, provenance, research, rights,
  workflow, release, audit, api_v1 FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA raw, core, provenance, research, rights,
  workflow, release, audit, api_v1 FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA raw, core, provenance, research, rights,
  workflow, release, audit, api_v1 FROM PUBLIC;
DO $revoke_existing_types$
DECLARE
  v_type record;
BEGIN
  FOR v_type IN
    SELECT n.nspname, t.typname
    FROM pg_catalog.pg_type t
    JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = ANY (ARRAY[
      'raw', 'core', 'provenance', 'research', 'rights',
      'workflow', 'release', 'audit', 'api_v1'
    ])
      AND t.typtype IN ('c', 'd', 'e')
      AND t.typname NOT LIKE '\\_%'
  LOOP
    EXECUTE pg_catalog.format(
      'REVOKE ALL PRIVILEGES ON TYPE %I.%I FROM PUBLIC',
      v_type.nspname, v_type.typname
    );
  END LOOP;
END
$revoke_existing_types$;

ALTER DEFAULT PRIVILEGES FOR ROLE gda_v49_phase2a_schema_owner
  REVOKE ALL ON TABLES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE gda_v49_phase2a_schema_owner
  REVOKE ALL ON SEQUENCES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE gda_v49_phase2a_schema_owner
  REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE gda_v49_phase2a_schema_owner
  REVOKE USAGE ON TYPES FROM PUBLIC;

GRANT USAGE ON SCHEMA raw, core, provenance, rights, workflow, release
  TO gda_v49_phase2a_ingest_writer;
GRANT USAGE ON TYPE raw.asset_authority, core.sha256_hex,
  provenance.evidence_role, rights.health_state
  TO gda_v49_phase2a_ingest_writer;
GRANT EXECUTE ON FUNCTION raw.register_source_asset(
  uuid, raw.asset_authority, text, core.sha256_hex, bytea, text, timestamptz
) TO gda_v49_phase2a_ingest_writer;
GRANT EXECUTE ON FUNCTION raw.register_source_record(
  uuid, uuid, bigint, text, bytea, core.sha256_hex, jsonb, text
) TO gda_v49_phase2a_ingest_writer;
GRANT EXECUTE ON FUNCTION raw.register_field_literal(
  uuid, uuid, text, integer, text, bytea, bigint, bigint
) TO gda_v49_phase2a_ingest_writer;
GRANT EXECUTE ON FUNCTION provenance.record_proposed_literal_assertion(
  uuid, uuid, uuid, uuid, text, text, text, uuid, text,
  uuid[], provenance.evidence_role[], uuid, text
) TO gda_v49_phase2a_ingest_writer;
GRANT EXECUTE ON FUNCTION provenance.record_proposed_entity_name_assignment(
  uuid, uuid, uuid, uuid[], provenance.evidence_role[], uuid, text
) TO gda_v49_phase2a_ingest_writer;
GRANT EXECUTE ON FUNCTION rights.record_endpoint_health_observation(
  uuid, uuid, rights.health_state, core.release_token,
  timestamptz, timestamptz, core.sha256_hex
) TO gda_v49_phase2a_ingest_writer;
GRANT EXECUTE ON FUNCTION release.append_visual_health_sidecar(
  uuid, uuid, uuid, uuid, uuid, uuid, core.sha256_hex
) TO gda_v49_phase2a_ingest_writer;
GRANT SELECT ON workflow.ingest_metadata_context
  TO gda_v49_phase2a_ingest_writer;

GRANT USAGE ON SCHEMA core, provenance, research, rights, workflow, release, audit
  TO gda_v49_phase2a_reviewer;
GRANT USAGE ON TYPE core.sha256_hex, provenance.evidence_role,
  workflow.review_outcome, rights.rights_subject_kind,
  rights.rights_evidence_state, rights.policy_state,
  rights.attribution_state, rights.delivery_mode, rights.locator_role,
  rights.takedown_scope_kind, rights.takedown_action,
  rights.delivery_rule_id, rights.delivery_reason_code,
  release.boundary_kind, release.validation_receipt_kind,
  core.release_token
  TO gda_v49_phase2a_reviewer;
GRANT EXECUTE ON FUNCTION research.record_relation_review_decision(
  uuid, uuid, workflow.review_outcome, text, uuid,
  uuid[], provenance.evidence_role[], uuid, core.sha256_hex
) TO gda_v49_phase2a_reviewer;
GRANT EXECUTE ON FUNCTION provenance.record_assertion_review_decision(
  uuid, uuid, workflow.review_outcome, text, uuid,
  uuid[], provenance.evidence_role[]
) TO gda_v49_phase2a_reviewer;
GRANT EXECUTE ON FUNCTION provenance.record_assignment_review_decision(
  uuid, uuid, workflow.review_outcome, text, uuid,
  uuid[], provenance.evidence_role[]
) TO gda_v49_phase2a_reviewer;
GRANT EXECUTE ON FUNCTION research.record_claim_review_decision(
  uuid, uuid, workflow.review_outcome, boolean, text, uuid,
  uuid[], provenance.evidence_role[]
) TO gda_v49_phase2a_reviewer;
GRANT EXECUTE ON FUNCTION workflow.claim_review_case(uuid)
  TO gda_v49_phase2a_reviewer;
GRANT EXECUTE ON FUNCTION rights.record_rights_observation(
  uuid, rights.rights_subject_kind, uuid, rights.rights_evidence_state,
  uuid, text, timestamptz, uuid
) TO gda_v49_phase2a_reviewer;
GRANT EXECUTE ON FUNCTION rights.record_object_visual_reference_review_decision(
  uuid, uuid, workflow.review_outcome, uuid, text, uuid, timestamptz
) TO gda_v49_phase2a_reviewer;
GRANT EXECUTE ON FUNCTION rights.record_rights_assessment(
  uuid, rights.rights_subject_kind, uuid, rights.rights_evidence_state,
  text, timestamptz, uuid, uuid[], provenance.evidence_role[]
) TO gda_v49_phase2a_reviewer;
GRANT EXECUTE ON FUNCTION rights.record_provider_policy_evaluation(
  uuid, uuid, rights.policy_state, uuid[], timestamptz, uuid
) TO gda_v49_phase2a_reviewer;
GRANT EXECUTE ON FUNCTION rights.record_delivery_assessment(
  uuid, uuid, uuid[], provenance.evidence_role[], uuid[], uuid,
  rights.delivery_mode, rights.delivery_rule_id, timestamptz, uuid,
  uuid[], uuid[], rights.locator_role[]
) TO gda_v49_phase2a_reviewer;
GRANT EXECUTE ON FUNCTION rights.record_takedown_override_correction(
  uuid, uuid, rights.delivery_mode, uuid
) TO gda_v49_phase2a_reviewer;
GRANT EXECUTE ON FUNCTION rights.record_attribution_bundle(
  uuid, uuid, rights.attribution_state, uuid, timestamptz, uuid,
  text[], integer[], text[], text[]
) TO gda_v49_phase2a_reviewer;
GRANT EXECUTE ON FUNCTION rights.record_takedown_event(
  uuid, rights.takedown_action, timestamptz, timestamptz, text, uuid,
  uuid[], rights.takedown_scope_kind[], uuid[], uuid[],
  rights.delivery_mode[], uuid[]
) TO gda_v49_phase2a_reviewer;
GRANT EXECUTE ON FUNCTION release.append_visual_takedown_sidecar(
  uuid, uuid, uuid, uuid, uuid, core.sha256_hex
) TO gda_v49_phase2a_reviewer;
GRANT SELECT ON workflow.reviewer_queue,
  workflow.reviewer_source_context, workflow.reviewer_provenance_context
  TO gda_v49_phase2a_reviewer;
GRANT EXECUTE ON FUNCTION release.record_research_verification(
  uuid, uuid, core.sha256_hex, core.release_token, core.sha256_hex,
  uuid, core.sha256_hex
) TO gda_v49_phase2a_reviewer;
GRANT EXECUTE ON FUNCTION release.record_visual_verification(
  uuid, uuid, core.sha256_hex, core.release_token, core.sha256_hex,
  uuid, core.sha256_hex
) TO gda_v49_phase2a_reviewer;
GRANT EXECUTE ON FUNCTION release.record_research_validation_receipt(
  uuid, uuid, release.validation_receipt_kind, core.release_token,
  core.sha256_hex, bytea, uuid
) TO gda_v49_phase2a_reviewer;
GRANT EXECUTE ON FUNCTION release.record_visual_validation_receipt(
  uuid, uuid, release.validation_receipt_kind, core.release_token,
  core.sha256_hex, bytea, uuid
) TO gda_v49_phase2a_reviewer;
GRANT EXECUTE ON FUNCTION release.build_validation_receipt_bytes(
  release.boundary_kind, uuid, release.validation_receipt_kind,
  core.release_token, core.sha256_hex
) TO gda_v49_phase2a_reviewer;

GRANT USAGE ON SCHEMA core, provenance, research, rights, workflow, release
  TO gda_v49_phase2a_publisher;
GRANT USAGE ON TYPE core.release_token, core.sha256_hex,
  provenance.assertion_status, research.membership_disposition,
  workflow.queue_state, rights.delivery_mode, rights.reference_role,
  rights.locator_role, rights.delivery_rule_id,
  rights.delivery_reason_code, release.research_source_role,
  release.publication_layer, release.count_eligibility
  TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.create_research_release(
  uuid, core.release_token, core.release_token, core.release_token,
  uuid, core.sha256_hex
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.close_research_candidate(
  uuid, core.sha256_hex, uuid, core.sha256_hex
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.validate_research_release(
  uuid, uuid, core.release_token, core.sha256_hex, uuid, core.sha256_hex
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.seal_research_release(
  uuid, uuid, uuid, core.sha256_hex
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.create_visual_registry(
  uuid, core.release_token, core.release_token, core.release_token,
  uuid, core.sha256_hex, uuid, core.sha256_hex
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.add_research_object_to_draft(uuid, uuid, uuid)
  TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.add_research_claim_to_draft(uuid, uuid)
  TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.add_research_relation_to_draft(uuid, uuid, uuid)
  TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.add_trace_node_to_draft(uuid, uuid, uuid, uuid)
  TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.add_trace_edge_to_draft(
  uuid, uuid, uuid, uuid, uuid, text
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.copy_visual_entry_to_draft(
  uuid, uuid, uuid, uuid
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.add_research_source_lineage_to_draft(
  uuid, release.research_source_role, uuid, text
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.set_research_projection_set_to_draft(
  uuid, text, core.sha256_hex, core.sha256_hex
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.set_research_registry_snapshot_to_draft(
  uuid, core.sha256_hex, core.sha256_hex, core.sha256_hex
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.copy_research_corpus_snapshot_to_draft(
  uuid, uuid, uuid, uuid, core.sha256_hex
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.add_research_count_snapshot_to_draft(
  uuid, core.release_token, text, text, core.sha256_hex, bigint
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.add_research_asset_to_draft(
  uuid, text, core.release_token, text, text, text, bigint, bigint,
  core.sha256_hex, text, text, core.sha256_hex
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.add_research_asset_dependency_to_draft(
  uuid, text, text
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.add_research_membership_projection_to_draft(
  uuid, uuid, uuid, uuid, text, release.publication_layer,
  text, release.count_eligibility, text
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.add_research_metric_eligibility_to_draft(
  uuid, uuid, text, release.count_eligibility, text
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.copy_research_folder_to_draft(uuid, uuid)
  TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.copy_legacy_identity_resolution_to_draft(
  uuid, uuid, uuid
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.copy_trace_tree_to_draft(uuid, uuid, uuid)
  TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.copy_trace_branch_to_draft(
  uuid, uuid, uuid, uuid
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.copy_trace_node_placement_to_draft(
  uuid, uuid, uuid, uuid, uuid, core.release_token
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.add_trace_edge_placement_to_draft(
  uuid, uuid, uuid, uuid, uuid, text, uuid, uuid, core.release_token
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.set_visual_policy_input_to_draft(
  uuid, core.sha256_hex, core.sha256_hex, core.sha256_hex,
  core.sha256_hex, core.sha256_hex
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.snapshot_legacy_visual_baseline_to_draft(
  uuid, core.sha256_hex
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.add_visual_asset_to_draft(
  uuid, text, core.release_token, text, text, text, bigint, bigint,
  core.sha256_hex, text, text, core.sha256_hex
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.add_visual_asset_dependency_to_draft(
  uuid, text, text
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.close_visual_candidate(
  uuid, core.sha256_hex, uuid, core.sha256_hex
) TO gda_v49_phase2a_publisher;
GRANT SELECT ON release.publisher_research_source,
  release.publisher_visual_source, release.publisher_artifact_inventory
  TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.validate_visual_registry(
  uuid, uuid, core.release_token, core.sha256_hex, uuid, core.sha256_hex
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.seal_visual_registry(
  uuid, uuid, uuid, core.sha256_hex
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.initialize_research_current(core.release_token)
  TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.initialize_visual_current(core.release_token)
  TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.promote_research_current_cas(
  uuid, core.release_token, bigint, uuid, core.sha256_hex, uuid
) TO gda_v49_phase2a_publisher;
GRANT EXECUTE ON FUNCTION release.promote_visual_current_cas(
  uuid, core.release_token, bigint, uuid, core.sha256_hex,
  core.release_token, bigint, uuid, core.sha256_hex, uuid
) TO gda_v49_phase2a_publisher;

GRANT USAGE ON SCHEMA api_v1 TO gda_v49_phase2a_api_reader;
GRANT SELECT ON api_v1.current_version_status,
  api_v1.current_object, api_v1.research_release_descriptor
  TO gda_v49_phase2a_api_reader;

GRANT USAGE ON SCHEMA audit, api_v1 TO gda_v49_phase2a_auditor;
GRANT SELECT ON audit.raw_hash_inventory,
  audit.release_history_inventory, audit.role_grant_inventory,
  audit.decision_event_inventory,
  api_v1.current_version_status, api_v1.research_release_descriptor
  TO gda_v49_phase2a_auditor;

RESET ROLE;
