import { geoCentroid, geoContains, geoPath, type GeoProjection } from "d3-geo";
import type {
  AggregateLayoutAnchor,
  GovernedGeometryCollection,
  GovernedGeometryFeature,
  RegisteredAggregateAnchor,
} from "./types";

export interface GovernedGeometryValidationBinding {
  readonly featureCount: number;
  readonly geometryArtifactId?: string;
}

export interface RegionAnchorInput {
  readonly geometry: GovernedGeometryFeature;
  readonly projection: GeoProjection;
  readonly geometryArtifactId: string;
  readonly geometryVersion: string;
  readonly registeredOverride?: RegisteredAggregateAnchor;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function assertLongitudeLatitude(longitude: number, latitude: number, label: string): void {
  if (!Number.isFinite(longitude) || longitude < -180 || longitude > 180) {
    throw new Error(`${label} longitude is outside [-180, 180]`);
  }
  if (!Number.isFinite(latitude) || latitude < -90 || latitude > 90) {
    throw new Error(`${label} latitude is outside [-90, 90]`);
  }
}

function freezeAnchor(
  input: RegionAnchorInput,
  longitude: number,
  latitude: number,
  method: AggregateLayoutAnchor["method"],
): AggregateLayoutAnchor {
  assertLongitudeLatitude(longitude, latitude, `${input.geometry.id} anchor`);
  return Object.freeze({
    semanticKind: "aggregate_layout_anchor",
    longitude,
    latitude,
    geometryId: input.geometry.id,
    geometryArtifactId: input.geometryArtifactId,
    geometryVersion: input.geometryVersion,
    derivationVersion: "trace-region-anchor-v1",
    method,
    positionClaim: "aggregate_only",
  });
}

export function loadGovernedGeometry(
  value: unknown,
  binding: GovernedGeometryValidationBinding,
): GovernedGeometryCollection {
  if (!isRecord(value) || value.type !== "FeatureCollection" || typeof value.name !== "string") {
    throw new Error("governed geometry must be a named GeoJSON FeatureCollection");
  }
  if (!Array.isArray(value.features) || value.features.length !== binding.featureCount) {
    throw new Error("governed geometry feature count does not match its manifest");
  }
  const geometryIds = new Set<string>();
  for (const candidate of value.features) {
    if (!isRecord(candidate) || candidate.type !== "Feature" || typeof candidate.id !== "string") {
      throw new Error("governed geometry contains an invalid Feature");
    }
    if (!isRecord(candidate.properties) || candidate.properties.geometryId !== candidate.id) {
      throw new Error(`governed geometry identity mismatch: ${candidate.id}`);
    }
    if (candidate.properties.geometryClass !== "admin0_country") {
      throw new Error(`unsupported governed geometry class: ${String(candidate.properties.geometryClass)}`);
    }
    if (!isRecord(candidate.geometry) || (candidate.geometry.type !== "Polygon" && candidate.geometry.type !== "MultiPolygon")) {
      throw new Error(`unsupported governed geometry type: ${candidate.id}`);
    }
    if (geometryIds.has(candidate.id)) throw new Error(`duplicate governed geometry ID: ${candidate.id}`);
    geometryIds.add(candidate.id);
  }
  return value as unknown as GovernedGeometryCollection;
}

export function indexGovernedGeometry(
  collection: GovernedGeometryCollection,
): ReadonlyMap<string, GovernedGeometryFeature> {
  return new Map<string, GovernedGeometryFeature>(
    collection.features.map((feature) => [String(feature.id), feature as GovernedGeometryFeature]),
  );
}

export function deriveRegionGeometry(
  geometryIndex: ReadonlyMap<string, GovernedGeometryFeature>,
  geometryId: string,
): GovernedGeometryFeature {
  const geometry = geometryIndex.get(geometryId);
  if (!geometry) throw new Error(`unknown governed geometry ID: ${geometryId}`);
  return geometry;
}

function deterministicInteriorPoint(
  geometry: GovernedGeometryFeature,
  projection: GeoProjection,
): readonly [number, number] | null {
  const path = geoPath(projection);
  const bounds = path.bounds(geometry);
  const centroid = path.centroid(geometry);
  if (bounds.flat().some((value) => !Number.isFinite(value))) return null;
  const width = bounds[1][0] - bounds[0][0];
  const height = bounds[1][1] - bounds[0][1];
  if (width <= 0 || height <= 0) return null;

  let best: { longitude: number; latitude: number; distanceSquared: number } | null = null;
  const divisions = 32;
  for (let row = 0; row < divisions; row += 1) {
    const y = bounds[0][1] + ((row + 0.5) / divisions) * height;
    for (let column = 0; column < divisions; column += 1) {
      const x = bounds[0][0] + ((column + 0.5) / divisions) * width;
      const geographic = projection.invert?.([x, y]);
      if (!geographic || !geoContains(geometry, geographic)) continue;
      const distanceSquared = (x - centroid[0]) ** 2 + (y - centroid[1]) ** 2;
      if (!best || distanceSquared < best.distanceSquared) {
        best = { longitude: geographic[0], latitude: geographic[1], distanceSquared };
      }
    }
  }
  return best ? Object.freeze([best.longitude, best.latitude]) : null;
}

export function deriveRegionAnchor(input: RegionAnchorInput): AggregateLayoutAnchor {
  if (input.registeredOverride) {
    return freezeAnchor(
      input,
      input.registeredOverride.longitude,
      input.registeredOverride.latitude,
      "registered_override",
    );
  }

  const sphericalCentroid = geoCentroid(input.geometry);
  if (
    sphericalCentroid.every(Number.isFinite) &&
    geoContains(input.geometry, sphericalCentroid)
  ) {
    return freezeAnchor(input, sphericalCentroid[0], sphericalCentroid[1], "geo_centroid");
  }

  const projectedCentroid = geoPath(input.projection).centroid(input.geometry);
  const invertedProjectedCentroid = input.projection.invert?.(projectedCentroid);
  if (
    invertedProjectedCentroid?.every(Number.isFinite) &&
    geoContains(input.geometry, invertedProjectedCentroid)
  ) {
    return freezeAnchor(
      input,
      invertedProjectedCentroid[0],
      invertedProjectedCentroid[1],
      "projected_path_centroid",
    );
  }

  const { labelLongitude, labelLatitude } = input.geometry.properties;
  if (Number.isFinite(labelLongitude) && Number.isFinite(labelLatitude)) {
    return freezeAnchor(input, labelLongitude, labelLatitude, "natural_earth_label_point");
  }

  const interiorPoint = deterministicInteriorPoint(input.geometry, input.projection);
  if (interiorPoint) {
    return freezeAnchor(input, interiorPoint[0], interiorPoint[1], "deterministic_interior_grid");
  }
  throw new Error(`unable to derive an aggregate layout anchor for ${input.geometry.id}`);
}
