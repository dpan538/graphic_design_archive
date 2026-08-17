\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL SERIALIZABLE;
\ir ../fixtures/phase2s_scale_snapshot.sql
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.create_research_release(
  :'release_id'::uuid, :'release_token'::core.release_token, 'schema-v49.0','model-v49.0',
  :'event_id'::uuid, repeat('d',64));
SELECT release.build_research_launch_snapshot_v4(
  :'release_id'::uuid,'a0000000-0000-4000-8000-000000000003',
  'a8000000-0000-4000-8000-000000000010',:'candidate_event_id'::uuid,repeat('e',64)) AS candidate_fingerprint \gset
RESET SESSION AUTHORIZATION;
SELECT jsonb_build_object(
  'objectCount',(SELECT count(*) FROM release.research_release_object WHERE research_release_id=:'release_id'::uuid),
  'membershipCount',(SELECT count(*) FROM release.research_folder_membership_projection_v3 WHERE research_release_id=:'release_id'::uuid),
  'componentManifest',release.research_launch_component_manifest_sha_v4(:'release_id'::uuid),
  'candidateFingerprint',:'candidate_fingerprint',
  'content',release.research_launch_content_sha_v4(:'release_id'::uuid)
)::text;
COMMIT;
\echo PHASE2S_SCALE=PASS
