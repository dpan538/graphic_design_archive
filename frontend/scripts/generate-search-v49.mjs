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
const outputDirectory = join(frontendRoot, "generated/search-v49");
const documentsPath = join(outputDirectory, "documents.json");
const manifestPath = join(outputDirectory, "manifest.json");
const checksumsPath = join(outputDirectory, "CHECKSUMS.sha256");
const checkOnly = process.argv.includes("--check");

const SEARCH_ALGORITHM_VERSION = "v49-lexical-fuzzy-1";
const INDEX_FORMAT_VERSION = "gda-search-documents-v1";
const SOURCE_SHA = "c0ca9a1d4745cfd1054b924c648e57887830960d";
const SOURCE_TREE_HASH = "f8ecd0046a4b8e3c1be657b2a31ac0b863f08ad0";
const RELEASE_ID = "v49-api-contract-fresh-c";
const RELEASE_MANIFEST_SHA256 = "4addfdb3cb9314587908096572242b9d63e9cef9e6e1be68c0c646491a43a90a";
const GENERATED_AT = "2026-08-21T15:34:10+10:00";
const EXPECTED_DOCUMENT_COUNT = 7995;
const EXPECTED_HELD_COUNT = 7928;
const PINNED_UNICODE_VERSION = "16.0";
const MAX_DOCUMENT_TITLE_CODE_POINTS = 1024;
const MAX_DOCUMENT_TOKENS = 128;
const MAX_DOCUMENT_TOKEN_CODE_POINTS = 64;

const fieldPolicy = {
  version: "v49-public-search-fields-1",
  eligibility: "trace.tier === source_verified (v49 corpus membership source)",
  includedFields: ["surfaceId", "title"],
  excludedFields: [
    "creator", "dateText", "placeText", "objectType", "medium", "sourceName",
    "descriptionSummary", "sourceDescription", "sourceNotes", "sourceSubjects",
    "folders", "tables", "rights", "image", "trace",
  ],
  reason: "The frozen v49 public surface projection exposes stable ID and title; all other candidate fields remain unindexed.",
};

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function caseFoldV1(value) {
  return value.toLowerCase().replaceAll("ß", "ss").replaceAll("ς", "σ");
}

function collapseSeparators(value) {
  return value
    .replace(/[\u00a0\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]/gu, " ")
    .replace(/[\u2010-\u2015\u2212_-]+/gu, " ")
    .replace(/[\u2018\u2019\u02bc'`]+/gu, " ")
    .replace(/[\\/]+/gu, " ")
    .replace(/[\p{P}\p{S}]+/gu, " ")
    .replace(/\s+/gu, " ")
    .trim();
}

function normalize(value, form) {
  return collapseSeparators(caseFoldV1(value.normalize(form)));
}

function foldLatinDiacritics(value) {
  let output = "";
  let latinStarter = false;
  for (const character of value.normalize("NFD")) {
    if (/\p{M}/u.test(character)) {
      if (!latinStarter) output += character;
      continue;
    }
    latinStarter = /\p{Script=Latin}/u.test(character);
    output += character;
  }
  return output.normalize("NFC");
}

function stableJson(value) {
  return `${JSON.stringify(value)}\n`;
}

async function expectFile(path, expected) {
  const actual = await readFile(path, "utf8").catch(() => null);
  if (actual !== expected) throw new Error(`generated artifact mismatch: ${path}`);
}

if (process.versions.unicode !== PINNED_UNICODE_VERSION) {
  throw new Error(`search index generation requires Unicode ${PINNED_UNICODE_VERSION}; found ${process.versions.unicode}`);
}

const [inputBytes, freezeBytes] = await Promise.all([readFile(inputPath), readFile(freezePath)]);
const freeze = JSON.parse(freezeBytes.toString("utf8"));
const expectedInputSha = freeze.perFileSha256?.["generated/public_surfaces_prefreeze_candidate_v48.json"];
const actualInputSha = sha256(inputBytes);
if (!expectedInputSha || actualInputSha !== expectedInputSha || actualInputSha !== freeze.canonicalInputDigest) {
  throw new Error("frozen v49 candidate checksum mismatch");
}

const payload = JSON.parse(inputBytes.toString("utf8"));
const surfaces = Array.isArray(payload.surfaces) ? payload.surfaces : [];
const eligible = surfaces.filter((surface) => surface?.trace?.tier === "source_verified");
const heldCount = surfaces.length - eligible.length;
if (eligible.length !== EXPECTED_DOCUMENT_COUNT || heldCount !== EXPECTED_HELD_COUNT) {
  throw new Error(`v49 eligibility boundary mismatch: ${eligible.length} eligible / ${heldCount} held`);
}

const seen = new Set();
const documents = eligible.map((surface) => {
  const stableId = String(surface.surfaceId ?? "").trim();
  const title = String(surface.title ?? "").trim();
  if (!stableId || !title || seen.has(stableId)) throw new Error(`invalid or duplicate public search document: ${stableId}`);
  seen.add(stableId);
  const primary = normalize(title, "NFC");
  const compatibility = normalize(title, "NFKC");
  const latinFolded = foldLatinDiacritics(primary);
  const titleTokens = primary.split(" ").filter(Boolean);
  if (Array.from(title).length > MAX_DOCUMENT_TITLE_CODE_POINTS
      || titleTokens.length > MAX_DOCUMENT_TOKENS
      || titleTokens.some((token) => Array.from(token).length > MAX_DOCUMENT_TOKEN_CODE_POINTS)) {
    throw new Error(`public title exceeds the fixed v1 search work bounds: ${stableId}`);
  }
  return [stableId, title, primary, compatibility, latinFolded];
}).sort((left, right) => left[0] < right[0] ? -1 : left[0] > right[0] ? 1 : 0);

const documentsPayload = {
  format: INDEX_FORMAT_VERSION,
  release_id: RELEASE_ID,
  search_algorithm_version: SEARCH_ALGORITHM_VERSION,
  schema: ["stableId", "title", "primary", "compatibility", "latinFolded"],
  documents,
};
const documentsText = stableJson(documentsPayload);
const documentsSha = sha256(documentsText);
const documentsBytes = Buffer.byteLength(documentsText);
const documentsGzipBytes = gzipSync(documentsText, { level: 9 }).byteLength;
const sourceFieldPolicyHash = sha256(stableJson(fieldPolicy));
const manifest = {
  format: "gda-search-index-manifest-v1",
  release_id: RELEASE_ID,
  release_manifest_sha256: RELEASE_MANIFEST_SHA256,
  release_projection_sha256: freeze.releaseProjectionDigest,
  canonical_input_sha256: actualInputSha,
  search_algorithm_version: SEARCH_ALGORITHM_VERSION,
  index_format_version: INDEX_FORMAT_VERSION,
  document_count: documents.length,
  held_document_count: heldCount,
  generated_at: GENERATED_AT,
  source_sha: SOURCE_SHA,
  source_tree_hash: SOURCE_TREE_HASH,
  source_field_policy_hash: sourceFieldPolicyHash,
  unicode_version: PINNED_UNICODE_VERSION,
  normalization_version: "nfc-nfkc-casefold-latin-diacritic-v1",
  index_sha256: documentsSha,
  index_bytes: documentsBytes,
  index_gzip_bytes: documentsGzipBytes,
  document_order: "stableId ascending by Unicode code point",
  public_fields: ["stableId", "title"],
  runtime_bounds: {
    max_query_code_points: 160,
    max_query_tokens: 24,
    max_page_size: 100,
    max_document_title_code_points: MAX_DOCUMENT_TITLE_CODE_POINTS,
    max_document_tokens: MAX_DOCUMENT_TOKENS,
    max_document_token_code_points: MAX_DOCUMENT_TOKEN_CODE_POINTS,
    max_edit_distance: 2,
  },
};
const manifestText = stableJson(manifest);
const manifestSha = sha256(manifestText);
const checksumsText = `${documentsSha}  documents.json\n${manifestSha}  manifest.json\n`;

if (checkOnly) {
  await Promise.all([
    expectFile(documentsPath, documentsText),
    expectFile(manifestPath, manifestText),
    expectFile(checksumsPath, checksumsText),
  ]);
} else {
  await mkdir(outputDirectory, { recursive: true });
  await Promise.all([
    writeFile(documentsPath, documentsText),
    writeFile(manifestPath, manifestText),
    writeFile(checksumsPath, checksumsText),
  ]);
}

console.log(JSON.stringify({
  mode: checkOnly ? "check" : "write",
  documentCount: documents.length,
  heldDocumentCount: heldCount,
  indexSha256: documentsSha,
  indexBytes: documentsBytes,
  indexGzipBytes: documentsGzipBytes,
}, null, 2));
