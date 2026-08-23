import type { TraceContextDataset } from "../types";
import { contextCanvasEntityRefsForMode, getGovernedContextMetadata } from "./model";
import { getContextCanvasTemplate } from "./templates";
import {
  CONTEXT_CANVAS_SCHEMA_VERSION,
  contextCanvasEntityId,
  isFiniteCanvasPosition,
  type ContextCanvasComposition,
  type ContextCanvasDataMetadata,
  type ContextCanvasDataMode,
  type ContextCanvasState,
  type ContextCanvasTemplateId,
  type ContextCanvasViewport,
} from "./types";
import { sanitizeContextCanvasViewport } from "./viewport";

const TEMPLATE_CATALOG_VERSION = 2;

interface ContextCanvasPersistedPayload {
  readonly schemaVersion: typeof CONTEXT_CANVAS_SCHEMA_VERSION;
  readonly templateCatalogVersion: typeof TEMPLATE_CATALOG_VERSION;
  readonly templateId: ContextCanvasTemplateId;
  readonly templateVersion: number;
  readonly visibleEntityIds: readonly string[];
  readonly positions: Readonly<Record<string, Readonly<{ x: number; y: number }>>>;
  readonly viewport: ContextCanvasViewport;
}

export interface RestoredContextCanvasWorkspace {
  readonly composition: ContextCanvasComposition;
  readonly viewport: ContextCanvasViewport;
}

export function contextCanvasPersistenceKey(
  dataset: TraceContextDataset,
  dataMode: ContextCanvasDataMode = "synthetic_contract",
  metadata?: ContextCanvasDataMetadata,
): string {
  const governed = dataMode === "governed_context_v1"
    ? getGovernedContextMetadata(dataMode, metadata ?? invalidMissingMetadata())
    : null;
  return [
    "trace-context-canvas",
    `schema-${CONTEXT_CANVAS_SCHEMA_VERSION}`,
    `templates-${TEMPLATE_CATALOG_VERSION}`,
    dataMode,
    dataset.release.manifestSha256,
    governed?.projectionId ?? "no-context-projection",
    governed?.projectionSha256 ?? "no-context-projection-sha",
    encodeURIComponent(dataset.selectedRecord.stableId),
  ].join(":");
}

export function serializeContextCanvasWorkspace(state: ContextCanvasState): string {
  const present = state.history.present;
  const positions = Object.fromEntries(
    present.visibleEntityIds.map((entityId) => [
      entityId,
      { x: present.positions[entityId].x, y: present.positions[entityId].y },
    ]),
  );
  const payload: ContextCanvasPersistedPayload = {
    schemaVersion: CONTEXT_CANVAS_SCHEMA_VERSION,
    templateCatalogVersion: TEMPLATE_CATALOG_VERSION,
    templateId: present.templateId,
    templateVersion: present.templateVersion,
    visibleEntityIds: [...present.visibleEntityIds],
    positions,
    viewport: sanitizeContextCanvasViewport(state.viewport),
  };
  return JSON.stringify(payload);
}

export function deserializeContextCanvasWorkspace(
  serialized: string,
  dataset: TraceContextDataset,
  dataMode: ContextCanvasDataMode = "synthetic_contract",
  metadata?: ContextCanvasDataMetadata,
): RestoredContextCanvasWorkspace | null {
  let value: unknown;
  try {
    value = JSON.parse(serialized);
  } catch {
    return null;
  }
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const payload = value as Partial<ContextCanvasPersistedPayload>;
  if (
    payload.schemaVersion !== CONTEXT_CANVAS_SCHEMA_VERSION
    || payload.templateCatalogVersion !== TEMPLATE_CATALOG_VERSION
    || typeof payload.templateId !== "string"
    || !Number.isSafeInteger(payload.templateVersion)
    || !Array.isArray(payload.visibleEntityIds)
    || !payload.positions
    || typeof payload.positions !== "object"
    || !payload.viewport
  ) return null;

  let template;
  try {
    template = getContextCanvasTemplate(payload.templateId as ContextCanvasTemplateId, dataMode);
  } catch {
    return null;
  }
  if (template.version !== payload.templateVersion) return null;

  if (!metadata && dataMode !== "synthetic_contract") return null;
  const effectiveMetadata = metadata ?? syntheticPersistenceMetadata(dataset);
  const allowed = new Set(
    contextCanvasEntityRefsForMode(dataset, dataMode, effectiveMetadata)
      .map(contextCanvasEntityId),
  );
  const rootId = contextCanvasEntityId(dataset.selectedRecord);
  const visibleEntityIds = payload.visibleEntityIds;
  if (
    new Set(visibleEntityIds).size !== visibleEntityIds.length
    || !visibleEntityIds.includes(rootId)
    || visibleEntityIds.some((id) => typeof id !== "string" || !allowed.has(id))
  ) return null;

  const positionEntries: Array<readonly [string, Readonly<{ x: number; y: number }>]> = [];
  for (const entityId of visibleEntityIds) {
    const position = (payload.positions as Record<string, unknown>)[entityId];
    if (!isFiniteCanvasPosition(position)) return null;
    positionEntries.push([entityId, Object.freeze({ x: position.x, y: position.y })]);
  }
  if (Object.keys(payload.positions).some((entityId) => !visibleEntityIds.includes(entityId))) return null;

  const composition: ContextCanvasComposition = Object.freeze({
    templateId: payload.templateId as ContextCanvasTemplateId,
    templateVersion: payload.templateVersion,
    visibleEntityIds: Object.freeze([...visibleEntityIds]),
    positions: Object.freeze(Object.fromEntries(positionEntries)),
  });
  return Object.freeze({
    composition,
    viewport: sanitizeContextCanvasViewport(payload.viewport),
  });
}

export function loadContextCanvasWorkspace(
  dataset: TraceContextDataset,
  storage: Pick<Storage, "getItem">,
  dataMode: ContextCanvasDataMode = "synthetic_contract",
  metadata?: ContextCanvasDataMetadata,
): RestoredContextCanvasWorkspace | null {
  try {
    const serialized = storage.getItem(contextCanvasPersistenceKey(dataset, dataMode, metadata));
    return serialized
      ? deserializeContextCanvasWorkspace(serialized, dataset, dataMode, metadata)
      : null;
  } catch {
    return null;
  }
}

export function saveContextCanvasWorkspace(
  dataset: TraceContextDataset,
  state: ContextCanvasState,
  storage: Pick<Storage, "setItem">,
  dataMode: ContextCanvasDataMode = "synthetic_contract",
  metadata?: ContextCanvasDataMetadata,
): boolean {
  try {
    storage.setItem(
      contextCanvasPersistenceKey(dataset, dataMode, metadata),
      serializeContextCanvasWorkspace(state),
    );
    return true;
  } catch {
    return false;
  }
}

export function clearContextCanvasWorkspace(
  dataset: TraceContextDataset,
  storage: Pick<Storage, "removeItem">,
  dataMode: ContextCanvasDataMode = "synthetic_contract",
  metadata?: ContextCanvasDataMetadata,
): boolean {
  try {
    storage.removeItem(contextCanvasPersistenceKey(dataset, dataMode, metadata));
    return true;
  } catch {
    return false;
  }
}

function invalidMissingMetadata(): ContextCanvasDataMetadata {
  throw new Error("Governed Context persistence requires metadata.");
}

function syntheticPersistenceMetadata(dataset: TraceContextDataset): ContextCanvasDataMetadata {
  return {
    dataLabel: "synthetic contract fixture",
    mappingVersion: "synthetic-context-contract-v1",
    candidateState: "synthetic_contract",
    historicalEvidence: false,
    governedPublicRelease: false,
    publicReleaseData: false,
    publicObjectCohortCount: dataset.counts.denominator,
  };
}
