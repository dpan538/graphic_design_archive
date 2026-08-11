\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

CREATE TABLE research.corpus (
  corpus_id uuid PRIMARY KEY,
  corpus_token core.release_token NOT NULL UNIQUE,
  label text NOT NULL CHECK (btrim(label) <> ''),
  created_at timestamptz NOT NULL
);

CREATE TABLE research.folder (
  folder_id uuid PRIMARY KEY,
  folder_token core.release_token NOT NULL UNIQUE,
  label text NOT NULL CHECK (btrim(label) <> ''),
  created_at timestamptz NOT NULL
);

ALTER TABLE provenance.assignment_folder_membership
  ADD CONSTRAINT assignment_folder_membership_folder_fk
  FOREIGN KEY (folder_id) REFERENCES research.folder(folder_id) ON DELETE RESTRICT;

CREATE TABLE research.corpus_version (
  corpus_version_id uuid PRIMARY KEY,
  corpus_id uuid NOT NULL REFERENCES research.corpus(corpus_id) ON DELETE RESTRICT,
  version_token core.release_token NOT NULL,
  policy_version core.release_token NOT NULL,
  policy_sha256 core.sha256_hex NOT NULL,
  population_frame text NOT NULL CHECK (btrim(population_frame) <> ''),
  created_at timestamptz NOT NULL,
  UNIQUE (corpus_id, version_token),
  UNIQUE (corpus_id, policy_sha256)
);

CREATE INDEX corpus_version_policy_idx ON research.corpus_version (policy_version, policy_sha256);

CREATE TABLE research.corpus_membership (
  corpus_version_id uuid NOT NULL
    REFERENCES research.corpus_version(corpus_version_id) ON DELETE RESTRICT,
  archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  disposition research.membership_disposition NOT NULL,
  reason_code text NOT NULL CHECK (btrim(reason_code) <> ''),
  evidence_item_id uuid
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  decided_by text NOT NULL CHECK (btrim(decided_by) <> ''),
  decided_at timestamptz NOT NULL,
  PRIMARY KEY (corpus_version_id, archive_object_id)
);

CREATE INDEX corpus_membership_queue_idx
  ON research.corpus_membership (corpus_version_id, disposition, archive_object_id);
CREATE INDEX corpus_membership_object_idx
  ON research.corpus_membership (archive_object_id, corpus_version_id);

CREATE TABLE research.missingness_snapshot (
  missingness_snapshot_id uuid PRIMARY KEY,
  corpus_version_id uuid NOT NULL
    REFERENCES research.corpus_version(corpus_version_id) ON DELETE RESTRICT,
  snapshot_token core.release_token NOT NULL,
  input_sha256 core.sha256_hex NOT NULL,
  method_version core.release_token NOT NULL,
  denominator_unit text NOT NULL CHECK (btrim(denominator_unit) <> ''),
  denominator_count bigint NOT NULL CHECK (denominator_count >= 0),
  generated_at timestamptz NOT NULL,
  UNIQUE (corpus_version_id, snapshot_token)
);

CREATE TABLE research.missingness_observation (
  missingness_snapshot_id uuid NOT NULL
    REFERENCES research.missingness_snapshot(missingness_snapshot_id) ON DELETE RESTRICT,
  reason_code text NOT NULL CHECK (btrim(reason_code) <> ''),
  unit text NOT NULL CHECK (btrim(unit) <> ''),
  observed_count bigint NOT NULL CHECK (observed_count >= 0),
  confidence_note text,
  PRIMARY KEY (missingness_snapshot_id, reason_code, unit)
);

CREATE TABLE research.coverage_snapshot (
  coverage_snapshot_id uuid PRIMARY KEY,
  corpus_version_id uuid NOT NULL
    REFERENCES research.corpus_version(corpus_version_id) ON DELETE RESTRICT,
  snapshot_token core.release_token NOT NULL,
  input_sha256 core.sha256_hex NOT NULL,
  method_version core.release_token NOT NULL,
  unit text NOT NULL CHECK (btrim(unit) <> ''),
  numerator_count bigint NOT NULL CHECK (numerator_count >= 0),
  denominator_count bigint NOT NULL CHECK (denominator_count >= 0),
  generated_at timestamptz NOT NULL,
  CHECK (numerator_count <= denominator_count),
  UNIQUE (corpus_version_id, snapshot_token, unit)
);

CREATE TABLE research.epistemic_class (
  epistemic_class_id uuid PRIMARY KEY,
  class_code text NOT NULL UNIQUE CHECK (class_code IN (
    'documented_source_statement', 'scholarly_claim', 'computed_association', 'causal_interpretation'
  )),
  active boolean NOT NULL,
  requires_analysis_run boolean NOT NULL,
  requires_claimant_source boolean NOT NULL,
  description text NOT NULL CHECK (btrim(description) <> '')
);

CREATE TABLE research.claim (
  claim_id uuid PRIMARY KEY,
  claim_urn core.canonical_urn GENERATED ALWAYS AS
    (('urn:gdarchive:claim:'::text || claim_id::text)::core.canonical_urn) STORED,
  created_at timestamptz NOT NULL,
  UNIQUE (claim_urn)
);

CREATE TABLE research.analysis_run (
  analysis_run_id uuid PRIMARY KEY,
  method_version core.release_token NOT NULL,
  parameters_sha256 core.sha256_hex NOT NULL,
  input_release_id uuid,
  input_manifest_sha256 core.sha256_hex NOT NULL,
  output_sha256 core.sha256_hex NOT NULL,
  executed_at timestamptz NOT NULL,
  UNIQUE (method_version, parameters_sha256, input_manifest_sha256, output_sha256)
);

CREATE TABLE research.claim_revision (
  claim_revision_id uuid PRIMARY KEY,
  claim_id uuid NOT NULL REFERENCES research.claim(claim_id) ON DELETE RESTRICT,
  revision_number integer NOT NULL CHECK (revision_number > 0),
  epistemic_class_id uuid NOT NULL
    REFERENCES research.epistemic_class(epistemic_class_id) ON DELETE RESTRICT,
  status research.claim_status NOT NULL,
  workflow_state workflow.queue_state NOT NULL,
  claimant_agent_id uuid REFERENCES core.agent(agent_id) ON DELETE RESTRICT,
  wording text NOT NULL CHECK (btrim(wording) <> ''),
  temporal_qualifier_id uuid
    REFERENCES core.temporal_extent(temporal_extent_id) ON DELETE RESTRICT,
  spatial_qualifier_id uuid REFERENCES core.place(place_id) ON DELETE RESTRICT,
  analysis_run_id uuid REFERENCES research.analysis_run(analysis_run_id) ON DELETE RESTRICT,
  supersedes_claim_revision_id uuid
    REFERENCES research.claim_revision(claim_revision_id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL,
  UNIQUE (claim_id, revision_number),
  UNIQUE (claim_id, claim_revision_id)
);

CREATE INDEX claim_revision_status_idx
  ON research.claim_revision (status, epistemic_class_id, claimant_agent_id);
CREATE INDEX claim_revision_supersedes_idx
  ON research.claim_revision (supersedes_claim_revision_id);

CREATE TABLE research.claim_review_decision (
  claim_review_decision_id uuid PRIMARY KEY,
  claim_revision_id uuid NOT NULL
    REFERENCES research.claim_revision(claim_revision_id) ON DELETE RESTRICT,
  outcome workflow.review_outcome NOT NULL,
  heightened_review boolean NOT NULL,
  reviewer_actor text NOT NULL CHECK (btrim(reviewer_actor) <> ''),
  rationale text NOT NULL CHECK (btrim(rationale) <> ''),
  supersedes_decision_id uuid
    REFERENCES research.claim_review_decision(claim_review_decision_id) ON DELETE RESTRICT,
  decided_at timestamptz NOT NULL,
  UNIQUE (supersedes_decision_id)
);

CREATE TABLE research.claim_decision_evidence (
  claim_review_decision_id uuid NOT NULL
    REFERENCES research.claim_review_decision(claim_review_decision_id) ON DELETE RESTRICT,
  evidence_item_id uuid NOT NULL
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  evidence_role provenance.evidence_role NOT NULL,
  PRIMARY KEY (claim_review_decision_id, evidence_item_id, evidence_role)
);

CREATE TABLE research.claim_evidence (
  claim_revision_id uuid NOT NULL
    REFERENCES research.claim_revision(claim_revision_id) ON DELETE RESTRICT,
  evidence_item_id uuid NOT NULL
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  evidence_role provenance.evidence_role NOT NULL,
  PRIMARY KEY (claim_revision_id, evidence_item_id, evidence_role)
);

CREATE INDEX claim_evidence_evidence_idx
  ON research.claim_evidence (evidence_item_id, claim_revision_id);

CREATE TABLE research.relation_type (
  relation_type_id uuid PRIMARY KEY,
  relation_code text NOT NULL UNIQUE CHECK (relation_code ~ '^[a-z][a-z0-9_]*$'),
  active boolean NOT NULL,
  subject_entity_kind core.entity_kind NOT NULL,
  object_entity_kind core.entity_kind NOT NULL,
  evidence_required boolean NOT NULL,
  evidence_profile_version core.release_token NOT NULL,
  implicit_transitivity boolean NOT NULL CHECK (implicit_transitivity = false),
  automatic_influence_inference boolean NOT NULL CHECK (automatic_influence_inference = false),
  description text NOT NULL CHECK (btrim(description) <> '')
);

CREATE TABLE research.relation_endpoint (
  relation_endpoint_id uuid PRIMARY KEY,
  endpoint_kind research.relation_endpoint_kind NOT NULL
);

CREATE TABLE research.relation_endpoint_entity (
  relation_endpoint_id uuid PRIMARY KEY
    REFERENCES research.relation_endpoint(relation_endpoint_id) ON DELETE RESTRICT,
  entity_id uuid NOT NULL REFERENCES core.entity(entity_id) ON DELETE RESTRICT,
  UNIQUE (entity_id)
);

CREATE TABLE research.semantic_relation (
  semantic_relation_id uuid PRIMARY KEY,
  relation_urn core.canonical_urn GENERATED ALWAYS AS
    (('urn:gdarchive:relation:'::text || semantic_relation_id::text)::core.canonical_urn) STORED,
  subject_endpoint_id uuid NOT NULL
    REFERENCES research.relation_endpoint(relation_endpoint_id) ON DELETE RESTRICT,
  relation_type_id uuid NOT NULL
    REFERENCES research.relation_type(relation_type_id) ON DELETE RESTRICT,
  object_endpoint_id uuid NOT NULL
    REFERENCES research.relation_endpoint(relation_endpoint_id) ON DELETE RESTRICT,
  origin research.relation_origin NOT NULL,
  status research.relation_status NOT NULL,
  temporal_qualifier_id uuid
    REFERENCES core.temporal_extent(temporal_extent_id) ON DELETE RESTRICT,
  spatial_qualifier_id uuid REFERENCES core.place(place_id) ON DELETE RESTRICT,
  supersedes_semantic_relation_id uuid
    REFERENCES research.semantic_relation(semantic_relation_id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL,
  CHECK (subject_endpoint_id <> object_endpoint_id),
  UNIQUE (relation_urn)
);

CREATE INDEX semantic_relation_subject_status_idx
  ON research.semantic_relation (subject_endpoint_id, relation_type_id, status);
CREATE INDEX semantic_relation_object_status_idx
  ON research.semantic_relation (object_endpoint_id, relation_type_id, status);
CREATE INDEX semantic_relation_supersedes_idx
  ON research.semantic_relation (supersedes_semantic_relation_id);
CREATE UNIQUE INDEX semantic_relation_current_natural_uidx
  ON research.semantic_relation
    (subject_endpoint_id, relation_type_id, object_endpoint_id)
  WHERE status <> 'superseded';

CREATE TABLE research.relation_context_evidence (
  semantic_relation_id uuid NOT NULL
    REFERENCES research.semantic_relation(semantic_relation_id) ON DELETE RESTRICT,
  evidence_item_id uuid NOT NULL
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  evidence_role provenance.evidence_role NOT NULL,
  PRIMARY KEY (semantic_relation_id, evidence_item_id, evidence_role)
);

CREATE INDEX relation_context_evidence_evidence_idx
  ON research.relation_context_evidence (evidence_item_id, semantic_relation_id);

CREATE TABLE research.relation_claim (
  semantic_relation_id uuid NOT NULL
    REFERENCES research.semantic_relation(semantic_relation_id) ON DELETE RESTRICT,
  claim_id uuid NOT NULL REFERENCES research.claim(claim_id) ON DELETE RESTRICT,
  claim_revision_id uuid NOT NULL
    REFERENCES research.claim_revision(claim_revision_id) ON DELETE RESTRICT,
  claim_role research.claim_relation_role NOT NULL,
  PRIMARY KEY (semantic_relation_id, claim_id, claim_role),
  FOREIGN KEY (claim_id, claim_revision_id)
    REFERENCES research.claim_revision(claim_id, claim_revision_id) ON DELETE RESTRICT
);

CREATE INDEX relation_claim_claim_idx
  ON research.relation_claim (claim_revision_id, semantic_relation_id);

CREATE TABLE research.relation_review_decision (
  relation_review_decision_id uuid PRIMARY KEY,
  semantic_relation_id uuid NOT NULL
    REFERENCES research.semantic_relation(semantic_relation_id) ON DELETE RESTRICT,
  outcome workflow.review_outcome NOT NULL,
  reviewer_actor text NOT NULL CHECK (btrim(reviewer_actor) <> ''),
  reviewer_agent_id uuid REFERENCES core.agent(agent_id) ON DELETE RESTRICT,
  rationale text NOT NULL CHECK (btrim(rationale) <> ''),
  supersedes_decision_id uuid
    REFERENCES research.relation_review_decision(relation_review_decision_id) ON DELETE RESTRICT,
  decided_at timestamptz NOT NULL,
  UNIQUE (supersedes_decision_id)
);

CREATE INDEX relation_review_effective_idx
  ON research.relation_review_decision (semantic_relation_id, decided_at DESC);

CREATE TABLE research.relation_decision_evidence (
  relation_review_decision_id uuid NOT NULL
    REFERENCES research.relation_review_decision(relation_review_decision_id) ON DELETE RESTRICT,
  evidence_item_id uuid NOT NULL
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  evidence_role provenance.evidence_role NOT NULL,
  PRIMARY KEY (relation_review_decision_id, evidence_item_id, evidence_role)
);

CREATE INDEX relation_decision_evidence_reverse_idx
  ON research.relation_decision_evidence (evidence_item_id, relation_review_decision_id);

CREATE TABLE workflow.relation_type_review_queue (
  relation_type_review_queue_id uuid PRIMARY KEY,
  field_literal_id uuid NOT NULL
    REFERENCES raw.field_literal(field_literal_id) ON DELETE RESTRICT,
  source_label_literal text NOT NULL CHECK (btrim(source_label_literal) <> ''),
  queue_state workflow.queue_state NOT NULL CHECK (queue_state IN ('queued', 'claimed', 'in_review', 'superseded')),
  reason_code text NOT NULL CHECK (btrim(reason_code) <> ''),
  created_at timestamptz NOT NULL,
  UNIQUE (field_literal_id)
);

CREATE INDEX relation_type_review_queue_state_idx
  ON workflow.relation_type_review_queue (queue_state, created_at);

CREATE TABLE workflow.review_case (
  review_case_id uuid PRIMARY KEY,
  case_kind workflow.case_kind NOT NULL,
  queue_state workflow.queue_state NOT NULL,
  priority smallint NOT NULL DEFAULT 0 CHECK (priority BETWEEN 0 AND 100),
  reason_code text NOT NULL CHECK (reason_code ~ '^[A-Z][A-Z0-9_]*$'),
  claimed_by text,
  claimed_at timestamptz,
  created_at timestamptz NOT NULL,
  resolved_at timestamptz,
  CHECK ((queue_state IN ('claimed', 'in_review')) =
    (claimed_by IS NOT NULL AND claimed_at IS NOT NULL)),
  CHECK ((queue_state = 'resolved') = (resolved_at IS NOT NULL))
);

CREATE TABLE workflow.review_case_assertion (
  review_case_id uuid PRIMARY KEY
    REFERENCES workflow.review_case(review_case_id) ON DELETE RESTRICT,
  assertion_id uuid NOT NULL UNIQUE
    REFERENCES provenance.assertion(assertion_id) ON DELETE RESTRICT
);

CREATE TABLE workflow.review_case_assignment (
  review_case_id uuid PRIMARY KEY
    REFERENCES workflow.review_case(review_case_id) ON DELETE RESTRICT,
  canonical_assignment_id uuid NOT NULL UNIQUE
    REFERENCES provenance.canonical_assignment(canonical_assignment_id) ON DELETE RESTRICT
);

CREATE TABLE workflow.review_case_claim (
  review_case_id uuid PRIMARY KEY
    REFERENCES workflow.review_case(review_case_id) ON DELETE RESTRICT,
  claim_revision_id uuid NOT NULL UNIQUE
    REFERENCES research.claim_revision(claim_revision_id) ON DELETE RESTRICT
);

CREATE TABLE workflow.review_case_relation (
  review_case_id uuid PRIMARY KEY
    REFERENCES workflow.review_case(review_case_id) ON DELETE RESTRICT,
  semantic_relation_id uuid NOT NULL UNIQUE
    REFERENCES research.semantic_relation(semantic_relation_id) ON DELETE RESTRICT
);

CREATE TABLE workflow.review_case_relation_type_literal (
  review_case_id uuid PRIMARY KEY
    REFERENCES workflow.review_case(review_case_id) ON DELETE RESTRICT,
  relation_type_review_queue_id uuid NOT NULL UNIQUE
    REFERENCES workflow.relation_type_review_queue(relation_type_review_queue_id)
    ON DELETE RESTRICT
);

CREATE INDEX review_case_queue_idx
  ON workflow.review_case (queue_state, priority DESC, created_at);

CREATE TABLE research.trace_node (
  trace_node_id uuid PRIMARY KEY,
  canonical_key text NOT NULL CHECK (btrim(canonical_key) <> ''),
  label text,
  created_at timestamptz NOT NULL
);

CREATE INDEX trace_node_canonical_key_idx ON research.trace_node (canonical_key);

CREATE TABLE research.object_trace_node (
  archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  trace_node_id uuid NOT NULL
    REFERENCES research.trace_node(trace_node_id) ON DELETE RESTRICT,
  node_role text NOT NULL CHECK (node_role ~ '^[a-z][a-z0-9_]*$'),
  PRIMARY KEY (archive_object_id, trace_node_id, node_role)
);

CREATE UNIQUE INDEX object_trace_root_unique
  ON research.object_trace_node (archive_object_id)
  WHERE node_role = 'root';
CREATE INDEX object_trace_node_reverse_idx
  ON research.object_trace_node (trace_node_id, archive_object_id);

CREATE TABLE research.object_relation_membership (
  archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  semantic_relation_id uuid NOT NULL
    REFERENCES research.semantic_relation(semantic_relation_id) ON DELETE RESTRICT,
  membership_role text NOT NULL CHECK (membership_role ~ '^[a-z][a-z0-9_]*$'),
  PRIMARY KEY (archive_object_id, semantic_relation_id, membership_role)
);

CREATE INDEX object_relation_membership_relation_idx
  ON research.object_relation_membership (semantic_relation_id, archive_object_id);

CREATE TABLE research.legacy_projection_fact (
  legacy_projection_fact_id uuid PRIMARY KEY,
  source_asset_id uuid NOT NULL
    REFERENCES raw.source_asset(source_asset_id) ON DELETE RESTRICT,
  legacy_fact_kind text NOT NULL CHECK (legacy_fact_kind IN ('node', 'edge', 'membership', 'evidence', 'review', 'auxiliary')),
  legacy_fact_id text NOT NULL CHECK (btrim(legacy_fact_id) <> ''),
  disposition research.legacy_graph_disposition NOT NULL,
  payload_fingerprint core.sha256_hex NOT NULL,
  reason_code text NOT NULL CHECK (btrim(reason_code) <> ''),
  recorded_at timestamptz NOT NULL,
  UNIQUE (source_asset_id, legacy_fact_kind, legacy_fact_id)
);

CREATE INDEX legacy_projection_disposition_idx
  ON research.legacy_projection_fact (disposition, legacy_fact_kind);

CREATE TABLE provenance.assertion_subject_source_record (
  assertion_id uuid PRIMARY KEY
    REFERENCES provenance.assertion(assertion_id) ON DELETE RESTRICT,
  source_record_id uuid NOT NULL
    REFERENCES raw.source_record(source_record_id) ON DELETE RESTRICT
);

CREATE TABLE provenance.assertion_subject_trace_node (
  assertion_id uuid PRIMARY KEY
    REFERENCES provenance.assertion(assertion_id) ON DELETE RESTRICT,
  trace_node_id uuid NOT NULL
    REFERENCES research.trace_node(trace_node_id) ON DELETE RESTRICT
);

CREATE TABLE provenance.assertion_value_source_record (
  assertion_id uuid PRIMARY KEY
    REFERENCES provenance.assertion(assertion_id) ON DELETE RESTRICT,
  source_record_id uuid NOT NULL
    REFERENCES raw.source_record(source_record_id) ON DELETE RESTRICT
);

CREATE TABLE provenance.assertion_value_trace_node (
  assertion_id uuid PRIMARY KEY
    REFERENCES provenance.assertion(assertion_id) ON DELETE RESTRICT,
  trace_node_id uuid NOT NULL
    REFERENCES research.trace_node(trace_node_id) ON DELETE RESTRICT
);

CREATE TABLE provenance.assignment_object_tree_membership (
  canonical_assignment_id uuid PRIMARY KEY
    REFERENCES provenance.canonical_assignment(canonical_assignment_id) ON DELETE RESTRICT,
  archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  trace_node_id uuid NOT NULL
    REFERENCES research.trace_node(trace_node_id) ON DELETE RESTRICT,
  tree_role text NOT NULL CHECK (tree_role ~ '^[a-z][a-z0-9_]*$'),
  UNIQUE (archive_object_id, trace_node_id, tree_role)
);

CREATE TABLE rights.provider (
  provider_id uuid PRIMARY KEY,
  provider_code text NOT NULL UNIQUE CHECK (provider_code ~ '^[a-z][a-z0-9_-]*$'),
  display_name text NOT NULL CHECK (btrim(display_name) <> ''),
  created_at timestamptz NOT NULL
);

CREATE TABLE rights.provider_object (
  provider_object_id uuid PRIMARY KEY,
  provider_id uuid NOT NULL REFERENCES rights.provider(provider_id) ON DELETE RESTRICT,
  provider_record_key text NOT NULL CHECK (btrim(provider_record_key) <> ''),
  created_at timestamptz NOT NULL,
  UNIQUE (provider_id, provider_record_key)
);

CREATE TABLE rights.digital_representation (
  digital_representation_id uuid PRIMARY KEY,
  media_type text NOT NULL CHECK (btrim(media_type) <> ''),
  content_sha256 core.sha256_hex,
  byte_length bigint CHECK (byte_length IS NULL OR byte_length >= 0),
  evidence_item_id uuid
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL,
  UNIQUE NULLS NOT DISTINCT (content_sha256, byte_length, evidence_item_id),
  CHECK (content_sha256 IS NOT NULL OR evidence_item_id IS NOT NULL)
);

CREATE TABLE provenance.assertion_subject_representation (
  assertion_id uuid PRIMARY KEY
    REFERENCES provenance.assertion(assertion_id) ON DELETE RESTRICT,
  digital_representation_id uuid NOT NULL
    REFERENCES rights.digital_representation(digital_representation_id) ON DELETE RESTRICT
);

CREATE TABLE provenance.assignment_object_representation (
  canonical_assignment_id uuid PRIMARY KEY
    REFERENCES provenance.canonical_assignment(canonical_assignment_id) ON DELETE RESTRICT,
  archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  digital_representation_id uuid NOT NULL
    REFERENCES rights.digital_representation(digital_representation_id) ON DELETE RESTRICT,
  representation_role rights.representation_role NOT NULL,
  UNIQUE (archive_object_id, digital_representation_id, representation_role)
);

CREATE TABLE rights.provider_policy_version (
  provider_policy_version_id uuid PRIMARY KEY,
  provider_id uuid NOT NULL REFERENCES rights.provider(provider_id) ON DELETE RESTRICT,
  version_token core.release_token NOT NULL,
  policy_sha256 core.sha256_hex NOT NULL,
  policy_state rights.policy_state NOT NULL,
  effective_from timestamptz NOT NULL,
  effective_until timestamptz,
  review_due timestamptz NOT NULL,
  source_evidence_item_id uuid
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  CHECK (effective_until IS NULL OR effective_until > effective_from),
  CHECK (review_due > effective_from),
  UNIQUE (provider_id, version_token),
  UNIQUE (provider_id, policy_sha256)
);

CREATE INDEX provider_policy_effective_idx
  ON rights.provider_policy_version (provider_id, effective_from DESC);

CREATE TABLE rights.external_visual_reference (
  external_visual_reference_id uuid PRIMARY KEY,
  visual_reference_urn core.canonical_urn GENERATED ALWAYS AS
    (('urn:gdarchive:visual-reference:'::text || external_visual_reference_id::text)::core.canonical_urn) STORED,
  source_asset_id uuid NOT NULL
    REFERENCES raw.source_asset(source_asset_id) ON DELETE RESTRICT,
  source_record_id uuid NOT NULL
    REFERENCES raw.source_record(source_record_id) ON DELETE RESTRICT,
  source_field_or_json_pointer text NOT NULL CHECK (source_field_or_json_pointer ~ '^/'),
  source_occurrence_ordinal integer NOT NULL CHECK (source_occurrence_ordinal >= 0),
  provider_object_id uuid REFERENCES rights.provider_object(provider_object_id) ON DELETE RESTRICT,
  reference_fingerprint core.sha256_hex NOT NULL,
  created_at timestamptz NOT NULL,
  UNIQUE (source_asset_id, source_record_id, source_field_or_json_pointer, source_occurrence_ordinal),
  UNIQUE (visual_reference_urn),
  FOREIGN KEY (source_asset_id, source_record_id)
    REFERENCES raw.source_record(source_asset_id, source_record_id) ON DELETE RESTRICT
);

CREATE INDEX visual_reference_provider_object_idx
  ON rights.external_visual_reference (provider_object_id);
CREATE INDEX visual_reference_fingerprint_idx
  ON rights.external_visual_reference (reference_fingerprint);

CREATE TABLE rights.visual_reference_representation (
  external_visual_reference_id uuid NOT NULL
    REFERENCES rights.external_visual_reference(external_visual_reference_id) ON DELETE RESTRICT,
  digital_representation_id uuid NOT NULL
    REFERENCES rights.digital_representation(digital_representation_id) ON DELETE RESTRICT,
  representation_role rights.representation_role NOT NULL,
  evidence_item_id uuid
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  PRIMARY KEY (
    external_visual_reference_id, digital_representation_id, representation_role
  )
);

CREATE INDEX visual_reference_representation_reverse_idx
  ON rights.visual_reference_representation
    (digital_representation_id, external_visual_reference_id);

CREATE TABLE rights.object_visual_reference (
  object_visual_reference_id uuid PRIMARY KEY,
  archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  external_visual_reference_id uuid NOT NULL
    REFERENCES rights.external_visual_reference(external_visual_reference_id) ON DELETE RESTRICT,
  reference_role rights.reference_role NOT NULL,
  ordinal integer NOT NULL CHECK (ordinal >= 0),
  acceptance_state provenance.assertion_status NOT NULL,
  evidence_item_id uuid
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  UNIQUE (archive_object_id, external_visual_reference_id, reference_role),
  UNIQUE (archive_object_id, reference_role, ordinal)
);

CREATE INDEX object_visual_reference_reverse_idx
  ON rights.object_visual_reference (external_visual_reference_id, archive_object_id);

CREATE TABLE rights.visual_locator (
  visual_locator_id uuid PRIMARY KEY,
  external_visual_reference_id uuid NOT NULL
    REFERENCES rights.external_visual_reference(external_visual_reference_id) ON DELETE RESTRICT,
  locator_role rights.locator_role NOT NULL,
  source_asset_id uuid NOT NULL
    REFERENCES raw.source_asset(source_asset_id) ON DELETE RESTRICT,
  source_record_id uuid NOT NULL
    REFERENCES raw.source_record(source_record_id) ON DELETE RESTRICT,
  source_field_or_json_pointer text NOT NULL CHECK (source_field_or_json_pointer ~ '^/'),
  occurrence_ordinal integer NOT NULL CHECK (occurrence_ordinal >= 0),
  source_evidence_item_id uuid
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  visibility rights.locator_visibility NOT NULL,
  raw_locator text NOT NULL CHECK (btrim(raw_locator) <> ''),
  locator_fingerprint core.sha256_hex NOT NULL,
  supersedes_visual_locator_id uuid
    REFERENCES rights.visual_locator(visual_locator_id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL,
  UNIQUE (
    external_visual_reference_id, locator_role, source_asset_id,
    source_record_id, source_field_or_json_pointer, occurrence_ordinal
  ),
  FOREIGN KEY (source_asset_id, source_record_id)
    REFERENCES raw.source_record(source_asset_id, source_record_id) ON DELETE RESTRICT
  ,CONSTRAINT visual_locator_fingerprint_matches
    CHECK (encode(sha256(convert_to(raw_locator, 'UTF8')), 'hex') = locator_fingerprint)
);

CREATE INDEX visual_locator_reference_role_idx
  ON rights.visual_locator (external_visual_reference_id, locator_role, visibility);
CREATE INDEX visual_locator_fingerprint_idx ON rights.visual_locator (locator_fingerprint);
ALTER TABLE rights.visual_locator
  ADD CONSTRAINT visual_locator_reference_identity_unique
  UNIQUE (visual_locator_id, external_visual_reference_id);

CREATE TABLE rights.visual_locator_representation (
  visual_locator_id uuid PRIMARY KEY,
  external_visual_reference_id uuid NOT NULL,
  digital_representation_id uuid NOT NULL,
  representation_role rights.representation_role NOT NULL,
  FOREIGN KEY (visual_locator_id, external_visual_reference_id)
    REFERENCES rights.visual_locator(
      visual_locator_id, external_visual_reference_id) ON DELETE RESTRICT,
  FOREIGN KEY (
    external_visual_reference_id, digital_representation_id,
    representation_role
  ) REFERENCES rights.visual_reference_representation (
    external_visual_reference_id, digital_representation_id,
    representation_role
  ) ON DELETE RESTRICT
);

CREATE INDEX visual_locator_representation_reverse_idx
  ON rights.visual_locator_representation
    (digital_representation_id, external_visual_reference_id);

CREATE TABLE rights.rights_observation (
  rights_observation_id uuid PRIMARY KEY,
  subject_kind rights.rights_subject_kind NOT NULL,
  evidence_state rights.rights_evidence_state NOT NULL,
  evidence_item_id uuid
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  observed_wording text,
  observed_at timestamptz NOT NULL,
  supersedes_rights_observation_id uuid
    REFERENCES rights.rights_observation(rights_observation_id) ON DELETE RESTRICT,
  UNIQUE (supersedes_rights_observation_id)
);

CREATE TABLE rights.rights_observation_provider_object (
  rights_observation_id uuid PRIMARY KEY
    REFERENCES rights.rights_observation(rights_observation_id) ON DELETE RESTRICT,
  provider_object_id uuid NOT NULL
    REFERENCES rights.provider_object(provider_object_id) ON DELETE RESTRICT
);

CREATE TABLE rights.rights_observation_visual_reference (
  rights_observation_id uuid PRIMARY KEY
    REFERENCES rights.rights_observation(rights_observation_id) ON DELETE RESTRICT,
  external_visual_reference_id uuid NOT NULL
    REFERENCES rights.external_visual_reference(external_visual_reference_id) ON DELETE RESTRICT
);

CREATE TABLE rights.rights_observation_representation (
  rights_observation_id uuid PRIMARY KEY
    REFERENCES rights.rights_observation(rights_observation_id) ON DELETE RESTRICT,
  digital_representation_id uuid NOT NULL
    REFERENCES rights.digital_representation(digital_representation_id) ON DELETE RESTRICT
);

CREATE TABLE rights.rights_observation_locator (
  rights_observation_id uuid PRIMARY KEY
    REFERENCES rights.rights_observation(rights_observation_id) ON DELETE RESTRICT,
  visual_locator_id uuid NOT NULL
    REFERENCES rights.visual_locator(visual_locator_id) ON DELETE RESTRICT
);

CREATE INDEX rights_observation_state_idx
  ON rights.rights_observation (subject_kind, evidence_state, observed_at DESC);

CREATE TABLE rights.rights_assessment (
  rights_assessment_id uuid PRIMARY KEY,
  subject_kind rights.rights_subject_kind NOT NULL,
  assessed_state rights.rights_evidence_state NOT NULL,
  reviewer_actor text NOT NULL CHECK (btrim(reviewer_actor) <> ''),
  rationale text NOT NULL CHECK (btrim(rationale) <> ''),
  assessed_at timestamptz NOT NULL,
  supersedes_rights_assessment_id uuid
    REFERENCES rights.rights_assessment(rights_assessment_id) ON DELETE RESTRICT,
  UNIQUE (supersedes_rights_assessment_id)
);

CREATE TABLE rights.rights_assessment_provider_object (
  rights_assessment_id uuid PRIMARY KEY
    REFERENCES rights.rights_assessment(rights_assessment_id) ON DELETE RESTRICT,
  provider_object_id uuid NOT NULL
    REFERENCES rights.provider_object(provider_object_id) ON DELETE RESTRICT
);

CREATE TABLE rights.rights_assessment_visual_reference (
  rights_assessment_id uuid PRIMARY KEY
    REFERENCES rights.rights_assessment(rights_assessment_id) ON DELETE RESTRICT,
  external_visual_reference_id uuid NOT NULL
    REFERENCES rights.external_visual_reference(external_visual_reference_id) ON DELETE RESTRICT
);

CREATE TABLE rights.rights_assessment_representation (
  rights_assessment_id uuid PRIMARY KEY
    REFERENCES rights.rights_assessment(rights_assessment_id) ON DELETE RESTRICT,
  digital_representation_id uuid NOT NULL
    REFERENCES rights.digital_representation(digital_representation_id) ON DELETE RESTRICT
);

CREATE TABLE rights.rights_assessment_locator (
  rights_assessment_id uuid PRIMARY KEY
    REFERENCES rights.rights_assessment(rights_assessment_id) ON DELETE RESTRICT,
  visual_locator_id uuid NOT NULL
    REFERENCES rights.visual_locator(visual_locator_id) ON DELETE RESTRICT
);

CREATE INDEX rights_assessment_state_idx
  ON rights.rights_assessment (subject_kind, assessed_state, assessed_at DESC);

CREATE TABLE rights.rights_assessment_observation (
  rights_assessment_id uuid NOT NULL
    REFERENCES rights.rights_assessment(rights_assessment_id) ON DELETE RESTRICT,
  rights_observation_id uuid NOT NULL
    REFERENCES rights.rights_observation(rights_observation_id) ON DELETE RESTRICT,
  evidence_role provenance.evidence_role NOT NULL,
  PRIMARY KEY (rights_assessment_id, rights_observation_id, evidence_role)
);

CREATE TABLE workflow.review_case_rights_assessment (
  review_case_id uuid PRIMARY KEY
    REFERENCES workflow.review_case(review_case_id) ON DELETE RESTRICT,
  rights_assessment_id uuid NOT NULL UNIQUE
    REFERENCES rights.rights_assessment(rights_assessment_id) ON DELETE RESTRICT
);

CREATE INDEX rights_assessment_observation_reverse_idx
  ON rights.rights_assessment_observation (rights_observation_id, rights_assessment_id);

CREATE TABLE rights.provider_policy_evaluation (
  provider_policy_evaluation_id uuid PRIMARY KEY,
  object_visual_reference_id uuid NOT NULL
    REFERENCES rights.object_visual_reference(object_visual_reference_id) ON DELETE RESTRICT,
  evaluated_state rights.policy_state NOT NULL,
  evaluator_actor text NOT NULL CHECK (btrim(evaluator_actor) <> ''),
  evaluated_at timestamptz NOT NULL,
  supersedes_provider_policy_evaluation_id uuid
    REFERENCES rights.provider_policy_evaluation(provider_policy_evaluation_id) ON DELETE RESTRICT,
  UNIQUE (supersedes_provider_policy_evaluation_id)
);

CREATE INDEX provider_policy_evaluation_reference_idx
  ON rights.provider_policy_evaluation (object_visual_reference_id, evaluated_at DESC);

CREATE TABLE rights.provider_policy_evaluation_version (
  provider_policy_evaluation_id uuid NOT NULL
    REFERENCES rights.provider_policy_evaluation(provider_policy_evaluation_id) ON DELETE RESTRICT,
  provider_policy_version_id uuid NOT NULL
    REFERENCES rights.provider_policy_version(provider_policy_version_id) ON DELETE RESTRICT,
  PRIMARY KEY (provider_policy_evaluation_id, provider_policy_version_id)
);

CREATE INDEX provider_policy_evaluation_version_reverse_idx
  ON rights.provider_policy_evaluation_version
    (provider_policy_version_id, provider_policy_evaluation_id);

CREATE TABLE rights.attribution_bundle (
  attribution_bundle_id uuid PRIMARY KEY,
  object_visual_reference_id uuid NOT NULL
    REFERENCES rights.object_visual_reference(object_visual_reference_id) ON DELETE RESTRICT,
  attribution_state rights.attribution_state NOT NULL,
  bundle_sha256 core.sha256_hex NOT NULL,
  evidence_item_id uuid
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  validated_by text NOT NULL CHECK (btrim(validated_by) <> ''),
  validated_at timestamptz NOT NULL,
  supersedes_attribution_bundle_id uuid
    REFERENCES rights.attribution_bundle(attribution_bundle_id) ON DELETE RESTRICT,
  UNIQUE (object_visual_reference_id, bundle_sha256)
);

CREATE TABLE rights.attribution_bundle_value (
  attribution_bundle_id uuid NOT NULL
    REFERENCES rights.attribution_bundle(attribution_bundle_id) ON DELETE RESTRICT,
  value_kind text NOT NULL CHECK (value_kind IN ('attribution', 'required_statement')),
  value_ordinal integer NOT NULL CHECK (value_ordinal >= 0),
  language_tag text,
  value_text text NOT NULL CHECK (btrim(value_text) <> ''),
  PRIMARY KEY (attribution_bundle_id, value_kind, value_ordinal)
);

CREATE TABLE rights.endpoint_health_observation (
  endpoint_health_observation_id uuid PRIMARY KEY,
  visual_locator_id uuid NOT NULL
    REFERENCES rights.visual_locator(visual_locator_id) ON DELETE RESTRICT,
  health_state rights.health_state NOT NULL,
  method_version core.release_token NOT NULL,
  checked_at timestamptz NOT NULL,
  valid_until timestamptz,
  request_fingerprint core.sha256_hex NOT NULL,
  CHECK (valid_until IS NULL OR valid_until > checked_at),
  CHECK (valid_until IS NULL OR valid_until <= checked_at + interval '31 days'),
  UNIQUE (visual_locator_id, checked_at, method_version, request_fingerprint)
);

CREATE INDEX endpoint_health_locator_idx
  ON rights.endpoint_health_observation (visual_locator_id, checked_at DESC);

CREATE TABLE rights.delivery_assessment (
  delivery_assessment_id uuid PRIMARY KEY,
  object_visual_reference_id uuid NOT NULL
    REFERENCES rights.object_visual_reference(object_visual_reference_id) ON DELETE RESTRICT,
  attribution_bundle_id uuid
    REFERENCES rights.attribution_bundle(attribution_bundle_id) ON DELETE RESTRICT,
  delivery_mode rights.delivery_mode NOT NULL,
  reason_code text NOT NULL CHECK (reason_code ~ '^RD-[0-9]{3}$'),
  assessor_actor text NOT NULL CHECK (btrim(assessor_actor) <> ''),
  assessed_at timestamptz NOT NULL,
  supersedes_delivery_assessment_id uuid
    REFERENCES rights.delivery_assessment(delivery_assessment_id) ON DELETE RESTRICT,
  UNIQUE (supersedes_delivery_assessment_id)
);

CREATE INDEX delivery_assessment_reference_idx
  ON rights.delivery_assessment (object_visual_reference_id, assessed_at DESC);
CREATE INDEX delivery_assessment_mode_idx
  ON rights.delivery_assessment (delivery_mode, assessed_at DESC);

CREATE TABLE rights.delivery_rights_assessment (
  delivery_assessment_id uuid NOT NULL
    REFERENCES rights.delivery_assessment(delivery_assessment_id) ON DELETE RESTRICT,
  rights_assessment_id uuid NOT NULL
    REFERENCES rights.rights_assessment(rights_assessment_id) ON DELETE RESTRICT,
  evidence_role provenance.evidence_role NOT NULL,
  PRIMARY KEY (delivery_assessment_id, rights_assessment_id, evidence_role)
);

CREATE TABLE rights.delivery_policy_evaluation (
  delivery_assessment_id uuid NOT NULL
    REFERENCES rights.delivery_assessment(delivery_assessment_id) ON DELETE RESTRICT,
  provider_policy_evaluation_id uuid NOT NULL
    REFERENCES rights.provider_policy_evaluation(provider_policy_evaluation_id) ON DELETE RESTRICT,
  PRIMARY KEY (delivery_assessment_id, provider_policy_evaluation_id)
);

CREATE TABLE rights.delivery_locator_qualification (
  delivery_assessment_id uuid NOT NULL
    REFERENCES rights.delivery_assessment(delivery_assessment_id) ON DELETE RESTRICT,
  visual_locator_id uuid NOT NULL
    REFERENCES rights.visual_locator(visual_locator_id) ON DELETE RESTRICT,
  endpoint_health_observation_id uuid NOT NULL
    REFERENCES rights.endpoint_health_observation(endpoint_health_observation_id) ON DELETE RESTRICT,
  allowlisted_role rights.locator_role NOT NULL,
  PRIMARY KEY (delivery_assessment_id, visual_locator_id, endpoint_health_observation_id),
  UNIQUE (delivery_assessment_id, allowlisted_role)
);

CREATE TABLE rights.takedown_scope (
  takedown_scope_id uuid PRIMARY KEY,
  takedown_event_id uuid NOT NULL,
  scope_kind rights.takedown_scope_kind NOT NULL
);

CREATE TABLE rights.takedown_scope_visual_reference (
  takedown_scope_id uuid PRIMARY KEY
    REFERENCES rights.takedown_scope(takedown_scope_id) ON DELETE RESTRICT,
  external_visual_reference_id uuid NOT NULL
    REFERENCES rights.external_visual_reference(external_visual_reference_id) ON DELETE RESTRICT
);

CREATE TABLE rights.takedown_scope_provider (
  takedown_scope_id uuid PRIMARY KEY
    REFERENCES rights.takedown_scope(takedown_scope_id) ON DELETE RESTRICT,
  provider_id uuid NOT NULL REFERENCES rights.provider(provider_id) ON DELETE RESTRICT
);

CREATE TABLE rights.takedown_scope_locator (
  takedown_scope_id uuid PRIMARY KEY
    REFERENCES rights.takedown_scope(takedown_scope_id) ON DELETE RESTRICT,
  visual_locator_id uuid NOT NULL
    REFERENCES rights.visual_locator(visual_locator_id) ON DELETE RESTRICT
);

CREATE TABLE rights.takedown_scope_provider_object (
  takedown_scope_id uuid PRIMARY KEY
    REFERENCES rights.takedown_scope(takedown_scope_id) ON DELETE RESTRICT,
  provider_object_id uuid NOT NULL
    REFERENCES rights.provider_object(provider_object_id) ON DELETE RESTRICT
);

CREATE TABLE rights.takedown_scope_representation (
  takedown_scope_id uuid PRIMARY KEY
    REFERENCES rights.takedown_scope(takedown_scope_id) ON DELETE RESTRICT,
  digital_representation_id uuid NOT NULL
    REFERENCES rights.digital_representation(digital_representation_id) ON DELETE RESTRICT
);

CREATE TABLE rights.takedown_scope_object_visual_reference (
  takedown_scope_id uuid PRIMARY KEY
    REFERENCES rights.takedown_scope(takedown_scope_id) ON DELETE RESTRICT,
  object_visual_reference_id uuid NOT NULL
    REFERENCES rights.object_visual_reference(object_visual_reference_id) ON DELETE RESTRICT
);

CREATE TABLE rights.takedown_event (
  takedown_event_id uuid PRIMARY KEY,
  action rights.takedown_action NOT NULL,
  effective_from timestamptz NOT NULL,
  effective_until timestamptz,
  reason_code text NOT NULL CHECK (btrim(reason_code) <> ''),
  evidence_item_id uuid
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  recorded_by text NOT NULL CHECK (btrim(recorded_by) <> ''),
  recorded_at timestamptz NOT NULL,
  CHECK (effective_until IS NULL OR effective_until > effective_from)
);

ALTER TABLE rights.takedown_scope
  ADD CONSTRAINT takedown_scope_event_fk
  FOREIGN KEY (takedown_event_id)
  REFERENCES rights.takedown_event(takedown_event_id) ON DELETE RESTRICT;

CREATE INDEX takedown_scope_event_idx
  ON rights.takedown_scope (takedown_event_id, scope_kind);
CREATE INDEX takedown_event_effective_idx
  ON rights.takedown_event (effective_from DESC);

CREATE TABLE rights.takedown_override (
  takedown_override_id uuid PRIMARY KEY,
  takedown_scope_id uuid NOT NULL
    REFERENCES rights.takedown_scope(takedown_scope_id) ON DELETE RESTRICT,
  restrictive_mode rights.delivery_mode NOT NULL
    CHECK (restrictive_mode IN ('blocked', 'citation_only')),
  overlay_sha256 core.sha256_hex NOT NULL,
  supersedes_takedown_override_id uuid
    REFERENCES rights.takedown_override(takedown_override_id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL,
  UNIQUE (takedown_scope_id, overlay_sha256),
  UNIQUE (supersedes_takedown_override_id)
);

ALTER TABLE core.legacy_identity_resolution
  ADD CONSTRAINT legacy_resolution_trace_node_fk
    FOREIGN KEY (target_trace_node_id)
    REFERENCES research.trace_node(trace_node_id) ON DELETE RESTRICT,
  ADD CONSTRAINT legacy_resolution_folder_fk
    FOREIGN KEY (target_folder_id)
    REFERENCES research.folder(folder_id) ON DELETE RESTRICT,
  ADD CONSTRAINT legacy_resolution_decision_evidence_fk
    FOREIGN KEY (decision_evidence_item_id)
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT;

RESET ROLE;
