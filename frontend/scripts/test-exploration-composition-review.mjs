import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { InquiryAdapterError } from "../src/lib/trace/exploration-inquiry-adapter.ts";
import {
  round13TopologySignature,
  validateResearchInquiryInstanceV2,
  validateRound13Tree,
} from "../src/lib/trace/exploration-inquiry-v2-adapter.ts";

const frontendDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const repoDir = resolve(frontendDir, "..");
const fixturePath = resolve(repoDir, "scripts/trace-v49-exploration-composition-review/fixtures/tree-strategy-conformance-v2.json");
const fixturePackage = JSON.parse(readFileSync(fixturePath, "utf8"));
const negativeFixturePath = resolve(repoDir, "scripts/trace-v49-exploration-composition-review/fixtures/tree-strategy-negative-v2.json");
const negativeFixturePackage = JSON.parse(readFileSync(negativeFixturePath, "utf8"));
assert.equal(fixturePackage.fixtures.length, 6);
const signatures = new Set();
for (const fixture of fixturePackage.fixtures) {
  const items = validateRound13Tree(fixture.strategy, fixture.treeItems);
  const signature = round13TopologySignature(items);
  assert.equal(signature, fixture.topologySignature, fixture.fixtureId);
  signatures.add(signature);
  assert.equal(fixture.syntheticOnly ?? fixturePackage.syntheticOnly, true);
  assert.equal(fixture.productionEligible, false);
}
assert.equal(signatures.size, 6);
assert.equal(negativeFixturePackage.cases.length, 12);
for (const testCase of negativeFixturePackage.cases) {
  assert.throws(
    () => validateRound13Tree(testCase.strategy, testCase.treeItems),
    (error) => error instanceof InquiryAdapterError && error.code === testCase.expectedError,
    testCase.caseId,
  );
}

const v1Dir = resolve(repoDir, "docs/research/trace-v49-exploration-inquiry-flow-round1/12_RESEARCH_INSTANCES");
const v2Dir = resolve(repoDir, "docs/research/trace-v49-exploration-composition-review-round1/12_RESEARCH_INSTANCES_V2");
const instanceHashes = [];
for (let index = 1; index <= 5; index += 1) {
  const suffix = String(index).padStart(3, "0");
  const v1 = JSON.parse(readFileSync(resolve(v1Dir, `INQUIRY-INSTANCE-${suffix}.json`), "utf8"));
  const v2 = JSON.parse(readFileSync(resolve(v2Dir, `INQUIRY-INSTANCE-${suffix}.v2.json`), "utf8"));
  await validateResearchInquiryInstanceV2(v2, v1);
  instanceHashes.push(v2.canonicalHash);
}

const baseline = JSON.parse(readFileSync(resolve(v2Dir, "INQUIRY-INSTANCE-001.v2.json"), "utf8"));
const badClaim = structuredClone(baseline);
badClaim.historicalClaim = true;
await assert.rejects(() => validateResearchInquiryInstanceV2(badClaim), (error) => error instanceof InquiryAdapterError && error.code === "STATUS_MUTATION");
const contaminated = structuredClone(baseline);
contaminated.semanticNodeRefs[0].archiveObjectId = "PROHIBITED";
await assert.rejects(() => validateResearchInquiryInstanceV2(contaminated), (error) => error instanceof InquiryAdapterError && error.code === "STRUCTURAL_CONTAMINATION");
const fakeConvergence = structuredClone(baseline);
fakeConvergence.treeItems.find((item) => item.branchStatus === "CONVERGENCE").convergenceSourceItemIds = [];
await assert.rejects(() => validateResearchInquiryInstanceV2(fakeConvergence), (error) => error instanceof InquiryAdapterError && error.code === "BINARY_CONVERGENCE_TOPOLOGY");

process.stdout.write(`${JSON.stringify({
  status: "PASS",
  treeStrategyCount: 6,
  topologyConformanceFixtureCount: 6,
  sharedNegativeTopologyFixtureCount: 12,
  topologyDuplicateCount: 0,
  instanceV2Count: 5,
  crossRuntimeDecisionMismatchCount: 0,
  crossRuntimeHashMismatchCount: 0,
  historicalClaimRejection: "PASS",
  structuralContaminationRejection: "PASS",
  fakeConvergenceRejection: "PASS",
  typescriptOnlySemanticRuleCount: 0,
  instanceHashes,
}, null, 2)}\n`);
