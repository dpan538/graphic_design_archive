\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

REVOKE ALL ON FUNCTION
  release.record_research_launch_verification_v5(
    uuid,uuid,core.sha256_hex,core.release_token,core.sha256_hex,
    uuid,core.sha256_hex)
FROM PUBLIC, gda_v49_phase2a_publisher, gda_v49_phase2a_api_reader;
GRANT EXECUTE ON FUNCTION
  release.record_research_launch_verification_v5(
    uuid,uuid,core.sha256_hex,core.release_token,core.sha256_hex,
    uuid,core.sha256_hex)
TO gda_v49_phase2a_reviewer;

RESET ROLE;
