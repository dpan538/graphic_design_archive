\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

-- Phase 2C-S closure is forward-only.  It records which construction
-- protocol created a launch snapshot without changing the v3 read-model
-- tables or any historical migration.
CREATE TABLE release.research_launch_protocol_v4 (
  research_release_id uuid PRIMARY KEY
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  protocol_version core.release_token NOT NULL
    CHECK (protocol_version = 'release-snapshot-v4'),
  created_at timestamptz NOT NULL
);

-- The v4 builder's pinned source and bidirectional parity checks use these
-- bounded release-selection access paths; they avoid correlated scans at the
-- authorized 15,923/47,982 scale.
CREATE INDEX legacy_surface_ledger_launch_v4_selection_idx
  ON raw.legacy_surface_ledger(migration_batch_id,import_disposition,archive_object_id);
CREATE INDEX canonical_assignment_launch_v4_selection_idx
  ON provenance.canonical_assignment(assignment_kind,status,supersedes_assignment_id,canonical_assignment_id);

RESET ROLE;
