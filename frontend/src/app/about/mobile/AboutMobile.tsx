"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import SiteNavMobile from "@/components/site/mobile/SiteNavMobile";
import TopButton from "@/components/site/mobile/TopButton";
import shell from "@/components/site/mobile/MobileShell.module.css";
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
  rightsProse,
  scaleFigures,
  scaleLead,
  scaleNote,
  typeSystem,
  visualReferences,
} from "../content";
import {
  acquisitionChain,
  acquisitionMethods,
  acquisitionNotes,
  evidenceStatusLegend,
  evidenceStatusNote,
  integrityRecord,
  overviewLayers,
  overviewNote,
  overviewText,
  registerGroups,
  reproNote,
  rightsColumns,
  rightsGlobalVisual,
  rightsIntro,
  statusIntro,
  transformationCategories,
  transformationCaveat,
  versionIntro,
  versionRecord,
} from "../../source/content";
import styles from "./AboutMobile.module.css";

/* About, mobile (§4a; owner 2026-09-06): its own tree, sharing only the
   content modules. The section order is the owner's: Purpose · Methodology
   (the research approach) · Visual design rationale · The archive in
   numbers · Contact & citation · Source (the desktop /source page, folded in
   here — provenance, register, acquisition, transformation, rights, evidence
   status, version) · Claim boundaries & rights. Every section opens on a
   colour plate with its cropped numeral, its kicker and title; below, paper
   and ink. Long matter folds by default; nothing is dropped. */

type Tone = "blue" | "red" | "yellow" | "green" | "teal" | "coral" | "night";

const SECTIONS: { id: string; n: string; sec: Tone; kicker: string; title: string }[] = [
  { id: "purpose", n: "1", sec: "blue", kicker: "Purpose", title: "An archive made to be read, located, and explored." },
  { id: "methodology", n: "2", sec: "red", kicker: "Methodology · research approach", title: "Provenance before interpretation." },
  { id: "visual", n: "3", sec: "yellow", kicker: "Visual design rationale", title: "One idea per cover, set like a stamp." },
  { id: "scale", n: "4", sec: "green", kicker: "The archive in numbers", title: "A large raw pool, cleaned to a verified core." },
  { id: "contact", n: "5", sec: "teal", kicker: "Contact & citation", title: "Reach the project, and cite it." },
  { id: "source", n: "6", sec: "coral", kicker: "Source", title: "Where the material comes from, and on what terms." },
  { id: "boundaries", n: "7", sec: "night", kicker: "Claim boundaries & rights", title: "What the archive supports, and what it does not claim." },
];

function Mark({ id }: { id: string }) {
  const common = { viewBox: "0 0 120 66", className: styles.mark, fill: "none", stroke: "currentColor", strokeWidth: 3.5, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, "aria-hidden": true };
  switch (id) {
    case "purpose":
      return <svg {...common}><circle cx={60} cy={33} r={27} /><circle cx={60} cy={33} r={17} /><circle cx={60} cy={33} r={8} /><circle cx={60} cy={33} r={2.5} fill="currentColor" /></svg>;
    case "methodology":
      return <svg {...common}>{[0, 1, 2, 3, 4].map((i) => <rect key={i} x={8 + i * 22} y={12 + (i % 2) * 4} width={15} height={42 - (i % 2) * 8} rx={7.5} />)}</svg>;
    case "visual":
      return <svg {...common}><circle cx={60} cy={33} r={22} /><path d="M60 3 v60 M30 33 h60" /><path d="M60 33 h22 a22 22 0 0 1 -22 22 z" fill="currentColor" stroke="none" /></svg>;
    case "scale":
      return <svg {...common}><path d="M8 58 h104" />{[[14, 14], [34, 26], [54, 20], [74, 42], [94, 34]].map(([x, h]) => <rect key={x} x={x} y={58 - h} width={12} height={h} rx={4} />)}</svg>;
    case "contact":
      return <svg {...common}><circle cx={46} cy={33} r={23} /><circle cx={74} cy={33} r={23} /></svg>;
    case "source":
      return <svg {...common}><path d="M16 12 h88 M16 33 h88 M16 54 h88" /><circle cx={16} cy={12} r={4} fill="currentColor" /><circle cx={16} cy={33} r={4} fill="currentColor" /><circle cx={16} cy={54} r={4} fill="currentColor" /></svg>;
    case "boundaries":
      return <svg {...common}><circle cx={60} cy={33} r={27} /><circle cx={60} cy={33} r={17} /><path d="M8 33 h104" /></svg>;
    default:
      return null;
  }
}

function Plate({ s }: { s: (typeof SECTIONS)[number] }) {
  return (
    <div className={styles.plate} data-sec={s.sec}>
      <span className={styles.plateNum} aria-hidden="true">{s.n}</span>
      <div className={styles.plateText}>
        <p className={styles.kicker}>{s.kicker}</p>
        <h2 className={styles.title}>{s.title}</h2>
      </div>
      <Mark id={s.id} />
    </div>
  );
}

/* fold by default: the matter stays on the page, behind one 48 px control */
function Fold({ label, children, open = false }: { label: string; children: ReactNode; open?: boolean }) {
  return (
    <details className={styles.fold} open={open || undefined}>
      <summary className={styles.foldHead}>{label}</summary>
      <div className={styles.foldBody}>{children}</div>
    </details>
  );
}

function CopyButton({ text }: { text: string }) {
  const [done, setDone] = useState(false);
  return (
    <button
      type="button"
      className={styles.copy}
      onClick={() => {
        void navigator.clipboard?.writeText(text).then(() => { setDone(true); setTimeout(() => setDone(false), 1600); });
      }}
    >
      {done ? "Copied" : "Copy"}
    </button>
  );
}

export default function AboutMobile({ focus }: { focus?: "source" }) {
  /* the citations carry today's access date; they are built after mount so the server and the client agree */
  const [citations, setCitations] = useState<readonly { readonly tone: string; readonly style: string; readonly text: string }[]>([]);
  useEffect(() => { setCitations(buildCitations(new Date())); }, []);
  useEffect(() => {
    if (!focus) return;
    document.getElementById(focus)?.scrollIntoView({ block: "start" });
  }, [focus]);
  const S = useMemo(() => Object.fromEntries(SECTIONS.map((s) => [s.id, s])) as Record<string, (typeof SECTIONS)[number]>, []);

  return (
    <div className={`${shell.shell} ${styles.page}`}>
      <a href="#main" className="skip-link">Skip to content</a>
      <SiteNavMobile active="about" />

      <main id="main" className={styles.main}>
        <header className={styles.masthead}>
          <p className={styles.eyebrow}>About</p>
          <h1 className={styles.statement}>{openingStatement}</h1>
          <p className={styles.lead}>{openingLead}</p>
          <p className={styles.meta}>{openingMeta}</p>
          <nav className={styles.contents} aria-label="Sections">
            <ol role="list">
              {SECTIONS.map((s) => (
                <li key={s.id}><a href={`#${s.id}`}><span className={styles.contentsNum} data-sec={s.sec}>{s.n}</span>{s.kicker}</a></li>
              ))}
            </ol>
          </nav>
        </header>

        {/* 1 · Purpose */}
        <section id="purpose" className={styles.section} data-sec={S.purpose.sec}>
          <Plate s={S.purpose} />
          <div className={styles.body}>
            <p className={styles.prose}>{purposeLead}</p>
            <ul role="list" className={styles.cards}>
              {audiences.map((a) => (
                <li key={a.title} className={styles.card} data-tone={a.tone}>
                  <p className={styles.cardTitle}>{a.title}</p>
                  <p className={styles.cardBody}>{a.body}</p>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* 2 · Methodology — the research approach */}
        <section id="methodology" className={styles.section} data-sec={S.methodology.sec}>
          <Plate s={S.methodology} />
          <div className={styles.body}>
            {methodProse.map((p) => <p key={p.slice(0, 24)} className={styles.prose}>{p}</p>)}
            <p className={styles.subhead}>Pipeline</p>
            <ol role="list" className={styles.pipeline}>
              {pipelineStages.map((stage, i) => <li key={stage}><span className={styles.stageNum}>{i + 1}</span>{stage}</li>)}
            </ol>
            <Fold label="Evidence protocol" open>
              <dl className={styles.defs}>
                {evidenceProtocol.map((e) => (
                  <div key={e.term}><dt>{e.term}</dt><dd>{e.def}</dd></div>
                ))}
              </dl>
            </Fold>
            <p className={styles.prose}>{designResearchNote}</p>
          </div>
        </section>

        {/* 3 · Visual design rationale */}
        <section id="visual" className={styles.section} data-sec={S.visual.sec}>
          <Plate s={S.visual} />
          <div className={styles.body}>
            <p className={styles.prose}>{rationaleLead}</p>
            {/* six references as small folded cards: the name and the line stand,
                the reading opens on a tap (owner, 2026-09-06) */}
            <ul role="list" className={styles.refs}>
              {visualReferences.map((r) => (
                <li key={r.title}>
                  <details className={styles.ref} data-tone={r.tone}>
                    <summary className={styles.refHead}>
                      <span className={styles.refTitle}>{r.title}</span>
                      <span className={styles.refMeta}>{r.meta}</span>
                    </summary>
                    <p className={styles.refBody}>{r.body}</p>
                  </details>
                </li>
              ))}
            </ul>
            <Fold label="Type system">
              <dl className={styles.defs}>
                {typeSystem.map((t) => (
                  <div key={t.role}><dt>{t.role}</dt><dd>{t.face}</dd></div>
                ))}
              </dl>
            </Fold>
          </div>
        </section>

        {/* 4 · The archive in numbers */}
        <section id="scale" className={styles.section} data-sec={S.scale.sec}>
          <Plate s={S.scale} />
          <div className={styles.body}>
            <p className={styles.prose}>{scaleLead}</p>
            <ul role="list" className={styles.figures}>
              {scaleFigures.map((f) => (
                <li key={f.label} className={styles.figure} data-tone={f.tone}>
                  <span className={styles.figureValue}>{f.value}</span>
                  <span className={styles.figureLabel}>{f.label}</span>
                </li>
              ))}
            </ul>
            <p className={styles.prose}>{scaleNote}</p>
          </div>
        </section>

        {/* 5 · Contact & citation */}
        <section id="contact" className={styles.section} data-sec={S.contact.sec}>
          <Plate s={S.contact} />
          <div className={styles.body}>
            <dl className={styles.defs}>
              {contact.map((c) => (
                <div key={c.label}>
                  <dt data-tone={c.tone}>{c.label}</dt>
                  <dd>
                    {c.links.map((l, i) => (
                      <span key={l.text}>
                        {i > 0 ? " · " : null}
                        {l.href ? <a href={l.href} className={styles.link}>{l.text}</a> : l.text}
                      </span>
                    ))}
                  </dd>
                </div>
              ))}
            </dl>
            <p className={styles.subhead} id="cite">Cite this archive</p>
            <p className={styles.prose}>{citeHint}</p>
            <ul role="list" className={styles.cites}>
              {citations.map((c) => (
                <li key={c.style} className={styles.cite} data-tone={c.tone}>
                  <p className={styles.citeStyle}>{c.style}</p>
                  <p className={styles.citeText}>{c.text}</p>
                  <CopyButton text={c.text} />
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* 6 · Source — the desktop's own page, folded into About on the phone */}
        <section id="source" className={styles.section} data-sec={S.source.sec}>
          <Plate s={S.source} />
          <div className={styles.body}>
            <p className={styles.prose}>{overviewText}</p>
            <ol role="list" className={styles.layers}>
              {overviewLayers.map((l) => (
                <li key={l.n}><span className={styles.stageNum}>{l.n}</span><span><b>{l.label}</b> — {l.note}</span></li>
              ))}
            </ol>
            <p className={styles.prose}>{overviewNote}</p>
            <p className={styles.subhead}>Source register</p>
            {registerGroups.map((g) => (
              <Fold key={g.key} label={`${g.title} · ${g.entries.length}`}>
                <p className={styles.small}>{g.blurb}</p>
                <ul role="list" className={styles.register}>
                  {g.entries.map((e) => (
                    <li key={`${e.name}-${e.org}`} className={styles.entry}>
                      <p className={styles.entryName}>{e.name}</p>
                      <p className={styles.entryMeta}>{[e.org, e.type, e.coverage].filter(Boolean).join(" · ")}</p>
                      <p className={styles.entryMeta}><span className={styles.pill}>{e.status}</span> {e.rights}</p>
                    </li>
                  ))}
                </ul>
              </Fold>
            ))}
            <Fold label="Acquisition">
              <ol role="list" className={styles.pipeline}>
                {acquisitionChain.map((step, i) => <li key={step}><span className={styles.stageNum}>{i + 1}</span>{step}</li>)}
              </ol>
              <dl className={styles.defs}>
                {acquisitionMethods.map((m) => <div key={m.method}><dt>{m.method}</dt><dd>{m.note}</dd></div>)}
              </dl>
              {acquisitionNotes.map((n) => <p key={n.slice(0, 24)} className={styles.small}>{n}</p>)}
            </Fold>
            <Fold label="Transformation record">
              <dl className={styles.defs}>
                {transformationCategories.map((t) => <div key={t.name}><dt>{t.name}</dt><dd>{t.example}</dd></div>)}
              </dl>
              <p className={styles.small}>{transformationCaveat}</p>
            </Fold>
            <Fold label="Rights conditions" open>
              <p className={styles.small}>{rightsIntro}</p>
              <p className={styles.small}><b>{rightsGlobalVisual}</b></p>
              <dl className={styles.defs}>
                {rightsColumns.map((c) => <div key={c.key}><dt>{c.title}</dt><dd>{c.body}</dd></div>)}
              </dl>
            </Fold>
            <Fold label="Evidence & source status">
              <p className={styles.small}>{statusIntro}</p>
              <dl className={styles.defs}>
                {evidenceStatusLegend.map((l) => <div key={l.status}><dt>{l.status}</dt><dd>{l.meaning}</dd></div>)}
              </dl>
              <p className={styles.small}>{evidenceStatusNote}</p>
            </Fold>
            <Fold label="Version & reproducibility">
              <p className={styles.small}>{versionIntro}</p>
              <dl className={styles.defs}>
                {versionRecord.map((r) => <div key={r.label}><dt>{r.label}</dt><dd>{r.value}</dd></div>)}
              </dl>
              <dl className={`${styles.defs} ${styles.mono}`}>
                {integrityRecord.map((r) => <div key={r.label}><dt>{r.label}</dt><dd>{r.value}</dd></div>)}
              </dl>
              <p className={styles.small}>{reproNote}</p>
            </Fold>
          </div>
        </section>

        {/* 7 · Claim boundaries & rights */}
        <section id="boundaries" className={styles.section} data-sec={S.boundaries.sec}>
          <Plate s={S.boundaries} />
          <div className={styles.body}>
            <ul role="list" className={styles.claims}>
              {claimBoundaries.map((c) => (
                <li key={c.area} className={styles.claim}>
                  <p className={styles.claimArea}>{c.area}</p>
                  <p className={styles.claimLine}><span className={styles.claimKey}>Supports</span>{c.supports}</p>
                  <p className={styles.claimLine}><span className={styles.claimKey} data-no>Does not claim</span>{c.notClaim}</p>
                </li>
              ))}
            </ul>
            <p className={styles.prose}>{rightsProse}</p>
            <p className={styles.foot}>{footerNote}</p>
          </div>
        </section>
      </main>

      <TopButton />
    </div>
  );
}
