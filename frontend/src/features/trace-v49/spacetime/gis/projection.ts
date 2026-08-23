import {
  geoEqualEarth,
  geoNaturalEarth1,
  geoPath,
  type GeoPath,
  type GeoPermissibleObjects,
  type GeoProjection,
} from "d3-geo";
import type { SpacetimeProjectionKind, SpacetimeProjectionViewport } from "./types";

export const DEFAULT_SPACETIME_PROJECTION_PRECISION = 0.1;
export const DEFAULT_SPACETIME_PATH_DIGITS = 3;

function assertViewport(viewport: SpacetimeProjectionViewport): void {
  if (!Number.isFinite(viewport.width) || viewport.width <= 0) throw new Error("projection viewport width must be positive");
  if (!Number.isFinite(viewport.height) || viewport.height <= 0) throw new Error("projection viewport height must be positive");
  if (!Number.isFinite(viewport.padding) || viewport.padding < 0) throw new Error("projection viewport padding cannot be negative");
  if (viewport.padding * 2 >= Math.min(viewport.width, viewport.height)) {
    throw new Error("projection viewport padding consumes the viewport");
  }
}

export function buildProjection(
  kind: SpacetimeProjectionKind,
  precision = DEFAULT_SPACETIME_PROJECTION_PRECISION,
): GeoProjection {
  if (!Number.isFinite(precision) || precision <= 0) throw new Error("projection precision must be positive");
  if (kind === "equal-earth") return geoEqualEarth().precision(precision);
  if (kind === "natural-earth-1") return geoNaturalEarth1().precision(precision);
  const exhaustiveCheck: never = kind;
  throw new Error(`unsupported projection: ${exhaustiveCheck}`);
}

export function fitProjection(
  kind: SpacetimeProjectionKind,
  geometry: GeoPermissibleObjects,
  viewport: SpacetimeProjectionViewport,
  precision = DEFAULT_SPACETIME_PROJECTION_PRECISION,
): GeoProjection {
  assertViewport(viewport);
  const projection = buildProjection(kind, precision);
  projection.fitExtent(
    [
      [viewport.padding, viewport.padding],
      [viewport.width - viewport.padding, viewport.height - viewport.padding],
    ],
    geometry,
  );
  return projection;
}

export function deriveGeoPath(
  projection: GeoProjection,
  digits = DEFAULT_SPACETIME_PATH_DIGITS,
): GeoPath<unknown, GeoPermissibleObjects> {
  if (!Number.isSafeInteger(digits) || digits < 0 || digits > 15) throw new Error("geo path digits must be an integer from 0 to 15");
  return geoPath(projection).digits(digits);
}

export function deriveProjectedPath(
  geometry: GeoPermissibleObjects,
  kind: SpacetimeProjectionKind,
  viewport: SpacetimeProjectionViewport,
  digits = DEFAULT_SPACETIME_PATH_DIGITS,
  precision = DEFAULT_SPACETIME_PROJECTION_PRECISION,
): string {
  const path = deriveGeoPath(fitProjection(kind, geometry, viewport, precision), digits)(geometry);
  if (!path) throw new Error("governed geometry produced an empty projected path");
  return path;
}

export function deriveProjectedBounds(
  geometry: GeoPermissibleObjects,
  projection: GeoProjection,
): readonly [readonly [number, number], readonly [number, number]] {
  const bounds = deriveGeoPath(projection).bounds(geometry);
  if (bounds.flat().some((value) => !Number.isFinite(value))) throw new Error("governed geometry produced non-finite bounds");
  const minimum = Object.freeze([bounds[0][0], bounds[0][1]]) as readonly [number, number];
  const maximum = Object.freeze([bounds[1][0], bounds[1][1]]) as readonly [number, number];
  return Object.freeze([minimum, maximum]);
}
