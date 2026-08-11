\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

CREATE VIEW release.effective_visual_entry
WITH (security_barrier = true)
AS
WITH selected_locator AS (
  SELECT l.visual_registry_release_id, l.visual_registry_entry_id,
    l.visual_locator_id, l.locator_role, l.public_locator,
    l.health_state AS sealed_health_state,
    l.health_observed_at AS sealed_observed_at,
    l.health_valid_until AS sealed_valid_until
  FROM release.visual_registry_public_locator l
), latest_health AS (
  SELECT DISTINCT ON (
    h.visual_registry_release_id, h.visual_registry_entry_id,
    h.visual_locator_id
  ) h.visual_registry_release_id, h.visual_registry_entry_id,
    h.visual_locator_id, h.health_state, h.observed_at, h.valid_until
  FROM release.visual_health_sidecar_event h
  WHERE h.observed_at <= clock_timestamp()
  ORDER BY h.visual_registry_release_id, h.visual_registry_entry_id,
    h.visual_locator_id, h.observed_at DESC,
    h.visual_health_sidecar_event_id DESC
), locator_effective AS (
  SELECT s.*,
    COALESCE(h.health_state, s.sealed_health_state) AS effective_health_state,
    COALESCE(h.observed_at, s.sealed_observed_at) AS effective_observed_at,
    CASE WHEN h.visual_locator_id IS NULL
      THEN s.sealed_valid_until ELSE h.valid_until END AS effective_valid_until,
    (COALESCE(h.health_state, s.sealed_health_state) = 'healthy_fresh'
      AND COALESCE(h.observed_at, s.sealed_observed_at) <= clock_timestamp()
      AND (CASE WHEN h.visual_locator_id IS NULL
        THEN s.sealed_valid_until ELSE h.valid_until END) > clock_timestamp()
    ) AS is_healthy_fresh
  FROM selected_locator s
  LEFT JOIN latest_health h USING (
    visual_registry_release_id, visual_registry_entry_id, visual_locator_id
  )
), locator_rollup AS (
  SELECT l.visual_registry_release_id, l.visual_registry_entry_id,
    max(l.public_locator) FILTER (
      WHERE l.locator_role = 'canonical_record' AND l.is_healthy_fresh
    ) AS canonical_record_url,
    max(l.public_locator) FILTER (
      WHERE l.locator_role = 'source_viewer' AND l.is_healthy_fresh
    ) AS source_viewer_url,
    max(l.public_locator) FILTER (
      WHERE l.locator_role = 'direct_image' AND l.is_healthy_fresh
    ) AS remote_image_url,
    max(l.effective_health_state::text) FILTER (
      WHERE l.locator_role = 'direct_image') AS pixel_health_state
  FROM locator_effective l
  GROUP BY l.visual_registry_release_id, l.visual_registry_entry_id
), attribution_rollup AS (
  SELECT a.visual_registry_release_id, a.visual_registry_entry_id,
    jsonb_agg(jsonb_build_object(
      'ordinal', a.value_ordinal, 'language', a.language_tag,
      'value', a.value_text
    ) ORDER BY a.value_ordinal) FILTER (
      WHERE a.value_kind = 'attribution') AS attribution_values,
    jsonb_agg(jsonb_build_object(
      'ordinal', a.value_ordinal, 'language', a.language_tag,
      'value', a.value_text
    ) ORDER BY a.value_ordinal) FILTER (
      WHERE a.value_kind = 'required_statement') AS required_statement_values
  FROM release.visual_registry_attribution_value a
  GROUP BY a.visual_registry_release_id, a.visual_registry_entry_id
), policy_cap AS (
  SELECT e.visual_registry_release_id, e.visual_registry_entry_id,
    COALESCE(min(CASE
      WHEN p.effective_from > clock_timestamp()
        OR p.review_due <= clock_timestamp()
        OR (p.effective_until IS NOT NULL
          AND p.effective_until <= clock_timestamp()) THEN 1
      WHEN p.policy_state = 'remote_display_allowed' THEN 4
      WHEN p.policy_state = 'source_viewer_only' THEN 3
      WHEN p.policy_state = 'link_only' THEN 2
      WHEN p.policy_state = 'citation_only' THEN 1
      WHEN p.policy_state = 'disallowed' THEN 0
      ELSE 1 END), 1) AS delivery_cap
  FROM release.visual_registry_entry e
  LEFT JOIN release.visual_registry_delivery_policy_snapshot dp
    ON dp.visual_registry_release_id = e.visual_registry_release_id
    AND dp.delivery_assessment_id = e.delivery_assessment_id
  LEFT JOIN release.visual_registry_policy_evaluation_version_snapshot ev
    ON ev.visual_registry_release_id = dp.visual_registry_release_id
    AND ev.provider_policy_evaluation_id = dp.provider_policy_evaluation_id
  LEFT JOIN release.visual_registry_policy_version_snapshot p
    ON p.visual_registry_release_id = ev.visual_registry_release_id
    AND p.provider_policy_version_id = ev.provider_policy_version_id
  GROUP BY e.visual_registry_release_id, e.visual_registry_entry_id
), sidecar_takedown AS (
  SELECT t.visual_registry_release_id, t.visual_registry_entry_id,
    t.restrictive_mode, t.overlay_sha256, t.effective_from
  FROM release.visual_takedown_sidecar_event t
  WHERE t.effective_from <= clock_timestamp()
), sealed_takedown AS (
  SELECT t.visual_registry_release_id, t.visual_registry_entry_id,
    t.restrictive_mode, t.overlay_sha256, t.effective_from
  FROM release.visual_registry_takedown_snapshot t
  WHERE t.effective_from <= clock_timestamp()
), all_takedowns AS (
  SELECT * FROM sidecar_takedown
  UNION ALL
  SELECT * FROM sealed_takedown
), latched_takedown AS (
  SELECT DISTINCT ON (t.visual_registry_release_id, t.visual_registry_entry_id)
    t.visual_registry_release_id, t.visual_registry_entry_id,
    t.restrictive_mode, t.overlay_sha256
  FROM all_takedowns t
  ORDER BY t.visual_registry_release_id, t.visual_registry_entry_id,
    CASE t.restrictive_mode WHEN 'blocked' THEN 0 ELSE 1 END,
    t.effective_from DESC, t.overlay_sha256
), reduced AS (
  SELECT e.*, l.canonical_record_url, l.source_viewer_url,
    l.remote_image_url, l.pixel_health_state,
    a.attribution_values, a.required_statement_values,
    t.overlay_sha256, t.restrictive_mode, p.delivery_cap,
    CASE
      WHEN t.restrictive_mode = 'blocked' THEN 'blocked'::rights.delivery_mode
      WHEN t.restrictive_mode = 'citation_only' THEN 'citation_only'::rights.delivery_mode
      WHEN e.base_delivery_mode IN ('blocked', 'citation_only') THEN e.base_delivery_mode
      WHEN p.delivery_cap < 2 THEN 'citation_only'::rights.delivery_mode
      WHEN e.base_delivery_mode = 'link_only' THEN
        CASE WHEN l.canonical_record_url IS NOT NULL
          THEN 'link_only'::rights.delivery_mode
          ELSE 'citation_only'::rights.delivery_mode END
      WHEN e.base_delivery_mode = 'source_viewer' THEN
        CASE WHEN p.delivery_cap >= 3 AND l.source_viewer_url IS NOT NULL
          THEN 'source_viewer'::rights.delivery_mode
          WHEN l.canonical_record_url IS NOT NULL
          THEN 'link_only'::rights.delivery_mode
          ELSE 'citation_only'::rights.delivery_mode END
      WHEN e.base_delivery_mode = 'remote_image' THEN
        CASE WHEN p.delivery_cap >= 4 AND l.remote_image_url IS NOT NULL
          THEN 'remote_image'::rights.delivery_mode
          WHEN l.canonical_record_url IS NOT NULL
          THEN 'link_only'::rights.delivery_mode
          ELSE 'citation_only'::rights.delivery_mode END
      ELSE 'citation_only'::rights.delivery_mode
    END AS effective_delivery_mode
  FROM release.visual_registry_entry e
  LEFT JOIN locator_rollup l USING (
    visual_registry_release_id, visual_registry_entry_id)
  LEFT JOIN attribution_rollup a USING (
    visual_registry_release_id, visual_registry_entry_id)
  LEFT JOIN latched_takedown t USING (
    visual_registry_release_id, visual_registry_entry_id)
  LEFT JOIN policy_cap p USING (
    visual_registry_release_id, visual_registry_entry_id)
), reasoned AS (
  SELECT r.*,
    CASE
      WHEN r.restrictive_mode = 'blocked' THEN 'RD-001'::rights.delivery_rule_id
      WHEN r.restrictive_mode = 'citation_only' THEN 'RD-002'::rights.delivery_rule_id
      WHEN r.base_delivery_mode NOT IN ('blocked','citation_only')
        AND r.delivery_cap < 2 THEN 'RD-030'::rights.delivery_rule_id
      WHEN r.base_delivery_mode = 'link_only'
        AND r.effective_delivery_mode = 'citation_only'
        THEN 'RD-041'::rights.delivery_rule_id
      WHEN r.base_delivery_mode = 'source_viewer'
        AND r.effective_delivery_mode = 'link_only'
        THEN 'RD-051'::rights.delivery_rule_id
      WHEN r.base_delivery_mode = 'source_viewer'
        AND r.effective_delivery_mode = 'citation_only'
        THEN 'RD-052'::rights.delivery_rule_id
      WHEN r.base_delivery_mode = 'remote_image'
        AND r.effective_delivery_mode = 'link_only'
        THEN 'RD-081'::rights.delivery_rule_id
      WHEN r.base_delivery_mode = 'remote_image'
        AND r.effective_delivery_mode = 'citation_only'
        THEN 'RD-082'::rights.delivery_rule_id
      ELSE r.reason_code
    END AS effective_reason_code
  FROM reduced r
)
SELECT r.visual_registry_release_id, r.visual_registry_entry_id,
  r.archive_object_id, r.external_visual_reference_id,
  r.object_urn, r.visual_reference_urn, r.provider_code,
  r.base_delivery_mode, r.effective_delivery_mode,
  r.effective_reason_code AS reason_code,
  rights.machine_reason_for_rule(r.effective_reason_code)
    AS machine_reason_code,
  r.attribution_values, r.required_statement_values,
  r.pixel_health_state, r.overlay_sha256,
  CASE WHEN r.effective_delivery_mode IN ('link_only','source_viewer','remote_image')
    THEN r.canonical_record_url END AS canonical_record_url,
  CASE WHEN r.effective_delivery_mode = 'source_viewer'
    THEN r.source_viewer_url END AS source_viewer_url,
  CASE WHEN r.effective_delivery_mode = 'remote_image'
    THEN r.remote_image_url END AS remote_image_url
FROM reasoned r;

CREATE VIEW api_v1.current_version_status
WITH (security_barrier = true)
AS
SELECT rp.channel, rp.generation AS research_generation,
  rr.release_token AS research_release_id,
  rp.manifest_sha256 AS research_manifest_sha256,
  vp.generation AS visual_generation,
  vr.registry_version AS visual_registry_version,
  vp.manifest_sha256 AS visual_registry_sha256,
  CASE WHEN rp.research_release_id IS NULL THEN 'research_unavailable'
    WHEN vp.visual_registry_release_id IS NULL THEN 'not_selected'
    WHEN vr.compatible_research_release_id = rp.research_release_id
      AND vr.compatible_research_manifest_sha256 = rp.manifest_sha256
      THEN 'compatible' ELSE 'release_version_mismatch' END
    AS visual_registry_state
FROM release.public_channel pc
JOIN release.research_current_pointer rp ON rp.channel = pc.channel
LEFT JOIN release.research_release rr
  ON rr.research_release_id = rp.research_release_id
LEFT JOIN release.visual_current_pointer vp ON vp.channel = rp.channel
LEFT JOIN release.visual_registry_release vr
  ON vr.visual_registry_release_id = vp.visual_registry_release_id;

CREATE VIEW api_v1.current_object
WITH (security_barrier = true)
AS
SELECT rr.release_token AS research_release_id,
  rp.manifest_sha256 AS research_manifest_sha256,
  CASE WHEN vr.compatible_research_release_id = rp.research_release_id
      AND vr.compatible_research_manifest_sha256 = rp.manifest_sha256
    THEN vr.registry_version END AS visual_registry_version,
  CASE WHEN vr.compatible_research_release_id = rp.research_release_id
      AND vr.compatible_research_manifest_sha256 = rp.manifest_sha256
    THEN vp.manifest_sha256 END AS visual_registry_sha256,
  CASE WHEN vp.visual_registry_release_id IS NULL THEN 'not_selected'
    WHEN vr.compatible_research_release_id = rp.research_release_id
      AND vr.compatible_research_manifest_sha256 = rp.manifest_sha256
      THEN 'compatible' ELSE 'release_version_mismatch' END
    AS visual_registry_state,
  ro.archive_object_id AS object_id, ro.object_urn,
  ro.legacy_surface_id AS surface_id, ro.title,
  ro.publication_layer, ro.acceptance_state,
  ev.external_visual_reference_id AS visual_reference_id,
  ev.visual_reference_urn, ev.effective_delivery_mode,
  ev.reason_code AS visual_reason_code,
  ev.machine_reason_code AS visual_machine_reason_code,
  ev.pixel_health_state,
  ev.attribution_values, ev.required_statement_values,
  ev.overlay_sha256 AS takedown_overlay_sha256,
  ev.canonical_record_url, ev.source_viewer_url, ev.remote_image_url
FROM release.public_channel pc
JOIN release.research_current_pointer rp ON rp.channel = pc.channel
JOIN release.research_release rr
  ON rr.research_release_id = rp.research_release_id
  AND rr.release_state = 'sealed'
  AND EXISTS (SELECT 1 FROM release.research_release_verification verified
    WHERE verified.research_release_id = rr.research_release_id
      AND verified.manifest_sha256 = rr.manifest_sha256
      AND verified.verified)
JOIN release.research_release_object ro
  ON ro.research_release_id = rr.research_release_id
  AND ro.acceptance_state = 'accepted'
  AND ro.publication_layer = 'active'
LEFT JOIN release.visual_current_pointer vp ON vp.channel = rp.channel
LEFT JOIN release.visual_registry_release vr
  ON vr.visual_registry_release_id = vp.visual_registry_release_id
  AND vr.release_state = 'sealed'
  AND EXISTS (SELECT 1 FROM release.visual_registry_verification verified
    WHERE verified.visual_registry_release_id = vr.visual_registry_release_id
      AND verified.manifest_sha256 = vr.manifest_sha256
      AND verified.verified)
LEFT JOIN release.effective_visual_entry ev
  ON ev.visual_registry_release_id = vr.visual_registry_release_id
  AND ev.archive_object_id = ro.archive_object_id
  AND vr.compatible_research_release_id = rp.research_release_id
  AND vr.compatible_research_manifest_sha256 = rp.manifest_sha256;

CREATE VIEW api_v1.research_release_descriptor
WITH (security_barrier = true)
AS
SELECT DISTINCT r.release_token AS research_release_id,
  r.manifest_sha256 AS research_manifest_sha256,
  r.schema_version, r.model_version, r.sealed_at,
  (SELECT count(*) FROM release.research_release_object o
    WHERE o.research_release_id = r.research_release_id
      AND o.acceptance_state = 'accepted'
      AND o.publication_layer = 'active') AS object_count,
  (SELECT count(*) FROM release.research_release_relation rel
    WHERE rel.research_release_id = r.research_release_id)
    AS accepted_relation_projection_count,
  (SELECT count(*) FROM release.trace_projection_edge edge
    WHERE edge.research_release_id = r.research_release_id)
    AS trace_projection_edge_count
FROM release.research_publication_history published
JOIN release.research_release r
  ON r.research_release_id = published.research_release_id
  AND r.manifest_sha256 = published.manifest_sha256
JOIN release.research_release_verification verified
  ON verified.research_release_id = r.research_release_id
  AND verified.manifest_sha256 = r.manifest_sha256
  AND verified.verified
WHERE r.release_state = 'sealed';

RESET ROLE;
