import { geoPath, type GeoProjection } from "d3-geo";
import type { PublicSpacetimeAtlasDataset } from "../governed/types";
import type {
  GovernedGeometryFeature,
  RegisteredAggregateAnchor,
  SpacetimeMapRegionMark,
  SpacetimeMapSelection,
  SpacetimeMapViewModel,
} from "./types";
import { deriveRegionAnchor } from "./geometry";

export interface DeriveSpacetimeMapViewModelInput {
  readonly atlas: PublicSpacetimeAtlasDataset;
  readonly geometryIndex: ReadonlyMap<string, GovernedGeometryFeature>;
  readonly projection: GeoProjection;
  readonly registeredAnchorOverrides?: ReadonlyMap<string, RegisteredAggregateAnchor>;
}

function assertCount(value: number, label: string): void {
  if (!Number.isSafeInteger(value) || value < 0) throw new Error(`${label} must be a non-negative safe integer`);
}

function selectAnchorGeometry(
  geographyId: string,
  geometryIds: readonly string[],
  geometryIndex: ReadonlyMap<string, GovernedGeometryFeature>,
  projection: GeoProjection,
): GovernedGeometryFeature {
  if (geometryIds.length === 0) throw new Error(`mapped geography has no geometry: ${geographyId}`);
  const path = geoPath(projection);
  const resolved = geometryIds.map((geometryId) => {
    const geometry = geometryIndex.get(geometryId);
    if (!geometry) throw new Error(`mapped geography ${geographyId} references unknown geometry ${geometryId}`);
    return geometry;
  });
  return resolved
    .map((geometry) => ({ geometry, area: path.area(geometry) }))
    .sort((left, right) => right.area - left.area || left.geometry.id.localeCompare(right.geometry.id))[0].geometry;
}

function deriveMappedMark(
  input: DeriveSpacetimeMapViewModelInput,
  geography: PublicSpacetimeAtlasDataset["mappedGeographies"][number],
): SpacetimeMapRegionMark {
  assertCount(geography.recordCount, `${geography.geographyId} record count`);
  assertCount(geography.denominator, `${geography.geographyId} denominator`);
  if (geography.recordCount > geography.denominator) {
    throw new Error(`mapped geography ${geography.geographyId} exceeds its denominator`);
  }
  const anchorGeometry = selectAnchorGeometry(
    geography.geographyId,
    geography.geometryIds,
    input.geometryIndex,
    input.projection,
  );
  const anchor = deriveRegionAnchor({
    geometry: anchorGeometry,
    projection: input.projection,
    geometryArtifactId: input.atlas.geometry.geometryArtifactId,
    geometryVersion: input.atlas.geometry.sourceVersion,
    registeredOverride: input.registeredAnchorOverrides?.get(geography.geographyId),
  });
  return Object.freeze({
    geographyId: geography.geographyId,
    label: geography.label,
    geometryIds: Object.freeze([...geography.geometryIds]),
    recordCount: geography.recordCount,
    denominator: geography.denominator,
    mappedState: "mapped",
    anchor,
    anchorComponentPolicy: "largest_projected_area",
    precisionBreakdown: Object.freeze({ ...geography.precisionBreakdown }),
    qualification: geography.qualification,
    historicalStatus: geography.historicalStatus,
    transnational: geography.transnational,
    broadRegion: geography.broadRegion,
    positionClaim: "aggregate_only",
  });
}

export function deriveSpacetimeMapViewModel(
  input: DeriveSpacetimeMapViewModelInput,
): SpacetimeMapViewModel {
  const { atlas } = input;
  if (atlas.realSemanticEdgeCount !== 0) throw new Error("Spacetime map marks cannot become TRACE semantic edges");
  assertCount(atlas.counts.denominator, "atlas denominator");
  assertCount(atlas.counts.mappedRecords, "atlas mapped record count");
  assertCount(atlas.counts.unmappedRecords, "atlas unmapped record count");
  if (atlas.counts.mappedRecords + atlas.counts.unmappedRecords !== atlas.counts.denominator) {
    throw new Error("Spacetime mapped + unmapped counts do not reconcile to the denominator");
  }
  const mappedMarks = atlas.mappedGeographies
    .map((geography) => deriveMappedMark(input, geography))
    .sort((left, right) => left.geographyId.localeCompare(right.geographyId));
  if (new Set(mappedMarks.map((mark) => mark.geographyId)).size !== mappedMarks.length) {
    throw new Error("Spacetime map contains duplicate governed geography IDs");
  }
  return Object.freeze({
    selectedPeriod: Object.freeze({ ...atlas.selectedPeriod }),
    mappedMarks: Object.freeze(mappedMarks),
    aggregateOnlyGeographies: Object.freeze([...atlas.aggregateOnlyGeographies]),
    unmappedGeographies: Object.freeze([...atlas.unmappedGeographies]),
    accessibleRows: Object.freeze([...atlas.accessibleRows]),
    counts: Object.freeze({ ...atlas.counts }),
    dotPolicy: Object.freeze({ ...atlas.dotPolicy }),
    geometry: Object.freeze({ ...atlas.geometry }),
    realSemanticEdgeCount: 0,
  });
}

export function selectSpacetimeMapGeography(
  viewModel: SpacetimeMapViewModel,
  geographyId: string | null,
): SpacetimeMapSelection | null {
  if (!geographyId) return null;
  const mapped = viewModel.mappedMarks.find((mark) => mark.geographyId === geographyId);
  if (mapped) return Object.freeze({ kind: "mapped", value: mapped });
  const aggregateOnly = viewModel.aggregateOnlyGeographies.find((geography) => geography.geographyId === geographyId);
  if (aggregateOnly) return Object.freeze({ kind: "aggregate_only", value: aggregateOnly });
  const unmapped = viewModel.unmappedGeographies.find((geography) => geography.geographyId === geographyId);
  if (unmapped) return Object.freeze({ kind: "unmapped", value: unmapped });
  return null;
}
