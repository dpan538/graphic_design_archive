/** Structural parity validator for Python-authored TRACE Round 15 images. */

export class CompositionAdapterError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.code = code;
  }
}
const PACKAGE_KEYS = [
  "package_id", "version", "source_sha", "method_version", "python_normative",
  "typescript_mirror_mode", "images", "canonical_hash",
] as const;
const IMAGE_KEYS = [
  "schema_version", "semantic_core", "evidence_core", "composition_core",
  "presentation_hints", "provenance", "audit", "semantic_core_hash", "presentation_hash",
] as const;

function record(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new CompositionAdapterError("INVALID_TYPE", "object required");
  }
  return value as Record<string, unknown>;
}

function exact(value: unknown, keys: readonly string[]): Record<string, unknown> {
  const item = record(value);
  if (Object.keys(item).length !== keys.length || Object.keys(item).some((key) => !keys.includes(key))) {
    throw new CompositionAdapterError("EXACT_FIELD_CONTRACT", "unknown or missing field");
  }
  return item;
}

function strings(value: unknown): string[] {
  if (!Array.isArray(value) || !value.every((item) => typeof item === "string" && item.length > 0)) {
    throw new CompositionAdapterError("INVALID_STRING_ARRAY", "non-empty strings required");
  }
  if (new Set(value).size !== value.length) throw new CompositionAdapterError("DUPLICATE_VALUE", "array values must be unique");
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
  throw new CompositionAdapterError("NON_CANONICAL_VALUE", "unsupported canonical value");
}

export async function hashRound15Value(value: unknown): Promise<string> {
  const bytes = new TextEncoder().encode(JSON.stringify(canonicalize(value)));
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

export type Round15ParityResult = {
  imageCount: number;
  crossRuntimeDecisionMismatchCount: number;
  crossRuntimeHashMismatchCount: number;
  typescriptOnlySemanticRuleCount: number;
};

export async function validateRound15CompositionAudit(
  value: unknown,
  round14Package: unknown,
): Promise<Round15ParityResult> {
  const pkg = exact(value, PACKAGE_KEYS);
  if (pkg.package_id !== "trace-exploration-composition-decision-audit-v1" || pkg.version !== "1") {
    throw new CompositionAdapterError("PACKAGE_IDENTITY", "unexpected Round 15 package identity");
  }
  if (pkg.source_sha !== "cf4490e93449a46823a6de0c0676e431a7da6738" || pkg.method_version !== "trace-evidence-governed-composition-v1") {
    throw new CompositionAdapterError("SOURCE_OR_METHOD", "frozen source or method changed");
  }
  if (pkg.python_normative !== true || pkg.typescript_mirror_mode !== "FROZEN_SEMANTIC_VALIDATION_AND_PRESENTATION_ONLY") {
    throw new CompositionAdapterError("NORMATIVE_BOUNDARY", "TypeScript cannot become normative");
  }
  const { canonical_hash: canonicalHash, ...unsigned } = pkg;
  if (typeof canonicalHash !== "string" || await hashRound15Value(unsigned) !== canonicalHash) {
    throw new CompositionAdapterError("PACKAGE_HASH_MISMATCH", "composition audit canonical hash mismatch");
  }

  const round14 = record(round14Package);
  if (!Array.isArray(round14.assessments)) throw new CompositionAdapterError("ROUND14_PACKAGE", "Round 14 assessments required");
  const activeIds = new Set(
    round14.assessments
      .map(record)
      .filter((item) => item.activeForProximity === true)
      .map((item) => String(item.assessmentId)),
  );
  if (activeIds.size !== 21) throw new CompositionAdapterError("ROUND14_ACTIVE_COUNT", "21 frozen passes required");
  if (!Array.isArray(pkg.images) || pkg.images.length < 20) throw new CompositionAdapterError("IMAGE_COUNT", "bounded research corpus required");

  let decisionMismatchCount = 0;
  let hashMismatchCount = 0;
  for (const rawImage of pkg.images) {
    const image = exact(rawImage, IMAGE_KEYS);
    if (image.schema_version !== "bounded-semantic-image-v1") throw new CompositionAdapterError("IMAGE_VERSION", "unexpected semantic image version");
    const semantic = record(image.semantic_core);
    const admitted = strings(semantic.admitted_association_ids);
    const qualified = new Set(strings(semantic.qualified_association_ids));
    if (admitted.some((id) => !qualified.has(id) || !activeIds.has(id))) decisionMismatchCount += 1;
    if (await hashRound15Value(semantic) !== image.semantic_core_hash) hashMismatchCount += 1;
    if (await hashRound15Value(image.presentation_hints) !== image.presentation_hash) hashMismatchCount += 1;

    const composition = record(image.composition_core);
    if (composition.arbitration_method !== "PARETO_MINIMAL_SUFFICIENT_V1" || composition.degree_bound !== 2) {
      throw new CompositionAdapterError("ARBITRATION_CONTRACT", "Python-authored arbitration contract changed");
    }
    if (!Array.isArray(composition.candidate_decisions)) throw new CompositionAdapterError("CANDIDATE_DECISIONS", "candidate decisions required");
    for (const rawCandidate of composition.candidate_decisions) {
      const candidate = record(rawCandidate);
      if (candidate.semantic_eligibility === "NOT_QUALIFIED" && candidate.decision_state !== "INELIGIBLE_CONTROL") decisionMismatchCount += 1;
      if (candidate.decision_state === "ADMITTED" && !admitted.includes(String(candidate.assessment_id))) decisionMismatchCount += 1;
    }

    const hints = record(image.presentation_hints);
    if (hints.semantic_mutation_permitted !== false || !Array.isArray(hints.edge_hints)) {
      throw new CompositionAdapterError("PRESENTATION_BOUNDARY", "presentation hints cannot change semantics");
    }
    for (const rawEdge of hints.edge_hints) {
      const edge = record(rawEdge);
      if (edge.arrowhead !== false || edge.stroke_width !== 2 || !admitted.includes(String(edge.association_id))) decisionMismatchCount += 1;
    }
    if (!Array.isArray(image.provenance) || new Set(image.provenance.map((row) => String(record(row).assessment_id))).size !== admitted.length) {
      decisionMismatchCount += 1;
    }
  }
  return {
    imageCount: pkg.images.length,
    crossRuntimeDecisionMismatchCount: decisionMismatchCount,
    crossRuntimeHashMismatchCount: hashMismatchCount,
    typescriptOnlySemanticRuleCount: 0,
  };
}
