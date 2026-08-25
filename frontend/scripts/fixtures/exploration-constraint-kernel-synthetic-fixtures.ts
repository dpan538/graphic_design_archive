/** Test-only positive fixtures. Production modules must never import this file. */

import {
  UNRESOLVED_ACTIVE_GRAMMAR_VERSION,
  UNRESOLVED_ACTIVE_VOCABULARY_VERSION,
  createExplorationConstraintPackage,
  type ConstraintPackageInput,
  type ExplorationBuildRequest,
} from "../../src/lib/trace/exploration-build-contract.ts";

export const SYNTHETIC_TEST_ONLY = true as const;

export const syntheticConstraintInput: ConstraintPackageInput = {
  packageId: "CONSTRAINT-PACKAGE-TEST-V1",
  packageVersion: "GRAMMAR-TEST-V1",
  activationState: "GOVERNED_ACTIVE",
  vocabularyVersion: "VOCABULARY-TEST-V1",
  grammarVersion: "GRAMMAR-TEST-V1",
  nodePolicies: [
    {
      nodeConceptId: "NODE-TEST-A",
      senseId: "SENSE-TEST-A",
      semanticLabel: "Synthetic concept alpha",
      activationState: "GOVERNED_ACTIVE",
      technicalRole: "SYNTHETIC_TEST_ROLE",
      arity: 2,
      subjectRole: "bounded synthetic source role",
      targetRole: "bounded synthetic target role",
      additionalPartyRoles: [],
      requiredContext: ["scope"],
      requiredQualification: [],
      scopeIn: "synthetic compiler validation only",
      scopeOut: "all real semantic use",
      directionalityCapability: "DIRECTED",
      universalNodeAllowed: false,
      provenanceRef: "PROVENANCE-TEST-A",
    },
    {
      nodeConceptId: "NODE-TEST-B",
      senseId: "SENSE-TEST-B",
      semanticLabel: "Synthetic concept beta",
      activationState: "GOVERNED_ACTIVE",
      technicalRole: "SYNTHETIC_TEST_ROLE",
      arity: 2,
      subjectRole: "bounded synthetic participant role",
      targetRole: "bounded synthetic counterpart role",
      additionalPartyRoles: [],
      requiredContext: ["scope"],
      requiredQualification: [],
      scopeIn: "synthetic compiler validation only",
      scopeOut: "all real semantic use",
      directionalityCapability: "RECIPROCAL",
      universalNodeAllowed: false,
      provenanceRef: "PROVENANCE-TEST-B",
    },
    {
      nodeConceptId: "NODE-TEST-C",
      senseId: "SENSE-TEST-C",
      semanticLabel: "Synthetic concept gamma",
      activationState: "GOVERNED_ACTIVE",
      technicalRole: "SYNTHETIC_TEST_ROLE",
      arity: 2,
      subjectRole: "bounded qualified synthetic source role",
      targetRole: "bounded qualified synthetic target role",
      additionalPartyRoles: [],
      requiredContext: ["scope"],
      requiredQualification: ["jurisdiction"],
      scopeIn: "synthetic compiler validation only",
      scopeOut: "all real semantic use",
      directionalityCapability: "DIRECTED",
      universalNodeAllowed: false,
      provenanceRef: "PROVENANCE-TEST-C",
    },
  ],
  pairPolicies: [
    {
      pairPolicyId: "PAIR-POLICY-TEST-A",
      sourceNodeConceptId: "NODE-TEST-A",
      targetNodeConceptId: "NODE-TEST-B",
      activationState: "GOVERNED_ACTIVE",
      decision: "ALLOW_EVIDENCE_BACKED_FLOW",
      directionality: "DIRECTED",
      sourceRole: "bounded synthetic source role",
      targetRole: "bounded synthetic counterpart role",
      requiredQualification: [],
      allowedOrigins: ["EVIDENCE_BACKED"],
      provenanceRef: "PROVENANCE-PAIR-TEST-A",
    },
    {
      pairPolicyId: "PAIR-POLICY-TEST-B",
      sourceNodeConceptId: "NODE-TEST-B",
      targetNodeConceptId: "NODE-TEST-C",
      activationState: "GOVERNED_ACTIVE",
      decision: "ALLOW_EVIDENCE_BACKED_FLOW",
      directionality: "RECIPROCAL",
      sourceRole: "bounded synthetic participant role",
      targetRole: "bounded qualified synthetic target role",
      requiredQualification: [],
      allowedOrigins: ["EVIDENCE_BACKED"],
      provenanceRef: "PROVENANCE-PAIR-TEST-B",
    },
    {
      pairPolicyId: "PAIR-POLICY-TEST-C",
      sourceNodeConceptId: "NODE-TEST-A",
      targetNodeConceptId: "NODE-TEST-C",
      activationState: "GOVERNED_ACTIVE",
      decision: "ALLOW_QUALIFICATION",
      directionality: "DIRECTED",
      sourceRole: "bounded synthetic source role",
      targetRole: "bounded qualified synthetic target role",
      requiredQualification: ["jurisdiction"],
      allowedOrigins: ["EVIDENCE_BACKED"],
      provenanceRef: "PROVENANCE-PAIR-TEST-C",
    },
    {
      pairPolicyId: "PAIR-POLICY-TEST-DEFER",
      sourceNodeConceptId: "NODE-TEST-A",
      targetNodeConceptId: "NODE-TEST-C",
      activationState: "RESEARCH_CANDIDATE_ONLY",
      decision: "DEFER",
      directionality: "DIRECTED",
      sourceRole: "bounded synthetic source role",
      targetRole: "bounded qualified synthetic target role",
      requiredQualification: [],
      allowedOrigins: ["RESEARCH_INQUIRY"],
      provenanceRef: "PROVENANCE-PAIR-TEST-DEFER",
    },
    {
      pairPolicyId: "PAIR-POLICY-TEST-REJECT",
      sourceNodeConceptId: "NODE-TEST-C",
      targetNodeConceptId: "NODE-TEST-A",
      activationState: "UNRESOLVED",
      decision: "REJECT",
      directionality: "DIRECTED",
      sourceRole: "bounded qualified synthetic source role",
      targetRole: "bounded synthetic target role",
      requiredQualification: [],
      allowedOrigins: ["EVIDENCE_BACKED"],
      provenanceRef: "PROVENANCE-PAIR-TEST-REJECT",
    },
    {
      pairPolicyId: "PAIR-POLICY-TEST-STRUCTURAL",
      sourceNodeConceptId: "NODE-TEST-B",
      targetNodeConceptId: "NODE-TEST-A",
      activationState: "GOVERNED_ACTIVE",
      decision: "ALLOW_CONDITION",
      directionality: "STRUCTURAL_NON_EDGE",
      sourceRole: "bounded synthetic participant role",
      targetRole: "bounded synthetic target role",
      requiredQualification: [],
      allowedOrigins: ["EVIDENCE_BACKED"],
      provenanceRef: "PROVENANCE-PAIR-TEST-STRUCTURAL",
    },
  ],
  clusterPolicies: [
    {
      clusterPolicyId: "CLUSTER-POLICY-TEST-A",
      activationState: "GOVERNED_ACTIVE",
      nodeConceptIds: ["NODE-TEST-A", "NODE-TEST-B", "NODE-TEST-C"],
      pairPolicyIds: [
        "PAIR-POLICY-TEST-A",
        "PAIR-POLICY-TEST-B",
        "PAIR-POLICY-TEST-C",
      ],
      provenanceRef: "PROVENANCE-CLUSTER-TEST-A",
    },
  ],
  chainPolicies: [
    {
      chainPolicyId: "CHAIN-POLICY-TEST-A",
      activationState: "GOVERNED_ACTIVE",
      orderedNodeConceptIds: ["NODE-TEST-A", "NODE-TEST-B", "NODE-TEST-C"],
      orderedPairPolicyIds: ["PAIR-POLICY-TEST-A", "PAIR-POLICY-TEST-B"],
      provenanceRef: "PROVENANCE-CHAIN-TEST-A",
    },
  ],
  qualificationPolicies: [
    {
      qualificationPolicyId: "QUALIFICATION-POLICY-TEST-A",
      activationState: "GOVERNED_ACTIVE",
      qualificationKey: "jurisdiction",
      valueRequired: true,
      provenanceRef: "PROVENANCE-QUALIFICATION-TEST-A",
    },
  ],
  provenanceRef: "PROVENANCE-CONSTRAINT-PACKAGE-TEST-V1",
  syntheticTestOnly: true,
};

export const unresolvedRealConstraintInput: ConstraintPackageInput = {
  packageId: "CONSTRAINT-PACKAGE-UNRESOLVED",
  packageVersion: "UNRESOLVED-PREPROGRAM-V1",
  activationState: "UNRESOLVED",
  vocabularyVersion: UNRESOLVED_ACTIVE_VOCABULARY_VERSION,
  grammarVersion: UNRESOLVED_ACTIVE_GRAMMAR_VERSION,
  nodePolicies: [],
  pairPolicies: [],
  clusterPolicies: [],
  chainPolicies: [],
  qualificationPolicies: [],
  provenanceRef: "PROVENANCE-ROUND10-NEGATIVE-CONSTRAINT-RECONCILIATION",
  syntheticTestOnly: false,
};

export async function createSyntheticFixturePackage() {
  return createExplorationConstraintPackage(syntheticConstraintInput);
}

export async function createUnresolvedRealFixturePackage() {
  return createExplorationConstraintPackage(unresolvedRealConstraintInput);
}

export function createSyntheticBuildRequest(
  constraintPackageHash: string,
): ExplorationBuildRequest {
  return {
    requestId: "BUILD-REQUEST-TEST-A",
    imageVersion: "IMAGE-TEST-V1",
    seed: "SEED-TEST-A",
    semanticMode: "SYNTHETIC_TEST",
    syntheticTestOnly: true,
    constraintPackageHash,
    requestedNodes: syntheticConstraintInput.nodePolicies.map(
      ({ nodeConceptId, senseId, semanticLabel, technicalRole, requiredQualification }) => ({
        nodeConceptId,
        senseId,
        semanticLabel,
        technicalRole,
        context: { scope: "synthetic compiler validation only" },
        qualifications: Object.fromEntries(
          requiredQualification.map((key) => [key, "TEST-JURISDICTION"]),
        ),
      }),
    ),
    requestedFlows: [
      {
        flowId: "FLOW-TEST-A",
        pairPolicyId: "PAIR-POLICY-TEST-A",
        sourceNodeConceptId: "NODE-TEST-A",
        targetNodeConceptId: "NODE-TEST-B",
        directionality: "DIRECTED",
        sourceRole: "bounded synthetic source role",
        targetRole: "bounded synthetic counterpart role",
        origin: "EVIDENCE_BACKED",
        qualifications: {},
        provenanceRef: "PROVENANCE-FLOW-TEST-A",
      },
      {
        flowId: "FLOW-TEST-B",
        pairPolicyId: "PAIR-POLICY-TEST-B",
        sourceNodeConceptId: "NODE-TEST-B",
        targetNodeConceptId: "NODE-TEST-C",
        directionality: "RECIPROCAL",
        sourceRole: "bounded synthetic participant role",
        targetRole: "bounded qualified synthetic target role",
        origin: "EVIDENCE_BACKED",
        qualifications: {},
        provenanceRef: "PROVENANCE-FLOW-TEST-B",
      },
      {
        flowId: "FLOW-TEST-C",
        pairPolicyId: "PAIR-POLICY-TEST-C",
        sourceNodeConceptId: "NODE-TEST-A",
        targetNodeConceptId: "NODE-TEST-C",
        directionality: "DIRECTED",
        sourceRole: "bounded synthetic source role",
        targetRole: "bounded qualified synthetic target role",
        origin: "EVIDENCE_BACKED",
        qualifications: { jurisdiction: "TEST-JURISDICTION" },
        provenanceRef: "PROVENANCE-FLOW-TEST-C",
      },
    ],
    requestedClusters: [
      {
        clusterId: "CLUSTER-TEST-A",
        clusterPolicyId: "CLUSTER-POLICY-TEST-A",
        nodeConceptIds: ["NODE-TEST-A", "NODE-TEST-B", "NODE-TEST-C"],
        flowIds: ["FLOW-TEST-A", "FLOW-TEST-B", "FLOW-TEST-C"],
      },
    ],
    requestedChains: [
      {
        chainId: "CHAIN-TEST-A",
        chainPolicyId: "CHAIN-POLICY-TEST-A",
        orderedNodeConceptIds: ["NODE-TEST-A", "NODE-TEST-B", "NODE-TEST-C"],
        orderedFlowIds: ["FLOW-TEST-A", "FLOW-TEST-B"],
      },
    ],
    forbiddenInputKinds: [],
  };
}

export function createCurrentRealBuildRequest(
  constraintPackageHash: string,
): ExplorationBuildRequest {
  return {
    requestId: "BUILD-REQUEST-CURRENT-REAL-STATE",
    imageVersion: "REAL-IMAGE-PROHIBITED",
    seed: "SEED-REAL-BUILD-REJECTION",
    semanticMode: "REAL",
    syntheticTestOnly: false,
    constraintPackageHash,
    requestedNodes: [],
    requestedFlows: [],
    requestedClusters: [],
    requestedChains: [],
    forbiddenInputKinds: [],
  };
}
