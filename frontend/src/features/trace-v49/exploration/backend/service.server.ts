import { getExplorationReadModel } from "./read-model.server.ts";
import { TRACE_EXPLORATION_ACTIONS } from "./types.ts";
import type { ExplorationActionRequest, ExplorationExportRequest, ExplorationMapRequest, ExplorationServiceResult } from "./types.ts";

const SHA256_PATTERN = /^[0-9a-f]{64}$/u;
function success<T>(data: T): ExplorationServiceResult<T> { return { ok: true, data }; }
function failure(code: string, message: string, status = 400, details?: Readonly<Record<string, unknown>>): ExplorationServiceResult<never> {
  return { ok: false, code, message, status, details };
}
function categoryById(categoryId: string) {
  return getExplorationReadModel().categories.find((item) => item.category_id === categoryId);
}
function mapResponse(category: any, stateId?: string) {
  const model = getExplorationReadModel();
  const map = model.maps[category.map_id];
  const selectedStateId = stateId ?? map.initial_state_id;
  const state = model.states[selectedStateId];
  if (!state || state.map_id !== map.map_id) return undefined;
  const composition = model.compositions[state.selected_composition_id];
  const tree = model.trees[`${composition.composition_id}|${state.focused_node_id}`];
  return {
    api_version: model.api_version,
    database_snapshot_id: model.database.database_snapshot_id,
    map,
    [stateId ? "state" : "initial_state"]: state,
    regions: map.map_regions,
    nodes: model.vocabulary.filter((item) => map.node_ids.includes(item.vocabulary_id)),
    associations: model.associations.filter((item) => map.association_ids.includes(item.association_id)),
    compositions: map.composition_ids.map((id: string) => model.compositions[id]),
    default_focus: map.default_focus,
    available_actions: state.available_actions,
    plain_text_tree: tree,
    provenance_summary: {
      archive_object_refs: map.archive_object_references,
      context_refs: map.context_references,
      spacetime_refs: map.spacetime_references,
      database_snapshot_id: model.database.database_snapshot_id,
    },
    semantic_hash: state.semantic_hash,
    state_hash: state.state_hash,
  };
}

export function listExplorationCategories(): ExplorationServiceResult<unknown> {
  const model = getExplorationReadModel();
  return success({
    api_version: model.api_version,
    database_snapshot_id: model.database.database_snapshot_id,
    categories: model.categories.map(({ archive_object_refs: _archive, context_refs: _context, spacetime_refs: _spacetime, ...category }) => category),
  });
}

export function createExplorationMap(request: unknown): ExplorationServiceResult<unknown> {
  if (!request || typeof request !== "object" || Array.isArray(request)) return failure("INVALID_CATEGORY", "A category_id is required.");
  const input = request as Partial<ExplorationMapRequest>;
  const category = categoryById(String(input.category_id ?? ""));
  if (!category) return failure("INVALID_CATEGORY", "The requested category is not one of the four canonical categories.");
  if (input.locale !== undefined && input.locale !== "en") return failure("INVALID_CATEGORY", "Only the governed English vocabulary is available in v1.");
  if (input.max_visible_nodes !== undefined && (!Number.isInteger(input.max_visible_nodes) || input.max_visible_nodes < 1 || input.max_visible_nodes > 40)) {
    return failure("REQUEST_LIMIT_EXCEEDED", "max_visible_nodes must be between 1 and 40.", 413, { maximum_nodes: 40 });
  }
  const response = mapResponse(category);
  return response ? success(response) : failure("INTERNAL_DATA_INTEGRITY_FAILURE", "The category map is not available from the governed read model.", 503);
}

export function retrieveExplorationMap(mapId: string, stateId?: string | null): ExplorationServiceResult<unknown> {
  const model = getExplorationReadModel();
  const map = model.maps[mapId];
  if (!map) return failure("STATE_NOT_FOUND", "The requested map does not exist.", 404);
  const response = mapResponse(categoryById(map.category_id), stateId || undefined);
  return response ? success(response) : failure("STATE_NOT_FOUND", "The requested state does not belong to this map.", 404);
}

export function applyExplorationAction(mapId: string, request: unknown): ExplorationServiceResult<unknown> {
  const model = getExplorationReadModel();
  const map = model.maps[mapId];
  if (!map) return failure("STATE_NOT_FOUND", "The requested map does not exist.", 404);
  if (!request || typeof request !== "object" || Array.isArray(request)) return failure("INVALID_ACTION", "An action request object is required.");
  const input = request as Partial<ExplorationActionRequest>;
  if (!TRACE_EXPLORATION_ACTIONS.includes(input.action as any)) return failure("INVALID_ACTION", "The requested browse action is not supported.");
  if (!input.expected_state_hash || !SHA256_PATTERN.test(input.expected_state_hash)) return failure("STALE_EXPLORATION_STATE", "A valid expected_state_hash is required.", 409);
  if (input.database_snapshot_id && input.database_snapshot_id !== model.database.database_snapshot_id) {
    return failure("STATE_DATABASE_VERSION_MISMATCH", "The request targets a different frozen database snapshot.", 409);
  }
  const currentStateId = model.states_by_hash[input.expected_state_hash];
  const currentState = currentStateId ? model.states[currentStateId] : undefined;
  if (!currentState || currentState.map_id !== mapId) return failure("STALE_EXPLORATION_STATE", "The expected state is stale or belongs to another map.", 409);
  const target = typeof input.target_id === "string" ? input.target_id : "";
  const nextStateId = model.transitions[`${input.expected_state_hash}|${input.action}|${target}`];
  if (!nextStateId) return failure("ACTION_NOT_AVAILABLE", "The action is not available for the requested target in this state.", 409);
  const response = mapResponse(categoryById(map.category_id), nextStateId);
  return response ? success(response) : failure("INTERNAL_DATA_INTEGRITY_FAILURE", "The governed transition target is missing.", 503);
}

export function retrieveExplorationVocabulary(vocabularyId: string): ExplorationServiceResult<unknown> {
  const model = getExplorationReadModel();
  if (vocabularyId.startsWith("HELD:")) return failure("HELD_DATA_BLOCKED", "Held archive identifiers are outside the public Exploration boundary.", 403);
  const item = model.vocabulary.find((row) => row.vocabulary_id === vocabularyId);
  return item ? success(item) : failure("INVALID_VOCABULARY", "The vocabulary identifier is not active.", 404);
}
export function retrieveExplorationAssociation(associationId: string): ExplorationServiceResult<unknown> {
  const model = getExplorationReadModel();
  if (associationId.startsWith("HELD:")) return failure("HELD_DATA_BLOCKED", "Held archive identifiers are outside the public Exploration boundary.", 403);
  const item = model.associations.find((row) => row.association_id === associationId);
  return item ? success(item) : failure("INVALID_ASSOCIATION", "The association identifier is not qualified for product proximity.", 404);
}
export function retrieveExplorationCapabilities(): ExplorationServiceResult<unknown> {
  return success(getExplorationReadModel().capabilities);
}

export function createExplorationExportManifest(request: unknown): ExplorationServiceResult<any> {
  const model = getExplorationReadModel();
  if (!request || typeof request !== "object" || Array.isArray(request)) return failure("INVALID_EXPORT_PRESET", "An export request object is required.");
  const input = request as Partial<ExplorationExportRequest>;
  if (input.export_preset !== "portrait_card" || !["neutral-v1", "neutral-contrast-v1"].includes(String(input.theme_token_set))) {
    return failure("INVALID_EXPORT_PRESET", "The requested export preset or theme token set is unsupported.");
  }
  const map = input.map_id ? model.maps[input.map_id] : undefined;
  if (!map) return failure("STATE_NOT_FOUND", "The export map does not exist.", 404);
  const stateId = input.state_hash ? model.states_by_hash[input.state_hash] : undefined;
  const state = stateId ? model.states[stateId] : undefined;
  if (!state || state.map_id !== input.map_id) return failure("STALE_EXPLORATION_STATE", "The export state is stale or belongs to another map.", 409);
  if (state.selected_composition_id !== input.selected_composition_id) return failure("NO_EXPORTABLE_COMPOSITION", "The selected composition does not match the state.", 409);
  const key = `${state.state_hash}|${state.selected_composition_id}|portrait_card|${input.theme_token_set}`;
  const manifest = model.export_manifests[key];
  return manifest ? success(manifest) : failure("NO_EXPORTABLE_COMPOSITION", "No governed export manifest exists for this state.", 409);
}
