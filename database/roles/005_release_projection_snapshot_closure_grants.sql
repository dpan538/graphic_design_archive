\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

-- The six-argument v3 function is retained only as a historical artifact.
-- A publisher can construct a closure snapshot only through the five argument
-- production wrapper.  The faultable internal function remains owner-only.
REVOKE ALL ON FUNCTION
  release.build_research_launch_snapshot_v3(uuid,uuid,uuid,uuid,core.sha256_hex,text),
  release.build_research_launch_snapshot_v4_internal(uuid,uuid,uuid,uuid,core.sha256_hex,text)
FROM PUBLIC, gda_v49_phase2a_publisher;

REVOKE ALL ON TABLE release.research_launch_protocol_v4
  FROM PUBLIC, gda_v49_phase2a_publisher, gda_v49_phase2a_api_reader;

GRANT EXECUTE ON FUNCTION
  release.build_research_launch_snapshot_v4(uuid,uuid,uuid,uuid,core.sha256_hex),
  release.validate_research_launch_snapshot_v4(uuid,core.sha256_hex,uuid,core.sha256_hex),
  release.seal_research_launch_snapshot_v4(uuid,uuid,uuid,core.sha256_hex)
TO gda_v49_phase2a_publisher;

RESET ROLE;
