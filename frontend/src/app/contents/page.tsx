import Link from "next/link";
import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import TocNav from "@/components/archive/shell/TocNav";
import { TypeSwatch } from "@/components/archive/primitives";
import {
  dateSpanLabel,
  getFolderTypes,
  getFoldersByType,
  getSurfacesForFolder,
  sortChronologically,
} from "@/lib/archive-data";

export const metadata = {
  title: "Index — Modern Graphic Design History",
  description:
    "Full table of contents for the rights-aware graphic design history archive: folder types, folders, and every staged surface.",
};

const prospectiveSourceFamilies = [
  ["Museum and design APIs", "AIC, V&A, Met, Cleveland, Cooper Hewitt, Harvard, Rijksmuseum, Getty Museum"],
  ["National libraries", "LoC, Gallica/BnF, NDL, NLB Singapore, Trove, DigitalNZ, Biblioteca Nacional Digital de Chile"],
  ["Periodical/OCR portals", "Chronicling America, Delpher, ANNO, Papers Past, NewspaperSG, HNDM, Hemeroteca Digital Brasileira"],
  ["Regional aggregators", "Europeana, DPLA, Deutsche Digitale Bibliothek, Japan Search, dLOC"],
  ["Community and movement archives", "Chinese Posters, Interference Archive, SAHA, Palestinian Museum Digital Archive, African Activist Archive, NAIDOC/AIATSIS"],
  ["Repository systems", "CONTENTdm, Kramerius, Omeka S, DSpace, OAI-PMH repositories, IIIF manifests"],
];

const openSourceStack = [
  ["Scrapy", "https://github.com/scrapy/scrapy", "BSD-3-Clause", "Official APIs, paginated HTML, retries, throttling, and reproducible CSV/JSON output."],
  ["Crawlee", "https://github.com/apify/crawlee", "Apache-2.0", "Browser/HTTP crawling for brittle or JavaScript-heavy portals with queueing and structured datasets."],
  ["Playwright", "https://github.com/microsoft/playwright", "Apache-2.0", "Deterministic browser automation for viewer pages, lazy-loaded source pages, and local interface verification."],
  ["Browsertrix", "https://github.com/webrecorder/browsertrix", "AGPL-3.0", "High-fidelity WARC/WACZ capture for complex pages and viewers; archive evidence, not a rights grant."],
  ["pywb", "https://github.com/webrecorder/pywb", "GPL-3.0", "Replay and QA layer for WARC/WACZ captures."],
  ["ArchiveBox", "https://github.com/ArchiveBox/ArchiveBox", "MIT", "Small-scale snapshot index for manually selected source URLs and candidate pages awaiting adapter work."],
  ["Sickle", "https://github.com/mloesch/sickle", "BSD-3-Clause", "OAI-PMH client for DSpace, university repositories, national-library feeds, and metadata harvests."],
  ["iiif-prezi3", "https://github.com/iiif-prezi/iiif-prezi3", "Apache-2.0", "IIIF Presentation parser/generator for manifests, canvases, thumbnails, attribution, and rights fields."],
  ["Trafilatura", "https://github.com/adbar/trafilatura", "Apache-2.0", "Main-text and metadata extraction from essays, exhibition pages, institutional histories, and source descriptions."],
  ["Newspaper4k", "https://github.com/AndyTheFactory/newspaper4k", "MIT", "Article extraction fallback for news-like pages where title, byline, date, lead image, and body need a first pass."],
];

const projectRepository = {
  label: "dpan538 / graphic_design_archive",
  url: "https://github.com/dpan538/graphic_design_archive",
  note: "Project repository for the Modern Graphic Design History archive prototype, including code, scripts, generated payloads, rulebooks, and frontend implementation.",
};

function IndexLedger({ rows }: { rows: string[][] }) {
  return (
    <div className="toc-ledger">
      {rows.map(([label, ...rest]) => (
        <div key={label} className="contents">
          <strong>{label}</strong>
          <span>{rest.join(" / ")}</span>
        </div>
      ))}
    </div>
  );
}

/**
 * Full Table of Contents — two-column layout.
 * Left: sticky TocNav quick-jump card.
 * Right: scrollable hierarchical TOC.
 */
export default function IndexPage() {
  const types = getFolderTypes();

  const main = (
    <div className="toc-shell">
      {/* ── Left sticky sidebar ── */}
      <aside className="toc-sidebar">
        <TocNav />
      </aside>

      {/* ── Main TOC ── */}
      <div className="toc">
        <header>
          <p className="label-caps text-ink-soft">Index · January 2026</p>
          <h1 className="mt-1">Modern Graphic Design<br />History</h1>
          <p className="mt-3" style={{ fontSize: "0.78rem", lineHeight: 1.6, maxWidth: "30rem" }}>
            A rights-aware archive index. Organised into four folder types; each
            folder is a filter view — the same surface may appear in several folders.
            Entries are listed chronologically and link to their loose-leaf pages.
          </p>
        </header>

        <section className="toc__appendices" aria-label="Method appendices">
          <details className="toc-appendix" id="project-repository" open>
            <summary>
              <span>repository</span>
              <strong>Project GitHub</strong>
            </summary>
            <p>
              This repository is the project-level citation target for code,
              scripts, generated payloads, rulebooks, and frontend implementation.
              It does not transfer rights in upstream archive records, images,
              scans, source metadata, or project-authored research text.
            </p>
            <div className="toc-repo-callout">
              <a href={projectRepository.url} target="_blank" rel="noreferrer">
                {projectRepository.label}
              </a>
              <span>{projectRepository.url}</span>
              <p>{projectRepository.note}</p>
            </div>
          </details>

          <details className="toc-appendix" id="source-families">
            <summary>
              <span>method appendix</span>
              <strong>Prospective source families</strong>
            </summary>
            <p>
              Candidate sources are planning evidence until they produce captured
              records. They are listed here for audit and expansion planning, but
              they do not count as active coverage.
            </p>
            <IndexLedger rows={prospectiveSourceFamilies} />
          </details>

          <details className="toc-appendix" id="capture-tools">
            <summary>
              <span>method appendix</span>
              <strong>Open-source capture stack</strong>
            </summary>
            <p>
              Tools are used as auditable infrastructure. Tool licenses govern
              software use only; captured source records keep their own rights,
              citation, and display terms. Repository links below are cited as
              upstream software references, accessed 2026-06-02.
            </p>
            <div className="toc-tools">
              <div className="toc-tools__head">tool</div>
              <div className="toc-tools__head">repository</div>
              <div className="toc-tools__head">license</div>
              <div className="toc-tools__head">method role</div>
              {openSourceStack.map(([name, url, license, role]) => (
                <div key={name} className="contents">
                  <a href={url} target="_blank" rel="noreferrer">
                    {name}
                  </a>
                  <span>{url}</span>
                  <strong>{license}</strong>
                  <p>{role}</p>
                </div>
              ))}
            </div>
          </details>
        </section>

        <div className="mt-6">
          {types.map((ft, ti) => {
            const folders = getFoldersByType(ft.type);
            return (
              <section key={ft.type} id={`toc-${ft.type}`} className="toc__sect">
                <div className="toc__secthead">
                  <span className="inline-flex items-center gap-2">
                    <TypeSwatch type={ft.type} />
                    {ti + 1} · {ft.label}
                  </span>
                  <p
                    className="mt-1 font-normal normal-case tracking-normal text-ink-soft"
                    style={{ fontSize: "0.62rem", lineHeight: 1.45 }}
                  >
                    {ft.scopeNote}
                  </p>
                </div>

                <div>
                  {folders.map((folder, fi) => {
                    const surfaces = sortChronologically(
                      getSurfacesForFolder(folder),
                    );
                    return (
                      <div key={folder.folderId} id={`folder-${folder.folderId}`} className="mb-3">
                        <div className="toc__entry">
                          <Link
                            href={`/folders/${folder.type}/${folder.slug}`}
                            className="font-bold"
                          >
                            {ti + 1}.{fi + 1} {folder.title}
                          </Link>
                          <span className="lead" aria-hidden />
                          <span className="ref">
                            {dateSpanLabel(folder.dateStart, folder.dateEnd)} ·{" "}
                            {surfaces.length}
                          </span>
                        </div>
                        <ul className="mt-0.5 ml-3">
                          {surfaces.map((su) => (
                            <li key={su.surfaceId} className="toc__entry">
                              <Link
                                href={`/surfaces/${su.surfaceId}?folder=${folder.folderId}`}
                              >
                                {su.title}
                              </Link>
                              <span className="lead" aria-hidden />
                              <span className="ref">
                                {su.dateText} · {su.provisionalDisplayNumber}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    );
                  })}
                </div>
              </section>
            );
          })}
        </div>
      </div>
    </div>
  );

  return <ArchiveShell main={main} activeNav="index" mainScroll />;
}
