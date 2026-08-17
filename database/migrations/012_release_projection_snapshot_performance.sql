\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

-- Phase 2S-P is a forward-only v5 construction protocol.  It deliberately
-- reuses the immutable v3 projection tables but never reinterprets a v4
-- receipt or digest as v5 evidence.
CREATE TABLE release.research_launch_protocol_v5 (
  research_release_id uuid PRIMARY KEY
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  protocol_version core.release_token NOT NULL
    CHECK (protocol_version = 'release-snapshot-v5'),
  created_at timestamptz NOT NULL
);

-- A newer assignment/decision points back to the superseded record.  These
-- indexes support the anti-joins that select current leaves without asserting
-- an invalid no-branching rule on historical provenance.
CREATE INDEX canonical_assignment_current_leaf_v5_idx
  ON provenance.canonical_assignment(supersedes_assignment_id)
  WHERE supersedes_assignment_id IS NOT NULL;
CREATE INDEX assignment_review_decision_current_leaf_v5_idx
  ON provenance.assignment_review_decision(supersedes_decision_id)
  WHERE supersedes_decision_id IS NOT NULL;
CREATE INDEX canonical_assignment_publishable_v5_idx
  ON provenance.canonical_assignment(assignment_kind, status, canonical_assignment_id);
CREATE INDEX assignment_decision_evidence_supports_v5_idx
  ON provenance.assignment_decision_evidence(assignment_review_decision_id)
  WHERE evidence_role = 'supports';

RESET ROLE;
