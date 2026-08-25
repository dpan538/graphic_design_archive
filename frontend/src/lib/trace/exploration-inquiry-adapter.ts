/** Strict TypeScript compatibility adapter for Python-authored inquiry artifacts. */

export const INQUIRY_TREE_STRATEGIES = [
  "LINEAR_PATH", "BINARY_FORK", "BINARY_CONVERGENCE", "QUALIFIED_PATH",
  "REFLEXIVE_RETURN", "EVIDENCE_GAP_TREE",
] as const;
export const INQUIRY_LINK_KINDS = [
  "OPEN_QUESTION", "CONTRAST_QUESTION", "CONDITION_QUESTION", "QUALIFICATION_QUESTION",
  "REFLEXIVE_QUESTION", "EVIDENCE_GAP_QUESTION",
] as const;

export class InquiryAdapterError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.code = code;
  }
}

const SORTED_STRING_ARRAY_KEYS = new Set([
  "allowedOrigins", "allowedTreeStrategies", "clusterHandoffIds", "contestationRefs",
  "convergenceSourceItemIds", "evidenceRefs", "gapRefs", "grammarAttestationIds", "grammarAttestationRefs",
  "lexicalAttestationIds", "observedChainIds", "pairQuestionIds", "qualificationRefs",
  "sourceIds", "unresolvedGapRefs", "vocabularyGapIds",
]);
const ORDERED_ARRAY_KEYS = new Set(["candidateSenseIds", "orderedFlowIds", "orderedNodeConceptIds", "treeItems"]);
const SORTED_OBJECT_ARRAY_KEYS: Readonly<Record<string, string>> = {
  candidates: "candidateId",
  semanticNodeRefs: "senseId",
};

function canonicalize(value: unknown, key?: string): unknown {
  if (value === null || typeof value === "string" || typeof value === "boolean") return value;
  if (typeof value === "number") {
    if (!Number.isInteger(value)) throw new InquiryAdapterError("FLOAT_PROHIBITED", "floating point semantic input is prohibited");
    return value;
  }
  if (Array.isArray(value)) {
    const items = value.map((item) => canonicalize(item));
    if (ORDERED_ARRAY_KEYS.has(key ?? "")) return items;
    if (SORTED_STRING_ARRAY_KEYS.has(key ?? "")) {
      if (!items.every((item) => typeof item === "string")) throw new InquiryAdapterError("INVALID_TYPE", `${key} must contain strings`);
      return [...items].sort();
    }
    const sortKey = SORTED_OBJECT_ARRAY_KEYS[key ?? ""];
    if (sortKey) return [...items].sort((left, right) => String((left as Record<string, unknown>)[sortKey]).localeCompare(String((right as Record<string, unknown>)[sortKey])));
    throw new InquiryAdapterError("UNKNOWN_ARRAY_ORDER", `no canonical ordering rule for ${String(key)}`);
  }
  if (typeof value === "object" && value !== null) {
    const record = value as Record<string, unknown>;
    return Object.fromEntries(Object.keys(record).sort().map((name) => [name, canonicalize(record[name], name)]));
  }
  throw new InquiryAdapterError("INVALID_TYPE", "value is not canonically serializable");
}

export function canonicalSerializeInquiryValue(value: unknown): string {
  return JSON.stringify(canonicalize(value));
}

export async function hashInquiryValue(value: unknown): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(canonicalSerializeInquiryValue(value)));
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function record(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new InquiryAdapterError("INVALID_TYPE", "object required");
  return value as Record<string, unknown>;
}

function exact(value: unknown, required: readonly string[], optional: readonly string[] = []): Record<string, unknown> {
  const item = record(value);
  const allowed = new Set([...required, ...optional]);
  if (Object.keys(item).some((key) => !allowed.has(key))) throw new InquiryAdapterError("UNKNOWN_FIELD", "unknown object field");
  if (required.some((key) => !(key in item))) throw new InquiryAdapterError("MISSING_FIELD", "required object field missing");
  return item;
}

function strings(value: unknown, code = "DUPLICATE_ID"): string[] {
  if (!Array.isArray(value) || !value.every((item) => typeof item === "string" && item.trim())) throw new InquiryAdapterError("EMPTY_VALUE", "non-empty string array required");
  if (new Set(value).size !== value.length) throw new InquiryAdapterError(code, "duplicate array identity");
  return value;
}

const FREEZE_KEYS = ["packageId", "version", "round9CandidateRegistrySha256", "round10InputTermSha256", "round10CommitSha", "round11CommitSha", "active", "candidates", "canonicalHash"];
const CANDIDATE_KEYS = ["candidateId", "senseId", "label", "researchStatus", "round9Decision", "round10NodeRoleDecision", "technicalRole", "plainLanguageGlossRef", "argumentRoleRef", "directionalityStatus", "qualificationStatus", "contestationStatus", "lexicalAttestationIds", "grammarAttestationIds", "sourceIds", "pairQuestionIds", "clusterHandoffIds", "observedChainIds", "vocabularyGapIds", "active"];
const SEED_KEYS = ["seedId", "seedKind", "candidateSenseIds", "researchStatus", "pairDecision", "evidenceRefs", "grammarAttestationRefs", "unresolvedGapRefs", "allowedTreeStrategies", "canonicalTreeStrategy", "plainLanguageResearchQuestion", "historicalClaim", "publicExportable", "allowedOrigins"];
const FLOW_KEYS = ["flowId", "origin", "carrierKind", "linkKind", "candidateSenseIds", "navigationDirection", "historicalDirectionStatus", "historicalClaim", "semanticRelation", "evidenceBackedHistoricalFlow"];
const ITEM_REQUIRED = ["itemId", "itemKind", "parentItemId", "depth", "order", "label", "evidenceRefs", "gapRefs"];
const INSTANCE_KEYS = ["instanceId", "instanceVersion", "freezePackageHash", "seedId", "seedHash", "treeStrategy", "treeStrategyVersion", "rootInquiry", "semanticNodeRefs", "primaryInquiryFlow", "treeItems", "evidenceCoverage", "sourceCoverage", "qualificationRefs", "contestationRefs", "gapRefs", "inclusionExplanation", "nonClaimExplanation", "evidenceSummary", "limitationStatement", "historicalClaim", "semanticRelation", "publicExportable", "activationState", "researchPreviewOnly", "canonicalHash"];
const NODE_KEYS = ["candidateId", "senseId", "label", "researchStatus", "round9Decision", "round10NodeRoleDecision", "technicalRole", "plainLanguageGlossRef", "argumentRoleRef", "directionalityStatus", "qualificationStatus", "contestationStatus", "lexicalAttestationIds", "grammarAttestationIds", "sourceIds"];
/* exploration-guard:allow-denial-start */
const CONTAMINATION = new Map([
  ["archiveobjectid", "ARCHIVE_OBJECT_CONTAMINATION"], ["objectid", "ARCHIVE_OBJECT_CONTAMINATION"],
  ["recordid", "ARCHIVE_OBJECT_CONTAMINATION"], ["surfaceid", "ARCHIVE_OBJECT_CONTAMINATION"],
  ["objecttitle", "ARCHIVE_OBJECT_CONTAMINATION"], ["thumbnail", "ARCHIVE_OBJECT_CONTAMINATION"],
  ["recordurl", "ARCHIVE_OBJECT_CONTAMINATION"], ["objecthref", "ARCHIVE_OBJECT_CONTAMINATION"],
  ["contextdto", "CONTEXT_CONTAMINATION"], ["contextpayload", "CONTEXT_CONTAMINATION"],
  ["spacetimedto", "SPACETIME_CONTAMINATION"], ["spacetimepayload", "SPACETIME_CONTAMINATION"],
  ["modelid", "EXTERNAL_MODEL_CONTAMINATION"], ["modelprovenance", "EXTERNAL_MODEL_CONTAMINATION"],
  ["embeddingmodel", "EXTERNAL_MODEL_CONTAMINATION"], ["vectorref", "VECTOR_REFERENCE_CONTAMINATION"],
  ["vectorreference", "VECTOR_REFERENCE_CONTAMINATION"],
]);
/* exploration-guard:allow-denial-end */
const CLAIM = /\b(caused|led to|became|influenced)\b/i;

function contamination(value: unknown): void {
  if (Array.isArray(value)) return value.forEach(contamination);
  if (typeof value !== "object" || value === null) return;
  const item = value as Record<string, unknown>;
  for (const key of Object.keys(item)) {
    const code = CONTAMINATION.get(key.replaceAll("_", "").replaceAll("-", "").toLowerCase());
    if (code) throw new InquiryAdapterError(code, "structural contamination detected");
  }
  Object.values(item).forEach(contamination);
}

export async function validateCandidateFreeze(value: unknown): Promise<Record<string, unknown>> {
  contamination(value);
  const freeze = exact(value, FREEZE_KEYS);
  if (freeze.packageId !== "trace-exploration-research-candidates-v1" || freeze.version !== "1" || freeze.active !== false) throw new InquiryAdapterError("STATUS_MUTATION", "freeze identity/status changed");
  if (!Array.isArray(freeze.candidates) || freeze.candidates.length !== 16) throw new InquiryAdapterError("CANDIDATE_COUNT", "freeze must contain 16 candidates");
  const ids: string[] = [], senses: string[] = [];
  for (const raw of freeze.candidates) {
    const candidate = exact(raw, CANDIDATE_KEYS);
    ids.push(String(candidate.candidateId)); senses.push(String(candidate.senseId));
    for (const key of ["lexicalAttestationIds", "grammarAttestationIds", "sourceIds", "pairQuestionIds", "clusterHandoffIds", "observedChainIds", "vocabularyGapIds"]) strings(candidate[key]);
    if (candidate.active !== false) throw new InquiryAdapterError("STATUS_MUTATION", "candidate activated");
  }
  if (new Set(ids).size !== 16 || new Set(senses).size !== 16) throw new InquiryAdapterError("DUPLICATE_SEMANTIC_ID", "duplicate frozen identity");
  const { canonicalHash, ...unsigned } = freeze;
  if (await hashInquiryValue(unsigned) !== canonicalHash) throw new InquiryAdapterError("HASH_MISMATCH", "freeze hash mismatch");
  return freeze;
}

export function validateInquirySeed(value: unknown): Record<string, unknown> {
  contamination(value);
  const seed = exact(value, SEED_KEYS);
  const senses = strings(seed.candidateSenseIds);
  if ((seed.seedKind === "PAIR_RESEARCH_QUESTION" ? 2 : seed.seedKind === "SINGLE_NODE_INQUIRY" ? 1 : 0) !== senses.length) throw new InquiryAdapterError("ARITY_MISMATCH", "seed arity mismatch");
  if (seed.historicalClaim !== false || seed.publicExportable !== false || JSON.stringify(seed.allowedOrigins) !== '["RESEARCH_INQUIRY"]') throw new InquiryAdapterError("ORIGIN_POLICY_VIOLATION", "research-only origin/status required");
  if (typeof seed.plainLanguageResearchQuestion !== "string" || !seed.plainLanguageResearchQuestion.endsWith("?") || CLAIM.test(seed.plainLanguageResearchQuestion)) throw new InquiryAdapterError("QUESTION_FORM_REQUIRED", "question form required");
  for (const key of ["evidenceRefs", "grammarAttestationRefs", "unresolvedGapRefs", "allowedTreeStrategies"]) strings(seed[key]);
  return seed;
}

export function validateInquiryTree(value: unknown): Record<string, unknown> {
  contamination(value);
  const tree = exact(value, ["rootInquiryId", "strategy", "primaryInquiryFlow", "treeItems"]);
  const flow = exact(tree.primaryInquiryFlow, FLOW_KEYS);
  if (flow.origin !== "RESEARCH_INQUIRY" || flow.carrierKind !== "INQUIRY_LINK") throw new InquiryAdapterError("ORIGIN_POLICY_VIOLATION", "inquiry origin/carrier changed");
  if (flow.historicalClaim !== false || flow.semanticRelation !== false || flow.evidenceBackedHistoricalFlow !== false) throw new InquiryAdapterError("CARRIER_SEPARATION", "inquiry carrier crossed historical boundary");
  if (!Array.isArray(tree.treeItems) || tree.treeItems.length < 1 || tree.treeItems.length > 7) throw new InquiryAdapterError("TREE_LIMIT", "tree item count invalid");
  const items = tree.treeItems.map((item) => exact(item, ITEM_REQUIRED, ["candidateSenseId"]));
  const ids = items.map((item) => String(item.itemId));
  if (new Set(ids).size !== ids.length) throw new InquiryAdapterError("DUPLICATE_ID", "duplicate tree item");
  const idSet = new Set(ids), childCounts = new Map<string, number>();
  const roots = items.filter((item) => item.parentItemId === null);
  for (const item of items) {
    if (typeof item.depth !== "number" || !Number.isInteger(item.depth) || item.depth < 0 || item.depth > 4) throw new InquiryAdapterError("TREE_LIMIT", "tree depth invalid");
    if (item.parentItemId !== null) {
      if (!idSet.has(String(item.parentItemId))) throw new InquiryAdapterError("DANGLING_REFERENCE", "dangling tree parent");
      const parent = String(item.parentItemId); childCounts.set(parent, (childCounts.get(parent) ?? 0) + 1);
    }
    strings(item.evidenceRefs); strings(item.gapRefs);
  }
  if (roots.length !== 1 || roots[0].itemKind !== "INQUIRY_OPERATION" || roots[0].itemId !== tree.rootInquiryId) throw new InquiryAdapterError("ROOT_INQUIRY_REQUIRED", "one root inquiry required");
  if ([...childCounts.values()].some((count) => count > 2)) throw new InquiryAdapterError("TREE_LIMIT", "sibling limit exceeded");
  return tree;
}

export async function validateResearchInquiryInstance(value: unknown): Promise<Record<string, unknown>> {
  contamination(value);
  const instance = exact(value, INSTANCE_KEYS);
  if (instance.historicalClaim !== false || instance.semanticRelation !== false || instance.publicExportable !== false || instance.activationState !== "RESEARCH_CANDIDATE_ONLY" || instance.researchPreviewOnly !== true) throw new InquiryAdapterError("STATUS_MUTATION", "instance crossed research boundary");
  for (const key of ["rootInquiry", "inclusionExplanation", "nonClaimExplanation", "evidenceSummary", "limitationStatement"]) if (typeof instance[key] !== "string" || CLAIM.test(instance[key] as string)) throw new InquiryAdapterError("HISTORICAL_CLAIM_REJECTED", "historical assertion emitted");
  if (!(instance.rootInquiry as string).endsWith("?")) throw new InquiryAdapterError("QUESTION_FORM_REQUIRED", "root question required");
  if (!Array.isArray(instance.semanticNodeRefs) || instance.semanticNodeRefs.length < 1 || instance.semanticNodeRefs.length > 2) throw new InquiryAdapterError("TREE_LIMIT", "semantic node count invalid");
  const nodes = instance.semanticNodeRefs.map((item) => exact(item, NODE_KEYS));
  const senses = nodes.map((node) => String(node.senseId));
  if (new Set(senses).size !== senses.length) throw new InquiryAdapterError("DUPLICATE_SEMANTIC_ID", "duplicate semantic node");
  for (const node of nodes) for (const key of ["lexicalAttestationIds", "grammarAttestationIds", "sourceIds"]) strings(node[key]);
  const tree = validateInquiryTree({ rootInquiryId: (instance.treeItems as Array<Record<string, unknown>>).find((item) => item.parentItemId === null)?.itemId, strategy: instance.treeStrategy, primaryInquiryFlow: instance.primaryInquiryFlow, treeItems: instance.treeItems });
  const flow = tree.primaryInquiryFlow as Record<string, unknown>;
  if (JSON.stringify(flow.candidateSenseIds) !== JSON.stringify(senses)) throw new InquiryAdapterError("DANGLING_REFERENCE", "flow/node binding mismatch");
  exact(instance.evidenceCoverage, ["lexicalAttestationCount", "grammarAttestationCount", "directAttestationCount"]);
  const sourceCoverage = exact(instance.sourceCoverage, ["distinctSourceCount", "sourceIds"]); strings(sourceCoverage.sourceIds);
  for (const key of ["qualificationRefs", "contestationRefs", "gapRefs"]) strings(instance[key]);
  const { canonicalHash, ...unsigned } = instance;
  if (await hashInquiryValue(unsigned) !== canonicalHash) throw new InquiryAdapterError("HASH_MISMATCH", "instance hash mismatch");
  return instance;
}

export async function validateConformanceArtifact(kind: string, value: unknown): Promise<Record<string, unknown>> {
  if (kind === "FREEZE") return validateCandidateFreeze(value);
  if (kind === "SEED") return validateInquirySeed(value);
  if (kind === "TREE") return validateInquiryTree(value);
  if (kind === "INSTANCE") return validateResearchInquiryInstance(value);
  throw new InquiryAdapterError("INVALID_KIND", "unknown fixture kind");
}
