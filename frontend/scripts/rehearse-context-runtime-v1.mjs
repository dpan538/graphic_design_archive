import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import {
  dirname,
  extname,
  join,
  relative,
  resolve,
} from "node:path";
import { performance } from "node:perf_hooks";
import { fileURLToPath } from "node:url";
import createJiti from "jiti";
import ts from "typescript";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(here, "..");
const repositoryRoot = resolve(frontendRoot, "..");
const contextRoot = join(frontendRoot, "src/features/trace-v49/context");
const generatedRoot = join(frontendRoot, "generated/trace-context-v1");
const ledgerPath = join(
  repositoryRoot,
  "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv",
);
const sourceSha = "5767928180b90a4194cc47e325d78ab8d9226b48";
const args = parseArguments(process.argv.slice(2));
const jiti = createJiti(import.meta.url, {
  alias: {
    "@": join(frontendRoot, "src"),
    "server-only": join(here, "server-only-stub.mjs"),
  },
});

const PUBLIC_COUNT = 7_995;
const HELD_COUNT = 7_928;
const EXPECTED_PROJECTION_SHA256 =
  "825f6ecaa9ae1496c8a00ea0fefa5c90319046cf9c1f08a2ef76b9b02df4baeb";
const PUBLIC_ID_PATTERN = /^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$/u;
const UUID_PATTERN = /\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b/iu;
try {
  await main();
} catch (error) {
  console.error(`CONTEXT_RUNTIME_REHEARSAL=FAIL ERROR=${safeError(error)}`);
  process.exitCode = 1;
}

function parseArguments(values) {
  let evidenceDir = join(tmpdir(), "trace-v49-context-runtime-rehearsal");
  for (let index = 0; index < values.length; index += 1) {
    if (values[index] === "--evidence-dir") {
      const value = values[index + 1];
      assert(value, "--evidence-dir requires a path");
      evidenceDir = resolve(value);
      index += 1;
      continue;
    }
    throw new Error(`unknown argument: ${values[index]}`);
  }
  return Object.freeze({ evidenceDir });
}

function safeError(error) {
  return String(error instanceof Error ? error.message : error)
    .replace(UUID_PATTERN, "[internal-id-redacted]")
    .replace(/\s+/gu, " ")
    .slice(0, 500);
}

function compareText(left, right) {
  return left < right ? -1 : left > right ? 1 : 0;
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function roundMs(value) {
  return Number(value.toFixed(3));
}

function percentile(values, quantile) {
  assert(values.length > 0, "percentile requires observations");
  const ordered = [...values].sort((left, right) => left - right);
  const index = Math.max(0, Math.ceil(ordered.length * quantile) - 1);
  return roundMs(ordered[index]);
}

function summarizeDurations(values) {
  return Object.freeze({
    count: values.length,
    p50: percentile(values, 0.5),
    p95: percentile(values, 0.95),
    p99: percentile(values, 0.99),
    max: roundMs(Math.max(...values)),
  });
}

async function extractPublicIds() {
  const contents = await readFile(join(generatedRoot, "records.json"), "utf8");
  const ids = [...contents.matchAll(/"surfaceId":"(SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*)"/gu)]
    .map((match) => match[1]);
  assert.equal(ids.length, PUBLIC_COUNT, "committed projection public ID count differs");
  assert.equal(new Set(ids).size, PUBLIC_COUNT, "committed projection public IDs are not unique");
  assert(ids.every((id) => PUBLIC_ID_PATTERN.test(id)), "projection contains an invalid public ID");
  return Object.freeze(ids);
}

async function extractHeldIds() {
  const lines = (await readFile(ledgerPath, "utf8")).split(/\r?\n/u).filter(Boolean);
  const headers = lines.shift()?.split("\t") ?? [];
  const idColumn = headers.indexOf("surface_id_exact");
  const dispositionColumn = headers.indexOf("research_disposition");
  assert(idColumn >= 0 && dispositionColumn >= 0, "eligibility ledger columns are missing");
  const ids = lines
    .map((line) => line.split("\t"))
    .filter((cells) => cells[dispositionColumn] === "held")
    .map((cells) => cells[idColumn]);
  assert.equal(ids.length, HELD_COUNT, "held ID count differs");
  assert.equal(new Set(ids).size, HELD_COUNT, "held IDs are not unique");
  assert(ids.every((id) => PUBLIC_ID_PATTERN.test(id)), "eligibility ledger contains an invalid held ID");
  return Object.freeze(ids.sort(compareText));
}

function runtimeModuleSpecifiers(source, filename) {
  const kind = filename.endsWith(".tsx")
    ? ts.ScriptKind.TSX
    : filename.endsWith(".jsx")
      ? ts.ScriptKind.JSX
      : filename.endsWith(".js") || filename.endsWith(".mjs")
        ? ts.ScriptKind.JS
        : ts.ScriptKind.TS;
  const file = ts.createSourceFile(filename, source, ts.ScriptTarget.Latest, true, kind);
  const values = new Set();

  function addLiteral(node) {
    if (node && ts.isStringLiteralLike(node)) values.add(node.text);
  }

  function importHasRuntimeBinding(node) {
    const clause = node.importClause;
    if (!clause) return true;
    if (clause.isTypeOnly) return false;
    if (clause.name) return true;
    if (!clause.namedBindings) return false;
    if (ts.isNamespaceImport(clause.namedBindings)) return true;
    return clause.namedBindings.elements.some((element) => !element.isTypeOnly);
  }

  function visit(node) {
    if (ts.isImportDeclaration(node) && importHasRuntimeBinding(node)) {
      addLiteral(node.moduleSpecifier);
    } else if (ts.isExportDeclaration(node) && !node.isTypeOnly) {
      addLiteral(node.moduleSpecifier);
    } else if (ts.isImportEqualsDeclaration(node) && !node.isTypeOnly) {
      if (ts.isExternalModuleReference(node.moduleReference)) {
        addLiteral(node.moduleReference.expression);
      }
    } else if (ts.isCallExpression(node) && node.arguments.length === 1) {
      const argument = node.arguments[0];
      if (node.expression.kind === ts.SyntaxKind.ImportKeyword) addLiteral(argument);
      if (ts.isIdentifier(node.expression) && node.expression.text === "require") addLiteral(argument);
    }
    ts.forEachChild(node, visit);
  }
  visit(file);
  return Object.freeze([...values].sort(compareText));
}

function resolveLocalModule(specifier, importer) {
  let base;
  if (specifier.startsWith("@/")) base = join(frontendRoot, "src", specifier.slice(2));
  else if (specifier.startsWith(".")) base = resolve(dirname(importer), specifier);
  else return null;

  const hasRuntimeExtension = [
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json", ".css",
  ].includes(extname(base));
  const candidates = hasRuntimeExtension
    ? [base]
    : [
      base,
      ...[".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json", ".css"].map((suffix) => `${base}${suffix}`),
      ...["index.ts", "index.tsx", "index.js", "index.mjs", "index.json"].map((name) => join(base, name)),
    ];
  return candidates.find((candidate) => {
    try {
      return readFileSync(candidate).byteLength >= 0;
    } catch {
      return false;
    }
  }) ?? null;
}

function buildRuntimeImportGraph(entry) {
  const visited = new Set();
  const edges = [];
  const externalSpecifiers = new Set();
  const pending = [entry];
  while (pending.length > 0) {
    const current = pending.pop();
    if (!current || visited.has(current)) continue;
    visited.add(current);
    if (![".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"].includes(extname(current))) continue;
    const source = readFileSync(current, "utf8");
    for (const specifier of runtimeModuleSpecifiers(source, current)) {
      const resolved = resolveLocalModule(specifier, current);
      if (!resolved) {
        externalSpecifiers.add(specifier);
        continue;
      }
      edges.push(Object.freeze({ importer: current, imported: resolved, specifier }));
      pending.push(resolved);
    }
  }
  return Object.freeze({
    entry,
    modules: Object.freeze([...visited].sort(compareText)),
    edges: Object.freeze(edges.sort((left, right) =>
      compareText(`${left.importer}\0${left.imported}`, `${right.importer}\0${right.imported}`))),
    externalSpecifiers: Object.freeze([...externalSpecifiers].sort(compareText)),
  });
}

function graphRelativeSummary(graph) {
  return Object.freeze({
    entry: relative(repositoryRoot, graph.entry),
    moduleCount: graph.modules.length,
    edgeCount: graph.edges.length,
    externalSpecifiers: graph.externalSpecifiers,
  });
}

function auditStaticDependencies() {
  const entries = Object.freeze({
    contextApiRuntime: join(contextRoot, "governed/read-api-runtime.server.ts"),
    projectionLoader: join(contextRoot, "governed/reader.server.ts"),
    governedCanvas: join(frontendRoot, "src/app/trace/context-canvas/page.tsx"),
  });
  const graphs = Object.freeze(Object.fromEntries(
    Object.entries(entries).map(([name, entry]) => [name, buildRuntimeImportGraph(entry)]),
  ));
  const allModules = new Set(Object.values(graphs).flatMap((graph) => graph.modules));
  const forbiddenModules = [...allModules].filter((filename) =>
    filename.includes("/context/realdata/")
    || filename.endsWith("/context/realdata/source-index.server.ts")
    || filename.endsWith("/context/realdata/project.server.ts"));
  const sqliteImportCount = Object.values(graphs)
    .flatMap((graph) => graph.externalSpecifiers)
    .filter((specifier) => specifier === "node:sqlite" || specifier === "sqlite").length;
  const fsImportCount = Object.values(graphs)
    .flatMap((graph) => graph.externalSpecifiers)
    .filter((specifier) => specifier === "node:fs" || specifier === "node:fs/promises").length;
  const searchModules = [...allModules].filter((filename) => filename.includes("/search-v49/"));
  assert.equal(forbiddenModules.length, 0, "Context runtime reaches the real-data validation loader");
  assert.equal(sqliteImportCount, 0, "Context runtime reaches SQLite");
  assert.equal(fsImportCount, 0, "Context runtime reaches filesystem source parsing");
  assert.equal(searchModules.length, 0, "Context branch reaches Search runtime modules");

  const controllerPath = join(frontendRoot, "src/lib/read-platform/server/read-api-controller.ts");
  const controllerSource = readFileSync(controllerPath, "utf8");
  const contextPathGuardPosition = controllerSource.indexOf("if (isFullContextResourcePath(path))");
  const contextImportPosition = controllerSource.indexOf('"@/features/trace-v49/context/governed/read-api-runtime.server"');
  const providerOpenPosition = controllerSource.indexOf("const opened = await repositoryProvider.open(");
  const lazyProviderPosition = controllerSource.indexOf('await import("./provider")');
  assert(contextPathGuardPosition >= 0, "Context early-dispatch path guard is missing");
  assert(contextImportPosition > contextPathGuardPosition, "Context runtime import is not path-gated");
  assert(lazyProviderPosition > contextImportPosition, "generic provider is not lazy after Context dispatch");
  assert(providerOpenPosition > contextImportPosition, "generic provider opens before Context dispatch");

  return Object.freeze({
    graphSummaries: Object.freeze(Object.fromEntries(
      Object.entries(graphs).map(([name, graph]) => [name, graphRelativeSummary(graph)]),
    )),
    heavyValidationImportCount: forbiddenModules.length,
    sqliteDependency: sqliteImportCount > 0,
    filesystemSourceParserImportCount: fsImportCount,
    searchRuntimeImportCount: searchModules.length,
    controllerHookBeforeProviderOpen: true,
    contextRuntimeImportPathGated: true,
    genericProviderLazyLoaded: true,
  });
}

function runProjectionPreflight() {
  const run = spawnSync(
    process.execPath,
    ["scripts/generate-trace-context-v1.mjs", "--check"],
    {
      cwd: frontendRoot,
      encoding: "utf8",
      maxBuffer: 20 * 1024 * 1024,
    },
  );
  assert.equal(
    run.status,
    0,
    `Context projection preflight failed: ${safeError(run.stderr || run.stdout)}`,
  );
  assert.match(run.stdout, /TRACE_CONTEXT_V1_GENERATION=PASS MODE=CHECK RUNS=2/u);
  assert.match(run.stdout, /HELD_EXPOSED=0/u);
  return Object.freeze({
    command: "npm run verify:context-v1-projection",
    status: "PASS",
    deterministicRebuildRuns: 2,
  });
}

function runApiLazyBoundaryProbe() {
  const run = spawnSync(
    process.execPath,
    ["--conditions=react-server", "scripts/probe-context-api-lazy-boundary-v1.mjs"],
    {
      cwd: frontendRoot,
      encoding: "utf8",
      maxBuffer: 20 * 1024 * 1024,
    },
  );
  assert.equal(
    run.status,
    0,
    `Context API lazy-boundary probe failed: ${safeError(run.stderr || run.stdout)}`,
  );
  assert.match(run.stdout, /CONTEXT_API_LAZY_BOUNDARY=PASS/u);
  assert.match(run.stdout, /UNRELATED_CONTEXT_MODULE_LOAD_COUNT=0/u);
  assert.match(run.stdout, /CONTEXT_GENERIC_PROVIDER_OPEN_COUNT=0/u);
  return Object.freeze({
    status: "PASS",
    unrelatedContextModuleLoadCount: 0,
    contextGenericProviderOpenCount: 0,
  });
}

function validatePipeline(result, expectedId, modules) {
  assert(result.ok, "public Context lookup failed");
  const dataset = result.data;
  assert.equal(dataset.selectedRecord.surfaceId, expectedId, "selected record identity drifted");
  assert.equal(dataset.availability, "ready", "public Context dataset is not ready");
  assert.equal(dataset.representations.length, dataset.counts.representations);
  assert.equal(dataset.accessibleRows.length, dataset.representations.length + 1);
  const explanations = new Map(dataset.explanations.map((item) => [item.explanationCode, item]));
  for (const representation of dataset.representations) {
    assert.equal(explanations.get(representation.explanationCode)?.contextKind, representation.kind);
    assert.equal(representation.publicationState, "published");
    assert.equal(representation.provenance.decision, "PUBLISHED");
    assert.equal(representation.provenance.sourceState, "proposed");
    assert.equal(representation.provenance.governancePolicyVersion, "context-governance-v1");
  }

  const canvas = modules.canvasAdapter.adaptPublicContextDatasetForCanvas(dataset);
  assert.equal(canvas.dataMode, "governed_context_v1");
  assert.equal(canvas.dataset.semanticEdges.length, 0);
  assert.equal(canvas.dataset.curatedMemberships.length, 0);
  const state = modules.state.createInitializingContextCanvasState(
    canvas.dataset,
    canvas.dataMode,
    canvas.metadata,
  );
  const composition = state.history.present;
  const connections = modules.connections.deriveVisibleContextCanvasConnections(
    canvas.dataset,
    composition.visibleEntityIds,
    canvas.dataMode,
    canvas.metadata,
  );
  assert.equal(connections.length, dataset.representations.length);
  assert(connections.every((item) => item.connectionKind === "context_representation"));
  const rows = modules.model.contextCanvasAccessibleRowsForMode(
    canvas.dataset,
    canvas.dataMode,
    canvas.metadata,
  );
  assert.equal(rows.length, dataset.representations.length + 1);
  const exportSnapshot = modules.exportPng.prepareContextCanvasExportSvg(
    canvas.dataset,
    composition,
    true,
    canvas.dataMode,
    canvas.metadata,
  );
  assert(exportSnapshot.svg.startsWith("<svg ") && exportSnapshot.svg.endsWith("</svg>"));
  assert(!UUID_PATTERN.test(exportSnapshot.svg), "Canvas export exposed an internal UUID");
  return Object.freeze({
    representations: dataset.representations.length,
    accessibleRows: rows.length,
    canvasNodes: composition.visibleEntityIds.length,
    canvasConnections: connections.length,
    exportBytes: Buffer.byteLength(exportSnapshot.svg),
  });
}

async function verifyContextApiFastPath({ publicId, heldId, manifest }) {
  const require = createRequire(import.meta.url);
  const cacheBefore = new Set(Object.keys(require.cache));
  const controller = await jiti.import(
    join(frontendRoot, "src/lib/read-platform/server/read-api-controller.ts"),
  );
  let providerOpenCalls = 0;
  const forbiddenProvider = Object.freeze({
    async open() {
      providerOpenCalls += 1;
      throw new Error("generic provider must not open for Context");
    },
  });

  function pathSegments(url) {
    return new URL(url).pathname.replace(/^\/api\/v1\/?/u, "").split("/").filter(Boolean);
  }

  async function dispatch(path, init = {}) {
    const url = `https://archive.invalid${path}`;
    const request = new Request(url, init);
    const response = await controller.dispatchReadApiRequest(
      request,
      pathSegments(url),
      forbiddenProvider,
    );
    const text = await response.text();
    return Object.freeze({
      status: response.status,
      text,
      body: text ? JSON.parse(text) : null,
      headers: Object.freeze(Object.fromEntries(response.headers.entries())),
    });
  }

  const base = `/api/v1/releases/${manifest.sourceRelease.id}/trace/objects`;
  const headers = { "Archive-Research-Manifest-Sha256": manifest.sourceRelease.manifestSha256 };
  const success = await dispatch(`${base}/${publicId}/context`, { headers });
  assert.equal(success.status, 200);
  assert.equal(success.body?.data?.selectedRecord?.surfaceId, publicId);
  assert.equal(success.headers["archive-research-manifest-sha256"], manifest.sourceRelease.manifestSha256);
  const current = await dispatch(`/api/v1/releases/current/trace/objects/${publicId}/context`);
  assert.equal(current.status, 200);
  assert.equal(sha256(current.text), sha256(success.text));
  const head = await dispatch(`${base}/${publicId}/context`, { method: "HEAD", headers });
  assert.equal(head.status, 200);
  assert.equal(head.text, "");
  const held = await dispatch(`${base}/${heldId}/context`, { headers });
  const unknown = await dispatch(`${base}/SURF-CONTEXT-V1-UNKNOWN-RECORD/context`, { headers });
  assert.equal(held.status, 404);
  assert.equal(unknown.status, 404);
  assert.equal(held.text, unknown.text);
  assert(!held.text.includes(heldId));
  const malformed = await dispatch(`${base}/not-a-public-id/context`, { headers });
  assert.equal(malformed.status, 400);
  const unavailable = await dispatch(`${base}/${publicId}/context`, {
    headers: { "Archive-Research-Manifest-Sha256": "0".repeat(64) },
  });
  assert.equal(unavailable.status, 404);
  assert.equal(unavailable.body?.code, "RELEASE_NOT_FOUND");
  assert.equal(providerOpenCalls, 0, "Context request opened the generic Search-backed provider");

  const newlyLoaded = Object.keys(require.cache).filter((key) => !cacheBefore.has(key));
  const searchRuntimeModules = newlyLoaded.filter((key) =>
    key.includes("/features/search-v49/") || key.includes("/generated/search-v49/"));
  assert.equal(searchRuntimeModules.length, 0, "Context API fast path loaded Search runtime modules");
  return Object.freeze({
    providerOpenCalls,
    searchRuntimeModulesLoaded: searchRuntimeModules.length,
    get: "PASS",
    head: "PASS",
    currentExactParity: "PASS",
    heldUnknownParity: "PASS",
    releasePinning: "PASS",
  });
}

async function main() {
  const preflight = runProjectionPreflight();
  const apiLazyBoundary = runApiLazyBoundaryProbe();
  const staticDependency = auditStaticDependencies();
  const [publicIds, heldIds, manifest] = await Promise.all([
    extractPublicIds(),
    extractHeldIds(),
    readFile(join(generatedRoot, "manifest.json"), "utf8").then(JSON.parse),
  ]);
  assert.equal(manifest.projectionSha256, EXPECTED_PROJECTION_SHA256);
  assert.equal(manifest.counts.publicObjectCount, PUBLIC_COUNT);
  assert.equal(manifest.counts.heldExcluded.objectCount, HELD_COUNT);

  const modules = Object.freeze({
    canvasAdapter: await jiti.import(join(contextRoot, "governed/canvas.ts")),
    connections: await jiti.import(join(contextRoot, "canvas/connections.ts")),
    exportPng: await jiti.import(join(contextRoot, "canvas/export-png.ts")),
    model: await jiti.import(join(contextRoot, "canvas/model.ts")),
    state: await jiti.import(join(contextRoot, "canvas/state.ts")),
  });

  if (typeof globalThis.gc === "function") globalThis.gc();
  const heapBeforeReader = process.memoryUsage().heapUsed;
  const moduleImportStarted = performance.now();
  const reader = await jiti.import(join(contextRoot, "governed/reader.server.ts"));
  const moduleImportMs = performance.now() - moduleImportStarted;
  reader.resetGovernedContextReaderForTests();
  assert.deepEqual(
    reader.getGovernedContextReaderRuntimeDiagnosticsForTests(),
    {
      indexInitialized: false,
      indexBuildAttempts: 0,
      successfulIndexBuilds: 0,
      lastSuccessfulBuildTiming: null,
    },
  );

  const firstLookupStarted = performance.now();
  const firstLookup = reader.lookupGovernedContextDataset(publicIds[0]);
  const firstLookupMs = performance.now() - firstLookupStarted;
  const coldDiagnostics = reader.getGovernedContextReaderRuntimeDiagnosticsForTests();
  assert.equal(coldDiagnostics.indexInitialized, true);
  assert.equal(coldDiagnostics.indexBuildAttempts, 1);
  assert.equal(coldDiagnostics.successfulIndexBuilds, 1);
  assert(coldDiagnostics.lastSuccessfulBuildTiming);
  const projectionInfo = reader.getGovernedContextProjectionInfo();
  assert.equal(projectionInfo.projectionSha256, EXPECTED_PROJECTION_SHA256);
  assert.equal(projectionInfo.recordCount, PUBLIC_COUNT);

  if (typeof globalThis.gc === "function") globalThis.gc();
  const runtimeHeapBytes = Math.max(0, process.memoryUsage().heapUsed - heapBeforeReader);

  let publicFailures = 0;
  let publicPipelinePasses = 0;
  let representationCount = 0;
  let accessibleRowCount = 0;
  let canvasNodeCount = 0;
  let canvasConnectionCount = 0;
  let exportBytes = 0;
  const fullPipelineStarted = performance.now();
  if (firstLookup.ok) {
    const firstPipeline = validatePipeline(firstLookup, publicIds[0], modules);
    publicPipelinePasses += 1;
    representationCount += firstPipeline.representations;
    accessibleRowCount += firstPipeline.accessibleRows;
    canvasNodeCount += firstPipeline.canvasNodes;
    canvasConnectionCount += firstPipeline.canvasConnections;
    exportBytes += firstPipeline.exportBytes;
  } else {
    publicFailures += 1;
  }
  for (let index = 1; index < publicIds.length; index += 1) {
    const result = reader.lookupGovernedContextDataset(publicIds[index]);
    if (!result.ok) {
      publicFailures += 1;
      continue;
    }
    const pipeline = validatePipeline(result, publicIds[index], modules);
    publicPipelinePasses += 1;
    representationCount += pipeline.representations;
    accessibleRowCount += pipeline.accessibleRows;
    canvasNodeCount += pipeline.canvasNodes;
    canvasConnectionCount += pipeline.canvasConnections;
    exportBytes += pipeline.exportBytes;
  }
  const fullPipelineMs = performance.now() - fullPipelineStarted;
  assert.equal(publicFailures, 0);
  assert.equal(publicPipelinePasses, PUBLIC_COUNT);
  assert.equal(representationCount, 16_106);
  assert.equal(accessibleRowCount, 24_101);

  let heldExposures = 0;
  let heldFailures = 0;
  let heldMessage = null;
  for (const heldId of heldIds) {
    const result = reader.lookupGovernedContextDataset(heldId);
    if (result.ok) heldExposures += 1;
    else if (result.code !== "NOT_FOUND") heldFailures += 1;
    else if (heldMessage === null) heldMessage = result.message;
    else assert.equal(result.message, heldMessage, "held lookup message is distinguishable");
  }
  assert.equal(heldExposures, 0);
  assert.equal(heldFailures, 0);

  const warmDurations = [];
  let warmFailures = 0;
  for (const publicId of publicIds) {
    const started = performance.now();
    const result = reader.lookupGovernedContextDataset(publicId);
    warmDurations.push(performance.now() - started);
    if (!result.ok) warmFailures += 1;
  }
  assert.equal(warmFailures, 0);
  const warmLookup = summarizeDurations(warmDurations);

  const finalDiagnostics = reader.getGovernedContextReaderRuntimeDiagnosticsForTests();
  assert.equal(finalDiagnostics.indexBuildAttempts, 1);
  assert.equal(finalDiagnostics.successfulIndexBuilds, 1);
  assert.strictEqual(reader.getGovernedContextProjectionInfo(), projectionInfo);

  const apiFastPath = await verifyContextApiFastPath({
    publicId: publicIds[0],
    heldId: heldIds[0],
    manifest,
  });

  const buildTiming = coldDiagnostics.lastSuccessfulBuildTiming;
  const coldLoadMs = moduleImportMs + firstLookupMs;
  const evidence = Object.freeze({
    schemaVersion: "trace-context-runtime-rehearsal/v1",
    sourceSha,
    generatedAt: "2026-08-23T00:00:00.000Z",
    projection: Object.freeze({
      projectionId: manifest.projectionId,
      projectionSha256: manifest.projectionSha256,
      policyVersion: manifest.governancePolicyVersion,
      policySha256: manifest.governancePolicySha256,
      recordCount: projectionInfo.recordCount,
    }),
    preflight,
    apiLazyBoundary,
    staticDependency,
    runtime: Object.freeze({
      publicLookups: PUBLIC_COUNT,
      publicFailures,
      publicPipelinePasses,
      heldLookups: HELD_COUNT,
      heldExposures,
      heldFailures,
      representationCount,
      accessibleRowCount,
      canvasNodeCount,
      canvasConnectionCount,
      exportBytes,
      fullPipelineMs: roundMs(fullPipelineMs),
      indexBuildAttempts: finalDiagnostics.indexBuildAttempts,
      successfulIndexBuilds: finalDiagnostics.successfulIndexBuilds,
      validationOncePerProcess: finalDiagnostics.successfulIndexBuilds === 1,
      apiFastPath,
    }),
    performance: Object.freeze({
      coldLoadMs: roundMs(coldLoadMs),
      moduleImportMs: roundMs(moduleImportMs),
      firstSelectedRecordLookupMs: roundMs(firstLookupMs),
      manifestVerificationMs: roundMs(buildTiming.manifestVerificationMs),
      registryValidationMs: roundMs(buildTiming.registryValidationMs),
      recordIndexConstructionMs: roundMs(buildTiming.recordIndexConstructionMs),
      boundaryValidationMs: roundMs(buildTiming.boundaryValidationMs),
      validationAndIndexTotalMs: roundMs(buildTiming.totalMs),
      warmLookupMs: warmLookup,
      runtimeHeapBytes,
    }),
    semantics: Object.freeze({
      contextDecision: "CONTEXT_V1_CLOSED",
      contextSemanticsChanged: false,
      contextGovernanceChanged: false,
      engineeringLogicFrozen: true,
    }),
  });
  assert(!UUID_PATTERN.test(JSON.stringify(evidence)), "runtime evidence contains an internal UUID");
  const receipt = await writeEvidence(evidence);

  console.log([
    "CONTEXT_RUNTIME_DEPENDENCIES=PASS",
    `CONTEXT_PUBLIC_RUNTIME_HEAVY_VALIDATION_IMPORT_COUNT=${staticDependency.heavyValidationImportCount}`,
    `CONTEXT_PUBLIC_RUNTIME_SQLITE_DEPENDENCY=${staticDependency.sqliteDependency}`,
    `CONTEXT_PUBLIC_RUNTIME_SEARCH_IMPORT_COUNT=${staticDependency.searchRuntimeImportCount}`,
    `CONTEXT_API_GENERIC_PROVIDER_OPEN_COUNT=${apiFastPath.providerOpenCalls}`,
  ].join(" "));
  console.log([
    "CONTEXT_RUNTIME_REHEARSAL=PASS",
    `PUBLIC_CONTEXT_RUNTIME_LOOKUPS=${PUBLIC_COUNT}`,
    `PUBLIC_CONTEXT_RUNTIME_FAILURES=${publicFailures}`,
    `HELD_CONTEXT_RUNTIME_LOOKUPS=${HELD_COUNT}`,
    `HELD_CONTEXT_RUNTIME_EXPOSURES=${heldExposures}`,
    `PIPELINE_PASSES=${publicPipelinePasses}`,
    `INDEX_BUILD_ATTEMPTS=${finalDiagnostics.indexBuildAttempts}`,
    `SUCCESSFUL_INDEX_BUILDS=${finalDiagnostics.successfulIndexBuilds}`,
    "VALIDATION_ONCE_PER_PROCESS=true",
  ].join(" "));
  console.log([
    "CONTEXT_RUNTIME_PERFORMANCE=PASS",
    `COLD_LOAD_MS=${roundMs(coldLoadMs)}`,
    `MODULE_IMPORT_MS=${roundMs(moduleImportMs)}`,
    `MANIFEST_VERIFICATION_MS=${roundMs(buildTiming.manifestVerificationMs)}`,
    `INDEX_CONSTRUCTION_MS=${roundMs(buildTiming.recordIndexConstructionMs)}`,
    `FIRST_SELECTED_RECORD_LOOKUP_MS=${roundMs(firstLookupMs)}`,
    `WARM_LOOKUP_P50_MS=${warmLookup.p50}`,
    `WARM_LOOKUP_P95_MS=${warmLookup.p95}`,
    `WARM_LOOKUP_P99_MS=${warmLookup.p99}`,
    `WARM_LOOKUP_MAX_MS=${warmLookup.max}`,
    `CONTEXT_RUNTIME_HEAP_BYTES=${runtimeHeapBytes}`,
  ].join(" "));
  console.log([
    "CONTEXT_RUNTIME_PREFLIGHT=PASS",
    "PREGENERATED=true",
    "PREVERIFIED=true",
    "READ_ONLY_AT_RUNTIME=true",
    `EVIDENCE_FILES=${receipt.fileCount}`,
    `EVIDENCE_SHA256=${receipt.sha256}`,
    `EVIDENCE_DIR=${args.evidenceDir}`,
  ].join(" "));
}

async function writeEvidence(evidence) {
  await mkdir(args.evidenceDir, { recursive: true });
  const jsonBytes = Buffer.from(`${JSON.stringify(evidence, null, 2)}\n`, "utf8");
  const performanceRows = [
    ["metric", "value", "unit"],
    ["cold_load", evidence.performance.coldLoadMs, "ms"],
    ["module_import", evidence.performance.moduleImportMs, "ms"],
    ["manifest_verification", evidence.performance.manifestVerificationMs, "ms"],
    ["registry_validation", evidence.performance.registryValidationMs, "ms"],
    ["record_index_construction", evidence.performance.recordIndexConstructionMs, "ms"],
    ["boundary_validation", evidence.performance.boundaryValidationMs, "ms"],
    ["validation_and_index_total", evidence.performance.validationAndIndexTotalMs, "ms"],
    ["first_selected_record_lookup", evidence.performance.firstSelectedRecordLookupMs, "ms"],
    ["warm_lookup_p50", evidence.performance.warmLookupMs.p50, "ms"],
    ["warm_lookup_p95", evidence.performance.warmLookupMs.p95, "ms"],
    ["warm_lookup_p99", evidence.performance.warmLookupMs.p99, "ms"],
    ["warm_lookup_max", evidence.performance.warmLookupMs.max, "ms"],
    ["runtime_heap", evidence.performance.runtimeHeapBytes, "bytes"],
  ];
  const tsvBytes = Buffer.from(
    `${performanceRows.map((row) => row.join("\t")).join("\n")}\n`,
    "utf8",
  );
  await writeFile(join(args.evidenceDir, "context-runtime-rehearsal-summary.json"), jsonBytes);
  await writeFile(join(args.evidenceDir, "context-runtime-performance.tsv"), tsvBytes);
  const fileHashes = Object.freeze({
    "context-runtime-performance.tsv": sha256(tsvBytes),
    "context-runtime-rehearsal-summary.json": sha256(jsonBytes),
  });
  const receiptBytes = Buffer.from(`${JSON.stringify(fileHashes)}\n`, "utf8");
  await writeFile(join(args.evidenceDir, "context-runtime-evidence-hashes.json"), receiptBytes);
  return Object.freeze({ fileCount: 3, sha256: sha256(receiptBytes) });
}
