import "server-only";

import { getExplorationV3RuntimeReadModel } from "./read-model.server.ts";
import { TRACE_EXPLORATION_V3_API_VERSION } from "./types.ts";
import type {
  ExplorationV3ErrorCode,
  ExplorationV3CollectionDtoMap,
  ExplorationV3ReadModel,
  ExplorationV3ResponseEnvelope,
  ExplorationV3ServiceResult,
  ExplorationV3Surface,
} from "./types.ts";

const MAXIMUM_IDENTIFIER_LENGTH = 512;

export const EXPLORATION_V3_COLLECTIONS = Object.freeze({
  "association-realizations": {
    identity: "association_realization_id",
    surfaceKey: "association_realizations",
  },
  associations: { identity: "association_id", surfaceKey: "associations" },
  "composition-coherence-reviews": {
    identity: "composition_coherence_review_id",
    surfaceKey: "composition_coherence_reviews",
  },
  compositions: { identity: "composition_id", surfaceKey: "compositions" },
  "concept-senses": { identity: "sense_id", surfaceKey: "concept_senses" },
  concepts: { identity: "concept_id", surfaceKey: "concepts" },
  exports: { identity: "export_id", surfaceKey: "exports" },
  incidences: { identity: "incidence_id", surfaceKey: "incidences" },
  "navigation-states": { identity: "state_id", surfaceKey: "navigation_states" },
  scopes: { identity: "scope_id", surfaceKey: "scopes" },
  transitions: { identity: "transition_id", surfaceKey: "transitions" },
  workflows: { identity: "workflow_id", surfaceKey: "workflows" },
} as const satisfies Readonly<Record<keyof ExplorationV3CollectionDtoMap, {
  readonly identity: string;
  readonly surfaceKey: keyof ExplorationV3Surface;
}>>);

export type ExplorationV3CollectionPath = keyof typeof EXPLORATION_V3_COLLECTIONS;

function success<T>(data: T): ExplorationV3ServiceResult<T> {
  const runtime = getExplorationV3RuntimeReadModel();
  const envelope: ExplorationV3ResponseEnvelope<T> = {
    api_version: TRACE_EXPLORATION_V3_API_VERSION,
    closure_flags: runtime.model.closure_flags,
    fact_boundary: runtime.model.fact_boundary,
    read_model_sha256: runtime.readModelSha256,
    data,
  };
  return { ok: true, data: envelope };
}

function failure<T>(
  code: ExplorationV3ErrorCode,
  message: string,
  status: number,
  retryable = false,
): ExplorationV3ServiceResult<T> {
  return { ok: false, code, message, status, retryable };
}

function validIdentifier(value: string): boolean {
  return value.length > 0 && value.length <= MAXIMUM_IDENTIFIER_LENGTH;
}

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function collectionItems<C extends ExplorationV3CollectionPath>(
  surface: ExplorationV3Surface,
  collection: C,
): readonly ExplorationV3CollectionDtoMap[C][] {
  const key = EXPLORATION_V3_COLLECTIONS[collection].surfaceKey;
  const records = surface as unknown as Readonly<Record<string, readonly unknown[]>>;
  const values = records[key] ?? [];
  if (!values.every(isRecord)) throw new Error("READ_MODEL_INVALID:collection_record");
  return values as unknown as readonly ExplorationV3CollectionDtoMap[C][];
}

function findItem<C extends ExplorationV3CollectionPath>(
  surface: ExplorationV3Surface,
  collection: C,
  identifier: string,
): ExplorationV3CollectionDtoMap[C] | undefined {
  const identity = EXPLORATION_V3_COLLECTIONS[collection].identity;
  return collectionItems(surface, collection).find(
    (item) => (item as unknown as Readonly<Record<string, unknown>>)[identity] === identifier,
  );
}

export function isExplorationV3CollectionPath(value: string): value is ExplorationV3CollectionPath {
  return Object.hasOwn(EXPLORATION_V3_COLLECTIONS, value);
}

export function retrieveExplorationV3Capabilities(): ExplorationV3ServiceResult<{
  readonly capabilities: ExplorationV3ReadModel["capabilities"];
  readonly contract_version: ExplorationV3ReadModel["contract_version"];
  readonly source_authority: ExplorationV3ReadModel["source_authority"];
}> {
  const { model } = getExplorationV3RuntimeReadModel();
  return success({
    capabilities: model.capabilities,
    contract_version: model.contract_version,
    source_authority: model.source_authority,
  });
}

export function retrieveExplorationV3BaselineReconciliation(): ExplorationV3ServiceResult<{
  readonly baseline_reconciliation: ExplorationV3ReadModel["baseline_reconciliation"];
}> {
  const { model } = getExplorationV3RuntimeReadModel();
  return success({ baseline_reconciliation: model.baseline_reconciliation });
}

export function listExplorationV3Collection<C extends ExplorationV3CollectionPath>(
  collection: C,
  control = false,
): ExplorationV3ServiceResult<{
  readonly collection: C;
  readonly count: number;
  readonly data_class: "ACTIVE_PRODUCT_FACT" | "SYNTHETIC_CONTROL";
  readonly items: readonly ExplorationV3CollectionDtoMap[C][];
}> {
  const { model } = getExplorationV3RuntimeReadModel();
  const surface = control ? model.research_controls : model.active_product;
  const items = collectionItems(surface, collection);
  return success({
    collection,
    count: items.length,
    data_class: control ? "SYNTHETIC_CONTROL" : "ACTIVE_PRODUCT_FACT",
    items,
  });
}

export function retrieveExplorationV3CollectionItem<C extends ExplorationV3CollectionPath>(
  collection: C,
  identifier: string,
  control = false,
): ExplorationV3ServiceResult<{
  readonly collection: C;
  readonly data_class: "ACTIVE_PRODUCT_FACT" | "SYNTHETIC_CONTROL";
  readonly item: ExplorationV3CollectionDtoMap[C];
}> {
  if (!validIdentifier(identifier)) {
    return failure("INVALID_CONTROL", "The requested governed identifier is invalid.", 404);
  }
  const { model } = getExplorationV3RuntimeReadModel();
  const surface = control ? model.research_controls : model.active_product;
  const item = findItem(surface, collection, identifier);
  if (item) {
    return success({
      collection,
      data_class: control ? "SYNTHETIC_CONTROL" : "ACTIVE_PRODUCT_FACT",
      item,
    });
  }
  if (!control && findItem(model.research_controls, collection, identifier)) {
    return failure(
      "NOT_ACTIVE_PRODUCT_FACT",
      "The identifier exists only in the synthetic research-control catalog and is not an active product fact.",
      404,
    );
  }
  const code = collection === "associations"
    ? "INVALID_ASSOCIATION"
    : collection === "compositions"
      ? "INVALID_COMPOSITION"
      : "INVALID_CONTROL";
  return failure(code, "The requested governed record is not available in this catalog.", 404);
}
