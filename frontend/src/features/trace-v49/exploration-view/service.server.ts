import "server-only";

import { createHash } from "node:crypto";
import { deriveExplorationV2Map, getExplorationV2CategoryByEntry } from "../exploration-v2/derive.server.ts";
import { getExplorationV2ReadModel } from "../exploration-v2/read-model.server.ts";
import { getExplorationV2TransitionIndex } from "../exploration-v2/transition.server.ts";
import type {
  ExplorationV2CategoryId,
  ExplorationV2MapDto,
  ExplorationV2ReadModel,
  ExplorationV2StateRecord,
} from "../exploration-v2/types.ts";
import { EXPORT_SCALE, STAMP_FORMS } from "./forms.ts";
import { renderExplorationExportSvg, renderExplorationViewSvg } from "./render.ts";
import {
  buildExplorationScene,
  getCompatibleTemplates,
  nextTemplate,
  presentationSeed,
  sceneContentFromMap,
  selectPresentationTemplate,
  selectPresentationVariant,
} from "./templates.ts";
import {
  EXPLORATION_FORM_NAMES,
  EXPLORATION_FORM_OF_TEMPLATE,
  EXPLORATION_PRESENTATION_VERSION,
  EXPLORATION_TEMPLATE_IDS,
  EXPLORATION_TEMPLATE_NAMES,
  EXPLORATION_TEMPLATE_VARIANTS,
  EXPLORATION_VIEW_ACTIONS,
  EXPLORATION_VIEW_API_VERSION,
  EXPLORATION_VIEW_EXPORT_MANIFEST_VERSION,
  EXPLORATION_VIEW_RENDER_VERSION,
  type ExplorationScene,
  type ExplorationStartingPointDto,
  type SceneText,
  type ExplorationFormId,
  type ExplorationTemplateId,
  type ExplorationViewControlDto,
  type ExplorationViewDto,
  type ExplorationViewErrorCode,
  type ExplorationViewExportManifestDto,
  type ExplorationViewResult,
} from "./types.ts";

/* Exploration VIEW v1 — the service over the frozen V2 state machine
   (§7i). It resolves a starting WORD to a governed initial state, tells
   which of the product's three controls are really available in a state,
   moves only along V2's own transitions, and builds the presentation
   (template, variant, seed → scene → SVG). It never adds a term, an
   association or a transition; it never reads V3; the frozen v2
   renderer and its export identities are untouched. */

const SHA256 = /^[0-9a-f]{64}$/u;
const CATEGORY_LABEL: Readonly<Record<ExplorationV2CategoryId, string>> = Object.freeze({
  region: "Region", theme: "Theme", medium: "Medium / format", movement: "Movement context",
});
const TEMPLATE_SET = new Set<string>(EXPLORATION_TEMPLATE_IDS);
const ACTION_SET = new Set<string>(EXPLORATION_VIEW_ACTIONS);

function ok<T>(data: T): ExplorationViewResult<T> {
  return { ok: true, data };
}
function fail<T>(code: ExplorationViewErrorCode, message: string, status: number): ExplorationViewResult<T> {
  return { ok: false, code, message, status };
}
function compare(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0;
}
function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

/* ---- indexes over the frozen model, built once ---- */

interface ViewIndex {
  readonly model: ExplorationV2ReadModel;
  readonly categoryOfEntry: ReadonlyMap<string, ExplorationV2CategoryId>;
  readonly rootStateOfComposition: ReadonlyMap<string, ExplorationV2StateRecord>;
  readonly labelOf: ReadonlyMap<string, string>;
  /* the starting words: seeds of at least one composition, in label order */
  readonly startingPoints: readonly ResolvedStartingPoint[];
  readonly startingPointById: ReadonlyMap<string, ResolvedStartingPoint>;
}

interface ResolvedStartingPoint {
  readonly vocabularyId: string;
  readonly label: string;
  readonly categoryId: ExplorationV2CategoryId;
  readonly compositionIds: readonly string[];
  /* the governed initial state and how it is reached */
  readonly initial: ExplorationV2StateRecord;
  readonly twoStep: boolean;
  readonly expandable: boolean;
}

let cached: ViewIndex | undefined;

function stateKeyOf(state: ExplorationV2StateRecord): string {
  return JSON.stringify([[...state.visible_node_ids].sort(compare), [...state.visible_association_ids].sort(compare), state.focused_node_id]);
}

function buildIndex(): ViewIndex {
  const model = getExplorationV2ReadModel();
  const transitions = getExplorationV2TransitionIndex(model);
  const categoryOfEntry = new Map(model.categories.map((entry) => [entry.category_entry_id, entry.category_id]));
  const labelOf = new Map(model.vocabulary.map((term) => [term.vocabulary_id, term.canonical_label]));
  const rootStateOfComposition = new Map<string, ExplorationV2StateRecord>();
  for (const state of Object.values(model.states)) {
    const composition = model.compositions[state.composition_id];
    if (composition && state.focused_node_id === composition.seed_node_id && state.expanded_node_ids.length === 0) {
      rootStateOfComposition.set(state.composition_id, state);
    }
  }
  const bySeed = new Map<string, string[]>();
  for (const composition of Object.values(model.compositions)) {
    const list = bySeed.get(composition.seed_node_id) ?? [];
    list.push(composition.composition_id);
    bySeed.set(composition.seed_node_id, list);
  }
  const startingPoints: ResolvedStartingPoint[] = [];
  for (const [vocabularyId, compositionIds] of bySeed) {
    compositionIds.sort(compare);
    const categories = new Set(compositionIds.map((id) => categoryOfEntry.get(model.compositions[id]?.category_entry_id ?? "")));
    if (categories.size !== 1) throw new Error("VIEW_INDEX_SEED_SPANS_CATEGORIES");
    const categoryId = [...categories][0] as ExplorationV2CategoryId;
    /* the governed way to each candidate's root: the entry's initial state,
       then SELECT_COMPOSITION when the canonical composition is another */
    const candidates = compositionIds.map((compositionId) => {
      const composition = model.compositions[compositionId];
      const entry = model.categories.find((item) => item.category_entry_id === composition?.category_entry_id);
      const initial = entry ? model.states[entry.initial_state_id] : undefined;
      if (!composition || !entry || !initial) throw new Error("VIEW_INDEX_COMPOSITION_ENTRY");
      const root = initial.composition_id === compositionId
        ? initial
        : transitions.resolve(initial, "SELECT_COMPOSITION", compositionId)?.next_state;
      if (!root) throw new Error("VIEW_INDEX_COMPOSITION_ROOT");
      return { compositionId, root, twoStep: initial.composition_id !== compositionId, expandable: effectiveStep(model, root, "MORE") !== undefined };
    });
    /* prefer a root with a real "more" step; then the stable lowest id */
    const chosen = candidates.find((candidate) => candidate.expandable) ?? candidates[0];
    if (!chosen) continue;
    startingPoints.push({
      vocabularyId,
      label: labelOf.get(vocabularyId) ?? vocabularyId,
      categoryId,
      compositionIds,
      initial: chosen.root,
      twoStep: chosen.twoStep,
      expandable: chosen.expandable,
    });
  }
  startingPoints.sort((left, right) => compare(left.label, right.label));
  return {
    model,
    categoryOfEntry,
    rootStateOfComposition,
    labelOf,
    startingPoints,
    startingPointById: new Map(startingPoints.map((point) => [point.vocabularyId, point])),
  };
}

function index(): ViewIndex {
  cached ??= buildIndex();
  return cached;
}

/* ---- the controls: only a legal V2 transition that changes the visible count ---- */

function effectiveStep(model: ExplorationV2ReadModel, state: ExplorationV2StateRecord, direction: "MORE" | "LESS"): ExplorationV2StateRecord | undefined {
  const transitions = getExplorationV2TransitionIndex(model);
  const action = direction === "MORE" ? "EXPAND_NODE" : "COLLAPSE_NODE";
  if (!state.available_actions.includes(action)) return undefined;
  const current = state.visible_node_ids.length;
  const candidates = [...transitions.targets(state, action)].sort(compare)
    .map((target) => transitions.resolve(state, action, target)?.next_state)
    .filter((next): next is ExplorationV2StateRecord => next !== undefined)
    .filter((next) => (direction === "MORE" ? next.visible_node_ids.length > current : next.visible_node_ids.length < current))
    .sort((left, right) => Math.abs(left.visible_node_ids.length - current) - Math.abs(right.visible_node_ids.length - current) || compare(left.state_id, right.state_id));
  return candidates[0];
}

interface AnotherViewPool {
  readonly roots: readonly ExplorationV2StateRecord[]; /* distinct pictures, composition-id order */
  readonly position: number; /* the current composition's picture in that order */
}

function anotherViewPool(view: ViewIndex, state: ExplorationV2StateRecord): AnotherViewPool {
  const composition = view.model.compositions[state.composition_id];
  if (!composition) throw new Error("VIEW_STATE_COMPOSITION");
  const categoryId = view.categoryOfEntry.get(composition.category_entry_id);
  const seen = new Map<string, ExplorationV2StateRecord>();
  const ordered = Object.values(view.model.compositions)
    .filter((item) => item.seed_node_id === composition.seed_node_id && view.categoryOfEntry.get(item.category_entry_id) === categoryId)
    .sort((left, right) => compare(left.composition_id, right.composition_id));
  for (const item of ordered) {
    const root = view.rootStateOfComposition.get(item.composition_id);
    if (!root) throw new Error("VIEW_POOL_ROOT");
    const key = stateKeyOf(root);
    if (!seen.has(key)) seen.set(key, root);
  }
  const roots = [...seen.values()];
  const currentRoot = view.rootStateOfComposition.get(state.composition_id);
  const position = currentRoot ? roots.findIndex((root) => stateKeyOf(root) === stateKeyOf(currentRoot)) : -1;
  return { roots, position: Math.max(0, position) };
}

function controlsFor(view: ViewIndex, state: ExplorationV2StateRecord): ExplorationViewDto["controls"] {
  const more = effectiveStep(view.model, state, "MORE");
  const less = effectiveStep(view.model, state, "LESS");
  const pool = anotherViewPool(view, state);
  const moreControl: ExplorationViewControlDto = more ? { available: true, next_visible_count: more.visible_node_ids.length } : { available: false, reason: "AT_RICHEST" };
  const lessControl: ExplorationViewControlDto = less ? { available: true, next_visible_count: less.visible_node_ids.length } : { available: false, reason: "AT_SIMPLEST" };
  return {
    more: moreControl,
    less: lessControl,
    another_view: pool.roots.length > 1
      ? { available: true, pool_size: pool.roots.length, position: pool.position }
      : { available: false, reason: "SINGLE_VIEW", pool_size: pool.roots.length, position: pool.position },
  };
}

/* ---- the presentation for a state ---- */

function startingPointOfState(view: ViewIndex, state: ExplorationV2StateRecord): ResolvedStartingPoint {
  const composition = view.model.compositions[state.composition_id];
  const point = composition ? view.startingPointById.get(composition.seed_node_id) : undefined;
  if (!point) throw new Error("VIEW_STATE_STARTING_POINT");
  return point;
}

function exportIdentity(map: ExplorationV2MapDto, templateId: ExplorationTemplateId, variantId: number, seed: number): { readonly hash: string; readonly exportId: string } {
  const identity = {
    api_version: EXPLORATION_VIEW_API_VERSION,
    presentation_version: EXPLORATION_PRESENTATION_VERSION,
    render_version: EXPLORATION_VIEW_RENDER_VERSION,
    database_snapshot: map.database_snapshot,
    state_hash: map.state.state_hash,
    state_presentation_hash: map.state.presentation_hash,
    composition_id: map.composition.composition_id,
    template_id: templateId,
    variant_id: variantId,
    presentation_seed: seed,
    form_id: EXPLORATION_FORM_OF_TEMPLATE[templateId],
  };
  const hash = createHash("sha256").update(JSON.stringify(identity, Object.keys(identity).sort()), "utf8").digest("hex");
  return { hash, exportId: `TEP1-${hash.slice(0, 24)}` };
}

function viewFor(view: ViewIndex, state: ExplorationV2StateRecord, templateId: ExplorationTemplateId, variantId: number): ExplorationViewDto {
  const map = deriveExplorationV2Map(view.model, state);
  const content = sceneContentFromMap(map);
  const compatible = getCompatibleTemplates(content);
  const point = startingPointOfState(view, state);
  const seed = presentationSeed(map.state.state_hash, `${templateId}:${variantId}`);
  const scene = buildExplorationScene(content, templateId, variantId, seed);
  const formId = EXPLORATION_FORM_OF_TEMPLATE[templateId];
  return {
    api_version: EXPLORATION_VIEW_API_VERSION,
    database_snapshot: map.database_snapshot,
    starting_point: { vocabulary_id: point.vocabularyId, label: point.label, category_id: point.categoryId, category_label: CATEGORY_LABEL[point.categoryId] },
    map,
    controls: controlsFor(view, state),
    presentation: {
      presentation_version: EXPLORATION_PRESENTATION_VERSION,
      template_id: templateId,
      template_name: EXPLORATION_TEMPLATE_NAMES[templateId],
      variant_id: variantId,
      variant_name: scene.variantName,
      presentation_seed: seed,
      palette_id: scene.palette.id,
      compatible_templates: compatible,
      form_id: formId,
      form_name: EXPLORATION_FORM_NAMES[formId],
      form_dimensions: { width: STAMP_FORMS[formId].width * EXPORT_SCALE, height: STAMP_FORMS[formId].height * EXPORT_SCALE },
    },
    scene,
    svg: renderExplorationViewSvg(scene),
    restore: { map_id: map.map_id, state_id: map.state.state_id, state_hash: map.state.state_hash, template_id: templateId, variant_id: variantId },
  };
}

function defaultPresentation(state: ExplorationV2StateRecord, map: ExplorationV2MapDto): { templateId: ExplorationTemplateId; variantId: number } {
  const compatible = getCompatibleTemplates(sceneContentFromMap(map));
  const seed = presentationSeed(state.state_hash, "initial");
  const templateId = selectPresentationTemplate(seed, compatible);
  return { templateId, variantId: selectPresentationVariant(seed, templateId) };
}

function validPresentation(templateId: unknown, variantId: unknown): templateId is ExplorationTemplateId {
  return typeof templateId === "string" && TEMPLATE_SET.has(templateId)
    && typeof variantId === "number" && Number.isInteger(variantId) && variantId >= 0
    && variantId < EXPLORATION_TEMPLATE_VARIANTS[templateId as ExplorationTemplateId].length;
}

/* ---- the public service ---- */

export function listExplorationStartingPoints(): ExplorationViewResult<{ readonly api_version: typeof EXPLORATION_VIEW_API_VERSION; readonly database_snapshot: string; readonly starting_points: readonly ExplorationStartingPointDto[] }> {
  const view = index();
  return ok({
    api_version: EXPLORATION_VIEW_API_VERSION,
    database_snapshot: view.model.database.database_snapshot_id,
    starting_points: view.startingPoints.map((point) => ({
      vocabulary_id: point.vocabularyId,
      label: point.label,
      category_id: point.categoryId,
      category_label: CATEGORY_LABEL[point.categoryId],
      composition_count: point.compositionIds.length,
      expandable: point.expandable,
      two_step: point.twoStep,
    })),
  });
}

export function getDefaultStartingPointId(): string {
  /* the largest governed pool, deterministically: most compositions, then label (design diplomacy) */
  const view = index();
  const sorted = [...view.startingPoints].sort((l, r) => r.compositionIds.length - l.compositionIds.length || compare(l.label, r.label));
  return sorted[0]?.vocabularyId ?? "";
}

export function createExplorationView(request: unknown): ExplorationViewResult<ExplorationViewDto> {
  if (!isRecord(request) || typeof request.vocabulary_id !== "string") return fail("INVALID_REQUEST", "A starting point is required.", 400);
  const view = index();
  const point = view.startingPointById.get(request.vocabulary_id);
  if (!point) return fail("INVALID_STARTING_POINT", "The requested word is not a governed starting point.", 404);
  const map = deriveExplorationV2Map(view.model, point.initial);
  if ((request.template_id !== undefined || request.variant_id !== undefined) && !validPresentation(request.template_id, request.variant_id)) return fail("INVALID_PRESENTATION", "The template or variant is not one of the presentation's.", 400);
  const chosen = request.template_id !== undefined
    ? { templateId: request.template_id as ExplorationTemplateId, variantId: request.variant_id as number }
    : defaultPresentation(point.initial, map);
  try {
    return ok(viewFor(view, point.initial, chosen.templateId, chosen.variantId));
  } catch {
    return fail("INTERNAL_DATA_INTEGRITY_FAILURE", "The governed initial view could not be built.", 503);
  }
}

export function retrieveExplorationView(mapId: string, stateId: string | undefined, templateId: string | undefined, variantId: number | undefined): ExplorationViewResult<ExplorationViewDto> {
  const view = index();
  if (!getExplorationV2CategoryByEntry(mapId)) return fail("STATE_NOT_FOUND", "The requested map does not exist.", 404);
  const entry = view.model.categories.find((item) => item.category_entry_id === mapId);
  const state = view.model.states[stateId ?? entry?.initial_state_id ?? ""];
  if (!state || state.category_entry_id !== mapId) return fail("STATE_NOT_FOUND", "The requested state does not belong to this map.", 404);
  const map = deriveExplorationV2Map(view.model, state);
  /* no presentation asked: the deterministic default; a presentation asked: it must be legal — never a silent substitute */
  if ((templateId !== undefined || variantId !== undefined) && !validPresentation(templateId, variantId ?? Number.NaN)) return fail("INVALID_PRESENTATION", "The template or variant is not one of the presentation's.", 400);
  const chosen = templateId !== undefined
    ? { templateId: templateId as ExplorationTemplateId, variantId: variantId as number }
    : defaultPresentation(state, map);
  if (!getCompatibleTemplates(sceneContentFromMap(map)).includes(chosen.templateId)) return fail("INVALID_PRESENTATION", "The template cannot present this view.", 400);
  try {
    return ok(viewFor(view, state, chosen.templateId, chosen.variantId));
  } catch {
    return fail("INTERNAL_DATA_INTEGRITY_FAILURE", "The governed view could not be built.", 503);
  }
}

export function applyExplorationViewAction(mapId: string, request: unknown): ExplorationViewResult<ExplorationViewDto> {
  if (!isRecord(request) || typeof request.action !== "string" || !ACTION_SET.has(request.action)) return fail("INVALID_ACTION", "The requested action is not one of the view's controls.", 400);
  if (typeof request.expected_state_hash !== "string" || !SHA256.test(request.expected_state_hash)) return fail("INVALID_REQUEST", "A valid expected state hash is required.", 400);
  if (!validPresentation(request.template_id, request.variant_id)) return fail("INVALID_PRESENTATION", "A valid template and variant are required.", 400);
  const view = index();
  if (!getExplorationV2CategoryByEntry(mapId)) return fail("STATE_NOT_FOUND", "The requested map does not exist.", 404);
  const stateId = view.model.states_by_hash[request.expected_state_hash];
  const state = stateId ? view.model.states[stateId] : undefined;
  if (!state || state.category_entry_id !== mapId) return fail("STALE_EXPLORATION_STATE", "The expected state is stale or belongs to another map.", 409);
  const templateId = request.template_id as ExplorationTemplateId;
  const variantId = request.variant_id as number;
  let next: ExplorationV2StateRecord | undefined;
  let presentation = { templateId, variantId };
  if (request.action === "MORE" || request.action === "LESS") {
    next = effectiveStep(view.model, state, request.action);
    if (!next) return fail("ACTION_NOT_AVAILABLE", request.action === "MORE" ? "This view is at its richest." : "This view is at its simplest.", 409);
  } else {
    const pool = anotherViewPool(view, state);
    if (pool.roots.length <= 1) return fail("ACTION_NOT_AVAILABLE", "This starting point has a single view.", 409);
    next = pool.roots[(pool.position + 1) % pool.roots.length];
    if (!next) return fail("INTERNAL_DATA_INTEGRITY_FAILURE", "The next view is unavailable.", 503);
    /* a new composition, and the next compatible treatment */
    const compatible = getCompatibleTemplates(sceneContentFromMap(deriveExplorationV2Map(view.model, next)));
    const nextTemplateId = compatible.includes(templateId) ? nextTemplate(templateId, compatible) : selectPresentationTemplate(presentationSeed(next.state_hash, "another"), compatible);
    presentation = { templateId: nextTemplateId, variantId: selectPresentationVariant(presentationSeed(next.state_hash, `another:${nextTemplateId}`), nextTemplateId) };
  }
  /* More / Less keep the treatment while it can present the new count */
  const nextMap = deriveExplorationV2Map(view.model, next);
  const compatible = getCompatibleTemplates(sceneContentFromMap(nextMap));
  if (!compatible.includes(presentation.templateId)) {
    const fallback = selectPresentationTemplate(presentationSeed(next.state_hash, "fallback"), compatible);
    presentation = { templateId: fallback, variantId: selectPresentationVariant(presentationSeed(next.state_hash, `fallback:${fallback}`), fallback) };
  }
  try {
    return ok(viewFor(view, next, presentation.templateId, presentation.variantId));
  } catch {
    return fail("INTERNAL_DATA_INTEGRITY_FAILURE", "The governed view could not be built.", 503);
  }
}

export function createExplorationViewExportManifest(request: unknown): ExplorationViewResult<{ readonly manifest: ExplorationViewExportManifestDto; readonly scene: ExplorationScene; readonly furniture: readonly SceneText[] }> {
  if (!isRecord(request)) return fail("INVALID_REQUEST", "A valid export request is required.", 400);
  const { map_id: mapId, state_hash: stateHash, composition_id: compositionId } = request;
  if (typeof mapId !== "string" || !getExplorationV2CategoryByEntry(mapId)) return fail("STATE_NOT_FOUND", "The export map does not exist.", 404);
  if (typeof stateHash !== "string" || !SHA256.test(stateHash)) return fail("INVALID_REQUEST", "A valid export state hash is required.", 400);
  if (typeof compositionId !== "string") return fail("INVALID_REQUEST", "A valid export composition identifier is required.", 400);
  if (!validPresentation(request.template_id, request.variant_id)) return fail("INVALID_PRESENTATION", "A valid template and variant are required.", 400);
  const view = index();
  const stateId = view.model.states_by_hash[stateHash];
  const state = stateId ? view.model.states[stateId] : undefined;
  if (!state || state.category_entry_id !== mapId) return fail("STALE_EXPLORATION_STATE", "The export state is stale or belongs to another map.", 409);
  if (state.composition_id !== compositionId || !state.available_actions.includes("EXPORT_CURRENT_STATE")) return fail("ACTION_NOT_AVAILABLE", "The requested composition is not the state's own.", 409);
  const templateId = request.template_id as ExplorationTemplateId;
  const variantId = request.variant_id as number;
  const map = deriveExplorationV2Map(view.model, state);
  const content = sceneContentFromMap(map);
  if (!getCompatibleTemplates(content).includes(templateId)) return fail("INVALID_PRESENTATION", "The template cannot present this view.", 400);
  const point = startingPointOfState(view, state);
  const seed = presentationSeed(map.state.state_hash, `${templateId}:${variantId}`);
  const identity = exportIdentity(map, templateId, variantId, seed);
  const formId = EXPLORATION_FORM_OF_TEMPLATE[templateId];
  const form = STAMP_FORMS[formId];
  /* the same template, variant and seed, laid out for the form's image area */
  const scene = buildExplorationScene(content, templateId, variantId, seed, form.image);
  const furniture = form.furniture({
    seedLabel: content.seedLabel,
    termCount: content.termCount,
    associationCount: content.associationCount,
    categoryLabel: content.categoryLabel,
    exportId: identity.exportId,
    terms: content.nodes.map((node) => node.label),
    associations: map.associations.map((item) => [item.endpoint_labels[0], item.endpoint_labels[1]] as const),
    templateName: EXPLORATION_TEMPLATE_NAMES[templateId],
    variantName: scene.variantName,
  });
  const externally = map.associations.filter((item) => item.support_status === "ACTIVE_EXTERNALLY_SUPPORTED").length;
  const manifest: ExplorationViewExportManifestDto = {
    manifest_version: EXPLORATION_VIEW_EXPORT_MANIFEST_VERSION,
    api_version: EXPLORATION_VIEW_API_VERSION,
    presentation_version: EXPLORATION_PRESENTATION_VERSION,
    render_version: EXPLORATION_VIEW_RENDER_VERSION,
    export_id: identity.exportId,
    database_snapshot: map.database_snapshot,
    map_id: map.map_id,
    state_id: map.state.state_id,
    state_hash: map.state.state_hash,
    semantic_hash: map.state.semantic_hash,
    state_presentation_hash: map.state.presentation_hash,
    composition_id: map.composition.composition_id,
    seed_node_id: map.composition.seed_node_id,
    template_id: templateId,
    variant_id: variantId,
    variant_name: scene.variantName,
    presentation_seed: seed,
    seed_chain: scene.seedChain,
    palette_id: scene.palette.id,
    form_id: formId,
    form_name: EXPLORATION_FORM_NAMES[formId],
    dimensions: { width: form.width * EXPORT_SCALE, height: form.height * EXPORT_SCALE },
    starting_point: { vocabulary_id: point.vocabularyId, label: point.label, category_id: point.categoryId },
    nodes: map.nodes.map((node) => ({ vocabulary_id: node.vocabulary_id, canonical_label: node.canonical_label, focused: node.focused })),
    associations: map.associations,
    plain_text_tree: map.plain_text_tree.plain_text_tree,
    node_count: map.nodes.length,
    association_count: map.associations.length,
    provenance_summary: {
      association_count: map.associations.length,
      externally_supported_count: externally,
      source_supported_count: map.associations.length - externally,
      generic_association_only: true,
      source_locators_withheld_from_public_export: true,
      presentation_is_semantics_free: true,
    },
    export_alt_text: scene.altText,
    suggested_filename: `mgda-exploration-${point.label.replace(/[^a-z0-9]+/giu, "-").toLowerCase()}-${templateId.toLowerCase()}-${formId.toLowerCase()}-${map.state.state_hash.slice(0, 8)}.png`,
  };
  return ok({ manifest, scene, furniture });
}

/* the export's SVG: the form around the picture */
export function renderExplorationExport(scene: ExplorationScene, formId: ExplorationFormId, furniture: readonly SceneText[]): string {
  return renderExplorationExportSvg(scene, formId, furniture);
}
