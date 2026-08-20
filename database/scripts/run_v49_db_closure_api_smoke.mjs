#!/usr/bin/env node
// Minimal server-side Read API smoke against one fresh, verified sealed release.
// This does not start a browser, render a page, or load any client component.

import { createRequire } from "node:module";
import { spawnSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { resolve } from "node:path";

function argumentsOf(argv) {
  const result = {};
  for (let index = 2; index < argv.length; index += 2) result[argv[index]] = argv[index + 1];
  return result;
}
const args = argumentsOf(process.argv);
for (const key of ["--psql", "--host", "--port", "--database", "--repo", "--output"]) {
  if (!args[key]) throw new Error(`missing ${key}`);
}
if (!args["--host"].startsWith("/") || args["--port"] === "5432" || !args["--database"].startsWith("gda_v49_phase2a_")) {
  throw new Error("isolated database boundary rejected");
}

const repo = resolve(args["--repo"]);
const frontendRequire = createRequire(`${repo}/frontend/package.json`);
const jiti = frontendRequire("jiti")(`${repo}/database/scripts/run_v49_db_closure_api_smoke.mjs`, {
  interopDefault: true,
  alias: { "@": `${repo}/frontend/src` },
});
const { PostgresArchiveRepositoryProvider } = jiti(`${repo}/frontend/src/lib/read-platform/server/postgres-repository.ts`);
const { dispatchReadApiRequest } = jiti(`${repo}/frontend/src/app/api/v1/[...path]/route.ts`);

const dbEnv = {
  ...process.env,
  PGHOST: args["--host"],
  PGPORT: args["--port"],
  PGDATABASE: args["--database"],
  PGUSER: "gda_v49_phase2a_api_reader",
};
function sqlLiteral(value, index, variables) {
  if (value === null || value === undefined) return "NULL";
  if (typeof value === "number") return String(value);
  if (typeof value === "boolean") return value ? "TRUE" : "FALSE";
  const name = `gda_value_${index}`;
  variables.push("-v", `${name}=${String(value)}`);
  return `:'${name}'`;
}
class PsqlReader {
  async query(sql, values, signal) {
    if (signal?.aborted) throw new DOMException("request aborted", "AbortError");
    const variables = [];
    const parameters = values.map((value, index) => sqlLiteral(value, index + 1, variables));
    const execute = parameters.length ? `EXECUTE gda_read(${parameters.join(",")})` : "EXECUTE gda_read";
    const wrapped = `PREPARE gda_read AS SELECT coalesce(jsonb_agg(to_jsonb(gda_rows)), '[]'::jsonb) FROM (${sql}) gda_rows; ${execute};`;
    const result = spawnSync(args["--psql"], ["-X", "-Atq", "-v", "ON_ERROR_STOP=1", ...variables, "-c", wrapped], {
      env: dbEnv, encoding: "utf8", timeout: 30000,
    });
    if (result.status !== 0) throw new Error(`read query failed: ${result.stderr.trim()}`);
    const lines = result.stdout.split("\n").filter((line) => line.startsWith("[") || line === "[]");
    if (!lines.length) throw new Error("read query returned no JSON envelope");
    return { rows: JSON.parse(lines.at(-1)) };
  }
}

const reader = new PsqlReader();
const exactProvider = new PostgresArchiveRepositoryProvider(reader);
// The route's provider seam resolves the existing current-version view to the
// existing exact-pair PostgreSQL provider.  No alternate data source is used.
const provider = {
  async open(input, options) {
    if (!("alias" in input.research)) return exactProvider.open(input, options);
    const current = await reader.query(
      "SELECT research_release_id, research_manifest_sha256 FROM api_v1.current_version_status WHERE channel = $1",
      ["public"], options?.signal,
    );
    const row = current.rows[0];
    if (!row?.research_release_id || !row?.research_manifest_sha256) {
      return { ok: false, error: { code: "UNAVAILABLE", message: "current release is unavailable", retryable: false } };
    }
    return exactProvider.open({ research: {
      researchReleaseId: row.research_release_id,
      researchManifestSha256: row.research_manifest_sha256,
    } }, options);
  },
};

function pathSegments(url) {
  return new URL(url).pathname.replace(/^\/api\/v1\/?/, "").split("/").filter(Boolean);
}
async function invoke(name, url, init = {}) {
  const request = new Request(url, init);
  const response = await dispatchReadApiRequest(request, pathSegments(url), provider);
  const text = await response.text();
  const body = text ? JSON.parse(text) : null;
  const item = {
    name, method: request.method, path: new URL(url).pathname,
    status: response.status, contentType: response.headers.get("content-type"),
    allow: response.headers.get("allow"), body,
  };
  results.push(item);
  return item;
}
function assert(condition, message) { if (!condition) throw new Error(message); }
function stable(value) { return JSON.stringify(value); }
function assertNoLeak(item) {
  const value = stable(item.body);
  for (const token of ["raw.", "core.", "provenance.", "research.", "rights.", "release."]) {
    assert(!value.includes(token), `${item.name} leaked internal schema token ${token}`);
  }
}

const results = [];
const descriptorRows = await reader.query(
  "SELECT research_release_id, research_manifest_sha256, object_count FROM api_v1.sealed_research_release_descriptor ORDER BY sealed_at DESC LIMIT 1", [],
);
assert(descriptorRows.rows.length === 1, "one sealed descriptor required");
const descriptor = descriptorRows.rows[0];
const releaseId = descriptor.research_release_id;
const manifest = descriptor.research_manifest_sha256;
const exactBase = `http://api-smoke.local/api/v1/releases/${encodeURIComponent(releaseId)}`;
const exactHeaders = { "Archive-Research-Manifest-Sha256": manifest };

const currentManifest = await invoke("current-release-metadata", "http://api-smoke.local/api/v1/releases/current/manifest");
assert(currentManifest.status === 200 && currentManifest.body.researchReleaseId === releaseId, "current metadata mismatch");
const exactManifest = await invoke("exact-release-metadata", `${exactBase}/manifest`, { headers: exactHeaders });
assert(exactManifest.status === 200 && exactManifest.body.researchManifestSha256 === manifest, "exact metadata mismatch");
const overview = await invoke("archive-overview", `${exactBase}/archive/overview`, { headers: exactHeaders });
assert(overview.status === 200 && overview.body.data.objectCount === 32 && overview.body.data.traceEligibleObjectCount === 0, "overview count mismatch");

const surfaceRows = await reader.query(
  "SELECT surface_id FROM api_v1.sealed_surface WHERE research_release_id=$1 AND research_manifest_sha256=$2 ORDER BY surface_id LIMIT 1",
  [releaseId, manifest],
);
const surfaceId = surfaceRows.rows[0].surface_id;
const surface = await invoke("surface-detail", `${exactBase}/surfaces/${encodeURIComponent(surfaceId)}`, { headers: exactHeaders });
assert(surface.status === 200 && surface.body.data.surfaceId === surfaceId && surface.body.data.deliveryState === "CITATION_ONLY", "surface detail mismatch");
const missingSurface = await invoke("surface-not-found", `${exactBase}/surfaces/not-present`, { headers: exactHeaders });
assert(missingSurface.status === 404, "missing surface must be 404");

const searchOne = await invoke("filtered-page-1", `${exactBase}/search?q=Phase%202S&first=5`, { headers: exactHeaders });
assert(searchOne.status === 200 && searchOne.body.data.nodes.length === 5 && searchOne.body.data.pageInfo.hasNextPage, "search page one mismatch");
const idsOne = searchOne.body.data.nodes.map((node) => node.surface.surfaceId);
assert(stable(idsOne) === stable([...idsOne].sort()), "search ordering is not deterministic");
const cursor = searchOne.body.data.pageInfo.nextCursor;
const searchTwo = await invoke("filtered-page-2", `${exactBase}/search?q=Phase%202S&first=5&after=${encodeURIComponent(cursor)}`, { headers: exactHeaders });
assert(searchTwo.status === 200 && searchTwo.body.data.nodes.length === 5, "search page two mismatch");
const idsTwo = searchTwo.body.data.nodes.map((node) => node.surface.surfaceId);
assert(idsOne.every((id) => !idsTwo.includes(id)), "search pages overlap");
const searchRepeat = await invoke("deterministic-search-repeat", `${exactBase}/search?q=Phase%202S&first=5`, { headers: exactHeaders });
assert(stable(searchOne.body) === stable(searchRepeat.body), "search repeat drift");
const emptySearch = await invoke("empty-search-result", `${exactBase}/search?q=does-not-exist&first=5`, { headers: exactHeaders });
assert(emptySearch.status === 200 && emptySearch.body.data.nodes.length === 0, "empty search mismatch");

const folderTypes = await invoke("folder-types-empty", `${exactBase}/folder-types`, { headers: exactHeaders });
assert(folderTypes.status === 200 && folderTypes.body.data.length === 0, "folder type fail-closed mismatch");
const folders = await invoke("folders-filtered-empty", `${exactBase}/folders?type=region&first=5`, { headers: exactHeaders });
assert(folders.status === 200 && folders.body.data.nodes.length === 0, "folder projection fail-closed mismatch");
const missingFolder = await invoke("folder-not-found", `${exactBase}/folders/not-present`, { headers: exactHeaders });
assert(missingFolder.status === 404, "missing folder must be 404");
const traceAtlas = await invoke("trace-atlas-empty", `${exactBase}/trace/atlas`, { headers: exactHeaders });
assert(traceAtlas.status === 200 && traceAtlas.body.data.totalExact === 0, "TRACE availability mismatch");
const traceObjects = await invoke("trace-objects-empty", `${exactBase}/trace/objects?first=5`, { headers: exactHeaders });
assert(traceObjects.status === 200 && traceObjects.body.data.nodes.length === 0, "TRACE objects mismatch");
const relationTypes = await invoke("relation-types-empty", `${exactBase}/trace/relation-types`, { headers: exactHeaders });
assert(relationTypes.status === 200 && relationTypes.body.data.length === 0, "relation registry must fail closed empty");
const unknown = await invoke("unknown-resource", `${exactBase}/unknown`, { headers: exactHeaders });
assert(unknown.status === 404, "unknown endpoint must be 404");
const head = await invoke("head-read", `${exactBase}/archive/overview`, { method: "HEAD", headers: exactHeaders });
assert(head.status === 200 && head.body === null, "HEAD contract mismatch");
const options = await invoke("options-read", `${exactBase}/archive/overview`, { method: "OPTIONS", headers: exactHeaders });
assert(options.status === 204 && options.allow === "GET, HEAD, OPTIONS", "OPTIONS contract mismatch");
for (const method of ["POST", "PUT", "PATCH", "DELETE"]) {
  const denied = await invoke(`${method.toLowerCase()}-denied`, `${exactBase}/archive/overview`, { method, headers: exactHeaders });
  assert(denied.status === 405, `${method} must be denied`);
}
for (const item of results) {
  if (item.body !== null) assert(item.contentType?.startsWith("application/json"), `${item.name} content type mismatch`);
  assertNoLeak(item);
}

function deniedSql(sql) {
  const probe = spawnSync(args["--psql"], ["-X", "-q", "-v", "ON_ERROR_STOP=1", "-c", sql], {
    env: dbEnv, encoding: "utf8", timeout: 30000,
  });
  return { exitCode: probe.status, denied: probe.status !== 0, stderr: probe.stderr.trim().split("\n").at(-1) ?? "" };
}
const roleProbes = {
  coreWrite: deniedSql("BEGIN; DELETE FROM core.archive_object WHERE false; ROLLBACK;"),
  researchWrite: deniedSql("BEGIN; DELETE FROM research.corpus_membership WHERE false; ROLLBACK;"),
  releaseWrite: deniedSql("BEGIN; DELETE FROM release.research_release_object WHERE false; ROLLBACK;"),
  rawSelect: deniedSql("SELECT 1 FROM raw.source_record LIMIT 1;"),
};
assert(Object.values(roleProbes).every((probe) => probe.denied), "API role privilege boundary failed");

const payload = {
  format: "gda-v49-db-closure-api-read-smoke/v1",
  status: "PASS",
  database: args["--database"],
  apiReadRole: "gda_v49_phase2a_api_reader",
  releaseId, manifestSha256: manifest,
  endpointsTested: results.length,
  writeMethodNegativeCheck: "PASS",
  directRoleBoundary: "PASS",
  frontendFilesChanged: 0,
  browserMatrixRun: false,
  visualRegressionRun: false,
  accessibilityMatrixRun: false,
  roleProbes,
  results,
};
writeFileSync(resolve(args["--output"]), `${JSON.stringify(payload, null, 2)}\n`);
console.log(JSON.stringify({ status: payload.status, endpointsTested: payload.endpointsTested, apiReadRole: payload.apiReadRole }));
