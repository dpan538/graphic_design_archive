/** Atomic synthetic-only Image compilation over the fail-closed kernel. */

import {
  EXPLORATION_CONSTRAINT_COMPILER_VERSION,
  type BuildRejectedReceipt,
  type BuildSucceededReceipt,
  type CompiledExplorationImage,
  type ExplorationBuildReceipt,
  type ExplorationBuildRequest,
  type ExplorationConstraintPackage,
  type SyntheticExplorationContainer,
  type SyntheticExplorationInstance,
  deepFreezeConstraintValue,
  hashExplorationBuildRequest,
  sha256ConstraintValue,
} from "./exploration-build-contract.ts";
import { evaluateExplorationConstraints } from "./exploration-constraint-kernel.ts";

function layoutChoiceFromSeed(seed: string): string {
  let accumulator = 0;
  for (const character of seed) accumulator = (accumulator * 31 + character.charCodeAt(0)) >>> 0;
  return `AUTHORIZED-LAYOUT-CHOICE-${accumulator % 4}`;
}

export async function compileConstrainedExplorationImage(
  constraintPackage: ExplorationConstraintPackage,
  request: ExplorationBuildRequest,
): Promise<ExplorationBuildReceipt> {
  const requestHash = await hashExplorationBuildRequest(request);
  const evaluation = await evaluateExplorationConstraints(constraintPackage, request);
  if (!evaluation.authorized) {
    const receipt: BuildRejectedReceipt = {
      buildStatus: "REJECTED",
      failureCodes: evaluation.failureCodes,
      constraintPackageHash: constraintPackage.buildSha256,
      requestHash,
      compilerVersion: EXPLORATION_CONSTRAINT_COMPILER_VERSION,
    };
    return deepFreezeConstraintValue(receipt);
  }

  if (request.semanticMode !== "SYNTHETIC_TEST" || !request.syntheticTestOnly) {
    const receipt: BuildRejectedReceipt = {
      buildStatus: "REJECTED",
      failureCodes: ["SYNTHETIC_POLICY_LEAKAGE"],
      constraintPackageHash: constraintPackage.buildSha256,
      requestHash,
      compilerVersion: EXPLORATION_CONSTRAINT_COMPILER_VERSION,
    };
    return deepFreezeConstraintValue(receipt);
  }

  const unsigned = {
    imageVersion: request.imageVersion,
    compilerVersion: EXPLORATION_CONSTRAINT_COMPILER_VERSION,
    constraintPackageHash: constraintPackage.buildSha256,
    requestHash,
    seed: request.seed,
    syntheticTestOnly: true as const,
    immutable: true as const,
    authorizationReceipt: {
      nodeConceptIds: evaluation.plan.nodePolicies.map((policy) => policy.nodeConceptId),
      pairPolicyIds: evaluation.plan.pairPolicies.map((policy) => policy.pairPolicyId),
      clusterPolicyIds: [...evaluation.plan.clusterPolicyIds],
      chainPolicyIds: [...evaluation.plan.chainPolicyIds],
    },
    topology: {
      nodes: structuredClone(request.requestedNodes),
      flows: structuredClone(request.requestedFlows),
      clusters: structuredClone(request.requestedClusters),
      chains: structuredClone(request.requestedChains),
    },
    layoutChoice: layoutChoiceFromSeed(request.seed),
  };
  const imageHash = await sha256ConstraintValue(unsigned);
  const image: CompiledExplorationImage = {
    imageId: `IMAGE-${imageHash.slice(0, 24).toUpperCase()}`,
    ...unsigned,
    imageHash,
  };
  const frozenImage = deepFreezeConstraintValue(image);
  const receipt: BuildSucceededReceipt = {
    buildStatus: "COMPILED_SYNTHETIC_TEST_ONLY",
    imageId: image.imageId,
    imageVersion: image.imageVersion,
    compilerVersion: EXPLORATION_CONSTRAINT_COMPILER_VERSION,
    constraintPackageHash: constraintPackage.buildSha256,
    requestHash,
    imageHash,
    seed: request.seed,
    syntheticTestOnly: true,
    image: frozenImage,
  };
  return deepFreezeConstraintValue(receipt);
}

export async function verifyCompiledExplorationImageHash(
  image: CompiledExplorationImage,
): Promise<boolean> {
  const { imageId: _imageId, imageHash: _imageHash, ...unsigned } = image;
  return (await sha256ConstraintValue(unsigned)) === image.imageHash;
}

export async function instantiateSyntheticExplorationImage(
  image: CompiledExplorationImage,
  generationPolicyVersion: string,
): Promise<Readonly<SyntheticExplorationInstance>> {
  if (!image.syntheticTestOnly || !(await verifyCompiledExplorationImageHash(image))) {
    throw new Error("only a valid immutable synthetic Image may be instantiated");
  }
  const unsigned = {
    baseImageId: image.imageId,
    baseImageVersion: image.imageVersion,
    baseImageBuildSha256: image.imageHash,
    seed: image.seed,
    generationPolicyVersion,
    syntheticTestOnly: true as const,
  };
  const structuralReceiptSha256 = await sha256ConstraintValue(unsigned);
  return deepFreezeConstraintValue({
    instanceId: `INSTANCE-${structuralReceiptSha256.slice(0, 24).toUpperCase()}`,
    ...unsigned,
    structuralReceiptSha256,
  });
}

export function createSyntheticExplorationContainer(
  instance: SyntheticExplorationInstance,
  image: CompiledExplorationImage,
): SyntheticExplorationContainer {
  if (
    !instance.syntheticTestOnly ||
    !image.syntheticTestOnly ||
    instance.baseImageId !== image.imageId ||
    instance.baseImageVersion !== image.imageVersion ||
    instance.baseImageBuildSha256 !== image.imageHash
  ) {
    throw new Error("real semantic Container creation is prohibited");
  }
  return {
    containerId: `CONTAINER-${instance.instanceId.slice("INSTANCE-".length)}`,
    instanceId: instance.instanceId,
    imageHash: image.imageHash,
    activeNodeIds: image.topology.nodes.map((node) => node.nodeConceptId),
    activeFlowIds: image.topology.flows.map((flow) => flow.flowId),
    activeClusterIds: image.topology.clusters.map((cluster) => cluster.clusterId),
    positions: [],
    localEdits: [],
    expandedBranchIds: [],
    hiddenComponentIds: [],
    syntheticTestOnly: true,
  };
}

export function applySyntheticContainerEdit(
  container: SyntheticExplorationContainer,
  image: CompiledExplorationImage,
  edit: {
    editId: string;
    targetId: string;
    editKind: string;
    value: string | number | boolean;
  },
): void {
  if (
    !container.syntheticTestOnly ||
    !image.syntheticTestOnly ||
    container.imageHash !== image.imageHash
  ) {
    throw new Error("Container is not bound to this immutable synthetic Image");
  }
  const authorizedIds = new Set([
    ...image.topology.nodes.map((node) => node.nodeConceptId),
    ...image.topology.flows.map((flow) => flow.flowId),
    ...image.topology.clusters.map((cluster) => cluster.clusterId),
  ]);
  if (!authorizedIds.has(edit.targetId)) {
    throw new Error("Container edit cannot activate an unauthorized semantic ID");
  }
  container.localEdits.push(structuredClone(edit));
}
