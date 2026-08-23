import type { PublicSpacetimeGeometryReference } from "../governed/types";
import {
  deriveRegionAnchor,
  indexGovernedGeometry,
  loadGovernedGeometry,
} from "./geometry";
import {
  DEFAULT_SPACETIME_PATH_DIGITS,
  DEFAULT_SPACETIME_PROJECTION_PRECISION,
  deriveGeoPath,
  fitProjection,
} from "./projection";
import type {
  GovernedGeometryCollection,
  GovernedGeometryFeature,
  AggregateLayoutAnchor,
  SpacetimeProjectionKind,
  SpacetimeProjectionViewport,
} from "./types";

const SHA256_PATTERN = /^[0-9a-f]{64}$/u;
const SOURCE_CACHE_LIMIT = 2;
const PROJECTION_CACHE_LIMIT = 4;

export interface SpacetimeGeometrySource {
  readonly sourceKey: string;
  readonly reference: PublicSpacetimeGeometryReference;
  readonly collection: GovernedGeometryCollection;
  readonly byId: ReadonlyMap<string, GovernedGeometryFeature>;
}

export interface SpacetimeProjectionCacheInput {
  readonly projectionId: SpacetimeProjectionKind;
  readonly viewport: SpacetimeProjectionViewport;
  readonly geometryAssetSha256: string;
  readonly projectionPrecision?: number;
}

export interface PreparedSpacetimeProjection {
  readonly cacheKey: string;
  readonly projectionId: SpacetimeProjectionKind;
  readonly viewport: SpacetimeProjectionViewport;
  readonly geometryAssetSha256: string;
  readonly projectionPrecision: number;
  readonly source: SpacetimeGeometrySource;
  readonly projection: ReturnType<typeof fitProjection>;
  readonly pathById: ReadonlyMap<string, string>;
  readonly projectedAreaById: ReadonlyMap<string, number>;
  readonly anchorByGeometryId: ReadonlyMap<string, AggregateLayoutAnchor>;
  readonly boundsById: ReadonlyMap<
    string,
    readonly [readonly [number, number], readonly [number, number]]
  >;
}

export interface SpacetimeGeometryColdTiming {
  readonly fetchMs: number;
  readonly hashVerificationMs: number;
  readonly decodeMs: number;
  readonly validationMs: number;
  readonly indexMs: number;
  readonly totalMs: number;
}

export interface SpacetimeProjectionMissTiming {
  readonly projectionFitMs: number;
  readonly pathGenerationMs: number;
  readonly totalMs: number;
}

export interface SpacetimeGeometryRuntimeDiagnostics {
  readonly sourceCacheEntries: number;
  readonly projectionCacheEntries: number;
  readonly sourceCacheHits: number;
  readonly sourceCacheMisses: number;
  readonly sourceLoadFailures: number;
  readonly projectionCacheHits: number;
  readonly projectionCacheMisses: number;
  readonly lastColdGeometryTiming: SpacetimeGeometryColdTiming | null;
  readonly lastProjectionMissTiming: SpacetimeProjectionMissTiming | null;
}

export type SpacetimeGeometryFetcher = (
  input: RequestInfo | URL,
  init?: RequestInit,
) => Promise<Response>;

function roundTiming(value: number): number {
  return Number(value.toFixed(3));
}

function deepFreezeGeometry(value: unknown): void {
  if (!value || typeof value !== "object" || Object.isFrozen(value)) return;
  for (const child of Object.values(value)) deepFreezeGeometry(child);
  Object.freeze(value);
}

function assertGeometryReference(reference: PublicSpacetimeGeometryReference): void {
  if (!reference.geometryArtifactId.trim()) throw new Error("geometry artifact ID is required");
  if (!reference.assetPath.startsWith("/")) throw new Error("geometry asset path must be absolute");
  if (!SHA256_PATTERN.test(reference.assetSha256)) throw new Error("geometry asset SHA-256 is invalid");
  if (!Number.isSafeInteger(reference.featureCount) || reference.featureCount <= 0) {
    throw new Error("geometry feature count must be a positive safe integer");
  }
}

function assertProjectionInput(input: SpacetimeProjectionCacheInput): number {
  if (!SHA256_PATTERN.test(input.geometryAssetSha256)) {
    throw new Error("projection cache geometry SHA-256 is invalid");
  }
  const precision = input.projectionPrecision ?? DEFAULT_SPACETIME_PROJECTION_PRECISION;
  if (!Number.isFinite(precision) || precision <= 0) {
    throw new Error("projection cache precision must be positive");
  }
  for (const [label, value] of [
    ["width", input.viewport.width],
    ["height", input.viewport.height],
    ["padding", input.viewport.padding],
  ] as const) {
    if (!Number.isFinite(value) || (label === "padding" ? value < 0 : value <= 0)) {
      throw new Error(`projection cache ${label} is invalid`);
    }
  }
  return precision;
}

export function buildSpacetimeGeometrySourceKey(
  reference: PublicSpacetimeGeometryReference,
): string {
  assertGeometryReference(reference);
  return JSON.stringify([
    reference.geometryArtifactId,
    reference.assetSha256,
    reference.assetPath,
    reference.featureCount,
  ]);
}

/**
 * The path cache contract intentionally has exactly these six dimensions.
 * Path digits are fixed by DEFAULT_SPACETIME_PATH_DIGITS and are not mutable
 * runtime state.
 */
export function buildSpacetimeProjectionCacheKey(
  input: SpacetimeProjectionCacheInput,
): string {
  const precision = assertProjectionInput(input);
  return JSON.stringify([
    input.projectionId,
    input.viewport.width,
    input.viewport.height,
    input.viewport.padding,
    input.geometryAssetSha256,
    precision,
  ]);
}

async function sha256Hex(bytes: ArrayBuffer): Promise<string> {
  if (!globalThis.crypto?.subtle) throw new Error("Web Crypto is required to verify governed geometry");
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)]
    .map((value) => value.toString(16).padStart(2, "0"))
    .join("");
}

function refreshBoundedEntry<T>(map: Map<string, T>, key: string, value: T, limit: number): void {
  map.delete(key);
  map.set(key, value);
  while (map.size > limit) {
    const oldest = map.keys().next().value as string | undefined;
    if (oldest === undefined) break;
    map.delete(oldest);
  }
}

/**
 * A DOM-free runtime cache. It retains decoded source geometry independently
 * from projected paths and never keys by object identity.
 */
export class SpacetimeGeometryRuntimeCache {
  private readonly sourcePromises = new Map<string, Promise<SpacetimeGeometrySource>>();
  private readonly projectedByKey = new Map<string, PreparedSpacetimeProjection>();
  private sourceCacheHits = 0;
  private sourceCacheMisses = 0;
  private sourceLoadFailures = 0;
  private projectionCacheHits = 0;
  private projectionCacheMisses = 0;
  private lastColdGeometryTiming: SpacetimeGeometryColdTiming | null = null;
  private lastProjectionMissTiming: SpacetimeProjectionMissTiming | null = null;

  loadSource(
    reference: PublicSpacetimeGeometryReference,
    fetcher: SpacetimeGeometryFetcher = globalThis.fetch,
  ): Promise<SpacetimeGeometrySource> {
    const sourceKey = buildSpacetimeGeometrySourceKey(reference);
    const cached = this.sourcePromises.get(sourceKey);
    if (cached) {
      this.sourceCacheHits += 1;
      refreshBoundedEntry(this.sourcePromises, sourceKey, cached, SOURCE_CACHE_LIMIT);
      return cached;
    }

    this.sourceCacheMisses += 1;
    let pending: Promise<SpacetimeGeometrySource>;
    pending = this.loadSourceCold(reference, sourceKey, fetcher).catch((error: unknown) => {
      this.sourceLoadFailures += 1;
      if (this.sourcePromises.get(sourceKey) === pending) this.sourcePromises.delete(sourceKey);
      throw error;
    });
    refreshBoundedEntry(this.sourcePromises, sourceKey, pending, SOURCE_CACHE_LIMIT);
    return pending;
  }

  private async loadSourceCold(
    reference: PublicSpacetimeGeometryReference,
    sourceKey: string,
    fetcher: SpacetimeGeometryFetcher,
  ): Promise<SpacetimeGeometrySource> {
    const started = performance.now();
    const fetchStarted = performance.now();
    // This shared request deliberately has no consumer AbortSignal: one
    // unmount must not poison the module-level single-flight cache.
    const response = await fetcher(reference.assetPath, { cache: "force-cache" });
    if (!response.ok) throw new Error(`Geometry request failed (${response.status})`);
    const bytes = await response.arrayBuffer();
    const fetchMs = performance.now() - fetchStarted;

    const hashStarted = performance.now();
    if (await sha256Hex(bytes) !== reference.assetSha256) {
      throw new Error("governed geometry SHA-256 does not match its projection reference");
    }
    const hashVerificationMs = performance.now() - hashStarted;

    const decodeStarted = performance.now();
    const decoded = JSON.parse(new TextDecoder().decode(bytes)) as unknown;
    const decodeMs = performance.now() - decodeStarted;

    const validationStarted = performance.now();
    const collection = loadGovernedGeometry(decoded, {
      featureCount: reference.featureCount,
      geometryArtifactId: reference.geometryArtifactId,
    });
    deepFreezeGeometry(collection);
    const validationMs = performance.now() - validationStarted;

    const indexStarted = performance.now();
    const byId = indexGovernedGeometry(collection);
    const indexMs = performance.now() - indexStarted;
    this.lastColdGeometryTiming = Object.freeze({
      fetchMs: roundTiming(fetchMs),
      hashVerificationMs: roundTiming(hashVerificationMs),
      decodeMs: roundTiming(decodeMs),
      validationMs: roundTiming(validationMs),
      indexMs: roundTiming(indexMs),
      totalMs: roundTiming(performance.now() - started),
    });
    return Object.freeze({
      sourceKey,
      reference: Object.freeze({ ...reference }),
      collection,
      byId,
    });
  }

  prepareProjection(
    source: SpacetimeGeometrySource,
    input: Omit<SpacetimeProjectionCacheInput, "geometryAssetSha256">,
  ): PreparedSpacetimeProjection {
    const projectionInput = Object.freeze({
      ...input,
      geometryAssetSha256: source.reference.assetSha256,
    });
    const cacheKey = buildSpacetimeProjectionCacheKey(projectionInput);
    const cached = this.projectedByKey.get(cacheKey);
    if (cached) {
      if (cached.source.sourceKey !== source.sourceKey) {
        throw new Error("projection cache source identity differs for the same geometry SHA");
      }
      this.projectionCacheHits += 1;
      refreshBoundedEntry(this.projectedByKey, cacheKey, cached, PROJECTION_CACHE_LIMIT);
      return cached;
    }

    this.projectionCacheMisses += 1;
    const started = performance.now();
    const projectionStarted = performance.now();
    const precision = projectionInput.projectionPrecision ?? DEFAULT_SPACETIME_PROJECTION_PRECISION;
    const projection = fitProjection(
      projectionInput.projectionId,
      source.collection,
      projectionInput.viewport,
      precision,
    );
    const projectionFitMs = performance.now() - projectionStarted;

    const pathStarted = performance.now();
    const path = deriveGeoPath(projection, DEFAULT_SPACETIME_PATH_DIGITS);
    const pathById = new Map<string, string>();
    const projectedAreaById = new Map<string, number>();
    const anchorByGeometryId = new Map<string, AggregateLayoutAnchor>();
    const boundsById = new Map<
      string,
      readonly [readonly [number, number], readonly [number, number]]
    >();
    for (const feature of source.collection.features) {
      const geometryId = String(feature.id);
      const value = path(feature);
      if (!value) throw new Error(`governed geometry produced an empty path: ${geometryId}`);
      pathById.set(geometryId, value);
    }
    const pathGenerationMs = performance.now() - pathStarted;
    const prepared: PreparedSpacetimeProjection = Object.freeze({
      cacheKey,
      projectionId: projectionInput.projectionId,
      viewport: Object.freeze({ ...projectionInput.viewport }),
      geometryAssetSha256: projectionInput.geometryAssetSha256,
      projectionPrecision: precision,
      source,
      projection,
      pathById,
      projectedAreaById,
      anchorByGeometryId,
      boundsById,
    });
    this.lastProjectionMissTiming = Object.freeze({
      projectionFitMs: roundTiming(projectionFitMs),
      pathGenerationMs: roundTiming(pathGenerationMs),
      totalMs: roundTiming(performance.now() - started),
    });
    refreshBoundedEntry(this.projectedByKey, cacheKey, prepared, PROJECTION_CACHE_LIMIT);
    return prepared;
  }

  /** Test-only stable snapshot; it never initializes a cache entry. */
  diagnosticsForTests(): SpacetimeGeometryRuntimeDiagnostics {
    return Object.freeze({
      sourceCacheEntries: this.sourcePromises.size,
      projectionCacheEntries: this.projectedByKey.size,
      sourceCacheHits: this.sourceCacheHits,
      sourceCacheMisses: this.sourceCacheMisses,
      sourceLoadFailures: this.sourceLoadFailures,
      projectionCacheHits: this.projectionCacheHits,
      projectionCacheMisses: this.projectionCacheMisses,
      lastColdGeometryTiming: this.lastColdGeometryTiming,
      lastProjectionMissTiming: this.lastProjectionMissTiming,
    });
  }

  /** Test-only reset. Call only after pending test loads have settled. */
  resetForTests(): void {
    this.sourcePromises.clear();
    this.projectedByKey.clear();
    this.sourceCacheHits = 0;
    this.sourceCacheMisses = 0;
    this.sourceLoadFailures = 0;
    this.projectionCacheHits = 0;
    this.projectionCacheMisses = 0;
    this.lastColdGeometryTiming = null;
    this.lastProjectionMissTiming = null;
  }
}

export const spacetimeGeometryRuntimeCache = new SpacetimeGeometryRuntimeCache();

/**
 * Lazily fill projection/geometry-only areas, bounds, and aggregate anchors
 * for the exact cached projection. This avoids repeated path work while also
 * avoiding Natural Earth features that no governed public atlas references.
 */
export function ensureSpacetimeProjectionGeometryAnchors(
  prepared: PreparedSpacetimeProjection,
  geometryIds: readonly string[],
): ReadonlyMap<string, AggregateLayoutAnchor> {
  const anchorCache = prepared.anchorByGeometryId as Map<string, AggregateLayoutAnchor>;
  const areaCache = prepared.projectedAreaById as Map<string, number>;
  const boundsCache = prepared.boundsById as Map<
    string,
    readonly [readonly [number, number], readonly [number, number]]
  >;
  const path = deriveGeoPath(prepared.projection, DEFAULT_SPACETIME_PATH_DIGITS);
  for (const geometryId of [...new Set(geometryIds)].sort()) {
    const geometry = prepared.source.byId.get(geometryId);
    if (!geometry) throw new Error(`unknown governed anchor geometry: ${geometryId}`);
    if (!areaCache.has(geometryId)) areaCache.set(geometryId, path.area(geometry));
    if (!boundsCache.has(geometryId)) {
      const bounds = path.bounds(geometry);
      if (bounds.flat().some((number) => !Number.isFinite(number))) {
        throw new Error(`governed geometry produced non-finite bounds: ${geometryId}`);
      }
      boundsCache.set(geometryId, Object.freeze([
        Object.freeze([bounds[0][0], bounds[0][1]]) as readonly [number, number],
        Object.freeze([bounds[1][0], bounds[1][1]]) as readonly [number, number],
      ]));
    }
    if (!anchorCache.has(geometryId)) {
      anchorCache.set(geometryId, deriveRegionAnchor({
        geometry,
        projection: prepared.projection,
        geometryArtifactId: prepared.source.reference.geometryArtifactId,
        geometryVersion: prepared.source.reference.sourceVersion,
      }));
    }
  }
  return prepared.anchorByGeometryId;
}

export function getSpacetimeGeometryRuntimeDiagnosticsForTests(): SpacetimeGeometryRuntimeDiagnostics {
  return spacetimeGeometryRuntimeCache.diagnosticsForTests();
}

export function resetSpacetimeGeometryRuntimeForTests(): void {
  spacetimeGeometryRuntimeCache.resetForTests();
}
