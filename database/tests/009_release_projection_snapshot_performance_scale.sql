\set ON_ERROR_STOP on
\if :{?object_count}
\else
  \quit 64
\endif
\if :{?membership_count}
\else
  \quit 64
\endif
\if :{?scale_tag}
\else
  \quit 64
\endif
\if :{?release_id}
\else
  \quit 64
\endif
\if :{?event_id}
\else
  \quit 64
\endif
\if :{?candidate_event_id}
\else
  \quit 64
\endif

BEGIN ISOLATION LEVEL SERIALIZABLE;
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.create_research_release(
  :'release_id'::uuid, :'scale_tag'::core.release_token, 'schema-v49.0','model-v49.0',
  :'event_id'::uuid, repeat('d',64));
SELECT release.build_research_launch_snapshot_v5(
  :'release_id'::uuid,'a0000000-0000-4000-8000-000000000003',
  'a8000000-0000-4000-8000-000000000010',:'candidate_event_id'::uuid,repeat('e',64)) AS candidate_fingerprint \gset
RESET SESSION AUTHORIZATION;
SELECT jsonb_build_object(
  'objectCount',(SELECT count(*) FROM release.research_release_object WHERE research_release_id=:'release_id'::uuid),
  'membershipCount',(SELECT count(*) FROM release.research_folder_membership_projection_v3 WHERE research_release_id=:'release_id'::uuid),
  'componentManifest',release.research_launch_component_manifest_sha_v5(:'release_id'::uuid),
  'candidateFingerprint',:'candidate_fingerprint',
  'content',(SELECT projection_content_sha256 FROM release.research_launch_build_receipt_v3 WHERE research_release_id=:'release_id'::uuid)
)::text;
COMMIT;
\echo PHASE2SP_SCALE_V5=PASS
