\set ON_ERROR_STOP on
BEGIN;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
SET CONSTRAINTS ALL DEFERRED;

CREATE FUNCTION pg_temp.assert_true(p_condition boolean, p_label text)
RETURNS void LANGUAGE plpgsql AS $function$
BEGIN
  IF NOT COALESCE(p_condition, false) THEN
    RAISE EXCEPTION 'ASSERTION_FAILED: %', p_label;
  END IF;
END
$function$;

CREATE FUNCTION pg_temp.expect_error(
  p_sql text, p_expected_states text[], p_label text
)
RETURNS void LANGUAGE plpgsql AS $function$
DECLARE v_failed boolean := false; v_state text;
BEGIN
  BEGIN
    EXECUTE p_sql;
    SET CONSTRAINTS ALL IMMEDIATE;
  EXCEPTION WHEN OTHERS THEN
    v_failed := true;
    v_state := SQLSTATE;
  END;
  SET CONSTRAINTS ALL DEFERRED;
  IF NOT v_failed THEN
    RAISE EXCEPTION 'EXPECTED_ERROR_NOT_RAISED: %', p_label;
  END IF;
  IF NOT (v_state = ANY (p_expected_states)) THEN
    RAISE EXCEPTION 'WRONG_SQLSTATE: % got %, expected %',
      p_label, v_state, p_expected_states;
  END IF;
END
$function$;

\ir ../fixtures/phase2a_base.sql

INSERT INTO release.public_channel VALUES (
  'public', 'read-api-v1', clock_timestamp());

-- A canonical relation accepted solely by an evidence-bearing effective
-- curator decision must be releasable without inventing a claim epistemic class.
INSERT INTO research.relation_type VALUES (
  '70000000-0000-4000-8000-000000000020',
  'fixture_decision_supported', true, 'archive_object', 'archive_object',
  true, 'fixture-evidence-v1', false, false,
  'Decision-only release-path fixture', 'phase2a-fixture-v1');
INSERT INTO research.semantic_relation (
  semantic_relation_id, subject_endpoint_id, relation_type_id,
  object_endpoint_id, origin, status, created_at
) VALUES (
  '70000000-0000-4000-8000-000000000021',
  '40000000-0000-4000-8000-000000000007',
  '70000000-0000-4000-8000-000000000020',
  '40000000-0000-4000-8000-000000000008',
  'curator_created', 'accepted', clock_timestamp());
INSERT INTO research.relation_review_decision VALUES (
  '70000000-0000-4000-8000-000000000022',
  '70000000-0000-4000-8000-000000000021', 'accept',
  'fixture-reviewer', NULL, 'Decision-only acceptance evidence', NULL,
  clock_timestamp());
INSERT INTO research.relation_decision_evidence VALUES (
  '70000000-0000-4000-8000-000000000022',
  '30000000-0000-4000-8000-000000000003', 'supports');

SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.create_research_release(
  '70000000-0000-4000-8000-000000000001',
  'phase2a-empty-trace-v1', 'schema-v49.0', 'model-v49.0',
  '70000000-0000-4000-8000-000000000002', repeat('1', 64));
SELECT release.add_research_source_lineage_to_draft(
  '70000000-0000-4000-8000-000000000001', 'v48_candidate_json',
  '10000000-0000-4000-8000-000000000001', repeat('a', 40));
SELECT release.add_research_source_lineage_to_draft(
  '70000000-0000-4000-8000-000000000001',
  'v48_sqlite_reconciliation',
  '10000000-0000-4000-8000-000000000021', repeat('a', 40));
SELECT release.add_research_source_lineage_to_draft(
  '70000000-0000-4000-8000-000000000001',
  'v48_transfer_manifest_json',
  '10000000-0000-4000-8000-000000000022', repeat('a', 40));
SELECT release.add_research_source_lineage_to_draft(
  '70000000-0000-4000-8000-000000000001',
  'v48_transfer_manifest_csv',
  '10000000-0000-4000-8000-000000000023', repeat('a', 40));
SELECT release.add_research_source_lineage_to_draft(
  '70000000-0000-4000-8000-000000000001', 'v48_trace_manifest',
  '10000000-0000-4000-8000-000000000024', repeat('a', 40));
SELECT release.set_research_projection_set_to_draft(
  '70000000-0000-4000-8000-000000000001', 'fixture-db-snapshot',
  repeat('1', 64), repeat('2', 64));
SELECT release.set_research_registry_snapshot_to_draft(
  '70000000-0000-4000-8000-000000000001',
  repeat('3', 64), repeat('4', 64), repeat('5', 64));
SELECT release.copy_research_corpus_snapshot_to_draft(
  '70000000-0000-4000-8000-000000000001',
  '40000000-0000-4000-8000-000000000002',
  '40000000-0000-4000-8000-000000000021',
  '40000000-0000-4000-8000-000000000022', repeat('6', 64));
SELECT release.add_research_count_snapshot_to_draft(
  '70000000-0000-4000-8000-000000000001', 'fixture-object-count',
  'fixture operational archive objects', 'archive_object',
  repeat('7', 64), 2);
SELECT release.add_research_asset_to_draft(
  '70000000-0000-4000-8000-000000000001', 'objects.json',
  'release-object-projection', 'application/json', 'identity',
  'schema-v49.0', 2, 2, repeat('8', 64), '001-objects', NULL, NULL);
SELECT release.add_research_object_to_draft(
  '70000000-0000-4000-8000-000000000001',
  '40000000-0000-4000-8000-000000000002',
  '20000000-0000-4000-8000-000000000001');
SELECT release.add_research_object_to_draft(
  '70000000-0000-4000-8000-000000000001',
  '40000000-0000-4000-8000-000000000002',
  '20000000-0000-4000-8000-000000000002');
SELECT release.add_research_relation_to_draft(
  '70000000-0000-4000-8000-000000000001',
  '70000000-0000-4000-8000-000000000021', NULL);
RESET SESSION AUTHORIZATION;

SELECT release.compute_research_candidate_fingerprint(
  '70000000-0000-4000-8000-000000000001') AS research_fp \gset
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.close_research_candidate(
  '70000000-0000-4000-8000-000000000001', :'research_fp',
  '70000000-0000-4000-8000-000000000003', repeat('2', 64));
RESET SESSION AUTHORIZATION;

SET SESSION AUTHORIZATION gda_v49_phase2a_reviewer;
DO $record_research_receipts$
DECLARE k release.validation_receipt_kind; b bytea;
BEGIN
  FOREACH k IN ARRAY ARRAY[
    'research_frozen_asset_authority',
    'research_migration_query_identity',
    'research_population_and_count_parity',
    'research_corpus_missingness_concentration',
    'research_fk_orphan_integrity',
    'research_predicate_relation_epistemic_registry',
    'research_claim_projection_eligibility',
    'research_unknown_relation_isolation',
    'research_projection_fingerprint',
    'research_deterministic_asset_inventory',
    'research_role_grant_security'
  ]::release.validation_receipt_kind[]
  LOOP
    b := release.build_validation_receipt_bytes(
      'research', '70000000-0000-4000-8000-000000000001', k,
      'phase2a-test-v1', repeat('a', 64));
    PERFORM release.record_research_validation_receipt(
      gen_random_uuid(), '70000000-0000-4000-8000-000000000001', k,
      'phase2a-test-v1', repeat('a', 64), b, gen_random_uuid());
  END LOOP;
END
$record_research_receipts$;
RESET SESSION AUTHORIZATION;
SELECT research_validation_receipt_id AS research_receipt_id,
  receipt_sha256 AS research_receipt_sha
FROM release.research_validation_receipt
WHERE research_release_id = '70000000-0000-4000-8000-000000000001'
ORDER BY receipt_kind LIMIT 1 \gset
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.validate_research_release(
  '70000000-0000-4000-8000-000000000001',
  :'research_receipt_id', 'phase2a-test-v1',
  :'research_receipt_sha',
  '70000000-0000-4000-8000-000000000005', repeat('3', 64));
SELECT release.seal_research_release(
  '70000000-0000-4000-8000-000000000001',
  '70000000-0000-4000-8000-000000000006',
  '70000000-0000-4000-8000-000000000007', repeat('4', 64));
RESET SESSION AUTHORIZATION;

SELECT manifest_sha256 AS research_manifest_sha
FROM release.research_release
WHERE research_release_id = '70000000-0000-4000-8000-000000000001'
\gset
SELECT release.compute_research_verification_sidecar_sha(
  '70000000-0000-4000-8000-000000000001', :'research_manifest_sha',
  'phase2a-independent-v1') AS research_sidecar_sha \gset

SET SESSION AUTHORIZATION gda_v49_phase2a_reviewer;
SELECT release.record_research_verification(
  '70000000-0000-4000-8000-000000000008',
  '70000000-0000-4000-8000-000000000001', :'research_manifest_sha',
  'phase2a-independent-v1', :'research_sidecar_sha',
  '70000000-0000-4000-8000-000000000009', repeat('5', 64));
RESET SESSION AUTHORIZATION;

-- Fractional epistemic measurements remain exact decimal strings in the JCS
-- payload.  A normal computed-association score must survive the complete
-- candidate -> validated -> sealed path and be timezone invariant.
INSERT INTO research.epistemic_class VALUES (
  '73000000-0000-4000-8000-000000000001',
  'computed_association', true, true, false,
  'Fractional computed-association fixture',
  'phase2a-computed-profile-v1', repeat('1',64));
INSERT INTO research.analysis_run (
  analysis_run_id, method_version, parameters_sha256,
  input_release_id, input_manifest_sha256, output_sha256, executed_at,
  software_sha256, input_corpus_version_id,
  input_corpus_policy_sha256, score_value, score_unit,
  uncertainty_lower, uncertainty_upper, threshold_value, threshold_unit
) VALUES (
  '73000000-0000-4000-8000-000000000002',
  'phase2a-computed-method-v1', repeat('2',64),
  '70000000-0000-4000-8000-000000000001', :'research_manifest_sha',
  repeat('3',64), clock_timestamp(), repeat('4',64),
  '40000000-0000-4000-8000-000000000002', repeat('6',64),
  0.7500, 'probability', 0.100, 0.9000, 0.500, 'probability'
);
INSERT INTO research.claim (claim_id, created_at) VALUES (
  '73000000-0000-4000-8000-000000000003', clock_timestamp());
INSERT INTO research.claim_revision (
  claim_revision_id, claim_id, revision_number, epistemic_class_id,
  status, workflow_state, claimant_agent_id, wording,
  temporal_qualifier_id, spatial_qualifier_id, analysis_run_id,
  supersedes_claim_revision_id, created_at,
  claim_date_or_version, claim_stance
) VALUES (
  '73000000-0000-4000-8000-000000000004',
  '73000000-0000-4000-8000-000000000003', 1,
  '73000000-0000-4000-8000-000000000001',
  'accepted', 'resolved', NULL,
  'Synthetic fractional computed association', NULL, NULL,
  '73000000-0000-4000-8000-000000000002', NULL,
  clock_timestamp(), 'phase2a-computed-claim-v1', 'supports'
);
INSERT INTO research.claim_evidence VALUES (
  '73000000-0000-4000-8000-000000000004',
  '30000000-0000-4000-8000-000000000003', 'supports');
INSERT INTO research.claim_review_decision VALUES (
  '73000000-0000-4000-8000-000000000005',
  '73000000-0000-4000-8000-000000000004', 'accept', false,
  'fixture-reviewer', 'Fractional computed association accepted', NULL,
  clock_timestamp());
INSERT INTO research.claim_decision_evidence VALUES (
  '73000000-0000-4000-8000-000000000005',
  '30000000-0000-4000-8000-000000000003', 'supports');

SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.create_research_release(
  '73000000-0000-4000-8000-000000000010',
  'phase2a-fractional-computed-v1', 'schema-v49.0', 'model-v49.0',
  '73000000-0000-4000-8000-000000000011', repeat('5',64));
SELECT release.add_research_source_lineage_to_draft(
  '73000000-0000-4000-8000-000000000010', 'v48_candidate_json',
  '10000000-0000-4000-8000-000000000001', repeat('a',40));
SELECT release.add_research_source_lineage_to_draft(
  '73000000-0000-4000-8000-000000000010',
  'v48_sqlite_reconciliation',
  '10000000-0000-4000-8000-000000000021', repeat('a',40));
SELECT release.add_research_source_lineage_to_draft(
  '73000000-0000-4000-8000-000000000010',
  'v48_transfer_manifest_json',
  '10000000-0000-4000-8000-000000000022', repeat('a',40));
SELECT release.add_research_source_lineage_to_draft(
  '73000000-0000-4000-8000-000000000010',
  'v48_transfer_manifest_csv',
  '10000000-0000-4000-8000-000000000023', repeat('a',40));
SELECT release.add_research_source_lineage_to_draft(
  '73000000-0000-4000-8000-000000000010', 'v48_trace_manifest',
  '10000000-0000-4000-8000-000000000024', repeat('a',40));
SELECT release.set_research_projection_set_to_draft(
  '73000000-0000-4000-8000-000000000010',
  'fixture-computed-db-snapshot', repeat('6',64), repeat('7',64));
SELECT release.set_research_registry_snapshot_to_draft(
  '73000000-0000-4000-8000-000000000010',
  repeat('8',64), repeat('9',64), repeat('a',64));
SELECT release.copy_research_corpus_snapshot_to_draft(
  '73000000-0000-4000-8000-000000000010',
  '40000000-0000-4000-8000-000000000002',
  '40000000-0000-4000-8000-000000000021',
  '40000000-0000-4000-8000-000000000022', repeat('6',64));
SELECT release.add_research_count_snapshot_to_draft(
  '73000000-0000-4000-8000-000000000010',
  'fixture-computed-object-count', 'computed fixture objects',
  'archive_object', repeat('b',64), 1);
SELECT release.add_research_asset_to_draft(
  '73000000-0000-4000-8000-000000000010',
  'computed-claims.json', 'release-claim-projection',
  'application/json', 'identity', 'schema-v49.0', 1, 1,
  repeat('c',64), '001-computed-claims', NULL, NULL);
SELECT release.add_research_object_to_draft(
  '73000000-0000-4000-8000-000000000010',
  '40000000-0000-4000-8000-000000000002',
  '20000000-0000-4000-8000-000000000001');
SELECT release.add_research_claim_to_draft(
  '73000000-0000-4000-8000-000000000010',
  '73000000-0000-4000-8000-000000000004');
RESET SESSION AUTHORIZATION;

SELECT release.compute_research_candidate_fingerprint(
  '73000000-0000-4000-8000-000000000010') AS computed_fp_utc \gset
SET TIME ZONE 'Pacific/Honolulu';
SELECT release.compute_research_candidate_fingerprint(
  '73000000-0000-4000-8000-000000000010') AS computed_fp_non_utc \gset
SET TIME ZONE 'UTC';
SELECT pg_temp.assert_true(
  :'computed_fp_utc' = :'computed_fp_non_utc',
  'fractional computed candidate fingerprint is timezone invariant');
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.close_research_candidate(
  '73000000-0000-4000-8000-000000000010', :'computed_fp_utc',
  '73000000-0000-4000-8000-000000000012', repeat('d',64));
RESET SESSION AUTHORIZATION;
SET SESSION AUTHORIZATION gda_v49_phase2a_reviewer;
DO $record_computed_receipts$
DECLARE k release.validation_receipt_kind; b bytea;
BEGIN
  FOREACH k IN ARRAY ARRAY[
    'research_frozen_asset_authority',
    'research_migration_query_identity',
    'research_population_and_count_parity',
    'research_corpus_missingness_concentration',
    'research_fk_orphan_integrity',
    'research_predicate_relation_epistemic_registry',
    'research_claim_projection_eligibility',
    'research_unknown_relation_isolation',
    'research_projection_fingerprint',
    'research_deterministic_asset_inventory',
    'research_role_grant_security'
  ]::release.validation_receipt_kind[]
  LOOP
    b := release.build_validation_receipt_bytes(
      'research', '73000000-0000-4000-8000-000000000010', k,
      'phase2a-computed-test-v1', repeat('e',64));
    PERFORM release.record_research_validation_receipt(
      gen_random_uuid(), '73000000-0000-4000-8000-000000000010', k,
      'phase2a-computed-test-v1', repeat('e',64), b, gen_random_uuid());
  END LOOP;
END
$record_computed_receipts$;
RESET SESSION AUTHORIZATION;
SELECT research_validation_receipt_id AS computed_receipt_id,
  receipt_sha256 AS computed_receipt_sha
FROM release.research_validation_receipt
WHERE research_release_id = '73000000-0000-4000-8000-000000000010'
ORDER BY receipt_kind LIMIT 1 \gset
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.validate_research_release(
  '73000000-0000-4000-8000-000000000010',
  :'computed_receipt_id', 'phase2a-computed-test-v1',
  :'computed_receipt_sha',
  '73000000-0000-4000-8000-000000000013', repeat('f',64));
SELECT release.seal_research_release(
  '73000000-0000-4000-8000-000000000010',
  '73000000-0000-4000-8000-000000000014',
  '73000000-0000-4000-8000-000000000015', repeat('1',64));
RESET SESSION AUTHORIZATION;
SELECT pg_temp.assert_true(
  (SELECT release_state FROM release.research_release
    WHERE research_release_id =
      '73000000-0000-4000-8000-000000000010') = 'sealed'
  AND (SELECT score_value FROM release.research_release_analysis_run
    WHERE research_release_id =
      '73000000-0000-4000-8000-000000000010'
      AND analysis_run_id =
        '73000000-0000-4000-8000-000000000002') = 0.7500,
  'fractional computed association validates and seals without numeric drift');

SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.create_research_release(
  '70000000-0000-4000-8000-000000000010',
  'phase2a-unsealed-v1', 'schema-v49.0', 'model-v49.0',
  '70000000-0000-4000-8000-000000000011', repeat('6', 64));
SELECT release.initialize_research_current('public');
SELECT release.initialize_visual_current('public');
SELECT * FROM release.promote_research_current_cas(
  '70000000-0000-4000-8000-000000000012', 'public',
  0, NULL, NULL, '70000000-0000-4000-8000-000000000010');
SELECT * FROM release.promote_research_current_cas(
  '70000000-0000-4000-8000-000000000013', 'public',
  0, NULL, NULL, '70000000-0000-4000-8000-000000000001');
SELECT * FROM release.promote_research_current_cas(
  '70000000-0000-4000-8000-000000000014', 'public',
  0, NULL, NULL, '70000000-0000-4000-8000-000000000001');
SELECT * FROM release.promote_research_current_cas(
  '70000000-0000-4000-8000-000000000015', 'public',
  NULL, '70000000-0000-4000-8000-000000000001',
  :'research_manifest_sha', '70000000-0000-4000-8000-000000000001');
RESET SESSION AUTHORIZATION;

SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.create_visual_registry(
  '71000000-0000-4000-8000-000000000001', 'phase2a-zero-rights-v1',
  'schema-v49.0', 'model-v49.0',
  '70000000-0000-4000-8000-000000000001', :'research_manifest_sha',
  '71000000-0000-4000-8000-000000000002', repeat('7', 64));
SELECT release.set_visual_policy_input_to_draft(
  '71000000-0000-4000-8000-000000000001', repeat('1', 64),
  repeat('2', 64), repeat('3', 64), repeat('4', 64), repeat('5', 64));
SELECT release.snapshot_legacy_visual_baseline_to_draft(
  '71000000-0000-4000-8000-000000000001', repeat('6', 64));
SELECT release.add_visual_asset_to_draft(
  '71000000-0000-4000-8000-000000000001', 'entries.json',
  'visual-registry-projection', 'application/json', 'identity',
  'schema-v49.0', 2, 0, repeat('7', 64), '001-entries', NULL, NULL);
RESET SESSION AUTHORIZATION;

SELECT release.compute_visual_candidate_fingerprint(
  '71000000-0000-4000-8000-000000000001') AS visual_fp \gset
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.close_visual_candidate(
  '71000000-0000-4000-8000-000000000001', :'visual_fp',
  '71000000-0000-4000-8000-000000000003', repeat('8', 64));
RESET SESSION AUTHORIZATION;

SET SESSION AUTHORIZATION gda_v49_phase2a_reviewer;
DO $record_visual_receipts$
DECLARE k release.validation_receipt_kind; b bytea;
BEGIN
  FOREACH k IN ARRAY ARRAY[
    'visual_legacy_disposition',
    'visual_reference_bridge_provider_locator_identity',
    'visual_rights_policy_delivery_health_takedown',
    'visual_attribution_review_due',
    'visual_held_pixel_non_disclosure',
    'visual_research_compatibility',
    'visual_projection_fingerprint',
    'visual_deterministic_asset_inventory',
    'visual_role_grant_security'
  ]::release.validation_receipt_kind[]
  LOOP
    b := release.build_validation_receipt_bytes(
      'visual', '71000000-0000-4000-8000-000000000001', k,
      'phase2a-test-v1', repeat('f', 64));
    PERFORM release.record_visual_validation_receipt(
      gen_random_uuid(), '71000000-0000-4000-8000-000000000001', k,
      'phase2a-test-v1', repeat('f', 64), b, gen_random_uuid());
  END LOOP;
END
$record_visual_receipts$;
RESET SESSION AUTHORIZATION;
SELECT visual_validation_receipt_id AS visual_receipt_id,
  receipt_sha256 AS visual_receipt_sha
FROM release.visual_validation_receipt
WHERE visual_registry_release_id = '71000000-0000-4000-8000-000000000001'
ORDER BY receipt_kind LIMIT 1 \gset
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.validate_visual_registry(
  '71000000-0000-4000-8000-000000000001',
  :'visual_receipt_id', 'phase2a-test-v1',
  :'visual_receipt_sha',
  '71000000-0000-4000-8000-000000000005', repeat('9', 64));
SELECT release.seal_visual_registry(
  '71000000-0000-4000-8000-000000000001',
  '71000000-0000-4000-8000-000000000006',
  '71000000-0000-4000-8000-000000000007', repeat('a', 64));
RESET SESSION AUTHORIZATION;

SELECT manifest_sha256 AS visual_manifest_sha
FROM release.visual_registry_release
WHERE visual_registry_release_id = '71000000-0000-4000-8000-000000000001'
\gset
SELECT release.compute_visual_verification_sidecar_sha(
  '71000000-0000-4000-8000-000000000001', :'visual_manifest_sha',
  'phase2a-independent-v1') AS visual_sidecar_sha \gset

SET SESSION AUTHORIZATION gda_v49_phase2a_reviewer;
SELECT release.record_visual_verification(
  '71000000-0000-4000-8000-000000000008',
  '71000000-0000-4000-8000-000000000001', :'visual_manifest_sha',
  'phase2a-independent-v1', :'visual_sidecar_sha',
  '71000000-0000-4000-8000-000000000009', repeat('b', 64));
RESET SESSION AUTHORIZATION;

SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.create_visual_registry(
  '71000000-0000-4000-8000-000000000010', 'phase2a-unsealed-visual-v1',
  'schema-v49.0', 'model-v49.0',
  '70000000-0000-4000-8000-000000000001', :'research_manifest_sha',
  '71000000-0000-4000-8000-000000000011', repeat('c', 64));
SELECT * FROM release.promote_visual_current_cas(
  '71000000-0000-4000-8000-000000000012',
  'public', 1, '70000000-0000-4000-8000-000000000001',
  :'research_manifest_sha', 'public', 0, NULL, NULL,
  '71000000-0000-4000-8000-000000000010');
SELECT * FROM release.promote_visual_current_cas(
  '71000000-0000-4000-8000-000000000013',
  'public', 1, '70000000-0000-4000-8000-000000000001',
  :'research_manifest_sha', 'public', 0, NULL, NULL,
  '71000000-0000-4000-8000-000000000001');
SELECT * FROM release.promote_visual_current_cas(
  '71000000-0000-4000-8000-000000000014',
  'public', 1, '70000000-0000-4000-8000-000000000001',
  :'research_manifest_sha', 'public', 0, NULL, NULL,
  '71000000-0000-4000-8000-000000000001');
RESET SESSION AUTHORIZATION;

SET SESSION AUTHORIZATION gda_v49_phase2a_api_reader;
SELECT pg_temp.assert_true(
  (SELECT count(*) FROM api_v1.current_object
    WHERE remote_image_url IS NOT NULL
       OR canonical_record_url IS NOT NULL
       OR source_viewer_url IS NOT NULL) = 0,
  'zero-rights current registry contains no public locator');
RESET SESSION AUTHORIZATION;

SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.create_visual_registry(
  '72000000-0000-4000-8000-000000000001', 'phase2a-positive-control-v1',
  'schema-v49.0', 'model-v49.0',
  '70000000-0000-4000-8000-000000000001', :'research_manifest_sha',
  '72000000-0000-4000-8000-000000000002', repeat('c', 64));
SELECT release.set_visual_policy_input_to_draft(
  '72000000-0000-4000-8000-000000000001', repeat('1', 64),
  repeat('2', 64), repeat('3', 64), repeat('4', 64), repeat('5', 64));
SELECT release.snapshot_legacy_visual_baseline_to_draft(
  '72000000-0000-4000-8000-000000000001', repeat('6', 64));
SELECT release.add_visual_asset_to_draft(
  '72000000-0000-4000-8000-000000000001', 'entries.json',
  'visual-registry-projection', 'application/json', 'identity',
  'schema-v49.0', 2, 1, repeat('7', 64), '001-entries', NULL, NULL);
SELECT release.copy_visual_entry_to_draft(
  '72000000-0000-4000-8000-000000000001',
  '72000000-0000-4000-8000-000000000003',
  '50000000-0000-4000-8000-000000000014',
  '50000000-0000-4000-8000-000000000010');
RESET SESSION AUTHORIZATION;

SELECT release.compute_visual_candidate_fingerprint(
  '72000000-0000-4000-8000-000000000001') AS positive_visual_fp_utc \gset
SET TIME ZONE 'Pacific/Honolulu';
SELECT release.compute_visual_candidate_fingerprint(
  '72000000-0000-4000-8000-000000000001') AS positive_visual_fp_non_utc \gset
SET TIME ZONE 'UTC';
SELECT pg_temp.assert_true(
  :'positive_visual_fp_utc' = :'positive_visual_fp_non_utc',
  'visual fingerprint is timezone invariant');

SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.close_visual_candidate(
  '72000000-0000-4000-8000-000000000001', :'positive_visual_fp_utc',
  '72000000-0000-4000-8000-000000000004', repeat('d', 64));
RESET SESSION AUTHORIZATION;
SET SESSION AUTHORIZATION gda_v49_phase2a_reviewer;
DO $record_positive_visual_receipts$
DECLARE k release.validation_receipt_kind; b bytea;
BEGIN
  FOREACH k IN ARRAY ARRAY[
    'visual_legacy_disposition',
    'visual_reference_bridge_provider_locator_identity',
    'visual_rights_policy_delivery_health_takedown',
    'visual_attribution_review_due',
    'visual_held_pixel_non_disclosure',
    'visual_research_compatibility',
    'visual_projection_fingerprint',
    'visual_deterministic_asset_inventory',
    'visual_role_grant_security'
  ]::release.validation_receipt_kind[]
  LOOP
    b := release.build_validation_receipt_bytes(
      'visual', '72000000-0000-4000-8000-000000000001', k,
      'phase2a-test-v1', repeat('e', 64));
    PERFORM release.record_visual_validation_receipt(
      gen_random_uuid(), '72000000-0000-4000-8000-000000000001', k,
      'phase2a-test-v1', repeat('e', 64), b, gen_random_uuid());
  END LOOP;
END
$record_positive_visual_receipts$;
RESET SESSION AUTHORIZATION;
SELECT visual_validation_receipt_id AS positive_visual_receipt_id,
  receipt_sha256 AS positive_visual_receipt_sha
FROM release.visual_validation_receipt
WHERE visual_registry_release_id = '72000000-0000-4000-8000-000000000001'
ORDER BY receipt_kind LIMIT 1 \gset
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.validate_visual_registry(
  '72000000-0000-4000-8000-000000000001',
  :'positive_visual_receipt_id', 'phase2a-test-v1',
  :'positive_visual_receipt_sha',
  '72000000-0000-4000-8000-000000000006', repeat('e', 64));
SELECT release.seal_visual_registry(
  '72000000-0000-4000-8000-000000000001',
  '72000000-0000-4000-8000-000000000007',
  '72000000-0000-4000-8000-000000000008', repeat('f', 64));
RESET SESSION AUTHORIZATION;

SELECT manifest_sha256 AS positive_visual_manifest_sha
FROM release.visual_registry_release
WHERE visual_registry_release_id = '72000000-0000-4000-8000-000000000001'
\gset
SELECT release.compute_visual_verification_sidecar_sha(
  '72000000-0000-4000-8000-000000000001',
  :'positive_visual_manifest_sha', 'phase2a-independent-v1')
  AS positive_visual_sidecar_sha \gset
SET SESSION AUTHORIZATION gda_v49_phase2a_reviewer;
SELECT release.record_visual_verification(
  '72000000-0000-4000-8000-000000000009',
  '72000000-0000-4000-8000-000000000001',
  :'positive_visual_manifest_sha', 'phase2a-independent-v1',
  :'positive_visual_sidecar_sha',
  '72000000-0000-4000-8000-000000000010', repeat('1', 64));
RESET SESSION AUTHORIZATION;

SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT * FROM release.promote_visual_current_cas(
  '72000000-0000-4000-8000-000000000011',
  'public', 1, '70000000-0000-4000-8000-000000000001',
  :'research_manifest_sha', 'public', 1,
  '71000000-0000-4000-8000-000000000001', :'visual_manifest_sha',
  '72000000-0000-4000-8000-000000000001');
RESET SESSION AUTHORIZATION;

SET SESSION AUTHORIZATION gda_v49_phase2a_api_reader;
SELECT pg_temp.assert_true(
  (SELECT count(*) FROM api_v1.current_object
    WHERE effective_delivery_mode = 'remote_image'
      AND remote_image_url IS NOT NULL) = 1,
  'positive control exposes reviewed remote image');
RESET SESSION AUTHORIZATION;

SET SESSION AUTHORIZATION gda_v49_phase2a_reviewer;
SELECT rights.record_takedown_event(
  '73000000-0000-4000-8000-000000000001', 'citation_only',
  clock_timestamp() + interval '1 day', NULL,
  'SCHEDULED_FIXTURE_TAKEDOWN',
  '30000000-0000-4000-8000-000000000003',
  ARRAY['73000000-0000-4000-8000-000000000002'::uuid],
  ARRAY['object_visual_reference'::rights.takedown_scope_kind],
  ARRAY['50000000-0000-4000-8000-000000000014'::uuid],
  ARRAY['73000000-0000-4000-8000-000000000003'::uuid],
  ARRAY['citation_only'::rights.delivery_mode], ARRAY[NULL::uuid]);
RESET SESSION AUTHORIZATION;
SET SESSION AUTHORIZATION gda_v49_phase2a_api_reader;
SELECT pg_temp.assert_true(
  (SELECT count(*) FROM api_v1.current_object
    WHERE effective_delivery_mode = 'remote_image'
      AND remote_image_url IS NOT NULL) = 1,
  'future takedown sidecar does not activate early');
RESET SESSION AUTHORIZATION;

SET SESSION AUTHORIZATION gda_v49_phase2a_reviewer;
SELECT rights.record_takedown_event(
  '73000000-0000-4000-8000-000000000020', 'citation_only',
  clock_timestamp() - interval '1 minute', NULL,
  'ACTIVE_CORRECTION_FIXTURE_TAKEDOWN',
  '30000000-0000-4000-8000-000000000003',
  ARRAY['73000000-0000-4000-8000-000000000021'::uuid],
  ARRAY['object_visual_reference'::rights.takedown_scope_kind],
  ARRAY['50000000-0000-4000-8000-000000000014'::uuid],
  ARRAY['73000000-0000-4000-8000-000000000022'::uuid],
  ARRAY['citation_only'::rights.delivery_mode], ARRAY[NULL::uuid]);
RESET SESSION AUTHORIZATION;
SET SESSION AUTHORIZATION gda_v49_phase2a_api_reader;
SELECT pg_temp.assert_true(
  (SELECT count(*) FROM api_v1.current_object
    WHERE effective_delivery_mode = 'citation_only'
      AND remote_image_url IS NULL
      AND canonical_record_url IS NULL
      AND source_viewer_url IS NULL) = 1,
  'active citation-only event immediately removes public locators');
RESET SESSION AUTHORIZATION;

SET SESSION AUTHORIZATION gda_v49_phase2a_reviewer;
SELECT rights.record_takedown_override_correction(
  '73000000-0000-4000-8000-000000000023',
  '73000000-0000-4000-8000-000000000021', 'blocked',
  '73000000-0000-4000-8000-000000000022');
RESET SESSION AUTHORIZATION;
SET SESSION AUTHORIZATION gda_v49_phase2a_api_reader;
SELECT pg_temp.assert_true(
  (SELECT count(*) FROM api_v1.current_object
    WHERE effective_delivery_mode = 'blocked'
      AND remote_image_url IS NULL
      AND canonical_record_url IS NULL
      AND source_viewer_url IS NULL) = 1,
  'stricter takedown correction atomically reaches public view');
RESET SESSION AUTHORIZATION;
SELECT pg_temp.assert_true(
  (SELECT count(*)
   FROM release.visual_takedown_sidecar_event t
   JOIN audit.sidecar_event a
     ON a.visual_takedown_sidecar_event_id =
       t.visual_takedown_sidecar_event_id
   WHERE t.takedown_override_id =
     '73000000-0000-4000-8000-000000000023') = 1,
  'takedown correction appends exact sealed-entry sidecar and audit event');
SET SESSION AUTHORIZATION gda_v49_phase2a_reviewer;
SELECT pg_temp.expect_error(
  $$SELECT rights.record_takedown_override_correction(
      '73000000-0000-4000-8000-000000000024',
      '73000000-0000-4000-8000-000000000021', 'citation_only',
      '73000000-0000-4000-8000-000000000023')$$,
  ARRAY['23514'], 'takedown correction cannot relax a blocked leaf');
RESET SESSION AUTHORIZATION;

SET SESSION AUTHORIZATION gda_v49_phase2a_reviewer;
SELECT rights.record_takedown_event(
  '73000000-0000-4000-8000-000000000004', 'blocked',
  clock_timestamp() - interval '2 minutes',
  clock_timestamp() - interval '1 minute',
  'EXPIRED_BUT_LATCHED_FIXTURE_TAKEDOWN',
  '30000000-0000-4000-8000-000000000003',
  ARRAY['73000000-0000-4000-8000-000000000005'::uuid],
  ARRAY['object_visual_reference'::rights.takedown_scope_kind],
  ARRAY['50000000-0000-4000-8000-000000000014'::uuid],
  ARRAY['73000000-0000-4000-8000-000000000006'::uuid],
  ARRAY['blocked'::rights.delivery_mode], ARRAY[NULL::uuid]);
RESET SESSION AUTHORIZATION;
SET SESSION AUTHORIZATION gda_v49_phase2a_api_reader;
SELECT pg_temp.assert_true(
  (SELECT count(*) FROM api_v1.current_object
    WHERE effective_delivery_mode = 'blocked'
      AND remote_image_url IS NULL
      AND canonical_record_url IS NULL
      AND source_viewer_url IS NULL) = 1,
  'expired takedown stays latched for sealed registry');
RESET SESSION AUTHORIZATION;

SELECT pg_temp.expect_error(
  $$INSERT INTO release.research_release_object (
      research_release_id, archive_object_id, object_urn,
      legacy_surface_id, title, publication_layer,
      acceptance_state, workflow_state
    ) SELECT
      '70000000-0000-4000-8000-000000000001', archive_object_id,
      object_urn, 'held-after-seal', preferred_label, 'excluded',
      'proposed', 'queued'
    FROM core.archive_object
    WHERE archive_object_id = '20000000-0000-4000-8000-000000000002'$$,
  ARRAY['55000'], 'post-seal child insert denied');
SELECT pg_temp.expect_error(
  $$UPDATE release.research_release_object SET title = 'mutated'
    WHERE research_release_id = '70000000-0000-4000-8000-000000000001'$$,
  ARRAY['55000'], 'post-seal child update denied');
SELECT pg_temp.expect_error(
  $$DELETE FROM release.research_release_object
    WHERE research_release_id = '70000000-0000-4000-8000-000000000001'$$,
  ARRAY['55000'], 'post-seal child delete denied');
SELECT pg_temp.expect_error(
  $$UPDATE release.research_release_manifest
      SET generated_at = clock_timestamp()
      WHERE research_release_id = '70000000-0000-4000-8000-000000000001'$$,
  ARRAY['55000'], 'post-seal manifest update denied');

SELECT pg_temp.assert_true(
  (SELECT count(*) FROM release.trace_projection_edge
    WHERE research_release_id = '70000000-0000-4000-8000-000000000001') = 0,
  'empty accepted TRACE state supported');
SELECT pg_temp.assert_true(
  (SELECT count(*) FROM release.research_release_relation
    WHERE research_release_id = '70000000-0000-4000-8000-000000000001'
      AND acceptance_basis = 'curator_decision'
      AND supporting_claim_revision_id IS NULL
      AND supporting_decision_id = '70000000-0000-4000-8000-000000000022'
      AND epistemic_code IS NULL) = 1,
  'decision-only accepted relation release path supported');
SELECT pg_temp.assert_true(
  (SELECT count(*) FROM release.visual_registry_entry
    WHERE visual_registry_release_id = '71000000-0000-4000-8000-000000000001') = 0,
  'zero positive-rights registry supported');
SELECT pg_temp.assert_true(
  (SELECT generation FROM release.research_current_pointer
    WHERE channel = 'public') = 1,
  'visual promotion did not mutate research current');
SELECT pg_temp.assert_true(
  (SELECT generation FROM release.visual_current_pointer
    WHERE channel = 'public') = 2,
  'visual current promoted independently');
SELECT pg_temp.assert_true(
  (SELECT count(*) FROM audit.research_cas_attempt
    WHERE reason_code = 'UNSEALED_RESEARCH_CURRENT_TARGET' AND NOT succeeded) = 1,
  'unsealed research current promotion denied');
SELECT pg_temp.assert_true(
  (SELECT count(*) FROM audit.research_cas_attempt
    WHERE reason_code = 'STALE_RESEARCH_CURRENT_CAS' AND NOT succeeded) = 2,
  'stale and NULL research CAS denied');
SELECT pg_temp.assert_true(
  (SELECT count(*) FROM audit.visual_cas_attempt
    WHERE reason_code = 'UNSEALED_VISUAL_CURRENT_TARGET' AND NOT succeeded) = 1,
  'unsealed visual current promotion denied');
SELECT pg_temp.assert_true(
  (SELECT count(*) FROM audit.visual_cas_attempt
    WHERE reason_code = 'STALE_VISUAL_CURRENT_CAS' AND NOT succeeded) = 1,
  'stale visual CAS denied');
SELECT pg_temp.assert_true(
  (SELECT count(*) FROM release.research_publication_history) = 1
  AND (SELECT count(*) FROM release.visual_publication_history) = 2,
  'public promotion history appended atomically');
SELECT pg_temp.assert_true(
  (SELECT count(*) FROM raw.legacy_surface_ledger
    WHERE import_disposition = 'held') = 1,
  'held migration row survives release build');

SET SESSION AUTHORIZATION gda_v49_phase2a_api_reader;
SELECT pg_temp.assert_true(
  (SELECT count(*) FROM api_v1.current_object) = 1,
  'public reader sees accepted active object');
SELECT pg_temp.assert_true(
  (SELECT count(*) FROM api_v1.current_object
    WHERE effective_delivery_mode = 'blocked'
      AND remote_image_url IS NULL
      AND canonical_record_url IS NULL
      AND source_viewer_url IS NULL) = 1,
  'takedown serializer omits every locator');
RESET SESSION AUTHORIZATION;

-- Detached verification rechecks only immutable copied rows and manifest
-- bytes; post-seal sidecars and later working-state changes cannot invalidate
-- an already sealed snapshot.
SELECT release.compute_visual_verification_sidecar_sha(
  '72000000-0000-4000-8000-000000000001',
  :'positive_visual_manifest_sha', 'phase2a-post-sidecar-v1')
  AS post_sidecar_visual_sha \gset
SELECT release.compute_research_verification_sidecar_sha(
  '70000000-0000-4000-8000-000000000001',
  :'research_manifest_sha', 'phase2a-post-seal-v1')
  AS post_seal_research_sha \gset
SET SESSION AUTHORIZATION gda_v49_phase2a_reviewer;
SELECT release.record_visual_verification(
  '73000000-0000-4000-8000-000000000010',
  '72000000-0000-4000-8000-000000000001',
  :'positive_visual_manifest_sha', 'phase2a-post-sidecar-v1',
  :'post_sidecar_visual_sha',
  '73000000-0000-4000-8000-000000000011', repeat('2', 64));
SELECT release.record_research_verification(
  '73000000-0000-4000-8000-000000000012',
  '70000000-0000-4000-8000-000000000001',
  :'research_manifest_sha', 'phase2a-post-seal-v1',
  :'post_seal_research_sha',
  '73000000-0000-4000-8000-000000000013', repeat('3', 64));
RESET SESSION AUTHORIZATION;
SELECT pg_temp.assert_true(
  (SELECT count(*) FROM release.visual_registry_verification
    WHERE visual_registry_release_id = '72000000-0000-4000-8000-000000000001') = 2
  AND (SELECT count(*) FROM release.research_release_verification
    WHERE research_release_id = '70000000-0000-4000-8000-000000000001') = 2,
  'post-seal detached verification ignores mutable working-state drift');

SET CONSTRAINTS ALL IMMEDIATE;
ROLLBACK;
