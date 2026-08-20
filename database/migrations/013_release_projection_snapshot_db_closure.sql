\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

-- The v5 publishable index is fully covered by the earlier v4 selection
-- index for the shared (assignment_kind, status) predicate.  Internal 1k/2k
-- plans use the reverse current-leaf index plus set-based scans; no function,
-- constraint, sealed release, API object, or canonical adapter depends on
-- this candidate-only duplicate.
DROP INDEX provenance.canonical_assignment_publishable_v5_idx;

RESET ROLE;
