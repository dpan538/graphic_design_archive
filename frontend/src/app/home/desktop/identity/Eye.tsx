"use client";

import { useEffect, useRef } from "react";
import styles from "../sections/IdentitySection.module.css";

/* Study II of the ellipsis — the eye (HOMEPAGE_IDENTITY_SEQUENCE_v1.md §F3):
   a halftone iris around a pupil, inside a halftone sclera, behind two
   LIDS. It arrives closed; the lids part once the row has centred it —
   scrubbed, so the film opens it at its own pace — then it looks about in
   saccades, blinks, and follows the pointer: the one study that looks back.

   Built for the compositor: every moving part is an HTML layer carrying a
   transform — the follow, the saccades, the two lids and their blink —
   over SVGs that never change and so are rasterised once. The lids are
   black plates whose edges are arcs of the eye's own circle: closed, the
   two arcs meet at the centre; each moved by the circle's radius they
   coincide with the circle and the eye is whole. No clip-path anywhere —
   the opening and the blink cost the compositor only. (The first cut
   opened an ellipse clip-path over the whole stack: a repaint of ~2,200
   marks on every frame of the opening, and the stutter the owner saw.) */

const S = 440;
const C = S / 2;
const r1 = (n: number) => Math.round(n * 10) / 10;
const polar = (r: number, a: number) => [r1(C + r * Math.cos(a)), r1(C + r * Math.sin(a))] as const;
function mulberry(seed: number) {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

type HDot = { x: number; y: number; r: number };
const IRIS: HDot[] = [];
const SCLERA: HDot[] = [];
const PUPIL_RIM: HDot[] = [];
/* iris 52–118, pupil 40, in a sclera that runs out to 206 — the white of
   the eye is what says "eye" */
const IRIS_IN = 52;
const IRIS_OUT = 118;
const PUPIL = 40;
{
  const rand = mulberry(0x77c1);
  for (let k = 0; k < 60; k++) {
    const a0 = (k / 60) * Math.PI * 2;
    const gain = 0.5 + rand();
    for (let r = IRIS_IN; r < IRIS_OUT; r += 4.6) {
      const jitter = (rand() - 0.5) * 0.03;
      const band = 0.5 + 0.5 * Math.cos(((r - IRIS_IN) / (IRIS_OUT - IRIS_IN)) * Math.PI * 2.2);
      const size = (0.45 + 1.45 * band) * (0.6 + 0.4 * gain);
      const [x, y] = polar(r, a0 + jitter);
      IRIS.push({ x, y, r: r1(size) });
    }
  }
  for (let i = 0; i < 120; i++) {
    const [x, y] = polar(IRIS_OUT + 4, (i / 120) * Math.PI * 2);
    IRIS.push({ x, y, r: 1.7 });
  }
  for (let i = 0; i < 48; i++) {
    const [x, y] = polar(PUPIL + 4, (i / 48) * Math.PI * 2);
    PUPIL_RIM.push({ x, y, r: 1.3 });
  }
  /* sclera: a halftone from the iris out to the rim, densest at the rim */
  for (let k = 0; k < 11; k++) {
    const r = 140 + k * 6.2;
    const n = Math.round((Math.PI * 2 * r) / 8.4);
    for (let i = 0; i < n; i++) {
      const [x, y] = polar(r, ((i + (k % 2) * 0.5) / n) * Math.PI * 2);
      SCLERA.push({ x, y, r: r1(0.6 + k * 0.22) });
    }
  }
}

/* The halftones are shipped as two IMAGES (SVG data URIs), not inline SVG.
   Inline, their ~2,200 elements were recomputed on every scroll frame of
   the section — an inherited custom property changes on every frame — and
   painted again at each act change; an image inherits nothing and is
   rasterised once. */
const PAPER = "#fbfaf7";
const BLACK = "#0a0a0c";
const svgSrc = (inner: string) =>
  `data:image/svg+xml;charset=utf-8,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${S} ${S}">${inner}</svg>`)}`;
const circles = (dots: HDot[]) => dots.map((d) => `<circle cx="${d.x}" cy="${d.y}" r="${d.r}"/>`).join("");
const SCLERA_SRC = svgSrc(`<g fill="${PAPER}" fill-opacity="0.55">${circles(SCLERA)}</g>`);
const IRIS_SRC = svgSrc(
  `<g fill="${PAPER}">${circles(IRIS)}</g><circle cx="${C}" cy="${C}" r="${PUPIL}" fill="${BLACK}"/><g fill="${PAPER}">${circles(PUPIL_RIM)}</g><circle cx="${C - 15}" cy="${C - 17}" r="5.5" fill="${PAPER}" fill-opacity="0.9"/>`,
);

/* The lids. Each is the stage's rectangle less a half-disc of the eye's
   radius: the upper lid's edge is the upper half of a circle centred a
   radius BELOW the centre, so closed it arches up to the centre point;
   moved up by one radius (48.64% of the stage) it becomes the upper half
   of the eye's own circle. The lower lid mirrors it. Between them, half
   open, is an almond. The rectangles run well past the stage so a blink
   at any opening still covers. */
const LID_R = 214;
const LID_UPPER = `M0 -700H${S}V${C + LID_R}H${C + LID_R}A${LID_R} ${LID_R} 0 0 0 ${C - LID_R} ${C + LID_R}H0Z`;
const LID_LOWER = `M0 ${S + 700}H${S}V${C - LID_R}H${C + LID_R}A${LID_R} ${LID_R} 0 0 1 ${C - LID_R} ${C - LID_R}H0Z`;

export default function Eye() {
  const follow = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = follow.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let visible = false;
    let raf = 0;
    let px = 0;
    let py = 0;
    let cx = 0;
    let cy = 0;
    let measured = 0;
    const apply = () => {
      raf = 0;
      /* the eye's centre is re-measured at most four times a second — a
         layout read on every pointer move, with the film dirtying style on
         every frame, forced a synchronous layout per move */
      const now = performance.now();
      if (now - measured > 250) {
        measured = now;
        const b = el.getBoundingClientRect();
        cx = b.left + b.width / 2;
        cy = b.top + b.height / 2;
      }
      const dx = (px - cx) / (window.innerWidth * 0.5);
      const dy = (py - cy) / (window.innerHeight * 0.5);
      const m = Math.hypot(dx, dy);
      const k = Math.min(1, m) / (m || 1);
      /* the pupil may travel a third of the way to the rim */
      el.style.transform = `translate(${(dx * k * 30).toFixed(1)}px, ${(dy * k * 22).toFixed(1)}px)`;
    };
    const onMove = (e: PointerEvent) => {
      if (!visible) return;
      px = e.clientX;
      py = e.clientY;
      if (!raf) raf = requestAnimationFrame(apply);
    };
    const io = new IntersectionObserver(
      ([en]) => {
        visible = en.isIntersecting;
        measured = 0;
        if (!visible) {
          cancelAnimationFrame(raf);
          raf = 0;
          el.style.transform = "translate(0px, 0px)";
        }
      },
      { threshold: 0.4 },
    );
    io.observe(el);
    window.addEventListener("pointermove", onMove, { passive: true });
    return () => {
      io.disconnect();
      window.removeEventListener("pointermove", onMove);
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <div className={styles.eyeStage} aria-hidden="true">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={SCLERA_SRC} alt="" draggable={false} className={styles.layerSvg} />
      <div ref={follow} className={`${styles.layer} ${styles.eyeFollow}`}>
        <div className={`${styles.layer} ${styles.eyeLook}`}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={IRIS_SRC} alt="" draggable={false} className={styles.layerSvg} />
        </div>
      </div>
      {/* the lids: the outer layer is the opening (scrubbed), the inner
          the blink (its own clock) */}
      <div className={`${styles.layer} ${styles.lidUpper}`}>
        <div className={`${styles.layer} ${styles.lidBlinkUpper}`}>
          <svg viewBox={`0 0 ${S} ${S}`} className={`${styles.layerSvg} ${styles.lidPlate}`}>
            <path d={LID_UPPER} />
          </svg>
        </div>
      </div>
      <div className={`${styles.layer} ${styles.lidLower}`}>
        <div className={`${styles.layer} ${styles.lidBlinkLower}`}>
          <svg viewBox={`0 0 ${S} ${S}`} className={`${styles.layerSvg} ${styles.lidPlate}`}>
            <path d={LID_LOWER} />
          </svg>
        </div>
      </div>
      {/* the seam of the closed lids — a hairline across the middle that
          goes as they part, so the closed eye reads as closed, not empty */}
      <span className={styles.lidSeam} />
      {/* the lid line: the edge of the eye, drawn, so the lids read as
          lids even when fully open */}
      <svg viewBox={`0 0 ${S} ${S}`} className={`${styles.layerSvg} ${styles.lidLine}`}>
        <ellipse cx={C} cy={C} rx={LID_R} ry={LID_R} pathLength={1} />
      </svg>
    </div>
  );
}
