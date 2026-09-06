/* Exploration view v1 — the acceptance contract (FRONTEND_DESIGN_DECISION.md §7i):
   the 26 starting points resolve to their own seed (the six two-step words
   included; the five isolated words absent); over ALL 5,760 V2 states the
   More / Less controls are available exactly when a legal transition changes
   the visible term count, and applying them changes it by exactly one;
   Another view keeps the starting point and the category, cycles a
   deduplicated pool (visible terms + associations + focus) and is single
   when the pool is one; a view restores by map/state/template/variant
   byte-identically; the presentation is deterministic and semantics-free;
   every template × variant lays out 2-, 3- and 4-term views inside the field
   without label overlap; the PNG is the same scene; the frozen v2 renderer,
   controller, service and derivations are byte-identical to HEAD and the
   sealed export ledger still replays; the page never reads V3, exposes no
   graph editing, and the narration gate holds. */
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { readFileSync, readdirSync } from "node:fs";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(here, "..");
const repoRoot = join(frontendRoot, "..");
const require = createRequire(import.meta.url);
const jiti = require("jiti")(fileURLToPath(import.meta.url), {
  interopDefault: true,
  tryNative: false,
  alias: { "@": join(frontendRoot, "src"), "server-only": join(here, "server-only-marker.mjs") },
});
const sharp = require("sharp");

let checks = 0;
const check = (condition, message) => { assert.ok(condition, message); checks += 1; };
const read = (path) => readFileSync(join(frontendRoot, path), "utf8");

const svc = await jiti.import(join(frontendRoot, "src/features/trace-v49/exploration-view/service.server.ts"));
const tpl = await jiti.import(join(frontendRoot, "src/features/trace-v49/exploration-view/templates.ts"));
const types = await jiti.import(join(frontendRoot, "src/features/trace-v49/exploration-view/types.ts"));
const render = await jiti.import(join(frontendRoot, "src/features/trace-v49/exploration-view/render.ts"));
const renderServer = await jiti.import(join(frontendRoot, "src/features/trace-v49/exploration-view/render.server.ts"));
const forms = await jiti.import(join(frontendRoot, "src/features/trace-v49/exploration-view/forms.ts"));
const { getExplorationV2ReadModel } = await jiti.import(join(frontendRoot, "src/features/trace-v49/exploration-v2/read-model.server.ts"));
const { getExplorationV2TransitionIndex } = await jiti.import(join(frontendRoot, "src/features/trace-v49/exploration-v2/transition.server.ts"));
const v2 = await jiti.import(join(frontendRoot, "src/features/trace-v49/exploration-v2/service.server.ts"));
const { createSystemSuggestions } = await jiti.import(join(frontendRoot, "src/features/system-suggestions/service.server.ts"));
const { explorationFallbackNote, openInquiryFallbackNote } = await jiti.import(join(frontendRoot, "src/features/system-suggestions/providers.server.ts"));

const model = getExplorationV2ReadModel();
const transitions = getExplorationV2TransitionIndex(model);
const labelOf = new Map(model.vocabulary.map((term) => [term.vocabulary_id, term.canonical_label]));
const categoryOfEntry = new Map(model.categories.map((entry) => [entry.category_entry_id, entry.category_id]));
const stateKey = (state) => JSON.stringify([[...state.visible_node_ids].sort(), [...state.visible_association_ids].sort(), state.focused_node_id]);

/* --- A · the starting points --- */
const points = svc.listExplorationStartingPoints();
check(points.ok && points.data.starting_points.length === 26, "twenty-six governed starting points");
const seeds = new Set(Object.values(model.compositions).map((composition) => composition.seed_node_id));
check(points.data.starting_points.every((point) => seeds.has(point.vocabulary_id)), "every starting point seeds a composition");
const isolated = model.vocabulary.filter((term) => !model.associations.some((association) => association.endpoint_vocabulary_ids.includes(term.vocabulary_id)));
check(isolated.length === 5 && isolated.every((term) => !points.data.starting_points.some((point) => point.vocabulary_id === term.vocabulary_id)), "the five isolated words never open a view");
const twoStep = points.data.starting_points.filter((point) => point.two_step).map((point) => point.label).sort();
/* two-step = reached through a governed SELECT_COMPOSITION after the entry's initial state: the six words without a
   canonical entry of their own, plus the words whose canonical root has no real More while another root has */
check(["commodification", "consumer culture", "craft", "design education", "imitation", "photography"].every((word) => twoStep.includes(word)), `the six words without a canonical entry are two-step (${twoStep.join(", ")})`);
for (const point of points.data.starting_points.filter((item) => item.two_step)) {
  const view = svc.createExplorationView({ vocabulary_id: point.vocabulary_id }).data;
  const entry = model.categories.find((item) => item.category_entry_id === view.restore.map_id);
  const initial = model.states[entry.initial_state_id];
  const reached = transitions.resolve(initial, "SELECT_COMPOSITION", view.map.composition.composition_id)?.next_state;
  check(reached && reached.state_id === view.restore.state_id, `${point.label}: the two-step root is the entry's initial state followed by one governed SELECT_COMPOSITION`);
}
for (const point of points.data.starting_points) {
  const view = svc.createExplorationView({ vocabulary_id: point.vocabulary_id });
  check(view.ok, `${point.label} opens a view`);
  check(view.data.map.composition.seed_node_id === point.vocabulary_id && view.data.starting_point.vocabulary_id === point.vocabulary_id, `${point.label} lands on its own seed`);
  check(view.data.map.state.focused_node_id === point.vocabulary_id && view.data.map.state.expanded_node_ids.length === 0, `${point.label} opens at a composition root`);
  check(view.data.controls.more.available === point.expandable, `${point.label}: expandable matches the initial view's More`);
  const candidates = Object.values(model.compositions).filter((composition) => composition.seed_node_id === point.vocabulary_id);
  const anyExpandable = candidates.some((composition) => {
    const root = Object.values(model.states).find((state) => state.composition_id === composition.composition_id && state.focused_node_id === composition.seed_node_id && state.expanded_node_ids.length === 0);
    return transitions.targets(root, "EXPAND_NODE").some((target) => transitions.resolve(root, "EXPAND_NODE", target)?.next_state.visible_node_ids.length > root.visible_node_ids.length);
  });
  check(anyExpandable === point.expandable, `${point.label}: prefers a root with a real More when one exists`);
}
check(!svc.createExplorationView({ vocabulary_id: isolated[0].vocabulary_id }).ok, "an isolated word is refused");
check(svc.getDefaultStartingPointId() === points.data.starting_points.find((point) => point.label === "design diplomacy")?.vocabulary_id, "the default starting point is the largest governed pool");

/* --- B · More / Less over all 5,760 states --- */
let moreStates = 0;
let lessStates = 0;
let neither = 0;
let lessByTwo = 0;
const effective = (state, action) => transitions.targets(state, action)
  .map((target) => transitions.resolve(state, action, target)?.next_state)
  .filter(Boolean)
  .filter((next) => action === "EXPAND_NODE" ? next.visible_node_ids.length > state.visible_node_ids.length : next.visible_node_ids.length < state.visible_node_ids.length);
for (const state of Object.values(model.states)) {
  const view = svc.retrieveExplorationView(state.category_entry_id, state.state_id);
  assert.ok(view.ok, `view for ${state.state_id}`);
  const more = effective(state, "EXPAND_NODE");
  const less = effective(state, "COLLAPSE_NODE");
  assert.equal(view.data.controls.more.available, more.length > 0, `More availability ${state.state_id}`);
  assert.equal(view.data.controls.less.available, less.length > 0, `Less availability ${state.state_id}`);
  if (more.length > 0) {
    moreStates += 1;
    const next = svc.applyExplorationViewAction(state.category_entry_id, { action: "MORE", expected_state_hash: state.state_hash, template_id: view.data.presentation.template_id, variant_id: view.data.presentation.variant_id });
    assert.ok(next.ok && next.data.map.nodes.length === state.visible_node_ids.length + 1, `More adds exactly one term ${state.state_id}`);
    assert.ok(next.data.presentation.template_id === view.data.presentation.template_id && next.data.presentation.variant_id === view.data.presentation.variant_id, `More keeps the treatment ${state.state_id}`);
    assert.ok(next.data.map.composition.composition_id === state.composition_id, `More stays in the composition ${state.state_id}`);
  } else {
    const refused = svc.applyExplorationViewAction(state.category_entry_id, { action: "MORE", expected_state_hash: state.state_hash, template_id: view.data.presentation.template_id, variant_id: view.data.presentation.variant_id });
    assert.ok(!refused.ok && refused.code === "ACTION_NOT_AVAILABLE", `More refused at the richest ${state.state_id}`);
  }
  if (less.length > 0) {
    lessStates += 1;
    const next = svc.applyExplorationViewAction(state.category_entry_id, { action: "LESS", expected_state_hash: state.state_hash, template_id: view.data.presentation.template_id, variant_id: view.data.presentation.variant_id });
    const smallest = Math.min(...less.map((candidate) => state.visible_node_ids.length - candidate.visible_node_ids.length));
    assert.ok(next.ok && next.data.map.nodes.length === state.visible_node_ids.length - smallest, `Less removes the smallest legal reduction ${state.state_id}`);
    if (smallest > 1) lessByTwo += 1;
  }
  if (more.length === 0 && less.length === 0) neither += 1;
}
check(moreStates === 1032 && lessStates === 2160 && neither === 2664, `the effective steps match the census (${moreStates} / ${lessStates} / ${neither})`);

/* --- C · Another view --- */
for (const point of points.data.starting_points) {
  const first = svc.createExplorationView({ vocabulary_id: point.vocabulary_id }).data;
  const pool = first.controls.another_view.pool_size;
  const compositions = Object.values(model.compositions).filter((composition) => composition.seed_node_id === point.vocabulary_id);
  check(pool >= 1 && pool <= compositions.length, `${point.label}: the pool is bounded by its compositions`);
  const rootKeys = new Set(compositions.map((composition) => stateKey(Object.values(model.states).find((state) => state.composition_id === composition.composition_id && state.focused_node_id === composition.seed_node_id && state.expanded_node_ids.length === 0))));
  check(pool === rootKeys.size, `${point.label}: the pool is the distinct pictures (${pool} of ${compositions.length} compositions)`);
  if (pool === 1) {
    check(!first.controls.another_view.available && first.controls.another_view.reason === "SINGLE_VIEW", `${point.label}: a single view says so`);
    const refused = svc.applyExplorationViewAction(first.restore.map_id, { action: "ANOTHER_VIEW", expected_state_hash: first.restore.state_hash, template_id: first.restore.template_id, variant_id: first.restore.variant_id });
    check(!refused.ok && refused.code === "ACTION_NOT_AVAILABLE", `${point.label}: Another view refused`);
    continue;
  }
  let current = first;
  const seen = [stateKey(model.states[current.restore.state_id])];
  for (let step = 0; step < pool; step += 1) {
    const next = svc.applyExplorationViewAction(current.restore.map_id, { action: "ANOTHER_VIEW", expected_state_hash: current.restore.state_hash, template_id: current.restore.template_id, variant_id: current.restore.variant_id });
    assert.ok(next.ok, `${point.label}: Another view step ${step}`);
    assert.equal(next.data.starting_point.vocabulary_id, point.vocabulary_id, `${point.label}: the starting point is kept`);
    assert.equal(categoryOfEntry.get(next.data.restore.map_id), point.category_id, `${point.label}: the category is kept`);
    assert.ok(next.data.map.state.expanded_node_ids.length === 0 && next.data.map.state.focused_node_id === point.vocabulary_id, `${point.label}: lands on a root`);
    const key = stateKey(model.states[next.data.restore.state_id]);
    if (step < pool - 1) assert.ok(!seen.includes(key), `${point.label}: step ${step} shows a picture not yet shown`);
    else assert.equal(key, seen[0], `${point.label}: the cycle returns to the first picture after ${pool} steps`);
    assert.ok(next.data.presentation.template_id !== current.presentation.template_id || next.data.presentation.variant_id !== current.presentation.variant_id || pool === 1, `${point.label}: the treatment moves with the view`);
    seen.push(key);
    current = next.data;
  }
}

/* --- D · restore and determinism --- */
{
  const first = svc.createExplorationView({ vocabulary_id: points.data.starting_points.find((point) => point.label === "propaganda").vocabulary_id }).data;
  const moved = svc.applyExplorationViewAction(first.restore.map_id, { action: "MORE", expected_state_hash: first.restore.state_hash, template_id: first.restore.template_id, variant_id: first.restore.variant_id }).data;
  const restored = svc.retrieveExplorationView(moved.restore.map_id, moved.restore.state_id, moved.restore.template_id, moved.restore.variant_id).data;
  check(restored.svg === moved.svg && restored.restore.state_hash === moved.restore.state_hash, "a view restores byte-identically from map · state · template · variant");
  const again = svc.retrieveExplorationView(moved.restore.map_id, moved.restore.state_id, moved.restore.template_id, moved.restore.variant_id).data;
  check(again.svg === moved.svg && again.presentation.presentation_seed === moved.presentation.presentation_seed, "the same input renders the same bytes");
  const stale = svc.applyExplorationViewAction(first.restore.map_id, { action: "MORE", expected_state_hash: "0".repeat(64), template_id: first.restore.template_id, variant_id: first.restore.variant_id });
  check(!stale.ok && stale.code === "STALE_EXPLORATION_STATE", "a stale hash is refused");
  const otherMap = svc.applyExplorationViewAction("R16A-ENTRY-1922FEE2B602A64A22A0", { action: "MORE", expected_state_hash: first.restore.state_hash, template_id: first.restore.template_id, variant_id: first.restore.variant_id });
  check(!otherMap.ok, "a state cannot act on another map");
  const badTemplate = svc.retrieveExplorationView(moved.restore.map_id, moved.restore.state_id, "NOT_A_TEMPLATE", 0);
  check(!badTemplate.ok && badTemplate.code === "INVALID_PRESENTATION", "an unknown template fails closed, never a substitute drawing");
  const badVariant = svc.retrieveExplorationView(moved.restore.map_id, moved.restore.state_id, "DOTS", 9);
  check(!badVariant.ok && badVariant.code === "INVALID_PRESENTATION", "an unknown variant fails closed");
  const noPresentation = svc.retrieveExplorationView(moved.restore.map_id, moved.restore.state_id);
  check(noPresentation.ok && types.EXPLORATION_TEMPLATE_IDS.includes(noPresentation.data.presentation.template_id), "no presentation asked: the deterministic default");
  check(!svc.applyExplorationViewAction(first.restore.map_id, { action: "EXPAND_NODE", expected_state_hash: first.restore.state_hash, template_id: first.restore.template_id, variant_id: first.restore.variant_id }).ok, "raw V2 actions are not the view's controls");
}

/* --- E · every template × variant on 2 / 3 / 4-term views --- */
const field = types.VIEW_FRAME;
const sampleStates = [2, 3, 4].map((count) => {
  const longest = Object.values(model.states)
    .filter((state) => state.visible_node_ids.length === count)
    .sort((left, right) => right.visible_node_ids.reduce((sum, id) => sum + labelOf.get(id).length, 0) - left.visible_node_ids.reduce((sum, id) => sum + labelOf.get(id).length, 0))[0];
  return longest;
});
let scenes = 0;
for (const state of sampleStates) {
  for (const templateId of types.EXPLORATION_TEMPLATE_IDS) {
    const variants = types.EXPLORATION_TEMPLATE_VARIANTS[templateId];
    for (let variant = 0; variant < variants.length; variant += 1) {
      const view = svc.retrieveExplorationView(state.category_entry_id, state.state_id, templateId, variant);
      assert.ok(view.ok, `${templateId} ${variant} renders ${state.visible_node_ids.length} terms`);
      const scene = view.data.scene;
      assert.ok(!/NaN|undefined/.test(view.data.svg), `${templateId} ${variant}: no NaN in the SVG`);
      assert.equal(scene.nodes.length, state.visible_node_ids.length, `${templateId} ${variant}: one node per visible term`);
      assert.equal(scene.connectors.length, state.visible_association_ids.length, `${templateId} ${variant}: one connector per visible association`);
      for (const node of scene.nodes) {
        const box = node.region;
        assert.ok(box.width > 0 && box.height > 0, `${templateId} ${variant}: a term occupies a region`);
        assert.ok(box.x >= field.x - 1 && box.y >= field.y - 1 && box.x + box.width <= field.x + field.width + 1 && box.y + box.height <= field.y + field.height + 1, `${templateId} ${variant}: the term's motif is inside the field (${JSON.stringify(box)})`);
        assert.ok(node.anchor.x >= field.x && node.anchor.x <= field.x + field.width && node.anchor.y >= field.y && node.anchor.y <= field.y + field.height, `${templateId} ${variant}: the anchor is inside the field`);
      }
      assert.ok(scene.decorations.some((item) => item.role === "term"), `${templateId} ${variant}: terms are drawn`);
      if (scene.connectors.length > 0) assert.ok(scene.decorations.some((item) => item.role === "association") || templateId === "CROSSFIELD" || templateId === "HALFTONE", `${templateId} ${variant}: associations are drawn`);
      assert.ok(scene.connectors.every((c) => state.visible_association_ids.includes(c.associationId)), `${templateId} ${variant}: every connector is a visible V2 association — none fabricated`);
      assert.ok(!/<text/.test(view.data.svg), `${templateId} ${variant}: the view is pure graphic — no word`);
      assert.ok(view.data.svg.includes(`data-template="${templateId}"`) && view.data.svg.includes(`data-term="${state.visible_node_ids[0]}"`), `${templateId} ${variant}: the SVG names its template and terms`);
      assert.ok(view.data.svg.startsWith(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="${field.x} ${field.y} ${field.width} ${field.height}"`) && (scene.defs.some((d) => d.kind === "grain")) && view.data.svg.includes("feTurbulence"), `${templateId} ${variant}: the view is the full frame, with its grain`);
      assert.equal(scene.seedChain.length, 4, `${templateId} ${variant}: the seed chain is recorded`);
      const exported = svc.createExplorationViewExportManifest({ map_id: state.category_entry_id, state_hash: state.state_hash, composition_id: state.composition_id, template_id: templateId, variant_id: variant });
      assert.ok(exported.ok, `${templateId} ${variant}: the export manifest builds`);
      const formId = types.EXPLORATION_FORM_OF_TEMPLATE[templateId];
      assert.equal(exported.data.manifest.form_id, formId, `${templateId} ${variant}: the export takes the template's form`);
      const withFurniture = svc.renderExplorationExport(exported.data.scene, formId, exported.data.furniture);
      assert.ok(withFurniture.toLowerCase().includes(labelOf.get(model.compositions[state.composition_id].seed_node_id).toLowerCase()) && withFurniture.includes("MGDA") && withFurniture.includes(`data-form="${formId}"`), `${templateId} ${variant}: the export carries the form's furniture`);
      assert.ok(exported.data.scene.frame.x === forms.STAMP_FORMS[formId].image.x && exported.data.scene.frame.width === forms.STAMP_FORMS[formId].image.width, `${templateId} ${variant}: the export is laid out for the form's image area`);
      assert.ok(JSON.stringify(exported.data.scene.connectors.map((c) => [c.from, c.to, c.associationId])) === JSON.stringify(scene.connectors.map((c) => [c.from, c.to, c.associationId])) && exported.data.scene.presentationSeed === scene.presentationSeed, `${templateId} ${variant}: the export draws the same associations from the same seed`);
      scenes += 1;
    }
  }
}
check(scenes === 3 * 48, `one hundred and forty-four scenes laid out (${scenes})`);
check(types.EXPLORATION_TEMPLATE_IDS.length === 16 && types.EXPLORATION_TEMPLATE_IDS.every((id) => tpl.getCompatibleTemplates(tpl.sceneContentFromMap(svc.retrieveExplorationView(sampleStates[2].category_entry_id, sampleStates[2].state_id).data.map)).includes(id)), "all sixteen templates present a four-term view");
check(types.EXPLORATION_FORM_IDS.length === 5 && types.EXPLORATION_FORM_IDS.every((form) => types.EXPLORATION_TEMPLATE_IDS.filter((id) => types.EXPLORATION_FORM_OF_TEMPLATE[id] === form).length >= 3), "the five export forms each carry at least three templates");
/* the presentation is semantics-free: the same content in two palettes/templates keeps the same connectors */
{
  const a = svc.retrieveExplorationView(sampleStates[1].category_entry_id, sampleStates[1].state_id, "DOTS", 0).data;
  const b = svc.retrieveExplorationView(sampleStates[1].category_entry_id, sampleStates[1].state_id, "GRID", 2).data;
  check(JSON.stringify(a.scene.connectors.map((c) => [c.from, c.to, c.associationId])) === JSON.stringify(b.scene.connectors.map((c) => [c.from, c.to, c.associationId])), "template change keeps the associations");
  check(a.map.state.state_hash === b.map.state.state_hash && a.restore.state_id === b.restore.state_id, "template change keeps the research state");
  const templatesSource = read("src/features/trace-v49/exploration-view/templates.ts");
  const layouts = templatesSource.slice(templatesSource.indexOf("/* ================= 1 · DOTS"), templatesSource.indexOf("/* ---- the scene ---- */")).replace(/\/\*[\s\S]*?\*\//g, "");
  check(!/confidence|strength|support_status|HIGH|MODERATE|STRONG/i.test(a.svg) && !/confidence|strength|support_status|canonical_label|\.label\b|seedLabel/.test(layouts), "no confidence, strength or label reaches the layouts");
}
/* the PNG is the scene */
{
  const view = svc.retrieveExplorationView(sampleStates[2].category_entry_id, sampleStates[2].state_id, "CHEVRON", 0).data;
  const manifest = svc.createExplorationViewExportManifest({ map_id: view.restore.map_id, state_hash: view.restore.state_hash, composition_id: view.map.composition.composition_id, template_id: "CHEVRON", variant_id: 0 });
  check(manifest.ok && manifest.data.manifest.export_id.startsWith("TEP1-") && manifest.data.manifest.render_version === "trace-exploration-stamp-png-v1" && manifest.data.manifest.template_id === "CHEVRON" && manifest.data.manifest.form_id === "GERMANY" && manifest.data.manifest.seed_chain.length === 4, "the export manifest carries the presentation identity, its form and its seed chain");
  check(manifest.data.scene.presentationSeed === view.scene.presentationSeed && manifest.data.scene.seedChain.slice(0, 3).join("|") === view.scene.seedChain.slice(0, 3).join("|") && manifest.data.scene.frame.width === forms.STAMP_FORMS.GERMANY.image.width, "the export scene is the page's scene — same seed, same skeleton — laid out for the form's image area");
  const png = await renderServer.renderExplorationScenePng(manifest.data.scene, "GERMANY", manifest.data.furniture);
  const meta = await sharp(png).metadata();
  check(meta.width === manifest.data.manifest.dimensions.width && meta.height === manifest.data.manifest.dimensions.height && meta.width === forms.STAMP_FORMS.GERMANY.width * forms.EXPORT_SCALE, `the PNG is ${forms.EXPORT_SCALE} × the form's size (${meta.width} × ${meta.height})`);
  const wrongComposition = svc.createExplorationViewExportManifest({ map_id: view.restore.map_id, state_hash: view.restore.state_hash, composition_id: "R16A-PCOMP-0032182383B75CA3BAD2", template_id: "CHEVRON", variant_id: 0 });
  check(!wrongComposition.ok, "an export cannot re-select a composition");
  check(!/state_hash|[0-9a-f]{64}/.test(manifest.data.furniture.map((item) => item.text).join(" ")) && !/<text/.test(view.svg), "no hash is printed on the stamp; the view carries no word");
}

/* --- E1 · the picture is the largest thing on every form: its image area spans at least 80 % of the paper's width or height --- */
for (const formId of types.EXPLORATION_FORM_IDS) {
  const form = forms.STAMP_FORMS[formId];
  const share = Math.max(form.image.width / form.sheet.width, form.image.height / form.sheet.height);
  check(share >= 0.8, `${formId}: the image area spans ${Math.round(share * 100)} % of the paper's ${form.image.width / form.sheet.width >= form.image.height / form.sheet.height ? "width" : "height"} (≥ 80 %)`);
}

/* --- E2 · the export's furniture: every line measured, inside the paper, off the picture, off the frame line, off every other line ---
   on every distinct picture (visible terms + associations) × every form, so the longest labels are covered */
{
  const overlaps = (a, b, tolerance = 0) => a.x < b.x + b.width - tolerance && a.x + a.width > b.x + tolerance && a.y < b.y + b.height - tolerance && a.y + a.height > b.y + tolerance;
  const inside = (a, b, tolerance = 2) => a.x >= b.x - tolerance && a.y >= b.y - tolerance && a.x + a.width <= b.x + b.width + tolerance && a.y + a.height <= b.y + b.height + tolerance;
  const pictures = new Map();
  for (const state of Object.values(model.states)) {
    const key = [...state.visible_node_ids].sort().join(",") + "|" + [...state.visible_association_ids].sort().join(",");
    if (!pictures.has(key)) pictures.set(key, state);
  }
  let layouts = 0;
  const faults = [];
  for (const state of pictures.values()) {
    for (const formId of types.EXPLORATION_FORM_IDS) {
      const templateId = types.EXPLORATION_TEMPLATE_IDS.find((id) => types.EXPLORATION_FORM_OF_TEMPLATE[id] === formId);
      const exported = svc.createExplorationViewExportManifest({ map_id: state.category_entry_id, state_hash: state.state_hash, composition_id: state.composition_id, template_id: templateId, variant_id: 0 });
      assert.ok(exported.ok, `${formId} export for ${state.state_id}`);
      const form = forms.STAMP_FORMS[formId];
      const boxes = exported.data.furniture.map((item) => ({ item, box: forms.textBox(item) }));
      layouts += 1;
      for (let i = 0; i < boxes.length; i += 1) {
        const { item, box } = boxes[i];
        const where = `${formId} ${state.state_id} "${item.text.slice(0, 40)}"`;
        if (!inside(box, form.sheet)) faults.push(`${where} leaves the paper`);
        for (const block of form.boxes.filter((b) => b.fill)) if (overlaps(box, block.box) && !inside(box, block.box, 3)) faults.push(`${where} spills out of its block`);
        if (!form.furnitureOverImage && overlaps(box, form.image, 1)) faults.push(`${where} stands on the picture`);
        if (form.frame) {
          const f = form.frame.box;
          const wholly = inside(box, { x: f.x + form.frame.stroke, y: f.y + form.frame.stroke, width: f.width - form.frame.stroke * 2, height: f.height - form.frame.stroke * 2 }, 0);
          const apart = !overlaps(box, { x: f.x - 1, y: f.y - 1, width: f.width + 2, height: f.height + 2 });
          if (!wholly && !apart) faults.push(`${where} crosses the frame line`);
        }
        for (let j = i + 1; j < boxes.length; j += 1) if (overlaps(box, boxes[j].box, 1)) faults.push(`${where} overlaps "${boxes[j].item.text.slice(0, 40)}"`);
      }
    }
  }
  check(faults.length === 0, `${layouts} export layouts (${pictures.size} distinct pictures × ${types.EXPLORATION_FORM_IDS.length} forms): every furniture line inside the paper, off the picture, off the frame line and off every other line${faults.length ? ` — ${faults.slice(0, 6).join("; ")}${faults.length > 6 ? ` (+${faults.length - 6})` : ""}` : ""}`);
}

/* --- F · the frozen v2 is untouched and still replays its sealed ledger --- */
for (const file of ["renderer.server.ts", "controller.server.ts", "service.server.ts", "derive.server.ts", "transition.server.ts", "read-model.server.ts", "types.ts", "theme-tokens.ts", "client.ts"]) {
  const head = execFileSync("git", ["show", `HEAD:frontend/src/features/trace-v49/exploration-v2/${file}`], { cwd: repoRoot });
  check(createHash("sha256").update(head).digest("hex") === createHash("sha256").update(readFileSync(join(frontendRoot, "src/features/trace-v49/exploration-v2", file))).digest("hex"), `frozen v2 ${file} is byte-identical to HEAD`);
}
{
  const ledger = readFileSync(join(repoRoot, "docs/audits/v49-exploration-full-space-closure-round1/raw/api-v2-export-case-ledger.tsv"), "utf8").trim().split("\n");
  const header = ledger[0].split("\t");
  const rows = ledger.slice(1, 4).map((line) => Object.fromEntries(line.split("\t").map((value, index) => [header[index], value])));
  for (const row of rows) {
    const state = model.states[row.state_id];
    const manifest = v2.createExplorationV2ExportManifest({ map_id: state.category_entry_id, state_hash: row.state_hash, composition_id: state.composition_id, export_preset: row.export_preset, theme_token_set: row.theme_token_set });
    check(manifest.ok && manifest.data.export_id === row.export_id && manifest.data.presentation_hash === row.presentation_hash, `sealed export ${row.export_id} still replays`);
  }
}

/* --- G · the release boundary in the page --- */
const page = read("src/app/trace/exploration/page.tsx");
const desktopDir = join(frontendRoot, "src/app/trace/exploration/desktop");
const desktop = readdirSync(desktopDir).filter((name) => name.endsWith(".tsx")).map((name) => readFileSync(join(desktopDir, name), "utf8")).join("\n");
const rail = read("src/app/trace/exploration/desktop/ExplorationRail.tsx");
const inquiry = read("src/app/trace/exploration/desktop/InquiryDrawer.tsx");
const description = read("src/app/trace/exploration/desktop/DescriptionDrawer.tsx");
const desktopShell = read("src/app/trace/exploration/desktop/ExplorationDesktop.tsx");
const stage = read("src/app/trace/exploration/desktop/Stage.tsx");
check(!/exploration-v3|exploration\/backend|TraceExplorationReference/.test(page + desktop), "the page reads neither V3 nor the reference view");
check(page.indexOf("isLikelyMobileTraceRequest") < page.indexOf("await Promise.all"), "the mobile boundary comes before any runtime import");
check(!/FOCUS_NODE|MOVE_FOCUS|EXPAND_NODE|COLLAPSE_NODE|SELECT_COMPOSITION|Promote|Add to view|Explore connection|Draw edge|Remove node/.test(desktop), "no raw V2 action or graph editing reaches the UI");
check(rail.indexOf("exploration-start-heading") < rail.indexOf("exploration-complexity-heading") && rail.indexOf("exploration-complexity-heading") < rail.indexOf("exploration-another-heading") && rail.indexOf("exploration-another-heading") < rail.indexOf("exploration-export-heading") && rail.indexOf("exploration-export-heading") < rail.indexOf("exploration-inquiry-heading"), "the rail keeps the owner's order, Open Inquiry last");
{
  const choosing = rail.slice(rail.indexOf("if (choosing)"), rail.indexOf("return (\n    <div className={styles.rail} data-state=\"normal\">"));
  check(choosing.includes("CHOOSER_CLOSE") && choosing.includes('aria-current="true"') && choosing.includes("CURRENT") && !choosing.includes("exploration-complexity-heading") && !choosing.includes("exploration-another-heading") && !choosing.includes("exploration-export-heading") && !choosing.includes("exploration-inquiry-heading"), "the selection state is one task: keep-current, the current word marked and no candidate, the other controls hidden");
  const railCss = read("src/app/trace/exploration/desktop/ExplorationRail.module.css");
  check(railCss.includes(".wordCurrent") && railCss.includes('.word:hover:not(:disabled)') && railCss.includes(".word:focus-visible") && railCss.includes(".word:disabled"), "current, hover, keyboard-focus and disabled states are styled apart");
  check(!/About this view|ABOUT_CLOSE|\bABOUT\b/.test(desktop + read("src/app/trace/exploration/lib/content.ts")), "About this view is renamed Description everywhere");
  check(desktopShell.includes('useState<Drawer>("description")') && desktopShell.includes("closedByReader"), "Description opens by default and the reader's closing is respected");
  const order = ['aria-label="System suggests"', 'id="exploration-shown-heading"', 'id="exploration-presentation-heading"', "<summary>{PROVENANCE}</summary>"].map((marker) => description.indexOf(marker));
  check(order.every((index, i) => index >= 0 && (i === 0 || index > order[i - 1])), "DESCRIPTION → SYSTEM SUGGESTS → WHAT IS SHOWN → PRESENTATION → TECHNICAL PROVENANCE");
  check(description.includes("maxActions={0}") && description.includes("reference={reference}") && !description.includes("validActionIds"), "the validated narration is narration only and names its state rather than describing its facts");
  check(description.includes("item.endpoint_labels[0]} — {item.endpoint_labels[1]}") && description.includes("VISIBLE_TERMS(terms.length)") && !description.includes("ordered.join"), "WHAT IS SHOWN lists the counts and the exact association pairs, once");
  check(description.includes("SUGGESTS_BOUNDARY") && description.indexOf("SUGGESTS_BOUNDARY}") > description.indexOf('aria-label="System suggests"') && description.indexOf("SUGGESTS_BOUNDARY}") < description.indexOf('id="exploration-shown-heading"'), "the fixed boundary sits once under the narration");
  check(!/relationForm/.test(inquiry.slice(inquiry.indexOf("return ("), inquiry.indexOf("<details"))) && /Technical provenance|INQUIRY_PROVENANCE/.test(inquiry), "the inquiry's relation form leaves the surface for Technical provenance");
  check(!/hyperedge|incidence|reroute|governed inquiry/i.test(read("src/app/trace/exploration/lib/content.ts")), "no internal research language in the copy");
  check(read("src/app/trace/exploration/desktop/Drawer.module.css").includes(".suggestsCard"), "System suggests has its own bounded container");
}
check(inquiry.indexOf("OPEN_INQUIRY_DISCLOSURE[0]") < inquiry.indexOf("OPEN_INQUIRY_DISCLOSURE[1]") && inquiry.indexOf("OPEN_INQUIRY_DISCLOSURE[1]") < inquiry.indexOf("OPEN_INQUIRY_DISCLOSURE[2]") && inquiry.indexOf("OPEN_INQUIRY_DISCLOSURE[2]") < inquiry.indexOf("SystemSuggestionsPanel surface"), "the inquiry drawer discloses in order before any content or guidance");
check(!stage.includes("SystemSuggestionsPanel") && !rail.includes("SystemSuggestionsPanel") && description.includes('surface="TRACE_VALIDATED_EXPLORATION"') && inquiry.includes('surface="TRACE_OPEN_INQUIRY"'), "System suggests lives only in the drawers");
check((inquiry.match(/maxActions=\{1\}/g) ?? []).length === 1, "the inquiry narration offers at most one action");
check(!/state_hash|semantic_hash|presentation_hash|confidence|strength/.test(description.slice(description.indexOf("return ("), description.indexOf("<details"))), "no hash, confidence or strength on the description's surface");
check(!stage.includes("<button") && stage.includes("dangerouslySetInnerHTML={{ __html: view.svg }}"), "the stage shows the server's SVG and carries no control");
check(read("src/app/trace/lib/content.ts").includes("deferred: true"), "Spacetime stays deferred");
check(!read("src/app/trace/exploration/desktop/ExplorationDesktop.tsx").includes("context-canvas/desktop"), "Context Canvas is not touched");

/* --- H · the narration gate (release pass: the server's facts, the model's wording) --- */
{
  const { resetGuidanceCacheForTest } = await jiti.import(join(frontendRoot, "src/features/system-suggestions/cache.server.ts"));
  const { resolveSystemSuggestionsFactsForTest } = await jiti.import(join(frontendRoot, "src/features/system-suggestions/service.server.ts"));
  const { listOpenInquiries } = await jiti.import(join(frontendRoot, "src/features/trace-v49/open-inquiry-v1/service.server.ts"));
  const environment = { SYSTEM_SUGGESTIONS_PROVIDER: "deepseek", DEEPSEEK_API_KEY: "test-key" };
  const providerWith = (note, ids, used = []) => async () => new Response(JSON.stringify({ status: "completed", output: [{ type: "message", role: "assistant", content: [{ type: "output_text", text: JSON.stringify({ note, used_fact_ids: used, suggestion_ids: ids }) }] }] }), { status: 200, headers: { "Content-Type": "application/json" } });
  const ask = async (request, note, ids = [], used = []) => { resetGuidanceCacheForTest(); return createSystemSuggestions(request, { environment, fetchImpl: providerWith(note, ids, used) }); };
  /* the three-term chain: design diplomacy's ladder at S3 */
  const s3 = sampleStates[1];
  const validated = { schemaVersion: "gda-system-suggestions-request/v2", surface: "TRACE_VALIDATED_EXPLORATION", reference: { mapId: s3.category_entry_id, stateId: s3.state_id } };
  const { facts } = resolveSystemSuggestionsFactsForTest(validated);
  const seed = facts.seedLabel;
  const others = facts.labels.filter((label) => label !== seed);
  const cap = (value) => value.charAt(0).toUpperCase() + value.slice(1);
  const pair = facts.pairs[0];
  const unpaired = (() => { for (const a of facts.labels) for (const b of facts.labels) if (a !== b && !facts.pairs.some((p) => (p.a === a && p.b === b) || (p.a === b && p.b === a))) return [a, b]; return null; })();
  check(facts.labels.length === 3 && facts.pairs.length === 2 && unpaired !== null, `S3 is a three-term chain with one unpaired couple (${unpaired?.join(" / ")})`);
  const good = await ask(validated, `In this view, ${pair.a} is paired with ${pair.b}.`, [], ["E3"]);
  check(good.sourceClass === "MODEL" && good.suggestions.length === 0 && good.usedFactIds.join() === "E3" && good.contextFingerprint === facts.contextFingerprint, "a pairing the view shows passes the gate, narration only, with its fact id");
  const statics = await ask(validated, `${cap(seed)} is shown here alongside ${others.join(" and ")} through two evidence-qualified generic associations. The view invites these terms to be read together without asserting influence, sequence or causation.`);
  check(statics.sourceClass === "MODEL", "the owner's upper-limit narration (co-visibility plus a denial) passes the gate");
  for (const [label, note] of [
    ["influence", `${cap(pair.a)} influenced ${pair.b}.`],
    ["star from a chain", `${cap(seed)} is paired with ${others.join(" and ")}.`],
    ["pair not shown", `In this view, ${unpaired[0]} is paired with ${unpaired[1]}.`],
    ["transitive", `${cap(unpaired[0])} is linked to ${unpaired[1]} through ${facts.labels.find((l) => !unpaired.includes(l))}.`],
    ["source count", `In this view, ${pair.a} is paired with ${pair.b} by one source.`],
    ["weak", `In this view, ${pair.a} is weakly paired with ${pair.b}.`],
    ["similarity", `${cap(pair.a)} and ${pair.b} are semantically similar here.`],
    ["progression", `This suggests a progression from ${pair.a} to ${pair.b}.`],
    ["confidence", "These associations carry high confidence."],
    ["three sentences", `${cap(pair.a)} is shown with ${pair.b}. ${cap(seed)} is shown too. Both are qualified.`],
    ["percentage", `${cap(pair.a)} carries 50% of the associations here.`],
    ["number", `${cap(pair.a)} is shown with 7 other terms.`],
    ["history", `${cap(pair.a)} appears with ${pair.b} in the twentieth century.`],
    ["unknown fact", null],
  ]) {
    const response = note === null ? await ask(validated, `In this view, ${pair.a} is paired with ${pair.b}.`, [], ["E9"]) : await ask(validated, note);
    check(response.sourceClass === "STATIC_FALLBACK" && response.providerStatus === "INVALID_RESPONSE", `${label} falls back to the deterministic narration (${response.providerStatus})`);
    check(response.note === `${cap(seed)} is shown here alongside ${others.join(" and ")} through two evidence-qualified generic associations.`, `${label}: the fallback narrates the visible structure`);
  }
  const single = sampleStates[0];
  const s2 = resolveSystemSuggestionsFactsForTest({ schemaVersion: "gda-system-suggestions-request/v2", surface: "TRACE_VALIDATED_EXPLORATION", reference: { mapId: single.category_entry_id, stateId: single.state_id } }).facts;
  const s2Fallback = await createSystemSuggestions({ schemaVersion: "gda-system-suggestions-request/v2", surface: "TRACE_VALIDATED_EXPLORATION", reference: { mapId: single.category_entry_id, stateId: single.state_id } }, { environment: { SYSTEM_SUGGESTIONS_PROVIDER: "static" } });
  check(s2Fallback.note === `In this view, ${s2.pairs[0].a} is paired with ${s2.pairs[0].b}.` && s2Fallback.suggestions.length === 0, "a single pair narrates as one direct sentence");
  await assert.rejects(() => createSystemSuggestions({ ...validated, shown: { qualifiedAssociations: 5 } }, { environment: { SYSTEM_SUGGESTIONS_PROVIDER: "static" } }), (error) => error.code === "INVALID_ARGUMENT");
  checks += 1;
  /* the inquiry: the registry's own participants and scope */
  const inquiry = listOpenInquiries().data.data.items[0];
  const inquiryRequest = { schemaVersion: "gda-system-suggestions-request/v2", surface: "TRACE_OPEN_INQUIRY", reference: { inquiryId: inquiry.inquiry_id } };
  const participants = inquiry.participants.map((item) => item.label);
  const list = `${participants.slice(0, -1).join(", ")} and ${participants[participants.length - 1]}`;
  const inquiryGood = await ask(inquiryRequest, `This inquiry considers a bounded question between ${list}; the current evidence does not qualify it for the validated graph.`, ["trace-trace-open-inquiry-return-to-exploration"]);
  check(inquiryGood.sourceClass === "MODEL" && inquiryGood.suggestions.length === 1, "a bounded inquiry description with one reading action passes");
  const inquiryBad = await ask(inquiryRequest, `${cap(participants[0])} may have influenced ${participants[1]}.`);
  check(inquiryBad.sourceClass === "STATIC_FALLBACK" && inquiryBad.note.startsWith(`This open inquiry considers a bounded question between ${list}.`), "an inquiry phrased as an association falls back to the registry's own words");
  const inquiryValidated = await ask(inquiryRequest, `${cap(participants[0])} and ${participants[1]} form a validated association.`);
  check(inquiryValidated.sourceClass === "STATIC_FALLBACK", "an inquiry framed as validated falls back");
  check(openInquiryFallbackNote({ labels: [] }) === "This inquiry remains outside the validated graph because its evidence is incomplete." && explorationFallbackNote({ labels: ["a", "b"], counts: { visibleTerms: 2, qualifiedAssociations: 1 } }).startsWith("A is shown here alongside b"), "the v1 deterministic narrations are kept for the frozen reference contexts");
  const legacy = await createSystemSuggestions({ schemaVersion: "gda-system-suggestions-request/v1", surface: "TRACE_VALIDATED_EXPLORATION", stateHash: "a".repeat(64), context: { stateType: "EXPLORATION_VIEW_AXIS", labels: ["x"], counts: { validatedCompositions: 0 }, validActionIds: ["RETURN_TO_COMPOSITION"], evidenceClass: "VALIDATED" } }, { environment: { SYSTEM_SUGGESTIONS_PROVIDER: "static" } });
  check(legacy.note.startsWith("No validated composition is active") && legacy.providerStatus === "LEGACY_CONTEXT_STATIC", "the legacy reference context keeps its own fallback and never reaches a model");
}

console.log(`EXPLORATION_VIEW_V1=PASS CHECKS=${checks} STATES=${Object.keys(model.states).length} MORE_STATES=${moreStates} LESS_STATES=${lessStates} LESS_STATES_WHOSE_SMALLEST_STEP_REMOVES_TWO=${lessByTwo} SCENES=${scenes}`);
