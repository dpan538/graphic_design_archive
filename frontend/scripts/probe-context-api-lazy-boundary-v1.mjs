import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import createJiti from "jiti";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(here, "..");
const generatedRoot = join(frontendRoot, "generated/trace-context-v1");
const require = createRequire(import.meta.url);
const jiti = createJiti(import.meta.url, {
  alias: {
    "@": join(frontendRoot, "src"),
    "server-only": join(here, "server-only-stub.mjs"),
  },
});

const manifest = JSON.parse(await readFile(join(generatedRoot, "manifest.json"), "utf8"));
const recordsText = await readFile(join(generatedRoot, "records.json"), "utf8");
const publicId = recordsText.match(/"surfaceId":"(SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*)"/u)?.[1];
assert(publicId, "Context lazy-boundary probe could not identify a public record");

function loadedContextRuntimeModules() {
  return Object.keys(require.cache).filter((path) =>
    path.includes("/context/governed/reader.server")
    || path.includes("/context/governed/read-api-runtime.server")
    || path.includes("/generated/trace-context-v1/"));
}

function pathSegments(url) {
  return new URL(url).pathname.replace(/^\/api\/v1\/?/u, "").split("/").filter(Boolean);
}

const controller = await jiti.import(
  join(frontendRoot, "src/lib/read-platform/server/read-api-controller.ts"),
);
assert.equal(
  loadedContextRuntimeModules().length,
  0,
  "importing the generic API controller eagerly initialized Context",
);

let providerOpenCalls = 0;
const provider = Object.freeze({
  async open() {
    providerOpenCalls += 1;
    return Object.freeze({
      ok: false,
      error: Object.freeze({
        code: "RELEASE_NOT_FOUND",
        message: "probe repository intentionally unavailable",
        retryable: false,
      }),
    });
  },
});

const unrelatedUrl = "https://archive.invalid/api/v1/releases/current/manifest";
const unrelated = await controller.dispatchReadApiRequest(
  new Request(unrelatedUrl),
  pathSegments(unrelatedUrl),
  provider,
);
assert.equal(unrelated.status, 404);
assert.equal(providerOpenCalls, 1);
const unrelatedContextLoads = loadedContextRuntimeModules().length;
assert.equal(unrelatedContextLoads, 0, "an unrelated API resource initialized Context");

const contextUrl = `https://archive.invalid/api/v1/releases/${manifest.sourceRelease.id}/trace/objects/${publicId}/context`;
const context = await controller.dispatchReadApiRequest(
  new Request(contextUrl, {
    headers: {
      "Archive-Research-Manifest-Sha256": manifest.sourceRelease.manifestSha256,
    },
  }),
  pathSegments(contextUrl),
  provider,
);
assert.equal(context.status, 200);
assert.equal(providerOpenCalls, 1, "Context request opened the generic provider");

console.log([
  "CONTEXT_API_LAZY_BOUNDARY=PASS",
  `UNRELATED_CONTEXT_MODULE_LOAD_COUNT=${unrelatedContextLoads}`,
  "CONTEXT_GENERIC_PROVIDER_OPEN_COUNT=0",
  "UNRELATED_GENERIC_PROVIDER_OPEN_COUNT=1",
].join(" "));
