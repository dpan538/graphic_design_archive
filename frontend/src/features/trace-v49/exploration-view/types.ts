/* Exploration VIEW v1 — the product layer over the frozen Exploration V2
   state machine (FRONTEND_DESIGN_DECISION.md §7i). Two states, kept apart:

   CONTENT STATE  — V2's: starting vocabulary, composition, visible terms,
                    associations, complexity (visible term count), focus.
                    Never touched here.
   PRESENTATION   — a template, a variant, a seed: how the same content is
                    drawn. Semantics-free by contract: no colour, size,
                    length or position means confidence, importance,
                    chronology or direction.

   The page and the PNG share one scene: a template is a layout function
   over the content (slots, anchors, connector routes, text regions,
   decorative regions), the renderer draws that scene once, identically. */

import type {
  ExplorationV2AssociationDto,
  ExplorationV2CategoryId,
  ExplorationV2MapDto,
} from "../exploration-v2/types.ts";

export const EXPLORATION_VIEW_API_VERSION = "trace-exploration-view/v1" as const;
export const EXPLORATION_PRESENTATION_VERSION = "trace-exploration-presentation-v1" as const;
export const EXPLORATION_VIEW_EXPORT_MANIFEST_VERSION = "trace-exploration-view-export-manifest-v1" as const;
export const EXPLORATION_VIEW_RENDER_VERSION = "trace-exploration-stamp-png-v1" as const;

/* the eight presentation templates — spatial logics, not data structures */
export const EXPLORATION_TEMPLATE_IDS = [
  "DOTS",
  "SPOTS",
  "CHEVRON",
  "CROSSFIELD",
  "LINES",
  "GRID",
  "RAYS",
  "OVERLAP",
  "HALFTONE",
  "STRIPES",
  "PETALS",
  "WAVES",
  "CUBES",
  "ARCS",
  "MOIRE",
  "SCATTER",
] as const;
export type ExplorationTemplateId = (typeof EXPLORATION_TEMPLATE_IDS)[number];

/* each template's variants — orientation / arrangement, named for the record */
/* each template's three variants are STRUCTURAL — a different skeleton family,
   a different way of drawing the associations, a different density — never a
   colour swap alone */
export const EXPLORATION_TEMPLATE_VARIANTS: Readonly<Record<ExplorationTemplateId, readonly string[]>> = Object.freeze({
  DOTS: ["rows", "columns", "diagonal"],
  SPOTS: ["lattice", "drift", "cluster"],
  CHEVRON: ["two flags", "nested", "stacked"],
  CROSSFIELD: ["figure", "corridor", "halo"],
  LINES: ["vertical", "horizontal", "woven"],
  GRID: ["blocks", "rings", "bars"],
  RAYS: ["full", "fan", "split"],
  OVERLAP: ["diagonal", "stacked", "scattered"],
  HALFTONE: ["radial", "linear", "ring"],
  STRIPES: ["diagonal", "vertical", "fan"],
  PETALS: ["flower", "ring", "spray"],
  WAVES: ["horizontal", "vertical", "crossing"],
  CUBES: ["lattice", "stack", "scatter"],
  ARCS: ["nested", "opposed", "spiral"],
  MOIRE: ["cross", "radial", "offset"],
  SCATTER: ["bokeh", "beam", "field"],
});

export const EXPLORATION_TEMPLATE_NAMES: Readonly<Record<ExplorationTemplateId, string>> = Object.freeze({
  DOTS: "Dot rows",
  SPOTS: "Spots",
  CHEVRON: "Chevron bands",
  CROSSFIELD: "Cross field",
  LINES: "Lines and bars",
  GRID: "Modular grid",
  RAYS: "Rays",
  OVERLAP: "Overlap",
  HALFTONE: "Halftone",
  STRIPES: "Stripes",
  PETALS: "Petals",
  WAVES: "Waves",
  CUBES: "Cubes",
  ARCS: "Arcs",
  MOIRE: "Moiré",
  SCATTER: "Scatter",
});

/* the export forms: the five reference stamps, replicated in form, carrying
   the archive's identity; every template is matched to one */
export const EXPLORATION_FORM_IDS = ["FRANCE", "SOUTH_AFRICA", "GERMANY", "CANADA", "SWEDEN"] as const;
export type ExplorationFormId = (typeof EXPLORATION_FORM_IDS)[number];
export const EXPLORATION_FORM_NAMES: Readonly<Record<ExplorationFormId, string>> = Object.freeze({
  FRANCE: "Télévision 1985",
  SOUTH_AFRICA: "R10 spots",
  GERMANY: "Treaty 1973",
  CANADA: "Vancouver 1983",
  SWEDEN: "Streaming 2026",
});
export const EXPLORATION_FORM_OF_TEMPLATE: Readonly<Record<ExplorationTemplateId, ExplorationFormId>> = Object.freeze({
  DOTS: "FRANCE", OVERLAP: "FRANCE", ARCS: "FRANCE",
  SPOTS: "SOUTH_AFRICA", PETALS: "SOUTH_AFRICA", SCATTER: "SOUTH_AFRICA",
  CHEVRON: "GERMANY", GRID: "GERMANY", STRIPES: "GERMANY", CUBES: "GERMANY",
  CROSSFIELD: "CANADA", RAYS: "CANADA", HALFTONE: "CANADA",
  LINES: "SWEDEN", WAVES: "SWEDEN", MOIRE: "SWEDEN",
});

/* the view's controls: the only actions the product exposes */
export const EXPLORATION_VIEW_ACTIONS = ["MORE", "LESS", "ANOTHER_VIEW"] as const;
export type ExplorationViewAction = (typeof EXPLORATION_VIEW_ACTIONS)[number];

/* ---- the scene: pure graphic ---- */

export interface Frame { readonly x: number; readonly y: number; readonly width: number; readonly height: number }

/* the VIEW's frame: a full portrait picture, no paper, no furniture */
export const VIEW_FRAME: Frame = Object.freeze({ x: 0, y: 0, width: 840, height: 1120 });

export interface ScenePalette {
  readonly id: string;
  readonly paper: string;
  readonly ground: string;
  readonly ink: string;
  /* the template's inks, in the order its layout uses them */
  readonly colours: readonly string[];
}

/* a term's place in the picture: a motif the template chose, no label */
export interface SceneNode {
  readonly index: number;
  readonly vocabularyId: string;
  readonly focused: boolean;
  readonly seed: boolean;
  readonly anchor: { readonly x: number; readonly y: number };
  readonly region: { readonly x: number; readonly y: number; readonly width: number; readonly height: number };
}

/* an association's place in the picture: the shapes that carry it */
export interface SceneConnector {
  readonly associationId: string;
  readonly from: number;
  readonly to: number;
  readonly region: { readonly x: number; readonly y: number; readonly width: number; readonly height: number };
}

/* definitions the primitives may reference by url(#id): gradients and the grain */
export type SceneDef =
  | { readonly kind: "linear"; readonly id: string; readonly x1: number; readonly y1: number; readonly x2: number; readonly y2: number; readonly stops: readonly { readonly offset: number; readonly colour: string; readonly opacity?: number }[] }
  | { readonly kind: "radial"; readonly id: string; readonly cx: number; readonly cy: number; readonly r: number; readonly stops: readonly { readonly offset: number; readonly colour: string; readonly opacity?: number }[] }
  | { readonly kind: "grain"; readonly id: string; readonly baseFrequency: number; readonly octaves: number; readonly seed: number; readonly opacity: number };

/* decorations flagged clip are cut to the frame */
export type SceneDecoration = { readonly clip?: boolean; readonly role?: "field" | "term" | "association" | "texture" } & (
  | { readonly kind: "rect"; readonly x: number; readonly y: number; readonly width: number; readonly height: number; readonly fill: string; readonly stroke?: string; readonly strokeWidth?: number; readonly rotate?: number; readonly opacity?: number }
  | { readonly kind: "circle"; readonly cx: number; readonly cy: number; readonly r: number; readonly fill: string; readonly stroke?: string; readonly strokeWidth?: number; readonly opacity?: number }
  | { readonly kind: "line"; readonly x1: number; readonly y1: number; readonly x2: number; readonly y2: number; readonly stroke: string; readonly width: number; readonly opacity?: number }
  | { readonly kind: "polygon"; readonly points: readonly { readonly x: number; readonly y: number }[]; readonly fill: string; readonly stroke?: string; readonly strokeWidth?: number; readonly opacity?: number }
  | { readonly kind: "path"; readonly d: string; readonly fill: string; readonly stroke?: string; readonly strokeWidth?: number; readonly opacity?: number }
  | { readonly kind: "cross"; readonly cx: number; readonly cy: number; readonly size: number; readonly stroke: string; readonly width: number; readonly opacity?: number }
);

/* the export form's furniture — the small text the reference stamps carry,
   never drawn in the view */
export interface SceneText {
  readonly role: "caption" | "denomination" | "denomination-word" | "issuer" | "meta" | "title";
  readonly text: string;
  readonly x: number;
  readonly y: number;
  readonly size: number;
  readonly anchor: "start" | "middle" | "end";
  readonly weight: 300 | 400 | 700;
  readonly font: "sans" | "serif" | "mono";
  readonly colour: string;
  readonly letterSpacing?: number;
  readonly rotate?: number;
}

export interface ExplorationScene {
  readonly presentationVersion: typeof EXPLORATION_PRESENTATION_VERSION;
  readonly templateId: ExplorationTemplateId;
  readonly variantId: number;
  readonly variantName: string;
  readonly presentationSeed: number;
  /* the seed's derivation, for the record: state hash → salt → picks */
  readonly seedChain: readonly string[];
  readonly palette: ScenePalette;
  /* the frame the picture was laid out in */
  readonly frame: Frame;
  /* the frame's own ground, painted by the template */
  readonly fieldFill: string;
  readonly defs: readonly SceneDef[];
  readonly nodes: readonly SceneNode[];
  readonly connectors: readonly SceneConnector[];
  readonly decorations: readonly SceneDecoration[];
  readonly altText: string;
}

/* ---- the content the templates lay out (derived from the V2 map) ---- */

export interface SceneContent {
  readonly nodes: readonly { readonly vocabularyId: string; readonly label: string; readonly focused: boolean; readonly seed: boolean }[];
  readonly edges: readonly { readonly associationId: string; readonly from: number; readonly to: number }[];
  readonly seedLabel: string;
  readonly categoryId: ExplorationV2CategoryId;
  readonly categoryLabel: string;
  readonly topologyFamily: string;
  readonly termCount: number;
  readonly associationCount: number;
  /* the state's semantic hash: names the spatial field the skeleton is bent by */
  readonly semanticHash: string;
}

/* ---- DTOs ---- */

export interface ExplorationStartingPointDto {
  readonly vocabulary_id: string;
  readonly label: string;
  readonly category_id: ExplorationV2CategoryId;
  readonly category_label: string;
  readonly composition_count: number;
  /* whether the resolved initial view has a real "more" step */
  readonly expandable: boolean;
  /* whether reaching it takes a governed SELECT_COMPOSITION after the map's initial state */
  readonly two_step: boolean;
}

export interface ExplorationViewControlDto {
  readonly available: boolean;
  /* why not, when not — the view's own boundary, never the starting point's */
  readonly reason?: "AT_RICHEST" | "AT_SIMPLEST" | "SINGLE_VIEW";
  readonly next_visible_count?: number;
}

export interface ExplorationViewPresentationDto {
  readonly presentation_version: typeof EXPLORATION_PRESENTATION_VERSION;
  readonly template_id: ExplorationTemplateId;
  readonly template_name: string;
  readonly variant_id: number;
  readonly variant_name: string;
  readonly presentation_seed: number;
  readonly palette_id: string;
  readonly compatible_templates: readonly ExplorationTemplateId[];
  readonly form_id: ExplorationFormId;
  readonly form_name: string;
  readonly form_dimensions: { readonly width: number; readonly height: number };
}

export interface ExplorationViewDto {
  readonly api_version: typeof EXPLORATION_VIEW_API_VERSION;
  readonly database_snapshot: string;
  readonly starting_point: { readonly vocabulary_id: string; readonly label: string; readonly category_id: ExplorationV2CategoryId; readonly category_label: string };
  readonly map: ExplorationV2MapDto;
  readonly controls: {
    readonly more: ExplorationViewControlDto;
    readonly less: ExplorationViewControlDto;
    readonly another_view: ExplorationViewControlDto & { readonly pool_size: number; readonly position: number };
  };
  readonly presentation: ExplorationViewPresentationDto;
  readonly scene: ExplorationScene;
  readonly svg: string;
  readonly restore: { readonly map_id: string; readonly state_id: string; readonly state_hash: string; readonly template_id: ExplorationTemplateId; readonly variant_id: number };
}

export interface ExplorationViewActionRequest {
  readonly action: ExplorationViewAction;
  readonly expected_state_hash: string;
  readonly template_id: ExplorationTemplateId;
  readonly variant_id: number;
}

export interface ExplorationViewExportRequest {
  readonly map_id: string;
  readonly state_hash: string;
  readonly composition_id: string;
  readonly template_id: ExplorationTemplateId;
  readonly variant_id: number;
}

export interface ExplorationViewExportManifestDto {
  readonly manifest_version: typeof EXPLORATION_VIEW_EXPORT_MANIFEST_VERSION;
  readonly api_version: typeof EXPLORATION_VIEW_API_VERSION;
  readonly presentation_version: typeof EXPLORATION_PRESENTATION_VERSION;
  readonly render_version: typeof EXPLORATION_VIEW_RENDER_VERSION;
  readonly export_id: string;
  readonly database_snapshot: string;
  readonly map_id: string;
  readonly state_id: string;
  readonly state_hash: string;
  readonly semantic_hash: string;
  readonly state_presentation_hash: string;
  readonly composition_id: string;
  readonly seed_node_id: string;
  readonly template_id: ExplorationTemplateId;
  readonly variant_id: number;
  readonly variant_name: string;
  readonly presentation_seed: number;
  readonly seed_chain: readonly string[];
  readonly palette_id: string;
  readonly form_id: ExplorationFormId;
  readonly form_name: string;
  readonly dimensions: { readonly width: number; readonly height: number };
  readonly starting_point: { readonly vocabulary_id: string; readonly label: string; readonly category_id: ExplorationV2CategoryId };
  readonly nodes: readonly { readonly vocabulary_id: string; readonly canonical_label: string; readonly focused: boolean }[];
  readonly associations: readonly ExplorationV2AssociationDto[];
  readonly plain_text_tree: string;
  readonly node_count: number;
  readonly association_count: number;
  readonly provenance_summary: {
    readonly association_count: number;
    readonly externally_supported_count: number;
    readonly source_supported_count: number;
    readonly generic_association_only: true;
    readonly source_locators_withheld_from_public_export: true;
    readonly presentation_is_semantics_free: true;
  };
  readonly export_alt_text: string;
  readonly suggested_filename: string;
}

export type ExplorationViewErrorCode =
  | "INVALID_REQUEST"
  | "INVALID_STARTING_POINT"
  | "INVALID_ACTION"
  | "ACTION_NOT_AVAILABLE"
  | "STALE_EXPLORATION_STATE"
  | "STATE_NOT_FOUND"
  | "INVALID_PRESENTATION"
  | "METHOD_NOT_ALLOWED"
  | "REQUEST_LIMIT_EXCEEDED"
  | "INTERNAL_DATA_INTEGRITY_FAILURE";

export interface ExplorationViewApiError {
  readonly schema_version: "trace-exploration-view-api-error-v1";
  readonly api_version: typeof EXPLORATION_VIEW_API_VERSION;
  readonly code: ExplorationViewErrorCode;
  readonly message: string;
  readonly status: number;
}

export type ExplorationViewResult<T> =
  | { readonly ok: true; readonly data: T }
  | { readonly ok: false; readonly code: ExplorationViewErrorCode; readonly message: string; readonly status: number };
