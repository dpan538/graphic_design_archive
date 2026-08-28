\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

-- Forward-only v50 research capability.  The frozen v49 binary relation and
-- release surfaces are intentionally unchanged.  Associations are semantic
-- research objects; compositions are separately governed realizations.
CREATE SCHEMA exploration_v3 AUTHORIZATION gda_v49_phase2a_schema_owner;
CREATE SCHEMA api_v3 AUTHORIZATION gda_v49_phase2a_schema_owner;

CREATE TYPE exploration_v3.realm AS ENUM ('PRODUCTION', 'SYNTHETIC_CONTROL');
CREATE TYPE exploration_v3.authority_kind AS ENUM (
  'SYNTHETIC_TEST_AUTHORITY', 'RESEARCH_REVIEW', 'EXTERNAL_HUMAN_REVIEW'
);
CREATE TYPE exploration_v3.authority_state AS ENUM ('PENDING', 'FINAL');
CREATE TYPE exploration_v3.lifecycle_state AS ENUM (
  'INQUIRY_ONLY', 'INACTIVE', 'ACTIVE', 'REJECTED'
);
CREATE TYPE exploration_v3.association_kind AS ENUM ('PAIR', 'HIGHER_ORDER');
CREATE TYPE exploration_v3.order_semantics AS ENUM ('UNORDERED', 'ORDERED');
CREATE TYPE exploration_v3.pair_projection_policy AS ENUM ('NOT_APPLICABLE', 'NONE');
CREATE TYPE exploration_v3.support_mode AS ENUM (
  'DIRECT_PAIR', 'DIRECT_GROUP', 'COHERENT_COMPOSITE', 'MIXED', 'PAIR_ONLY', 'NONE'
);
CREATE TYPE exploration_v3.review_state AS ENUM ('PENDING', 'NONFINAL', 'FINAL');
CREATE TYPE exploration_v3.association_disposition AS ENUM (
  'DIRECT_PAIRWISE_SUPPORT',
  'DIRECT_HIGHER_ORDER_SUPPORT',
  'COHERENT_COMPOSITE_SUPPORT',
  'MIXED_DIRECT_AND_COMPOSITE_SUPPORT',
  'PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE',
  'INQUIRY_ONLY_OR_UNRESOLVED',
  'INSUFFICIENT_EVIDENCE',
  'COOCCURRENCE_ONLY',
  'BOUNDED_SENSE_OR_SCOPE_CONFLICT',
  'TOPOLOGY_OR_ROLE_CONFLICT',
  'HARD_NEGATIVE',
  'PENDING_GOVERNED_REVIEW'
);
CREATE TYPE exploration_v3.coherence_result AS ENUM ('PASS', 'FAIL', 'UNRESOLVED');
CREATE TYPE exploration_v3.activation_decision AS ENUM ('ALLOW', 'REJECT', 'NOT_REQUESTED');
CREATE TYPE exploration_v3.uncertainty_status AS ENUM (
  'RESOLVED_BOUNDED', 'UNRESOLVED', 'UNKNOWN'
);
CREATE TYPE exploration_v3.uncertainty_level AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'UNKNOWN');
CREATE TYPE exploration_v3.uncertainty_activation_policy AS ENUM (
  'ALLOWED_BOUNDED', 'BLOCKS_ACTIVATION'
);
CREATE TYPE exploration_v3.product_eligibility_disposition AS ENUM (
  'ELIGIBLE', 'INELIGIBLE', 'DEFERRED', 'NOT_APPLICABLE_SYNTHETIC'
);
CREATE TYPE exploration_v3.realization_kind AS ENUM (
  'PAIR_EDGE', 'HYPEREDGE_HUB', 'HYPEREDGE_CONTOUR', 'LIST_GROUP'
);
CREATE TYPE exploration_v3.renderability_result AS ENUM ('PASS', 'FAIL');
CREATE TYPE exploration_v3.composition_decision AS ENUM ('COHERENT', 'INCOHERENT', 'UNRESOLVED');
CREATE TYPE exploration_v3.navigation_node_kind AS ENUM ('CONCEPT', 'ASSOCIATION');
CREATE TYPE exploration_v3.transition_kind AS ENUM ('FOLLOW_INCIDENCE', 'MOVE_FOCUS', 'EXPORT');

CREATE TABLE exploration_v3.governed_authority (
  authority_id text PRIMARY KEY CHECK (btrim(authority_id) <> ''),
  authority_kind exploration_v3.authority_kind NOT NULL,
  authority_state exploration_v3.authority_state NOT NULL,
  authority_version text NOT NULL CHECK (btrim(authority_version) <> ''),
  authority_sha256 core.sha256_hex NOT NULL,
  decided_at timestamptz,
  CHECK ((authority_state = 'FINAL') = (decided_at IS NOT NULL)),
  UNIQUE (authority_id, authority_state),
  UNIQUE (authority_id, authority_version)
);

CREATE TABLE exploration_v3.governed_scope (
  scope_id text PRIMARY KEY CHECK (btrim(scope_id) <> ''),
  realm exploration_v3.realm NOT NULL,
  historical_case_ids text[] NOT NULL DEFAULT '{}',
  time_start text,
  time_end text,
  geographies text[] NOT NULL DEFAULT '{}',
  institutions text[] NOT NULL DEFAULT '{}',
  actors text[] NOT NULL DEFAULT '{}',
  mechanisms text[] NOT NULL DEFAULT '{}',
  context_qualifications text[] NOT NULL DEFAULT '{}',
  semantic_sha256 core.sha256_hex NOT NULL UNIQUE,
  CHECK (array_position(historical_case_ids, NULL) IS NULL),
  CHECK (array_position(geographies, NULL) IS NULL),
  CHECK (array_position(institutions, NULL) IS NULL),
  CHECK (array_position(actors, NULL) IS NULL),
  CHECK (array_position(mechanisms, NULL) IS NULL),
  CHECK (array_position(context_qualifications, NULL) IS NULL)
);

CREATE TABLE exploration_v3.concept (
  concept_id text PRIMARY KEY CHECK (btrim(concept_id) <> ''),
  realm exploration_v3.realm NOT NULL,
  canonical_label text NOT NULL CHECK (btrim(canonical_label) <> ''),
  lifecycle_state exploration_v3.lifecycle_state NOT NULL,
  association_eligible boolean NOT NULL,
  authority_id text NOT NULL REFERENCES exploration_v3.governed_authority(authority_id) ON DELETE RESTRICT,
  semantic_version text NOT NULL CHECK (btrim(semantic_version) <> ''),
  semantic_sha256 core.sha256_hex NOT NULL UNIQUE,
  product_eligible boolean NOT NULL,
  product_eligibility_disposition exploration_v3.product_eligibility_disposition NOT NULL,
  product_path text,
  product_ineligibility_reason text,
  CHECK (product_path IS NULL OR btrim(product_path) <> ''),
  CHECK (product_ineligibility_reason IS NULL OR btrim(product_ineligibility_reason) <> ''),
  CHECK (
    (realm = 'PRODUCTION' AND (
      (product_eligible AND lifecycle_state = 'ACTIVE' AND association_eligible
        AND product_eligibility_disposition = 'ELIGIBLE'
        AND product_path IS NOT NULL AND product_ineligibility_reason IS NULL)
      OR
      (NOT product_eligible AND product_eligibility_disposition IN ('INELIGIBLE','DEFERRED')
        AND product_path IS NULL AND product_ineligibility_reason IS NOT NULL)
    ))
    OR
    (realm = 'SYNTHETIC_CONTROL' AND NOT product_eligible
      AND product_eligibility_disposition = 'NOT_APPLICABLE_SYNTHETIC'
      AND product_path IS NULL AND product_ineligibility_reason IS NOT NULL)
  )
);

CREATE TABLE exploration_v3.concept_sense (
  sense_id text PRIMARY KEY CHECK (btrim(sense_id) <> ''),
  concept_id text NOT NULL REFERENCES exploration_v3.concept(concept_id) ON DELETE RESTRICT,
  realm exploration_v3.realm NOT NULL,
  bounded_definition text NOT NULL CHECK (btrim(bounded_definition) <> ''),
  lifecycle_state exploration_v3.lifecycle_state NOT NULL,
  association_eligible boolean NOT NULL,
  authority_id text NOT NULL REFERENCES exploration_v3.governed_authority(authority_id) ON DELETE RESTRICT,
  semantic_version text NOT NULL CHECK (btrim(semantic_version) <> ''),
  semantic_sha256 core.sha256_hex NOT NULL UNIQUE,
  vocabulary_crosswalk_ids text[] NOT NULL DEFAULT '{}',
  product_eligible boolean NOT NULL,
  product_eligibility_disposition exploration_v3.product_eligibility_disposition NOT NULL,
  product_path text,
  product_ineligibility_reason text,
  CHECK (array_position(vocabulary_crosswalk_ids, NULL) IS NULL),
  CHECK (product_path IS NULL OR btrim(product_path) <> ''),
  CHECK (product_ineligibility_reason IS NULL OR btrim(product_ineligibility_reason) <> ''),
  CHECK (
    (realm = 'PRODUCTION' AND (
      (product_eligible AND lifecycle_state = 'ACTIVE' AND association_eligible
        AND product_eligibility_disposition = 'ELIGIBLE'
        AND product_path IS NOT NULL AND product_ineligibility_reason IS NULL)
      OR
      (NOT product_eligible AND product_eligibility_disposition IN ('INELIGIBLE','DEFERRED')
        AND product_path IS NULL AND product_ineligibility_reason IS NOT NULL)
    ))
    OR
    (realm = 'SYNTHETIC_CONTROL' AND NOT product_eligible
      AND product_eligibility_disposition = 'NOT_APPLICABLE_SYNTHETIC'
      AND product_path IS NULL AND product_ineligibility_reason IS NOT NULL)
  ),
  UNIQUE (sense_id, concept_id)
);

CREATE TABLE exploration_v3.concept_sense_scope (
  sense_id text NOT NULL REFERENCES exploration_v3.concept_sense(sense_id) ON DELETE RESTRICT,
  scope_id text NOT NULL REFERENCES exploration_v3.governed_scope(scope_id) ON DELETE RESTRICT,
  PRIMARY KEY (sense_id, scope_id)
);

CREATE TABLE exploration_v3.evidence_reference (
  evidence_reference_id text PRIMARY KEY CHECK (btrim(evidence_reference_id) <> ''),
  realm exploration_v3.realm NOT NULL,
  provenance_evidence_item_id uuid REFERENCES provenance.evidence_item(evidence_item_id) ON DELETE RESTRICT,
  source_asset_id uuid REFERENCES raw.source_asset(source_asset_id) ON DELETE RESTRICT,
  source_record_id uuid REFERENCES raw.source_record(source_record_id) ON DELETE RESTRICT,
  evidence_sha256 core.sha256_hex NOT NULL,
  evidence_note text NOT NULL CHECK (btrim(evidence_note) <> ''),
  negative_or_conflicting boolean NOT NULL,
  rights_cleared_for_governed_use boolean NOT NULL,
  access_condition text NOT NULL CHECK (btrim(access_condition) <> ''),
  UNIQUE (evidence_reference_id, realm)
);

CREATE TABLE exploration_v3.evidence_locator (
  locator_id text PRIMARY KEY CHECK (btrim(locator_id) <> ''),
  evidence_reference_id text NOT NULL
    REFERENCES exploration_v3.evidence_reference(evidence_reference_id) ON DELETE RESTRICT,
  stable_locator text NOT NULL CHECK (btrim(stable_locator) <> ''),
  locator_sha256 core.sha256_hex NOT NULL,
  access_condition text NOT NULL CHECK (btrim(access_condition) <> ''),
  UNIQUE (evidence_reference_id, stable_locator)
);

CREATE TABLE exploration_v3.association (
  association_id text PRIMARY KEY CHECK (btrim(association_id) <> ''),
  realm exploration_v3.realm NOT NULL,
  association_kind exploration_v3.association_kind NOT NULL,
  arity integer NOT NULL CHECK (arity >= 2),
  order_semantics exploration_v3.order_semantics NOT NULL,
  roles_meaningful boolean NOT NULL,
  pair_projection_policy exploration_v3.pair_projection_policy NOT NULL,
  identity_material_sha256 core.sha256_hex NOT NULL UNIQUE,
  created_at timestamptz NOT NULL,
  CHECK (
    (association_kind = 'PAIR' AND arity = 2 AND pair_projection_policy = 'NOT_APPLICABLE')
    OR
    (association_kind = 'HIGHER_ORDER' AND arity >= 3 AND pair_projection_policy = 'NONE')
  )
);

CREATE TABLE exploration_v3.association_revision (
  association_revision_id text PRIMARY KEY CHECK (btrim(association_revision_id) <> ''),
  association_id text NOT NULL REFERENCES exploration_v3.association(association_id) ON DELETE RESTRICT,
  revision_number integer NOT NULL CHECK (revision_number > 0),
  scope_id text NOT NULL REFERENCES exploration_v3.governed_scope(scope_id) ON DELETE RESTRICT,
  lifecycle_state exploration_v3.lifecycle_state NOT NULL,
  support_mode exploration_v3.support_mode NOT NULL,
  evidence_complete boolean NOT NULL,
  same_configuration boolean NOT NULL,
  conflicts_resolved boolean NOT NULL,
  rights_cleared_for_governed_use boolean NOT NULL,
  synthesis_complete boolean NOT NULL,
  uncertainty_status exploration_v3.uncertainty_status NOT NULL,
  uncertainty_level exploration_v3.uncertainty_level NOT NULL,
  uncertainty_activation_policy exploration_v3.uncertainty_activation_policy NOT NULL,
  uncertainty_rationale text NOT NULL CHECK (btrim(uncertainty_rationale) <> ''),
  activation_decision exploration_v3.activation_decision NOT NULL,
  all_activation_gates_pass boolean NOT NULL,
  semantic_version text NOT NULL CHECK (btrim(semantic_version) <> ''),
  semantic_sha256 core.sha256_hex NOT NULL UNIQUE,
  presentation_sha256 core.sha256_hex NOT NULL,
  product_eligible boolean NOT NULL,
  product_eligibility_disposition exploration_v3.product_eligibility_disposition NOT NULL,
  product_path text,
  product_ineligibility_reason text,
  qualifications text[] NOT NULL DEFAULT '{}',
  explicit_non_claims text[] NOT NULL,
  supersedes_association_revision_id text,
  created_at timestamptz NOT NULL,
  scope_context_qualifications text[] NOT NULL DEFAULT '{}',
  CHECK (array_position(qualifications, NULL) IS NULL),
  CHECK (array_position(explicit_non_claims, NULL) IS NULL),
  CHECK (array_position(scope_context_qualifications, NULL) IS NULL),
  CHECK (cardinality(explicit_non_claims) > 0),
  CHECK (product_path IS NULL OR btrim(product_path) <> ''),
  CHECK (product_ineligibility_reason IS NULL OR btrim(product_ineligibility_reason) <> ''),
  CHECK (
    (product_eligible AND lifecycle_state = 'ACTIVE'
      AND activation_decision = 'ALLOW' AND all_activation_gates_pass
      AND product_eligibility_disposition = 'ELIGIBLE'
      AND product_path IS NOT NULL AND product_ineligibility_reason IS NULL)
    OR
    (NOT product_eligible
      AND product_eligibility_disposition IN (
        'INELIGIBLE','DEFERRED','NOT_APPLICABLE_SYNTHETIC')
      AND product_path IS NULL AND product_ineligibility_reason IS NOT NULL)
  ),
  UNIQUE (association_id, revision_number),
  UNIQUE (association_id, association_revision_id),
  FOREIGN KEY (association_id, supersedes_association_revision_id)
    REFERENCES exploration_v3.association_revision(association_id, association_revision_id)
    ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
);

CREATE UNIQUE INDEX association_revision_single_successor_uidx
  ON exploration_v3.association_revision (association_id, supersedes_association_revision_id)
  WHERE supersedes_association_revision_id IS NOT NULL;

CREATE TABLE exploration_v3.association_incidence (
  incidence_id text PRIMARY KEY CHECK (btrim(incidence_id) <> ''),
  association_revision_id text NOT NULL
    REFERENCES exploration_v3.association_revision(association_revision_id) ON DELETE RESTRICT,
  concept_id text NOT NULL REFERENCES exploration_v3.concept(concept_id) ON DELETE RESTRICT,
  sense_id text NOT NULL,
  ordinal integer CHECK (ordinal >= 0),
  role_id text,
  participant_scope_id text NOT NULL
    REFERENCES exploration_v3.governed_scope(scope_id) ON DELETE RESTRICT,
  qualifications text[] NOT NULL DEFAULT '{}',
  CHECK (role_id IS NULL OR btrim(role_id) <> ''),
  CHECK (array_position(qualifications, NULL) IS NULL),
  FOREIGN KEY (sense_id, concept_id)
    REFERENCES exploration_v3.concept_sense(sense_id, concept_id) ON DELETE RESTRICT,
  UNIQUE (association_revision_id, concept_id, sense_id),
  UNIQUE (association_revision_id, incidence_id)
);

CREATE UNIQUE INDEX association_incidence_ordered_ordinal_uidx
  ON exploration_v3.association_incidence (association_revision_id, ordinal)
  WHERE ordinal IS NOT NULL;

CREATE TABLE exploration_v3.association_revision_evidence (
  association_revision_id text NOT NULL
    REFERENCES exploration_v3.association_revision(association_revision_id) ON DELETE RESTRICT,
  evidence_reference_id text NOT NULL
    REFERENCES exploration_v3.evidence_reference(evidence_reference_id) ON DELETE RESTRICT,
  evidence_role provenance.evidence_role NOT NULL,
  PRIMARY KEY (association_revision_id, evidence_reference_id, evidence_role)
);

CREATE TABLE exploration_v3.association_synthesis_step (
  association_revision_id text NOT NULL
    REFERENCES exploration_v3.association_revision(association_revision_id) ON DELETE RESTRICT,
  step_ordinal integer NOT NULL CHECK (step_ordinal >= 0),
  synthesis_statement text NOT NULL CHECK (btrim(synthesis_statement) <> ''),
  bridge_supported boolean NOT NULL,
  PRIMARY KEY (association_revision_id, step_ordinal)
);

CREATE TABLE exploration_v3.association_synthesis_step_evidence (
  association_revision_id text NOT NULL,
  step_ordinal integer NOT NULL,
  evidence_reference_id text NOT NULL
    REFERENCES exploration_v3.evidence_reference(evidence_reference_id) ON DELETE RESTRICT,
  FOREIGN KEY (association_revision_id, step_ordinal)
    REFERENCES exploration_v3.association_synthesis_step(
      association_revision_id, step_ordinal) ON DELETE RESTRICT,
  PRIMARY KEY (association_revision_id, step_ordinal, evidence_reference_id)
);

CREATE TABLE exploration_v3.association_conflict_resolution (
  conflict_resolution_id text PRIMARY KEY CHECK (btrim(conflict_resolution_id) <> ''),
  association_revision_id text NOT NULL
    REFERENCES exploration_v3.association_revision(association_revision_id) ON DELETE RESTRICT,
  evidence_reference_id text NOT NULL
    REFERENCES exploration_v3.evidence_reference(evidence_reference_id) ON DELETE RESTRICT,
  authority_id text NOT NULL
    REFERENCES exploration_v3.governed_authority(authority_id) ON DELETE RESTRICT,
  resolution_state exploration_v3.authority_state NOT NULL,
  rationale text NOT NULL CHECK (btrim(rationale) <> ''),
  resolved_at timestamptz,
  CHECK ((resolution_state = 'FINAL') = (resolved_at IS NOT NULL)),
  UNIQUE (association_revision_id, evidence_reference_id)
);

CREATE TABLE exploration_v3.association_review (
  review_id text PRIMARY KEY CHECK (btrim(review_id) <> ''),
  association_revision_id text NOT NULL UNIQUE
    REFERENCES exploration_v3.association_revision(association_revision_id) ON DELETE RESTRICT,
  review_state exploration_v3.review_state NOT NULL,
  disposition exploration_v3.association_disposition NOT NULL,
  global_coherence exploration_v3.coherence_result NOT NULL,
  bounded_senses_compatible boolean NOT NULL,
  case_scope_compatible boolean NOT NULL,
  roles_and_topology_supported boolean NOT NULL,
  unsupported_bridge_count integer NOT NULL CHECK (unsupported_bridge_count >= 0),
  authority_id text NOT NULL
    REFERENCES exploration_v3.governed_authority(authority_id) ON DELETE RESTRICT,
  review_version text NOT NULL CHECK (btrim(review_version) <> ''),
  qualifications text[] NOT NULL DEFAULT '{}',
  explicit_non_claims text[] NOT NULL,
  semantic_sha256 core.sha256_hex NOT NULL UNIQUE,
  reviewed_at timestamptz,
  CHECK (array_position(qualifications, NULL) IS NULL),
  CHECK (array_position(explicit_non_claims, NULL) IS NULL),
  CHECK (cardinality(explicit_non_claims) > 0),
  CHECK ((review_state = 'FINAL') = (reviewed_at IS NOT NULL))
);

-- Explicit links may cite independently governed pair revisions as composite
-- support.  They never generate pair rows and never imply the unlisted pairs.
CREATE TABLE exploration_v3.internal_pair_link (
  higher_order_revision_id text NOT NULL
    REFERENCES exploration_v3.association_revision(association_revision_id) ON DELETE RESTRICT,
  pair_revision_id text NOT NULL
    REFERENCES exploration_v3.association_revision(association_revision_id) ON DELETE RESTRICT,
  higher_incidence_a text NOT NULL,
  higher_incidence_b text NOT NULL,
  pair_incidence_a text NOT NULL,
  pair_incidence_b text NOT NULL,
  CHECK (higher_incidence_a < higher_incidence_b),
  CHECK (pair_incidence_a < pair_incidence_b),
  FOREIGN KEY (higher_order_revision_id, higher_incidence_a)
    REFERENCES exploration_v3.association_incidence(association_revision_id, incidence_id) ON DELETE RESTRICT,
  FOREIGN KEY (higher_order_revision_id, higher_incidence_b)
    REFERENCES exploration_v3.association_incidence(association_revision_id, incidence_id) ON DELETE RESTRICT,
  FOREIGN KEY (pair_revision_id, pair_incidence_a)
    REFERENCES exploration_v3.association_incidence(association_revision_id, incidence_id) ON DELETE RESTRICT,
  FOREIGN KEY (pair_revision_id, pair_incidence_b)
    REFERENCES exploration_v3.association_incidence(association_revision_id, incidence_id) ON DELETE RESTRICT,
  PRIMARY KEY (higher_order_revision_id, pair_revision_id, higher_incidence_a, higher_incidence_b)
);

CREATE TABLE exploration_v3.composition (
  composition_id text PRIMARY KEY CHECK (btrim(composition_id) <> ''),
  realm exploration_v3.realm NOT NULL,
  created_at timestamptz NOT NULL
);

CREATE TABLE exploration_v3.composition_revision (
  composition_revision_id text PRIMARY KEY CHECK (btrim(composition_revision_id) <> ''),
  composition_id text NOT NULL REFERENCES exploration_v3.composition(composition_id) ON DELETE RESTRICT,
  revision_number integer NOT NULL CHECK (revision_number > 0),
  topology_family text NOT NULL CHECK (btrim(topology_family) <> ''),
  association_trace_complete boolean NOT NULL,
  renderability exploration_v3.renderability_result NOT NULL,
  semantic_sha256 core.sha256_hex NOT NULL UNIQUE,
  presentation_sha256 core.sha256_hex NOT NULL,
  product_eligible boolean NOT NULL,
  product_eligibility_disposition exploration_v3.product_eligibility_disposition NOT NULL,
  product_path text,
  product_ineligibility_reason text,
  supersedes_composition_revision_id text,
  created_at timestamptz NOT NULL,
  CHECK (product_path IS NULL OR btrim(product_path) <> ''),
  CHECK (product_ineligibility_reason IS NULL OR btrim(product_ineligibility_reason) <> ''),
  CHECK (
    (product_eligible AND association_trace_complete AND renderability = 'PASS'
      AND product_eligibility_disposition = 'ELIGIBLE'
      AND product_path IS NOT NULL AND product_ineligibility_reason IS NULL)
    OR
    (NOT product_eligible
      AND product_eligibility_disposition IN (
        'INELIGIBLE','DEFERRED','NOT_APPLICABLE_SYNTHETIC')
      AND product_path IS NULL AND product_ineligibility_reason IS NOT NULL)
  ),
  UNIQUE (composition_id, revision_number),
  UNIQUE (composition_id, composition_revision_id),
  FOREIGN KEY (composition_id, supersedes_composition_revision_id)
    REFERENCES exploration_v3.composition_revision(composition_id, composition_revision_id)
    ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
);

CREATE UNIQUE INDEX composition_revision_single_successor_uidx
  ON exploration_v3.composition_revision (composition_id, supersedes_composition_revision_id)
  WHERE supersedes_composition_revision_id IS NOT NULL;

CREATE TABLE exploration_v3.composition_node (
  composition_revision_id text NOT NULL
    REFERENCES exploration_v3.composition_revision(composition_revision_id) ON DELETE RESTRICT,
  concept_id text NOT NULL REFERENCES exploration_v3.concept(concept_id) ON DELETE RESTRICT,
  PRIMARY KEY (composition_revision_id, concept_id)
);

CREATE TABLE exploration_v3.association_realization (
  association_realization_id text PRIMARY KEY CHECK (btrim(association_realization_id) <> ''),
  composition_revision_id text NOT NULL
    REFERENCES exploration_v3.composition_revision(composition_revision_id) ON DELETE RESTRICT,
  association_revision_id text NOT NULL
    REFERENCES exploration_v3.association_revision(association_revision_id) ON DELETE RESTRICT,
  realization_kind exploration_v3.realization_kind NOT NULL,
  semantic_sha256 core.sha256_hex NOT NULL UNIQUE,
  presentation_sha256 core.sha256_hex NOT NULL,
  layout text NOT NULL CHECK (btrim(layout) <> ''),
  style text NOT NULL CHECK (btrim(style) <> ''),
  UNIQUE (composition_revision_id, association_revision_id),
  UNIQUE (composition_revision_id, association_realization_id)
);

CREATE TABLE exploration_v3.realization_incidence (
  association_realization_id text NOT NULL
    REFERENCES exploration_v3.association_realization(association_realization_id) ON DELETE RESTRICT,
  incidence_id text NOT NULL
    REFERENCES exploration_v3.association_incidence(incidence_id) ON DELETE RESTRICT,
  PRIMARY KEY (association_realization_id, incidence_id)
);

CREATE TABLE exploration_v3.composition_coherence_review (
  composition_coherence_review_id text PRIMARY KEY CHECK (btrim(composition_coherence_review_id) <> ''),
  composition_revision_id text NOT NULL UNIQUE
    REFERENCES exploration_v3.composition_revision(composition_revision_id) ON DELETE RESTRICT,
  realm exploration_v3.realm NOT NULL,
  review_state exploration_v3.review_state NOT NULL,
  authority_id text NOT NULL REFERENCES exploration_v3.governed_authority(authority_id) ON DELETE RESTRICT,
  review_version text NOT NULL CHECK (btrim(review_version) <> ''),
  global_coherence exploration_v3.coherence_result NOT NULL,
  bounded_senses_compatible boolean NOT NULL,
  case_scope_compatible boolean NOT NULL,
  roles_and_topology_supported boolean NOT NULL,
  same_configuration boolean NOT NULL,
  unsupported_bridge_count integer NOT NULL CHECK (unsupported_bridge_count >= 0),
  decision exploration_v3.composition_decision NOT NULL,
  reasons text[] NOT NULL,
  semantic_sha256 core.sha256_hex NOT NULL UNIQUE,
  reviewed_at timestamptz,
  CHECK (cardinality(reasons) > 0),
  CHECK (array_position(reasons, NULL) IS NULL),
  CHECK ((review_state = 'FINAL') = (reviewed_at IS NOT NULL))
);

CREATE TABLE exploration_v3.composition_review_realization (
  composition_coherence_review_id text NOT NULL
    REFERENCES exploration_v3.composition_coherence_review(composition_coherence_review_id) ON DELETE RESTRICT,
  association_realization_id text NOT NULL
    REFERENCES exploration_v3.association_realization(association_realization_id) ON DELETE RESTRICT,
  PRIMARY KEY (composition_coherence_review_id, association_realization_id)
);

CREATE TABLE exploration_v3.navigation_state (
  state_id text PRIMARY KEY CHECK (btrim(state_id) <> ''),
  realm exploration_v3.realm NOT NULL,
  composition_revision_id text NOT NULL
    REFERENCES exploration_v3.composition_revision(composition_revision_id) ON DELETE RESTRICT,
  focus_navigation_node_id text NOT NULL CHECK (btrim(focus_navigation_node_id) <> ''),
  bipartite_alternation_valid boolean NOT NULL CHECK (bipartite_alternation_valid),
  semantic_sha256 core.sha256_hex NOT NULL UNIQUE,
  presentation_sha256 core.sha256_hex NOT NULL,
  focus_style text NOT NULL CHECK (btrim(focus_style) <> ''),
  viewport text NOT NULL CHECK (btrim(viewport) <> '')
);

CREATE TABLE exploration_v3.navigation_node (
  state_id text NOT NULL REFERENCES exploration_v3.navigation_state(state_id) ON DELETE RESTRICT,
  navigation_node_id text NOT NULL CHECK (btrim(navigation_node_id) <> ''),
  node_kind exploration_v3.navigation_node_kind NOT NULL,
  concept_id text REFERENCES exploration_v3.concept(concept_id) ON DELETE RESTRICT,
  association_revision_id text
    REFERENCES exploration_v3.association_revision(association_revision_id) ON DELETE RESTRICT,
  CHECK (
    (node_kind = 'CONCEPT' AND concept_id IS NOT NULL AND association_revision_id IS NULL)
    OR
    (node_kind = 'ASSOCIATION' AND concept_id IS NULL AND association_revision_id IS NOT NULL)
  ),
  PRIMARY KEY (state_id, navigation_node_id)
);

CREATE TABLE exploration_v3.navigation_path_step (
  state_id text NOT NULL REFERENCES exploration_v3.navigation_state(state_id) ON DELETE RESTRICT,
  step_ordinal integer NOT NULL CHECK (step_ordinal >= 0),
  from_navigation_node_id text NOT NULL,
  incidence_id text NOT NULL REFERENCES exploration_v3.association_incidence(incidence_id) ON DELETE RESTRICT,
  to_navigation_node_id text NOT NULL,
  CHECK (from_navigation_node_id <> to_navigation_node_id),
  FOREIGN KEY (state_id, from_navigation_node_id)
    REFERENCES exploration_v3.navigation_node(state_id, navigation_node_id) ON DELETE RESTRICT,
  FOREIGN KEY (state_id, to_navigation_node_id)
    REFERENCES exploration_v3.navigation_node(state_id, navigation_node_id) ON DELETE RESTRICT,
  PRIMARY KEY (state_id, step_ordinal)
);

CREATE TABLE exploration_v3.interaction_transition (
  transition_id text PRIMARY KEY CHECK (btrim(transition_id) <> ''),
  realm exploration_v3.realm NOT NULL,
  from_state_id text NOT NULL
    REFERENCES exploration_v3.navigation_state(state_id) ON DELETE RESTRICT,
  to_state_id text NOT NULL
    REFERENCES exploration_v3.navigation_state(state_id) ON DELETE RESTRICT,
  transition_kind exploration_v3.transition_kind NOT NULL,
  incidence_id text REFERENCES exploration_v3.association_incidence(incidence_id) ON DELETE RESTRICT,
  association_revision_id text
    REFERENCES exploration_v3.association_revision(association_revision_id) ON DELETE RESTRICT,
  association_realization_id text
    REFERENCES exploration_v3.association_realization(association_realization_id) ON DELETE RESTRICT,
  state_mutated boolean NOT NULL,
  semantic_sha256 core.sha256_hex NOT NULL UNIQUE,
  product_eligible boolean NOT NULL,
  product_eligibility_disposition exploration_v3.product_eligibility_disposition NOT NULL,
  product_path text,
  product_ineligibility_reason text,
  CHECK (product_path IS NULL OR btrim(product_path) <> ''),
  CHECK (product_ineligibility_reason IS NULL OR btrim(product_ineligibility_reason) <> ''),
  CHECK (transition_kind <> 'FOLLOW_INCIDENCE' OR (
    incidence_id IS NOT NULL AND association_revision_id IS NOT NULL
    AND association_realization_id IS NOT NULL
  )),
  CHECK (
    (realm = 'PRODUCTION' AND (
      (product_eligible AND product_eligibility_disposition = 'ELIGIBLE'
        AND product_path IS NOT NULL AND product_ineligibility_reason IS NULL)
      OR
      (NOT product_eligible AND product_eligibility_disposition IN ('INELIGIBLE','DEFERRED')
        AND product_path IS NULL AND product_ineligibility_reason IS NOT NULL)
    ))
    OR
    (realm = 'SYNTHETIC_CONTROL' AND NOT product_eligible
      AND product_eligibility_disposition = 'NOT_APPLICABLE_SYNTHETIC'
      AND product_path IS NULL AND product_ineligibility_reason IS NOT NULL)
  )
);

CREATE TABLE exploration_v3.exploration_workflow (
  workflow_id text PRIMARY KEY CHECK (btrim(workflow_id) <> ''),
  realm exploration_v3.realm NOT NULL,
  initial_state_id text NOT NULL REFERENCES exploration_v3.navigation_state(state_id) ON DELETE RESTRICT,
  transition_kind exploration_v3.transition_kind NOT NULL,
  reachable boolean NOT NULL,
  semantic_sha256 core.sha256_hex NOT NULL UNIQUE,
  product_eligible boolean NOT NULL,
  product_eligibility_disposition exploration_v3.product_eligibility_disposition NOT NULL,
  product_path text,
  product_ineligibility_reason text,
  CHECK (product_path IS NULL OR btrim(product_path) <> ''),
  CHECK (product_ineligibility_reason IS NULL OR btrim(product_ineligibility_reason) <> ''),
  CHECK (
    (realm = 'PRODUCTION' AND (
      (product_eligible AND reachable
        AND product_eligibility_disposition = 'ELIGIBLE'
        AND product_path IS NOT NULL AND product_ineligibility_reason IS NULL)
      OR
      (NOT product_eligible AND product_eligibility_disposition IN ('INELIGIBLE','DEFERRED')
        AND product_path IS NULL AND product_ineligibility_reason IS NOT NULL)
    ))
    OR
    (realm = 'SYNTHETIC_CONTROL' AND NOT product_eligible
      AND product_eligibility_disposition = 'NOT_APPLICABLE_SYNTHETIC'
      AND product_path IS NULL AND product_ineligibility_reason IS NOT NULL)
  )
);

CREATE TABLE exploration_v3.workflow_state (
  workflow_id text NOT NULL REFERENCES exploration_v3.exploration_workflow(workflow_id) ON DELETE RESTRICT,
  state_id text NOT NULL REFERENCES exploration_v3.navigation_state(state_id) ON DELETE RESTRICT,
  PRIMARY KEY (workflow_id, state_id)
);

CREATE TABLE exploration_v3.workflow_association_revision (
  workflow_id text NOT NULL REFERENCES exploration_v3.exploration_workflow(workflow_id) ON DELETE RESTRICT,
  association_revision_id text NOT NULL
    REFERENCES exploration_v3.association_revision(association_revision_id) ON DELETE RESTRICT,
  PRIMARY KEY (workflow_id, association_revision_id)
);

CREATE TABLE exploration_v3.workflow_association_realization (
  workflow_id text NOT NULL REFERENCES exploration_v3.exploration_workflow(workflow_id) ON DELETE RESTRICT,
  association_realization_id text NOT NULL
    REFERENCES exploration_v3.association_realization(association_realization_id) ON DELETE RESTRICT,
  PRIMARY KEY (workflow_id, association_realization_id)
);

CREATE TABLE exploration_v3.workflow_transition (
  workflow_id text NOT NULL REFERENCES exploration_v3.exploration_workflow(workflow_id) ON DELETE RESTRICT,
  transition_id text NOT NULL REFERENCES exploration_v3.interaction_transition(transition_id) ON DELETE RESTRICT,
  PRIMARY KEY (workflow_id, transition_id)
);

CREATE TABLE exploration_v3.export_manifest (
  export_id text PRIMARY KEY CHECK (btrim(export_id) <> ''),
  realm exploration_v3.realm NOT NULL,
  workflow_id text NOT NULL REFERENCES exploration_v3.exploration_workflow(workflow_id) ON DELETE RESTRICT,
  state_id text NOT NULL REFERENCES exploration_v3.navigation_state(state_id) ON DELETE RESTRICT,
  composition_revision_id text NOT NULL
    REFERENCES exploration_v3.composition_revision(composition_revision_id) ON DELETE RESTRICT,
  semantic_sha256 core.sha256_hex NOT NULL UNIQUE,
  presentation_sha256 core.sha256_hex NOT NULL,
  export_format text NOT NULL CHECK (btrim(export_format) <> ''),
  theme text NOT NULL CHECK (btrim(theme) <> ''),
  pair_projection_policy_preserved boolean NOT NULL CHECK (pair_projection_policy_preserved),
  product_eligible boolean NOT NULL,
  product_eligibility_disposition exploration_v3.product_eligibility_disposition NOT NULL,
  product_path text,
  product_ineligibility_reason text,
  CHECK (product_path IS NULL OR btrim(product_path) <> ''),
  CHECK (product_ineligibility_reason IS NULL OR btrim(product_ineligibility_reason) <> ''),
  CHECK (
    (realm = 'PRODUCTION' AND (
      (product_eligible AND product_eligibility_disposition = 'ELIGIBLE'
        AND product_path IS NOT NULL AND product_ineligibility_reason IS NULL)
      OR
      (NOT product_eligible AND product_eligibility_disposition IN ('INELIGIBLE','DEFERRED')
        AND product_path IS NULL AND product_ineligibility_reason IS NOT NULL)
    ))
    OR
    (realm = 'SYNTHETIC_CONTROL' AND NOT product_eligible
      AND product_eligibility_disposition = 'NOT_APPLICABLE_SYNTHETIC'
      AND product_path IS NULL AND product_ineligibility_reason IS NOT NULL)
  )
);

CREATE TABLE exploration_v3.export_projection_preservation (
  export_id text NOT NULL REFERENCES exploration_v3.export_manifest(export_id) ON DELETE RESTRICT,
  association_revision_id text NOT NULL
    REFERENCES exploration_v3.association_revision(association_revision_id) ON DELETE RESTRICT,
  association_realization_id text NOT NULL
    REFERENCES exploration_v3.association_realization(association_realization_id) ON DELETE RESTRICT,
  pair_projection_policy exploration_v3.pair_projection_policy NOT NULL,
  realization_kind exploration_v3.realization_kind NOT NULL,
  PRIMARY KEY (export_id, association_revision_id, association_realization_id)
);

-- A seal is written after every aggregate child set is complete.  Row-level
-- append-only triggers prevent replacement, while seal-aware child triggers
-- prevent a later INSERT from changing reviewed/hash-bound aggregate meaning.
CREATE TABLE exploration_v3.aggregate_seal (
  aggregate_kind text NOT NULL CHECK (aggregate_kind IN (
    'EVIDENCE_REFERENCE', 'CONCEPT_SENSE', 'ASSOCIATION_REVISION',
    'COMPOSITION_REVISION', 'NAVIGATION_STATE', 'WORKFLOW', 'EXPORT'
  )),
  aggregate_id text NOT NULL CHECK (btrim(aggregate_id) <> ''),
  aggregate_content_sha256 core.sha256_hex NOT NULL,
  sealed_at timestamptz NOT NULL,
  PRIMARY KEY (aggregate_kind, aggregate_id)
);

CREATE INDEX association_revision_lifecycle_idx
  ON exploration_v3.association_revision (lifecycle_state, product_eligible, association_id);
CREATE INDEX association_incidence_concept_idx
  ON exploration_v3.association_incidence (concept_id, sense_id, association_revision_id);
CREATE INDEX association_review_disposition_idx
  ON exploration_v3.association_review (review_state, disposition, global_coherence);
CREATE INDEX composition_revision_product_idx
  ON exploration_v3.composition_revision (product_eligible, composition_id);
CREATE INDEX navigation_state_composition_idx
  ON exploration_v3.navigation_state (composition_revision_id, state_id);
CREATE INDEX interaction_transition_endpoint_idx
  ON exploration_v3.interaction_transition (from_state_id, to_state_id, transition_id);
CREATE INDEX export_workflow_idx
  ON exploration_v3.export_manifest (workflow_id, state_id, export_id);

COMMENT ON TABLE exploration_v3.association IS
  'Stable semantic identity. HIGHER_ORDER rows always preserve pair_projection_policy NONE.';
COMMENT ON TABLE exploration_v3.internal_pair_link IS
  'Explicit support links to pre-existing pair revisions; never a pair generator or projection table.';
COMMENT ON TABLE exploration_v3.association_realization IS
  'Presentation identity distinct from semantic association identity.';
COMMENT ON TABLE exploration_v3.aggregate_seal IS
  'Final child-membership boundary. A sealed aggregate can only be corrected by a new governed revision.';
COMMENT ON SCHEMA api_v3 IS
  'Positive-allowlist research read contract; empty until governed production activation.';

RESET ROLE;
