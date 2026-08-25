/** Structural TypeScript verifier for Python-authored Round 13 inquiry Instance v2 artifacts. */

import { hashInquiryValue, InquiryAdapterError } from "./exploration-inquiry-adapter.ts";

export const ROUND13_TREE_STRATEGIES = [
  "LINEAR_PATH", "BINARY_FORK", "BINARY_CONVERGENCE", "QUALIFIED_PATH",
  "REFLEXIVE_RETURN", "EVIDENCE_GAP_TREE",
] as const;

const INSTANCE_KEYS = [
  "instanceId", "instanceVersion", "parentInstanceHash", "parentInstanceVersion", "freezePackageHash",
  "seedId", "seedHash", "treeStrategy", "treeStrategyVersion", "rootInquiry", "semanticNodeRefs",
  "primaryInquiryFlow", "treeItems", "evidenceCoverage", "sourceCoverage", "qualificationRefs",
  "contestationRefs", "gapRefs", "inclusionExplanation", "nonClaimExplanation", "evidenceSummary",
  "limitationStatement", "topologyChange", "historicalClaim", "semanticRelation", "publicExportable",
  "activationState", "researchPreviewOnly", "canonicalHash",
] as const;
const ITEM_REQUIRED = [
  "itemId", "itemKind", "parentItemId", "depth", "order", "label", "inquiryRole", "branchStatus",
  "evidenceRefs", "gapRefs", "convergenceSourceItemIds", "navigationTargetItemId",
] as const;
const ITEM_KINDS = new Set([
  "SEMANTIC_NODE_REFERENCE", "INQUIRY_OPERATION", "EVIDENCE_NOTE",
  "QUALIFICATION_NOTE", "CONTESTATION_NOTE", "EVIDENCE_GAP_NOTE",
]);
const V1_PRESERVED = [
  "instanceId", "freezePackageHash", "seedId", "seedHash", "treeStrategy", "rootInquiry",
  "semanticNodeRefs", "primaryInquiryFlow", "evidenceCoverage", "sourceCoverage", "qualificationRefs",
  "contestationRefs", "gapRefs", "inclusionExplanation", "nonClaimExplanation", "evidenceSummary",
  "limitationStatement", "historicalClaim", "semanticRelation", "publicExportable", "activationState",
  "researchPreviewOnly",
] as const;
const CLAIM = /\b(caused|led to|became|influenced)\b/i;
/* exploration-guard:allow-denial-start */
const PROHIBITED = new Set([
  "archiveobjectid", "objectid", "recordid", "surfaceid", "objecttitle", "recordurl", "objecthref",
  "contextdto", "contextpayload", "spacetimedto", "spacetimepayload", "modelid", "modelprovenance",
  "embeddingmodel", "vectorref", "vectorreference",
]);
/* exploration-guard:allow-denial-end */

function record(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new InquiryAdapterError("INVALID_TYPE", "object required");
  return value as Record<string, unknown>;
}

function exact(value: unknown, required: readonly string[], optional: readonly string[] = []): Record<string, unknown> {
  const item = record(value);
  const allowed = new Set([...required, ...optional]);
  if (Object.keys(item).some((key) => !allowed.has(key))) throw new InquiryAdapterError("UNKNOWN_FIELD", "unknown field");
  if (required.some((key) => !(key in item))) throw new InquiryAdapterError("MISSING_FIELD", "required field missing");
  return item;
}

function strings(value: unknown): string[] {
  if (!Array.isArray(value) || !value.every((item) => typeof item === "string" && item.trim())) throw new InquiryAdapterError("INVALID_TYPE", "string array required");
  if (new Set(value).size !== value.length) throw new InquiryAdapterError("DUPLICATE_ID", "duplicate array item");
  return value;
}

function contamination(value: unknown): void {
  if (Array.isArray(value)) return value.forEach(contamination);
  if (typeof value !== "object" || value === null) return;
  for (const [key, child] of Object.entries(value as Record<string, unknown>)) {
    if (PROHIBITED.has(key.replaceAll("_", "").replaceAll("-", "").toLowerCase())) throw new InquiryAdapterError("STRUCTURAL_CONTAMINATION", "prohibited input shape");
    contamination(child);
  }
}

export function validateRound13Tree(strategy: string, rawItems: unknown): Record<string, unknown>[] {
  if (!ROUND13_TREE_STRATEGIES.includes(strategy as (typeof ROUND13_TREE_STRATEGIES)[number])) throw new InquiryAdapterError("INVALID_ENUM", "unknown strategy");
  if (!Array.isArray(rawItems) || rawItems.length < 1 || rawItems.length > 7) throw new InquiryAdapterError("TREE_LIMIT", "tree item count invalid");
  const items = rawItems.map((item) => exact(item, ITEM_REQUIRED, ["candidateSenseId"]));
  const ids = items.map((item) => String(item.itemId));
  if (new Set(ids).size !== ids.length) throw new InquiryAdapterError("DUPLICATE_ID", "duplicate tree item");
  const byId = new Map(items.map((item, index) => [String(item.itemId), { item, index }]));
  const roots = items.filter((item) => item.parentItemId === null);
  const childCount = new Map<string, number>();
  let semanticCount = 0;
  for (const item of items) {
    if (!ITEM_KINDS.has(String(item.itemKind))) throw new InquiryAdapterError("UNKNOWN_TREE_ITEM_KIND", "unknown tree item kind");
    if (!Number.isInteger(item.depth) || Number(item.depth) < 0 || Number(item.depth) > 4) throw new InquiryAdapterError("TREE_LIMIT", "tree depth invalid");
    if (item.itemKind === "SEMANTIC_NODE_REFERENCE") semanticCount += 1;
    strings(item.evidenceRefs); strings(item.gapRefs); strings(item.convergenceSourceItemIds);
    if (item.parentItemId !== null) {
      const parent = byId.get(String(item.parentItemId));
      if (!parent || Number(parent.item.depth) + 1 !== Number(item.depth)) throw new InquiryAdapterError("DANGLING_REFERENCE", "invalid parent");
      childCount.set(String(item.parentItemId), (childCount.get(String(item.parentItemId)) ?? 0) + 1);
    }
    if (item.navigationTargetItemId !== null && !byId.has(String(item.navigationTargetItemId))) throw new InquiryAdapterError("DANGLING_REFERENCE", "invalid navigation target");
    for (const source of item.convergenceSourceItemIds as string[]) if (!byId.has(source)) throw new InquiryAdapterError("DANGLING_REFERENCE", "invalid convergence source");
  }
  if (roots.length !== 1 || roots[0].itemKind !== "INQUIRY_OPERATION" || roots[0].depth !== 0) throw new InquiryAdapterError("ROOT_INQUIRY_REQUIRED", "one root inquiry required");
  if (semanticCount > 2 || [...childCount.values()].some((count) => count > 2)) throw new InquiryAdapterError("TREE_LIMIT", "semantic node or sibling limit exceeded");
  const rootId = String(roots[0].itemId);
  const descendantsOf = (item: Record<string, unknown>, ancestorId: string): boolean => {
    let parent = item.parentItemId;
    while (parent !== null) {
      if (String(parent) === ancestorId) return true;
      parent = byId.get(String(parent))?.item.parentItemId ?? null;
    }
    return false;
  };
  const convergence = items.filter((item) => item.branchStatus === "CONVERGENCE");
  const returns = items.filter((item) => item.branchStatus === "RETURN" && item.navigationTargetItemId !== null);
  const gaps = items.filter((item) => item.itemKind === "EVIDENCE_GAP_NOTE");
  const gates = items.filter((item) => item.branchStatus === "GATE");
  const navigationItems = items.filter((item) => item.navigationTargetItemId !== null);
  if (navigationItems.some((item) => item.itemKind === "SEMANTIC_NODE_REFERENCE")) throw new InquiryAdapterError("SEMANTIC_NAVIGATION_FORBIDDEN", "semantic nodes cannot navigate");
  if (strategy !== "REFLEXIVE_RETURN" && navigationItems.length) throw new InquiryAdapterError("UNEXPECTED_NAVIGATION", "navigation is strategy-specific");
  if (strategy !== "BINARY_CONVERGENCE" && items.some((item) => (item.convergenceSourceItemIds as string[]).length)) throw new InquiryAdapterError("UNEXPECTED_CONVERGENCE_SOURCE", "convergence sources are strategy-specific");

  const one = (role: string): Record<string, unknown> => {
    const matches = items.filter((item) => item.inquiryRole === role);
    if (matches.length !== 1) throw new InquiryAdapterError(`${strategy}_ROLE_CARDINALITY`, role);
    return matches[0];
  };
  const roleContract = (expected: Record<string, string[]>): boolean => (
    items.length === Object.keys(expected).length
    && Object.entries(expected).every(([role, kinds]) => {
      const matches = items.filter((item) => item.inquiryRole === role);
      return matches.length === 1 && kinds.includes(String(matches[0].itemKind));
    })
  );

  if (strategy === "LINEAR_PATH") {
    const followRole = items.some((item) => item.inquiryRole === "FOLLOWING_CONCEPT_QUESTION") ? "FOLLOWING_CONCEPT_QUESTION" : "FOLLOWING_QUESTION";
    const expected = {
      ROOT_INQUIRY: ["INQUIRY_OPERATION"], STARTING_CONCEPT_QUESTION: ["SEMANTIC_NODE_REFERENCE"],
      EVIDENCE_CHECK: ["EVIDENCE_NOTE"], [followRole]: followRole === "FOLLOWING_CONCEPT_QUESTION" ? ["SEMANTIC_NODE_REFERENCE"] : ["INQUIRY_OPERATION"],
      SEQUENCE_BOUNDARY: ["QUALIFICATION_NOTE"],
    };
    if (!roleContract(expected) || one("STARTING_CONCEPT_QUESTION").parentItemId !== rootId || one("EVIDENCE_CHECK").parentItemId !== one("STARTING_CONCEPT_QUESTION").itemId || one(followRole).parentItemId !== one("EVIDENCE_CHECK").itemId || one("SEQUENCE_BOUNDARY").parentItemId !== one(followRole).itemId || [...childCount.values()].some((count) => count > 1)) throw new InquiryAdapterError("LINEAR_PATH_TOPOLOGY", "linear role-kind-parent contract invalid");
  } else if (strategy === "BINARY_FORK") {
    const rightRole = items.some((item) => item.inquiryRole === "BRANCH_B_CONCEPT") ? "BRANCH_B_CONCEPT" : "BRANCH_B_CONTESTATION";
    const expected = {
      ROOT_INQUIRY: ["INQUIRY_OPERATION"], ALTERNATIVE_BRANCH_A: ["INQUIRY_OPERATION"], ALTERNATIVE_BRANCH_B: ["INQUIRY_OPERATION"],
      BRANCH_A_CONCEPT: ["SEMANTIC_NODE_REFERENCE"], [rightRole]: rightRole === "BRANCH_B_CONCEPT" ? ["SEMANTIC_NODE_REFERENCE"] : ["CONTESTATION_NOTE"],
    };
    const left = one("ALTERNATIVE_BRANCH_A"); const right = one("ALTERNATIVE_BRANCH_B");
    if (!roleContract(expected) || left.parentItemId !== rootId || right.parentItemId !== rootId || left.branchStatus !== "ALTERNATIVE" || right.branchStatus !== "ALTERNATIVE" || one("BRANCH_A_CONCEPT").parentItemId !== left.itemId || one(rightRole).parentItemId !== right.itemId || convergence.length || returns.length) throw new InquiryAdapterError("BINARY_FORK_TOPOLOGY", "fork role-kind-parent contract invalid");
  } else if (strategy === "BINARY_CONVERGENCE") {
    const expected = {
      ROOT_INQUIRY: ["INQUIRY_OPERATION"], CONVERGENCE_BRANCH_A: ["INQUIRY_OPERATION"], CONVERGENCE_BRANCH_B: ["INQUIRY_OPERATION"],
      CONVERGENCE_INPUT_A: ["SEMANTIC_NODE_REFERENCE"], CONVERGENCE_INPUT_B: ["SEMANTIC_NODE_REFERENCE"], SHARED_REVIEW_PROBLEM: ["INQUIRY_OPERATION"],
    };
    const left = one("CONVERGENCE_BRANCH_A"); const right = one("CONVERGENCE_BRANCH_B");
    const inputA = one("CONVERGENCE_INPUT_A"); const inputB = one("CONVERGENCE_INPUT_B"); const shared = one("SHARED_REVIEW_PROBLEM");
    const sources = new Set(shared.convergenceSourceItemIds as string[]);
    if (!roleContract(expected) || left.parentItemId !== rootId || right.parentItemId !== rootId || left.branchStatus !== "CONVERGING" || right.branchStatus !== "CONVERGING" || inputA.parentItemId !== left.itemId || inputB.parentItemId !== right.itemId || shared.branchStatus !== "CONVERGENCE" || convergence.length !== 1 || sources.size !== 2 || !sources.has(String(inputA.itemId)) || !sources.has(String(inputB.itemId))) throw new InquiryAdapterError("BINARY_CONVERGENCE_TOPOLOGY", "convergence role-kind-parent contract invalid");
  } else if (strategy === "QUALIFIED_PATH") {
    const expected = {
      ROOT_INQUIRY: ["INQUIRY_OPERATION"], PRIMARY_CONCEPT_QUESTION: ["SEMANTIC_NODE_REFERENCE"], MANDATORY_QUALIFICATION_GATE: ["QUALIFICATION_NOTE"],
      QUALIFIED_CONTINUATION: ["SEMANTIC_NODE_REFERENCE", "INQUIRY_OPERATION"], QUALIFICATION_REVIEW: ["CONTESTATION_NOTE"],
    };
    const primary = one("PRIMARY_CONCEPT_QUESTION"); const gate = one("MANDATORY_QUALIFICATION_GATE"); const continuation = one("QUALIFIED_CONTINUATION"); const review = one("QUALIFICATION_REVIEW");
    if (!roleContract(expected) || primary.parentItemId !== rootId || gate.parentItemId !== primary.itemId || continuation.parentItemId !== gate.itemId || review.parentItemId !== continuation.itemId || !descendantsOf(continuation, String(gate.itemId)) || [...childCount.values()].some((count) => count > 1)) throw new InquiryAdapterError("QUALIFIED_PATH_TOPOLOGY", "qualification role-kind-parent contract invalid");
  } else if (strategy === "REFLEXIVE_RETURN") {
    const expected = {
      ROOT_INQUIRY: ["INQUIRY_OPERATION"], REFLEXIVE_CONCEPT_QUESTION: ["SEMANTIC_NODE_REFERENCE"], SELF_POSITIONING_QUESTION: ["INQUIRY_OPERATION"],
      NAVIGATION_RETURN: ["CONTESTATION_NOTE"], RETURN_BOUNDARY: ["QUALIFICATION_NOTE"],
    };
    const concept = one("REFLEXIVE_CONCEPT_QUESTION"); const self = one("SELF_POSITIONING_QUESTION"); const returnItem = one("NAVIGATION_RETURN"); const boundary = one("RETURN_BOUNDARY");
    if (!roleContract(expected) || concept.parentItemId !== rootId || self.parentItemId !== concept.itemId || returnItem.parentItemId !== self.itemId || boundary.parentItemId !== returnItem.itemId || returns.length !== 1 || navigationItems.length !== 1 || returnItem.navigationTargetItemId !== rootId || [...childCount.values()].some((count) => count > 1)) throw new InquiryAdapterError("REFLEXIVE_RETURN_TOPOLOGY", "reflexive role-kind-parent contract invalid");
  } else if (strategy === "EVIDENCE_GAP_TREE") {
    const expected = {
      ROOT_INQUIRY: ["INQUIRY_OPERATION"], SUPPORTED_BRANCH: ["INQUIRY_OPERATION"], UNRESOLVED_BRANCH: ["INQUIRY_OPERATION"],
      SUPPORTED_CONCEPT: ["SEMANTIC_NODE_REFERENCE"], SUPPORTED_EVIDENCE: ["EVIDENCE_NOTE"], FIRST_CLASS_EVIDENCE_GAP: ["EVIDENCE_GAP_NOTE"],
    };
    const supported = one("SUPPORTED_BRANCH"); const unresolved = one("UNRESOLVED_BRANCH"); const concept = one("SUPPORTED_CONCEPT"); const evidence = one("SUPPORTED_EVIDENCE"); const gap = one("FIRST_CLASS_EVIDENCE_GAP");
    if (!roleContract(expected) || supported.parentItemId !== rootId || unresolved.parentItemId !== rootId || supported.branchStatus !== "SUPPORTED" || unresolved.branchStatus !== "UNRESOLVED" || concept.parentItemId !== supported.itemId || evidence.parentItemId !== concept.itemId || gap.parentItemId !== unresolved.itemId || gap.branchStatus !== "UNRESOLVED" || (gap.gapRefs as string[]).length === 0 || gaps.length !== 1) throw new InquiryAdapterError("EVIDENCE_GAP_TREE_TOPOLOGY", "gap role-kind-parent contract invalid");
  }
  return items;
}

export function round13TopologySignature(items: Record<string, unknown>[]): string {
  const byId = new Map(items.map((item, index) => [String(item.itemId), index]));
  return items.map((item) => [
    item.itemKind,
    item.parentItemId === null ? "ROOT" : byId.get(String(item.parentItemId)),
    item.depth,
    item.branchStatus,
    (item.convergenceSourceItemIds as string[]).map((source) => byId.get(source)).join(","),
    item.navigationTargetItemId === null ? "" : byId.get(String(item.navigationTargetItemId)),
  ].join("|")).join(";");
}

export async function validateResearchInquiryInstanceV2(value: unknown, parentV1?: unknown): Promise<Record<string, unknown>> {
  contamination(value);
  const instance = exact(value, INSTANCE_KEYS);
  if (instance.instanceVersion !== "2" || instance.parentInstanceVersion !== "1" || instance.treeStrategyVersion !== "2") throw new InquiryAdapterError("V2_VERSION_FAILURE", "invalid v2 version");
  if (instance.historicalClaim !== false || instance.semanticRelation !== false || instance.publicExportable !== false || instance.activationState !== "RESEARCH_CANDIDATE_ONLY" || instance.researchPreviewOnly !== true) throw new InquiryAdapterError("STATUS_MUTATION", "research boundary crossed");
  if (typeof instance.rootInquiry !== "string" || !instance.rootInquiry.endsWith("?") || CLAIM.test(instance.rootInquiry)) throw new InquiryAdapterError("QUESTION_FORM_REQUIRED", "question required");
  const topologyChange = exact(instance.topologyChange, ["changed", "summary", "semanticContentUnchanged", "evidenceBindingChange"]);
  if (topologyChange.changed !== true || topologyChange.semanticContentUnchanged !== true || topologyChange.evidenceBindingChange !== "UNCHANGED") throw new InquiryAdapterError("TOPOLOGY_CHANGE_RECEIPT_FAILURE", "invalid topology receipt");
  const items = validateRound13Tree(String(instance.treeStrategy), instance.treeItems);
  if (!Array.isArray(instance.semanticNodeRefs) || instance.semanticNodeRefs.length < 1 || instance.semanticNodeRefs.length > 2) throw new InquiryAdapterError("TREE_LIMIT", "semantic node count invalid");
  const semanticSenses = (instance.semanticNodeRefs as Array<Record<string, unknown>>).map((node) => String(node.senseId)).sort();
  const treeSenses = items.filter((item) => item.itemKind === "SEMANTIC_NODE_REFERENCE").map((item) => String(item.candidateSenseId)).sort();
  if (JSON.stringify(semanticSenses) !== JSON.stringify(treeSenses)) throw new InquiryAdapterError("TREE_SEMANTIC_NODE_MISMATCH", "semantic nodes changed");
  for (const key of ["qualificationRefs", "contestationRefs", "gapRefs"]) strings(instance[key]);
  if (parentV1 !== undefined) {
    const parent = record(parentV1);
    if (instance.parentInstanceHash !== parent.canonicalHash) throw new InquiryAdapterError("PARENT_INSTANCE_HASH_MISMATCH", "parent hash mismatch");
    for (const key of V1_PRESERVED) if (JSON.stringify(instance[key]) !== JSON.stringify(parent[key])) throw new InquiryAdapterError("V1_V2_SEMANTIC_PRESERVATION_FAILURE", key);
    for (const bindingKey of ["evidenceRefs", "gapRefs"] as const) {
      const parentBindings = new Set((parent.treeItems as Array<Record<string, unknown>>).flatMap((item) => item[bindingKey] as string[] ?? []));
      const childBindings = new Set(items.flatMap((item) => item[bindingKey] as string[]));
      if (parentBindings.size !== childBindings.size || [...parentBindings].some((binding) => !childBindings.has(binding))) throw new InquiryAdapterError("TREE_BINDING_PRESERVATION_FAILURE", bindingKey);
    }
  }
  const { canonicalHash, ...unsigned } = instance;
  if (await hashInquiryValue(unsigned) !== canonicalHash) throw new InquiryAdapterError("HASH_MISMATCH", "v2 hash mismatch");
  return instance;
}
