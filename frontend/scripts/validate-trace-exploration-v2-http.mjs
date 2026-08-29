#!/usr/bin/env node
/** Actual-production HTTP and exhaustive export validation for TRACE v2. */

import { createHash } from "node:crypto";
import { createReadStream } from "node:fs";
import { appendFile, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { createInterface } from "node:readline";
import sharp from "sharp";

const DATABASE_SNAPSHOT = "v49:ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e";
const REQUIRED_PNG_FIELDS = [
  "export_variant_id", "state_id", "theme_token_set", "export_preset",
  "manifest_validated", "manifest_schema_valid", "state_hash_match", "semantic_hash_match",
  "presentation_hash_match", "manifest_sha256", "manifest_replay_sha256", "manifest_replay_match",
  "svg_rendered", "svg_headers_valid", "svg_envelope_valid", "svg_dimensions_valid", "svg_all_labels_valid",
  "svg_all_visible_associations_valid", "svg_provenance_non_claims_valid",
  "svg_zero_archive_object_exposure", "svg_sha256", "svg_replay_sha256", "svg_replay_match",
  "png_rendered", "png_decoded", "png_content_type_valid", "png_headers_valid", "png_metadata_safe", "svg_png_render_match", "width", "height",
  "dimensions_valid", "upper_map_zone_valid", "lower_tree_zone_valid", "all_labels_valid",
  "all_visible_associations_valid", "provenance_summary_valid", "zero_archive_object_exposure",
  "png_sha256", "replay_png_sha256", "replay_match", "map_tree_state_match",
  "http_request_count", "http_status", "elapsed_ms", "error_code",
];

const EXPORT_BOOLEAN_FIELDS = [
  "manifest_validated", "manifest_schema_valid", "state_hash_match", "semantic_hash_match",
  "presentation_hash_match", "manifest_replay_match", "svg_rendered", "svg_headers_valid", "svg_envelope_valid",
  "svg_dimensions_valid", "svg_all_labels_valid", "svg_all_visible_associations_valid",
  "svg_provenance_non_claims_valid", "svg_zero_archive_object_exposure", "svg_replay_match",
  "png_rendered", "png_decoded", "png_content_type_valid", "png_headers_valid", "png_metadata_safe",
  "svg_png_render_match",
  "dimensions_valid", "upper_map_zone_valid", "lower_tree_zone_valid", "all_labels_valid",
  "all_visible_associations_valid", "provenance_summary_valid", "zero_archive_object_exposure",
  "replay_match", "map_tree_state_match",
];

const FUNCTIONAL_LEDGER_FIELDS = [
  "case_id", "case_family", "route", "method", "expected_status", "actual_status", "pass",
  "schema_valid", "contract_valid", "elapsed_ms", "response_bytes", "archive_object_id_count",
  "archive_object_title_count", "record_link_count", "context_reference_count",
  "spacetime_reference_count", "search_reference_count", "error_code",
  "held_data_reference_count",
];

let commonSchema;

function argumentsMap(argv) {
  const result = { input: [] };
  for (let index = 2; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--")) throw new Error(`Unexpected argument: ${token}`);
    const name = token.slice(2).replaceAll("-", "_");
    if (name === "replay") result.replay = true;
    else {
      const value = argv[index + 1];
      if (value === undefined || value.startsWith("--")) throw new Error(`Missing value for ${token}`);
      index += 1;
      if (name === "input") result.input.push(value);
      else result[name] = value;
    }
  }
  return result;
}

function canonicalJson(value) {
  if (value === null || typeof value === "boolean" || typeof value === "number" || typeof value === "string") {
    return JSON.stringify(value) ?? "null";
  }
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(",")}}`;
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function deepEqual(left, right) {
  return canonicalJson(left) === canonicalJson(right);
}

function typeMatches(value, expected) {
  if (expected === "null") return value === null;
  if (expected === "array") return Array.isArray(value);
  if (expected === "object") return value !== null && typeof value === "object" && !Array.isArray(value);
  if (expected === "integer") return Number.isInteger(value);
  if (expected === "number") return typeof value === "number" && Number.isFinite(value);
  return typeof value === expected;
}

function resolveSchemaReference(reference) {
  const marker = "#/$defs/";
  const index = reference.indexOf(marker);
  if (index < 0) throw new Error(`Unsupported schema reference: ${reference}`);
  const name = reference.slice(index + marker.length);
  const resolved = commonSchema?.$defs?.[name];
  if (!resolved) throw new Error(`Unknown schema definition: ${name}`);
  return resolved;
}

function schemaErrors(value, schema, location = "$") {
  if (schema.$ref) return schemaErrors(value, resolveSchemaReference(schema.$ref), location);
  const errors = [];
  if (schema.allOf) {
    for (const child of schema.allOf) errors.push(...schemaErrors(value, child, location));
  }
  if (schema.oneOf) {
    const matches = schema.oneOf.filter((child) => schemaErrors(value, child, location).length === 0).length;
    if (matches !== 1) errors.push(`${location}:oneOf:${matches}`);
  }
  if (schema.const !== undefined && !deepEqual(value, schema.const)) errors.push(`${location}:const`);
  if (schema.enum && !schema.enum.some((item) => deepEqual(value, item))) errors.push(`${location}:enum`);
  if (schema.type !== undefined) {
    const types = Array.isArray(schema.type) ? schema.type : [schema.type];
    if (!types.some((type) => typeMatches(value, type))) return [...errors, `${location}:type`];
  }
  if (typeof value === "string") {
    if (schema.minLength !== undefined && [...value].length < schema.minLength) errors.push(`${location}:minLength`);
    if (schema.maxLength !== undefined && [...value].length > schema.maxLength) errors.push(`${location}:maxLength`);
    if (schema.pattern !== undefined && !(new RegExp(schema.pattern, "u")).test(value)) errors.push(`${location}:pattern`);
  }
  if (typeof value === "number") {
    if (schema.minimum !== undefined && value < schema.minimum) errors.push(`${location}:minimum`);
    if (schema.maximum !== undefined && value > schema.maximum) errors.push(`${location}:maximum`);
  }
  if (Array.isArray(value)) {
    if (schema.minItems !== undefined && value.length < schema.minItems) errors.push(`${location}:minItems`);
    if (schema.maxItems !== undefined && value.length > schema.maxItems) errors.push(`${location}:maxItems`);
    if (schema.uniqueItems && new Set(value.map(canonicalJson)).size !== value.length) errors.push(`${location}:uniqueItems`);
    if (schema.items) value.forEach((item, index) => errors.push(...schemaErrors(item, schema.items, `${location}[${index}]`)));
  }
  if (value !== null && typeof value === "object" && !Array.isArray(value)) {
    const keys = Object.keys(value);
    if (schema.minProperties !== undefined && keys.length < schema.minProperties) errors.push(`${location}:minProperties`);
    for (const required of schema.required ?? []) {
      if (!Object.hasOwn(value, required)) errors.push(`${location}.${required}:required`);
    }
    for (const [key, item] of Object.entries(value)) {
      if (schema.propertyNames) errors.push(...schemaErrors(key, schema.propertyNames, `${location}{key:${key}}`));
      if (schema.properties?.[key]) errors.push(...schemaErrors(item, schema.properties[key], `${location}.${key}`));
      else if (schema.additionalProperties === false) errors.push(`${location}.${key}:additionalProperties`);
      else if (schema.additionalProperties && typeof schema.additionalProperties === "object") {
        errors.push(...schemaErrors(item, schema.additionalProperties, `${location}.${key}`));
      }
    }
  }
  return errors;
}

function validatesDefinition(value, definition) {
  return schemaErrors(value, { $ref: `#/$defs/${definition}` }).length === 0;
}

function parseTsv(text) {
  const lines = text.replace(/\n$/u, "").split("\n");
  const fields = lines.shift().split("\t");
  return lines.filter(Boolean).map((line) => {
    const values = line.split("\t");
    if (values.length !== fields.length) throw new Error(`TSV field mismatch: ${values.length} != ${fields.length}`);
    return Object.fromEntries(fields.map((field, index) => [field, values[index]]));
  });
}

async function* streamTsv(file) {
  const input = createReadStream(file, { encoding: "utf8" });
  const lines = createInterface({ input, crlfDelay: Infinity });
  let fields;
  for await (const line of lines) {
    if (!fields) {
      fields = line.split("\t");
      continue;
    }
    if (!line) continue;
    const values = line.split("\t");
    if (values.length !== fields.length) throw new Error(`TSV field mismatch in ${file}: ${values.length} != ${fields.length}`);
    yield Object.fromEntries(fields.map((field, index) => [field, values[index]]));
  }
  if (!fields) throw new Error(`Empty TSV: ${file}`);
}

function tsvValue(value) {
  return String(value ?? "").replaceAll("\t", " ").replaceAll("\n", "\\n");
}

function encodeTsv(rows, fields) {
  return `${fields.join("\t")}\n${rows.map((row) => fields.map((field) => tsvValue(row[field])).join("\t")).join("\n")}\n`;
}

async function readJson(file) {
  return JSON.parse(await readFile(file, "utf8"));
}

async function pool(items, concurrency, operation) {
  const output = new Array(items.length);
  let cursor = 0;
  async function worker() {
    while (true) {
      const index = cursor;
      cursor += 1;
      if (index >= items.length) return;
      output[index] = await operation(items[index], index);
    }
  }
  await Promise.all(Array.from({ length: Math.min(concurrency, items.length) }, worker));
  return output;
}

function countForbidden(value) {
  const counts = {
    archive_object_id: 0,
    archive_object_title: 0,
    record_link: 0,
    context_reference: 0,
    spacetime_reference: 0,
    search_reference: 0,
    held_data_reference: 0,
  };
  const visit = (item, key = "") => {
    const foldedKey = key.toLowerCase();
    if (/archive[_-]?object[_-]?(id|ref)/u.test(foldedKey) || /^object[_-]?id$/u.test(foldedKey)) counts.archive_object_id += 1;
    if (/archive[_-]?object[_-]?title/u.test(foldedKey) || /^object[_-]?title$/u.test(foldedKey)) counts.archive_object_title += 1;
    if (/^(thumbnail|thumbnail_url|record_card|record_detail_url|related_record_links?)$/u.test(foldedKey)) counts.record_link += 1;
    if (/record[_-]?(link|url|detail)/u.test(foldedKey)) counts.record_link += 1;
    if (/context[_-]?(id|ref)/u.test(foldedKey)) counts.context_reference += 1;
    if (/spacetime[_-]?(id|ref)/u.test(foldedKey)) counts.spacetime_reference += 1;
    if (/search[_-]?(result|manifest|dto|index)/u.test(foldedKey)) counts.search_reference += 1;
    if (/^(?:is_)?held(?:_data|_object|_record)?$/u.test(foldedKey)) counts.held_data_reference += 1;
    if (Array.isArray(item)) item.forEach((child) => visit(child, key));
    else if (item && typeof item === "object") Object.entries(item).forEach(([childKey, child]) => visit(child, childKey));
  };
  visit(value);
  return counts;
}

function forbiddenTextCount(value) {
  const text = String(value).toLowerCase();
  return [
    /archive[_ -]?object[_ -]?(?:id|title|ref)/u,
    /record[_ -]?(?:detail[_ -]?url|card|link)/u,
    /related[_ -]?record/u,
    /(?:context|spacetime)[_ -]?(?:id|ref)/u,
    /(?:search result|search manifest|search index)/u,
    /\/archive\/(?:object|record)s?\//u,
  ].reduce((count, pattern) => count + (pattern.test(text) ? 1 : 0), 0);
}

function xml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

function wrappedLabelLines(label, maximumCodePoints = 18) {
  const words = String(label).split(/\s+/u).filter(Boolean);
  const lines = [];
  let current = "";
  for (const word of words) {
    const proposed = current ? `${current} ${word}` : word;
    if ([...proposed].length <= maximumCodePoints || current.length === 0) current = proposed;
    else {
      lines.push(current);
      current = word;
    }
  }
  if (current) lines.push(current);
  return lines.flatMap((line) => {
    const points = [...line];
    if (points.length <= maximumCodePoints) return [line];
    const chunks = [];
    for (let index = 0; index < points.length; index += maximumCodePoints) {
      chunks.push(points.slice(index, index + maximumCodePoints).join(""));
    }
    return chunks;
  });
}

async function request(baseUrl, route, options = {}, timeoutMs = 30_000) {
  const started = performance.now();
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(new Error(`REQUEST_TIMEOUT:${timeoutMs}`)), timeoutMs);
  try {
    const response = await fetch(`${baseUrl}${route}`, { ...options, signal: controller.signal });
    const bytes = Buffer.from(await response.arrayBuffer());
    const elapsedMs = performance.now() - started;
    let json;
    if ((response.headers.get("content-type") ?? "").includes("application/json")) {
      try { json = JSON.parse(bytes.toString("utf8")); } catch { json = undefined; }
    }
    return { response, bytes, json, elapsedMs };
  } finally {
    clearTimeout(timer);
  }
}

function jsonPost(body) {
  return { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}

async function functionalMode(options, repo, model) {
  const baseUrl = options.base_url ?? "http://127.0.0.1:3034";
  const timeoutMs = Number(options.timeout_ms ?? 30_000);
  const concurrency = Number(options.concurrency ?? 25);
  const outputPath = path.resolve(options.output);
  const ledgerPath = path.resolve(options.case_ledger ?? path.join(path.dirname(outputPath), "api-functional-http-case-ledger-v2.tsv"));
  const cases = [];
  const familyCounters = new Map();
  const aggregateForbidden = countForbidden({});
  let caseCount = 0;
  let passCount = 0;
  let unexpected5xxCount = 0;
  let staleStateAcceptedCount = 0;
  let invalidTargetAcceptedCount = 0;
  await writeFile(ledgerPath, `${FUNCTIONAL_LEDGER_FIELDS.join("\t")}\n`);

  const execute = async ({ caseId, caseFamily, route, requestOptions = {}, expectedStatus, schemaDefinition, validate = () => true }) => {
    try {
      const result = await request(baseUrl, route, requestOptions, timeoutMs);
      const forbidden = result.json ? countForbidden(result.json) : countForbidden({});
      const schemaValid = schemaDefinition ? result.json !== undefined && validatesDefinition(result.json, schemaDefinition) : true;
      let contractValid = false;
      try { contractValid = validate(result) === true; } catch { contractValid = false; }
      const pass = result.response.status === expectedStatus
        && schemaValid
        && contractValid
        && Object.values(forbidden).every((value) => value === 0);
      return {
        case_id: caseId, case_family: caseFamily,
        route,
        method: requestOptions?.method ?? "GET",
        expected_status: expectedStatus,
        actual_status: result.response.status,
        pass,
        schema_valid: schemaValid,
        contract_valid: contractValid,
        elapsed_ms: result.elapsedMs,
        response_bytes: result.bytes.length,
        archive_object_id_count: forbidden.archive_object_id,
        archive_object_title_count: forbidden.archive_object_title,
        record_link_count: forbidden.record_link,
        context_reference_count: forbidden.context_reference,
        spacetime_reference_count: forbidden.spacetime_reference,
        search_reference_count: forbidden.search_reference,
        held_data_reference_count: forbidden.held_data_reference,
        error_code: pass ? "" : (result.json?.code ?? "VALIDATION_FAILURE"),
      };
    } catch (error) {
      return {
        case_id: caseId, case_family: caseFamily, route, method: requestOptions?.method ?? "GET",
        expected_status: expectedStatus, actual_status: 0, pass: false, schema_valid: false,
        contract_valid: false, elapsed_ms: 0, response_bytes: 0, archive_object_id_count: 0,
        archive_object_title_count: 0, record_link_count: 0, context_reference_count: 0,
        spacetime_reference_count: 0, search_reference_count: 0, held_data_reference_count: 0,
        error_code: String(error),
      };
    }
  };

  const commitRows = async (rows) => {
    if (!rows.length) return;
    await appendFile(ledgerPath, encodeTsv(rows, FUNCTIONAL_LEDGER_FIELDS).split("\n").slice(1).join("\n"));
    for (const row of rows) {
      caseCount += 1;
      if (row.pass) passCount += 1;
      if (row.actual_status >= 500) unexpected5xxCount += 1;
      if (row.case_id === "ERROR:STALE_STATE" && row.actual_status === 200) staleStateAcceptedCount += 1;
      if (row.case_id === "ERROR:INVALID_TARGET" && row.actual_status === 200) invalidTargetAcceptedCount += 1;
      for (const key of Object.keys(aggregateForbidden)) {
        const field = `${key}_count`;
        aggregateForbidden[key] += Number(row[field] ?? 0);
      }
      const family = familyCounters.get(row.case_family) ?? { case_count: 0, pass_count: 0, fail_count: 0, elapsed_ms: [], response_bytes: 0 };
      family.case_count += 1;
      family.pass_count += row.pass ? 1 : 0;
      family.fail_count += row.pass ? 0 : 1;
      family.elapsed_ms.push(Number(row.elapsed_ms));
      family.response_bytes += Number(row.response_bytes);
      familyCounters.set(row.case_family, family);
      cases.push({ case_id: row.case_id, pass: row.pass });
    }
  };

  const runCases = async (specifications, requestedConcurrency = concurrency) => {
    const rows = await pool(specifications, requestedConcurrency, execute);
    await commitRows(rows);
  };

  await runCases([
    {
      caseId: "CATEGORIES", caseFamily: "CATEGORIES", route: "/api/trace/v2/exploration/categories",
      expectedStatus: 200, schemaDefinition: "CategoriesResponse",
      validate: ({ json }) => json?.categories?.length === model.categories.length && json?.database_snapshot === DATABASE_SNAPSHOT,
    },
    {
      caseId: "CAPABILITIES", caseFamily: "CAPABILITIES", route: "/api/trace/v2/exploration/capabilities",
      expectedStatus: 200, schemaDefinition: "CapabilitiesResponse",
      validate: ({ json }) => json?.state_count === Object.keys(model.states).length
        && json?.transition_count === model.transitions.transition_count
        && json?.category_entry_count === model.categories.length
        && json?.vocabulary_count === model.vocabulary.length
        && json?.association_count === model.associations.length,
    },
  ], 1);

  await runCases(model.categories.map((category) => ({
    caseId: `CREATE_MAP:${category.category_entry_id}`, caseFamily: "INITIAL_MAP",
    route: "/api/trace/v2/exploration/maps",
    requestOptions: jsonPost({ category_id: category.category_id, category_entry_id: category.category_entry_id, locale: "en" }),
    expectedStatus: 200, schemaDefinition: "MapResponse",
    validate: ({ json }) => json?.map_id === category.category_entry_id
      && json?.state?.state_id === category.initial_state_id
      && json?.state?.state_hash === model.states[category.initial_state_id]?.state_hash,
  })));

  await runCases(Object.values(model.states).sort((left, right) => left.state_id < right.state_id ? -1 : left.state_id > right.state_id ? 1 : 0).map((state) => ({
    caseId: `GET_STATE:${state.state_id}`, caseFamily: "RETRIEVE_MAP",
    route: `/api/trace/v2/exploration/maps/${encodeURIComponent(state.category_entry_id)}?state_id=${encodeURIComponent(state.state_id)}`,
    expectedStatus: 200, schemaDefinition: "MapResponse",
    validate: ({ json }) => json?.state?.state_id === state.state_id
      && json?.state?.state_hash === state.state_hash
      && json?.state?.semantic_hash === state.semantic_hash
      && json?.state?.presentation_hash === state.presentation_hash
      && json?.map_id === state.category_entry_id,
  })));
  await runCases([...model.vocabulary].sort((left, right) => left.vocabulary_id < right.vocabulary_id ? -1 : 1).map((item) => ({
    caseId: `VOCABULARY:${item.vocabulary_id}`, caseFamily: "VOCABULARY",
    route: `/api/trace/v2/exploration/vocabulary/${encodeURIComponent(item.vocabulary_id)}`,
    expectedStatus: 200, schemaDefinition: "VocabularyResponse",
    validate: ({ json }) => json?.vocabulary?.vocabulary_id === item.vocabulary_id
      && json?.vocabulary?.canonical_label === item.canonical_label,
  })));
  await runCases([...model.associations].sort((left, right) => left.association_id < right.association_id ? -1 : 1).map((item) => ({
    caseId: `ASSOCIATION:${item.association_id}`, caseFamily: "ASSOCIATION",
    route: `/api/trace/v2/exploration/associations/${encodeURIComponent(item.association_id)}`,
    expectedStatus: 200, schemaDefinition: "AssociationResponse",
    validate: ({ json }) => json?.association?.association_id === item.association_id
      && json?.association?.generic_association_only === true
      && deepEqual(json?.association?.endpoint_vocabulary_ids, item.endpoint_vocabulary_ids),
  })));

  let transitionOrdinal = 0;
  let transitionBatch = [];
  const transitionCensusPath = path.join(repo, "docs/audits/v49-exploration-full-space-closure-round1/raw/transition-census-v2.tsv");
  for await (const transition of streamTsv(transitionCensusPath)) {
    const current = model.states[transition.current_state_id];
    const nextStateId = transition.next_state_id;
    const next = model.states[nextStateId];
    if (!current || !next
      || current.state_hash !== transition.current_state_hash
      || next.state_hash !== transition.next_state_hash
      || transition.executed !== "true"
      || transition.passed !== "true"
      || transition.state_mutated !== "false"
      || transition.database_snapshot !== DATABASE_SNAPSHOT) {
      throw new Error(`Transition census integrity mismatch: ${transition.transition_id}`);
    }
    transitionOrdinal += 1;
    transitionBatch.push({
      caseId: `TRANSITION:${transition.transition_id}`,
      caseFamily: `ACTION:${transition.action}`,
      route: `/api/trace/v2/exploration/maps/${encodeURIComponent(current.category_entry_id)}/actions`,
      requestOptions: jsonPost({ action: transition.action, ...(transition.target_id ? { target_id: transition.target_id } : {}), expected_state_hash: current.state_hash, database_snapshot: DATABASE_SNAPSHOT }),
      expectedStatus: 200,
      schemaDefinition: "MapResponse",
      validate: ({ json }) => json?.state?.state_id === nextStateId
        && json?.state?.state_hash === next.state_hash
        && json?.state?.semantic_hash === next.semantic_hash
        && json?.state?.presentation_hash === next.presentation_hash
        && json?.map_id === next.category_entry_id,
    });
    if (transitionBatch.length === 1_000) {
      await runCases(transitionBatch);
      transitionBatch = [];
    }
  }
  await runCases(transitionBatch);
  if (transitionOrdinal !== model.transitions.transition_count) {
    throw new Error(`Transition HTTP coverage mismatch: ${transitionOrdinal} != ${model.transitions.transition_count}`);
  }

  const firstState = Object.values(model.states)[0];
  const differentCompositionId = Object.keys(model.compositions).find((id) => id !== firstState.composition_id);
  const actionRoute = `/api/trace/v2/exploration/maps/${encodeURIComponent(firstState.category_entry_id)}/actions`;
  const errorCase = (caseId, route, requestOptions, expectedStatus, code) => ({
    caseId, caseFamily: "DOCUMENTED_ERROR", route, requestOptions, expectedStatus,
    schemaDefinition: "ApiError", validate: ({ json }) => json?.code === code && json?.status === expectedStatus,
  });
  await runCases([
    errorCase("ERROR:STALE_STATE", actionRoute, jsonPost({ action: "FOCUS_NODE", target_id: firstState.focused_node_id, expected_state_hash: "0".repeat(64), database_snapshot: DATABASE_SNAPSHOT }), 409, "STALE_EXPLORATION_STATE"),
    errorCase("ERROR:INVALID_TARGET", actionRoute, jsonPost({ action: "FOCUS_NODE", target_id: "NOT-A-NODE", expected_state_hash: firstState.state_hash, database_snapshot: DATABASE_SNAPSHOT }), 409, "ACTION_NOT_AVAILABLE"),
    errorCase("ERROR:SNAPSHOT", actionRoute, jsonPost({ action: "FOCUS_NODE", target_id: firstState.focused_node_id, expected_state_hash: firstState.state_hash, database_snapshot: "v49:wrong" }), 409, "STATE_DATABASE_VERSION_MISMATCH"),
    errorCase("ERROR:INVALID_ACTION", actionRoute, jsonPost({ action: "INVENTED_ACTION", expected_state_hash: firstState.state_hash }), 400, "INVALID_ACTION"),
    errorCase("ERROR:MALFORMED_JSON", "/api/trace/v2/exploration/maps", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{" }, 400, "INVALID_REQUEST"),
    errorCase("ERROR:BODY_LIMIT", "/api/trace/v2/exploration/maps", jsonPost({ category_id: "region", padding: "x".repeat(70_000) }), 413, "REQUEST_LIMIT_EXCEEDED"),
    errorCase("ERROR:INVALID_CATEGORY", "/api/trace/v2/exploration/maps", jsonPost({ category_id: "not-a-category" }), 404, "INVALID_CATEGORY"),
    errorCase("ERROR:INVALID_CATEGORY_ENTRY", "/api/trace/v2/exploration/maps", jsonPost({ category_id: "region", category_entry_id: "NOT-AN-ENTRY" }), 404, "INVALID_CATEGORY_ENTRY"),
    errorCase("ERROR:INVALID_VOCABULARY", "/api/trace/v2/exploration/vocabulary/NOT-A-VOCABULARY-ID", {}, 404, "INVALID_VOCABULARY"),
    errorCase("ERROR:INVALID_ASSOCIATION", "/api/trace/v2/exploration/associations/NOT-AN-ASSOCIATION-ID", {}, 404, "INVALID_ASSOCIATION"),
    errorCase("ERROR:STATE_NOT_FOUND", "/api/trace/v2/exploration/maps/NOT-A-MAP", {}, 404, "STATE_NOT_FOUND"),
    errorCase("ERROR:METHOD_NOT_ALLOWED", "/api/trace/v2/exploration/categories", { method: "PUT" }, 405, "METHOD_NOT_ALLOWED"),
    errorCase("ERROR:INVALID_EXPORT_PRESET", "/api/trace/v2/exploration/exports/manifest", jsonPost({ map_id: firstState.category_entry_id, state_hash: firstState.state_hash, composition_id: firstState.composition_id, export_preset: "not-a-preset", theme_token_set: "neutral-v1" }), 400, "INVALID_EXPORT_PRESET"),
    errorCase("ERROR:NO_EXPORTABLE_COMPOSITION", "/api/trace/v2/exploration/exports/manifest", jsonPost({ map_id: firstState.category_entry_id, state_hash: firstState.state_hash, composition_id: differentCompositionId, export_preset: "portrait_card", theme_token_set: "neutral-v1" }), 409, "NO_EXPORTABLE_COMPOSITION"),
    {
      caseId: "V1:RETIRED_ROOT", caseFamily: "V1_RETIREMENT", route: "/api/trace/v1/exploration",
      expectedStatus: 410, validate: ({ json, response }) => json?.code === "API_VERSION_RETIRED"
        && json?.successor === "/api/trace/v2/exploration" && response.headers.get("link")?.includes("successor-version"),
    },
    {
      caseId: "V1:RETIRED_NESTED", caseFamily: "V1_RETIREMENT", route: "/api/trace/v1/exploration/categories",
      expectedStatus: 410, validate: ({ json, response }) => json?.code === "API_VERSION_RETIRED"
        && json?.successor === "/api/trace/v2/exploration" && response.headers.get("link")?.includes("successor-version"),
    },
  ]);

  const failCount = caseCount - passCount;
  const output = {
    schema_version: "trace-exploration-api-functional-validation-v2",
    status: passCount === caseCount ? "PASS" : "FAIL",
    api_version: "trace-exploration/v2",
    base_url: baseUrl,
    actual_production_http_tested: true,
    case_count: caseCount,
    pass_count: passCount,
    fail_count: failCount,
    unexpected_5xx_count: unexpected5xxCount,
    stale_state_accepted_count: staleStateAcceptedCount,
    invalid_target_accepted_count: invalidTargetAcceptedCount,
    held_data_leak_count: aggregateForbidden.held_data_reference ?? 0,
    public_archive_object_id_count: aggregateForbidden.archive_object_id ?? 0,
    public_archive_object_title_count: aggregateForbidden.archive_object_title ?? 0,
    public_record_link_count: aggregateForbidden.record_link ?? 0,
    public_context_reference_count: aggregateForbidden.context_reference ?? 0,
    public_spacetime_reference_count: aggregateForbidden.spacetime_reference ?? 0,
    cases,
  };
  await writeFile(options.output, `${JSON.stringify(output, null, 2)}\n`);
  if (output.status !== "PASS") throw new Error(`Functional HTTP validation failed: ${output.fail_count}`);
  console.log(JSON.stringify({
    status: output.status,
    case_count: output.case_count,
    pass_count: output.pass_count,
    transition_http_case_count: transitionOrdinal,
    case_ledger: path.relative(repo, ledgerPath),
    case_family_count: familyCounters.size,
  }));
}

function validManifest(manifest, exportRow, state) {
  return manifest?.manifest_version === "trace-exploration-export-manifest-v2"
    && manifest?.api_version === "trace-exploration/v2"
    && manifest?.export_id === exportRow.export_variant_id
    && manifest?.database_snapshot === DATABASE_SNAPSHOT
    && manifest?.map_id === state.category_entry_id
    && manifest?.state_id === state.state_id
    && manifest?.state_hash === state.state_hash
    && manifest?.category_entry_id === state.category_entry_id
    && manifest?.composition_id === state.composition_id
    && manifest?.seed_id === state.seed_id
    && manifest?.export_preset === exportRow.export_preset
    && manifest?.theme_token_set === exportRow.theme_token_set
    && manifest?.semantic_hash === state.semantic_hash
    && manifest?.presentation_hash === exportRow.export_presentation_hash
    && manifest?.dimensions?.width === 1080
    && manifest?.dimensions?.height === 1620
    && manifest?.node_count === state.visible_node_ids.length
    && manifest?.association_count === state.visible_association_ids.length;
}

function exactSet(left, right) {
  return left.size === right.size && [...left].every((item) => right.has(item));
}

function svgValidation(svgText, manifest) {
  const nodeById = new Map((manifest?.nodes ?? []).map((node) => [node.vocabulary_id, node]));
  const associationGeometryValid = (manifest?.associations ?? []).every((association) => {
    const [leftId, rightId] = association.endpoint_vocabulary_ids;
    const left = nodeById.get(leftId);
    const right = nodeById.get(rightId);
    if (!left || !right) return false;
    const leftX = 136 + (left.position.normalised_x * 808);
    const leftY = 216 + (left.position.normalised_y * 500);
    const rightX = 136 + (right.position.normalised_x * 808);
    const rightY = 216 + (right.position.normalised_y * 500);
    return svgText.includes(`<line x1="${leftX}" y1="${leftY}" x2="${rightX}" y2="${rightY}"`);
  });
  const labelsValid = (manifest?.nodes ?? []).every((node) => (
    svgText.includes(`aria-label="${xml(node.canonical_label)}"`)
    && wrappedLabelLines(node.canonical_label).every((line) => svgText.includes(`>${xml(line)}</tspan>`))
  ));
  const nonClaimsValid = manifest?.provenance_summary?.generic_association_only === true
    && manifest?.provenance_summary?.source_locators_withheld_from_public_export === true
    && (manifest?.associations ?? []).every((association) => (
      association.generic_association_only === true
      && ["causation", "influence", "chronology", "hierarchy", "direction", "equivalence"]
        .every((claim) => association.explicit_non_claims.includes(claim))
    ))
    && svgText.includes("evidence-qualified; no typed relation");
  return {
    envelopeValid: /^<\?xml[^>]*>\s*<svg\b/u.test(svgText) && /<\/svg>\s*$/u.test(svgText),
    dimensionsValid: /<svg\b[^>]*\bwidth="1080"[^>]*\bheight="1620"[^>]*\bviewBox="0 0 1080 1620"/u.test(svgText),
    labelsValid,
    associationsValid: associationGeometryValid,
    provenanceNonClaimsValid: nonClaimsValid,
    zeroForbidden: forbiddenTextCount(svgText) === 0,
  };
}

async function zoneHasContent(buffer, left, top, width, height) {
  const stats = await sharp(buffer).extract({ left, top, width, height }).stats();
  return stats.channels.some((channel) => channel.stdev > 2);
}

async function exportMode(options, repo, model) {
  const baseUrl = options.base_url ?? "http://127.0.0.1:3034";
  const timeoutMs = Number(options.timeout_ms ?? 30_000);
  if (!options.replay) throw new Error("Exhaustive export validation requires --replay");
  const censusPath = path.join(repo, "docs/audits/v49-exploration-full-space-closure-round1/raw/export-census-v2.tsv");
  const census = parseTsv(await readFile(censusPath, "utf8"));
  const start = Number(options.start ?? 0);
  const count = Number(options.count ?? census.length - start);
  const selected = census.slice(start, start + count);
  if (selected.length !== count) throw new Error(`Export partition outside census: ${start}+${count}`);
  const rows = await pool(selected, Number(options.concurrency ?? 2), async (item) => {
    const state = model.states[item.state_id];
    const body = { map_id: item.category_entry_id, state_hash: item.state_hash, composition_id: item.composition_id, export_preset: item.export_preset, theme_token_set: item.theme_token_set };
    const started = performance.now();
    const base = Object.fromEntries(REQUIRED_PNG_FIELDS.map((field) => [field, ""]));
    Object.assign(base, { export_variant_id: item.export_variant_id, state_id: item.state_id, theme_token_set: item.theme_token_set, export_preset: item.export_preset });
    try {
      if (!state) throw new Error(`Unknown export state: ${item.state_id}`);
      const manifestResult = await request(baseUrl, "/api/trace/v2/exploration/exports/manifest", jsonPost(body), timeoutMs);
      const manifest = manifestResult.json;
      const forbidden = countForbidden(manifest ?? {});
      const manifestSchemaValid = manifestResult.response.status === 200 && validatesDefinition(manifest, "ExportManifest");
      const manifestContractValid = manifestResult.response.status === 200 && validManifest(manifest, item, state);
      const manifestHash = sha256(Buffer.from(canonicalJson(manifest)));
      const manifestReplayResult = await request(baseUrl, "/api/trace/v2/exploration/exports/manifest", jsonPost(body), timeoutMs);
      const manifestReplayHash = manifestReplayResult.json === undefined ? "" : sha256(Buffer.from(canonicalJson(manifestReplayResult.json)));
      const vocabularyById = new Map(model.vocabulary.map((row) => [row.vocabulary_id, row]));
      const associationById = new Map(model.associations.map((row) => [row.association_id, row]));
      const expectedLabels = new Map(state.visible_node_ids.map((id) => [id, vocabularyById.get(id)?.canonical_label]));
      const actualLabels = new Map((manifest?.nodes ?? []).map((node) => [node.vocabulary_id, node.canonical_label]));
      const expectedAssociations = new Set(state.visible_association_ids);
      const actualAssociations = new Set((manifest?.associations ?? []).map((association) => association.association_id));
      const labelsValid = expectedLabels.size === actualLabels.size
        && [...expectedLabels].every(([id, label]) => actualLabels.get(id) === label)
        && [...expectedLabels.values()].every((label) => manifest?.plain_text_tree?.plain_text_tree?.includes(label));
      const associationsValid = exactSet(expectedAssociations, actualAssociations)
        && (manifest?.associations ?? []).every((association) => {
          const expected = associationById.get(association.association_id);
          return expected
            && deepEqual(association.endpoint_vocabulary_ids, expected.endpoint_vocabulary_ids)
            && association.support_status === expected.support_status
            && association.generic_association_only === true;
        });
      const provenance = manifest?.provenance_summary;
      const expectedAssociationRows = state.visible_association_ids.map((id) => associationById.get(id));
      const expectedExternal = expectedAssociationRows.filter((row) => row?.support_status === "ACTIVE_EXTERNALLY_SUPPORTED").length;
      const expectedSource = expectedAssociationRows.filter((row) => row?.support_status === "ACTIVE_SOURCE_SUPPORTED").length;
      const provenanceValid = provenance?.association_count === state.visible_association_ids.length
        && provenance?.externally_supported_count === expectedExternal
        && provenance?.source_supported_count === expectedSource
        && provenance?.generic_association_only === true
        && provenance?.source_locators_withheld_from_public_export === true;

      const svgResult = await request(baseUrl, "/api/trace/v2/exploration/export/svg", jsonPost(body), timeoutMs);
      const svgText = svgResult.bytes.toString("utf8");
      const svgChecks = svgValidation(svgText, manifest);
      const svgHash = sha256(svgResult.bytes);
      const svgReplayResult = await request(baseUrl, "/api/trace/v2/exploration/export/svg", jsonPost(body), timeoutMs);
      const svgReplayHash = sha256(svgReplayResult.bytes);
      const svgContentTypeValid = (svgResult.response.headers.get("content-type") ?? "").toLowerCase().includes("image/svg+xml");
      const svgHeadersValid = svgResult.response.headers.get("x-trace-state-hash") === state.state_hash
        && svgResult.response.headers.get("x-trace-semantic-hash") === state.semantic_hash
        && svgResult.response.headers.get("x-trace-presentation-hash") === item.export_presentation_hash
        && svgResult.response.headers.get("x-trace-export-id") === item.export_variant_id
        && svgResult.response.headers.get("content-security-policy") === "default-src 'none'; sandbox"
        && Number(svgResult.response.headers.get("content-length")) === svgResult.bytes.length
        && svgReplayResult.response.headers.get("x-trace-state-hash") === state.state_hash
        && svgReplayResult.response.headers.get("x-trace-semantic-hash") === state.semantic_hash
        && svgReplayResult.response.headers.get("x-trace-presentation-hash") === item.export_presentation_hash
        && svgReplayResult.response.headers.get("x-trace-export-id") === item.export_variant_id;

      const pngResult = await request(baseUrl, "/api/trace/v2/exploration/exports/png", jsonPost(body), timeoutMs);
      const pngMetadata = pngResult.response.status === 200 ? await sharp(pngResult.bytes).metadata() : {};
      const pngHash = sha256(pngResult.bytes);
      const locallyRenderedPng = svgResult.response.status === 200 ? await sharp(Buffer.from(svgText, "utf8"), { density: 144, limitInputPixels: 20_000_000 })
        .resize(1080, 1620, { fit: "fill" })
        .png({ compressionLevel: 9, adaptiveFiltering: false, palette: false })
        .toBuffer() : Buffer.alloc(0);
      const replayResult = await request(baseUrl, "/api/trace/v2/exploration/exports/png", jsonPost(body), timeoutMs);
      const replayHash = sha256(replayResult.bytes);
      const upperValid = pngResult.response.status === 200 && await zoneHasContent(pngResult.bytes, 80, 160, 920, 620);
      const lowerValid = pngResult.response.status === 200 && await zoneHasContent(pngResult.bytes, 80, 850, 920, 600);
      const pngContentTypeValid = (pngResult.response.headers.get("content-type") ?? "").toLowerCase().includes("image/png")
        && pngResult.bytes.subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]));
      const pngHeadersValid = pngResult.response.headers.get("x-trace-state-hash") === state.state_hash
        && pngResult.response.headers.get("x-trace-semantic-hash") === state.semantic_hash
        && pngResult.response.headers.get("x-trace-presentation-hash") === item.export_presentation_hash
        && pngResult.response.headers.get("x-trace-export-id") === item.export_variant_id
        && replayResult.response.headers.get("x-trace-state-hash") === state.state_hash
        && replayResult.response.headers.get("x-trace-semantic-hash") === state.semantic_hash
        && replayResult.response.headers.get("x-trace-presentation-hash") === item.export_presentation_hash
        && replayResult.response.headers.get("x-trace-export-id") === item.export_variant_id;
      const pngMetadataSafe = !pngMetadata.exif && !pngMetadata.icc && !pngMetadata.iptc
        && !pngMetadata.xmp && !(pngMetadata.comments?.length);
      const treeNodes = new Set(manifest?.plain_text_tree?.tree_node_ids ?? []);
      const treeAssociations = new Set(manifest?.plain_text_tree?.visible_association_ids ?? []);
      Object.assign(base, {
        manifest_validated: manifestSchemaValid && manifestContractValid,
        manifest_schema_valid: manifestSchemaValid,
        state_hash_match: manifest?.state_hash === state.state_hash,
        semantic_hash_match: manifest?.semantic_hash === state.semantic_hash,
        presentation_hash_match: manifest?.presentation_hash === item.export_presentation_hash,
        manifest_sha256: manifestHash,
        manifest_replay_sha256: manifestReplayHash,
        manifest_replay_match: manifestReplayResult.response.status === 200
          && validatesDefinition(manifestReplayResult.json, "ExportManifest")
          && manifestHash === manifestReplayHash,
        svg_rendered: svgResult.response.status === 200 && svgContentTypeValid,
        svg_headers_valid: svgHeadersValid,
        svg_envelope_valid: svgChecks.envelopeValid,
        svg_dimensions_valid: svgChecks.dimensionsValid,
        svg_all_labels_valid: svgChecks.labelsValid,
        svg_all_visible_associations_valid: svgChecks.associationsValid,
        svg_provenance_non_claims_valid: svgChecks.provenanceNonClaimsValid,
        svg_zero_archive_object_exposure: svgChecks.zeroForbidden,
        svg_sha256: svgHash,
        svg_replay_sha256: svgReplayHash,
        svg_replay_match: svgReplayResult.response.status === 200 && svgHash === svgReplayHash,
        png_rendered: pngResult.response.status === 200,
        png_decoded: pngMetadata.format === "png",
        png_content_type_valid: pngContentTypeValid,
        png_headers_valid: pngHeadersValid,
        png_metadata_safe: pngMetadataSafe,
        svg_png_render_match: locallyRenderedPng.length > 0 && sha256(locallyRenderedPng) === pngHash,
        width: pngMetadata.width ?? 0,
        height: pngMetadata.height ?? 0,
        dimensions_valid: pngMetadata.width === 1080 && pngMetadata.height === 1620,
        upper_map_zone_valid: upperValid,
        lower_tree_zone_valid: lowerValid,
        all_labels_valid: labelsValid,
        all_visible_associations_valid: associationsValid,
        provenance_summary_valid: provenanceValid,
        zero_archive_object_exposure: Object.values(forbidden).every((value) => value === 0),
        png_sha256: pngHash,
        replay_png_sha256: replayHash,
        replay_match: replayResult.response.status === 200 && pngHash === replayHash,
        map_tree_state_match: manifest?.plain_text_tree?.root_node_id === state.focused_node_id
          && treeNodes.size === expectedLabels.size && state.visible_node_ids.every((id) => treeNodes.has(id))
          && treeAssociations.size === expectedAssociations.size && state.visible_association_ids.every((id) => treeAssociations.has(id)),
        http_request_count: 6,
        http_status: `${manifestResult.response.status};${manifestReplayResult.response.status};${svgResult.response.status};${svgReplayResult.response.status};${pngResult.response.status};${replayResult.response.status}`,
        elapsed_ms: performance.now() - started,
        error_code: "",
      });
    } catch (error) {
      base.error_code = String(error);
      base.elapsed_ms = performance.now() - started;
    }
    if (EXPORT_BOOLEAN_FIELDS.some((field) => base[field] !== true)) base.error_code ||= "EXPORT_VALIDATION_FAILURE";
    return base;
  });
  await writeFile(options.output, encodeTsv(rows, REQUIRED_PNG_FIELDS));
  const failures = rows.filter((row) => row.error_code).length;
  console.log(JSON.stringify({ status: failures === 0 ? "PASS" : "FAIL", start, count: rows.length, failures }));
  if (failures) throw new Error(`Export validation failures: ${failures}`);
}

async function mergePngMode(options, repo) {
  if (!options.input.length) throw new Error("merge-png requires --input shards");
  const census = parseTsv(await readFile(path.join(repo, "docs/audits/v49-exploration-full-space-closure-round1/raw/export-census-v2.tsv"), "utf8"));
  const rows = [];
  for (const input of options.input) {
    const text = await readFile(input, "utf8");
    const header = text.slice(0, text.indexOf("\n")).split("\t");
    if (header.join("|") !== REQUIRED_PNG_FIELDS.join("|")) throw new Error(`PNG shard header mismatch: ${input}`);
    rows.push(...parseTsv(text));
  }
  const byId = new Map();
  for (const row of rows) {
    if (byId.has(row.export_variant_id)) throw new Error(`Duplicate export validation: ${row.export_variant_id}`);
    byId.set(row.export_variant_id, row);
  }
  if (byId.size !== census.length) throw new Error(`PNG validation coverage ${byId.size} != ${census.length}`);
  const ordered = census.map((item) => {
    const row = byId.get(item.export_variant_id);
    if (!row) throw new Error(`Missing export validation: ${item.export_variant_id}`);
    if (row.error_code) throw new Error(`Failed export validation: ${item.export_variant_id}`);
    if (EXPORT_BOOLEAN_FIELDS.some((field) => row[field] !== "true")) {
      throw new Error(`False export gate: ${item.export_variant_id}`);
    }
    if (row.state_id !== item.state_id || row.theme_token_set !== item.theme_token_set || row.export_preset !== item.export_preset) {
      throw new Error(`Export identity mismatch: ${item.export_variant_id}`);
    }
    if (row.http_request_count !== "6" || row.http_status.split(";").length !== 6 || row.http_status.split(";").some((status) => status !== "200")) {
      throw new Error(`Export HTTP coverage mismatch: ${item.export_variant_id}`);
    }
    for (const [left, right, label] of [
      [row.manifest_sha256, row.manifest_replay_sha256, "manifest"],
      [row.svg_sha256, row.svg_replay_sha256, "svg"],
      [row.png_sha256, row.replay_png_sha256, "png"],
    ]) {
      if (!/^[0-9a-f]{64}$/u.test(left) || left !== right) throw new Error(`Export ${label} replay mismatch: ${item.export_variant_id}`);
    }
    return row;
  });
  await writeFile(options.output, encodeTsv(ordered, REQUIRED_PNG_FIELDS));
  console.log(JSON.stringify({ status: "PASS", png_validation_count: ordered.length }));
}

async function main() {
  const options = argumentsMap(process.argv);
  const mode = options.mode;
  if (!mode || !options.output) throw new Error("--mode and --output are required");
  const repo = path.resolve(options.repo ?? path.join(import.meta.dirname, "../.."));
  if (mode === "merge-png") return mergePngMode(options, repo);
  commonSchema = await readJson(path.join(repo, "schemas/trace/exploration/v2/common.schema.json"));
  const model = await readJson(path.join(repo, "frontend/generated/trace-exploration-v2/production-read-model.json"));
  if (mode === "functional") return functionalMode(options, repo, model);
  if (mode === "export") return exportMode(options, repo, model);
  throw new Error(`Unknown mode: ${mode}`);
}

await main();
