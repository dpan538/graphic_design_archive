import assert from "node:assert/strict";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
  CompositionAdapterError,
  validateRound15CompositionAudit,
} from "../src/lib/trace/exploration-composition-adapter.ts";
import { renderRound15ResearchSvg } from "../src/lib/trace/exploration-composition-research-renderer.ts";

const frontendDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const repoDir = resolve(frontendDir, "..");
const auditDir = resolve(repoDir, "docs/audits/v49-exploration-composition-engine-round1");
const rawDir = resolve(auditDir, "raw");
const snapshotDir = resolve(auditDir, "snapshots");
const round15Path = resolve(rawDir, "composition-decision-audit.json");
const round14Path = resolve(repoDir, "scripts/trace-v49-exploration-association-calibration/fixtures/association-assessments-v1.json");
const pkg = JSON.parse(readFileSync(round15Path, "utf8"));
const round14 = JSON.parse(readFileSync(round14Path, "utf8"));
const parity = await validateRound15CompositionAudit(pkg, round14);
assert.equal(parity.crossRuntimeDecisionMismatchCount, 0);
assert.equal(parity.crossRuntimeHashMismatchCount, 0);
assert.equal(parity.typescriptOnlySemanticRuleCount, 0);

const badHash = structuredClone(pkg);
badHash.images[0].semantic_core.topology_type = "UNRESOLVED";
await assert.rejects(
  () => validateRound15CompositionAudit(badHash, round14),
  (error) => error instanceof CompositionAdapterError && error.code === "PACKAGE_HASH_MISMATCH",
);
const leakedControl = structuredClone(pkg);
const control = leakedControl.images.find((image) => image.composition_core.candidate_decisions.some((candidate) => candidate.semantic_eligibility === "NOT_QUALIFIED"));
const controlCandidate = control.composition_core.candidate_decisions.find((candidate) => candidate.semantic_eligibility === "NOT_QUALIFIED");
controlCandidate.decision_state = "ADMITTED";
control.semantic_core.admitted_association_ids.push(controlCandidate.assessment_id);
await assert.rejects(
  () => validateRound15CompositionAudit(leakedControl, round14),
  (error) => error instanceof CompositionAdapterError && error.code === "PACKAGE_HASH_MISMATCH",
);

mkdirSync(snapshotDir, { recursive: true });
const representativeIds = [
  "R15-COMP-001", "R15-COMP-002", "R15-COMP-004", "R15-COMP-009",
  "R15-COMP-010", "R15-COMP-011", "R15-COMP-018", "R15-COMP-020",
];
for (const fixtureId of representativeIds) {
  const image = pkg.images.find((item) => item.audit.fixture_id === fixtureId);
  assert.ok(image, `missing ${fixtureId}`);
  const svg = renderRound15ResearchSvg(image);
  assert.equal(svg.includes("marker-end"), false);
  assert.equal(svg.includes("stroke-width=\"3\""), false);
  assert.equal(svg.includes("data-internal-research-only=\"true\""), true);
  writeFileSync(resolve(snapshotDir, `${fixtureId}.svg`), `${svg}\n`, "utf8");
}

const receipt = {
  status: "PASS",
  imageCount: parity.imageCount,
  renderedSnapshotCount: representativeIds.length,
  crossRuntimeDecisionMismatchCount: parity.crossRuntimeDecisionMismatchCount,
  crossRuntimeHashMismatchCount: parity.crossRuntimeHashMismatchCount,
  typescriptOnlySemanticRuleCount: parity.typescriptOnlySemanticRuleCount,
  pythonNormative: true,
  typescriptNormativeSemanticEngine: false,
  publicRouteAdded: false,
  publicApiAdded: false,
};
writeFileSync(resolve(rawDir, "cross-runtime-composition-audit.json"), `${JSON.stringify(receipt, null, 2)}\n`, "utf8");
process.stdout.write(`${JSON.stringify(receipt, null, 2)}\n`);
