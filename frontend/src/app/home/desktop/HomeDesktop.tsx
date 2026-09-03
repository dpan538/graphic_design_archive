"use client";

import { useEffect, useRef, useState } from "react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { ScrollToPlugin } from "gsap/ScrollToPlugin";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import SiteNav from "@/components/site/SiteNav";
import ContributionSection from "./sections/ContributionSection";
import EnterSection from "./sections/EnterSection";
import IdentitySection from "./sections/IdentitySection";
import StatusSection from "./sections/StatusSection";
import styles from "./HomeDesktop.module.css";

gsap.registerPlugin(ScrollTrigger, ScrollToPlugin, useGSAP);

/* Homepage, desktop — pinned left-nav / right-pane split screen
   (HOMEPAGE_DESIGN_v1.md). One tall scroll container; a sticky frame holds a
   constant left nav plus a right pane whose four sections crossfade at
   section boundaries (a discrete page-switch) while each section's own
   `--local-progress` custom property drives a continuous scrub-tied
   sub-animation inside it. Weights below set each section's share of the
   total scroll distance — Contribution carries the most because of its
   nested chart -> 3D sequence. */
type SectionDef = { key: string; n: string; label: string; accentVar: string; weight: number };

/* Identity runs the full gallery -> spheres -> grid -> black -> MGDA
   sequence (HOMEPAGE_IDENTITY_SEQUENCE_v1.md) — six screens, most of which
   is pinned state-change rather than movement. The other three keep the
   ~2.6x pacing bump from the previous round. */
const SECTIONS: SectionDef[] = [
  /* Eleven screens: the film's scrubbed beats (frames, studies, sentence,
     field) were too quick to read at eight. */
  { key: "identity", n: "01", label: "Identity", accentVar: "--sky", weight: 11.0 },
  { key: "contribution", n: "02", label: "Contribution", accentVar: "--green", weight: 10.0 },
  { key: "enter", n: "03", label: "Enter the Archive", accentVar: "--coral", weight: 1.5 },
  /* Six viewport-heights: the sheet draws over the first 1.5, the lens
     visits three stations at 0.75 each, then the panorama and the reading.
     StatusSection.module.css reads the same 6 as its --v unit. */
  { key: "status", n: "04", label: "Research status", accentVar: "--yellow", weight: 6.0 },
];

const CONTRIBUTION_INDEX = SECTIONS.findIndex((s) => s.key === "contribution");
/* Contribution holds its opening state before anything starts moving. The
   card lands about 9% into the section's own range, and without a pause after
   that the reader keeps scrolling straight through the one composed frame the
   section opens on, never realising it was a place to stop and read.
   Cut 40% from an initial 0.2: long enough to register as a held frame, short
   enough that it never reads as the page having stopped responding. */
const CONTRIBUTION_HOLD = 0.12;
const IDENTITY_INDEX = SECTIONS.findIndex((s) => s.key === "identity");
const STATUS_INDEX = SECTIONS.findIndex((s) => s.key === "status");

/* Identity's act boundaries in its own local progress
   (HOMEPAGE_IDENTITY_SEQUENCE_v1.md §A2). Crossing one of these is an
   *event* — it fires a self-driven timeline in IdentitySection rather than
   scrubbing a value, which is what gives those beats their own tempo
   instead of being draggable halfway by the wheel. */
/* 0.175: study I draws only once the frames have merged (0.13–0.17) — at
   0.12 it drew over them. 0.30: study IV arrives; from here to the
   engraving the film drives the scroll itself (see the effect below). */
/* act changes re-render the section and recalc its style, so each boundary
   sits where the film is at rest or nothing visible moves: 0.175 the
   hand-over, 0.19 before the arrivals' first motion, 0.30 the hold on the
   open eye, 0.45 the film's end */
const IDENTITY_ACT_BOUNDS = [0.09, 0.175, 0.19, 0.3, 0.45, 0.6, 0.815, 0.985];
/* The self-driven stretch of Identity, as SEGMENTS of its local progress:
   each is a scroll destination and the seconds to reach it; a segment
   whose destination is where we already are is a hold. Holds are where
   the timed animations (study I drawing itself, the eye opening) get the
   time they need — a single sweep dragged the row away mid-draw. */
/* the field's beat: where the scrub first carries the field to rest, the
   page holds for the blink drawn in it (identity/CrowdField.tsx) */
const FIELD_REST = 0.685;
const FIELD_BEAT_SECONDS = 3.1;
const IDENTITY_FILM: { to: number; seconds: number; ease: string }[] = [
  /* the reader is already moving when this starts, so it starts AT speed
     (an ease-out, not in-out): the frames fly at once and settle into the
     merge — a standing start here read as a hesitation */
  { to: 0.18, seconds: 2.4, ease: "power2.out" }, // the frames fly and merge; the ring hands over to study I
  { to: 0.18, seconds: 5.5, ease: "none" }, // study I draws itself (the last loop lands at 5.47 s)
  { to: 0.26, seconds: 2.2, ease: "power1.inOut" }, // the eye and the engraving come in and the row moves with them: one motion, to the eye
  { to: 0.3, seconds: 1.3, ease: "power2.out" }, // the lids part
  { to: 0.3, seconds: 2.2, ease: "none" }, // on the open eye: it looks about, follows the pointer
  { to: 0.45, seconds: 1.6, ease: "power2.inOut" }, // the last step; the engraving centred; scroll returns
];
const actFor = (local: number) => IDENTITY_ACT_BOUNDS.filter((b) => local >= b).length;

const TOTAL_WEIGHT = SECTIONS.reduce((a, s) => a + s.weight, 0);
const BOUNDS = (() => {
  let acc = 0;
  const b = [0];
  SECTIONS.forEach((s) => {
    acc += s.weight / TOTAL_WEIGHT;
    b.push(acc);
  });
  return b;
})();

/* Sections hand over by being DEALT, not dissolved: the incoming one slides up
   over the one before it at full opacity, like a card drawn off a deck. A
   cross-fade briefly renders two solid-background pages on top of each other,
   which is what made the change of section look cheap. Because nothing is
   translucent, this window can be much wider than the old fade could be —
   that width is what makes the hand-over feel smooth rather than snapped. */
/* The deal happens INSIDE the incoming section's own share, never in the tail
   of the outgoing one. Starting it a margin BEFORE the boundary meant the
   incoming card began covering Identity at 88% of Identity's progress — past
   its last act boundary (0.985), so Identity's closing tagline was buried
   before it could ever run and Contribution appeared to cut in early. */
const SLIDE_MARGIN = 0.045;
/* Capped against the section's OWN share as well. A fixed slice of total
   progress is a reasonable deal for Contribution (9% of its range) but 72% of
   Research status's, so a nav jump past a fixed margin landed three-quarters
   of the way through the short sections. Proportional, every section is
   entered ~10% in. */
const dealWindowFor = (i: number) =>
  Math.min(SLIDE_MARGIN, (BOUNDS[i + 1] - BOUNDS[i]) * 0.55);
const clamp01 = (v: number) => Math.min(Math.max(v, 0), 1);
/* Decelerating: the card is quick off the deck and settles into place. */
const easeOut = (t: number) => 1 - Math.pow(1 - t, 3);

export default function HomeDesktop() {
  const root = useRef<HTMLDivElement>(null);
  const rootRef = root;
  const splitRef = useRef<HTMLDivElement>(null);
  const sectionRefs = useRef<(HTMLDivElement | null)[]>([]);
  const contributionProgressRef = useRef(0);
  const activeIndexRef = useRef(0);
  const identityActRef = useRef(0);
  const identityProgressRef = useRef(0);
  const identityPrevLocalRef = useRef(0);
  const fieldBeatRef = useRef(false);
  /* Set inside the scroll effect: applies a progress value with NO easing, so
     a nav jump can land on a section without the scrub rendering every state
     between here and there. */
  const jumpRef = useRef<((p: number) => void) | null>(null);

  const [identityAct, setIdentityAct] = useState(0);
  const [activeIndex, setActiveIndex] = useState(0);
  const [reduced, setReduced] = useState(false);

  /* The pinned frame must start exactly at the masthead's bottom edge. Any
     drift between them clips the frame's top behind the header AND pushes its
     bottom past the viewport by the same amount, which reads as the whole
     section sitting too low with the title crowding the top. Measured, not
     assumed, so it survives changes to the header. */
  useEffect(() => {
    const header = document.querySelector("header");
    const root = rootRef.current;
    if (!header || !root) return undefined;
    const sync = () => {
      root.style.setProperty("--nav-top", `${header.getBoundingClientRect().height}px`);
      /* The measurement changes the pinned frame's height, which changes every
         ScrollTrigger start/end derived from it. Without recalibrating, a load
         that restores a mid-page scroll position renders the section against
         stale bounds — the upper half clipped, its title cut off above the
         frame. Rare, because it needs the restore to land inside the pin. */
      ScrollTrigger.refresh();
    };
    sync();
    const ro = new ResizeObserver(sync);
    ro.observe(header);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const onChange = () => setReduced(mq.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  /* Study I's draw is self-driven and takes ~3.5 s; while it plays the
     wheel, touch and the keyboard are refused, so a reader cannot scrub
     past it or drag the row in over it (the owner: "the animation would be
     skipped, and it reads as chaos"). Preventing the events keeps the
     layout untouched, so ScrollTrigger sees no refresh. */
  /* One stretch of the page plays ITSELF: Identity's ellipsis, from the
     frames' flight through the three studies to the engraving centred. The
     scroll position is driven by a tween across the stretch — so every
     scrubbed beat runs at its designed pace — and the wheel, touch and the
     scrolling keys are refused until it is done; the reader then scrolls
     into the sentence. Entered only from below; scrolling back through it
     later is an ordinary scrub. (A second film over Contribution's middle
     was tried and withdrawn — it read as the page acting on its own.) */
  const filmRef = useRef<{ tween: gsap.core.Timeline; release: () => void } | null>(null);
  const playFilm = (segments: { toGlobal: number; seconds: number; ease: string }[]) => {
    const split = splitRef.current;
    if (!split) return;
    filmRef.current?.tween.kill();
    filmRef.current?.release();
    const range = split.offsetHeight - window.innerHeight;
    const proxy = { y: window.scrollY };
    let done = false;
    const block = (e: Event) => {
      if (!done) e.preventDefault();
    };
    const KEYS = new Set(["ArrowDown", "ArrowUp", "PageDown", "PageUp", "Home", "End", " "]);
    const onKey = (e: KeyboardEvent) => {
      if (!done && KEYS.has(e.key)) e.preventDefault();
    };
    window.addEventListener("wheel", block, { passive: false });
    window.addEventListener("touchmove", block, { passive: false });
    window.addEventListener("keydown", onKey);
    const release = () => {
      done = true;
      window.removeEventListener("wheel", block);
      window.removeEventListener("touchmove", block);
      window.removeEventListener("keydown", onKey);
      filmRef.current = null;
    };
    const tween = gsap.timeline({ onUpdate: () => window.scrollTo(0, proxy.y), onComplete: release });
    for (const seg of segments) {
      tween.to(proxy, { y: split.offsetTop + seg.toGlobal * range, duration: seg.seconds, ease: seg.ease });
    }
    filmRef.current = { tween, release };
  };
  useEffect(
    () => () => {
      filmRef.current?.tween.kill();
      filmRef.current?.release();
    },
    [],
  );

  const prevIdentityAct = useRef(0);
  useEffect(() => {
    const prev = prevIdentityAct.current;
    prevIdentityAct.current = identityAct;
    if (reduced || identityAct !== 1 || prev !== 0 || activeIndexRef.current !== IDENTITY_INDEX) return;
    const span = BOUNDS[1] - BOUNDS[0];
    playFilm(IDENTITY_FILM.map((seg) => ({ toGlobal: BOUNDS[0] + seg.to * span, seconds: seg.seconds, ease: seg.ease })));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [identityAct, reduced]);

  useGSAP(
    () => {
      if (reduced || !splitRef.current) return undefined;

      splitRef.current.style.height = `${TOTAL_WEIGHT * 100}vh`;

      const apply = (p: number) => {
        let newActive = 0;
        SECTIONS.forEach((_, i) => {
          if (p >= BOUNDS[i]) newActive = i;
        });

        /* How far section i has been drawn over its predecessor. Section 0 is
           the bottom of the deck and is always seated — this is also what
           makes its rest state correct on first paint, with no ramp to land
           in the middle of. */
        const dealt = (i: number) =>
          i <= 0 ? 1 : clamp01((p - BOUNDS[i]) / dealWindowFor(i));

        SECTIONS.forEach((_, i) => {
          const start = BOUNDS[i];
          const end = BOUNDS[i + 1];
          /* Local progress is measured from the END of the deal window, so a
             section that is still sliding in shows its REST state rather than
             one already advanced into its sequence. Without this, a nav jump
             landed every section ~10.5% into its range — which for Identity is
             past its first act boundary (0.09), into the gap after the gallery
             has faded and before the next beat begins: a black screen. */
          const dw = i === 0 ? 0 : dealWindowFor(i);
          let local = clamp01((p - (start + dw)) / Math.max(end - start - dw, 0.0001));
          if (i === CONTRIBUTION_INDEX) {
            local = clamp01((local - CONTRIBUTION_HOLD) / (1 - CONTRIBUTION_HOLD));
          }

          const raw = dealt(i);
          /* Once the next card is fully seated this one is completely hidden
             behind it, so stop painting it — but only then. Nothing is ever
             made translucent, so there is no state where a section is
             half-there and reads as washed out. */
          const covered = i < SECTIONS.length - 1 && dealt(i + 1) >= 1;

          const el = sectionRefs.current[i];
          if (el) {
            el.style.setProperty("--enter", String(easeOut(raw)));
            el.style.setProperty("--local-progress", String(local));
            el.dataset.visible = raw > 0 && !covered ? "true" : "false";
          }
          if (i === CONTRIBUTION_INDEX) contributionProgressRef.current = local;
          if (i === IDENTITY_INDEX) {
            identityProgressRef.current = local;
            /* the field's beat — only on a real scrub down through the rest
               point (never a nav jump's leap, never scrolling back up), once
               per visit; a snap to the point, then the hold */
            const prevLocal = identityPrevLocalRef.current;
            identityPrevLocalRef.current = local;
            if (local < 0.6) fieldBeatRef.current = false;
            else if (
              !fieldBeatRef.current &&
              prevLocal < FIELD_REST &&
              local >= FIELD_REST &&
              local - prevLocal < 0.02 &&
              activeIndexRef.current === IDENTITY_INDEX
            ) {
              fieldBeatRef.current = true;
              const restGlobal = BOUNDS[IDENTITY_INDEX] + FIELD_REST * (BOUNDS[IDENTITY_INDEX + 1] - BOUNDS[IDENTITY_INDEX]);
              playFilm([
                { toGlobal: restGlobal, seconds: 0.35, ease: "power2.out" },
                { toGlobal: restGlobal, seconds: FIELD_BEAT_SECONDS, ease: "none" },
              ]);
            }
            const act = actFor(local);
            if (act !== identityActRef.current) {
              identityActRef.current = act;
              setIdentityAct(act);
            }
          }
        });

        if (newActive !== activeIndexRef.current) {
          activeIndexRef.current = newActive;
          setActiveIndex(newActive);
        }
      };

      /* Raw ScrollTrigger progress maps 1:1 to scroll position, which reads
         mechanical — every stage starts and stops abruptly and a fast flick
         snaps. Render a value that eases toward the scroll-driven target on
         a rAF loop instead, so motion has weight. The loop parks itself once
         it converges, so an idle page costs nothing. */
      /* Smoothing with velocity but NO overshoot: the rendered value chases
         the scroll-driven target on a critically damped spring (ζ = 1 at
         these per-frame constants), so a flick settles in ~0.5 s without
         ever passing its mark. An earlier under-damped version (ζ ≈ 0.86)
         read as pages catching and lurching — "bouncy, not smooth". */
      const STIFF = 0.036;
      const DAMP = 0.68;
      let target = 0;
      let rendered = 0;
      let velocity = 0;
      let raf = 0;
      const tick = () => {
        const delta = target - rendered;
        if (Math.abs(delta) < 0.00005 && Math.abs(velocity) < 0.00002) {
          rendered = target;
          velocity = 0;
          apply(rendered);
          raf = 0;
          return;
        }
        velocity = (velocity + delta * STIFF) * DAMP;
        rendered += velocity;
        apply(rendered);
        raf = requestAnimationFrame(tick);
      };
      const schedule = (p: number) => {
        target = p;
        if (!raf) raf = requestAnimationFrame(tick);
      };

      jumpRef.current = (p: number) => {
        target = p;
        rendered = p;
        velocity = 0;
        apply(p);
      };

      /* A hand-over left half-dealt is the "page stuck halfway" the owner
         saw. When the wheel rests inside a deal window, finish it: the
         scroll itself glides to the near end of the window (back if under
         a third in, forward otherwise), so no frame ever holds two cards
         mid-pull. */
      let snapTimer = 0;
      let snapTween: gsap.core.Tween | null = null;
      const snapIfDealing = (p: number) => {
        const split = splitRef.current;
        if (!split) return;
        const range = split.offsetHeight - window.innerHeight;
        for (let i = 1; i < SECTIONS.length; i++) {
          const a = BOUNDS[i];
          const b = a + dealWindowFor(i);
          if (p > a + 0.002 && p < b - 0.002) {
            const to = p - a < (b - a) * 0.34 ? a - 0.001 : b + 0.001;
            const proxy = { y: window.scrollY };
            snapTween?.kill();
            snapTween = gsap.to(proxy, {
              y: split.offsetTop + to * range,
              duration: 0.7,
              ease: "power2.inOut",
              onUpdate: () => window.scrollTo(0, proxy.y),
            });
            return;
          }
        }
      };
      const onWheelSettle = () => {
        window.clearTimeout(snapTimer);
        snapTween?.kill();
        snapTimer = window.setTimeout(() => snapIfDealing(target), 220);
      };
      window.addEventListener("wheel", onWheelSettle, { passive: true });
      window.addEventListener("touchend", onWheelSettle, { passive: true });

      const st = ScrollTrigger.create({
        trigger: splitRef.current,
        start: "top top",
        end: "bottom bottom",
        onUpdate: (self) => schedule(self.progress),
        onRefresh: (self) => {
          /* Layout changed under us — jump, don't ease, or the page eases
             from a stale position after a resize. */
          target = self.progress;
          rendered = self.progress;
          velocity = 0;
          apply(rendered);
        },
      });
      apply(0);

      return () => {
        cancelAnimationFrame(raf);
        window.clearTimeout(snapTimer);
        snapTween?.kill();
        window.removeEventListener("wheel", onWheelSettle);
        window.removeEventListener("touchend", onWheelSettle);
        jumpRef.current = null;
        st.kill();
      };
    },
    { scope: root, dependencies: [reduced] },
  );

  /* Nav jumps are DEALT, not scrubbed. Animating the scroll ran the eased
     scrub across the whole span between here and there, so clicking
     "Contribution" from Identity replayed every intermediate state as a fast
     flashback and dropped the reader into a mid-sequence frame. Instead: land
     the scroll instantly, then play the same opacity-free card pull the scroll
     boundary uses. */
  const goToSection = (i: number) => {
    if (reduced) {
      sectionRefs.current[i]?.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    const split = splitRef.current;
    if (!split) return;
    const from = activeIndexRef.current;
    if (from === i) return;

    /* a nav jump wins over any film in progress — left running, the film's
       tween kept driving scrollTo and dragged the page back to the studies */
    filmRef.current?.tween.kill();
    filmRef.current?.release();

    const scrollRange = split.offsetHeight - window.innerHeight;
    /* Land just past the deal window so the target reads as seated: at the
       boundary itself its own dealt() is still 0. */
    /* Identity is the bottom of the deck — always seated, never dealt — so it
       lands on its own start. Offsetting it by a deal window put it 10.5% in,
       past the gallery's exit at 0.09. */
    const p =
      i === 0 ? BOUNDS[0] : Math.min(BOUNDS[i] + dealWindowFor(i) * 1.05, 0.9999);
    window.scrollTo(0, split.offsetTop + p * scrollRange);
    jumpRef.current?.(p);

    const incoming = sectionRefs.current[i];
    const outgoing = sectionRefs.current[from];
    if (!incoming) return;
    /* The tween is a flourish; correctness must not depend on it finishing.
       GSAP runs on requestAnimationFrame, so anything that suspends frames
       (a background tab, reduced-motion shims) would otherwise strand the
       outgoing section forced-visible on top. Settle on a real timer too. */
    let settled = false;
    let tween: gsap.core.Tween | null = null;
    const settle = () => {
      if (settled) return;
      settled = true;
      /* Kill first: a settle that does not stop the tween it supersedes gets
         overwritten the next time that tween ticks, stranding the section
         mid-slide. */
      tween?.kill();
      jumpRef.current?.(p);
    };
    window.setTimeout(settle, 1250);

    if (i > from) {
      /* Forward: the target is dealt over the one you were on, which has to
         stay on screen underneath for the pull to read as a card at all. */
      if (outgoing) {
        outgoing.dataset.visible = "true";
        outgoing.style.setProperty("--enter", "1");
      }
      tween = gsap.fromTo(
        incoming,
        { "--enter": 0 },
        { "--enter": 1, duration: 1.05, ease: "power3.out", onComplete: settle },
      );
    } else {
      /* Backward: nothing slides in — the card you are on slides off to
         uncover the one beneath it. */
      incoming.dataset.visible = "true";
      incoming.style.setProperty("--enter", "1");
      if (outgoing) {
        outgoing.dataset.visible = "true";
        tween = gsap.fromTo(
          outgoing,
          { "--enter": 1 },
          { "--enter": 0, duration: 1.05, ease: "power3.in", onComplete: settle },
        );
      }
    }
  };

  return (
    <div className={styles.page} ref={root}>
      <SiteNav revealTone="dark" />

      <div className={styles.split} ref={splitRef}>
        <div className={styles.navFrame}>
          <nav className={styles.leftNav} aria-label="Homepage sections">
            {SECTIONS.map((s, i) => (
              <button
                key={s.key}
                type="button"
                className={styles.navItem}
                data-active={reduced ? true : activeIndex === i}
                aria-current={(reduced ? true : activeIndex === i) ? "true" : undefined}
                style={{ ["--nav-accent" as string]: `var(${s.accentVar})` }}
                onClick={() => goToSection(i)}
              >
                <span className={styles.navN}>{s.n}</span>
                <span className={styles.navLabel}>{s.label}</span>
              </button>
            ))}
          </nav>

          <div className={styles.rightPane}>
            {SECTIONS.map((s, i) => (
              <div
                key={s.key}
                ref={(el) => {
                  sectionRefs.current[i] = el;
                }}
                className={styles.sectionSlot}
                style={{ zIndex: i }}
                data-visible={reduced ? true : undefined}
              >
                {s.key === "identity" && (
                  <IdentitySection act={reduced ? 7 : identityAct} reducedMotion={reduced} progress={identityProgressRef} />
                )}
                {s.key === "contribution" && (
                  <ContributionSection
                    active={reduced || activeIndex === CONTRIBUTION_INDEX || (activeIndex === IDENTITY_INDEX && identityAct >= 7)}
                    entered={reduced || activeIndex === CONTRIBUTION_INDEX}
                    progressRef={contributionProgressRef}
                    reducedMotion={reduced}
                  />
                )}
                {s.key === "enter" && <EnterSection />}
                {s.key === "status" && (
                  <StatusSection
                    active={reduced || activeIndex === STATUS_INDEX}
                    reducedMotion={reduced}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
