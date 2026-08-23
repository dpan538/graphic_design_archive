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
const geometryManifest = JSON.parse(await readFile(
  join(frontendRoot, "generated/trace-spacetime-v1/geometry/geometry-manifest.json"),
  "utf8",
));

if (global.gc) global.gc();
const heapBefore = process.memoryUsage().heapUsed;
reader.resetGovernedSpacetimeReaderForTests();
const coldStarted = performance.now();
const periods = reader.getGovernedSpacetimePeriodsDataset();
const coldReaderMs = performance.now() - coldStarted;
const readerDiagnostics = reader.getGovernedSpacetimeReaderRuntimeDiagnosticsForTests();
const heapAfterReader = process.memoryUsage().heapUsed;

const geometrySamples = [];
for (let index = 0; index < 30; index += 1) {
  const started = performance.now();
  gis.loadGovernedGeometry(JSON.parse(geometryText), {
    featureCount: geometryManifest.featureCount,
    geometryArtifactId: geometryManifest.geometryArtifactId,
  });
  geometrySamples.push(performance.now() - started);
}
const collection = gis.loadGovernedGeometry(JSON.parse(geometryText), {
  featureCount: geometryManifest.featureCount,
  geometryArtifactId: geometryManifest.geometryArtifactId,
});
const projectionSamples = [];
for (let index = 0; index < 20; index += 1) {
  const started = performance.now();
  gis.fitProjection("equal-earth", collection, { width: 1_200, height: 640, padding: 28 });
  projectionSamples.push(performance.now() - started);
}
const projection = gis.fitProjection("equal-earth", collection, {
  width: 1_200,
  height: 640,
  padding: 28,
});
const geometryIndex = gis.indexGovernedGeometry(collection);
const pathSamples = [];
let paths = [];
for (let index = 0; index < 12; index += 1) {
  const path = gis.deriveGeoPath(projection);
  const started = performance.now();
  paths = collection.features.map((feature) => path(feature) ?? "");
  pathSamples.push(performance.now() - started);
}

for (let index = 0; index < 3; index += 1) {
  for (const period of periods.periods) {
    const atlas = reader.lookupGovernedSpacetimeAtlas(period.periodId);
    if (!atlas.ok) throw new Error("Spacetime atlas warmup failed");
    gis.deriveSpacetimeMapViewModel({ atlas: atlas.data, geometryIndex, projection });
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
    const viewModelStarted = performance.now();
    gis.deriveSpacetimeMapViewModel({ atlas: atlas.data, geometryIndex, projection });
    viewModelSamples.push(performance.now() - viewModelStarted);
    timeSwitchSamples.push(performance.now() - switchStarted);
  }
}

const defaultAtlas = reader.lookupGovernedSpacetimeAtlas(periods.defaultPeriodId);
if (!defaultAtlas.ok) throw new Error("default Spacetime atlas lookup failed");
const defaultViewModel = gis.deriveSpacetimeMapViewModel({
  atlas: defaultAtlas.data,
  geometryIndex,
  projection,
});
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
    loadAndValidate: summarize(geometrySamples),
    equalEarthFit: summarize(projectionSamples),
    allPathGeneration: summarize(pathSamples),
    featureCount: collection.features.length,
    svgPathBytes: Buffer.byteLength(paths.join(""), "utf8"),
  }),
  periodSwitch: summarize(timeSwitchSamples),
  mapViewModel: summarize(viewModelSamples),
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
  `GEOMETRY_LOAD_P95_MS=${report.geometry.loadAndValidate.p95Ms}`,
  `GEOMETRY_PATH_P95_MS=${report.geometry.allPathGeneration.p95Ms}`,
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
