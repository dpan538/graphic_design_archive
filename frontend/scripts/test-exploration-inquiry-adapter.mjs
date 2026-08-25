import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
  InquiryAdapterError,
  canonicalSerializeInquiryValue,
  hashInquiryValue,
  validateCandidateFreeze,
  validateConformanceArtifact,
} from "../src/lib/trace/exploration-inquiry-adapter.ts";
import { createExplorationConstraintPackage } from "../src/lib/trace/exploration-build-contract.ts";
import { compileConstrainedExplorationImage } from "../src/lib/trace/exploration-image-compiler.ts";
import {
  createSyntheticBuildRequest,
  createSyntheticFixturePackage,
  syntheticConstraintInput,
} from "./fixtures/exploration-constraint-kernel-synthetic-fixtures.ts";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const fixturePath = resolve(scriptDir, "../../scripts/trace-v49-exploration-inquiry-engine/fixtures/cross-runtime-fixtures.json");
const fixtures = JSON.parse(readFileSync(fixturePath, "utf8")).fixtures;
const results = [];

for (const fixture of fixtures) {
  let accepted = true;
  let failureCode = "";
  try {
    await validateConformanceArtifact(fixture.kind, fixture.value);
  } catch (error) {
    accepted = false;
    failureCode = error instanceof InquiryAdapterError ? error.code : "UNEXPECTED_ERROR";
  }
  assert.equal(accepted, fixture.expectedAccepted, fixture.fixtureId);
  assert.equal(failureCode, fixture.expectedFailureCode, fixture.fixtureId);
  if (accepted) {
    let hashInput = fixture.value;
    if (fixture.kind === "FREEZE" || fixture.kind === "INSTANCE") {
      const { canonicalHash: _canonicalHash, ...unsigned } = fixture.value;
      hashInput = unsigned;
    }
    assert.equal(await hashInquiryValue(hashInput), fixture.expectedCanonicalHash, fixture.fixtureId);
  }
  results.push({ fixtureId: fixture.fixtureId, accepted, failureCode, status: "PASS" });
}

const freezeFixture = fixtures.find((fixture) => fixture.kind === "FREEZE" && fixture.expectedAccepted);
const reorderedFreeze = structuredClone(freezeFixture.value);
reorderedFreeze.candidates.reverse();
await validateCandidateFreeze(reorderedFreeze);
assert.equal(reorderedFreeze.canonicalHash, freezeFixture.value.canonicalHash);

const orderedA = { treeItems: [{ itemId: "A" }, { itemId: "B" }] };
const orderedB = { treeItems: [{ itemId: "B" }, { itemId: "A" }] };
assert.notEqual(canonicalSerializeInquiryValue(orderedA), canonicalSerializeInquiryValue(orderedB));
assert.throws(() => canonicalSerializeInquiryValue({ undeclaredArray: ["B", "A"] }), (error) => error instanceof InquiryAdapterError && error.code === "UNKNOWN_ARRAY_ORDER");

const syntheticPackage = await createSyntheticFixturePackage();
const baseline = createSyntheticBuildRequest(syntheticPackage.buildSha256);
async function expectKernelCode(mutate, code) {
  const request = structuredClone(baseline);
  mutate(request);
  const receipt = await compileConstrainedExplorationImage(syntheticPackage, request);
  assert.equal(receipt.buildStatus, "REJECTED");
  assert.ok(receipt.failureCodes.includes(code), JSON.stringify(receipt));
}

await expectKernelCode((request) => { request.requestedNodes[0].recordUrl = "/archive/prohibited"; }, "ARCHIVE_OBJECT_CONTAMINATION");
await expectKernelCode((request) => { request.requestedNodes[0].context.contextDTO = "prohibited"; }, "CONTEXT_CONTAMINATION");
await expectKernelCode((request) => { request.requestedNodes[0].context.spacetimeDTO = "prohibited"; }, "SPACETIME_CONTAMINATION");
await expectKernelCode((request) => { request.requestedNodes[0].context.modelId = "external-model"; }, "EXTERNAL_MODEL_CONTAMINATION");
await expectKernelCode((request) => { request.unexpected = true; }, "UNKNOWN_FIELD");
await expectKernelCode((request) => { request.requestedFlows[1].flowId = request.requestedFlows[0].flowId; }, "DUPLICATE_ID");
await expectKernelCode((request) => { request.requestedFlows[0].sourceNodeConceptId = "NODE-MISSING"; }, "DANGLING_REFERENCE");
await expectKernelCode((request) => { request.requestedFlows[0].origin = "USER_COMPOSED"; }, "ORIGIN_POLICY_VIOLATION");

const duplicateQualificationInput = structuredClone(syntheticConstraintInput);
duplicateQualificationInput.qualificationPolicies.push(structuredClone(duplicateQualificationInput.qualificationPolicies[0]));
duplicateQualificationInput.qualificationPolicies[1].qualificationPolicyId = "QUALIFICATION-POLICY-TEST-B";
const duplicateQualificationPackage = await createExplorationConstraintPackage(duplicateQualificationInput);
const duplicateQualificationReceipt = await compileConstrainedExplorationImage(duplicateQualificationPackage, createSyntheticBuildRequest(duplicateQualificationPackage.buildSha256));
assert.equal(duplicateQualificationReceipt.buildStatus, "REJECTED");
assert.ok(duplicateQualificationReceipt.failureCodes.includes("DUPLICATE_QUALIFICATION_KEY"));

process.stdout.write(`${JSON.stringify({
  status: "PASS",
  crossRuntimeFixtureCount: fixtures.length,
  crossRuntimeDecisionMismatchCount: 0,
  crossRuntimeHashMismatchCount: 0,
  unknownFieldRejection: "PASS",
  duplicateIdRejection: "PASS",
  danglingReferenceRejection: "PASS",
  undeclaredArchiveContaminationRejection: "PASS",
  undeclaredContextContaminationRejection: "PASS",
  undeclaredSpacetimeContaminationRejection: "PASS",
  undeclaredModelContaminationRejection: "PASS",
  originPolicyEnforcement: "PASS",
  schemaAwareCanonicalization: "PASS",
  results,
}, null, 2)}\n`);
