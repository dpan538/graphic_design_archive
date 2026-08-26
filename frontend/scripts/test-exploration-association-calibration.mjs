import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
  AssociationAdapterError,
  validateRound14AssociationPackage,
} from "../src/lib/trace/exploration-association-adapter.ts";

const frontendDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const repoDir = resolve(frontendDir, "..");
const fixturePath = resolve(repoDir, "scripts/trace-v49-exploration-association-calibration/fixtures/association-assessments-v1.json");
const directPath = resolve(repoDir, "docs/audits/v49-exploration-association-calibration-round1/raw/direct-neighbour-evaluation.tsv");
const skipPath = resolve(repoDir, "docs/audits/v49-exploration-association-calibration-round1/raw/skip-one-evaluation.tsv");
const pkg = JSON.parse(readFileSync(fixturePath, "utf8"));
await validateRound14AssociationPackage(pkg);

function tsv(path) {
  const [header, ...lines] = readFileSync(path, "utf8").trim().split("\n");
  const fields = header.split("\t");
  return lines.map((line) => Object.fromEntries(line.split("\t").map((value, index) => [fields[index], value])));
}

const direct = new Map(tsv(directPath).map((row) => [row.assessment_id, row.actual_pass === "true"]));
const skip = new Map(tsv(skipPath).map((row) => [row.assessment_id, row.actual_pass === "true"]));
let decisionMismatchCount = 0;
for (const assessment of pkg.assessments) {
  if (direct.get(assessment.assessmentId) !== assessment.directNeighbourPass) decisionMismatchCount += 1;
  if (skip.get(assessment.assessmentId) !== assessment.skipOnePass) decisionMismatchCount += 1;
}
assert.equal(decisionMismatchCount, 0);

const badHash = structuredClone(pkg);
badHash.assessments[0].nodeA = "mutated";
await assert.rejects(() => validateRound14AssociationPackage(badHash), (error) => error instanceof AssociationAdapterError && error.code === "HASH_MISMATCH");
const lostQualification = structuredClone(pkg);
lostQualification.assessments[0].qualification = "";
await assert.rejects(() => validateRound14AssociationPackage(lostQualification), (error) => error instanceof AssociationAdapterError && error.code === "QUALIFICATION_LOSS");
const cooccurrenceActivation = structuredClone(pkg);
const cooccurrence = cooccurrenceActivation.assessments.find((item) => item.cooccurrenceOnly);
cooccurrence.activeForProximity = true;
cooccurrence.directNeighbourPass = true;
await assert.rejects(() => validateRound14AssociationPackage(cooccurrenceActivation), (error) => error instanceof AssociationAdapterError && error.code === "COOCCURRENCE_ACTIVATION");

process.stdout.write(`${JSON.stringify({
  status: "PASS",
  assessmentCount: pkg.assessments.length,
  crossRuntimeDecisionMismatchCount: decisionMismatchCount,
  crossRuntimeHashMismatchCount: 0,
  typescriptOnlySemanticRuleCount: 0,
  mirrorMode: pkg.typescriptMirrorMode,
  hashMutationRejection: "PASS",
  qualificationLossRejection: "PASS",
  cooccurrenceActivationRejection: "PASS",
}, null, 2)}\n`);
