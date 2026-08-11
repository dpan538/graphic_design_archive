\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

-- Release copies retain working-row lineage through real keys. The copied
-- values remain immutable after candidate close, but an identifier cannot be
-- paired with source/version data from a different evidence occurrence.
ALTER TABLE provenance.evidence_item
  ADD CONSTRAINT evidence_item_source_triplet_unique
    UNIQUE (evidence_item_id, source_asset_id, source_version_id);

ALTER TABLE release.research_release_claim
  ADD CONSTRAINT research_claim_claimant_fk
    FOREIGN KEY (claimant_agent_id)
    REFERENCES core.agent(agent_id) ON DELETE RESTRICT,
  ADD CONSTRAINT research_claim_temporal_fk
    FOREIGN KEY (temporal_qualifier_id)
    REFERENCES core.temporal_extent(temporal_extent_id) ON DELETE RESTRICT,
  ADD CONSTRAINT research_claim_spatial_fk
    FOREIGN KEY (spatial_qualifier_id)
    REFERENCES core.place(place_id) ON DELETE RESTRICT,
  ADD CONSTRAINT research_claim_analysis_copy_fk
    FOREIGN KEY (research_release_id, analysis_run_id)
    REFERENCES release.research_release_analysis_run(
      research_release_id, analysis_run_id) ON DELETE RESTRICT;

ALTER TABLE release.research_release_claim_evidence
  ADD CONSTRAINT research_claim_evidence_item_fk
    FOREIGN KEY (evidence_item_id)
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  ADD CONSTRAINT research_claim_evidence_item_source_fk
    FOREIGN KEY (evidence_item_id, source_asset_id, source_version_id)
    REFERENCES provenance.evidence_item(
      evidence_item_id, source_asset_id, source_version_id) ON DELETE RESTRICT;

ALTER TABLE release.research_release_analysis_run
  ADD CONSTRAINT research_analysis_run_source_fk
    FOREIGN KEY (analysis_run_id)
    REFERENCES research.analysis_run(analysis_run_id) ON DELETE RESTRICT,
  ADD CONSTRAINT research_analysis_run_input_release_fk
    FOREIGN KEY (input_research_release_id, input_research_manifest_sha256)
    REFERENCES release.research_release(
      research_release_id, manifest_sha256) ON DELETE RESTRICT,
  ADD CONSTRAINT research_analysis_run_corpus_policy_fk
    FOREIGN KEY (input_corpus_version_id, input_corpus_policy_sha256)
    REFERENCES research.corpus_version(
      corpus_version_id, policy_sha256) ON DELETE RESTRICT;

ALTER TABLE release.research_release_relation
  ADD CONSTRAINT research_relation_type_fk
    FOREIGN KEY (relation_type_id)
    REFERENCES research.relation_type(relation_type_id) ON DELETE RESTRICT,
  ADD CONSTRAINT research_relation_temporal_fk
    FOREIGN KEY (temporal_qualifier_id)
    REFERENCES core.temporal_extent(temporal_extent_id) ON DELETE RESTRICT,
  ADD CONSTRAINT research_relation_spatial_fk
    FOREIGN KEY (spatial_qualifier_id)
    REFERENCES core.place(place_id) ON DELETE RESTRICT;

ALTER TABLE release.research_release_relation_evidence
  ADD COLUMN source_version_id uuid NOT NULL,
  ADD COLUMN source_record_id uuid,
  ADD CONSTRAINT research_relation_evidence_item_fk
    FOREIGN KEY (evidence_item_id)
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  ADD CONSTRAINT research_relation_evidence_item_source_fk
    FOREIGN KEY (evidence_item_id, source_asset_id, source_version_id)
    REFERENCES provenance.evidence_item(
      evidence_item_id, source_asset_id, source_version_id) ON DELETE RESTRICT,
  ADD CONSTRAINT research_relation_evidence_source_version_fk
    FOREIGN KEY (source_version_id, source_asset_id)
    REFERENCES provenance.source_version(
      source_version_id, source_asset_id) ON DELETE RESTRICT,
  ADD CONSTRAINT research_relation_evidence_source_record_fk
    FOREIGN KEY (source_asset_id, source_record_id)
    REFERENCES raw.source_record(
      source_asset_id, source_record_id) ON DELETE RESTRICT;

CREATE TABLE release.research_folder_projection (
  research_release_id uuid NOT NULL
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  folder_id uuid NOT NULL
    REFERENCES research.folder(folder_id) ON DELETE RESTRICT,
  folder_token core.release_token NOT NULL,
  label text NOT NULL CHECK (btrim(label) <> ''),
  PRIMARY KEY (research_release_id, folder_id)
);

ALTER TABLE release.research_legacy_identity_resolution
  ADD COLUMN target_trace_node_corpus_version_id uuid,
  ADD CONSTRAINT research_legacy_resolution_object_fk
    FOREIGN KEY (research_release_id, target_archive_object_id)
    REFERENCES release.research_release_object(
      research_release_id, archive_object_id) ON DELETE RESTRICT,
  ADD CONSTRAINT research_legacy_resolution_source_record_fk
    FOREIGN KEY (target_source_record_id)
    REFERENCES raw.source_record(source_record_id) ON DELETE RESTRICT,
  ADD CONSTRAINT research_legacy_resolution_trace_node_fk
    FOREIGN KEY (
      research_release_id, target_trace_node_corpus_version_id,
      target_trace_node_id)
    REFERENCES release.trace_projection_node(
      research_release_id, corpus_version_id, trace_node_id)
    ON DELETE RESTRICT,
  ADD CONSTRAINT research_legacy_resolution_folder_fk
    FOREIGN KEY (research_release_id, target_folder_id)
    REFERENCES release.research_folder_projection(
      research_release_id, folder_id) ON DELETE RESTRICT,
  ADD CONSTRAINT research_legacy_resolution_trace_node_shape CHECK (
    (target_trace_node_id IS NULL
      AND target_trace_node_corpus_version_id IS NULL)
    OR
    (target_trace_node_id IS NOT NULL
      AND target_trace_node_corpus_version_id IS NOT NULL));

CREATE INDEX research_relation_evidence_source_idx
  ON release.research_release_relation_evidence(
    research_release_id, source_asset_id, source_version_id, source_record_id);
CREATE INDEX research_folder_projection_token_idx
  ON release.research_folder_projection(research_release_id, folder_token);

RESET ROLE;
