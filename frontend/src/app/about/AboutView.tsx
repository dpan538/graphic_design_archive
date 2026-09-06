"use client";

import ImplementationNote from "@/components/site/ImplementationNote";

import { Fragment, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
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
  rationaleLead,
  REPO_URL,
  rightsProse,
  scaleFigures,
  scaleLead,
  scaleNote,
  typeSystem,
  visualReferences,
} from "./content";

/* About — set like Source, like the rest of the sheet (FRONTEND_DESIGN_DECISION.md
   §7a): each section opens on a solid colour plate carrying its numeral
   oversized and cropped by the plate's edge, its title in the heavy rounded
   face, and one small line-drawn mark; below the plate, paper and ink, with
   the section's colour returned as pills, discs and colour heads. The last
   section turns the sheet over: a yellow plate on an ink ground. Nothing
   moves on scroll. */

type Tone = "blue" | "red" | "yellow" | "green" | "teal" | "night";

const SECTIONS: { id: string; n: string; sec: Tone; kicker: string; title: string }[] = [
  { id: "purpose", n: "1", sec: "blue", kicker: "Purpose", title: "An archive made to be read, located, and explored." },
  { id: "methodology", n: "2", sec: "red", kicker: "Methodology", title: "Provenance before interpretation." },
  { id: "visual", n: "3", sec: "yellow", kicker: "Visual design rationale", title: "One idea per cover, set like a stamp." },
  { id: "scale", n: "4", sec: "green", kicker: "The archive in numbers", title: "A large raw pool, cleaned to a verified core." },
  { id: "contact", n: "5", sec: "teal", kicker: "Contact & citation", title: "Reach the project, and cite it." },
  { id: "boundaries", n: "6", sec: "night", kicker: "Claim boundaries & rights", title: "What the archive supports, and what it does not claim." },
];

/* one line-drawn mark per section — the only thing that changes down the page */
function Mark({ id }: { id: string }) {
  const common = {
    viewBox: "0 0 200 110",
    className: styles.plateMark,
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 4,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };
  switch (id) {
    case "purpose": // reading: rings around a point
      return (
        <svg {...common}>
          <circle cx={100} cy={55} r={46} />
          <circle cx={100} cy={55} r={30} />
          <circle cx={100} cy={55} r={14} />
          <circle cx={100} cy={55} r={4} fill="currentColor" />
        </svg>
      );
    case "methodology": // gates, one after another
      return (
        <svg {...common}>
          {[0, 1, 2, 3, 4].map((i) => (
            <rect key={i} x={12 + i * 37} y={20 + (i % 2) * 6} width={26} height={70 - (i % 2) * 12} rx={13} />
          ))}
        </svg>
      );
    case "visual": // a registration mark
      return (
        <svg {...common}>
          <circle cx={100} cy={55} r={36} />
          <path d="M100 4 v102 M49 55 h102" />
          <path d="M100 55 h36 a36 36 0 0 1 -36 36 z" fill="currentColor" stroke="none" />
        </svg>
      );
    case "scale": // bars on a baseline
      return (
        <svg {...common}>
          <path d="M14 96 h172" />
          {[
            [24, 22],
            [58, 44],
            [92, 34],
            [126, 70],
            [160, 56],
          ].map(([x, h]) => (
            <rect key={x} x={x} y={96 - h} width={20} height={h} rx={6} />
          ))}
        </svg>
      );
    case "contact": // two rings, linked
      return (
        <svg {...common}>
          <circle cx={78} cy={55} r={38} />
          <circle cx={122} cy={55} r={38} />
        </svg>
      );
    case "boundaries": // a seal, and a line drawn through it
      return (
        <svg {...common}>
          <circle cx={100} cy={55} r={46} />
          <circle cx={100} cy={55} r={30} />
          <path d="M14 55 h172" />
        </svg>
      );
    default:
      return null;
  }
}

function Plate({ s }: { s: (typeof SECTIONS)[number] }) {
  return (
    <div className={styles.plate}>
      <span className={styles.plateNum} aria-hidden="true">
        {s.n}
      </span>
      <div className={styles.plateText}>
        <span className={styles.plateKicker}>
          Section {s.n} · {s.kicker}
        </span>
        <h2 className={styles.plateTitle}>{s.title}</h2>
      </div>
      <Mark id={s.id} />
    </div>
  );
}

/* the pull-statement: a solid stub with one cropped glyph, an outlined body */
function Statement({ label, children }: { label?: string; children: ReactNode }) {
  return (
    <div className={styles.statement}>
      <span className={styles.stub} aria-hidden="true">
        <span className={styles.stubGlyph}>&ldquo;</span>
      </span>
      <div className={styles.statementBody}>
        {label ? <span className={styles.statementLabel}>{label}</span> : null}
        <p>{children}</p>
      </div>
    </div>
  );
}

const FlowArrow = () => (
  <svg className={styles.flowArrow} viewBox="0 0 28 20" aria-hidden="true">
    <path d="M2 10 h22 m-8 -8 l8 8 l-8 8" fill="none" stroke="currentColor" strokeWidth={3.5} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

function CitationCard({ tone, style, text }: { tone: string; style: string; text: string }) {
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
        <button type="button" className={styles.copyBtn} data-copied={copied || undefined} onClick={copy} aria-label={`Copy ${style} citation`}>
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <p className={styles.citeText}>{text}</p>
    </article>
  );
}

export default function AboutView() {
  /* the access date in the citations is today's; the first render uses a
     fixed date so server and client agree, then the real one takes over */
  const [accessDate, setAccessDate] = useState<Date>(() => new Date("2026-08-30T00:00:00"));
  useEffect(() => setAccessDate(new Date()), []);
  const citations = useMemo(() => buildCitations(accessDate), [accessDate]);

  const S = Object.fromEntries(SECTIONS.map((s) => [s.id, s])) as Record<string, (typeof SECTIONS)[number]>;

  return (
    <div className={styles.page}>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <SiteNav active="about" />

      <main id="main">
        <header className={styles.masthead}>
          <div className={styles.mastText}>
            <p className={styles.kicker}>About</p>
            <h1 className={styles.title}>{openingStatement}</h1>
            <p className={styles.lead}>{openingLead}</p>
            <p className={styles.meta}>{openingMeta}</p>
          </div>
          <div className={styles.stamp} aria-hidden="true">
            <span className={styles.stampLine}>Modern Graphic Design Archive</span>
            <span className={styles.stampWords}>
              <span className={styles.stampWord} data-row="tail">ABOUT</span>
              <span className={styles.stampWord} data-row="head">ABOUT</span>
            </span>
            <span className={styles.stampFoot}>Brisbane · since 2024</span>
          </div>
        </header>

        {/* 1 — Purpose */}
        <section id="purpose" className={styles.section} data-sec={S.purpose.sec}>
          <div className={styles.inner}>
            <Plate s={S.purpose} />
            <div className={styles.secGrid}>
              <div className={styles.gloss}>
                <span className={styles.glossKicker}>What it is for</span>
                Reading objects in context, locating them by place and period, and exploring how the evidence connects.
              </div>
              <div className={styles.secMain}>
                <Statement>{purposeLead}</Statement>
                <p className={styles.subHead}>Audiences</p>
                <div className={styles.grid3}>
                  {audiences.map((a) => (
                    <div key={a.title} className={styles.card} data-tone={a.tone}>
                      <span className={styles.cardDisc} aria-hidden="true" />
                      <h3>{a.title}</h3>
                      <p>{a.body}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 2 — Methodology */}
        <section id="methodology" className={styles.section} data-sec={S.methodology.sec}>
          <div className={styles.inner}>
            <Plate s={S.methodology} />
            <div className={styles.secGrid}>
              <div className={styles.gloss}>
                <span className={styles.glossKicker}>Archive &amp; research method</span>
                Gathering is not publishing. Every record you can read here has passed source, rights, classification, completeness, and
                reading gates.
              </div>
              <div className={styles.secMain}>
                <div className={styles.prose}>
                  {methodProse.map((p, i) => (
                    <p key={p.slice(0, 24)} className={i === 0 ? styles.dropcap : undefined}>
                      {p}
                    </p>
                  ))}
                </div>

                <ImplementationNote />
                <p className={styles.subHead}>Evidence protocol</p>
                <dl className={styles.defs}>
                  {evidenceProtocol.map((e, i) => (
                    <div key={e.term} className={styles.def}>
                      <span className={styles.defN} aria-hidden="true">
                        {i + 1}
                      </span>
                      <dt>{e.term}</dt>
                      <dd>{e.def}</dd>
                    </div>
                  ))}
                </dl>

                <p className={styles.subHead}>How a record reaches the page</p>
                <div className={styles.flow} aria-label="Production pipeline">
                  {pipelineStages.map((step, i) => (
                    <Fragment key={step}>
                      <span className={styles.flowStep}>{step}</span>
                      {i < pipelineStages.length - 1 ? <FlowArrow /> : null}
                    </Fragment>
                  ))}
                </div>

                <Statement label="The interface is part of the method">{designResearchNote}</Statement>
              </div>
            </div>
          </div>
        </section>

        {/* 3 — Visual design rationale */}
        <section id="visual" className={styles.section} data-sec={S.visual.sec}>
          <div className={styles.inner}>
            <Plate s={S.visual} />
            <div className={styles.secGrid}>
              <div className={styles.gloss}>
                <span className={styles.glossKicker}>Combined, not copied</span>
                Six references — three of them from one record label — synthesised into one language for reading evidence.
              </div>
              <div className={styles.secMain}>
                <div className={styles.prose}>
                  <p className={styles.dropcap}>{rationaleLead}</p>
                  <p>
                    The centre of it is <span className={styles.kw} data-tone="red">Columbia Records</span> between 1940 and 1960:
                    Alex Steinweiss&rsquo;s one idea per cover, S. Neil Fujita&rsquo;s painted fields of colour, and Jim Flora&rsquo;s
                    crowds of figures. The <span className={styles.kw} data-tone="green">postage stamp</span> gives that idiom its
                    economy — a field, a cropped figure, a small device; the{" "}
                    <span className={styles.kw} data-tone="blue">pictogram</span> gives the crowd its grid; and the
                    engraver&rsquo;s line gives the opening circles their hand.
                  </p>
                </div>

                <p className={styles.subHead}>References</p>
                <div className={styles.refs}>
                  {visualReferences.map((r) => (
                    <div key={r.title} className={styles.ref} data-tone={r.tone}>
                      <h3 className={styles.refHead}>{r.title}</h3>
                      <div className={styles.refBody}>
                        <p className={styles.refMeta}>{r.meta}</p>
                        <p>{r.body}</p>
                      </div>
                    </div>
                  ))}
                </div>

                <p className={styles.subHead}>Type system</p>
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
          </div>
        </section>

        {/* 4 — Scale */}
        <section id="scale" className={styles.section} data-sec={S.scale.sec}>
          <div className={styles.inner}>
            <Plate s={S.scale} />
            <div className={styles.secGrid}>
              <div className={styles.gloss}>
                <span className={styles.glossKicker}>Gathered, then reduced</span>
                What is public now is a fraction of what has been collected — the rest is held until its evidence is complete.
              </div>
              <div className={styles.secMain}>
                <div className={styles.prose}>
                  <p className={styles.dropcap}>{scaleLead}</p>
                </div>
                <div className={styles.figures}>
                  {scaleFigures.map((f) => (
                    <div key={f.label} className={styles.figure} data-tone={f.tone}>
                      <div className={styles.figureValue}>{f.value}</div>
                      <div className={styles.figureLabel}>{f.label}</div>
                    </div>
                  ))}
                </div>
                <Statement label="Coverage">{scaleNote}</Statement>
              </div>
            </div>
          </div>
        </section>

        {/* 5 — Contact & citation */}
        <section id="contact" className={styles.section} data-sec={S.contact.sec}>
          <div className={styles.inner}>
            <Plate s={S.contact} />
            <div className={styles.secGrid}>
              <div className={styles.gloss}>
                <span className={styles.glossKicker}>Get in touch</span>
                Questions, corrections, and source leads are welcome through any of these.
              </div>
              <div className={styles.secMain}>
                <p className={styles.subHead}>Contact</p>
                <dl className={styles.contact}>
                  {contact.map((c) => (
                    <div key={c.label} className={styles.contactRow}>
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

                <p className={styles.subHead} id="cite">
                  How to cite this project
                </p>
                <div className={styles.citeGrid}>
                  {citations.map((c) => (
                    <CitationCard key={c.style} tone={c.tone} style={c.style} text={c.text} />
                  ))}
                </div>
                <p className={styles.hint}>{citeHint}</p>
              </div>
            </div>
          </div>
        </section>

        {/* 6 — Claim boundaries & rights: the sheet turned over */}
        <section id="boundaries" className={styles.section} data-sec={S.boundaries.sec}>
          <div className={styles.inner}>
            <Plate s={S.boundaries} />
            <div className={styles.secGrid}>
              <div className={styles.gloss}>
                <span className={styles.glossKicker}>The honest edge</span>
                Each boundary is a deliberate limit, not a gap to be filled later by inference. Open any row for what is not claimed.
              </div>
              <div className={styles.secMain}>
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
                        <span className={styles.bTag}>Does not claim&nbsp;— </span>
                        {b.notClaim}
                      </div>
                    </details>
                  ))}
                </div>

                <p className={styles.subHead}>Rights</p>
                <div className={styles.prose}>
                  <p>{rightsProse}</p>
                </div>
                <a href="/source" className={styles.sourceLink}>
                  Full provenance &amp; permissions on Source
                  <ArrowRight size={18} strokeWidth={3} aria-hidden="true" />
                </a>
              </div>
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
