\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL SERIALIZABLE;
SET CONSTRAINTS ALL DEFERRED;
\ir phase2s_32_snapshot.sql

INSERT INTO release.public_channel VALUES(
  'public','v49-db-closure-api-smoke',clock_timestamp());

SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.create_research_release(
  '98000000-0000-4000-8000-000000000001','v49-db-closure-api-v1',
  'schema-v49.0','model-v49.0',
  '98000000-0000-4000-8000-000000000002',repeat('1',64));
SELECT release.build_research_launch_snapshot_v5(
  '98000000-0000-4000-8000-000000000001',
  '10000000-0000-4000-8000-000000000003',
  '80000000-0000-4000-8000-000000000010',
  '98000000-0000-4000-8000-000000000003',repeat('2',64))
  AS candidate_fingerprint \gset
RESET SESSION AUTHORIZATION;

SELECT release.canonical_jsonb_sha256(jsonb_build_object(
  'format','gda-v49-research-validation-v5',
  'releaseId','98000000-0000-4000-8000-000000000001'::uuid,
  'candidateFingerprint',:'candidate_fingerprint'::core.sha256_hex,
  'componentManifestSha256',release.research_launch_component_manifest_sha_v5(
    '98000000-0000-4000-8000-000000000001'))) AS validation_sha \gset
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.validate_research_launch_snapshot_v5(
  '98000000-0000-4000-8000-000000000001',:'validation_sha',
  '98000000-0000-4000-8000-000000000004',repeat('3',64));
SELECT release.seal_research_launch_snapshot_v5(
  '98000000-0000-4000-8000-000000000001',
  '98000000-0000-4000-8000-000000000005',
  '98000000-0000-4000-8000-000000000006',repeat('4',64)) AS manifest_sha \gset
RESET SESSION AUTHORIZATION;

SELECT release.compute_research_verification_sidecar_sha(
  '98000000-0000-4000-8000-000000000001',:'manifest_sha',
  'v49-db-closure-verifier-v1') AS sidecar_sha \gset
SET SESSION AUTHORIZATION gda_v49_phase2a_reviewer;
SELECT release.record_research_launch_verification_v5(
  '98000000-0000-4000-8000-000000000007',
  '98000000-0000-4000-8000-000000000001',:'manifest_sha',
  'v49-db-closure-verifier-v1',:'sidecar_sha',
  '98000000-0000-4000-8000-000000000008',repeat('5',64));
RESET SESSION AUTHORIZATION;

SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.initialize_research_current('public');
SELECT * FROM release.promote_research_current_cas(
  '98000000-0000-4000-8000-000000000009','public',0,NULL,NULL,
  '98000000-0000-4000-8000-000000000001');
RESET SESSION AUTHORIZATION;

SET CONSTRAINTS ALL IMMEDIATE;
COMMIT;

SELECT jsonb_build_object(
  'researchReleaseId','v49-db-closure-api-v1',
  'researchReleaseUuid','98000000-0000-4000-8000-000000000001',
  'researchManifestSha256',manifest_sha256,
  'surfaceId',(SELECT min(surface_id) FROM api_v1.sealed_surface
    WHERE research_release_id='v49-db-closure-api-v1'),
  'objectCount',(SELECT object_count FROM api_v1.sealed_research_release_descriptor
    WHERE research_release_id='v49-db-closure-api-v1'))
FROM release.research_release
WHERE research_release_id='98000000-0000-4000-8000-000000000001';
