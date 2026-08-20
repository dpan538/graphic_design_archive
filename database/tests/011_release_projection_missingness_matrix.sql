\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL SERIALIZABLE;
SET CONSTRAINTS ALL DEFERRED;
\ir ../fixtures/phase2s_32_snapshot.sql

CREATE TABLE pg_temp.v49_missingness_ledger (
  case_id text PRIMARY KEY,
  expected_sqlstate text NOT NULL,
  actual_sqlstate text NOT NULL,
  actual_constraint text,
  residue_count bigint NOT NULL,
  pass boolean NOT NULL
);

CREATE FUNCTION pg_temp.expect_missingness_check(p_case_id text,p_sql text)
RETURNS void LANGUAGE plpgsql AS $function$
DECLARE
  v_state text := '00000';
  v_constraint text;
  v_residue bigint;
BEGIN
  BEGIN
    EXECUTE p_sql;
  EXCEPTION WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS
      v_state = RETURNED_SQLSTATE,
      v_constraint = CONSTRAINT_NAME;
  END;
  SELECT count(*) INTO v_residue
  FROM release.research_surface_presentation_projection_v3
  WHERE research_release_id='94000000-0000-4000-8000-000000000001';
  INSERT INTO pg_temp.v49_missingness_ledger
  VALUES(p_case_id,'23514',v_state,v_constraint,v_residue,
    v_state='23514' AND v_residue=0);
  IF v_state <> '23514' OR v_residue <> 0 THEN
    RAISE EXCEPTION 'MISSINGNESS_CASE_FAILED: %, state %, residue %',
      p_case_id,v_state,v_residue;
  END IF;
END
$function$;

SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.create_research_release(
  '94000000-0000-4000-8000-000000000001','v49-missingness-matrix',
  'schema-v49.0','model-v49.0',
  '94000000-0000-4000-8000-000000000002',repeat('1',64));
RESET SESSION AUTHORIZATION;

INSERT INTO release.research_release_object(
  research_release_id,archive_object_id,object_urn,legacy_surface_id,title,
  publication_layer,acceptance_state,workflow_state)
SELECT '94000000-0000-4000-8000-000000000001',archive_object_id,object_urn,
  'missingness-surface',preferred_label,'active','accepted','resolved'
FROM core.archive_object
WHERE archive_object_id='20000000-0000-4000-8000-000000001001';

-- Each of the seven nullable public values has exactly two illegal states:
-- explicit NULL marked present, and a value marked missing.  The statements
-- otherwise contain a valid complete row, so every rejection is attributable
-- to the named value/missingness pair rather than a different constraint.
SELECT pg_temp.expect_missingness_check('title_null_present',$sql$
  INSERT INTO release.research_surface_presentation_projection_v3 VALUES(
    '94000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000001001','missingness-surface',
    NULL,'present',NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing',
    'citation',NULL,'missing','citation','/sources/'||repeat('a',64),'active')$sql$);
SELECT pg_temp.expect_missingness_check('title_value_missing',$sql$
  INSERT INTO release.research_surface_presentation_projection_v3 VALUES(
    '94000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000001001','missingness-surface',
    'title','missing',NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing',
    'citation',NULL,'missing','citation','/sources/'||repeat('a',64),'active')$sql$);

SELECT pg_temp.expect_missingness_check('display_date_null_present',$sql$
  INSERT INTO release.research_surface_presentation_projection_v3 VALUES(
    '94000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000001001','missingness-surface',
    NULL,'missing',NULL,'present',NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing',
    'citation',NULL,'missing','citation','/sources/'||repeat('a',64),'active')$sql$);
SELECT pg_temp.expect_missingness_check('display_date_value_missing',$sql$
  INSERT INTO release.research_surface_presentation_projection_v3 VALUES(
    '94000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000001001','missingness-surface',
    NULL,'missing','2026','missing',NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing',
    'citation',NULL,'missing','citation','/sources/'||repeat('a',64),'active')$sql$);

SELECT pg_temp.expect_missingness_check('normalized_year_null_present',$sql$
  INSERT INTO release.research_surface_presentation_projection_v3 VALUES(
    '94000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000001001','missingness-surface',
    NULL,'missing',NULL,'missing',NULL,'present',NULL,'missing',NULL,'missing',NULL,'missing',
    'citation',NULL,'missing','citation','/sources/'||repeat('a',64),'active')$sql$);
SELECT pg_temp.expect_missingness_check('normalized_year_value_missing',$sql$
  INSERT INTO release.research_surface_presentation_projection_v3 VALUES(
    '94000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000001001','missingness-surface',
    NULL,'missing',NULL,'missing',2026,'missing',NULL,'missing',NULL,'missing',NULL,'missing',
    'citation',NULL,'missing','citation','/sources/'||repeat('a',64),'active')$sql$);

SELECT pg_temp.expect_missingness_check('place_null_present',$sql$
  INSERT INTO release.research_surface_presentation_projection_v3 VALUES(
    '94000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000001001','missingness-surface',
    NULL,'missing',NULL,'missing',NULL,'missing',NULL,'present',NULL,'missing',NULL,'missing',
    'citation',NULL,'missing','citation','/sources/'||repeat('a',64),'active')$sql$);
SELECT pg_temp.expect_missingness_check('place_value_missing',$sql$
  INSERT INTO release.research_surface_presentation_projection_v3 VALUES(
    '94000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000001001','missingness-surface',
    NULL,'missing',NULL,'missing',NULL,'missing','Brisbane','missing',NULL,'missing',NULL,'missing',
    'citation',NULL,'missing','citation','/sources/'||repeat('a',64),'active')$sql$);

SELECT pg_temp.expect_missingness_check('medium_null_present',$sql$
  INSERT INTO release.research_surface_presentation_projection_v3 VALUES(
    '94000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000001001','missingness-surface',
    NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing',NULL,'present',NULL,'missing',
    'citation',NULL,'missing','citation','/sources/'||repeat('a',64),'active')$sql$);
SELECT pg_temp.expect_missingness_check('medium_value_missing',$sql$
  INSERT INTO release.research_surface_presentation_projection_v3 VALUES(
    '94000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000001001','missingness-surface',
    NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing','poster','missing',NULL,'missing',
    'citation',NULL,'missing','citation','/sources/'||repeat('a',64),'active')$sql$);

SELECT pg_temp.expect_missingness_check('type_null_present',$sql$
  INSERT INTO release.research_surface_presentation_projection_v3 VALUES(
    '94000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000001001','missingness-surface',
    NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing',NULL,'present',
    'citation',NULL,'missing','citation','/sources/'||repeat('a',64),'active')$sql$);
SELECT pg_temp.expect_missingness_check('type_value_missing',$sql$
  INSERT INTO release.research_surface_presentation_projection_v3 VALUES(
    '94000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000001001','missingness-surface',
    NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing','design','missing',
    'citation',NULL,'missing','citation','/sources/'||repeat('a',64),'active')$sql$);

SELECT pg_temp.expect_missingness_check('description_null_present',$sql$
  INSERT INTO release.research_surface_presentation_projection_v3 VALUES(
    '94000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000001001','missingness-surface',
    NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing',
    'citation',NULL,'present','citation','/sources/'||repeat('a',64),'active')$sql$);
SELECT pg_temp.expect_missingness_check('description_value_missing',$sql$
  INSERT INTO release.research_surface_presentation_projection_v3 VALUES(
    '94000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000001001','missingness-surface',
    NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing',
    'citation','description','missing','citation','/sources/'||repeat('a',64),'active')$sql$);

SELECT * FROM pg_temp.v49_missingness_ledger ORDER BY case_id;
DO $assert_count$
BEGIN
  IF (SELECT count(*) FROM pg_temp.v49_missingness_ledger WHERE pass) <> 14
    OR (SELECT count(*) FROM pg_temp.v49_missingness_ledger) <> 14 THEN
    RAISE EXCEPTION 'V49_MISSINGNESS_MATRIX_NOT_14_OF_14';
  END IF;
END
$assert_count$;
ROLLBACK;
\echo V49_MISSINGNESS_MATRIX=PASS CASES=14/14
