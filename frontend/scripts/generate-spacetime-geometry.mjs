#!/usr/bin/env node

import { createHash } from "node:crypto";
import { gzipSync } from "node:zlib";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(scriptDirectory, "..");

const SOURCE_BY_SCALE = Object.freeze({
  "110m": Object.freeze({
    expectedSha256: "6866c877d39cba9c357620878839b336d569f8c662d3cfab4cb1dbe2d39c977f",
    sourceUrl:
      "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.1/geojson/ne_110m_admin_0_countries.geojson",
  }),
  "50m": Object.freeze({
    expectedSha256: "3e458fc036ad0a66411f2c1e6cac49c5d7bfb81cb1123bc513b22511a2b7fdeb",
    sourceUrl:
      "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.1/geojson/ne_50m_admin_0_countries.geojson",
  }),
});

const DEFAULT_SCALE = "50m";
const DEFAULT_PUBLIC_OUTPUT_DIRECTORY = join(frontendRoot, "public", "trace-spacetime-v1");
const DEFAULT_MANIFEST_OUTPUT_DIRECTORY = join(frontendRoot, "generated", "trace-spacetime-v1", "geometry");
const COORDINATE_PRECISION_DIGITS = 5;
const GENERATED_AT = "2026-08-23T00:00:00.000Z";

function parseArguments(argv) {
  const options = {
    check: false,
    publicOutputDirectory: DEFAULT_PUBLIC_OUTPUT_DIRECTORY,
    manifestOutputDirectory: DEFAULT_MANIFEST_OUTPUT_DIRECTORY,
    scale: DEFAULT_SCALE,
    sourcePath: undefined,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--check") {
      options.check = true;
      continue;
    }
    if (argument === "--source") {
      options.sourcePath = resolve(argv[index + 1] ?? "");
      index += 1;
      continue;
    }
    if (argument === "--output") {
      options.publicOutputDirectory = resolve(argv[index + 1] ?? "");
      index += 1;
      continue;
    }
    if (argument === "--manifest-output") {
      options.manifestOutputDirectory = resolve(argv[index + 1] ?? "");
      index += 1;
      continue;
    }
    if (argument === "--scale") {
      options.scale = argv[index + 1];
      index += 1;
      continue;
    }
    throw new Error(`Unknown argument: ${argument}`);
  }

  if (!options.sourcePath) throw new Error("--source is required; runtime downloads are forbidden");
  if (!(options.scale in SOURCE_BY_SCALE)) throw new Error(`Unsupported Natural Earth scale: ${options.scale}`);
  return Object.freeze(options);
}

function sha256(buffer) {
  return createHash("sha256").update(buffer).digest("hex");
}

function finiteNumber(value, label) {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) throw new Error(`Invalid ${label}`);
  return numericValue;
}

function nullableString(value) {
  if (value === null || value === undefined || value === "") return null;
  return String(value);
}

function roundCoordinate(value) {
  if (Array.isArray(value)) return value.map(roundCoordinate);
  const numericValue = finiteNumber(value, "geometry coordinate");
  return Number(numericValue.toFixed(COORDINATE_PRECISION_DIGITS));
}

function normalizeFeature(feature) {
  if (!feature || feature.type !== "Feature") throw new Error("Natural Earth source contains a non-Feature member");
  if (feature.geometry?.type !== "Polygon" && feature.geometry?.type !== "MultiPolygon") {
    throw new Error(`Unsupported Natural Earth geometry type: ${feature.geometry?.type ?? "missing"}`);
  }

  const sourceProperties = feature.properties ?? {};
  const neId = String(sourceProperties.NE_ID ?? "").trim();
  if (!/^\d+$/.test(neId)) throw new Error("Natural Earth feature is missing a numeric NE_ID");
  const geometryId = String(sourceProperties.ADM0_A3 ?? "").trim();
  if (!geometryId) throw new Error(`Natural Earth feature ${neId} is missing ADM0_A3`);

  return {
    type: "Feature",
    id: geometryId,
    properties: {
      geometryId,
      geometryClass: "admin0_country",
      neId,
      admin0A3: geometryId,
      isoA2: nullableString(sourceProperties.ISO_A2),
      isoA3: nullableString(sourceProperties.ISO_A3),
      isoN3: nullableString(sourceProperties.ISO_N3),
      name: String(sourceProperties.NAME ?? sourceProperties.ADMIN ?? geometryId),
      nameLong: nullableString(sourceProperties.NAME_LONG),
      admin: nullableString(sourceProperties.ADMIN),
      labelLongitude: finiteNumber(sourceProperties.LABEL_X, `${geometryId} LABEL_X`),
      labelLatitude: finiteNumber(sourceProperties.LABEL_Y, `${geometryId} LABEL_Y`),
      tinyScaleRank:
        Number.isSafeInteger(sourceProperties.TINY) && sourceProperties.TINY >= 0 ? sourceProperties.TINY : null,
    },
    geometry: {
      type: feature.geometry.type,
      coordinates: roundCoordinate(feature.geometry.coordinates),
    },
  };
}

function buildArtifact(source, scale) {
  if (!source || source.type !== "FeatureCollection" || !Array.isArray(source.features)) {
    throw new Error("Natural Earth source must be a GeoJSON FeatureCollection");
  }
  const features = source.features.map(normalizeFeature).sort((left, right) => left.id.localeCompare(right.id));
  if (new Set(features.map((feature) => feature.id)).size !== features.length) {
    throw new Error("Natural Earth NE_ID values are not unique");
  }
  return {
    type: "FeatureCollection",
    name: `natural-earth-admin0-countries-5.1.1-${scale}`,
    features,
  };
}

function serializeJson(value) {
  return Buffer.from(`${JSON.stringify(value)}\n`, "utf8");
}

async function compareOrWrite(path, expected, check) {
  if (check) {
    const actual = await readFile(path);
    if (!actual.equals(expected)) throw new Error(`Generated geometry drift: ${path}`);
    return;
  }
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, expected);
}

async function main() {
  const options = parseArguments(process.argv.slice(2));
  const sourceMetadata = SOURCE_BY_SCALE[options.scale];
  const sourceBytes = await readFile(options.sourcePath);
  const sourceSha256 = sha256(sourceBytes);
  if (sourceSha256 !== sourceMetadata.expectedSha256) {
    throw new Error(
      `Natural Earth ${options.scale} source SHA-256 mismatch: expected ${sourceMetadata.expectedSha256}, received ${sourceSha256}`,
    );
  }

  const artifact = buildArtifact(JSON.parse(sourceBytes.toString("utf8")), options.scale);
  const artifactBytes = serializeJson(artifact);
  const artifactFilename = `natural-earth-${options.scale}-admin0-v5.1.1.geojson`;
  const artifactPath = join(options.publicOutputDirectory, artifactFilename);
  const outputSha256 = sha256(artifactBytes);
  const manifest = {
    geometryArtifactId: `natural-earth-admin0-countries-5.1.1-${options.scale}`,
    source: "Natural Earth",
    sourceDataset: "Admin 0 - Countries",
    sourceVersion: "5.1.1",
    sourceScale: options.scale,
    sourceUrl: sourceMetadata.sourceUrl,
    sourceSha256,
    sourceRawBytes: sourceBytes.length,
    sourceGzipBytes: gzipSync(sourceBytes, { level: 9, mtime: 0 }).length,
    license: "Public domain",
    licenseUrl: "https://www.naturalearthdata.com/about/terms-of-use/",
    boundaryPolicy:
      "Natural Earth Admin-0 Countries uses its documented de facto boundary convention; inclusion does not express archive endorsement of a geopolitical claim.",
    conversionTool: "trace-spacetime-geometry-normalizer",
    conversionVersion: "1.0.0",
    conversionParameters: {
      coordinatePrecisionDigits: COORDINATE_PRECISION_DIGITS,
      featureIdentity: "Natural Earth ADM0_A3 (NE_ID retained as provenance)",
      featureOrder: "geometryId ascending",
      properties: [
        "geometryId",
        "geometryClass",
        "neId",
        "admin0A3",
        "isoA2",
        "isoA3",
        "isoN3",
        "name",
        "nameLong",
        "admin",
        "labelLongitude",
        "labelLatitude",
        "tinyScaleRank",
      ],
    },
    outputFormat: "GeoJSON FeatureCollection (RFC 7946 coordinate order)",
    outputFilename: artifactFilename,
    publicAssetPath: `/trace-spacetime-v1/${artifactFilename}`,
    outputSha256,
    outputRawBytes: artifactBytes.length,
    outputGzipBytes: gzipSync(artifactBytes, { level: 9, mtime: 0 }).length,
    featureCount: artifact.features.length,
    generatedAt: GENERATED_AT,
  };
  const manifestBytes = serializeJson(manifest);

  await compareOrWrite(artifactPath, artifactBytes, options.check);
  await compareOrWrite(join(options.manifestOutputDirectory, "geometry-manifest.json"), manifestBytes, options.check);

  console.log(
    `SPACETIME_GEOMETRY_GENERATION=PASS MODE=${options.check ? "CHECK" : "WRITE"} ARTIFACT_ID=${manifest.geometryArtifactId} SOURCE_SHA256=${sourceSha256} OUTPUT_SHA256=${outputSha256} FEATURE_COUNT=${artifact.features.length} RAW_BYTES=${artifactBytes.length} GZIP_BYTES=${manifest.outputGzipBytes}`,
  );
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack : error);
  process.exitCode = 1;
});
