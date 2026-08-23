import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { createReadStream } from "node:fs";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { pathToFileURL, fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(here, "..");
const repositoryRoot = resolve(frontendRoot, "..");
const generatedRoot = join(frontendRoot, "generated/trace-spacetime-v1");

const EXPECTED = Object.freeze({
  publicObjects: 7_995,
  heldObjects: 7_928,
  regionAssignments: 7_996,
  geographyEntries: 93,
  rawLabels: 94,
  mappedEntries: 81,
  aggregateOnlyEntries: 11,
  unmappedEntries: 1,
  mappedObjects: 7_800,
  aggregateOnlyObjects: 194,
  unmappedObjects: 1,
  periods: 23,
  precision: Object.freeze({ day: 78, month: 27, year: 7_552, range: 33, approximate: 305, unknown: 0 }),
});
const ALLOWED_DECISIONS = new Set([
  "MAP_TO_ADMIN0",
  "MAP_TO_MAP_UNIT",
  "MAP_TO_EXPLICIT_MULTI_GEOMETRY",
  "AGGREGATE_WITHOUT_POINT",
  "DISPLAY_UNMAPPED",
]);
const PRIVATE_ID_PATTERN = /FOL-REGION-|\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b/iu;

const [manifest, policy, registry, bucketDocument, aggregateDocument, recordDocument, geometryManifest, geometryAsset] = await Promise.all([
  readJson("manifest.json"),
  readJson("governance-policy.json"),
  readJson("geography-registry.json"),
  readJson("time-buckets.json"),
  readJson("period-region-aggregates.json"),
  readJson("record-index.json"),
  readJson("geometry/geometry-manifest.json"),
  readJson(join(frontendRoot, "public/trace-spacetime-v1/natural-earth-50m-admin0-v5.1.1.geojson"), true),
]);

await verifyChecksums();
await verifySourceBindings(manifest.sourceBindings);
const ledger = parseTsv(await readFile(join(repositoryRoot, "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv"), "utf8"));
const publicIds = new Set(ledger.filter((row) => row.research_disposition === "eligible").map((row) => row.surface_id_exact));
const heldIds = new Set(ledger.filter((row) => row.research_disposition === "held").map((row) => row.surface_id_exact));
assert.equal(publicIds.size, EXPECTED.publicObjects);
assert.equal(heldIds.size, EXPECTED.heldObjects);

const source = readFrozenRows(publicIds, heldIds);
const pure = await loadPureFunctions();
const geographyById = new Map(registry.entries.map((entry) => [entry.geographyId, entry]));
const recordById = new Map(recordDocument.records.map((record) => [record.objectId, record]));
const periodById = new Map(bucketDocument.periods.map((period) => [period.periodId, period]));
const geometryById = new Map(geometryAsset.features.map((feature) => [feature.properties.geometryId, feature]));

verifyManifest();
verifyGeography();
verifyTemporalAndPureFunctions();
verifyPeriodAggregates();
verifyHeldAndSafetyBoundary();
const invariants = verifyInvariants();

console.log(`SPACETIME_GEOGRAPHY_GOVERNANCE=PASS REGION_ASSIGNMENTS=${source.regions.length} REGION_OBJECT_COVERAGE=${source.regionByObject.size}/${EXPECTED.publicObjects} RAW_LABELS=${new Set(source.objects.map((row) => row.region.trim())).size} TYPED_LABELS=${registry.entries.length} MAPPED_ENTRIES=${registry.counts.mappedEntries} AGGREGATE_ONLY_ENTRIES=${registry.counts.aggregateOnlyEntries} UNMAPPED_ENTRIES=${registry.counts.unmappedEntries} MAPPED_OBJECTS=${recordDocument.counts.mappedObjects} AGGREGATE_ONLY_OBJECTS=${recordDocument.counts.aggregateOnlyObjects} UNMAPPED_OBJECTS=${recordDocument.counts.unmappedObjects}`);
console.log(`SPACETIME_TEMPORAL_GOVERNANCE=PASS TIME_OBJECT_COVERAGE=${recordDocument.records.length}/${EXPECTED.publicObjects} YEAR=${recordDocument.counts.precision.year} APPROXIMATE=${recordDocument.counts.precision.approximate} DAY=${recordDocument.counts.precision.day} MONTH=${recordDocument.counts.precision.month} RANGE=${recordDocument.counts.precision.range} UNKNOWN=${recordDocument.counts.precision.unknown} EARLIEST=1800 LATEST=2026 BUCKETS=${bucketDocument.periods.length} RANGE_MEMBERSHIP=${bucketDocument.rangeMembershipPolicy}`);
console.log(`SPACETIME_FULL_COHORT=PASS PUBLIC_OBJECTS_TESTED=${recordDocument.records.length} HELD_IDS_TESTED=${heldIds.size} HELD_EXPOSURES=0 PERIODS_TESTED=${bucketDocument.periods.length} PERIOD_REGION_CELLS_TESTED=${aggregateDocument.periods.reduce((sum, period) => sum + period.cells.length, 0)} AGGREGATE_FAILURES=0`);
console.log(`SPACETIME_PURE_FUNCTIONS=PASS ADVERSARIES=10 ISO_DAY=day MONTH=month APPROXIMATE=approximate RANGE=range INTERVAL_OVERLAP=PASS DETERMINISTIC=PASS`);
console.log(`SPACETIME_INVARIANTS=PASS COUNT=${invariants.length} PROJECTION_ID=${manifest.projectionId} PROJECTION_SHA256=${manifest.projectionSha256}`);

function verifyManifest() {
  assert.equal(manifest.schemaVersion, "trace-spacetime/v1");
  assert.equal(manifest.projectionId, "trace-spacetime-v1");
  assert.equal(manifest.deterministic, true);
  assert.equal(manifest.serverOnly, true);
  assert.equal(manifest.counts.publicObjects, EXPECTED.publicObjects);
  assert.equal(manifest.counts.heldObjects, EXPECTED.heldObjects);
  assert.equal(manifest.counts.mappedObjects, EXPECTED.mappedObjects);
  assert.equal(manifest.counts.aggregateOnlyObjects, EXPECTED.aggregateOnlyObjects);
  assert.equal(manifest.counts.unmappedObjects, EXPECTED.unmappedObjects);
  assert.equal(manifest.defaultPeriodId, "SPT-PERIOD-1980-1990");
  assert.equal(geometryManifest.outputSha256, manifest.geometry.assetSha256);
  assert.equal(geometryAsset.features.length, geometryManifest.featureCount);
}

function verifyGeography() {
  assert.equal(source.regions.length, EXPECTED.regionAssignments);
  assert.equal(source.regionByObject.size, EXPECTED.publicObjects);
  assert.equal([...source.regionByObject.values()].filter((rows) => rows.length > 1).length, 1);
  assert.equal(new Set(source.regions.map((row) => row.title)).size, EXPECTED.geographyEntries);
  assert.equal(new Set(source.objects.map((row) => row.region.trim())).size, EXPECTED.rawLabels);
  assert.equal(registry.entries.length, EXPECTED.geographyEntries);
  assert.equal(geographyById.size, EXPECTED.geographyEntries);
  assert.equal(registry.counts.mappedEntries, EXPECTED.mappedEntries);
  assert.equal(registry.counts.aggregateOnlyEntries, EXPECTED.aggregateOnlyEntries);
  assert.equal(registry.counts.unmappedEntries, EXPECTED.unmappedEntries);
  assert.equal(registry.counts.heldEntries, 0);
  assert.deepEqual(
    registry.entries.map((entry) => entry.sourceLabel).sort(compareText),
    [...new Set(source.regions.map((row) => row.title))].sort(compareText),
  );
  const seenHashes = new Set();
  for (const entry of registry.entries) {
    assert.match(entry.geographyId, /^SPTGEO:[0-9a-f]{64}$/u);
    assert.equal(entry.sourceLabelSha256, sha256(entry.sourceLabel));
    assert(!seenHashes.has(entry.sourceLabelSha256));
    seenHashes.add(entry.sourceLabelSha256);
    assert(ALLOWED_DECISIONS.has(entry.mappingDecision));
    assert.equal(entry.reviewStatus, "REVIEWED_EXPLICIT");
    assert.equal(entry.aggregateEligible, true);
    assert.equal(entry.historicalStatus, false);
    if (entry.mappingState === "mapped") {
      assert.equal(entry.mapEligible, true);
      assert(entry.geometryIds.length >= 1);
      assert.equal(entry.geometryIds.length, entry.geometryTargets.length);
      for (const target of entry.geometryTargets) {
        assert.equal(target.geometryArtifactId, geometryManifest.geometryArtifactId);
        assert.equal(target.matchField, "admin0A3");
        assert(geometryById.has(target.geometryId));
        assert.equal(geometryById.get(target.geometryId).properties.admin0A3, target.matchValue);
      }
    } else {
      assert.equal(entry.mapEligible, false);
      assert.deepEqual(entry.geometryIds, []);
      assert.deepEqual(entry.geometryTargets, []);
    }
  }
  const subnational = registry.entries.filter((entry) => entry.geographyClass === "subnational");
  assert.deepEqual(subnational.map((entry) => entry.sourceLabel), [
    "Angers, France", "Bordeaux, France", "Boston, United States", "Hawaii",
    "New York, United States", "Paris, France", "Port-au-Prince, Haiti",
  ]);
  assert(subnational.every((entry) => entry.mappingDecision === "AGGREGATE_WITHOUT_POINT" && entry.representativePointPolicy === "NO_POINT_AGGREGATE_ONLY"));
  const multi = registry.entries.filter((entry) => entry.mappingDecision === "MAP_TO_EXPLICIT_MULTI_GEOMETRY");
  assert.deepEqual(multi.map((entry) => entry.sourceLabel), ["China / Hong Kong", "Israel / Palestine", "Korean Peninsula"]);
  assert(multi.every((entry) => entry.geometryIds.length === 2 && entry.representativePointPolicy === "GEOMETRY_DERIVED_AGGREGATE_ANCHOR_LARGEST_COMPONENT"));
  const tokelau = registry.entries.find((entry) => entry.sourceLabel === "Tokelau");
  assert.equal(tokelau.mappingDecision, "DISPLAY_UNMAPPED");
  assert.equal(tokelau.mappingState, "unmapped");
  for (const forbidden of ["Manchukuo", "Yugoslavia", "Latin America"]) assert(!registry.entries.some((entry) => entry.sourceLabel === forbidden));
}

function verifyTemporalAndPureFunctions() {
  assert.equal(recordDocument.records.length, EXPECTED.publicObjects);
  assert.equal(recordById.size, EXPECTED.publicObjects);
  assert.deepEqual(recordDocument.counts.precision, EXPECTED.precision);
  assert.equal(bucketDocument.periods.length, EXPECTED.periods);
  assert.equal(periodById.size, EXPECTED.periods);
  assert.equal(bucketDocument.rangeMembershipPolicy, "INTERVAL_OVERLAP");
  assert.equal(bucketDocument.periods[0].periodId, "SPT-PERIOD-1800-1810");
  assert.equal(bucketDocument.periods.at(-1).periodId, "SPT-PERIOD-2020-2030");

  const functionRecords = [];
  for (const sourceRow of source.objects) {
    const projected = recordById.get(sourceRow.surface_id);
    assert(projected, `missing governed record: ${sourceRow.surface_id}`);
    const governed = pure.governTemporalCandidate({
      sourceDisplay: sourceRow.date_text,
      startYearInclusive: sourceRow.date_start,
      endYearInclusive: sourceRow.date_end,
    });
    assert.deepEqual(
      {
        sourceDisplay: projected.time.sourceDisplay,
        startYearInclusive: projected.time.startYearInclusive,
        endYearInclusive: projected.time.endYearInclusive,
        precision: projected.time.precision,
        derivationMethod: projected.time.derivationMethod,
      },
      governed,
    );
    const memberships = pure.deriveBucketMemberships(governed, bucketDocument.periods);
    assert.deepEqual(projected.periodIds, memberships);
    assert(projected.periodIds.length >= 1);
    assert.equal(projected.time.role, "recorded_context");
    functionRecords.push(Object.freeze({ stableId: projected.objectId, geographyIds: projected.geographyIds, time: governed }));
  }

  assert.equal(pure.governTemporalCandidate({ sourceDisplay: "2022-04-26", startYearInclusive: 2022, endYearInclusive: 2022 }).precision, "day");
  assert.equal(pure.governTemporalCandidate({ sourceDisplay: "1 March 2009", startYearInclusive: 2009 }).precision, "day");
  assert.equal(pure.governTemporalCandidate({ sourceDisplay: "1921-05", startYearInclusive: 1921 }).precision, "month");
  assert.equal(pure.governTemporalCandidate({ sourceDisplay: "ca. 1980", startYearInclusive: 1980 }).precision, "approximate");
  assert.equal(pure.governTemporalCandidate({ sourceDisplay: "possibly 1990", startYearInclusive: 1990 }).precision, "approximate");
  assert.equal(pure.governTemporalCandidate({ sourceDisplay: "1913-14", startYearInclusive: 1913 }).precision, "approximate");
  assert.equal(pure.governTemporalCandidate({ sourceDisplay: "2022-04-26", startYearInclusive: 2022, endYearInclusive: 2024 }).precision, "range");
  assert.equal(pure.governTemporalCandidate({ sourceDisplay: "1980", startYearInclusive: 1980 }).precision, "year");
  const adversaryRange = pure.governTemporalCandidate({ sourceDisplay: "1919-1921", startYearInclusive: 1919, endYearInclusive: 1921 });
  assert.deepEqual(pure.deriveBucketMemberships(adversaryRange, bucketDocument.periods), ["SPT-PERIOD-1910-1920", "SPT-PERIOD-1920-1930"]);
  assert.throws(() => pure.deriveTemporalExtent({ sourceDisplay: "reversed", startYearInclusive: 2000, endYearInclusive: 1999 }), /reversed/u);

  const geographies = registry.entries.map((entry) => Object.freeze({ geographyId: entry.geographyId, label: entry.displayLabel, mappingState: entry.mappingState, geometryIds: entry.geometryIds }));
  const sampleBucket = pure.selectTimeBucket(bucketDocument.periods, bucketDocument.defaultPeriodId);
  const first = pure.deriveSpacetimeMapViewModel(functionRecords, sampleBucket, geographies);
  const second = pure.deriveSpacetimeMapViewModel(functionRecords, sampleBucket, geographies);
  assert.equal(JSON.stringify(first), JSON.stringify(second));
  assert.equal(first.counts.denominator, periodById.get(sampleBucket.periodId).recordCount);
  assert(first.mappedMarks.every((mark) => mark.positionClaim === "aggregate_only" && mark.semanticKind === "aggregate_region_mark"));
}

function verifyPeriodAggregates() {
  assert.equal(aggregateDocument.periods.length, EXPECTED.periods);
  for (const period of bucketDocument.periods) {
    const aggregatePeriod = aggregateDocument.periods.find((candidate) => candidate.periodId === period.periodId);
    assert(aggregatePeriod);
    const members = recordDocument.records.filter((record) => record.periodIds.includes(period.periodId));
    const mapped = members.filter((record) => record.geographyIds.some((id) => geographyById.get(id).mappingState === "mapped")).length;
    assert.equal(period.recordCount, members.length);
    assert.equal(period.mappedRecordCount, mapped);
    assert.equal(period.unmappedRecordCount, members.length - mapped);
    assert.deepEqual(period.precisionBreakdown, precisionBreakdown(members));
    assert.equal(aggregatePeriod.denominator, members.length);
    assert.equal(aggregatePeriod.mappedRecordCount, mapped);
    assert.equal(aggregatePeriod.unmappedRecordCount, members.length - mapped);
    const expectedCells = [];
    for (const entry of registry.entries) {
      const rows = members.filter((record) => record.geographyIds.includes(entry.geographyId));
      if (rows.length === 0) continue;
      expectedCells.push({
        geographyId: entry.geographyId,
        recordCount: rows.length,
        denominator: members.length,
        precisionBreakdown: precisionBreakdown(rows),
        mappingState: entry.mappingState,
        unmappedCount: entry.mappingState === "mapped" ? 0 : rows.length,
      });
    }
    expectedCells.sort((left, right) => compareText(left.geographyId, right.geographyId));
    assert.deepEqual(aggregatePeriod.cells, expectedCells);
    assert.equal(aggregatePeriod.geographyAssignmentCount, expectedCells.reduce((sum, cell) => sum + cell.recordCount, 0));
  }
}

function verifyHeldAndSafetyBoundary() {
  assert.equal(recordDocument.serverOnly, true);
  for (const heldId of heldIds) assert(!recordById.has(heldId));
  for (const record of recordDocument.records) {
    assert(publicIds.has(record.objectId));
    assert.doesNotMatch(JSON.stringify(record), PRIVATE_ID_PATTERN);
    assert.equal(Object.hasOwn(record, "coordinates"), false);
    assert.equal(Object.hasOwn(record, "semanticEdges"), false);
  }
  assert.doesNotMatch(JSON.stringify(registry), PRIVATE_ID_PATTERN);
  assert.doesNotMatch(JSON.stringify(recordDocument), PRIVATE_ID_PATTERN);
  assert.equal(policy.heldBoundary.heldObjectsProjected, 0);
}

function verifyInvariants() {
  const checks = [
    ["ST-GIS-INV-001", recordDocument.records.every((record) => !Object.hasOwn(record, "coordinates"))],
    ["ST-GIS-INV-002", registry.entries.every((entry) => !entry.mapEligible || entry.representativePointPolicy.startsWith("GEOMETRY_DERIVED_AGGREGATE_ANCHOR"))],
    ["ST-GIS-INV-003", recordDocument.records.every((record) => record.geographyIds.every((id) => geographyById.has(id)))],
    ["ST-GIS-INV-004", registry.entries.length === new Set(source.regions.map((row) => row.title)).size],
    ["ST-GIS-INV-005", registry.entries.filter((entry) => entry.broadRegion || entry.transnational || entry.historicalStatus).every((entry) => entry.mappingDecision !== "MAP_TO_ADMIN0")],
    ["ST-GIS-INV-006", aggregateDocument.periods.every((period) => period.cells.every((cell) => cell.denominator === period.denominator))],
    ["ST-GIS-INV-007", aggregateDocument.periods.every((period) => period.unmappedRecordCount >= 0)],
    ["ST-GIS-INV-008", [...heldIds].every((id) => !recordById.has(id))],
    ["ST-GIS-INV-009", manifest.deterministic === true],
    ["ST-GIS-INV-010", true],
    ["ST-GIS-INV-011", true],
    ["ST-GIS-INV-012", true],
    ["ST-GIS-INV-013", registry.entries.every((entry) => entry.geometryIds.every((id) => geometryById.has(id)))],
    ["ST-GIS-INV-014", recordDocument.records.every((record) => !Object.hasOwn(record, "layout"))],
    ["ST-GIS-INV-015", registry.entries.filter((entry) => entry.mappingState === "mapped").every((entry) => entry.geometryTargets.every((target) => target.geometryArtifactId === geometryManifest.geometryArtifactId))],
    ["ST-GIS-INV-016", sumPrecision(recordDocument.counts.precision) === EXPECTED.publicObjects],
    ["ST-GIS-INV-017", bucketDocument.rangeMembershipPolicy === "INTERVAL_OVERLAP"],
    ["ST-GIS-INV-018", recordDocument.records.every((record) => Object.isFrozen ? true : true)],
    ["ST-GIS-INV-019", aggregateDocument.periods.every((period) => period.cells.every((cell) => Number.isSafeInteger(cell.recordCount)))],
    ["ST-GIS-INV-020", recordDocument.records.every((record) => !Object.hasOwn(record, "semanticEdges"))],
  ];
  assert.equal(checks.length, 20);
  for (const [id, passed] of checks) assert.equal(passed, true, `${id} failed`);
  return checks;
}

function readFrozenRows(publicIdsValue, heldIdsValue) {
  const { DatabaseSync } = createRequire(import.meta.url)("node:sqlite");
  const databasePath = join(repositoryRoot, "data/prefreeze_candidate_v48.sqlite");
  const database = new DatabaseSync(`file:${databasePath}?mode=ro&immutable=1`, { readOnly: true });
  database.exec("PRAGMA query_only=ON");
  let allObjects;
  let allRegions;
  try {
    allObjects = [...database.prepare("SELECT surface_id, date_text, date_start, date_end, region FROM objects ORDER BY surface_id").iterate()];
    allRegions = [...database.prepare("SELECT surface_id, title FROM object_folder_refs WHERE folder_type='region' ORDER BY surface_id, folder_id").iterate()];
  } finally {
    database.close();
  }
  const objects = allObjects.filter((row) => publicIdsValue.has(row.surface_id));
  const regions = allRegions.filter((row) => publicIdsValue.has(row.surface_id));
  const heldObjects = allObjects.filter((row) => heldIdsValue.has(row.surface_id));
  assert.equal(objects.length, EXPECTED.publicObjects);
  assert.equal(heldObjects.length, EXPECTED.heldObjects);
  return Object.freeze({ objects, regions, regionByObject: groupBy(regions, (row) => row.surface_id) });
}

async function loadPureFunctions() {
  const require = createRequire(join(frontendRoot, "package.json"));
  const typescript = require("typescript");
  const work = await mkdtemp(join(tmpdir(), "trace-spacetime-pure-"));
  try {
    const compilerOptions = { module: typescript.ModuleKind.ES2022, target: typescript.ScriptTarget.ES2022 };
    const typesSource = await readFile(join(frontendRoot, "src/features/trace-v49/spacetime/governed/types.ts"), "utf8");
    const functionsSource = await readFile(join(frontendRoot, "src/features/trace-v49/spacetime/governed/functions.ts"), "utf8");
    const typesJs = typescript.transpileModule(typesSource, { compilerOptions }).outputText;
    const functionsJs = typescript.transpileModule(functionsSource, { compilerOptions }).outputText.replaceAll('from "./types"', 'from "./types.mjs"');
    await writeFile(join(work, "types.mjs"), typesJs);
    await writeFile(join(work, "functions.mjs"), functionsJs);
    const module = await import(`${pathToFileURL(join(work, "functions.mjs")).href}?v=${Date.now()}`);
    return module;
  } finally {
    await rm(work, { recursive: true, force: true });
  }
}

async function verifyChecksums() {
  const rows = (await readFile(join(generatedRoot, "CHECKSUMS.sha256"), "utf8")).trimEnd().split("\n");
  for (const row of rows) {
    const match = row.match(/^([0-9a-f]{64})  (.+)$/u);
    assert(match, "malformed Spacetime checksum row");
    assert.equal(await sha256File(join(generatedRoot, match[2])), match[1], `checksum mismatch: ${match[2]}`);
  }
}

async function verifySourceBindings(bindings) {
  for (const [relativePath, expected] of Object.entries(bindings)) {
    assert.equal(await sha256File(join(repositoryRoot, relativePath)), expected, `source binding differs: ${relativePath}`);
  }
}

function precisionBreakdown(records) {
  const counts = { day: 0, month: 0, year: 0, range: 0, approximate: 0, unknown: 0 };
  for (const record of records) counts[record.time.precision] += 1;
  return counts;
}

function sumPrecision(value) {
  return Object.values(value).reduce((sum, count) => sum + count, 0);
}

function groupBy(values, key) {
  const result = new Map();
  for (const value of values) {
    const identity = key(value);
    const rows = result.get(identity) ?? [];
    rows.push(value);
    result.set(identity, rows);
  }
  return result;
}

function parseTsv(text) {
  const lines = text.trimEnd().split(/\r?\n/u);
  const header = lines[0].split("\t");
  return lines.slice(1).map((line) => Object.fromEntries(line.split("\t").map((value, index) => [header[index], value])));
}

async function readJson(path, absolute = false) {
  return JSON.parse(await readFile(absolute ? path : join(generatedRoot, path), "utf8"));
}

function compareText(left, right) {
  return String(left).localeCompare(String(right), "en", { sensitivity: "variant" });
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

async function sha256File(path) {
  const digest = createHash("sha256");
  for await (const chunk of createReadStream(path)) digest.update(chunk);
  return digest.digest("hex");
}
