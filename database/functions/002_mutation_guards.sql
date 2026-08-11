\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

CREATE FUNCTION audit.reject_update_delete()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  RAISE EXCEPTION USING ERRCODE = '55000',
    MESSAGE = 'APPEND_ONLY_HISTORY_MUTATION_DENIED';
END
$function$;

CREATE FUNCTION audit.reject_identity_reassignment()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  IF to_jsonb(NEW) -> TG_ARGV[0] IS DISTINCT FROM to_jsonb(OLD) -> TG_ARGV[0] THEN
    RAISE EXCEPTION USING ERRCODE = '55000',
      MESSAGE = 'TYPED_IDENTITY_REASSIGNMENT_DENIED';
  END IF;
  RETURN NEW;
END
$function$;

CREATE TRIGGER archive_object_identity_immutable BEFORE UPDATE ON core.archive_object
  FOR EACH ROW EXECUTE FUNCTION audit.reject_identity_reassignment('archive_object_id');
CREATE TRIGGER agent_identity_immutable BEFORE UPDATE ON core.agent
  FOR EACH ROW EXECUTE FUNCTION audit.reject_identity_reassignment('agent_id');
CREATE TRIGGER place_identity_immutable BEFORE UPDATE ON core.place
  FOR EACH ROW EXECUTE FUNCTION audit.reject_identity_reassignment('place_id');
CREATE TRIGGER concept_identity_immutable BEFORE UPDATE ON core.concept
  FOR EACH ROW EXECUTE FUNCTION audit.reject_identity_reassignment('concept_id');
CREATE TRIGGER collection_identity_immutable BEFORE UPDATE ON core.collection
  FOR EACH ROW EXECUTE FUNCTION audit.reject_identity_reassignment('collection_id');
CREATE TRIGGER temporal_identity_immutable BEFORE UPDATE ON core.temporal_extent
  FOR EACH ROW EXECUTE FUNCTION audit.reject_identity_reassignment('temporal_extent_id');
CREATE TRIGGER relation_subject_identity_immutable BEFORE UPDATE ON research.semantic_relation
  FOR EACH ROW EXECUTE FUNCTION audit.reject_identity_reassignment('subject_endpoint_id');
CREATE TRIGGER relation_type_identity_immutable BEFORE UPDATE ON research.semantic_relation
  FOR EACH ROW EXECUTE FUNCTION audit.reject_identity_reassignment('relation_type_id');
CREATE TRIGGER relation_object_identity_immutable BEFORE UPDATE ON research.semantic_relation
  FOR EACH ROW EXECUTE FUNCTION audit.reject_identity_reassignment('object_endpoint_id');
CREATE TRIGGER claim_revision_claim_identity_immutable BEFORE UPDATE ON research.claim_revision
  FOR EACH ROW EXECUTE FUNCTION audit.reject_identity_reassignment('claim_id');
CREATE TRIGGER object_visual_reference_object_immutable BEFORE UPDATE ON rights.object_visual_reference
  FOR EACH ROW EXECUTE FUNCTION audit.reject_identity_reassignment('archive_object_id');
CREATE TRIGGER object_visual_reference_reference_immutable BEFORE UPDATE ON rights.object_visual_reference
  FOR EACH ROW EXECUTE FUNCTION audit.reject_identity_reassignment('external_visual_reference_id');
CREATE TRIGGER object_visual_reference_role_immutable BEFORE UPDATE ON rights.object_visual_reference
  FOR EACH ROW EXECUTE FUNCTION audit.reject_identity_reassignment('reference_role');

CREATE TRIGGER audit_review_event_append_only BEFORE UPDATE OR DELETE ON audit.review_event
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER audit_decision_event_append_only BEFORE UPDATE OR DELETE ON audit.decision_event
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER audit_decision_assertion_append_only BEFORE UPDATE OR DELETE ON audit.decision_event_assertion_review
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER audit_decision_assignment_append_only BEFORE UPDATE OR DELETE ON audit.decision_event_assignment_review
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER audit_decision_claim_append_only BEFORE UPDATE OR DELETE ON audit.decision_event_claim_review
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER audit_decision_relation_append_only BEFORE UPDATE OR DELETE ON audit.decision_event_relation_review
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER audit_decision_observation_append_only BEFORE UPDATE OR DELETE ON audit.decision_event_rights_observation
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER audit_decision_assessment_append_only BEFORE UPDATE OR DELETE ON audit.decision_event_rights_assessment
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER audit_decision_policy_append_only BEFORE UPDATE OR DELETE ON audit.decision_event_policy_evaluation
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER audit_decision_delivery_append_only BEFORE UPDATE OR DELETE ON audit.decision_event_delivery_assessment
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER audit_decision_attribution_append_only BEFORE UPDATE OR DELETE ON audit.decision_event_attribution_validation
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER audit_decision_takedown_append_only BEFORE UPDATE OR DELETE ON audit.decision_event_takedown
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER audit_decision_visual_bridge_append_only
BEFORE UPDATE OR DELETE ON audit.decision_event_visual_bridge_review
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER audit_research_release_event_append_only BEFORE UPDATE OR DELETE ON audit.research_release_event
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER audit_visual_release_event_append_only BEFORE UPDATE OR DELETE ON audit.visual_release_event
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER audit_research_seal_event_append_only BEFORE UPDATE OR DELETE ON audit.research_seal_event
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER audit_visual_seal_event_append_only BEFORE UPDATE OR DELETE ON audit.visual_seal_event
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER audit_research_cas_append_only BEFORE UPDATE OR DELETE ON audit.research_cas_attempt
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER audit_visual_cas_append_only BEFORE UPDATE OR DELETE ON audit.visual_cas_attempt
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER audit_verification_append_only BEFORE UPDATE OR DELETE ON audit.verification_receipt_event
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER audit_sidecar_append_only BEFORE UPDATE OR DELETE ON audit.sidecar_event
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();

CREATE TRIGGER source_asset_append_only BEFORE UPDATE OR DELETE ON raw.source_asset
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER source_record_append_only BEFORE UPDATE OR DELETE ON raw.source_record
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER field_literal_append_only BEFORE UPDATE OR DELETE ON raw.field_literal
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER mapping_version_append_only BEFORE UPDATE OR DELETE ON raw.mapping_version
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER migration_batch_append_only BEFORE UPDATE OR DELETE ON raw.migration_batch
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER legacy_surface_ledger_append_only BEFORE UPDATE OR DELETE ON raw.legacy_surface_ledger
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER fail_closed_delta_append_only BEFORE UPDATE OR DELETE ON raw.fail_closed_delta
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER legacy_identity_append_only BEFORE UPDATE OR DELETE ON core.legacy_identity
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER legacy_identity_resolution_append_only BEFORE UPDATE OR DELETE ON core.legacy_identity_resolution
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER legacy_identity_split_append_only BEFORE UPDATE OR DELETE ON core.legacy_identity_split_successor
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER source_document_append_only BEFORE UPDATE OR DELETE ON provenance.source_document
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER source_version_append_only BEFORE UPDATE OR DELETE ON provenance.source_version
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER evidence_item_append_only BEFORE UPDATE OR DELETE ON provenance.evidence_item
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assertion_subject_entity_append_only BEFORE UPDATE OR DELETE ON provenance.assertion_subject_entity
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assertion_subject_source_append_only BEFORE UPDATE OR DELETE ON provenance.assertion_subject_source_record
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assertion_subject_trace_append_only BEFORE UPDATE OR DELETE ON provenance.assertion_subject_trace_node
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assertion_subject_representation_append_only BEFORE UPDATE OR DELETE ON provenance.assertion_subject_representation
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assertion_value_literal_append_only BEFORE UPDATE OR DELETE ON provenance.assertion_value_literal
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assertion_value_entity_append_only BEFORE UPDATE OR DELETE ON provenance.assertion_value_entity
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assertion_value_source_append_only BEFORE UPDATE OR DELETE ON provenance.assertion_value_source_record
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assertion_value_trace_append_only BEFORE UPDATE OR DELETE ON provenance.assertion_value_trace_node
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assignment_entity_name_append_only BEFORE UPDATE OR DELETE ON provenance.assignment_entity_name
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assignment_source_append_only BEFORE UPDATE OR DELETE ON provenance.assignment_object_source_record
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assignment_agent_append_only BEFORE UPDATE OR DELETE ON provenance.assignment_object_agent_credit
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assignment_medium_append_only BEFORE UPDATE OR DELETE ON provenance.assignment_object_medium
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assignment_type_append_only BEFORE UPDATE OR DELETE ON provenance.assignment_object_type
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assignment_subject_append_only BEFORE UPDATE OR DELETE ON provenance.assignment_object_subject
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assignment_collection_append_only BEFORE UPDATE OR DELETE ON provenance.assignment_object_collection
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assignment_temporal_append_only BEFORE UPDATE OR DELETE ON provenance.assignment_object_temporal
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assignment_place_append_only BEFORE UPDATE OR DELETE ON provenance.assignment_object_place
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assignment_folder_append_only BEFORE UPDATE OR DELETE ON provenance.assignment_folder_membership
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assignment_tree_append_only BEFORE UPDATE OR DELETE ON provenance.assignment_object_tree_membership
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assignment_representation_append_only BEFORE UPDATE OR DELETE ON provenance.assignment_object_representation
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assignment_identity_append_only BEFORE UPDATE OR DELETE ON provenance.assignment_identity_resolution
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assignment_decision_append_only BEFORE UPDATE OR DELETE ON provenance.assignment_review_decision
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assignment_decision_evidence_append_only BEFORE UPDATE OR DELETE ON provenance.assignment_decision_evidence
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assignment_context_evidence_append_only BEFORE UPDATE OR DELETE ON provenance.assignment_context_evidence
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assertion_evidence_append_only BEFORE UPDATE OR DELETE ON provenance.assertion_evidence
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assertion_decision_append_only BEFORE UPDATE OR DELETE ON provenance.assertion_review_decision
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assertion_decision_evidence_append_only BEFORE UPDATE OR DELETE ON provenance.assertion_decision_evidence
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assignment_assertion_append_only BEFORE UPDATE OR DELETE ON provenance.assignment_assertion
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER claim_decision_append_only BEFORE UPDATE OR DELETE ON research.claim_review_decision
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER claim_decision_evidence_append_only BEFORE UPDATE OR DELETE ON research.claim_decision_evidence
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER relation_decision_append_only BEFORE UPDATE OR DELETE ON research.relation_review_decision
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER relation_decision_evidence_append_only BEFORE UPDATE OR DELETE ON research.relation_decision_evidence
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER relation_endpoint_append_only BEFORE UPDATE OR DELETE ON research.relation_endpoint
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER relation_endpoint_entity_append_only BEFORE UPDATE OR DELETE ON research.relation_endpoint_entity
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER relation_context_evidence_append_only BEFORE UPDATE OR DELETE ON research.relation_context_evidence
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER claim_evidence_append_only BEFORE UPDATE OR DELETE ON research.claim_evidence
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER relation_claim_append_only BEFORE UPDATE OR DELETE ON research.relation_claim
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER object_visual_reference_decision_append_only
BEFORE UPDATE OR DELETE ON rights.object_visual_reference_review_decision
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();

CREATE TRIGGER provider_append_only BEFORE UPDATE OR DELETE ON rights.provider
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER provider_object_append_only BEFORE UPDATE OR DELETE ON rights.provider_object
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER digital_representation_append_only BEFORE UPDATE OR DELETE ON rights.digital_representation
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER visual_reference_append_only BEFORE UPDATE OR DELETE ON rights.external_visual_reference
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER visual_reference_representation_append_only BEFORE UPDATE OR DELETE ON rights.visual_reference_representation
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER visual_locator_append_only BEFORE UPDATE OR DELETE ON rights.visual_locator
FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER visual_locator_representation_append_only
BEFORE UPDATE OR DELETE ON rights.visual_locator_representation
FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();

CREATE TRIGGER rights_observation_append_only BEFORE UPDATE OR DELETE ON rights.rights_observation
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER rights_observation_provider_object_append_only BEFORE UPDATE OR DELETE ON rights.rights_observation_provider_object
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER rights_observation_reference_append_only BEFORE UPDATE OR DELETE ON rights.rights_observation_visual_reference
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER rights_observation_representation_append_only BEFORE UPDATE OR DELETE ON rights.rights_observation_representation
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER rights_observation_locator_append_only BEFORE UPDATE OR DELETE ON rights.rights_observation_locator
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER rights_assessment_append_only BEFORE UPDATE OR DELETE ON rights.rights_assessment
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER rights_assessment_provider_object_append_only BEFORE UPDATE OR DELETE ON rights.rights_assessment_provider_object
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER rights_assessment_reference_append_only BEFORE UPDATE OR DELETE ON rights.rights_assessment_visual_reference
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER rights_assessment_representation_append_only BEFORE UPDATE OR DELETE ON rights.rights_assessment_representation
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER rights_assessment_locator_append_only BEFORE UPDATE OR DELETE ON rights.rights_assessment_locator
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER rights_assessment_observation_append_only BEFORE UPDATE OR DELETE ON rights.rights_assessment_observation
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER provider_policy_version_append_only BEFORE UPDATE OR DELETE ON rights.provider_policy_version
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER provider_policy_evaluation_append_only BEFORE UPDATE OR DELETE ON rights.provider_policy_evaluation
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER provider_policy_evaluation_version_append_only BEFORE UPDATE OR DELETE ON rights.provider_policy_evaluation_version
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER attribution_bundle_append_only BEFORE UPDATE OR DELETE ON rights.attribution_bundle
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER attribution_bundle_value_append_only BEFORE UPDATE OR DELETE ON rights.attribution_bundle_value
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER delivery_assessment_append_only BEFORE UPDATE OR DELETE ON rights.delivery_assessment
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER delivery_rights_append_only BEFORE UPDATE OR DELETE ON rights.delivery_rights_assessment
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER delivery_policy_append_only BEFORE UPDATE OR DELETE ON rights.delivery_policy_evaluation
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER delivery_locator_append_only BEFORE UPDATE OR DELETE ON rights.delivery_locator_qualification
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER endpoint_health_observation_append_only BEFORE UPDATE OR DELETE ON rights.endpoint_health_observation
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER takedown_event_append_only BEFORE UPDATE OR DELETE ON rights.takedown_event
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER takedown_scope_append_only BEFORE UPDATE OR DELETE ON rights.takedown_scope
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER takedown_scope_provider_append_only BEFORE UPDATE OR DELETE ON rights.takedown_scope_provider
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER takedown_scope_provider_object_append_only BEFORE UPDATE OR DELETE ON rights.takedown_scope_provider_object
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER takedown_scope_reference_append_only BEFORE UPDATE OR DELETE ON rights.takedown_scope_visual_reference
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER takedown_scope_representation_append_only BEFORE UPDATE OR DELETE ON rights.takedown_scope_representation
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER takedown_scope_locator_append_only BEFORE UPDATE OR DELETE ON rights.takedown_scope_locator
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER takedown_scope_bridge_append_only BEFORE UPDATE OR DELETE ON rights.takedown_scope_object_visual_reference
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER takedown_override_append_only BEFORE UPDATE OR DELETE ON rights.takedown_override
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();

CREATE FUNCTION release.guard_research_release_parent()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  IF TG_OP = 'DELETE' THEN
    IF OLD.release_state <> 'draft' THEN
      RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RESEARCH_RELEASE_NOT_DELETABLE';
    END IF;
    RETURN OLD;
  END IF;
  IF OLD.release_state = 'sealed' THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'SEALED_RELEASE_IMMUTABLE';
  END IF;
  IF OLD.release_token IS DISTINCT FROM NEW.release_token
    OR OLD.schema_version IS DISTINCT FROM NEW.schema_version
    OR OLD.model_version IS DISTINCT FROM NEW.model_version
    OR OLD.created_at IS DISTINCT FROM NEW.created_at THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RELEASE_IDENTITY_MUTATION_DENIED';
  END IF;
  IF NOT (
    (OLD.release_state = 'draft' AND NEW.release_state = 'candidate')
    OR (OLD.release_state = 'candidate' AND NEW.release_state = 'validated')
    OR (OLD.release_state = 'validated' AND NEW.release_state = 'sealed')
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'INVALID_RESEARCH_RELEASE_TRANSITION';
  END IF;
  RETURN NEW;
END
$function$;

CREATE TRIGGER guard_research_release_parent BEFORE UPDATE OR DELETE ON release.research_release
  FOR EACH ROW EXECUTE FUNCTION release.guard_research_release_parent();

CREATE FUNCTION release.guard_visual_release_parent()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  IF TG_OP = 'DELETE' THEN
    IF OLD.release_state <> 'draft' THEN
      RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'VISUAL_REGISTRY_NOT_DELETABLE';
    END IF;
    RETURN OLD;
  END IF;
  IF OLD.release_state = 'sealed' THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'SEALED_VISUAL_REGISTRY_IMMUTABLE';
  END IF;
  IF OLD.registry_version IS DISTINCT FROM NEW.registry_version
    OR OLD.schema_version IS DISTINCT FROM NEW.schema_version
    OR OLD.model_version IS DISTINCT FROM NEW.model_version
    OR OLD.created_at IS DISTINCT FROM NEW.created_at
    OR OLD.compatible_research_release_id IS DISTINCT FROM NEW.compatible_research_release_id
    OR OLD.compatible_research_manifest_sha256 IS DISTINCT FROM NEW.compatible_research_manifest_sha256 THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'VISUAL_REGISTRY_IDENTITY_MUTATION_DENIED';
  END IF;
  IF NOT (
    (OLD.release_state = 'draft' AND NEW.release_state = 'candidate')
    OR (OLD.release_state = 'candidate' AND NEW.release_state = 'validated')
    OR (OLD.release_state = 'validated' AND NEW.release_state = 'sealed')
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'INVALID_VISUAL_RELEASE_TRANSITION';
  END IF;
  RETURN NEW;
END
$function$;

CREATE TRIGGER guard_visual_release_parent BEFORE UPDATE OR DELETE ON release.visual_registry_release
  FOR EACH ROW EXECUTE FUNCTION release.guard_visual_release_parent();

CREATE FUNCTION release.guard_research_projection_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_new jsonb := CASE WHEN TG_OP = 'DELETE' THEN NULL ELSE to_jsonb(NEW) END;
  v_old jsonb := CASE WHEN TG_OP = 'INSERT' THEN NULL ELSE to_jsonb(OLD) END;
  v_release_id uuid := COALESCE(
    (v_new ->> 'research_release_id')::uuid,
    (v_old ->> 'research_release_id')::uuid
  );
  v_state release.release_state;
BEGIN
  IF TG_OP = 'UPDATE'
    AND (v_new ->> 'research_release_id') IS DISTINCT FROM (v_old ->> 'research_release_id') THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RESEARCH_PROJECTION_REPARENT_DENIED';
  END IF;
  SELECT r.release_state INTO v_state
  FROM release.research_release r
  WHERE r.research_release_id = v_release_id
  FOR SHARE;
  IF v_state IS DISTINCT FROM 'draft'::release.release_state THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RESEARCH_PROJECTION_CLOSED';
  END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END
$function$;

CREATE TRIGGER guard_research_release_object BEFORE INSERT OR UPDATE OR DELETE ON release.research_release_object
  FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_research_release_corpus BEFORE INSERT OR UPDATE OR DELETE ON release.research_release_corpus_member
  FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_research_release_claim BEFORE INSERT OR UPDATE OR DELETE ON release.research_release_claim
  FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_research_release_relation BEFORE INSERT OR UPDATE OR DELETE ON release.research_release_relation
  FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_trace_projection_node BEFORE INSERT OR UPDATE OR DELETE ON release.trace_projection_node
  FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_trace_projection_edge BEFORE INSERT OR UPDATE OR DELETE ON release.trace_projection_edge
  FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_object_relation_membership_projection BEFORE INSERT OR UPDATE OR DELETE ON release.object_relation_membership_projection
  FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_research_metric_eligibility BEFORE INSERT OR UPDATE OR DELETE ON release.research_object_metric_eligibility
  FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();

CREATE FUNCTION release.guard_visual_projection_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_new jsonb := CASE WHEN TG_OP = 'DELETE' THEN NULL ELSE to_jsonb(NEW) END;
  v_old jsonb := CASE WHEN TG_OP = 'INSERT' THEN NULL ELSE to_jsonb(OLD) END;
  v_release_id uuid := COALESCE(
    (v_new ->> 'visual_registry_release_id')::uuid,
    (v_old ->> 'visual_registry_release_id')::uuid
  );
  v_state release.release_state;
BEGIN
  IF TG_OP = 'UPDATE'
    AND (v_new ->> 'visual_registry_release_id') IS DISTINCT FROM (v_old ->> 'visual_registry_release_id') THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'VISUAL_PROJECTION_REPARENT_DENIED';
  END IF;
  SELECT r.release_state INTO v_state
  FROM release.visual_registry_release r
  WHERE r.visual_registry_release_id = v_release_id
  FOR SHARE;
  IF v_state IS DISTINCT FROM 'draft'::release.release_state THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'VISUAL_PROJECTION_CLOSED';
  END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END
$function$;

CREATE TRIGGER guard_visual_provider_snapshot BEFORE INSERT OR UPDATE OR DELETE ON release.visual_registry_provider_snapshot
  FOR EACH ROW EXECUTE FUNCTION release.guard_visual_projection_mutation();
CREATE TRIGGER guard_visual_provider_object_snapshot BEFORE INSERT OR UPDATE OR DELETE ON release.visual_registry_provider_object_snapshot
  FOR EACH ROW EXECUTE FUNCTION release.guard_visual_projection_mutation();
CREATE TRIGGER guard_visual_reference_snapshot BEFORE INSERT OR UPDATE OR DELETE ON release.visual_registry_reference_snapshot
  FOR EACH ROW EXECUTE FUNCTION release.guard_visual_projection_mutation();
CREATE TRIGGER guard_visual_bridge_snapshot BEFORE INSERT OR UPDATE OR DELETE ON release.visual_registry_bridge_snapshot
  FOR EACH ROW EXECUTE FUNCTION release.guard_visual_projection_mutation();
CREATE TRIGGER guard_visual_rights_snapshot BEFORE INSERT OR UPDATE OR DELETE ON release.visual_registry_rights_assessment_snapshot
  FOR EACH ROW EXECUTE FUNCTION release.guard_visual_projection_mutation();
CREATE TRIGGER guard_visual_rights_observation_snapshot BEFORE INSERT OR UPDATE OR DELETE ON release.visual_registry_rights_observation_snapshot
  FOR EACH ROW EXECUTE FUNCTION release.guard_visual_projection_mutation();
CREATE TRIGGER guard_visual_policy_version_snapshot BEFORE INSERT OR UPDATE OR DELETE ON release.visual_registry_policy_version_snapshot
  FOR EACH ROW EXECUTE FUNCTION release.guard_visual_projection_mutation();
CREATE TRIGGER guard_visual_policy_evaluation_snapshot BEFORE INSERT OR UPDATE OR DELETE ON release.visual_registry_policy_evaluation_snapshot
  FOR EACH ROW EXECUTE FUNCTION release.guard_visual_projection_mutation();
CREATE TRIGGER guard_visual_policy_evaluation_version_snapshot BEFORE INSERT OR UPDATE OR DELETE ON release.visual_registry_policy_evaluation_version_snapshot
  FOR EACH ROW EXECUTE FUNCTION release.guard_visual_projection_mutation();
CREATE TRIGGER guard_visual_delivery_snapshot BEFORE INSERT OR UPDATE OR DELETE ON release.visual_registry_delivery_snapshot
  FOR EACH ROW EXECUTE FUNCTION release.guard_visual_projection_mutation();
CREATE TRIGGER guard_visual_delivery_rights_snapshot BEFORE INSERT OR UPDATE OR DELETE ON release.visual_registry_delivery_rights_snapshot
  FOR EACH ROW EXECUTE FUNCTION release.guard_visual_projection_mutation();
CREATE TRIGGER guard_visual_delivery_policy_snapshot BEFORE INSERT OR UPDATE OR DELETE ON release.visual_registry_delivery_policy_snapshot
  FOR EACH ROW EXECUTE FUNCTION release.guard_visual_projection_mutation();
CREATE TRIGGER guard_visual_registry_entry BEFORE INSERT OR UPDATE OR DELETE ON release.visual_registry_entry
  FOR EACH ROW EXECUTE FUNCTION release.guard_visual_projection_mutation();
CREATE TRIGGER guard_visual_attribution_value BEFORE INSERT OR UPDATE OR DELETE ON release.visual_registry_attribution_value
  FOR EACH ROW EXECUTE FUNCTION release.guard_visual_projection_mutation();
CREATE TRIGGER guard_visual_registry_public_locator BEFORE INSERT OR UPDATE OR DELETE ON release.visual_registry_public_locator
  FOR EACH ROW EXECUTE FUNCTION release.guard_visual_projection_mutation();
CREATE TRIGGER guard_visual_registry_takedown_snapshot BEFORE INSERT OR UPDATE OR DELETE ON release.visual_registry_takedown_snapshot
  FOR EACH ROW EXECUTE FUNCTION release.guard_visual_projection_mutation();

CREATE FUNCTION release.enforce_visual_registry_entry_source()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_delivery rights.delivery_assessment%ROWTYPE;
  v_bridge rights.object_visual_reference%ROWTYPE;
  v_reference rights.external_visual_reference%ROWTYPE;
  v_provider_code text;
  v_object_urn core.canonical_urn;
  v_attribution_sha core.sha256_hex;
BEGIN
  SELECT * INTO v_delivery FROM rights.delivery_assessment d
  WHERE d.delivery_assessment_id = NEW.delivery_assessment_id;
  SELECT * INTO v_bridge FROM rights.object_visual_reference b
  WHERE b.object_visual_reference_id = NEW.object_visual_reference_id;
  SELECT * INTO v_reference FROM rights.external_visual_reference r
  WHERE r.external_visual_reference_id = NEW.external_visual_reference_id;
  SELECT o.object_urn INTO v_object_urn FROM core.archive_object o
  WHERE o.archive_object_id = NEW.archive_object_id;
  SELECT p.provider_code INTO v_provider_code
  FROM rights.provider_object po
  JOIN rights.provider p ON p.provider_id = po.provider_id
  WHERE po.provider_object_id = v_reference.provider_object_id;
  SELECT a.bundle_sha256 INTO v_attribution_sha
  FROM rights.attribution_bundle a
  WHERE a.attribution_bundle_id = v_delivery.attribution_bundle_id;

  IF v_delivery.object_visual_reference_id IS DISTINCT FROM NEW.object_visual_reference_id
    OR v_delivery.delivery_mode IS DISTINCT FROM NEW.base_delivery_mode
    OR v_delivery.reason_code IS DISTINCT FROM NEW.reason_code
    OR v_bridge.archive_object_id IS DISTINCT FROM NEW.archive_object_id
    OR v_bridge.external_visual_reference_id IS DISTINCT FROM NEW.external_visual_reference_id
    OR v_bridge.reference_role IS DISTINCT FROM NEW.reference_role
    OR v_bridge.acceptance_state <> 'accepted'
    OR v_object_urn IS DISTINCT FROM NEW.object_urn
    OR v_reference.visual_reference_urn IS DISTINCT FROM NEW.visual_reference_urn
    OR v_provider_code IS DISTINCT FROM NEW.provider_code
    OR v_attribution_sha IS DISTINCT FROM NEW.attribution_bundle_sha256
    OR rights.compute_delivery_rights_sha(NEW.delivery_assessment_id)
      IS DISTINCT FROM NEW.rights_outcome_sha256
    OR rights.compute_delivery_policy_sha(NEW.delivery_assessment_id)
      IS DISTINCT FROM NEW.policy_outcome_sha256 THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'VISUAL_ENTRY_COPIED_SOURCE_MISMATCH';
  END IF;
  RETURN NEW;
END
$function$;

CREATE TRIGGER enforce_visual_registry_entry_source
BEFORE INSERT OR UPDATE ON release.visual_registry_entry
FOR EACH ROW EXECUTE FUNCTION release.enforce_visual_registry_entry_source();

CREATE FUNCTION release.enforce_public_locator_mode()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_entry release.visual_registry_entry%ROWTYPE;
  v_locator rights.visual_locator%ROWTYPE;
  v_health rights.endpoint_health_observation%ROWTYPE;
BEGIN
  SELECT * INTO v_entry FROM release.visual_registry_entry e
  WHERE e.visual_registry_release_id = NEW.visual_registry_release_id
    AND e.visual_registry_entry_id = NEW.visual_registry_entry_id;
  SELECT * INTO v_locator FROM rights.visual_locator l
  WHERE l.visual_locator_id = NEW.visual_locator_id;
  SELECT * INTO v_health FROM rights.endpoint_health_observation h
  WHERE h.endpoint_health_observation_id = NEW.endpoint_health_observation_id;

  IF v_locator.external_visual_reference_id IS DISTINCT FROM v_entry.external_visual_reference_id
    OR v_locator.locator_role IS DISTINCT FROM NEW.locator_role
    OR v_locator.visibility <> 'public_candidate'
    OR v_locator.raw_locator IS DISTINCT FROM NEW.public_locator
    OR v_locator.locator_fingerprint IS DISTINCT FROM NEW.locator_sha256
    OR v_health.visual_locator_id IS DISTINCT FROM NEW.visual_locator_id
    OR v_health.health_state <> 'healthy_fresh'
    OR v_health.checked_at > clock_timestamp()
    OR v_health.valid_until IS NULL
    OR v_health.valid_until <= clock_timestamp()
    OR v_health.health_state IS DISTINCT FROM NEW.health_state
    OR v_health.checked_at IS DISTINCT FROM NEW.health_observed_at
    OR v_health.valid_until IS DISTINCT FROM NEW.health_valid_until
    OR rights.compute_health_observation_sha(NEW.endpoint_health_observation_id)
      IS DISTINCT FROM NEW.health_observation_sha256
    OR NOT EXISTS (
      SELECT 1 FROM rights.delivery_locator_qualification q
      WHERE q.delivery_assessment_id = v_entry.delivery_assessment_id
        AND q.visual_locator_id = NEW.visual_locator_id
        AND q.endpoint_health_observation_id = NEW.endpoint_health_observation_id
        AND q.allowlisted_role = NEW.locator_role
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'PUBLIC_LOCATOR_SOURCE_HEALTH_OR_QUALIFICATION_MISMATCH';
  END IF;
  IF (NEW.locator_role = 'direct_image' AND v_entry.base_delivery_mode <> 'remote_image')
    OR (NEW.locator_role = 'source_viewer' AND v_entry.base_delivery_mode <> 'source_viewer')
    OR (NEW.locator_role = 'canonical_record'
      AND v_entry.base_delivery_mode NOT IN ('link_only', 'source_viewer', 'remote_image')) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'PUBLIC_LOCATOR_NOT_ALLOWED_FOR_DELIVERY_MODE';
  END IF;
  RETURN NEW;
END
$function$;

CREATE TRIGGER enforce_public_locator_mode
BEFORE INSERT OR UPDATE ON release.visual_registry_public_locator
FOR EACH ROW EXECUTE FUNCTION release.enforce_public_locator_mode();

CREATE FUNCTION release.enforce_takedown_snapshot()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_entry release.visual_registry_entry%ROWTYPE;
  v_override rights.takedown_override%ROWTYPE;
  v_event rights.takedown_event%ROWTYPE;
BEGIN
  SELECT * INTO v_entry FROM release.visual_registry_entry e
  WHERE e.visual_registry_release_id = NEW.visual_registry_release_id
    AND e.visual_registry_entry_id = NEW.visual_registry_entry_id;
  SELECT * INTO v_override FROM rights.takedown_override o
  WHERE o.takedown_override_id = NEW.takedown_override_id;
  SELECT te.* INTO v_event
  FROM rights.takedown_scope s
  JOIN rights.takedown_event te ON te.takedown_event_id = s.takedown_event_id
  WHERE s.takedown_scope_id = v_override.takedown_scope_id;
  IF NOT rights.scope_matches_bridge(v_override.takedown_scope_id, v_entry.object_visual_reference_id)
    OR v_override.restrictive_mode IS DISTINCT FROM NEW.restrictive_mode
    OR v_override.overlay_sha256 IS DISTINCT FROM NEW.overlay_sha256
    OR v_event.effective_from IS DISTINCT FROM NEW.effective_from
    OR v_event.effective_until IS DISTINCT FROM NEW.effective_until THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'TAKEDOWN_SNAPSHOT_SCOPE_OR_COPY_MISMATCH';
  END IF;
  RETURN NEW;
END
$function$;

CREATE TRIGGER enforce_takedown_snapshot
BEFORE INSERT OR UPDATE ON release.visual_registry_takedown_snapshot
FOR EACH ROW EXECUTE FUNCTION release.enforce_takedown_snapshot();

CREATE FUNCTION release.guard_research_manifest()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE v_state release.release_state;
BEGIN
  IF TG_OP <> 'INSERT' THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RESEARCH_MANIFEST_IMMUTABLE';
  END IF;
  SELECT r.release_state INTO v_state FROM release.research_release r
  WHERE r.research_release_id = NEW.research_release_id FOR SHARE;
  IF v_state <> 'validated' THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RESEARCH_MANIFEST_REQUIRES_VALIDATED_RELEASE';
  END IF;
  RETURN NEW;
END
$function$;

CREATE TRIGGER guard_research_manifest BEFORE INSERT OR UPDATE OR DELETE ON release.research_release_manifest
  FOR EACH ROW EXECUTE FUNCTION release.guard_research_manifest();

CREATE FUNCTION release.guard_visual_manifest()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE v_state release.release_state;
BEGIN
  IF TG_OP <> 'INSERT' THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'VISUAL_MANIFEST_IMMUTABLE';
  END IF;
  SELECT r.release_state INTO v_state FROM release.visual_registry_release r
  WHERE r.visual_registry_release_id = NEW.visual_registry_release_id FOR SHARE;
  IF v_state <> 'validated' THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'VISUAL_MANIFEST_REQUIRES_VALIDATED_RELEASE';
  END IF;
  RETURN NEW;
END
$function$;

CREATE TRIGGER guard_visual_manifest BEFORE INSERT OR UPDATE OR DELETE ON release.visual_registry_manifest
  FOR EACH ROW EXECUTE FUNCTION release.guard_visual_manifest();

CREATE TRIGGER research_validation_receipt_append_only BEFORE UPDATE OR DELETE ON release.research_validation_receipt
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER visual_validation_receipt_append_only BEFORE UPDATE OR DELETE ON release.visual_validation_receipt
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER research_verification_append_only BEFORE UPDATE OR DELETE ON release.research_release_verification
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER visual_verification_append_only BEFORE UPDATE OR DELETE ON release.visual_registry_verification
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER visual_health_sidecar_append_only BEFORE UPDATE OR DELETE ON release.visual_health_sidecar_event
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER visual_takedown_sidecar_append_only BEFORE UPDATE OR DELETE ON release.visual_takedown_sidecar_event
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER research_publication_history_append_only BEFORE UPDATE OR DELETE ON release.research_publication_history
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER visual_publication_history_append_only BEFORE UPDATE OR DELETE ON release.visual_publication_history
  FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();

RESET ROLE;
