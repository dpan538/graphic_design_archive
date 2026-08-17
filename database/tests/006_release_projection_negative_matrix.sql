\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL SERIALIZABLE;
SET CONSTRAINTS ALL DEFERRED;

CREATE TABLE pg_temp.phase2s_negative_ledger (
  case_id text PRIMARY KEY,
  expected_sqlstate text NOT NULL,
  actual_sqlstate text,
  expected_message_or_constraint text NOT NULL,
  actual_message text,
  actual_constraint text,
  pre_state_digest text NOT NULL,
  post_state_digest text NOT NULL,
  residue_count bigint NOT NULL,
  pass boolean NOT NULL
);
GRANT SELECT, INSERT ON pg_temp.phase2s_negative_ledger TO PUBLIC;
CREATE FUNCTION pg_temp.assert_true(p_condition boolean,p_label text)
RETURNS void LANGUAGE plpgsql AS $function$
BEGIN
  IF NOT COALESCE(p_condition,false) THEN RAISE EXCEPTION 'ASSERTION_FAILED: %',p_label; END IF;
END
$function$;
CREATE FUNCTION pg_temp.snapshot_digest() RETURNS text LANGUAGE sql STABLE
SECURITY DEFINER SET search_path=pg_catalog AS $function$
  SELECT encode(sha256(convert_to(jsonb_build_object(
    'releases',(SELECT count(*) FROM release.research_release),
    'objects',(SELECT count(*) FROM release.research_release_object),
    'members',(SELECT count(*) FROM release.research_folder_membership_projection_v3),
    'receipts',(SELECT count(*) FROM release.research_launch_build_receipt_v3),
    'protocols',(SELECT count(*) FROM release.research_launch_protocol_v4)
  )::text,'UTF8')),'hex')
$function$;
CREATE FUNCTION pg_temp.record_expected_error(
  p_case_id text,p_expected_state text,p_expected_message text,p_sql text
) RETURNS void LANGUAGE plpgsql AS $function$
DECLARE v_state text; v_message text; v_constraint text; v_before text; v_after text;
BEGIN
  v_before:=pg_temp.snapshot_digest();
  BEGIN
    EXECUTE p_sql;
  EXCEPTION WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS v_state=RETURNED_SQLSTATE,
      v_message=MESSAGE_TEXT,v_constraint=CONSTRAINT_NAME;
  END;
  v_after:=pg_temp.snapshot_digest();
  INSERT INTO pg_temp.phase2s_negative_ledger
  VALUES(p_case_id,p_expected_state,v_state,p_expected_message,v_message,v_constraint,
    v_before,v_after,0,
    v_state=p_expected_state AND position(p_expected_message in coalesce(v_message,''))>0);
  PERFORM pg_temp.assert_true((SELECT pass FROM pg_temp.phase2s_negative_ledger WHERE case_id=p_case_id),p_case_id);
END
$function$;

\ir ../fixtures/phase2s_32_snapshot.sql

-- Published fixture: 32 eligible objects, four folders, a held accounted
-- object and a proposed held assignment.  All public rows must come from the
-- v4 common predicate.
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.create_research_release(
  '92000000-0000-4000-8000-000000000101','phase2s-v4-r1','schema-v49.0','model-v49.0',
  '92000000-0000-4000-8000-000000000102',repeat('1',64));
SELECT release.build_research_launch_snapshot_v4(
  '92000000-0000-4000-8000-000000000101',
  '10000000-0000-4000-8000-000000000003',
  '80000000-0000-4000-8000-000000000010',
  '92000000-0000-4000-8000-000000000103',repeat('2',64));
RESET SESSION AUTHORIZATION;

SELECT pg_temp.assert_true((SELECT count(*) FROM release.research_release_object
  WHERE research_release_id='92000000-0000-4000-8000-000000000101')=32,'v4 32 public objects');
SELECT pg_temp.assert_true((SELECT count(*) FROM release.research_folder_projection_v3
  WHERE research_release_id='92000000-0000-4000-8000-000000000101')=4,'v4 four folders');
SELECT pg_temp.assert_true((SELECT count(*) FROM release.research_folder_membership_projection_v3
  WHERE research_release_id='92000000-0000-4000-8000-000000000101')=32,'v4 32 published memberships');
SELECT pg_temp.assert_true(NOT EXISTS (SELECT 1 FROM release.research_release_object
  WHERE research_release_id='92000000-0000-4000-8000-000000000101'
    AND archive_object_id='20000000-0000-4000-8000-000000001033'),'held object is absent');
SELECT pg_temp.assert_true((SELECT trace_eligible_object_count=0 AND trace_relation_count=0
  AND availability_reason='NO_ACCEPTED_SEMANTIC_RELATIONS'
  FROM release.research_trace_availability_projection_v3
  WHERE research_release_id='92000000-0000-4000-8000-000000000101'), 'honest trace empty');
SELECT release.canonical_jsonb_sha256(jsonb_build_object(
  'format','gda-v49-research-validation-v4',
  'releaseId','92000000-0000-4000-8000-000000000101'::uuid,
  'candidateFingerprint',(SELECT candidate_fingerprint FROM release.research_release
    WHERE research_release_id='92000000-0000-4000-8000-000000000101'),
  'componentManifestSha256',release.research_launch_component_manifest_sha_v4(
    '92000000-0000-4000-8000-000000000101')))
  AS validation_sha \gset
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.validate_research_launch_snapshot_v4(
  '92000000-0000-4000-8000-000000000101',:'validation_sha',
  '92000000-0000-4000-8000-000000000105',repeat('3',64));
SELECT release.seal_research_launch_snapshot_v4(
  '92000000-0000-4000-8000-000000000101',
  '92000000-0000-4000-8000-000000000106',
  '92000000-0000-4000-8000-000000000107',repeat('4',64));
RESET SESSION AUTHORIZATION;
SELECT pg_temp.assert_true((SELECT release_state='sealed' FROM release.research_release
  WHERE research_release_id='92000000-0000-4000-8000-000000000101'), 'v4 fixture sealed through official lifecycle');

-- Fault hook is not publisher-callable; production wrapper has no fault arg.
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT pg_temp.record_expected_error('publisher_v3_fault_denied','42501',
  'permission denied',$$SELECT release.build_research_launch_snapshot_v3(
    '92000000-0000-4000-8000-000000000101','10000000-0000-4000-8000-000000000003',
    '80000000-0000-4000-8000-000000000010','92000000-0000-4000-8000-000000000104',repeat('f',64),'after_folders')$$);
RESET SESSION AUTHORIZATION;

-- Build receipt freezes the twelve guarded projection tables.  The function
-- records diagnostics rather than treating a broad exception as a pass.
SELECT pg_temp.record_expected_error('post_build_object_dml','55000',
  'PROJECTION_CLOSED',$$UPDATE release.research_release_object SET title='tamper'
    WHERE research_release_id='92000000-0000-4000-8000-000000000101'$$);
SELECT pg_temp.record_expected_error('post_build_member_dml','55000',
  'PROJECTION_CLOSED',$$DELETE FROM release.research_folder_membership_projection_v3
    WHERE research_release_id='92000000-0000-4000-8000-000000000101'$$);

-- Six independently created drafts exercise the owner-only fault hook.  Each
-- invocation is inside a savepoint so parent, projections, receipts and event
-- rows must all disappear.
DO $faults$
DECLARE f text; i integer:=0; v_release uuid; v_state text; v_message text;
BEGIN
  FOREACH f IN ARRAY ARRAY['after_release_objects','after_folders','after_memberships',
    'after_component_hashes','after_build_receipt','before_candidate_transition'] LOOP
    i:=i+1;
    v_release:=('92100000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
    BEGIN
      INSERT INTO release.research_release(
        research_release_id,release_token,release_state,schema_version,model_version,
        candidate_fingerprint,manifest_sha256,created_at,candidate_at,validated_at,sealed_at,
        validation_profile_id,validation_boundary
      ) VALUES (v_release,('phase2s-v4-fault-'||i)::core.release_token,'draft',
        'schema-v49.0','model-v49.0',NULL,NULL,'2026-08-16T00:00:00Z',NULL,NULL,NULL,
        '90000000-0000-4000-8000-000000000001','research');
      PERFORM release.build_research_launch_snapshot_v4_internal(v_release,
        '10000000-0000-4000-8000-000000000003','80000000-0000-4000-8000-000000000010',
        ('92100000-0000-4000-8000-'||lpad((200+i)::text,12,'0'))::uuid,repeat('6',64),f);
    EXCEPTION WHEN OTHERS THEN
      GET STACKED DIAGNOSTICS v_state=RETURNED_SQLSTATE,v_message=MESSAGE_TEXT;
      IF v_state <> 'P0001' THEN RAISE; END IF;
    END;
    IF NOT FOUND THEN NULL; END IF;
  END LOOP;
END
$faults$;
SELECT pg_temp.assert_true((SELECT count(*) FROM release.research_release
  WHERE release_token LIKE 'phase2s-v4-fault-%')=0,'fault parent zero residue');
SELECT pg_temp.assert_true((SELECT count(*) FROM release.research_launch_build_receipt_v3
  WHERE research_release_id::text LIKE '92100000-0000-4000-8000-%')=0,'fault receipt zero residue');
SELECT pg_temp.assert_true((SELECT count(*) FROM release.research_launch_protocol_v4
  WHERE research_release_id::text LIKE '92100000-0000-4000-8000-%')=0,'fault protocol zero residue');

-- A currently accepted semantic relation cannot be silently represented as
-- zero TRACE availability until a nonempty projection is implemented.
INSERT INTO research.relation_endpoint VALUES
  ('93000000-0000-4000-8000-000000000001','entity'),
  ('93000000-0000-4000-8000-000000000002','entity');
INSERT INTO research.relation_endpoint_entity VALUES
  ('93000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000001001'),
  ('93000000-0000-4000-8000-000000000002','20000000-0000-4000-8000-000000001002');
INSERT INTO research.relation_type VALUES
  ('93000000-0000-4000-8000-000000000003','fixture_relation',true,'archive_object','archive_object',true,
   'phase2s-profile',false,false,'fixture relation','phase2s-registry-v1');
INSERT INTO research.semantic_relation(
  semantic_relation_id,subject_endpoint_id,relation_type_id,object_endpoint_id,
  origin,status,temporal_qualifier_id,spatial_qualifier_id,
  supersedes_semantic_relation_id,created_at
) VALUES (
  '93000000-0000-4000-8000-000000000004','93000000-0000-4000-8000-000000000001',
  '93000000-0000-4000-8000-000000000003','93000000-0000-4000-8000-000000000002',
  'curator_created','accepted',NULL,NULL,NULL,'2026-08-16T00:00:00Z'
);
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.create_research_release('92000000-0000-4000-8000-000000000201','phase2s-v4-trace-stop',
  'schema-v49.0','model-v49.0','92000000-0000-4000-8000-000000000202',repeat('7',64));
SELECT pg_temp.record_expected_error('accepted_trace_fail_closed','23514',
  'TRACE_NONEMPTY_PROJECTION_NOT_IMPLEMENTED',$$SELECT release.build_research_launch_snapshot_v4(
  '92000000-0000-4000-8000-000000000201','10000000-0000-4000-8000-000000000003',
  '80000000-0000-4000-8000-000000000010','92000000-0000-4000-8000-000000000203',repeat('8',64))$$);
RESET SESSION AUTHORIZATION;

SELECT case_id,expected_sqlstate,actual_sqlstate,expected_message_or_constraint,
  actual_message,actual_constraint,pre_state_digest,post_state_digest,residue_count,pass
FROM pg_temp.phase2s_negative_ledger ORDER BY case_id;
ROLLBACK;
\echo PHASE2S_CLOSURE_NEGATIVE_MATRIX=PASS
