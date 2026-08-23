import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { createRequire } from "node:module";
import {
  dirname,
  extname,
  join,
  relative,
  resolve,
} from "node:path";
import { fileURLToPath } from "node:url";
import createJiti from "jiti";
import ts from "typescript";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(here, "..");
const repositoryRoot = resolve(frontendRoot, "..");
const spacetimeRoot = join(frontendRoot, "src/features/trace-v49/spacetime");
const generatedRoot = join(frontendRoot, "generated/trace-spacetime-v1");
const requireBuild = parseArguments(process.argv.slice(2));
const jiti = createJiti(import.meta.url, {
  interopDefault: true,
  alias: {
    "@": join(frontendRoot, "src"),
    "server-only": join(here, "server-only-marker.mjs"),
  },
});

const EXPECTED_RECORDS = 7_995;
const EXPECTED_HELD = 7_928;
const EXPECTED_GEOGRAPHIES = 93;
const EXPECTED_PERIODS = 23;
const UUID_PATTERN = /\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b/iu;

try {
  const result = await verify();
  console.log([
    "SPACETIME_API_V1=PASS",
    "SPACETIME_API_ENDPOINT_COUNT=3",
    `SPACETIME_PROJECTION_SHA256=${result.projectionSha256}`,
    `SPACETIME_API_PERIOD_COUNT=${result.periodCount}`,
    `SPACETIME_API_GEOGRAPHY_COUNT=${result.geographyCount}`,
    `SPACETIME_API_PUBLIC_RECORD_COUNT=${result.recordCount}`,
    `SPACETIME_API_HELD_EXCLUDED=${result.heldExcluded}`,
    `SPACETIME_API_PROVIDER_OPEN_COUNT=${result.providerOpenCount}`,
    `SPACETIME_API_SEARCH_RUNTIME_IMPORT_COUNT=${result.searchRuntimeImportCount}`,
    `SPACETIME_API_SQLITE_RUNTIME_IMPORT_COUNT=${result.sqliteRuntimeImportCount}`,
    `SPACETIME_CLIENT_RECORD_ARTIFACT_REFERENCE_COUNT=${result.clientRecordArtifactReferenceCount}`,
    `SPACETIME_BUILD_CLIENT_GUARD=${result.buildClientGuard}`,
  ].join(" "));
} catch (error) {
  console.error(`SPACETIME_API_V1=FAIL ERROR=${safeError(error)}`);
  process.exitCode = 1;
}

function parseArguments(values) {
  let value = false;
  for (const argument of values) {
    if (argument === "--require-build") value = true;
    else throw new Error(`unknown argument: ${argument}`);
  }
  return value;
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

function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
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
      if (ts.isExternalModuleReference(node.moduleReference)) addLiteral(node.moduleReference.expression);
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
  const extensions = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json", ".css"];
  const candidates = extensions.includes(extname(base))
    ? [base]
    : [
      base,
      ...extensions.map((suffix) => `${base}${suffix}`),
      ...["index.ts", "index.tsx", "index.js", "index.mjs", "index.json"].map((name) => join(base, name)),
    ];
  return candidates.find((candidate) => existsSync(candidate)) ?? null;
}

function buildRuntimeImportGraph(entry) {
  const modules = new Set();
  const externalSpecifiers = new Set();
  const pending = [entry];
  while (pending.length > 0) {
    const current = pending.pop();
    if (!current || modules.has(current)) continue;
    modules.add(current);
    if (![".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"].includes(extname(current))) continue;
    for (const specifier of runtimeModuleSpecifiers(readFileSync(current, "utf8"), current)) {
      const resolved = resolveLocalModule(specifier, current);
      if (resolved) pending.push(resolved);
      else externalSpecifiers.add(specifier);
    }
  }
  return Object.freeze({
    modules: Object.freeze([...modules].sort(compareText)),
    externalSpecifiers: Object.freeze([...externalSpecifiers].sort(compareText)),
  });
}

function verifySourceBoundaries() {
  const readerPath = join(spacetimeRoot, "governed/reader.server.ts");
  const apiRuntimePath = join(spacetimeRoot, "governed/read-api-runtime.server.ts");
  const clientPath = join(spacetimeRoot, "map/SpacetimeWorkspace.tsx");
  const pagePath = join(frontendRoot, "src/app/trace/spacetime/page.tsx");
  const readerGraph = buildRuntimeImportGraph(readerPath);
  const apiGraph = buildRuntimeImportGraph(apiRuntimePath);
  const clientGraph = buildRuntimeImportGraph(clientPath);
  const serverModules = new Set([...readerGraph.modules, ...apiGraph.modules]);
  const searchModules = [...serverModules].filter((path) => path.includes("/search-v49/") || path.includes("/generated/search-v49/"));
  const sqliteImports = [...readerGraph.externalSpecifiers, ...apiGraph.externalSpecifiers]
    .filter((value) => value === "node:sqlite" || value === "sqlite");
  const filesystemImports = [...readerGraph.externalSpecifiers, ...apiGraph.externalSpecifiers]
    .filter((value) => value === "node:fs" || value === "node:fs/promises");
  assert.equal(searchModules.length, 0, "Spacetime runtime reaches Search modules");
  assert.equal(sqliteImports.length, 0, "Spacetime runtime reaches SQLite");
  assert.equal(filesystemImports.length, 0, "Spacetime runtime parses source files at request time");
  const forbiddenClientModules = clientGraph.modules.filter((path) =>
    path.endsWith("/governed/reader.server.ts")
    || path.endsWith("/governed/read-api-runtime.server.ts")
    || path.includes("/generated/trace-spacetime-v1/"));
  assert.equal(forbiddenClientModules.length, 0, "Spacetime client graph reaches server projection artifacts");

  const pageSource = readFileSync(pagePath, "utf8");
  assert(pageSource.includes("getGovernedSpacetimePeriodsDataset"), "Spacetime RSC does not read the projection directly");
  assert(!/\bfetch\s*\(/u.test(pageSource), "Spacetime RSC self-fetches its own API");
  assert(!pageSource.includes("/api/v1/"), "Spacetime RSC contains an internal API round trip");

  const controllerSource = readFileSync(join(frontendRoot, "src/lib/read-platform/server/read-api-controller.ts"), "utf8");
  const guardPosition = controllerSource.indexOf("if (isFullSpacetimeResourcePath(path))");
  const importPosition = controllerSource.indexOf('"@/features/trace-v49/spacetime/governed/read-api-runtime.server"');
  const lazyProviderPosition = controllerSource.indexOf('await import("./provider")');
  const providerOpenPosition = controllerSource.indexOf("const opened = await repositoryProvider.open(");
  const contextGuardPosition = controllerSource.indexOf("if (isFullContextResourcePath(path))");
  assert(guardPosition >= 0 && importPosition > guardPosition, "Spacetime API runtime import is not exact-path gated");
  assert(contextGuardPosition >= 0 && contextGuardPosition < lazyProviderPosition, "Context early dispatch was not preserved");
  assert(lazyProviderPosition > importPosition && providerOpenPosition > importPosition, "generic provider precedes Spacetime dispatch");
  return Object.freeze({
    searchRuntimeImportCount: searchModules.length,
    sqliteRuntimeImportCount: sqliteImports.length,
    clientRecordArtifactReferenceCount: forbiddenClientModules.length,
    graph: Object.freeze({
      readerModules: readerGraph.modules.length,
      apiModules: apiGraph.modules.length,
      clientModules: clientGraph.modules.length,
      clientEntry: relative(repositoryRoot, clientPath),
    }),
  });
}

function walkFiles(root) {
  if (!existsSync(root)) return [];
  const files = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    const path = join(root, entry.name);
    if (entry.isDirectory()) files.push(...walkFiles(path));
    else files.push(path);
  }
  return files;
}

function verifyBuildClientBoundary(firstPublicId) {
  if (!requireBuild) return "NOT_REQUIRED";
  const staticRoot = join(frontendRoot, ".next/static");
  const clientReferenceManifest = join(
    frontendRoot,
    ".next/server/app/trace/spacetime/page_client-reference-manifest.js",
  );
  assert(existsSync(staticRoot), "--require-build needs a completed Next production build");
  assert(existsSync(clientReferenceManifest), "Spacetime client-reference manifest is missing");
  const inspected = [
    ...walkFiles(staticRoot).filter((path) => /\.(?:js|json)$/u.test(path)),
    clientReferenceManifest,
  ];
  assert(inspected.length > 0, "no built client artifacts were found");
  const globallyForbidden = [
    "record-index.json",
    "reader.server.ts",
    "read-api-runtime.server.ts",
    "generated/trace-spacetime-v1/record-index",
  ];
  const hits = [];
  for (const path of inspected) {
    const text = readFileSync(path, "utf8");
    for (const needle of globallyForbidden) {
      if (text.includes(needle)) hits.push(`${relative(frontendRoot, path)}:${needle}`);
    }
  }
  assert.equal(hits.length, 0, `server record projection entered built client artifacts: ${hits.join(", ")}`);
  // A public stable ID can legitimately occur in an unrelated legacy client
  // route. Restrict that sentinel to this route's client-reference manifest
  // and the chunks it names instead of treating every archive chunk as owned
  // by Spacetime.
  const referenceText = readFileSync(clientReferenceManifest, "utf8");
  const routeChunkRefs = [...new Set([
    ...[...referenceText.matchAll(/static\/chunks\/[A-Za-z0-9_./-]+\.js/gu)].map((match) => match[0]),
    ...walkFiles(join(frontendRoot, ".next/static/chunks/app/trace/spacetime"))
      .filter((path) => path.endsWith(".js"))
      .map((path) => relative(join(frontendRoot, ".next"), path)),
  ])];
  const routeClientFiles = [
    clientReferenceManifest,
    ...routeChunkRefs.map((path) => join(frontendRoot, ".next", path)).filter(existsSync),
  ];
  assert(routeClientFiles.length > 1, "Spacetime route client chunk was not resolved");
  const publicIdHits = routeClientFiles.filter((path) => readFileSync(path, "utf8").includes(firstPublicId));
  assert.equal(publicIdHits.length, 0, "the Spacetime route client bundle contains a source-record sentinel");
  return "PASS";
}

function pathSegments(url) {
  return new URL(url).pathname
    .replace(/^\/api\/v1\/?/u, "")
    .split("/")
    .filter(Boolean)
    .map((value) => decodeURIComponent(value));
}

async function verify() {
  const manifest = readJson(join(generatedRoot, "manifest.json"));
  const records = readJson(join(generatedRoot, "record-index.json"));
  const geography = readJson(join(generatedRoot, "geography-registry.json"));
  assert.equal(records.records.length, EXPECTED_RECORDS);
  assert.equal(geography.entries.length, EXPECTED_GEOGRAPHIES);
  const sourceBoundaries = verifySourceBoundaries();
  const buildClientGuard = verifyBuildClientBoundary(records.records[0].objectId);

  const require = createRequire(import.meta.url);
  const cacheBefore = new Set(Object.keys(require.cache));
  const controller = await jiti.import(
    join(frontendRoot, "src/lib/read-platform/server/read-api-controller.ts"),
  );
  const reader = await jiti.import(
    join(spacetimeRoot, "governed/reader.server.ts"),
  );
  const gisDots = await jiti.import(join(spacetimeRoot, "gis/dot-density.ts"));
  reader.resetGovernedSpacetimeReaderForTests();
  assert.equal(reader.getGovernedSpacetimeReaderRuntimeDiagnosticsForTests().indexInitialized, false);
  let providerOpenCount = 0;
  const forbiddenProvider = Object.freeze({
    async open() {
      providerOpenCount += 1;
      throw new Error("generic provider must not open for governed Spacetime resources");
    },
  });

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

  const release = manifest.sourceRelease.researchReleaseId;
  const releaseHeader = {
    "Archive-Research-Manifest-Sha256": manifest.sourceRelease.researchManifestSha256,
  };
  const exactBase = `/api/v1/releases/${release}/trace/spacetime`;
  const periods = await dispatch(`${exactBase}/periods`, { headers: releaseHeader });
  assert.equal(periods.status, 200);
  assert.equal(periods.headers["cache-control"], "no-store");
  assert.equal(periods.headers.allow, "GET, HEAD, OPTIONS");
  assert.equal(periods.headers.vary, "Archive-Research-Manifest-Sha256");
  assert.equal(periods.headers["archive-research-release-id"], release);
  assert.equal(periods.headers["archive-research-manifest-sha256"], manifest.sourceRelease.researchManifestSha256);
  assert.equal(periods.body.apiVersion, "v1");
  assert.equal(periods.body.data.schemaVersion, "trace-spacetime/v1");
  assert.equal(periods.body.data.release.spacetimeProjectionSha256, manifest.projectionSha256);
  assert.equal(periods.body.data.periods.length, EXPECTED_PERIODS);
  assert.equal(periods.body.data.defaultPeriodId, manifest.defaultPeriodId);
  assert.equal(periods.body.data.geometry.assetPath, manifest.geometry.assetPath);

  const currentPeriods = await dispatch("/api/v1/releases/current/trace/spacetime/periods");
  assert.equal(currentPeriods.status, 200);
  assert.equal(sha256(currentPeriods.text), sha256(periods.text));
  const periodId = periods.body.data.defaultPeriodId;
  const atlas = await dispatch(`${exactBase}/atlas?period=${periodId}`, { headers: releaseHeader });
  assert.equal(atlas.status, 200);
  assert.equal(atlas.body.data.selectedPeriod.periodId, periodId);
  assert.equal(atlas.body.data.counts.denominator, atlas.body.data.selectedPeriod.recordCount);
  assert.equal(atlas.body.data.counts.heldExcluded, EXPECTED_HELD);
  assert.equal(atlas.body.data.realSemanticEdgeCount, 0);
  assert.equal(atlas.body.data.dotPolicy.policyVersion, gisDots.DEFAULT_AGGREGATE_DOT_FIELD_POLICY.policyVersion);
  assert.equal(atlas.body.data.dotPolicy.dotUnit, gisDots.DEFAULT_AGGREGATE_DOT_FIELD_POLICY.dotUnit);
  assert.equal(atlas.body.data.accessibleRows.length,
    atlas.body.data.mappedGeographies.length
    + atlas.body.data.aggregateOnlyGeographies.length
    + atlas.body.data.unmappedGeographies.length);
  const selectedGeography = atlas.body.data.mappedGeographies
    .slice()
    .sort((left, right) => right.recordCount - left.recordCount)[0];
  assert(selectedGeography, "default atlas has no mapped geography");
  const recordPath = `${exactBase}/geographies/${selectedGeography.geographyId}/records?period=${periodId}&first=2`;
  const firstPage = await dispatch(recordPath, { headers: releaseHeader });
  assert.equal(firstPage.status, 200);
  assert.equal(firstPage.body.data.nodes.length, 2);
  assert.equal(firstPage.body.data.totalCount, selectedGeography.recordCount);
  assert.equal(firstPage.body.data.geography.geographyId, selectedGeography.geographyId);
  assert.equal(firstPage.body.data.pageInfo.hasNextPage, true);
  assert(firstPage.body.data.pageInfo.endCursor);
  assert(!firstPage.text.includes("observationId"));
  assert(!firstPage.text.includes("rawRegionDisplay"));
  assert(!UUID_PATTERN.test(firstPage.text));
  const secondPage = await dispatch(
    `${recordPath}&after=${encodeURIComponent(firstPage.body.data.pageInfo.endCursor)}`,
    { headers: releaseHeader },
  );
  assert.equal(secondPage.status, 200);
  assert.equal(secondPage.body.data.nodes.length, 2);
  assert.notEqual(secondPage.body.data.nodes[0].stableId, firstPage.body.data.nodes[0].stableId);

  const invalidCursor = await dispatch(`${recordPath}&after=not-a-cursor`, { headers: releaseHeader });
  assert.equal(invalidCursor.status, 400);
  assert.equal(invalidCursor.body.code, "INVALID_CURSOR");
  const missingPeriod = await dispatch(`${exactBase}/atlas`, { headers: releaseHeader });
  assert.equal(missingPeriod.status, 400);
  const unknownPeriod = await dispatch(`${exactBase}/atlas?period=SPT-PERIOD-1790-1800`, { headers: releaseHeader });
  assert.equal(unknownPeriod.status, 404);
  const unknownGeography = await dispatch(
    `${exactBase}/geographies/SPTGEO:${"0".repeat(64)}/records?period=${periodId}`,
    { headers: releaseHeader },
  );
  assert.equal(unknownGeography.status, 404);
  const overLimit = await dispatch(
    `${exactBase}/geographies/${selectedGeography.geographyId}/records?period=${periodId}&first=101`,
    { headers: releaseHeader },
  );
  assert.equal(overLimit.status, 400);
  const wrongRelease = await dispatch(`${exactBase}/periods`, {
    headers: { "Archive-Research-Manifest-Sha256": "0".repeat(64) },
  });
  assert.equal(wrongRelease.status, 404);
  assert.equal(wrongRelease.body.code, "RELEASE_NOT_FOUND");
  const extraQuery = await dispatch(`${exactBase}/periods?period=${periodId}`, { headers: releaseHeader });
  assert.equal(extraQuery.status, 400);
  for (const path of [
    `${exactBase}/periods`,
    `${exactBase}/atlas?period=${periodId}`,
    recordPath,
  ]) {
    const head = await dispatch(path, { method: "HEAD", headers: releaseHeader });
    assert.equal(head.status, 200);
    assert.equal(head.text, "");
  }
  const options = await dispatch(`${exactBase}/periods`, { method: "OPTIONS" });
  assert.equal(options.status, 204);
  assert.equal(options.text, "");
  const post = await dispatch(`${exactBase}/periods`, { method: "POST" });
  assert.equal(post.status, 405);
  assert.equal(providerOpenCount, 0, "Spacetime API opened the generic provider");

  const diagnostics = reader.getGovernedSpacetimeReaderRuntimeDiagnosticsForTests();
  assert.equal(diagnostics.indexBuildAttempts, 1);
  assert.equal(diagnostics.successfulIndexBuilds, 1);
  assert(diagnostics.lastSuccessfulBuildTiming.totalMs > 0);
  const newlyLoaded = Object.keys(require.cache).filter((key) => !cacheBefore.has(key));
  const searchRuntimeModules = newlyLoaded.filter((key) =>
    key.includes("/features/search-v49/") || key.includes("/generated/search-v49/"));
  assert.equal(searchRuntimeModules.length, 0, "Spacetime fast path loaded Search runtime modules");
  assert.equal(manifest.counts.publicObjects, EXPECTED_RECORDS);
  assert.equal(manifest.counts.heldObjects, EXPECTED_HELD);
  return Object.freeze({
    projectionSha256: manifest.projectionSha256,
    periodCount: periods.body.data.periods.length,
    geographyCount: geography.entries.length,
    recordCount: manifest.counts.publicObjects,
    heldExcluded: atlas.body.data.counts.heldExcluded,
    providerOpenCount,
    searchRuntimeImportCount: sourceBoundaries.searchRuntimeImportCount + searchRuntimeModules.length,
    sqliteRuntimeImportCount: sourceBoundaries.sqliteRuntimeImportCount,
    clientRecordArtifactReferenceCount: sourceBoundaries.clientRecordArtifactReferenceCount,
    buildClientGuard,
  });
}
