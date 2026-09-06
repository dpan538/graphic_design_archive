/* The sixteen presentation templates (§7i, second engine) — pure graphic.
   Every template draws the same three things in its own idiom: the TERMS
   as motifs at the positions the structural engine gives them (skeleton →
   semantic field → seed jitter; skeleton.ts), the ASSOCIATIONS as shapes
   the two motifs share, drawn in the variant's connection mode, and a
   FIELD — the idiom's texture — that responds to the motifs (denser, larger,
   warmer near them). Gradients and grain are part of the idiom, as in the
   reference stamps. No word is drawn. Nothing reads confidence, strength,
   support status or evidence. Same content, template, variant and seed →
   the same scene, byte for byte. Layouts take the frame they draw in, so
   the view and every export form lay the picture out for their own area. */

import type { ExplorationV2MapDto } from "../exploration-v2/types.ts";
import { presentationSeed } from "./seed.ts";
import { pick, termPositions, unit, type Point } from "./skeleton.ts";
import {
  EXPLORATION_PRESENTATION_VERSION,
  EXPLORATION_TEMPLATE_IDS,
  EXPLORATION_TEMPLATE_NAMES,
  EXPLORATION_TEMPLATE_VARIANTS,
  VIEW_FRAME,
  type ExplorationScene,
  type ExplorationTemplateId,
  type Frame,
  type SceneConnector,
  type SceneContent,
  type SceneDecoration,
  type SceneDef,
  type SceneNode,
  type ScenePalette,
} from "./types.ts";

export { presentationSeed } from "./seed.ts";

const PAPER = "#f7f5ef";
const GROUND = "#f2f0eb";
const INK = "#161514";

type Box = { readonly x: number; readonly y: number; readonly width: number; readonly height: number };
type Edge = SceneContent["edges"][number];
interface Layout {
  readonly palette: ScenePalette;
  readonly fieldFill: string;
  readonly defs: SceneDef[];
  readonly nodes: SceneNode[];
  readonly connectors: SceneConnector[];
  readonly decorations: SceneDecoration[];
}
interface Input {
  readonly content: SceneContent;
  readonly variant: number;
  readonly seed: number;
  readonly frame: Frame;
  readonly points: Point[];
  readonly semanticHash: string;
}

const r1 = (value: number) => Math.round(value * 10) / 10;
const pt = (x: number, y: number): Point => ({ x: r1(x), y: r1(y) });
const box = (x: number, y: number, width: number, height: number): Box => ({ x: r1(x), y: r1(y), width: r1(width), height: r1(height) });

/* ---- the content, read from the V2 map (tree order, focused first) ---- */

export function sceneContentFromMap(map: ExplorationV2MapDto): SceneContent {
  const order = map.plain_text_tree.tree_node_ids;
  const byId = new Map(map.nodes.map((node) => [node.vocabulary_id, node]));
  const nodes = order.map((id) => {
    const node = byId.get(id);
    if (!node) throw new Error("SCENE_CONTENT_NODE_MISSING");
    return { vocabularyId: id, label: node.canonical_label, focused: node.focused, seed: id === map.composition.seed_node_id };
  });
  const indexOf = new Map(order.map((id, index) => [id, index]));
  const edges = map.associations.map((association) => {
    const [left, right] = association.endpoint_vocabulary_ids;
    const from = indexOf.get(left);
    const to = indexOf.get(right);
    if (from === undefined || to === undefined) throw new Error("SCENE_CONTENT_EDGE_OUTSIDE_VIEW");
    return { associationId: association.association_id, from: Math.min(from, to), to: Math.max(from, to) };
  }).sort((l, r) => l.from - r.from || l.to - r.to || (l.associationId < r.associationId ? -1 : 1));
  const seedNode = map.nodes.find((node) => node.vocabulary_id === map.composition.seed_node_id);
  return {
    nodes,
    edges,
    seedLabel: seedNode?.canonical_label ?? nodes[0]?.label ?? "",
    categoryId: map.category.category_id,
    categoryLabel: map.category.label,
    topologyFamily: map.composition.topology_family,
    termCount: nodes.length,
    associationCount: edges.length,
    semanticHash: map.state.semantic_hash,
  };
}

/* ---- compatibility and selection ---- */

export function getCompatibleTemplates(content: SceneContent): readonly ExplorationTemplateId[] {
  const count = content.nodes.length;
  if (count < 1 || count > 8) return [];
  return [...EXPLORATION_TEMPLATE_IDS];
}

export function selectPresentationTemplate(seed: number, compatible: readonly ExplorationTemplateId[]): ExplorationTemplateId {
  if (compatible.length === 0) throw new Error("NO_COMPATIBLE_TEMPLATE");
  return compatible[seed % compatible.length] as ExplorationTemplateId;
}

export function selectPresentationVariant(seed: number, templateId: ExplorationTemplateId): number {
  const variants = EXPLORATION_TEMPLATE_VARIANTS[templateId];
  return Math.floor(seed / 256) % variants.length;
}

export function nextTemplate(current: ExplorationTemplateId, compatible: readonly ExplorationTemplateId[]): ExplorationTemplateId {
  const index = compatible.indexOf(current);
  return compatible[(index + 1) % compatible.length] as ExplorationTemplateId;
}

/* ---- helpers ---- */

function palette(id: string, colours: readonly string[], paper = PAPER, ink = INK): ScenePalette {
  return { id, paper, ground: GROUND, ink, colours };
}
function clampToFrame(region: Box, F: Frame): Box {
  const x = Math.max(F.x, region.x);
  const y = Math.max(F.y, region.y);
  const right = Math.min(F.x + F.width, region.x + region.width);
  const bottom = Math.min(F.y + F.height, region.y + region.height);
  return box(x, y, Math.max(0, right - x), Math.max(0, bottom - y));
}
function nodeAt(index: number, content: SceneContent, anchor: Point, region: Box, F: Frame): SceneNode {
  const source = content.nodes[index];
  if (!source) throw new Error("SCENE_NODE_INDEX");
  const clamped = pt(Math.min(F.x + F.width - 1, Math.max(F.x + 1, anchor.x)), Math.min(F.y + F.height - 1, Math.max(F.y + 1, anchor.y)));
  return { index, vocabularyId: source.vocabularyId, focused: source.focused, seed: source.seed, anchor: clamped, region: clampToFrame(region, F) };
}
function link(edge: Edge, region: Box, F: Frame): SceneConnector {
  return { associationId: edge.associationId, from: edge.from, to: edge.to, region: clampToFrame(region, F) };
}
function segmentBox(a: Point, b: Point, pad: number): Box {
  return box(Math.min(a.x, b.x) - pad, Math.min(a.y, b.y) - pad, Math.abs(a.x - b.x) + pad * 2, Math.abs(a.y - b.y) + pad * 2);
}
function linear(id: string, from: string, to: string, angle: number, mid?: string): SceneDef {
  const rad = (angle * Math.PI) / 180;
  const x1 = r1(0.5 - Math.cos(rad) / 2);
  const y1 = r1(0.5 - Math.sin(rad) / 2);
  const stops = mid ? [{ offset: 0, colour: from }, { offset: 0.5, colour: mid }, { offset: 1, colour: to }] : [{ offset: 0, colour: from }, { offset: 1, colour: to }];
  return { kind: "linear", id, x1, y1, x2: r1(1 - x1), y2: r1(1 - y1), stops };
}
function radial(id: string, centre: string, edge: string, edgeOpacity = 1): SceneDef {
  return { kind: "radial", id, cx: 0.5, cy: 0.5, r: 0.5, stops: [{ offset: 0, colour: centre }, { offset: 1, colour: edge, opacity: edgeOpacity }] };
}
function grain(seed: number, opacity: number, baseFrequency = 0.85): SceneDef {
  return { kind: "grain", id: "grain", baseFrequency, octaves: 2, seed: seed % 1000, opacity };
}
const url = (id: string) => `url(#${id})`;

/* the connection mode the variant chooses: how a shared shape runs between two motifs */
function route(a: Point, b: Point, mode: number, F: Frame): Point[] {
  if (mode === 1) {
    /* orthogonal: an elbow, the bend on the side away from the frame's centre */
    const cx = F.x + F.width / 2;
    const bend = Math.abs(a.x - cx) > Math.abs(b.x - cx) ? pt(a.x, b.y) : pt(b.x, a.y);
    return [a, bend, b];
  }
  if (mode === 2) {
    /* arc: a bow away from the centre */
    const mx = (a.x + b.x) / 2;
    const my = (a.y + b.y) / 2;
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const len = Math.hypot(dx, dy) || 1;
    const away = (mx - (F.x + F.width / 2)) * (-dy / len) + (my - (F.y + F.height / 2)) * (dx / len) >= 0 ? 1 : -1;
    const control = pt(mx + (-dy / len) * len * 0.35 * away, my + (dx / len) * len * 0.35 * away);
    const out: Point[] = [];
    for (let t = 0; t <= 1.0001; t += 0.1) out.push(pt((1 - t) ** 2 * a.x + 2 * (1 - t) * t * control.x + t * t * b.x, (1 - t) ** 2 * a.y + 2 * (1 - t) * t * control.y + t * t * b.y));
    return out;
  }
  return [a, b];
}
function polyline(points: Point[], stroke: string, width: number, role: SceneDecoration["role"], opacity?: number): SceneDecoration {
  const d = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x} ${p.y}`).join("");
  return { kind: "path", d, fill: "none", stroke, strokeWidth: width, clip: true, role, ...(opacity !== undefined ? { opacity } : {}) };
}
function along(points: Point[], count: number): Point[] {
  /* count points spread along a polyline */
  const lengths: number[] = [];
  let total = 0;
  for (let i = 1; i < points.length; i += 1) { const l = Math.hypot((points[i] as Point).x - (points[i - 1] as Point).x, (points[i] as Point).y - (points[i - 1] as Point).y); lengths.push(l); total += l; }
  const out: Point[] = [];
  for (let k = 0; k < count; k += 1) {
    const target = (total * (k + 0.5)) / count;
    let run = 0;
    for (let i = 1; i < points.length; i += 1) {
      const l = lengths[i - 1] as number;
      if (run + l >= target) { const t = (target - run) / (l || 1); out.push(pt((points[i - 1] as Point).x + ((points[i] as Point).x - (points[i - 1] as Point).x) * t, (points[i - 1] as Point).y + ((points[i] as Point).y - (points[i - 1] as Point).y) * t)); break; }
      run += l;
    }
  }
  return out;
}
const dist = (a: Point, b: Point) => Math.hypot(a.x - b.x, a.y - b.y);

/* ================= 1 · DOTS — France 1985 ================= */
function layoutDots({ content, variant, seed, frame: F, points }: Input): Layout {
  const pal = palette("television", ["#e4472c", "#3fb26b", "#2f6fd6", INK, "#a9a49b"]);
  const defs: SceneDef[] = [grain(seed, 0.16), radial("dot-shade", "#ffffff", "#000000", 0.28)];
  const decorations: SceneDecoration[] = [];
  const nodes: SceneNode[] = [];
  const connectors: SceneConnector[] = [];
  const vertical = variant === 1;
  const diagonal = variant === 2;
  /* the field's pitch and reach are the state's: the seed sets them */
  const pitch = [58, 62, 66, 72][pick(seed, "dots:pitch", 4)] as number;
  const radius = pitch * 0.39;
  const cols = Math.floor((F.width - 40) / pitch);
  const rows = Math.floor((F.height - 40) / pitch);
  const reach = Math.min(F.width, F.height) * (0.3 + pick(seed, "dots:reach", 3) * 0.04);
  /* the field: rows (or columns) of alternating dots; near a term the dots swell in that term's ink */
  for (let r = 0; r < rows; r += 1) {
    const shift = ((r + pick(seed, "dots:shift", 2)) % 2 === 1 ? pitch / 2 : 0);
    for (let c = 0; c < cols; c += 1) {
      const x = F.x + 20 + radius + c * pitch + shift;
      const y = F.y + 20 + radius + r * pitch;
      if (x > F.x + F.width - 10) continue;
      let nearest = -1;
      let near = Infinity;
      points.forEach((p, k) => { const d = dist({ x, y }, p); if (d < near) { near = d; nearest = k; } });
      const w = Math.max(0, 1 - near / reach);
      const lineIndex = diagonal ? Math.floor((c + r) / 2) : vertical ? c : r;
      const colour = w > 0.55 ? (pal.colours[nearest % 3] as string) : (pal.colours[(lineIndex + c + pick(seed, "dots:colour", 3)) % 3] as string);
      const rr = radius * (0.42 + 0.9 * w);
      decorations.push({ kind: "circle", cx: r1(x), cy: r1(y), r: r1(rr), fill: colour, role: w > 0.55 ? "term" : "field", opacity: w > 0.55 ? 1 : 0.82 });
      if (w > 0.55) decorations.push({ kind: "circle", cx: r1(x), cy: r1(y), r: r1(rr), fill: url("dot-shade"), role: "term", opacity: 0.35 });
    }
  }
  points.forEach((p, k) => nodes.push(nodeAt(k, content, p, box(p.x - reach, p.y - reach, reach * 2, reach * 2), F)));
  /* an association: a chain of black-and-grey pairs from one motif to the other */
  for (const edge of content.edges) {
    const a = points[edge.from] as Point;
    const b = points[edge.to] as Point;
    const path = route(a, b, variant, F);
    const beads = along(path, Math.max(4, Math.round(dist(a, b) / 46)));
    beads.forEach((bead, i) => decorations.push({ kind: "circle", cx: bead.x, cy: bead.y, r: 19, fill: i % 2 === 0 ? INK : (pal.colours[4] as string), role: "association", clip: true }));
    connectors.push(link(edge, segmentBox(a, b, 30), F));
  }
  decorations.push({ kind: "rect", x: F.x, y: F.y, width: F.width, height: F.height, fill: url("grain"), role: "texture" });
  return { palette: pal, fieldFill: pal.paper, defs, nodes, connectors, decorations };
}

/* ================= 2 · SPOTS — South Africa R10 ================= */
const SPOT_WARM = ["#f5c400", "#f4a11d", "#ef7a2a", "#ea5a2e", "#e6407c", "#c81d6b", "#a5145e"];
function layoutSpots({ content, variant, seed, frame: F, points }: Input): Layout {
  const pal = palette("warm", SPOT_WARM);
  const defs: SceneDef[] = [grain(seed, 0.12), ...SPOT_WARM.map((c, i) => radial(`spot-${i}`, "#fff3c4", c))];
  const decorations: SceneDecoration[] = [];
  const nodes: SceneNode[] = [];
  const connectors: SceneConnector[] = [];
  const big = Math.min(F.width, F.height) * (0.1 + pick(seed, "spots:big", 3) * 0.012);
  const colourAt = (y: number) => Math.min(SPOT_WARM.length - 1, Math.floor(((y - F.y) / F.height) * SPOT_WARM.length));
  /* the lattice: the field's spots, sized by their distance to the nearest motif */
  const rowsCount = (variant === 2 ? 8 : 6) + pick(seed, "spots:rows", 3);
  const pitchX = F.width / (3.8 + pick(seed, "spots:cols", 3) * 0.4);
  const pitchY = F.height / rowsCount;
  const reach = Math.min(F.width, F.height) * 0.3;
  for (let r = 0; r < rowsCount; r += 1) {
    for (let c = 0; c < 5; c += 1) {
      const drift = variant === 1 ? (unit(seed, `spots:drift:${r}:${c}`) - 0.5) * pitchX * 0.6 : 0;
      const x = F.x + pitchX * (c + (r % 2 === 0 ? 0.5 : 0.9)) + drift;
      const y = F.y + pitchY * (r + 0.6);
      if (x < F.x - big || x > F.x + F.width + big) continue;
      const near = Math.min(...points.map((p) => dist({ x, y }, p)));
      const w = Math.max(0, 1 - near / reach);
      const rr = big * (0.38 + 0.5 * (variant === 2 ? w : 1 - w * 0.6));
      const ci = colourAt(y);
      decorations.push({ kind: "circle", cx: r1(x), cy: r1(y), r: r1(rr), fill: url(`spot-${ci}`), role: "field", clip: true, opacity: 0.94 });
    }
  }
  /* the terms: the largest spots, on the skeleton */
  points.forEach((p, k) => {
    decorations.push({ kind: "circle", cx: p.x, cy: p.y, r: r1(big * 1.25), fill: url(`spot-${colourAt(p.y)}`), role: "term", clip: true });
    decorations.push({ kind: "circle", cx: p.x, cy: p.y, r: r1(big * 0.42), fill: pal.paper, role: "term", opacity: 0.85 });
    nodes.push(nodeAt(k, content, p, box(p.x - big * 1.25, p.y - big * 1.25, big * 2.5, big * 2.5), F));
  });
  /* an association: a run of mid spots between the two, in the connection mode */
  for (const edge of content.edges) {
    const a = points[edge.from] as Point;
    const b = points[edge.to] as Point;
    const beads = along(route(a, b, variant, F), Math.max(3, Math.round(dist(a, b) / (big * 1.6))));
    beads.forEach((bead) => decorations.push({ kind: "circle", cx: bead.x, cy: bead.y, r: r1(big * 0.55), fill: INK, role: "association", clip: true, opacity: 0.9 }));
    connectors.push(link(edge, segmentBox(a, b, big), F));
  }
  decorations.push({ kind: "rect", x: F.x, y: F.y, width: F.width, height: F.height, fill: url("grain"), role: "texture" });
  return { palette: pal, fieldFill: "#fbfaf6", defs, nodes, connectors, decorations };
}

/* ================= 3 · CHEVRON — Germany 1973 ================= */
function layoutChevron({ content, variant, seed, frame: F, points }: Input): Layout {
  const pal = palette("treaty", ["#1f4fd0", INK, "#e4472c", "#c8a02a", "#3fa684", "#2f5fb8", "#7b5ea7", "#d49454"]);
  const defs: SceneDef[] = [grain(seed, 0.1), ...pal.colours.map((c, i) => linear(`band-${i}`, c, "#ffffff", 90))];
  const decorations: SceneDecoration[] = [];
  const nodes: SceneNode[] = [];
  const connectors: SceneConnector[] = [];
  const thickness = Math.min(F.width, F.height) * (0.05 + pick(seed, "chevron:thick", 3) * 0.01);
  const arm = Math.max(F.width, F.height) * 1.2;
  const hatchPitch = 10 + pick(seed, "chevron:hatch", 3) * 2;
  /* each term: a chevron whose vertex is its point, opening away from the frame's centre */
  points.forEach((p, k) => {
    const cx = F.x + F.width / 2;
    const cy = F.y + F.height / 2;
    const towards = variant === 2 ? Math.PI / 2 : Math.atan2(p.y - cy, p.x - cx);
    const open = variant === 1 ? Math.PI * 0.42 : Math.PI * 0.5;
    const a1 = towards + Math.PI - open;
    const a2 = towards + Math.PI + open;
    const colour = pal.colours[k % pal.colours.length] as string;
    for (let layer = 0; layer < (variant === 1 ? 3 : 2); layer += 1) {
      const offset = layer * thickness * 1.7;
      const v = pt(p.x - Math.cos(towards) * offset, p.y - Math.sin(towards) * offset);
      const stroke = layer === 0 ? colour : layer === 1 ? INK : (pal.colours[(k + 2) % pal.colours.length] as string);
      decorations.push({ kind: "path", d: `M${r1(v.x + Math.cos(a1) * arm)} ${r1(v.y + Math.sin(a1) * arm)}L${v.x} ${v.y}L${r1(v.x + Math.cos(a2) * arm)} ${r1(v.y + Math.sin(a2) * arm)}`, fill: "none", stroke, strokeWidth: r1(thickness * (layer === 0 ? 1 : 0.6)), clip: true, role: "term" });
    }
    nodes.push(nodeAt(k, content, p, box(p.x - thickness * 3, p.y - thickness * 3, thickness * 6, thickness * 6), F));
  });
  /* an association: the cross-hatch where two bands meet — both inks at right angles, along the route */
  for (const edge of content.edges) {
    const a = points[edge.from] as Point;
    const b = points[edge.to] as Point;
    const centre = along(route(a, b, variant, F), 1)[0] as Point;
    const size = Math.min(F.width, F.height) * (0.16 + pick(seed, `chevron:hatch:${edge.from}:${edge.to}`, 3) * 0.02);
    const colourA = pal.colours[edge.from % pal.colours.length] as string;
    const colourB = pal.colours[edge.to % pal.colours.length] as string;
    const angle = Math.atan2(b.y - a.y, b.x - a.x);
    for (let i = -size; i <= size; i += hatchPitch) {
      for (const [colour, rot] of [[colourA, angle + Math.PI / 4], [colourB, angle - Math.PI / 4]] as const) {
        const nx = Math.cos(rot + Math.PI / 2) * i;
        const ny = Math.sin(rot + Math.PI / 2) * i;
        decorations.push({ kind: "line", x1: r1(centre.x + nx - Math.cos(rot) * size), y1: r1(centre.y + ny - Math.sin(rot) * size), x2: r1(centre.x + nx + Math.cos(rot) * size), y2: r1(centre.y + ny + Math.sin(rot) * size), stroke: colour, width: 2.6, clip: true, role: "association" });
      }
    }
    connectors.push(link(edge, box(centre.x - size, centre.y - size, size * 2, size * 2), F));
  }
  decorations.push({ kind: "rect", x: F.x, y: F.y, width: F.width, height: F.height, fill: url("grain"), role: "texture" });
  return { palette: pal, fieldFill: pal.paper, defs, nodes, connectors, decorations };
}

/* ================= 4 · CROSSFIELD — Canada 1983 ================= */
function layoutCrossfield({ content, variant, seed, frame: F, points }: Input): Layout {
  const pal = palette("green-rose", ["#2f9a6a", "#f0dcd8", "#1d6f4a"]);
  const defs: SceneDef[] = [grain(seed, 0.14), linear("rose", "#f3e2dd", "#e9cfc9", 60 + pick(seed, "crossfield:rose", 3) * 30)];
  const decorations: SceneDecoration[] = [{ kind: "rect", x: F.x, y: F.y, width: F.width, height: F.height, fill: url("rose"), role: "field" }];
  const nodes: SceneNode[] = [];
  const connectors: SceneConnector[] = [];
  const cols = 20 + pick(seed, "crossfield:cols", 5) * 2;
  const rows = Math.round((F.height / F.width) * cols);
  const pitchX = F.width / cols;
  const pitchY = F.height / rows;
  const armX = F.width * 0.3;
  const armY = F.height * 0.3;
  const figure = (x: number, y: number): number => {
    let value = 0;
    for (const c of points) {
      const dx = Math.abs(x - c.x);
      const dy = Math.abs(y - c.y);
      if (variant === 2) value = Math.max(value, Math.max(0, 1 - Math.hypot(dx, dy) / (Math.min(armX, armY) * 0.9)));
      else {
        const horizontal = dy < pitchY * 1.6 && dx < armX ? 1 - dx / armX : 0;
        const vertical = dx < pitchX * 1.6 && dy < armY ? 1 - dy / armY : 0;
        const core = Math.max(0, 1 - Math.hypot(dx / (pitchX * 3.2), dy / (pitchY * 3.2)));
        value = Math.max(value, horizontal, vertical, core);
      }
    }
    if (variant !== 0) for (const edge of content.edges) {
      const a = points[edge.from] as Point;
      const b = points[edge.to] as Point;
      const t = Math.max(0, Math.min(1, ((x - a.x) * (b.x - a.x) + (y - a.y) * (b.y - a.y)) / ((b.x - a.x) ** 2 + (b.y - a.y) ** 2 || 1)));
      const d = Math.hypot(x - (a.x + (b.x - a.x) * t), y - (a.y + (b.y - a.y) * t));
      value = Math.max(value, Math.max(0, 0.8 - d / (pitchX * 2.6)));
    }
    return Math.min(1, value);
  };
  for (let r = 0; r < rows; r += 1) for (let c = 0; c < cols; c += 1) {
    const x = F.x + pitchX * (c + 0.5);
    const y = F.y + pitchY * (r + 0.5);
    const value = figure(x, y);
    const size = 5 + 24 * value;
    decorations.push({ kind: "cross", cx: r1(x), cy: r1(y), size: r1(size), stroke: value > 0.6 ? (pal.colours[2] as string) : (pal.colours[0] as string), width: size > 18 ? 5 : 3.5, role: value > 0.5 ? "term" : "field" });
  }
  points.forEach((c, k) => nodes.push(nodeAt(k, content, c, box(c.x - armX, c.y - armY, armX * 2, armY * 2), F)));
  for (const edge of content.edges) {
    const a = points[edge.from] as Point;
    const b = points[edge.to] as Point;
    if (variant === 0) { const path = route(a, b, 2, F); decorations.push(polyline(path, pal.colours[2] as string, 5, "association", 0.8)); }
    connectors.push(link(edge, segmentBox(a, b, 40), F));
  }
  decorations.push({ kind: "rect", x: F.x, y: F.y, width: F.width, height: F.height, fill: url("grain"), role: "texture" });
  return { palette: pal, fieldFill: "#f0dcd8", defs, nodes, connectors, decorations };
}

/* ================= 5 · LINES — Sweden 2026 ================= */
function layoutLines({ content, variant, seed, frame: F, points }: Input): Layout {
  const pal = palette("streaming", ["#b57f92", "#5e9c7d", "#3e7a5c"]);
  const defs: SceneDef[] = [grain(seed, 0.1), linear("bar", "#5e9c7d", "#2f5f47", 90)];
  const decorations: SceneDecoration[] = [];
  const nodes: SceneNode[] = [];
  const connectors: SceneConnector[] = [];
  const horizontal = variant === 1;
  const lineCount = 22 + pick(seed, "lines:count", 5) * 2;
  const pitch = ((horizontal ? F.height : F.width) - 40) / (lineCount - 1);
  const lineAt = (i: number) => (horizontal ? F.y : F.x) + 20 + i * pitch;
  const hair = 2.5 + pick(seed, "lines:hair", 3) * 0.7;
  const barWidth = 11;
  for (let i = 0; i < lineCount; i += 1) {
    const p = lineAt(i);
    decorations.push(horizontal
      ? { kind: "line", x1: F.x + 10, y1: r1(p), x2: F.x + F.width - 10, y2: r1(p), stroke: pal.colours[0] as string, width: hair, role: "field" }
      : { kind: "line", x1: r1(p), y1: F.y + 10, x2: r1(p), y2: F.y + F.height - 10, stroke: pal.colours[0] as string, width: hair, role: "field" });
    if (variant === 2 && i % 3 === 0) decorations.push(horizontal
      ? { kind: "line", x1: r1(lineAt(i) - pitch * 0.4 + F.x - F.y), y1: F.y + 10, x2: r1(lineAt(i) - pitch * 0.4 + F.x - F.y), y2: F.y + F.height - 10, stroke: pal.colours[0] as string, width: 1.5, role: "field", opacity: 0.6, clip: true }
      : { kind: "line", x1: F.x + 10, y1: r1(F.y + 20 + i * ((F.height - 40) / (lineCount - 1))), x2: F.x + F.width - 10, y2: r1(F.y + 20 + i * ((F.height - 40) / (lineCount - 1))), stroke: pal.colours[0] as string, width: 1.5, role: "field", opacity: 0.6 });
  }
  /* the terms: a bell of bars around each point — the nearer the line, the longer the bar */
  const reach = (horizontal ? F.height : F.width) * 0.2;
  const length = horizontal ? F.width : F.height;
  points.forEach((p, k) => {
    for (let i = 0; i < lineCount; i += 1) {
      const coord = lineAt(i);
      const d = Math.abs(coord - (horizontal ? p.y : p.x));
      if (d > reach) continue;
      const w = 1 - d / reach;
      const extent = length * (0.08 + 0.34 * w * w) * (0.85 + unit(seed, `lines:${k}:${i}`) * 0.3);
      const centre = horizontal ? p.x : p.y;
      const start = centre - extent / 2;
      decorations.push(horizontal
        ? { kind: "rect", x: r1(start), y: r1(coord - barWidth / 2), width: r1(extent), height: barWidth, fill: url("bar"), role: "term", clip: true }
        : { kind: "rect", x: r1(coord - barWidth / 2), y: r1(start), width: barWidth, height: r1(extent), fill: url("bar"), role: "term", clip: true });
    }
    nodes.push(nodeAt(k, content, p, horizontal ? box(F.x, p.y - reach, F.width, reach * 2) : box(p.x - reach, F.y, reach * 2, F.height), F));
  });
  /* an association: short bars on every line between the two motifs, at the route's height */
  for (const edge of content.edges) {
    const a = points[edge.from] as Point;
    const b = points[edge.to] as Point;
    const path = route(a, b, variant === 2 ? 2 : 0, F);
    const beads = along(path, Math.max(4, Math.round(dist(a, b) / pitch)));
    beads.forEach((bead) => {
      const i = Math.round(((horizontal ? bead.y : bead.x) - (horizontal ? F.y : F.x) - 20) / pitch);
      const coord = lineAt(Math.max(0, Math.min(lineCount - 1, i)));
      decorations.push(horizontal
        ? { kind: "rect", x: r1(bead.x - 26), y: r1(coord - barWidth / 2), width: 52, height: barWidth, fill: INK, role: "association", clip: true }
        : { kind: "rect", x: r1(coord - barWidth / 2), y: r1(bead.y - 26), width: barWidth, height: 52, fill: INK, role: "association", clip: true });
    });
    connectors.push(link(edge, segmentBox(a, b, 30), F));
  }
  decorations.push({ kind: "rect", x: F.x, y: F.y, width: F.width, height: F.height, fill: url("grain"), role: "texture" });
  return { palette: pal, fieldFill: pal.paper, defs, nodes, connectors, decorations };
}

/* ================= 6 · GRID — Venezuela 1975 ================= */
function layoutGrid({ content, variant, seed, frame: F, points }: Input): Layout {
  const field = INK;
  const cell = PAPER;
  const pal = palette("black", [cell, field, "#c9d63a"]);
  const defs: SceneDef[] = [grain(seed, 0.08), radial("cell-shade", "#ffffff", "#d9d6cd")];
  const decorations: SceneDecoration[] = [];
  const nodes: SceneNode[] = [];
  const connectors: SceneConnector[] = [];
  /* the grid's count is the variant's, the term count's and the seed's: the field grows finer as
     the view grows richer (blocks 8–11 → 10–13, rings one fewer, bars one more), never the same
     lattice for two counts */
  const cols = (variant === 2 ? 7 : variant === 1 ? 5 : 6) + points.length + pick(seed, "grid:cols", 2) * 3;
  const rows = Math.max(5, Math.round((F.height / F.width) * cols));
  const gap = 9 + pick(seed, "grid:gap", 3) * 3;
  const cw = (F.width - gap * (cols + 1)) / cols;
  const ch = (F.height - gap * (rows + 1)) / rows;
  const cellBox = (c: number, r: number): Box => box(F.x + gap + c * (cw + gap), F.y + gap + r * (ch + gap), cw, ch);
  const cellOf = (p: Point): [number, number] => [Math.max(0, Math.min(cols - 1, Math.floor((p.x - F.x) / (cw + gap)))), Math.max(0, Math.min(rows - 1, Math.floor((p.y - F.y) / (ch + gap))))];
  const termCells = points.map(cellOf);
  const ringCells = new Map<string, Edge>();
  const key = (c: number, r: number) => `${c},${r}`;
  for (const edge of content.edges) {
    const [ac, ar] = termCells[edge.from] as [number, number];
    const [bc, br] = termCells[edge.to] as [number, number];
    const steps = Math.max(Math.abs(bc - ac), Math.abs(br - ar));
    for (let s = 1; s < steps; s += 1) {
      const c = variant === 2 ? (s <= Math.abs(bc - ac) ? ac + Math.sign(bc - ac) * s : bc) : Math.round(ac + ((bc - ac) * s) / steps);
      const r = variant === 2 ? (s <= Math.abs(bc - ac) ? ar : ar + Math.sign(br - ar) * (s - Math.abs(bc - ac))) : Math.round(ar + ((br - ar) * s) / steps);
      if (!termCells.some(([tc, tr]) => tc === c && tr === r)) ringCells.set(key(c, r), edge);
    }
    const a = cellBox(Math.min(ac, bc), Math.min(ar, br));
    const b = cellBox(Math.max(ac, bc), Math.max(ar, br));
    connectors.push(link(edge, box(a.x, a.y, b.x + b.width - a.x, b.y + b.height - a.y), F));
  }
  for (let r = 0; r < rows; r += 1) for (let c = 0; c < cols; c += 1) {
    const b = cellBox(c, r);
    const term = termCells.findIndex(([tc, tr]) => tc === c && tr === r);
    if (term >= 0) continue;
    const ring = ringCells.get(key(c, r));
    if (ring) {
      decorations.push({ kind: "circle", cx: r1(b.x + b.width / 2), cy: r1(b.y + b.height / 2), r: r1(Math.min(cw, ch) / 2), fill: cell, role: "association" });
      decorations.push({ kind: "circle", cx: r1(b.x + b.width / 2), cy: r1(b.y + b.height / 2), r: r1(Math.min(cw, ch) / 2 - 14), fill: field, role: "association" });
      continue;
    }
    /* the cells beside a term take a tone: the field answers the terms */
    const near = termCells.some(([tc, tr]) => Math.max(Math.abs(tc - c), Math.abs(tr - r)) === 1);
    decorations.push({ kind: "rect", x: r1(b.x), y: r1(b.y), width: r1(b.width), height: r1(b.height), fill: variant === 1 ? url("cell-shade") : near ? "#dedbd2" : cell, role: "field" });
  }
  /* the terms: the focused term a circle over a 2 × 2 block cut by the gaps; the others quartered circles */
  termCells.forEach(([c, r], k) => {
    const b = cellBox(c, r);
    if (k === 0 && c < cols - 1 && r < rows - 1) {
      const bw = cw * 2 + gap;
      const bh = ch * 2 + gap;
      decorations.push({ kind: "circle", cx: r1(b.x + bw / 2), cy: r1(b.y + bh / 2), r: r1(Math.min(bw, bh) / 2), fill: cell, role: "term" });
      decorations.push({ kind: "rect", x: r1(b.x + cw), y: r1(b.y), width: gap, height: r1(bh), fill: field, role: "term" });
      decorations.push({ kind: "rect", x: r1(b.x), y: r1(b.y + ch), width: r1(bw), height: gap, fill: field, role: "term" });
      nodes.push(nodeAt(k, content, pt(b.x + bw / 2, b.y + bh / 2), box(b.x, b.y, bw, bh), F));
      return;
    }
    decorations.push({ kind: "circle", cx: r1(b.x + b.width / 2), cy: r1(b.y + b.height / 2), r: r1(Math.min(cw, ch) / 2), fill: variant === 2 ? (pal.colours[2] as string) : cell, role: "term" });
    decorations.push({ kind: "rect", x: r1(b.x + b.width / 2 - gap / 2), y: r1(b.y), width: gap, height: r1(b.height), fill: field, role: "term" });
    decorations.push({ kind: "rect", x: r1(b.x), y: r1(b.y + b.height / 2 - gap / 2), width: r1(b.width), height: gap, fill: field, role: "term" });
    nodes.push(nodeAt(k, content, pt(b.x + b.width / 2, b.y + b.height / 2), b, F));
  });
  decorations.push({ kind: "rect", x: F.x, y: F.y, width: F.width, height: F.height, fill: url("grain"), role: "texture" });
  return { palette: pal, fieldFill: field, defs, nodes, connectors, decorations };
}

/* ================= 7 · RAYS — the homage's radial rays ================= */
function layoutRays({ content, variant, seed, frame: F, points }: Input): Layout {
  const pal = palette("rays", ["#e4472c", "#2f5fb8", "#3fa684", "#d49454", "#c81d6b", "#1f4491", "#7b5ea7", "#8fc35a"]);
  const defs: SceneDef[] = [grain(seed, 0.1), ...pal.colours.map((c, i) => linear(`ray-${i}`, c, "#ffffff", 0))];
  const decorations: SceneDecoration[] = [];
  const nodes: SceneNode[] = [];
  const connectors: SceneConnector[] = [];
  const cx = F.x + F.width / 2;
  const cy = F.y + F.height / 2;
  const centre = variant === 1 ? pt(cx, F.y + F.height - 60) : pt(cx, cy);
  const radius = Math.max(F.width, F.height);
  const rad = (deg: number) => (deg * Math.PI) / 180;
  const rayStep = rad(2.8 + pick(seed, "rays:step", 4) * 0.4);
  const fieldStep = 5 + pick(seed, "rays:field", 3);
  const fieldPhase = unit(seed, "rays:phase") * fieldStep;
  /* each term: a sector of rays aimed at its point, its width from its distance */
  points.forEach((p, k) => {
    const aim = Math.atan2(p.y - centre.y, p.x - centre.x);
    const half = rad(variant === 2 ? 14 : 22);
    const colour = pal.colours[k % pal.colours.length] as string;
    for (let a = aim - half; a < aim + half; a += rayStep) {
      const a2 = a + rad(1.8);
      const inner = variant === 2 ? dist(p, centre) * 0.5 : 30;
      decorations.push({ kind: "polygon", points: [pt(centre.x + Math.cos(a) * inner, centre.y + Math.sin(a) * inner), pt(centre.x + Math.cos(a) * radius, centre.y + Math.sin(a) * radius), pt(centre.x + Math.cos(a2) * radius, centre.y + Math.sin(a2) * radius), pt(centre.x + Math.cos(a2) * inner, centre.y + Math.sin(a2) * inner)], fill: colour, clip: true, role: "term" });
    }
    decorations.push({ kind: "circle", cx: p.x, cy: p.y, r: 30, fill: pal.paper, stroke: colour, strokeWidth: 8, role: "term", clip: true });
    nodes.push(nodeAt(k, content, p, box(p.x - 90, p.y - 90, 180, 180), F));
  });
  /* the field between sectors: faint rays */
  for (let a = fieldPhase; a < 360; a += fieldStep) decorations.push({ kind: "line", x1: centre.x, y1: centre.y, x2: r1(centre.x + Math.cos(rad(a)) * radius), y2: r1(centre.y + Math.sin(rad(a)) * radius), stroke: INK, width: 1, opacity: 0.18, clip: true, role: "field" });
  /* an association: an arc band from one sector to the other, its radius from the pair */
  content.edges.forEach((edge, k) => {
    const a = points[edge.from] as Point;
    const b = points[edge.to] as Point;
    const r = Math.min(dist(a, centre), dist(b, centre)) * (0.55 + k * 0.12);
    const from = Math.atan2(a.y - centre.y, a.x - centre.x);
    const to = Math.atan2(b.y - centre.y, b.x - centre.x);
    let delta = to - from;
    while (delta > Math.PI) delta -= Math.PI * 2;
    while (delta < -Math.PI) delta += Math.PI * 2;
    const sweep = delta >= 0 ? 1 : 0;
    const p1 = pt(centre.x + Math.cos(from) * r, centre.y + Math.sin(from) * r);
    const p2 = pt(centre.x + Math.cos(to) * r, centre.y + Math.sin(to) * r);
    const d = `M${p1.x} ${p1.y}A${r1(r)} ${r1(r)} 0 0 ${sweep} ${p2.x} ${p2.y}`;
    decorations.push({ kind: "path", d, fill: "none", stroke: pal.paper, strokeWidth: 26, clip: true, role: "association" });
    decorations.push({ kind: "path", d, fill: "none", stroke: INK, strokeWidth: 9, clip: true, role: "association" });
    connectors.push(link(edge, segmentBox(a, b, 40), F));
  });
  decorations.push({ kind: "rect", x: F.x, y: F.y, width: F.width, height: F.height, fill: url("grain"), role: "texture" });
  return { palette: pal, fieldFill: pal.paper, defs, nodes, connectors, decorations };
}

/* ================= 8 · OVERLAP — the homage's translucent panels ================= */
function layoutOverlap({ content, variant, seed, frame: F, points }: Input): Layout {
  const pal = palette("overprint", ["#2fb3c9", "#f2c230", "#e4472c", "#2f5fb8", "#3fa684", "#c81d6b", "#d49454", "#7b5ea7"]);
  const defs: SceneDef[] = [grain(seed, 0.12), ...pal.colours.map((c, i) => linear(`panel-${i}`, c, c === "#f2c230" ? "#f7e08a" : "#ffffff", 45 + i * 20))];
  const decorations: SceneDecoration[] = [];
  const nodes: SceneNode[] = [];
  const connectors: SceneConnector[] = [];
  const w = Math.min(F.width, F.height) * ((points.length <= 2 ? 0.48 : 0.38) + pick(seed, "overlap:w", 4) * 0.03);
  const h = w * ((variant === 1 ? 0.65 : 1.05) + pick(seed, "overlap:h", 3) * 0.08);
  /* the field: a ghost lattice of panel outlines across the frame, its count from the term count and the seed */
  {
    const latticeCols = 2 + points.length + pick(seed, "overlap:lattice", 2);
    const cellW = F.width / latticeCols;
    const cellH = cellW * (variant === 1 ? 0.7 : 1.1);
    const phase = unit(seed, "overlap:phase") * cellH;
    for (let r = -1; r * cellH - phase < F.height + cellH; r += 1) for (let c = 0; c < latticeCols; c += 1) {
      decorations.push({ kind: "rect", x: r1(F.x + c * cellW + 6), y: r1(F.y + r * cellH - phase + 6), width: r1(cellW - 12), height: r1(cellH - 12), fill: "none", stroke: INK, strokeWidth: 1.2, opacity: 0.22, clip: true, role: "field" });
    }
  }
  /* the field: each term casts three faint echoes of its panel, stepping away along the field's direction */
  points.forEach((p, k) => {
    const rot = variant === 2 ? (pick(seed, `overlap:rot:${k}`, 5) - 2) * 9 : 0;
    for (const [ex, ey] of [[0.42, -0.3], [-0.36, 0.34], [0.78, -0.56]] as const) {
      decorations.push({ kind: "rect", x: r1(p.x + w * ex - w / 2), y: r1(p.y + h * ey - h / 2), width: r1(w), height: r1(h), fill: url(`panel-${k % pal.colours.length}`), opacity: 0.22, rotate: rot, clip: true, role: "field" });
    }
  });
  /* each term: a translucent panel centred on its point; where associated panels meet, the inks mix */
  points.forEach((p, k) => {
    const rot = variant === 2 ? (pick(seed, `overlap:rot:${k}`, 5) - 2) * 9 : 0;
    decorations.push({ kind: "rect", x: r1(p.x - w / 2), y: r1(p.y - h / 2), width: r1(w), height: r1(h), fill: url(`panel-${k % pal.colours.length}`), opacity: 0.74, rotate: rot, clip: true, role: "term" });
    nodes.push(nodeAt(k, content, p, box(p.x - w / 2, p.y - h / 2, w, h), F));
  });
  /* an association: a bridging panel spanning both, in the two inks' mix, along the route */
  for (const edge of content.edges) {
    const a = points[edge.from] as Point;
    const b = points[edge.to] as Point;
    const angle = (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI;
    const length = dist(a, b);
    const mx = (a.x + b.x) / 2;
    const my = (a.y + b.y) / 2;
    decorations.push({ kind: "rect", x: r1(mx - length / 2), y: r1(my - h * 0.16), width: r1(length), height: r1(h * 0.32), fill: INK, opacity: 0.55, rotate: r1(angle), clip: true, role: "association" });
    connectors.push(link(edge, segmentBox(a, b, h * 0.2), F));
  }
  decorations.push({ kind: "rect", x: F.x, y: F.y, width: F.width, height: F.height, fill: url("grain"), role: "texture" });
  return { palette: pal, fieldFill: pal.paper, defs, nodes, connectors, decorations };
}

/* ================= 9 · HALFTONE — a dot screen whose size follows the figure ================= */
function layoutHalftone({ content, variant, seed, frame: F, points }: Input): Layout {
  const pal = palette("halftone", ["#1f4491", "#e4472c", "#f5c400"]);
  const defs: SceneDef[] = [grain(seed, 0.1), linear("halftone-ground", "#fbf7ee", "#efe6d6", 90)];
  const decorations: SceneDecoration[] = [{ kind: "rect", x: F.x, y: F.y, width: F.width, height: F.height, fill: url("halftone-ground"), role: "field" }];
  const nodes: SceneNode[] = [];
  const connectors: SceneConnector[] = [];
  const pitch = 26 + pick(seed, "halftone:pitch", 5) * 2;
  const cols = Math.floor(F.width / pitch);
  const rows = Math.floor(F.height / pitch);
  const reach = Math.min(F.width, F.height) * (variant === 2 ? 0.34 : 0.26);
  const cx = F.x + F.width / 2;
  for (let r = 0; r < rows; r += 1) for (let c = 0; c < cols; c += 1) {
    const x = F.x + pitch * (c + 0.5) + (r % 2 === 1 ? pitch / 2 : 0);
    const y = F.y + pitch * (r + 0.5);
    if (x > F.x + F.width - pitch / 2) continue;
    let value = 0;
    let nearest = 0;
    points.forEach((p, k) => {
      const d = dist({ x, y }, p);
      const v = variant === 1 ? Math.max(0, 1 - Math.abs(x - p.x) / reach) * Math.max(0, 1 - Math.abs(y - p.y) / (reach * 1.6)) : variant === 2 ? Math.max(0, 1 - Math.abs(d - reach * 0.5) / (reach * 0.35)) : Math.max(0, 1 - d / reach);
      if (v > value) { value = v; nearest = k; }
    });
    for (const edge of content.edges) {
      const a = points[edge.from] as Point;
      const b = points[edge.to] as Point;
      const t = Math.max(0, Math.min(1, ((x - a.x) * (b.x - a.x) + (y - a.y) * (b.y - a.y)) / ((b.x - a.x) ** 2 + (b.y - a.y) ** 2 || 1)));
      const d = Math.hypot(x - (a.x + (b.x - a.x) * t), y - (a.y + (b.y - a.y) * t));
      value = Math.max(value, Math.max(0, 0.6 - d / (pitch * 2)));
    }
    const rr = 2 + 12 * value;
    const colour = value > 0.45 ? (pal.colours[nearest % pal.colours.length] as string) : x < cx ? "#1f4491" : "#2b3a55";
    decorations.push({ kind: "circle", cx: r1(x), cy: r1(y), r: r1(rr), fill: colour, role: value > 0.45 ? "term" : "field", opacity: value > 0.45 ? 1 : 0.5 });
  }
  points.forEach((p, k) => nodes.push(nodeAt(k, content, p, box(p.x - reach, p.y - reach, reach * 2, reach * 2), F)));
  for (const edge of content.edges) connectors.push(link(edge, segmentBox(points[edge.from] as Point, points[edge.to] as Point, pitch), F));
  decorations.push({ kind: "rect", x: F.x, y: F.y, width: F.width, height: F.height, fill: url("grain"), role: "texture" });
  return { palette: pal, fieldFill: "#fbf7ee", defs, nodes, connectors, decorations };
}

/* ================= 10 · STRIPES — the homage's diagonal stripes ================= */
function layoutStripes({ content, variant, seed, frame: F, points }: Input): Layout {
  const pal = palette("stripes", ["#7b5ea7", "#e4472c", "#f2c230", "#3fa684", "#2f5fb8", "#c81d6b", "#d49454", "#1f4491"]);
  const defs: SceneDef[] = [grain(seed, 0.1), ...pal.colours.map((c, i) => linear(`stripe-${i}`, c, "#ffffff", 0))];
  const decorations: SceneDecoration[] = [];
  const nodes: SceneNode[] = [];
  const connectors: SceneConnector[] = [];
  const angle = (variant === 1 ? Math.PI / 2 : variant === 2 ? -Math.PI / 5 : Math.PI / 4) + ((pick(seed, "stripes:tilt", 3) - 1) * Math.PI) / 18;
  const dir = pt(Math.cos(angle), Math.sin(angle));
  const nrm = pt(-dir.y, dir.x);
  const long = Math.max(F.width, F.height) * 1.5;
  const band = (through: Point, offset: number, width: number, fill: string, role: SceneDecoration["role"], opacity?: number) => {
    const c = pt(through.x + nrm.x * offset, through.y + nrm.y * offset);
    const corner = (s: number, t: number) => pt(c.x + dir.x * s + nrm.x * t, c.y + dir.y * s + nrm.y * t);
    decorations.push({ kind: "polygon", points: [corner(-long, -width / 2), corner(long, -width / 2), corner(long, width / 2), corner(-long, width / 2)], fill, clip: true, role, ...(opacity !== undefined ? { opacity } : {}) });
  };
  /* the field: thin stripes across the frame */
  const pitch = 28 + pick(seed, "stripes:pitch", 4) * 4;
  const cx = F.x + F.width / 2;
  const cy = F.y + F.height / 2;
  for (let i = -48; i <= 48; i += 1) band(pt(cx, cy), i * pitch, 4, INK, "field", 0.12);
  /* each term: a bundle of stripes through its point, in its ink */
  const bundleWidth = Math.min(F.width, F.height) * 0.16;
  points.forEach((p, k) => {
    const colour = pal.colours[k % pal.colours.length] as string;
    for (let i = -2; i <= 2; i += 1) band(p, i * (bundleWidth / 5), bundleWidth / 6.5, i === 0 ? INK : colour, "term", i === 0 ? 0.85 : 0.92);
    nodes.push(nodeAt(k, content, p, box(p.x - bundleWidth, p.y - bundleWidth, bundleWidth * 2, bundleWidth * 2), F));
  });
  /* an association: a cross-stripe in the paper's colour between the two bundles, along the route */
  for (const edge of content.edges) {
    const a = points[edge.from] as Point;
    const b = points[edge.to] as Point;
    decorations.push(polyline(route(a, b, variant, F), pal.paper, 18, "association"));
    decorations.push(polyline(route(a, b, variant, F), INK, 5, "association"));
    connectors.push(link(edge, segmentBox(a, b, 20), F));
  }
  decorations.push({ kind: "rect", x: F.x, y: F.y, width: F.width, height: F.height, fill: url("grain"), role: "texture" });
  return { palette: pal, fieldFill: pal.paper, defs, nodes, connectors, decorations };
}

/* ================= 11 · PETALS — the homage's flower ================= */
function layoutPetals({ content, variant, seed, frame: F, points }: Input): Layout {
  const pal = palette("petals", ["#e4472c", "#f2c230", "#3fa684", "#2f5fb8", "#c81d6b", "#d49454", "#7b5ea7", "#8fc35a"]);
  const defs: SceneDef[] = [grain(seed, 0.1), ...pal.colours.map((c, i) => radial(`petal-${i}`, "#ffffff", c))];
  const decorations: SceneDecoration[] = [];
  const nodes: SceneNode[] = [];
  const connectors: SceneConnector[] = [];
  const size = Math.min(F.width, F.height) * ((points.length <= 2 ? 0.22 : 0.16) + pick(seed, "petals:size", 3) * 0.015);
  const petal = (centre: Point, angle: number, length: number, width: number, fill: string, role: SceneDecoration["role"], opacity: number) => {
    const tip = pt(centre.x + Math.cos(angle) * length, centre.y + Math.sin(angle) * length);
    const c1 = pt(centre.x + Math.cos(angle - 0.5) * width, centre.y + Math.sin(angle - 0.5) * width);
    const c2 = pt(centre.x + Math.cos(angle + 0.5) * width, centre.y + Math.sin(angle + 0.5) * width);
    decorations.push({ kind: "path", d: `M${centre.x} ${centre.y}Q${c1.x} ${c1.y} ${tip.x} ${tip.y}Q${c2.x} ${c2.y} ${centre.x} ${centre.y}Z`, fill, opacity, clip: true, role });
  };
  /* each term: a flower of petals, one ring (or a spray) in its ink */
  points.forEach((p, k) => {
    const count = variant === 2 ? 5 + pick(seed, "petals:count", 2) : 10 + pick(seed, "petals:count", 3) * 2;
    const spread = variant === 2 ? Math.PI * 0.9 : Math.PI * 2;
    const base = variant === 2 ? Math.atan2(p.y - (F.y + F.height / 2), p.x - (F.x + F.width / 2)) - spread / 2 : unit(seed, `petals:rot:${k}`) * Math.PI;
    for (let i = 0; i < count; i += 1) {
      const a = base + (i * spread) / count;
      petal(p, a, size * (variant === 1 ? 1.2 : 1), size * 0.5, url(`petal-${(k + (variant === 1 ? i % 2 : 0)) % pal.colours.length}`), "term", 0.86);
    }
    decorations.push({ kind: "circle", cx: p.x, cy: p.y, r: r1(size * 0.16), fill: INK, role: "term" });
    nodes.push(nodeAt(k, content, p, box(p.x - size * 1.2, p.y - size * 1.2, size * 2.4, size * 2.4), F));
  });
  /* an association: a stem between two flowers with small leaves, along the route */
  for (const edge of content.edges) {
    const a = points[edge.from] as Point;
    const b = points[edge.to] as Point;
    const path = route(a, b, variant, F);
    decorations.push(polyline(path, INK, 6, "association"));
    along(path, 3).forEach((leaf, i) => petal(leaf, Math.atan2(b.y - a.y, b.x - a.x) + (i % 2 === 0 ? 1 : -1) * Math.PI / 2, size * 0.5, size * 0.22, "#3fa684", "association", 0.9));
    connectors.push(link(edge, segmentBox(a, b, size * 0.5), F));
  }
  decorations.push({ kind: "rect", x: F.x, y: F.y, width: F.width, height: F.height, fill: url("grain"), role: "texture" });
  return { palette: pal, fieldFill: pal.paper, defs, nodes, connectors, decorations };
}

/* ================= 12 · WAVES — the homage's flowing bands ================= */
function layoutWaves({ content, variant, seed, frame: F, points }: Input): Layout {
  const pal = palette("waves", ["#2fb3c9", "#f2c230", "#e4472c", "#3fa684", "#2f5fb8", "#d49454", "#c81d6b", "#7b5ea7"]);
  const defs: SceneDef[] = [grain(seed, 0.1), ...pal.colours.map((c, i) => linear(`wave-${i}`, c, "#ffffff", variant === 1 ? 90 : 0))];
  const decorations: SceneDecoration[] = [];
  const nodes: SceneNode[] = [];
  const connectors: SceneConnector[] = [];
  const vertical = variant === 1;
  const thickness = Math.min(F.width, F.height) * (0.06 + pick(seed, "waves:thick", 3) * 0.01);
  const fieldWaves = 7 + pick(seed, "waves:field", 5);
  const fieldAmplitude = 18 + pick(seed, "waves:amp", 4) * 6;
  const wave = (through: Point, amplitude: number, phase: number, offset: number, width: number, fill: string, role: SceneDecoration["role"], opacity: number) => {
    const pts: Point[] = [];
    const span = vertical ? F.height : F.width;
    for (let s = 0; s <= span; s += span / 24) {
      const wobble = Math.sin((s / span) * Math.PI * 2 + phase) * amplitude;
      pts.push(vertical ? pt(through.x + offset + wobble, F.y + s) : pt(F.x + s, through.y + offset + wobble));
    }
    const d = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x} ${p.y}`).join("");
    decorations.push({ kind: "path", d, fill: "none", stroke: fill, strokeWidth: width, opacity, clip: true, role });
  };
  /* the field: faint waves */
  for (let i = 0; i < fieldWaves; i += 1) wave(pt(F.x + F.width * (i + 0.5) / fieldWaves, F.y + F.height * (i + 0.5) / fieldWaves), fieldAmplitude, i, 0, 2, INK, "field", 0.2);
  /* each term: a bundle of three waves through its point */
  points.forEach((p, k) => {
    const phase = unit(seed, `waves:phase:${k}`) * Math.PI * 2;
    for (let i = -1; i <= 1; i += 1) wave(p, thickness * 0.9, phase, i * thickness * 1.15, thickness * 0.85, url(`wave-${(k + (variant === 2 ? Math.abs(i) : 0)) % pal.colours.length}`), "term", 0.92);
    nodes.push(nodeAt(k, content, p, vertical ? box(p.x - thickness * 2, F.y, thickness * 4, F.height) : box(F.x, p.y - thickness * 2, F.width, thickness * 4), F));
  });
  /* an association: the two bundles' crossing, a knot along the route */
  for (const edge of content.edges) {
    const a = points[edge.from] as Point;
    const b = points[edge.to] as Point;
    const path = route(a, b, variant === 2 ? 2 : 0, F);
    decorations.push(polyline(path, pal.paper, 16, "association"));
    decorations.push(polyline(path, INK, 6, "association"));
    connectors.push(link(edge, segmentBox(a, b, 20), F));
  }
  decorations.push({ kind: "rect", x: F.x, y: F.y, width: F.width, height: F.height, fill: url("grain"), role: "texture" });
  return { palette: pal, fieldFill: pal.paper, defs, nodes, connectors, decorations };
}

/* ================= 13 · CUBES — the homage's isometric lattice ================= */
function layoutCubes({ content, variant, seed, frame: F, points }: Input): Layout {
  const pal = palette("cubes", ["#2fb3c9", "#f2c230", "#e4472c", "#3fa684", "#2f5fb8", "#c81d6b", "#d49454", "#7b5ea7"]);
  const defs: SceneDef[] = [grain(seed, 0.1)];
  const decorations: SceneDecoration[] = [];
  const nodes: SceneNode[] = [];
  const connectors: SceneConnector[] = [];
  const s = Math.min(F.width, F.height) * (0.045 + pick(seed, "cubes:size", 5) * 0.005);
  const h = s * 0.5;
  const cube = (c: Point, top: string, left: string, right: string, role: SceneDecoration["role"], opacity: number) => {
    decorations.push({ kind: "polygon", points: [pt(c.x, c.y - s), pt(c.x + s * 0.866, c.y - h), pt(c.x, c.y), pt(c.x - s * 0.866, c.y - h)], fill: top, opacity, clip: true, role });
    decorations.push({ kind: "polygon", points: [pt(c.x - s * 0.866, c.y - h), pt(c.x, c.y), pt(c.x, c.y + s), pt(c.x - s * 0.866, c.y + h)], fill: left, opacity, clip: true, role });
    decorations.push({ kind: "polygon", points: [pt(c.x, c.y), pt(c.x + s * 0.866, c.y - h), pt(c.x + s * 0.866, c.y + h), pt(c.x, c.y + s)], fill: right, opacity, clip: true, role });
  };
  const reach = Math.min(F.width, F.height) * 0.2;
  const dx = s * 1.732;
  const dy = s * 1.5;
  const cols = Math.ceil(F.width / dx) + 2;
  const rows = Math.ceil(F.height / dy) + 2;
  for (let r = 0; r < rows; r += 1) for (let c = 0; c < cols; c += 1) {
    const x = F.x + c * dx + (r % 2 === 1 ? dx / 2 : 0) - dx;
    const y = F.y + r * dy - dy;
    if (variant === 2 && pick(seed, `cubes:skip:${r}:${c}`, 3) === 0) continue;
    let nearest = -1;
    let near = Infinity;
    points.forEach((p, k) => { const d = dist({ x, y }, p); if (d < near) { near = d; nearest = k; } });
    const w = Math.max(0, 1 - near / reach);
    if (w > 0.35) {
      const ink = pal.colours[nearest % pal.colours.length] as string;
      cube({ x, y }, ink, INK, "#ffffff", "term", 0.95);
    } else cube({ x, y }, variant === 1 ? "#e6e2d6" : "#ece8dc", "#cfc9b9", "#f7f4ea", "field", 0.9);
  }
  points.forEach((p, k) => nodes.push(nodeAt(k, content, p, box(p.x - reach, p.y - reach, reach * 2, reach * 2), F)));
  /* an association: a run of black-topped cubes between the two clusters, along the route */
  for (const edge of content.edges) {
    const a = points[edge.from] as Point;
    const b = points[edge.to] as Point;
    along(route(a, b, variant, F), Math.max(3, Math.round(dist(a, b) / (s * 1.6)))).forEach((c) => cube(c, INK, "#3a3835", "#8c887f", "association", 1));
    connectors.push(link(edge, segmentBox(a, b, s), F));
  }
  decorations.push({ kind: "rect", x: F.x, y: F.y, width: F.width, height: F.height, fill: url("grain"), role: "texture" });
  return { palette: pal, fieldFill: pal.paper, defs, nodes, connectors, decorations };
}

/* ================= 14 · ARCS — the BC stamp's concentric bands ================= */
function layoutArcs({ content, variant, seed, frame: F, points }: Input): Layout {
  const pal = palette("arcs", ["#7b5ea7", "#e4472c", "#f2c230", "#3fa684", "#2f5fb8", "#c81d6b", "#d49454", "#1f4491"]);
  const defs: SceneDef[] = [grain(seed, 0.1)];
  const decorations: SceneDecoration[] = [];
  const nodes: SceneNode[] = [];
  const connectors: SceneConnector[] = [];
  const band = Math.min(F.width, F.height) * (0.028 + pick(seed, "arcs:band", 4) * 0.003);
  const rings = 5 + pick(seed, "arcs:rings", 3);
  /* each term: nested arcs around its point, opening toward the frame's centre (or away, opposed) */
  points.forEach((p, k) => {
    const cx = F.x + F.width / 2;
    const cy = F.y + F.height / 2;
    const toCentre = Math.atan2(cy - p.y, cx - p.x) + (variant === 1 ? Math.PI : 0);
    const spread = variant === 2 ? Math.PI * 1.6 : Math.PI;
    for (let i = 0; i < rings; i += 1) {
      const r = band * (1.5 + i * 1.6);
      const a1 = toCentre - spread / 2 + (variant === 2 ? i * 0.25 : 0);
      const a2 = a1 + spread;
      const p1 = pt(p.x + Math.cos(a1) * r, p.y + Math.sin(a1) * r);
      const p2 = pt(p.x + Math.cos(a2) * r, p.y + Math.sin(a2) * r);
      decorations.push({ kind: "path", d: `M${p1.x} ${p1.y}A${r1(r)} ${r1(r)} 0 ${spread > Math.PI ? 1 : 0} 1 ${p2.x} ${p2.y}`, fill: "none", stroke: pal.colours[(k * 2 + i) % pal.colours.length] as string, strokeWidth: r1(band), clip: true, role: "term" });
    }
    decorations.push({ kind: "circle", cx: p.x, cy: p.y, r: r1(band * 0.9), fill: INK, role: "term" });
    nodes.push(nodeAt(k, content, p, box(p.x - band * 11, p.y - band * 11, band * 22, band * 22), F));
  });
  /* an association: a band that runs from one arc set into the other */
  for (const edge of content.edges) {
    const a = points[edge.from] as Point;
    const b = points[edge.to] as Point;
    const path = route(a, b, variant === 0 ? 2 : variant, F);
    decorations.push(polyline(path, pal.paper, band * 1.6, "association"));
    decorations.push(polyline(path, INK, band * 0.7, "association"));
    connectors.push(link(edge, segmentBox(a, b, band * 2), F));
  }
  decorations.push({ kind: "rect", x: F.x, y: F.y, width: F.width, height: F.height, fill: url("grain"), role: "texture" });
  return { palette: pal, fieldFill: pal.paper, defs, nodes, connectors, decorations };
}

/* ================= 15 · MOIRE — two line screens, interfering ================= */
function layoutMoire({ content, variant, seed, frame: F, points }: Input): Layout {
  const pal = palette("moire", ["#1f4491", "#e4472c", "#3fa684", "#d49454"]);
  const defs: SceneDef[] = [grain(seed, 0.08)];
  const decorations: SceneDecoration[] = [];
  const nodes: SceneNode[] = [];
  const connectors: SceneConnector[] = [];
  const pitch = 11 + pick(seed, "moire:pitch", 5);
  const long = Math.max(F.width, F.height) * 1.5;
  const fieldTilt = ((pick(seed, "moire:tilt", 5) - 2) * Math.PI) / 36;
  const reach = Math.min(F.width, F.height) * 0.3;
  const screen = (centre: Point, angle: number, colour: string, radius: number, role: SceneDecoration["role"], opacity: number) => {
    const dir = pt(Math.cos(angle), Math.sin(angle));
    const nrm = pt(-dir.y, dir.x);
    for (let i = -Math.ceil(radius / pitch); i <= Math.ceil(radius / pitch); i += 1) {
      const off = i * pitch;
      const half = Math.sqrt(Math.max(0, radius * radius - off * off));
      if (variant === 1) {
        /* radial: rings instead of lines */
        if (i <= 0) continue;
        decorations.push({ kind: "circle", cx: centre.x, cy: centre.y, r: r1(off), fill: "none", stroke: colour, strokeWidth: 1.6, opacity, clip: true, role });
        continue;
      }
      decorations.push({ kind: "line", x1: r1(centre.x + nrm.x * off - dir.x * half), y1: r1(centre.y + nrm.y * off - dir.y * half), x2: r1(centre.x + nrm.x * off + dir.x * half), y2: r1(centre.y + nrm.y * off + dir.y * half), stroke: colour, width: 1.6, opacity, clip: true, role });
    }
    void long;
  };
  /* the field: one faint screen across the frame */
  screen(pt(F.x + F.width / 2, F.y + F.height / 2), (variant === 2 ? Math.PI / 6 : 0) + fieldTilt, INK, long, "field", 0.16);
  /* each term: a screen of its own angle, centred on its point */
  points.forEach((p, k) => {
    screen(p, (k + 1) * (Math.PI / 7) + (variant === 2 ? Math.PI / 6 : 0), pal.colours[k % pal.colours.length] as string, reach, "term", 0.9);
    nodes.push(nodeAt(k, content, p, box(p.x - reach, p.y - reach, reach * 2, reach * 2), F));
  });
  /* an association: a third screen on the route between two, where their lines interfere */
  for (const edge of content.edges) {
    const a = points[edge.from] as Point;
    const b = points[edge.to] as Point;
    const mid = along(route(a, b, variant === 1 ? 2 : variant, F), 1)[0] as Point;
    screen(mid, Math.atan2(b.y - a.y, b.x - a.x) + Math.PI / 2, INK, reach * 0.55, "association", 0.85);
    connectors.push(link(edge, box(mid.x - reach * 0.55, mid.y - reach * 0.55, reach * 1.1, reach * 1.1), F));
  }
  decorations.push({ kind: "rect", x: F.x, y: F.y, width: F.width, height: F.height, fill: url("grain"), role: "texture" });
  return { palette: pal, fieldFill: pal.paper, defs, nodes, connectors, decorations };
}

/* ================= 16 · SCATTER — soft discs, a beam between ================= */
function layoutScatter({ content, variant, seed, frame: F, points }: Input): Layout {
  const pal = palette("scatter", ["#e4472c", "#2f5fb8", "#f2c230", "#3fa684", "#c81d6b", "#d49454", "#7b5ea7", "#2fb3c9"]);
  const defs: SceneDef[] = [grain(seed, 0.14), ...pal.colours.map((c, i) => radial(`soft-${i}`, c, c, 0)), linear("scatter-ground", "#fbfaf5", "#ebe6d8", 90)];
  const decorations: SceneDecoration[] = [{ kind: "rect", x: F.x, y: F.y, width: F.width, height: F.height, fill: url("scatter-ground"), role: "field" }];
  const nodes: SceneNode[] = [];
  const connectors: SceneConnector[] = [];
  const big = Math.min(F.width, F.height) * (0.17 + pick(seed, "scatter:big", 4) * 0.015);
  /* the field: small soft discs, denser toward the motifs */
  const count = (variant === 2 ? 200 : 100) + pick(seed, "scatter:count", 5) * 10;
  for (let i = 0; i < count; i += 1) {
    const x = F.x + unit(seed, `scatter:x:${i}`) * F.width;
    const y = F.y + unit(seed, `scatter:y:${i}`) * F.height;
    const near = Math.min(...points.map((p) => dist({ x, y }, p)));
    const w = Math.max(0, 1 - near / (big * 2.2));
    if (variant !== 2 && w < 0.15 && unit(seed, `scatter:keep:${i}`) < 0.6) continue;
    decorations.push({ kind: "circle", cx: r1(x), cy: r1(y), r: r1(4 + w * 14), fill: url(`soft-${i % pal.colours.length}`), opacity: 0.55 + w * 0.4, role: "field", clip: true });
  }
  /* each term: a large soft disc with a firm core */
  points.forEach((p, k) => {
    decorations.push({ kind: "circle", cx: p.x, cy: p.y, r: r1(big), fill: url(`soft-${k % pal.colours.length}`), role: "term", clip: true });
    decorations.push({ kind: "circle", cx: p.x, cy: p.y, r: r1(big * 0.42), fill: pal.colours[k % pal.colours.length] as string, role: "term" });
    nodes.push(nodeAt(k, content, p, box(p.x - big, p.y - big, big * 2, big * 2), F));
  });
  /* an association: a beam of paper and ink between two cores, along the route */
  for (const edge of content.edges) {
    const a = points[edge.from] as Point;
    const b = points[edge.to] as Point;
    const path = route(a, b, variant === 0 ? 0 : variant, F);
    decorations.push(polyline(path, pal.paper, 22, "association", 0.9));
    decorations.push(polyline(path, INK, 7, "association"));
    connectors.push(link(edge, segmentBox(a, b, 20), F));
  }
  decorations.push({ kind: "rect", x: F.x, y: F.y, width: F.width, height: F.height, fill: url("grain"), role: "texture" });
  return { palette: pal, fieldFill: "#fbfaf5", defs, nodes, connectors, decorations };
}

/* ---- the scene ---- */

const LAYOUTS: Readonly<Record<ExplorationTemplateId, (input: Input) => Layout>> = Object.freeze({
  DOTS: layoutDots,
  SPOTS: layoutSpots,
  CHEVRON: layoutChevron,
  CROSSFIELD: layoutCrossfield,
  LINES: layoutLines,
  GRID: layoutGrid,
  RAYS: layoutRays,
  OVERLAP: layoutOverlap,
  HALFTONE: layoutHalftone,
  STRIPES: layoutStripes,
  PETALS: layoutPetals,
  WAVES: layoutWaves,
  CUBES: layoutCubes,
  ARCS: layoutArcs,
  MOIRE: layoutMoire,
  SCATTER: layoutScatter,
});

const TOPOLOGY_WORDS: Readonly<Record<string, string>> = Object.freeze({
  LINEAR_PATH: "linear path",
  BINARY_FORK: "binary fork",
  BINARY_CONVERGENCE: "binary convergence",
});

export function topologyWord(family: string): string {
  return TOPOLOGY_WORDS[family] ?? family.toLowerCase().replaceAll("_", " ");
}

export function buildExplorationScene(
  content: SceneContent,
  templateId: ExplorationTemplateId,
  variantId: number,
  seed: number,
  frame: Frame = VIEW_FRAME,
): ExplorationScene {
  const variants = EXPLORATION_TEMPLATE_VARIANTS[templateId];
  if (!Number.isInteger(variantId) || variantId < 0 || variantId >= variants.length) throw new Error("INVALID_PRESENTATION_VARIANT");
  if (!getCompatibleTemplates(content).includes(templateId)) throw new Error("TEMPLATE_INCOMPATIBLE");
  const points = termPositions(content.nodes.length, variantId, seed, content.semanticHash, frame);
  const layout = (LAYOUTS[templateId])({ content, variant: variantId, seed, frame, points, semanticHash: content.semanticHash });
  const variantName = variants[variantId] ?? "";
  return {
    presentationVersion: EXPLORATION_PRESENTATION_VERSION,
    templateId,
    variantId,
    variantName,
    presentationSeed: seed,
    seedChain: [`semantic ${content.semanticHash.slice(0, 12)}`, `seed ${seed}`, `skeleton ${content.nodes.length} terms · variant ${variantId}`, `frame ${frame.width}×${frame.height}`],
    palette: layout.palette,
    frame,
    fieldFill: layout.fieldFill,
    defs: layout.defs,
    nodes: layout.nodes,
    connectors: layout.connectors,
    decorations: layout.decorations,
    altText: `${content.categoryLabel} exploration view from ${content.seedLabel}: ${content.termCount} ${content.termCount === 1 ? "term" : "terms"} and ${content.associationCount} qualified generic ${content.associationCount === 1 ? "association" : "associations"}, drawn as ${EXPLORATION_TEMPLATE_NAMES[templateId]} (${variantName}).`,
  };
}
