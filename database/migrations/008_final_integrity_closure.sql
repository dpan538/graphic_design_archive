\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

-- A relation-to-claim support edge is revision-pinned. Older immutable rows
-- remain historical when a new accepted claim revision replaces them.
ALTER TABLE research.relation_claim
  DROP CONSTRAINT relation_claim_pkey,
  ADD CONSTRAINT relation_claim_pkey PRIMARY KEY (
    semantic_relation_id, claim_revision_id, claim_role
  );
CREATE INDEX relation_claim_claim_identity_idx
  ON research.relation_claim (claim_id, semantic_relation_id, claim_role);

-- Stable bridge identity plus append-only, evidence-bound review history.
CREATE TABLE rights.object_visual_reference_review_decision (
  object_visual_reference_review_decision_id uuid PRIMARY KEY,
  object_visual_reference_id uuid NOT NULL
    REFERENCES rights.object_visual_reference(object_visual_reference_id)
    ON DELETE RESTRICT,
  outcome workflow.review_outcome NOT NULL
    CHECK (outcome IN ('accept','hold','reject','supersede')),
  evidence_item_id uuid NOT NULL
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  reviewer_actor text NOT NULL CHECK (btrim(reviewer_actor) <> ''),
  rationale text NOT NULL CHECK (btrim(rationale) <> ''),
  supersedes_decision_id uuid
    REFERENCES rights.object_visual_reference_review_decision(
      object_visual_reference_review_decision_id) ON DELETE RESTRICT,
  decided_at timestamptz NOT NULL,
  UNIQUE (supersedes_decision_id)
);
CREATE INDEX object_visual_reference_decision_current_idx
  ON rights.object_visual_reference_review_decision (
    object_visual_reference_id, decided_at DESC
  );

ALTER TABLE release.visual_registry_bridge_snapshot
  ADD COLUMN acceptance_state provenance.assertion_status NOT NULL,
  ADD COLUMN evidence_item_id uuid NOT NULL
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  ADD COLUMN bridge_review_decision_id uuid NOT NULL
    REFERENCES rights.object_visual_reference_review_decision(
      object_visual_reference_review_decision_id) ON DELETE RESTRICT,
  ADD COLUMN evidence_snapshot_sha256 core.sha256_hex NOT NULL,
  ADD COLUMN decision_snapshot_sha256 core.sha256_hex NOT NULL;

ALTER TYPE audit.decision_kind ADD VALUE 'visual_bridge_review';
CREATE TABLE audit.decision_event_visual_bridge_review (
  decision_event_id uuid PRIMARY KEY
    REFERENCES audit.decision_event(decision_event_id) ON DELETE RESTRICT,
  object_visual_reference_review_decision_id uuid NOT NULL UNIQUE
    REFERENCES rights.object_visual_reference_review_decision(
      object_visual_reference_review_decision_id) ON DELETE RESTRICT
);

RESET ROLE;
