/** Fail-closed semantic constraint evaluation for Exploration preprogramming. */

import {
  type BuildFailureCode,
  type DirectionalityCapability,
  type ExplorationBuildRequest,
  type ExplorationConstraintPackage,
  type NodePolicy,
  type PairPolicy,
  verifyExplorationConstraintPackageHash,
} from "./exploration-build-contract.ts";

export interface AuthorizedBuildPlan {
  nodePolicies: readonly NodePolicy[];
  pairPolicies: readonly PairPolicy[];
  clusterPolicyIds: readonly string[];
  chainPolicyIds: readonly string[];
}

export type ConstraintEvaluation =
  | { authorized: true; plan: AuthorizedBuildPlan }
  | { authorized: false; failureCodes: readonly BuildFailureCode[] };

const ALLOW_PAIR_DECISIONS = new Set([
  "ALLOW_EVIDENCE_BACKED_FLOW",
  "ALLOW_CONDITION",
  "ALLOW_CONTRAST",
  "ALLOW_QUALIFICATION",
]);

function hasUnboundedRole(value: string): boolean {
  const normalized = value.trim().toUpperCase();
  return normalized === "ANY" || normalized.includes("ANY-TO-ANY");
}

function directionIsCompatible(
  authorized: DirectionalityCapability,
  requested: DirectionalityCapability,
): boolean {
  if (authorized === "STRUCTURAL_NON_EDGE") return false;
  return authorized === requested;
}

function uniqueSorted(codes: Iterable<BuildFailureCode>): BuildFailureCode[] {
  return [...new Set(codes)].sort();
}

function sameMembers(left: readonly string[], right: readonly string[]): boolean {
  if (left.length !== right.length) return false;
  const normalizedLeft = [...left].sort();
  const normalizedRight = [...right].sort();
  return normalizedLeft.every((value, index) => value === normalizedRight[index]);
}

function contaminationFailures(
  request: ExplorationBuildRequest,
): BuildFailureCode[] {
  /* exploration-guard:allow-denial-start */
  const mapping = {
    ARCHIVE_OBJECT: "ARCHIVE_OBJECT_CONTAMINATION",
    CONTEXT_PAYLOAD: "CONTEXT_CONTAMINATION",
    SPACETIME_PAYLOAD: "SPACETIME_CONTAMINATION",
    EXTERNAL_MODEL_PROVENANCE: "EXTERNAL_MODEL_CONTAMINATION",
  } as const satisfies Record<
    ExplorationBuildRequest["forbiddenInputKinds"][number],
    BuildFailureCode
  >;
  /* exploration-guard:allow-denial-end */
  return request.forbiddenInputKinds.map((kind) => mapping[kind]);
}

export async function evaluateExplorationConstraints(
  constraintPackage: ExplorationConstraintPackage,
  request: ExplorationBuildRequest,
): Promise<ConstraintEvaluation> {
  const failures: BuildFailureCode[] = contaminationFailures(request);

  if (!(await verifyExplorationConstraintPackageHash(constraintPackage))) {
    failures.push("PACKAGE_HASH_MISMATCH");
  }
  if (!constraintPackage.provenanceRef) failures.push("PROVENANCE_MISSING");
  if (request.constraintPackageHash !== constraintPackage.buildSha256) {
    failures.push("PACKAGE_HASH_MISMATCH");
  }

  if (request.semanticMode === "REAL") {
    if (constraintPackage.activationState !== "GOVERNED_ACTIVE") {
      failures.push("NO_ACTIVE_VOCABULARY", "NO_ACTIVE_GRAMMAR");
    }
    if (constraintPackage.nodePolicies.length === 0) failures.push("NO_ACTIVE_VOCABULARY");
    if (
      constraintPackage.pairPolicies.filter((policy) =>
        ALLOW_PAIR_DECISIONS.has(policy.decision),
      ).length === 0
    ) {
      failures.push("NO_AUTHORIZED_PAIR_RULES");
    }
    if (constraintPackage.syntheticTestOnly) failures.push("SYNTHETIC_POLICY_LEAKAGE");
  } else if (!constraintPackage.syntheticTestOnly || !request.syntheticTestOnly) {
    failures.push("SYNTHETIC_FLAG_MISMATCH");
  }

  if (request.semanticMode === "REAL" && request.syntheticTestOnly) {
    failures.push("SYNTHETIC_FLAG_MISMATCH");
  }

  const nodePolicyById = new Map(
    constraintPackage.nodePolicies.map((policy) => [policy.nodeConceptId, policy]),
  );
  const requestedNodeIds = new Set(request.requestedNodes.map((node) => node.nodeConceptId));
  const activeQualificationKeys = new Set(
    constraintPackage.qualificationPolicies
      .filter((policy) => policy.activationState === "GOVERNED_ACTIVE")
      .map((policy) => policy.qualificationKey),
  );
  const authorizedNodePolicies: NodePolicy[] = [];

  for (const requestedNode of request.requestedNodes) {
    const policy = nodePolicyById.get(requestedNode.nodeConceptId);
    if (!policy) {
      failures.push("UNKNOWN_NODE");
      continue;
    }
    if (policy.activationState === "UNRESOLVED") failures.push("UNRESOLVED_NODE");
    if (policy.activationState === "RESEARCH_CANDIDATE_ONLY") {
      failures.push("RESEARCH_ONLY_NODE");
    }
    if (policy.senseId !== requestedNode.senseId) failures.push("SENSE_ID_MISMATCH");
    if (policy.semanticLabel !== requestedNode.semanticLabel) {
      failures.push("SEMANTIC_LABEL_MISMATCH");
    }
    if (policy.technicalRole !== requestedNode.technicalRole) failures.push("ROLE_MISMATCH");
    for (const required of policy.requiredContext) {
      if (!requestedNode.context[required]) failures.push("REQUIRED_CONTEXT_MISSING");
    }
    for (const required of policy.requiredQualification) {
      if (
        !requestedNode.qualifications[required] ||
        !activeQualificationKeys.has(required)
      ) {
        failures.push("REQUIRED_QUALIFICATION_MISSING");
      }
    }
    if (
      hasUnboundedRole(policy.subjectRole) ||
      hasUnboundedRole(policy.targetRole) ||
      policy.additionalPartyRoles.some(hasUnboundedRole)
    ) {
      failures.push("UNBOUNDED_ARGUMENT_ROLE");
    }
    if (policy.universalNodeAllowed !== false || policy.scopeIn.trim() === "") {
      failures.push("UNIVERSAL_NODE_PROHIBITED");
    }
    if (!policy.provenanceRef) failures.push("PROVENANCE_MISSING");
    authorizedNodePolicies.push(policy);
  }

  const pairPolicyById = new Map(
    constraintPackage.pairPolicies.map((policy) => [policy.pairPolicyId, policy]),
  );
  const authorizedPairPolicies: PairPolicy[] = [];

  for (const requestedFlow of request.requestedFlows) {
    const policy = pairPolicyById.get(requestedFlow.pairPolicyId);
    if (!policy) {
      failures.push("UNAUTHORIZED_PAIR");
      continue;
    }
    if (
      !requestedNodeIds.has(requestedFlow.sourceNodeConceptId) ||
      !requestedNodeIds.has(requestedFlow.targetNodeConceptId)
    ) {
      failures.push("UNKNOWN_NODE");
    }
    if (policy.decision === "DEFER") failures.push("DEFERRED_PAIR");
    if (policy.decision === "REJECT") failures.push("REJECTED_PAIR");
    if (policy.decision === "DEFAULT_DENY") failures.push("UNAUTHORIZED_PAIR");
    if (!ALLOW_PAIR_DECISIONS.has(policy.decision)) continue;
    if (policy.activationState !== "GOVERNED_ACTIVE") failures.push("UNAUTHORIZED_PAIR");
    if (
      policy.sourceNodeConceptId !== requestedFlow.sourceNodeConceptId ||
      policy.targetNodeConceptId !== requestedFlow.targetNodeConceptId
    ) {
      failures.push("DIRECTIONALITY_NOT_AUTHORIZED");
    }
    if (
      requestedFlow.sourceNodeConceptId === requestedFlow.targetNodeConceptId &&
      policy.directionality !== "REFLEXIVE"
    ) {
      failures.push("SELF_RELATION_NOT_AUTHORIZED");
    }
    if (!directionIsCompatible(policy.directionality, requestedFlow.directionality)) {
      failures.push("DIRECTIONALITY_NOT_AUTHORIZED");
    }
    if (
      policy.sourceRole !== requestedFlow.sourceRole ||
      policy.targetRole !== requestedFlow.targetRole
    ) {
      failures.push("ROLE_MISMATCH");
    }
    if (hasUnboundedRole(policy.sourceRole) || hasUnboundedRole(policy.targetRole)) {
      failures.push("UNBOUNDED_ARGUMENT_ROLE");
    }
    for (const required of policy.requiredQualification) {
      if (
        !requestedFlow.qualifications[required] ||
        !activeQualificationKeys.has(required)
      ) {
        failures.push("REQUIRED_QUALIFICATION_MISSING");
      }
    }
    if (!policy.provenanceRef || !requestedFlow.provenanceRef) {
      failures.push("PROVENANCE_MISSING");
    }
    authorizedPairPolicies.push(policy);
  }

  const flowIds = new Set(request.requestedFlows.map((flow) => flow.flowId));
  const requestedFlowById = new Map(
    request.requestedFlows.map((flow) => [flow.flowId, flow]),
  );
  const authorizedClusterPolicyIds: string[] = [];
  for (const requestedCluster of request.requestedClusters) {
    const policy = constraintPackage.clusterPolicies.find(
      (candidate) => candidate.clusterPolicyId === requestedCluster.clusterPolicyId,
    );
    if (
      !policy ||
      policy.activationState !== "GOVERNED_ACTIVE" ||
      !sameMembers(policy.nodeConceptIds, requestedCluster.nodeConceptIds) ||
      !sameMembers(
        policy.pairPolicyIds,
        requestedCluster.flowIds
          .map((flowId) => requestedFlowById.get(flowId)?.pairPolicyId)
          .filter((pairPolicyId): pairPolicyId is string => Boolean(pairPolicyId)),
      ) ||
      requestedCluster.flowIds.some((flowId) => !flowIds.has(flowId))
    ) {
      failures.push("UNAUTHORIZED_CLUSTER");
      continue;
    }
    if (!policy.provenanceRef) failures.push("PROVENANCE_MISSING");
    authorizedClusterPolicyIds.push(policy.clusterPolicyId);
  }

  const authorizedChainPolicyIds: string[] = [];
  for (const requestedChain of request.requestedChains) {
    const policy = constraintPackage.chainPolicies.find(
      (candidate) => candidate.chainPolicyId === requestedChain.chainPolicyId,
    );
    if (!policy || policy.activationState !== "GOVERNED_ACTIVE") {
      failures.push("UNAUTHORIZED_CHAIN", "TRANSITIVE_INFERENCE_PROHIBITED");
      continue;
    }
    if (
      policy.orderedNodeConceptIds.join("|") !==
        requestedChain.orderedNodeConceptIds.join("|") ||
      policy.orderedPairPolicyIds.join("|") !==
        requestedChain.orderedFlowIds
          .map((flowId) => requestedFlowById.get(flowId)?.pairPolicyId ?? "")
          .join("|") ||
      requestedChain.orderedFlowIds.some((flowId) => !flowIds.has(flowId))
    ) {
      failures.push("TRANSITIVE_INFERENCE_PROHIBITED");
      continue;
    }
    if (!policy.provenanceRef) failures.push("PROVENANCE_MISSING");
    authorizedChainPolicyIds.push(policy.chainPolicyId);
  }

  if (failures.length > 0) {
    return { authorized: false, failureCodes: uniqueSorted(failures) };
  }
  return {
    authorized: true,
    plan: {
      nodePolicies: authorizedNodePolicies,
      pairPolicies: authorizedPairPolicies,
      clusterPolicyIds: authorizedClusterPolicyIds,
      chainPolicyIds: authorizedChainPolicyIds,
    },
  };
}
