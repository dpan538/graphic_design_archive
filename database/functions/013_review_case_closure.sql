\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

ALTER FUNCTION research.record_claim_review_decision(
  uuid, uuid, workflow.review_outcome, boolean, text, uuid,
  uuid[], provenance.evidence_role[]
) RENAME TO record_claim_review_decision_v1;

CREATE FUNCTION research.record_claim_review_decision(
  p_decision_id uuid, p_claim_revision_id uuid,
  p_outcome workflow.review_outcome, p_heightened_review boolean,
  p_rationale text, p_supersedes_decision_id uuid,
  p_evidence_item_ids uuid[], p_evidence_roles provenance.evidence_role[]
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM rights.require_reviewer();
  IF p_supersedes_decision_id IS NULL THEN
    PERFORM 1
    FROM workflow.review_case c
    JOIN workflow.review_case_claim x USING (review_case_id)
    WHERE x.claim_revision_id = p_claim_revision_id
      AND c.queue_state IN ('claimed', 'in_review')
      AND c.claimed_by = session_user::text
    FOR UPDATE OF c;
    IF NOT FOUND THEN
      RAISE EXCEPTION USING ERRCODE = '55000',
        MESSAGE = 'CLAIM_REVIEW_CASE_NOT_CLAIMED';
    END IF;
  END IF;
  PERFORM research.record_claim_review_decision_v1(
    p_decision_id, p_claim_revision_id, p_outcome,
    p_heightened_review, p_rationale, p_supersedes_decision_id,
    p_evidence_item_ids, p_evidence_roles);
  UPDATE workflow.review_case c
  SET queue_state = 'resolved', claimed_by = NULL, claimed_at = NULL,
    resolved_at = clock_timestamp()
  FROM workflow.review_case_claim x
  WHERE x.review_case_id = c.review_case_id
    AND x.claim_revision_id = p_claim_revision_id
    AND c.claimed_by = session_user::text;
END
$function$;

ALTER FUNCTION research.record_relation_review_decision(
  uuid, uuid, workflow.review_outcome, text, uuid,
  uuid[], provenance.evidence_role[], uuid, core.sha256_hex
) RENAME TO record_relation_review_decision_v1;

CREATE FUNCTION research.record_relation_review_decision(
  p_decision_id uuid, p_relation_id uuid,
  p_outcome workflow.review_outcome, p_rationale text,
  p_supersedes_decision_id uuid,
  p_evidence_item_ids uuid[], p_evidence_roles provenance.evidence_role[],
  p_audit_event_id uuid, p_audit_event_sha256 core.sha256_hex
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM rights.require_reviewer();
  IF p_supersedes_decision_id IS NULL THEN
    PERFORM 1
    FROM workflow.review_case c
    JOIN workflow.review_case_relation x USING (review_case_id)
    WHERE x.semantic_relation_id = p_relation_id
      AND c.queue_state IN ('claimed', 'in_review')
      AND c.claimed_by = session_user::text
    FOR UPDATE OF c;
    IF NOT FOUND THEN
      RAISE EXCEPTION USING ERRCODE = '55000',
        MESSAGE = 'RELATION_REVIEW_CASE_NOT_CLAIMED';
    END IF;
  END IF;
  PERFORM research.record_relation_review_decision_v1(
    p_decision_id, p_relation_id, p_outcome, p_rationale,
    p_supersedes_decision_id, p_evidence_item_ids, p_evidence_roles,
    p_audit_event_id, p_audit_event_sha256);
  UPDATE workflow.review_case c
  SET queue_state = 'resolved', claimed_by = NULL, claimed_at = NULL,
    resolved_at = clock_timestamp()
  FROM workflow.review_case_relation x
  WHERE x.review_case_id = c.review_case_id
    AND x.semantic_relation_id = p_relation_id
    AND c.claimed_by = session_user::text;
END
$function$;

RESET ROLE;
