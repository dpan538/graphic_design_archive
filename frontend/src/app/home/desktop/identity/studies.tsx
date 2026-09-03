import HatchSphere from "./HatchSphere";
import Eye from "./Eye";
import styles from "../sections/IdentitySection.module.css";

/* The readings of the circle (HOMEPAGE_IDENTITY_SEQUENCE_v1.md §F3) — three
   now: the owner cut the strokes, the contours and the spiral for a
   tempo and a frame budget that hold.
   Each is a 440-unit stage. Geometry is computed once here, rounded so the
   server and the client agree. Every moving part is an HTML LAYER carrying
   a transform over an SVG that never changes — so each SVG is rasterised
   once and the idle motion costs the compositor only. (Animating a <g>
   inside an SVG re-rasterised the whole SVG every frame: with ~5,000 marks
   across the row that was the jank.) III is a canvas. Six languages that must not resemble one
   another: a family of loops, radial strokes, nested contours, a
   phyllotaxis of dots, a halftone eye that looks about, an engraver's
   hatching. */

const S = 440;
const C = S / 2;
const r1 = (n: number) => Math.round(n * 10) / 10;

function mulberry(seed: number) {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const polar = (r: number, a: number) => [r1(C + r * Math.cos(a)), r1(C + r * Math.sin(a))] as const;

/* ---- I · the line: a family of loops sharing a centre, and a stack ---- */
const LOOP_N = 36;
const LOOPS = Array.from({ length: LOOP_N }, (_, i) => r1((i * 180) / LOOP_N));
const NEST = Array.from({ length: 13 }, (_, i) => r1(22 + (i * (188 - 22)) / 12));
/* a second, narrower family turned a quarter, so the figure reads as a
   lens inside a lens — the hourglass of the reference */
const LOOPS2 = Array.from({ length: 18 }, (_, i) => r1(90 + (i * 180) / 18));

export function StudyLoops() {
  return (
    <div className={styles.stack} aria-hidden="true">
      <svg viewBox={`0 0 ${S} ${S}`} className={styles.layerSvg}>
        <circle className={styles.ringBase} cx={C} cy={C} r={196} pathLength={1} />
      </svg>
      <div className={`${styles.layer} ${styles.spinSlow}`}>
        <svg viewBox={`0 0 ${S} ${S}`} className={styles.layerSvg}>
          {LOOPS.map((a, i) => (
            <ellipse key={a} className={styles.loop} cx={C} cy={C} rx={190} ry={112} transform={`rotate(${a} ${C} ${C})`} pathLength={1} style={{ ["--i" as string]: i }} />
          ))}
        </svg>
      </div>
      <div className={`${styles.layer} ${styles.spinSlowReverse}`}>
        <svg viewBox={`0 0 ${S} ${S}`} className={styles.layerSvg}>
          {LOOPS2.map((a, i) => (
            <ellipse key={a} className={styles.loop} cx={C} cy={C} rx={196} ry={58} transform={`rotate(${a} ${C} ${C})`} pathLength={1} style={{ ["--i" as string]: i + LOOP_N }} />
          ))}
        </svg>
      </div>
      <div className={`${styles.layer} ${styles.precess}`}>
        <svg viewBox={`0 0 ${S} ${S}`} className={styles.layerSvg}>
          {NEST.map((rx, i) => (
            <ellipse key={rx} className={styles.loop} cx={C} cy={C} rx={rx} ry={150} pathLength={1} style={{ ["--i" as string]: i + LOOP_N + 18 }} />
          ))}
        </svg>
      </div>
    </div>
  );
}

/* ---- V · the eye — a client component of its own: it follows the
   pointer (identity/Eye.tsx) ---- */
export function StudyEye() {
  return <Eye />;
}

/* ---- VI · the engraving ---- */
export function StudyEngraving() {
  return <HatchSphere className={styles.studyCanvas} />;
}

export const STUDIES = [
  { id: "line", name: "I · the line", Component: StudyLoops },
  { id: "eye", name: "II · the eye", Component: StudyEye },
  { id: "engraving", name: "III · the engraving", Component: StudyEngraving },
] as const;
