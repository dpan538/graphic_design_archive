#!/usr/bin/env node
import { createRequire } from "node:module";
import { resolve } from "node:path";
import assert from "node:assert/strict";

const frontendRoot = resolve(import.meta.dirname, "..");
const frontendRequire = createRequire(`${frontendRoot}/package.json`);
const jiti = frontendRequire("jiti")(import.meta.url, {
  interopDefault: true,
  alias: { "@": `${frontendRoot}/src`, "server-only": `${frontendRoot}/scripts/server-only-marker.mjs` },
});
const paginationPath = `${frontendRoot}/src/lib/read-platform/pagination.ts`;
const productionImportPath = `${frontendRoot}/src/lib/read-platform/server/postgres-repository.ts`;
const pagination = jiti(paginationPath);
const repository = jiti(productionImportPath);

assert.equal(typeof pagination.pageByKey, "function", "pageByKey must be a named runtime function");
assert.equal(typeof repository.PostgresArchiveRepository, "function", "production search adapter import must resolve");

const version = {
  research: { apiVersion: "v1", researchReleaseId: "module-contract-release", researchManifestSha256: "a".repeat(64), schemaVersion: "archive-research-release/v1" },
  visual: null, visualState: "UNAVAILABLE", visualReasonCodes: ["NOT_SELECTED"], takedownOverlaySha256: null,
};
const values = [{ key: "alpha" }, { key: "beta" }, { key: "gamma" }];
const first = pagination.pageByKey(values, (value) => value.key, version, { first: 1 }, "module-contract", "all", "key");
assert(first.ok && first.data.nodes[0]?.key === "alpha" && first.data.pageInfo.nextCursor, "known first key lookup failed");
const second = pagination.pageByKey(values, (value) => value.key, version, { first: 1, after: first.data.pageInfo.nextCursor }, "module-contract", "all", "key");
assert(second.ok && second.data.nodes[0]?.key === "beta", "known cursor key lookup failed");
const unknownCursor = pagination.encodeCursor(version, "module-contract", "all", "key", "not-present");
const unknown = pagination.pageByKey(values, (value) => value.key, version, { first: 1, after: unknownCursor }, "module-contract", "all", "key");
assert(!unknown.ok && unknown.error.code === "INVALID_CURSOR", "unknown key must fail closed as INVALID_CURSOR");

console.log(JSON.stringify({
  status: "PASS",
  pageByKeyRuntimeType: typeof pagination.pageByKey,
  definitionFile: paginationPath,
  productionImportFile: productionImportPath,
  knownKey: "PASS",
  unknownKey: "PASS:INVALID_CURSOR",
}));
