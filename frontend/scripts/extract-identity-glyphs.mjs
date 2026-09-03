/* Extracts the glyph outlines the Identity sequence morphs and draws
   (HOMEPAGE_IDENTITY_SEQUENCE_v1.md §F4a, §F1): M · G · D · A in
   Baskervville 400, Instrument Sans 400 and 700 (variable), and LINE Seed
   JP 800; and the bridge sentence set in Instrument Sans 600, laid out with
   the face's own advances and kerning.

   Every outline is normalised to a 1000-unit em, y down, baseline at y=0,
   so paths from different faces can be morphed into one another. Writes
   src/data/identity-glyphs.json. (LINE Seed JP itself is served by the
   @fontsource imports in globals.css.)

   Run: node scripts/extract-identity-glyphs.mjs (from frontend/). */
import { createRequire } from "node:module";
const fontkit = createRequire(import.meta.url)("fontkit");
import { readFileSync, writeFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(process.cwd());
const nm = resolve(root, "node_modules");

function open(p) {
  return fontkit.create(readFileSync(p));
}
/* LINE Seed JP ships as numbered unicode-range subsets; find the one that
   has the Latin capitals. */
function lineSeedFile(weight) {
  const dir = resolve(nm, "@fontsource/line-seed-jp/files");
  for (const f of readdirSync(dir)) {
    if (!f.endsWith(`-${weight}-normal.woff2`)) continue;
    const font = open(resolve(dir, f));
    if (font.hasGlyphForCodePoint(0x4d) && font.hasGlyphForCodePoint(0x47)) return { file: resolve(dir, f), font };
  }
  throw new Error(`no LINE Seed JP ${weight} subset with Latin capitals`);
}

const bask = open(resolve(nm, "@fontsource/baskervville/files/baskervville-latin-400-normal.woff"));
const baskItalic = open(resolve(nm, "@fontsource/baskervville/files/baskervville-latin-400-italic.woff"));
/* Static weights: fontkit's variation instances are shallow objects without
   their own tables, so outlines are taken from the static files instead. */
const instr = (w) => open(resolve(nm, `@fontsource/instrument-sans/files/instrument-sans-latin-${w}-normal.woff2`));
const instr400 = instr(400);
const instr600 = instr(600);
const instr700 = instr(700);
const seed800 = lineSeedFile(800);
const seed700 = lineSeedFile(700);
const seed400 = lineSeedFile(400);

const r1 = (n) => Math.round(n * 10) / 10;

/* One glyph → normalised SVG path (1000 em, y down, baseline 0). Layout
   (cmap, advances, kerning) comes from the BASE font; a variation instance
   only supplies the outline for a glyph id — fontkit's instances do not
   carry a cmap processor of their own. */
function glyphPath(font, ch, base = font) {
  const run = base.layout(ch);
  const id = run.glyphs[0].id;
  const g = font.getGlyph(id);
  const k = 1000 / base.unitsPerEm;
  const cmds = g.path.commands;
  let d = "";
  let minX = Infinity;
  let maxX = -Infinity;
  for (const c of cmds) {
    const a = c.args.map((v, i) => r1(i % 2 === 0 ? v * k : -v * k));
    for (let i = 0; i < a.length; i += 2) {
      if (a[i] < minX) minX = a[i];
      if (a[i] > maxX) maxX = a[i];
    }
    switch (c.command) {
      case "moveTo": d += `M${a[0]},${a[1]}`; break;
      case "lineTo": d += `L${a[0]},${a[1]}`; break;
      case "quadraticCurveTo": d += `Q${a[0]},${a[1]} ${a[2]},${a[3]}`; break;
      case "bezierCurveTo": d += `C${a[0]},${a[1]} ${a[2]},${a[3]} ${a[4]},${a[5]}`; break;
      case "closePath": d += "Z"; break;
      default: break;
    }
  }
  return { d, advance: r1(g.advanceWidth * k), minX: r1(minX), maxX: r1(maxX) };
}

/* A whole line → per-glyph paths with x positions (advances + kerning). */
function linePaths(font, text, base = font) {
  const run = base.layout(text);
  const k = 1000 / base.unitsPerEm;
  const out = [];
  let x = 0;
  run.glyphs.forEach((g, i) => {
    const pos = run.positions[i];
    const ch = text[i] ?? "";
    const vg = font.getGlyph(g.id);
    if (vg.path.commands.length) {
      const { d } = glyphPath(font, ch, base);
      out.push({ ch, x: r1(x + pos.xOffset * k), d });
    }
    x += pos.xAdvance * k;
  });
  return { glyphs: out, width: r1(x) };
}

const LETTERS = ["M", "G", "D", "A"];
/* The wordmark's road: italic serif → roman serif → sans → bold sans →
   the site's face light → the site's face heavy. */
const faces = {
  serifItalic: { font: baskItalic, base: baskItalic, name: "Baskervville 400 italic" },
  serif: { font: bask, base: bask, name: "Baskervville 400" },
  sans: { font: instr400, base: instr400, name: "Instrument Sans 400" },
  sansBold: { font: instr700, base: instr700, name: "Instrument Sans 700" },
  seed400: { font: seed400.font, base: seed400.font, name: "LINE Seed JP 400" },
  seed700: { font: seed700.font, base: seed700.font, name: "LINE Seed JP 700" },
  seed: { font: seed800.font, base: seed800.font, name: "LINE Seed JP 800" },
};
const wordmark = {};
for (const [key, f] of Object.entries(faces)) {
  const glyphs = LETTERS.map((ch) => glyphPath(f.font, ch, f.base));
  /* lay the four out on their own advances, then centre the word on 0 */
  let x = 0;
  let inkL = Infinity;
  let inkR = -Infinity;
  const laid = glyphs.map((g) => {
    const at = x;
    x += g.advance;
    inkL = Math.min(inkL, at + g.minX);
    inkR = Math.max(inkR, at + g.maxX);
    return { d: g.d, x: r1(at), advance: g.advance };
  });
  /* ink bounds, so the wordmark is centred on what is printed, not on the
     advances — a side bearing's worth of drift otherwise */
  wordmark[key] = { name: f.name, width: r1(x), ink: [r1(inkL), r1(inkR)], capHeight: r1(f.base.capHeight * (1000 / f.base.unitsPerEm)), glyphs: laid };
}

const BRIDGE = "Where design history becomes traceable.";
const bridge = linePaths(instr600, BRIDGE);
const settled = linePaths(instr600, "A research archive for modern design.");

const out = { em: 1000, wordmark, bridge: { text: BRIDGE, face: "Instrument Sans 600", ...bridge }, settled: { text: "A research archive for modern design.", face: "Instrument Sans 600", ...settled } };
const dest = resolve(root, "src/data/identity-glyphs.json");
writeFileSync(dest, JSON.stringify(out));

console.log(
  JSON.stringify(
    {
      wrote: dest,
      bytes: readFileSync(dest).length,
      faces: Object.fromEntries(Object.entries(wordmark).map(([k, v]) => [k, { width: v.width, cap: v.capHeight, pathChars: v.glyphs.map((g) => g.d.length) }])),
      bridgeGlyphs: bridge.glyphs.length,
      variationApplied: wordmark.sans.glyphs[0].d !== wordmark.sansBold.glyphs[0].d,
      bridgeWidth: bridge.width,
    },
    null,
    1,
  ),
);
