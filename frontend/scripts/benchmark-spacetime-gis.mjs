#!/usr/bin/env node

import { gzipSync } from "node:zlib";
import { readFile, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { performance } from "node:perf_hooks";
import { geoEqualEarth, geoNaturalEarth1, geoPath } from "d3-geo";
import { feature as topojsonFeature } from "topojson-client";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(scriptDirectory, "..");

const { buildAggregateDotSeed, generateAggregateDotField, prepareAggregateDotGeometry } = await import(
  "../src/features/trace-v49/spacetime/gis/dot-density.ts"
);
const { deriveRegionAnchor } = await import("../src/features/trace-v49/spacetime/gis/geometry.ts");
const { deriveNativePatternDefinition, serializeNativePatternDefinition } = await import(
  "../src/features/trace-v49/spacetime/gis/native-pattern.ts"
);

function parseArguments(argv) {
  const options = {
    geometry110m: undefined,
    geometry50m: join(
      frontendRoot,
      "public",
      "trace-spacetime-v1",
      "natural-earth-50m-admin0-v5.1.1.geojson",
    ),
    output: undefined,
    texturesEsm: undefined,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    const value = argv[index + 1];
    if (argument === "--geometry-110m") options.geometry110m = resolve(value ?? "");
    else if (argument === "--geometry-50m") options.geometry50m = resolve(value ?? "");
    else if (argument === "--textures-esm") options.texturesEsm = resolve(value ?? "");
    else if (argument === "--output") options.output = resolve(value ?? "");
    else throw new Error(`unknown argument: ${argument}`);
    index += 1;
  }
  if (!options.geometry110m) throw new Error("--geometry-110m is required for the Natural Earth 5.1.1 scale benchmark");
  return Object.freeze(options);
}

function percentile(sorted, percentileValue) {
  const index = Math.min(sorted.length - 1, Math.max(0, Math.ceil((percentileValue / 100) * sorted.length) - 1));
  return sorted[index];
}

function round(value, digits = 3) {
  return Number(value.toFixed(digits));
}

function measure(operation, runs, warmups = 2) {
  for (let index = 0; index < warmups; index += 1) operation();
  const values = [];
  for (let index = 0; index < runs; index += 1) {
    const started = performance.now();
    operation();
    values.push(performance.now() - started);
  }
  values.sort((left, right) => left - right);
  return Object.freeze({
    runs,
    p50Ms: round(percentile(values, 50)),
    p95Ms: round(percentile(values, 95)),
    p99Ms: round(percentile(values, 99)),
    maxMs: round(values.at(-1) ?? 0),
  });
}

function geometryComplexity(collection) {
  let coordinateCount = 0;
  let ringCount = 0;
  let polygonCount = 0;
  for (const feature of collection.features) {
    const polygons = feature.geometry.type === "Polygon" ? [feature.geometry.coordinates] : feature.geometry.coordinates;
    polygonCount += polygons.length;
    for (const polygon of polygons) {
      ringCount += polygon.length;
      for (const ring of polygon) coordinateCount += ring.length;
    }
  }
  return Object.freeze({ featureCount: collection.features.length, polygonCount, ringCount, coordinateCount });
}

function projectionFactory(kind) {
  return kind === "equal-earth" ? geoEqualEarth() : geoNaturalEarth1();
}

function projectCollection(collection, kind) {
  const projection = projectionFactory(kind).precision(0.1).fitExtent(
    [
      [24, 24],
      [1416, 776],
    ],
    collection,
  );
  const path = geoPath(projection).digits(3);
  const paths = collection.features.map((feature) => path(feature) ?? "");
  return Object.freeze({ projection, paths, totalPathBytes: Buffer.byteLength(paths.join(""), "utf8") });
}

async function benchmarkGeometry(path, scale) {
  const bytes = await readFile(path);
  const sourceText = bytes.toString("utf8");
  const collection = JSON.parse(sourceText);
  const projections = {};
  for (const kind of ["equal-earth", "natural-earth-1"]) {
    const result = projectCollection(collection, kind);
    projections[kind] = {
      fit: measure(() => {
        projectionFactory(kind).precision(0.1).fitExtent(
          [
            [24, 24],
            [1416, 776],
          ],
          collection,
        );
      }, 20),
      pathGeneration: measure(() => projectCollection(collection, kind), 12, 1),
      svgPathStringBytes: result.totalPathBytes,
      areaProperty: kind === "equal-earth" ? "equal-area" : "neither-equal-area-nor-conformal",
    };
  }
  const zoomSamples = {};
  for (const featureId of ["USA", "JPN", "FJI"]) {
    const feature = collection.features.find((candidate) => candidate.id === featureId);
    if (!feature) continue;
    const projection = geoEqualEarth().precision(0.1).fitExtent(
      [
        [24, 24],
        [1416, 776],
      ],
      feature,
    );
    zoomSamples[featureId] = Buffer.byteLength(geoPath(projection).digits(3)(feature) ?? "", "utf8");
  }
  return Object.freeze({
    scale,
    rawBytes: bytes.length,
    gzipBytes: gzipSync(bytes, { level: 9, mtime: 0 }).length,
    jsonParse: measure(() => JSON.parse(sourceText), 30),
    ...geometryComplexity(collection),
    projections,
    selectedRegionZoomPathBytes: zoomSamples,
    collection,
  });
}

async function benchmarkWorldAtlas(scale) {
  const path = join(frontendRoot, "node_modules", "world-atlas", `countries-${scale}.json`);
  const bytes = await readFile(path);
  const sourceText = bytes.toString("utf8");
  const topology = JSON.parse(sourceText);
  const decoded = topojsonFeature(topology, topology.objects.countries);
  return Object.freeze({
    scale,
    sourceVersion: "Natural Earth 4.1.0",
    rawBytes: bytes.length,
    gzipBytes: gzipSync(bytes, { level: 9, mtime: 0 }).length,
    featureCount: decoded.features.length,
    topojsonDecode: measure(() => {
      const parsed = JSON.parse(sourceText);
      topojsonFeature(parsed, parsed.objects.countries);
    }, 30),
  });
}

async function benchmarkDots(collection) {
  const projection = geoEqualEarth().precision(0.1).fitExtent(
    [
      [24, 24],
      [1416, 776],
    ],
    collection,
  );
  const workloads = [
    ["USA", 500],
    ["AUS", 250],
    ["JPN", 100],
    ["FJI", 25],
    ["VAT", 7],
  ];
  const operations = workloads.map(([geometryId, recordCount]) => {
    const geometry = collection.features.find((feature) => feature.id === geometryId);
    if (!geometry) throw new Error(`dot benchmark geometry missing: ${geometryId}`);
    const anchor = deriveRegionAnchor({
      geometry,
      projection,
      geometryArtifactId: "natural-earth-admin0-countries-5.1.1-50m",
      geometryVersion: "5.1.1",
    });
    const seed = buildAggregateDotSeed({
      releaseId: "prefreeze_candidate_v48",
      geometryId,
      timeBucketId: "decade-1960",
      recordCount,
      policyVersion: "trace-dot-density-grid-v1",
    });
    const preparedGeometry = prepareAggregateDotGeometry(geometry, projection, "equal-earth:1440x800:padding-24");
    return {
      geometryId,
      recordCount,
      operation: () =>
        generateAggregateDotField({ geometry, projection, recordCount, seed, fallbackAnchor: anchor, preparedGeometry }),
    };
  });
  const perGeometry = Object.fromEntries(
    operations.map(({ geometryId, recordCount, operation }) => [
      geometryId,
      { recordCount, generation: measure(operation, 30, 2) },
    ]),
  );
  const worstFieldP95Ms = Math.max(...Object.values(perGeometry).map((value) => value.generation.p95Ms));
  const registry = JSON.parse(await readFile(
    join(frontendRoot, "generated", "trace-spacetime-v1", "geography-registry.json"),
    "utf8",
  ));
  const aggregateDocument = JSON.parse(await readFile(
    join(frontendRoot, "generated", "trace-spacetime-v1", "period-region-aggregates.json"),
    "utf8",
  ));
  const timeBuckets = JSON.parse(await readFile(
    join(frontendRoot, "generated", "trace-spacetime-v1", "time-buckets.json"),
    "utf8",
  ));
  const actualMaximumCell = aggregateDocument.periods
    .flatMap((period) => period.cells.map((cell) => ({ ...cell, periodId: period.periodId })))
    .filter((cell) => cell.mappingState === "mapped")
    .sort((left, right) => right.recordCount - left.recordCount || left.geographyId.localeCompare(right.geographyId))[0];
  const actualMaximumEntry = registry.entries.find((entry) => entry.geographyId === actualMaximumCell.geographyId);
  const actualMaximumGeometry = collection.features.find((feature) => feature.id === actualMaximumEntry?.geometryIds?.[0]);
  if (!actualMaximumEntry || !actualMaximumGeometry) throw new Error("actual maximum mapped dot field did not resolve");
  const actualMaximumAnchor = deriveRegionAnchor({
    geometry: actualMaximumGeometry,
    projection,
    geometryArtifactId: "natural-earth-admin0-countries-5.1.1-50m",
    geometryVersion: "5.1.1",
  });
  const actualMaximumSeed = buildAggregateDotSeed({
    releaseId: "v49-api-contract-fresh-c",
    geometryId: actualMaximumGeometry.id,
    timeBucketId: actualMaximumCell.periodId,
    recordCount: actualMaximumCell.recordCount,
    policyVersion: "trace-dot-density-grid-v1",
  });
  const actualMaximumPreparedGeometry = prepareAggregateDotGeometry(
    actualMaximumGeometry,
    projection,
    "equal-earth:1440x800:padding-24",
  );
  const actualMaximumOperation = () => generateAggregateDotField({
    geometry: actualMaximumGeometry,
    projection,
    recordCount: actualMaximumCell.recordCount,
    seed: actualMaximumSeed,
    fallbackAnchor: actualMaximumAnchor,
    preparedGeometry: actualMaximumPreparedGeometry,
  });
  const actualMaximumOutput = actualMaximumOperation();
  return Object.freeze({
    policyVersion: "trace-dot-density-grid-v1",
    dotUnit: 1,
    workloads: workloads.map(([geometryId, recordCount]) => ({ geometryId, recordCount })),
    perGeometry,
    worstFieldP95Ms,
    aggregateWorkload: measure(() => operations.map(({ operation }) => operation()), 30, 2),
    actualMaximumField: Object.freeze({
      periodId: actualMaximumCell.periodId,
      geographyId: actualMaximumCell.geographyId,
      geometryId: actualMaximumGeometry.id,
      recordCount: actualMaximumCell.recordCount,
      generatedDotCount: actualMaximumOutput.generatedDotCount,
      representedRecordCount: actualMaximumOutput.representedRecordCount,
      generation: measure(actualMaximumOperation, 20, 2),
    }),
    maxDotsPerPeriod: Math.max(...timeBuckets.periods.map((period) => period.recordCount)),
    deterministic: true,
    positionSemantics: "aggregate_only",
    tinyGeographyPolicy: "aggregate_anchor",
    multipartPolicy: "whole_geometry_candidate_pool",
  });
}

class MockSelection {
  constructor(node) {
    this.node = node;
  }

  append(tag) {
    const child = { tag, attributes: {}, children: [] };
    this.node.children.push(child);
    return new MockSelection(child);
  }

  attr(name, value) {
    this.node.attributes[name] = String(value);
    return this;
  }
}

function serializeMockNode(node) {
  const attributes = Object.entries(node.attributes)
    .map(([name, value]) => ` ${name}="${value}"`)
    .join("");
  return `<${node.tag}${attributes}>${node.children.map(serializeMockNode).join("")}</${node.tag}>`;
}

async function benchmarkTextures(texturesEsmPath) {
  const nativeSource = await readFile(
    join(frontendRoot, "src", "features", "trace-v49", "spacetime", "gis", "native-pattern.ts"),
  );
  const nativeDefinitions = () =>
    Array.from({ length: 100 }, (_, index) => {
      const definition = deriveNativePatternDefinition({
        namespace: "trace-spacetime-v1",
        family: ["dots", "horizontal_lines", "diagonal_lines"][index % 3],
        encodedVariable: "record_count_tier",
        legendValue: `tier-${index % 5}`,
        spacingPx: 6 + (index % 5),
        weightPx: 1,
      });
      return serializeNativePatternDefinition(definition);
    });
  const nativeSerialized = nativeDefinitions();
  const result = {
    native: {
      sourceRawBytes: nativeSource.length,
      sourceGzipBytes: gzipSync(nativeSource, { level: 9, mtime: 0 }).length,
      generation: measure(nativeDefinitions, 100, 3),
      definitions: nativeSerialized.length,
      serializedBytes: Buffer.byteLength(nativeSerialized.join(""), "utf8"),
      deterministicIds: true,
      reactDeclarative: true,
    },
    texturesJs: null,
  };
  if (!texturesEsmPath) return Object.freeze(result);

  const texturesSource = await readFile(texturesEsmPath);
  const moduleUrl = `data:text/javascript;base64,${texturesSource.toString("base64")}`;
  const textures = (await import(moduleUrl)).default;
  const textureDefinitions = () =>
    Array.from({ length: 100 }, (_, index) => {
      const root = { tag: "svg", attributes: {}, children: [] };
      const texture = textures.lines().size(6 + (index % 5)).strokeWidth(1).id(`texture-${index % 5}`);
      texture(new MockSelection(root));
      return serializeMockNode(root);
    });
  const texturesSerialized = textureDefinitions();
  result.texturesJs = {
    version: "1.2.3",
    esmRawBytes: texturesSource.length,
    esmGzipBytes: gzipSync(texturesSource, { level: 9, mtime: 0 }).length,
    generation: measure(textureDefinitions, 100, 3),
    definitions: texturesSerialized.length,
    serializedBytes: Buffer.byteLength(texturesSerialized.join(""), "utf8"),
    deterministicIdsByDefault: false,
    usesMathRandomByDefault: texturesSource.includes("Math.random"),
    requiresImperativeSelectionApi: true,
    reactDeclarative: false,
  };
  return Object.freeze(result);
}

const options = parseArguments(process.argv.slice(2));
const geometry110m = await benchmarkGeometry(options.geometry110m, "110m");
const geometry50m = await benchmarkGeometry(options.geometry50m, "50m");
const report = {
  benchmarkId: "trace-spacetime-gis-benchmark-v1",
  runtime: { node: process.version, platform: process.platform, architecture: process.arch },
  viewport: { width: 1440, height: 800, padding: 24 },
  naturalEarth: {
    version: "5.1.1",
    scales: {
      "110m": { ...geometry110m, collection: undefined },
      "50m": { ...geometry50m, collection: undefined },
    },
    decision: "50m",
    decisionRationale:
      "50m preserves materially more Admin-0 features and selected-region detail; measured costs remain suitable for one immutable fetched asset. 10m is not justified for the v1 full-world research viewport.",
  },
  worldAtlas: {
    packageVersion: "2.0.2",
    naturalEarthVersion: "4.1.0",
    scales: {
      "110m": await benchmarkWorldAtlas("110m"),
      "50m": await benchmarkWorldAtlas("50m"),
      "10m": await benchmarkWorldAtlas("10m"),
    },
    decision: "REPLACE_WITH_PINNED_NATURAL_EARTH_ARTIFACT",
    packageRetention: "LEGACY_AND_TEST_REFERENCE_ONLY",
  },
  projections: {
    default: "Equal Earth",
    alternative: "Natural Earth 1",
    rationale:
      "D3 documents Equal Earth as equal-area and Natural Earth 1 as neither conformal nor equal-area; equal-area is the defensible default for aggregate density comparison.",
  },
  dots: await benchmarkDots(geometry50m.collection),
  textures: await benchmarkTextures(options.texturesEsm),
  externalReferences: [
    "https://d3js.org/d3-geo",
    "https://d3js.org/d3-geo/path",
    "https://d3js.org/d3-geo/projection",
    "https://d3js.org/d3-geo/cylindrical",
    "https://www.naturalearthdata.com/downloads/50m-cultural-vectors/",
    "https://www.naturalearthdata.com/downloads/110m-cultural-vectors/",
    "https://www.naturalearthdata.com/about/terms-of-use/",
    "https://github.com/nvkelso/natural-earth-vector/releases/tag/v5.1.1",
    "https://github.com/topojson/world-atlas",
    "https://github.com/topojson/world-atlas/releases/tag/v2.0.2",
    "https://github.com/riccardoscalco/textures",
  ],
};

const serializedReport = `${JSON.stringify(report, null, 2)}\n`;
if (options.output) await writeFile(options.output, serializedReport);
process.stdout.write(serializedReport);
