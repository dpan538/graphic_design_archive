export const TRACE_OPEN_INQUIRY_API_VERSION = "trace-open-inquiry/v1" as const;
export const TRACE_OPEN_INQUIRY_REGISTRY_VERSION = "trace-open-inquiry-registry/v1" as const;
export const TRACE_OPEN_INQUIRY_RESPONSE_SCHEMA_VERSION = "trace-open-inquiry-response/v1" as const;
export const TRACE_OPEN_INQUIRY_ERROR_SCHEMA_VERSION = "trace-open-inquiry-error/v1" as const;
export const TRACE_OPEN_INQUIRY_LAYER = "OPEN_INQUIRY" as const;

export type OpenInquiryArity = 2 | 3 | 4 | 5;

export interface OpenInquiryParticipant {
  readonly label: string;
  readonly sense_id: string;
}

export interface OpenInquiryAssociationIdentity {
  readonly association_id: string;
  readonly association_revision_id: string;
  readonly authority_path: string | null;
  readonly authority_queue_ref: string | null;
}

export interface OpenInquiryEvidence {
  readonly support_mode: string;
  readonly disposition: string;
  readonly exact_group_support_status: string | null;
  readonly global_coherence_status: string | null;
  readonly sense_scope_status: string | null;
  readonly locators: readonly string[] | null;
  readonly synthesis_steps: readonly string[] | null;
  readonly counterevidence: readonly string[] | null;
  readonly qualifications: readonly string[] | null;
  readonly nonclaims: readonly string[];
}

export interface OpenInquiryProvenance {
  readonly authority_base_sha: string;
  readonly shard_id: string;
  readonly source_ledger_path: string;
  readonly source_ledger_sha256: string;
  readonly source_row_number: number;
  readonly source_record_sha256: string;
  readonly source_ids: readonly string[];
  readonly rights_record_ids: readonly string[] | null;
  readonly linked_parent_candidate_id: string | null;
  readonly parent_disposition_preserved: string | null;
  readonly source_external_human_review_status: string;
  readonly source_activation_status: string;
}

export interface OpenInquiryRecord {
  readonly inquiry_id: string;
  readonly inquiry_key: string;
  readonly record_version: typeof TRACE_OPEN_INQUIRY_API_VERSION;
  readonly arity: OpenInquiryArity;
  readonly participants: readonly OpenInquiryParticipant[];
  readonly bounded_scope: string;
  readonly relation_form: string;
  readonly epistemic_status: "UNRESOLVED_OPEN_INQUIRY";
  readonly validated_relation: false;
  readonly counts_as_validated: false;
  readonly eligible_for_validated_graph: false;
  readonly eligible_for_validated_composition: false;
  readonly may_generate_pair_edges: false;
  readonly may_modify_validated_topology: false;
  readonly display_eligible: true;
  readonly display_layer: typeof TRACE_OPEN_INQUIRY_LAYER;
  readonly default_in_validated_results: false;
  readonly active: false;
  readonly external_human_review_status: "PENDING";
  readonly product_eligible: false;
  readonly product_path: null;
  readonly participant_order_meaningful: false;
  readonly relation_roles_asserted: false;
  readonly pair_projection_policy: "NONE";
  readonly implicit_pair_projection_count: 0;
  readonly inquiry_only_association_identity: OpenInquiryAssociationIdentity | null;
  readonly evidence: OpenInquiryEvidence;
  readonly provenance: OpenInquiryProvenance;
  readonly record_sha256: string;
}

export interface OpenInquiryRegistryCounts {
  readonly scoped_higher_order_hypothesis_count: 11;
  readonly arity_2_count: 3;
  readonly arity_3_count: 6;
  readonly arity_4_count: 1;
  readonly arity_5_count: 1;
  readonly governed_inquiry_only_association_identity_count: 4;
  readonly ungoverned_hypothesis_count: 7;
  readonly active_pending_review_count: 0;
  readonly implicit_pair_projection_count: 0;
}

export interface OpenInquiryClosureFlags {
  readonly PAIR_ASSOCIATION_CLOSURE: false;
  readonly HIGHER_ORDER_ASSOCIATION_CLOSURE: false;
  readonly GLOBAL_COMPOSITION_COHERENCE_CLOSURE: false;
  readonly PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE: false;
  readonly COMPUTATIONAL_SPACE_CLOSURE: false;
  readonly FUNCTION3_CLOSURE: false;
}

export interface OpenInquiryInputBinding {
  readonly path: string;
  readonly sha256: string;
  readonly bytes: number;
  readonly record_count: number;
}

export interface OpenInquiryRegistry {
  readonly registry_version: typeof TRACE_OPEN_INQUIRY_REGISTRY_VERSION;
  readonly api_version: typeof TRACE_OPEN_INQUIRY_API_VERSION;
  readonly canonical_serialization: "UTF8_SORTED_KEYS_COMPACT_JSON_RECORD_DIGEST";
  readonly input_bindings: readonly OpenInquiryInputBinding[];
  readonly counts: OpenInquiryRegistryCounts;
  readonly closure_flags: OpenInquiryClosureFlags;
  readonly records_sha256: string;
  readonly records: readonly OpenInquiryRecord[];
}

export interface OpenInquiryBoundary {
  readonly evidence_bounded: true;
  readonly validated_layer_contamination_allowed: false;
  readonly implicit_pair_projection_allowed: false;
  readonly validated_topology_mutation_allowed: false;
  readonly stochastic_display: false;
}

export interface OpenInquiryResponseEnvelope<T> {
  readonly schema_version: typeof TRACE_OPEN_INQUIRY_RESPONSE_SCHEMA_VERSION;
  readonly api_version: typeof TRACE_OPEN_INQUIRY_API_VERSION;
  readonly layer: typeof TRACE_OPEN_INQUIRY_LAYER;
  readonly registry_sha256: string;
  readonly boundary: OpenInquiryBoundary;
  readonly data: T;
}

export interface OpenInquiryListData {
  readonly count: 11;
  readonly items: readonly OpenInquiryRecord[];
}

export interface OpenInquiryDetailData {
  readonly item: OpenInquiryRecord;
}

export type OpenInquiryErrorCode =
  | "OPEN_INQUIRY_NOT_FOUND"
  | "UNSUPPORTED_QUERY_PARAMETER"
  | "METHOD_NOT_ALLOWED"
  | "REGISTRY_INTEGRITY_FAILURE";

export interface OpenInquiryApiError {
  readonly schema_version: typeof TRACE_OPEN_INQUIRY_ERROR_SCHEMA_VERSION;
  readonly api_version: typeof TRACE_OPEN_INQUIRY_API_VERSION;
  readonly layer: typeof TRACE_OPEN_INQUIRY_LAYER;
  readonly code: OpenInquiryErrorCode;
  readonly message: string;
  readonly status: number;
  readonly retryable: boolean;
  readonly instance: string;
  readonly registry_sha256: string | null;
}

export type OpenInquiryServiceResult<T> =
  | { readonly ok: true; readonly data: OpenInquiryResponseEnvelope<T> }
  | {
    readonly ok: false;
    readonly code: OpenInquiryErrorCode;
    readonly message: string;
    readonly status: number;
    readonly retryable?: boolean;
  };
