#!/usr/bin/env node
/** Measured actual-HTTP workloads for TRACE Exploration v2. */

import { createHash } from "node:crypto";
import { createReadStream } from "node:fs";
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { createInterface } from "node:readline";
import sharp from "sharp";

const DATABASE_SNAPSHOT = "v49:ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e";
const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

function args(argv) {
  const result = {};
  for (let index = 2; index < argv.length; index += 2) {
    const name = argv[index];
    const value = argv[index + 1];
    if (!name?.startsWith("--") || value === undefined) throw new Error(`Invalid argument near ${name}`);
    result[name.slice(2).replaceAll("-", "_")] = value;
  }
  return result;
}

function parseTsv(text) {
  const lines = text.replace(/\n$/u, "").split("\n");
  const fields = lines.shift().split("\t");
  return lines.filter(Boolean).map((line) => Object.fromEntries(fields.map((field, index) => [field, line.split("\t")[index]])));
}

function percentile(sorted, probability) {
  if (!sorted.length) return 0;
  return sorted[Math.min(sorted.length - 1, Math.max(0, Math.ceil(sorted.length * probability) - 1))];
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function parseJsonBuffer(buffer) {
  try { return JSON.parse(buffer.toString("utf8")); } catch { return undefined; }
}

function scenarioFor(mode, concurrency, explicit) {
  if (explicit) return explicit;
  if (mode === "mixed") return "sustained_mixed_load";
  if (mode === "png") return "concurrent_png_load";
  if (mode === "json" && concurrency === 50) return "burst_load";
  if (mode === "json" && concurrency === 1) return "warm_steady_state";
  return "concurrency_scaling";
}

async function loadTransitionSample(file, model, maximumSampleCount = 8_192) {
  const expectedCount = model.transitions?.transition_count;
  if (model.transitions?.derivation_version !== "trace-exploration-derived-transitions-v2"
    || model.transitions?.key_format !== "state_hash|action|target"
    || !Number.isInteger(expectedCount) || expectedCount < 1) {
    throw new Error("Invalid compact transition derivation descriptor");
  }
  const stride = Math.max(1, Math.floor(expectedCount / maximumSampleCount));
  const sample = [];
  const selectedIds = new Set();
  const representedActions = new Set();
  const lines = createInterface({ input: createReadStream(file, { encoding: "utf8" }), crlfDelay: Infinity });
  let fields;
  let rowCount = 0;
  for await (const line of lines) {
    if (!fields) {
      fields = line.split("\t");
      continue;
    }
    if (!line) continue;
    const values = line.split("\t");
    if (values.length !== fields.length) throw new Error(`Transition TSV field mismatch: ${values.length} != ${fields.length}`);
    const row = Object.fromEntries(fields.map((field, index) => [field, values[index]]));
    rowCount += 1;
    const current = model.states[row.current_state_id];
    const next = model.states[row.next_state_id];
    if (!current || !next || current.state_hash !== row.current_state_hash || next.state_hash !== row.next_state_hash
      || row.executed !== "true" || row.passed !== "true" || row.state_mutated !== "false"
      || row.database_snapshot !== DATABASE_SNAPSHOT) {
      throw new Error(`Transition census integrity mismatch: ${row.transition_id}`);
    }
    const firstForAction = !representedActions.has(row.action);
    if ((firstForAction || (rowCount % stride === 0 && sample.length < maximumSampleCount))
      && !selectedIds.has(row.transition_id)) {
      sample.push(row);
      selectedIds.add(row.transition_id);
      representedActions.add(row.action);
    }
  }
  if (rowCount !== expectedCount) throw new Error(`Transition census coverage mismatch: ${rowCount} != ${expectedCount}`);
  const expectedActions = new Set(model.capabilities.actions);
  if (representedActions.size !== expectedActions.size || [...expectedActions].some((action) => !representedActions.has(action))) {
    throw new Error("Transition load sample does not cover every governed action");
  }
  return sample;
}

async function main() {
  const options = args(process.argv);
  const repo = path.resolve(options.repo ?? path.join(import.meta.dirname, "../.."));
  const baseUrl = options.base_url ?? "http://127.0.0.1:3034";
  const mode = options.mode;
  const concurrency = Number(options.concurrency);
  const minimumRequests = Number(options.requests ?? 100);
  const minimumDurationMs = Number(options.minimum_duration_ms ?? 0);
  const requestTimeoutMs = Number(options.timeout_ms ?? 30_000);
  if (!["json", "png", "mixed"].includes(mode) || !options.output || !Number.isInteger(concurrency) || concurrency < 1) throw new Error("known mode/output/positive concurrency required");
  if (!Number.isInteger(minimumRequests) || minimumRequests < 1 || !Number.isFinite(minimumDurationMs) || minimumDurationMs < 0) throw new Error("positive request count and non-negative duration required");
  if (!Number.isFinite(requestTimeoutMs) || requestTimeoutMs <= 0) throw new Error("positive timeout required");
  const model = JSON.parse(await readFile(path.join(repo, "frontend/generated/trace-exploration-v2/production-read-model.json"), "utf8"));
  const exports = parseTsv(await readFile(path.join(repo, "docs/audits/v49-exploration-full-space-closure-round1/raw/export-census-v2.tsv"), "utf8"));
  const states = Object.values(model.states);
  const transitions = await loadTransitionSample(path.join(repo, "docs/audits/v49-exploration-full-space-closure-round1/raw/transition-census-v2.tsv"), model);
  const pngHashes = new Map();
  const jsonDescriptor = (family, route, init, validate, expected = {}) => ({ family, route, init, validate, ...expected });
  const jsonRequests = [
    () => jsonDescriptor("categories", "/api/trace/v2/exploration/categories", {}, (json) => json?.database_snapshot === DATABASE_SNAPSHOT && json?.categories?.length === model.categories.length),
    () => jsonDescriptor("capabilities", "/api/trace/v2/exploration/capabilities", {}, (json) => json?.database_snapshot === DATABASE_SNAPSHOT && json?.state_count === states.length && json?.transition_count === model.transitions.transition_count),
    (index) => {
      const category = model.categories[index % model.categories.length];
      return jsonDescriptor("initial_map", "/api/trace/v2/exploration/maps", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ category_id: category.category_id, category_entry_id: category.category_entry_id, locale: "en" }),
      }, (json) => json?.database_snapshot === DATABASE_SNAPSHOT && json?.map_id === category.category_entry_id && json?.state?.state_id === category.initial_state_id, {
        expectedStateHash: model.states[category.initial_state_id].state_hash,
        expectedSemanticHash: model.states[category.initial_state_id].semantic_hash,
      });
    },
    (index) => {
      const state = states[index % states.length];
      return jsonDescriptor("retrieve_map", `/api/trace/v2/exploration/maps/${encodeURIComponent(state.category_entry_id)}?state_id=${encodeURIComponent(state.state_id)}`, {}, (json) => (
        json?.database_snapshot === DATABASE_SNAPSHOT
        && json?.state?.state_id === state.state_id
        && json?.state?.state_hash === state.state_hash
        && json?.state?.semantic_hash === state.semantic_hash
        && json?.state?.presentation_hash === state.presentation_hash
      ), { expectedStateHash: state.state_hash, expectedSemanticHash: state.semantic_hash });
    },
    (index) => {
      const item = model.vocabulary[index % model.vocabulary.length];
      return jsonDescriptor("vocabulary", `/api/trace/v2/exploration/vocabulary/${encodeURIComponent(item.vocabulary_id)}`, {}, (json) => json?.database_snapshot === DATABASE_SNAPSHOT && json?.vocabulary?.vocabulary_id === item.vocabulary_id);
    },
    (index) => {
      const item = model.associations[index % model.associations.length];
      return jsonDescriptor("association", `/api/trace/v2/exploration/associations/${encodeURIComponent(item.association_id)}`, {}, (json) => json?.database_snapshot === DATABASE_SNAPSHOT && json?.association?.association_id === item.association_id && json?.association?.generic_association_only === true);
    },
    (index) => {
      const transition = transitions[index % transitions.length];
      const state = model.states[transition.current_state_id];
      const next = model.states[transition.next_state_id];
      return jsonDescriptor("browse_action", `/api/trace/v2/exploration/maps/${encodeURIComponent(state.category_entry_id)}/actions`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: transition.action, ...(transition.target_id ? { target_id: transition.target_id } : {}), expected_state_hash: transition.current_state_hash, database_snapshot: state.database_snapshot }),
      }, (json) => json?.database_snapshot === DATABASE_SNAPSHOT && json?.state?.state_id === transition.next_state_id && json?.state?.state_hash === next.state_hash && json?.state?.semantic_hash === next.semantic_hash, {
        expectedStateHash: next.state_hash,
        expectedSemanticHash: next.semantic_hash,
      });
    },
    (index) => {
      const item = exports[index % exports.length];
      return jsonDescriptor("export_manifest", "/api/trace/v2/exploration/exports/manifest", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ map_id: item.category_entry_id, state_hash: item.state_hash, composition_id: item.composition_id, export_preset: item.export_preset, theme_token_set: item.theme_token_set }),
      }, (json) => json?.export_id === item.export_variant_id && json?.state_hash === item.state_hash && json?.semantic_hash === item.semantic_hash && json?.presentation_hash === item.export_presentation_hash, {
        expectedStateHash: item.state_hash,
        expectedSemanticHash: item.semantic_hash,
      });
    },
  ];
  const pngRequest = (index) => {
    const item = exports[index % exports.length];
    return {
      family: "png_export",
      route: "/api/trace/v2/exploration/exports/png",
      init: { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ map_id: item.category_entry_id, state_hash: item.state_hash, composition_id: item.composition_id, export_preset: item.export_preset, theme_token_set: item.theme_token_set }) },
      export: item,
    };
  };
  const select = (index) => {
    if (mode === "json") return jsonRequests[index % jsonRequests.length](index);
    if (mode === "png") return pngRequest(index);
    if (mode === "mixed") return index % 10 === 0 ? pngRequest(index) : jsonRequests[index % jsonRequests.length](index);
    throw new Error(`Unknown mode: ${mode}`);
  };

  const observations = [];
  let issued = 0;
  const started = performance.now();
  const termination = () => issued >= minimumRequests && (performance.now() - started) >= minimumDurationMs;
  async function worker() {
    while (!termination()) {
      const requestIndex = issued;
      issued += 1;
      const selected = select(requestIndex);
      const requestStarted = performance.now();
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(new Error(`REQUEST_TIMEOUT:${requestTimeoutMs}`)), requestTimeoutMs);
      try {
        const response = await fetch(`${baseUrl}${selected.route}`, { ...selected.init, signal: controller.signal });
        const body = Buffer.from(await response.arrayBuffer());
        const httpSuccess = response.status >= 200 && response.status < 300;
        let responseValid = false;
        let validationCode = "";
        let stateHashMatch = true;
        let semanticHashMatch = true;
        let pngDecoded = true;
        if (selected.family === "png_export") {
          const metadata = httpSuccess ? await sharp(body).metadata().catch(() => ({})) : {};
          const contentTypeValid = (response.headers.get("content-type") ?? "").toLowerCase().includes("image/png");
          const signatureValid = body.subarray(0, 8).equals(PNG_SIGNATURE);
          stateHashMatch = response.headers.get("x-trace-state-hash") === selected.export.state_hash;
          semanticHashMatch = response.headers.get("x-trace-semantic-hash") === selected.export.semantic_hash;
          const presentationHashMatch = response.headers.get("x-trace-presentation-hash") === selected.export.export_presentation_hash;
          pngDecoded = metadata.format === "png" && metadata.width === 1080 && metadata.height === 1620;
          const hash = sha256(body);
          const priorHash = pngHashes.get(selected.export.export_variant_id);
          const deterministic = priorHash === undefined || priorHash === hash;
          if (priorHash === undefined) pngHashes.set(selected.export.export_variant_id, hash);
          responseValid = httpSuccess && contentTypeValid && signatureValid && stateHashMatch && semanticHashMatch && presentationHashMatch && pngDecoded && deterministic;
          if (!responseValid) validationCode = "PNG_RESPONSE_INTEGRITY_FAILURE";
        } else {
          const contentTypeValid = (response.headers.get("content-type") ?? "").toLowerCase().includes("application/json");
          const json = parseJsonBuffer(body);
          responseValid = httpSuccess && contentTypeValid && json !== undefined && selected.validate(json);
          if (!responseValid) validationCode = "JSON_RESPONSE_INTEGRITY_FAILURE";
          if (selected.expectedStateHash) {
            stateHashMatch = (json?.state?.state_hash ?? json?.state_hash) === selected.expectedStateHash;
          }
          if (selected.expectedSemanticHash) {
            semanticHashMatch = (json?.state?.semantic_hash ?? json?.semantic_hash) === selected.expectedSemanticHash;
          }
        }
        observations.push({
          index: requestIndex, family: selected.family, route: selected.route, status: response.status,
          success: httpSuccess && responseValid, http_success: httpSuccess, response_valid: responseValid,
          timeout: false, elapsed_ms: performance.now() - requestStarted, response_bytes: body.length,
          state_hash_match: stateHashMatch, semantic_hash_match: semanticHashMatch, png_decoded: pngDecoded,
          validation_code: validationCode, error: "",
        });
      } catch (error) {
        const timeout = controller.signal.aborted || error?.name === "AbortError" || error?.name === "TimeoutError" || String(error).toLowerCase().includes("timeout");
        observations.push({
          index: requestIndex, family: selected.family, route: selected.route, status: 0, success: false,
          http_success: false, response_valid: false, timeout, elapsed_ms: performance.now() - requestStarted,
          response_bytes: 0, state_hash_match: false, semantic_hash_match: false,
          png_decoded: selected.family !== "png_export", validation_code: "CLIENT_REQUEST_FAILURE", error: String(error),
        });
      } finally {
        clearTimeout(timer);
      }
    }
  }
  await Promise.all(Array.from({ length: concurrency }, worker));
  const durationMs = performance.now() - started;
  observations.sort((left, right) => left.index - right.index);
  const latencies = observations.map((item) => item.elapsed_ms).sort((a, b) => a - b);
  const successCount = observations.filter((item) => item.success).length;
  const responseSizes = observations.map((item) => item.response_bytes);
  const responseValidationFailureCount = observations.filter((item) => item.status > 0 && !item.response_valid).length;
  const stateCorruptionCount = observations.filter((item) => item.status > 0 && !item.state_hash_match).length;
  const semanticHashMismatchCount = observations.filter((item) => item.status > 0 && !item.semantic_hash_match).length;
  const pngCorruptionCount = observations.filter((item) => item.family === "png_export" && item.status > 0 && !item.png_decoded).length;
  const output = {
    schema_version: "trace-exploration-http-workload-v2",
    status: successCount === observations.length ? "PASS" : "FAIL",
    workload_id: options.workload_id ?? `${mode}-c${concurrency}`,
    mode,
    scenario: scenarioFor(mode, concurrency, options.scenario),
    concurrency,
    request_timeout_ms: requestTimeoutMs,
    termination_criterion: { minimum_request_count: minimumRequests, minimum_duration_ms: minimumDurationMs, both_required: true },
    started_utc: new Date(Date.now() - durationMs).toISOString(),
    ended_utc: new Date().toISOString(),
    duration_ms: durationMs,
    request_count: observations.length,
    success_count: successCount,
    failure_count: observations.length - successCount,
    http_2xx_count: observations.filter((item) => item.http_success).length,
    timeout_count: observations.filter((item) => item.timeout).length,
    unexpected_5xx_count: observations.filter((item) => item.status >= 500).length,
    server_side_error_count: observations.filter((item) => item.status >= 500).length,
    client_side_error_count: observations.filter((item) => item.error).length,
    response_validation_failure_count: responseValidationFailureCount,
    state_corruption_count: stateCorruptionCount,
    semantic_hash_mismatch_count: semanticHashMismatchCount,
    png_corruption_count: pngCorruptionCount,
    p50_ms: percentile(latencies, 0.50),
    p95_ms: percentile(latencies, 0.95),
    p99_ms: percentile(latencies, 0.99),
    maximum_ms: latencies.at(-1) ?? 0,
    requests_per_second: observations.length / (durationMs / 1000),
    response_bytes: observations.reduce((sum, item) => sum + item.response_bytes, 0),
    response_bytes_mean: responseSizes.reduce((sum, value) => sum + value, 0) / Math.max(1, responseSizes.length),
    response_bytes_minimum: responseSizes.reduce((minimum, value) => Math.min(minimum, value), Number.POSITIVE_INFINITY),
    response_bytes_maximum: responseSizes.reduce((maximum, value) => Math.max(maximum, value), 0),
    client_error_count: observations.filter((item) => item.error).length,
    observations,
  };
  await writeFile(options.output, `${JSON.stringify(output, null, 2)}\n`);
  console.log(JSON.stringify({ workload_id: output.workload_id, request_count: output.request_count, success_count: output.success_count, failure_count: output.failure_count, p95_ms: output.p95_ms, requests_per_second: output.requests_per_second }));
  if (output.status !== "PASS" || output.failure_count || output.timeout_count || output.unexpected_5xx_count
    || output.response_validation_failure_count || output.state_corruption_count
    || output.semantic_hash_mismatch_count || output.png_corruption_count) process.exitCode = 1;
}

await main();
