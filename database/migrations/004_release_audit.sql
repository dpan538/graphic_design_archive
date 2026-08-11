\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

CREATE TABLE release.research_release (
  research_release_id uuid PRIMARY KEY,
  release_token core.release_token NOT NULL UNIQUE,
  release_state release.release_state NOT NULL,
  schema_version core.release_token NOT NULL,
  model_version core.release_token NOT NULL,
  candidate_fingerprint core.sha256_hex,
  manifest_sha256 core.sha256_hex,
  created_at timestamptz NOT NULL,
  candidate_at timestamptz,
  validated_at timestamptz,
  sealed_at timestamptz,
  CONSTRAINT research_release_state_shape CHECK (
    (release_state = 'draft' AND candidate_fingerprint IS NULL AND manifest_sha256 IS NULL
      AND candidate_at IS NULL AND validated_at IS NULL AND sealed_at IS NULL)
    OR (release_state = 'candidate' AND candidate_fingerprint IS NOT NULL AND manifest_sha256 IS NULL
      AND candidate_at IS NOT NULL AND validated_at IS NULL AND sealed_at IS NULL)
    OR (release_state = 'validated' AND candidate_fingerprint IS NOT NULL AND manifest_sha256 IS NULL
      AND candidate_at IS NOT NULL AND validated_at IS NOT NULL AND sealed_at IS NULL)
    OR (release_state = 'sealed' AND candidate_fingerprint IS NOT NULL AND manifest_sha256 IS NOT NULL
      AND candidate_at IS NOT NULL AND validated_at IS NOT NULL AND sealed_at IS NOT NULL)
  ),
  UNIQUE (research_release_id, manifest_sha256)
);

CREATE INDEX research_release_state_idx ON release.research_release (release_state, created_at);

ALTER TABLE research.analysis_run
  ADD CONSTRAINT analysis_run_input_release_fk
  FOREIGN KEY (input_release_id, input_manifest_sha256)
  REFERENCES release.research_release(research_release_id, manifest_sha256) ON DELETE RESTRICT;

ALTER TABLE core.legacy_identity_resolution
  ADD CONSTRAINT legacy_resolution_effective_release_fk
  FOREIGN KEY (effective_release_id)
  REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT;

CREATE TABLE release.research_release_object (
  research_release_id uuid NOT NULL
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  object_urn core.canonical_urn NOT NULL,
  legacy_surface_id text,
  title text,
  publication_layer release.publication_layer NOT NULL,
  acceptance_state provenance.assertion_status NOT NULL,
  workflow_state workflow.queue_state NOT NULL,
  PRIMARY KEY (research_release_id, archive_object_id),
  UNIQUE (research_release_id, object_urn)
);

CREATE UNIQUE INDEX research_release_object_legacy_surface_uidx
  ON release.research_release_object (research_release_id, legacy_surface_id)
  WHERE legacy_surface_id IS NOT NULL;

CREATE INDEX research_release_object_legacy_idx
  ON release.research_release_object (research_release_id, legacy_surface_id);

CREATE TABLE release.research_release_corpus_member (
  research_release_id uuid NOT NULL,
  corpus_version_id uuid NOT NULL
    REFERENCES research.corpus_version(corpus_version_id) ON DELETE RESTRICT,
  archive_object_id uuid NOT NULL,
  disposition research.membership_disposition NOT NULL,
  reason_code text NOT NULL CHECK (btrim(reason_code) <> ''),
  PRIMARY KEY (research_release_id, corpus_version_id, archive_object_id),
  FOREIGN KEY (research_release_id, archive_object_id)
    REFERENCES release.research_release_object(research_release_id, archive_object_id)
    ON DELETE RESTRICT
);

CREATE INDEX research_release_corpus_disposition_idx
  ON release.research_release_corpus_member
    (research_release_id, corpus_version_id, disposition, archive_object_id);

CREATE TABLE release.research_release_claim (
  research_release_id uuid NOT NULL
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  claim_id uuid NOT NULL REFERENCES research.claim(claim_id) ON DELETE RESTRICT,
  claim_revision_id uuid NOT NULL
    REFERENCES research.claim_revision(claim_revision_id) ON DELETE RESTRICT,
  claim_urn core.canonical_urn NOT NULL,
  epistemic_code text NOT NULL CHECK (epistemic_code ~ '^[a-z][a-z0-9_]*$'),
  wording text NOT NULL,
  PRIMARY KEY (research_release_id, claim_id),
  UNIQUE (research_release_id, claim_urn),
  UNIQUE (research_release_id, claim_revision_id),
  FOREIGN KEY (claim_id, claim_revision_id)
    REFERENCES research.claim_revision(claim_id, claim_revision_id) ON DELETE RESTRICT
);

CREATE TABLE release.research_release_relation (
  research_release_id uuid NOT NULL
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  semantic_relation_id uuid NOT NULL
    REFERENCES research.semantic_relation(semantic_relation_id) ON DELETE RESTRICT,
  relation_urn core.canonical_urn NOT NULL,
  relation_code text NOT NULL CHECK (relation_code ~ '^[a-z][a-z0-9_]*$'),
  subject_entity_id uuid NOT NULL REFERENCES core.entity(entity_id) ON DELETE RESTRICT,
  object_entity_id uuid NOT NULL REFERENCES core.entity(entity_id) ON DELETE RESTRICT,
  acceptance_basis research.relation_acceptance_basis NOT NULL,
  supporting_claim_revision_id uuid,
  supporting_decision_id uuid
    REFERENCES research.relation_review_decision(relation_review_decision_id)
    ON DELETE RESTRICT,
  epistemic_code text CHECK (
    epistemic_code IS NULL OR epistemic_code ~ '^[a-z][a-z0-9_]*$'),
  PRIMARY KEY (research_release_id, semantic_relation_id),
  UNIQUE (research_release_id, relation_urn),
  FOREIGN KEY (research_release_id, supporting_claim_revision_id)
    REFERENCES release.research_release_claim
      (research_release_id, claim_revision_id) ON DELETE RESTRICT,
  CHECK (
    (acceptance_basis = 'accepted_claim'
      AND supporting_claim_revision_id IS NOT NULL
      AND supporting_decision_id IS NULL AND epistemic_code IS NOT NULL)
    OR
    (acceptance_basis = 'curator_decision'
      AND supporting_claim_revision_id IS NULL
      AND supporting_decision_id IS NOT NULL AND epistemic_code IS NULL)
  )
);

CREATE INDEX research_release_relation_subject_idx
  ON release.research_release_relation (research_release_id, subject_entity_id, relation_code);
CREATE INDEX research_release_relation_object_idx
  ON release.research_release_relation (research_release_id, object_entity_id, relation_code);

CREATE TABLE release.trace_projection_node (
  research_release_id uuid NOT NULL
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  corpus_version_id uuid NOT NULL
    REFERENCES research.corpus_version(corpus_version_id) ON DELETE RESTRICT,
  trace_node_id uuid NOT NULL
    REFERENCES research.trace_node(trace_node_id) ON DELETE RESTRICT,
  archive_object_id uuid,
  canonical_key text NOT NULL CHECK (btrim(canonical_key) <> ''),
  label text,
  PRIMARY KEY (research_release_id, corpus_version_id, trace_node_id),
  FOREIGN KEY (research_release_id, archive_object_id)
    REFERENCES release.research_release_object(research_release_id, archive_object_id)
    ON DELETE RESTRICT
);

CREATE INDEX trace_projection_node_canonical_key_idx
  ON release.trace_projection_node
    (research_release_id, corpus_version_id, canonical_key);

CREATE INDEX trace_projection_node_object_idx
  ON release.trace_projection_node (research_release_id, archive_object_id);

CREATE TABLE release.trace_projection_edge (
  research_release_id uuid NOT NULL,
  corpus_version_id uuid NOT NULL,
  subject_trace_node_id uuid NOT NULL,
  semantic_relation_id uuid NOT NULL,
  object_trace_node_id uuid NOT NULL,
  projection_role text NOT NULL CHECK (projection_role ~ '^[a-z][a-z0-9_]*$'),
  generation_key core.sha256_hex NOT NULL,
  PRIMARY KEY (
    research_release_id, corpus_version_id, subject_trace_node_id,
    semantic_relation_id, object_trace_node_id, projection_role
  ),
  FOREIGN KEY (research_release_id, corpus_version_id, subject_trace_node_id)
    REFERENCES release.trace_projection_node
      (research_release_id, corpus_version_id, trace_node_id) ON DELETE RESTRICT,
  FOREIGN KEY (research_release_id, corpus_version_id, object_trace_node_id)
    REFERENCES release.trace_projection_node
      (research_release_id, corpus_version_id, trace_node_id) ON DELETE RESTRICT,
  FOREIGN KEY (research_release_id, semantic_relation_id)
    REFERENCES release.research_release_relation
      (research_release_id, semantic_relation_id) ON DELETE RESTRICT,
  CHECK (subject_trace_node_id <> object_trace_node_id)
);

ALTER TABLE core.legacy_identity_resolution
  ADD CONSTRAINT legacy_identity_resolution_effective_release_fk
  FOREIGN KEY (effective_release_id)
  REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  ADD CONSTRAINT legacy_identity_resolution_trace_edge_fk
  FOREIGN KEY (
    target_trace_edge_release_id, target_trace_edge_corpus_version_id,
    target_trace_edge_subject_node_id, target_trace_edge_relation_id,
    target_trace_edge_object_node_id, target_trace_edge_projection_role
  ) REFERENCES release.trace_projection_edge (
    research_release_id, corpus_version_id, subject_trace_node_id,
    semantic_relation_id, object_trace_node_id, projection_role
  ) ON DELETE RESTRICT;

CREATE INDEX trace_projection_edge_relation_idx
  ON release.trace_projection_edge
    (research_release_id, semantic_relation_id, corpus_version_id);

CREATE TABLE release.object_relation_membership_projection (
  research_release_id uuid NOT NULL,
  corpus_version_id uuid NOT NULL
    REFERENCES research.corpus_version(corpus_version_id) ON DELETE RESTRICT,
  archive_object_id uuid NOT NULL,
  semantic_relation_id uuid NOT NULL,
  membership_role text NOT NULL CHECK (membership_role ~ '^[a-z][a-z0-9_]*$'),
  publication_layer release.publication_layer NOT NULL,
  metric_code text NOT NULL CHECK (metric_code ~ '^[a-z][a-z0-9_]*$'),
  count_eligibility release.count_eligibility NOT NULL,
  eligibility_reason_code text NOT NULL CHECK (btrim(eligibility_reason_code) <> ''),
  PRIMARY KEY (
    research_release_id, corpus_version_id, archive_object_id,
    semantic_relation_id, membership_role, metric_code
  ),
  FOREIGN KEY (research_release_id, archive_object_id)
    REFERENCES release.research_release_object(research_release_id, archive_object_id)
    ON DELETE RESTRICT,
  FOREIGN KEY (research_release_id, semantic_relation_id)
    REFERENCES release.research_release_relation(research_release_id, semantic_relation_id)
    ON DELETE RESTRICT
);

CREATE INDEX object_relation_membership_projection_relation_idx
  ON release.object_relation_membership_projection
    (research_release_id, corpus_version_id, semantic_relation_id, archive_object_id);

CREATE TABLE release.research_object_metric_eligibility (
  research_release_id uuid NOT NULL,
  archive_object_id uuid NOT NULL,
  metric_code text NOT NULL CHECK (metric_code ~ '^[a-z][a-z0-9_]*$'),
  count_eligibility release.count_eligibility NOT NULL,
  reason_code text NOT NULL CHECK (btrim(reason_code) <> ''),
  PRIMARY KEY (research_release_id, archive_object_id, metric_code),
  FOREIGN KEY (research_release_id, archive_object_id)
    REFERENCES release.research_release_object(research_release_id, archive_object_id)
    ON DELETE RESTRICT
);

CREATE TABLE release.research_release_manifest (
  research_release_id uuid PRIMARY KEY
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  manifest_bytes bytea NOT NULL,
  manifest_sha256 core.sha256_hex NOT NULL,
  byte_length bigint NOT NULL CHECK (byte_length >= 0),
  generated_at timestamptz NOT NULL,
  CHECK (octet_length(manifest_bytes) = byte_length),
  CHECK (encode(sha256(manifest_bytes), 'hex') = manifest_sha256)
);

CREATE TABLE release.research_validation_receipt (
  research_validation_receipt_id uuid PRIMARY KEY,
  research_release_id uuid NOT NULL
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  candidate_fingerprint core.sha256_hex NOT NULL,
  verifier_version core.release_token NOT NULL,
  receipt_sha256 core.sha256_hex NOT NULL,
  validation_result release.validation_result NOT NULL,
  checked_at timestamptz NOT NULL,
  UNIQUE (research_release_id, verifier_version, receipt_sha256)
);

CREATE INDEX research_validation_receipt_result_idx
  ON release.research_validation_receipt (research_release_id, validation_result);

CREATE TABLE release.research_release_verification (
  research_release_verification_id uuid PRIMARY KEY,
  research_release_id uuid NOT NULL,
  manifest_sha256 core.sha256_hex NOT NULL,
  verifier_version core.release_token NOT NULL,
  sidecar_sha256 core.sha256_hex NOT NULL,
  verified boolean NOT NULL,
  verified_at timestamptz NOT NULL,
  FOREIGN KEY (research_release_id, manifest_sha256)
    REFERENCES release.research_release(research_release_id, manifest_sha256)
    ON DELETE RESTRICT,
  UNIQUE (research_release_id, manifest_sha256, verifier_version, sidecar_sha256)
);

CREATE TABLE release.research_current_pointer (
  channel core.release_token PRIMARY KEY,
  generation bigint NOT NULL CHECK (generation >= 0),
  research_release_id uuid,
  manifest_sha256 core.sha256_hex,
  updated_at timestamptz NOT NULL,
  CHECK ((research_release_id IS NULL) = (manifest_sha256 IS NULL)),
  FOREIGN KEY (research_release_id, manifest_sha256)
    REFERENCES release.research_release(research_release_id, manifest_sha256)
    ON DELETE RESTRICT
);

CREATE TABLE release.visual_registry_release (
  visual_registry_release_id uuid PRIMARY KEY,
  registry_version core.release_token NOT NULL UNIQUE,
  release_state release.release_state NOT NULL,
  schema_version core.release_token NOT NULL,
  model_version core.release_token NOT NULL,
  compatible_research_release_id uuid NOT NULL,
  compatible_research_manifest_sha256 core.sha256_hex NOT NULL,
  candidate_fingerprint core.sha256_hex,
  manifest_sha256 core.sha256_hex,
  created_at timestamptz NOT NULL,
  candidate_at timestamptz,
  validated_at timestamptz,
  sealed_at timestamptz,
  FOREIGN KEY (compatible_research_release_id, compatible_research_manifest_sha256)
    REFERENCES release.research_release(research_release_id, manifest_sha256)
    ON DELETE RESTRICT,
  CONSTRAINT visual_registry_state_shape CHECK (
    (release_state = 'draft' AND candidate_fingerprint IS NULL AND manifest_sha256 IS NULL
      AND candidate_at IS NULL AND validated_at IS NULL AND sealed_at IS NULL)
    OR (release_state = 'candidate' AND candidate_fingerprint IS NOT NULL AND manifest_sha256 IS NULL
      AND candidate_at IS NOT NULL AND validated_at IS NULL AND sealed_at IS NULL)
    OR (release_state = 'validated' AND candidate_fingerprint IS NOT NULL AND manifest_sha256 IS NULL
      AND candidate_at IS NOT NULL AND validated_at IS NOT NULL AND sealed_at IS NULL)
    OR (release_state = 'sealed' AND candidate_fingerprint IS NOT NULL AND manifest_sha256 IS NOT NULL
      AND candidate_at IS NOT NULL AND validated_at IS NOT NULL AND sealed_at IS NOT NULL)
  ),
  UNIQUE (visual_registry_release_id, manifest_sha256),
  UNIQUE (
    visual_registry_release_id, compatible_research_release_id,
    compatible_research_manifest_sha256
  )
);

CREATE INDEX visual_registry_state_idx
  ON release.visual_registry_release (release_state, created_at);
CREATE INDEX visual_registry_compatible_research_idx
  ON release.visual_registry_release
    (compatible_research_release_id, compatible_research_manifest_sha256, release_state);

CREATE TABLE release.visual_registry_provider_snapshot (
  visual_registry_release_id uuid NOT NULL
    REFERENCES release.visual_registry_release(visual_registry_release_id) ON DELETE RESTRICT,
  provider_id uuid NOT NULL REFERENCES rights.provider(provider_id) ON DELETE RESTRICT,
  provider_code text NOT NULL CHECK (provider_code ~ '^[a-z][a-z0-9_-]*$'),
  display_name text NOT NULL CHECK (btrim(display_name) <> ''),
  provider_snapshot_sha256 core.sha256_hex NOT NULL,
  PRIMARY KEY (visual_registry_release_id, provider_id),
  UNIQUE (visual_registry_release_id, provider_code)
);

CREATE TABLE release.visual_registry_provider_object_snapshot (
  visual_registry_release_id uuid NOT NULL,
  provider_object_id uuid NOT NULL
    REFERENCES rights.provider_object(provider_object_id) ON DELETE RESTRICT,
  provider_id uuid NOT NULL,
  provider_record_key text NOT NULL CHECK (btrim(provider_record_key) <> ''),
  provider_object_snapshot_sha256 core.sha256_hex NOT NULL,
  PRIMARY KEY (visual_registry_release_id, provider_object_id),
  FOREIGN KEY (visual_registry_release_id, provider_id)
    REFERENCES release.visual_registry_provider_snapshot
      (visual_registry_release_id, provider_id) ON DELETE RESTRICT
);

CREATE TABLE release.visual_registry_reference_snapshot (
  visual_registry_release_id uuid NOT NULL
    REFERENCES release.visual_registry_release(visual_registry_release_id) ON DELETE RESTRICT,
  external_visual_reference_id uuid NOT NULL
    REFERENCES rights.external_visual_reference(external_visual_reference_id) ON DELETE RESTRICT,
  visual_reference_urn core.canonical_urn NOT NULL,
  provider_object_id uuid,
  reference_fingerprint core.sha256_hex NOT NULL,
  reference_snapshot_sha256 core.sha256_hex NOT NULL,
  PRIMARY KEY (visual_registry_release_id, external_visual_reference_id),
  UNIQUE (visual_registry_release_id, visual_reference_urn),
  FOREIGN KEY (visual_registry_release_id, provider_object_id)
    REFERENCES release.visual_registry_provider_object_snapshot
      (visual_registry_release_id, provider_object_id) ON DELETE RESTRICT
);

CREATE TABLE release.visual_registry_bridge_snapshot (
  visual_registry_release_id uuid NOT NULL,
  compatible_research_release_id uuid NOT NULL,
  compatible_research_manifest_sha256 core.sha256_hex NOT NULL,
  object_visual_reference_id uuid NOT NULL
    REFERENCES rights.object_visual_reference(object_visual_reference_id) ON DELETE RESTRICT,
  archive_object_id uuid NOT NULL,
  external_visual_reference_id uuid NOT NULL,
  reference_role rights.reference_role NOT NULL,
  bridge_snapshot_sha256 core.sha256_hex NOT NULL,
  PRIMARY KEY (visual_registry_release_id, object_visual_reference_id),
  UNIQUE (
    visual_registry_release_id, archive_object_id,
    external_visual_reference_id, reference_role
  ),
  UNIQUE (
    visual_registry_release_id, compatible_research_release_id,
    compatible_research_manifest_sha256, object_visual_reference_id,
    archive_object_id, external_visual_reference_id, reference_role
  ),
  FOREIGN KEY (
    visual_registry_release_id, compatible_research_release_id,
    compatible_research_manifest_sha256
  ) REFERENCES release.visual_registry_release (
    visual_registry_release_id, compatible_research_release_id,
    compatible_research_manifest_sha256
  ) ON DELETE RESTRICT,
  FOREIGN KEY (compatible_research_release_id, archive_object_id)
    REFERENCES release.research_release_object
      (research_release_id, archive_object_id) ON DELETE RESTRICT,
  FOREIGN KEY (visual_registry_release_id, external_visual_reference_id)
    REFERENCES release.visual_registry_reference_snapshot
      (visual_registry_release_id, external_visual_reference_id) ON DELETE RESTRICT
);

CREATE TABLE release.visual_registry_rights_assessment_snapshot (
  visual_registry_release_id uuid NOT NULL
    REFERENCES release.visual_registry_release(visual_registry_release_id) ON DELETE RESTRICT,
  rights_assessment_id uuid NOT NULL
    REFERENCES rights.rights_assessment(rights_assessment_id) ON DELETE RESTRICT,
  assessed_state rights.rights_evidence_state NOT NULL,
  assessed_at timestamptz NOT NULL,
  assessment_snapshot_sha256 core.sha256_hex NOT NULL,
  PRIMARY KEY (visual_registry_release_id, rights_assessment_id)
);

CREATE TABLE release.visual_registry_rights_observation_snapshot (
  visual_registry_release_id uuid NOT NULL,
  rights_assessment_id uuid NOT NULL,
  rights_observation_id uuid NOT NULL
    REFERENCES rights.rights_observation(rights_observation_id) ON DELETE RESTRICT,
  evidence_role provenance.evidence_role NOT NULL,
  evidence_state rights.rights_evidence_state NOT NULL,
  evidence_item_id uuid
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  observed_at timestamptz NOT NULL,
  observation_snapshot_sha256 core.sha256_hex NOT NULL,
  PRIMARY KEY (
    visual_registry_release_id, rights_assessment_id,
    rights_observation_id, evidence_role
  ),
  FOREIGN KEY (visual_registry_release_id, rights_assessment_id)
    REFERENCES release.visual_registry_rights_assessment_snapshot
      (visual_registry_release_id, rights_assessment_id) ON DELETE RESTRICT
);

CREATE TABLE release.visual_registry_policy_version_snapshot (
  visual_registry_release_id uuid NOT NULL
    REFERENCES release.visual_registry_release(visual_registry_release_id) ON DELETE RESTRICT,
  provider_policy_version_id uuid NOT NULL
    REFERENCES rights.provider_policy_version(provider_policy_version_id) ON DELETE RESTRICT,
  provider_id uuid NOT NULL,
  version_token core.release_token NOT NULL,
  policy_sha256 core.sha256_hex NOT NULL,
  policy_state rights.policy_state NOT NULL,
  source_evidence_item_id uuid
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  effective_from timestamptz NOT NULL,
  effective_until timestamptz,
  review_due timestamptz NOT NULL,
  PRIMARY KEY (visual_registry_release_id, provider_policy_version_id),
  FOREIGN KEY (visual_registry_release_id, provider_id)
    REFERENCES release.visual_registry_provider_snapshot
      (visual_registry_release_id, provider_id) ON DELETE RESTRICT
);

CREATE TABLE release.visual_registry_policy_evaluation_snapshot (
  visual_registry_release_id uuid NOT NULL
    REFERENCES release.visual_registry_release(visual_registry_release_id) ON DELETE RESTRICT,
  provider_policy_evaluation_id uuid NOT NULL
    REFERENCES rights.provider_policy_evaluation(provider_policy_evaluation_id) ON DELETE RESTRICT,
  object_visual_reference_id uuid NOT NULL,
  evaluated_state rights.policy_state NOT NULL,
  evaluated_at timestamptz NOT NULL,
  evaluation_snapshot_sha256 core.sha256_hex NOT NULL,
  PRIMARY KEY (visual_registry_release_id, provider_policy_evaluation_id),
  FOREIGN KEY (visual_registry_release_id, object_visual_reference_id)
    REFERENCES release.visual_registry_bridge_snapshot
      (visual_registry_release_id, object_visual_reference_id) ON DELETE RESTRICT
);

CREATE TABLE release.visual_registry_policy_evaluation_version_snapshot (
  visual_registry_release_id uuid NOT NULL,
  provider_policy_evaluation_id uuid NOT NULL,
  provider_policy_version_id uuid NOT NULL,
  PRIMARY KEY (
    visual_registry_release_id, provider_policy_evaluation_id,
    provider_policy_version_id
  ),
  FOREIGN KEY (visual_registry_release_id, provider_policy_evaluation_id)
    REFERENCES release.visual_registry_policy_evaluation_snapshot
      (visual_registry_release_id, provider_policy_evaluation_id) ON DELETE RESTRICT,
  FOREIGN KEY (visual_registry_release_id, provider_policy_version_id)
    REFERENCES release.visual_registry_policy_version_snapshot
      (visual_registry_release_id, provider_policy_version_id) ON DELETE RESTRICT
);

CREATE TABLE release.visual_registry_delivery_snapshot (
  visual_registry_release_id uuid NOT NULL
    REFERENCES release.visual_registry_release(visual_registry_release_id) ON DELETE RESTRICT,
  delivery_assessment_id uuid NOT NULL
    REFERENCES rights.delivery_assessment(delivery_assessment_id) ON DELETE RESTRICT,
  object_visual_reference_id uuid NOT NULL,
  attribution_bundle_id uuid,
  base_delivery_mode rights.delivery_mode NOT NULL,
  reason_code text NOT NULL CHECK (reason_code ~ '^RD-[0-9]{3}$'),
  assessed_at timestamptz NOT NULL,
  rights_outcome_sha256 core.sha256_hex NOT NULL,
  policy_outcome_sha256 core.sha256_hex NOT NULL,
  attribution_bundle_sha256 core.sha256_hex,
  delivery_snapshot_sha256 core.sha256_hex NOT NULL,
  PRIMARY KEY (visual_registry_release_id, delivery_assessment_id),
  UNIQUE (
    visual_registry_release_id, delivery_assessment_id,
    object_visual_reference_id, base_delivery_mode, reason_code,
    rights_outcome_sha256, policy_outcome_sha256,
    attribution_bundle_sha256
  ),
  FOREIGN KEY (visual_registry_release_id, object_visual_reference_id)
    REFERENCES release.visual_registry_bridge_snapshot
      (visual_registry_release_id, object_visual_reference_id) ON DELETE RESTRICT
);

CREATE TABLE release.visual_registry_delivery_rights_snapshot (
  visual_registry_release_id uuid NOT NULL,
  delivery_assessment_id uuid NOT NULL,
  rights_assessment_id uuid NOT NULL,
  evidence_role provenance.evidence_role NOT NULL,
  PRIMARY KEY (
    visual_registry_release_id, delivery_assessment_id,
    rights_assessment_id, evidence_role
  ),
  FOREIGN KEY (visual_registry_release_id, delivery_assessment_id)
    REFERENCES release.visual_registry_delivery_snapshot
      (visual_registry_release_id, delivery_assessment_id) ON DELETE RESTRICT,
  FOREIGN KEY (visual_registry_release_id, rights_assessment_id)
    REFERENCES release.visual_registry_rights_assessment_snapshot
      (visual_registry_release_id, rights_assessment_id) ON DELETE RESTRICT
);

CREATE TABLE release.visual_registry_delivery_policy_snapshot (
  visual_registry_release_id uuid NOT NULL,
  delivery_assessment_id uuid NOT NULL,
  provider_policy_evaluation_id uuid NOT NULL,
  PRIMARY KEY (
    visual_registry_release_id, delivery_assessment_id,
    provider_policy_evaluation_id
  ),
  FOREIGN KEY (visual_registry_release_id, delivery_assessment_id)
    REFERENCES release.visual_registry_delivery_snapshot
      (visual_registry_release_id, delivery_assessment_id) ON DELETE RESTRICT,
  FOREIGN KEY (visual_registry_release_id, provider_policy_evaluation_id)
    REFERENCES release.visual_registry_policy_evaluation_snapshot
      (visual_registry_release_id, provider_policy_evaluation_id) ON DELETE RESTRICT
);

CREATE TABLE release.visual_registry_entry (
  visual_registry_release_id uuid NOT NULL
    REFERENCES release.visual_registry_release(visual_registry_release_id) ON DELETE RESTRICT,
  visual_registry_entry_id uuid NOT NULL,
  compatible_research_release_id uuid NOT NULL,
  compatible_research_manifest_sha256 core.sha256_hex NOT NULL,
  object_visual_reference_id uuid NOT NULL,
  archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  external_visual_reference_id uuid NOT NULL
    REFERENCES rights.external_visual_reference(external_visual_reference_id) ON DELETE RESTRICT,
  reference_role rights.reference_role NOT NULL,
  delivery_assessment_id uuid NOT NULL
    REFERENCES rights.delivery_assessment(delivery_assessment_id) ON DELETE RESTRICT,
  object_urn core.canonical_urn NOT NULL,
  visual_reference_urn core.canonical_urn NOT NULL,
  provider_code text,
  rights_outcome_sha256 core.sha256_hex NOT NULL,
  policy_outcome_sha256 core.sha256_hex NOT NULL,
  attribution_bundle_sha256 core.sha256_hex,
  base_delivery_mode rights.delivery_mode NOT NULL,
  reason_code text NOT NULL CHECK (reason_code ~ '^RD-[0-9]{3}$'),
  PRIMARY KEY (visual_registry_release_id, visual_registry_entry_id),
  UNIQUE (
    visual_registry_release_id, archive_object_id,
    external_visual_reference_id, reference_role
  ),
  UNIQUE (visual_registry_release_id, delivery_assessment_id),
  FOREIGN KEY (
    visual_registry_release_id, compatible_research_release_id,
    compatible_research_manifest_sha256, object_visual_reference_id,
    archive_object_id, external_visual_reference_id, reference_role
  ) REFERENCES release.visual_registry_bridge_snapshot (
    visual_registry_release_id, compatible_research_release_id,
    compatible_research_manifest_sha256, object_visual_reference_id,
    archive_object_id, external_visual_reference_id, reference_role
  ) ON DELETE RESTRICT,
  FOREIGN KEY (
    visual_registry_release_id, delivery_assessment_id,
    object_visual_reference_id, base_delivery_mode, reason_code,
    rights_outcome_sha256, policy_outcome_sha256,
    attribution_bundle_sha256
  ) REFERENCES release.visual_registry_delivery_snapshot (
    visual_registry_release_id, delivery_assessment_id,
    object_visual_reference_id, base_delivery_mode, reason_code,
    rights_outcome_sha256, policy_outcome_sha256,
    attribution_bundle_sha256
  ) ON DELETE RESTRICT,
  FOREIGN KEY (visual_registry_release_id, delivery_assessment_id)
    REFERENCES release.visual_registry_delivery_snapshot
      (visual_registry_release_id, delivery_assessment_id) ON DELETE RESTRICT
);

CREATE INDEX visual_registry_entry_object_idx
  ON release.visual_registry_entry (visual_registry_release_id, archive_object_id);
CREATE INDEX visual_registry_entry_reference_idx
  ON release.visual_registry_entry (external_visual_reference_id, visual_registry_release_id);

CREATE TABLE release.visual_registry_attribution_value (
  visual_registry_release_id uuid NOT NULL,
  visual_registry_entry_id uuid NOT NULL,
  value_kind text NOT NULL CHECK (value_kind IN ('attribution', 'required_statement')),
  value_ordinal integer NOT NULL CHECK (value_ordinal >= 0),
  language_tag text,
  value_text text NOT NULL CHECK (btrim(value_text) <> ''),
  PRIMARY KEY (
    visual_registry_release_id, visual_registry_entry_id,
    value_kind, value_ordinal
  ),
  FOREIGN KEY (visual_registry_release_id, visual_registry_entry_id)
    REFERENCES release.visual_registry_entry
      (visual_registry_release_id, visual_registry_entry_id) ON DELETE RESTRICT
);

CREATE TABLE release.visual_registry_public_locator (
  visual_registry_release_id uuid NOT NULL,
  visual_registry_entry_id uuid NOT NULL,
  visual_locator_id uuid NOT NULL
    REFERENCES rights.visual_locator(visual_locator_id) ON DELETE RESTRICT,
  locator_role rights.locator_role NOT NULL CHECK (
    locator_role IN ('canonical_record', 'source_viewer', 'direct_image')
  ),
  locator_ordinal integer NOT NULL CHECK (locator_ordinal >= 0),
  public_locator text NOT NULL CHECK (public_locator ~ '^https://'),
  locator_sha256 core.sha256_hex NOT NULL,
  endpoint_health_observation_id uuid NOT NULL
    REFERENCES rights.endpoint_health_observation(endpoint_health_observation_id) ON DELETE RESTRICT,
  health_state rights.health_state NOT NULL,
  health_method_version core.release_token NOT NULL,
  health_observed_at timestamptz NOT NULL,
  health_valid_until timestamptz NOT NULL,
  health_observation_sha256 core.sha256_hex NOT NULL,
  PRIMARY KEY (
    visual_registry_release_id, visual_registry_entry_id,
    locator_role, locator_ordinal
  ),
  FOREIGN KEY (visual_registry_release_id, visual_registry_entry_id)
    REFERENCES release.visual_registry_entry
      (visual_registry_release_id, visual_registry_entry_id) ON DELETE RESTRICT,
  CHECK (health_valid_until IS NULL OR health_valid_until > health_observed_at)
);

CREATE INDEX visual_registry_public_locator_source_idx
  ON release.visual_registry_public_locator
    (visual_locator_id, endpoint_health_observation_id);

CREATE TABLE release.visual_registry_takedown_snapshot (
  visual_registry_release_id uuid NOT NULL,
  visual_registry_entry_id uuid NOT NULL,
  takedown_override_id uuid NOT NULL
    REFERENCES rights.takedown_override(takedown_override_id) ON DELETE RESTRICT,
  restrictive_mode rights.delivery_mode NOT NULL
    CHECK (restrictive_mode IN ('blocked', 'citation_only')),
  overlay_sha256 core.sha256_hex NOT NULL,
  effective_from timestamptz NOT NULL,
  effective_until timestamptz,
  evaluated_at timestamptz NOT NULL,
  PRIMARY KEY (
    visual_registry_release_id, visual_registry_entry_id,
    takedown_override_id
  ),
  FOREIGN KEY (visual_registry_release_id, visual_registry_entry_id)
    REFERENCES release.visual_registry_entry
      (visual_registry_release_id, visual_registry_entry_id) ON DELETE RESTRICT,
  CHECK (effective_until IS NULL OR effective_until > effective_from)
);

CREATE TABLE release.visual_registry_manifest (
  visual_registry_release_id uuid PRIMARY KEY
    REFERENCES release.visual_registry_release(visual_registry_release_id) ON DELETE RESTRICT,
  manifest_bytes bytea NOT NULL,
  manifest_sha256 core.sha256_hex NOT NULL,
  byte_length bigint NOT NULL CHECK (byte_length >= 0),
  generated_at timestamptz NOT NULL,
  CHECK (octet_length(manifest_bytes) = byte_length),
  CHECK (encode(sha256(manifest_bytes), 'hex') = manifest_sha256)
);

CREATE TABLE release.visual_validation_receipt (
  visual_validation_receipt_id uuid PRIMARY KEY,
  visual_registry_release_id uuid NOT NULL
    REFERENCES release.visual_registry_release(visual_registry_release_id) ON DELETE RESTRICT,
  candidate_fingerprint core.sha256_hex NOT NULL,
  verifier_version core.release_token NOT NULL,
  receipt_sha256 core.sha256_hex NOT NULL,
  validation_result release.validation_result NOT NULL,
  checked_at timestamptz NOT NULL,
  UNIQUE (visual_registry_release_id, verifier_version, receipt_sha256)
);

CREATE INDEX visual_validation_receipt_result_idx
  ON release.visual_validation_receipt (visual_registry_release_id, validation_result);

CREATE TABLE release.visual_registry_verification (
  visual_registry_verification_id uuid PRIMARY KEY,
  visual_registry_release_id uuid NOT NULL,
  manifest_sha256 core.sha256_hex NOT NULL,
  verifier_version core.release_token NOT NULL,
  sidecar_sha256 core.sha256_hex NOT NULL,
  verified boolean NOT NULL,
  verified_at timestamptz NOT NULL,
  FOREIGN KEY (visual_registry_release_id, manifest_sha256)
    REFERENCES release.visual_registry_release(visual_registry_release_id, manifest_sha256)
    ON DELETE RESTRICT,
  UNIQUE (visual_registry_release_id, manifest_sha256, verifier_version, sidecar_sha256)
);

CREATE TABLE release.visual_current_pointer (
  channel core.release_token PRIMARY KEY,
  generation bigint NOT NULL CHECK (generation >= 0),
  visual_registry_release_id uuid,
  manifest_sha256 core.sha256_hex,
  updated_at timestamptz NOT NULL,
  CHECK ((visual_registry_release_id IS NULL) = (manifest_sha256 IS NULL)),
  FOREIGN KEY (visual_registry_release_id, manifest_sha256)
    REFERENCES release.visual_registry_release(visual_registry_release_id, manifest_sha256)
    ON DELETE RESTRICT
);

CREATE TABLE release.public_channel (
  channel core.release_token PRIMARY KEY,
  public_contract_version core.release_token NOT NULL,
  created_at timestamptz NOT NULL
);

CREATE TABLE release.research_publication_history (
  channel core.release_token NOT NULL
    REFERENCES release.public_channel(channel) ON DELETE RESTRICT,
  research_release_id uuid NOT NULL,
  manifest_sha256 core.sha256_hex NOT NULL,
  promoted_generation bigint NOT NULL CHECK (promoted_generation > 0),
  published_at timestamptz NOT NULL,
  PRIMARY KEY (channel, promoted_generation),
  FOREIGN KEY (research_release_id, manifest_sha256)
    REFERENCES release.research_release(research_release_id, manifest_sha256)
    ON DELETE RESTRICT
);

CREATE INDEX research_publication_history_release_idx
  ON release.research_publication_history
    (research_release_id, manifest_sha256, published_at DESC);

CREATE TABLE release.visual_publication_history (
  channel core.release_token NOT NULL
    REFERENCES release.public_channel(channel) ON DELETE RESTRICT,
  visual_registry_release_id uuid NOT NULL,
  manifest_sha256 core.sha256_hex NOT NULL,
  promoted_generation bigint NOT NULL CHECK (promoted_generation > 0),
  published_at timestamptz NOT NULL,
  PRIMARY KEY (channel, promoted_generation),
  FOREIGN KEY (visual_registry_release_id, manifest_sha256)
    REFERENCES release.visual_registry_release(
      visual_registry_release_id, manifest_sha256) ON DELETE RESTRICT
);


CREATE INDEX visual_publication_history_release_idx
  ON release.visual_publication_history
    (visual_registry_release_id, manifest_sha256, published_at DESC);

CREATE TABLE release.visual_health_sidecar_event (
  visual_health_sidecar_event_id uuid PRIMARY KEY,
  visual_registry_release_id uuid NOT NULL,
  visual_registry_entry_id uuid NOT NULL,
  visual_locator_id uuid NOT NULL
    REFERENCES rights.visual_locator(visual_locator_id) ON DELETE RESTRICT,
  endpoint_health_observation_id uuid NOT NULL
    REFERENCES rights.endpoint_health_observation(endpoint_health_observation_id) ON DELETE RESTRICT,
  locator_role rights.locator_role NOT NULL,
  health_state rights.health_state NOT NULL,
  observed_at timestamptz NOT NULL,
  valid_until timestamptz,
  observation_sha256 core.sha256_hex NOT NULL,
  FOREIGN KEY (visual_registry_release_id, visual_registry_entry_id)
    REFERENCES release.visual_registry_entry
      (visual_registry_release_id, visual_registry_entry_id) ON DELETE RESTRICT,
  CHECK (valid_until IS NULL OR valid_until > observed_at)
);

CREATE INDEX visual_health_sidecar_latest_idx
  ON release.visual_health_sidecar_event
    (visual_registry_release_id, visual_registry_entry_id, locator_role, observed_at DESC);

CREATE TABLE release.visual_takedown_sidecar_event (
  visual_takedown_sidecar_event_id uuid PRIMARY KEY,
  visual_registry_release_id uuid NOT NULL,
  visual_registry_entry_id uuid NOT NULL,
  takedown_override_id uuid NOT NULL
    REFERENCES rights.takedown_override(takedown_override_id) ON DELETE RESTRICT,
  restrictive_mode rights.delivery_mode NOT NULL
    CHECK (restrictive_mode IN ('blocked', 'citation_only')),
  overlay_sha256 core.sha256_hex NOT NULL,
  effective_from timestamptz NOT NULL,
  effective_until timestamptz,
  recorded_at timestamptz NOT NULL,
  FOREIGN KEY (visual_registry_release_id, visual_registry_entry_id)
    REFERENCES release.visual_registry_entry
      (visual_registry_release_id, visual_registry_entry_id) ON DELETE RESTRICT,
  CHECK (effective_until IS NULL OR effective_until > effective_from)
);

CREATE INDEX visual_takedown_sidecar_effective_idx
  ON release.visual_takedown_sidecar_event
    (visual_registry_release_id, visual_registry_entry_id, effective_from DESC);

CREATE TABLE audit.review_event (
  review_event_id uuid PRIMARY KEY,
  relation_review_decision_id uuid NOT NULL
    REFERENCES research.relation_review_decision(relation_review_decision_id) ON DELETE RESTRICT,
  actor text NOT NULL CHECK (btrim(actor) <> ''),
  occurred_at timestamptz NOT NULL,
  event_sha256 core.sha256_hex NOT NULL,
  UNIQUE (relation_review_decision_id, event_sha256)
);

CREATE TABLE audit.decision_event (
  decision_event_id uuid PRIMARY KEY,
  decision_kind audit.decision_kind NOT NULL,
  actor text NOT NULL CHECK (btrim(actor) <> ''),
  occurred_at timestamptz NOT NULL,
  event_sha256 core.sha256_hex NOT NULL
);

CREATE TABLE audit.decision_event_claim_review (
  decision_event_id uuid PRIMARY KEY
    REFERENCES audit.decision_event(decision_event_id) ON DELETE RESTRICT,
  claim_review_decision_id uuid NOT NULL UNIQUE
    REFERENCES research.claim_review_decision(claim_review_decision_id) ON DELETE RESTRICT
);

CREATE TABLE audit.decision_event_assertion_review (
  decision_event_id uuid PRIMARY KEY
    REFERENCES audit.decision_event(decision_event_id) ON DELETE RESTRICT,
  assertion_review_decision_id uuid NOT NULL UNIQUE
    REFERENCES provenance.assertion_review_decision(assertion_review_decision_id)
    ON DELETE RESTRICT
);

CREATE TABLE audit.decision_event_assignment_review (
  decision_event_id uuid PRIMARY KEY
    REFERENCES audit.decision_event(decision_event_id) ON DELETE RESTRICT,
  assignment_review_decision_id uuid NOT NULL UNIQUE
    REFERENCES provenance.assignment_review_decision(assignment_review_decision_id)
    ON DELETE RESTRICT
);

CREATE TABLE audit.decision_event_relation_review (
  decision_event_id uuid PRIMARY KEY
    REFERENCES audit.decision_event(decision_event_id) ON DELETE RESTRICT,
  relation_review_decision_id uuid NOT NULL UNIQUE
    REFERENCES research.relation_review_decision(relation_review_decision_id) ON DELETE RESTRICT
);

CREATE TABLE audit.decision_event_rights_observation (
  decision_event_id uuid PRIMARY KEY
    REFERENCES audit.decision_event(decision_event_id) ON DELETE RESTRICT,
  rights_observation_id uuid NOT NULL UNIQUE
    REFERENCES rights.rights_observation(rights_observation_id) ON DELETE RESTRICT
);

CREATE TABLE audit.decision_event_rights_assessment (
  decision_event_id uuid PRIMARY KEY
    REFERENCES audit.decision_event(decision_event_id) ON DELETE RESTRICT,
  rights_assessment_id uuid NOT NULL UNIQUE
    REFERENCES rights.rights_assessment(rights_assessment_id) ON DELETE RESTRICT
);

CREATE TABLE audit.decision_event_policy_evaluation (
  decision_event_id uuid PRIMARY KEY
    REFERENCES audit.decision_event(decision_event_id) ON DELETE RESTRICT,
  provider_policy_evaluation_id uuid NOT NULL UNIQUE
    REFERENCES rights.provider_policy_evaluation(provider_policy_evaluation_id) ON DELETE RESTRICT
);

CREATE TABLE audit.decision_event_delivery_assessment (
  decision_event_id uuid PRIMARY KEY
    REFERENCES audit.decision_event(decision_event_id) ON DELETE RESTRICT,
  delivery_assessment_id uuid NOT NULL UNIQUE
    REFERENCES rights.delivery_assessment(delivery_assessment_id) ON DELETE RESTRICT
);

CREATE TABLE audit.decision_event_attribution_validation (
  decision_event_id uuid PRIMARY KEY
    REFERENCES audit.decision_event(decision_event_id) ON DELETE RESTRICT,
  attribution_bundle_id uuid NOT NULL UNIQUE
    REFERENCES rights.attribution_bundle(attribution_bundle_id) ON DELETE RESTRICT
);

CREATE TABLE audit.decision_event_takedown (
  decision_event_id uuid PRIMARY KEY
    REFERENCES audit.decision_event(decision_event_id) ON DELETE RESTRICT,
  takedown_event_id uuid NOT NULL UNIQUE
    REFERENCES rights.takedown_event(takedown_event_id) ON DELETE RESTRICT
);

CREATE TABLE audit.research_release_event (
  research_release_event_id uuid PRIMARY KEY,
  research_release_id uuid NOT NULL
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  from_state release.release_state,
  to_state release.release_state NOT NULL,
  actor text NOT NULL CHECK (btrim(actor) <> ''),
  occurred_at timestamptz NOT NULL,
  event_sha256 core.sha256_hex NOT NULL
);

CREATE INDEX research_release_event_release_idx
  ON audit.research_release_event (research_release_id, occurred_at);

CREATE TABLE audit.visual_release_event (
  visual_release_event_id uuid PRIMARY KEY,
  visual_registry_release_id uuid NOT NULL
    REFERENCES release.visual_registry_release(visual_registry_release_id) ON DELETE RESTRICT,
  from_state release.release_state,
  to_state release.release_state NOT NULL,
  actor text NOT NULL CHECK (btrim(actor) <> ''),
  occurred_at timestamptz NOT NULL,
  event_sha256 core.sha256_hex NOT NULL
);

CREATE INDEX visual_release_event_release_idx
  ON audit.visual_release_event (visual_registry_release_id, occurred_at);

CREATE TABLE audit.research_seal_event (
  research_seal_event_id uuid PRIMARY KEY,
  research_release_id uuid NOT NULL,
  manifest_sha256 core.sha256_hex NOT NULL,
  actor text NOT NULL CHECK (btrim(actor) <> ''),
  sealed_at timestamptz NOT NULL,
  FOREIGN KEY (research_release_id, manifest_sha256)
    REFERENCES release.research_release(research_release_id, manifest_sha256) ON DELETE RESTRICT,
  UNIQUE (research_release_id)
);

CREATE TABLE audit.visual_seal_event (
  visual_seal_event_id uuid PRIMARY KEY,
  visual_registry_release_id uuid NOT NULL,
  manifest_sha256 core.sha256_hex NOT NULL,
  actor text NOT NULL CHECK (btrim(actor) <> ''),
  sealed_at timestamptz NOT NULL,
  FOREIGN KEY (visual_registry_release_id, manifest_sha256)
    REFERENCES release.visual_registry_release(visual_registry_release_id, manifest_sha256)
    ON DELETE RESTRICT,
  UNIQUE (visual_registry_release_id)
);

CREATE TABLE audit.research_cas_attempt (
  research_cas_attempt_id uuid PRIMARY KEY,
  channel core.release_token NOT NULL,
  expected_generation bigint NOT NULL,
  observed_generation bigint NOT NULL,
  target_research_release_id uuid
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  succeeded boolean NOT NULL,
  reason_code text NOT NULL CHECK (btrim(reason_code) <> ''),
  actor text NOT NULL CHECK (btrim(actor) <> ''),
  attempted_at timestamptz NOT NULL
);

CREATE INDEX research_cas_attempt_channel_idx
  ON audit.research_cas_attempt (channel, attempted_at DESC);

CREATE TABLE audit.visual_cas_attempt (
  visual_cas_attempt_id uuid PRIMARY KEY,
  channel core.release_token NOT NULL,
  expected_generation bigint NOT NULL,
  observed_generation bigint NOT NULL,
  target_visual_registry_release_id uuid
    REFERENCES release.visual_registry_release(visual_registry_release_id) ON DELETE RESTRICT,
  guarded_research_release_id uuid
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  succeeded boolean NOT NULL,
  reason_code text NOT NULL CHECK (btrim(reason_code) <> ''),
  actor text NOT NULL CHECK (btrim(actor) <> ''),
  attempted_at timestamptz NOT NULL
);

CREATE INDEX visual_cas_attempt_channel_idx
  ON audit.visual_cas_attempt (channel, attempted_at DESC);

CREATE TABLE audit.verification_receipt_event (
  verification_receipt_event_id uuid PRIMARY KEY,
  research_release_verification_id uuid
    REFERENCES release.research_release_verification(research_release_verification_id) ON DELETE RESTRICT,
  visual_registry_verification_id uuid
    REFERENCES release.visual_registry_verification(visual_registry_verification_id) ON DELETE RESTRICT,
  receipt_sha256 core.sha256_hex NOT NULL,
  actor text NOT NULL CHECK (btrim(actor) <> ''),
  occurred_at timestamptz NOT NULL,
  CHECK (num_nonnulls(research_release_verification_id, visual_registry_verification_id) = 1)
);

CREATE TABLE audit.sidecar_event (
  sidecar_event_id uuid PRIMARY KEY,
  visual_health_sidecar_event_id uuid
    REFERENCES release.visual_health_sidecar_event(visual_health_sidecar_event_id) ON DELETE RESTRICT,
  visual_takedown_sidecar_event_id uuid
    REFERENCES release.visual_takedown_sidecar_event(visual_takedown_sidecar_event_id) ON DELETE RESTRICT,
  event_sha256 core.sha256_hex NOT NULL,
  actor text NOT NULL CHECK (btrim(actor) <> ''),
  occurred_at timestamptz NOT NULL,
  CHECK (num_nonnulls(visual_health_sidecar_event_id, visual_takedown_sidecar_event_id) = 1)
);

RESET ROLE;
