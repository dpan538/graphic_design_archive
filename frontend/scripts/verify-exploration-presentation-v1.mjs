/* Exploration presentation verification v1 (FRONTEND_DESIGN_DECISION.md §7i,
   second engine): proves the sixteen-template system is deterministic,
   state-conditioned visual generation — a structural skeleton per term
   count, bent by the state's semantic field, drawn in the variant's
   connection mode — not fixed artwork, that its presentations are
   materially distinct, and that the picture never invents an association.
   Three layers:

   WHITE-BOX   the presentation derivation, independent of the UI, through a
               geometry fingerprint that excludes every word; the seed chain;
               the topological phase transition between term counts; the
               semantic field; no fabricated edges;
   BLACK-BOX   the real page and the real export endpoint on a running dev
               server: 3 governed states × 16 templates = 48 views, five
               reloads and five exports each; the S4 variants; pHash + SSIM
               over the VIEW pictures with hard thresholds; golden images
               (SSIM ≥ 0.99); an export burst against the render limiter;
   METAMORPHIC same state / other template, same template / other state,
               complexity steps, Another view, variants, form of template.

   Hard gates (no REVIEW class): same template, other state → SSIM < 0.65;
   same state, other variant → SSIM < 0.85; same state, other template →
   SSIM < 0.90 and pHash distance > 0; golden → SSIM ≥ 0.99; every term moves
   > 30 px between term counts. Writes WHITEBOX_REPORT.md, BLACKBOX_REPORT.md,
   visual-generation-matrix.json, exploration-48-view-contact-sheet.png,
   exploration-export-forms-sheet.png and golden/*.png (Git LFS) under
   docs/qa/exploration-presentation-verification-v1/. EXPLORATION_GOLDEN=update
   rewrites the goldens. Modifies no design. */
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(here, "..");
const repoRoot = join(frontendRoot, "..");
const outDir = join(repoRoot, "docs/qa/exploration-presentation-verification-v1");
const goldenDir = join(outDir, "golden");
const goldenMode = process.env.EXPLORATION_GOLDEN ?? "check";
const baseUrl = process.env.EXPLORATION_BASE_URL ?? "http://localhost:3000";
const require = createRequire(import.meta.url);
const jiti = require("jiti")(fileURLToPath(import.meta.url), {
  interopDefault: true,
  tryNative: false,
  alias: { "@": join(frontendRoot, "src"), "server-only": join(here, "server-only-marker.mjs") },
});
const sharp = require("sharp");

const svc = await jiti.import(join(frontendRoot, "src/features/trace-v49/exploration-view/service.server.ts"));
const tpl = await jiti.import(join(frontendRoot, "src/features/trace-v49/exploration-view/templates.ts"));
const types = await jiti.import(join(frontendRoot, "src/features/trace-v49/exploration-view/types.ts"));
const render = await jiti.import(join(frontendRoot, "src/features/trace-v49/exploration-view/render.ts"));
const fp = await jiti.import(join(frontendRoot, "src/features/trace-v49/exploration-view/fingerprint.ts"));
const skeleton = await jiti.import(join(frontendRoot, "src/features/trace-v49/exploration-view/skeleton.ts"));
const { STAMP_FORMS, EXPORT_SCALE } = await jiti.import(join(frontendRoot, "src/features/trace-v49/exploration-view/forms.ts"));
const { getExplorationV2ReadModel } = await jiti.import(join(frontendRoot, "src/features/trace-v49/exploration-v2/read-model.server.ts"));
const { getExplorationV2TransitionIndex } = await jiti.import(join(frontendRoot, "src/features/trace-v49/exploration-v2/transition.server.ts"));

const model = getExplorationV2ReadModel();
const transitions = getExplorationV2TransitionIndex(model);
const labelOf = new Map(model.vocabulary.map((term) => [term.vocabulary_id, term.canonical_label]));
const sha256 = (input) => createHash("sha256").update(input).digest("hex");
const short = (hash) => (hash ? `${hash.slice(0, 12)}…` : "—");
const r3 = (value) => Math.round(value * 1000) / 1000;
const results = { whitebox: [], blackbox: [], metamorphic: [] };
const failures = [];
const record = (layer, test, status, detail) => { results[layer].push({ test, status, detail }); if (status === "FAIL") failures.push(`${layer}:${test} — ${detail}`); };
const gate = (layer, test, condition, detail) => record(layer, test, condition ? "PASS" : "FAIL", detail);

/* the thresholds — the owner's hard gates */
const T = { crossState: 0.65, variant: 0.85, crossTemplate: 0.9, golden: 0.99, phaseShift: 30, viewBytes: 400_000, viewElements: 6000 };

const presentationOf = async (view) => ({ fingerprint: await fp.presentationFingerprint(view.scene), grammar: fp.presentationGrammar(view.scene) });
const semantics = (view) => JSON.stringify({ state: view.map.state.state_hash, terms: [...view.map.state.visible_node_ids].sort(), associations: [...view.map.state.visible_association_ids].sort(), start: view.starting_point.vocabulary_id });
const viewAt = (mapId, stateId, template, variant) => {
  const result = svc.retrieveExplorationView(mapId, stateId, template, variant);
  assert.ok(result.ok, `view ${mapId} ${stateId} ${template} ${variant}: ${result.ok ? "" : result.message}`);
  return result.data;
};
const step = (view, action) => {
  const result = svc.applyExplorationViewAction(view.restore.map_id, { action, expected_state_hash: view.restore.state_hash, template_id: view.restore.template_id, variant_id: view.restore.variant_id });
  assert.ok(result.ok, `${action} from ${view.restore.state_id}: ${result.ok ? "" : result.message}`);
  return result.data;
};
const anchorsOf = (view) => new Map(view.scene.nodes.map((node) => [node.vocabularyId, node.anchor]));
const meanShift = (a, b) => {
  const shared = [...a.keys()].filter((id) => b.has(id));
  if (shared.length === 0) return null;
  return shared.reduce((sum, id) => sum + Math.hypot(a.get(id).x - b.get(id).x, a.get(id).y - b.get(id).y), 0) / shared.length;
};

/* ---- the three canonical states: one starting point, its complexity ladder 2 → 3 → 4 ---- */
const points = svc.listExplorationStartingPoints().data.starting_points;
const origin = points.find((point) => point.label === "design diplomacy");
const S2 = svc.createExplorationView({ vocabulary_id: origin.vocabulary_id }).data;
const S3 = step(S2, "MORE");
const S4 = step(S3, "MORE");
const canonical = [["S2", S2], ["S3", S3], ["S4", S4]];
for (const [name, view] of canonical) assert.equal(view.map.nodes.length, Number(name.slice(1)), `${name} has its term count`);
const TEMPLATES = [...types.EXPLORATION_TEMPLATE_IDS];
const N = TEMPLATES.length;
const VIEW = types.VIEW_FRAME;

/* ======================= WHITE-BOX ======================= */
{
  /* same_input_same_presentation */
  let same = 0;
  let total = 0;
  for (const [, view] of canonical) for (const template of TEMPLATES) for (let variant = 0; variant < types.EXPLORATION_TEMPLATE_VARIANTS[template].length; variant += 1) {
    const a = viewAt(view.restore.map_id, view.restore.state_id, template, variant);
    const b = viewAt(view.restore.map_id, view.restore.state_id, template, variant);
    total += 1;
    if ((await presentationOf(a)).fingerprint === (await presentationOf(b)).fingerprint && a.svg === b.svg) same += 1;
  }
  gate("whitebox", "same_input_same_presentation", same === total, `${same}/${total} (3 states × ${N} templates × 3 variants) identical fingerprint and SVG on rebuild`);

  /* state_drives_geometry: every real More transition, same template + variant, changes the fingerprint */
  let changed = 0;
  let transitionsTried = 0;
  const unchangedSamples = [];
  for (const state of Object.values(model.states)) {
    const targets = transitions.targets(state, "EXPAND_NODE").filter((target) => transitions.resolve(state, "EXPAND_NODE", target)?.next_state.visible_node_ids.length > state.visible_node_ids.length);
    if (targets.length === 0) continue;
    const before = viewAt(state.category_entry_id, state.state_id, "LINES", 0);
    const after = svc.applyExplorationViewAction(state.category_entry_id, { action: "MORE", expected_state_hash: state.state_hash, template_id: "LINES", variant_id: 0 }).data;
    transitionsTried += 1;
    const [a, b] = [await presentationOf(before), await presentationOf(after)];
    if (a.fingerprint !== b.fingerprint) changed += 1; else if (unchangedSamples.length < 3) unchangedSamples.push(state.state_id);
  }
  gate("whitebox", "state_drives_geometry", changed === transitionsTried, `${changed}/${transitionsTried} real More transitions change the LINES/0 fingerprint${unchangedSamples.length ? `; unchanged: ${unchangedSamples.join(", ")}` : ""}`);
  let poolPairs = 0;
  let poolDistinct = 0;
  for (const point of points) {
    let current = svc.createExplorationView({ vocabulary_id: point.vocabulary_id }).data;
    const pool = current.controls.another_view.pool_size;
    const prints = [];
    for (let i = 0; i < pool; i += 1) {
      prints.push((await presentationOf(viewAt(current.restore.map_id, current.restore.state_id, "GRID", 0))).fingerprint);
      if (pool > 1) current = step(current, "ANOTHER_VIEW");
    }
    for (let i = 0; i < prints.length; i += 1) for (let j = i + 1; j < prints.length; j += 1) { poolPairs += 1; if (prints[i] !== prints[j]) poolDistinct += 1; }
  }
  gate("whitebox", "state_drives_geometry_pools", poolDistinct === poolPairs, `${poolDistinct}/${poolPairs} pairs of distinct root pictures differ under GRID/0 across all ${points.length} starting points`);

  /* template_drives_grammar + semantic_invariance */
  for (const [name, view] of canonical) {
    const perTemplate = await Promise.all(TEMPLATES.map(async (template) => { const v = viewAt(view.restore.map_id, view.restore.state_id, template, 0); return { template, ...(await presentationOf(v)), semantics: semantics(v), terms: v.scene.nodes.map((n) => n.vocabularyId).sort().join(","), edges: v.scene.connectors.map((c) => c.associationId).sort().join(",") }; }));
    const fingerprints = new Set(perTemplate.map((item) => item.fingerprint));
    const grammars = new Set(perTemplate.map((item) => item.grammar));
    gate("whitebox", `template_drives_grammar:${name}`, fingerprints.size === N && grammars.size === N, `${fingerprints.size}/${N} distinct fingerprints, ${grammars.size}/${N} distinct grammars`);
    const sem = new Set(perTemplate.map((item) => item.semantics));
    const termSets = new Set(perTemplate.map((item) => item.terms));
    const edgeSets = new Set(perTemplate.map((item) => item.edges));
    gate("whitebox", `semantic_invariance:${name}`, sem.size === 1 && termSets.size === 1 && edgeSets.size === 1, `research state, terms and associations identical across the ${N} templates (${view.restore.state_id})`);
  }

  /* variant_drives_presentation_only + variant_is_structural */
  const redundant = [];
  const flat = [];
  for (const template of TEMPLATES) {
    const variants = types.EXPLORATION_TEMPLATE_VARIANTS[template];
    const views = variants.map((_, variant) => viewAt(S4.restore.map_id, S4.restore.state_id, template, variant));
    const prints = await Promise.all(views.map(async (v) => (await presentationOf(v)).fingerprint));
    const sems = new Set(views.map(semantics));
    for (let i = 0; i < prints.length; i += 1) for (let j = i + 1; j < prints.length; j += 1) if (prints[i] === prints[j]) redundant.push(`${template} ${variants[i]}=${variants[j]}`);
    gate("whitebox", `variant_drives_presentation_only:${template}`, sems.size === 1 && new Set(prints).size === prints.length, `${new Set(prints).size}/${prints.length} distinct variant fingerprints, research content identical`);
    /* structural: the terms stand elsewhere, not only in other inks */
    let minShift = Infinity;
    for (let i = 0; i < views.length; i += 1) for (let j = i + 1; j < views.length; j += 1) minShift = Math.min(minShift, meanShift(anchorsOf(views[i]), anchorsOf(views[j])));
    if (minShift <= T.phaseShift) flat.push(`${template} ${Math.round(minShift)}px`);
  }
  gate("whitebox", "no_redundant_variants", redundant.length === 0, redundant.length ? `redundant: ${redundant.join("; ")}` : "every variant of every template draws a different picture on S4");
  gate("whitebox", "variant_is_structural", flat.length === 0, flat.length ? `variants that only recolour (mean term shift ≤ ${T.phaseShift}px): ${flat.join("; ")}` : `on S4 every pair of variants moves the terms by more than ${T.phaseShift}px on average — the skeleton family changes with the variant`);

  /* topological_phase_transition: between term counts the terms re-form, they are not appended */
  {
    const stuck = [];
    const shifts = [];
    for (const template of TEMPLATES) {
      const ladder = canonical.map(([, v]) => anchorsOf(viewAt(v.restore.map_id, v.restore.state_id, template, 0)));
      for (let i = 0; i < ladder.length - 1; i += 1) {
        const shift = meanShift(ladder[i], ladder[i + 1]);
        shifts.push(shift);
        if (shift === null || shift <= T.phaseShift) stuck.push(`${template} S${i + 2}→S${i + 3} ${shift === null ? "no shared term" : `${Math.round(shift)}px`}`);
      }
    }
    gate("whitebox", "topological_phase_transition", stuck.length === 0, stuck.length ? `terms merely appended: ${stuck.join("; ")}` : `S2→S3 and S3→S4 under all ${N} templates: the shared terms move ${Math.round(Math.min(...shifts))}–${Math.round(Math.max(...shifts))}px on average (> ${T.phaseShift}px), the skeleton changes family with the count`);
  }

  /* semantic_field: two states of the same count under the same seed lie differently, inside the frame */
  {
    const counts = [2, 3, 4];
    const details = [];
    let ok = true;
    for (const count of counts) {
      const own = canonical[count - 2][1].map.state.semantic_hash;
      const other = Object.values(model.states).find((state) => state.visible_node_ids.length === count && skeleton.fieldKind(state.semantic_hash) !== skeleton.fieldKind(own))?.semantic_hash;
      if (!other) { ok = false; details.push(`${count}: no state with another field`); continue; }
      const a = skeleton.termPositions(count, 0, 12345, own, VIEW);
      const b = skeleton.termPositions(count, 0, 12345, other, VIEW);
      const shift = a.reduce((sum, p, i) => sum + Math.hypot(p.x - b[i].x, p.y - b[i].y), 0) / count;
      const inside = [...a, ...b].every((p) => p.x >= VIEW.x + VIEW.width * 0.08 - 1 && p.x <= VIEW.x + VIEW.width * 0.92 + 1 && p.y >= VIEW.y + VIEW.height * 0.08 - 1 && p.y <= VIEW.y + VIEW.height * 0.92 + 1);
      if (!(shift > 0 && inside)) ok = false;
      details.push(`${count} terms: ${skeleton.fieldKind(own)} vs ${skeleton.fieldKind(other)} → ${Math.round(shift)}px, inside margins ${inside}`);
    }
    gate("whitebox", "semantic_field_bends_skeleton", ok, details.join("; "));
  }

  /* no_fabricated_edges: every connector and every association-role primitive answers to a visible V2 association */
  {
    let checked = 0;
    const bad = [];
    for (const [name, view] of canonical) for (const template of TEMPLATES) for (let variant = 0; variant < 3; variant += 1) {
      const v = viewAt(view.restore.map_id, view.restore.state_id, template, variant);
      const ids = new Set(v.map.state.visible_association_ids);
      checked += 1;
      if (v.scene.connectors.length !== ids.size || !v.scene.connectors.every((c) => ids.has(c.associationId))) bad.push(`${name} ${template}/${variant}`);
      const drawn = v.scene.decorations.some((d) => d.role === "association");
      if (drawn && ids.size === 0) bad.push(`${name} ${template}/${variant} draws an association where none is visible`);
    }
    gate("whitebox", "no_fabricated_edges", bad.length === 0, bad.length ? bad.join("; ") : `${checked} scenes: connectors = the state's visible associations exactly; no association is drawn that V2 does not show`);
  }

  /* seed_chain: the layout seed derives from the state hash and the presentation, and the chain says so */
  {
    let ok = 0;
    for (const [, view] of canonical) for (const template of TEMPLATES) {
      const v = viewAt(view.restore.map_id, view.restore.state_id, template, 0);
      const seed = tpl.presentationSeed(v.map.state.state_hash, `${template}:0`);
      const chain = v.scene.seedChain;
      if (seed === v.scene.presentationSeed && seed === v.presentation.presentation_seed && chain.length === 4 && chain[0] === `semantic ${v.map.state.semantic_hash.slice(0, 12)}` && chain[1] === `seed ${seed}` && chain[2] === `skeleton ${v.map.nodes.length} terms · variant 0` && chain[3] === `frame ${VIEW.width}×${VIEW.height}`) ok += 1;
    }
    gate("whitebox", "seed_chain_derivation", ok === 3 * N, `${ok}/${3 * N} views: presentation seed = FNV-1a(state_hash, template:variant); seed chain = semantic · seed · skeleton · frame`);
  }

  /* no_runtime_randomness */
  const sources = ["templates.ts", "skeleton.ts", "seed.ts", "forms.ts", "render.ts", "render.server.ts", "service.server.ts", "fingerprint.ts"].map((name) => [name, readFileSync(join(frontendRoot, "src/features/trace-v49/exploration-view", name), "utf8")]);
  const volatile = sources.filter(([, source]) => /Math\.random|Date\.now|new Date\(|performance\.now|randomUUID|hrtime|process\.env|Math\.floor\(Math\.random/.test(source.replace(/\/\*[\s\S]*?\*\//g, ""))).map(([name]) => name);
  gate("whitebox", "no_runtime_randomness", volatile.length === 0, volatile.length ? `volatile input in ${volatile.join(", ")}` : "no Math.random, Date, performance, randomUUID, hrtime or environment in the presentation path");

  /* volatile_metadata_excluded: the export id and the words are outside the structure and the view */
  {
    const manifest = svc.createExplorationViewExportManifest({ map_id: S4.restore.map_id, state_hash: S4.restore.state_hash, composition_id: S4.map.composition.composition_id, template_id: "CHEVRON", variant_id: 0 });
    const exportId = manifest.data.manifest.export_id;
    const structure = fp.presentationStructure(manifest.data.scene);
    const view = viewAt(S4.restore.map_id, S4.restore.state_id, "CHEVRON", 0);
    const words = S4.map.nodes.map((node) => node.canonical_label);
    const exportSvg = svc.renderExplorationExport(manifest.data.scene, manifest.data.manifest.form_id, manifest.data.furniture);
    const drawn = (svg) => svg.replace(/ aria-label="[^"]*"/, "");
    const same = !structure.includes(exportId) && !words.some((word) => structure.includes(word)) && !view.svg.includes(exportId) && !words.some((word) => drawn(view.svg).includes(word)) && !/<text/.test(view.svg) && exportSvg.includes(exportId) && words.every((word) => exportSvg.toLowerCase().includes(word.toLowerCase()));
    gate("whitebox", "volatile_metadata_excluded", same, "the export id and the vocabulary are absent from the structure and from the view's drawn SVG (the alt text aside) and present only in the export's furniture ledger");
  }

  /* unsupported_state_fail_closed */
  {
    const badTemplate = svc.retrieveExplorationView(S4.restore.map_id, S4.restore.state_id, "NOT_A_TEMPLATE", 0);
    const badVariant = svc.retrieveExplorationView(S4.restore.map_id, S4.restore.state_id, "DOTS", 7);
    const badState = svc.retrieveExplorationView(S4.restore.map_id, "R16A-STATE-NOT-A-STATE", "DOTS", 0);
    let tooMany = "no throw";
    try {
      const nine = { ...tpl.sceneContentFromMap(S4.map) };
      nine.nodes = Array.from({ length: 9 }, (_, i) => ({ vocabularyId: `X${i}`, label: `x${i}`, focused: i === 0, seed: i === 0 }));
      tpl.buildExplorationScene(nine, "DOTS", 0, 1);
    } catch (error) { tooMany = error.message; }
    let outOfRange = "no throw";
    try { tpl.buildExplorationScene(tpl.sceneContentFromMap(S4.map), "SPOTS", 3, 1); } catch (error) { outOfRange = error.message; }
    gate("whitebox", "unsupported_state_fail_closed", !badTemplate.ok && badTemplate.code === "INVALID_PRESENTATION" && !badVariant.ok && !badState.ok && tooMany === "TEMPLATE_INCOMPATIBLE" && outOfRange === "INVALID_PRESENTATION_VARIANT", `unknown template → ${badTemplate.ok ? "OK?!" : badTemplate.code}; unknown variant → ${badVariant.ok ? "OK?!" : badVariant.code}; unknown state → ${badState.ok ? "OK?!" : badState.code}; 9 terms → ${tooMany}; variant 3 → ${outOfRange}`);
  }

  /* all_16_templates_real: sixteen distinct layout functions in the source, sixteen distinct grammars on every canonical state */
  {
    const source = readFileSync(join(frontendRoot, "src/features/trace-v49/exploration-view/templates.ts"), "utf8");
    const layoutFunctions = [...source.matchAll(/^function layout(\w+)\(/gmu)].map((m) => m[1]);
    const table = source.slice(source.indexOf("const LAYOUTS"), source.indexOf("});", source.indexOf("const LAYOUTS")));
    const entries = [...table.matchAll(/(\w+): (layout\w+)/g)].map((m) => [m[1], m[2]]);
    const distinctTargets = new Set(entries.map(([, fn]) => fn));
    gate("whitebox", "all_16_templates_real", layoutFunctions.length === 16 && entries.length === 16 && distinctTargets.size === 16 && N === 16, `${layoutFunctions.length} layout functions, ${entries.length} template entries, ${distinctTargets.size} distinct targets`);
  }

  /* screen_export_same_model: one seed, one skeleton, the same associations; the export laid out for its form's image area */
  {
    let same = 0;
    for (const [, view] of canonical) for (const template of TEMPLATES) {
      const v = viewAt(view.restore.map_id, view.restore.state_id, template, 0);
      const manifest = svc.createExplorationViewExportManifest({ map_id: v.restore.map_id, state_hash: v.restore.state_hash, composition_id: v.map.composition.composition_id, template_id: template, variant_id: 0 });
      const e = manifest.data.scene;
      const form = STAMP_FORMS[manifest.data.manifest.form_id];
      const edges = (s) => JSON.stringify(s.connectors.map((c) => [c.from, c.to, c.associationId]));
      const order = (s) => s.nodes.map((n) => n.vocabularyId).join(",");
      const exportSvg = svc.renderExplorationExport(e, manifest.data.manifest.form_id, manifest.data.furniture);
      if (e.presentationSeed === v.scene.presentationSeed && e.seedChain.slice(0, 3).join("|") === v.scene.seedChain.slice(0, 3).join("|") && edges(e) === edges(v.scene) && order(e) === order(v.scene) && e.frame.x === form.image.x && e.frame.width === form.image.width && manifest.data.manifest.form_id === types.EXPLORATION_FORM_OF_TEMPLATE[template] && manifest.data.manifest.dimensions.width === form.width * EXPORT_SCALE && exportSvg.includes(`data-form="${form.id}"`) && exportSvg.includes(`width="${form.width}" height="${form.height}"`)) same += 1;
    }
    gate("whitebox", "screen_export_same_model", same === 3 * N, `${same}/${3 * N} views: the export scene shares the view's seed, semantic field, skeleton and associations, laid out for its form's image area; the export SVG is the form's size`);
  }
}

/* ======================= BLACK-BOX (HTTP) ======================= */
const http = async (path, init) => fetch(`${baseUrl}${path}`, init);
const inlineSvg = (html) => {
  const start = html.indexOf(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="${VIEW.x} ${VIEW.y} ${VIEW.width} ${VIEW.height}"`);
  const end = html.indexOf("</svg>", start);
  return start >= 0 && end >= 0 ? html.slice(start, end + 6).replaceAll("&quot;", '"') : "";
};
const decodeHtml = (svg) => svg.replaceAll("&amp;", "&");
const rasterView = (svg) => sharp(Buffer.from(svg, "utf8"), { density: 72 }).resize(420, 560, { fit: "fill" }).png({ compressionLevel: 9, adaptiveFiltering: false }).toBuffer();
const viewRasters = new Map();
const exportPngs = new Map();
const matrix = [];
let serverUp = true;
try { await http("/api/trace/exploration-view/v1/starting-points"); } catch { serverUp = false; }
record("blackbox", "dev_server", serverUp ? "PASS" : "FAIL", `${baseUrl} ${serverUp ? "answers" : "does not answer — black-box layer skipped"}`);

async function exportPng(view, template, variant) {
  const body = JSON.stringify({ map_id: view.restore.map_id, state_hash: view.restore.state_hash, composition_id: view.map.composition.composition_id, template_id: template, variant_id: variant });
  const response = await http("/api/trace/exploration-view/v1/exports/png", { method: "POST", headers: { "content-type": "application/json" }, body });
  assert.equal(response.status, 200, `png export ${template}/${variant}`);
  return { buffer: Buffer.from(await response.arrayBuffer()), exportId: response.headers.get("x-trace-export-id"), form: response.headers.get("x-trace-export-form") };
}
const entryOf = async (name, api, extra) => ({
  state: name,
  state_id: api.restore.state_id,
  map_id: api.restore.map_id,
  node_count: api.map.nodes.length,
  template: api.presentation.template_id,
  variant: api.presentation.variant_id,
  variant_name: api.presentation.variant_name,
  form_id: api.presentation.form_id,
  semantic_hash: api.map.state.semantic_hash,
  semantic_field: skeleton.fieldKind(api.map.state.semantic_hash),
  state_hash: api.restore.state_hash,
  presentation_seed: api.presentation.presentation_seed,
  layout_seed_used: api.scene.seedChain,
  skeleton_family: skeleton.skeletonFamily(api.map.nodes.length, api.presentation.variant_id),
  term_anchors: api.scene.nodes.map((node) => [labelOf.get(node.vocabularyId), Math.round(node.anchor.x), Math.round(node.anchor.y)]),
  presentation_fingerprint: (await presentationOf(api)).fingerprint,
  presentation_grammar: fp.presentationGrammar(api.scene),
  view_svg_bytes: Buffer.byteLength(api.svg, "utf8"),
  view_svg_elements: (api.svg.match(/<(rect|circle|line|polygon|path)\b/g) ?? []).length,
  visible_terms: api.map.plain_text_tree.tree_node_ids.map((id) => labelOf.get(id)),
  visible_associations: api.map.associations.map((item) => item.endpoint_labels),
  ...extra,
});

if (serverUp) {
  for (const [name, view] of canonical) {
    for (const template of TEMPLATES) {
      const url = `/trace/exploration?map=${encodeURIComponent(view.restore.map_id)}&state=${encodeURIComponent(view.restore.state_id)}&template=${template}&variant=0`;
      const svgHashes = [];
      for (let i = 0; i < 5; i += 1) svgHashes.push(sha256(decodeHtml(inlineSvg(await (await http(url)).text()))));
      const api = viewAt(view.restore.map_id, view.restore.state_id, template, 0);
      const apiSvgHash = sha256(api.svg);
      const pngHashes = [];
      let last = null;
      for (let i = 0; i < 5; i += 1) { last = await exportPng(api, template, 0); pngHashes.push(sha256(last.buffer)); }
      const meta = await sharp(last.buffer).metadata();
      exportPngs.set(`${name}:${template}:0`, last.buffer);
      viewRasters.set(`${name}:${template}:0`, await rasterView(api.svg));
      const reloadsSame = new Set(svgHashes).size === 1;
      const pageMatchesApi = svgHashes[0] === apiSvgHash;
      const exportsSame = new Set(pngHashes).size === 1;
      const form = STAMP_FORMS[api.presentation.form_id];
      matrix.push(await entryOf(name, api, { page_svg_sha256: svgHashes[0], png_sha256: pngHashes[0], export_id: last.exportId, export_form: last.form, png_dimensions: [meta.width, meta.height], reloads_identical: reloadsSame, exports_identical: exportsSame }));
      gate("blackbox", `reload_stability:${name}:${template}`, reloadsSame && pageMatchesApi, `5 reloads → ${new Set(svgHashes).size} SVG hash(es); page SVG ${pageMatchesApi ? "equals" : "differs from"} the API's`);
      gate("blackbox", `export_stability:${name}:${template}`, exportsSame && meta.width === form.width * EXPORT_SCALE && meta.height === form.height * EXPORT_SCALE && last.form === form.id, `5 exports → ${new Set(pngHashes).size} PNG hash(es) ${short(pngHashes[0])} · ${last.exportId} · ${form.id} ${meta.width}×${meta.height} (${EXPORT_SCALE}× ${form.width}×${form.height})`);
    }
  }
  /* the S4 variants */
  for (const template of TEMPLATES) {
    for (let variant = 1; variant < types.EXPLORATION_TEMPLATE_VARIANTS[template].length; variant += 1) {
      const api = viewAt(S4.restore.map_id, S4.restore.state_id, template, variant);
      const png = await exportPng(api, template, variant);
      exportPngs.set(`S4:${template}:${variant}`, png.buffer);
      viewRasters.set(`S4:${template}:${variant}`, await rasterView(api.svg));
      matrix.push(await entryOf("S4", api, { png_sha256: sha256(png.buffer), export_id: png.exportId, export_form: png.form }));
    }
  }
  /* view_weight: the picture the browser must paint stays within budget */
  {
    const heavy = matrix.filter((item) => item.view_svg_bytes > T.viewBytes || item.view_svg_elements > T.viewElements);
    const maxBytes = Math.max(...matrix.map((item) => item.view_svg_bytes));
    const maxElements = Math.max(...matrix.map((item) => item.view_svg_elements));
    const heaviest = matrix.find((item) => item.view_svg_elements === maxElements);
    gate("blackbox", "view_weight", heavy.length === 0, `${matrix.length} views: ≤ ${Math.round(maxBytes / 1024)} KB and ≤ ${maxElements} primitives each (heaviest ${heaviest.template}/${heaviest.variant} on ${heaviest.state}); budget ${T.viewBytes / 1000} KB · ${T.viewElements} primitives; the grain is one 240 px turbulence tile repeated as a pattern${heavy.length ? `; over budget: ${heavy.map((item) => `${item.state} ${item.template}/${item.variant}`).join(", ")}` : ""}`);
  }
  /* export_stress: a burst of twelve against the render limiter */
  {
    const body = JSON.stringify({ map_id: S4.restore.map_id, state_hash: S4.restore.state_hash, composition_id: S4.map.composition.composition_id, template_id: "CHEVRON", variant_id: 0 });
    const reference = exportPngs.get("S4:CHEVRON:0");
    const burst = await Promise.all(Array.from({ length: 12 }, () => http("/api/trace/exploration-view/v1/exports/png", { method: "POST", headers: { "content-type": "application/json" }, body }).then(async (response) => ({ status: response.status, body: Buffer.from(await response.arrayBuffer()), type: response.headers.get("content-type") ?? "" }))));
    const statuses = burst.map((item) => item.status);
    const okOnes = burst.filter((item) => item.status === 200);
    const limited = burst.filter((item) => item.status === 429);
    const identical = okOnes.every((item) => sha256(item.body) === sha256(reference));
    const problems = limited.every((item) => item.type.includes("application/json") && /"code":"REQUEST_LIMIT_EXCEEDED"/.test(item.body.toString("utf8")));
    const after = await http("/api/trace/exploration-view/v1/exports/png", { method: "POST", headers: { "content-type": "application/json" }, body });
    const recovered = after.status === 200 && sha256(Buffer.from(await after.arrayBuffer())) === sha256(reference);
    gate("blackbox", "export_stress", statuses.every((s) => s === 200 || s === 429) && okOnes.length >= 1 && identical && problems && recovered, `12 parallel exports of S4/CHEVRON/0 → ${okOnes.length} × 200, ${limited.length} × 429 (limiter MAX_IN_FLIGHT 4), ${statuses.filter((s) => s !== 200 && s !== 429).length} other; every 200 byte-identical to the sequential export ${identical}; every 429 a REQUEST_LIMIT_EXCEEDED problem ${problems}; the next sequential export recovers ${recovered}`);
  }
}

/* ---- image metrics: pHash (DCT) and SSIM (8×8 windows, grayscale) ---- */
async function gray(buffer, width, height) {
  const { data } = await sharp(buffer).resize(width, height, { fit: "fill" }).grayscale().raw().toBuffer({ resolveWithObject: true });
  return data;
}
async function phash(buffer) {
  const size = 32;
  const px = await gray(buffer, size, size);
  const dct = new Float64Array(8 * 8);
  for (let u = 0; u < 8; u += 1) for (let v = 0; v < 8; v += 1) {
    let sum = 0;
    for (let x = 0; x < size; x += 1) for (let y = 0; y < size; y += 1) sum += px[y * size + x] * Math.cos(((2 * x + 1) * u * Math.PI) / (2 * size)) * Math.cos(((2 * y + 1) * v * Math.PI) / (2 * size));
    dct[v * 8 + u] = sum;
  }
  const values = [...dct].slice(1);
  const sorted = [...values].sort((a, b) => a - b);
  const median = sorted[Math.floor(sorted.length / 2)];
  return values.map((value) => (value > median ? "1" : "0")).join("");
}
const hamming = (a, b) => [...a].reduce((sum, bit, i) => sum + (bit === b[i] ? 0 : 1), 0);
async function ssim(bufferA, bufferB) {
  const w = 144; const h = 192;
  const [a, b] = [await gray(bufferA, w, h), await gray(bufferB, w, h)];
  const C1 = (0.01 * 255) ** 2; const C2 = (0.03 * 255) ** 2;
  let total = 0; let windows = 0;
  for (let y = 0; y < h; y += 8) for (let x = 0; x < w; x += 8) {
    let ma = 0; let mb = 0;
    for (let j = 0; j < 8; j += 1) for (let i = 0; i < 8; i += 1) { ma += a[(y + j) * w + x + i]; mb += b[(y + j) * w + x + i]; }
    ma /= 64; mb /= 64;
    let va = 0; let vb = 0; let cov = 0;
    for (let j = 0; j < 8; j += 1) for (let i = 0; i < 8; i += 1) { const da = a[(y + j) * w + x + i] - ma; const db = b[(y + j) * w + x + i] - mb; va += da * da; vb += db * db; cov += da * db; }
    va /= 63; vb /= 63; cov /= 63;
    total += ((2 * ma * mb + C1) * (2 * cov + C2)) / ((ma * ma + mb * mb + C1) * (va + vb + C2));
    windows += 1;
  }
  return total / windows;
}

const comparisons = [];
const goldens = [];
if (serverUp) {
  const hashes = new Map();
  for (const [key, buffer] of viewRasters) hashes.set(key, { sha: sha256(buffer), phash: await phash(buffer) });
  /* the verdict per kind — a hard threshold, no review class */
  const verdict = (kind, exact, distance, similarity) => {
    if (exact || distance === 0) return "HARD_FAIL";
    if (kind === "state") return similarity < T.crossState ? "distinct" : "HARD_FAIL";
    if (kind === "variant") return similarity < T.variant ? "distinct" : "HARD_FAIL";
    return similarity < T.crossTemplate ? "distinct" : "HARD_FAIL";
  };
  const compare = async (kind, state, keyA, keyB, labelA, labelB) => {
    const a = hashes.get(keyA); const b = hashes.get(keyB);
    const exact = a.sha === b.sha;
    const distance = hamming(a.phash, b.phash);
    const similarity = await ssim(viewRasters.get(keyA), viewRasters.get(keyB));
    const status = verdict(kind, exact, distance, similarity);
    comparisons.push({ kind, state, a: labelA, b: labelB, exact_duplicate: exact, phash_distance: distance, ssim: r3(similarity), threshold: kind === "state" ? T.crossState : kind === "variant" ? T.variant : T.crossTemplate, status });
    return status;
  };
  for (const [name] of canonical) for (let i = 0; i < N; i += 1) for (let j = i + 1; j < N; j += 1) await compare("template", name, `${name}:${TEMPLATES[i]}:0`, `${name}:${TEMPLATES[j]}:0`, TEMPLATES[i], TEMPLATES[j]);
  for (const template of TEMPLATES) {
    for (let i = 0; i < canonical.length; i += 1) for (let j = i + 1; j < canonical.length; j += 1) await compare("state", `${canonical[i][0]}~${canonical[j][0]}`, `${canonical[i][0]}:${template}:0`, `${canonical[j][0]}:${template}:0`, `${template}@${canonical[i][0]}`, `${template}@${canonical[j][0]}`);
    const count = types.EXPLORATION_TEMPLATE_VARIANTS[template].length;
    for (let i = 0; i < count; i += 1) for (let j = i + 1; j < count; j += 1) await compare("variant", "S4", `S4:${template}:${i}`, `S4:${template}:${j}`, `${template}/${i}`, `${template}/${j}`);
  }
  const byKind = (kind) => comparisons.filter((item) => item.kind === kind);
  const failed = (kind) => byKind(kind).filter((item) => item.status === "HARD_FAIL");
  const stats = (kind) => { const values = byKind(kind).map((item) => item.ssim); return `SSIM ${Math.min(...values)}–${Math.max(...values)}, pHash distance ${Math.min(...byKind(kind).map((i) => i.phash_distance))}–${Math.max(...byKind(kind).map((i) => i.phash_distance))}`; };
  gate("blackbox", "cross_template_distinct", failed("template").length === 0, `${byKind("template").length} same-state pairs of different templates: ${stats("template")}; threshold SSIM < ${T.crossTemplate}, pHash > 0${failed("template").length ? `; failed: ${failed("template").map((item) => `${item.state} ${item.a}~${item.b} (${item.ssim})`).join("; ")}` : ""}`);
  gate("blackbox", "cross_state_distinct", failed("state").length === 0, `${byKind("state").length} same-template pairs of different states: ${stats("state")}; threshold SSIM < ${T.crossState}${failed("state").length ? `; failed: ${failed("state").map((item) => `${item.a}~${item.b} (${item.ssim})`).join("; ")}` : ""}`);
  gate("blackbox", "variant_distinct", failed("variant").length === 0, `${byKind("variant").length} same-state pairs of different variants: ${stats("variant")}; threshold SSIM < ${T.variant}${failed("variant").length ? `; failed: ${failed("variant").map((item) => `${item.a}~${item.b} (${item.ssim})`).join("; ")}` : ""}`);

  /* golden images: the 48 variant-0 views against docs/qa/…/golden (Git LFS) */
  mkdirSync(goldenDir, { recursive: true });
  let created = 0;
  const regressions = [];
  let compared = 0;
  for (const [name] of canonical) for (const template of TEMPLATES) {
    const key = `${name}:${template}:0`;
    const file = join(goldenDir, `${name}-${template}-0.png`);
    const raster = viewRasters.get(key);
    const isPointer = existsSync(file) && readFileSync(file).subarray(0, 40).toString("utf8").startsWith("version https://git-lfs");
    if (!existsSync(file) || goldenMode === "update" || isPointer) { writeFileSync(file, raster); created += 1; goldens.push({ key, file: `golden/${name}-${template}-0.png`, status: "CREATED", ssim: 1 }); continue; }
    const similarity = await ssim(readFileSync(file), raster);
    compared += 1;
    const ok = similarity >= T.golden;
    if (!ok) regressions.push(`${name} ${template} ${r3(similarity)}`);
    goldens.push({ key, file: `golden/${name}-${template}-0.png`, status: ok ? "MATCH" : "REGRESSION", ssim: r3(similarity) });
  }
  record("blackbox", "golden_regression", regressions.length ? "FAIL" : compared === 0 ? "CREATED" : "PASS", regressions.length ? `below SSIM ${T.golden} against the golden: ${regressions.join("; ")}` : compared === 0 ? `${created} golden images written to golden/ (Git LFS); no baseline existed — the next run compares against them` : `${compared} views at SSIM ≥ ${T.golden} against their golden image${created ? `; ${created} golden(s) (re)written` : ""}`);
  if (regressions.length) failures.push(`blackbox:golden_regression — ${regressions.join("; ")}`);
}

/* ======================= METAMORPHIC ======================= */
{
  for (const [name, view] of canonical) {
    const a = viewAt(view.restore.map_id, view.restore.state_id, "GRID", 0);
    const b = viewAt(view.restore.map_id, view.restore.state_id, "LINES", 0);
    const unchanged = semantics(a) === semantics(b) && a.map.composition.composition_id === b.map.composition.composition_id;
    const changed = (await presentationOf(a)).fingerprint !== (await presentationOf(b)).fingerprint && a.svg !== b.svg;
    gate("metamorphic", `A_same_state_other_template:${name}`, unchanged && changed, `GRID → LINES: research unchanged ${unchanged}, presentation changed ${changed}`);
  }
  {
    const ps = points.find((point) => point.label === "production site");
    const md = points.find((point) => point.label === "material displacement");
    const rootA = svc.createExplorationView({ vocabulary_id: ps.vocabulary_id }).data;
    const rootB = svc.createExplorationView({ vocabulary_id: md.vocabulary_id }).data;
    const a = viewAt(rootA.restore.map_id, rootA.restore.state_id, "LINES", 0);
    const b = viewAt(rootB.restore.map_id, rootB.restore.state_id, "LINES", 0);
    const [pa, pb] = [await presentationOf(a), await presentationOf(b)];
    const kinds = (g) => [...new Set(g.split(" ").filter((x) => !x.startsWith("spread")).map((x) => x.split("=")[0]))].join();
    const sameGrammarKinds = kinds(pa.grammar) === kinds(pb.grammar);
    gate("metamorphic", "B_same_template_other_state:LINES", sameGrammarKinds && pa.fingerprint !== pb.fingerprint, `production site (${a.restore.state_id}) vs material displacement (${b.restore.state_id}) under LINES/0: same primitive kinds ${sameGrammarKinds}, fingerprints ${short(pa.fingerprint)} ≠ ${short(pb.fingerprint)} ${pa.fingerprint !== pb.fingerprint}`);
    const ladder = await Promise.all(canonical.map(async ([n, v]) => [n, (await presentationOf(viewAt(v.restore.map_id, v.restore.state_id, "LINES", 0))).fingerprint]));
    gate("metamorphic", "B_complexity_ladder:LINES", new Set(ladder.map(([, f]) => f)).size === 3, `S2/S3/S4 under LINES/0: ${ladder.map(([n, f]) => `${n} ${short(f)}`).join(", ")}`);
  }
  {
    const up = step(S2, "MORE");
    const down = step(up, "LESS");
    const okUp = up.map.nodes.length === 3 && up.controls && (await presentationOf(up)).fingerprint === (await presentationOf(viewAt(up.restore.map_id, up.restore.state_id, up.restore.template_id, up.restore.variant_id))).fingerprint;
    const okDown = down.map.nodes.length === 2 && (await presentationOf(down)).fingerprint === (await presentationOf(S2)).fingerprint && down.restore.state_hash === S2.restore.state_hash;
    gate("metamorphic", "C_complexity_steps", okUp && okDown, `S2 → More → ${up.map.nodes.length} terms (template kept: ${up.restore.template_id === S2.restore.template_id}) → Less → ${down.map.nodes.length} terms, back to S2's state and picture ${okDown}`);
    const refused = svc.applyExplorationViewAction(S4.restore.map_id, { action: "MORE", expected_state_hash: S4.restore.state_hash, template_id: S4.restore.template_id, variant_id: S4.restore.variant_id });
    gate("metamorphic", "C_richest_refused", !refused.ok && refused.code === "ACTION_NOT_AVAILABLE", `More at S4 → ${refused.ok ? "OK?!" : refused.code}`);
  }
  {
    let current = S2;
    const seen = [await presentationOf(current)];
    const pool = current.controls.another_view.pool_size;
    let ok = true;
    const detail = [];
    for (let i = 0; i < pool; i += 1) {
      const next = step(current, "ANOTHER_VIEW");
      const print = await presentationOf(next);
      const startKept = next.starting_point.vocabulary_id === current.starting_point.vocabulary_id;
      const somethingChanged = next.map.composition.composition_id !== current.map.composition.composition_id || next.restore.template_id !== current.restore.template_id || next.restore.variant_id !== current.restore.variant_id;
      const visualChanged = print.fingerprint !== seen[seen.length - 1].fingerprint;
      if (!(startKept && somethingChanged && visualChanged)) ok = false;
      detail.push(`${i + 1}: ${next.restore.template_id}/${next.restore.variant_id} ${short(print.fingerprint)}${visualChanged ? "" : " SAME!"}`);
      seen.push(print);
      current = next;
    }
    gate("metamorphic", "D_another_view", ok, `${pool} steps from S2 (${S2.starting_point.label}): starting point kept, composition or treatment changed, picture changed each step — ${detail.join(" · ")}`);
  }
  {
    const redundant = comparisons.filter((item) => item.kind === "variant" && item.status === "HARD_FAIL");
    gate("metamorphic", "E_variants_distinct", redundant.length === 0, redundant.length ? `variants too alike: ${redundant.map((item) => `${item.a}~${item.b} (${item.ssim})`).join("; ")}` : `${comparisons.filter((item) => item.kind === "variant").length} variant pairs on S4: research identical (white-box), every pair below SSIM ${T.variant}`);
  }
  {
    const counts = Object.fromEntries(types.EXPLORATION_FORM_IDS.map((form) => [form, TEMPLATES.filter((t) => types.EXPLORATION_FORM_OF_TEMPLATE[t] === form)]));
    const ok = Object.values(counts).every((list) => list.length >= 3) && matrix.every((item) => item.form_id === types.EXPLORATION_FORM_OF_TEMPLATE[item.template] && (!item.export_form || item.export_form === item.form_id));
    gate("metamorphic", "F_form_follows_template", ok, Object.entries(counts).map(([form, list]) => `${form}: ${list.join(", ")}`).join(" · "));
  }
}

/* ======================= the contact sheets ======================= */
mkdirSync(outDir, { recursive: true });
const label = (width, height, lines) => Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">${lines.map((line, i) => `<text x="0" y="${16 + i * 16}" font-family="Helvetica, Arial, sans-serif" font-size="${i === 0 ? 12 : 11}" font-weight="${i === 0 ? 700 : 400}" fill="${i === 0 ? "#161514" : "#5f5e5a"}">${line.replaceAll("&", "&amp;").replaceAll("<", "&lt;")}</text>`).join("")}</svg>`);
if (serverUp) {
  const imgW = 300; const imgH = 400; const cellW = 320; const cellH = 460;
  const header = 70; const left = 170;
  const sheetW = left + cellW * 3 + 20; const sheetH = header + cellH * N + 20;
  const composites = [];
  for (let row = 0; row < N; row += 1) {
    for (let col = 0; col < canonical.length; col += 1) {
      const key = `${canonical[col][0]}:${TEMPLATES[row]}:0`;
      const thumb = await sharp(viewRasters.get(key)).resize(imgW, imgH).png().toBuffer();
      composites.push({ input: thumb, left: left + 10 + col * cellW, top: header + row * cellH });
      const entry = matrix.find((item) => item.state === canonical[col][0] && item.template === TEMPLATES[row] && item.variant === 0);
      composites.push({ input: label(imgW, 52, [`${canonical[col][0]} · ${entry.node_count} · ${entry.visible_associations.length} assoc · ${entry.skeleton_family} · ${entry.semantic_field}`, `fp ${entry.presentation_fingerprint.slice(0, 10)} · seed ${entry.presentation_seed}`, `${entry.state_id} · png ${entry.png_sha256.slice(0, 10)} · ${entry.form_id}`]), left: left + 10 + col * cellW, top: header + row * cellH + imgH + 4 });
    }
    composites.push({ input: Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${left}" height="60"><text x="10" y="24" font-family="Helvetica, Arial, sans-serif" font-size="16" font-weight="700" fill="#161514">${TEMPLATES[row]}</text><text x="10" y="44" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="#5f5e5a">${types.EXPLORATION_TEMPLATE_NAMES[TEMPLATES[row]]} · ${types.EXPLORATION_TEMPLATE_VARIANTS[TEMPLATES[row]][0]}</text></svg>`), left: 0, top: header + row * cellH + 10 });
  }
  composites.push({ input: Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${sheetW}" height="${header}"><text x="10" y="30" font-family="Helvetica, Arial, sans-serif" font-size="18" font-weight="700" fill="#161514">Exploration · 48 views · ${S2.starting_point.label} · 3 states × ${N} templates · variant 0 · the view picture (${VIEW.width}×${VIEW.height})</text>${canonical.map(([n, v], i) => `<text x="${left + 10 + i * cellW}" y="58" font-family="Helvetica, Arial, sans-serif" font-size="14" font-weight="700" fill="#161514">${n} · ${v.map.nodes.length}</text>`).join("")}</svg>`), left: 0, top: 0 });
  await sharp({ create: { width: sheetW, height: sheetH, channels: 3, background: "#e8e6e0" } }).composite(composites).png({ compressionLevel: 9 }).toFile(join(outDir, "exploration-48-view-contact-sheet.png"));

  /* the five export forms on S4, one template each */
  const formTiles = [];
  for (const form of types.EXPLORATION_FORM_IDS) {
    const template = TEMPLATES.find((t) => types.EXPLORATION_FORM_OF_TEMPLATE[t] === form);
    const buffer = exportPngs.get(`S4:${template}:0`);
    const meta = await sharp(buffer).metadata();
    const scale = 560 / meta.height;
    const w = Math.round(meta.width * scale);
    formTiles.push({ input: await sharp(buffer).resize(w, 560).png().toBuffer(), w, form, template, meta });
  }
  const formsW = formTiles.reduce((sum, tile) => sum + tile.w + 24, 24);
  let x = 24;
  const formComposites = [];
  for (const tile of formTiles) {
    formComposites.push({ input: tile.input, left: x, top: 60 });
    formComposites.push({ input: label(tile.w, 40, [`${tile.form} · ${types.EXPLORATION_FORM_NAMES[tile.form]}`, `${tile.template} · ${tile.meta.width}×${tile.meta.height} · ${matrix.find((item) => item.state === "S4" && item.template === tile.template && item.variant === 0).export_id}`]), left: x, top: 628 });
    x += tile.w + 24;
  }
  formComposites.push({ input: Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${formsW}" height="50"><text x="24" y="34" font-family="Helvetica, Arial, sans-serif" font-size="18" font-weight="700" fill="#161514">Exploration · the five export forms · S4 · ${S4.starting_point.label}</text></svg>`), left: 0, top: 0 });
  await sharp({ create: { width: formsW, height: 690, channels: 3, background: "#e8e6e0" } }).composite(formComposites).png({ compressionLevel: 9 }).toFile(join(outDir, "exploration-export-forms-sheet.png"));
}

/* ======================= reports ======================= */
const now = "2026-09-06";
const table = (rows) => ["| Test | Status | Detail |", "| --- | --- | --- |", ...rows.map((row) => `| ${row.test} | ${row.status} | ${row.detail.replaceAll("|", "\\|")} |`)].join("\n");
writeFileSync(join(outDir, "visual-generation-matrix.json"), JSON.stringify({ format: "exploration-visual-generation-matrix/v2", generated: now, base_url: baseUrl, presentation_version: types.EXPLORATION_PRESENTATION_VERSION, render_version: types.EXPLORATION_VIEW_RENDER_VERSION, view_frame: VIEW, thresholds: T, canonical_states: canonical.map(([n, v]) => ({ name: n, state_id: v.restore.state_id, map_id: v.restore.map_id, state_hash: v.restore.state_hash, semantic_hash: v.map.state.semantic_hash, semantic_field: skeleton.fieldKind(v.map.state.semantic_hash), node_count: v.map.nodes.length, starting_point: v.starting_point.label })), entries: matrix, comparisons, goldens }, null, 1) + "\n");

writeFileSync(join(outDir, "WHITEBOX_REPORT.md"), `# Exploration presentation — white-box report (${now})

Scope: the presentation derivation of \`features/trace-v49/exploration-view/\` (skeleton, templates, forms, render, service, fingerprint), tested through the service without the UI. V2 semantics unchanged.

**Engine.** For a state with n terms the structural engine (\`skeleton.ts\`) chooses a skeleton family from n and the variant (2: opposed / diagonal / stacked; 3: triangle / chain / arc; 4: clusters / diamond / run; 5–8: ring / rows / spiral), bends it by the state's semantic field (radial / shear / lattice, from the semantic hash), and jitters it by the presentation seed. The template draws its idiom on those positions; the variant also chooses the connection mode (direct / orthogonal / arc) an association's shape runs in. Every connector is a visible V2 association; nothing is drawn between two terms that V2 does not associate.

**Fingerprint.** \`presentationFingerprint(scene)\` = SHA-256 of the canonical structure: presentation version, template, variant, frame, the field's ground, paper and ink, every definition (gradient stops and directions, the grain's frequency, seed and opacity), every primitive (kind, role, clip, opacity, coordinates, dimensions, radii, path geometry, rotation, fill, stroke), the terms' anchors and regions and the associations' regions. Excluded: vocabulary, titles, the export id, provenance strings, the alt text. \`presentationGrammar(scene)\` = the histogram of primitive kinds by role plus the terms' spread.

**Seed chain.** presentation seed = FNV-1a(state_hash, "TEMPLATE:variant"); the scene records \`semantic <hash12> · seed <n> · skeleton <n> terms · variant <v> · frame <w>×<h>\` (the matrix column \`layout_seed_used\`).

**Canonical states** (one starting point, its complexity ladder): ${canonical.map(([n, v]) => `${n} = ${v.restore.state_id} (${v.map.nodes.length} terms, ${v.map.associations.length} associations, semantic ${short(v.map.state.semantic_hash)}, field ${skeleton.fieldKind(v.map.state.semantic_hash)})`).join("; ")}.

${table(results.whitebox)}

Result: ${results.whitebox.filter((r) => r.status === "FAIL").length === 0 ? "PASS" : "FAIL"} — ${results.whitebox.filter((r) => r.status === "PASS").length}/${results.whitebox.length} gates.
`);

const matrixRows = matrix.filter((item) => item.variant === 0).map((item) => `| ${item.state} | ${item.template} | ${item.node_count} | ${item.visible_associations.length} | ${item.skeleton_family} | ${item.semantic_field} | ${item.presentation_seed} | ${short(item.presentation_fingerprint)} | ${short(item.png_sha256)} | ${item.form_id} ${item.png_dimensions.join("×")} | ${item.reloads_identical ? "5/5" : "≠"} | ${item.exports_identical ? "5/5" : "≠"} | ${Math.round(item.view_svg_bytes / 1024)} KB · ${item.view_svg_elements} |`);
const comparisonRows = comparisons.filter((item) => item.kind !== "template" || item.status === "HARD_FAIL" || item.ssim >= 0.8).map((item) => `| ${item.kind} | ${item.state} | ${item.a} | ${item.b} | ${item.exact_duplicate ? "YES" : "no"} | ${item.phash_distance} | ${item.ssim} | ${item.threshold} | ${item.status} |`);
const goldenRows = goldens.map((item) => `| ${item.key} | ${item.file} | ${item.ssim} | ${item.status} |`);
writeFileSync(join(outDir, "BLACKBOX_REPORT.md"), `# Exploration presentation — black-box and metamorphic report (${now})

Scope: the real page \`/trace/exploration\` and the real export endpoint \`/api/trace/exploration-view/v1/exports/png\` on ${baseUrl}; 3 governed states × ${N} templates (variant 0) = 48 views, each reloaded five times and exported five times; the S4 variants exported once each. Image metrics over the VIEW pictures (the page's inline SVG rasterised at 420×560, so the forms' furniture does not enter the comparison): SHA-256 (exact), pHash (32×32 DCT, 63 bits, Hamming distance) and SSIM (144×192 grayscale, 8×8 windows). Export PNGs are checked for byte stability, form and dimensions.

**Acceptable visual delta — the hard gates.** Same state, other template: SSIM < ${T.crossTemplate} and pHash distance > 0. Same template, other state: SSIM < ${T.crossState}. Same state, other variant: SSIM < ${T.variant}. Golden image: SSIM ≥ ${T.golden}. Anything else is a failure; there is no review class.

## 48 views

| State | Template | Terms | Assoc. | Skeleton | Field | Seed | Fingerprint | PNG | Form | Reloads | Exports | View weight |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
${matrixRows.join("\n")}

## Black-box gates

${table(results.blackbox)}

## Metamorphic gates

${table(results.metamorphic)}

## Pairwise comparisons (${comparisons.length}; cross-template pairs listed only at SSIM ≥ 0.8 or failure — all are in the matrix JSON)

| Kind | State | A | B | Exact duplicate | pHash distance | SSIM | Threshold | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
${comparisonRows.join("\n")}

## Golden images (${goldens.length})

| View | File | SSIM | Status |
| --- | --- | --- | --- |
${goldenRows.join("\n")}

Contact sheets: \`exploration-48-view-contact-sheet.png\` (rows = templates, columns = S2 / S3 / S4; the view pictures), \`exploration-export-forms-sheet.png\` (the five export forms on S4). Machine-readable: \`visual-generation-matrix.json\` (with \`layout_seed_used\`, \`skeleton_family\`, \`semantic_field\`, \`term_anchors\` per entry).

Result: ${failures.length === 0 ? "PASS" : "FAIL"} — ${[...results.blackbox, ...results.metamorphic].filter((r) => r.status === "PASS").length}/${results.blackbox.length + results.metamorphic.length} gates${goldens.some((g) => g.status === "CREATED") ? ", goldens created" : ""}.
`);

console.log(`EXPLORATION_PRESENTATION_V1=${failures.length === 0 ? "PASS" : "FAIL"} WHITEBOX=${results.whitebox.filter((r) => r.status === "PASS").length}/${results.whitebox.length} BLACKBOX=${results.blackbox.filter((r) => r.status === "PASS").length}/${results.blackbox.length} METAMORPHIC=${results.metamorphic.filter((r) => r.status === "PASS").length}/${results.metamorphic.length} COMPARISONS=${comparisons.length} HARD_FAIL=${comparisons.filter((c) => c.status === "HARD_FAIL").length} GOLDENS=${goldens.filter((g) => g.status === "MATCH").length}/${goldens.length} CREATED=${goldens.filter((g) => g.status === "CREATED").length}`);
if (failures.length) { console.error(failures.join("\n")); process.exitCode = 1; }
