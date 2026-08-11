\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

CREATE FUNCTION rights.machine_reason_for_rule(p_rule rights.delivery_rule_id)
RETURNS rights.delivery_reason_code
LANGUAGE sql IMMUTABLE STRICT
SET search_path=pg_catalog
RETURN CASE p_rule
  WHEN 'RD-001' THEN 'ACTIVE_TAKEDOWN_BLOCK'::rights.delivery_reason_code
  WHEN 'RD-002' THEN 'ACTIVE_TAKEDOWN_CITATION_ONLY'::rights.delivery_reason_code
  WHEN 'RD-010' THEN 'RIGHTS_PROHIBIT_LOCATOR'::rights.delivery_reason_code
  WHEN 'RD-011' THEN 'POLICY_PROHIBITS_PUBLIC_LOCATOR'::rights.delivery_reason_code
  WHEN 'RD-020' THEN 'RIGHTS_FAIL_CLOSED_LINK'::rights.delivery_reason_code
  WHEN 'RD-021' THEN 'RIGHTS_FAIL_CLOSED_CITATION'::rights.delivery_reason_code
  WHEN 'RD-030' THEN 'POLICY_FAIL_CLOSED_CITATION'::rights.delivery_reason_code
  WHEN 'RD-040' THEN 'RIGHTS_CAP_LINK_ONLY'::rights.delivery_reason_code
  WHEN 'RD-041' THEN 'LINK_ENDPOINT_UNQUALIFIED'::rights.delivery_reason_code
  WHEN 'RD-050' THEN 'POLICY_CAP_SOURCE_VIEWER'::rights.delivery_reason_code
  WHEN 'RD-051' THEN 'VIEWER_ENDPOINT_DOWNGRADE_LINK'::rights.delivery_reason_code
  WHEN 'RD-052' THEN 'VIEWER_ENDPOINT_DOWNGRADE_CITATION'::rights.delivery_reason_code
  WHEN 'RD-060' THEN 'POLICY_CAP_LINK_ONLY'::rights.delivery_reason_code
  WHEN 'RD-061' THEN 'POLICY_LINK_UNAVAILABLE'::rights.delivery_reason_code
  WHEN 'RD-070' THEN 'ATTRIBUTION_FAIL_CLOSED_LINK'::rights.delivery_reason_code
  WHEN 'RD-071' THEN 'ATTRIBUTION_FAIL_CLOSED_CITATION'::rights.delivery_reason_code
  WHEN 'RD-080' THEN 'REMOTE_IMAGE_ALL_GATES_PASS'::rights.delivery_reason_code
  WHEN 'RD-081' THEN 'REMOTE_ENDPOINT_DOWNGRADE_LINK'::rights.delivery_reason_code
  WHEN 'RD-082' THEN 'REMOTE_ENDPOINT_DOWNGRADE_CITATION'::rights.delivery_reason_code
  ELSE 'FAIL_CLOSED_DEFAULT'::rights.delivery_reason_code
END;

ALTER FUNCTION release.compute_research_candidate_fingerprint(uuid)
  RENAME TO compute_research_candidate_fingerprint_v1;

CREATE FUNCTION release.compute_research_candidate_fingerprint(p_release_id uuid)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path=pg_catalog
SET TimeZone='UTC'
RETURN encode(sha256(release.jcs_bytes(jsonb_build_object(
  'format','gda-v49-research-candidate-physical-v2',
  'legacyCoreFingerprint',release.compute_research_candidate_fingerprint_v1(p_release_id),
  'release',(SELECT to_jsonb(r)-ARRAY[
      'release_state','candidate_fingerprint','manifest_sha256',
      'candidate_at','validated_at','sealed_at']
    FROM release.research_release r WHERE r.research_release_id=p_release_id),
  'sourceLineage',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.source_role)
    FROM release.research_source_lineage x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'projectionSet',(SELECT to_jsonb(x) FROM release.research_projection_set x WHERE x.research_release_id=p_release_id),
  'registrySnapshot',(SELECT to_jsonb(x) FROM release.research_registry_snapshot x WHERE x.research_release_id=p_release_id),
  'corpusSnapshots',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.corpus_version_id)
    FROM release.research_corpus_snapshot x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'countSnapshots',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.metric_code)
    FROM release.research_count_snapshot x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'objects',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.archive_object_id)
    FROM release.research_release_object x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'corpusMembers',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.corpus_version_id,x.archive_object_id)
    FROM release.research_release_corpus_member x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'claims',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.claim_id)
    FROM release.research_release_claim x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'claimEvidence',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.claim_revision_id,x.evidence_item_id,x.evidence_role)
    FROM release.research_release_claim_evidence x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'analysisRuns',COALESCE((SELECT jsonb_agg(
      release.analysis_run_manifest_json(to_jsonb(x))
      ORDER BY x.analysis_run_id)
    FROM release.research_release_analysis_run x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'relations',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.semantic_relation_id)
    FROM release.research_release_relation x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'relationEvidence',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.semantic_relation_id,x.evidence_item_id,x.evidence_role,x.evidence_basis)
    FROM release.research_release_relation_evidence x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'traceNodes',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.corpus_version_id,x.trace_node_id)
    FROM release.trace_projection_node x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'traceTrees',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.corpus_version_id,x.trace_tree_id)
    FROM release.trace_tree_projection x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'traceBranches',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.corpus_version_id,x.trace_tree_id,x.trace_branch_id)
    FROM release.trace_branch_projection x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'traceNodePlacements',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.corpus_version_id,x.trace_node_id,x.trace_tree_id,x.trace_branch_id,x.placement_role)
    FROM release.trace_node_tree_placement x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'traceEdges',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.corpus_version_id,x.subject_trace_node_id,x.semantic_relation_id,x.object_trace_node_id,x.projection_role)
    FROM release.trace_projection_edge x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'traceEdgePlacements',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.corpus_version_id,x.subject_trace_node_id,x.semantic_relation_id,x.object_trace_node_id,x.projection_role,x.trace_tree_id,x.trace_branch_id)
    FROM release.trace_edge_tree_placement x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'memberships',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.corpus_version_id,x.archive_object_id,x.semantic_relation_id,x.membership_role,x.metric_code)
    FROM release.object_relation_membership_projection x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'metrics',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.archive_object_id,x.metric_code)
    FROM release.research_object_metric_eligibility x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'legacyResolutions',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.legacy_identity_id)
    FROM release.research_legacy_identity_resolution x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'legacySplitSuccessors',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.legacy_identity_resolution_id,x.successor_ordinal)
    FROM release.research_legacy_identity_split_successor x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'folders',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.folder_id)
    FROM release.research_folder_projection x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'assets',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.deterministic_sort_key,x.relative_path)
    FROM release.research_asset x WHERE x.research_release_id=p_release_id),'[]'::jsonb),
  'assetDependencies',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.asset_path,x.dependency_path)
    FROM release.research_asset_dependency x WHERE x.research_release_id=p_release_id),'[]'::jsonb)
))),'hex')::core.sha256_hex;

ALTER FUNCTION release.compute_visual_candidate_fingerprint(uuid)
  RENAME TO compute_visual_candidate_fingerprint_v1;

CREATE FUNCTION release.compute_visual_candidate_fingerprint(p_registry_id uuid)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path=pg_catalog
SET TimeZone='UTC'
RETURN encode(sha256(release.jcs_bytes(jsonb_build_object(
  'format','gda-v49-visual-candidate-physical-v2',
  'legacyCoreFingerprint',release.compute_visual_candidate_fingerprint_v1(p_registry_id),
  'release',(SELECT to_jsonb(r)-ARRAY[
      'release_state','candidate_fingerprint','manifest_sha256',
      'candidate_at','validated_at','sealed_at']
    FROM release.visual_registry_release r WHERE r.visual_registry_release_id=p_registry_id),
  'policyInput',(SELECT to_jsonb(x) FROM release.visual_registry_policy_input x WHERE x.visual_registry_release_id=p_registry_id),
  'legacyDisposition',(SELECT to_jsonb(x) FROM release.visual_registry_legacy_disposition_snapshot x WHERE x.visual_registry_release_id=p_registry_id),
  'providers',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.provider_id) FROM release.visual_registry_provider_snapshot x WHERE x.visual_registry_release_id=p_registry_id),'[]'::jsonb),
  'providerObjects',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.provider_object_id) FROM release.visual_registry_provider_object_snapshot x WHERE x.visual_registry_release_id=p_registry_id),'[]'::jsonb),
  'references',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.external_visual_reference_id) FROM release.visual_registry_reference_snapshot x WHERE x.visual_registry_release_id=p_registry_id),'[]'::jsonb),
  'bridges',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.object_visual_reference_id) FROM release.visual_registry_bridge_snapshot x WHERE x.visual_registry_release_id=p_registry_id),'[]'::jsonb),
  'rightsAssessments',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.rights_assessment_id) FROM release.visual_registry_rights_assessment_snapshot x WHERE x.visual_registry_release_id=p_registry_id),'[]'::jsonb),
  'rightsObservations',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.rights_assessment_id,x.rights_observation_id,x.evidence_role) FROM release.visual_registry_rights_observation_snapshot x WHERE x.visual_registry_release_id=p_registry_id),'[]'::jsonb),
  'policyVersions',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.provider_policy_version_id) FROM release.visual_registry_policy_version_snapshot x WHERE x.visual_registry_release_id=p_registry_id),'[]'::jsonb),
  'policyEvaluations',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.provider_policy_evaluation_id) FROM release.visual_registry_policy_evaluation_snapshot x WHERE x.visual_registry_release_id=p_registry_id),'[]'::jsonb),
  'policyLinks',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.provider_policy_evaluation_id,x.provider_policy_version_id) FROM release.visual_registry_policy_evaluation_version_snapshot x WHERE x.visual_registry_release_id=p_registry_id),'[]'::jsonb),
  'deliveries',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.delivery_assessment_id) FROM release.visual_registry_delivery_snapshot x WHERE x.visual_registry_release_id=p_registry_id),'[]'::jsonb),
  'deliveryRights',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.delivery_assessment_id,x.rights_assessment_id,x.evidence_role) FROM release.visual_registry_delivery_rights_snapshot x WHERE x.visual_registry_release_id=p_registry_id),'[]'::jsonb),
  'deliveryPolicies',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.delivery_assessment_id,x.provider_policy_evaluation_id) FROM release.visual_registry_delivery_policy_snapshot x WHERE x.visual_registry_release_id=p_registry_id),'[]'::jsonb),
  'entries',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.visual_registry_entry_id) FROM release.visual_registry_entry x WHERE x.visual_registry_release_id=p_registry_id),'[]'::jsonb),
  'attribution',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.visual_registry_entry_id,x.value_kind,x.value_ordinal) FROM release.visual_registry_attribution_value x WHERE x.visual_registry_release_id=p_registry_id),'[]'::jsonb),
  'locators',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.visual_registry_entry_id,x.locator_role,x.locator_ordinal) FROM release.visual_registry_public_locator x WHERE x.visual_registry_release_id=p_registry_id),'[]'::jsonb),
  'takedowns',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.visual_registry_entry_id,x.takedown_override_id) FROM release.visual_registry_takedown_snapshot x WHERE x.visual_registry_release_id=p_registry_id),'[]'::jsonb),
  'assets',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.deterministic_sort_key,x.relative_path) FROM release.visual_registry_asset x WHERE x.visual_registry_release_id=p_registry_id),'[]'::jsonb),
  'assetDependencies',COALESCE((SELECT jsonb_agg(to_jsonb(x) ORDER BY x.asset_path,x.dependency_path) FROM release.visual_registry_asset_dependency x WHERE x.visual_registry_release_id=p_registry_id),'[]'::jsonb)
))),'hex')::core.sha256_hex;

ALTER FUNCTION release.validate_research_projection(uuid)
  RENAME TO validate_research_projection_v1;

CREATE FUNCTION release.assert_legacy_resolution_projection_complete(
  p_release_id uuid
)
RETURNS void LANGUAGE plpgsql STABLE
SET search_path=pg_catalog
AS $function$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM release.research_legacy_identity_resolution r
    WHERE r.research_release_id = p_release_id
      AND (
        (r.resolution_state = 'split' AND (
          (SELECT count(*)
           FROM release.research_legacy_identity_split_successor c
           WHERE c.research_release_id = r.research_release_id
             AND c.legacy_identity_resolution_id =
               r.legacy_identity_resolution_id) < 2
          OR EXISTS (
            SELECT s.successor_ordinal + 1,
              s.successor_archive_object_id
            FROM core.legacy_identity_split_successor s
            WHERE s.legacy_identity_resolution_id =
              r.legacy_identity_resolution_id
            EXCEPT
            SELECT c.successor_ordinal, c.successor_archive_object_id
            FROM release.research_legacy_identity_split_successor c
            WHERE c.research_release_id = r.research_release_id
              AND c.legacy_identity_resolution_id =
                r.legacy_identity_resolution_id
          )
          OR EXISTS (
            SELECT c.successor_ordinal, c.successor_archive_object_id
            FROM release.research_legacy_identity_split_successor c
            WHERE c.research_release_id = r.research_release_id
              AND c.legacy_identity_resolution_id =
                r.legacy_identity_resolution_id
            EXCEPT
            SELECT s.successor_ordinal + 1,
              s.successor_archive_object_id
            FROM core.legacy_identity_split_successor s
            WHERE s.legacy_identity_resolution_id =
              r.legacy_identity_resolution_id
          )
        ))
        OR (r.resolution_state <> 'split' AND EXISTS (
          SELECT 1
          FROM release.research_legacy_identity_split_successor c
          WHERE c.research_release_id = r.research_release_id
            AND c.legacy_identity_resolution_id =
              r.legacy_identity_resolution_id
        ))
      )
  ) THEN
    RAISE EXCEPTION USING ERRCODE='23514',
      MESSAGE='RESEARCH_LEGACY_SPLIT_PROJECTION_INCOMPLETE';
  END IF;
END
$function$;

CREATE FUNCTION release.validate_research_projection(p_release_id uuid)
RETURNS void LANGUAGE plpgsql SET search_path=pg_catalog
AS $function$
DECLARE v_stored core.sha256_hex; v_profile uuid;
BEGIN
  SELECT candidate_fingerprint,validation_profile_id INTO v_stored,v_profile
  FROM release.research_release WHERE research_release_id=p_release_id
    AND release_state IN ('candidate','validated','sealed') FOR SHARE;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='RESEARCH_RELEASE_NOT_VALIDATABLE'; END IF;
  PERFORM release.assert_validation_profile_complete(v_profile,'research');
  IF v_stored IS DISTINCT FROM release.compute_research_candidate_fingerprint(p_release_id) THEN
    RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='RESEARCH_CANDIDATE_FINGERPRINT_MISMATCH';
  END IF;
  IF (SELECT count(*) FROM release.research_source_lineage x WHERE x.research_release_id=p_release_id)<>5
    OR EXISTS (SELECT 1 FROM release.research_source_lineage x JOIN raw.source_asset a ON a.source_asset_id=x.source_asset_id WHERE x.research_release_id=p_release_id AND (x.asset_authority IS DISTINCT FROM a.authority OR x.asset_sha256 IS DISTINCT FROM a.sha256))
    OR NOT EXISTS (SELECT 1 FROM release.research_projection_set x WHERE x.research_release_id=p_release_id)
    OR NOT EXISTS (SELECT 1 FROM release.research_registry_snapshot x WHERE x.research_release_id=p_release_id)
    OR NOT EXISTS (SELECT 1 FROM release.research_count_snapshot x WHERE x.research_release_id=p_release_id)
    OR NOT EXISTS (SELECT 1 FROM release.research_asset x WHERE x.research_release_id=p_release_id) THEN
    RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='RESEARCH_REQUIRED_INVENTORY_OR_LINEAGE_MISSING';
  END IF;
  IF EXISTS (SELECT 1 FROM release.research_release_object x JOIN core.archive_object o ON o.archive_object_id=x.archive_object_id WHERE x.research_release_id=p_release_id AND x.object_urn IS DISTINCT FROM o.object_urn)
    OR EXISTS (SELECT 1 FROM release.research_release_corpus_member x LEFT JOIN research.corpus_membership m ON m.corpus_version_id=x.corpus_version_id AND m.archive_object_id=x.archive_object_id WHERE x.research_release_id=p_release_id AND (m.archive_object_id IS NULL OR m.disposition IS DISTINCT FROM x.disposition OR m.reason_code IS DISTINCT FROM x.reason_code)) THEN
    RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='RESEARCH_OBJECT_OR_CORPUS_COPY_MISMATCH';
  END IF;
  IF EXISTS (
    SELECT 1 FROM release.research_release_claim x
    JOIN research.claim_revision c ON c.claim_revision_id=x.claim_revision_id
    JOIN research.claim q ON q.claim_id=c.claim_id
    JOIN research.epistemic_class e ON e.epistemic_class_id=c.epistemic_class_id
    LEFT JOIN research.claim_review_decision d ON d.claim_review_decision_id=x.claim_review_decision_id
    WHERE x.research_release_id=p_release_id AND (
      c.status<>'accepted' OR NOT e.active OR q.claim_urn IS DISTINCT FROM x.claim_urn
      OR c.wording IS DISTINCT FROM x.wording OR e.class_code IS DISTINCT FROM x.epistemic_code
      OR e.profile_version IS DISTINCT FROM x.epistemic_profile_version
      OR d.claim_revision_id IS DISTINCT FROM c.claim_revision_id OR d.outcome<>'accept'
      OR EXISTS (SELECT 1 FROM research.claim_review_decision n WHERE n.supersedes_decision_id=d.claim_review_decision_id)
      OR EXISTS (SELECT 1 FROM research.claim_revision n WHERE n.supersedes_claim_revision_id=c.claim_revision_id)
      OR NOT EXISTS (SELECT 1 FROM release.research_release_claim_evidence ce WHERE ce.research_release_id=x.research_release_id AND ce.claim_revision_id=x.claim_revision_id AND ce.evidence_role='supports')
      OR (e.requires_analysis_run AND NOT EXISTS (SELECT 1 FROM release.research_release_analysis_run ar WHERE ar.research_release_id=x.research_release_id AND ar.analysis_run_id=x.analysis_run_id)))) THEN
    RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='RESEARCH_CLAIM_COPY_NOT_CURRENT_ACCEPTED_OR_COMPLETE';
  END IF;
  IF EXISTS (
    SELECT 1 FROM release.research_release_relation x
    JOIN research.semantic_relation r ON r.semantic_relation_id=x.semantic_relation_id
    JOIN research.relation_type t ON t.relation_type_id=r.relation_type_id
    JOIN research.relation_endpoint_entity se ON se.relation_endpoint_id=r.subject_endpoint_id
    JOIN research.relation_endpoint_entity oe ON oe.relation_endpoint_id=r.object_endpoint_id
    WHERE x.research_release_id=p_release_id AND (
      r.status<>'accepted' OR r.origin='legacy_projection_only' OR NOT t.active
      OR t.relation_type_id IS DISTINCT FROM x.relation_type_id
      OR t.evidence_profile_version IS DISTINCT FROM x.relation_evidence_profile_version
      OR se.entity_id IS DISTINCT FROM x.subject_entity_id OR oe.entity_id IS DISTINCT FROM x.object_entity_id
      OR NOT EXISTS (SELECT 1 FROM release.research_release_relation_evidence re WHERE re.research_release_id=x.research_release_id AND re.semantic_relation_id=x.semantic_relation_id AND re.evidence_role='supports'))) THEN
    RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='RESEARCH_RELATION_COPY_NOT_ACCEPTED_TYPED_OR_EVIDENCED';
  END IF;
  IF EXISTS (
    SELECT 1 FROM release.trace_projection_node x JOIN research.trace_node n ON n.trace_node_id=x.trace_node_id
    WHERE x.research_release_id=p_release_id AND (x.canonical_key IS DISTINCT FROM n.canonical_key OR x.label IS DISTINCT FROM n.label OR x.entity_id IS DISTINCT FROM n.entity_id OR x.node_type IS DISTINCT FROM n.node_type OR x.evidence_item_id IS DISTINCT FROM n.evidence_item_id))
    OR EXISTS (
      SELECT 1 FROM release.trace_projection_edge e
      JOIN release.trace_projection_node s ON s.research_release_id=e.research_release_id AND s.corpus_version_id=e.corpus_version_id AND s.trace_node_id=e.subject_trace_node_id
      JOIN release.trace_projection_node o ON o.research_release_id=e.research_release_id AND o.corpus_version_id=e.corpus_version_id AND o.trace_node_id=e.object_trace_node_id
      JOIN release.research_release_relation r ON r.research_release_id=e.research_release_id AND r.semantic_relation_id=e.semantic_relation_id
      WHERE e.research_release_id=p_release_id AND (s.entity_id IS NULL OR o.entity_id IS NULL OR s.entity_id IS DISTINCT FROM r.subject_entity_id OR o.entity_id IS DISTINCT FROM r.object_entity_id OR e.generation_key IS DISTINCT FROM release.trace_edge_generation_key(e.research_release_id,e.corpus_version_id,e.subject_trace_node_id,e.semantic_relation_id,e.object_trace_node_id,e.projection_role))) THEN
    RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='TRACE_TYPED_TOPOLOGY_OR_GENERATION_MISMATCH';
  END IF;
  IF EXISTS (SELECT 1 FROM release.trace_edge_tree_placement p WHERE p.research_release_id=p_release_id AND NOT EXISTS (SELECT 1 FROM release.trace_node_tree_placement n WHERE n.research_release_id=p.research_release_id AND n.corpus_version_id=p.corpus_version_id AND n.trace_node_id=p.subject_trace_node_id AND n.trace_tree_id=p.trace_tree_id AND n.trace_branch_id=p.trace_branch_id)) THEN
    RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='TRACE_EDGE_PLACEMENT_WITHOUT_SUBJECT_NODE_PLACEMENT';
  END IF;
  PERFORM release.assert_legacy_resolution_projection_complete(p_release_id);
END
$function$;

ALTER FUNCTION release.validate_visual_projection(uuid)
  RENAME TO validate_visual_projection_v1;
CREATE FUNCTION release.validate_visual_projection(p_registry_id uuid)
RETURNS void LANGUAGE plpgsql SET search_path=pg_catalog
AS $function$
DECLARE v_profile uuid;
BEGIN
  PERFORM release.validate_visual_projection_v1(p_registry_id);
  SELECT validation_profile_id INTO v_profile FROM release.visual_registry_release
  WHERE visual_registry_release_id=p_registry_id;
  PERFORM release.assert_validation_profile_complete(v_profile,'visual');
  IF NOT EXISTS (SELECT 1 FROM release.visual_registry_policy_input x WHERE x.visual_registry_release_id=p_registry_id)
    OR NOT EXISTS (SELECT 1 FROM release.visual_registry_legacy_disposition_snapshot x WHERE x.visual_registry_release_id=p_registry_id AND x.unclassified_surface_count=0)
    OR NOT EXISTS (SELECT 1 FROM release.visual_registry_asset x WHERE x.visual_registry_release_id=p_registry_id)
    OR EXISTS (SELECT 1 FROM release.visual_registry_delivery_snapshot x WHERE x.visual_registry_release_id=p_registry_id AND x.machine_reason_code IS DISTINCT FROM rights.machine_reason_for_rule(x.reason_code))
    OR EXISTS (SELECT 1 FROM release.visual_registry_entry x WHERE x.visual_registry_release_id=p_registry_id AND x.machine_reason_code IS DISTINCT FROM rights.machine_reason_for_rule(x.reason_code))
    OR EXISTS (SELECT 1 FROM release.visual_registry_policy_version_snapshot x JOIN rights.provider_policy_version p ON p.provider_policy_version_id=x.provider_policy_version_id WHERE x.visual_registry_release_id=p_registry_id AND (x.policy_scope_id IS DISTINCT FROM p.policy_scope_id OR x.source_evidence_item_id IS DISTINCT FROM p.source_evidence_item_id)) THEN
    RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='VISUAL_REQUIRED_POLICY_BASELINE_INVENTORY_OR_REASON_MISMATCH';
  END IF;
END
$function$;

CREATE FUNCTION release.build_validation_receipt_bytes(
  p_boundary release.boundary_kind, p_release_id uuid,
  p_kind release.validation_receipt_kind,
  p_verifier_version core.release_token, p_evidence_sha256 core.sha256_hex
)
RETURNS bytea LANGUAGE sql STABLE SET search_path=pg_catalog
RETURN release.jcs_bytes(jsonb_build_object(
  'boundary',p_boundary::text,
  'candidateFingerprint',CASE p_boundary WHEN 'research' THEN
    (SELECT candidate_fingerprint FROM release.research_release WHERE research_release_id=p_release_id)
    ELSE (SELECT candidate_fingerprint FROM release.visual_registry_release WHERE visual_registry_release_id=p_release_id) END,
  'evidenceSha256',p_evidence_sha256,
  'receiptKind',p_kind::text,
  'releaseId',p_release_id::text,
  'result','pass',
  'verifierVersion',p_verifier_version::text
));

ALTER FUNCTION release.build_validation_receipt_bytes(
  release.boundary_kind, uuid, release.validation_receipt_kind,
  core.release_token, core.sha256_hex
) SECURITY DEFINER;

CREATE FUNCTION release.record_research_validation_receipt(
  p_receipt_id uuid,p_release_id uuid,p_kind release.validation_receipt_kind,
  p_verifier_version core.release_token,p_evidence_sha256 core.sha256_hex,
  p_receipt_bytes bytea,p_audit_event_id uuid
)
RETURNS core.sha256_hex LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog
AS $function$
DECLARE v_expected bytea;v_sha core.sha256_hex;v_fingerprint core.sha256_hex;v_now timestamptz:=clock_timestamp();
BEGIN
  PERFORM rights.require_reviewer();
  SELECT candidate_fingerprint INTO v_fingerprint FROM release.research_release
  WHERE research_release_id=p_release_id AND release_state='candidate' FOR SHARE;
  IF NOT FOUND OR p_kind::text !~ '^research_' THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='RESEARCH_RECEIPT_REQUIRES_CANDIDATE_AND_RESEARCH_KIND';END IF;
  IF NOT EXISTS (SELECT 1 FROM release.validation_profile_requirement req JOIN release.research_release r ON r.validation_profile_id=req.validation_profile_id WHERE r.research_release_id=p_release_id AND req.receipt_kind=p_kind) THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='RECEIPT_KIND_NOT_REQUIRED_BY_PROFILE';END IF;
  v_expected:=release.build_validation_receipt_bytes('research',p_release_id,p_kind,p_verifier_version,p_evidence_sha256);
  IF p_receipt_bytes IS DISTINCT FROM v_expected THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='RESEARCH_RECEIPT_BYTES_NOT_CANONICAL_OR_BOUND';END IF;
  v_sha:=encode(sha256(p_receipt_bytes),'hex')::core.sha256_hex;
  INSERT INTO release.research_validation_receipt(
    research_validation_receipt_id,research_release_id,candidate_fingerprint,
    verifier_version,receipt_sha256,validation_result,checked_at,
    receipt_kind,receipt_bytes,byte_length)
  VALUES(p_receipt_id,p_release_id,v_fingerprint,p_verifier_version,v_sha,'pass',v_now,p_kind,p_receipt_bytes,octet_length(p_receipt_bytes));
  INSERT INTO audit.research_validation_receipt_event VALUES(
    p_audit_event_id,p_receipt_id,session_user::text,v_now,
    release.canonical_jsonb_sha256(jsonb_build_array(p_audit_event_id,p_receipt_id,session_user::text,(extract(epoch FROM v_now)*1000000)::bigint,v_sha)));
  RETURN v_sha;
END
$function$;

CREATE FUNCTION release.record_visual_validation_receipt(
  p_receipt_id uuid,p_registry_id uuid,p_kind release.validation_receipt_kind,
  p_verifier_version core.release_token,p_evidence_sha256 core.sha256_hex,
  p_receipt_bytes bytea,p_audit_event_id uuid
)
RETURNS core.sha256_hex LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog
AS $function$
DECLARE v_expected bytea;v_sha core.sha256_hex;v_fingerprint core.sha256_hex;v_now timestamptz:=clock_timestamp();
BEGIN
  PERFORM rights.require_reviewer();
  SELECT candidate_fingerprint INTO v_fingerprint FROM release.visual_registry_release
  WHERE visual_registry_release_id=p_registry_id AND release_state='candidate' FOR SHARE;
  IF NOT FOUND OR p_kind::text !~ '^visual_' THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='VISUAL_RECEIPT_REQUIRES_CANDIDATE_AND_VISUAL_KIND';END IF;
  IF NOT EXISTS (SELECT 1 FROM release.validation_profile_requirement req JOIN release.visual_registry_release r ON r.validation_profile_id=req.validation_profile_id WHERE r.visual_registry_release_id=p_registry_id AND req.receipt_kind=p_kind) THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='RECEIPT_KIND_NOT_REQUIRED_BY_PROFILE';END IF;
  v_expected:=release.build_validation_receipt_bytes('visual',p_registry_id,p_kind,p_verifier_version,p_evidence_sha256);
  IF p_receipt_bytes IS DISTINCT FROM v_expected THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='VISUAL_RECEIPT_BYTES_NOT_CANONICAL_OR_BOUND';END IF;
  v_sha:=encode(sha256(p_receipt_bytes),'hex')::core.sha256_hex;
  INSERT INTO release.visual_validation_receipt(
    visual_validation_receipt_id,visual_registry_release_id,candidate_fingerprint,
    verifier_version,receipt_sha256,validation_result,checked_at,
    receipt_kind,receipt_bytes,byte_length)
  VALUES(p_receipt_id,p_registry_id,v_fingerprint,p_verifier_version,v_sha,'pass',v_now,p_kind,p_receipt_bytes,octet_length(p_receipt_bytes));
  INSERT INTO audit.visual_validation_receipt_event VALUES(
    p_audit_event_id,p_receipt_id,session_user::text,v_now,
    release.canonical_jsonb_sha256(jsonb_build_array(p_audit_event_id,p_receipt_id,session_user::text,(extract(epoch FROM v_now)*1000000)::bigint,v_sha)));
  RETURN v_sha;
END
$function$;

CREATE OR REPLACE FUNCTION release.build_research_manifest_bytes(p_release_id uuid)
RETURNS bytea LANGUAGE sql STABLE SET search_path=pg_catalog SET TimeZone='UTC'
RETURN release.jcs_bytes((SELECT jsonb_build_object(
  'assets',COALESCE((SELECT jsonb_agg(jsonb_build_object('byteLength',a.byte_length,'mediaType',a.media_type,'path',a.relative_path,'recordCount',a.record_count,'sha256',a.sha256) ORDER BY a.deterministic_sort_key,a.relative_path) FROM release.research_asset a WHERE a.research_release_id=r.research_release_id),'[]'::jsonb),
  'candidateFingerprint',r.candidate_fingerprint,
  'counts',COALESCE((SELECT jsonb_agg(jsonb_build_object('count',c.exact_count,'metric',c.metric_code,'querySha256',c.query_sha256) ORDER BY c.metric_code) FROM release.research_count_snapshot c WHERE c.research_release_id=r.research_release_id),'[]'::jsonb),
  'format','gda-v49-research-release-manifest-jcs-v2',
  'modelVersion',r.model_version,
  'projectionSet',(SELECT jsonb_build_object('databaseSnapshotIdentity',p.database_snapshot_identity,'migrationSetSha256',p.migration_set_sha256,'queryPackSha256',p.projection_query_pack_sha256) FROM release.research_projection_set p WHERE p.research_release_id=r.research_release_id),
  'receipts',COALESCE((SELECT jsonb_agg(jsonb_build_object('byteLength',x.byte_length,'kind',x.receipt_kind,'receiptSha256',x.receipt_sha256,'result',x.validation_result,'verifierVersion',x.verifier_version) ORDER BY x.receipt_kind) FROM release.research_validation_receipt x WHERE x.research_release_id=r.research_release_id),'[]'::jsonb),
  'registrySnapshot',(SELECT to_jsonb(x)-'research_release_id' FROM release.research_registry_snapshot x WHERE x.research_release_id=r.research_release_id),
  'researchReleaseId',r.release_token,
  'researchReleaseUuid',r.research_release_id::text,
  'schemaVersion',r.schema_version,
  'sourceLineage',COALESCE((SELECT jsonb_agg(jsonb_build_object('authority',x.asset_authority,'role',x.source_role,'sha256',x.asset_sha256,'sourceGitCommit',x.source_git_commit) ORDER BY x.source_role) FROM release.research_source_lineage x WHERE x.research_release_id=r.research_release_id),'[]'::jsonb),
  'validationProfileSha256',(SELECT p.profile_sha256 FROM release.validation_profile p WHERE p.validation_profile_id=r.validation_profile_id)
) FROM release.research_release r WHERE r.research_release_id=p_release_id));

CREATE OR REPLACE FUNCTION release.build_visual_manifest_bytes(p_registry_id uuid)
RETURNS bytea LANGUAGE sql STABLE SET search_path=pg_catalog SET TimeZone='UTC'
RETURN release.jcs_bytes((SELECT jsonb_build_object(
  'assets',COALESCE((SELECT jsonb_agg(jsonb_build_object('byteLength',a.byte_length,'mediaType',a.media_type,'path',a.relative_path,'recordCount',a.record_count,'sha256',a.sha256) ORDER BY a.deterministic_sort_key,a.relative_path) FROM release.visual_registry_asset a WHERE a.visual_registry_release_id=r.visual_registry_release_id),'[]'::jsonb),
  'candidateFingerprint',r.candidate_fingerprint,
  'compatibleResearchManifestSha256',r.compatible_research_manifest_sha256,
  'compatibleResearchReleaseId',r.compatible_research_release_id::text,
  'format','gda-v49-visual-registry-manifest-jcs-v2',
  'legacyDisposition',(SELECT to_jsonb(x)-'visual_registry_release_id' FROM release.visual_registry_legacy_disposition_snapshot x WHERE x.visual_registry_release_id=r.visual_registry_release_id),
  'modelVersion',r.model_version,
  'policyInput',(SELECT to_jsonb(x)-'visual_registry_release_id' FROM release.visual_registry_policy_input x WHERE x.visual_registry_release_id=r.visual_registry_release_id),
  'receipts',COALESCE((SELECT jsonb_agg(jsonb_build_object('byteLength',x.byte_length,'kind',x.receipt_kind,'receiptSha256',x.receipt_sha256,'result',x.validation_result,'verifierVersion',x.verifier_version) ORDER BY x.receipt_kind) FROM release.visual_validation_receipt x WHERE x.visual_registry_release_id=r.visual_registry_release_id),'[]'::jsonb),
  'schemaVersion',r.schema_version,
  'validationProfileSha256',(SELECT p.profile_sha256 FROM release.validation_profile p WHERE p.validation_profile_id=r.validation_profile_id),
  'visualRegistryUuid',r.visual_registry_release_id::text,
  'visualRegistryVersion',r.registry_version
) FROM release.visual_registry_release r WHERE r.visual_registry_release_id=p_registry_id));

CREATE OR REPLACE FUNCTION release.create_research_release(
  p_release_id uuid,p_release_token core.release_token,
  p_schema_version core.release_token,p_model_version core.release_token,
  p_event_id uuid,p_event_sha256 core.sha256_hex)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog
AS $function$
DECLARE v_profile uuid;v_now timestamptz:=clock_timestamp();
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  SELECT validation_profile_id INTO v_profile FROM release.validation_profile
  WHERE boundary_kind='research' AND profile_token=p_model_version;
  IF v_profile IS NULL THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='APPROVED_RESEARCH_VALIDATION_PROFILE_REQUIRED';END IF;
  PERFORM release.assert_validation_profile_complete(v_profile,'research');
  INSERT INTO release.research_release(research_release_id,release_token,release_state,schema_version,model_version,created_at,validation_profile_id,validation_boundary)
  VALUES(p_release_id,p_release_token,'draft',p_schema_version,p_model_version,v_now,v_profile,'research');
  INSERT INTO audit.research_release_event VALUES(p_event_id,p_release_id,NULL,'draft',session_user::text,v_now,p_event_sha256);
END
$function$;

CREATE OR REPLACE FUNCTION release.create_visual_registry(
  p_registry_id uuid,p_registry_version core.release_token,
  p_schema_version core.release_token,p_model_version core.release_token,
  p_research_release_id uuid,p_research_manifest_sha256 core.sha256_hex,
  p_event_id uuid,p_event_sha256 core.sha256_hex)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog
AS $function$
DECLARE v_profile uuid;v_now timestamptz:=clock_timestamp();
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  SELECT validation_profile_id INTO v_profile FROM release.validation_profile
  WHERE boundary_kind='visual' AND profile_token=p_model_version;
  IF v_profile IS NULL THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='APPROVED_VISUAL_VALIDATION_PROFILE_REQUIRED';END IF;
  PERFORM release.assert_validation_profile_complete(v_profile,'visual');
  INSERT INTO release.visual_registry_release(visual_registry_release_id,registry_version,release_state,schema_version,model_version,compatible_research_release_id,compatible_research_manifest_sha256,created_at,validation_profile_id,validation_boundary)
  VALUES(p_registry_id,p_registry_version,'draft',p_schema_version,p_model_version,p_research_release_id,p_research_manifest_sha256,v_now,v_profile,'visual');
  INSERT INTO audit.visual_release_event VALUES(p_event_id,p_registry_id,NULL,'draft',session_user::text,v_now,p_event_sha256);
END
$function$;

CREATE OR REPLACE FUNCTION release.close_research_candidate(
  p_release_id uuid,p_expected_fingerprint core.sha256_hex,
  p_event_id uuid,p_event_sha256 core.sha256_hex)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog
AS $function$
DECLARE v_computed core.sha256_hex;v_now timestamptz:=clock_timestamp();
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM 1 FROM release.research_release WHERE research_release_id=p_release_id AND release_state='draft' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='RESEARCH_RELEASE_NOT_DRAFT';END IF;
  v_computed:=release.compute_research_candidate_fingerprint(p_release_id);
  IF p_expected_fingerprint IS DISTINCT FROM v_computed THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='RESEARCH_EXPECTED_FINGERPRINT_MISMATCH';END IF;
  UPDATE release.research_release SET release_state='candidate',candidate_fingerprint=v_computed,candidate_at=v_now WHERE research_release_id=p_release_id;
  PERFORM release.validate_research_projection(p_release_id);
  INSERT INTO audit.research_release_event VALUES(p_event_id,p_release_id,'draft','candidate',session_user::text,v_now,p_event_sha256);
END
$function$;

CREATE OR REPLACE FUNCTION release.close_visual_candidate(
  p_registry_id uuid,p_expected_fingerprint core.sha256_hex,
  p_event_id uuid,p_event_sha256 core.sha256_hex)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog
AS $function$
DECLARE v_computed core.sha256_hex;v_now timestamptz:=clock_timestamp();
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM pg_advisory_xact_lock(hashtext('gda_v49_visual_seal_takedown'));
  PERFORM 1 FROM release.visual_registry_release WHERE visual_registry_release_id=p_registry_id AND release_state='draft' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='VISUAL_REGISTRY_NOT_DRAFT';END IF;
  v_computed:=release.compute_visual_candidate_fingerprint(p_registry_id);
  IF p_expected_fingerprint IS DISTINCT FROM v_computed THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='VISUAL_EXPECTED_FINGERPRINT_MISMATCH';END IF;
  UPDATE release.visual_registry_release SET release_state='candidate',candidate_fingerprint=v_computed,candidate_at=v_now WHERE visual_registry_release_id=p_registry_id;
  PERFORM release.validate_visual_projection(p_registry_id);
  INSERT INTO audit.visual_release_event VALUES(p_event_id,p_registry_id,'draft','candidate',session_user::text,v_now,p_event_sha256);
END
$function$;

CREATE OR REPLACE FUNCTION release.validate_research_release(
  p_release_id uuid,p_receipt_id uuid,p_verifier_version core.release_token,
  p_receipt_sha256 core.sha256_hex,p_event_id uuid,p_event_sha256 core.sha256_hex)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog
AS $function$
DECLARE v_now timestamptz:=clock_timestamp();
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM 1 FROM release.research_release WHERE research_release_id=p_release_id AND release_state='candidate' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='RESEARCH_RELEASE_NOT_CANDIDATE';END IF;
  IF NOT EXISTS(SELECT 1 FROM release.research_validation_receipt r WHERE r.research_validation_receipt_id=p_receipt_id AND r.research_release_id=p_release_id AND r.verifier_version=p_verifier_version AND r.receipt_sha256=p_receipt_sha256 AND r.validation_result='pass') THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='NAMED_RESEARCH_RECEIPT_NOT_FOUND';END IF;
  PERFORM release.assert_required_receipts_complete('research',p_release_id);
  PERFORM release.validate_research_projection(p_release_id);
  UPDATE release.research_release SET release_state='validated',validated_at=v_now WHERE research_release_id=p_release_id;
  INSERT INTO audit.research_release_event VALUES(p_event_id,p_release_id,'candidate','validated',session_user::text,v_now,p_event_sha256);
END
$function$;

CREATE OR REPLACE FUNCTION release.validate_visual_registry(
  p_registry_id uuid,p_receipt_id uuid,p_verifier_version core.release_token,
  p_receipt_sha256 core.sha256_hex,p_event_id uuid,p_event_sha256 core.sha256_hex)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog
AS $function$
DECLARE v_now timestamptz:=clock_timestamp();
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM pg_advisory_xact_lock(hashtext('gda_v49_visual_seal_takedown'));
  PERFORM 1 FROM release.visual_registry_release WHERE visual_registry_release_id=p_registry_id AND release_state='candidate' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='VISUAL_REGISTRY_NOT_CANDIDATE';END IF;
  IF NOT EXISTS(SELECT 1 FROM release.visual_validation_receipt r WHERE r.visual_validation_receipt_id=p_receipt_id AND r.visual_registry_release_id=p_registry_id AND r.verifier_version=p_verifier_version AND r.receipt_sha256=p_receipt_sha256 AND r.validation_result='pass') THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='NAMED_VISUAL_RECEIPT_NOT_FOUND';END IF;
  PERFORM release.assert_required_receipts_complete('visual',p_registry_id);
  PERFORM release.validate_visual_projection(p_registry_id);
  UPDATE release.visual_registry_release SET release_state='validated',validated_at=v_now WHERE visual_registry_release_id=p_registry_id;
  INSERT INTO audit.visual_release_event VALUES(p_event_id,p_registry_id,'candidate','validated',session_user::text,v_now,p_event_sha256);
END
$function$;

CREATE OR REPLACE FUNCTION release.seal_research_release(
  p_release_id uuid,p_seal_event_id uuid,p_release_event_id uuid,
  p_event_sha256 core.sha256_hex)
RETURNS core.sha256_hex LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog
AS $function$
DECLARE v_bytes bytea;v_sha core.sha256_hex;v_fingerprint core.sha256_hex;v_now timestamptz:=clock_timestamp();v_tx bigint:=txid_current();
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  IF current_setting('transaction_isolation')<>'serializable' THEN RAISE EXCEPTION USING ERRCODE='25001',MESSAGE='RESEARCH_SEAL_REQUIRES_SERIALIZABLE_TRANSACTION';END IF;
  SELECT candidate_fingerprint INTO v_fingerprint FROM release.research_release WHERE research_release_id=p_release_id AND release_state='validated' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='RESEARCH_RELEASE_NOT_VALIDATED';END IF;
  PERFORM release.assert_required_receipts_complete('research',p_release_id);
  PERFORM release.validate_research_projection(p_release_id);
  v_bytes:=release.build_research_manifest_bytes(p_release_id);v_sha:=encode(sha256(v_bytes),'hex')::core.sha256_hex;
  INSERT INTO release.research_release_manifest VALUES(p_release_id,v_bytes,v_sha,octet_length(v_bytes),v_now);
  UPDATE release.research_release SET release_state='sealed',manifest_sha256=v_sha,sealed_at=v_now WHERE research_release_id=p_release_id;
  INSERT INTO audit.research_release_event VALUES(p_release_event_id,p_release_id,'validated','sealed',session_user::text,v_now,p_event_sha256);
  INSERT INTO audit.research_seal_event(research_seal_event_id,research_release_id,manifest_sha256,actor,sealed_at,seal_transaction_id,candidate_fingerprint,seal_function_version)
  VALUES(p_seal_event_id,p_release_id,v_sha,session_user::text,v_now,v_tx,v_fingerprint,'phase2a-seal-v2');
  RETURN v_sha;
END
$function$;

CREATE OR REPLACE FUNCTION release.seal_visual_registry(
  p_registry_id uuid,p_seal_event_id uuid,p_release_event_id uuid,
  p_event_sha256 core.sha256_hex)
RETURNS core.sha256_hex LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog
AS $function$
DECLARE v_bytes bytea;v_sha core.sha256_hex;v_fingerprint core.sha256_hex;v_now timestamptz:=clock_timestamp();v_tx bigint:=txid_current();
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  IF current_setting('transaction_isolation')<>'serializable' THEN RAISE EXCEPTION USING ERRCODE='25001',MESSAGE='VISUAL_SEAL_REQUIRES_SERIALIZABLE_TRANSACTION';END IF;
  PERFORM pg_advisory_xact_lock(hashtext('gda_v49_visual_seal_takedown'));
  SELECT candidate_fingerprint INTO v_fingerprint FROM release.visual_registry_release WHERE visual_registry_release_id=p_registry_id AND release_state='validated' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='VISUAL_REGISTRY_NOT_VALIDATED';END IF;
  PERFORM release.assert_required_receipts_complete('visual',p_registry_id);
  PERFORM release.validate_visual_projection(p_registry_id);
  v_bytes:=release.build_visual_manifest_bytes(p_registry_id);v_sha:=encode(sha256(v_bytes),'hex')::core.sha256_hex;
  INSERT INTO release.visual_registry_manifest VALUES(p_registry_id,v_bytes,v_sha,octet_length(v_bytes),v_now);
  UPDATE release.visual_registry_release SET release_state='sealed',manifest_sha256=v_sha,sealed_at=v_now WHERE visual_registry_release_id=p_registry_id;
  INSERT INTO audit.visual_release_event VALUES(p_release_event_id,p_registry_id,'validated','sealed',session_user::text,v_now,p_event_sha256);
  INSERT INTO audit.visual_seal_event(visual_seal_event_id,visual_registry_release_id,manifest_sha256,actor,sealed_at,seal_transaction_id,candidate_fingerprint,seal_function_version)
  VALUES(p_seal_event_id,p_registry_id,v_sha,session_user::text,v_now,v_tx,v_fingerprint,'phase2a-seal-v2');
  RETURN v_sha;
END
$function$;

CREATE OR REPLACE FUNCTION release.verify_sealed_research_integrity(
  p_release_id uuid,p_manifest_sha256 core.sha256_hex)
RETURNS void LANGUAGE plpgsql STABLE SET search_path=pg_catalog
AS $function$
BEGIN
  IF NOT EXISTS(SELECT 1 FROM release.research_release r JOIN release.research_release_manifest m USING(research_release_id) WHERE r.research_release_id=p_release_id AND r.release_state='sealed' AND r.manifest_sha256=p_manifest_sha256 AND m.manifest_sha256=p_manifest_sha256 AND r.candidate_fingerprint=release.compute_research_candidate_fingerprint(p_release_id) AND m.manifest_bytes=release.build_research_manifest_bytes(p_release_id) AND encode(sha256(m.manifest_bytes),'hex')=p_manifest_sha256) THEN
    RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SEALED_RESEARCH_DETACHED_INTEGRITY_FAILURE';
  END IF;
END
$function$;

CREATE OR REPLACE FUNCTION release.verify_sealed_visual_integrity(
  p_registry_id uuid,p_manifest_sha256 core.sha256_hex)
RETURNS void LANGUAGE plpgsql STABLE SET search_path=pg_catalog
AS $function$
BEGIN
  IF NOT EXISTS(SELECT 1 FROM release.visual_registry_release r JOIN release.visual_registry_manifest m USING(visual_registry_release_id) WHERE r.visual_registry_release_id=p_registry_id AND r.release_state='sealed' AND r.manifest_sha256=p_manifest_sha256 AND m.manifest_sha256=p_manifest_sha256 AND r.candidate_fingerprint=release.compute_visual_candidate_fingerprint(p_registry_id) AND m.manifest_bytes=release.build_visual_manifest_bytes(p_registry_id) AND encode(sha256(m.manifest_bytes),'hex')=p_manifest_sha256) THEN
    RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SEALED_VISUAL_DETACHED_INTEGRITY_FAILURE';
  END IF;
END
$function$;

CREATE OR REPLACE FUNCTION release.compute_research_verification_sidecar_sha(p_release_id uuid,p_manifest_sha256 core.sha256_hex,p_verifier_version core.release_token)
RETURNS core.sha256_hex LANGUAGE sql STABLE SET search_path=pg_catalog
RETURN release.canonical_jsonb_sha256(jsonb_build_object('candidateFingerprint',(SELECT candidate_fingerprint FROM release.research_release WHERE research_release_id=p_release_id),'format','gda-v49-research-verification-sidecar-v2','manifestSha256',p_manifest_sha256,'releaseId',p_release_id::text,'sealFunctionVersion',(SELECT seal_function_version FROM audit.research_seal_event WHERE research_release_id=p_release_id),'sealTransactionId',(SELECT seal_transaction_id FROM audit.research_seal_event WHERE research_release_id=p_release_id),'verifierVersion',p_verifier_version));

CREATE OR REPLACE FUNCTION release.compute_visual_verification_sidecar_sha(p_registry_id uuid,p_manifest_sha256 core.sha256_hex,p_verifier_version core.release_token)
RETURNS core.sha256_hex LANGUAGE sql STABLE SET search_path=pg_catalog
RETURN release.canonical_jsonb_sha256(jsonb_build_object('candidateFingerprint',(SELECT candidate_fingerprint FROM release.visual_registry_release WHERE visual_registry_release_id=p_registry_id),'format','gda-v49-visual-verification-sidecar-v2','manifestSha256',p_manifest_sha256,'registryId',p_registry_id::text,'sealFunctionVersion',(SELECT seal_function_version FROM audit.visual_seal_event WHERE visual_registry_release_id=p_registry_id),'sealTransactionId',(SELECT seal_transaction_id FROM audit.visual_seal_event WHERE visual_registry_release_id=p_registry_id),'verifierVersion',p_verifier_version));

CREATE OR REPLACE FUNCTION release.record_research_verification(
  p_verification_id uuid,p_release_id uuid,p_manifest_sha256 core.sha256_hex,
  p_verifier_version core.release_token,p_sidecar_sha256 core.sha256_hex,
  p_audit_event_id uuid,p_audit_receipt_sha256 core.sha256_hex)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog
AS $function$
DECLARE v_expected core.sha256_hex;v_seal audit.research_seal_event%ROWTYPE;v_now timestamptz:=clock_timestamp();
BEGIN
  PERFORM rights.require_reviewer();PERFORM release.verify_sealed_research_integrity(p_release_id,p_manifest_sha256);
  SELECT * INTO STRICT v_seal FROM audit.research_seal_event WHERE research_release_id=p_release_id;
  v_expected:=release.compute_research_verification_sidecar_sha(p_release_id,p_manifest_sha256,p_verifier_version);
  IF p_sidecar_sha256 IS DISTINCT FROM v_expected THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='RESEARCH_VERIFICATION_SIDECAR_MISMATCH';END IF;
  INSERT INTO release.research_release_verification(research_release_verification_id,research_release_id,manifest_sha256,verifier_version,sidecar_sha256,verified,verified_at,seal_transaction_id,candidate_fingerprint,seal_function_version,attestation_sha256)
  VALUES(p_verification_id,p_release_id,p_manifest_sha256,p_verifier_version,p_sidecar_sha256,true,v_now,v_seal.seal_transaction_id,v_seal.candidate_fingerprint,v_seal.seal_function_version,NULL);
  INSERT INTO audit.verification_receipt_event VALUES(p_audit_event_id,p_verification_id,NULL,p_audit_receipt_sha256,session_user::text,v_now);
END
$function$;

CREATE OR REPLACE FUNCTION release.record_visual_verification(
  p_verification_id uuid,p_registry_id uuid,p_manifest_sha256 core.sha256_hex,
  p_verifier_version core.release_token,p_sidecar_sha256 core.sha256_hex,
  p_audit_event_id uuid,p_audit_receipt_sha256 core.sha256_hex)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog
AS $function$
DECLARE v_expected core.sha256_hex;v_seal audit.visual_seal_event%ROWTYPE;v_now timestamptz:=clock_timestamp();
BEGIN
  PERFORM rights.require_reviewer();PERFORM release.verify_sealed_visual_integrity(p_registry_id,p_manifest_sha256);
  SELECT * INTO STRICT v_seal FROM audit.visual_seal_event WHERE visual_registry_release_id=p_registry_id;
  v_expected:=release.compute_visual_verification_sidecar_sha(p_registry_id,p_manifest_sha256,p_verifier_version);
  IF p_sidecar_sha256 IS DISTINCT FROM v_expected THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='VISUAL_VERIFICATION_SIDECAR_MISMATCH';END IF;
  INSERT INTO release.visual_registry_verification(visual_registry_verification_id,visual_registry_release_id,manifest_sha256,verifier_version,sidecar_sha256,verified,verified_at,seal_transaction_id,candidate_fingerprint,seal_function_version,attestation_sha256)
  VALUES(p_verification_id,p_registry_id,p_manifest_sha256,p_verifier_version,p_sidecar_sha256,true,v_now,v_seal.seal_transaction_id,v_seal.candidate_fingerprint,v_seal.seal_function_version,NULL);
  INSERT INTO audit.verification_receipt_event VALUES(p_audit_event_id,NULL,p_verification_id,p_audit_receipt_sha256,session_user::text,v_now);
END
$function$;

RESET ROLE;
