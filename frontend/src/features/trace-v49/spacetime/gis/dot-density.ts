import { geoContains, geoPath, type GeoContext, type GeoProjection } from "d3-geo";
import type {
  AggregateDensityDot,
  AggregateDotFallback,
  AggregateDotField,
  AggregateDotFieldPolicy,
  AggregateLayoutAnchor,
  GovernedGeometryFeature,
} from "./types";

export const DEFAULT_AGGREGATE_DOT_FIELD_POLICY: AggregateDotFieldPolicy = Object.freeze({
  policyVersion: "trace-dot-density-grid-v1",
  dotUnit: 1,
  preferredSpacingPx: 5,
  minimumSpacingPx: 2.5,
  maxDots: 2_000,
  maxCandidateTests: 250_000,
  tinyGeometryPolicy: "aggregate_anchor",
  multipartPolicy: "whole_geometry_candidate_pool",
});

export interface AggregateDotSeedInput {
  readonly releaseId: string;
  readonly geometryId: string;
  readonly timeBucketId: string;
  readonly recordCount: number;
  readonly policyVersion: AggregateDotFieldPolicy["policyVersion"];
}

export interface AggregateDotFieldInput {
  readonly geometry: GovernedGeometryFeature;
  readonly projection: GeoProjection;
  readonly recordCount: number;
  readonly seed: string;
  readonly policy?: AggregateDotFieldPolicy;
  readonly fallbackAnchor?: AggregateLayoutAnchor;
  readonly preparedGeometry?: PreparedAggregateDotGeometry;
}

interface CandidatePoint {
  readonly x: number;
  readonly y: number;
  readonly score: number;
  readonly row: number;
  readonly column: number;
}

export interface ProjectedAggregateDotRing {
  readonly points: readonly (readonly [number, number])[];
  readonly minimumX: number;
  readonly minimumY: number;
  readonly maximumX: number;
  readonly maximumY: number;
}

export interface PreparedAggregateDotGeometry {
  readonly semanticKind: "aggregate_dot_geometry_preparation";
  readonly derivationVersion: "trace-projected-dot-surface-v1";
  readonly geometryId: string;
  readonly projectionKey: string;
  readonly rings: readonly ProjectedAggregateDotRing[];
  readonly bounds: readonly [readonly [number, number], readonly [number, number]];
}

class ProjectedRingContext implements GeoContext {
  readonly rings: Array<Array<readonly [number, number]>> = [];
  private currentRing: Array<readonly [number, number]> | null = null;

  beginPath(): void {
    this.rings.length = 0;
    this.currentRing = null;
  }

  moveTo(x: number, y: number): void {
    this.currentRing = [[x, y]];
    this.rings.push(this.currentRing);
  }

  lineTo(x: number, y: number): void {
    this.currentRing?.push([x, y]);
  }

  closePath(): void {
    this.currentRing = null;
  }

  arc(): void {
    throw new Error("aggregate dot polygons must not contain point arcs");
  }
}

function fnv1a32(value: string): number {
  let hash = 0x811c9dc5;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return hash >>> 0;
}

function unitInterval(seed: string): number {
  return fnv1a32(seed) / 0x1_0000_0000;
}

export function prepareAggregateDotGeometry(
  geometry: GovernedGeometryFeature,
  projection: GeoProjection,
  projectionKey: string,
): PreparedAggregateDotGeometry {
  if (!projectionKey.trim()) throw new Error("aggregate dot geometry preparation requires a projection key");
  const context = new ProjectedRingContext();
  context.beginPath();
  geoPath(projection, context)(geometry);
  const rings: ProjectedAggregateDotRing[] = context.rings
    .filter((points) => points.length >= 3)
    .map((points) => {
      const xValues = points.map((point) => point[0]);
      const yValues = points.map((point) => point[1]);
      return Object.freeze({
        points: Object.freeze(points),
        minimumX: Math.min(...xValues),
        minimumY: Math.min(...yValues),
        maximumX: Math.max(...xValues),
        maximumY: Math.max(...yValues),
      });
    });
  if (rings.length === 0) {
    const emptyBounds = Object.freeze([
      Object.freeze([0, 0]) as readonly [number, number],
      Object.freeze([0, 0]) as readonly [number, number],
    ]) as readonly [readonly [number, number], readonly [number, number]];
    return Object.freeze({
      semanticKind: "aggregate_dot_geometry_preparation",
      derivationVersion: "trace-projected-dot-surface-v1",
      geometryId: geometry.id,
      projectionKey,
      rings: Object.freeze([]),
      bounds: emptyBounds,
    });
  }
  const bounds = Object.freeze([
    Object.freeze([Math.min(...rings.map((ring) => ring.minimumX)), Math.min(...rings.map((ring) => ring.minimumY))]),
    Object.freeze([Math.max(...rings.map((ring) => ring.maximumX)), Math.max(...rings.map((ring) => ring.maximumY))]),
  ]) as readonly [readonly [number, number], readonly [number, number]];
  return Object.freeze({
    semanticKind: "aggregate_dot_geometry_preparation",
    derivationVersion: "trace-projected-dot-surface-v1",
    geometryId: geometry.id,
    projectionKey,
    rings: Object.freeze(rings),
    bounds,
  });
}

function ringContains(ring: ProjectedAggregateDotRing, x: number, y: number): boolean {
  if (x < ring.minimumX || x > ring.maximumX || y < ring.minimumY || y > ring.maximumY) return false;
  let inside = false;
  for (let current = 0, previous = ring.points.length - 1; current < ring.points.length; previous = current, current += 1) {
    const [currentX, currentY] = ring.points[current];
    const [previousX, previousY] = ring.points[previous];
    if (
      (currentY > y) !== (previousY > y) &&
      x < ((previousX - currentX) * (y - currentY)) / (previousY - currentY) + currentX
    ) {
      inside = !inside;
    }
  }
  return inside;
}

function surfaceContains(surface: PreparedAggregateDotGeometry, x: number, y: number): boolean {
  let containingRingCount = 0;
  for (const ring of surface.rings) {
    if (ringContains(ring, x, y)) containingRingCount += 1;
  }
  return containingRingCount % 2 === 1;
}

function validatePolicy(policy: AggregateDotFieldPolicy): void {
  for (const [label, value] of [
    ["dotUnit", policy.dotUnit],
    ["preferredSpacingPx", policy.preferredSpacingPx],
    ["minimumSpacingPx", policy.minimumSpacingPx],
    ["maxDots", policy.maxDots],
    ["maxCandidateTests", policy.maxCandidateTests],
  ] as const) {
    if (!Number.isFinite(value) || value <= 0) throw new Error(`aggregate dot ${label} must be positive`);
  }
  if (!Number.isSafeInteger(policy.dotUnit) || !Number.isSafeInteger(policy.maxDots) || !Number.isSafeInteger(policy.maxCandidateTests)) {
    throw new Error("aggregate dot counts must be safe integers");
  }
  if (policy.minimumSpacingPx > policy.preferredSpacingPx) {
    throw new Error("aggregate dot minimum spacing exceeds preferred spacing");
  }
}

export function buildAggregateDotSeed(input: AggregateDotSeedInput): string {
  if (!input.releaseId || !input.geometryId || !input.timeBucketId) {
    throw new Error("aggregate dot seed requires release, geometry, and time bucket IDs");
  }
  if (!Number.isSafeInteger(input.recordCount) || input.recordCount < 0) {
    throw new Error("aggregate dot seed record count must be a non-negative safe integer");
  }
  return [
    input.policyVersion,
    input.releaseId,
    input.timeBucketId,
    input.geometryId,
    String(input.recordCount),
  ].join(":");
}

function candidateSpacingSequence(policy: AggregateDotFieldPolicy): readonly number[] {
  const sequence: number[] = [];
  let spacing = policy.preferredSpacingPx;
  while (spacing > policy.minimumSpacingPx) {
    sequence.push(spacing);
    spacing = Math.max(policy.minimumSpacingPx, spacing * 0.8);
    if (sequence.some((existing) => Math.abs(existing - spacing) < 1e-9)) break;
  }
  if (!sequence.some((existing) => Math.abs(existing - policy.minimumSpacingPx) < 1e-9)) {
    sequence.push(policy.minimumSpacingPx);
  }
  return Object.freeze(sequence);
}

function generateCandidates(
  surface: PreparedAggregateDotGeometry,
  seed: string,
  spacing: number,
  maxCandidateTests: number,
): readonly CandidatePoint[] {
  const bounds = surface.bounds;
  if (bounds.flat().some((value) => !Number.isFinite(value))) return Object.freeze([]);
  const width = bounds[1][0] - bounds[0][0];
  const height = bounds[1][1] - bounds[0][1];
  if (width <= 0 || height <= 0) return Object.freeze([]);

  const estimatedTests = Math.ceil(width / spacing) * Math.ceil(height / spacing);
  const safeSpacing =
    estimatedTests > maxCandidateTests
      ? Math.max(spacing, Math.sqrt((width * height) / maxCandidateTests))
      : spacing;
  const phaseX = unitInterval(`${seed}:phase-x`) * safeSpacing;
  const phaseY = unitInterval(`${seed}:phase-y`) * safeSpacing;
  const startX = bounds[0][0] + phaseX;
  const startY = bounds[0][1] + phaseY;
  const candidates: CandidatePoint[] = [];
  let tests = 0;

  for (let row = 0, y = startY; y <= bounds[1][1] && tests < maxCandidateTests; row += 1, y += safeSpacing) {
    for (let column = 0, x = startX; x <= bounds[1][0] && tests < maxCandidateTests; column += 1, x += safeSpacing) {
      tests += 1;
      if (!surfaceContains(surface, x, y)) continue;
      candidates.push({
        x,
        y,
        score: fnv1a32(`${seed}:${safeSpacing.toFixed(6)}:${row}:${column}`),
        row,
        column,
      });
    }
  }
  candidates.sort(
    (left, right) =>
      left.score - right.score || left.row - right.row || left.column - right.column || left.y - right.y || left.x - right.x,
  );
  return Object.freeze(candidates);
}

function selectCandidates(input: AggregateDotFieldInput, policy: AggregateDotFieldPolicy, target: number): readonly CandidatePoint[] {
  const surface =
    input.preparedGeometry ?? prepareAggregateDotGeometry(input.geometry, input.projection, "unregistered-projection");
  if (surface.geometryId !== input.geometry.id) throw new Error("aggregate dot prepared geometry ID mismatch");
  let best: readonly CandidatePoint[] = Object.freeze([]);
  for (const spacing of candidateSpacingSequence(policy)) {
    // Coordinates are serialized to three decimals below. Revalidate that
    // exact serialized position so rounding cannot move a boundary candidate
    // outside its governed projected surface.
    const candidates = generateCandidates(surface, input.seed, spacing, policy.maxCandidateTests)
      .filter((candidate) => {
        const serializedX = Number(candidate.x.toFixed(3));
        const serializedY = Number(candidate.y.toFixed(3));
        if (!surfaceContains(surface, serializedX, serializedY)) return false;
        const geographic = input.projection.invert?.([serializedX, serializedY]);
        return Boolean(geographic && geoContains(input.geometry, geographic));
      });
    best = candidates;
    if (candidates.length >= target) break;
  }
  return Object.freeze(best.slice(0, target));
}

function buildFallback(
  input: AggregateDotFieldInput,
  representedRecordCount: number,
  reason: AggregateDotFallback["reason"],
): AggregateDotFallback {
  if (!input.fallbackAnchor) {
    throw new Error(`aggregate dot fallback anchor required for ${input.geometry.id}: ${reason}`);
  }
  if (input.fallbackAnchor.geometryId !== input.geometry.id) {
    throw new Error("aggregate dot fallback anchor geometry mismatch");
  }
  return Object.freeze({
    semanticKind: "aggregate_anchor_mark",
    anchor: input.fallbackAnchor,
    representedRecordCount,
    reason,
    positionClaim: "aggregate_only",
  });
}

export function generateAggregateDotField(input: AggregateDotFieldInput): AggregateDotField {
  if (!Number.isSafeInteger(input.recordCount) || input.recordCount < 0) {
    throw new Error("aggregate dot field record count must be a non-negative safe integer");
  }
  if (!input.seed) throw new Error("aggregate dot field requires a deterministic seed");
  const policy = input.policy ?? DEFAULT_AGGREGATE_DOT_FIELD_POLICY;
  validatePolicy(policy);
  const requestedDotCount = Math.ceil(input.recordCount / policy.dotUnit);
  const targetDotCount = Math.min(requestedDotCount, policy.maxDots);
  const candidates = selectCandidates(input, policy, targetDotCount);
  const dots: AggregateDensityDot[] = candidates.map((candidate, index) => {
    const recordsBeforeDot = index * policy.dotUnit;
    return Object.freeze({
      id: `${input.geometry.id}:aggregate-density:${index + 1}`,
      semanticKind: "aggregate_density_mark",
      x: Number(candidate.x.toFixed(3)),
      y: Number(candidate.y.toFixed(3)),
      representedRecordCount: Math.min(policy.dotUnit, input.recordCount - recordsBeforeDot),
      positionClaim: "aggregate_only",
    });
  });
  const dotRepresentedRecordCount = dots.reduce((sum, dot) => sum + dot.representedRecordCount, 0);
  const remainingRecordCount = input.recordCount - dotRepresentedRecordCount;
  let fallback: AggregateDotFallback | null = null;
  if (remainingRecordCount > 0) {
    const reason: AggregateDotFallback["reason"] =
      requestedDotCount > policy.maxDots
        ? "dot_budget"
        : dots.length === 0
          ? "tiny_geometry"
          : "candidate_capacity";
    fallback = buildFallback(input, remainingRecordCount, reason);
  }

  return Object.freeze({
    semanticKind: "aggregate_density_field",
    policyVersion: policy.policyVersion,
    geometryId: input.geometry.id,
    seed: input.seed,
    recordCount: input.recordCount,
    dotUnit: policy.dotUnit,
    requestedDotCount,
    generatedDotCount: dots.length,
    representedRecordCount: dotRepresentedRecordCount + (fallback?.representedRecordCount ?? 0),
    dots: Object.freeze(dots),
    fallback,
    positionClaim: "aggregate_only",
  });
}
