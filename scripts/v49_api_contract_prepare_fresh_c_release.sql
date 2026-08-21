\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL SERIALIZABLE;
SET CONSTRAINTS ALL DEFERRED;

DO $preflight$
BEGIN
  IF (SELECT count(*) FROM core.archive_object) <> 15923
    OR (SELECT count(*) FROM research.corpus_membership WHERE disposition='eligible') <> 7995
    OR EXISTS (SELECT 1 FROM release.research_release) THEN
    RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='V49_API_CONTRACT_FRESH_C_PREFLIGHT_FAILED';
  END IF;
END
$preflight$;

SELECT migration_batch_id AS canonical_batch_id, canonical_input_asset_id AS canonical_asset_id
FROM raw.migration_batch
WHERE completed_at IS NOT NULL
ORDER BY completed_at DESC, migration_batch_id DESC
LIMIT 1 \gset

SELECT corpus_version_id AS public_corpus_version_id
FROM research.corpus_version
WHERE version_token='v48-candidate-v1'
ORDER BY corpus_version_id
LIMIT 1 \gset

INSERT INTO release.validation_profile(
  validation_profile_id,boundary_kind,profile_token,profile_sha256,approved_at
) VALUES (
  '99000000-0000-4000-8000-000000000001','research','model-v49.0',repeat('9',64),
  '2026-08-21T00:00:00Z'
);

INSERT INTO release.validation_profile_requirement(
  validation_profile_id,receipt_kind,requirement_ordinal
)
SELECT '99000000-0000-4000-8000-000000000001'::uuid,kind,ordinality::integer
FROM unnest(ARRAY[
  'research_frozen_asset_authority','research_migration_query_identity',
  'research_population_and_count_parity','research_corpus_missingness_concentration',
  'research_fk_orphan_integrity','research_predicate_relation_epistemic_registry',
  'research_claim_projection_eligibility','research_unknown_relation_isolation',
  'research_projection_fingerprint','research_deterministic_asset_inventory',
  'research_role_grant_security'
]::release.validation_receipt_kind[]) WITH ORDINALITY AS required(kind,ordinality);

INSERT INTO research.launch_snapshot_policy_v3(
  launch_snapshot_policy_id,policy_token,public_corpus_version_id,
  projection_query_pack_sha256,selection_policy_sha256,
  registry_corpus_policy_sha256,created_at
) VALUES (
  '99000000-0000-4000-8000-000000000010','v49-api-contract-policy',
  :'public_corpus_version_id'::uuid,repeat('a',64),repeat('b',64),repeat('c',64),
  '2026-08-21T00:00:00Z'
);

INSERT INTO research.public_source_citation_allowlist_v3(
  source_asset_id,citation_label,created_at
) VALUES (
  :'canonical_asset_id'::uuid,'v48 Candidate JSON canonical release',
  '2026-08-21T00:00:00Z'
);

INSERT INTO release.public_channel(channel,public_contract_version,created_at)
VALUES ('public','v49-api-contract-v1','2026-08-21T00:00:00Z');

SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.create_research_release(
  '99000000-0000-4000-8000-000000000100','v49-api-contract-fresh-c',
  'schema-v49.0','model-v49.0',
  '99000000-0000-4000-8000-000000000101',repeat('1',64));
SELECT release.build_research_launch_snapshot_v5(
  '99000000-0000-4000-8000-000000000100',:'canonical_batch_id'::uuid,
  '99000000-0000-4000-8000-000000000010',
  '99000000-0000-4000-8000-000000000102',repeat('2',64)) AS candidate_fingerprint \gset
RESET SESSION AUTHORIZATION;

SELECT release.canonical_jsonb_sha256(jsonb_build_object(
  'format','gda-v49-research-validation-v5',
  'releaseId','99000000-0000-4000-8000-000000000100'::uuid,
  'candidateFingerprint',:'candidate_fingerprint'::core.sha256_hex,
  'componentManifestSha256',release.research_launch_component_manifest_sha_v5(
    '99000000-0000-4000-8000-000000000100'))) AS validation_sha \gset

SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.validate_research_launch_snapshot_v5(
  '99000000-0000-4000-8000-000000000100',:'validation_sha',
  '99000000-0000-4000-8000-000000000103',repeat('3',64));
SELECT release.seal_research_launch_snapshot_v5(
  '99000000-0000-4000-8000-000000000100',
  '99000000-0000-4000-8000-000000000104',
  '99000000-0000-4000-8000-000000000105',repeat('4',64)) AS manifest_sha \gset
RESET SESSION AUTHORIZATION;

SELECT release.compute_research_verification_sidecar_sha(
  '99000000-0000-4000-8000-000000000100',:'manifest_sha',
  'v49-api-contract-verifier-v1') AS sidecar_sha \gset

SET SESSION AUTHORIZATION gda_v49_phase2a_reviewer;
SELECT release.record_research_launch_verification_v5(
  '99000000-0000-4000-8000-000000000106',
  '99000000-0000-4000-8000-000000000100',:'manifest_sha',
  'v49-api-contract-verifier-v1',:'sidecar_sha',
  '99000000-0000-4000-8000-000000000107',repeat('5',64));
RESET SESSION AUTHORIZATION;

SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.initialize_research_current('public');
SELECT * FROM release.promote_research_current_cas(
  '99000000-0000-4000-8000-000000000108','public',0,NULL,NULL,
  '99000000-0000-4000-8000-000000000100');
RESET SESSION AUTHORIZATION;

SET CONSTRAINTS ALL IMMEDIATE;
COMMIT;

SELECT jsonb_build_object(
  'status','PASS',
  'releaseId',research_release_id,
  'manifestSha256',research_manifest_sha256,
  'objectCount',object_count,
  'relationCount',relation_count,
  'traceEligibleObjectCount',trace_eligible_object_count,
  'searchDocumentCount',(SELECT count(*) FROM release.research_search_document_projection_v3
    WHERE research_release_id='99000000-0000-4000-8000-000000000100'),
  'folderMembershipCount',(SELECT count(*) FROM release.research_folder_membership_projection_v3
    WHERE research_release_id='99000000-0000-4000-8000-000000000100'),
  'projectionContentSha256',(SELECT projection_content_sha256
    FROM release.research_launch_build_receipt_v3
    WHERE research_release_id='99000000-0000-4000-8000-000000000100')
)::text
FROM api_v1.sealed_research_release_descriptor
WHERE research_release_id='v49-api-contract-fresh-c';
