import {
  CONTEXT_CANVAS_MAX_ZOOM,
  CONTEXT_CANVAS_MIN_ZOOM,
  type ContextCanvasPosition,
  type ContextCanvasViewport,
} from "./types";

export const CONTEXT_CANVAS_DEFAULT_VIEWPORT: ContextCanvasViewport = Object.freeze({
  x: 0,
  y: 0,
  zoom: 1,
});

export function clampContextCanvasZoom(zoom: number): number {
  if (!Number.isFinite(zoom)) return 1;
  return Math.min(CONTEXT_CANVAS_MAX_ZOOM, Math.max(CONTEXT_CANVAS_MIN_ZOOM, zoom));
}

export function sanitizeContextCanvasViewport(
  viewport: ContextCanvasViewport,
): ContextCanvasViewport {
  return Object.freeze({
    x: Number.isFinite(viewport.x) ? viewport.x : 0,
    y: Number.isFinite(viewport.y) ? viewport.y : 0,
    zoom: clampContextCanvasZoom(viewport.zoom),
  });
}

export function contextCanvasWorldToScreen(
  world: ContextCanvasPosition,
  viewport: ContextCanvasViewport,
): ContextCanvasPosition {
  const safe = sanitizeContextCanvasViewport(viewport);
  return Object.freeze({
    x: world.x * safe.zoom + safe.x,
    y: world.y * safe.zoom + safe.y,
  });
}

export function contextCanvasScreenToWorld(
  screen: ContextCanvasPosition,
  viewport: ContextCanvasViewport,
): ContextCanvasPosition {
  const safe = sanitizeContextCanvasViewport(viewport);
  return Object.freeze({
    x: (screen.x - safe.x) / safe.zoom,
    y: (screen.y - safe.y) / safe.zoom,
  });
}

export function zoomContextCanvasAtPoint(
  viewport: ContextCanvasViewport,
  screenPoint: ContextCanvasPosition,
  requestedZoom: number,
): ContextCanvasViewport {
  const safe = sanitizeContextCanvasViewport(viewport);
  const zoom = clampContextCanvasZoom(requestedZoom);
  const worldPoint = contextCanvasScreenToWorld(screenPoint, safe);
  return Object.freeze({
    x: screenPoint.x - worldPoint.x * zoom,
    y: screenPoint.y - worldPoint.y * zoom,
    zoom,
  });
}

export function panContextCanvasFromPointer(
  originViewport: ContextCanvasViewport,
  startClient: ContextCanvasPosition,
  currentClient: ContextCanvasPosition,
): ContextCanvasViewport {
  const safe = sanitizeContextCanvasViewport(originViewport);
  const deltaX = Number.isFinite(currentClient.x - startClient.x)
    ? currentClient.x - startClient.x
    : 0;
  const deltaY = Number.isFinite(currentClient.y - startClient.y)
    ? currentClient.y - startClient.y
    : 0;
  return Object.freeze({ x: safe.x + deltaX, y: safe.y + deltaY, zoom: safe.zoom });
}
