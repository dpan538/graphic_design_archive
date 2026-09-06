/* 04 · Research status — the two smaller figures both trees draw: the year
   strip (one column a year, public over held, intensity on a square-root
   scale) and the wheel (places × decades, coloured by the decade's commonest
   object type). Computed once, on the server, from the frozen v49 per-record
   dataset; the desktop page and the phone read the same numbers. */
import { YEAR_TIERS } from "./content";
import { STATUS } from "./statusLayout";

const r1 = (n: number) => Math.round(n * 10) / 10;

/* ---- the year strip, 1800–2026: one column a year, split public / held,
   intensity = records on a square-root scale that saturates at STRIP_CAP.
   No peak: 1965's 850 is the most saturated column, not a spike. ---- */
export const STRIP_CAP = 260;
export const S_H = 100;
export const stripCols = YEAR_TIERS.map(([year, canonical, pub], i) => {
  const held = canonical - pub;
  const k = Math.min(1, Math.sqrt(canonical / STRIP_CAP));
  const share = canonical ? pub / canonical : 0;
  return { year, i, canonical, pub, held, k: r1(0.16 + 0.84 * k), hPub: r1(S_H * share), hHeld: r1(S_H * (1 - share)) };
});
export const decades = (() => {
  const out: { label: string; total: number; pub: number; i0: number; n: number }[] = [];
  for (const c of stripCols) {
    const d = Math.floor(c.year / 10) * 10;
    const cur = out[out.length - 1];
    if (cur && cur.label === `${d}s`) {
      cur.total += c.canonical;
      cur.pub += c.pub;
      cur.n += 1;
    } else out.push({ label: `${d}s`, total: c.canonical, pub: c.pub, i0: c.i, n: 1 });
  }
  return out;
})();
export const STRIP_YEARS = [1800, 1850, 1900, 1950, 2000, 2026];

/* ---- the wheel: places × decades, in the manner of a radial barcode.
   One spoke per place (the RADIAL_N largest), decades 1900s → 2020s from
   the hub outward (the century before is on the strip); a block wherever
   the place has records in that decade, coloured by the decade's commonest
   object type; runs of the same type merge into one longer block. ---- */
export const RADIAL_N = 60;
export const RADIAL_Y0 = 1900;
export const RADIAL_DECADES = 13;
export const RADIAL_TYPES = 7; // named types; the rest is "other"
export const TYPE_COLORS = ["#f5df2a", "#2b6cff", "#19c4b4", "#8fd83a", "#ff7a1f", "#ff3d2e", "#c02bd6"];
export const TYPE_OTHER = "#9a97a0";
const R_IN = 30;
const R_OUT = 146;
const R_STEP = (R_OUT - R_IN) / RADIAL_DECADES;
export const RADIAL = (() => {
  const cells = new Map<string, number[]>();
  for (const o of STATUS.objects) {
    const p = o[1];
    if (p >= RADIAL_N || o[0] < RADIAL_Y0) continue;
    const dec = Math.min(Math.floor((o[0] - RADIAL_Y0) / 10), RADIAL_DECADES - 1);
    const k = `${p}:${dec}`;
    let c = cells.get(k);
    if (!c) {
      c = new Array<number>(26).fill(0);
      cells.set(k, c);
    }
    c[o[6]] += 1;
  }
  const pitch = (Math.PI * 2) / RADIAL_N;
  const half = pitch * 0.36;
  const pt = (r: number, a: number) => `${r1(150 + r * Math.cos(a))},${r1(150 + r * Math.sin(a))}`;
  const blocks: { key: string; d: string; fill: string; dec: number }[] = [];
  for (let p = 0; p < RADIAL_N; p++) {
    const a0 = -Math.PI / 2 + p * pitch - half;
    const a1 = a0 + half * 2;
    let run: { t: number; d0: number; d1: number } | null = null;
    const flush = () => {
      if (!run) return;
      const r0 = R_IN + run.d0 * R_STEP + 0.6;
      const r1v = R_IN + (run.d1 + 1) * R_STEP - 0.6;
      blocks.push({
        key: `${p}-${run.d0}`,
        d: `M${pt(r0, a0)}A${r1(r0)},${r1(r0)} 0 0 1 ${pt(r0, a1)}L${pt(r1v, a1)}A${r1(r1v)},${r1(r1v)} 0 0 0 ${pt(r1v, a0)}Z`,
        fill: run.t < RADIAL_TYPES ? TYPE_COLORS[run.t] : TYPE_OTHER,
        dec: run.d0,
      });
      run = null;
    };
    for (let dec = 0; dec < RADIAL_DECADES; dec++) {
      const c = cells.get(`${p}:${dec}`);
      if (!c) {
        flush();
        continue;
      }
      let t = 0;
      for (let i = 1; i < 26; i++) if (c[i] > c[t]) t = i;
      const tt = t < RADIAL_TYPES ? t : RADIAL_TYPES;
      if (run && run.t === tt && run.d1 === dec - 1) run.d1 = dec;
      else {
        flush();
        run = { t: tt, d0: dec, d1: dec };
      }
    }
    flush();
  }
  const spokes = Array.from({ length: RADIAL_N }, (_, p) => {
    const a = -Math.PI / 2 + p * pitch;
    return { key: p, x1: r1(150 + (R_IN - 6) * Math.cos(a)), y1: r1(150 + (R_IN - 6) * Math.sin(a)), x2: r1(150 + (R_OUT + 3) * Math.cos(a)), y2: r1(150 + (R_OUT + 3) * Math.sin(a)) };
  });
  return { blocks, spokes, cells: cells.size };
})();
/* The top types' system names are long; the legend shows them short. */
export const SHORT_TYPES: Record<string, string> = {
  "Poster": "Poster",
  "Commons country category-tree open image record": "Category tree",
  "authority-weighted Commons open image record": "Authority",
  "open image record": "Open image",
  "region-balanced open image record": "Balanced",
  "controlled Commons open image record": "Controlled",
  "large region-balanced open image record": "Large balanced",
};
export const TYPE_LEGEND = STATUS.types.slice(0, RADIAL_TYPES).map((t, i) => ({ name: t.name, short: SHORT_TYPES[t.name] ?? t.name, color: TYPE_COLORS[i] }));
