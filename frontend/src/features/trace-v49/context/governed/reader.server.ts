import eligibilityJson from "../../../../../generated/reader-eligibility-v49/eligibility.json";
import eligibilityManifestJson from "../../../../../generated/reader-eligibility-v49/manifest.json";
import type { GovernedContextExampleOption, GovernedContextExampleRole, GovernedContextObjectEntry } from "./types";
import "server-only";

import { createHash } from "node:crypto";
import { performance } from "node:perf_hooks";
import exceptionRegisterJson from "../../../../../generated/trace-context-v1/exception-register.json";
import explanationRegistryJson from "../../../../../generated/trace-context-v1/explanation-registry.json";
import governancePolicyJson from "../../../../../generated/trace-context-v1/governance-policy.json";
import manifestJson from "../../../../../generated/trace-context-v1/manifest.json";
import recordsJson from "../../../../../generated/trace-context-v1/records.json";
import termsJson from "../../../../../generated/trace-context-v1/terms.json";
import {
  TRACE_CONTEXT_EXPLANATION_REGISTRY_VERSION,
  TRACE_CONTEXT_GOVERNANCE_POLICY_VERSION,
  TRACE_CONTEXT_GOVERNED_MAPPING_VERSION,
  TRACE_CONTEXT_PUBLIC_PROJECTION_ID,
  TRACE_CONTEXT_PUBLIC_SCHEMA_VERSION,
  type GovernedContextSampleOption,
  type GovernedContextLookup,
  type PublicContextAccessibleRow,
  type PublicContextDataset,
  type PublicContextExplanation,
  type PublicContextRepresentation,
  type PublicContextRepresentationKind,
  type PublicContextRootMetadata,
} from "./types";

const MANIFEST_SCHEMA_VERSION = "trace-context-manifest/v1" as const;
const TERMS_SCHEMA_VERSION = "trace-context-terms/v1" as const;
const EXPLANATIONS_SCHEMA_VERSION = "trace-context-explanations/v1" as const;
const GOVERNANCE_POLICY_SCHEMA_VERSION = "trace-context-governance-policy/v1" as const;
const EXCEPTION_REGISTER_SCHEMA_VERSION = "trace-context-exceptions/v1" as const;
const ID_POLICY_VERSION = "trace-context-public-id-v1" as const;
const GENERATOR_VERSION = "trace-context-projection-generator-v1" as const;
const ROOT_TEXT_POLICY_VERSION = "trace-context-root-text-v1" as const;
const PROVENANCE_ID_NAMESPACE = "trace-context-provenance-v1" as const;
const CANONICAL_SERIALIZATION =
  "recursive-key-sort;array-order-preserved;json-minified;final-lf;utf8" as const;
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
const PUBLIC_STABLE_ID_PATTERN = /^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$/u;
const TERM_ID_PATTERN = /^CTX:(?:MEDIUM|THEME|MOVEMENT):[0-9a-f]{64}$/u;
const REPRESENTATION_ID_PATTERN = /^CTXA:[0-9a-f]{64}$/u;
const PROVENANCE_ID_PATTERN = /^CTXP:[0-9a-f]{64}$/u;
const SHA256_PATTERN = /^[0-9a-f]{64}$/u;
const UUID_PATTERN = /\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b/iu;
const URL_PATTERN = /(?:https?:\/\/|www\.)/iu;
const RAW_SOURCE_TERM_PATTERN = /\bFOL-(?:MEDIUM|THEME|MOVEMENT|REGION)-/u;
const EXPECTED_ASSIGNMENTS = Object.freeze({
  medium: 7_995,
  movement_context: 115,
  theme: 7_996,
  total: 16_106,
});
const EXPECTED_TERMS = Object.freeze({
  medium: 10,
  movement_context: 7,
  theme: 8,
  total: 25,
});
const EXPECTED_OBJECT_COVERAGE = Object.freeze({
  medium: 7_995,
  movement_context: 110,
  theme: 7_995,
  anyContext: 7_995,
});
const GENERIC_NOT_FOUND_MESSAGE = "Context dataset is not available for this object.";

type SourceKind = "medium" | "theme" | "movement";
type ArtifactProvenance = Readonly<{
  provenanceId: string;
  basis: "project_curated_typed_membership";
  sourceKind: SourceKind;
  sourceState: "proposed";
  mappingPolicyVersion: string;
  governancePolicyVersion: string;
  decision: "PUBLISHED";
}>;
type ArtifactRepresentation = Readonly<{
  id: string;
  kind: PublicContextRepresentationKind;
  termId: string;
  label: string;
  epistemicRole: "project_curated_context";
  publicationState: "published";
  explanationCode: string;
  provenance: ArtifactProvenance;
}>;
type ArtifactRecord = Readonly<{
  selectedRecord: Readonly<{
    surfaceId: string;
    title: string;
    rootMetadata: PublicContextRootMetadata;
  }>;
  availability: "ready";
  representations: readonly ArtifactRepresentation[];
  counts: Readonly<{ representations: number }>;
}>;
type ArtifactTerm = Readonly<{
  id: string;
  kind: PublicContextRepresentationKind;
  label: string;
  explanationCode: string;
  publicationState: "published";
  assignmentCount: number;
}>;
type ArtifactRecordsDocument = Readonly<{
  schemaVersion: string;
  projectionId: string;
  policyVersion: string;
  mappingVersion: string;
  explanationRegistryVersion: string;
  rootMetadataTextPolicyVersion: string;
  rootMetadataNormalizedFieldCount: number;
  sourceRelease: typeof SOURCE_RELEASE;
  records: readonly ArtifactRecord[];
}>;
type ArtifactTermsDocument = Readonly<{
  schemaVersion: string;
  projectionId: string;
  policyVersion: string;
  idPolicyVersion: string;
  counts: Readonly<{
    total: number;
    byKind: Readonly<Record<PublicContextRepresentationKind, number>>;
  }>;
  terms: readonly ArtifactTerm[];
}>;
type ArtifactExplanationRegistry = Readonly<{
  schemaVersion: string;
  registryVersion: string;
  policyVersion: string;
  epistemicRole: "project_curated_context";
  termPlaceholder: "{term}";
  entries: readonly PublicContextExplanation[];
}>;
type ArtifactManifest = Readonly<Record<string, unknown>> & {
  readonly schemaVersion: string;
  readonly contextSchemaVersion: string;
  readonly projectionId: string;
  readonly projectionSha256: string;
  readonly canonicalSerialization: string;
  readonly canonicalSourceState: string;
  readonly sourceRelease: typeof SOURCE_RELEASE;
  readonly artifactSha256: Readonly<Record<string, string>>;
  readonly artifactBytes: Readonly<Record<string, number>>;
  readonly counts: Readonly<Record<string, unknown>>;
  readonly frozenInputs: readonly Readonly<{ path: string; sha256: string }>[];
  readonly releaseProfile: typeof RELEASE_PROFILE;
  readonly governancePolicyVersion: string;
  readonly governancePolicySha256: string;
  readonly exceptionRegisterSha256: string;
  readonly explanationRegistryVersion: string;
  readonly explanationRegistrySha256: string;
  readonly termRegistrySha256: string;
  readonly recordsSha256: string;
  readonly eligibilityLedgerSha256: string;
  readonly sourceArtifactSha256: string;
  readonly idPolicyVersion: string;
  readonly mappingVersion: string;
  readonly generatorVersion: string;
  readonly rootTextPolicyVersion: string;
  readonly provenanceIdNamespace: string;
  readonly governedProjectionRawBytes: number;
  readonly governedProjectionGzipBytes: number;
  readonly recordsRawBytes: number;
  readonly recordsGzipBytes: number;
  readonly realSemanticEdgeCount: number;
  readonly regionContextNodeCount: number;
};

export interface GovernedContextProjectionInfo {
  readonly projectionId: typeof TRACE_CONTEXT_PUBLIC_PROJECTION_ID;
  readonly projectionSha256: string;
  readonly researchReleaseId: string;
  readonly researchManifestSha256: string;
  readonly recordCount: number;
  readonly termCount: number;
  readonly representationCount: number;
  readonly rawBytes: number;
  readonly gzipBytes: number;
}

interface GovernedContextIndex {
  readonly manifest: ArtifactManifest;
  readonly recordById: ReadonlyMap<string, ArtifactRecord>;
  readonly explanationByCode: ReadonlyMap<string, PublicContextExplanation>;
  readonly info: GovernedContextProjectionInfo;
  readonly sampleOptions: readonly GovernedContextSampleOption[];
  /* the reader-facing objects, for the canvas's object chooser: title
     search and the worked examples read this; the deterministic samples
     above stay a QA tool */
  readonly objects: readonly GovernedContextObjectEntry[];
  readonly exampleOptions: readonly GovernedContextExampleOption[];
  /* the object the canvas opens on when none is asked for and none is
     remembered: reader-facing, governed context in all three dimensions,
     the most representations (ties by stable ID) */
  readonly landingRecord: GovernedContextSampleOption;
}

/* a title folded for search: lower case, diacritics stripped, spaces
   squeezed — "Kestavalla" finds "Kestävällä" */
export function foldForSearch(value: string): string {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/gu, "").toLowerCase().replace(/\s+/gu, " ").trim();
}

let cachedIndex: GovernedContextIndex | null = null;
let indexBuildAttempts = 0;
let successfulIndexBuilds = 0;
let lastSuccessfulBuildTiming: GovernedContextReaderBuildTiming | null = null;

export interface GovernedContextReaderBuildTiming {
  readonly manifestVerificationMs: number;
  readonly registryValidationMs: number;
  readonly recordIndexConstructionMs: number;
  readonly boundaryValidationMs: number;
  readonly totalMs: number;
}

export interface GovernedContextReaderRuntimeDiagnostics {
  readonly indexInitialized: boolean;
  readonly indexBuildAttempts: number;
  readonly successfulIndexBuilds: number;
  readonly lastSuccessfulBuildTiming: GovernedContextReaderBuildTiming | null;
}

function compareText(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0;
}

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function canonicalValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value)
      .sort(([left], [right]) => compareText(left, right))
      .map(([key, child]) => [key, canonicalValue(child)]));
  }
  return value;
}

function canonicalBytes(value: unknown): Buffer {
  return Buffer.from(`${JSON.stringify(canonicalValue(value))}\n`, "utf8");
}

function sameCanonical(left: unknown, right: unknown): boolean {
  return Buffer.compare(canonicalBytes(left), canonicalBytes(right)) === 0;
}

function sha256(value: string | Buffer): string {
  return createHash("sha256").update(value).digest("hex");
}

function isNonNegativeInteger(value: unknown): value is number {
  return Number.isSafeInteger(value) && Number(value) >= 0;
}

function assertText(value: unknown, field: string): asserts value is string {
  assert(typeof value === "string" && value.trim().length > 0, `${field} must be non-empty text`);
}

function assertSha256(value: unknown, field: string): asserts value is string {
  assert(typeof value === "string" && SHA256_PATTERN.test(value), `${field} must be a SHA-256`);
}

function freezeExplanation(value: PublicContextExplanation): PublicContextExplanation {
  return Object.freeze({
    ...value,
    prohibitedInterpretations: Object.freeze([...value.prohibitedInterpretations]),
  });
}

function validateExplanationRegistry(
  registry: ArtifactExplanationRegistry,
): ReadonlyMap<string, PublicContextExplanation> {
  assert(registry.schemaVersion === EXPLANATIONS_SCHEMA_VERSION, "explanation schema differs");
  assert(registry.registryVersion === TRACE_CONTEXT_EXPLANATION_REGISTRY_VERSION, "explanation registry version differs");
  assert(registry.policyVersion === TRACE_CONTEXT_GOVERNANCE_POLICY_VERSION, "explanation policy version differs");
  assert(registry.epistemicRole === "project_curated_context", "explanation epistemic role differs");
  assert(registry.termPlaceholder === "{term}", "explanation placeholder differs");
  assert(Array.isArray(registry.entries) && registry.entries.length === 3, "explanation registry count differs");
  const byCode = new Map<string, PublicContextExplanation>();
  for (const value of registry.entries) {
    assertText(value.explanationCode, "explanation code");
    assert(["medium", "theme", "movement_context"].includes(value.contextKind), "explanation kind differs");
    for (const [field, text] of Object.entries(value)) {
      if (field === "prohibitedInterpretations" || field === "contextKind") continue;
      assertText(text, `explanation ${value.explanationCode} ${field}`);
    }
    assert(Array.isArray(value.prohibitedInterpretations) && value.prohibitedInterpretations.length > 0, "prohibited interpretations are missing");
    for (const statement of value.prohibitedInterpretations) assertText(statement, "prohibited interpretation");
    assert(!byCode.has(value.explanationCode), "duplicate explanation code");
    byCode.set(value.explanationCode, freezeExplanation(value));
  }
  assert(byCode.has("CTX-MEDIUM") && byCode.has("CTX-THEME") && byCode.has("CTX-MOVEMENT"), "required explanation code is missing");
  return byCode;
}

function validateTerms(
  document: ArtifactTermsDocument,
  explanations: ReadonlyMap<string, PublicContextExplanation>,
): ReadonlyMap<string, ArtifactTerm> {
  assert(document.schemaVersion === TERMS_SCHEMA_VERSION, "term schema differs");
  assert(document.projectionId === TRACE_CONTEXT_PUBLIC_PROJECTION_ID, "term projection differs");
  assert(document.policyVersion === TRACE_CONTEXT_GOVERNANCE_POLICY_VERSION, "term policy differs");
  assert(document.idPolicyVersion === ID_POLICY_VERSION, "term ID policy differs");
  assert(document.counts?.total === EXPECTED_TERMS.total, "term count differs");
  assert(sameCanonical(document.counts.byKind, { medium: 10, movement_context: 7, theme: 8 }), "term kind counts differ");
  assert(Array.isArray(document.terms) && document.terms.length === EXPECTED_TERMS.total, "term rows differ");
  const byId = new Map<string, ArtifactTerm>();
  for (const term of document.terms) {
    assert(TERM_ID_PATTERN.test(term.id), "governed term ID is invalid");
    assert(["medium", "theme", "movement_context"].includes(term.kind), "governed term kind is invalid");
    assertText(term.label, "governed term label");
    assert(term.publicationState === "published", "term publication state differs");
    assert(isNonNegativeInteger(term.assignmentCount) && term.assignmentCount > 0, "term assignment count is invalid");
    assert(explanations.get(term.explanationCode)?.contextKind === term.kind, "term explanation did not resolve");
    assert(!byId.has(term.id), "duplicate governed term ID");
    byId.set(term.id, term);
  }
  return byId;
}

function validateRootMetadata(value: PublicContextRootMetadata): void {
  for (const [field, text] of Object.entries(value)) {
    assert(["creatorAttribution", "dateDisplay", "objectType", "sourceName"].includes(field), "unexpected root metadata field");
    assertText(text, `root metadata ${field}`);
    assert(!URL_PATTERN.test(text) && !UUID_PATTERN.test(text), `unsafe root metadata ${field}`);
  }
  assert(Object.keys(value).length === 4, "root metadata field count differs");
}

function validateRecords(
  document: ArtifactRecordsDocument,
  terms: ReadonlyMap<string, ArtifactTerm>,
  explanations: ReadonlyMap<string, PublicContextExplanation>,
): ReadonlyMap<string, ArtifactRecord> {
  assert(document.schemaVersion === TRACE_CONTEXT_PUBLIC_SCHEMA_VERSION, "record schema differs");
  assert(document.projectionId === TRACE_CONTEXT_PUBLIC_PROJECTION_ID, "record projection differs");
  assert(document.policyVersion === TRACE_CONTEXT_GOVERNANCE_POLICY_VERSION, "record policy differs");
  assert(document.mappingVersion === TRACE_CONTEXT_GOVERNED_MAPPING_VERSION, "record mapping differs");
  assert(document.explanationRegistryVersion === TRACE_CONTEXT_EXPLANATION_REGISTRY_VERSION, "record explanation version differs");
  assert(document.rootMetadataTextPolicyVersion === ROOT_TEXT_POLICY_VERSION, "root text policy differs");
  assert(isNonNegativeInteger(document.rootMetadataNormalizedFieldCount), "root normalization count is invalid");
  assert(document.sourceRelease?.id === SOURCE_RELEASE.id && document.sourceRelease.manifestSha256 === SOURCE_RELEASE.manifestSha256, "record release differs");
  assert(Array.isArray(document.records) && document.records.length === 7_995, "record count differs");

  const recordById = new Map<string, ArtifactRecord>();
  const representationIds = new Set<string>();
  const provenanceIds = new Set<string>();
  const assignmentCounts: Record<PublicContextRepresentationKind, number> = {
    medium: 0,
    movement_context: 0,
    theme: 0,
  };
  const observedTermAssignments = new Map<string, number>();
  let representationCount = 0;
  let priorStableId = "";
  for (const record of document.records) {
    const stableId = record.selectedRecord?.surfaceId;
    assert(typeof stableId === "string" && stableId.length <= 80 && PUBLIC_STABLE_ID_PATTERN.test(stableId), "public record ID is invalid");
    assert(priorStableId === "" || compareText(priorStableId, stableId) < 0, "public records are not strictly ordered");
    priorStableId = stableId;
    assertText(record.selectedRecord.title, "selected record title");
    assert(!UUID_PATTERN.test(record.selectedRecord.title), "selected record title contains an internal UUID");
    validateRootMetadata(record.selectedRecord.rootMetadata);
    assert(record.availability === "ready", "public Context availability differs");
    assert(Array.isArray(record.representations) && record.representations.length >= 2, "public Context record is incomplete");
    assert(record.counts?.representations === record.representations.length, "record representation count differs");
    assert(!recordById.has(stableId), "duplicate public Context record");
    recordById.set(stableId, record);
    for (const representation of record.representations) {
      representationCount += 1;
      assert(REPRESENTATION_ID_PATTERN.test(representation.id), "governed representation ID is invalid");
      assert(!representationIds.has(representation.id), "governed representation ID collision");
      representationIds.add(representation.id);
      assert(TERM_ID_PATTERN.test(representation.termId), "representation term ID is invalid");
      const term = terms.get(representation.termId);
      assert(term, "representation term did not resolve");
      assert(representation.kind === term.kind && representation.label === term.label, "representation term fields differ");
      assert(representation.explanationCode === term.explanationCode, "representation explanation differs from term");
      assert(representation.epistemicRole === "project_curated_context", "representation epistemic role differs");
      assert(representation.publicationState === "published", "representation publication differs");
      assert(explanations.get(representation.explanationCode)?.contextKind === representation.kind, "representation explanation did not resolve");
      const provenance = representation.provenance;
      assert(PROVENANCE_ID_PATTERN.test(provenance.provenanceId), "governed provenance ID is invalid");
      assert(!provenanceIds.has(provenance.provenanceId), "governed provenance ID collision");
      provenanceIds.add(provenance.provenanceId);
      assert(provenance.provenanceId === `CTXP:${sha256([PROVENANCE_ID_NAMESPACE, representation.id].join("\u0000"))}`, "governed provenance identity differs");
      assert(provenance.basis === "project_curated_typed_membership", "provenance basis differs");
      assert(provenance.sourceState === "proposed", "frozen source state was relabeled");
      assert(provenance.mappingPolicyVersion === TRACE_CONTEXT_GOVERNED_MAPPING_VERSION, "provenance mapping policy differs");
      assert(provenance.governancePolicyVersion === TRACE_CONTEXT_GOVERNANCE_POLICY_VERSION, "provenance governance policy differs");
      assert(provenance.decision === "PUBLISHED", "provenance decision differs");
      assert(provenance.sourceKind === (representation.kind === "movement_context" ? "movement" : representation.kind), "provenance source kind differs");
      assignmentCounts[representation.kind as PublicContextRepresentationKind] += 1;
      observedTermAssignments.set(term.id, (observedTermAssignments.get(term.id) ?? 0) + 1);
    }
  }
  assert(representationCount === EXPECTED_ASSIGNMENTS.total, "representation count differs");
  assert(sameCanonical(assignmentCounts, { medium: 7_995, movement_context: 115, theme: 7_996 }), "representation kind counts differ");
  for (const term of terms.values()) {
    assert(observedTermAssignments.get(term.id) === term.assignmentCount, "term assignment census differs");
  }
  return recordById;
}

function validateManifest(
  manifest: ArtifactManifest,
  payloads: Readonly<Record<string, unknown>>,
): void {
  assert(manifest.schemaVersion === MANIFEST_SCHEMA_VERSION, "Context manifest schema differs");
  assert(manifest.contextSchemaVersion === TRACE_CONTEXT_PUBLIC_SCHEMA_VERSION, "Context manifest DTO schema differs");
  assert(manifest.projectionId === TRACE_CONTEXT_PUBLIC_PROJECTION_ID, "Context projection identity differs");
  assertSha256(manifest.projectionSha256, "Context projection hash");
  assert(manifest.canonicalSerialization === CANONICAL_SERIALIZATION, "Context canonical serialization differs");
  assert(manifest.canonicalSourceState === "proposed", "Context canonical source state differs");
  assert(manifest.sourceRelease?.id === SOURCE_RELEASE.id && manifest.sourceRelease.manifestSha256 === SOURCE_RELEASE.manifestSha256, "Context source release differs");
  assert(manifest.governancePolicyVersion === TRACE_CONTEXT_GOVERNANCE_POLICY_VERSION, "Context governance policy differs");
  assert(manifest.explanationRegistryVersion === TRACE_CONTEXT_EXPLANATION_REGISTRY_VERSION, "Context explanation version differs");
  assert(manifest.idPolicyVersion === ID_POLICY_VERSION, "Context ID policy differs");
  assert(manifest.mappingVersion === TRACE_CONTEXT_GOVERNED_MAPPING_VERSION, "Context mapping version differs");
  assert(manifest.generatorVersion === GENERATOR_VERSION, "Context generator version differs");
  assert(manifest.rootTextPolicyVersion === ROOT_TEXT_POLICY_VERSION, "Context root text policy differs");
  assert(manifest.provenanceIdNamespace === PROVENANCE_ID_NAMESPACE, "Context provenance namespace differs");
  assert(manifest.releaseProfile?.path === RELEASE_PROFILE.path && manifest.releaseProfile.sha256 === RELEASE_PROFILE.sha256, "Context release profile differs");
  assert(manifest.realSemanticEdgeCount === 0 && manifest.regionContextNodeCount === 0, "prohibited Context node/edge count differs");

  const expectedFrequencies = Object.freeze({
    assignmentCounts: EXPECTED_ASSIGNMENTS,
    heldExcluded: Object.freeze({ controlledAssignmentSourceRowCount: 15_952, folderSourceRowCount: 23_880, objectCount: 7_928, regionSourceRowCount: 7_928 }),
    objectCoverage: EXPECTED_OBJECT_COVERAGE,
    publicationCounts: Object.freeze({ excluded: 0, held: 0, published: 16_106, qualified: 0 }),
    publicObjectCount: 7_995,
    regionHandoff: Object.freeze({ contextNodeCount: 0, decision: "DEFER_TO_SPACETIME", publicObjectCount: 7_995, sourceRowCount: 7_996, termCount: 93 }),
    representationHistogram: Object.freeze({ "2": 7_884, "3": 106, "4": 5 }),
    rootMetadataNormalizedFieldCount: 3,
    sameKindMultivalueObjectCount: 6,
    termCounts: EXPECTED_TERMS,
  });
  assert(sameCanonical(manifest.counts, expectedFrequencies), "Context manifest census differs");

  const frozenInputObject = Object.freeze(Object.fromEntries(
    [...manifest.frozenInputs]
      .sort((left, right) => compareText(left.path, right.path))
      .map((entry) => [entry.path, entry.sha256]),
  ));
  assert(sameCanonical(frozenInputObject, FROZEN_INPUT_SHA256), "Context frozen input binding differs");
  assert(manifest.eligibilityLedgerSha256 === FROZEN_INPUT_SHA256["docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv"], "eligibility ledger binding differs");
  assert(manifest.sourceArtifactSha256 === FROZEN_INPUT_SHA256["data/prefreeze_candidate_v48.sqlite"], "source artifact binding differs");

  let rawBytes = 0;
  for (const [filename, payload] of Object.entries(payloads)) {
    const bytes = canonicalBytes(payload);
    const digest = sha256(bytes);
    assert(manifest.artifactSha256?.[filename] === digest, `${filename} hash differs`);
    assert(manifest.artifactBytes?.[filename] === bytes.byteLength, `${filename} byte count differs`);
    rawBytes += bytes.byteLength;
  }
  assert(rawBytes === manifest.governedProjectionRawBytes, "Context raw byte census differs");
  assert(manifest.recordsRawBytes === manifest.artifactBytes["records.json"], "Context records byte census differs");
  assert(manifest.recordsSha256 === manifest.artifactSha256["records.json"], "Context records hash alias differs");
  assert(manifest.termRegistrySha256 === manifest.artifactSha256["terms.json"], "Context term hash alias differs");
  assert(manifest.explanationRegistrySha256 === manifest.artifactSha256["explanation-registry.json"], "Context explanation hash alias differs");
  assert(manifest.exceptionRegisterSha256 === manifest.artifactSha256["exception-register.json"], "Context exception hash alias differs");
  assert(manifest.governancePolicySha256 === manifest.artifactSha256["governance-policy.json"], "Context policy hash alias differs");

  const projectionHashMaterial = Object.freeze({
    artifactSha256: manifest.artifactSha256,
    contextSchemaVersion: TRACE_CONTEXT_PUBLIC_SCHEMA_VERSION,
    counts: manifest.counts,
    generatorVersion: GENERATOR_VERSION,
    governedProjectionGzipBytes: manifest.governedProjectionGzipBytes,
    governedProjectionRawBytes: manifest.governedProjectionRawBytes,
    governancePolicySha256: manifest.governancePolicySha256,
    governancePolicyVersion: TRACE_CONTEXT_GOVERNANCE_POLICY_VERSION,
    idPolicyVersion: ID_POLICY_VERSION,
    mappingVersion: TRACE_CONTEXT_GOVERNED_MAPPING_VERSION,
    projectionId: TRACE_CONTEXT_PUBLIC_PROJECTION_ID,
    provenanceIdNamespace: PROVENANCE_ID_NAMESPACE,
    rootTextPolicyVersion: ROOT_TEXT_POLICY_VERSION,
    sourceBindings: Object.freeze({
      frozenInputs: frozenInputObject,
      releaseProfile: RELEASE_PROFILE,
      sourceRelease: SOURCE_RELEASE,
    }),
  });
  assert(sha256(canonicalBytes(projectionHashMaterial)) === manifest.projectionSha256, "Context projection aggregate hash differs");
}

function buildIndex(): GovernedContextIndex {
  indexBuildAttempts += 1;
  const buildStarted = performance.now();
  const manifest = manifestJson as unknown as ArtifactManifest;
  const records = recordsJson as unknown as ArtifactRecordsDocument;
  const terms = termsJson as unknown as ArtifactTermsDocument;
  const explanations = explanationRegistryJson as unknown as ArtifactExplanationRegistry;
  const governancePolicy = governancePolicyJson as unknown as Readonly<Record<string, unknown>>;
  const exceptionRegister = exceptionRegisterJson as unknown as Readonly<Record<string, unknown>>;
  assert(governancePolicy.schemaVersion === GOVERNANCE_POLICY_SCHEMA_VERSION && governancePolicy.policyVersion === TRACE_CONTEXT_GOVERNANCE_POLICY_VERSION, "governance policy artifact differs");
  assert(exceptionRegister.schemaVersion === EXCEPTION_REGISTER_SCHEMA_VERSION && exceptionRegister.policyVersion === TRACE_CONTEXT_GOVERNANCE_POLICY_VERSION, "exception register artifact differs");

  const payloads = Object.freeze({
    "exception-register.json": exceptionRegister,
    "explanation-registry.json": explanations,
    "governance-policy.json": governancePolicy,
    "records.json": records,
    "terms.json": terms,
  });
  const manifestStarted = performance.now();
  validateManifest(manifest, payloads);
  const manifestVerificationMs = performance.now() - manifestStarted;
  const registryStarted = performance.now();
  const explanationByCode = validateExplanationRegistry(explanations);
  const termById = validateTerms(terms, explanationByCode);
  const registryValidationMs = performance.now() - registryStarted;
  const recordsStarted = performance.now();
  const recordById = validateRecords(records, termById, explanationByCode);
  const recordIndexConstructionMs = performance.now() - recordsStarted;
  const boundaryStarted = performance.now();
  const orderedRecords = [...recordById.values()];
  const sampleCount = 12;
  const sampleOptions = Object.freeze(Array.from({ length: sampleCount }, (_, index) => {
    const recordIndex = Math.floor((index * (orderedRecords.length - 1)) / (sampleCount - 1));
    const record = orderedRecords[recordIndex];
    assert(record, "governed Context sample did not resolve");
    return Object.freeze({
      stableId: record.selectedRecord.surfaceId,
      title: record.selectedRecord.title,
    });
  }));

  /* the reader-facing verdicts: the sealed reader-eligibility projection
     read directly (its own loader verifies against the Search index,
     which the Context branch must never reach) and gated here on its
     format, its release, its checksum and its count against this cohort */
  const eligibility = eligibilityJson as unknown as Readonly<{ format: string; release_id: string; rules_version: string; entries: readonly (readonly [string, string, string | null])[] }>;
  const eligibilityManifest = eligibilityManifestJson as unknown as Readonly<{ release_id: string; rules_version: string; eligibility_sha256: string; counts: Readonly<{ public: number }> }>;
  const eligibilitySerialized = `${JSON.stringify(eligibility)}\n`;
  assert(eligibility.format === "gda-reader-eligibility-v1", "reader eligibility format differs");
  assert(eligibility.release_id === SOURCE_RELEASE.id && eligibilityManifest.release_id === SOURCE_RELEASE.id, "reader eligibility release differs");
  assert(eligibility.rules_version === eligibilityManifest.rules_version, "reader eligibility rules differ");
  assert(eligibilityManifest.eligibility_sha256 === createHash("sha256").update(eligibilitySerialized).digest("hex"), "reader eligibility checksum differs");
  assert(eligibility.entries.length === eligibilityManifest.counts.public && eligibility.entries.length === recordById.size, "reader eligibility count differs from the public cohort");
  const readerFacingById = new Map(eligibility.entries.map(([id, verdict]) => [id, verdict === "INDEX_ELIGIBLE"] as const));
  assert(readerFacingById.size === eligibility.entries.length, "reader eligibility names a stable ID twice");

  /* the chooser's objects: every public record with its title folded for
     search and its reader-facing verdict; the examples are picked from
     the reader-facing ones by fixed criteria, first by stable ID — never
     by hand */
  const objects = Object.freeze(orderedRecords.map((record) => {
    const counts = { medium: 0, theme: 0, movement_context: 0 };
    for (const representation of record.representations) counts[representation.kind] += 1;
    return Object.freeze({
      stableId: record.selectedRecord.surfaceId,
      title: record.selectedRecord.title,
      folded: foldForSearch(record.selectedRecord.title),
      readerFacing: record.availability === "ready" && (readerFacingById.get(record.selectedRecord.surfaceId) ?? false),
      counts: Object.freeze(counts),
    });
  }));
  const readerFacing = objects.filter((entry) => entry.readerFacing);
  const kindsOf = (entry: GovernedContextObjectEntry) => [entry.counts.medium, entry.counts.theme, entry.counts.movement_context].filter((n) => n > 0).length;
  const total = (entry: GovernedContextObjectEntry) => entry.counts.medium + entry.counts.theme + entry.counts.movement_context;
  const taken = new Set<string>();
  const pick = (role: GovernedContextExampleRole, fits: (entry: GovernedContextObjectEntry) => boolean): GovernedContextExampleOption | null => {
    const entry = readerFacing.find((candidate) => !taken.has(candidate.stableId) && fits(candidate));
    if (!entry) return null;
    taken.add(entry.stableId);
    return Object.freeze({ stableId: entry.stableId, title: entry.title, role, counts: entry.counts });
  };
  const exampleOptions = Object.freeze([
    pick("three_contexts", (e) => kindsOf(e) === 3 && total(e) === 3),
    pick("medium_theme", (e) => e.counts.medium >= 1 && e.counts.theme >= 1 && e.counts.movement_context === 0 && total(e) === 2),
    pick("two_themes", (e) => e.counts.theme >= 2),
    pick("two_movements", (e) => e.counts.movement_context >= 2 && kindsOf(e) === 3),
    pick("other_language", (e) => /[^\u0000-\u007f]/u.test(e.title) && kindsOf(e) >= 2),
  ].filter((entry): entry is GovernedContextExampleOption => entry !== null));
  assert(exampleOptions.length >= 4, "governed Context examples did not resolve");
  const landingEntry = [...readerFacing]
    .filter((entry) => kindsOf(entry) === 3)
    .sort((a, b) => total(b) - total(a) || (a.stableId < b.stableId ? -1 : 1))[0] ?? readerFacing[0] ?? objects[0];
  assert(landingEntry, "governed Context landing record did not resolve");
  const landingRecord = Object.freeze({ stableId: landingEntry.stableId, title: landingEntry.title });

  const publicPayloadText = canonicalBytes({ explanations, records, terms }).toString("utf8");
  assert(!publicPayloadText.includes("ctxv49:"), "validation-only ID entered governed projection");
  assert(!RAW_SOURCE_TERM_PATTERN.test(publicPayloadText), "raw source term entered governed projection");
  assert(!UUID_PATTERN.test(publicPayloadText), "internal UUID entered governed projection");
  assert(!URL_PATTERN.test(publicPayloadText), "URL entered governed projection");

  const boundaryValidationMs = performance.now() - boundaryStarted;
  successfulIndexBuilds += 1;
  lastSuccessfulBuildTiming = Object.freeze({
    manifestVerificationMs,
    registryValidationMs,
    recordIndexConstructionMs,
    boundaryValidationMs,
    totalMs: performance.now() - buildStarted,
  });

  return Object.freeze({
    manifest,
    recordById,
    explanationByCode,
    sampleOptions,
    objects,
    exampleOptions,
    landingRecord,
    info: Object.freeze({
      projectionId: TRACE_CONTEXT_PUBLIC_PROJECTION_ID,
      projectionSha256: manifest.projectionSha256,
      researchReleaseId: SOURCE_RELEASE.id,
      researchManifestSha256: SOURCE_RELEASE.manifestSha256,
      recordCount: recordById.size,
      termCount: termById.size,
      representationCount: EXPECTED_ASSIGNMENTS.total,
      rawBytes: manifest.governedProjectionRawBytes,
      gzipBytes: manifest.governedProjectionGzipBytes,
    }),
  });
}

function getIndex(): GovernedContextIndex {
  if (!cachedIndex) cachedIndex = buildIndex();
  return cachedIndex;
}

function freezeAccessibleRow(value: PublicContextAccessibleRow): PublicContextAccessibleRow {
  return Object.freeze({
    ...value,
    values: Object.freeze(value.values.map((item) => Object.freeze({ ...item }))),
  });
}

function buildAccessibleRows(
  record: ArtifactRecord,
  representations: readonly PublicContextRepresentation[],
  explanationByCode: ReadonlyMap<string, PublicContextExplanation>,
): readonly PublicContextAccessibleRow[] {
  const root = record.selectedRecord;
  const rows: PublicContextAccessibleRow[] = [freezeAccessibleRow({
    id: `selected:${root.surfaceId}`,
    category: "selected_record",
    label: root.title,
    explanationCode: null,
    values: [
      { label: "Stable public ID", value: root.surfaceId },
      { label: "Source-reported attribution", value: root.rootMetadata.creatorAttribution },
      { label: "Source-reported object type", value: root.rootMetadata.objectType },
      { label: "Source-reported date", value: root.rootMetadata.dateDisplay },
      { label: "Source name", value: root.rootMetadata.sourceName },
    ],
  })];
  for (const representation of representations) {
    const explanation = explanationByCode.get(representation.explanationCode);
    assert(explanation, "accessible explanation did not resolve");
    rows.push(freezeAccessibleRow({
      id: `representation:${representation.id}`,
      category: "context_representation",
      label: `${explanation.publicLabel}: ${representation.label}`,
      explanationCode: representation.explanationCode,
      values: [
        { label: "Context type", value: explanation.publicLabel },
        { label: "Publication state", value: representation.publicationState },
        { label: "Epistemic role", value: "Project-curated context" },
        { label: "Source basis", value: explanation.sourceBasis },
        { label: "Source state", value: representation.provenance.sourceState },
        { label: "Governance policy", value: representation.provenance.governancePolicyVersion },
        { label: "Permitted interpretation", value: explanation.permittedInterpretation.replaceAll("{term}", representation.label) },
      ],
    }));
  }
  return Object.freeze(rows);
}

function projectDataset(index: GovernedContextIndex, record: ArtifactRecord): PublicContextDataset {
  const representations = Object.freeze(record.representations.map((representation) => Object.freeze({
    ...representation,
    provenance: Object.freeze({ ...representation.provenance }),
  }))) as readonly PublicContextRepresentation[];
  const usedExplanationCodes = [...new Set(representations.map((item) => item.explanationCode))]
    .sort(compareText);
  const explanations = Object.freeze(usedExplanationCodes.map((code) => {
    const explanation = index.explanationByCode.get(code);
    assert(explanation, "selected explanation did not resolve");
    return explanation;
  }));
  const byKind = Object.freeze({
    medium: representations.filter((item) => item.kind === "medium").length,
    theme: representations.filter((item) => item.kind === "theme").length,
    movementContext: representations.filter((item) => item.kind === "movement_context").length,
  });
  return Object.freeze({
    schemaVersion: TRACE_CONTEXT_PUBLIC_SCHEMA_VERSION,
    release: Object.freeze({
      researchReleaseId: SOURCE_RELEASE.id,
      researchManifestSha256: SOURCE_RELEASE.manifestSha256,
      contextProjectionId: TRACE_CONTEXT_PUBLIC_PROJECTION_ID,
      contextProjectionSha256: index.manifest.projectionSha256,
    }),
    selectedRecord: Object.freeze({
      surfaceId: record.selectedRecord.surfaceId,
      title: record.selectedRecord.title,
      rootMetadata: Object.freeze({ ...record.selectedRecord.rootMetadata }),
    }),
    availability: record.representations.length > 0 ? "ready" : "empty",
    representations,
    counts: Object.freeze({ representations: representations.length, byKind }),
    explanationRegistryVersion: TRACE_CONTEXT_EXPLANATION_REGISTRY_VERSION,
    explanations,
    accessibleRows: buildAccessibleRows(record, representations, index.explanationByCode),
  });
}

export function resetGovernedContextReaderForTests(): void {
  cachedIndex = null;
  indexBuildAttempts = 0;
  successfulIndexBuilds = 0;
  lastSuccessfulBuildTiming = null;
}

/** Test/rehearsal diagnostics only; this never initializes or mutates the runtime index. */
export function getGovernedContextReaderRuntimeDiagnosticsForTests(): GovernedContextReaderRuntimeDiagnostics {
  return Object.freeze({
    indexInitialized: cachedIndex !== null,
    indexBuildAttempts,
    successfulIndexBuilds,
    lastSuccessfulBuildTiming,
  });
}

export function getGovernedContextProjectionInfo(): GovernedContextProjectionInfo {
  return getIndex().info;
}

export function getGovernedContextSampleOptions(): readonly GovernedContextSampleOption[] {
  return getIndex().sampleOptions;
}

export function getGovernedContextExampleOptions(): readonly GovernedContextExampleOption[] {
  return getIndex().exampleOptions;
}

export function getGovernedContextLandingRecord(): GovernedContextSampleOption {
  return getIndex().landingRecord;
}

/* the chooser's search: a public record ID (or its prefix) finds any
   public record; words find reader-facing titles only — record-only
   objects (a source identifier for a title) stay reachable by ID alone */
export function searchGovernedContextObjects(query: string, limit = 8): readonly GovernedContextObjectEntry[] {
  const raw = query.trim().slice(0, 80);
  if (raw.length === 0) return Object.freeze([]);
  const objects = getIndex().objects;
  const upper = raw.toUpperCase();
  if (/^SURF(?:-|$)/u.test(upper)) {
    return Object.freeze(objects.filter((entry) => entry.stableId.startsWith(upper)).slice(0, limit));
  }
  const folded = foldForSearch(raw);
  if (folded.length < 2) return Object.freeze([]);
  const starts: GovernedContextObjectEntry[] = [];
  const within: GovernedContextObjectEntry[] = [];
  for (const entry of objects) {
    if (!entry.readerFacing) continue;
    if (entry.folded.startsWith(folded)) starts.push(entry);
    else if (entry.folded.includes(folded)) within.push(entry);
    if (starts.length >= limit) break;
  }
  return Object.freeze([...starts, ...within].slice(0, limit));
}

export function lookupGovernedContextDataset(
  objectId: string,
  release: Readonly<{
    researchReleaseId: string;
    researchManifestSha256: string;
  }> = Object.freeze({
    researchReleaseId: SOURCE_RELEASE.id,
    researchManifestSha256: SOURCE_RELEASE.manifestSha256,
  }),
): GovernedContextLookup {
  if (
    typeof objectId !== "string"
    || objectId.length > 80
    || !PUBLIC_STABLE_ID_PATTERN.test(objectId)
  ) return Object.freeze({
    ok: false as const,
    code: "INVALID_ARGUMENT" as const,
    message: "The Context object ID is not a valid public stable ID.",
  });

  let index: GovernedContextIndex;
  try {
    index = getIndex();
  } catch {
    return Object.freeze({
      ok: false as const,
      code: "INTEGRITY_FAILURE" as const,
      message: "The governed Context projection failed its integrity contract.",
    });
  }
  if (
    release.researchReleaseId !== index.info.researchReleaseId
    || release.researchManifestSha256 !== index.info.researchManifestSha256
  ) return Object.freeze({
    ok: false as const,
    code: "RELEASE_VERSION_MISMATCH" as const,
    message: "The governed Context projection is incompatible with the opened research release.",
  });

  const record = index.recordById.get(objectId);
  if (!record) return Object.freeze({
    ok: false as const,
    code: "NOT_FOUND" as const,
    message: GENERIC_NOT_FOUND_MESSAGE,
  });
  try {
    return Object.freeze({ ok: true as const, data: projectDataset(index, record) });
  } catch {
    return Object.freeze({
      ok: false as const,
      code: "INTEGRITY_FAILURE" as const,
      message: "The selected governed Context record failed its integrity contract.",
    });
  }
}
