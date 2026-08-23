#!/usr/bin/env node

import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { geoContains } from "d3-geo";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(scriptDirectory, "..");

const { buildAggregateDotSeed, generateAggregateDotField, prepareAggregateDotGeometry } = await import(
  "../src/features/trace-v49/spacetime/gis/dot-density.ts"
);
const { deriveRegionAnchor, indexGovernedGeometry, loadGovernedGeometry } = await import(
  "../src/features/trace-v49/spacetime/gis/geometry.ts"
);
const {
  deriveNativeCountTier,
  deriveNativePatternDefinition,
  serializeNativePatternDefinition,
  TRACE_NATIVE_COUNT_TIERS,
  TRACE_NATIVE_COUNT_TIER_POLICY_VERSION,
} = await import(
  "../src/features/trace-v49/spacetime/gis/native-pattern.ts"
);
const { deriveGeoPath, fitProjection } = await import(
  "../src/features/trace-v49/spacetime/gis/projection.ts"
);

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function sha256(buffer) {
  return createHash("sha256").update(buffer).digest("hex");
}

function jsonStable(value) {
  return JSON.stringify(value);
}

const manifestPath = join(frontendRoot, "generated", "trace-spacetime-v1", "geometry", "geometry-manifest.json");
const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
const geometryPath = join(frontendRoot, "public", manifest.publicAssetPath.replace(/^\//, ""));
const geometryBytes = await readFile(geometryPath);
assert(sha256(geometryBytes) === manifest.outputSha256, "public geometry SHA-256 does not match manifest");
assert(geometryBytes.length === manifest.outputRawBytes, "public geometry byte count does not match manifest");
const collection = loadGovernedGeometry(JSON.parse(geometryBytes.toString("utf8")), manifest);
const index = indexGovernedGeometry(collection);
assert(index.size === 242, "Natural Earth 5.1.1 50m feature count changed");
assert(collection.features.every((feature) => feature.id === feature.properties.admin0A3), "feature identity is not ADM0_A3");
const geographyRegistry = JSON.parse(
  await readFile(join(frontendRoot, "generated", "trace-spacetime-v1", "geography-registry.json"), "utf8"),
);
assert(
  geographyRegistry.geometryArtifactId === manifest.geometryArtifactId,
  "geography registry and geometry manifest artifact IDs differ",
);
const mappedRegistryEntries = geographyRegistry.entries.filter((entry) => entry.mappingState === "mapped");
const registryGeometryTargets = mappedRegistryEntries.flatMap((entry) => entry.geometryTargets);
const registryGeometryTargetIds = registryGeometryTargets.map((target) => target.geometryId);
const registryGeometryIds = mappedRegistryEntries.flatMap((entry) => entry.geometryIds);
assert(mappedRegistryEntries.length === geographyRegistry.counts.mappedEntries, "mapped geography registry count drifted");
assert(
  registryGeometryTargets.every(
    (target) =>
      target.geometryArtifactId === manifest.geometryArtifactId &&
      target.matchField === "admin0A3" &&
      target.matchValue === target.geometryId,
  ),
  "mapped geography target contract does not bind exact ADM0_A3 identity",
);
assert(registryGeometryTargetIds.every((target) => index.has(target)), "mapped geography target is absent from geometry");
assert(registryGeometryIds.every((geometryId) => index.has(geometryId)), "resolved geometry ID is absent from geometry");
assert(
  mappedRegistryEntries.every(
    (entry) => jsonStable(entry.geometryTargets.map((target) => target.geometryId)) === jsonStable(entry.geometryIds),
  ),
  "geometry target and resolved geometry identity differ",
);

const viewport = Object.freeze({ width: 1440, height: 800, padding: 24 });
const projection = fitProjection("equal-earth", collection, viewport);
const path = deriveGeoPath(projection);
const projectedPaths = collection.features.map((feature) => path(feature));
assert(projectedPaths.every(Boolean), "one or more governed features produced an empty path");

const large = index.get("USA");
const multipart = index.get("FJI");
const tiny = index.get("VAT");
assert(large && multipart && tiny, "pathological GIS sample feature missing");

const anchors = [large, multipart, tiny].map((geometry) =>
  deriveRegionAnchor({
    geometry,
    projection,
    geometryArtifactId: manifest.geometryArtifactId,
    geometryVersion: manifest.sourceVersion,
  }),
);
assert(anchors.every((anchor) => anchor.semanticKind === "aggregate_layout_anchor"), "anchor semantic kind changed");
assert(anchors.every((anchor) => anchor.positionClaim === "aggregate_only"), "anchor claims an object location");

const seed = buildAggregateDotSeed({
  releaseId: "prefreeze_candidate_v48",
  geometryId: large.id,
  timeBucketId: "decade-1960",
  recordCount: 250,
  policyVersion: "trace-dot-density-grid-v1",
});
const dotInput = {
  geometry: large,
  projection,
  recordCount: 250,
  seed,
  fallbackAnchor: anchors[0],
  preparedGeometry: prepareAggregateDotGeometry(large, projection, "equal-earth:1440x800:padding-24"),
};
const firstField = generateAggregateDotField(dotInput);
const repeatedField = generateAggregateDotField(dotInput);
assert(jsonStable(firstField) === jsonStable(repeatedField), "aggregate dot field is not deterministic");
assert(firstField.positionClaim === "aggregate_only", "aggregate dot field claims object positions");
assert(firstField.representedRecordCount === dotInput.recordCount, "aggregate dot field loses records");
for (const dot of firstField.dots) {
  const geographic = projection.invert?.([dot.x, dot.y]);
  assert(geographic && geoContains(large, geographic), `density dot ${dot.id} lies outside governed geometry`);
  assert(dot.positionClaim === "aggregate_only", `density dot ${dot.id} claims an object location`);
}

const tinySeed = buildAggregateDotSeed({
  releaseId: "prefreeze_candidate_v48",
  geometryId: tiny.id,
  timeBucketId: "decade-1960",
  recordCount: 7,
  policyVersion: "trace-dot-density-grid-v1",
});
const tinyField = generateAggregateDotField({
  geometry: tiny,
  projection,
  recordCount: 7,
  seed: tinySeed,
  fallbackAnchor: anchors[2],
  preparedGeometry: prepareAggregateDotGeometry(tiny, projection, "equal-earth:1440x800:padding-24"),
});
assert(tinyField.representedRecordCount === 7, "tiny geography handling loses records");
assert(tinyField.fallback?.reason === "tiny_geometry", "tiny geography does not use the registered aggregate-anchor policy");

const patternInput = Object.freeze({
  namespace: "trace-spacetime-v1",
  family: "dots",
  encodedVariable: "record_count_tier",
  legendValue: "high",
  spacingPx: 8,
  weightPx: 1.25,
});
const pattern = deriveNativePatternDefinition(patternInput);
const repeatedPattern = deriveNativePatternDefinition(patternInput);
assert(jsonStable(pattern) === jsonStable(repeatedPattern), "native SVG pattern is not deterministic");
assert(pattern.encodedVariable === "record_count_tier", "native SVG pattern lost its encoded variable");
assert(serializeNativePatternDefinition(pattern).length < 500, "native SVG pattern definition is unexpectedly large");
assert(TRACE_NATIVE_COUNT_TIER_POLICY_VERSION === "trace-native-count-tier-v1", "native count-tier policy drifted");
assert(TRACE_NATIVE_COUNT_TIERS.length === 4, "native count-tier registry length drifted");
assert(deriveNativeCountTier(1).legendValue === "1–4 records", "native low-count tier drifted");
assert(deriveNativeCountTier(5).legendValue === "5–24 records", "native lower-middle tier drifted");
assert(deriveNativeCountTier(25).legendValue === "25–99 records", "native upper-middle tier drifted");
assert(deriveNativeCountTier(100).legendValue === "100 or more records", "native high-count tier drifted");
assert(
  TRACE_NATIVE_COUNT_TIERS.every((tier) => tier.legendValue.trim() && Number.isFinite(tier.spacingPx)),
  "native count-tier legend is incomplete",
);

const implementationSources = await Promise.all(
  ["dot-density.ts", "geometry.ts", "projection.ts"].map((filename) =>
    readFile(join(frontendRoot, "src", "features", "trace-v49", "spacetime", "gis", filename), "utf8"),
  ),
);
assert(!implementationSources.some((source) => source.includes("Math.random")), "unseeded randomness entered GIS implementation");
assert(!implementationSources.some((source) => /\bd\s*=\s*["'`]M[-\d]/.test(source)), "hand-authored SVG geography path detected");

console.log(
  [
    "SPACETIME_GIS=PASS",
    `GEOMETRY_ARTIFACT_ID=${manifest.geometryArtifactId}`,
    `GEOMETRY_SHA256=${manifest.outputSha256}`,
    `FEATURE_COUNT=${collection.features.length}`,
    `MAPPED_REGISTRY_ENTRIES=${mappedRegistryEntries.length}`,
    `MAPPED_GEOMETRY_TARGETS=${registryGeometryTargetIds.length}`,
    "MISSING_MAPPED_GEOMETRY_TARGETS=0",
    "DEFAULT_PROJECTION=equal-earth",
    `PROJECTED_PATH_COUNT=${projectedPaths.length}`,
    `DOTS_TESTED=${firstField.dots.length}`,
    "DOT_DETERMINISTIC=true",
    "DOT_POSITION_SEMANTICS=aggregate_only",
    `TINY_GEOGRAPHY_FALLBACK=${tinyField.fallback?.reason ?? "none"}`,
    "NATIVE_PATTERN_DETERMINISTIC=true",
    `NATIVE_PATTERN_TIER_POLICY=${TRACE_NATIVE_COUNT_TIER_POLICY_VERSION}`,
    `NATIVE_PATTERN_TIER_COUNT=${TRACE_NATIVE_COUNT_TIERS.length}`,
    "HAND_AUTHORED_GEOGRAPHY_PATH_COUNT=0",
    "MANUAL_OBJECT_COORDINATE_COUNT=0",
  ].join(" "),
);

// The runtime closure extends the focused GIS samples above with the complete
// 23-period / 93-geography state cube, both deterministic dot passes, renderer
// parity, cache lifecycle, races, export preparation, and texture stability.
await import("./verify-spacetime-runtime-v1.mjs");
