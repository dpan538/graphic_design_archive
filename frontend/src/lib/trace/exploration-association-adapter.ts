/** Structural mirror for Python-authored TRACE Round 14 association decisions. */

export class AssociationAdapterError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.code = code;
  }
}

export const ROUND14_GENERIC_TYPES = [
  "TEMPORAL_HISTORICAL_CONTEXT", "INSTITUTIONAL_PROFESSIONAL", "CULTURAL_DISCURSIVE",
  "ECONOMIC_COMMERCIAL", "SOCIAL_IDENTITY", "MATERIAL_TECHNOLOGICAL",
  "CIRCULATION_EXCHANGE", "PRACTICE_PRODUCTION",
] as const;
export const ROUND14_EVIDENCE_STATUSES = [
  "EXTERNALLY_SUPPORTED", "SOURCE_SUPPORTED", "QUALIFIED", "INSUFFICIENT",
] as const;

const PACKAGE_KEYS = [
  "packageId", "version", "methodVersion", "pythonNormative", "typescriptMirrorMode",
  "selectedThresholds", "taxonomy", "evidenceStatusVocabulary", "assessments", "canonicalHash",
] as const;
const ASSESSMENT_KEYS = [
  "assessmentId", "nodeA", "nodeB", "primaryGenericType", "secondaryGenericType",
  "historicalScope", "contextScope", "associationStrength", "evidenceConfidence", "evidenceStatus",
  "rubricDimensions", "externalSourceRefs", "archiveSourceRefs", "directNeighbourPass", "skipOnePass",
  "qualification", "decisionReason", "methodVersion", "activeForProximity", "redirectTargets",
  "calibrationStratum", "hardNegative", "cooccurrenceOnly",
] as const;
const DIMENSIONS = ["D1", "D2", "D3", "D4", "D5", "D6", "D7"] as const;

function record(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new AssociationAdapterError("INVALID_TYPE", "object required");
  }
  return value as Record<string, unknown>;
}

function exact(value: unknown, keys: readonly string[]): Record<string, unknown> {
  const item = record(value);
  if (Object.keys(item).length !== keys.length || Object.keys(item).some((key) => !keys.includes(key))) {
    throw new AssociationAdapterError("EXACT_FIELD_CONTRACT", "unknown or missing field");
  }
  return item;
}

function strings(value: unknown): string[] {
  if (!Array.isArray(value) || !value.every((item) => typeof item === "string" && item.length > 0)) {
    throw new AssociationAdapterError("INVALID_STRING_ARRAY", "non-empty strings required");
  }
  if (new Set(value).size !== value.length) throw new AssociationAdapterError("DUPLICATE_REFERENCE", "duplicate array value");
  return value;
}

function canonicalize(value: unknown): unknown {
  if (value === null || typeof value === "string" || typeof value === "boolean") return value;
  if (typeof value === "number" && Number.isInteger(value)) return value;
  if (Array.isArray(value)) return value.map(canonicalize);
  if (typeof value === "object" && value !== null) {
    const item = value as Record<string, unknown>;
    return Object.fromEntries(Object.keys(item).sort().map((key) => [key, canonicalize(item[key])]));
  }
  throw new AssociationAdapterError("NON_CANONICAL_VALUE", "unsupported canonical value");
}

export async function hashRound14Value(value: unknown): Promise<string> {
  const bytes = new TextEncoder().encode(JSON.stringify(canonicalize(value)));
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

export async function validateRound14AssociationPackage(value: unknown): Promise<Record<string, unknown>> {
  const pkg = exact(value, PACKAGE_KEYS);
  if (pkg.packageId !== "trace-exploration-generic-association-assessments-v1" || pkg.version !== "1") {
    throw new AssociationAdapterError("PACKAGE_IDENTITY", "unexpected package identity");
  }
  if (pkg.methodVersion !== "trace-generic-association-rubric-v1" || pkg.pythonNormative !== true || pkg.typescriptMirrorMode !== "SCHEMA_AND_FROZEN_DECISION_VALIDATION_ONLY") {
    throw new AssociationAdapterError("NORMATIVE_BOUNDARY", "Python normative boundary changed");
  }
  if (JSON.stringify(pkg.taxonomy) !== JSON.stringify(ROUND14_GENERIC_TYPES) || JSON.stringify(pkg.evidenceStatusVocabulary) !== JSON.stringify(ROUND14_EVIDENCE_STATUSES)) {
    throw new AssociationAdapterError("CLOSED_VOCABULARY", "closed vocabulary changed");
  }
  exact(pkg.selectedThresholds, ["directNeighbour", "skipOne"]);
  if (!Array.isArray(pkg.assessments) || pkg.assessments.length !== 35) {
    throw new AssociationAdapterError("ASSESSMENT_COUNT", "bounded calibration package must contain 35 assessments");
  }
  const ids = new Set<string>();
  for (const raw of pkg.assessments) {
    const item = exact(raw, ASSESSMENT_KEYS);
    if (typeof item.assessmentId !== "string" || ids.has(item.assessmentId)) throw new AssociationAdapterError("ASSESSMENT_ID", "duplicate or invalid assessment id");
    ids.add(item.assessmentId);
    if (typeof item.nodeA !== "string" || typeof item.nodeB !== "string" || item.nodeA === item.nodeB) throw new AssociationAdapterError("PAIR_IDENTITY", "two distinct concept labels required");
    if (!ROUND14_GENERIC_TYPES.includes(item.primaryGenericType as (typeof ROUND14_GENERIC_TYPES)[number])) throw new AssociationAdapterError("CLOSED_VOCABULARY", "unknown primary type");
    if (item.secondaryGenericType !== null && (!ROUND14_GENERIC_TYPES.includes(item.secondaryGenericType as (typeof ROUND14_GENERIC_TYPES)[number]) || item.secondaryGenericType === item.primaryGenericType)) throw new AssociationAdapterError("CLOSED_VOCABULARY", "invalid secondary type");
    const dimensions = exact(item.rubricDimensions, DIMENSIONS);
    if (Object.values(dimensions).some((score) => !Number.isInteger(score) || Number(score) < 0 || Number(score) > 2)) throw new AssociationAdapterError("RUBRIC_RANGE", "ordinal dimension out of range");
    const external = strings(item.externalSourceRefs); const archive = strings(item.archiveSourceRefs); const redirects = strings(item.redirectTargets);
    if (redirects.some((url) => !url.startsWith("https://"))) throw new AssociationAdapterError("UNSTABLE_REDIRECT", "HTTPS redirect required");
    if (typeof item.qualification !== "string" || !item.qualification.trim() || typeof item.decisionReason !== "string" || !item.decisionReason.trim()) throw new AssociationAdapterError("QUALIFICATION_LOSS", "qualification and reason required");
    const direct = item.directNeighbourPass === true; const skip = item.skipOnePass === true; const active = item.activeForProximity === true;
    if (active !== (direct || skip)) throw new AssociationAdapterError("FROZEN_DECISION_INVARIANT", "active flag does not match frozen decisions");
    if (item.cooccurrenceOnly === true && active) throw new AssociationAdapterError("COOCCURRENCE_ACTIVATION", "co-occurrence cannot activate proximity");
    if (item.evidenceStatus === "EXTERNALLY_SUPPORTED" && external.length === 0) throw new AssociationAdapterError("PROVENANCE_STATUS", "external source required");
    if (item.evidenceStatus === "SOURCE_SUPPORTED" && (archive.length === 0 || external.length !== 0)) throw new AssociationAdapterError("PROVENANCE_STATUS", "source-only provenance required");
    if ((item.evidenceStatus === "QUALIFIED" || item.evidenceStatus === "INSUFFICIENT") && active) throw new AssociationAdapterError("INACTIVE_STATUS_ACTIVATION", "inactive evidence status cannot activate");
    if (active && redirects.length === 0) throw new AssociationAdapterError("REDIRECT_REQUIRED", "active assessment requires a stable redirect");
  }
  const { canonicalHash, ...unsigned } = pkg;
  if (typeof canonicalHash !== "string" || await hashRound14Value(unsigned) !== canonicalHash) {
    throw new AssociationAdapterError("HASH_MISMATCH", "canonical package hash mismatch");
  }
  return pkg;
}
