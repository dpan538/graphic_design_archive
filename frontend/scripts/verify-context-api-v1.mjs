import { createHash } from "node:crypto";
import { readFileSync, readdirSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(here, "..");
const repositoryRoot = join(frontendRoot, "..");
const require = createRequire(import.meta.url);
const jiti = require("jiti")(fileURLToPath(import.meta.url), {
  interopDefault: true,
  alias: {
    "@": join(frontendRoot, "src"),
    "server-only": join(here, "server-only-marker.mjs"),
  },
});

const { DerivedV49ArchiveRepositoryProvider } = await jiti.import(
  join(frontendRoot, "src/features/search-v49/server/derived-repository.ts"),
);
const { GovernedContextArchiveRepositoryProvider } = await jiti.import(
  join(frontendRoot, "src/lib/read-platform/server/context-repository-provider.ts"),
);
const { dispatchReadApiRequest } = await jiti.import(
  join(frontendRoot, "src/lib/read-platform/server/read-api-controller.ts"),
);
const { getArchiveRepositoryProvider } = await jiti.import(
  join(frontendRoot, "src/lib/read-platform/server/provider.ts"),
);
const {
  getGovernedContextProjectionInfo,
  getGovernedContextSampleOptions,
  lookupGovernedContextDataset,
} = await jiti.import(
  join(frontendRoot, "src/features/trace-v49/context/governed/reader.server.ts"),
);

const generatedRoot = join(frontendRoot, "generated/trace-context-v1");
const frozenSearchRepositoryPath = join(
  frontendRoot,
  "src/features/search-v49/server/derived-repository.ts",
);
assert(
  sha256(readFileSync(frozenSearchRepositoryPath)) === "9ecdc0ed5dc74d3ebf315e7a74b615b487b242650dd8ddf009cf079d771c1f92",
  "frozen Search repository source changed",
);
const manifest = JSON.parse(readFileSync(join(generatedRoot, "manifest.json"), "utf8"));
const recordsPayload = JSON.parse(readFileSync(join(generatedRoot, "records.json"), "utf8"));
const ledgerLines = readFileSync(
  join(repositoryRoot, "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv"),
  "utf8",
).split(/\r?\n/u).filter(Boolean);
const ledgerHeaders = ledgerLines.shift().split("\t");
const stableIdColumn = ledgerHeaders.indexOf("surface_id_exact");
const dispositionColumn = ledgerHeaders.indexOf("research_disposition");

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function pathSegments(url) {
  return new URL(url).pathname.replace(/^\/api\/v1\/?/u, "").split("/").filter(Boolean);
}

function collectKeys(value, keys = new Set()) {
  if (!value || typeof value !== "object") return keys;
  for (const [key, child] of Object.entries(value)) {
    keys.add(key);
    collectKeys(child, keys);
  }
  return keys;
}

function listSourceFiles(root) {
  const files = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    const path = join(root, entry.name);
    if (entry.isDirectory()) files.push(...listSourceFiles(path));
    else if (/\.(?:ts|tsx|js|mjs)$/u.test(entry.name)) files.push(path);
  }
  return files;
}

async function dispatch(provider, path, init = {}) {
  const url = `https://archive.invalid${path}`;
  const request = new Request(url, init);
  const response = await dispatchReadApiRequest(request, pathSegments(url), provider);
  const text = await response.text();
  return {
    status: response.status,
    headers: Object.fromEntries(response.headers.entries()),
    text,
    body: text ? JSON.parse(text) : null,
    sha256: sha256(text),
  };
}

assert(Array.isArray(recordsPayload.records) && recordsPayload.records.length === 7_995, "generated Context record count differs");
const publicRecordId = recordsPayload.records[0]?.selectedRecord?.surfaceId;
assert(typeof publicRecordId === "string", "generated Context record ID is unavailable");
const heldRecordId = ledgerLines
  .map((line) => line.split("\t"))
  .find((cells) => cells[dispositionColumn] === "held")?.[stableIdColumn];
assert(typeof heldRecordId === "string", "held negative-test identity is unavailable");
const unknownRecordId = "SURF-CONTEXT-V1-UNKNOWN-RECORD";
const provider = new GovernedContextArchiveRepositoryProvider(
  new DerivedV49ArchiveRepositoryProvider(),
);
const productionProvider = getArchiveRepositoryProvider();
const productionOpened = await productionProvider.open({ research: { alias: "current" } });
assert(productionOpened.ok && typeof productionOpened.data.getTraceContext === "function", "production provider did not attach governed Context capability");
const exactBase = `/api/v1/releases/${encodeURIComponent(manifest.sourceRelease.id)}`;
const exactHeaders = {
  "Archive-Research-Manifest-Sha256": manifest.sourceRelease.manifestSha256,
};
const resource = (id) => `${exactBase}/trace/objects/${encodeURIComponent(id)}/context`;

const success = await dispatch(provider, resource(publicRecordId), { headers: exactHeaders });
assert(success.status === 200, `Context GET expected 200, got ${success.status}`);
assert(success.headers["cache-control"] === "no-store", "Context cache policy drifted");
assert(success.headers.vary === "Archive-Research-Manifest-Sha256", "Context Vary header drifted");
assert(success.headers.allow === "GET, HEAD, OPTIONS", "Context Allow header drifted");
assert(success.headers["archive-research-release-id"] === manifest.sourceRelease.id, "research release response header drifted");
assert(success.headers["archive-research-manifest-sha256"] === manifest.sourceRelease.manifestSha256, "research manifest response header drifted");

const envelope = success.body;
const dataset = envelope?.data;
assert(envelope?.apiVersion === "v1", "Read API envelope version drifted");
assert(envelope?.researchReleaseId === manifest.sourceRelease.id, "Read API envelope release drifted");
assert(envelope?.researchManifestSha256 === manifest.sourceRelease.manifestSha256, "Read API envelope manifest drifted");
assert(dataset?.schemaVersion === "trace-context/v1", "Context DTO schema drifted");
assert(dataset?.explanationRegistryVersion === "trace-context-explanations-v1", "Context explanation registry version drifted");
assert(dataset?.release?.researchReleaseId === manifest.sourceRelease.id, "Context DTO release drifted");
assert(dataset?.release?.researchManifestSha256 === manifest.sourceRelease.manifestSha256, "Context DTO manifest drifted");
assert(dataset?.release?.contextProjectionId === manifest.projectionId, "Context DTO projection ID drifted");
assert(dataset?.release?.contextProjectionSha256 === manifest.projectionSha256, "Context DTO projection hash drifted");
assert(dataset?.selectedRecord?.surfaceId === publicRecordId, "Context DTO selected record drifted");
assert(dataset?.availability === "ready", "Context DTO public record is not ready");
assert(dataset?.counts?.representations === dataset?.representations?.length, "Context representation count drifted");
assert(dataset?.accessibleRows?.length === dataset?.representations?.length + 1, "accessible row count drifted");

const rootMetadata = dataset?.selectedRecord?.rootMetadata;
assert(rootMetadata && ["creatorAttribution", "objectType", "dateDisplay", "sourceName"].every((key) => typeof rootMetadata[key] === "string"), "safe root metadata shape drifted");
const explanations = new Map(dataset.explanations.map((item) => [item.explanationCode, item]));
const representationIds = new Set();
for (const representation of dataset.representations) {
  assert(/^CTXA:[0-9a-f]{64}$/u.test(representation.id), "governed representation ID is invalid");
  assert(/^CTX:(?:MEDIUM|THEME|MOVEMENT):[0-9a-f]{64}$/u.test(representation.termId), "governed term ID is invalid");
  assert(/^CTXP:[0-9a-f]{64}$/u.test(representation.provenance?.provenanceId), "governed provenance ID is invalid");
  assert(!representationIds.has(representation.id), "duplicate selected-dataset representation ID");
  representationIds.add(representation.id);
  assert(["medium", "theme", "movement_context"].includes(representation.kind), "invalid Context kind");
  assert(representation.epistemicRole === "project_curated_context", "Context epistemic role drifted");
  assert(representation.publicationState === "published", "unexpected Context publication state");
  assert(representation.provenance?.sourceState === "proposed", "frozen source state was relabeled");
  assert(representation.provenance?.basis === "project_curated_typed_membership", "Context provenance basis drifted");
  assert(representation.provenance?.decision === "PUBLISHED", "Context provenance decision drifted");
  assert(representation.provenance?.mappingPolicyVersion === "trace-context-governance-mapping-v1", "Context mapping policy drifted");
  assert(representation.provenance?.governancePolicyVersion === "context-governance-v1", "Context governance policy drifted");
  assert(explanations.get(representation.explanationCode)?.contextKind === representation.kind, "representation explanation did not resolve");
  assert(dataset.accessibleRows.some((row) => row.explanationCode === representation.explanationCode && row.id.includes(representation.id)), "equivalent accessible row did not resolve");
}

const forbiddenKeys = new Set([
  "curatedMemberships", "semanticEdges", "memberships", "folderId", "folderToken",
  "internalId", "internalUuid", "rawMemberships", "sourceUrl", "url", "href",
]);
const leakedKeys = [...collectKeys(dataset)].filter((key) => forbiddenKeys.has(key));
assert(leakedKeys.length === 0, `forbidden Context DTO keys: ${leakedKeys.join(",")}`);
const serializedDataset = JSON.stringify(dataset);
assert(!serializedDataset.includes("ctxv49:"), "validation-only ID entered governed DTO");
assert(!/\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b/iu.test(serializedDataset), "internal UUID entered governed DTO");
assert(!Object.hasOwn(dataset, "records") && !Object.hasOwn(dataset, "terms"), "full Context corpus entered selected DTO");

const repeat = await dispatch(provider, resource(publicRecordId), { headers: exactHeaders });
assert(repeat.status === 200 && repeat.sha256 === success.sha256, "Context GET serialization is not deterministic");
const current = await dispatch(provider, `/api/v1/releases/current/trace/objects/${encodeURIComponent(publicRecordId)}/context`);
assert(current.status === 200 && current.sha256 === success.sha256, "current and exact Context resources differ");

const head = await dispatch(provider, resource(publicRecordId), { method: "HEAD", headers: exactHeaders });
assert(head.status === 200 && head.text === "", "Context HEAD status/body drifted");
assert(head.headers["archive-research-manifest-sha256"] === manifest.sourceRelease.manifestSha256, "Context HEAD release pin is absent");
const options = await dispatch(provider, resource(publicRecordId), { method: "OPTIONS", headers: exactHeaders });
assert(options.status === 204 && options.text === "", "Context OPTIONS status/body drifted");
assert(options.headers.allow === "GET, HEAD, OPTIONS", "Context OPTIONS Allow header drifted");
for (const method of ["POST", "PUT", "PATCH", "DELETE"]) {
  const denied = await dispatch(provider, resource(publicRecordId), { method, headers: exactHeaders });
  assert(denied.status === 405 && denied.headers.allow === "GET, HEAD, OPTIONS", `Context ${method} was not denied`);
}

const malformed = await dispatch(provider, resource("not-a-public-stable-id"), { headers: exactHeaders });
assert(malformed.status === 400 && malformed.body?.code === "INVALID_ARGUMENT", "malformed Context ID did not return 400");
const held = await dispatch(provider, resource(heldRecordId), { headers: exactHeaders });
const unknown = await dispatch(provider, resource(unknownRecordId), { headers: exactHeaders });
assert(held.status === 404 && unknown.status === 404, "held/unknown Context lookup did not return 404");
assert(held.text === unknown.text, "held and unknown Context problem bodies differ");
assert(!held.text.includes(heldRecordId), "held Context problem body reflected a held ID");
const heldHead = await dispatch(provider, resource(heldRecordId), { method: "HEAD", headers: exactHeaders });
assert(heldHead.status === 404 && heldHead.text === "", "held Context HEAD did not fail closed");

const badPair = await dispatch(provider, resource(publicRecordId), {
  headers: { "Archive-Research-Manifest-Sha256": "0".repeat(64) },
});
assert(badPair.status === 404 && badPair.body?.code === "RELEASE_NOT_FOUND", "unavailable exact release pair did not return 404");
const wrongProjectionPair = lookupGovernedContextDataset(publicRecordId, {
  researchReleaseId: manifest.sourceRelease.id,
  researchManifestSha256: "0".repeat(64),
});
assert(!wrongProjectionPair.ok && wrongProjectionPair.code === "RELEASE_VERSION_MISMATCH", "projection/repository mismatch did not fail with 409-class code");

const info = getGovernedContextProjectionInfo();
assert(info.recordCount === 7_995 && info.termCount === 25 && info.representationCount === 16_106, "Context projection reader census drifted");
assert(info.projectionSha256 === manifest.projectionSha256, "Context reader projection hash drifted");
const samples = getGovernedContextSampleOptions();
assert(samples.length === 12, "Context route sample count drifted");
assert(new Set(samples.map((item) => item.stableId)).size === samples.length, "Context route samples are not unique");
assert(samples.every((item) => /^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$/u.test(item.stableId) && item.title.trim()), "Context route sample shape drifted");
assert(JSON.stringify(samples) === JSON.stringify(getGovernedContextSampleOptions()), "Context route samples are not deterministic");

let failedContextObjects = 0;
let apiSerializationFailures = 0;
let governedValidationIdCount = 0;
for (const sourceRecord of recordsPayload.records) {
  const result = lookupGovernedContextDataset(sourceRecord.selectedRecord.surfaceId, {
    researchReleaseId: manifest.sourceRelease.id,
    researchManifestSha256: manifest.sourceRelease.manifestSha256,
  });
  if (!result.ok) {
    failedContextObjects += 1;
    continue;
  }
  try {
    const serialized = JSON.stringify({ apiVersion: "v1", data: result.data });
    if (!serialized || JSON.parse(serialized).data?.selectedRecord?.surfaceId !== sourceRecord.selectedRecord.surfaceId) {
      apiSerializationFailures += 1;
    }
    governedValidationIdCount += serialized.match(/ctxv49:/gu)?.length ?? 0;
  } catch {
    apiSerializationFailures += 1;
  }
}
const heldIds = ledgerLines
  .map((line) => line.split("\t"))
  .filter((cells) => cells[dispositionColumn] === "held")
  .map((cells) => cells[stableIdColumn]);
const heldObjectsExposed = heldIds.filter((stableId) => lookupGovernedContextDataset(stableId, {
  researchReleaseId: manifest.sourceRelease.id,
  researchManifestSha256: manifest.sourceRelease.manifestSha256,
}).ok).length;
assert(failedContextObjects === 0, `full-cohort Context failures: ${failedContextObjects}`);
assert(apiSerializationFailures === 0, `full-cohort API serialization failures: ${apiSerializationFailures}`);
assert(governedValidationIdCount === 0, `validation-only governed IDs exposed: ${governedValidationIdCount}`);
assert(heldObjectsExposed === 0, `held Context objects exposed: ${heldObjectsExposed}`);

const sourceFiles = listSourceFiles(join(frontendRoot, "src"));
const generatedImporters = sourceFiles.filter((path) => readFileSync(path, "utf8").includes("generated/trace-context-v1"));
assert(
  generatedImporters.length === 1 && generatedImporters[0].endsWith("/governed/reader.server.ts"),
  `governed corpus import boundary drifted: ${generatedImporters.join(",")}`,
);
const readerSource = readFileSync(generatedImporters[0], "utf8");
assert(readerSource.startsWith('import "server-only";'), "governed corpus reader lost its server-only guard");
const clientServerReaderImports = sourceFiles.filter((path) => {
  const source = readFileSync(path, "utf8");
  return /^\s*["']use client["'];/u.test(source)
    && /context\/governed\/(?:reader|index)\.server/u.test(source);
});
assert(clientServerReaderImports.length === 0, `client module imports governed server reader: ${clientServerReaderImports.join(",")}`);

console.log([
  "CONTEXT_API_V1=PASS",
  "ENDPOINT_TEMPLATES_ADDED=1",
  `PUBLIC_RECORD=${publicRecordId}`,
  `REPRESENTATIONS=${dataset.representations.length}`,
  `PROJECTION_SHA256=${manifest.projectionSha256}`,
  "GET=PASS",
  "HEAD=PASS",
  "OPTIONS=PASS",
  "MALFORMED_400=PASS",
  "HELD_UNKNOWN_PARITY=PASS",
  "RELEASE_PINNING=PASS",
  "DETERMINISM=PASS",
  `PUBLIC_OBJECTS_TESTED=${recordsPayload.records.length}`,
  `HELD_OBJECTS_EXPOSED=${heldObjectsExposed}`,
  `FAILED_CONTEXT_OBJECTS=${failedContextObjects}`,
  `API_SERIALIZATION_FAILURES=${apiSerializationFailures}`,
  `GOVERNED_CONTEXT_VALIDATION_ID_COUNT=${governedValidationIdCount}`,
  "FULL_CONTEXT_CORPUS_IN_CLIENT_BUNDLE=false",
  "INTERNAL_ID_EXPOSURE_COUNT=0",
].join(" "));
