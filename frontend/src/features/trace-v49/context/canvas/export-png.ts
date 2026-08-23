import type { TraceContextDataset } from "../types";
import { buildContextCanvasConnectionGeometry, contextCanvasConnectionLabel, visibleContextCanvasNodes } from "./connections";
import { computeContextCanvasBounds } from "./layout";
import {
  CONTEXT_CANVAS_DEFAULT_EXPORT_SCALE,
  CONTEXT_CANVAS_NODE_HEIGHT,
  CONTEXT_CANVAS_NODE_WIDTH,
  type ContextCanvasComposition,
  type ContextCanvasExportSnapshot,
} from "./types";

const EXPORT_PADDING = 48;
const EXPORT_FOOTER_HEIGHT = 44;
const MAX_EXPORT_SCALE = 4;
const MAX_EXPORT_DIMENSION = 16_384;
const MAX_EXPORT_PIXEL_AREA = 64_000_000;
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function publicSafeExportValue(value: string): string {
  return UUID_PATTERN.test(value.trim()) ? "public-reference-withheld" : value;
}

function escapeXml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

function connectionStroke(connectionKind: "controlled_assignment" | "curated_membership" | "semantic_edge"): string {
  if (connectionKind === "controlled_assignment") return "#53606b";
  if (connectionKind === "curated_membership") return "#6c6254";
  return "#4f5969";
}

export function prepareContextCanvasExportSvg(
  dataset: TraceContextDataset,
  composition: ContextCanvasComposition,
  includeMetadataFooter = true,
): ContextCanvasExportSnapshot {
  const nodes = visibleContextCanvasNodes(dataset, composition);
  const connections = buildContextCanvasConnectionGeometry(dataset, composition);
  const contentBounds = computeContextCanvasBounds(
    composition.visibleEntityIds,
    composition.positions,
  );
  const naturalWidth = contentBounds.empty ? 480 : contentBounds.width + EXPORT_PADDING * 2;
  const naturalHeight = contentBounds.empty ? 240 : contentBounds.height + EXPORT_PADDING * 2;
  const width = Math.ceil(naturalWidth);
  const height = Math.ceil(naturalHeight + (includeMetadataFooter ? EXPORT_FOOTER_HEIGHT : 0));
  const offsetX = contentBounds.empty ? EXPORT_PADDING : EXPORT_PADDING - contentBounds.x;
  const offsetY = contentBounds.empty ? EXPORT_PADDING : EXPORT_PADDING - contentBounds.y;

  const connectionMarkup = connections.map((item) => {
    const stroke = connectionStroke(item.connection.connectionKind);
    return [
      `<g data-connection-kind="${item.connection.connectionKind}">`,
      `<path d="${item.path}" fill="none" stroke="${stroke}" stroke-width="2" marker-end="url(#context-arrow)"/>`,
      `<text x="${item.labelX}" y="${item.labelY}" fill="#333b43" font-family="ui-monospace, monospace" font-size="12">${escapeXml(publicSafeExportValue(contextCanvasConnectionLabel(item.connection)))}</text>`,
      "</g>",
    ].join("");
  }).join("");

  const nodeMarkup = nodes.map((node) => {
    const displayLabel = publicSafeExportValue(node.ref.label?.trim() || node.ref.stableId);
    return [
      `<g transform="translate(${node.position.x} ${node.position.y})" data-entity-kind="${escapeXml(node.ref.kind)}">`,
      `<rect width="${CONTEXT_CANVAS_NODE_WIDTH}" height="${CONTEXT_CANVAS_NODE_HEIGHT}" rx="8" fill="#ffffff" stroke="#27313a" stroke-width="2"/>`,
      `<text x="16" y="29" fill="#172028" font-family="ui-sans-serif, sans-serif" font-size="16" font-weight="600">${escapeXml(displayLabel)}</text>`,
      `<text x="16" y="55" fill="#56616a" font-family="ui-monospace, monospace" font-size="11">${escapeXml(node.ref.kind)}</text>`,
      `<text x="16" y="79" fill="#56616a" font-family="ui-monospace, monospace" font-size="10">${escapeXml(publicSafeExportValue(node.ref.stableId))}</text>`,
      "</g>",
    ].join("");
  }).join("");

  const footer = includeMetadataFooter
    ? `<text x="${EXPORT_PADDING}" y="${height - 16}" fill="#4e5962" font-family="ui-monospace, monospace" font-size="11">${escapeXml(`Context Canvas · ${publicSafeExportValue(dataset.selectedRecord.stableId)} · ${publicSafeExportValue(dataset.release.releaseId)}`)}</text>`
    : "";
  const emptyMessage = contentBounds.empty
    ? `<text x="${EXPORT_PADDING}" y="${EXPORT_PADDING + 24}" fill="#4e5962" font-family="ui-sans-serif, sans-serif" font-size="16">No visible canvas entities</text>`
    : "";

  const svg = [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`,
    `<title>Context Canvas for ${escapeXml(publicSafeExportValue(dataset.selectedRecord.stableId))}</title>`,
    '<defs><marker id="context-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 8 4 L 0 8 z" fill="#4f5962"/></marker></defs>',
    `<rect width="${width}" height="${height}" fill="#f5f5f2"/>`,
    `<g transform="translate(${offsetX} ${offsetY})">${connectionMarkup}${nodeMarkup}</g>`,
    emptyMessage,
    footer,
    "</svg>",
  ].join("");

  return Object.freeze({ svg, width, height, contentBounds });
}

export function buildContextCanvasPngFilename(
  selectedPublicRecordId: string,
  instant: Date = new Date(),
): string {
  const rawId = publicSafeExportValue(selectedPublicRecordId.trim()) === "public-reference-withheld"
    ? "public-record"
    : selectedPublicRecordId.trim();
  const safeId = rawId
    .replace(/[^a-z0-9_-]+/gi, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "public-record";
  const safeInstant = Number.isFinite(instant.getTime())
    ? instant.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z")
    : "undated";
  return `context-canvas-${safeId}-${safeInstant}.png`;
}

export async function downloadContextCanvasPng(
  snapshot: ContextCanvasExportSnapshot,
  filename: string,
  scale = CONTEXT_CANVAS_DEFAULT_EXPORT_SCALE,
): Promise<void> {
  if (typeof document === "undefined" || typeof Image === "undefined") {
    throw new Error("PNG export requires browser-native image APIs.");
  }
  const safeScale = Number.isFinite(scale) && scale > 0
    ? Math.min(MAX_EXPORT_SCALE, scale)
    : CONTEXT_CANVAS_DEFAULT_EXPORT_SCALE;
  const pixelWidth = Math.max(1, Math.ceil(snapshot.width * safeScale));
  const pixelHeight = Math.max(1, Math.ceil(snapshot.height * safeScale));
  if (
    !Number.isSafeInteger(pixelWidth)
    || !Number.isSafeInteger(pixelHeight)
    || pixelWidth > MAX_EXPORT_DIMENSION
    || pixelHeight > MAX_EXPORT_DIMENSION
    || pixelWidth * pixelHeight > MAX_EXPORT_PIXEL_AREA
  ) {
    throw new Error("The canvas content is too large for a safe PNG export.");
  }
  const svgUrl = URL.createObjectURL(new Blob([snapshot.svg], { type: "image/svg+xml;charset=utf-8" }));
  try {
    const image = new Image();
    const loaded = new Promise<void>((resolve, reject) => {
      image.onload = () => resolve();
      image.onerror = () => reject(new Error("The export-only SVG could not be rendered."));
    });
    image.src = svgUrl;
    await loaded;

    const canvas = document.createElement("canvas");
    canvas.width = pixelWidth;
    canvas.height = pixelHeight;
    const context = canvas.getContext("2d");
    if (!context) throw new Error("A 2D canvas context is unavailable.");
    context.fillStyle = "#f5f5f2";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.drawImage(image, 0, 0, canvas.width, canvas.height);

    const blob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob((value) => value ? resolve(value) : reject(new Error("PNG encoding failed.")), "image/png");
    });
    const pngUrl = URL.createObjectURL(blob);
    try {
      const link = document.createElement("a");
      link.href = pngUrl;
      link.download = filename;
      link.rel = "noopener";
      link.click();
    } finally {
      URL.revokeObjectURL(pngUrl);
    }
  } finally {
    URL.revokeObjectURL(svgUrl);
  }
}
