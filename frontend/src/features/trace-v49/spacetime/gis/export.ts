import type { PublicSpacetimeAtlasDataset } from "../governed/types";
import {
  serializeNativePatternDefinition,
  TRACE_NATIVE_COUNT_TIERS,
  TRACE_NATIVE_COUNT_TIER_POLICY_VERSION,
} from "./native-pattern";
import type { PreparedSpacetimeProjection } from "./runtime-cache";
import type { SpacetimeRendererModel } from "./renderer";

const UUID_PATTERN = /\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b/iu;

function compareText(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0;
}

function canonicalValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value)
        .sort(([left], [right]) => compareText(left, right))
        .map(([key, child]) => [key, canonicalValue(child)]),
    );
  }
  return value;
}

function mappingSummary(atlas: PublicSpacetimeAtlasDataset) {
  const summarize = (mappingState: "mapped" | "aggregate_only" | "unmapped") => {
    const rows = atlas.accessibleRows.filter((row) => row.mappingState === mappingState);
    return Object.freeze({
      geographyCount: rows.length,
      recordCount: rows.reduce((sum, row) => sum + row.recordCount, 0),
    });
  };
  return Object.freeze({
    mapped: summarize("mapped"),
    aggregateOnly: summarize("aggregate_only"),
    unmapped: summarize("unmapped"),
  });
}

function legendFor(model: SpacetimeRendererModel, atlas: PublicSpacetimeAtlasDataset) {
  if (model.mode === "aggregate") {
    return Object.freeze({
      encodedVariable: "record_count",
      method: "aggregate_anchor_radius",
      positionClaim: "aggregate_only",
    });
  }
  if (model.mode === "density") {
    return Object.freeze({
      encodedVariable: "record_count",
      method: atlas.dotPolicy.policyVersion,
      dotUnit: atlas.dotPolicy.dotUnit,
      remainderMethod: "aggregate_anchor",
      positionClaim: "aggregate_only",
    });
  }
  return Object.freeze({
    encodedVariable: "record_count_tier",
    method: TRACE_NATIVE_COUNT_TIER_POLICY_VERSION,
    tiers: Object.freeze(TRACE_NATIVE_COUNT_TIERS.map((tier) => Object.freeze({ ...tier }))),
    positionClaim: "aggregate_only",
  });
}

/**
 * Prepare a deterministic, JSON/SVG-ready data contract. It intentionally
 * contains no DOM node, CSS state, archive record payload, or object coordinate.
 */
export function prepareSpacetimeFunctionalExport(input: Readonly<{
  atlas: PublicSpacetimeAtlasDataset;
  projection: PreparedSpacetimeProjection;
  renderer: SpacetimeRendererModel;
}>) {
  if (input.renderer.semanticState.selectedPeriodId !== input.atlas.selectedPeriod.periodId) {
    throw new Error("renderer/export period identity mismatch");
  }
  if (input.renderer.semanticState.denominator !== input.atlas.counts.denominator) {
    throw new Error("renderer/export denominator mismatch");
  }
  if (input.projection.geometryAssetSha256 !== input.atlas.geometry.assetSha256) {
    throw new Error("renderer/export geometry identity mismatch");
  }

  const baseMapGeometry = [...input.projection.pathById]
    .sort(([left], [right]) => compareText(left, right))
    .map(([geometryId, path]) => Object.freeze({ geometryId, path }));
  const marks = input.renderer.marks
    .slice()
    .sort((left, right) => compareText(left.geography.geographyId, right.geography.geographyId))
    .map((mark) => Object.freeze({
      geographyId: mark.geography.geographyId,
      label: mark.geography.label,
      geometryIds: mark.geography.geometryIds,
      recordCount: mark.geography.recordCount,
      denominator: mark.geography.denominator,
      precisionBreakdown: mark.geography.precisionBreakdown,
      anchor: Object.freeze({
        x: Number(mark.x.toFixed(3)),
        y: Number(mark.y.toFixed(3)),
        geometryId: mark.geography.anchor.geometryId,
        derivationMethod: mark.geography.anchor.method,
        coordinateSpace: "projected_aggregate_layout",
        positionClaim: "aggregate_only",
      }),
      density: mark.density
        ? Object.freeze({
            strategy: mark.density.strategy,
            generatedDotCount: mark.density.generatedDotCount,
            anchorRemainderCount: mark.density.anchorRemainderCount,
            representedRecordCount: mark.density.representedRecordCount,
            dots: Object.freeze(mark.density.dots.map((dot) => Object.freeze({
              id: dot.id,
              x: dot.x,
              y: dot.y,
              representedRecordCount: dot.representedRecordCount,
              coordinateSpace: "projected_aggregate_layout",
              positionClaim: "aggregate_only",
            }))),
          })
        : null,
      pattern: mark.pattern
        ? Object.freeze({
            definition: mark.pattern,
            svgDefinition: serializeNativePatternDefinition(mark.pattern),
          })
        : null,
      positionClaim: "aggregate_only",
    }));
  const geographyRows = input.atlas.accessibleRows
    .slice()
    .sort((left, right) => compareText(left.geographyId, right.geographyId))
    .map((row) => Object.freeze({
      geographyId: row.geographyId,
      label: row.label,
      mappingState: row.mappingState,
      recordCount: row.recordCount,
      denominator: row.denominator,
      precisionBreakdown: row.precisionBreakdown,
      interpretation: row.interpretation,
    }));
  const prepared = Object.freeze({
    schemaVersion: "trace-spacetime-functional-export/v1" as const,
    release: input.atlas.release,
    selectedPeriod: input.atlas.selectedPeriod,
    rendererMode: input.renderer.mode,
    projection: Object.freeze({
      projectionId: input.projection.projectionId,
      viewport: input.projection.viewport,
      projectionPrecision: input.projection.projectionPrecision,
      geometryArtifactId: input.atlas.geometry.geometryArtifactId,
      geometryAssetSha256: input.projection.geometryAssetSha256,
    }),
    baseMapGeometry: Object.freeze(baseMapGeometry),
    mapMarks: Object.freeze(marks),
    legend: legendFor(input.renderer, input.atlas),
    counts: Object.freeze({ ...input.atlas.counts }),
    mappingSummary: mappingSummary(input.atlas),
    geographyRows: Object.freeze(geographyRows),
    selectedGeographyId: input.renderer.semanticState.selectedGeographyId,
    coordinateInterpretation: "derived aggregate layout positions; not object coordinates",
    positionClaim: "aggregate_only" as const,
    realSemanticEdgeCount: 0 as const,
  });
  const serialized = serializeSpacetimeFunctionalExport(prepared);
  if (UUID_PATTERN.test(serialized)) throw new Error("internal UUID entered Spacetime functional export");
  if (prepared.geographyRows.some((row) => /\bheld\b/iu.test(row.label))) {
    throw new Error("held geography row entered Spacetime functional export");
  }
  return prepared;
}

export function serializeSpacetimeFunctionalExport(value: unknown): string {
  return `${JSON.stringify(canonicalValue(value))}\n`;
}
