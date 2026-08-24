/**
 * Renderer-neutral TRACE Exploration Field contracts.
 *
 * Exploration is a conceptual-relation composition environment. This module is
 * intentionally independent from archive records, Search, Context, Spacetime,
 * renderers, and external semantic models.
 */

export const UNRESOLVED_RELATION_VOCABULARY_VERSION =
  "UNRESOLVED_RESEARCH_NEXT" as const;
export const UNRESOLVED_RELATION_GRAMMAR_VERSION =
  "UNRESOLVED_RESEARCH_NEXT" as const;
export const UNRESOLVED_CONCEPT_KIND =
  "UNRESOLVED_RESEARCH_PLACEHOLDER" as const;
export const UNRESOLVED_FLOW_KIND =
  "UNRESOLVED_RESEARCH_PLACEHOLDER" as const;
export const UNRESOLVED_DIRECTIONALITY =
  "UNRESOLVED_RESEARCH_PLACEHOLDER" as const;

export type ExplorationFlowOrigin =
  | "EVIDENCE_BACKED"
  | "GENERATIVE_COMPOSITION"
  | "USER_COMPOSED";

export type ExplorationClusterOrigin =
  | "GRAMMAR_COMPOSED"
  | "USER_COMPOSED";

export interface ExplorationNode {
  nodeId: string;
  conceptRef: string;
  conceptKind: string;
  provenanceRef?: string;
  epistemicStatus: string;
  visualRole?: string;
}

export interface ExplorationFlow {
  flowId: string;
  nodeSequence: readonly string[];
  flowKind: string;
  directionality: string;
  origin: ExplorationFlowOrigin;
  historicalClaim: boolean;
  evidenceRef?: string;
}

export interface ExplorationCluster {
  clusterId: string;
  nodeIds: readonly string[];
  flowIds: readonly string[];
  groupingRule: string;
  origin: ExplorationClusterOrigin;
}

export interface ExplorationBranch {
  branchId: string;
  nodeIds: readonly string[];
  childBranchIds: readonly string[];
}

export interface ExplorationVisualRoleBinding {
  roleId: string;
  nodeIds: readonly string[];
  flowIds: readonly string[];
  clusterIds: readonly string[];
}

export interface ExplorationTreeMap {
  treeMapId: string;
  nodes: readonly ExplorationNode[];
  flows: readonly ExplorationFlow[];
  clusters: readonly ExplorationCluster[];
  rootNodeIds: readonly string[];
  branches: readonly ExplorationBranch[];
  interClusterFlowIds: readonly string[];
  compositionConstraints: readonly string[];
  visualRoles: readonly ExplorationVisualRoleBinding[];
  topologyIsVisualGeometry: false;
}

export interface ExplorationImage {
  imageId: string;
  imageVersion: string;
  relationVocabularyVersion: string;
  relationGrammarVersion: string;
  treeMap: ExplorationTreeMap;
  layoutGrammarVersion: string;
  seedPolicyVersion: string;
  buildSha256: string;
  immutable: true;
}

export interface ExplorationInstance {
  instanceId: string;
  baseImageId: string;
  baseImageVersion: string;
  seed: string;
  createdFromBuildSha256: string;
  generationPolicyVersion: string;
  structuralReceiptSha256: string;
}

export interface ExplorationPosition {
  nodeId: string;
  x: number;
  y: number;
}

export interface ExplorationLocalEdit {
  editId: string;
  targetKind: "NODE" | "FLOW" | "CLUSTER";
  targetId: string;
  editKind: string;
  valueRef?: string;
  numberValue?: number;
  booleanValue?: boolean;
}

export interface ExplorationContainer {
  containerId: string;
  instanceId: string;
  activeNodeIds: string[];
  activeFlowIds: string[];
  activeClusterIds: string[];
  positions: ExplorationPosition[];
  localEdits: ExplorationLocalEdit[];
  expandedBranchIds: string[];
  hiddenComponentIds: string[];
}

export interface RenderedPng {
  mediaType: "image/png";
  metadataSchemaVersion: string;
  imageId: string;
  imageVersion: string;
  imageBuildSha256: string;
  instanceId: string;
  seed: string;
  rendererVersion: string;
  pngIsSourceOfTruth: false;
}

export type RelationVocabularyPolicy =
  | {
      status: "UNRESOLVED";
      vocabularyVersion: typeof UNRESOLVED_RELATION_VOCABULARY_VERSION;
      grammarVersion: typeof UNRESOLVED_RELATION_GRAMMAR_VERSION;
    }
  | {
      status: "GOVERNED";
      vocabularyVersion: string;
      grammarVersion: string;
      governanceRef: string;
      conceptKinds: readonly string[];
      flowKinds: readonly string[];
      directionalities: readonly string[];
    };

export const RESET_RELATION_POLICY: RelationVocabularyPolicy = Object.freeze({
  status: "UNRESOLVED",
  vocabularyVersion: UNRESOLVED_RELATION_VOCABULARY_VERSION,
  grammarVersion: UNRESOLVED_RELATION_GRAMMAR_VERSION,
});

export class ExplorationContractError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ExplorationContractError";
  }
}

/* exploration-guard:allow-denial-start */
const FORBIDDEN_ARCHIVE_KEYS = new Set([
  "archiveobjectid",
  "objectid",
  "recordid",
  "surfaceid",
  "sourceobjectid",
  "creatorid",
  "objecttitle",
  "thumbnail",
  "thumbnailurl",
  "imageurl",
  "recordurl",
  "recordhref",
  "objecthref",
  "objecturl",
  "objectcard",
  "recorddto",
  "archiveobject",
]);

const ARCHIVE_ID_PREFIXES = ["SURF-", "TRN-OBJ-", "OBJECT-", "RECORD-"];
const CLUSTER_PROHIBITIONS = [
  "similarity",
  "similar works",
  "nearest neighbor",
  "affinity",
  "k-means",
  "kmeans",
  "hdbscan",
  "dbscan",
  "community detection",
  "object cluster",
];
/* exploration-guard:allow-denial-end */

function normalizeKey(key: string): string {
  return key.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requireRecord(value: unknown, scope: string): Record<string, unknown> {
  if (!isRecord(value)) {
    throw new ExplorationContractError(`${scope} must be a plain record`);
  }
  return value;
}

function assertExactKeys(
  value: Record<string, unknown>,
  required: readonly string[],
  optional: readonly string[],
  scope: string,
): void {
  const allowed = new Set([...required, ...optional]);
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) {
      throw new ExplorationContractError(`${scope} contains unknown key: ${key}`);
    }
  }
  for (const key of required) {
    if (!(key in value)) {
      throw new ExplorationContractError(`${scope} is missing required key: ${key}`);
    }
  }
}

function requireString(value: unknown, scope: string): string {
  if (typeof value !== "string" || value.trim() === "") {
    throw new ExplorationContractError(`${scope} must be a nonempty string`);
  }
  return value;
}

function requireBoolean(value: unknown, scope: string): boolean {
  if (typeof value !== "boolean") {
    throw new ExplorationContractError(`${scope} must be a boolean`);
  }
  return value;
}

function requireFiniteNumber(value: unknown, scope: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new ExplorationContractError(`${scope} must be a finite number`);
  }
  return value;
}

function requireStringArray(value: unknown, scope: string): string[] {
  if (!Array.isArray(value)) {
    throw new ExplorationContractError(`${scope} must be an array`);
  }
  const strings = value.map((entry, index) =>
    requireString(entry, `${scope}[${index}]`),
  );
  if (new Set(strings).size !== strings.length) {
    throw new ExplorationContractError(`${scope} contains duplicate IDs`);
  }
  return strings;
}

function assertConceptualId(
  value: unknown,
  scope: string,
  allowedPrefixes: readonly string[],
): string {
  const identifier = requireString(value, scope);
  if (ARCHIVE_ID_PREFIXES.some((prefix) => identifier.startsWith(prefix))) {
    throw new ExplorationContractError(`${scope} aliases an archive identity`);
  }
  if (!allowedPrefixes.some((prefix) => identifier.startsWith(prefix))) {
    throw new ExplorationContractError(
      `${scope} must use a governed conceptual prefix: ${allowedPrefixes.join(", ")}`,
    );
  }
  if (!/^[A-Z][A-Z0-9._-]*$/.test(identifier)) {
    throw new ExplorationContractError(`${scope} has invalid conceptual ID syntax`);
  }
  return identifier;
}

function assertReferenceSet(
  references: readonly string[],
  known: ReadonlySet<string>,
  scope: string,
): void {
  for (const reference of references) {
    if (!known.has(reference)) {
      throw new ExplorationContractError(`${scope} references unknown ID: ${reference}`);
    }
  }
}

export function assertNoArchiveObjectIdentity(
  value: unknown,
  scope = "Exploration artifact",
): void {
  const visit = (candidate: unknown, path: string): void => {
    if (typeof candidate === "string") {
      if (
        ARCHIVE_ID_PREFIXES.some((prefix) => candidate.startsWith(prefix)) ||
        /\/surfaces\//i.test(candidate)
      ) {
        throw new ExplorationContractError(`${path} contains an archive identity value`);
      }
      return;
    }
    if (Array.isArray(candidate)) {
      candidate.forEach((entry, index) => visit(entry, `${path}[${index}]`));
      return;
    }
    if (!isRecord(candidate)) return;

    const normalizedKeys = new Set(Object.keys(candidate).map(normalizeKey));
    for (const key of Object.keys(candidate)) {
      if (FORBIDDEN_ARCHIVE_KEYS.has(normalizeKey(key))) {
        throw new ExplorationContractError(`${path} contains archive key: ${key}`);
      }
    }
    const looksLikeProjectRecord =
      normalizedKeys.has("id") &&
      normalizedKeys.has("title") &&
      (["href", "source", "sourceurl", "thumbnail"].some((key) =>
        normalizedKeys.has(key),
      ));
    if (looksLikeProjectRecord) {
      throw new ExplorationContractError(`${path} contains a project record DTO shape`);
    }
    for (const [key, entry] of Object.entries(candidate)) {
      visit(entry, `${path}.${key}`);
    }
  };
  visit(value, scope);
}

function assertPolicy(policy: RelationVocabularyPolicy): void {
  if (policy.status === "UNRESOLVED") return;
  requireString(policy.governanceRef, "relation policy governanceRef");
  if (
    policy.conceptKinds.length === 0 ||
    policy.flowKinds.length === 0 ||
    policy.directionalities.length === 0
  ) {
    throw new ExplorationContractError(
      "a governed relation policy requires governed vocabulary and grammar sets",
    );
  }
}

export function assertExplorationNode(
  candidate: unknown,
  policy: RelationVocabularyPolicy = RESET_RELATION_POLICY,
): asserts candidate is ExplorationNode {
  assertNoArchiveObjectIdentity(candidate, "ExplorationNode");
  assertPolicy(policy);
  const node = requireRecord(candidate, "ExplorationNode");
  assertExactKeys(
    node,
    ["nodeId", "conceptRef", "conceptKind", "epistemicStatus"],
    ["provenanceRef", "visualRole"],
    "ExplorationNode",
  );
  assertConceptualId(node.nodeId, "ExplorationNode.nodeId", ["NODE-", "EXP-NODE-"]);
  assertConceptualId(node.conceptRef, "ExplorationNode.conceptRef", [
    "CONCEPT-",
    "CONCEPT-REF-",
  ]);
  const conceptKind = requireString(node.conceptKind, "ExplorationNode.conceptKind");
  if (policy.status === "UNRESOLVED") {
    if (conceptKind !== UNRESOLVED_CONCEPT_KIND) {
      throw new ExplorationContractError(
        "relation vocabulary is unresolved; ungoverned conceptKind is prohibited",
      );
    }
  } else if (!policy.conceptKinds.includes(conceptKind)) {
    throw new ExplorationContractError("conceptKind is absent from the governed vocabulary");
  }
  requireString(node.epistemicStatus, "ExplorationNode.epistemicStatus");
  if (node.provenanceRef !== undefined) {
    assertConceptualId(node.provenanceRef, "ExplorationNode.provenanceRef", [
      "PROVENANCE-",
      "EVIDENCE-",
    ]);
  }
  if (node.visualRole !== undefined) {
    requireString(node.visualRole, "ExplorationNode.visualRole");
  }
}

export function assertExplorationFlow(
  candidate: unknown,
  policy: RelationVocabularyPolicy = RESET_RELATION_POLICY,
): asserts candidate is ExplorationFlow {
  assertNoArchiveObjectIdentity(candidate, "ExplorationFlow");
  assertPolicy(policy);
  const flow = requireRecord(candidate, "ExplorationFlow");
  assertExactKeys(
    flow,
    [
      "flowId",
      "nodeSequence",
      "flowKind",
      "directionality",
      "origin",
      "historicalClaim",
    ],
    ["evidenceRef"],
    "ExplorationFlow",
  );
  assertConceptualId(flow.flowId, "ExplorationFlow.flowId", ["FLOW-", "EXP-FLOW-"]);
  const nodeSequence = requireStringArray(flow.nodeSequence, "ExplorationFlow.nodeSequence");
  if (nodeSequence.length < 2) {
    throw new ExplorationContractError("ExplorationFlow requires at least two conceptual nodes");
  }
  nodeSequence.forEach((nodeId, index) =>
    assertConceptualId(nodeId, `ExplorationFlow.nodeSequence[${index}]`, [
      "NODE-",
      "EXP-NODE-",
    ]),
  );
  const flowKind = requireString(flow.flowKind, "ExplorationFlow.flowKind");
  const directionality = requireString(
    flow.directionality,
    "ExplorationFlow.directionality",
  );
  if (policy.status === "UNRESOLVED") {
    if (
      flowKind !== UNRESOLVED_FLOW_KIND ||
      directionality !== UNRESOLVED_DIRECTIONALITY
    ) {
      throw new ExplorationContractError(
        "relation grammar is unresolved; ungoverned flow semantics are prohibited",
      );
    }
  } else {
    if (!policy.flowKinds.includes(flowKind)) {
      throw new ExplorationContractError("flowKind is absent from the governed grammar");
    }
    if (!policy.directionalities.includes(directionality)) {
      throw new ExplorationContractError(
        "directionality is absent from the governed grammar",
      );
    }
  }
  if (!(["EVIDENCE_BACKED", "GENERATIVE_COMPOSITION", "USER_COMPOSED"] as unknown[]).includes(flow.origin)) {
    throw new ExplorationContractError("ExplorationFlow.origin is invalid");
  }
  const historicalClaim = requireBoolean(
    flow.historicalClaim,
    "ExplorationFlow.historicalClaim",
  );
  if (
    (flow.origin === "GENERATIVE_COMPOSITION" || flow.origin === "USER_COMPOSED") &&
    historicalClaim
  ) {
    throw new ExplorationContractError(
      `${flow.origin} must always set historicalClaim=false`,
    );
  }
  if (flow.origin === "EVIDENCE_BACKED") {
    assertConceptualId(flow.evidenceRef, "ExplorationFlow.evidenceRef", ["EVIDENCE-"]);
  } else if (flow.evidenceRef !== undefined) {
    throw new ExplorationContractError(
      "composition-only flows cannot carry an evidence-backed assertion reference",
    );
  }
}

export function assertExplorationCluster(
  candidate: unknown,
): asserts candidate is ExplorationCluster {
  assertNoArchiveObjectIdentity(candidate, "ExplorationCluster");
  const cluster = requireRecord(candidate, "ExplorationCluster");
  assertExactKeys(
    cluster,
    ["clusterId", "nodeIds", "flowIds", "groupingRule", "origin"],
    [],
    "ExplorationCluster",
  );
  assertConceptualId(cluster.clusterId, "ExplorationCluster.clusterId", [
    "CLUSTER-",
    "EXP-CLUSTER-",
  ]);
  requireStringArray(cluster.nodeIds, "ExplorationCluster.nodeIds").forEach(
    (nodeId, index) =>
      assertConceptualId(nodeId, `ExplorationCluster.nodeIds[${index}]`, [
        "NODE-",
        "EXP-NODE-",
      ]),
  );
  requireStringArray(cluster.flowIds, "ExplorationCluster.flowIds").forEach(
    (flowId, index) =>
      assertConceptualId(flowId, `ExplorationCluster.flowIds[${index}]`, [
        "FLOW-",
        "EXP-FLOW-",
      ]),
  );
  const groupingRule = requireString(
    cluster.groupingRule,
    "ExplorationCluster.groupingRule",
  ).toLowerCase();
  if (CLUSTER_PROHIBITIONS.some((term) => groupingRule.includes(term))) {
    throw new ExplorationContractError(
      "cluster groupingRule invokes prohibited similarity/object-clustering semantics",
    );
  }
  if (!(cluster.origin === "GRAMMAR_COMPOSED" || cluster.origin === "USER_COMPOSED")) {
    throw new ExplorationContractError("ExplorationCluster.origin is invalid");
  }
}

function assertExplorationBranch(candidate: unknown): asserts candidate is ExplorationBranch {
  const branch = requireRecord(candidate, "ExplorationBranch");
  assertExactKeys(branch, ["branchId", "nodeIds", "childBranchIds"], [], "ExplorationBranch");
  assertConceptualId(branch.branchId, "ExplorationBranch.branchId", ["BRANCH-"]);
  requireStringArray(branch.nodeIds, "ExplorationBranch.nodeIds");
  requireStringArray(branch.childBranchIds, "ExplorationBranch.childBranchIds");
}

function assertVisualRoleBinding(
  candidate: unknown,
): asserts candidate is ExplorationVisualRoleBinding {
  const binding = requireRecord(candidate, "ExplorationVisualRoleBinding");
  assertExactKeys(
    binding,
    ["roleId", "nodeIds", "flowIds", "clusterIds"],
    [],
    "ExplorationVisualRoleBinding",
  );
  assertConceptualId(binding.roleId, "ExplorationVisualRoleBinding.roleId", ["ROLE-"]);
  requireStringArray(binding.nodeIds, "ExplorationVisualRoleBinding.nodeIds");
  requireStringArray(binding.flowIds, "ExplorationVisualRoleBinding.flowIds");
  requireStringArray(binding.clusterIds, "ExplorationVisualRoleBinding.clusterIds");
}

export function assertExplorationTreeMap(
  candidate: unknown,
  policy: RelationVocabularyPolicy = RESET_RELATION_POLICY,
): asserts candidate is ExplorationTreeMap {
  assertNoArchiveObjectIdentity(candidate, "ExplorationTreeMap");
  const treeMap = requireRecord(candidate, "ExplorationTreeMap");
  assertExactKeys(
    treeMap,
    [
      "treeMapId",
      "nodes",
      "flows",
      "clusters",
      "rootNodeIds",
      "branches",
      "interClusterFlowIds",
      "compositionConstraints",
      "visualRoles",
      "topologyIsVisualGeometry",
    ],
    [],
    "ExplorationTreeMap",
  );
  assertConceptualId(treeMap.treeMapId, "ExplorationTreeMap.treeMapId", ["TREE-"]);
  if (!Array.isArray(treeMap.nodes) || !Array.isArray(treeMap.flows) || !Array.isArray(treeMap.clusters)) {
    throw new ExplorationContractError("ExplorationTreeMap collections must be arrays");
  }
  treeMap.nodes.forEach((node) => assertExplorationNode(node, policy));
  treeMap.flows.forEach((flow) => assertExplorationFlow(flow, policy));
  treeMap.clusters.forEach(assertExplorationCluster);

  const nodeIds = new Set(treeMap.nodes.map((node) => (node as ExplorationNode).nodeId));
  const flowIds = new Set(treeMap.flows.map((flow) => (flow as ExplorationFlow).flowId));
  const clusterIds = new Set(
    treeMap.clusters.map((cluster) => (cluster as ExplorationCluster).clusterId),
  );
  if (
    nodeIds.size !== treeMap.nodes.length ||
    flowIds.size !== treeMap.flows.length ||
    clusterIds.size !== treeMap.clusters.length
  ) {
    throw new ExplorationContractError("ExplorationTreeMap IDs must be unique by primitive kind");
  }
  for (const flow of treeMap.flows as ExplorationFlow[]) {
    assertReferenceSet(flow.nodeSequence, nodeIds, `${flow.flowId}.nodeSequence`);
  }
  for (const cluster of treeMap.clusters as ExplorationCluster[]) {
    assertReferenceSet(cluster.nodeIds, nodeIds, `${cluster.clusterId}.nodeIds`);
    assertReferenceSet(cluster.flowIds, flowIds, `${cluster.clusterId}.flowIds`);
  }
  assertReferenceSet(
    requireStringArray(treeMap.rootNodeIds, "ExplorationTreeMap.rootNodeIds"),
    nodeIds,
    "ExplorationTreeMap.rootNodeIds",
  );
  if (!Array.isArray(treeMap.branches)) {
    throw new ExplorationContractError("ExplorationTreeMap.branches must be an array");
  }
  treeMap.branches.forEach(assertExplorationBranch);
  const branchIds = new Set(
    treeMap.branches.map((branch) => (branch as ExplorationBranch).branchId),
  );
  for (const branch of treeMap.branches as ExplorationBranch[]) {
    assertReferenceSet(branch.nodeIds, nodeIds, `${branch.branchId}.nodeIds`);
    assertReferenceSet(
      branch.childBranchIds,
      branchIds,
      `${branch.branchId}.childBranchIds`,
    );
  }
  assertReferenceSet(
    requireStringArray(
      treeMap.interClusterFlowIds,
      "ExplorationTreeMap.interClusterFlowIds",
    ),
    flowIds,
    "ExplorationTreeMap.interClusterFlowIds",
  );
  requireStringArray(
    treeMap.compositionConstraints,
    "ExplorationTreeMap.compositionConstraints",
  ).forEach((constraintId, index) =>
    assertConceptualId(
      constraintId,
      `ExplorationTreeMap.compositionConstraints[${index}]`,
      ["CONSTRAINT-"],
    ),
  );
  if (!Array.isArray(treeMap.visualRoles)) {
    throw new ExplorationContractError("ExplorationTreeMap.visualRoles must be an array");
  }
  treeMap.visualRoles.forEach(assertVisualRoleBinding);
  for (const binding of treeMap.visualRoles as ExplorationVisualRoleBinding[]) {
    assertReferenceSet(binding.nodeIds, nodeIds, `${binding.roleId}.nodeIds`);
    assertReferenceSet(binding.flowIds, flowIds, `${binding.roleId}.flowIds`);
    assertReferenceSet(binding.clusterIds, clusterIds, `${binding.roleId}.clusterIds`);
  }
  if (treeMap.topologyIsVisualGeometry !== false) {
    throw new ExplorationContractError("TreeMap topology must not be visual geometry");
  }
}

function assertSha256(value: unknown, scope: string): string {
  const sha = requireString(value, scope);
  if (!/^[a-f0-9]{64}$/.test(sha)) {
    throw new ExplorationContractError(`${scope} must be a lowercase SHA-256 digest`);
  }
  return sha;
}

export function assertExplorationImage(
  candidate: unknown,
  policy: RelationVocabularyPolicy = RESET_RELATION_POLICY,
): asserts candidate is ExplorationImage {
  assertNoArchiveObjectIdentity(candidate, "ExplorationImage");
  const image = requireRecord(candidate, "ExplorationImage");
  assertExactKeys(
    image,
    [
      "imageId",
      "imageVersion",
      "relationVocabularyVersion",
      "relationGrammarVersion",
      "treeMap",
      "layoutGrammarVersion",
      "seedPolicyVersion",
      "buildSha256",
      "immutable",
    ],
    [],
    "ExplorationImage",
  );
  assertConceptualId(image.imageId, "ExplorationImage.imageId", ["IMAGE-"]);
  requireString(image.imageVersion, "ExplorationImage.imageVersion");
  if (image.relationVocabularyVersion !== policy.vocabularyVersion) {
    throw new ExplorationContractError("Image relationVocabularyVersion does not match policy");
  }
  if (image.relationGrammarVersion !== policy.grammarVersion) {
    throw new ExplorationContractError("Image relationGrammarVersion does not match policy");
  }
  assertExplorationTreeMap(image.treeMap, policy);
  requireString(image.layoutGrammarVersion, "ExplorationImage.layoutGrammarVersion");
  requireString(image.seedPolicyVersion, "ExplorationImage.seedPolicyVersion");
  assertSha256(image.buildSha256, "ExplorationImage.buildSha256");
  if (image.immutable !== true) {
    throw new ExplorationContractError("ExplorationImage.immutable must be true");
  }
}

type CanonicalJson = null | boolean | number | string | CanonicalJson[] | {
  [key: string]: CanonicalJson;
};

function canonicalize(value: unknown, scope = "value"): CanonicalJson {
  if (value === null || typeof value === "string" || typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      throw new ExplorationContractError(`${scope} contains a non-finite number`);
    }
    return value;
  }
  if (Array.isArray(value)) {
    return value.map((entry, index) => canonicalize(entry, `${scope}[${index}]`));
  }
  if (isRecord(value)) {
    const output: { [key: string]: CanonicalJson } = {};
    for (const key of Object.keys(value).sort()) {
      const entry = value[key];
      if (entry !== undefined) output[key] = canonicalize(entry, `${scope}.${key}`);
    }
    return output;
  }
  throw new ExplorationContractError(`${scope} is not canonically serializable`);
}

export function canonicalSerialize(value: unknown): string {
  assertNoArchiveObjectIdentity(value);
  return JSON.stringify(canonicalize(value));
}

export async function sha256Canonical(value: unknown): Promise<string> {
  const bytes = new TextEncoder().encode(canonicalSerialize(value));
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function deepFreeze<T>(value: T): Readonly<T> {
  if (typeof value !== "object" || value === null || Object.isFrozen(value)) {
    return value;
  }
  Object.freeze(value);
  for (const entry of Object.values(value as Record<string, unknown>)) {
    deepFreeze(entry);
  }
  return value;
}

export type ExplorationImageBuildInput = Omit<
  ExplorationImage,
  "buildSha256" | "immutable"
>;

export async function computeExplorationImageBuildSha256(
  image: ExplorationImage | (ExplorationImageBuildInput & { immutable?: true }),
): Promise<string> {
  const { buildSha256: _ignored, ...unsigned } = image as ExplorationImage;
  return sha256Canonical({ ...unsigned, immutable: true });
}

export async function compileExplorationImage(
  input: ExplorationImageBuildInput,
  policy: RelationVocabularyPolicy = RESET_RELATION_POLICY,
): Promise<Readonly<ExplorationImage>> {
  const unsigned = structuredClone({ ...input, immutable: true });
  const buildSha256 = await sha256Canonical(unsigned);
  const image = { ...unsigned, buildSha256 } as ExplorationImage;
  assertExplorationImage(image, policy);
  return deepFreeze(image);
}

export async function verifyExplorationImageBuildHash(
  image: ExplorationImage,
): Promise<boolean> {
  return (await computeExplorationImageBuildSha256(image)) === image.buildSha256;
}

export function assertExplorationInstance(
  candidate: unknown,
): asserts candidate is ExplorationInstance {
  assertNoArchiveObjectIdentity(candidate, "ExplorationInstance");
  const instance = requireRecord(candidate, "ExplorationInstance");
  assertExactKeys(
    instance,
    [
      "instanceId",
      "baseImageId",
      "baseImageVersion",
      "seed",
      "createdFromBuildSha256",
      "generationPolicyVersion",
      "structuralReceiptSha256",
    ],
    [],
    "ExplorationInstance",
  );
  assertConceptualId(instance.instanceId, "ExplorationInstance.instanceId", [
    "INSTANCE-",
  ]);
  assertConceptualId(instance.baseImageId, "ExplorationInstance.baseImageId", [
    "IMAGE-",
  ]);
  requireString(instance.baseImageVersion, "ExplorationInstance.baseImageVersion");
  requireString(instance.seed, "ExplorationInstance.seed");
  assertSha256(
    instance.createdFromBuildSha256,
    "ExplorationInstance.createdFromBuildSha256",
  );
  requireString(
    instance.generationPolicyVersion,
    "ExplorationInstance.generationPolicyVersion",
  );
  assertSha256(
    instance.structuralReceiptSha256,
    "ExplorationInstance.structuralReceiptSha256",
  );
}

export async function instantiateExplorationImage(
  image: ExplorationImage,
  seed: string,
  generationPolicyVersion: string,
  policy: RelationVocabularyPolicy = RESET_RELATION_POLICY,
): Promise<Readonly<ExplorationInstance>> {
  assertExplorationImage(image, policy);
  if (!(await verifyExplorationImageBuildHash(image))) {
    throw new ExplorationContractError("cannot instantiate an Image with an invalid build hash");
  }
  const receiptInput = {
    baseImageId: image.imageId,
    baseImageVersion: image.imageVersion,
    seed: requireString(seed, "ExplorationInstance.seed"),
    createdFromBuildSha256: image.buildSha256,
    generationPolicyVersion: requireString(
      generationPolicyVersion,
      "ExplorationInstance.generationPolicyVersion",
    ),
  };
  const structuralReceiptSha256 = await sha256Canonical(receiptInput);
  const instance = {
    instanceId: `INSTANCE-${structuralReceiptSha256.slice(0, 24).toUpperCase()}`,
    ...receiptInput,
    structuralReceiptSha256,
  };
  assertExplorationInstance(instance);
  return deepFreeze(instance);
}

export function assertExplorationContainer(
  candidate: unknown,
): asserts candidate is ExplorationContainer {
  assertNoArchiveObjectIdentity(candidate, "ExplorationContainer");
  const container = requireRecord(candidate, "ExplorationContainer");
  assertExactKeys(
    container,
    [
      "containerId",
      "instanceId",
      "activeNodeIds",
      "activeFlowIds",
      "activeClusterIds",
      "positions",
      "localEdits",
      "expandedBranchIds",
      "hiddenComponentIds",
    ],
    [],
    "ExplorationContainer",
  );
  assertConceptualId(container.containerId, "ExplorationContainer.containerId", [
    "CONTAINER-",
  ]);
  assertConceptualId(container.instanceId, "ExplorationContainer.instanceId", ["INSTANCE-"]);
  requireStringArray(container.activeNodeIds, "ExplorationContainer.activeNodeIds").forEach(
    (id, index) =>
      assertConceptualId(id, `ExplorationContainer.activeNodeIds[${index}]`, ["NODE-", "EXP-NODE-"]),
  );
  requireStringArray(container.activeFlowIds, "ExplorationContainer.activeFlowIds").forEach(
    (id, index) =>
      assertConceptualId(id, `ExplorationContainer.activeFlowIds[${index}]`, ["FLOW-", "EXP-FLOW-"]),
  );
  requireStringArray(container.activeClusterIds, "ExplorationContainer.activeClusterIds").forEach(
    (id, index) =>
      assertConceptualId(id, `ExplorationContainer.activeClusterIds[${index}]`, ["CLUSTER-", "EXP-CLUSTER-"]),
  );
  requireStringArray(container.expandedBranchIds, "ExplorationContainer.expandedBranchIds").forEach(
    (id, index) =>
      assertConceptualId(id, `ExplorationContainer.expandedBranchIds[${index}]`, ["BRANCH-"]),
  );
  requireStringArray(container.hiddenComponentIds, "ExplorationContainer.hiddenComponentIds").forEach(
    (id, index) =>
      assertConceptualId(id, `ExplorationContainer.hiddenComponentIds[${index}]`, [
        "NODE-",
        "EXP-NODE-",
        "FLOW-",
        "EXP-FLOW-",
        "CLUSTER-",
        "EXP-CLUSTER-",
        "BRANCH-",
        "ROLE-",
      ]),
  );
  if (!Array.isArray(container.positions) || !Array.isArray(container.localEdits)) {
    throw new ExplorationContractError("Container positions and localEdits must be arrays");
  }
  container.positions.forEach((candidatePosition, index) => {
    const position = requireRecord(candidatePosition, `ExplorationPosition[${index}]`);
    assertExactKeys(position, ["nodeId", "x", "y"], [], `ExplorationPosition[${index}]`);
    assertConceptualId(position.nodeId, `ExplorationPosition[${index}].nodeId`, [
      "NODE-",
      "EXP-NODE-",
    ]);
    requireFiniteNumber(position.x, `ExplorationPosition[${index}].x`);
    requireFiniteNumber(position.y, `ExplorationPosition[${index}].y`);
  });
  container.localEdits.forEach((candidateEdit, index) => {
    const edit = requireRecord(candidateEdit, `ExplorationLocalEdit[${index}]`);
    assertExactKeys(
      edit,
      ["editId", "targetKind", "targetId", "editKind"],
      ["valueRef", "numberValue", "booleanValue"],
      `ExplorationLocalEdit[${index}]`,
    );
    assertConceptualId(edit.editId, `ExplorationLocalEdit[${index}].editId`, ["EDIT-"]);
    if (!(edit.targetKind === "NODE" || edit.targetKind === "FLOW" || edit.targetKind === "CLUSTER")) {
      throw new ExplorationContractError(`ExplorationLocalEdit[${index}].targetKind is invalid`);
    }
    const targetPrefixes =
      edit.targetKind === "NODE"
        ? ["NODE-", "EXP-NODE-"]
        : edit.targetKind === "FLOW"
          ? ["FLOW-", "EXP-FLOW-"]
          : ["CLUSTER-", "EXP-CLUSTER-"];
    assertConceptualId(
      edit.targetId,
      `ExplorationLocalEdit[${index}].targetId`,
      targetPrefixes,
    );
    requireString(edit.editKind, `ExplorationLocalEdit[${index}].editKind`);
    if (edit.valueRef !== undefined) {
      assertConceptualId(edit.valueRef, `ExplorationLocalEdit[${index}].valueRef`, [
        "VALUE-",
      ]);
    }
    if (edit.numberValue !== undefined) requireFiniteNumber(edit.numberValue, `ExplorationLocalEdit[${index}].numberValue`);
    if (edit.booleanValue !== undefined) requireBoolean(edit.booleanValue, `ExplorationLocalEdit[${index}].booleanValue`);
  });
}

export function createExplorationContainer(
  instance: ExplorationInstance,
  treeMap: ExplorationTreeMap,
): ExplorationContainer {
  assertExplorationInstance(instance);
  assertExplorationTreeMap(treeMap);
  const container: ExplorationContainer = {
    containerId: `CONTAINER-${instance.instanceId.slice("INSTANCE-".length)}`,
    instanceId: instance.instanceId,
    activeNodeIds: treeMap.nodes.map(({ nodeId }) => nodeId),
    activeFlowIds: treeMap.flows.map(({ flowId }) => flowId),
    activeClusterIds: treeMap.clusters.map(({ clusterId }) => clusterId),
    positions: [],
    localEdits: [],
    expandedBranchIds: [],
    hiddenComponentIds: [],
  };
  assertExplorationContainer(container);
  return container;
}

export function assertRenderedPng(candidate: unknown): asserts candidate is RenderedPng {
  assertNoArchiveObjectIdentity(candidate, "RenderedPng");
  const png = requireRecord(candidate, "RenderedPng");
  assertExactKeys(
    png,
    [
      "mediaType",
      "metadataSchemaVersion",
      "imageId",
      "imageVersion",
      "imageBuildSha256",
      "instanceId",
      "seed",
      "rendererVersion",
      "pngIsSourceOfTruth",
    ],
    [],
    "RenderedPng",
  );
  if (png.mediaType !== "image/png") {
    throw new ExplorationContractError("RenderedPng.mediaType must be image/png");
  }
  requireString(png.metadataSchemaVersion, "RenderedPng.metadataSchemaVersion");
  assertConceptualId(png.imageId, "RenderedPng.imageId", ["IMAGE-"]);
  requireString(png.imageVersion, "RenderedPng.imageVersion");
  assertSha256(png.imageBuildSha256, "RenderedPng.imageBuildSha256");
  assertConceptualId(png.instanceId, "RenderedPng.instanceId", ["INSTANCE-"]);
  requireString(png.seed, "RenderedPng.seed");
  requireString(png.rendererVersion, "RenderedPng.rendererVersion");
  if (png.pngIsSourceOfTruth !== false) {
    throw new ExplorationContractError("RenderedPng cannot be a semantic source of truth");
  }
}
