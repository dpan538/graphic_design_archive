export const TRACE_EXPLORATION_V3_API_VERSION = "trace-exploration/v3" as const;
export const TRACE_EXPLORATION_V3_READ_MODEL_VERSION =
  "trace-exploration-runtime-read-model-v3-1.0.0" as const;
export const TRACE_EXPLORATION_V3_MANIFEST_VERSION =
  "trace-exploration-runtime-manifest-v3-1.0.0" as const;

export type ExplorationV3Realm = "PRODUCTION" | "SYNTHETIC_CONTROL";
export type ExplorationV3AssociationKind = "PAIR" | "HIGHER_ORDER";
export type ExplorationV3DataClass = "ACTIVE_PRODUCT_FACT" | "SYNTHETIC_CONTROL";
export type ExplorationV3PairProjectionPolicy = "NOT_APPLICABLE" | "NONE";
export type ExplorationV3RealizationKind =
  | "PAIR_EDGE"
  | "HYPEREDGE_HUB"
  | "HYPEREDGE_CONTOUR"
  | "LIST_GROUP";
export type ExplorationV3TransitionKind =
  | "FOLLOW_INCIDENCE"
  | "MOVE_FOCUS"
  | "EXPORT";

export interface ExplorationV3FactBoundary {
  readonly data_class: ExplorationV3DataClass;
  readonly production_fact: boolean;
  readonly synthetic_control: boolean;
}

export interface ExplorationV3Authority {
  readonly authority_id: string;
  readonly authority_kind: string;
  readonly authority_state: string;
  readonly authority_version: string;
}

export interface ExplorationV3ParticipantIncidence {
  readonly concept_id: string;
  readonly incidence_id: string;
  readonly ordinal: number | null;
  readonly participant_scope_id: string;
  readonly qualifications: readonly string[];
  readonly role_id: string | null;
  readonly sense_id: string;
}

export interface ExplorationV3InternalPairLink {
  readonly endpoint_sense_ids: readonly [string, string];
  readonly pair_association_id: string;
  readonly pair_association_revision_id: string;
  readonly pair_participant_incidence_ids: readonly [string, string];
  readonly participant_incidence_ids: readonly [string, string];
}

export interface ExplorationV3Scope {
  readonly actors: readonly string[];
  readonly context_qualifications: readonly string[];
  readonly geographies: readonly string[];
  readonly historical_case_ids: readonly string[];
  readonly institutions: readonly string[];
  readonly mechanisms: readonly string[];
  readonly scope_id: string;
  readonly time_bounds: {
    readonly end: string | null;
    readonly start: string | null;
  };
}

export interface ExplorationV3EvidenceProvenance {
  readonly conflict_resolution_ids: readonly string[];
  readonly conflicts_resolved: boolean;
  readonly evidence_complete: boolean;
  readonly evidence_item_ids: readonly string[];
  readonly locator_ids: readonly string[];
  readonly negative_or_conflicting_evidence: readonly string[];
  readonly rights_cleared_for_governed_use: boolean;
  readonly same_configuration: boolean;
  readonly support_mode: string;
  readonly synthesis_steps: readonly string[];
}

export interface ExplorationV3AssociationReview {
  readonly authority_state: string;
  readonly bounded_senses_compatible: boolean;
  readonly case_scope_compatible: boolean;
  readonly disposition: string;
  readonly explicit_non_claims: readonly string[];
  readonly global_coherence: "PASS" | "FAIL" | "UNRESOLVED";
  readonly qualifications: readonly string[];
  readonly review_authority: string;
  readonly review_id: string;
  readonly review_state: "FINAL" | "PENDING" | string;
  readonly review_version: string;
  readonly roles_and_topology_supported: boolean;
  readonly unsupported_bridge_count: number;
}

export interface ExplorationV3Activation {
  readonly all_gates_pass: boolean;
  readonly authority_gate: boolean;
  readonly bounded_scope_gate: boolean;
  readonly coherence_gate: boolean;
  readonly conflict_gate: boolean;
  readonly decision: string;
  readonly evidence_gate: boolean;
  readonly final_review_gate: boolean;
  readonly product_policy_gate: boolean;
  readonly reasons: readonly string[];
  readonly requested_state: string;
  readonly rights_gate: boolean;
  readonly synthesis_gate: boolean;
}

export interface ExplorationV3Uncertainty {
  readonly activation_policy: string;
  readonly basis: readonly string[];
  readonly level: string;
  readonly rationale: string;
  readonly reviewed_in_review_id: string;
  readonly status: string;
  readonly unresolved_questions: readonly string[];
}

export interface ExplorationV3Eligibility {
  readonly lifecycle_state: string;
  readonly product_eligibility_disposition: string;
  readonly product_eligible: boolean;
  readonly product_ineligibility_reason: string | null;
  readonly product_path: string | null;
}

export interface ExplorationV3AssociationDto {
  readonly activation: ExplorationV3Activation;
  readonly arity: number;
  readonly association_id: string;
  readonly association_kind: ExplorationV3AssociationKind;
  readonly association_revision_id: string;
  readonly eligibility: ExplorationV3Eligibility;
  readonly fact_boundary: ExplorationV3FactBoundary;
  readonly identity_material_sha256: string;
  readonly internal_pair_association_ids: readonly string[];
  readonly internal_pair_links: readonly ExplorationV3InternalPairLink[];
  readonly order_semantics: "ORDERED" | "UNORDERED";
  readonly pair_projection_policy: ExplorationV3PairProjectionPolicy;
  readonly participants: readonly ExplorationV3ParticipantIncidence[];
  readonly presentation: Readonly<Record<string, string>>;
  readonly presentation_sha256: string;
  readonly provenance: ExplorationV3EvidenceProvenance;
  readonly realm: ExplorationV3Realm;
  readonly review: ExplorationV3AssociationReview;
  readonly roles_meaningful: boolean;
  readonly scope: ExplorationV3Scope;
  readonly semantic_sha256: string;
  readonly semantic_version: string;
  readonly uncertainty: ExplorationV3Uncertainty;
}

export interface ExplorationV3AssociationRealization {
  readonly association_id: string;
  readonly association_kind: ExplorationV3AssociationKind;
  readonly association_realization_id: string;
  readonly association_revision_id: string;
  readonly presentation: Readonly<Record<string, string>>;
  readonly presentation_sha256: string;
  readonly realization_kind: ExplorationV3RealizationKind;
  readonly realized_incidence_ids: readonly string[];
  readonly semantic_sha256: string;
}

export interface ExplorationV3AssociationRealizationDto
  extends ExplorationV3AssociationRealization {
  readonly composition_id: string;
  readonly composition_revision_id: string;
  readonly fact_boundary: ExplorationV3FactBoundary;
}

export interface ExplorationV3IncidenceDto
  extends ExplorationV3ParticipantIncidence {
  readonly association_id: string;
  readonly association_kind: ExplorationV3AssociationKind;
  readonly association_revision_id: string;
  readonly fact_boundary: ExplorationV3FactBoundary;
}

export interface ExplorationV3ScopeDto extends ExplorationV3Scope {
  readonly fact_boundary: ExplorationV3FactBoundary;
  readonly realm: ExplorationV3Realm;
}

export interface ExplorationV3CompositionCoherenceReviewDto {
  readonly association_realization_ids: readonly string[];
  readonly association_revision_ids: readonly string[];
  readonly authority: ExplorationV3Authority;
  readonly bounded_senses_compatible: boolean;
  readonly case_scope_compatible: boolean;
  readonly composition_coherence_review_id: string;
  readonly composition_id: string;
  readonly decision: "COHERENT" | "INCOHERENT" | string;
  readonly global_coherence: "PASS" | "FAIL" | "UNRESOLVED";
  readonly incidence_ids: readonly string[];
  readonly realm: ExplorationV3Realm;
  readonly reasons: readonly string[];
  readonly review_state: "FINAL" | "PENDING" | string;
  readonly review_version: string;
  readonly roles_and_topology_supported: boolean;
  readonly same_configuration: boolean;
  readonly semantic_sha256: string;
  readonly unsupported_bridge_count: number;
  readonly fact_boundary: ExplorationV3FactBoundary;
}

export interface ExplorationV3CompositionDto {
  readonly association_realizations: readonly ExplorationV3AssociationRealization[];
  readonly association_trace_complete: boolean;
  readonly coherence_review: ExplorationV3CompositionCoherenceReviewDto;
  readonly composition_id: string;
  readonly composition_node_ids: readonly string[];
  readonly composition_revision_id: string;
  readonly eligibility: Omit<ExplorationV3Eligibility, "lifecycle_state">;
  readonly fact_boundary: ExplorationV3FactBoundary;
  readonly global_coherence_review_id: string;
  readonly presentation: Readonly<Record<string, string>>;
  readonly presentation_sha256: string;
  readonly realm: ExplorationV3Realm;
  readonly renderability: string;
  readonly semantic_sha256: string;
  readonly topology_family: string;
}

export interface ExplorationV3ConceptDto {
  readonly association_eligible: boolean;
  readonly authority: ExplorationV3Authority;
  readonly canonical_label: string;
  readonly concept_id: string;
  readonly fact_boundary: ExplorationV3FactBoundary;
  readonly lifecycle_state: string;
  readonly product_eligibility_disposition: string;
  readonly product_eligible: boolean;
  readonly product_ineligibility_reason: string | null;
  readonly product_path: string | null;
  readonly realm: ExplorationV3Realm;
  readonly semantic_sha256: string;
  readonly semantic_version: string;
}

export interface ExplorationV3ConceptSenseDto {
  readonly association_eligible: boolean;
  readonly authority: ExplorationV3Authority;
  readonly bounded_definition: string;
  readonly concept_id: string;
  readonly fact_boundary: ExplorationV3FactBoundary;
  readonly governed_scope_ids: readonly string[];
  readonly lifecycle_state: string;
  readonly product_eligibility_disposition: string;
  readonly product_eligible: boolean;
  readonly product_ineligibility_reason: string | null;
  readonly product_path: string | null;
  readonly realm: ExplorationV3Realm;
  readonly semantic_sha256: string;
  readonly semantic_version: string;
  readonly sense_id: string;
  readonly vocabulary_crosswalk_ids: readonly string[];
}

export interface ExplorationV3ConceptNavigationNodeDto {
  readonly association_revision_id: null;
  readonly concept_id: string;
  readonly navigation_node_id: string;
  readonly node_kind: "CONCEPT";
}

export interface ExplorationV3AssociationNavigationNodeDto {
  readonly association_revision_id: string;
  readonly concept_id: null;
  readonly navigation_node_id: string;
  readonly node_kind: "ASSOCIATION";
}

export type ExplorationV3NavigationNodeDto =
  | ExplorationV3ConceptNavigationNodeDto
  | ExplorationV3AssociationNavigationNodeDto;

export interface ExplorationV3NavigationPathStepDto {
  readonly from_navigation_node_id: string;
  readonly incidence_id: string;
  readonly to_navigation_node_id: string;
}

export interface ExplorationV3NavigationStateDto {
  readonly bipartite_alternation_valid: true;
  readonly composition_revision_id: string;
  readonly fact_boundary: ExplorationV3FactBoundary;
  readonly focus_navigation_node_id: string;
  readonly nodes: readonly ExplorationV3NavigationNodeDto[];
  readonly path: readonly ExplorationV3NavigationPathStepDto[];
  readonly presentation: {
    readonly focus_style: string;
    readonly viewport: string;
  };
  readonly presentation_sha256: string;
  readonly realm: ExplorationV3Realm;
  readonly semantic_sha256: string;
  readonly state_id: string;
}

export interface ExplorationV3WorkflowDto {
  readonly association_realization_ids: readonly string[];
  readonly association_revision_ids: readonly string[];
  readonly fact_boundary: ExplorationV3FactBoundary;
  readonly initial_state_id: string;
  readonly reachable: boolean;
  readonly realm: ExplorationV3Realm;
  readonly semantic_sha256: string;
  readonly state_ids: readonly string[];
  readonly transition_ids: readonly string[];
  readonly transition_kind: ExplorationV3TransitionKind;
  readonly workflow_id: string;
}

export interface ExplorationV3ProjectionPreservationRecordDto {
  readonly association_realization_id: string;
  readonly association_revision_id: string;
  readonly pair_projection_policy: ExplorationV3PairProjectionPolicy;
  readonly realization_kind: ExplorationV3RealizationKind;
}

export interface ExplorationV3ExportDto {
  readonly association_realization_ids: readonly string[];
  readonly association_revision_ids: readonly string[];
  readonly composition_revision_id: string;
  readonly export_id: string;
  readonly fact_boundary: ExplorationV3FactBoundary;
  readonly pair_projection_policy_preserved: true;
  readonly presentation: {
    readonly format: string;
    readonly theme: string;
  };
  readonly presentation_sha256: string;
  readonly projection_preservation_records: readonly ExplorationV3ProjectionPreservationRecordDto[];
  readonly realm: ExplorationV3Realm;
  readonly semantic_sha256: string;
  readonly state_id: string;
  readonly workflow_id: string;
}

export interface ExplorationV3TransitionDto {
  readonly association_realization_id: string | null;
  readonly association_revision_id: string | null;
  readonly fact_boundary: ExplorationV3FactBoundary;
  readonly from_state_id: string;
  readonly incidence_id: string | null;
  readonly realm: ExplorationV3Realm;
  readonly semantic_sha256: string;
  readonly state_mutated: boolean;
  readonly to_state_id: string;
  readonly transition_id: string;
  readonly transition_kind: ExplorationV3TransitionKind;
}

export interface ExplorationV3ClosureFlags {
  readonly computational_space_closure: boolean;
  readonly function3_closure: boolean;
  readonly global_composition_coherence_closure: boolean;
  readonly higher_order_association_closure: boolean;
  readonly pair_association_closure: boolean;
  readonly product_association_reachability_closure: boolean;
}

export interface ExplorationV3Capabilities {
  readonly active_pending_review_count: number;
  readonly active_product_association_count: number;
  readonly active_product_coherence_review_count: number;
  readonly active_product_composition_count: number;
  readonly active_product_concept_count: number;
  readonly active_product_export_count: number;
  readonly active_product_incidence_count: number;
  readonly active_product_navigation_state_count: number;
  readonly active_product_realization_count: number;
  readonly active_product_scope_count: number;
  readonly active_product_sense_count: number;
  readonly active_product_transition_count: number;
  readonly active_product_workflow_count: number;
  readonly association_and_composition_identity_separate: true;
  readonly backend_association_arity_support: "PAIR_2_OR_HIGHER_ORDER_3_PLUS_NO_FIXED_SCHEMA_MAXIMUM";
  readonly control_association_count: number;
  readonly control_coherence_review_count: number;
  readonly control_composition_count: number;
  readonly control_concept_count: number;
  readonly control_export_count: number;
  readonly control_higher_order_association_count: number;
  readonly control_incidence_count: number;
  readonly control_navigation_state_count: number;
  readonly control_pair_association_count: number;
  readonly control_realization_count: number;
  readonly control_scope_count: number;
  readonly control_sense_count: number;
  readonly control_transition_count: number;
  readonly control_workflow_count: number;
  readonly governed_product_arity_bound: null;
  readonly higher_order_associations_supported: true;
  readonly implicit_pair_projection_allowed: false;
  readonly implicit_hyperedge_projection_count: number;
  readonly production_activation_count: 0;
  readonly product_activation_available: false;
  readonly read_paths: readonly string[];
  readonly research_controls_only: true;
  readonly supported_association_kinds: readonly ExplorationV3AssociationKind[];
  readonly transition_derivation_policy: "NONE_NO_V2_INHERITANCE";
  readonly transition_status: "FAIL_CLOSED_NO_ACTIVE_PRODUCT_STATE_GRAPH";
  readonly transitions_available: false;
}

export interface ExplorationV3Surface {
  readonly association_realizations: readonly ExplorationV3AssociationRealizationDto[];
  readonly associations: readonly ExplorationV3AssociationDto[];
  readonly composition_coherence_reviews: readonly ExplorationV3CompositionCoherenceReviewDto[];
  readonly compositions: readonly ExplorationV3CompositionDto[];
  readonly concept_senses: readonly ExplorationV3ConceptSenseDto[];
  readonly concepts: readonly ExplorationV3ConceptDto[];
  readonly exports: readonly ExplorationV3ExportDto[];
  readonly incidences: readonly ExplorationV3IncidenceDto[];
  readonly navigation_states: readonly ExplorationV3NavigationStateDto[];
  readonly scopes: readonly ExplorationV3ScopeDto[];
  readonly transitions: readonly ExplorationV3TransitionDto[];
  readonly workflows: readonly ExplorationV3WorkflowDto[];
}

export interface ExplorationV3CollectionDtoMap {
  readonly "association-realizations": ExplorationV3AssociationRealizationDto;
  readonly associations: ExplorationV3AssociationDto;
  readonly "composition-coherence-reviews": ExplorationV3CompositionCoherenceReviewDto;
  readonly compositions: ExplorationV3CompositionDto;
  readonly "concept-senses": ExplorationV3ConceptSenseDto;
  readonly concepts: ExplorationV3ConceptDto;
  readonly exports: ExplorationV3ExportDto;
  readonly incidences: ExplorationV3IncidenceDto;
  readonly "navigation-states": ExplorationV3NavigationStateDto;
  readonly scopes: ExplorationV3ScopeDto;
  readonly transitions: ExplorationV3TransitionDto;
  readonly workflows: ExplorationV3WorkflowDto;
}

export interface ExplorationV3ReadModel {
  readonly active_product: ExplorationV3Surface;
  readonly api_version: typeof TRACE_EXPLORATION_V3_API_VERSION;
  readonly baseline_reconciliation: Readonly<Record<string, unknown>>;
  readonly capabilities: ExplorationV3Capabilities;
  readonly closure_flags: ExplorationV3ClosureFlags;
  readonly contract_version: "trace-exploration-v3-semantic-contract-1.0.0";
  readonly fact_boundary: {
    readonly active_product_policy: "FINAL_PRODUCTION_AUTHORITY_AND_ALL_GATES_REQUIRED";
    readonly current_status: "FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS";
    readonly inquiry_or_pending_records_are_active_facts: false;
    readonly synthetic_controls_are_active_facts: false;
  };
  readonly read_model_version: typeof TRACE_EXPLORATION_V3_READ_MODEL_VERSION;
  readonly research_controls: ExplorationV3Surface;
  readonly source_authority: {
    readonly authorized_round16a_source_sha: string;
    readonly semantic_contract_namespace: "trace/exploration/v3";
    readonly semantic_contract_parent_sha: string;
    readonly semantic_contract_source_sha: string;
  };
}

export interface ExplorationV3RuntimeReadModel {
  readonly model: ExplorationV3ReadModel;
  readonly readModelSha256: string;
}

export interface ExplorationV3ResponseEnvelope<T> {
  readonly api_version: typeof TRACE_EXPLORATION_V3_API_VERSION;
  readonly closure_flags: ExplorationV3ClosureFlags;
  readonly fact_boundary: ExplorationV3ReadModel["fact_boundary"];
  readonly read_model_sha256: string;
  readonly data: T;
}

export type ExplorationV3ErrorCode =
  | "ENDPOINT_NOT_FOUND"
  | "INTERNAL_DATA_INTEGRITY_FAILURE"
  | "INVALID_ASSOCIATION"
  | "INVALID_COMPOSITION"
  | "INVALID_CONTROL"
  | "METHOD_NOT_ALLOWED"
  | "NOT_ACTIVE_PRODUCT_FACT";

export interface ExplorationV3ApiError {
  readonly schema_version: "trace-exploration-api-error-v3";
  readonly api_version: typeof TRACE_EXPLORATION_V3_API_VERSION;
  readonly code: ExplorationV3ErrorCode;
  readonly message: string;
  readonly status: number;
  readonly retryable: boolean;
  readonly instance: string;
  readonly read_model_sha256: string | null;
}

export type ExplorationV3ServiceResult<T> =
  | { readonly ok: true; readonly data: ExplorationV3ResponseEnvelope<T> }
  | {
      readonly ok: false;
      readonly code: ExplorationV3ErrorCode;
      readonly message: string;
      readonly status: number;
      readonly retryable?: boolean;
    };
