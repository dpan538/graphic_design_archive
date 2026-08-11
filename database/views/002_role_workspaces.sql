\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

CREATE VIEW workflow.reviewer_queue
WITH (security_barrier = true)
AS
SELECT c.review_case_id, c.case_kind, c.queue_state, c.priority,
  c.reason_code, c.claimed_by, c.claimed_at, c.created_at,
  a.assertion_id, x.canonical_assignment_id,
  q.claim_revision_id, r.semantic_relation_id,
  t.relation_type_review_queue_id, z.rights_assessment_id
FROM workflow.review_case c
LEFT JOIN workflow.review_case_assertion a USING (review_case_id)
LEFT JOIN workflow.review_case_assignment x USING (review_case_id)
LEFT JOIN workflow.review_case_claim q USING (review_case_id)
LEFT JOIN workflow.review_case_relation r USING (review_case_id)
LEFT JOIN workflow.review_case_relation_type_literal t USING (review_case_id)
LEFT JOIN workflow.review_case_rights_assessment z USING (review_case_id)
WHERE c.queue_state = 'queued'
  OR c.claimed_by = session_user::text;

CREATE VIEW workflow.ingest_metadata_context
WITH (security_barrier = true)
AS
SELECT a.source_asset_id, a.logical_name, a.sha256 AS asset_sha256,
  r.source_record_id, r.record_ordinal, r.raw_fingerprint,
  f.field_literal_id, f.json_pointer, f.occurrence_ordinal
FROM raw.source_asset a
LEFT JOIN raw.source_record r ON r.source_asset_id = a.source_asset_id
LEFT JOIN raw.field_literal f ON f.source_record_id = r.source_record_id
WHERE a.authority = 'governed_source';

CREATE VIEW workflow.reviewer_source_context
WITH (security_barrier = true)
AS
SELECT c.review_case_id, f.field_literal_id, f.json_pointer,
  f.occurrence_ordinal, f.raw_text, f.raw_bytes,
  r.source_record_id, r.raw_fingerprint, r.parse_error_code,
  a.source_asset_id, a.authority, a.logical_name, a.sha256 AS asset_sha256
FROM workflow.review_case c
JOIN workflow.review_case_assertion ca USING (review_case_id)
JOIN provenance.assertion_value_literal av
  ON av.assertion_id = ca.assertion_id
JOIN raw.field_literal f ON f.field_literal_id = av.field_literal_id
JOIN raw.source_record r ON r.source_record_id = f.source_record_id
JOIN raw.source_asset a ON a.source_asset_id = r.source_asset_id
WHERE c.queue_state = 'queued'
  OR c.claimed_by = session_user::text;

CREATE VIEW workflow.reviewer_provenance_context
WITH (security_barrier = true)
AS
SELECT c.review_case_id, c.case_kind,
  p.assertion_id, p.assertion_predicate_id,
  p.subject_kind, p.value_kind, p.status AS assertion_status,
  x.canonical_assignment_id, x.assignment_kind,
  x.status AS assignment_status,
  q.claim_revision_id, q.status AS claim_status,
  r.semantic_relation_id, r.status AS relation_status
FROM workflow.review_case c
LEFT JOIN workflow.review_case_assertion ca USING (review_case_id)
LEFT JOIN provenance.assertion p ON p.assertion_id = ca.assertion_id
LEFT JOIN workflow.review_case_assignment cx USING (review_case_id)
LEFT JOIN provenance.canonical_assignment x
  ON x.canonical_assignment_id = cx.canonical_assignment_id
LEFT JOIN workflow.review_case_claim cq USING (review_case_id)
LEFT JOIN research.claim_revision q ON q.claim_revision_id = cq.claim_revision_id
LEFT JOIN workflow.review_case_relation cr USING (review_case_id)
LEFT JOIN research.semantic_relation r
  ON r.semantic_relation_id = cr.semantic_relation_id
WHERE c.queue_state = 'queued'
  OR c.claimed_by = session_user::text;

CREATE VIEW release.publisher_research_source
WITH (security_barrier = true)
AS
SELECT m.corpus_version_id, m.archive_object_id, m.disposition,
  m.reason_code, o.object_urn, o.preferred_label,
  l.surface_id AS legacy_surface_id
FROM research.corpus_membership m
JOIN core.archive_object o ON o.archive_object_id = m.archive_object_id
LEFT JOIN raw.legacy_surface_ledger l
  ON l.archive_object_id = m.archive_object_id
WHERE m.disposition IN ('eligible', 'held', 'rejected');

CREATE VIEW release.publisher_visual_source
WITH (security_barrier = true)
AS
SELECT d.delivery_assessment_id, d.object_visual_reference_id,
  d.delivery_mode, d.reason_code, d.assessed_at,
  b.archive_object_id, b.external_visual_reference_id, b.reference_role,
  r.visual_reference_urn, p.provider_id, p.provider_code,
  q.visual_locator_id, q.allowlisted_role, l.raw_locator,
  h.endpoint_health_observation_id, h.health_state,
  h.checked_at, h.valid_until,
  rights.compute_delivery_rights_sha(d.delivery_assessment_id)
    AS rights_outcome_sha256,
  rights.compute_delivery_policy_sha(d.delivery_assessment_id)
    AS policy_outcome_sha256,
  rights.compute_attribution_bundle_sha(d.attribution_bundle_id)
    AS attribution_bundle_sha256
FROM rights.delivery_assessment d
JOIN rights.object_visual_reference b
  ON b.object_visual_reference_id = d.object_visual_reference_id
JOIN rights.external_visual_reference r
  ON r.external_visual_reference_id = b.external_visual_reference_id
LEFT JOIN rights.provider_object po ON po.provider_object_id = r.provider_object_id
LEFT JOIN rights.provider p ON p.provider_id = po.provider_id
LEFT JOIN rights.delivery_locator_qualification q
  ON q.delivery_assessment_id = d.delivery_assessment_id
LEFT JOIN rights.visual_locator l ON l.visual_locator_id = q.visual_locator_id
LEFT JOIN rights.endpoint_health_observation h
  ON h.endpoint_health_observation_id = q.endpoint_health_observation_id
WHERE NOT EXISTS (
  SELECT 1 FROM rights.delivery_assessment newer
  WHERE newer.supersedes_delivery_assessment_id = d.delivery_assessment_id
);

CREATE VIEW release.publisher_artifact_inventory
WITH (security_barrier = true)
AS
SELECT 'research'::text AS boundary,
  r.research_release_id AS release_id, r.release_token AS version_token,
  r.release_state, r.candidate_fingerprint, r.manifest_sha256,
  (SELECT count(*) FROM release.research_validation_receipt v
    WHERE v.research_release_id = r.research_release_id
      AND v.validation_result = 'pass') AS passing_receipt_count,
  (SELECT count(*) FROM release.research_release_verification v
    WHERE v.research_release_id = r.research_release_id AND v.verified)
    AS verification_count
FROM release.research_release r
UNION ALL
SELECT 'visual', r.visual_registry_release_id, r.registry_version,
  r.release_state, r.candidate_fingerprint, r.manifest_sha256,
  (SELECT count(*) FROM release.visual_validation_receipt v
    WHERE v.visual_registry_release_id = r.visual_registry_release_id
      AND v.validation_result = 'pass'),
  (SELECT count(*) FROM release.visual_registry_verification v
    WHERE v.visual_registry_release_id = r.visual_registry_release_id
      AND v.verified)
FROM release.visual_registry_release r;

CREATE VIEW audit.raw_hash_inventory
WITH (security_barrier = true)
AS
SELECT a.source_asset_id, a.authority, a.logical_name,
  a.sha256, a.byte_length, a.media_type, a.received_at,
  count(r.source_record_id) AS source_record_count
FROM raw.source_asset a
LEFT JOIN raw.source_record r ON r.source_asset_id = a.source_asset_id
GROUP BY a.source_asset_id, a.authority, a.logical_name,
  a.sha256, a.byte_length, a.media_type, a.received_at;

CREATE VIEW audit.release_history_inventory
WITH (security_barrier = true)
AS
SELECT 'research'::text AS boundary, h.channel,
  h.promoted_generation, h.research_release_id AS release_id,
  h.manifest_sha256, h.published_at
FROM release.research_publication_history h
UNION ALL
SELECT 'visual', h.channel, h.promoted_generation,
  h.visual_registry_release_id, h.manifest_sha256, h.published_at
FROM release.visual_publication_history h;

CREATE VIEW audit.role_grant_inventory
WITH (security_barrier = true)
AS
SELECT grantor, grantee, table_schema, table_name,
  privilege_type, is_grantable
FROM information_schema.role_table_grants
WHERE grantee LIKE 'gda_v49_phase2a_%';

CREATE VIEW audit.decision_event_inventory
WITH (security_barrier = true)
AS
SELECT e.decision_event_id, e.decision_kind, e.actor,
  e.occurred_at, e.event_sha256
FROM audit.decision_event e;

RESET ROLE;
