import type {
  NativePatternDefinition,
  NativePatternFamily,
  NativePatternVariable,
} from "./types";

export interface NativePatternInput {
  readonly namespace: string;
  readonly family: NativePatternFamily;
  readonly encodedVariable: NativePatternVariable;
  readonly legendValue: string;
  readonly spacingPx: number;
  readonly weightPx: number;
}

export interface NativeCountTier {
  readonly minimumInclusive: number;
  readonly maximumInclusive: number | null;
  readonly legendValue: string;
  readonly spacingPx: number;
  readonly weightPx: number;
}

export const TRACE_NATIVE_COUNT_TIER_POLICY_VERSION = "trace-native-count-tier-v1";

export const TRACE_NATIVE_COUNT_TIERS: readonly NativeCountTier[] = Object.freeze([
  Object.freeze({
    minimumInclusive: 1,
    maximumInclusive: 4,
    legendValue: "1–4 records",
    spacingPx: 12,
    weightPx: 1,
  }),
  Object.freeze({
    minimumInclusive: 5,
    maximumInclusive: 24,
    legendValue: "5–24 records",
    spacingPx: 9,
    weightPx: 1.1,
  }),
  Object.freeze({
    minimumInclusive: 25,
    maximumInclusive: 99,
    legendValue: "25–99 records",
    spacingPx: 7,
    weightPx: 1.2,
  }),
  Object.freeze({
    minimumInclusive: 100,
    maximumInclusive: null,
    legendValue: "100 or more records",
    spacingPx: 5,
    weightPx: 1.2,
  }),
]);

export function deriveNativeCountTier(recordCount: number): NativeCountTier {
  if (!Number.isSafeInteger(recordCount) || recordCount < 1) {
    throw new Error("native count tier requires a positive safe-integer record count");
  }
  const tier = TRACE_NATIVE_COUNT_TIERS.find((candidate) =>
    recordCount >= candidate.minimumInclusive
    && (candidate.maximumInclusive === null || recordCount <= candidate.maximumInclusive));
  if (!tier) throw new Error("native count tier policy has no matching tier");
  return tier;
}

function fnv1a32(value: string): string {
  let hash = 0x811c9dc5;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

function formatNumber(value: number): string {
  return Number(value.toFixed(3)).toString();
}

function escapeXmlAttribute(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

export function deriveNativePatternDefinition(input: NativePatternInput): NativePatternDefinition {
  if (!input.namespace.trim() || !input.legendValue.trim()) {
    throw new Error("native pattern requires namespace and legend value");
  }
  if (!Number.isFinite(input.spacingPx) || input.spacingPx < 2 || input.spacingPx > 64) {
    throw new Error("native pattern spacing must be within [2, 64] pixels");
  }
  if (!Number.isFinite(input.weightPx) || input.weightPx <= 0 || input.weightPx > input.spacingPx / 2) {
    throw new Error("native pattern weight must be positive and no greater than half the spacing");
  }
  const identity = [
    "trace-native-pattern-v1",
    input.namespace,
    input.family,
    input.encodedVariable,
    input.legendValue,
    formatNumber(input.spacingPx),
    formatNumber(input.weightPx),
  ].join(":");
  const id = `trace-pattern-${fnv1a32(identity)}`;
  const midpoint = input.spacingPx / 2;
  const primitive: NativePatternDefinition["primitive"] =
    input.family === "dots"
      ? Object.freeze({ kind: "circle", cx: midpoint, cy: midpoint, radius: input.weightPx })
      : input.family === "horizontal_lines"
        ? Object.freeze({
            kind: "line",
            x1: 0,
            y1: midpoint,
            x2: input.spacingPx,
            y2: midpoint,
            strokeWidth: input.weightPx,
          })
        : Object.freeze({
            kind: "line",
            x1: 0,
            y1: input.spacingPx,
            x2: input.spacingPx,
            y2: 0,
            strokeWidth: input.weightPx,
          });

  return Object.freeze({
    id,
    family: input.family,
    encodedVariable: input.encodedVariable,
    legendValue: input.legendValue,
    width: input.spacingPx,
    height: input.spacingPx,
    primitive,
    deterministic: true,
  });
}

export function deriveNativePatternFillUrl(definition: NativePatternDefinition): string {
  return `url(#${definition.id})`;
}

export function serializeNativePatternDefinition(
  definition: NativePatternDefinition,
  foreground = "currentColor",
): string {
  const common = `id="${escapeXmlAttribute(definition.id)}" patternUnits="userSpaceOnUse" width="${formatNumber(definition.width)}" height="${formatNumber(definition.height)}" data-encoded-variable="${escapeXmlAttribute(definition.encodedVariable)}" data-legend-value="${escapeXmlAttribute(definition.legendValue)}"`;
  const primitive =
    definition.primitive.kind === "circle"
      ? `<circle cx="${formatNumber(definition.primitive.cx)}" cy="${formatNumber(definition.primitive.cy)}" r="${formatNumber(definition.primitive.radius)}" fill="${escapeXmlAttribute(foreground)}"/>`
      : `<line x1="${formatNumber(definition.primitive.x1)}" y1="${formatNumber(definition.primitive.y1)}" x2="${formatNumber(definition.primitive.x2)}" y2="${formatNumber(definition.primitive.y2)}" stroke="${escapeXmlAttribute(foreground)}" stroke-width="${formatNumber(definition.primitive.strokeWidth)}"/>`;
  return `<pattern ${common}>${primitive}</pattern>`;
}
