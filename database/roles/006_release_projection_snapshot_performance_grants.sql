\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

-- The faultable v5 entry point is test-owner only.  Publishers receive only
-- the five business arguments and cannot request a fault injection.
REVOKE ALL ON FUNCTION
  release.build_research_launch_snapshot_v5_internal(uuid,uuid,uuid,uuid,core.sha256_hex,text)
FROM PUBLIC, gda_v49_phase2a_publisher;
REVOKE ALL ON TABLE release.research_launch_protocol_v5
FROM PUBLIC, gda_v49_phase2a_publisher, gda_v49_phase2a_api_reader;

GRANT EXECUTE ON FUNCTION
  release.build_research_launch_snapshot_v5(uuid,uuid,uuid,uuid,core.sha256_hex),
  release.validate_research_launch_snapshot_v5(uuid,core.sha256_hex,uuid,core.sha256_hex),
  release.seal_research_launch_snapshot_v5(uuid,uuid,uuid,core.sha256_hex)
TO gda_v49_phase2a_publisher;

RESET ROLE;
