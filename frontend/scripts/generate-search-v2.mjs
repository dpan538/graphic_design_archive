import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(here, "..");
const repositoryRoot = join(frontendRoot, "..");
const inputPath = join(repositoryRoot, "generated/public_surfaces_prefreeze_candidate_v48.json");
const freezePath = join(repositoryRoot, "database/FREEZE_V49.json");
const outputDirectory = join(frontendRoot, "generated/search-v2");
const documentsPath = join(outputDirectory, "documents.json");
const facetsPath = join(outputDirectory, "facets.json");
const manifestPath = join(outputDirectory, "manifest.json");
const checksumsPath = join(outputDirectory, "CHECKSUMS.sha256");
const checkOnly = process.argv.includes("--check");

const SEARCH_ALGORITHM_VERSION = "gda-public-object-relevance-v2";
const INDEX_FORMAT_VERSION = "gda-public-object-search-documents-v2";
const RELEASE_ID = "v49-api-contract-fresh-c";
const RELEASE_MANIFEST_SHA256 = "4addfdb3cb9314587908096572242b9d63e9cef9e6e1be68c0c646491a43a90a";
const GENERATED_AT = "2026-08-29T00:00:00Z";
const EXPECTED_DOCUMENT_COUNT = 7995;
const EXPECTED_HELD_COUNT = 7928;
const PINNED_UNICODE_VERSION = "16.0";
const PUBLIC_FIELDS = ["stable_id", "title", "credited_label", "display_date", "year_range", "place", "object_type", "theme", "movement", "source_collection", "delivery_state", "object_route"];
const SEARCHABLE_FIELDS = ["stable_id", "title", "credited_label", "place"];
const FILTERABLE_FIELDS = ["year_range", "object_type", "theme", "movement"];

const fieldPolicy = {
  version: "gda-public-object-search-fields-v2",
  eligibility: "trace.tier === source_verified",
  publicFields: PUBLIC_FIELDS,
  searchableFields: SEARCHABLE_FIELDS,
  filterableFields: FILTERABLE_FIELDS,
  heldFieldsExcluded: ["sourceDescription", "sourceNotes", "sourceSubjects", "trace", "authority", "collectionEvidence", "publicationGate"],
  noInference: ["credited_label", "place", "theme", "movement", "year_range"],
};

const sha256 = (value) => createHash("sha256").update(value).digest("hex");
const stableJson = (value) => `${JSON.stringify(value)}\n`;
const compare = (left, right) => left < right ? -1 : left > right ? 1 : 0;

function publicCredit(value) {
  const label = String(value ?? "").trim();
  return !label || /^(?:unknown|anonymous|unattributed|not identified|ukjent|inconnu|anonym\b|n\/a\b|none\b)/i.test(label) ? null : label;
}

function folderLabels(surface, type) {
  return [...new Set((surface.folders ?? []).filter((folder) => folder?.type === type && String(folder.title ?? "").trim()).map((folder) => String(folder.title).trim()))].sort(compare);
}

function deliveryState(surface) {
  const policy = String(surface?.rights?.displayPolicy ?? "").toLowerCase();
  const imageState = String(surface?.image?.state ?? "");
  if (policy.includes("open_image") || imageState === "IMG03") return "REMOTE_IMAGE";
  if (policy.includes("source_visible") || policy.includes("viewer") || imageState === "IMG02") return "SOURCE_VIEWER";
  if (policy.includes("link") || imageState === "IMG01") return "LINK_ONLY";
  return "CITATION_ONLY";
}

function countValues(documents, index) {
  const counts = new Map();
  for (const document of documents) {
    const raw = document[index];
    const values = Array.isArray(raw) ? raw : [raw];
    for (const value of values) if (value) counts.set(value, (counts.get(value) ?? 0) + 1);
  }
  return [...counts].map(([value, count]) => ({ value, count })).sort((left, right) => right.count - left.count || compare(left.value, right.value));
}

async function expectFile(path, expected) {
  const actual = await readFile(path, "utf8").catch(() => null);
  if (actual !== expected) throw new Error(`generated artifact mismatch: ${path}`);
}

if (process.versions.unicode !== PINNED_UNICODE_VERSION) throw new Error(`Search v2 generation requires Unicode ${PINNED_UNICODE_VERSION}; found ${process.versions.unicode}`);
const [inputBytes, freezeBytes] = await Promise.all([readFile(inputPath), readFile(freezePath)]);
const freeze = JSON.parse(freezeBytes.toString("utf8"));
const expectedInputSha = freeze.perFileSha256?.["generated/public_surfaces_prefreeze_candidate_v48.json"];
const actualInputSha = sha256(inputBytes);
if (!expectedInputSha || actualInputSha !== expectedInputSha || actualInputSha !== freeze.canonicalInputDigest) throw new Error("frozen v49 candidate checksum mismatch");

const source = JSON.parse(inputBytes.toString("utf8"));
const surfaces = Array.isArray(source.surfaces) ? source.surfaces : [];
const eligible = surfaces.filter((surface) => surface?.trace?.tier === "source_verified");
const held = surfaces.length - eligible.length;
if (eligible.length !== EXPECTED_DOCUMENT_COUNT || held !== EXPECTED_HELD_COUNT) throw new Error(`Search v2 eligibility boundary mismatch: ${eligible.length} public / ${held} held`);

const seen = new Set();
const documents = eligible.map((surface) => {
  const stableId = String(surface.surfaceId ?? "").trim();
  const title = String(surface.title ?? "").trim();
  const displayDate = String(surface.dateText ?? "").trim();
  const yearStart = Number(surface.dateStart);
  const yearEnd = Number.isInteger(surface.dateEnd) ? Number(surface.dateEnd) : yearStart;
  const place = String(surface.placeText ?? "").trim();
  const objectType = String(surface.objectType ?? "").trim();
  const sourceLabel = String(surface.sourceName ?? "").trim();
  if (!stableId || !title || seen.has(stableId) || !displayDate || !Number.isInteger(yearStart) || !Number.isInteger(yearEnd) || !place || !objectType || !sourceLabel) {
    throw new Error(`invalid public Search v2 document: ${stableId}`);
  }
  seen.add(stableId);
  return [
    stableId,
    title,
    publicCredit(surface.creator),
    displayDate,
    yearStart,
    yearEnd,
    place,
    objectType,
    folderLabels(surface, "theme"),
    folderLabels(surface, "movement"),
    sourceLabel,
    deliveryState(surface),
  ];
}).sort((left, right) => compare(left[0], right[0]));

const objectTypes = countValues(documents, 7);
const themes = countValues(documents, 8);
const movements = countValues(documents, 9);
const documentsPayload = {
  format: INDEX_FORMAT_VERSION,
  release_id: RELEASE_ID,
  search_algorithm_version: SEARCH_ALGORITHM_VERSION,
  schema: ["stableId", "title", "creditedLabel", "displayDate", "yearStart", "yearEnd", "place", "objectType", "themes", "movements", "sourceLabel", "deliveryState"],
  documents,
};
const facets = {
  format: "gda-public-object-search-facets-v1",
  release_id: RELEASE_ID,
  year: {
    min: Math.min(...documents.map((document) => document[4])),
    max: Math.max(...documents.map((document) => document[5])),
  },
  object_types: objectTypes,
  themes,
  movements,
  starter_queries: [
    { id: "starter-posters", label: objectTypes[0].value, query: "", filters: { objectType: objectTypes[0].value } },
    { id: "starter-modern-typography", label: themes.find((item) => item.value === "Modern typography and layout").value, query: "", filters: { theme: "Modern typography and layout" } },
    { id: "starter-bauhaus", label: movements.find((item) => item.value.startsWith("Bauhaus")).value, query: "", filters: { movement: movements.find((item) => item.value.startsWith("Bauhaus")).value } },
    { id: "starter-1960s", label: "1960s", query: "", filters: { yearFrom: 1960, yearTo: 1969 } },
  ],
};
const documentsText = stableJson(documentsPayload);
const facetsText = stableJson(facets);
const manifest = {
  format: "gda-public-object-search-manifest-v2",
  release_id: RELEASE_ID,
  release_manifest_sha256: RELEASE_MANIFEST_SHA256,
  canonical_input_sha256: actualInputSha,
  search_algorithm_version: SEARCH_ALGORITHM_VERSION,
  index_format_version: INDEX_FORMAT_VERSION,
  document_count: documents.length,
  source_held_record_count: held,
  held_document_count: 0,
  trace_record_count: 0,
  open_inquiry_record_count: 0,
  generated_at: GENERATED_AT,
  source_field_policy_hash: sha256(stableJson(fieldPolicy)),
  unicode_version: PINNED_UNICODE_VERSION,
  normalization_version: "nfc-nfkc-casefold-latin-diacritic-osa-v2",
  index_sha256: sha256(documentsText),
  index_bytes: Buffer.byteLength(documentsText),
  index_gzip_bytes: gzipSync(documentsText, { level: 9 }).byteLength,
  facets_sha256: sha256(facetsText),
  facets_bytes: Buffer.byteLength(facetsText),
  document_order: "stableId ascending by Unicode code point",
  public_fields: PUBLIC_FIELDS,
  searchable_fields: SEARCHABLE_FIELDS,
  filterable_fields: FILTERABLE_FIELDS,
  coverage: {
    credited_label_present: documents.filter((document) => document[2]).length,
    movement_present: documents.filter((document) => document[9].length).length,
    year_end_present_in_source: eligible.filter((surface) => Number.isInteger(surface.dateEnd)).length,
  },
  runtime_bounds: {
    max_query_code_points: 160,
    max_query_tokens: 24,
    default_page_size: 25,
    max_page_size: 50,
    max_edit_distance: 2,
  },
};
const manifestText = stableJson(manifest);
const checksumsText = `${sha256(documentsText)}  documents.json\n${sha256(facetsText)}  facets.json\n${sha256(manifestText)}  manifest.json\n`;

if (checkOnly) {
  await Promise.all([
    expectFile(documentsPath, documentsText),
    expectFile(facetsPath, facetsText),
    expectFile(manifestPath, manifestText),
    expectFile(checksumsPath, checksumsText),
  ]);
} else {
  await mkdir(outputDirectory, { recursive: true });
  await Promise.all([
    writeFile(documentsPath, documentsText),
    writeFile(facetsPath, facetsText),
    writeFile(manifestPath, manifestText),
    writeFile(checksumsPath, checksumsText),
  ]);
}

console.log(JSON.stringify({
  mode: checkOnly ? "check" : "write",
  publicDocumentCount: documents.length,
  sourceHeldRecordCount: held,
  heldDocumentCount: 0,
  traceRecordCount: 0,
  openInquiryRecordCount: 0,
  indexSha256: manifest.index_sha256,
  indexBytes: manifest.index_bytes,
  indexGzipBytes: manifest.index_gzip_bytes,
  creditedLabelPresent: manifest.coverage.credited_label_present,
  movementPresent: manifest.coverage.movement_present,
  objectTypeFacetCount: objectTypes.length,
  themeFacetCount: themes.length,
  movementFacetCount: movements.length,
}, null, 2));
