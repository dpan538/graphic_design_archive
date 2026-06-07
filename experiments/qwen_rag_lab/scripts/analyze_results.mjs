#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const labRoot = path.resolve(import.meta.dirname, "..");
const reportPath = process.argv[2]
  ? path.resolve(process.argv[2])
  : path.join(labRoot, "reports/benchmark_baseline_v0.json");

const report = JSON.parse(fs.readFileSync(reportPath, "utf8"));
const variants = report.summary.variants;

console.log("Qwen RAG lab benchmark summary");
console.log(`records=${report.summary.recordCount} queries=${report.summary.queryCount} runs=${report.summary.runCount}`);
for (const variant of variants) {
  console.log(`${variant.variantId}: avgPromptTokens=${variant.avgPromptTokensEst}, avgRetrievalMs=${variant.avgRetrievalMs}, sourceRights=${variant.sourceRightsPreservedRate}, refusal=${variant.refusalCorrectRate}`);
}
