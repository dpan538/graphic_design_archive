#!/usr/bin/env node
/** Verify the isolated Open Inquiry contract against a built production server. */

import { readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const registryPath = resolve(
  repositoryRoot,
  "frontend/generated/trace-open-inquiry-v1/open-inquiry-registry.v1.json",
);

function argumentsMap(argv) {
  const result = {};
  for (let index = 2; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--")) throw new Error(`UNEXPECTED_ARGUMENT:${token}`);
    const value = argv[index + 1];
    if (value === undefined || value.startsWith("--")) {
      throw new Error(`MISSING_ARGUMENT_VALUE:${token}`);
    }
    result[token.slice(2).replaceAll("-", "_")] = value;
    index += 1;
  }
  return result;
}

function requireValue(condition, code) {
  if (!condition) throw new Error(code);
}

function canonicalJson(value) {
  if (
    value === null
    || typeof value === "boolean"
    || typeof value === "number"
    || typeof value === "string"
  ) {
    return JSON.stringify(value) ?? "null";
  }
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  return `{${Object.keys(value).sort().map((key) => (
    `${JSON.stringify(key)}:${canonicalJson(value[key])}`
  )).join(",")}}`;
}

function countForbiddenProbabilityFields(value) {
  const forbidden = new Set([
    "truth_probability",
    "probability_true",
    "likelihood_score",
    "confidence_percentage",
  ]);
  if (Array.isArray(value)) {
    return value.reduce((total, child) => total + countForbiddenProbabilityFields(child), 0);
  }
  if (value === null || typeof value !== "object") return 0;
  return Object.entries(value).reduce(
    (total, [key, child]) => total + Number(forbidden.has(key)) + countForbiddenProbabilityFields(child),
    0,
  );
}

function countInquiryMaterial(value, inquiryIds) {
  const text = canonicalJson(value);
  let count = 0;
  for (const inquiryId of inquiryIds) count += Number(text.includes(inquiryId));
  count += Number(text.includes("UNRESOLVED_OPEN_INQUIRY"));
  count += Number(text.includes("OPEN_INQUIRY"));
  return count;
}

function assertHeaders(response, registrySha256, label) {
  const expected = {
    allow: "GET, HEAD, OPTIONS",
    "cache-control": "private, no-store",
    "x-content-type-options": "nosniff",
    "x-trace-api-version": "trace-open-inquiry/v1",
    "x-trace-exploration-layer": "OPEN_INQUIRY",
    "x-trace-validated-relation": "false",
    "x-trace-default-in-validated-results": "false",
    "x-trace-open-inquiry-registry": registrySha256,
  };
  for (const [name, value] of Object.entries(expected)) {
    requireValue(response.headers.get(name) === value, `${label}:HEADER:${name}`);
  }
  const varyTokens = (response.headers.get("vary") ?? "")
    .split(",")
    .map((value) => value.trim().toLowerCase());
  requireValue(varyTokens.includes("accept"), `${label}:HEADER:vary:accept`);
}

async function jsonResponse(response, label) {
  const text = await response.text();
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new Error(`${label}:INVALID_JSON:${error instanceof Error ? error.message : String(error)}`);
  }
}

const args = argumentsMap(process.argv);
requireValue(typeof args.base_url === "string", "BASE_URL_REQUIRED");
const baseUrl = new URL(args.base_url);
requireValue(["127.0.0.1", "localhost", "::1"].includes(baseUrl.hostname), "LOOPBACK_ONLY");
requireValue(baseUrl.protocol === "http:", "HTTP_LOOPBACK_REQUIRED");

const registry = JSON.parse(await readFile(registryPath, "utf8"));
const inquiryIds = registry.records.map((record) => record.inquiry_id);
requireValue(registry.records.length === 11, "REGISTRY_COUNT");
requireValue(new Set(inquiryIds).size === 11, "REGISTRY_ID_UNIQUENESS");
const root = new URL("/api/trace/v1/open-inquiry", baseUrl);
let caseCount = 0;

async function request(path, init, expectedStatus, label) {
  const response = await fetch(new URL(path, baseUrl), init);
  caseCount += 1;
  requireValue(response.status === expectedStatus, `${label}:STATUS:${response.status}`);
  assertHeaders(response, registry.records_sha256, label);
  return response;
}

const listResponse = await request(root, undefined, 200, "LIST_GET");
const listPayload = await jsonResponse(listResponse, "LIST_GET");
requireValue(listPayload.api_version === "trace-open-inquiry/v1", "LIST_API_VERSION");
requireValue(listPayload.layer === "OPEN_INQUIRY", "LIST_LAYER");
requireValue(listPayload.registry_sha256 === registry.records_sha256, "LIST_REGISTRY_BINDING");
requireValue(listPayload.data.count === 11, "LIST_COUNT");
requireValue(
  canonicalJson(listPayload.data.items) === canonicalJson(registry.records),
  "LIST_CANONICAL_INVENTORY",
);
requireValue(countForbiddenProbabilityFields(listPayload) === 0, "LIST_PROBABILITY_FIELD");

for (const inquiryId of inquiryIds) {
  const response = await request(
    `/api/trace/v1/open-inquiry/${encodeURIComponent(inquiryId)}`,
    undefined,
    200,
    `DETAIL_GET:${inquiryId}`,
  );
  const payload = await jsonResponse(response, `DETAIL_GET:${inquiryId}`);
  requireValue(payload.data.item.inquiry_id === inquiryId, `DETAIL_ID:${inquiryId}`);
  requireValue(payload.data.item.validated_relation === false, `DETAIL_VALIDATED:${inquiryId}`);
  requireValue(payload.data.item.may_generate_pair_edges === false, `DETAIL_PAIR_EDGE:${inquiryId}`);
  requireValue(
    payload.data.item.may_modify_validated_topology === false,
    `DETAIL_TOPOLOGY:${inquiryId}`,
  );
  requireValue(countForbiddenProbabilityFields(payload) === 0, `DETAIL_PROBABILITY_FIELD:${inquiryId}`);
}

for (const [path, expectedStatus, label] of [
  ["/api/trace/v1/open-inquiry", 200, "LIST_HEAD"],
  [`/api/trace/v1/open-inquiry/${encodeURIComponent(inquiryIds[0])}`, 200, "DETAIL_HEAD"],
  ["/api/trace/v1/open-inquiry/unknown", 404, "UNKNOWN_HEAD"],
]) {
  const response = await request(path, { method: "HEAD" }, expectedStatus, label);
  requireValue((await response.text()) === "", `${label}:BODY`);
}

for (const [path, label] of [
  ["/api/trace/v1/open-inquiry", "LIST_OPTIONS"],
  [`/api/trace/v1/open-inquiry/${encodeURIComponent(inquiryIds[0])}`, "DETAIL_OPTIONS"],
]) {
  const response = await request(path, { method: "OPTIONS" }, 204, label);
  requireValue((await response.text()) === "", `${label}:BODY`);
}

for (const query of [
  "include_unresolved=true",
  "include-unresolved=true",
  "sort=inquiry_key",
  "page=1",
  "random=true",
  "seed=42",
  "unknown=value",
]) {
  const response = await request(
    `/api/trace/v1/open-inquiry?${query}`,
    undefined,
    400,
    `LIST_QUERY:${query}`,
  );
  const payload = await jsonResponse(response, `LIST_QUERY:${query}`);
  requireValue(payload.code === "UNSUPPORTED_QUERY_PARAMETER", `LIST_QUERY_CODE:${query}`);
}

const detailQuery = await request(
  `/api/trace/v1/open-inquiry/${encodeURIComponent(inquiryIds[0])}?sort=random`,
  undefined,
  400,
  "DETAIL_QUERY",
);
requireValue(
  (await jsonResponse(detailQuery, "DETAIL_QUERY")).code === "UNSUPPORTED_QUERY_PARAMETER",
  "DETAIL_QUERY_CODE",
);

const unknown = await request(
  "/api/trace/v1/open-inquiry/unknown",
  undefined,
  404,
  "UNKNOWN_GET",
);
requireValue(
  (await jsonResponse(unknown, "UNKNOWN_GET")).code === "OPEN_INQUIRY_NOT_FOUND",
  "UNKNOWN_GET_CODE",
);

const validatedResponse = await fetch(new URL("/api/trace/v2/exploration/capabilities", baseUrl));
caseCount += 1;
requireValue(validatedResponse.status === 200, `VALIDATED_CAPABILITIES_STATUS:${validatedResponse.status}`);
const validatedPayload = await jsonResponse(validatedResponse, "VALIDATED_CAPABILITIES");
requireValue(validatedPayload.association_count === 21, "VALIDATED_PAIR_COUNT");
requireValue(
  countInquiryMaterial(validatedPayload, inquiryIds) === 0,
  "VALIDATED_CAPABILITIES_OPEN_INQUIRY_LEAK",
);

const summary = {
  schema_version: "trace-open-inquiry-production-http-verification/v1",
  status: "PASS",
  api_version: "trace-open-inquiry/v1",
  layer: "OPEN_INQUIRY",
  case_count: caseCount,
  case_failure_count: 0,
  registry_count: registry.records.length,
  registry_sha256: registry.records_sha256,
  validated_pair_association_count: validatedPayload.association_count,
  open_inquiry_validated_response_leak_count: 0,
  unsupported_query_acceptance_count: 0,
  stochastic_display_case_count: 0,
  external_network_used: false,
  loopback_only: true,
};
if (args.output) await writeFile(resolve(args.output), `${JSON.stringify(summary, null, 2)}\n`, "utf8");
console.log(JSON.stringify(summary));
