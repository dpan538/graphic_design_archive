\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

-- This is additive.  Historical role grants remain an immutable Phase 2A
-- record; Phase 2C grants only the exact-pair, rights-reduced projections.
GRANT SELECT ON api_v1.sealed_research_release_descriptor,
  api_v1.sealed_surface TO gda_v49_phase2a_api_reader;

RESET ROLE;
