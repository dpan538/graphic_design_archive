\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

CREATE OR REPLACE FUNCTION rights.compute_health_observation_sha(
  p_health_id uuid
)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
SET TimeZone = 'UTC'
RETURN (
  SELECT release.canonical_jsonb_sha256(jsonb_build_object(
    'checkedAtUs', (extract(epoch FROM h.checked_at) * 1000000)::bigint,
    'healthId', h.endpoint_health_observation_id,
    'locatorId', h.visual_locator_id,
    'methodVersion', h.method_version,
    'requestFingerprintSha256', h.request_fingerprint,
    'state', h.health_state,
    'validUntilUs', CASE WHEN h.valid_until IS NULL THEN NULL ELSE
      (extract(epoch FROM h.valid_until) * 1000000)::bigint END
  ))
  FROM rights.endpoint_health_observation h
  WHERE h.endpoint_health_observation_id = p_health_id
);

CREATE OR REPLACE FUNCTION rights.compute_takedown_override_sha(
  p_override_id uuid
)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
SET TimeZone = 'UTC'
RETURN (
  SELECT release.canonical_jsonb_sha256(jsonb_build_object(
    'action', e.action,
    'createdAtUs', (extract(epoch FROM o.created_at) * 1000000)::bigint,
    'effectiveFromUs',
      (extract(epoch FROM e.effective_from) * 1000000)::bigint,
    'effectiveUntilUs', CASE WHEN e.effective_until IS NULL THEN NULL ELSE
      (extract(epoch FROM e.effective_until) * 1000000)::bigint END,
    'eventId', e.takedown_event_id,
    'evidenceId', e.evidence_item_id,
    'overrideId', o.takedown_override_id,
    'overrideVersion', o.override_version,
    'reasonCode', e.reason_code,
    'restrictiveMode', o.restrictive_mode,
    'scopeId', s.takedown_scope_id,
    'scopeKind', s.scope_kind,
    'scopeOrdinal', s.scope_ordinal,
    'scopeTarget', rights.takedown_scope_target_key(s.takedown_scope_id),
    'supersedesOverrideId', o.supersedes_takedown_override_id
  ))
  FROM rights.takedown_override o
  JOIN rights.takedown_scope s ON s.takedown_scope_id = o.takedown_scope_id
  JOIN rights.takedown_event e ON e.takedown_event_id = s.takedown_event_id
  WHERE o.takedown_override_id = p_override_id
);

CREATE OR REPLACE FUNCTION rights.compute_rights_observation_sha(
  p_observation_id uuid
)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
SET TimeZone = 'UTC'
RETURN (
  SELECT release.canonical_jsonb_sha256(jsonb_build_object(
    'evidence', CASE WHEN ei.evidence_item_id IS NULL THEN NULL ELSE
      to_jsonb(ei) END,
    'evidenceId', o.evidence_item_id,
    'observationId', o.rights_observation_id,
    'observedAtUs',
      (extract(epoch FROM o.observed_at) * 1000000)::bigint,
    'state', o.evidence_state,
    'subjectKey', rights.observation_subject_key(o.rights_observation_id),
    'subjectKind', o.subject_kind,
    'wording', o.observed_wording
  ))
  FROM rights.rights_observation o
  LEFT JOIN provenance.evidence_item ei
    ON ei.evidence_item_id = o.evidence_item_id
  WHERE o.rights_observation_id = p_observation_id
);

CREATE OR REPLACE FUNCTION rights.compute_rights_assessment_sha(
  p_assessment_id uuid
)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
SET TimeZone = 'UTC'
RETURN (
  SELECT release.canonical_jsonb_sha256(jsonb_build_object(
    'assessedAtUs',
      (extract(epoch FROM a.assessed_at) * 1000000)::bigint,
    'assessmentId', a.rights_assessment_id,
    'observations', COALESCE((
      SELECT jsonb_agg(jsonb_build_object(
        'observationId', x.rights_observation_id,
        'observationSha256',
          rights.compute_rights_observation_sha(x.rights_observation_id),
        'role', x.evidence_role
      ) ORDER BY x.rights_observation_id, x.evidence_role)
      FROM rights.rights_assessment_observation x
      WHERE x.rights_assessment_id = a.rights_assessment_id
    ), '[]'::jsonb),
    'rationale', a.rationale,
    'reviewer', a.reviewer_actor,
    'state', a.assessed_state,
    'subjectKey', rights.assessment_subject_key(a.rights_assessment_id),
    'subjectKind', a.subject_kind
  ))
  FROM rights.rights_assessment a
  WHERE a.rights_assessment_id = p_assessment_id
);

CREATE OR REPLACE FUNCTION rights.compute_attribution_bundle_sha(
  p_bundle_id uuid
)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
SET TimeZone = 'UTC'
RETURN (
  SELECT release.canonical_jsonb_sha256(jsonb_build_object(
    'bridgeId', a.object_visual_reference_id,
    'bundleId', a.attribution_bundle_id,
    'evidenceId', a.evidence_item_id,
    'state', a.attribution_state,
    'supersedesBundleId', a.supersedes_attribution_bundle_id,
    'validatedAtUs',
      (extract(epoch FROM a.validated_at) * 1000000)::bigint,
    'validatedBy', a.validated_by,
    'values', COALESCE((
      SELECT jsonb_agg(jsonb_build_array(
        v.value_kind, v.value_ordinal, v.language_tag, v.value_text
      ) ORDER BY v.value_kind, v.value_ordinal)
      FROM rights.attribution_bundle_value v
      WHERE v.attribution_bundle_id = a.attribution_bundle_id
    ), '[]'::jsonb)
  ))
  FROM rights.attribution_bundle a
  WHERE a.attribution_bundle_id = p_bundle_id
);

CREATE OR REPLACE FUNCTION rights.compute_provider_policy_evaluation_sha(
  p_evaluation_id uuid
)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
SET TimeZone = 'UTC'
RETURN (
  SELECT release.canonical_jsonb_sha256(jsonb_build_object(
    'bridgeId', e.object_visual_reference_id,
    'evaluatedAtUs',
      (extract(epoch FROM e.evaluated_at) * 1000000)::bigint,
    'evaluationId', e.provider_policy_evaluation_id,
    'evaluator', e.evaluator_actor,
    'state', e.evaluated_state,
    'versions', COALESCE((
      SELECT jsonb_agg(jsonb_build_object(
        'effectiveFromUs',
          (extract(epoch FROM pv.effective_from) * 1000000)::bigint,
        'effectiveUntilUs', CASE WHEN pv.effective_until IS NULL THEN NULL
          ELSE (extract(epoch FROM pv.effective_until) * 1000000)::bigint END,
        'policyScopeId', pv.policy_scope_id,
        'policySha256', pv.policy_sha256,
        'policyState', pv.policy_state,
        'providerId', pv.provider_id,
        'reviewDueUs',
          (extract(epoch FROM pv.review_due) * 1000000)::bigint,
        'sourceEvidence', to_jsonb(ei),
        'sourceEvidenceId', pv.source_evidence_item_id,
        'versionId', pv.provider_policy_version_id,
        'versionToken', pv.version_token
      ) ORDER BY pv.provider_policy_version_id)
      FROM rights.provider_policy_evaluation_version x
      JOIN rights.provider_policy_version pv
        ON pv.provider_policy_version_id = x.provider_policy_version_id
      JOIN provenance.evidence_item ei
        ON ei.evidence_item_id = pv.source_evidence_item_id
      WHERE x.provider_policy_evaluation_id = e.provider_policy_evaluation_id
    ), '[]'::jsonb)
  ))
  FROM rights.provider_policy_evaluation e
  WHERE e.provider_policy_evaluation_id = p_evaluation_id
);

CREATE OR REPLACE FUNCTION rights.compute_delivery_rights_sha(
  p_delivery_id uuid
)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
RETURN release.canonical_jsonb_sha256(COALESCE((
  SELECT jsonb_agg(jsonb_build_array(
    x.rights_assessment_id, x.evidence_role,
    rights.compute_rights_assessment_sha(x.rights_assessment_id)
  ) ORDER BY x.rights_assessment_id, x.evidence_role)
  FROM rights.delivery_rights_assessment x
  WHERE x.delivery_assessment_id = p_delivery_id
), '[]'::jsonb));

CREATE OR REPLACE FUNCTION rights.compute_delivery_policy_sha(
  p_delivery_id uuid
)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
RETURN release.canonical_jsonb_sha256(COALESCE((
  SELECT jsonb_agg(jsonb_build_array(
    x.provider_policy_evaluation_id,
    rights.compute_provider_policy_evaluation_sha(
      x.provider_policy_evaluation_id)
  ) ORDER BY x.provider_policy_evaluation_id)
  FROM rights.delivery_policy_evaluation x
  WHERE x.delivery_assessment_id = p_delivery_id
), '[]'::jsonb));

CREATE OR REPLACE FUNCTION rights.compute_delivery_snapshot_sha(
  p_delivery_id uuid
)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
SET TimeZone = 'UTC'
RETURN (
  SELECT release.canonical_jsonb_sha256(jsonb_build_object(
    'assessedAtUs',
      (extract(epoch FROM d.assessed_at) * 1000000)::bigint,
    'assessor', d.assessor_actor,
    'attributionBundleId', d.attribution_bundle_id,
    'attributionSha256', CASE WHEN d.attribution_bundle_id IS NULL THEN NULL
      ELSE rights.compute_attribution_bundle_sha(d.attribution_bundle_id) END,
    'bridgeId', d.object_visual_reference_id,
    'deliveryId', d.delivery_assessment_id,
    'machineReasonCode', d.machine_reason_code,
    'mode', d.delivery_mode,
    'policySha256', rights.compute_delivery_policy_sha(d.delivery_assessment_id),
    'qualifications', COALESCE((
      SELECT jsonb_agg(jsonb_build_array(
        q.visual_locator_id, q.endpoint_health_observation_id,
        q.allowlisted_role,
        rights.compute_health_observation_sha(
          q.endpoint_health_observation_id)
      ) ORDER BY q.allowlisted_role, q.visual_locator_id)
      FROM rights.delivery_locator_qualification q
      WHERE q.delivery_assessment_id = d.delivery_assessment_id
    ), '[]'::jsonb),
    'reasonCode', d.reason_code,
    'rightsSha256', rights.compute_delivery_rights_sha(d.delivery_assessment_id)
  ))
  FROM rights.delivery_assessment d
  WHERE d.delivery_assessment_id = p_delivery_id
);

RESET ROLE;
