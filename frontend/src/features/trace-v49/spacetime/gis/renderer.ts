import type { PublicSpacetimeAtlasDataset } from "../governed/types";
import {
  buildAggregateDotSeed,
  DEFAULT_AGGREGATE_DOT_FIELD_POLICY,
  generateAggregateDotField,
  prepareAggregateDotGeometry,
  type PreparedAggregateDotGeometry,
} from "./dot-density";
import { deriveSpacetimeMapViewModel } from "./marks";
import {
  deriveNativeCountTier,
  deriveNativePatternDefinition,
  TRACE_NATIVE_COUNT_TIER_POLICY_VERSION,
} from "./native-pattern";
import {
  ensureSpacetimeProjectionGeometryAnchors,
  type PreparedSpacetimeProjection,
} from "./runtime-cache";
import type {
  AggregateDensityDot,
  AggregateDotField,
  NativePatternDefinition,
  SpacetimeMapRegionMark,
} from "./types";

const DOT_SURFACE_CACHE_LIMIT = 256;
const DOT_FIELD_CACHE_LIMIT = 1_024;

export type SpacetimeRendererMode = "aggregate" | "density" | "texture";

export interface PreparedSpacetimeDensity {
  readonly strategy: "dot_field" | "multi_geometry_anchor";
  readonly dots: readonly AggregateDensityDot[];
  readonly generatedDotCount: number;
  readonly anchorRemainderCount: number;
  readonly representedRecordCount: number;
  readonly field: AggregateDotField | null;
  readonly positionClaim: "aggregate_only";
}

export interface PreparedSpacetimeRendererMark {
  readonly geography: SpacetimeMapRegionMark;
  readonly x: number;
  readonly y: number;
  readonly density: PreparedSpacetimeDensity | null;
  readonly pattern: NativePatternDefinition | null;
}

export interface SpacetimeRendererSemanticState {
  readonly selectedPeriodId: string;
  readonly selectedGeographyId: string | null;
  readonly denominator: number;
  readonly mappedRecords: number;
  readonly unmappedRecords: number;
  readonly geographyAssignments: number;
  readonly heldExcluded: number;
  readonly mappingRows: readonly Readonly<{
    geographyId: string;
    mappingState: "mapped" | "aggregate_only" | "unmapped";
    recordCount: number;
    denominator: number;
    precisionBreakdown: PublicSpacetimeAtlasDataset["accessibleRows"][number]["precisionBreakdown"];
  }>[];
  readonly realSemanticEdgeCount: 0;
}

export interface SpacetimeRendererModel {
  readonly mode: SpacetimeRendererMode;
  readonly marks: readonly PreparedSpacetimeRendererMark[];
  readonly semanticState: SpacetimeRendererSemanticState;
}

export interface SpacetimeRendererRuntimeDiagnostics {
  readonly dotSurfaceCacheEntries: number;
  readonly dotFieldCacheEntries: number;
  readonly dotSurfaceCacheHits: number;
  readonly dotSurfaceCacheMisses: number;
  readonly dotFieldCacheHits: number;
  readonly dotFieldCacheMisses: number;
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

function buildDotFieldCacheKey(
  atlas: PublicSpacetimeAtlasDataset,
  geography: SpacetimeMapRegionMark,
  projection: PreparedSpacetimeProjection,
): string {
  return JSON.stringify([
    atlas.release.researchReleaseId,
    atlas.release.researchManifestSha256,
    atlas.release.spacetimeProjectionSha256,
    atlas.selectedPeriod.periodId,
    geography.geographyId,
    geography.recordCount,
    projection.geometryAssetSha256,
    projection.cacheKey,
    atlas.dotPolicy.policyVersion,
    geography.anchor.geometryId,
  ]);
}

function deriveSemanticState(
  atlas: PublicSpacetimeAtlasDataset,
  selectedGeographyId: string | null,
): SpacetimeRendererSemanticState {
  const mappingRows = atlas.accessibleRows
    .map((row) => Object.freeze({
      geographyId: row.geographyId,
      mappingState: row.mappingState,
      recordCount: row.recordCount,
      denominator: row.denominator,
      precisionBreakdown: Object.freeze({ ...row.precisionBreakdown }),
    }))
    .sort((left, right) => left.geographyId.localeCompare(right.geographyId));
  return Object.freeze({
    selectedPeriodId: atlas.selectedPeriod.periodId,
    selectedGeographyId,
    denominator: atlas.counts.denominator,
    mappedRecords: atlas.counts.mappedRecords,
    unmappedRecords: atlas.counts.unmappedRecords,
    geographyAssignments: atlas.counts.geographyAssignments,
    heldExcluded: atlas.counts.heldExcluded,
    mappingRows: Object.freeze(mappingRows),
    realSemanticEdgeCount: 0,
  });
}

export class SpacetimeRendererRuntimeCache {
  private readonly dotSurfaceByKey = new Map<string, PreparedAggregateDotGeometry>();
  private readonly dotFieldByKey = new Map<string, PreparedSpacetimeDensity>();
  private dotSurfaceCacheHits = 0;
  private dotSurfaceCacheMisses = 0;
  private dotFieldCacheHits = 0;
  private dotFieldCacheMisses = 0;

  private prepareDotSurface(
    projection: PreparedSpacetimeProjection,
    geometryId: string,
  ): PreparedAggregateDotGeometry {
    const key = JSON.stringify([projection.cacheKey, geometryId]);
    const cached = this.dotSurfaceByKey.get(key);
    if (cached) {
      this.dotSurfaceCacheHits += 1;
      refreshBoundedEntry(this.dotSurfaceByKey, key, cached, DOT_SURFACE_CACHE_LIMIT);
      return cached;
    }
    this.dotSurfaceCacheMisses += 1;
    const geometry = projection.source.byId.get(geometryId);
    if (!geometry) throw new Error(`unknown aggregate-dot geometry: ${geometryId}`);
    const prepared = prepareAggregateDotGeometry(geometry, projection.projection, projection.cacheKey);
    refreshBoundedEntry(this.dotSurfaceByKey, key, prepared, DOT_SURFACE_CACHE_LIMIT);
    return prepared;
  }

  prepareDensity(
    atlas: PublicSpacetimeAtlasDataset,
    geography: SpacetimeMapRegionMark,
    projection: PreparedSpacetimeProjection,
  ): PreparedSpacetimeDensity {
    if (atlas.dotPolicy.policyVersion !== DEFAULT_AGGREGATE_DOT_FIELD_POLICY.policyVersion) {
      throw new Error("atlas dot policy differs from the governed renderer policy");
    }
    if (atlas.dotPolicy.dotUnit !== DEFAULT_AGGREGATE_DOT_FIELD_POLICY.dotUnit) {
      throw new Error("atlas dot unit differs from the governed renderer policy");
    }
    const key = buildDotFieldCacheKey(atlas, geography, projection);
    const cached = this.dotFieldByKey.get(key);
    if (cached) {
      this.dotFieldCacheHits += 1;
      refreshBoundedEntry(this.dotFieldByKey, key, cached, DOT_FIELD_CACHE_LIMIT);
      return cached;
    }
    this.dotFieldCacheMisses += 1;

    // This is the frozen explicit multi-geometry rule: one aggregate anchor,
    // never one repeated dot field per component.
    if (geography.geometryIds.length > 1) {
      const prepared = Object.freeze({
        strategy: "multi_geometry_anchor" as const,
        dots: Object.freeze([]),
        generatedDotCount: 0,
        anchorRemainderCount: geography.recordCount,
        representedRecordCount: geography.recordCount,
        field: null,
        positionClaim: "aggregate_only" as const,
      });
      refreshBoundedEntry(this.dotFieldByKey, key, prepared, DOT_FIELD_CACHE_LIMIT);
      return prepared;
    }

    const geometry = projection.source.byId.get(geography.anchor.geometryId);
    if (!geometry) throw new Error(`unknown aggregate-dot anchor geometry: ${geography.anchor.geometryId}`);
    const field = generateAggregateDotField({
      geometry,
      projection: projection.projection,
      recordCount: geography.recordCount,
      seed: buildAggregateDotSeed({
        releaseId: atlas.release.researchReleaseId,
        geometryId: geometry.id,
        timeBucketId: atlas.selectedPeriod.periodId,
        recordCount: geography.recordCount,
        policyVersion: DEFAULT_AGGREGATE_DOT_FIELD_POLICY.policyVersion,
      }),
      fallbackAnchor: geography.anchor,
      preparedGeometry: this.prepareDotSurface(projection, geometry.id),
    });
    const prepared = Object.freeze({
      strategy: "dot_field" as const,
      dots: field.dots,
      generatedDotCount: field.generatedDotCount,
      anchorRemainderCount: field.fallback?.representedRecordCount ?? 0,
      representedRecordCount: field.representedRecordCount,
      field,
      positionClaim: "aggregate_only" as const,
    });
    refreshBoundedEntry(this.dotFieldByKey, key, prepared, DOT_FIELD_CACHE_LIMIT);
    return prepared;
  }

  diagnosticsForTests(): SpacetimeRendererRuntimeDiagnostics {
    return Object.freeze({
      dotSurfaceCacheEntries: this.dotSurfaceByKey.size,
      dotFieldCacheEntries: this.dotFieldByKey.size,
      dotSurfaceCacheHits: this.dotSurfaceCacheHits,
      dotSurfaceCacheMisses: this.dotSurfaceCacheMisses,
      dotFieldCacheHits: this.dotFieldCacheHits,
      dotFieldCacheMisses: this.dotFieldCacheMisses,
    });
  }

  resetForTests(): void {
    this.dotSurfaceByKey.clear();
    this.dotFieldByKey.clear();
    this.dotSurfaceCacheHits = 0;
    this.dotSurfaceCacheMisses = 0;
    this.dotFieldCacheHits = 0;
    this.dotFieldCacheMisses = 0;
  }
}

export const spacetimeRendererRuntimeCache = new SpacetimeRendererRuntimeCache();

export function deriveSpacetimeRendererModel(
  input: Readonly<{
    atlas: PublicSpacetimeAtlasDataset;
    projection: PreparedSpacetimeProjection;
    mode: SpacetimeRendererMode;
    selectedGeographyId: string | null;
    cache?: SpacetimeRendererRuntimeCache;
  }>,
): SpacetimeRendererModel {
  if (input.atlas.geometry.assetSha256 !== input.projection.geometryAssetSha256) {
    throw new Error("atlas and prepared projection geometry SHA differ");
  }
  ensureSpacetimeProjectionGeometryAnchors(
    input.projection,
    input.atlas.mappedGeographies.flatMap((geography) => geography.geometryIds),
  );
  const cache = input.cache ?? spacetimeRendererRuntimeCache;
  const viewModel = deriveSpacetimeMapViewModel({
    atlas: input.atlas,
    geometryIndex: input.projection.source.byId,
    projection: input.projection.projection,
    projectedAreaByGeometryId: input.projection.projectedAreaById,
    anchorByGeometryId: input.projection.anchorByGeometryId,
  });
  const marks = viewModel.mappedMarks.map((geography) => {
    const projected = input.projection.projection([
      geography.anchor.longitude,
      geography.anchor.latitude,
    ]);
    if (!projected) throw new Error(`aggregate anchor could not be projected: ${geography.geographyId}`);
    let density: PreparedSpacetimeDensity | null = null;
    let pattern: NativePatternDefinition | null = null;
    if (input.mode === "density") {
      density = cache.prepareDensity(input.atlas, geography, input.projection);
    } else if (input.mode === "texture") {
      const tier = deriveNativeCountTier(geography.recordCount);
      pattern = deriveNativePatternDefinition({
        namespace: [
          TRACE_NATIVE_COUNT_TIER_POLICY_VERSION,
          input.atlas.release.researchReleaseId,
          input.atlas.selectedPeriod.periodId,
          geography.geographyId,
        ].join(":"),
        family: "dots",
        encodedVariable: "record_count_tier",
        legendValue: tier.legendValue,
        spacingPx: tier.spacingPx,
        weightPx: tier.weightPx,
      });
    }
    return Object.freeze({
      geography,
      x: projected[0],
      y: projected[1],
      density,
      pattern,
    });
  });
  return Object.freeze({
    mode: input.mode,
    marks: Object.freeze(marks),
    semanticState: deriveSemanticState(input.atlas, input.selectedGeographyId),
  });
}

export function getSpacetimeRendererRuntimeDiagnosticsForTests(): SpacetimeRendererRuntimeDiagnostics {
  return spacetimeRendererRuntimeCache.diagnosticsForTests();
}

export function resetSpacetimeRendererRuntimeForTests(): void {
  spacetimeRendererRuntimeCache.resetForTests();
}
