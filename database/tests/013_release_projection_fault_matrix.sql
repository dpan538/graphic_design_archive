\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL SERIALIZABLE;
SET CONSTRAINTS ALL DEFERRED;
\ir ../fixtures/phase2s_32_snapshot.sql

CREATE TABLE pg_temp.v49_fault_ledger (
  fault_point text PRIMARY KEY,
  expected_sqlstate text NOT NULL,
  actual_sqlstate text NOT NULL,
  actual_message text,
  release_residue bigint NOT NULL,
  projection_residue bigint NOT NULL,
  receipt_residue bigint NOT NULL,
  event_residue bigint NOT NULL,
  pass boolean NOT NULL
);

DO $faults$
DECLARE
  f text;
  i integer := 0;
  v_release uuid;
  v_state text;
  v_message text;
  v_release_residue bigint;
  v_projection_residue bigint;
  v_receipt_residue bigint;
  v_event_residue bigint;
BEGIN
  FOREACH f IN ARRAY ARRAY[
    'after_release_objects','after_folders','after_memberships',
    'after_component_hashes','after_build_receipt','before_candidate_transition'
  ] LOOP
    i := i+1;
    v_release := ('96000000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
    v_state := '00000'; v_message := NULL;
    BEGIN
      INSERT INTO release.research_release(
        research_release_id,release_token,release_state,schema_version,model_version,
        candidate_fingerprint,manifest_sha256,created_at,candidate_at,validated_at,sealed_at,
        validation_profile_id,validation_boundary)
      VALUES(v_release,('v49-fault-'||i)::core.release_token,'draft',
        'schema-v49.0','model-v49.0',NULL,NULL,'2026-08-20T00:00:00Z',
        NULL,NULL,NULL,'90000000-0000-4000-8000-000000000001','research');
      PERFORM release.build_research_launch_snapshot_v5_internal(
        v_release,'10000000-0000-4000-8000-000000000003',
        '80000000-0000-4000-8000-000000000010',
        ('96000000-0000-4000-8000-'||lpad((100+i)::text,12,'0'))::uuid,
        repeat('6',64),f);
    EXCEPTION WHEN OTHERS THEN
      GET STACKED DIAGNOSTICS v_state=RETURNED_SQLSTATE,v_message=MESSAGE_TEXT;
    END;
    SELECT count(*) INTO v_release_residue FROM release.research_release
      WHERE research_release_id=v_release;
    SELECT
      (SELECT count(*) FROM release.research_release_object WHERE research_release_id=v_release)+
      (SELECT count(*) FROM release.research_folder_type_projection_v3 WHERE research_release_id=v_release)+
      (SELECT count(*) FROM release.research_folder_projection_v3 WHERE research_release_id=v_release)+
      (SELECT count(*) FROM release.research_folder_membership_projection_v3 WHERE research_release_id=v_release)+
      (SELECT count(*) FROM release.research_surface_presentation_projection_v3 WHERE research_release_id=v_release)+
      (SELECT count(*) FROM release.research_surface_credit_projection_v3 WHERE research_release_id=v_release)+
      (SELECT count(*) FROM release.research_surface_citation_projection_v3 WHERE research_release_id=v_release)+
      (SELECT count(*) FROM release.research_search_document_projection_v3 WHERE research_release_id=v_release)+
      (SELECT count(*) FROM release.research_corpus_summary_projection_v3 WHERE research_release_id=v_release)+
      (SELECT count(*) FROM release.research_trace_availability_projection_v3 WHERE research_release_id=v_release)+
      (SELECT count(*) FROM release.research_launch_component_manifest_v3 WHERE research_release_id=v_release)+
      (SELECT count(*) FROM release.research_launch_source_disposition_count_v3 WHERE research_release_id=v_release)
      INTO v_projection_residue;
    SELECT count(*) INTO v_receipt_residue FROM release.research_launch_build_receipt_v3
      WHERE research_release_id=v_release;
    SELECT count(*) INTO v_event_residue FROM audit.research_release_event
      WHERE research_release_id=v_release;
    INSERT INTO pg_temp.v49_fault_ledger VALUES(
      f,'P0001',v_state,v_message,v_release_residue,v_projection_residue,
      v_receipt_residue,v_event_residue,
      v_state='P0001' AND v_message='RESEARCH_LAUNCH_V5_FAULT_'||upper(f)
        AND v_release_residue=0 AND v_projection_residue=0
        AND v_receipt_residue=0 AND v_event_residue=0);
  END LOOP;
END
$faults$;

SELECT * FROM pg_temp.v49_fault_ledger ORDER BY fault_point;
DO $assert_faults$
BEGIN
  IF (SELECT count(*) FROM pg_temp.v49_fault_ledger) <> 6
    OR (SELECT count(*) FROM pg_temp.v49_fault_ledger WHERE pass) <> 6 THEN
    RAISE EXCEPTION 'V49_FAULT_MATRIX_NOT_6_OF_6';
  END IF;
END
$assert_faults$;

-- A wrong digest may not move a candidate to validated/sealed or publish it.
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.create_research_release(
  '96000000-0000-4000-8000-000000000100','v49-digest-fault',
  'schema-v49.0','model-v49.0',
  '96000000-0000-4000-8000-000000000101',repeat('7',64));
SELECT release.build_research_launch_snapshot_v5(
  '96000000-0000-4000-8000-000000000100',
  '10000000-0000-4000-8000-000000000003',
  '80000000-0000-4000-8000-000000000010',
  '96000000-0000-4000-8000-000000000102',repeat('8',64));
DO $digest_failure$
DECLARE v_state text; v_message text;
BEGIN
  BEGIN
    PERFORM release.validate_research_launch_snapshot_v5(
      '96000000-0000-4000-8000-000000000100',repeat('0',64),
      '96000000-0000-4000-8000-000000000103',repeat('9',64));
  EXCEPTION WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS v_state=RETURNED_SQLSTATE,v_message=MESSAGE_TEXT;
  END;
  IF v_state <> '23514' OR v_message <> 'RESEARCH_LAUNCH_V5_VALIDATION_RECEIPT_MISMATCH' THEN
    RAISE EXCEPTION 'DIGEST_FAILURE_NOT_FAIL_CLOSED: %, %',v_state,v_message;
  END IF;
END
$digest_failure$;
RESET SESSION AUTHORIZATION;

DO $digest_residue$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM release.research_release
      WHERE research_release_id='96000000-0000-4000-8000-000000000100'
        AND release_state='candidate' AND validated_at IS NULL
        AND sealed_at IS NULL AND manifest_sha256 IS NULL)
    OR EXISTS (SELECT 1 FROM release.research_current_pointer
      WHERE research_release_id='96000000-0000-4000-8000-000000000100') THEN
    RAISE EXCEPTION 'DIGEST_FAILURE_PUBLISHED_OR_ADVANCED_STATE';
  END IF;
END
$digest_residue$;

-- The production publisher cannot call the internal fault surface.
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
DO $permission_failure$
DECLARE v_state text;
BEGIN
  BEGIN
    PERFORM release.build_research_launch_snapshot_v5_internal(
      '96000000-0000-4000-8000-000000000100',
      '10000000-0000-4000-8000-000000000003',
      '80000000-0000-4000-8000-000000000010',
      '96000000-0000-4000-8000-000000000104',repeat('a',64),
      'after_release_objects');
  EXCEPTION WHEN OTHERS THEN GET STACKED DIAGNOSTICS v_state=RETURNED_SQLSTATE;
  END;
  IF v_state <> '42501' THEN RAISE EXCEPTION 'INTERNAL_FAULT_PERMISSION_NOT_DENIED: %',v_state; END IF;
END
$permission_failure$;
RESET SESSION AUTHORIZATION;

ROLLBACK;
\echo V49_FAULT_MATRIX=PASS CASES=6/6 DIGEST_FAILURE=PASS PERMISSION_FAILURE=PASS
