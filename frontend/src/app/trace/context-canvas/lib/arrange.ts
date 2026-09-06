/* Context Canvas — the arrangement (§7g). Pure geometry in world units
   (CSS px at zoom 1); nothing here reads or writes the composition state,
   which stays with features/trace-v49/context/canvas (reducer, state,
   persistence). Four LAYOUT PRESETS over exactly the same governed
   object and contexts — they move things, and change nothing else:

   overview  the object at the centre; Medium left, Theme right,
             Movement below, each the same distance from the object
   focus     the object at the left; one dimension read in full beside
             it; the other two kept compact beneath the object
   columns   the object above three equal columns, for comparison
   dense     the object above three bands, for objects with many terms

   Every chip is one size. A FIELD is drawn from its default place and
   grows to hold its chips wherever they have been dragged, so its label
   never lies; a dimension with nothing on the canvas is a COMPACT
   marker (one line: the word, "Not recorded" or "n set aside"), never
   a large empty region. Nothing in the picture ranks one context above
   another or reads distance as strength. */

import {
  CONTEXT_CANVAS_MAX_ZOOM,
  CONTEXT_CANVAS_MIN_ZOOM,
  type ContextCanvasPosition,
  type ContextCanvasViewport,
  type ContextCanvasViewportSize,
} from "@/features/trace-v49/context/canvas/types";
import type { ContextKind, LayoutPreset } from "./content";

export const OBJECT = Object.freeze({ width: 320, height: 156 });
export const CHIP = Object.freeze({ width: 280, height: 52 });
export const COMPACT = Object.freeze({ width: 320, height: 36 });
/* the one distance from the object's edge to every field's edge — room
   for a connection wire with its wording where wires are drawn */
export const RING = 72;
export const RING_WIRED = 160;
export const RING_COLUMNS = 110;
export function ringFor(preset: LayoutPreset): number {
  return preset === "overview" || preset === "focus" ? RING_WIRED : preset === "columns" ? RING_COLUMNS : RING;
}
/* inside a field: the edge to its chips, the room for its label, and the
   gap between chips; between fields in a row */
export const FIELD_PAD = 20;
export const FIELD_HEAD = 60;
export const PITCH = 16;
export const GAP = 24;
export const FIELD_MIN = Object.freeze({
  width: CHIP.width + FIELD_PAD * 2,
  height: FIELD_HEAD + CHIP.height + FIELD_PAD,
});
/* dense: the label column at the left of a band, chips per row, and the
   first row's offset under the band's word */
export const DENSE_LABEL = 176;
export const DENSE_PER_ROW = 3;
export const DENSE_ROW_TOP = 44;

export const KIND_ORDER: readonly ContextKind[] = Object.freeze(["medium", "theme", "movement_context"]);

export interface Size {
  readonly width: number;
  readonly height: number;
}

export interface Box {
  readonly x: number;
  readonly y: number;
  readonly width: number;
  readonly height: number;
}

export interface Bounds extends Box {
  readonly empty: boolean;
}

export interface ArrangedNode {
  readonly id: string;
  readonly isRoot: boolean;
  readonly kind: ContextKind | null;
  readonly position: ContextCanvasPosition;
}

export type FieldState = "filled" | "set_aside" | "not_recorded";

export interface Field {
  readonly kind: ContextKind;
  readonly box: Box;
  readonly visible: number;
  readonly total: number;
  readonly state: FieldState;
  readonly compact: boolean;
}

export interface LayoutInput {
  readonly preset: LayoutPreset;
  readonly focusKind: ContextKind;
}

type Counts = Readonly<Record<ContextKind, number>>;

/* a field's box for `n` chips (at least one) laid out as a column or as
   rows of `perRow` */
function fieldSize(n: number, perRow: number): Size {
  const chips = Math.max(1, n);
  const rows = Math.ceil(chips / perRow);
  const cols = Math.min(chips, perRow);
  return Object.freeze({
    width: FIELD_PAD * 2 + cols * CHIP.width + (cols - 1) * PITCH,
    height: FIELD_HEAD + rows * CHIP.height + (rows - 1) * PITCH + FIELD_PAD,
  });
}

/* the fields' default places beside an object at `root` for a preset,
   each sized for `counts[kind]` chips; `perRow` per kind tells how chips
   flow inside */
export function defaultFields(
  root: ContextCanvasPosition,
  counts: Counts,
  layout: LayoutInput,
): Readonly<Record<ContextKind, Readonly<{ box: Box; perRow: number; chipX: number }>>> {
  const centreX = root.x + OBJECT.width / 2;
  const centreY = root.y + OBJECT.height / 2;
  const ring = ringFor(layout.preset);
  const below = root.y + OBJECT.height + ring;
  if (layout.preset === "columns") {
    const columnWidth = FIELD_MIN.width;
    const total = 3 * columnWidth + 2 * GAP;
    const left = Math.round(centreX - total / 2);
    const entry = (kind: ContextKind, index: number) => {
      const size = fieldSize(counts[kind], 1);
      const x = left + index * (columnWidth + GAP);
      return Object.freeze({ box: Object.freeze({ x, y: below, width: columnWidth, height: size.height }), perRow: 1, chipX: x + FIELD_PAD });
    };
    return Object.freeze({
      medium: entry("medium", 0),
      theme: entry("theme", 1),
      movement_context: entry("movement_context", 2),
    });
  }
  if (layout.preset === "dense") {
    const width = FIELD_PAD * 2 + DENSE_LABEL + DENSE_PER_ROW * CHIP.width + (DENSE_PER_ROW - 1) * PITCH;
    let y = below;
    const out: Partial<Record<ContextKind, Readonly<{ box: Box; perRow: number; chipX: number }>>> = {};
    for (const kind of KIND_ORDER) {
      const chips = Math.max(1, counts[kind]);
      const rows = Math.ceil(chips / DENSE_PER_ROW);
      const height = DENSE_ROW_TOP + FIELD_PAD + rows * CHIP.height + (rows - 1) * PITCH;
      out[kind] = Object.freeze({
        box: Object.freeze({ x: root.x, y, width, height }),
        perRow: DENSE_PER_ROW,
        chipX: root.x + FIELD_PAD + DENSE_LABEL,
      });
      y += height + GAP;
    }
    return out as Readonly<Record<ContextKind, Readonly<{ box: Box; perRow: number; chipX: number }>>>;
  }
  if (layout.preset === "focus") {
    const focus = layout.focusKind;
    const others = KIND_ORDER.filter((kind) => kind !== focus);
    const focusPerRow = counts[focus] > 6 ? 2 : 1;
    const focusSize = fieldSize(counts[focus], focusPerRow);
    const focusX = root.x + OBJECT.width + ring;
    const out: Partial<Record<ContextKind, Readonly<{ box: Box; perRow: number; chipX: number }>>> = {
      [focus]: Object.freeze({
        box: Object.freeze({ x: focusX, y: root.y, width: focusSize.width, height: focusSize.height }),
        perRow: focusPerRow,
        chipX: focusX + FIELD_PAD,
      }),
    };
    let y = below;
    for (const kind of others) {
      const size = fieldSize(counts[kind], 1);
      out[kind] = Object.freeze({
        box: Object.freeze({ x: root.x, y, width: FIELD_MIN.width, height: size.height }),
        perRow: 1,
        chipX: root.x + FIELD_PAD,
      });
      y += size.height + GAP;
    }
    return out as Readonly<Record<ContextKind, Readonly<{ box: Box; perRow: number; chipX: number }>>>;
  }
  /* overview */
  const column = (kind: ContextKind, x: number) => {
    const size = fieldSize(counts[kind], 1);
    return Object.freeze({
      box: Object.freeze({ x, y: Math.round(centreY - size.height / 2), width: FIELD_MIN.width, height: size.height }),
      perRow: 1,
      chipX: x + FIELD_PAD,
    });
  };
  const medium = column("medium", root.x - ring - FIELD_MIN.width);
  const theme = column("theme", root.x + OBJECT.width + ring);
  const movementChips = Math.max(1, counts.movement_context);
  const movementPerRow = Math.min(movementChips, 3);
  const movementSize = fieldSize(counts.movement_context, movementPerRow);
  const movementX = Math.round(centreX - movementSize.width / 2);
  /* a movement row wider than the object and its rings would run under
     the side columns: then it stands below them instead */
  const crossesColumns = movementX < medium.box.x + medium.box.width || movementX + movementSize.width > theme.box.x;
  const columnsBottom = Math.max(medium.box.y + medium.box.height, theme.box.y + theme.box.height);
  const movementY = crossesColumns ? Math.max(below, columnsBottom + GAP) : below;
  return Object.freeze({
    medium,
    theme,
    movement_context: Object.freeze({
      box: Object.freeze({ x: movementX, y: movementY, width: movementSize.width, height: movementSize.height }),
      perRow: movementPerRow,
      chipX: movementX + FIELD_PAD,
    }),
  });
}

/* where a field's compact marker stands when it holds no chip: at the
   field's default place, one line tall */
function compactBox(base: Box, preset: LayoutPreset): Box {
  if (preset === "dense") return Object.freeze({ x: base.x, y: base.y, width: base.width, height: COMPACT.height });
  if (preset === "overview") {
    /* centred on the field's default place */
    return Object.freeze({
      x: Math.round(base.x + base.width / 2 - COMPACT.width / 2),
      y: Math.round(base.y + base.height / 2 - COMPACT.height / 2),
      width: COMPACT.width,
      height: COMPACT.height,
    });
  }
  return Object.freeze({ x: base.x, y: base.y, width: Math.max(COMPACT.width, Math.min(base.width, FIELD_MIN.width)), height: COMPACT.height });
}

/* the initial layout, and Arrange: the object at the origin, its chips in
   their fields in the order the items are given (the projection's order) */
export function arrangeWith(
  rootId: string,
  items: readonly Readonly<{ id: string; kind: ContextKind | null }>[],
  layout: LayoutInput,
): Readonly<Record<string, ContextCanvasPosition>> {
  const root = Object.freeze({ x: 0, y: 0 });
  const out: Record<string, ContextCanvasPosition> = { [rootId]: root };
  const of = (kind: ContextKind | null) => items.filter((item) => item.kind === kind);
  const fields = defaultFields(root, {
    medium: of("medium").length,
    theme: of("theme").length,
    movement_context: of("movement_context").length,
  }, layout);
  for (const kind of KIND_ORDER) {
    const field = fields[kind];
    const chipY0 = layout.preset === "dense" ? field.box.y + DENSE_ROW_TOP : field.box.y + FIELD_HEAD;
    of(kind).forEach((item, i) => {
      const row = Math.floor(i / field.perRow);
      const col = i % field.perRow;
      out[item.id] = Object.freeze({
        x: field.chipX + col * (CHIP.width + PITCH),
        y: chipY0 + row * (CHIP.height + PITCH),
      });
    });
  }
  /* an entity without a governed kind never occurs in governed mode; if it
     did it would stand below everything rather than be dropped */
  const bottom = Math.max(...KIND_ORDER.map((kind) => fields[kind].box.y + fields[kind].box.height));
  of(null).forEach((item, i) => {
    out[item.id] = Object.freeze({ x: root.x + i * (CHIP.width + PITCH), y: bottom + ringFor(layout.preset) });
  });
  return Object.freeze(out);
}

/* the three fields as they stand now: each from its default place beside
   the object (wherever the object is), grown to hold its chips wherever
   they are; an empty one is a compact marker at its default place */
export function fieldsOf(
  nodes: readonly ArrangedNode[],
  totals: Counts,
  layout: LayoutInput,
): readonly Field[] {
  const root = nodes.find((node) => node.isRoot);
  const origin = root?.position ?? Object.freeze({ x: 0, y: 0 });
  const visibleCount = (kind: ContextKind) => nodes.filter((node) => !node.isRoot && node.kind === kind).length;
  const defaults = defaultFields(origin, {
    medium: visibleCount("medium"),
    theme: visibleCount("theme"),
    movement_context: visibleCount("movement_context"),
  }, layout);
  return Object.freeze(KIND_ORDER.map((kind) => {
    const chips = nodes.filter((node) => !node.isRoot && node.kind === kind);
    const total = totals[kind];
    if (chips.length === 0) {
      return Object.freeze({
        kind,
        box: compactBox(defaults[kind].box, layout.preset),
        visible: 0,
        total,
        state: total > 0 ? "set_aside" as const : "not_recorded" as const,
        compact: true,
      });
    }
    const head = layout.preset === "dense" ? DENSE_ROW_TOP : FIELD_HEAD;
    const padded = chips.map((chip) => {
      const box = boxOf(chip);
      return Object.freeze({
        x: box.x - FIELD_PAD,
        y: box.y - head,
        width: box.width + FIELD_PAD * 2,
        height: box.height + head + FIELD_PAD,
      });
    });
    return Object.freeze({
      kind,
      box: unionBox([defaults[kind].box, ...padded]) ?? defaults[kind].box,
      visible: chips.length,
      total,
      state: "filled" as const,
      compact: false,
    });
  }));
}

export function itemSize(isRoot: boolean): Size {
  return isRoot ? OBJECT : CHIP;
}

export function boxOf(node: Pick<ArrangedNode, "isRoot" | "position">): Box {
  const size = itemSize(node.isRoot);
  return Object.freeze({ x: node.position.x, y: node.position.y, width: size.width, height: size.height });
}

export function unionBox(boxes: readonly Box[]): Box | null {
  if (boxes.length === 0) return null;
  let minX = Number.POSITIVE_INFINITY;
  let minY = Number.POSITIVE_INFINITY;
  let maxX = Number.NEGATIVE_INFINITY;
  let maxY = Number.NEGATIVE_INFINITY;
  for (const box of boxes) {
    minX = Math.min(minX, box.x);
    minY = Math.min(minY, box.y);
    maxX = Math.max(maxX, box.x + box.width);
    maxY = Math.max(maxY, box.y + box.height);
  }
  return Object.freeze({ x: minX, y: minY, width: maxX - minX, height: maxY - minY });
}

export function boxesOverlap(a: Box, b: Box, gap = 0): boolean {
  return a.x < b.x + b.width + gap
    && a.x + a.width + gap > b.x
    && a.y < b.y + b.height + gap
    && a.y + a.height + gap > b.y;
}

export function boundsOf(
  nodes: readonly Pick<ArrangedNode, "isRoot" | "position">[],
  fields: readonly Pick<Field, "box">[] = [],
): Bounds {
  const union = unionBox([...nodes.map(boxOf), ...fields.map((field) => field.box)]);
  if (!union) return Object.freeze({ x: 0, y: 0, width: 0, height: 0, empty: true });
  return Object.freeze({ ...union, empty: false });
}

/* fit a box into the stage: padded, centred, never beyond maxZoom so a
   small canvas is not blown up to fill the stage */
export function fitBounds(
  bounds: Box & { readonly empty?: boolean },
  size: ContextCanvasViewportSize,
  pad = 48,
  maxZoom = 1,
): ContextCanvasViewport {
  if (bounds.empty || bounds.width <= 0 || bounds.height <= 0) return Object.freeze({ x: 0, y: 0, zoom: 1 });
  const width = Number.isFinite(size.width) && size.width > 0 ? size.width : 1;
  const height = Number.isFinite(size.height) && size.height > 0 ? size.height : 1;
  const raw = Math.min(
    Math.max(1, width - pad * 2) / bounds.width,
    Math.max(1, height - pad * 2) / bounds.height,
  );
  const zoom = Math.min(maxZoom, CONTEXT_CANVAS_MAX_ZOOM, Math.max(CONTEXT_CANVAS_MIN_ZOOM, raw));
  return Object.freeze({
    x: (width - bounds.width * zoom) / 2 - bounds.x * zoom,
    y: (height - bounds.height * zoom) / 2 - bounds.y * zoom,
    zoom,
  });
}

/* a free slot for a chip added back: its place in the arrangement of
   everything visible plus itself, relative to where the object stands
   now, nudged while it would lie over a chip that has been moved there */
export function slotFor(
  entityId: string,
  kind: ContextKind | null,
  rootId: string,
  visible: readonly ArrangedNode[],
  layout: LayoutInput,
): ContextCanvasPosition {
  const root = visible.find((node) => node.isRoot)?.position ?? Object.freeze({ x: 0, y: 0 });
  const ideal = arrangeWith(rootId, [
    ...visible.filter((node) => !node.isRoot).map((node) => ({ id: node.id, kind: node.kind })),
    { id: entityId, kind },
  ], layout)[entityId] ?? Object.freeze({ x: 0, y: 0 });
  const occupied = visible.map(boxOf);
  let position = Object.freeze({ x: ideal.x + root.x, y: ideal.y + root.y });
  let attempt = 0;
  while (
    attempt < 12
    && occupied.some((box) => boxesOverlap(box, { x: position.x, y: position.y, width: CHIP.width, height: CHIP.height }, PITCH))
  ) {
    attempt += 1;
    position = Object.freeze({ x: position.x + 24, y: position.y + 24 });
  }
  return position;
}

/* the connections (§7g): governed Context V1 has ONE connection class —
   the selected object to one of its context representations — read as
   three wordings, the registry's own: Medium "classified as", Theme
   "themed as", Movement "curated within". Drawn as WIRES: orthogonal,
   1 px, neutral, no arrowhead, no weight, the wording ON the wire,
   interrupting it; stronger (and in the dimension's accent) only while
   a chip of the wire is hovered or selected — focus, never strength.
   Never between two terms or two objects, never for a dimension not
   recorded. Anchors: the object's side that faces the field — right →
   Theme chip's left edge, left → Medium chip's right edge, bottom →
   Movement chip's top edge — and where a chip is approached from the
   side it gets its own wire; where a stack of chips is approached from
   above (Columns, the compact stacks in Focus, the bands in Dense) the
   wire reaches the stack's first chip and the stack is the wire's group.
   The wording sits on the longest segment outside the field, at least
   20 px from either card and 24 px from the field's word. */
export interface Connector {
  readonly id: string;
  readonly kind: ContextKind;
  readonly label: string;
  readonly points: readonly ContextCanvasPosition[];
  readonly labelAt: ContextCanvasPosition;
  readonly labelVertical: boolean;
  readonly chipIds: readonly string[];
}

/* the lane a wire turns in, past the object's edge; the wording's clearance
   from either card; its box, for keeping wordings apart */
/* a drag ends in a determination: a context snaps to a slot of its own
   field — its own (kept), or another chip's (the two change places) —
   and is put back when dropped away from its field or when the object
   itself was moved (the fields are laid out around the object) */
export type DropOutcome =
  | Readonly<{ kind: "keep" }>
  | Readonly<{ kind: "swap"; otherId: string; positions: Readonly<Record<string, ContextCanvasPosition>> }>
  | Readonly<{ kind: "put_back"; reason: "object_moved" | "outside_field" }>;

export function dropOutcome(
  nodes: readonly ArrangedNode[],
  baseline: Readonly<Record<string, ContextCanvasPosition>>,
  layout: LayoutInput,
  movedId: string,
): DropOutcome {
  const root = nodes.find((node) => node.isRoot);
  const moved = nodes.find((node) => node.id === movedId);
  if (!root || !moved) return Object.freeze({ kind: "keep" as const });
  if (moved.isRoot) return Object.freeze({ kind: "put_back" as const, reason: "object_moved" as const });
  const kind = moved.kind;
  if (!kind) return Object.freeze({ kind: "keep" as const });
  const counts: Counts = {
    medium: nodes.filter((node) => !node.isRoot && node.kind === "medium").length,
    theme: nodes.filter((node) => !node.isRoot && node.kind === "theme").length,
    movement_context: nodes.filter((node) => !node.isRoot && node.kind === "movement_context").length,
  };
  const field = defaultFields(root.position, counts, layout)[kind];
  const head = layout.preset === "dense" ? DENSE_ROW_TOP : FIELD_HEAD;
  const chips = nodes.filter((node) => !node.isRoot && node.kind === kind);
  const slots = chips.map((_, index) => Object.freeze({
    x: field.chipX + (index % field.perRow) * (CHIP.width + PITCH),
    y: field.box.y + head + Math.floor(index / field.perRow) * (CHIP.height + PITCH),
  }));
  const dist = (a: ContextCanvasPosition, b: ContextCanvasPosition) => Math.hypot(a.x - b.x, a.y - b.y);
  const nearest = slots.reduce((best, slot, index) => {
    const d = dist(slot, moved.position);
    return d < best.d ? { d, index } : best;
  }, { d: Number.POSITIVE_INFINITY, index: -1 });
  /* dropped away from every slot of its field: put back */
  if (nearest.index < 0 || nearest.d > CHIP.width) return Object.freeze({ kind: "put_back" as const, reason: "outside_field" as const });
  const origin = baseline[movedId] ?? moved.position;
  const target = slots[nearest.index];
  if (dist(target, origin) < 0.5) return Object.freeze({ kind: "keep" as const });
  const other = chips.find((chip) => chip.id !== movedId && dist(baseline[chip.id] ?? chip.position, target) < 0.5);
  if (!other) return Object.freeze({ kind: "keep" as const });
  const positions: Record<string, ContextCanvasPosition> = { ...baseline };
  positions[movedId] = P(target.x, target.y);
  positions[other.id] = P(origin.x, origin.y);
  return Object.freeze({ kind: "swap" as const, otherId: other.id, positions: Object.freeze(positions) });
}

export const LANE = 34;
export const WIRE_CLEAR = 20;
export const LABEL_H = 20;
export const labelWidth = (label: string) => label.length * 8 + 12;

const P = (x: number, y: number): ContextCanvasPosition => Object.freeze({ x: n2(x), y: n2(y) });
const n2 = (v: number) => Math.round(v * 100) / 100;

type Side = "left" | "right" | "below" | "above";

/* a wording with the run it may slide along, before the wordings are
   kept apart */
interface Draft {
  readonly id: string;
  readonly kind: ContextKind;
  readonly label: string;
  readonly points: readonly ContextCanvasPosition[];
  readonly chipIds: readonly string[];
  readonly axis: "x" | "y";
  readonly fixed: number;
  at: number;
  readonly min: number;
  readonly max: number;
  /* the wording turned along an outer vertical lane */
  readonly vertical?: boolean;
}

/* whether a polyline's segments pass through any of the boxes */
function blocked(points: readonly ContextCanvasPosition[], obstacles: readonly Box[]): boolean {
  for (let i = 1; i < points.length; i++) {
    const a = points[i - 1];
    const b = points[i];
    const sx = Math.min(a.x, b.x);
    const ex = Math.max(a.x, b.x);
    const sy = Math.min(a.y, b.y);
    const ey = Math.max(a.y, b.y);
    if (obstacles.some((o) => ex > o.x + 0.5 && sx < o.x + o.width - 0.5 && ey > o.y + 0.5 && sy < o.y + o.height - 0.5)) return true;
  }
  return false;
}

/* the side of the object a field is approached from: the axis with the
   wider clear gap wins, so a column below and to the left of the object
   is still "below" (a wire comes down to it, not sideways into it) */
function sideOf(object: Box, field: Box): Side {
  const gapX = Math.max(field.x - (object.x + object.width), object.x - (field.x + field.width), 0);
  const gapY = Math.max(field.y - (object.y + object.height), object.y - (field.y + field.height), 0);
  const dx = (field.x + field.width / 2) - (object.x + object.width / 2);
  const dy = (field.y + field.height / 2) - (object.y + object.height / 2);
  if (gapY > gapX) return dy > 0 ? "below" : "above";
  if (gapX > gapY) return dx > 0 ? "right" : "left";
  return Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? "right" : "left") : (dy > 0 ? "below" : "above");
}

function boxOfDraft(d: Draft): Box {
  const w = labelWidth(d.label);
  const x = d.axis === "x" ? d.at : d.fixed;
  const y = d.axis === "x" ? d.fixed : d.at;
  if (d.vertical) return { x: x - LABEL_H / 2, y: y - w / 2, width: LABEL_H, height: w };
  return { x: x - w / 2, y: y - LABEL_H / 2, width: w, height: LABEL_H };
}

/* keep the wordings apart: a wording that lies on another slides along
   its own run, within its clearances, away from the other */
function keepApart(drafts: Draft[]): void {
  for (let pass = 0; pass < 4; pass++) {
    let moved = false;
    for (let i = 0; i < drafts.length; i++) {
      for (let j = i + 1; j < drafts.length; j++) {
        const a = boxOfDraft(drafts[i]);
        const b = boxOfDraft(drafts[j]);
        if (!boxesOverlap(a, b, 6)) continue;
        const d = drafts[j];
        const need = d.axis === "x"
          ? Math.min(a.x + a.width, b.x + b.width) - Math.max(a.x, b.x) + 8
          : Math.min(a.y + a.height, b.y + b.height) - Math.max(a.y, b.y) + 8;
        const centreA = d.axis === "x" ? a.x + a.width / 2 : a.y + a.height / 2;
        const away = d.at >= centreA ? 1 : -1;
        const next = Math.min(d.max, Math.max(d.min, d.at + away * need));
        if (Math.abs(next - d.at) > 0.5) {
          d.at = next;
          moved = true;
        } else {
          const other = drafts[i];
          const back = Math.min(other.max, Math.max(other.min, other.at - away * need));
          if (Math.abs(back - other.at) > 0.5) {
            other.at = back;
            moved = true;
          }
        }
      }
    }
    if (!moved) return;
  }
}

function finish(drafts: Draft[]): readonly Connector[] {
  keepApart(drafts);
  return Object.freeze(drafts.map((d) => Object.freeze({
    id: d.id,
    kind: d.kind,
    label: d.label,
    points: d.points,
    labelAt: d.axis === "x" ? P(d.at, d.fixed) : P(d.fixed, d.at),
    labelVertical: d.vertical === true,
    chipIds: d.chipIds,
  })));
}

export function connectorsOf(
  nodes: readonly ArrangedNode[],
  fields: readonly Field[],
  layout: LayoutInput,
  wording: Readonly<Record<string, string>>,
): readonly Connector[] {
  const root = nodes.find((node) => node.isRoot);
  if (!root) return Object.freeze([]);
  const O = boxOf(root);
  const ocx = O.x + O.width / 2;
  const ocy = O.y + O.height / 2;
  const drafts: Draft[] = [];

  /* Dense: one lane down the bands' outer left, clear of every band's
     outline, one wire per band from the object's left edge into the
     band's first chip; the wording on the run inside the band's label
     column, clear of the band's outline and of the chip */
  if (layout.preset === "dense") {
    const laneX = Math.min(O.x, ...fields.map((f) => f.box.x)) - LANE;
    for (const field of fields) {
      if (field.state !== "filled") continue;
      const chips = nodes.filter((node) => !node.isRoot && node.kind === field.kind);
      const sorted = [...chips].sort((a, b) => a.position.y - b.position.y || a.position.x - b.position.x);
      const chip = boxOf(sorted[0]);
      const cy = chip.y + chip.height / 2;
      const label = wording[field.kind] ?? "";
      const half = labelWidth(label) / 2;
      drafts.push({
        id: `band:${field.kind}`, kind: field.kind, label,
        points: Object.freeze([P(O.x, ocy), P(laneX, ocy), P(laneX, cy), P(chip.x, cy)]),
        chipIds: Object.freeze(sorted.map((c) => c.id)),
        axis: "x", fixed: cy, at: (field.box.x + chip.x) / 2, min: field.box.x + WIRE_CLEAR + half, max: chip.x - WIRE_CLEAR - half,
      });
    }
    return finish(drafts);
  }

  for (const field of fields) {
    if (field.state !== "filled") continue;
    const chips = nodes.filter((node) => !node.isRoot && node.kind === field.kind);
    const side = sideOf(O, field.box);
    if (side === "left" || side === "right") {
      /* approached from the side: every chip its own wire */
      const right = side === "right";
      const fromX = right ? O.x + O.width : O.x;
      const laneX = right ? fromX + LANE : fromX - LANE;
      const fieldEdge = right ? field.box.x : field.box.x + field.box.width;
      for (const node of chips) {
        const chip = boxOf(node);
        const cy = chip.y + chip.height / 2;
        const toX = right ? chip.x : chip.x + chip.width;
        const straight = Math.abs(cy - ocy) < 0.5;
        const points = straight
          ? [P(fromX, ocy), P(toX, cy)]
          : [P(fromX, ocy), P(laneX, ocy), P(laneX, cy), P(toX, cy)];
        const label = wording[node.id] ?? wording[field.kind] ?? "";
        const half = labelWidth(label) / 2;
        const runStart = straight ? fromX : laneX;
        const lo = Math.min(runStart, fieldEdge);
        const hi = Math.max(runStart, fieldEdge);
        drafts.push({
          id: `chip:${node.id}`, kind: field.kind, label,
          points: Object.freeze(points), chipIds: Object.freeze([node.id]),
          axis: "x", fixed: cy, at: (runStart + fieldEdge) / 2, min: lo + WIRE_CLEAR + half, max: hi - WIRE_CLEAR - half,
        });
      }
      continue;
    }
    /* approached from above or below: chips that share a column are one
       stack; the wire reaches the stack's nearest chip */
    const below = side === "below";
    const fromY = below ? O.y + O.height : O.y;
    const laneY = below ? fromY + LANE : fromY - LANE;
    const fieldEdge = below ? field.box.y : field.box.y + field.box.height;
    const stacks = new Map<number, ArrangedNode[]>();
    for (const node of chips) {
      const key = Math.round(node.position.x);
      stacks.set(key, [...(stacks.get(key) ?? []), node]);
    }
    for (const stack of stacks.values()) {
      const sorted = [...stack].sort((a, b) => below ? a.position.y - b.position.y : b.position.y - a.position.y);
      const first = sorted[0];
      const chip = boxOf(first);
      const cx = chip.x + chip.width / 2;
      const toY = below ? chip.y : chip.y + chip.height;
      const straight = Math.abs(cx - ocx) < 0.5;
      const points = straight
        ? [P(ocx, fromY), P(cx, toY)]
        : [P(ocx, fromY), P(ocx, laneY), P(cx, laneY), P(cx, toY)];
      const label = wording[first.id] ?? wording[field.kind] ?? "";
      const half = labelWidth(label) / 2;
      const others = fields.filter((f) => f.kind !== field.kind).map((f) => f.box);
      if (blocked(points, others)) {
        /* another field lies in the way (Focus: the second compact stack
           under the first) — the wire leaves the object's side, takes an
           outer lane down the clearer side and enters the chip from that
           side; the wording turns along the lane, clear of the object's
           and the chip's edges */
        const all = [O, field.box, ...others];
        const leftEdge = Math.min(...all.map((b) => b.x));
        const rightEdge = Math.max(...all.map((b) => b.x + b.width));
        const left = chip.x - leftEdge <= rightEdge - (chip.x + chip.width);
        const laneX = left ? leftEdge - LANE : rightEdge + LANE;
        const fromX = left ? O.x : O.x + O.width;
        const toX = left ? chip.x : chip.x + chip.width;
        const cy = chip.y + chip.height / 2;
        const objectEdge = below ? O.y + O.height : O.y;
        const lo = Math.min(objectEdge, cy);
        const hi = Math.max(objectEdge, cy);
        drafts.push({
          id: `stack:${first.id}`, kind: field.kind, label,
          points: Object.freeze([P(fromX, ocy), P(laneX, ocy), P(laneX, cy), P(toX, cy)]),
          chipIds: Object.freeze(sorted.map((c) => c.id)),
          axis: "y", fixed: laneX, at: (lo + hi) / 2, min: lo + WIRE_CLEAR + half, max: hi - WIRE_CLEAR - half,
          vertical: true,
        });
        continue;
      }
      if (straight) {
        /* the wording on the vertical run, between the object and the
           field's edge, clear of the field's word */
        const lo = Math.min(fromY, fieldEdge);
        const hi = Math.max(fromY, fieldEdge);
        drafts.push({
          id: `stack:${first.id}`, kind: field.kind, label,
          points: Object.freeze(points), chipIds: Object.freeze(sorted.map((c) => c.id)),
          axis: "y", fixed: cx, at: (fromY + fieldEdge) / 2, min: lo + WIRE_CLEAR + LABEL_H / 2, max: hi - 24 - LABEL_H / 2,
        });
      } else {
        const lo = Math.min(ocx, cx);
        const hi = Math.max(ocx, cx);
        drafts.push({
          id: `stack:${first.id}`, kind: field.kind, label,
          points: Object.freeze(points), chipIds: Object.freeze(sorted.map((c) => c.id)),
          axis: "x", fixed: laneY, at: (ocx + cx) / 2, min: lo + half, max: hi - half,
        });
      }
    }
  }
  return finish(drafts);
}
