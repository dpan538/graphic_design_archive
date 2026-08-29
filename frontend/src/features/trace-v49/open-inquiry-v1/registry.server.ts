import "server-only";

import { createHash } from "node:crypto";
import registryJson from "../../../../generated/trace-open-inquiry-v1/open-inquiry-registry.v1.json";
import {
  TRACE_OPEN_INQUIRY_API_VERSION,
  TRACE_OPEN_INQUIRY_LAYER,
  TRACE_OPEN_INQUIRY_REGISTRY_VERSION,
} from "./types.ts";
import type {
  OpenInquiryArity,
  OpenInquiryInputBinding,
  OpenInquiryRecord,
  OpenInquiryRegistry,
} from "./types.ts";

const SHA256_PATTERN = /^[0-9a-f]{64}$/u;
const INQUIRY_ID_PATTERN = /^R16B-(?:SCOPED-)?HYPOTHESIS:[0-9a-f]{64}$/u;
const DISALLOWED_PROBABILITY_FIELDS = new Set([
  "truth_probability",
  "probability_true",
  "likelihood_score",
  "confidence_percentage",
]);

const EXPECTED_IDENTITIES_SOURCE_ORDER = [
  [
    "R16B-SCOPED-HYPOTHESIS:a0e30d08141918154af4f53f880ac05f3569b12c48e62c5543248d2f14fbd576",
    "FORMAL_DESIGN_EDUCATION_1870_1970",
  ],
  [
    "R16B-SCOPED-HYPOTHESIS:67ac66f329e9e99eea98f88b5774af991f86151074a17a42ae6a0b878e8f223b",
    "ARCHITECTURAL_CONTACT_ZONE",
  ],
  [
    "R16B-SCOPED-HYPOTHESIS:22ad79d53f782e7d7465c2b97e18887f1b2707c97dda4862010c179bec1406fd",
    "KERATON_SURAKARTA",
  ],
  [
    "R16B-SCOPED-HYPOTHESIS:0fe29f358c06b38af17d854967de28874292c4159c7c3f16ca424313966cf341",
    "BRUSSELS_EXPO_1958",
  ],
  [
    "R16B-SCOPED-HYPOTHESIS:d1246bca6141726a7750164794993a29ed5a70da59d6c8dd3a3eabae6a2555c5",
    "TURIN_INTERNATIONAL_LABOUR_EXHIBITION_1961",
  ],
  [
    "R16B-SCOPED-HYPOTHESIS:a297b080573533c028d2ee743579da4f5ba0f310694f83ab7836d61ae94f887c",
    "BAUHAUS_CRAFT_DESIGN_EDUCATION",
  ],
  [
    "R16B-SCOPED-HYPOTHESIS:6323d405ac092f64fefd009439529b1c1a3c136e42b0e29523ff9a7107071d2a",
    "PROFESSIONAL_EDUCATION_TRAINING_SENSE",
  ],
  [
    "R16B-SCOPED-HYPOTHESIS:952e179084b06cee685b8b8bde81bb78d4b3e13fd7cd914647dd8f5908be4a71",
    "SWEDEN_IN_SYDNEY_1954",
  ],
  [
    "R16B-SCOPED-HYPOTHESIS:d9a20fb3c74b9bc084660e7c6a0bbeadbfc17d1bbf9ebc0ad6291f1d461dcb47",
    "HUTTON_RECIPROCAL_LANDSCAPES_ARTICLE_METHOD_2013",
  ],
  [
    "R16B-HYPOTHESIS:801109bf849868a8419ec96ffb4f8b111820e4892b62699936851b59915b6f43",
    "VISIBLE_LANGUAGE_CANON_CRITIQUE_1967_2015",
  ],
  [
    "R16B-HYPOTHESIS:656fef1cfac074d6b21d87e2c6306733ad0a80b97a73875fdb96fcc47b7c9540",
    "MEZA_PAINTING_MOBILITY_MEDIATION_MARKET_1790_1836",
  ],
] as const;

const EXPECTED_IDENTITIES = Object.freeze(
  [...EXPECTED_IDENTITIES_SOURCE_ORDER].sort((left, right) => compareCodePoints(left[0], right[0])),
);

const EXPECTED_INPUT_BINDINGS: readonly OpenInquiryInputBinding[] = [
  {
    path: "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/scoped-association-hypothesis-ledger-shard-1-v1.tsv",
    sha256: "f16deeca67663b05262640cba1512bb46acb0a36ffe8dcae006fd45dc475bed3",
    bytes: 13_131,
    record_count: 9,
  },
  {
    path: "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/scoped-association-hypothesis-ledger-shard-2-v1.tsv",
    sha256: "5b7e04bde8fc0c91f7d141f0ecdccf23579394dafba21e33e91ad512f9ab5a4d",
    bytes: 4_544,
    record_count: 2,
  },
];

let validatedRegistry: OpenInquiryRegistry | undefined;

function integrityFailure(label: string): never {
  throw new Error(`REGISTRY_INTEGRITY_FAILURE:${label}`);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function requireRecord(value: unknown, label: string): Record<string, unknown> {
  if (!isRecord(value)) return integrityFailure(label);
  return value;
}

function compareCodePoints(left: string, right: string): number {
  const leftPoints = Array.from(left, (character) => character.codePointAt(0) ?? 0);
  const rightPoints = Array.from(right, (character) => character.codePointAt(0) ?? 0);
  const length = Math.min(leftPoints.length, rightPoints.length);
  for (let index = 0; index < length; index += 1) {
    if (leftPoints[index] !== rightPoints[index]) return leftPoints[index] - rightPoints[index];
  }
  return leftPoints.length - rightPoints.length;
}

function requireExactKeys(value: object, expected: readonly string[], label: string): void {
  const actual = Object.keys(value).sort(compareCodePoints);
  const wanted = [...expected].sort(compareCodePoints);
  if (actual.length !== wanted.length || actual.some((key, index) => key !== wanted[index])) {
    integrityFailure(`${label}.keys`);
  }
}

function requireString(value: unknown, label: string): string {
  if (typeof value !== "string" || value.length === 0) return integrityFailure(label);
  return value;
}

function requireNullableString(value: unknown, label: string): string | null {
  if (value === null) return null;
  return requireString(value, label);
}

function requireSha256(value: unknown, label: string): string {
  const hash = requireString(value, label);
  if (!SHA256_PATTERN.test(hash)) return integrityFailure(label);
  return hash;
}

function requirePositiveInteger(value: unknown, label: string): number {
  if (!Number.isInteger(value) || (value as number) < 1) return integrityFailure(label);
  return value as number;
}

function requireStringArray(value: unknown, label: string): readonly string[] {
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string" || item.length === 0)) {
    return integrityFailure(label);
  }
  return value as string[];
}

function requireNullableStringArray(value: unknown, label: string): readonly string[] | null {
  if (value === null) return null;
  return requireStringArray(value, label);
}

function requireUnique(values: readonly string[], label: string): void {
  if (new Set(values).size !== values.length) integrityFailure(label);
}

function rejectProbabilityFields(value: unknown, label: string): void {
  if (Array.isArray(value)) {
    value.forEach((item, index) => rejectProbabilityFields(item, `${label}[${index}]`));
    return;
  }
  if (!isRecord(value)) return;
  for (const [key, child] of Object.entries(value)) {
    if (DISALLOWED_PROBABILITY_FIELDS.has(key)) integrityFailure(`${label}.${key}`);
    rejectProbabilityFields(child, `${label}.${key}`);
  }
}

function canonicalValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (!isRecord(value)) return value;
  return Object.fromEntries(
    Object.keys(value)
      .sort(compareCodePoints)
      .map((key) => [key, canonicalValue(value[key])]),
  );
}

function sha256Canonical(value: unknown): string {
  return createHash("sha256").update(JSON.stringify(canonicalValue(value)), "utf8").digest("hex");
}

function deepFreeze<T>(root: T): T {
  if (root === null || typeof root !== "object") return root;
  const pending: object[] = [root];
  const visited = new WeakSet<object>();
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

function validateInputBindings(value: unknown): void {
  if (!Array.isArray(value) || value.length !== EXPECTED_INPUT_BINDINGS.length) {
    integrityFailure("input_bindings");
  }
  value.forEach((candidate, index) => {
    const binding = requireRecord(candidate, `input_bindings[${index}]`);
    requireExactKeys(binding, ["bytes", "path", "record_count", "sha256"], `input_bindings[${index}]`);
    const expected = EXPECTED_INPUT_BINDINGS[index];
    if (
      binding.path !== expected?.path
      || binding.sha256 !== expected.sha256
      || binding.bytes !== expected.bytes
      || binding.record_count !== expected.record_count
    ) integrityFailure(`input_bindings[${index}].values`);
  });
}

function validateParticipants(value: unknown, arity: OpenInquiryArity, label: string): void {
  if (!Array.isArray(value) || value.length !== arity) integrityFailure(label);
  const senseIds: string[] = [];
  value.forEach((candidate, index) => {
    const participant = requireRecord(candidate, `${label}[${index}]`);
    requireExactKeys(participant, ["label", "sense_id"], `${label}[${index}]`);
    requireString(participant.label, `${label}[${index}].label`);
    senseIds.push(requireString(participant.sense_id, `${label}[${index}].sense_id`));
  });
  requireUnique(senseIds, `${label}.sense_ids`);
}

function validateAssociationIdentity(value: unknown, label: string): void {
  if (value === null) return;
  const identity = requireRecord(value, label);
  requireExactKeys(
    identity,
    ["association_id", "association_revision_id", "authority_path", "authority_queue_ref"],
    label,
  );
  requireString(identity.association_id, `${label}.association_id`);
  requireString(identity.association_revision_id, `${label}.association_revision_id`);
  requireNullableString(identity.authority_path, `${label}.authority_path`);
  requireNullableString(identity.authority_queue_ref, `${label}.authority_queue_ref`);
}

function validateEvidence(value: unknown, label: string): void {
  const evidence = requireRecord(value, label);
  requireExactKeys(evidence, [
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
  ], label);
  requireString(evidence.support_mode, `${label}.support_mode`);
  requireString(evidence.disposition, `${label}.disposition`);
  requireNullableString(evidence.exact_group_support_status, `${label}.exact_group_support_status`);
  requireNullableString(evidence.global_coherence_status, `${label}.global_coherence_status`);
  requireNullableString(evidence.sense_scope_status, `${label}.sense_scope_status`);
  requireNullableStringArray(evidence.locators, `${label}.locators`);
  requireNullableStringArray(evidence.synthesis_steps, `${label}.synthesis_steps`);
  requireNullableStringArray(evidence.counterevidence, `${label}.counterevidence`);
  requireNullableStringArray(evidence.qualifications, `${label}.qualifications`);
  requireStringArray(evidence.nonclaims, `${label}.nonclaims`);
}

function validateProvenance(value: unknown, label: string): void {
  const provenance = requireRecord(value, label);
  requireExactKeys(provenance, [
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
  ], label);
  requireString(provenance.authority_base_sha, `${label}.authority_base_sha`);
  requireString(provenance.shard_id, `${label}.shard_id`);
  requireString(provenance.source_ledger_path, `${label}.source_ledger_path`);
  requireSha256(provenance.source_ledger_sha256, `${label}.source_ledger_sha256`);
  requirePositiveInteger(provenance.source_row_number, `${label}.source_row_number`);
  requireSha256(provenance.source_record_sha256, `${label}.source_record_sha256`);
  requireStringArray(provenance.source_ids, `${label}.source_ids`);
  requireNullableStringArray(provenance.rights_record_ids, `${label}.rights_record_ids`);
  requireNullableString(provenance.linked_parent_candidate_id, `${label}.linked_parent_candidate_id`);
  requireNullableString(provenance.parent_disposition_preserved, `${label}.parent_disposition_preserved`);
  requireString(
    provenance.source_external_human_review_status,
    `${label}.source_external_human_review_status`,
  );
  requireString(provenance.source_activation_status, `${label}.source_activation_status`);
}

function validateOpenInquiryRecord(value: unknown, index: number): OpenInquiryRecord {
  const label = `records[${index}]`;
  const record = requireRecord(value, label);
  requireExactKeys(record, [
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
  ], label);

  const expected = EXPECTED_IDENTITIES[index];
  if (
    typeof record.inquiry_id !== "string"
    || !INQUIRY_ID_PATTERN.test(record.inquiry_id)
    || record.inquiry_id !== expected?.[0]
    || record.inquiry_key !== expected[1]
  ) integrityFailure(`${label}.identity`);
  if (record.record_version !== TRACE_OPEN_INQUIRY_API_VERSION) {
    integrityFailure(`${label}.record_version`);
  }
  if (![2, 3, 4, 5].includes(record.arity as number)) integrityFailure(`${label}.arity`);
  const arity = record.arity as OpenInquiryArity;
  validateParticipants(record.participants, arity, `${label}.participants`);
  requireString(record.bounded_scope, `${label}.bounded_scope`);
  requireString(record.relation_form, `${label}.relation_form`);
  if (
    record.epistemic_status !== "UNRESOLVED_OPEN_INQUIRY"
    || record.validated_relation !== false
    || record.counts_as_validated !== false
    || record.eligible_for_validated_graph !== false
    || record.eligible_for_validated_composition !== false
    || record.may_generate_pair_edges !== false
    || record.may_modify_validated_topology !== false
    || record.display_eligible !== true
    || record.display_layer !== TRACE_OPEN_INQUIRY_LAYER
    || record.default_in_validated_results !== false
    || record.active !== false
    || record.external_human_review_status !== "PENDING"
    || record.product_eligible !== false
    || record.product_path !== null
    || record.participant_order_meaningful !== false
    || record.relation_roles_asserted !== false
    || record.pair_projection_policy !== "NONE"
    || record.implicit_pair_projection_count !== 0
  ) integrityFailure(`${label}.boundary`);
  validateAssociationIdentity(record.inquiry_only_association_identity, `${label}.inquiry_only_association_identity`);
  validateEvidence(record.evidence, `${label}.evidence`);
  validateProvenance(record.provenance, `${label}.provenance`);
  const recordSha256 = requireSha256(record.record_sha256, `${label}.record_sha256`);
  const recordWithoutDigest = Object.fromEntries(
    Object.entries(record).filter(([key]) => key !== "record_sha256"),
  );
  if (sha256Canonical(recordWithoutDigest) !== recordSha256) {
    integrityFailure(`${label}.record_sha256.mismatch`);
  }
  return record as unknown as OpenInquiryRecord;
}

export function validateOpenInquiryRegistry(candidate: unknown): OpenInquiryRegistry {
  const registry = requireRecord(candidate, "registry");
  requireExactKeys(registry, [
    "api_version",
    "canonical_serialization",
    "closure_flags",
    "counts",
    "input_bindings",
    "records",
    "records_sha256",
    "registry_version",
  ], "registry");
  if (
    registry.api_version !== TRACE_OPEN_INQUIRY_API_VERSION
    || registry.registry_version !== TRACE_OPEN_INQUIRY_REGISTRY_VERSION
    || registry.canonical_serialization !== "UTF8_SORTED_KEYS_COMPACT_JSON_RECORD_DIGEST"
  ) integrityFailure("registry.identity");
  validateInputBindings(registry.input_bindings);

  const counts = requireRecord(registry.counts, "counts");
  requireExactKeys(counts, [
    "active_pending_review_count",
    "arity_2_count",
    "arity_3_count",
    "arity_4_count",
    "arity_5_count",
    "governed_inquiry_only_association_identity_count",
    "implicit_pair_projection_count",
    "scoped_higher_order_hypothesis_count",
    "ungoverned_hypothesis_count",
  ], "counts");
  if (
    counts.scoped_higher_order_hypothesis_count !== 11
    || counts.arity_2_count !== 3
    || counts.arity_3_count !== 6
    || counts.arity_4_count !== 1
    || counts.arity_5_count !== 1
    || counts.governed_inquiry_only_association_identity_count !== 4
    || counts.ungoverned_hypothesis_count !== 7
    || counts.active_pending_review_count !== 0
    || counts.implicit_pair_projection_count !== 0
  ) integrityFailure("counts.values");

  const closureFlags = requireRecord(registry.closure_flags, "closure_flags");
  requireExactKeys(closureFlags, [
    "COMPUTATIONAL_SPACE_CLOSURE",
    "FUNCTION3_CLOSURE",
    "GLOBAL_COMPOSITION_COHERENCE_CLOSURE",
    "HIGHER_ORDER_ASSOCIATION_CLOSURE",
    "PAIR_ASSOCIATION_CLOSURE",
    "PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE",
  ], "closure_flags");
  if (Object.values(closureFlags).some((value) => value !== false)) {
    integrityFailure("closure_flags.values");
  }

  if (!Array.isArray(registry.records) || registry.records.length !== EXPECTED_IDENTITIES.length) {
    integrityFailure("records");
  }
  rejectProbabilityFields(registry.records, "records");
  const records = registry.records.map(validateOpenInquiryRecord);
  requireUnique(records.map((record) => record.inquiry_id), "records.inquiry_id");
  requireUnique(records.map((record) => record.inquiry_key), "records.inquiry_key");

  const computedCounts = {
    2: records.filter((record) => record.arity === 2).length,
    3: records.filter((record) => record.arity === 3).length,
    4: records.filter((record) => record.arity === 4).length,
    5: records.filter((record) => record.arity === 5).length,
  };
  if (
    computedCounts[2] !== 3
    || computedCounts[3] !== 6
    || computedCounts[4] !== 1
    || computedCounts[5] !== 1
    || records.filter((record) => record.inquiry_only_association_identity !== null).length !== 4
    || records.filter((record) => record.inquiry_only_association_identity === null).length !== 7
    || records.filter((record) => record.active && record.external_human_review_status === "PENDING").length !== 0
    || records.reduce((sum, record) => sum + record.implicit_pair_projection_count, 0) !== 0
  ) integrityFailure("records.computed_counts");

  const recordsSha256 = requireSha256(registry.records_sha256, "records_sha256");
  if (sha256Canonical(records) !== recordsSha256) integrityFailure("records_sha256.mismatch");
  return deepFreeze(registry as unknown as OpenInquiryRegistry);
}

export function getOpenInquiryRegistry(): OpenInquiryRegistry {
  if (!validatedRegistry) validatedRegistry = validateOpenInquiryRegistry(registryJson as unknown);
  return validatedRegistry;
}

export function getOpenInquiryRegistryIdentity(): string {
  return getOpenInquiryRegistry().records_sha256;
}
