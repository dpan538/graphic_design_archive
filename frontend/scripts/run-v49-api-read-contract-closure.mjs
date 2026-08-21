#!/usr/bin/env node
// Exhaustive server-side Read API contract and runtime verification against a
// fresh sealed PostgreSQL release. This script never starts a browser and all
// application queries use the formal read-only API role.

import { createHash } from "node:crypto";
import { spawn, spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { performance } from "node:perf_hooks";

function parseArguments(argv) {
  const parsed = {};
  for (let index = 2; index < argv.length; index += 2) parsed[argv[index]] = argv[index + 1];
  return parsed;
}
const args = parseArguments(process.argv);
for (const key of ["--psql", "--host", "--port", "--database", "--repo", "--output", "--examples-output", "--runtime-json", "--runtime-csv", "--runtime-md", "--held-surface"]) {
  if (!args[key]) throw new Error(`missing ${key}`);
}
if (!args["--host"].startsWith("/private/tmp/") || args["--port"] === "5432" || !args["--database"].startsWith("gda_v49_phase2a_")) {
  throw new Error("isolated local database boundary rejected");
}

const repoRoot = resolve(args["--repo"]);
const require = createRequire(import.meta.url);
const jiti = require("jiti")(import.meta.url, {
  interopDefault: true,
  alias: {
    "@": `${repoRoot}/frontend/src`,
    "server-only": `${repoRoot}/frontend/scripts/server-only-marker.mjs`,
  },
});
const { PostgresArchiveRepositoryProvider } = jiti(`${repoRoot}/frontend/src/lib/read-platform/server/postgres-repository.ts`);
const { dispatchReadApiRequest } = jiti(`${repoRoot}/frontend/src/lib/read-platform/server/read-api-controller.ts`);

const apiRole = "gda_v49_phase2a_api_reader";
const dbEnv = {
  ...process.env,
  PGHOST: args["--host"],
  PGPORT: args["--port"],
  PGDATABASE: args["--database"],
  PGUSER: apiRole,
};
let databaseQueryCount = 0;

function sqlLiteral(value, index, variables) {
  if (value === null || value === undefined) return "NULL";
  if (typeof value === "number") return String(value);
  if (typeof value === "boolean") return value ? "TRUE" : "FALSE";
  const name = `gda_value_${index}`;
  variables.push("-v", `${name}=${String(value)}`);
  return `:'${name}'`;
}

function runPsql(psqlArgs, { timeoutMs = 30_000, env = dbEnv, input = "" } = {}) {
  return new Promise((accept, reject) => {
    const child = spawn(args["--psql"], psqlArgs, { env, stdio: ["pipe", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    let timedOut = false;
    const timer = setTimeout(() => { timedOut = true; child.kill("SIGTERM"); }, timeoutMs);
    child.stdout.on("data", (chunk) => { stdout += chunk; });
    child.stderr.on("data", (chunk) => { stderr += chunk; });
    child.on("error", reject);
    child.on("close", (status, signal) => {
      clearTimeout(timer);
      accept({ status, signal, stdout, stderr, timedOut });
    });
    child.stdin.end(input);
  });
}

class PsqlReader {
  async query(sql, values, signal) {
    if (signal?.aborted) throw new DOMException("request aborted", "AbortError");
    databaseQueryCount += 1;
    const variables = [];
    const parameters = values.map((value, index) => sqlLiteral(value, index + 1, variables));
    const execute = parameters.length ? `EXECUTE gda_read(${parameters.join(",")})` : "EXECUTE gda_read";
    const wrapped = `PREPARE gda_read AS SELECT coalesce(jsonb_agg(to_jsonb(gda_rows)), '[]'::jsonb) FROM (${sql}) gda_rows; ${execute};`;
    const result = await runPsql(["-X", "-Atq", "-v", "ON_ERROR_STOP=1", ...variables], { input: `${wrapped}\n` });
    if (result.timedOut) throw new Error("read query timed out");
    if (result.status !== 0) throw new Error(`read query failed: ${result.stderr.trim()}`);
    const lines = result.stdout.split("\n").filter((line) => line.startsWith("[") || line === "[]");
    if (!lines.length) throw new Error("read query returned no JSON envelope");
    return { rows: JSON.parse(lines.at(-1)) };
  }
}

const reader = new PsqlReader();
const provider = new PostgresArchiveRepositoryProvider(reader);
const baseOrigin = "http://api-contract.local";
function segments(url) { return new URL(url).pathname.replace(/^\/api\/v1\/?/, "").split("/").filter(Boolean); }
function sha256(value) { return createHash("sha256").update(typeof value === "string" ? value : JSON.stringify(value)).digest("hex"); }
function assert(condition, message) { if (!condition) throw new Error(message); }
function stable(value) { return JSON.stringify(value); }
function output(path, value) { const target = resolve(path); mkdirSync(dirname(target), { recursive: true }); writeFileSync(target, value); }
function headerObject(headers) { return Object.fromEntries([...headers.entries()].sort(([a], [b]) => a.localeCompare(b))); }
function percentile(sorted, p) { return sorted[Math.max(0, Math.ceil(sorted.length * p) - 1)]; }
function countReturned(body) {
  if (!body || typeof body !== "object") return 0;
  const data = body.data;
  if (Array.isArray(data)) return data.length;
  if (Array.isArray(data?.nodes)) return data.nodes.length;
  return data ? 1 : 0;
}
function assertEnvelope(item, releaseId, manifest) {
  if (item.status !== 200) return;
  assert(item.body?.apiVersion === "v1", `${item.name}: missing v1 envelope`);
  assert(item.body?.researchReleaseId === releaseId, `${item.name}: release ID mismatch`);
  assert(item.body?.researchManifestSha256 === manifest, `${item.name}: manifest mismatch`);
  assert(item.headers["archive-research-release-id"] === releaseId, `${item.name}: release response header mismatch`);
  assert(item.headers["archive-research-manifest-sha256"] === manifest, `${item.name}: manifest response header mismatch`);
}
function assertProblem(item) {
  if (item.status < 400 || item.method === "HEAD") return;
  assert(typeof item.body?.code === "string", `${item.name}: error code missing`);
  assert(typeof item.body?.detail === "string", `${item.name}: error detail missing`);
}
function assertNoInternalLeak(item) {
  const body = stable(item.body);
  for (const token of ["raw.", "core.", "provenance.", "research.", "rights.", "release.", "pg_catalog", "information_schema"]) {
    assert(!body.includes(token), `${item.name}: leaked internal schema token ${token}`);
  }
}

async function request(name, url, init = {}, record = true) {
  const started = performance.now();
  const requestObject = new Request(url, init);
  const queryBefore = databaseQueryCount;
  const response = await dispatchReadApiRequest(requestObject, segments(url), provider);
  const text = await response.text();
  const elapsedMs = performance.now() - started;
  let body = null;
  if (text) {
    try { body = JSON.parse(text); } catch { throw new Error(`${name}: non-JSON response body`); }
  }
  const item = {
    name,
    method: requestObject.method,
    url,
    path: new URL(url).pathname,
    query: Object.fromEntries(new URL(url).searchParams),
    status: response.status,
    headers: headerObject(response.headers),
    contentType: response.headers.get("content-type"),
    responseBytes: Buffer.byteLength(text),
    returnedRecords: countReturned(body),
    elapsedMs: Number(elapsedMs.toFixed(3)),
    databaseQueryCount: databaseQueryCount - queryBefore,
    body,
    bodySha256: sha256(text),
  };
  if (record) contractResults.push(item);
  return item;
}

async function apiViewFingerprint() {
  const [descriptors, surfaces] = await Promise.all([
    reader.query("SELECT research_release_id, research_manifest_sha256, schema_version, model_version, object_count, relation_count, trace_eligible_object_count FROM api_v1.sealed_research_release_descriptor ORDER BY research_release_id, research_manifest_sha256", []),
    reader.query("SELECT research_release_id, research_manifest_sha256, surface_id, title, publication_layer, object_urn FROM api_v1.sealed_surface ORDER BY research_release_id, research_manifest_sha256, surface_id", []),
  ]);
  return { descriptorCount: descriptors.rows.length, surfaceCount: surfaces.rows.length, sha256: sha256({ descriptors: descriptors.rows, surfaces: surfaces.rows }) };
}

const descriptorResult = await reader.query("SELECT research_release_id, research_manifest_sha256, object_count, relation_count, trace_eligible_object_count FROM api_v1.sealed_research_release_descriptor ORDER BY sealed_at DESC LIMIT 1", []);
assert(descriptorResult.rows.length === 1, "one sealed descriptor is required");
const descriptor = descriptorResult.rows[0];
const releaseId = descriptor.research_release_id;
const manifest = descriptor.research_manifest_sha256;
const exactBase = `${baseOrigin}/api/v1/releases/${encodeURIComponent(releaseId)}`;
const exactHeaders = { "Archive-Research-Manifest-Sha256": manifest };
const surfaceRows = await reader.query("SELECT surface_id, title FROM api_v1.sealed_surface WHERE research_release_id=$1 AND research_manifest_sha256=$2 ORDER BY surface_id", [releaseId, manifest]);
assert(surfaceRows.rows.length === Number(descriptor.object_count), "descriptor and sealed_surface counts differ");
const knownSurface = surfaceRows.rows[0];
const unicodeSurface = surfaceRows.rows.find((row) => /[^\u0000-\u007f]/u.test(row.title ?? "")) ?? knownSurface;
const punctuationSurface = surfaceRows.rows.find((row) => /['“”‘’.,:;!?()-]/u.test(row.title ?? "")) ?? knownSurface;
const heldSurface = args["--held-surface"];
const contractResults = [];
const examples = {};
const beforeFingerprint = await apiViewFingerprint();

const endpointCases = [
  { id: "visual-registry-current", template: "/api/v1/visual-registries/current", url: `${baseOrigin}/api/v1/visual-registries/current`, expected: 404 },
  { id: "current-release", template: "/api/v1/releases/{release}", url: `${baseOrigin}/api/v1/releases/current`, expected: 200 },
  { id: "release-manifest", template: "/api/v1/releases/{release}/manifest", url: `${exactBase}/manifest`, expected: 200 },
  { id: "archive-overview", template: "/api/v1/releases/{release}/archive/overview", url: `${exactBase}/archive/overview`, expected: 200 },
  { id: "folder-types", template: "/api/v1/releases/{release}/folder-types", url: `${exactBase}/folder-types`, expected: 200 },
  { id: "folders", template: "/api/v1/releases/{release}/folders", url: `${exactBase}/folders?first=10`, expected: 200 },
  { id: "folder-members", template: "/api/v1/releases/{release}/folders/{id}/surfaces", url: `${exactBase}/folders/not-published/surfaces?first=10`, expected: 404 },
  { id: "folder-detail", template: "/api/v1/releases/{release}/folders/{id}", url: `${exactBase}/folders/not-published`, expected: 404 },
  { id: "surface-detail", template: "/api/v1/releases/{release}/surfaces/{id}", url: `${exactBase}/surfaces/${encodeURIComponent(knownSurface.surface_id)}`, expected: 200 },
  { id: "search", template: "/api/v1/releases/{release}/search", url: `${exactBase}/search?q=Poster&first=10`, expected: 200 },
  { id: "trace-atlas", template: "/api/v1/releases/{release}/trace/atlas", url: `${exactBase}/trace/atlas`, expected: 200 },
  { id: "trace-objects", template: "/api/v1/releases/{release}/trace/objects", url: `${exactBase}/trace/objects?first=10`, expected: 200 },
  { id: "trace-neighborhood", template: "/api/v1/releases/{release}/trace/objects/{id}/neighborhood", url: `${exactBase}/trace/objects/${encodeURIComponent(knownSurface.surface_id)}/neighborhood`, expected: 404 },
  { id: "relation-types", template: "/api/v1/releases/{release}/trace/relation-types", url: `${exactBase}/trace/relation-types`, expected: 200 },
  { id: "relation-type", template: "/api/v1/releases/{release}/trace/relation-types/{id}", url: `${exactBase}/trace/relation-types/not-published`, expected: 404 },
  { id: "relation-detail", template: "/api/v1/releases/{release}/relations/{id}", url: `${exactBase}/relations/not-published`, expected: 404 },
  { id: "claim-detail", template: "/api/v1/releases/{release}/claims/{id}", url: `${exactBase}/claims/not-published`, expected: 404 },
  { id: "corpus-detail", template: "/api/v1/releases/{release}/corpora/{version}", url: `${exactBase}/corpora/not-published`, expected: 404 },
];

for (const endpoint of endpointCases) {
  const item = await request(endpoint.id, endpoint.url, endpoint.url.includes("/current") ? {} : { headers: exactHeaders });
  assert(item.status === endpoint.expected, `${endpoint.id}: expected ${endpoint.expected}, got ${item.status}`);
  assert(item.status < 500, `${endpoint.id}: unexpected 5xx`);
  if (item.body !== null) assert(item.contentType?.startsWith("application/json"), `${endpoint.id}: content type mismatch`);
  assertEnvelope(item, releaseId, manifest);
  assertProblem(item);
  assertNoInternalLeak(item);
  const repeat = await request(`${endpoint.id}-deterministic-repeat`, endpoint.url, endpoint.url.includes("/current") ? {} : { headers: exactHeaders });
  assert(item.status === repeat.status && item.bodySha256 === repeat.bodySha256, `${endpoint.id}: repeat response drift`);
  examples[endpoint.template] = { primary: item, deterministicRepeat: { status: repeat.status, bodySha256: repeat.bodySha256 } };
  process.stdout.write(`contract ${endpoint.id} PASS\n`);
}

const overview = contractResults.find((item) => item.name === "archive-overview");
assert(overview.body.data.objectCount === Number(descriptor.object_count), "overview object count mismatch");
assert(overview.body.data.traceEligibleObjectCount === Number(descriptor.trace_eligible_object_count), "overview TRACE count mismatch");
assert(overview.body.data.folderCount === 0, "overview folder count must fail closed at zero");
assert(overview.body.data.positiveVisualRightsCount === 0, "overview rights count widened");
const surfaceDetail = contractResults.find((item) => item.name === "surface-detail");
assert(surfaceDetail.body.data.surfaceId === knownSurface.surface_id, "surface stable ID mismatch");
assert(surfaceDetail.body.data.title === (knownSurface.title ?? knownSurface.surface_id), "surface title mismatch");
assert(surfaceDetail.body.data.deliveryState === "CITATION_ONLY", "surface delivery state widened");

async function searchCase(name, parameters, expectedStatus, predicate = () => true) {
  const url = `${exactBase}/search?${parameters}`;
  const item = await request(name, url, { headers: exactHeaders });
  assert(item.status === expectedStatus, `${name}: expected ${expectedStatus}, got ${item.status}`);
  assert(item.status < 500, `${name}: unexpected 5xx`);
  assert(predicate(item), `${name}: response predicate failed`);
  if (item.status === 200) assertEnvelope(item, releaseId, manifest); else assertProblem(item);
  assertNoInternalLeak(item);
  return item;
}

const exactTitle = knownSurface.title;
const exact = await searchCase("search-known-exact-title", new URLSearchParams({ q: exactTitle, first: "100" }), 200, (item) => item.body.data.nodes.some((node) => node.surface.surfaceId === knownSurface.surface_id));
const canonicalSearch = await searchCase("search-canonical-request", new URLSearchParams({ q: "Poster", first: "10" }), 200, (item) => item.body.data.nodes.length === 10);
await searchCase("search-no-result", new URLSearchParams({ q: "gda-definitely-no-result-6d8f", first: "10" }), 200, (item) => item.body.data.nodes.length === 0 && item.body.data.pageInfo.totalExact === 0);
await searchCase("search-empty-query", "q=&first=10", 400);
await searchCase("search-whitespace-only", new URLSearchParams({ q: "   ", first: "10" }), 400);
const trimmed = await searchCase("search-trimmed", new URLSearchParams({ q: "  Poster  ", first: "10" }), 200);
assert(trimmed.bodySha256 === canonicalSearch.bodySha256, "trimmed query changed canonical response");
const caseVariant = await searchCase("search-case-variation", new URLSearchParams({ q: "pOsTeR", first: "10" }), 200);
assert(caseVariant.bodySha256 === canonicalSearch.bodySha256, "case variation changed canonical response");
await searchCase("search-unicode", new URLSearchParams({ q: unicodeSurface.title, first: "100" }), 200, (item) => item.body.data.nodes.some((node) => node.surface.surfaceId === unicodeSurface.surface_id));
await searchCase("search-punctuation", new URLSearchParams({ q: punctuationSurface.title, first: "100" }), 200, (item) => item.body.data.nodes.some((node) => node.surface.surfaceId === punctuationSurface.surface_id));
const encoded = await searchCase("search-url-encoded", `q=${encodeURIComponent("Poster")}&first=10`, 200);
assert(encoded.bodySha256 === canonicalSearch.bodySha256, "URL encoding changed canonical response");
const repeated = await searchCase("search-repeated-query-parameter", "q=Poster&q=does-not-exist&first=10", 200);
assert(repeated.bodySha256 === canonicalSearch.bodySha256, "repeated q did not use the first value");
await searchCase("search-page-invalid-ignored", new URLSearchParams({ q: "Poster", page: "invalid", first: "10" }), 200);
await searchCase("search-page-zero-ignored", new URLSearchParams({ q: "Poster", page: "0", first: "10" }), 200);
await searchCase("search-page-negative-ignored", new URLSearchParams({ q: "Poster", page: "-1", first: "10" }), 200);
await searchCase("search-first-zero", new URLSearchParams({ q: "Poster", first: "0" }), 400);
await searchCase("search-first-negative", new URLSearchParams({ q: "Poster", first: "-1" }), 400);
await searchCase("search-first-decimal", new URLSearchParams({ q: "Poster", first: "1.5" }), 400);
await searchCase("search-first-over-maximum", new URLSearchParams({ q: "Poster", first: "101" }), 400);
await searchCase("search-first-not-a-number", new URLSearchParams({ q: "Poster", first: "not-a-number" }), 400);
await searchCase("search-very-long-query", new URLSearchParams({ q: "x".repeat(121), first: "10" }), 400);
const literalMatchCount = (query) => surfaceRows.rows.filter((row) => (row.title ?? "").toLowerCase().includes(query.toLowerCase())).length;
await searchCase("search-sql-metacharacters", new URLSearchParams({ q: "' OR 1=1 --", first: "10" }), 200, (item) => item.body.data.pageInfo.totalExact === literalMatchCount("' OR 1=1 --"));
await searchCase("search-wildcard-percent-literal", new URLSearchParams({ q: "%", first: "10" }), 200, (item) => item.body.data.pageInfo.totalExact === literalMatchCount("%") && item.body.data.pageInfo.totalExact < surfaceRows.rows.length);
await searchCase("search-wildcard-underscore-literal", new URLSearchParams({ q: "_", first: "10" }), 200, (item) => item.body.data.pageInfo.totalExact === literalMatchCount("_") && item.body.data.pageInfo.totalExact < surfaceRows.rows.length);
await searchCase("search-invalid-scope", new URLSearchParams({ q: "Poster", scope: "invalid", first: "10" }), 400);
await searchCase("search-trace-scope-empty", new URLSearchParams({ q: "Poster", scope: "trace", first: "10" }), 200, (item) => item.body.data.nodes.length === 0);
await searchCase("search-relation-scope-empty", new URLSearchParams({ q: "Poster", scope: "relation", first: "10" }), 200, (item) => item.body.data.nodes.length === 0);
await searchCase("search-invalid-cursor", new URLSearchParams({ q: "Poster", first: "10", after: "invalid" }), 400);
await searchCase("search-cross-filter-cursor", new URLSearchParams({ q: "Portfolio", first: "10", after: canonicalSearch.body.data.pageInfo.nextCursor }), 400);

const expectedPosterRows = await reader.query("SELECT surface_id, title FROM api_v1.sealed_surface WHERE research_release_id=$1 AND research_manifest_sha256=$2 AND strpos(lower(coalesce(title, '')), lower($3)) > 0 ORDER BY surface_id", [releaseId, manifest, "Poster"]);
let cursor = null;
const pagedIds = [];
let finalPage = null;
do {
  const parameters = new URLSearchParams({ q: "Poster", first: "100" });
  if (cursor) parameters.set("after", cursor);
  finalPage = await searchCase(`search-exhaustive-page-${pagedIds.length / 100 + 1}`, parameters, 200);
  pagedIds.push(...finalPage.body.data.nodes.map((node) => node.surface.surfaceId));
  cursor = finalPage.body.data.pageInfo.nextCursor;
} while (cursor);
const expectedPosterIds = expectedPosterRows.rows.map((row) => row.surface_id);
assert(new Set(pagedIds).size === pagedIds.length, "search pagination contains duplicate stable IDs");
assert(pagedIds.length === expectedPosterIds.length, "search pagination omitted rows by count");
assert(stable([...pagedIds].sort()) === stable([...expectedPosterIds].sort()), "search pagination stable-ID set differs from api_v1 view");
assert(finalPage.body.data.pageInfo.hasNextPage === false && finalPage.body.data.pageInfo.nextCursor === null, "search final-page semantics mismatch");
for (const node of canonicalSearch.body.data.nodes) {
  const detail = await request(`search-detail-crosscheck-${node.surface.surfaceId}`, `${exactBase}/surfaces/${encodeURIComponent(node.surface.surfaceId)}`, { headers: exactHeaders });
  assert(detail.status === 200 && detail.body.data.surfaceId === node.surface.surfaceId, "search result did not resolve through detail endpoint");
}
const held = await request("held-quarantined-surface", `${exactBase}/surfaces/${encodeURIComponent(heldSurface)}`, { headers: exactHeaders });
assert(held.status === 404, "held/quarantined stable ID was exposed");
examples["/api/v1/releases/{release}/surfaces/{id}"].notFound = held;
examples["/api/v1/releases/{release}/search"].success = canonicalSearch;
examples["/api/v1/releases/{release}/search"].empty = contractResults.find((item) => item.name === "search-no-result");
examples["/api/v1/releases/{release}/search"].invalid = contractResults.find((item) => item.name === "search-empty-query");

const extraCases = [
  ["release-not-found", `${baseOrigin}/api/v1/releases/not-published/manifest`, { headers: { "Archive-Research-Manifest-Sha256": "0".repeat(64) } }, 404],
  ["release-manifest-mismatch", `${exactBase}/manifest`, { headers: { "Archive-Research-Manifest-Sha256": "0".repeat(64) } }, 404],
  ["surface-not-found", `${exactBase}/surfaces/not-published`, { headers: exactHeaders }, 404],
  ["unknown-resource", `${exactBase}/unknown`, { headers: exactHeaders }, 404],
  ["head-overview", `${exactBase}/archive/overview`, { method: "HEAD", headers: exactHeaders }, 200],
  ["options-overview", `${exactBase}/archive/overview`, { method: "OPTIONS", headers: exactHeaders }, 204],
];
for (const [name, url, init, expectedStatus] of extraCases) {
  const item = await request(name, url, init);
  assert(item.status === expectedStatus, `${name}: expected ${expectedStatus}, got ${item.status}`);
  assert(item.status < 500, `${name}: unexpected 5xx`);
}

// Materialize actual success/not-found/invalid examples for every discovered
// template. Where the sealed release publishes no singleton of that type, the
// catalog records the observed 404 and explicitly marks success unavailable;
// it never invents a fixture resource.
for (const endpoint of endpointCases) {
  const primary = contractResults.find((item) => item.name === endpoint.id);
  const entry = examples[endpoint.template];
  entry.successResponse = primary.status >= 200 && primary.status < 300 ? primary : null;
  entry.successUnavailableReason = entry.successResponse ? null : "the fresh sealed release publishes no resource of this type";
  if (primary.status === 404) entry.emptyOrNotFoundResponse = primary;
  else {
    const missingBase = `${baseOrigin}/api/v1/releases/not-published`;
    const missingUrl = endpoint.url.includes("/releases/current")
      ? endpoint.url.replace(`${baseOrigin}/api/v1/releases/current`, missingBase)
      : endpoint.url.replace(exactBase, missingBase);
    const missing = await request(`${endpoint.id}-example-not-found`, missingUrl, { headers: { "Archive-Research-Manifest-Sha256": "0".repeat(64) } });
    assert(missing.status === 404, `${endpoint.id}: example not-found response drift`);
    entry.emptyOrNotFoundResponse = missing;
  }
  if (endpoint.id === "folders" || endpoint.id === "trace-objects") {
    const invalidUrl = new URL(endpoint.url); invalidUrl.searchParams.set("first", "0");
    const invalid = await request(`${endpoint.id}-example-invalid`, invalidUrl.toString(), { headers: exactHeaders });
    assert(invalid.status === 400, `${endpoint.id}: example invalid response drift`);
    entry.invalidResponse = invalid;
    entry.invalidNotApplicableReason = null;
  } else if (endpoint.id === "search") {
    entry.invalidResponse = contractResults.find((item) => item.name === "search-empty-query");
    entry.invalidNotApplicableReason = null;
  } else {
    entry.invalidResponse = null;
    entry.invalidNotApplicableReason = "the implemented endpoint has no independently validated request parameter";
  }
}

function deniedSql(name, sql) {
  const probe = spawnSync(args["--psql"], ["-X", "-q", "-v", "ON_ERROR_STOP=1", "-c", sql], { env: dbEnv, encoding: "utf8", timeout: 30_000 });
  return { name, exitCode: probe.status, denied: probe.status !== 0, stderr: probe.stderr.trim() };
}
const roleProbes = [
  deniedSql("insert-core", "BEGIN; INSERT INTO core.archive_object DEFAULT VALUES; ROLLBACK;"),
  deniedSql("update-core", "BEGIN; UPDATE core.archive_object SET object_urn=object_urn WHERE false; ROLLBACK;"),
  deniedSql("delete-core", "BEGIN; DELETE FROM core.archive_object WHERE false; ROLLBACK;"),
  deniedSql("insert-research", "BEGIN; INSERT INTO research.corpus_membership DEFAULT VALUES; ROLLBACK;"),
  deniedSql("update-research", "BEGIN; UPDATE research.corpus_membership SET corpus_id=corpus_id WHERE false; ROLLBACK;"),
  deniedSql("delete-research", "BEGIN; DELETE FROM research.corpus_membership WHERE false; ROLLBACK;"),
  deniedSql("write-release", "BEGIN; DELETE FROM release.research_release_object WHERE false; ROLLBACK;"),
  deniedSql("ddl", "BEGIN; CREATE TABLE public.gda_api_forbidden_probe(id integer); ROLLBACK;"),
  deniedSql("raw-select", "SELECT 1 FROM raw.source_record LIMIT 1;"),
];
assert(roleProbes.every((probe) => probe.denied), "API role direct privilege boundary failed");

const methodResults = [];
for (const endpoint of endpointCases) {
  for (const method of ["POST", "PUT", "PATCH", "DELETE"]) {
    const item = await request(`${endpoint.id}-${method.toLowerCase()}-denied`, endpoint.url, { method, headers: exactHeaders });
    assert(item.status === 405, `${endpoint.id} ${method}: expected 405, got ${item.status}`);
    assert(item.headers.allow === "GET, HEAD, OPTIONS", `${endpoint.id} ${method}: Allow header mismatch`);
    methodResults.push(item);
  }
}
const afterFingerprint = await apiViewFingerprint();
assert(stable(beforeFingerprint) === stable(afterFingerprint), "API-visible release fingerprint changed after negative methods");

const runtimeRows = [];
const memoryBefore = process.memoryUsage().rss;
for (const endpoint of endpointCases) {
  const init = endpoint.url.includes("/current") ? {} : { headers: exactHeaders };
  const queryStart = databaseQueryCount;
  const cold = await request(`runtime-${endpoint.id}-cold`, endpoint.url, init, false);
  const warm = [];
  for (let index = 0; index < 20; index++) warm.push(await request(`runtime-${endpoint.id}-warm-${index + 1}`, endpoint.url, init, false));
  const concurrent = await Promise.all(Array.from({ length: 10 }, (_, index) => request(`runtime-${endpoint.id}-concurrent-${index + 1}`, endpoint.url, init, false)));
  const all = [cold, ...warm, ...concurrent];
  for (const item of all) {
    assert(item.status === endpoint.expected, `${item.name}: runtime status drift`);
    assert(item.status < 500, `${item.name}: runtime 5xx`);
    assert(item.bodySha256 === cold.bodySha256, `${item.name}: runtime response drift`);
  }
  const latencies = all.map((item) => item.elapsedMs).sort((a, b) => a - b);
  const statusDistribution = Object.fromEntries([...new Set(all.map((item) => item.status))].sort().map((status) => [status, all.filter((item) => item.status === status).length]));
  runtimeRows.push({
    endpointId: endpoint.id,
    template: endpoint.template,
    expectedStatus: endpoint.expected,
    requestCount: all.length,
    successCount: all.filter((item) => item.status === endpoint.expected).length,
    statusDistribution,
    coldLatencyMs: cold.elapsedMs,
    minLatencyMs: latencies[0],
    medianLatencyMs: percentile(latencies, 0.5),
    p95LatencyMs: percentile(latencies, 0.95),
    maxLatencyMs: latencies.at(-1),
    responseBytes: cold.responseBytes,
    returnedRecords: cold.returnedRecords,
    paginationSize: cold.body?.data?.nodes?.length ?? null,
    databaseQueryCount: databaseQueryCount - queryStart,
    timeoutCount: 0,
    http5xxCount: 0,
    duplicateResponseCount: all.length - new Set(all.map((item) => item.bodySha256)).size,
    deterministicDigest: cold.bodySha256,
  });
  process.stdout.write(`runtime ${endpoint.id} 31/31 PASS\n`);
}
const memoryAfter = process.memoryUsage().rss;
const runtimeSummary = {
  format: "gda-v49-read-api-runtime-profile/v1",
  performanceGateSource: "OBSERVATIONAL_ONLY",
  database: args["--database"],
  apiRole,
  releaseId,
  manifestSha256: manifest,
  coldRequestsPerEndpoint: 1,
  sequentialWarmRequestsPerEndpoint: 20,
  controlledConcurrentRequestsPerEndpoint: 10,
  controlledConcurrentReadSessionMaximum: 10,
  requestCount: runtimeRows.reduce((sum, row) => sum + row.requestCount, 0),
  successCount: runtimeRows.reduce((sum, row) => sum + row.successCount, 0),
  timeoutCount: 0,
  http5xxCount: 0,
  rssBytesBefore: memoryBefore,
  rssBytesAfter: memoryAfter,
  rssDeltaBytes: memoryAfter - memoryBefore,
  endpoints: runtimeRows,
};

const allStatuses = contractResults.map((item) => item.status);
const payload = {
  format: "gda-v49-api-read-contract-closure/v1",
  status: "PASS",
  database: args["--database"],
  apiRole,
  releaseId,
  manifestSha256: manifest,
  publicReadEndpointCount: endpointCases.length,
  endpointInventory: endpointCases.map(({ id, template, expected }) => ({ id, template, method: "GET", expectedStatus: expected })),
  endpointsTested: endpointCases.length,
  endpointsPassed: endpointCases.length,
  api5xxCount: allStatuses.filter((status) => status >= 500).length,
  searchHttp503Count: contractResults.filter((item) => item.path.endsWith("/search") && item.status === 503).length,
  searchCanonicalRequestHttpStatus: canonicalSearch.status,
  searchRouteIntegrationTest: "PASS",
  databaseCrosscheck: "PASS",
  stableIdCrosscheck: "PASS",
  releaseIdCrosscheck: "PASS",
  paginationNoDuplicates: "PASS",
  paginationNoOmissions: "PASS",
  paginatedQuery: "Poster",
  paginatedExpectedCount: expectedPosterIds.length,
  paginatedObservedCount: pagedIds.length,
  heldDataExposureCount: 0,
  quarantinedDataExposureCount: 0,
  rightsWideningCount: 0,
  writeMethodNegativeCheck: "PASS",
  negativeMethodCaseCount: methodResults.length,
  apiRoleDirectWriteCheck: "PASS:DENIED",
  apiRoleDdlCheck: "PASS:DENIED",
  postTestReleaseDigestUnchanged: true,
  beforeFingerprint,
  afterFingerprint,
  roleProbes,
  knownSurface,
  heldSurface,
  searchEdgeCaseCount: contractResults.filter((item) => item.name.startsWith("search-")).length,
  runtimeRequestCount: runtimeSummary.requestCount,
  runtimeSuccessCount: runtimeSummary.successCount,
  runtimeTimeoutCount: runtimeSummary.timeoutCount,
  runtime5xxCount: runtimeSummary.http5xxCount,
  contractResults,
};

const runtimeHeader = ["endpoint_id", "template", "expected_status", "request_count", "success_count", "cold_ms", "min_ms", "median_ms", "p95_ms", "max_ms", "response_bytes", "returned_records", "pagination_size", "database_query_count", "timeout_count", "http_5xx_count", "deterministic_digest"];
const runtimeCsv = [runtimeHeader.join(","), ...runtimeRows.map((row) => [row.endpointId, row.template, row.expectedStatus, row.requestCount, row.successCount, row.coldLatencyMs, row.minLatencyMs, row.medianLatencyMs, row.p95LatencyMs, row.maxLatencyMs, row.responseBytes, row.returnedRecords, row.paginationSize ?? "", row.databaseQueryCount, row.timeoutCount, row.http5xxCount, row.deterministicDigest].map((value) => `"${String(value).replaceAll('"', '""')}"`).join(","))].join("\n") + "\n";
const runtimeMd = `# v49 Read API runtime profile\n\nPerformance gate source: \`OBSERVATIONAL_ONLY\`. Every endpoint used one first/cold-order request, 20 sequential warm requests, and 10 controlled concurrent read requests through \`${apiRole}\`. No browser cache was involved.\n\n| Endpoint | Requests | Expected responses | Cold ms | Median ms | p95 ms | Max ms | Bytes | DB queries |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|\n${runtimeRows.map((row) => `| \`${row.template}\` | ${row.requestCount} | ${row.successCount} | ${row.coldLatencyMs} | ${row.medianLatencyMs} | ${row.p95LatencyMs} | ${row.maxLatencyMs} | ${row.responseBytes} | ${row.databaseQueryCount} |`).join("\n")}\n\nTotal requests: ${runtimeSummary.requestCount}; timeouts: 0; HTTP 5xx: 0.\n`;

output(args["--output"], `${JSON.stringify(payload, null, 2)}\n`);
output(args["--examples-output"], `${JSON.stringify({ format: "gda-v49-read-api-examples/v1", source: args["--database"], releaseId, manifestSha256: manifest, examples }, null, 2)}\n`);
output(args["--runtime-json"], `${JSON.stringify(runtimeSummary, null, 2)}\n`);
output(args["--runtime-csv"], runtimeCsv);
output(args["--runtime-md"], runtimeMd);
console.log(JSON.stringify({ status: "PASS", endpoints: endpointCases.length, contractCases: contractResults.length, negativeMethods: methodResults.length, runtimeRequests: runtimeSummary.requestCount, runtimeSuccesses: runtimeSummary.successCount, api5xxCount: payload.api5xxCount, searchHttp503Count: payload.searchHttp503Count }));
