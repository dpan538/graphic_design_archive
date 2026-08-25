import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { performance } from "node:perf_hooks";

import {
  createExplorationConstraintPackage,
  sha256ConstraintValue,
} from "../src/lib/trace/exploration-build-contract.ts";
import { evaluateExplorationConstraints } from "../src/lib/trace/exploration-constraint-kernel.ts";
import {
  applySyntheticContainerEdit,
  compileConstrainedExplorationImage,
  createSyntheticExplorationContainer,
  instantiateSyntheticExplorationImage,
  verifyCompiledExplorationImageHash,
} from "../src/lib/trace/exploration-image-compiler.ts";
import {
  createCurrentRealBuildRequest,
  createSyntheticBuildRequest,
  createSyntheticFixturePackage,
  createUnresolvedRealFixturePackage,
  syntheticConstraintInput,
} from "./fixtures/exploration-constraint-kernel-synthetic-fixtures.ts";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(scriptDir, "..");
const productionTraceRoot = join(frontendRoot, "src/lib/trace");
const syntheticFixtureName = "exploration-constraint-kernel-synthetic-fixtures";
const roundResearchLabels = [
  "mediation",
  "canonization",
  "professionalization",
  "institutionalization",
  "transnational interactions",
  "cultural translation",
  "design exchanges",
  "commodification",
  "gendering",
  "displacement",
  "transculturation",
  "cultural mobility",
  "self-exoticization",
  "coloniality",
  "imitation",
  "piracy",
];

function walk(path) {
  const entries = [];
  for (const name of readdirSync(path).sort()) {
    const candidate = join(path, name);
    if (statSync(candidate).isDirectory()) entries.push(...walk(candidate));
    else entries.push(candidate);
  }
  return entries;
}

function clone(value) {
  return structuredClone(value);
}

async function expectRejectedWith(receiptPromise, expectedCode) {
  const receipt = await receiptPromise;
  assert.equal(receipt.buildStatus, "REJECTED");
  assert.ok(receipt.failureCodes.includes(expectedCode), JSON.stringify(receipt));
  assert.equal("image" in receipt, false);
  return receipt;
}

const suiteStart = performance.now();
const packageStart = performance.now();
const syntheticPackage = await createSyntheticFixturePackage();
const unresolvedRealPackage = await createUnresolvedRealFixturePackage();
const constraintPackageValidationMs = performance.now() - packageStart;
const syntheticRequest = createSyntheticBuildRequest(syntheticPackage.buildSha256);
const realRequest = createCurrentRealBuildRequest(unresolvedRealPackage.buildSha256);

const cases = [];
async function runCase(id, name, fn) {
  const started = performance.now();
  await fn();
  cases.push({ id, name, status: "PASS", durationMs: +(performance.now() - started).toFixed(3) });
}

await runCase("A", "UNRESOLVED vocabulary rejects real build", async () => {
  await expectRejectedWith(
    compileConstrainedExplorationImage(unresolvedRealPackage, realRequest),
    "NO_ACTIVE_VOCABULARY",
  );
});

await runCase("B", "RESEARCH_CANDIDATE_ONLY node rejects", async () => {
  const input = clone(syntheticConstraintInput);
  input.nodePolicies[0].activationState = "RESEARCH_CANDIDATE_ONLY";
  const candidatePackage = await createExplorationConstraintPackage(input);
  const request = createSyntheticBuildRequest(candidatePackage.buildSha256);
  await expectRejectedWith(
    compileConstrainedExplorationImage(candidatePackage, request),
    "RESEARCH_ONLY_NODE",
  );
});

await runCase("C", "unknown pair default denies", async () => {
  const request = clone(syntheticRequest);
  request.requestedFlows[0].pairPolicyId = "PAIR-POLICY-UNKNOWN";
  await expectRejectedWith(
    compileConstrainedExplorationImage(syntheticPackage, request),
    "UNAUTHORIZED_PAIR",
  );
});

await runCase("D", "deferred pair rejects", async () => {
  const request = clone(syntheticRequest);
  request.requestedFlows = [{
    ...request.requestedFlows[2],
    flowId: "FLOW-TEST-DEFER",
    pairPolicyId: "PAIR-POLICY-TEST-DEFER",
    qualifications: {},
  }];
  request.requestedClusters = [];
  request.requestedChains = [];
  await expectRejectedWith(
    compileConstrainedExplorationImage(syntheticPackage, request),
    "DEFERRED_PAIR",
  );
});

await runCase("E", "wrong direction rejects", async () => {
  const request = clone(syntheticRequest);
  request.requestedFlows[0].directionality = "RECIPROCAL";
  await expectRejectedWith(
    compileConstrainedExplorationImage(syntheticPackage, request),
    "DIRECTIONALITY_NOT_AUTHORIZED",
  );
});

let baselineReceipt;
let syntheticCompileMs = 0;
await runCase("F", "authorized directed reciprocal qualified synthetic compile passes", async () => {
  const started = performance.now();
  baselineReceipt = await compileConstrainedExplorationImage(syntheticPackage, syntheticRequest);
  syntheticCompileMs = performance.now() - started;
  assert.equal(baselineReceipt.buildStatus, "COMPILED_SYNTHETIC_TEST_ONLY");
  assert.equal(await verifyCompiledExplorationImageHash(baselineReceipt.image), true);
  assert.equal(baselineReceipt.image.topology.flows.length, 3);
});

await runCase("G", "reciprocal pair cannot become one-way", async () => {
  const request = clone(syntheticRequest);
  request.requestedFlows[1].directionality = "DIRECTED";
  await expectRejectedWith(
    compileConstrainedExplorationImage(syntheticPackage, request),
    "DIRECTIONALITY_NOT_AUTHORIZED",
  );
});

await runCase("H", "structural condition cannot become binary Flow", async () => {
  const request = clone(syntheticRequest);
  request.requestedFlows = [{
    flowId: "FLOW-TEST-STRUCTURAL",
    pairPolicyId: "PAIR-POLICY-TEST-STRUCTURAL",
    sourceNodeConceptId: "NODE-TEST-B",
    targetNodeConceptId: "NODE-TEST-A",
    directionality: "DIRECTED",
    sourceRole: "bounded synthetic participant role",
    targetRole: "bounded synthetic target role",
    origin: "EVIDENCE_BACKED",
    qualifications: {},
    provenanceRef: "PROVENANCE-FLOW-TEST-STRUCTURAL",
  }];
  request.requestedClusters = [];
  request.requestedChains = [];
  await expectRejectedWith(
    compileConstrainedExplorationImage(syntheticPackage, request),
    "DIRECTIONALITY_NOT_AUTHORIZED",
  );
});

await runCase("I", "universal ANY role rejects", async () => {
  const input = clone(syntheticConstraintInput);
  input.nodePolicies[0].subjectRole = "ANY";
  const candidatePackage = await createExplorationConstraintPackage(input);
  const request = createSyntheticBuildRequest(candidatePackage.buildSha256);
  await expectRejectedWith(
    compileConstrainedExplorationImage(candidatePackage, request),
    "UNBOUNDED_ARGUMENT_ROLE",
  );
});

await runCase("J", "required qualification drop rejects", async () => {
  const request = clone(syntheticRequest);
  request.requestedFlows[2].qualifications = {};
  await expectRejectedWith(
    compileConstrainedExplorationImage(syntheticPackage, request),
    "REQUIRED_QUALIFICATION_MISSING",
  );
  const nodeRequest = clone(syntheticRequest);
  nodeRequest.requestedNodes[2].qualifications = {};
  await expectRejectedWith(
    compileConstrainedExplorationImage(syntheticPackage, nodeRequest),
    "REQUIRED_QUALIFICATION_MISSING",
  );
});

await runCase("K", "unauthorized Cluster rejects", async () => {
  const request = clone(syntheticRequest);
  request.requestedClusters[0].clusterPolicyId = "CLUSTER-POLICY-UNKNOWN";
  await expectRejectedWith(
    compileConstrainedExplorationImage(syntheticPackage, request),
    "UNAUTHORIZED_CLUSTER",
  );
  const mismatchedMembership = clone(syntheticRequest);
  mismatchedMembership.requestedClusters[0].flowIds = ["FLOW-TEST-A", "FLOW-TEST-B"];
  await expectRejectedWith(
    compileConstrainedExplorationImage(syntheticPackage, mismatchedMembership),
    "UNAUTHORIZED_CLUSTER",
  );
});

await runCase("L", "unauthorized transitive chain rejects", async () => {
  const request = clone(syntheticRequest);
  request.requestedChains[0].chainPolicyId = "CHAIN-POLICY-UNKNOWN";
  await expectRejectedWith(
    compileConstrainedExplorationImage(syntheticPackage, request),
    "TRANSITIVE_INFERENCE_PROHIBITED",
  );
  const mismatchedChain = clone(syntheticRequest);
  mismatchedChain.requestedChains[0].orderedFlowIds = ["FLOW-TEST-A", "FLOW-TEST-C"];
  await expectRejectedWith(
    compileConstrainedExplorationImage(syntheticPackage, mismatchedChain),
    "TRANSITIVE_INFERENCE_PROHIBITED",
  );
});

const contaminationCases = [
  ["M", "ARCHIVE_OBJECT", "ARCHIVE_OBJECT_CONTAMINATION"],
  ["N", "CONTEXT_PAYLOAD", "CONTEXT_CONTAMINATION"],
  ["O", "SPACETIME_PAYLOAD", "SPACETIME_CONTAMINATION"],
  ["P", "EXTERNAL_MODEL_PROVENANCE", "EXTERNAL_MODEL_CONTAMINATION"],
];
for (const [id, kind, failureCode] of contaminationCases) {
  await runCase(id, `${kind} contamination rejects`, async () => {
    const request = clone(syntheticRequest);
    request.forbiddenInputKinds = [kind];
    await expectRejectedWith(
      compileConstrainedExplorationImage(syntheticPackage, request),
      failureCode,
    );
  });
}

let instance;
let container;
await runCase("Q", "Container mutation leaves Image hash unchanged", async () => {
  instance = await instantiateSyntheticExplorationImage(
    baselineReceipt.image,
    "GENERATION-POLICY-TEST-V1",
  );
  container = createSyntheticExplorationContainer(instance, baselineReceipt.image);
  const before = baselineReceipt.image.imageHash;
  container.positions.push({ nodeConceptId: "NODE-TEST-A", x: 8, y: 13 });
  applySyntheticContainerEdit(container, baselineReceipt.image, {
    editId: "EDIT-TEST-A",
    targetId: "NODE-TEST-A",
    editKind: "LOCAL-NOTE",
    value: "SYNTHETIC-LOCAL-ONLY",
  });
  assert.equal(baselineReceipt.image.imageHash, before);
  assert.equal(await verifyCompiledExplorationImageHash(baselineReceipt.image), true);
  assert.throws(() =>
    applySyntheticContainerEdit(container, baselineReceipt.image, {
      editId: "EDIT-TEST-UNAUTHORIZED",
      targetId: "NODE-TEST-UNKNOWN",
      editKind: "ACTIVATE",
      value: true,
    }),
  );
  const mismatchedInstance = clone(instance);
  mismatchedInstance.baseImageBuildSha256 = "0".repeat(64);
  assert.throws(() => createSyntheticExplorationContainer(mismatchedInstance, baselineReceipt.image));
  const mismatchedContainer = clone(container);
  mismatchedContainer.imageHash = "0".repeat(64);
  assert.throws(() =>
    applySyntheticContainerEdit(mismatchedContainer, baselineReceipt.image, {
      editId: "EDIT-TEST-WRONG-IMAGE",
      targetId: "NODE-TEST-A",
      editKind: "ACTIVATE",
      value: true,
    }),
  );
});

let replayReceipt;
await runCase("R", "same synthetic request replays identical Image hash", async () => {
  replayReceipt = await compileConstrainedExplorationImage(
    syntheticPackage,
    clone(syntheticRequest),
  );
  assert.equal(replayReceipt.buildStatus, "COMPILED_SYNTHETIC_TEST_ONLY");
  assert.equal(replayReceipt.imageHash, baselineReceipt.imageHash);
  assert.deepEqual(replayReceipt.image.authorizationReceipt, baselineReceipt.image.authorizationReceipt);
});

let alternateSeedReceipt;
await runCase("S", "seed changes layout choice only, never authorization", async () => {
  const request = clone(syntheticRequest);
  request.seed = "SEED-TEST-B";
  alternateSeedReceipt = await compileConstrainedExplorationImage(syntheticPackage, request);
  assert.equal(alternateSeedReceipt.buildStatus, "COMPILED_SYNTHETIC_TEST_ONLY");
  assert.deepEqual(
    alternateSeedReceipt.image.authorizationReceipt,
    baselineReceipt.image.authorizationReceipt,
  );
  assert.notEqual(alternateSeedReceipt.image.layoutChoice, baselineReceipt.image.layoutChoice);
});

let currentRealReceipt;
await runCase("T", "current real semantic build rejects atomically", async () => {
  currentRealReceipt = await compileConstrainedExplorationImage(
    unresolvedRealPackage,
    realRequest,
  );
  assert.equal(currentRealReceipt.buildStatus, "REJECTED");
  for (const required of [
    "NO_ACTIVE_VOCABULARY",
    "NO_ACTIVE_GRAMMAR",
    "NO_AUTHORIZED_PAIR_RULES",
  ]) assert.ok(currentRealReceipt.failureCodes.includes(required));
  assert.equal("image" in currentRealReceipt, false);
});

const mutationCases = [
  ["activation state", async () => {
    const input = clone(syntheticConstraintInput);
    input.nodePolicies[0].activationState = "UNRESOLVED";
    const pkg = await createExplorationConstraintPackage(input);
    return [pkg, createSyntheticBuildRequest(pkg.buildSha256), "UNRESOLVED_NODE"];
  }],
  ["pair decision", async () => {
    const input = clone(syntheticConstraintInput);
    input.pairPolicies[0].decision = "DEFAULT_DENY";
    const pkg = await createExplorationConstraintPackage(input);
    return [pkg, createSyntheticBuildRequest(pkg.buildSha256), "UNAUTHORIZED_PAIR"];
  }],
  ["directionality", async () => {
    const request = clone(syntheticRequest);
    request.requestedFlows[0].directionality = "RECIPROCAL";
    return [syntheticPackage, request, "DIRECTIONALITY_NOT_AUTHORIZED"];
  }],
  ["qualification", async () => {
    const request = clone(syntheticRequest);
    request.requestedFlows[2].qualifications = {};
    return [syntheticPackage, request, "REQUIRED_QUALIFICATION_MISSING"];
  }],
  ["sense ID", async () => {
    const request = clone(syntheticRequest);
    request.requestedNodes[0].senseId = "SENSE-TEST-MUTATED";
    return [syntheticPackage, request, "SENSE_ID_MISMATCH"];
  }],
  ["constraint package hash", async () => {
    const request = clone(syntheticRequest);
    request.constraintPackageHash = "0".repeat(64);
    return [syntheticPackage, request, "PACKAGE_HASH_MISMATCH"];
  }],
  ["provenance reference", async () => {
    const request = clone(syntheticRequest);
    request.requestedFlows[0].provenanceRef = "";
    return [syntheticPackage, request, "PROVENANCE_MISSING"];
  }],
  ["synthetic flag", async () => {
    const request = clone(syntheticRequest);
    request.syntheticTestOnly = false;
    return [syntheticPackage, request, "SYNTHETIC_FLAG_MISMATCH"];
  }],
  ["node role", async () => {
    const request = clone(syntheticRequest);
    request.requestedNodes[0].technicalRole = "DIRECTED_PROCESS";
    return [syntheticPackage, request, "ROLE_MISMATCH"];
  }],
  ["cluster authorization", async () => {
    const request = clone(syntheticRequest);
    request.requestedClusters[0].clusterPolicyId = "CLUSTER-POLICY-MUTATED";
    return [syntheticPackage, request, "UNAUTHORIZED_CLUSTER"];
  }],
];

const mutationResults = [];
for (const [name, prepare] of mutationCases) {
  const [pkg, request, code] = await prepare();
  await expectRejectedWith(compileConstrainedExplorationImage(pkg, request), code);
  mutationResults.push({ name, status: "REJECTED" });
}

await runCase("ISOLATION", "synthetic fixtures are absent from production imports", async () => {
  const productionFiles = walk(productionTraceRoot).filter((path) => /\.(?:ts|tsx|js|mjs)$/.test(path));
  const fixtureImports = productionFiles.filter((path) =>
    readFileSync(path, "utf8").includes(syntheticFixtureName),
  );
  assert.deepEqual(fixtureImports, []);
  const compilerFiles = productionFiles.filter((path) =>
    path.includes("exploration-build-contract") ||
    path.includes("exploration-constraint-kernel") ||
    path.includes("exploration-image-compiler"),
  );
  const lower = compilerFiles.map((path) => readFileSync(path, "utf8").toLowerCase()).join("\n");
  assert.deepEqual(roundResearchLabels.filter((label) => lower.includes(label)), []);
  assert.equal(/docs\/research\/.+\.tsv|docs\/audits\/.+\.tsv/i.test(lower), false);
});

const hashStart = performance.now();
await sha256ConstraintValue(baselineReceipt.image);
const hashingMs = performance.now() - hashStart;
const suiteMs = performance.now() - suiteStart;

const receipt = {
  status: "PASS",
  compilerVersion: baselineReceipt.image.compilerVersion,
  requiredAdversarialCaseCount: 20,
  requiredAdversarialPassCount: 20,
  totalCheckCount: cases.length,
  failOpenMutationCount: 0,
  mutationCaseCount: mutationResults.length,
  currentRealBuildAttemptCount: 1,
  currentRealBuildSuccessCount: 0,
  currentRealBuildRejectionCount: 1,
  syntheticTestImageBuildCount: 3,
  syntheticTestImageBuildPass: true,
  syntheticInstanceCreation: "PASS",
  syntheticContainerLifecycle: "PASS",
  syntheticFixtureProductionImportCount: 0,
  realSemanticImageBuildCount: 0,
  realSemanticFlowBuildCount: 0,
  realSemanticClusterBuildCount: 0,
  realSemanticChainBuildCount: 0,
  syntheticBuildReplayCount: 2,
  syntheticBuildHashEquality: "PASS",
  imageImmutability: "PASS",
  imageHashMutationAfterContainerEditCount: 0,
  constraintPackageValidationMs: +constraintPackageValidationMs.toFixed(3),
  syntheticCompileMs: +syntheticCompileMs.toFixed(3),
  hashingMs: +hashingMs.toFixed(3),
  testSuiteMs: +suiteMs.toFixed(3),
  cases,
  mutationResults,
};

process.stdout.write(`${JSON.stringify(receipt, null, 2)}\n`);
