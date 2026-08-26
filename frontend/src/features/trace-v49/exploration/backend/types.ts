export const TRACE_EXPLORATION_ACTIONS = [
  "SELECT_CATEGORY", "FOCUS_NODE", "EXPAND_NODE", "COLLAPSE_NODE",
  "MOVE_FOCUS", "SELECT_COMPOSITION", "RESET_CATEGORY", "EXPORT_CURRENT_STATE",
] as const;

export type ExplorationAction = (typeof TRACE_EXPLORATION_ACTIONS)[number];
export type ExplorationCategoryId = "region" | "theme" | "medium" | "movement";
export type ExplorationThemeTokenSet = "neutral-v1" | "neutral-contrast-v1";

export interface ExplorationMapRequest {
  readonly category_id: ExplorationCategoryId;
  readonly locale?: "en";
  readonly max_visible_nodes?: number;
  readonly include_context?: boolean;
  readonly include_spacetime?: boolean;
}

export interface ExplorationActionRequest {
  readonly action: ExplorationAction;
  readonly target_id?: string;
  readonly expected_state_hash: string;
  readonly database_snapshot_id?: string;
}

export interface ExplorationExportRequest {
  readonly map_id: string;
  readonly state_hash: string;
  readonly selected_composition_id: string;
  readonly export_preset: "portrait_card";
  readonly theme_token_set: ExplorationThemeTokenSet;
  readonly include_compact_provenance?: boolean;
}

export interface ExplorationApiError {
  readonly schema_version: "trace-exploration-api-error-v1";
  readonly api_version: string;
  readonly code: string;
  readonly message: string;
  readonly status: number;
  readonly retryable: boolean;
  readonly instance: string;
  readonly database_snapshot_id: string;
  readonly details?: Readonly<Record<string, unknown>>;
}

export interface ExplorationReadModel {
  readonly format: string;
  readonly api_version: string;
  readonly source_sha: string;
  readonly read_model_sha256: string;
  readonly database: Readonly<Record<string, unknown>> & { readonly database_snapshot_id: string };
  readonly categories: readonly any[];
  readonly maps: Readonly<Record<string, any>>;
  readonly vocabulary: readonly any[];
  readonly associations: readonly any[];
  readonly compositions: Readonly<Record<string, any>>;
  readonly states: Readonly<Record<string, any>>;
  readonly states_by_hash: Readonly<Record<string, string>>;
  readonly transitions: Readonly<Record<string, string>>;
  readonly trees: Readonly<Record<string, any>>;
  readonly export_manifests: Readonly<Record<string, any>>;
  readonly workflows: readonly any[];
  readonly capabilities: any;
}

export type ExplorationServiceResult<T> =
  | { readonly ok: true; readonly data: T }
  | { readonly ok: false; readonly code: string; readonly message: string; readonly status: number; readonly details?: Readonly<Record<string, unknown>> };
