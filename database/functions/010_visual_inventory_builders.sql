\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

CREATE FUNCTION release.set_visual_policy_input_to_draft(
  p_registry_id uuid,
  p_legacy_disposition_receipt_sha256 core.sha256_hex,
  p_provider_registry_sha256 core.sha256_hex,
  p_rights_policy_sha256 core.sha256_hex,
  p_delivery_truth_table_sha256 core.sha256_hex,
  p_serializer_contract_sha256 core.sha256_hex
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_visual_draft(p_registry_id);
  INSERT INTO release.visual_registry_policy_input VALUES (
    p_registry_id, p_legacy_disposition_receipt_sha256,
    p_provider_registry_sha256, p_rights_policy_sha256,
    p_delivery_truth_table_sha256, p_serializer_contract_sha256);
END
$function$;

CREATE FUNCTION release.snapshot_legacy_visual_baseline_to_draft(
  p_registry_id uuid, p_receipt_sha256 core.sha256_hex
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
SET TimeZone = 'UTC'
AS $function$
DECLARE
  v_accounted bigint;
  v_reference bigint;
  v_none bigint;
  v_unclassified bigint;
  v_set_sha core.sha256_hex;
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_visual_draft(p_registry_id);
  SELECT count(*),
    count(*) FILTER (WHERE d.visual_reference_count > 0),
    count(*) FILTER (WHERE d.visual_reference_count = 0),
    count(*) FILTER (WHERE NOT EXISTS (
      SELECT 1 FROM rights.legacy_visual_surface_classification c
      WHERE c.legacy_surface_ledger_id = d.legacy_surface_ledger_id))
  INTO v_accounted, v_reference, v_none, v_unclassified
  FROM rights.legacy_visual_surface_disposition d;

  SELECT release.canonical_jsonb_sha256(COALESCE(jsonb_agg(
    jsonb_build_object(
      'classifications', COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
          'disposition', c.disposition,
          'evidenceItemId', c.evidence_item_id
        ) ORDER BY c.disposition)
        FROM rights.legacy_visual_surface_classification c
        WHERE c.legacy_surface_ledger_id = d.legacy_surface_ledger_id
      ), '[]'::jsonb),
      'dispositionSetSha256', d.disposition_set_sha256,
      'legacySurfaceLedgerId', d.legacy_surface_ledger_id,
      'locatorOccurrenceCount', d.locator_occurrence_count,
      'sourceFingerprint', d.source_fingerprint,
      'visualReferenceCount', d.visual_reference_count
    ) ORDER BY d.legacy_surface_ledger_id
  ), '[]'::jsonb))
  INTO v_set_sha
  FROM rights.legacy_visual_surface_disposition d;

  INSERT INTO release.visual_registry_legacy_disposition_snapshot VALUES (
    p_registry_id, v_accounted, v_reference, v_none,
    v_unclassified, v_set_sha, p_receipt_sha256);
END
$function$;

CREATE FUNCTION release.add_visual_asset_to_draft(
  p_registry_id uuid, p_relative_path text,
  p_resource_kind core.release_token, p_media_type text,
  p_content_encoding text, p_schema_id text,
  p_byte_length bigint, p_record_count bigint,
  p_sha256 core.sha256_hex, p_deterministic_sort_key text,
  p_partition_description text, p_uncompressed_sha256 core.sha256_hex
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_visual_draft(p_registry_id);
  INSERT INTO release.visual_registry_asset VALUES (
    p_registry_id, p_relative_path, p_resource_kind, p_media_type,
    p_content_encoding, p_schema_id, p_byte_length, p_record_count,
    p_sha256, p_deterministic_sort_key, p_partition_description,
    p_uncompressed_sha256);
END
$function$;

CREATE FUNCTION release.add_visual_asset_dependency_to_draft(
  p_registry_id uuid, p_asset_path text, p_dependency_path text
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
DECLARE v_dependency_sha core.sha256_hex;
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_visual_draft(p_registry_id);
  SELECT a.sha256 INTO STRICT v_dependency_sha
  FROM release.visual_registry_asset a
  WHERE a.visual_registry_release_id = p_registry_id
    AND a.relative_path = p_dependency_path;
  INSERT INTO release.visual_registry_asset_dependency VALUES (
    p_registry_id, p_asset_path, p_dependency_path, v_dependency_sha);
END
$function$;

CREATE OR REPLACE FUNCTION release.copy_visual_entry_to_draft(
  p_registry_id uuid, p_entry_id uuid,
  p_object_visual_reference_id uuid, p_delivery_assessment_id uuid
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
SET TimeZone = 'UTC'
AS $function$
DECLARE
  v_registry release.visual_registry_release%ROWTYPE;
  v_bridge rights.object_visual_reference%ROWTYPE;
  v_reference rights.external_visual_reference%ROWTYPE;
  v_object core.archive_object%ROWTYPE;
  v_delivery rights.delivery_assessment%ROWTYPE;
  v_provider_object rights.provider_object%ROWTYPE;
  v_provider rights.provider%ROWTYPE;
  v_bridge_decision rights.object_visual_reference_review_decision%ROWTYPE;
  v_machine_reason rights.delivery_reason_code;
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_visual_draft(p_registry_id);
  SELECT * INTO STRICT v_registry
  FROM release.visual_registry_release r
  WHERE r.visual_registry_release_id = p_registry_id
  FOR SHARE;
  SELECT * INTO STRICT v_bridge
  FROM rights.object_visual_reference b
  WHERE b.object_visual_reference_id = p_object_visual_reference_id
    AND b.acceptance_state = 'accepted';
  SELECT * INTO STRICT v_bridge_decision
  FROM rights.object_visual_reference_review_decision d
  WHERE d.object_visual_reference_id = p_object_visual_reference_id
    AND d.outcome = 'accept'
    AND d.evidence_item_id = v_bridge.evidence_item_id
    AND NOT EXISTS (
      SELECT 1
      FROM rights.object_visual_reference_review_decision newer
      WHERE newer.supersedes_decision_id =
        d.object_visual_reference_review_decision_id
    );
  SELECT * INTO STRICT v_reference
  FROM rights.external_visual_reference r
  WHERE r.external_visual_reference_id = v_bridge.external_visual_reference_id;
  SELECT * INTO STRICT v_object
  FROM core.archive_object o
  WHERE o.archive_object_id = v_bridge.archive_object_id;
  SELECT * INTO STRICT v_delivery
  FROM rights.delivery_assessment d
  WHERE d.delivery_assessment_id = p_delivery_assessment_id
    AND d.object_visual_reference_id = p_object_visual_reference_id
    AND NOT EXISTS (
      SELECT 1 FROM rights.delivery_assessment newer
      WHERE newer.supersedes_delivery_assessment_id = d.delivery_assessment_id);
  v_machine_reason := rights.machine_reason_for_rule(v_delivery.reason_code);
  IF v_delivery.machine_reason_code IS DISTINCT FROM v_machine_reason THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'DELIVERY_RULE_MACHINE_REASON_MISMATCH';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM release.research_release_object ro
    WHERE ro.research_release_id = v_registry.compatible_research_release_id
      AND ro.archive_object_id = v_bridge.archive_object_id
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'VISUAL_OBJECT_NOT_IN_COMPATIBLE_RESEARCH_RELEASE';
  END IF;

  IF v_reference.provider_object_id IS NOT NULL THEN
    SELECT * INTO STRICT v_provider_object
    FROM rights.provider_object po
    WHERE po.provider_object_id = v_reference.provider_object_id;
    SELECT * INTO STRICT v_provider
    FROM rights.provider p
    WHERE p.provider_id = v_provider_object.provider_id;
    INSERT INTO release.visual_registry_provider_snapshot (
      visual_registry_release_id, provider_id, provider_code,
      display_name, provider_snapshot_sha256
    ) VALUES (
      p_registry_id, v_provider.provider_id, v_provider.provider_code,
      v_provider.display_name,
      release.canonical_jsonb_sha256(jsonb_build_array(
        v_provider.provider_id, v_provider.provider_code,
        v_provider.display_name))
    ) ON CONFLICT DO NOTHING;
    INSERT INTO release.visual_registry_provider_object_snapshot (
      visual_registry_release_id, provider_object_id, provider_id,
      provider_record_key, provider_object_snapshot_sha256
    ) VALUES (
      p_registry_id, v_provider_object.provider_object_id,
      v_provider_object.provider_id, v_provider_object.provider_record_key,
      release.canonical_jsonb_sha256(jsonb_build_array(
        v_provider_object.provider_object_id, v_provider_object.provider_id,
        v_provider_object.provider_record_key))
    ) ON CONFLICT DO NOTHING;
  END IF;

  INSERT INTO release.visual_registry_reference_snapshot (
    visual_registry_release_id, external_visual_reference_id,
    visual_reference_urn, provider_object_id, reference_fingerprint,
    reference_snapshot_sha256
  ) VALUES (
    p_registry_id, v_reference.external_visual_reference_id,
    v_reference.visual_reference_urn, v_reference.provider_object_id,
    v_reference.reference_fingerprint,
    release.canonical_jsonb_sha256(jsonb_build_array(
      v_reference.external_visual_reference_id,
      v_reference.visual_reference_urn, v_reference.provider_object_id,
      v_reference.reference_fingerprint))
  ) ON CONFLICT DO NOTHING;

  INSERT INTO release.visual_registry_bridge_snapshot (
    visual_registry_release_id, compatible_research_release_id,
    compatible_research_manifest_sha256, object_visual_reference_id,
    archive_object_id, external_visual_reference_id, reference_role,
    bridge_snapshot_sha256, acceptance_state, evidence_item_id,
    bridge_review_decision_id, evidence_snapshot_sha256,
    decision_snapshot_sha256
  ) VALUES (
    p_registry_id, v_registry.compatible_research_release_id,
    v_registry.compatible_research_manifest_sha256,
    v_bridge.object_visual_reference_id, v_bridge.archive_object_id,
    v_bridge.external_visual_reference_id, v_bridge.reference_role,
    rights.object_visual_reference_snapshot_sha(
      v_bridge.object_visual_reference_id,
      v_registry.compatible_research_release_id,
      v_registry.compatible_research_manifest_sha256),
    v_bridge.acceptance_state, v_bridge.evidence_item_id,
    v_bridge_decision.object_visual_reference_review_decision_id,
    rights.object_visual_reference_evidence_sha(v_bridge.evidence_item_id),
    rights.object_visual_reference_decision_sha(
      v_bridge_decision.object_visual_reference_review_decision_id)
  ) ON CONFLICT DO NOTHING;

  INSERT INTO release.visual_registry_rights_assessment_snapshot (
    visual_registry_release_id, rights_assessment_id,
    assessed_state, assessed_at, assessment_snapshot_sha256
  )
  SELECT p_registry_id, a.rights_assessment_id, a.assessed_state,
    a.assessed_at, rights.compute_rights_assessment_sha(a.rights_assessment_id)
  FROM rights.delivery_rights_assessment x
  JOIN rights.rights_assessment a
    ON a.rights_assessment_id = x.rights_assessment_id
  WHERE x.delivery_assessment_id = p_delivery_assessment_id
  ON CONFLICT DO NOTHING;

  INSERT INTO release.visual_registry_rights_observation_snapshot (
    visual_registry_release_id, rights_assessment_id,
    rights_observation_id, evidence_role, evidence_state,
    evidence_item_id, observed_at, observation_snapshot_sha256
  )
  SELECT p_registry_id, x.rights_assessment_id, o.rights_observation_id,
    x.evidence_role, o.evidence_state, o.evidence_item_id, o.observed_at,
    rights.compute_rights_observation_sha(o.rights_observation_id)
  FROM rights.delivery_rights_assessment d
  JOIN rights.rights_assessment_observation x
    ON x.rights_assessment_id = d.rights_assessment_id
  JOIN rights.rights_observation o
    ON o.rights_observation_id = x.rights_observation_id
  WHERE d.delivery_assessment_id = p_delivery_assessment_id
  ON CONFLICT DO NOTHING;

  INSERT INTO release.visual_registry_policy_evaluation_snapshot (
    visual_registry_release_id, provider_policy_evaluation_id,
    object_visual_reference_id, evaluated_state, evaluated_at,
    evaluation_snapshot_sha256
  )
  SELECT p_registry_id, e.provider_policy_evaluation_id,
    e.object_visual_reference_id, e.evaluated_state, e.evaluated_at,
    rights.compute_provider_policy_evaluation_sha(
      e.provider_policy_evaluation_id)
  FROM rights.delivery_policy_evaluation x
  JOIN rights.provider_policy_evaluation e
    ON e.provider_policy_evaluation_id = x.provider_policy_evaluation_id
  WHERE x.delivery_assessment_id = p_delivery_assessment_id
  ON CONFLICT DO NOTHING;

  INSERT INTO release.visual_registry_policy_version_snapshot (
    visual_registry_release_id, provider_policy_version_id,
    provider_id, version_token, policy_sha256, policy_state,
    source_evidence_item_id, effective_from, effective_until,
    review_due, policy_scope_id
  )
  SELECT p_registry_id, p.provider_policy_version_id, p.provider_id,
    p.version_token, p.policy_sha256, p.policy_state,
    p.source_evidence_item_id, p.effective_from, p.effective_until,
    p.review_due, p.policy_scope_id
  FROM rights.delivery_policy_evaluation d
  JOIN rights.provider_policy_evaluation_version x
    ON x.provider_policy_evaluation_id = d.provider_policy_evaluation_id
  JOIN rights.provider_policy_version p
    ON p.provider_policy_version_id = x.provider_policy_version_id
  WHERE d.delivery_assessment_id = p_delivery_assessment_id
  ON CONFLICT DO NOTHING;

  INSERT INTO release.visual_registry_policy_evaluation_version_snapshot (
    visual_registry_release_id, provider_policy_evaluation_id,
    provider_policy_version_id
  )
  SELECT p_registry_id, d.provider_policy_evaluation_id,
    x.provider_policy_version_id
  FROM rights.delivery_policy_evaluation d
  JOIN rights.provider_policy_evaluation_version x
    ON x.provider_policy_evaluation_id = d.provider_policy_evaluation_id
  WHERE d.delivery_assessment_id = p_delivery_assessment_id
  ON CONFLICT DO NOTHING;

  INSERT INTO release.visual_registry_delivery_snapshot (
    visual_registry_release_id, delivery_assessment_id,
    object_visual_reference_id, attribution_bundle_id,
    base_delivery_mode, reason_code, assessed_at,
    rights_outcome_sha256, policy_outcome_sha256,
    attribution_bundle_sha256, delivery_snapshot_sha256,
    machine_reason_code
  ) VALUES (
    p_registry_id, v_delivery.delivery_assessment_id,
    v_delivery.object_visual_reference_id, v_delivery.attribution_bundle_id,
    v_delivery.delivery_mode, v_delivery.reason_code, v_delivery.assessed_at,
    rights.compute_delivery_rights_sha(v_delivery.delivery_assessment_id),
    rights.compute_delivery_policy_sha(v_delivery.delivery_assessment_id),
    CASE WHEN v_delivery.attribution_bundle_id IS NULL THEN NULL ELSE
      rights.compute_attribution_bundle_sha(
        v_delivery.attribution_bundle_id) END,
    rights.compute_delivery_snapshot_sha(v_delivery.delivery_assessment_id),
    v_machine_reason
  );

  INSERT INTO release.visual_registry_delivery_rights_snapshot
  SELECT p_registry_id, p_delivery_assessment_id,
    x.rights_assessment_id, x.evidence_role
  FROM rights.delivery_rights_assessment x
  WHERE x.delivery_assessment_id = p_delivery_assessment_id;
  INSERT INTO release.visual_registry_delivery_policy_snapshot
  SELECT p_registry_id, p_delivery_assessment_id,
    x.provider_policy_evaluation_id
  FROM rights.delivery_policy_evaluation x
  WHERE x.delivery_assessment_id = p_delivery_assessment_id;

  INSERT INTO release.visual_registry_entry (
    visual_registry_release_id, visual_registry_entry_id,
    compatible_research_release_id,
    compatible_research_manifest_sha256,
    object_visual_reference_id, archive_object_id,
    external_visual_reference_id, reference_role,
    delivery_assessment_id, object_urn, visual_reference_urn,
    provider_code, rights_outcome_sha256, policy_outcome_sha256,
    attribution_bundle_sha256, base_delivery_mode, reason_code,
    machine_reason_code
  ) VALUES (
    p_registry_id, p_entry_id,
    v_registry.compatible_research_release_id,
    v_registry.compatible_research_manifest_sha256,
    v_bridge.object_visual_reference_id, v_bridge.archive_object_id,
    v_bridge.external_visual_reference_id, v_bridge.reference_role,
    v_delivery.delivery_assessment_id, v_object.object_urn,
    v_reference.visual_reference_urn, v_provider.provider_code,
    rights.compute_delivery_rights_sha(v_delivery.delivery_assessment_id),
    rights.compute_delivery_policy_sha(v_delivery.delivery_assessment_id),
    CASE WHEN v_delivery.attribution_bundle_id IS NULL THEN NULL ELSE
      rights.compute_attribution_bundle_sha(
        v_delivery.attribution_bundle_id) END,
    v_delivery.delivery_mode, v_delivery.reason_code, v_machine_reason
  );

  INSERT INTO release.visual_registry_attribution_value
  SELECT p_registry_id, p_entry_id, a.value_kind, a.value_ordinal,
    a.language_tag, a.value_text
  FROM rights.attribution_bundle_value a
  WHERE a.attribution_bundle_id = v_delivery.attribution_bundle_id;

  INSERT INTO release.visual_registry_public_locator
  SELECT p_registry_id, p_entry_id, l.visual_locator_id,
    q.allowlisted_role,
    row_number() OVER (
      PARTITION BY q.allowlisted_role ORDER BY l.visual_locator_id)::integer - 1,
    l.raw_locator, l.locator_fingerprint,
    h.endpoint_health_observation_id, h.health_state, h.method_version,
    h.checked_at, h.valid_until,
    rights.compute_health_observation_sha(h.endpoint_health_observation_id)
  FROM rights.delivery_locator_qualification q
  JOIN rights.visual_locator l ON l.visual_locator_id = q.visual_locator_id
  JOIN rights.endpoint_health_observation h
    ON h.endpoint_health_observation_id = q.endpoint_health_observation_id
  WHERE q.delivery_assessment_id = p_delivery_assessment_id
    AND l.visibility = 'public_candidate'
    AND h.health_state = 'healthy_fresh'
    AND h.checked_at <= clock_timestamp()
    AND h.valid_until > clock_timestamp()
    AND q.allowlisted_role IN (
      'canonical_record', 'source_viewer', 'direct_image')
    AND ((v_delivery.delivery_mode = 'link_only'
          AND q.allowlisted_role = 'canonical_record')
      OR (v_delivery.delivery_mode = 'source_viewer'
          AND q.allowlisted_role IN ('canonical_record', 'source_viewer'))
      OR (v_delivery.delivery_mode = 'remote_image'
          AND q.allowlisted_role IN ('canonical_record', 'direct_image')));

  INSERT INTO release.visual_registry_takedown_snapshot
  SELECT p_registry_id, p_entry_id, o.takedown_override_id,
    o.restrictive_mode, o.overlay_sha256, te.effective_from,
    te.effective_until, clock_timestamp()
  FROM rights.takedown_scope s
  JOIN rights.takedown_event te ON te.takedown_event_id = s.takedown_event_id
  JOIN rights.takedown_override o ON o.takedown_scope_id = s.takedown_scope_id
  WHERE rights.scope_matches_bridge(
      s.takedown_scope_id, p_object_visual_reference_id)
    AND NOT EXISTS (
      SELECT 1 FROM rights.takedown_override newer
      WHERE newer.supersedes_takedown_override_id = o.takedown_override_id)
  ON CONFLICT DO NOTHING;
END
$function$;

RESET ROLE;
