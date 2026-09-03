"use client";

import { Fragment, useState, type ReactNode } from "react";
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
  rightsIntro,
  statusIntro,
  versionIntro,
  transformationCaveat,
  transformationCategories,
  versionRecord,
  type SourceEntry,
} from "./content";

/* The Source page — an academic reference appendix set like a sheet of
   stamps (FRONTEND_DESIGN_DECISION.md §7a, second register): each section
   opens on a solid colour PLATE carrying its numeral oversized and cropped
   by the plate's edge, its title in the heavy rounded face, and one small
   line-drawn mark of its own. Colour is a field, not a rule; type is
   heavy; corners are round; every label sits on the 17px floor. Nothing
   moves on scroll — the marks change from section to section instead. */

type Tone = "yellow" | "blue" | "red" | "ink" | "green" | "teal" | "coral" | "sky";

const SECTIONS: {
  id: string;
  n: string;
  sec: Tone;
  title: string;
  gloss: string;
  kicker: string;
}[] = [
  { id: "overview", n: "1", sec: "yellow", title: "Source overview", kicker: "Read this first", gloss: "Four kinds of material, and why they must not be conflated." },
  { id: "register", n: "2", sec: "blue", title: "Source register", kicker: "The core inventory", gloss: "What each source is, and what the project does with it — held as separate properties." },
  { id: "provenance", n: "3", sec: "red", title: "Provenance & acquisition", kicker: "How it enters", gloss: "How material reaches the archive, and in what state it arrives." },
  { id: "transformation", n: "4", sec: "ink", title: "Editorial & data transformation", kicker: "Description, not inference", gloss: "How source values become fields. The record here is not a copy of the source." },
  { id: "rights", n: "5", sec: "green", title: "Rights & permissions", kicker: "What may be shown", gloss: "Metadata, text, and image are assessed separately, per source." },
  { id: "status", n: "6", sec: "teal", title: "Evidence & source status", kicker: "Not equally settled", gloss: "A legend for what each status means, and what it does not." },
  { id: "version", n: "7", sec: "coral", title: "Version & reproducibility", kicker: "Fixed and checkable", gloss: "What you see today, bound to a sealed release so it can be re-checked." },
  { id: "citation", n: "8", sec: "sky", title: "Source citation", kicker: "Cite the source first", gloss: "The original source, then the archive's provenance record." },
];

/* One mark per section, drawn in a single line weight — the stamp's small
   device (the SOZPHILEX waves, the EFTA rule). They are the only thing
   that changes as the reader scrolls. */
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
    case "overview":
      return (
        <svg {...common}>
          <path d="M20 100 A80 80 0 0 1 180 100" />
          <path d="M40 100 A60 60 0 0 1 160 100" />
          <path d="M60 100 A40 40 0 0 1 140 100" />
          <path d="M80 100 A20 20 0 0 1 120 100" />
        </svg>
      );
    case "register":
      return (
        <svg {...common}>
          {[0, 1, 2].map((r) =>
            [0, 1, 2, 3, 4].map((c) => (
              <circle key={`${r}${c}`} cx={28 + c * 36} cy={19 + r * 36} r={7} fill={r === 0 && c < 3 ? "currentColor" : "none"} />
            )),
          )}
        </svg>
      );
    case "provenance":
      return (
        <svg {...common}>
          <path d="M12 28 q22 -20 44 0 t44 0 t44 0 t44 0" />
          <path d="M12 55 q22 -20 44 0 t44 0 t44 0 t44 0" />
          <path d="M12 82 q22 -20 44 0 t44 0 t44 0 t44 0" />
        </svg>
      );
    case "transformation":
      return (
        <svg {...common}>
          <rect x={18} y={27} width={56} height={56} rx={8} />
          <path d="M92 55 h34 m-12 -12 l12 12 l-12 12" />
          <circle cx={160} cy={55} r={28} />
        </svg>
      );
    case "rights":
      return (
        <svg {...common}>
          <rect x={14} y={14} width={172} height={18} rx={9} />
          <rect x={14} y={46} width={118} height={18} rx={9} />
          <rect x={14} y={78} width={64} height={18} rx={9} />
        </svg>
      );
    case "status":
      return (
        <svg {...common}>
          {[0, 1, 2, 3, 4].map((i) => (
            <circle key={i} cx={28 + i * 36} cy={55} r={13} fill={i === 0 ? "currentColor" : "none"} />
          ))}
        </svg>
      );
    case "version":
      return (
        <svg {...common}>
          <circle cx={100} cy={55} r={44} />
          <circle cx={100} cy={55} r={28} />
          <path d="M86 55 l10 10 l20 -22" />
        </svg>
      );
    case "citation":
      return (
        <svg {...common}>
          <circle cx={62} cy={44} r={14} fill="currentColor" />
          <path d="M48 46 v22 q0 22 26 26" />
          <circle cx={132} cy={44} r={14} fill="currentColor" />
          <path d="M118 46 v22 q0 22 26 26" />
        </svg>
      );
    default:
      return null;
  }
}

/* the plate: numeral cropped by the plate's edge, title, mark */
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

/* the pull-statement, built like everything else on the sheet: a solid
   stub in the section's colour carrying one oversized glyph cropped by its
   edges, and an ink-outlined body for the editorial voice */
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

const FlowArrow = () => (
  <svg className={styles.flowArrow} viewBox="0 0 28 20" aria-hidden="true">
    <path d="M2 10 h22 m-8 -8 l8 8 l-8 8" fill="none" stroke="currentColor" strokeWidth={3.5} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export default function SourceView() {
  const [filter, setFilter] = useState("all");
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({});

  const groups = filter === "all" ? registerGroups : registerGroups.filter((g) => g.key === filter);
  const S = Object.fromEntries(SECTIONS.map((s) => [s.id, s])) as Record<string, (typeof SECTIONS)[number]>;

  return (
    <div className={styles.page}>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <SiteNav active="source" />

      <main id="main">
        <header className={styles.masthead}>
          <div className={styles.mastText}>
            <p className={styles.kicker}>Source</p>
            <h1 className={styles.title}>Provenance, rights, and research use of the archive&rsquo;s materials.</h1>
            <p className={styles.lead}>{overviewText}</p>
          </div>
          {/* the sheet's own stamp: the page's name set too large for its
              plate and cropped by it, the way the EFTA stamp crops its
              letters — a field of colour with one word in it */}
          <div className={styles.stamp} aria-hidden="true">
            <span className={styles.stampLine}>Modern Graphic Design Archive</span>
            <span className={styles.stampWords}>
              <span className={styles.stampWord} data-row="tail">SOURCE</span>
              <span className={styles.stampWord} data-row="head">SOURCE</span>
            </span>
            <span className={styles.stampFoot}>8 sections · release v49</span>
          </div>
        </header>

        {/* 1 — Source overview */}
        <section id="overview" className={styles.section} data-sec={S.overview.sec}>
          <div className={styles.inner}>
            <Plate s={S.overview} />
            <div className={styles.secGrid}>
              <div className={styles.gloss}>
                <span className={styles.glossKicker}>{S.overview.kicker}</span>
                {S.overview.gloss}
              </div>
              <div className={styles.secMain}>
                <p className={styles.subHead}>Four layers, kept distinct</p>
                <div className={styles.layers}>
                  {overviewLayers.map((l, i) => (
                    <div key={l.n} className={styles.layer} data-tone={["blue", "green", "gold", "red"][i]}>
                      <span className={styles.layerN}>{l.n}</span>
                      <h3>{l.label}</h3>
                      <p>{l.note}</p>
                    </div>
                  ))}
                </div>
                <Statement>{overviewNote}</Statement>
              </div>
            </div>
          </div>
        </section>

        {/* 2 — Source register */}
        <section id="register" className={styles.section} data-sec={S.register.sec}>
          <div className={styles.inner}>
            <Plate s={S.register} />
            <div className={styles.secGrid}>
              <div className={styles.gloss}>
                <span className={styles.glossKicker}>{S.register.kicker}</span>
                {S.register.gloss}
              </div>
              <div className={styles.secMain}>
                <div className={styles.prose}>
                  <p className={styles.dropcap}>
                    Each source carries what it is — its <span className={styles.kw} data-tone="ink">source type</span> — and what the project
                    does with it — its <span className={styles.kw} data-tone="blue">project role</span> — as separate properties, so different
                    kinds of material are not flattened into one bibliography.
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
                        onToggle={(e) => {
                          /* read the target now — the updater may run after
                             React has released the event (a null currentTarget
                             took the whole page to the error boundary) */
                          const open = e.currentTarget.open;
                          setOpenGroups((s) => ({ ...s, [g.key]: open }));
                        }}
                      >
                        <summary>{isOpen ? "Hide sources" : `Show ${g.entries.length} sources`}</summary>
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
        <section id="provenance" className={styles.section} data-sec={S.provenance.sec}>
          <div className={styles.inner}>
            <Plate s={S.provenance} />
            <div className={styles.secGrid}>
              <div className={styles.gloss}>
                <span className={styles.glossKicker}>{S.provenance.kicker}</span>
                {S.provenance.gloss}
              </div>
              <div className={styles.secMain}>
                <div className={styles.prose}>
                  <p className={styles.dropcap}>
                    Nothing is published from a raw capture. Every record you can read here has passed the chain below, and each source is held
                    as a <span className={styles.kw} data-tone="red">frozen snapshot</span> at the moment it was acquired.
                  </p>
                </div>
                <div className={styles.flow} aria-label="Acquisition chain">
                  {acquisitionChain.map((s, i) => (
                    <Fragment key={s}>
                      <span className={styles.flowStep}>{s}</span>
                      {i < acquisitionChain.length - 1 ? <FlowArrow /> : null}
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
        <section id="transformation" className={styles.section} data-sec={S.transformation.sec}>
          <div className={styles.inner}>
            <Plate s={S.transformation} />
            <div className={styles.secGrid}>
              <div className={styles.gloss}>
                <span className={styles.glossKicker}>{S.transformation.kicker}</span>
                {S.transformation.gloss}
              </div>
              <div className={styles.secMain}>
                <div className={styles.prose}>
                  <p className={styles.dropcap}>
                    Database fields are not found in nature. Source values are reshaped into consistent fields;{" "}
                    <span className={styles.kw} data-tone="ink">normalizing a value is describing it</span>, not inferring something the source
                    did not state.
                  </p>
                </div>
                <Statement label="Transformation is not inference">{transformationCaveat}</Statement>
                <details className={styles.details}>
                  <summary>Transformation categories ({transformationCategories.length})</summary>
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
        <section id="rights" className={styles.section} data-sec={S.rights.sec}>
          <div className={styles.inner}>
            <Plate s={S.rights} />
            <div className={styles.secGrid}>
              <div className={styles.gloss}>
                <span className={styles.glossKicker}>{S.rights.kicker}</span>
                {S.rights.gloss}
              </div>
              <div className={styles.secMain}>
                <div className={styles.prose}>
                  <p className={styles.dropcap}>{rightsIntro}</p>
                </div>
                <Statement label="Visual material">{rightsGlobalVisual}</Statement>
                <div className={styles.cols3}>
                  {rightsColumns.map((cc, i) => (
                    <div key={cc.key} className={styles.rcol} data-tone={["green", "blue", "red"][i]}>
                      <h3 className={styles.rcolHead}>{cc.title}</h3>
                      <p>{cc.body}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 6 — Evidence & source status */}
        <section id="status" className={styles.section} data-sec={S.status.sec}>
          <div className={styles.inner}>
            <Plate s={S.status} />
            <div className={styles.secGrid}>
              <div className={styles.gloss}>
                <span className={styles.glossKicker}>{S.status.kicker}</span>
                {S.status.gloss}
              </div>
              <div className={styles.secMain}>
                <div className={styles.prose}>
                  <p className={styles.dropcap}>{statusIntro}</p>
                </div>
                <dl className={styles.legend}>
                  {evidenceStatusLegend.map((s) => (
                    <div key={s.status} className={styles.legendRow}>
                      <dt data-s={s.status}>{s.status}</dt>
                      <dd>{s.meaning}</dd>
                    </div>
                  ))}
                </dl>
                <Statement>{evidenceStatusNote}</Statement>
              </div>
            </div>
          </div>
        </section>

        {/* 7 — Version & reproducibility */}
        <section id="version" className={styles.section} data-sec={S.version.sec}>
          <div className={styles.inner}>
            <Plate s={S.version} />
            <div className={styles.secGrid}>
              <div className={styles.gloss}>
                <span className={styles.glossKicker}>{S.version.kicker}</span>
                {S.version.gloss}
              </div>
              <div className={styles.secMain}>
                <div className={styles.prose}>
                  <p className={styles.dropcap}>{versionIntro}</p>
                </div>
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
        <section id="citation" className={styles.section} data-sec={S.citation.sec}>
          <div className={styles.inner}>
            <Plate s={S.citation} />
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
                  {citationExample.map((cc, i) => (
                    <div key={cc.label} className={styles.citeBlock}>
                      <span className={styles.stub} aria-hidden="true">
                        <span className={styles.stubNum}>{i + 1}</span>
                      </span>
                      <div className={styles.citeBody}>
                        <b>{cc.label}</b>
                        <p>{cc.text}</p>
                      </div>
                    </div>
                  ))}
                </div>
                <a href={`${ABOUT_URL}#cite`} className={styles.aboutLink}>
                  How to cite the archive itself — About
                  <ArrowRight size={18} strokeWidth={3} aria-hidden="true" />
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
