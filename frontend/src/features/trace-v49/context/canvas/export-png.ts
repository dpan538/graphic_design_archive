import type { TraceContextDataset } from "../types";
import { buildContextCanvasConnectionGeometry, contextCanvasConnectionLabel, visibleContextCanvasNodes } from "./connections";
import { getGovernedContextMetadata } from "./model";
import { computeContextCanvasBounds } from "./layout";
import {
  CONTEXT_CANVAS_CONNECTION_LABEL_DISPLAY_UNIT_LIMIT,
  CONTEXT_CANVAS_NODE_ID_DISPLAY_UNIT_LIMIT,
  contextCanvasFullLabel,
  escapeContextCanvasXml,
  fitContextCanvasDisplayLabel,
} from "./display-label";
import {
  CONTEXT_CANVAS_DEFAULT_EXPORT_SCALE,
  CONTEXT_CANVAS_NODE_HEIGHT,
  CONTEXT_CANVAS_NODE_WIDTH,
  type ContextCanvasComposition,
  type ContextCanvasDataMetadata,
  type ContextCanvasDataMode,
  type ContextCanvasExportSnapshot,
} from "./types";

const EXPORT_PADDING = 48;
const EXPORT_FOOTER_HEIGHT = 44;
const MAX_EXPORT_SCALE = 4;
const MAX_EXPORT_DIMENSION = 16_384;
const MAX_EXPORT_PIXEL_AREA = 64_000_000;
const UUID_PATTERN = /\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b/gi;

function publicSafeExportValue(value: string): string {
  return value.replace(UUID_PATTERN, "public-reference-withheld");
}

function connectionStroke(
  connectionKind: "context_representation" | "controlled_assignment" | "curated_membership" | "semantic_edge",
): string {
  if (connectionKind === "context_representation") return "#53606b";
  if (connectionKind === "controlled_assignment") return "#53606b";
  if (connectionKind === "curated_membership") return "#6c6254";
  return "#4f5969";
}

export function prepareContextCanvasExportSvg(
  dataset: TraceContextDataset,
  composition: ContextCanvasComposition,
  includeMetadataFooter = true,
  dataMode: ContextCanvasDataMode = "synthetic_contract",
  metadata?: ContextCanvasDataMetadata,
): ContextCanvasExportSnapshot {
  if (!metadata && dataMode !== "synthetic_contract") {
    throw new Error(`${dataMode} Context Canvas export requires metadata.`);
  }
  const effectiveMetadata = metadata ?? {
    dataLabel: "synthetic contract fixture",
    mappingVersion: "synthetic-context-contract-v1",
    candidateState: "synthetic_contract" as const,
    historicalEvidence: false as const,
    governedPublicRelease: false,
    publicReleaseData: false,
    publicObjectCohortCount: dataset.counts.denominator,
  };
  const governed = getGovernedContextMetadata(dataMode, effectiveMetadata);
  const nodes = visibleContextCanvasNodes(dataset, composition, dataMode, effectiveMetadata);
  const connections = buildContextCanvasConnectionGeometry(
    dataset,
    composition,
    dataMode,
    effectiveMetadata,
  );
  const contentBounds = computeContextCanvasBounds(
    composition.visibleEntityIds,
    composition.positions,
  );
  const footerText = governed
    ? `Context Canvas · ${publicSafeExportValue(dataset.selectedRecord.stableId)} · research release ${publicSafeExportValue(dataset.release.releaseId)} · Context projection ${publicSafeExportValue(governed.projectionId)} · ${governed.projectionSha256}`
    : `Context Canvas · ${publicSafeExportValue(dataset.selectedRecord.stableId)} · ${publicSafeExportValue(dataset.release.releaseId)}`;
  const contentWidth = contentBounds.empty ? 480 : contentBounds.width + EXPORT_PADDING * 2;
  const footerWidth = includeMetadataFooter
    ? Array.from(footerText).length * 8 + EXPORT_PADDING * 2
    : 0;
  const naturalWidth = Math.max(contentWidth, footerWidth);
  const naturalHeight = contentBounds.empty ? 240 : contentBounds.height + EXPORT_PADDING * 2;
  const width = Math.ceil(naturalWidth);
  const height = Math.ceil(naturalHeight + (includeMetadataFooter ? EXPORT_FOOTER_HEIGHT : 0));
  const offsetX = contentBounds.empty ? EXPORT_PADDING : EXPORT_PADDING - contentBounds.x;
  const offsetY = contentBounds.empty ? EXPORT_PADDING : EXPORT_PADDING - contentBounds.y;
  if (
    !Number.isSafeInteger(width)
    || !Number.isSafeInteger(height)
    || !Number.isFinite(offsetX)
    || !Number.isFinite(offsetY)
    || width <= 0
    || height <= 0
  ) throw new Error("The canvas composition cannot be prepared for a safe export.");

  const connectionMarkup = connections.map((item) => {
    const stroke = connectionStroke(item.connection.connectionKind);
    const fullLabel = publicSafeExportValue(contextCanvasConnectionLabel(item.connection));
    const displayLabel = fitContextCanvasDisplayLabel(
      fullLabel,
      CONTEXT_CANVAS_CONNECTION_LABEL_DISPLAY_UNIT_LIMIT,
    ).displayText;
    return [
      `<g data-connection-kind="${item.connection.connectionKind}">`,
      `<title>${escapeContextCanvasXml(publicSafeExportValue(item.accessibleLabel))}</title>`,
      `<path d="${item.path}" fill="none" stroke="${stroke}" stroke-width="2"${item.connection.connectionKind === "context_representation" ? "" : ' marker-end="url(#context-arrow)"'}/>`,
      `<text x="${item.labelX}" y="${item.labelY}" fill="#333b43" font-family="ui-monospace, monospace" font-size="12">${escapeContextCanvasXml(displayLabel)}</text>`,
      "</g>",
    ].join("");
  }).join("");

  const nodeMarkup = nodes.map((node) => {
    const fullLabel = publicSafeExportValue(contextCanvasFullLabel(node.ref));
    const displayLabel = fitContextCanvasDisplayLabel(fullLabel).displayText;
    const displayId = fitContextCanvasDisplayLabel(
      publicSafeExportValue(node.ref.stableId),
      CONTEXT_CANVAS_NODE_ID_DISPLAY_UNIT_LIMIT,
    ).displayText;
    const publicKind = node.representation?.explanation.publicName || node.ref.kind;
    const fullTitle = node.representation
      ? `${fullLabel} (${publicKind}). ${publicSafeExportValue(node.representation.explanation.accessibilityWording)}`
      : `${fullLabel} (${node.ref.kind})`;
    return [
      `<g transform="translate(${node.position.x} ${node.position.y})" data-entity-kind="${escapeContextCanvasXml(node.ref.kind)}">`,
      `<title>${escapeContextCanvasXml(fullTitle)}</title>`,
      `<rect width="${CONTEXT_CANVAS_NODE_WIDTH}" height="${CONTEXT_CANVAS_NODE_HEIGHT}" rx="8" fill="#ffffff" stroke="#27313a" stroke-width="2"/>`,
      `<text x="16" y="29" fill="#172028" font-family="ui-sans-serif, sans-serif" font-size="16" font-weight="600">${escapeContextCanvasXml(displayLabel)}</text>`,
      `<text x="16" y="55" fill="#56616a" font-family="ui-monospace, monospace" font-size="11">${escapeContextCanvasXml(publicKind)}</text>`,
      `<text x="16" y="79" fill="#56616a" font-family="ui-monospace, monospace" font-size="10">${escapeContextCanvasXml(displayId)}</text>`,
      "</g>",
    ].join("");
  }).join("");

  const footer = includeMetadataFooter
    ? `<text x="${EXPORT_PADDING}" y="${height - 16}" fill="#4e5962" font-family="ui-monospace, monospace" font-size="11">${escapeContextCanvasXml(footerText)}</text>`
    : "";
  const emptyMessage = contentBounds.empty
    ? `<text x="${EXPORT_PADDING}" y="${EXPORT_PADDING + 24}" fill="#4e5962" font-family="ui-sans-serif, sans-serif" font-size="16">No visible canvas entities</text>`
    : "";

  const svg = [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`,
    `<title>Context Canvas for ${escapeContextCanvasXml(publicSafeExportValue(dataset.selectedRecord.stableId))}</title>`,
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
  const redactedId = publicSafeExportValue(selectedPublicRecordId.trim());
  const rawId = redactedId.includes("public-reference-withheld") ? "public-record" : redactedId;
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
  signal?: AbortSignal,
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
    signal?.throwIfAborted();
    const image = new Image();
    const loaded = new Promise<void>((resolve, reject) => {
      const abort = () => {
        image.onload = null;
        image.onerror = null;
        reject(new DOMException("PNG export was cancelled.", "AbortError"));
      };
      image.onload = () => {
        signal?.removeEventListener("abort", abort);
        resolve();
      };
      image.onerror = () => {
        signal?.removeEventListener("abort", abort);
        reject(new Error("The export-only SVG could not be rendered."));
      };
      signal?.addEventListener("abort", abort, { once: true });
    });
    image.src = svgUrl;
    await loaded;
    signal?.throwIfAborted();

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
    signal?.throwIfAborted();
    const pngUrl = URL.createObjectURL(blob);
    try {
      const link = document.createElement("a");
      link.href = pngUrl;
      link.download = filename;
      link.rel = "noopener";
      signal?.throwIfAborted();
      link.click();
    } finally {
      URL.revokeObjectURL(pngUrl);
    }
  } finally {
    URL.revokeObjectURL(svgUrl);
  }
}
