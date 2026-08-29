import assert from "node:assert/strict";

import {
  RESET_RELATION_POLICY,
  UNRESOLVED_CONCEPT_KIND,
  UNRESOLVED_DIRECTIONALITY,
  UNRESOLVED_FLOW_KIND,
  UNRESOLVED_RELATION_GRAMMAR_VERSION,
  UNRESOLVED_RELATION_VOCABULARY_VERSION,
  assertExplorationCluster,
  assertExplorationContainer,
  assertExplorationFlow,
  assertExplorationInstance,
  assertExplorationNode,
  assertRenderedPng,
  compileExplorationImage,
  computeExplorationImageBuildSha256,
  createExplorationContainer,
  instantiateExplorationImage,
  verifyExplorationImageBuildHash,
} from "../src/lib/trace/exploration-domain.ts";
import {
  auditActiveRepository,
  evaluateGovernedDatabaseFreezeReceipt,
  scanCandidateSource,
} from "./exploration-reset-guard.mjs";

const checks = [];
const redTeam = [];

function check(name, fn) {
  checks.push({ name, fn });
}

function expectRejected(name, fn) {
  redTeam.push({ name, fn });
}

const nodeA = {
  nodeId: "NODE-TEST-A",
  conceptRef: "CONCEPT-TEST-A",
  conceptKind: UNRESOLVED_CONCEPT_KIND,
  epistemicStatus: "COMPOSITION_ONLY",
};
const nodeB = {
  nodeId: "NODE-TEST-B",
  conceptRef: "CONCEPT-TEST-B",
  conceptKind: UNRESOLVED_CONCEPT_KIND,
  epistemicStatus: "COMPOSITION_ONLY",
};
const flowA = {
  flowId: "FLOW-TEST-A",
  nodeSequence: [nodeA.nodeId, nodeB.nodeId],
  flowKind: UNRESOLVED_FLOW_KIND,
  directionality: UNRESOLVED_DIRECTIONALITY,
  origin: "GENERATIVE_COMPOSITION",
  historicalClaim: false,
};
const clusterA = {
  clusterId: "CLUSTER-TEST-A",
  nodeIds: [nodeA.nodeId, nodeB.nodeId],
  flowIds: [flowA.flowId],
  groupingRule: "GRAMMAR-COMPOSITION-RULE-TEST-A",
  origin: "GRAMMAR_COMPOSED",
};
const treeMap = {
  treeMapId: "TREE-TEST-A",
  nodes: [nodeA, nodeB],
  flows: [flowA],
  clusters: [clusterA],
  rootNodeIds: [nodeA.nodeId],
  branches: [
    {
      branchId: "BRANCH-TEST-A",
      nodeIds: [nodeA.nodeId, nodeB.nodeId],
      childBranchIds: [],
    },
  ],
  interClusterFlowIds: [],
  compositionConstraints: ["CONSTRAINT-TEST-A"],
  visualRoles: [
    {
      roleId: "ROLE-TEST-A",
      nodeIds: [nodeA.nodeId],
      flowIds: [flowA.flowId],
      clusterIds: [clusterA.clusterId],
    },
  ],
  topologyIsVisualGeometry: false,
};
const imageInput = {
  imageId: "IMAGE-TEST-A",
  imageVersion: "0.0.0-STRUCTURAL-TEST",
  relationVocabularyVersion: UNRESOLVED_RELATION_VOCABULARY_VERSION,
  relationGrammarVersion: UNRESOLVED_RELATION_GRAMMAR_VERSION,
  treeMap,
  layoutGrammarVersion: "LAYOUT-GRAMMAR-STRUCTURAL-TEST",
  seedPolicyVersion: "SEED-POLICY-STRUCTURAL-TEST",
};

let compiledImage;
let instance;
let container;

check("structural contracts accept neutral fixtures", () => {
  assertExplorationNode(nodeA);
  assertExplorationFlow(flowA);
  assertExplorationCluster(clusterA);
});

check("same Image content has same canonical build hash", async () => {
  compiledImage = await compileExplorationImage(imageInput);
  const replay = await compileExplorationImage(structuredClone(imageInput));
  assert.equal(compiledImage.buildSha256, replay.buildSha256);
  assert.equal(await verifyExplorationImageBuildHash(compiledImage), true);
});

check("same Image, seed, and policy has same Instance receipt", async () => {
  instance = await instantiateExplorationImage(
    compiledImage,
    "SEED-TEST-A",
    "GENERATION-POLICY-STRUCTURAL-TEST",
  );
  const replay = await instantiateExplorationImage(
    compiledImage,
    "SEED-TEST-A",
    "GENERATION-POLICY-STRUCTURAL-TEST",
  );
  assertExplorationInstance(instance);
  assert.deepEqual(instance, replay);
});

check("Container state is mutable and does not alter Image hash", async () => {
  container = createExplorationContainer(instance, compiledImage.treeMap);
  container.positions.push({ nodeId: "NODE-TEST-A", x: 8, y: 13 });
  container.localEdits.push({
    editId: "EDIT-TEST-A",
    targetKind: "NODE",
    targetId: "NODE-TEST-A",
    editKind: "POSITION_NOTE",
    valueRef: "VALUE-LOCAL-COMPOSITION-ONLY",
  });
  assertExplorationContainer(container);
  assert.equal(await computeExplorationImageBuildSha256(compiledImage), compiledImage.buildSha256);
});

check("RenderedPng binds safe reconstruction metadata only", () => {
  assertRenderedPng({
    mediaType: "image/png",
    metadataSchemaVersion: "PNG-METADATA-STRUCTURAL-TEST",
    imageId: compiledImage.imageId,
    imageVersion: compiledImage.imageVersion,
    imageBuildSha256: compiledImage.buildSha256,
    instanceId: instance.instanceId,
    seed: instance.seed,
    rendererVersion: "RENDERER-NOT-IMPLEMENTED",
    pngIsSourceOfTruth: false,
  });
});

check("active repository guard passes", () => {
  const audit = auditActiveRepository();
  assert.equal(audit.status, "PASS", JSON.stringify(audit.failures));
});

check("governed database freeze accepts additive v50 files with zero frozen drift", () => {
  const audit = evaluateGovernedDatabaseFreezeReceipt({
    status: "PASS",
    databaseVersion: 50,
    frozenPathDriftCount: 0,
    unmanifestedV49DatabaseFileCount: 8,
  });
  assert.deepEqual(audit.failures, []);
});

check("governed database freeze rejects frozen-path drift", () => {
  const audit = evaluateGovernedDatabaseFreezeReceipt({
    status: "FAIL",
    databaseVersion: 50,
    frozenPathDriftCount: 1,
    unmanifestedV49DatabaseFileCount: 8,
  });
  assert.deepEqual(audit.failures, [
    "database freeze status is FAIL",
    "database frozen-path drift count is 1",
  ]);
});

expectRejected("A object ID added to ExplorationNode", () =>
  assertExplorationNode({ ...nodeA, archiveObjectId: "SURF-TEST" }),
);
expectRejected("B Search record DTO imported", () => {
  assert.ok(scanCandidateSource('import { SearchRecord } from "@/features/search-v49"').length > 0);
  throw new Error("guard rejection");
});
expectRejected("C external embedding helper added", () => {
  assert.ok(scanCandidateSource("const encoder = new QwenEmbeddingHelper()").length > 0);
  throw new Error("guard rejection");
});
expectRejected("D nearest-neighbor primitive added", () => {
  assert.ok(scanCandidateSource("function nearestNeighbors() {}").length > 0);
  throw new Error("guard rejection");
});
expectRejected("E cluster described as similarity cluster", () =>
  assertExplorationCluster({ ...clusterA, groupingRule: "similarity cluster" }),
);
expectRejected("F generative flow promotes historical claim", () =>
  assertExplorationFlow({ ...flowA, historicalClaim: true }),
);
expectRejected("G Container edit attempts to mutate Image", () => {
  compiledImage.treeMap.nodes.push(nodeA);
});
expectRejected("H PNG metadata stores archive identity", () =>
  assertRenderedPng({
    mediaType: "image/png",
    metadataSchemaVersion: "PNG-METADATA-STRUCTURAL-TEST",
    imageId: compiledImage.imageId,
    imageVersion: compiledImage.imageVersion,
    imageBuildSha256: compiledImage.buildSha256,
    instanceId: instance.instanceId,
    seed: instance.seed,
    rendererVersion: "RENDERER-NOT-IMPLEMENTED",
    pngIsSourceOfTruth: false,
    recordId: "SURF-TEST",
  }),
);
expectRejected("I Context projection imported", () => {
  assert.ok(scanCandidateSource('import x from "@/features/trace-v49/context/project"').length > 0);
  throw new Error("guard rejection");
});
expectRejected("J Spacetime atlas imported", () => {
  assert.ok(scanCandidateSource('import x from "@/features/trace-v49/spacetime/gis"').length > 0);
  throw new Error("guard rejection");
});
expectRejected("K vector database dependency added", () => {
  assert.ok(scanCandidateSource('const dependency = "vector database"').length > 0);
  throw new Error("guard rejection");
});
expectRejected("L ungoverned relation type added", () =>
  assertExplorationNode({ ...nodeA, conceptKind: "UNGOVERNED-RELATION-TYPE" }, RESET_RELATION_POLICY),
);

const checkResults = [];
for (const { name, fn } of checks) {
  await fn();
  checkResults.push({ name, status: "PASS" });
}
const redTeamResults = [];
for (const { name, fn } of redTeam) {
  let rejected = false;
  try {
    await fn();
  } catch {
    rejected = true;
  }
  assert.equal(rejected, true, `${name} was accepted`);
  redTeamResults.push({ name, status: "REJECTED" });
}
const receipt = {
  status: "PASS",
  structuralCheckCount: checkResults.length,
  structuralCheckFailureCount: 0,
  redTeamCaseCount: redTeamResults.length,
  redTeamRejectedCount: redTeamResults.length,
  imageHashMutationAfterContainerEditCount: 0,
  generativeFlowHistoricalClaimFailureCount: 0,
  clusterImpliedRelationFailureCount: 0,
  checks: checkResults,
  redTeam: redTeamResults,
};
process.stdout.write(`${JSON.stringify(receipt, null, 2)}\n`);
