\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

CREATE FUNCTION rights.validate_one_object_visual_reference(p_bridge_id uuid)
RETURNS void
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_bridge rights.object_visual_reference%ROWTYPE;
  v_current_count integer;
  v_current rights.object_visual_reference_review_decision%ROWTYPE;
BEGIN
  SELECT * INTO v_bridge
  FROM rights.object_visual_reference b
  WHERE b.object_visual_reference_id = p_bridge_id;
  IF NOT FOUND THEN
    RETURN;
  END IF;

  SELECT count(*) INTO v_current_count
  FROM rights.object_visual_reference_review_decision d
  WHERE d.object_visual_reference_id = p_bridge_id
    AND NOT EXISTS (
      SELECT 1
      FROM rights.object_visual_reference_review_decision newer
      WHERE newer.supersedes_decision_id =
        d.object_visual_reference_review_decision_id
    );
  IF v_current_count > 1 THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'VISUAL_BRIDGE_REQUIRES_AT_MOST_ONE_CURRENT_DECISION';
  END IF;
  IF v_current_count = 1 THEN
    SELECT * INTO STRICT v_current
    FROM rights.object_visual_reference_review_decision d
    WHERE d.object_visual_reference_id = p_bridge_id
      AND NOT EXISTS (
        SELECT 1
        FROM rights.object_visual_reference_review_decision newer
        WHERE newer.supersedes_decision_id =
          d.object_visual_reference_review_decision_id
      );
  END IF;

  IF v_bridge.acceptance_state = 'accepted' AND (
      v_current_count <> 1 OR v_bridge.evidence_item_id IS NULL
      OR v_current.outcome <> 'accept'
      OR v_current.evidence_item_id IS DISTINCT FROM v_bridge.evidence_item_id
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'ACCEPTED_VISUAL_BRIDGE_REQUIRES_EVIDENCE_BOUND_ACCEPT_DECISION';
  ELSIF v_bridge.acceptance_state = 'rejected' AND (
      v_current_count <> 1 OR v_current.outcome <> 'reject'
      OR v_current.evidence_item_id IS DISTINCT FROM v_bridge.evidence_item_id
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'REJECTED_VISUAL_BRIDGE_REQUIRES_EVIDENCE_BOUND_REJECT_DECISION';
  ELSIF v_bridge.acceptance_state = 'superseded' AND (
      v_current_count <> 1 OR v_current.outcome <> 'supersede'
      OR v_current.evidence_item_id IS DISTINCT FROM v_bridge.evidence_item_id
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'SUPERSEDED_VISUAL_BRIDGE_REQUIRES_EVIDENCE_BOUND_DECISION';
  ELSIF v_bridge.acceptance_state = 'proposed' AND (
      v_current_count = 1 AND (
        v_current.outcome <> 'hold'
        OR v_current.evidence_item_id IS DISTINCT FROM
          v_bridge.evidence_item_id
      )
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'PROPOSED_VISUAL_BRIDGE_DECISION_MUST_BE_EVIDENCE_BOUND_HOLD';
  END IF;
END
$function$;

CREATE FUNCTION rights.enforce_object_visual_reference_decision()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_new_id uuid;
  v_old_id uuid;
BEGIN
  IF TG_OP <> 'DELETE' THEN
    v_new_id := (to_jsonb(NEW) ->> 'object_visual_reference_id')::uuid;
    PERFORM rights.validate_one_object_visual_reference(v_new_id);
  END IF;
  IF TG_OP <> 'INSERT' THEN
    v_old_id := (to_jsonb(OLD) ->> 'object_visual_reference_id')::uuid;
    IF v_old_id IS DISTINCT FROM v_new_id THEN
      PERFORM rights.validate_one_object_visual_reference(v_old_id);
    END IF;
  END IF;
  RETURN NULL;
END
$function$;

CREATE FUNCTION rights.enforce_object_visual_reference_decision_parent()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  IF NEW.supersedes_decision_id IS NOT NULL AND NOT EXISTS (
    SELECT 1
    FROM rights.object_visual_reference_review_decision prior
    WHERE prior.object_visual_reference_review_decision_id =
        NEW.supersedes_decision_id
      AND prior.object_visual_reference_id =
        NEW.object_visual_reference_id
      AND prior.decided_at < NEW.decided_at
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'VISUAL_BRIDGE_DECISION_SUPERSESSION_MISMATCH';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER object_visual_reference_decision_parent
AFTER INSERT ON rights.object_visual_reference_review_decision
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION rights.enforce_object_visual_reference_decision_parent();
CREATE CONSTRAINT TRIGGER object_visual_reference_decision_from_bridge
AFTER INSERT OR UPDATE ON rights.object_visual_reference
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION rights.enforce_object_visual_reference_decision();
CREATE CONSTRAINT TRIGGER object_visual_reference_decision_from_history
AFTER INSERT OR UPDATE OR DELETE
ON rights.object_visual_reference_review_decision
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION rights.enforce_object_visual_reference_decision();

CREATE FUNCTION rights.record_object_visual_reference_review_decision(
  p_decision_id uuid,
  p_bridge_id uuid,
  p_outcome workflow.review_outcome,
  p_evidence_item_id uuid,
  p_rationale text,
  p_supersedes_decision_id uuid,
  p_decided_at timestamptz
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
DECLARE
  v_bridge rights.object_visual_reference%ROWTYPE;
  v_current_id uuid;
  v_state provenance.assertion_status;
BEGIN
  PERFORM rights.require_reviewer();
  IF p_decided_at IS NULL OR p_decided_at > clock_timestamp() THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'FUTURE_VISUAL_BRIDGE_REVIEW_DENIED';
  END IF;
  IF p_outcome NOT IN ('accept','hold','reject','supersede') THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'VISUAL_BRIDGE_REVIEW_OUTCOME_INVALID';
  END IF;
  SELECT * INTO STRICT v_bridge
  FROM rights.object_visual_reference b
  WHERE b.object_visual_reference_id = p_bridge_id
  FOR UPDATE;
  SELECT d.object_visual_reference_review_decision_id INTO v_current_id
  FROM rights.object_visual_reference_review_decision d
  WHERE d.object_visual_reference_id = p_bridge_id
    AND NOT EXISTS (
      SELECT 1
      FROM rights.object_visual_reference_review_decision newer
      WHERE newer.supersedes_decision_id =
        d.object_visual_reference_review_decision_id
    );
  IF p_supersedes_decision_id IS DISTINCT FROM v_current_id THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'VISUAL_BRIDGE_REVIEW_MUST_SUPERSEDE_CURRENT_DECISION';
  END IF;
  IF v_current_id IS NULL AND v_bridge.acceptance_state <> 'proposed' THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'VISUAL_BRIDGE_INITIAL_REVIEW_REQUIRES_PROPOSED_STATE';
  END IF;

  INSERT INTO rights.object_visual_reference_review_decision (
    object_visual_reference_review_decision_id,
    object_visual_reference_id, outcome, evidence_item_id,
    reviewer_actor, rationale, supersedes_decision_id, decided_at
  ) VALUES (
    p_decision_id, p_bridge_id, p_outcome, p_evidence_item_id,
    session_user::text, p_rationale, p_supersedes_decision_id,
    p_decided_at
  );
  v_state := CASE p_outcome
    WHEN 'accept' THEN 'accepted'::provenance.assertion_status
    WHEN 'reject' THEN 'rejected'::provenance.assertion_status
    WHEN 'supersede' THEN 'superseded'::provenance.assertion_status
    ELSE 'proposed'::provenance.assertion_status
  END;
  UPDATE rights.object_visual_reference
  SET acceptance_state = v_state,
      evidence_item_id = p_evidence_item_id
  WHERE object_visual_reference_id = p_bridge_id;
  PERFORM audit.record_decision_event('visual_bridge_review', p_decision_id);
END
$function$;

RESET ROLE;
