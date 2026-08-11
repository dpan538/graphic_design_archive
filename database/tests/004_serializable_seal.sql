\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION pg_temp.expect_error(
  p_sql text, p_expected_state text, p_label text
)
RETURNS void LANGUAGE plpgsql AS $function$
DECLARE v_state text;
BEGIN
  BEGIN
    EXECUTE p_sql;
    RAISE EXCEPTION 'EXPECTED_ERROR_NOT_RAISED: %', p_label;
  EXCEPTION WHEN OTHERS THEN
    v_state := SQLSTATE;
  END;
  IF v_state IS DISTINCT FROM p_expected_state THEN
    RAISE EXCEPTION 'WRONG_SQLSTATE: % got %, expected %',
      p_label, v_state, p_expected_state;
  END IF;
END
$function$;

SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT pg_temp.expect_error(
  $$SELECT release.seal_research_release(
    'ffffffff-ffff-4fff-8fff-fffffffffff1',
    'ffffffff-ffff-4fff-8fff-fffffffffff2',
    'ffffffff-ffff-4fff-8fff-fffffffffff3', repeat('1', 64))$$,
  '25001', 'research seal denied outside serializable transaction');
SELECT pg_temp.expect_error(
  $$SELECT release.seal_visual_registry(
    'ffffffff-ffff-4fff-8fff-fffffffffff4',
    'ffffffff-ffff-4fff-8fff-fffffffffff5',
    'ffffffff-ffff-4fff-8fff-fffffffffff6', repeat('2', 64))$$,
  '25001', 'visual seal denied outside serializable transaction');
RESET SESSION AUTHORIZATION;

ROLLBACK;
