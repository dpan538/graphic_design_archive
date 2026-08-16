\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL SERIALIZABLE;
SET CONSTRAINTS ALL DEFERRED;

CREATE FUNCTION pg_temp.assert_true(p_condition boolean,p_label text)
RETURNS void LANGUAGE plpgsql AS $function$
BEGIN IF NOT COALESCE(p_condition,false) THEN RAISE EXCEPTION 'ASSERTION_FAILED: %',p_label; END IF; END $function$;
CREATE FUNCTION pg_temp.expect_error(p_sql text,p_states text[],p_label text)
RETURNS void LANGUAGE plpgsql AS $function$
DECLARE v_failed boolean:=false;v_state text;
BEGIN
  BEGIN EXECUTE p_sql; EXCEPTION WHEN OTHERS THEN v_failed:=true;v_state:=SQLSTATE; END;
  IF NOT v_failed OR NOT (v_state=ANY(p_states)) THEN RAISE EXCEPTION 'EXPECTED_ERROR: % got %',p_label,v_state; END IF;
END $function$;

\ir ../fixtures/phase2s_32_snapshot.sql

SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.create_research_release(
  '90000000-0000-4000-8000-000000000101','phase2s-r1','schema-v49.0','model-v49.0',
  '90000000-0000-4000-8000-000000000102',repeat('1',64));
SELECT release.build_research_launch_snapshot_v3(
  '90000000-0000-4000-8000-000000000101',
  '10000000-0000-4000-8000-000000000003',
  '80000000-0000-4000-8000-000000000010',
  '90000000-0000-4000-8000-000000000103',repeat('2',64));
RESET SESSION AUTHORIZATION;

SELECT pg_temp.assert_true((SELECT count(*) FROM release.research_release_object WHERE research_release_id='90000000-0000-4000-8000-000000000101')=32,'32 public release objects');
SELECT pg_temp.assert_true(NOT EXISTS (SELECT 1 FROM release.research_release_object WHERE research_release_id='90000000-0000-4000-8000-000000000101' AND archive_object_id='20000000-0000-4000-8000-000000001033'),'accounted but held corpus sentinel excluded from public release');
SELECT pg_temp.assert_true((SELECT count(*) FROM release.research_folder_projection_v3 WHERE research_release_id='90000000-0000-4000-8000-000000000101')=4,'four release folders');
SELECT pg_temp.assert_true((SELECT count(*) FROM release.research_folder_membership_projection_v3 WHERE research_release_id='90000000-0000-4000-8000-000000000101')=32,'32 accepted memberships');
SELECT pg_temp.assert_true((SELECT count(*) FROM release.research_folder_membership_projection_v3 WHERE research_release_id='90000000-0000-4000-8000-000000000101' AND membership_role='held_sentinel')=0,'proposed held sentinel excluded');
SELECT pg_temp.assert_true((SELECT trace_eligible_object_count FROM release.research_trace_availability_projection_v3 WHERE research_release_id='90000000-0000-4000-8000-000000000101')=0,'TRACE zero computed from source');
SELECT pg_temp.assert_true((SELECT count(*) FROM release.research_launch_component_manifest_v3 WHERE research_release_id='90000000-0000-4000-8000-000000000101')=10,'all v3 components registered');
SELECT pg_temp.assert_true((SELECT row_count FROM release.research_launch_source_disposition_count_v3 WHERE research_release_id='90000000-0000-4000-8000-000000000101' AND source_component='corpusMemberships' AND source_disposition='held')=1,'held corpus disposition is named but not promoted');

-- A component hash, receipt, role, ordinal, or object mutation changes the
-- candidate fingerprint; validation is release-only and catches it.
SELECT pg_temp.expect_error($$UPDATE release.research_folder_membership_projection_v3 SET member_ordinal=7 WHERE research_release_id='90000000-0000-4000-8000-000000000101' AND member_ordinal=0$$,ARRAY['55000'],'post-build membership mutation denied');

SELECT release.canonical_jsonb_sha256(jsonb_build_object(
  'format','gda-v49-research-validation-v3','releaseId','90000000-0000-4000-8000-000000000101'::uuid,
  'candidateFingerprint',(SELECT candidate_fingerprint FROM release.research_release WHERE research_release_id='90000000-0000-4000-8000-000000000101'),
  'componentManifestSha256',release.research_launch_component_manifest_sha_v3('90000000-0000-4000-8000-000000000101')))
  AS validation_sha \gset
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.validate_research_launch_snapshot_v3('90000000-0000-4000-8000-000000000101',:'validation_sha','90000000-0000-4000-8000-000000000104',repeat('3',64));
SELECT release.seal_research_launch_snapshot_v3('90000000-0000-4000-8000-000000000101','90000000-0000-4000-8000-000000000105','90000000-0000-4000-8000-000000000106',repeat('4',64)) AS sealed_manifest \gset
RESET SESSION AUTHORIZATION;
SELECT pg_temp.assert_true((SELECT release_state='sealed' FROM release.research_release WHERE research_release_id='90000000-0000-4000-8000-000000000101'),'v3 release sealed');
SELECT pg_temp.assert_true((SELECT manifest_sha256 FROM release.research_launch_manifest_v3 WHERE research_release_id='90000000-0000-4000-8000-000000000101')=:'sealed_manifest','v3 manifest recorded');
SELECT pg_temp.expect_error($$DELETE FROM release.research_surface_presentation_projection_v3 WHERE research_release_id='90000000-0000-4000-8000-000000000101'$$,ARRAY['55000'],'post-seal mutation denied');

-- Canonical drift changes the next release only.  This validation/query uses
-- release-owned tables exclusively after build.
UPDATE research.folder SET label='Drift after build' WHERE folder_id='80000000-0000-4000-8000-000000000001';
SELECT release.validate_research_launch_snapshot_v3_integrity('90000000-0000-4000-8000-000000000101');
SELECT pg_temp.assert_true((SELECT label FROM release.research_folder_projection_v3 WHERE research_release_id='90000000-0000-4000-8000-000000000101' AND folder_id='80000000-0000-4000-8000-000000000001')='Region Alpha','post-build canonical drift does not alter release');

-- Failure injection is atomic when a draft and build are in the same caller
-- transaction.  Parent, children, receipt and events are all rolled back.
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
DO $failure_injection$
DECLARE f text; i integer:=0; v_release uuid; v_failed boolean;
BEGIN
  FOREACH f IN ARRAY ARRAY['after_release_objects','after_folders','after_memberships','after_component_hashes','after_build_receipt'] LOOP
    i:=i+1; v_release:=('91000000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid; v_failed:=false;
    BEGIN
      PERFORM release.create_research_release(v_release,('phase2s-fault-'||i)::core.release_token,'schema-v49.0','model-v49.0',('91000000-0000-4000-8000-'||lpad((100+i)::text,12,'0'))::uuid,repeat('5',64));
      PERFORM release.build_research_launch_snapshot_v3(v_release,'10000000-0000-4000-8000-000000000003','80000000-0000-4000-8000-000000000010',('91000000-0000-4000-8000-'||lpad((200+i)::text,12,'0'))::uuid,repeat('6',64),f);
    EXCEPTION WHEN SQLSTATE 'P0001' THEN v_failed:=true;
    END;
    IF NOT v_failed THEN RAISE EXCEPTION 'FAILURE_INJECTION_NOT_RAISED %',f; END IF;
  END LOOP;
END $failure_injection$;
RESET SESSION AUTHORIZATION;
-- Event rows have a mandatory parent FK, so absent parents also prove no
-- task-owned candidate events survived the five failed savepoints.
SELECT pg_temp.assert_true((SELECT count(*) FROM release.research_release WHERE release_token LIKE 'phase2s-fault-%')=0,'five failure injection parents rolled back');
SELECT pg_temp.assert_true((SELECT count(*) FROM release.research_launch_build_receipt_v3 WHERE research_release_id::text LIKE '91000000-0000-4000-8000-%')=0,'five failure injection receipts rolled back');

SET SESSION AUTHORIZATION gda_v49_phase2a_api_reader;
SELECT pg_temp.expect_error($$SELECT * FROM release.research_folder_membership_projection_v3$$,ARRAY['42501'],'api_reader base table select denied');
SELECT pg_temp.expect_error($$INSERT INTO release.research_folder_type_projection_v3 VALUES ('90000000-0000-4000-8000-000000000101','x','x',9)$$,ARRAY['42501'],'api_reader write denied');
RESET SESSION AUTHORIZATION;
SELECT pg_temp.assert_true(NOT EXISTS (
  SELECT 1 FROM pg_class c CROSS JOIN LATERAL aclexplode(c.relacl) a
  WHERE c.oid='release.research_folder_membership_projection_v3'::regclass
    AND a.grantee=0 AND a.privilege_type='SELECT'
),'PUBLIC has no v3 projection access');

ROLLBACK;
\echo PHASE2S_SNAPSHOT_TESTS=PASS
