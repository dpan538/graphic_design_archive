#!/usr/bin/env node

import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const options = Object.fromEntries(process.argv.slice(2).reduce((pairs, value, index, values) => {
  if (index % 2 === 0) pairs.push([value.replace(/^--/u, "").replaceAll("-", "_"), values[index + 1]]);
  return pairs;
}, []));
const repo = path.resolve(options.repo ?? path.join(import.meta.dirname, "../.."));
const modelPath = path.join(repo, "frontend/generated/trace-exploration-v2/production-read-model.json");
const metadataPath = path.resolve(options.metadata ?? path.join(repo, "docs/audits/v49-exploration-full-space-closure-round1/raw/production-read-model-metadata-v2.json"));
const gcAvailable = typeof global.gc === "function";
if (gcAvailable) global.gc();
const before = process.memoryUsage();
const started = performance.now();
let source = await readFile(modelPath, "utf8");
const readFinished = performance.now();
const modelBytes = Buffer.byteLength(source, "utf8");
const modelSha256 = createHash("sha256").update(source).digest("hex");
const model = JSON.parse(source);
const parsed = performance.now();
source = undefined;
if (gcAvailable) global.gc();
const after = process.memoryUsage();
const metadata = JSON.parse(await readFile(metadataPath, "utf8"));
const mismatchCodes = [];
if (!gcAvailable) mismatchCodes.push("GC_NOT_EXPOSED");
if (model.transitions?.derivation_version !== "trace-exploration-derived-transitions-v2"
  || model.transitions?.key_format !== "state_hash|action|target"
  || !Number.isInteger(model.transitions?.transition_count)
  || model.transitions.transition_count < 1) mismatchCodes.push("TRANSITION_DERIVATION_DESCRIPTOR_INVALID");
if (metadata.production_read_model_bytes !== modelBytes) mismatchCodes.push("MODEL_BYTE_COUNT_MISMATCH");
if (metadata.production_read_model_sha256 !== modelSha256) mismatchCodes.push("MODEL_SHA256_MISMATCH");
for (const [metadataKey, actual] of [
  ["audit_state_count", Object.keys(model.states).length],
  ["audit_transition_count", model.transitions.transition_count],
  ["audit_workflow_count", model.capabilities.workflow_count],
  ["audit_export_variant_count", model.capabilities.export_variant_count],
]) {
  if (metadata[metadataKey] !== actual) mismatchCodes.push(`${metadataKey.toUpperCase()}_MISMATCH`);
}
const output = {
  schema_version: "trace-exploration-production-model-load-v2",
  status: mismatchCodes.length === 0 ? "PASS" : "FAIL",
  production_read_model_path: path.relative(repo, modelPath),
  production_read_model_bytes: modelBytes,
  production_read_model_sha256: modelSha256,
  gc_available: gcAvailable,
  file_read_ms: readFinished - started,
  json_parse_ms: parsed - readFinished,
  production_model_load_ms: parsed - started,
  rss_before_bytes: before.rss,
  rss_after_bytes: after.rss,
  rss_delta_bytes: after.rss - before.rss,
  heap_used_before_bytes: before.heapUsed,
  heap_used_after_bytes: after.heapUsed,
  heap_delta_bytes: after.heapUsed - before.heapUsed,
  heap_total_before_bytes: before.heapTotal,
  heap_total_after_bytes: after.heapTotal,
  heap_total_delta_bytes: after.heapTotal - before.heapTotal,
  external_before_bytes: before.external,
  external_after_bytes: after.external,
  external_delta_bytes: after.external - before.external,
  category_entry_count: model.categories.length,
  vocabulary_count: model.vocabulary.length,
  association_count: model.associations.length,
  production_composition_count: Object.keys(model.compositions).length,
  state_count: Object.keys(model.states).length,
  transition_count: model.transitions.transition_count,
  workflow_count: model.capabilities.workflow_count,
  export_variant_count: model.capabilities.export_variant_count,
  audit_to_production_equivalence_mismatch_count: mismatchCodes.filter((code) => code !== "GC_NOT_EXPOSED").length,
  mismatch_codes: mismatchCodes,
};
if (!options.output) throw new Error("--output is required");
await writeFile(options.output, `${JSON.stringify(output, null, 2)}\n`);
console.log(JSON.stringify(output));
if (output.status !== "PASS") process.exitCode = 1;
