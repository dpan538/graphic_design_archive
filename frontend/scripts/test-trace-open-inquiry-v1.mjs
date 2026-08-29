#!/usr/bin/env node

import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptPath = fileURLToPath(import.meta.url);
const frontendRoot = resolve(dirname(scriptPath), "..");
const repositoryRoot = resolve(frontendRoot, "..");
const sourceRoot = resolve(
  repositoryRoot,
  "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw",
);
const generatedRegistryPath = resolve(
  frontendRoot,
  "generated/trace-open-inquiry-v1/open-inquiry-registry.v1.json",
);
const builderPath = resolve(
  repositoryRoot,
  "scripts/trace_round16b_integration/build_open_inquiry_registry.py",
);
const validatedReadModelPath = resolve(
  frontendRoot,
  "generated/trace-exploration-v2/production-read-model.json",
);
const jiti = createRequire(import.meta.url)("jiti")(import.meta.url, {
  interopDefault: true,
  alias: {
    "@": resolve(frontendRoot, "src"),
    "server-only": resolve(frontendRoot, "scripts/server-only-marker.mjs"),
  },
});

const SHA256_PATTERN = /^[0-9a-f]{64}$/u;
const EXPECTED_REGISTRY_RECORDS_SHA256 =
  "4a8109c9f4b4296522aead0227331ee5e117fa26a40a9782605192adccdcb44e";
const FORBIDDEN_PROBABILITY_KEYS = new Set([
  "truth_probability",
  "probability_true",
  "likelihood_score",
  "confidence_percentage",
]);
const REQUIRED_POLICY = Object.freeze({
  active: false,
  counts_as_validated: false,
  default_in_validated_results: false,
  display_eligible: true,
  display_layer: "OPEN_INQUIRY",
  eligible_for_validated_composition: false,
  eligible_for_validated_graph: false,
  epistemic_status: "UNRESOLVED_OPEN_INQUIRY",
  external_human_review_status: "PENDING",
  implicit_pair_projection_count: 0,
  may_generate_pair_edges: false,
  may_modify_validated_topology: false,
  pair_projection_policy: "NONE",
  product_eligible: false,
  product_path: null,
  validated_relation: false,
});
const REQUIRED_BOUNDARY = Object.freeze({
  evidence_bounded: true,
  implicit_pair_projection_allowed: false,
  stochastic_display: false,
  validated_layer_contamination_allowed: false,
  validated_topology_mutation_allowed: false,
});
const REQUIRED_CLOSURE_FLAGS = Object.freeze({
  COMPUTATIONAL_SPACE_CLOSURE: false,
  FUNCTION3_CLOSURE: false,
  GLOBAL_COMPOSITION_COHERENCE_CLOSURE: false,
  HIGHER_ORDER_ASSOCIATION_CLOSURE: false,
  PAIR_ASSOCIATION_CLOSURE: false,
  PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE: false,
});
const SHARDS = Object.freeze([
  Object.freeze({
    filename: "scoped-association-hypothesis-ledger-shard-1-v1.tsv",
    bytes: 13_131,
    sha256: "f16deeca67663b05262640cba1512bb46acb0a36ffe8dcae006fd45dc475bed3",
    headers: Object.freeze([
      "evidence_authority_base_sha",
      "shard_id",
      "hypothesis_id",
      "governed_association_id",
      "governed_association_revision_id",
      "canonical_identity_authority_path",
      "canonical_identity_queue_ref",
      "source_ids_json",
      "linked_parent_candidate_id",
      "parent_disposition_preserved",
      "scope_key",
      "scope_note",
      "participant_labels_json",
      "participant_sense_ids_json",
      "arity",
      "participant_order_meaningful",
      "relation_roles_asserted",
      "relation_form",
      "support_mode",
      "exact_group_support_status",
      "global_coherence_status",
      "sense_scope_status",
      "evidence_disposition",
      "governed_identity_status",
      "external_human_review_status",
      "association_activation_status",
      "active_fact_created",
      "product_eligibility",
      "pair_projection_count",
      "subset_projection_count",
      "nonclaims_json",
      "record_sha256",
    ]),
  }),
  Object.freeze({
    filename: "scoped-association-hypothesis-ledger-shard-2-v1.tsv",
    bytes: 4_544,
    sha256: "5b7e04bde8fc0c91f7d141f0ecdccf23579394dafba21e33e91ad512f9ab5a4d",
    headers: Object.freeze([
      "authority_base_sha",
      "shard_id",
      "hypothesis_id",
      "hypothesis_key",
      "association_id",
      "association_revision_id",
      "association_class",
      "arity",
      "participant_labels_json",
      "participant_sense_ids_json",
      "order_semantics",
      "role_semantics",
      "source_id",
      "rights_record_id",
      "bounded_scope",
      "locators_json",
      "support_mode",
      "synthesis_steps_json",
      "counterevidence_json",
      "qualifications_json",
      "source_level_disposition",
      "external_human_review_status",
      "activation_status",
      "product_eligible",
      "product_path",
      "pair_projection_policy",
      "implicit_pair_projection_count",
      "nonclaims_json",
      "closure_effect",
      "record_sha256",
    ]),
  }),
]);
const EXPECTED_INQUIRIES = Object.freeze([
  Object.freeze({
    inquiry_id: "R16B-SCOPED-HYPOTHESIS:a0e30d08141918154af4f53f880ac05f3569b12c48e62c5543248d2f14fbd576",
    inquiry_key: "FORMAL_DESIGN_EDUCATION_1870_1970",
    arity: 3,
    participant_labels: Object.freeze(["institutionalization", "design education", "professionalization"]),
  }),
  Object.freeze({
    inquiry_id: "R16B-SCOPED-HYPOTHESIS:67ac66f329e9e99eea98f88b5774af991f86151074a17a42ae6a0b878e8f223b",
    inquiry_key: "ARCHITECTURAL_CONTACT_ZONE",
    arity: 3,
    participant_labels: Object.freeze(["adaptation", "contact-zone negotiation NEW", "rejection"]),
  }),
  Object.freeze({
    inquiry_id: "R16B-SCOPED-HYPOTHESIS:22ad79d53f782e7d7465c2b97e18887f1b2707c97dda4862010c179bec1406fd",
    inquiry_key: "KERATON_SURAKARTA",
    arity: 2,
    participant_labels: Object.freeze(["adaptation", "cultural negotiation"]),
  }),
  Object.freeze({
    inquiry_id: "R16B-SCOPED-HYPOTHESIS:0fe29f358c06b38af17d854967de28874292c4159c7c3f16ca424313966cf341",
    inquiry_key: "BRUSSELS_EXPO_1958",
    arity: 2,
    participant_labels: Object.freeze(["exhibition", "design diplomacy"]),
  }),
  Object.freeze({
    inquiry_id: "R16B-SCOPED-HYPOTHESIS:d1246bca6141726a7750164794993a29ed5a70da59d6c8dd3a3eabae6a2555c5",
    inquiry_key: "TURIN_INTERNATIONAL_LABOUR_EXHIBITION_1961",
    arity: 3,
    participant_labels: Object.freeze(["exhibition", "propaganda", "design diplomacy"]),
  }),
  Object.freeze({
    inquiry_id: "R16B-SCOPED-HYPOTHESIS:a297b080573533c028d2ee743579da4f5ba0f310694f83ab7836d61ae94f887c",
    inquiry_key: "BAUHAUS_CRAFT_DESIGN_EDUCATION",
    arity: 2,
    participant_labels: Object.freeze(["craft", "design education"]),
  }),
  Object.freeze({
    inquiry_id: "R16B-SCOPED-HYPOTHESIS:6323d405ac092f64fefd009439529b1c1a3c136e42b0e29523ff9a7107071d2a",
    inquiry_key: "PROFESSIONAL_EDUCATION_TRAINING_SENSE",
    arity: 3,
    participant_labels: Object.freeze(["institutionalization", "professional education or training NEW", "professionalization"]),
  }),
  Object.freeze({
    inquiry_id: "R16B-SCOPED-HYPOTHESIS:952e179084b06cee685b8b8bde81bb78d4b3e13fd7cd914647dd8f5908be4a71",
    inquiry_key: "SWEDEN_IN_SYDNEY_1954",
    arity: 4,
    participant_labels: Object.freeze(["exhibition", "trade", "propaganda", "design diplomacy"]),
  }),
  Object.freeze({
    inquiry_id: "R16B-SCOPED-HYPOTHESIS:d9a20fb3c74b9bc084660e7c6a0bbeadbfc17d1bbf9ebc0ad6291f1d461dcb47",
    inquiry_key: "HUTTON_RECIPROCAL_LANDSCAPES_ARTICLE_METHOD_2013",
    arity: 5,
    participant_labels: Object.freeze(["consumption", "production site", "production", "material displacement", "supply chain"]),
  }),
  Object.freeze({
    inquiry_id: "R16B-HYPOTHESIS:801109bf849868a8419ec96ffb4f8b111820e4892b62699936851b59915b6f43",
    inquiry_key: "VISIBLE_LANGUAGE_CANON_CRITIQUE_1967_2015",
    arity: 3,
    participant_labels: Object.freeze(["canonization", "exclusion", "gendering"]),
  }),
  Object.freeze({
    inquiry_id: "R16B-HYPOTHESIS:656fef1cfac074d6b21d87e2c6306733ad0a80b97a73875fdb96fcc47b7c9540",
    inquiry_key: "MEZA_PAINTING_MOBILITY_MEDIATION_MARKET_1790_1836",
    arity: 3,
    participant_labels: Object.freeze(["commodification", "mediation", "mobile object"]),
  }),
]);

let checkCount = 0;

function check(condition, message) {
  checkCount += 1;
  assert(condition, message);
}

function equal(actual, expected, message) {
  checkCount += 1;
  assert.equal(actual, expected, message);
}

function deepEqual(actual, expected, message) {
  checkCount += 1;
  assert.deepEqual(actual, expected, message);
}

function throws(callback, pattern, message) {
  checkCount += 1;
  assert.throws(callback, pattern, message);
}

function sha256(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

function canonicalValue(value) {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, child]) => [key, canonicalValue(child)]),
    );
  }
  return value;
}

function canonicalBytes(value) {
  return Buffer.from(JSON.stringify(canonicalValue(value)), "utf8");
}

function compareText(left, right) {
  return left < right ? -1 : left > right ? 1 : 0;
}

function parseTsv(bytes, label) {
  equal(bytes.at(-1), 0x0a, `${label} ends in LF`);
  check(bytes.length < 2 || bytes.at(-2) !== 0x0a, `${label} has exactly one final LF`);
  check(!bytes.includes(0x0d), `${label} contains no CR bytes`);
  const text = bytes.toString("utf8");
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (quoted) {
      if (character === '"') {
        if (text[index + 1] === '"') {
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
      row.push(field);
      field = "";
    } else if (character === "\n") {
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
    } else {
      field += character;
    }
  }
  check(!quoted, `${label} has no unterminated quoted field`);
  deepEqual(row, [], `${label} parser consumes the final LF`);
  equal(field, "", `${label} parser leaves no partial field`);
  check(rows.length >= 2, `${label} has a header and data rows`);
  const [headers, ...values] = rows;
  check(headers.every((header) => header.length > 0), `${label} headers are nonempty`);
  equal(new Set(headers).size, headers.length, `${label} headers are unique`);
  return {
    headers,
    rows: values.map((fields, index) => {
      equal(fields.length, headers.length, `${label} row ${index + 2} field count`);
      return Object.fromEntries(headers.map((header, fieldIndex) => [header, fields[fieldIndex]]));
    }),
  };
}

function findForbiddenKeys(value, path = "$", findings = []) {
  if (Array.isArray(value)) {
    value.forEach((child, index) => findForbiddenKeys(child, `${path}[${index}]`, findings));
    return findings;
  }
  if (value !== null && typeof value === "object") {
    for (const [key, child] of Object.entries(value)) {
      if (FORBIDDEN_PROBABILITY_KEYS.has(key.toLowerCase())) findings.push(`${path}.${key}`);
      findForbiddenKeys(child, `${path}.${key}`, findings);
    }
  }
  return findings;
}

function collectStrings(value, result = new Set()) {
  if (typeof value === "string") result.add(value);
  else if (Array.isArray(value)) value.forEach((child) => collectStrings(child, result));
  else if (value !== null && typeof value === "object") {
    Object.values(value).forEach((child) => collectStrings(child, result));
  }
  return result;
}

function exactKeys(value, keys, label) {
  deepEqual(Object.keys(value).sort(compareText), [...keys].sort(compareText), `${label} exact keys`);
}

function normalizeSourceRow(shardFilename, sourceRow, sourceRowNumber) {
  const shardOne = shardFilename.endsWith("shard-1-v1.tsv");
  return {
    arity: Number(sourceRow.arity),
    association_id: shardOne ? sourceRow.governed_association_id : sourceRow.association_id,
    association_revision_id: shardOne
      ? sourceRow.governed_association_revision_id
      : sourceRow.association_revision_id,
    authority_base_sha: shardOne
      ? sourceRow.evidence_authority_base_sha
      : sourceRow.authority_base_sha,
    authority_path: shardOne ? sourceRow.canonical_identity_authority_path : "",
    authority_queue_ref: shardOne ? sourceRow.canonical_identity_queue_ref : "",
    bounded_scope: shardOne ? sourceRow.scope_note : sourceRow.bounded_scope,
    counterevidence: shardOne ? null : JSON.parse(sourceRow.counterevidence_json),
    disposition: shardOne ? sourceRow.evidence_disposition : sourceRow.source_level_disposition,
    exact_group_support_status: shardOne ? sourceRow.exact_group_support_status : null,
    global_coherence_status: shardOne ? sourceRow.global_coherence_status : null,
    inquiry_id: sourceRow.hypothesis_id,
    inquiry_key: shardOne ? sourceRow.scope_key : sourceRow.hypothesis_key,
    labels: JSON.parse(sourceRow.participant_labels_json),
    linked_parent_candidate_id: shardOne ? sourceRow.linked_parent_candidate_id : "",
    locators: shardOne ? null : JSON.parse(sourceRow.locators_json),
    nonclaims: JSON.parse(sourceRow.nonclaims_json),
    parent_disposition_preserved: shardOne ? sourceRow.parent_disposition_preserved : "",
    qualifications: shardOne ? null : JSON.parse(sourceRow.qualifications_json),
    relation_form: shardOne ? sourceRow.relation_form : sourceRow.association_class,
    rights_record_ids: shardOne ? null : [sourceRow.rights_record_id],
    sense_ids: JSON.parse(sourceRow.participant_sense_ids_json),
    sense_scope_status: shardOne ? sourceRow.sense_scope_status : null,
    shard_id: sourceRow.shard_id,
    source_activation_status: shardOne
      ? sourceRow.association_activation_status
      : sourceRow.activation_status,
    source_external_human_review_status: sourceRow.external_human_review_status,
    source_ids: shardOne ? JSON.parse(sourceRow.source_ids_json) : [sourceRow.source_id],
    source_ledger_path: `docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/${shardFilename}`,
    source_record_sha256: sourceRow.record_sha256,
    source_row_number: sourceRowNumber,
    support_mode: sourceRow.support_mode,
    synthesis_steps: shardOne ? null : JSON.parse(sourceRow.synthesis_steps_json),
  };
}

function responseJson(response) {
  return response.text().then((text) => JSON.parse(text));
}

function assertHeaders(response, registrySha256, label) {
  equal(response.headers.get("allow"), "GET, HEAD, OPTIONS", `${label} Allow header`);
  equal(response.headers.get("cache-control"), "private, no-store", `${label} cache policy`);
  equal(response.headers.get("vary"), "Accept", `${label} Vary header`);
  equal(response.headers.get("x-content-type-options"), "nosniff", `${label} content type hardening`);
  equal(response.headers.get("x-trace-api-version"), "trace-open-inquiry/v1", `${label} API header`);
  equal(response.headers.get("x-trace-exploration-layer"), "OPEN_INQUIRY", `${label} layer header`);
  equal(response.headers.get("x-trace-validated-relation"), "false", `${label} validated header`);
  equal(
    response.headers.get("x-trace-default-in-validated-results"),
    "false",
    `${label} validated-result default header`,
  );
  equal(
    response.headers.get("x-trace-open-inquiry-registry"),
    registrySha256,
    `${label} registry binding header`,
  );
}

function assertEnvelope(envelope, registrySha256, label) {
  exactKeys(
    envelope,
    ["api_version", "boundary", "data", "layer", "registry_sha256", "schema_version"],
    `${label} envelope`,
  );
  equal(envelope.schema_version, "trace-open-inquiry-response/v1", `${label} response schema`);
  equal(envelope.api_version, "trace-open-inquiry/v1", `${label} API version`);
  equal(envelope.layer, "OPEN_INQUIRY", `${label} layer`);
  equal(envelope.registry_sha256, registrySha256, `${label} registry hash`);
  deepEqual(envelope.boundary, REQUIRED_BOUNDARY, `${label} evidence boundary`);
}

function assertError(error, code, status, registrySha256, label) {
  exactKeys(
    error,
    ["api_version", "code", "instance", "layer", "message", "registry_sha256", "retryable", "schema_version", "status"],
    `${label} error`,
  );
  equal(error.schema_version, "trace-open-inquiry-error/v1", `${label} error schema`);
  equal(error.api_version, "trace-open-inquiry/v1", `${label} error API version`);
  equal(error.layer, "OPEN_INQUIRY", `${label} error layer`);
  equal(error.code, code, `${label} error code`);
  equal(error.status, status, `${label} error status`);
  equal(error.retryable, status >= 500, `${label} retryability`);
  equal(error.registry_sha256, registrySha256, `${label} registry binding`);
}

const sourceRows = [];
const sourceById = new Map();
for (const shard of SHARDS) {
  const path = resolve(sourceRoot, shard.filename);
  const bytes = await readFile(path);
  equal(bytes.byteLength, shard.bytes, `${shard.filename} frozen byte length`);
  equal(sha256(bytes), shard.sha256, `${shard.filename} frozen SHA-256`);
  const parsed = parseTsv(bytes, shard.filename);
  deepEqual(parsed.headers, shard.headers, `${shard.filename} frozen header`);
  parsed.rows.forEach((row, index) => {
    const storedDigest = row.record_sha256;
    check(SHA256_PATTERN.test(storedDigest), `${shard.filename} row ${index + 2} record digest shape`);
    const material = Object.fromEntries(
      Object.entries(row).filter(([key]) => key !== "record_sha256"),
    );
    equal(
      sha256(canonicalBytes(material)),
      storedDigest,
      `${shard.filename} row ${index + 2} independent record digest`,
    );
    if (shard.filename.endsWith("shard-1-v1.tsv")) {
      equal(row.active_fact_created, "false", `${shard.filename} row ${index + 2} creates no active fact`);
      equal(row.pair_projection_count, "0", `${shard.filename} row ${index + 2} projects no pair`);
      equal(row.subset_projection_count, "0", `${shard.filename} row ${index + 2} projects no subset`);
    } else {
      equal(row.product_eligible, "false", `${shard.filename} row ${index + 2} is product-ineligible`);
      equal(row.pair_projection_policy, "NONE", `${shard.filename} row ${index + 2} has no pair projection policy`);
      equal(row.implicit_pair_projection_count, "0", `${shard.filename} row ${index + 2} projects no implicit pair`);
    }
    const normalized = normalizeSourceRow(shard.filename, row, index + 2);
    check(!sourceById.has(normalized.inquiry_id), `${normalized.inquiry_id} is unique across source shards`);
    sourceById.set(normalized.inquiry_id, normalized);
    sourceRows.push(normalized);
  });
}

equal(sourceRows.length, 11, "canonical source inventory contains exactly 11 hypotheses");
deepEqual(
  Object.fromEntries(
    [2, 3, 4, 5].map((arity) => [arity, sourceRows.filter((row) => row.arity === arity).length]),
  ),
  { 2: 3, 3: 6, 4: 1, 5: 1 },
  "canonical source arity census is 3/6/1/1",
);
deepEqual(
  sourceRows.map((row) => ({
    arity: row.arity,
    inquiry_id: row.inquiry_id,
    inquiry_key: row.inquiry_key,
    participant_labels: row.labels,
  })),
  EXPECTED_INQUIRIES,
  "exact source-derived 11-record identity, key, arity, and participant mapping",
);

const builderOutput = execFileSync("python3", [builderPath, "--check"], {
  cwd: repositoryRoot,
  encoding: "utf8",
  stdio: ["ignore", "pipe", "pipe"],
});
check(/PASS/u.test(builderOutput), "deterministic registry builder --check passes");

const registryBytes = await readFile(generatedRegistryPath);
equal(registryBytes.at(-1), 0x0a, "generated registry ends in LF");
check(registryBytes.length < 2 || registryBytes.at(-2) !== 0x0a, "generated registry has one final LF");
const registry = JSON.parse(registryBytes.toString("utf8"));
exactKeys(
  registry,
  [
    "api_version",
    "canonical_serialization",
    "closure_flags",
    "counts",
    "input_bindings",
    "records",
    "records_sha256",
    "registry_version",
  ],
  "registry",
);
equal(registry.registry_version, "trace-open-inquiry-registry/v1", "registry version");
equal(registry.api_version, "trace-open-inquiry/v1", "registry API binding");
equal(
  registry.canonical_serialization,
  "UTF8_SORTED_KEYS_COMPACT_JSON_RECORD_DIGEST",
  "registry canonical serialization",
);
check(SHA256_PATTERN.test(registry.records_sha256), "registry record-set digest shape");
equal(
  registry.records_sha256,
  EXPECTED_REGISTRY_RECORDS_SHA256,
  "independent canonical registry record-set trust pin",
);
equal(
  sha256(canonicalBytes(registry.records)),
  registry.records_sha256,
  "registry record-set digest independently recomputes",
);
deepEqual(registry.closure_flags, REQUIRED_CLOSURE_FLAGS, "all required nonclosure flags remain false");
deepEqual(
  registry.counts,
  {
    active_pending_review_count: 0,
    arity_2_count: 3,
    arity_3_count: 6,
    arity_4_count: 1,
    arity_5_count: 1,
    governed_inquiry_only_association_identity_count: 4,
    implicit_pair_projection_count: 0,
    scoped_higher_order_hypothesis_count: 11,
    ungoverned_hypothesis_count: 7,
  },
  "registry count contract",
);
equal(registry.records.length, 11, "OPEN_INQUIRY_REGISTRY_COUNT=11");
equal(new Set(registry.records.map((record) => record.inquiry_id)).size, 11, "registry IDs are unique");
equal(new Set(registry.records.map((record) => record.inquiry_key)).size, 11, "registry keys are unique");
deepEqual(findForbiddenKeys(registry), [], "registry contains no forbidden probability fields");

const expectedInputBindings = SHARDS.map((shard, index) => ({
  bytes: shard.bytes,
  path: `docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/${shard.filename}`,
  record_count: index === 0 ? 9 : 2,
  sha256: shard.sha256,
}));
deepEqual(registry.input_bindings, expectedInputBindings, "registry binds both exact canonical source shards");

const registryById = new Map(registry.records.map((record) => [record.inquiry_id, record]));
for (const expected of EXPECTED_INQUIRIES) {
  const source = sourceById.get(expected.inquiry_id);
  const record = registryById.get(expected.inquiry_id);
  check(source, `${expected.inquiry_id} source row resolves`);
  check(record, `${expected.inquiry_id} registry record resolves`);
  exactKeys(
    record,
    [
      "active",
      "arity",
      "bounded_scope",
      "counts_as_validated",
      "default_in_validated_results",
      "display_eligible",
      "display_layer",
      "eligible_for_validated_composition",
      "eligible_for_validated_graph",
      "epistemic_status",
      "evidence",
      "external_human_review_status",
      "implicit_pair_projection_count",
      "inquiry_id",
      "inquiry_key",
      "inquiry_only_association_identity",
      "may_generate_pair_edges",
      "may_modify_validated_topology",
      "pair_projection_policy",
      "participant_order_meaningful",
      "participants",
      "product_eligible",
      "product_path",
      "provenance",
      "record_sha256",
      "record_version",
      "relation_form",
      "relation_roles_asserted",
      "validated_relation",
    ],
    `${expected.inquiry_id} record`,
  );
  equal(record.inquiry_key, expected.inquiry_key, `${expected.inquiry_id} stable inquiry key`);
  equal(record.record_version, "trace-open-inquiry/v1", `${expected.inquiry_id} record version`);
  equal(record.arity, expected.arity, `${expected.inquiry_id} arity`);
  deepEqual(record.participants.map((participant) => participant.label), expected.participant_labels, `${expected.inquiry_id} participant labels`);
  deepEqual(record.participants.map((participant) => participant.sense_id), source.sense_ids, `${expected.inquiry_id} participant sense IDs`);
  equal(record.participants.length, record.arity, `${expected.inquiry_id} participant/arity parity`);
  for (const [key, value] of Object.entries(REQUIRED_POLICY)) {
    equal(record[key], value, `${expected.inquiry_id} policy ${key}`);
  }
  equal(record.participant_order_meaningful, false, `${expected.inquiry_id} has no participant order semantics`);
  equal(record.relation_roles_asserted, false, `${expected.inquiry_id} has no asserted relation roles`);
  equal(record.bounded_scope, source.bounded_scope, `${expected.inquiry_id} bounded scope provenance`);
  equal(record.relation_form, source.relation_form, `${expected.inquiry_id} relation-form provenance`);
  check(SHA256_PATTERN.test(record.record_sha256), `${expected.inquiry_id} normalized record digest shape`);
  const recordMaterial = Object.fromEntries(
    Object.entries(record).filter(([key]) => key !== "record_sha256"),
  );
  equal(
    sha256(canonicalBytes(recordMaterial)),
    record.record_sha256,
    `${expected.inquiry_id} normalized record digest`,
  );
  exactKeys(
    record.provenance,
    [
      "authority_base_sha",
      "linked_parent_candidate_id",
      "parent_disposition_preserved",
      "rights_record_ids",
      "shard_id",
      "source_activation_status",
      "source_external_human_review_status",
      "source_ids",
      "source_ledger_path",
      "source_ledger_sha256",
      "source_record_sha256",
      "source_row_number",
    ],
    `${expected.inquiry_id} provenance`,
  );
  equal(record.provenance.authority_base_sha, source.authority_base_sha, `${expected.inquiry_id} authority base`);
  equal(record.provenance.shard_id, source.shard_id, `${expected.inquiry_id} shard ID`);
  equal(record.provenance.source_ledger_path, source.source_ledger_path, `${expected.inquiry_id} source path`);
  equal(
    record.provenance.source_ledger_sha256,
    SHARDS.find((shard) => source.source_ledger_path.endsWith(shard.filename)).sha256,
    `${expected.inquiry_id} source-ledger hash`,
  );
  equal(record.provenance.source_row_number, source.source_row_number, `${expected.inquiry_id} source row number`);
  equal(record.provenance.source_record_sha256, source.source_record_sha256, `${expected.inquiry_id} source-record hash`);
  deepEqual(record.provenance.source_ids, source.source_ids, `${expected.inquiry_id} source identities`);
  deepEqual(record.provenance.rights_record_ids, source.rights_record_ids, `${expected.inquiry_id} rights identities`);
  equal(
    record.provenance.linked_parent_candidate_id,
    source.linked_parent_candidate_id || null,
    `${expected.inquiry_id} linked-parent provenance`,
  );
  equal(
    record.provenance.parent_disposition_preserved,
    source.parent_disposition_preserved || null,
    `${expected.inquiry_id} parent-disposition provenance`,
  );
  equal(
    record.provenance.source_external_human_review_status,
    source.source_external_human_review_status,
    `${expected.inquiry_id} source review disposition`,
  );
  equal(
    record.provenance.source_activation_status,
    source.source_activation_status,
    `${expected.inquiry_id} source activation disposition`,
  );
  exactKeys(
    record.evidence,
    [
      "counterevidence",
      "disposition",
      "exact_group_support_status",
      "global_coherence_status",
      "locators",
      "nonclaims",
      "qualifications",
      "sense_scope_status",
      "support_mode",
      "synthesis_steps",
    ],
    `${expected.inquiry_id} evidence`,
  );
  equal(record.evidence.support_mode, source.support_mode, `${expected.inquiry_id} support mode`);
  equal(record.evidence.disposition, source.disposition, `${expected.inquiry_id} evidence disposition`);
  equal(
    record.evidence.exact_group_support_status,
    source.exact_group_support_status,
    `${expected.inquiry_id} exact-group support status`,
  );
  equal(
    record.evidence.global_coherence_status,
    source.global_coherence_status,
    `${expected.inquiry_id} global-coherence status`,
  );
  equal(record.evidence.sense_scope_status, source.sense_scope_status, `${expected.inquiry_id} sense-scope status`);
  deepEqual(record.evidence.locators, source.locators, `${expected.inquiry_id} evidence locators`);
  deepEqual(record.evidence.synthesis_steps, source.synthesis_steps, `${expected.inquiry_id} synthesis steps`);
  deepEqual(record.evidence.counterevidence, source.counterevidence, `${expected.inquiry_id} counterevidence`);
  deepEqual(record.evidence.qualifications, source.qualifications, `${expected.inquiry_id} qualifications`);
  deepEqual(record.evidence.nonclaims, source.nonclaims, `${expected.inquiry_id} source nonclaims`);
  const identity = record.inquiry_only_association_identity;
  if (source.association_id) {
    check(identity, `${expected.inquiry_id} preserves inquiry-only association identity`);
    equal(identity.association_id, source.association_id, `${expected.inquiry_id} association identity`);
    equal(identity.association_revision_id, source.association_revision_id, `${expected.inquiry_id} revision identity`);
    equal(identity.authority_path, source.authority_path || null, `${expected.inquiry_id} authority path`);
    equal(identity.authority_queue_ref, source.authority_queue_ref || null, `${expected.inquiry_id} authority queue ref`);
  } else {
    equal(identity, null, `${expected.inquiry_id} does not manufacture association identity`);
  }
}

equal(
  registry.records.filter((record) => record.active && record.external_human_review_status === "PENDING").length,
  0,
  "ACTIVE_PENDING_REVIEW_COUNT=0",
);
equal(
  registry.records.reduce((total, record) => total + record.implicit_pair_projection_count, 0),
  0,
  "OPEN_INQUIRY_IMPLICIT_PAIR_PROJECTION_COUNT=0",
);
equal(
  registry.records.filter((record) => record.inquiry_only_association_identity !== null).length,
  4,
  "exactly four records preserve inquiry-only association identities",
);

const registryModule = jiti(resolve(frontendRoot, "src/features/trace-v49/open-inquiry-v1/registry.server.ts"));
const service = jiti(resolve(frontendRoot, "src/features/trace-v49/open-inquiry-v1/service.server.ts"));
const controller = jiti(resolve(frontendRoot, "src/features/trace-v49/open-inquiry-v1/controller.server.ts"));
const runtimeRegistry = registryModule.getOpenInquiryRegistry();
deepEqual(runtimeRegistry, registry, "runtime registry is byte-source equivalent to canonical artifact");
equal(
  registryModule.getOpenInquiryRegistryIdentity(),
  registry.records_sha256,
  "runtime registry identity binds normalized record digest",
);
check(Object.isFrozen(runtimeRegistry), "runtime registry is deeply frozen at its root");
check(Object.isFrozen(runtimeRegistry.records), "runtime registry record array is frozen");
check(runtimeRegistry.records.every((record) => Object.isFrozen(record)), "every runtime registry record is frozen");

const integrityMutations = [
  ["top-level record count", (candidate) => { candidate.counts.scoped_higher_order_hypothesis_count = 10; }],
  ["record-set digest", (candidate) => { candidate.records_sha256 = "0".repeat(64); }],
  ["validated relation", (candidate) => { candidate.records[0].validated_relation = true; }],
  ["validated graph eligibility", (candidate) => { candidate.records[0].eligible_for_validated_graph = true; }],
  ["implicit pair projection", (candidate) => { candidate.records[0].implicit_pair_projection_count = 1; }],
  ["topology mutation", (candidate) => { candidate.records[0].may_modify_validated_topology = true; }],
  ["forbidden probability field", (candidate) => { candidate.records[0].truth_probability = 0.5; }],
  ["participant/arity mismatch", (candidate) => { candidate.records[0].arity = 4; }],
  ["duplicate stable ID", (candidate) => { candidate.records[1].inquiry_id = candidate.records[0].inquiry_id; }],
  ["source binding hash", (candidate) => { candidate.input_bindings[0].sha256 = "0".repeat(64); }],
];
for (const [label, mutate] of integrityMutations) {
  const candidate = structuredClone(registry);
  mutate(candidate);
  throws(
    () => registryModule.validateOpenInquiryRegistry(candidate),
    /REGISTRY_INTEGRITY_FAILURE/u,
    `runtime validator rejects ${label} corruption`,
  );
}

const listResult = service.listOpenInquiries();
check(listResult.ok, "Open Inquiry list service succeeds");
assertEnvelope(listResult.data, registry.records_sha256, "list service");
equal(listResult.data.data.count, 11, "list service returns exactly 11 records");
deepEqual(listResult.data.data.items, registry.records, "list service returns the canonical deterministic inventory");
for (const inquiryId of EXPECTED_INQUIRIES.map((record) => record.inquiry_id)) {
  const detailResult = service.retrieveOpenInquiry(inquiryId);
  check(detailResult.ok, `${inquiryId} detail service succeeds`);
  assertEnvelope(detailResult.data, registry.records_sha256, `${inquiryId} detail service`);
  equal(detailResult.data.data.item.inquiry_id, inquiryId, `${inquiryId} detail identity is exact`);
}
for (const inquiryId of ["", "unknown", "R16B-HYPOTHESIS:0", "R16B-SCOPED-HYPOTHESIS:../escape"]) {
  const missing = service.retrieveOpenInquiry(inquiryId);
  check(!missing.ok, `${JSON.stringify(inquiryId)} does not resolve`);
  equal(missing.code, "OPEN_INQUIRY_NOT_FOUND", `${JSON.stringify(inquiryId)} not-found code`);
  equal(missing.status, 404, `${JSON.stringify(inquiryId)} not-found status`);
}

const listResponse = await controller.dispatchOpenInquiryListRequest(
  new Request("http://localhost/api/trace/v1/open-inquiry"),
);
equal(listResponse.status, 200, "list controller GET status");
assertHeaders(listResponse, registry.records_sha256, "list GET");
const listPayload = await responseJson(listResponse);
assertEnvelope(listPayload, registry.records_sha256, "list controller");
equal(listPayload.data.count, 11, "list controller inventory count");

const representativeId = EXPECTED_INQUIRIES[0].inquiry_id;
const detailResponse = await controller.dispatchOpenInquiryDetailRequest(
  new Request(`http://localhost/api/trace/v1/open-inquiry/${representativeId}`),
  representativeId,
);
equal(detailResponse.status, 200, "detail controller GET status");
assertHeaders(detailResponse, registry.records_sha256, "detail GET");
const detailPayload = await responseJson(detailResponse);
assertEnvelope(detailPayload, registry.records_sha256, "detail controller");
equal(detailPayload.data.item.inquiry_id, representativeId, "detail controller exact stable ID");

for (const query of [
  "include_unresolved=true",
  "include-unresolved=true",
  "sort=inquiry_key",
  "page=1",
  "random=true",
  "seed=42",
  "unknown=value",
]) {
  const queryResponse = await controller.dispatchOpenInquiryListRequest(
    new Request(`http://localhost/api/trace/v1/open-inquiry?${query}`),
  );
  equal(queryResponse.status, 400, `list rejects query ${query}`);
  assertError(
    await responseJson(queryResponse),
    "UNSUPPORTED_QUERY_PARAMETER",
    400,
    registry.records_sha256,
    `query ${query}`,
  );
}

const detailQueryResponse = await controller.dispatchOpenInquiryDetailRequest(
  new Request(`http://localhost/api/trace/v1/open-inquiry/${representativeId}?sort=random`),
  representativeId,
);
equal(detailQueryResponse.status, 400, "detail rejects every query parameter");
assertError(
  await responseJson(detailQueryResponse),
  "UNSUPPORTED_QUERY_PARAMETER",
  400,
  registry.records_sha256,
  "detail query",
);

for (const [label, dispatch, url, expectedStatus, expectedCode] of [
  [
    "list HEAD",
    (request) => controller.dispatchOpenInquiryListRequest(request),
    "http://localhost/api/trace/v1/open-inquiry",
    200,
    null,
  ],
  [
    "detail HEAD",
    (request) => controller.dispatchOpenInquiryDetailRequest(request, representativeId),
    `http://localhost/api/trace/v1/open-inquiry/${representativeId}`,
    200,
    null,
  ],
  [
    "unknown detail HEAD",
    (request) => controller.dispatchOpenInquiryDetailRequest(request, "unknown"),
    "http://localhost/api/trace/v1/open-inquiry/unknown",
    404,
    "OPEN_INQUIRY_NOT_FOUND",
  ],
]) {
  const response = await dispatch(new Request(url, { method: "HEAD" }));
  equal(response.status, expectedStatus, `${label} status`);
  equal(await response.text(), "", `${label} has no body`);
  assertHeaders(response, registry.records_sha256, label);
  if (expectedCode) equal(response.status, 404, `${label} mirrors GET failure status`);
}

for (const [label, dispatch, url] of [
  [
    "list OPTIONS",
    (request) => controller.dispatchOpenInquiryListRequest(request),
    "http://localhost/api/trace/v1/open-inquiry",
  ],
  [
    "detail OPTIONS",
    (request) => controller.dispatchOpenInquiryDetailRequest(request, representativeId),
    `http://localhost/api/trace/v1/open-inquiry/${representativeId}`,
  ],
]) {
  const response = await dispatch(new Request(url, { method: "OPTIONS" }));
  equal(response.status, 204, `${label} status`);
  equal(await response.text(), "", `${label} has no body`);
  assertHeaders(response, registry.records_sha256, label);
}

for (const [label, dispatch, url] of [
  [
    "list POST",
    (request) => controller.dispatchOpenInquiryListRequest(request),
    "http://localhost/api/trace/v1/open-inquiry",
  ],
  [
    "detail DELETE",
    (request) => controller.dispatchOpenInquiryDetailRequest(request, representativeId),
    `http://localhost/api/trace/v1/open-inquiry/${representativeId}`,
  ],
]) {
  const method = label.endsWith("POST") ? "POST" : "DELETE";
  const response = await dispatch(new Request(url, { method }));
  equal(response.status, 405, `${label} read-only status`);
  assertError(
    await responseJson(response),
    "METHOD_NOT_ALLOWED",
    405,
    registry.records_sha256,
    label,
  );
}

const unknownResponse = await controller.dispatchOpenInquiryDetailRequest(
  new Request("http://localhost/api/trace/v1/open-inquiry/unknown"),
  "unknown",
);
equal(unknownResponse.status, 404, "unknown detail controller status");
assertError(
  await responseJson(unknownResponse),
  "OPEN_INQUIRY_NOT_FOUND",
  404,
  registry.records_sha256,
  "unknown detail",
);

const rootRoutePath = resolve(frontendRoot, "src/app/api/trace/v1/open-inquiry/route.ts");
const detailRoutePath = resolve(frontendRoot, "src/app/api/trace/v1/open-inquiry/[inquiryId]/route.ts");
const rootRouteSource = await readFile(rootRoutePath, "utf8");
const detailRouteSource = await readFile(detailRoutePath, "utf8");
for (const [label, source] of [["root route", rootRouteSource], ["detail route", detailRouteSource]]) {
  const exportedMethods = [...source.matchAll(/export\s+(?:async\s+)?function\s+([A-Z]+)/gu)]
    .map((match) => match[1])
    .sort(compareText);
  deepEqual(exportedMethods, ["GET", "HEAD", "OPTIONS"], `${label} exports only read methods`);
  check(!/Math\.random|randomUUID|Date\.now/u.test(source), `${label} has no stochastic display code`);
}

try {
  const rootRoute = jiti(rootRoutePath);
  const detailRoute = jiti(detailRoutePath);
  const routeListResponse = await rootRoute.GET(
    new Request("http://localhost/api/trace/v1/open-inquiry"),
  );
  equal(routeListResponse.status, 200, "App Router root GET delegates to list controller");
  equal((await responseJson(routeListResponse)).data.count, 11, "App Router root GET count");
  const routeListHead = await rootRoute.HEAD(
    new Request("http://localhost/api/trace/v1/open-inquiry", { method: "HEAD" }),
  );
  equal(routeListHead.status, 200, "App Router root HEAD status");
  equal(await routeListHead.text(), "", "App Router root HEAD body");
  equal(
    (await rootRoute.OPTIONS(new Request("http://localhost/api/trace/v1/open-inquiry", { method: "OPTIONS" }))).status,
    204,
    "App Router root OPTIONS status",
  );
  const routeDetailResponse = await detailRoute.GET(
    new Request(`http://localhost/api/trace/v1/open-inquiry/${representativeId}`),
    { params: Promise.resolve({ inquiryId: representativeId }) },
  );
  equal(routeDetailResponse.status, 200, "App Router detail GET awaits Promise params");
  equal((await responseJson(routeDetailResponse)).data.item.inquiry_id, representativeId, "App Router detail identity");
  const routeDetailHead = await detailRoute.HEAD(
    new Request(`http://localhost/api/trace/v1/open-inquiry/${representativeId}`, { method: "HEAD" }),
    { params: Promise.resolve({ inquiryId: representativeId }) },
  );
  equal(routeDetailHead.status, 200, "App Router detail HEAD status");
  equal(await routeDetailHead.text(), "", "App Router detail HEAD body");
  equal(
    (await detailRoute.OPTIONS(
      new Request(`http://localhost/api/trace/v1/open-inquiry/${representativeId}`, { method: "OPTIONS" }),
      { params: Promise.resolve({ inquiryId: representativeId }) },
    )).status,
    204,
    "App Router detail OPTIONS status",
  );
} catch (error) {
  throw new Error(`OPEN_INQUIRY_APP_ROUTER_IMPORT_OR_DISPATCH_FAILED:${error instanceof Error ? error.message : String(error)}`);
}

const validatedBytes = await readFile(validatedReadModelPath);
equal(
  sha256(validatedBytes),
  "53eaf59c95446eeb3781a7153183c54b3ff59fd52f21744cc917053959dfdcc9",
  "independent validated v2 read-model trust pin",
);
const validatedModel = JSON.parse(validatedBytes.toString("utf8"));
equal(validatedModel.capabilities.association_count, 21, "VALIDATED_PAIR_ASSOCIATION_COUNT=21 capability");
equal(validatedModel.associations.length, 21, "VALIDATED_PAIR_ASSOCIATION_COUNT=21 payload");
check(validatedModel.associations.every((association) => association.generic_association_only === true), "all 21 validated associations remain generic pair associations");
const registryText = registryBytes.toString("utf8");
for (const inquiryId of EXPECTED_INQUIRIES.map((record) => record.inquiry_id)) {
  check(!validatedBytes.includes(Buffer.from(inquiryId, "utf8")), `${inquiryId} is absent from validated v2`);
}
check(!/OPEN_INQUIRY|UNRESOLVED_OPEN_INQUIRY/u.test(validatedBytes.toString("utf8")), "validated v2 has no Open Inquiry layer or status");
check(!/include[_-]unresolved/iu.test(validatedBytes.toString("utf8")), "validated v2 has no include-unresolved switch");

const validatedArtifactIds = new Set([
  ...validatedModel.associations.map((record) => record.association_id),
  ...Object.keys(validatedModel.compositions),
  ...Object.keys(validatedModel.states),
  ...Object.keys(validatedModel.transitions),
]);
const registryStrings = collectStrings(registry);
deepEqual(
  [...validatedArtifactIds].filter((identifier) => registryStrings.has(identifier)),
  [],
  "Open Inquiry contains no validated association, composition, state, or transition artifact IDs",
);
check(!/EXPORT_CURRENT_STATE|portrait_card|image\/png|\.png\b/u.test(registryText), "Open Inquiry contains no validated export artifact or preset");
equal(
  registry.records.filter((record) => record.validated_relation).length,
  0,
  "OPEN_INQUIRY_LEAK_INTO_VALIDATED_ASSOCIATION_COUNT=0",
);
equal(
  registry.records.filter((record) => record.eligible_for_validated_composition).length,
  0,
  "OPEN_INQUIRY_LEAK_INTO_VALIDATED_COMPOSITION_COUNT=0",
);
equal(
  registry.records.filter((record) => record.may_modify_validated_topology).length,
  0,
  "OPEN_INQUIRY_VALIDATED_TOPOLOGY_MUTATION_COUNT=0",
);
equal(
  registry.records.filter((record) => record.default_in_validated_results).length,
  0,
  "OPEN_INQUIRY_VALIDATED_METRIC_CONTAMINATION_COUNT=0",
);

const isolationSources = await Promise.all([
  "src/features/trace-v49/open-inquiry-v1/registry.server.ts",
  "src/features/trace-v49/open-inquiry-v1/service.server.ts",
  "src/features/trace-v49/open-inquiry-v1/controller.server.ts",
  "src/app/api/trace/v1/open-inquiry/route.ts",
  "src/app/api/trace/v1/open-inquiry/[inquiryId]/route.ts",
].map(async (path) => [path, await readFile(resolve(frontendRoot, path), "utf8")]));
for (const [path, source] of isolationSources) {
  check(!/exploration-v2|exploration-v3|production-read-model/iu.test(source), `${path} does not import validated or v3 runtime state`);
  check(!/Math\.random|randomUUID|crypto\.random|Date\.now/iu.test(source), `${path} has no stochastic display implementation`);
}

const validatedImplementationSources = await Promise.all([
  "src/app/api/trace/v2/exploration/route.ts",
  "src/app/api/trace/v2/exploration/[...path]/route.ts",
  "src/features/trace-v49/exploration/backend/controller.server.ts",
  "src/features/trace-v49/exploration/backend/read-model.server.ts",
  "src/features/trace-v49/exploration/backend/renderer.server.ts",
  "src/features/trace-v49/exploration/backend/service.server.ts",
  "src/features/trace-v49/exploration/backend/types.ts",
].map(async (path) => [path, await readFile(resolve(frontendRoot, path), "utf8")]));
for (const [path, source] of validatedImplementationSources) {
  check(!/include[_-]?unresolved/iu.test(source), `${path} has no include-unresolved switch`);
  check(!/open[_-]?inquiry|UNRESOLVED_OPEN_INQUIRY/iu.test(source), `${path} does not import or mix Open Inquiry`);
}

process.stdout.write(`${JSON.stringify({
  ACTIVE_PENDING_REVIEW_COUNT: 0,
  ARITY_2_COUNT: 3,
  ARITY_3_COUNT: 6,
  ARITY_4_COUNT: 1,
  ARITY_5_COUNT: 1,
  OPEN_INQUIRY_IMPLICIT_PAIR_PROJECTION_COUNT: 0,
  OPEN_INQUIRY_LEAK_INTO_VALIDATED_ASSOCIATION_COUNT: 0,
  OPEN_INQUIRY_LEAK_INTO_VALIDATED_COMPOSITION_COUNT: 0,
  OPEN_INQUIRY_REGISTRY_COUNT: 11,
  OPEN_INQUIRY_VALIDATED_EXPORT_LEAK_COUNT: 0,
  OPEN_INQUIRY_VALIDATED_METRIC_CONTAMINATION_COUNT: 0,
  OPEN_INQUIRY_VALIDATED_TOPOLOGY_MUTATION_COUNT: 0,
  SCOPED_HIGHER_ORDER_HYPOTHESIS_COUNT: 11,
  VALIDATED_PAIR_ASSOCIATION_COUNT: 21,
  check_count: checkCount,
  records_sha256: registry.records_sha256,
  status: "PASS",
}, null, 2)}\n`);
