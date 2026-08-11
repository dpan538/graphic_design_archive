\set ON_ERROR_STOP on
BEGIN;
SET CONSTRAINTS ALL DEFERRED;

CREATE FUNCTION pg_temp.assert_true(p_condition boolean, p_label text)
RETURNS void LANGUAGE plpgsql AS $function$
BEGIN
  IF NOT COALESCE(p_condition, false) THEN
    RAISE EXCEPTION 'ASSERTION_FAILED: %', p_label;
  END IF;
END
$function$;

\ir ../fixtures/phase2a_base.sql

SELECT pg_temp.assert_true(
  NOT (SELECT rolcanlogin FROM pg_roles
       WHERE rolname = 'gda_v49_phase2a_schema_owner'),
  'schema owner is NOLOGIN');
SELECT pg_temp.assert_true(
  NOT EXISTS (
    SELECT 1 FROM pg_roles
    WHERE rolname = ANY (ARRAY[
      'gda_v49_phase2a_migrator','gda_v49_phase2a_ingest_writer',
      'gda_v49_phase2a_reviewer','gda_v49_phase2a_publisher',
      'gda_v49_phase2a_api_reader','gda_v49_phase2a_auditor'
    ]) AND (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)
  ), 'runtime roles have no cluster escalation attributes');
SELECT pg_temp.assert_true(
  pg_has_role('gda_v49_phase2a_migrator',
              'gda_v49_phase2a_schema_owner', 'MEMBER')
  AND NOT pg_has_role('gda_v49_phase2a_publisher',
                      'gda_v49_phase2a_schema_owner', 'MEMBER'),
  'only migrator is schema-owner member');
SELECT pg_temp.assert_true(
  NOT has_database_privilege('public', current_database(), 'CONNECT'),
  'PUBLIC database connect revoked');
SELECT pg_temp.assert_true(
  NOT has_schema_privilege('public', 'raw', 'USAGE')
  AND NOT has_schema_privilege('public', 'api_v1', 'USAGE'),
  'PUBLIC project schema access revoked');
SELECT pg_temp.assert_true(
  NOT has_type_privilege('public', 'rights.delivery_mode', 'USAGE'),
  'PUBLIC existing type usage revoked');
SELECT pg_temp.assert_true(
  has_table_privilege('gda_v49_phase2a_api_reader',
                      'api_v1.current_object', 'SELECT')
  AND NOT has_table_privilege('gda_v49_phase2a_api_reader',
                              'raw.source_asset', 'SELECT')
  AND NOT has_table_privilege('gda_v49_phase2a_api_reader',
                              'rights.visual_locator', 'SELECT')
  AND NOT has_table_privilege('gda_v49_phase2a_api_reader',
                              'api_v1.current_object', 'INSERT'),
  'api reader has positive allowlist only');
SELECT pg_temp.assert_true(
  has_table_privilege('gda_v49_phase2a_reviewer',
                      'workflow.reviewer_queue', 'SELECT')
  AND has_function_privilege('gda_v49_phase2a_reviewer',
    'provenance.record_assertion_review_decision(uuid,uuid,workflow.review_outcome,text,uuid,uuid[],provenance.evidence_role[])',
    'EXECUTE')
  AND has_function_privilege('gda_v49_phase2a_reviewer',
    'provenance.record_assignment_review_decision(uuid,uuid,workflow.review_outcome,text,uuid,uuid[],provenance.evidence_role[])',
    'EXECUTE')
  AND has_function_privilege('gda_v49_phase2a_reviewer',
    'research.record_relation_review_decision(uuid,uuid,workflow.review_outcome,text,uuid,uuid[],provenance.evidence_role[],uuid,core.sha256_hex)',
    'EXECUTE')
  AND has_function_privilege('gda_v49_phase2a_reviewer',
    'rights.record_object_visual_reference_review_decision(uuid,uuid,workflow.review_outcome,uuid,text,uuid,timestamptz)',
    'EXECUTE'),
  'reviewer can read queue and call every controlled review family');
SELECT pg_temp.assert_true(
  has_table_privilege('gda_v49_phase2a_ingest_writer',
                      'workflow.ingest_metadata_context', 'SELECT')
  AND NOT has_table_privilege('gda_v49_phase2a_ingest_writer',
                              'raw.source_asset', 'SELECT'),
  'ingestor reads governed metadata only through allowlisted view');
SELECT pg_temp.assert_true(
  has_table_privilege('gda_v49_phase2a_publisher',
                      'release.publisher_research_source', 'SELECT')
  AND has_function_privilege('gda_v49_phase2a_publisher',
    'release.add_research_object_to_draft(uuid,uuid,uuid)', 'EXECUTE')
  AND has_function_privilege('gda_v49_phase2a_publisher',
    'release.copy_legacy_identity_resolution_to_draft(uuid,uuid,uuid)',
    'EXECUTE')
  AND NOT has_table_privilege('gda_v49_phase2a_publisher',
                              'release.research_release_object', 'INSERT'),
  'publisher builds only through controlled projection functions');
SELECT pg_temp.assert_true(
  has_table_privilege('gda_v49_phase2a_auditor',
                      'audit.raw_hash_inventory', 'SELECT')
  AND NOT has_function_privilege('gda_v49_phase2a_auditor',
    'release.promote_research_current_cas(uuid,core.release_token,bigint,uuid,core.sha256_hex,uuid)',
    'EXECUTE'),
  'auditor is read-only and cannot promote');
SELECT pg_temp.assert_true(
  NOT EXISTS (
    SELECT 1
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = ANY (ARRAY[
      'raw','core','provenance','research','rights',
      'workflow','release','audit','api_v1'
    ])
      AND p.prosecdef
      AND NOT (p.proconfig @> ARRAY['search_path=pg_catalog'])
  ), 'all SECURITY DEFINER functions pin search_path');
SELECT pg_temp.assert_true(
  NOT EXISTS (
    SELECT 1
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = ANY (ARRAY[
      'raw','core','provenance','research','rights',
      'workflow','release','audit','api_v1'
    ]) AND p.prosecdef AND p.prosrc ~* '\mexecute\M'
  ), 'SECURITY DEFINER functions contain no dynamic SQL');

-- Prove the two provenance review families are not merely granted by name:
-- they must complete a claimed workflow case, change state, and append the
-- exact typed audit subtype in one transaction.
INSERT INTO provenance.assertion (
  assertion_id, assertion_predicate_id, subject_kind, value_kind,
  status, claimant_agent_id, source_wording, created_at
) VALUES (
  '80000000-0000-4000-8000-000000000010',
  '30000000-0000-4000-8000-000000000004', 'entity', 'literal',
  'proposed', '20000000-0000-4000-8000-000000000003',
  'Reviewer positive assertion fixture', clock_timestamp());
INSERT INTO provenance.assertion_subject_entity VALUES (
  '80000000-0000-4000-8000-000000000010',
  '20000000-0000-4000-8000-000000000002');
INSERT INTO provenance.assertion_value_literal VALUES (
  '80000000-0000-4000-8000-000000000010',
  '10000000-0000-4000-8000-000000000005',
  'Reviewer positive value', 'en', NULL);
INSERT INTO provenance.assertion_evidence VALUES (
  '80000000-0000-4000-8000-000000000010',
  '30000000-0000-4000-8000-000000000003', 'supports');
INSERT INTO workflow.review_case VALUES (
  '80000000-0000-4000-8000-000000000011', 'assertion',
  'queued', 0, 'ROLE_POSITIVE_ASSERTION', NULL, NULL,
  clock_timestamp(), NULL);
INSERT INTO workflow.review_case_assertion VALUES (
  '80000000-0000-4000-8000-000000000011',
  '80000000-0000-4000-8000-000000000010');

INSERT INTO provenance.canonical_assignment VALUES (
  '80000000-0000-4000-8000-000000000012',
  'entity_name', 'proposed', NULL, clock_timestamp());
INSERT INTO provenance.assignment_entity_name VALUES (
  '80000000-0000-4000-8000-000000000012',
  '20000000-0000-4000-8000-000000000002',
  '10000000-0000-4000-8000-000000000005');
INSERT INTO provenance.assignment_assertion VALUES (
  '80000000-0000-4000-8000-000000000012',
  '80000000-0000-4000-8000-000000000010', 'supports');
INSERT INTO workflow.review_case VALUES (
  '80000000-0000-4000-8000-000000000013', 'canonical_assignment',
  'queued', 0, 'ROLE_POSITIVE_ASSIGNMENT', NULL, NULL,
  clock_timestamp(), NULL);
INSERT INTO workflow.review_case_assignment VALUES (
  '80000000-0000-4000-8000-000000000013',
  '80000000-0000-4000-8000-000000000012');

SET SESSION AUTHORIZATION gda_v49_phase2a_reviewer;
SELECT workflow.claim_review_case(
  '80000000-0000-4000-8000-000000000011');
SELECT provenance.record_assertion_review_decision(
  '80000000-0000-4000-8000-000000000014',
  '80000000-0000-4000-8000-000000000010', 'accept',
  'Positive assertion role path', NULL,
  ARRAY['30000000-0000-4000-8000-000000000003'::uuid],
  ARRAY['supports'::provenance.evidence_role]);
SELECT workflow.claim_review_case(
  '80000000-0000-4000-8000-000000000013');
SELECT provenance.record_assignment_review_decision(
  '80000000-0000-4000-8000-000000000015',
  '80000000-0000-4000-8000-000000000012', 'accept',
  'Positive assignment role path', NULL,
  ARRAY['30000000-0000-4000-8000-000000000003'::uuid],
  ARRAY['supports'::provenance.evidence_role]);
RESET SESSION AUTHORIZATION;
SET CONSTRAINTS ALL IMMEDIATE;
SET CONSTRAINTS ALL DEFERRED;
SELECT pg_temp.assert_true(
  (SELECT status FROM provenance.assertion
    WHERE assertion_id = '80000000-0000-4000-8000-000000000010') = 'accepted'
  AND (SELECT status FROM provenance.canonical_assignment
    WHERE canonical_assignment_id = '80000000-0000-4000-8000-000000000012') = 'accepted'
  AND (SELECT count(*) FROM audit.decision_event_assertion_review
    WHERE assertion_review_decision_id = '80000000-0000-4000-8000-000000000014') = 1
  AND (SELECT count(*) FROM audit.decision_event_assignment_review
    WHERE assignment_review_decision_id = '80000000-0000-4000-8000-000000000015') = 1,
  'assertion and assignment reviewer paths append exact audit subtypes');

SET SESSION AUTHORIZATION gda_v49_phase2a_reviewer;
SELECT research.record_claim_review_decision(
  '80000000-0000-4000-8000-000000000016',
  '40000000-0000-4000-8000-000000000005', 'accept', false,
  'Positive claim supersession path',
  '40000000-0000-4000-8000-000000000011',
  ARRAY['30000000-0000-4000-8000-000000000003'::uuid],
  ARRAY['supports'::provenance.evidence_role]);
SELECT research.record_relation_review_decision(
  '80000000-0000-4000-8000-000000000017',
  '40000000-0000-4000-8000-000000000009', 'accept',
  'Positive relation supersession path',
  '40000000-0000-4000-8000-000000000010',
  ARRAY['30000000-0000-4000-8000-000000000003'::uuid],
  ARRAY['supports'::provenance.evidence_role],
  '80000000-0000-4000-8000-000000000018', repeat('8', 64));
SELECT rights.record_object_visual_reference_review_decision(
  '80000000-0000-4000-8000-000000000019',
  '50000000-0000-4000-8000-000000000014', 'accept',
  '30000000-0000-4000-8000-000000000003',
  'Positive bridge evidence-bound correction',
  '50000000-0000-4000-8000-000000000017', clock_timestamp());
RESET SESSION AUTHORIZATION;
SET CONSTRAINTS ALL IMMEDIATE;
SET CONSTRAINTS ALL DEFERRED;
SELECT pg_temp.assert_true(
  (SELECT status FROM research.claim_revision
    WHERE claim_revision_id = '40000000-0000-4000-8000-000000000005') = 'accepted'
  AND (SELECT status FROM research.semantic_relation
    WHERE semantic_relation_id = '40000000-0000-4000-8000-000000000009') = 'accepted'
  AND NOT EXISTS (
    SELECT 1 FROM research.claim_review_decision newer
    WHERE newer.supersedes_decision_id =
      '80000000-0000-4000-8000-000000000016')
  AND NOT EXISTS (
    SELECT 1 FROM research.relation_review_decision newer
    WHERE newer.supersedes_decision_id =
      '80000000-0000-4000-8000-000000000017')
  AND (SELECT acceptance_state FROM rights.object_visual_reference
    WHERE object_visual_reference_id =
      '50000000-0000-4000-8000-000000000014') = 'accepted'
  AND (SELECT count(*) FROM audit.decision_event_visual_bridge_review
    WHERE object_visual_reference_review_decision_id =
      '80000000-0000-4000-8000-000000000019') = 1,
  'claim, relation, and visual bridge review corrections remain controlled and audited');

SET SESSION AUTHORIZATION gda_v49_phase2a_ingest_writer;
SELECT raw.register_source_asset(
  '80000000-0000-4000-8000-000000000001', 'governed_source',
  'role-positive-governed-source',
  encode(sha256(convert_to('governed-role-fixture', 'UTF8')), 'hex'),
  convert_to('governed-role-fixture', 'UTF8'), 'application/octet-stream',
  clock_timestamp());
DO $block$
BEGIN
  BEGIN
    PERFORM raw.register_source_asset(
      '80000000-0000-4000-8000-000000000002',
      'canonical_migration_input', 'forbidden-authority',
      encode(sha256(convert_to('forbidden-authority', 'UTF8')), 'hex'),
      convert_to('forbidden-authority', 'UTF8'),
      'application/octet-stream', clock_timestamp());
    RAISE EXCEPTION 'EXPECTED_AUTHORITY_DENIAL_NOT_RAISED';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
  BEGIN
    PERFORM raw.register_source_record(
      '80000000-0000-4000-8000-000000000003',
      '10000000-0000-4000-8000-000000000001', 999,
      'forbidden-frozen-parent', convert_to('x', 'UTF8'),
      encode(sha256(convert_to('x', 'UTF8')), 'hex'), NULL, NULL);
    RAISE EXCEPTION 'EXPECTED_FROZEN_PARENT_DENIAL_NOT_RAISED';
  EXCEPTION WHEN insufficient_privilege OR object_not_in_prerequisite_state THEN NULL;
  END;
END
$block$;
RESET SESSION AUTHORIZATION;

SET SESSION AUTHORIZATION gda_v49_phase2a_api_reader;
DO $block$
BEGIN
  BEGIN
    PERFORM 1 FROM raw.source_asset;
    RAISE EXCEPTION 'EXPECTED_RAW_READ_DENIAL_NOT_RAISED';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
  BEGIN
    INSERT INTO api_v1.current_object (research_release_id)
      VALUES ('forbidden');
    RAISE EXCEPTION 'EXPECTED_PUBLIC_WRITE_DENIAL_NOT_RAISED';
  EXCEPTION WHEN insufficient_privilege OR object_not_in_prerequisite_state THEN NULL;
  END;
END
$block$;
RESET SESSION AUTHORIZATION;

SET SESSION AUTHORIZATION gda_v49_phase2a_ingest_writer;
DO $block$
BEGIN
  BEGIN
    PERFORM release.seal_research_release(
      'ffffffff-ffff-4fff-8fff-fffffffffff1',
      'ffffffff-ffff-4fff-8fff-fffffffffff2',
      'ffffffff-ffff-4fff-8fff-fffffffffff3', repeat('f', 64));
    RAISE EXCEPTION 'EXPECTED_CURATOR_SEAL_DENIAL_NOT_RAISED';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
END
$block$;
RESET SESSION AUTHORIZATION;

SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
DO $block$
BEGIN
  BEGIN
    INSERT INTO release.research_release (
      research_release_id, release_token, release_state,
      schema_version, model_version, created_at
    ) VALUES (
      '80000000-0000-4000-8000-000000000004', 'direct-bypass', 'draft',
      'schema-v49.0', 'model-v49.0', clock_timestamp());
    RAISE EXCEPTION 'EXPECTED_PUBLISHER_DML_DENIAL_NOT_RAISED';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
END
$block$;
RESET SESSION AUTHORIZATION;

SET SESSION AUTHORIZATION gda_v49_phase2a_auditor;
DO $block$
BEGIN
  BEGIN
    PERFORM release.initialize_research_current('forbidden-auditor');
    RAISE EXCEPTION 'EXPECTED_AUDITOR_PROMOTION_DENIAL_NOT_RAISED';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
END
$block$;
RESET SESSION AUTHORIZATION;

SET CONSTRAINTS ALL IMMEDIATE;
ROLLBACK;
