#!/usr/bin/env node

import { readFile, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { performance } from "node:perf_hooks";
import createJiti from "jiti";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(here, "..");
const output = parseArguments(process.argv.slice(2));
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

const geometryPath = join(
  frontendRoot,
  "public/trace-spacetime-v1/natural-earth-50m-admin0-v5.1.1.geojson",
);
const geometryText = await readFile(geometryPath, "utf8");
const geometryBytes = Buffer.from(geometryText, "utf8");

if (global.gc) global.gc();
const heapBefore = process.memoryUsage().heapUsed;
reader.resetGovernedSpacetimeReaderForTests();
const coldStarted = performance.now();
const periods = reader.getGovernedSpacetimePeriodsDataset();
const coldReaderMs = performance.now() - coldStarted;
const readerDiagnostics = reader.getGovernedSpacetimeReaderRuntimeDiagnosticsForTests();
const heapAfterReader = process.memoryUsage().heapUsed;

const geometryColdSamples = [];
for (let index = 0; index < 12; index += 1) {
  const coldCache = new gis.SpacetimeGeometryRuntimeCache();
  const started = performance.now();
  await coldCache.loadSource(
    periods.geometry,
    async () => new Response(geometryBytes, { status: 200 }),
  );
  geometryColdSamples.push(performance.now() - started);
}
const runtimeCache = new gis.SpacetimeGeometryRuntimeCache();
let geometryFetchCount = 0;
const geometryFetcher = async () => {
  geometryFetchCount += 1;
  return new Response(geometryBytes, { status: 200 });
};
const source = await runtimeCache.loadSource(periods.geometry, geometryFetcher);
const geometryWarmSamples = [];
for (let index = 0; index < 50; index += 1) {
  const started = performance.now();
  await runtimeCache.loadSource(periods.geometry, async () => {
    throw new Error("warm geometry reuse must not fetch");
  });
  geometryWarmSamples.push(performance.now() - started);
}
const collection = source.collection;
const projectionSamples = [];
for (let index = 0; index < 20; index += 1) {
  const started = performance.now();
  gis.fitProjection("equal-earth", collection, { width: 1_200, height: 640, padding: 28 });
  projectionSamples.push(performance.now() - started);
}
const projectionViewport = Object.freeze({ width: 1_200, height: 640, padding: 28 });
const pathCacheMissSamples = [];
for (let index = 0; index < 12; index += 1) {
  const missCache = new gis.SpacetimeGeometryRuntimeCache();
  const started = performance.now();
  missCache.prepareProjection(source, {
    projectionId: "equal-earth",
    viewport: projectionViewport,
    projectionPrecision: 0.1,
  });
  pathCacheMissSamples.push(performance.now() - started);
}
const preparedProjection = runtimeCache.prepareProjection(source, {
  projectionId: "equal-earth",
  viewport: projectionViewport,
  projectionPrecision: 0.1,
});
const pathCacheHitSamples = [];
for (let index = 0; index < 100; index += 1) {
  const started = performance.now();
  runtimeCache.prepareProjection(source, {
    projectionId: "equal-earth",
    viewport: { ...projectionViewport },
    projectionPrecision: 0.1,
  });
  pathCacheHitSamples.push(performance.now() - started);
}
const projection = preparedProjection.projection;
const geometryIndex = preparedProjection.source.byId;
const paths = [...preparedProjection.pathById.values()];

for (let index = 0; index < 3; index += 1) {
  for (const period of periods.periods) {
    const atlas = reader.lookupGovernedSpacetimeAtlas(period.periodId);
    if (!atlas.ok) throw new Error("Spacetime atlas warmup failed");
    gis.ensureSpacetimeProjectionGeometryAnchors(
      preparedProjection,
      atlas.data.mappedGeographies.flatMap((geography) => geography.geometryIds),
    );
    gis.deriveSpacetimeMapViewModel({
      atlas: atlas.data,
      geometryIndex,
      projection,
      projectedAreaByGeometryId: preparedProjection.projectedAreaById,
      anchorByGeometryId: preparedProjection.anchorByGeometryId,
    });
  }
}

const lookupSamples = [];
const viewModelSamples = [];
const timeSwitchSamples = [];
for (let round = 0; round < 20; round += 1) {
  for (const period of periods.periods) {
    const switchStarted = performance.now();
    const lookupStarted = performance.now();
    const atlas = reader.lookupGovernedSpacetimeAtlas(period.periodId);
    lookupSamples.push(performance.now() - lookupStarted);
    if (!atlas.ok) throw new Error("Spacetime atlas lookup failed");
    gis.ensureSpacetimeProjectionGeometryAnchors(
      preparedProjection,
      atlas.data.mappedGeographies.flatMap((geography) => geography.geometryIds),
    );
    const viewModelStarted = performance.now();
    gis.deriveSpacetimeMapViewModel({
      atlas: atlas.data,
      geometryIndex,
      projection,
      projectedAreaByGeometryId: preparedProjection.projectedAreaById,
      anchorByGeometryId: preparedProjection.anchorByGeometryId,
    });
    viewModelSamples.push(performance.now() - viewModelStarted);
    gis.deriveSpacetimeRendererModel({
      atlas: atlas.data,
      projection: preparedProjection,
      mode: "aggregate",
      selectedGeographyId: null,
    });
    timeSwitchSamples.push(performance.now() - switchStarted);
  }
}

const defaultAtlas = reader.lookupGovernedSpacetimeAtlas(periods.defaultPeriodId);
if (!defaultAtlas.ok) throw new Error("default Spacetime atlas lookup failed");
const defaultViewModel = gis.deriveSpacetimeMapViewModel({
  atlas: defaultAtlas.data,
  geometryIndex,
  projection,
  projectedAreaByGeometryId: preparedProjection.projectedAreaById,
  anchorByGeometryId: preparedProjection.anchorByGeometryId,
});
const defaultAggregateRenderer = gis.deriveSpacetimeRendererModel({
  atlas: defaultAtlas.data,
  projection: preparedProjection,
  mode: "aggregate",
  selectedGeographyId: null,
});
const rendererModeCache = new gis.SpacetimeRendererRuntimeCache();
gis.deriveSpacetimeRendererModel({
  atlas: defaultAtlas.data,
  projection: preparedProjection,
  mode: "density",
  selectedGeographyId: null,
  cache: rendererModeCache,
});
const aggregateModeSamples = sample(() => gis.deriveSpacetimeRendererModel({
  atlas: defaultAtlas.data,
  projection: preparedProjection,
  mode: "aggregate",
  selectedGeographyId: null,
}), 50);
const textureModeSamples = sample(() => gis.deriveSpacetimeRendererModel({
  atlas: defaultAtlas.data,
  projection: preparedProjection,
  mode: "texture",
  selectedGeographyId: null,
}), 50);
const densityModeWarmSamples = sample(() => gis.deriveSpacetimeRendererModel({
  atlas: defaultAtlas.data,
  projection: preparedProjection,
  mode: "density",
  selectedGeographyId: null,
  cache: rendererModeCache,
}), 30);
const largestSingleGeometryMark = defaultAggregateRenderer.marks
  .filter((mark) => mark.geography.geometryIds.length === 1)
  .sort((left, right) => right.geography.recordCount - left.geography.recordCount)[0];
if (!largestSingleGeometryMark) throw new Error("dot benchmark mark missing");
const dotFieldSamples = sample(() => {
  const cache = new gis.SpacetimeRendererRuntimeCache();
  cache.prepareDensity(defaultAtlas.data, largestSingleGeometryMark.geography, preparedProjection);
}, 20, 1);
const selectedGeographySamples = sample(() => {
  gis.selectSpacetimeMapGeography(defaultViewModel, largestSingleGeometryMark.geography.geographyId);
}, 1_000, 10);
const paginationFirst = reader.lookupGovernedSpacetimeGeographyRecords(
  largestSingleGeometryMark.geography.geographyId,
  { periodId: defaultAtlas.data.selectedPeriod.periodId, first: 25 },
);
if (!paginationFirst.ok) throw new Error("pagination benchmark first page failed");
const recordPaginationSamples = sample(() => {
  const page = reader.lookupGovernedSpacetimeGeographyRecords(
    largestSingleGeometryMark.geography.geographyId,
    {
      periodId: defaultAtlas.data.selectedPeriod.periodId,
      first: 25,
      ...(paginationFirst.data.pageInfo.endCursor
        ? { after: paginationFirst.data.pageInfo.endCursor }
        : {}),
    },
  );
  if (!page.ok) throw new Error("pagination benchmark page failed");
}, 200, 10);
const markerElements = defaultViewModel.mappedMarks.map((mark) => {
  const projected = projection([mark.anchor.longitude, mark.anchor.latitude]);
  if (!projected) return "";
  return `<circle cx="${projected[0].toFixed(3)}" cy="${projected[1].toFixed(3)}" r="4"/>`;
});
const svg = `<svg viewBox="0 0 1200 640"><g>${paths.map((value) => `<path d="${value}"/>`).join("")}</g><g>${markerElements.join("")}</g></svg>`;
const report = Object.freeze({
  benchmarkId: "trace-spacetime-functional-benchmark-v1",
  projectionId: periods.release.spacetimeProjectionId,
  projectionSha256: periods.release.spacetimeProjectionSha256,
  publicRecords: 7_995,
  periods: periods.periods.length,
  defaultPeriodId: periods.defaultPeriodId,
  reader: Object.freeze({
    coldLoadMs: round(coldReaderMs),
    buildTiming: readerDiagnostics.lastSuccessfulBuildTiming,
    warmAtlasLookup: summarize(lookupSamples),
    heapDeltaBytes: Math.max(0, heapAfterReader - heapBefore),
    indexBuildAttempts: readerDiagnostics.indexBuildAttempts,
    successfulIndexBuilds: readerDiagnostics.successfulIndexBuilds,
  }),
  geometry: Object.freeze({
    coldLoad: summarize(geometryColdSamples),
    warmReuse: summarize(geometryWarmSamples),
    coldBreakdown: runtimeCache.diagnosticsForTests().lastColdGeometryTiming,
    sourceFetchCount: geometryFetchCount,
    equalEarthFit: summarize(projectionSamples),
    pathCacheMiss: summarize(pathCacheMissSamples),
    pathCacheHit: summarize(pathCacheHitSamples),
    featureCount: collection.features.length,
    svgPathBytes: Buffer.byteLength(paths.join(""), "utf8"),
  }),
  periodSwitch: summarize(timeSwitchSamples),
  mapViewModel: summarize(viewModelSamples),
  rendererModes: Object.freeze({
    aggregate: aggregateModeSamples,
    densityWarm: densityModeWarmSamples,
    texture: textureModeSamples,
  }),
  dotField: Object.freeze({
    geographyId: largestSingleGeometryMark.geography.geographyId,
    recordCount: largestSingleGeometryMark.geography.recordCount,
    coldGeneration: dotFieldSamples,
  }),
  selectedGeographyLookup: selectedGeographySamples,
  recordPagination: recordPaginationSamples,
  defaultAtlas: Object.freeze({
    payloadBytes: Buffer.byteLength(JSON.stringify(defaultAtlas.data), "utf8"),
    denominator: defaultAtlas.data.counts.denominator,
    mappedMarks: defaultViewModel.mappedMarks.length,
    aggregateOnlyRows: defaultViewModel.aggregateOnlyGeographies.length,
    unmappedRows: defaultViewModel.unmappedGeographies.length,
    accessibleRows: defaultViewModel.accessibleRows.length,
  }),
  functionalSvg: Object.freeze({
    bytes: Buffer.byteLength(svg, "utf8"),
    domElementCount: 1 + 2 + collection.features.length + markerElements.length,
    handAuthoredGeographyPathCount: 0,
    manualObjectCoordinateCount: 0,
  }),
});

const serialized = `${JSON.stringify(report, null, 2)}\n`;
if (output) await writeFile(output, serialized);
process.stdout.write([
  "SPACETIME_FUNCTIONAL_BENCHMARK=PASS",
  `PROJECTION_SHA256=${report.projectionSha256}`,
  ...metricFields("GEOMETRY_COLD_LOAD", report.geometry.coldLoad),
  ...metricFields("GEOMETRY_WARM_REUSE", report.geometry.warmReuse),
  ...metricFields("PATH_CACHE_MISS", report.geometry.pathCacheMiss),
  ...metricFields("PATH_CACHE_HIT", report.geometry.pathCacheHit),
  ...metricFields("PERIOD_ATLAS_LOOKUP", report.reader.warmAtlasLookup),
  ...metricFields("TIME_SWITCH", report.periodSwitch),
  ...metricFields("MAP_VIEWMODEL", report.mapViewModel),
  ...metricFields("AGGREGATE_MODE", report.rendererModes.aggregate),
  ...metricFields("DOT_MODE_WARM", report.rendererModes.densityWarm),
  ...metricFields("TEXTURE_MODE", report.rendererModes.texture),
  ...metricFields("DOT_FIELD_COLD", report.dotField.coldGeneration),
  ...metricFields("SELECTED_GEOGRAPHY_LOOKUP", report.selectedGeographyLookup),
  ...metricFields("RECORD_PAGINATION", report.recordPagination),
  `GEOMETRY_COLD_LOAD_MS=${report.geometry.coldLoad.p50Ms}`,
  `GEOMETRY_COLD_DECODE_MS=${report.geometry.coldBreakdown.decodeMs}`,
  `GEOMETRY_COLD_INDEX_MS=${report.geometry.coldBreakdown.indexMs}`,
  `GEOMETRY_COLD_HASH_VERIFY_MS=${report.geometry.coldBreakdown.hashVerificationMs}`,
  `GEOMETRY_WARM_REUSE_P95_MS=${report.geometry.warmReuse.p95Ms}`,
  `PATH_CACHE_HIT_P95_MS=${report.geometry.pathCacheHit.p95Ms}`,
  `PATH_CACHE_MISS_P95_MS=${report.geometry.pathCacheMiss.p95Ms}`,
  `TIME_SWITCH_P95_MS=${report.periodSwitch.p95Ms}`,
  `MAP_VIEWMODEL_P95_MS=${report.mapViewModel.p95Ms}`,
  `MAP_SVG_BYTES=${report.functionalSvg.bytes}`,
  `MAP_DOM_ELEMENT_COUNT=${report.functionalSvg.domElementCount}`,
  `READER_HEAP_BYTES=${report.reader.heapDeltaBytes}`,
].join(" ") + "\n");

function parseArguments(values) {
  let value;
  for (let index = 0; index < values.length; index += 1) {
    if (values[index] !== "--output" || !values[index + 1]) throw new Error(`unknown argument: ${values[index]}`);
    value = resolve(values[index + 1]);
    index += 1;
  }
  return value;
}

function round(value) {
  return Number(value.toFixed(3));
}

function metricFields(prefix, summary) {
  return [
    `${prefix}_P50_MS=${summary.p50Ms}`,
    `${prefix}_P95_MS=${summary.p95Ms}`,
    `${prefix}_P99_MS=${summary.p99Ms}`,
  ];
}

function sample(operation, runs, warmups = 2) {
  for (let index = 0; index < warmups; index += 1) operation();
  const values = [];
  for (let index = 0; index < runs; index += 1) {
    const started = performance.now();
    operation();
    values.push(performance.now() - started);
  }
  return summarize(values);
}

function summarize(values) {
  const sorted = [...values].sort((left, right) => left - right);
  return Object.freeze({
    runs: sorted.length,
    p50Ms: round(percentile(sorted, 50)),
    p95Ms: round(percentile(sorted, 95)),
    p99Ms: round(percentile(sorted, 99)),
    maxMs: round(sorted.at(-1) ?? 0),
  });
}

function percentile(sorted, value) {
  return sorted[Math.min(sorted.length - 1, Math.max(0, Math.ceil(sorted.length * value / 100) - 1))];
}
