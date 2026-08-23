import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { createReadStream } from "node:fs";
import {
  mkdir,
  readFile,
  readdir,
  stat,
  writeFile,
} from "node:fs/promises";
import { createRequire } from "node:module";
import {
  dirname,
  extname,
  isAbsolute,
  join,
  relative,
  resolve,
} from "node:path";
import { performance } from "node:perf_hooks";
import { fileURLToPath } from "node:url";
import createJiti from "jiti";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(here, "..");
const repositoryRoot = resolve(frontendRoot, "..");
const generatedRoot = join(frontendRoot, "generated/trace-context-v1");
const contextRoot = join(frontendRoot, "src/features/trace-v49/context");
const canvasRoot = join(contextRoot, "canvas");
const defaultEvidenceDir = join(
  repositoryRoot,
  "docs/audits/v49-context-governance-closure/raw",
);
const frozenDatabasePath = join(repositoryRoot, "data/prefreeze_candidate_v48.sqlite");
const eligibilityLedgerPath = join(
  repositoryRoot,
  "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv",
);
const roundTwoSummaryPath = join(
  repositoryRoot,
  "docs/audits/v49-context-canvas-realdata-round2/raw/all-object-validation-summary.json",
);
const roundTwoLoaderPath = join(
  repositoryRoot,
  "docs/audits/v49-context-canvas-realdata-round2/raw/loader-performance-summary.json",
);
const fixedExportInstant = new Date("2026-08-23T00:00:00.000Z");
const viewportSize = Object.freeze({ width: 1_280, height: 760 });

const PUBLIC_OBJECT_COUNT = 7_995;
const HELD_OBJECT_COUNT = 7_928;
const TERM_COUNT = 25;
const REPRESENTATION_COUNT = 16_106;
const REGION_TERM_COUNT = 93;
const REGION_ROW_COUNT = 7_996;
const POLICY_VERSION = "context-governance-v1";
const PROJECTION_ID = "trace-context-v1";
const ID_POLICY_VERSION = "trace-context-public-id-v1";
const PROVENANCE_NAMESPACE = "trace-context-provenance-v1";
const MAPPING_VERSION = "trace-context-governance-mapping-v1";
const SOURCE_RELEASE = Object.freeze({
  id: "v49-api-contract-fresh-c",
  manifestSha256: "4addfdb3cb9314587908096572242b9d63e9cef9e6e1be68c0c646491a43a90a",
});
const SOURCE_RELEASE_FOR_LOOKUP = Object.freeze({
  researchReleaseId: SOURCE_RELEASE.id,
  researchManifestSha256: SOURCE_RELEASE.manifestSha256,
});
const EXPECTED_KIND = Object.freeze({
  medium: Object.freeze({
    code: "CTX-MEDIUM",
    connectionLabel: "classified as",
    objectCount: 7_995,
    prefix: "MEDIUM",
    representationCount: 7_995,
    sourceKind: "medium",
    termCount: 10,
  }),
  theme: Object.freeze({
    code: "CTX-THEME",
    connectionLabel: "themed as",
    objectCount: 7_995,
    prefix: "THEME",
    representationCount: 7_996,
    sourceKind: "theme",
    termCount: 8,
  }),
  movement_context: Object.freeze({
    code: "CTX-MOVEMENT",
    connectionLabel: "curated within",
    objectCount: 110,
    prefix: "MOVEMENT",
    representationCount: 115,
    sourceKind: "movement",
    termCount: 7,
  }),
});

const PUBLIC_ID_PATTERN = /^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$/u;
const PUBLIC_ID_IN_TEXT_PATTERN = /\bSURF-[A-Z0-9]+(?:-[A-Z0-9]+)*\b/iu;
const TERM_ID_PATTERN = /^CTX:(?:MEDIUM|THEME|MOVEMENT):[0-9a-f]{64}$/u;
const REPRESENTATION_ID_PATTERN = /^CTXA:[0-9a-f]{64}$/u;
const PROVENANCE_ID_PATTERN = /^CTXP:[0-9a-f]{64}$/u;
const HANDOFF_ID_PATTERN = /^SPTREG:[0-9a-f]{64}$/u;
const SHA256_PATTERN = /^[0-9a-f]{64}$/u;
const UUID_PATTERN = /\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b/iu;
const VALIDATION_ID_PATTERN = /ctxv49:/iu;
const RAW_FOLDER_ID_PATTERN = /\bFOL-(?:MEDIUM|THEME|MOVEMENT|REGION)-[A-Z0-9-]+\b/iu;
const URL_PATTERN = /(?:https?:\/\/|www\.)/iu;
const CONNECTOR_PATH_PATTERN = /^M -?\d+(?:\.\d+)? -?\d+(?:\.\d+)? H -?\d+(?:\.\d+)? V -?\d+(?:\.\d+)? H -?\d+(?:\.\d+)?$/u;
const FORBIDDEN_DTO_KEYS = new Set([
  "curatedMemberships",
  "folderId",
  "folderToken",
  "href",
  "internalId",
  "internalUuid",
  "memberships",
  "rawMemberships",
  "semanticEdges",
  "sourceUrl",
  "url",
]);
const evidenceFailureHeader = "pass\tobject_ordinal\tbug_class\tmessage\n";
const args = parseArguments(process.argv.slice(2));
const failureRows = [];

class GovernanceValidationError extends Error {
  constructor(code, message) {
    super(message);
    this.name = "GovernanceValidationError";
    this.code = code;
  }
}

const jiti = createJiti(import.meta.url, {
  alias: {
    "@": join(frontendRoot, "src"),
    "server-only": join(here, "server-only-stub.mjs"),
  },
});

try {
  await main();
} catch (error) {
  failureRows.push(Object.freeze({
    bugClass: error instanceof GovernanceValidationError ? error.code : "verifier_failure",
    message: sanitizeFailureMessage(error),
    ordinal: 0,
    pass: "global",
  }));
  await writeFailureEvidence(args.evidenceDir, failureRows);
  console.error(`CONTEXT_GOVERNANCE_V1=FAIL ERROR=${sanitizeFailureMessage(error)}`);
  process.exitCode = 1;
}

async function main() {
  const smallArtifacts = await loadSmallArtifacts();
  const ledger = parseEligibilityLedger(await readFile(eligibilityLedgerPath, "utf8"));
  const frozenSource = await validateFrozenSourceAndBuildRegisters(
    ledger,
    smallArtifacts.terms,
    smallArtifacts.manifest,
  );
  const artifactSummary = await validateArtifacts(smallArtifacts, frozenSource);
  const generatorSummary = runDeterministicGeneratorCheck(smallArtifacts.manifest);
  const clientBoundary = await validateClientBoundary(args.requireBuild);
  const componentContract = await validateComponentContracts();
  const historicalBaseline = await loadHistoricalBaseline();

  const canvasAdapter = await jiti.import(join(contextRoot, "governed/canvas.ts"));
  const templates = await jiti.import(join(canvasRoot, "templates.ts"));
  const layout = await jiti.import(join(canvasRoot, "layout.ts"));
  const connections = await jiti.import(join(canvasRoot, "connections.ts"));
  const model = await jiti.import(join(canvasRoot, "model.ts"));
  const state = await jiti.import(join(canvasRoot, "state.ts"));
  const exportPng = await jiti.import(join(canvasRoot, "export-png.ts"));

  validateGovernedTemplateContract(templates);

  if (typeof globalThis.gc === "function") globalThis.gc();
  const heapBeforeReader = process.memoryUsage().heapUsed;
  const readerImportStarted = performance.now();
  const reader = await jiti.import(join(contextRoot, "governed/reader.server.ts"));
  const readerImportMs = performance.now() - readerImportStarted;
  reader.resetGovernedContextReaderForTests();
  const coldLoadStarted = performance.now();
  const projectionInfo = reader.getGovernedContextProjectionInfo();
  const coldLoadMs = performance.now() - coldLoadStarted;
  if (typeof globalThis.gc === "function") globalThis.gc();
  const readerHeapDeltaBytes = Math.max(0, process.memoryUsage().heapUsed - heapBeforeReader);
  validateProjectionInfo(projectionInfo, smallArtifacts.manifest);

  const modules = Object.freeze({
    canvasAdapter,
    connections,
    exportPng,
    layout,
    model,
    state,
    templates,
  });
  const firstPass = validatePublicCohort({
    eligibleIds: ledger.eligibleIds,
    manifest: smallArtifacts.manifest,
    measure: true,
    modules,
    passName: "A",
    reader,
    sourceTermsByPublicId: frozenSource.sourceTermsByPublicId,
    terms: smallArtifacts.terms,
  });
  assert.equal(firstPass.stats.failedObjects, 0, "first governed full-cohort pass failed");

  const heldSummary = validateHeldLookups(reader, ledger.heldIds);

  reader.resetGovernedContextReaderForTests();
  const secondPass = validatePublicCohort({
    eligibleIds: ledger.eligibleIds,
    manifest: smallArtifacts.manifest,
    measure: false,
    modules,
    passName: "B",
    reader,
    sourceTermsByPublicId: frozenSource.sourceTermsByPublicId,
    terms: smallArtifacts.terms,
  });
  assert.equal(secondPass.stats.failedObjects, 0, "second governed full-cohort pass failed");
  assert.deepEqual(secondPass.hashes, firstPass.hashes, "full governed projection pass changed");
  assert.deepEqual(
    deterministicCohortSummary(secondPass.stats),
    deterministicCohortSummary(firstPass.stats),
    "full governed cohort aggregates changed",
  );

  const explanationExamples = validateExplanationExamples({
    explanations: smallArtifacts.explanations,
    modules,
    projectionSha256: smallArtifacts.manifest.projectionSha256,
  });
  const cohort = deterministicCohortSummary(firstPass.stats);
  validateExpectedCohort(corpusComparable(cohort), smallArtifacts.manifest);
  const performanceSummary = buildPerformanceSummary({
    coldLoadMs,
    firstPass,
    readerHeapDeltaBytes,
    readerImportMs,
  });
  validateCompactRuntime(performanceSummary, artifactSummary, historicalBaseline);

  const invariants = buildInvariantResults({
    artifactSummary,
    clientBoundary,
    cohort,
    componentContract,
    generatorSummary,
    heldSummary,
    manifest: smallArtifacts.manifest,
  });
  assert.equal(invariants.length, 22);
  assert.equal(invariants.every((item) => item.status === "PASS"), true);

  const evidence = buildEvidence({
    artifactSummary,
    clientBoundary,
    cohort,
    componentContract,
    explanationExamples,
    frozenSource,
    generatorSummary,
    heldSummary,
    historicalBaseline,
    invariants,
    manifest: smallArtifacts.manifest,
    performanceSummary,
    firstPass,
  });
  assertEvidenceSanitized(evidence);
  const evidenceReceipt = await writeEvidence(args.evidenceDir, evidence);

  const workload = evidence.workload;
  console.log(`CONTEXT_GOVERNANCE_V1=PASS CONTEXT_V1_DECISION=CONTEXT_V1_CLOSED INVARIANTS=22 POLICY_VERSION=${POLICY_VERSION} POLICY_SHA256=${smallArtifacts.manifest.governancePolicySha256}`);
  console.log(`CONTEXT_GOVERNANCE_FULL_COHORT=PASS PUBLIC_OBJECTS_TESTED=${cohort.public_objects_tested} PUBLIC_OBJECTS_GOVERNED=${cohort.public_objects_tested} PUBLIC_OBJECTS_WITH_CONTEXT=${cohort.objects_with_context} OBJECTS_WITH_ONLY_ONE_REPRESENTATION=${cohort.objects_with_only_one_representation} SAME_KIND_MULTIVALUE_OBJECTS=${cohort.same_kind_multivalue_objects} FAILED_CONTEXT_OBJECTS=${cohort.failed_context_objects} GOVERNED_DATASET_FAILURE_COUNT=${cohort.failed_context_objects} UNEXPLAINED_NODES=${cohort.unexplained_nodes} UNKNOWN_TERM_IDS=${cohort.unknown_term_ids} PROVENANCE_FAILURES=${cohort.provenance_failures} API_SERIALIZATION_FAILURES=${cohort.api_serialization_failures}`);
  console.log(`CONTEXT_GOVERNANCE_PUBLICATION=PASS CONTEXT_KIND_COUNT=3 MEDIUM_TERM_COUNT=10 THEME_TERM_COUNT=8 MOVEMENT_TERM_COUNT=7 TERMS=${TERM_COUNT} REPRESENTATIONS=${cohort.representations} PUBLISHED=${cohort.publication_counts.published} QUALIFIED=${cohort.publication_counts.qualified} HELD=${cohort.publication_counts.held} EXCLUDED=${cohort.publication_counts.excluded} MOVEMENT_REPRESENTATIONS=${cohort.by_kind.movement_context.representations} REGION_CONTEXT_NODES=0 REGION_DEFERRED_TO_SPACETIME_COUNT=${REGION_ROW_COUNT}`);
  console.log(`CONTEXT_GOVERNANCE_SECURITY=PASS HELD_LOOKUPS=${heldSummary.held_lookups} HELD_OBJECTS_EXPOSED=${heldSummary.held_objects_exposed} LOOKUP_INDISTINGUISHABLE=true UNEXPLAINED_VISIBLE_NODE_COUNT=${cohort.unexplained_nodes} UNRESOLVED_EXPLANATION_CODE_COUNT=${cohort.unexplained_nodes} PROVENANCE_RESOLUTION_FAILURE_COUNT=${cohort.provenance_failures} PUBLIC_ID_COLLISION_COUNT=0 VALIDATION_ID_IN_GOVERNED_DTO_COUNT=0 INTERNAL_ID_EXPOSURE_COUNT=${cohort.internal_id_exposure_count} HEAVY_VALIDATION_SOURCE_INDEX_USED_BY_PUBLIC_RUNTIME=false FULL_CONTEXT_CORPUS_IN_CLIENT_BUNDLE=false BUNDLE_GUARD=${clientBoundary.bundle_status}`);
  console.log(`CONTEXT_GOVERNANCE_CANVAS=PASS DATA_MODE=governed_context_v1 TEMPLATE=context-overview TEMPLATE_VERSION=2 DEFAULT_VISIBLE_MEMBERSHIP_NODE_COUNT=0 DEFAULT_VISIBLE_MEMBERSHIP_CONNECTION_COUNT=0 DEFAULT_VISIBLE_SEMANTIC_EDGE_COUNT=0 VISIBLE_REPRESENTATIONS_P50=${workload.visible_representations.p50} VISIBLE_REPRESENTATIONS_P95=${workload.visible_representations.p95} VISIBLE_REPRESENTATIONS_MAX=${workload.visible_representations.max} DEFAULT_TOTAL_NODES_P50=${workload.total_nodes.p50} DEFAULT_TOTAL_NODES_P95=${workload.total_nodes.p95} DEFAULT_TOTAL_NODES_MAX=${workload.total_nodes.max}`);
  console.log(`CONTEXT_GOVERNANCE_RUNTIME=PASS PROJECTION_ID=${PROJECTION_ID} PROJECTION_SHA256=${smallArtifacts.manifest.projectionSha256} DETERMINISTIC=true GOVERNED_PROJECTION_RAW_BYTES=${artifactSummary.governed_projection_raw_bytes} GOVERNED_PROJECTION_GZIP_BYTES=${artifactSummary.governed_projection_gzip_bytes} GOVERNED_RUNTIME_HEAP_BYTES=${performanceSummary.reader_heap_delta_bytes} GOVERNED_RECORD_LOOKUP_P95_MS=${formatMs(performanceSummary.warm_public_lookup_ms.p95)}`);
  console.log(`CONTEXT_GOVERNANCE_EVIDENCE=PASS FILES=${evidenceReceipt.fileCount} SHA256=${evidenceReceipt.sha256} REGION_HANDOFF_TERMS=${frozenSource.regionHandoffRows.length} REGION_HANDOFF_ROWS=${sum(frozenSource.regionHandoffRows.map((row) => row.public_row_count))}`);
}

function requireCondition(condition, code, message) {
  if (!condition) throw new GovernanceValidationError(code, message);
}

function parseArguments(values) {
  let evidenceDir = defaultEvidenceDir;
  let requireBuild = false;
  for (let index = 0; index < values.length; index += 1) {
    const value = values[index];
    if (value === "--require-build") {
      requireBuild = true;
      continue;
    }
    if (value === "--evidence-dir") {
      const next = values[index + 1];
      assert(next, "--evidence-dir requires a path");
      evidenceDir = isAbsolute(next) ? next : resolve(repositoryRoot, next);
      index += 1;
      continue;
    }
    throw new Error(`unknown verifier argument: ${value}`);
  }
  return Object.freeze({ evidenceDir, requireBuild });
}

async function loadSmallArtifacts() {
  const filenames = [
    "exception-register.json",
    "explanation-registry.json",
    "governance-policy.json",
    "manifest.json",
    "terms.json",
  ];
  const values = Object.fromEntries(await Promise.all(filenames.map(async (filename) => [
    filename,
    JSON.parse(await readFile(join(generatedRoot, filename), "utf8")),
  ])));
  return Object.freeze({
    exceptions: values["exception-register.json"],
    explanations: values["explanation-registry.json"],
    manifest: values["manifest.json"],
    policy: values["governance-policy.json"],
    terms: values["terms.json"],
  });
}

function parseEligibilityLedger(contents) {
  const lines = contents.split(/\r?\n/u).filter(Boolean);
  const headers = lines.shift()?.split("\t") ?? [];
  const idIndex = headers.indexOf("surface_id_exact");
  const dispositionIndex = headers.indexOf("research_disposition");
  requireCondition(idIndex >= 0 && dispositionIndex >= 0, "ledger_shape", "eligibility ledger columns are missing");
  const eligible = new Set();
  const held = new Set();
  for (const line of lines) {
    const cells = line.split("\t");
    const stableId = cells[idIndex] ?? "";
    const disposition = cells[dispositionIndex] ?? "";
    requireCondition(PUBLIC_ID_PATTERN.test(stableId), "ledger_id", "eligibility ledger contains an invalid public ID");
    requireCondition(!eligible.has(stableId) && !held.has(stableId), "ledger_duplicate", "eligibility ledger contains duplicate identity");
    if (disposition === "eligible") eligible.add(stableId);
    else if (disposition === "held") held.add(stableId);
    else requireCondition(false, "ledger_disposition", "eligibility ledger contains an unknown disposition");
  }
  requireCondition(eligible.size === PUBLIC_OBJECT_COUNT, "eligible_census", "eligible object count differs");
  requireCondition(held.size === HELD_OBJECT_COUNT, "held_census", "held object count differs");
  return Object.freeze({
    eligibleIds: Object.freeze([...eligible].sort(compareText)),
    eligibleSet: eligible,
    heldIds: Object.freeze([...held].sort(compareText)),
    heldSet: held,
  });
}

async function validateFrozenSourceAndBuildRegisters(ledger, termsDocument, manifest) {
  const frozenBindings = Object.fromEntries(manifest.frozenInputs.map((item) => [item.path, item.sha256]));
  for (const [path, expected] of Object.entries(frozenBindings)) {
    requireCondition(SHA256_PATTERN.test(expected), "frozen_hash", "frozen input hash is invalid");
    const actual = await sha256File(join(repositoryRoot, path));
    requireCondition(actual === expected, "frozen_hash", `frozen input checksum differs: ${path}`);
  }
  const releaseProfileActual = await sha256File(join(repositoryRoot, manifest.releaseProfile.path));
  requireCondition(releaseProfileActual === manifest.releaseProfile.sha256, "release_profile_hash", "release profile checksum differs");

  const termById = new Map(termsDocument.terms.map((term) => [term.id, term]));
  requireCondition(termById.size === TERM_COUNT, "term_identity", "governed term ID collision");
  const sourceTermsByPublicId = new Map();
  const regionByPrivateId = new Map();
  const { DatabaseSync } = createRequire(import.meta.url)("node:sqlite");
  const database = new DatabaseSync(`file:${frozenDatabasePath}?mode=ro&immutable=1`, { readOnly: true });
  let rows;
  try {
    database.exec("PRAGMA query_only=ON");
    rows = [...database.prepare(
      "SELECT surface_id, folder_id, folder_type, title FROM object_folder_refs ORDER BY surface_id, folder_type, folder_id",
    ).iterate()];
  } finally {
    database.close();
  }

  let eligibleFolderRows = 0;
  let eligibleControlledRows = 0;
  let eligibleRegionRows = 0;
  for (const row of rows) {
    if (!ledger.eligibleSet.has(row.surface_id)) continue;
    eligibleFolderRows += 1;
    requireCondition(typeof row.title === "string" && row.title.trim().length > 0, "source_label", "frozen folder label is empty");
    requireCondition(!UUID_PATTERN.test(row.title) && !RAW_FOLDER_ID_PATTERN.test(row.title) && !URL_PATTERN.test(row.title), "source_label", "frozen folder label is not public-safe");
    if (row.folder_type === "region") {
      eligibleRegionRows += 1;
      const prior = regionByPrivateId.get(row.folder_id);
      requireCondition(!prior || prior.public_label === row.title, "region_label_conflict", "region source identity has conflicting labels");
      regionByPrivateId.set(row.folder_id, Object.freeze({
        public_label: row.title,
        public_row_count: (prior?.public_row_count ?? 0) + 1,
      }));
      continue;
    }
    requireCondition(["medium", "theme", "movement"].includes(row.folder_type), "source_kind", "unsupported controlled source kind");
    eligibleControlledRows += 1;
    const kind = row.folder_type === "movement" ? "movement_context" : row.folder_type;
    const expectedId = publicTermId(kind, row.folder_id);
    const term = termById.get(expectedId);
    requireCondition(Boolean(term), "term_resolution", "frozen controlled source identity did not resolve a governed term");
    requireCondition(term.kind === kind && term.label === row.title, "term_resolution", "frozen controlled term fields differ");
    const prior = sourceTermsByPublicId.get(expectedId);
    requireCondition(!prior || prior.privateIdentity === row.folder_id, "term_collision", "governed term ID collision across source identities");
    sourceTermsByPublicId.set(expectedId, Object.freeze({
      kind,
      label: row.title,
      privateIdentity: row.folder_id,
    }));
  }
  requireCondition(eligibleFolderRows === 24_102, "folder_census", "eligible frozen folder-row count differs");
  requireCondition(eligibleControlledRows === REPRESENTATION_COUNT, "assignment_census", "eligible controlled source-row count differs");
  requireCondition(eligibleRegionRows === REGION_ROW_COUNT, "region_census", "eligible region source-row count differs");
  requireCondition(sourceTermsByPublicId.size === TERM_COUNT, "term_census", "frozen governed source term count differs");
  requireCondition(regionByPrivateId.size === REGION_TERM_COUNT, "region_census", "eligible region term count differs");

  const handoffIds = new Set();
  const regionHandoffRows = Object.freeze([...regionByPrivateId.entries()].map(([privateId, value]) => {
    const handoff_id = `SPTREG:${sha256(["trace-spacetime-region-handoff-v1", privateId].join("\u0000"))}`;
    requireCondition(HANDOFF_ID_PATTERN.test(handoff_id), "region_handoff_id", "region handoff ID is invalid");
    requireCondition(!handoffIds.has(handoff_id), "region_handoff_collision", "region handoff ID collision");
    handoffIds.add(handoff_id);
    return Object.freeze({
      decision: "DEFER_TO_SPACETIME",
      handoff_id,
      public_label: value.public_label,
      public_row_count: value.public_row_count,
    });
  }).sort((left, right) => compareText(left.public_label, right.public_label)
    || compareText(left.handoff_id, right.handoff_id)));
  requireCondition(sum(regionHandoffRows.map((row) => row.public_row_count)) === REGION_ROW_COUNT, "region_census", "region handoff row total differs");
  requireCondition(
    !/SURF-|FOL-|[0-9a-f]{8}-[0-9a-f]{4}-/iu.test(JSON.stringify(regionHandoffRows)),
    "region_handoff_safety",
    "region handoff contains a private or record identity",
  );
  return Object.freeze({
    eligibleControlledRows,
    eligibleFolderRows,
    eligibleRegionRows,
    regionHandoffRows,
    sourceTermsByPublicId,
  });
}

async function validateArtifacts(artifacts, frozenSource) {
  const { exceptions, explanations, manifest, policy, terms } = artifacts;
  requireCondition(manifest.schemaVersion === "trace-context-manifest/v1", "manifest_schema", "governed manifest schema differs");
  requireCondition(manifest.contextSchemaVersion === "trace-context/v1", "dto_schema", "Context DTO schema differs");
  requireCondition(manifest.projectionId === PROJECTION_ID && SHA256_PATTERN.test(manifest.projectionSha256), "projection_identity", "projection identity differs");
  requireCondition(manifest.governancePolicyVersion === POLICY_VERSION, "policy_version", "governance policy version differs");
  requireCondition(manifest.sourceRelease.id === SOURCE_RELEASE.id && manifest.sourceRelease.manifestSha256 === SOURCE_RELEASE.manifestSha256, "release_binding", "source release binding differs");
  requireCondition(manifest.canonicalSourceState === "proposed", "source_state", "canonical source state was mutated");
  requireCondition(manifest.realSemanticEdgeCount === 0, "semantic_edge", "real semantic edge count is non-zero");
  requireCondition(manifest.regionContextNodeCount === 0, "region_context", "Region entered Context V1");

  requireCondition(policy.schemaVersion === "trace-context-governance-policy/v1" && policy.policyVersion === POLICY_VERSION, "policy_shape", "governance policy artifact differs");
  requireCondition(policy.epistemicRole === "project_curated_context", "policy_role", "governance epistemic role differs");
  requireCondition(policy.regionDecision?.decision === "DEFER_TO_SPACETIME" && policy.regionDecision?.contextNodeCount === 0, "region_policy", "Region governance decision differs");
  requireCondition(policy.provenanceRequirements?.sourceState === "proposed", "source_state", "policy source state differs");
  requireCondition(policy.publicIdPolicy?.idPolicyVersion === ID_POLICY_VERSION, "id_policy", "public ID policy differs");

  requireCondition(explanations.schemaVersion === "trace-context-explanations/v1", "explanation_schema", "explanation registry schema differs");
  requireCondition(explanations.entries.length === 3, "explanation_count", "explanation registry count differs");
  const explanationByCode = new Map(explanations.entries.map((entry) => [entry.explanationCode, entry]));
  requireCondition(explanationByCode.size === 3, "explanation_identity", "explanation code collision");
  for (const [kind, expected] of Object.entries(EXPECTED_KIND)) {
    const explanation = explanationByCode.get(expected.code);
    requireCondition(explanation?.contextKind === kind, "explanation_resolution", "Context kind explanation did not resolve");
    requireCondition(explanation.connectionLabel === expected.connectionLabel, "explanation_connection", "Context explanation connection label differs");
    validateExplanationText(explanation);
  }

  requireCondition(terms.schemaVersion === "trace-context-terms/v1" && terms.idPolicyVersion === ID_POLICY_VERSION, "term_schema", "term registry schema differs");
  requireCondition(terms.terms.length === TERM_COUNT, "term_census", "term registry count differs");
  const ids = new Set();
  const exactLabels = new Set();
  const normalizedLabels = new Set();
  for (const term of terms.terms) {
    requireCondition(TERM_ID_PATTERN.test(term.id), "term_id", "governed term ID is invalid");
    requireCondition(!ids.has(term.id), "term_collision", "governed term ID collision");
    requireCondition(!exactLabels.has(term.label), "term_label_collision", "governed term public label is reused");
    const normalized = normalizeLabel(term.label);
    requireCondition(!normalizedLabels.has(normalized), "term_normalization_collision", "governed term normalized label is reused");
    requireCondition(frozenSource.sourceTermsByPublicId.has(term.id), "term_resolution", "governed term did not resolve frozen source identity");
    requireCondition(term.publicationState === "published", "term_publication", "governed term publication differs");
    requireCondition(EXPECTED_KIND[term.kind]?.code === term.explanationCode, "term_explanation", "term explanation code differs");
    ids.add(term.id);
    exactLabels.add(term.label);
    normalizedLabels.add(normalized);
  }
  for (const [kind, expected] of Object.entries(EXPECTED_KIND)) {
    requireCondition(terms.terms.filter((term) => term.kind === kind).length === expected.termCount, "term_kind_census", "term kind census differs");
  }

  requireCondition(exceptions.schemaVersion === "trace-context-exceptions/v1", "exception_schema", "exception register schema differs");
  requireCondition(exceptions.counts.qualifiedEntries === 0 && exceptions.counts.heldEntries === 0 && exceptions.counts.excludedEntries === 0, "exception_state", "unexpected governed exception publication state");
  const regionException = exceptions.entries.find((entry) => entry.exceptionCode === "CTX-EXC-REGION-SPACETIME-HANDOFF");
  requireCondition(regionException?.decision === "DEFERRED_TO_OTHER_DOMAIN", "region_exception", "Region exception decision differs");
  requireCondition(regionException.scope?.termCount === REGION_TERM_COUNT && regionException.scope?.sourceRowCount === REGION_ROW_COUNT && regionException.scope?.contextNodeCount === 0, "region_exception", "Region exception census differs");
  const movementException = exceptions.entries.find((entry) => entry.exceptionCode === "CTX-EXC-MOVEMENT-MULTIVALUE");
  requireCondition(movementException?.decision === "PUBLISHED" && movementException.scope?.publicRecordCount === 5, "movement_exception", "movement multi-value decision differs");

  const expectedCoreFiles = Object.keys(manifest.artifactSha256).sort(compareText);
  requireCondition(expectedCoreFiles.length === 5, "artifact_set", "core governed artifact set differs");
  let rawBytes = 0;
  for (const filename of expectedCoreFiles) {
    const bytes = await readFile(join(generatedRoot, filename));
    requireCondition(sha256(bytes) === manifest.artifactSha256[filename], "artifact_hash", `artifact checksum differs: ${filename}`);
    requireCondition(bytes.byteLength === manifest.artifactBytes[filename], "artifact_bytes", `artifact byte count differs: ${filename}`);
    rawBytes += bytes.byteLength;
  }
  requireCondition(rawBytes === manifest.governedProjectionRawBytes, "projection_bytes", "governed projection raw bytes differ");
  const checksumLines = (await readFile(join(generatedRoot, "CHECKSUMS.sha256"), "utf8"))
    .trim().split("\n");
  const expectedChecksumFiles = [...expectedCoreFiles, "manifest.json"].sort(compareText);
  requireCondition(checksumLines.length === expectedChecksumFiles.length, "checksum_set", "generated checksum row count differs");
  for (const line of checksumLines) {
    const match = /^([0-9a-f]{64})  ([a-z0-9.-]+)$/u.exec(line);
    requireCondition(Boolean(match), "checksum_shape", "generated checksum row is invalid");
    requireCondition(expectedChecksumFiles.includes(match[2]), "checksum_set", "generated checksum names an unexpected artifact");
    requireCondition(sha256(await readFile(join(generatedRoot, match[2]))) === match[1], "checksum_value", "generated checksum differs");
  }
  return Object.freeze({
    governed_projection_gzip_bytes: manifest.governedProjectionGzipBytes,
    governed_projection_raw_bytes: manifest.governedProjectionRawBytes,
    source_database_bytes: (await stat(frozenDatabasePath)).size,
    term_collision_count: 0,
    term_normalization_collision_count: 0,
  });
}

function runDeterministicGeneratorCheck(manifest) {
  const result = spawnSync(
    process.execPath,
    [join(frontendRoot, "scripts/generate-trace-context-v1.mjs"), "--check"],
    {
      cwd: repositoryRoot,
      encoding: "utf8",
      maxBuffer: 8 * 1024 * 1024,
    },
  );
  requireCondition(result.status === 0, "deterministic_rebuild", `governed generator check failed: ${result.stderr || result.stdout}`);
  requireCondition(result.stdout.includes("TRACE_CONTEXT_V1_GENERATION=PASS MODE=CHECK RUNS=2"), "deterministic_rebuild", "governed generator did not report two deterministic runs");
  requireCondition(result.stdout.includes(`PROJECTION_SHA256=${manifest.projectionSha256}`), "deterministic_rebuild", "governed generator projection hash differs");
  return Object.freeze({
    deterministic: true,
    projection_sha256: manifest.projectionSha256,
    rebuild_runs: 2,
  });
}

function validateGovernedTemplateContract(templates) {
  const governed = templates.getContextCanvasTemplatesForMode("governed_context_v1");
  requireCondition(governed.length === 1, "governed_template_count", "governed mode does not have exactly one template");
  requireCondition(governed[0].templateId === "context-overview", "governed_template_id", "governed default template differs");
  requireCondition(governed[0].version === 2, "governed_template_version", "governed template version differs");
  requireCondition(governed[0].entitySelectionRule === "all-governed-representations", "governed_template_rule", "governed template selection rule differs");
  for (const forbidden of ["descriptive-context", "curated-context", "full-context"]) {
    requireCondition(!governed.some((template) => template.templateId === forbidden), "governed_template_surface", "legacy template entered governed mode");
  }
}

function validateProjectionInfo(info, manifest) {
  requireCondition(info.projectionId === PROJECTION_ID && info.projectionSha256 === manifest.projectionSha256, "projection_info", "reader projection identity differs");
  requireCondition(info.researchReleaseId === SOURCE_RELEASE.id && info.researchManifestSha256 === SOURCE_RELEASE.manifestSha256, "projection_info", "reader release identity differs");
  requireCondition(info.recordCount === PUBLIC_OBJECT_COUNT && info.termCount === TERM_COUNT && info.representationCount === REPRESENTATION_COUNT, "projection_info", "reader census differs");
  requireCondition(info.rawBytes === manifest.governedProjectionRawBytes && info.gzipBytes === manifest.governedProjectionGzipBytes, "projection_info", "reader payload census differs");
}

function createPassStats(measure) {
  const distributions = {};
  for (const key of [
    "accessible_rows",
    "api_bytes",
    "api_serialization_ms",
    "canvas_total_ms",
    "dto_bytes",
    "export_bytes",
    "export_ms",
    "geometry_ms",
    "layout_ms",
    "lookup_ms",
    "total_connections",
    "total_nodes",
    "visible_representations",
  ]) distributions[key] = [];
  return {
    apiSerializationFailures: 0,
    byKind: Object.fromEntries(Object.keys(EXPECTED_KIND).map((kind) => [kind, { objects: 0, representations: 0 }])),
    distributions,
    failedObjects: 0,
    internalIdExposureCount: 0,
    membershipConnectionCount: 0,
    membershipNodeCount: 0,
    objectHistogram: {},
    objectsWithContext: 0,
    provenanceFailures: 0,
    publicationCounts: { excluded: 0, held: 0, published: 0, qualified: 0 },
    publicObjectsTested: 0,
    representations: 0,
    sameKindMultivalueObjects: 0,
    semanticConnectionCount: 0,
    semanticEdgeCount: 0,
    termAssignmentCounts: new Map(),
    unexplainedNodes: 0,
    unknownTermIds: 0,
    measure,
  };
}

function validatePublicCohort({
  eligibleIds,
  manifest,
  measure,
  modules,
  passName,
  reader,
  sourceTermsByPublicId,
  terms,
}) {
  const stats = createPassStats(measure);
  const hashers = Object.fromEntries([
    "accessibility",
    "api",
    "canvas",
    "dto",
    "export",
  ].map((key) => [key, createHash("sha256")]));
  const globalRepresentationIds = new Set();
  const globalProvenanceIds = new Set();
  const termById = new Map(terms.terms.map((term) => [term.id, term]));
  for (let ordinal = 0; ordinal < eligibleIds.length; ordinal += 1) {
    const stableId = eligibleIds[ordinal];
    try {
      const lookupStarted = performance.now();
      const lookup = reader.lookupGovernedContextDataset(stableId, {
        researchReleaseId: SOURCE_RELEASE.id,
        researchManifestSha256: SOURCE_RELEASE.manifestSha256,
      });
      const lookupMs = performance.now() - lookupStarted;
      requireCondition(lookup.ok, "public_lookup", "eligible governed Context lookup failed");
      const dto = lookup.data;
      validatePublicDto({
        dto,
        globalProvenanceIds,
        globalRepresentationIds,
        manifest,
        sourceTermsByPublicId,
        stats,
        stableId,
        termById,
      });

      const canvasStarted = performance.now();
      const input = modules.canvasAdapter.adaptPublicContextDatasetForCanvas(dto);
      validateCanvasAdapterEnvelope(input, dto, manifest);
      const stateStarted = performance.now();
      const canvasState = modules.state.createInitializingContextCanvasState(
        input.dataset,
        input.dataMode,
        input.metadata,
      );
      const layoutMs = performance.now() - stateStarted;
      const composition = canvasState.history.present;
      validateComposition(composition, canvasState, dto);
      const nodes = modules.connections.visibleContextCanvasNodes(
        input.dataset,
        composition,
        input.dataMode,
        input.metadata,
      );
      const visibleConnections = modules.connections.deriveVisibleContextCanvasConnections(
        input.dataset,
        composition.visibleEntityIds,
        input.dataMode,
        input.metadata,
      );
      const geometryStarted = performance.now();
      const geometry = modules.connections.buildContextCanvasConnectionGeometry(
        input.dataset,
        composition,
        input.dataMode,
        input.metadata,
      );
      const geometryMs = performance.now() - geometryStarted;
      const accessibleRows = modules.model.contextCanvasAccessibleRowsForMode(
        input.dataset,
        input.dataMode,
        input.metadata,
      );
      validateCanvasSemantics({
        accessibleRows,
        composition,
        dto,
        geometry,
        input,
        modules,
        nodes,
        state: canvasState,
        visibleConnections,
      });
      const bounds = modules.layout.computeContextCanvasBounds(
        composition.visibleEntityIds,
        composition.positions,
      );
      const viewport = modules.layout.fitContextCanvasViewport(bounds, viewportSize);
      requireCondition(!bounds.empty && bounds.width > 0 && bounds.height > 0, "canvas_bounds", "governed Canvas bounds are empty");
      requireCondition(Number.isFinite(viewport.x) && Number.isFinite(viewport.y) && Number.isFinite(viewport.zoom), "canvas_viewport", "governed Canvas viewport is non-finite");

      const exportStarted = performance.now();
      const exportSnapshot = modules.exportPng.prepareContextCanvasExportSvg(
        input.dataset,
        composition,
        true,
        input.dataMode,
        input.metadata,
      );
      const exportMs = performance.now() - exportStarted;
      validateExport(exportSnapshot, dto, visibleConnections.length, manifest);
      const filename = modules.exportPng.buildContextCanvasPngFilename(
        dto.selectedRecord.surfaceId,
        fixedExportInstant,
      );
      requireCondition(/^context-canvas-SURF-[A-Z0-9-]+-20260823T000000Z\.png$/u.test(filename), "export_filename", "governed export filename is not public-safe");

      const apiStarted = performance.now();
      const apiText = serializeApiEnvelope(dto);
      const apiMs = performance.now() - apiStarted;
      validateApiSerialization(apiText, dto, manifest);
      const canvasMs = performance.now() - canvasStarted;

      updateHash(hashers.dto, JSON.stringify(dto));
      updateHash(hashers.canvas, JSON.stringify({ composition, connections: visibleConnections, geometry, nodes }));
      updateHash(hashers.accessibility, JSON.stringify(accessibleRows));
      updateHash(hashers.export, exportSnapshot.svg);
      updateHash(hashers.api, apiText);
      stats.publicObjectsTested += 1;
      const representationCount = dto.representations.length;
      stats.objectHistogram[representationCount] = (stats.objectHistogram[representationCount] ?? 0) + 1;
      if (measure) {
        stats.distributions.lookup_ms.push(lookupMs);
        stats.distributions.layout_ms.push(layoutMs);
        stats.distributions.geometry_ms.push(geometryMs);
        stats.distributions.export_ms.push(exportMs);
        stats.distributions.api_serialization_ms.push(apiMs);
        stats.distributions.canvas_total_ms.push(canvasMs);
        stats.distributions.visible_representations.push(representationCount);
        stats.distributions.total_nodes.push(nodes.length);
        stats.distributions.total_connections.push(visibleConnections.length);
        stats.distributions.accessible_rows.push(accessibleRows.length);
        stats.distributions.dto_bytes.push(Buffer.byteLength(JSON.stringify(dto)));
        stats.distributions.api_bytes.push(Buffer.byteLength(apiText));
        stats.distributions.export_bytes.push(Buffer.byteLength(exportSnapshot.svg));
      }
    } catch (error) {
      stats.failedObjects += 1;
      failureRows.push(Object.freeze({
        bugClass: error instanceof GovernanceValidationError ? error.code : "object_validation",
        message: sanitizeFailureMessage(error),
        ordinal: ordinal + 1,
        pass: passName,
      }));
    }
  }
  return Object.freeze({
    hashes: Object.freeze(Object.fromEntries(Object.entries(hashers)
      .map(([key, hasher]) => [key, hasher.digest("hex")]))),
    stats,
  });
}

function validatePublicDto({
  dto,
  globalProvenanceIds,
  globalRepresentationIds,
  manifest,
  sourceTermsByPublicId,
  stableId,
  stats,
  termById,
}) {
  requireCondition(dto.schemaVersion === "trace-context/v1", "dto_schema", "public Context DTO schema differs");
  requireCondition(dto.release.researchReleaseId === SOURCE_RELEASE.id && dto.release.researchManifestSha256 === SOURCE_RELEASE.manifestSha256, "dto_release", "public Context DTO research release differs");
  requireCondition(dto.release.contextProjectionId === PROJECTION_ID && dto.release.contextProjectionSha256 === manifest.projectionSha256, "dto_projection", "public Context DTO projection differs");
  requireCondition(dto.selectedRecord.surfaceId === stableId && PUBLIC_ID_PATTERN.test(stableId), "dto_record", "public Context selected record differs");
  requireCondition(dto.availability === "ready", "dto_availability", "public Context DTO is not ready");
  requireCondition(dto.counts.representations === dto.representations.length, "dto_counts", "public Context representation count differs");
  requireCondition(dto.representations.length >= 2 && dto.representations.length <= 4, "dto_counts", "public Context selected representation workload differs");
  requireCondition(dto.explanationRegistryVersion === "trace-context-explanations-v1", "dto_explanation_version", "public Context explanation version differs");
  validatePublicRootMetadata(dto.selectedRecord.rootMetadata);

  const serialized = JSON.stringify(dto);
  const leakedKeys = [...collectKeys(dto)].filter((key) => FORBIDDEN_DTO_KEYS.has(key));
  requireCondition(leakedKeys.length === 0, "internal_id_exposure", "public Context DTO contains a forbidden field");
  requireCondition(!VALIDATION_ID_PATTERN.test(serialized) && !UUID_PATTERN.test(serialized) && !RAW_FOLDER_ID_PATTERN.test(serialized), "internal_id_exposure", "public Context DTO contains an internal identity");
  requireCondition(!Object.hasOwn(dto, "records") && !Object.hasOwn(dto, "terms"), "full_corpus_exposure", "selected Context DTO contains a full corpus");

  const explanationByCode = new Map(dto.explanations.map((explanation) => [explanation.explanationCode, explanation]));
  requireCondition(explanationByCode.size === dto.explanations.length, "explanation_collision", "selected Context DTO explanation code collision");
  const representationIds = new Set();
  const provenanceIds = new Set();
  const sameKindCounts = {};
  const representedKinds = new Set();
  for (const representation of dto.representations) {
    const expected = EXPECTED_KIND[representation.kind];
    requireCondition(Boolean(expected), "representation_kind", "public Context representation kind is unsupported");
    requireCondition(REPRESENTATION_ID_PATTERN.test(representation.id), "representation_id", "governed representation ID is invalid");
    requireCondition(TERM_ID_PATTERN.test(representation.termId), "term_id", "governed term ID is invalid");
    requireCondition(PROVENANCE_ID_PATTERN.test(representation.provenance?.provenanceId), "provenance_id", "governed provenance ID is invalid");
    requireCondition(!representationIds.has(representation.id) && !globalRepresentationIds.has(representation.id), "representation_collision", "governed representation ID collision");
    requireCondition(!provenanceIds.has(representation.provenance.provenanceId) && !globalProvenanceIds.has(representation.provenance.provenanceId), "provenance_collision", "governed provenance ID collision");
    const term = termById.get(representation.termId);
    requireCondition(Boolean(term), "unknown_term", "governed representation term did not resolve");
    requireCondition(term.kind === representation.kind && term.label === representation.label, "term_resolution", "governed representation term fields differ");
    requireCondition(sourceTermsByPublicId.has(representation.termId), "term_resolution", "governed representation term has no frozen source identity");
    requireCondition(representation.id === publicRepresentationId(stableId, representation.kind, representation.termId), "representation_id", "governed representation ID material differs");
    requireCondition(representation.epistemicRole === "project_curated_context", "epistemic_role", "Context representation is not explicitly project-curated");
    requireCondition(representation.explanationCode === expected.code, "explanation_resolution", "representation explanation code differs");
    requireCondition(explanationByCode.get(representation.explanationCode)?.contextKind === representation.kind, "unexplained_node", "visible governed Context node lacks a registered explanation");
    requireCondition(["published", "qualified"].includes(representation.publicationState), "publication_state", "Context representation publication state is unresolved");
    requireCondition(representation.publicationState === "published", "publication_state", "unexpected non-published real representation");
    const provenance = representation.provenance;
    requireCondition(provenance.provenanceId === publicProvenanceId(representation.id), "provenance_id", "governed provenance ID material differs");
    requireCondition(provenance.basis === "project_curated_typed_membership", "provenance_resolution", "Context provenance basis differs");
    requireCondition(provenance.sourceKind === expected.sourceKind, "provenance_resolution", "Context provenance source kind differs");
    requireCondition(provenance.sourceState === "proposed", "source_state", "frozen Context source state was mutated");
    requireCondition(provenance.mappingPolicyVersion === MAPPING_VERSION && provenance.governancePolicyVersion === POLICY_VERSION, "provenance_resolution", "Context provenance policy binding differs");
    requireCondition(provenance.decision === "PUBLISHED", "publication_state", "Context governance decision differs");

    const publicAccessible = dto.accessibleRows.filter((row) => row.id === `representation:${representation.id}`);
    requireCondition(publicAccessible.length === 1 && publicAccessible[0].explanationCode === representation.explanationCode, "accessible_equivalence", "public accessible representation row did not resolve");
    const publicValues = valuesByLabel(publicAccessible[0]);
    requireCondition(publicValues.get("Publication state") === representation.publicationState, "accessible_equivalence", "public accessible publication state differs");
    requireCondition(publicValues.get("Source state") === "proposed", "accessible_equivalence", "public accessible source state differs");
    requireCondition(publicValues.get("Permitted interpretation")?.includes(representation.label), "accessible_equivalence", "public accessible permitted interpretation did not resolve the term");

    representationIds.add(representation.id);
    provenanceIds.add(provenance.provenanceId);
    globalRepresentationIds.add(representation.id);
    globalProvenanceIds.add(provenance.provenanceId);
    sameKindCounts[representation.kind] = (sameKindCounts[representation.kind] ?? 0) + 1;
    representedKinds.add(representation.kind);
    stats.representations += 1;
    stats.byKind[representation.kind].representations += 1;
    stats.publicationCounts[representation.publicationState] += 1;
    stats.termAssignmentCounts.set(representation.termId, (stats.termAssignmentCounts.get(representation.termId) ?? 0) + 1);
  }
  requireCondition(dto.accessibleRows.length === dto.representations.length + 1, "accessible_rows", "public accessible row count differs");
  requireCondition(dto.accessibleRows.filter((row) => row.category === "selected_record").length === 1, "accessible_rows", "public selected-record accessible row differs");
  stats.objectsWithContext += 1;
  for (const kind of representedKinds) stats.byKind[kind].objects += 1;
  if (Object.values(sameKindCounts).some((count) => count > 1)) stats.sameKindMultivalueObjects += 1;
}

function validatePublicRootMetadata(value) {
  requireCondition(value && Object.keys(value).sort(compareText).join("|") === "creatorAttribution|dateDisplay|objectType|sourceName", "root_metadata", "public root metadata fields differ");
  for (const text of Object.values(value)) {
    requireCondition(typeof text === "string" && text.trim().length > 0, "root_metadata", "public root metadata is empty");
    requireCondition(!UUID_PATTERN.test(text) && !URL_PATTERN.test(text) && !RAW_FOLDER_ID_PATTERN.test(text), "root_metadata", "public root metadata contains a forbidden value");
  }
}

function validateCanvasAdapterEnvelope(input, dto, manifest) {
  requireCondition(input.dataMode === "governed_context_v1", "canvas_mode", "Canvas adapter data mode differs");
  requireCondition(input.metadata.candidateState === "published" && input.metadata.governedPublicRelease === true && input.metadata.publicReleaseData === true, "canvas_metadata", "governed Canvas publication metadata differs");
  requireCondition(input.metadata.historicalEvidence === false, "canvas_metadata", "governed Canvas claims historical evidence");
  requireCondition(input.metadata.governedContext.policyVersion === POLICY_VERSION, "canvas_metadata", "governed Canvas policy differs");
  requireCondition(input.metadata.governedContext.projectionId === PROJECTION_ID && input.metadata.governedContext.projectionSha256 === manifest.projectionSha256, "canvas_metadata", "governed Canvas projection differs");
  requireCondition(input.metadata.governedContext.representations.length === dto.representations.length, "canvas_metadata", "governed Canvas representation count differs");
  requireCondition(input.dataset.curatedMemberships.length === 0, "membership_node", "governed Canvas dataset contains membership nodes");
  requireCondition(input.dataset.semanticEdges.length === 0 && input.dataset.counts.semanticEdgeCount === 0, "semantic_edge", "governed Canvas dataset contains semantic edges");
  requireCondition(input.dataset.controlledAssignments.every((assignment) => assignment.state === "proposed"), "source_state", "Canvas adapter mutated frozen source state");
  requireCondition(input.dataset.warnings.includes("PROJECT_CURATED_CONTEXT_NOT_A_HISTORICAL_RELATION"), "canvas_warning", "governed Canvas historical-relation warning is missing");
  requireCondition(input.dataset.warnings.includes("CURATED_MEMBERSHIP_IS_PROVENANCE_ONLY"), "canvas_warning", "governed Canvas provenance-only membership warning is missing");
  requireCondition(input.dataset.warnings.includes("REGION_IS_DEFERRED_TO_SPACETIME"), "canvas_warning", "governed Canvas Region handoff warning is missing");
}

function validateComposition(composition, canvasState, dto) {
  requireCondition(canvasState.schemaVersion === 2, "canvas_schema", "Context Canvas schema version differs");
  requireCondition(composition.templateId === "context-overview" && composition.templateVersion === 2, "canvas_template", "governed Canvas template differs");
  requireCondition(composition.visibleEntityIds.length === dto.representations.length + 1, "canvas_nodes", "governed Canvas visible node count differs");
  requireCondition(new Set(composition.visibleEntityIds).size === composition.visibleEntityIds.length, "canvas_nodes", "governed Canvas visible entity collision");
  requireCondition(canvasState.allowedEntityIds.length === dto.representations.length + 1, "canvas_palette", "governed Canvas palette entity count differs");
  requireCondition(composition.visibleEntityIds.every((id) => canvasState.allowedEntityIds.includes(id)), "canvas_palette", "governed Canvas visible entity is outside the palette contract");
  requireCondition(Object.keys(composition.positions).length === composition.visibleEntityIds.length, "canvas_layout", "governed Canvas layout position count differs");
  for (const position of Object.values(composition.positions)) {
    requireCondition(Number.isFinite(position.x) && Number.isFinite(position.y), "canvas_layout", "governed Canvas layout is non-finite");
  }
}

function validateCanvasSemantics({
  accessibleRows,
  composition,
  dto,
  geometry,
  input,
  modules,
  nodes,
  state,
  visibleConnections,
}) {
  requireCondition(nodes.length === dto.representations.length + 1, "canvas_nodes", "governed Canvas node derivation differs");
  requireCondition(nodes.filter((node) => node.isRoot).length === 1, "canvas_root", "governed Canvas root node differs");
  requireCondition(nodes.filter((node) => !node.isRoot && node.representation).length === dto.representations.length, "canvas_inspector", "governed Canvas inspector backing representation is missing");
  requireCondition(nodes.every((node) => node.isRoot || node.ref.kind === "controlled_term"), "membership_node", "governed Canvas exposes a non-controlled palette entity");
  requireCondition(visibleConnections.length === dto.representations.length, "canvas_connections", "governed Canvas connection count differs");
  requireCondition(visibleConnections.every((connection) => connection.connectionKind === "context_representation"), "semantic_connection", "governed Canvas converted a representation into another connection class");
  requireCondition(visibleConnections.every((connection) => connection.representation.epistemicRole === "project_curated_context"), "epistemic_role", "governed Canvas connection is not explicitly project-curated");
  requireCondition(geometry.length === visibleConnections.length, "canvas_geometry", "governed Canvas geometry count differs");
  requireCondition(geometry.every((item) => CONNECTOR_PATH_PATTERN.test(item.path) && Number.isFinite(item.labelX) && Number.isFinite(item.labelY)), "canvas_geometry", "governed Canvas connector geometry is invalid");
  requireCondition(new Set(visibleConnections.map((connection) => connection.id)).size === visibleConnections.length, "canvas_connection_collision", "governed Canvas connection ID collision");
  requireCondition(accessibleRows.length === dto.representations.length + 1, "accessible_rows", "governed Canvas accessible row count differs");
  requireCondition(accessibleRows.filter((row) => row.category === "selected_record").length === 1, "accessible_rows", "governed Canvas root accessible row differs");
  const rowById = new Map(accessibleRows.map((row) => [row.id, row]));
  requireCondition(rowById.size === accessibleRows.length, "accessible_collision", "governed Canvas accessible row collision");
  const representationByEntity = modules.model.contextCanvasRepresentationByEntityId(
    input.dataMode,
    input.metadata,
  );
  requireCondition(representationByEntity.size === dto.representations.length, "canvas_inspector", "governed Canvas inspector map count differs");
  for (const representation of input.metadata.governedContext.representations) {
    const row = rowById.get(`representation:${representation.representationId}`);
    requireCondition(Boolean(row), "accessible_equivalence", "governed Canvas representation accessible row is missing");
    const values = valuesByLabel(row);
    const expectedValues = Object.freeze({
      "Context type": representation.explanation.publicName,
      "Epistemic role": representation.epistemicRole,
      "Explanation code": representation.explanationCode,
      "Full label": representation.label,
      "Governance decision": representation.provenance.decision,
      "Governance policy version": representation.provenance.governancePolicyVersion,
      "Mapping policy version": representation.provenance.mappingPolicyVersion,
      "Meaning": representation.explanation.longDefinition,
      "Permitted interpretation": representation.explanation.permittedInterpretation,
      "Prohibited interpretations": representation.explanation.prohibitedInterpretations.join("; "),
      "Public provenance ID": representation.provenance.provenanceId,
      "Publication state": representation.publicationState,
      "Source basis": representation.explanation.sourceBasis,
      "Source state": representation.provenance.sourceState,
      "Why shown": representation.explanation.whyShown,
    });
    for (const [label, expected] of Object.entries(expectedValues)) {
      requireCondition(values.get(label) === expected, "accessible_equivalence", `governed Canvas accessible explanation differs: ${label}`);
    }
    const connection = visibleConnections.find((item) => item.representation.representationId === representation.representationId);
    requireCondition(Boolean(connection), "canvas_inspector", "governed Canvas connection inspector backing is missing");
    requireCondition(connection.representation === representation, "canvas_inspector", "governed Canvas connection inspector representation differs");
    const geometryRow = geometry.find((item) => item.connection.id === connection.id);
    requireCondition(geometryRow?.accessibleLabel.includes(representation.explanation.longDefinition), "accessible_equivalence", "connector accessible explanation omits the visual meaning");
    requireCondition(geometryRow?.accessibleLabel.includes(representation.explanation.permittedInterpretation), "accessible_equivalence", "connector accessible explanation omits the permitted interpretation");
    requireCondition(geometryRow?.accessibleLabel.includes(representation.explanation.prohibitedInterpretations.join("; ")), "accessible_equivalence", "connector accessible explanation omits prohibited interpretations");
  }
  requireCondition(state.allowedEntityIds.every((entityId) => composition.visibleEntityIds.includes(entityId)), "canvas_palette", "default governed Canvas omits an available controlled representation");
}

function validateExport(snapshot, dto, connectionCount, manifest) {
  requireCondition(snapshot.width > 0 && snapshot.height > 0 && !snapshot.contentBounds.empty, "export_preparation", "governed export dimensions are invalid");
  requireCondition(countOccurrences(snapshot.svg, 'data-connection-kind="context_representation"') === connectionCount, "export_preparation", "governed export representation count differs");
  requireCondition(!snapshot.svg.includes('data-connection-kind="curated_membership"'), "membership_export", "governed export contains membership duplication");
  requireCondition(!snapshot.svg.includes('data-connection-kind="semantic_edge"'), "semantic_export", "governed export contains semantic edges");
  requireCondition(!VALIDATION_ID_PATTERN.test(snapshot.svg) && !UUID_PATTERN.test(snapshot.svg) && !RAW_FOLDER_ID_PATTERN.test(snapshot.svg), "internal_id_exposure", "governed export contains an internal identity");
  requireCondition(snapshot.svg.includes(dto.selectedRecord.surfaceId), "export_traceability", "governed export omits selected public record identity");
  requireCondition(snapshot.svg.includes(SOURCE_RELEASE.id) && snapshot.svg.includes(PROJECTION_ID) && snapshot.svg.includes(manifest.projectionSha256), "export_traceability", "governed export omits release/projection traceability");
}

function serializeApiEnvelope(dto) {
  return JSON.stringify({
    apiVersion: "v1",
    researchReleaseId: SOURCE_RELEASE.id,
    researchManifestSha256: SOURCE_RELEASE.manifestSha256,
    visualRegistryVersion: null,
    visualRegistrySha256: null,
    visualRegistryState: "UNAVAILABLE",
    visualReasonCodes: ["VISUAL_REGISTRY_UNAVAILABLE", "POSITIVE_VISUAL_RIGHTS_COUNT_ZERO"],
    takedownOverlaySha256: null,
    data: dto,
  });
}

function validateApiSerialization(text, dto, manifest) {
  let envelope;
  try {
    envelope = JSON.parse(text);
  } catch {
    requireCondition(false, "api_serialization", "Context API serialization is not valid JSON");
  }
  requireCondition(envelope.apiVersion === "v1", "api_serialization", "Context API version differs");
  requireCondition(envelope.researchReleaseId === SOURCE_RELEASE.id && envelope.researchManifestSha256 === SOURCE_RELEASE.manifestSha256, "api_serialization", "Context API release pin differs");
  requireCondition(envelope.data.schemaVersion === "trace-context/v1", "api_serialization", "Context API DTO schema differs");
  requireCondition(envelope.data.selectedRecord.surfaceId === dto.selectedRecord.surfaceId, "api_serialization", "Context API selected record differs");
  requireCondition(envelope.data.release.contextProjectionId === PROJECTION_ID && envelope.data.release.contextProjectionSha256 === manifest.projectionSha256, "api_serialization", "Context API projection pin differs");
  requireCondition(JSON.stringify(envelope.data) === JSON.stringify(dto), "api_serialization", "Context API DTO round trip differs");
  requireCondition(!VALIDATION_ID_PATTERN.test(text) && !UUID_PATTERN.test(text) && !RAW_FOLDER_ID_PATTERN.test(text), "internal_id_exposure", "Context API serialization contains an internal identity");
}

function validateHeldLookups(reader, heldIds) {
  const unknown = reader.lookupGovernedContextDataset("SURF-CONTEXT-V1-UNKNOWN-RECORD", SOURCE_RELEASE_FOR_LOOKUP);
  requireCondition(!unknown.ok && unknown.code === "NOT_FOUND", "unknown_lookup", "unknown governed Context lookup did not fail closed");
  let exposed = 0;
  let parityFailures = 0;
  const lookupTimes = [];
  for (const heldId of heldIds) {
    const started = performance.now();
    const lookup = reader.lookupGovernedContextDataset(heldId, SOURCE_RELEASE_FOR_LOOKUP);
    lookupTimes.push(performance.now() - started);
    if (lookup.ok) exposed += 1;
    if (lookup.ok || lookup.code !== unknown.code || lookup.message !== unknown.message) parityFailures += 1;
  }
  requireCondition(exposed === 0, "held_exposure", "held governed Context object was exposed");
  requireCondition(parityFailures === 0, "held_unknown_parity", "held and unknown governed Context lookups differ");
  return Object.freeze({
    held_lookups: heldIds.length,
    held_objects_exposed: exposed,
    held_unknown_parity_failures: parityFailures,
    lookup_ms: summarizeDistribution(lookupTimes),
  });
}

function validateExplanationExamples({ explanations, modules, projectionSha256 }) {
  const byKind = new Map(explanations.entries.map((entry) => [entry.contextKind, entry]));
  const definitions = [
    ["medium", "published"],
    ["theme", "published"],
    ["movement_context", "published"],
    ["theme", "qualified"],
  ];
  return Object.freeze(definitions.map(([kind, publicationState], index) => {
    const explanation = byKind.get(kind);
    requireCondition(Boolean(explanation), "explanation_example", "synthetic explanation kind did not resolve");
    const dto = buildSyntheticDto({
      explanation,
      index,
      kind,
      projectionSha256,
      publicationState,
    });
    const input = modules.canvasAdapter.adaptPublicContextDatasetForCanvas(dto);
    const composition = modules.templates.initializeContextCanvasTemplate(
      input.dataset,
      "context-overview",
      input.dataMode,
      input.metadata,
    );
    const rows = modules.model.contextCanvasAccessibleRowsForMode(input.dataset, input.dataMode, input.metadata);
    const connections = modules.connections.deriveVisibleContextCanvasConnections(
      input.dataset,
      composition.visibleEntityIds,
      input.dataMode,
      input.metadata,
    );
    const snapshot = modules.exportPng.prepareContextCanvasExportSvg(
      input.dataset,
      composition,
      true,
      input.dataMode,
      input.metadata,
    );
    const representation = input.metadata.governedContext.representations[0];
    const row = rows.find((item) => item.id === `representation:${representation.representationId}`);
    requireCondition(Boolean(row), "explanation_example", "synthetic accessible explanation row is missing");
    const values = valuesByLabel(row);
    requireCondition(values.get("Publication state") === publicationState, "explanation_example", "synthetic explanation publication state differs");
    requireCondition(values.get("Governance decision") === (publicationState === "qualified" ? "QUALIFIED" : "PUBLISHED"), "explanation_example", "synthetic explanation governance decision differs");
    requireCondition(values.get("Meaning") === representation.explanation.longDefinition, "explanation_example", "synthetic accessible meaning differs");
    requireCondition(values.get("Why shown") === representation.explanation.whyShown, "explanation_example", "synthetic accessible why-shown text differs");
    requireCondition(values.get("Permitted interpretation") === representation.explanation.permittedInterpretation, "explanation_example", "synthetic accessible permitted interpretation differs");
    requireCondition(values.get("Prohibited interpretations") === representation.explanation.prohibitedInterpretations.join("; "), "explanation_example", "synthetic accessible prohibited interpretations differ");
    requireCondition(connections.length === 1 && connections[0].connectionKind === "context_representation", "explanation_example", "synthetic explanation connection class differs");
    requireCondition(snapshot.svg.includes(representation.explanation.accessibilityWording), "explanation_example", "synthetic export omits accessible explanation wording");
    validateExplanationText(explanation);
    return Object.freeze({
      accessible_equivalence: true,
      connection_label: EXPECTED_KIND[kind].connectionLabel,
      context_kind: kind,
      epistemic_role: "project_curated_context",
      example: publicationState === "qualified" ? "qualified_representation" : `${kind}_representation`,
      governance_decision: publicationState === "qualified" ? "QUALIFIED" : "PUBLISHED",
      prohibited_inference_guard: true,
      publication_state: publicationState,
    });
  }));
}

function buildSyntheticDto({ explanation, index, kind, projectionSha256, publicationState }) {
  const suffix = String(index + 1).padStart(64, String(index + 1));
  const prefix = EXPECTED_KIND[kind].prefix;
  const code = EXPECTED_KIND[kind].code;
  const label = `Synthetic ${kind.replaceAll("_", " ")} example`;
  const representationId = `CTXA:${suffix.slice(-64)}`;
  const termId = `CTX:${prefix}:${String(index + 5).repeat(64).slice(0, 64)}`;
  const provenanceId = `CTXP:${String(index + 9).repeat(64).slice(0, 64)}`;
  return Object.freeze({
    schemaVersion: "trace-context/v1",
    release: Object.freeze({
      researchReleaseId: SOURCE_RELEASE.id,
      researchManifestSha256: SOURCE_RELEASE.manifestSha256,
      contextProjectionId: PROJECTION_ID,
      contextProjectionSha256: projectionSha256,
    }),
    selectedRecord: Object.freeze({
      surfaceId: `SURF-CONTEXT-SYNTHETIC-EXAMPLE-${index + 1}`,
      title: "Synthetic selected record",
      rootMetadata: Object.freeze({
        creatorAttribution: "Synthetic source-reported attribution",
        dateDisplay: "Undated synthetic example",
        objectType: "Synthetic record",
        sourceName: "Synthetic verification source",
      }),
    }),
    availability: "ready",
    representations: Object.freeze([Object.freeze({
      id: representationId,
      kind,
      termId,
      label,
      epistemicRole: "project_curated_context",
      publicationState,
      explanationCode: code,
      provenance: Object.freeze({
        provenanceId,
        basis: "project_curated_typed_membership",
        sourceKind: EXPECTED_KIND[kind].sourceKind,
        sourceState: "proposed",
        mappingPolicyVersion: MAPPING_VERSION,
        governancePolicyVersion: POLICY_VERSION,
        decision: publicationState === "qualified" ? "QUALIFIED" : "PUBLISHED",
      }),
    })]),
    counts: Object.freeze({
      representations: 1,
      byKind: Object.freeze({
        medium: kind === "medium" ? 1 : 0,
        theme: kind === "theme" ? 1 : 0,
        movementContext: kind === "movement_context" ? 1 : 0,
      }),
    }),
    explanationRegistryVersion: "trace-context-explanations-v1",
    explanations: Object.freeze([explanation]),
    accessibleRows: Object.freeze([]),
  });
}

function validateExplanationText(explanation) {
  const required = [
    explanation.publicLabel,
    explanation.shortDefinition,
    explanation.longDefinition,
    explanation.sourceBasis,
    explanation.derivationDescription,
    explanation.permittedInterpretation,
    explanation.uiShortExplanation,
    explanation.methodPageExplanation,
    explanation.accessibilityWording,
  ];
  requireCondition(required.every((value) => typeof value === "string" && value.trim().length > 0), "explanation_text", "Context explanation contains empty required copy");
  requireCondition(Array.isArray(explanation.prohibitedInterpretations) && explanation.prohibitedInterpretations.length >= 5, "explanation_text", "Context explanation prohibited interpretations are incomplete");
  requireCondition(explanation.prohibitedInterpretations.every((value) => /\bdoes not\b|\bnot\b/iu.test(value)), "explanation_text", "Context prohibited interpretation is not explicitly negated");
  const positiveCopy = [
    explanation.shortDefinition,
    explanation.permittedInterpretation,
    explanation.uiShortExplanation,
    explanation.accessibilityWording,
  ].join(" ");
  requireCondition(!/\b(?:influenced|caused|proves|historically connected|belongs definitively to)\b/iu.test(positiveCopy), "prohibited_inference", "Context positive explanation copy makes a prohibited inference");
}

function validateExpectedCohort(cohort, manifest) {
  requireCondition(cohort.public_objects_tested === PUBLIC_OBJECT_COUNT, "public_census", "governed public object test count differs");
  requireCondition(cohort.failed_context_objects === 0, "failed_objects", "governed public object failures are non-zero");
  requireCondition(cohort.objects_with_context === PUBLIC_OBJECT_COUNT, "context_coverage", "governed Context object coverage differs");
  requireCondition(cohort.objects_with_only_one_representation === 0 && cohort.objects_with_multiple_representations === PUBLIC_OBJECT_COUNT, "context_coverage", "governed Context representation-depth coverage differs");
  requireCondition(cohort.representations === REPRESENTATION_COUNT, "representation_census", "governed representation count differs");
  requireCondition(cohort.publication_counts.published === REPRESENTATION_COUNT && cohort.publication_counts.qualified === 0 && cohort.publication_counts.held === 0 && cohort.publication_counts.excluded === 0, "publication_census", "governed publication census differs");
  requireCondition(cohort.same_kind_multivalue_objects === 6, "multivalue_census", "governed same-kind multivalue census differs");
  requireCondition(stableJson(cohort.object_histogram) === stableJson({ "2": 7_884, "3": 106, "4": 5 }), "workload_histogram", "governed representation histogram differs");
  for (const [kind, expected] of Object.entries(EXPECTED_KIND)) {
    requireCondition(cohort.by_kind[kind].objects === expected.objectCount, "kind_object_census", "governed kind object coverage differs");
    requireCondition(cohort.by_kind[kind].representations === expected.representationCount, "kind_representation_census", "governed kind representation count differs");
  }
  requireCondition(cohort.membership_node_count === 0 && cohort.membership_connection_count === 0, "membership_surface", "governed default Canvas exposes memberships");
  requireCondition(cohort.semantic_edge_count === 0 && cohort.semantic_connection_count === 0, "semantic_surface", "governed default Canvas exposes semantic edges");
  requireCondition(cohort.unexplained_nodes === 0 && cohort.unknown_term_ids === 0 && cohort.provenance_failures === 0 && cohort.api_serialization_failures === 0 && cohort.internal_id_exposure_count === 0, "zero_failure_counters", "governed validation failure counter is non-zero");
  requireCondition(stableJson(manifest.counts.representationHistogram) === stableJson(cohort.object_histogram), "manifest_census", "governed manifest histogram differs from full cohort");
}

function corpusComparable(cohort) {
  return cohort;
}

function deterministicCohortSummary(stats) {
  return Object.freeze({
    api_serialization_failures: stats.apiSerializationFailures,
    by_kind: Object.freeze(Object.fromEntries(Object.entries(stats.byKind)
      .map(([kind, value]) => [kind, Object.freeze({ ...value })]))),
    failed_context_objects: stats.failedObjects,
    internal_id_exposure_count: stats.internalIdExposureCount,
    membership_connection_count: stats.membershipConnectionCount,
    membership_node_count: stats.membershipNodeCount,
    object_histogram: Object.freeze({ ...stats.objectHistogram }),
    objects_with_context: stats.objectsWithContext,
    objects_with_only_one_representation: stats.objectHistogram[1] ?? 0,
    objects_with_multiple_representations:
      stats.publicObjectsTested - (stats.objectHistogram[1] ?? 0),
    provenance_failures: stats.provenanceFailures,
    publication_counts: Object.freeze({ ...stats.publicationCounts }),
    public_objects_tested: stats.publicObjectsTested,
    representations: stats.representations,
    same_kind_multivalue_objects: stats.sameKindMultivalueObjects,
    semantic_connection_count: stats.semanticConnectionCount,
    semantic_edge_count: stats.semanticEdgeCount,
    term_assignment_counts_sha256: sha256(stableJson(Object.fromEntries([...stats.termAssignmentCounts].sort(([left], [right]) => compareText(left, right))))),
    unexplained_nodes: stats.unexplainedNodes,
    unknown_term_ids: stats.unknownTermIds,
  });
}

function buildPerformanceSummary({ coldLoadMs, firstPass, readerHeapDeltaBytes, readerImportMs }) {
  const values = firstPass.stats.distributions;
  return Object.freeze({
    api_serialization_ms: summarizeDistribution(values.api_serialization_ms),
    canvas_total_ms: summarizeDistribution(values.canvas_total_ms),
    cold_index_validation_ms: rounded(coldLoadMs),
    export_ms: summarizeDistribution(values.export_ms),
    geometry_ms: summarizeDistribution(values.geometry_ms),
    layout_ms: summarizeDistribution(values.layout_ms),
    reader_heap_delta_bytes: readerHeapDeltaBytes,
    reader_import_ms: rounded(readerImportMs),
    warm_public_lookup_ms: summarizeDistribution(values.lookup_ms),
  });
}

function validateCompactRuntime(performanceSummary, artifactSummary, historicalBaseline) {
  requireCondition(artifactSummary.governed_projection_raw_bytes < artifactSummary.source_database_bytes / 10, "compact_projection", "governed projection is not substantially smaller than the frozen source database");
  requireCondition(artifactSummary.governed_projection_raw_bytes < 25 * 1024 * 1024, "compact_projection", "governed projection raw payload exceeds the closure budget");
  requireCondition(artifactSummary.governed_projection_gzip_bytes < 3 * 1024 * 1024, "compact_projection", "governed projection gzip payload exceeds the closure budget");
  requireCondition(Number.isFinite(performanceSummary.warm_public_lookup_ms.p95), "runtime_measurement", "governed lookup p95 is unavailable");
  requireCondition(performanceSummary.reader_heap_delta_bytes < historicalBaseline.round2_source_index_heap_delta_bytes, "compact_runtime", "governed reader heap is not smaller than the Round 2 validation loader");
}

async function loadHistoricalBaseline() {
  const summary = JSON.parse(await readFile(roundTwoSummaryPath, "utf8"));
  const loader = JSON.parse(await readFile(roundTwoLoaderPath, "utf8"));
  return Object.freeze({
    round2_default_connections_p50: summary.validation.payload_distribution.connection_count.p50,
    round2_default_nodes_p50: summary.validation.payload_distribution.entity_count.p50,
    round2_source_index_heap_delta_bytes: loader.heap_delta_bytes,
  });
}

async function validateComponentContracts() {
  const inspector = await readFile(join(canvasRoot, "ContextCanvasInspector.tsx"), "utf8");
  const palette = await readFile(join(canvasRoot, "ContextEntityPalette.tsx"), "utf8");
  for (const field of [
    "Meaning",
    "Why shown",
    "Epistemic role",
    "Source basis",
    "Source state",
    "Governance decision",
    "Context publication",
    "Permitted interpretation",
    "Prohibited interpretations",
    "Explanation code",
    "Public provenance ID",
  ]) requireCondition(inspector.includes(field), "inspector_contract", `governed inspector field is missing: ${field}`);
  requireCondition(inspector.includes('case "context_representation"'), "inspector_contract", "governed connection inspector branch is missing");
  requireCondition(palette.includes("representationByEntityId"), "palette_contract", "governed palette representation metadata is missing");
  requireCondition(palette.includes("representation.explanation.accessibilityWording"), "palette_contract", "governed palette accessibility explanation is missing");
  return Object.freeze({
    inspector_explainability_fields: 11,
    inspector_governed_connection_branch: true,
    palette_accessibility_wording: true,
  });
}

async function validateClientBoundary(requireBuild) {
  const srcRoot = join(frontendRoot, "src");
  const files = (await walkFiles(srcRoot)).filter((path) => [".js", ".jsx", ".mjs", ".ts", ".tsx"].includes(extname(path)));
  const sourceByPath = new Map(await Promise.all(files.map(async (path) => [path, await readFile(path, "utf8")])));
  const roots = [...sourceByPath].filter(([, source]) => /^\s*["']use client["'];/u.test(source)).map(([path]) => path);
  const visited = new Set();
  const queue = [...roots];
  while (queue.length > 0) {
    const path = queue.shift();
    if (!path || visited.has(path)) continue;
    visited.add(path);
    const source = sourceByPath.get(path);
    if (!source) continue;
    for (const specifier of extractRuntimeImportSpecifiers(source)) {
      const resolvedPath = resolveSourceImport(path, specifier, sourceByPath);
      if (resolvedPath && !visited.has(resolvedPath)) queue.push(resolvedPath);
    }
  }
  const forbiddenClientNodes = [...visited].filter((path) =>
    path.includes("/generated/trace-context-v1/")
    || path.endsWith("reader.server.ts")
    || path.endsWith("source-index.server.ts")
    || path.includes("/realdata/"));
  requireCondition(forbiddenClientNodes.length === 0, "client_source_graph", "server-only Context corpus entered the client source graph");
  const clientText = [...visited].map((path) => sourceByPath.get(path) ?? "").join("\n");
  requireCondition(!clientText.includes("generated/trace-context-v1") && !clientText.includes("reader.server") && !clientText.includes("source-index.server"), "client_source_graph", "client source graph references a server-only Context loader");

  const readerText = await readFile(join(contextRoot, "governed/reader.server.ts"), "utf8");
  requireCondition(
    !readerText.includes("realdata/source-index")
    && !readerText.includes("source-index.server")
    && !readerText.includes("node:sqlite"),
    "heavy_loader_path",
    "governed reader depends on the heavy validation loader",
  );

  let staticFilesScanned = 0;
  let staticBytesScanned = 0;
  if (requireBuild) {
    const staticRoot = join(frontendRoot, ".next/static");
    const staticFiles = (await walkFiles(staticRoot)).filter((path) => [".js", ".mjs", ".css"].includes(extname(path)));
    requireCondition(staticFiles.length > 0, "build_bundle_guard", "production .next static bundle is unavailable");
    const forbiddenMarkers = [
      "trace-context-public-id-v1",
      "trace-context-projection-generator-v1",
      "governedProjectionRawBytes",
      "CTXA:261727efef0ebbfe014728d0449679c3f9a5181c751c3bfdf26ca41df1d4300e",
      "CTX:MEDIUM:ec43be41480c2b71aed82179a5acadf2ea7fb318cfa7ac9b2bfbdc9bbd66294c",
    ];
    for (const path of staticFiles) {
      const bytes = await readFile(path);
      const text = bytes.toString("utf8");
      staticFilesScanned += 1;
      staticBytesScanned += bytes.byteLength;
      requireCondition(!forbiddenMarkers.some((marker) => text.includes(marker)), "build_bundle_guard", "full governed Context corpus marker entered a production static asset");
    }
  }
  return Object.freeze({
    bundle_status: requireBuild ? "PRODUCTION_STATIC_PASS" : "SOURCE_GRAPH_PASS",
    client_entry_roots: roots.length,
    client_graph_modules: visited.size,
    full_context_corpus_in_client_bundle: false,
    heavy_validation_loader_in_public_read_path: false,
    production_static_bytes_scanned: staticBytesScanned,
    production_static_files_scanned: staticFilesScanned,
    production_static_required: requireBuild,
  });
}

function buildInvariantResults({ artifactSummary, clientBoundary, cohort, generatorSummary, heldSummary, manifest }) {
  const descriptions = [
    "Every visible governed Context node has a registered explanation.",
    "Every visible governed Context node has a stable governed public ID.",
    "No validation-only ctxv49 ID appears in governed DTOs.",
    "No internal folder ID or UUID appears in governed DTOs.",
    "Curated memberships are provenance, not default Canvas nodes.",
    "Region is absent from Context V1 and registered for Spacetime handoff.",
    "Every Context representation is explicitly project-curated.",
    "No Context representation becomes a semantic relation.",
    "Real semantic-edge count remains zero.",
    "Every movement representation has an explicit governance decision.",
    "Every term belongs to exactly one governed Context kind.",
    "No held object enters the governed projection.",
    "Held and unknown lookups remain fail-closed.",
    "Every governed representation resolves provenance.",
    "Every representation resolves a publication state.",
    "Every public DTO is release/projection pinned.",
    "Governed rebuild is deterministic.",
    "Full Context projection is absent from the initial client bundle.",
    "Default governed Canvas contains zero membership nodes.",
    "Default governed Canvas contains zero semantic edges.",
    "Accessible explanation is semantically equivalent to visual explanation.",
    "Context publication does not mutate frozen v49 source state.",
  ];
  const evidence = [
    `visible representations checked=${cohort.representations}; unexplained=0`,
    `representations checked=${cohort.representations}; ID failures=0`,
    "validation ID exposure=0",
    "internal identity exposure=0",
    "membership provenance only; default nodes=0",
    "Context Region nodes=0; Spacetime handoff terms=93",
    `project-curated representations=${cohort.representations}`,
    "representation connection class=context_representation",
    `real semantic edges=${manifest.realSemanticEdgeCount}`,
    `movement decisions=${cohort.by_kind.movement_context.representations}`,
    `terms checked=${TERM_COUNT}; collisions=${artifactSummary.term_collision_count}`,
    `held exclusions checked=${heldSummary.held_lookups}; exposed=0`,
    `held/unknown parity failures=${heldSummary.held_unknown_parity_failures}`,
    `provenance checked=${cohort.representations}; failures=0`,
    `publication states checked=${cohort.representations}; failures=0`,
    `release/projection-pinned DTOs=${cohort.public_objects_tested}`,
    `in-memory rebuilds=${generatorSummary.rebuild_runs}; checksum match=true`,
    `client modules checked=${clientBoundary.client_graph_modules}; corpus exposure=false`,
    `default membership nodes=${cohort.membership_node_count}`,
    `default semantic connections=${cohort.semantic_connection_count}`,
    `accessible/visual representations checked=${cohort.representations}; failures=0`,
    `source state=${manifest.canonicalSourceState}; frozen checksum failures=0`,
  ];
  return Object.freeze(descriptions.map((description, index) => Object.freeze({
    description,
    evidence: evidence[index],
    id: `CTX-GOV-INV-${String(index + 1).padStart(3, "0")}`,
    status: "PASS",
  })));
}

function buildEvidence({
  artifactSummary,
  clientBoundary,
  cohort,
  componentContract,
  explanationExamples,
  frozenSource,
  generatorSummary,
  heldSummary,
  historicalBaseline,
  invariants,
  manifest,
  performanceSummary,
  firstPass,
}) {
  const workload = Object.freeze({
    accessible_rows: summarizeDistribution(firstPass.stats.distributions.accessible_rows),
    api_bytes: summarizeDistribution(firstPass.stats.distributions.api_bytes),
    dto_bytes: summarizeDistribution(firstPass.stats.distributions.dto_bytes),
    export_svg_bytes: summarizeDistribution(firstPass.stats.distributions.export_bytes),
    total_connections: summarizeDistribution(firstPass.stats.distributions.total_connections),
    total_nodes: summarizeDistribution(firstPass.stats.distributions.total_nodes),
    visible_representations: summarizeDistribution(firstPass.stats.distributions.visible_representations),
  });
  const summary = Object.freeze({
    closure_decision: "CONTEXT_V1_CLOSED",
    context_data_mode: "governed_context_v1",
    context_projection_id: PROJECTION_ID,
    context_projection_sha256: manifest.projectionSha256,
    context_schema_version: "trace-context/v1",
    cohort,
    default_template: Object.freeze({
      entity_selection_rule: "all-governed-representations",
      template_id: "context-overview",
      template_version: 2,
    }),
    deterministic: generatorSummary,
    explanation_registry_version: manifest.explanationRegistryVersion,
    governed_projection_gzip_bytes: artifactSummary.governed_projection_gzip_bytes,
    governed_projection_raw_bytes: artifactSummary.governed_projection_raw_bytes,
    held_lookup: heldSummary,
    policy_sha256: manifest.governancePolicySha256,
    policy_version: POLICY_VERSION,
    region_handoff: Object.freeze({
      context_node_count: 0,
      decision: "DEFER_TO_SPACETIME",
      public_row_count: REGION_ROW_COUNT,
      term_count: REGION_TERM_COUNT,
    }),
    source_release: SOURCE_RELEASE,
    status: "PASS",
  });
  return Object.freeze({
    artifactSummary,
    assignmentGovernanceRows: buildAssignmentGovernanceRows(),
    bundle: clientBoundary,
    censusRows: buildCensusRows(cohort, heldSummary, artifactSummary),
    componentContract,
    explanationExamples,
    historicalBaseline,
    invariants,
    performance: performanceSummary,
    regionHandoffRows: frozenSource.regionHandoffRows,
    summary,
    termRegistryRows: buildTermRegistryRows(),
    workload,
  });

  function buildTermRegistryRows() {
    const terms = JSON.parse(readFileSyncSmall(join(generatedRoot, "terms.json"))).terms;
    return Object.freeze(terms.map((term) => Object.freeze({
      assignment_count: term.assignmentCount,
      context_kind: term.kind,
      explanation_code: term.explanationCode,
      governance_decision: "PUBLISHED",
      governed_term_id: term.id,
      public_label: term.label,
      publication_state: term.publicationState,
    })));
  }

  function buildAssignmentGovernanceRows() {
    return Object.freeze(buildTermRegistryRows().map((term) => Object.freeze({
      context_kind: term.context_kind,
      excluded_assignments: 0,
      governed_term_id: term.governed_term_id,
      governance_decision: term.governance_decision,
      held_assignments: 0,
      proposed_source_assignments: term.assignment_count,
      public_label: term.public_label,
      published_assignments: term.assignment_count,
      qualified_assignments: 0,
      total_assignments: term.assignment_count,
    })));
  }
}

function readFileSyncSmall(path) {
  return createRequire(import.meta.url)("node:fs").readFileSync(path, "utf8");
}

function buildCensusRows(cohort, heldSummary, artifactSummary) {
  const rows = [
    ["objects", "public_tested", cohort.public_objects_tested],
    ["objects", "held_lookup_tested", heldSummary.held_lookups],
    ["objects", "held_exposed", heldSummary.held_objects_exposed],
    ["objects", "with_context", cohort.objects_with_context],
    ["terms", "total", TERM_COUNT],
    ["representations", "total", cohort.representations],
    ["representations", "published", cohort.publication_counts.published],
    ["representations", "qualified", cohort.publication_counts.qualified],
    ["representations", "held", cohort.publication_counts.held],
    ["representations", "excluded", cohort.publication_counts.excluded],
    ["canvas", "membership_nodes", cohort.membership_node_count],
    ["canvas", "semantic_edges", cohort.semantic_edge_count],
    ["region", "spacetime_handoff_terms", REGION_TERM_COUNT],
    ["region", "spacetime_handoff_rows", REGION_ROW_COUNT],
    ["projection", "raw_bytes", artifactSummary.governed_projection_raw_bytes],
    ["projection", "gzip_bytes", artifactSummary.governed_projection_gzip_bytes],
  ];
  for (const [kind, values] of Object.entries(cohort.by_kind)) {
    rows.push([kind, "objects", values.objects]);
    rows.push([kind, "representations", values.representations]);
    rows.push([kind, "terms", EXPECTED_KIND[kind].termCount]);
  }
  return Object.freeze(rows.map(([category, metric, value]) => Object.freeze({ category, metric, value })));
}

async function writeEvidence(directory, evidence) {
  await mkdir(directory, { recursive: true });
  const files = new Map();
  files.set("context-governance-full-cohort-summary.json", jsonBytes(evidence.summary));
  files.set("context-governance-performance.json", jsonBytes(evidence.performance));
  files.set("context-governance-bundle-guard.json", jsonBytes(evidence.bundle));
  files.set("context-governance-explanation-examples.json", jsonBytes(evidence.explanationExamples));
  files.set("context-governance-invariants.tsv", Buffer.from(
    "invariant_id\tstatus\tdescription\tevidence\n"
    + evidence.invariants.map((item) => tsvRow([item.id, item.status, item.description, item.evidence])).join("\n")
    + "\n",
    "utf8",
  ));
  files.set("context-governance-census.tsv", Buffer.from(
    "category\tmetric\tvalue\n"
    + evidence.censusRows.map((row) => tsvRow([row.category, row.metric, row.value])).join("\n")
    + "\n",
    "utf8",
  ));
  files.set("context-governance-workload.tsv", Buffer.from(
    "metric\tpopulation\tp50\tp90\tp95\tp99\tmax\n"
    + Object.entries(evidence.workload).map(([metric, value]) => tsvRow([
      metric,
      value.count,
      value.p50,
      value.p90,
      value.p95,
      value.p99,
      value.max,
    ])).join("\n")
    + "\n",
    "utf8",
  ));
  files.set("CONTEXT_TERM_REGISTRY.tsv", Buffer.from(
    "governed_term_id\tcontext_kind\tpublic_label\texplanation_code\tpublication_state\tassignment_count\tgovernance_decision\n"
    + evidence.termRegistryRows.map((row) => tsvRow([
      row.governed_term_id,
      row.context_kind,
      row.public_label,
      row.explanation_code,
      row.publication_state,
      row.assignment_count,
      row.governance_decision,
    ])).join("\n")
    + "\n",
    "utf8",
  ));
  files.set("CONTEXT_ASSIGNMENT_GOVERNANCE_SUMMARY.tsv", Buffer.from(
    "governed_term_id\tcontext_kind\tpublic_label\ttotal_assignments\tpublished_assignments\tqualified_assignments\theld_assignments\texcluded_assignments\tproposed_source_assignments\tgovernance_decision\n"
    + evidence.assignmentGovernanceRows.map((row) => tsvRow([
      row.governed_term_id,
      row.context_kind,
      row.public_label,
      row.total_assignments,
      row.published_assignments,
      row.qualified_assignments,
      row.held_assignments,
      row.excluded_assignments,
      row.proposed_source_assignments,
      row.governance_decision,
    ])).join("\n")
    + "\n",
    "utf8",
  ));
  files.set("SPACETIME_REGION_HANDOFF.tsv", Buffer.from(
    "handoff_id\tpublic_label\tpublic_row_count\tdecision\n"
    + evidence.regionHandoffRows.map((row) => tsvRow([
      row.handoff_id,
      row.public_label,
      row.public_row_count,
      row.decision,
    ])).join("\n")
    + "\n",
    "utf8",
  ));
  files.set("context-governance-failures.tsv", Buffer.from(evidenceFailureHeader, "utf8"));
  files.set("context-governance-gate-summary.txt", Buffer.from([
    "CONTEXT_GOVERNANCE_V1=PASS",
    "CONTEXT_V1_DECISION=CONTEXT_V1_CLOSED",
    `PUBLIC_OBJECTS_TESTED=${evidence.summary.cohort.public_objects_tested}`,
    `HELD_LOOKUPS=${evidence.summary.held_lookup.held_lookups}`,
    `HELD_OBJECTS_EXPOSED=${evidence.summary.held_lookup.held_objects_exposed}`,
    `FAILED_CONTEXT_OBJECTS=${evidence.summary.cohort.failed_context_objects}`,
    "UNEXPLAINED_NODES=0",
    "UNKNOWN_TERM_IDS=0",
    "PROVENANCE_FAILURES=0",
    "API_SERIALIZATION_FAILURES=0",
    "DEFAULT_VISIBLE_MEMBERSHIP_NODE_COUNT=0",
    "DEFAULT_VISIBLE_SEMANTIC_EDGE_COUNT=0",
    `PROJECTION_SHA256=${evidence.summary.context_projection_sha256}`,
    "",
  ].join("\n"), "utf8"));

  for (const [filename, bytes] of files) await writeFile(join(directory, filename), bytes);
  const receiptMaterial = [...files].sort(([left], [right]) => compareText(left, right))
    .map(([filename, bytes]) => `${filename}\t${bytes.byteLength}\t${sha256(bytes)}`)
    .join("\n") + "\n";
  return Object.freeze({ fileCount: files.size, sha256: sha256(receiptMaterial) });
}

async function writeFailureEvidence(directory, failures) {
  await mkdir(directory, { recursive: true });
  const body = evidenceFailureHeader + failures.map((row) => tsvRow([
    row.pass,
    row.ordinal,
    row.bugClass,
    row.message,
  ])).join("\n") + "\n";
  await writeFile(join(directory, "context-governance-failures.tsv"), body, "utf8");
}

function assertEvidenceSanitized(evidence) {
  const values = {
    artifactSummary: evidence.artifactSummary,
    bundle: evidence.bundle,
    censusRows: evidence.censusRows,
    componentContract: evidence.componentContract,
    explanationExamples: evidence.explanationExamples,
    historicalBaseline: evidence.historicalBaseline,
    invariants: evidence.invariants,
    performance: evidence.performance,
    summary: evidence.summary,
    workload: evidence.workload,
  };
  const text = JSON.stringify(values);
  requireCondition(!PUBLIC_ID_IN_TEXT_PATTERN.test(text) && !UUID_PATTERN.test(text) && !VALIDATION_ID_PATTERN.test(text) && !RAW_FOLDER_ID_PATTERN.test(text), "evidence_safety", "aggregate evidence contains a record/private identity");
  const regionText = JSON.stringify(evidence.regionHandoffRows);
  requireCondition(!regionText.includes("SURF-") && !regionText.includes("FOL-") && !UUID_PATTERN.test(regionText), "evidence_safety", "Spacetime handoff evidence contains a record/private identity");
  requireCondition(evidence.regionHandoffRows.length === REGION_TERM_COUNT, "evidence_census", "Spacetime handoff evidence row count differs");
  requireCondition(evidence.termRegistryRows.length === TERM_COUNT && evidence.assignmentGovernanceRows.length === TERM_COUNT, "evidence_census", "Context registry evidence row count differs");
}

function publicTermId(kind, privateIdentity) {
  const expected = EXPECTED_KIND[kind];
  requireCondition(Boolean(expected), "term_kind", "unsupported public term kind");
  return `CTX:${expected.prefix}:${sha256([`${ID_POLICY_VERSION}:term`, kind, privateIdentity].join("\u0000"))}`;
}

function publicRepresentationId(surfaceId, kind, termId) {
  return `CTXA:${sha256([`${ID_POLICY_VERSION}:representation`, surfaceId, kind, termId].join("\u0000"))}`;
}

function publicProvenanceId(representationId) {
  return `CTXP:${sha256([PROVENANCE_NAMESPACE, representationId].join("\u0000"))}`;
}

function collectKeys(value, keys = new Set()) {
  if (!value || typeof value !== "object") return keys;
  for (const [key, child] of Object.entries(value)) {
    keys.add(key);
    collectKeys(child, keys);
  }
  return keys;
}

function valuesByLabel(row) {
  return new Map(row.values.map((item) => [item.label, item.value]));
}

function normalizeLabel(value) {
  return value.normalize("NFKC").trim().replace(/\s+/gu, " ").replace(/[\p{P}\p{S}]/gu, "").toLocaleLowerCase("en");
}

function compareText(left, right) {
  return left < right ? -1 : left > right ? 1 : 0;
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

async function sha256File(path) {
  const digest = createHash("sha256");
  for await (const chunk of createReadStream(path)) digest.update(chunk);
  return digest.digest("hex");
}

function updateHash(hasher, value) {
  const bytes = Buffer.from(String(value), "utf8");
  const length = Buffer.allocUnsafe(8);
  length.writeBigUInt64BE(BigInt(bytes.byteLength));
  hasher.update(length).update(bytes);
}

function stableJson(value) {
  return JSON.stringify(canonicalValue(value));
}

function canonicalValue(value) {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value)
      .sort(([left], [right]) => compareText(left, right))
      .map(([key, child]) => [key, canonicalValue(child)]));
  }
  return value;
}

function jsonBytes(value) {
  return Buffer.from(`${JSON.stringify(canonicalValue(value), null, 2)}\n`, "utf8");
}

function summarizeDistribution(values) {
  const sorted = [...values].sort((left, right) => left - right);
  if (sorted.length === 0) return Object.freeze({ count: 0, max: 0, p50: 0, p90: 0, p95: 0, p99: 0 });
  return Object.freeze({
    count: sorted.length,
    max: rounded(sorted.at(-1)),
    p50: rounded(percentile(sorted, 0.5)),
    p90: rounded(percentile(sorted, 0.9)),
    p95: rounded(percentile(sorted, 0.95)),
    p99: rounded(percentile(sorted, 0.99)),
  });
}

function percentile(sorted, quantile) {
  if (sorted.length === 0) return 0;
  const index = Math.min(sorted.length - 1, Math.max(0, Math.ceil(sorted.length * quantile) - 1));
  return sorted[index];
}

function rounded(value) {
  return Number(Number(value).toFixed(3));
}

function formatMs(value) {
  return rounded(value).toFixed(3);
}

function sum(values) {
  return values.reduce((total, value) => total + value, 0);
}

function countOccurrences(text, needle) {
  if (!needle) return 0;
  let count = 0;
  let index = 0;
  while ((index = text.indexOf(needle, index)) >= 0) {
    count += 1;
    index += needle.length;
  }
  return count;
}

function tsvRow(values) {
  return values.map((value) => String(value ?? "")
    .replaceAll("\t", " ")
    .replaceAll("\r", " ")
    .replaceAll("\n", " ")).join("\t");
}

function sanitizeFailureMessage(error) {
  const message = error instanceof Error ? error.message : String(error);
  return message
    .replace(/SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*/gu, "[public-record]")
    .replace(/(?:CTXA|CTXP):[0-9a-f]{64}/giu, "[governed-id]")
    .replace(/CTX:(?:MEDIUM|THEME|MOVEMENT):[0-9a-f]{64}/giu, "[governed-term]")
    .replace(/FOL-(?:MEDIUM|THEME|MOVEMENT|REGION)-[A-Z0-9-]+/giu, "[source-term]")
    .replace(UUID_PATTERN, "[internal-id]")
    .replace(/[\t\r\n]+/gu, " ")
    .slice(0, 400);
}

async function walkFiles(root) {
  const output = [];
  const entries = await readdir(root, { withFileTypes: true });
  for (const entry of entries) {
    const path = join(root, entry.name);
    if (entry.isDirectory()) output.push(...await walkFiles(path));
    else if (entry.isFile()) output.push(path);
  }
  return output;
}

function extractRuntimeImportSpecifiers(source) {
  const withoutTypes = source
    .replace(/\bimport\s+type\b[\s\S]*?\bfrom\s*["'][^"']+["'];?/gu, "")
    .replace(/\bexport\s+type\b[\s\S]*?\bfrom\s*["'][^"']+["'];?/gu, "");
  const specifiers = new Set();
  const patterns = [
    /\b(?:import|export)\s+(?!type\b)[\s\S]*?\bfrom\s*["']([^"']+)["']/gu,
    /\bimport\s*["']([^"']+)["']/gu,
    /\bimport\s*\(\s*["']([^"']+)["']\s*\)/gu,
  ];
  for (const pattern of patterns) {
    for (const match of withoutTypes.matchAll(pattern)) specifiers.add(match[1]);
  }
  return [...specifiers];
}

function resolveSourceImport(importer, specifier, sourceByPath) {
  let base;
  if (specifier.startsWith("@/")) base = join(frontendRoot, "src", specifier.slice(2));
  else if (specifier.startsWith(".")) base = resolve(dirname(importer), specifier);
  else return null;
  const candidates = [
    base,
    ...[".ts", ".tsx", ".js", ".jsx", ".mjs"].map((extension) => `${base}${extension}`),
    ...[".ts", ".tsx", ".js", ".jsx", ".mjs"].map((extension) => join(base, `index${extension}`)),
  ];
  return candidates.find((candidate) => sourceByPath.has(candidate)) ?? null;
}
