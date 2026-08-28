#!/usr/bin/env node

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptPath = fileURLToPath(import.meta.url);
const frontendRoot = resolve(dirname(scriptPath), "..");
const generatedRoot = resolve(frontendRoot, "generated/trace-exploration-v3");
const EXPECTED_READ_MODEL_SHA256 = "f1ae8a35895b27c15fb3d9b42828b8611633ee8ee7e2cbc825772b590304351b";
const EXPECTED_MANIFEST_SHA256 = "8346574defad9dcb16f49202f88d0aeb25c11440deb41fe5623f515f6c28e9a1";
const EXPECTED_CHECKSUMS_SHA256 = "45b0d047fa103ae3fb56b31909d8aa3bfa4f3fc586131891b60ab5bdfa70b243";
const jiti = createRequire(import.meta.url)("jiti")(import.meta.url, {
  interopDefault: true,
  alias: {
    "@": resolve(frontendRoot, "src"),
    "server-only": resolve(frontendRoot, "scripts/server-only-marker.mjs"),
  },
});

const COLLECTIONS = [
  "association-realizations",
  "associations",
  "composition-coherence-reviews",
  "compositions",
  "concept-senses",
  "concepts",
  "exports",
  "incidences",
  "navigation-states",
  "scopes",
  "transitions",
  "workflows",
];
const COLLECTION_IDENTITIES = {
  "association-realizations": ["association_realizations", "association_realization_id"],
  associations: ["associations", "association_id"],
  "composition-coherence-reviews": ["composition_coherence_reviews", "composition_coherence_review_id"],
  compositions: ["compositions", "composition_id"],
  "concept-senses": ["concept_senses", "sense_id"],
  concepts: ["concepts", "concept_id"],
  exports: ["exports", "export_id"],
  incidences: ["incidences", "incidence_id"],
  "navigation-states": ["navigation_states", "state_id"],
  scopes: ["scopes", "scope_id"],
  transitions: ["transitions", "transition_id"],
  workflows: ["workflows", "workflow_id"],
};
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
];
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

async function jsonResponse(response) {
  return JSON.parse(await response.text());
}

function canonicalValue(value) {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).sort(([left], [right]) => left.localeCompare(right))
      .map(([key, child]) => [key, canonicalValue(child)]));
  }
  return value;
}

function canonicalBytes(value) {
  return Buffer.from(`${JSON.stringify(canonicalValue(value))}\n`, "utf8");
}

function semanticDigest(value) {
  return sha256(Buffer.from(JSON.stringify(canonicalValue(value)), "utf8"));
}

function reboundArtifactSet(baseManifest, baseModel, mutate) {
  const changedModel = structuredClone(baseModel);
  mutate(changedModel);
  const changedModelBytes = canonicalBytes(changedModel);
  const changedManifest = structuredClone(baseManifest);
  changedManifest.artifact_bytes["read-model.json"] = changedModelBytes.byteLength;
  changedManifest.artifact_sha256["read-model.json"] = sha256(changedModelBytes);
  changedManifest.counts = changedModel.capabilities;
  changedManifest.closure_flags = changedModel.closure_flags;
  changedManifest.fact_boundary = changedModel.fact_boundary;
  const changedManifestBytes = canonicalBytes(changedManifest);
  const changedChecksumsBytes = Buffer.from(
    `${sha256(changedManifestBytes)}  manifest.json\n${sha256(changedModelBytes)}  read-model.json\n`,
    "utf8",
  );
  return [changedChecksumsBytes, changedManifestBytes, changedModelBytes, "REBOUND_TEST"];
}

function refreshStateBinding(state, { refreshId = true } = {}) {
  state.semantic_sha256 = semanticDigest({
    bipartite_alternation_valid: state.bipartite_alternation_valid,
    composition_revision_id: state.composition_revision_id,
    focus_navigation_node_id: state.focus_navigation_node_id,
    nodes: state.nodes,
    path: state.path,
    realm: state.realm,
  });
  if (refreshId) state.state_id = `state:v3:${state.semantic_sha256.slice(0, 24)}`;
  state.presentation_sha256 = semanticDigest(state.presentation);
  return state;
}

function refreshTransitionBinding(transition, { refreshId = true } = {}) {
  transition.semantic_sha256 = semanticDigest({
    association_realization_id: transition.association_realization_id,
    association_revision_id: transition.association_revision_id,
    from_state_id: transition.from_state_id,
    incidence_id: transition.incidence_id,
    realm: transition.realm,
    state_mutated: transition.state_mutated,
    to_state_id: transition.to_state_id,
    transition_kind: transition.transition_kind,
  });
  if (refreshId) transition.transition_id = `transition:v3:${transition.semantic_sha256.slice(0, 24)}`;
  return transition;
}

function refreshWorkflowBinding(workflow, { refreshId = true } = {}) {
  workflow.semantic_sha256 = semanticDigest({
    association_realization_ids: workflow.association_realization_ids,
    association_revision_ids: workflow.association_revision_ids,
    initial_state_id: workflow.initial_state_id,
    reachable: workflow.reachable,
    realm: workflow.realm,
    state_ids: workflow.state_ids,
    transition_ids: workflow.transition_ids,
    transition_kind: workflow.transition_kind,
  });
  if (refreshId) workflow.workflow_id = `workflow:v3:${workflow.semantic_sha256.slice(0, 24)}`;
  return workflow;
}

function refreshExportBinding(exported, { refreshId = true } = {}) {
  exported.semantic_sha256 = semanticDigest({
    association_realization_ids: exported.association_realization_ids,
    association_revision_ids: exported.association_revision_ids,
    composition_revision_id: exported.composition_revision_id,
    pair_projection_policy_preserved: exported.pair_projection_policy_preserved,
    projection_preservation_records: exported.projection_preservation_records,
    realm: exported.realm,
    state_id: exported.state_id,
    workflow_id: exported.workflow_id,
  });
  if (refreshId) exported.export_id = `export:v3:${exported.semantic_sha256.slice(0, 24)}`;
  exported.presentation_sha256 = semanticDigest(exported.presentation);
  return exported;
}

function refreshWorkflowAndDependentExports(changed, workflow) {
  const previousWorkflowId = workflow.workflow_id;
  refreshWorkflowBinding(workflow);
  for (const exported of changed.research_controls.exports) {
    if (exported.workflow_id === previousWorkflowId) {
      exported.workflow_id = workflow.workflow_id;
      refreshExportBinding(exported);
    }
  }
  return workflow;
}

function addClonedControlState(changed, stateId = "state:v3:corruption-probe-second-state") {
  const cloned = structuredClone(changed.research_controls.navigation_states[0]);
  cloned.nodes.reverse();
  cloned.path = [...cloned.path].reverse().map((step) => ({
    from_navigation_node_id: step.to_navigation_node_id,
    incidence_id: step.incidence_id,
    to_navigation_node_id: step.from_navigation_node_id,
  }));
  cloned.focus_navigation_node_id = cloned.path.at(-1).to_navigation_node_id;
  refreshStateBinding(cloned);
  if (stateId !== "state:v3:corruption-probe-second-state") cloned.state_id = stateId;
  changed.research_controls.navigation_states.push(cloned);
  changed.capabilities.control_navigation_state_count =
    changed.research_controls.navigation_states.length;
  return cloned;
}

function addValidControlTransition(changed, options = {}) {
  const fromState = changed.research_controls.navigation_states.find(
    (item) => item.state_id === (options.fromStateId
      ?? changed.research_controls.navigation_states[0].state_id),
  );
  const toState = changed.research_controls.navigation_states.find(
    (item) => item.state_id === (options.toStateId ?? fromState.state_id),
  );
  const incidence = changed.research_controls.incidences.find(
    (item) => item.incidence_id === fromState.path[0].incidence_id,
  );
  const realization = changed.research_controls.association_realizations.find(
    (item) => item.composition_revision_id === fromState.composition_revision_id
      && item.association_revision_id === incidence.association_revision_id
      && item.realized_incidence_ids.includes(incidence.incidence_id),
  );
  const transition = {
    association_realization_id: realization.association_realization_id,
    association_revision_id: incidence.association_revision_id,
    fact_boundary: {
      data_class: "SYNTHETIC_CONTROL",
      production_fact: false,
      synthetic_control: true,
    },
    from_state_id: fromState.state_id,
    incidence_id: incidence.incidence_id,
    realm: "SYNTHETIC_CONTROL",
    semantic_sha256: "",
    state_mutated: fromState.state_id !== toState.state_id,
    to_state_id: toState.state_id,
    transition_id: "",
    transition_kind: "FOLLOW_INCIDENCE",
  };
  refreshTransitionBinding(transition);
  if (options.transitionId) transition.transition_id = options.transitionId;
  changed.research_controls.transitions.push(transition);
  changed.capabilities.control_transition_count = changed.research_controls.transitions.length;
  return transition;
}

const checksumsBytes = await readFile(resolve(generatedRoot, "CHECKSUMS.sha256"));
const manifestBytes = await readFile(resolve(generatedRoot, "manifest.json"));
const modelBytes = await readFile(resolve(generatedRoot, "read-model.json"));
const manifest = JSON.parse(manifestBytes.toString("utf8"));
equal(sha256(modelBytes), EXPECTED_READ_MODEL_SHA256, "independent frozen read-model trust pin");
equal(sha256(manifestBytes), EXPECTED_MANIFEST_SHA256, "independent frozen manifest trust pin");
equal(sha256(checksumsBytes), EXPECTED_CHECKSUMS_SHA256, "independent frozen checksum-ledger trust pin");
equal(sha256(modelBytes), manifest.artifact_sha256["read-model.json"], "manifest binds model hash");
equal(modelBytes.byteLength, manifest.artifact_bytes["read-model.json"], "manifest binds model bytes");
equal(manifest.api_version, "trace-exploration/v3", "manifest API version");

const readModelModule = jiti(resolve(frontendRoot, "src/features/trace-v49/exploration-v3/read-model.server.ts"));
const service = jiti(resolve(frontendRoot, "src/features/trace-v49/exploration-v3/service.server.ts"));
const controller = jiti(resolve(frontendRoot, "src/features/trace-v49/exploration-v3/controller.server.ts"));
const nextConfig = jiti(resolve(frontendRoot, "next.config.ts"));
const rootRoute = jiti(resolve(frontendRoot, "src/app/api/trace/v3/exploration/route.ts"));
const catchAllRoute = jiti(resolve(frontendRoot, "src/app/api/trace/v3/exploration/[...path]/route.ts"));

equal(
  nextConfig.experimental?.preloadEntriesOnStart,
  false,
  "production startup does not eagerly preload unrelated archival route entries",
);

const runtime = readModelModule.getExplorationV3RuntimeReadModel();
const model = runtime.model;
const parsedModel = JSON.parse(modelBytes.toString("utf8"));
const validateArtifactSet = readModelModule.validateExplorationV3GeneratedArtifactSet;
equal(
  validateArtifactSet(checksumsBytes, manifestBytes, modelBytes).readModelSha256,
  manifest.artifact_sha256["read-model.json"],
  "standalone artifact-set validation",
);
const tamperedManifestBytes = Buffer.from(
  manifestBytes.toString("utf8").replace(
    manifest.source_sha,
    `6${manifest.source_sha.slice(1)}`,
  ),
  "utf8",
);
throws(
  () => validateArtifactSet(checksumsBytes, tamperedManifestBytes, modelBytes),
  /frozen_artifact_trust_anchor/u,
  "manifest tampering violates the frozen trust anchor",
);
const malformedChecksums = Buffer.from(checksumsBytes.toString("utf8").replace("  manifest.json", " manifest.json"));
throws(
  () => validateArtifactSet(malformedChecksums, manifestBytes, modelBytes),
  /frozen_artifact_trust_anchor/u,
  "checksum-ledger tampering violates the frozen trust anchor",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.incidences[0].concept_id = "concept:tampered";
    }),
  ),
  /incidence_owner/u,
  "flattened incidence must equal its nested participant",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.associations[0].participants[0].ordinal = 0;
    }),
  ),
  /unordered_incidence_ordinals/u,
  "unordered associations reject ordinals",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.associations[0].participants[0].role_id = "role:tampered";
    }),
  ),
  /participant_role_semantics/u,
  "role bindings follow roles-meaningful semantics",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      const association = changed.research_controls.associations.find(
        (item) => item.internal_pair_links.length > 0,
      );
      association.internal_pair_links[0].endpoint_sense_ids[0] = "sense:tampered";
    }),
  ),
  /association_semantic_hash/u,
  "internal pair endpoint tampering breaks the normative association hash",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.compositions[0].coherence_review.association_realization_ids.pop();
      const reviewId = changed.research_controls.compositions[0].global_coherence_review_id;
      changed.research_controls.composition_coherence_reviews.find(
        (item) => item.composition_coherence_review_id === reviewId,
      ).association_realization_ids.pop();
    }),
  ),
  /composition_review_semantic_hash/u,
  "composition review trace tampering breaks its normative semantic hash",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      addValidControlTransition(changed);
    }),
  ),
  /transition_unlisted_by_workflow/u,
  "every governed transition must be explicitly selected by at least one workflow",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.concepts[0].product_eligible = true;
    }),
  ),
  /control_product_eligible/u,
  "synthetic controls cannot be made product eligible",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.concepts[0].product_eligibility_disposition = "ELIGIBLE";
    }),
  ),
  /control_product_disposition/u,
  "synthetic controls cannot receive a product-eligible disposition",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.concepts[0].product_path = "/invented-product-path";
    }),
  ),
  /control_product_path/u,
  "synthetic controls cannot receive a product path",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      const realization = changed.research_controls.association_realizations.find(
        (item) => item.association_kind === "PAIR",
      );
      realization.realization_kind = "HYPEREDGE_HUB";
    }),
  ),
  /pair_realization/u,
  "pair realizations must remain exact two-incidence pair edges",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.capabilities.association_and_composition_identity_separate = false;
    }),
  ),
  /capability_boundary/u,
  "association/composition identity separation capability is invariant",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.compositions[0].composition_id =
        changed.research_controls.associations[0].association_id;
    }),
  ),
  /association_composition_identity_collision/u,
  "association and composition identifiers cannot collide",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      const group = changed.research_controls.associations.find(
        (item) => item.internal_pair_links.length > 0,
      );
      const pairRevisionId = group.internal_pair_links[0].pair_association_revision_id;
      changed.research_controls.associations.find(
        (item) => item.association_revision_id === pairRevisionId,
      ).eligibility.lifecycle_state = "INACTIVE";
    }),
  ),
  /association_semantic_hash/u,
  "internal pair lifecycle tampering breaks its governed association hash",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.associations[0].participants.reverse();
    }),
  ),
  /unordered_participant_order/u,
  "unordered association participant storage must remain canonical",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.navigation_states[0].unexpected = true;
    }),
  ),
  /state\.keys/u,
  "navigation state DTO rejects undeclared fields",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.navigation_states[0].nodes[0].unexpected = true;
    }),
  ),
  /state\.node\.keys/u,
  "navigation node DTO rejects undeclared fields",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.navigation_states[0].path[0].unexpected = true;
    }),
  ),
  /state\.path_step\.keys/u,
  "navigation path-step DTO rejects undeclared fields",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.navigation_states[0].presentation.unexpected = true;
    }),
  ),
  /state\.presentation\.keys/u,
  "navigation presentation DTO rejects undeclared fields",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.workflows[0].unexpected = true;
    }),
  ),
  /workflow\.keys/u,
  "workflow DTO rejects undeclared fields",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.exports[0].unexpected = true;
    }),
  ),
  /export\.keys/u,
  "export DTO rejects undeclared fields",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.exports[0].presentation.unexpected = true;
    }),
  ),
  /export\.presentation\.keys/u,
  "export presentation DTO rejects undeclared fields",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.exports[0].projection_preservation_records[0].unexpected = true;
    }),
  ),
  /export\.projection_preservation_record\.keys/u,
  "projection-preservation DTO rejects undeclared fields",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      addValidControlTransition(changed).unexpected = true;
    }),
  ),
  /transition\.keys/u,
  "transition DTO rejects undeclared fields",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.navigation_states[0].nodes.pop();
    }),
  ),
  /state_node_count/u,
  "navigation state retains the governed minimum node shape",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.navigation_states[0].path = [];
    }),
  ),
  /state_path_empty/u,
  "navigation state requires a governed path",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      const state = changed.research_controls.navigation_states[0];
      state.path[1].from_navigation_node_id = state.path[1].to_navigation_node_id;
      state.path[1].to_navigation_node_id = state.path[0].to_navigation_node_id;
    }),
  ),
  /state_path_discontinuous/u,
  "navigation path steps must be continuous",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      const state = changed.research_controls.navigation_states[0];
      state.focus_navigation_node_id = state.path[0].from_navigation_node_id;
    }),
  ),
  /state_terminal_focus/u,
  "navigation path terminal must equal focus",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      const state = changed.research_controls.navigation_states[0];
      const composition = changed.research_controls.compositions.find(
        (item) => item.composition_revision_id === state.composition_revision_id,
      );
      const outside = changed.research_controls.concepts.find(
        (item) => !composition.composition_node_ids.includes(item.concept_id),
      );
      state.nodes.find((item) => item.node_kind === "CONCEPT").concept_id = outside.concept_id;
    }),
  ),
  /state_node_outside_composition/u,
  "concept navigation nodes must belong to the selected composition",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      const state = changed.research_controls.navigation_states[0];
      const composition = changed.research_controls.compositions.find(
        (item) => item.composition_revision_id === state.composition_revision_id,
      );
      const inside = new Set(
        composition.association_realizations.map((item) => item.association_revision_id),
      );
      const outside = changed.research_controls.associations.find(
        (item) => !inside.has(item.association_revision_id),
      );
      state.nodes.find((item) => item.node_kind === "ASSOCIATION").association_revision_id =
        outside.association_revision_id;
    }),
  ),
  /state_node_outside_composition/u,
  "association navigation nodes must resolve through a selected-composition realization",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.navigation_states[0].realm = "PRODUCTION";
    }),
  ),
  /state_composition_realm/u,
  "navigation state realm must equal its composition realm",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.workflows[0].state_ids = [];
    }),
  ),
  /workflow_initial_state_membership/u,
  "workflow initial state must occur in its own state set",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.workflows[0].realm = "PRODUCTION";
    }),
  ),
  /workflow_state_realm/u,
  "workflow realm must equal every member state realm",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.workflows[0].association_realization_ids.pop();
    }),
  ),
  /workflow_realization_trace_exact_set/u,
  "workflow realization trace equals the union of state-composition realizations",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.workflows[0].association_revision_ids.pop();
    }),
  ),
  /workflow_association_trace_exact_set/u,
  "workflow association trace equals its realization-derived revision set",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      const second = addClonedControlState(changed);
      changed.research_controls.workflows[0].state_ids.push(second.state_id);
    }),
  ),
  /workflow_reachability/u,
  "workflow reachable flag is derived from graph reachability",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      addValidControlTransition(changed).realm = "PRODUCTION";
    }),
  ),
  /transition_realm/u,
  "transition realm must equal both endpoint realms",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      const transition = addValidControlTransition(changed);
      transition.to_state_id = "state:v3:missing-endpoint";
      transition.state_mutated = true;
    }),
  ),
  /transition_endpoint/u,
  "transition endpoints must resolve",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      const second = addClonedControlState(changed);
      addValidControlTransition(changed, { toStateId: second.state_id });
    }),
  ),
  /transition_unlisted_by_workflow/u,
  "every governed transition must be selected explicitly by at least one workflow",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      const transition = addValidControlTransition(changed);
      transition.association_revision_id = changed.research_controls.associations.find(
        (item) => item.association_revision_id !== transition.association_revision_id,
      ).association_revision_id;
    }),
  ),
  /transition_trace$/u,
  "transition incidence, association, and realization trace must agree",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      addValidControlTransition(changed).state_mutated = true;
    }),
  ),
  /transition_state_mutated/u,
  "transition state-mutated assertion is endpoint-derived",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      const transition = addValidControlTransition(changed);
      transition.association_realization_id = null;
    }),
  ),
  /transition_trace_partial/u,
  "transition trace cannot be partially populated",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.exports[0].realm = "PRODUCTION";
    }),
  ),
  /export_realm/u,
  "export realm equals its workflow, state, and composition realms",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.exports[0].association_realization_ids.pop();
    }),
  ),
  /export_realization_trace_exact_set/u,
  "export realization trace equals its workflow/state composition trace",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.exports[0].association_revision_ids.pop();
    }),
  ),
  /export_association_trace_exact_set/u,
  "export association trace equals its workflow/state composition trace",
);

// Named normative-binding probes. Each code proves that semantic material,
// presentation material, and hash-derived identity are rejected independently.
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.navigation_states[0].semantic_sha256 = "0".repeat(64);
    }),
  ),
  /state_semantic_hash/u,
  "STATE_SEMANTIC_HASH",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.navigation_states[0].presentation_sha256 = "0".repeat(64);
    }),
  ),
  /state_presentation_hash/u,
  "STATE_PRESENTATION_HASH",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.navigation_states[0].state_id = "state:v3:000000000000000000000000";
    }),
  ),
  /state_id_hash/u,
  "STATE_ID_HASH",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.workflows[0].semantic_sha256 = "0".repeat(64);
    }),
  ),
  /workflow_semantic_hash/u,
  "WORKFLOW_SEMANTIC_HASH",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.workflows[0].workflow_id = "workflow:v3:000000000000000000000000";
    }),
  ),
  /workflow_id_hash/u,
  "WORKFLOW_ID_HASH",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.exports[0].semantic_sha256 = "0".repeat(64);
    }),
  ),
  /export_semantic_hash/u,
  "EXPORT_SEMANTIC_HASH",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.exports[0].presentation_sha256 = "0".repeat(64);
    }),
  ),
  /export_presentation_hash/u,
  "EXPORT_PRESENTATION_HASH",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.exports[0].export_id = "export:v3:000000000000000000000000";
    }),
  ),
  /export_id_hash/u,
  "EXPORT_ID_HASH",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      const association = changed.research_controls.associations[0];
      association.participants[0].participant_scope_id = changed.research_controls.scopes.find(
        (scope) => scope.scope_id !== association.scope.scope_id,
      ).scope_id;
    }),
  ),
  /participant_scope_divergence/u,
  "PARTICIPANT_SCOPE_DIVERGENCE",
);

for (const [probe, collection] of [
  ["STATE_FACT_BOUNDARY_EXTRA_KEY", "navigation_states"],
  ["WORKFLOW_FACT_BOUNDARY_EXTRA_KEY", "workflows"],
  ["EXPORT_FACT_BOUNDARY_EXTRA_KEY", "exports"],
]) {
  throws(
    () => validateArtifactSet(
      ...reboundArtifactSet(manifest, parsedModel, (changed) => {
        changed.research_controls[collection][0].fact_boundary.unexpected = true;
      }),
    ),
    /fact_boundary_keys/u,
    probe,
  );
}
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      addValidControlTransition(changed).fact_boundary.unexpected = true;
    }),
  ),
  /fact_boundary_keys/u,
  "TRANSITION_FACT_BOUNDARY_EXTRA_KEY",
);

for (const [probe, mutate, expected] of [
  ["STATE_MISSING_COMPOSITION", (changed) => {
    changed.research_controls.navigation_states[0].composition_revision_id = "composition-revision:v3:missing";
  }, /state_composition$/u],
  ["STATE_FALSE_BIPARTITE", (changed) => {
    changed.research_controls.navigation_states[0].bipartite_alternation_valid = false;
  }, /state_bipartite_flag/u],
  ["STATE_MISSING_FOCUS", (changed) => {
    changed.research_controls.navigation_states[0].focus_navigation_node_id = "navigation-node:v3:missing";
  }, /state_focus_node/u],
  ["STATE_DUPLICATE_NODES", (changed) => {
    const state = changed.research_controls.navigation_states[0];
    state.nodes.push(structuredClone(state.nodes[0]));
  }, /state\.navigation_node_ids/u],
  ["STATE_BAD_DISCRIMINATOR_REFERENCE", (changed) => {
    const state = changed.research_controls.navigation_states[0];
    const conceptNode = state.nodes.find((node) => node.node_kind === "CONCEPT");
    conceptNode.association_revision_id = changed.research_controls.associations[0].association_revision_id;
  }, /state_concept_node/u],
  ["STATE_BAD_PATH_REFERENCE", (changed) => {
    changed.research_controls.navigation_states[0].path[0].to_navigation_node_id = "navigation-node:v3:missing";
  }, /state_path_reference/u],
  ["STATE_WRONG_INCIDENCE", (changed) => {
    const state = changed.research_controls.navigation_states[0];
    state.path[0].incidence_id = changed.research_controls.incidences.find(
      (item) => item.incidence_id !== state.path[0].incidence_id,
    ).incidence_id;
  }, /state_path_incidence_ownership/u],
  ["WORKFLOW_MISSING_STATE", (changed) => {
    changed.research_controls.workflows[0].state_ids.push("state:v3:missing");
  }, /workflow_state$/u],
  ["WORKFLOW_DUPLICATE_STATE", (changed) => {
    const workflow = changed.research_controls.workflows[0];
    workflow.state_ids.push(workflow.state_ids[0]);
  }, /workflow\.state_ids/u],
  ["WORKFLOW_INVALID_KIND", (changed) => {
    changed.research_controls.workflows[0].transition_kind = "INVALID_KIND";
  }, /workflow_transition_kind/u],
  ["WORKFLOW_DUPLICATE_REALIZATION", (changed) => {
    const workflow = changed.research_controls.workflows[0];
    workflow.association_realization_ids.push(workflow.association_realization_ids[0]);
  }, /workflow\.association_realization_ids/u],
  ["WORKFLOW_DUPLICATE_REVISION", (changed) => {
    const workflow = changed.research_controls.workflows[0];
    workflow.association_revision_ids.push(workflow.association_revision_ids[0]);
  }, /workflow\.association_revision_ids/u],
  ["EXPORT_MISSING_REFERENCES", (changed) => {
    changed.research_controls.exports[0].workflow_id = "workflow:v3:missing";
  }, /export_trace/u],
  ["EXPORT_COMPOSITION_MISMATCH", (changed) => {
    const exported = changed.research_controls.exports[0];
    exported.composition_revision_id = changed.research_controls.compositions.find(
      (item) => item.composition_revision_id !== exported.composition_revision_id,
    ).composition_revision_id;
  }, /export_workflow_projection/u],
  ["EXPORT_FALSE_PRESERVATION_FLAG", (changed) => {
    changed.research_controls.exports[0].pair_projection_policy_preserved = false;
  }, /export_trace/u],
  ["EXPORT_INCOMPLETE_RECORDS", (changed) => {
    changed.research_controls.exports[0].projection_preservation_records.pop();
  }, /export_projection_record_set/u],
  ["EXPORT_INCORRECT_RECORD", (changed) => {
    changed.research_controls.exports[0].projection_preservation_records[0].realization_kind = "INVALID_KIND";
  }, /export_projection_record/u],
]) {
  throws(
    () => validateArtifactSet(...reboundArtifactSet(manifest, parsedModel, mutate)),
    expected,
    probe,
  );
}

throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      const first = addValidControlTransition(changed);
      const duplicate = addValidControlTransition(changed);
      duplicate.transition_id = first.transition_id;
    }),
  ),
  /transition_ids/u,
  "TRANSITION_DUPLICATE_ID",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      addValidControlTransition(changed).transition_kind = "INVALID_KIND";
    }),
  ),
  /transition_kind/u,
  "TRANSITION_INVALID_KIND",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      addValidControlTransition(changed).semantic_sha256 = "0".repeat(64);
    }),
  ),
  /transition_semantic_hash/u,
  "TRANSITION_SEMANTIC_HASH_MISMATCH",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      addValidControlTransition(changed).transition_id = "transition:v3:000000000000000000000000";
    }),
  ),
  /transition_id_hash/u,
  "TRANSITION_ID_HASH_MISMATCH",
);

throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      changed.research_controls.workflows[0].transition_ids = ["transition:v3:missing"];
    }),
  ),
  /workflow_transition_reference/u,
  "WORKFLOW_FOREIGN_TRANSITION_SELECTION",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      const transition = addValidControlTransition(changed);
      changed.research_controls.workflows[0].transition_ids = [
        transition.transition_id,
        transition.transition_id,
      ];
    }),
  ),
  /workflow\.transition_ids/u,
  "WORKFLOW_DUPLICATE_TRANSITION_SELECTION",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      const second = addClonedControlState(changed);
      const transition = addValidControlTransition(changed, { toStateId: second.state_id });
      changed.research_controls.workflows[0].transition_ids = [transition.transition_id];
    }),
  ),
  /workflow_selected_transition_scope/u,
  "WORKFLOW_SELECTED_TRANSITION_FOREIGN_STATE",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      const second = addClonedControlState(changed);
      const selectedSelf = addValidControlTransition(changed);
      addValidControlTransition(changed, { toStateId: second.state_id });
      const workflow = changed.research_controls.workflows[0];
      workflow.state_ids.push(second.state_id);
      workflow.transition_ids = [selectedSelf.transition_id];
    }),
  ),
  /workflow_reachability/u,
  "WORKFLOW_REACHABILITY_USES_EXACT_SELECTED_SUBSET",
);
throws(
  () => validateArtifactSet(
    ...reboundArtifactSet(manifest, parsedModel, (changed) => {
      const controlsSurface = changed.research_controls;
      const follow = addValidControlTransition(changed);
      const move = addValidControlTransition(changed);
      move.transition_kind = "MOVE_FOCUS";
      move.incidence_id = null;
      move.association_revision_id = null;
      move.association_realization_id = null;
      refreshTransitionBinding(move);
      const firstWorkflow = controlsSurface.workflows[0];
      firstWorkflow.transition_ids = [follow.transition_id];
      refreshWorkflowAndDependentExports(changed, firstWorkflow);
      const sharedStateWorkflow = structuredClone(firstWorkflow);
      sharedStateWorkflow.transition_kind = "MOVE_FOCUS";
      sharedStateWorkflow.transition_ids = [move.transition_id];
      refreshWorkflowBinding(sharedStateWorkflow);
      controlsSurface.workflows.push(sharedStateWorkflow);
      changed.capabilities.control_workflow_count = controlsSurface.workflows.length;
    }),
  ),
  /transition_surface_disallowed/u,
  "WORKFLOW_SHARED_STATE_ALLOWED_WITH_EXPLICIT_TRANSITIONS",
);
equal(runtime.readModelSha256, manifest.artifact_sha256["read-model.json"], "runtime model identity");
check(Object.isFrozen(runtime), "runtime is frozen");
check(Object.isFrozen(model.research_controls.associations[0]), "nested model records are frozen");
deepEqual(Object.keys(model.active_product).sort(), [...SURFACE_KEYS].sort(), "active surface class set");
deepEqual(Object.keys(model.research_controls).sort(), [...SURFACE_KEYS].sort(), "control surface class set");
check(SURFACE_KEYS.every((key) => model.active_product[key].length === 0), "every active product class fails closed");
check(Object.values(model.closure_flags).every((value) => value === false), "all closure flags remain false");
equal(model.capabilities.governed_product_arity_bound, null, "product arity bound remains unresolved");
equal(
  model.capabilities.backend_association_arity_support,
  "PAIR_2_OR_HIGHER_ORDER_3_PLUS_NO_FIXED_SCHEMA_MAXIMUM",
  "backend arity support is distinct from product bound",
);
equal(model.capabilities.production_activation_count, 0, "production activation count");
equal(model.capabilities.research_controls_only, true, "research-controls-only status");
equal(model.capabilities.transition_derivation_policy, "NONE_NO_V2_INHERITANCE", "transition derivation boundary");
equal(model.capabilities.transition_status, "FAIL_CLOSED_NO_ACTIVE_PRODUCT_STATE_GRAPH", "transition status");
equal(model.capabilities.transitions_available, false, "transitions unavailable");
equal(model.active_product.transitions.length, 0, "active transitions empty");
equal(model.research_controls.transitions.length, 0, "control transitions empty rather than synthesized");

const controls = model.research_controls;
deepEqual(
  {
    association_realizations: controls.association_realizations.length,
    associations: controls.associations.length,
    composition_coherence_reviews: controls.composition_coherence_reviews.length,
    compositions: controls.compositions.length,
    concept_senses: controls.concept_senses.length,
    concepts: controls.concepts.length,
    exports: controls.exports.length,
    incidences: controls.incidences.length,
    navigation_states: controls.navigation_states.length,
    scopes: controls.scopes.length,
    transitions: controls.transitions.length,
    workflows: controls.workflows.length,
  },
  {
    association_realizations: 10,
    associations: 14,
    composition_coherence_reviews: 2,
    compositions: 2,
    concept_senses: 21,
    concepts: 21,
    exports: 1,
    incidences: 37,
    navigation_states: 1,
    scopes: 6,
    transitions: 0,
    workflows: 1,
  },
  "separate governed control class counts",
);
check(
  SURFACE_KEYS.flatMap((key) => controls[key]).every(
    (item) => item.fact_boundary.data_class === "SYNTHETIC_CONTROL"
      && item.fact_boundary.production_fact === false
      && item.fact_boundary.synthetic_control === true,
  ),
  "every control record is explicitly non-production",
);

const pairControls = controls.associations.filter((item) => item.association_kind === "PAIR");
const higherOrderControls = controls.associations.filter((item) => item.association_kind === "HIGHER_ORDER");
equal(pairControls.length, 9, "pair control count");
equal(higherOrderControls.length, 5, "higher-order control count");
check(pairControls.every((item) => item.arity === 2), "pair arity is exactly two");
check(
  higherOrderControls.every((item) => item.arity >= 3 && item.pair_projection_policy === "NONE"),
  "higher-order controls forbid implicit pair projection",
);
check(
  higherOrderControls.every((item) => item.participants.length === item.arity),
  "higher-order participant incidence count equals arity",
);
const nestedIncidenceIds = new Set(
  controls.associations.flatMap((item) => item.participants.map((participant) => participant.incidence_id)),
);
deepEqual(
  [...nestedIncidenceIds].sort(),
  controls.incidences.map((item) => item.incidence_id).sort(),
  "first-class incidence collection exactly projects nested participant incidences",
);

const sparse = higherOrderControls.find((item) => item.arity === 5 && item.review.global_coherence === "PASS");
check(sparse, "sparse valid arity-five control exists");
equal(sparse.lifecycle_state, undefined, "lifecycle is nested under eligibility");
equal(sparse.eligibility.lifecycle_state, "ACTIVE", "synthetic higher-order control exercises active branch");
equal(sparse.eligibility.product_eligible, false, "synthetic active branch remains product-ineligible");
equal(sparse.internal_pair_links.length, 2, "sparse hyperedge retains only two governed internal pairs");
check(sparse.internal_pair_links.length < 10, "arity-five hyperedge does not manufacture ten pairs");
equal(sparse.pair_projection_policy, "NONE", "sparse hyperedge projection policy");

const invalidClique = higherOrderControls.find(
  (item) => item.arity === 4 && item.internal_pair_links.length === 6,
);
check(invalidClique, "complete-pair-clique invalid group control exists");
equal(invalidClique.review.global_coherence, "FAIL", "full pair clique fails global coherence");
equal(invalidClique.eligibility.lifecycle_state, "INACTIVE", "invalid clique is inactive");
equal(invalidClique.eligibility.product_eligible, false, "invalid clique is product-ineligible");
const pending = higherOrderControls.find((item) => item.review.review_state === "PENDING");
check(pending, "pending review control exists");
equal(pending.activation.requested_state, "ACTIVE", "pending control attempts activation");
equal(pending.activation.decision, "REJECT", "pending control fails closed");
equal(pending.eligibility.lifecycle_state, "INACTIVE", "pending control is not active");

check(
  controls.association_realizations.every((realization) => {
    if (realization.association_kind !== "HIGHER_ORDER") return true;
    const association = controls.associations.find(
      (item) => item.association_revision_id === realization.association_revision_id,
    );
    return realization.realization_kind !== "PAIR_EDGE"
      && association
      && realization.realized_incidence_ids.length === association.arity;
  }),
  "higher-order realizations preserve complete hyperedges",
);
const coherentComposition = controls.compositions.find(
  (item) => item.coherence_review.global_coherence === "PASS",
);
const incoherentComposition = controls.compositions.find(
  (item) => item.coherence_review.global_coherence === "FAIL",
);
check(coherentComposition && incoherentComposition, "both coherent and incoherent composition controls exist");
check(
  !controls.associations.some((association) => association.association_id === coherentComposition.composition_id),
  "association and composition identities are disjoint",
);
equal(coherentComposition.eligibility.product_eligible, false, "coherent synthetic composition remains non-product");
equal(incoherentComposition.renderability, "PASS", "incoherent composition is still renderable");
equal(incoherentComposition.eligibility.product_eligible, false, "renderability does not create eligibility");
equal(incoherentComposition.coherence_review.decision, "INCOHERENT", "composition review preserves incoherence");

const workflow = controls.workflows[0];
const exported = controls.exports[0];
const state = controls.navigation_states[0];
check(workflow.state_ids.includes(state.state_id), "workflow resolves governed state");
equal(exported.workflow_id, workflow.workflow_id, "export resolves workflow identity");
equal(exported.state_id, state.state_id, "export resolves state identity");
equal(exported.pair_projection_policy_preserved, true, "export preserves pair projection policy");
check(
  exported.projection_preservation_records.some(
    (item) => item.pair_projection_policy === "NONE" && item.realization_kind !== "PAIR_EDGE",
  ),
  "export preserves higher-order realization without projected pair edges",
);

const capabilities = service.retrieveExplorationV3Capabilities();
check(capabilities.ok, "capabilities service succeeds");
equal(capabilities.data.data.capabilities.active_product_association_count, 0, "capabilities active association count");
equal(capabilities.data.data.capabilities.control_association_count, 14, "capabilities control association count");
for (const collection of COLLECTIONS) {
  const activeResult = service.listExplorationV3Collection(collection);
  const controlResult = service.listExplorationV3Collection(collection, true);
  check(activeResult.ok && controlResult.ok, `${collection} services succeed`);
  equal(activeResult.data.data.count, 0, `${collection} active service fails closed`);
}
const hiddenControl = service.retrieveExplorationV3CollectionItem(
  "associations",
  sparse.association_id,
);
check(!hiddenControl.ok, "synthetic association is not retrievable as active product fact");
equal(hiddenControl.code, "NOT_ACTIVE_PRODUCT_FACT", "active/control identity boundary error");
const visibleControl = service.retrieveExplorationV3CollectionItem(
  "associations",
  sparse.association_id,
  true,
);
check(visibleControl.ok, "synthetic association is retrievable in control namespace");
equal(visibleControl.data.data.item.association_id, sparse.association_id, "control identity retrieval");

const capabilitiesResponse = await controller.dispatchExplorationV3Request(
  new Request("http://localhost/api/trace/v3/exploration/capabilities"),
  ["capabilities"],
);
equal(capabilitiesResponse.status, 200, "capabilities HTTP status");
equal(capabilitiesResponse.headers.get("cache-control"), "private, no-store", "research response cache policy");
equal(capabilitiesResponse.headers.get("x-trace-product-activation"), "FAIL-CLOSED", "activation header");
equal(capabilitiesResponse.headers.get("x-trace-read-model"), runtime.readModelSha256, "read-model header");
const capabilitiesPayload = await jsonResponse(capabilitiesResponse);
equal(capabilitiesPayload.data.capabilities.governed_product_arity_bound, null, "HTTP unresolved product bound");

deepEqual(
  service.EXPLORATION_V3_COLLECTIONS,
  Object.fromEntries(Object.entries(COLLECTION_IDENTITIES).map(([collection, [surfaceKey, identity]]) => [
    collection,
    { identity, surfaceKey },
  ])),
  "exact collection-to-DTO surface and identity map",
);
const expectedReadPaths = [
  "/capabilities",
  ...COLLECTIONS.flatMap((collection) => [
    `/${collection}`,
    `/${collection}/{${COLLECTION_IDENTITIES[collection][1]}}`,
  ]),
  ...COLLECTIONS.flatMap((collection) => [
    `/controls/${collection}`,
    `/controls/${collection}/{${COLLECTION_IDENTITIES[collection][1]}}`,
  ]),
  "/baseline/reconciliation",
];
deepEqual(model.capabilities.read_paths, expectedReadPaths, "advertised path parity is exact");

for (const collection of COLLECTIONS) {
  const [surfaceKey, identity] = COLLECTION_IDENTITIES[collection];
  const activeListResponse = await controller.dispatchExplorationV3Request(
    new Request(`http://localhost/api/trace/v3/exploration/${collection}`),
    [collection],
  );
  equal(activeListResponse.status, 200, `${collection} active list HTTP status`);
  equal((await jsonResponse(activeListResponse)).data.count, 0, `${collection} active list empty`);
  const controlListResponse = await controller.dispatchExplorationV3Request(
    new Request(`http://localhost/api/trace/v3/exploration/controls/${collection}`),
    ["controls", collection],
  );
  equal(controlListResponse.status, 200, `${collection} control list HTTP status`);
  equal(
    (await jsonResponse(controlListResponse)).data.count,
    controls[surfaceKey].length,
    `${collection} control list count`,
  );

  const representative = controls[surfaceKey][0];
  const identifier = representative?.[identity] ?? `${identity}:unknown`;
  const controlItemResponse = await controller.dispatchExplorationV3Request(
    new Request(`http://localhost/api/trace/v3/exploration/controls/${collection}/${identifier}`),
    ["controls", collection, identifier],
  );
  equal(
    controlItemResponse.status,
    representative ? 200 : 404,
    `${collection} control item route status`,
  );
  if (representative) {
    equal(
      (await jsonResponse(controlItemResponse)).data.item[identity],
      identifier,
      `${collection} control item identity`,
    );
  }
  const activeItemResponse = await controller.dispatchExplorationV3Request(
    new Request(`http://localhost/api/trace/v3/exploration/${collection}/${identifier}`),
    [collection, identifier],
  );
  equal(activeItemResponse.status, 404, `${collection} control cannot resolve through active endpoint`);
  equal(
    (await jsonResponse(activeItemResponse)).code,
    representative ? "NOT_ACTIVE_PRODUCT_FACT" : "INVALID_CONTROL",
    `${collection} active/control isolation`,
  );
  const unknownControlResponse = await controller.dispatchExplorationV3Request(
    new Request(`http://localhost/api/trace/v3/exploration/controls/${collection}/unknown:v3:item`),
    ["controls", collection, "unknown:v3:item"],
  );
  equal(unknownControlResponse.status, 404, `${collection} unknown control item status`);
  const unknownControlPayload = await jsonResponse(unknownControlResponse);
  equal(
    unknownControlPayload.code,
    collection === "associations"
      ? "INVALID_ASSOCIATION"
      : collection === "compositions"
        ? "INVALID_COMPOSITION"
        : "INVALID_CONTROL",
    `${collection} unknown item error code`,
  );

  for (const [prefix, expectedStatus] of [
    [[], 404],
    [["controls"], representative ? 200 : 404],
  ]) {
    const itemPath = [...prefix, collection, identifier];
    const itemHead = await controller.dispatchExplorationV3Request(
      new Request(`http://localhost/api/trace/v3/exploration/${itemPath.join("/")}`, { method: "HEAD" }),
      itemPath,
    );
    equal(itemHead.status, expectedStatus, `${collection} ${prefix.length ? "control" : "active"} item HEAD status`);
    equal(await itemHead.text(), "", `${collection} item HEAD has no body`);
  }
  for (const prefix of [[], ["controls"]]) {
    const listPath = [...prefix, collection];
    const listHead = await controller.dispatchExplorationV3Request(
      new Request(`http://localhost/api/trace/v3/exploration/${listPath.join("/")}`, { method: "HEAD" }),
      listPath,
    );
    equal(listHead.status, 200, `${collection} ${prefix.length ? "control" : "active"} list HEAD status`);
    equal(await listHead.text(), "", `${collection} list HEAD has no body`);
  }
}

const transitionResponse = await catchAllRoute.GET(
  new Request("http://localhost/api/trace/v3/exploration/transitions"),
  { params: Promise.resolve({ path: ["transitions"] }) },
);
equal(transitionResponse.status, 200, "App Router catch-all awaits Promise params");
equal((await jsonResponse(transitionResponse)).data.count, 0, "App Router transition response empty");
const headResponse = await catchAllRoute.HEAD(
  new Request("http://localhost/api/trace/v3/exploration/controls/workflows", { method: "HEAD" }),
  { params: Promise.resolve({ path: ["controls", "workflows"] }) },
);
equal(headResponse.status, 200, "HEAD status");
equal(await headResponse.text(), "", "HEAD has no body");
const postResponse = await controller.dispatchExplorationV3Request(
  new Request("http://localhost/api/trace/v3/exploration/capabilities", { method: "POST" }),
  ["capabilities"],
);
equal(postResponse.status, 405, "read-only endpoint rejects POST");
const unknownResponse = await controller.dispatchExplorationV3Request(
  new Request("http://localhost/api/trace/v3/exploration/unknown"),
  ["unknown"],
);
equal(unknownResponse.status, 404, "unknown endpoint status");
const optionsResponse = controller.dispatchExplorationV3Request(
  new Request("http://localhost/api/trace/v3/exploration/capabilities", { method: "OPTIONS" }),
  ["capabilities"],
);
equal((await optionsResponse).status, 204, "OPTIONS status");
const rootResponse = rootRoute.GET();
equal(rootResponse.status, 308, "root route redirects");
equal(rootResponse.headers.get("location"), "/api/trace/v3/exploration/capabilities", "root redirect target");
const rootHeadResponse = rootRoute.HEAD();
equal(rootHeadResponse.status, 308, "root HEAD redirects");
equal(await rootHeadResponse.text(), "", "root HEAD has no body");

process.stdout.write(`${JSON.stringify({
  active_product_association_count: model.active_product.associations.length,
  active_product_transition_count: model.active_product.transitions.length,
  check_count: checkCount,
  control_association_count: controls.associations.length,
  control_class_count: SURFACE_KEYS.length,
  control_composition_count: controls.compositions.length,
  control_incidence_count: controls.incidences.length,
  higher_order_control_count: higherOrderControls.length,
  read_model_sha256: runtime.readModelSha256,
  status: "PASS",
  transition_derivation_policy: model.capabilities.transition_derivation_policy,
}, null, 2)}\n`);
