#!/usr/bin/env node
import { createRequire } from "node:module";
import { spawnSync } from "node:child_process";
import { resolve } from "node:path";
import { writeFileSync } from "node:fs";

const args = Object.fromEntries(process.argv.slice(2).reduce((pairs, value, index, all) => {
  if (index % 2 === 0) pairs.push([value, all[index + 1]]);
  return pairs;
}, []));
for (const name of ["--repo", "--psql", "--host", "--port", "--database", "--output"]) {
  if (!args[name]) throw new Error(`missing ${name}`);
}

const repo = resolve(args["--repo"]);
const marker = resolve(repo, "docs/audits/v49-api-read-contract-closure/raw/api/server-only-marker.js");
const frontendRequire = createRequire(`${repo}/frontend/package.json`);
const jiti = frontendRequire("jiti")(import.meta.url, {
  interopDefault: true,
  alias: { "@": `${repo}/frontend/src`, "server-only": marker },
});
const paginationFile = `${repo}/frontend/src/lib/read-platform/pagination.ts`;
const repositoryFile = `${repo}/frontend/src/lib/read-platform/server/postgres-repository.ts`;
const routeFile = `${repo}/frontend/src/app/api/v1/[...path]/route.ts`;
const pagination = jiti(paginationFile);
const { PostgresArchiveRepositoryProvider } = jiti(repositoryFile);
const { dispatchReadApiRequest } = jiti(routeFile);

const dbEnv = {
  ...process.env,
  PGHOST: args["--host"],
  PGPORT: args["--port"],
  PGDATABASE: args["--database"],
  PGUSER: "gda_v49_phase2a_api_reader",
};
function literal(value, index, variables) {
  if (typeof value === "number") return String(value);
  const name = `gda_value_${index}`;
  variables.push("-v", `${name}=${String(value)}`);
  return `:'${name}'`;
}
class PsqlReader {
  async query(sql, values) {
    const variables = [];
    const parameters = values.map((value, index) => literal(value, index + 1, variables));
    const execute = parameters.length ? `EXECUTE gda_read(${parameters.join(",")})` : "EXECUTE gda_read";
    const input = `PREPARE gda_read AS SELECT coalesce(jsonb_agg(to_jsonb(gda_rows)), '[]'::jsonb) FROM (${sql}) gda_rows; ${execute};\n`;
    const result = spawnSync(args["--psql"], ["-X", "-Atq", "-v", "ON_ERROR_STOP=1", ...variables, "-f", "-"], {
      env: dbEnv,
      encoding: "utf8",
      input,
      timeout: 30000,
    });
    if (result.status !== 0) throw new Error(`read query failed: ${result.stderr.trim()}`);
    const line = result.stdout.split("\n").filter((item) => item.startsWith("[") || item === "[]").at(-1);
    if (!line) throw new Error("read query returned no JSON envelope");
    return { rows: JSON.parse(line) };
  }
}

const reader = new PsqlReader();
const descriptors = await reader.query(
  "SELECT research_release_id, research_manifest_sha256 FROM api_v1.sealed_research_release_descriptor ORDER BY sealed_at DESC LIMIT 1",
  [],
);
const descriptor = descriptors.rows[0];
if (!descriptor) throw new Error("sealed release required");
const exactProvider = new PostgresArchiveRepositoryProvider(reader);
const opened = await exactProvider.open({ research: {
  researchReleaseId: descriptor.research_release_id,
  researchManifestSha256: descriptor.research_manifest_sha256,
} });
if (!opened.ok) throw new Error(opened.error.message);

let directStack = null;
try {
  await opened.data.search({ q: "Phase 2S", first: 5 });
} catch (error) {
  directStack = error instanceof Error ? error.stack ?? error.message : String(error);
}
if (!directStack) throw new Error("expected direct pageByKey failure was not reproduced");

const provider = {
  async open(input, options) {
    if (!("alias" in input.research)) return exactProvider.open(input, options);
    return exactProvider.open({ research: {
      researchReleaseId: descriptor.research_release_id,
      researchManifestSha256: descriptor.research_manifest_sha256,
    } }, options);
  },
};
const requestUrl = `http://api-contract.local/api/v1/releases/${encodeURIComponent(descriptor.research_release_id)}/search?q=Phase%202S&first=5`;
const request = new Request(requestUrl, { headers: {
  "Archive-Research-Manifest-Sha256": descriptor.research_manifest_sha256,
} });
const response = await dispatchReadApiRequest(request, ["releases", descriptor.research_release_id, "search"], provider);
const responseBody = await response.json();
const firstApplicationFrame = directStack.split("\n").find((line) => line.includes("/frontend/src/"))?.trim() ?? null;
const payload = {
  format: "gda-v49-page-by-key-reproduction/v1",
  status: response.status === 503 && typeof pagination.pageByKey === "undefined" ? "PASS" : "FAIL",
  startupCommand: process.argv.join(" "),
  runtimeMode: "node-jiti-server-route-dispatch",
  nodeVersion: process.version,
  request: { method: "GET", url: requestUrl, query: { q: "Phase 2S", first: 5 } },
  response: {
    status: response.status,
    headers: Object.fromEntries(response.headers.entries()),
    body: responseBody,
  },
  moduleResolution: { paginationFile, repositoryFile, routeFile, serverOnlyAlias: marker },
  pageByKey: {
    definitionFile: paginationFile,
    importFile: repositoryFile,
    exportForm: "ABSENT_NAMED_EXPORT",
    importForm: "NAMED_IMPORT",
    runtimeType: typeof pagination.pageByKey,
    expectedType: "function",
    availableExports: Object.keys(pagination).sort(),
    keysetPageRuntimeType: typeof pagination.keysetPage,
  },
  directError: { stack: directStack, firstApplicationFrame },
};
writeFileSync(resolve(args["--output"]), `${JSON.stringify(payload, null, 2)}\n`);
console.error(directStack);
console.log(JSON.stringify({ status: payload.status, httpStatus: response.status, pageByKeyType: typeof pagination.pageByKey }));
if (payload.status !== "PASS") process.exit(1);
