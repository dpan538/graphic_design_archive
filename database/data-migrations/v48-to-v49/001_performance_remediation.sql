-- Phase 2B-P forward-only performance remediation.
--
-- This migration is deliberately separate from the frozen Phase 2A replay.
-- It preserves every constraint and trigger and changes only the execution
-- plan used to prove the same one-current-leaf and delivery-completeness
-- invariants.
\set ON_ERROR_STOP on

BEGIN;

CREATE INDEX rights_assessment_provider_object_target_idx
  ON rights.rights_assessment_provider_object
  (provider_object_id, rights_assessment_id);

CREATE INDEX rights_assessment_visual_reference_target_idx
  ON rights.rights_assessment_visual_reference
  (external_visual_reference_id, rights_assessment_id);

CREATE INDEX rights_assessment_representation_target_idx
  ON rights.rights_assessment_representation
  (digital_representation_id, rights_assessment_id);

CREATE INDEX rights_assessment_locator_target_idx
  ON rights.rights_assessment_locator
  (visual_locator_id, rights_assessment_id);

CREATE OR REPLACE FUNCTION rights.enforce_one_current_history_leaf()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog
AS $function$
DECLARE
  v_count integer;
  v_target uuid;
BEGIN
  IF TG_TABLE_NAME='rights_assessment' THEN
    IF NEW.supersedes_rights_assessment_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM rights.rights_assessment p
      WHERE p.rights_assessment_id=NEW.supersedes_rights_assessment_id
        AND p.assessed_at < NEW.assessed_at) THEN
      RAISE EXCEPTION USING ERRCODE='23514',
        MESSAGE='RIGHTS_ASSESSMENT_SUPERSESSION_TIME_OR_PARENT_MISMATCH';
    END IF;

    IF NEW.subject_kind='provider_object' THEN
      SELECT t.provider_object_id INTO v_target
      FROM rights.rights_assessment_provider_object t
      WHERE t.rights_assessment_id=NEW.rights_assessment_id;
      SELECT count(*) INTO v_count
      FROM rights.rights_assessment_provider_object t
      JOIN rights.rights_assessment x
        ON x.rights_assessment_id=t.rights_assessment_id
       AND x.subject_kind='provider_object'
      WHERE t.provider_object_id=v_target
        AND NOT EXISTS (SELECT 1 FROM rights.rights_assessment n
          WHERE n.supersedes_rights_assessment_id=x.rights_assessment_id);
    ELSIF NEW.subject_kind='external_visual_reference' THEN
      SELECT t.external_visual_reference_id INTO v_target
      FROM rights.rights_assessment_visual_reference t
      WHERE t.rights_assessment_id=NEW.rights_assessment_id;
      SELECT count(*) INTO v_count
      FROM rights.rights_assessment_visual_reference t
      JOIN rights.rights_assessment x
        ON x.rights_assessment_id=t.rights_assessment_id
       AND x.subject_kind='external_visual_reference'
      WHERE t.external_visual_reference_id=v_target
        AND NOT EXISTS (SELECT 1 FROM rights.rights_assessment n
          WHERE n.supersedes_rights_assessment_id=x.rights_assessment_id);
    ELSIF NEW.subject_kind='digital_representation' THEN
      SELECT t.digital_representation_id INTO v_target
      FROM rights.rights_assessment_representation t
      WHERE t.rights_assessment_id=NEW.rights_assessment_id;
      SELECT count(*) INTO v_count
      FROM rights.rights_assessment_representation t
      JOIN rights.rights_assessment x
        ON x.rights_assessment_id=t.rights_assessment_id
       AND x.subject_kind='digital_representation'
      WHERE t.digital_representation_id=v_target
        AND NOT EXISTS (SELECT 1 FROM rights.rights_assessment n
          WHERE n.supersedes_rights_assessment_id=x.rights_assessment_id);
    ELSIF NEW.subject_kind='visual_locator' THEN
      SELECT t.visual_locator_id INTO v_target
      FROM rights.rights_assessment_locator t
      WHERE t.rights_assessment_id=NEW.rights_assessment_id;
      SELECT count(*) INTO v_count
      FROM rights.rights_assessment_locator t
      JOIN rights.rights_assessment x
        ON x.rights_assessment_id=t.rights_assessment_id
       AND x.subject_kind='visual_locator'
      WHERE t.visual_locator_id=v_target
        AND NOT EXISTS (SELECT 1 FROM rights.rights_assessment n
          WHERE n.supersedes_rights_assessment_id=x.rights_assessment_id);
    ELSE
      v_count := 0;
    END IF;
  ELSIF TG_TABLE_NAME='provider_policy_evaluation' THEN
    IF NEW.supersedes_provider_policy_evaluation_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM rights.provider_policy_evaluation p
      WHERE p.provider_policy_evaluation_id=
          NEW.supersedes_provider_policy_evaluation_id
        AND p.object_visual_reference_id=NEW.object_visual_reference_id
        AND p.evaluated_at < NEW.evaluated_at) THEN
      RAISE EXCEPTION USING ERRCODE='23514',
        MESSAGE='POLICY_EVALUATION_SUPERSESSION_TIME_OR_PARENT_MISMATCH';
    END IF;
    SELECT count(*) INTO v_count FROM rights.provider_policy_evaluation x
    WHERE x.object_visual_reference_id=NEW.object_visual_reference_id
      AND NOT EXISTS (SELECT 1 FROM rights.provider_policy_evaluation n
        WHERE n.supersedes_provider_policy_evaluation_id=x.provider_policy_evaluation_id);
  ELSIF TG_TABLE_NAME='delivery_assessment' THEN
    IF NEW.supersedes_delivery_assessment_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM rights.delivery_assessment p
      WHERE p.delivery_assessment_id=NEW.supersedes_delivery_assessment_id
        AND p.object_visual_reference_id=NEW.object_visual_reference_id
        AND p.assessed_at < NEW.assessed_at) THEN
      RAISE EXCEPTION USING ERRCODE='23514',
        MESSAGE='DELIVERY_SUPERSESSION_TIME_OR_PARENT_MISMATCH';
    END IF;
    SELECT count(*) INTO v_count FROM rights.delivery_assessment x
    WHERE x.object_visual_reference_id=NEW.object_visual_reference_id
      AND NOT EXISTS (SELECT 1 FROM rights.delivery_assessment n
        WHERE n.supersedes_delivery_assessment_id=x.delivery_assessment_id);
  ELSE
    IF NEW.supersedes_attribution_bundle_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM rights.attribution_bundle p
      WHERE p.attribution_bundle_id=NEW.supersedes_attribution_bundle_id
        AND p.object_visual_reference_id=NEW.object_visual_reference_id
        AND p.validated_at < NEW.validated_at) THEN
      RAISE EXCEPTION USING ERRCODE='23514',
        MESSAGE='ATTRIBUTION_SUPERSESSION_TIME_OR_PARENT_MISMATCH';
    END IF;
    SELECT count(*) INTO v_count FROM rights.attribution_bundle x
    WHERE x.object_visual_reference_id=NEW.object_visual_reference_id
      AND NOT EXISTS (SELECT 1 FROM rights.attribution_bundle n
        WHERE n.supersedes_attribution_bundle_id=x.attribution_bundle_id);
  END IF;
  IF v_count<>1 THEN
    RAISE EXCEPTION USING ERRCODE='23514',
      MESSAGE='RIGHTS_HISTORY_REQUIRES_ONE_CURRENT_LEAF';
  END IF;
  RETURN NULL;
END
$function$;

CREATE OR REPLACE FUNCTION rights.validate_one_delivery_assessment(p_delivery_id uuid)
RETURNS void
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_id uuid := p_delivery_id;
  v_bridge uuid;
  v_mode rights.delivery_mode;
  v_assessed_at timestamptz;
  v_attribution uuid;
  v_rights_cap integer;
  v_policy_cap integer;
  v_attribution_cap integer;
  v_takedown_cap integer := 4;
  v_required_role rights.locator_role;
BEGIN
  SELECT d.object_visual_reference_id, d.delivery_mode, d.assessed_at,
    d.attribution_bundle_id
  INTO v_bridge, v_mode, v_assessed_at, v_attribution
  FROM rights.delivery_assessment d WHERE d.delivery_assessment_id = v_id;
  IF NOT FOUND THEN RETURN; END IF;
  IF v_assessed_at > clock_timestamp() THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'FUTURE_DELIVERY_ASSESSMENT_DENIED';
  END IF;

  -- Enumerate only subjects reachable from this delivery.  Each branch starts
  -- from a typed target and therefore uses the four forward-migration indexes
  -- above.  UNION retains the original set semantics when a representation is
  -- reachable through more than one qualified locator.
  IF NOT EXISTS (
    SELECT 1 FROM rights.delivery_rights_assessment x
    WHERE x.delivery_assessment_id = v_id
  ) OR EXISTS (
    WITH applicable(rights_assessment_id) AS (
      SELECT t.rights_assessment_id
      FROM rights.object_visual_reference b
      JOIN rights.external_visual_reference r
        ON r.external_visual_reference_id=b.external_visual_reference_id
      JOIN rights.rights_assessment_provider_object t
        ON t.provider_object_id=r.provider_object_id
      JOIN rights.rights_assessment a
        ON a.rights_assessment_id=t.rights_assessment_id
       AND a.subject_kind='provider_object'
      WHERE b.object_visual_reference_id=v_bridge
      UNION
      SELECT t.rights_assessment_id
      FROM rights.object_visual_reference b
      JOIN rights.rights_assessment_visual_reference t
        ON t.external_visual_reference_id=b.external_visual_reference_id
      JOIN rights.rights_assessment a
        ON a.rights_assessment_id=t.rights_assessment_id
       AND a.subject_kind='external_visual_reference'
      WHERE b.object_visual_reference_id=v_bridge
      UNION
      SELECT t.rights_assessment_id
      FROM rights.object_visual_reference b
      JOIN rights.delivery_locator_qualification q
        ON q.delivery_assessment_id=v_id
      JOIN rights.visual_locator_representation r
        ON r.visual_locator_id=q.visual_locator_id
       AND r.external_visual_reference_id=b.external_visual_reference_id
      JOIN rights.rights_assessment_representation t
        ON t.digital_representation_id=r.digital_representation_id
      JOIN rights.rights_assessment a
        ON a.rights_assessment_id=t.rights_assessment_id
       AND a.subject_kind='digital_representation'
      WHERE b.object_visual_reference_id=v_bridge
      UNION
      SELECT t.rights_assessment_id
      FROM rights.object_visual_reference b
      JOIN rights.delivery_locator_qualification q
        ON q.delivery_assessment_id=v_id
      JOIN rights.visual_locator l
        ON l.visual_locator_id=q.visual_locator_id
       AND l.external_visual_reference_id=b.external_visual_reference_id
      JOIN rights.rights_assessment_locator t
        ON t.visual_locator_id=q.visual_locator_id
      JOIN rights.rights_assessment a
        ON a.rights_assessment_id=t.rights_assessment_id
       AND a.subject_kind='visual_locator'
      WHERE b.object_visual_reference_id=v_bridge
    )
    SELECT 1
    FROM rights.delivery_rights_assessment x
    JOIN rights.rights_assessment a
      ON a.rights_assessment_id=x.rights_assessment_id
    WHERE x.delivery_assessment_id=v_id
      AND (
        NOT EXISTS (SELECT 1 FROM applicable p
          WHERE p.rights_assessment_id=a.rights_assessment_id)
        OR a.assessed_at > v_assessed_at
        OR EXISTS (SELECT 1 FROM rights.rights_assessment newer
          WHERE newer.supersedes_rights_assessment_id=a.rights_assessment_id)
      )
  ) OR EXISTS (
    WITH applicable(rights_assessment_id) AS (
      SELECT t.rights_assessment_id
      FROM rights.object_visual_reference b
      JOIN rights.external_visual_reference r
        ON r.external_visual_reference_id=b.external_visual_reference_id
      JOIN rights.rights_assessment_provider_object t
        ON t.provider_object_id=r.provider_object_id
      JOIN rights.rights_assessment a
        ON a.rights_assessment_id=t.rights_assessment_id
       AND a.subject_kind='provider_object'
      WHERE b.object_visual_reference_id=v_bridge
      UNION
      SELECT t.rights_assessment_id
      FROM rights.object_visual_reference b
      JOIN rights.rights_assessment_visual_reference t
        ON t.external_visual_reference_id=b.external_visual_reference_id
      JOIN rights.rights_assessment a
        ON a.rights_assessment_id=t.rights_assessment_id
       AND a.subject_kind='external_visual_reference'
      WHERE b.object_visual_reference_id=v_bridge
      UNION
      SELECT t.rights_assessment_id
      FROM rights.object_visual_reference b
      JOIN rights.delivery_locator_qualification q
        ON q.delivery_assessment_id=v_id
      JOIN rights.visual_locator_representation r
        ON r.visual_locator_id=q.visual_locator_id
       AND r.external_visual_reference_id=b.external_visual_reference_id
      JOIN rights.rights_assessment_representation t
        ON t.digital_representation_id=r.digital_representation_id
      JOIN rights.rights_assessment a
        ON a.rights_assessment_id=t.rights_assessment_id
       AND a.subject_kind='digital_representation'
      WHERE b.object_visual_reference_id=v_bridge
      UNION
      SELECT t.rights_assessment_id
      FROM rights.object_visual_reference b
      JOIN rights.delivery_locator_qualification q
        ON q.delivery_assessment_id=v_id
      JOIN rights.visual_locator l
        ON l.visual_locator_id=q.visual_locator_id
       AND l.external_visual_reference_id=b.external_visual_reference_id
      JOIN rights.rights_assessment_locator t
        ON t.visual_locator_id=q.visual_locator_id
      JOIN rights.rights_assessment a
        ON a.rights_assessment_id=t.rights_assessment_id
       AND a.subject_kind='visual_locator'
      WHERE b.object_visual_reference_id=v_bridge
    )
    SELECT 1
    FROM applicable p
    JOIN rights.rights_assessment a
      ON a.rights_assessment_id=p.rights_assessment_id
    WHERE NOT EXISTS (SELECT 1 FROM rights.rights_assessment newer
      WHERE newer.supersedes_rights_assessment_id=a.rights_assessment_id)
      AND NOT EXISTS (
        SELECT 1 FROM rights.delivery_rights_assessment linked
        WHERE linked.delivery_assessment_id=v_id
          AND linked.rights_assessment_id=a.rights_assessment_id
      )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'DELIVERY_REQUIRES_APPLICABLE_RIGHTS_ASSESSMENT';
  END IF;

  SELECT min(CASE
    WHEN x.evidence_role = 'contradicts' THEN 1
    WHEN x.evidence_role = 'contextualises' THEN 2
    WHEN a.assessed_state = 'permitted' THEN CASE
      WHEN a.subject_kind = 'digital_representation' THEN 2 ELSE 4 END
    WHEN a.assessed_state = 'restricted' THEN 1
    ELSE 2 END)
  INTO v_rights_cap
  FROM rights.delivery_rights_assessment x
  JOIN rights.rights_assessment a ON a.rights_assessment_id = x.rights_assessment_id
  WHERE x.delivery_assessment_id = v_id;

  IF NOT EXISTS (
    SELECT 1 FROM rights.delivery_policy_evaluation x
    WHERE x.delivery_assessment_id = v_id
  ) OR EXISTS (
    SELECT 1 FROM rights.delivery_policy_evaluation x
    JOIN rights.provider_policy_evaluation e
      ON e.provider_policy_evaluation_id = x.provider_policy_evaluation_id
    WHERE x.delivery_assessment_id = v_id
      AND (e.object_visual_reference_id IS DISTINCT FROM v_bridge
        OR e.evaluated_at > v_assessed_at
        OR EXISTS (
          SELECT 1 FROM rights.provider_policy_evaluation newer
          WHERE newer.supersedes_provider_policy_evaluation_id =
            e.provider_policy_evaluation_id
        ))
  ) OR EXISTS (
    SELECT 1 FROM rights.provider_policy_evaluation e
    WHERE e.object_visual_reference_id = v_bridge
      AND NOT EXISTS (
        SELECT 1 FROM rights.provider_policy_evaluation newer
        WHERE newer.supersedes_provider_policy_evaluation_id =
          e.provider_policy_evaluation_id
      )
      AND NOT EXISTS (
        SELECT 1 FROM rights.delivery_policy_evaluation linked
        WHERE linked.delivery_assessment_id = v_id
          AND linked.provider_policy_evaluation_id =
            e.provider_policy_evaluation_id
      )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'DELIVERY_REQUIRES_APPLICABLE_PROVIDER_POLICY_EVALUATION';
  END IF;

  SELECT min(rights.policy_rank(e.evaluated_state))
  INTO v_policy_cap
  FROM rights.delivery_policy_evaluation x
  JOIN rights.provider_policy_evaluation e
    ON e.provider_policy_evaluation_id = x.provider_policy_evaluation_id
  WHERE x.delivery_assessment_id = v_id;

  IF v_attribution IS NULL THEN
    v_attribution_cap := 2;
  ELSIF NOT EXISTS (
    SELECT 1 FROM rights.attribution_bundle a
    WHERE a.attribution_bundle_id = v_attribution
      AND a.object_visual_reference_id = v_bridge
      AND a.evidence_item_id IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM rights.attribution_bundle newer
        WHERE newer.supersedes_attribution_bundle_id = a.attribution_bundle_id
      )
      AND 1 = (
        SELECT count(*) FROM rights.attribution_bundle current_bundle
        WHERE current_bundle.object_visual_reference_id = v_bridge
          AND NOT EXISTS (
            SELECT 1 FROM rights.attribution_bundle newer
            WHERE newer.supersedes_attribution_bundle_id =
              current_bundle.attribution_bundle_id
          )
      )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'DELIVERY_ATTRIBUTION_BUNDLE_BRIDGE_MISMATCH';
  ELSIF EXISTS (
    SELECT 1 FROM rights.attribution_bundle a
    WHERE a.attribution_bundle_id = v_attribution
      AND a.validated_at > v_assessed_at
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'DELIVERY_ATTRIBUTION_POSTDATES_DECISION';
  ELSIF EXISTS (
    SELECT 1 FROM rights.attribution_bundle a
    WHERE a.attribution_bundle_id = v_attribution
      AND a.bundle_sha256 IS DISTINCT FROM
        rights.compute_attribution_bundle_sha(a.attribution_bundle_id)
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'ATTRIBUTION_BUNDLE_HASH_MISMATCH';
  ELSIF EXISTS (
    SELECT 1 FROM rights.attribution_bundle a
    WHERE a.attribution_bundle_id = v_attribution
      AND a.attribution_state = 'complete'
      AND EXISTS (
        SELECT 1 FROM rights.attribution_bundle_value x
        WHERE x.attribution_bundle_id = a.attribution_bundle_id
          AND x.value_kind = 'attribution'
      )
      AND EXISTS (
        SELECT 1 FROM rights.attribution_bundle_value x
        WHERE x.attribution_bundle_id = a.attribution_bundle_id
          AND x.value_kind = 'required_statement'
      )
  ) THEN
    v_attribution_cap := 4;
  ELSE
    v_attribution_cap := 2;
  END IF;

  SELECT COALESCE(min(CASE e.action WHEN 'blocked' THEN 0 ELSE 1 END), 4)
  INTO v_takedown_cap
  FROM rights.takedown_event e
  JOIN rights.takedown_scope s ON s.takedown_event_id = e.takedown_event_id
  WHERE e.effective_from <= v_assessed_at
    AND (e.effective_until IS NULL OR e.effective_until > v_assessed_at)
    AND rights.scope_matches_bridge(s.takedown_scope_id, v_bridge);

  IF rights.delivery_rank(v_mode) > LEAST(
    v_rights_cap, v_policy_cap, v_attribution_cap, v_takedown_cap
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'DELIVERY_ASSESSMENT_EXCEEDS_FAIL_CLOSED_CAP';
  END IF;

  v_required_role := CASE v_mode
    WHEN 'link_only' THEN 'canonical_record'::rights.locator_role
    WHEN 'source_viewer' THEN 'source_viewer'::rights.locator_role
    WHEN 'remote_image' THEN 'direct_image'::rights.locator_role
    ELSE NULL
  END;

  IF EXISTS (
    SELECT 1
    FROM rights.delivery_locator_qualification q
    JOIN rights.visual_locator l ON l.visual_locator_id = q.visual_locator_id
    JOIN rights.endpoint_health_observation h
      ON h.endpoint_health_observation_id = q.endpoint_health_observation_id
    JOIN rights.object_visual_reference b ON b.object_visual_reference_id = v_bridge
    WHERE q.delivery_assessment_id = v_id
      AND (
        l.external_visual_reference_id IS DISTINCT FROM b.external_visual_reference_id
        OR l.locator_role IS DISTINCT FROM q.allowlisted_role
        OR h.visual_locator_id IS DISTINCT FROM l.visual_locator_id
        OR h.health_state <> 'healthy_fresh'
        OR h.checked_at > v_assessed_at
        OR h.valid_until IS NULL
        OR h.valid_until <= v_assessed_at
        OR EXISTS (
          SELECT 1 FROM rights.visual_locator newer
          WHERE newer.supersedes_visual_locator_id = l.visual_locator_id
        )
      )
  ) OR (v_required_role IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM rights.delivery_locator_qualification q
    WHERE q.delivery_assessment_id = v_id
      AND q.allowlisted_role = v_required_role
  )) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'DELIVERY_REQUIRES_MATCHING_HEALTHY_FRESH_TYPED_LOCATOR';
  END IF;
  RETURN;
END
$function$;

COMMIT;
