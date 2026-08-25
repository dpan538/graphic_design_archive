/** Runtime-only rejection for untrusted Round 11 constraint inputs. */

import type {
  BuildFailureCode,
  ExplorationBuildRequest,
  ExplorationConstraintPackage,
} from "./exploration-build-contract.ts";

const PACKAGE_KEYS = new Set([
  "packageId", "packageVersion", "activationState", "vocabularyVersion", "grammarVersion",
  "nodePolicies", "pairPolicies", "clusterPolicies", "chainPolicies", "qualificationPolicies",
  "provenanceRef", "syntheticTestOnly", "buildSha256",
]);
const NODE_KEYS = new Set([
  "nodeConceptId", "senseId", "semanticLabel", "activationState", "technicalRole", "arity",
  "subjectRole", "targetRole", "additionalPartyRoles", "requiredContext",
  "requiredQualification", "scopeIn", "scopeOut", "directionalityCapability",
  "universalNodeAllowed", "provenanceRef",
]);
const PAIR_KEYS = new Set([
  "pairPolicyId", "sourceNodeConceptId", "targetNodeConceptId", "activationState", "decision",
  "directionality", "sourceRole", "targetRole", "requiredQualification", "allowedOrigins",
  "provenanceRef",
]);
const CLUSTER_KEYS = new Set(["clusterPolicyId", "activationState", "nodeConceptIds", "pairPolicyIds", "provenanceRef"]);
const CHAIN_KEYS = new Set(["chainPolicyId", "activationState", "orderedNodeConceptIds", "orderedPairPolicyIds", "provenanceRef"]);
const QUALIFICATION_KEYS = new Set(["qualificationPolicyId", "activationState", "qualificationKey", "valueRequired", "provenanceRef"]);
const REQUEST_KEYS = new Set([
  "requestId", "imageVersion", "seed", "semanticMode", "syntheticTestOnly", "constraintPackageHash",
  "requestedNodes", "requestedFlows", "requestedClusters", "requestedChains", "forbiddenInputKinds",
]);
const REQUEST_NODE_KEYS = new Set(["nodeConceptId", "senseId", "semanticLabel", "technicalRole", "context", "qualifications"]);
const REQUEST_FLOW_KEYS = new Set([
  "flowId", "pairPolicyId", "sourceNodeConceptId", "targetNodeConceptId", "directionality",
  "sourceRole", "targetRole", "origin", "qualifications", "provenanceRef",
]);
const REQUEST_CLUSTER_KEYS = new Set(["clusterId", "clusterPolicyId", "nodeConceptIds", "flowIds"]);
const REQUEST_CHAIN_KEYS = new Set(["chainId", "chainPolicyId", "orderedNodeConceptIds", "orderedFlowIds"]);

/* exploration-guard:allow-denial-start */
const CONTAMINATION_KEYS: Readonly<Record<string, BuildFailureCode>> = {
  archiveobjectid: "ARCHIVE_OBJECT_CONTAMINATION",
  objectid: "ARCHIVE_OBJECT_CONTAMINATION",
  recordid: "ARCHIVE_OBJECT_CONTAMINATION",
  surfaceid: "ARCHIVE_OBJECT_CONTAMINATION",
  objecttitle: "ARCHIVE_OBJECT_CONTAMINATION",
  thumbnail: "ARCHIVE_OBJECT_CONTAMINATION",
  recordurl: "ARCHIVE_OBJECT_CONTAMINATION",
  objecthref: "ARCHIVE_OBJECT_CONTAMINATION",
  contextdto: "CONTEXT_CONTAMINATION",
  contextpayload: "CONTEXT_CONTAMINATION",
  spacetimedto: "SPACETIME_CONTAMINATION",
  spacetimepayload: "SPACETIME_CONTAMINATION",
  modelid: "EXTERNAL_MODEL_CONTAMINATION",
  modelprovenance: "EXTERNAL_MODEL_CONTAMINATION",
  embeddingmodel: "EXTERNAL_MODEL_CONTAMINATION",
  vectorref: "VECTOR_REFERENCE_CONTAMINATION",
  vectorreference: "VECTOR_REFERENCE_CONTAMINATION",
};
/* exploration-guard:allow-denial-end */

function normalizedKey(value: string): string {
  return value.replaceAll("_", "").replaceAll("-", "").toLowerCase();
}

export function detectExplorationStructuralContamination(value: unknown): BuildFailureCode[] {
  const failures = new Set<BuildFailureCode>();
  const visit = (current: unknown): void => {
    if (Array.isArray(current)) {
      current.forEach(visit);
      return;
    }
    if (typeof current !== "object" || current === null) return;
    const record = current as Record<string, unknown>;
    const keys = new Set(Object.keys(record).map(normalizedKey));
    for (const key of keys) {
      const failure = CONTAMINATION_KEYS[key];
      if (failure) failures.add(failure);
    }
    if ((keys.has("contextkind") && keys.has("termid")) || (keys.has("representations") && keys.has("contextkind"))) failures.add("CONTEXT_CONTAMINATION");
    if ((keys.has("periodid") && keys.has("geographyid")) || (keys.has("latitude") && keys.has("longitude") && keys.has("periodid"))) failures.add("SPACETIME_CONTAMINATION");
    Object.values(record).forEach(visit);
  };
  visit(value);
  return [...failures].sort();
}

function unknownFields(value: unknown, allowed: ReadonlySet<string>, failures: Set<BuildFailureCode>): void {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    failures.add("UNKNOWN_FIELD");
    return;
  }
  const keys = Object.keys(value);
  if (keys.some((key) => !allowed.has(key)) || [...allowed].some((key) => !keys.includes(key))) failures.add("UNKNOWN_FIELD");
}

function duplicates(values: readonly string[], code: BuildFailureCode, failures: Set<BuildFailureCode>): void {
  if (values.length !== new Set(values).size) failures.add(code);
}

function nonempty(value: unknown, failures: Set<BuildFailureCode>): void {
  if (typeof value !== "string" || value.trim() === "") failures.add("EMPTY_VALUE");
}

export function validateExplorationRuntimeInputs(
  constraintPackage: ExplorationConstraintPackage,
  request: ExplorationBuildRequest,
): BuildFailureCode[] {
  const failures = new Set<BuildFailureCode>([
    ...detectExplorationStructuralContamination(constraintPackage),
    ...detectExplorationStructuralContamination(request),
  ]);
  unknownFields(constraintPackage, PACKAGE_KEYS, failures);
  unknownFields(request, REQUEST_KEYS, failures);
  constraintPackage.nodePolicies.forEach((item) => unknownFields(item, NODE_KEYS, failures));
  constraintPackage.pairPolicies.forEach((item) => unknownFields(item, PAIR_KEYS, failures));
  constraintPackage.clusterPolicies.forEach((item) => unknownFields(item, CLUSTER_KEYS, failures));
  constraintPackage.chainPolicies.forEach((item) => unknownFields(item, CHAIN_KEYS, failures));
  constraintPackage.qualificationPolicies.forEach((item) => unknownFields(item, QUALIFICATION_KEYS, failures));
  request.requestedNodes.forEach((item) => unknownFields(item, REQUEST_NODE_KEYS, failures));
  request.requestedFlows.forEach((item) => unknownFields(item, REQUEST_FLOW_KEYS, failures));
  request.requestedClusters.forEach((item) => unknownFields(item, REQUEST_CLUSTER_KEYS, failures));
  request.requestedChains.forEach((item) => unknownFields(item, REQUEST_CHAIN_KEYS, failures));

  duplicates(constraintPackage.nodePolicies.map((item) => item.nodeConceptId), "DUPLICATE_SEMANTIC_ID", failures);
  duplicates(constraintPackage.nodePolicies.map((item) => item.senseId), "DUPLICATE_SEMANTIC_ID", failures);
  duplicates(constraintPackage.pairPolicies.map((item) => item.pairPolicyId), "DUPLICATE_ID", failures);
  duplicates(constraintPackage.clusterPolicies.map((item) => item.clusterPolicyId), "DUPLICATE_ID", failures);
  duplicates(constraintPackage.chainPolicies.map((item) => item.chainPolicyId), "DUPLICATE_ID", failures);
  duplicates(constraintPackage.qualificationPolicies.map((item) => item.qualificationPolicyId), "DUPLICATE_ID", failures);
  duplicates(constraintPackage.qualificationPolicies.map((item) => item.qualificationKey), "DUPLICATE_QUALIFICATION_KEY", failures);
  duplicates(request.requestedNodes.map((item) => item.nodeConceptId), "DUPLICATE_SEMANTIC_ID", failures);
  duplicates(request.requestedFlows.map((item) => item.flowId), "DUPLICATE_ID", failures);
  duplicates(request.requestedClusters.map((item) => item.clusterId), "DUPLICATE_ID", failures);
  duplicates(request.requestedChains.map((item) => item.chainId), "DUPLICATE_ID", failures);

  const nodeIds = new Set(constraintPackage.nodePolicies.map((item) => item.nodeConceptId));
  const pairIds = new Set(constraintPackage.pairPolicies.map((item) => item.pairPolicyId));
  for (const node of constraintPackage.nodePolicies) {
    [node.nodeConceptId, node.senseId, node.semanticLabel, node.subjectRole, node.targetRole, node.scopeIn, node.scopeOut, node.provenanceRef].forEach((value) => nonempty(value, failures));
    if (!Number.isInteger(node.arity) || node.arity < 1) failures.add("INVALID_ARITY");
    if (node.arity !== 2 + node.additionalPartyRoles.length) failures.add("PARTY_ROLE_COUNT_MISMATCH");
  }
  for (const pair of constraintPackage.pairPolicies) {
    [pair.pairPolicyId, pair.sourceRole, pair.targetRole, pair.provenanceRef].forEach((value) => nonempty(value, failures));
    if (!nodeIds.has(pair.sourceNodeConceptId) || !nodeIds.has(pair.targetNodeConceptId)) failures.add("DANGLING_REFERENCE");
    if (!Array.isArray(pair.allowedOrigins) || pair.allowedOrigins.length === 0) failures.add("ORIGIN_POLICY_VIOLATION");
  }
  for (const cluster of constraintPackage.clusterPolicies) {
    if (cluster.nodeConceptIds.some((id) => !nodeIds.has(id)) || cluster.pairPolicyIds.some((id) => !pairIds.has(id))) failures.add("DANGLING_REFERENCE");
  }
  for (const chain of constraintPackage.chainPolicies) {
    if (chain.orderedNodeConceptIds.some((id) => !nodeIds.has(id)) || chain.orderedPairPolicyIds.some((id) => !pairIds.has(id))) failures.add("DANGLING_REFERENCE");
  }

  const requestedNodeIds = new Set(request.requestedNodes.map((item) => item.nodeConceptId));
  const requestedFlowIds = new Set(request.requestedFlows.map((item) => item.flowId));
  for (const node of request.requestedNodes) [node.nodeConceptId, node.senseId, node.semanticLabel].forEach((value) => nonempty(value, failures));
  for (const flow of request.requestedFlows) {
    [flow.flowId, flow.pairPolicyId, flow.sourceRole, flow.targetRole, flow.provenanceRef].forEach((value) => nonempty(value, failures));
    if (!requestedNodeIds.has(flow.sourceNodeConceptId) || !requestedNodeIds.has(flow.targetNodeConceptId)) failures.add("DANGLING_REFERENCE");
    const policy = constraintPackage.pairPolicies.find((item) => item.pairPolicyId === flow.pairPolicyId);
    if (policy && !policy.allowedOrigins.includes(flow.origin)) failures.add("ORIGIN_POLICY_VIOLATION");
  }
  for (const cluster of request.requestedClusters) {
    if (cluster.nodeConceptIds.some((id) => !requestedNodeIds.has(id)) || cluster.flowIds.some((id) => !requestedFlowIds.has(id))) failures.add("DANGLING_REFERENCE");
  }
  for (const chain of request.requestedChains) {
    if (chain.orderedNodeConceptIds.some((id) => !requestedNodeIds.has(id)) || chain.orderedFlowIds.some((id) => !requestedFlowIds.has(id))) failures.add("DANGLING_REFERENCE");
  }
  if (constraintPackage.activationState === "UNRESOLVED" && [
    ...constraintPackage.nodePolicies, ...constraintPackage.pairPolicies,
    ...constraintPackage.clusterPolicies, ...constraintPackage.chainPolicies,
    ...constraintPackage.qualificationPolicies,
  ].some((item) => item.activationState === "GOVERNED_ACTIVE")) failures.add("INCONSISTENT_ACTIVATION_STATE");
  return [...failures].sort();
}
