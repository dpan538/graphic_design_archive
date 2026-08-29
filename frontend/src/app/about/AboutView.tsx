"use client";

import { Fragment, useEffect, useMemo, useRef, useState } from "react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { ArrowRight } from "lucide-react";
import SiteNav from "@/components/site/SiteNav";
import styles from "./about.module.css";
import {
  audiences,
  buildCitations,
  citeHint,
  claimBoundaries,
  contact,
  designResearchNote,
  evidenceProtocol,
  footerNote,
  methodProse,
  openingLead,
  openingMeta,
  openingStatement,
  pipelineStages,
  purposeLead,
  REPO_URL,
  rightsProse,
  scaleFigures,
  scaleLead,
  scaleNote,
  typeSystem,
  visualReferences,
} from "./content";

gsap.registerPlugin(ScrollTrigger, useGSAP);

/* ---- Per-section geometric device (varied, not one repeated ring) ---- */

type MotifKind =
  | "grooves"
  | "fan"
  | "registration"
  | "chart"
  | "rings"
  | "seal";

function Motif({ kind }: { kind: MotifKind }) {
  const common = {
    viewBox: "0 0 100 100",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2.5,
    strokeLinecap: "round",
  } as const;
  const solid = { fill: "currentColor", stroke: "none" } as const;
  let shape: React.ReactNode = null;

  switch (kind) {
    // §1 — record grooves / a reading eye
    case "grooves":
      shape = (
        <>
          {[15, 26, 37, 48].map((r) => (
            <circle key={r} cx="74" cy="78" r={r} />
          ))}
          <circle cx="74" cy="78" r="4" {...solid} />
        </>
      );
      break;
    // §2 — a radiating fan from the corner (Steinweiss)
    case "fan":
      shape = (
        <>
          {[22, 35, 48, 61, 74].map((r) => (
            <path key={r} d={`M ${100 - r} 100 A ${r} ${r} 0 0 1 100 ${100 - r}`} />
          ))}
          <path d="M 100 100 L 40 66" />
          <path d="M 100 100 L 66 40" />
        </>
      );
      break;
    // §3 — a printer's registration mark
    case "registration":
      shape = (
        <>
          <circle cx="72" cy="74" r="20" />
          <path d="M 72 42 L 72 106" />
          <path d="M 40 74 L 104 74" />
          <path d="M 72 74 L 92 74 A 20 20 0 0 1 72 94 Z" {...solid} />
        </>
      );
      break;
    // §4 — a bar chart on a baseline, with one data point
    case "chart":
      shape = (
        <>
          <path d="M 34 96 L 100 96" />
          {[
            [40, 18],
            [53, 34],
            [66, 26],
            [79, 50],
            [92, 40],
          ].map(([x, h]) => (
            <rect key={x} x={x} y={96 - h} width="8" height={h} />
          ))}
          <circle cx="83" cy="46" r="3.5" {...solid} />
        </>
      );
      break;
    // §5 — two interlocking rings (reach / connect)
    case "rings":
      shape = (
        <>
          <circle cx="65" cy="78" r="22" />
          <circle cx="87" cy="78" r="22" />
          <circle cx="65" cy="78" r="3" {...solid} />
          <circle cx="87" cy="78" r="3" {...solid} />
        </>
      );
      break;
    // §6 — a seal with a line drawn through it (a boundary)
    case "seal":
      shape = (
        <>
          <circle cx="74" cy="76" r="34" />
          <circle cx="74" cy="76" r="24" />
          <path d="M 34 76 L 114 76" />
        </>
      );
      break;
  }

  return (
    <div className={styles.motif} aria-hidden="true">
      <svg {...common}>{shape}</svg>
    </div>
  );
}

function Band({
  num,
  kicker,
  title,
  motif,
}: {
  num: string;
  kicker: string;
  title: string;
  motif: MotifKind;
}) {
  return (
    <div className={styles.band} data-animate="band">
      <Motif kind={motif} />
      <p className={styles.bandKicker}>{kicker}</p>
      <div className={styles.bandHead}>
        <span className={styles.bandNum} data-parallax>
          {num}
        </span>
        <h2 className={styles.bandTitle}>{title}</h2>
      </div>
    </div>
  );
}

function CitationCard({
  tone,
  style,
  text,
}: {
  tone: string;
  style: string;
  text: string;
}) {
  const [copied, setCopied] = useState(false);
  const timer = useRef<number | null>(null);

  useEffect(
    () => () => {
      if (timer.current !== null) window.clearTimeout(timer.current);
    },
    [],
  );

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      if (timer.current !== null) window.clearTimeout(timer.current);
      timer.current = window.setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard unavailable — text stays selectable */
    }
  }

  return (
    <article className={styles.cite} data-tone={tone}>
      <div className={styles.citeHead}>
        <span className={styles.citeStyle}>{style}</span>
        <button
          type="button"
          className={styles.copyBtn}
          data-copied={copied || undefined}
          onClick={copy}
          aria-label={`Copy ${style} citation`}
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <p className={styles.citeText}>{text}</p>
    </article>
  );
}

export default function AboutView() {
  const root = useRef<HTMLDivElement>(null);

  const [accessDate, setAccessDate] = useState<Date>(
    () => new Date("2026-08-30T00:00:00"),
  );
  useEffect(() => setAccessDate(new Date()), []);
  const citations = useMemo(() => buildCitations(accessDate), [accessDate]);

  useGSAP(
    () => {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

      gsap.utils.toArray<HTMLElement>("[data-animate]").forEach((g) => {
        const kids = Array.from(g.children);
        if (g.dataset.animate === "masthead") {
          gsap.from(kids, {
            y: 16,
            duration: 0.8,
            ease: "power2.out",
            stagger: 0.07,
          });
          return;
        }
        gsap.from(kids, {
          y: 20,
          duration: 0.7,
          ease: "power2.out",
          stagger: 0.06,
          scrollTrigger: { trigger: g, start: "top 85%", once: true },
        });
      });

      gsap.utils.toArray<HTMLElement>("[data-parallax]").forEach((el) => {
        const plate = el.closest("section");
        if (!plate) return;
        gsap.to(el, {
          yPercent: -16,
          ease: "none",
          scrollTrigger: {
            trigger: plate,
            start: "top bottom",
            end: "bottom top",
            scrub: true,
          },
        });
      });

      document.addEventListener("visibilitychange", ScrollTrigger.refresh);
      return () =>
        document.removeEventListener("visibilitychange", ScrollTrigger.refresh);
    },
    { scope: root },
  );

  return (
    <div className={styles.page} ref={root}>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <SiteNav active="about" />

      <main id="main">
        {/* Masthead */}
        <header className={styles.masthead} data-animate="masthead">
          <p className={styles.mastKicker}>
            About
            <span className={styles.draftTag}>Working draft &middot; not final</span>
          </p>
          <h1 className={styles.mastTitle}>{openingStatement}</h1>
          <div className={styles.mastSide}>
            <p className={styles.mastLead}>{openingLead}</p>
            <p className={styles.mastMeta}>{openingMeta}</p>
          </div>
        </header>

        {/* 1 — Purpose */}
        <section id="purpose" className={styles.plate} data-tone="blue">
          <Band
            num="1"
            kicker="Purpose"
            title="An archive made to be read, located, and explored."
            motif="grooves"
          />
          <div className={styles.body} data-animate="body">
            <div className={styles.rail}>
              <span className={styles.railKicker}>What it is for</span>
              Reading objects in context, locating them by place and period, and
              exploring how the evidence connects.
            </div>
            <div className={styles.main}>
              <p className={styles.pull}>{purposeLead}</p>
              <p className={styles.subLabel}>Audiences</p>
              <div className={styles.grid3}>
                {audiences.map((a) => (
                  <div key={a.title} className={styles.card} data-tick={a.tone}>
                    <h3>{a.title}</h3>
                    <p>{a.body}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* 2 — Methodology */}
        <section id="methodology" className={styles.plate} data-tone="red">
          <Band
            num="2"
            kicker="Methodology"
            title="Provenance before interpretation."
            motif="fan"
          />
          <div className={styles.body} data-animate="body">
            <div className={styles.rail}>
              <span className={styles.railKicker}>Archive &amp; research method</span>
              Gathering is not publishing. Every record you can read here has
              passed source, rights, classification, completeness, and reading
              gates.
            </div>
            <div className={styles.main}>
              <div className={styles.proseCols}>
                {methodProse.map((p) => (
                  <p key={p.slice(0, 24)}>{p}</p>
                ))}
              </div>

              <p className={styles.subLabel}>Evidence protocol</p>
              <dl className={styles.defs}>
                {evidenceProtocol.map((e) => (
                  <div key={e.term}>
                    <dt>{e.term}</dt>
                    <dd>{e.def}</dd>
                  </div>
                ))}
              </dl>

              <p className={styles.subLabel}>How a record reaches the page</p>
              <div className={styles.flow} aria-label="Production pipeline">
                {pipelineStages.map((step, i) => (
                  <Fragment key={step}>
                    <span className={styles.flowStep}>{step}</span>
                    {i < pipelineStages.length - 1 ? (
                      <span className={styles.flowArrow} aria-hidden="true">
                        →
                      </span>
                    ) : null}
                  </Fragment>
                ))}
              </div>

              <div className={styles.prose}>
                <p>{designResearchNote}</p>
              </div>
            </div>
          </div>
        </section>

        {/* 3 — Visual design rationale */}
        <section id="visual" className={styles.plate} data-tone="yellow">
          <Band
            num="3"
            kicker="Visual design rationale"
            title="Built like a printed catalogue."
            motif="registration"
          />
          <div className={styles.body} data-animate="body">
            <div className={styles.rail}>
              <span className={styles.railKicker}>Combined, not copied</span>
              Three references synthesised into one language for reading
              evidence.
            </div>
            <div className={styles.main}>
              <div className={styles.prose}>
                <p>
                  The interface is set the way a printed reference catalogue is:{" "}
                  <span className={styles.kw} data-tone="ink">colour as a coding system</span>,
                  a heavy line holding the structure, and one clear idea per
                  section. It draws on{" "}
                  <span className={styles.kw} data-tone="red">Alex Steinweiss</span>, who
                  gave each record cover a single announced idea;{" "}
                  <span className={styles.kw} data-tone="blue">New York editorial
                  illustration</span>, for flat bright colour held by a black
                  line; and{" "}
                  <span className={styles.kw} data-tone="green">spot-colour printing</span>,
                  where a few inks and one line block do all the work.
                </p>
              </div>

              <p className={styles.subLabel}>References</p>
              <div className={styles.grid2}>
                {visualReferences.map((r) => (
                  <div key={r.title} className={styles.card} data-tick={r.tone}>
                    <h3>{r.title}</h3>
                    <p className={styles.cardMeta}>{r.meta}</p>
                    <p>{r.body}</p>
                  </div>
                ))}
              </div>

              <p className={styles.subLabel}>Type system</p>
              <div className={styles.typeList}>
                {typeSystem.map((t) => (
                  <div key={t.role} className={styles.typeRow}>
                    <span>{t.role}</span>
                    <span>{t.face}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* 4 — Scale */}
        <section id="scale" className={styles.plate} data-tone="green">
          <Band
            num="4"
            kicker="The archive in numbers"
            title="A large raw pool, cleaned to a verified core."
            motif="chart"
          />
          <div className={styles.body} data-animate="body">
            <div className={styles.rail}>
              <span className={styles.railKicker}>Gathered, then reduced</span>
              What is public now is a fraction of what has been collected — the
              rest is held until its evidence is complete.
            </div>
            <div className={styles.main}>
              <div className={styles.prose}>
                <p>{scaleLead}</p>
              </div>
              <div className={styles.figures}>
                {scaleFigures.map((f) => (
                  <div key={f.label} className={styles.figure}>
                    <div className={styles.figureValue} data-tone={f.tone}>
                      {f.value}
                    </div>
                    <div className={styles.figureLabel}>{f.label}</div>
                  </div>
                ))}
              </div>
              <p className={styles.scaleNote}>{scaleNote}</p>
            </div>
          </div>
        </section>

        {/* 5 — Contact & citation */}
        <section id="contact" className={styles.plate} data-tone="teal">
          <Band
            num="5"
            kicker="Contact & citation"
            title="Reach the project, and cite it."
            motif="rings"
          />
          <div className={styles.body} data-animate="body">
            <div className={styles.rail}>
              <span className={styles.railKicker}>Get in touch</span>
              Questions, corrections, and source leads are welcome through any of
              these.
            </div>
            <div className={styles.main}>
              <p className={styles.subLabel}>Contact</p>
              <dl className={styles.contact}>
                {contact.map((c) => (
                  <div key={c.label}>
                    <dt data-tone={c.tone}>{c.label}</dt>
                    <dd>
                      {c.links.map((l, i) => (
                        <Fragment key={l.text}>
                          {i > 0 ? <span className={styles.sep}> · </span> : null}
                          {l.href ? (
                            <a href={l.href} target="_blank" rel="noreferrer">
                              {l.text}
                            </a>
                          ) : (
                            l.text
                          )}
                        </Fragment>
                      ))}
                    </dd>
                  </div>
                ))}
              </dl>

              <p className={styles.subLabel}>How to cite this project</p>
              <div className={styles.citeGrid}>
                {citations.map((c) => (
                  <CitationCard
                    key={c.style}
                    tone={c.tone}
                    style={c.style}
                    text={c.text}
                  />
                ))}
              </div>
              <p className={styles.hint}>{citeHint}</p>
            </div>
          </div>
        </section>

        {/* 6 — Claim boundaries & rights */}
        <section id="boundaries" className={styles.plate} data-tone="ink">
          <Band
            num="6"
            kicker="Claim boundaries & rights"
            title="What the archive supports, and what it does not claim."
            motif="seal"
          />
          <div className={styles.body} data-animate="body">
            <div className={styles.rail}>
              <span className={styles.railKicker}>The honest edge</span>
              Each boundary is a deliberate limit, not a gap to be filled later
              by inference. Expand any row for detail.
            </div>
            <div className={styles.main}>
              <div className={styles.acc}>
                {claimBoundaries.map((b) => (
                  <details key={b.area} className={styles.accItem}>
                    <summary>
                      <span className={styles.accArea}>{b.area}</span>
                      <span className={styles.accSummary}>
                        <span className={styles.bTag}>Supports&nbsp;— </span>
                        {b.supports}
                      </span>
                    </summary>
                    <div className={styles.accBody}>
                      <span className={styles.bNot}>
                        <span className={styles.bTag}>Does not claim&nbsp;— </span>
                        {b.notClaim}
                      </span>
                    </div>
                  </details>
                ))}
              </div>

              <p className={styles.subLabel}>Rights</p>
              <div className={styles.prose}>
                <p>{rightsProse}</p>
              </div>
              <a href="/source" className={styles.sourceLink}>
                Full provenance &amp; permissions on Source
                <ArrowRight size={17} strokeWidth={3} aria-hidden="true" />
              </a>
            </div>
          </div>
        </section>

        <footer className={styles.footer}>
          <span>Modern Graphic Design Archive</span>
          <span>
            <a href={REPO_URL} target="_blank" rel="noreferrer">
              github.com/dpan538/graphic_design_archive
            </a>
          </span>
          <span>{footerNote}</span>
        </footer>
      </main>
    </div>
  );
}
