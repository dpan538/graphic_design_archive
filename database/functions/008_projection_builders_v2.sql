\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

CREATE FUNCTION release.require_research_draft(p_release_id uuid)
RETURNS void
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM 1
  FROM release.research_release r
  WHERE r.research_release_id = p_release_id
    AND r.release_state = 'draft'
  FOR SHARE;
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '55000',
      MESSAGE = 'RESEARCH_DRAFT_REQUIRED';
  END IF;
END
$function$;

CREATE FUNCTION release.require_visual_draft(p_registry_id uuid)
RETURNS void
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM 1
  FROM release.visual_registry_release r
  WHERE r.visual_registry_release_id = p_registry_id
    AND r.release_state = 'draft'
  FOR SHARE;
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '55000',
      MESSAGE = 'VISUAL_REGISTRY_DRAFT_REQUIRED';
  END IF;
END
$function$;

CREATE FUNCTION release.evidence_snapshot_sha(p_evidence_item_id uuid)
RETURNS core.sha256_hex
LANGUAGE sql
STABLE STRICT
SET search_path = pg_catalog
SET TimeZone = 'UTC'
RETURN release.canonical_jsonb_sha256((
  SELECT to_jsonb(e)
  FROM provenance.evidence_item e
  WHERE e.evidence_item_id = p_evidence_item_id
));

CREATE FUNCTION release.analysis_run_snapshot_sha(p_analysis_run_id uuid)
RETURNS core.sha256_hex
LANGUAGE sql
STABLE STRICT
SET search_path = pg_catalog
SET TimeZone = 'UTC'
RETURN release.canonical_jsonb_sha256((
  SELECT release.analysis_run_manifest_json(to_jsonb(a))
  FROM research.analysis_run a
  WHERE a.analysis_run_id = p_analysis_run_id
));

CREATE OR REPLACE FUNCTION release.add_research_claim_to_draft(
  p_release_id uuid, p_claim_revision_id uuid
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
SET TimeZone = 'UTC'
AS $function$
DECLARE
  v_decision_id uuid;
  v_analysis_run_id uuid;
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_research_draft(p_release_id);

  SELECT d.claim_review_decision_id, cr.analysis_run_id
  INTO STRICT v_decision_id, v_analysis_run_id
  FROM research.claim_revision cr
  JOIN research.epistemic_class ec
    ON ec.epistemic_class_id = cr.epistemic_class_id
   AND ec.active
  JOIN research.claim_review_decision d
    ON d.claim_revision_id = cr.claim_revision_id
   AND d.outcome = 'accept'
  WHERE cr.claim_revision_id = p_claim_revision_id
    AND cr.status = 'accepted'
    AND cr.workflow_state = 'resolved'
    AND NOT EXISTS (
      SELECT 1 FROM research.claim_revision newer
      WHERE newer.supersedes_claim_revision_id = cr.claim_revision_id)
    AND NOT EXISTS (
      SELECT 1 FROM research.claim_review_decision newer
      WHERE newer.supersedes_decision_id = d.claim_review_decision_id);

  IF v_analysis_run_id IS NOT NULL THEN
    INSERT INTO release.research_release_analysis_run (
      research_release_id, analysis_run_id, method_version,
      software_sha256, parameters_sha256,
      input_research_release_id, input_research_manifest_sha256,
      input_corpus_version_id, input_corpus_policy_sha256,
      score_value, score_unit, uncertainty_lower, uncertainty_upper,
      threshold_value, threshold_unit, output_sha256, run_snapshot_sha256
    )
    SELECT p_release_id, a.analysis_run_id, a.method_version,
      a.software_sha256, a.parameters_sha256,
      a.input_release_id, a.input_manifest_sha256,
      a.input_corpus_version_id, a.input_corpus_policy_sha256,
      a.score_value, a.score_unit, a.uncertainty_lower,
      a.uncertainty_upper, a.threshold_value, a.threshold_unit,
      a.output_sha256, release.analysis_run_snapshot_sha(a.analysis_run_id)
    FROM research.analysis_run a
    WHERE a.analysis_run_id = v_analysis_run_id
    ON CONFLICT (research_release_id, analysis_run_id) DO NOTHING;
  END IF;

  INSERT INTO release.research_release_claim (
    research_release_id, claim_id, claim_revision_id,
    claim_urn, epistemic_code, wording,
    claimant_agent_id, claimant_label,
    claim_date_or_version, claim_stance,
    temporal_qualifier_id, temporal_qualifier_snapshot,
    spatial_qualifier_id, spatial_qualifier_snapshot,
    analysis_run_id, analysis_run_snapshot_sha256,
    claim_review_decision_id, epistemic_profile_version
  )
  SELECT p_release_id, c.claim_id, cr.claim_revision_id,
    c.claim_urn, ec.class_code, cr.wording,
    cr.claimant_agent_id, a.preferred_name,
    cr.claim_date_or_version, cr.claim_stance,
    cr.temporal_qualifier_id,
    CASE WHEN te.temporal_extent_id IS NULL THEN NULL
      ELSE release.jcs_text(to_jsonb(te)) END,
    cr.spatial_qualifier_id,
    CASE WHEN p.place_id IS NULL THEN NULL
      ELSE release.jcs_text(to_jsonb(p)) END,
    cr.analysis_run_id,
    CASE WHEN cr.analysis_run_id IS NULL THEN NULL
      ELSE release.analysis_run_snapshot_sha(cr.analysis_run_id) END,
    v_decision_id, ec.profile_version
  FROM research.claim_revision cr
  JOIN research.claim c ON c.claim_id = cr.claim_id
  JOIN research.epistemic_class ec
    ON ec.epistemic_class_id = cr.epistemic_class_id
  LEFT JOIN core.agent a ON a.agent_id = cr.claimant_agent_id
  LEFT JOIN core.temporal_extent te
    ON te.temporal_extent_id = cr.temporal_qualifier_id
  LEFT JOIN core.place p ON p.place_id = cr.spatial_qualifier_id
  WHERE cr.claim_revision_id = p_claim_revision_id;

  INSERT INTO release.research_release_claim_evidence (
    research_release_id, claim_revision_id, evidence_item_id,
    evidence_role, source_version_id, source_record_id,
    locator_scheme, locator_value, span_start, span_end,
    content_sha256, stable_citation, evidence_snapshot_sha256,
    source_asset_id
  )
  SELECT p_release_id, p_claim_revision_id, e.evidence_item_id,
    src.evidence_role, e.source_version_id, e.source_record_id,
    COALESCE(e.locator_scheme, 'none'), e.internal_locator,
    e.span_start, e.span_end, e.content_sha256, e.stable_citation,
    release.evidence_snapshot_sha(e.evidence_item_id), e.source_asset_id
  FROM (
    SELECT ce.evidence_item_id, ce.evidence_role
    FROM research.claim_evidence ce
    WHERE ce.claim_revision_id = p_claim_revision_id
    UNION
    SELECT de.evidence_item_id, de.evidence_role
    FROM research.claim_decision_evidence de
    WHERE de.claim_review_decision_id = v_decision_id
  ) src
  JOIN provenance.evidence_item e
    ON e.evidence_item_id = src.evidence_item_id;
END
$function$;

CREATE OR REPLACE FUNCTION release.add_research_relation_to_draft(
  p_release_id uuid, p_semantic_relation_id uuid,
  p_supporting_claim_revision_id uuid
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
SET TimeZone = 'UTC'
AS $function$
DECLARE
  v_basis research.relation_acceptance_basis;
  v_decision_id uuid;
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_research_draft(p_release_id);

  IF p_supporting_claim_revision_id IS NOT NULL THEN
    IF NOT EXISTS (
      SELECT 1 FROM release.research_release_claim c
      WHERE c.research_release_id = p_release_id
        AND c.claim_revision_id = p_supporting_claim_revision_id
    ) THEN
      RAISE EXCEPTION USING ERRCODE = '23514',
        MESSAGE = 'SUPPORTING_CLAIM_MUST_BE_COPIED_FIRST';
    END IF;
    v_basis := 'accepted_claim';
  ELSE
    SELECT d.relation_review_decision_id
    INTO STRICT v_decision_id
    FROM research.relation_review_decision d
    WHERE d.semantic_relation_id = p_semantic_relation_id
      AND d.outcome = 'accept'
      AND NOT EXISTS (
        SELECT 1 FROM research.relation_review_decision newer
        WHERE newer.supersedes_decision_id = d.relation_review_decision_id)
      AND EXISTS (
        SELECT 1 FROM research.relation_decision_evidence de
        WHERE de.relation_review_decision_id = d.relation_review_decision_id
          AND de.evidence_role = 'supports');
    v_basis := 'curator_decision';
  END IF;

  INSERT INTO release.research_release_relation (
    research_release_id, semantic_relation_id, relation_urn,
    relation_code, subject_entity_id, object_entity_id,
    acceptance_basis, supporting_claim_revision_id,
    supporting_decision_id, epistemic_code,
    relation_type_id, relation_evidence_profile_version,
    temporal_qualifier_id, temporal_qualifier_snapshot,
    spatial_qualifier_id, spatial_qualifier_snapshot
  )
  SELECT p_release_id, sr.semantic_relation_id, sr.relation_urn,
    rt.relation_code, se.entity_id, oe.entity_id,
    v_basis, p_supporting_claim_revision_id, v_decision_id,
    CASE WHEN v_basis = 'accepted_claim' THEN rc.epistemic_code ELSE NULL END,
    rt.relation_type_id, rt.evidence_profile_version,
    sr.temporal_qualifier_id,
    CASE WHEN te.temporal_extent_id IS NULL THEN NULL
      ELSE release.jcs_text(to_jsonb(te)) END,
    sr.spatial_qualifier_id,
    CASE WHEN p.place_id IS NULL THEN NULL
      ELSE release.jcs_text(to_jsonb(p)) END
  FROM research.semantic_relation sr
  JOIN research.relation_type rt
    ON rt.relation_type_id = sr.relation_type_id AND rt.active
  JOIN research.relation_endpoint_entity se
    ON se.relation_endpoint_id = sr.subject_endpoint_id
  JOIN research.relation_endpoint_entity oe
    ON oe.relation_endpoint_id = sr.object_endpoint_id
  LEFT JOIN release.research_release_claim rc
    ON rc.research_release_id = p_release_id
   AND rc.claim_revision_id = p_supporting_claim_revision_id
  LEFT JOIN research.relation_claim rcl
    ON rcl.semantic_relation_id = sr.semantic_relation_id
   AND rcl.claim_revision_id = p_supporting_claim_revision_id
   AND rcl.claim_role = 'supports'
  LEFT JOIN core.temporal_extent te
    ON te.temporal_extent_id = sr.temporal_qualifier_id
  LEFT JOIN core.place p ON p.place_id = sr.spatial_qualifier_id
  WHERE sr.semantic_relation_id = p_semantic_relation_id
    AND sr.status = 'accepted'
    AND sr.origin <> 'legacy_projection_only'
    AND (v_basis = 'curator_decision' OR rcl.semantic_relation_id IS NOT NULL);
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'ONLY_ACCEPTED_TYPED_EVIDENCE_BOUND_RELATION_CAN_BE_COPIED';
  END IF;

  INSERT INTO release.research_release_relation_evidence (
    research_release_id, semantic_relation_id, evidence_item_id,
    evidence_role, evidence_basis, stable_citation,
    locator_value, content_sha256, evidence_snapshot_sha256,
    source_asset_id, source_version_id, source_record_id
  )
  SELECT p_release_id, p_semantic_relation_id, e.evidence_item_id,
    src.evidence_role, v_basis, e.stable_citation,
    e.internal_locator, e.content_sha256,
    release.evidence_snapshot_sha(e.evidence_item_id),
    e.source_asset_id, e.source_version_id, e.source_record_id
  FROM (
    SELECT ce.evidence_item_id, ce.evidence_role
    FROM research.claim_evidence ce
    WHERE v_basis = 'accepted_claim'
      AND ce.claim_revision_id = p_supporting_claim_revision_id
    UNION
    SELECT de.evidence_item_id, de.evidence_role
    FROM research.relation_decision_evidence de
    WHERE v_basis = 'curator_decision'
      AND de.relation_review_decision_id = v_decision_id
  ) src
  JOIN provenance.evidence_item e
    ON e.evidence_item_id = src.evidence_item_id;
END
$function$;

CREATE OR REPLACE FUNCTION release.add_trace_node_to_draft(
  p_release_id uuid, p_corpus_version_id uuid,
  p_trace_node_id uuid, p_archive_object_id uuid
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_research_draft(p_release_id);
  INSERT INTO release.trace_projection_node (
    research_release_id, corpus_version_id, trace_node_id,
    archive_object_id, canonical_key, label,
    entity_id, node_type, evidence_item_id
  )
  SELECT p_release_id, p_corpus_version_id, n.trace_node_id,
    p_archive_object_id, n.canonical_key, n.label,
    n.entity_id, n.node_type, n.evidence_item_id
  FROM research.trace_node n
  WHERE n.trace_node_id = p_trace_node_id
    AND EXISTS (
      SELECT 1 FROM release.research_corpus_snapshot c
      WHERE c.research_release_id = p_release_id
        AND c.corpus_version_id = p_corpus_version_id)
    AND (
      (p_archive_object_id IS NULL)
      OR
      (n.entity_id = p_archive_object_id AND EXISTS (
        SELECT 1 FROM research.object_trace_node x
        WHERE x.trace_node_id = n.trace_node_id
          AND x.archive_object_id = p_archive_object_id))
    );
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'TRACE_NODE_COPY_SOURCE_MISMATCH';
  END IF;
END
$function$;

RESET ROLE;
