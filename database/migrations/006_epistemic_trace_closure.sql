\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

-- Evidence lineage is anchored to the governed raw asset.  A source record is
-- optional for document-level evidence, but when present it must belong to the
-- same asset as both the source version and the evidence occurrence.
ALTER TABLE provenance.source_version
  ADD COLUMN source_asset_id uuid NOT NULL
    REFERENCES raw.source_asset(source_asset_id) ON DELETE RESTRICT,
  ADD CONSTRAINT source_version_asset_identity_unique
    UNIQUE (source_version_id, source_asset_id);

ALTER TABLE provenance.evidence_item
  DROP CONSTRAINT evidence_item_source_identity_unique,
  ADD COLUMN source_asset_id uuid NOT NULL
    REFERENCES raw.source_asset(source_asset_id) ON DELETE RESTRICT,
  ADD CONSTRAINT evidence_item_source_version_asset_fk
    FOREIGN KEY (source_version_id, source_asset_id)
    REFERENCES provenance.source_version(source_version_id, source_asset_id)
    ON DELETE RESTRICT,
  ADD CONSTRAINT evidence_item_record_asset_fk
    FOREIGN KEY (source_asset_id, source_record_id)
    REFERENCES raw.source_record(source_asset_id, source_record_id)
    ON DELETE RESTRICT,
  ADD CONSTRAINT evidence_item_source_identity_unique
    UNIQUE NULLS NOT DISTINCT (
      source_asset_id, source_version_id, source_record_id,
      locator_scheme, internal_locator, span_start, span_end, content_sha256);

CREATE TABLE provenance.predicate_evidence_profile (
  predicate_evidence_profile_id uuid PRIMARY KEY,
  profile_version core.release_token NOT NULL,
  profile_sha256 core.sha256_hex NOT NULL,
  requires_supporting_evidence boolean NOT NULL,
  requires_review_decision boolean NOT NULL,
  minimum_support_count integer NOT NULL CHECK (minimum_support_count >= 0),
  description text NOT NULL CHECK (btrim(description) <> ''),
  UNIQUE (profile_version, profile_sha256),
  CHECK (requires_supporting_evidence AND requires_review_decision
    AND minimum_support_count >= 1)
);

ALTER TABLE provenance.assertion_predicate
  ADD COLUMN registry_version core.release_token NOT NULL,
  ADD COLUMN subject_domain provenance.assertion_subject_kind NOT NULL,
  ADD COLUMN value_range provenance.assertion_value_kind NOT NULL,
  ADD COLUMN predicate_evidence_profile_id uuid NOT NULL
    REFERENCES provenance.predicate_evidence_profile(
      predicate_evidence_profile_id) ON DELETE RESTRICT;

CREATE TABLE provenance.assignment_predicate_compatibility (
  assignment_kind provenance.assignment_kind NOT NULL,
  assertion_predicate_id uuid NOT NULL
    REFERENCES provenance.assertion_predicate(assertion_predicate_id)
    ON DELETE RESTRICT,
  compatibility_version core.release_token NOT NULL,
  compatibility_sha256 core.sha256_hex NOT NULL,
  PRIMARY KEY (assignment_kind, assertion_predicate_id)
);

ALTER TYPE provenance.assertion_value_kind ADD VALUE 'folder';
ALTER TYPE provenance.assertion_value_kind ADD VALUE 'digital_representation';
ALTER TYPE provenance.assertion_value_kind ADD VALUE 'legacy_identity_resolution';

CREATE TABLE provenance.assertion_value_folder (
  assertion_id uuid PRIMARY KEY
    REFERENCES provenance.assertion(assertion_id) ON DELETE RESTRICT,
  folder_id uuid NOT NULL
    REFERENCES research.folder(folder_id) ON DELETE RESTRICT
);

CREATE TABLE provenance.assertion_value_representation (
  assertion_id uuid PRIMARY KEY
    REFERENCES provenance.assertion(assertion_id) ON DELETE RESTRICT,
  digital_representation_id uuid NOT NULL
    REFERENCES rights.digital_representation(digital_representation_id)
    ON DELETE RESTRICT
);

CREATE TABLE provenance.assertion_value_identity_resolution (
  assertion_id uuid PRIMARY KEY
    REFERENCES provenance.assertion(assertion_id) ON DELETE RESTRICT,
  legacy_identity_resolution_id uuid NOT NULL
    REFERENCES core.legacy_identity_resolution(legacy_identity_resolution_id)
    ON DELETE RESTRICT
);

-- A trace node may describe any closed core entity, not only archive objects.
-- Object-root identity remains the dedicated object_trace_node bridge.
ALTER TABLE research.trace_node
  ADD COLUMN entity_id uuid REFERENCES core.entity(entity_id) ON DELETE RESTRICT,
  ADD COLUMN node_type core.release_token NOT NULL,
  ADD COLUMN evidence_item_id uuid
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT;

CREATE INDEX trace_node_entity_idx
  ON research.trace_node(entity_id, trace_node_id);

CREATE TABLE research.trace_tree (
  trace_tree_id uuid PRIMARY KEY,
  tree_token core.release_token NOT NULL UNIQUE,
  label text NOT NULL CHECK (btrim(label) <> ''),
  evidence_item_id uuid
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL
);

CREATE TABLE research.trace_branch (
  trace_tree_id uuid NOT NULL
    REFERENCES research.trace_tree(trace_tree_id) ON DELETE RESTRICT,
  trace_branch_id uuid NOT NULL,
  branch_token core.release_token NOT NULL,
  label text NOT NULL CHECK (btrim(label) <> ''),
  created_at timestamptz NOT NULL,
  PRIMARY KEY (trace_tree_id, trace_branch_id),
  UNIQUE (trace_tree_id, branch_token)
);

CREATE TABLE research.trace_node_tree_membership (
  trace_node_id uuid NOT NULL
    REFERENCES research.trace_node(trace_node_id) ON DELETE RESTRICT,
  trace_tree_id uuid NOT NULL,
  trace_branch_id uuid NOT NULL,
  placement_role core.release_token NOT NULL,
  evidence_item_id uuid
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  PRIMARY KEY (
    trace_node_id, trace_tree_id, trace_branch_id, placement_role),
  FOREIGN KEY (trace_tree_id, trace_branch_id)
    REFERENCES research.trace_branch(trace_tree_id, trace_branch_id)
    ON DELETE RESTRICT
);

ALTER TABLE release.trace_projection_node
  ADD COLUMN entity_id uuid REFERENCES core.entity(entity_id) ON DELETE RESTRICT,
  ADD COLUMN node_type core.release_token NOT NULL,
  ADD COLUMN evidence_item_id uuid
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  ADD CONSTRAINT trace_projection_node_object_entity_match CHECK (
    archive_object_id IS NULL
    OR (entity_id IS NOT NULL AND entity_id = archive_object_id));

CREATE TABLE release.trace_tree_projection (
  research_release_id uuid NOT NULL,
  corpus_version_id uuid NOT NULL,
  trace_tree_id uuid NOT NULL,
  tree_token core.release_token NOT NULL,
  label text NOT NULL,
  evidence_item_id uuid,
  PRIMARY KEY (research_release_id, corpus_version_id, trace_tree_id),
  FOREIGN KEY (research_release_id, corpus_version_id)
    REFERENCES release.research_corpus_snapshot(
      research_release_id, corpus_version_id) ON DELETE RESTRICT,
  FOREIGN KEY (trace_tree_id)
    REFERENCES research.trace_tree(trace_tree_id) ON DELETE RESTRICT,
  FOREIGN KEY (evidence_item_id)
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT
);

CREATE TABLE release.trace_branch_projection (
  research_release_id uuid NOT NULL,
  corpus_version_id uuid NOT NULL,
  trace_tree_id uuid NOT NULL,
  trace_branch_id uuid NOT NULL,
  branch_token core.release_token NOT NULL,
  label text NOT NULL,
  PRIMARY KEY (
    research_release_id, corpus_version_id, trace_tree_id, trace_branch_id),
  FOREIGN KEY (research_release_id, corpus_version_id, trace_tree_id)
    REFERENCES release.trace_tree_projection(
      research_release_id, corpus_version_id, trace_tree_id)
    ON DELETE RESTRICT,
  FOREIGN KEY (trace_tree_id, trace_branch_id)
    REFERENCES research.trace_branch(trace_tree_id, trace_branch_id)
    ON DELETE RESTRICT
);

CREATE TABLE release.trace_node_tree_placement (
  research_release_id uuid NOT NULL,
  corpus_version_id uuid NOT NULL,
  trace_node_id uuid NOT NULL,
  trace_tree_id uuid NOT NULL,
  trace_branch_id uuid NOT NULL,
  placement_role core.release_token NOT NULL,
  evidence_item_id uuid,
  PRIMARY KEY (
    research_release_id, corpus_version_id, trace_node_id,
    trace_tree_id, trace_branch_id, placement_role),
  FOREIGN KEY (research_release_id, corpus_version_id, trace_node_id)
    REFERENCES release.trace_projection_node(
      research_release_id, corpus_version_id, trace_node_id)
    ON DELETE RESTRICT,
  FOREIGN KEY (
    research_release_id, corpus_version_id,
    trace_tree_id, trace_branch_id)
    REFERENCES release.trace_branch_projection(
      research_release_id, corpus_version_id,
      trace_tree_id, trace_branch_id) ON DELETE RESTRICT,
  FOREIGN KEY (evidence_item_id)
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT
);

CREATE TABLE release.trace_edge_tree_placement (
  research_release_id uuid NOT NULL,
  corpus_version_id uuid NOT NULL,
  subject_trace_node_id uuid NOT NULL,
  semantic_relation_id uuid NOT NULL,
  object_trace_node_id uuid NOT NULL,
  projection_role text NOT NULL,
  trace_tree_id uuid NOT NULL,
  trace_branch_id uuid NOT NULL,
  placement_role core.release_token NOT NULL,
  PRIMARY KEY (
    research_release_id, corpus_version_id, subject_trace_node_id,
    semantic_relation_id, object_trace_node_id, projection_role,
    trace_tree_id, trace_branch_id, placement_role),
  FOREIGN KEY (
    research_release_id, corpus_version_id, subject_trace_node_id,
    semantic_relation_id, object_trace_node_id, projection_role)
    REFERENCES release.trace_projection_edge(
      research_release_id, corpus_version_id, subject_trace_node_id,
      semantic_relation_id, object_trace_node_id, projection_role)
    ON DELETE RESTRICT,
  FOREIGN KEY (
    research_release_id, corpus_version_id,
    trace_tree_id, trace_branch_id)
    REFERENCES release.trace_branch_projection(
      research_release_id, corpus_version_id,
      trace_tree_id, trace_branch_id) ON DELETE RESTRICT
);

-- Validation profiles are boundary-specific; a research release can never be
-- closed under a visual profile and vice versa.
ALTER TABLE release.research_release
  ADD COLUMN validation_boundary release.boundary_kind NOT NULL
    DEFAULT 'research' CHECK (validation_boundary = 'research'),
  ADD CONSTRAINT research_release_validation_profile_boundary_fk
    FOREIGN KEY (validation_profile_id, validation_boundary)
    REFERENCES release.validation_profile(
      validation_profile_id, boundary_kind) ON DELETE RESTRICT;
ALTER TABLE release.visual_registry_release
  ADD COLUMN validation_boundary release.boundary_kind NOT NULL
    DEFAULT 'visual' CHECK (validation_boundary = 'visual'),
  ADD CONSTRAINT visual_release_validation_profile_boundary_fk
    FOREIGN KEY (validation_profile_id, validation_boundary)
    REFERENCES release.validation_profile(
      validation_profile_id, boundary_kind) ON DELETE RESTRICT;

ALTER TABLE research.analysis_run
  ALTER COLUMN input_release_id SET NOT NULL;

ALTER TABLE research.epistemic_class
  ADD COLUMN profile_version core.release_token NOT NULL,
  ADD COLUMN profile_sha256 core.sha256_hex NOT NULL;
ALTER TABLE research.relation_type
  ADD COLUMN registry_version core.release_token NOT NULL;

ALTER TABLE research.claim_revision
  ADD CONSTRAINT claim_revision_one_successor
    UNIQUE (supersedes_claim_revision_id);

ALTER TABLE release.research_release_claim
  ADD COLUMN claim_review_decision_id uuid NOT NULL
    REFERENCES research.claim_review_decision(claim_review_decision_id)
    ON DELETE RESTRICT,
  ADD COLUMN epistemic_profile_version core.release_token NOT NULL;

ALTER TABLE release.research_release_claim_evidence
  ADD COLUMN source_asset_id uuid NOT NULL,
  ADD CONSTRAINT research_claim_evidence_source_version_asset_fk
    FOREIGN KEY (source_version_id, source_asset_id)
    REFERENCES provenance.source_version(source_version_id, source_asset_id)
    ON DELETE RESTRICT,
  ADD CONSTRAINT research_claim_evidence_record_asset_fk
    FOREIGN KEY (source_asset_id, source_record_id)
    REFERENCES raw.source_record(source_asset_id, source_record_id)
    ON DELETE RESTRICT;

ALTER TABLE release.research_release_relation_evidence
  ADD COLUMN source_asset_id uuid NOT NULL
    REFERENCES raw.source_asset(source_asset_id) ON DELETE RESTRICT;

ALTER TABLE rights.provider_policy_version
  DROP CONSTRAINT provider_policy_version_provider_id_policy_sha256_key,
  DROP CONSTRAINT provider_policy_version_provider_id_version_token_key,
  ADD CONSTRAINT provider_policy_version_scoped_token_unique
    UNIQUE (provider_id, policy_scope_id, version_token);

ALTER TABLE release.visual_registry_policy_version_snapshot
  ADD CONSTRAINT visual_policy_snapshot_scope_fk
    FOREIGN KEY (provider_id, policy_scope_id)
    REFERENCES rights.provider_policy_scope(provider_id, policy_scope_id)
    ON DELETE RESTRICT;

CREATE INDEX research_source_lineage_asset_idx
  ON release.research_source_lineage(source_asset_id, research_release_id);
CREATE INDEX research_claim_evidence_asset_idx
  ON release.research_release_claim_evidence(
    research_release_id, source_asset_id, source_record_id);
CREATE INDEX trace_edge_tree_placement_tree_idx
  ON release.trace_edge_tree_placement(
    research_release_id, corpus_version_id,
    trace_tree_id, trace_branch_id);

RESET ROLE;
