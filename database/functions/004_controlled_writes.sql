\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

CREATE FUNCTION raw.require_ingest_writer()
RETURNS void LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
BEGIN
  IF session_user::text <> 'gda_v49_phase2a_ingest_writer' THEN
    RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'INGEST_WRITER_REQUIRED';
  END IF;
END
$function$;

CREATE FUNCTION rights.require_reviewer()
RETURNS void LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
BEGIN
  IF session_user::text <> 'gda_v49_phase2a_reviewer' THEN
    RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'REVIEWER_REQUIRED';
  END IF;
END
$function$;

CREATE FUNCTION audit.record_decision_event(
  p_kind audit.decision_kind, p_target_id uuid
)
RETURNS uuid
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_event_id uuid := gen_random_uuid();
  v_occurred_at timestamptz := clock_timestamp();
  v_sha256 core.sha256_hex;
BEGIN
  v_sha256 := release.canonical_jsonb_sha256(jsonb_build_object(
    'decisionEventId', v_event_id,
    'kind', p_kind,
    'targetId', p_target_id,
    'actor', session_user::text,
    'occurredAtUs',
      (extract(epoch FROM v_occurred_at) * 1000000)::bigint
  ));
  INSERT INTO audit.decision_event VALUES (
    v_event_id, p_kind, session_user::text, v_occurred_at, v_sha256);
  CASE p_kind
    WHEN 'assertion_review' THEN
      INSERT INTO audit.decision_event_assertion_review VALUES (v_event_id, p_target_id);
    WHEN 'assignment_review' THEN
      INSERT INTO audit.decision_event_assignment_review VALUES (v_event_id, p_target_id);
    WHEN 'claim_review' THEN
      INSERT INTO audit.decision_event_claim_review VALUES (v_event_id, p_target_id);
    WHEN 'relation_review' THEN
      INSERT INTO audit.decision_event_relation_review VALUES (v_event_id, p_target_id);
    WHEN 'rights_observation' THEN
      INSERT INTO audit.decision_event_rights_observation VALUES (v_event_id, p_target_id);
    WHEN 'rights_assessment' THEN
      INSERT INTO audit.decision_event_rights_assessment VALUES (v_event_id, p_target_id);
    WHEN 'provider_policy_evaluation' THEN
      INSERT INTO audit.decision_event_policy_evaluation VALUES (v_event_id, p_target_id);
    WHEN 'delivery_assessment' THEN
      INSERT INTO audit.decision_event_delivery_assessment VALUES (v_event_id, p_target_id);
    WHEN 'attribution_validation' THEN
      INSERT INTO audit.decision_event_attribution_validation VALUES (v_event_id, p_target_id);
    WHEN 'takedown' THEN
      INSERT INTO audit.decision_event_takedown VALUES (v_event_id, p_target_id);
    WHEN 'visual_bridge_review' THEN
      INSERT INTO audit.decision_event_visual_bridge_review
        VALUES (v_event_id, p_target_id);
  END CASE;
  RETURN v_event_id;
END
$function$;

CREATE FUNCTION raw.register_source_asset(
  p_source_asset_id uuid, p_authority raw.asset_authority,
  p_logical_name text, p_sha256 core.sha256_hex,
  p_raw_bytes bytea, p_media_type text, p_received_at timestamptz
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM raw.require_ingest_writer();
  IF p_authority <> 'governed_source' THEN
    RAISE EXCEPTION USING ERRCODE = '42501',
      MESSAGE = 'RUNTIME_INGESTOR_CANNOT_DECLARE_FROZEN_ASSET_AUTHORITY';
  END IF;
  INSERT INTO raw.source_asset (
    source_asset_id, authority, logical_name, sha256, byte_length,
    raw_bytes, media_type, received_at
  ) VALUES (
    p_source_asset_id, p_authority, p_logical_name, p_sha256,
    octet_length(p_raw_bytes), p_raw_bytes, p_media_type, p_received_at
  );
END
$function$;

CREATE FUNCTION raw.register_source_record(
  p_source_record_id uuid, p_source_asset_id uuid, p_record_ordinal bigint,
  p_legacy_source_record_id text, p_raw_value bytea,
  p_raw_fingerprint core.sha256_hex, p_parsed_projection jsonb,
  p_parse_error_code text
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM raw.require_ingest_writer();
  PERFORM 1 FROM raw.source_asset a
  WHERE a.source_asset_id = p_source_asset_id
    AND a.authority = 'governed_source'
  FOR SHARE;
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '42501',
      MESSAGE = 'RUNTIME_SOURCE_RECORD_REQUIRES_GOVERNED_SOURCE_PARENT';
  END IF;
  INSERT INTO raw.source_record (
    source_record_id, source_asset_id, record_ordinal,
    legacy_source_record_id, raw_value, raw_fingerprint,
    parsed_projection, parse_error_code
  ) VALUES (
    p_source_record_id, p_source_asset_id, p_record_ordinal,
    p_legacy_source_record_id, p_raw_value, p_raw_fingerprint,
    p_parsed_projection, p_parse_error_code
  );
END
$function$;

CREATE FUNCTION raw.register_field_literal(
  p_field_literal_id uuid, p_source_record_id uuid,
  p_json_pointer text, p_occurrence_ordinal integer,
  p_raw_text text, p_raw_bytes bytea,
  p_byte_start bigint, p_byte_end bigint
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM raw.require_ingest_writer();
  PERFORM 1
  FROM raw.source_record r
  JOIN raw.source_asset a ON a.source_asset_id = r.source_asset_id
  WHERE r.source_record_id = p_source_record_id
    AND a.authority = 'governed_source'
  FOR SHARE OF r, a;
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '42501',
      MESSAGE = 'RUNTIME_FIELD_LITERAL_REQUIRES_GOVERNED_SOURCE_PARENT';
  END IF;
  INSERT INTO raw.field_literal VALUES (
    p_field_literal_id, p_source_record_id, p_json_pointer,
    p_occurrence_ordinal, p_raw_text, p_raw_bytes,
    p_byte_start, p_byte_end);
END
$function$;

CREATE FUNCTION provenance.record_proposed_literal_assertion(
  p_assertion_id uuid, p_predicate_id uuid,
  p_subject_entity_id uuid, p_field_literal_id uuid,
  p_normalized_text text, p_language_tag text, p_datatype_uri text,
  p_claimant_agent_id uuid, p_source_wording text,
  p_evidence_item_ids uuid[], p_evidence_roles provenance.evidence_role[],
  p_review_case_id uuid, p_reason_code text
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE v_index integer;
BEGIN
  PERFORM raw.require_ingest_writer();
  IF cardinality(p_evidence_item_ids) IS DISTINCT FROM cardinality(p_evidence_roles) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'PROPOSED_ASSERTION_EVIDENCE_SET_INVALID';
  END IF;
  INSERT INTO provenance.assertion (
    assertion_id, assertion_predicate_id, subject_kind, value_kind,
    status, claimant_agent_id, source_wording, supersedes_assertion_id,
    created_at
  ) VALUES (
    p_assertion_id, p_predicate_id, 'entity', 'literal', 'proposed',
    p_claimant_agent_id, p_source_wording, NULL, clock_timestamp());
  INSERT INTO provenance.assertion_subject_entity VALUES (
    p_assertion_id, p_subject_entity_id);
  INSERT INTO provenance.assertion_value_literal VALUES (
    p_assertion_id, p_field_literal_id, p_normalized_text,
    p_language_tag, p_datatype_uri);
  IF COALESCE(cardinality(p_evidence_item_ids), 0) > 0 THEN
    FOR v_index IN 1..cardinality(p_evidence_item_ids) LOOP
      INSERT INTO provenance.assertion_evidence VALUES (
        p_assertion_id, p_evidence_item_ids[v_index], p_evidence_roles[v_index]);
    END LOOP;
  END IF;
  INSERT INTO workflow.review_case (
    review_case_id, case_kind, queue_state, priority, reason_code,
    claimed_by, claimed_at, created_at, resolved_at
  ) VALUES (
    p_review_case_id, 'assertion', 'queued', 0, p_reason_code,
    NULL, NULL, clock_timestamp(), NULL);
  INSERT INTO workflow.review_case_assertion VALUES (
    p_review_case_id, p_assertion_id);
END
$function$;

CREATE FUNCTION provenance.record_proposed_entity_name_assignment(
  p_assignment_id uuid, p_entity_id uuid, p_field_literal_id uuid,
  p_assertion_ids uuid[], p_support_roles provenance.evidence_role[],
  p_review_case_id uuid, p_reason_code text
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE v_index integer;
BEGIN
  PERFORM raw.require_ingest_writer();
  IF cardinality(p_assertion_ids) IS DISTINCT FROM cardinality(p_support_roles) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'PROPOSED_ASSIGNMENT_ASSERTION_SET_INVALID';
  END IF;
  INSERT INTO provenance.canonical_assignment VALUES (
    p_assignment_id, 'entity_name', 'proposed', NULL, clock_timestamp());
  INSERT INTO provenance.assignment_entity_name VALUES (
    p_assignment_id, p_entity_id, p_field_literal_id);
  IF COALESCE(cardinality(p_assertion_ids), 0) > 0 THEN
    FOR v_index IN 1..cardinality(p_assertion_ids) LOOP
      INSERT INTO provenance.assignment_assertion VALUES (
        p_assignment_id, p_assertion_ids[v_index], p_support_roles[v_index]);
    END LOOP;
  END IF;
  INSERT INTO workflow.review_case (
    review_case_id, case_kind, queue_state, priority, reason_code,
    claimed_by, claimed_at, created_at, resolved_at
  ) VALUES (
    p_review_case_id, 'canonical_assignment', 'queued', 0,
    p_reason_code, NULL, NULL, clock_timestamp(), NULL);
  INSERT INTO workflow.review_case_assignment VALUES (
    p_review_case_id, p_assignment_id);
END
$function$;

CREATE FUNCTION workflow.claim_review_case(p_review_case_id uuid)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM rights.require_reviewer();
  UPDATE workflow.review_case
  SET queue_state = 'claimed', claimed_by = session_user::text,
    claimed_at = clock_timestamp()
  WHERE review_case_id = p_review_case_id AND queue_state = 'queued';
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '55000',
      MESSAGE = 'REVIEW_CASE_NOT_CLAIMABLE';
  END IF;
END
$function$;

CREATE FUNCTION provenance.record_assertion_review_decision(
  p_decision_id uuid, p_assertion_id uuid,
  p_outcome workflow.review_outcome, p_rationale text,
  p_supersedes_decision_id uuid,
  p_evidence_item_ids uuid[], p_evidence_roles provenance.evidence_role[]
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE v_index integer;
BEGIN
  PERFORM rights.require_reviewer();
  IF COALESCE(cardinality(p_evidence_item_ids), 0) = 0
    OR cardinality(p_evidence_item_ids) IS DISTINCT FROM cardinality(p_evidence_roles) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'ASSERTION_REVIEW_EVIDENCE_SET_INVALID';
  END IF;
  IF p_supersedes_decision_id IS NULL THEN
    PERFORM 1
    FROM workflow.review_case c
    JOIN workflow.review_case_assertion x USING (review_case_id)
    WHERE x.assertion_id = p_assertion_id
      AND c.queue_state IN ('claimed', 'in_review')
      AND c.claimed_by = session_user::text
    FOR UPDATE OF c;
    IF NOT FOUND THEN
      RAISE EXCEPTION USING ERRCODE = '55000',
        MESSAGE = 'ASSERTION_REVIEW_CASE_NOT_CLAIMED';
    END IF;
  ELSIF NOT EXISTS (
    SELECT 1 FROM provenance.assertion_review_decision prior
    WHERE prior.assertion_review_decision_id = p_supersedes_decision_id
      AND prior.assertion_id = p_assertion_id
      AND NOT EXISTS (
        SELECT 1 FROM provenance.assertion_review_decision newer
        WHERE newer.supersedes_decision_id = prior.assertion_review_decision_id)
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '55000',
      MESSAGE = 'ASSERTION_REVIEW_SUPERSEDES_NONCURRENT_DECISION';
  END IF;
  INSERT INTO provenance.assertion_review_decision VALUES (
    p_decision_id, p_assertion_id, p_outcome, session_user::text,
    p_rationale, p_supersedes_decision_id, clock_timestamp());
  FOR v_index IN 1..cardinality(p_evidence_item_ids) LOOP
    INSERT INTO provenance.assertion_decision_evidence VALUES (
      p_decision_id, p_evidence_item_ids[v_index], p_evidence_roles[v_index]);
  END LOOP;
  UPDATE provenance.assertion
  SET status = CASE p_outcome
      WHEN 'accept' THEN 'accepted'::provenance.assertion_status
      WHEN 'reject' THEN 'rejected'::provenance.assertion_status
      WHEN 'supersede' THEN 'superseded'::provenance.assertion_status
      ELSE 'proposed'::provenance.assertion_status END
  WHERE assertion_id = p_assertion_id
    AND ((p_supersedes_decision_id IS NULL AND status = 'proposed')
      OR (p_supersedes_decision_id IS NOT NULL AND status <> 'superseded'));
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'ASSERTION_NOT_REVIEWABLE';
  END IF;
  UPDATE workflow.review_case c
  SET queue_state = 'resolved', claimed_by = NULL, claimed_at = NULL,
    resolved_at = clock_timestamp()
  FROM workflow.review_case_assertion x
  WHERE x.review_case_id = c.review_case_id
    AND x.assertion_id = p_assertion_id;
  PERFORM audit.record_decision_event('assertion_review', p_decision_id);
END
$function$;

CREATE FUNCTION provenance.record_assignment_review_decision(
  p_decision_id uuid, p_assignment_id uuid,
  p_outcome workflow.review_outcome, p_rationale text,
  p_supersedes_decision_id uuid,
  p_evidence_item_ids uuid[], p_evidence_roles provenance.evidence_role[]
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE v_index integer;
BEGIN
  PERFORM rights.require_reviewer();
  IF COALESCE(cardinality(p_evidence_item_ids), 0) = 0
    OR cardinality(p_evidence_item_ids) IS DISTINCT FROM cardinality(p_evidence_roles) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'ASSIGNMENT_REVIEW_EVIDENCE_SET_INVALID';
  END IF;
  IF p_supersedes_decision_id IS NULL THEN
    PERFORM 1
    FROM workflow.review_case c
    JOIN workflow.review_case_assignment x USING (review_case_id)
    WHERE x.canonical_assignment_id = p_assignment_id
      AND c.queue_state IN ('claimed', 'in_review')
      AND c.claimed_by = session_user::text
    FOR UPDATE OF c;
    IF NOT FOUND THEN
      RAISE EXCEPTION USING ERRCODE = '55000',
        MESSAGE = 'ASSIGNMENT_REVIEW_CASE_NOT_CLAIMED';
    END IF;
  ELSIF NOT EXISTS (
    SELECT 1 FROM provenance.assignment_review_decision prior
    WHERE prior.assignment_review_decision_id = p_supersedes_decision_id
      AND prior.canonical_assignment_id = p_assignment_id
      AND NOT EXISTS (
        SELECT 1 FROM provenance.assignment_review_decision newer
        WHERE newer.supersedes_decision_id = prior.assignment_review_decision_id)
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '55000',
      MESSAGE = 'ASSIGNMENT_REVIEW_SUPERSEDES_NONCURRENT_DECISION';
  END IF;
  INSERT INTO provenance.assignment_review_decision VALUES (
    p_decision_id, p_assignment_id, p_outcome, session_user::text,
    p_rationale, p_supersedes_decision_id, clock_timestamp());
  FOR v_index IN 1..cardinality(p_evidence_item_ids) LOOP
    INSERT INTO provenance.assignment_decision_evidence VALUES (
      p_decision_id, p_evidence_item_ids[v_index], p_evidence_roles[v_index]);
  END LOOP;
  UPDATE provenance.canonical_assignment
  SET status = CASE p_outcome
      WHEN 'accept' THEN 'accepted'::provenance.assertion_status
      WHEN 'reject' THEN 'rejected'::provenance.assertion_status
      WHEN 'supersede' THEN 'superseded'::provenance.assertion_status
      ELSE 'proposed'::provenance.assertion_status END
  WHERE canonical_assignment_id = p_assignment_id
    AND ((p_supersedes_decision_id IS NULL AND status = 'proposed')
      OR (p_supersedes_decision_id IS NOT NULL AND status <> 'superseded'));
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'ASSIGNMENT_NOT_REVIEWABLE';
  END IF;
  UPDATE workflow.review_case c
  SET queue_state = 'resolved', claimed_by = NULL, claimed_at = NULL,
    resolved_at = clock_timestamp()
  FROM workflow.review_case_assignment x
  WHERE x.review_case_id = c.review_case_id
    AND x.canonical_assignment_id = p_assignment_id;
  PERFORM audit.record_decision_event('assignment_review', p_decision_id);
END
$function$;

CREATE FUNCTION rights.record_endpoint_health_observation(
  p_observation_id uuid, p_locator_id uuid,
  p_health_state rights.health_state, p_method_version core.release_token,
  p_checked_at timestamptz,
  p_valid_until timestamptz, p_request_fingerprint core.sha256_hex
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM raw.require_ingest_writer();
  PERFORM pg_advisory_xact_lock(hashtext('gda_v49_visual_seal_takedown'));
  IF p_checked_at > clock_timestamp() THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'FUTURE_ENDPOINT_HEALTH_OBSERVATION_DENIED';
  END IF;
  INSERT INTO rights.endpoint_health_observation (
    endpoint_health_observation_id, visual_locator_id, health_state,
    method_version,
    checked_at, valid_until, request_fingerprint
  ) VALUES (
    p_observation_id, p_locator_id, p_health_state,
    p_method_version,
    p_checked_at, p_valid_until, p_request_fingerprint
  );
END
$function$;

CREATE FUNCTION research.record_relation_review_decision(
  p_decision_id uuid, p_relation_id uuid, p_outcome workflow.review_outcome,
  p_rationale text, p_supersedes_decision_id uuid,
  p_evidence_item_ids uuid[], p_evidence_roles provenance.evidence_role[],
  p_audit_event_id uuid, p_audit_event_sha256 core.sha256_hex
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE
  v_index integer;
BEGIN
  PERFORM rights.require_reviewer();
  IF COALESCE(cardinality(p_evidence_item_ids), 0) = 0
    OR cardinality(p_evidence_item_ids) IS DISTINCT FROM cardinality(p_evidence_roles) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'RELATION_REVIEW_EVIDENCE_SET_INVALID';
  END IF;
  IF p_supersedes_decision_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM research.relation_review_decision prior
    WHERE prior.relation_review_decision_id = p_supersedes_decision_id
      AND prior.semantic_relation_id = p_relation_id
      AND NOT EXISTS (
        SELECT 1 FROM research.relation_review_decision newer
        WHERE newer.supersedes_decision_id = prior.relation_review_decision_id)
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '55000',
      MESSAGE = 'RELATION_REVIEW_SUPERSEDES_NONCURRENT_DECISION';
  END IF;
  INSERT INTO research.relation_review_decision (
    relation_review_decision_id, semantic_relation_id, outcome,
    reviewer_actor, reviewer_agent_id, rationale, supersedes_decision_id, decided_at
  ) VALUES (
    p_decision_id, p_relation_id, p_outcome, session_user::text,
    NULL, p_rationale, p_supersedes_decision_id, clock_timestamp()
  );
  FOR v_index IN 1..cardinality(p_evidence_item_ids) LOOP
    INSERT INTO research.relation_decision_evidence VALUES (
      p_decision_id, p_evidence_item_ids[v_index], p_evidence_roles[v_index]);
  END LOOP;
  UPDATE research.semantic_relation
  SET status = CASE p_outcome
      WHEN 'accept' THEN 'accepted'::research.relation_status
      WHEN 'reject' THEN 'rejected'::research.relation_status
      WHEN 'supersede' THEN 'superseded'::research.relation_status
      ELSE 'proposed'::research.relation_status END
  WHERE semantic_relation_id = p_relation_id
    AND ((p_supersedes_decision_id IS NULL AND status = 'proposed')
      OR (p_supersedes_decision_id IS NOT NULL AND status <> 'superseded'));
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '55000',
      MESSAGE = 'SEMANTIC_RELATION_NOT_REVIEWABLE';
  END IF;
  INSERT INTO audit.review_event VALUES (
    p_audit_event_id, p_decision_id, session_user::text,
    clock_timestamp(), p_audit_event_sha256
  );
  PERFORM audit.record_decision_event('relation_review', p_decision_id);
END
$function$;

CREATE FUNCTION research.attach_relation_decision_evidence(
  p_decision_id uuid, p_evidence_item_id uuid,
  p_role provenance.evidence_role
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM rights.require_reviewer();
  INSERT INTO research.relation_decision_evidence VALUES (
    p_decision_id, p_evidence_item_id, p_role);
END
$function$;

CREATE FUNCTION research.record_claim_review_decision(
  p_decision_id uuid, p_claim_revision_id uuid,
  p_outcome workflow.review_outcome, p_heightened_review boolean,
  p_rationale text, p_supersedes_decision_id uuid,
  p_evidence_item_ids uuid[], p_evidence_roles provenance.evidence_role[]
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE
  v_index integer;
BEGIN
  PERFORM rights.require_reviewer();
  IF COALESCE(cardinality(p_evidence_item_ids), 0) = 0
    OR cardinality(p_evidence_item_ids) IS DISTINCT FROM cardinality(p_evidence_roles) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'CLAIM_REVIEW_EVIDENCE_SET_INVALID';
  END IF;
  IF p_supersedes_decision_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM research.claim_review_decision prior
    WHERE prior.claim_review_decision_id = p_supersedes_decision_id
      AND prior.claim_revision_id = p_claim_revision_id
      AND NOT EXISTS (
        SELECT 1 FROM research.claim_review_decision newer
        WHERE newer.supersedes_decision_id = prior.claim_review_decision_id)
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '55000',
      MESSAGE = 'CLAIM_REVIEW_SUPERSEDES_NONCURRENT_DECISION';
  END IF;
  INSERT INTO research.claim_review_decision (
    claim_review_decision_id, claim_revision_id, outcome,
    heightened_review, reviewer_actor, rationale,
    supersedes_decision_id, decided_at
  ) VALUES (
    p_decision_id, p_claim_revision_id, p_outcome,
    p_heightened_review, session_user::text, p_rationale,
    p_supersedes_decision_id, clock_timestamp()
  );
  FOR v_index IN 1..cardinality(p_evidence_item_ids) LOOP
    INSERT INTO research.claim_decision_evidence VALUES (
      p_decision_id, p_evidence_item_ids[v_index], p_evidence_roles[v_index]);
  END LOOP;
  UPDATE research.claim_revision
  SET status = CASE p_outcome
      WHEN 'accept' THEN 'accepted'::research.claim_status
      WHEN 'reject' THEN 'rejected'::research.claim_status
      WHEN 'supersede' THEN 'superseded'::research.claim_status
      ELSE 'proposed'::research.claim_status END,
    workflow_state = 'resolved'
  WHERE claim_revision_id = p_claim_revision_id
    AND ((p_supersedes_decision_id IS NULL AND status IN ('draft', 'proposed'))
      OR (p_supersedes_decision_id IS NOT NULL AND status <> 'superseded'));
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '55000',
      MESSAGE = 'CLAIM_REVISION_NOT_REVIEWABLE';
  END IF;
  PERFORM audit.record_decision_event('claim_review', p_decision_id);
END
$function$;

CREATE FUNCTION rights.record_rights_observation(
  p_observation_id uuid, p_subject_kind rights.rights_subject_kind,
  p_subject_id uuid, p_evidence_state rights.rights_evidence_state,
  p_evidence_item_id uuid, p_wording text, p_observed_at timestamptz,
  p_supersedes_id uuid
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM rights.require_reviewer();
  PERFORM pg_advisory_xact_lock(hashtext('gda_v49_visual_seal_takedown'));
  IF p_observed_at > clock_timestamp() THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'FUTURE_RIGHTS_OBSERVATION_DENIED';
  END IF;
  INSERT INTO rights.rights_observation (
    rights_observation_id, subject_kind, evidence_state, evidence_item_id,
    observed_wording, observed_at, supersedes_rights_observation_id
  ) VALUES (
    p_observation_id, p_subject_kind, p_evidence_state, p_evidence_item_id,
    p_wording, p_observed_at, p_supersedes_id
  );
  CASE p_subject_kind
    WHEN 'provider_object' THEN
      INSERT INTO rights.rights_observation_provider_object VALUES (p_observation_id, p_subject_id);
    WHEN 'external_visual_reference' THEN
      INSERT INTO rights.rights_observation_visual_reference VALUES (p_observation_id, p_subject_id);
    WHEN 'digital_representation' THEN
      INSERT INTO rights.rights_observation_representation VALUES (p_observation_id, p_subject_id);
    WHEN 'visual_locator' THEN
      INSERT INTO rights.rights_observation_locator VALUES (p_observation_id, p_subject_id);
  END CASE;
  PERFORM audit.record_decision_event('rights_observation', p_observation_id);
END
$function$;

CREATE FUNCTION rights.record_rights_assessment(
  p_assessment_id uuid, p_subject_kind rights.rights_subject_kind,
  p_subject_id uuid, p_assessed_state rights.rights_evidence_state,
  p_rationale text, p_assessed_at timestamptz, p_supersedes_id uuid,
  p_observation_ids uuid[], p_evidence_roles provenance.evidence_role[]
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE
  v_index integer;
BEGIN
  PERFORM rights.require_reviewer();
  PERFORM pg_advisory_xact_lock(hashtext('gda_v49_visual_seal_takedown'));
  IF p_assessed_at > clock_timestamp() THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'FUTURE_RIGHTS_ASSESSMENT_DENIED';
  END IF;
  INSERT INTO rights.rights_assessment (
    rights_assessment_id, subject_kind, assessed_state, reviewer_actor,
    rationale, assessed_at, supersedes_rights_assessment_id
  ) VALUES (
    p_assessment_id, p_subject_kind, p_assessed_state, session_user::text,
    p_rationale, p_assessed_at, p_supersedes_id
  );
  CASE p_subject_kind
    WHEN 'provider_object' THEN
      INSERT INTO rights.rights_assessment_provider_object VALUES (p_assessment_id, p_subject_id);
    WHEN 'external_visual_reference' THEN
      INSERT INTO rights.rights_assessment_visual_reference VALUES (p_assessment_id, p_subject_id);
    WHEN 'digital_representation' THEN
      INSERT INTO rights.rights_assessment_representation VALUES (p_assessment_id, p_subject_id);
    WHEN 'visual_locator' THEN
      INSERT INTO rights.rights_assessment_locator VALUES (p_assessment_id, p_subject_id);
  END CASE;
  IF COALESCE(cardinality(p_observation_ids), 0) = 0
    OR cardinality(p_observation_ids) IS DISTINCT FROM cardinality(p_evidence_roles) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'RIGHTS_ASSESSMENT_OBSERVATION_SET_INVALID';
  END IF;
  FOR v_index IN 1..cardinality(p_observation_ids) LOOP
    INSERT INTO rights.rights_assessment_observation VALUES (
      p_assessment_id, p_observation_ids[v_index], p_evidence_roles[v_index]);
  END LOOP;
  PERFORM audit.record_decision_event('rights_assessment', p_assessment_id);
END
$function$;

CREATE FUNCTION rights.record_provider_policy_evaluation(
  p_evaluation_id uuid, p_bridge_id uuid, p_state rights.policy_state,
  p_policy_version_ids uuid[], p_evaluated_at timestamptz,
  p_supersedes_id uuid
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE v_policy_id uuid;
BEGIN
  PERFORM rights.require_reviewer();
  PERFORM pg_advisory_xact_lock(hashtext('gda_v49_visual_seal_takedown'));
  IF p_evaluated_at > clock_timestamp() THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'FUTURE_PROVIDER_POLICY_EVALUATION_DENIED';
  END IF;
  INSERT INTO rights.provider_policy_evaluation (
    provider_policy_evaluation_id, object_visual_reference_id,
    evaluated_state, evaluator_actor, evaluated_at,
    supersedes_provider_policy_evaluation_id
  ) VALUES (
    p_evaluation_id, p_bridge_id, p_state, session_user::text,
    p_evaluated_at, p_supersedes_id
  );
  FOREACH v_policy_id IN ARRAY COALESCE(p_policy_version_ids, ARRAY[]::uuid[]) LOOP
    INSERT INTO rights.provider_policy_evaluation_version VALUES (
      p_evaluation_id, v_policy_id);
  END LOOP;
  PERFORM audit.record_decision_event(
    'provider_policy_evaluation', p_evaluation_id);
END
$function$;

CREATE FUNCTION rights.record_attribution_bundle(
  p_bundle_id uuid, p_bridge_id uuid,
  p_state rights.attribution_state, p_evidence_item_id uuid,
  p_validated_at timestamptz, p_supersedes_bundle_id uuid,
  p_value_kinds text[], p_value_ordinals integer[],
  p_language_tags text[], p_value_texts text[]
)
RETURNS core.sha256_hex
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE
  v_index integer;
  v_values jsonb;
  v_sha256 core.sha256_hex;
BEGIN
  PERFORM rights.require_reviewer();
  PERFORM pg_advisory_xact_lock(hashtext('gda_v49_visual_seal_takedown'));
  IF p_validated_at > clock_timestamp()
    OR cardinality(p_value_kinds) IS DISTINCT FROM cardinality(p_value_ordinals)
    OR cardinality(p_value_kinds) IS DISTINCT FROM cardinality(p_language_tags)
    OR cardinality(p_value_kinds) IS DISTINCT FROM cardinality(p_value_texts)
    OR (p_state = 'complete' AND (
      p_evidence_item_id IS NULL OR COALESCE(cardinality(p_value_kinds), 0) = 0)) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'ATTRIBUTION_BUNDLE_INPUT_INVALID';
  END IF;
  SELECT COALESCE(jsonb_agg(jsonb_build_array(
      p_value_kinds[i], p_value_ordinals[i],
      p_language_tags[i], p_value_texts[i]
    ) ORDER BY p_value_kinds[i], p_value_ordinals[i]), '[]'::jsonb)
  INTO v_values
  FROM generate_subscripts(COALESCE(p_value_kinds, ARRAY[]::text[]), 1) AS g(i);
  v_sha256 := release.canonical_jsonb_sha256(jsonb_build_object(
    'bundleId', p_bundle_id,
    'bridgeId', p_bridge_id,
    'state', p_state,
    'evidenceId', p_evidence_item_id,
    'validatedBy', session_user::text,
    'validatedAtUs', (extract(epoch FROM p_validated_at) * 1000000)::bigint,
    'supersedesBundleId', p_supersedes_bundle_id,
    'values', v_values
  ));
  INSERT INTO rights.attribution_bundle VALUES (
    p_bundle_id, p_bridge_id, p_state, v_sha256, p_evidence_item_id,
    session_user::text, p_validated_at, p_supersedes_bundle_id);
  IF COALESCE(cardinality(p_value_kinds), 0) > 0 THEN
    FOR v_index IN 1..cardinality(p_value_kinds) LOOP
      INSERT INTO rights.attribution_bundle_value VALUES (
        p_bundle_id, p_value_kinds[v_index], p_value_ordinals[v_index],
        p_language_tags[v_index], p_value_texts[v_index]);
    END LOOP;
  END IF;
  PERFORM audit.record_decision_event('attribution_validation', p_bundle_id);
  RETURN v_sha256;
END
$function$;

CREATE FUNCTION rights.record_delivery_assessment(
  p_delivery_id uuid, p_bridge_id uuid,
  p_rights_assessment_ids uuid[],
  p_rights_evidence_roles provenance.evidence_role[],
  p_policy_evaluation_ids uuid[], p_attribution_bundle_id uuid,
  p_mode rights.delivery_mode, p_reason_code text, p_assessed_at timestamptz,
  p_supersedes_id uuid, p_locator_ids uuid[],
  p_health_observation_ids uuid[], p_locator_roles rights.locator_role[]
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE
  v_index integer;
BEGIN
  PERFORM rights.require_reviewer();
  PERFORM pg_advisory_xact_lock(hashtext('gda_v49_visual_seal_takedown'));
  IF p_assessed_at > clock_timestamp() THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'FUTURE_DELIVERY_ASSESSMENT_DENIED';
  END IF;
  INSERT INTO rights.delivery_assessment (
    delivery_assessment_id, object_visual_reference_id,
    attribution_bundle_id, delivery_mode, reason_code, assessor_actor,
    assessed_at, supersedes_delivery_assessment_id
  ) VALUES (
    p_delivery_id, p_bridge_id, p_attribution_bundle_id, p_mode,
    p_reason_code, session_user::text, p_assessed_at, p_supersedes_id
  );
  IF COALESCE(cardinality(p_rights_assessment_ids), 0) = 0
    OR cardinality(p_rights_assessment_ids)
      IS DISTINCT FROM cardinality(p_rights_evidence_roles)
    OR COALESCE(cardinality(p_policy_evaluation_ids), 0) = 0
    OR cardinality(p_locator_ids) IS DISTINCT FROM
      cardinality(p_health_observation_ids)
    OR cardinality(p_locator_ids) IS DISTINCT FROM cardinality(p_locator_roles) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'DELIVERY_GOVERNING_SET_CARDINALITY_INVALID';
  END IF;
  FOR v_index IN 1..cardinality(p_rights_assessment_ids) LOOP
    INSERT INTO rights.delivery_rights_assessment VALUES (
      p_delivery_id, p_rights_assessment_ids[v_index],
      p_rights_evidence_roles[v_index]);
  END LOOP;
  FOR v_index IN 1..cardinality(p_policy_evaluation_ids) LOOP
    INSERT INTO rights.delivery_policy_evaluation VALUES (
      p_delivery_id, p_policy_evaluation_ids[v_index]);
  END LOOP;
  IF COALESCE(cardinality(p_locator_ids), 0) > 0 THEN
    FOR v_index IN 1..cardinality(p_locator_ids) LOOP
      IF num_nonnulls(p_locator_ids[v_index], p_health_observation_ids[v_index],
          p_locator_roles[v_index]) <> 3 THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
          MESSAGE = 'DELIVERY_LOCATOR_QUALIFICATION_MUST_BE_COMPLETE';
      END IF;
      INSERT INTO rights.delivery_locator_qualification VALUES (
        p_delivery_id, p_locator_ids[v_index],
        p_health_observation_ids[v_index], p_locator_roles[v_index]);
    END LOOP;
  END IF;
  PERFORM audit.record_decision_event('delivery_assessment', p_delivery_id);
END
$function$;

CREATE FUNCTION rights.insert_takedown_scope(
  p_event_id uuid, p_scope_id uuid, p_scope_kind rights.takedown_scope_kind,
  p_subject_id uuid, p_override_id uuid,
  p_restrictive_mode rights.delivery_mode,
  p_supersedes_override_id uuid
)
RETURNS core.sha256_hex LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
DECLARE
  v_created_at timestamptz := clock_timestamp();
  v_overlay_sha256 core.sha256_hex;
  v_event rights.takedown_event%ROWTYPE;
BEGIN
  INSERT INTO rights.takedown_scope VALUES (p_scope_id, p_event_id, p_scope_kind);
  CASE p_scope_kind
    WHEN 'provider' THEN INSERT INTO rights.takedown_scope_provider VALUES (p_scope_id, p_subject_id);
    WHEN 'provider_object' THEN INSERT INTO rights.takedown_scope_provider_object VALUES (p_scope_id, p_subject_id);
    WHEN 'external_visual_reference' THEN INSERT INTO rights.takedown_scope_visual_reference VALUES (p_scope_id, p_subject_id);
    WHEN 'digital_representation' THEN INSERT INTO rights.takedown_scope_representation VALUES (p_scope_id, p_subject_id);
    WHEN 'visual_locator' THEN INSERT INTO rights.takedown_scope_locator VALUES (p_scope_id, p_subject_id);
    WHEN 'object_visual_reference' THEN INSERT INTO rights.takedown_scope_object_visual_reference VALUES (p_scope_id, p_subject_id);
  END CASE;
  SELECT * INTO STRICT v_event FROM rights.takedown_event e
  WHERE e.takedown_event_id = p_event_id;
  v_overlay_sha256 := release.canonical_jsonb_sha256(jsonb_build_object(
    'overrideId', p_override_id,
    'scopeId', p_scope_id,
    'scopeKind', p_scope_kind,
    'scopeTarget', p_subject_id,
    'eventId', p_event_id,
    'action', v_event.action,
    'effectiveFromUs',
      (extract(epoch FROM v_event.effective_from) * 1000000)::bigint,
    'effectiveUntilUs', CASE WHEN v_event.effective_until IS NULL THEN NULL
      ELSE (extract(epoch FROM v_event.effective_until) * 1000000)::bigint END,
    'reasonCode', v_event.reason_code,
    'evidenceId', v_event.evidence_item_id,
    'restrictiveMode', p_restrictive_mode,
    'supersedesOverrideId', p_supersedes_override_id,
    'createdAtUs', (extract(epoch FROM v_created_at) * 1000000)::bigint
  ));
  INSERT INTO rights.takedown_override VALUES (
    p_override_id, p_scope_id, p_restrictive_mode, v_overlay_sha256,
    p_supersedes_override_id, v_created_at);
  RETURN v_overlay_sha256;
END
$function$;

CREATE FUNCTION rights.record_takedown_event(
  p_event_id uuid, p_action rights.takedown_action,
  p_effective_from timestamptz, p_effective_until timestamptz,
  p_reason_code text, p_evidence_item_id uuid,
  p_scope_ids uuid[], p_scope_kinds rights.takedown_scope_kind[],
  p_subject_ids uuid[], p_override_ids uuid[],
  p_restrictive_modes rights.delivery_mode[],
  p_supersedes_override_ids uuid[]
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE
  v_overlay_sha256 core.sha256_hex;
  v_entry record;
  v_sidecar_id uuid;
  v_index integer;
BEGIN
  PERFORM rights.require_reviewer();
  PERFORM pg_advisory_xact_lock(hashtext('gda_v49_visual_seal_takedown'));
  IF COALESCE(cardinality(p_scope_ids), 0) = 0
    OR cardinality(p_scope_ids) IS DISTINCT FROM cardinality(p_scope_kinds)
    OR cardinality(p_scope_ids) IS DISTINCT FROM cardinality(p_subject_ids)
    OR cardinality(p_scope_ids) IS DISTINCT FROM cardinality(p_override_ids)
    OR cardinality(p_scope_ids) IS DISTINCT FROM cardinality(p_restrictive_modes)
    OR cardinality(p_scope_ids) IS DISTINCT FROM cardinality(p_supersedes_override_ids) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'TAKEDOWN_SCOPE_SET_CARDINALITY_INVALID';
  END IF;
  INSERT INTO rights.takedown_event VALUES (
    p_event_id, p_action, p_effective_from, p_effective_until,
    p_reason_code, p_evidence_item_id, session_user::text, clock_timestamp());
  PERFORM audit.record_decision_event('takedown', p_event_id);
  FOR v_index IN 1..cardinality(p_scope_ids) LOOP
    v_overlay_sha256 := rights.insert_takedown_scope(
      p_event_id, p_scope_ids[v_index], p_scope_kinds[v_index],
      p_subject_ids[v_index], p_override_ids[v_index],
      p_restrictive_modes[v_index], p_supersedes_override_ids[v_index]);
    FOR v_entry IN
      SELECT e.visual_registry_release_id, e.visual_registry_entry_id
      FROM release.visual_registry_entry e
      JOIN release.visual_registry_release r
        ON r.visual_registry_release_id = e.visual_registry_release_id
      WHERE r.release_state = 'sealed'
        AND rights.scope_matches_bridge(p_scope_ids[v_index],
          e.object_visual_reference_id)
    LOOP
      v_sidecar_id := gen_random_uuid();
      INSERT INTO release.visual_takedown_sidecar_event (
        visual_takedown_sidecar_event_id, visual_registry_release_id,
        visual_registry_entry_id, takedown_override_id, restrictive_mode,
        overlay_sha256, effective_from, effective_until, recorded_at
      ) VALUES (
        v_sidecar_id, v_entry.visual_registry_release_id,
        v_entry.visual_registry_entry_id, p_override_ids[v_index],
        p_restrictive_modes[v_index], v_overlay_sha256,
        p_effective_from, p_effective_until, clock_timestamp()
      );
      INSERT INTO audit.sidecar_event VALUES (
        gen_random_uuid(), NULL, v_sidecar_id,
        release.canonical_jsonb_sha256(jsonb_build_array(
          'takedown-sidecar', v_sidecar_id,
          v_entry.visual_registry_release_id,
          v_entry.visual_registry_entry_id, p_override_ids[v_index],
          v_overlay_sha256)), session_user::text, clock_timestamp()
      );
    END LOOP;
  END LOOP;
END
$function$;

CREATE FUNCTION release.append_visual_health_sidecar(
  p_sidecar_id uuid, p_registry_id uuid, p_entry_id uuid,
  p_locator_id uuid, p_health_observation_id uuid,
  p_audit_event_id uuid, p_audit_sha256 core.sha256_hex
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE v_health rights.endpoint_health_observation%ROWTYPE;
  v_role rights.locator_role;
BEGIN
  PERFORM raw.require_ingest_writer();
  IF NOT EXISTS (
    SELECT 1 FROM release.visual_registry_release r
    WHERE r.visual_registry_release_id = p_registry_id AND r.release_state = 'sealed'
  ) THEN RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'SIDECAR_REQUIRES_SEALED_VISUAL_REGISTRY'; END IF;
  SELECT h.* INTO v_health FROM rights.endpoint_health_observation h
  WHERE h.endpoint_health_observation_id = p_health_observation_id
    AND h.visual_locator_id = p_locator_id;
  SELECT l.locator_role INTO v_role FROM release.visual_registry_public_locator l
  WHERE l.visual_registry_release_id = p_registry_id
    AND l.visual_registry_entry_id = p_entry_id
    AND l.visual_locator_id = p_locator_id;
  IF v_health.endpoint_health_observation_id IS NULL OR v_role IS NULL
    OR v_health.checked_at > clock_timestamp() THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'HEALTH_SIDECAR_SOURCE_MISMATCH';
  END IF;
  INSERT INTO release.visual_health_sidecar_event (
    visual_health_sidecar_event_id, visual_registry_release_id,
    visual_registry_entry_id, visual_locator_id,
    endpoint_health_observation_id, locator_role, health_state,
    observed_at, valid_until, observation_sha256
  ) VALUES (
    p_sidecar_id, p_registry_id, p_entry_id, p_locator_id,
    p_health_observation_id, v_role, v_health.health_state,
    v_health.checked_at, v_health.valid_until,
    rights.compute_health_observation_sha(p_health_observation_id)
  );
  INSERT INTO audit.sidecar_event VALUES (
    p_audit_event_id, p_sidecar_id, NULL, p_audit_sha256,
    session_user::text, clock_timestamp());
END
$function$;

CREATE FUNCTION release.append_visual_takedown_sidecar(
  p_sidecar_id uuid, p_registry_id uuid, p_entry_id uuid,
  p_override_id uuid, p_audit_event_id uuid,
  p_audit_sha256 core.sha256_hex
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE v_entry release.visual_registry_entry%ROWTYPE;
  v_override rights.takedown_override%ROWTYPE;
  v_event rights.takedown_event%ROWTYPE;
BEGIN
  PERFORM rights.require_reviewer();
  SELECT * INTO v_entry FROM release.visual_registry_entry e
  WHERE e.visual_registry_release_id = p_registry_id
    AND e.visual_registry_entry_id = p_entry_id;
  SELECT o.* INTO v_override FROM rights.takedown_override o
  WHERE o.takedown_override_id = p_override_id;
  SELECT e.* INTO v_event FROM rights.takedown_scope s
  JOIN rights.takedown_event e ON e.takedown_event_id = s.takedown_event_id
  WHERE s.takedown_scope_id = v_override.takedown_scope_id;
  IF v_entry.visual_registry_entry_id IS NULL
    OR NOT EXISTS (
      SELECT 1 FROM release.visual_registry_release r
      WHERE r.visual_registry_release_id = p_registry_id AND r.release_state = 'sealed')
    OR NOT rights.scope_matches_bridge(
      v_override.takedown_scope_id, v_entry.object_visual_reference_id) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'TAKEDOWN_SIDECAR_SCOPE_MISMATCH';
  END IF;
  INSERT INTO release.visual_takedown_sidecar_event (
    visual_takedown_sidecar_event_id, visual_registry_release_id,
    visual_registry_entry_id, takedown_override_id, restrictive_mode,
    overlay_sha256, effective_from, effective_until, recorded_at
  ) VALUES (
    p_sidecar_id, p_registry_id, p_entry_id, p_override_id,
    v_override.restrictive_mode, v_override.overlay_sha256,
    v_event.effective_from, v_event.effective_until, clock_timestamp()
  );
  INSERT INTO audit.sidecar_event VALUES (
    p_audit_event_id, NULL, p_sidecar_id, p_audit_sha256,
    session_user::text, clock_timestamp());
END
$function$;

RESET ROLE;
