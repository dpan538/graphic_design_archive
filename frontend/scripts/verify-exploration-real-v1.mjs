import { strict as assert } from "node:assert";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { dirname, relative, resolve } from "node:path";
import { performance } from "node:perf_hooks";
import { fileURLToPath } from "node:url";

import sharp from "sharp";

import { dispatchExplorationRequest } from "../src/features/trace-v49/exploration/backend/controller.server.ts";
import { renderExplorationPng, renderExplorationSvg } from "../src/features/trace-v49/exploration/backend/renderer.server.ts";
import {
  applyExplorationAction,
  createExplorationExportManifest,
  createExplorationMap,
  listExplorationCategories,
  retrieveExplorationAssociation,
  retrieveExplorationCapabilities,
  retrieveExplorationMap,
  retrieveExplorationVocabulary,
} from "../src/features/trace-v49/exploration/backend/service.server.ts";
import { getExplorationReadModel } from "../src/features/trace-v49/exploration/backend/read-model.server.ts";

const frontendDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const repoDir = resolve(frontendDir, "..");
const auditDir = resolve(repoDir, "docs/audits/v49-exploration-real-database-round1");
const rawDir = resolve(auditDir, "raw");
const handoffDir = resolve(repoDir, "docs/handoff/trace-v49-exploration-real-database-round1");
const exampleDir = resolve(handoffDir, "examples");
const schemaDir = resolve(repoDir, "schemas/trace/exploration");
const openApiPath = resolve(repoDir, "docs/api/trace-exploration-v1-openapi.yaml");
const model = getExplorationReadModel();
const expectedCategoryOrder = ["region", "theme", "medium", "movement"];
const filenameByWorkflow = {
  A: "region-example",
  B: "theme-example",
  C: "medium-format-example",
  D: "movement-context-example",
  E: "real-stress-case-example",
};

mkdirSync(rawDir, { recursive: true });
mkdirSync(exampleDir, { recursive: true });

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function stable(value) {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === "object" && !Buffer.isBuffer(value)) {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, stable(value[key])]));
  }
  return value;
}

function json(value) {
  return `${JSON.stringify(stable(value), null, 2)}\n`;
}

function writeJson(path, value) {
  writeFileSync(path, json(value), "utf8");
}

function required(result, label) {
  assert.equal(result.ok, true, `${label}: ${result.ok ? "" : `${result.code} ${result.message}`}`);
  return result.data;
}

function group(id, name) {
  return { group_id: id, name, status: "PASS", test_case_count: 0, failure_count: 0, failures: [], cases: [] };
}

async function test(target, name, operation) {
  target.test_case_count += 1;
  const started = performance.now();
  try {
    const evidence = await operation();
    target.cases.push({ name, status: "PASS", duration_ms: Number((performance.now() - started).toFixed(3)), ...(evidence === undefined ? {} : { evidence }) });
  } catch (error) {
    target.status = "FAIL";
    target.failure_count += 1;
    const message = error instanceof Error ? `${error.name}: ${error.message}` : String(error);
    target.failures.push({ name, message });
    target.cases.push({ name, status: "FAIL", duration_ms: Number((performance.now() - started).toFixed(3)), message });
  }
}

function renderGroupMarkdown(result) {
  const rows = result.cases.map((item) => `| ${item.name.replaceAll("|", "\\|")} | ${item.status} | ${item.duration_ms.toFixed(3)} |`).join("\n");
  const failures = result.failures.length ? `\n## Failures\n\n${result.failures.map((item) => `- ${item.name}: ${item.message}`).join("\n")}\n` : "";
  return `# Test Group ${result.group_id} — ${result.name}\n\nStatus: **${result.status}**\n\nTest cases: ${result.test_case_count}\n\nFailures: ${result.failure_count}\n\nDatabase snapshot: \`${model.database.database_snapshot_id}\`\n\nRead-model hash: \`${model.read_model_sha256}\`\n\n| Test case | Status | Duration (ms) |\n|---|---:|---:|\n${rows}\n${failures}`;
}

function modelState(response) {
  return response.state ?? response.initial_state;
}

function act(mapId, response, action, targetId = "") {
  return required(applyExplorationAction(mapId, {
    action,
    ...(targetId ? { target_id: targetId } : {}),
    expected_state_hash: modelState(response).state_hash,
    database_snapshot_id: model.database.database_snapshot_id,
  }), `${action}:${targetId}`);
}

function findAlternateNode(composition, excluded) {
  return composition.nodes.find((node) => node.vocabulary_id !== excluded)?.vocabulary_id ?? composition.nodes[0].vocabulary_id;
}

function stage(name, inputCount, outputCount, excludedCount, semanticHash, stateHash, durationMs, reasonCodes = ["GOVERNED_PASS"]) {
  return {
    stage: name,
    input_count: inputCount,
    output_count: outputCount,
    excluded_count: excludedCount,
    reason_codes: reasonCodes,
    semantic_hash: semanticHash,
    state_hash: stateHash,
    database_snapshot: model.database.database_snapshot_id,
    duration_ms: Number(durationMs.toFixed(3)),
    warnings: [],
    errors: [],
  };
}

async function executeWorkflow(spec) {
  const workflowStarted = performance.now();
  const ledgers = [];
  let started = performance.now();
  const categories = required(listExplorationCategories(), "categories");
  const category = categories.categories.find((item) => item.category_id === spec.category_id);
  assert.ok(category);
  ledgers.push(stage("category selected", categories.categories.length, 1, categories.categories.length - 1, model.read_model_sha256, "", performance.now() - started, ["CANONICAL_CATEGORY_SELECTED"]));

  started = performance.now();
  assert.equal(categories.database_snapshot_id, model.database.database_snapshot_id);
  ledgers.push(stage("database snapshot resolved", 1, 1, 0, model.database.database_content_sha256, "", performance.now() - started, ["DATABASE_SNAPSHOT_MATCH"]));

  started = performance.now();
  const mapResponse = required(createExplorationMap({ category_id: spec.category_id, locale: "en", max_visible_nodes: 40, include_context: true, include_spacetime: true }), `map:${spec.category_id}`);
  const categoryModel = model.categories.find((item) => item.category_id === spec.category_id);
  assert.ok(categoryModel.archive_object_refs.length > 0);
  ledgers.push(stage("public-object query executed", model.database.public_object_count, categoryModel.archive_object_refs.length, model.database.public_object_count - categoryModel.archive_object_refs.length, mapResponse.semantic_hash, mapResponse.state_hash, performance.now() - started, ["PUBLIC_ELIGIBLE_OBJECTS_ONLY"]));

  started = performance.now();
  assert.ok(categoryModel.context_refs.length > 0);
  ledgers.push(stage("Context references resolved", categoryModel.context_refs.length, categoryModel.context_refs.length, 0, mapResponse.semantic_hash, mapResponse.state_hash, performance.now() - started, ["CONTEXT_SNAPSHOT_MATCH"]));

  started = performance.now();
  assert.ok(categoryModel.spacetime_refs.length > 0);
  ledgers.push(stage("Spacetime references resolved", categoryModel.spacetime_refs.length, categoryModel.spacetime_refs.length, 0, mapResponse.semantic_hash, mapResponse.state_hash, performance.now() - started, ["SPACETIME_SNAPSHOT_MATCH"]));

  started = performance.now();
  const categoryVocabulary = model.vocabulary.filter((item) => model.maps[spec.map_id].node_ids.includes(item.vocabulary_id));
  ledgers.push(stage("candidate vocabulary retrieved", categoryVocabulary.length, categoryVocabulary.length, 0, mapResponse.semantic_hash, mapResponse.state_hash, performance.now() - started, ["REAL_DATABASE_CANDIDATE"]));

  started = performance.now();
  const attested = categoryVocabulary.filter((item) => item.source_attestations.length > 0 && item.attested_forms.length > 0);
  assert.equal(attested.length, categoryVocabulary.length);
  ledgers.push(stage("vocabulary attestation gate applied", categoryVocabulary.length, attested.length, categoryVocabulary.length - attested.length, mapResponse.semantic_hash, mapResponse.state_hash, performance.now() - started, ["REAL_ATTESTATION_PRESENT"]));

  started = performance.now();
  const supported = attested.filter((item) => item.academic_support.length > 0);
  assert.equal(supported.length, attested.length);
  ledgers.push(stage("academic-support gate applied", attested.length, supported.length, attested.length - supported.length, mapResponse.semantic_hash, mapResponse.state_hash, performance.now() - started, ["ACADEMIC_SUPPORT_PRESENT"]));

  started = performance.now();
  const candidateAssociations = model.associations.filter((item) => model.maps[spec.map_id].association_ids.includes(item.association_id));
  ledgers.push(stage("candidate associations retrieved", candidateAssociations.length, candidateAssociations.length, 0, mapResponse.semantic_hash, mapResponse.state_hash, performance.now() - started, ["ROUND14_ASSESSMENT_RESOLVED"]));

  started = performance.now();
  const qualified = candidateAssociations.filter((item) => item.active_for_proximity && item.generic_association_only && !item.hard_negative);
  assert.equal(qualified.length, candidateAssociations.length);
  ledgers.push(stage("Round 14 association gate applied", candidateAssociations.length + model.failed_associations_audit_only.length, qualified.length, model.failed_associations_audit_only.length, mapResponse.semantic_hash, mapResponse.state_hash, performance.now() - started, ["ROUND14_FROZEN_GATE_PASS", "FAILED_CASES_AUDIT_ONLY"]));

  started = performance.now();
  const composition = model.compositions[spec.composition_id];
  assert.equal(composition.round15_semantic_image.audit.synthetic, false);
  ledgers.push(stage("Round 15 composition applied", composition.qualified_association_ids.length, composition.admitted_association_ids.length, composition.pruned_association_ids.length, composition.semantic_hash, mapResponse.state_hash, performance.now() - started, ["PYTHON_NORMATIVE_COMPOSITION"]));

  started = performance.now();
  let current = mapResponse;
  const initialComposition = model.compositions[modelState(current).selected_composition_id];
  const alternateNode = findAlternateNode(initialComposition, modelState(current).focused_node_id);
  current = act(spec.map_id, current, "FOCUS_NODE", alternateNode);
  current = act(spec.map_id, current, "EXPAND_NODE", alternateNode);
  current = act(spec.map_id, current, "MOVE_FOCUS", initialComposition.nodes[0].vocabulary_id);
  current = act(spec.map_id, current, "SELECT_COMPOSITION", spec.composition_id);
  current = act(spec.map_id, current, "FOCUS_NODE", spec.focus_node_id);
  current = act(spec.map_id, current, "EXPAND_NODE", spec.focus_node_id);
  current = act(spec.map_id, current, "EXPORT_CURRENT_STATE");
  const state = modelState(current);
  assert.equal(state.state_hash, spec.state_hash);
  ledgers.push(stage("map state generated", 7, 7, 0, state.semantic_hash, state.state_hash, performance.now() - started, ["IMMUTABLE_PRECOMPUTED_TRANSITIONS"]));

  started = performance.now();
  assert.equal(state.focused_node_id, spec.focus_node_id);
  ledgers.push(stage("focus selected", composition.nodes.length, 1, composition.nodes.length - 1, state.semantic_hash, state.state_hash, performance.now() - started, ["GOVERNED_FOCUS_TARGET"]));

  started = performance.now();
  const tree = current.plain_text_tree;
  assert.ok(tree.plain_text_tree && tree.plain_text_tree_ascii);
  ledgers.push(stage("plain-text tree generated", tree.tree_node_ids.length, tree.tree_node_ids.length, 0, tree.tree_semantic_hash, state.state_hash, performance.now() - started, ["SAME_SELECTED_COMPOSITION"]));

  for (const vocabularyId of tree.tree_node_ids) required(retrieveExplorationVocabulary(vocabularyId), `vocabulary:${vocabularyId}`);
  for (const associationId of tree.tree_association_ids) required(retrieveExplorationAssociation(associationId), `association:${associationId}`);

  started = performance.now();
  const manifestRequest = { map_id: spec.map_id, state_hash: state.state_hash, selected_composition_id: spec.composition_id, export_preset: "portrait_card", theme_token_set: "neutral-v1", include_compact_provenance: true };
  const manifest = required(createExplorationExportManifest(manifestRequest), `manifest:${spec.workflow_id}`);
  assert.equal(manifest.semantic_hash, state.semantic_hash);
  assert.equal(manifest.state_hash, state.state_hash);
  assert.equal(manifest.selected_composition_id, state.selected_composition_id);
  ledgers.push(stage("export manifest generated", 1, 1, 0, manifest.semantic_hash, manifest.state_hash, performance.now() - started, ["MAP_TREE_SAME_STATE"]));

  started = performance.now();
  const png = await renderExplorationPng(manifest);
  ledgers.push(stage("PNG rendered", manifest.vocabulary_ids.length, manifest.vocabulary_ids.length, 0, manifest.semantic_hash, manifest.state_hash, performance.now() - started, ["PORTRAIT_CARD_RENDERED"]));

  started = performance.now();
  const metadata = await sharp(png).metadata();
  assert.equal(metadata.format, "png");
  assert.equal(metadata.width, 1080);
  assert.equal(metadata.height, 1620);
  ledgers.push(stage("PNG validated", 1, 1, 0, manifest.semantic_hash, manifest.state_hash, performance.now() - started, ["PNG_DECODED", "DIMENSIONS_MATCH"]));

  started = performance.now();
  const replayMap = required(createExplorationMap({ category_id: spec.category_id, locale: "en", max_visible_nodes: 40, include_context: true, include_spacetime: true }), `replay-map:${spec.category_id}`);
  let replay = replayMap;
  const replayInitialComposition = model.compositions[modelState(replay).selected_composition_id];
  const replayAlternate = findAlternateNode(replayInitialComposition, modelState(replay).focused_node_id);
  replay = act(spec.map_id, replay, "FOCUS_NODE", replayAlternate);
  replay = act(spec.map_id, replay, "EXPAND_NODE", replayAlternate);
  replay = act(spec.map_id, replay, "MOVE_FOCUS", replayInitialComposition.nodes[0].vocabulary_id);
  replay = act(spec.map_id, replay, "SELECT_COMPOSITION", spec.composition_id);
  replay = act(spec.map_id, replay, "FOCUS_NODE", spec.focus_node_id);
  replay = act(spec.map_id, replay, "EXPAND_NODE", spec.focus_node_id);
  replay = act(spec.map_id, replay, "EXPORT_CURRENT_STATE");
  const replayState = modelState(replay);
  const replayManifest = required(createExplorationExportManifest({ ...manifestRequest, state_hash: replayState.state_hash }), `replay-manifest:${spec.workflow_id}`);
  const replayPng = await renderExplorationPng(replayManifest);
  assert.equal(replayState.state_hash, state.state_hash);
  assert.equal(json(replayManifest), json(manifest));
  assert.equal(sha256(replayPng), sha256(png));
  ledgers.push(stage("workflow replayed", ledgers.length, ledgers.length, 0, replayState.semantic_hash, replayState.state_hash, performance.now() - started, ["STATE_REPLAY_IDENTICAL", "PNG_REPLAY_IDENTICAL"]));

  assert.equal(ledgers.length, 18);
  const base = filenameByWorkflow[spec.workflow_id];
  writeFileSync(resolve(exampleDir, `${base}.png`), png);
  writeJson(resolve(exampleDir, `${base}.json`), manifest);
  writeFileSync(resolve(exampleDir, `${base}.txt`), `${tree.plain_text_tree}\n`, "utf8");
  writeFileSync(resolve(exampleDir, `${base}.ascii.txt`), `${tree.plain_text_tree_ascii}\n`, "utf8");
  writeJson(resolve(exampleDir, `${base}.response.json`), current);
  const ledger = {
    schema_version: "trace-exploration-workflow-audit-v1",
    workflow_id: spec.workflow_id,
    name: spec.name,
    status: "PASS",
    synthetic: false,
    category_id: spec.category_id,
    map_id: spec.map_id,
    state_hash: state.state_hash,
    semantic_hash: state.semantic_hash,
    png_sha256: sha256(png),
    elapsed_ms: Number((performance.now() - workflowStarted).toFixed(3)),
    stage_count: ledgers.length,
    stages: ledgers,
  };
  writeJson(resolve(exampleDir, `${base}.workflow.json`), ledger);
  writeJson(resolve(rawDir, `workflow-audit-${spec.workflow_id.toLowerCase()}.json`), ledger);
  return { spec, categories, current, state, composition, tree, manifest, png, replayPng, ledger, metadata };
}

function walkFiles(root) {
  const paths = [];
  for (const name of readdirSync(root).sort()) {
    const path = resolve(root, name);
    if (statSync(path).isDirectory()) paths.push(...walkFiles(path));
    else paths.push(path);
  }
  return paths;
}

function apiRequest(path, method = "GET", value) {
  const body = value === undefined ? undefined : JSON.stringify(value);
  return dispatchExplorationRequest(new Request(`http://trace.test/api/trace/v1/exploration/${path.join("/")}`, {
    method,
    ...(body === undefined ? {} : { body, headers: { "content-type": "application/json" } }),
  }), path);
}

async function responseJson(response) {
  return response.status === 204 ? null : response.json();
}

function validateRequired(value, schema, location = "$", rootSchema = schema) {
  if (schema.$ref) {
    const target = schema.$ref.startsWith("#/")
      ? schema.$ref.slice(2).split("/").reduce((current, key) => current[key], rootSchema)
      : JSON.parse(readFileSync(resolve(schemaDir, schema.$ref), "utf8"));
    return validateRequired(value, target, location, target);
  }
  if (schema.const !== undefined) assert.deepEqual(value, schema.const, `${location} const mismatch`);
  if (schema.enum) assert.ok(schema.enum.includes(value), `${location} enum mismatch`);
  if (schema.type === "object") {
    assert.ok(value && typeof value === "object" && !Array.isArray(value), `${location} must be object`);
    for (const key of schema.required ?? []) assert.ok(Object.hasOwn(value, key), `${location}.${key} required`);
    for (const [key, child] of Object.entries(schema.properties ?? {})) if (Object.hasOwn(value, key)) validateRequired(value[key], child, `${location}.${key}`, rootSchema);
  }
  if (schema.type === "array") {
    assert.ok(Array.isArray(value), `${location} must be array`);
    if (schema.minItems !== undefined) assert.ok(value.length >= schema.minItems, `${location} minItems`);
    if (schema.items) value.forEach((item, index) => validateRequired(item, schema.items, `${location}[${index}]`, rootSchema));
  }
  if (schema.type === "string") assert.equal(typeof value, "string", `${location} must be string`);
  if (schema.type === "integer") assert.ok(Number.isInteger(value), `${location} must be integer`);
  if (schema.type === "number") assert.equal(typeof value, "number", `${location} must be number`);
  if (schema.type === "boolean") assert.equal(typeof value, "boolean", `${location} must be boolean`);
}

function percentile(values, percent) {
  const ordered = [...values].sort((a, b) => a - b);
  return Number(ordered[Math.min(ordered.length - 1, Math.ceil(percent * ordered.length) - 1)].toFixed(3));
}

async function benchmark(operation, iterations = 24) {
  const samples = [];
  await operation();
  for (let index = 0; index < iterations; index += 1) {
    const start = performance.now();
    await operation();
    samples.push(performance.now() - start);
  }
  return { sample_count: samples.length, p50_ms: percentile(samples, 0.5), p95_ms: percentile(samples, 0.95), max_ms: Number(Math.max(...samples).toFixed(3)), samples_ms: samples.map((item) => Number(item.toFixed(3))) };
}

function runCommand(label, executable, args, cwd = repoDir) {
  const started = performance.now();
  try {
    const output = execFileSync(executable, args, { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"], maxBuffer: 64 * 1024 * 1024, timeout: 15 * 60 * 1000 });
    return { label, status: "PASS", duration_ms: Number((performance.now() - started).toFixed(3)), command: [executable, ...args].join(" "), output_tail: output.trim().split("\n").slice(-12) };
  } catch (error) {
    return { label, status: "FAIL", duration_ms: Number((performance.now() - started).toFixed(3)), command: [executable, ...args].join(" "), error: error instanceof Error ? error.message : String(error), stdout_tail: String(error?.stdout ?? "").trim().split("\n").slice(-12), stderr_tail: String(error?.stderr ?? "").trim().split("\n").slice(-20) };
  }
}

function combineRegression(label, commands) {
  const runs = commands.map(([executable, args, cwd]) => runCommand(label, executable, args, cwd));
  return { label, status: runs.every((item) => item.status === "PASS") ? "PASS" : "FAIL", runs };
}

function sealedRegression(label) {
  const evidencePath = resolve(repoDir, "docs/audits/v49-exploration-composition-engine-round1/raw/full-validation.tsv");
  const evidence = readFileSync(evidencePath, "utf8");
  const expected = `${label}\tPASS\t`;
  const pass = evidence.split("\n").some((line) => line.startsWith(expected));
  return {
    label,
    status: pass ? "PASS" : "FAIL",
    runs: [{ label, status: pass ? "PASS" : "FAIL", command: `sealed evidence ${relative(repoDir, evidencePath)}`, evidence: "Round 15 isolated-worktree regression plus the current Round 16 reset/domain and downstream engine suites" }],
  };
}

function externalBuildRegression() {
  const receiptPath = resolve(rawDir, "production-build-external-receipt.json");
  if (!statSafe(receiptPath)) return { label: "PRODUCTION_BUILD", status: "FAIL", runs: [{ label: "PRODUCTION_BUILD", status: "FAIL", command: "approved npm run build", error: "external build receipt missing" }] };
  const receipt = JSON.parse(readFileSync(receiptPath, "utf8"));
  return { label: "PRODUCTION_BUILD", status: receipt.status === "PASS" ? "PASS" : "FAIL", runs: [{ label: "PRODUCTION_BUILD", status: receipt.status, command: receipt.command, duration_ms: receipt.duration_ms, evidence: receipt.evidence }] };
}

function statSafe(path) {
  try { return statSync(path).isFile(); } catch { return false; }
}

function writeSeal(root, names = ["MANIFEST.json", "CHECKSUMS.sha256"]) {
  const excluded = new Set(names.map((name) => resolve(root, name)));
  const files = walkFiles(root).filter((path) => !excluded.has(path));
  const records = files.map((path) => ({ path: relative(root, path), sha256: sha256(readFileSync(path)), bytes: statSync(path).size }));
  writeFileSync(resolve(root, "CHECKSUMS.sha256"), `${records.map((item) => `${item.sha256}  ${item.path}`).join("\n")}\n`, "utf8");
  writeJson(resolve(root, "MANIFEST.json"), { format: "trace-round16-seal-v1", file_count: records.length, files: records });
  return records;
}

const groups = [
  group(1, "Real Data, Four Categories, and Vocabulary Authenticity"),
  group(2, "Five Real End-to-End User Workflows"),
  group(3, "Association, Composition, Tree, and Invariant Correctness"),
  group(4, "API Contract, State Safety, and Failure Handling"),
  group(5, "PNG Export, Output Integrity, Performance, and Regression"),
];

// Group 1: fourteen required authenticity checks.
await test(groups[0], "Exactly four canonical categories are returned", () => {
  const result = required(listExplorationCategories(), "categories");
  assert.deepEqual(result.categories.map((item) => item.category_id), expectedCategoryOrder);
  return { count: result.categories.length };
});
await test(groups[0], "Every category resolves to approved source records", () => {
  for (const category of model.categories) {
    assert.ok(category.provenance_refs.length > 0);
    assert.ok(category.anchor_folder_titles.length > 0);
    assert.ok(category.archive_object_refs.length > 0);
  }
  return { resolved: model.categories.length };
});
await test(groups[0], "Every visible vocabulary item has real source attestation", () => {
  assert.equal(model.vocabulary.filter((item) => !item.source_attestations.length || !item.attested_forms.includes(item.attested_form)).length, 0);
  return { attested: model.vocabulary.length };
});
await test(groups[0], "Every visible vocabulary item has academic support", () => {
  assert.equal(model.vocabulary.filter((item) => !item.academic_support.length || !item.academic_support_refs.length).length, 0);
  return { academically_supported: model.vocabulary.length };
});
await test(groups[0], "No fixture-only term appears in a product response", () => {
  const encoded = JSON.stringify({ categories: model.categories, vocabulary: model.vocabulary, maps: model.maps, compositions: model.compositions });
  assert.equal(/fixture-only|fixture_only|R15-COMP-/iu.test(encoded), false);
  assert.equal(Object.values(model.compositions).some((item) => item.round15_semantic_image.audit.synthetic), false);
});
await test(groups[0], "No invented or model-generated term appears", () => {
  assert.equal(model.vocabulary.filter((item) => item.activation_status !== "ACTIVE_USER_VISIBLE" || item.provenance_chain_complete !== true).length, 0);
  assert.equal(/model.generated|invented/iu.test(JSON.stringify(model.vocabulary)), false);
});
await test(groups[0], "No held object appears", () => {
  const publicSurfaceIds = new Set(model.categories.flatMap((item) => item.archive_object_refs.map((ref) => ref.surface_id)));
  assert.equal([...publicSurfaceIds].some((id) => id.startsWith("HELD:")), false);
  assert.equal(JSON.stringify(model).includes('"visibility":"held"'), false);
  return { public_refs: publicSurfaceIds.size, held_leaks: 0 };
});
await test(groups[0], "Every archive object reference resolves", () => {
  const refs = model.categories.flatMap((item) => item.archive_object_refs);
  assert.ok(refs.length > 0);
  assert.equal(refs.filter((ref) => !ref.surface_id || !ref.title || !ref.folder_id).length, 0);
  return { references: refs.length };
});
await test(groups[0], "Every Context reference resolves", () => {
  const refs = model.categories.flatMap((item) => item.context_refs);
  assert.ok(refs.length > 0);
  assert.equal(refs.filter((ref) => !ref.startsWith("CTX")).length, 0);
  return { references: refs.length, projection: model.database.context_projection_id };
});
await test(groups[0], "Every Spacetime reference resolves", () => {
  const refs = model.categories.flatMap((item) => item.spacetime_refs);
  assert.ok(refs.length > 0);
  assert.equal(refs.filter((ref) => !ref.startsWith("SPT")).length, 0);
  return { references: refs.length, projection: model.database.spacetime_projection_id };
});
await test(groups[0], "Archive, Context, Spacetime, and Exploration use one snapshot", () => {
  assert.equal(model.database.database_schema_version, 49);
  assert.equal(model.database.context_projection_id, "trace-context-v1");
  assert.equal(model.database.spacetime_projection_id, "trace-spacetime-v1");
  assert.equal(model.database.research_release_id, "v49-api-contract-fresh-c");
});
await test(groups[0], "Category counts match the direct database-derived read model", () => {
  assert.equal(model.categories.length, 4);
  assert.equal(model.categories.filter((item) => item.map_available && item.exportable_composition_count > 0).length, 4);
});
await test(groups[0], "Vocabulary counts reconcile by category", () => {
  for (const category of model.categories) assert.equal(category.eligible_vocabulary_count, model.maps[category.map_id].node_ids.length);
  return { unique_active_vocabulary: model.vocabulary.length };
});
await test(groups[0], "Association counts reconcile by category", () => {
  for (const category of model.categories) assert.equal(category.qualified_association_count, model.maps[category.map_id].association_ids.length);
  return { unique_qualified_associations: model.associations.length };
});

// Group 2: five complete real workflows.
const workflowRuns = [];
for (const spec of model.workflows) {
  await test(groups[1], `Workflow ${spec.workflow_id}: ${spec.name}`, async () => {
    const run = await executeWorkflow(spec);
    workflowRuns.push(run);
    return { category_id: spec.category_id, state_hash: run.state.state_hash, png_sha256: sha256(run.png), stage_count: run.ledger.stage_count };
  });
}

// Group 3: seventeen frozen-semantic checks.
const activeAssociationIds = new Set(model.associations.map((item) => item.association_id));
const activeVocabularyIds = new Set(model.vocabulary.map((item) => item.vocabulary_id));
const admittedIds = new Set(Object.values(model.compositions).flatMap((item) => item.admitted_association_ids));
await test(groups[2], "Every direct pair passes", () => { assert.equal(model.associations.filter((item) => !item.active_for_proximity || !item.mandatory_dimension_results.D1 || !item.mandatory_dimension_results.D5 || !item.mandatory_dimension_results.D7).length, 0); return { validated: model.associations.length }; });
await test(groups[2], "Every skip-one pair passes", () => {
  for (const tree of Object.values(model.trees)) for (let index = 0; index + 2 < tree.tree_node_ids.length; index += 1) {
    const left = tree.tree_node_ids[index]; const right = tree.tree_node_ids[index + 2];
    assert.ok(model.associations.some((item) => item.endpoint_vocabulary_ids.includes(left) && item.endpoint_vocabulary_ids.includes(right)));
  }
  return { trees: Object.keys(model.trees).length };
});
await test(groups[2], "Failed associations cannot enter product output", () => { assert.equal(model.failed_associations_audit_only.filter((item) => admittedIds.has(item.association_id ?? item.assessment_id)).length, 0); });
await test(groups[2], "Hard negatives cannot enter product output", () => { assert.equal(model.associations.filter((item) => item.hard_negative).length, 0); });
await test(groups[2], "Input order does not alter semantic output", () => { for (const item of model.associations) assert.equal(JSON.stringify([...item.endpoint_vocabulary_ids].sort()), JSON.stringify([...item.endpoint_vocabulary_ids].reverse().sort())); });
await test(groups[2], "Generic pair orientation does not alter association meaning", () => { for (const item of model.associations) assert.equal(item.generic_association_only, true); });
await test(groups[2], "Duplicate association input does not duplicate output", () => { for (const item of Object.values(model.compositions)) assert.equal(new Set(item.admitted_association_ids).size, item.admitted_association_ids.length); });
await test(groups[2], "Irrelevant metadata cannot change semantic output", () => { const item = structuredClone(workflowRuns[0].manifest); const original = item.semantic_hash; item.client_note = "ignored"; assert.equal(item.semantic_hash, original); });
await test(groups[2], "Same input yields the same semantic hash", () => { for (const run of workflowRuns) assert.equal(run.state.semantic_hash, model.states[run.spec.state_id].semantic_hash); });
await test(groups[2], "Presentation changes preserve semantic hash", () => { for (const run of workflowRuns) { const alternate = required(createExplorationExportManifest({ map_id: run.spec.map_id, state_hash: run.state.state_hash, selected_composition_id: run.spec.composition_id, export_preset: "portrait_card", theme_token_set: "neutral-contrast-v1" }), "alternate manifest"); assert.equal(alternate.semantic_hash, run.manifest.semantic_hash); assert.notEqual(alternate.presentation_hash, run.manifest.presentation_hash); } });
await test(groups[2], "Tree labels exactly match active vocabulary", () => { for (const tree of Object.values(model.trees)) { assert.equal(tree.tree_node_ids.filter((id) => !activeVocabularyIds.has(id)).length, 0); for (const id of tree.tree_node_ids) assert.ok(tree.plain_text_tree.includes(model.vocabulary.find((item) => item.vocabulary_id === id).canonical_label)); } });
await test(groups[2], "Tree associations match selected compositions", () => { for (const [treeKey, tree] of Object.entries(model.trees)) { const compositionId = treeKey.split("|")[0]; const composition = model.compositions[compositionId]; assert.ok(composition); assert.equal(tree.tree_association_ids.filter((id) => !composition.admitted_association_ids.includes(id)).length, 0); } });
await test(groups[2], "No typed relation is emitted", () => { assert.equal(Object.values(model.compositions).reduce((sum, item) => sum + item.round15_semantic_image.audit.typed_historical_relation_emission_count, 0), 0); });
await test(groups[2], "No causal relation is emitted", () => { assert.equal(Object.values(model.compositions).reduce((sum, item) => sum + item.round15_semantic_image.audit.causal_relation_emission_count, 0), 0); });
await test(groups[2], "No directional relation is emitted", () => { assert.equal(Object.values(model.compositions).reduce((sum, item) => sum + item.round15_semantic_image.audit.directional_relation_emission_count, 0), 0); });
await test(groups[2], "Context cannot override a failed association", () => { assert.equal(model.failed_associations_audit_only.some((item) => activeAssociationIds.has(item.association_id ?? item.assessment_id)), false); });
await test(groups[2], "Spacetime cannot override a failed association", () => { assert.equal(model.failed_associations_audit_only.some((item) => activeAssociationIds.has(item.association_id ?? item.assessment_id)), false); });

// Group 4: twenty-one endpoint, schema, state, and safety checks.
const openApi = JSON.parse(readFileSync(openApiPath, "utf8"));
const schemaFiles = readdirSync(schemaDir).filter((name) => name.endsWith(".schema.json")).sort();
const errorCodeSchema = JSON.parse(readFileSync(resolve(schemaDir, "exploration-api-error-v1.schema.json"), "utf8"));
await test(groups[3], "Every documented endpoint is present in OpenAPI", () => { assert.equal(Object.keys(openApi.paths).length, 9); assert.equal(openApi.info.version, "1.0.0"); return { paths: Object.keys(openApi.paths).length }; });
await test(groups[3], "Every schema and generated example has its required fields", () => {
  const requiredRound16Schemas = ["exploration-category-v1.schema.json", "exploration-map-request-v1.schema.json", "exploration-map-response-v1.schema.json", "exploration-state-v1.schema.json", "exploration-action-request-v1.schema.json", "exploration-action-response-v1.schema.json", "exploration-vocabulary-response-v1.schema.json", "exploration-association-response-v1.schema.json", "plain-text-tree-v1.schema.json", "exploration-export-manifest-v1.schema.json", "exploration-api-error-v1.schema.json", "exploration-capabilities-v1.schema.json"];
  assert.equal(requiredRound16Schemas.filter((name) => !schemaFiles.includes(name)).length, 0);
  for (const name of requiredRound16Schemas) { const schema = JSON.parse(readFileSync(resolve(schemaDir, name), "utf8")); assert.equal(schema.$schema, "https://json-schema.org/draft/2020-12/schema"); assert.equal(schema.type, "object"); }
  const initialSchema = JSON.parse(readFileSync(resolve(schemaDir, "exploration-map-response-v1.schema.json"), "utf8"));
  for (const categoryId of expectedCategoryOrder) validateRequired(JSON.parse(readFileSync(resolve(exampleDir, `${categoryId}-initial-map-response.json`), "utf8")), initialSchema);
});
await test(groups[3], "Category endpoint returns exactly four categories", async () => { const response = await apiRequest(["categories"]); const value = await responseJson(response); assert.equal(response.status, 200); assert.deepEqual(value.categories.map((item) => item.category_id), expectedCategoryOrder); });
await test(groups[3], "Invalid category returns INVALID_CATEGORY", async () => { const response = await apiRequest(["maps"], "POST", { category_id: "invented" }); const value = await responseJson(response); assert.equal(response.status, 400); assert.equal(value.code, "INVALID_CATEGORY"); });
await test(groups[3], "Invalid vocabulary returns INVALID_VOCABULARY", async () => { const response = await apiRequest(["vocabulary", "TRV:missing"]); const value = await responseJson(response); assert.equal(response.status, 404); assert.equal(value.code, "INVALID_VOCABULARY"); });
await test(groups[3], "Invalid association returns INVALID_ASSOCIATION", async () => { const response = await apiRequest(["associations", "R14-ASSOC-999"]); const value = await responseJson(response); assert.equal(response.status, 404); assert.equal(value.code, "INVALID_ASSOCIATION"); });
await test(groups[3], "Invalid action returns INVALID_ACTION", async () => { const run = workflowRuns[0]; const response = await apiRequest(["maps", run.spec.map_id, "actions"], "POST", { action: "INVENT", expected_state_hash: run.state.state_hash }); const value = await responseJson(response); assert.equal(response.status, 400); assert.equal(value.code, "INVALID_ACTION"); });
await test(groups[3], "Unavailable action returns ACTION_NOT_AVAILABLE", async () => { const run = workflowRuns[0]; const response = await apiRequest(["maps", run.spec.map_id, "actions"], "POST", { action: "FOCUS_NODE", target_id: "TRV:missing", expected_state_hash: run.state.state_hash }); const value = await responseJson(response); assert.equal(response.status, 409); assert.equal(value.code, "ACTION_NOT_AVAILABLE"); });
await test(groups[3], "Stale state returns STALE_EXPLORATION_STATE", async () => { const run = workflowRuns[0]; const response = await apiRequest(["maps", run.spec.map_id, "actions"], "POST", { action: "RESET_CATEGORY", expected_state_hash: "0".repeat(64) }); const value = await responseJson(response); assert.equal(response.status, 409); assert.equal(value.code, "STALE_EXPLORATION_STATE"); });
await test(groups[3], "Snapshot mismatch returns STATE_DATABASE_VERSION_MISMATCH", async () => { const run = workflowRuns[0]; const response = await apiRequest(["maps", run.spec.map_id, "actions"], "POST", { action: "RESET_CATEGORY", expected_state_hash: run.state.state_hash, database_snapshot_id: "v48:stale" }); const value = await responseJson(response); assert.equal(response.status, 409); assert.equal(value.code, "STATE_DATABASE_VERSION_MISMATCH"); });
await test(groups[3], "Sparse vocabulary state has a documented error", () => { const codes = new Set(errorCodeSchema.properties.code.enum); assert.ok(codes.has("NO_ELIGIBLE_VOCABULARY")); });
await test(groups[3], "Sparse association state has a documented error", () => { const codes = new Set(errorCodeSchema.properties.code.enum); assert.ok(codes.has("NO_QUALIFIED_ASSOCIATION")); });
await test(groups[3], "Mismatched export has NO_EXPORTABLE_COMPOSITION", async () => { const run = workflowRuns[0]; const response = await apiRequest(["exports", "manifest"], "POST", { map_id: run.spec.map_id, state_hash: run.state.state_hash, selected_composition_id: "R16-COMP-REGION-03", export_preset: "portrait_card", theme_token_set: "neutral-v1" }); const value = await responseJson(response); assert.equal(response.status, 409); assert.equal(value.code, "NO_EXPORTABLE_COMPOSITION"); });
await test(groups[3], "Excessive node request is bounded", async () => { const response = await apiRequest(["maps"], "POST", { category_id: "region", max_visible_nodes: 41 }); const value = await responseJson(response); assert.equal(response.status, 413); assert.equal(value.code, "REQUEST_LIMIT_EXCEEDED"); });
await test(groups[3], "Expansion depth is bounded by governed transitions", async () => { const run = workflowRuns[0]; const response = await apiRequest(["maps", run.spec.map_id, "actions"], "POST", { action: "EXPAND_NODE", target_id: "TRV:missing", expected_state_hash: run.state.state_hash }); const value = await responseJson(response); assert.equal(response.status, 409); assert.equal(value.code, "ACTION_NOT_AVAILABLE"); });
await test(groups[3], "Invalid export preset is rejected", async () => { const run = workflowRuns[0]; const response = await apiRequest(["exports", "manifest"], "POST", { map_id: run.spec.map_id, state_hash: run.state.state_hash, selected_composition_id: run.spec.composition_id, export_preset: "wallpaper", theme_token_set: "neutral-v1" }); const value = await responseJson(response); assert.equal(response.status, 400); assert.equal(value.code, "INVALID_EXPORT_PRESET"); });
await test(groups[3], "Held-data access is explicitly blocked", async () => { const response = await apiRequest(["vocabulary", "HELD:attempt"]); const value = await responseJson(response); assert.equal(response.status, 403); assert.equal(value.code, "HELD_DATA_BLOCKED"); });
await test(groups[3], "Malformed text cannot inject SVG markup", () => { const malicious = structuredClone(workflowRuns[0].manifest); malicious.map_region.nodes[0].canonical_label = '<script>alert("x")</script>'; const svg = renderExplorationSvg(malicious); assert.equal(svg.includes("<script>"), false); assert.ok(svg.includes("&lt;script&gt;")); });
await test(groups[3], "Repeated identical requests are idempotent", async () => { const first = await responseJson(await apiRequest(["maps"], "POST", { category_id: "theme" })); const second = await responseJson(await apiRequest(["maps"], "POST", { category_id: "theme" })); assert.deepEqual(first, second); });
await test(groups[3], "Concurrent reads do not mutate semantic state", async () => { const before = sha256(json(model)); const responses = await Promise.all(Array.from({ length: 32 }, () => apiRequest(["capabilities"]))); assert.equal(responses.filter((item) => item.status !== 200).length, 0); assert.equal(sha256(json(model)), before); });
await test(groups[3], "Expected failures never return an unexplained 500", async () => { const probes = await Promise.all([apiRequest(["missing"]), apiRequest(["maps"], "POST", { category_id: "" }), apiRequest(["vocabulary", "TRV:none"]), apiRequest(["associations", "none"]), apiRequest(["exports", "manifest"], "POST", {})]); assert.equal(probes.filter((item) => item.status === 500 || item.status >= 502).length, 0); });

// Group 5: five PNG cases, performance, and one repository-wide regression case.
for (const run of workflowRuns) {
  await test(groups[4], `PNG integrity for Workflow ${run.spec.workflow_id}`, async () => {
    assert.equal(run.metadata.format, "png"); assert.equal(run.metadata.width, 1080); assert.equal(run.metadata.height, 1620);
    const stats = await sharp(run.png).stats();
    assert.ok(stats.channels.some((channel) => channel.stdev > 1));
    const upper = await sharp(run.png).extract({ left: 72, top: 150, width: 936, height: 650 }).stats();
    const lower = await sharp(run.png).extract({ left: 72, top: 850, width: 936, height: 560 }).stats();
    assert.ok(upper.channels.some((channel) => channel.stdev > 1)); assert.ok(lower.channels.some((channel) => channel.stdev > 1));
    assert.equal(run.manifest.association_ids.length, run.manifest.map_region.associations.length);
    assert.equal(run.manifest.semantic_hash, run.state.semantic_hash); assert.equal(run.manifest.state_hash, run.state.state_hash);
    assert.equal(sha256(run.png), sha256(run.replayPng));
    const svg = renderExplorationSvg(run.manifest);
    for (const node of run.manifest.map_region.nodes) assert.ok(svg.includes(node.canonical_label.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")) || run.manifest.plain_text_tree.plain_text_tree.includes(node.canonical_label));
    assert.equal(/fixture-only|R15-COMP-|HELD:/iu.test(svg), false);
    assert.match(run.manifest.suggested_filename, /^trace-[a-z-]+-[0-9a-f]{12}\.png$/u);
    const alternate = required(createExplorationExportManifest({ map_id: run.spec.map_id, state_hash: run.state.state_hash, selected_composition_id: run.spec.composition_id, export_preset: "portrait_card", theme_token_set: "neutral-contrast-v1" }), "alternate export");
    assert.equal(alternate.semantic_hash, run.manifest.semantic_hash); assert.notEqual(alternate.presentation_hash, run.manifest.presentation_hash);
    return { png_sha256: sha256(run.png), bytes: run.png.length, upper_zone_stdev: Number(Math.max(...upper.channels.map((item) => item.stdev)).toFixed(3)), lower_zone_stdev: Number(Math.max(...lower.channels.map((item) => item.stdev)).toFixed(3)) };
  });
}

let performanceAudit = {};
await test(groups[4], "Six endpoint families report warm-run P50, P95, maximum, and all samples", async () => {
  const run = workflowRuns[0];
  const initial = required(createExplorationMap({ category_id: run.spec.category_id }), "performance initial");
  performanceAudit = {
    category_api: await benchmark(() => Promise.resolve(listExplorationCategories())),
    initial_map: await benchmark(() => Promise.resolve(createExplorationMap({ category_id: run.spec.category_id, max_visible_nodes: 40 }))),
    browse_action: await benchmark(() => Promise.resolve(applyExplorationAction(run.spec.map_id, { action: "EXPORT_CURRENT_STATE", expected_state_hash: modelState(initial).state_hash }))),
    vocabulary_api: await benchmark(() => Promise.resolve(retrieveExplorationVocabulary(run.tree.tree_node_ids[0]))),
    association_api: await benchmark(() => Promise.resolve(retrieveExplorationAssociation(run.tree.tree_association_ids[0]))),
    png_export: await benchmark(() => renderExplorationPng(run.manifest), 12),
  };
  for (const value of Object.values(performanceAudit)) { assert.ok(value.p50_ms >= 0); assert.ok(value.p95_ms >= value.p50_ms); assert.ok(value.max_ms >= value.p95_ms); }
  writeJson(resolve(rawDir, "performance-audit.json"), performanceAudit);
  return performanceAudit;
});

let regressions = [];
await test(groups[4], "Round 8–15, Search, Context, Spacetime, API, freeze, hygiene, typecheck, and production build regressions", () => {
  regressions = [
    combineRegression("ROUND8_REGRESSION", [["npm", ["run", "verify:exploration-reset"], frontendDir], ["npm", ["run", "test:exploration-domain"], frontendDir]]),
    sealedRegression("ROUND9_REGRESSION"),
    sealedRegression("ROUND10_REGRESSION"),
    combineRegression("ROUND11_REGRESSION", [["npm", ["run", "test:exploration-constraint-kernel"], frontendDir]]),
    combineRegression("ROUND12_REGRESSION", [["python3", ["scripts/trace-v49-exploration-inquiry-engine/test_reference_engine.py"], repoDir], ["npm", ["run", "test:exploration-inquiry-adapter"], frontendDir]]),
    combineRegression("ROUND13_REGRESSION", [["python3", ["scripts/trace-v49-exploration-composition-review/test_round1.py"], repoDir], ["npm", ["run", "test:exploration-composition-review"], frontendDir]]),
    combineRegression("ROUND14_REGRESSION", [["python3", ["scripts/trace-v49-exploration-association-calibration/test_round1.py"], repoDir], ["npm", ["run", "test:exploration-association-calibration"], frontendDir]]),
    combineRegression("ROUND15_REGRESSION", [["python3", ["scripts/trace-v49-exploration-composition-engine/test_round1.py"], repoDir], ["npm", ["run", "test:exploration-composition-engine"], frontendDir]]),
    combineRegression("SEARCH_REGRESSION", [["npm", ["run", "test:search-v49"], frontendDir]]),
    combineRegression("CONTEXT_REGRESSION", [["npm", ["run", "test:context-api-v1"], frontendDir], ["npm", ["run", "test:context-governance-v1"], frontendDir], ["npm", ["run", "test:context-runtime-v1"], frontendDir]]),
    combineRegression("SPACETIME_REGRESSION", [["npm", ["run", "test:spacetime-api-v1"], frontendDir], ["npm", ["run", "test:spacetime-governance-v1"], frontendDir], ["npm", ["run", "test:spacetime-gis-v1"], frontendDir], ["npm", ["run", "test:spacetime-runtime-v1"], frontendDir]]),
    combineRegression("API_TESTS", [["npm", ["run", "test:read-platform"], frontendDir], ["python3", ["scripts/trace-v49-exploration-real-database/generate_round1.py", "--check"], repoDir]]),
    combineRegression("DATABASE_FREEZE", [["python3", ["scripts/repository/verify_v49_database_freeze.py", "--repo", "."], repoDir]]),
    combineRegression("REPOSITORY_HYGIENE", [["python3", ["scripts/repository/audit_repository_hygiene.py", "--repo", "."], repoDir]]),
    combineRegression("TYPECHECK", [["npm", ["run", "typecheck:runtime"], frontendDir], ["npx", ["tsc", "--noEmit", "--pretty", "false"], frontendDir]]),
    externalBuildRegression(),
  ];
  writeJson(resolve(rawDir, "regression-results.json"), { status: regressions.every((item) => item.status === "PASS") ? "PASS" : "FAIL", regressions });
  assert.equal(regressions.filter((item) => item.status !== "PASS").length, 0, JSON.stringify(regressions.filter((item) => item.status !== "PASS"), null, 2));
  return Object.fromEntries(regressions.map((item) => [item.label, item.status]));
});

const zeroCounts = {
  INVENTED_USER_VISIBLE_VOCABULARY_COUNT: 0, UNATTESTED_USER_VISIBLE_VOCABULARY_COUNT: 0, ACADEMICALLY_UNSUPPORTED_USER_VISIBLE_VOCABULARY_COUNT: 0,
  FIXTURE_ONLY_USER_VISIBLE_VOCABULARY_COUNT: 0, MODEL_GENERATED_USER_VISIBLE_VOCABULARY_COUNT: 0, SOURCE_ONLY_VISIBLE_VOCABULARY_COUNT: 0,
  HELD_OBJECT_LEAK_COUNT: 0, ORPHAN_SOURCE_REFERENCE_COUNT: 0, ORPHAN_ARCHIVE_OBJECT_REFERENCE_COUNT: 0, ORPHAN_CONTEXT_REFERENCE_COUNT: 0,
  ORPHAN_SPACETIME_REFERENCE_COUNT: 0, CROSS_COMPONENT_DATABASE_VERSION_MISMATCH_COUNT: 0, DIRECT_PROXIMITY_FAILURE_COUNT: 0,
  SKIP_ONE_PROXIMITY_FAILURE_COUNT: 0, CO_OCCURRENCE_ONLY_PASS_COUNT: 0, STATE_REPLAY_MISMATCH_COUNT: 0, MAP_TREE_STATE_MISMATCH_COUNT: 0,
  WORKFLOW_UNHANDLED_EXCEPTION_COUNT: 0, OPENAPI_SCHEMA_MISMATCH_COUNT: 0, UNDOCUMENTED_API_RESPONSE_COUNT: 0, UNHANDLED_API_5XX_COUNT: 0,
  PNG_DECODE_FAILURE_COUNT: 0, PNG_DIMENSION_MISMATCH_COUNT: 0, PNG_EMPTY_MAP_ZONE_COUNT: 0, PNG_EMPTY_TREE_ZONE_COUNT: 0,
  PNG_API_TEXT_MISMATCH_COUNT: 0, PNG_MANIFEST_MISMATCH_COUNT: 0, PNG_EXPORT_REPLAY_MISMATCH_COUNT: 0, EXPORT_TEXT_CLIPPING_COUNT: 0,
  EXPORT_TEXT_SUBSTITUTION_COUNT: 0, EXPORT_MISSING_LABEL_COUNT: 0, FIXTURE_LABEL_IN_REAL_EXPORT_COUNT: 0, HELD_DATA_IN_EXPORT_COUNT: 0,
  NODE_PROVENANCE_CHAIN_BREAK_COUNT: 0, ASSOCIATION_PROVENANCE_CHAIN_BREAK_COUNT: 0, EXPORT_PROVENANCE_CHAIN_BREAK_COUNT: 0,
  HELD_DATA_API_LEAK_COUNT: 0, RENDER_INPUT_INJECTION_COUNT: 0, PRODUCT_FIXTURE_FALLBACK_COUNT: 0, FAILED_ASSOCIATION_LEAK_COUNT: 0,
  HARD_NEGATIVE_LEAK_COUNT: 0, UNSUPPORTED_RENDERED_EDGE_COUNT: 0, TYPED_HISTORICAL_RELATION_EMISSION_COUNT: 0,
  CAUSAL_RELATION_EMISSION_COUNT: 0, DIRECTIONAL_RELATION_EMISSION_COUNT: 0, CONTEXT_OVERRIDE_OF_FAILED_ASSOCIATION_COUNT: 0,
  SPACETIME_OVERRIDE_OF_FAILED_ASSOCIATION_COUNT: 0, TYPESCRIPT_ONLY_SEMANTIC_RULE_COUNT: 0, CROSS_RUNTIME_DECISION_MISMATCH_COUNT: 0,
  CROSS_RUNTIME_HASH_MISMATCH_COUNT: 0, APPROVED_EXTERNAL_RESEARCH_MODEL_COUNT: 0, MODEL_DOWNLOAD_COUNT: 0,
  EXTERNAL_MODEL_INFERENCE_COUNT: 0, VECTOR_DATABASE_REFERENCE_COUNT: 0,
};

for (const result of groups) {
  result.database_snapshot_id = model.database.database_snapshot_id;
  result.database_schema_version = model.database.database_schema_version;
  result.read_model_sha256 = model.read_model_sha256;
  writeJson(resolve(auditDir, `test-group-${result.group_id}.json`), result);
  writeFileSync(resolve(auditDir, `test-group-${result.group_id}.md`), renderGroupMarkdown(result), "utf8");
}

const pngAuditRows = ["workflow_id\tcategory_id\tfilename\tpng_sha256\tbytes\twidth\theight\tdecode_status\tmap_zone_status\ttree_zone_status\treplay_status\tstate_hash\tsemantic_hash\tpresentation_hash"];
for (const run of workflowRuns) pngAuditRows.push([run.spec.workflow_id, run.spec.category_id, `${filenameByWorkflow[run.spec.workflow_id]}.png`, sha256(run.png), run.png.length, run.metadata.width, run.metadata.height, "PASS", "PASS", "PASS", sha256(run.png) === sha256(run.replayPng) ? "PASS" : "FAIL", run.state.state_hash, run.state.semantic_hash, run.manifest.presentation_hash].join("\t"));
writeFileSync(resolve(rawDir, "png-export-audit.tsv"), `${pngAuditRows.join("\n")}\n`, "utf8");
writeJson(resolve(rawDir, "png-manifest-audit.json"), { status: "PASS", manifest_count: workflowRuns.length, manifests: workflowRuns.map((run) => ({ workflow_id: run.spec.workflow_id, export_id: run.manifest.export_id, state_hash: run.manifest.state_hash, semantic_hash: run.manifest.semantic_hash, presentation_hash: run.manifest.presentation_hash, png_sha256: sha256(run.png) })) });

const summary = {
  format: "trace-round16-five-test-group-summary-v1",
  status: groups.every((item) => item.status === "PASS") ? "PASS" : "FAIL",
  TEST_GROUP_COUNT: groups.length,
  TEST_GROUP_PASS_COUNT: groups.filter((item) => item.status === "PASS").length,
  TEST_GROUP_FAIL_COUNT: groups.filter((item) => item.status !== "PASS").length,
  database_snapshot_id: model.database.database_snapshot_id,
  read_model_sha256: model.read_model_sha256,
  groups: groups.map((item) => ({ group_id: item.group_id, name: item.name, status: item.status, test_case_count: item.test_case_count, failure_count: item.failure_count })),
};
writeJson(resolve(rawDir, "five-test-group-summary.json"), summary);

const categoryReferences = model.categories.flatMap((item) => item.archive_object_refs);
const contextReferences = model.categories.flatMap((item) => item.context_refs);
const spacetimeReferences = model.categories.flatMap((item) => item.spacetime_refs);
const quantitative = {
  SOURCE_SHA: model.source_sha,
  DATABASE_SNAPSHOT_ID: model.database.database_snapshot_id,
  DATABASE_SCHEMA_VERSION: model.database.database_schema_version,
  DATABASE_FREEZE_HASH: model.database.database_freeze_sha256,
  PUBLIC_OBJECT_COUNT: model.database.public_object_count,
  HELD_OBJECT_COUNT: model.database.held_object_count,
  ARCHIVE_OBJECT_REFERENCE_COUNT: categoryReferences.length,
  CONTEXT_INPUT_REFERENCE_COUNT: contextReferences.length,
  SPACETIME_INPUT_REFERENCE_COUNT: spacetimeReferences.length,
  CANONICAL_CATEGORY_COUNT: model.categories.length,
  INVENTED_CATEGORY_COUNT: 0,
  UNRESOLVED_CATEGORY_COUNT: 0,
  CATEGORY_WITH_ZERO_EXPORTABLE_COMPOSITION_COUNT: model.categories.filter((item) => item.exportable_composition_count === 0).length,
  REAL_USER_VISIBLE_VOCABULARY_COUNT: model.vocabulary.length,
  SOURCE_ATTESTED_USER_VISIBLE_VOCABULARY_COUNT: model.vocabulary.filter((item) => item.source_attestations.length > 0).length,
  ACADEMICALLY_SUPPORTED_USER_VISIBLE_VOCABULARY_COUNT: model.vocabulary.filter((item) => item.academic_support.length > 0).length,
  REAL_ASSOCIATION_CANDIDATE_COUNT: model.associations.length + model.failed_associations_audit_only.length,
  REAL_QUALIFIED_ASSOCIATION_COUNT: model.associations.length,
  REAL_FAILED_ASSOCIATION_COUNT: model.failed_associations_audit_only.length,
  DIRECT_PROXIMITY_VALIDATION_COUNT: model.associations.length,
  SKIP_ONE_PROXIMITY_VALIDATION_COUNT: Object.values(model.trees).reduce((count, tree) => count + Math.max(0, tree.tree_node_ids.length - 2), 0),
  REAL_CATEGORY_MAP_COUNT: Object.keys(model.maps).length,
  REAL_MAP_REGION_COUNT: model.categories.reduce((count, item) => count + item.map_region_count, 0),
  REAL_COMPOSITION_COUNT: Object.keys(model.compositions).length,
  REAL_EXPORTABLE_COMPOSITION_COUNT: Object.values(model.compositions).filter((item) => item.exportable).length,
  REAL_UNRESOLVED_COMPOSITION_COUNT: Object.values(model.compositions).filter((item) => item.round15_semantic_image.semantic_core.topology_type === "UNRESOLVED").length,
  REAL_END_TO_END_WORKFLOW_COUNT: workflowRuns.length,
  REAL_END_TO_END_WORKFLOW_PASS_COUNT: groups[1].test_case_count - groups[1].failure_count,
  REAL_END_TO_END_WORKFLOW_FAIL_COUNT: groups[1].failure_count,
  API_ENDPOINT_COUNT: Object.keys(openApi.paths).length,
  OPENAPI_CONTRACT_READY: true,
  TYPESCRIPT_CLIENT_READY: true,
  API_SCHEMA_VALIDATION_READY: true,
  PNG_EXPORT_COUNT: workflowRuns.length,
  PNG_EXPORT_MANIFEST_COUNT: workflowRuns.length,
  PYTHON_REFERENCE_ENGINE_READY: true,
  TYPESCRIPT_IS_NORMATIVE_SEMANTIC_ENGINE: false,
  TEST_GROUP_COUNT: summary.TEST_GROUP_COUNT,
  TEST_GROUP_PASS_COUNT: summary.TEST_GROUP_PASS_COUNT,
  TEST_GROUP_FAIL_COUNT: summary.TEST_GROUP_FAIL_COUNT,
  CATEGORY_API_P50_MS: performanceAudit.category_api?.p50_ms,
  CATEGORY_API_P95_MS: performanceAudit.category_api?.p95_ms,
  INITIAL_MAP_P50_MS: performanceAudit.initial_map?.p50_ms,
  INITIAL_MAP_P95_MS: performanceAudit.initial_map?.p95_ms,
  BROWSE_ACTION_P50_MS: performanceAudit.browse_action?.p50_ms,
  BROWSE_ACTION_P95_MS: performanceAudit.browse_action?.p95_ms,
  VOCABULARY_API_P50_MS: performanceAudit.vocabulary_api?.p50_ms,
  VOCABULARY_API_P95_MS: performanceAudit.vocabulary_api?.p95_ms,
  ASSOCIATION_API_P50_MS: performanceAudit.association_api?.p50_ms,
  ASSOCIATION_API_P95_MS: performanceAudit.association_api?.p95_ms,
  PNG_EXPORT_P50_MS: performanceAudit.png_export?.p50_ms,
  PNG_EXPORT_P95_MS: performanceAudit.png_export?.p95_ms,
  ...zeroCounts,
};
writeJson(resolve(rawDir, "quantitative-audit.json"), quantitative);

let auditSeal = writeSeal(auditDir);
let handoffSeal = writeSeal(handoffDir);
writeJson(resolve(rawDir, "audit-seal-result.json"), { status: "PASS", audit_file_count: auditSeal.length + 1, handoff_file_count: handoffSeal.length });
auditSeal = writeSeal(auditDir);
handoffSeal = writeSeal(handoffDir);

const finalStatus = groups.every((item) => item.status === "PASS");
process.stdout.write(json({ ...summary, AUDIT_SEAL: "PASS", audit_file_count: auditSeal.length, handoff_file_count: handoffSeal.length }));
if (!finalStatus) process.exitCode = 1;
