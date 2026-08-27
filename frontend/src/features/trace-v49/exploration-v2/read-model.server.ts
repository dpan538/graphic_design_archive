import "server-only";

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";
import {
  TRACE_EXPLORATION_V2_ACTIONS,
  TRACE_EXPLORATION_V2_API_VERSION,
  TRACE_EXPLORATION_V2_EXPORT_PRESETS,
  TRACE_EXPLORATION_V2_THEMES,
  TRACE_EXPLORATION_V2_TRANSITION_DERIVATION_VERSION,
} from "./types.ts";
import { getExplorationV2TransitionIndex } from "./transition.server.ts";
import type {
  ExplorationV2CategoryId,
  ExplorationV2ReadModel,
} from "./types.ts";

const SHA256_PATTERN = /^[0-9a-f]{64}$/u;
const DATABASE_SNAPSHOT = "v49:ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e";
const DATABASE_CONTENT_SHA256 = "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e";
const DATABASE_IDENTITY_SHA256 = "ec21af8af43b1fb9d661a18ac9b0223f561d28b06176deba78849d60535a2d3c";
const SOURCE_SHA = "8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e";
const CATEGORY_IDS = new Set<ExplorationV2CategoryId>(["region", "theme", "medium", "movement"]);
const ACTIONS = new Set<string>(TRACE_EXPLORATION_V2_ACTIONS);
const PRODUCTION_READ_MODEL_SHA256 = "53eaf59c95446eeb3781a7153183c54b3ff59fd52f21744cc917053959dfdcc9";
let validatedModel: ExplorationV2ReadModel | undefined;

const PRODUCTION_READ_MODEL_RELATIVE_PATH = path.join(
  "generated",
  "trace-exploration-v2",
  "production-read-model.json",
);

function loadProductionReadModel(): unknown {
  // Keep the multi-megabyte governed model out of TypeScript's program and the
  // JavaScript bundle. Next traces the file explicitly (see next.config.ts),
  // and the server process parses and validates it once on first use.
  const candidates = [
    path.join(process.cwd(), PRODUCTION_READ_MODEL_RELATIVE_PATH),
    path.join(process.cwd(), "frontend", PRODUCTION_READ_MODEL_RELATIVE_PATH),
  ];
  let source: Buffer | undefined;
  for (const candidate of candidates) {
    try {
      source = readFileSync(candidate);
      break;
    } catch {
      // Try the repository-root layout after the application-root layout.
    }
  }
  if (source === undefined) throw new Error("READ_MODEL_UNAVAILABLE:production_read_model");
  const sourceSha256 = createHash("sha256").update(source).digest("hex");
  if (sourceSha256 !== PRODUCTION_READ_MODEL_SHA256) {
    throw new Error("READ_MODEL_INVALID:production_read_model_sha256");
  }
  try {
    const parsed = JSON.parse(source.toString("utf8")) as unknown;
    if (isRecord(parsed) && isRecord(parsed.database)) {
      parsed.database.production_read_model_sha256 = sourceSha256;
    }
    return parsed;
  } catch {
    throw new Error("READ_MODEL_INVALID:json");
  }
}

function deepFreezeReadModel<T>(root: T): T {
  if (root === null || typeof root !== "object") return root;
  const pending: object[] = [root];
  const visited = new WeakSet<object>();
  while (pending.length > 0) {
    const current = pending.pop();
    if (!current || visited.has(current)) continue;
    visited.add(current);
    for (const value of Object.values(current)) {
      if (value !== null && typeof value === "object") pending.push(value);
    }
    Object.freeze(current);
  }
  return root;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function requireRecord(value: unknown, label: string): asserts value is Record<string, unknown> {
  if (!isRecord(value)) throw new Error(`READ_MODEL_INVALID:${label}`);
}

function requireString(value: unknown, label: string): asserts value is string {
  if (typeof value !== "string" || value.length === 0) throw new Error(`READ_MODEL_INVALID:${label}`);
}

function requireHash(value: unknown, label: string): asserts value is string {
  if (typeof value !== "string" || !SHA256_PATTERN.test(value)) throw new Error(`READ_MODEL_INVALID:${label}`);
}

function requirePositiveInteger(value: unknown, label: string): asserts value is number {
  if (!Number.isInteger(value) || (value as number) < 1) throw new Error(`READ_MODEL_INVALID:${label}`);
}

function requireStringArray(value: unknown, label: string): asserts value is string[] {
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string" || item.length === 0)) {
    throw new Error(`READ_MODEL_INVALID:${label}`);
  }
}

function requireUnique(values: readonly string[], label: string): void {
  if (new Set(values).size !== values.length) throw new Error(`READ_MODEL_DUPLICATE:${label}`);
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

function requireExactKeys(value: object, expected: readonly string[], label: string): void {
  const actual = Object.keys(value).sort(compareCodePoints);
  const wanted = [...expected].sort(compareCodePoints);
  if (actual.length !== wanted.length || actual.some((key, index) => key !== wanted[index])) {
    throw new Error(`READ_MODEL_INVALID:${label}`);
  }
}

function sameOrderedValues(left: readonly string[], right: readonly string[]): boolean {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}

function validateTopLevel(candidate: Record<string, unknown>): void {
  const exactKeys = [
    "associations",
    "capabilities",
    "categories",
    "compositions",
    "database",
    "states",
    "states_by_hash",
    "transitions",
    "vocabulary",
  ];
  const actualKeys = Reflect.ownKeys(candidate)
    .filter((key): key is string => typeof key === "string")
    .sort(compareCodePoints);
  if (actualKeys.length !== exactKeys.length || actualKeys.some((key, index) => key !== exactKeys[index])) {
    throw new Error("READ_MODEL_INVALID:top_level_keys");
  }
  requireRecord(candidate.database, "database");
  if (!Array.isArray(candidate.categories)) throw new Error("READ_MODEL_INVALID:categories");
  if (!Array.isArray(candidate.vocabulary)) throw new Error("READ_MODEL_INVALID:vocabulary");
  if (!Array.isArray(candidate.associations)) throw new Error("READ_MODEL_INVALID:associations");
  requireRecord(candidate.compositions, "compositions");
  requireRecord(candidate.states, "states");
  requireRecord(candidate.states_by_hash, "states_by_hash");
  requireRecord(candidate.transitions, "transitions");
  requireRecord(candidate.capabilities, "capabilities");
}

function validateReadModel(model: ExplorationV2ReadModel): void {
  requireExactKeys(model.database, [
    "database_content_sha256",
    "database_identity_sha256",
    "database_schema_version",
    "database_snapshot_id",
    "production_read_model_sha256",
    "release_id",
    "source_sha",
  ], "database.keys");
  if (
    model.database.database_snapshot_id !== DATABASE_SNAPSHOT
    || model.database.database_schema_version !== 49
    || model.database.database_content_sha256 !== DATABASE_CONTENT_SHA256
    || model.database.database_identity_sha256 !== DATABASE_IDENTITY_SHA256
    || model.database.release_id !== "v49"
    || model.database.source_sha !== SOURCE_SHA
    || model.database.production_read_model_sha256 !== PRODUCTION_READ_MODEL_SHA256
  ) throw new Error("READ_MODEL_INVALID:database.values");

  const vocabularyIds = new Set<string>();
  for (const item of model.vocabulary) {
    requireExactKeys(item, [
      "activation_status",
      "ambiguity_note",
      "attested_forms",
      "canonical_label",
      "language",
      "scope_note",
      "vocabulary_id",
    ], "vocabulary.keys");
    requireString(item.vocabulary_id, "vocabulary.vocabulary_id");
    requireString(item.canonical_label, "vocabulary.canonical_label");
    if (vocabularyIds.has(item.vocabulary_id)) throw new Error("READ_MODEL_DUPLICATE:vocabulary_id");
    vocabularyIds.add(item.vocabulary_id);
    requireStringArray(item.attested_forms, "vocabulary.attested_forms");
    if (item.attested_forms.length === 0 || item.language !== "en") throw new Error("READ_MODEL_INVALID:vocabulary.values");
    requireString(item.scope_note, "vocabulary.scope_note");
    requireString(item.ambiguity_note, "vocabulary.ambiguity_note");
    requireString(item.activation_status, "vocabulary.activation_status");
  }

  const associationIds = new Set<string>();
  for (const item of model.associations) {
    requireExactKeys(item, [
      "association_accessible_description",
      "association_id",
      "confidence",
      "endpoint_labels",
      "endpoint_vocabulary_ids",
      "explicit_non_claims",
      "generic_association_only",
      "strength",
      "support_status",
    ], "associations.keys");
    requireString(item.association_id, "associations.association_id");
    if (associationIds.has(item.association_id)) throw new Error("READ_MODEL_DUPLICATE:association_id");
    associationIds.add(item.association_id);
    requireStringArray(item.endpoint_vocabulary_ids, "associations.endpoint_vocabulary_ids");
    if (item.endpoint_vocabulary_ids.length !== 2 || item.endpoint_vocabulary_ids[0] === item.endpoint_vocabulary_ids[1]) {
      throw new Error("READ_MODEL_INVALID:association_endpoints");
    }
    if (item.endpoint_vocabulary_ids.some((id) => !vocabularyIds.has(id))) {
      throw new Error("READ_MODEL_INVALID:association_vocabulary_reference");
    }
    requireStringArray(item.endpoint_labels, "associations.endpoint_labels");
    if (item.endpoint_labels.length !== 2) throw new Error("READ_MODEL_INVALID:association_endpoint_labels");
    requireString(item.strength, "associations.strength");
    requireString(item.confidence, "associations.confidence");
    requireString(item.association_accessible_description, "associations.association_accessible_description");
    requireStringArray(item.explicit_non_claims, "associations.explicit_non_claims");
    if (item.explicit_non_claims.length === 0 || item.generic_association_only !== true) {
      throw new Error("READ_MODEL_INVALID:association_public_boundary");
    }
    if (
      item.support_status !== "ACTIVE_EXTERNALLY_SUPPORTED"
      && item.support_status !== "ACTIVE_SOURCE_SUPPORTED"
    ) {
      throw new Error("READ_MODEL_INVALID:association_support_status");
    }
  }

  const compositionIds = new Set<string>();
  for (const [key, item] of Object.entries(model.compositions)) {
    requireExactKeys(item, [
      "association_ids",
      "category_entry_id",
      "composition_id",
      "description",
      "label",
      "node_ids",
      "seed_id",
      "seed_node_id",
      "semantic_hash",
      "topology_family",
    ], "compositions.keys");
    requireString(item.composition_id, "compositions.composition_id");
    if (key !== item.composition_id || compositionIds.has(item.composition_id)) {
      throw new Error("READ_MODEL_INVALID:composition_key");
    }
    compositionIds.add(item.composition_id);
    requireString(item.category_entry_id, "compositions.category_entry_id");
    requireString(item.seed_id, "compositions.seed_id");
    requireString(item.seed_node_id, "compositions.seed_node_id");
    requireString(item.topology_family, "compositions.topology_family");
    requireString(item.label, "compositions.label");
    requireString(item.description, "compositions.description");
    requireHash(item.semantic_hash, "compositions.semantic_hash");
    requireStringArray(item.node_ids, "compositions.node_ids");
    requireStringArray(item.association_ids, "compositions.association_ids");
    requireUnique(item.node_ids, "composition.node_ids");
    requireUnique(item.association_ids, "composition.association_ids");
    if (item.node_ids.length < 2 || item.node_ids.length > 8) throw new Error("READ_MODEL_INVALID:composition_node_bound");
    if (!item.node_ids.includes(item.seed_node_id)) throw new Error("READ_MODEL_INVALID:composition_seed_node");
    if (item.node_ids.some((id) => !vocabularyIds.has(id)) || item.association_ids.some((id) => !associationIds.has(id))) {
      throw new Error("READ_MODEL_INVALID:composition_reference");
    }
  }

  const categoryEntries = new Set<string>();
  const observedCategories = new Set<ExplorationV2CategoryId>();
  for (const item of model.categories) {
    requireExactKeys(item, [
      "category_entry_id",
      "category_id",
      "composition_ids",
      "description",
      "entry_label",
      "initial_state_id",
      "label",
    ], "categories.keys");
    if (!CATEGORY_IDS.has(item.category_id)) throw new Error("READ_MODEL_INVALID:category_id");
    requireString(item.category_entry_id, "categories.category_entry_id");
    if (categoryEntries.has(item.category_entry_id)) throw new Error("READ_MODEL_DUPLICATE:category_entry_id");
    categoryEntries.add(item.category_entry_id);
    observedCategories.add(item.category_id);
    requireString(item.label, "categories.label");
    requireString(item.entry_label, "categories.entry_label");
    requireString(item.description, "categories.description");
    requireStringArray(item.composition_ids, "categories.composition_ids");
    requireUnique(item.composition_ids, "category.composition_ids");
    if (item.composition_ids.length === 0 || item.composition_ids.some((id) => !compositionIds.has(id))) {
      throw new Error("READ_MODEL_INVALID:category_composition_reference");
    }
    requireString(item.initial_state_id, "categories.initial_state_id");
    for (const compositionId of item.composition_ids) {
      if (model.compositions[compositionId]?.category_entry_id !== item.category_entry_id) {
        throw new Error("READ_MODEL_INVALID:composition_category_entry");
      }
    }
  }
  if (observedCategories.size !== CATEGORY_IDS.size) throw new Error("READ_MODEL_INVALID:four_category_contract");

  for (const [key, item] of Object.entries(model.states)) {
    requireExactKeys(item, [
      "available_actions",
      "category_entry_id",
      "composition_id",
      "database_snapshot",
      "expanded_node_ids",
      "focused_node_id",
      "presentation_hash",
      "seed_id",
      "semantic_hash",
      "state_hash",
      "state_id",
      "visible_association_ids",
      "visible_node_ids",
    ], "states.keys");
    requireString(item.state_id, "states.state_id");
    if (key !== item.state_id) throw new Error("READ_MODEL_INVALID:state_key");
    requireHash(item.state_hash, "states.state_hash");
    requireString(item.category_entry_id, "states.category_entry_id");
    requireString(item.composition_id, "states.composition_id");
    requireString(item.seed_id, "states.seed_id");
    requireString(item.focused_node_id, "states.focused_node_id");
    requireStringArray(item.expanded_node_ids, "states.expanded_node_ids");
    requireStringArray(item.visible_node_ids, "states.visible_node_ids");
    requireStringArray(item.visible_association_ids, "states.visible_association_ids");
    requireUnique(item.expanded_node_ids, "state.expanded_node_ids");
    requireUnique(item.visible_node_ids, "state.visible_node_ids");
    requireUnique(item.visible_association_ids, "state.visible_association_ids");
    requireHash(item.semantic_hash, "states.semantic_hash");
    requireHash(item.presentation_hash, "states.presentation_hash");
    requireString(item.database_snapshot, "states.database_snapshot");
    if (item.database_snapshot !== model.database.database_snapshot_id) throw new Error("READ_MODEL_INVALID:state_snapshot");
    if (!categoryEntries.has(item.category_entry_id)) throw new Error("READ_MODEL_INVALID:state_category_entry");
    const composition = model.compositions[item.composition_id];
    if (!composition || composition.category_entry_id !== item.category_entry_id || composition.seed_id !== item.seed_id) {
      throw new Error("READ_MODEL_INVALID:state_composition");
    }
    if (item.visible_node_ids.length === 0 || item.visible_node_ids.length > 8 || !item.visible_node_ids.includes(item.focused_node_id)) {
      throw new Error("READ_MODEL_INVALID:state_visible_nodes");
    }
    if (item.visible_node_ids.some((id) => !composition.node_ids.includes(id))) {
      throw new Error("READ_MODEL_INVALID:state_node_reference");
    }
    if (item.expanded_node_ids.some((id) => !item.visible_node_ids.includes(id))) {
      throw new Error("READ_MODEL_INVALID:state_expansion_reference");
    }
    if (item.visible_association_ids.some((id) => !composition.association_ids.includes(id))) {
      throw new Error("READ_MODEL_INVALID:state_association_reference");
    }
    if (!Array.isArray(item.available_actions) || item.available_actions.some((action) => !ACTIONS.has(action))) {
      throw new Error("READ_MODEL_INVALID:state_actions");
    }
    if (model.states_by_hash[item.state_hash] !== item.state_id) throw new Error("READ_MODEL_INVALID:state_hash_index");
  }

  for (const category of model.categories) {
    const initial = model.states[category.initial_state_id];
    if (!initial || initial.category_entry_id !== category.category_entry_id) {
      throw new Error("READ_MODEL_INVALID:category_initial_state");
    }
  }

  if (Object.keys(model.states_by_hash).length !== Object.keys(model.states).length) {
    throw new Error("READ_MODEL_INVALID:state_hash_index_size");
  }
  for (const [stateHash, stateId] of Object.entries(model.states_by_hash)) {
    requireHash(stateHash, "states_by_hash.key");
    if (model.states[stateId]?.state_hash !== stateHash) throw new Error("READ_MODEL_INVALID:state_hash_target");
  }

  requireExactKeys(model.transitions, ["derivation_version", "key_format", "transition_count"], "transitions.keys");
  if (
    model.transitions.derivation_version !== TRACE_EXPLORATION_V2_TRANSITION_DERIVATION_VERSION
    || model.transitions.key_format !== "state_hash|action|target"
  ) throw new Error("READ_MODEL_INVALID:transition_derivation_contract");
  requirePositiveInteger(model.transitions.transition_count, "transitions.transition_count");
  const transitionIndex = getExplorationV2TransitionIndex(model);
  if (transitionIndex.transitionCount !== model.transitions.transition_count) {
    throw new Error("READ_MODEL_INVALID:derived_transition_count");
  }

  const capabilities = model.capabilities;
  requireExactKeys(capabilities, [
    "actions",
    "api_version",
    "association_count",
    "category_count",
    "category_entry_count",
    "export_presets",
    "export_variant_count",
    "generic_association_only",
    "maximum_node_count",
    "production_composition_count",
    "state_count",
    "themes",
    "topology_composition_count",
    "transition_count",
    "vocabulary_count",
    "workflow_count",
  ], "capabilities.keys");
  for (const key of [
    "category_count",
    "category_entry_count",
    "vocabulary_count",
    "association_count",
    "topology_composition_count",
    "production_composition_count",
    "state_count",
    "transition_count",
    "workflow_count",
    "export_variant_count",
  ] as const) requirePositiveInteger(capabilities[key], `capabilities.${key}`);
  if (
    capabilities.api_version !== TRACE_EXPLORATION_V2_API_VERSION
    || capabilities.category_count !== CATEGORY_IDS.size
    || capabilities.category_entry_count !== 81
    || capabilities.vocabulary_count !== 31
    || capabilities.association_count !== 21
    || capabilities.topology_composition_count !== 81
    || capabilities.production_composition_count !== 228
    || capabilities.state_count !== 5_760
    || capabilities.transition_count !== 749_944
    || capabilities.workflow_count !== 5_760
    || capabilities.export_variant_count !== 11_520
    || capabilities.category_entry_count !== model.categories.length
    || capabilities.vocabulary_count !== model.vocabulary.length
    || capabilities.association_count !== model.associations.length
    || capabilities.production_composition_count !== Object.keys(model.compositions).length
    || capabilities.state_count !== Object.keys(model.states).length
    || capabilities.transition_count !== model.transitions.transition_count
    || capabilities.workflow_count !== Object.keys(model.states).length
    || capabilities.export_variant_count !== Object.keys(model.states).length
      * TRACE_EXPLORATION_V2_EXPORT_PRESETS.length * TRACE_EXPLORATION_V2_THEMES.length
    || capabilities.maximum_node_count !== 8
    || capabilities.generic_association_only !== true
    || !sameOrderedValues(capabilities.actions, TRACE_EXPLORATION_V2_ACTIONS)
    || !sameOrderedValues(capabilities.themes, TRACE_EXPLORATION_V2_THEMES)
    || !sameOrderedValues(capabilities.export_presets, TRACE_EXPLORATION_V2_EXPORT_PRESETS)
  ) throw new Error("READ_MODEL_INVALID:capabilities.values");
}

export function getExplorationV2ReadModel(): ExplorationV2ReadModel {
  if (validatedModel) return validatedModel;
  const raw = loadProductionReadModel();
  requireRecord(raw, "root");
  validateTopLevel(raw);
  const candidate = raw as unknown as ExplorationV2ReadModel;
  validateReadModel(candidate);
  // The transition table describes new state identity; actions never mutate
  // a governed state (or any other part of the read model) in place.
  validatedModel = deepFreezeReadModel(candidate);
  return candidate;
}
