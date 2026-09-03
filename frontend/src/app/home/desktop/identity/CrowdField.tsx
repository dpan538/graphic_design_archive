"use client";

import { useEffect, useRef } from "react";
import styles from "../sections/IdentitySection.module.css";

/* The field, then the crowd (HOMEPAGE_IDENTITY_SEQUENCE_v1.md §F): 52 × 26
   marks (1,352) whose sizes carry two crossed waves and a ring. Each
   arrives from beyond its slot, passing through its own hue on the way
   and landing white; then it is a PERSON — the Tokyo poster's pair, a
   white head over a coloured body — and the crowd runs for the edges,
   each on their own beat. Scrubbed on the section's progress like
   everything else.

   Drawn OFF the main thread. As an SVG of 2,704 circles with per-mark
   custom properties, every scroll frame recomputed the style of the
   whole field, re-laid it out and repainted it — 15–25 ms, the jank the
   owner saw. Now the page's canvas only presents ImageBitmaps that a
   Worker draws into an OffscreenCanvas from the progress value it is
   sent; the main thread posts one number per frame. Where OffscreenCanvas
   is missing the same program draws straight into the canvas. */

/* the program: geometry once, then a frame for any progress. It refers to
   nothing outside itself — it is shipped to the Worker as source text. */
function crowdProgram(ctx: CanvasRenderingContext2D | OffscreenCanvasRenderingContext2D, dpr: number) {
  const COLS = 52;
  const ROWS = 26;
  const W = 1000;
  const H = 620;
  const TAU = Math.PI * 2;
  /* the site's own spot colours (globals.css): blue, red, yellow, green,
     teal, sky, coral, pink — the bodies of the crowd, and the hue each mark
     passes through in flight */
  const BODIES = ["#2743d6", "#e8492b", "#f6c63c", "#3da35d", "#1f9b9b", "#4fa8de", "#f0876a", "#ec7bab"];
  const PAPER = [251, 250, 247];
  const clamp = (v: number) => (v < 0 ? 0 : v > 1 ? 1 : v);
  const hex = (s: string) => [parseInt(s.slice(1, 3), 16), parseInt(s.slice(3, 5), 16), parseInt(s.slice(5, 7), 16)];
  const bodyRgb = BODIES.map(hex);

  type Mark = { x: number; y: number; ox: number; oy: number; r: number; k: number; d: number; rx: number; ry: number; lead: number; hue: number[]; body: number[] };
  const marks: Mark[] = [];
  for (let i = 0; i < COLS * ROWS; i++) {
    const col = i % COLS;
    const row = Math.floor(i / COLS);
    const dx = (col - (COLS - 1) / 2) / ((COLS - 1) / 2);
    const dy = (row - (ROWS - 1) / 2) / ((ROWS - 1) / 2);
    const wave = 0.5 + 0.25 * Math.sin(dx * 7.3 + dy * 2.1) + 0.25 * Math.cos(dx * 2.4 - dy * 6.7 + 0.8);
    const ring = 0.5 + 0.5 * Math.cos(Math.sqrt(dx * dx * 1.6 + dy * dy) * 9.5);
    const k = Math.min(1, 0.15 + 0.55 * wave + 0.3 * ring);
    const h = ((i * 2654435761) >>> 0) % 1000;
    const x = W / 2 + dx * (W / 2 - 16) + (row % 2) * 4;
    const y = H / 2 + dy * (H / 2 - 16);
    /* where this person runs: away from the centre, with a little of their
       own heading, far enough to leave the screen */
    const ang = Math.atan2(y - H / 2, (x - W / 2) * 0.62) + ((h % 200) / 200 - 0.5) * 0.5;
    const dist = 900 + (h % 400);
    marks.push({
      x,
      y,
      ox: dx * 140,
      oy: dy * 90,
      r: 0.9 + 2.1 * k,
      k,
      d: Math.min(Math.sqrt(dx * dx + dy * dy) / Math.SQRT2, 1),
      rx: Math.cos(ang) * dist,
      ry: Math.sin(ang) * dist,
      lead: (h % 100) / 100,
      hue: bodyRgb[Math.floor(((dx * 0.5 + dy * 0.35 + 1) / 2) * 7.999 + (h % 3) * 0.34) % bodyRgb.length],
      body: bodyRgb[h % bodyRgb.length],
    });
  }

  /* the field sits in its box the way the SVG did: 1000 × 620, meet, centred */
  let s = 1;
  let tx = 0;
  let ty = 0;
  let bw = 0;
  let bh = 0;
  const size = (w: number, h: number) => {
    bw = w;
    bh = h;
    s = Math.min(w / W, h / H);
    tx = (w - W * s) / 2;
    ty = (h - H * s) / 2;
  };
  /* the figure — the field's one gesture: the first time the field comes
     to rest an EYE opens in it, drawn in negative AND positive at once. The
     marks inside an almond shrink away (the negative); along the almond's
     edge the marks swell and brighten into the lids' line, and in the
     pupil they stay large and bright, with a faint iris ring between (the
     positive). It glances to the side, and closes; the field is whole
     again. On its own clock, 2.8 s, once per visit (the page holds for it:
     HomeDesktop's FIELD_BEAT). */
  const FIG_MS = 2800;
  const FIG_CX = W / 2;
  const FIG_CY = H / 2;
  const FIG_A = 230;
  const FIG_H = 130;
  const FIG_P = 56;
  let figStart = -1;
  let figPlayed = false;
  const easeOut = (t: number) => 1 - (1 - t) * (1 - t);
  const smooth = (t: number) => t * t * (3 - 2 * t);

  /* returns whether the figure is live — the caller keeps drawing while it is */
  const draw = (p: number, now: number): boolean => {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, bw, bh);
    /* the beats, as in the stylesheet: the marks fly in (0.605–0.682), the
       field rests (the blink, at 0.685), the bodies come up (0.69–0.72),
       everyone runs (0.72–0.776) */
    const gridIn = clamp((p - 0.605) * 13);
    if (gridIn <= 0) {
      figPlayed = false;
      figStart = -1;
      return false;
    }
    const crowd = clamp((p - 0.69) * 33);
    const run = clamp((p - 0.72) * 18);
    if (gridIn < 0.5) {
      figPlayed = false;
      figStart = -1;
    } else if (!figPlayed && gridIn >= 1 && crowd < 0.05) {
      figPlayed = true;
      figStart = now;
    }
    const ft = figStart >= 0 ? (now - figStart) / FIG_MS : 2;
    let lid = 0;
    let glance = 0;
    if (ft < 1) {
      if (ft < 0.28) lid = easeOut(ft / 0.28);
      else if (ft < 0.68) lid = 1;
      else if (ft < 0.92) lid = 1 - smooth((ft - 0.68) / 0.24);
      glance = ft > 0.42 && ft < 0.68 ? smooth(clamp((ft - 0.42) / 0.1)) : 0;
    }
    const figure = lid > 0.001 && crowd < 0.5;
    const pupilX = FIG_CX + glance * 26;
    ctx.setTransform(dpr * s, 0, 0, dpr * s, dpr * tx, dpr * ty);
    for (let i = 0; i < marks.length; i++) {
      const m = marks[i];
      const dotEnter = clamp(gridIn * 1.75 - m.d * 0.75);
      if (dotEnter <= 0) continue;
      const back = 1 - dotEnter;
      const flight = 4 * dotEnter * back;
      const go = clamp(run * 1.6 - m.lead * 0.6);
      const goE = go * go * go;
      const op = dotEnter * (1 - go * 0.85);
      if (op <= 0.004) continue;
      const x = m.x + back * m.ox + goE * m.rx;
      const y = m.y + back * m.oy + goE * m.ry;
      if (crowd > 0) {
        const a = op * crowd * (0.55 + 0.45 * m.k);
        ctx.fillStyle = `rgba(${m.body[0]},${m.body[1]},${m.body[2]},${a.toFixed(3)})`;
        ctx.beginPath();
        ctx.arc(x, y + m.r * 2.3 - (1 - crowd) * 6, m.r * 1.15, 0, TAU);
        ctx.fill();
      }
      let rMul = 1;
      let lift = 0;
      if (figure) {
        const u = (m.x - FIG_CX) / FIG_A;
        if (u > -1.15 && u < 1.15) {
          const ry = FIG_H * lid * Math.max(0, 1 - u * u);
          const dy = Math.abs(m.y - FIG_CY);
          const hole = clamp((ry - dy) / 14);
          /* the lids' edge: a band of swollen marks either side of the almond's
             boundary, only where the almond has some height */
          const rim = ry > 8 ? clamp(1 - Math.abs(dy - ry) / 20) : 0;
          if (hole > 0) {
            const pd = Math.hypot(m.x - pupilX, m.y - FIG_CY);
            const pupil = clamp((FIG_P - pd) / 14) * hole;
            const iris = clamp((FIG_P + 46 - pd) / 14) * clamp((pd - FIG_P) / 14) * hole;
            rMul = 1 - hole + pupil * 1.45 + iris * 0.5;
            lift = pupil;
          }
          const outside = 1 - hole;
          rMul += rim * outside * 0.9;
          lift = Math.max(lift, rim * outside);
        }
      }
      const rr = m.r * rMul;
      if (rr < 0.05) continue;
      const a = Math.min(1, op * (0.45 + 0.55 * m.k) * (1 - lift) + lift);
      const r = Math.round(PAPER[0] + (m.hue[0] - PAPER[0]) * flight);
      const g = Math.round(PAPER[1] + (m.hue[1] - PAPER[1]) * flight);
      const b = Math.round(PAPER[2] + (m.hue[2] - PAPER[2]) * flight);
      ctx.fillStyle = `rgba(${r},${g},${b},${a.toFixed(3)})`;
      ctx.beginPath();
      ctx.arc(x, y, rr, 0, TAU);
      ctx.fill();
    }
    return ft < 1;
  };
  return { size, draw };
}

/* the Worker: the program, a canvas the size it is told, and one frame per
   progress value — coalesced, so a burst of values draws once */
const workerSource = () => `"use strict";
const program = ${crowdProgram.toString()};
let canvas = null, api = null, latest = null, scheduled = false;
const flush = () => {
  scheduled = false;
  if (!api || latest === null) return;
  const live = api.draw(latest, performance.now());
  const bitmap = canvas.transferToImageBitmap();
  self.postMessage(bitmap, [bitmap]);
  if (live) {
    scheduled = true;
    setTimeout(flush, 33);
  }
};
const schedule = () => {
  if (scheduled || !api) return;
  scheduled = true;
  setTimeout(flush, 0);
};
self.onmessage = (e) => {
  const m = e.data;
  if (m.type === "size") {
    canvas = new OffscreenCanvas(Math.max(1, Math.round(m.w * m.dpr)), Math.max(1, Math.round(m.h * m.dpr)));
    api = program(canvas.getContext("2d"), m.dpr);
    api.size(m.w, m.h);
    schedule();
  } else if (m.type === "p") {
    latest = m.p;
    schedule();
  }
};
`;

type Props = {
  /* the section's local progress, written by HomeDesktop every frame */
  progress: { current: number };
  /* only the act the field lives in runs the loop */
  active: boolean;
  reduced: boolean;
};

export default function CrowdField({ progress, active, reduced }: Props) {
  const ref = useRef<HTMLCanvasElement>(null);
  const post = useRef<(p: number) => void>(() => {});

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || reduced) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    let dispose = () => {};
    let resize = (w: number, h: number) => {
      void w;
      void h;
    };
    const presenter =
      typeof OffscreenCanvas !== "undefined" && typeof Worker !== "undefined" ? canvas.getContext("bitmaprenderer") : null;
    if (presenter) {
      const url = URL.createObjectURL(new Blob([workerSource()], { type: "text/javascript" }));
      const worker = new Worker(url);
      worker.onmessage = (e: MessageEvent<ImageBitmap>) => presenter.transferFromImageBitmap(e.data);
      resize = (w, h) => worker.postMessage({ type: "size", w, h, dpr });
      post.current = (p) => worker.postMessage({ type: "p", p });
      dispose = () => {
        worker.terminate();
        URL.revokeObjectURL(url);
      };
    } else {
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      const api = crowdProgram(ctx, dpr);
      let last = 0;
      let raf = 0;
      const step = () => {
        raf = 0;
        if (api.draw(last, performance.now())) raf = requestAnimationFrame(step);
      };
      resize = (w, h) => {
        canvas.width = Math.round(w * dpr);
        canvas.height = Math.round(h * dpr);
        api.size(w, h);
        step();
      };
      post.current = (p) => {
        last = p;
        if (!raf) step();
      };
      dispose = () => cancelAnimationFrame(raf);
    }
    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      if (width > 0 && height > 0) resize(width, height);
    });
    ro.observe(canvas);
    if (process.env.NODE_ENV !== "production") {
      (window as unknown as { __mgdaCrowd?: { draw: (p: number) => void } }).__mgdaCrowd = { draw: (p) => post.current(p) };
    }
    return () => {
      ro.disconnect();
      post.current = () => {};
      dispose();
    };
  }, [reduced]);

  useEffect(() => {
    if (!active || reduced) return;
    let raf = 0;
    let last = -1;
    const tick = () => {
      const p = progress.current;
      if (p !== last) {
        last = p;
        post.current(p);
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [active, reduced, progress]);

  return <canvas ref={ref} className={styles.field} aria-hidden="true" />;
}
