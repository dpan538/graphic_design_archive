import type { TraceContextDataset } from "../types";
import { getContextCanvasTemplate } from "./templates";
import {
  CONTEXT_CANVAS_SCHEMA_VERSION,
  contextCanvasEntityId,
  isFiniteCanvasPosition,
  type ContextCanvasComposition,
  type ContextCanvasState,
  type ContextCanvasTemplateId,
  type ContextCanvasViewport,
} from "./types";
import { sanitizeContextCanvasViewport } from "./viewport";

const TEMPLATE_CATALOG_VERSION = 1;

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

export function contextCanvasPersistenceKey(dataset: TraceContextDataset): string {
  return [
    "trace-context-canvas",
    `schema-${CONTEXT_CANVAS_SCHEMA_VERSION}`,
    `templates-${TEMPLATE_CATALOG_VERSION}`,
    dataset.release.manifestSha256,
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
    template = getContextCanvasTemplate(payload.templateId as ContextCanvasTemplateId);
  } catch {
    return null;
  }
  if (template.version !== payload.templateVersion) return null;

  const allowed = new Set(dataset.items.map(contextCanvasEntityId));
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
): RestoredContextCanvasWorkspace | null {
  try {
    const serialized = storage.getItem(contextCanvasPersistenceKey(dataset));
    return serialized ? deserializeContextCanvasWorkspace(serialized, dataset) : null;
  } catch {
    return null;
  }
}

export function saveContextCanvasWorkspace(
  dataset: TraceContextDataset,
  state: ContextCanvasState,
  storage: Pick<Storage, "setItem">,
): boolean {
  try {
    storage.setItem(contextCanvasPersistenceKey(dataset), serializeContextCanvasWorkspace(state));
    return true;
  } catch {
    return false;
  }
}

export function clearContextCanvasWorkspace(
  dataset: TraceContextDataset,
  storage: Pick<Storage, "removeItem">,
): boolean {
  try {
    storage.removeItem(contextCanvasPersistenceKey(dataset));
    return true;
  } catch {
    return false;
  }
}
