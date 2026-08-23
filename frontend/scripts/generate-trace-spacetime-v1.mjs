import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { createReadStream } from "node:fs";
import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(here, "..");
const repositoryRoot = resolve(frontendRoot, "..");
const outputDirectory = join(frontendRoot, "generated/trace-spacetime-v1");
const geometryManifestPath = join(outputDirectory, "geometry/geometry-manifest.json");
const geometryAssetPath = join(frontendRoot, "public/trace-spacetime-v1/natural-earth-50m-admin0-v5.1.1.geojson");

const args = process.argv.slice(2);
const checkOnly = args.includes("--check");
assert.deepEqual(args.filter((arg) => arg !== "--check"), [], "unknown generator argument");

const SCHEMA_VERSION = "trace-spacetime/v1";
const PROJECTION_ID = "trace-spacetime-v1";
const GENERATOR_VERSION = "trace-spacetime-projection-generator-v1";
const ID_POLICY_VERSION = "trace-spacetime-public-id-v1";
const GEOGRAPHY_ID_NAMESPACE = "trace-spacetime-geography-id-v1";
const TIME_ID_NAMESPACE = "trace-spacetime-time-observation-v1";
const GEOGRAPHY_POLICY_VERSION = "spacetime-geography-governance-v1";
const TEMPORAL_POLICY_VERSION = "spacetime-temporal-governance-v1";
const BUCKET_POLICY = "DECADE";
const RANGE_MEMBERSHIP_POLICY = "INTERVAL_OVERLAP";
const TEMPORAL_DERIVATION_METHOD = "FROZEN_YEAR_EXTENT_AND_LEXICAL_PRECISION_V1";
const CANONICAL_SERIALIZATION = "recursive-key-sort;array-order-preserved;json-minified;final-lf;utf8";
const GENERATED_AT = "2026-08-23T00:00:00.000Z";

const SOURCE_RELEASE = Object.freeze({
  researchReleaseId: "v49-api-contract-fresh-c",
  researchManifestSha256: "4addfdb3cb9314587908096572242b9d63e9cef9e6e1be68c0c646491a43a90a",
});
const SOURCE_BINDINGS = Object.freeze({
  "data/prefreeze_candidate_v48.sqlite": "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e",
  "database/FREEZE_V49.json": "f0dda59dd515ba243eaf213bce9f42513727f1ab0a44685635921c3759a7d22e",
  "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv": "48f98f68ca2ec0cef96c82ecc9c01e4129eb9a3f91e08b07ad9a59644a9d4e01",
  "docs/statistics/v49-release-data-profile.json": "091dba486c2096f99c332b03cf9586139f1bc26594bce4e1575d2b1ddc8fea0f",
});
const EXPECTED = Object.freeze({
  canonicalObjects: 15_923,
  publicObjects: 7_995,
  heldObjects: 7_928,
  publicRegionAssignments: 7_996,
  publicRegionObjects: 7_995,
  publicTypedRegionLabels: 93,
  publicRawRegionLabels: 94,
  multiRegionObjects: 1,
  year: 7_552,
  approximate: 305,
  day: 78,
  month: 27,
  range: 33,
  unknown: 0,
  earliestYear: 1800,
  latestYear: 2026,
  bucketCount: 23,
});
const MONTH_NAME = "(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)";
const NATURAL_DAY_RE = new RegExp(`^(?:\\d{1,2}[\\/-]\\d{1,2}[\\/-]\\d{4}|\\d{1,2}\\s+${MONTH_NAME}\\s+\\d{4}|${MONTH_NAME}\\s+\\d{1,2},\\s*\\d{4})$`, "iu");
const NATURAL_MONTH_RE = new RegExp(`^(?:${MONTH_NAME}\\s+\\d{4}|\\d{1,2}[\\/-]\\d{4})$`, "iu");

// Every public typed-region label has one explicit, reviewed decision. The
// controlled folder identity is used only as private hash material and is never
// serialized. Subnational labels remain aggregate-only because this release has
// no evidence-backed point or subnational geometry.
const GEOGRAPHY_DECISIONS = Object.freeze([
  ["Angers, France", "subnational", "AGGREGATE_WITHOUT_POINT", []],
  ["Aotearoa New Zealand", "country", "MAP_TO_ADMIN0", ["NZL"]],
  ["Argentina", "country", "MAP_TO_ADMIN0", ["ARG"]],
  ["Australia", "country", "MAP_TO_ADMIN0", ["AUS"]],
  ["Australia / Indigenous", "broad_region", "AGGREGATE_WITHOUT_POINT", []],
  ["Austria", "country", "MAP_TO_ADMIN0", ["AUT"]],
  ["Bangladesh", "country", "MAP_TO_ADMIN0", ["BGD"]],
  ["Belgium", "country", "MAP_TO_ADMIN0", ["BEL"]],
  ["Bordeaux, France", "subnational", "AGGREGATE_WITHOUT_POINT", []],
  ["Boston, United States", "subnational", "AGGREGATE_WITHOUT_POINT", []],
  ["Brazil", "country", "MAP_TO_ADMIN0", ["BRA"]],
  ["Canada", "country", "MAP_TO_ADMIN0", ["CAN"]],
  ["Chile", "country", "MAP_TO_ADMIN0", ["CHL"]],
  ["China / Hong Kong", "transnational", "MAP_TO_EXPLICIT_MULTI_GEOMETRY", ["CHN", "HKG"]],
  ["Cook Islands", "territory", "MAP_TO_MAP_UNIT", ["COK"]],
  ["Cuba / transnational", "transnational", "AGGREGATE_WITHOUT_POINT", []],
  ["Czech Republic", "country", "MAP_TO_ADMIN0", ["CZE"]],
  ["Denmark", "country", "MAP_TO_ADMIN0", ["DNK"]],
  ["Dominican Republic", "country", "MAP_TO_ADMIN0", ["DOM"]],
  ["Egypt", "country", "MAP_TO_ADMIN0", ["EGY"]],
  ["El Salvador", "country", "MAP_TO_ADMIN0", ["SLV"]],
  ["Estonia", "country", "MAP_TO_ADMIN0", ["EST"]],
  ["Federated States of Micronesia", "country", "MAP_TO_ADMIN0", ["FSM"]],
  ["Fiji", "country", "MAP_TO_ADMIN0", ["FJI"]],
  ["Finland", "country", "MAP_TO_ADMIN0", ["FIN"]],
  ["France", "country", "MAP_TO_ADMIN0", ["FRA"]],
  ["Georgia", "country", "MAP_TO_ADMIN0", ["GEO"]],
  ["Germany", "country", "MAP_TO_ADMIN0", ["DEU"]],
  ["Ghana", "country", "MAP_TO_ADMIN0", ["GHA"]],
  ["Global / transnational", "broad_region", "AGGREGATE_WITHOUT_POINT", []],
  ["Greece", "country", "MAP_TO_ADMIN0", ["GRC"]],
  ["Guatemala", "country", "MAP_TO_ADMIN0", ["GTM"]],
  ["Hawaii", "subnational", "AGGREGATE_WITHOUT_POINT", []],
  ["Hungary", "country", "MAP_TO_ADMIN0", ["HUN"]],
  ["India", "country", "MAP_TO_ADMIN0", ["IND"]],
  ["Indonesia", "country", "MAP_TO_ADMIN0", ["IDN"]],
  ["Iran", "country", "MAP_TO_ADMIN0", ["IRN"]],
  ["Iraq", "country", "MAP_TO_ADMIN0", ["IRQ"]],
  ["Ireland", "country", "MAP_TO_ADMIN0", ["IRL"]],
  ["Israel / Palestine", "transnational", "MAP_TO_EXPLICIT_MULTI_GEOMETRY", ["ISR", "PSX"]],
  ["Italy", "country", "MAP_TO_ADMIN0", ["ITA"]],
  ["Japan", "country", "MAP_TO_ADMIN0", ["JPN"]],
  ["Jordan", "country", "MAP_TO_ADMIN0", ["JOR"]],
  ["Kiribati", "country", "MAP_TO_ADMIN0", ["KIR"]],
  ["Korean Peninsula", "transnational", "MAP_TO_EXPLICIT_MULTI_GEOMETRY", ["KOR", "PRK"]],
  ["Lebanon", "country", "MAP_TO_ADMIN0", ["LBN"]],
  ["Malaysia", "country", "MAP_TO_ADMIN0", ["MYS"]],
  ["Marshall Islands", "country", "MAP_TO_ADMIN0", ["MHL"]],
  ["Mexico", "country", "MAP_TO_ADMIN0", ["MEX"]],
  ["Nauru", "country", "MAP_TO_ADMIN0", ["NRU"]],
  ["Netherlands", "country", "MAP_TO_ADMIN0", ["NLD"]],
  ["New Caledonia", "territory", "MAP_TO_MAP_UNIT", ["NCL"]],
  ["New York, United States", "subnational", "AGGREGATE_WITHOUT_POINT", []],
  ["Nicaragua", "country", "MAP_TO_ADMIN0", ["NIC"]],
  ["Nigeria", "country", "MAP_TO_ADMIN0", ["NGA"]],
  ["Niue", "territory", "MAP_TO_MAP_UNIT", ["NIU"]],
  ["Norway", "country", "MAP_TO_ADMIN0", ["NOR"]],
  ["Pakistan", "country", "MAP_TO_ADMIN0", ["PAK"]],
  ["Palau", "country", "MAP_TO_ADMIN0", ["PLW"]],
  ["Palestine / transnational", "transnational", "AGGREGATE_WITHOUT_POINT", []],
  ["Papua New Guinea", "country", "MAP_TO_ADMIN0", ["PNG"]],
  ["Paraguay", "country", "MAP_TO_ADMIN0", ["PRY"]],
  ["Paris, France", "subnational", "AGGREGATE_WITHOUT_POINT", []],
  ["Peru", "country", "MAP_TO_ADMIN0", ["PER"]],
  ["Poland", "country", "MAP_TO_ADMIN0", ["POL"]],
  ["Port-au-Prince, Haiti", "subnational", "AGGREGATE_WITHOUT_POINT", []],
  ["Portugal", "country", "MAP_TO_ADMIN0", ["PRT"]],
  ["Puerto Rico", "territory", "MAP_TO_MAP_UNIT", ["PRI"]],
  ["Romania", "country", "MAP_TO_ADMIN0", ["ROU"]],
  ["Russia", "country", "MAP_TO_ADMIN0", ["RUS"]],
  ["Samoa", "country", "MAP_TO_ADMIN0", ["WSM"]],
  ["Serbia", "country", "MAP_TO_ADMIN0", ["SRB"]],
  ["Singapore", "country", "MAP_TO_ADMIN0", ["SGP"]],
  ["Solomon Islands", "country", "MAP_TO_ADMIN0", ["SLB"]],
  ["South Africa", "country", "MAP_TO_ADMIN0", ["ZAF"]],
  ["Spain", "country", "MAP_TO_ADMIN0", ["ESP"]],
  ["Sweden", "country", "MAP_TO_ADMIN0", ["SWE"]],
  ["Switzerland", "country", "MAP_TO_ADMIN0", ["CHE"]],
  ["Syria", "country", "MAP_TO_ADMIN0", ["SYR"]],
  ["Thailand", "country", "MAP_TO_ADMIN0", ["THA"]],
  ["Tokelau", "territory", "DISPLAY_UNMAPPED", []],
  ["Tonga", "country", "MAP_TO_ADMIN0", ["TON"]],
  ["Turkey", "country", "MAP_TO_ADMIN0", ["TUR"]],
  ["Tuvalu", "country", "MAP_TO_ADMIN0", ["TUV"]],
  ["Ukraine", "country", "MAP_TO_ADMIN0", ["UKR"]],
  ["United Kingdom", "country", "MAP_TO_ADMIN0", ["GBR"]],
  ["United States", "country", "MAP_TO_ADMIN0", ["USA"]],
  ["Uruguay", "country", "MAP_TO_ADMIN0", ["URY"]],
  ["Vanuatu", "country", "MAP_TO_ADMIN0", ["VUT"]],
  ["Venezuela", "country", "MAP_TO_ADMIN0", ["VEN"]],
  ["Vietnam", "country", "MAP_TO_ADMIN0", ["VNM"]],
  ["Wallis and Futuna", "territory", "MAP_TO_MAP_UNIT", ["WLF"]],
  ["Zimbabwe", "country", "MAP_TO_ADMIN0", ["ZWE"]],
]);

try {
  const built = await buildProjection();
  if (checkOnly) await checkProjection(built);
  else await writeProjection(built);
} catch (error) {
  console.error(`TRACE_SPACETIME_V1_GENERATION=FAIL ERROR=${safeError(error)}`);
  process.exitCode = 1;
}

async function buildProjection() {
  await verifySourceBindings();
  const source = await readFrozenSource();
  const geometry = await readGeometry();
  const geography = buildGeographyRegistry(source, geometry);
  const records = buildRecords(source, geography);
  const buckets = buildTimeBuckets(records, geography);
  const aggregates = buildPeriodRegionAggregates(records, geography, buckets);
  const policy = buildGovernancePolicy(source, geography);

  const payloads = new Map([
    ["geography-registry.json", canonicalBytes(geography.document)],
    ["governance-policy.json", canonicalBytes(policy)],
    ["period-region-aggregates.json", canonicalBytes(aggregates)],
    ["record-index.json", canonicalBytes(records.document)],
    ["time-buckets.json", canonicalBytes(buckets.document)],
  ]);
  const payloadHashes = Object.fromEntries([...payloads].sort(([a], [b]) => compareText(a, b)).map(([name, bytes]) => [name, sha256(bytes)]));
  const projectionSha256 = sha256(canonicalBytes({
    projectionId: PROJECTION_ID,
    payloadHashes,
    geometryManifestSha256: sha256(await readFile(geometryManifestPath)),
    geometryAssetSha256: geometry.manifest.outputSha256,
  }));
  const manifest = buildManifest({ source, geography, records, buckets, aggregates, geometry, payloadHashes, projectionSha256 });
  payloads.set("manifest.json", canonicalBytes(manifest));
  const geometryManifestBytes = await readFile(geometryManifestPath);
  const checksumRows = [...payloads]
    .sort(([a], [b]) => compareText(a, b))
    .map(([name, bytes]) => `${sha256(bytes)}  ${name}`);
  checksumRows.push(`${sha256(geometryManifestBytes)}  geometry/geometry-manifest.json`);
  const checksums = checksumRows.sort(compareText).join("\n") + "\n";
  payloads.set("CHECKSUMS.sha256", Buffer.from(checksums, "utf8"));
  return Object.freeze({ files: payloads, manifest });
}

async function verifySourceBindings() {
  for (const [relativePath, expected] of Object.entries(SOURCE_BINDINGS)) {
    assert.equal(await sha256File(join(repositoryRoot, relativePath)), expected, `frozen source checksum differs: ${relativePath}`);
  }
  const geometryManifest = JSON.parse(await readFile(geometryManifestPath, "utf8"));
  assert.equal(await sha256File(geometryAssetPath), geometryManifest.outputSha256, "geometry asset checksum differs");
}

async function readFrozenSource() {
  const ledger = parseTsv(await readFile(join(repositoryRoot, "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv"), "utf8"));
  const publicIds = new Set(ledger.filter((row) => row.research_disposition === "eligible").map((row) => row.surface_id_exact));
  const heldIds = new Set(ledger.filter((row) => row.research_disposition === "held").map((row) => row.surface_id_exact));
  assert.equal(publicIds.size, EXPECTED.publicObjects);
  assert.equal(heldIds.size, EXPECTED.heldObjects);

  const { DatabaseSync } = createRequire(import.meta.url)("node:sqlite");
  const path = join(repositoryRoot, "data/prefreeze_candidate_v48.sqlite");
  const database = new DatabaseSync(`file:${path}?mode=ro&immutable=1`, { readOnly: true });
  database.exec("PRAGMA query_only=ON");
  let allObjects;
  let allRegions;
  try {
    allObjects = [...database.prepare("SELECT surface_id, title, date_text, date_start, date_end, region FROM objects ORDER BY surface_id").iterate()];
    allRegions = [...database.prepare("SELECT surface_id, folder_id, title FROM object_folder_refs WHERE folder_type='region' ORDER BY surface_id, folder_id").iterate()];
  } finally {
    database.close();
  }
  assert.equal(allObjects.length, EXPECTED.canonicalObjects);
  const objects = allObjects.filter((row) => publicIds.has(row.surface_id));
  const heldObjects = allObjects.filter((row) => heldIds.has(row.surface_id));
  const regions = allRegions.filter((row) => publicIds.has(row.surface_id));
  const heldRegions = allRegions.filter((row) => heldIds.has(row.surface_id));
  assert.equal(objects.length, EXPECTED.publicObjects);
  assert.equal(heldObjects.length, EXPECTED.heldObjects);
  assert.equal(regions.length, EXPECTED.publicRegionAssignments);
  assert.equal(heldRegions.length, EXPECTED.heldObjects);

  const regionByObject = groupBy(regions, (row) => row.surface_id);
  assert.equal(regionByObject.size, EXPECTED.publicRegionObjects);
  assert.equal([...regionByObject.values()].filter((rows) => rows.length > 1).length, EXPECTED.multiRegionObjects);
  assert.equal(new Set(regions.map((row) => row.title)).size, EXPECTED.publicTypedRegionLabels);
  assert.equal(new Set(objects.map((row) => row.region.trim())).size, EXPECTED.publicRawRegionLabels);
  const mexicoCity = objects.filter((row) => row.region.trim() === "Mexico City");
  assert.equal(mexicoCity.length, 1);
  assert.deepEqual(regionByObject.get(mexicoCity[0].surface_id).map((row) => row.title), ["Mexico"]);

  return Object.freeze({ publicIds, heldIds, objects, regions, regionByObject });
}

async function readGeometry() {
  const manifestBytes = await readFile(geometryManifestPath);
  const manifest = JSON.parse(manifestBytes.toString("utf8"));
  const asset = JSON.parse(await readFile(geometryAssetPath, "utf8"));
  assert.equal(manifest.geometryArtifactId, "natural-earth-admin0-countries-5.1.1-50m");
  assert.equal(asset.type, "FeatureCollection");
  assert.equal(asset.features.length, manifest.featureCount);
  const byAdmin0A3 = new Map();
  for (const feature of asset.features) {
    const code = feature.properties?.admin0A3;
    const geometryId = feature.properties?.geometryId;
    assert.equal(typeof code, "string");
    assert.equal(typeof geometryId, "string");
    assert(!byAdmin0A3.has(code), `duplicate admin0A3: ${code}`);
    byAdmin0A3.set(code, Object.freeze({ geometryId, label: feature.properties.name }));
  }
  return Object.freeze({ manifest, manifestSha256: sha256(manifestBytes), byAdmin0A3 });
}

function buildGeographyRegistry(source, geometry) {
  assert.equal(GEOGRAPHY_DECISIONS.length, EXPECTED.publicTypedRegionLabels);
  const decisionsByLabel = new Map(GEOGRAPHY_DECISIONS.map((decision) => [decision[0], decision]));
  assert.equal(decisionsByLabel.size, EXPECTED.publicTypedRegionLabels);
  const sourceLabels = [...new Set(source.regions.map((row) => row.title))].sort(compareText);
  assert.deepEqual([...decisionsByLabel.keys()].sort(compareText), sourceLabels, "explicit geography decision labels differ from frozen public labels");
  const sourceRowsByLabel = groupBy(source.regions, (row) => row.title);
  const entries = sourceLabels.map((sourceLabel) => {
    const rows = sourceRowsByLabel.get(sourceLabel);
    const folderIds = [...new Set(rows.map((row) => row.folder_id))];
    assert.equal(folderIds.length, 1, `typed region identity differs for label: ${sourceLabel}`);
    const [label, geographyClass, mappingDecision, targetCodes] = decisionsByLabel.get(sourceLabel);
    assert.equal(label, sourceLabel);
    const geometryTargets = targetCodes.map((code) => {
      const target = geometry.byAdmin0A3.get(code);
      assert(target, `Natural Earth target missing for ${sourceLabel}: ${code}`);
      return Object.freeze({
        geometryArtifactId: geometry.manifest.geometryArtifactId,
        matchField: "admin0A3",
        matchValue: code,
        geometryId: target.geometryId,
      });
    });
    const mappingState = mappingDecision === "AGGREGATE_WITHOUT_POINT"
      ? "aggregate_only"
      : mappingDecision === "DISPLAY_UNMAPPED"
        ? "unmapped"
        : "mapped";
    const mapped = mappingState === "mapped";
    const isTransnational = ["China / Hong Kong", "Cuba / transnational", "Global / transnational", "Israel / Palestine", "Korean Peninsula", "Palestine / transnational"].includes(sourceLabel);
    const isBroad = ["Australia / Indigenous", "Global / transnational"].includes(sourceLabel);
    const qualification = qualificationFor({ sourceLabel, geographyClass, mappingDecision });
    return Object.freeze({
      geographyId: `SPTGEO:${sha256([GEOGRAPHY_ID_NAMESPACE, "region", folderIds[0]].join("\0"))}`,
      sourceLabel,
      sourceLabelSha256: sha256(sourceLabel),
      sourceAssignmentCount: rows.length,
      displayLabel: sourceLabel,
      geographyClass,
      mappingDecision,
      mappingState,
      geometryTargets: Object.freeze(geometryTargets),
      geometryIds: Object.freeze(geometryTargets.map((target) => target.geometryId)),
      mapEligible: mapped,
      aggregateEligible: true,
      representativePointPolicy: mapped ? (geometryTargets.length > 1 ? "GEOMETRY_DERIVED_AGGREGATE_ANCHOR_LARGEST_COMPONENT" : "GEOMETRY_DERIVED_AGGREGATE_ANCHOR") : "NO_POINT_AGGREGATE_ONLY",
      historicalStatus: false,
      transnational: isTransnational,
      broadRegion: isBroad,
      qualification,
      decisionRationale: rationaleFor({ sourceLabel, geographyClass, mappingDecision }),
      reviewStatus: "REVIEWED_EXPLICIT",
    });
  });
  const ids = new Set(entries.map((entry) => entry.geographyId));
  assert.equal(ids.size, entries.length, "governed geography ID collision");
  const mappedEntries = entries.filter((entry) => entry.mappingState === "mapped");
  const aggregateOnlyEntries = entries.filter((entry) => entry.mappingState === "aggregate_only");
  const unmappedEntries = entries.filter((entry) => entry.mappingState === "unmapped");
  assert.equal(mappedEntries.length, 81);
  assert.equal(aggregateOnlyEntries.length, 11);
  assert.equal(unmappedEntries.length, 1);
  const byLabel = new Map(entries.map((entry) => [entry.sourceLabel, entry]));
  const byId = new Map(entries.map((entry) => [entry.geographyId, entry]));
  const document = Object.freeze({
    format: "trace-spacetime-geography-registry/v1",
    schemaVersion: SCHEMA_VERSION,
    projectionId: PROJECTION_ID,
    sourceRelease: SOURCE_RELEASE,
    geographyRole: "recorded_region_context",
    geographyPolicyVersion: GEOGRAPHY_POLICY_VERSION,
    idPolicyVersion: ID_POLICY_VERSION,
    geometryArtifactId: geometry.manifest.geometryArtifactId,
    counts: Object.freeze({
      registryEntries: entries.length,
      mappedEntries: mappedEntries.length,
      aggregateOnlyEntries: aggregateOnlyEntries.length,
      unmappedEntries: unmappedEntries.length,
      heldEntries: 0,
      sourceAssignments: source.regions.length,
      sourceObjectCoverage: source.regionByObject.size,
    }),
    entries: Object.freeze(entries),
  });
  assert.doesNotMatch(JSON.stringify(document), /FOL-REGION-|[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-/iu, "private geography identity leaked");
  return Object.freeze({ document, entries, byLabel, byId });
}

function buildRecords(source, geography) {
  const records = source.objects.map((object) => {
    const regionRows = source.regionByObject.get(object.surface_id);
    assert(regionRows?.length >= 1);
    const geographyEntries = regionRows.map((row) => geography.byLabel.get(row.title));
    assert(geographyEntries.every(Boolean));
    const temporal = governTemporalCandidate(object);
    const periodIds = deriveBucketMemberships(temporal.startYearInclusive, temporal.endYearInclusive);
    return Object.freeze({
      objectId: object.surface_id,
      title: object.title,
      geographyIds: Object.freeze(geographyEntries.map((entry) => entry.geographyId)),
      recordedRegionDisplays: Object.freeze(regionRows.map((row) => row.title)),
      rawRegionDisplay: object.region.trim(),
      time: temporal,
      periodIds: Object.freeze(periodIds),
    });
  }).sort((left, right) => compareText(left.objectId, right.objectId));
  assert.equal(records.length, EXPECTED.publicObjects);
  assert.equal(new Set(records.map((record) => record.objectId)).size, records.length);
  const precision = precisionBreakdown(records);
  for (const key of ["year", "approximate", "day", "month", "range", "unknown"]) assert.equal(precision[key], EXPECTED[key]);
  const mappedObjects = records.filter((record) => record.geographyIds.some((id) => geography.byId.get(id).mappingState === "mapped")).length;
  const aggregateOnlyObjects = records.filter((record) => record.geographyIds.every((id) => geography.byId.get(id).mappingState === "aggregate_only")).length;
  const unmappedObjects = records.filter((record) => record.geographyIds.every((id) => geography.byId.get(id).mappingState === "unmapped")).length;
  const document = Object.freeze({
    format: "trace-spacetime-record-index/v1",
    schemaVersion: SCHEMA_VERSION,
    projectionId: PROJECTION_ID,
    sourceRelease: SOURCE_RELEASE,
    geographyRole: "recorded_region_context",
    temporalRole: "recorded_date_context",
    geographyPolicyVersion: GEOGRAPHY_POLICY_VERSION,
    temporalPolicyVersion: TEMPORAL_POLICY_VERSION,
    rangeMembershipPolicy: RANGE_MEMBERSHIP_POLICY,
    serverOnly: true,
    counts: Object.freeze({ records: records.length, mappedObjects, aggregateOnlyObjects, unmappedObjects, heldObjects: source.heldIds.size, precision }),
    records: Object.freeze(records),
  });
  assert.doesNotMatch(JSON.stringify(document), /FOL-REGION-|[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-/iu, "private record identity leaked");
  return Object.freeze({ document, records, mappedObjects, aggregateOnlyObjects, unmappedObjects, precision });
}

function buildTimeBuckets(records, geography) {
  const periodDefinitions = [];
  for (let start = EXPECTED.earliestYear; start <= EXPECTED.latestYear; start += 10) {
    periodDefinitions.push(Object.freeze({
      periodId: periodId(start, start + 10),
      label: `${start}s`,
      startYearInclusive: start,
      endYearExclusive: start + 10,
      membershipPolicy: RANGE_MEMBERSHIP_POLICY,
    }));
  }
  assert.equal(periodDefinitions.length, EXPECTED.bucketCount);
  const periods = periodDefinitions.map((period) => {
    const members = records.records.filter((record) => record.periodIds.includes(period.periodId));
    const mappedRecordCount = members.filter((record) => record.geographyIds.some((id) => geography.byId.get(id).mappingState === "mapped")).length;
    return Object.freeze({
      ...period,
      recordCount: members.length,
      mappedRecordCount,
      unmappedRecordCount: members.length - mappedRecordCount,
      precisionBreakdown: precisionBreakdown(members),
    });
  });
  const defaultPeriod = [...periods].sort((left, right) => right.recordCount - left.recordCount || left.startYearInclusive - right.startYearInclusive)[0];
  const document = Object.freeze({
    format: "trace-spacetime-time-buckets/v1",
    schemaVersion: SCHEMA_VERSION,
    projectionId: PROJECTION_ID,
    sourceRelease: SOURCE_RELEASE,
    temporalRole: "recorded_date_context",
    temporalPolicyVersion: TEMPORAL_POLICY_VERSION,
    bucketPolicy: BUCKET_POLICY,
    rangeMembershipPolicy: RANGE_MEMBERSHIP_POLICY,
    defaultPeriodId: defaultPeriod.periodId,
    periods: Object.freeze(periods),
  });
  return Object.freeze({ document, periods, defaultPeriodId: defaultPeriod.periodId });
}

function buildPeriodRegionAggregates(records, geography, buckets) {
  const periods = buckets.periods.map((period) => {
    const members = records.records.filter((record) => record.periodIds.includes(period.periodId));
    const cells = [];
    for (const entry of geography.entries) {
      const cellRecords = members.filter((record) => record.geographyIds.includes(entry.geographyId));
      if (cellRecords.length === 0) continue;
      cells.push(Object.freeze({
        geographyId: entry.geographyId,
        recordCount: cellRecords.length,
        denominator: members.length,
        precisionBreakdown: precisionBreakdown(cellRecords),
        mappingState: entry.mappingState,
        unmappedCount: entry.mappingState === "mapped" ? 0 : cellRecords.length,
      }));
    }
    cells.sort((left, right) => compareText(left.geographyId, right.geographyId));
    return Object.freeze({
      periodId: period.periodId,
      denominator: members.length,
      mappedRecordCount: period.mappedRecordCount,
      unmappedRecordCount: period.unmappedRecordCount,
      geographyAssignmentCount: cells.reduce((sum, cell) => sum + cell.recordCount, 0),
      cells: Object.freeze(cells),
    });
  });
  return Object.freeze({
    format: "trace-spacetime-period-region-aggregates/v1",
    schemaVersion: SCHEMA_VERSION,
    projectionId: PROJECTION_ID,
    sourceRelease: SOURCE_RELEASE,
    geographyPolicyVersion: GEOGRAPHY_POLICY_VERSION,
    temporalPolicyVersion: TEMPORAL_POLICY_VERSION,
    bucketPolicy: BUCKET_POLICY,
    rangeMembershipPolicy: RANGE_MEMBERSHIP_POLICY,
    periodCount: periods.length,
    periods: Object.freeze(periods),
  });
}

function buildGovernancePolicy(source, geography) {
  return Object.freeze({
    format: "trace-spacetime-governance-policy/v1",
    schemaVersion: SCHEMA_VERSION,
    projectionId: PROJECTION_ID,
    sourceRelease: SOURCE_RELEASE,
    geographyPolicyVersion: GEOGRAPHY_POLICY_VERSION,
    temporalPolicyVersion: TEMPORAL_POLICY_VERSION,
    geographyRole: Object.freeze({
      role: "recorded_region_context",
      statement: "A governed release-pinned record-region context; not an exact creation, publication, collection, subject, travel, or diffusion location.",
    }),
    temporalRole: Object.freeze({
      role: "recorded_date_context",
      statement: "A governed release-pinned record-date context; not an exact creation or historical-event claim unless separately evidenced.",
    }),
    timeBucketPolicy: Object.freeze({
      bucketPolicy: BUCKET_POLICY,
      rangeMembershipPolicy: RANGE_MEMBERSHIP_POLICY,
      statement: "A record contributes to every decade whose half-open interval overlaps its inclusive governed year extent.",
    }),
    geographyDecisionPolicy: Object.freeze({
      noFuzzyFinalMapping: true,
      noExternalGeocoder: true,
      noInventedObjectCoordinates: true,
      aggregateAnchorSemanticKind: "AGGREGATE_LAYOUT_ANCHOR",
      subnationalWithoutGovernedGeometry: "AGGREGATE_WITHOUT_POINT",
      broadTransnationalHistoricalSilentNormalizationAllowed: false,
    }),
    rawTypedDiagnostics: Object.freeze({
      publicRawLabelCount: EXPECTED.publicRawRegionLabels,
      publicTypedLabelCount: EXPECTED.publicTypedRegionLabels,
      discrepancies: Object.freeze([{ rawLabel: "Mexico City", typedLabel: "Mexico", recordCount: 1, decision: "USE_TYPED_GOVERNED_ASSIGNMENT_PRESERVE_RAW_AS_DIAGNOSTIC" }]),
    }),
    heldBoundary: Object.freeze({ heldObjectCount: source.heldIds.size, heldObjectsProjected: 0 }),
    invariants: Object.freeze([
      "ST-GIS-INV-001", "ST-GIS-INV-002", "ST-GIS-INV-003", "ST-GIS-INV-004", "ST-GIS-INV-005",
      "ST-GIS-INV-006", "ST-GIS-INV-007", "ST-GIS-INV-008", "ST-GIS-INV-009", "ST-GIS-INV-010",
      "ST-GIS-INV-011", "ST-GIS-INV-012", "ST-GIS-INV-013", "ST-GIS-INV-014", "ST-GIS-INV-015",
      "ST-GIS-INV-016", "ST-GIS-INV-017", "ST-GIS-INV-018", "ST-GIS-INV-019", "ST-GIS-INV-020",
    ]),
    registryCounts: geography.document.counts,
  });
}

function buildManifest({ source, geography, records, buckets, aggregates, geometry, payloadHashes, projectionSha256 }) {
  const totalCells = aggregates.periods.reduce((sum, period) => sum + period.cells.length, 0);
  return Object.freeze({
    format: "trace-spacetime-projection-manifest/v1",
    schemaVersion: SCHEMA_VERSION,
    projectionId: PROJECTION_ID,
    projectionSha256,
    deterministic: true,
    canonicalSerialization: CANONICAL_SERIALIZATION,
    generatorVersion: GENERATOR_VERSION,
    generatedAt: GENERATED_AT,
    serverOnly: true,
    sourceRelease: SOURCE_RELEASE,
    sourceBindings: SOURCE_BINDINGS,
    idPolicyVersion: ID_POLICY_VERSION,
    geographyPolicyVersion: GEOGRAPHY_POLICY_VERSION,
    temporalPolicyVersion: TEMPORAL_POLICY_VERSION,
    bucketPolicy: BUCKET_POLICY,
    rangeMembershipPolicy: RANGE_MEMBERSHIP_POLICY,
    geometry: Object.freeze({
      geometryArtifactId: geometry.manifest.geometryArtifactId,
      geometryManifestPath: "geometry/geometry-manifest.json",
      geometryManifestSha256: geometry.manifestSha256,
      assetPath: geometry.manifest.publicAssetPath,
      assetSha256: geometry.manifest.outputSha256,
      featureCount: geometry.manifest.featureCount,
    }),
    counts: Object.freeze({
      publicObjects: source.publicIds.size,
      heldObjects: source.heldIds.size,
      regionAssignments: source.regions.length,
      regionObjectCoverage: source.regionByObject.size,
      rawRegionLabels: EXPECTED.publicRawRegionLabels,
      governedGeographyEntries: geography.entries.length,
      mappedGeographyEntries: geography.document.counts.mappedEntries,
      aggregateOnlyGeographyEntries: geography.document.counts.aggregateOnlyEntries,
      unmappedGeographyEntries: geography.document.counts.unmappedEntries,
      mappedObjects: records.mappedObjects,
      aggregateOnlyObjects: records.aggregateOnlyObjects,
      unmappedObjects: records.unmappedObjects,
      temporalObjectCoverage: records.records.length,
      temporalPrecision: records.precision,
      earliestGovernedYear: EXPECTED.earliestYear,
      latestGovernedYear: EXPECTED.latestYear,
      timeBuckets: buckets.periods.length,
      periodRegionCells: totalCells,
    }),
    defaultPeriodId: buckets.defaultPeriodId,
    payloadSha256: Object.freeze(payloadHashes),
  });
}

function governTemporalCandidate(row) {
  const sourceDisplay = String(row.date_text ?? "").trim();
  const startYearInclusive = Number(row.date_start);
  const endYearInclusive = row.date_end === null ? startYearInclusive : Number(row.date_end);
  assert(Number.isSafeInteger(startYearInclusive), `invalid date_start: ${row.surface_id}`);
  assert(Number.isSafeInteger(endYearInclusive), `invalid date_end: ${row.surface_id}`);
  assert(endYearInclusive >= startYearInclusive, `reversed temporal extent: ${row.surface_id}`);
  const precision = classifyTemporalPrecision(sourceDisplay, startYearInclusive, row.date_end === null ? null : endYearInclusive);
  return Object.freeze({
    observationId: `SPTTIME:${sha256([TIME_ID_NAMESPACE, row.surface_id, sourceDisplay, startYearInclusive, endYearInclusive, precision].join("\0"))}`,
    role: "recorded_context",
    sourceDisplay,
    startYearInclusive,
    endYearInclusive,
    precision,
    derivationMethod: TEMPORAL_DERIVATION_METHOD,
  });
}

function classifyTemporalPrecision(sourceDisplay, start, end) {
  if (!Number.isSafeInteger(start) || !sourceDisplay || ["unknown", "n/a", "none"].includes(sourceDisplay.toLowerCase())) return "unknown";
  if (/^\d{4}$/u.test(sourceDisplay) && (end === null || end === start)) return "year";
  if (end !== null && end !== start) return "range";
  if (isDayDisplay(sourceDisplay)) return "day";
  if (isMonthDisplay(sourceDisplay)) return "month";
  return "approximate";
}

function isDayDisplay(value) {
  return /^\d{4}-\d{2}-\d{2}$/u.test(value) || NATURAL_DAY_RE.test(value);
}

function isMonthDisplay(value) {
  const yearMonth = value.match(/^\d{4}[-/](\d{2})$/u);
  return Boolean(yearMonth && Number(yearMonth[1]) >= 1 && Number(yearMonth[1]) <= 12) || NATURAL_MONTH_RE.test(value);
}

function deriveBucketMemberships(startYearInclusive, endYearInclusive) {
  const out = [];
  for (let start = EXPECTED.earliestYear; start <= EXPECTED.latestYear; start += 10) {
    const endExclusive = start + 10;
    if (startYearInclusive < endExclusive && endYearInclusive >= start) out.push(periodId(start, endExclusive));
  }
  assert(out.length >= 1, `temporal extent has no period: ${startYearInclusive}-${endYearInclusive}`);
  return out;
}

function precisionBreakdown(records) {
  const result = { day: 0, month: 0, year: 0, range: 0, approximate: 0, unknown: 0 };
  for (const record of records) result[record.time.precision] += 1;
  return Object.freeze(result);
}

function qualificationFor({ sourceLabel, geographyClass, mappingDecision }) {
  if (mappingDecision === "MAP_TO_EXPLICIT_MULTI_GEOMETRY") return "Explicit multi-geometry world-map aggregate; the combined source label remains visible and is not normalized to one polity.";
  if (mappingDecision === "AGGREGATE_WITHOUT_POINT" && geographyClass === "subnational") return "No evidence-backed subnational geometry or representative point is present in the frozen release; retain as an aggregate-only row.";
  if (mappingDecision === "AGGREGATE_WITHOUT_POINT") return "The broad or transnational source scope cannot be represented by one current polygon or point without overclaiming.";
  if (mappingDecision === "DISPLAY_UNMAPPED") return "The pinned Natural Earth 50m artifact has no matching governed map-unit geometry; retain the record in explicit unmapped counts without inventing a point or parent-country substitute.";
  if (mappingDecision === "MAP_TO_MAP_UNIT") return "Mapped to the explicitly reviewed Natural Earth map unit; no object coordinate is asserted.";
  if (sourceLabel === "Georgia") return "Explicitly reviewed as the country-level controlled region label and mapped to Natural Earth GEO; not inferred as the U.S. state.";
  return null;
}

function rationaleFor({ sourceLabel, geographyClass, mappingDecision }) {
  if (mappingDecision === "MAP_TO_ADMIN0") return `${sourceLabel} is an explicitly reviewed country-level label mapped to one pinned Natural Earth Admin-0 geometry.`;
  if (mappingDecision === "MAP_TO_MAP_UNIT") return `${sourceLabel} is an explicitly reviewed territory/map-unit label mapped to its pinned Natural Earth unit.`;
  if (mappingDecision === "MAP_TO_EXPLICIT_MULTI_GEOMETRY") return `${sourceLabel} is explicitly represented by the listed pinned geometries; no single-country substitution is made.`;
  if (mappingDecision === "DISPLAY_UNMAPPED") return `${sourceLabel} has no matching feature in the pinned Natural Earth 50m artifact and remains visibly unmapped without a parent-country substitution.`;
  if (geographyClass === "subnational") return `${sourceLabel} has no governed subnational geometry or evidence-backed point in v1 and remains visible without a map position.`;
  return `${sourceLabel} is broad or transnational and remains visible in aggregates without an invented point or silent modern-country normalization.`;
}

async function writeProjection(built) {
  await mkdir(outputDirectory, { recursive: true });
  for (const [filename, bytes] of built.files) await writeFile(join(outputDirectory, filename), bytes);
  console.log(receipt("WRITE", built));
}

async function checkProjection(built) {
  const names = new Set(await readdir(outputDirectory));
  for (const [filename, expected] of built.files) {
    assert(names.has(filename), `missing generated artifact: ${filename}`);
    assert.deepEqual(await readFile(join(outputDirectory, filename)), expected, `generated artifact drifted: ${filename}`);
  }
  console.log(receipt("CHECK", built));
}

function receipt(mode, built) {
  const counts = built.manifest.counts;
  return [
    `TRACE_SPACETIME_V1_GENERATION=PASS MODE=${mode}`,
    `PROJECTION_ID=${PROJECTION_ID}`,
    `PROJECTION_SHA256=${built.manifest.projectionSha256}`,
    `PUBLIC_OBJECTS=${counts.publicObjects}`,
    `HELD_OBJECTS=${counts.heldObjects}`,
    `REGION_ASSIGNMENTS=${counts.regionAssignments}`,
    `GEOGRAPHIES=${counts.governedGeographyEntries}`,
    `MAPPED_GEOGRAPHIES=${counts.mappedGeographyEntries}`,
    `AGGREGATE_ONLY_GEOGRAPHIES=${counts.aggregateOnlyGeographyEntries}`,
    `UNMAPPED_GEOGRAPHIES=${counts.unmappedGeographyEntries}`,
    `MAPPED_OBJECTS=${counts.mappedObjects}`,
    `AGGREGATE_ONLY_OBJECTS=${counts.aggregateOnlyObjects}`,
    `UNMAPPED_OBJECTS=${counts.unmappedObjects}`,
    `PERIODS=${counts.timeBuckets}`,
    `DEFAULT_PERIOD=${built.manifest.defaultPeriodId}`,
  ].join(" ");
}

function parseTsv(text) {
  const lines = text.trimEnd().split(/\r?\n/u);
  const header = lines[0].split("\t");
  return lines.slice(1).map((line) => Object.fromEntries(line.split("\t").map((value, index) => [header[index], value])));
}

function groupBy(values, key) {
  const result = new Map();
  for (const value of values) {
    const identity = key(value);
    const list = result.get(identity) ?? [];
    list.push(value);
    result.set(identity, list);
  }
  return result;
}

function periodId(start, endExclusive) {
  return `SPT-PERIOD-${start}-${endExclusive}`;
}

function canonicalBytes(value) {
  return Buffer.from(`${JSON.stringify(sortKeys(value))}\n`, "utf8");
}

function sortKeys(value) {
  if (Array.isArray(value)) return value.map(sortKeys);
  if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort(compareText).map((key) => [key, sortKeys(value[key])]));
  return value;
}

function compareText(left, right) {
  return String(left).localeCompare(String(right), "en", { sensitivity: "variant" });
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

async function sha256File(path) {
  const hash = createHash("sha256");
  for await (const chunk of createReadStream(path)) hash.update(chunk);
  return hash.digest("hex");
}

function safeError(error) {
  return String(error instanceof Error ? error.message : error).replaceAll(/[^\x20-\x7e]/gu, "?").slice(0, 500);
}
