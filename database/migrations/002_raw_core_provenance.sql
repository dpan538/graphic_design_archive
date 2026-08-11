\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

CREATE TABLE raw.source_asset (
  source_asset_id uuid PRIMARY KEY,
  authority raw.asset_authority NOT NULL,
  logical_name text NOT NULL CHECK (btrim(logical_name) <> ''),
  sha256 core.sha256_hex NOT NULL,
  byte_length bigint NOT NULL CHECK (byte_length >= 0),
  raw_bytes bytea NOT NULL,
  media_type text,
  received_at timestamptz NOT NULL,
  CONSTRAINT source_asset_byte_length_matches
    CHECK (octet_length(raw_bytes) = byte_length),
  CONSTRAINT source_asset_sha256_matches
    CHECK (encode(sha256(raw_bytes), 'hex') = sha256),
  CONSTRAINT source_asset_lexical_identity_unique UNIQUE (sha256, byte_length),
  CONSTRAINT source_asset_id_sha_unique UNIQUE (source_asset_id, sha256)
);

CREATE INDEX source_asset_authority_idx ON raw.source_asset (authority, logical_name);

CREATE TABLE raw.mapping_version (
  mapping_version_id uuid PRIMARY KEY,
  version_token core.release_token NOT NULL UNIQUE,
  specification_sha256 core.sha256_hex NOT NULL,
  parser_version text NOT NULL CHECK (btrim(parser_version) <> ''),
  delimiter_policy text NOT NULL CHECK (delimiter_policy = 'preserve_no_automatic_split'),
  created_at timestamptz NOT NULL
);

CREATE TABLE raw.migration_batch (
  migration_batch_id uuid PRIMARY KEY,
  batch_token core.release_token NOT NULL UNIQUE,
  canonical_input_asset_id uuid NOT NULL
    REFERENCES raw.source_asset(source_asset_id) ON DELETE RESTRICT,
  mapping_version_id uuid NOT NULL
    REFERENCES raw.mapping_version(mapping_version_id) ON DELETE RESTRICT,
  input_sha256 core.sha256_hex NOT NULL,
  started_at timestamptz NOT NULL,
  completed_at timestamptz,
  CHECK (completed_at IS NULL OR completed_at >= started_at),
  FOREIGN KEY (canonical_input_asset_id, input_sha256)
    REFERENCES raw.source_asset(source_asset_id, sha256) ON DELETE RESTRICT
);

CREATE INDEX migration_batch_input_idx ON raw.migration_batch (canonical_input_asset_id);
CREATE INDEX migration_batch_mapping_idx ON raw.migration_batch (mapping_version_id);

CREATE TABLE raw.source_record (
  source_record_id uuid PRIMARY KEY,
  source_asset_id uuid NOT NULL
    REFERENCES raw.source_asset(source_asset_id) ON DELETE RESTRICT,
  record_ordinal bigint NOT NULL CHECK (record_ordinal >= 0),
  legacy_source_record_id text,
  raw_value bytea NOT NULL,
  raw_fingerprint core.sha256_hex NOT NULL,
  parsed_projection jsonb,
  parse_error_code text,
  CONSTRAINT source_record_occurrence_unique UNIQUE (source_asset_id, record_ordinal),
  CONSTRAINT source_record_asset_identity_unique UNIQUE (source_asset_id, source_record_id),
  CONSTRAINT source_record_value_nonempty CHECK (octet_length(raw_value) > 0),
  CONSTRAINT source_record_fingerprint_matches
    CHECK (encode(sha256(raw_value), 'hex') = raw_fingerprint)
);

CREATE INDEX source_record_legacy_id_idx ON raw.source_record (legacy_source_record_id);
CREATE INDEX source_record_fingerprint_idx ON raw.source_record (raw_fingerprint);

CREATE TABLE raw.field_literal (
  field_literal_id uuid PRIMARY KEY,
  source_record_id uuid NOT NULL
    REFERENCES raw.source_record(source_record_id) ON DELETE RESTRICT,
  json_pointer text NOT NULL CHECK (json_pointer ~ '^/'),
  occurrence_ordinal integer NOT NULL CHECK (occurrence_ordinal >= 0),
  raw_text text,
  raw_bytes bytea,
  byte_start bigint CHECK (byte_start IS NULL OR byte_start >= 0),
  byte_end bigint CHECK (byte_end IS NULL OR byte_end >= byte_start),
  CONSTRAINT field_literal_occurrence_unique
    UNIQUE (source_record_id, json_pointer, occurrence_ordinal),
  CONSTRAINT field_literal_has_lexical_value
    CHECK (raw_text IS NOT NULL OR raw_bytes IS NOT NULL)
);

CREATE INDEX field_literal_source_idx ON raw.field_literal (source_record_id);

CREATE TABLE core.entity (
  entity_id uuid PRIMARY KEY,
  entity_kind core.entity_kind NOT NULL,
  lifecycle_state core.lifecycle_state NOT NULL,
  created_at timestamptz NOT NULL,
  withdrawn_at timestamptz,
  CHECK ((lifecycle_state = 'active' AND withdrawn_at IS NULL)
      OR (lifecycle_state <> 'active'))
);

CREATE INDEX entity_kind_state_idx ON core.entity (entity_kind, lifecycle_state);

CREATE TABLE core.archive_object (
  archive_object_id uuid PRIMARY KEY
    REFERENCES core.entity(entity_id) ON DELETE RESTRICT,
  object_urn core.canonical_urn GENERATED ALWAYS AS
    (('urn:gdarchive:object:'::text || archive_object_id::text)::core.canonical_urn) STORED,
  operational_semantics_version core.release_token NOT NULL,
  preferred_label text,
  created_from_surface_ledger_id uuid
);

CREATE UNIQUE INDEX archive_object_urn_uidx ON core.archive_object (object_urn);

CREATE TABLE core.agent (
  agent_id uuid PRIMARY KEY REFERENCES core.entity(entity_id) ON DELETE RESTRICT,
  preferred_name text NOT NULL CHECK (btrim(preferred_name) <> '')
);

CREATE TABLE core.place (
  place_id uuid PRIMARY KEY REFERENCES core.entity(entity_id) ON DELETE RESTRICT,
  preferred_name text NOT NULL CHECK (btrim(preferred_name) <> '')
);

CREATE TABLE core.concept (
  concept_id uuid PRIMARY KEY REFERENCES core.entity(entity_id) ON DELETE RESTRICT,
  preferred_label text NOT NULL CHECK (btrim(preferred_label) <> '')
);

CREATE TABLE core.collection (
  collection_id uuid PRIMARY KEY REFERENCES core.entity(entity_id) ON DELETE RESTRICT,
  preferred_label text NOT NULL CHECK (btrim(preferred_label) <> '')
);

CREATE TABLE core.temporal_extent (
  temporal_extent_id uuid PRIMARY KEY REFERENCES core.entity(entity_id) ON DELETE RESTRICT,
  start_date date,
  end_date date,
  label text,
  CHECK (start_date IS NULL OR end_date IS NULL OR end_date >= start_date),
  CHECK (start_date IS NOT NULL OR end_date IS NOT NULL OR label IS NOT NULL)
);

CREATE TABLE raw.legacy_surface_ledger (
  legacy_surface_ledger_id uuid PRIMARY KEY,
  migration_batch_id uuid NOT NULL
    REFERENCES raw.migration_batch(migration_batch_id) ON DELETE RESTRICT,
  source_record_id uuid NOT NULL
    REFERENCES raw.source_record(source_record_id) ON DELETE RESTRICT,
  canonical_input_asset_id uuid NOT NULL,
  input_ordinal bigint NOT NULL CHECK (input_ordinal >= 0),
  surface_id text NOT NULL CHECK (btrim(surface_id) <> ''),
  legacy_source_record_id text,
  source_fingerprint core.sha256_hex NOT NULL,
  import_disposition raw.import_disposition NOT NULL,
  archive_object_id uuid REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  reason_code text NOT NULL CHECK (btrim(reason_code) <> ''),
  CONSTRAINT legacy_surface_batch_ordinal_unique UNIQUE (migration_batch_id, input_ordinal),
  CONSTRAINT legacy_surface_batch_surface_unique UNIQUE (migration_batch_id, surface_id),
  CONSTRAINT legacy_surface_batch_source_occurrence_unique UNIQUE (migration_batch_id, source_record_id),
  CONSTRAINT legacy_surface_closed_disposition_requires_object CHECK (
    (import_disposition = 'candidate')
    OR archive_object_id IS NOT NULL
  ),
  FOREIGN KEY (canonical_input_asset_id, source_record_id)
    REFERENCES raw.source_record(source_asset_id, source_record_id) ON DELETE RESTRICT
);

ALTER TABLE core.archive_object
  ADD CONSTRAINT archive_object_surface_ledger_fk
  FOREIGN KEY (created_from_surface_ledger_id)
  REFERENCES raw.legacy_surface_ledger(legacy_surface_ledger_id)
  ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED;

CREATE INDEX legacy_surface_source_record_idx ON raw.legacy_surface_ledger (source_record_id);
CREATE INDEX legacy_surface_archive_object_idx ON raw.legacy_surface_ledger (archive_object_id);
CREATE INDEX legacy_surface_disposition_idx ON raw.legacy_surface_ledger (migration_batch_id, import_disposition);
CREATE INDEX legacy_surface_fingerprint_idx ON raw.legacy_surface_ledger (source_fingerprint);

CREATE TABLE raw.fail_closed_delta (
  fail_closed_delta_id uuid PRIMARY KEY,
  migration_batch_id uuid NOT NULL
    REFERENCES raw.migration_batch(migration_batch_id) ON DELETE RESTRICT,
  source_record_id uuid NOT NULL
    REFERENCES raw.source_record(source_record_id) ON DELETE RESTRICT,
  field_literal_id uuid REFERENCES raw.field_literal(field_literal_id) ON DELETE RESTRICT,
  expected_classification text,
  actual_literal text,
  reason_code text NOT NULL CHECK (btrim(reason_code) <> ''),
  disposition raw.delta_disposition NOT NULL,
  recorded_at timestamptz NOT NULL,
  resolved_by_delta_id uuid REFERENCES raw.fail_closed_delta(fail_closed_delta_id) ON DELETE RESTRICT
);

CREATE INDEX fail_closed_delta_queue_idx ON raw.fail_closed_delta (migration_batch_id, disposition, reason_code);
CREATE INDEX fail_closed_delta_source_idx ON raw.fail_closed_delta (source_record_id);

CREATE TABLE core.legacy_identity (
  legacy_identity_id uuid PRIMARY KEY,
  identity_kind core.legacy_identity_kind NOT NULL,
  namespace text NOT NULL CHECK (btrim(namespace) <> ''),
  legacy_id text NOT NULL CHECK (btrim(legacy_id) <> ''),
  created_at timestamptz NOT NULL,
  CONSTRAINT legacy_identity_natural_key UNIQUE (identity_kind, namespace, legacy_id)
);

CREATE TABLE core.legacy_identity_resolution (
  legacy_identity_resolution_id uuid PRIMARY KEY,
  legacy_identity_id uuid NOT NULL
    REFERENCES core.legacy_identity(legacy_identity_id) ON DELETE RESTRICT,
  resolution_state core.identity_resolution_state NOT NULL,
  target_archive_object_id uuid
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  target_source_record_id uuid
    REFERENCES raw.source_record(source_record_id) ON DELETE RESTRICT,
  target_trace_node_id uuid,
  target_trace_edge_release_id uuid,
  target_trace_edge_corpus_version_id uuid,
  target_trace_edge_subject_node_id uuid,
  target_trace_edge_relation_id uuid,
  target_trace_edge_object_node_id uuid,
  target_trace_edge_projection_role text,
  target_folder_id uuid,
  decision_evidence_item_id uuid,
  effective_release_id uuid,
  supersedes_resolution_id uuid
    REFERENCES core.legacy_identity_resolution(legacy_identity_resolution_id) ON DELETE RESTRICT,
  effective_from timestamptz NOT NULL,
  reason_code text NOT NULL CHECK (btrim(reason_code) <> ''),
  CONSTRAINT legacy_identity_resolution_target_shape CHECK (
    num_nonnulls(
      target_trace_edge_release_id, target_trace_edge_corpus_version_id,
      target_trace_edge_subject_node_id, target_trace_edge_relation_id,
      target_trace_edge_object_node_id, target_trace_edge_projection_role
    ) IN (0, 6)
    AND
    (resolution_state IN ('primary', 'alias', 'redirect', 'merged')
      AND num_nonnulls(target_archive_object_id, target_source_record_id,
        target_trace_node_id, target_folder_id)
        + CASE WHEN target_trace_edge_release_id IS NULL THEN 0 ELSE 1 END = 1)
    OR (resolution_state IN ('split', 'withdrawn', 'unresolved')
      AND num_nonnulls(target_archive_object_id, target_source_record_id,
        target_trace_node_id, target_folder_id,
        target_trace_edge_release_id, target_trace_edge_corpus_version_id,
        target_trace_edge_subject_node_id, target_trace_edge_relation_id,
        target_trace_edge_object_node_id, target_trace_edge_projection_role) = 0)
  ),
  UNIQUE (supersedes_resolution_id)
);

CREATE INDEX legacy_identity_resolution_object_idx
  ON core.legacy_identity_resolution (target_archive_object_id);
CREATE INDEX legacy_identity_resolution_trace_edge_idx
  ON core.legacy_identity_resolution (
    target_trace_edge_release_id, target_trace_edge_corpus_version_id,
    target_trace_edge_subject_node_id, target_trace_edge_relation_id,
    target_trace_edge_object_node_id, target_trace_edge_projection_role);

CREATE TABLE core.legacy_identity_split_successor (
  legacy_identity_resolution_id uuid NOT NULL
    REFERENCES core.legacy_identity_resolution(legacy_identity_resolution_id) ON DELETE RESTRICT,
  successor_archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  successor_ordinal integer NOT NULL CHECK (successor_ordinal >= 0),
  PRIMARY KEY (legacy_identity_resolution_id, successor_archive_object_id),
  UNIQUE (legacy_identity_resolution_id, successor_ordinal)
);

CREATE INDEX legacy_split_successor_object_idx
  ON core.legacy_identity_split_successor (successor_archive_object_id);

CREATE TABLE core.object_identity_candidate (
  object_identity_candidate_id uuid PRIMARY KEY,
  subject_archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  object_archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  candidate_kind core.object_identity_candidate_kind NOT NULL,
  workflow_state workflow.queue_state NOT NULL,
  evidence_summary text,
  created_at timestamptz NOT NULL,
  CHECK (subject_archive_object_id <> object_archive_object_id),
  UNIQUE (subject_archive_object_id, object_archive_object_id, candidate_kind)
);

CREATE INDEX object_identity_candidate_reverse_idx
  ON core.object_identity_candidate (object_archive_object_id, candidate_kind, workflow_state);

CREATE TABLE provenance.source_document (
  source_document_id uuid PRIMARY KEY,
  source_urn core.canonical_urn GENERATED ALWAYS AS
    (('urn:gdarchive:source:'::text || source_document_id::text)::core.canonical_urn) STORED,
  source_kind text NOT NULL CHECK (btrim(source_kind) <> ''),
  public_citation text,
  created_at timestamptz NOT NULL,
  UNIQUE (source_urn)
);

CREATE TABLE provenance.source_version (
  source_version_id uuid PRIMARY KEY,
  source_document_id uuid NOT NULL
    REFERENCES provenance.source_document(source_document_id) ON DELETE RESTRICT,
  version_token core.release_token NOT NULL,
  content_sha256 core.sha256_hex NOT NULL,
  byte_length bigint NOT NULL CHECK (byte_length >= 0),
  supersedes_source_version_id uuid
    REFERENCES provenance.source_version(source_version_id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL,
  UNIQUE (source_document_id, version_token),
  UNIQUE (source_document_id, content_sha256, byte_length)
);

CREATE INDEX source_version_supersedes_idx ON provenance.source_version (supersedes_source_version_id);

CREATE TABLE provenance.object_source_record (
  archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  source_record_id uuid NOT NULL
    REFERENCES raw.source_record(source_record_id) ON DELETE RESTRICT,
  source_role text NOT NULL CHECK (btrim(source_role) <> ''),
  PRIMARY KEY (archive_object_id, source_record_id, source_role)
);

CREATE INDEX object_source_record_source_idx
  ON provenance.object_source_record (source_record_id, archive_object_id);

CREATE TABLE provenance.evidence_item (
  evidence_item_id uuid PRIMARY KEY,
  source_version_id uuid NOT NULL
    REFERENCES provenance.source_version(source_version_id) ON DELETE RESTRICT,
  source_record_id uuid
    REFERENCES raw.source_record(source_record_id) ON DELETE RESTRICT,
  locator_scheme text,
  internal_locator text,
  span_start bigint CHECK (span_start IS NULL OR span_start >= 0),
  span_end bigint CHECK (span_end IS NULL OR span_end >= span_start),
  content_sha256 core.sha256_hex,
  stable_citation text,
  supersedes_evidence_item_id uuid
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL,
  CONSTRAINT evidence_item_source_identity_unique
    UNIQUE NULLS NOT DISTINCT
      (source_version_id, source_record_id, locator_scheme, internal_locator,
       span_start, span_end, content_sha256),
  CONSTRAINT evidence_item_has_locator_or_hash CHECK (
    internal_locator IS NOT NULL OR content_sha256 IS NOT NULL OR stable_citation IS NOT NULL
  )
);

CREATE INDEX evidence_item_source_record_idx ON provenance.evidence_item (source_record_id);
CREATE INDEX evidence_item_content_hash_idx ON provenance.evidence_item (content_sha256);
CREATE INDEX evidence_item_supersedes_idx ON provenance.evidence_item (supersedes_evidence_item_id);

CREATE TABLE provenance.object_evidence (
  archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  evidence_item_id uuid NOT NULL
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  evidence_role provenance.evidence_role NOT NULL,
  PRIMARY KEY (archive_object_id, evidence_item_id, evidence_role)
);

CREATE INDEX object_evidence_evidence_idx
  ON provenance.object_evidence (evidence_item_id, archive_object_id);

CREATE TABLE provenance.assertion_predicate (
  assertion_predicate_id uuid PRIMARY KEY,
  predicate_code text NOT NULL UNIQUE CHECK (predicate_code ~ '^[a-z][a-z0-9_]*$'),
  active boolean NOT NULL,
  description text NOT NULL CHECK (btrim(description) <> '')
);

CREATE TABLE provenance.assertion (
  assertion_id uuid PRIMARY KEY,
  assertion_predicate_id uuid NOT NULL
    REFERENCES provenance.assertion_predicate(assertion_predicate_id) ON DELETE RESTRICT,
  subject_kind provenance.assertion_subject_kind NOT NULL,
  value_kind provenance.assertion_value_kind NOT NULL,
  status provenance.assertion_status NOT NULL,
  claimant_agent_id uuid REFERENCES core.agent(agent_id) ON DELETE RESTRICT,
  source_wording text,
  supersedes_assertion_id uuid REFERENCES provenance.assertion(assertion_id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL
);

CREATE INDEX assertion_predicate_status_idx
  ON provenance.assertion (assertion_predicate_id, status);
CREATE INDEX assertion_supersedes_idx ON provenance.assertion (supersedes_assertion_id);

CREATE TABLE provenance.assertion_subject_entity (
  assertion_id uuid PRIMARY KEY
    REFERENCES provenance.assertion(assertion_id) ON DELETE RESTRICT,
  entity_id uuid NOT NULL REFERENCES core.entity(entity_id) ON DELETE RESTRICT
);

CREATE INDEX assertion_subject_entity_target_idx
  ON provenance.assertion_subject_entity (entity_id);

CREATE TABLE provenance.assertion_value_literal (
  assertion_id uuid PRIMARY KEY
    REFERENCES provenance.assertion(assertion_id) ON DELETE RESTRICT,
  field_literal_id uuid NOT NULL
    REFERENCES raw.field_literal(field_literal_id) ON DELETE RESTRICT,
  normalized_text text,
  language_tag text,
  datatype_uri text
);

CREATE TABLE provenance.assertion_value_entity (
  assertion_id uuid PRIMARY KEY
    REFERENCES provenance.assertion(assertion_id) ON DELETE RESTRICT,
  entity_id uuid NOT NULL REFERENCES core.entity(entity_id) ON DELETE RESTRICT
);

CREATE INDEX assertion_value_entity_target_idx ON provenance.assertion_value_entity (entity_id);

CREATE TABLE provenance.assertion_evidence (
  assertion_id uuid NOT NULL
    REFERENCES provenance.assertion(assertion_id) ON DELETE RESTRICT,
  evidence_item_id uuid NOT NULL
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  evidence_role provenance.evidence_role NOT NULL,
  PRIMARY KEY (assertion_id, evidence_item_id, evidence_role)
);

CREATE INDEX assertion_evidence_evidence_idx
  ON provenance.assertion_evidence (evidence_item_id, assertion_id);

CREATE TABLE provenance.assertion_review_decision (
  assertion_review_decision_id uuid PRIMARY KEY,
  assertion_id uuid NOT NULL
    REFERENCES provenance.assertion(assertion_id) ON DELETE RESTRICT,
  outcome workflow.review_outcome NOT NULL,
  reviewer_actor text NOT NULL CHECK (btrim(reviewer_actor) <> ''),
  rationale text NOT NULL CHECK (btrim(rationale) <> ''),
  supersedes_decision_id uuid
    REFERENCES provenance.assertion_review_decision(assertion_review_decision_id)
    ON DELETE RESTRICT,
  decided_at timestamptz NOT NULL,
  UNIQUE (supersedes_decision_id)
);

CREATE INDEX assertion_review_effective_idx
  ON provenance.assertion_review_decision (assertion_id, decided_at DESC);

CREATE TABLE provenance.assertion_decision_evidence (
  assertion_review_decision_id uuid NOT NULL
    REFERENCES provenance.assertion_review_decision(assertion_review_decision_id)
    ON DELETE RESTRICT,
  evidence_item_id uuid NOT NULL
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  evidence_role provenance.evidence_role NOT NULL,
  PRIMARY KEY (assertion_review_decision_id, evidence_item_id, evidence_role)
);

CREATE INDEX assertion_decision_evidence_reverse_idx
  ON provenance.assertion_decision_evidence
    (evidence_item_id, assertion_review_decision_id);

CREATE TABLE provenance.canonical_assignment (
  canonical_assignment_id uuid PRIMARY KEY,
  assignment_kind provenance.assignment_kind NOT NULL,
  status provenance.assertion_status NOT NULL,
  supersedes_assignment_id uuid
    REFERENCES provenance.canonical_assignment(canonical_assignment_id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL
);

CREATE INDEX canonical_assignment_kind_status_idx
  ON provenance.canonical_assignment (assignment_kind, status, created_at);

CREATE TABLE provenance.assignment_entity_name (
  canonical_assignment_id uuid PRIMARY KEY
    REFERENCES provenance.canonical_assignment(canonical_assignment_id) ON DELETE RESTRICT,
  entity_id uuid NOT NULL REFERENCES core.entity(entity_id) ON DELETE RESTRICT,
  field_literal_id uuid NOT NULL
    REFERENCES raw.field_literal(field_literal_id) ON DELETE RESTRICT,
  UNIQUE (entity_id, field_literal_id)
);

CREATE TABLE provenance.assignment_object_source_record (
  canonical_assignment_id uuid PRIMARY KEY
    REFERENCES provenance.canonical_assignment(canonical_assignment_id) ON DELETE RESTRICT,
  archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  source_record_id uuid NOT NULL
    REFERENCES raw.source_record(source_record_id) ON DELETE RESTRICT,
  source_role text NOT NULL CHECK (btrim(source_role) <> ''),
  UNIQUE (archive_object_id, source_record_id, source_role)
);

CREATE TABLE provenance.assignment_object_agent_credit (
  canonical_assignment_id uuid PRIMARY KEY
    REFERENCES provenance.canonical_assignment(canonical_assignment_id) ON DELETE RESTRICT,
  archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  agent_id uuid NOT NULL REFERENCES core.agent(agent_id) ON DELETE RESTRICT,
  credit_role text NOT NULL CHECK (btrim(credit_role) <> ''),
  UNIQUE (archive_object_id, agent_id, credit_role)
);

CREATE TABLE provenance.assignment_object_medium (
  canonical_assignment_id uuid PRIMARY KEY
    REFERENCES provenance.canonical_assignment(canonical_assignment_id) ON DELETE RESTRICT,
  archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  medium_concept_id uuid NOT NULL REFERENCES core.concept(concept_id) ON DELETE RESTRICT,
  UNIQUE (archive_object_id, medium_concept_id)
);

CREATE TABLE provenance.assignment_object_type (
  canonical_assignment_id uuid PRIMARY KEY
    REFERENCES provenance.canonical_assignment(canonical_assignment_id) ON DELETE RESTRICT,
  archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  type_concept_id uuid NOT NULL REFERENCES core.concept(concept_id) ON DELETE RESTRICT,
  UNIQUE (archive_object_id, type_concept_id)
);

CREATE TABLE provenance.assignment_object_subject (
  canonical_assignment_id uuid PRIMARY KEY
    REFERENCES provenance.canonical_assignment(canonical_assignment_id) ON DELETE RESTRICT,
  archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  subject_concept_id uuid NOT NULL REFERENCES core.concept(concept_id) ON DELETE RESTRICT,
  UNIQUE (archive_object_id, subject_concept_id)
);

CREATE TABLE provenance.assignment_object_collection (
  canonical_assignment_id uuid PRIMARY KEY
    REFERENCES provenance.canonical_assignment(canonical_assignment_id) ON DELETE RESTRICT,
  archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  collection_id uuid NOT NULL REFERENCES core.collection(collection_id) ON DELETE RESTRICT,
  UNIQUE (archive_object_id, collection_id)
);

CREATE TABLE provenance.assignment_object_temporal (
  canonical_assignment_id uuid PRIMARY KEY
    REFERENCES provenance.canonical_assignment(canonical_assignment_id) ON DELETE RESTRICT,
  archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  temporal_extent_id uuid NOT NULL
    REFERENCES core.temporal_extent(temporal_extent_id) ON DELETE RESTRICT,
  UNIQUE (archive_object_id, temporal_extent_id)
);

CREATE TABLE provenance.assignment_object_place (
  canonical_assignment_id uuid PRIMARY KEY
    REFERENCES provenance.canonical_assignment(canonical_assignment_id) ON DELETE RESTRICT,
  archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  place_id uuid NOT NULL REFERENCES core.place(place_id) ON DELETE RESTRICT,
  UNIQUE (archive_object_id, place_id)
);

CREATE TABLE provenance.assignment_folder_membership (
  canonical_assignment_id uuid PRIMARY KEY
    REFERENCES provenance.canonical_assignment(canonical_assignment_id) ON DELETE RESTRICT,
  folder_id uuid NOT NULL,
  archive_object_id uuid NOT NULL
    REFERENCES core.archive_object(archive_object_id) ON DELETE RESTRICT,
  membership_role text NOT NULL CHECK (membership_role ~ '^[a-z][a-z0-9_]*$'),
  member_ordinal integer NOT NULL CHECK (member_ordinal >= 0),
  UNIQUE (folder_id, archive_object_id, membership_role),
  UNIQUE (folder_id, membership_role, member_ordinal)
);

CREATE TABLE provenance.assignment_identity_resolution (
  canonical_assignment_id uuid PRIMARY KEY
    REFERENCES provenance.canonical_assignment(canonical_assignment_id) ON DELETE RESTRICT,
  legacy_identity_resolution_id uuid NOT NULL
    REFERENCES core.legacy_identity_resolution(legacy_identity_resolution_id) ON DELETE RESTRICT,
  UNIQUE (legacy_identity_resolution_id)
);

CREATE TABLE provenance.assignment_assertion (
  canonical_assignment_id uuid NOT NULL
    REFERENCES provenance.canonical_assignment(canonical_assignment_id) ON DELETE RESTRICT,
  assertion_id uuid NOT NULL
    REFERENCES provenance.assertion(assertion_id) ON DELETE RESTRICT,
  support_role provenance.evidence_role NOT NULL,
  PRIMARY KEY (canonical_assignment_id, assertion_id, support_role)
);

CREATE INDEX assignment_assertion_assertion_idx
  ON provenance.assignment_assertion (assertion_id, canonical_assignment_id);

CREATE TABLE provenance.assignment_context_evidence (
  canonical_assignment_id uuid NOT NULL
    REFERENCES provenance.canonical_assignment(canonical_assignment_id) ON DELETE RESTRICT,
  evidence_item_id uuid NOT NULL
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  evidence_role provenance.evidence_role NOT NULL,
  PRIMARY KEY (canonical_assignment_id, evidence_item_id, evidence_role)
);

CREATE INDEX assignment_context_evidence_evidence_idx
  ON provenance.assignment_context_evidence (evidence_item_id, canonical_assignment_id);

CREATE TABLE provenance.assignment_review_decision (
  assignment_review_decision_id uuid PRIMARY KEY,
  canonical_assignment_id uuid NOT NULL
    REFERENCES provenance.canonical_assignment(canonical_assignment_id) ON DELETE RESTRICT,
  outcome workflow.review_outcome NOT NULL,
  reviewer_actor text NOT NULL CHECK (btrim(reviewer_actor) <> ''),
  rationale text NOT NULL CHECK (btrim(rationale) <> ''),
  supersedes_decision_id uuid
    REFERENCES provenance.assignment_review_decision(assignment_review_decision_id) ON DELETE RESTRICT,
  decided_at timestamptz NOT NULL
);

CREATE INDEX assignment_review_effective_idx
  ON provenance.assignment_review_decision
    (canonical_assignment_id, decided_at DESC);

CREATE TABLE provenance.assignment_decision_evidence (
  assignment_review_decision_id uuid NOT NULL
    REFERENCES provenance.assignment_review_decision(assignment_review_decision_id) ON DELETE RESTRICT,
  evidence_item_id uuid NOT NULL
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  evidence_role provenance.evidence_role NOT NULL,
  PRIMARY KEY (
    assignment_review_decision_id, evidence_item_id, evidence_role
  )
);

CREATE INDEX assignment_decision_evidence_reverse_idx
  ON provenance.assignment_decision_evidence
    (evidence_item_id, assignment_review_decision_id);

RESET ROLE;
