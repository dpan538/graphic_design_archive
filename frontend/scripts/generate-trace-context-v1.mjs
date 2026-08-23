import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { createReadStream } from "node:fs";
import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(here, "..");
const repositoryRoot = resolve(frontendRoot, "..");
const outputDirectory = join(frontendRoot, "generated/trace-context-v1");

const args = process.argv.slice(2);
const checkOnly = args.includes("--check");
assert.deepEqual(args.filter((arg) => arg !== "--check"), [], "unknown generator argument");

const CONTEXT_SCHEMA_VERSION = "trace-context/v1";
const POLICY_SCHEMA_VERSION = "trace-context-governance-policy/v1";
const POLICY_VERSION = "context-governance-v1";
const PROJECTION_ID = "trace-context-v1";
const ID_POLICY_VERSION = "trace-context-public-id-v1";
const MAPPING_VERSION = "trace-context-governance-mapping-v1";
const GENERATOR_VERSION = "trace-context-projection-generator-v1";
const EXPLANATION_REGISTRY_VERSION = "trace-context-explanations-v1";
const ROOT_TEXT_POLICY_VERSION = "trace-context-root-text-v1";
const PROVENANCE_ID_NAMESPACE = "trace-context-provenance-v1";
const PUBLISHED_PROVENANCE_DECISION = "PUBLISHED";
const CANONICAL_SERIALIZATION =
  "recursive-key-sort;array-order-preserved;json-minified;final-lf;utf8";

const SOURCE_RELEASE = Object.freeze({
  id: "v49-api-contract-fresh-c",
  manifestSha256: "4addfdb3cb9314587908096572242b9d63e9cef9e6e1be68c0c646491a43a90a",
});
const FROZEN_INPUT_SHA256 = Object.freeze({
  "data/prefreeze_candidate_v48.sqlite":
    "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e",
  "database/FREEZE_V49.json":
    "f0dda59dd515ba243eaf213bce9f42513727f1ab0a44685635921c3759a7d22e",
  "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv":
    "48f98f68ca2ec0cef96c82ecc9c01e4129eb9a3f91e08b07ad9a59644a9d4e01",
});
const RELEASE_PROFILE = Object.freeze({
  path: "docs/statistics/v49-release-data-profile.json",
  sha256: "091dba486c2096f99c332b03cf9586139f1bc26594bce4e1575d2b1ddc8fea0f",
});

const EXPECTED = Object.freeze({
  canonicalObjects: 15_923,
  publicObjects: 7_995,
  heldObjects: 7_928,
  canonicalFolderRows: 47_982,
  publicFolderRows: 24_102,
  publicControlledAssignments: 16_106,
  heldControlledAssignmentRows: 15_952,
  publicRegionRows: 7_996,
  heldRegionRows: 7_928,
  publicTerms: 25,
  publicRegionTerms: 93,
  groupedPublicRecords: 15,
  themeMultivalueRecords: 1,
  movementMultivalueRecords: 5,
});
const EXPECTED_KIND_COUNTS = Object.freeze({
  assignments: Object.freeze({ medium: 7_995, movement_context: 115, theme: 7_996 }),
  objects: Object.freeze({ medium: 7_995, movement_context: 110, theme: 7_995 }),
  terms: Object.freeze({ medium: 10, movement_context: 7, theme: 8 }),
});

const SOURCE_TO_PUBLIC_KIND = Object.freeze({
  medium: "medium",
  movement: "movement_context",
  theme: "theme",
});
const KIND_ORDER = Object.freeze(["medium", "theme", "movement_context"]);
const KIND_PREFIX = Object.freeze({
  medium: "MEDIUM",
  movement_context: "MOVEMENT",
  theme: "THEME",
});
const EXPLANATION_CODE = Object.freeze({
  medium: "CTX-MEDIUM",
  movement_context: "CTX-MOVEMENT",
  theme: "CTX-THEME",
});
const PUBLIC_STABLE_ID_PATTERN = /^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$/u;
const PUBLIC_STABLE_ID_IN_TEXT_PATTERN = /\bSURF-[A-Z0-9]+(?:-[A-Z0-9]+)*\b/gu;
const SOURCE_TERM_ID_PATTERN = /^FOL-(?:MEDIUM|THEME|MOVEMENT|REGION)-[A-Z0-9]+(?:-[A-Z0-9]+)*$/u;
const SHA256_PATTERN = /^[0-9a-f]{64}$/u;
const UUID_PATTERN = /\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b/iu;
const URL_PATTERN = /(?:https?:\/\/|www\.)/iu;
const RAW_SOURCE_TERM_PATTERN = /\bFOL-(?:MEDIUM|THEME|MOVEMENT|REGION)-/u;
const VALID_OUTPUT_FILES = Object.freeze([
  "CHECKSUMS.sha256",
  "exception-register.json",
  "explanation-registry.json",
  "governance-policy.json",
  "manifest.json",
  "records.json",
  "terms.json",
]);

try {
  if (checkOnly) await checkProjection();
  else await writeProjection();
} catch (error) {
  console.error(`TRACE_CONTEXT_V1_GENERATION=FAIL ERROR=${safeError(error)}`);
  process.exitCode = 1;
}

async function writeProjection() {
  const built = await buildProjection();
  await mkdir(outputDirectory, { recursive: true });
  for (const [filename, bytes] of [...built.files].sort(([left], [right]) => compareText(left, right))) {
    await writeFile(join(outputDirectory, filename), bytes);
  }
  printReceipt("WRITE", built);
}

async function checkProjection() {
  const first = await buildProjection();
  const second = await buildProjection();
  assert.equal(first.files.size, second.files.size, "in-memory artifact count changed");
  for (const [filename, firstBytes] of first.files) {
    const secondBytes = second.files.get(filename);
    assert(secondBytes, `second build omitted ${filename}`);
    assert.equal(
      Buffer.compare(firstBytes, secondBytes),
      0,
      `in-memory deterministic rebuild mismatch: ${filename}`,
    );
  }

  const committedFiles = (await readdir(outputDirectory)).sort(compareText);
  assert.deepEqual(committedFiles, [...VALID_OUTPUT_FILES], "committed artifact file set differs");
  for (const [filename, expectedBytes] of first.files) {
    const actualBytes = await readFile(join(outputDirectory, filename));
    assert.equal(
      Buffer.compare(actualBytes, expectedBytes),
      0,
      `committed generated artifact differs: ${filename}`,
    );
  }
  printReceipt("CHECK", first);
}

async function buildProjection() {
  const source = await readAndValidateSource();
  const policy = buildGovernancePolicy();
  const explanationRegistry = buildExplanationRegistry();
  const exceptionRegister = buildExceptionRegister(source);
  const { termsDocument, termBySourceIdentity } = buildTerms(source);
  const recordsDocument = buildRecords(source, termBySourceIdentity);

  validateProjectionDocuments({
    exceptionRegister,
    explanationRegistry,
    policy,
    recordsDocument,
    source,
    termsDocument,
  });

  const coreValues = new Map([
    ["exception-register.json", exceptionRegister],
    ["explanation-registry.json", explanationRegistry],
    ["governance-policy.json", policy],
    ["records.json", recordsDocument],
    ["terms.json", termsDocument],
  ]);
  const coreFiles = new Map(
    [...coreValues].map(([filename, value]) => [filename, canonicalJsonBytes(value)]),
  );
  const artifactSha256 = Object.freeze(Object.fromEntries(
    [...coreFiles].sort(([left], [right]) => compareText(left, right))
      .map(([filename, bytes]) => [filename, sha256(bytes)]),
  ));
  const artifactBytes = Object.freeze(Object.fromEntries(
    [...coreFiles].sort(([left], [right]) => compareText(left, right))
      .map(([filename, bytes]) => [filename, bytes.byteLength]),
  ));
  const governedProjectionRawBytes = sum([...coreFiles.values()].map((bytes) => bytes.byteLength));
  const governedProjectionGzipBytes = sum(
    [...coreFiles.values()].map((bytes) => deterministicGzip(bytes).byteLength),
  );
  const recordsBytes = coreFiles.get("records.json");
  assert(recordsBytes, "records artifact bytes are missing");

  const counts = buildCounts(source, recordsDocument, termsDocument);
  const projectionHashMaterial = Object.freeze({
    artifactSha256,
    contextSchemaVersion: CONTEXT_SCHEMA_VERSION,
    counts,
    generatorVersion: GENERATOR_VERSION,
    governedProjectionGzipBytes,
    governedProjectionRawBytes,
    governancePolicySha256: artifactSha256["governance-policy.json"],
    governancePolicyVersion: POLICY_VERSION,
    idPolicyVersion: ID_POLICY_VERSION,
    mappingVersion: MAPPING_VERSION,
    provenanceIdNamespace: PROVENANCE_ID_NAMESPACE,
    projectionId: PROJECTION_ID,
    rootTextPolicyVersion: ROOT_TEXT_POLICY_VERSION,
    sourceBindings: Object.freeze({
      frozenInputs: FROZEN_INPUT_SHA256,
      releaseProfile: RELEASE_PROFILE,
      sourceRelease: SOURCE_RELEASE,
    }),
  });
  const projectionSha256 = sha256(canonicalJsonBytes(projectionHashMaterial));
  const manifest = Object.freeze({
    artifactBytes,
    artifactSha256,
    canonicalSerialization: CANONICAL_SERIALIZATION,
    canonicalSourceState: "proposed",
    contextSchemaVersion: CONTEXT_SCHEMA_VERSION,
    counts,
    deterministicBuildContract:
      "--check rebuilds twice in memory, compares every byte, then compares committed artifacts without writing.",
    eligibilityLedgerSha256:
      FROZEN_INPUT_SHA256["docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv"],
    exceptionRegisterSha256: artifactSha256["exception-register.json"],
    explanationRegistrySha256: artifactSha256["explanation-registry.json"],
    explanationRegistryVersion: EXPLANATION_REGISTRY_VERSION,
    frozenInputs: Object.freeze(Object.entries(FROZEN_INPUT_SHA256)
      .sort(([left], [right]) => compareText(left, right))
      .map(([path, digest]) => Object.freeze({ path, sha256: digest }))),
    generatorVersion: GENERATOR_VERSION,
    governedProjectionGzipBytes,
    governedProjectionGzipDefinition:
      "Sum of gzipSync level-9, mtime-0 byte lengths for governance-policy, explanation-registry, exception-register, terms, and records exact canonical payload bytes; manifest and CHECKSUMS excluded.",
    governedProjectionRawBytes,
    governedProjectionRawDefinition:
      "Sum of exact canonical UTF-8 byte lengths for governance-policy, explanation-registry, exception-register, terms, and records; manifest and CHECKSUMS excluded.",
    governancePolicySha256: artifactSha256["governance-policy.json"],
    governancePolicyVersion: POLICY_VERSION,
    idPolicyVersion: ID_POLICY_VERSION,
    mappingVersion: MAPPING_VERSION,
    provenanceIdNamespace: PROVENANCE_ID_NAMESPACE,
    projectionId: PROJECTION_ID,
    projectionSha256,
    projectionSha256Definition:
      "SHA-256 of canonical projection-hash material binding schema/projection identity, policy hash/version, all five core artifact hashes, source release and frozen input hashes, exact counts, payload byte metrics, mapping/generator/ID/root-text versions, and provenance ID namespace.",
    realSemanticEdgeCount: 0,
    recordsRawBytes: recordsBytes.byteLength,
    recordsGzipBytes: deterministicGzip(recordsBytes).byteLength,
    recordsSha256: artifactSha256["records.json"],
    regionContextNodeCount: 0,
    releaseProfile: RELEASE_PROFILE,
    rootTextPolicyVersion: ROOT_TEXT_POLICY_VERSION,
    schemaVersion: "trace-context-manifest/v1",
    sourceArtifactSha256: FROZEN_INPUT_SHA256["data/prefreeze_candidate_v48.sqlite"],
    sourceRelease: SOURCE_RELEASE,
    termRegistrySha256: artifactSha256["terms.json"],
  });
  const manifestBytes = canonicalJsonBytes(manifest);
  const filesWithoutChecksums = new Map(coreFiles);
  filesWithoutChecksums.set("manifest.json", manifestBytes);
  const checksumsBytes = Buffer.from(
    [...filesWithoutChecksums]
      .sort(([left], [right]) => compareText(left, right))
      .map(([filename, bytes]) => `${sha256(bytes)}  ${filename}`)
      .join("\n") + "\n",
    "utf8",
  );
  const files = new Map(filesWithoutChecksums);
  files.set("CHECKSUMS.sha256", checksumsBytes);
  assert.deepEqual([...files.keys()].sort(compareText), [...VALID_OUTPUT_FILES]);

  return Object.freeze({
    counts,
    files,
    governedProjectionGzipBytes,
    governedProjectionRawBytes,
    manifest,
    projectionSha256,
  });
}

async function readAndValidateSource() {
  for (const [relativePath, expectedSha256] of Object.entries(FROZEN_INPUT_SHA256)) {
    assert.equal(
      await sha256File(join(repositoryRoot, relativePath)),
      expectedSha256,
      `frozen input checksum differs: ${relativePath}`,
    );
  }
  assert.equal(
    await sha256File(join(repositoryRoot, RELEASE_PROFILE.path)),
    RELEASE_PROFILE.sha256,
    "release profile checksum differs",
  );

  const freeze = JSON.parse(await readFile(join(repositoryRoot, "database/FREEZE_V49.json"), "utf8"));
  assert.equal(freeze.objectCount, EXPECTED.canonicalObjects);
  assert.equal(freeze.eligibleCount, EXPECTED.publicObjects);
  assert.equal(freeze.heldCount, EXPECTED.heldObjects);
  assert.equal(freeze.relationshipCount, EXPECTED.canonicalFolderRows);
  assert.equal(freeze.acceptedTraceCount, 0);

  const releaseProfile = JSON.parse(
    await readFile(join(repositoryRoot, RELEASE_PROFILE.path), "utf8"),
  );
  assert.equal(releaseProfile.releaseIdentity?.releaseId, SOURCE_RELEASE.id);
  assert.equal(
    releaseProfile.releaseIdentity?.manifestSha256,
    SOURCE_RELEASE.manifestSha256,
  );
  assert.equal(releaseProfile.coreScale?.eligibleObjectCount, EXPECTED.publicObjects);
  assert.equal(releaseProfile.coreScale?.heldObjectCount, EXPECTED.heldObjects);
  assert.equal(releaseProfile.coreScale?.acceptedSemanticRelationCount, 0);

  const { eligible, held } = parseEligibilityLedger(
    await readFile(
      join(repositoryRoot, "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv"),
      "utf8",
    ),
  );
  assert.equal(eligible.size, EXPECTED.publicObjects);
  assert.equal(held.size, EXPECTED.heldObjects);

  const { DatabaseSync } = createRequire(import.meta.url)("node:sqlite");
  const sqlitePath = join(repositoryRoot, "data/prefreeze_candidate_v48.sqlite");
  const database = new DatabaseSync(`file:${sqlitePath}?mode=ro&immutable=1`, { readOnly: true });
  let allObjects;
  let allFolders;
  let classificationBasisRows;
  try {
    database.exec("PRAGMA query_only=ON");
    allObjects = [...database.prepare(
      "SELECT surface_id, title, creator, date_text, object_type, source_name FROM objects ORDER BY surface_id",
    ).iterate()];
    allFolders = [...database.prepare(
      "SELECT surface_id, folder_id, folder_type, title FROM object_folder_refs ORDER BY surface_id, folder_type, folder_id",
    ).iterate()];
    classificationBasisRows = [...database.prepare(
      "SELECT surface_id, value FROM object_metadata_rows WHERE table_kind = 'CLASSIFICATION' AND label = 'Classification basis' ORDER BY surface_id",
    ).iterate()];
  } finally {
    database.close();
  }

  assert.equal(allObjects.length, EXPECTED.canonicalObjects);
  assert.equal(allFolders.length, EXPECTED.canonicalFolderRows);
  const canonicalIds = new Set(allObjects.map((row) => row.surface_id));
  assert.equal(canonicalIds.size, EXPECTED.canonicalObjects);
  for (const stableId of canonicalIds) {
    assert(eligible.has(stableId) || held.has(stableId), `unclassified canonical object: ${stableId}`);
  }

  const objects = allObjects.filter((row) => eligible.has(row.surface_id));
  const folderRows = allFolders.filter((row) => eligible.has(row.surface_id));
  const heldFolderRows = allFolders.filter((row) => held.has(row.surface_id));
  const publicClassificationBasisRows = classificationBasisRows.filter((row) =>
    eligible.has(row.surface_id));
  assert.equal(objects.length, EXPECTED.publicObjects);
  assert.equal(folderRows.length, EXPECTED.publicFolderRows);
  assert.equal(heldFolderRows.length, EXPECTED.canonicalFolderRows - EXPECTED.publicFolderRows);
  assert.equal(new Set(objects.map((row) => row.surface_id)).size, EXPECTED.publicObjects);
  for (const row of objects) assert.match(row.surface_id, PUBLIC_STABLE_ID_PATTERN);

  const controlledRows = folderRows.filter((row) => row.folder_type !== "region");
  const regionRows = folderRows.filter((row) => row.folder_type === "region");
  const heldControlledRows = heldFolderRows.filter((row) => row.folder_type !== "region");
  const heldRegionRows = heldFolderRows.filter((row) => row.folder_type === "region");
  assert.equal(controlledRows.length, EXPECTED.publicControlledAssignments);
  assert.equal(regionRows.length, EXPECTED.publicRegionRows);
  assert.equal(heldControlledRows.length, EXPECTED.heldControlledAssignmentRows);
  assert.equal(heldRegionRows.length, EXPECTED.heldRegionRows);

  for (const row of folderRows) {
    assert(["medium", "movement", "region", "theme"].includes(row.folder_type));
    assert.match(row.folder_id, SOURCE_TERM_ID_PATTERN);
    assertSafeSourceLabel(row.title, `${row.folder_type} source label`);
  }

  const groupedRecordCount = publicClassificationBasisRows.filter((row) =>
    row.value === "Compound grouping over atomic source records"
    || row.value === "Grouped surface classification inherited from member records."
  ).length;
  assert.equal(groupedRecordCount, EXPECTED.groupedPublicRecords);

  return Object.freeze({
    controlledRows: Object.freeze(controlledRows),
    eligible,
    folderRows: Object.freeze(folderRows),
    groupedRecordCount,
    held,
    heldControlledRowCount: heldControlledRows.length,
    heldFolderRowCount: heldFolderRows.length,
    heldRegionRowCount: heldRegionRows.length,
    objects: Object.freeze(objects),
    regionRows: Object.freeze(regionRows),
  });
}

function parseEligibilityLedger(contents) {
  const lines = contents.split(/\r?\n/u).filter(Boolean);
  const headers = lines.shift()?.split("\t") ?? [];
  const stableIdIndex = headers.indexOf("surface_id_exact");
  const dispositionIndex = headers.indexOf("research_disposition");
  assert(stableIdIndex >= 0, "eligibility ledger stable-ID column is missing");
  assert(dispositionIndex >= 0, "eligibility ledger disposition column is missing");
  const eligible = new Set();
  const held = new Set();
  for (const line of lines) {
    const cells = line.split("\t");
    const stableId = cells[stableIdIndex] ?? "";
    const disposition = cells[dispositionIndex] ?? "";
    assert.match(stableId, PUBLIC_STABLE_ID_PATTERN);
    assert(!eligible.has(stableId) && !held.has(stableId), `duplicate ledger ID: ${stableId}`);
    if (disposition === "eligible") eligible.add(stableId);
    else if (disposition === "held") held.add(stableId);
    else assert.fail(`unknown research disposition: ${disposition}`);
  }
  return { eligible, held };
}

function buildGovernancePolicy() {
  return Object.freeze({
    allowedContextKinds: Object.freeze(["medium", "theme", "movement_context"]),
    ambiguityHandling: Object.freeze({
      principle: "Do not guess. Qualify or hold a representation when project curation cannot be stated safely.",
      qualifiedUse: "Use only when a bounded project-curated interpretation remains safe and the qualifier is exposed.",
      heldUse: "Use when even the bounded project-curated interpretation lacks adequate source identity or provenance.",
    }),
    assignmentIdentityPolicy: Object.freeze({
      material: "public surface ID + Context kind + governed public term ID",
      prohibitedMaterial: Object.freeze(["array position", "label-only identity", "internal UUID"]),
      representationIdPrefix: "CTXA:",
    }),
    eligiblePopulation: Object.freeze({
      authority: "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv",
      disposition: "eligible",
      heldBehavior: "fail_closed_and_absent",
    }),
    epistemicRole: "project_curated_context",
    exceptionProcedure: Object.freeze({
      allowedDecisions: Object.freeze([
        "PUBLISHED",
        "QUALIFIED",
        "HELD",
        "EXCLUDED",
        "DEFERRED_TO_OTHER_DOMAIN",
      ]),
      requirement: "Every non-standard case is recorded with scope, evidence, review method, and revisit condition.",
    }),
    explainabilityRequirements: Object.freeze([
      "what the representation is",
      "why it is shown",
      "where it came from",
      "its project-curated epistemic role",
      "permitted interpretation",
      "prohibited interpretation",
      "publication state",
      "policy version",
    ]),
    fieldDecisions: Object.freeze([
      Object.freeze({ decision: "INCLUDE_AS_ROOT_METADATA", field: "surface_id and title" }),
      Object.freeze({ decision: "INCLUDE_AS_ROOT_METADATA", field: "creator attribution" }),
      Object.freeze({ decision: "INCLUDE_AS_ROOT_METADATA", field: "object type" }),
      Object.freeze({ decision: "INCLUDE_AS_ROOT_METADATA", field: "source-reported date display" }),
      Object.freeze({ decision: "INCLUDE_AS_ROOT_METADATA", field: "source name" }),
      Object.freeze({ decision: "INCLUDE_AS_CONTROLLED_REPRESENTATION", field: "typed medium membership" }),
      Object.freeze({ decision: "INCLUDE_AS_CONTROLLED_REPRESENTATION", field: "typed theme membership" }),
      Object.freeze({ decision: "INCLUDE_AS_CONTROLLED_REPRESENTATION", field: "typed movement membership as movement context" }),
      Object.freeze({ decision: "INCLUDE_AS_EXPLANATION_ONLY", field: "medium/theme/movement source membership rows" }),
      Object.freeze({ decision: "DEFER_TO_SPACETIME", field: "typed and raw region" }),
      Object.freeze({ decision: "DEFER_TO_SPACETIME", field: "normalized date range" }),
      Object.freeze({ decision: "DEFER_TO_SOURCE/PROVENANCE", field: "raw objects.medium" }),
      Object.freeze({ decision: "DEFER_TO_SOURCE/PROVENANCE", field: "collection, source IDs, locators, URLs, descriptions, notes, and subjects" }),
      Object.freeze({ decision: "EXCLUDE_FROM_CONTEXT_V1", field: "image and rights fields" }),
      Object.freeze({ decision: "EXCLUDE_FROM_CONTEXT_V1", field: "Trace semantic relation fields" }),
    ]),
    heldExclusion: Object.freeze({
      publicTermRegistry: "held-only terms are absent",
      publicProjection: "held objects and their assignments are absent",
      lookupBehavior: "held and unknown public lookups are indistinguishable",
    }),
    mappingVersion: MAPPING_VERSION,
    missingnessHandling: Object.freeze({
      movement_context: "Optional; absence creates no placeholder representation.",
      selectedRecord: "An eligible record remains available when an optional kind is absent.",
    }),
    multiValueHandling: "Preserve each distinct source identity; never merge by label or array position.",
    policyVersion: POLICY_VERSION,
    prohibitedInference: Object.freeze([
      "historical relationship between records",
      "influence",
      "causation",
      "contact",
      "lineage or diffusion",
      "chronological progression",
      "creator intent",
      "definitive historical movement membership",
      "historical importance or ranking",
      "universal taxonomy or objective classification truth",
      "archival original order",
    ]),
    provenanceRequirements: Object.freeze({
      basis: "project_curated_typed_membership",
      decision: PUBLISHED_PROVENANCE_DECISION,
      governancePolicyVersion: POLICY_VERSION,
      mappingPolicyVersion: MAPPING_VERSION,
      provenanceIdNamespace: PROVENANCE_ID_NAMESPACE,
      sourceState: "proposed",
    }),
    publicationStates: Object.freeze({
      excluded: "Not exposed in the Context public projection.",
      held: "Not exposed pending sufficient evidence for a safe project-curated statement.",
      published: "Intentionally exposed as project-curated Context; not accepted as historical fact.",
      qualified: "Exposed only with an explicit bounded qualifier; not accepted as historical fact.",
    }),
    publicIdPolicy: Object.freeze({
      idPolicyVersion: ID_POLICY_VERSION,
      prohibitedExposure: Object.freeze(["raw folder identity", "internal UUID", "label-only identity"]),
      representationIdentity: "category-bound public term ID plus public surface ID under a representation salt",
      provenanceIdentity: "public representation ID under a dedicated provenance namespace",
      termIdentity: "category-bound hash of frozen source identity under the ID-policy salt; label and explanatory copy excluded",
    }),
    regionDecision: Object.freeze({
      contextNodeCount: 0,
      decision: "DEFER_TO_SPACETIME",
      reason: "Geographic context is governed by Spacetime rather than duplicated in Context Canvas.",
    }),
    reviewProcedure: Object.freeze([
      "verify frozen-input and eligibility bindings",
      "audit every unique controlled term",
      "validate every assignment identity and object eligibility",
      "review all multi-value and structural exceptions",
      "run collision, label-integrity, explainability, provenance, held-exclusion, and deterministic rebuild gates",
    ]),
    rootMetadataTextPolicyVersion: ROOT_TEXT_POLICY_VERSION,
    schemaVersion: POLICY_SCHEMA_VERSION,
    scope: "Controlled project representations for research navigation in Context V1.",
    sourceHierarchy: Object.freeze([
      "authoritative eligible surface ledger",
      "immutable frozen v49 object and typed-folder rows",
      "Context Governance v1 term and exception decisions",
    ]),
    supersession: "A later policy version must identify this policy explicitly and regenerate the projection; source v49 remains unchanged.",
    termIdentityPolicy: Object.freeze({
      collisionRequirement: "zero collisions across every public Context kind",
      labelChangeBehavior: "explanatory or display-copy changes do not regenerate identity",
      source: "typed folder identity plus Context kind",
    }),
    title: "Context Governance Policy v1",
    versioning: "Policy, mapping, explanation registry, generator, ID policy, and projection identities are independently versioned and manifest-bound.",
  });
}

function buildExplanationRegistry() {
  const commonProhibited = Object.freeze([
    "It does not establish a historical relation, influence, causation, contact, lineage, or diffusion between records.",
    "It does not establish creator intent, historical importance, ranking, chronology, or objective classification truth.",
    "A shared Context representation does not establish a relationship between records.",
  ]);
  return Object.freeze({
    entries: Object.freeze([
      Object.freeze({
        accessibilityWording:
          "Medium or format Context, published as project-curated classification; use only as archive classification.",
        connectionLabel: "classified as",
        contextKind: "medium",
        derivationDescription:
          "Mapped deterministically from the eligible record's typed medium membership; the frozen source state remains proposed.",
        explanationCode: "CTX-MEDIUM",
        governanceStatus: "Published as project-curated context under Context Governance v1.",
        longDefinition:
          "A project-controlled category that may describe medium, format, technique, or record grouping. It is not a universal material taxonomy.",
        methodPageExplanation:
          "Medium/format representations reproduce governed project classification for navigation and do not assert historical relations or complete material analysis.",
        permittedInterpretation:
          "The archive classifies the selected record under the medium/format category {term}.",
        prohibitedInterpretations: Object.freeze([
          "It does not establish material composition or production technique beyond the project's classification.",
          "It does not establish definitive historical membership or affiliation.",
          ...commonProhibited,
        ]),
        publicLabel: "Medium / format",
        shortDefinition: "A project-controlled medium or format category used to organize the archive.",
        sourceBasis: "Project-curated typed membership in the frozen v49 source.",
        uiShortExplanation: "Shown because the project assigns this record to a typed medium/format category.",
      }),
      Object.freeze({
        accessibilityWording:
          "Theme Context, published as a project-curated research category; it does not prove subject, intent, or relation.",
        connectionLabel: "themed as",
        contextKind: "theme",
        derivationDescription:
          "Mapped deterministically from the eligible record's typed theme membership; the frozen source state remains proposed.",
        explanationCode: "CTX-THEME",
        governanceStatus: "Published as project-curated context under Context Governance v1.",
        longDefinition:
          "A project-defined thematic category for research navigation. It records how the archive organizes the selected record, not what a creator intended or what history proves.",
        methodPageExplanation:
          "Theme representations expose governed project research categories without converting them into creator intent, historical claims, or relations between records.",
        permittedInterpretation:
          "The archive assigns {term} as a thematic research category for the selected record.",
        prohibitedInterpretations: Object.freeze([
          "It does not prove that the creator intended the theme or that the theme is the record's only subject.",
          "It does not establish definitive historical membership or affiliation.",
          ...commonProhibited,
        ]),
        publicLabel: "Theme",
        shortDefinition: "A project-curated thematic research category used to navigate the archive.",
        sourceBasis: "Project-curated typed membership in the frozen v49 source.",
        uiShortExplanation: "Shown because the archive assigns this record to a governed thematic research category.",
      }),
      Object.freeze({
        accessibilityWording:
          "Movement context, published for project-curated research navigation; it is not definitive historical membership.",
        connectionLabel: "curated within",
        contextKind: "movement_context",
        derivationDescription:
          "Mapped deterministically from the eligible record's typed movement membership as a movement context; the frozen source state remains proposed.",
        explanationCode: "CTX-MOVEMENT",
        governanceStatus: "Published as project-curated context under Context Governance v1.",
        longDefinition:
          "A bounded project-curated movement, network, formation, school, or poster-culture context used for research navigation. It is not acceptance of historical membership.",
        methodPageExplanation:
          "Movement context records project curation only. Stronger claims about affiliation, membership, influence, contact, or chronology require separately published evidence.",
        permittedInterpretation:
          "The project places the selected record within {term} as a curated movement context for research navigation.",
        prohibitedInterpretations: Object.freeze([
          "It does not establish definitive historical movement membership, affiliation, or authorship.",
          "It does not establish that the creator intended, joined, influenced, or contacted the named context.",
          ...commonProhibited,
        ]),
        publicLabel: "Movement context",
        shortDefinition: "A project-curated movement context for research navigation.",
        sourceBasis: "Project-curated typed membership in the frozen v49 source.",
        uiShortExplanation: "Shown because the project curates this record within a governed movement context.",
      }),
    ]),
    epistemicRole: "project_curated_context",
    policyVersion: POLICY_VERSION,
    registryVersion: EXPLANATION_REGISTRY_VERSION,
    schemaVersion: "trace-context-explanations/v1",
    termPlaceholder: "{term}",
  });
}

function buildExceptionRegister(source) {
  const rowsByObjectAndKind = groupBy(source.folderRows, (row) =>
    `${row.surface_id}\u0000${row.folder_type}`);
  const themeMultivalueRecords = [...rowsByObjectAndKind]
    .filter(([key, rows]) => key.endsWith("\u0000theme") && rows.length > 1).length;
  const movementMultivalueRecords = [...rowsByObjectAndKind]
    .filter(([key, rows]) => key.endsWith("\u0000movement") && rows.length > 1).length;
  const regionMultivalueRecords = [...rowsByObjectAndKind]
    .filter(([key, rows]) => key.endsWith("\u0000region") && rows.length > 1).length;
  assert.equal(themeMultivalueRecords, EXPECTED.themeMultivalueRecords);
  assert.equal(movementMultivalueRecords, EXPECTED.movementMultivalueRecords);
  assert.equal(regionMultivalueRecords, 1);

  return Object.freeze({
    counts: Object.freeze({
      deferredToOtherDomainEntries: 1,
      excludedEntries: 0,
      heldEntries: 0,
      publishedEntries: 3,
      qualifiedEntries: 0,
      totalEntries: 4,
    }),
    entries: Object.freeze([
      Object.freeze({
        decision: "PUBLISHED",
        evidence: `${source.groupedRecordCount} eligible grouped or compound public surfaces.`,
        exceptionCode: "CTX-EXC-GROUPED-RECORD-SURFACES",
        reason: "Controlled classifications apply to the selected public record or group surface and do not propagate to every member record.",
        revisitCondition: "Revisit only if member-level Context publication is separately governed.",
        reviewMethod: "Exhaustive eligible classification-basis census.",
        scope: Object.freeze({ publicRecordCount: source.groupedRecordCount }),
      }),
      Object.freeze({
        decision: "PUBLISHED",
        evidence: "One eligible record carries two distinct typed theme identities with no collision or conflicting label.",
        exceptionCode: "CTX-EXC-THEME-MULTIVALUE",
        reason: "Both project-curated theme assignments remain distinct at the selected-record level.",
        revisitCondition: "Revisit only if the frozen typed source identity changes under a later release.",
        reviewMethod: "Exhaustive same-kind multiplicity and source-identity validation.",
        scope: Object.freeze({ publicRecordCount: themeMultivalueRecords, representationCount: 2 }),
      }),
      Object.freeze({
        decision: "PUBLISHED",
        evidence: "Five eligible records each carry two distinct typed movement identities; every internal movement-reference token count reconciles with typed assignments.",
        exceptionCode: "CTX-EXC-MOVEMENT-MULTIVALUE",
        reason: "Each assignment is published only as project-curated movement context, never historical membership.",
        revisitCondition: "Revisit if stronger historical claims are proposed or the frozen typed source identity changes.",
        reviewMethod: "Exhaustive movement assignment and supporting project-classification audit.",
        scope: Object.freeze({ publicRecordCount: movementMultivalueRecords, representationCount: 10 }),
      }),
      Object.freeze({
        decision: "DEFERRED_TO_OTHER_DOMAIN",
        evidence: `${source.regionRows.length} eligible typed region rows over ${new Set(source.regionRows.map((row) => row.surface_id)).size} public records.`,
        exceptionCode: "CTX-EXC-REGION-SPACETIME-HANDOFF",
        reason: "Geographic context belongs to Spacetime and is not duplicated as a Context representation.",
        revisitCondition: "Review under Spacetime parameter governance; do not normalize geography in Context V1.",
        reviewMethod: "Exhaustive eligible typed-region census; aggregate only, with no record rows emitted here.",
        scope: Object.freeze({
          contextNodeCount: 0,
          publicObjectCount: new Set(source.regionRows.map((row) => row.surface_id)).size,
          sourceRowCount: source.regionRows.length,
          termCount: new Set(source.regionRows.map((row) => row.folder_id)).size,
        }),
      }),
    ]),
    policyVersion: POLICY_VERSION,
    schemaVersion: "trace-context-exceptions/v1",
  });
}

function buildTerms(source) {
  const rowsBySourceIdentity = groupBy(source.controlledRows, (row) =>
    `${SOURCE_TO_PUBLIC_KIND[row.folder_type]}\u0000${row.folder_id}`);
  const terms = [];
  const termBySourceIdentity = new Map();
  for (const [sourceKey, rows] of rowsBySourceIdentity) {
    const [kind, rawSourceIdentity] = sourceKey.split("\u0000");
    assert(KIND_ORDER.includes(kind), `unsupported governed kind: ${kind}`);
    const labels = new Set(rows.map((row) => row.title));
    assert.equal(labels.size, 1, `one source identity has conflicting labels: ${kind}`);
    const label = [...labels][0];
    const id = publicTermId(kind, rawSourceIdentity);
    const term = Object.freeze({
      assignmentCount: rows.length,
      explanationCode: EXPLANATION_CODE[kind],
      id,
      kind,
      label,
      publicationState: "published",
    });
    terms.push(term);
    termBySourceIdentity.set(sourceKey, term);
  }
  terms.sort(compareTerms);
  assert.equal(terms.length, EXPECTED.publicTerms);
  assert.equal(new Set(terms.map((term) => term.id)).size, terms.length);
  assert.equal(
    new Set(terms.map((term) => `${term.kind}\u0000${term.label}`)).size,
    terms.length,
    "same governed kind and label map to different term IDs",
  );
  assert.equal(
    new Set(terms.map((term) => term.label)).size,
    terms.length,
    "a public label is reused across governed Context kinds",
  );
  return Object.freeze({
    termBySourceIdentity,
    termsDocument: Object.freeze({
      counts: Object.freeze({
        byKind: countByKind(terms),
        total: terms.length,
      }),
      idPolicyVersion: ID_POLICY_VERSION,
      policyVersion: POLICY_VERSION,
      projectionId: PROJECTION_ID,
      schemaVersion: "trace-context-terms/v1",
      terms: Object.freeze(terms),
    }),
  });
}

function buildRecords(source, termBySourceIdentity) {
  const foldersByObject = groupBy(source.controlledRows, (row) => row.surface_id);
  let rootMetadataNormalizedFieldCount = 0;
  const records = source.objects.map((object) => {
    const representations = (foldersByObject.get(object.surface_id) ?? []).map((row) => {
      const kind = SOURCE_TO_PUBLIC_KIND[row.folder_type];
      const term = termBySourceIdentity.get(`${kind}\u0000${row.folder_id}`);
      assert(term, `governed term lookup failed: ${kind}`);
      const id = publicRepresentationId(object.surface_id, kind, term.id);
      return Object.freeze({
        epistemicRole: "project_curated_context",
        explanationCode: term.explanationCode,
        id,
        kind,
        label: term.label,
        provenance: Object.freeze({
          basis: "project_curated_typed_membership",
          decision: PUBLISHED_PROVENANCE_DECISION,
          governancePolicyVersion: POLICY_VERSION,
          mappingPolicyVersion: MAPPING_VERSION,
          provenanceId: publicProvenanceId(id),
          sourceKind: row.folder_type,
          sourceState: "proposed",
        }),
        publicationState: "published",
        termId: term.id,
      });
    }).sort(compareRepresentations);
    assert(representations.length >= 2, `public Context record is incomplete: ${object.surface_id}`);
    const title = sanitizeRootText(object.title);
    const creatorAttribution = sanitizeRootText(object.creator);
    const objectType = sanitizeRootText(object.object_type);
    const dateDisplay = sanitizeRootText(object.date_text);
    const sourceName = sanitizeRootText(object.source_name);
    rootMetadataNormalizedFieldCount += [
      [object.title, title],
      [object.creator, creatorAttribution],
      [object.object_type, objectType],
      [object.date_text, dateDisplay],
      [object.source_name, sourceName],
    ].filter(([sourceValue, publicValue]) => sourceValue !== publicValue).length;
    for (const value of [creatorAttribution, objectType, dateDisplay, sourceName]) {
      assert(!URL_PATTERN.test(value), "root metadata contains a URL");
      assert(!UUID_PATTERN.test(value), "root metadata contains an internal UUID");
    }
    return Object.freeze({
      availability: "ready",
      counts: Object.freeze({ representations: representations.length }),
      representations: Object.freeze(representations),
      selectedRecord: Object.freeze({
        rootMetadata: Object.freeze({
          creatorAttribution,
          dateDisplay,
          objectType,
          sourceName,
        }),
        surfaceId: object.surface_id,
        title,
      }),
    });
  }).sort((left, right) => compareText(
    left.selectedRecord.surfaceId,
    right.selectedRecord.surfaceId,
  ));

  return Object.freeze({
    explanationRegistryVersion: EXPLANATION_REGISTRY_VERSION,
    mappingVersion: MAPPING_VERSION,
    policyVersion: POLICY_VERSION,
    projectionId: PROJECTION_ID,
    records: Object.freeze(records),
    rootMetadataNormalizedFieldCount,
    rootMetadataTextPolicyVersion: ROOT_TEXT_POLICY_VERSION,
    schemaVersion: CONTEXT_SCHEMA_VERSION,
    sourceRelease: SOURCE_RELEASE,
  });
}

function validateProjectionDocuments({
  exceptionRegister,
  explanationRegistry,
  policy,
  recordsDocument,
  source,
  termsDocument,
}) {
  assert.equal(policy.policyVersion, POLICY_VERSION);
  assert.equal(explanationRegistry.entries.length, 3);
  assert.deepEqual(
    explanationRegistry.entries.map((entry) => entry.contextKind),
    KIND_ORDER,
  );
  assert.deepEqual(
    explanationRegistry.entries.map((entry) => entry.connectionLabel),
    ["classified as", "themed as", "curated within"],
  );
  const explanationsByCode = new Map(
    explanationRegistry.entries.map((entry) => [entry.explanationCode, entry]),
  );
  assert.equal(explanationsByCode.size, 3);
  assert.equal(exceptionRegister.entries.length, 4);
  assert.equal(recordsDocument.records.length, EXPECTED.publicObjects);
  assert.equal(termsDocument.terms.length, EXPECTED.publicTerms);

  const representationIds = new Set();
  const provenanceIds = new Set();
  const projectedTermIds = new Set();
  const projectedStableIds = new Set();
  let representationCount = 0;
  const assignmentCounts = { medium: 0, movement_context: 0, theme: 0 };
  const objectCoverage = {
    medium: new Set(),
    movement_context: new Set(),
    theme: new Set(),
  };
  for (const record of recordsDocument.records) {
    const stableId = record.selectedRecord.surfaceId;
    assert(source.eligible.has(stableId));
    assert(!source.held.has(stableId));
    assert(!projectedStableIds.has(stableId), `duplicate governed record: ${stableId}`);
    projectedStableIds.add(stableId);
    assert.equal(record.availability, "ready");
    assert.equal(record.counts.representations, record.representations.length);
    for (const representation of record.representations) {
      representationCount += 1;
      assignmentCounts[representation.kind] += 1;
      objectCoverage[representation.kind].add(stableId);
      assert(!representationIds.has(representation.id), `representation ID collision: ${representation.id}`);
      representationIds.add(representation.id);
      assert(
        !provenanceIds.has(representation.provenance.provenanceId),
        `provenance ID collision: ${representation.provenance.provenanceId}`,
      );
      provenanceIds.add(representation.provenance.provenanceId);
      projectedTermIds.add(representation.termId);
      assert.match(representation.id, /^CTXA:[0-9a-f]{64}$/u);
      assert.match(representation.termId, /^CTX:(?:MEDIUM|THEME|MOVEMENT):[0-9a-f]{64}$/u);
      assert.equal(representation.epistemicRole, "project_curated_context");
      assert.equal(representation.publicationState, "published");
      assert.equal(representation.provenance.basis, "project_curated_typed_membership");
      assert.equal(representation.provenance.decision, PUBLISHED_PROVENANCE_DECISION);
      assert.equal(representation.provenance.governancePolicyVersion, POLICY_VERSION);
      assert.equal(representation.provenance.mappingPolicyVersion, MAPPING_VERSION);
      assert.match(representation.provenance.provenanceId, /^CTXP:[0-9a-f]{64}$/u);
      assert.equal(
        representation.provenance.sourceKind,
        representation.kind === "movement_context" ? "movement" : representation.kind,
      );
      assert.equal(representation.provenance.sourceState, "proposed");
      assert(explanationsByCode.has(representation.explanationCode));
      assert.equal(
        explanationsByCode.get(representation.explanationCode).contextKind,
        representation.kind,
      );
    }
  }
  assert.equal(representationCount, EXPECTED.publicControlledAssignments);
  assert.equal(representationIds.size, representationCount);
  assert.equal(provenanceIds.size, representationCount);
  assert.equal(projectedTermIds.size, EXPECTED.publicTerms);
  assert.deepEqual(Object.freeze(assignmentCounts), EXPECTED_KIND_COUNTS.assignments);
  assert.deepEqual(
    Object.freeze(Object.fromEntries(KIND_ORDER.map((kind) => [kind, objectCoverage[kind].size]))),
    EXPECTED_KIND_COUNTS.objects,
  );
  assert.deepEqual(termsDocument.counts.byKind, EXPECTED_KIND_COUNTS.terms);
  assert.equal(new Set(termsDocument.terms.map((term) => term.id)).size, EXPECTED.publicTerms);
  assert.equal(
    sum(termsDocument.terms.map((term) => term.assignmentCount)),
    EXPECTED.publicControlledAssignments,
  );

  const serializedPublicPayload = canonicalJsonBytes({
    explanationRegistry,
    recordsDocument,
    termsDocument,
  }).toString("utf8");
  assert(!serializedPublicPayload.includes("ctxv49:"), "validation ID leaked into governed projection");
  assert(!RAW_SOURCE_TERM_PATTERN.test(serializedPublicPayload), "raw folder identity leaked");
  assert(!UUID_PATTERN.test(serializedPublicPayload), "internal UUID leaked");
  assert(!URL_PATTERN.test(serializedPublicPayload), "URL leaked into public governed payload");
  const serializedStableIds = new Set(
    serializedPublicPayload.match(PUBLIC_STABLE_ID_IN_TEXT_PATTERN) ?? [],
  );
  assert.equal(serializedStableIds.size, EXPECTED.publicObjects);
  for (const exposedStableId of serializedStableIds) {
    assert(source.eligible.has(exposedStableId), "non-eligible stable ID leaked into governed projection");
    assert(!source.held.has(exposedStableId), "held stable ID leaked into governed projection");
  }
}

function buildCounts(source, recordsDocument, termsDocument) {
  const representations = recordsDocument.records.flatMap((record) => record.representations);
  const assignmentCounts = countByKind(representations);
  const objectSets = Object.fromEntries(KIND_ORDER.map((kind) => [kind, new Set()]));
  const representationHistogram = {};
  let sameKindMultivalueObjectCount = 0;
  for (const record of recordsDocument.records) {
    representationHistogram[record.representations.length] =
      (representationHistogram[record.representations.length] ?? 0) + 1;
    const perKind = countByKind(record.representations);
    if (Object.values(perKind).some((count) => count > 1)) sameKindMultivalueObjectCount += 1;
    for (const representation of record.representations) {
      objectSets[representation.kind].add(record.selectedRecord.surfaceId);
    }
  }
  const objectCoverage = Object.freeze(Object.fromEntries(
    KIND_ORDER.map((kind) => [kind, objectSets[kind].size]),
  ));
  const termCounts = termsDocument.counts.byKind;
  return Object.freeze({
    assignmentCounts: Object.freeze({ ...assignmentCounts, total: representations.length }),
    heldExcluded: Object.freeze({
      controlledAssignmentSourceRowCount: source.heldControlledRowCount,
      folderSourceRowCount: source.heldFolderRowCount,
      objectCount: source.held.size,
      regionSourceRowCount: source.heldRegionRowCount,
    }),
    objectCoverage: Object.freeze({ ...objectCoverage, anyContext: recordsDocument.records.length }),
    publicObjectCount: recordsDocument.records.length,
    publicationCounts: Object.freeze({
      excluded: 0,
      held: 0,
      published: representations.length,
      qualified: 0,
    }),
    regionHandoff: Object.freeze({
      contextNodeCount: 0,
      decision: "DEFER_TO_SPACETIME",
      publicObjectCount: new Set(source.regionRows.map((row) => row.surface_id)).size,
      sourceRowCount: source.regionRows.length,
      termCount: new Set(source.regionRows.map((row) => row.folder_id)).size,
    }),
    representationHistogram: Object.freeze(Object.fromEntries(
      Object.entries(representationHistogram).sort(([left], [right]) => Number(left) - Number(right)),
    )),
    rootMetadataNormalizedFieldCount: recordsDocument.rootMetadataNormalizedFieldCount,
    sameKindMultivalueObjectCount,
    termCounts: Object.freeze({ ...termCounts, total: termsDocument.terms.length }),
  });
}

function publicTermId(kind, rawSourceIdentity) {
  assert(KIND_PREFIX[kind], `term ID kind is unsupported: ${kind}`);
  assert.match(rawSourceIdentity, SOURCE_TERM_ID_PATTERN);
  const digest = sha256(Buffer.from(
    [
      `${ID_POLICY_VERSION}:term`,
      kind,
      rawSourceIdentity,
    ].join("\u0000"),
    "utf8",
  ));
  return `CTX:${KIND_PREFIX[kind]}:${digest}`;
}

function publicRepresentationId(surfaceId, kind, termId) {
  assert.match(surfaceId, PUBLIC_STABLE_ID_PATTERN);
  const digest = sha256(Buffer.from(
    [
      `${ID_POLICY_VERSION}:representation`,
      surfaceId,
      kind,
      termId,
    ].join("\u0000"),
    "utf8",
  ));
  return `CTXA:${digest}`;
}

function publicProvenanceId(representationId) {
  assert.match(representationId, /^CTXA:[0-9a-f]{64}$/u);
  return `CTXP:${sha256(Buffer.from(
    [PROVENANCE_ID_NAMESPACE, representationId].join("\u0000"),
    "utf8",
  ))}`;
}

function sanitizeRootText(value) {
  assert.equal(typeof value, "string", "root metadata must be text");
  let output = "";
  for (let index = 0; index < value.length; index += 1) {
    const codeUnit = value.charCodeAt(index);
    if (codeUnit >= 0xd800 && codeUnit <= 0xdbff) {
      const next = value.charCodeAt(index + 1);
      if (next >= 0xdc00 && next <= 0xdfff) {
        output += value[index] + value[index + 1];
        index += 1;
      } else output += "\ufffd";
    } else if (codeUnit >= 0xdc00 && codeUnit <= 0xdfff) output += "\ufffd";
    else if (codeUnit <= 0x1f || (codeUnit >= 0x7f && codeUnit <= 0x9f)) output += "\ufffd";
    else output += value[index];
  }
  assert(output.trim(), "root metadata is empty");
  return output;
}

function assertSafeSourceLabel(value, field) {
  assert.equal(typeof value, "string", `${field} must be text`);
  assert(value.trim(), `${field} is empty`);
  assert.equal(value, value.trim(), `${field} has boundary whitespace`);
  assert(!/[\u0000-\u001f\u007f-\u009f]/u.test(value), `${field} contains control text`);
  assert.equal(sanitizeRootText(value), value, `${field} contains invalid Unicode`);
}

function compareTerms(left, right) {
  return KIND_ORDER.indexOf(left.kind) - KIND_ORDER.indexOf(right.kind)
    || compareText(left.id, right.id);
}

function compareRepresentations(left, right) {
  return KIND_ORDER.indexOf(left.kind) - KIND_ORDER.indexOf(right.kind)
    || compareText(left.termId, right.termId);
}

function countByKind(values) {
  return Object.freeze(Object.fromEntries(KIND_ORDER.map((kind) => [
    kind,
    values.filter((value) => value.kind === kind).length,
  ])));
}

function groupBy(values, keyFor) {
  const result = new Map();
  for (const value of values) {
    const key = keyFor(value);
    const bucket = result.get(key) ?? [];
    bucket.push(value);
    result.set(key, bucket);
  }
  return result;
}

function canonicalJsonBytes(value) {
  return Buffer.from(`${JSON.stringify(sortObjectKeys(value))}\n`, "utf8");
}

function sortObjectKeys(value) {
  if (Array.isArray(value)) return value.map(sortObjectKeys);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value)
        .sort(([left], [right]) => compareText(left, right))
        .map(([key, child]) => [key, sortObjectKeys(child)]),
    );
  }
  return value;
}

function deterministicGzip(bytes) {
  return gzipSync(bytes, { level: 9, mtime: 0 });
}

async function sha256File(path) {
  const digest = createHash("sha256");
  for await (const chunk of createReadStream(path)) digest.update(chunk);
  return digest.digest("hex");
}

function sha256(value) {
  const digest = createHash("sha256").update(value).digest("hex");
  assert.match(digest, SHA256_PATTERN);
  return digest;
}

function compareText(left, right) {
  return left < right ? -1 : left > right ? 1 : 0;
}

function sum(values) {
  return values.reduce((total, value) => total + value, 0);
}

function printReceipt(mode, built) {
  console.log(
    `TRACE_CONTEXT_V1_GENERATION=PASS MODE=${mode} RUNS=${mode === "CHECK" ? 2 : 1} `
    + `PUBLIC_OBJECTS=${built.counts.publicObjectCount} TERMS=${built.counts.termCounts.total} `
    + `REPRESENTATIONS=${built.counts.assignmentCounts.total} PROJECTION_SHA256=${built.projectionSha256}`,
  );
  console.log(
    `TRACE_CONTEXT_V1_COUNTS=PASS MEDIUM_TERMS=${built.counts.termCounts.medium} `
    + `THEME_TERMS=${built.counts.termCounts.theme} MOVEMENT_TERMS=${built.counts.termCounts.movement_context} `
    + `MEDIUM_REPRESENTATIONS=${built.counts.assignmentCounts.medium} `
    + `THEME_REPRESENTATIONS=${built.counts.assignmentCounts.theme} `
    + `MOVEMENT_REPRESENTATIONS=${built.counts.assignmentCounts.movement_context}`,
  );
  console.log(
    `TRACE_CONTEXT_V1_PAYLOAD=PASS RAW_BYTES=${built.governedProjectionRawBytes} `
    + `GZIP_BYTES=${built.governedProjectionGzipBytes} RECORDS_RAW_BYTES=${built.manifest.recordsRawBytes} `
    + `RECORDS_GZIP_BYTES=${built.manifest.recordsGzipBytes}`,
  );
  console.log(
    `TRACE_CONTEXT_V1_SECURITY=PASS HELD_EXPOSED=0 REGION_CONTEXT_NODES=0 `
    + `VALIDATION_IDS=0 RAW_FOLDER_IDS=0 INTERNAL_UUIDS=0 REAL_SEMANTIC_EDGES=0`,
  );
}

function safeError(error) {
  return String(error instanceof Error ? error.message : error)
    .replace(/[\r\n\t]+/gu, " ")
    .slice(0, 500);
}
