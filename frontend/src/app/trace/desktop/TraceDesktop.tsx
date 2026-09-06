"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import SiteNav from "@/components/site/SiteNav";
import { IDENTITY_TAGLINE } from "@/app/home/lib/content";
import { BASELINE_NOTE, BETWEEN, CAPTIONS, CLOSING, CLOSING_WORD, PRINCIPLES, SPACETIME_RELEASE_NOTE, TRACE_DEFINITION, TRACE_LEAD, TRACE_LINE, TRACE_TITLE, WAYS, type Baseline } from "../lib/content";
import Instrument from "./Instrument";
import { PATTERN_HOLD, sceneFrontProgram, sceneProgram, setAxisYears, setScroll } from "./instruments";
import { ContextGlyph, ExplorationGlyph } from "./icons";
import styles from "./TraceDesktop.module.css";

/* TRACE landing, desktop (FRONTEND_DESIGN_DECISION.md §7f).

   One pinned scene (the sceneWrap is 800vh; the scene is sticky under
   the nav), two canvases (the set behind the text, the field's outer
   rings in front), one clock, one scroll state. SCRIPT maps the scene's
   scroll (0..1) to the system's state (0..4): holds on each of the five
   screens — TRACE · Context Canvas · Spacetime · Between records ·
   Exploration — and transformations between them. Over the canvases,
   the text layer: the title while screen 0 holds; each view's note
   (name, question, brief, boundary / what the function does) in its own
   region as its screen settles (data-screen in the CSS module); and the
   CAPTIONS from content.ts inserted with the scroll — labels
   accumulate, paragraphs take turns (only the latest paragraph reached
   on a screen is shown), so no two paragraphs share the sheet. Rules
   checked in the browser at frozen states: no text box overlaps
   another; every label sits at least 24 px from the figures' boxes; no
   paragraph ends on a lone last word (text-wrap: pretty).

   The entries are the dock: a fixed column of the nav's 60 px controls,
   vertically centred, in line with the nav's Source icon, with the nav's
   own hover reveal — the page's only controls. Only the released views
   have one: Spacetime keeps its screen, its note and its place in the
   sequence as a research direction under review (2026-09-05), with its
   status stated and no control, no link and no leader line. While a
   released view's screen holds a leader line draws from the scene's
   anchor to its icon (gone once the scene releases). The closing block follows the scene:
   the line "TRACE the design history no single record can show on its
   own." joined by a fixed line to the nav's TRACE control once the
   headline has come up the page; the definition; the identity tagline
   (shown only at the page's very end); the principles and the baseline
   (figures from the governed manifests, never typed in).

   Dev hook (not in production builds): window.__mgdaTrace.freeze(sp)
   pins the scene at a scroll progress and dispatches a synchronous
   frame, because the browser harness cannot scroll and screenshot a
   pinned stage. */

const GLYPHS = { context: ContextGlyph, exploration: ExplorationGlyph } as const;
/* the views with an entry — the dock, the leaders */
const ENTRIES = WAYS.filter((w) => !w.deferred);
/* the scene's scroll (0..1) → the system's state (0..4): five screens —
   TRACE · Context Canvas · Spacetime · Between records · Exploration —
   holds, and the transformations between (PATTERN_HOLD is shared with
   the scene so the rings' straight↔smooth blend spans exactly its hold) */
const SCRIPT: [number, number, number, number][] = [
  /* from, to (scroll), state from, state to */
  [0, 0.1, 0, 0],
  [0.1, 0.18, 0, 1],
  [0.18, 0.32, 1, 1],
  [0.32, 0.4, 1, 2],
  [0.4, 0.54, 2, 2],
  [0.54, PATTERN_HOLD[0], 2, 3],
  [PATTERN_HOLD[0], PATTERN_HOLD[1], 3, 3],
  [PATTERN_HOLD[1], 0.82, 3, 4],
  [0.82, 1, 4, 4],
];
/* the view each icon and note belongs to */
const VIEW_SCREEN = [1, 2, 4];
const holdOf = (screen: number) => SCRIPT.find(([, , s0, s1]) => s0 === screen && s1 === screen) ?? [0, 0.1, 0, 0];
const fmt = (n: number) => n.toLocaleString("en-US");
const clamp01 = (x: number) => Math.min(1, Math.max(0, x));
const stateOf = (sp: number) => {
  for (const [a, b, s0, s1] of SCRIPT) if (sp <= b) return s0 + (s1 - s0) * clamp01((sp - a) / (b - a || 1));
  return 4;
};

export default function TraceDesktop({ baseline }: { baseline: Baseline }) {
  const root = useRef<HTMLDivElement>(null);
  const wrap = useRef<HTMLDivElement>(null);
  const stage = useRef<HTMLDivElement>(null);
  const dock = useRef<HTMLElement>(null);
  const anchor = useRef<HTMLSpanElement>(null);
  const heroText = useRef<HTMLDivElement>(null);
  const leads = useRef<(SVGPathElement | null)[]>([]);
  const notes = useRef<(HTMLDivElement | null)[]>([]);
  const readouts = useRef<(HTMLSpanElement | null)[]>([]);
  const captions = useRef<(HTMLSpanElement | null)[]>([]);
  const between = useRef<HTMLDivElement>(null);
  const closingWord = useRef<HTMLSpanElement>(null);
  const closingLine = useRef<HTMLHeadingElement>(null);
  const tagline = useRef<HTMLParagraphElement>(null);
  const footLead = useRef<SVGPathElement>(null);
  const state = useMemo(() => ({ current: 0 }), []);
  const drawIn = useMemo(() => ({ current: 0 }), []);
  const [reduced, setReduced] = useState(false);
  const [revealed, setRevealed] = useState<number | null>(null);
  /* dev hook: freeze the scene at a given scroll progress (the harness
     cannot scroll and screenshot a pinned stage) */
  const forced = useRef<number | null>(null);

  useEffect(() => {
    setAxisYears(baseline.yearFrom, baseline.yearTo);
  }, [baseline.yearFrom, baseline.yearTo]);

  /* the ground stays dark to the very end of the scroll (the document's
     own background is the archive's paper) */
  useEffect(() => {
    const prev = document.documentElement.style.background;
    document.documentElement.style.background = "#050506";
    return () => {
      document.documentElement.style.background = prev;
    };
  }, []);


  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const on = () => setReduced(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);

  /* the instrument draws itself in once, on arrival */
  useEffect(() => {
    if (reduced) {
      drawIn.current = 1;
      return;
    }
    let raf = 0;
    const t0 = performance.now();
    const tick = (now: number) => {
      const t = (now - t0) / 1000;
      drawIn.current = clamp01(t / 2.4);
      if (t < 2.6) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [reduced, drawIn]);

  const apply = useCallback(() => {
    const el = root.current;
    const w = wrap.current;
    const st = stage.current;
    const dk = dock.current;
    const an = anchor.current;
    const hero = heroText.current;
    if (!el || !w || !st || !dk || !an || !hero) return;
    const nav = document.querySelector("header");
    const navH = nav ? nav.getBoundingClientRect().height : 0;
    el.style.setProperty("--nav-h", `${Math.round(navH)}px`);
    const max = document.documentElement.scrollHeight - window.innerHeight;
    el.style.setProperty("--tp", (max > 0 ? clamp01(window.scrollY / max) : 1).toFixed(4));

    /* the scene's own scroll: 0 as it pins, 1 as it releases */
    const wr = w.getBoundingClientRect();
    const range = wr.height - st.getBoundingClientRect().height;
    const sp = forced.current ?? (range > 0 ? clamp01((navH - wr.top) / range) : 1);
    st.style.setProperty("--sp", sp.toFixed(4));
    setScroll(sp);
    const s = stateOf(sp);
    state.current = s;

    /* the text layer: the title while the matrix holds, then each view's
       sentence as its state settles */
    const heroOn = clamp01(1 - s / 0.45);
    hero.style.opacity = String(heroOn);
    hero.style.transform = `translateY(${(1 - heroOn) * -10}px)`;
    hero.style.visibility = heroOn > 0.01 ? "visible" : "hidden";
    /* the readout line: the sealed release while the matrix holds, then
       each view's governed figures */
    readouts.current.forEach((r, i) => {
      if (!r) return;
      /* the readout line belongs to the first screen only */
      const on = i === 0 ? heroOn : 0;
      r.style.opacity = String(on);
      r.style.visibility = on > 0.01 ? "visible" : "hidden";
    });
    /* the tagline: only at the page's very end */
    if (tagline.current) {
      const atEnd = max - window.scrollY < 8 ? 1 : 0;
      tagline.current.style.opacity = String(atEnd);
    }
    /* the closing block: TRACE, the verb, wired to TRACE, the control */
    if (closingLine.current && footLead.current) {
      const cl = closingLine.current.getBoundingClientRect();
      const nav = document.querySelector<HTMLElement>('header nav a[aria-label="TRACE"]');
      /* only once the closing block has come up the page */
      const inView = cl.top < window.innerHeight * 0.45 && cl.bottom > 0;
      if (nav && inView) {
        const nr = nav.getBoundingClientRect();
        const header = nav.closest("header");
        const hb = header ? header.getBoundingClientRect().bottom : nr.bottom;
        const ax = cl.right + 24;
        const ay = cl.top + cl.height * 0.5;
        const tx = nr.left + nr.width * 0.5;
        /* from the headline's edge, across to the control's column, up to
           the header's edge right under the icon */
        footLead.current.setAttribute("d", `M${ax} ${ay} H${tx} V${hb + 4}`);
        footLead.current.style.opacity = "1";
      } else footLead.current.style.opacity = "0";
    }
    if (between.current) {
      const nb = clamp01((clamp01(1 - Math.abs(s - 3) / 0.42) - 0.55) / 0.45);
      between.current.style.opacity = String(nb);
      between.current.style.transform = `translateY(${(1 - nb) * 8}px)`;
      between.current.style.visibility = nb > 0.01 ? "visible" : "hidden";
    }
    /* the captions: labels accumulate; paragraphs take turns — on each
       screen only the latest paragraph the scroll has reached is shown */
    const latestPara: Record<number, number> = {};
    CAPTIONS.forEach((cap, i) => {
      if (cap.kind !== "para") return;
      const [h0, h1] = holdOf(cap.screen);
      if (sp >= h0 + (h1 - h0) * cap.at) latestPara[cap.screen] = i;
    });
    captions.current.forEach((c, i) => {
      if (!c) return;
      const cap = CAPTIONS[i];
      const [h0, h1] = holdOf(cap.screen);
      const nearScreen = clamp01(1 - Math.abs(s - cap.screen) / 0.3);
      const arrived = sp >= h0 + (h1 - h0) * cap.at ? 1 : 0;
      const turn = cap.kind === "para" ? (latestPara[cap.screen] === i ? 1 : 0) : 1;
      const on = nearScreen * arrived * turn;
      c.style.opacity = String(on);
      c.style.visibility = on > 0.01 ? "visible" : "hidden";
    });

    const sr = st.getBoundingClientRect();
    const fr = an.getBoundingClientRect();
    const icons = Array.from(dk.querySelectorAll<HTMLElement>("a"));
    WAYS.forEach((w, i) => {
      const k = VIEW_SCREEN[i];
      const near = clamp01(1 - Math.abs(s - k) / 0.42);
      const settled = clamp01((near - 0.55) / 0.45);
      const note = notes.current[i];
      const lead = leads.current[i];
      const icon = w.deferred ? undefined : icons[ENTRIES.indexOf(w)];
      if (note) {
        note.style.opacity = String(settled);
        note.style.transform = `translateY(${(1 - settled) * 8}px)`;
        note.style.visibility = settled > 0.01 ? "visible" : "hidden";
      }
      if (lead && icon) {
        /* the leader: from the instrument's mark to the icon's edge, an elbow */
        const ir = icon.getBoundingClientRect();
        const ax = fr.left - sr.left + fr.width / 2;
        const ay = fr.top - sr.top + fr.height / 2;
        const tx = ir.left - sr.left - 10;
        const ty = ir.top - sr.top + ir.height / 2;
        const bx = ax + (tx - ax) * 0.55;
        lead.setAttribute("d", `M${ax} ${ay} H${bx} V${ty} H${tx}`);
        lead.style.strokeDashoffset = String(1 - clamp01((near - 0.35) / 0.4));
        /* gone once the scene is released to the closing block */
        lead.style.opacity = near > 0.35 && sp < 0.985 ? "1" : "0";
      }
    });
  }, [state]);

  useEffect(() => {
    let raf = 0;
    const onScroll = () => {
      if (!raf)
        raf = requestAnimationFrame(() => {
          raf = 0;
          apply();
        });
    };
    apply();
    const t = window.setTimeout(apply, 300);
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    if (process.env.NODE_ENV !== "production") {
      (window as unknown as { __mgdaTrace?: unknown }).__mgdaTrace = {
        freeze: (sp: number | null) => {
          forced.current = sp;
          apply();
          window.dispatchEvent(new Event("mgda:frame"));
        },
      };
    }
    return () => {
      window.clearTimeout(t);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      cancelAnimationFrame(raf);
    };
  }, [apply]);

  return (
    <div className={styles.page} ref={root}>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <SiteNav active="trace" revealTone="dark" />

      {/* the entries: fixed, centred, under the nav's Source icon; hover
          reveals the name the way the nav does; a deferred view has none */}
      <nav className={styles.dock} aria-label="TRACE functions" ref={dock}>
        <ol role="list">
          {ENTRIES.map((w, i) => {
            const Glyph = GLYPHS[w.key as keyof typeof GLYPHS];
            return (
              <li key={w.key}>
                <Link
                  href={w.href}
                  className={styles.dockItem}
                  aria-label={w.name}
                  onMouseEnter={() => setRevealed(i)}
                  onMouseLeave={() => setRevealed((c) => (c === i ? null : c))}
                  onFocus={() => setRevealed(i)}
                  onBlur={() => setRevealed((c) => (c === i ? null : c))}
                >
                  <Glyph />
                </Link>
              </li>
            );
          })}
        </ol>
        <span className={styles.dockReveal} data-shown={revealed !== null} style={{ top: `${(revealed ?? 0) * 74 + 30}px` }} aria-hidden="true">
          {revealed !== null ? ENTRIES[revealed].name : ""}
        </span>
      </nav>

      {/* the line from the closing block's TRACE to the nav's TRACE control */}
      <svg className={styles.footLead} aria-hidden="true">
        <path ref={footLead} />
      </svg>

      <main id="main" className={styles.main}>
        <div className={styles.grid} aria-hidden="true" />
        <div className={styles.grain} aria-hidden="true" />

        {/* the scene */}
        <div className={styles.sceneWrap} ref={wrap}>
          <div className={styles.scene} ref={stage}>
            <span className={styles.spine} aria-hidden="true" />

            <Instrument program={sceneProgram} progress={state} active={drawIn} reduced={reduced} className={styles.canvasFull} />
            <Instrument program={sceneFrontProgram} progress={state} active={drawIn} reduced={reduced} className={styles.canvasFront} />
            <span className={styles.anchor} ref={anchor} aria-hidden="true" />

            {/* the readout line, top left: the release, then each view's figures */}
            <p className={styles.readout} aria-live="polite">
              {[
                `Sealed release v49 · ${fmt(baseline.objects)} public objects`,
                `Context Canvas · ${fmt(baseline.objects)} public objects`,
                `Spacetime · a research direction under review · not released in v49`,
                `Between records · a pattern, not a claim`,
                `Exploration · ${baseline.associations} associations · ${baseline.inquiries} open inquiries`,
              ].map((line, i) => (
                <span
                  key={line}
                  ref={(n) => {
                    readouts.current[i] = n;
                  }}
                >
                  {line}
                </span>
              ))}
            </p>
            <div className={styles.text}>
              <div className={styles.heroText} ref={heroText}>
                <h1 className={styles.title}>{TRACE_TITLE}</h1>
                <p className={styles.line}>
                  {TRACE_LINE.split(". ")[0]}.
                  <br />
                  {TRACE_LINE.split(". ").slice(1).join(". ")}
                </p>
                <p className={styles.lead}>{TRACE_LEAD}</p>
              </div>
              {WAYS.map((w, i) => (
                <div
                  key={w.key}
                  className={styles.note}
                  data-screen={VIEW_SCREEN[i]}
                  ref={(n) => {
                    notes.current[i] = n;
                  }}
                >
                  <p className={styles.noteName}>{w.name}</p>
                  <p className={styles.noteQ}>{w.question}</p>
                  <p className={styles.noteBrief}>{w.brief}</p>
                  {w.boundary ? <p className={styles.noteBoundary}>{w.boundary}</p> : null}
                  {w.does ? <p className={styles.noteDoes}>{w.does}</p> : null}
                  {w.status ? <p className={styles.noteStatus}>{w.status}</p> : null}
                </div>
              ))}
              {/* the interlayer's own text */}
              <div className={styles.note} data-screen="3" ref={between}>
                <p className={styles.noteName}>{BETWEEN.name}</p>
                <p className={styles.noteQ}>{BETWEEN.question}</p>
                <p className={styles.noteBrief}>{BETWEEN.brief}</p>
                <p className={styles.noteBoundary}>{BETWEEN.boundary}</p>
              </div>
            </div>

            {/* the captions inserted into the scene with the scroll */}
            {CAPTIONS.map((c, i) => (
              <span
                key={`${c.screen}-${i}`}
                className={styles.cap}
                data-align={c.align ?? "left"}
                data-kind={c.kind ?? "label"}
                style={c.align === "right" ? { right: `${100 - c.x}%`, top: `${c.y}%`, maxWidth: c.width ? `${c.width}rem` : undefined } : { left: `${c.x}%`, top: `${c.y}%`, maxWidth: c.width ? `${c.width}rem` : undefined }}
                ref={(n) => {
                  captions.current[i] = n;
                }}
              >
                {c.text}
              </span>
            ))}

            <svg className={styles.leads} aria-hidden="true">
              {WAYS.map((w, i) => w.deferred ? null : (
                <path
                  key={w.key}
                  pathLength={1}
                  ref={(n) => {
                    leads.current[i] = n;
                  }}
                />
              ))}
            </svg>
          </div>
        </div>

        {/* the closing block — the concept in the owner's words, the
            principles, the baseline, and the line the page ends on */}
        <section className={styles.foot}>
          <h2 className={styles.closing} ref={closingLine}>
            <span className={styles.closingWord} ref={closingWord}>
              {CLOSING_WORD}
            </span>{" "}
            {CLOSING}
          </h2>
          <div className={styles.footTop}>
            <p className={styles.definition}>{TRACE_DEFINITION}</p>
            <p className={styles.tagline} ref={tagline}>
              {IDENTITY_TAGLINE}
            </p>
          </div>
          <div className={styles.footGrid}>
          <div className={styles.principles}>
            <p className={styles.eyebrow}>Shared research principles</p>
            <ul className={styles.pList} role="list">
              {PRINCIPLES.map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
          </div>
          <div className={styles.baseline}>
            <p className={styles.eyebrow}>Current TRACE baseline</p>
            <dl className={styles.ledger}>
              <div>
                <dt>Context Canvas</dt>
                <dd>
                  <b>{fmt(baseline.objects)}</b> public objects
                </dd>
              </div>
              <div>
                <dt>Spacetime</dt>
                <dd>{SPACETIME_RELEASE_NOTE}</dd>
              </div>
              <div>
                <dt>Exploration</dt>
                <dd>
                  <b>{baseline.associations}</b> evidence-qualified associations · <b>{baseline.inquiries}</b> open inquiries
                </dd>
              </div>
            </dl>
            <p className={styles.note2}>{BASELINE_NOTE}</p>
          </div>
          </div>
        </section>
      </main>
    </div>
  );
}
