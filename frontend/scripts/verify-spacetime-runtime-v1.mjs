#!/usr/bin/env node

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { geoContains } from "d3-geo";
import createJiti from "jiti";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(here, "..");
const jiti = createJiti(import.meta.url, {
  interopDefault: true,
  alias: {
    "@": join(frontendRoot, "src"),
    "server-only": join(here, "server-only-marker.mjs"),
  },
});
const reader = await jiti.import(
  join(frontendRoot, "src/features/trace-v49/spacetime/governed/reader.server.ts"),
);
const gis = await jiti.import(
  join(frontendRoot, "src/features/trace-v49/spacetime/gis/index.ts"),
);
const requests = await jiti.import(
  join(frontendRoot, "src/features/trace-v49/spacetime/map/request-epochs.ts"),
);

const geometryBytes = await readFile(join(
  frontendRoot,
  "public/trace-spacetime-v1/natural-earth-50m-admin0-v5.1.1.geojson",
));

function deferred() {
  let resolvePromise;
  const promise = new Promise((resolveValue) => {
    resolvePromise = resolveValue;
  });
  return Object.freeze({ promise, resolve: resolvePromise });
}

reader.resetGovernedSpacetimeReaderForTests();
const periods = reader.getGovernedSpacetimePeriodsDataset();
assert.equal(periods.periods.length, 23);

const sourceCache = new gis.SpacetimeGeometryRuntimeCache();
let fetchCount = 0;
let sawSharedSignal = false;
const fetcher = async (_input, init = {}) => {
  fetchCount += 1;
  sawSharedSignal ||= "signal" in init;
  return new Response(geometryBytes, { status: 200 });
};
const firstSourcePromise = sourceCache.loadSource(periods.geometry, fetcher);
const secondSourcePromise = sourceCache.loadSource(periods.geometry, fetcher);
assert.equal(firstSourcePromise, secondSourcePromise, "geometry load is not single-flight");
const [firstSource, secondSource] = await Promise.all([firstSourcePromise, secondSourcePromise]);
assert.equal(firstSource, secondSource, "geometry warm reuse did not retain decoded source identity");
assert.equal(fetchCount, 1, "geometry single-flight performed more than one fetch");
assert.equal(sawSharedSignal, false, "a consumer AbortSignal entered the shared geometry request");
assert.equal(firstSource.byId.size, periods.geometry.featureCount);
const sourceDiagnostics = sourceCache.diagnosticsForTests();
assert.equal(sourceDiagnostics.sourceCacheMisses, 1);
assert.equal(sourceDiagnostics.sourceCacheHits, 1);
assert.equal(sourceDiagnostics.sourceCacheEntries, 1);
assert(sourceDiagnostics.lastColdGeometryTiming?.decodeMs >= 0);
assert(sourceDiagnostics.lastColdGeometryTiming?.indexMs >= 0);

const failureCache = new gis.SpacetimeGeometryRuntimeCache();
await assert.rejects(
  failureCache.loadSource(periods.geometry, async () => new Response("{}", { status: 200 })),
  /SHA-256/u,
);
const recoveredSource = await failureCache.loadSource(
  periods.geometry,
  async () => new Response(geometryBytes, { status: 200 }),
);
assert.equal(recoveredSource.byId.size, periods.geometry.featureCount);
assert.equal(failureCache.diagnosticsForTests().sourceLoadFailures, 1);
assert.equal(failureCache.diagnosticsForTests().sourceCacheMisses, 2);

const viewport = Object.freeze({ width: 1_200, height: 640, padding: 28 });
const projectionInput = Object.freeze({
  projectionId: "equal-earth",
  viewport,
  geometryAssetSha256: periods.geometry.assetSha256,
  projectionPrecision: 0.1,
});
const cacheKey = gis.buildSpacetimeProjectionCacheKey(projectionInput);
assert.equal(cacheKey, gis.buildSpacetimeProjectionCacheKey({ ...projectionInput }));
for (const changed of [
  { ...projectionInput, projectionId: "natural-earth-1" },
  { ...projectionInput, viewport: { ...viewport, width: 1_201 } },
  { ...projectionInput, viewport: { ...viewport, height: 641 } },
  { ...projectionInput, viewport: { ...viewport, padding: 29 } },
  { ...projectionInput, geometryAssetSha256: "0".repeat(64) },
  { ...projectionInput, projectionPrecision: 0.2 },
]) {
  assert.notEqual(gis.buildSpacetimeProjectionCacheKey(changed), cacheKey);
}
const firstProjection = sourceCache.prepareProjection(firstSource, {
  projectionId: "equal-earth",
  viewport,
  projectionPrecision: 0.1,
});
const secondProjection = sourceCache.prepareProjection(firstSource, {
  projectionId: "equal-earth",
  viewport: { ...viewport },
  projectionPrecision: 0.1,
});
assert.equal(firstProjection, secondProjection, "same governed projection missed its path cache");
assert.equal(firstProjection.pathById.size, periods.geometry.featureCount);
assert.equal(firstProjection.boundsById.size, 0, "path miss eagerly prepared unused governed bounds");
assert.equal(firstProjection.projectedAreaById.size, 0, "path miss eagerly prepared unused governed areas");
assert.equal(firstProjection.anchorByGeometryId.size, 0, "path miss eagerly prepared unused governed anchors");
for (let index = 0; index < 5; index += 1) {
  sourceCache.prepareProjection(firstSource, {
    projectionId: "equal-earth",
    viewport: { ...viewport, width: viewport.width + 10 + index },
    projectionPrecision: 0.1,
  });
}
assert.equal(sourceCache.diagnosticsForTests().projectionCacheEntries, 4, "projection cache is not bounded");

const raceGate = new requests.SpacetimeRequestEpochGate();
const slowA = deferred();
const atlasA = raceGate.begin("atlas");
const slowB = deferred();
const atlasB = raceGate.begin("atlas");
const slowC = deferred();
const atlasC = raceGate.begin("atlas");
assert.equal(atlasA.isCurrent(), false);
assert.equal(atlasB.isCurrent(), false);
assert.equal(atlasC.isCurrent(), true);
const committed = [];
const slowCommits = [
  slowA.promise.then((value) => atlasA.isCurrent() && committed.push(value)),
  slowB.promise.then((value) => atlasB.isCurrent() && committed.push(value)),
  slowC.promise.then((value) => atlasC.isCurrent() && committed.push(value)),
];
// The simulated fetches deliberately ignore every AbortSignal and settle out
// of order. Only C may commit.
slowB.resolve("B");
slowC.resolve("C");
slowA.resolve("A");
await Promise.all(slowCommits);
assert.deepEqual(committed, ["C"], "late non-abortable atlas response can commit");
const recordsBeforePeriodSwitch = raceGate.begin("records");
raceGate.abort("records");
assert.equal(recordsBeforePeriodSwitch.isCurrent(), false, "period switch did not invalidate records");

const firstAtlasResult = reader.lookupGovernedSpacetimeAtlas(periods.defaultPeriodId);
assert(firstAtlasResult.ok);
const firstAtlas = firstAtlasResult.data;
const selectedRow = firstAtlas.accessibleRows.find((row) => row.recordCount > 1);
assert(selectedRow, "default atlas has no cursor-test geography");
const firstRecordResult = reader.lookupGovernedSpacetimeGeographyRecords(selectedRow.geographyId, {
  periodId: firstAtlas.selectedPeriod.periodId,
  first: 1,
});
assert(firstRecordResult.ok);
const recordIdentity = Object.freeze({
  spacetimeProjectionSha256: periods.release.spacetimeProjectionSha256,
  periodId: firstAtlas.selectedPeriod.periodId,
  geographyId: selectedRow.geographyId,
  after: null,
});
const accumulator = requests.applySpacetimeRecordPage(null, recordIdentity, firstRecordResult.data);
assert(firstRecordResult.data.pageInfo.endCursor);
const secondRecordResult = reader.lookupGovernedSpacetimeGeographyRecords(selectedRow.geographyId, {
  periodId: firstAtlas.selectedPeriod.periodId,
  first: 1,
  after: firstRecordResult.data.pageInfo.endCursor,
});
assert(secondRecordResult.ok);
const appendIdentity = Object.freeze({
  ...recordIdentity,
  after: firstRecordResult.data.pageInfo.endCursor,
});
const appended = requests.applySpacetimeRecordPage(accumulator, appendIdentity, secondRecordResult.data);
assert.equal(appended.records.length, 2);
await assert.rejects(
  async () => requests.applySpacetimeRecordPage(
    accumulator,
    { ...appendIdentity, periodId: periods.periods.find((period) => period.periodId !== recordIdentity.periodId).periodId },
    secondRecordResult.data,
  ),
  /identity|stale/u,
);
await assert.rejects(
  async () => requests.applySpacetimeRecordPage(
    accumulator,
    { ...appendIdentity, geographyId: firstAtlas.accessibleRows.find((row) => row.geographyId !== recordIdentity.geographyId).geographyId },
    secondRecordResult.data,
  ),
  /identity|stale/u,
);
assert.equal(requests.spacetimeAtlasResultMatches(
  { ...recordIdentity, periodId: firstAtlas.selectedPeriod.periodId },
  firstAtlas,
), true);
assert.equal(requests.spacetimeAtlasResultMatches(
  { ...recordIdentity, periodId: periods.periods.find((period) => period.periodId !== firstAtlas.selectedPeriod.periodId).periodId },
  firstAtlas,
), false);

const rendererCacheOne = new gis.SpacetimeRendererRuntimeCache();
const rendererCacheTwo = new gis.SpacetimeRendererRuntimeCache();
let nonzeroCellCount = 0;
let mappedCellCount = 0;
let reconciliationFailureCount = 0;
let determinismFailureCount = 0;
let containmentFailureCount = 0;
let firstContainmentFailure = null;
let multiGeometryCellCount = 0;
let patternIdCollisionCount = 0;
let aggregateParity = true;
let densityParity = true;
let textureParity = true;
let defaultModels = null;
let hostileBoundaryRegressionPass = false;

for (const period of periods.periods) {
  const atlasResult = reader.lookupGovernedSpacetimeAtlas(period.periodId);
  assert(atlasResult.ok);
  const atlas = atlasResult.data;
  nonzeroCellCount += atlas.accessibleRows.length;
  const selectedGeographyId = atlas.accessibleRows[0]?.geographyId ?? null;
  const uncachedViewModel = gis.deriveSpacetimeMapViewModel({
    atlas,
    geometryIndex: firstProjection.source.byId,
    projection: firstProjection.projection,
  });
  gis.ensureSpacetimeProjectionGeometryAnchors(
    firstProjection,
    atlas.mappedGeographies.flatMap((geography) => geography.geometryIds),
  );
  const cachedViewModel = gis.deriveSpacetimeMapViewModel({
    atlas,
    geometryIndex: firstProjection.source.byId,
    projection: firstProjection.projection,
    projectedAreaByGeometryId: firstProjection.projectedAreaById,
    anchorByGeometryId: firstProjection.anchorByGeometryId,
  });
  assert.deepEqual(cachedViewModel, uncachedViewModel, "cached geometry invariants changed a map view model");
  const aggregate = gis.deriveSpacetimeRendererModel({
    atlas,
    projection: firstProjection,
    mode: "aggregate",
    selectedGeographyId,
    cache: rendererCacheOne,
  });
  const densityOne = gis.deriveSpacetimeRendererModel({
    atlas,
    projection: firstProjection,
    mode: "density",
    selectedGeographyId,
    cache: rendererCacheOne,
  });
  const densityTwo = gis.deriveSpacetimeRendererModel({
    atlas,
    projection: firstProjection,
    mode: "density",
    selectedGeographyId,
    cache: rendererCacheTwo,
  });
  const texture = gis.deriveSpacetimeRendererModel({
    atlas,
    projection: firstProjection,
    mode: "texture",
    selectedGeographyId,
    cache: rendererCacheOne,
  });
  const semantic = JSON.stringify(aggregate.semanticState);
  aggregateParity &&= semantic === JSON.stringify(aggregate.semanticState);
  densityParity &&= semantic === JSON.stringify(densityOne.semanticState);
  textureParity &&= semantic === JSON.stringify(texture.semanticState);
  assert(aggregate.marks.every((mark) => mark.density === null && mark.pattern === null));
  assert(densityOne.marks.every((mark) => mark.density && mark.pattern === null));
  assert(texture.marks.every((mark) => mark.density === null && mark.pattern));
  assert.equal(aggregate.semanticState.selectedGeographyId, selectedGeographyId);
  assert.equal(densityOne.semanticState.selectedGeographyId, selectedGeographyId);
  assert.equal(texture.semanticState.selectedGeographyId, selectedGeographyId);

  const patternIds = texture.marks.map((mark) => mark.pattern.id);
  patternIdCollisionCount += patternIds.length - new Set(patternIds).size;
  for (const mark of texture.marks) {
    const tier = gis.deriveNativeCountTier(mark.geography.recordCount);
    assert.equal(mark.pattern.legendValue, tier.legendValue);
    assert.equal(mark.pattern.width, tier.spacingPx);
    assert.equal(mark.pattern.height, tier.spacingPx);
  }
  mappedCellCount += densityOne.marks.length;
  for (let index = 0; index < densityOne.marks.length; index += 1) {
    const mark = densityOne.marks[index];
    const repeatedMark = densityTwo.marks[index];
    const density = mark.density;
    assert(density);
    if (density.generatedDotCount + density.anchorRemainderCount !== mark.geography.recordCount) {
      reconciliationFailureCount += 1;
    }
    if (density.representedRecordCount !== mark.geography.recordCount) reconciliationFailureCount += 1;
    if (JSON.stringify(density) !== JSON.stringify(repeatedMark.density)) determinismFailureCount += 1;
    if (density.positionClaim !== "aggregate_only") determinismFailureCount += 1;
    if (mark.geography.geometryIds.length > 1) {
      multiGeometryCellCount += 1;
      if (density.strategy !== "multi_geometry_anchor" || density.dots.length !== 0) {
        reconciliationFailureCount += 1;
      }
      continue;
    }
    const geometry = firstProjection.source.byId.get(mark.geography.anchor.geometryId);
    assert(geometry);
    if (period.periodId === "SPT-PERIOD-1930-1940" && geometry.id === "GBR") {
      assert.equal(
        density.dots.some((dot) => dot.x === 588.337 && dot.y === 102.405),
        false,
        "serialized near-boundary GBR candidate re-entered the emitted field",
      );
      hostileBoundaryRegressionPass = true;
    }
    for (const dot of density.dots) {
      const geographic = firstProjection.projection.invert?.([dot.x, dot.y]);
      if (!geographic || !geoContains(geometry, geographic)) {
        containmentFailureCount += 1;
        firstContainmentFailure ??= Object.freeze({
          periodId: period.periodId,
          geographyId: mark.geography.geographyId,
          geometryId: geometry.id,
          dot,
          geographic,
        });
      }
      if (dot.positionClaim !== "aggregate_only") containmentFailureCount += 1;
    }
  }
  if (period.periodId === periods.defaultPeriodId) {
    defaultModels = Object.freeze({ atlas, aggregate, density: densityOne, texture });
  }
}

assert.equal(nonzeroCellCount, 373);
assert.equal(mappedCellCount, 351);
assert.equal(multiGeometryCellCount, 14);
assert.equal(reconciliationFailureCount, 0);
assert.equal(determinismFailureCount, 0);
assert.equal(containmentFailureCount, 0, JSON.stringify(firstContainmentFailure));
assert.equal(patternIdCollisionCount, 0);
assert.equal(aggregateParity, true);
assert.equal(densityParity, true);
assert.equal(textureParity, true);
assert.equal(hostileBoundaryRegressionPass, true);
assert.equal(firstProjection.anchorByGeometryId.size, 84, "geometry anchor cache coverage drifted");
assert.equal(firstProjection.projectedAreaById.size, 84, "geometry area cache coverage drifted");
assert.equal(firstProjection.boundsById.size, 84, "geometry bounds cache coverage drifted");
assert(defaultModels);

for (const model of [defaultModels.aggregate, defaultModels.density, defaultModels.texture]) {
  const prepared = gis.prepareSpacetimeFunctionalExport({
    atlas: defaultModels.atlas,
    projection: firstProjection,
    renderer: model,
  });
  const serializedOne = gis.serializeSpacetimeFunctionalExport(prepared);
  const serializedTwo = gis.serializeSpacetimeFunctionalExport(
    gis.prepareSpacetimeFunctionalExport({
      atlas: defaultModels.atlas,
      projection: firstProjection,
      renderer: model,
    }),
  );
  assert.equal(serializedOne, serializedTwo, `${model.mode} export is not deterministic`);
  assert.equal(prepared.baseMapGeometry.length, periods.geometry.featureCount);
  assert.equal(prepared.mapMarks.length, model.marks.length);
  assert.equal(prepared.geographyRows.length, defaultModels.atlas.accessibleRows.length);
  assert.equal(prepared.positionClaim, "aggregate_only");
  assert(!/\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b/iu.test(serializedOne));
  assert(!serializedOne.includes("observationId"));
  assert(!serializedOne.includes("rawRegionDisplay"));
}
assert(defaultModels.texture.marks.every((mark) =>
  mark.pattern.deterministic
  && gis.serializeNativePatternDefinition(mark.pattern).startsWith("<pattern ")));
assert.deepEqual(
  defaultModels.texture.marks.map((mark) => mark.pattern.id),
  gis.deriveSpacetimeRendererModel({
    atlas: defaultModels.atlas,
    projection: firstProjection,
    mode: "texture",
    selectedGeographyId: defaultModels.texture.semanticState.selectedGeographyId,
    cache: rendererCacheTwo,
  }).marks.map((mark) => mark.pattern.id),
  "native texture IDs are not hydration-stable",
);

const workspaceSource = await readFile(
  join(frontendRoot, "src/features/trace-v49/spacetime/map/SpacetimeWorkspace.tsx"),
  "utf8",
);
assert(workspaceSource.includes("Accessible geography table"));
assert(workspaceSource.includes("TRACE_NATIVE_COUNT_TIERS.map"));
assert(workspaceSource.includes("not object coordinates"));
const controlsSource = workspaceSource.slice(
  workspaceSource.indexOf('<section className={styles.controls}'),
  workspaceSource.indexOf('</section>', workspaceSource.indexOf('<section className={styles.controls}')),
);
assert(!controlsSource.includes('disabled={atlasState === "loading"}'));
assert(!workspaceSource.includes("Math.random"));

console.log([
  "SPACETIME_RUNTIME_V1=PASS",
  `SPACETIME_PERIOD_COUNT=${periods.periods.length}`,
  `SPACETIME_NONZERO_PERIOD_REGION_CELL_COUNT=${nonzeroCellCount}`,
  `DOT_FIELD_CELL_COUNT=${mappedCellCount}`,
  `DOT_FIELD_RECONCILIATION_FAILURE_COUNT=${reconciliationFailureCount}`,
  `DOT_FIELD_DETERMINISM_FAILURE_COUNT=${determinismFailureCount}`,
  `DOT_FIELD_CONTAINMENT_FAILURE_COUNT=${containmentFailureCount}`,
  `MULTI_GEOMETRY_ANCHOR_ONLY_CELL_COUNT=${multiGeometryCellCount}`,
  `NATIVE_PATTERN_ID_COLLISION_COUNT=${patternIdCollisionCount}`,
  `DOT_HOSTILE_BOUNDARY_REGRESSION=${hostileBoundaryRegressionPass ? "PASS" : "FAIL"}`,
  `GEOMETRY_SINGLE_FLIGHT_FETCH_COUNT=${fetchCount}`,
  `GEOMETRY_SOURCE_CACHE_HIT_COUNT=${sourceDiagnostics.sourceCacheHits}`,
  `PROJECTION_PATH_CACHE_HIT_COUNT=${sourceCache.diagnosticsForTests().projectionCacheHits}`,
  `PROJECTION_GEOMETRY_ANCHOR_CACHE_COUNT=${firstProjection.anchorByGeometryId.size}`,
  "SPACETIME_RAPID_PERIOD_SWITCH=PASS",
  "SPACETIME_STALE_RESPONSE_GUARD=PASS",
  "SPACETIME_CURSOR_ISOLATION=PASS",
  `AGGREGATE_MODE_SEMANTIC_PARITY=${aggregateParity ? "PASS" : "FAIL"}`,
  `DOT_MODE_SEMANTIC_PARITY=${densityParity ? "PASS" : "FAIL"}`,
  `TEXTURE_MODE_SEMANTIC_PARITY=${textureParity ? "PASS" : "FAIL"}`,
  "SPACETIME_EXPORT_PREPARATION=PASS",
  "SPACETIME_TEXTURE_HYDRATION_STABILITY=PASS",
].join(" "));
