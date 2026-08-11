\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

CREATE FUNCTION release.require_session_actor(p_expected text)
RETURNS void
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  IF session_user::text <> p_expected THEN
    RAISE EXCEPTION USING ERRCODE = '42501',
      MESSAGE = 'ROLE_NOT_AUTHORIZED_FOR_CONTROLLED_FUNCTION';
  END IF;
END
$function$;

CREATE FUNCTION release.compute_research_candidate_fingerprint(p_release_id uuid)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
RETURN encode(sha256(convert_to(jsonb_build_object(
  'format', 'gda-v49-research-candidate-jsonb-v1',
  'releaseId', p_release_id,
  'objects', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    o.archive_object_id, o.object_urn, o.legacy_surface_id, o.title,
    o.publication_layer, o.acceptance_state, o.workflow_state
  ) ORDER BY o.archive_object_id) FROM release.research_release_object o
    WHERE o.research_release_id = p_release_id), '[]'::jsonb),
  'corpus', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    c.corpus_version_id, c.archive_object_id, c.disposition, c.reason_code
  ) ORDER BY c.corpus_version_id, c.archive_object_id)
    FROM release.research_release_corpus_member c
    WHERE c.research_release_id = p_release_id), '[]'::jsonb),
  'claims', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    c.claim_id, c.claim_revision_id, c.claim_urn, c.epistemic_code, c.wording
  ) ORDER BY c.claim_id) FROM release.research_release_claim c
    WHERE c.research_release_id = p_release_id), '[]'::jsonb),
  'relations', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    r.semantic_relation_id, r.relation_urn, r.relation_code,
    r.subject_entity_id, r.object_entity_id, r.acceptance_basis,
    r.supporting_claim_revision_id, r.supporting_decision_id,
    r.epistemic_code
  ) ORDER BY r.semantic_relation_id) FROM release.research_release_relation r
    WHERE r.research_release_id = p_release_id), '[]'::jsonb),
  'nodes', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    n.corpus_version_id, n.trace_node_id, n.archive_object_id,
    n.canonical_key, n.label
  ) ORDER BY n.corpus_version_id, n.trace_node_id)
    FROM release.trace_projection_node n
    WHERE n.research_release_id = p_release_id), '[]'::jsonb),
  'edges', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    e.corpus_version_id, e.subject_trace_node_id, e.semantic_relation_id,
    e.object_trace_node_id, e.projection_role, e.generation_key
  ) ORDER BY e.corpus_version_id, e.subject_trace_node_id,
      e.semantic_relation_id, e.object_trace_node_id, e.projection_role)
    FROM release.trace_projection_edge e
    WHERE e.research_release_id = p_release_id), '[]'::jsonb),
  'memberships', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    m.corpus_version_id, m.archive_object_id, m.semantic_relation_id,
    m.membership_role, m.publication_layer, m.metric_code,
    m.count_eligibility, m.eligibility_reason_code
  ) ORDER BY m.corpus_version_id, m.archive_object_id,
      m.semantic_relation_id, m.membership_role, m.metric_code)
    FROM release.object_relation_membership_projection m
    WHERE m.research_release_id = p_release_id), '[]'::jsonb),
  'metrics', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    m.archive_object_id, m.metric_code, m.count_eligibility, m.reason_code
  ) ORDER BY m.archive_object_id, m.metric_code)
    FROM release.research_object_metric_eligibility m
    WHERE m.research_release_id = p_release_id), '[]'::jsonb)
)::text, 'UTF8')), 'hex')::core.sha256_hex;

CREATE FUNCTION release.compute_visual_candidate_fingerprint(p_registry_id uuid)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
RETURN encode(sha256(convert_to(jsonb_build_object(
  'format', 'gda-v49-visual-candidate-jsonb-v1',
  'registryId', p_registry_id,
  'providers', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    p.provider_id, p.provider_code, p.display_name, p.provider_snapshot_sha256
  ) ORDER BY p.provider_id) FROM release.visual_registry_provider_snapshot p
    WHERE p.visual_registry_release_id = p_registry_id), '[]'::jsonb),
  'providerObjects', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    p.provider_object_id, p.provider_id, p.provider_record_key,
    p.provider_object_snapshot_sha256
  ) ORDER BY p.provider_object_id)
    FROM release.visual_registry_provider_object_snapshot p
    WHERE p.visual_registry_release_id = p_registry_id), '[]'::jsonb),
  'references', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    r.external_visual_reference_id, r.visual_reference_urn,
    r.provider_object_id, r.reference_fingerprint, r.reference_snapshot_sha256
  ) ORDER BY r.external_visual_reference_id)
    FROM release.visual_registry_reference_snapshot r
    WHERE r.visual_registry_release_id = p_registry_id), '[]'::jsonb),
  'bridges', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    b.object_visual_reference_id, b.archive_object_id,
    b.external_visual_reference_id, b.reference_role, b.bridge_snapshot_sha256
  ) ORDER BY b.object_visual_reference_id)
    FROM release.visual_registry_bridge_snapshot b
    WHERE b.visual_registry_release_id = p_registry_id), '[]'::jsonb),
  'rights', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    s.rights_assessment_id, s.assessed_state,
    (extract(epoch FROM s.assessed_at) * 1000000)::bigint,
    s.assessment_snapshot_sha256
  ) ORDER BY s.rights_assessment_id)
    FROM release.visual_registry_rights_assessment_snapshot s
    WHERE s.visual_registry_release_id = p_registry_id), '[]'::jsonb),
  'rightsObservations', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    s.rights_assessment_id, s.rights_observation_id, s.evidence_role,
    s.evidence_state, s.evidence_item_id,
    (extract(epoch FROM s.observed_at) * 1000000)::bigint,
    s.observation_snapshot_sha256
  ) ORDER BY s.rights_assessment_id, s.rights_observation_id, s.evidence_role)
    FROM release.visual_registry_rights_observation_snapshot s
    WHERE s.visual_registry_release_id = p_registry_id), '[]'::jsonb),
  'policyVersions', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    s.provider_policy_version_id, s.provider_id, s.version_token,
    s.policy_sha256, s.policy_state, s.source_evidence_item_id,
    (extract(epoch FROM s.effective_from) * 1000000)::bigint,
    CASE WHEN s.effective_until IS NULL THEN NULL
      ELSE (extract(epoch FROM s.effective_until) * 1000000)::bigint END,
    (extract(epoch FROM s.review_due) * 1000000)::bigint
  ) ORDER BY s.provider_policy_version_id)
    FROM release.visual_registry_policy_version_snapshot s
    WHERE s.visual_registry_release_id = p_registry_id), '[]'::jsonb),
  'policyEvaluations', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    s.provider_policy_evaluation_id, s.object_visual_reference_id,
    s.evaluated_state,
    (extract(epoch FROM s.evaluated_at) * 1000000)::bigint,
    s.evaluation_snapshot_sha256
  ) ORDER BY s.provider_policy_evaluation_id)
    FROM release.visual_registry_policy_evaluation_snapshot s
    WHERE s.visual_registry_release_id = p_registry_id), '[]'::jsonb),
  'policyLinks', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    s.provider_policy_evaluation_id, s.provider_policy_version_id
  ) ORDER BY s.provider_policy_evaluation_id, s.provider_policy_version_id)
    FROM release.visual_registry_policy_evaluation_version_snapshot s
    WHERE s.visual_registry_release_id = p_registry_id), '[]'::jsonb),
  'deliveries', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    s.delivery_assessment_id, s.object_visual_reference_id,
    s.attribution_bundle_id, s.base_delivery_mode, s.reason_code,
    (extract(epoch FROM s.assessed_at) * 1000000)::bigint,
    s.rights_outcome_sha256, s.policy_outcome_sha256,
    s.attribution_bundle_sha256, s.delivery_snapshot_sha256
  ) ORDER BY s.delivery_assessment_id)
    FROM release.visual_registry_delivery_snapshot s
    WHERE s.visual_registry_release_id = p_registry_id), '[]'::jsonb),
  'deliveryRights', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    s.delivery_assessment_id, s.rights_assessment_id, s.evidence_role
  ) ORDER BY s.delivery_assessment_id, s.rights_assessment_id, s.evidence_role)
    FROM release.visual_registry_delivery_rights_snapshot s
    WHERE s.visual_registry_release_id = p_registry_id), '[]'::jsonb),
  'deliveryPolicies', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    s.delivery_assessment_id, s.provider_policy_evaluation_id
  ) ORDER BY s.delivery_assessment_id, s.provider_policy_evaluation_id)
    FROM release.visual_registry_delivery_policy_snapshot s
    WHERE s.visual_registry_release_id = p_registry_id), '[]'::jsonb),
  'entries', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    e.visual_registry_entry_id, e.object_visual_reference_id,
    e.archive_object_id, e.external_visual_reference_id, e.reference_role,
    e.delivery_assessment_id, e.object_urn, e.visual_reference_urn,
    e.provider_code, e.rights_outcome_sha256, e.policy_outcome_sha256,
    e.attribution_bundle_sha256, e.base_delivery_mode, e.reason_code
  ) ORDER BY e.visual_registry_entry_id)
    FROM release.visual_registry_entry e
    WHERE e.visual_registry_release_id = p_registry_id), '[]'::jsonb),
  'attributionValues', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    a.visual_registry_entry_id, a.value_kind, a.value_ordinal,
    a.language_tag, a.value_text
  ) ORDER BY a.visual_registry_entry_id, a.value_kind, a.value_ordinal)
    FROM release.visual_registry_attribution_value a
    WHERE a.visual_registry_release_id = p_registry_id), '[]'::jsonb),
  'locators', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    l.visual_registry_entry_id, l.visual_locator_id, l.locator_role,
    l.locator_ordinal, l.public_locator, l.locator_sha256,
    l.endpoint_health_observation_id, l.health_state,
    l.health_method_version,
    (extract(epoch FROM l.health_observed_at) * 1000000)::bigint,
    (extract(epoch FROM l.health_valid_until) * 1000000)::bigint,
    l.health_observation_sha256
  ) ORDER BY l.visual_registry_entry_id, l.locator_role, l.locator_ordinal)
    FROM release.visual_registry_public_locator l
    WHERE l.visual_registry_release_id = p_registry_id), '[]'::jsonb),
  'takedowns', COALESCE((SELECT jsonb_agg(jsonb_build_array(
    t.visual_registry_entry_id, t.takedown_override_id,
    t.restrictive_mode, t.overlay_sha256,
    (extract(epoch FROM t.effective_from) * 1000000)::bigint,
    CASE WHEN t.effective_until IS NULL THEN NULL ELSE
      (extract(epoch FROM t.effective_until) * 1000000)::bigint END,
    (extract(epoch FROM t.evaluated_at) * 1000000)::bigint
  ) ORDER BY t.visual_registry_entry_id, t.takedown_override_id)
    FROM release.visual_registry_takedown_snapshot t
    WHERE t.visual_registry_release_id = p_registry_id), '[]'::jsonb)
)::text, 'UTF8')), 'hex')::core.sha256_hex;

CREATE FUNCTION release.validate_research_projection(p_release_id uuid)
RETURNS void
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE v_stored core.sha256_hex; v_computed core.sha256_hex;
BEGIN
  SELECT r.candidate_fingerprint INTO v_stored
  FROM release.research_release r
  WHERE r.research_release_id = p_release_id
    AND r.release_state IN ('candidate', 'validated', 'sealed')
  FOR SHARE;
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RESEARCH_RELEASE_NOT_VALIDATABLE';
  END IF;
  v_computed := release.compute_research_candidate_fingerprint(p_release_id);
  IF v_stored IS DISTINCT FROM v_computed THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'RESEARCH_CANDIDATE_FINGERPRINT_MISMATCH';
  END IF;
  IF EXISTS (
    SELECT 1 FROM release.research_release_object ro
    JOIN core.archive_object o ON o.archive_object_id = ro.archive_object_id
    WHERE ro.research_release_id = p_release_id
      AND ro.object_urn IS DISTINCT FROM o.object_urn
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'RESEARCH_OBJECT_COPY_MISMATCH';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM release.research_release_corpus_member c
    LEFT JOIN research.corpus_membership live
      ON live.corpus_version_id = c.corpus_version_id
      AND live.archive_object_id = c.archive_object_id
    WHERE c.research_release_id = p_release_id
      AND (live.archive_object_id IS NULL
        OR live.disposition IS DISTINCT FROM c.disposition
        OR live.reason_code IS DISTINCT FROM c.reason_code)
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'RESEARCH_CORPUS_COPY_MISMATCH';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM release.research_release_claim rc
    LEFT JOIN research.claim c ON c.claim_id = rc.claim_id
    LEFT JOIN research.claim_revision cr
      ON cr.claim_id = rc.claim_id AND cr.claim_revision_id = rc.claim_revision_id
    LEFT JOIN research.epistemic_class ec ON ec.epistemic_class_id = cr.epistemic_class_id
    WHERE rc.research_release_id = p_release_id
      AND (c.claim_id IS NULL OR cr.status <> 'accepted'
        OR c.claim_urn IS DISTINCT FROM rc.claim_urn
        OR cr.wording IS DISTINCT FROM rc.wording
        OR ec.class_code IS DISTINCT FROM rc.epistemic_code)
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'RESEARCH_CLAIM_COPY_NOT_ACCEPTED_OR_MISMATCHED';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM release.research_release_relation rr
    LEFT JOIN research.semantic_relation sr
      ON sr.semantic_relation_id = rr.semantic_relation_id
    LEFT JOIN research.relation_type rt ON rt.relation_type_id = sr.relation_type_id
    LEFT JOIN research.relation_endpoint_entity se
      ON se.relation_endpoint_id = sr.subject_endpoint_id
    LEFT JOIN research.relation_endpoint_entity oe
      ON oe.relation_endpoint_id = sr.object_endpoint_id
    WHERE rr.research_release_id = p_release_id
      AND (sr.semantic_relation_id IS NULL OR sr.status <> 'accepted'
        OR sr.origin = 'legacy_projection_only' OR NOT rt.active
        OR sr.relation_urn IS DISTINCT FROM rr.relation_urn
        OR rt.relation_code IS DISTINCT FROM rr.relation_code
        OR se.entity_id IS DISTINCT FROM rr.subject_entity_id
        OR oe.entity_id IS DISTINCT FROM rr.object_entity_id
        OR NOT (
          (rr.acceptance_basis = 'accepted_claim'
            AND EXISTS (
              SELECT 1
              FROM research.relation_claim rcl
              JOIN research.claim_revision cr
                ON cr.claim_revision_id = rcl.claim_revision_id
              JOIN research.epistemic_class ec
                ON ec.epistemic_class_id = cr.epistemic_class_id
              JOIN release.research_release_claim copied
                ON copied.research_release_id = rr.research_release_id
                AND copied.claim_revision_id = cr.claim_revision_id
              WHERE rcl.semantic_relation_id = sr.semantic_relation_id
                AND rcl.claim_role = 'supports' AND cr.status = 'accepted'
                AND cr.claim_revision_id = rr.supporting_claim_revision_id
                AND ec.class_code = rr.epistemic_code
            ))
          OR
          (rr.acceptance_basis = 'curator_decision'
            AND EXISTS (
              SELECT 1
              FROM research.relation_review_decision d
              WHERE d.relation_review_decision_id = rr.supporting_decision_id
                AND d.semantic_relation_id = sr.semantic_relation_id
                AND d.outcome = 'accept'
                AND NOT EXISTS (
                  SELECT 1 FROM research.relation_review_decision newer
                  WHERE newer.supersedes_decision_id = d.relation_review_decision_id
                )
                AND EXISTS (
                  SELECT 1 FROM research.relation_decision_evidence de
                  WHERE de.relation_review_decision_id = d.relation_review_decision_id
                    AND de.evidence_role = 'supports'
                )
            ))
        ))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'RESEARCH_RELATION_COPY_NOT_ACCEPTED_OR_MISMATCHED';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM release.trace_projection_node n
    LEFT JOIN research.trace_node tn ON tn.trace_node_id = n.trace_node_id
    WHERE n.research_release_id = p_release_id
      AND (tn.trace_node_id IS NULL
        OR tn.canonical_key IS DISTINCT FROM n.canonical_key
        OR tn.label IS DISTINCT FROM n.label
        OR (n.archive_object_id IS NOT NULL AND NOT EXISTS (
          SELECT 1 FROM research.object_trace_node ot
          WHERE ot.archive_object_id = n.archive_object_id
            AND ot.trace_node_id = n.trace_node_id
        )))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'TRACE_NODE_COPY_OR_OBJECT_BINDING_MISMATCH';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM release.trace_projection_edge e
    JOIN release.trace_projection_node sn
      ON sn.research_release_id = e.research_release_id
      AND sn.corpus_version_id = e.corpus_version_id
      AND sn.trace_node_id = e.subject_trace_node_id
    JOIN release.trace_projection_node onode
      ON onode.research_release_id = e.research_release_id
      AND onode.corpus_version_id = e.corpus_version_id
      AND onode.trace_node_id = e.object_trace_node_id
    JOIN release.research_release_relation rr
      ON rr.research_release_id = e.research_release_id
      AND rr.semantic_relation_id = e.semantic_relation_id
    WHERE e.research_release_id = p_release_id
      AND (sn.archive_object_id IS NULL OR onode.archive_object_id IS NULL
        OR sn.archive_object_id IS DISTINCT FROM rr.subject_entity_id
        OR onode.archive_object_id IS DISTINCT FROM rr.object_entity_id
        OR e.generation_key IS DISTINCT FROM release.trace_edge_generation_key(
          e.research_release_id, e.corpus_version_id,
          e.subject_trace_node_id, e.semantic_relation_id,
          e.object_trace_node_id, e.projection_role))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'TRACE_EDGE_TOPOLOGY_OR_GENERATION_KEY_MISMATCH';
  END IF;
  IF EXISTS (
    SELECT 1 FROM release.object_relation_membership_projection p
    WHERE p.research_release_id = p_release_id
      AND NOT EXISTS (
        SELECT 1 FROM research.object_relation_membership live
        WHERE live.archive_object_id = p.archive_object_id
          AND live.semantic_relation_id = p.semantic_relation_id
          AND live.membership_role = p.membership_role
      )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'TRACE_MEMBERSHIP_COPY_MISMATCH';
  END IF;
END
$function$;

CREATE FUNCTION release.canonical_jsonb_sha256(p_value jsonb)
RETURNS core.sha256_hex
LANGUAGE sql IMMUTABLE
SET search_path = pg_catalog
RETURN encode(sha256(convert_to(p_value::text, 'UTF8')), 'hex')::core.sha256_hex;

CREATE FUNCTION release.trace_edge_generation_key(
  p_release_id uuid,
  p_corpus_version_id uuid,
  p_subject_trace_node_id uuid,
  p_semantic_relation_id uuid,
  p_object_trace_node_id uuid,
  p_projection_role text
)
RETURNS core.sha256_hex
LANGUAGE sql IMMUTABLE
SET search_path = pg_catalog
RETURN release.canonical_jsonb_sha256(jsonb_build_array(
  'gda-v49-trace-edge-v1', p_release_id, p_corpus_version_id,
  p_subject_trace_node_id, p_semantic_relation_id,
  p_object_trace_node_id, p_projection_role
));

CREATE FUNCTION release.validate_visual_projection(p_registry_id uuid)
RETURNS void
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE v_stored core.sha256_hex; v_computed core.sha256_hex;
BEGIN
  SELECT r.candidate_fingerprint INTO v_stored
  FROM release.visual_registry_release r
  WHERE r.visual_registry_release_id = p_registry_id
    AND r.release_state IN ('candidate', 'validated', 'sealed')
  FOR SHARE;
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'VISUAL_REGISTRY_NOT_VALIDATABLE';
  END IF;
  v_computed := release.compute_visual_candidate_fingerprint(p_registry_id);
  IF v_stored IS DISTINCT FROM v_computed THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'VISUAL_CANDIDATE_FINGERPRINT_MISMATCH';
  END IF;
  PERFORM rights.validate_one_provider_policy_evaluation(
    s.provider_policy_evaluation_id)
  FROM release.visual_registry_policy_evaluation_snapshot s
  WHERE s.visual_registry_release_id = p_registry_id;
  PERFORM rights.validate_one_delivery_assessment(s.delivery_assessment_id)
  FROM release.visual_registry_delivery_snapshot s
  WHERE s.visual_registry_release_id = p_registry_id;
  IF EXISTS (
    SELECT 1
    FROM release.visual_registry_policy_evaluation_snapshot evaluation
    JOIN rights.object_visual_reference bridge
      ON bridge.object_visual_reference_id = evaluation.object_visual_reference_id
    JOIN rights.external_visual_reference reference
      ON reference.external_visual_reference_id = bridge.external_visual_reference_id
    JOIN rights.provider_object provider_object
      ON provider_object.provider_object_id = reference.provider_object_id
    JOIN rights.provider_policy_version current_policy
      ON current_policy.provider_id = provider_object.provider_id
      AND current_policy.effective_from <= clock_timestamp()
      AND (current_policy.effective_until IS NULL
        OR current_policy.effective_until > clock_timestamp())
      AND current_policy.review_due > clock_timestamp()
    WHERE evaluation.visual_registry_release_id = p_registry_id
      AND NOT EXISTS (
        SELECT 1
        FROM release.visual_registry_policy_evaluation_version_snapshot linked
        WHERE linked.visual_registry_release_id =
            evaluation.visual_registry_release_id
          AND linked.provider_policy_evaluation_id =
            evaluation.provider_policy_evaluation_id
          AND linked.provider_policy_version_id =
            current_policy.provider_policy_version_id
      )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'VISUAL_POLICY_EVALUATION_NOT_CURRENT_AT_VALIDATION';
  END IF;
  IF EXISTS (
    SELECT 1 FROM release.visual_registry_provider_snapshot s
    JOIN rights.provider p ON p.provider_id = s.provider_id
    WHERE s.visual_registry_release_id = p_registry_id
      AND (s.provider_code IS DISTINCT FROM p.provider_code
        OR s.display_name IS DISTINCT FROM p.display_name
        OR s.provider_snapshot_sha256 IS DISTINCT FROM
          release.canonical_jsonb_sha256(jsonb_build_array(
            p.provider_id, p.provider_code, p.display_name)))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'VISUAL_PROVIDER_SNAPSHOT_MISMATCH';
  END IF;
  IF EXISTS (
    SELECT 1 FROM release.visual_registry_provider_object_snapshot s
    JOIN rights.provider_object p ON p.provider_object_id = s.provider_object_id
    WHERE s.visual_registry_release_id = p_registry_id
      AND (s.provider_id IS DISTINCT FROM p.provider_id
        OR s.provider_record_key IS DISTINCT FROM p.provider_record_key
        OR s.provider_object_snapshot_sha256 IS DISTINCT FROM
          release.canonical_jsonb_sha256(jsonb_build_array(
            p.provider_object_id, p.provider_id, p.provider_record_key)))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'VISUAL_PROVIDER_OBJECT_SNAPSHOT_MISMATCH';
  END IF;
  IF EXISTS (
    SELECT 1 FROM release.visual_registry_reference_snapshot s
    JOIN rights.external_visual_reference r
      ON r.external_visual_reference_id = s.external_visual_reference_id
    WHERE s.visual_registry_release_id = p_registry_id
      AND (s.visual_reference_urn IS DISTINCT FROM r.visual_reference_urn
        OR s.provider_object_id IS DISTINCT FROM r.provider_object_id
        OR s.reference_fingerprint IS DISTINCT FROM r.reference_fingerprint
        OR s.reference_snapshot_sha256 IS DISTINCT FROM
          release.canonical_jsonb_sha256(jsonb_build_array(
            r.external_visual_reference_id, r.visual_reference_urn,
            r.provider_object_id, r.reference_fingerprint)))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'VISUAL_REFERENCE_SNAPSHOT_MISMATCH';
  END IF;
  IF EXISTS (
    SELECT 1 FROM release.visual_registry_bridge_snapshot s
    JOIN rights.object_visual_reference b
      ON b.object_visual_reference_id = s.object_visual_reference_id
    LEFT JOIN rights.object_visual_reference_review_decision d
      ON d.object_visual_reference_review_decision_id =
        s.bridge_review_decision_id
    WHERE s.visual_registry_release_id = p_registry_id
      AND (b.acceptance_state <> 'accepted'
        OR s.archive_object_id IS DISTINCT FROM b.archive_object_id
        OR s.external_visual_reference_id IS DISTINCT FROM b.external_visual_reference_id
        OR s.reference_role IS DISTINCT FROM b.reference_role
        OR s.acceptance_state IS DISTINCT FROM b.acceptance_state
        OR s.evidence_item_id IS DISTINCT FROM b.evidence_item_id
        OR d.object_visual_reference_id IS DISTINCT FROM
          b.object_visual_reference_id
        OR d.outcome IS DISTINCT FROM 'accept'
        OR d.evidence_item_id IS DISTINCT FROM b.evidence_item_id
        OR EXISTS (
          SELECT 1
          FROM rights.object_visual_reference_review_decision newer
          WHERE newer.supersedes_decision_id =
            d.object_visual_reference_review_decision_id
        )
        OR s.evidence_snapshot_sha256 IS DISTINCT FROM
          rights.object_visual_reference_evidence_sha(b.evidence_item_id)
        OR s.decision_snapshot_sha256 IS DISTINCT FROM
          rights.object_visual_reference_decision_sha(
            d.object_visual_reference_review_decision_id)
        OR s.bridge_snapshot_sha256 IS DISTINCT FROM
          rights.object_visual_reference_snapshot_sha(
            b.object_visual_reference_id,
            s.compatible_research_release_id,
            s.compatible_research_manifest_sha256))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'VISUAL_BRIDGE_SNAPSHOT_MISMATCH';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM release.visual_registry_rights_assessment_snapshot s
    LEFT JOIN rights.rights_assessment a
      ON a.rights_assessment_id = s.rights_assessment_id
    WHERE s.visual_registry_release_id = p_registry_id
      AND (a.rights_assessment_id IS NULL
        OR a.assessed_state IS DISTINCT FROM s.assessed_state
        OR a.assessed_at IS DISTINCT FROM s.assessed_at
        OR a.assessed_at > clock_timestamp()
        OR s.assessment_snapshot_sha256 IS DISTINCT FROM
          rights.compute_rights_assessment_sha(s.rights_assessment_id)
        OR EXISTS (
          SELECT 1 FROM rights.rights_assessment newer
          WHERE newer.supersedes_rights_assessment_id = a.rights_assessment_id
        )
        OR 1 <> (
          SELECT count(*) FROM rights.rights_assessment current_assessment
          WHERE rights.assessment_subject_key(
              current_assessment.rights_assessment_id)
            = rights.assessment_subject_key(a.rights_assessment_id)
            AND NOT EXISTS (
              SELECT 1 FROM rights.rights_assessment newer
              WHERE newer.supersedes_rights_assessment_id =
                current_assessment.rights_assessment_id
            )
        )
        OR NOT EXISTS (
          SELECT 1 FROM release.visual_registry_delivery_rights_snapshot use_row
          WHERE use_row.visual_registry_release_id = s.visual_registry_release_id
            AND use_row.rights_assessment_id = s.rights_assessment_id
        ))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'VISUAL_RIGHTS_ASSESSMENT_SNAPSHOT_MISMATCH_OR_UNUSED';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM release.visual_registry_rights_observation_snapshot copied
    LEFT JOIN rights.rights_assessment_observation live_link
      ON live_link.rights_assessment_id = copied.rights_assessment_id
      AND live_link.rights_observation_id = copied.rights_observation_id
      AND live_link.evidence_role = copied.evidence_role
    LEFT JOIN rights.rights_observation live
      ON live.rights_observation_id = copied.rights_observation_id
    WHERE copied.visual_registry_release_id = p_registry_id
      AND (live_link.rights_observation_id IS NULL
        OR live.evidence_state IS DISTINCT FROM copied.evidence_state
        OR live.evidence_item_id IS DISTINCT FROM copied.evidence_item_id
        OR live.observed_at IS DISTINCT FROM copied.observed_at
        OR copied.observation_snapshot_sha256 IS DISTINCT FROM
          rights.compute_rights_observation_sha(copied.rights_observation_id))
  ) OR EXISTS (
    SELECT 1
    FROM release.visual_registry_rights_assessment_snapshot assessment
    JOIN rights.rights_assessment_observation live
      ON live.rights_assessment_id = assessment.rights_assessment_id
    WHERE assessment.visual_registry_release_id = p_registry_id
      AND NOT EXISTS (
        SELECT 1
        FROM release.visual_registry_rights_observation_snapshot copied
        WHERE copied.visual_registry_release_id =
            assessment.visual_registry_release_id
          AND copied.rights_assessment_id = live.rights_assessment_id
          AND copied.rights_observation_id = live.rights_observation_id
          AND copied.evidence_role = live.evidence_role
      )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'VISUAL_RIGHTS_OBSERVATION_COPY_SET_MISMATCH';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM release.visual_registry_policy_version_snapshot s
    LEFT JOIN rights.provider_policy_version p
      ON p.provider_policy_version_id = s.provider_policy_version_id
    WHERE s.visual_registry_release_id = p_registry_id
      AND (p.provider_policy_version_id IS NULL
        OR p.provider_id IS DISTINCT FROM s.provider_id
        OR p.version_token IS DISTINCT FROM s.version_token
        OR p.policy_sha256 IS DISTINCT FROM s.policy_sha256
        OR p.policy_state IS DISTINCT FROM s.policy_state
        OR p.source_evidence_item_id IS DISTINCT FROM s.source_evidence_item_id
        OR p.effective_from IS DISTINCT FROM s.effective_from
        OR p.effective_until IS DISTINCT FROM s.effective_until
        OR p.review_due IS DISTINCT FROM s.review_due
        OR NOT EXISTS (
          SELECT 1 FROM release.visual_registry_policy_evaluation_version_snapshot use_row
          WHERE use_row.visual_registry_release_id = s.visual_registry_release_id
            AND use_row.provider_policy_version_id = s.provider_policy_version_id
        ))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'VISUAL_PROVIDER_POLICY_VERSION_SNAPSHOT_MISMATCH_OR_UNUSED';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM release.visual_registry_policy_evaluation_snapshot s
    LEFT JOIN rights.provider_policy_evaluation p
      ON p.provider_policy_evaluation_id = s.provider_policy_evaluation_id
    WHERE s.visual_registry_release_id = p_registry_id
      AND (p.provider_policy_evaluation_id IS NULL
        OR p.object_visual_reference_id IS DISTINCT FROM s.object_visual_reference_id
        OR p.evaluated_state IS DISTINCT FROM s.evaluated_state
        OR p.evaluated_at IS DISTINCT FROM s.evaluated_at
        OR p.evaluated_at > clock_timestamp()
        OR s.evaluation_snapshot_sha256 IS DISTINCT FROM
          rights.compute_provider_policy_evaluation_sha(
            s.provider_policy_evaluation_id)
        OR EXISTS (
          SELECT 1 FROM rights.provider_policy_evaluation newer
          WHERE newer.supersedes_provider_policy_evaluation_id =
            p.provider_policy_evaluation_id
        )
        OR 1 <> (
          SELECT count(*) FROM rights.provider_policy_evaluation current_eval
          WHERE current_eval.object_visual_reference_id =
              p.object_visual_reference_id
            AND NOT EXISTS (
              SELECT 1 FROM rights.provider_policy_evaluation newer
              WHERE newer.supersedes_provider_policy_evaluation_id =
                current_eval.provider_policy_evaluation_id
            )
        )
        OR NOT EXISTS (
          SELECT 1 FROM release.visual_registry_delivery_policy_snapshot use_row
          WHERE use_row.visual_registry_release_id = s.visual_registry_release_id
            AND use_row.provider_policy_evaluation_id =
              s.provider_policy_evaluation_id
        ))
  ) OR EXISTS (
    SELECT 1
    FROM release.visual_registry_policy_evaluation_version_snapshot copied
    WHERE copied.visual_registry_release_id = p_registry_id
      AND NOT EXISTS (
        SELECT 1 FROM rights.provider_policy_evaluation_version live
        WHERE live.provider_policy_evaluation_id =
          copied.provider_policy_evaluation_id
          AND live.provider_policy_version_id = copied.provider_policy_version_id
      )
  ) OR EXISTS (
    SELECT 1
    FROM release.visual_registry_policy_evaluation_snapshot evaluation
    JOIN rights.provider_policy_evaluation_version live
      ON live.provider_policy_evaluation_id = evaluation.provider_policy_evaluation_id
    WHERE evaluation.visual_registry_release_id = p_registry_id
      AND NOT EXISTS (
        SELECT 1
        FROM release.visual_registry_policy_evaluation_version_snapshot copied
        WHERE copied.visual_registry_release_id = evaluation.visual_registry_release_id
          AND copied.provider_policy_evaluation_id =
            live.provider_policy_evaluation_id
          AND copied.provider_policy_version_id = live.provider_policy_version_id
      )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'VISUAL_POLICY_EVALUATION_SNAPSHOT_OR_LINK_SET_MISMATCH';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM release.visual_registry_policy_evaluation_snapshot evaluation
    JOIN release.visual_registry_policy_evaluation_version_snapshot link
      ON link.visual_registry_release_id = evaluation.visual_registry_release_id
      AND link.provider_policy_evaluation_id =
        evaluation.provider_policy_evaluation_id
    JOIN release.visual_registry_policy_version_snapshot policy
      ON policy.visual_registry_release_id = link.visual_registry_release_id
      AND policy.provider_policy_version_id = link.provider_policy_version_id
    JOIN release.visual_registry_delivery_policy_snapshot delivery_link
      ON delivery_link.visual_registry_release_id =
        evaluation.visual_registry_release_id
      AND delivery_link.provider_policy_evaluation_id =
        evaluation.provider_policy_evaluation_id
    JOIN release.visual_registry_delivery_snapshot delivery
      ON delivery.visual_registry_release_id = delivery_link.visual_registry_release_id
      AND delivery.delivery_assessment_id = delivery_link.delivery_assessment_id
    WHERE evaluation.visual_registry_release_id = p_registry_id
      AND delivery.base_delivery_mode = 'remote_image'
      AND (policy.source_evidence_item_id IS NULL
        OR policy.effective_from > clock_timestamp()
        OR policy.effective_until IS NULL
        OR policy.effective_until <= clock_timestamp()
        OR policy.review_due <= clock_timestamp())
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'REMOTE_DELIVERY_POLICY_NOT_EVIDENCED_OR_FRESH_AT_VALIDATION';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM release.visual_registry_delivery_snapshot s
    LEFT JOIN rights.delivery_assessment d
      ON d.delivery_assessment_id = s.delivery_assessment_id
    WHERE s.visual_registry_release_id = p_registry_id
      AND (d.delivery_assessment_id IS NULL
        OR d.object_visual_reference_id IS DISTINCT FROM s.object_visual_reference_id
        OR d.attribution_bundle_id IS DISTINCT FROM s.attribution_bundle_id
        OR d.delivery_mode IS DISTINCT FROM s.base_delivery_mode
        OR d.reason_code IS DISTINCT FROM s.reason_code
        OR d.assessed_at IS DISTINCT FROM s.assessed_at
        OR s.rights_outcome_sha256 IS DISTINCT FROM
          rights.compute_delivery_rights_sha(s.delivery_assessment_id)
        OR s.policy_outcome_sha256 IS DISTINCT FROM
          rights.compute_delivery_policy_sha(s.delivery_assessment_id)
        OR s.attribution_bundle_sha256 IS DISTINCT FROM CASE
          WHEN d.attribution_bundle_id IS NULL THEN NULL
          ELSE rights.compute_attribution_bundle_sha(d.attribution_bundle_id) END
        OR s.delivery_snapshot_sha256 IS DISTINCT FROM
          rights.compute_delivery_snapshot_sha(s.delivery_assessment_id)
        OR d.assessed_at > clock_timestamp()
        OR EXISTS (
          SELECT 1 FROM rights.delivery_assessment newer
          WHERE newer.supersedes_delivery_assessment_id = d.delivery_assessment_id
        )
        OR 1 <> (
          SELECT count(*) FROM rights.delivery_assessment current_delivery
          WHERE current_delivery.object_visual_reference_id = d.object_visual_reference_id
            AND NOT EXISTS (
              SELECT 1 FROM rights.delivery_assessment newer
              WHERE newer.supersedes_delivery_assessment_id =
                current_delivery.delivery_assessment_id
            )
        )
        OR (d.attribution_bundle_id IS NOT NULL AND (
          EXISTS (
            SELECT 1 FROM rights.attribution_bundle newer
            WHERE newer.supersedes_attribution_bundle_id = d.attribution_bundle_id
          )
          OR 1 <> (
            SELECT count(*) FROM rights.attribution_bundle current_bundle
            WHERE current_bundle.object_visual_reference_id =
                d.object_visual_reference_id
              AND NOT EXISTS (
                SELECT 1 FROM rights.attribution_bundle newer
                WHERE newer.supersedes_attribution_bundle_id =
                  current_bundle.attribution_bundle_id
              )
          )
          OR EXISTS (
            SELECT 1 FROM rights.attribution_bundle a
            WHERE a.attribution_bundle_id = d.attribution_bundle_id
              AND (a.validated_at > clock_timestamp()
                OR (d.delivery_mode = 'remote_image'
                  AND a.evidence_item_id IS NULL))
          )
        )))
  ) OR EXISTS (
    SELECT 1
    FROM release.visual_registry_delivery_rights_snapshot copied
    WHERE copied.visual_registry_release_id = p_registry_id
      AND NOT EXISTS (
        SELECT 1 FROM rights.delivery_rights_assessment live
        WHERE live.delivery_assessment_id = copied.delivery_assessment_id
          AND live.rights_assessment_id = copied.rights_assessment_id
          AND live.evidence_role = copied.evidence_role
      )
  ) OR EXISTS (
    SELECT 1
    FROM release.visual_registry_delivery_snapshot delivery
    JOIN rights.delivery_rights_assessment live
      ON live.delivery_assessment_id = delivery.delivery_assessment_id
    WHERE delivery.visual_registry_release_id = p_registry_id
      AND NOT EXISTS (
        SELECT 1 FROM release.visual_registry_delivery_rights_snapshot copied
        WHERE copied.visual_registry_release_id = delivery.visual_registry_release_id
          AND copied.delivery_assessment_id = live.delivery_assessment_id
          AND copied.rights_assessment_id = live.rights_assessment_id
          AND copied.evidence_role = live.evidence_role
      )
  ) OR EXISTS (
    SELECT 1
    FROM release.visual_registry_delivery_policy_snapshot copied
    WHERE copied.visual_registry_release_id = p_registry_id
      AND NOT EXISTS (
        SELECT 1 FROM rights.delivery_policy_evaluation live
        WHERE live.delivery_assessment_id = copied.delivery_assessment_id
          AND live.provider_policy_evaluation_id =
            copied.provider_policy_evaluation_id
      )
  ) OR EXISTS (
    SELECT 1
    FROM release.visual_registry_delivery_snapshot delivery
    JOIN rights.delivery_policy_evaluation live
      ON live.delivery_assessment_id = delivery.delivery_assessment_id
    WHERE delivery.visual_registry_release_id = p_registry_id
      AND NOT EXISTS (
        SELECT 1 FROM release.visual_registry_delivery_policy_snapshot copied
        WHERE copied.visual_registry_release_id = delivery.visual_registry_release_id
          AND copied.delivery_assessment_id = live.delivery_assessment_id
          AND copied.provider_policy_evaluation_id =
            live.provider_policy_evaluation_id
      )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'VISUAL_DELIVERY_SNAPSHOT_OR_GOVERNING_LINK_SET_MISMATCH';
  END IF;
  IF EXISTS (
    SELECT 1 FROM release.visual_registry_entry e
    WHERE e.visual_registry_release_id = p_registry_id
      AND (
        EXISTS (
          SELECT value_kind, value_ordinal, language_tag, value_text
          FROM release.visual_registry_attribution_value copied
          WHERE copied.visual_registry_release_id = e.visual_registry_release_id
            AND copied.visual_registry_entry_id = e.visual_registry_entry_id
          EXCEPT
          SELECT value_kind, value_ordinal, language_tag, value_text
          FROM rights.attribution_bundle_value live
          JOIN rights.delivery_assessment d
            ON d.attribution_bundle_id = live.attribution_bundle_id
          WHERE d.delivery_assessment_id = e.delivery_assessment_id
        )
        OR EXISTS (
          SELECT value_kind, value_ordinal, language_tag, value_text
          FROM rights.attribution_bundle_value live
          JOIN rights.delivery_assessment d
            ON d.attribution_bundle_id = live.attribution_bundle_id
          WHERE d.delivery_assessment_id = e.delivery_assessment_id
          EXCEPT
          SELECT value_kind, value_ordinal, language_tag, value_text
          FROM release.visual_registry_attribution_value copied
          WHERE copied.visual_registry_release_id = e.visual_registry_release_id
            AND copied.visual_registry_entry_id = e.visual_registry_entry_id
        )
      )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'VISUAL_ATTRIBUTION_ORDERED_COPY_SET_MISMATCH';
  END IF;
  IF EXISTS (
    SELECT 1 FROM release.visual_registry_public_locator l
    WHERE l.visual_registry_release_id = p_registry_id
      AND (l.health_state <> 'healthy_fresh'
        OR l.health_observed_at > clock_timestamp()
        OR l.health_valid_until IS NULL
        OR l.health_valid_until <= clock_timestamp()
        OR NOT EXISTS (
          SELECT 1
          FROM release.visual_registry_entry e
          JOIN rights.visual_locator live
            ON live.visual_locator_id = l.visual_locator_id
          JOIN rights.endpoint_health_observation h
            ON h.endpoint_health_observation_id =
              l.endpoint_health_observation_id
          JOIN rights.delivery_locator_qualification q
            ON q.delivery_assessment_id = e.delivery_assessment_id
            AND q.visual_locator_id = l.visual_locator_id
            AND q.endpoint_health_observation_id =
              l.endpoint_health_observation_id
            AND q.allowlisted_role = l.locator_role
          WHERE e.visual_registry_release_id = l.visual_registry_release_id
            AND e.visual_registry_entry_id = l.visual_registry_entry_id
            AND live.external_visual_reference_id =
              e.external_visual_reference_id
            AND live.locator_role = l.locator_role
            AND live.visibility = 'public_candidate'
            AND live.raw_locator = l.public_locator
            AND live.locator_fingerprint = l.locator_sha256
            AND h.visual_locator_id = l.visual_locator_id
            AND h.health_state = l.health_state
            AND h.method_version = l.health_method_version
            AND h.checked_at = l.health_observed_at
            AND h.valid_until = l.health_valid_until
            AND rights.compute_health_observation_sha(
              h.endpoint_health_observation_id) =
                l.health_observation_sha256
            AND NOT EXISTS (
              SELECT 1 FROM rights.visual_locator newer
              WHERE newer.supersedes_visual_locator_id = l.visual_locator_id
            )
        ))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'VISUAL_LOCATOR_NOT_HEALTHY_FRESH_AT_VALIDATION';
  END IF;
  IF EXISTS (
    SELECT 1 FROM release.visual_registry_entry e
    WHERE e.visual_registry_release_id = p_registry_id
      AND (
        (e.base_delivery_mode IN ('blocked', 'citation_only') AND EXISTS (
          SELECT 1 FROM release.visual_registry_public_locator l
          WHERE l.visual_registry_release_id = e.visual_registry_release_id
            AND l.visual_registry_entry_id = e.visual_registry_entry_id))
        OR (e.base_delivery_mode = 'link_only' AND NOT EXISTS (
          SELECT 1 FROM release.visual_registry_public_locator l
          WHERE l.visual_registry_release_id = e.visual_registry_release_id
            AND l.visual_registry_entry_id = e.visual_registry_entry_id
            AND l.locator_role = 'canonical_record'))
        OR (e.base_delivery_mode = 'source_viewer' AND NOT EXISTS (
          SELECT 1 FROM release.visual_registry_public_locator l
          WHERE l.visual_registry_release_id = e.visual_registry_release_id
            AND l.visual_registry_entry_id = e.visual_registry_entry_id
            AND l.locator_role = 'source_viewer'))
        OR (e.base_delivery_mode = 'remote_image' AND NOT EXISTS (
          SELECT 1 FROM release.visual_registry_public_locator l
          WHERE l.visual_registry_release_id = e.visual_registry_release_id
            AND l.visual_registry_entry_id = e.visual_registry_entry_id
            AND l.locator_role = 'direct_image'))
      )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'VISUAL_ENTRY_REQUIRED_LOCATOR_SET_MISSING';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM release.visual_registry_entry e
    JOIN rights.takedown_scope s
      ON rights.scope_matches_bridge(s.takedown_scope_id, e.object_visual_reference_id)
    JOIN rights.takedown_event te ON te.takedown_event_id = s.takedown_event_id
    WHERE e.visual_registry_release_id = p_registry_id
      AND (te.effective_until IS NULL OR te.effective_until > clock_timestamp())
      AND NOT EXISTS (
        SELECT 1
        FROM rights.takedown_override o
        JOIN release.visual_registry_takedown_snapshot ts
          ON ts.takedown_override_id = o.takedown_override_id
        WHERE o.takedown_scope_id = s.takedown_scope_id
          AND NOT EXISTS (
            SELECT 1 FROM rights.takedown_override newer
            WHERE newer.supersedes_takedown_override_id = o.takedown_override_id
          )
          AND ts.visual_registry_release_id = e.visual_registry_release_id
          AND ts.visual_registry_entry_id = e.visual_registry_entry_id
          AND ts.restrictive_mode = o.restrictive_mode
          AND ts.overlay_sha256 = o.overlay_sha256
          AND rights.delivery_rank(e.base_delivery_mode)
            <= rights.delivery_rank(o.restrictive_mode)
      )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ACTIVE_TAKEDOWN_NOT_COVERED_BY_RESTRICTIVE_SNAPSHOT';
  END IF;
END
$function$;

CREATE FUNCTION release.compute_research_validation_receipt_sha(
  p_release_id uuid, p_verifier_version core.release_token
)
RETURNS core.sha256_hex LANGUAGE sql STABLE SET search_path = pg_catalog
RETURN release.canonical_jsonb_sha256(jsonb_build_object(
  'format', 'gda-v49-research-validation-receipt-v1',
  'releaseId', p_release_id,
  'verifierVersion', p_verifier_version,
  'candidateFingerprint', release.compute_research_candidate_fingerprint(p_release_id),
  'objectCount', (SELECT count(*) FROM release.research_release_object x
    WHERE x.research_release_id = p_release_id),
  'claimCount', (SELECT count(*) FROM release.research_release_claim x
    WHERE x.research_release_id = p_release_id),
  'relationCount', (SELECT count(*) FROM release.research_release_relation x
    WHERE x.research_release_id = p_release_id),
  'traceNodeCount', (SELECT count(*) FROM release.trace_projection_node x
    WHERE x.research_release_id = p_release_id),
  'traceEdgeCount', (SELECT count(*) FROM release.trace_projection_edge x
    WHERE x.research_release_id = p_release_id),
  'result', 'pass'
));

CREATE FUNCTION release.compute_visual_validation_receipt_sha(
  p_registry_id uuid, p_verifier_version core.release_token
)
RETURNS core.sha256_hex LANGUAGE sql STABLE SET search_path = pg_catalog
RETURN release.canonical_jsonb_sha256(jsonb_build_object(
  'format', 'gda-v49-visual-validation-receipt-v1',
  'registryId', p_registry_id,
  'verifierVersion', p_verifier_version,
  'candidateFingerprint', release.compute_visual_candidate_fingerprint(p_registry_id),
  'entryCount', (SELECT count(*) FROM release.visual_registry_entry x
    WHERE x.visual_registry_release_id = p_registry_id),
  'locatorCount', (SELECT count(*) FROM release.visual_registry_public_locator x
    WHERE x.visual_registry_release_id = p_registry_id),
  'takedownCount', (SELECT count(*) FROM release.visual_registry_takedown_snapshot x
    WHERE x.visual_registry_release_id = p_registry_id),
  'result', 'pass'
));

CREATE FUNCTION release.compute_research_verification_sidecar_sha(
  p_release_id uuid, p_manifest_sha256 core.sha256_hex,
  p_verifier_version core.release_token
)
RETURNS core.sha256_hex LANGUAGE sql STABLE SET search_path = pg_catalog
RETURN release.canonical_jsonb_sha256(jsonb_build_object(
  'format', 'gda-v49-research-verification-sidecar-v1',
  'releaseId', p_release_id,
  'manifestSha256', p_manifest_sha256,
  'verifierVersion', p_verifier_version,
  'candidateFingerprint', release.compute_research_candidate_fingerprint(p_release_id),
  'manifestBytesSha256', (SELECT encode(sha256(m.manifest_bytes), 'hex')
    FROM release.research_release_manifest m
    WHERE m.research_release_id = p_release_id)
));

CREATE FUNCTION release.compute_visual_verification_sidecar_sha(
  p_registry_id uuid, p_manifest_sha256 core.sha256_hex,
  p_verifier_version core.release_token
)
RETURNS core.sha256_hex LANGUAGE sql STABLE SET search_path = pg_catalog
RETURN release.canonical_jsonb_sha256(jsonb_build_object(
  'format', 'gda-v49-visual-verification-sidecar-v1',
  'registryId', p_registry_id,
  'manifestSha256', p_manifest_sha256,
  'verifierVersion', p_verifier_version,
  'candidateFingerprint', release.compute_visual_candidate_fingerprint(p_registry_id),
  'manifestBytesSha256', (SELECT encode(sha256(m.manifest_bytes), 'hex')
    FROM release.visual_registry_manifest m
    WHERE m.visual_registry_release_id = p_registry_id)
));

CREATE FUNCTION release.build_research_manifest_bytes(p_release_id uuid)
RETURNS bytea
LANGUAGE sql STABLE
SET search_path = pg_catalog
RETURN convert_to((
  SELECT jsonb_build_object(
    'candidateFingerprint', r.candidate_fingerprint,
    'modelVersion', r.model_version,
    'objectCount', (SELECT count(*) FROM release.research_release_object x WHERE x.research_release_id = r.research_release_id),
    'relationCount', (SELECT count(*) FROM release.research_release_relation x WHERE x.research_release_id = r.research_release_id),
    'researchReleaseId', r.release_token,
    'schemaVersion', r.schema_version,
    'validationReceipts', COALESCE((SELECT jsonb_agg(jsonb_build_array(
      vr.verifier_version, vr.receipt_sha256, vr.validation_result
    ) ORDER BY vr.verifier_version, vr.receipt_sha256)
      FROM release.research_validation_receipt vr
      WHERE vr.research_release_id = r.research_release_id), '[]'::jsonb),
    'traceEdgeCount', (SELECT count(*) FROM release.trace_projection_edge x WHERE x.research_release_id = r.research_release_id)
  )::text FROM release.research_release r WHERE r.research_release_id = p_release_id
), 'UTF8');

CREATE FUNCTION release.build_visual_manifest_bytes(p_registry_id uuid)
RETURNS bytea
LANGUAGE sql STABLE
SET search_path = pg_catalog
RETURN convert_to((
  SELECT jsonb_build_object(
    'candidateFingerprint', r.candidate_fingerprint,
    'compatibleResearchManifestSha256', r.compatible_research_manifest_sha256,
    'compatibleResearchReleaseId', rr.release_token,
    'entryCount', (SELECT count(*) FROM release.visual_registry_entry x WHERE x.visual_registry_release_id = r.visual_registry_release_id),
    'modelVersion', r.model_version,
    'registryVersion', r.registry_version,
    'schemaVersion', r.schema_version,
    'validationReceipts', COALESCE((SELECT jsonb_agg(jsonb_build_array(
      vr.verifier_version, vr.receipt_sha256, vr.validation_result
    ) ORDER BY vr.verifier_version, vr.receipt_sha256)
      FROM release.visual_validation_receipt vr
      WHERE vr.visual_registry_release_id = r.visual_registry_release_id), '[]'::jsonb)
  )::text
  FROM release.visual_registry_release r
  JOIN release.research_release rr
    ON rr.research_release_id = r.compatible_research_release_id
  WHERE r.visual_registry_release_id = p_registry_id
), 'UTF8');

CREATE FUNCTION release.verify_sealed_research_integrity(
  p_release_id uuid, p_manifest_sha256 core.sha256_hex
)
RETURNS void LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
DECLARE
  v_release release.research_release%ROWTYPE;
  v_manifest release.research_release_manifest%ROWTYPE;
BEGIN
  SELECT * INTO v_release FROM release.research_release r
  WHERE r.research_release_id = p_release_id AND r.release_state = 'sealed'
  FOR SHARE;
  SELECT * INTO v_manifest FROM release.research_release_manifest m
  WHERE m.research_release_id = p_release_id
    AND m.manifest_sha256 = p_manifest_sha256;
  IF v_release.research_release_id IS NULL
    OR v_manifest.research_release_id IS NULL
    OR v_release.manifest_sha256 IS DISTINCT FROM p_manifest_sha256
    OR v_release.candidate_fingerprint IS DISTINCT FROM
      release.compute_research_candidate_fingerprint(p_release_id)
    OR encode(sha256(v_manifest.manifest_bytes), 'hex')
      IS DISTINCT FROM p_manifest_sha256
    OR v_manifest.manifest_bytes IS DISTINCT FROM
      release.build_research_manifest_bytes(p_release_id) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'SEALED_RESEARCH_SNAPSHOT_INTEGRITY_MISMATCH';
  END IF;
END
$function$;

CREATE FUNCTION release.verify_sealed_visual_integrity(
  p_registry_id uuid, p_manifest_sha256 core.sha256_hex
)
RETURNS void LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
DECLARE
  v_release release.visual_registry_release%ROWTYPE;
  v_manifest release.visual_registry_manifest%ROWTYPE;
BEGIN
  SELECT * INTO v_release FROM release.visual_registry_release r
  WHERE r.visual_registry_release_id = p_registry_id
    AND r.release_state = 'sealed' FOR SHARE;
  SELECT * INTO v_manifest FROM release.visual_registry_manifest m
  WHERE m.visual_registry_release_id = p_registry_id
    AND m.manifest_sha256 = p_manifest_sha256;
  IF v_release.visual_registry_release_id IS NULL
    OR v_manifest.visual_registry_release_id IS NULL
    OR v_release.manifest_sha256 IS DISTINCT FROM p_manifest_sha256
    OR v_release.candidate_fingerprint IS DISTINCT FROM
      release.compute_visual_candidate_fingerprint(p_registry_id)
    OR encode(sha256(v_manifest.manifest_bytes), 'hex')
      IS DISTINCT FROM p_manifest_sha256
    OR v_manifest.manifest_bytes IS DISTINCT FROM
      release.build_visual_manifest_bytes(p_registry_id) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'SEALED_VISUAL_SNAPSHOT_INTEGRITY_MISMATCH';
  END IF;
END
$function$;

CREATE FUNCTION release.create_research_release(
  p_release_id uuid, p_release_token core.release_token,
  p_schema_version core.release_token, p_model_version core.release_token,
  p_event_id uuid, p_event_sha256 core.sha256_hex
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  INSERT INTO release.research_release (
    research_release_id, release_token, release_state, schema_version, model_version, created_at
  ) VALUES (p_release_id, p_release_token, 'draft', p_schema_version, p_model_version, clock_timestamp());
  INSERT INTO audit.research_release_event VALUES (
    p_event_id, p_release_id, NULL, 'draft', session_user::text, clock_timestamp(), p_event_sha256);
END
$function$;

CREATE FUNCTION release.close_research_candidate(
  p_release_id uuid, p_expected_fingerprint core.sha256_hex,
  p_event_id uuid, p_event_sha256 core.sha256_hex
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE v_computed core.sha256_hex;
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM 1 FROM release.research_release r
    WHERE r.research_release_id = p_release_id AND r.release_state = 'draft' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RESEARCH_RELEASE_NOT_DRAFT'; END IF;
  v_computed := release.compute_research_candidate_fingerprint(p_release_id);
  IF p_expected_fingerprint IS DISTINCT FROM v_computed THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'RESEARCH_EXPECTED_FINGERPRINT_MISMATCH';
  END IF;
  UPDATE release.research_release SET release_state = 'candidate',
    candidate_fingerprint = v_computed, candidate_at = clock_timestamp()
  WHERE research_release_id = p_release_id;
  INSERT INTO audit.research_release_event VALUES (
    p_event_id, p_release_id, 'draft', 'candidate', session_user::text, clock_timestamp(), p_event_sha256);
END
$function$;

CREATE FUNCTION release.validate_research_release(
  p_release_id uuid, p_receipt_id uuid, p_verifier_version core.release_token,
  p_receipt_sha256 core.sha256_hex, p_event_id uuid, p_event_sha256 core.sha256_hex
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE v_fingerprint core.sha256_hex; v_expected core.sha256_hex;
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  SELECT r.candidate_fingerprint INTO v_fingerprint FROM release.research_release r
    WHERE r.research_release_id = p_release_id AND r.release_state = 'candidate' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RESEARCH_RELEASE_NOT_CANDIDATE'; END IF;
  PERFORM release.validate_research_projection(p_release_id);
  v_expected := release.compute_research_validation_receipt_sha(
    p_release_id, p_verifier_version);
  IF p_receipt_sha256 IS DISTINCT FROM v_expected THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'RESEARCH_VALIDATION_RECEIPT_DIGEST_MISMATCH';
  END IF;
  INSERT INTO release.research_validation_receipt VALUES (
    p_receipt_id, p_release_id, v_fingerprint, p_verifier_version,
    p_receipt_sha256, 'pass', clock_timestamp());
  UPDATE release.research_release SET release_state = 'validated', validated_at = clock_timestamp()
    WHERE research_release_id = p_release_id;
  INSERT INTO audit.research_release_event VALUES (
    p_event_id, p_release_id, 'candidate', 'validated', session_user::text, clock_timestamp(), p_event_sha256);
END
$function$;

CREATE FUNCTION release.seal_research_release(
  p_release_id uuid, p_seal_event_id uuid,
  p_release_event_id uuid, p_event_sha256 core.sha256_hex
)
RETURNS core.sha256_hex LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE v_bytes bytea; v_sha core.sha256_hex; v_fingerprint core.sha256_hex;
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  IF current_setting('transaction_isolation') <> 'serializable' THEN
    RAISE EXCEPTION USING ERRCODE = '25001',
      MESSAGE = 'RESEARCH_SEAL_REQUIRES_SERIALIZABLE_TRANSACTION';
  END IF;
  SELECT r.candidate_fingerprint INTO v_fingerprint FROM release.research_release r
    WHERE r.research_release_id = p_release_id AND r.release_state = 'validated' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RESEARCH_RELEASE_NOT_VALIDATED'; END IF;
  PERFORM release.validate_research_projection(p_release_id);
  IF NOT EXISTS (
    SELECT 1 FROM release.research_validation_receipt vr
    WHERE vr.research_release_id = p_release_id
      AND vr.candidate_fingerprint = v_fingerprint AND vr.validation_result = 'pass'
  ) THEN RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RESEARCH_RELEASE_PASS_RECEIPT_REQUIRED'; END IF;
  v_bytes := release.build_research_manifest_bytes(p_release_id);
  v_sha := encode(sha256(v_bytes), 'hex')::core.sha256_hex;
  INSERT INTO release.research_release_manifest VALUES (
    p_release_id, v_bytes, v_sha, octet_length(v_bytes), clock_timestamp());
  UPDATE release.research_release SET release_state = 'sealed',
    manifest_sha256 = v_sha, sealed_at = clock_timestamp() WHERE research_release_id = p_release_id;
  INSERT INTO audit.research_release_event VALUES (
    p_release_event_id, p_release_id, 'validated', 'sealed', session_user::text, clock_timestamp(), p_event_sha256);
  INSERT INTO audit.research_seal_event VALUES (
    p_seal_event_id, p_release_id, v_sha, session_user::text, clock_timestamp());
  RETURN v_sha;
END
$function$;

CREATE FUNCTION release.record_research_verification(
  p_verification_id uuid, p_release_id uuid, p_manifest_sha256 core.sha256_hex,
  p_verifier_version core.release_token, p_sidecar_sha256 core.sha256_hex,
  p_audit_event_id uuid, p_audit_receipt_sha256 core.sha256_hex
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE v_expected core.sha256_hex; v_manifest release.research_release_manifest%ROWTYPE;
BEGIN
  PERFORM rights.require_reviewer();
  SELECT * INTO v_manifest FROM release.research_release_manifest m
  WHERE m.research_release_id = p_release_id
    AND m.manifest_sha256 = p_manifest_sha256;
  IF v_manifest.research_release_id IS NULL THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'RESEARCH_VERIFICATION_MANIFEST_MISMATCH';
  END IF;
  PERFORM release.verify_sealed_research_integrity(
    p_release_id, p_manifest_sha256);
  v_expected := release.compute_research_verification_sidecar_sha(
    p_release_id, p_manifest_sha256, p_verifier_version);
  IF p_sidecar_sha256 IS DISTINCT FROM v_expected THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'RESEARCH_VERIFICATION_SIDECAR_MISMATCH';
  END IF;
  INSERT INTO release.research_release_verification VALUES (
    p_verification_id, p_release_id, p_manifest_sha256, p_verifier_version,
    p_sidecar_sha256, true, clock_timestamp());
  INSERT INTO audit.verification_receipt_event VALUES (
    p_audit_event_id, p_verification_id, NULL, p_audit_receipt_sha256,
    session_user::text, clock_timestamp());
END
$function$;

CREATE FUNCTION release.create_visual_registry(
  p_registry_id uuid, p_registry_version core.release_token,
  p_schema_version core.release_token, p_model_version core.release_token,
  p_research_release_id uuid, p_research_manifest_sha256 core.sha256_hex,
  p_event_id uuid, p_event_sha256 core.sha256_hex
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  INSERT INTO release.visual_registry_release (
    visual_registry_release_id, registry_version, release_state, schema_version,
    model_version, compatible_research_release_id,
    compatible_research_manifest_sha256, created_at
  ) VALUES (p_registry_id, p_registry_version, 'draft', p_schema_version,
    p_model_version, p_research_release_id, p_research_manifest_sha256, clock_timestamp());
  INSERT INTO audit.visual_release_event VALUES (
    p_event_id, p_registry_id, NULL, 'draft', session_user::text, clock_timestamp(), p_event_sha256);
END
$function$;

CREATE FUNCTION release.close_visual_candidate(
  p_registry_id uuid, p_expected_fingerprint core.sha256_hex,
  p_event_id uuid, p_event_sha256 core.sha256_hex
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE v_computed core.sha256_hex;
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM 1 FROM release.visual_registry_release r
    WHERE r.visual_registry_release_id = p_registry_id AND r.release_state = 'draft' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'VISUAL_REGISTRY_NOT_DRAFT'; END IF;
  v_computed := release.compute_visual_candidate_fingerprint(p_registry_id);
  IF p_expected_fingerprint IS DISTINCT FROM v_computed THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'VISUAL_EXPECTED_FINGERPRINT_MISMATCH';
  END IF;
  UPDATE release.visual_registry_release SET release_state = 'candidate',
    candidate_fingerprint = v_computed, candidate_at = clock_timestamp()
  WHERE visual_registry_release_id = p_registry_id;
  INSERT INTO audit.visual_release_event VALUES (
    p_event_id, p_registry_id, 'draft', 'candidate', session_user::text, clock_timestamp(), p_event_sha256);
END
$function$;

CREATE FUNCTION release.validate_visual_registry(
  p_registry_id uuid, p_receipt_id uuid, p_verifier_version core.release_token,
  p_receipt_sha256 core.sha256_hex, p_event_id uuid, p_event_sha256 core.sha256_hex
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE v_fingerprint core.sha256_hex; v_expected core.sha256_hex;
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM pg_advisory_xact_lock(hashtext('gda_v49_visual_seal_takedown'));
  SELECT r.candidate_fingerprint INTO v_fingerprint FROM release.visual_registry_release r
    WHERE r.visual_registry_release_id = p_registry_id AND r.release_state = 'candidate' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'VISUAL_REGISTRY_NOT_CANDIDATE'; END IF;
  PERFORM release.validate_visual_projection(p_registry_id);
  v_expected := release.compute_visual_validation_receipt_sha(
    p_registry_id, p_verifier_version);
  IF p_receipt_sha256 IS DISTINCT FROM v_expected THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'VISUAL_VALIDATION_RECEIPT_DIGEST_MISMATCH';
  END IF;
  INSERT INTO release.visual_validation_receipt VALUES (
    p_receipt_id, p_registry_id, v_fingerprint, p_verifier_version,
    p_receipt_sha256, 'pass', clock_timestamp());
  UPDATE release.visual_registry_release SET release_state = 'validated', validated_at = clock_timestamp()
    WHERE visual_registry_release_id = p_registry_id;
  INSERT INTO audit.visual_release_event VALUES (
    p_event_id, p_registry_id, 'candidate', 'validated', session_user::text, clock_timestamp(), p_event_sha256);
END
$function$;

CREATE FUNCTION release.seal_visual_registry(
  p_registry_id uuid, p_seal_event_id uuid,
  p_release_event_id uuid, p_event_sha256 core.sha256_hex
)
RETURNS core.sha256_hex LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE v_bytes bytea; v_sha core.sha256_hex; v_fingerprint core.sha256_hex;
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  IF current_setting('transaction_isolation') <> 'serializable' THEN
    RAISE EXCEPTION USING ERRCODE = '25001',
      MESSAGE = 'VISUAL_SEAL_REQUIRES_SERIALIZABLE_TRANSACTION';
  END IF;
  PERFORM pg_advisory_xact_lock(hashtext('gda_v49_visual_seal_takedown'));
  SELECT r.candidate_fingerprint INTO v_fingerprint FROM release.visual_registry_release r
    WHERE r.visual_registry_release_id = p_registry_id AND r.release_state = 'validated' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'VISUAL_REGISTRY_NOT_VALIDATED'; END IF;
  PERFORM release.validate_visual_projection(p_registry_id);
  IF NOT EXISTS (
    SELECT 1 FROM release.visual_validation_receipt vr
    WHERE vr.visual_registry_release_id = p_registry_id
      AND vr.candidate_fingerprint = v_fingerprint AND vr.validation_result = 'pass'
  ) THEN RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'VISUAL_REGISTRY_PASS_RECEIPT_REQUIRED'; END IF;
  v_bytes := release.build_visual_manifest_bytes(p_registry_id);
  v_sha := encode(sha256(v_bytes), 'hex')::core.sha256_hex;
  INSERT INTO release.visual_registry_manifest VALUES (
    p_registry_id, v_bytes, v_sha, octet_length(v_bytes), clock_timestamp());
  UPDATE release.visual_registry_release SET release_state = 'sealed',
    manifest_sha256 = v_sha, sealed_at = clock_timestamp()
  WHERE visual_registry_release_id = p_registry_id;
  INSERT INTO audit.visual_release_event VALUES (
    p_release_event_id, p_registry_id, 'validated', 'sealed', session_user::text, clock_timestamp(), p_event_sha256);
  INSERT INTO audit.visual_seal_event VALUES (
    p_seal_event_id, p_registry_id, v_sha, session_user::text, clock_timestamp());
  RETURN v_sha;
END
$function$;

CREATE FUNCTION release.record_visual_verification(
  p_verification_id uuid, p_registry_id uuid, p_manifest_sha256 core.sha256_hex,
  p_verifier_version core.release_token, p_sidecar_sha256 core.sha256_hex,
  p_audit_event_id uuid, p_audit_receipt_sha256 core.sha256_hex
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE v_expected core.sha256_hex; v_manifest release.visual_registry_manifest%ROWTYPE;
BEGIN
  PERFORM rights.require_reviewer();
  SELECT * INTO v_manifest FROM release.visual_registry_manifest m
  WHERE m.visual_registry_release_id = p_registry_id
    AND m.manifest_sha256 = p_manifest_sha256;
  IF v_manifest.visual_registry_release_id IS NULL THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'VISUAL_VERIFICATION_MANIFEST_MISMATCH';
  END IF;
  PERFORM release.verify_sealed_visual_integrity(
    p_registry_id, p_manifest_sha256);
  v_expected := release.compute_visual_verification_sidecar_sha(
    p_registry_id, p_manifest_sha256, p_verifier_version);
  IF p_sidecar_sha256 IS DISTINCT FROM v_expected THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'VISUAL_VERIFICATION_SIDECAR_MISMATCH';
  END IF;
  INSERT INTO release.visual_registry_verification VALUES (
    p_verification_id, p_registry_id, p_manifest_sha256, p_verifier_version,
    p_sidecar_sha256, true, clock_timestamp());
  INSERT INTO audit.verification_receipt_event VALUES (
    p_audit_event_id, NULL, p_verification_id, p_audit_receipt_sha256,
    session_user::text, clock_timestamp());
END
$function$;

CREATE FUNCTION release.initialize_research_current(p_channel core.release_token)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  INSERT INTO release.research_current_pointer VALUES (
    p_channel, 0, NULL, NULL, clock_timestamp());
END
$function$;

CREATE FUNCTION release.initialize_visual_current(p_channel core.release_token)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  INSERT INTO release.visual_current_pointer VALUES (
    p_channel, 0, NULL, NULL, clock_timestamp());
END
$function$;

CREATE FUNCTION release.promote_research_current_cas(
  p_attempt_id uuid, p_channel core.release_token,
  p_expected_generation bigint, p_expected_release_id uuid,
  p_expected_manifest_sha256 core.sha256_hex, p_target_release_id uuid
)
RETURNS TABLE (succeeded boolean, reason_code text, new_generation bigint)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE v_pointer release.research_current_pointer%ROWTYPE;
  v_target release.research_release%ROWTYPE; v_reason text;
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  SELECT * INTO v_pointer FROM release.research_current_pointer p
    WHERE p.channel = p_channel FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RESEARCH_CURRENT_CHANNEL_NOT_INITIALIZED'; END IF;
  IF p_expected_generation IS NULL
    OR v_pointer.generation IS DISTINCT FROM p_expected_generation
    OR v_pointer.research_release_id IS DISTINCT FROM p_expected_release_id
    OR v_pointer.manifest_sha256 IS DISTINCT FROM p_expected_manifest_sha256 THEN
    v_reason := 'STALE_RESEARCH_CURRENT_CAS';
  ELSE
    SELECT * INTO v_target FROM release.research_release r
      WHERE r.research_release_id = p_target_release_id;
    IF NOT FOUND OR v_target.release_state <> 'sealed' THEN
      v_reason := 'UNSEALED_RESEARCH_CURRENT_TARGET';
    ELSIF NOT EXISTS (
      SELECT 1 FROM release.research_release_verification v
      WHERE v.research_release_id = v_target.research_release_id
        AND v.manifest_sha256 = v_target.manifest_sha256 AND v.verified
    ) THEN v_reason := 'UNVERIFIED_RESEARCH_CURRENT_TARGET'; END IF;
  END IF;
  IF v_reason IS NOT NULL THEN
    INSERT INTO audit.research_cas_attempt VALUES (
      p_attempt_id, p_channel, COALESCE(p_expected_generation, -1), v_pointer.generation,
      p_target_release_id, false, v_reason, session_user::text, clock_timestamp());
    RETURN QUERY SELECT false, v_reason, v_pointer.generation; RETURN;
  END IF;
  UPDATE release.research_current_pointer SET generation = generation + 1,
    research_release_id = v_target.research_release_id,
    manifest_sha256 = v_target.manifest_sha256, updated_at = clock_timestamp()
  WHERE channel = p_channel;
  IF EXISTS (SELECT 1 FROM release.public_channel c WHERE c.channel = p_channel) THEN
    INSERT INTO release.research_publication_history (
      channel, research_release_id, manifest_sha256,
      promoted_generation, published_at
    ) VALUES (
      p_channel, v_target.research_release_id, v_target.manifest_sha256,
      v_pointer.generation + 1, clock_timestamp()
    );
  END IF;
  INSERT INTO audit.research_cas_attempt VALUES (
    p_attempt_id, p_channel, p_expected_generation, v_pointer.generation,
    p_target_release_id, true, 'PROMOTED', session_user::text, clock_timestamp());
  RETURN QUERY SELECT true, 'PROMOTED'::text, v_pointer.generation + 1;
END
$function$;

CREATE FUNCTION release.promote_visual_current_cas(
  p_attempt_id uuid, p_research_channel core.release_token,
  p_expected_research_generation bigint, p_expected_research_release_id uuid,
  p_expected_research_manifest_sha256 core.sha256_hex,
  p_visual_channel core.release_token, p_expected_visual_generation bigint,
  p_expected_visual_release_id uuid, p_expected_visual_manifest_sha256 core.sha256_hex,
  p_target_visual_release_id uuid
)
RETURNS TABLE (succeeded boolean, reason_code text, new_generation bigint)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog
AS $function$
DECLARE v_research release.research_current_pointer%ROWTYPE;
  v_visual release.visual_current_pointer%ROWTYPE;
  v_target release.visual_registry_release%ROWTYPE; v_reason text;
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  SELECT * INTO v_research FROM release.research_current_pointer p
    WHERE p.channel = p_research_channel FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'RESEARCH_CURRENT_CHANNEL_NOT_INITIALIZED'; END IF;
  SELECT * INTO v_visual FROM release.visual_current_pointer p
    WHERE p.channel = p_visual_channel FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'VISUAL_CURRENT_CHANNEL_NOT_INITIALIZED'; END IF;
  IF p_expected_research_generation IS NULL
    OR v_research.research_release_id IS NULL OR v_research.manifest_sha256 IS NULL
    OR v_research.generation IS DISTINCT FROM p_expected_research_generation
    OR v_research.research_release_id IS DISTINCT FROM p_expected_research_release_id
    OR v_research.manifest_sha256 IS DISTINCT FROM p_expected_research_manifest_sha256 THEN
    v_reason := 'STALE_OR_UNAVAILABLE_RESEARCH_GUARD_FOR_VISUAL_CAS';
  ELSIF p_expected_visual_generation IS NULL
    OR v_visual.generation IS DISTINCT FROM p_expected_visual_generation
    OR v_visual.visual_registry_release_id IS DISTINCT FROM p_expected_visual_release_id
    OR v_visual.manifest_sha256 IS DISTINCT FROM p_expected_visual_manifest_sha256 THEN
    v_reason := 'STALE_VISUAL_CURRENT_CAS';
  ELSE
    SELECT * INTO v_target FROM release.visual_registry_release r
      WHERE r.visual_registry_release_id = p_target_visual_release_id;
    IF NOT FOUND OR v_target.release_state <> 'sealed' THEN
      v_reason := 'UNSEALED_VISUAL_CURRENT_TARGET';
    ELSIF NOT EXISTS (
      SELECT 1 FROM release.visual_registry_verification v
      WHERE v.visual_registry_release_id = v_target.visual_registry_release_id
        AND v.manifest_sha256 = v_target.manifest_sha256 AND v.verified
    ) THEN v_reason := 'UNVERIFIED_VISUAL_CURRENT_TARGET';
    ELSIF v_target.compatible_research_release_id IS DISTINCT FROM v_research.research_release_id
      OR v_target.compatible_research_manifest_sha256 IS DISTINCT FROM v_research.manifest_sha256 THEN
      v_reason := 'RELEASE_VERSION_MISMATCH'; END IF;
  END IF;
  IF v_reason IS NOT NULL THEN
    INSERT INTO audit.visual_cas_attempt VALUES (
      p_attempt_id, p_visual_channel, COALESCE(p_expected_visual_generation, -1),
      v_visual.generation, p_target_visual_release_id, v_research.research_release_id,
      false, v_reason, session_user::text, clock_timestamp());
    RETURN QUERY SELECT false, v_reason, v_visual.generation; RETURN;
  END IF;
  UPDATE release.visual_current_pointer SET generation = generation + 1,
    visual_registry_release_id = v_target.visual_registry_release_id,
    manifest_sha256 = v_target.manifest_sha256, updated_at = clock_timestamp()
  WHERE channel = p_visual_channel;
  IF EXISTS (
    SELECT 1 FROM release.public_channel c WHERE c.channel = p_visual_channel
  ) THEN
    INSERT INTO release.visual_publication_history (
      channel, visual_registry_release_id, manifest_sha256,
      promoted_generation, published_at
    ) VALUES (
      p_visual_channel, v_target.visual_registry_release_id,
      v_target.manifest_sha256, v_visual.generation + 1,
      clock_timestamp()
    );
  END IF;
  INSERT INTO audit.visual_cas_attempt VALUES (
    p_attempt_id, p_visual_channel, p_expected_visual_generation,
    v_visual.generation, p_target_visual_release_id, v_research.research_release_id,
    true, 'PROMOTED', session_user::text, clock_timestamp());
  RETURN QUERY SELECT true, 'PROMOTED'::text, v_visual.generation + 1;
END
$function$;

RESET ROLE;
