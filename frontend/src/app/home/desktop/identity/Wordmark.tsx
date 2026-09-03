"use client";

import { useLayoutEffect, useRef } from "react";
import { gsap } from "gsap";
import { MorphSVGPlugin } from "gsap/MorphSVGPlugin";
import glyphs from "@/data/identity-glyphs.json";
import styles from "../sections/IdentitySection.module.css";

/* The wordmark's entrance (HOMEPAGE_IDENTITY_SEQUENCE_v1.md §F4a):
   from one point, a line draws the outlines of M · G · D · A in an italic
   serif; they fill, stand upright, shed their serifs into the sans, thicken,
   pass into the site's own face light, then heavy. Seven faces, six morphs,
   nine seconds, no bounce anywhere.
   Every frame is a real letterform: the outlines come from the build script
   and MorphSVG interpolates outline → outline.

   The rest state, rendered on the server, is the finished wordmark. The
   timeline only replays the entrance when the act is entered, so a frame
   where it never ran still shows MGDA. */

type Face = { name: string; width: number; ink: [number, number]; capHeight: number; glyphs: { d: string; x: number; advance: number }[] };
type FaceKey = "serifItalic" | "serif" | "sans" | "sansBold" | "seed400" | "seed700" | "seed";
/* the JSON importer types `ink` as number[]; the script writes a pair */
const FACES = (glyphs as unknown as { wordmark: Record<FaceKey, Face> }).wordmark;
/* the road, after the drawn italic serif; each step's start (s) and length */
const ROAD: { key: FaceKey; at: number; dur: number; ease: string }[] = [
  { key: "serif", at: 2.3, dur: 0.9, ease: "power2.inOut" },
  { key: "sans", at: 3.4, dur: 1.0, ease: "power2.inOut" },
  { key: "sansBold", at: 4.6, dur: 0.8, ease: "power2.inOut" },
  { key: "seed400", at: 5.6, dur: 0.9, ease: "power2.inOut" },
  { key: "seed700", at: 6.7, dur: 0.8, ease: "power2.inOut" },
  { key: "seed", at: 7.7, dur: 1.0, ease: "power3.inOut" },
];
/* Each glyph sits at its own advance; the word is centred on its INK, not
   its advances, so the wordmark and the line beneath share one axis. */
const gx = (face: Face, i: number) => face.glyphs[i].x - (face.ink[0] + face.ink[1]) / 2;

const EM = 1000;

export default function Wordmark({ play, reduced }: { play: boolean; reduced: boolean }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const seed = FACES.seed;

  /* A layout effect, not an effect: the act flips the block visible in the
     same commit, and an effect would let one frame paint the finished
     wordmark before the timeline took it back to the point — a flash. The
     initial state is applied synchronously here, before paint. */
  useLayoutEffect(() => {
    if (!play || reduced) return;
    const svg = svgRef.current;
    if (!svg) return;
    gsap.registerPlugin(MorphSVGPlugin);
    const paths = Array.from(svg.querySelectorAll<SVGPathElement>("[data-glyph]"));
    const groups = Array.from(svg.querySelectorAll<SVGGElement>("[data-glyph-group]"));
    const dot = svg.querySelector<SVGCircleElement>("[data-dot]");
    const word = svg.querySelector<SVGGElement>("[data-word]");
    if (!dot || !word) return;

    const first = FACES.serifItalic;
    /* start: nothing but the point — applied now, before this frame paints */
    gsap.set(paths, {
      attr: { d: (i: number) => first.glyphs[i].d },
      fillOpacity: 0,
      strokeOpacity: 1,
      strokeWidth: 7,
      strokeDasharray: 1,
      strokeDashoffset: 1,
    });
    gsap.set(groups, { x: (i: number) => gx(first, i) });
    gsap.set(dot, { attr: { r: 0 }, opacity: 1 });
    gsap.set(word, { scale: 1, transformOrigin: "50% 50%" });
    const tl = gsap.timeline({ defaults: { overwrite: "auto" } });

    /* 0.0–0.6 the point arrives; 0.6–1.0 held black */
    tl.to(dot, { attr: { r: 12 }, duration: 0.6, ease: "power2.inOut" }, 0);
    /* 1.0–2.2 the line draws the italic serif outlines, left to right */
    tl.to(dot, { attr: { r: 0 }, duration: 0.4, ease: "power2.in" }, 1.0);
    tl.to(paths, { strokeDashoffset: 0, duration: 1.1, ease: "power2.inOut", stagger: 0.22 }, 1.0);
    tl.to(paths, { fillOpacity: 1, strokeWidth: 0, duration: 0.6, ease: "power2.inOut", stagger: 0.22 }, 1.7);
    /* the road: italic → roman → sans → bold sans → the face, light → heavy */
    for (const step of ROAD) {
      const face = FACES[step.key];
      paths.forEach((path, i) => {
        tl.to(path, { morphSVG: { shape: face.glyphs[i].d, shapeIndex: "auto" }, duration: step.dur, ease: step.ease }, step.at + i * 0.09);
      });
      tl.to(groups, { x: (i: number) => gx(face, i), duration: step.dur, ease: step.ease, stagger: 0.09 }, step.at);
    }
    /* the weight settles — a slow, small press, not a bounce */
    tl.fromTo(word, { scale: 1.018 }, { scale: 1, duration: 1.2, ease: "power3.out" }, 8.3);

    return () => {
      tl.kill();
      /* leave the rest state, whatever was interrupted */
      gsap.set(paths, { attr: { d: (i: number) => seed.glyphs[i].d }, fillOpacity: 1, strokeWidth: 0, strokeDashoffset: 0 });
      gsap.set(groups, { x: (i: number) => gx(seed, i) });
      gsap.set(dot, { attr: { r: 0 } });
      gsap.set(word, { scale: 1 });
    };
  }, [play, reduced, seed]);

  return (
    <svg
      ref={svgRef}
      className={styles.wordmark}
      viewBox={`-2100 -${EM} 4200 ${EM + 120}`}
      aria-label="MGDA"
      role="img"
    >
      <g data-word>
        {seed.glyphs.map((g, i) => (
          <g key={i} data-glyph-group transform={`translate(${gx(seed, i)} 0)`}>
            <path data-glyph d={g.d} className={styles.wordGlyph} pathLength={1} />
          </g>
        ))}
      </g>
      <circle data-dot cx={0} cy={-seed.capHeight / 2} r={0} className={styles.wordDot} />
    </svg>
  );
}
