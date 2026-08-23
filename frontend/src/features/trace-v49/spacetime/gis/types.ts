import type { Feature, FeatureCollection, MultiPolygon, Polygon, Position } from "geojson";
import type {
  PublicSpacetimeAccessibleGeographyRow,
  PublicSpacetimeDotPolicy,
  PublicSpacetimeGeometryReference,
  PublicSpacetimeNonMappedGeography,
  PublicSpacetimePeriod,
  PublicSpacetimePrecisionBreakdown,
} from "../governed/types";

export type GovernedPolygon = Polygon | MultiPolygon;

export interface GovernedGeometryProperties {
  readonly geometryId: string;
  readonly geometryClass: "admin0_country";
  readonly neId: string;
  readonly admin0A3: string | null;
  readonly isoA2: string | null;
  readonly isoA3: string | null;
  readonly isoN3: string | null;
  readonly name: string;
  readonly nameLong: string | null;
  readonly admin: string | null;
  readonly labelLongitude: number;
  readonly labelLatitude: number;
  readonly tinyScaleRank: number | null;
}

export type GovernedGeometryFeature = Feature<GovernedPolygon, GovernedGeometryProperties> & {
  readonly id: string;
};

export type GovernedGeometryCollection = FeatureCollection<GovernedPolygon, GovernedGeometryProperties> & {
  readonly name: string;
  readonly features: readonly GovernedGeometryFeature[];
};

export interface GovernedGeometryManifest {
  readonly geometryArtifactId: string;
  readonly source: "Natural Earth";
  readonly sourceDataset: "Admin 0 - Countries";
  readonly sourceVersion: string;
  readonly sourceScale: "110m" | "50m" | "10m";
  readonly sourceUrl: string;
  readonly sourceSha256: string;
  readonly license: "Public domain";
  readonly licenseUrl: string;
  readonly boundaryPolicy: string;
  readonly conversionTool: string;
  readonly conversionVersion: string;
  readonly outputFormat: string;
  readonly outputFilename: string;
  readonly publicAssetPath: string;
  readonly outputSha256: string;
  readonly outputRawBytes: number;
  readonly outputGzipBytes: number;
  readonly featureCount: number;
  readonly generatedAt: string;
}

export type SpacetimeProjectionKind = "equal-earth" | "natural-earth-1";

export interface SpacetimeProjectionViewport {
  readonly width: number;
  readonly height: number;
  readonly padding: number;
}

export interface AggregateLayoutAnchor {
  readonly semanticKind: "aggregate_layout_anchor";
  readonly longitude: number;
  readonly latitude: number;
  readonly geometryId: string;
  readonly geometryArtifactId: string;
  readonly geometryVersion: string;
  readonly derivationVersion: "trace-region-anchor-v1";
  readonly method:
    | "registered_override"
    | "geo_centroid"
    | "projected_path_centroid"
    | "natural_earth_label_point"
    | "deterministic_interior_grid";
  readonly positionClaim: "aggregate_only";
}

export interface RegisteredAggregateAnchor {
  readonly longitude: number;
  readonly latitude: number;
  readonly registryEntryId: string;
}

export interface AggregateDotFieldPolicy {
  readonly policyVersion: "trace-dot-density-grid-v1";
  readonly dotUnit: number;
  readonly preferredSpacingPx: number;
  readonly minimumSpacingPx: number;
  readonly maxDots: number;
  readonly maxCandidateTests: number;
  readonly tinyGeometryPolicy: "aggregate_anchor";
  readonly multipartPolicy: "whole_geometry_candidate_pool";
}

export interface AggregateDensityDot {
  readonly id: string;
  readonly semanticKind: "aggregate_density_mark";
  readonly x: number;
  readonly y: number;
  readonly representedRecordCount: number;
  readonly positionClaim: "aggregate_only";
}

export interface AggregateDotFallback {
  readonly semanticKind: "aggregate_anchor_mark";
  readonly anchor: AggregateLayoutAnchor;
  readonly representedRecordCount: number;
  readonly reason: "tiny_geometry" | "candidate_capacity" | "dot_budget";
  readonly positionClaim: "aggregate_only";
}

export interface AggregateDotField {
  readonly semanticKind: "aggregate_density_field";
  readonly policyVersion: AggregateDotFieldPolicy["policyVersion"];
  readonly geometryId: string;
  readonly seed: string;
  readonly recordCount: number;
  readonly dotUnit: number;
  readonly requestedDotCount: number;
  readonly generatedDotCount: number;
  readonly representedRecordCount: number;
  readonly dots: readonly AggregateDensityDot[];
  readonly fallback: AggregateDotFallback | null;
  readonly positionClaim: "aggregate_only";
}

export interface SpacetimeMapRegionMark {
  readonly geographyId: string;
  readonly label: string;
  readonly geometryIds: readonly string[];
  readonly recordCount: number;
  readonly denominator: number;
  readonly mappedState: "mapped";
  readonly anchor: AggregateLayoutAnchor;
  readonly anchorComponentPolicy: "largest_projected_area";
  readonly precisionBreakdown: PublicSpacetimePrecisionBreakdown;
  readonly qualification: string | null;
  readonly historicalStatus: boolean;
  readonly transnational: boolean;
  readonly broadRegion: boolean;
  readonly positionClaim: "aggregate_only";
}

export interface SpacetimeMapViewModel {
  readonly selectedPeriod: PublicSpacetimePeriod;
  readonly mappedMarks: readonly SpacetimeMapRegionMark[];
  readonly aggregateOnlyGeographies: readonly PublicSpacetimeNonMappedGeography[];
  readonly unmappedGeographies: readonly PublicSpacetimeNonMappedGeography[];
  readonly accessibleRows: readonly PublicSpacetimeAccessibleGeographyRow[];
  readonly counts: Readonly<{
    denominator: number;
    mappedRecords: number;
    unmappedRecords: number;
    geographyAssignments: number;
    heldExcluded: number;
  }>;
  readonly dotPolicy: PublicSpacetimeDotPolicy;
  readonly geometry: PublicSpacetimeGeometryReference;
  readonly realSemanticEdgeCount: 0;
}

export type SpacetimeMapSelection =
  | Readonly<{ kind: "mapped"; value: SpacetimeMapRegionMark }>
  | Readonly<{ kind: "aggregate_only"; value: PublicSpacetimeNonMappedGeography }>
  | Readonly<{ kind: "unmapped"; value: PublicSpacetimeNonMappedGeography }>;

export type NativePatternFamily = "dots" | "horizontal_lines" | "diagonal_lines";
export type NativePatternVariable = "record_count_tier" | "precision_mix" | "mapping_qualification";

export interface NativePatternDefinition {
  readonly id: string;
  readonly family: NativePatternFamily;
  readonly encodedVariable: NativePatternVariable;
  readonly legendValue: string;
  readonly width: number;
  readonly height: number;
  readonly primitive:
    | Readonly<{ kind: "circle"; cx: number; cy: number; radius: number }>
    | Readonly<{ kind: "line"; x1: number; y1: number; x2: number; y2: number; strokeWidth: number }>;
  readonly deterministic: true;
}

export type GeographicPosition = Position;
