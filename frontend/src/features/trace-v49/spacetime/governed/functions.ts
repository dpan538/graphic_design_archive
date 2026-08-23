import {
  TRACE_SPACETIME_RANGE_MEMBERSHIP_POLICY,
  type PublicSpacetimeMappingState,
  type PublicSpacetimePrecisionBreakdown,
  type PublicSpacetimeTimePrecision,
} from "./types";

export const SPACETIME_TEMPORAL_DERIVATION_METHOD =
  "FROZEN_YEAR_EXTENT_AND_LEXICAL_PRECISION_V1" as const;
const MONTH_NAME = "(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)";
const NATURAL_DAY_RE = new RegExp(`^(?:\\d{1,2}[\\/-]\\d{1,2}[\\/-]\\d{4}|\\d{1,2}\\s+${MONTH_NAME}\\s+\\d{4}|${MONTH_NAME}\\s+\\d{1,2},\\s*\\d{4})$`, "iu");
const NATURAL_MONTH_RE = new RegExp(`^(?:${MONTH_NAME}\\s+\\d{4}|\\d{1,2}[\\/-]\\d{4})$`, "iu");

export interface GovernedTemporalCandidateInput {
  readonly sourceDisplay: string;
  readonly startYearInclusive: number;
  readonly endYearInclusive?: number | null;
}

export interface GovernedTemporalExtent {
  readonly sourceDisplay: string;
  readonly startYearInclusive: number;
  readonly endYearInclusive: number;
  readonly precision: PublicSpacetimeTimePrecision;
  readonly derivationMethod: typeof SPACETIME_TEMPORAL_DERIVATION_METHOD;
}

export interface GovernedTimeBucket {
  readonly periodId: string;
  readonly label: string;
  readonly startYearInclusive: number;
  readonly endYearExclusive: number;
  readonly membershipPolicy: typeof TRACE_SPACETIME_RANGE_MEMBERSHIP_POLICY;
}

export interface GovernedSpacetimeFunctionRecord {
  readonly stableId: string;
  readonly geographyIds: readonly string[];
  readonly time: GovernedTemporalExtent;
}

export interface GovernedSpacetimeFunctionGeography {
  readonly geographyId: string;
  readonly label: string;
  readonly mappingState: PublicSpacetimeMappingState;
  readonly geometryIds: readonly string[];
}

export interface GovernedPeriodCounts {
  readonly periodId: string;
  readonly denominator: number;
  readonly mappedRecordCount: number;
  readonly unmappedRecordCount: number;
  readonly precisionBreakdown: PublicSpacetimePrecisionBreakdown;
}

export interface GovernedGeographyAggregate {
  readonly geographyId: string;
  readonly recordCount: number;
  readonly denominator: number;
  readonly mappingState: PublicSpacetimeMappingState;
  readonly geometryIds: readonly string[];
  readonly precisionBreakdown: PublicSpacetimePrecisionBreakdown;
}

export interface GovernedSpacetimeMapMark extends GovernedGeographyAggregate {
  readonly semanticKind: "aggregate_region_mark";
  readonly positionClaim: "aggregate_only";
}

export interface GovernedSpacetimeMapViewModel {
  readonly period: GovernedTimeBucket;
  readonly counts: GovernedPeriodCounts;
  readonly mappedMarks: readonly GovernedSpacetimeMapMark[];
  readonly aggregateOnly: readonly GovernedGeographyAggregate[];
  readonly unmapped: readonly GovernedGeographyAggregate[];
  readonly accessibleRows: readonly Readonly<{
    geographyId: string;
    label: string;
    mappingState: PublicSpacetimeMappingState;
    recordCount: number;
    denominator: number;
  }>[];
}

export function governTemporalCandidate(
  input: GovernedTemporalCandidateInput,
): GovernedTemporalExtent {
  const extent = deriveTemporalExtent(input);
  return Object.freeze({
    ...extent,
    precision: classifyTemporalPrecision(
      extent.sourceDisplay,
      extent.startYearInclusive,
      input.endYearInclusive ?? null,
    ),
    derivationMethod: SPACETIME_TEMPORAL_DERIVATION_METHOD,
  });
}

export function deriveTemporalExtent(
  input: GovernedTemporalCandidateInput,
): Readonly<{
  sourceDisplay: string;
  startYearInclusive: number;
  endYearInclusive: number;
}> {
  const sourceDisplay = input.sourceDisplay.trim();
  const startYearInclusive = input.startYearInclusive;
  const endYearInclusive = input.endYearInclusive ?? startYearInclusive;
  if (!sourceDisplay) throw new Error("recorded temporal display is required");
  if (!Number.isSafeInteger(startYearInclusive) || !Number.isSafeInteger(endYearInclusive)) {
    throw new Error("governed temporal extent requires integer years");
  }
  if (endYearInclusive < startYearInclusive) {
    throw new Error("governed temporal extent is reversed");
  }
  return Object.freeze({ sourceDisplay, startYearInclusive, endYearInclusive });
}

export function buildTimeBucketRegistry(
  records: readonly GovernedSpacetimeFunctionRecord[],
): readonly GovernedTimeBucket[] {
  if (records.length === 0) return Object.freeze([]);
  const earliest = Math.min(...records.map((record) => record.time.startYearInclusive));
  const latest = Math.max(...records.map((record) => record.time.endYearInclusive));
  const firstDecade = Math.floor(earliest / 10) * 10;
  const finalDecade = Math.floor(latest / 10) * 10;
  const buckets: GovernedTimeBucket[] = [];
  for (let start = firstDecade; start <= finalDecade; start += 10) {
    buckets.push(Object.freeze({
      periodId: periodId(start, start + 10),
      label: `${start}s`,
      startYearInclusive: start,
      endYearExclusive: start + 10,
      membershipPolicy: TRACE_SPACETIME_RANGE_MEMBERSHIP_POLICY,
    }));
  }
  return Object.freeze(buckets);
}

export function deriveBucketMemberships(
  time: GovernedTemporalExtent,
  buckets: readonly GovernedTimeBucket[],
): readonly string[] {
  return Object.freeze(buckets
    .filter((bucket) => intervalOverlapsBucket(time, bucket))
    .map((bucket) => bucket.periodId));
}

export function selectTimeBucket(
  buckets: readonly GovernedTimeBucket[],
  periodIdValue: string,
): GovernedTimeBucket {
  const bucket = buckets.find((candidate) => candidate.periodId === periodIdValue);
  if (!bucket) throw new Error("unknown governed Spacetime period");
  return bucket;
}

export function filterRecordsByTimeBucket(
  records: readonly GovernedSpacetimeFunctionRecord[],
  bucket: GovernedTimeBucket,
): readonly GovernedSpacetimeFunctionRecord[] {
  return Object.freeze(records.filter((record) => intervalOverlapsBucket(record.time, bucket)));
}

export function deriveTimeBucketCounts(
  records: readonly GovernedSpacetimeFunctionRecord[],
  bucket: GovernedTimeBucket,
  geographies: readonly GovernedSpacetimeFunctionGeography[],
): GovernedPeriodCounts {
  const members = filterRecordsByTimeBucket(records, bucket);
  const geographyById = uniqueGeographies(geographies);
  const mappedRecordCount = members.filter((record) => record.geographyIds.some(
    (geographyId) => geographyById.get(geographyId)?.mappingState === "mapped",
  )).length;
  return Object.freeze({
    periodId: bucket.periodId,
    denominator: members.length,
    mappedRecordCount,
    unmappedRecordCount: members.length - mappedRecordCount,
    precisionBreakdown: precisionBreakdown(members),
  });
}

export function deriveSpacetimePeriodDataset(
  records: readonly GovernedSpacetimeFunctionRecord[],
  bucket: GovernedTimeBucket,
  geographies: readonly GovernedSpacetimeFunctionGeography[],
): Readonly<{
  period: GovernedTimeBucket;
  records: readonly GovernedSpacetimeFunctionRecord[];
  counts: GovernedPeriodCounts;
}> {
  return Object.freeze({
    period: bucket,
    records: filterRecordsByTimeBucket(records, bucket),
    counts: deriveTimeBucketCounts(records, bucket, geographies),
  });
}

export function aggregateSpacetimeByGeography(
  records: readonly GovernedSpacetimeFunctionRecord[],
  bucket: GovernedTimeBucket,
  geographies: readonly GovernedSpacetimeFunctionGeography[],
): readonly GovernedGeographyAggregate[] {
  const members = filterRecordsByTimeBucket(records, bucket);
  const geographyById = uniqueGeographies(geographies);
  const recordsByGeography = new Map<string, GovernedSpacetimeFunctionRecord[]>();
  for (const record of members) {
    for (const geographyId of new Set(record.geographyIds)) {
      if (!geographyById.has(geographyId)) throw new Error("record references unknown governed geography");
      const rows = recordsByGeography.get(geographyId) ?? [];
      rows.push(record);
      recordsByGeography.set(geographyId, rows);
    }
  }
  return Object.freeze([...recordsByGeography]
    .sort(([left], [right]) => compareText(left, right))
    .map(([geographyId, geographyRecords]) => {
      const geography = geographyById.get(geographyId);
      if (!geography) throw new Error("governed geography disappeared during aggregation");
      return Object.freeze({
        geographyId,
        recordCount: geographyRecords.length,
        denominator: members.length,
        mappingState: geography.mappingState,
        geometryIds: Object.freeze([...geography.geometryIds]),
        precisionBreakdown: precisionBreakdown(geographyRecords),
      });
    }));
}

export function deriveSpacetimeMapMarks(
  aggregates: readonly GovernedGeographyAggregate[],
): readonly GovernedSpacetimeMapMark[] {
  return Object.freeze(aggregates
    .filter((aggregate) => aggregate.mappingState === "mapped")
    .map((aggregate) => {
      if (aggregate.geometryIds.length === 0) {
        throw new Error("mapped governed geography has no geometry");
      }
      return Object.freeze({
        ...aggregate,
        semanticKind: "aggregate_region_mark" as const,
        positionClaim: "aggregate_only" as const,
      });
    }));
}

export function deriveSpacetimeMapViewModel(
  records: readonly GovernedSpacetimeFunctionRecord[],
  bucket: GovernedTimeBucket,
  geographies: readonly GovernedSpacetimeFunctionGeography[],
): GovernedSpacetimeMapViewModel {
  const geographyById = uniqueGeographies(geographies);
  const aggregates = aggregateSpacetimeByGeography(records, bucket, geographies);
  const counts = deriveTimeBucketCounts(records, bucket, geographies);
  const accessibleRows = aggregates.map((aggregate) => {
    const geography = geographyById.get(aggregate.geographyId);
    if (!geography) throw new Error("accessible row references unknown governed geography");
    return Object.freeze({
      geographyId: aggregate.geographyId,
      label: geography.label,
      mappingState: aggregate.mappingState,
      recordCount: aggregate.recordCount,
      denominator: aggregate.denominator,
    });
  });
  return Object.freeze({
    period: bucket,
    counts,
    mappedMarks: deriveSpacetimeMapMarks(aggregates),
    aggregateOnly: Object.freeze(aggregates.filter((aggregate) => aggregate.mappingState === "aggregate_only")),
    unmapped: Object.freeze(aggregates.filter((aggregate) => aggregate.mappingState === "unmapped")),
    accessibleRows: Object.freeze(accessibleRows),
  });
}

function classifyTemporalPrecision(
  sourceDisplay: string,
  start: number,
  explicitEnd: number | null,
): PublicSpacetimeTimePrecision {
  if (!Number.isSafeInteger(start)) return "unknown";
  if (/^\d{4}$/u.test(sourceDisplay) && (explicitEnd === null || explicitEnd === start)) {
    return "year";
  }
  if (explicitEnd !== null && explicitEnd !== start) return "range";
  if (isDayDisplay(sourceDisplay)) {
    return "day";
  }
  if (isMonthDisplay(sourceDisplay)) {
    return "month";
  }
  return "approximate";
}

function isDayDisplay(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/u.test(value) || NATURAL_DAY_RE.test(value);
}

function isMonthDisplay(value: string): boolean {
  const yearMonth = value.match(/^\d{4}[-/](\d{2})$/u);
  return Boolean(yearMonth && Number(yearMonth[1]) >= 1 && Number(yearMonth[1]) <= 12)
    || NATURAL_MONTH_RE.test(value);
}

function intervalOverlapsBucket(
  time: GovernedTemporalExtent,
  bucket: GovernedTimeBucket,
): boolean {
  return time.startYearInclusive < bucket.endYearExclusive
    && time.endYearInclusive >= bucket.startYearInclusive;
}

function uniqueGeographies(
  geographies: readonly GovernedSpacetimeFunctionGeography[],
): ReadonlyMap<string, GovernedSpacetimeFunctionGeography> {
  const geographyById = new Map(geographies.map((geography) => [geography.geographyId, geography]));
  if (geographyById.size !== geographies.length) throw new Error("duplicate governed geography ID");
  return geographyById;
}

function precisionBreakdown(
  records: readonly GovernedSpacetimeFunctionRecord[],
): PublicSpacetimePrecisionBreakdown {
  const counts = { day: 0, month: 0, year: 0, range: 0, approximate: 0, unknown: 0 };
  for (const record of records) counts[record.time.precision] += 1;
  return Object.freeze(counts);
}

function periodId(startYearInclusive: number, endYearExclusive: number): string {
  return `SPT-PERIOD-${startYearInclusive}-${endYearExclusive}`;
}

function compareText(left: string, right: string): number {
  return left.localeCompare(right, "en", { sensitivity: "variant" });
}
