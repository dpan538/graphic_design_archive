\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

CREATE FUNCTION release.add_research_object_to_draft(
  p_release_id uuid, p_corpus_version_id uuid, p_archive_object_id uuid
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE
  v_membership research.corpus_membership%ROWTYPE;
  v_object core.archive_object%ROWTYPE;
  v_surface_id text;
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM 1 FROM release.research_release r
  WHERE r.research_release_id = p_release_id AND r.release_state = 'draft'
  FOR SHARE;
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RESEARCH_DRAFT_REQUIRED';
  END IF;
  SELECT * INTO STRICT v_membership FROM research.corpus_membership m
  WHERE m.corpus_version_id = p_corpus_version_id
    AND m.archive_object_id = p_archive_object_id;
  SELECT * INTO STRICT v_object FROM core.archive_object o
  WHERE o.archive_object_id = p_archive_object_id;
  SELECT min(l.surface_id) INTO v_surface_id
  FROM raw.legacy_surface_ledger l
  WHERE l.archive_object_id = p_archive_object_id;
  INSERT INTO release.research_release_object (
    research_release_id, archive_object_id, object_urn,
    legacy_surface_id, title, publication_layer,
    acceptance_state, workflow_state
  ) VALUES (
    p_release_id, p_archive_object_id, v_object.object_urn,
    v_surface_id, v_object.preferred_label,
    CASE v_membership.disposition WHEN 'eligible'
      THEN 'active'::release.publication_layer
      ELSE 'excluded'::release.publication_layer END,
    CASE v_membership.disposition
      WHEN 'eligible' THEN 'accepted'::provenance.assertion_status
      WHEN 'held' THEN 'proposed'::provenance.assertion_status
      ELSE 'rejected'::provenance.assertion_status END,
    CASE v_membership.disposition WHEN 'held'
      THEN 'queued'::workflow.queue_state
      ELSE 'resolved'::workflow.queue_state END
  );
  INSERT INTO release.research_release_corpus_member VALUES (
    p_release_id, p_corpus_version_id, p_archive_object_id,
    v_membership.disposition, v_membership.reason_code);
END
$function$;

CREATE FUNCTION release.add_research_claim_to_draft(
  p_release_id uuid, p_claim_revision_id uuid
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM 1 FROM release.research_release r
  WHERE r.research_release_id = p_release_id AND r.release_state = 'draft'
  FOR SHARE;
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RESEARCH_DRAFT_REQUIRED';
  END IF;
  INSERT INTO release.research_release_claim (
    research_release_id, claim_id, claim_revision_id,
    claim_urn, epistemic_code, wording
  )
  SELECT p_release_id, c.claim_id, cr.claim_revision_id,
    c.claim_urn, e.class_code, cr.wording
  FROM research.claim_revision cr
  JOIN research.claim c ON c.claim_id = cr.claim_id
  JOIN research.epistemic_class e
    ON e.epistemic_class_id = cr.epistemic_class_id
  WHERE cr.claim_revision_id = p_claim_revision_id
    AND cr.status = 'accepted' AND cr.workflow_state = 'resolved'
    AND e.active;
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'ONLY_ACCEPTED_RESOLVED_CLAIM_CAN_BE_COPIED';
  END IF;
END
$function$;

CREATE FUNCTION release.add_research_relation_to_draft(
  p_release_id uuid, p_semantic_relation_id uuid,
  p_supporting_claim_revision_id uuid
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM 1 FROM release.research_release r
  WHERE r.research_release_id = p_release_id AND r.release_state = 'draft'
  FOR SHARE;
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RESEARCH_DRAFT_REQUIRED';
  END IF;
  IF p_supporting_claim_revision_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM release.research_release_claim c
    WHERE c.research_release_id = p_release_id
      AND c.claim_revision_id = p_supporting_claim_revision_id
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'SUPPORTING_CLAIM_MUST_BE_COPIED_FIRST';
  END IF;
  INSERT INTO release.research_release_relation (
    research_release_id, semantic_relation_id, relation_urn,
    relation_code, subject_entity_id, object_entity_id,
    acceptance_basis, supporting_claim_revision_id,
    supporting_decision_id, epistemic_code
  )
  SELECT p_release_id, sr.semantic_relation_id, sr.relation_urn,
    rt.relation_code, se.entity_id, oe.entity_id,
    'accepted_claim'::research.relation_acceptance_basis,
    cr.claim_revision_id, NULL::uuid, ec.class_code
  FROM research.semantic_relation sr
  JOIN research.relation_type rt ON rt.relation_type_id = sr.relation_type_id
  JOIN research.relation_endpoint_entity se
    ON se.relation_endpoint_id = sr.subject_endpoint_id
  JOIN research.relation_endpoint_entity oe
    ON oe.relation_endpoint_id = sr.object_endpoint_id
  JOIN research.relation_claim rc
    ON rc.semantic_relation_id = sr.semantic_relation_id
    AND rc.claim_revision_id = p_supporting_claim_revision_id
    AND rc.claim_role = 'supports'
  JOIN research.claim_revision cr
    ON cr.claim_revision_id = rc.claim_revision_id AND cr.status = 'accepted'
  JOIN research.epistemic_class ec
    ON ec.epistemic_class_id = cr.epistemic_class_id AND ec.active
  WHERE p_supporting_claim_revision_id IS NOT NULL
    AND sr.semantic_relation_id = p_semantic_relation_id
    AND sr.status = 'accepted' AND sr.origin <> 'legacy_projection_only'
    AND rt.active
  UNION ALL
  SELECT p_release_id, sr.semantic_relation_id, sr.relation_urn,
    rt.relation_code, se.entity_id, oe.entity_id,
    'curator_decision'::research.relation_acceptance_basis,
    NULL::uuid, d.relation_review_decision_id, NULL::text
  FROM research.semantic_relation sr
  JOIN research.relation_type rt ON rt.relation_type_id = sr.relation_type_id
  JOIN research.relation_endpoint_entity se
    ON se.relation_endpoint_id = sr.subject_endpoint_id
  JOIN research.relation_endpoint_entity oe
    ON oe.relation_endpoint_id = sr.object_endpoint_id
  JOIN research.relation_review_decision d
    ON d.semantic_relation_id = sr.semantic_relation_id
    AND d.outcome = 'accept'
    AND NOT EXISTS (
      SELECT 1 FROM research.relation_review_decision newer
      WHERE newer.supersedes_decision_id = d.relation_review_decision_id)
    AND EXISTS (
      SELECT 1 FROM research.relation_decision_evidence de
      WHERE de.relation_review_decision_id = d.relation_review_decision_id
        AND de.evidence_role = 'supports')
  WHERE p_supporting_claim_revision_id IS NULL
    AND sr.semantic_relation_id = p_semantic_relation_id
    AND sr.status = 'accepted' AND sr.origin <> 'legacy_projection_only'
    AND rt.active;
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'ONLY_ACCEPTED_TYPED_EVIDENCE_BOUND_RELATION_CAN_BE_COPIED';
  END IF;
END
$function$;

CREATE FUNCTION release.add_trace_node_to_draft(
  p_release_id uuid, p_corpus_version_id uuid,
  p_trace_node_id uuid, p_archive_object_id uuid
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM 1 FROM release.research_release r
  WHERE r.research_release_id = p_release_id AND r.release_state = 'draft'
  FOR SHARE;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RESEARCH_DRAFT_REQUIRED'; END IF;
  INSERT INTO release.trace_projection_node (
    research_release_id, corpus_version_id, trace_node_id,
    archive_object_id, canonical_key, label
  )
  SELECT p_release_id, p_corpus_version_id, n.trace_node_id,
    p_archive_object_id, n.canonical_key, n.label
  FROM research.trace_node n
  WHERE n.trace_node_id = p_trace_node_id
    AND (p_archive_object_id IS NULL OR EXISTS (
      SELECT 1 FROM research.object_trace_node x
      WHERE x.trace_node_id = n.trace_node_id
        AND x.archive_object_id = p_archive_object_id));
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'TRACE_NODE_COPY_SOURCE_MISMATCH'; END IF;
END
$function$;

CREATE FUNCTION release.add_trace_edge_to_draft(
  p_release_id uuid, p_corpus_version_id uuid,
  p_subject_trace_node_id uuid, p_semantic_relation_id uuid,
  p_object_trace_node_id uuid, p_projection_role text
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  INSERT INTO release.trace_projection_edge VALUES (
    p_release_id, p_corpus_version_id, p_subject_trace_node_id,
    p_semantic_relation_id, p_object_trace_node_id, p_projection_role,
    release.trace_edge_generation_key(
      p_release_id, p_corpus_version_id, p_subject_trace_node_id,
      p_semantic_relation_id, p_object_trace_node_id, p_projection_role)
  );
END
$function$;

CREATE FUNCTION release.copy_visual_entry_to_draft(
  p_registry_id uuid, p_entry_id uuid,
  p_object_visual_reference_id uuid, p_delivery_assessment_id uuid
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE
  v_registry release.visual_registry_release%ROWTYPE;
  v_bridge rights.object_visual_reference%ROWTYPE;
  v_reference rights.external_visual_reference%ROWTYPE;
  v_object core.archive_object%ROWTYPE;
  v_delivery rights.delivery_assessment%ROWTYPE;
  v_provider_object rights.provider_object%ROWTYPE;
  v_provider rights.provider%ROWTYPE;
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  SELECT * INTO STRICT v_registry FROM release.visual_registry_release r
  WHERE r.visual_registry_release_id = p_registry_id
    AND r.release_state = 'draft' FOR SHARE;
  SELECT * INTO STRICT v_bridge FROM rights.object_visual_reference b
  WHERE b.object_visual_reference_id = p_object_visual_reference_id
    AND b.acceptance_state = 'accepted';
  SELECT * INTO STRICT v_reference FROM rights.external_visual_reference r
  WHERE r.external_visual_reference_id = v_bridge.external_visual_reference_id;
  SELECT * INTO STRICT v_object FROM core.archive_object o
  WHERE o.archive_object_id = v_bridge.archive_object_id;
  SELECT * INTO STRICT v_delivery FROM rights.delivery_assessment d
  WHERE d.delivery_assessment_id = p_delivery_assessment_id
    AND d.object_visual_reference_id = p_object_visual_reference_id
    AND NOT EXISTS (SELECT 1 FROM rights.delivery_assessment newer
      WHERE newer.supersedes_delivery_assessment_id = d.delivery_assessment_id);
  IF NOT EXISTS (
    SELECT 1 FROM release.research_release_object ro
    WHERE ro.research_release_id = v_registry.compatible_research_release_id
      AND ro.archive_object_id = v_bridge.archive_object_id
  ) THEN RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'VISUAL_OBJECT_NOT_IN_COMPATIBLE_RESEARCH_RELEASE'; END IF;

  IF v_reference.provider_object_id IS NOT NULL THEN
    SELECT * INTO STRICT v_provider_object FROM rights.provider_object po
    WHERE po.provider_object_id = v_reference.provider_object_id;
    SELECT * INTO STRICT v_provider FROM rights.provider p
    WHERE p.provider_id = v_provider_object.provider_id;
    INSERT INTO release.visual_registry_provider_snapshot VALUES (
      p_registry_id, v_provider.provider_id, v_provider.provider_code,
      v_provider.display_name,
      release.canonical_jsonb_sha256(jsonb_build_array(
        v_provider.provider_id, v_provider.provider_code, v_provider.display_name))
    ) ON CONFLICT DO NOTHING;
    INSERT INTO release.visual_registry_provider_object_snapshot VALUES (
      p_registry_id, v_provider_object.provider_object_id,
      v_provider_object.provider_id, v_provider_object.provider_record_key,
      release.canonical_jsonb_sha256(jsonb_build_array(
        v_provider_object.provider_object_id, v_provider_object.provider_id,
        v_provider_object.provider_record_key))
    ) ON CONFLICT DO NOTHING;
  END IF;
  INSERT INTO release.visual_registry_reference_snapshot VALUES (
    p_registry_id, v_reference.external_visual_reference_id,
    v_reference.visual_reference_urn, v_reference.provider_object_id,
    v_reference.reference_fingerprint,
    release.canonical_jsonb_sha256(jsonb_build_array(
      v_reference.external_visual_reference_id, v_reference.visual_reference_urn,
      v_reference.provider_object_id, v_reference.reference_fingerprint))
  ) ON CONFLICT DO NOTHING;
  INSERT INTO release.visual_registry_bridge_snapshot VALUES (
    p_registry_id, v_registry.compatible_research_release_id,
    v_registry.compatible_research_manifest_sha256,
    v_bridge.object_visual_reference_id, v_bridge.archive_object_id,
    v_bridge.external_visual_reference_id, v_bridge.reference_role,
    release.canonical_jsonb_sha256(jsonb_build_array(
      v_bridge.object_visual_reference_id,
      v_registry.compatible_research_release_id,
      v_registry.compatible_research_manifest_sha256,
      v_bridge.archive_object_id, v_bridge.external_visual_reference_id,
      v_bridge.reference_role))
  ) ON CONFLICT DO NOTHING;

  INSERT INTO release.visual_registry_rights_assessment_snapshot
  SELECT p_registry_id, a.rights_assessment_id, a.assessed_state,
    a.assessed_at, rights.compute_rights_assessment_sha(a.rights_assessment_id)
  FROM rights.delivery_rights_assessment x
  JOIN rights.rights_assessment a ON a.rights_assessment_id = x.rights_assessment_id
  WHERE x.delivery_assessment_id = p_delivery_assessment_id
  ON CONFLICT DO NOTHING;
  INSERT INTO release.visual_registry_rights_observation_snapshot
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

  INSERT INTO release.visual_registry_policy_evaluation_snapshot
  SELECT p_registry_id, e.provider_policy_evaluation_id,
    e.object_visual_reference_id, e.evaluated_state, e.evaluated_at,
    rights.compute_provider_policy_evaluation_sha(e.provider_policy_evaluation_id)
  FROM rights.delivery_policy_evaluation x
  JOIN rights.provider_policy_evaluation e
    ON e.provider_policy_evaluation_id = x.provider_policy_evaluation_id
  WHERE x.delivery_assessment_id = p_delivery_assessment_id
  ON CONFLICT DO NOTHING;
  INSERT INTO release.visual_registry_policy_version_snapshot
  SELECT p_registry_id, p.provider_policy_version_id, p.provider_id,
    p.version_token, p.policy_sha256, p.policy_state,
    p.source_evidence_item_id, p.effective_from, p.effective_until,
    p.review_due
  FROM rights.delivery_policy_evaluation d
  JOIN rights.provider_policy_evaluation_version x
    ON x.provider_policy_evaluation_id = d.provider_policy_evaluation_id
  JOIN rights.provider_policy_version p
    ON p.provider_policy_version_id = x.provider_policy_version_id
  WHERE d.delivery_assessment_id = p_delivery_assessment_id
  ON CONFLICT DO NOTHING;
  INSERT INTO release.visual_registry_policy_evaluation_version_snapshot
  SELECT p_registry_id, d.provider_policy_evaluation_id,
    x.provider_policy_version_id
  FROM rights.delivery_policy_evaluation d
  JOIN rights.provider_policy_evaluation_version x
    ON x.provider_policy_evaluation_id = d.provider_policy_evaluation_id
  WHERE d.delivery_assessment_id = p_delivery_assessment_id
  ON CONFLICT DO NOTHING;

  INSERT INTO release.visual_registry_delivery_snapshot VALUES (
    p_registry_id, v_delivery.delivery_assessment_id,
    v_delivery.object_visual_reference_id, v_delivery.attribution_bundle_id,
    v_delivery.delivery_mode, v_delivery.reason_code, v_delivery.assessed_at,
    rights.compute_delivery_rights_sha(v_delivery.delivery_assessment_id),
    rights.compute_delivery_policy_sha(v_delivery.delivery_assessment_id),
    CASE WHEN v_delivery.attribution_bundle_id IS NULL THEN NULL ELSE
      rights.compute_attribution_bundle_sha(v_delivery.attribution_bundle_id) END,
    rights.compute_delivery_snapshot_sha(v_delivery.delivery_assessment_id)
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
    compatible_research_release_id, compatible_research_manifest_sha256,
    object_visual_reference_id, archive_object_id,
    external_visual_reference_id, reference_role,
    delivery_assessment_id, object_urn, visual_reference_urn,
    provider_code, rights_outcome_sha256, policy_outcome_sha256,
    attribution_bundle_sha256, base_delivery_mode, reason_code
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
      rights.compute_attribution_bundle_sha(v_delivery.attribution_bundle_id) END,
    v_delivery.delivery_mode, v_delivery.reason_code
  );
  INSERT INTO release.visual_registry_attribution_value
  SELECT p_registry_id, p_entry_id, a.value_kind, a.value_ordinal,
    a.language_tag, a.value_text
  FROM rights.attribution_bundle_value a
  WHERE a.attribution_bundle_id = v_delivery.attribution_bundle_id;
  INSERT INTO release.visual_registry_public_locator
  SELECT p_registry_id, p_entry_id, l.visual_locator_id,
    q.allowlisted_role,
    row_number() OVER (PARTITION BY q.allowlisted_role
      ORDER BY l.visual_locator_id)::integer - 1,
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
    AND q.allowlisted_role IN ('canonical_record', 'source_viewer', 'direct_image')
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
  WHERE rights.scope_matches_bridge(s.takedown_scope_id,
      p_object_visual_reference_id)
    AND NOT EXISTS (SELECT 1 FROM rights.takedown_override newer
      WHERE newer.supersedes_takedown_override_id = o.takedown_override_id)
  ON CONFLICT DO NOTHING;
END
$function$;

RESET ROLE;
