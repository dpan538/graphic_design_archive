/* Context Canvas — the PNG export as an MGDA TICKET (§7g): a grey-white
   ticket, square-cut, laid on black; a hairline frame inset on either
   side of a perforated rule with round notches parting the long body
   (70 %) from the stub; the body on the canvas's own dot grid. The body is the
   CONTEXT MAP — the selected object's plate, a spine, one worded branch
   per dimension, the terms on the canvas as leaves in the dimension
   colours, the selected one coral; a dimension with nothing on the
   canvas is named and noted, and gets no branch. The stub carries the
   mark and wordmark under two decorative bars (the brand sheet's blue
   and lavender — decoration only), the record's title, year and
   attribution, source, the stable ID as the serial, the dimension key
   with counts, the interpretation boundary, the short release and the
   site. Membership, selection, wording and colours are preserved; the
   geometry is normalised, never the screen's; a tree taller than the
   body is scaled as one, never cut. No full hash, internal identifier,
   publication state or suggestion is printed; the binding is in <desc>.
*/

import type { ContextCanvasExportSnapshot } from "@/features/trace-v49/context/canvas/types";
import { type ContextKind, type LayoutPreset, kindWord } from "./content";
import { shortRelease, type ContextPresentation } from "./presentation";

export const CARD = Object.freeze({ width: 1800, height: 1200 });
export const TICKET = Object.freeze({ x: 60, y: 120, width: 1680, height: 960, notch: 24, inset: 14 });
export const STUB_SPLIT = Object.freeze(TICKET.x + Math.round(TICKET.width * 0.7));
/* the ticket lies on black; the ticket itself is the page's grey-white;
   the brand sheet's blue and lavender are decorative bars only; the
   dimension accents, the object's light blue and the selection coral are
   the canvas's own */
export const CARD_COLOURS = Object.freeze({
  field: "#0a0a0b",
  paper: "#f2f0eb",
  ink: "#0a0a0b",
  label: "#5f5e5a",
  rule: "#c4c3be",
  object: "#a9c2e4",
  highlight: "#dd745f",
  blue: "#537cde",
  lavender: "#a785fe",
  medium: "#53b3c6",
  theme: "#3fa684",
  movement_context: "#d49454",
});
const SANS = "'Instrument Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif";
const SERIF = "Baskervville, Georgia, 'Times New Roman', serif";
const UUID_PATTERN = /\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b/gi;

export interface CardTerm {
  readonly entityId: string;
  readonly label: string;
  readonly kind: ContextKind;
  readonly wording: string;
  readonly selected: boolean;
}

export interface CardInput {
  readonly presentation: ContextPresentation;
  readonly terms: readonly CardTerm[];
  readonly layout: Readonly<{ preset: LayoutPreset; focusKind: ContextKind }>;
  readonly identity: Readonly<{
    releaseId: string;
    manifestSha256: string;
    projectionId: string;
    projectionSha256: string;
  }>;
  readonly kicker: string;
  readonly canvasName: string;
  readonly record: string;
  readonly wordmark: readonly [string, string];
  readonly site: string;
  readonly notRecorded: string;
}

const safe = (value: string) => value.replace(UUID_PATTERN, "public-reference-withheld");
const esc = (value: string) => safe(value)
  .replace(/&/g, "&amp;")
  .replace(/</g, "&lt;")
  .replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;");
const short = (sha: string) => (sha.length > 8 ? sha.slice(0, 8) : sha);
const n = (value: number) => Number(value.toFixed(2));

/* wrap by words to a character budget; the last line takes an ellipsis
   when the budget of lines is spent — the full text is in the <title> */
function wrap(text: string, perLine: number, maxLines: number): readonly string[] {
  const words = safe(text).trim().split(/\s+/);
  const lines: string[] = [];
  let line = "";
  for (const word of words) {
    const next = line ? `${line} ${word}` : word;
    if (next.length <= perLine || !line) {
      line = next;
    } else {
      lines.push(line);
      line = word;
    }
    if (lines.length === maxLines) break;
  }
  if (lines.length < maxLines && line) lines.push(line);
  if (lines.length === maxLines && words.join(" ").length > lines.join(" ").length) {
    const last = lines[maxLines - 1];
    lines[maxLines - 1] = `${last.slice(0, Math.max(0, perLine - 1)).trimEnd()}…`;
  }
  return lines;
}

type TextOptions = Readonly<{
  weight?: number;
  anchor?: "start" | "middle" | "end";
  tracking?: number;
  upper?: boolean;
  title?: string;
  family?: string;
  italic?: boolean;
  rotate?: number;
}>;

/* a stable ID has no spaces: it breaks after a hyphen, never mid-token */
function splitId(id: string, perLine: number): readonly string[] {
  const out: string[] = [];
  let line = "";
  for (const token of id.split(/(?<=-)/)) {
    if (line && (line + token).length > perLine) {
      out.push(line);
      line = token;
    } else {
      line += token;
    }
  }
  if (line) out.push(line);
  return out.length > 2 ? [out[0], `${out.slice(1).join("").slice(0, perLine - 1)}…`] : out;
}

function text(x: number, y: number, value: string, size: number, colour: string, options: TextOptions = {}): string {
  const content = options.upper ? value.toUpperCase() : value;
  const transform = options.rotate ? ` transform="rotate(${options.rotate} ${n(x)} ${n(y)})"` : "";
  return `<text x="${n(x)}" y="${n(y)}" font-family="${options.family ?? SANS}" font-size="${size}" font-weight="${options.weight ?? 400}"${options.italic ? ' font-style="italic"' : ""} fill="${colour}"${options.anchor ? ` text-anchor="${options.anchor}"` : ""}${options.tracking ? ` letter-spacing="${options.tracking}"` : ""}${transform}>${options.title ? `<title>${esc(options.title)}</title>` : ""}${esc(content)}</text>`;
}

function lines(x: number, y: number, values: readonly string[], size: number, leading: number, colour: string, options: TextOptions = {}): string {
  return values.map((value, i) => text(x, y + i * leading, value, size, colour, { ...options, title: i === 0 ? options.title : undefined })).join("");
}

/* the wording on a branch: the line broken, the word on the sheet */
function wordedRun(x1: number, x2: number, y: number, label: string, colour: string, size = 17): string {
  const w = label.length * size * 0.56 + 20;
  const cx = (x1 + x2) / 2;
  return [
    `<line x1="${n(x1)}" y1="${n(y)}" x2="${n(x2)}" y2="${n(y)}" stroke="${CARD_COLOURS.ink}" stroke-opacity="0.5" stroke-width="1"/>`,
    `<rect x="${n(cx - w / 2)}" y="${n(y - size * 0.8)}" width="${n(w)}" height="${n(size * 1.6)}" fill="${CARD_COLOURS.paper}"/>`,
    text(cx, y + size * 0.36, label, size, colour, { anchor: "middle" }),
  ].join("");
}

export function prepareContextCardSvg(input: CardInput): ContextCanvasExportSnapshot {
  const { presentation, terms, identity } = input;
  const C = CARD_COLOURS;
  const colourOf = (kind: ContextKind) => C[kind];

  /* ---- the body: the context map, a tree ---- */
  const bodyX = TICKET.x + 40;
  const bodyY = TICKET.y + 40;
  const bodyW = STUB_SPLIT - TICKET.x - 80;
  const bodyH = TICKET.height - 80;
  const OBJECT_W = 340;
  const idLines = splitId(presentation.object.stableId, 34);
  const OBJECT_H = 158 + idLines.length * 18;
  const RUN = 160;
  const DIM_W = 150;
  const TIE = 30;
  const LEAF_W = 380;
  const LEAF_H = 72;
  const LEAF_GAP = 16;
  const GROUP_GAP = 40;
  const spineX = bodyX + OBJECT_W + 36;
  const dimX = spineX + RUN;
  const leafX = dimX + DIM_W + TIE;

  /* the groups' heights: one leaf row each, at least one line for "Not recorded" */
  const groups = presentation.dimensions.map((dimension) => {
    const shown = terms.filter((t) => t.kind === dimension.kind);
    const rows = Math.max(1, shown.length);
    return { dimension, shown, height: rows * LEAF_H + (rows - 1) * LEAF_GAP };
  });
  const treeH = groups.reduce((sum, g) => sum + g.height, 0) + GROUP_GAP * (groups.length - 1);
  /* a tree taller than the body (only a synthetic fixture: the real
     workload is five nodes at most) is scaled down as one, never cut */
  const avail = bodyH - 70;
  const fit = Math.min(1, Math.floor((avail / Math.max(treeH, OBJECT_H)) * 100) / 100);
  const treeTop = bodyY + 70 + Math.max(0, (avail - treeH * fit) / 2);
  const objectY = treeTop + treeH / 2 - OBJECT_H / 2;
  const objectCy = objectY + OBJECT_H / 2;

  const tree: string[] = [];
  let y = treeTop;
  const dimCentres: number[] = [];
  for (const group of groups) {
    const { dimension, shown, height } = group;
    const cy = y + height / 2;
    dimCentres.push(cy);
    const colour = colourOf(dimension.kind);
    const recorded = dimension.items.length > 0;
    const onCanvas = shown.length > 0;
    /* the dimension node: bar + word */
    tree.push(`<rect x="${n(dimX - 10)}" y="${n(cy - 16)}" width="${n(DIM_W + 8)}" height="32" fill="${C.paper}"/>`);
    tree.push(`<rect x="${n(dimX)}" y="${n(cy - 3)}" width="18" height="6" fill="${recorded ? colour : C.rule}"/>`);
    tree.push(text(dimX + 28, cy + 6, kindWord(dimension.kind), 18, recorded ? C.ink : C.label, { weight: 700, tracking: 2, upper: true }));
    if (!onCanvas) {
      /* no branch: nothing on the canvas — "Not recorded", or set aside */
      const note = recorded ? `${dimension.items.length} set aside` : input.notRecorded;
      tree.push(`<rect x="${n(leafX - 8)}" y="${n(cy - 16)}" width="${n(note.length * 10 + 16)}" height="32" fill="${C.paper}"/>`);
      tree.push(text(leafX, cy + 6, note, 18, C.label, { italic: true }));
    } else {
      /* the branch from the spine, worded */
      tree.push(wordedRun(spineX, dimX - 14, cy, shown[0].wording, C.label));
      /* the leaves: one plate per term, a short tie from the dimension */
      const leafSpine = leafX - TIE / 2;
      if (shown.length > 1) {
        tree.push(`<line x1="${n(leafSpine)}" y1="${n(y + LEAF_H / 2)}" x2="${n(leafSpine)}" y2="${n(y + height - LEAF_H / 2)}" stroke="${C.ink}" stroke-opacity="0.5" stroke-width="1"/>`);
        tree.push(`<line x1="${n(dimX + DIM_W)}" y1="${n(cy)}" x2="${n(leafSpine)}" y2="${n(cy)}" stroke="${C.ink}" stroke-opacity="0.5" stroke-width="1"/>`);
      } else {
        tree.push(`<line x1="${n(dimX + DIM_W)}" y1="${n(cy)}" x2="${n(leafX)}" y2="${n(cy)}" stroke="${C.ink}" stroke-opacity="0.5" stroke-width="1"/>`);
      }
      shown.forEach((term, i) => {
        const ly = y + i * (LEAF_H + LEAF_GAP);
        const lcy = ly + LEAF_H / 2;
        if (shown.length > 1) {
          tree.push(`<line x1="${n(leafSpine)}" y1="${n(lcy)}" x2="${n(leafX)}" y2="${n(lcy)}" stroke="${C.ink}" stroke-opacity="0.5" stroke-width="1"/>`);
        }
        const fill = term.selected ? C.highlight : C.paper;
        tree.push(`<g><title>${esc(term.label)}</title>`);
        tree.push(`<rect x="${n(leafX)}" y="${n(ly)}" width="${LEAF_W}" height="${LEAF_H}" fill="${fill}" stroke="${term.selected ? C.highlight : C.ink}" stroke-opacity="${term.selected ? 1 : 0.55}" stroke-width="1"/>`);
        tree.push(`<rect x="${n(leafX)}" y="${n(ly)}" width="6" height="${LEAF_H}" fill="${colour}"/>`);
        tree.push(lines(leafX + 22, ly + 31, wrap(term.label, 30, 2), 20, 24, C.ink, { weight: 600 }));
        tree.push("</g>");
      });
    }
    y += height + GROUP_GAP;
  }
  /* the spine and the object's stem */
  const branched = groups.map((g, i) => ({ g, cy: dimCentres[i] })).filter(({ g }) => g.shown.length > 0);
  if (branched.length > 0) {
    const top = Math.min(objectCy, ...branched.map((b) => b.cy));
    const bottom = Math.max(objectCy, ...branched.map((b) => b.cy));
    tree.push(`<line x1="${n(spineX)}" y1="${n(top)}" x2="${n(spineX)}" y2="${n(bottom)}" stroke="${C.ink}" stroke-opacity="0.5" stroke-width="1"/>`);
    tree.push(`<line x1="${n(bodyX + OBJECT_W)}" y1="${n(objectCy)}" x2="${n(spineX)}" y2="${n(objectCy)}" stroke="${C.ink}" stroke-opacity="0.5" stroke-width="1"/>`);
  }
  const object = [
    `<g><title>${esc(presentation.object.title)}</title>`,
    `<rect x="${n(bodyX)}" y="${n(objectY)}" width="${OBJECT_W}" height="${OBJECT_H}" fill="${C.object}"/>`,
    text(bodyX + 18, objectY + 30, "Selected object", 14, C.ink, { weight: 600, tracking: 2, upper: true }),
    lines(bodyX + 18, objectY + 64, wrap(presentation.object.title, 22, 2), 26, 32, C.ink, { weight: 700 }),
    lines(bodyX + 18, objectY + 130, idLines, 15, 18, C.ink),
    text(bodyX + 18, objectY + 130 + idLines.length * 18 + 4, [presentation.object.dateDisplay, presentation.object.objectType].filter(Boolean).join(" · ").slice(0, 36), 15, C.ink),
    "</g>",
  ].join("");
  const map = `<g transform="translate(${n(bodyX)} ${n(treeTop)}) scale(${fit}) translate(${n(-bodyX)} ${n(-treeTop)})">${tree.join("")}${object}</g>`;
  const head = [
    `<rect x="${n(bodyX - 8)}" y="${n(bodyY - 4)}" width="${n(input.kicker.length * 13 + 28 + 300)}" height="30" fill="${C.paper}"/>`,
    text(bodyX, bodyY + 16, input.kicker, 16, C.ink, { weight: 700, tracking: 3, upper: true }),
    text(bodyX + input.kicker.length * 13 + 28, bodyY + 16, `${presentation.dimensions.length} dimensions · ${terms.length} on the canvas`, 16, C.label),
    `<line x1="${n(bodyX)}" y1="${n(bodyY + 36)}" x2="${n(bodyX + bodyW)}" y2="${n(bodyY + 36)}" stroke="${C.rule}" stroke-width="1"/>`,
  ].join("");

  /* ---- the stub ---- */
  const sx = STUB_SPLIT + 40;
  const stripW = TICKET.x + TICKET.width - sx - 40;
  const titlePer = Math.floor(stripW / 17);
  const bodyPer = Math.floor(stripW / 10);
  const claimPer = Math.floor(stripW / 11);
  const strip: string[] = [];
  /* the head: two decorative bars, the mark on an ink tile, the wordmark */
  const headY = TICKET.y + 40;
  strip.push(`<rect x="${n(sx)}" y="${n(headY)}" width="${n(stripW)}" height="6" fill="${C.lavender}"/>`);
  strip.push(`<rect x="${n(sx)}" y="${n(headY + 6)}" width="${n(stripW)}" height="6" fill="${C.blue}"/>`);
  strip.push(`<rect x="${n(sx)}" y="${n(headY + 30)}" width="104" height="46" fill="${C.ink}"/>`);
  strip.push(text(sx + 52, headY + 62, "MGDA", 24, C.paper, { weight: 800, anchor: "middle", tracking: 1.5 }));
  strip.push(text(sx + 122, headY + 48, input.wordmark[0], 20, C.ink, { family: SERIF }));
  strip.push(text(sx + 122, headY + 75, input.wordmark[1], 20, C.ink, { family: SERIF, italic: true }));
  strip.push(text(sx, headY + 112, input.canvasName, 14, C.ink, { weight: 700, tracking: 3, upper: true }));
  let sy = headY + 112 + 52;
  strip.push(text(sx, sy, input.record, 14, C.label, { weight: 600, tracking: 3, upper: true }));
  sy += 38;
  const titleLines = wrap(presentation.object.title, titlePer, 3);
  strip.push(lines(sx, sy, titleLines, 30, 38, C.ink, { weight: 700, title: presentation.object.title }));
  sy += titleLines.length * 38 + 4;
  const meta = [presentation.object.dateDisplay, presentation.object.creatorAttribution].filter((v) => v && v.trim()).join(" · ");
  if (meta) {
    const metaLines = wrap(meta, bodyPer, 3);
    strip.push(lines(sx, sy, metaLines, 18, 26, C.ink));
    sy += metaLines.length * 26 + 2;
  }
  if (presentation.object.sourceName?.trim()) {
    const sourceLines = wrap(presentation.object.sourceName, bodyPer + 2, 2);
    strip.push(lines(sx, sy, sourceLines, 17, 24, C.label));
    sy += sourceLines.length * 24 + 2;
  }
  sy += 14;
  strip.push(`<line x1="${n(sx)}" y1="${n(sy)}" x2="${n(sx + stripW)}" y2="${n(sy)}" stroke="${C.rule}" stroke-width="1"/>`);
  sy += 36;
  strip.push(text(sx, sy, "Serial", 14, C.label, { weight: 600, tracking: 3, upper: true }));
  const serialLines = splitId(presentation.object.stableId, 32);
  strip.push(lines(sx, sy + 28, serialLines, 18, 24, C.ink, { tracking: 1 }));
  sy += 40 + serialLines.length * 24;
  strip.push(`<line x1="${n(sx)}" y1="${n(sy)}" x2="${n(sx + stripW)}" y2="${n(sy)}" stroke="${C.rule}" stroke-width="1"/>`);
  sy += 36;
  for (const dimension of presentation.dimensions) {
    const shown = dimension.items.filter((item) => item.visible);
    strip.push(`<rect x="${n(sx)}" y="${n(sy - 12)}" width="14" height="14" fill="${colourOf(dimension.kind)}"/>`);
    strip.push(text(sx + 26, sy, kindWord(dimension.kind), 15, C.ink, { weight: 700, tracking: 2, upper: true }));
    const count = shown.length === 0
      ? (dimension.items.length > 0 ? `${dimension.items.length} set aside` : input.notRecorded)
      : `${shown.length}/${dimension.items.length} on the canvas`;
    strip.push(text(sx + stripW, sy, count, 16, C.label, { anchor: "end" }));
    sy += 32;
  }
  /* the boundary and the release, from the stub's foot up */
  const footY = TICKET.y + TICKET.height - 44;
  strip.push(text(sx, footY, input.site, 14, C.label));
  strip.push(text(sx + stripW, footY, `${shortRelease(identity.releaseId)} · ${identity.projectionId} · ${short(identity.projectionSha256)}`, 14, C.label, { anchor: "end" }));
  const claimLines = wrap(presentation.boundary, claimPer, 3);
  const claimY = footY - 40 - (claimLines.length - 1) * 27;
  strip.push(`<line x1="${n(sx)}" y1="${n(claimY - 36)}" x2="${n(sx + stripW)}" y2="${n(claimY - 36)}" stroke="${C.rule}" stroke-width="1"/>`);
  strip.push(lines(sx, claimY, claimLines, 19, 27, C.ink, { weight: 700 }));
  /* the microtext along the ticket's edge */
  strip.push(text(TICKET.x + TICKET.width - 18, TICKET.y + TICKET.height - 44, `${input.canvasName} · ${shortRelease(identity.releaseId)} · ${presentation.object.stableId}`, 12, C.label, { rotate: -90, tracking: 2, upper: true }));

  /* ---- the ticket: square-cut, a hairline frame inset on either side
     of the perforation, the body on the canvas's own dot grid ---- */
  const inset = TICKET.inset;
  const frames = [
    `<defs><pattern id="ground" width="28" height="28" patternUnits="userSpaceOnUse"><circle cx="14" cy="14" r="1.1" fill="${C.ink}" fill-opacity="0.16"/></pattern></defs>`,
    `<rect x="${n(TICKET.x + inset)}" y="${n(TICKET.y + inset)}" width="${n(STUB_SPLIT - inset - TICKET.x - inset)}" height="${n(TICKET.height - inset * 2)}" fill="url(#ground)" stroke="${C.ink}" stroke-opacity="0.35" stroke-width="1"/>`,
    `<rect x="${n(STUB_SPLIT + inset)}" y="${n(TICKET.y + inset)}" width="${n(TICKET.x + TICKET.width - inset - STUB_SPLIT - inset)}" height="${n(TICKET.height - inset * 2)}" fill="none" stroke="${C.ink}" stroke-opacity="0.35" stroke-width="1"/>`,
  ].join("");
  const perforation = [
    `<line x1="${STUB_SPLIT}" y1="${TICKET.y + 30}" x2="${STUB_SPLIT}" y2="${TICKET.y + TICKET.height - 30}" stroke="${C.ink}" stroke-opacity="0.55" stroke-width="1.5" stroke-dasharray="7 9" stroke-linecap="round"/>`,
    `<circle cx="${STUB_SPLIT}" cy="${TICKET.y}" r="${TICKET.notch}" fill="${C.field}"/>`,
    `<circle cx="${STUB_SPLIT}" cy="${TICKET.y + TICKET.height}" r="${TICKET.notch}" fill="${C.field}"/>`,
  ].join("");

  const desc = esc([
    `Context Canvas · ${presentation.object.stableId}`,
    `research release ${identity.releaseId}`,
    `research manifest ${identity.manifestSha256}`,
    `Context projection ${identity.projectionId} · ${identity.projectionSha256}`,
    `layout ${input.layout.preset}`,
  ].join(" · "));

  const svg = [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${CARD.width}" height="${CARD.height}" viewBox="0 0 ${CARD.width} ${CARD.height}">`,
    `<title>${esc(`Context Canvas for ${presentation.object.stableId}`)}</title>`,
    `<desc>${desc}</desc>`,
    `<rect width="${CARD.width}" height="${CARD.height}" fill="${C.field}"/>`,
    `<rect x="${TICKET.x}" y="${TICKET.y}" width="${TICKET.width}" height="${TICKET.height}" fill="${C.paper}"/>`,
    frames,
    head,
    map,
    perforation,
    strip.join(""),
    "</svg>",
  ].join("");

  return Object.freeze({
    svg,
    width: CARD.width,
    height: CARD.height,
    contentBounds: Object.freeze({ x: 0, y: 0, width: CARD.width, height: CARD.height, empty: false }),
  });
}
