\set ON_ERROR_STOP on
BEGIN;
-- This regression must fail if somebody restores the obsolete publisher
-- grants merely to make the historical phase2c fixture green.
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
DO $legacy_denied$
DECLARE command text; denied integer := 0;
BEGIN
  FOREACH command IN ARRAY ARRAY[
    $sql$SELECT release.add_research_source_lineage_to_draft(NULL::uuid, 'v48_candidate_json'::release.research_source_role, NULL::uuid, NULL::text)$sql$,
    $sql$SELECT release.close_research_candidate(NULL::uuid, NULL::core.sha256_hex, NULL::uuid, NULL::core.sha256_hex)$sql$,
    $sql$SELECT release.validate_research_release(NULL::uuid, NULL::uuid, NULL::core.release_token, NULL::core.sha256_hex, NULL::uuid, NULL::core.sha256_hex)$sql$,
    $sql$SELECT release.seal_research_release(NULL::uuid, NULL::uuid, NULL::uuid, NULL::core.sha256_hex)$sql$,
    $sql$SELECT release.build_research_launch_snapshot_v3(NULL::uuid, NULL::uuid, NULL::uuid, NULL::uuid, NULL::core.sha256_hex, NULL::text)$sql$,
    $sql$SELECT release.build_research_launch_snapshot_v5_internal(NULL::uuid, NULL::uuid, NULL::uuid, NULL::uuid, NULL::core.sha256_hex, NULL::text)$sql$
  ] LOOP
    BEGIN
      EXECUTE command;
      RAISE EXCEPTION 'OBSOLETE_OR_INTERNAL_PUBLISHER_ENTRYPOINT_ALLOWED';
    EXCEPTION WHEN insufficient_privilege THEN
      denied := denied + 1;
    END;
  END LOOP;
  IF denied <> 6 THEN RAISE EXCEPTION 'PUBLISHER_DENIAL_COUNT: %', denied; END IF;
END
$legacy_denied$;
RESET SESSION AUTHORIZATION;
ROLLBACK;
\echo CURRENT_PUBLISHER_ENTRYPOINTS=PASS DENIED=6/6
