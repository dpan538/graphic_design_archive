\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

-- Phase 2A normative closure.  This migration adds only empty schema
-- structures and closed registries; no production or v48 rows are seeded.

CREATE TYPE release.boundary_kind AS ENUM ('research', 'visual');
CREATE TYPE release.validation_receipt_kind AS ENUM (
  'research_frozen_asset_authority',
  'research_migration_query_identity',
  'research_population_and_count_parity',
  'research_corpus_missingness_concentration',
  'research_fk_orphan_integrity',
  'research_predicate_relation_epistemic_registry',
  'research_claim_projection_eligibility',
  'research_unknown_relation_isolation',
  'research_projection_fingerprint',
  'research_deterministic_asset_inventory',
  'research_role_grant_security',
  'visual_legacy_disposition',
  'visual_reference_bridge_provider_locator_identity',
  'visual_rights_policy_delivery_health_takedown',
  'visual_attribution_review_due',
  'visual_held_pixel_non_disclosure',
  'visual_research_compatibility',
  'visual_projection_fingerprint',
  'visual_deterministic_asset_inventory',
  'visual_role_grant_security'
);
CREATE TYPE release.research_source_role AS ENUM (
  'v48_candidate_json',
  'v48_sqlite_reconciliation',
  'v48_transfer_manifest_json',
  'v48_transfer_manifest_csv',
  'v48_trace_manifest'
);
CREATE TYPE rights.legacy_visual_disposition AS ENUM (
  'evidence_present', 'rights_unknown', 'policy_unknown', 'conflict',
  'stale', 'no_visual_reference', 'takedown_hold', 'malformed',
  'unmapped_provider'
);
CREATE TYPE rights.delivery_rule_id AS ENUM (
  'RD-001', 'RD-002', 'RD-010', 'RD-011', 'RD-020', 'RD-021',
  'RD-030', 'RD-040', 'RD-041', 'RD-050', 'RD-051', 'RD-052',
  'RD-060', 'RD-061', 'RD-070', 'RD-071', 'RD-080', 'RD-081',
  'RD-082', 'RD-999'
);
CREATE TYPE rights.delivery_reason_code AS ENUM (
  'ACTIVE_TAKEDOWN_BLOCK',
  'ACTIVE_TAKEDOWN_CITATION_ONLY',
  'RIGHTS_PROHIBIT_LOCATOR',
  'POLICY_PROHIBITS_PUBLIC_LOCATOR',
  'RIGHTS_FAIL_CLOSED_LINK',
  'RIGHTS_FAIL_CLOSED_CITATION',
  'POLICY_FAIL_CLOSED_CITATION',
  'RIGHTS_CAP_LINK_ONLY',
  'LINK_ENDPOINT_UNQUALIFIED',
  'POLICY_CAP_SOURCE_VIEWER',
  'VIEWER_ENDPOINT_DOWNGRADE_LINK',
  'VIEWER_ENDPOINT_DOWNGRADE_CITATION',
  'POLICY_CAP_LINK_ONLY',
  'POLICY_LINK_UNAVAILABLE',
  'ATTRIBUTION_FAIL_CLOSED_LINK',
  'ATTRIBUTION_FAIL_CLOSED_CITATION',
  'REMOTE_IMAGE_ALL_GATES_PASS',
  'REMOTE_ENDPOINT_DOWNGRADE_LINK',
  'REMOTE_ENDPOINT_DOWNGRADE_CITATION',
  'FAIL_CLOSED_DEFAULT'
);

CREATE TABLE release.validation_profile (
  validation_profile_id uuid PRIMARY KEY,
  boundary_kind release.boundary_kind NOT NULL,
  profile_token core.release_token NOT NULL,
  profile_sha256 core.sha256_hex NOT NULL,
  approved_at timestamptz NOT NULL,
  UNIQUE (boundary_kind, profile_token),
  UNIQUE (boundary_kind, validation_profile_id)
);

CREATE TABLE release.validation_profile_requirement (
  validation_profile_id uuid NOT NULL
    REFERENCES release.validation_profile(validation_profile_id) ON DELETE RESTRICT,
  receipt_kind release.validation_receipt_kind NOT NULL,
  requirement_ordinal integer NOT NULL CHECK (requirement_ordinal > 0),
  PRIMARY KEY (validation_profile_id, receipt_kind),
  UNIQUE (validation_profile_id, requirement_ordinal)
);

ALTER TABLE release.research_release
  ADD COLUMN validation_profile_id uuid NOT NULL
    REFERENCES release.validation_profile(validation_profile_id) ON DELETE RESTRICT;
ALTER TABLE release.visual_registry_release
  ADD COLUMN validation_profile_id uuid NOT NULL
    REFERENCES release.validation_profile(validation_profile_id) ON DELETE RESTRICT;

CREATE TABLE release.research_source_lineage (
  research_release_id uuid NOT NULL
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  source_role release.research_source_role NOT NULL,
  source_asset_id uuid NOT NULL
    REFERENCES raw.source_asset(source_asset_id) ON DELETE RESTRICT,
  asset_authority raw.asset_authority NOT NULL,
  asset_sha256 core.sha256_hex NOT NULL,
  source_git_commit text NOT NULL CHECK (source_git_commit ~ '^[0-9a-f]{40}$'),
  PRIMARY KEY (research_release_id, source_role),
  UNIQUE (research_release_id, source_asset_id)
);

CREATE TABLE release.research_projection_set (
  research_release_id uuid PRIMARY KEY
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  database_snapshot_identity text NOT NULL CHECK (btrim(database_snapshot_identity) <> ''),
  migration_set_sha256 core.sha256_hex NOT NULL,
  projection_query_pack_sha256 core.sha256_hex NOT NULL
);

CREATE TABLE release.research_registry_snapshot (
  research_release_id uuid PRIMARY KEY
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  predicate_registry_sha256 core.sha256_hex NOT NULL,
  relation_registry_sha256 core.sha256_hex NOT NULL,
  epistemic_registry_sha256 core.sha256_hex NOT NULL
);

CREATE TABLE release.research_corpus_snapshot (
  research_release_id uuid NOT NULL
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  corpus_version_id uuid NOT NULL
    REFERENCES research.corpus_version(corpus_version_id) ON DELETE RESTRICT,
  corpus_token core.release_token NOT NULL,
  corpus_version_token core.release_token NOT NULL,
  selection_policy_sha256 core.sha256_hex NOT NULL,
  population_frame text NOT NULL CHECK (btrim(population_frame) <> ''),
  missingness_snapshot_sha256 core.sha256_hex NOT NULL,
  coverage_snapshot_sha256 core.sha256_hex NOT NULL,
  concentration_receipt_sha256 core.sha256_hex NOT NULL,
  PRIMARY KEY (research_release_id, corpus_version_id)
);

ALTER TABLE release.research_release_corpus_member
  ADD CONSTRAINT research_release_corpus_snapshot_fk
  FOREIGN KEY (research_release_id, corpus_version_id)
  REFERENCES release.research_corpus_snapshot
    (research_release_id, corpus_version_id) ON DELETE RESTRICT;

CREATE TABLE release.research_count_snapshot (
  research_release_id uuid NOT NULL
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  metric_code core.release_token NOT NULL,
  scope_definition text NOT NULL CHECK (btrim(scope_definition) <> ''),
  unit_definition text NOT NULL CHECK (btrim(unit_definition) <> ''),
  query_sha256 core.sha256_hex NOT NULL,
  exact_count bigint NOT NULL CHECK (exact_count >= 0),
  PRIMARY KEY (research_release_id, metric_code)
);

CREATE TABLE release.research_asset (
  research_release_id uuid NOT NULL
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  relative_path text NOT NULL CHECK (
    btrim(relative_path) <> '' AND relative_path !~ '(^/|(^|/)\.\.(/|$))'),
  resource_kind core.release_token NOT NULL,
  media_type text NOT NULL CHECK (btrim(media_type) <> ''),
  content_encoding text NOT NULL CHECK (btrim(content_encoding) <> ''),
  schema_id text NOT NULL CHECK (btrim(schema_id) <> ''),
  byte_length bigint NOT NULL CHECK (byte_length BETWEEN 0 AND 9007199254740991),
  record_count bigint NOT NULL CHECK (record_count BETWEEN 0 AND 9007199254740991),
  sha256 core.sha256_hex NOT NULL,
  deterministic_sort_key text NOT NULL CHECK (btrim(deterministic_sort_key) <> ''),
  partition_description text,
  uncompressed_sha256 core.sha256_hex,
  PRIMARY KEY (research_release_id, relative_path)
);

CREATE TABLE release.research_asset_dependency (
  research_release_id uuid NOT NULL,
  asset_path text NOT NULL,
  dependency_path text NOT NULL,
  dependency_sha256 core.sha256_hex NOT NULL,
  PRIMARY KEY (research_release_id, asset_path, dependency_path),
  FOREIGN KEY (research_release_id, asset_path)
    REFERENCES release.research_asset(research_release_id, relative_path) ON DELETE RESTRICT,
  FOREIGN KEY (research_release_id, dependency_path)
    REFERENCES release.research_asset(research_release_id, relative_path) ON DELETE RESTRICT,
  CHECK (asset_path <> dependency_path)
);

CREATE TABLE release.visual_registry_policy_input (
  visual_registry_release_id uuid PRIMARY KEY
    REFERENCES release.visual_registry_release(visual_registry_release_id) ON DELETE RESTRICT,
  legacy_disposition_receipt_sha256 core.sha256_hex NOT NULL,
  provider_registry_sha256 core.sha256_hex NOT NULL,
  rights_policy_sha256 core.sha256_hex NOT NULL,
  delivery_truth_table_sha256 core.sha256_hex NOT NULL,
  serializer_contract_sha256 core.sha256_hex NOT NULL
);

CREATE TABLE release.visual_registry_asset (
  visual_registry_release_id uuid NOT NULL
    REFERENCES release.visual_registry_release(visual_registry_release_id) ON DELETE RESTRICT,
  relative_path text NOT NULL CHECK (
    btrim(relative_path) <> '' AND relative_path !~ '(^/|(^|/)\.\.(/|$))'),
  resource_kind core.release_token NOT NULL,
  media_type text NOT NULL CHECK (btrim(media_type) <> ''),
  content_encoding text NOT NULL CHECK (btrim(content_encoding) <> ''),
  schema_id text NOT NULL CHECK (btrim(schema_id) <> ''),
  byte_length bigint NOT NULL CHECK (byte_length BETWEEN 0 AND 9007199254740991),
  record_count bigint NOT NULL CHECK (record_count BETWEEN 0 AND 9007199254740991),
  sha256 core.sha256_hex NOT NULL,
  deterministic_sort_key text NOT NULL CHECK (btrim(deterministic_sort_key) <> ''),
  partition_description text,
  uncompressed_sha256 core.sha256_hex,
  PRIMARY KEY (visual_registry_release_id, relative_path)
);

CREATE TABLE release.visual_registry_asset_dependency (
  visual_registry_release_id uuid NOT NULL,
  asset_path text NOT NULL,
  dependency_path text NOT NULL,
  dependency_sha256 core.sha256_hex NOT NULL,
  PRIMARY KEY (visual_registry_release_id, asset_path, dependency_path),
  FOREIGN KEY (visual_registry_release_id, asset_path)
    REFERENCES release.visual_registry_asset
      (visual_registry_release_id, relative_path) ON DELETE RESTRICT,
  FOREIGN KEY (visual_registry_release_id, dependency_path)
    REFERENCES release.visual_registry_asset
      (visual_registry_release_id, relative_path) ON DELETE RESTRICT,
  CHECK (asset_path <> dependency_path)
);

CREATE TABLE rights.legacy_visual_surface_disposition (
  legacy_surface_ledger_id uuid PRIMARY KEY
    REFERENCES raw.legacy_surface_ledger(legacy_surface_ledger_id) ON DELETE RESTRICT,
  source_fingerprint core.sha256_hex NOT NULL,
  visual_reference_count integer NOT NULL CHECK (visual_reference_count >= 0),
  locator_occurrence_count integer NOT NULL CHECK (locator_occurrence_count >= 0),
  disposition_set_sha256 core.sha256_hex NOT NULL,
  classified_at timestamptz NOT NULL
);

CREATE TABLE rights.legacy_visual_surface_classification (
  legacy_surface_ledger_id uuid NOT NULL
    REFERENCES rights.legacy_visual_surface_disposition
      (legacy_surface_ledger_id) ON DELETE RESTRICT,
  disposition rights.legacy_visual_disposition NOT NULL,
  evidence_item_id uuid
    REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  PRIMARY KEY (legacy_surface_ledger_id, disposition)
);

CREATE TABLE release.visual_registry_legacy_disposition_snapshot (
  visual_registry_release_id uuid PRIMARY KEY
    REFERENCES release.visual_registry_release(visual_registry_release_id) ON DELETE RESTRICT,
  accounted_surface_count bigint NOT NULL CHECK (accounted_surface_count >= 0),
  reference_bearing_surface_count bigint NOT NULL CHECK (reference_bearing_surface_count >= 0),
  no_visual_reference_count bigint NOT NULL CHECK (no_visual_reference_count >= 0),
  unclassified_surface_count bigint NOT NULL CHECK (unclassified_surface_count = 0),
  disposition_set_sha256 core.sha256_hex NOT NULL,
  receipt_sha256 core.sha256_hex NOT NULL,
  CHECK (reference_bearing_surface_count + no_visual_reference_count
    <= accounted_surface_count)
);

CREATE TABLE rights.provider_policy_scope (
  policy_scope_id uuid PRIMARY KEY,
  provider_id uuid NOT NULL
    REFERENCES rights.provider(provider_id) ON DELETE RESTRICT,
  scope_token core.release_token NOT NULL,
  scope_description text NOT NULL CHECK (btrim(scope_description) <> ''),
  created_at timestamptz NOT NULL,
  UNIQUE (provider_id, policy_scope_id),
  UNIQUE (provider_id, scope_token)
);

ALTER TABLE rights.provider_policy_version
  ADD COLUMN policy_scope_id uuid NOT NULL,
  ALTER COLUMN source_evidence_item_id SET NOT NULL,
  ADD CONSTRAINT provider_policy_scope_provider_fk
    FOREIGN KEY (provider_id, policy_scope_id)
    REFERENCES rights.provider_policy_scope(provider_id, policy_scope_id)
    ON DELETE RESTRICT,
  ADD CONSTRAINT provider_policy_version_natural_key
    UNIQUE (provider_id, policy_scope_id, effective_from, policy_sha256);

ALTER TABLE release.visual_registry_policy_version_snapshot
  ADD COLUMN policy_scope_id uuid NOT NULL;

ALTER TABLE rights.takedown_event
  ALTER COLUMN evidence_item_id SET NOT NULL;
ALTER TABLE rights.takedown_scope
  ADD COLUMN scope_ordinal integer NOT NULL CHECK (scope_ordinal > 0),
  ADD CONSTRAINT takedown_scope_event_ordinal_unique
    UNIQUE (takedown_event_id, scope_ordinal);
ALTER TABLE rights.takedown_override
  ADD COLUMN override_version integer NOT NULL CHECK (override_version > 0),
  ADD CONSTRAINT takedown_override_scope_version_unique
    UNIQUE (takedown_scope_id, override_version);
ALTER TABLE rights.attribution_bundle
  ADD CONSTRAINT attribution_bundle_one_successor
    UNIQUE (supersedes_attribution_bundle_id);

ALTER TABLE research.corpus_version
  ADD CONSTRAINT corpus_version_exact_policy_pair
    UNIQUE (corpus_version_id, policy_sha256);
ALTER TABLE research.analysis_run
  ADD COLUMN software_sha256 core.sha256_hex NOT NULL,
  ADD COLUMN input_corpus_version_id uuid NOT NULL,
  ADD COLUMN input_corpus_policy_sha256 core.sha256_hex NOT NULL,
  ADD COLUMN score_value numeric NOT NULL,
  ADD COLUMN score_unit text NOT NULL CHECK (btrim(score_unit) <> ''),
  ADD COLUMN uncertainty_lower numeric,
  ADD COLUMN uncertainty_upper numeric,
  ADD COLUMN threshold_value numeric NOT NULL,
  ADD COLUMN threshold_unit text NOT NULL CHECK (btrim(threshold_unit) <> ''),
  ADD CONSTRAINT analysis_run_exact_corpus_policy_fk
    FOREIGN KEY (input_corpus_version_id, input_corpus_policy_sha256)
    REFERENCES research.corpus_version(corpus_version_id, policy_sha256)
    ON DELETE RESTRICT,
  ADD CONSTRAINT analysis_run_uncertainty_order CHECK (
    uncertainty_lower IS NULL OR uncertainty_upper IS NULL
    OR uncertainty_lower <= uncertainty_upper);
ALTER TABLE research.claim_revision
  ADD COLUMN claim_date_or_version text NOT NULL
    CHECK (btrim(claim_date_or_version) <> ''),
  ADD COLUMN claim_stance research.claim_relation_role NOT NULL;

ALTER TABLE release.research_release_claim
  ADD COLUMN claimant_agent_id uuid,
  ADD COLUMN claimant_label text,
  ADD COLUMN claim_date_or_version text NOT NULL,
  ADD COLUMN claim_stance research.claim_relation_role NOT NULL,
  ADD COLUMN temporal_qualifier_id uuid,
  ADD COLUMN temporal_qualifier_snapshot text,
  ADD COLUMN spatial_qualifier_id uuid,
  ADD COLUMN spatial_qualifier_snapshot text,
  ADD COLUMN analysis_run_id uuid,
  ADD COLUMN analysis_run_snapshot_sha256 core.sha256_hex;

CREATE TABLE release.research_release_claim_evidence (
  research_release_id uuid NOT NULL,
  claim_revision_id uuid NOT NULL,
  evidence_item_id uuid NOT NULL,
  evidence_role provenance.evidence_role NOT NULL,
  source_version_id uuid NOT NULL,
  source_record_id uuid,
  locator_scheme text NOT NULL,
  locator_value text,
  span_start bigint,
  span_end bigint,
  content_sha256 core.sha256_hex,
  stable_citation text,
  evidence_snapshot_sha256 core.sha256_hex NOT NULL,
  PRIMARY KEY (
    research_release_id, claim_revision_id, evidence_item_id, evidence_role),
  FOREIGN KEY (research_release_id, claim_revision_id)
    REFERENCES release.research_release_claim
      (research_release_id, claim_revision_id) ON DELETE RESTRICT
);

CREATE TABLE release.research_release_analysis_run (
  research_release_id uuid NOT NULL,
  analysis_run_id uuid NOT NULL,
  method_version core.release_token NOT NULL,
  software_sha256 core.sha256_hex NOT NULL,
  parameters_sha256 core.sha256_hex NOT NULL,
  input_research_release_id uuid NOT NULL,
  input_research_manifest_sha256 core.sha256_hex NOT NULL,
  input_corpus_version_id uuid NOT NULL,
  input_corpus_policy_sha256 core.sha256_hex NOT NULL,
  score_value numeric NOT NULL,
  score_unit text NOT NULL,
  uncertainty_lower numeric,
  uncertainty_upper numeric,
  threshold_value numeric NOT NULL,
  threshold_unit text NOT NULL,
  output_sha256 core.sha256_hex NOT NULL,
  run_snapshot_sha256 core.sha256_hex NOT NULL,
  PRIMARY KEY (research_release_id, analysis_run_id),
  FOREIGN KEY (research_release_id)
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT
);

ALTER TABLE release.research_release_relation
  ADD COLUMN relation_type_id uuid NOT NULL,
  ADD COLUMN relation_evidence_profile_version core.release_token NOT NULL,
  ADD COLUMN temporal_qualifier_id uuid,
  ADD COLUMN temporal_qualifier_snapshot text,
  ADD COLUMN spatial_qualifier_id uuid,
  ADD COLUMN spatial_qualifier_snapshot text;

CREATE TABLE release.research_release_relation_evidence (
  research_release_id uuid NOT NULL,
  semantic_relation_id uuid NOT NULL,
  evidence_item_id uuid NOT NULL,
  evidence_role provenance.evidence_role NOT NULL,
  evidence_basis research.relation_acceptance_basis NOT NULL,
  stable_citation text,
  locator_value text,
  content_sha256 core.sha256_hex,
  evidence_snapshot_sha256 core.sha256_hex NOT NULL,
  PRIMARY KEY (
    research_release_id, semantic_relation_id,
    evidence_item_id, evidence_role, evidence_basis),
  FOREIGN KEY (research_release_id, semantic_relation_id)
    REFERENCES release.research_release_relation
      (research_release_id, semantic_relation_id) ON DELETE RESTRICT
);

CREATE TABLE release.research_legacy_identity_resolution (
  research_release_id uuid NOT NULL,
  legacy_identity_id uuid NOT NULL,
  legacy_identity_resolution_id uuid NOT NULL,
  identity_kind core.legacy_identity_kind NOT NULL,
  namespace text NOT NULL,
  legacy_id text NOT NULL,
  resolution_state core.identity_resolution_state NOT NULL,
  target_archive_object_id uuid,
  target_source_record_id uuid,
  target_trace_node_id uuid,
  target_folder_id uuid,
  target_trace_edge_corpus_version_id uuid,
  target_trace_edge_subject_node_id uuid,
  target_trace_edge_relation_id uuid,
  target_trace_edge_object_node_id uuid,
  target_trace_edge_projection_role text,
  reason_code text NOT NULL,
  effective_from timestamptz NOT NULL,
  PRIMARY KEY (research_release_id, legacy_identity_id),
  UNIQUE (research_release_id, legacy_identity_resolution_id),
  FOREIGN KEY (research_release_id)
    REFERENCES release.research_release(research_release_id) ON DELETE RESTRICT,
  FOREIGN KEY (research_release_id, target_archive_object_id)
    REFERENCES release.research_release_object
      (research_release_id, archive_object_id) ON DELETE RESTRICT,
  FOREIGN KEY (
    research_release_id, target_trace_edge_corpus_version_id,
    target_trace_edge_subject_node_id, target_trace_edge_relation_id,
    target_trace_edge_object_node_id, target_trace_edge_projection_role
  ) REFERENCES release.trace_projection_edge (
    research_release_id, corpus_version_id, subject_trace_node_id,
    semantic_relation_id, object_trace_node_id, projection_role
  ) ON DELETE RESTRICT
);

CREATE TABLE release.research_legacy_identity_split_successor (
  research_release_id uuid NOT NULL,
  legacy_identity_resolution_id uuid NOT NULL,
  successor_ordinal integer NOT NULL CHECK (successor_ordinal > 0),
  successor_archive_object_id uuid NOT NULL,
  successor_object_urn core.canonical_urn NOT NULL,
  PRIMARY KEY (
    research_release_id, legacy_identity_resolution_id, successor_ordinal),
  FOREIGN KEY (research_release_id, legacy_identity_resolution_id)
    REFERENCES release.research_legacy_identity_resolution
      (research_release_id, legacy_identity_resolution_id) ON DELETE RESTRICT,
  FOREIGN KEY (research_release_id, successor_archive_object_id)
    REFERENCES release.research_release_object
      (research_release_id, archive_object_id) ON DELETE RESTRICT
);

ALTER TABLE rights.delivery_assessment
  DROP CONSTRAINT delivery_assessment_reason_code_check,
  ALTER COLUMN reason_code TYPE rights.delivery_rule_id
    USING reason_code::rights.delivery_rule_id,
  ADD COLUMN machine_reason_code rights.delivery_reason_code NOT NULL;
ALTER TABLE release.visual_registry_entry
  DROP CONSTRAINT
    visual_registry_entry_visual_registry_release_id_delivery__fkey;
ALTER TABLE release.visual_registry_delivery_snapshot
  DROP CONSTRAINT visual_registry_delivery_snapshot_reason_code_check,
  DROP CONSTRAINT
    visual_registry_delivery_snap_visual_registry_release_id_de_key,
  ALTER COLUMN reason_code TYPE rights.delivery_rule_id
    USING reason_code::rights.delivery_rule_id,
  ADD COLUMN machine_reason_code rights.delivery_reason_code NOT NULL,
  ADD CONSTRAINT visual_registry_delivery_snapshot_exact_outcome_unique
    UNIQUE (
      visual_registry_release_id, delivery_assessment_id,
      object_visual_reference_id, base_delivery_mode, reason_code,
      machine_reason_code, rights_outcome_sha256, policy_outcome_sha256,
      attribution_bundle_sha256);
ALTER TABLE release.visual_registry_entry
  DROP CONSTRAINT visual_registry_entry_reason_code_check,
  ALTER COLUMN reason_code TYPE rights.delivery_rule_id
    USING reason_code::rights.delivery_rule_id,
  ADD COLUMN machine_reason_code rights.delivery_reason_code NOT NULL,
  ADD CONSTRAINT visual_registry_entry_exact_delivery_snapshot_fk
    FOREIGN KEY (
      visual_registry_release_id, delivery_assessment_id,
      object_visual_reference_id, base_delivery_mode, reason_code,
      machine_reason_code, rights_outcome_sha256, policy_outcome_sha256,
      attribution_bundle_sha256
    ) REFERENCES release.visual_registry_delivery_snapshot (
      visual_registry_release_id, delivery_assessment_id,
      object_visual_reference_id, base_delivery_mode, reason_code,
      machine_reason_code, rights_outcome_sha256, policy_outcome_sha256,
      attribution_bundle_sha256
    ) ON DELETE RESTRICT;

ALTER TABLE release.research_validation_receipt
  ADD COLUMN receipt_kind release.validation_receipt_kind NOT NULL,
  ADD COLUMN receipt_bytes bytea NOT NULL,
  ADD COLUMN byte_length bigint NOT NULL CHECK (byte_length >= 0),
  ADD CONSTRAINT research_validation_receipt_bytes_match CHECK (
    octet_length(receipt_bytes) = byte_length
    AND encode(sha256(receipt_bytes), 'hex') = receipt_sha256),
  ADD CONSTRAINT research_validation_receipt_kind_unique
    UNIQUE (research_release_id, receipt_kind);
ALTER TABLE release.visual_validation_receipt
  ADD COLUMN receipt_kind release.validation_receipt_kind NOT NULL,
  ADD COLUMN receipt_bytes bytea NOT NULL,
  ADD COLUMN byte_length bigint NOT NULL CHECK (byte_length >= 0),
  ADD CONSTRAINT visual_validation_receipt_bytes_match CHECK (
    octet_length(receipt_bytes) = byte_length
    AND encode(sha256(receipt_bytes), 'hex') = receipt_sha256),
  ADD CONSTRAINT visual_validation_receipt_kind_unique
    UNIQUE (visual_registry_release_id, receipt_kind);

ALTER TABLE audit.research_seal_event
  ADD COLUMN seal_transaction_id bigint NOT NULL,
  ADD COLUMN candidate_fingerprint core.sha256_hex NOT NULL,
  ADD COLUMN seal_function_version core.release_token NOT NULL;
ALTER TABLE audit.visual_seal_event
  ADD COLUMN seal_transaction_id bigint NOT NULL,
  ADD COLUMN candidate_fingerprint core.sha256_hex NOT NULL,
  ADD COLUMN seal_function_version core.release_token NOT NULL;
ALTER TABLE release.research_release_verification
  ADD COLUMN seal_transaction_id bigint NOT NULL,
  ADD COLUMN candidate_fingerprint core.sha256_hex NOT NULL,
  ADD COLUMN seal_function_version core.release_token NOT NULL,
  ADD COLUMN attestation_sha256 core.sha256_hex;
ALTER TABLE release.visual_registry_verification
  ADD COLUMN seal_transaction_id bigint NOT NULL,
  ADD COLUMN candidate_fingerprint core.sha256_hex NOT NULL,
  ADD COLUMN seal_function_version core.release_token NOT NULL,
  ADD COLUMN attestation_sha256 core.sha256_hex;

CREATE TABLE audit.research_validation_receipt_event (
  research_validation_receipt_event_id uuid PRIMARY KEY,
  research_validation_receipt_id uuid NOT NULL UNIQUE
    REFERENCES release.research_validation_receipt
      (research_validation_receipt_id) ON DELETE RESTRICT,
  actor text NOT NULL CHECK (btrim(actor) <> ''),
  occurred_at timestamptz NOT NULL,
  event_sha256 core.sha256_hex NOT NULL
);
CREATE TABLE audit.visual_validation_receipt_event (
  visual_validation_receipt_event_id uuid PRIMARY KEY,
  visual_validation_receipt_id uuid NOT NULL UNIQUE
    REFERENCES release.visual_validation_receipt
      (visual_validation_receipt_id) ON DELETE RESTRICT,
  actor text NOT NULL CHECK (btrim(actor) <> ''),
  occurred_at timestamptz NOT NULL,
  event_sha256 core.sha256_hex NOT NULL
);

RESET ROLE;
