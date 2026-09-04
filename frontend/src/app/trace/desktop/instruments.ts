/* The TRACE landing's scene — a FLOW of five screens on one signal bus
   (design record: docs/frontend/FRONTEND_DESIGN_DECISION.md §7f).

   One clock (t, seconds since mount), one scroll state (s, 0..4: the
   screen index, fractional between screens; SCROLL, the scene's 0..1
   progress). Every screen is a Frame built on the same fixed budgets —
   N = 1400 particles, M = 96 polylines of V = 48 vertices — so the set
   can TRANSFORM index by index into the next screen (blend()). Nothing
   is piled up: each screen shows only its own set.

     0 TRACE            SPHERE · FUNNEL · STRIP · LATTICE (with the small time axis)
     1 Context Canvas   CHAIN · NETWORK · HALFTONE            + reactive PRISM
     2 Spacetime        WORLD MAP · GEOGRAPHY TAPE · TIME TAPE + reactive LEDGER
     3 Between records  seven nested Lissajous rings on the scope's scales
                        (straight ↔ smooth by the scroll; no brackets)
     4 Exploration      DIAL · WAVE · inquiry LOOP            + reactive OSCILLON, PULSES

   Each screen has its own layout (boxesFor) so the composition moves,
   not only the figures. Drawn flat, depth implied by dot size, ring
   foreshortening and particle density — NO perspective camera (the
   owner rejected it). Each component appears exactly once across the
   flow; no human figures, no moiré, no scan, no corner registration
   marks. One design language — paper lines with a cheap bloom, points
   sized by role; coral, mint and sky only for what carries a signal.
   The HUD — the readout tiles top right, the tracking brackets on the
   main form (not on screen 3), the wires (each screen's own,
   cross-faded) — frames the set. The wires are the bus couplings
   drawn, and run only between FIXED anchors (frame edges, tape ends,
   readouts), never after a moving mark, so nothing flickers.

   Program signature: (ctx, w, h, t seconds, s state 0..4, a draw-in
   0..1). Governed matter on the sheet: the year range (setAxisYears),
   the 23 periods, and the coastlines and mapped geographies of
   world-outline.ts. The tiles, the halftone and the ledger's cells are
   hash-seeded texture, not data. */

import { MARKS, WORLD } from "./world-outline";

export type Program = (ctx: CanvasRenderingContext2D, w: number, h: number, t: number, p: number, a: number) => void;

const TAU = Math.PI * 2;
const GOLDEN = Math.PI * (3 - Math.sqrt(5));
const PAPER = "239,233,221";
const SAND = "201,163,123";
const SKY = "79,168,222";
const CORAL = "240,135,106";
const MINT = "95,191,179";
type RGB = [number, number, number];
type XY = [number, number];
const C_PAPER: RGB = [239, 233, 221];
const C_CORAL: RGB = [240, 135, 106];
const C_MINT: RGB = [95, 191, 179];
const C_SKY: RGB = [79, 168, 222];
const C_SAND: RGB = [201, 163, 123];
const rgb = (c: RGB) => `${c[0] | 0},${c[1] | 0},${c[2] | 0}`;
const mix = (a: RGB, b: RGB, f: number): RGB => [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f];

const lerp = (a: number, b: number, f: number) => a + (b - a) * f;
const clamp01 = (x: number) => Math.min(1, Math.max(0, x));
const smooth = (x: number) => {
  const c = clamp01(x);
  return c * c * (3 - 2 * c);
};
const ease = (x: number) => 1 - Math.pow(1 - clamp01(x), 3);
const hash = (n: number) => ((((n | 0) * 2654435761) ^ ((n | 0) >>> 7)) >>> 0) % 1000 / 1000;

/* ================= the BUS =================
   The system's signals. Every component reads from here and some write
   here, so what one does is what another shows.
   · PERIOD — one of the 23 governed decade buckets, scanned by the clock
     (about 83 s per cycle) and pushed on by the scroll. periodF is the
     continuous value everything that MOVES must follow (the lattice's
     mass, the strip's window, the time tape's cursor) so the scroll
     never steps; the integer period lights the sphere's column, the
     funnel's ring, the map's held mark (region = period % 6, also the
     geography tape's bar and the ledger's row) and the ledger's column,
     and stamps periodChangedAt for the pulses.
   · WALK — the network's path, one step every 4.2 s; a completed walk
     chooses the chain's context ring, fires the prism and centres the
     halftone's gradient.
   · SWEEP — the dial's head (0.22 rad/s); its pass over the satellite
     emits the PULSE the wave's packet, the inquiry loop and the pulses
     answer; the sweep shears the oscillon.
   · FLOW — the funnel's delivery every 5 s; deepens the lattice's well.
   Every decay is 2–3 s: exchanges are slow by the owner's rule (no
   high-frequency flicker). */
export type Bus = {
  t: number;
  s: number;
  scroll: number;
  period: number;
  periodF: number;
  periodChangedAt: number;
  walkStep: number;
  walkNode: number[];
  walkDoneAt: number;
  walkCount: number;
  sweep: number;
  pulseAt: number;
  pulseCount: number;
  flowAt: number;
  region: number;
};
export const bus: Bus = { t: 0, s: 0, scroll: 0, period: 0, periodF: 0, periodChangedAt: -10, walkStep: 0, walkNode: [0, 0, 0, 0, 0], walkDoneAt: -10, walkCount: 0, sweep: 0, pulseAt: -10, pulseCount: 0, flowAt: -10, region: 0 };
let SCROLL = 0;
export function setScroll(sp: number) {
  SCROLL = sp;
}
const decay = (at: number, t: number, len: number) => Math.max(0, 1 - (t - at) / len);
function computeBus(t: number, s: number) {
  bus.t = t;
  bus.s = s;
  bus.scroll = SCROLL;
  /* the period: scanned by the clock, and pushed on by the scroll */
  const periodF = (((t * 0.012 + SCROLL * 2) % 1) + 1) % 1 * 23;
  bus.periodF = periodF;
  const period = Math.floor(periodF);
  if (period !== bus.period) {
    bus.period = period;
    bus.periodChangedAt = t;
    bus.region = period % 6;
  }
  /* the walk: a path through the network, one step a beat */
  const beat = Math.floor(t / 4.2);
  const walkNode = [4, 6, 6, 6, 4].map((n, c) => Math.floor(hash(beat * 31 + c * 7) * n));
  bus.walkStep = (t / 4.2) % 1;
  if (walkNode[0] !== bus.walkNode[0] || walkNode[4] !== bus.walkNode[4]) {
    bus.walkNode = walkNode;
    bus.walkDoneAt = t;
    bus.walkCount += 1;
  }
  /* the sweep, and its pass over the satellite */
  const sweep = t * 0.22;
  const satA = Math.atan2(0.62, 0.95);
  const before = ((bus.sweep - satA) % TAU + TAU) % TAU;
  const after = ((sweep - satA) % TAU + TAU) % TAU;
  if (after < before) {
    bus.pulseAt = t;
    bus.pulseCount += 1;
  }
  bus.sweep = sweep;
}

/* ---- the matter and the lines: fixed budgets so every screen can
   become the next ---- */
const N = 1400;
const M = 96;
const V = 48;
type Pt = { x: number; y: number; r: number; bright: number; c: RGB; kind: number; ang: number };
type Poly = { v: XY[]; bright: number; width: number; c: RGB; dashed: number };
type Frame = { pts: Pt[]; polys: Poly[]; cursor: XY; main: { x0: number; y0: number; x1: number; y1: number }; anchors: Record<string, XY>; frame?: number };
const pt = (x: number, y: number, r: number, bright: number, c: RGB = C_PAPER, kind = 0, ang = 0): Pt => ({ x, y, r, bright, c, kind, ang });

function ringPoly(cx: number, cy: number, rx: number, ry: number, rot: number, bright: number, width = 0.9, c: RGB = C_PAPER, dashed = 0, a0 = 0, span = 1): Poly {
  const v: XY[] = [];
  for (let i = 0; i < V; i++) {
    const a = a0 + (i / (V - 1)) * TAU * span;
    const x = Math.cos(a) * rx;
    const y = Math.sin(a) * ry;
    v.push([cx + x * Math.cos(rot) - y * Math.sin(rot), cy + x * Math.sin(rot) + y * Math.cos(rot)]);
  }
  return { v, bright, width, c, dashed };
}
function linePoly(x0: number, y0: number, x1: number, y1: number, bright: number, width = 0.9, c: RGB = C_PAPER, dashed = 0): Poly {
  const v: XY[] = [];
  for (let i = 0; i < V; i++) v.push([lerp(x0, x1, i / (V - 1)), lerp(y0, y1, i / (V - 1))]);
  return { v, bright, width, c, dashed };
}
function curvePoly(fn: (u: number) => XY, bright: number, width = 0.9, c: RGB = C_PAPER, dashed = 0): Poly {
  const v: XY[] = [];
  for (let i = 0; i < V; i++) v.push(fn(i / (V - 1)));
  return { v, bright, width, c, dashed };
}
const parkedPoly = (x: number, y: number): Poly => ({ v: Array.from({ length: V }, () => [x, y] as XY), bright: 0, width: 0.8, c: C_PAPER, dashed: 0 });
function pad<T>(arr: T[], n: number, mk: () => T): T[] {
  const out = arr.slice(0, n);
  while (out.length < n) out.push(mk());
  return out;
}

/* ---- the sheet: each screen has its own layout — the main form and the
   text change places, so the transformation moves the whole composition,
   not only the figures ---- */
type Box = { x: number; y: number; w: number; h: number };
function boxesFor(k: number, w: number, h: number): { main: Box; left: Box; right: Box; strip: Box } {
  const b = (x: number, y: number, bw: number, bh: number): Box => ({ x: w * x, y: h * y, w: w * bw, h: h * bh });
  const strip = b(0.5, 0.06, 0.18, 0.035);
  if (k === 1) return { main: b(0.03, 0.24, 0.5, 0.45), left: b(0.03, 0.79, 0.42, 0.18), right: b(0.66, 0.64, 0.31, 0.32), strip };
  if (k === 2) return { main: b(0.05, 0.14, 0.57, 0.5), left: b(0.64, 0.16, 0.05, 0.4), right: b(0.05, 0.68, 0.57, 0.05), strip };
  if (k === 3) return { main: b(0.46, 0.08, 0.5, 0.86), left: b(0.03, 0.72, 0.16, 0.2), right: b(0.82, 0.72, 0.15, 0.2), strip };
  if (k === 4) return { main: b(0.05, 0.1, 0.46, 0.54), left: b(0.6, 0.78, 0.18, 0.19), right: b(0.03, 0.75, 0.52, 0.21), strip };
  return { main: b(0.56, 0.2, 0.41, 0.5), left: b(0.05, 0.62, 0.22, 0.34), right: b(0.5, 0.78, 0.44, 0.17), strip };
}
const tilesBox = (w: number, h: number): Box => ({ x: w * 0.72, y: h * 0.06, w: w * 0.19, h: h * 0.035 });

/* ================= screen 0 — TRACE ================= */
function screenTrace(w: number, h: number, t: number): Frame {
  const B = boxesFor(0, w, h);
  const pts: Pt[] = [];
  const polys: Poly[] = [];
  /* the SPHERE — a circle of 36 meridians, rings above, columns fading below */
  const cx = B.main.x + B.main.w * 0.5;
  const cy = B.main.y + B.main.h * 0.5;
  const R = Math.min(B.main.w, B.main.h) * 0.4;
  const spin = t * 0.06;
  const tilt = 0.42;
  const breathe = 1 + 0.015 * Math.sin(t * 0.6);
  const beat = Math.floor(t * 0.5);
  const litCol = Math.round((bus.period / 23) * 36) % 36;
  const flash = decay(bus.periodChangedAt, t, 2.4);
  for (let i = 0; i < 900; i++) {
    const j = Math.floor(i / 25);
    const k = i % 25;
    const onCol = j === litCol;
    const lon = (j / 36) * TAU + spin;
    const lat = (Math.PI / 2) * (1 - (2 * (k + 0.5)) / 25);
    const ux = Math.cos(lat) * Math.sin(lon);
    const up = Math.sin(lat);
    const depth = Math.cos(lat) * Math.cos(lon);
    const y2 = up * Math.cos(tilt) - depth * Math.sin(tilt);
    const z2 = up * Math.sin(tilt) + depth * Math.cos(tilt);
    const front = 0.5 + 0.5 * z2;
    const v = (k + 0.5) / 25;
    const c: RGB = v < 0.25 ? mix(C_CORAL, C_PAPER, v / 0.25) : v < 0.6 ? C_PAPER : mix(C_PAPER, C_MINT, (v - 0.6) / 0.4);
    const fade = v < 0.5 ? 1 : 1 - (v - 0.5) * 1.5;
    const lit = hash(beat * 7919 + i) < 0.05;
    pts.push(pt(cx + R * ux * breathe, cy - R * y2 * breathe, (2.6 - v * 1.4) * (0.5 + 0.5 * front) + (lit ? 1 : 0) + (onCol ? 0.8 * flash : 0), Math.min(1, (0.35 + 0.65 * front) * fade + (lit ? 0.4 : 0) + (onCol ? 0.5 : 0)), onCol ? mix(c, C_CORAL, 0.5 + 0.5 * flash) : c));
  }
  polys.push(ringPoly(cx, cy, R * 1.04, R * 1.04, 0, 0.22, 0.8));
  /* the FUNNEL — dotted rings down a bright axis into a spiral */
  const fx = B.left.x + B.left.w * 0.5;
  const top = B.left.y + B.left.h * 0.06;
  const bottom = B.left.y + B.left.h * 0.88;
  const radiusAt = (u: number) => B.left.w * 0.5 * (0.05 + 0.95 * Math.pow(1 - u, 1.4));
  const litRing = bus.period % 12;
  const flowPulse = decay(bus.flowAt, t, 2);
  for (let i = 0; i < 300; i++) {
    if (i < 240) {
      const k = Math.floor(i / 20);
      const u = k / 11;
      const th = ((i % 20) / 20) * TAU + t * (0.25 + u * 0.4) * (1 + flowPulse);
      const rad = radiusAt(u) * (1 + (hash(i) - 0.5) * 0.22);
      const front = 0.5 + 0.5 * Math.sin(th);
      const lit = k === litRing;
      pts.push(pt(fx + Math.cos(th) * rad, top + (bottom - top) * u + Math.sin(th) * rad * 0.28, (1 + 0.9 * front) * (1 - u * 0.5) * (lit ? 1.5 : 1), Math.min(1, (0.25 + 0.6 * front) * (lit ? 1.5 : 1)), lit ? C_CORAL : mix(C_MINT, C_PAPER, u)));
    } else {
      const j = i - 240;
      const u = hash(j * 5 + 1);
      const th = hash(j * 5 + 2) * TAU + t * 0.25;
      const rad = radiusAt(u) * Math.sqrt(hash(j * 5 + 3));
      pts.push(pt(fx + Math.cos(th) * rad, top + (bottom - top) * u, 0.7 + hash(j), 0.25, mix(C_MINT, C_PAPER, u)));
    }
  }
  polys.push(linePoly(fx, top - B.left.h * 0.04, fx, bottom + B.left.h * 0.06, 0.9, 1.4));
  polys.push(curvePoly((u) => [fx + Math.cos(u * TAU * 2.5 + t * 0.6) * (2 + u * 18), bottom + B.left.h * 0.09 + Math.sin(u * TAU * 2.5 + t * 0.6) * (2 + u * 18) * 0.35], 0.8, 1));
  /* the STRIP — 23 cells the periods, the window at the bus's period */
  const win = bus.periodF;
  void t;
  for (let i = 0; i < 46; i++) {
    const c = i % 23;
    const r = Math.floor(i / 23);
    const d = Math.abs(c - win);
    const hot = d < 2.5 ? 1 - d / 2.5 : 0;
    pts.push(pt(B.strip.x + (c + 0.5) * (B.strip.w / 23), B.strip.y + (r + 0.5) * (B.strip.h / 2), B.strip.w / 23 * 0.42, hot > 0.3 ? 0.3 + 0.7 * hot : 0.2, hot > 0.3 ? C_CORAL : C_PAPER, 1));
  }
  /* the LATTICE — a grid sunk toward a mass, one orbit, the time axis */
  const gx0 = B.right.x;
  const gx1 = B.right.x + B.right.w;
  const gy0 = B.right.y;
  const gy1 = B.right.y + B.right.h * 0.72;
  /* the mass stands at the period's place on the axis; the well deepens
     when the funnel delivers */
  const mx = gx0 + B.right.w * (0.3 + 0.4 * Math.min(1, bus.periodF / 22));
  const my = gy0 + (gy1 - gy0) * 0.5;
  const depth = 1 + 0.6 * flowPulse;
  const sink = (px: number, py: number): XY => {
    const dx = px - mx;
    const dy = py - my;
    const d = Math.hypot(dx, dy) + 1e-3;
    const pull = (1800 * depth) / (d * d + 1800);
    return [px - (dx / d) * pull * 22, py - (dy / d) * pull * 22 + pull * 12];
  };
  for (let i = 0; i <= 13; i++) polys.push(curvePoly((u) => sink(gx0 + (i / 13) * (gx1 - gx0), gy0 + u * (gy1 - gy0)), 0.28, 0.8));
  for (let j = 0; j <= 5; j++) polys.push(curvePoly((u) => sink(gx0 + u * (gx1 - gx0), gy0 + (j / 5) * (gy1 - gy0)), 0.28, 0.8));
  for (let i = 0; i < 154; i++) {
    const c = i % 14;
    const r = Math.floor(i / 14);
    const [sx, sy] = sink(gx0 + (c / 13) * (gx1 - gx0), gy0 + (r / 10) * (gy1 - gy0));
    pts.push(pt(sx, sy, 0.9, 0.35));
  }
  polys.push(ringPoly(mx, my, B.right.w * 0.3, B.right.h * 0.26, -0.2, 0.6, 1, C_CORAL));
  const oa = t * 0.45;
  const ox = mx + Math.cos(oa) * B.right.w * 0.3 * Math.cos(-0.2) - Math.sin(oa) * B.right.h * 0.26 * Math.sin(-0.2);
  const oy = my + Math.cos(oa) * B.right.w * 0.3 * Math.sin(-0.2) + Math.sin(oa) * B.right.h * 0.26 * Math.cos(-0.2);
  const axY = B.right.y + B.right.h * 0.96;
  const ax0 = B.right.x + B.right.w * 0.3;
  const ax1 = B.right.x + B.right.w * 0.7;
  polys.push(linePoly(ax0, axY, ax1, axY, 0.85, 1));
  polys.push(linePoly(mx, my, Math.min(ax1, Math.max(ax0, mx)), axY, 0.6, 1, C_CORAL, 1));
  pts.push(pt(mx, my, 3.5, 1, C_CORAL), pt(ox, oy, 2.4, 1, C_CORAL), pt(Math.min(ax1, Math.max(ax0, mx)), axY, 2.4, 1, C_CORAL));
  for (let i = 0; i < 23; i++) pts.push(pt(ax0 + (i / 22) * (ax1 - ax0), axY, i % 5 === 0 ? 1.6 : 1, 0.7));
  const crown: XY = [cx, cy - R * Math.cos(tilt) * breathe];
  pts.push(pt(crown[0], crown[1], 2.8, 1, C_CORAL));
  return {
    pts: pad(pts, N, () => pt(cx, cy, 0.6, 0)),
    polys: pad(polys, M, () => parkedPoly(cx, cy)),
    cursor: crown,
    main: { x0: cx - R * 1.04, y0: cy - R * 1.04, x1: cx + R * 1.04, y1: cy + R * 1.04 },
    anchors: { top: [cx, cy - R * 1.04], left: [cx - R * 1.04, cy], funnelTop: [fx, top - B.left.h * 0.04], funnelFoot: [fx, bottom + B.left.h * 0.09], mass: [mx, my], axisFoot: [Math.min(ax1, Math.max(ax0, mx)), axY], strip: [B.strip.x, B.strip.y + B.strip.h * 0.5], years: [ax0, axY] },
  };
}

/* ================= screen 1 — Context Canvas ================= */
function screenContext(w: number, h: number, t: number): Frame {
  const B = boxesFor(1, w, h);
  const pts: Pt[] = [];
  const polys: Poly[] = [];
  /* the CHAIN — five overlapping rings, the record's coral inner ring, a line through */
  const cx = B.main.x + B.main.w * 0.5;
  const cy = B.main.y + B.main.h * 0.5;
  const r = Math.min(B.main.w, B.main.h) * 0.19;
  const step = r * 0.82;
  const left = cx - step * 2;
  /* the context ring the network's walk has reached */
  const ctxRing = bus.walkNode[2] % 5;
  const walkFlash = decay(bus.walkDoneAt, t, 2.4);
  for (let i = 0; i < 900; i++) {
    const c = Math.min(4, Math.floor(i / 180));
    const j = i - c * 180;
    const th = (j / 180) * TAU + 0.03 * Math.sin(t * 0.9 + c);
    const inner = c === 2 && j % 4 === 0;
    const rr = inner ? r * 0.42 : r;
    const glide = 0.5 + 0.5 * Math.sin(th * 2 - t * 0.8 + c);
    const on = c === ctxRing;
    pts.push(pt(left + c * step + Math.cos(th) * rr, cy + Math.sin(th) * rr, inner ? 1.9 : on ? 1.8 : 1.4, (c === 2 ? 0.7 : on ? 0.8 : 0.4) + 0.3 * glide, inner ? C_CORAL : on ? mix(C_PAPER, C_SKY, 0.5 + 0.5 * walkFlash) : C_PAPER));
  }
  for (let c = 0; c < 5; c++) polys.push(ringPoly(left + c * step, cy, r, r, 0, c === 2 ? 0.7 : c === ctxRing ? 0.8 : 0.35, c === ctxRing ? 1.2 : 0.9, c === ctxRing ? C_SKY : C_PAPER));
  polys.push(ringPoly(cx, cy, r * 0.42, r * 0.42, 0, 0.9));
  polys.push(linePoly(left - r * 1.2, cy, left + 4 * step + r * 1.2, cy, 0.45));
  const ang = -1.05 + 0.08 * Math.sin(t * 0.35);
  polys.push(linePoly(cx - Math.cos(ang) * r * 1.7, cy - Math.sin(ang) * r * 1.7, cx + Math.cos(ang) * r * 1.7, cy + Math.sin(ang) * r * 1.7, 0.9));
  /* the NETWORK — five layers of nodes, edges between, a signal walking */
  const L = [4, 6, 6, 6, 4];
  const nx = (c: number) => B.left.x + (c / 4) * B.left.w;
  const ny = (c: number, i: number) => B.left.y + B.left.h * 0.5 + (i - (L[c] - 1) / 2) * (B.left.h / 6);
  const walk = bus.walkNode;
  let ei = 0;
  for (let c = 0; c < 4; c++) for (let a = 0; a < L[c]; a++) for (let b = 0; b < L[c + 1]; b++) {
    const on = walk[c] === a && walk[c + 1] === b;
    for (let k = 0; k < 2; k++) {
      const u = ((hash(ei * 7 + k) + t * 0.05) % 1);
      if (pts.length < 900 + 274) pts.push(pt(lerp(nx(c), nx(c + 1), u), lerp(ny(c, a), ny(c + 1, b), u), on ? 1.8 : 0.9, on ? 0.9 : 0.22, on ? C_SKY : C_PAPER));
    }
    if (on) polys.push(linePoly(nx(c), ny(c, a), nx(c + 1), ny(c + 1, b), 0.7, 1, C_SKY));
    ei++;
  }
  L.forEach((n, c) => {
    for (let i = 0; i < n; i++) pts.push(pt(nx(c), ny(c, i), 4.2, walk[c] === i ? 1 : 0.55, walk[c] === i ? C_SKY : C_PAPER, 2));
  });
  /* the HALFTONE — a field of dots whose size follows a moving gradient */
  for (let i = 0; i < 200; i++) {
    const c = i % 20;
    const rr = Math.floor(i / 20);
    const x = B.right.x + (c + 0.5) * (B.right.w / 20);
    const y = B.right.y + (rr + 0.5) * (B.right.h / 10);
    /* the gradient's centre is where the walk is, column for column */
    const centreCol = bus.walkStep * 20;
    const dcol = Math.abs(c - centreCol);
    const g = clamp01(1 - dcol / 7) * (0.6 + 0.4 * Math.cos(rr * 0.5 + t * 0.3));
    pts.push(pt(x, y, 0.8 + 4.2 * g, 0.25 + 0.6 * g, g > 0.75 ? mix(C_PAPER, C_SKY, 0.5) : C_PAPER));
  }
  const rec: XY = [cx, cy];
  pts.push(pt(cx, cy, 3, 1, C_CORAL));
  return {
    pts: pad(pts, N, () => pt(cx, cy, 0.6, 0)),
    polys: pad(polys, M, () => parkedPoly(cx, cy)),
    cursor: rec,
    main: { x0: left - r * 1.25, y0: cy - r * 1.3, x1: left + 4 * step + r * 1.25, y1: cy + r * 1.3 },
    anchors: { top: [cx, cy - r * 1.3], left: [left - r * 1.25, cy], netIn: [nx(0), ny(0, walk[0])], netOut: [nx(4), ny(4, walk[4])], halftone: [B.right.x + B.right.w, B.right.y + B.right.h * 0.5], record: rec },
  };
}

/* ================= screen 2 — Spacetime ================= */
/* map and time: the WORLD MAP — the governed coastlines in an
   equirectangular frame with a 30° graticule, one aggregate mark per
   mapped geography at its feature's label point, sized by its source
   assignments, the one the bus holds in coral with a bearing line from
   the frame's centre; the GEOGRAPHY TAPE, vertical at the right — the six
   largest mapped geographies as bars; the TIME TAPE below the map — the
   23 periods with the current one bracketed in coral */
const LON0 = -170;
const LON1 = 180;
const LAT0 = -56;
const LAT1 = 84;
function screenSpacetime(w: number, h: number, t: number): Frame {
  const B = boxesFor(2, w, h);
  const pts: Pt[] = [];
  const polys: Poly[] = [];
  const proj = (lon: number, lat: number): XY => [B.main.x + ((lon - LON0) / (LON1 - LON0)) * B.main.w, B.main.y + ((LAT1 - lat) / (LAT1 - LAT0)) * B.main.h];
  /* the frame and the graticule */
  polys.push(linePoly(B.main.x, B.main.y, B.main.x + B.main.w, B.main.y, 0.4), linePoly(B.main.x + B.main.w, B.main.y, B.main.x + B.main.w, B.main.y + B.main.h, 0.4), linePoly(B.main.x + B.main.w, B.main.y + B.main.h, B.main.x, B.main.y + B.main.h, 0.4), linePoly(B.main.x, B.main.y + B.main.h, B.main.x, B.main.y, 0.4));
  for (let lon = -150; lon <= 180; lon += 30) {
    const [x] = proj(lon, 0);
    polys.push(linePoly(x, B.main.y, x, B.main.y + B.main.h, 0.12, 0.7));
  }
  for (let lat = -30; lat <= 60; lat += 30) {
    const [, y] = proj(0, lat);
    polys.push(linePoly(B.main.x, y, B.main.x + B.main.w, y, lat === 0 ? 0.22 : 0.12, 0.7));
  }
  /* the coastlines, as points along the rings — the governed matter */
  const ringLens = WORLD.map((r) => r.length / 2);
  const totalPts = ringLens.reduce((a, b) => a + b, 0);
  let budget = 1200;
  WORLD.forEach((r, ri) => {
    const n = ri === WORLD.length - 1 ? budget : Math.max(2, Math.round((ringLens[ri] / totalPts) * 1200));
    budget -= n;
    const m = ringLens[ri];
    for (let i = 0; i < n; i++) {
      const u = (i / n) * m;
      const i0 = Math.floor(u) % m;
      const i1 = (i0 + 1) % m;
      const f = u - Math.floor(u);
      const lon = lerp(r[i0 * 2], r[i1 * 2], f);
      const lat = lerp(r[i0 * 2 + 1], r[i1 * 2 + 1], f);
      if (Math.abs(r[i0 * 2] - r[i1 * 2]) > 90) continue;
      const [x, y] = proj(lon, lat);
      if (x < B.main.x || x > B.main.x + B.main.w || y < B.main.y || y > B.main.y + B.main.h) continue;
      pts.push(pt(x, y, 1, 0.6));
    }
  });
  /* the marks: one per mapped geography, sized by its assignments; the
     bus holds one of the six largest */
  const maxN = MARKS[0]?.n ?? 1;
  const held = bus.region % 6;
  let cur: XY = proj(0, 0);
  MARKS.forEach((mk, i) => {
    const [x, y] = proj(mk.lon, mk.lat);
    const r = 3 + 11 * Math.sqrt(mk.n / maxN);
    const on = i === held;
    polys.push(ringPoly(x, y, r, r, 0, on ? 0.95 : 0.35, on ? 1.2 : 0.8, on ? C_CORAL : C_PAPER));
    pts.push(pt(x, y, on ? 2.6 : 1.4, on ? 1 : 0.6, on ? C_CORAL : mix(C_PAPER, C_SKY, 0.5)));
    if (on) cur = [x, y];
  });
  const fc: XY = [B.main.x + B.main.w * 0.5, B.main.y + B.main.h * 0.5];
  polys.push(linePoly(fc[0], fc[1], cur[0], cur[1], 0.55, 0.9, C_CORAL, 1));
  pts.push(pt(fc[0], fc[1], 1.6, 0.6));
  /* the geography tape, vertical: the six largest, as bars */
  const tx = B.left.x + B.left.w * 0.5;
  const ty0 = B.left.y;
  const ty1 = B.left.y + B.left.h;
  polys.push(linePoly(tx, ty0, tx, ty1, 0.5, 1));
  for (let i = 0; i <= 24; i++) pts.push(pt(tx - (i % 4 === 0 ? 8 : 4), ty0 + (i / 24) * (ty1 - ty0), 1, 0.5, C_PAPER, 1));
  for (let k = 0; k < 6; k++) {
    const y = ty0 + ((k + 0.5) / 6) * (ty1 - ty0);
    const on = k === held;
    const len = B.left.w * 3 * ((MARKS[k]?.n ?? 1) / maxN);
    polys.push(linePoly(tx + 6, y, tx + 6 + len, y, on ? 0.95 : 0.4, on ? 2 : 1.2, on ? C_CORAL : C_PAPER));
    pts.push(pt(tx, y, on ? 2.4 : 1.6, on ? 1 : 0.6, on ? C_CORAL : C_PAPER));
  }
  /* the time tape */
  const ax0 = B.right.x;
  const ax1 = B.right.x + B.right.w;
  const ay = B.right.y + B.right.h * 0.5;
  polys.push(linePoly(ax0, ay, ax1, ay, 0.6, 1));
  for (let i = 0; i < 23; i++) {
    const x = ax0 + (i / 22) * (ax1 - ax0);
    const big = i % 5 === 0;
    pts.push(pt(x, ay - (big ? 9 : 5), 1, 0.6, C_PAPER, 1), pt(x, ay + (big ? 9 : 5), 1, 0.6, C_PAPER, 1));
  }
  const px = ax0 + (Math.min(22, bus.periodF) / 22) * (ax1 - ax0);
  polys.push(linePoly(px - 10, ay - 16, px - 10, ay + 16, 0.9, 1.2, C_CORAL), linePoly(px + 10, ay - 16, px + 10, ay + 16, 0.9, 1.2, C_CORAL));
  pts.push(pt(px, ay, 2.6, 1, C_CORAL));
  return {
    pts: pad(pts, N, () => pt(fc[0], fc[1], 0.6, 0)),
    polys: pad(polys, M, () => parkedPoly(fc[0], fc[1])),
    cursor: cur,
    main: { x0: B.main.x - 12, y0: B.main.y - 12, x1: B.main.x + B.main.w + 12, y1: B.main.y + B.main.h + 12 },
    anchors: { top: [fc[0], B.main.y - 12], left: [B.main.x - 12, fc[1]], cursor: cur, regionTape: [tx, ty0 + ((held + 0.5) / 6) * (ty1 - ty0)], tapeCursor: [px, ay], tapeL: [ax0, ay], tapeR: [ax1, ay] },
  };
}

/* ================= screen 3 — Exploration ================= */
function screenExploration(w: number, h: number, t: number): Frame {
  const B = boxesFor(4, w, h);
  const pts: Pt[] = [];
  const polys: Poly[] = [];
  /* the DIAL — a ring a wave of light sweeps, a satellite with its crosshair, the open inquiry apart */
  const cx = B.main.x + B.main.w * 0.46;
  const cy = B.main.y + B.main.h * 0.5;
  const R = Math.min(B.main.w, B.main.h) * 0.34;
  const head = t * 0.5;
  const sx = cx + R * 0.95;
  const sy = cy + R * 0.62;
  const sr = R * 0.3;
  for (let i = 0; i < 900; i++) {
    if (i < 640) {
      const th = (i / 640) * TAU;
      let d = ((th - head) % TAU + TAU) % TAU;
      if (d > Math.PI) d -= TAU;
      const inSweep = d <= 0 && d > -Math.PI * 0.75;
      const g = inSweep ? 0.45 + 0.55 * (1 + d / (Math.PI * 0.75)) : 0;
      pts.push(pt(cx + Math.cos(th) * R, cy + Math.sin(th) * R, inSweep ? 2 : 1.3, 0.3 + 0.7 * g, inSweep ? mix(C_PAPER, C_SKY, 0.5) : C_PAPER));
    } else if (i < 790) {
      const th = ((i - 640) / 150) * TAU;
      pts.push(pt(sx + Math.cos(th) * sr, sy + Math.sin(th) * sr, 1.3, 0.6));
    } else {
      const j = i - 790;
      const u = (j / 110) * 2 - 1;
      pts.push(j % 2 === 0 ? pt(sx + u * R * 1.2, sy, 1.1, 0.45) : pt(sx, sy + u * R * 1.2, 1.1, 0.45));
    }
  }
  polys.push(ringPoly(cx, cy, R, R, 0, 0.3, 1));
  polys.push(ringPoly(cx, cy, R, R, 0, 1, 2.2, C_PAPER, 0, head - Math.PI * 0.75, 0.375));
  polys.push(ringPoly(sx, sy, sr, sr, 0, 0.9, 1));
  polys.push(ringPoly(sx, sy, sr * 0.45, sr * 0.45, 0, 0.8, 0.8));
  polys.push(ringPoly(cx - R * 0.95, cy - R * 0.85, sr * 0.7, sr * 0.7, 0, 0.8, 1, C_SAND, 1));
  polys.push(linePoly(sx - R * 1.7, sy, sx + R * 0.7, sy, 0.45, 1));
  polys.push(linePoly(sx, sy - R * 1.9, sx, sy + R * 0.7, 0.45, 1));
  polys.push(linePoly(sx - R * 1.9, sy + R * 1.2, sx + R * 0.35, sy - R * 1.05, 0.5, 0.8));
  const hp: XY = [cx + Math.cos(head) * R, cy + Math.sin(head) * R];
  const bump = decay(bus.pulseAt, t, 3);
  /* the WAVE — a packet on a line whose centre follows the sweep, the inquiry loop apart */
  const wy = B.right.y + B.right.h * 0.55;
  const wc = B.right.x + B.right.w * (0.5 + 0.35 * Math.sin(head));
  polys.push(linePoly(B.right.x, wy, B.right.x + B.right.w, wy, 0.35));
  polys.push(curvePoly((u) => {
    const x = B.right.x + u * B.right.w;
    const d = x - wc;
    const env = Math.exp(-(d * d) / (2 * 110 * 110));
    return [x, wy - B.right.h * (0.32 + 0.3 * bump) * env * Math.sin(d / 12 - t * 1.2)];
  }, 0.9, 1.3, C_CORAL));
  for (let i = 0; i < 200; i++) {
    const u = (i + 0.5) / 200;
    const x = B.right.x + u * B.right.w;
    const d = x - wc;
    const env = Math.exp(-(d * d) / (2 * 110 * 110));
    pts.push(pt(x, wy - B.right.h * (0.32 + 0.3 * bump) * env * Math.sin(d / 12 - t * 1.2), 0.8 + 1.4 * env, 0.25 + 0.7 * env, mix(C_PAPER, C_CORAL, env)));
  }
  const lx = B.right.x + B.right.w * 0.88;
  const ly = B.right.y + B.right.h * 0.12;
  polys.push(ringPoly(lx, ly, B.right.h * 0.1 * (1 + 0.3 * bump), B.right.h * 0.1 * (1 + 0.3 * bump), 0, 0.5 + 0.5 * bump, 1, C_SAND, 1));
  for (let i = 0; i < 50; i++) {
    const u = (i / 50) * TAU;
    pts.push(pt(lx + Math.cos(u) * B.right.h * 0.1, ly + Math.sin(u) * B.right.h * 0.1, 1, 0.5, C_SAND));
  }
  pts.push(pt(hp[0], hp[1], 2.6, 1, C_SKY), pt(sx, sy, 1.6, 1));
  return {
    pts: pad(pts, N, () => pt(cx, cy, 0.6, 0)),
    polys: pad(polys, M, () => parkedPoly(cx, cy)),
    cursor: hp,
    main: { x0: cx - R * 1.06, y0: cy - R * 1.06, x1: sx + sr * 1.3, y1: cy + R * 1.06 },
    anchors: { top: [cx, cy - R * 1.06], left: [cx - R * 1.06, cy], head: hp, sat: [sx, sy], wavePeak: [B.right.x + B.right.w * 0.5, wy - B.right.h * 0.34], loop: [lx, ly - B.right.h * 0.1] },
  };
}

/* ================= screen 3 — BETWEEN RECORDS =================
   The owner's prototype is Exploration's scope — the coral dotted
   figure with its glowing head — seven times, one inside the next: each
   ring a closed Lissajous figure of its own ratio, its particles coral,
   a bright head tracing it at its own slow pace, all on the scope's
   scales. The figures never change; across the hold the scroll changes
   only how they are drawn — with few straight segments, then smoothly,
   then few again. Patterns no single record carries, kept as
   observations, never closed into a claim. */
export const PATTERN_HOLD: [number, number] = [0.6, 0.76];
function screenPattern(w: number, h: number, t: number): Frame {
  const B = boxesFor(3, w, h);
  const pts: Pt[] = [];
  const polys: Poly[] = [];
  const cx = B.main.x + B.main.w * 0.5;
  const cy = B.main.y + B.main.h * 0.48;
  const R = Math.min(B.main.w, B.main.h) * 0.42;
  const prog = clamp01((SCROLL - PATTERN_HOLD[0]) / (PATTERN_HOLD[1] - PATTERN_HOLD[0]));
  const round = Math.sin(prog * Math.PI);
  const COARSE = 8;
  /* the scope's figure — sin 5u by sin 4u — seven times, one inside the
     next, all in step; one head per ring, all at the same place on the
     curve */
  const ph = t * 0.06;
  const smoothAt = (k: number, u: number): XY => {
    const sc = R * (0.22 + 0.78 * (k / 6));
    return [cx + sc * Math.sin(5 * u + ph), cy + sc * 0.9 * Math.sin(4 * u)];
  };
  /* the same curve sampled at eight straight segments, blended with its
     smooth form by the scroll — continuous, so nothing steps */
  const ringAt = (k: number, u: number): XY => {
    const step = TAU / COARSE;
    const i0 = Math.floor(u / step);
    const f = (u - i0 * step) / step;
    const p0 = smoothAt(k, i0 * step);
    const p1 = smoothAt(k, (i0 + 1) * step);
    const sm = smoothAt(k, u);
    return [lerp(lerp(p0[0], p1[0], f), sm[0], round), lerp(lerp(p0[1], p1[1], f), sm[1], round)];
  };
  const headU = ((t * 0.045) % 1) * TAU;
  for (let k = 0; k < 7; k++) {
    for (let i = 0; i < 200; i++) {
      const u = (i / 200) * TAU;
      const [px, py] = ringAt(k, u);
      const lead = ((u - headU) % TAU + TAU) % TAU;
      const on = lead < 0.6;
      pts.push(pt(px, py, 1.2 + (on ? 1.6 : 0), on ? 1 : 0.5, C_CORAL));
    }
  }
  /* the scope's scales: a left edge and a bottom edge with ticks */
  const sx = B.main.x + B.main.w * 0.04;
  const sy = B.main.y + B.main.h * 0.95;
  polys.push(linePoly(sx, B.main.y + B.main.h * 0.02, sx, sy, 0.55), linePoly(sx, sy, B.main.x + B.main.w * 0.98, sy, 0.55));
  for (let i = 0; i <= 10; i++) {
    pts.push(pt(sx - (i % 5 === 0 ? 8 : 4), B.main.y + B.main.h * 0.02 + (i / 10) * (sy - B.main.y - B.main.h * 0.02), 1.2, 0.6, C_PAPER, 1));
    pts.push(pt(sx + (i / 10) * (B.main.w * 0.94), sy + (i % 5 === 0 ? 8 : 4), 1.2, 0.6, C_PAPER, 1));
  }
  const head6 = ringAt(6, headU);
  return {
    pts: pad(pts, N, () => pt(cx, cy, 0.6, 0)),
    polys: pad(polys, M, () => parkedPoly(cx, cy)),
    cursor: head6,
    main: { x0: B.main.x, y0: B.main.y, x1: B.main.x + B.main.w, y1: B.main.y + B.main.h },
    anchors: { top: [cx, B.main.y], left: [B.main.x, cy], head: head6, wall: [B.main.x + B.main.w, B.main.y] },
    frame: 0,
  };
}

const SCREENS = [screenTrace, screenContext, screenSpacetime, screenPattern, screenExploration];

/* ---- the transformation: every particle and every line moves to its
   place in the next screen ---- */
function blend(A: Frame, B: Frame, f: number): Frame {
  if (f <= 0) return A;
  if (f >= 1) return B;
  const L = (a: number, b: number) => lerp(a, b, f);
  return {
    pts: A.pts.map((d, i) => {
      const q = B.pts[i];
      return { x: L(d.x, q.x), y: L(d.y, q.y), r: L(d.r, q.r), bright: L(d.bright, q.bright), c: mix(d.c, q.c, f), kind: f < 0.5 ? d.kind : q.kind, ang: L(d.ang, q.ang) };
    }),
    polys: A.polys.map((p, i) => {
      const q = B.polys[i];
      return { v: p.v.map((v, k) => [L(v[0], q.v[k][0]), L(v[1], q.v[k][1])] as XY), bright: L(p.bright, q.bright), width: L(p.width, q.width), c: mix(p.c, q.c, f), dashed: f < 0.5 ? p.dashed : q.dashed };
    }),
    cursor: [L(A.cursor[0], B.cursor[0]), L(A.cursor[1], B.cursor[1])],
    main: { x0: L(A.main.x0, B.main.x0), y0: L(A.main.y0, B.main.y0), x1: L(A.main.x1, B.main.x1), y1: L(A.main.y1, B.main.y1) },
    anchors: f < 0.5 ? A.anchors : B.anchors,
  };
}

/* ---- strokes ---- */
function glow(ctx: CanvasRenderingContext2D, draw: () => void, bright: number, width: number, col = PAPER) {
  if (bright <= 0.01) return;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.strokeStyle = `rgba(${col},${0.05 * bright})`;
  ctx.lineWidth = width * 9;
  draw();
  ctx.strokeStyle = `rgba(${col},${0.12 * bright})`;
  ctx.lineWidth = width * 3.2;
  draw();
  ctx.strokeStyle = `rgba(${col},${Math.min(1, 0.55 + 0.45 * bright) * bright})`;
  ctx.lineWidth = width;
  draw();
}
function point(ctx: CanvasRenderingContext2D, x: number, y: number, r: number, bright: number, col = PAPER) {
  if (bright <= 0.01 || r <= 0.05) return;
  if (bright > 0.45) {
    ctx.fillStyle = `rgba(${col},${0.08 * bright})`;
    ctx.beginPath();
    ctx.arc(x, y, r * 3.2, 0, TAU);
    ctx.fill();
  }
  ctx.fillStyle = `rgba(${col},${Math.min(1, 0.9 * bright)})`;
  ctx.beginPath();
  ctx.arc(x, y, r, 0, TAU);
  ctx.fill();
}
function cap(ctx: CanvasRenderingContext2D, x: number, y: number, bright: number) {
  if (bright <= 0.01) return;
  ctx.fillStyle = `rgba(${PAPER},${0.85 * bright})`;
  ctx.fillRect(x - 2.5, y - 2.5, 5, 5);
}
function drawFrame(ctx: CanvasRenderingContext2D, F: Frame, e: number) {
  F.polys.forEach((p) => {
    if (p.bright <= 0.01) return;
    const n = Math.max(2, Math.round(V * e));
    const draw = () => {
      ctx.beginPath();
      for (let i = 0; i < n; i++) (i === 0 ? ctx.moveTo(p.v[i][0], p.v[i][1]) : ctx.lineTo(p.v[i][0], p.v[i][1]));
      ctx.stroke();
    };
    if (p.dashed > 0.5) {
      ctx.setLineDash([3, 5]);
      ctx.strokeStyle = `rgba(${rgb(p.c)},${0.85 * p.bright})`;
      ctx.lineWidth = 1;
      draw();
      ctx.setLineDash([]);
    } else glow(ctx, draw, p.bright, p.width, rgb(p.c));
  });
  const [cx, cy] = F.cursor;
  F.pts.forEach((d, i) => {
    const local = ease((e - (i / N) * 0.5) / 0.5);
    if (local <= 0 || d.bright <= 0.01) return;
    const x = cx + (d.x - cx) * local;
    const y = cy + (d.y - cy) * local;
    const b = d.bright * local;
    const col = rgb(d.c);
    if (d.kind === 1) {
      ctx.fillStyle = `rgba(${col},${Math.min(1, 0.9 * b)})`;
      ctx.fillRect(x - d.r, y - d.r, d.r * 2, d.r * 2);
      return;
    }
    if (d.kind === 2) {
      ctx.beginPath();
      ctx.arc(x, y, d.r, 0, TAU);
      ctx.fillStyle = "rgba(10,10,11,1)";
      ctx.fill();
      ctx.strokeStyle = `rgba(${col},${0.9 * b})`;
      ctx.lineWidth = 1.2;
      ctx.stroke();
      return;
    }
    if (d.kind === 3) {
      const l = 4 + d.r * 3;
      ctx.strokeStyle = `rgba(${col},${Math.min(1, 0.9 * b)})`;
      ctx.lineWidth = 1.4;
      ctx.beginPath();
      ctx.moveTo(x - Math.cos(d.ang) * l * 0.5, y - Math.sin(d.ang) * l * 0.5);
      ctx.lineTo(x + Math.cos(d.ang) * l * 0.5, y + Math.sin(d.ang) * l * 0.5);
      ctx.stroke();
      return;
    }
    point(ctx, x, y, d.r, b, col);
  });
}

/* ---- the HUD ---- */
function drawTracking(ctx: CanvasRenderingContext2D, box: { x0: number; y0: number; x1: number; y1: number }, bright: number) {
  if (bright <= 0.01) return;
  const arm = Math.min(box.x1 - box.x0, box.y1 - box.y0) * 0.1;
  ctx.strokeStyle = `rgba(${PAPER},${0.8 * bright})`;
  ctx.lineWidth = 1.2;
  ctx.beginPath();
  for (const [x, y, dx, dy] of [
    [box.x0, box.y0, 1, 1],
    [box.x1, box.y0, -1, 1],
    [box.x0, box.y1, 1, -1],
    [box.x1, box.y1, -1, -1],
  ]) {
    ctx.moveTo(x + dx * arm, y);
    ctx.lineTo(x, y);
    ctx.lineTo(x, y + dy * arm);
  }
  ctx.stroke();
}
function drawTiles(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, t: number, e: number, burst: number) {
  const beat = Math.floor(t * 0.6);
  const cols = 7;
  const rows = 4;
  const blocks = 3;
  const cell = Math.min((w - (blocks - 1) * 16) / blocks / cols, h / rows);
  for (let k = 0; k < blocks; k++) {
    const ox = x + k * (cols * cell + 16);
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const idx = r * cols + c;
        const lit = hash(beat * 7919 + k * 104729 + idx) < 0.42 + 0.4 * burst;
        const local = ease((e - (k * cols + c) * 0.012) / 0.4);
        if (local <= 0) continue;
        point(ctx, ox + c * cell + cell * 0.5, y + r * cell + cell * 0.5, lit ? 1.9 : 1.1, local * (lit ? 0.9 : 0.25), burst > 0.5 && lit ? CORAL : PAPER);
      }
    }
  }
}
function elbow(a: XY, b: XY, bend = 0.55): XY[] {
  const bx = a[0] + (b[0] - a[0]) * bend;
  return [a, [bx, a[1]], [bx, b[1]], b];
}
function drawWire(ctx: CanvasRenderingContext2D, pts: XY[], period: number, offset: number, t: number, e: number, col: string, burst: number) {
  if (e <= 0.02) return;
  ctx.strokeStyle = `rgba(${PAPER},${0.2 * e})`;
  ctx.lineWidth = 1;
  ctx.beginPath();
  pts.forEach(([x, y], i) => (i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)));
  ctx.stroke();
  cap(ctx, pts[0][0], pts[0][1], e);
  cap(ctx, pts[pts.length - 1][0], pts[pts.length - 1][1], e);
  const lens: number[] = [];
  let total = 0;
  for (let i = 1; i < pts.length; i++) {
    const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
    lens.push(l);
    total += l;
  }
  const at = (u: number): XY => {
    let d = u * total;
    for (let i = 0; i < lens.length; i++) {
      if (d <= lens[i]) {
        const f = lens[i] ? d / lens[i] : 0;
        return [pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f];
      }
      d -= lens[i];
    }
    return pts[pts.length - 1];
  };
  const u = ((t / period + offset) % 1 + 1) % 1;
  for (let k = 3; k >= 0; k--) {
    const uu = u - k * 0.012;
    if (uu < 0) continue;
    const [x, y] = at(uu);
    point(ctx, x, y, k === 0 ? 2.4 : 1.4, e * (k === 0 ? 1 : 0.35 / k), col);
  }
  if (burst > 0.02) {
    const [x, y] = at(1 - burst);
    point(ctx, x, y, 3.2, burst * e, CORAL);
  }
}
function drawQuanta(ctx: CanvasRenderingContext2D, w: number, h: number, fx: number, fy: number, t: number, e: number, front: boolean) {
  const R = Math.min(w, h) * 0.22;
  const breathe = 1 + 0.012 * Math.sin(t * 0.5);
  ctx.lineWidth = 1;
  ctx.strokeStyle = `rgba(${PAPER},${(front ? 0.03 : 0.05) * e})`;
  for (let i = 1; i <= 6; i++) {
    if (front !== i >= 4) continue;
    const r = R * i * 0.5 * breathe;
    for (const [dx, dy] of [[0, -1], [0, 1], [-1, 0], [1, 0]] as XY[]) {
      ctx.beginPath();
      ctx.arc(fx + dx * r, fy + dy * r, r, 0, TAU);
      ctx.stroke();
    }
  }
  if (!front) {
    ctx.strokeStyle = `rgba(${PAPER},${0.07 * e})`;
    for (let i = 1; i <= 3; i++) {
      ctx.beginPath();
      ctx.arc(fx, fy, R * (0.6 + i * 0.55) * breathe, 0, TAU);
      ctx.stroke();
    }
    ctx.strokeStyle = `rgba(${PAPER},${0.08 * e})`;
    ctx.beginPath();
    ctx.moveTo(fx - R * 3, fy);
    ctx.lineTo(fx + R * 3, fy);
    ctx.moveTo(fx, 0);
    ctx.lineTo(fx, h * e);
    ctx.stroke();
  }
}

/* ---- each screen's wires, cross-faded through the transformation ---- */
/* the wires are the couplings: each runs between the two components a
   signal joins, and its pulse is that signal's own trigger */
function wiresFor(ctx: CanvasRenderingContext2D, k: number, F: Frame, T: XY, RO: XY, t: number, e: number, burst: number) {
  const A = F.anchors;
  const main = F.main;
  /* every wire runs between fixed points — the frames' edges, the tapes'
     ends, the readouts — never after a moving mark, so nothing jumps */
  const right: XY = [main.x1, (main.y0 + main.y1) * 0.5];
  const bottom: XY = [(main.x0 + main.x1) * 0.5, main.y1];
  const top: XY = [(main.x0 + main.x1) * 0.5, main.y0];
  const left: XY = [main.x0, (main.y0 + main.y1) * 0.5];
  const periodPulse = Math.max(burst, decay(bus.periodChangedAt, t, 2.4));
  const walkPulse = Math.max(burst, decay(bus.walkDoneAt, t, 2.4));
  const sweepPulse = Math.max(burst, decay(bus.pulseAt, t, 2.4));
  const flowPulse = Math.max(burst, decay(bus.flowAt, t, 2));
  if (k === 0) {
    /* sphere → strip → lattice → funnel, on the period */
    drawWire(ctx, [top, [top[0], T[1] + 30], [T[0] - 30, T[1] + 30], [T[0] - 30, T[1]], T], 4.1, 0.55, t, e, SKY, periodPulse);
    drawWire(ctx, [A.strip, [A.strip[0] - 30, A.strip[1]], [A.strip[0] - 30, top[1]], top], 3.4, 0.2, t, e, CORAL, periodPulse);
    drawWire(ctx, elbow(A.years, A.funnelFoot, 0.5), 2.8, 0.3, t, e, CORAL, periodPulse);
    drawWire(ctx, elbow(A.funnelTop, left, 0.45), 2.2, 0.3, t, e, MINT, flowPulse);
  } else if (k === 1) {
    /* network → chain; chain → readouts; network → halftone */
    const netCorner: XY = [A.netIn[0], A.netIn[1] - 40];
    drawWire(ctx, elbow(netCorner, left, 0.5), 1.8, 0.2, t, e, SKY, walkPulse);
    drawWire(ctx, [top, [top[0], T[1] + 30], [T[0] - 30, T[1] + 30], [T[0] - 30, T[1]], T], 3.6, 0.1, t, e, CORAL, walkPulse);
    drawWire(ctx, elbow(right, A.halftone, 0.3), 1.8, 0.5, t, e * 0.8, SKY, walkPulse);
    drawWire(ctx, elbow(bottom, RO, 0.2), 4.4, 0.7, t, e * 0.6, SKY, walkPulse);
  } else if (k === 3) {
    /* the figure's frame → tiles; its scales → readout */
    drawWire(ctx, [top, [top[0], T[1] + 30], [T[0] - 30, T[1] + 30], [T[0] - 30, T[1]], T], 6, 0.2, t, e * 0.7, SKY, burst);
    drawWire(ctx, elbow(A.wall, RO, 0.3), 7, 0.6, t, e * 0.6, SKY, burst);
  } else if (k === 2) {
    /* the map's frame → the geography tape → the time tape → tiles */
    drawWire(ctx, elbow(right, [A.regionTape[0], main.y0 + 20], 0.6), 3, 0.2, t, e, CORAL, periodPulse);
    drawWire(ctx, [[A.regionTape[0], main.y1 - 20], [A.regionTape[0], A.tapeR[1] + 40], [A.tapeR[0], A.tapeR[1] + 40], A.tapeR], 4.2, 0.4, t, e * 0.8, CORAL, periodPulse);
    drawWire(ctx, [A.tapeL, [A.tapeL[0], A.tapeL[1] + 50], [T[0] - 40, A.tapeL[1] + 50], [T[0] - 40, T[1]], T], 5, 0.6, t, e * 0.6, SKY, periodPulse);
    drawWire(ctx, elbow(top, RO, 0.35), 6, 0.8, t, e * 0.7, SKY, periodPulse);
  } else {
    /* the dial's frame → the wave; the frame → the loop; the wave → tiles; the loop → readout */
    drawWire(ctx, elbow(bottom, [A.wavePeak[0], A.wavePeak[1] - 30], 0.35), 1.6, 0.4, t, e, SKY, sweepPulse);
    drawWire(ctx, elbow([main.x0, main.y0 + 30], A.loop, 0.5), 2.2, 0.15, t, e * 0.8, SKY, sweepPulse);
    drawWire(ctx, [right, [right[0] + 40, right[1]], [right[0] + 40, T[1] + 30], [T[0] - 30, T[1] + 30], [T[0] - 30, T[1]], T], 5.4, 0.6, t, e * 0.8, CORAL, sweepPulse);
    drawWire(ctx, elbow(A.loop, RO, 0.9), 6.2, 0.85, t, e * 0.7, SKY, sweepPulse);
  }
}

/* ================= six reactive components =================
   Each is bound to another component's motion or to the scroll, so the
   page has more than one track of movement and exchanges trigger
   exchanges. Drawn with its screen's nearness; not part of the budget. */
const near = (s: number, k: number) => clamp01(1 - Math.abs(s - k) / 0.5);

/* Context · the PRISM: a triangle of concentric arcs and a beam; it fires
   (the arcs run outward) each time the network's walk completes */
function drawPrism(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, t: number, e: number) {
  if (e <= 0.02) return;
  const ax = x + w * 0.5;
  const ay = y + h * 0.08;
  const base = y + h * 0.92;
  const half = w * 0.46;
  ctx.strokeStyle = `rgba(${PAPER},${0.7 * e})`;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(ax, ay);
  ctx.lineTo(ax + half, base);
  ctx.lineTo(ax - half, base);
  ctx.closePath();
  ctx.stroke();
  const fire = clamp01((t - bus.walkDoneAt) / 4.2);
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(ax, ay);
  ctx.lineTo(ax + half, base);
  ctx.lineTo(ax - half, base);
  ctx.closePath();
  ctx.clip();
  for (let i = 0; i < 18; i++) {
    const u = ((i / 18) + fire) % 1;
    const r = u * (base - ay) * 1.05;
    ctx.strokeStyle = `rgba(${SKY},${(0.12 + 0.5 * (1 - u)) * e})`;
    ctx.lineWidth = 0.9;
    ctx.beginPath();
    ctx.arc(ax, base, r, Math.PI, TAU);
    ctx.stroke();
  }
  ctx.restore();
  glow(ctx, () => {
    ctx.beginPath();
    ctx.moveTo(ax - half, base);
    ctx.lineTo(ax + half, base);
    ctx.stroke();
  }, 0.8 * e, 1.2, SKY);
  glow(ctx, () => {
    ctx.beginPath();
    ctx.moveTo(ax, ay);
    ctx.lineTo(ax, base);
    ctx.stroke();
  }, 0.5 * e, 0.8, SKY);
  point(ctx, ax, ay - h * 0.06, 2.6, e * (0.4 + 0.6 * (1 - fire)), SKY);
  ctx.strokeStyle = `rgba(${CORAL},${0.7 * e})`;
  ctx.lineWidth = 1.2;
  ctx.beginPath();
  ctx.arc(ax, ay - h * 0.14, 4, 0, TAU);
  ctx.stroke();
}

/* Spacetime · the LEDGER of concentration and absence: six region rows
   by 23 period columns; a mark where records gather, an empty cell where
   they are absent; the bus's period column and the globe's lit region
   row read together */
function drawLedger(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, e: number) {
  if (e <= 0.02) return;
  const cw = w / 23;
  const rh = h / 6;
  for (let r = 0; r < 6; r++) {
    for (let c = 0; c < 23; c++) {
      const present = hash(r * 23 + c + 11) < 0.58;
      const onCol = c === bus.period;
      const onRow = r === bus.region;
      const cx = x + (c + 0.5) * cw;
      const cy = y + (r + 0.5) * rh;
      if (present) {
        const hgt = rh * (0.25 + 0.6 * hash(r * 31 + c * 7));
        ctx.fillStyle = onCol && onRow ? `rgba(${CORAL},${0.95 * e})` : onCol || onRow ? `rgba(${PAPER},${0.7 * e})` : `rgba(${PAPER},${0.35 * e})`;
        ctx.fillRect(cx - cw * 0.28, cy - hgt * 0.5, cw * 0.56, hgt);
      } else {
        ctx.strokeStyle = `rgba(${PAPER},${(onCol || onRow ? 0.45 : 0.18) * e})`;
        ctx.lineWidth = 0.8;
        ctx.strokeRect(cx - cw * 0.28, cy - rh * 0.14, cw * 0.56, rh * 0.28);
      }
    }
  }
  ctx.strokeStyle = `rgba(${PAPER},${0.45 * e})`;
  ctx.lineWidth = 1;
  ctx.strokeRect(x - 6, y - 6, w + 12, h + 12);
  ctx.strokeStyle = `rgba(${CORAL},${0.5 * e})`;
  ctx.strokeRect(x + bus.period * cw, y - 6, cw, h + 12);
}

/* Exploration · the OSCILLON: Laposky's ribbon — rings along a horizontal
   axis, sheared by the dial's head, drawn as sweeps */
function drawOscillon(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, head: number, t: number, e: number) {
  if (e <= 0.02) return;
  const cy = y + h * 0.5;
  const n = 40;
  for (let k = 0; k < n; k++) {
    const u = k / (n - 1);
    const cx = x + w * 0.1 + u * w * 0.8;
    const shear = Math.sin(u * TAU + head) * h * 0.22;
    const ry = h * 0.34 * (0.6 + 0.4 * Math.cos(u * Math.PI * 2 + t * 0.3));
    ctx.strokeStyle = `rgba(${PAPER},${(0.12 + 0.3 * Math.abs(Math.sin(u * Math.PI))) * e})`;
    ctx.lineWidth = 0.7;
    ctx.beginPath();
    ctx.ellipse(cx, cy + shear, w * 0.03, ry, 0.15 * Math.sin(head + u * 4), 0, TAU);
    ctx.stroke();
  }
  const hx = x + w * 0.1 + ((head / TAU) % 1) * w * 0.8;
  point(ctx, hx, cy + Math.sin(((head / TAU) % 1) * TAU + head) * h * 0.22, 2.6, e, SKY);
}

/* Exploration · the PULSES: rings emitted from the dial's satellite each
   time the sweep passes it; the wave answers with its bump */
function drawPulses(ctx: CanvasRenderingContext2D, sat: XY, t: number, e: number) {
  if (e <= 0.02) return;
  for (let k = 0; k < 4; k++) {
    const age = (t - bus.pulseAt) - k * 0.6;
    if (age < 0 || age > 3) continue;
    const u = age / 3;
    ctx.strokeStyle = `rgba(${SKY},${(1 - u) * 0.6 * e})`;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(sat[0], sat[1], 8 + u * 90, 0, TAU);
    ctx.stroke();
  }
}

let lastState = -1;
let changeAt = -10;
function burstAt(t: number, s: number) {
  const st = Math.round(s);
  if (st !== lastState) {
    lastState = st;
    changeAt = t;
  }
  return Math.max(0, 1 - (t - changeAt) / 2.4);
}
let YEARS: [number, number] = [1800, 2026];
export function setAxisYears(from: number, to: number) {
  YEARS = [from, to];
}

/* ================= the scene ================= */
export const sceneProgram: Program = (ctx, w, h, t, s, a) => {
  const e = ease(a);
  computeBus(t, s);
  /* the funnel delivers on its own beat, and the lattice's well answers */
  if (Math.floor(t / 5) !== Math.floor((t - 0.04) / 5)) bus.flowAt = t;
  const TB = tilesBox(w, h);
  const B0 = boxesFor(0, w, h);
  const k = Math.min(3, Math.max(0, Math.floor(s)));
  const f = smooth(s - k);
  const A = SCREENS[k](w, h, t);
  const Bf = f > 0 ? SCREENS[k + 1](w, h, t) : A;
  const F = blend(A, Bf, f);
  const burst = burstAt(t, s);
  const flow = Math.pow(Math.sin(f * Math.PI), 1.4);
  const centre: XY = [(F.main.x0 + F.main.x1) * 0.5, (F.main.y0 + F.main.y1) * 0.5];

  drawQuanta(ctx, w, h, centre[0], centre[1], t, e * (1 - near(s, 3)), false);
  drawTiles(ctx, TB.x, TB.y, TB.w, TB.h, t, e, burst);
  /* the reactive layer, each screen's own */
  const n1 = near(s, 1);
  const n2 = near(s, 2);
  const n4 = near(s, 4);
  if (n1 > 0.02) {
    drawPrism(ctx, w * 0.52, h * 0.7, w * 0.1, h * 0.2, t, e * n1);
  }
  if (n2 > 0.02) {
    drawLedger(ctx, w * 0.72, h * 0.74, w * 0.25, h * 0.18, e * n2);
  }
  if (n4 > 0.02) {
    drawOscillon(ctx, w * 0.58, h * 0.06, w * 0.36, h * 0.16, bus.sweep, t, e * n4);
    drawPulses(ctx, F.anchors.sat ?? [0, 0], t, e * n4);
  }
  drawFrame(ctx, F, e);
  drawTracking(ctx, F.main, (1 - flow) * e * (A.frame ?? 1) * (Bf.frame ?? 1));
  /* the years, on the first screen's axis */
  const near0 = clamp01(1 - s / 0.5);
  ctx.font = "500 17px Inter, ui-sans-serif, system-ui, sans-serif";
  ctx.textBaseline = "middle";
  if (near0 > 0.02) {
    const [ax, ay] = A.anchors.years;
    ctx.fillStyle = `rgba(${SAND},${0.9 * e * near0})`;
    ctx.textAlign = "right";
    ctx.fillText(String(YEARS[0]), ax - 14, ay);
    ctx.textAlign = "left";
    ctx.fillText(String(YEARS[1]), ax + B0.right.w * 0.4 + 14, ay);
  }
  /* and on Spacetime's time tape */
  const near2y = near(s, 2);
  if (near2y > 0.02) {
    const S2 = SCREENS[2](w, h, t).anchors;
    ctx.fillStyle = `rgba(${SAND},${0.9 * e * near2y})`;
    ctx.textAlign = "right";
    ctx.fillText(String(YEARS[0]), S2.tapeL[0] - 14, S2.tapeL[1]);
    ctx.textAlign = "left";
    ctx.fillText(String(YEARS[1]), S2.tapeR[0] + 14, S2.tapeR[1]);
  }
  /* the wires: this screen's, and the next's fading in */
  const T: XY = [TB.x - 12, TB.y + TB.h * 0.5];
  const RO: XY = [w * 0.47, TB.y + TB.h * 0.5];
  wiresFor(ctx, k, A, T, RO, t, e * (1 - f) * (1 - f), burst);
  if (f > 0) wiresFor(ctx, k + 1, Bf, T, RO, t, e * f * f, burst);
};

/* ---- the front layer, over the text ---- */
export const sceneFrontProgram: Program = (ctx, w, h, t, s, a) => {
  const e = ease(a);
  const k = Math.min(3, Math.max(0, Math.floor(s)));
  const f = smooth(s - k);
  const A = boxesFor(k, w, h).main;
  const Bx = boxesFor(k + 1, w, h).main;
  const cx = lerp(A.x + A.w * 0.5, Bx.x + Bx.w * 0.5, f);
  const cy = lerp(A.y + A.h * 0.5, Bx.y + Bx.h * 0.5, f);
  drawQuanta(ctx, w, h, cx, cy, t, e, true);
};
