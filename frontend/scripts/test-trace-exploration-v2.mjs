#!/usr/bin/env node

import { once } from "node:events";
import { createHash } from "node:crypto";
import { createReadStream, createWriteStream } from "node:fs";
import { mkdir, readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { createInterface } from "node:readline";
import { fileURLToPath } from "node:url";

const SCRIPT_PATH = fileURLToPath(import.meta.url);
const FRONTEND_ROOT = resolve(dirname(SCRIPT_PATH), "..");
const REPO_ROOT = resolve(FRONTEND_ROOT, "..");
const AUDIT_RAW = resolve(REPO_ROOT, "docs/audits/v49-exploration-full-space-closure-round1/raw");
const jiti = createRequire(import.meta.url)("jiti")(import.meta.url, {
  interopDefault: true,
  alias: {
    "@": resolve(FRONTEND_ROOT, "src"),
    "server-only": resolve(FRONTEND_ROOT, "scripts/server-only-marker.mjs"),
  },
});
const SHA256_PATTERN = /^[0-9a-f]{64}$/u;
const PRODUCTION_READ_MODEL_SHA256 = "53eaf59c95446eeb3781a7153183c54b3ff59fd52f21744cc917053959dfdcc9";
const MODEL_KEYS = [
  "associations",
  "capabilities",
  "categories",
  "compositions",
  "database",
  "states",
  "states_by_hash",
  "transitions",
  "vocabulary",
];
const ACTIONS = [
  "SELECT_CATEGORY",
  "FOCUS_NODE",
  "EXPAND_NODE",
  "COLLAPSE_NODE",
  "MOVE_FOCUS",
  "SELECT_COMPOSITION",
  "RESET_CATEGORY",
  "EXPORT_CURRENT_STATE",
];
const ACTION_SET = new Set(ACTIONS);
const CATEGORY_SET = new Set(["region", "theme", "medium", "movement"]);
const THEMES = ["neutral-v1", "neutral-contrast-v1"];
const THEMES_SET = new Set(THEMES);
const EXPORT_PRESET = "portrait_card";
const SUPPORT_STATUSES = ["ACTIVE_EXTERNALLY_SUPPORTED", "ACTIVE_SOURCE_SUPPORTED"];
const SUPPORT_STATUS_SET = new Set(SUPPORT_STATUSES);

const ALLOWED_DATABASE_KEYS = [
  "database_content_sha256",
  "database_identity_sha256",
  "database_schema_version",
  "database_snapshot_id",
  "production_read_model_sha256",
  "release_id",
  "source_sha",
];
const REQUIRED_DATABASE_KEYS = [
  "database_content_sha256",
  "database_identity_sha256",
  "database_schema_version",
  "database_snapshot_id",
  "release_id",
  "source_sha",
];
const ALLOWED_CATEGORY_RECORD_KEYS = [
  "category_entry_id",
  "category_id",
  "composition_ids",
  "description",
  "entry_label",
  "initial_state_id",
  "label",
];
const ALLOWED_VOCABULARY_RECORD_KEYS = [
  "activation_status",
  "ambiguity_note",
  "attested_forms",
  "canonical_label",
  "language",
  "scope_note",
  "vocabulary_id",
];
const ALLOWED_ASSOCIATION_RECORD_KEYS = [
  "association_accessible_description",
  "association_id",
  "confidence",
  "endpoint_labels",
  "endpoint_vocabulary_ids",
  "explicit_non_claims",
  "generic_association_only",
  "strength",
  "support_status",
];
const ALLOWED_COMPOSITION_KEYS = [
  "association_ids",
  "category_entry_id",
  "composition_id",
  "description",
  "label",
  "node_ids",
  "seed_id",
  "seed_node_id",
  "semantic_hash",
  "topology_family",
];
const STATE_KEYS = [
  "available_actions",
  "category_entry_id",
  "composition_id",
  "database_snapshot",
  "expanded_node_ids",
  "focused_node_id",
  "presentation_hash",
  "seed_id",
  "semantic_hash",
  "state_hash",
  "state_id",
  "visible_association_ids",
  "visible_node_ids",
];
const MODEL_CAPABILITIES_KEYS = [
  "actions",
  "api_version",
  "association_count",
  "category_count",
  "category_entry_count",
  "export_presets",
  "export_variant_count",
  "generic_association_only",
  "maximum_node_count",
  "production_composition_count",
  "state_count",
  "themes",
  "topology_composition_count",
  "transition_count",
  "vocabulary_count",
  "workflow_count",
];
const LOCAL_WORKFLOW_ACTION_SET = new Set([
  "FOCUS_NODE",
  "MOVE_FOCUS",
  "EXPAND_NODE",
  "COLLAPSE_NODE",
  "EXPORT_CURRENT_STATE",
]);
const ERROR_DISPOSITIONS = Object.freeze({
  ACTION_NOT_AVAILABLE: [409, false],
  INTERNAL_DATA_INTEGRITY_FAILURE: [503, true],
  INVALID_ACTION: [400, false],
  INVALID_ASSOCIATION: [404, false],
  INVALID_CATEGORY: [404, false],
  INVALID_CATEGORY_ENTRY: [404, false],
  INVALID_EXPORT_PRESET: [400, false],
  INVALID_REQUEST: [400, false],
  INVALID_VOCABULARY: [404, false],
  METHOD_NOT_ALLOWED: [405, false],
  NO_EXPORTABLE_COMPOSITION: [409, false],
  RENDER_CAPACITY_EXCEEDED: [503, true],
  REQUEST_LIMIT_EXCEEDED: [413, false],
  STALE_EXPLORATION_STATE: [409, false],
  STATE_DATABASE_VERSION_MISMATCH: [409, false],
  STATE_NOT_FOUND: [404, false],
});

function usage() {
  return `Usage: node --conditions=react-server --experimental-strip-types scripts/test-trace-exploration-v2.mjs [options]

Inputs:
  --model PATH              Compact production read model
  --transition-census PATH  Exhaustive governed transition TSV
  --workflow-census PATH    Canonical workflow TSV
  --export-census PATH      Export census TSV
  --service-module PATH     TypeScript service module used only for DTO checks
  --renderer-module PATH    TypeScript SVG renderer used for exhaustive export checks
  --skip-service            Skip service/DTO checks

Case-ledger outputs:
  --model-ledger PATH
  --transition-ledger PATH
  --workflow-ledger PATH
  --export-ledger PATH
  --service-ledger PATH
  --summary-json PATH
`;
}

function parseArgs(argv) {
  const defaults = {
    model: resolve(FRONTEND_ROOT, "generated/trace-exploration-v2/production-read-model.json"),
    transitionCensus: resolve(AUDIT_RAW, "transition-census-v2.tsv"),
    workflowCensus: resolve(AUDIT_RAW, "workflow-census-v2.tsv"),
    exportCensus: resolve(AUDIT_RAW, "export-census-v2.tsv"),
    serviceModule: resolve(FRONTEND_ROOT, "src/features/trace-v49/exploration-v2/service.server.ts"),
    rendererModule: resolve(FRONTEND_ROOT, "src/features/trace-v49/exploration-v2/renderer.server.ts"),
    modelLedger: resolve(AUDIT_RAW, "api-v2-model-case-ledger.tsv"),
    transitionLedger: resolve(AUDIT_RAW, "api-v2-transition-case-ledger.tsv"),
    workflowLedger: resolve(AUDIT_RAW, "api-v2-workflow-replay-case-ledger.tsv"),
    exportLedger: resolve(AUDIT_RAW, "api-v2-export-case-ledger.tsv"),
    serviceLedger: resolve(AUDIT_RAW, "api-v2-service-dto-case-ledger.tsv"),
    summaryJson: resolve(AUDIT_RAW, "api-functional-validation-v2.json"),
    skipService: false,
  };
  const optionMap = new Map([
    ["--model", "model"],
    ["--transition-census", "transitionCensus"],
    ["--workflow-census", "workflowCensus"],
    ["--export-census", "exportCensus"],
    ["--service-module", "serviceModule"],
    ["--renderer-module", "rendererModule"],
    ["--model-ledger", "modelLedger"],
    ["--transition-ledger", "transitionLedger"],
    ["--workflow-ledger", "workflowLedger"],
    ["--export-ledger", "exportLedger"],
    ["--service-ledger", "serviceLedger"],
    ["--summary-json", "summaryJson"],
  ]);
  const result = { ...defaults };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--help" || argument === "-h") {
      process.stdout.write(usage());
      process.exit(0);
    }
    if (argument === "--skip-service") {
      result.skipService = true;
      continue;
    }
    const key = optionMap.get(argument);
    if (!key) throw new Error(`UNKNOWN_OPTION:${argument}`);
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`MISSING_OPTION_VALUE:${argument}`);
    result[key] = resolve(REPO_ROOT, value);
    index += 1;
  }
  return result;
}

function invariant(condition, code) {
  if (!condition) throw new Error(code);
}

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function requireRecord(value, code) {
  invariant(isRecord(value), code);
  return value;
}

function requireArray(value, code) {
  invariant(Array.isArray(value), code);
  return value;
}

function requireString(value, code) {
  invariant(typeof value === "string" && value.length > 0, code);
  return value;
}

function requireHash(value, code) {
  invariant(typeof value === "string" && SHA256_PATTERN.test(value), code);
  return value;
}

function exactKeys(value, expected, code) {
  const keys = Object.keys(requireRecord(value, `${code}:NOT_RECORD`)).sort(compareCodePoints);
  const wanted = [...expected].sort(compareCodePoints);
  invariant(keys.length === wanted.length && keys.every((key, index) => key === wanted[index]), `${code}:KEYS:${keys.join(",")}`);
}

function allowedKeys(value, allowed, required, code) {
  const keys = Object.keys(requireRecord(value, `${code}:NOT_RECORD`));
  const allowedSet = new Set(allowed);
  invariant(keys.every((key) => allowedSet.has(key)), `${code}:EXTRA_KEYS:${keys.filter((key) => !allowedSet.has(key)).join(",")}`);
  invariant(required.every((key) => Object.hasOwn(value, key)), `${code}:MISSING_REQUIRED`);
}

function uniqueStrings(value, code, minimum = 0, maximum = Number.POSITIVE_INFINITY) {
  const values = requireArray(value, `${code}:NOT_ARRAY`);
  invariant(values.length >= minimum && values.length <= maximum, `${code}:SIZE`);
  invariant(values.every((item) => typeof item === "string" && item.length > 0), `${code}:NON_STRING`);
  invariant(new Set(values).size === values.length, `${code}:DUPLICATE`);
  return values;
}

function canonicalJson(value) {
  if (value === null || typeof value === "boolean" || typeof value === "number" || typeof value === "string") {
    return JSON.stringify(value) ?? "null";
  }
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  const record = requireRecord(value, "CANONICAL_JSON_NON_RECORD");
  return `{${Object.keys(record).sort(compareCodePoints).map((key) => `${JSON.stringify(key)}:${canonicalJson(record[key])}`).join(",")}}`;
}

function canonicalHash(value) {
  return createHash("sha256").update(canonicalJson(value), "utf8").digest("hex");
}

function deepFreeze(root) {
  if (root === null || typeof root !== "object") return root;
  const pending = [root];
  const visited = new WeakSet();
  while (pending.length > 0) {
    const current = pending.pop();
    if (!current || visited.has(current)) continue;
    visited.add(current);
    for (const value of Object.values(current)) {
      if (value !== null && typeof value === "object") pending.push(value);
    }
    Object.freeze(current);
  }
  return root;
}

function isDeepFrozen(root) {
  if (root === null || typeof root !== "object") return true;
  const pending = [root];
  const visited = new WeakSet();
  while (pending.length > 0) {
    const current = pending.pop();
    if (!current || visited.has(current)) continue;
    visited.add(current);
    if (!Object.isFrozen(current)) return false;
    for (const value of Object.values(current)) {
      if (value !== null && typeof value === "object") pending.push(value);
    }
  }
  return true;
}

function compareCodePoints(left, right) {
  const leftPoints = Array.from(left, (character) => character.codePointAt(0));
  const rightPoints = Array.from(right, (character) => character.codePointAt(0));
  const length = Math.min(leftPoints.length, rightPoints.length);
  for (let index = 0; index < length; index += 1) {
    if (leftPoints[index] !== rightPoints[index]) return leftPoints[index] - rightPoints[index];
  }
  return leftPoints.length - rightPoints.length;
}

function cleanDetail(error) {
  const message = error instanceof Error ? error.message : String(error);
  return message.replace(/[\t\r\n]+/gu, " ").slice(0, 1000);
}

function encodeTsv(value) {
  if (value === undefined || value === null) return "";
  const text = typeof value === "string" ? value : JSON.stringify(value);
  return text.replace(/[\t\r\n]+/gu, " ");
}

class TsvLedger {
  constructor(path, columns) {
    this.path = path;
    this.columns = columns;
    this.stream = undefined;
  }

  async open() {
    await mkdir(dirname(this.path), { recursive: true });
    this.stream = createWriteStream(this.path, { encoding: "utf8", flags: "w" });
    await this.writeRaw(`${this.columns.join("\t")}\n`);
  }

  async write(record) {
    await this.writeRaw(`${this.columns.map((column) => encodeTsv(record[column])).join("\t")}\n`);
  }

  async writeRaw(text) {
    invariant(this.stream, "LEDGER_NOT_OPEN");
    if (!this.stream.write(text)) await once(this.stream, "drain");
  }

  async close() {
    if (!this.stream) return;
    const finished = once(this.stream, "finish");
    this.stream.end();
    await finished;
    this.stream = undefined;
  }
}

function parseTsvLine(line, path, rowNumber) {
  const fields = [];
  let field = "";
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const character = line[index];
    if (quoted) {
      if (character === '"') {
        if (line[index + 1] === '"') {
          field += '"';
          index += 1;
        } else {
          quoted = false;
        }
      } else {
        field += character;
      }
      continue;
    }
    if (character === '"' && field.length === 0) {
      quoted = true;
    } else if (character === "\t") {
      fields.push(field);
      field = "";
    } else {
      field += character;
    }
  }
  invariant(!quoted, `TSV_UNTERMINATED_QUOTE:${path}:${rowNumber}`);
  fields.push(field);
  return fields;
}

async function* readTsv(path) {
  const input = createReadStream(path, { encoding: "utf8" });
  const lines = createInterface({ input, crlfDelay: Number.POSITIVE_INFINITY });
  let headers;
  let rowNumber = 0;
  for await (const line of lines) {
    rowNumber += 1;
    if (rowNumber === 1) {
      headers = parseTsvLine(line.replace(/^\uFEFF/u, ""), path, rowNumber);
      continue;
    }
    if (!line.trim()) continue;
    invariant(headers, `TSV_WITHOUT_HEADER:${path}`);
    const values = parseTsvLine(line, path, rowNumber);
    const row = { __row_number: String(rowNumber) };
    headers.forEach((header, index) => { row[header] = values[index] ?? ""; });
    yield row;
  }
}

function firstValue(row, names) {
  for (const name of names) {
    if (typeof row[name] === "string" && row[name].length > 0) return row[name];
  }
  return undefined;
}

function parseJsonCell(value, code) {
  try {
    return JSON.parse(requireString(value, code));
  } catch (error) {
    throw new Error(`${code}:${cleanDetail(error)}`);
  }
}

function findForbidden(value, path = "$", findings = []) {
  if (Array.isArray(value)) {
    value.forEach((item, index) => findForbidden(item, `${path}[${index}]`, findings));
    return findings;
  }
  if (isRecord(value)) {
    for (const [key, child] of Object.entries(value)) {
      const lower = key.toLowerCase();
      const exactWithholdingFlag = lower === "source_locators_withheld_from_public_export" && child === true;
      if (!exactWithholdingFlag && (
        lower === "search"
        || lower.startsWith("search_")
        || lower === "context"
        || lower.startsWith("context_")
        || lower === "spacetime"
        || lower.startsWith("spacetime_")
        || lower.includes("archive")
        || lower === "surface_id"
        || lower === "folder_id"
        || lower === "folder_title"
        || lower === "object_id"
        || lower === "object_title"
        || lower === "title"
        || lower.includes("record_link")
        || lower.includes("record_url")
        || lower.includes("source_locator")
        || lower === "source_url"
        || lower === "source_urls"
        || lower === "source_ref"
        || lower === "source_refs"
        || lower === "provenance_ref"
        || lower === "provenance_refs"
        || lower === "evidence_ref"
        || lower === "evidence_refs"
        || (lower.startsWith("source_") && ![
          "source_sha",
          "source_supported_count",
          "source_locators_withheld_from_public_export",
        ].includes(lower))
        || lower === "thumbnail"
        || lower === "thumbnail_url"
        || lower === "image_url"
      )) findings.push(`${path}.${key}`);
      findForbidden(child, `${path}.${key}`, findings);
    }
    return findings;
  }
  if (
    typeof value === "string"
    && (
      /(?:^|[^A-Z])(SURF-[A-Z0-9]|FOL-[A-Z0-9]|COMP-SRC-[A-Z0-9]|R14-EVID-[A-Z0-9]|CTX[A-Z]*:|SPTGEO:)|\/(?:surfaces|objects)\//u.test(value)
      || /https?:\/\//iu.test(value)
    )
  ) {
    findings.push(path);
  }
  return findings;
}

function transitionParts(key) {
  const first = key.indexOf("|");
  const second = key.indexOf("|", first + 1);
  invariant(first > 0 && second > first + 1, `TRANSITION_KEY_INVALID:${key}`);
  return {
    stateHash: key.slice(0, first),
    action: key.slice(first + 1, second),
    targetId: key.slice(second + 1),
  };
}

async function runRecordedCase(ledger, counters, record, operation) {
  try {
    const result = await operation();
    counters.pass += 1;
    await ledger.write({ ...record, ...(isRecord(result) ? result : {}), status: "PASS", detail: "" });
    return true;
  } catch (error) {
    counters.fail += 1;
    await ledger.write({ ...record, status: "FAIL", detail: cleanDetail(error) });
    return false;
  }
}

async function validateModel(model, ledger, counters) {
  await runRecordedCase(ledger, counters, { case_type: "MODEL_ROOT", case_id: "root" }, () => {
    exactKeys(model, MODEL_KEYS, "MODEL_ROOT");
    allowedKeys(model.database, ALLOWED_DATABASE_KEYS, REQUIRED_DATABASE_KEYS, "DATABASE_FIELDS");
    requireString(model.database.database_snapshot_id, "DATABASE_SNAPSHOT_MISSING");
    requireHash(model.database.database_content_sha256, "DATABASE_CONTENT_HASH");
    requireHash(model.database.database_identity_sha256, "DATABASE_IDENTITY_HASH");
    invariant(Number.isInteger(model.database.database_schema_version) && model.database.database_schema_version > 0, "DATABASE_SCHEMA_VERSION");
    requireString(model.database.release_id, "DATABASE_RELEASE_ID");
    invariant(typeof model.database.source_sha === "string" && /^(?:[0-9a-f]{40}|[0-9a-f]{64})$/u.test(model.database.source_sha), "DATABASE_SOURCE_SHA");
    if (model.database.production_read_model_sha256 !== undefined) {
      requireHash(model.database.production_read_model_sha256, "DATABASE_PRODUCTION_MODEL_HASH");
    }
    requireArray(model.categories, "CATEGORIES_NOT_ARRAY");
    requireArray(model.vocabulary, "VOCABULARY_NOT_ARRAY");
    requireArray(model.associations, "ASSOCIATIONS_NOT_ARRAY");
    requireRecord(model.compositions, "COMPOSITIONS_NOT_RECORD");
    requireRecord(model.states, "STATES_NOT_RECORD");
    requireRecord(model.states_by_hash, "STATE_HASH_INDEX_NOT_RECORD");
    requireRecord(model.transitions, "TRANSITIONS_NOT_RECORD");
    exactKeys(model.transitions, ["derivation_version", "key_format", "transition_count"], "TRANSITION_DERIVATION_FIELDS");
    invariant(model.transitions.derivation_version === "trace-exploration-derived-transitions-v2", "TRANSITION_DERIVATION_VERSION");
    invariant(model.transitions.key_format === "state_hash|action|target", "TRANSITION_DERIVATION_KEY_FORMAT");
    invariant(Number.isInteger(model.transitions.transition_count) && model.transitions.transition_count > 0, "TRANSITION_DERIVATION_COUNT");
    requireRecord(model.capabilities, "CAPABILITIES_NOT_RECORD");
  });

  const vocabularyIds = new Set();
  const vocabularyById = new Map();
  for (const item of model.vocabulary) {
    const caseId = isRecord(item) && typeof item.vocabulary_id === "string" ? item.vocabulary_id : `row-${vocabularyIds.size + 1}`;
    await runRecordedCase(ledger, counters, { case_type: "VOCABULARY", case_id: caseId }, () => {
      exactKeys(item, ALLOWED_VOCABULARY_RECORD_KEYS, "VOCABULARY_FIELDS");
      allowedKeys(item, ALLOWED_VOCABULARY_RECORD_KEYS, [
        "vocabulary_id", "canonical_label", "attested_forms", "language", "scope_note", "ambiguity_note", "activation_status",
      ], "VOCABULARY_FIELDS");
      requireString(item.vocabulary_id, "VOCABULARY_ID");
      requireString(item.canonical_label, "VOCABULARY_LABEL");
      uniqueStrings(item.attested_forms, "VOCABULARY_ATTESTED_FORMS", 1);
      invariant(item.language === "en", "VOCABULARY_LANGUAGE");
      requireString(item.scope_note, "VOCABULARY_SCOPE_NOTE");
      requireString(item.ambiguity_note, "VOCABULARY_AMBIGUITY_NOTE");
      requireString(item.activation_status, "VOCABULARY_ACTIVATION_STATUS");
      invariant(!vocabularyIds.has(item.vocabulary_id), "VOCABULARY_ID_DUPLICATE");
      vocabularyIds.add(item.vocabulary_id);
      vocabularyById.set(item.vocabulary_id, item);
      invariant(findForbidden(item).length === 0, `VOCABULARY_FORBIDDEN:${findForbidden(item).join(",")}`);
    });
  }

  const associationById = new Map();
  for (const item of model.associations) {
    const caseId = isRecord(item) && typeof item.association_id === "string" ? item.association_id : `row-${associationById.size + 1}`;
    await runRecordedCase(ledger, counters, { case_type: "ASSOCIATION", case_id: caseId }, () => {
      exactKeys(item, ALLOWED_ASSOCIATION_RECORD_KEYS, "ASSOCIATION_FIELDS");
      allowedKeys(item, ALLOWED_ASSOCIATION_RECORD_KEYS, [
        "association_id", "endpoint_vocabulary_ids", "endpoint_labels", "support_status", "strength", "confidence",
        "generic_association_only", "association_accessible_description", "explicit_non_claims",
      ], "ASSOCIATION_FIELDS");
      requireString(item.association_id, "ASSOCIATION_ID");
      const endpoints = uniqueStrings(item.endpoint_vocabulary_ids, "ASSOCIATION_ENDPOINTS", 2, 2);
      invariant(endpoints.every((id) => vocabularyIds.has(id)), "ASSOCIATION_UNKNOWN_ENDPOINT");
      const endpointLabels = uniqueStrings(item.endpoint_labels, "ASSOCIATION_ENDPOINT_LABELS", 2, 2);
      invariant(
        endpointLabels.every((label, index) => label === vocabularyById.get(endpoints[index])?.canonical_label),
        "ASSOCIATION_ENDPOINT_LABEL_MISMATCH",
      );
      invariant(SUPPORT_STATUS_SET.has(item.support_status), "ASSOCIATION_SUPPORT_STATUS_INVALID");
      requireString(item.strength, "ASSOCIATION_STRENGTH");
      requireString(item.confidence, "ASSOCIATION_CONFIDENCE");
      invariant(item.generic_association_only === true, "ASSOCIATION_GENERIC_BOUNDARY");
      requireString(item.association_accessible_description, "ASSOCIATION_DESCRIPTION");
      uniqueStrings(item.explicit_non_claims, "ASSOCIATION_NON_CLAIMS", 1);
      invariant(!associationById.has(item.association_id), "ASSOCIATION_ID_DUPLICATE");
      associationById.set(item.association_id, item);
      invariant(findForbidden(item).length === 0, `ASSOCIATION_FORBIDDEN:${findForbidden(item).join(",")}`);
    });
  }

  const compositionById = new Map();
  const compositionAdjacencyById = new Map();
  for (const [key, item] of Object.entries(model.compositions)) {
    await runRecordedCase(ledger, counters, { case_type: "COMPOSITION", case_id: key }, () => {
      exactKeys(item, ALLOWED_COMPOSITION_KEYS, "COMPOSITION_FIELDS");
      allowedKeys(item, ALLOWED_COMPOSITION_KEYS, [
        "composition_id", "category_entry_id", "seed_id", "seed_node_id", "node_ids", "association_ids",
        "topology_family", "semantic_hash", "label", "description",
      ], "COMPOSITION_FIELDS");
      invariant(item.composition_id === key, "COMPOSITION_KEY_MISMATCH");
      const nodeIds = uniqueStrings(item.node_ids, "COMPOSITION_NODES", 2, 8);
      const edgeIds = uniqueStrings(item.association_ids, "COMPOSITION_ASSOCIATIONS", 1);
      invariant(nodeIds.every((id) => vocabularyIds.has(id)), "COMPOSITION_UNKNOWN_NODE");
      invariant(edgeIds.every((id) => associationById.has(id)), "COMPOSITION_UNKNOWN_ASSOCIATION");
      const adjacency = new Map(nodeIds.map((nodeId) => [nodeId, new Set()]));
      for (const edgeId of edgeIds) {
        const [leftId, rightId] = associationById.get(edgeId).endpoint_vocabulary_ids;
        invariant(nodeIds.includes(leftId) && nodeIds.includes(rightId), "COMPOSITION_EDGE_OUTSIDE_NODES");
        adjacency.get(leftId).add(rightId);
        adjacency.get(rightId).add(leftId);
      }
      invariant(nodeIds.includes(item.seed_node_id), "COMPOSITION_SEED_NODE_OUTSIDE_NODES");
      const visited = new Set();
      const queue = [nodeIds[0]];
      while (queue.length > 0) {
        const nodeId = queue.shift();
        if (!nodeId || visited.has(nodeId)) continue;
        visited.add(nodeId);
        for (const neighbour of adjacency.get(nodeId) ?? []) if (!visited.has(neighbour)) queue.push(neighbour);
      }
      invariant(visited.size === nodeIds.length, "COMPOSITION_GRAPH_DISCONNECTED");
      requireString(item.category_entry_id, "COMPOSITION_CATEGORY_ENTRY");
      requireString(item.seed_id, "COMPOSITION_SEED");
      requireString(item.topology_family, "COMPOSITION_TOPOLOGY");
      requireHash(item.semantic_hash, "COMPOSITION_SEMANTIC_HASH");
      requireString(item.label, "COMPOSITION_LABEL");
      requireString(item.description, "COMPOSITION_DESCRIPTION");
      invariant(!compositionById.has(key), "COMPOSITION_ID_DUPLICATE");
      compositionById.set(key, item);
      compositionAdjacencyById.set(key, adjacency);
      invariant(findForbidden(item).length === 0, `COMPOSITION_FORBIDDEN:${findForbidden(item).join(",")}`);
    });
  }

  const categoryByEntry = new Map();
  const observedCategories = new Set();
  for (const item of model.categories) {
    const caseId = isRecord(item) && typeof item.category_entry_id === "string" ? item.category_entry_id : `row-${categoryByEntry.size + 1}`;
    await runRecordedCase(ledger, counters, { case_type: "CATEGORY_ENTRY", case_id: caseId }, () => {
      exactKeys(item, ALLOWED_CATEGORY_RECORD_KEYS, "CATEGORY_FIELDS");
      invariant(CATEGORY_SET.has(item.category_id), "CATEGORY_ID_INVALID");
      requireString(item.category_entry_id, "CATEGORY_ENTRY_ID");
      requireString(item.label, "CATEGORY_LABEL");
      requireString(item.entry_label, "CATEGORY_ENTRY_LABEL");
      requireString(item.description, "CATEGORY_DESCRIPTION");
      const compositionIds = uniqueStrings(item.composition_ids, "CATEGORY_COMPOSITIONS", 1);
      invariant(compositionIds.every((id) => compositionById.get(id)?.category_entry_id === item.category_entry_id), "CATEGORY_COMPOSITION_MISMATCH");
      requireString(item.initial_state_id, "CATEGORY_INITIAL_STATE");
      invariant(!categoryByEntry.has(item.category_entry_id), "CATEGORY_ENTRY_DUPLICATE");
      categoryByEntry.set(item.category_entry_id, item);
      observedCategories.add(item.category_id);
      invariant(findForbidden(item).length === 0, `CATEGORY_FORBIDDEN:${findForbidden(item).join(",")}`);
    });
  }
  await runRecordedCase(ledger, counters, { case_type: "CATEGORY_SET", case_id: "four-categories" }, () => {
    invariant(observedCategories.size === 4 && [...CATEGORY_SET].every((id) => observedCategories.has(id)), "FOUR_CATEGORY_CONTRACT_FAILED");
  });
  for (const composition of compositionById.values()) {
    await runRecordedCase(ledger, counters, { case_type: "COMPOSITION_CATEGORY_REVERSE", case_id: composition.composition_id }, () => {
      const category = categoryByEntry.get(composition.category_entry_id);
      invariant(category && category.composition_ids.includes(composition.composition_id), "COMPOSITION_ORPHANED_FROM_CATEGORY");
    });
  }

  const stateById = new Map();
  const stateHashSet = new Set();
  for (const [key, item] of Object.entries(model.states)) {
    await runRecordedCase(ledger, counters, { case_type: "STATE", case_id: key }, () => {
      exactKeys(item, STATE_KEYS, "STATE_FIELDS");
      invariant(item.state_id === key, "STATE_KEY_MISMATCH");
      requireHash(item.state_hash, "STATE_HASH");
      invariant(!stateHashSet.has(item.state_hash), "STATE_HASH_DUPLICATE");
      stateHashSet.add(item.state_hash);
      const category = categoryByEntry.get(item.category_entry_id);
      const composition = compositionById.get(item.composition_id);
      const adjacency = compositionAdjacencyById.get(item.composition_id);
      invariant(category, "STATE_UNKNOWN_CATEGORY_ENTRY");
      invariant(composition && composition.category_entry_id === item.category_entry_id, "STATE_COMPOSITION_MISMATCH");
      invariant(category.composition_ids.includes(item.composition_id), "STATE_COMPOSITION_NOT_EXPOSED_BY_CATEGORY");
      invariant(adjacency, "STATE_COMPOSITION_ADJACENCY_MISSING");
      invariant(composition.seed_id === item.seed_id, "STATE_SEED_MISMATCH");
      const visibleNodes = uniqueStrings(item.visible_node_ids, "STATE_VISIBLE_NODES", 1, 8);
      const visibleEdges = uniqueStrings(item.visible_association_ids, "STATE_VISIBLE_ASSOCIATIONS");
      const expandedNodes = uniqueStrings(item.expanded_node_ids, "STATE_EXPANDED_NODES");
      invariant(visibleNodes.includes(item.focused_node_id), "STATE_FOCUS_NOT_VISIBLE");
      invariant(visibleNodes.every((id) => composition.node_ids.includes(id)), "STATE_NODE_OUTSIDE_COMPOSITION");
      invariant(expandedNodes.every((id) => composition.node_ids.includes(id)), "STATE_EXPANDED_NODE_OUTSIDE_COMPOSITION");
      invariant(expandedNodes.every((id) => visibleNodes.includes(id)), "STATE_EXPANDED_NODE_NOT_VISIBLE");
      invariant(visibleEdges.every((id) => composition.association_ids.includes(id)), "STATE_ASSOCIATION_OUTSIDE_COMPOSITION");
      for (const edgeId of visibleEdges) {
        invariant(associationById.get(edgeId).endpoint_vocabulary_ids.every((id) => visibleNodes.includes(id)), "STATE_VISIBLE_EDGE_ENDPOINT_HIDDEN");
      }
      const availableActions = uniqueStrings(item.available_actions, "STATE_AVAILABLE_ACTIONS");
      invariant(availableActions.every((action) => ACTION_SET.has(action)), "STATE_UNKNOWN_ACTION");
      requireHash(item.semantic_hash, "STATE_SEMANTIC_HASH");
      requireHash(item.presentation_hash, "STATE_PRESENTATION_HASH");
      invariant(item.semantic_hash === composition.semantic_hash, "STATE_SEMANTIC_COMPOSITION_MISMATCH");
      const expectedVisible = new Set([item.focused_node_id, ...expandedNodes]);
      for (const neighbour of adjacency.get(item.focused_node_id) ?? []) expectedVisible.add(neighbour);
      for (const expandedNodeId of expandedNodes) {
        for (const neighbour of adjacency.get(expandedNodeId) ?? []) expectedVisible.add(neighbour);
      }
      const expectedVisibleNodes = [...expectedVisible].sort(compareCodePoints);
      invariant(
        visibleNodes.length === expectedVisibleNodes.length
        && visibleNodes.every((id, index) => id === expectedVisibleNodes[index]),
        "STATE_VISIBLE_NODE_DERIVATION_MISMATCH",
      );
      const expectedVisibleEdges = composition.association_ids.filter((associationId) => (
        associationById.get(associationId).endpoint_vocabulary_ids.every((id) => expectedVisible.has(id))
      )).sort(compareCodePoints);
      invariant(
        visibleEdges.length === expectedVisibleEdges.length
        && visibleEdges.every((id, index) => id === expectedVisibleEdges[index]),
        "STATE_VISIBLE_ASSOCIATION_DERIVATION_MISMATCH",
      );
      const localTargetCounts = {
        FOCUS_NODE: composition.node_ids.length,
        MOVE_FOCUS: adjacency.get(item.focused_node_id)?.size ?? 0,
        EXPAND_NODE: visibleNodes.filter((id) => !expandedNodes.includes(id)).length,
        COLLAPSE_NODE: expandedNodes.length,
      };
      const expectedActions = ACTIONS.filter((action) => (
        !Object.hasOwn(localTargetCounts, action) || localTargetCounts[action] > 0
      ));
      invariant(
        availableActions.length === expectedActions.length
        && availableActions.every((action, index) => action === expectedActions[index]),
        "STATE_AVAILABLE_ACTION_DERIVATION_MISMATCH",
      );
      const presentationIdentity = {
        category_entry_id: item.category_entry_id,
        production_composition_id: item.composition_id,
        seed_id: item.seed_id,
        focused_node_id: item.focused_node_id,
        expanded_node_ids: expandedNodes,
        visible_node_ids: visibleNodes,
        visible_association_ids: visibleEdges,
        database_snapshot: item.database_snapshot,
      };
      invariant(canonicalHash(presentationIdentity) === item.presentation_hash, "STATE_PRESENTATION_HASH_DERIVATION_MISMATCH");
      invariant(
        canonicalHash({ ...presentationIdentity, semantic_hash: item.semantic_hash, presentation_hash: item.presentation_hash }) === item.state_hash,
        "STATE_HASH_DERIVATION_MISMATCH",
      );
      invariant(item.database_snapshot === model.database.database_snapshot_id, "STATE_DATABASE_SNAPSHOT_MISMATCH");
      invariant(model.states_by_hash[item.state_hash] === item.state_id, "STATE_HASH_INDEX_MISMATCH");
      stateById.set(key, item);
      invariant(findForbidden(item).length === 0, `STATE_FORBIDDEN:${findForbidden(item).join(",")}`);
    });
  }

  for (const [stateHash, stateId] of Object.entries(model.states_by_hash)) {
    await runRecordedCase(ledger, counters, { case_type: "STATE_HASH_INDEX", case_id: stateHash }, () => {
      requireHash(stateHash, "STATE_HASH_INDEX_KEY");
      invariant(stateById.get(stateId)?.state_hash === stateHash, "STATE_HASH_INDEX_TARGET");
    });
  }
  await runRecordedCase(ledger, counters, { case_type: "STATE_HASH_INDEX", case_id: "cardinality" }, () => {
    invariant(Object.keys(model.states_by_hash).length === stateById.size, "STATE_HASH_INDEX_CARDINALITY");
  });
  for (const category of categoryByEntry.values()) {
    await runRecordedCase(ledger, counters, { case_type: "INITIAL_STATE", case_id: category.category_entry_id }, () => {
      const initial = stateById.get(category.initial_state_id);
      const expectedCompositionId = [...category.composition_ids].sort(compareCodePoints)[0];
      const composition = compositionById.get(expectedCompositionId);
      invariant(initial?.category_entry_id === category.category_entry_id, "INITIAL_STATE_CATEGORY_MISMATCH");
      invariant(initial.composition_id === expectedCompositionId, "INITIAL_STATE_COMPOSITION_MISMATCH");
      invariant(composition && initial.focused_node_id === composition.seed_node_id, "INITIAL_STATE_FOCUS_NOT_SEED");
      invariant(initial.expanded_node_ids.length === 0, "INITIAL_STATE_NOT_COLLAPSED");
    });
  }
  await runRecordedCase(ledger, counters, { case_type: "MODEL_CAPABILITIES", case_id: "counts-and-domains" }, () => {
    const capabilities = requireRecord(model.capabilities, "MODEL_CAPABILITIES_RECORD");
    exactKeys(capabilities, MODEL_CAPABILITIES_KEYS, "MODEL_CAPABILITIES_FIELDS");
    invariant(capabilities.api_version === "trace-exploration/v2", "MODEL_CAPABILITIES_API_VERSION");
    invariant(capabilities.category_count === CATEGORY_SET.size, "MODEL_CAPABILITIES_CATEGORY_COUNT");
    invariant(capabilities.category_entry_count === 81, "MODEL_CAPABILITIES_EXACT_CATEGORY_ENTRY_COUNT");
    invariant(capabilities.vocabulary_count === 31, "MODEL_CAPABILITIES_EXACT_VOCABULARY_COUNT");
    invariant(capabilities.association_count === 21, "MODEL_CAPABILITIES_EXACT_ASSOCIATION_COUNT");
    invariant(capabilities.topology_composition_count === 81, "MODEL_CAPABILITIES_EXACT_TOPOLOGY_COUNT");
    invariant(capabilities.production_composition_count === 228, "MODEL_CAPABILITIES_EXACT_COMPOSITION_COUNT");
    invariant(capabilities.state_count === 5_760, "MODEL_CAPABILITIES_EXACT_STATE_COUNT");
    invariant(capabilities.transition_count === 749_944, "MODEL_CAPABILITIES_EXACT_TRANSITION_COUNT");
    invariant(capabilities.workflow_count === 5_760, "MODEL_CAPABILITIES_EXACT_WORKFLOW_COUNT");
    invariant(capabilities.export_variant_count === 11_520, "MODEL_CAPABILITIES_EXACT_EXPORT_COUNT");
    invariant(capabilities.category_entry_count === categoryByEntry.size, "MODEL_CAPABILITIES_CATEGORY_ENTRY_COUNT");
    invariant(capabilities.vocabulary_count === vocabularyIds.size, "MODEL_CAPABILITIES_VOCABULARY_COUNT");
    invariant(capabilities.association_count === associationById.size, "MODEL_CAPABILITIES_ASSOCIATION_COUNT");
    invariant(capabilities.production_composition_count === compositionById.size, "MODEL_CAPABILITIES_COMPOSITION_COUNT");
    invariant(Number.isInteger(capabilities.topology_composition_count) && capabilities.topology_composition_count > 0, "MODEL_CAPABILITIES_TOPOLOGY_COUNT");
    invariant(capabilities.state_count === stateById.size, "MODEL_CAPABILITIES_STATE_COUNT");
    invariant(capabilities.transition_count === model.transitions.transition_count, "MODEL_CAPABILITIES_TRANSITION_COUNT");
    invariant(capabilities.workflow_count === stateById.size, "MODEL_CAPABILITIES_WORKFLOW_COUNT");
    invariant(
      capabilities.export_variant_count === stateById.size * THEMES.length,
      "MODEL_CAPABILITIES_EXPORT_COUNT",
    );
    invariant(canonicalJson(capabilities.actions) === canonicalJson(ACTIONS), "MODEL_CAPABILITIES_ACTIONS");
    invariant(canonicalJson(capabilities.themes) === canonicalJson(THEMES), "MODEL_CAPABILITIES_THEMES");
    invariant(canonicalJson(capabilities.export_presets) === canonicalJson([EXPORT_PRESET]), "MODEL_CAPABILITIES_EXPORT_PRESETS");
    invariant(capabilities.maximum_node_count === 8, "MODEL_CAPABILITIES_NODE_BOUND");
    invariant(capabilities.generic_association_only === true, "MODEL_CAPABILITIES_GENERIC_BOUNDARY");
  });
  await runRecordedCase(ledger, counters, { case_type: "PUBLIC_BOUNDARY", case_id: "production-model" }, () => {
    const findings = findForbidden(model);
    invariant(findings.length === 0, `FORBIDDEN_PUBLIC_FIELDS:${findings.slice(0, 20).join(",")}`);
  });
  const forbiddenFixtures = [
    ["folder-identifier", { note: "FOL-EXAMPLE-001" }],
    ["surface-identifier", { note: "SURF-EXAMPLE-001" }],
    ["source-locator-key", { source_locator: "withheld" }],
    ["source-url-key", { source_url: "withheld" }],
    ["record-link-key", { record_links: ["withheld"] }],
    ["archive-title-key", { archive_title: "withheld" }],
    ["web-locator-value", { note: "https://example.invalid/source" }],
  ];
  for (const [caseId, fixture] of forbiddenFixtures) {
    await runRecordedCase(ledger, counters, { case_type: "PUBLIC_BOUNDARY_NEGATIVE", case_id: caseId }, () => {
      invariant(findForbidden(fixture).length > 0, "FORBIDDEN_DETECTOR_FALSE_NEGATIVE");
    });
  }
  return { vocabularyIds, vocabularyById, associationById, compositionById, compositionAdjacencyById, categoryByEntry, stateById };
}

function governedRootStateIdForCategory(categoryId, categoryByEntry) {
  const entries = [...categoryByEntry.values()]
    .filter((category) => category.category_id === categoryId)
    .sort((left, right) => compareCodePoints(left.category_entry_id, right.category_entry_id));
  invariant(entries.length > 0, `CATEGORY_ROOT_MISSING:${categoryId}`);
  return entries[0].initial_state_id;
}

function validateActionInvariant(action, targetId, current, next, indexes) {
  invariant(current.database_snapshot === next.database_snapshot, "TRANSITION_DATABASE_CHANGED");
  if (["FOCUS_NODE", "MOVE_FOCUS", "EXPAND_NODE", "COLLAPSE_NODE"].includes(action)) {
    invariant(current.category_entry_id === next.category_entry_id, "INTERACTION_CATEGORY_CHANGED");
    invariant(current.composition_id === next.composition_id, "INTERACTION_COMPOSITION_CHANGED");
    invariant(current.semantic_hash === next.semantic_hash, "INTERACTION_SEMANTIC_HASH_CHANGED");
  }
  if (action === "FOCUS_NODE" || action === "MOVE_FOCUS") {
    invariant(next.focused_node_id === targetId, "FOCUS_TARGET_MISMATCH");
    invariant(canonicalJson(next.expanded_node_ids) === canonicalJson(current.expanded_node_ids), "FOCUS_EXPANSION_CHANGED");
  }
  if (action === "EXPAND_NODE") {
    invariant(next.focused_node_id === current.focused_node_id, "EXPAND_FOCUS_CHANGED");
    invariant(
      canonicalJson(next.expanded_node_ids) === canonicalJson([...new Set([...current.expanded_node_ids, targetId])].sort(compareCodePoints)),
      "EXPAND_SET_MISMATCH",
    );
  }
  if (action === "COLLAPSE_NODE") {
    invariant(next.focused_node_id === current.focused_node_id, "COLLAPSE_FOCUS_CHANGED");
    invariant(
      canonicalJson(next.expanded_node_ids) === canonicalJson(current.expanded_node_ids.filter((id) => id !== targetId)),
      "COLLAPSE_SET_MISMATCH",
    );
  }
  if (action === "SELECT_COMPOSITION") {
    invariant(next.composition_id === targetId, "SELECT_COMPOSITION_TARGET_MISMATCH");
    const currentCategory = indexes.categoryByEntry.get(current.category_entry_id);
    const nextCategory = indexes.categoryByEntry.get(next.category_entry_id);
    const nextComposition = indexes.compositionById.get(next.composition_id);
    invariant(currentCategory?.category_id === nextCategory?.category_id, "SELECT_COMPOSITION_CATEGORY_CHANGED");
    invariant(nextComposition && next.focused_node_id === nextComposition.seed_node_id, "SELECT_COMPOSITION_ROOT_FOCUS");
    invariant(next.expanded_node_ids.length === 0, "SELECT_COMPOSITION_ROOT_EXPANSION");
  }
  if (action === "SELECT_CATEGORY") {
    invariant(CATEGORY_SET.has(targetId), "SELECT_CATEGORY_TARGET_MISMATCH");
    invariant(next.state_id === governedRootStateIdForCategory(targetId, indexes.categoryByEntry), "SELECT_CATEGORY_ROOT_MISMATCH");
  }
  if (action === "RESET_CATEGORY") {
    const categoryId = indexes.categoryByEntry.get(current.category_entry_id)?.category_id;
    invariant(targetId === "", "RESET_TARGET_NOT_EMPTY");
    invariant(categoryId && next.state_id === governedRootStateIdForCategory(categoryId, indexes.categoryByEntry), "RESET_TARGET_MISMATCH");
  }
  if (action === "EXPORT_CURRENT_STATE") {
    invariant(targetId === "", "EXPORT_TARGET_NOT_EMPTY");
    invariant(next.state_id === current.state_id, "EXPORT_TRANSITION_NOT_SELF_LOOP");
  }
}

function derivedStateKey(compositionId, focusedNodeId, expandedNodeIds) {
  return canonicalJson([compositionId, focusedNodeId, [...expandedNodeIds].sort(compareCodePoints)]);
}

function buildDerivedTransitionIndex(model, indexes) {
  const stateByKey = new Map();
  const rootByComposition = new Map();
  const compositionIdsByCategory = new Map([...CATEGORY_SET].map((categoryId) => [categoryId, []]));
  for (const composition of indexes.compositionById.values()) {
    const categoryId = indexes.categoryByEntry.get(composition.category_entry_id)?.category_id;
    invariant(categoryId, "DERIVED_TRANSITION_COMPOSITION_CATEGORY_MISSING");
    compositionIdsByCategory.get(categoryId).push(composition.composition_id);
  }
  for (const compositionIds of compositionIdsByCategory.values()) compositionIds.sort(compareCodePoints);
  for (const state of indexes.stateById.values()) {
    const key = derivedStateKey(state.composition_id, state.focused_node_id, state.expanded_node_ids);
    invariant(!stateByKey.has(key), "DERIVED_TRANSITION_STATE_KEY_DUPLICATE");
    stateByKey.set(key, state);
  }
  for (const composition of indexes.compositionById.values()) {
    const compositionStates = [...indexes.stateById.values()].filter((state) => state.composition_id === composition.composition_id);
    invariant(
      compositionStates.length === composition.node_ids.length * (2 ** composition.node_ids.length),
      "DERIVED_TRANSITION_INCOMPLETE_STATE_PRODUCT",
    );
    const root = stateByKey.get(derivedStateKey(composition.composition_id, composition.seed_node_id, []));
    invariant(root, "DERIVED_TRANSITION_COMPOSITION_ROOT_MISSING");
    rootByComposition.set(composition.composition_id, root);
  }
  const derived = { stateByKey, rootByComposition, compositionIdsByCategory, transitionCount: 0 };
  for (const state of indexes.stateById.values()) {
    for (const action of ACTIONS) derived.transitionCount += expectedTransitionTargets(action, state, indexes, derived).length;
  }
  return derived;
}

function expectedTransitionTargets(action, state, indexes, derived) {
  const composition = indexes.compositionById.get(state.composition_id);
  const adjacency = indexes.compositionAdjacencyById.get(state.composition_id);
  invariant(composition && adjacency, "TRANSITION_COVERAGE_COMPOSITION_MISSING");
  if (action === "SELECT_CATEGORY") return [...CATEGORY_SET];
  if (action === "FOCUS_NODE") return [...composition.node_ids];
  if (action === "MOVE_FOCUS") return [...(adjacency.get(state.focused_node_id) ?? [])];
  if (action === "EXPAND_NODE") return state.visible_node_ids.filter((id) => !state.expanded_node_ids.includes(id));
  if (action === "COLLAPSE_NODE") return [...state.expanded_node_ids];
  if (action === "SELECT_COMPOSITION") {
    const categoryId = indexes.categoryByEntry.get(state.category_entry_id)?.category_id;
    invariant(categoryId, "TRANSITION_COVERAGE_CATEGORY_MISSING");
    return derived.compositionIdsByCategory.get(categoryId) ?? [];
  }
  if (action === "RESET_CATEGORY" || action === "EXPORT_CURRENT_STATE") return [""];
  throw new Error(`TRANSITION_COVERAGE_UNKNOWN_ACTION:${action}`);
}

function resolveDerivedTransition(action, targetId, state, indexes, derived) {
  if (!expectedTransitionTargets(action, state, indexes, derived).includes(targetId)) return undefined;
  if (action === "SELECT_CATEGORY") {
    return indexes.stateById.get(governedRootStateIdForCategory(targetId, indexes.categoryByEntry));
  }
  if (action === "FOCUS_NODE" || action === "MOVE_FOCUS") {
    return derived.stateByKey.get(derivedStateKey(state.composition_id, targetId, state.expanded_node_ids));
  }
  if (action === "EXPAND_NODE") {
    return derived.stateByKey.get(derivedStateKey(
      state.composition_id,
      state.focused_node_id,
      [...state.expanded_node_ids, targetId],
    ));
  }
  if (action === "COLLAPSE_NODE") {
    return derived.stateByKey.get(derivedStateKey(
      state.composition_id,
      state.focused_node_id,
      state.expanded_node_ids.filter((nodeId) => nodeId !== targetId),
    ));
  }
  if (action === "SELECT_COMPOSITION") return derived.rootByComposition.get(targetId);
  if (action === "RESET_CATEGORY") {
    const categoryId = indexes.categoryByEntry.get(state.category_entry_id)?.category_id;
    return categoryId ? indexes.stateById.get(governedRootStateIdForCategory(categoryId, indexes.categoryByEntry)) : undefined;
  }
  if (action === "EXPORT_CURRENT_STATE") return state;
  return undefined;
}

function censusBoolean(value, code) {
  invariant(typeof value === "string", code);
  const normalised = value.trim().toLowerCase();
  invariant(normalised === "true" || normalised === "false", code);
  return normalised === "true";
}

async function validateTransitions(path, model, indexes, derived, ledger, counters, auditStats) {
  const adjacency = new Map([...indexes.stateById.keys()].map((stateId) => [stateId, new Set()]));
  const observedTargets = new Map([...indexes.stateById.keys()].map((stateId) => [
    stateId,
    new Map(ACTIONS.map((action) => [action, new Set()])),
  ]));
  let rowCount = 0;
  for await (const row of readTsv(path)) {
    rowCount += 1;
    const currentStateHash = firstValue(row, ["current_state_hash"]) ?? "";
    const action = firstValue(row, ["action"]) ?? "";
    const targetId = firstValue(row, ["target_id"]) ?? "";
    const nextStateId = firstValue(row, ["next_state_id"]) ?? "";
    const key = `${currentStateHash}|${action}|${targetId}`;
    const caseRecord = {
      transition_key: key,
      current_state_id: firstValue(row, ["current_state_id"]) ?? "",
      action,
      target_id: targetId,
      next_state_id: nextStateId,
      in_place_mutation_detected: "NOT_EVALUATED",
    };
    await runRecordedCase(ledger, counters, caseRecord, () => {
      const parts = transitionParts(key);
      requireHash(parts.stateHash, "TRANSITION_STATE_HASH");
      invariant(ACTION_SET.has(parts.action), "TRANSITION_ACTION_INVALID");
      const currentState = model.states[model.states_by_hash[parts.stateHash]];
      const nextState = model.states[nextStateId];
      invariant(currentState, "TRANSITION_CURRENT_STATE_MISSING");
      invariant(nextState, "TRANSITION_NEXT_STATE_MISSING");
      invariant(firstValue(row, ["current_state_id"]) === currentState.state_id, "TRANSITION_CENSUS_CURRENT_STATE_ID_MISMATCH");
      invariant(firstValue(row, ["next_state_hash"]) === nextState.state_hash, "TRANSITION_CENSUS_NEXT_STATE_HASH_MISMATCH");
      invariant(firstValue(row, ["database_snapshot"]) === model.database.database_snapshot_id, "TRANSITION_CENSUS_DATABASE_MISMATCH");
      invariant(censusBoolean(firstValue(row, ["executed"]) ?? "", "TRANSITION_CENSUS_EXECUTED") === true, "TRANSITION_NOT_EXECUTED");
      invariant(censusBoolean(firstValue(row, ["passed"]) ?? "", "TRANSITION_CENSUS_PASSED") === true, "TRANSITION_NOT_PASSED");
      invariant(censusBoolean(firstValue(row, ["state_mutated"]) ?? "", "TRANSITION_CENSUS_MUTATED") === false, "TRANSITION_CENSUS_IN_PLACE_MUTATION");
      const transitionId = `R16A-TRANSITION-${canonicalHash({ key, next: nextStateId }).slice(0, 24).toUpperCase()}`;
      invariant(firstValue(row, ["transition_id"]) === transitionId, "TRANSITION_CENSUS_IDENTITY_MISMATCH");
      invariant(currentState.available_actions.includes(parts.action), "TRANSITION_ACTION_NOT_ADVERTISED");
      const currentBefore = canonicalHash(currentState);
      const nextBefore = canonicalHash(nextState);
      const derivedNext = resolveDerivedTransition(parts.action, parts.targetId, currentState, indexes, derived);
      invariant(derivedNext?.state_id === nextStateId, "TRANSITION_DERIVATION_LOOKUP_MISMATCH");
      validateActionInvariant(parts.action, parts.targetId, currentState, nextState, indexes);
      const inPlaceMutationDetected = canonicalHash(currentState) !== currentBefore || canonicalHash(nextState) !== nextBefore;
      caseRecord.in_place_mutation_detected = inPlaceMutationDetected;
      if (inPlaceMutationDetected) auditStats.inPlaceStateMutationCount += 1;
      invariant(!inPlaceMutationDetected, "TRANSITION_IN_PLACE_STATE_MUTATION");
      adjacency.get(currentState.state_id)?.add(nextState.state_id);
      const actionTargets = observedTargets.get(currentState.state_id)?.get(parts.action);
      invariant(actionTargets && !actionTargets.has(parts.targetId), "TRANSITION_CENSUS_DUPLICATE_KEY");
      actionTargets.add(parts.targetId);
      return {
        current_state_id: currentState.state_id,
        action: parts.action,
        target_id: parts.targetId,
        in_place_mutation_detected: false,
      };
    });
  }
  for (const state of indexes.stateById.values()) {
    for (const action of ACTIONS) {
      await runRecordedCase(ledger, counters, {
        transition_key: `COVERAGE|${state.state_hash}|${action}`,
        current_state_id: state.state_id,
        action,
        target_id: "",
        next_state_id: "",
      }, () => {
        const expected = [...expectedTransitionTargets(action, state, indexes, derived)].sort(compareCodePoints);
        const actual = [...observedTargets.get(state.state_id).get(action)].sort(compareCodePoints);
        const advertised = state.available_actions.includes(action);
        invariant(advertised === (expected.length > 0), "TRANSITION_ADVERTISED_ACTION_COVERAGE_MISMATCH");
        invariant(
          actual.length === expected.length && actual.every((target, index) => target === expected[index]),
          `TRANSITION_TARGET_COVERAGE_MISMATCH:${actual.length}:${expected.length}`,
        );
      });
    }
  }
  await runRecordedCase(ledger, counters, {
    transition_key: "DERIVED_TRANSITION_COUNT",
    current_state_id: "",
    action: "",
    target_id: "",
    next_state_id: "",
  }, () => {
    invariant(rowCount === model.transitions.transition_count, "TRANSITION_CENSUS_COUNT_MISMATCH");
    invariant(derived.transitionCount === model.transitions.transition_count, "TRANSITION_DERIVED_COUNT_MISMATCH");
    invariant(model.capabilities.transition_count === derived.transitionCount, "TRANSITION_CAPABILITY_COUNT_MISMATCH");
  });

  await runRecordedCase(ledger, counters, {
    transition_key: "MODEL_MUTATION_GUARD",
    current_state_id: "",
    action: "",
    target_id: "",
    next_state_id: "",
  }, () => invariant(isDeepFrozen(model), "TRANSITION_MODEL_NOT_DEEPLY_FROZEN"));

  await runRecordedCase(ledger, counters, {
    transition_key: "PRODUCTION_REACHABILITY",
    current_state_id: "",
    action: "",
    target_id: "",
    next_state_id: "",
  }, () => {
    const visited = new Set();
    const queue = [...indexes.categoryByEntry.values()].map((category) => category.initial_state_id);
    while (queue.length > 0) {
      const stateId = queue.shift();
      if (!stateId || visited.has(stateId)) continue;
      visited.add(stateId);
      for (const nextStateId of adjacency.get(stateId) ?? []) if (!visited.has(nextStateId)) queue.push(nextStateId);
    }
    invariant(visited.size === indexes.stateById.size, `UNREACHABLE_PRODUCTION_STATES:${indexes.stateById.size - visited.size}`);
  });
}

function workflowTransitionKeys(row) {
  const jsonValue = firstValue(row, ["transition_keys_json", "workflow_transition_keys_json"]);
  if (jsonValue) {
    const parsed = parseJsonCell(jsonValue, "WORKFLOW_TRANSITION_KEYS_JSON");
    invariant(Array.isArray(parsed) && parsed.every((item) => typeof item === "string"), "WORKFLOW_TRANSITION_KEYS_INVALID");
    return parsed;
  }
  const stepsValue = firstValue(row, ["steps", "steps_json", "workflow_steps_json"]);
  if (stepsValue) {
    const steps = parseJsonCell(stepsValue, "WORKFLOW_STEPS_JSON");
    invariant(Array.isArray(steps), "WORKFLOW_STEPS_NOT_ARRAY");
    return steps.map((step) => {
      if (typeof step === "string") return step;
      const record = requireRecord(step, "WORKFLOW_STEP_NOT_RECORD");
      if (typeof record.transition_key === "string") return record.transition_key;
      const action = requireString(record.action, "WORKFLOW_STEP_ACTION");
      invariant(ACTION_SET.has(action), "WORKFLOW_STEP_ACTION_INVALID");
      const suffix = `|${action}|${typeof record.target_id === "string" ? record.target_id : ""}`;
      return record.current_state_hash === undefined
        ? suffix
        : `${requireHash(record.current_state_hash, "WORKFLOW_STEP_STATE_HASH")}${suffix}`;
    });
  }
  const delimited = firstValue(row, ["transition_keys", "workflow_transition_keys"]);
  if (delimited !== undefined) return delimited ? delimited.split(";").filter(Boolean) : [];
  throw new Error("WORKFLOW_TRANSITIONS_MISSING");
}

function canonicalShortestPaths(model, initialStateId, indexes, derived) {
  const initialState = model.states[initialStateId];
  invariant(initialState, "CANONICAL_WORKFLOW_INITIAL_STATE_MISSING");
  const outgoing = new Map();
  for (const current of indexes.stateById.values()) {
    if (current.composition_id !== initialState.composition_id) continue;
    for (const action of ACTIONS) {
      if (!LOCAL_WORKFLOW_ACTION_SET.has(action)) continue;
      for (const targetId of expectedTransitionTargets(action, current, indexes, derived)) {
        const next = resolveDerivedTransition(action, targetId, current, indexes, derived);
        if (!next || next.composition_id !== initialState.composition_id) continue;
        const key = `${current.state_hash}|${action}|${targetId}`;
        const entries = outgoing.get(current.state_id) ?? [];
        entries.push({ key, nextStateId: next.state_id, stateHash: current.state_hash, action, targetId });
        outgoing.set(current.state_id, entries);
      }
    }
  }
  for (const entries of outgoing.values()) {
    entries.sort((left, right) => (
      ACTIONS.indexOf(left.action) - ACTIONS.indexOf(right.action)
      || compareCodePoints(left.targetId, right.targetId)
      || compareCodePoints(left.nextStateId, right.nextStateId)
      || compareCodePoints(left.key, right.key)
    ));
  }
  const paths = new Map([[initialStateId, []]]);
  const queue = [initialStateId];
  while (queue.length > 0) {
    const currentStateId = queue.shift();
    if (!currentStateId) break;
    const currentPath = paths.get(currentStateId);
    for (const transition of outgoing.get(currentStateId) ?? []) {
      if (paths.has(transition.nextStateId)) continue;
      paths.set(transition.nextStateId, [...currentPath, transition.key]);
      queue.push(transition.nextStateId);
    }
  }
  return paths;
}

async function replayWorkflows(path, model, indexes, derived, ledger, counters) {
  const coveredExportStates = new Set();
  const pathsByInitialState = new Map();
  let workflowCount = 0;
  for await (const row of readTsv(path)) {
    workflowCount += 1;
    const workflowId = firstValue(row, ["workflow_id", "canonical_workflow_id"]) ?? `row-${row.__row_number}`;
    let firstReplayTarget;
    for (let replay = 1; replay <= 2; replay += 1) {
      await runRecordedCase(ledger, counters, {
        workflow_id: workflowId,
        replay_ordinal: replay,
        initial_state_id: firstValue(row, ["initial_state_id", "start_state_id"]) ?? "",
        target_state_id: firstValue(row, ["target_state_id", "exportable_state_id", "final_state_id"]) ?? "",
        transition_count: "",
      }, () => {
        const keySpecifications = workflowTransitionKeys(row);
        const declaredLength = firstValue(row, ["workflow_length", "transition_count"]);
        if (declaredLength !== undefined) invariant(Number(declaredLength) === keySpecifications.length, "WORKFLOW_LENGTH_MISMATCH");
        const firstExplicitKey = keySpecifications.find((key) => !key.startsWith("|"));
        const firstParts = firstExplicitKey ? transitionParts(firstExplicitKey) : undefined;
        const initialStateId = firstValue(row, ["initial_state_id", "start_state_id"])
          ?? (firstParts ? model.states_by_hash[firstParts.stateHash] : undefined);
        invariant(initialStateId && model.states[initialStateId], "WORKFLOW_INITIAL_STATE_MISSING");
        let current = model.states[initialStateId];
        const rootComposition = indexes.compositionById.get(current.composition_id);
        invariant(rootComposition, "WORKFLOW_ROOT_COMPOSITION_MISSING");
        invariant(current.focused_node_id === rootComposition.seed_node_id, "WORKFLOW_ROOT_FOCUS_NOT_SEED");
        invariant(current.expanded_node_ids.length === 0, "WORKFLOW_ROOT_NOT_COLLAPSED");
        invariant(current.seed_id === rootComposition.seed_id, "WORKFLOW_ROOT_SEED_MISMATCH");
        const declaredCompositionId = firstValue(row, ["composition_id"]);
        const declaredSeedId = firstValue(row, ["seed_id"]);
        if (declaredCompositionId) invariant(declaredCompositionId === current.composition_id, "WORKFLOW_ROOT_COMPOSITION_MISMATCH");
        if (declaredSeedId) invariant(declaredSeedId === current.seed_id, "WORKFLOW_ROOT_DECLARED_SEED_MISMATCH");
        if (firstValue(row, ["replay_count"]) !== undefined) invariant(Number(row.replay_count) === 2, "WORKFLOW_DECLARED_REPLAY_COUNT");
        if (firstValue(row, ["replay_pass_count"]) !== undefined) invariant(Number(row.replay_pass_count) === 2, "WORKFLOW_DECLARED_REPLAY_PASS_COUNT");
        for (const field of ["state_replay_mismatch_count", "semantic_replay_mismatch_count"]) {
          if (firstValue(row, [field]) !== undefined) invariant(Number(row[field]) === 0, `WORKFLOW_DECLARED_MISMATCH:${field}`);
        }
        const categoryEntryId = firstValue(row, ["category_entry_id"]);
        if (categoryEntryId) invariant(current.category_entry_id === categoryEntryId, "WORKFLOW_CATEGORY_ENTRY_MISMATCH");
        const executedKeys = [];
        for (const keySpecification of keySpecifications) {
          const key = keySpecification.startsWith("|") ? `${current.state_hash}${keySpecification}` : keySpecification;
          const parts = transitionParts(key);
          invariant(parts.stateHash === current.state_hash, "WORKFLOW_STEP_CURRENT_STATE_MISMATCH");
          const nextState = resolveDerivedTransition(parts.action, parts.targetId, current, indexes, derived);
          const nextStateId = nextState?.state_id;
          invariant(nextStateId && model.states[nextStateId], "WORKFLOW_TRANSITION_MISSING");
          executedKeys.push(key);
          current = model.states[nextStateId];
        }
        const targetStateId = firstValue(row, ["target_state_id", "exportable_state_id", "final_state_id"]);
        const targetStateHash = firstValue(row, ["target_state_hash", "final_state_hash"]);
        const targetSemanticHash = firstValue(row, ["target_semantic_hash", "semantic_hash"]);
        if (targetStateId) invariant(current.state_id === targetStateId, "WORKFLOW_TARGET_STATE_ID_MISMATCH");
        if (targetStateHash) invariant(current.state_hash === targetStateHash, "WORKFLOW_TARGET_STATE_HASH_MISMATCH");
        if (targetSemanticHash) invariant(current.semantic_hash === targetSemanticHash, "WORKFLOW_TARGET_SEMANTIC_HASH_MISMATCH");
        invariant(current.available_actions.includes("EXPORT_CURRENT_STATE"), "WORKFLOW_TARGET_NOT_EXPORTABLE");
        if (!pathsByInitialState.has(initialStateId)) {
          pathsByInitialState.set(initialStateId, canonicalShortestPaths(model, initialStateId, indexes, derived));
        }
        const canonicalKeys = pathsByInitialState.get(initialStateId).get(current.state_id);
        invariant(canonicalKeys, "WORKFLOW_TARGET_UNREACHABLE_FROM_INITIAL_STATE");
        invariant(canonicalKeys.length === executedKeys.length, "WORKFLOW_NOT_SHORTEST");
        invariant(canonicalKeys.every((key, index) => key === executedKeys[index]), "WORKFLOW_TIE_BREAK_MISMATCH");
        if (firstReplayTarget) invariant(firstReplayTarget === current.state_id, "WORKFLOW_REPLAY_NOT_DETERMINISTIC");
        firstReplayTarget = current.state_id;
        coveredExportStates.add(current.state_id);
        return {
          initial_state_id: initialStateId,
          target_state_id: current.state_id,
          transition_count: executedKeys.length,
        };
      });
    }
  }
  await runRecordedCase(ledger, counters, {
    workflow_id: "WORKFLOW_COVERAGE",
    replay_ordinal: "",
    initial_state_id: "",
    target_state_id: "",
    transition_count: "",
  }, () => {
    const exportableStates = [...indexes.stateById.values()].filter((state) => state.available_actions.includes("EXPORT_CURRENT_STATE"));
    invariant(exportableStates.length === indexes.stateById.size, "WORKFLOW_NON_EXPORTABLE_PRODUCTION_STATE");
    invariant(workflowCount === exportableStates.length, `WORKFLOW_COUNT_MISMATCH:${workflowCount}:${exportableStates.length}`);
    invariant(coveredExportStates.size === exportableStates.length, "WORKFLOW_EXPORTABLE_STATE_COVERAGE_MISMATCH");
  });
}

function exportRequestFromRow(row) {
  const requestCell = firstValue(row, ["request_json", "export_request_json"]);
  const parsed = requestCell ? requireRecord(parseJsonCell(requestCell, "EXPORT_REQUEST_JSON"), "EXPORT_REQUEST_NOT_RECORD") : {};
  return {
    map_id: firstValue(row, ["map_id", "category_entry_id"]) ?? parsed.map_id,
    state_hash: firstValue(row, ["state_hash"]) ?? parsed.state_hash,
    composition_id: firstValue(row, ["composition_id"]) ?? parsed.composition_id,
    export_preset: firstValue(row, ["export_preset", "preset"]) ?? parsed.export_preset,
    theme_token_set: firstValue(row, ["theme_token_set", "theme"]) ?? parsed.theme_token_set,
  };
}

function exportIdentity(model, state, request) {
  const requestIdentity = {
    map_id: request.map_id,
    state_hash: request.state_hash,
    composition_id: request.composition_id,
    export_preset: request.export_preset,
    theme_token_set: request.theme_token_set,
  };
  const presentationIdentity = {
    api_version: "trace-exploration/v2",
    render_version: "trace-exploration-portrait-png-v2",
    database_snapshot: model.database.database_snapshot_id,
    state_hash: state.state_hash,
    state_presentation_hash: state.presentation_hash,
    composition_id: state.composition_id,
    export_preset: request.export_preset,
    theme_token_set: request.theme_token_set,
  };
  const presentationHash = canonicalHash(presentationIdentity);
  return {
    requestIdentitySha256: canonicalHash(requestIdentity),
    presentationHash,
    exportId: `TEV2-${presentationHash.slice(0, 24)}`,
  };
}

async function validateExports(path, model, indexes, ledger, counters) {
  const observed = new Set();
  const observedVariantIds = new Set();
  let rowCount = 0;
  for await (const row of readTsv(path)) {
    rowCount += 1;
    const request = exportRequestFromRow(row);
    const variantId = firstValue(row, ["export_variant_id"]) ?? `row-${row.__row_number}`;
    await runRecordedCase(ledger, counters, {
      export_variant_id: variantId,
      state_id: firstValue(row, ["state_id"]) ?? "",
      state_hash: request.state_hash ?? "",
      export_preset: request.export_preset ?? "",
      theme_token_set: request.theme_token_set ?? "",
      request_identity_sha256: "",
      presentation_hash: "",
      export_id: firstValue(row, ["export_id"]) ?? "",
    }, () => {
      requireString(request.map_id, "EXPORT_MAP_ID");
      requireHash(request.state_hash, "EXPORT_STATE_HASH");
      requireString(request.composition_id, "EXPORT_COMPOSITION_ID");
      invariant(request.export_preset === EXPORT_PRESET, "EXPORT_PRESET_INVALID");
      invariant(THEMES_SET.has(request.theme_token_set), "EXPORT_THEME_INVALID");
      const stateId = model.states_by_hash[request.state_hash];
      const state = model.states[stateId];
      invariant(state, "EXPORT_STATE_MISSING");
      invariant(state.category_entry_id === request.map_id, "EXPORT_MAP_STATE_MISMATCH");
      invariant(state.composition_id === request.composition_id, "EXPORT_COMPOSITION_STATE_MISMATCH");
      invariant(state.available_actions.includes("EXPORT_CURRENT_STATE"), "EXPORT_STATE_NOT_EXPORTABLE");
      const declaredStateId = firstValue(row, ["state_id"]);
      invariant(declaredStateId === state.state_id, "EXPORT_STATE_ID_MISMATCH");
      invariant(firstValue(row, ["seed_id"]) === state.seed_id, "EXPORT_SEED_ID_MISMATCH");
      invariant(firstValue(row, ["semantic_hash"]) === state.semantic_hash, "EXPORT_SEMANTIC_HASH_MISMATCH");
      invariant(firstValue(row, ["state_presentation_hash"]) === state.presentation_hash, "EXPORT_STATE_PRESENTATION_HASH_MISMATCH");
      invariant(Number(firstValue(row, ["width"])) === 1080 && Number(firstValue(row, ["height"])) === 1620, "EXPORT_DIMENSIONS_MISMATCH");
      const identity = exportIdentity(model, state, request);
      const requestHash = firstValue(row, ["request_identity_sha256", "export_request_sha256"]);
      const presentationHash = firstValue(row, ["export_presentation_hash", "presentation_hash"]);
      const exportId = firstValue(row, ["export_id"]);
      if (requestHash) invariant(requestHash === identity.requestIdentitySha256, "EXPORT_REQUEST_IDENTITY_MISMATCH");
      invariant(presentationHash === identity.presentationHash, "EXPORT_PRESENTATION_HASH_MISMATCH");
      if (exportId) invariant(exportId === identity.exportId, "EXPORT_ID_MISMATCH");
      invariant(variantId === identity.exportId, "EXPORT_VARIANT_ID_MISMATCH");
      const key = `${state.state_id}|${request.export_preset}|${request.theme_token_set}`;
      invariant(!observed.has(key), "EXPORT_VARIANT_DUPLICATE");
      invariant(!observedVariantIds.has(variantId), "EXPORT_VARIANT_ID_DUPLICATE");
      observed.add(key);
      observedVariantIds.add(variantId);
      return {
        state_id: state.state_id,
        request_identity_sha256: identity.requestIdentitySha256,
        presentation_hash: identity.presentationHash,
        export_id: identity.exportId,
      };
    });
  }
  await runRecordedCase(ledger, counters, {
    export_variant_id: "EXPORT_COVERAGE",
    state_id: "",
    state_hash: "",
    export_preset: "",
    theme_token_set: "",
    request_identity_sha256: "",
    presentation_hash: "",
    export_id: "",
  }, () => {
    const expected = new Set();
    for (const state of indexes.stateById.values()) {
      if (!state.available_actions.includes("EXPORT_CURRENT_STATE")) continue;
      for (const theme of THEMES) expected.add(`${state.state_id}|${EXPORT_PRESET}|${theme}`);
    }
    invariant(rowCount === expected.size, `EXPORT_ROW_COUNT_MISMATCH:${rowCount}:${expected.size}`);
    invariant(observed.size === expected.size && [...expected].every((key) => observed.has(key)), "EXPORT_VARIANT_COVERAGE_MISMATCH");
  });
}

const MAP_RESPONSE_KEYS = [
  "api_version", "associations", "category", "composition", "database_snapshot", "is_initial_state",
  "map_id", "map_summary", "nodes", "plain_text_tree", "state",
];
const CATEGORY_DTO_KEYS = ["category_entry_id", "category_id", "composition_ids", "description", "entry_label", "initial_state_id", "label"];
const VOCABULARY_DTO_KEYS = ["activation_status", "ambiguity_note", "attested_forms", "canonical_label", "language", "scope_note", "vocabulary_id"];
const ASSOCIATION_DTO_KEYS = [
  "association_accessible_description", "association_id", "confidence", "endpoint_labels", "endpoint_vocabulary_ids",
  "explicit_non_claims", "generic_association_only", "strength", "support_status",
];
const MAP_NODE_KEYS = [...VOCABULARY_DTO_KEYS, "expanded", "focused", "position"];
const TREE_KEYS = [
  "composition_id", "plain_text_tree", "plain_text_tree_ascii", "root_node_id", "tree_association_ids",
  "tree_node_ids", "tree_version", "visible_association_ids",
];
const CAPABILITIES_KEYS = [
  "api_version", "association_count", "category_count", "category_entry_count", "composition_count", "database_snapshot",
  "export", "maximum_visible_nodes", "state_count", "supported_actions", "topology_families", "transition_count", "vocabulary_count",
];
const EXPORT_MANIFEST_KEYS = [
  "api_version", "association_count", "associations", "category", "category_entry_id", "composition_id", "database_snapshot",
  "dimensions", "export_alt_text", "export_id", "export_preset", "manifest_version", "map_id", "node_count", "nodes",
  "plain_text_tree", "presentation_hash", "provenance_summary", "render_version", "seed_id", "semantic_hash", "state_hash", "state_id",
  "suggested_filename", "theme_token_set",
];
const PROVENANCE_SUMMARY_KEYS = [
  "association_count", "externally_supported_count", "generic_association_only", "source_locators_withheld_from_public_export",
  "source_supported_count",
];

function unwrapServiceResult(result, code) {
  invariant(isRecord(result) && result.ok === true && Object.hasOwn(result, "data"), `${code}:SERVICE_FAILURE`);
  return result.data;
}

function validateServiceFailure(result, expectedCode) {
  exactKeys(result, ["code", "message", "ok", "retryable", "status"], `SERVICE_ERROR_${expectedCode}`);
  invariant(result.ok === false && result.code === expectedCode, `SERVICE_ERROR_CODE:${expectedCode}`);
  requireString(result.message, `SERVICE_ERROR_MESSAGE:${expectedCode}`);
  const disposition = ERROR_DISPOSITIONS[expectedCode];
  invariant(disposition && result.status === disposition[0] && result.retryable === disposition[1], `SERVICE_ERROR_DISPOSITION:${expectedCode}`);
}

function validateCategoryDto(value, code) {
  allowedKeys(value, CATEGORY_DTO_KEYS, ["category_id", "category_entry_id", "label", "composition_ids", "initial_state_id"], code);
  invariant(CATEGORY_SET.has(value.category_id), `${code}:CATEGORY_ID`);
  requireString(value.category_entry_id, `${code}:CATEGORY_ENTRY_ID`);
  requireString(value.label, `${code}:LABEL`);
  uniqueStrings(value.composition_ids, `${code}:COMPOSITIONS`, 1);
  requireString(value.initial_state_id, `${code}:INITIAL_STATE`);
  invariant(findForbidden(value).length === 0, `${code}:FORBIDDEN`);
}

function validateVocabularyDto(value, code) {
  allowedKeys(value, VOCABULARY_DTO_KEYS, ["vocabulary_id", "canonical_label", "attested_forms", "language"], code);
  requireString(value.vocabulary_id, `${code}:ID`);
  requireString(value.canonical_label, `${code}:LABEL`);
  uniqueStrings(value.attested_forms, `${code}:ATTESTED_FORMS`, 1);
  invariant(value.language === "en", `${code}:LANGUAGE`);
  invariant(findForbidden(value).length === 0, `${code}:FORBIDDEN`);
}

function validateAssociationDto(value, code) {
  allowedKeys(value, ASSOCIATION_DTO_KEYS, [
    "association_id", "endpoint_vocabulary_ids", "endpoint_labels", "support_status", "generic_association_only",
    "association_accessible_description", "explicit_non_claims",
  ], code);
  invariant(SUPPORT_STATUS_SET.has(value.support_status), `${code}:SUPPORT_STATUS`);
  uniqueStrings(value.endpoint_vocabulary_ids, `${code}:ENDPOINT_IDS`, 2, 2);
  uniqueStrings(value.endpoint_labels, `${code}:ENDPOINT_LABELS`, 2, 2);
  requireString(value.association_accessible_description, `${code}:DESCRIPTION`);
  uniqueStrings(value.explicit_non_claims, `${code}:NON_CLAIMS`, 1);
  invariant(value.generic_association_only === true, `${code}:BOUNDARY_FLAG`);
  invariant(findForbidden(value).length === 0, `${code}:FORBIDDEN`);
}

function validateMapDto(value) {
  exactKeys(value, MAP_RESPONSE_KEYS, "MAP_DTO");
  validateCategoryDto(value.category, "MAP_CATEGORY_DTO");
  exactKeys(value.state, STATE_KEYS, "MAP_STATE_DTO");
  allowedKeys(value.composition, ALLOWED_COMPOSITION_KEYS, [
    "composition_id", "category_entry_id", "seed_id", "seed_node_id", "node_ids", "association_ids", "topology_family", "semantic_hash",
  ], "MAP_COMPOSITION_DTO");
  for (const node of requireArray(value.nodes, "MAP_NODES")) {
    allowedKeys(node, MAP_NODE_KEYS, ["vocabulary_id", "canonical_label", "attested_forms", "language", "focused", "expanded", "position"], "MAP_NODE_DTO");
  }
  for (const association of requireArray(value.associations, "MAP_ASSOCIATIONS")) validateAssociationDto(association, "MAP_ASSOCIATION_DTO");
  exactKeys(value.plain_text_tree, TREE_KEYS, "MAP_TREE_DTO");
  invariant(value.api_version === "trace-exploration/v2", "MAP_API_VERSION");
  invariant(value.map_id === value.category.category_entry_id && value.map_id === value.state.category_entry_id, "MAP_CATEGORY_IDENTITY");
  invariant(value.composition.composition_id === value.state.composition_id, "MAP_COMPOSITION_IDENTITY");
  invariant(value.composition.seed_id === value.state.seed_id, "MAP_SEED_IDENTITY");
  invariant(value.state.database_snapshot === value.database_snapshot, "MAP_DATABASE_IDENTITY");
  invariant(value.is_initial_state === (value.state.state_id === value.category.initial_state_id), "MAP_INITIAL_STATE_FLAG");
  const nodeIds = value.nodes.map((node) => node.vocabulary_id);
  const associationIds = value.associations.map((association) => association.association_id);
  invariant(
    canonicalJson([...nodeIds].sort(compareCodePoints)) === canonicalJson([...value.state.visible_node_ids].sort(compareCodePoints)),
    "MAP_VISIBLE_NODE_IDENTITY",
  );
  invariant(canonicalJson(associationIds) === canonicalJson(value.state.visible_association_ids), "MAP_VISIBLE_ASSOCIATION_IDENTITY");
  for (const node of value.nodes) {
    invariant(node.focused === (node.vocabulary_id === value.state.focused_node_id), "MAP_NODE_FOCUS_FLAG");
    invariant(node.expanded === value.state.expanded_node_ids.includes(node.vocabulary_id), "MAP_NODE_EXPANSION_FLAG");
  }
  invariant(value.plain_text_tree.composition_id === value.composition.composition_id, "MAP_TREE_COMPOSITION");
  invariant(
    canonicalJson([...value.plain_text_tree.tree_node_ids].sort(compareCodePoints)) === canonicalJson([...nodeIds].sort(compareCodePoints)),
    "MAP_TREE_NODE_COVERAGE",
  );
  invariant(
    canonicalJson(value.plain_text_tree.visible_association_ids) === canonicalJson(value.state.visible_association_ids),
    "MAP_TREE_VISIBLE_ASSOCIATIONS",
  );
  invariant(findForbidden(value).length === 0, `MAP_DTO_FORBIDDEN:${findForbidden(value).join(",")}`);
}

function validateManifestDto(value) {
  exactKeys(value, EXPORT_MANIFEST_KEYS, "EXPORT_MANIFEST_DTO");
  validateCategoryDto(value.category, "EXPORT_CATEGORY_DTO");
  for (const node of value.nodes) allowedKeys(node, MAP_NODE_KEYS, ["vocabulary_id", "canonical_label", "attested_forms", "language", "focused", "expanded", "position"], "EXPORT_NODE_DTO");
  for (const association of value.associations) validateAssociationDto(association, "EXPORT_ASSOCIATION_DTO");
  exactKeys(value.plain_text_tree, TREE_KEYS, "EXPORT_TREE_DTO");
  invariant(value.manifest_version === "trace-exploration-export-manifest-v2", "EXPORT_MANIFEST_VERSION");
  invariant(value.api_version === "trace-exploration/v2", "EXPORT_MANIFEST_API_VERSION");
  invariant(value.render_version === "trace-exploration-portrait-png-v2", "EXPORT_RENDER_VERSION");
  invariant(value.dimensions.width === 1080 && value.dimensions.height === 1620, "EXPORT_MANIFEST_DIMENSIONS");
  invariant(value.node_count === value.nodes.length, "EXPORT_NODE_COUNT_MISMATCH");
  exactKeys(value.provenance_summary, PROVENANCE_SUMMARY_KEYS, "EXPORT_PROVENANCE_SUMMARY");
  const externallySupportedCount = value.associations.filter(
    (association) => association.support_status === "ACTIVE_EXTERNALLY_SUPPORTED",
  ).length;
  const sourceSupportedCount = value.associations.filter(
    (association) => association.support_status === "ACTIVE_SOURCE_SUPPORTED",
  ).length;
  invariant(value.association_count === value.associations.length, "EXPORT_ASSOCIATION_COUNT_MISMATCH");
  invariant(value.provenance_summary.association_count === value.association_count, "EXPORT_PROVENANCE_ASSOCIATION_COUNT");
  invariant(value.provenance_summary.externally_supported_count === externallySupportedCount, "EXPORT_PROVENANCE_EXTERNAL_COUNT");
  invariant(value.provenance_summary.source_supported_count === sourceSupportedCount, "EXPORT_PROVENANCE_SOURCE_COUNT");
  invariant(value.provenance_summary.generic_association_only === true, "EXPORT_PROVENANCE_GENERIC_FLAG");
  invariant(
    value.provenance_summary.source_locators_withheld_from_public_export === true,
    "EXPORT_PROVENANCE_SOURCE_WITHHOLDING_FLAG",
  );
  invariant(findForbidden(value).length === 0, `EXPORT_MANIFEST_FORBIDDEN:${findForbidden(value).join(",")}`);
}

async function validateServiceDtos(options, model, indexes, derived, ledger, counters) {
  let service;
  let renderer;
  const loaded = await runRecordedCase(ledger, counters, { case_type: "SERVICE_MODULE", case_id: options.serviceModule }, async () => {
    service = await jiti.import(options.serviceModule);
    invariant(isRecord(service), "SERVICE_MODULE_INVALID");
  });
  if (!loaded) return;
  const rendererLoaded = await runRecordedCase(ledger, counters, { case_type: "RENDERER_MODULE", case_id: options.rendererModule }, async () => {
    renderer = await jiti.import(options.rendererModule);
    invariant(isRecord(renderer) && typeof renderer.renderExplorationV2Svg === "function", "SVG_RENDERER_MODULE_INVALID");
  });
  if (!rendererLoaded) return;
  await runRecordedCase(ledger, counters, { case_type: "CATEGORIES", case_id: "all" }, () => {
    const response = unwrapServiceResult(service.listExplorationV2Categories(), "CATEGORIES");
    exactKeys(response, ["api_version", "categories", "database_snapshot"], "CATEGORIES_RESPONSE");
    response.categories.forEach((category) => validateCategoryDto(category, "CATEGORY_DTO"));
  });
  await runRecordedCase(ledger, counters, { case_type: "CAPABILITIES", case_id: "runtime" }, () => {
    const response = unwrapServiceResult(service.retrieveExplorationV2Capabilities(), "CAPABILITIES");
    exactKeys(response, CAPABILITIES_KEYS, "CAPABILITIES_DTO");
    exactKeys(response.export, ["height", "presets", "theme_token_sets", "width"], "CAPABILITIES_EXPORT_DTO");
    invariant(response.api_version === "trace-exploration/v2", "CAPABILITIES_API_VERSION");
    invariant(response.database_snapshot === model.database.database_snapshot_id, "CAPABILITIES_DATABASE_SNAPSHOT");
    invariant(response.category_count === CATEGORY_SET.size, "CAPABILITIES_CATEGORY_COUNT");
    invariant(response.category_entry_count === indexes.categoryByEntry.size, "CAPABILITIES_CATEGORY_ENTRY_COUNT");
    invariant(response.vocabulary_count === indexes.vocabularyIds.size, "CAPABILITIES_VOCABULARY_COUNT");
    invariant(response.association_count === indexes.associationById.size, "CAPABILITIES_ASSOCIATION_COUNT");
    invariant(response.composition_count === indexes.compositionById.size, "CAPABILITIES_COMPOSITION_COUNT");
    invariant(response.state_count === indexes.stateById.size, "CAPABILITIES_STATE_COUNT");
    invariant(response.transition_count === model.transitions.transition_count, "CAPABILITIES_TRANSITION_COUNT");
    invariant(response.maximum_visible_nodes === 8, "CAPABILITIES_NODE_BOUND");
    invariant(canonicalJson(response.supported_actions) === canonicalJson(ACTIONS), "CAPABILITIES_ACTIONS");
    const expectedTopologies = [...new Set([...indexes.compositionById.values()].map((item) => item.topology_family))].sort(compareCodePoints);
    invariant(canonicalJson(response.topology_families) === canonicalJson(expectedTopologies), "CAPABILITIES_TOPOLOGIES");
    invariant(canonicalJson(response.export.presets) === canonicalJson([EXPORT_PRESET]), "CAPABILITIES_EXPORT_PRESETS");
    invariant(canonicalJson(response.export.theme_token_sets) === canonicalJson(THEMES), "CAPABILITIES_EXPORT_THEMES");
    invariant(response.export.width === 1080 && response.export.height === 1620, "CAPABILITIES_EXPORT_DIMENSIONS");
    invariant(findForbidden(response).length === 0, "CAPABILITIES_FORBIDDEN");
  });
  for (const category of indexes.categoryByEntry.values()) {
    await runRecordedCase(ledger, counters, { case_type: "INITIAL_MAP", case_id: category.category_entry_id }, () => {
      const response = unwrapServiceResult(service.createExplorationV2Map({
        category_id: category.category_id,
        category_entry_id: category.category_entry_id,
        locale: "en",
      }), "INITIAL_MAP");
      validateMapDto(response);
      invariant(response.state.state_id === category.initial_state_id, "INITIAL_MAP_STATE_MISMATCH");
    });
  }
  let serviceTransitionCount = 0;
  for await (const row of readTsv(options.transitionCensus)) {
    const currentStateHash = firstValue(row, ["current_state_hash"]) ?? "";
    const action = firstValue(row, ["action"]) ?? "";
    const targetId = firstValue(row, ["target_id"]) ?? "";
    const expectedNextStateId = firstValue(row, ["next_state_id"]) ?? "";
    const transitionKey = `${currentStateHash}|${action}|${targetId}`;
    const passed = await runRecordedCase(ledger, counters, { case_type: "ACTION_TRANSITION", case_id: transitionKey }, () => {
      const parts = transitionParts(transitionKey);
      const currentState = model.states[model.states_by_hash[parts.stateHash]];
      invariant(currentState, "SERVICE_ACTION_CURRENT_STATE_MISSING");
      invariant(resolveDerivedTransition(parts.action, parts.targetId, currentState, indexes, derived)?.state_id === expectedNextStateId, "SERVICE_EXPECTED_DERIVATION_MISMATCH");
      const response = unwrapServiceResult(service.applyExplorationV2Action(currentState.category_entry_id, {
        action: parts.action,
        expected_state_hash: currentState.state_hash,
        database_snapshot: model.database.database_snapshot_id,
        ...(parts.targetId ? { target_id: parts.targetId } : {}),
      }), "ACTION_TRANSITION");
      validateMapDto(response);
      invariant(response.state.state_id === expectedNextStateId, "SERVICE_ACTION_NEXT_STATE_MISMATCH");
      invariant(response.state.state_hash === model.states[expectedNextStateId].state_hash, "SERVICE_ACTION_NEXT_HASH_MISMATCH");
    });
    if (passed) serviceTransitionCount += 1;
  }
  await runRecordedCase(ledger, counters, { case_type: "ACTION_TRANSITION", case_id: "SERVICE_TRANSITION_COVERAGE" }, () => {
    invariant(serviceTransitionCount === model.transitions.transition_count, "SERVICE_TRANSITION_COVERAGE_MISMATCH");
  });
  await runRecordedCase(ledger, counters, { case_type: "ACTION_TRANSITION", case_id: "MODEL_MUTATION_GUARD" }, () => {
    invariant(isDeepFrozen(model), "SERVICE_ACTION_MODEL_NOT_DEEPLY_FROZEN");
  });
  const exampleCategory = indexes.categoryByEntry.values().next().value;
  const exampleState = indexes.stateById.get(exampleCategory.initial_state_id);
  invariant(exampleCategory && exampleState, "SERVICE_ERROR_FIXTURE_MISSING");
  const validExportRequest = {
    map_id: exampleState.category_entry_id,
    state_hash: exampleState.state_hash,
    composition_id: exampleState.composition_id,
    export_preset: EXPORT_PRESET,
    theme_token_set: THEMES[0],
  };
  const serviceErrorCases = [
    ["missing-map-category", "INVALID_REQUEST", () => service.createExplorationV2Map({})],
    ["invalid-map-category", "INVALID_CATEGORY", () => service.createExplorationV2Map({ category_id: "not-a-category" })],
    ["invalid-category-entry", "INVALID_CATEGORY_ENTRY", () => service.createExplorationV2Map({
      category_id: exampleCategory.category_id,
      category_entry_id: "not-present",
    })],
    ["missing-map", "STATE_NOT_FOUND", () => service.retrieveExplorationV2Map("not-present")],
    ["missing-action-state", "INVALID_REQUEST", () => service.applyExplorationV2Action(exampleState.category_entry_id, {
      action: "RESET_CATEGORY",
    })],
    ["invalid-action", "INVALID_ACTION", () => service.applyExplorationV2Action(exampleState.category_entry_id, {
      action: "NOT_AN_ACTION",
      expected_state_hash: exampleState.state_hash,
    })],
    ["stale-action-state", "STALE_EXPLORATION_STATE", () => service.applyExplorationV2Action(exampleState.category_entry_id, {
      action: "RESET_CATEGORY",
      expected_state_hash: "0".repeat(64),
    })],
    ["database-mismatch", "STATE_DATABASE_VERSION_MISMATCH", () => service.applyExplorationV2Action(exampleState.category_entry_id, {
      action: "RESET_CATEGORY",
      expected_state_hash: exampleState.state_hash,
      database_snapshot: "different-frozen-snapshot",
    })],
    ["invalid-action-target", "ACTION_NOT_AVAILABLE", () => service.applyExplorationV2Action(exampleState.category_entry_id, {
      action: "FOCUS_NODE",
      target_id: "not-present",
      expected_state_hash: exampleState.state_hash,
    })],
    ["invalid-vocabulary", "INVALID_VOCABULARY", () => service.retrieveExplorationV2Vocabulary("not-present")],
    ["invalid-association", "INVALID_ASSOCIATION", () => service.retrieveExplorationV2Association("not-present")],
    ["missing-export-fields", "INVALID_REQUEST", () => service.createExplorationV2ExportManifest({})],
    ["invalid-export-preset", "INVALID_EXPORT_PRESET", () => service.createExplorationV2ExportManifest({
      ...validExportRequest,
      export_preset: "not-supported",
    })],
    ["stale-export-state", "STALE_EXPLORATION_STATE", () => service.createExplorationV2ExportManifest({
      ...validExportRequest,
      state_hash: "0".repeat(64),
    })],
    ["nonexportable-composition", "NO_EXPORTABLE_COMPOSITION", () => service.createExplorationV2ExportManifest({
      ...validExportRequest,
      composition_id: "not-present",
    })],
  ];
  for (const [caseId, expectedCode, operation] of serviceErrorCases) {
    await runRecordedCase(ledger, counters, { case_type: "ERROR_CONTRACT", case_id: caseId }, () => {
      validateServiceFailure(operation(), expectedCode);
    });
  }
  for (const state of indexes.stateById.values()) {
    await runRecordedCase(ledger, counters, { case_type: "STATE_MAP", case_id: state.state_id }, () => {
      const response = unwrapServiceResult(service.retrieveExplorationV2Map(state.category_entry_id, state.state_id), "STATE_MAP");
      validateMapDto(response);
      invariant(response.state.state_hash === state.state_hash, "STATE_MAP_HASH_MISMATCH");
    });
  }
  for (const vocabularyId of indexes.vocabularyIds) {
    await runRecordedCase(ledger, counters, { case_type: "VOCABULARY_DTO", case_id: vocabularyId }, () => {
      const response = unwrapServiceResult(service.retrieveExplorationV2Vocabulary(vocabularyId), "VOCABULARY");
      exactKeys(response, ["api_version", "database_snapshot", "vocabulary"], "VOCABULARY_RESPONSE");
      validateVocabularyDto(response.vocabulary, "VOCABULARY_DTO");
    });
  }
  for (const associationId of indexes.associationById.keys()) {
    await runRecordedCase(ledger, counters, { case_type: "ASSOCIATION_DTO", case_id: associationId }, () => {
      const response = unwrapServiceResult(service.retrieveExplorationV2Association(associationId), "ASSOCIATION");
      exactKeys(response, ["api_version", "association", "database_snapshot"], "ASSOCIATION_RESPONSE");
      validateAssociationDto(response.association, "ASSOCIATION_DTO");
    });
  }
  for await (const row of readTsv(options.exportCensus)) {
    const request = exportRequestFromRow(row);
    const caseId = firstValue(row, ["export_variant_id", "export_id"]) ?? `row-${row.__row_number}`;
    await runRecordedCase(ledger, counters, { case_type: "EXPORT_MANIFEST_AND_SVG", case_id: caseId }, () => {
      const response = unwrapServiceResult(service.createExplorationV2ExportManifest(request), "EXPORT_MANIFEST");
      validateManifestDto(response);
      const state = model.states[model.states_by_hash[request.state_hash]];
      const identity = exportIdentity(model, state, request);
      invariant(response.export_id === identity.exportId && response.presentation_hash === identity.presentationHash, "EXPORT_SERVICE_IDENTITY_MISMATCH");
      invariant(response.database_snapshot === model.database.database_snapshot_id, "EXPORT_SERVICE_DATABASE_MISMATCH");
      invariant(response.map_id === request.map_id && response.category_entry_id === request.map_id, "EXPORT_SERVICE_MAP_MISMATCH");
      invariant(response.state_id === state.state_id && response.state_hash === state.state_hash, "EXPORT_SERVICE_STATE_MISMATCH");
      invariant(response.composition_id === request.composition_id && response.composition_id === state.composition_id, "EXPORT_SERVICE_COMPOSITION_MISMATCH");
      invariant(response.seed_id === state.seed_id, "EXPORT_SERVICE_SEED_MISMATCH");
      invariant(response.export_preset === request.export_preset && response.theme_token_set === request.theme_token_set, "EXPORT_SERVICE_PRESENTATION_REQUEST_MISMATCH");
      invariant(response.semantic_hash === state.semantic_hash, "EXPORT_SERVICE_SEMANTIC_HASH_MISMATCH");
      invariant(
        canonicalJson(response.nodes.map((node) => node.vocabulary_id).sort(compareCodePoints))
          === canonicalJson([...state.visible_node_ids].sort(compareCodePoints)),
        "EXPORT_SERVICE_VISIBLE_NODE_MISMATCH",
      );
      invariant(
        canonicalJson(response.associations.map((association) => association.association_id)) === canonicalJson(state.visible_association_ids),
        "EXPORT_SERVICE_VISIBLE_ASSOCIATION_MISMATCH",
      );
      invariant(
        canonicalJson(response.plain_text_tree.visible_association_ids) === canonicalJson(state.visible_association_ids),
        "EXPORT_SERVICE_TREE_ASSOCIATION_MISMATCH",
      );
      const firstSvg = renderer.renderExplorationV2Svg(response);
      const secondSvg = renderer.renderExplorationV2Svg(response);
      invariant(firstSvg === secondSvg, "EXPORT_SVG_REPLAY_MISMATCH");
      const svgBytes = new TextEncoder().encode(firstSvg);
      invariant(svgBytes.byteLength > 0 && svgBytes.byteLength <= 262_144, "EXPORT_SVG_BYTE_BOUND");
      invariant(firstSvg.startsWith("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<svg "), "EXPORT_SVG_DOCUMENT_PREFIX");
      invariant(firstSvg.includes('width="1080" height="1620" viewBox="0 0 1080 1620"'), "EXPORT_SVG_DIMENSIONS");
      invariant(firstSvg.includes(response.export_id), "EXPORT_SVG_MANIFEST_IDENTITY");
      invariant(!/<(?:script|foreignObject)\b|\son[a-z]+\s*=/iu.test(firstSvg), "EXPORT_SVG_ACTIVE_CONTENT");
      invariant(findForbidden(firstSvg.replace("http://www.w3.org/2000/svg", "")).length === 0, "EXPORT_SVG_FORBIDDEN_REFERENCE");
      return {
        manifest_export_id: response.export_id,
        svg_sha256: createHash("sha256").update(svgBytes).digest("hex"),
        svg_byte_length: svgBytes.byteLength,
      };
    });
  }
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const ledgers = {
    model: new TsvLedger(options.modelLedger, ["case_type", "case_id", "status", "detail"]),
    transition: new TsvLedger(options.transitionLedger, [
      "transition_key", "current_state_id", "action", "target_id", "next_state_id",
      "in_place_mutation_detected", "status", "detail",
    ]),
    workflow: new TsvLedger(options.workflowLedger, [
      "workflow_id", "replay_ordinal", "initial_state_id", "target_state_id", "transition_count", "status", "detail",
    ]),
    export: new TsvLedger(options.exportLedger, [
      "export_variant_id", "state_id", "state_hash", "export_preset", "theme_token_set",
      "request_identity_sha256", "presentation_hash", "export_id", "status", "detail",
    ]),
    service: new TsvLedger(options.serviceLedger, [
      "case_type", "case_id", "manifest_export_id", "svg_sha256", "svg_byte_length", "status", "detail",
    ]),
  };
  for (const ledger of Object.values(ledgers)) await ledger.open();
  const counters = {
    model: { pass: 0, fail: 0 },
    transition: { pass: 0, fail: 0 },
    workflow: { pass: 0, fail: 0 },
    export: { pass: 0, fail: 0 },
    service: { pass: 0, fail: 0 },
  };
  const auditStats = { inPlaceStateMutationCount: 0 };
  let status = "FAIL";
  let fatalError = "";
  try {
    const modelSource = await readFile(options.model);
    invariant(createHash("sha256").update(modelSource).digest("hex") === PRODUCTION_READ_MODEL_SHA256, "PRODUCTION_READ_MODEL_FILE_HASH_MISMATCH");
    const model = JSON.parse(modelSource.toString("utf8"));
    const indexes = await validateModel(model, ledgers.model, counters.model);
    invariant(counters.model.fail === 0, "MODEL_VALIDATION_FAILED");
    deepFreeze(model);
    const derived = buildDerivedTransitionIndex(model, indexes);
    await validateTransitions(options.transitionCensus, model, indexes, derived, ledgers.transition, counters.transition, auditStats);
    await replayWorkflows(options.workflowCensus, model, indexes, derived, ledgers.workflow, counters.workflow);
    await validateExports(options.exportCensus, model, indexes, ledgers.export, counters.export);
    if (!options.skipService) await validateServiceDtos(options, model, indexes, derived, ledgers.service, counters.service);
    const failureCount = Object.values(counters).reduce((total, suite) => total + suite.fail, 0);
    invariant(failureCount === 0, `CASE_FAILURE_COUNT:${failureCount}`);
    status = "PASS";
  } catch (error) {
    fatalError = cleanDetail(error);
    process.exitCode = 1;
  } finally {
    for (const ledger of Object.values(ledgers)) await ledger.close();
    const summary = {
      format: "trace-exploration-v2-functional-validation",
      status,
      fatal_error: fatalError,
      inputs: {
        production_read_model: options.model,
        production_read_model_sha256: PRODUCTION_READ_MODEL_SHA256,
        transition_census: options.transitionCensus,
        workflow_census: options.workflowCensus,
        export_census: options.exportCensus,
        service_module: options.skipService ? "SKIPPED" : options.serviceModule,
        renderer_module: options.skipService ? "SKIPPED" : options.rendererModule,
      },
      case_ledgers: {
        model: options.modelLedger,
        transitions: options.transitionLedger,
        workflows: options.workflowLedger,
        exports: options.exportLedger,
        service_dtos: options.serviceLedger,
      },
      suites: counters,
      invariants: {
        exact_production_model_keys: counters.model.fail === 0,
        every_transition_table_executed: counters.transition.fail === 0,
        every_workflow_replayed_twice: counters.workflow.fail === 0,
        every_export_identity_verified: counters.export.fail === 0,
        every_service_transition_executed: options.skipService ? "SKIPPED" : counters.service.fail === 0,
        governed_error_dispositions_verified: options.skipService ? "SKIPPED" : counters.service.fail === 0,
        export_provenance_summary_verified: options.skipService ? "SKIPPED" : counters.service.fail === 0,
        every_export_svg_rendered_twice: options.skipService ? "SKIPPED" : counters.service.fail === 0,
        public_dto_allowlists_verified: options.skipService ? "SKIPPED" : counters.service.fail === 0,
        forbidden_public_field_count: counters.model.fail === 0 && (!options.skipService && counters.service.fail === 0) ? 0 : null,
        state_mutation_count: auditStats.inPlaceStateMutationCount,
        state_mutation_definition: "In-place mutation of a governed current/next state; a transition to a different next-state identity is expected and is not a mutation.",
        STATE_MUTATION_COUNT: auditStats.inPlaceStateMutationCount,
        NEXT_STATE_IDENTITY_CHANGE_IS_MUTATION: false,
      },
    };
    await mkdir(dirname(options.summaryJson), { recursive: true });
    await import("node:fs/promises").then(({ writeFile }) => writeFile(options.summaryJson, `${JSON.stringify(summary, null, 2)}\n`, "utf8"));
    process.stdout.write(`${JSON.stringify(summary)}\n`);
  }
}

await main();
