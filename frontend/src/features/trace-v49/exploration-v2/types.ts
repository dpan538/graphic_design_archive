export const TRACE_EXPLORATION_V2_API_VERSION = "trace-exploration/v2" as const;

export const TRACE_EXPLORATION_V2_ACTIONS = [
  "SELECT_CATEGORY",
  "FOCUS_NODE",
  "EXPAND_NODE",
  "COLLAPSE_NODE",
  "MOVE_FOCUS",
  "SELECT_COMPOSITION",
  "RESET_CATEGORY",
  "EXPORT_CURRENT_STATE",
] as const;

export const TRACE_EXPLORATION_V2_THEMES = [
  "neutral-v1",
  "neutral-contrast-v1",
] as const;

export const TRACE_EXPLORATION_V2_EXPORT_PRESETS = ["portrait_card"] as const;
export const TRACE_EXPLORATION_V2_TRANSITION_DERIVATION_VERSION = "trace-exploration-derived-transitions-v2" as const;

export type ExplorationV2Action = (typeof TRACE_EXPLORATION_V2_ACTIONS)[number];
export type ExplorationV2Theme = (typeof TRACE_EXPLORATION_V2_THEMES)[number];
export type ExplorationV2ExportPreset = (typeof TRACE_EXPLORATION_V2_EXPORT_PRESETS)[number];
export type ExplorationV2CategoryId = "region" | "theme" | "medium" | "movement";

export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | readonly JsonValue[] | { readonly [key: string]: JsonValue };

export interface ExplorationV2DatabaseRecord {
  readonly database_snapshot_id: string;
  readonly database_schema_version: 49;
  readonly database_content_sha256: string;
  readonly database_identity_sha256: string;
  readonly release_id: "v49";
  readonly source_sha: string;
  readonly production_read_model_sha256?: string;
}

export interface ExplorationV2CategoryRecord {
  readonly category_id: ExplorationV2CategoryId;
  readonly category_entry_id: string;
  readonly label: string;
  readonly entry_label: string;
  readonly description: string;
  readonly composition_ids: readonly string[];
  readonly initial_state_id: string;
}

export interface ExplorationV2VocabularyRecord {
  readonly vocabulary_id: string;
  readonly canonical_label: string;
  readonly attested_forms: readonly string[];
  readonly language: "en";
  readonly scope_note: string;
  readonly ambiguity_note: string;
  readonly activation_status: string;
}

export interface ExplorationV2AssociationRecord {
  readonly association_id: string;
  readonly endpoint_vocabulary_ids: readonly [string, string];
  readonly endpoint_labels: readonly [string, string];
  readonly support_status: "ACTIVE_EXTERNALLY_SUPPORTED" | "ACTIVE_SOURCE_SUPPORTED";
  readonly strength: string;
  readonly confidence: string;
  readonly generic_association_only: true;
  readonly association_accessible_description: string;
  readonly explicit_non_claims: readonly string[];
}

export interface ExplorationV2CompositionRecord {
  readonly composition_id: string;
  readonly category_entry_id: string;
  readonly seed_id: string;
  readonly seed_node_id: string;
  readonly node_ids: readonly string[];
  readonly association_ids: readonly string[];
  readonly topology_family: string;
  readonly semantic_hash: string;
  readonly label: string;
  readonly description: string;
}

export interface ExplorationV2TransitionDerivationRecord {
  readonly derivation_version: typeof TRACE_EXPLORATION_V2_TRANSITION_DERIVATION_VERSION;
  readonly key_format: "state_hash|action|target";
  readonly transition_count: 749_944;
}

export interface ExplorationV2StateRecord {
  readonly state_id: string;
  readonly state_hash: string;
  readonly category_entry_id: string;
  readonly composition_id: string;
  readonly seed_id: string;
  readonly focused_node_id: string;
  readonly expanded_node_ids: readonly string[];
  readonly visible_node_ids: readonly string[];
  readonly visible_association_ids: readonly string[];
  readonly available_actions: readonly ExplorationV2Action[];
  readonly semantic_hash: string;
  readonly presentation_hash: string;
  readonly database_snapshot: string;
}

export interface ExplorationV2ReadModel {
  readonly database: ExplorationV2DatabaseRecord;
  readonly categories: readonly ExplorationV2CategoryRecord[];
  readonly vocabulary: readonly ExplorationV2VocabularyRecord[];
  readonly associations: readonly ExplorationV2AssociationRecord[];
  readonly compositions: Readonly<Record<string, ExplorationV2CompositionRecord>>;
  readonly states: Readonly<Record<string, ExplorationV2StateRecord>>;
  readonly states_by_hash: Readonly<Record<string, string>>;
  readonly transitions: ExplorationV2TransitionDerivationRecord;
  readonly capabilities: ExplorationV2ReadModelCapabilities;
}

export interface ExplorationV2ReadModelCapabilities {
  readonly api_version: typeof TRACE_EXPLORATION_V2_API_VERSION;
  readonly category_count: 4;
  readonly category_entry_count: 81;
  readonly vocabulary_count: 31;
  readonly association_count: 21;
  readonly topology_composition_count: 81;
  readonly production_composition_count: 228;
  readonly state_count: 5_760;
  readonly transition_count: 749_944;
  readonly workflow_count: 5_760;
  readonly export_variant_count: 11_520;
  readonly actions: readonly ExplorationV2Action[];
  readonly themes: readonly ExplorationV2Theme[];
  readonly export_presets: readonly ExplorationV2ExportPreset[];
  readonly maximum_node_count: 8;
  readonly generic_association_only: true;
}

export interface ExplorationV2MapRequest {
  readonly category_id: ExplorationV2CategoryId;
  readonly category_entry_id?: string;
  readonly locale?: "en";
}

export interface ExplorationV2ActionRequest {
  readonly action: ExplorationV2Action;
  readonly target_id?: string;
  readonly expected_state_hash: string;
  readonly database_snapshot?: string;
}

export interface ExplorationV2ExportRequest {
  readonly map_id: string;
  readonly state_hash: string;
  readonly composition_id: string;
  readonly export_preset: ExplorationV2ExportPreset;
  readonly theme_token_set: ExplorationV2Theme;
}

export interface ExplorationV2CategoryDto {
  readonly category_id: ExplorationV2CategoryId;
  readonly category_entry_id: string;
  readonly label: string;
  readonly entry_label?: string;
  readonly description?: string;
  readonly composition_ids: readonly string[];
  readonly initial_state_id: string;
}

export interface ExplorationV2VocabularyDto {
  readonly vocabulary_id: string;
  readonly canonical_label: string;
  readonly attested_forms: readonly string[];
  readonly language: string;
  readonly scope_note?: string;
  readonly ambiguity_note?: string;
  readonly activation_status?: string;
}

export interface ExplorationV2AssociationDto {
  readonly association_id: string;
  readonly endpoint_vocabulary_ids: readonly [string, string];
  readonly endpoint_labels: readonly [string, string];
  readonly support_status: "ACTIVE_EXTERNALLY_SUPPORTED" | "ACTIVE_SOURCE_SUPPORTED";
  readonly strength?: string | number;
  readonly confidence?: string | number;
  readonly generic_association_only: true;
  readonly association_accessible_description: string;
  readonly explicit_non_claims: readonly string[];
}

export interface ExplorationV2CompositionDto {
  readonly composition_id: string;
  readonly category_entry_id: string;
  readonly seed_id: string;
  readonly seed_node_id: string;
  readonly node_ids: readonly string[];
  readonly association_ids: readonly string[];
  readonly topology_family: string;
  readonly semantic_hash: string;
  readonly label: string;
  readonly description: string;
}

export interface ExplorationV2StateDto {
  readonly state_id: string;
  readonly state_hash: string;
  readonly category_entry_id: string;
  readonly composition_id: string;
  readonly seed_id: string;
  readonly focused_node_id: string;
  readonly expanded_node_ids: readonly string[];
  readonly visible_node_ids: readonly string[];
  readonly visible_association_ids: readonly string[];
  readonly available_actions: readonly ExplorationV2Action[];
  readonly semantic_hash: string;
  readonly presentation_hash: string;
  readonly database_snapshot: string;
}

export interface ExplorationV2MapNodeDto extends ExplorationV2VocabularyDto {
  readonly focused: boolean;
  readonly expanded: boolean;
  readonly position: {
    readonly normalised_x: number;
    readonly normalised_y: number;
  };
}

export interface ExplorationV2PlainTextTreeDto {
  readonly tree_version: "trace-exploration-plain-text-tree-v2";
  readonly composition_id: string;
  readonly root_node_id: string;
  readonly tree_node_ids: readonly string[];
  readonly tree_association_ids: readonly string[];
  readonly visible_association_ids: readonly string[];
  readonly plain_text_tree: string;
  readonly plain_text_tree_ascii: string;
}

export interface ExplorationV2MapDto {
  readonly api_version: typeof TRACE_EXPLORATION_V2_API_VERSION;
  readonly database_snapshot: string;
  readonly map_id: string;
  readonly is_initial_state: boolean;
  readonly category: ExplorationV2CategoryDto;
  readonly state: ExplorationV2StateDto;
  readonly composition: ExplorationV2CompositionDto;
  readonly nodes: readonly ExplorationV2MapNodeDto[];
  readonly associations: readonly ExplorationV2AssociationDto[];
  readonly plain_text_tree: ExplorationV2PlainTextTreeDto;
  readonly map_summary: string;
}

export interface ExplorationV2CategoriesResponse {
  readonly api_version: typeof TRACE_EXPLORATION_V2_API_VERSION;
  readonly database_snapshot: string;
  readonly categories: readonly ExplorationV2CategoryDto[];
}

export interface ExplorationV2CapabilitiesResponse {
  readonly api_version: typeof TRACE_EXPLORATION_V2_API_VERSION;
  readonly database_snapshot: string;
  readonly category_count: 4;
  readonly category_entry_count: 81;
  readonly vocabulary_count: 31;
  readonly association_count: 21;
  readonly composition_count: 228;
  readonly state_count: 5_760;
  readonly transition_count: 749_944;
  readonly maximum_visible_nodes: 8;
  readonly supported_actions: readonly ExplorationV2Action[];
  readonly topology_families: readonly string[];
  readonly export: {
    readonly presets: readonly ExplorationV2ExportPreset[];
    readonly theme_token_sets: readonly ExplorationV2Theme[];
    readonly width: 1080;
    readonly height: 1620;
  };
}

export interface ExplorationV2VocabularyResponse {
  readonly api_version: typeof TRACE_EXPLORATION_V2_API_VERSION;
  readonly database_snapshot: string;
  readonly vocabulary: ExplorationV2VocabularyDto;
}

export interface ExplorationV2AssociationResponse {
  readonly api_version: typeof TRACE_EXPLORATION_V2_API_VERSION;
  readonly database_snapshot: string;
  readonly association: ExplorationV2AssociationDto;
}

export interface ExplorationV2ExportManifestDto {
  readonly manifest_version: "trace-exploration-export-manifest-v2";
  readonly api_version: typeof TRACE_EXPLORATION_V2_API_VERSION;
  readonly render_version: "trace-exploration-portrait-png-v2";
  readonly export_id: string;
  readonly database_snapshot: string;
  readonly map_id: string;
  readonly state_id: string;
  readonly state_hash: string;
  readonly category_entry_id: string;
  readonly composition_id: string;
  readonly seed_id: string;
  readonly export_preset: ExplorationV2ExportPreset;
  readonly theme_token_set: ExplorationV2Theme;
  readonly dimensions: { readonly width: 1080; readonly height: 1620 };
  readonly category: ExplorationV2CategoryDto;
  readonly nodes: readonly ExplorationV2MapNodeDto[];
  readonly associations: readonly ExplorationV2AssociationDto[];
  readonly plain_text_tree: ExplorationV2PlainTextTreeDto;
  readonly node_count: number;
  readonly association_count: number;
  readonly provenance_summary: {
    readonly association_count: number;
    readonly externally_supported_count: number;
    readonly source_supported_count: number;
    readonly generic_association_only: true;
    readonly source_locators_withheld_from_public_export: true;
  };
  readonly semantic_hash: string;
  readonly presentation_hash: string;
  readonly export_alt_text: string;
  readonly suggested_filename: string;
}

export type ExplorationV2ErrorCode =
  | "ACTION_NOT_AVAILABLE"
  | "INTERNAL_DATA_INTEGRITY_FAILURE"
  | "INVALID_ACTION"
  | "INVALID_ASSOCIATION"
  | "INVALID_CATEGORY"
  | "INVALID_CATEGORY_ENTRY"
  | "INVALID_EXPORT_PRESET"
  | "INVALID_REQUEST"
  | "INVALID_VOCABULARY"
  | "METHOD_NOT_ALLOWED"
  | "NO_EXPORTABLE_COMPOSITION"
  | "RENDER_CAPACITY_EXCEEDED"
  | "REQUEST_LIMIT_EXCEEDED"
  | "STALE_EXPLORATION_STATE"
  | "STATE_DATABASE_VERSION_MISMATCH"
  | "STATE_NOT_FOUND";

export interface ExplorationV2ApiError {
  readonly schema_version: "trace-exploration-api-error-v2";
  readonly api_version: typeof TRACE_EXPLORATION_V2_API_VERSION;
  readonly code: ExplorationV2ErrorCode;
  readonly message: string;
  readonly status: number;
  readonly retryable: boolean;
  readonly instance: string;
  readonly database_snapshot: string;
}

export type ExplorationV2ServiceResult<T> =
  | { readonly ok: true; readonly data: T }
  | {
      readonly ok: false;
      readonly code: ExplorationV2ErrorCode;
      readonly message: string;
      readonly status: number;
      readonly retryable?: boolean;
    };
