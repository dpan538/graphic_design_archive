"use client";

import { Fragment, useRef, useState } from "react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { ArrowRight } from "lucide-react";
import SiteNav from "@/components/site/SiteNav";
import styles from "./source.module.css";
import {
  ABOUT_URL,
  acquisitionChain,
  acquisitionMethods,
  acquisitionNotes,
  citationExample,
  citationPolicy,
  evidenceStatusLegend,
  evidenceStatusNote,
  integrityRecord,
  overviewLayers,
  overviewNote,
  overviewText,
  REPO_URL,
  registerGroups,
  reproNote,
  rightsColumns,
  rightsGlobalVisual,
  transformationCaveat,
  transformationCategories,
  versionRecord,
  type SourceEntry,
} from "./content";

gsap.registerPlugin(ScrollTrigger, useGSAP);

const SECTIONS: {
  id: string;
  n: string;
  sec: string;
  title: string;
  gloss: string;
  kicker: string;
}[] = [
  { id: "overview", n: "1", sec: "ink", title: "Source overview", kicker: "Read this first", gloss: "Four kinds of material, and why they must not be conflated." },
  { id: "register", n: "2", sec: "blue", title: "Source register", kicker: "The core inventory", gloss: "What each source is, and what the project does with it — held as separate properties." },
  { id: "provenance", n: "3", sec: "red", title: "Provenance & acquisition", kicker: "How it enters", gloss: "How material reaches the archive, and in what state it arrives." },
  { id: "transformation", n: "4", sec: "gold", title: "Editorial & data transformation", kicker: "Description, not inference", gloss: "How source values become fields. The record here is not a copy of the source." },
  { id: "rights", n: "5", sec: "green", title: "Rights & permissions", kicker: "What may be shown", gloss: "Metadata, text, and image are assessed separately, per source." },
  { id: "status", n: "6", sec: "teal", title: "Evidence & source status", kicker: "Not equally settled", gloss: "A legend for what each status means, and what it does not." },
  { id: "version", n: "7", sec: "coral", title: "Version & reproducibility", kicker: "Fixed and checkable", gloss: "What you see today, bound to a sealed release so it can be re-checked." },
  { id: "citation", n: "8", sec: "blue", title: "Source citation", kicker: "Cite the source first", gloss: "The original source, then the archive's provenance record." },
];

function SecHead({ s }: { s: (typeof SECTIONS)[number] }) {
  return (
    <div className={styles.secHead} data-reveal>
      <span className={styles.secNum}>{s.n}</span>
      <h2 className={styles.secTitle}>{s.title}</h2>
    </div>
  );
}

const ROLE_TONE: Record<string, string> = {
  "Object metadata": "blue",
  "Object corpus": "blue",
  "Creator attribution": "blue",
  Dating: "blue",
  "Object typing": "blue",
  Discovery: "coral",
  "Regional coverage": "teal",
  "Cultural-context reference": "coral",
  "Bibliographic evidence": "teal",
  "Rights reference": "green",
  "Local rights reference": "green",
  "Rights advisory reference": "green",
  "Public-domain reference": "green",
  "Classification reference": "gold",
  "Methodology reference": "teal",
  "Design reference": "gold",
  "TRACE evidence": "red",
  "TRACE data": "blue",
  Authority: "teal",
  "Open-image candidates": "green",
};

function Entry({ entry }: { entry: SourceEntry }) {
  return (
    <div className={styles.entry}>
      <div className={styles.entryTop}>
        <span className={styles.entryName}>{entry.name}</span>
        <span className={styles.entryOrg}>{entry.org}</span>
      </div>
      <div className={styles.tags}>
        <span className={styles.tag} data-kind="type">
          {entry.type}
        </span>
        {entry.role.map((r) => (
          <span key={r} className={styles.tag} data-tone={ROLE_TONE[r] ?? undefined}>
            {r}
          </span>
        ))}
      </div>
      <dl className={styles.entryGrid}>
        <dt>Coverage</dt>
        <dd>{entry.coverage}</dd>
        <dt>Material</dt>
        <dd>{entry.material}</dd>
        {entry.contribution ? (
          <>
            <dt>Contribution</dt>
            <dd>{entry.contribution}</dd>
          </>
        ) : null}
        <dt>Identifier</dt>
        <dd>{entry.identifier}</dd>
        <dt>Acquired</dt>
        <dd>{entry.acquired}</dd>
        <dt>Rights</dt>
        <dd>{entry.rights}</dd>
        <dt>Status</dt>
        <dd>
          <span className={styles.statusChip} data-s={entry.status}>
            {entry.status}
          </span>
        </dd>
      </dl>
    </div>
  );
}

const FILTERS = [
  { key: "all", label: "All" },
  { key: "archives", label: "Archives & Collections" },
  { key: "scholarly", label: "Scholarly Research" },
  { key: "datasets", label: "Datasets & Standards" },
  { key: "design", label: "Design References" },
];

export default function SourceView() {
  const root = useRef<HTMLDivElement>(null);
  const [filter, setFilter] = useState("all");
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({});

  useGSAP(
    () => {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      gsap.utils.toArray<HTMLElement>("[data-reveal]").forEach((el) => {
        gsap.from(el, {
          y: 12,
          duration: 0.55,
          ease: "power2.out",
          scrollTrigger: { trigger: el, start: "top 90%", once: true },
        });
      });
    },
    { scope: root },
  );

  const groups =
    filter === "all"
      ? registerGroups
      : registerGroups.filter((g) => g.key === filter);

  const S = Object.fromEntries(SECTIONS.map((s) => [s.id, s])) as Record<
    string,
    (typeof SECTIONS)[number]
  >;

  return (
    <div className={styles.page} ref={root}>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <SiteNav active="source" />

      <main id="main">
        <header className={styles.masthead}>
          <p className={styles.kicker}>
            Source
            <span className={styles.draftTag}>Working draft &middot; not final</span>
          </p>
          <h1 className={styles.title}>
            Provenance, rights, and research use of the archive&rsquo;s materials.
          </h1>
          <p className={styles.lead}>{overviewText}</p>
        </header>

        {/* 1 — Source overview */}
        <section id="overview" className={styles.section} data-sec="ink">
          <div className={styles.inner}>
            <SecHead s={S.overview} />
            <div className={styles.secGrid}>
              <div className={styles.gloss}>
                <span className={styles.glossKicker}>{S.overview.kicker}</span>
                {S.overview.gloss}
              </div>
              <div className={styles.secMain}>
                <p className={styles.subHead}>Four layers, kept distinct</p>
                <div className={styles.layers}>
                  {overviewLayers.map((l, i) => (
                    <div
                      key={l.n}
                      className={styles.layer}
                      data-tone={["blue", "green", "gold", "red"][i]}
                    >
                      <span className={styles.layerN}>{l.n}</span>
                      <h3>{l.label}</h3>
                      <p>{l.note}</p>
                    </div>
                  ))}
                </div>
                <div className={styles.statement}>
                  <p>{overviewNote}</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 2 — Source register */}
        <section id="register" className={styles.section} data-sec="blue">
          <div className={styles.inner}>
            <SecHead s={S.register} />
            <div className={styles.secGrid}>
              <div className={styles.gloss}>
                <span className={styles.glossKicker}>{S.register.kicker}</span>
                {S.register.gloss}
              </div>
              <div className={styles.secMain}>
                <div className={styles.prose}>
                  <p className={styles.dropcap}>
                    Each source carries what it is — its{" "}
                    <span className={styles.kw} data-tone="ink">source type</span> —
                    and what the project does with it — its{" "}
                    <span className={styles.kw} data-tone="blue">project role</span> —
                    as separate properties, so different kinds of material are not
                    flattened into one bibliography.
                  </p>
                </div>

                <div className={styles.filters} role="group" aria-label="Filter the register">
                  {FILTERS.map((f) => (
                    <button
                      key={f.key}
                      type="button"
                      className={styles.chip}
                      data-on={filter === f.key}
                      aria-pressed={filter === f.key}
                      onClick={() => setFilter(f.key)}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>

                {groups.map((g) => {
                  const isOpen = openGroups[g.key] ?? filter === g.key;
                  return (
                    <div key={g.key} className={styles.group}>
                      <div className={styles.groupHead}>
                        <h3>
                          {g.title}
                          <span className={styles.groupCount}>{g.entries.length}</span>
                        </h3>
                        <p className={styles.groupBlurb}>{g.blurb}</p>
                      </div>
                      <details
                        className={styles.details}
                        open={isOpen}
                        onToggle={(e) =>
                          setOpenGroups((s) => ({
                            ...s,
                            [g.key]: e.currentTarget.open,
                          }))
                        }
                      >
                        <summary>
                          {isOpen ? "Hide sources" : `Show ${g.entries.length} sources`}
                        </summary>
                        <div className={styles.detailsBody}>
                          <div className={styles.entries}>
                            {g.entries.map((e) => (
                              <Entry key={e.name} entry={e} />
                            ))}
                          </div>
                        </div>
                      </details>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </section>

        {/* 3 — Provenance & acquisition */}
        <section id="provenance" className={styles.section} data-sec="red">
          <div className={styles.inner}>
            <SecHead s={S.provenance} />
            <div className={styles.secGrid}>
              <div className={styles.gloss}>
                <span className={styles.glossKicker}>{S.provenance.kicker}</span>
                {S.provenance.gloss}
              </div>
              <div className={styles.secMain}>
                <div className={styles.prose}>
                  <p className={styles.dropcap}>
                    Nothing is published from a raw capture. Every record you can
                    read here has passed the chain below, and each source is held
                    as a{" "}
                    <span className={styles.kw} data-tone="red">frozen snapshot</span>{" "}
                    at the moment it was acquired.
                  </p>
                </div>
                <div className={styles.flow} aria-label="Acquisition chain">
                  {acquisitionChain.map((s, i) => (
                    <Fragment key={s}>
                      <span className={styles.flowStep}>{s}</span>
                      {i < acquisitionChain.length - 1 ? (
                        <span className={styles.flowArrow} aria-hidden="true">
                          →
                        </span>
                      ) : null}
                    </Fragment>
                  ))}
                </div>

                <details className={styles.details}>
                  <summary>Acquisition methods ({acquisitionMethods.length})</summary>
                  <div className={styles.detailsBody}>
                    <div className={styles.methods}>
                      {acquisitionMethods.map((m) => (
                        <div key={m.method} className={styles.method}>
                          <b>{m.method}</b>
                          <p>{m.note}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </details>

                <ul className={styles.notes}>
                  {acquisitionNotes.map((n) => (
                    <li key={n.slice(0, 24)}>{n}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* 4 — Editorial / data transformation */}
        <section id="transformation" className={styles.section} data-sec="gold">
          <div className={styles.inner}>
            <SecHead s={S.transformation} />
            <div className={styles.secGrid}>
              <div className={styles.gloss}>
                <span className={styles.glossKicker}>{S.transformation.kicker}</span>
                {S.transformation.gloss}
              </div>
              <div className={styles.secMain}>
                <div className={styles.prose}>
                  <p className={styles.dropcap}>
                    Database fields are not found in nature. Source values are
                    reshaped into consistent fields;{" "}
                    <span className={styles.kw} data-tone="ink">normalizing a value is describing it</span>,
                    not inferring something the source did not state.
                  </p>
                </div>
                <div className={styles.statement}>
                  <span className={styles.statementLabel}>Transformation is not inference</span>
                  <p>{transformationCaveat}</p>
                </div>
                <details className={styles.details}>
                  <summary>
                    Transformation categories ({transformationCategories.length})
                  </summary>
                  <div className={styles.detailsBody}>
                    <div className={styles.transforms}>
                      {transformationCategories.map((t) => (
                        <div key={t.name} className={styles.transform}>
                          <b>{t.name}</b>
                          <p>{t.example}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </details>
              </div>
            </div>
          </div>
        </section>

        {/* 5 — Rights & permissions */}
        <section id="rights" className={styles.section} data-sec="green">
          <div className={styles.inner}>
            <SecHead s={S.rights} />
            <div className={styles.secGrid}>
              <div className={styles.gloss}>
                <span className={styles.glossKicker}>{S.rights.kicker}</span>
                {S.rights.gloss}
              </div>
              <div className={styles.secMain}>
                <div className={styles.statement}>
                  <span className={styles.statementLabel}>Visual material</span>
                  <p>{rightsGlobalVisual}</p>
                </div>
                <div className={styles.cols3}>
                  {rightsColumns.map((cc, i) => (
                    <div
                      key={cc.key}
                      className={styles.rcol}
                      data-tone={["green", "blue", "red"][i]}
                    >
                      <h3>{cc.title}</h3>
                      <p>{cc.body}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 6 — Evidence & source status */}
        <section id="status" className={styles.section} data-sec="teal">
          <div className={styles.inner}>
            <SecHead s={S.status} />
            <div className={styles.secGrid}>
              <div className={styles.gloss}>
                <span className={styles.glossKicker}>{S.status.kicker}</span>
                {S.status.gloss}
              </div>
              <div className={styles.secMain}>
                <dl className={styles.legend}>
                  {evidenceStatusLegend.map((s) => (
                    <div key={s.status} className={styles.legendRow}>
                      <dt data-s={s.status}>{s.status}</dt>
                      <dd>{s.meaning}</dd>
                    </div>
                  ))}
                </dl>
                <div className={styles.statement}>
                  <p>{evidenceStatusNote}</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 7 — Version & reproducibility */}
        <section id="version" className={styles.section} data-sec="coral">
          <div className={styles.inner}>
            <SecHead s={S.version} />
            <div className={styles.secGrid}>
              <div className={styles.gloss}>
                <span className={styles.glossKicker}>{S.version.kicker}</span>
                {S.version.gloss}
              </div>
              <div className={styles.secMain}>
                <dl className={styles.vled}>
                  {versionRecord.map((v) => (
                    <div key={v.label} className={styles.vrow}>
                      <dt>{v.label}</dt>
                      <dd>{v.value}</dd>
                    </div>
                  ))}
                </dl>
                <details className={styles.details}>
                  <summary>Integrity record</summary>
                  <div className={styles.integrity}>
                    <dl>
                      {integrityRecord.map((r) => (
                        <div key={r.label} className={styles.irow}>
                          <dt>{r.label}</dt>
                          <dd>{r.value}</dd>
                        </div>
                      ))}
                    </dl>
                    <p className={styles.reproNote}>{reproNote}</p>
                  </div>
                </details>
              </div>
            </div>
          </div>
        </section>

        {/* 8 — Source citation */}
        <section id="citation" className={styles.section} data-sec="blue">
          <div className={styles.inner}>
            <SecHead s={S.citation} />
            <div className={styles.secGrid}>
              <div className={styles.gloss}>
                <span className={styles.glossKicker}>{S.citation.kicker}</span>
                {S.citation.gloss}
              </div>
              <div className={styles.secMain}>
                <div className={styles.prose}>
                  <p className={styles.dropcap}>{citationPolicy}</p>
                </div>
                <div className={styles.citeBlocks}>
                  {citationExample.map((cc) => (
                    <div key={cc.label} className={styles.citeBlock}>
                      <b>{cc.label}</b>
                      <p>{cc.text}</p>
                    </div>
                  ))}
                </div>
                <a href={`${ABOUT_URL}#cite`} className={styles.aboutLink}>
                  How to cite the archive itself — About
                  <ArrowRight size={16} strokeWidth={3} aria-hidden="true" />
                </a>
              </div>
            </div>
          </div>
        </section>

        <footer className={styles.footer}>
          <span>
            <a href={ABOUT_URL}>Read full methodology &amp; claim boundaries — About</a>
          </span>
          <span>
            <a href={REPO_URL} target="_blank" rel="noreferrer">
              github.com/dpan538/graphic_design_archive
            </a>
          </span>
        </footer>
      </main>
    </div>
  );
}
