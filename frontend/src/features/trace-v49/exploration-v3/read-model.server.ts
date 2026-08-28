import "server-only";

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";
import {
  TRACE_EXPLORATION_V3_API_VERSION,
  TRACE_EXPLORATION_V3_MANIFEST_VERSION,
  TRACE_EXPLORATION_V3_READ_MODEL_VERSION,
} from "./types.ts";
import type {
  ExplorationV3AssociationDto,
  ExplorationV3ReadModel,
  ExplorationV3RuntimeReadModel,
  ExplorationV3Surface,
} from "./types.ts";

const SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c";
const SHA256_PATTERN = /^[0-9a-f]{64}$/u;
const EXPECTED_READ_MODEL_SHA256 = "f1ae8a35895b27c15fb3d9b42828b8611633ee8ee7e2cbc825772b590304351b";
const EXPECTED_MANIFEST_SHA256 = "2ee550028cb60749bee7efa456ed21ea4f0c6170bb5c68d8888017fc948fdd2c";
const EXPECTED_CHECKSUMS_SHA256 = "002d13c9175354054ee550b4d55d275ea2fad1c10693991bd726897aa50e8173";
const GENERATED_RELATIVE_DIRECTORY = path.join("generated", "trace-exploration-v3");
const SURFACE_KEYS = [
  "association_realizations",
  "associations",
  "composition_coherence_reviews",
  "compositions",
  "concept_senses",
  "concepts",
  "exports",
  "incidences",
  "navigation_states",
  "scopes",
  "transitions",
  "workflows",
] as const;
const COLLECTION_ROUTE_IDENTITIES = [
  ["association-realizations", "association_realization_id"],
  ["associations", "association_id"],
  ["composition-coherence-reviews", "composition_coherence_review_id"],
  ["compositions", "composition_id"],
  ["concept-senses", "sense_id"],
  ["concepts", "concept_id"],
  ["exports", "export_id"],
  ["incidences", "incidence_id"],
  ["navigation-states", "state_id"],
  ["scopes", "scope_id"],
  ["transitions", "transition_id"],
  ["workflows", "workflow_id"],
] as const;
const EXPECTED_READ_PATHS = [
  "/capabilities",
  ...COLLECTION_ROUTE_IDENTITIES.flatMap(([collection, identity]) => [
    `/${collection}`,
    `/${collection}/{${identity}}`,
  ]),
  ...COLLECTION_ROUTE_IDENTITIES.flatMap(([collection, identity]) => [
    `/controls/${collection}`,
    `/controls/${collection}/{${identity}}`,
  ]),
  "/baseline/reconciliation",
] as const;
const NAVIGATION_STATE_KEYS = [
  "bipartite_alternation_valid",
  "composition_revision_id",
  "fact_boundary",
  "focus_navigation_node_id",
  "nodes",
  "path",
  "presentation",
  "presentation_sha256",
  "realm",
  "semantic_sha256",
  "state_id",
] as const;
const FACT_BOUNDARY_KEYS = [
  "data_class",
  "production_fact",
  "synthetic_control",
] as const;
const NAVIGATION_NODE_KEYS = [
  "association_revision_id",
  "concept_id",
  "navigation_node_id",
  "node_kind",
] as const;
const NAVIGATION_PATH_STEP_KEYS = [
  "from_navigation_node_id",
  "incidence_id",
  "to_navigation_node_id",
] as const;
const WORKFLOW_KEYS = [
  "association_realization_ids",
  "association_revision_ids",
  "fact_boundary",
  "initial_state_id",
  "reachable",
  "realm",
  "semantic_sha256",
  "state_ids",
  "transition_ids",
  "transition_kind",
  "workflow_id",
] as const;
const EXPORT_KEYS = [
  "association_realization_ids",
  "association_revision_ids",
  "composition_revision_id",
  "export_id",
  "fact_boundary",
  "pair_projection_policy_preserved",
  "presentation",
  "presentation_sha256",
  "projection_preservation_records",
  "realm",
  "semantic_sha256",
  "state_id",
  "workflow_id",
] as const;
const PROJECTION_PRESERVATION_KEYS = [
  "association_realization_id",
  "association_revision_id",
  "pair_projection_policy",
  "realization_kind",
] as const;
const TRANSITION_KEYS = [
  "association_realization_id",
  "association_revision_id",
  "fact_boundary",
  "from_state_id",
  "incidence_id",
  "realm",
  "semantic_sha256",
  "state_mutated",
  "to_state_id",
  "transition_id",
  "transition_kind",
] as const;
let cachedRuntime: ExplorationV3RuntimeReadModel | undefined;

interface ExplorationV3Manifest {
  readonly api_version: string;
  readonly artifact_bytes: Readonly<Record<string, number>>;
  readonly artifact_sha256: Readonly<Record<string, string>>;
  readonly closure_flags: Readonly<Record<string, boolean>>;
  readonly manifest_version: string;
  readonly read_model_version: string;
  readonly source_sha: string;
}

const MANIFEST_KEYS = [
  "api_version",
  "artifact_bytes",
  "artifact_sha256",
  "canonical_serialization",
  "closure_flags",
  "counts",
  "deterministic_build_contract",
  "fact_boundary",
  "generator_version",
  "input_bindings",
  "manifest_version",
  "read_model_version",
  "source_sha",
] as const;
const INPUT_BINDING_PATHS = [
  "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/v3-semantic-contract-fixtures-v1.json",
  "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/v3-semantic-contract-census-v1.json",
  "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/v3-semantic-hash-binding-contract-v1.json",
  "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/round16a-global-reconciliation-census-v1.json",
] as const;

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function requireRecord(value: unknown, code: string): Record<string, unknown> {
  if (!isRecord(value)) throw new Error(`READ_MODEL_INVALID:${code}`);
  return value;
}

function requireArray(value: unknown, code: string): unknown[] {
  if (!Array.isArray(value)) throw new Error(`READ_MODEL_INVALID:${code}`);
  return value;
}

function requireStringArray(value: unknown, code: string): string[] {
  const values = requireArray(value, code);
  if (values.some((item) => typeof item !== "string" || item.length === 0)) {
    throw new Error(`READ_MODEL_INVALID:${code}`);
  }
  return values as string[];
}

function requireString(value: unknown, code: string): string {
  if (typeof value !== "string" || value.length === 0) {
    throw new Error(`READ_MODEL_INVALID:${code}`);
  }
  return value;
}

function requireHash(value: unknown, code: string): string {
  const text = requireString(value, code);
  if (!SHA256_PATTERN.test(text)) throw new Error(`READ_MODEL_INVALID:${code}`);
  return text;
}

function requireExactKeys(value: object, expected: readonly string[], code: string): void {
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  if (actual.length !== wanted.length || actual.some((key, index) => key !== wanted[index])) {
    throw new Error(`READ_MODEL_INVALID:${code}`);
  }
}

function requireUnique(values: readonly string[], code: string): void {
  if (new Set(values).size !== values.length) throw new Error(`READ_MODEL_INVALID:${code}`);
}

function loadGeneratedFile(filename: string): Buffer {
  const candidates = [
    path.join(process.cwd(), GENERATED_RELATIVE_DIRECTORY, filename),
    path.join(process.cwd(), "frontend", GENERATED_RELATIVE_DIRECTORY, filename),
  ];
  for (const candidate of candidates) {
    try {
      return readFileSync(candidate);
    } catch {
      // Support application-root and repository-root execution layouts.
    }
  }
  throw new Error(`READ_MODEL_UNAVAILABLE:${filename}`);
}

function parseJson(bytes: Buffer, code: string): unknown {
  try {
    return JSON.parse(bytes.toString("utf8")) as unknown;
  } catch {
    throw new Error(`READ_MODEL_INVALID:${code}`);
  }
}

function sha256(bytes: Buffer): string {
  return createHash("sha256").update(bytes).digest("hex");
}

function parseChecksumLedger(bytes: Buffer): ReadonlyMap<string, string> {
  let text: string;
  try {
    text = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch {
    throw new Error("READ_MODEL_INVALID:checksums_utf8");
  }
  if (!text.endsWith("\n")) throw new Error("READ_MODEL_INVALID:checksums_final_lf");
  const lines = text.slice(0, -1).split("\n");
  const expectedNames = ["manifest.json", "read-model.json"];
  if (lines.length !== expectedNames.length) throw new Error("READ_MODEL_INVALID:checksums_line_count");
  const parsed = new Map<string, string>();
  lines.forEach((line, index) => {
    const match = /^([0-9a-f]{64})  ([a-z0-9-]+\.json)$/u.exec(line);
    if (!match || match[2] !== expectedNames[index]) {
      throw new Error("READ_MODEL_INVALID:checksums_format_or_order");
    }
    parsed.set(match[2], match[1]);
  });
  return parsed;
}

function canonicalValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (isRecord(value)) {
    return Object.fromEntries(
      Object.entries(value).sort(([left], [right]) => compareText(left, right))
        .map(([key, child]) => [key, canonicalValue(child)]),
    );
  }
  return value;
}

function sameJson(left: unknown, right: unknown): boolean {
  return JSON.stringify(canonicalValue(left)) === JSON.stringify(canonicalValue(right));
}

function canonicalDigest(value: unknown): string {
  return createHash("sha256").update(JSON.stringify(canonicalValue(value)), "utf8").digest("hex");
}

function compareText(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0;
}

function validateControlProductIneligibility(value: unknown, pathLabel: string): void {
  if (Array.isArray(value)) {
    value.forEach((item, index) => validateControlProductIneligibility(item, `${pathLabel}[${index}]`));
    return;
  }
  if (!isRecord(value)) return;
  for (const [key, child] of Object.entries(value)) {
    if (key === "product_eligible" && child !== false) {
      throw new Error(`READ_MODEL_INVALID:control_product_eligible:${pathLabel}`);
    }
    if (key === "product_path" && child !== null) {
      throw new Error(`READ_MODEL_INVALID:control_product_path:${pathLabel}`);
    }
    if (key === "product_eligibility_disposition" && child !== "NOT_APPLICABLE_SYNTHETIC") {
      throw new Error(`READ_MODEL_INVALID:control_product_disposition:${pathLabel}`);
    }
    validateControlProductIneligibility(child, `${pathLabel}.${key}`);
  }
}

function validateFactBoundary(record: Record<string, unknown>, expected: "ACTIVE_PRODUCT_FACT" | "SYNTHETIC_CONTROL"): void {
  const boundary = requireRecord(record.fact_boundary, "fact_boundary");
  requireExactKeys(boundary, FACT_BOUNDARY_KEYS, "fact_boundary_keys");
  if (
    boundary.data_class !== expected
    || boundary.production_fact !== (expected === "ACTIVE_PRODUCT_FACT")
    || boundary.synthetic_control !== (expected === "SYNTHETIC_CONTROL")
  ) {
    throw new Error("READ_MODEL_INVALID:fact_boundary_values");
  }
}

function validateSurfaceShape(value: unknown, code: string): ExplorationV3Surface {
  const surface = requireRecord(value, code);
  requireExactKeys(surface, SURFACE_KEYS, `${code}.keys`);
  for (const key of SURFACE_KEYS) requireArray(surface[key], `${code}.${key}`);
  return surface as unknown as ExplorationV3Surface;
}

function validateVocabularyAndScopes(surface: ExplorationV3Surface, control: boolean): void {
  const expectedClass = control ? "SYNTHETIC_CONTROL" : "ACTIVE_PRODUCT_FACT";
  const scopeIds = surface.scopes.map((item) => item.scope_id);
  const conceptIds = surface.concepts.map((item) => item.concept_id);
  const senseIds = surface.concept_senses.map((item) => item.sense_id);
  requireUnique(scopeIds, "scope_ids");
  requireUnique(conceptIds, "concept_ids");
  requireUnique(senseIds, "sense_ids");
  const scopes = new Map(surface.scopes.map((item) => [item.scope_id, item]));
  const concepts = new Set(conceptIds);
  const senses = new Map(surface.concept_senses.map((item) => [item.sense_id, item]));
  for (const scope of surface.scopes) {
    validateFactBoundary(scope as unknown as Record<string, unknown>, expectedClass);
  }
  for (const concept of surface.concepts) {
    validateFactBoundary(concept as unknown as Record<string, unknown>, expectedClass);
    const conceptSemanticMaterial = {
      association_eligible: concept.association_eligible,
      authority: concept.authority,
      canonical_label: concept.canonical_label,
      lifecycle_state: concept.lifecycle_state,
      product_eligibility_disposition: concept.product_eligibility_disposition,
      product_eligible: concept.product_eligible,
      product_ineligibility_reason: concept.product_ineligibility_reason,
      product_path: concept.product_path,
      realm: concept.realm,
      semantic_version: concept.semantic_version,
    };
    if (
      !concept.concept_id.startsWith("concept:")
      || concept.semantic_sha256 !== canonicalDigest(conceptSemanticMaterial)
    ) throw new Error("READ_MODEL_INVALID:concept_semantic_hash");
  }
  for (const sense of surface.concept_senses) {
    validateFactBoundary(sense as unknown as Record<string, unknown>, expectedClass);
    const senseSemanticMaterial = {
      association_eligible: sense.association_eligible,
      authority: sense.authority,
      bounded_definition: sense.bounded_definition,
      concept_id: sense.concept_id,
      governed_scope_ids: sense.governed_scope_ids,
      lifecycle_state: sense.lifecycle_state,
      product_eligibility_disposition: sense.product_eligibility_disposition,
      product_eligible: sense.product_eligible,
      product_ineligibility_reason: sense.product_ineligibility_reason,
      product_path: sense.product_path,
      realm: sense.realm,
      semantic_version: sense.semantic_version,
      vocabulary_crosswalk_ids: sense.vocabulary_crosswalk_ids,
    };
    if (
      !sense.sense_id.startsWith("sense:")
      || sense.semantic_sha256 !== canonicalDigest(senseSemanticMaterial)
    ) throw new Error("READ_MODEL_INVALID:concept_sense_semantic_hash");
    if (
      !concepts.has(sense.concept_id)
      || sense.governed_scope_ids.length === 0
      || sense.governed_scope_ids.some((scopeId) => !scopes.has(scopeId))
    ) throw new Error("READ_MODEL_INVALID:concept_sense_reference");
  }
  for (const association of surface.associations) {
    const scope = scopes.get(association.scope.scope_id);
    if (!scope) throw new Error("READ_MODEL_INVALID:association_scope_reference");
    const projectedScope = {
      actors: scope.actors,
      context_qualifications: scope.context_qualifications,
      geographies: scope.geographies,
      historical_case_ids: scope.historical_case_ids,
      institutions: scope.institutions,
      mechanisms: scope.mechanisms,
      scope_id: scope.scope_id,
      time_bounds: scope.time_bounds,
    };
    if (!sameJson(projectedScope, association.scope)) {
      throw new Error("READ_MODEL_INVALID:association_scope_projection");
    }
    for (const participant of association.participants) {
      const sense = senses.get(participant.sense_id);
      if (
        !concepts.has(participant.concept_id)
        || !sense
        || sense.concept_id !== participant.concept_id
        || !scopes.has(participant.participant_scope_id)
        || participant.participant_scope_id !== association.scope.scope_id
        || !sense.governed_scope_ids.includes(participant.participant_scope_id)
      ) throw new Error("READ_MODEL_INVALID:participant_scope_divergence");
    }
  }
}

function validateAssociationCatalog(surface: ExplorationV3Surface, control: boolean): void {
  const associationIds = surface.associations.map((item) => item.association_id);
  const associationRevisionIds = surface.associations.map((item) => item.association_revision_id);
  const incidenceIds = surface.incidences.map((item) => item.incidence_id);
  requireUnique(associationIds, "association_ids");
  requireUnique(associationRevisionIds, "association_revision_ids");
  requireUnique(incidenceIds, "incidence_ids");
  const byId = new Map(surface.associations.map((item) => [item.association_id, item]));
  const byRevision = new Map(surface.associations.map((item) => [item.association_revision_id, item]));
  const explicitIncidenceIds = new Set(incidenceIds);
  const nestedByIncidenceId = new Map<string, ExplorationV3AssociationDto["participants"][number]>();
  for (const item of surface.associations) {
    validateFactBoundary(item as unknown as Record<string, unknown>, control ? "SYNTHETIC_CONTROL" : "ACTIVE_PRODUCT_FACT");
    if (item.arity !== item.participants.length) throw new Error("READ_MODEL_INVALID:association_arity");
    if (item.association_kind === "PAIR") {
      if (item.arity !== 2 || item.pair_projection_policy !== "NOT_APPLICABLE") {
        throw new Error("READ_MODEL_INVALID:pair_contract");
      }
    } else if (item.arity < 3 || item.pair_projection_policy !== "NONE") {
      throw new Error("READ_MODEL_INVALID:higher_order_projection");
    }
    const ordinals = item.participants.map((participant) => participant.ordinal);
    if (item.order_semantics === "ORDERED") {
      if (
        ordinals.some((ordinal) => !Number.isSafeInteger(ordinal) || Number(ordinal) < 0)
        || !ordinals.every((ordinal, index) => ordinal === index)
      ) throw new Error("READ_MODEL_INVALID:ordered_incidence_ordinals");
    } else if (ordinals.some((ordinal) => ordinal !== null)) {
      throw new Error("READ_MODEL_INVALID:unordered_incidence_ordinals");
    }
    if (
      item.roles_meaningful
        ? item.participants.some((participant) => typeof participant.role_id !== "string" || participant.role_id.length === 0)
        : item.participants.some((participant) => participant.role_id !== null)
    ) throw new Error("READ_MODEL_INVALID:participant_role_semantics");
    if (item.order_semantics === "UNORDERED") {
      const canonicalParticipants = [...item.participants].sort((left, right) => {
        const leftKey = item.roles_meaningful
          ? [left.role_id ?? "", left.sense_id, left.concept_id]
          : [left.sense_id, left.concept_id];
        const rightKey = item.roles_meaningful
          ? [right.role_id ?? "", right.sense_id, right.concept_id]
          : [right.sense_id, right.concept_id];
        for (let index = 0; index < leftKey.length; index += 1) {
          const compared = compareText(leftKey[index] ?? "", rightKey[index] ?? "");
          if (compared !== 0) return compared;
        }
        return 0;
      });
      if (!item.participants.every((participant, index) => participant === canonicalParticipants[index])) {
        throw new Error("READ_MODEL_INVALID:unordered_participant_order");
      }
    }
    const identityMaterial = {
      association_kind: item.association_kind,
      order_semantics: item.order_semantics,
      participants: item.participants.map((participant) => ({
        concept_id: participant.concept_id,
        ordinal: participant.ordinal,
        role_id: participant.role_id,
        sense_id: participant.sense_id,
      })),
      roles_meaningful: item.roles_meaningful,
      scope_identity: {
        actors: [...item.scope.actors].sort(compareText),
        geographies: [...item.scope.geographies].sort(compareText),
        historical_case_ids: [...item.scope.historical_case_ids].sort(compareText),
        institutions: [...item.scope.institutions].sort(compareText),
        mechanisms: [...item.scope.mechanisms].sort(compareText),
        scope_id: item.scope.scope_id,
        time_bounds: item.scope.time_bounds,
      },
    };
    const identitySha256 = canonicalDigest(identityMaterial);
    if (item.identity_material_sha256 !== identitySha256) {
      throw new Error("READ_MODEL_INVALID:association_identity_hash");
    }
    if (item.association_id !== `association:v3:${identitySha256.slice(0, 24)}`) {
      throw new Error("READ_MODEL_INVALID:association_id_hash");
    }
    const associationSemanticMaterial = {
      activation: item.activation,
      arity: item.arity,
      association_kind: item.association_kind,
      evidence: item.provenance,
      identity_material_sha256: item.identity_material_sha256,
      internal_pair_association_ids: item.internal_pair_association_ids,
      internal_pair_links: item.internal_pair_links,
      lifecycle_state: item.eligibility.lifecycle_state,
      order_semantics: item.order_semantics,
      pair_projection_policy: item.pair_projection_policy,
      participants: item.participants,
      product_eligibility_disposition: item.eligibility.product_eligibility_disposition,
      product_eligible: item.eligibility.product_eligible,
      product_ineligibility_reason: item.eligibility.product_ineligibility_reason,
      product_path: item.eligibility.product_path,
      realm: item.realm,
      review: item.review,
      roles_meaningful: item.roles_meaningful,
      scope: item.scope,
      semantic_version: item.semantic_version,
      uncertainty: item.uncertainty,
    };
    const associationSemanticSha256 = canonicalDigest(associationSemanticMaterial);
    if (item.semantic_sha256 !== associationSemanticSha256) {
      throw new Error("READ_MODEL_INVALID:association_semantic_hash");
    }
    if (
      item.association_revision_id
      !== `association-revision:v3:${canonicalDigest({
        association_id: item.association_id,
        ...associationSemanticMaterial,
      }).slice(0, 24)}`
    ) throw new Error("READ_MODEL_INVALID:association_revision_id_hash");
    const associationPresentation = requireRecord(item.presentation, "association.presentation");
    requireExactKeys(
      associationPresentation,
      ["realization_hint", "theme"],
      "association.presentation.keys",
    );
    if (item.presentation_sha256 !== canonicalDigest(associationPresentation)) {
      throw new Error("READ_MODEL_INVALID:association_presentation_hash");
    }
    for (const [participantIndex, participant] of item.participants.entries()) {
      const expectedIncidenceId = `incidence:${identitySha256.slice(0, 16)}:${String(
        participantIndex + 1,
      ).padStart(2, "0")}`;
      if (participant.incidence_id !== expectedIncidenceId) {
        throw new Error("READ_MODEL_INVALID:incidence_id_hash");
      }
      if (nestedByIncidenceId.has(participant.incidence_id)) {
        throw new Error("READ_MODEL_INVALID:nested_incidence_reuse");
      }
      nestedByIncidenceId.set(participant.incidence_id, participant);
    }
    requireUnique(item.internal_pair_association_ids, "internal_pair_association_ids");
    const linkedPairIds = item.internal_pair_links.map((link) => link.pair_association_id);
    requireUnique(linkedPairIds, "internal_pair_link_ids");
    if (
      item.internal_pair_links.length !== item.internal_pair_association_ids.length
      || item.internal_pair_links.some((link) => {
        const pair = byRevision.get(link.pair_association_revision_id);
        if (!pair
          || pair.association_kind !== "PAIR"
          || pair.association_id !== link.pair_association_id
          || !item.internal_pair_association_ids.includes(pair.association_id)
          || pair.eligibility.lifecycle_state !== "ACTIVE"
          || pair.review.review_state !== "FINAL"
          || pair.review.authority_state !== "FINAL"
          || pair.review.disposition !== "DIRECT_PAIRWISE_SUPPORT"
          || pair.review.global_coherence !== "PASS"
          || pair.review.unsupported_bridge_count !== 0
          || pair.provenance.support_mode !== "DIRECT_PAIR"
          || pair.provenance.evidence_complete !== true
          || pair.provenance.conflicts_resolved !== true
          || pair.activation.all_gates_pass !== true
          || pair.activation.decision !== "ALLOW"
        ) return true;
        const parentParticipants = link.participant_incidence_ids.map((id) =>
          item.participants.find((participant) => participant.incidence_id === id));
        const pairParticipants = link.pair_participant_incidence_ids.map((id) =>
          pair.participants.find((participant) => participant.incidence_id === id));
        return new Set(link.participant_incidence_ids).size !== 2
          || new Set(link.pair_participant_incidence_ids).size !== 2
          || parentParticipants.some((participant) => !participant)
          || pairParticipants.some((participant) => !participant)
          || !sameJson(
            [...link.endpoint_sense_ids].sort(),
            parentParticipants.map((participant) => participant?.sense_id).sort(),
          )
          || !sameJson(
            [...link.endpoint_sense_ids].sort(),
            pairParticipants.map((participant) => participant?.sense_id).sort(),
          )
          || !sameJson(
            [...link.pair_participant_incidence_ids].sort(),
            pair.participants.map((participant) => participant.incidence_id).sort(),
          );
      })
      || !sameJson([...item.internal_pair_association_ids].sort(), linkedPairIds.sort())
    ) throw new Error("READ_MODEL_INVALID:internal_pair_links");
  }
  if (
    nestedByIncidenceId.size !== explicitIncidenceIds.size
    || [...nestedByIncidenceId].some(([id]) => !explicitIncidenceIds.has(id))
  ) throw new Error("READ_MODEL_INVALID:incidence_projection");
  for (const incidence of surface.incidences) {
    validateFactBoundary(incidence as unknown as Record<string, unknown>, control ? "SYNTHETIC_CONTROL" : "ACTIVE_PRODUCT_FACT");
    const association = byId.get(incidence.association_id);
    const nested = nestedByIncidenceId.get(incidence.incidence_id);
    if (
      !association
      || !nested
      || association.association_revision_id !== incidence.association_revision_id
      || association.association_kind !== incidence.association_kind
      || nested.concept_id !== incidence.concept_id
      || nested.sense_id !== incidence.sense_id
      || nested.participant_scope_id !== incidence.participant_scope_id
      || nested.ordinal !== incidence.ordinal
      || nested.role_id !== incidence.role_id
      || !sameJson(nested.qualifications, incidence.qualifications)
    ) throw new Error("READ_MODEL_INVALID:incidence_owner");
  }
}

function validateCompositionCatalog(surface: ExplorationV3Surface, control: boolean): void {
  const expectedClass = control ? "SYNTHETIC_CONTROL" : "ACTIVE_PRODUCT_FACT";
  const associations = new Map(surface.associations.map((item) => [item.association_revision_id, item]));
  const conceptIds = new Set(surface.concepts.map((item) => item.concept_id));
  const incidenceById = new Map(surface.incidences.map((item) => [item.incidence_id, item]));
  const realizationIds = surface.association_realizations.map((item) => item.association_realization_id);
  const realizationById = new Map(surface.association_realizations.map((item) => [item.association_realization_id, item]));
  const reviewIds = surface.composition_coherence_reviews.map((item) => item.composition_coherence_review_id);
  const reviewById = new Map(surface.composition_coherence_reviews.map((item) => [item.composition_coherence_review_id, item]));
  const compositionByRevision = new Map(
    surface.compositions.map((item) => [item.composition_revision_id, item]),
  );
  requireUnique(realizationIds, "realization_ids");
  requireUnique(reviewIds, "coherence_review_ids");
  for (const realization of surface.association_realizations) {
    validateFactBoundary(realization as unknown as Record<string, unknown>, expectedClass);
    const association = associations.get(realization.association_revision_id);
    if (!association || association.association_id !== realization.association_id) {
      throw new Error("READ_MODEL_INVALID:realization_association");
    }
    const realizationSemanticMaterial = {
      association_revision_id: realization.association_revision_id,
      incidence_ids: realization.realized_incidence_ids,
      realization_kind: realization.realization_kind,
    };
    const realizationSemanticSha256 = canonicalDigest(realizationSemanticMaterial);
    const realizationPresentation = requireRecord(
      realization.presentation,
      "realization.presentation",
    );
    requireExactKeys(
      realizationPresentation,
      ["layout", "style"],
      "realization.presentation.keys",
    );
    if (association.association_kind === "PAIR") {
      if (
        realization.realization_kind !== "PAIR_EDGE"
        || realization.realized_incidence_ids.length !== 2
        || !sameJson(
          [...realization.realized_incidence_ids].sort(),
          association.participants.map((participant) => participant.incidence_id).sort(),
        )
      ) throw new Error("READ_MODEL_INVALID:pair_realization");
    } else if (
        realization.realization_kind === "PAIR_EDGE"
        || realization.realized_incidence_ids.length !== association.participants.length
        || association.participants.some((participant) => !realization.realized_incidence_ids.includes(participant.incidence_id))
    ) throw new Error("READ_MODEL_INVALID:higher_order_realization");
    if (realization.semantic_sha256 !== realizationSemanticSha256) {
      throw new Error("READ_MODEL_INVALID:realization_semantic_hash");
    }
    if (
      realization.association_realization_id
      !== `realization:v3:${realizationSemanticSha256.slice(0, 24)}`
    ) throw new Error("READ_MODEL_INVALID:realization_id_hash");
    if (realization.presentation_sha256 !== canonicalDigest(realizationPresentation)) {
      throw new Error("READ_MODEL_INVALID:realization_presentation_hash");
    }
  }
  for (const review of surface.composition_coherence_reviews) {
    validateFactBoundary(review as unknown as Record<string, unknown>, expectedClass);
    const reviewSemanticMaterial = {
      association_realization_ids: review.association_realization_ids,
      association_revision_ids: review.association_revision_ids,
      authority: review.authority,
      bounded_senses_compatible: review.bounded_senses_compatible,
      case_scope_compatible: review.case_scope_compatible,
      composition_id: review.composition_id,
      decision: review.decision,
      global_coherence: review.global_coherence,
      incidence_ids: review.incidence_ids,
      realm: review.realm,
      reasons: review.reasons,
      review_state: review.review_state,
      review_version: review.review_version,
      roles_and_topology_supported: review.roles_and_topology_supported,
      same_configuration: review.same_configuration,
      unsupported_bridge_count: review.unsupported_bridge_count,
    };
    const reviewSemanticSha256 = canonicalDigest(reviewSemanticMaterial);
    if (review.semantic_sha256 !== reviewSemanticSha256) {
      throw new Error("READ_MODEL_INVALID:composition_review_semantic_hash");
    }
    if (
      review.composition_coherence_review_id
      !== `composition-review:v3:${reviewSemanticSha256.slice(0, 24)}`
    ) throw new Error("READ_MODEL_INVALID:composition_review_id_hash");
  }
  for (const composition of surface.compositions) {
    validateFactBoundary(composition as unknown as Record<string, unknown>, expectedClass);
    const review = reviewById.get(composition.global_coherence_review_id);
    if (
      !review
      || review.composition_id !== composition.composition_id
      || !sameJson(review, composition.coherence_review)
    ) {
      throw new Error("READ_MODEL_INVALID:composition_review");
    }
    const sourceRealizations = composition.association_realizations.map((realization) => ({
      association_realization_id: realization.association_realization_id,
      association_revision_id: realization.association_revision_id,
      presentation: realization.presentation,
      presentation_sha256: realization.presentation_sha256,
      realization_kind: realization.realization_kind,
      realized_incidence_ids: realization.realized_incidence_ids,
      semantic_sha256: realization.semantic_sha256,
    }));
    const compositionSemanticMaterial = {
      association_realizations: sourceRealizations,
      association_trace_complete: composition.association_trace_complete,
      composition_node_ids: composition.composition_node_ids,
      global_coherence_review_id: composition.global_coherence_review_id,
      product_eligibility_disposition: composition.eligibility.product_eligibility_disposition,
      product_eligible: composition.eligibility.product_eligible,
      product_ineligibility_reason: composition.eligibility.product_ineligibility_reason,
      product_path: composition.eligibility.product_path,
      realm: composition.realm,
      renderability: composition.renderability,
      topology_family: composition.topology_family,
    };
    const compositionSemanticSha256 = canonicalDigest(compositionSemanticMaterial);
    if (composition.semantic_sha256 !== compositionSemanticSha256) {
      throw new Error("READ_MODEL_INVALID:composition_semantic_hash");
    }
    const compositionIdentityMaterial = {
      association_realization_ids: sourceRealizations.map(
        (realization) => realization.association_realization_id,
      ),
      node_ids: composition.composition_node_ids,
      topology_family: composition.topology_family,
    };
    if (
      composition.composition_id
      !== `composition:v3:${canonicalDigest(compositionIdentityMaterial).slice(0, 24)}`
    ) throw new Error("READ_MODEL_INVALID:composition_id_hash");
    if (
      composition.composition_revision_id
      !== `composition-revision:v3:${canonicalDigest({
        revision: 1,
        semantic: compositionSemanticMaterial,
      }).slice(0, 24)}`
    ) throw new Error("READ_MODEL_INVALID:composition_revision_id_hash");
    const compositionPresentation = requireRecord(
      composition.presentation,
      "composition.presentation",
    );
    requireExactKeys(compositionPresentation, ["layout", "seed"], "composition.presentation.keys");
    if (composition.presentation_sha256 !== canonicalDigest(compositionPresentation)) {
      throw new Error("READ_MODEL_INVALID:composition_presentation_hash");
    }
    const embeddedRealizationIds = composition.association_realizations
      .map((item) => item.association_realization_id).sort();
    const embeddedAssociationRevisionIds = [...new Set(composition.association_realizations
      .map((item) => item.association_revision_id))].sort();
    const embeddedIncidenceIds = [...new Set(composition.association_realizations
      .flatMap((item) => item.realized_incidence_ids))].sort();
    const explicitForComposition = surface.association_realizations
      .filter((item) => item.composition_revision_id === composition.composition_revision_id)
      .map((item) => item.association_realization_id).sort();
    if (
      !sameJson(embeddedRealizationIds, explicitForComposition)
      || !sameJson([...review.association_realization_ids].sort(), embeddedRealizationIds)
      || !sameJson([...review.association_revision_ids].sort(), embeddedAssociationRevisionIds)
      || !sameJson([...review.incidence_ids].sort(), embeddedIncidenceIds)
    ) throw new Error("READ_MODEL_INVALID:composition_trace_exact_set");
    for (const embedded of composition.association_realizations) {
      const explicit = realizationById.get(embedded.association_realization_id);
      if (
        !explicit
        || explicit.composition_revision_id !== composition.composition_revision_id
        || explicit.association_revision_id !== embedded.association_revision_id
        || explicit.association_id !== embedded.association_id
        || explicit.association_kind !== embedded.association_kind
        || explicit.realization_kind !== embedded.realization_kind
        || !sameJson(explicit.realized_incidence_ids, embedded.realized_incidence_ids)
        || explicit.semantic_sha256 !== embedded.semantic_sha256
        || explicit.presentation_sha256 !== embedded.presentation_sha256
      ) throw new Error("READ_MODEL_INVALID:composition_realization_projection");
    }
  }
  const expectedRealm = control ? "SYNTHETIC_CONTROL" : "PRODUCTION";
  const stateIds = surface.navigation_states.map((item) => item.state_id);
  requireUnique(stateIds, "state_ids");
  const stateById = new Map(surface.navigation_states.map((item) => [item.state_id, item]));
  for (const state of surface.navigation_states) {
    const stateRecord = state as unknown as Record<string, unknown>;
    requireExactKeys(state, NAVIGATION_STATE_KEYS, "state.keys");
    validateFactBoundary(stateRecord, expectedClass);
    const stateId = requireString(state.state_id, "state.state_id");
    requireHash(state.semantic_sha256, "state.semantic_sha256");
    requireHash(state.presentation_sha256, "state.presentation_sha256");
    const presentation = requireRecord(state.presentation, "state.presentation");
    requireExactKeys(presentation, ["focus_style", "viewport"], "state.presentation.keys");
    requireString(presentation.focus_style, "state.presentation.focus_style");
    requireString(presentation.viewport, "state.presentation.viewport");
    const stateSemanticMaterial = {
      bipartite_alternation_valid: state.bipartite_alternation_valid,
      composition_revision_id: state.composition_revision_id,
      focus_navigation_node_id: state.focus_navigation_node_id,
      nodes: state.nodes,
      path: state.path,
      realm: state.realm,
    };
    const expectedStateSemanticSha256 = canonicalDigest(stateSemanticMaterial);
    const compositionRevisionId = requireString(
      state.composition_revision_id,
      "state.composition_revision_id",
    );
    const composition = compositionByRevision.get(compositionRevisionId);
    if (!composition) throw new Error("READ_MODEL_INVALID:state_composition");
    if (state.realm !== expectedRealm || composition.realm !== state.realm) {
      throw new Error("READ_MODEL_INVALID:state_composition_realm");
    }
    if (state.bipartite_alternation_valid !== true) {
      throw new Error("READ_MODEL_INVALID:state_bipartite_flag");
    }
    const nodes = requireArray(state.nodes, "state.nodes")
      .map((value) => requireRecord(value, "state.node"));
    if (nodes.length < 3) throw new Error("READ_MODEL_INVALID:state_node_count");
    const navigationNodeIds = nodes.map((node) => {
      requireExactKeys(node, NAVIGATION_NODE_KEYS, "state.node.keys");
      return requireString(node.navigation_node_id, "state.navigation_node_id");
    });
    requireUnique(navigationNodeIds, "state.navigation_node_ids");
    const nodeById = new Map(nodes.map((node, index) => [navigationNodeIds[index], node]));
    const focusNodeId = requireString(
      state.focus_navigation_node_id,
      "state.focus_navigation_node_id",
    );
    if (!nodeById.has(focusNodeId)) throw new Error("READ_MODEL_INVALID:state_focus_node");
    const compositionConceptIds = new Set(composition.composition_node_ids);
    const compositionAssociationRevisionIds = new Set(
      composition.association_realizations.map((item) => item.association_revision_id),
    );
    for (const node of nodes) {
      if (node.node_kind === "CONCEPT") {
        const conceptId = requireString(node.concept_id, "state.concept_id");
        if (node.association_revision_id !== null || !conceptIds.has(conceptId)) {
          throw new Error("READ_MODEL_INVALID:state_concept_node");
        }
        if (!compositionConceptIds.has(conceptId)) {
          throw new Error("READ_MODEL_INVALID:state_node_outside_composition");
        }
      } else if (node.node_kind === "ASSOCIATION") {
        const associationRevisionId = requireString(
          node.association_revision_id,
          "state.association_revision_id",
        );
        if (node.concept_id !== null || !associations.has(associationRevisionId)) {
          throw new Error("READ_MODEL_INVALID:state_association_node");
        }
        if (!compositionAssociationRevisionIds.has(associationRevisionId)) {
          throw new Error("READ_MODEL_INVALID:state_node_outside_composition");
        }
      } else {
        throw new Error("READ_MODEL_INVALID:state_node_kind");
      }
    }
    const steps = requireArray(state.path, "state.path")
      .map((value) => requireRecord(value, "state.path_step"));
    if (steps.length === 0) throw new Error("READ_MODEL_INVALID:state_path_empty");
    for (let index = 0; index < steps.length; index += 1) {
      const step = steps[index];
      requireExactKeys(step, NAVIGATION_PATH_STEP_KEYS, "state.path_step.keys");
      const fromId = requireString(step.from_navigation_node_id, "state.path.from");
      const toId = requireString(step.to_navigation_node_id, "state.path.to");
      const incidenceId = requireString(step.incidence_id, "state.path.incidence_id");
      const from = nodeById.get(fromId);
      const to = nodeById.get(toId);
      const incidence = incidenceById.get(incidenceId);
      if (!from || !to || !incidence || from.node_kind === to.node_kind) {
        throw new Error("READ_MODEL_INVALID:state_path_reference");
      }
      if (
        index > 0
        && steps[index - 1].to_navigation_node_id !== step.from_navigation_node_id
      ) throw new Error("READ_MODEL_INVALID:state_path_discontinuous");
      const associationNode = from.node_kind === "ASSOCIATION" ? from : to;
      const conceptNode = from.node_kind === "CONCEPT" ? from : to;
      const realizationOwnsIncidence = composition.association_realizations.some(
        (realization) => realization.association_revision_id === incidence.association_revision_id
          && realization.realized_incidence_ids.includes(incidence.incidence_id),
      );
      if (
        associationNode.association_revision_id !== incidence.association_revision_id
        || conceptNode.concept_id !== incidence.concept_id
        || !realizationOwnsIncidence
      ) throw new Error("READ_MODEL_INVALID:state_path_incidence_ownership");
    }
    if (steps[steps.length - 1].to_navigation_node_id !== focusNodeId) {
      throw new Error("READ_MODEL_INVALID:state_terminal_focus");
    }
    if (state.semantic_sha256 !== expectedStateSemanticSha256) {
      throw new Error("READ_MODEL_INVALID:state_semantic_hash");
    }
    if (stateId !== `state:v3:${expectedStateSemanticSha256.slice(0, 24)}`) {
      throw new Error("READ_MODEL_INVALID:state_id_hash");
    }
    if (state.presentation_sha256 !== canonicalDigest(presentation)) {
      throw new Error("READ_MODEL_INVALID:state_presentation_hash");
    }
  }

  const transitionIds = surface.transitions.map((item) => item.transition_id);
  requireUnique(transitionIds, "transition_ids");
  for (const transition of surface.transitions) {
    const transitionRecord = transition as unknown as Record<string, unknown>;
    requireExactKeys(transition, TRANSITION_KEYS, "transition.keys");
    validateFactBoundary(transitionRecord, expectedClass);
    const transitionId = requireString(transition.transition_id, "transition.transition_id");
    requireHash(transition.semantic_sha256, "transition.semantic_sha256");
    const transitionSemanticMaterial = {
      association_realization_id: transition.association_realization_id,
      association_revision_id: transition.association_revision_id,
      from_state_id: transition.from_state_id,
      incidence_id: transition.incidence_id,
      realm: transition.realm,
      state_mutated: transition.state_mutated,
      to_state_id: transition.to_state_id,
      transition_kind: transition.transition_kind,
    };
    const transitionSemanticSha256 = canonicalDigest(transitionSemanticMaterial);
    const fromStateId = requireString(transition.from_state_id, "transition.from_state_id");
    const toStateId = requireString(transition.to_state_id, "transition.to_state_id");
    const fromState = stateById.get(fromStateId);
    const toState = stateById.get(toStateId);
    if (!fromState || !toState) throw new Error("READ_MODEL_INVALID:transition_endpoint");
    if (
      transition.realm !== expectedRealm
      || fromState.realm !== transition.realm
      || toState.realm !== transition.realm
    ) throw new Error("READ_MODEL_INVALID:transition_realm");
    if (!["FOLLOW_INCIDENCE", "MOVE_FOCUS", "EXPORT"].includes(transition.transition_kind)) {
      throw new Error("READ_MODEL_INVALID:transition_kind");
    }
    if (
      typeof transition.state_mutated !== "boolean"
      || transition.state_mutated !== (fromStateId !== toStateId)
    ) throw new Error("READ_MODEL_INVALID:transition_state_mutated");
    const trace = [
      transition.incidence_id,
      transition.association_revision_id,
      transition.association_realization_id,
    ];
    const traceIsNull = trace.every((value) => value === null);
    const traceIsComplete = trace.every(
      (value) => typeof value === "string" && value.length > 0,
    );
    if (
      (!traceIsNull && !traceIsComplete)
      || (transition.transition_kind === "FOLLOW_INCIDENCE" && !traceIsComplete)
    ) throw new Error("READ_MODEL_INVALID:transition_trace_partial");
    if (traceIsComplete) {
      const incidence = incidenceById.get(transition.incidence_id as string);
      const realization = realizationById.get(transition.association_realization_id as string);
      if (
        !incidence
        || !realization
        || incidence.association_revision_id !== transition.association_revision_id
        || realization.association_revision_id !== transition.association_revision_id
        || !realization.realized_incidence_ids.includes(transition.incidence_id as string)
        || fromState.composition_revision_id !== toState.composition_revision_id
        || realization.composition_revision_id !== fromState.composition_revision_id
      ) throw new Error("READ_MODEL_INVALID:transition_trace");
    }
    if (transition.semantic_sha256 !== transitionSemanticSha256) {
      throw new Error("READ_MODEL_INVALID:transition_semantic_hash");
    }
    if (transitionId !== `transition:v3:${transitionSemanticSha256.slice(0, 24)}`) {
      throw new Error("READ_MODEL_INVALID:transition_id_hash");
    }
  }

  const workflowIds = surface.workflows.map((item) => item.workflow_id);
  requireUnique(workflowIds, "workflow_ids");
  const workflowById = new Map(surface.workflows.map((item) => [item.workflow_id, item]));
  const transitionMembership = new Map(transitionIds.map((id) => [id, 0]));
  for (const workflow of surface.workflows) {
    const workflowRecord = workflow as unknown as Record<string, unknown>;
    requireExactKeys(workflow, WORKFLOW_KEYS, "workflow.keys");
    validateFactBoundary(workflowRecord, expectedClass);
    const workflowId = requireString(workflow.workflow_id, "workflow.workflow_id");
    requireHash(workflow.semantic_sha256, "workflow.semantic_sha256");
    if (workflow.realm !== expectedRealm) {
      throw new Error("READ_MODEL_INVALID:workflow_state_realm");
    }
    if (!["FOLLOW_INCIDENCE", "MOVE_FOCUS", "EXPORT"].includes(workflow.transition_kind)) {
      throw new Error("READ_MODEL_INVALID:workflow_transition_kind");
    }
    const workflowStateIds = requireStringArray(workflow.state_ids, "workflow.state_ids");
    requireUnique(workflowStateIds, "workflow.state_ids");
    const workflowTransitionIds = requireStringArray(
      workflow.transition_ids,
      "workflow.transition_ids",
    );
    requireUnique(workflowTransitionIds, "workflow.transition_ids");
    const workflowStates = workflowStateIds.map((stateId) => stateById.get(stateId));
    if (workflowStates.some((state) => !state)) {
      throw new Error("READ_MODEL_INVALID:workflow_state");
    }
    if (workflowStates.some((state) => state?.realm !== workflow.realm)) {
      throw new Error("READ_MODEL_INVALID:workflow_state_realm");
    }
    const initialStateId = requireString(workflow.initial_state_id, "workflow.initial_state_id");
    if (!workflowStateIds.includes(initialStateId)) {
      throw new Error("READ_MODEL_INVALID:workflow_initial_state_membership");
    }
    const workflowRealizationIds = requireStringArray(
      workflow.association_realization_ids,
      "workflow.association_realization_ids",
    );
    const workflowAssociationRevisionIds = requireStringArray(
      workflow.association_revision_ids,
      "workflow.association_revision_ids",
    );
    requireUnique(workflowRealizationIds, "workflow.association_realization_ids");
    requireUnique(workflowAssociationRevisionIds, "workflow.association_revision_ids");
    const workflowSemanticMaterial = {
      association_realization_ids: workflow.association_realization_ids,
      association_revision_ids: workflow.association_revision_ids,
      initial_state_id: workflow.initial_state_id,
      reachable: workflow.reachable,
      realm: workflow.realm,
      state_ids: workflow.state_ids,
      transition_ids: workflow.transition_ids,
      transition_kind: workflow.transition_kind,
    };
    const expectedWorkflowSemanticSha256 = canonicalDigest(workflowSemanticMaterial);
    const expectedRealizationIds = [...new Set(
      workflowStates.flatMap((state) => {
        const composition = compositionByRevision.get(state?.composition_revision_id ?? "");
        return composition?.association_realizations.map(
          (realization) => realization.association_realization_id,
        ) ?? [];
      }),
    )].sort(compareText);
    if (!sameJson([...workflowRealizationIds].sort(compareText), expectedRealizationIds)) {
      throw new Error("READ_MODEL_INVALID:workflow_realization_trace_exact_set");
    }
    const expectedAssociationRevisionIds = [...new Set(expectedRealizationIds.map(
      (realizationId) => realizationById.get(realizationId)?.association_revision_id,
    ))];
    if (
      expectedAssociationRevisionIds.some((value) => value === undefined)
      || !sameJson(
        [...workflowAssociationRevisionIds].sort(compareText),
        (expectedAssociationRevisionIds as string[]).sort(compareText),
      )
    ) throw new Error("READ_MODEL_INVALID:workflow_association_trace_exact_set");
    const workflowStateSet = new Set(workflowStateIds);
    const workflowTransitions = workflowTransitionIds.map((transitionId) => {
      const transition = surface.transitions.find((item) => item.transition_id === transitionId);
      if (!transition) throw new Error("READ_MODEL_INVALID:workflow_transition_reference");
      return transition;
    });
    for (const transition of workflowTransitions) {
      if (
        transition.realm !== workflow.realm
        || transition.transition_kind !== workflow.transition_kind
        || !workflowStateSet.has(transition.from_state_id)
        || !workflowStateSet.has(transition.to_state_id)
      ) throw new Error("READ_MODEL_INVALID:workflow_selected_transition_scope");
      transitionMembership.set(
        transition.transition_id,
        (transitionMembership.get(transition.transition_id) ?? 0) + 1,
      );
    }
    const reached = new Set([initialStateId]);
    const pending = [initialStateId];
    while (pending.length > 0) {
      const fromStateId = pending.pop();
      for (const transition of workflowTransitions) {
        if (
          transition.from_state_id === fromStateId
          && !reached.has(transition.to_state_id)
        ) {
          reached.add(transition.to_state_id);
          pending.push(transition.to_state_id);
        }
      }
    }
    const derivedReachable = workflowStateIds.every((stateId) => reached.has(stateId));
    if (typeof workflow.reachable !== "boolean" || workflow.reachable !== derivedReachable) {
      throw new Error("READ_MODEL_INVALID:workflow_reachability");
    }
    if (workflow.semantic_sha256 !== expectedWorkflowSemanticSha256) {
      throw new Error("READ_MODEL_INVALID:workflow_semantic_hash");
    }
    if (workflowId !== `workflow:v3:${expectedWorkflowSemanticSha256.slice(0, 24)}`) {
      throw new Error("READ_MODEL_INVALID:workflow_id_hash");
    }
  }
  if ([...transitionMembership.values()].some((memberships) => memberships === 0)) {
    throw new Error("READ_MODEL_INVALID:transition_unlisted_by_workflow");
  }

  const exportIds = surface.exports.map((item) => item.export_id);
  requireUnique(exportIds, "export_ids");
  for (const item of surface.exports) {
    const exportRecord = item as unknown as Record<string, unknown>;
    requireExactKeys(item, EXPORT_KEYS, "export.keys");
    validateFactBoundary(exportRecord, expectedClass);
    const exportId = requireString(item.export_id, "export.export_id");
    requireHash(item.semantic_sha256, "export.semantic_sha256");
    requireHash(item.presentation_sha256, "export.presentation_sha256");
    const presentation = requireRecord(item.presentation, "export.presentation");
    requireExactKeys(presentation, ["format", "theme"], "export.presentation.keys");
    requireString(presentation.format, "export.presentation.format");
    requireString(presentation.theme, "export.presentation.theme");
    const exportSemanticMaterial = {
      association_realization_ids: item.association_realization_ids,
      association_revision_ids: item.association_revision_ids,
      composition_revision_id: item.composition_revision_id,
      pair_projection_policy_preserved: item.pair_projection_policy_preserved,
      projection_preservation_records: item.projection_preservation_records,
      realm: item.realm,
      state_id: item.state_id,
      workflow_id: item.workflow_id,
    };
    const expectedExportSemanticSha256 = canonicalDigest(exportSemanticMaterial);
    const workflowId = requireString(item.workflow_id, "export.workflow_id");
    const stateId = requireString(item.state_id, "export.state_id");
    const compositionRevisionId = requireString(
      item.composition_revision_id,
      "export.composition_revision_id",
    );
    const workflow = workflowById.get(workflowId);
    const state = stateById.get(stateId);
    const composition = compositionByRevision.get(compositionRevisionId);
    if (!workflow || !state || !composition || item.pair_projection_policy_preserved !== true) {
      throw new Error("READ_MODEL_INVALID:export_trace");
    }
    if (
      item.realm !== expectedRealm
      || workflow.realm !== item.realm
      || state.realm !== item.realm
      || composition.realm !== item.realm
    ) throw new Error("READ_MODEL_INVALID:export_realm");
    if (
      !workflow.state_ids.includes(stateId)
      || state.composition_revision_id !== compositionRevisionId
    ) throw new Error("READ_MODEL_INVALID:export_workflow_projection");
    const expectedRealizationIds = [...new Set(
      composition.association_realizations.map(
        (realization) => realization.association_realization_id,
      ),
    )].sort(compareText);
    const expectedAssociationRevisionIds = [...new Set(
      composition.association_realizations.map(
        (realization) => realization.association_revision_id,
      ),
    )].sort(compareText);
    const exportRealizationIds = requireStringArray(
      item.association_realization_ids,
      "export.association_realization_ids",
    );
    const exportAssociationRevisionIds = requireStringArray(
      item.association_revision_ids,
      "export.association_revision_ids",
    );
    requireUnique(exportRealizationIds, "export.association_realization_ids");
    requireUnique(exportAssociationRevisionIds, "export.association_revision_ids");
    if (
      !sameJson([...exportRealizationIds].sort(compareText), expectedRealizationIds)
      || !sameJson(
        [...workflow.association_realization_ids].sort(compareText),
        expectedRealizationIds,
      )
    ) throw new Error("READ_MODEL_INVALID:export_realization_trace_exact_set");
    if (
      !sameJson(
        [...exportAssociationRevisionIds].sort(compareText),
        expectedAssociationRevisionIds,
      )
      || !sameJson(
        [...workflow.association_revision_ids].sort(compareText),
        expectedAssociationRevisionIds,
      )
    ) throw new Error("READ_MODEL_INVALID:export_association_trace_exact_set");
    const preservationRecords = requireArray(
      item.projection_preservation_records,
      "export.projection_preservation_records",
    ).map((value) => requireRecord(value, "export.projection_preservation_record"));
    const preservationRealizationIds = preservationRecords.map((record) => {
      requireExactKeys(
        record,
        PROJECTION_PRESERVATION_KEYS,
        "export.projection_preservation_record.keys",
      );
      return requireString(
        record.association_realization_id,
        "export.preservation.realization_id",
      );
    });
    requireUnique(preservationRealizationIds, "export.preservation.realization_ids");
    if (!sameJson([...preservationRealizationIds].sort(compareText), expectedRealizationIds)) {
      throw new Error("READ_MODEL_INVALID:export_projection_record_set");
    }
    for (const record of preservationRecords) {
      const realization = realizationById.get(record.association_realization_id as string);
      const association = associations.get(requireString(
        record.association_revision_id,
        "export.preservation.association_revision_id",
      ));
      if (
        !realization
        || !association
        || realization.association_revision_id !== association.association_revision_id
        || record.realization_kind !== realization.realization_kind
        || record.pair_projection_policy !== association.pair_projection_policy
      ) throw new Error("READ_MODEL_INVALID:export_projection_record");
    }
    if (item.semantic_sha256 !== expectedExportSemanticSha256) {
      throw new Error("READ_MODEL_INVALID:export_semantic_hash");
    }
    if (exportId !== `export:v3:${expectedExportSemanticSha256.slice(0, 24)}`) {
      throw new Error("READ_MODEL_INVALID:export_id_hash");
    }
    if (item.presentation_sha256 !== canonicalDigest(presentation)) {
      throw new Error("READ_MODEL_INVALID:export_presentation_hash");
    }
  }
  if (surface.transitions.length !== 0) {
    throw new Error("READ_MODEL_INVALID:transition_surface_disallowed");
  }
}

function countMatches(value: unknown, expected: number, code: string): void {
  if (!Number.isSafeInteger(value) || value !== expected) throw new Error(`READ_MODEL_INVALID:${code}`);
}

function validateCounts(model: ExplorationV3ReadModel): void {
  const active = model.active_product;
  const controls = model.research_controls;
  const capabilities = model.capabilities;
  const activeCounts: ReadonlyArray<readonly [unknown, number, string]> = [
    [capabilities.active_product_scope_count, active.scopes.length, "active_scope_count"],
    [capabilities.active_product_concept_count, active.concepts.length, "active_concept_count"],
    [capabilities.active_product_sense_count, active.concept_senses.length, "active_sense_count"],
    [capabilities.active_product_association_count, active.associations.length, "active_association_count"],
    [capabilities.active_product_incidence_count, active.incidences.length, "active_incidence_count"],
    [capabilities.active_product_realization_count, active.association_realizations.length, "active_realization_count"],
    [capabilities.active_product_coherence_review_count, active.composition_coherence_reviews.length, "active_review_count"],
    [capabilities.active_product_composition_count, active.compositions.length, "active_composition_count"],
    [capabilities.active_product_navigation_state_count, active.navigation_states.length, "active_state_count"],
    [capabilities.active_product_workflow_count, active.workflows.length, "active_workflow_count"],
    [capabilities.active_product_export_count, active.exports.length, "active_export_count"],
    [capabilities.active_product_transition_count, active.transitions.length, "active_transition_count"],
  ];
  const controlCounts: ReadonlyArray<readonly [unknown, number, string]> = [
    [capabilities.control_scope_count, controls.scopes.length, "control_scope_count"],
    [capabilities.control_concept_count, controls.concepts.length, "control_concept_count"],
    [capabilities.control_sense_count, controls.concept_senses.length, "control_sense_count"],
    [capabilities.control_association_count, controls.associations.length, "control_association_count"],
    [capabilities.control_incidence_count, controls.incidences.length, "control_incidence_count"],
    [capabilities.control_realization_count, controls.association_realizations.length, "control_realization_count"],
    [capabilities.control_coherence_review_count, controls.composition_coherence_reviews.length, "control_review_count"],
    [capabilities.control_composition_count, controls.compositions.length, "control_composition_count"],
    [capabilities.control_navigation_state_count, controls.navigation_states.length, "control_state_count"],
    [capabilities.control_workflow_count, controls.workflows.length, "control_workflow_count"],
    [capabilities.control_export_count, controls.exports.length, "control_export_count"],
    [capabilities.control_transition_count, controls.transitions.length, "control_transition_count"],
  ];
  for (const [actual, expected, code] of [...activeCounts, ...controlCounts]) countMatches(actual, expected, code);
}

function validateModel(value: unknown): ExplorationV3ReadModel {
  const model = requireRecord(value, "root");
  requireExactKeys(model, [
    "active_product",
    "api_version",
    "baseline_reconciliation",
    "capabilities",
    "closure_flags",
    "contract_version",
    "fact_boundary",
    "read_model_version",
    "research_controls",
    "source_authority",
  ], "root.keys");
  if (
    model.api_version !== TRACE_EXPLORATION_V3_API_VERSION
    || model.read_model_version !== TRACE_EXPLORATION_V3_READ_MODEL_VERSION
    || model.contract_version !== "trace-exploration-v3-semantic-contract-1.0.0"
  ) throw new Error("READ_MODEL_INVALID:version");
  const source = requireRecord(model.source_authority, "source_authority");
  if (
    source.authorized_round16a_source_sha !== SOURCE_SHA
    || source.semantic_contract_source_sha !== SOURCE_SHA
    || source.semantic_contract_namespace !== "trace/exploration/v3"
  ) throw new Error("READ_MODEL_INVALID:source_authority");
  const closure = requireRecord(model.closure_flags, "closure_flags");
  if (Object.keys(closure).length !== 6 || Object.values(closure).some((value) => value !== false)) {
    throw new Error("READ_MODEL_INVALID:closure_flags");
  }
  const boundary = requireRecord(model.fact_boundary, "fact_boundary");
  requireExactKeys(boundary, [
    "active_product_policy",
    "current_status",
    "inquiry_or_pending_records_are_active_facts",
    "synthetic_controls_are_active_facts",
  ], "root_fact_boundary_keys");
  if (
    boundary.current_status !== "FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS"
    || boundary.inquiry_or_pending_records_are_active_facts !== false
    || boundary.synthetic_controls_are_active_facts !== false
  ) throw new Error("READ_MODEL_INVALID:root_fact_boundary");
  const active = validateSurfaceShape(model.active_product, "active_product");
  const controls = validateSurfaceShape(model.research_controls, "research_controls");
  if (SURFACE_KEYS.some((key) => active[key].length !== 0)) {
    throw new Error("READ_MODEL_INVALID:unauthorized_active_product_record");
  }
  for (const key of SURFACE_KEYS) {
    for (const item of controls[key]) {
      const record = requireRecord(item, `controls.${key}`);
      validateFactBoundary(record, "SYNTHETIC_CONTROL");
      validateControlProductIneligibility(record, `controls.${key}`);
    }
  }
  const typed = model as unknown as ExplorationV3ReadModel;
  const derivedActivePendingReviewCount = typed.active_product.associations.filter(
    (association) => association.eligibility.lifecycle_state === "ACTIVE"
      && (
        association.review.review_state !== "FINAL"
        || association.review.authority_state !== "FINAL"
      ),
  ).length;
  const allAssociations = [
    ...typed.active_product.associations,
    ...typed.research_controls.associations,
  ];
  const allRealizations = [
    ...typed.active_product.association_realizations,
    ...typed.research_controls.association_realizations,
  ];
  const derivedImplicitHyperedgeProjectionCount = allAssociations.filter(
    (association) => association.association_kind === "HIGHER_ORDER"
      && (
        association.pair_projection_policy !== "NONE"
        || allRealizations.some(
          (realization) => realization.association_revision_id === association.association_revision_id
            && realization.realization_kind === "PAIR_EDGE",
        )
      ),
  ).length;
  if (
    typed.capabilities.governed_product_arity_bound !== null
    || typed.capabilities.backend_association_arity_support !== "PAIR_2_OR_HIGHER_ORDER_3_PLUS_NO_FIXED_SCHEMA_MAXIMUM"
    || typed.capabilities.association_and_composition_identity_separate !== true
    || typed.capabilities.production_activation_count !== 0
    || typed.capabilities.research_controls_only !== true
    || typed.capabilities.transition_derivation_policy !== "NONE_NO_V2_INHERITANCE"
    || typed.capabilities.transition_status !== "FAIL_CLOSED_NO_ACTIVE_PRODUCT_STATE_GRAPH"
    || typed.capabilities.transitions_available !== false
    || typed.capabilities.active_pending_review_count !== derivedActivePendingReviewCount
    || typed.capabilities.implicit_hyperedge_projection_count
      !== derivedImplicitHyperedgeProjectionCount
    || !sameJson(typed.capabilities.read_paths, EXPECTED_READ_PATHS)
  ) throw new Error("READ_MODEL_INVALID:capability_boundary");
  const allAssociationIds = [
    ...typed.active_product.associations,
    ...typed.research_controls.associations,
  ].map((item) => item.association_id);
  const allCompositionIds = [
    ...typed.active_product.compositions,
    ...typed.research_controls.compositions,
  ].map((item) => item.composition_id);
  requireUnique(allAssociationIds, "global_association_ids");
  requireUnique(allCompositionIds, "global_composition_ids");
  const associationIdSet = new Set(allAssociationIds);
  if (allCompositionIds.some((compositionId) => associationIdSet.has(compositionId))) {
    throw new Error("READ_MODEL_INVALID:association_composition_identity_collision");
  }
  validateVocabularyAndScopes(active, false);
  validateVocabularyAndScopes(controls, true);
  validateAssociationCatalog(active, false);
  validateAssociationCatalog(controls, true);
  validateCompositionCatalog(active, false);
  validateCompositionCatalog(controls, true);
  if (
    typed.capabilities.active_product_transition_count !== 0
    || typed.capabilities.control_transition_count !== 0
    || typed.active_product.transitions.length !== 0
    || typed.research_controls.transitions.length !== 0
  ) throw new Error("READ_MODEL_INVALID:transition_surface_disallowed");
  validateCounts(typed);
  return typed;
}

function deepFreeze<T>(value: T): T {
  if (value === null || typeof value !== "object") return value;
  const pending: object[] = [value];
  const seen = new WeakSet<object>();
  while (pending.length > 0) {
    const current = pending.pop();
    if (!current || seen.has(current)) continue;
    seen.add(current);
    for (const child of Object.values(current)) {
      if (child !== null && typeof child === "object") pending.push(child);
    }
    Object.freeze(current);
  }
  return value;
}

function validateManifest(value: unknown): ExplorationV3Manifest & Record<string, unknown> {
  const manifest = requireRecord(value, "manifest");
  requireExactKeys(manifest, MANIFEST_KEYS, "manifest.keys");
  if (
    manifest.manifest_version !== TRACE_EXPLORATION_V3_MANIFEST_VERSION
    || manifest.api_version !== TRACE_EXPLORATION_V3_API_VERSION
    || manifest.read_model_version !== TRACE_EXPLORATION_V3_READ_MODEL_VERSION
    || manifest.source_sha !== SOURCE_SHA
  ) throw new Error("READ_MODEL_INVALID:manifest_identity");
  const artifactBytes = requireRecord(manifest.artifact_bytes, "manifest.artifact_bytes");
  const artifactSha256 = requireRecord(manifest.artifact_sha256, "manifest.artifact_sha256");
  requireExactKeys(artifactBytes, ["read-model.json"], "manifest.artifact_bytes.keys");
  requireExactKeys(artifactSha256, ["read-model.json"], "manifest.artifact_sha256.keys");
  requireHash(artifactSha256["read-model.json"], "manifest_model_sha256");
  const inputBindings = requireArray(manifest.input_bindings, "manifest.input_bindings");
  if (inputBindings.length !== INPUT_BINDING_PATHS.length) {
    throw new Error("READ_MODEL_INVALID:manifest_input_binding_count");
  }
  inputBindings.forEach((value, index) => {
    const binding = requireRecord(value, `manifest.input_bindings[${index}]`);
    requireExactKeys(binding, ["path", "sha256"], `manifest.input_bindings[${index}].keys`);
    if (binding.path !== INPUT_BINDING_PATHS[index]) {
      throw new Error("READ_MODEL_INVALID:manifest_input_binding_path");
    }
    requireHash(binding.sha256, `manifest.input_bindings[${index}].sha256`);
  });
  return manifest as ExplorationV3Manifest & Record<string, unknown>;
}

export function validateExplorationV3GeneratedArtifactSet(
  checksumsBytes: Buffer,
  manifestBytes: Buffer,
  modelBytes: Buffer,
  trustMode: "FROZEN" | "REBOUND_TEST" = "FROZEN",
): ExplorationV3RuntimeReadModel {
  if (
    trustMode === "FROZEN"
    && (
      sha256(checksumsBytes) !== EXPECTED_CHECKSUMS_SHA256
      || sha256(manifestBytes) !== EXPECTED_MANIFEST_SHA256
      || sha256(modelBytes) !== EXPECTED_READ_MODEL_SHA256
    )
  ) throw new Error("READ_MODEL_INVALID:frozen_artifact_trust_anchor");
  const checksums = parseChecksumLedger(checksumsBytes);
  if (
    checksums.get("manifest.json") !== sha256(manifestBytes)
    || checksums.get("read-model.json") !== sha256(modelBytes)
  ) throw new Error("READ_MODEL_INVALID:checksums_artifact_mismatch");
  const manifest = validateManifest(parseJson(manifestBytes, "manifest_json"));
  const expectedSha256 = requireHash(manifest.artifact_sha256["read-model.json"], "manifest_model_sha256");
  const actualSha256 = sha256(modelBytes);
  if (
    actualSha256 !== expectedSha256
    || manifest.artifact_bytes["read-model.json"] !== modelBytes.byteLength
  ) throw new Error("READ_MODEL_INVALID:artifact_binding");
  const model = validateModel(parseJson(modelBytes, "read_model_json"));
  if (
    !sameJson(manifest.closure_flags, model.closure_flags)
    || !sameJson(manifest.counts, model.capabilities)
    || !sameJson(manifest.fact_boundary, model.fact_boundary)
  ) throw new Error("READ_MODEL_INVALID:manifest_model_contract_mismatch");
  return deepFreeze({ model, readModelSha256: actualSha256 });
}

export function getExplorationV3RuntimeReadModel(): ExplorationV3RuntimeReadModel {
  if (cachedRuntime) return cachedRuntime;
  const checksumsBytes = loadGeneratedFile("CHECKSUMS.sha256");
  const manifestBytes = loadGeneratedFile("manifest.json");
  const modelBytes = loadGeneratedFile("read-model.json");
  cachedRuntime = validateExplorationV3GeneratedArtifactSet(
    checksumsBytes,
    manifestBytes,
    modelBytes,
  );
  return cachedRuntime;
}

export function getExplorationV3ReadModel(): ExplorationV3ReadModel {
  return getExplorationV3RuntimeReadModel().model;
}

export function resetExplorationV3ReadModelForTests(): void {
  cachedRuntime = undefined;
}

export function findExplorationV3AssociationById(
  surface: ExplorationV3Surface,
  associationId: string,
): ExplorationV3AssociationDto | undefined {
  return surface.associations.find((item) => item.association_id === associationId);
}
