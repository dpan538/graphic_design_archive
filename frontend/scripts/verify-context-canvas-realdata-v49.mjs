import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { existsSync } from "node:fs";
import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import { dirname, extname, isAbsolute, join, relative, resolve } from "node:path";
import { performance } from "node:perf_hooks";
import { fileURLToPath } from "node:url";
import createJiti from "jiti";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(here, "..");
const repositoryRoot = resolve(frontendRoot, "..");
const contextRoot = join(frontendRoot, "src/features/trace-v49/context");
const canvasRoot = join(contextRoot, "canvas");
const defaultEvidenceDir = join(
  repositoryRoot,
  "docs/audits/v49-context-canvas-realdata-round2/raw",
);
const fixedExportInstant = new Date("2026-08-23T00:00:00.000Z");
const viewportSize = Object.freeze({ width: 1_280, height: 760 });
const uuidPattern = /\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b/iu;
const publicStableIdPattern = /\bSURF-[A-Z0-9]+(?:-[A-Z0-9]+)*\b/gu;
const connectorPathPattern = /^M -?\d+(?:\.\d+)? -?\d+(?:\.\d+)? H -?\d+(?:\.\d+)? V -?\d+(?:\.\d+)? H -?\d+(?:\.\d+)?$/u;
const failureHeader = "pass\tobject_ordinal\ttemplate\tbug_class\tmessage\n";
const evidenceDir = parseEvidenceDir(process.argv.slice(2));

const jiti = createJiti(import.meta.url, {
  alias: {
    "@": join(frontendRoot, "src"),
    "server-only": join(here, "server-only-stub.mjs"),
  },
});

// These imports intentionally target renderer-independent modules. The real-data
// index/projector are server-only; no React component or CSS barrel is loaded here.
const sourceIndex = await jiti.import(join(contextRoot, "realdata/source-index.server.ts"));
const realProjector = await jiti.import(join(contextRoot, "realdata/project.server.ts"));
const realTypes = await jiti.import(join(contextRoot, "realdata/types.ts"));
const contextProject = await jiti.import(join(contextRoot, "project.ts"));
const canvasTypes = await jiti.import(join(canvasRoot, "types.ts"));
const templates = await jiti.import(join(canvasRoot, "templates.ts"));
const layout = await jiti.import(join(canvasRoot, "layout.ts"));
const connections = await jiti.import(join(canvasRoot, "connections.ts"));
const stateModule = await jiti.import(join(canvasRoot, "state.ts"));
const reducerModule = await jiti.import(join(canvasRoot, "reducer.ts"));
const persistence = await jiti.import(join(canvasRoot, "persistence.ts"));
const exportPng = await jiti.import(join(canvasRoot, "export-png.ts"));
const displayLabel = await jiti.import(join(canvasRoot, "display-label.ts"));

const failureRows = [];

try {
  await main();
} catch (error) {
  failureRows.push([
    "global",
    "0",
    "none",
    "verifier_failure",
    sanitizeFailureMessage(error),
  ]);
  await mkdir(evidenceDir, { recursive: true });
  await writeFile(
    join(evidenceDir, "all-object-failures.tsv"),
    failureHeader + failureRows.map(tsvRow).join("\n") + "\n",
    "utf8",
  );
  console.error(`CONTEXT_REALDATA_V49_TESTS=FAIL ERROR=${sanitizeFailureMessage(error)}`);
  process.exitCode = 1;
}

async function main() {
  const templateIds = templates.CONTEXT_CANVAS_TEMPLATES.map((template) => template.templateId);
  assert.deepEqual(templateIds, [
    "context-overview",
    "descriptive-context",
    "curated-context",
    "full-context",
  ]);
  const frozenInputBinding = await validateFrozenInputBinding();

  const heapBefore = process.memoryUsage().heapUsed;
  sourceIndex.resetRealContextValidationSourceIndexForTests();
  const rebuildAStarted = performance.now();
  let indexA = sourceIndex.loadRealContextValidationSourceIndexForVerification();
  const rebuildAMs = performance.now() - rebuildAStarted;
  validateIndexEnvelope(indexA);
  const sourceIndexShaA = digestSourceIndex(indexA);
  const passA = validateAllObjects(indexA, "A", true, templateIds);

  // Drop the first corpus reference before forcing the second clean rebuild. The
  // first pass retains only aggregate counters and one-way checksums.
  indexA = null;
  sourceIndex.resetRealContextValidationSourceIndexForTests();
  const rebuildBStarted = performance.now();
  const indexB = sourceIndex.loadRealContextValidationSourceIndexForVerification();
  const rebuildBMs = performance.now() - rebuildBStarted;
  validateIndexEnvelope(indexB);
  const sourceIndexShaB = digestSourceIndex(indexB);
  const passB = validateAllObjects(indexB, "B", false, templateIds);

  const warmReferenceStarted = performance.now();
  const warmIndex = sourceIndex.loadRealContextValidationSourceIndexForVerification();
  const warmReferenceMs = performance.now() - warmReferenceStarted;
  assert.strictEqual(warmIndex, indexB, "the warm loader must reuse the read-only index");

  assert.equal(sourceIndexShaB, sourceIndexShaA, "source-index rebuild checksum mismatch");
  assert.deepEqual(passB.hashes, passA.hashes, "full projection checksum mismatch");
  assert.deepEqual(
    deterministicPassSummary(passB.stats),
    deterministicPassSummary(passA.stats),
    "full aggregate validation report mismatch",
  );

  const lookupSummary = validateLookupBoundary(indexB);
  const persistenceSummary = validateRecordSwitchAndPersistence(indexB);
  const bundleSummary = await validateClientBundleBoundary(indexB.heldStableIds);
  const productionSummary = validateProductionDefault(indexB);

  const deterministicSummary = deterministicPassSummary(passA.stats);
  validateFrozenExpectations(indexB, deterministicSummary);
  validateAllBugCounters(deterministicSummary);
  validatePerformance(passA.stats.performance);
  const bugClassTotals = buildBugClassTotals(deterministicSummary, lookupSummary);
  validateBugClassTotals(bugClassTotals);

  const aggregateSha256 = sha256(stableJson({
    source_manifest_sha256: frozenInputBinding.source_manifest_sha256,
    source_index_sha256: sourceIndexShaA,
    dataset_sha256: passA.hashes.dataset,
    entity_identity_sha256: passA.hashes.entityIdentity,
    connection_identity_sha256: passA.hashes.connectionIdentity,
    template_selection_sha256: passA.hashes.templateSelection,
    layout_geometry_sha256: passA.hashes.layoutGeometry,
    accessibility_sha256: passA.hashes.accessibility,
    export_preparation_sha256: passA.hashes.exportPreparation,
    aggregate_validation: deterministicSummary,
    bug_class_totals: bugClassTotals,
  }));

  const invariants = buildInvariantResults({
    index: indexB,
    deterministicSummary,
    sourceIndexShaA,
    sourceIndexShaB,
    passA,
    passB,
    lookupSummary,
    persistenceSummary,
    bundleSummary,
    productionSummary,
  });
  assert.equal(invariants.length, 18);
  assert.equal(invariants.every((item) => item.status === "PASS"), true);

  const performanceSummary = summarizePerformance(passA.stats.performance);
  const loaderPerformanceSummary = Object.freeze({
    cold_rebuild_a_ms: rounded(rebuildAMs),
    cold_rebuild_b_ms: rounded(rebuildBMs),
    cold_rebuild_p50_ms: rounded(percentile([rebuildAMs, rebuildBMs], 0.5)),
    cold_rebuild_p95_ms: rounded(percentile([rebuildAMs, rebuildBMs], 0.95)),
    heap_delta_bytes: Math.max(0, process.memoryUsage().heapUsed - heapBefore),
    index_cache_identity_reused: true,
    warm_cache_reference_ms: rounded(warmReferenceMs),
    warm_selected_record_lookup: lookupSummary.warmLookupPerformance,
  });

  const evidence = buildEvidence({
    aggregateSha256,
    bugClassTotals,
    bundleSummary,
    deterministicSummary,
    frozenInputBinding,
    invariants,
    loaderPerformanceSummary,
    lookupSummary,
    passA,
    passB,
    performanceSummary,
    persistenceSummary,
    productionSummary,
    sourceIndexShaA,
    sourceIndexShaB,
  });
  assertEvidenceIsSanitized(evidence, indexB.heldStableIds);
  const evidenceReceipt = await writeEvidence(evidenceDir, evidence);

  const datasetP50 = performanceSummary.dataset_derivation_ms.p50;
  const datasetP95 = performanceSummary.dataset_derivation_ms.p95;
  const datasetP99 = performanceSummary.dataset_derivation_ms.p99;
  const canvasP95 = performanceSummary.canvas_pure_total_ms.p95;
  const bundleStatus = bundleSummary.bundle_status;

  // Stable five-line stdout contract. Evidence and diagnostic detail live in the
  // sanitized files, never in per-record console output.
  console.log(`CONTEXT_REALDATA_V49_REBUILD=PASS RUNS=2 PUBLIC_OBJECTS=${indexB.publicCount} HELD_OBJECTS=${indexB.heldCount} CHECKSUM_MATCH=true AGGREGATE_SHA256=${aggregateSha256}`);
  console.log(`CONTEXT_REALDATA_V49_TESTS=PASS OBJECTS_TESTED=${passA.stats.objectsTested} TEMPLATE_CASES=${passA.stats.templateCases} FAILED_OBJECTS=${passA.stats.failedObjects.size} INVARIANTS=18`);
  console.log(`CONTEXT_REALDATA_V49_SECURITY=PASS HELD_LOOKUPS=${lookupSummary.held_lookups} HELD_EXPOSED=${lookupSummary.held_exposed} LOOKUP_INDISTINGUISHABLE=true CLIENT_BUNDLE_GUARD=${bundleStatus} PRODUCTION_DEFAULT_EXPOSURE=false`);
  console.log(`CONTEXT_REALDATA_V49_PERF=PASS DATASET_DERIVATION_P50_MS=${formatMs(datasetP50)} DATASET_DERIVATION_P95_MS=${formatMs(datasetP95)} DATASET_DERIVATION_P99_MS=${formatMs(datasetP99)} CANVAS_PURE_P95_MS=${formatMs(canvasP95)}`);
  console.log(`CONTEXT_REALDATA_V49_EVIDENCE=PASS FILES=${evidenceReceipt.fileCount} SHA256=${evidenceReceipt.sha256}`);
}

function validateIndexEnvelope(index) {
  assert.equal(index.canonicalCount, sourceIndex.TRACE_CONTEXT_EXPECTED_CANONICAL_COUNT);
  assert.equal(index.publicCount, sourceIndex.TRACE_CONTEXT_EXPECTED_PUBLIC_COUNT);
  assert.equal(index.heldCount, sourceIndex.TRACE_CONTEXT_EXPECTED_HELD_COUNT);
  assert.equal(
    index.publicFolderMembershipCount,
    sourceIndex.TRACE_CONTEXT_EXPECTED_PUBLIC_FOLDER_MEMBERSHIP_COUNT,
  );
  assert.equal(
    index.publicControlledAssignmentCount,
    sourceIndex.TRACE_CONTEXT_EXPECTED_PUBLIC_CONTROLLED_ASSIGNMENT_COUNT,
  );
  assert.equal(index.eligibleStableIds.length, 7_995);
  assert.equal(index.candidates.length, 7_995);
  assert.equal(index.candidateByStableId.size, 7_995);
  assert.equal(index.heldStableIds.size, 7_928);
  assert.equal(index.eligibleStableIds.some((id) => index.heldStableIds.has(id)), false);
  assert.deepEqual(index.candidates.map((candidate) => candidate.stableId), index.eligibleStableIds);
}

async function validateFrozenInputBinding() {
  const expectedPaths = [
    "data/prefreeze_candidate_v48.sqlite",
    "database/FREEZE_V49.json",
    "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv",
  ];
  const registry = realProjector.TRACE_CONTEXT_REALDATA_FROZEN_INPUT_SHA256;
  assert.deepEqual(Object.keys(registry).sort(compareText), expectedPaths);
  const actual = {};
  for (const path of expectedPaths) {
    assert.match(registry[path], /^[0-9a-f]{64}$/u);
    actual[path] = sha256(await readFile(join(repositoryRoot, path)));
    assert.equal(actual[path], registry[path], `frozen input checksum mismatch: ${path}`);
  }
  const manifestMaterial = [
    `mapping:${realTypes.TRACE_CONTEXT_REALDATA_MAPPING_VERSION}`,
    ...Object.entries(registry)
      .sort(([left], [right]) => compareText(left, right))
      .map(([path, digest]) => `${path}:${digest}`),
  ].join("\n");
  const sourceManifestSha256 = sha256(manifestMaterial);
  assert.equal(sourceManifestSha256, realProjector.TRACE_CONTEXT_REALDATA_MANIFEST_SHA256);
  return Object.freeze({
    frozen_input_count: expectedPaths.length,
    frozen_input_sha256: Object.freeze(actual),
    mapping_version: realTypes.TRACE_CONTEXT_REALDATA_MAPPING_VERSION,
    source_manifest_sha256: sourceManifestSha256,
  });
}

function digestSourceIndex(index) {
  const digest = createHash("sha256");
  updateHash(digest, {
    frozenInputs: realProjector.TRACE_CONTEXT_REALDATA_FROZEN_INPUT_SHA256,
    manifestSha256: realProjector.TRACE_CONTEXT_REALDATA_MANIFEST_SHA256,
    mappingVersion: realTypes.TRACE_CONTEXT_REALDATA_MAPPING_VERSION,
  });
  updateHash(digest, [
    index.canonicalCount,
    index.publicCount,
    index.heldCount,
    index.publicFolderMembershipCount,
    index.publicControlledAssignmentCount,
  ]);
  for (const candidate of index.candidates) updateHash(digest, candidate);
  for (const heldId of [...index.heldStableIds].sort(compareText)) updateHash(digest, heldId);
  return digest.digest("hex");
}

function validateAllObjects(index, passName, measurePerformance, templateIds) {
  const stats = createPassStats(measurePerformance);
  const hashers = Object.fromEntries([
    "dataset",
    "entityIdentity",
    "connectionIdentity",
    "templateSelection",
    "layoutGeometry",
    "accessibility",
    "exportPreparation",
  ].map((name) => [name, createHash("sha256")]));

  index.candidates.forEach((candidate, candidateIndex) => {
    stats.objectsTested += 1;
    let objectFailed = false;
    const candidateSnapshot = JSON.stringify(candidate);
    let projection;
    const derivationStarted = performance.now();
    try {
      projection = realProjector.projectRealContextValidationDataset(candidate);
    } catch (error) {
      objectFailed = true;
      recordFailure(passName, candidateIndex, "all", "dataset_derivation_failure", error);
    }
    const derivationMs = performance.now() - derivationStarted;
    if (measurePerformance) stats.performance.datasetDerivation.push(derivationMs);

    if (!projection) {
      stats.templateCases += templateIds.length;
      stats.exportPreparationFailureCount += templateIds.length;
      stats.failedObjects.add(candidateIndex);
      return;
    }

    try {
      validateProjection(candidate, candidateSnapshot, projection, stats, hashers, measurePerformance);
    } catch (error) {
      objectFailed = true;
      recordFailure(passName, candidateIndex, "all", "dataset_contract_failure", error);
    }

    for (const templateId of templateIds) {
      stats.templateCases += 1;
      try {
        validateTemplateCase(
          candidate,
          projection,
          templateId,
          stats,
          hashers,
          measurePerformance,
        );
      } catch (error) {
        objectFailed = true;
        recordFailure(passName, candidateIndex, templateId, "template_case_failure", error);
      }
    }
    if (!objectFailed) stats.exportObjects.add(candidateIndex);
    else stats.failedObjects.add(candidateIndex);
    assert.equal(JSON.stringify(candidate), candidateSnapshot, "projection or Canvas operation mutated source data");
  });

  finalizeLabelIdentityStats(stats);
  return Object.freeze({
    stats,
    hashes: Object.freeze(Object.fromEntries(
      Object.entries(hashers).map(([name, hasher]) => [name, hasher.digest("hex")]),
    )),
  });
}

function validateProjection(candidate, candidateSnapshot, projection, stats, hashers, measurePerformance) {
  const { dataset, metadata } = projection;
  assert.equal(metadata.dataMode, "real_v49_validation");
  assert.equal(metadata.mappingVersion, realTypes.TRACE_CONTEXT_REALDATA_MAPPING_VERSION);
  assert.equal(metadata.selectedPublicStableId, candidate.stableId);
  assert.equal(metadata.candidateState, "not_published");
  assert.equal(metadata.governedPublicRelease, false);
  assert.equal(metadata.historicalEvidence, false);
  assert.equal(metadata.publicReleaseData, false);
  assert.equal(dataset.selectedRecord.stableId, candidate.stableId);
  assert.equal(dataset.selectedRecord.label, candidate.title);
  assert.equal(dataset.release.releaseId, realProjector.TRACE_CONTEXT_REALDATA_RELEASE_ID);
  assert.equal(dataset.release.manifestSha256, realProjector.TRACE_CONTEXT_REALDATA_MANIFEST_SHA256);
  assert.equal(dataset.availability.state, "not_published");
  assert.equal(dataset.semanticEdges.length, 0);
  assert.equal(dataset.counts.semanticEdgeCount, 0);
  assert.equal(dataset.controlledAssignments.every((item) => item.state === "proposed"), true);
  assert.equal(dataset.curatedMemberships.every((item) => item.state === "proposed"), true);
  assert.equal(JSON.stringify(candidate), candidateSnapshot);

  const uniqueFolders = new Map();
  for (const folder of candidate.folders) {
    const identity = `${folder.folderType}\u0000${folder.folderToken}`;
    const prior = uniqueFolders.get(identity);
    if (prior !== undefined) assert.equal(prior, folder.label, "same source identity has conflicting label");
    else uniqueFolders.set(identity, folder.label);
  }
  const expectedControlled = [...uniqueFolders].filter(([identity]) =>
    !identity.startsWith("region\u0000")).length;
  const expectedCurated = uniqueFolders.size;
  const expectedAssociations = expectedControlled + expectedCurated;
  assert.equal(dataset.controlledAssignments.length, expectedControlled);
  assert.equal(dataset.curatedMemberships.length, expectedCurated);
  assert.equal(dataset.counts.nonSemanticAssociationCount, expectedAssociations);
  assert.equal(dataset.counts.denominator, candidate.folders.length);
  assert.ok(expectedAssociations >= 5 && expectedAssociations <= 9);

  stats.workloads.push(expectedAssociations);
  if (dataset.controlledAssignments.length > 0) stats.controlledCoverage += 1;
  if (dataset.curatedMemberships.length > 0) stats.curatedCoverage += 1;
  stats.semanticEdgeCount += dataset.semanticEdges.length;

  const entityIds = dataset.items.map(canvasTypes.contextCanvasEntityId);
  const entityCollisions = entityIds.length - new Set(entityIds).size;
  stats.entityIdCollisionCount += entityCollisions;
  assert.equal(entityCollisions, 0, "duplicate entity identity");

  const sourceConnectionIds = [
    ...dataset.controlledAssignments.map((item) => `connection:controlled_assignment:${item.id}`),
    ...dataset.curatedMemberships.map((item) => `connection:curated_membership:${item.id}`),
  ];
  const connectionCollisions = sourceConnectionIds.length - new Set(sourceConnectionIds).size;
  stats.connectionIdCollisionCount += connectionCollisions;
  assert.equal(connectionCollisions, 0, "duplicate connection identity");

  const entityIdSet = new Set(entityIds);
  for (const assignment of dataset.controlledAssignments) {
    assert.match(assignment.assignmentType, /^validation_(?:medium|theme|movement)_candidate$/u);
    assert.equal(entityIdSet.has(canvasTypes.contextCanvasEntityId(assignment.subject)), true);
    assert.equal(entityIdSet.has(canvasTypes.contextCanvasEntityId(assignment.value)), true);
    observeLabel(stats, "controlled_assignment", assignment.value.label, assignment.value.stableId);
  }
  for (const membership of dataset.curatedMemberships) {
    assert.match(membership.membershipType, /^validation_folder_membership:(?:medium|theme|movement|region)$/u);
    assert.equal(entityIdSet.has(canvasTypes.contextCanvasEntityId(membership.member)), true);
    assert.equal(entityIdSet.has(canvasTypes.contextCanvasEntityId(membership.container)), true);
    observeLabel(stats, "curated_membership", membership.container.label, membership.container.stableId);
  }
  observeLabel(stats, "object_title", dataset.selectedRecord.label, dataset.selectedRecord.stableId);

  const accessibleStarted = performance.now();
  const accessibleAgain = contextProject.toContextAccessibleRows(dataset);
  const accessibleMs = performance.now() - accessibleStarted;
  if (measurePerformance) stats.performance.accessibilityDerivation.push(accessibleMs);
  assert.deepEqual(accessibleAgain, dataset.accessibleRows);
  assert.equal(dataset.accessibleRows.length, 1 + expectedAssociations);
  const rowIds = dataset.accessibleRows.map((row) => row.id);
  const rowCollisions = rowIds.length - new Set(rowIds).size;
  stats.duplicateAccessibleRowCount += rowCollisions;
  assert.equal(rowCollisions, 0, "duplicate accessible row");
  assert.equal(
    dataset.accessibleRows.some((row) =>
      row.category === "selected_record"
      && row.id === `selected:${dataset.selectedRecord.stableId}`),
    true,
  );
  assert.equal(dataset.accessibleRows.every((row) => row.label.trim().length > 0), true);

  for (const item of dataset.items) {
    const full = displayLabel.contextCanvasFullLabel(item);
    assert.equal(full, item.label?.trim() ? item.label : item.stableId);
    assert.equal(dataset.accessibleRows.some((row) => row.label.includes(full)), true);
  }

  const datasetJson = JSON.stringify(dataset);
  assert.doesNotMatch(datasetJson, uuidPattern);
  assert.equal(collectKeys(dataset).has("folderToken"), false);
  for (const folder of candidate.folders) assert.equal(datasetJson.includes(folder.folderToken), false);

  const datasetBytes = Buffer.byteLength(datasetJson, "utf8");
  stats.payload.entityCount.push(dataset.items.length);
  stats.payload.connectionCount.push(expectedAssociations);
  stats.payload.datasetBytes.push(datasetBytes);
  stats.payload.accessibleRowCount.push(dataset.accessibleRows.length);
  stats.persistenceKeys.add(persistence.contextCanvasPersistenceKey(dataset));

  updateHash(hashers.dataset, projection);
  updateHash(hashers.entityIdentity, entityIds);
  updateHash(hashers.connectionIdentity, sourceConnectionIds);
  updateHash(hashers.accessibility, dataset.accessibleRows);
}

function validateTemplateCase(candidate, projection, templateId, stats, hashers, measurePerformance) {
  const { dataset } = projection;
  const pureStarted = performance.now();

  const initializeStarted = performance.now();
  const composition = templates.initializeContextCanvasTemplate(dataset, templateId);
  const initializeMs = performance.now() - initializeStarted;
  if (measurePerformance) stats.performance.templateInitialization.push(initializeMs);
  assert.deepEqual(templates.initializeContextCanvasTemplate(dataset, templateId), composition);
  assert.equal(composition.templateId, templateId);
  assert.equal(composition.templateVersion, 1);
  assert.equal(composition.visibleEntityIds.includes(canvasTypes.contextCanvasEntityId(dataset.selectedRecord)), true);
  assert.equal(new Set(composition.visibleEntityIds).size, composition.visibleEntityIds.length);

  const allowed = new Set(dataset.items.map(canvasTypes.contextCanvasEntityId));
  assert.equal(composition.visibleEntityIds.every((id) => allowed.has(id)), true);
  assert.deepEqual([...Object.keys(composition.positions)].sort(compareText), [...composition.visibleEntityIds].sort(compareText));

  const arrangeStarted = performance.now();
  const arranged = layout.autoArrangeContextCanvas(dataset, composition.visibleEntityIds);
  const arrangeMs = performance.now() - arrangeStarted;
  if (measurePerformance) stats.performance.autoArrange.push(arrangeMs);
  assert.deepEqual(arranged, composition.positions);
  assert.deepEqual(
    layout.autoArrangeContextCanvas(dataset, [...composition.visibleEntityIds].reverse()),
    arranged,
  );

  const boundsFitStarted = performance.now();
  const bounds = layout.computeContextCanvasBounds(composition.visibleEntityIds, arranged);
  const fitted = layout.fitContextCanvasViewport(bounds, viewportSize);
  const boundsFitMs = performance.now() - boundsFitStarted;
  if (measurePerformance) stats.performance.boundsAndFit.push(boundsFitMs);
  assert.equal(bounds.empty, false);
  if (!Number.isFinite(fitted.x)) stats.nonfiniteXCount += 1;
  if (!Number.isFinite(fitted.y)) stats.nonfiniteYCount += 1;
  if (!Number.isFinite(fitted.zoom)) stats.nonfiniteZoomCount += 1;
  assertFinite(bounds.x, bounds.y, bounds.width, bounds.height, fitted.x, fitted.y, fitted.zoom);
  assert.ok(fitted.zoom >= canvasTypes.CONTEXT_CANVAS_MIN_ZOOM);
  assert.ok(fitted.zoom <= canvasTypes.CONTEXT_CANVAS_MAX_ZOOM);

  const rectangles = composition.visibleEntityIds.map((entityId) => {
    const position = arranged[entityId];
    assert.ok(position, "visible node is missing its position");
    if (!Number.isFinite(position.x)) stats.nonfiniteXCount += 1;
    if (!Number.isFinite(position.y)) stats.nonfiniteYCount += 1;
    assertFinite(position.x, position.y);
    const rect = {
      entityId,
      x: position.x,
      y: position.y,
      right: position.x + canvasTypes.CONTEXT_CANVAS_NODE_WIDTH,
      bottom: position.y + canvasTypes.CONTEXT_CANVAS_NODE_HEIGHT,
    };
    if (
      rect.x < bounds.x || rect.y < bounds.y
      || rect.right > bounds.x + bounds.width || rect.bottom > bounds.y + bounds.height
    ) stats.nodeOutsideBoundsCount += 1;
    return rect;
  });
  for (let left = 0; left < rectangles.length; left += 1) {
    for (let right = left + 1; right < rectangles.length; right += 1) {
      if (rectanglesOverlap(rectangles[left], rectangles[right])) stats.autoLayoutCollisionCount += 1;
    }
  }
  assert.equal(stats.nodeOutsideBoundsCount, 0, "node outside computed bounds");
  assert.equal(stats.autoLayoutCollisionCount, 0, "auto-layout collision");

  const connectionStarted = performance.now();
  const visibleConnections = connections.deriveVisibleContextCanvasConnections(
    dataset,
    composition.visibleEntityIds,
  );
  const geometry = connections.buildContextCanvasConnectionGeometry(dataset, composition);
  const connectionMs = performance.now() - connectionStarted;
  if (measurePerformance) stats.performance.connectionDerivation.push(connectionMs);
  assert.equal(geometry.length, visibleConnections.length);
  const visibleIdSet = new Set(composition.visibleEntityIds);
  const rowIds = new Set(dataset.accessibleRows.map((row) => row.id));
  for (const item of geometry) {
    if (!visibleIdSet.has(item.connection.sourceEntityId) || !visibleIdSet.has(item.connection.targetEntityId)) {
      stats.danglingConnectionCount += 1;
    }
    if (!rowIds.has(item.connection.accessibleRowId)) stats.accessibleRowMismatchCount += 1;
    if (!connectorPathPattern.test(item.path) || /NaN|Infinity/u.test(item.path)) {
      stats.invalidConnectorCount += 1;
    }
    assertFinite(item.labelX, item.labelY);
  }
  assert.equal(stats.danglingConnectionCount, 0, "dangling visible connection");
  assert.equal(stats.accessibleRowMismatchCount, 0, "missing accessible row");
  assert.equal(stats.invalidConnectorCount, 0, "invalid connector geometry");
  assert.equal(new Set(visibleConnections.map((item) => item.accessibleRowId)).size, visibleConnections.length);
  const visibleAccessibleRowIds = new Set([
    `selected:${dataset.selectedRecord.stableId}`,
    ...visibleConnections.map((connection) => connection.accessibleRowId),
  ]);
  const visibleAccessibleRows = dataset.accessibleRows.filter((row) => visibleAccessibleRowIds.has(row.id));
  assert.equal(visibleAccessibleRows.length, visibleConnections.length + 1);

  const exportStarted = performance.now();
  let snapshot;
  try {
    snapshot = exportPng.prepareContextCanvasExportSvg(dataset, composition);
  } catch (error) {
    stats.exportPreparationFailureCount += 1;
    throw error;
  }
  const exportMs = performance.now() - exportStarted;
  if (measurePerformance) stats.performance.exportPreparation.push(exportMs);
  assert.match(snapshot.svg, /^<svg /u);
  assert.doesNotMatch(snapshot.svg, /NaN|Infinity/u);
  assert.doesNotMatch(snapshot.svg, uuidPattern);
  assert.doesNotMatch(
    snapshot.svg,
    /<(?:button|nav|aside)\b|\b(?:data|class|id)=["'][^"']*(?:toolbar|sidebar|inspector|palette|focus-ring|hover)[^"']*["']|\baria-selected=/iu,
  );
  assert.doesNotMatch(snapshot.svg, /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f]/u);
  assertFinite(snapshot.width, snapshot.height, snapshot.contentBounds.x, snapshot.contentBounds.y,
    snapshot.contentBounds.width, snapshot.contentBounds.height);
  assert.ok(snapshot.width > 0 && snapshot.height > 0);
  assert.equal((snapshot.svg.match(/data-entity-kind=/gu) ?? []).length, composition.visibleEntityIds.length);
  assert.equal((snapshot.svg.match(/data-connection-kind=/gu) ?? []).length, visibleConnections.length);
  for (const node of connections.visibleContextCanvasNodes(dataset, composition)) {
    const full = displayLabel.contextCanvasFullLabel(node.ref);
    const escapedTitle = displayLabel.escapeContextCanvasXml(`${full} (${node.ref.kind})`);
    assert.equal(snapshot.svg.includes(`<title>${escapedTitle}</title>`), true);
  }
  for (const folder of candidate.folders) assert.equal(snapshot.svg.includes(folder.folderToken), false);
  const filename = exportPng.buildContextCanvasPngFilename(dataset.selectedRecord.stableId, fixedExportInstant);
  const filenameSafe = /^[a-z0-9_-]+\.png$/iu.test(filename)
    && !/[/\\.?]/u.test(filename.slice(0, -4))
    && !uuidPattern.test(filename);
  if (!filenameSafe) stats.unsafeFilenameCount += 1;
  assert.equal(filenameSafe, true);
  assert.match(filename, /^[a-z0-9_-]+\.png$/iu);
  assert.doesNotMatch(filename.slice(0, -4), /[/\\.?]/u);
  assert.doesNotMatch(filename, uuidPattern);
  stats.exportTemplateCases += 1;
  if (templateId === "full-context") stats.payload.exportSvgBytes.push(Buffer.byteLength(snapshot.svg, "utf8"));

  const persistenceStarted = performance.now();
  const initializingState = stateModule.createInitializingContextCanvasState(dataset);
  const readyState = reducerModule.contextCanvasReducer(initializingState, {
    type: "INITIALIZE",
    composition,
    viewport: fitted,
  });
  let serialized;
  let restored;
  try {
    serialized = persistence.serializeContextCanvasWorkspace(readyState);
    restored = persistence.deserializeContextCanvasWorkspace(serialized, dataset);
  } catch (error) {
    stats.serializationFailureCount += 1;
    throw error;
  }
  const persistenceMs = performance.now() - persistenceStarted;
  if (measurePerformance) stats.performance.persistenceRoundtrip.push(persistenceMs);
  const persistenceMatches = Boolean(restored)
    && deepEqualJson(restored.composition, composition)
    && deepEqualJson(restored.viewport, fitted)
    && persistence.serializeContextCanvasWorkspace(readyState) === serialized;
  if (!persistenceMatches) stats.persistenceRoundtripMismatchCount += 1;
  assert.equal(persistenceMatches, true);
  assert.ok(restored);
  assert.deepEqual(restored.composition, composition);
  assert.deepEqual(restored.viewport, fitted);
  assert.equal(persistence.serializeContextCanvasWorkspace(readyState), serialized);
  validatePersistencePayload(JSON.parse(serialized));
  assert.doesNotMatch(serialized, uuidPattern);
  assert.equal(collectKeys(JSON.parse(serialized)).has("label"), false);
  for (const folder of candidate.folders) assert.equal(serialized.includes(folder.folderToken), false);

  updateHash(hashers.templateSelection, [templateId, composition.visibleEntityIds]);
  updateHash(hashers.layoutGeometry, [templateId, arranged, geometry.map((item) => ({
    id: item.connection.id,
    path: item.path,
    labelX: item.labelX,
    labelY: item.labelY,
  }))]);
  updateHash(hashers.exportPreparation, [
    templateId,
    snapshot.width,
    snapshot.height,
    snapshot.contentBounds,
    sha256(snapshot.svg),
    filename,
  ]);

  if (measurePerformance) {
    stats.performance.canvasPureTotal.push(
      initializeMs + arrangeMs + boundsFitMs + connectionMs + exportMs + persistenceMs,
    );
  }
  assert.ok(performance.now() >= pureStarted);
}

function observeLabel(stats, category, value, identity) {
  const before = value;
  const codePointLength = Array.from(value).length;
  const fitted = displayLabel.fitContextCanvasDisplayLabel(value);
  const categoryStats = stats.labels[category];
  categoryStats.lengths.push(codePointLength);
  categoryStats.count += 1;
  if (/[^\u0000-\u007f]/u.test(value)) categoryStats.nonAscii += 1;
  if (/\p{Script=Han}/u.test(value)) categoryStats.han += 1;
  if (/\p{M}/u.test(value.normalize("NFD"))) categoryStats.diacritic += 1;
  if (/[\r\n]/u.test(value)) categoryStats.multiline += 1;
  if (/\p{Cc}/u.test(value)) categoryStats.controlCharacter += 1;
  if (/[&<>"']/u.test(value)) categoryStats.xmlSpecial += 1;
  if (fitted.truncated) categoryStats.truncationRequired += 1;

  const empty = value.length === 0;
  const whitespaceOnly = value.length > 0 && !value.trim();
  const loneSurrogate = hasLoneSurrogate(value);
  const unexpectedNewline = /[\r\n]/u.test(value);
  const extremeLength = codePointLength > 4_096;
  const invalidUnicode = loneSurrogate;
  if (empty) categoryStats.empty += 1;
  if (whitespaceOnly) categoryStats.whitespaceOnly += 1;
  if (loneSurrogate) categoryStats.loneSurrogate += 1;
  if (invalidUnicode) categoryStats.invalidUnicode += 1;
  if (unexpectedNewline) categoryStats.unexpectedNewline += 1;
  if (extremeLength) categoryStats.extremeLength += 1;
  if (!fitted.displayText.trim()) categoryStats.emptyDisplay += 1;
  let invalid = false;
  if (empty || whitespaceOnly || invalidUnicode || /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/u.test(value)) invalid = true;
  if (unexpectedNewline || extremeLength) invalid = true;
  if (invalid) categoryStats.invalid += 1;
  assert.equal(invalid, false, "invalid or malformed source label");
  assert.equal(fitted.fullText, value);
  assert.equal(value, before, "display fitting mutated source label");
  assert.equal(hasLoneSurrogate(fitted.displayText), false);
  assert.equal(
    displayLabel.fitContextCanvasDisplayLabel(fitted.displayText).truncated,
    false,
  );

  const identityMap = stats.identityLabels[category];
  const prior = identityMap.get(identity);
  if (prior !== undefined && prior !== value) stats.sameIdentityConflictingLabelCount += 1;
  else identityMap.set(identity, value);
  const identitySet = stats.labelIdentities[category].get(value) ?? new Set();
  identitySet.add(identity);
  stats.labelIdentities[category].set(value, identitySet);
}

function finalizeLabelIdentityStats(stats) {
  for (const [category, labelMap] of Object.entries(stats.labelIdentities)) {
    for (const identities of labelMap.values()) {
      if (identities.size > 1) {
        stats.sameLabelDifferentIdentityCount += 1;
        stats.sameLabelDifferentIdentityByClass[category] += 1;
      }
    }
  }
}

function validatePersistencePayload(payload) {
  assert.deepEqual(Object.keys(payload).sort(compareText), [
    "positions",
    "schemaVersion",
    "templateCatalogVersion",
    "templateId",
    "templateVersion",
    "viewport",
    "visibleEntityIds",
  ]);
  assert.deepEqual(Object.keys(payload.positions).sort(compareText), [...payload.visibleEntityIds].sort(compareText));
  assert.equal(payload.visibleEntityIds.every((id) => typeof id === "string" && id.startsWith("entity:")), true);
  for (const position of Object.values(payload.positions)) {
    assert.deepEqual(Object.keys(position).sort(compareText), ["x", "y"]);
    assertFinite(position.x, position.y);
  }
  const forbiddenKeys = new Set([
    "assignment",
    "assignmentType",
    "availability",
    "container",
    "controlledAssignments",
    "curatedMemberships",
    "evidenceRefs",
    "folderToken",
    "label",
    "member",
    "membership",
    "membershipType",
    "semanticEdge",
    "semanticEdges",
    "subject",
    "value",
    "warnings",
  ]);
  assert.deepEqual([...collectKeys(payload)].filter((key) => forbiddenKeys.has(key)), []);
}

function validateLookupBoundary(index) {
  const unavailable = sourceIndex.lookupRealContextValidationDataset(
    "SURF-CONTEXT-VALIDATION-UNKNOWN",
    { allowWithoutGate: true },
  );
  assert.deepEqual(unavailable, {
    status: "error",
    code: "RECORD_NOT_AVAILABLE",
    message: "The requested record is not available in this validation workspace.",
  });
  let heldExposed = 0;
  let heldLookups = 0;
  for (const heldId of index.heldStableIds) {
    const result = sourceIndex.lookupRealContextValidationDataset(heldId, { allowWithoutGate: true });
    heldLookups += 1;
    if (result.status === "ready") heldExposed += 1;
    assert.deepEqual(result, unavailable);
    assert.equal(JSON.stringify(result).includes(heldId), false);
  }
  assert.equal(heldLookups, 7_928);
  assert.equal(heldExposed, 0);
  assert.deepEqual(
    sourceIndex.lookupRealContextValidationDataset("not a stable id", { allowWithoutGate: true }),
    {
      status: "error",
      code: "INVALID_RECORD_ID",
      message: "The record parameter is not a valid public stable ID.",
    },
  );

  const warmLookupTimings = [];
  let lookupSink = 0;
  for (let indexPosition = 0; indexPosition < 50; indexPosition += 1) {
    const result = sourceIndex.lookupRealContextValidationDataset(index.eligibleStableIds[0], {
      allowWithoutGate: true,
    });
    lookupSink += result.status === "ready" ? result.projection.dataset.items.length : 0;
  }
  for (let indexPosition = 0; indexPosition < 500; indexPosition += 1) {
    const started = performance.now();
    const result = sourceIndex.lookupRealContextValidationDataset(index.eligibleStableIds[0], {
      allowWithoutGate: true,
    });
    warmLookupTimings.push(performance.now() - started);
    lookupSink += result.status === "ready" ? result.projection.dataset.items.length : 0;
  }
  assert.ok(lookupSink > 0);
  return Object.freeze({
    held_lookups: heldLookups,
    held_exposed: heldExposed,
    unknown_lookup_code: unavailable.code,
    lookup_indistinguishable: true,
    malformed_lookup_code: "INVALID_RECORD_ID",
    warmLookupPerformance: distribution(warmLookupTimings),
  });
}

function validateRecordSwitchAndPersistence(index) {
  const projectionA = realProjector.projectRealContextValidationDataset(index.candidates[0]);
  const projectionB = realProjector.projectRealContextValidationDataset(index.candidates[1]);
  const datasetA = projectionA.dataset;
  const datasetB = projectionB.dataset;
  const compositionA = templates.initializeContextCanvasTemplate(datasetA, "full-context");
  const compositionB = templates.initializeContextCanvasTemplate(datasetB, "full-context");
  let stateA = reducerModule.contextCanvasReducer(
    stateModule.createInitializingContextCanvasState(datasetA),
    { type: "INITIALIZE", composition: compositionA, viewport: { x: 7, y: 11, zoom: 1.2 } },
  );
  stateA = reducerModule.contextCanvasReducer(stateA, {
    type: "SELECT",
    selection: { kind: "node", id: stateA.rootEntityId },
  });
  const paletteEntity = stateA.allowedEntityIds.find((id) => id !== stateA.rootEntityId);
  assert.ok(paletteEntity);
  stateA = reducerModule.contextCanvasReducer(stateA, {
    type: "BEGIN_PALETTE_DRAG",
    entityId: paletteEntity,
    pointerId: 31,
  });
  assert.equal(stateA.interaction.mode, "PALETTE_DRAGGING");

  const stateB = reducerModule.contextCanvasReducer(
    stateModule.createInitializingContextCanvasState(datasetB),
    { type: "INITIALIZE", composition: compositionB },
  );
  assert.equal(stateB.selection, null);
  assert.equal(stateB.interaction.mode, "READY");
  assert.equal(stateB.phase, "READY");
  assert.equal(stateB.allowedEntityIds.every((id) => compositionB.visibleEntityIds.includes(id)), true);
  assert.equal(stateB.allowedEntityIds.includes(stateA.rootEntityId), false);

  const memory = new Map();
  const storage = {
    getItem: (key) => memory.get(key) ?? null,
    setItem: (key, value) => memory.set(key, value),
    removeItem: (key) => memory.delete(key),
  };
  const cleanStateA = reducerModule.contextCanvasReducer(
    stateModule.createInitializingContextCanvasState(datasetA),
    { type: "INITIALIZE", composition: compositionA, viewport: { x: 19, y: -23, zoom: 1.25 } },
  );
  assert.equal(persistence.saveContextCanvasWorkspace(datasetA, cleanStateA, storage), true);
  assert.ok(persistence.loadContextCanvasWorkspace(datasetA, storage));
  assert.equal(persistence.loadContextCanvasWorkspace(datasetB, storage), null);
  assert.notEqual(
    persistence.contextCanvasPersistenceKey(datasetA),
    persistence.contextCanvasPersistenceKey(datasetB),
  );

  const alternateReleaseDataset = Object.freeze({
    ...datasetA,
    release: Object.freeze({
      ...datasetA.release,
      manifestSha256: "f".repeat(64),
    }),
  });
  assert.notEqual(
    persistence.contextCanvasPersistenceKey(datasetA),
    persistence.contextCanvasPersistenceKey(alternateReleaseDataset),
  );
  assert.equal(persistence.loadContextCanvasWorkspace(alternateReleaseDataset, storage), null);

  const serialized = persistence.serializeContextCanvasWorkspace(cleanStateA);
  const payload = JSON.parse(serialized);
  assert.equal(persistence.deserializeContextCanvasWorkspace("not-json", datasetA), null);
  assert.equal(persistence.deserializeContextCanvasWorkspace(JSON.stringify({
    ...payload,
    schemaVersion: payload.schemaVersion + 1,
  }), datasetA), null);
  assert.equal(persistence.deserializeContextCanvasWorkspace(JSON.stringify({
    ...payload,
    templateCatalogVersion: payload.templateCatalogVersion + 1,
  }), datasetA), null);
  assert.equal(persistence.deserializeContextCanvasWorkspace(JSON.stringify({
    ...payload,
    templateVersion: payload.templateVersion + 1,
  }), datasetA), null);

  return Object.freeze({
    corrupt_payload_ignored: true,
    different_record_isolated: true,
    different_release_isolated: true,
    record_switch_state_leak_count: 0,
    schema_version_mismatch_ignored: true,
    template_catalog_mismatch_ignored: true,
    template_version_mismatch_ignored: true,
  });
}

function validateProductionDefault(index) {
  const envName = sourceIndex.TRACE_CONTEXT_REALDATA_ENV_GATE;
  const hadValue = Object.hasOwn(process.env, envName);
  const priorValue = process.env[envName];
  try {
    delete process.env[envName];
    assert.equal(sourceIndex.realContextValidationEnabled(), false);
    assert.deepEqual(sourceIndex.lookupRealContextValidationDataset("not a stable id"), {
      status: "error",
      code: "INVALID_RECORD_ID",
      message: "The record parameter is not a valid public stable ID.",
    });
    const missingGate = sourceIndex.lookupRealContextValidationDataset(index.eligibleStableIds[0]);
    assert.deepEqual(missingGate, {
      status: "error",
      code: "VALIDATION_DATA_NOT_GENERATED",
      message: "Real v49 Context validation is disabled. Set the local validation gate to enable it.",
    });
    assert.equal(JSON.stringify(missingGate).includes(index.eligibleStableIds[0]), false);
    process.env[envName] = "0";
    assert.equal(sourceIndex.realContextValidationEnabled(), false);
    assert.equal(sourceIndex.lookupRealContextValidationDataset(index.eligibleStableIds[0]).status, "error");
  } finally {
    if (hadValue) process.env[envName] = priorValue;
    else delete process.env[envName];
  }
  return Object.freeze({
    env_gate: envName,
    explicit_value_required: "1",
    production_default_exposure: false,
  });
}

async function validateClientBundleBoundary(heldStableIds) {
  const srcRoot = join(frontendRoot, "src");
  const sourceFiles = await walkFiles(srcRoot, new Set([".js", ".jsx", ".mjs", ".ts", ".tsx"]));
  const sources = new Map(await Promise.all(sourceFiles.map(async (path) => [path, await readFile(path, "utf8")])));
  const clientEntries = [...sources].filter(([, source]) => /^\s*["']use client["'];/u.test(source)).map(([path]) => path);
  const reachable = new Set(clientEntries);
  const queue = [...clientEntries];
  while (queue.length > 0) {
    const path = queue.shift();
    const source = sources.get(path) ?? "";
    for (const specifier of importSpecifiers(source)) {
      const target = resolveSourceImport(path, specifier, sources);
      if (target && !reachable.has(target)) {
        reachable.add(target);
        queue.push(target);
      }
    }
  }

  const forbiddenSourceMarkers = [
    /source-index\.server/u,
    /project\.server/u,
    /node:sqlite/u,
    /prefreeze_candidate_v48\.sqlite/u,
    /18_SURFACE_ROW_LEDGER/u,
    /TRACE_CONTEXT_EXPECTED_HELD_COUNT/u,
    /heldStableIds/u,
    /folderToken/u,
  ];
  let sourceForbiddenMatches = 0;
  for (const path of reachable) {
    const source = sources.get(path) ?? "";
    for (const marker of forbiddenSourceMarkers) {
      if (marker.test(source) || marker.test(relative(srcRoot, path))) sourceForbiddenMatches += 1;
    }
  }
  assert.equal(sourceForbiddenMatches, 0, "server-only corpus source is reachable from a client entry");

  const nextRoot = join(frontendRoot, ".next");
  let bundleStatus = "NOT_PRESENT";
  let bundleFilesScanned = 0;
  let bundleForbiddenMatches = 0;
  let routeBundleFilesScanned = 0;
  if (existsSync(nextRoot)) {
    const bundleFiles = await walkFiles(join(nextRoot, "static"), new Set([".js", ".json", ".txt"]));
    if (bundleFiles.length > 0) {
      bundleStatus = "PASS";
      for (const path of bundleFiles) {
        const source = await readFile(path, "utf8");
        bundleFilesScanned += 1;
        for (const marker of forbiddenSourceMarkers) {
          if (marker.test(source)) bundleForbiddenMatches += 1;
        }
      }

      // Existing unrelated archive routes may legitimately contain legacy/static
      // identifiers. Held-ID enumeration is therefore scoped to the exact Context
      // Canvas client chunk closure, while corpus-source markers are guarded across
      // every emitted static chunk above.
      const manifestPath = join(nextRoot, "app-build-manifest.json");
      if (existsSync(manifestPath)) {
        const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
        const routeFiles = manifest.pages?.["/trace/context-canvas/page"] ?? [];
        for (const entry of routeFiles.filter((value) => extname(value) === ".js")) {
          const path = join(nextRoot, entry);
          if (!existsSync(path)) continue;
          const source = await readFile(path, "utf8");
          routeBundleFilesScanned += 1;
          for (const match of source.matchAll(publicStableIdPattern)) {
            if (heldStableIds.has(match[0])) bundleForbiddenMatches += 1;
          }
        }
      }
    }
  }
  assert.equal(bundleForbiddenMatches, 0, "real validation corpus marker found in client bundle");
  return Object.freeze({
    bundle_files_scanned: bundleFilesScanned,
    bundle_forbidden_match_count: bundleForbiddenMatches,
    bundle_status: bundleStatus,
    client_entry_count: clientEntries.length,
    reachable_client_module_count: reachable.size,
    route_bundle_files_scanned: routeBundleFilesScanned,
    source_forbidden_match_count: sourceForbiddenMatches,
    source_guard_status: "PASS",
  });
}

function validateFrozenExpectations(index, summary) {
  assert.equal(summary.objects_tested, 7_995);
  assert.equal(summary.failed_object_count, 0);
  assert.equal(summary.template_cases, 31_980);
  assert.equal(summary.export_template_cases, 31_980);
  assert.equal(summary.export_svg_preparation_object_count, 7_995);
  assert.equal(summary.controlled_assignment_object_coverage, 7_995);
  assert.equal(summary.curated_membership_object_coverage, 7_995);
  assert.equal(summary.real_semantic_edge_count, 0);
  assert.deepEqual(summary.context_associations, {
    max: 9,
    min: 5,
    p50: 5,
    p95: 5,
    p99: 7,
  });
  assert.equal(summary.label_shape.all_labels.count, 48_203);
  assert.equal(
    summary.label_shape.all_labels.count,
    summary.label_shape.object_title.count
      + summary.label_shape.controlled_assignment.count
      + summary.label_shape.curated_membership.count,
  );
  assert.equal(
    summary.same_label_different_identity_count,
    Object.values(summary.same_label_different_identity_by_label_class)
      .reduce((count, value) => count + value, 0),
  );
  assert.equal(summary.persistence_key_count, index.publicCount);
  assert.equal(displayLabel.CONTEXT_CANVAS_DISPLAY_LABEL_POLICY_VERSION, 1);
}

function validateAllBugCounters(summary) {
  const zeroKeys = [
    "accessible_row_mismatch_count",
    "auto_layout_collision_count",
    "connection_id_collision_count",
    "dangling_connection_count",
    "duplicate_accessible_row_count",
    "entity_id_collision_count",
    "export_preparation_failure_count",
    "invalid_connector_count",
    "node_outside_bounds_count",
    "nonfinite_x_count",
    "nonfinite_y_count",
    "nonfinite_zoom_count",
    "persistence_roundtrip_mismatch_count",
    "same_identity_conflicting_label_count",
    "serialization_failure_count",
    "unsafe_export_filename_count",
  ];
  for (const key of zeroKeys) assert.equal(summary[key], 0, `${key} must be zero`);
  for (const labelSummary of Object.values(summary.label_shape)) {
    assert.equal(labelSummary.invalid, 0, "invalid label count must be zero");
    assert.equal(labelSummary.empty_count, 0, "empty label count must be zero");
  }
}

function buildBugClassTotals(summary, lookupSummary) {
  const labels = summary.label_shape.all_labels;
  return Object.freeze({
    control_character_label_count: labels.control_character_label_count,
    dangling_endpoint_count: summary.dangling_connection_count,
    duplicate_accessible_row_count: summary.duplicate_accessible_row_count,
    duplicate_connection_id_count: summary.connection_id_collision_count,
    duplicate_entity_id_count: summary.entity_id_collision_count,
    empty_display_label_count: labels.empty_display_count,
    empty_source_label_count: labels.empty_count,
    export_preparation_failure_count: summary.export_preparation_failure_count,
    extreme_label_length_count: labels.extreme_length_count,
    held_object_exposure_count: lookupSummary.held_exposed,
    internal_uuid_exposure_count: summary.internal_uuid_exposure_count,
    invalid_connector_count: summary.invalid_connector_count,
    invalid_unicode_sequence_count: labels.invalid_unicode_count,
    lone_surrogate_count: labels.lone_surrogate_count,
    missing_accessible_row_count: summary.accessible_row_mismatch_count,
    node_outside_bounds_count: summary.node_outside_bounds_count,
    node_overlap_count: summary.auto_layout_collision_count,
    nonfinite_x_count: summary.nonfinite_x_count,
    nonfinite_y_count: summary.nonfinite_y_count,
    nonfinite_zoom_count: summary.nonfinite_zoom_count,
    persistence_roundtrip_mismatch_count: summary.persistence_roundtrip_mismatch_count,
    same_identity_conflicting_label_count: summary.same_identity_conflicting_label_count,
    same_label_different_identity_count: summary.same_label_different_identity_count,
    serialization_failure_count: summary.serialization_failure_count,
    truncation_required_label_count: labels.truncation_required_count,
    unexpected_newline_count: labels.unexpected_newline_count,
    unsafe_export_filename_count: summary.unsafe_export_filename_count,
    whitespace_only_label_count: labels.whitespace_only_count,
  });
}

function validateBugClassTotals(totals) {
  assert.equal(Object.keys(totals).length, 28);
  assert.equal(totals.control_character_label_count, 2);
  assert.equal(totals.truncation_required_label_count, 23_024);
  assert.equal(totals.same_label_different_identity_count, 155);
  for (const [name, count] of Object.entries(totals)) {
    assert.equal(Number.isSafeInteger(count) && count >= 0, true, `${name} must be a count`);
    if (![
      "control_character_label_count",
      "same_label_different_identity_count",
      "truncation_required_label_count",
    ].includes(name)) assert.equal(count, 0, `${name} must be zero`);
  }
}

function validatePerformance(performanceStats) {
  const summary = summarizePerformance(performanceStats);
  assert.equal(Number.isFinite(summary.dataset_derivation_ms.p95), true);
  assert.equal(Number.isFinite(summary.canvas_pure_total_ms.p95), true);
  assert.ok(
    summary.canvas_pure_total_ms.p95 < 5,
    `pure Canvas operation P95 ${summary.canvas_pure_total_ms.p95} ms exceeded 5 ms`,
  );
}

function buildInvariantResults(input) {
  const { deterministicSummary: summary } = input;
  const results = [
    ["CTX-REAL-INV-001", input.index.publicCount === 7_995 && summary.failed_object_count === 0, "Exactly 7,995 eligible records project."],
    ["CTX-REAL-INV-002", input.lookupSummary.held_exposed === 0, "No held record projects."],
    ["CTX-REAL-INV-003", input.lookupSummary.lookup_indistinguishable, "Held and unknown lookups are externally indistinguishable."],
    ["CTX-REAL-INV-004", summary.internal_uuid_exposure_count === 0, "No internal UUID enters Canvas data, persistence, or export."],
    ["CTX-REAL-INV-005", summary.non_proposed_candidate_count === 0, "No candidate is relabeled accepted."],
    ["CTX-REAL-INV-006", summary.real_semantic_edge_count === 0, "The real v49 semantic-edge collection remains empty."],
    ["CTX-REAL-INV-007", summary.undocumented_connection_category_count === 0, "Every connection maps to a documented validation source category."],
    ["CTX-REAL-INV-008", summary.visible_entity_outside_dataset_count === 0, "Every visible entity belongs to the selected dataset."],
    ["CTX-REAL-INV-009", input.persistenceSummary.record_switch_state_leak_count === 0, "Record switching retains no stale selection or interaction."],
    ["CTX-REAL-INV-010", input.persistenceSummary.different_record_isolated, "Persistence never crosses object identity."],
    ["CTX-REAL-INV-011", input.persistenceSummary.different_release_isolated, "Persistence never crosses release identity."],
    ["CTX-REAL-INV-012", input.sourceIndexShaA === input.sourceIndexShaB && deepEqualJson(input.passA.hashes, input.passB.hashes), "Same frozen source and mapping version are deterministic."],
    ["CTX-REAL-INV-013", summary.auto_layout_collision_count === 0, "Auto layout is collision-free for every object and template."],
    ["CTX-REAL-INV-014", summary.accessible_row_mismatch_count === 0 && summary.export_missing_full_label_count === 0, "Full labels remain accessible despite display truncation."],
    ["CTX-REAL-INV-015", summary.source_label_mutation_count === 0, "Display fitting never mutates source text."],
    ["CTX-REAL-INV-016", summary.export_preparation_failure_count === 0 && summary.export_svg_preparation_object_count === 7_995, "Export preparation succeeds for every public object."],
    ["CTX-REAL-INV-017", input.bundleSummary.source_forbidden_match_count === 0 && input.bundleSummary.bundle_forbidden_match_count === 0, "The real validation corpus is absent from client-reachable code and available bundles."],
    ["CTX-REAL-INV-018", input.productionSummary.production_default_exposure === false, "Production-default behavior does not expose real candidates."],
  ];
  return Object.freeze(results.map(([id, passed, description], index) => {
    assert.equal(id, `CTX-REAL-INV-${String(index + 1).padStart(3, "0")}`);
    assert.equal(passed, true, `${id} failed`);
    return Object.freeze({ id, description, status: "PASS" });
  }));
}

function createPassStats(measurePerformance) {
  const labelCategory = () => ({
    count: 0,
    controlCharacter: 0,
    diacritic: 0,
    empty: 0,
    emptyDisplay: 0,
    extremeLength: 0,
    han: 0,
    invalid: 0,
    invalidUnicode: 0,
    lengths: [],
    loneSurrogate: 0,
    multiline: 0,
    nonAscii: 0,
    truncationRequired: 0,
    unexpectedNewline: 0,
    whitespaceOnly: 0,
    xmlSpecial: 0,
  });
  return {
    accessibleRowMismatchCount: 0,
    autoLayoutCollisionCount: 0,
    connectionIdCollisionCount: 0,
    controlledCoverage: 0,
    curatedCoverage: 0,
    danglingConnectionCount: 0,
    duplicateAccessibleRowCount: 0,
    entityIdCollisionCount: 0,
    exportMissingFullLabelCount: 0,
    exportObjects: new Set(),
    exportPreparationFailureCount: 0,
    exportTemplateCases: 0,
    failedObjects: new Set(),
    identityLabels: {
      controlled_assignment: new Map(),
      curated_membership: new Map(),
      object_title: new Map(),
    },
    internalUuidExposureCount: 0,
    invalidConnectorCount: 0,
    nonfiniteXCount: 0,
    nonfiniteYCount: 0,
    nonfiniteZoomCount: 0,
    labelIdentities: {
      controlled_assignment: new Map(),
      curated_membership: new Map(),
      object_title: new Map(),
    },
    labels: {
      controlled_assignment: labelCategory(),
      curated_membership: labelCategory(),
      object_title: labelCategory(),
    },
    measurePerformance,
    nodeOutsideBoundsCount: 0,
    nonProposedCandidateCount: 0,
    objectsTested: 0,
    payload: {
      accessibleRowCount: [],
      connectionCount: [],
      datasetBytes: [],
      entityCount: [],
      exportSvgBytes: [],
    },
    performance: {
      accessibilityDerivation: [],
      autoArrange: [],
      boundsAndFit: [],
      canvasPureTotal: [],
      connectionDerivation: [],
      datasetDerivation: [],
      exportPreparation: [],
      persistenceRoundtrip: [],
      templateInitialization: [],
    },
    persistenceKeys: new Set(),
    persistenceRoundtripMismatchCount: 0,
    sameIdentityConflictingLabelCount: 0,
    sameLabelDifferentIdentityByClass: {
      controlled_assignment: 0,
      curated_membership: 0,
      object_title: 0,
    },
    sameLabelDifferentIdentityCount: 0,
    semanticEdgeCount: 0,
    sourceLabelMutationCount: 0,
    serializationFailureCount: 0,
    templateCases: 0,
    undocumentedConnectionCategoryCount: 0,
    unsafeFilenameCount: 0,
    visibleEntityOutsideDatasetCount: 0,
    workloads: [],
  };
}

function deterministicPassSummary(stats) {
  const allLabelStats = Object.freeze({
    count: Object.values(stats.labels).reduce((count, value) => count + value.count, 0),
    controlCharacter: Object.values(stats.labels).reduce(
      (count, value) => count + value.controlCharacter,
      0,
    ),
    diacritic: Object.values(stats.labels).reduce((count, value) => count + value.diacritic, 0),
    empty: Object.values(stats.labels).reduce((count, value) => count + value.empty, 0),
    emptyDisplay: Object.values(stats.labels).reduce(
      (count, value) => count + value.emptyDisplay,
      0,
    ),
    extremeLength: Object.values(stats.labels).reduce(
      (count, value) => count + value.extremeLength,
      0,
    ),
    han: Object.values(stats.labels).reduce((count, value) => count + value.han, 0),
    invalid: Object.values(stats.labels).reduce((count, value) => count + value.invalid, 0),
    invalidUnicode: Object.values(stats.labels).reduce(
      (count, value) => count + value.invalidUnicode,
      0,
    ),
    lengths: Object.values(stats.labels).flatMap((value) => value.lengths),
    loneSurrogate: Object.values(stats.labels).reduce(
      (count, value) => count + value.loneSurrogate,
      0,
    ),
    multiline: Object.values(stats.labels).reduce((count, value) => count + value.multiline, 0),
    nonAscii: Object.values(stats.labels).reduce((count, value) => count + value.nonAscii, 0),
    truncationRequired: Object.values(stats.labels).reduce(
      (count, value) => count + value.truncationRequired,
      0,
    ),
    unexpectedNewline: Object.values(stats.labels).reduce(
      (count, value) => count + value.unexpectedNewline,
      0,
    ),
    whitespaceOnly: Object.values(stats.labels).reduce(
      (count, value) => count + value.whitespaceOnly,
      0,
    ),
    xmlSpecial: Object.values(stats.labels).reduce((count, value) => count + value.xmlSpecial, 0),
  });
  const labelShape = Object.freeze(Object.fromEntries([
    ["all_labels", allLabelStats],
    ...Object.entries(stats.labels),
  ].map(([name, value]) => [name, summarizeLabelStats(value)])));
  return Object.freeze({
    accessible_row_mismatch_count: stats.accessibleRowMismatchCount,
    auto_layout_collision_count: stats.autoLayoutCollisionCount,
    connection_id_collision_count: stats.connectionIdCollisionCount,
    context_associations: Object.freeze({
      min: Math.min(...stats.workloads),
      p50: percentile(stats.workloads, 0.5),
      p95: percentile(stats.workloads, 0.95),
      p99: percentile(stats.workloads, 0.99),
      max: Math.max(...stats.workloads),
    }),
    controlled_assignment_object_coverage: stats.controlledCoverage,
    curated_membership_object_coverage: stats.curatedCoverage,
    dangling_connection_count: stats.danglingConnectionCount,
    duplicate_accessible_row_count: stats.duplicateAccessibleRowCount,
    entity_id_collision_count: stats.entityIdCollisionCount,
    export_missing_full_label_count: stats.exportMissingFullLabelCount,
    export_preparation_failure_count: stats.exportPreparationFailureCount,
    export_svg_preparation_object_count: stats.exportObjects.size,
    export_template_cases: stats.exportTemplateCases,
    failed_object_count: stats.failedObjects.size,
    internal_uuid_exposure_count: stats.internalUuidExposureCount,
    invalid_connector_count: stats.invalidConnectorCount,
    nonfinite_x_count: stats.nonfiniteXCount,
    nonfinite_y_count: stats.nonfiniteYCount,
    nonfinite_zoom_count: stats.nonfiniteZoomCount,
    label_shape: labelShape,
    node_outside_bounds_count: stats.nodeOutsideBoundsCount,
    non_proposed_candidate_count: stats.nonProposedCandidateCount,
    objects_tested: stats.objectsTested,
    payload_distribution: Object.freeze(Object.fromEntries(Object.entries(stats.payload).map(([name, values]) => [
      snakeCase(name),
      distribution(values),
    ]))),
    persistence_key_collision_count: stats.objectsTested - stats.persistenceKeys.size,
    persistence_key_count: stats.persistenceKeys.size,
    persistence_roundtrip_mismatch_count: stats.persistenceRoundtripMismatchCount,
    real_semantic_edge_count: stats.semanticEdgeCount,
    same_identity_conflicting_label_count: stats.sameIdentityConflictingLabelCount,
    same_label_different_identity_by_label_class: Object.freeze({
      ...stats.sameLabelDifferentIdentityByClass,
    }),
    same_label_different_identity_count: stats.sameLabelDifferentIdentityCount,
    source_label_mutation_count: stats.sourceLabelMutationCount,
    serialization_failure_count: stats.serializationFailureCount,
    template_cases: stats.templateCases,
    undocumented_connection_category_count: stats.undocumentedConnectionCategoryCount,
    unsafe_export_filename_count: stats.unsafeFilenameCount,
    visible_entity_outside_dataset_count: stats.visibleEntityOutsideDatasetCount,
    workload_histogram: histogram(stats.workloads),
  });
}

function summarizeLabelStats(value) {
  return Object.freeze({
    control_character_label_count: value.controlCharacter,
    count: value.count,
    diacritic_bearing_count: value.diacritic,
    empty_count: value.empty,
    empty_display_count: value.emptyDisplay,
    extreme_length_count: value.extremeLength,
    han_count: value.han,
    invalid: value.invalid,
    invalid_unicode_count: value.invalidUnicode,
    lone_surrogate_count: value.loneSurrogate,
    max: Math.max(...value.lengths),
    min: Math.min(...value.lengths),
    multiline_count: value.multiline,
    non_ascii_count: value.nonAscii,
    p50: percentile(value.lengths, 0.5),
    p90: percentile(value.lengths, 0.9),
    p95: percentile(value.lengths, 0.95),
    p99: percentile(value.lengths, 0.99),
    truncation_required_count: value.truncationRequired,
    unexpected_newline_count: value.unexpectedNewline,
    whitespace_only_count: value.whitespaceOnly,
    xml_special_count: value.xmlSpecial,
  });
}

function summarizePerformance(performanceStats) {
  return Object.freeze(Object.fromEntries(Object.entries(performanceStats).map(([name, values]) => [
    `${snakeCase(name)}_ms`,
    distribution(values),
  ])));
}

function buildEvidence(input) {
  const summary = input.deterministicSummary;
  const workloadRows = ["associations\tobject_count"];
  for (const [associations, count] of Object.entries(summary.workload_histogram)) {
    workloadRows.push(`${associations}\t${count}`);
  }

  const labelRows = [
    "label_class\tcount\tmin\tp50\tp90\tp95\tp99\tmax\tnon_ascii_count\than_count\tdiacritic_bearing_count\tmultiline_count\tcontrol_character_label_count\tempty_count\txml_special_count\ttruncation_required_count\tinvalid_count\tsame_label_different_identity_count",
  ];
  for (const category of ["all_labels", "object_title", "controlled_assignment", "curated_membership"]) {
    const value = summary.label_shape[category];
    labelRows.push([
      category,
      value.count,
      value.min,
      value.p50,
      value.p90,
      value.p95,
      value.p99,
      value.max,
      value.non_ascii_count,
      value.han_count,
      value.diacritic_bearing_count,
      value.multiline_count,
      value.control_character_label_count,
      value.empty_count,
      value.xml_special_count,
      value.truncation_required_count,
      value.invalid,
      category === "all_labels"
        ? summary.same_label_different_identity_count
        : summary.same_label_different_identity_by_label_class[category],
    ].join("\t"));
  }

  const payloadRows = ["metric\tpopulation\tp50\tp90\tp95\tp99\tmax"];
  for (const metric of [
    "entity_count",
    "connection_count",
    "dataset_bytes",
    "accessible_row_count",
    "export_svg_bytes",
  ]) {
    const value = summary.payload_distribution[metric];
    payloadRows.push([metric, value.count, value.p50, value.p90, value.p95, value.p99, value.max].join("\t"));
  }

  return Object.freeze({
    "all-object-validation-summary.json": stableJson({
      aggregate_sha256: input.aggregateSha256,
      bug_class_totals: input.bugClassTotals,
      canonical_object_count: 15_923,
      frozen_input_count: input.frozenInputBinding.frozen_input_count,
      held_object_count: 7_928,
      invariants: input.invariants,
      mapping_version: realTypes.TRACE_CONTEXT_REALDATA_MAPPING_VERSION,
      public_object_count: 7_995,
      source_manifest_sha256: input.frozenInputBinding.source_manifest_sha256,
      validation: summary,
      validation_mode: "real_v49_validation",
    }) + "\n",
    "context-workload-distribution.tsv": workloadRows.join("\n") + "\n",
    "label-shape-distribution.tsv": labelRows.join("\n") + "\n",
    "payload-distribution.tsv": payloadRows.join("\n") + "\n",
    "layout-validation-summary.json": stableJson({
      auto_layout_collision_count: summary.auto_layout_collision_count,
      invalid_connector_count: summary.invalid_connector_count,
      node_outside_bounds_count: summary.node_outside_bounds_count,
      nonfinite_position_count: 0,
      object_template_cases: summary.template_cases,
      templates: 4,
    }) + "\n",
    "export-validation-summary.json": stableJson({
      browser_png_conversion: "USER_REVIEW_PENDING",
      default_export_scale: canvasTypes.CONTEXT_CANVAS_DEFAULT_EXPORT_SCALE,
      export_preparation_failure_count: summary.export_preparation_failure_count,
      export_svg_preparation_object_count: summary.export_svg_preparation_object_count,
      export_template_cases: summary.export_template_cases,
      full_svg_emitted_in_evidence: false,
      internal_uuid_exposure_count: summary.internal_uuid_exposure_count,
    }) + "\n",
    "performance-summary.json": stableJson(input.performanceSummary) + "\n",
    "loader-performance-summary.json": stableJson(input.loaderPerformanceSummary) + "\n",
    "lookup-security-summary.json": stableJson({
      held_exposed: input.lookupSummary.held_exposed,
      held_lookups: input.lookupSummary.held_lookups,
      lookup_indistinguishable: input.lookupSummary.lookup_indistinguishable,
      malformed_lookup_code: input.lookupSummary.malformed_lookup_code,
      production_default_exposure: input.productionSummary.production_default_exposure,
      unknown_lookup_code: input.lookupSummary.unknown_lookup_code,
    }) + "\n",
    "client-bundle-guard.json": stableJson(input.bundleSummary) + "\n",
    "determinism-checksums.json": stableJson({
      aggregate_sha256: input.aggregateSha256,
      frozen_input_sha256: input.frozenInputBinding.frozen_input_sha256,
      full_projection_pass_a: input.passA.hashes,
      full_projection_pass_b: input.passB.hashes,
      real_context_checksum_match: true,
      real_context_rebuild_deterministic: true,
      rebuild_runs: 2,
      source_manifest_sha256: input.frozenInputBinding.source_manifest_sha256,
      source_index_pass_a_sha256: input.sourceIndexShaA,
      source_index_pass_b_sha256: input.sourceIndexShaB,
    }) + "\n",
    "all-object-failures.tsv": failureHeader,
  });
}

async function writeEvidence(directory, evidence) {
  await mkdir(directory, { recursive: true });
  const names = Object.keys(evidence).sort(compareText);
  const receiptHasher = createHash("sha256");
  for (const name of names) {
    const content = evidence[name];
    await writeFile(join(directory, name), content, "utf8");
    updateHash(receiptHasher, [name, sha256(content), Buffer.byteLength(content, "utf8")]);
  }
  return Object.freeze({ fileCount: names.length, sha256: receiptHasher.digest("hex") });
}

function assertEvidenceIsSanitized(evidence, heldStableIds) {
  assert.deepEqual(Object.keys(evidence).sort(compareText), [
    "all-object-failures.tsv",
    "all-object-validation-summary.json",
    "client-bundle-guard.json",
    "context-workload-distribution.tsv",
    "determinism-checksums.json",
    "export-validation-summary.json",
    "label-shape-distribution.tsv",
    "layout-validation-summary.json",
    "loader-performance-summary.json",
    "lookup-security-summary.json",
    "payload-distribution.tsv",
    "performance-summary.json",
  ]);
  for (const [name, content] of Object.entries(evidence)) {
    assert.doesNotMatch(content, uuidPattern, `${name} contains a UUID`);
    assert.doesNotMatch(content, /<svg\b/iu, `${name} contains SVG content`);
    assert.doesNotMatch(content, /\b(?:folderToken|candidateLabel|rawCandidateLabel)\b/u, `${name} contains a raw candidate field`);
    for (const match of content.matchAll(publicStableIdPattern)) {
      assert.equal(heldStableIds.has(match[0]), false, `${name} contains a held stable ID`);
    }
  }
  assert.equal(evidence["all-object-failures.tsv"], failureHeader);
}

function createSourceCandidates(path) {
  return [
    path,
    `${path}.js`,
    `${path}.jsx`,
    `${path}.mjs`,
    `${path}.ts`,
    `${path}.tsx`,
    join(path, "index.js"),
    join(path, "index.jsx"),
    join(path, "index.mjs"),
    join(path, "index.ts"),
    join(path, "index.tsx"),
  ];
}

function resolveSourceImport(importer, specifier, sources) {
  if (!specifier.startsWith(".") && !specifier.startsWith("@/")) return null;
  const base = specifier.startsWith("@/")
    ? join(frontendRoot, "src", specifier.slice(2))
    : resolve(dirname(importer), specifier);
  return createSourceCandidates(base).find((candidate) => sources.has(candidate)) ?? null;
}

async function walkFiles(root, extensions) {
  let entries;
  try {
    entries = await readdir(root, { withFileTypes: true });
  } catch (error) {
    if (error && typeof error === "object" && error.code === "ENOENT") return [];
    throw error;
  }
  const files = [];
  for (const entry of entries) {
    const path = join(root, entry.name);
    if (entry.isDirectory()) files.push(...await walkFiles(path, extensions));
    else if (extensions.has(extname(entry.name))) files.push(path);
  }
  return files.sort(compareText);
}

function importSpecifiers(source) {
  const values = [];
  const patterns = [
    /\bfrom\s*["']([^"']+)["']/gu,
    /\bimport\s*["']([^"']+)["']/gu,
    /\b(?:import|require)\s*\(\s*["']([^"']+)["']\s*\)/gu,
  ];
  for (const pattern of patterns) {
    for (const match of source.matchAll(pattern)) values.push(match[1]);
  }
  return values;
}

function rectanglesOverlap(left, right) {
  return left.x < right.right && left.right > right.x
    && left.y < right.bottom && left.bottom > right.y;
}

function hasLoneSurrogate(value) {
  for (let index = 0; index < value.length; index += 1) {
    const codeUnit = value.charCodeAt(index);
    if (codeUnit >= 0xd800 && codeUnit <= 0xdbff) {
      const next = value.charCodeAt(index + 1);
      if (!(next >= 0xdc00 && next <= 0xdfff)) return true;
      index += 1;
    } else if (codeUnit >= 0xdc00 && codeUnit <= 0xdfff) return true;
  }
  return false;
}

function collectKeys(value, found = new Set()) {
  if (!value || typeof value !== "object") return found;
  for (const [key, child] of Object.entries(value)) {
    found.add(key);
    collectKeys(child, found);
  }
  return found;
}

function distribution(values) {
  assert.ok(values.length > 0, "distribution requires observations");
  return Object.freeze({
    count: values.length,
    max: rounded(Math.max(...values)),
    p50: rounded(percentile(values, 0.5)),
    p90: rounded(percentile(values, 0.9)),
    p95: rounded(percentile(values, 0.95)),
    p99: rounded(percentile(values, 0.99)),
  });
}

function percentile(values, quantile) {
  assert.ok(values.length > 0, "percentile requires observations");
  const sorted = [...values].sort((left, right) => left - right);
  return sorted[Math.max(0, Math.ceil(sorted.length * quantile) - 1)];
}

function histogram(values) {
  const counts = new Map();
  for (const value of values) counts.set(value, (counts.get(value) ?? 0) + 1);
  return Object.freeze(Object.fromEntries([...counts].sort(([left], [right]) => left - right)));
}

function updateHash(hasher, value) {
  const serialized = typeof value === "string" ? value : JSON.stringify(value);
  hasher.update(String(Buffer.byteLength(serialized, "utf8")), "utf8");
  hasher.update(":", "utf8");
  hasher.update(serialized, "utf8");
  hasher.update("\n", "utf8");
}

function sha256(value) {
  const digest = createHash("sha256");
  if (typeof value === "string") digest.update(value, "utf8");
  else digest.update(value);
  return digest.digest("hex");
}

function rounded(value) {
  return Number(value.toFixed(3));
}

function formatMs(value) {
  return Number(value).toFixed(3);
}

function compareText(left, right) {
  return left < right ? -1 : left > right ? 1 : 0;
}

function snakeCase(value) {
  return value.replace(/([a-z0-9])([A-Z])/gu, "$1_$2").toLowerCase();
}

function deepEqualJson(left, right) {
  return stableJson(left) === stableJson(right);
}

function stableJson(value) {
  return JSON.stringify(canonicalize(value), null, 2);
}

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(Object.keys(value).sort(compareText).map((key) => [key, canonicalize(value[key])]));
}

function parseEvidenceDir(args) {
  let configured = null;
  for (let index = 0; index < args.length; index += 1) {
    const argument = args[index];
    if (argument === "--evidence-dir") {
      const value = args[index + 1];
      if (!value || value.startsWith("--")) throw new Error("--evidence-dir requires a path");
      configured = value;
      index += 1;
    } else if (argument.startsWith("--evidence-dir=")) {
      configured = argument.slice("--evidence-dir=".length);
      if (!configured) throw new Error("--evidence-dir requires a path");
    } else throw new Error(`unknown verifier argument: ${argument}`);
  }
  if (!configured) return defaultEvidenceDir;
  return isAbsolute(configured) ? resolve(configured) : resolve(repositoryRoot, configured);
}

function recordFailure(passName, objectIndex, templateId, bugClass, error) {
  failureRows.push([
    passName,
    String(objectIndex + 1),
    templateId,
    bugClass,
    sanitizeFailureMessage(error),
  ]);
}

function sanitizeFailureMessage(error) {
  const message = error instanceof Error ? error.message : String(error);
  return message
    .replace(/<svg\b[\s\S]*/iu, "<svg-withheld>")
    .replace(uuidPattern, "<uuid-withheld>")
    .replace(publicStableIdPattern, "<stable-id-withheld>")
    .replace(/ctxv49:[a-z_]+:[0-9a-f]+/giu, "<validation-id-withheld>")
    .replace(/[\t\r\n]+/gu, " ")
    .slice(0, 240) || "validation failed";
}

function tsvRow(values) {
  return values.map((value) => String(value).replace(/[\t\r\n]+/gu, " ")).join("\t");
}

function assertFinite(...values) {
  assert.equal(values.every(Number.isFinite), true, "non-finite Canvas geometry");
}
