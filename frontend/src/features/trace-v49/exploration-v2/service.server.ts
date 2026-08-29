import "server-only";

import {
  deriveExplorationV2ExportManifest,
  deriveExplorationV2Map,
  getExplorationV2AssociationById,
  getExplorationV2CategoryByEntry,
  getExplorationV2VocabularyById,
  toExplorationV2AssociationDto,
  toExplorationV2CategoryDto,
  toExplorationV2VocabularyDto,
} from "./derive.server.ts";
import { getExplorationV2ReadModel } from "./read-model.server.ts";
import { getExplorationV2TransitionIndex } from "./transition.server.ts";
import {
  TRACE_EXPLORATION_V2_ACTIONS,
  TRACE_EXPLORATION_V2_API_VERSION,
  TRACE_EXPLORATION_V2_EXPORT_PRESETS,
  TRACE_EXPLORATION_V2_THEMES,
} from "./types.ts";
import type {
  ExplorationV2Action,
  ExplorationV2ActionRequest,
  ExplorationV2AssociationResponse,
  ExplorationV2CapabilitiesResponse,
  ExplorationV2CategoriesResponse,
  ExplorationV2CategoryId,
  ExplorationV2ErrorCode,
  ExplorationV2ExportManifestDto,
  ExplorationV2ExportRequest,
  ExplorationV2MapDto,
  ExplorationV2ServiceResult,
  ExplorationV2StateRecord,
  ExplorationV2Theme,
  ExplorationV2VocabularyResponse,
} from "./types.ts";

const SHA256_PATTERN = /^[0-9a-f]{64}$/u;
const CATEGORY_IDS = new Set<string>(["region", "theme", "medium", "movement"]);
const ACTIONS = new Set<string>(TRACE_EXPLORATION_V2_ACTIONS);
const THEMES = new Set<string>(TRACE_EXPLORATION_V2_THEMES);
const EXPORT_PRESETS = new Set<string>(TRACE_EXPLORATION_V2_EXPORT_PRESETS);
const MAXIMUM_IDENTIFIER_LENGTH = 256;

function success<T>(data: T): ExplorationV2ServiceResult<T> {
  return { ok: true, data };
}

function failure<T>(
  code: ExplorationV2ErrorCode,
  message: string,
  status: number,
  retryable = false,
): ExplorationV2ServiceResult<T> {
  return { ok: false, code, message, status, retryable };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function hasOnlyKeys(record: Readonly<Record<string, unknown>>, allowed: readonly string[]): boolean {
  const allowedKeys = new Set(allowed);
  return Object.keys(record).every((key) => allowedKeys.has(key));
}

function hasRequiredKeys(record: Readonly<Record<string, unknown>>, required: readonly string[]): boolean {
  return required.every((key) => Object.hasOwn(record, key));
}

function validIdentifier(value: unknown): value is string {
  return typeof value === "string" && value.length > 0 && value.length <= MAXIMUM_IDENTIFIER_LENGTH;
}

function compareCodePoints(left: string, right: string): number {
  const leftPoints = Array.from(left, (character) => character.codePointAt(0) ?? 0);
  const rightPoints = Array.from(right, (character) => character.codePointAt(0) ?? 0);
  const length = Math.min(leftPoints.length, rightPoints.length);
  for (let index = 0; index < length; index += 1) {
    if (leftPoints[index] !== rightPoints[index]) return leftPoints[index] - rightPoints[index];
  }
  return leftPoints.length - rightPoints.length;
}

function isCategoryId(value: unknown): value is ExplorationV2CategoryId {
  return typeof value === "string" && CATEGORY_IDS.has(value);
}

function stateForHash(stateHash: string): ExplorationV2StateRecord | undefined {
  const model = getExplorationV2ReadModel();
  const stateId = model.states_by_hash[stateHash];
  return stateId ? model.states[stateId] : undefined;
}

function stateForMap(state: ExplorationV2StateRecord | undefined, mapId: string): ExplorationV2StateRecord | undefined {
  return state?.category_entry_id === mapId ? state : undefined;
}

export function listExplorationV2Categories(): ExplorationV2ServiceResult<ExplorationV2CategoriesResponse> {
  const model = getExplorationV2ReadModel();
  return success({
    api_version: TRACE_EXPLORATION_V2_API_VERSION,
    database_snapshot: model.database.database_snapshot_id,
    categories: [...model.categories]
      .sort((left, right) => compareCodePoints(left.category_id, right.category_id)
        || compareCodePoints(left.category_entry_id, right.category_entry_id))
      .map(toExplorationV2CategoryDto),
  });
}

export function retrieveExplorationV2Capabilities(): ExplorationV2ServiceResult<ExplorationV2CapabilitiesResponse> {
  const model = getExplorationV2ReadModel();
  const topologyFamilies = [...new Set(Object.values(model.compositions).map((item) => item.topology_family))]
    .sort(compareCodePoints);
  return success({
    api_version: TRACE_EXPLORATION_V2_API_VERSION,
    database_snapshot: model.database.database_snapshot_id,
    category_count: model.capabilities.category_count,
    category_entry_count: model.capabilities.category_entry_count,
    vocabulary_count: model.capabilities.vocabulary_count,
    association_count: model.capabilities.association_count,
    composition_count: model.capabilities.production_composition_count,
    state_count: model.capabilities.state_count,
    transition_count: model.transitions.transition_count,
    maximum_visible_nodes: 8,
    supported_actions: [...TRACE_EXPLORATION_V2_ACTIONS],
    topology_families: topologyFamilies,
    export: {
      presets: [...TRACE_EXPLORATION_V2_EXPORT_PRESETS],
      theme_token_sets: [...TRACE_EXPLORATION_V2_THEMES],
      width: 1080,
      height: 1620,
    },
  });
}

export function createExplorationV2Map(request: unknown): ExplorationV2ServiceResult<ExplorationV2MapDto> {
  if (
    !isRecord(request)
    || !hasOnlyKeys(request, ["category_id", "category_entry_id", "locale"])
    || !hasRequiredKeys(request, ["category_id"])
  ) {
    return failure("INVALID_REQUEST", "A valid map request is required.", 400);
  }
  if (!isCategoryId(request.category_id)) {
    return failure("INVALID_CATEGORY", "The requested category is not canonical.", 404);
  }
  if (request.locale !== undefined && request.locale !== "en") {
    return failure("INVALID_REQUEST", "Only the governed English vocabulary is available.", 400);
  }
  if (request.category_entry_id !== undefined && !validIdentifier(request.category_entry_id)) {
    return failure("INVALID_CATEGORY_ENTRY", "The category entry identifier is invalid.", 404);
  }
  const model = getExplorationV2ReadModel();
  const candidates = model.categories
    .filter((item) => item.category_id === request.category_id)
    .sort((left, right) => compareCodePoints(left.category_entry_id, right.category_entry_id));
  const category = request.category_entry_id
    ? candidates.find((item) => item.category_entry_id === request.category_entry_id)
    : candidates[0];
  if (!category) return failure("INVALID_CATEGORY_ENTRY", "The requested category entry is not available.", 404);
  const state = model.states[category.initial_state_id];
  if (!state) return failure("INTERNAL_DATA_INTEGRITY_FAILURE", "The governed initial state is unavailable.", 503, true);
  return success(deriveExplorationV2Map(model, state));
}

export function retrieveExplorationV2Map(mapId: string, stateId?: string): ExplorationV2ServiceResult<ExplorationV2MapDto> {
  if (!validIdentifier(mapId) || !getExplorationV2CategoryByEntry(mapId)) {
    return failure("STATE_NOT_FOUND", "The requested map does not exist.", 404);
  }
  const model = getExplorationV2ReadModel();
  const category = getExplorationV2CategoryByEntry(mapId);
  const selectedStateId = stateId ?? category?.initial_state_id;
  if (!selectedStateId || !validIdentifier(selectedStateId)) {
    return failure("STATE_NOT_FOUND", "The requested state does not exist.", 404);
  }
  const state = stateForMap(model.states[selectedStateId], mapId);
  if (!state) return failure("STATE_NOT_FOUND", "The requested state does not belong to this map.", 404);
  return success(deriveExplorationV2Map(model, state));
}

export function applyExplorationV2Action(
  mapId: string,
  request: unknown,
): ExplorationV2ServiceResult<ExplorationV2MapDto> {
  if (!validIdentifier(mapId) || !getExplorationV2CategoryByEntry(mapId)) {
    return failure("STATE_NOT_FOUND", "The requested map does not exist.", 404);
  }
  if (
    !isRecord(request)
    || !hasOnlyKeys(request, ["action", "target_id", "expected_state_hash", "database_snapshot"])
    || !hasRequiredKeys(request, ["action", "expected_state_hash"])
  ) {
    return failure("INVALID_REQUEST", "A valid action request is required.", 400);
  }
  if (typeof request.action !== "string" || !ACTIONS.has(request.action)) {
    return failure("INVALID_ACTION", "The requested browse action is not supported.", 400);
  }
  if (typeof request.expected_state_hash !== "string" || !SHA256_PATTERN.test(request.expected_state_hash)) {
    return failure("INVALID_REQUEST", "A valid expected state hash is required.", 400);
  }
  if (request.target_id !== undefined && !validIdentifier(request.target_id)) {
    return failure("INVALID_ACTION", "The action target identifier is invalid.", 400);
  }
  if (request.database_snapshot !== undefined && !validIdentifier(request.database_snapshot)) {
    return failure("STATE_DATABASE_VERSION_MISMATCH", "The database snapshot identifier is invalid.", 409);
  }

  const input: ExplorationV2ActionRequest = {
    action: request.action as ExplorationV2Action,
    expected_state_hash: request.expected_state_hash,
    ...(typeof request.target_id === "string" ? { target_id: request.target_id } : {}),
    ...(typeof request.database_snapshot === "string" ? { database_snapshot: request.database_snapshot } : {}),
  };
  const model = getExplorationV2ReadModel();
  if (input.database_snapshot && input.database_snapshot !== model.database.database_snapshot_id) {
    return failure("STATE_DATABASE_VERSION_MISMATCH", "The request targets a different frozen database snapshot.", 409);
  }
  const currentState = stateForMap(stateForHash(input.expected_state_hash), mapId);
  if (!currentState) {
    return failure("STALE_EXPLORATION_STATE", "The expected state is stale or belongs to another map.", 409);
  }
  if (!currentState.available_actions.includes(input.action)) {
    return failure("ACTION_NOT_AVAILABLE", "The action is not available in the expected state.", 409);
  }
  const transition = getExplorationV2TransitionIndex(model).resolve(currentState, input.action, input.target_id ?? "");
  if (!transition) return failure("ACTION_NOT_AVAILABLE", "The action is not available for the requested target.", 409);
  return success(deriveExplorationV2Map(model, transition.next_state));
}

export function retrieveExplorationV2Vocabulary(
  vocabularyId: string,
): ExplorationV2ServiceResult<ExplorationV2VocabularyResponse> {
  if (!validIdentifier(vocabularyId)) return failure("INVALID_VOCABULARY", "The vocabulary identifier is invalid.", 404);
  const item = getExplorationV2VocabularyById(vocabularyId);
  if (!item) return failure("INVALID_VOCABULARY", "The vocabulary identifier is not active.", 404);
  const model = getExplorationV2ReadModel();
  return success({
    api_version: TRACE_EXPLORATION_V2_API_VERSION,
    database_snapshot: model.database.database_snapshot_id,
    vocabulary: toExplorationV2VocabularyDto(item),
  });
}

export function retrieveExplorationV2Association(
  associationId: string,
): ExplorationV2ServiceResult<ExplorationV2AssociationResponse> {
  if (!validIdentifier(associationId)) return failure("INVALID_ASSOCIATION", "The association identifier is invalid.", 404);
  const item = getExplorationV2AssociationById(associationId);
  if (!item) return failure("INVALID_ASSOCIATION", "The association identifier is not active.", 404);
  const model = getExplorationV2ReadModel();
  return success({
    api_version: TRACE_EXPLORATION_V2_API_VERSION,
    database_snapshot: model.database.database_snapshot_id,
    association: toExplorationV2AssociationDto(item),
  });
}

function isTheme(value: unknown): value is ExplorationV2Theme {
  return typeof value === "string" && THEMES.has(value);
}

export function createExplorationV2ExportManifest(
  request: unknown,
): ExplorationV2ServiceResult<ExplorationV2ExportManifestDto> {
  if (
    !isRecord(request)
    || !hasOnlyKeys(request, ["map_id", "state_hash", "composition_id", "export_preset", "theme_token_set"])
    || !hasRequiredKeys(request, ["map_id", "state_hash", "composition_id", "export_preset", "theme_token_set"])
  ) {
    return failure("INVALID_REQUEST", "A valid export request is required.", 400);
  }
  if (!validIdentifier(request.map_id) || !getExplorationV2CategoryByEntry(request.map_id)) {
    return failure("STATE_NOT_FOUND", "The export map does not exist.", 404);
  }
  if (typeof request.state_hash !== "string" || !SHA256_PATTERN.test(request.state_hash)) {
    return failure("INVALID_REQUEST", "A valid export state hash is required.", 400);
  }
  if (!validIdentifier(request.composition_id)) {
    return failure("INVALID_REQUEST", "A valid export composition identifier is required.", 400);
  }
  if (typeof request.export_preset !== "string" || !EXPORT_PRESETS.has(request.export_preset) || !isTheme(request.theme_token_set)) {
    return failure("INVALID_EXPORT_PRESET", "The requested export preset or theme is unsupported.", 400);
  }
  const input: ExplorationV2ExportRequest = {
    map_id: request.map_id,
    state_hash: request.state_hash,
    composition_id: request.composition_id,
    export_preset: "portrait_card",
    theme_token_set: request.theme_token_set,
  };
  const model = getExplorationV2ReadModel();
  const state = stateForMap(stateForHash(input.state_hash), input.map_id);
  if (!state) return failure("STALE_EXPLORATION_STATE", "The export state is stale or belongs to another map.", 409);
  if (state.composition_id !== input.composition_id || !state.available_actions.includes("EXPORT_CURRENT_STATE")) {
    return failure("NO_EXPORTABLE_COMPOSITION", "The requested composition is not exportable from this state.", 409);
  }
  return success(deriveExplorationV2ExportManifest(model, state, input));
}
