\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

CREATE FUNCTION rights.delivery_mode_for_rule(p_rule rights.delivery_rule_id)
RETURNS rights.delivery_mode
LANGUAGE sql IMMUTABLE STRICT
SET search_path = pg_catalog
RETURN CASE p_rule
  WHEN 'RD-001' THEN 'blocked'::rights.delivery_mode
  WHEN 'RD-002' THEN 'citation_only'::rights.delivery_mode
  WHEN 'RD-010' THEN 'citation_only'::rights.delivery_mode
  WHEN 'RD-011' THEN 'citation_only'::rights.delivery_mode
  WHEN 'RD-020' THEN 'link_only'::rights.delivery_mode
  WHEN 'RD-021' THEN 'citation_only'::rights.delivery_mode
  WHEN 'RD-030' THEN 'citation_only'::rights.delivery_mode
  WHEN 'RD-040' THEN 'link_only'::rights.delivery_mode
  WHEN 'RD-041' THEN 'citation_only'::rights.delivery_mode
  WHEN 'RD-050' THEN 'source_viewer'::rights.delivery_mode
  WHEN 'RD-051' THEN 'link_only'::rights.delivery_mode
  WHEN 'RD-052' THEN 'citation_only'::rights.delivery_mode
  WHEN 'RD-060' THEN 'link_only'::rights.delivery_mode
  WHEN 'RD-061' THEN 'citation_only'::rights.delivery_mode
  WHEN 'RD-070' THEN 'link_only'::rights.delivery_mode
  WHEN 'RD-071' THEN 'citation_only'::rights.delivery_mode
  WHEN 'RD-080' THEN 'remote_image'::rights.delivery_mode
  WHEN 'RD-081' THEN 'link_only'::rights.delivery_mode
  WHEN 'RD-082' THEN 'citation_only'::rights.delivery_mode
  ELSE 'citation_only'::rights.delivery_mode
END;

CREATE FUNCTION rights.enforce_delivery_rule_pair()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  IF NEW.delivery_mode IS DISTINCT FROM
      rights.delivery_mode_for_rule(NEW.reason_code)
    OR NEW.machine_reason_code IS DISTINCT FROM
      rights.machine_reason_for_rule(NEW.reason_code) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'DELIVERY_RULE_MODE_REASON_PAIR_INVALID';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER delivery_rule_pair
AFTER INSERT OR UPDATE ON rights.delivery_assessment
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION rights.enforce_delivery_rule_pair();

DROP FUNCTION rights.record_delivery_assessment(
  uuid, uuid, uuid[], provenance.evidence_role[], uuid[], uuid,
  rights.delivery_mode, text, timestamptz, uuid,
  uuid[], uuid[], rights.locator_role[]
);

CREATE FUNCTION rights.record_delivery_assessment(
  p_delivery_id uuid, p_bridge_id uuid,
  p_rights_assessment_ids uuid[],
  p_rights_evidence_roles provenance.evidence_role[],
  p_policy_evaluation_ids uuid[], p_attribution_bundle_id uuid,
  p_mode rights.delivery_mode, p_reason_code rights.delivery_rule_id,
  p_assessed_at timestamptz, p_supersedes_id uuid,
  p_locator_ids uuid[], p_health_observation_ids uuid[],
  p_locator_roles rights.locator_role[]
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
DECLARE v_index integer;
BEGIN
  PERFORM rights.require_reviewer();
  PERFORM pg_advisory_xact_lock(hashtext('gda_v49_visual_seal_takedown'));
  IF p_assessed_at > clock_timestamp() THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'FUTURE_DELIVERY_ASSESSMENT_DENIED';
  END IF;
  IF p_mode IS DISTINCT FROM rights.delivery_mode_for_rule(p_reason_code) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'DELIVERY_RULE_MODE_PAIR_INVALID';
  END IF;
  IF COALESCE(cardinality(p_rights_assessment_ids), 0) = 0
    OR cardinality(p_rights_assessment_ids)
      IS DISTINCT FROM cardinality(p_rights_evidence_roles)
    OR COALESCE(cardinality(p_policy_evaluation_ids), 0) = 0
    OR cardinality(p_locator_ids)
      IS DISTINCT FROM cardinality(p_health_observation_ids)
    OR cardinality(p_locator_ids)
      IS DISTINCT FROM cardinality(p_locator_roles) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'DELIVERY_GOVERNING_SET_CARDINALITY_INVALID';
  END IF;
  INSERT INTO rights.delivery_assessment (
    delivery_assessment_id, object_visual_reference_id,
    attribution_bundle_id, delivery_mode, reason_code, assessor_actor,
    assessed_at, supersedes_delivery_assessment_id, machine_reason_code
  ) VALUES (
    p_delivery_id, p_bridge_id, p_attribution_bundle_id, p_mode,
    p_reason_code, session_user::text, p_assessed_at, p_supersedes_id,
    rights.machine_reason_for_rule(p_reason_code)
  );
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
      IF num_nonnulls(
          p_locator_ids[v_index], p_health_observation_ids[v_index],
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

DROP FUNCTION rights.insert_takedown_scope(
  uuid, uuid, rights.takedown_scope_kind, uuid, uuid,
  rights.delivery_mode, uuid
);

CREATE FUNCTION rights.insert_takedown_scope(
  p_event_id uuid, p_scope_id uuid, p_scope_ordinal integer,
  p_scope_kind rights.takedown_scope_kind, p_subject_id uuid,
  p_override_id uuid, p_override_version integer,
  p_restrictive_mode rights.delivery_mode,
  p_supersedes_override_id uuid
)
RETURNS core.sha256_hex
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_created_at timestamptz := clock_timestamp();
  v_overlay_sha256 core.sha256_hex;
  v_event rights.takedown_event%ROWTYPE;
BEGIN
  INSERT INTO rights.takedown_scope (
    takedown_scope_id, takedown_event_id, scope_kind, scope_ordinal
  ) VALUES (p_scope_id, p_event_id, p_scope_kind, p_scope_ordinal);
  CASE p_scope_kind
    WHEN 'provider' THEN
      INSERT INTO rights.takedown_scope_provider VALUES (
        p_scope_id, p_subject_id);
    WHEN 'provider_object' THEN
      INSERT INTO rights.takedown_scope_provider_object VALUES (
        p_scope_id, p_subject_id);
    WHEN 'external_visual_reference' THEN
      INSERT INTO rights.takedown_scope_visual_reference VALUES (
        p_scope_id, p_subject_id);
    WHEN 'digital_representation' THEN
      INSERT INTO rights.takedown_scope_representation VALUES (
        p_scope_id, p_subject_id);
    WHEN 'visual_locator' THEN
      INSERT INTO rights.takedown_scope_locator VALUES (
        p_scope_id, p_subject_id);
    WHEN 'object_visual_reference' THEN
      INSERT INTO rights.takedown_scope_object_visual_reference VALUES (
        p_scope_id, p_subject_id);
  END CASE;
  SELECT * INTO STRICT v_event
  FROM rights.takedown_event e
  WHERE e.takedown_event_id = p_event_id;
  v_overlay_sha256 := release.canonical_jsonb_sha256(jsonb_build_object(
    'action', v_event.action,
    'createdAtUs', (extract(epoch FROM v_created_at) * 1000000)::bigint,
    'effectiveFromUs',
      (extract(epoch FROM v_event.effective_from) * 1000000)::bigint,
    'effectiveUntilUs', CASE WHEN v_event.effective_until IS NULL THEN NULL
      ELSE (extract(epoch FROM v_event.effective_until) * 1000000)::bigint END,
    'eventId', p_event_id,
    'evidenceId', v_event.evidence_item_id,
    'overrideId', p_override_id,
    'overrideVersion', p_override_version,
    'reasonCode', v_event.reason_code,
    'restrictiveMode', p_restrictive_mode,
    'scopeId', p_scope_id,
    'scopeKind', p_scope_kind,
    'scopeOrdinal', p_scope_ordinal,
    'scopeTarget', p_subject_id,
    'supersedesOverrideId', p_supersedes_override_id
  ));
  INSERT INTO rights.takedown_override (
    takedown_override_id, takedown_scope_id, restrictive_mode,
    overlay_sha256, supersedes_takedown_override_id, created_at,
    override_version
  ) VALUES (
    p_override_id, p_scope_id, p_restrictive_mode,
    v_overlay_sha256, p_supersedes_override_id, v_created_at,
    p_override_version
  );
  RETURN v_overlay_sha256;
END
$function$;

CREATE OR REPLACE FUNCTION rights.record_takedown_event(
  p_event_id uuid, p_action rights.takedown_action,
  p_effective_from timestamptz, p_effective_until timestamptz,
  p_reason_code text, p_evidence_item_id uuid,
  p_scope_ids uuid[], p_scope_kinds rights.takedown_scope_kind[],
  p_subject_ids uuid[], p_override_ids uuid[],
  p_restrictive_modes rights.delivery_mode[],
  p_supersedes_override_ids uuid[]
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
DECLARE
  v_overlay_sha256 core.sha256_hex;
  v_entry record;
  v_sidecar_id uuid;
  v_index integer;
BEGIN
  PERFORM rights.require_reviewer();
  PERFORM pg_advisory_xact_lock(hashtext('gda_v49_visual_seal_takedown'));
  IF p_evidence_item_id IS NULL
    OR COALESCE(cardinality(p_scope_ids), 0) = 0
    OR cardinality(p_scope_ids) IS DISTINCT FROM cardinality(p_scope_kinds)
    OR cardinality(p_scope_ids) IS DISTINCT FROM cardinality(p_subject_ids)
    OR cardinality(p_scope_ids) IS DISTINCT FROM cardinality(p_override_ids)
    OR cardinality(p_scope_ids) IS DISTINCT FROM cardinality(p_restrictive_modes)
    OR cardinality(p_scope_ids)
      IS DISTINCT FROM cardinality(p_supersedes_override_ids)
    OR EXISTS (
      SELECT 1 FROM unnest(p_supersedes_override_ids) x(id)
      WHERE x.id IS NOT NULL) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'TAKEDOWN_NEW_EVENT_SCOPE_SET_INVALID';
  END IF;
  INSERT INTO rights.takedown_event VALUES (
    p_event_id, p_action, p_effective_from, p_effective_until,
    p_reason_code, p_evidence_item_id, session_user::text,
    clock_timestamp());
  PERFORM audit.record_decision_event('takedown', p_event_id);
  FOR v_index IN 1..cardinality(p_scope_ids) LOOP
    v_overlay_sha256 := rights.insert_takedown_scope(
      p_event_id, p_scope_ids[v_index], v_index,
      p_scope_kinds[v_index], p_subject_ids[v_index],
      p_override_ids[v_index], 1,
      p_restrictive_modes[v_index], NULL);
    FOR v_entry IN
      SELECT e.visual_registry_release_id, e.visual_registry_entry_id
      FROM release.visual_registry_entry e
      JOIN release.visual_registry_release r
        ON r.visual_registry_release_id = e.visual_registry_release_id
      WHERE r.release_state = 'sealed'
        AND rights.scope_matches_bridge(
          p_scope_ids[v_index], e.object_visual_reference_id)
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

CREATE FUNCTION rights.record_takedown_override_correction(
  p_override_id uuid, p_scope_id uuid,
  p_restrictive_mode rights.delivery_mode,
  p_supersedes_override_id uuid
)
RETURNS core.sha256_hex
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
DECLARE
  v_prior rights.takedown_override%ROWTYPE;
  v_event rights.takedown_event%ROWTYPE;
  v_created_at timestamptz := clock_timestamp();
  v_sha core.sha256_hex;
  v_entry record;
  v_sidecar_id uuid;
  v_recorded_at timestamptz;
BEGIN
  PERFORM rights.require_reviewer();
  PERFORM pg_advisory_xact_lock(hashtext('gda_v49_visual_seal_takedown'));
  SELECT * INTO STRICT v_prior
  FROM rights.takedown_override o
  WHERE o.takedown_override_id = p_supersedes_override_id
    AND o.takedown_scope_id = p_scope_id
    AND NOT EXISTS (
      SELECT 1 FROM rights.takedown_override newer
      WHERE newer.supersedes_takedown_override_id = o.takedown_override_id)
  FOR UPDATE;
  SELECT e.* INTO STRICT v_event
  FROM rights.takedown_scope s
  JOIN rights.takedown_event e ON e.takedown_event_id = s.takedown_event_id
  WHERE s.takedown_scope_id = p_scope_id;
  IF rights.delivery_rank(p_restrictive_mode) >
      rights.delivery_rank(v_prior.restrictive_mode)
    OR rights.delivery_rank(p_restrictive_mode) >
      rights.delivery_rank(CASE v_event.action
        WHEN 'blocked' THEN 'blocked'::rights.delivery_mode
        ELSE 'citation_only'::rights.delivery_mode END) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'TAKEDOWN_OVERRIDE_CANNOT_RELAX';
  END IF;
  v_sha := release.canonical_jsonb_sha256(jsonb_build_object(
    'action', v_event.action,
    'createdAtUs', (extract(epoch FROM v_created_at) * 1000000)::bigint,
    'effectiveFromUs',
      (extract(epoch FROM v_event.effective_from) * 1000000)::bigint,
    'effectiveUntilUs', CASE WHEN v_event.effective_until IS NULL THEN NULL
      ELSE (extract(epoch FROM v_event.effective_until) * 1000000)::bigint END,
    'eventId', v_event.takedown_event_id,
    'evidenceId', v_event.evidence_item_id,
    'overrideId', p_override_id,
    'overrideVersion', v_prior.override_version + 1,
    'reasonCode', v_event.reason_code,
    'restrictiveMode', p_restrictive_mode,
    'scopeId', p_scope_id,
    'scopeKind', (SELECT s.scope_kind FROM rights.takedown_scope s
      WHERE s.takedown_scope_id = p_scope_id),
    'scopeOrdinal', (SELECT s.scope_ordinal FROM rights.takedown_scope s
      WHERE s.takedown_scope_id = p_scope_id),
    'scopeTarget', rights.takedown_scope_target_key(p_scope_id),
    'supersedesOverrideId', p_supersedes_override_id
  ));
  INSERT INTO rights.takedown_override (
    takedown_override_id, takedown_scope_id, restrictive_mode,
    overlay_sha256, supersedes_takedown_override_id, created_at,
    override_version
  ) VALUES (
    p_override_id, p_scope_id, p_restrictive_mode, v_sha,
    p_supersedes_override_id, v_created_at,
    v_prior.override_version + 1
  );
  FOR v_entry IN
    SELECT e.visual_registry_release_id, e.visual_registry_entry_id
    FROM release.visual_registry_entry e
    JOIN release.visual_registry_release r
      ON r.visual_registry_release_id = e.visual_registry_release_id
    WHERE r.release_state = 'sealed'
      AND rights.scope_matches_bridge(
        p_scope_id, e.object_visual_reference_id)
  LOOP
    v_sidecar_id := gen_random_uuid();
    v_recorded_at := clock_timestamp();
    INSERT INTO release.visual_takedown_sidecar_event (
      visual_takedown_sidecar_event_id, visual_registry_release_id,
      visual_registry_entry_id, takedown_override_id, restrictive_mode,
      overlay_sha256, effective_from, effective_until, recorded_at
    ) VALUES (
      v_sidecar_id, v_entry.visual_registry_release_id,
      v_entry.visual_registry_entry_id, p_override_id,
      p_restrictive_mode, v_sha, v_event.effective_from,
      v_event.effective_until, v_recorded_at
    );
    INSERT INTO audit.sidecar_event (
      sidecar_event_id, visual_health_sidecar_event_id,
      visual_takedown_sidecar_event_id, event_sha256, actor, occurred_at
    ) VALUES (
      gen_random_uuid(), NULL, v_sidecar_id,
      release.canonical_jsonb_sha256(jsonb_build_array(
        'takedown-correction-sidecar', v_sidecar_id,
        v_entry.visual_registry_release_id,
        v_entry.visual_registry_entry_id, p_override_id, v_sha)),
      session_user::text, v_recorded_at
    );
  END LOOP;
  RETURN v_sha;
END
$function$;

RESET ROLE;
