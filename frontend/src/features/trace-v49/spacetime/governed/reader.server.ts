import "server-only";

import { createHash } from "node:crypto";
import { performance } from "node:perf_hooks";
import geographyRegistryJson from "../../../../../generated/trace-spacetime-v1/geography-registry.json";
import geometryManifestJson from "../../../../../generated/trace-spacetime-v1/geometry/geometry-manifest.json";
import governancePolicyJson from "../../../../../generated/trace-spacetime-v1/governance-policy.json";
import manifestJson from "../../../../../generated/trace-spacetime-v1/manifest.json";
import periodRegionAggregatesJson from "../../../../../generated/trace-spacetime-v1/period-region-aggregates.json";
import recordIndexJson from "../../../../../generated/trace-spacetime-v1/record-index.json";
import timeBucketsJson from "../../../../../generated/trace-spacetime-v1/time-buckets.json";
import {
  TRACE_SPACETIME_GEOGRAPHY_POLICY_VERSION,
  TRACE_SPACETIME_PUBLIC_PROJECTION_ID,
  TRACE_SPACETIME_PUBLIC_SCHEMA_VERSION,
  TRACE_SPACETIME_RANGE_MEMBERSHIP_POLICY,
  TRACE_SPACETIME_TEMPORAL_POLICY_VERSION,
  TRACE_SPACETIME_TIME_BUCKET_POLICY,
  type GovernedSpacetimeLookup,
  type PublicSpacetimeAccessibleGeographyRow,
  type PublicSpacetimeAtlasDataset,
  type PublicSpacetimeGeographyClass,
  type PublicSpacetimeGeometryReference,
  type PublicSpacetimeMappedGeography,
  type PublicSpacetimeMappingState,
  type PublicSpacetimeNonMappedGeography,
  type PublicSpacetimePeriod,
  type PublicSpacetimePeriodsDataset,
  type PublicSpacetimePrecisionBreakdown,
  type PublicSpacetimeRecordPage,
  type PublicSpacetimeRecordSummary,
  type PublicSpacetimeTimePrecision,
} from "./types";

const MANIFEST_FORMAT = "trace-spacetime-projection-manifest/v1" as const;
const GOVERNANCE_POLICY_FORMAT = "trace-spacetime-governance-policy/v1" as const;
const GEOGRAPHY_REGISTRY_FORMAT = "trace-spacetime-geography-registry/v1" as const;
const TIME_BUCKETS_FORMAT = "trace-spacetime-time-buckets/v1" as const;
const PERIOD_AGGREGATES_FORMAT = "trace-spacetime-period-region-aggregates/v1" as const;
const RECORD_INDEX_FORMAT = "trace-spacetime-record-index/v1" as const;
const GENERATOR_VERSION = "trace-spacetime-projection-generator-v1" as const;
const ID_POLICY_VERSION = "trace-spacetime-public-id-v1" as const;
const CANONICAL_SERIALIZATION =
  "recursive-key-sort;array-order-preserved;json-minified;final-lf;utf8" as const;
const GEOGRAPHY_ROLE = "recorded_region_context" as const;
const TEMPORAL_ROLE = "recorded_date_context" as const;
const DOT_POLICY_VERSION = "trace-dot-density-grid-v1" as const;
const DOT_UNIT = 1 as const;
const DEFAULT_PAGE_SIZE = 24;
const MAX_PAGE_SIZE = 100;
const EXPECTED_PUBLIC_RECORDS = 7_995;
const EXPECTED_HELD_RECORDS = 7_928;
const EXPECTED_GEOGRAPHIES = 93;
const EXPECTED_PERIODS = 23;
const SOURCE_RELEASE = Object.freeze({
  researchReleaseId: "v49-api-contract-fresh-c",
  researchManifestSha256:
    "4addfdb3cb9314587908096572242b9d63e9cef9e6e1be68c0c646491a43a90a",
});
const SOURCE_BINDINGS = Object.freeze({
  "data/prefreeze_candidate_v48.sqlite":
    "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e",
  "database/FREEZE_V49.json":
    "f0dda59dd515ba243eaf213bce9f42513727f1ab0a44685635921c3759a7d22e",
  "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv":
    "48f98f68ca2ec0cef96c82ecc9c01e4129eb9a3f91e08b07ad9a59644a9d4e01",
  "docs/statistics/v49-release-data-profile.json":
    "091dba486c2096f99c332b03cf9586139f1bc26594bce4e1575d2b1ddc8fea0f",
});

const SHA256_PATTERN = /^[0-9a-f]{64}$/u;
const GEOGRAPHY_ID_PATTERN = /^SPTGEO:[0-9a-f]{64}$/u;
const TIME_OBSERVATION_ID_PATTERN = /^SPTTIME:[0-9a-f]{64}$/u;
const PERIOD_ID_PATTERN = /^SPT-PERIOD-[0-9]{4}-[0-9]{4}$/u;
const PUBLIC_STABLE_ID_PATTERN = /^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$/u;
const UUID_PATTERN = /\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b/iu;
const PRIVATE_FOLDER_PATTERN = /FOL-REGION-/u;

type ArtifactSourceRelease = typeof SOURCE_RELEASE;
type ArtifactPrecision = PublicSpacetimePrecisionBreakdown;
type ArtifactPeriod = PublicSpacetimePeriod;
type MutablePrecision = Record<PublicSpacetimeTimePrecision, number>;

interface ArtifactManifest {
  readonly format: string;
  readonly schemaVersion: string;
  readonly projectionId: string;
  readonly projectionSha256: string;
  readonly deterministic: boolean;
  readonly canonicalSerialization: string;
  readonly generatorVersion: string;
  readonly serverOnly: boolean;
  readonly sourceRelease: ArtifactSourceRelease;
  readonly sourceBindings: Readonly<Record<string, string>>;
  readonly idPolicyVersion: string;
  readonly geographyPolicyVersion: string;
  readonly temporalPolicyVersion: string;
  readonly bucketPolicy: string;
  readonly rangeMembershipPolicy: string;
  readonly geometry: Readonly<{
    geometryArtifactId: string;
    geometryManifestPath: string;
    geometryManifestSha256: string;
    assetPath: string;
    assetSha256: string;
    featureCount: number;
  }>;
  readonly counts: Readonly<{
    publicObjects: number;
    heldObjects: number;
    regionAssignments: number;
    regionObjectCoverage: number;
    rawRegionLabels: number;
    governedGeographyEntries: number;
    mappedGeographyEntries: number;
    aggregateOnlyGeographyEntries: number;
    unmappedGeographyEntries: number;
    mappedObjects: number;
    aggregateOnlyObjects: number;
    unmappedObjects: number;
    temporalObjectCoverage: number;
    temporalPrecision: ArtifactPrecision;
    earliestGovernedYear: number;
    latestGovernedYear: number;
    timeBuckets: number;
    periodRegionCells: number;
  }>;
  readonly defaultPeriodId: string;
  readonly payloadSha256: Readonly<Record<string, string>>;
}

interface ArtifactGovernancePolicy {
  readonly format: string;
  readonly schemaVersion: string;
  readonly projectionId: string;
  readonly sourceRelease: ArtifactSourceRelease;
  readonly geographyPolicyVersion: string;
  readonly temporalPolicyVersion: string;
  readonly geographyRole: Readonly<{ role: string; statement: string }>;
  readonly temporalRole: Readonly<{ role: string; statement: string }>;
  readonly heldBoundary: Readonly<{
    heldObjectCount: number;
    heldObjectsProjected: number;
  }>;
  readonly invariants: readonly string[];
}

interface ArtifactGeometryManifest {
  readonly geometryArtifactId: string;
  readonly source: "Natural Earth";
  readonly sourceVersion: string;
  readonly sourceScale: "110m" | "50m" | "10m";
  readonly boundaryPolicy: string;
  readonly publicAssetPath: string;
  readonly outputSha256: string;
  readonly featureCount: number;
}

interface ArtifactGeometryTarget {
  readonly geometryArtifactId: string;
  readonly geometryId: string;
  readonly matchField: string;
  readonly matchValue: string;
}

interface ArtifactGeography {
  readonly geographyId: string;
  readonly sourceLabel: string;
  readonly sourceLabelSha256: string;
  readonly sourceAssignmentCount: number;
  readonly displayLabel: string;
  readonly geographyClass: PublicSpacetimeGeographyClass;
  readonly mappingDecision: string;
  readonly mappingState: PublicSpacetimeMappingState;
  readonly geometryTargets: readonly ArtifactGeometryTarget[];
  readonly geometryIds: readonly string[];
  readonly mapEligible: boolean;
  readonly aggregateEligible: boolean;
  readonly representativePointPolicy: string;
  readonly historicalStatus: boolean;
  readonly transnational: boolean;
  readonly broadRegion: boolean;
  readonly qualification: string | null;
  readonly decisionRationale: string;
  readonly reviewStatus: string;
}

interface ArtifactGeographyRegistry {
  readonly format: string;
  readonly schemaVersion: string;
  readonly projectionId: string;
  readonly sourceRelease: ArtifactSourceRelease;
  readonly geographyRole: string;
  readonly geographyPolicyVersion: string;
  readonly idPolicyVersion: string;
  readonly geometryArtifactId: string;
  readonly counts: Readonly<{
    registryEntries: number;
    mappedEntries: number;
    aggregateOnlyEntries: number;
    unmappedEntries: number;
    heldEntries: number;
    sourceAssignments: number;
    sourceObjectCoverage: number;
  }>;
  readonly entries: readonly ArtifactGeography[];
}

interface ArtifactTimeBuckets {
  readonly format: string;
  readonly schemaVersion: string;
  readonly projectionId: string;
  readonly sourceRelease: ArtifactSourceRelease;
  readonly temporalRole: string;
  readonly temporalPolicyVersion: string;
  readonly bucketPolicy: string;
  readonly rangeMembershipPolicy: string;
  readonly defaultPeriodId: string;
  readonly periods: readonly ArtifactPeriod[];
}

interface ArtifactAggregateCell {
  readonly geographyId: string;
  readonly recordCount: number;
  readonly denominator: number;
  readonly precisionBreakdown: ArtifactPrecision;
  readonly mappingState: PublicSpacetimeMappingState;
  readonly unmappedCount: number;
}

interface ArtifactPeriodAggregate {
  readonly periodId: string;
  readonly denominator: number;
  readonly mappedRecordCount: number;
  readonly unmappedRecordCount: number;
  readonly geographyAssignmentCount: number;
  readonly cells: readonly ArtifactAggregateCell[];
}

interface ArtifactPeriodAggregates {
  readonly format: string;
  readonly schemaVersion: string;
  readonly projectionId: string;
  readonly sourceRelease: ArtifactSourceRelease;
  readonly geographyPolicyVersion: string;
  readonly temporalPolicyVersion: string;
  readonly bucketPolicy: string;
  readonly rangeMembershipPolicy: string;
  readonly periodCount: number;
  readonly periods: readonly ArtifactPeriodAggregate[];
}

interface ArtifactRecord {
  readonly objectId: string;
  readonly title: string;
  readonly geographyIds: readonly string[];
  readonly recordedRegionDisplays: readonly string[];
  readonly rawRegionDisplay: string;
  readonly time: Readonly<{
    observationId: string;
    role: "recorded_context";
    sourceDisplay: string;
    startYearInclusive: number;
    endYearInclusive: number;
    precision: PublicSpacetimeTimePrecision;
    derivationMethod: string;
  }>;
  readonly periodIds: readonly string[];
}

interface ArtifactRecordIndex {
  readonly format: string;
  readonly schemaVersion: string;
  readonly projectionId: string;
  readonly sourceRelease: ArtifactSourceRelease;
  readonly geographyRole: string;
  readonly temporalRole: string;
  readonly geographyPolicyVersion: string;
  readonly temporalPolicyVersion: string;
  readonly rangeMembershipPolicy: string;
  readonly serverOnly: boolean;
  readonly counts: Readonly<{
    records: number;
    mappedObjects: number;
    aggregateOnlyObjects: number;
    unmappedObjects: number;
    heldObjects: number;
    precision: ArtifactPrecision;
  }>;
  readonly records: readonly ArtifactRecord[];
}

export interface GovernedSpacetimeProjectionInfo {
  readonly projectionId: typeof TRACE_SPACETIME_PUBLIC_PROJECTION_ID;
  readonly projectionSha256: string;
  readonly researchReleaseId: string;
  readonly researchManifestSha256: string;
  readonly recordCount: number;
  readonly geographyCount: number;
  readonly periodCount: number;
  readonly periodRegionCellCount: number;
  readonly heldExcluded: number;
}

export interface GovernedSpacetimeReaderBuildTiming {
  readonly payloadVerificationMs: number;
  readonly registryValidationMs: number;
  readonly recordIndexConstructionMs: number;
  readonly aggregateValidationMs: number;
  readonly publicProjectionConstructionMs: number;
  readonly totalMs: number;
}

export interface GovernedSpacetimeReaderRuntimeDiagnostics {
  readonly indexInitialized: boolean;
  readonly indexBuildAttempts: number;
  readonly successfulIndexBuilds: number;
  readonly lastSuccessfulBuildTiming: GovernedSpacetimeReaderBuildTiming | null;
}

type GovernedSpacetimeRecordLookup =
  | Readonly<{ ok: true; data: PublicSpacetimeRecordPage }>
  | Readonly<{
    ok: false;
    code: "INVALID_ARGUMENT" | "INVALID_CURSOR" | "NOT_FOUND" | "INTEGRITY_FAILURE";
    message: string;
  }>;

interface GovernedSpacetimeIndex {
  readonly manifest: ArtifactManifest;
  readonly info: GovernedSpacetimeProjectionInfo;
  readonly periodsDataset: PublicSpacetimePeriodsDataset;
  readonly periodById: ReadonlyMap<string, PublicSpacetimePeriod>;
  readonly aggregateByPeriodId: ReadonlyMap<string, ArtifactPeriodAggregate>;
  readonly geographyById: ReadonlyMap<string, ArtifactGeography>;
  readonly recordsByPeriodGeography: ReadonlyMap<string, readonly ArtifactRecord[]>;
  readonly geometry: PublicSpacetimeGeometryReference;
}

let cachedIndex: GovernedSpacetimeIndex | null = null;
let indexBuildAttempts = 0;
let successfulIndexBuilds = 0;
let lastSuccessfulBuildTiming: GovernedSpacetimeReaderBuildTiming | null = null;

function compareText(left: string, right: string): number {
  return left.localeCompare(right, "en", { sensitivity: "variant" });
}

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function assertText(value: unknown, field: string): asserts value is string {
  assert(typeof value === "string" && value.trim().length > 0, `${field} must be non-empty text`);
}

function assertCount(value: unknown, field: string): asserts value is number {
  assert(Number.isSafeInteger(value) && Number(value) >= 0, `${field} must be a non-negative safe integer`);
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

function canonicalBytes(value: unknown): Buffer {
  return Buffer.from(`${JSON.stringify(canonicalValue(value))}\n`, "utf8");
}

function serializedBytesPreservingOrder(value: unknown): Buffer {
  return Buffer.from(`${JSON.stringify(value)}\n`, "utf8");
}

function sha256(value: string | Buffer): string {
  return createHash("sha256").update(value).digest("hex");
}

function sameCanonical(left: unknown, right: unknown): boolean {
  return Buffer.compare(canonicalBytes(left), canonicalBytes(right)) === 0;
}

function deepFreeze<T>(value: T): T {
  if (value && typeof value === "object" && !Object.isFrozen(value)) {
    for (const child of Object.values(value)) deepFreeze(child);
    Object.freeze(value);
  }
  return value;
}

function assertSourceRelease(value: ArtifactSourceRelease, field: string): void {
  assert(sameCanonical(value, SOURCE_RELEASE), `${field} source release differs`);
}

function assertCoreDocument(
  document: Readonly<{
    schemaVersion: string;
    projectionId: string;
    sourceRelease: ArtifactSourceRelease;
  }>,
  field: string,
): void {
  assert(document.schemaVersion === TRACE_SPACETIME_PUBLIC_SCHEMA_VERSION, `${field} schema differs`);
  assert(document.projectionId === TRACE_SPACETIME_PUBLIC_PROJECTION_ID, `${field} projection differs`);
  assertSourceRelease(document.sourceRelease, field);
}

function precisionTotal(value: ArtifactPrecision): number {
  return value.day + value.month + value.year + value.range + value.approximate + value.unknown;
}

function assertPrecision(value: ArtifactPrecision, expected: number, field: string): void {
  for (const key of ["day", "month", "year", "range", "approximate", "unknown"] as const) {
    assertCount(value[key], `${field}.${key}`);
  }
  assert(precisionTotal(value) === expected, `${field} total differs`);
}

function freezePrecision(value: ArtifactPrecision): PublicSpacetimePrecisionBreakdown {
  return Object.freeze({
    day: value.day,
    month: value.month,
    year: value.year,
    range: value.range,
    approximate: value.approximate,
    unknown: value.unknown,
  });
}

function freezePeriod(value: ArtifactPeriod): PublicSpacetimePeriod {
  return Object.freeze({
    periodId: value.periodId,
    label: value.label,
    startYearInclusive: value.startYearInclusive,
    endYearExclusive: value.endYearExclusive,
    membershipPolicy: TRACE_SPACETIME_RANGE_MEMBERSHIP_POLICY,
    recordCount: value.recordCount,
    mappedRecordCount: value.mappedRecordCount,
    unmappedRecordCount: value.unmappedRecordCount,
    precisionBreakdown: freezePrecision(value.precisionBreakdown),
  });
}

function lookupKey(periodId: string, geographyId: string): string {
  return `${periodId}\0${geographyId}`;
}

function validatePayloadBindings(
  manifest: ArtifactManifest,
  geometryManifest: ArtifactGeometryManifest,
  payloads: Readonly<Record<string, unknown>>,
): void {
  assert(manifest.format === MANIFEST_FORMAT, "Spacetime manifest format differs");
  assert(manifest.schemaVersion === TRACE_SPACETIME_PUBLIC_SCHEMA_VERSION, "Spacetime manifest schema differs");
  assert(manifest.projectionId === TRACE_SPACETIME_PUBLIC_PROJECTION_ID, "Spacetime manifest projection differs");
  assert(SHA256_PATTERN.test(manifest.projectionSha256), "Spacetime projection SHA is invalid");
  assert(manifest.deterministic === true && manifest.serverOnly === true, "Spacetime projection boundary differs");
  assert(manifest.canonicalSerialization === CANONICAL_SERIALIZATION, "Spacetime canonical serialization differs");
  assert(manifest.generatorVersion === GENERATOR_VERSION, "Spacetime generator version differs");
  assertSourceRelease(manifest.sourceRelease, "manifest");
  assert(sameCanonical(manifest.sourceBindings, SOURCE_BINDINGS), "Spacetime frozen input bindings differ");
  assert(manifest.idPolicyVersion === ID_POLICY_VERSION, "Spacetime ID policy differs");
  assert(manifest.geographyPolicyVersion === TRACE_SPACETIME_GEOGRAPHY_POLICY_VERSION, "Spacetime geography policy differs");
  assert(manifest.temporalPolicyVersion === TRACE_SPACETIME_TEMPORAL_POLICY_VERSION, "Spacetime temporal policy differs");
  assert(manifest.bucketPolicy === TRACE_SPACETIME_TIME_BUCKET_POLICY, "Spacetime bucket policy differs");
  assert(manifest.rangeMembershipPolicy === TRACE_SPACETIME_RANGE_MEMBERSHIP_POLICY, "Spacetime membership policy differs");
  assert(Object.keys(payloads).length === 5, "Spacetime payload set differs");
  for (const [filename, payload] of Object.entries(payloads)) {
    assert(manifest.payloadSha256[filename] === sha256(canonicalBytes(payload)), `${filename} hash differs`);
  }
  assert(Object.keys(manifest.payloadSha256).length === Object.keys(payloads).length, "Spacetime payload hash set differs");
  assertText(geometryManifest.geometryArtifactId, "geometry artifact ID");
  assert(geometryManifest.source === "Natural Earth", "Spacetime geometry source differs");
  assert(SHA256_PATTERN.test(geometryManifest.outputSha256), "Spacetime geometry asset SHA is invalid");
  assertCount(geometryManifest.featureCount, "Spacetime geometry feature count");
  assert(manifest.geometry.geometryManifestPath === "geometry/geometry-manifest.json", "geometry manifest path differs");
  const geometryManifestSha256 = sha256(serializedBytesPreservingOrder(geometryManifest));
  assert(manifest.geometry.geometryManifestSha256 === geometryManifestSha256, "geometry manifest hash differs");
  assert(manifest.geometry.geometryArtifactId === geometryManifest.geometryArtifactId, "geometry artifact pin differs");
  assert(manifest.geometry.assetPath === geometryManifest.publicAssetPath, "geometry asset path differs");
  assert(manifest.geometry.assetSha256 === geometryManifest.outputSha256, "geometry asset hash differs");
  assert(manifest.geometry.featureCount === geometryManifest.featureCount, "geometry feature count differs");
  const projectionMaterial = Object.freeze({
    projectionId: TRACE_SPACETIME_PUBLIC_PROJECTION_ID,
    payloadHashes: manifest.payloadSha256,
    // The geometry generator's manifest is deterministic minified JSON whose
    // field order is itself pinned. The projection generator hashes those raw
    // serialized bytes, while the five semantic payloads use canonical keys.
    geometryManifestSha256,
    geometryAssetSha256: geometryManifest.outputSha256,
  });
  assert(sha256(canonicalBytes(projectionMaterial)) === manifest.projectionSha256, "Spacetime projection aggregate hash differs");
}

function validateGeographyRegistry(
  document: ArtifactGeographyRegistry,
  manifest: ArtifactManifest,
  geometryManifest: ArtifactGeometryManifest,
): ReadonlyMap<string, ArtifactGeography> {
  assertCoreDocument(document, "geography registry");
  assert(document.format === GEOGRAPHY_REGISTRY_FORMAT, "geography registry format differs");
  assert(document.geographyRole === GEOGRAPHY_ROLE, "geography registry role differs");
  assert(document.geographyPolicyVersion === TRACE_SPACETIME_GEOGRAPHY_POLICY_VERSION, "geography registry policy differs");
  assert(document.idPolicyVersion === ID_POLICY_VERSION, "geography registry ID policy differs");
  assert(document.geometryArtifactId === geometryManifest.geometryArtifactId, "geography registry geometry differs");
  assert(Array.isArray(document.entries) && document.entries.length === EXPECTED_GEOGRAPHIES, "geography registry count differs");
  const byId = new Map<string, ArtifactGeography>();
  let mapped = 0;
  let aggregateOnly = 0;
  let unmapped = 0;
  let assignments = 0;
  let priorLabel = "";
  for (const entry of document.entries) {
    assert(GEOGRAPHY_ID_PATTERN.test(entry.geographyId), "governed geography ID is invalid");
    assertText(entry.sourceLabel, "geography source label");
    assert(compareText(priorLabel, entry.sourceLabel) < 0, "governed geography registry order differs");
    priorLabel = entry.sourceLabel;
    assert(sha256(entry.sourceLabel) === entry.sourceLabelSha256, "geography source label hash differs");
    assertText(entry.displayLabel, "geography display label");
    assert(["country", "territory", "subnational", "broad_region", "transnational", "historical", "unresolved", "other"].includes(entry.geographyClass), "geography class is invalid");
    assert(["mapped", "aggregate_only", "unmapped"].includes(entry.mappingState), "geography mapping state is invalid");
    assertCount(entry.sourceAssignmentCount, "geography assignment count");
    assert(entry.sourceAssignmentCount > 0, "governed geography has no assignments");
    assert(Array.isArray(entry.geometryIds) && Array.isArray(entry.geometryTargets), "geography targets are invalid");
    assert(new Set(entry.geometryIds).size === entry.geometryIds.length, "duplicate geography geometry ID");
    assert(entry.geometryTargets.length === entry.geometryIds.length, "geography target count differs");
    for (let index = 0; index < entry.geometryIds.length; index += 1) {
      const geometryId = entry.geometryIds[index];
      const target = entry.geometryTargets[index];
      assertText(geometryId, "geometry ID");
      assert(target.geometryArtifactId === geometryManifest.geometryArtifactId, "geography target artifact differs");
      assert(target.geometryId === geometryId, "geography target ID differs");
      assert(target.matchField === "admin0A3" && target.matchValue === geometryId, "geography target match differs");
    }
    if (entry.mappingState === "mapped") {
      mapped += 1;
      assert(entry.mapEligible === true && entry.geometryIds.length > 0, "mapped geography lacks governed geometry");
      assert(entry.qualification === null || entry.qualification.trim().length > 0, "mapped qualification is invalid");
    } else {
      if (entry.mappingState === "aggregate_only") aggregateOnly += 1;
      else unmapped += 1;
      assert(entry.mapEligible === false && entry.geometryIds.length === 0, "non-mapped geography gained geometry");
      assertText(entry.qualification, "non-mapped qualification");
    }
    assert(entry.aggregateEligible === true, "governed geography aggregate eligibility differs");
    assertText(entry.mappingDecision, "geography mapping decision");
    assertText(entry.representativePointPolicy, "geography point policy");
    assertText(entry.decisionRationale, "geography decision rationale");
    assert(entry.reviewStatus === "REVIEWED_EXPLICIT", "geography review state differs");
    assert(!byId.has(entry.geographyId), "duplicate governed geography ID");
    byId.set(entry.geographyId, entry);
    assignments += entry.sourceAssignmentCount;
  }
  assert(sameCanonical(document.counts, {
    registryEntries: EXPECTED_GEOGRAPHIES,
    mappedEntries: mapped,
    aggregateOnlyEntries: aggregateOnly,
    unmappedEntries: unmapped,
    heldEntries: 0,
    sourceAssignments: assignments,
    sourceObjectCoverage: EXPECTED_PUBLIC_RECORDS,
  }), "geography registry census differs");
  assert(manifest.counts.governedGeographyEntries === byId.size, "manifest geography count differs");
  assert(manifest.counts.mappedGeographyEntries === mapped, "manifest mapped geography count differs");
  assert(manifest.counts.aggregateOnlyGeographyEntries === aggregateOnly, "manifest aggregate-only geography count differs");
  assert(manifest.counts.unmappedGeographyEntries === unmapped, "manifest unmapped geography count differs");
  assert(manifest.counts.regionAssignments === assignments, "manifest geography assignment count differs");
  return byId;
}

function validateTimeBuckets(
  document: ArtifactTimeBuckets,
  manifest: ArtifactManifest,
): ReadonlyMap<string, PublicSpacetimePeriod> {
  assertCoreDocument(document, "time buckets");
  assert(document.format === TIME_BUCKETS_FORMAT, "time bucket format differs");
  assert(document.temporalRole === TEMPORAL_ROLE, "time bucket role differs");
  assert(document.temporalPolicyVersion === TRACE_SPACETIME_TEMPORAL_POLICY_VERSION, "time bucket policy differs");
  assert(document.bucketPolicy === TRACE_SPACETIME_TIME_BUCKET_POLICY, "time bucket kind differs");
  assert(document.rangeMembershipPolicy === TRACE_SPACETIME_RANGE_MEMBERSHIP_POLICY, "time bucket membership differs");
  assert(Array.isArray(document.periods) && document.periods.length === EXPECTED_PERIODS, "time bucket count differs");
  const byId = new Map<string, PublicSpacetimePeriod>();
  let priorStart = Number.NEGATIVE_INFINITY;
  for (const period of document.periods) {
    assert(PERIOD_ID_PATTERN.test(period.periodId), "period ID is invalid");
    assertText(period.label, "period label");
    assert(Number.isSafeInteger(period.startYearInclusive) && Number.isSafeInteger(period.endYearExclusive), "period extent is invalid");
    assert(period.startYearInclusive === priorStart + 10 || priorStart === Number.NEGATIVE_INFINITY, "period sequence has a gap");
    assert(period.endYearExclusive === period.startYearInclusive + 10, "period width differs");
    priorStart = period.startYearInclusive;
    assert(period.membershipPolicy === TRACE_SPACETIME_RANGE_MEMBERSHIP_POLICY, "period membership differs");
    assertCount(period.recordCount, "period record count");
    assertCount(period.mappedRecordCount, "period mapped count");
    assertCount(period.unmappedRecordCount, "period unmapped count");
    assert(period.mappedRecordCount + period.unmappedRecordCount === period.recordCount, "period partition differs");
    assertPrecision(period.precisionBreakdown, period.recordCount, "period precision");
    assert(!byId.has(period.periodId), "duplicate period ID");
    byId.set(period.periodId, freezePeriod(period));
  }
  assert(byId.has(document.defaultPeriodId), "default period did not resolve");
  const derivedDefault = [...byId.values()]
    .sort((left, right) => right.recordCount - left.recordCount || left.startYearInclusive - right.startYearInclusive)[0];
  assert(derivedDefault?.periodId === document.defaultPeriodId, "default period policy differs");
  assert(manifest.defaultPeriodId === document.defaultPeriodId, "manifest default period differs");
  assert(manifest.counts.timeBuckets === byId.size, "manifest period count differs");
  assert(manifest.counts.earliestGovernedYear === document.periods[0].startYearInclusive, "earliest governed year differs");
  assert(manifest.counts.latestGovernedYear < document.periods[document.periods.length - 1].endYearExclusive, "latest governed year is outside period registry");
  return byId;
}

function validateRecordIndex(
  document: ArtifactRecordIndex,
  manifest: ArtifactManifest,
  geographyById: ReadonlyMap<string, ArtifactGeography>,
  periodById: ReadonlyMap<string, PublicSpacetimePeriod>,
): ReadonlyMap<string, readonly ArtifactRecord[]> {
  assertCoreDocument(document, "record index");
  assert(document.format === RECORD_INDEX_FORMAT, "record index format differs");
  assert(document.serverOnly === true, "record index server boundary differs");
  assert(document.geographyRole === GEOGRAPHY_ROLE && document.temporalRole === TEMPORAL_ROLE, "record index roles differ");
  assert(document.geographyPolicyVersion === TRACE_SPACETIME_GEOGRAPHY_POLICY_VERSION, "record geography policy differs");
  assert(document.temporalPolicyVersion === TRACE_SPACETIME_TEMPORAL_POLICY_VERSION, "record temporal policy differs");
  assert(document.rangeMembershipPolicy === TRACE_SPACETIME_RANGE_MEMBERSHIP_POLICY, "record membership policy differs");
  assert(document.records.length === EXPECTED_PUBLIC_RECORDS, "record index count differs");
  const lookup = new Map<string, ArtifactRecord[]>();
  const objectIds = new Set<string>();
  const assignmentCounts = new Map<string, number>();
  const precisionCounts: MutablePrecision = { day: 0, month: 0, year: 0, range: 0, approximate: 0, unknown: 0 };
  let mappedObjects = 0;
  let aggregateOnlyObjects = 0;
  let unmappedObjects = 0;
  let priorId = "";
  for (const record of document.records) {
    assert(PUBLIC_STABLE_ID_PATTERN.test(record.objectId), "record public stable ID is invalid");
    assert(compareText(priorId, record.objectId) < 0, "record index order differs");
    priorId = record.objectId;
    assert(!objectIds.has(record.objectId), "duplicate record public stable ID");
    objectIds.add(record.objectId);
    assertText(record.title, "record title");
    assert(record.geographyIds.length > 0, "record geography is missing");
    assert(record.recordedRegionDisplays.length === record.geographyIds.length, "record geography display count differs");
    assert(new Set(record.geographyIds).size === record.geographyIds.length, "record has duplicate geography assignments");
    assertText(record.rawRegionDisplay, "raw region diagnostic");
    const states = record.geographyIds.map((geographyId, index) => {
      const geography = geographyById.get(geographyId);
      assert(geography, "record geography did not resolve");
      assert(record.recordedRegionDisplays[index] === geography.sourceLabel, "record geography display differs");
      assignmentCounts.set(geographyId, (assignmentCounts.get(geographyId) ?? 0) + 1);
      return geography.mappingState;
    });
    if (states.includes("mapped")) mappedObjects += 1;
    else if (states.every((state) => state === "aggregate_only")) aggregateOnlyObjects += 1;
    else if (states.every((state) => state === "unmapped")) unmappedObjects += 1;
    else assert(false, "record has an unsupported mixed non-map state");
    assert(TIME_OBSERVATION_ID_PATTERN.test(record.time.observationId), "time observation ID is invalid");
    assert(record.time.role === "recorded_context", "record time role differs");
    assertText(record.time.sourceDisplay, "record time source display");
    assert(Number.isSafeInteger(record.time.startYearInclusive) && Number.isSafeInteger(record.time.endYearInclusive), "record time extent is invalid");
    assert(record.time.endYearInclusive >= record.time.startYearInclusive, "record time extent is reversed");
    assert(["day", "month", "year", "range", "approximate", "unknown"].includes(record.time.precision), "record precision is invalid");
    assertText(record.time.derivationMethod, "record time derivation");
    precisionCounts[record.time.precision] += 1;
    const expectedPeriodIds = [...periodById.values()]
      .filter((period) => record.time.startYearInclusive < period.endYearExclusive && record.time.endYearInclusive >= period.startYearInclusive)
      .map((period) => period.periodId);
    assert(sameCanonical(record.periodIds, expectedPeriodIds), "record period membership differs");
    for (const periodId of record.periodIds) {
      for (const geographyId of record.geographyIds) {
        const key = lookupKey(periodId, geographyId);
        const records = lookup.get(key) ?? [];
        records.push(record);
        lookup.set(key, records);
      }
    }
  }
  for (const geography of geographyById.values()) {
    assert(assignmentCounts.get(geography.geographyId) === geography.sourceAssignmentCount, "geography assignment census differs");
  }
  assert(sameCanonical(document.counts, {
    records: EXPECTED_PUBLIC_RECORDS,
    mappedObjects,
    aggregateOnlyObjects,
    unmappedObjects,
    heldObjects: EXPECTED_HELD_RECORDS,
    precision: precisionCounts,
  }), "record index census differs");
  assert(manifest.counts.publicObjects === objectIds.size, "manifest public object count differs");
  assert(manifest.counts.heldObjects === EXPECTED_HELD_RECORDS, "manifest held count differs");
  assert(manifest.counts.regionObjectCoverage === objectIds.size, "manifest region coverage differs");
  assert(manifest.counts.temporalObjectCoverage === objectIds.size, "manifest temporal coverage differs");
  assert(manifest.counts.mappedObjects === mappedObjects, "manifest mapped object count differs");
  assert(manifest.counts.aggregateOnlyObjects === aggregateOnlyObjects, "manifest aggregate-only object count differs");
  assert(manifest.counts.unmappedObjects === unmappedObjects, "manifest unmapped object count differs");
  assert(sameCanonical(manifest.counts.temporalPrecision, precisionCounts), "manifest temporal precision differs");
  return new Map([...lookup].map(([key, records]) => [key, Object.freeze(records)]));
}

function validatePeriodAggregates(
  document: ArtifactPeriodAggregates,
  manifest: ArtifactManifest,
  geographyById: ReadonlyMap<string, ArtifactGeography>,
  periodById: ReadonlyMap<string, PublicSpacetimePeriod>,
  recordsByPeriodGeography: ReadonlyMap<string, readonly ArtifactRecord[]>,
): ReadonlyMap<string, ArtifactPeriodAggregate> {
  assertCoreDocument(document, "period aggregates");
  assert(document.format === PERIOD_AGGREGATES_FORMAT, "period aggregate format differs");
  assert(document.geographyPolicyVersion === TRACE_SPACETIME_GEOGRAPHY_POLICY_VERSION, "aggregate geography policy differs");
  assert(document.temporalPolicyVersion === TRACE_SPACETIME_TEMPORAL_POLICY_VERSION, "aggregate temporal policy differs");
  assert(document.bucketPolicy === TRACE_SPACETIME_TIME_BUCKET_POLICY, "aggregate bucket policy differs");
  assert(document.rangeMembershipPolicy === TRACE_SPACETIME_RANGE_MEMBERSHIP_POLICY, "aggregate membership policy differs");
  assert(document.periodCount === EXPECTED_PERIODS && document.periods.length === EXPECTED_PERIODS, "aggregate period count differs");
  const byId = new Map<string, ArtifactPeriodAggregate>();
  let cellCount = 0;
  for (const aggregate of document.periods) {
    const period = periodById.get(aggregate.periodId);
    assert(period, "aggregate period did not resolve");
    assert(aggregate.denominator === period.recordCount, "aggregate denominator differs");
    assert(aggregate.mappedRecordCount === period.mappedRecordCount, "aggregate mapped count differs");
    assert(aggregate.unmappedRecordCount === period.unmappedRecordCount, "aggregate unmapped count differs");
    let assignmentCount = 0;
    let priorGeographyId = "";
    const seen = new Set<string>();
    for (const cell of aggregate.cells) {
      assert(GEOGRAPHY_ID_PATTERN.test(cell.geographyId), "aggregate geography ID is invalid");
      assert(compareText(priorGeographyId, cell.geographyId) < 0, "aggregate cell order differs");
      priorGeographyId = cell.geographyId;
      assert(!seen.has(cell.geographyId), "duplicate aggregate geography cell");
      seen.add(cell.geographyId);
      const geography = geographyById.get(cell.geographyId);
      assert(geography, "aggregate geography did not resolve");
      assert(cell.mappingState === geography.mappingState, "aggregate mapping state differs");
      assert(cell.denominator === period.recordCount, "cell denominator differs");
      const expectedRecords = recordsByPeriodGeography.get(lookupKey(period.periodId, cell.geographyId)) ?? [];
      assert(cell.recordCount === expectedRecords.length && cell.recordCount > 0, "cell record count differs");
      assert(cell.unmappedCount === (cell.mappingState === "mapped" ? 0 : cell.recordCount), "cell unmapped count differs");
      const precision: MutablePrecision = { day: 0, month: 0, year: 0, range: 0, approximate: 0, unknown: 0 };
      for (const record of expectedRecords) precision[record.time.precision] += 1;
      assert(sameCanonical(cell.precisionBreakdown, precision), "cell precision breakdown differs");
      assignmentCount += cell.recordCount;
      cellCount += 1;
    }
    assert(assignmentCount === aggregate.geographyAssignmentCount, "aggregate assignment count differs");
    assert(!byId.has(aggregate.periodId), "duplicate aggregate period");
    byId.set(aggregate.periodId, aggregate);
  }
  assert(byId.size === periodById.size, "aggregate period coverage differs");
  assert(cellCount === manifest.counts.periodRegionCells, "manifest aggregate cell count differs");
  return byId;
}

function buildGeometryReference(
  geometryManifest: ArtifactGeometryManifest,
): PublicSpacetimeGeometryReference {
  return Object.freeze({
    geometryArtifactId: geometryManifest.geometryArtifactId,
    source: "Natural Earth",
    sourceVersion: geometryManifest.sourceVersion,
    sourceScale: geometryManifest.sourceScale,
    assetPath: geometryManifest.publicAssetPath,
    assetSha256: geometryManifest.outputSha256,
    featureCount: geometryManifest.featureCount,
    boundaryPolicy: geometryManifest.boundaryPolicy,
  });
}

function buildIndex(): GovernedSpacetimeIndex {
  indexBuildAttempts += 1;
  const started = performance.now();
  const manifest = manifestJson as unknown as ArtifactManifest;
  const policy = governancePolicyJson as unknown as ArtifactGovernancePolicy;
  const geography = geographyRegistryJson as unknown as ArtifactGeographyRegistry;
  const timeBuckets = timeBucketsJson as unknown as ArtifactTimeBuckets;
  const aggregates = periodRegionAggregatesJson as unknown as ArtifactPeriodAggregates;
  const records = recordIndexJson as unknown as ArtifactRecordIndex;
  const geometryManifest = geometryManifestJson as unknown as ArtifactGeometryManifest;
  const payloads = Object.freeze({
    "geography-registry.json": geography,
    "governance-policy.json": policy,
    "period-region-aggregates.json": aggregates,
    "record-index.json": records,
    "time-buckets.json": timeBuckets,
  });

  const payloadStarted = performance.now();
  validatePayloadBindings(manifest, geometryManifest, payloads);
  assertCoreDocument(policy, "governance policy");
  assert(policy.format === GOVERNANCE_POLICY_FORMAT, "governance policy format differs");
  assert(policy.geographyPolicyVersion === TRACE_SPACETIME_GEOGRAPHY_POLICY_VERSION, "governance geography policy differs");
  assert(policy.temporalPolicyVersion === TRACE_SPACETIME_TEMPORAL_POLICY_VERSION, "governance temporal policy differs");
  assert(policy.geographyRole.role === GEOGRAPHY_ROLE && policy.temporalRole.role === TEMPORAL_ROLE, "governance roles differ");
  assert(policy.heldBoundary.heldObjectCount === EXPECTED_HELD_RECORDS && policy.heldBoundary.heldObjectsProjected === 0, "held boundary differs");
  assert(Array.isArray(policy.invariants) && policy.invariants.length === 20, "Spacetime invariant register differs");
  const payloadVerificationMs = performance.now() - payloadStarted;

  const registryStarted = performance.now();
  const geographyById = validateGeographyRegistry(geography, manifest, geometryManifest);
  const periodById = validateTimeBuckets(timeBuckets, manifest);
  const registryValidationMs = performance.now() - registryStarted;

  const recordsStarted = performance.now();
  const recordsByPeriodGeography = validateRecordIndex(
    records,
    manifest,
    geographyById,
    periodById,
  );
  const recordIndexConstructionMs = performance.now() - recordsStarted;

  const aggregatesStarted = performance.now();
  const aggregateByPeriodId = validatePeriodAggregates(
    aggregates,
    manifest,
    geographyById,
    periodById,
    recordsByPeriodGeography,
  );
  const aggregateValidationMs = performance.now() - aggregatesStarted;

  const publicStarted = performance.now();
  const geometry = buildGeometryReference(geometryManifest);
  const release = Object.freeze({
    researchReleaseId: SOURCE_RELEASE.researchReleaseId,
    researchManifestSha256: SOURCE_RELEASE.researchManifestSha256,
    spacetimeProjectionId: TRACE_SPACETIME_PUBLIC_PROJECTION_ID,
    spacetimeProjectionSha256: manifest.projectionSha256,
  });
  const periodsDataset: PublicSpacetimePeriodsDataset = Object.freeze({
    schemaVersion: TRACE_SPACETIME_PUBLIC_SCHEMA_VERSION,
    release,
    temporalRole: TEMPORAL_ROLE,
    temporalPolicyVersion: TRACE_SPACETIME_TEMPORAL_POLICY_VERSION,
    bucketPolicy: TRACE_SPACETIME_TIME_BUCKET_POLICY,
    rangeMembershipPolicy: TRACE_SPACETIME_RANGE_MEMBERSHIP_POLICY,
    defaultPeriodId: timeBuckets.defaultPeriodId,
    periods: Object.freeze([...periodById.values()]),
    geometry,
  });
  const publicText = JSON.stringify(periodsDataset);
  assert(!UUID_PATTERN.test(publicText) && !PRIVATE_FOLDER_PATTERN.test(publicText), "private identity entered public Spacetime periods");
  // The JSON modules are private, but freeze them after validation so every
  // lookup reuses one process-local immutable projection snapshot.
  for (const document of [manifest, policy, geography, timeBuckets, aggregates, records, geometryManifest]) {
    deepFreeze(document);
  }
  const publicProjectionConstructionMs = performance.now() - publicStarted;
  successfulIndexBuilds += 1;
  lastSuccessfulBuildTiming = Object.freeze({
    payloadVerificationMs,
    registryValidationMs,
    recordIndexConstructionMs,
    aggregateValidationMs,
    publicProjectionConstructionMs,
    totalMs: performance.now() - started,
  });

  return Object.freeze({
    manifest,
    periodsDataset,
    periodById,
    aggregateByPeriodId,
    geographyById,
    recordsByPeriodGeography,
    geometry,
    info: Object.freeze({
      projectionId: TRACE_SPACETIME_PUBLIC_PROJECTION_ID,
      projectionSha256: manifest.projectionSha256,
      researchReleaseId: SOURCE_RELEASE.researchReleaseId,
      researchManifestSha256: SOURCE_RELEASE.researchManifestSha256,
      recordCount: manifest.counts.publicObjects,
      geographyCount: manifest.counts.governedGeographyEntries,
      periodCount: manifest.counts.timeBuckets,
      periodRegionCellCount: manifest.counts.periodRegionCells,
      heldExcluded: manifest.counts.heldObjects,
    }),
  });
}

function getIndex(): GovernedSpacetimeIndex {
  if (!cachedIndex) cachedIndex = buildIndex();
  return cachedIndex;
}

function mappingInterpretation(geography: ArtifactGeography): string {
  if (geography.mappingState === "mapped") {
    return geography.qualification
      ?? "Mapped to governed aggregate geometry; the mark is not an exact object coordinate.";
  }
  return geography.qualification
    ?? "Retained in governed counts without an invented map position.";
}

function projectMappedGeography(
  geography: ArtifactGeography,
  cell: ArtifactAggregateCell,
): PublicSpacetimeMappedGeography {
  assert(geography.mappingState === "mapped", "mapped geography projection state differs");
  return Object.freeze({
    geographyId: geography.geographyId,
    label: geography.displayLabel,
    geographyClass: geography.geographyClass,
    mappingState: "mapped",
    geometryIds: Object.freeze([...geography.geometryIds]),
    recordCount: cell.recordCount,
    denominator: cell.denominator,
    precisionBreakdown: freezePrecision(cell.precisionBreakdown),
    qualification: geography.qualification,
    historicalStatus: geography.historicalStatus,
    transnational: geography.transnational,
    broadRegion: geography.broadRegion,
  });
}

function projectNonMappedGeography(
  geography: ArtifactGeography,
  cell: ArtifactAggregateCell,
): PublicSpacetimeNonMappedGeography {
  assert(geography.mappingState !== "mapped", "non-mapped geography projection state differs");
  assertText(geography.qualification, "non-mapped public qualification");
  return Object.freeze({
    geographyId: geography.geographyId,
    label: geography.displayLabel,
    geographyClass: geography.geographyClass,
    mappingState: geography.mappingState,
    recordCount: cell.recordCount,
    denominator: cell.denominator,
    precisionBreakdown: freezePrecision(cell.precisionBreakdown),
    qualification: geography.qualification,
    historicalStatus: geography.historicalStatus,
    transnational: geography.transnational,
    broadRegion: geography.broadRegion,
  });
}

function projectAccessibleRow(
  periodId: string,
  geography: ArtifactGeography,
  cell: ArtifactAggregateCell,
): PublicSpacetimeAccessibleGeographyRow {
  return Object.freeze({
    id: `spacetime:${periodId}:${geography.geographyId}`,
    geographyId: geography.geographyId,
    label: geography.displayLabel,
    mappingState: geography.mappingState,
    recordCount: cell.recordCount,
    denominator: cell.denominator,
    precisionBreakdown: freezePrecision(cell.precisionBreakdown),
    interpretation: mappingInterpretation(geography),
  });
}

function projectAtlas(
  index: GovernedSpacetimeIndex,
  period: PublicSpacetimePeriod,
  aggregate: ArtifactPeriodAggregate,
): PublicSpacetimeAtlasDataset {
  const projected = aggregate.cells.map((cell) => {
    const geography = index.geographyById.get(cell.geographyId);
    assert(geography, "selected atlas geography did not resolve");
    return { geography, cell };
  });
  const mappedGeographies = Object.freeze(projected
    .filter(({ geography }) => geography.mappingState === "mapped")
    .map(({ geography, cell }) => projectMappedGeography(geography, cell))
    .sort((left, right) => right.recordCount - left.recordCount || compareText(left.label, right.label)));
  const aggregateOnlyGeographies = Object.freeze(projected
    .filter(({ geography }) => geography.mappingState === "aggregate_only")
    .map(({ geography, cell }) => projectNonMappedGeography(geography, cell))
    .sort((left, right) => right.recordCount - left.recordCount || compareText(left.label, right.label)));
  const unmappedGeographies = Object.freeze(projected
    .filter(({ geography }) => geography.mappingState === "unmapped")
    .map(({ geography, cell }) => projectNonMappedGeography(geography, cell))
    .sort((left, right) => right.recordCount - left.recordCount || compareText(left.label, right.label)));
  const accessibleRows = Object.freeze(projected
    .map(({ geography, cell }) => projectAccessibleRow(period.periodId, geography, cell))
    .sort((left, right) => right.recordCount - left.recordCount || compareText(left.label, right.label)));
  const atlas: PublicSpacetimeAtlasDataset = Object.freeze({
    schemaVersion: TRACE_SPACETIME_PUBLIC_SCHEMA_VERSION,
    release: index.periodsDataset.release,
    geographyRole: GEOGRAPHY_ROLE,
    temporalRole: TEMPORAL_ROLE,
    geographyPolicyVersion: TRACE_SPACETIME_GEOGRAPHY_POLICY_VERSION,
    temporalPolicyVersion: TRACE_SPACETIME_TEMPORAL_POLICY_VERSION,
    selectedPeriod: period,
    counts: Object.freeze({
      denominator: aggregate.denominator,
      mappedRecords: aggregate.mappedRecordCount,
      unmappedRecords: aggregate.unmappedRecordCount,
      geographyAssignments: aggregate.geographyAssignmentCount,
      heldExcluded: EXPECTED_HELD_RECORDS,
    }),
    mappedGeographies,
    aggregateOnlyGeographies,
    unmappedGeographies,
    accessibleRows,
    dotPolicy: Object.freeze({
      semanticKind: "aggregate_density_mark",
      policyVersion: DOT_POLICY_VERSION,
      dotUnit: DOT_UNIT,
      positionClaim: "aggregate_only",
    }),
    geometry: index.geometry,
    realSemanticEdgeCount: 0,
  });
  const publicText = JSON.stringify(atlas);
  assert(!UUID_PATTERN.test(publicText) && !PRIVATE_FOLDER_PATTERN.test(publicText), "private identity entered public Spacetime atlas");
  return atlas;
}

interface CursorPayload {
  readonly version: "trace-spacetime-record-cursor/v1";
  readonly projectionSha256: string;
  readonly periodId: string;
  readonly geographyId: string;
  readonly offset: number;
}

function encodeCursor(payload: CursorPayload): string {
  return Buffer.from(JSON.stringify(payload), "utf8").toString("base64url");
}

function decodeCursor(
  value: string,
  projectionSha256: string,
  periodId: string,
  geographyId: string,
  totalCount: number,
): number | null {
  try {
    const parsed = JSON.parse(Buffer.from(value, "base64url").toString("utf8")) as Partial<CursorPayload>;
    if (
      Object.keys(parsed).sort(compareText).join(",") !== "geographyId,offset,periodId,projectionSha256,version"
      || parsed.version !== "trace-spacetime-record-cursor/v1"
      || parsed.projectionSha256 !== projectionSha256
      || parsed.periodId !== periodId
      || parsed.geographyId !== geographyId
      || !Number.isSafeInteger(parsed.offset)
      || Number(parsed.offset) <= 0
      || Number(parsed.offset) >= totalCount
    ) return null;
    return Number(parsed.offset);
  } catch {
    return null;
  }
}

function projectRecordSummary(record: ArtifactRecord): PublicSpacetimeRecordSummary {
  return Object.freeze({
    stableId: record.objectId,
    title: record.title,
    geographyIds: Object.freeze([...record.geographyIds]),
    recordedRegionDisplays: Object.freeze([...record.recordedRegionDisplays]),
    time: Object.freeze({
      role: "recorded_context",
      sourceDisplay: record.time.sourceDisplay,
      startYearInclusive: record.time.startYearInclusive,
      endYearInclusive: record.time.endYearInclusive,
      precision: record.time.precision,
      derivationMethod: record.time.derivationMethod,
    }),
  });
}

export function resetGovernedSpacetimeReaderForTests(): void {
  cachedIndex = null;
  indexBuildAttempts = 0;
  successfulIndexBuilds = 0;
  lastSuccessfulBuildTiming = null;
}

/** Test/rehearsal diagnostics only; this does not initialize the projection. */
export function getGovernedSpacetimeReaderRuntimeDiagnosticsForTests(): GovernedSpacetimeReaderRuntimeDiagnostics {
  return Object.freeze({
    indexInitialized: cachedIndex !== null,
    indexBuildAttempts,
    successfulIndexBuilds,
    lastSuccessfulBuildTiming,
  });
}

export function getGovernedSpacetimeProjectionInfo(): GovernedSpacetimeProjectionInfo {
  return getIndex().info;
}

export function getGovernedSpacetimePeriodsDataset(): PublicSpacetimePeriodsDataset {
  return getIndex().periodsDataset;
}

export function lookupGovernedSpacetimeAtlas(
  periodId: string,
): GovernedSpacetimeLookup<PublicSpacetimeAtlasDataset> {
  if (typeof periodId !== "string" || periodId.length > 80 || !PERIOD_ID_PATTERN.test(periodId)) {
    return Object.freeze({
      ok: false as const,
      code: "INVALID_ARGUMENT" as const,
      message: "The Spacetime period ID is invalid.",
    });
  }
  let index: GovernedSpacetimeIndex;
  try {
    index = getIndex();
  } catch {
    return Object.freeze({
      ok: false as const,
      code: "INTEGRITY_FAILURE" as const,
      message: "The governed Spacetime projection failed its integrity contract.",
    });
  }
  const period = index.periodById.get(periodId);
  const aggregate = index.aggregateByPeriodId.get(periodId);
  if (!period || !aggregate) return Object.freeze({
    ok: false as const,
    code: "NOT_FOUND" as const,
    message: "The requested Spacetime period is not available in this release.",
  });
  try {
    return Object.freeze({ ok: true as const, data: projectAtlas(index, period, aggregate) });
  } catch {
    return Object.freeze({
      ok: false as const,
      code: "INTEGRITY_FAILURE" as const,
      message: "The selected Spacetime atlas failed its integrity contract.",
    });
  }
}

export function lookupGovernedSpacetimeGeographyRecords(
  geographyId: string,
  input: Readonly<{ periodId: string; first?: number; after?: string }>,
): GovernedSpacetimeRecordLookup {
  if (typeof geographyId !== "string" || geographyId.length > 96 || !GEOGRAPHY_ID_PATTERN.test(geographyId)) {
    return Object.freeze({
      ok: false as const,
      code: "INVALID_ARGUMENT" as const,
      message: "The Spacetime geography ID is invalid.",
    });
  }
  if (typeof input.periodId !== "string" || input.periodId.length > 80 || !PERIOD_ID_PATTERN.test(input.periodId)) {
    return Object.freeze({
      ok: false as const,
      code: "INVALID_ARGUMENT" as const,
      message: "The Spacetime period ID is invalid.",
    });
  }
  const first = input.first ?? DEFAULT_PAGE_SIZE;
  if (!Number.isSafeInteger(first) || first < 1 || first > MAX_PAGE_SIZE) {
    return Object.freeze({
      ok: false as const,
      code: "INVALID_ARGUMENT" as const,
      message: `first must be an integer from 1 through ${MAX_PAGE_SIZE}.`,
    });
  }
  let index: GovernedSpacetimeIndex;
  try {
    index = getIndex();
  } catch {
    return Object.freeze({
      ok: false as const,
      code: "INTEGRITY_FAILURE" as const,
      message: "The governed Spacetime projection failed its integrity contract.",
    });
  }
  const geography = index.geographyById.get(geographyId);
  const period = index.periodById.get(input.periodId);
  if (!geography || !period) return Object.freeze({
    ok: false as const,
    code: "NOT_FOUND" as const,
    message: "The requested Spacetime geography or period is not available in this release.",
  });
  const matching = index.recordsByPeriodGeography.get(lookupKey(period.periodId, geography.geographyId)) ?? [];
  const offset = input.after === undefined
    ? 0
    : decodeCursor(
      input.after,
      index.info.projectionSha256,
      period.periodId,
      geography.geographyId,
      matching.length,
    );
  if (offset === null) return Object.freeze({
    ok: false as const,
    code: "INVALID_CURSOR" as const,
    message: "The Spacetime records cursor is invalid for this projection, period, or geography.",
  });
  const nodes = Object.freeze(matching.slice(offset, offset + first).map(projectRecordSummary));
  const nextOffset = offset + nodes.length;
  const hasNextPage = nextOffset < matching.length;
  const endCursor = hasNextPage
    ? encodeCursor(Object.freeze({
      version: "trace-spacetime-record-cursor/v1",
      projectionSha256: index.info.projectionSha256,
      periodId: period.periodId,
      geographyId: geography.geographyId,
      offset: nextOffset,
    }))
    : null;
  const page: PublicSpacetimeRecordPage = Object.freeze({
    schemaVersion: TRACE_SPACETIME_PUBLIC_SCHEMA_VERSION,
    release: index.periodsDataset.release,
    period,
    geography: Object.freeze({
      geographyId: geography.geographyId,
      label: geography.displayLabel,
      mappingState: geography.mappingState,
    }),
    nodes,
    pageInfo: Object.freeze({ hasNextPage, endCursor }),
    totalCount: matching.length,
  });
  const publicText = JSON.stringify(page);
  if (UUID_PATTERN.test(publicText) || PRIVATE_FOLDER_PATTERN.test(publicText)) return Object.freeze({
    ok: false as const,
    code: "INTEGRITY_FAILURE" as const,
    message: "The selected Spacetime records page failed its public-boundary contract.",
  });
  return Object.freeze({ ok: true as const, data: page });
}
