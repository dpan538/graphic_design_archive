/**
 * Renderer-neutral, fail-closed contracts for Exploration preprogramming.
 *
 * This module defines generic semantic authorization structures only. It does
 * not contain active vocabulary, active grammar, renderer concerns, research
 * labels, or project-record fields.
 */

export const EXPLORATION_CONSTRAINT_COMPILER_VERSION =
  "trace-exploration-constraint-compiler-preprogram-v1" as const;
export const UNRESOLVED_ACTIVE_VOCABULARY_VERSION =
  "UNRESOLVED_RELATION_VOCABULARY_VERSION" as const;
export const UNRESOLVED_ACTIVE_GRAMMAR_VERSION =
  "UNRESOLVED_RELATION_GRAMMAR_VERSION" as const;

export type SemanticActivationState =
  | "UNRESOLVED"
  | "RESEARCH_CANDIDATE_ONLY"
  | "GOVERNED_ACTIVE";

export type TechnicalRole =
  | "DIRECTED_PROCESS"
  | "DIRECTED_STATE_TRANSITION"
  | "HISTORIOGRAPHIC_POSITIONING"
  | "STRUCTURAL_CONDITION"
  | "REFLEXIVE_PROCESS"
  | "MULTIPARTY_ENCOUNTER"
  | "NORMATIVELY_QUALIFIED_RELATION"
  | "BOUNDED_INTERMEDIARY_PROCESS"
  | "SYNTHETIC_TEST_ROLE";

export type DirectionalityCapability =
  | "DIRECTED"
  | "RECIPROCAL"
  | "REFLEXIVE"
  | "MULTIPARTY"
  | "STRUCTURAL_NON_EDGE";

export type PairPolicyDecision =
  | "ALLOW_EVIDENCE_BACKED_FLOW"
  | "ALLOW_CONDITION"
  | "ALLOW_CONTRAST"
  | "ALLOW_QUALIFICATION"
  | "DEFER"
  | "REJECT"
  | "DEFAULT_DENY";

export interface NodePolicy {
  nodeConceptId: string;
  senseId: string;
  semanticLabel: string;
  activationState: SemanticActivationState;
  technicalRole: TechnicalRole;
  arity: number;
  subjectRole: string;
  targetRole: string;
  additionalPartyRoles: readonly string[];
  requiredContext: readonly string[];
  requiredQualification: readonly string[];
  scopeIn: string;
  scopeOut: string;
  directionalityCapability: DirectionalityCapability;
  universalNodeAllowed: false;
  provenanceRef: string;
}

export interface PairPolicy {
  pairPolicyId: string;
  sourceNodeConceptId: string;
  targetNodeConceptId: string;
  activationState: SemanticActivationState;
  decision: PairPolicyDecision;
  directionality: DirectionalityCapability;
  sourceRole: string;
  targetRole: string;
  requiredQualification: readonly string[];
  allowedOrigins: readonly FlowOrigin[];
  provenanceRef: string;
}

export type FlowOrigin =
  | "EVIDENCE_BACKED"
  | "GENERATIVE_COMPOSITION"
  | "USER_COMPOSED"
  | "RESEARCH_INQUIRY";

export interface ClusterPolicy {
  clusterPolicyId: string;
  activationState: SemanticActivationState;
  nodeConceptIds: readonly string[];
  pairPolicyIds: readonly string[];
  provenanceRef: string;
}

export interface ChainPolicy {
  chainPolicyId: string;
  activationState: SemanticActivationState;
  orderedNodeConceptIds: readonly string[];
  orderedPairPolicyIds: readonly string[];
  provenanceRef: string;
}

export interface QualificationPolicy {
  qualificationPolicyId: string;
  activationState: SemanticActivationState;
  qualificationKey: string;
  valueRequired: true;
  provenanceRef: string;
}

export interface ExplorationConstraintPackage {
  packageId: string;
  packageVersion: string;
  activationState: SemanticActivationState;
  vocabularyVersion: string;
  grammarVersion: string;
  nodePolicies: readonly NodePolicy[];
  pairPolicies: readonly PairPolicy[];
  clusterPolicies: readonly ClusterPolicy[];
  chainPolicies: readonly ChainPolicy[];
  qualificationPolicies: readonly QualificationPolicy[];
  provenanceRef: string;
  syntheticTestOnly: boolean;
  buildSha256: string;
}

export type ConstraintPackageInput = Omit<
  ExplorationConstraintPackage,
  "buildSha256"
>;

/* exploration-guard:allow-denial-start */
export type ForbiddenInputKind =
  | "ARCHIVE_OBJECT"
  | "CONTEXT_PAYLOAD"
  | "SPACETIME_PAYLOAD"
  | "EXTERNAL_MODEL_PROVENANCE";

export type BuildFailureCode =
  | "NO_ACTIVE_VOCABULARY"
  | "NO_ACTIVE_GRAMMAR"
  | "NO_AUTHORIZED_PAIR_RULES"
  | "UNRESOLVED_NODE"
  | "RESEARCH_ONLY_NODE"
  | "UNKNOWN_NODE"
  | "UNAUTHORIZED_PAIR"
  | "DEFERRED_PAIR"
  | "REJECTED_PAIR"
  | "DIRECTIONALITY_NOT_AUTHORIZED"
  | "SELF_RELATION_NOT_AUTHORIZED"
  | "UNBOUNDED_ARGUMENT_ROLE"
  | "ROLE_MISMATCH"
  | "SENSE_ID_MISMATCH"
  | "SEMANTIC_LABEL_MISMATCH"
  | "UNIVERSAL_NODE_PROHIBITED"
  | "REQUIRED_CONTEXT_MISSING"
  | "REQUIRED_QUALIFICATION_MISSING"
  | "UNAUTHORIZED_CLUSTER"
  | "UNAUTHORIZED_CHAIN"
  | "TRANSITIVE_INFERENCE_PROHIBITED"
  | "ARCHIVE_OBJECT_CONTAMINATION"
  | "CONTEXT_CONTAMINATION"
  | "SPACETIME_CONTAMINATION"
  | "EXTERNAL_MODEL_CONTAMINATION"
  | "PACKAGE_HASH_MISMATCH"
  | "PROVENANCE_MISSING"
  | "NONDETERMINISTIC_BUILD"
  | "SYNTHETIC_POLICY_LEAKAGE"
  | "SYNTHETIC_FLAG_MISMATCH"
  | "UNKNOWN_FIELD"
  | "DUPLICATE_ID"
  | "DUPLICATE_SEMANTIC_ID"
  | "DUPLICATE_QUALIFICATION_KEY"
  | "DANGLING_REFERENCE"
  | "INCONSISTENT_ACTIVATION_STATE"
  | "EMPTY_VALUE"
  | "INVALID_ARITY"
  | "PARTY_ROLE_COUNT_MISMATCH"
  | "ORIGIN_POLICY_VIOLATION"
  | "VECTOR_REFERENCE_CONTAMINATION";
/* exploration-guard:allow-denial-end */

export interface RequestedNode {
  nodeConceptId: string;
  senseId: string;
  semanticLabel: string;
  technicalRole: TechnicalRole;
  context: Readonly<Record<string, string>>;
  qualifications: Readonly<Record<string, string>>;
}

export interface RequestedFlow {
  flowId: string;
  pairPolicyId: string;
  sourceNodeConceptId: string;
  targetNodeConceptId: string;
  directionality: DirectionalityCapability;
  sourceRole: string;
  targetRole: string;
  origin: FlowOrigin;
  qualifications: Readonly<Record<string, string>>;
  provenanceRef: string;
}

export interface RequestedCluster {
  clusterId: string;
  clusterPolicyId: string;
  nodeConceptIds: readonly string[];
  flowIds: readonly string[];
}

export interface RequestedChain {
  chainId: string;
  chainPolicyId: string;
  orderedNodeConceptIds: readonly string[];
  orderedFlowIds: readonly string[];
}

export interface ExplorationBuildRequest {
  requestId: string;
  imageVersion: string;
  seed: string;
  semanticMode: "REAL" | "SYNTHETIC_TEST";
  syntheticTestOnly: boolean;
  constraintPackageHash: string;
  requestedNodes: readonly RequestedNode[];
  requestedFlows: readonly RequestedFlow[];
  requestedClusters: readonly RequestedCluster[];
  requestedChains: readonly RequestedChain[];
  forbiddenInputKinds: readonly ForbiddenInputKind[];
}

export interface CompiledExplorationImage {
  imageId: string;
  imageVersion: string;
  compilerVersion: typeof EXPLORATION_CONSTRAINT_COMPILER_VERSION;
  constraintPackageHash: string;
  requestHash: string;
  imageHash: string;
  seed: string;
  syntheticTestOnly: true;
  immutable: true;
  authorizationReceipt: {
    nodeConceptIds: readonly string[];
    pairPolicyIds: readonly string[];
    clusterPolicyIds: readonly string[];
    chainPolicyIds: readonly string[];
  };
  topology: {
    nodes: readonly RequestedNode[];
    flows: readonly RequestedFlow[];
    clusters: readonly RequestedCluster[];
    chains: readonly RequestedChain[];
  };
  layoutChoice: string;
}

export interface BuildRejectedReceipt {
  buildStatus: "REJECTED";
  failureCodes: readonly BuildFailureCode[];
  constraintPackageHash: string;
  requestHash: string;
  compilerVersion: typeof EXPLORATION_CONSTRAINT_COMPILER_VERSION;
}

export interface BuildSucceededReceipt {
  buildStatus: "COMPILED_SYNTHETIC_TEST_ONLY";
  imageId: string;
  imageVersion: string;
  compilerVersion: typeof EXPLORATION_CONSTRAINT_COMPILER_VERSION;
  constraintPackageHash: string;
  requestHash: string;
  imageHash: string;
  seed: string;
  syntheticTestOnly: true;
  image: Readonly<CompiledExplorationImage>;
}

export type ExplorationBuildReceipt =
  | BuildRejectedReceipt
  | BuildSucceededReceipt;

export interface SyntheticExplorationInstance {
  instanceId: string;
  baseImageId: string;
  baseImageVersion: string;
  baseImageBuildSha256: string;
  seed: string;
  generationPolicyVersion: string;
  structuralReceiptSha256: string;
  syntheticTestOnly: true;
}

export interface SyntheticExplorationContainer {
  containerId: string;
  instanceId: string;
  imageHash: string;
  activeNodeIds: string[];
  activeFlowIds: string[];
  activeClusterIds: string[];
  positions: Array<{ nodeConceptId: string; x: number; y: number }>;
  localEdits: Array<{
    editId: string;
    targetId: string;
    editKind: string;
    value: string | number | boolean;
  }>;
  expandedBranchIds: string[];
  hiddenComponentIds: string[];
  syntheticTestOnly: true;
}

type CanonicalValue =
  | null
  | boolean
  | number
  | string
  | CanonicalValue[]
  | { [key: string]: CanonicalValue };

function canonicalize(value: unknown, scope = "value"): CanonicalValue {
  if (value === null || typeof value === "string" || typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new Error(`${scope} contains a non-finite number`);
    return value;
  }
  if (Array.isArray(value)) {
    return value.map((entry, index) => canonicalize(entry, `${scope}[${index}]`));
  }
  if (typeof value === "object" && value !== null) {
    const output: { [key: string]: CanonicalValue } = {};
    for (const key of Object.keys(value as Record<string, unknown>).sort()) {
      const entry = (value as Record<string, unknown>)[key];
      if (entry !== undefined) output[key] = canonicalize(entry, `${scope}.${key}`);
    }
    return output;
  }
  throw new Error(`${scope} is not canonically serializable`);
}

export function canonicalSerializeConstraintValue(value: unknown): string {
  return JSON.stringify(canonicalize(value));
}

export async function sha256ConstraintValue(value: unknown): Promise<string> {
  const bytes = new TextEncoder().encode(canonicalSerializeConstraintValue(value));
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}

export function deepFreezeConstraintValue<T>(value: T): Readonly<T> {
  if (typeof value !== "object" || value === null || Object.isFrozen(value)) return value;
  Object.freeze(value);
  for (const entry of Object.values(value as Record<string, unknown>)) {
    deepFreezeConstraintValue(entry);
  }
  return value;
}

export async function createExplorationConstraintPackage(
  input: ConstraintPackageInput,
): Promise<Readonly<ExplorationConstraintPackage>> {
  const cloned = structuredClone(input);
  const buildSha256 = await sha256ConstraintValue(cloned);
  return deepFreezeConstraintValue({ ...cloned, buildSha256 });
}

export async function verifyExplorationConstraintPackageHash(
  constraintPackage: ExplorationConstraintPackage,
): Promise<boolean> {
  const { buildSha256: _ignored, ...unsigned } = constraintPackage;
  return (await sha256ConstraintValue(unsigned)) === constraintPackage.buildSha256;
}

export async function hashExplorationBuildRequest(
  request: ExplorationBuildRequest,
): Promise<string> {
  return sha256ConstraintValue(request);
}
