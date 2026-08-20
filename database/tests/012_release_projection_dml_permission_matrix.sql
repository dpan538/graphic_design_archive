\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL SERIALIZABLE;
SET CONSTRAINTS ALL DEFERRED;
\ir ../fixtures/phase2s_32_snapshot.sql

CREATE TABLE pg_temp.v49_dml_ledger (
  case_id text PRIMARY KEY,
  object_name text NOT NULL,
  operation text NOT NULL,
  expected_sqlstate text NOT NULL,
  actual_sqlstate text NOT NULL,
  actual_message text,
  pass boolean NOT NULL
);
GRANT SELECT,INSERT ON pg_temp.v49_dml_ledger TO PUBLIC;

CREATE FUNCTION pg_temp.expect_closed(
  p_case_id text,p_object text,p_operation text,p_sql text
) RETURNS void LANGUAGE plpgsql AS $function$
DECLARE v_state text := '00000'; v_message text;
BEGIN
  BEGIN
    EXECUTE p_sql;
  EXCEPTION WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS v_state=RETURNED_SQLSTATE,v_message=MESSAGE_TEXT;
  END;
  INSERT INTO pg_temp.v49_dml_ledger
  VALUES(p_case_id,p_object,p_operation,'55000',v_state,v_message,
    v_state='55000' AND position('RESEARCH_LAUNCH_V3_PROJECTION_CLOSED' in coalesce(v_message,''))>0);
  IF NOT (SELECT pass FROM pg_temp.v49_dml_ledger WHERE case_id=p_case_id) THEN
    RAISE EXCEPTION 'DML_CASE_FAILED: %, state %, message %',p_case_id,v_state,v_message;
  END IF;
END
$function$;

SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.create_research_release(
  '95000000-0000-4000-8000-000000000001','v49-dml-matrix',
  'schema-v49.0','model-v49.0',
  '95000000-0000-4000-8000-000000000002',repeat('1',64));
SELECT release.build_research_launch_snapshot_v5(
  '95000000-0000-4000-8000-000000000001',
  '10000000-0000-4000-8000-000000000003',
  '80000000-0000-4000-8000-000000000010',
  '95000000-0000-4000-8000-000000000003',repeat('2',64));
RESET SESSION AUTHORIZATION;

-- v5 deliberately emits zero surface-credit rows for this fixture.  Build a
-- second receipt-closed projection containing one valid credit so UPDATE and
-- DELETE are real row operations rather than vacuous zero-row statements.
INSERT INTO release.research_release(
  research_release_id,release_token,release_state,schema_version,model_version,
  candidate_fingerprint,manifest_sha256,created_at,candidate_at,validated_at,sealed_at,
  validation_profile_id,validation_boundary)
SELECT '95000000-0000-4000-8000-000000000010','v49-dml-credit-aux',
  'draft',schema_version,model_version,NULL,NULL,created_at,
  NULL,NULL,NULL,validation_profile_id,validation_boundary
FROM release.research_release
WHERE research_release_id='95000000-0000-4000-8000-000000000001';
INSERT INTO release.research_release_object
SELECT '95000000-0000-4000-8000-000000000010',archive_object_id,object_urn,
  legacy_surface_id,title,publication_layer,acceptance_state,workflow_state
FROM release.research_release_object
WHERE research_release_id='95000000-0000-4000-8000-000000000001'
ORDER BY archive_object_id LIMIT 1;
INSERT INTO release.research_surface_presentation_projection_v3
SELECT '95000000-0000-4000-8000-000000000010',archive_object_id,public_surface_id,
  title,title_missingness,display_date,display_date_missingness,normalized_year,
  normalized_year_missingness,place_label,place_missingness,medium_label,
  medium_missingness,type_label,type_missingness,source_label,description,
  description_missingness,public_citation_label,public_source_route,publication_layer
FROM release.research_surface_presentation_projection_v3
WHERE research_release_id='95000000-0000-4000-8000-000000000001'
ORDER BY archive_object_id LIMIT 1;
INSERT INTO release.research_surface_credit_projection_v3
SELECT '95000000-0000-4000-8000-000000000010',archive_object_id,0,
  'Closed credit fixture','creator'
FROM release.research_release_object
WHERE research_release_id='95000000-0000-4000-8000-000000000010';
INSERT INTO release.research_launch_build_receipt_v3
SELECT '95000000-0000-4000-8000-000000000010',builder_version,
  migration_batch_id,public_corpus_version_id,candidate_asset_id,
  candidate_asset_sha256,mapping_specification_sha256,
  projection_query_pack_sha256,selection_policy_sha256,
  registry_corpus_policy_sha256,source_snapshot_sha256,
  projection_component_manifest_sha256,projection_content_sha256,
  build_receipt_sha256,candidate_fingerprint,built_at
FROM release.research_launch_build_receipt_v3
WHERE research_release_id='95000000-0000-4000-8000-000000000001';
UPDATE release.research_release
SET release_state='candidate',candidate_fingerprint=(
  SELECT candidate_fingerprint FROM release.research_release
  WHERE research_release_id='95000000-0000-4000-8000-000000000001'),
  candidate_at=clock_timestamp()
WHERE research_release_id='95000000-0000-4000-8000-000000000010';

DO $matrix$
DECLARE
  t text;
  table_name text;
  base text;
  target_release uuid;
BEGIN
  FOREACH table_name IN ARRAY ARRAY[
    'research_folder_type_projection_v3',
    'research_folder_projection_v3',
    'research_folder_membership_projection_v3',
    'research_surface_presentation_projection_v3',
    'research_surface_credit_projection_v3',
    'research_surface_citation_projection_v3',
    'research_search_document_projection_v3',
    'research_corpus_summary_projection_v3',
    'research_trace_availability_projection_v3',
    'research_launch_component_manifest_v3',
    'research_launch_source_disposition_count_v3',
    'research_release_object'
  ] LOOP
    target_release := CASE WHEN table_name='research_surface_credit_projection_v3'
      THEN '95000000-0000-4000-8000-000000000010'::uuid
      ELSE '95000000-0000-4000-8000-000000000001'::uuid END;
    base := pg_catalog.format(
      ' WHERE research_release_id=%L::uuid',
      target_release);
    PERFORM pg_temp.expect_closed(table_name||'_update',
      'release.'||table_name,'UPDATE',pg_catalog.format(
        'UPDATE release.%I SET research_release_id=research_release_id%s',table_name,base));
    PERFORM pg_temp.expect_closed(table_name||'_delete',
      'release.'||table_name,'DELETE',pg_catalog.format(
        'DELETE FROM release.%I%s',table_name,base));
    IF table_name='research_surface_credit_projection_v3' THEN
      t := $sql$INSERT INTO release.research_surface_credit_projection_v3
        VALUES('95000000-0000-4000-8000-000000000010',
        '20000000-0000-4000-8000-000000001001',0,'tamper','creator')$sql$;
    ELSE
      t := pg_catalog.format(
        'INSERT INTO release.%I SELECT * FROM release.%I%s LIMIT 1',
        table_name,table_name,base);
    END IF;
    PERFORM pg_temp.expect_closed(table_name||'_insert',
      'release.'||table_name,'INSERT',t);
  END LOOP;
END
$matrix$;

-- Role and object boundary assertions accompany the 36 guarded-table cases;
-- they are deliberately not inflated into the 36/36 operation count.
DO $role_matrix$
DECLARE v_owner name;
BEGIN
  SELECT pg_get_userbyid(c.relowner) INTO v_owner
  FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname='release' AND c.relname='research_launch_protocol_v5';
  IF v_owner <> 'gda_v49_phase2a_schema_owner' THEN
    RAISE EXCEPTION 'MIGRATION_OWNER_DRIFT: %',v_owner;
  END IF;
  IF NOT has_schema_privilege('gda_v49_phase2a_api_reader','api_v1','USAGE')
    OR NOT has_table_privilege('gda_v49_phase2a_api_reader','api_v1.sealed_surface','SELECT')
    OR NOT has_table_privilege('gda_v49_phase2a_api_reader','api_v1.sealed_research_release_descriptor','SELECT') THEN
    RAISE EXCEPTION 'API_VIEW_READ_GRANT_MISSING';
  END IF;
  IF has_table_privilege('gda_v49_phase2a_api_reader','core.archive_object','SELECT,INSERT,UPDATE,DELETE')
    OR has_table_privilege('gda_v49_phase2a_api_reader','research.corpus_membership','SELECT,INSERT,UPDATE,DELETE')
    OR has_table_privilege('gda_v49_phase2a_api_reader','release.research_release_object','SELECT,INSERT,UPDATE,DELETE') THEN
    RAISE EXCEPTION 'API_DIRECT_TABLE_PRIVILEGE_LEAK';
  END IF;
  IF has_table_privilege('gda_v49_phase2a_publisher','core.archive_object','INSERT,UPDATE,DELETE')
    OR has_table_privilege('gda_v49_phase2a_publisher','research.corpus_membership','INSERT,UPDATE,DELETE') THEN
    RAISE EXCEPTION 'PUBLISHER_CANONICAL_WRITE_PRIVILEGE_LEAK';
  END IF;
  IF has_function_privilege('gda_v49_phase2a_publisher',
      'release.build_research_launch_snapshot_v5_internal(uuid,uuid,uuid,uuid,core.sha256_hex,text)','EXECUTE')
    OR NOT has_function_privilege('gda_v49_phase2a_publisher',
      'release.build_research_launch_snapshot_v5(uuid,uuid,uuid,uuid,core.sha256_hex)','EXECUTE') THEN
    RAISE EXCEPTION 'V5_FUNCTION_GRANT_DRIFT';
  END IF;
  IF NOT has_function_privilege('gda_v49_phase2a_reviewer',
      'release.record_research_launch_verification_v5(uuid,uuid,core.sha256_hex,core.release_token,core.sha256_hex,uuid,core.sha256_hex)','EXECUTE')
    OR has_function_privilege('gda_v49_phase2a_publisher',
      'release.record_research_launch_verification_v5(uuid,uuid,core.sha256_hex,core.release_token,core.sha256_hex,uuid,core.sha256_hex)','EXECUTE')
    OR has_function_privilege('gda_v49_phase2a_api_reader',
      'release.record_research_launch_verification_v5(uuid,uuid,core.sha256_hex,core.release_token,core.sha256_hex,uuid,core.sha256_hex)','EXECUTE') THEN
    RAISE EXCEPTION 'V5_VERIFICATION_FUNCTION_GRANT_DRIFT';
  END IF;
  IF EXISTS (
    SELECT 1 FROM information_schema.role_table_grants
    WHERE grantee='PUBLIC' AND privilege_type IN ('INSERT','UPDATE','DELETE','TRUNCATE')
      AND table_schema IN ('raw','core','provenance','research','rights','workflow','release','api_v1')
  ) THEN
    RAISE EXCEPTION 'PUBLIC_DML_GRANT_LEAK';
  END IF;
  IF to_regclass('provenance.canonical_assignment_publishable_v5_idx') IS NOT NULL
    OR to_regclass('provenance.canonical_assignment_current_leaf_v5_idx') IS NULL
    OR to_regclass('provenance.assignment_review_decision_current_leaf_v5_idx') IS NULL THEN
    RAISE EXCEPTION 'V49_INDEX_CLEANUP_OR_KEEP_SET_DRIFT';
  END IF;
END
$role_matrix$;

SET SESSION AUTHORIZATION gda_v49_phase2a_api_reader;
SELECT count(*) FROM api_v1.sealed_research_release_descriptor;
RESET SESSION AUTHORIZATION;

SELECT * FROM pg_temp.v49_dml_ledger ORDER BY object_name,operation;
DO $assert_count$
BEGIN
  IF (SELECT count(*) FROM pg_temp.v49_dml_ledger) <> 36
    OR (SELECT count(*) FROM pg_temp.v49_dml_ledger WHERE pass) <> 36 THEN
    RAISE EXCEPTION 'V49_DML_PERMISSION_MATRIX_NOT_36_OF_36';
  END IF;
END
$assert_count$;
ROLLBACK;
\echo V49_DML_PERMISSION_MATRIX=PASS CASES=36/36 ROLE_BOUNDARY=PASS
