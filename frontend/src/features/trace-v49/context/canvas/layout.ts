import type { TraceContextDataset } from "../types";
import { contextCanvasRepresentationByEntityId } from "./model";
import {
  CONTEXT_CANVAS_MAX_ZOOM,
  CONTEXT_CANVAS_MIN_ZOOM,
  CONTEXT_CANVAS_NODE_HEIGHT,
  CONTEXT_CANVAS_NODE_WIDTH,
  contextCanvasEntityId,
  type ContextCanvasBounds,
  type ContextCanvasDataMetadata,
  type ContextCanvasDataMode,
  type ContextCanvasEntityId,
  type ContextCanvasPosition,
  type ContextCanvasViewport,
  type ContextCanvasViewportSize,
} from "./types";

const LANE_X = Object.freeze({
  root: 64,
  controlled: 384,
  curated: 704,
  semantic: 1_024,
  other: 1_344,
});
const LANE_Y = 72;
const LANE_GAP_Y = 136;

function compareEntityIds(left: ContextCanvasEntityId, right: ContextCanvasEntityId): number {
  return left < right ? -1 : left > right ? 1 : 0;
}

export function autoArrangeContextCanvas(
  dataset: TraceContextDataset,
  visibleEntityIds: readonly ContextCanvasEntityId[],
  dataMode: ContextCanvasDataMode = "synthetic_contract",
  metadata?: ContextCanvasDataMetadata,
): Readonly<Record<ContextCanvasEntityId, ContextCanvasPosition>> {
  const visible = new Set(visibleEntityIds);
  const rootId = contextCanvasEntityId(dataset.selectedRecord);
  const controlled = new Set(
    dataset.controlledAssignments.map((item) => contextCanvasEntityId(item.value)),
  );
  if (dataMode === "governed_context_v1") {
    if (!metadata) throw new Error("Governed Context layout requires metadata.");
    for (const entityId of contextCanvasRepresentationByEntityId(dataMode, metadata).keys()) {
      controlled.add(entityId);
    }
  }
  const curated = new Set(
    dataset.curatedMemberships.map((item) => contextCanvasEntityId(item.container)),
  );
  const semantic = new Set(
    dataset.semanticEdges.flatMap((item) => [
      contextCanvasEntityId(item.subject),
      contextCanvasEntityId(item.object),
    ]),
  );
  const lanes: Record<keyof typeof LANE_X, ContextCanvasEntityId[]> = {
    root: [],
    controlled: [],
    curated: [],
    semantic: [],
    other: [],
  };

  for (const entityId of visible) {
    if (entityId === rootId) lanes.root.push(entityId);
    else if (controlled.has(entityId)) lanes.controlled.push(entityId);
    else if (curated.has(entityId)) lanes.curated.push(entityId);
    else if (semantic.has(entityId)) lanes.semantic.push(entityId);
    else lanes.other.push(entityId);
  }

  const positions: Record<ContextCanvasEntityId, ContextCanvasPosition> = {};
  for (const lane of Object.keys(lanes) as Array<keyof typeof lanes>) {
    const sorted = [...lanes[lane]].sort(compareEntityIds);
    sorted.forEach((entityId, index) => {
      positions[entityId] = Object.freeze({
        x: LANE_X[lane],
        y: LANE_Y + index * LANE_GAP_Y,
      });
    });
  }
  return Object.freeze(positions);
}

export function computeContextCanvasBounds(
  visibleEntityIds: readonly ContextCanvasEntityId[],
  positions: Readonly<Record<ContextCanvasEntityId, ContextCanvasPosition>>,
): ContextCanvasBounds {
  let minX = Number.POSITIVE_INFINITY;
  let minY = Number.POSITIVE_INFINITY;
  let maxX = Number.NEGATIVE_INFINITY;
  let maxY = Number.NEGATIVE_INFINITY;
  let count = 0;

  for (const entityId of visibleEntityIds) {
    const position = positions[entityId];
    if (!position || !Number.isFinite(position.x) || !Number.isFinite(position.y)) continue;
    minX = Math.min(minX, position.x);
    minY = Math.min(minY, position.y);
    maxX = Math.max(maxX, position.x + CONTEXT_CANVAS_NODE_WIDTH);
    maxY = Math.max(maxY, position.y + CONTEXT_CANVAS_NODE_HEIGHT);
    count += 1;
  }

  if (count === 0) return Object.freeze({ x: 0, y: 0, width: 0, height: 0, empty: true });
  return Object.freeze({
    x: minX,
    y: minY,
    width: maxX - minX,
    height: maxY - minY,
    empty: false,
  });
}

export function fitContextCanvasViewport(
  bounds: ContextCanvasBounds,
  viewportSize: ContextCanvasViewportSize,
  padding = 56,
): ContextCanvasViewport {
  if (bounds.empty) return Object.freeze({ x: 0, y: 0, zoom: 1 });
  const width = Number.isFinite(viewportSize.width) && viewportSize.width > 0
    ? viewportSize.width
    : 1;
  const height = Number.isFinite(viewportSize.height) && viewportSize.height > 0
    ? viewportSize.height
    : 1;
  const safePadding = Number.isFinite(padding) ? Math.max(0, padding) : 0;
  const availableWidth = Math.max(1, width - safePadding * 2);
  const availableHeight = Math.max(1, height - safePadding * 2);
  const rawZoom = Math.min(availableWidth / bounds.width, availableHeight / bounds.height);
  const zoom = Math.min(CONTEXT_CANVAS_MAX_ZOOM, Math.max(CONTEXT_CANVAS_MIN_ZOOM, rawZoom));
  return Object.freeze({
    x: (width - bounds.width * zoom) / 2 - bounds.x * zoom,
    y: (height - bounds.height * zoom) / 2 - bounds.y * zoom,
    zoom,
  });
}
