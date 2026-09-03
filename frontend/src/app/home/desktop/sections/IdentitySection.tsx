import type { CSSProperties } from "react";
import {
  GALLERY_CARDS,
  IDENTITY_HEADLINE_ACCENT,
  IDENTITY_HEADLINE_LEAD,
  IDENTITY_P1,
  IDENTITY_P2,
  IDENTITY_TAGLINE,
  IDENTITY_TAGLINE_SETTLED,
} from "../../lib/content";
import glyphs from "@/data/identity-glyphs.json";
import { STUDIES } from "../identity/studies";
import CrowdField from "../identity/CrowdField";
import Wordmark from "../identity/Wordmark";
import styles from "./IdentitySection.module.css";

/* 01 · Identity — HOMEPAGE_IDENTITY_SEQUENCE_v1.md §F (v2.1).

   A short film in seven acts. Scroll turns the pages — the gallery's
   travel, the frames' flight, the studies' arrival and pan, the sentence's
   drawing, the field's bloom, the cut to black — and inside every page
   something moves on its own: each circle study's idle loop, the merge,
   the wordmark's serif → sans → bold entrance, the stamps.

   The rule from the first build still holds: visibility is declarative
   (scrubbed from --local-progress or gated on [data-act]); keyframes and
   the wordmark timeline only decide HOW something enters. */

const cssVars = (o: Record<string, number | string>) => o as CSSProperties;
const round2 = (n: number) => Math.round(n * 100) / 100;

/* ---- the field, then the crowd: identity/CrowdField.tsx (a Worker draws
   it; the DOM holds one canvas) ---- */
const RULES = Array.from({ length: 44 }, (_, i) => i);

/* ---- the frames that fly off the gallery and merge into the ring ---- */
const FRAMES = GALLERY_CARDS.slice(0, 8).map((card, i) => {
  const [w, h] = card.ratio.split("/").map((s) => parseFloat(s));
  const fh = 150;
  return { i, fx: round2((i / 7 - 0.5) * 68), fy: round2(-56 - (i % 3) * 6), fw: round2((fh * w) / h), fh };
});

/* ---- the sentence, as outlines from the build script ---- */
type Line = { text: string; width: number; glyphs: { ch: string; x: number; d: string }[] };
const BRIDGE = (glyphs as { bridge: Line }).bridge;
const scatter = BRIDGE.glyphs.map((_, i, a) => {
  const angle = (i / a.length) * Math.PI * 2 + (i % 3) * 0.4;
  const radius = 900 + ((i * 53) % 700);
  return { dx: round2(Math.cos(angle) * radius), dy: round2(Math.sin(angle) * radius * 0.62) };
});

type Props = {
  act: number;
  reducedMotion: boolean;
  /* the section's local progress, written every frame by HomeDesktop —
     read by the field's canvas, which cannot be scrubbed from CSS */
  progress: { current: number };
};

export default function IdentitySection({ act, reducedMotion, progress }: Props) {
  const firstWords = IDENTITY_TAGLINE.split(" ");
  const settledWords = IDENTITY_TAGLINE_SETTLED.split(" ");

  return (
    <div className={styles.wrap} data-act={act} data-reduced={reducedMotion || undefined}>
      {/* ---- Act I · scroll layer ---- */}
      <div className={styles.scrollLayer}>
        <div className={styles.headerRegion}>
          <h2 className={styles.headline}>
            {IDENTITY_HEADLINE_LEAD}
            <em className={styles.headlineAccent}>{IDENTITY_HEADLINE_ACCENT}</em>
          </h2>
          <div className={styles.copy}>
            <p className={styles.para}>{IDENTITY_P1}</p>
            <p className={styles.para}>{IDENTITY_P2}</p>
          </div>
        </div>

        {/* A collection grid the way a museum sets one: plate on the ground,
            caption beneath, rows broken by real proportions. Every plate is
            empty; the reader finds that themselves. */}
        <div className={styles.gallery} aria-hidden="true">
          {GALLERY_CARDS.map((card, i) => (
            <figure key={i} className={styles.card} style={cssVars({ "--i": i })}>
              <div className={styles.plateBand}>
                <div className={styles.plate} style={cssVars({ "--ratio": card.ratio })}>
                  <span className={styles.plateMark} />
                </div>
              </div>
              <figcaption className={styles.caption}>
                <span className={styles.creator}>Not recorded</span>
                <span className={styles.workLine}>
                  <em>{card.type}</em>, {card.year}
                </span>
                <span className={styles.detail}>{card.medium}</span>
                <span className={styles.detail}>{card.dims}</span>
              </figcaption>
            </figure>
          ))}
        </div>
      </div>

      {/* ---- Act II · pinned layer ---- */}
      <div className={styles.pinnedLayer} aria-hidden="true">
        {/* The frames come back down as lines and merge into one ring. */}
        <div className={styles.frames}>
          {FRAMES.map((f) => (
            <span
              key={f.i}
              className={styles.frame}
              style={cssVars({ "--i": f.i, "--fx": f.fx, "--fy": f.fy, "--fw": f.fw, "--fh": f.fh })}
            />
          ))}
        </div>

        <div className={styles.sphereViewport}>
          <div className={styles.sphereRow}>
            {STUDIES.map((s, i) => (
              <div key={s.id} className={styles.study} data-i={i} data-lead={i === 0 || undefined} style={cssVars({ "--i": i })}>
                <div className={styles.stage}>
                  <s.Component />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* The sentence, drawn as a line — the same line the circles were
            drawn with — then filled, then burst into the field. */}
        <div className={styles.bridge}>
          <svg
            viewBox={`-40 -780 ${BRIDGE.width + 80} 1000`}
            className={styles.bridgeSvg}
            style={cssVars({ "--gn": BRIDGE.glyphs.length })}
          >
            {BRIDGE.glyphs.map((g, i) => (
              <g
                key={i}
                className={styles.bridgeGlyph}
                style={cssVars({ "--gi": i, "--dx": scatter[i].dx, "--dy": scatter[i].dy })}
              >
                <path d={g.d} transform={`translate(${g.x} 0)`} pathLength={1} />
              </g>
            ))}
          </svg>
        </div>

        {/* The ruled sheet: the engraving's hatching, unrolled across the
            pane; the sentence is drawn on it, and it goes as the letters fill. */}
        <svg className={styles.rules} viewBox="0 0 1000 620" preserveAspectRatio="none" aria-hidden="true">
          {RULES.map((i) => (
            <line key={i} className={styles.rule} x1={0} x2={1000} y1={12 + i * 13.8} y2={12 + i * 13.8} style={cssVars({ "--i": i })} />
          ))}
        </svg>

        {/* The screen: the field, the crowd, and the set switched off. */}
        <div className={styles.screen}>
          <CrowdField progress={progress} active={act === 6} reduced={reducedMotion} />
        </div>
        <span className={styles.crtLine} aria-hidden="true" />
      </div>

      {/* ---- Act III · black, the wordmark, the lines ---- */}
      <div className={styles.closing}>
        <div className={styles.closingInner}>
          <Wordmark play={act === 7} reduced={reducedMotion} />
          <span className={styles.taglineStack}>
            <span className={styles.tagline} data-stage="first">
              {firstWords.map((w, i) => (
                <span key={i} className={styles.stamp} style={cssVars({ "--i": i })}>
                  {w}
                </span>
              ))}
            </span>
            <span className={styles.tagline} data-stage="settled">
              {settledWords.map((w, i) => (
                <span key={i} className={styles.resolve} style={cssVars({ "--i": i })}>
                  {w}
                </span>
              ))}
            </span>
          </span>
        </div>
      </div>
    </div>
  );
}
