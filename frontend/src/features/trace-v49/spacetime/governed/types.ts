export const TRACE_SPACETIME_PUBLIC_SCHEMA_VERSION = "trace-spacetime/v1" as const;
export const TRACE_SPACETIME_PUBLIC_PROJECTION_ID = "trace-spacetime-v1" as const;
export const TRACE_SPACETIME_GEOGRAPHY_POLICY_VERSION =
  "spacetime-geography-governance-v1" as const;
export const TRACE_SPACETIME_TEMPORAL_POLICY_VERSION =
  "spacetime-temporal-governance-v1" as const;
export const TRACE_SPACETIME_TIME_BUCKET_POLICY = "DECADE" as const;
export const TRACE_SPACETIME_RANGE_MEMBERSHIP_POLICY = "INTERVAL_OVERLAP" as const;

export type PublicSpacetimeTimePrecision =
  | "day"
  | "month"
  | "year"
  | "range"
  | "approximate"
  | "unknown";

export type PublicSpacetimeGeographyClass =
  | "country"
  | "territory"
  | "subnational"
  | "broad_region"
  | "transnational"
  | "historical"
  | "unresolved"
  | "other";

export type PublicSpacetimeMappingState =
  | "mapped"
  | "aggregate_only"
  | "unmapped";

export interface PublicSpacetimeReleaseIdentity {
  readonly researchReleaseId: string;
  readonly researchManifestSha256: string;
  readonly spacetimeProjectionId: typeof TRACE_SPACETIME_PUBLIC_PROJECTION_ID;
  readonly spacetimeProjectionSha256: string;
}

export interface PublicSpacetimePrecisionBreakdown {
  readonly day: number;
  readonly month: number;
  readonly year: number;
  readonly range: number;
  readonly approximate: number;
  readonly unknown: number;
}

export interface PublicSpacetimePeriod {
  readonly periodId: string;
  readonly label: string;
  readonly startYearInclusive: number;
  readonly endYearExclusive: number;
  readonly membershipPolicy: typeof TRACE_SPACETIME_RANGE_MEMBERSHIP_POLICY;
  readonly recordCount: number;
  readonly mappedRecordCount: number;
  readonly unmappedRecordCount: number;
  readonly precisionBreakdown: PublicSpacetimePrecisionBreakdown;
}

export interface PublicSpacetimeGeometryReference {
  readonly geometryArtifactId: string;
  readonly source: "Natural Earth";
  readonly sourceVersion: string;
  readonly sourceScale: "110m" | "50m" | "10m";
  readonly assetPath: string;
  readonly assetSha256: string;
  readonly featureCount: number;
  readonly boundaryPolicy: string;
}

export interface PublicSpacetimePeriodsDataset {
  readonly schemaVersion: typeof TRACE_SPACETIME_PUBLIC_SCHEMA_VERSION;
  readonly release: PublicSpacetimeReleaseIdentity;
  readonly temporalRole: "recorded_date_context";
  readonly temporalPolicyVersion: typeof TRACE_SPACETIME_TEMPORAL_POLICY_VERSION;
  readonly bucketPolicy: typeof TRACE_SPACETIME_TIME_BUCKET_POLICY;
  readonly rangeMembershipPolicy: typeof TRACE_SPACETIME_RANGE_MEMBERSHIP_POLICY;
  readonly defaultPeriodId: string;
  readonly periods: readonly PublicSpacetimePeriod[];
  readonly geometry: PublicSpacetimeGeometryReference;
}

export interface PublicSpacetimeMappedGeography {
  readonly geographyId: string;
  readonly label: string;
  readonly geographyClass: PublicSpacetimeGeographyClass;
  readonly mappingState: "mapped";
  readonly geometryIds: readonly string[];
  readonly recordCount: number;
  readonly denominator: number;
  readonly precisionBreakdown: PublicSpacetimePrecisionBreakdown;
  readonly qualification: string | null;
  readonly historicalStatus: boolean;
  readonly transnational: boolean;
  readonly broadRegion: boolean;
}

export interface PublicSpacetimeNonMappedGeography {
  readonly geographyId: string;
  readonly label: string;
  readonly geographyClass: PublicSpacetimeGeographyClass;
  readonly mappingState: "aggregate_only" | "unmapped";
  readonly recordCount: number;
  readonly denominator: number;
  readonly precisionBreakdown: PublicSpacetimePrecisionBreakdown;
  readonly qualification: string;
  readonly historicalStatus: boolean;
  readonly transnational: boolean;
  readonly broadRegion: boolean;
}

export interface PublicSpacetimeAccessibleGeographyRow {
  readonly id: string;
  readonly geographyId: string;
  readonly label: string;
  readonly mappingState: PublicSpacetimeMappingState;
  readonly recordCount: number;
  readonly denominator: number;
  readonly precisionBreakdown: PublicSpacetimePrecisionBreakdown;
  readonly interpretation: string;
}

export interface PublicSpacetimeDotPolicy {
  readonly semanticKind: "aggregate_density_mark";
  readonly policyVersion: string;
  readonly dotUnit: number;
  readonly positionClaim: "aggregate_only";
}

export interface PublicSpacetimeAtlasDataset {
  readonly schemaVersion: typeof TRACE_SPACETIME_PUBLIC_SCHEMA_VERSION;
  readonly release: PublicSpacetimeReleaseIdentity;
  readonly geographyRole: "recorded_region_context";
  readonly temporalRole: "recorded_date_context";
  readonly geographyPolicyVersion: typeof TRACE_SPACETIME_GEOGRAPHY_POLICY_VERSION;
  readonly temporalPolicyVersion: typeof TRACE_SPACETIME_TEMPORAL_POLICY_VERSION;
  readonly selectedPeriod: PublicSpacetimePeriod;
  readonly counts: Readonly<{
    denominator: number;
    mappedRecords: number;
    unmappedRecords: number;
    geographyAssignments: number;
    heldExcluded: number;
  }>;
  readonly mappedGeographies: readonly PublicSpacetimeMappedGeography[];
  readonly aggregateOnlyGeographies: readonly PublicSpacetimeNonMappedGeography[];
  readonly unmappedGeographies: readonly PublicSpacetimeNonMappedGeography[];
  readonly accessibleRows: readonly PublicSpacetimeAccessibleGeographyRow[];
  readonly dotPolicy: PublicSpacetimeDotPolicy;
  readonly geometry: PublicSpacetimeGeometryReference;
  readonly realSemanticEdgeCount: 0;
}

export interface PublicSpacetimeRecordSummary {
  readonly stableId: string;
  readonly title: string;
  readonly geographyIds: readonly string[];
  readonly recordedRegionDisplays: readonly string[];
  readonly time: Readonly<{
    role: "recorded_context";
    sourceDisplay: string;
    startYearInclusive: number;
    endYearInclusive: number;
    precision: PublicSpacetimeTimePrecision;
    derivationMethod: string;
  }>;
}

export interface PublicSpacetimeRecordPage {
  readonly schemaVersion: typeof TRACE_SPACETIME_PUBLIC_SCHEMA_VERSION;
  readonly release: PublicSpacetimeReleaseIdentity;
  readonly period: PublicSpacetimePeriod;
  readonly geography: Readonly<{
    geographyId: string;
    label: string;
    mappingState: PublicSpacetimeMappingState;
  }>;
  readonly nodes: readonly PublicSpacetimeRecordSummary[];
  readonly pageInfo: Readonly<{
    hasNextPage: boolean;
    endCursor: string | null;
  }>;
  readonly totalCount: number;
}

export type GovernedSpacetimeLookup<T> =
  | Readonly<{ ok: true; data: T }>
  | Readonly<{
    ok: false;
    code: "INVALID_ARGUMENT" | "NOT_FOUND" | "RELEASE_NOT_FOUND" | "INTEGRITY_FAILURE";
    message: string;
  }>;
