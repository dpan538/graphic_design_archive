import type { TraceContextDataset } from "../types";
import { initializeContextCanvasTemplate } from "./templates";
import {
  CONTEXT_CANVAS_HISTORY_LIMIT,
  CONTEXT_CANVAS_SCHEMA_VERSION,
  contextCanvasEntityId,
  isFiniteCanvasPosition,
  type ContextCanvasComposition,
  type ContextCanvasState,
  type ContextCanvasViewport,
} from "./types";
import { CONTEXT_CANVAS_DEFAULT_VIEWPORT, sanitizeContextCanvasViewport } from "./viewport";

export function createInitializingContextCanvasState(
  dataset: TraceContextDataset,
): ContextCanvasState {
  const present = initializeContextCanvasTemplate(dataset, "context-overview");
  return Object.freeze({
    schemaVersion: CONTEXT_CANVAS_SCHEMA_VERSION,
    rootEntityId: contextCanvasEntityId(dataset.selectedRecord),
    allowedEntityIds: Object.freeze(dataset.items.map(contextCanvasEntityId).sort()),
    history: Object.freeze({ past: Object.freeze([]), present, future: Object.freeze([]) }),
    viewport: CONTEXT_CANVAS_DEFAULT_VIEWPORT,
    selection: null,
    phase: "INITIALIZING",
    interaction: Object.freeze({ mode: "READY" }),
    statusMessage: "Initializing Context Canvas.",
    exportError: null,
  });
}

export function contextCanvasCompositionsEqual(
  left: ContextCanvasComposition,
  right: ContextCanvasComposition,
): boolean {
  return JSON.stringify(left) === JSON.stringify(right);
}

export function boundContextCanvasHistory(
  values: readonly ContextCanvasComposition[],
): readonly ContextCanvasComposition[] {
  return Object.freeze(values.slice(-CONTEXT_CANVAS_HISTORY_LIMIT));
}

export function isCompositionValidForState(
  state: Pick<ContextCanvasState, "allowedEntityIds" | "rootEntityId">,
  composition: ContextCanvasComposition,
): boolean {
  const allowed = new Set(state.allowedEntityIds);
  const visible = composition.visibleEntityIds;
  if (!visible.includes(state.rootEntityId) || new Set(visible).size !== visible.length) return false;
  for (const entityId of visible) {
    if (!allowed.has(entityId) || !isFiniteCanvasPosition(composition.positions[entityId])) return false;
  }
  return Object.keys(composition.positions).every((entityId) => visible.includes(entityId));
}

export function commitContextCanvasComposition(
  state: ContextCanvasState,
  next: ContextCanvasComposition,
  statusMessage: string,
): ContextCanvasState {
  if (!isCompositionValidForState(state, next)) return state;
  if (contextCanvasCompositionsEqual(state.history.present, next)) {
    return Object.freeze({ ...state, statusMessage, interaction: Object.freeze({ mode: "READY" }) });
  }
  return Object.freeze({
    ...state,
    history: Object.freeze({
      past: boundContextCanvasHistory([...state.history.past, state.history.present]),
      present: next,
      future: Object.freeze([]),
    }),
    selection: null,
    interaction: Object.freeze({ mode: "READY" }),
    phase: "READY",
    exportError: null,
    statusMessage,
  });
}

export function restoreContextCanvasWorkspace(
  state: ContextCanvasState,
  composition: ContextCanvasComposition,
  viewport: ContextCanvasViewport,
): ContextCanvasState {
  if (!isCompositionValidForState(state, composition)) {
    return Object.freeze({
      ...state,
      phase: "READY",
      interaction: Object.freeze({ mode: "READY" }),
      statusMessage: "Started the default Context Canvas template.",
    });
  }
  return Object.freeze({
    ...state,
    history: Object.freeze({ past: Object.freeze([]), present: composition, future: Object.freeze([]) }),
    viewport: sanitizeContextCanvasViewport(viewport),
    phase: "READY",
    interaction: Object.freeze({ mode: "READY" }),
    selection: null,
    exportError: null,
    statusMessage: "Restored the local Context Canvas composition.",
  });
}

export function contextCanvasFunctionalState(state: ContextCanvasState): string {
  if (state.phase !== "READY") return state.phase;
  if (state.interaction.mode !== "READY") return state.interaction.mode;
  if (state.selection?.kind === "node") return "NODE_SELECTED";
  if (state.selection?.kind === "connection") return "CONNECTION_SELECTED";
  return "READY";
}
