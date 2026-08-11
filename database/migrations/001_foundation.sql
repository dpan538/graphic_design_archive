\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

CREATE SCHEMA raw AUTHORIZATION gda_v49_phase2a_schema_owner;
CREATE SCHEMA core AUTHORIZATION gda_v49_phase2a_schema_owner;
CREATE SCHEMA provenance AUTHORIZATION gda_v49_phase2a_schema_owner;
CREATE SCHEMA research AUTHORIZATION gda_v49_phase2a_schema_owner;
CREATE SCHEMA rights AUTHORIZATION gda_v49_phase2a_schema_owner;
CREATE SCHEMA workflow AUTHORIZATION gda_v49_phase2a_schema_owner;
CREATE SCHEMA release AUTHORIZATION gda_v49_phase2a_schema_owner;
CREATE SCHEMA audit AUTHORIZATION gda_v49_phase2a_schema_owner;
CREATE SCHEMA api_v1 AUTHORIZATION gda_v49_phase2a_schema_owner;

CREATE DOMAIN core.sha256_hex AS text
  CHECK (VALUE ~ '^[0-9a-f]{64}$');

CREATE DOMAIN core.release_token AS text
  CHECK (VALUE ~ '^[a-z0-9][a-z0-9._-]{0,127}$');

CREATE DOMAIN core.canonical_urn AS text
  CHECK (VALUE ~ '^urn:gdarchive:(object|relation|claim|source|visual-reference):[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$');

CREATE TYPE raw.asset_authority AS ENUM (
  'canonical_migration_input',
  'immutable_reconciliation_evidence',
  'integrity_evidence',
  'governed_source'
);

CREATE TYPE raw.import_disposition AS ENUM (
  'candidate', 'accounted', 'held', 'rejected'
);

CREATE TYPE raw.delta_disposition AS ENUM (
  'proposed', 'held', 'rejected', 'resolved'
);

CREATE TYPE core.entity_kind AS ENUM (
  'archive_object', 'agent', 'place', 'concept', 'collection', 'temporal_extent'
);

CREATE TYPE core.lifecycle_state AS ENUM (
  'active', 'withdrawn', 'merged', 'split', 'unresolved'
);

CREATE TYPE core.identity_resolution_state AS ENUM (
  'primary', 'alias', 'redirect', 'merged', 'split', 'withdrawn', 'unresolved'
);

CREATE TYPE core.legacy_identity_kind AS ENUM (
  'archive_object', 'source_record', 'trace_node', 'trace_edge', 'folder'
);

CREATE TYPE core.object_identity_candidate_kind AS ENUM (
  'duplicate_candidate', 'same_work_candidate', 'edition', 'version'
);

CREATE TYPE provenance.assertion_status AS ENUM (
  'proposed', 'accepted', 'rejected', 'superseded'
);

CREATE TYPE provenance.evidence_role AS ENUM (
  'supports', 'contradicts', 'contextualises'
);

CREATE TYPE provenance.assertion_subject_kind AS ENUM (
  'entity', 'source_record', 'trace_node', 'digital_representation'
);
CREATE TYPE provenance.assertion_value_kind AS ENUM (
  'entity', 'literal', 'source_record', 'trace_node'
);
CREATE TYPE provenance.assignment_kind AS ENUM (
  'entity_name', 'object_source_record', 'object_agent_credit',
  'object_medium', 'object_type', 'object_subject', 'object_collection',
  'object_temporal', 'object_place', 'folder_membership',
  'object_tree_membership', 'object_representation', 'identity_resolution'
);

CREATE TYPE workflow.queue_state AS ENUM (
  'queued', 'claimed', 'in_review', 'resolved', 'superseded'
);

CREATE TYPE workflow.review_outcome AS ENUM (
  'accept', 'hold', 'reject', 'supersede'
);

CREATE TYPE workflow.case_kind AS ENUM (
  'assertion', 'canonical_assignment', 'claim_revision',
  'semantic_relation', 'relation_type_literal', 'rights_assessment'
);

CREATE TYPE research.membership_disposition AS ENUM (
  'eligible', 'held', 'rejected', 'excluded'
);

CREATE TYPE research.relation_endpoint_kind AS ENUM ('entity');

CREATE TYPE research.relation_status AS ENUM (
  'proposed', 'accepted', 'rejected', 'superseded'
);

CREATE TYPE research.relation_origin AS ENUM (
  'canonical_assertion_candidate',
  'curator_created',
  'computed_association',
  'legacy_projection_only'
);

CREATE TYPE research.claim_status AS ENUM (
  'draft', 'proposed', 'accepted', 'rejected', 'superseded'
);

CREATE TYPE research.claim_relation_role AS ENUM (
  'supports', 'challenges', 'contextualises'
);

CREATE TYPE research.relation_acceptance_basis AS ENUM (
  'accepted_claim', 'curator_decision'
);

CREATE TYPE research.legacy_graph_disposition AS ENUM (
  'canonical_assertion_candidate',
  'legacy_projection_only',
  'computed_association',
  'held_unsupported',
  'rejected'
);

CREATE TYPE rights.locator_role AS ENUM (
  'canonical_record', 'source_viewer', 'provider_embed', 'direct_image',
  'thumbnail', 'iiif_manifest', 'iiif_canvas', 'iiif_image_service',
  'iiif_info', 'governed_local_asset'
);

CREATE TYPE rights.locator_visibility AS ENUM ('internal', 'held', 'public_candidate');
CREATE TYPE rights.reference_role AS ENUM (
  'primary_depiction', 'alternate_depiction', 'documentary_context',
  'source_record_visual', 'citation_visual'
);
CREATE TYPE rights.representation_role AS ENUM (
  'source_bytes', 'reference_representation', 'derived_representation'
);
CREATE TYPE rights.rights_subject_kind AS ENUM (
  'provider_object', 'external_visual_reference', 'digital_representation', 'visual_locator'
);

CREATE TYPE rights.rights_evidence_state AS ENUM (
  'permitted', 'restricted', 'unknown', 'missing', 'conflict', 'stale'
);

CREATE TYPE rights.policy_state AS ENUM (
  'remote_display_allowed', 'source_viewer_only', 'link_only',
  'citation_only', 'disallowed', 'unknown', 'missing', 'conflict', 'stale'
);

CREATE TYPE rights.attribution_state AS ENUM ('complete', 'incomplete', 'unknown');

CREATE TYPE rights.delivery_mode AS ENUM (
  'blocked', 'citation_only', 'link_only', 'source_viewer', 'remote_image'
);

CREATE TYPE rights.health_state AS ENUM (
  'healthy_fresh', 'redirected', 'unreachable', 'stale', 'unknown'
);

CREATE TYPE rights.takedown_scope_kind AS ENUM (
  'provider', 'provider_object', 'external_visual_reference',
  'digital_representation', 'visual_locator', 'object_visual_reference'
);
CREATE TYPE rights.takedown_action AS ENUM ('blocked', 'citation_only');

CREATE TYPE release.release_state AS ENUM ('draft', 'candidate', 'validated', 'sealed');
CREATE TYPE release.validation_result AS ENUM ('pass', 'fail');
CREATE TYPE release.visual_composition_state AS ENUM ('not_selected', 'unavailable', 'compatible');
CREATE TYPE release.publication_layer AS ENUM ('active', 'review', 'auxiliary', 'excluded');
CREATE TYPE release.count_eligibility AS ENUM ('eligible', 'ineligible');

CREATE TYPE audit.decision_kind AS ENUM (
  'assertion_review', 'assignment_review', 'claim_review', 'relation_review',
  'rights_observation',
  'rights_assessment', 'provider_policy_evaluation',
  'delivery_assessment', 'attribution_validation', 'takedown'
);

RESET ROLE;
