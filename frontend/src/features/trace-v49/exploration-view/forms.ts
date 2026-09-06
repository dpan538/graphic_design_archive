/* The five export forms (§7i): the owner's reference stamps replicated in
   form — their proportions, paper, perforation, frame, image area and the
   placement, faces and weights of their small text — carrying the archive's
   identity in place of the issuer's: the MGDA block where the country was,
   the number of terms alone where the denomination was, the starting word
   where the subject was, TRACE where the postal mark was — and, as a
   research product, the LEDGER: the terms shown, the associations drawn,
   the category, the presentation, the release and the export id. No hash,
   no date. Each template is matched to one form (types.ts). The picture is
   laid out for the form's image area with the same template, variant and
   seed as the view. Every line of furniture is measured (estimateTextWidth)
   and wrapped to its column (flow), so no text crosses the picture, the
   frame or another line; the acceptance test proves it on every picture.
   The PNG is rasterised at EXPORT_SCALE × the form's size. */

import { EXPLORATION_FORM_NAMES, type ExplorationFormId, type Frame, type SceneText } from "./types.ts";

/* the PNG's pixel ratio over the form's coordinate size */
export const EXPORT_SCALE = 2;

export interface FormFurnitureInput {
  readonly seedLabel: string;
  readonly termCount: number;
  readonly associationCount: number;
  readonly categoryLabel: string;
  readonly exportId: string;
  /* the terms shown, in the tree's order; the associations drawn, as label pairs */
  readonly terms: readonly string[];
  readonly associations: readonly (readonly [string, string])[];
  readonly templateName: string;
  readonly variantName: string;
}

export interface StampForm {
  readonly id: ExplorationFormId;
  readonly name: string;
  readonly width: number;
  readonly height: number;
  readonly ground: string;
  readonly paper: string;
  readonly ink: string;
  /* the perforation along the paper's edge */
  readonly perforation: { readonly kind: "round" | "wave"; readonly radius: number; readonly pitch: number };
  /* the paper's rectangle in the sheet */
  readonly sheet: Frame;
  /* the printed frame line, when the form has one */
  readonly frame?: { readonly box: Frame; readonly stroke: number };
  /* the image area the picture is laid out in */
  readonly image: Frame;
  /* boxes drawn over the picture and the paper: the label box, the MGDA block */
  readonly boxes: readonly { readonly box: Frame; readonly stroke: number; readonly fill?: string }[];
  /* the form lets its furniture stand over the picture (the label box of the South African form) */
  readonly furnitureOverImage: boolean;
  readonly furniture: (input: FormFurnitureInput) => readonly SceneText[];
}

const INK = "#161514";
const PAPER = "#fbfaf5";
const RED = "#e4472c";

type Font = SceneText["font"];
type Weight = SceneText["weight"];
type Anchor = SceneText["anchor"];
type Role = SceneText["role"];
interface Extra { readonly anchor?: Anchor; readonly rotate?: number; readonly letterSpacing?: number }

/* the measure: a conservative estimate of a line's advance in the form's
   faces — capitals and digits wide, lower case narrower, mono fixed — so
   wrapping and the layout check err toward room, never toward overlap */
export function estimateTextWidth(text: string, size: number, font: Font, weight: Weight, letterSpacing = 0): number {
  let width = 0;
  for (const ch of text) {
    let factor: number;
    if (font === "mono") factor = 0.62;
    else if (/[A-Z0-9]/.test(ch)) factor = font === "serif" ? 0.74 : 0.7;
    else if (/[a-z]/.test(ch)) factor = font === "serif" ? 0.54 : 0.56;
    else if (ch === " ") factor = 0.3;
    else factor = 0.4;
    width += factor * size + letterSpacing;
  }
  return width * (weight === 700 ? 1.06 : 1);
}

/* a text's box in the sheet: ascent 0.76 em, descent 0.24 em; rotated lines turn the box */
export function textBox(item: SceneText): Frame {
  const width = estimateTextWidth(item.text, item.size, item.font, item.weight, item.letterSpacing ?? 0);
  const ascent = item.size * 0.76;
  const descent = item.size * 0.24;
  const start = item.anchor === "end" ? -width : item.anchor === "middle" ? -width / 2 : 0;
  if (item.rotate === -90) return { x: item.x - ascent, y: item.y + start - width + (item.anchor === "end" ? width : 0) - (item.anchor === "middle" ? 0 : 0), width: ascent + descent, height: width };
  if (item.rotate === 90) return { x: item.x - descent, y: item.y + (item.anchor === "end" ? -width : item.anchor === "middle" ? -width / 2 : 0), width: ascent + descent, height: width };
  return { x: item.x + start, y: item.y - ascent, width, height: ascent + descent };
}

function text(role: Role, value: string, x: number, y: number, size: number, font: Font, weight: Weight, colour: string, extra: Extra = {}): SceneText {
  return { role, text: value, x, y, size, anchor: extra.anchor ?? "start", weight, font, colour, ...(extra.rotate !== undefined ? { rotate: extra.rotate } : {}), ...(extra.letterSpacing !== undefined ? { letterSpacing: extra.letterSpacing } : {}) };
}

/* the flow: one ledger line wrapped at its separators into lines that fit
   maxWidth, each a SceneText; upright lines advance in y, lines rotated −90
   advance in x. Returns the texts and the next free baseline (y, or x). */
function flow(role: Role, value: string, x: number, y: number, size: number, font: Font, weight: Weight, colour: string, maxWidth: number, lineHeight: number, extra: Extra = {}): { readonly texts: SceneText[]; readonly next: number } {
  const spacing = extra.letterSpacing ?? 0;
  const fits = (line: string) => estimateTextWidth(line, size, font, weight, spacing) <= maxWidth;
  const tokens = value.split(role === "title" ? /( )/u : /( · | — )/u).filter((token) => token.length > 0);
  const lines: string[] = [];
  let current = "";
  for (const token of tokens) {
    const isSeparator = token === " · " || token === " — " || token === " ";
    const candidate = current + token;
    if (current === "" || fits(candidate.trimEnd())) { current = candidate; continue; }
    if (isSeparator) { current = candidate; continue; }
    lines.push(current.trimEnd());
    current = token;
  }
  if (current.trim()) lines.push(current.trimEnd());
  const rotated = extra.rotate === -90;
  const texts = lines.map((line, i) => text(role, line.replace(/^(· |— | )/u, ""), rotated ? x + i * lineHeight : x, rotated ? y : y + i * lineHeight, size, font, weight, colour, extra));
  return { texts, next: (rotated ? x : y) + lines.length * lineHeight };
}

/* the ledger's lines: the terms shown and the associations drawn */
function termsLine(input: FormFurnitureInput, upper: boolean): string {
  const list = input.terms.join(" · ");
  return `TERMS · ${upper ? list.toUpperCase() : list}`;
}
function associationsLine(input: FormFurnitureInput, upper: boolean): string {
  const list = input.associations.map(([a, b]) => `${a} — ${b}`).join(" · ");
  return `ASSOCIATIONS · ${upper ? list.toUpperCase() : list}`;
}
function presentationLine(input: FormFurnitureInput): string {
  return `${input.categoryLabel.toUpperCase()} · ${input.templateName.toUpperCase()} · ${input.variantName.toUpperCase()}`;
}

export const STAMP_FORMS: Readonly<Record<ExplorationFormId, StampForm>> = Object.freeze({
  /* France 1985 — Télévision: a landscape white stamp, a thin black frame
     inset, the picture in the frame's upper part, two serif lines below it,
     the denomination at the right, the postal word upright; the ledger in
     small capitals under the serif lines, wrapped short of the number; the
     MGDA block and the export line outside the frame */
  FRANCE: {
    id: "FRANCE",
    name: EXPLORATION_FORM_NAMES.FRANCE,
    width: 1400,
    height: 980,
    ground: "#c9c8c4",
    paper: PAPER,
    ink: INK,
    perforation: { kind: "round", radius: 12, pitch: 32 },
    sheet: { x: 50, y: 50, width: 1300, height: 880 },
    frame: { box: { x: 96, y: 96, width: 1208, height: 760 }, stroke: 3 },
    image: { x: 126, y: 126, width: 1148, height: 500 },
    boxes: [{ box: { x: 96, y: 874, width: 118, height: 30 }, stroke: 0, fill: INK }],
    furnitureOverImage: false,
    furniture: (input) => {
      const ledgerWidth = 930;
      const terms = flow("caption", termsLine(input, false), 140, 758, 15, "sans", 400, INK, ledgerWidth, 20, { letterSpacing: 1 });
      const associations = flow("caption", associationsLine(input, false), 140, terms.next, 15, "sans", 400, INK, ledgerWidth, 20, { letterSpacing: 1 });
      return [
        text("title", input.seedLabel.toUpperCase(), 140, 672, 50, "serif", 700, INK, { letterSpacing: 2 }),
        text("issuer", "MODERN GRAPHIC DESIGN ARCHIVE", 140, 720, 34, "serif", 700, INK, { letterSpacing: 1 }),
        ...terms.texts,
        ...associations.texts,
        text("denomination", String(input.termCount), 1160, 800, 96, "serif", 400, INK, { anchor: "end" }),
        text("denomination-word", "TRACE", 1262, 800, 30, "serif", 400, INK, { rotate: -90 }),
        text("issuer", "MGDA", 155, 896, 19, "sans", 700, PAPER, { anchor: "middle", letterSpacing: 1 }),
        text("meta", `TRACE EXPLORATION · v49 · ${presentationLine(input)} · ${input.exportId}`, 230, 896, 15, "sans", 400, INK, { letterSpacing: 1.2 }),
      ];
    },
  },
  /* South Africa R10 — a tall stamp with a wavy edge, the spots to the
     paper's edge, a label box over them: the code and the MGDA block in its
     top row, the number large, the starting word upright along its side,
     the ledger upright beside it in columns */
  SOUTH_AFRICA: {
    id: "SOUTH_AFRICA",
    name: EXPLORATION_FORM_NAMES.SOUTH_AFRICA,
    width: 900,
    height: 1800,
    ground: "#ffffff",
    paper: "#fbfaf6",
    ink: INK,
    perforation: { kind: "wave", radius: 16, pitch: 40 },
    sheet: { x: 60, y: 60, width: 780, height: 1680 },
    image: { x: 60, y: 60, width: 780, height: 1680 },
    boxes: [
      { box: { x: 110, y: 640, width: 300, height: 940 }, stroke: 3 },
      { box: { x: 316, y: 664, width: 76, height: 28 }, stroke: 0, fill: INK },
    ],
    furnitureOverImage: true,
    furniture: (input) => {
      /* the label box reads top-down: the code row, the number, the starting word, the ledger — every line upright */
      const column = 262;
      const title = flow("title", input.seedLabel, 128, 936, 40, "sans", 300, INK, column, 44);
      const terms = flow("caption", termsLine(input, false), 128, title.next + 26, 14, "sans", 400, INK, column, 20, { letterSpacing: 0.8 });
      const associations = flow("caption", associationsLine(input, false), 128, terms.next + 8, 14, "sans", 400, INK, column, 20, { letterSpacing: 0.8 });
      const meta = flow("meta", `${presentationLine(input)} · TRACE EXPLORATION · v49`, 128, associations.next + 8, 12, "sans", 400, INK, column, 18, { letterSpacing: 1 });
      return [
        text("meta", input.exportId.slice(-4).toUpperCase(), 128, 686, 22, "sans", 400, INK, { letterSpacing: 2 }),
        text("issuer", "MGDA", 354, 685, 18, "sans", 700, PAPER, { anchor: "middle", letterSpacing: 1 }),
        text("denomination", String(input.termCount), 128, 856, 130, "sans", 700, INK, { letterSpacing: -4 }),
        ...title.texts,
        ...terms.texts,
        ...associations.texts,
        ...meta.texts,
      ];
    },
  },
  /* Germany 1973 — the treaty stamp: landscape, the picture at the right
     at the paper's full height, blocks of small capitals at the left — the
     release, then the starting word with the terms and associations one per
     line — the number red as a corner mark on the head row of the text
     column (a hint, not a denomination), the issuer upright along the right
     edge, the MGDA block at the head; text and picture never share ground */
  GERMANY: {
    id: "GERMANY",
    name: EXPLORATION_FORM_NAMES.GERMANY,
    width: 1400,
    height: 900,
    ground: "#050506",
    paper: PAPER,
    ink: INK,
    perforation: { kind: "round", radius: 9, pitch: 22 },
    sheet: { x: 40, y: 40, width: 1320, height: 820 },
    image: { x: 540, y: 70, width: 740, height: 760 },
    boxes: [{ box: { x: 90, y: 96, width: 118, height: 40 }, stroke: 0, fill: INK }],
    furnitureOverImage: false,
    furniture: (input) => {
      const columnWidth = 420;
      const head = ["TRACE EXPLORATION", "A GOVERNED VIEW FROM", "VALIDATED ASSOCIATIONS", `${input.categoryLabel.toUpperCase()} · V49`];
      const lines: SceneText[] = [];
      let y = 372;
      lines.push(text("title", input.seedLabel.toUpperCase(), 90, y, 26, "sans", 400, INK, { letterSpacing: 1 }));
      y += 38;
      lines.push(text("meta", "TERMS", 90, y, 14, "sans", 700, INK, { letterSpacing: 3 }));
      y += 26;
      for (const term of input.terms) { const flowed = flow("caption", term.toUpperCase(), 90, y, 19, "sans", 400, INK, columnWidth, 25, { letterSpacing: 1 }); lines.push(...flowed.texts); y = flowed.next; }
      y += 12;
      lines.push(text("meta", "ASSOCIATIONS", 90, y, 14, "sans", 700, INK, { letterSpacing: 3 }));
      y += 26;
      for (const [a, b] of input.associations) { const flowed = flow("caption", `${a.toUpperCase()} — ${b.toUpperCase()}`, 90, y, 19, "sans", 400, INK, columnWidth, 25, { letterSpacing: 1 }); lines.push(...flowed.texts); y = flowed.next; }
      const meta = flow("meta", `${input.templateName.toUpperCase()} · ${input.variantName.toUpperCase()} · ${input.exportId}`, 90, 792, 13, "sans", 400, INK, columnWidth, 20, { letterSpacing: 1.4 });
      return [
        text("issuer", "MGDA", 149, 125, 26, "sans", 700, PAPER, { anchor: "middle", letterSpacing: 1 }),
        ...head.map((value, i) => text("meta", value, 90, 190 + i * 34, 26, "sans", 400, INK, { letterSpacing: 1 })),
        ...lines,
        ...meta.texts,
        text("denomination", String(input.termCount), 510, 138, 64, "sans", 700, RED, { anchor: "end", letterSpacing: -2 }),
        text("issuer", "MODERN GRAPHIC DESIGN ARCHIVE", 1336, 820, 30, "sans", 700, INK, { rotate: -90, letterSpacing: 1 }),
      ];
    },
  },
  /* Canada 1983 — the World Council stamp: cream paper, the picture on a
     panel at the right, the number and the issuer reading downward at the
     left, the ledger in brown lines across the foot */
  CANADA: {
    id: "CANADA",
    name: EXPLORATION_FORM_NAMES.CANADA,
    width: 1200,
    height: 1040,
    ground: "#f6f4ee",
    paper: "#f4f1e6",
    ink: "#8a8680",
    perforation: { kind: "round", radius: 11, pitch: 30 },
    sheet: { x: 50, y: 50, width: 1100, height: 940 },
    image: { x: 270, y: 70, width: 850, height: 780 },
    boxes: [],
    furnitureOverImage: false,
    furniture: (input) => {
      const brown = "#8b7e6a";
      const width = 850;
      const terms = flow("caption", termsLine(input, false), 270, 898, 15, "sans", 400, brown, width, 20);
      const associations = flow("caption", associationsLine(input, false), 270, terms.next, 15, "sans", 400, brown, width, 20);
      return [
        text("denomination", String(input.termCount), 130, 110, 72, "sans", 400, "#8a8680", { rotate: 90 }),
        text("issuer", "MGDA", 130, 230, 84, "sans", 300, "#8a8680", { rotate: 90, letterSpacing: 2 }),
        text("title", input.seedLabel, 270, 876, 24, "serif", 700, "#5c5246"),
        text("caption", "TRACE Exploration · Modern Graphic Design Archive · v49", 1120, 876, 15, "sans", 400, brown, { anchor: "end" }),
        ...terms.texts,
        ...associations.texts,
        text("meta", `${presentationLine(input)} · ${input.exportId}`, 270, 978, 12, "sans", 400, brown, { letterSpacing: 1 }),
      ];
    },
  },
  /* Sweden 2026 — the streaming stamp: portrait white, the picture full
     width above, a mono caption and the ledger in mono, the issuer large,
     the number alone at the right, the release line at the foot */
  SWEDEN: {
    id: "SWEDEN",
    name: EXPLORATION_FORM_NAMES.SWEDEN,
    width: 1100,
    height: 1450,
    ground: "#d86fa0",
    paper: "#fdfdfb",
    ink: INK,
    perforation: { kind: "round", radius: 10, pitch: 26 },
    sheet: { x: 50, y: 50, width: 1000, height: 1350 },
    image: { x: 90, y: 90, width: 920, height: 960 },
    boxes: [],
    furnitureOverImage: false,
    furniture: (input) => {
      const width = 900;
      const terms = flow("caption", termsLine(input, true), 100, 1134, 15, "mono", 400, INK, width, 22, { letterSpacing: 1 });
      const associations = flow("caption", associationsLine(input, true), 100, terms.next, 15, "mono", 400, INK, width, 22, { letterSpacing: 1 });
      const meta = flow("meta", `TRACE · EXPLORATION · V49 · ${presentationLine(input)} · ${input.exportId}`, 100, 1356, 13, "mono", 400, INK, width, 18, { letterSpacing: 1 });
      return [
        text("caption", input.seedLabel.toUpperCase(), 100, 1100, 26, "mono", 700, INK, { letterSpacing: 4 }),
        ...terms.texts,
        ...associations.texts,
        text("issuer", "MGDA", 100, 1300, 100, "mono", 700, INK, { letterSpacing: 4 }),
        text("denomination", String(input.termCount), 990, 1300, 100, "mono", 700, INK, { anchor: "end" }),
        ...meta.texts,
      ];
    },
  },
});
