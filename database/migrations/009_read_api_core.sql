\set ON_ERROR_STOP on
-- Forward-only Phase 2C read projection.  These views deliberately join an
-- explicit sealed pair; they never resolve release.current themselves.
SET ROLE gda_v49_phase2a_schema_owner;

CREATE VIEW api_v1.sealed_research_release_descriptor
WITH (security_barrier = true)
AS
SELECT r.research_release_id::text AS research_release_key,
  r.release_token AS research_release_id,
  r.manifest_sha256 AS research_manifest_sha256,
  r.schema_version, r.model_version, r.sealed_at,
  (SELECT count(*) FROM release.research_release_object o
    WHERE o.research_release_id = r.research_release_id
      AND o.acceptance_state = 'accepted' AND o.publication_layer = 'active')
    AS object_count,
  (SELECT count(*) FROM release.research_release_relation rel
    WHERE rel.research_release_id = r.research_release_id) AS relation_count,
  (SELECT count(*) FROM release.trace_projection_node n
    WHERE n.research_release_id = r.research_release_id
      AND n.archive_object_id IS NOT NULL) AS trace_eligible_object_count
FROM release.research_release r
JOIN release.research_release_verification verified
  ON verified.research_release_id = r.research_release_id
  AND verified.manifest_sha256 = r.manifest_sha256 AND verified.verified
WHERE r.release_state = 'sealed';

CREATE VIEW api_v1.sealed_surface
WITH (security_barrier = true)
AS
SELECT d.research_release_id, d.research_manifest_sha256,
  o.legacy_surface_id AS surface_id, o.title,
  o.publication_layer::text AS publication_layer,
  o.object_urn::text AS object_urn
FROM api_v1.sealed_research_release_descriptor d
JOIN release.research_release_object o
  ON o.research_release_id::text = d.research_release_key
WHERE o.acceptance_state = 'accepted' AND o.publication_layer = 'active'
  AND o.legacy_surface_id IS NOT NULL;

CREATE INDEX research_release_object_read_api_keyset_idx
  ON release.research_release_object (research_release_id, legacy_surface_id)
  WHERE acceptance_state = 'accepted'
    AND publication_layer = 'active' AND legacy_surface_id IS NOT NULL;

CREATE INDEX trace_projection_node_read_api_count_idx
  ON release.trace_projection_node (research_release_id, archive_object_id)
  WHERE archive_object_id IS NOT NULL;

RESET ROLE;
