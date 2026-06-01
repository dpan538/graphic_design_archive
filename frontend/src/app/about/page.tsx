import ArchiveShell from "@/components/archive/shell/ArchiveShell";

export const metadata = {
  title: "About — Modern Graphic Design History",
  description:
    "Methodology, source strategy, design method, rights policy, and open-source capture stack for the archive index.",
};

const nav = [
  ["00", "Statement", "#statement"],
  ["01", "Sources", "#sources"],
  ["02", "Methodology", "#methodology"],
  ["03", "Design research", "#design"],
  ["04", "Evidence", "#evidence"],
  ["05", "Open source", "#open-source"],
  ["06", "Rights", "#rights"],
  ["07", "Copyright", "#copyright"],
  ["08", "License", "#license"],
  ["09", "Citation", "#citation"],
  ["10", "Limits", "#limits"],
];

const currentSources = [
  {
    name: "Gallica / BnF APIs",
    count: "239",
    route: "gallica.bnf.fr",
    role: "French national-library SRU/IIIF records for posters, advertising, typography, printing, periodicals, visual documents, and bibliographic context.",
    rights: "SRU dc:rights and Gallica/BnF item page; public-domain signals become IMG03, otherwise IIIF/source-hosted records stay IMG02.",
  },
  {
    name: "Wikimedia Commons",
    count: "104",
    route: "commons.wikimedia.org",
    role: "Open-license image supplement and discovery layer for poster/design-adjacent records. It is not treated as the original holding archive.",
    rights: "Commons extmetadata license fields; only open-license files are admitted as IMG03 candidates, with source and credit retained.",
  },
  {
    name: "Princeton University Library Digital Collections / Figgy",
    count: "41",
    route: "figgy.princeton.edu",
    role: "University-library IIIF records for posters, broadsides, banners, advertising print, scanned visual resources, and ephemera.",
    rights: "Manifest license and Princeton source page; explicit open/public-domain signals become IMG03, otherwise source-hosted IIIF remains IMG02.",
  },
  {
    name: "Wellcome Collection Catalogue API",
    count: "89",
    route: "wellcomecollection.org",
    role: "Medical, public-information, exhibition, poster, print, and design-adjacent collection records with explicit rights fields.",
    rights: "Wellcome item license or rights field; display follows source item status.",
  },
  {
    name: "Library of Congress loc.gov API",
    count: "50",
    route: "loc.gov",
    role: "American posters, WPA/FSA material, newspapers, pamphlets, catalog records, rights advisories, and persistent item pages.",
    rights: "LoC rights advisory per item; no universal public-domain assumption.",
  },
  {
    name: "V&A Collections API",
    count: "46",
    route: "collections.vam.ac.uk",
    role: "Design-object and collection metadata for posters, prints, ephemera, textiles, exhibitions, makers, and object types.",
    rights: "V&A item rights and image permissions; metadata used for navigation.",
  },
  {
    name: "Art Institute of Chicago API",
    count: "45",
    route: "artic.edu",
    role: "Museum collection records, artist metadata, artwork dates, image-state checks, and open-data identifiers.",
    rights: "AIC open data plus item-level image license or restriction.",
  },
  {
    name: "Internet Archive / text and periodical collections",
    count: "30",
    route: "archive.org",
    role: "Scanned books, periodicals, manuals, exhibition catalogues, OCR, page evidence, and downloadable metadata.",
    rights: "Collection and item metadata vary; scans are treated as source evidence.",
  },
  {
    name: "DigitalNZ",
    count: "21",
    route: "digitalnz.org",
    role: "New Zealand newspaper and cultural-heritage aggregation, especially local print traces and periodical evidence.",
    rights: "Provider rights statement via DigitalNZ / Papers Past item page.",
  },
  {
    name: "Georgia State University Library Digital Collections / CONTENTdm",
    count: "2",
    route: "digitalcollections.library.gsu.edu",
    role: "Local/university CONTENTdm records for labor, civil-rights, newspaper, theatre, and urban print-culture traces.",
    rights: "Item-level local rights statements; imageUri/IIIF is treated as source-hosted IMG02, not an open reuse grant.",
  },
  {
    name: "The Met Open Access",
    count: "15",
    route: "metmuseum.org",
    role: "Open-access museum records, object metadata, public-domain image candidates, and provenance fields.",
    rights: "Met Open Access / public-domain item evidence where explicitly supplied.",
  },
  {
    name: "Cleveland Museum Open Access API",
    count: "12",
    route: "clevelandart.org",
    role: "Open-access art and design records with rights, image, department, culture, and object-type metadata.",
    rights: "Open-access item evidence, reviewed per object record.",
  },
  {
    name: "Getty Research Portal",
    count: "3",
    route: "portal.getty.edu",
    role: "Digitized design-history books, catalogues, research scans, and bibliographic support records.",
    rights: "Portal and contributing-institution terms; used primarily as bibliographic evidence.",
  },
  {
    name: "Chinese Posters",
    count: "1",
    route: "chineseposters.net",
    role: "Specialist poster-history record used as a local, topic-specific source candidate rather than a bulk image source.",
    rights: "Specialist archive terms; source link only unless item permissions are clear.",
  },
];

const sourceFamilies = [
  ["Museum APIs", "AIC, V&A, Met, Cleveland, Harvard, Rijksmuseum, Getty Museum"],
  ["National libraries", "LoC, Gallica/BnF, NDL, NLB Singapore, Trove, DigitalNZ"],
  ["Periodical/OCR portals", "Chronicling America, Delpher, ANNO, Papers Past, NewspaperSG, HNDM, Hemeroteca Digital Brasileira"],
  ["Regional aggregators", "Europeana, DPLA, Deutsche Digitale Bibliothek, Japan Search, dLOC"],
  ["Community archives", "Chinese Posters, Interference Archive, SAHA, Palestinian Museum Digital Archive, African Activist Archive, NAIDOC/AIATSIS"],
  ["Repository systems", "Kramerius, Omeka S, DSpace, OAI-PMH repositories, IIIF manifests"],
];

const designReferences = [
  ["British Rail Corporate Identity", "Primary color and information-system reference: red signal bands, black rule structures, cyan/green instructional accents, forms, labels, and manual-like hierarchy."],
  ["Richard Hollis / systems modernism", "Reference for editorial restraint, diagrammatic clarity, identity manuals, public-information graphics, and typography that behaves like infrastructure."],
  ["Bauhaus exhibition and print layouts", "Reference for gridded page logic, asymmetry, text/image tension, serial numbering, and the use of design history as a working archive rather than a decorative citation."],
  ["Index-card and correspondence-storage diagrams", "Reference for the homepage and folder logic: drawers, tabs, headings, speed indexes, and records that can be searched and re-sorted."],
  ["IBM Plex Sans + IBM Plex Mono", "Type system for an institutional but contemporary voice: sans for reading, mono for labels, IDs, provenance, and evidence tables."],
  ["Words Over Time", "Structural reference for a long-form methodology page, but not a visual target; this project moves toward rail manuals, research ledgers, and archive-box mechanics."],
];

const citationFields = [
  ["Required", "title or supplied title, creator when known, date or date range, source name, stable source URL, access date, rights statement, and archive record ID."],
  ["Recommended", "collection name, object type, place, language, image state, original identifier, capture script or adapter, and any uncertainty note."],
  ["Project citation", "Modern Graphic Design History, Archive Box record, record ID, source name, source URL, accessed date, and rights note."],
  ["Image citation", "Always cite the original holding institution or source page. Do not cite this interface as the image owner unless a future record explicitly says so."],
];

const licensePolicy = [
  {
    label: "Interface and writing",
    status: "Prototype copyright retained",
    note: "The about-page text, interface design, visual system, and Archive Box composition are part of this research prototype and are not automatically open licensed.",
  },
  {
    label: "Project code",
    status: "Private repository / no public license declared",
    note: "The frontend package is currently marked private and does not declare a project license. Treat code reuse as permission-required until a repository LICENSE file is added.",
  },
  {
    label: "Index metadata",
    status: "Source-cited research index",
    note: "Normalized titles, dates, routes, folders, and notes are used for citation and navigation. Reuse must preserve source attribution and item-level uncertainty.",
  },
  {
    label: "Images and scans",
    status: "Original source terms control",
    note: "Images, scans, thumbnails, IIIF canvases, and viewer captures remain governed by the holding institution, creator, publisher, collection, or item page.",
  },
  {
    label: "Open-source tools",
    status: "Tool-specific licenses",
    note: "Scrapy, Crawlee, Playwright, Browsertrix, pywb, ArchiveBox, and other capture tools keep their own licenses; those licenses do not transfer rights in captured source material.",
  },
  {
    label: "Future release note",
    status: "License review required",
    note: "Before public release, choose a repository license for project code and a separate content/data license for project-authored metadata, then keep third-party source terms separate.",
  },
];

const openSourceStack = [
  {
    name: "Scrapy",
    license: "BSD-3-Clause",
    role: "Primary Python crawler framework for stable APIs, paginated HTML, source-specific spiders, retries, throttling, and reproducible CSV/JSON output.",
    url: "https://github.com/scrapy/scrapy",
  },
  {
    name: "Crawlee",
    license: "Apache-2.0",
    role: "Browser/HTTP crawling layer for brittle or JavaScript-heavy portals; useful when a local source needs queueing, Playwright/Puppeteer rendering, screenshots, and structured datasets.",
    url: "https://github.com/apify/crawlee",
  },
  {
    name: "Playwright",
    license: "Apache-2.0",
    role: "Deterministic browser automation under Crawlee or direct scripts; used for viewer pages, lazy-loaded search results, and visual verification of source pages.",
    url: "https://github.com/microsoft/playwright",
  },
  {
    name: "Browsertrix and browsertrix-crawler",
    license: "AGPL-3.0",
    role: "High-fidelity web-archive capture for complex pages and viewers; output should be treated as WARC/WACZ evidence, not as a rights grant.",
    url: "https://github.com/webrecorder/browsertrix",
  },
  {
    name: "Heritrix",
    license: "Apache-2.0",
    role: "Archival-quality focused crawling when a source needs strict politeness, seed scopes, robots handling, and institution-style crawl logs.",
    url: "https://github.com/internetarchive/heritrix3",
  },
  {
    name: "pywb",
    license: "GPL-3.0",
    role: "Replay and QA layer for WARC/WACZ captures; used to verify that archived evidence can be inspected later without relying on a live site.",
    url: "https://github.com/webrecorder/pywb",
  },
  {
    name: "ArchiveBox",
    license: "MIT",
    role: "Small-scale self-hosted capture and snapshot index for manually selected source URLs, especially candidate pages awaiting adapter work.",
    url: "https://github.com/ArchiveBox/ArchiveBox",
  },
  {
    name: "Sickle",
    license: "BSD-3-Clause",
    role: "OAI-PMH client for DSpace, Gallica/BnF-style feeds, university repositories, and national-library metadata harvests.",
    url: "https://github.com/mloesch/sickle",
  },
  {
    name: "iiif-prezi3",
    license: "Apache-2.0",
    role: "IIIF Presentation 3 parser/generator for manifests, canvases, thumbnails, image services, labels, attribution, and rights fields.",
    url: "https://github.com/iiif-prezi/iiif-prezi3",
  },
  {
    name: "Trafilatura",
    license: "Apache-2.0",
    role: "Main-text and metadata extraction from essays, exhibition pages, institutional histories, and source descriptions without copying whole pages.",
    url: "https://github.com/adbar/trafilatura",
  },
  {
    name: "Newspaper4k",
    license: "MIT",
    role: "Article extraction fallback for news-like pages where title, byline, date, lead image, and article body need a cleaner first pass.",
    url: "https://github.com/AndyTheFactory/newspaper4k",
  },
  {
    name: "Kramerius",
    license: "GPL-3.0",
    role: "Open-source digital-library platform used by many Czech and Slovak institutions; adapter target for periodicals, OCR, IIIF/OAI, local print, and ads.",
    url: "https://system-kramerius.cz/en/",
  },
  {
    name: "Omeka S",
    license: "GPL-3.0",
    role: "Open-source cultural-heritage publishing system; adapter target for item, media, item-set, linked-data, and community archive records.",
    url: "https://github.com/omeka/omeka-s",
  },
  {
    name: "DSpace",
    license: "BSD-3-Clause",
    role: "Open-source repository platform; adapter target for REST API, OAI-PMH, institutional publications, theses, reports, images, and PDFs.",
    url: "https://github.com/DSpace/DSpace",
  },
  {
    name: "pyeuropeana",
    license: "Repository license check required",
    role: "Europeana Python API client candidate for Search, Record, Entity, and IIIF APIs once an API key and terms review are configured.",
    url: "https://github.com/europeana/rd-europeana-python-api",
  },
];

const methods = [
  ["Source discovery", "Candidate sources are first classified by access method, rights clarity, geography, record family, automation feasibility, and expected image behavior."],
  ["Adapter selection", "A source should use the least fragile adapter available: official API first, then OAI-PMH or IIIF, then structured HTML, then browser capture."],
  ["Record normalization", "Every capture row is reduced into source identifier, source URL, title, creator, date text, place, object type, collection, rights text, image state, raw path, and access date."],
  ["Image decision", "Images are not displayed because an image URL exists. Display is controlled by IMG00 through IMG04 and item-level rights evidence."],
  ["Text enrichment", "Essays, descriptions, OCR, and bibliographic notes are treated as contextual evidence and are paraphrased or summarized when reuse is restricted."],
  ["Locality expansion", "The project should privilege local repositories, regional newspapers, community archives, and non-English search terms when they improve historical specificity."],
];

const sourceDependencyReferences = [
  ["Generated ledger", "data/source_dependency_ledger.csv", "Current source counts, IMG-state distribution, dependency role, rights dependency, text dependency, and capture scripts."],
  ["Source dependency rulebook", "docs/system/SOURCE_DEPENDENCY_AND_TEXT_REFERENCES_v0.md", "Public text and About-page claims must stay tied to inspectable source families and fields."],
  ["Text enrichment rules", "docs/methodology/IMAGE_AND_TEXT_ENRICHMENT_RULES_v0.md", "Defines source text, normalized summary, context note, interpretation, OCR limits, and text length targets."],
  ["Surface pipeline", "docs/methodology/SURFACE_GENERATION_PIPELINE_v0.md", "Defines how capture rows become reviewed source records, surfaces, folders, search documents, and static pages."],
  ["Rights strategy", "data/rights_strategy.csv", "Defines the rights ladder for open-access APIs, reuse licenses, IIIF, aggregators, community archives, and web captures."],
];

const textDependencyRules = [
  ["Source fields", "A public sentence may depend on title, creator, date, medium, collection, description, subject, rights text, source URL, source identifier, and access date."],
  ["Raw capture", "Parser status, raw JSON/XML path, API URL, image-state decision, and rights basis must remain available for audit."],
  ["Context", "Historical context notes and classification rationales are allowed only as source-grounded summaries or explicit project inference."],
  ["OCR and excerpts", "OCR can discover relevant material, but strong claims require page/image verification or a stable citation basis."],
  ["No substitute evidence", "AI or editor-authored wording may clarify the record, but it cannot create evidence, replace missing images, or assert influence without a reference."],
];

const evidenceColumns = [
  ["01", "source"],
  ["02", "rights"],
  ["03", "image"],
  ["04", "context"],
  ["05", "locality"],
  ["06", "limit"],
];

function AboutPageMain() {
  return (
    <div className="about-shell">
      <aside className="about-nav" aria-label="About page sections">
        <a href="#statement" className="about-nav__title">Method guide</a>
        {nav.map(([number, label, href]) => (
          <a key={href} href={href} className="about-nav__link">
            <span>{number}</span>
            {label}
          </a>
        ))}
      </aside>

      <article className="about-doc">
        <header id="statement" className="about-hero about-hover-panel">
          <div className="about-crumbs">
            <a href="/">Archive Box</a>
            <span>/</span>
            <span>About</span>
          </div>
          <div className="about-rail" aria-label="Archive evidence columns">
            {evidenceColumns.map(([number, label]) => (
              <div key={label} className="about-hover-panel">
                <span>{number}</span>
                {label}
              </div>
            ))}
          </div>
          <p className="label-caps text-ink-soft">00 / project statement</p>
          <h1>Modern Graphic Design History</h1>
          <p>
            is a rights-aware archive index, source-navigation system, and a
            learning/research prototype for building a fuller modern graphic
            design archive library in the AI era.
          </p>
          <p>
            It does not replace original archives, scrape away their authority,
            or claim one universal design history. It organizes distributed
            evidence so that students, researchers, designers, and AI-assisted
            study systems can inspect records, gaps, rights decisions, and
            source limits together.
          </p>
          <p className="about-hero__note">
            Current status: a static research prototype generated from source
            captures, not a final publication dataset. The goal is a more
            complete, citation-first archive library for learning and research:
            each public surface should remain traceable to a source record and
            an item-level rights note.
          </p>
        </header>

        <section id="sources" className="about-section about-hover-panel">
          <div className="about-section__num">01</div>
          <div>
            <p className="label-caps text-ink-soft">current source ledger</p>
            <h2>Sources currently used in the public surface dataset</h2>
            <p>
              These are the source names currently present in the public surface
              JSON, counted from the indexed records. The list separates actual
              evidence already in the interface from future source families.
            </p>
            <div className="about-source-table">
              <div className="about-source-table__head">source</div>
              <div className="about-source-table__head">route</div>
              <div className="about-source-table__head">records</div>
              {currentSources.map((source) => (
                <details key={source.name} className="about-source-item">
                  <summary className="about-source-summary">
                    <strong>{source.name}</strong>
                    <span>{source.route}</span>
                    <span className="about-source-count">{source.count}</span>
                  </summary>
                  <div className="about-source-detail">
                    <div>
                      <strong>Coverage</strong>
                      <p>{source.role}</p>
                    </div>
                    <div>
                      <strong>License / rights</strong>
                      <p>{source.rights}</p>
                    </div>
                  </div>
                </details>
              ))}
            </div>
            <h3>Source dependency references</h3>
            <p>
              Source counts and methodological claims are not written by hand
              alone. They are checked against generated ledgers and rulebooks so
              that source use, rights decisions, and text enrichment remain
              reproducible.
            </p>
            <div className="about-ledger">
              {sourceDependencyReferences.map(([title, path, body]) => (
                <div key={title} className="contents">
                  <strong>{title}</strong>
                  <span>
                    <code>{path}</code> — {body}
                  </span>
                </div>
              ))}
            </div>
            <h3>Expansion sources</h3>
            <p>
              The following families remain research targets for more local and
              more specific captures. They are not all displayed in the current
              public dataset yet.
            </p>
            <div className="about-ledger">
              {sourceFamilies.map(([family, examples]) => (
                <div key={family} className="contents">
                  <strong>{family}</strong>
                  <span>{examples}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="methodology" className="about-section about-hover-panel">
          <div className="about-section__num">02</div>
          <div>
            <p className="label-caps text-ink-soft">methodology</p>
            <h2>Source-led archive construction</h2>
            <p>
              The archive begins with source records, not illustrations. A
              poster, magazine, trade card, catalogue, campaign graphic, design
              institution, or movement page enters the system only when it can
              point back to an inspectable source URL or raw capture.
            </p>
            <div className="about-method-grid">
              {methods.map(([title, body]) => (
                <div key={title} className="about-method about-hover-panel">
                  <h3>{title}</h3>
                  <p>{body}</p>
                </div>
              ))}
            </div>
            <h3>Text dependency rules</h3>
            <p>
              Descriptive writing in this project is a normalization layer, not
              independent evidence. The public text page may clarify captured
              material, but every claim must point back to a source field, raw
              capture, authority/context record, or cited research reference.
            </p>
            <div className="about-ledger">
              {textDependencyRules.map(([label, body]) => (
                <div key={label} className="contents">
                  <strong>{label}</strong>
                  <span>{body}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="design" className="about-section about-hover-panel">
          <div className="about-section__num">03</div>
          <div>
            <p className="label-caps text-ink-soft">design research</p>
            <h2>Archive box as interface</h2>
            <p>
              The interface uses a paper-box metaphor: folders, loose sheets,
              source drawers, fixed image zones, and typed evidence tables.
              This is a design method, not decoration. The structure makes a
              claim that historical evidence should be sortable, inspectable,
              and honest about absence.
            </p>
            <div className="about-reference-grid">
              {designReferences.map(([title, body]) => (
                <div key={title} className="about-reference about-hover-panel">
                  <h3>{title}</h3>
                  <p>{body}</p>
                </div>
              ))}
            </div>
            <div className="about-ledger">
              <div>Folder views</div>
              <div>region, theme, medium, and movement are filter lenses, not separate archives</div>
              <div>Loose-leaf surfaces</div>
              <div>each public page keeps title, date, source, image state, notes, and folder links together</div>
              <div>Image zones</div>
              <div>the frame stays visible even when rights require an empty image state</div>
              <div>Monospace/manual style</div>
              <div>the typography favors auditability, inventory, and repeat use over a museum-poster hero treatment</div>
            </div>
          </div>
        </section>

        <section id="evidence" className="about-section about-hover-panel">
          <div className="about-section__num">04</div>
          <div>
            <p className="label-caps text-ink-soft">layered evidence</p>
            <h2>What a record must carry</h2>
            <p>
              Each record is expected to preserve provenance, classification,
              rights posture, display behavior, and uncertainty. The public
              interface should show enough of that chain for a researcher to
              return to the original archive.
            </p>
            <div className="about-evidence">
              <span>source URL</span>
              <span>stable identifier</span>
              <span>raw capture</span>
              <span>date evidence</span>
              <span>rights basis</span>
              <span>image state</span>
              <span>classification rationale</span>
              <span>uncertainty note</span>
              <span>citation basis</span>
              <span>capture script</span>
              <span>source dependency</span>
              <span>text dependency</span>
            </div>
          </div>
        </section>

        <section id="open-source" className="about-section about-hover-panel">
          <div className="about-section__num">05</div>
          <div>
            <p className="label-caps text-ink-soft">open-source capture stack</p>
            <h2>Tools and exactly how they should be used</h2>
            <p>
              Open-source tools are used as auditable infrastructure. They do
              not override source terms, bypass access controls, or turn a
              public image into a reusable image. Each tool has a bounded role.
            </p>
            <div className="oss-table">
              <div className="oss-head">tool</div>
              <div className="oss-head">role</div>
              <div className="oss-head">license</div>
              <div className="oss-head">use boundary</div>
              {openSourceStack.map((tool) => (
                <div key={tool.name} className="oss-row about-hover-panel">
                  <a href={tool.url} target="_blank" rel="noreferrer">
                    {tool.name}
                  </a>
                  <p>{tool.role}</p>
                  <span>{tool.license}</span>
                  <p>
                    {tool.license.includes("GPL") || tool.license.includes("AGPL")
                      ? "Review copyleft obligations before bundling, hosting, or distributing service code."
                      : "Tool license governs software use only; captured source records keep their own terms."}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="rights" className="about-section about-hover-panel">
          <div className="about-section__num">06</div>
          <div>
            <p className="label-caps text-ink-soft">rights and display policy</p>
            <h2>Image states are source decisions</h2>
            <div className="about-ledger">
              <div>IMG00</div>
              <div>image evidence exists or is expected, but the public page renders an empty rights-aware frame</div>
              <div>IMG01</div>
              <div>thumbnail-only candidate; item rights still require review</div>
              <div>IMG02</div>
              <div>source-hosted viewer or IIIF route; local display/copy is not assumed</div>
              <div>IMG03</div>
              <div>open image display candidate with explicit item-level evidence</div>
              <div>IMG04</div>
              <div>text, authority, bibliography, or context page with no image frame expected</div>
            </div>
          </div>
        </section>

        <section id="copyright" className="about-section about-hover-panel">
          <div className="about-section__num">07</div>
          <div>
            <p className="label-caps text-ink-soft">copyright statement</p>
            <h2>The interface is not a rights transfer</h2>
            <p>
              Modern Graphic Design History is an index and research interface.
              Copyright, neighboring rights, database rights, trademark rights,
              personality rights, and contractual access terms may remain with
              the original creators, publishers, institutions, or estates.
            </p>
            <div className="about-ledger">
              <div>Metadata</div>
              <div>Source metadata is cited and normalized for research navigation; original source terms still govern reuse.</div>
              <div>Images</div>
              <div>Images are displayed only when item-level evidence supports that display state, and even then the source remains the citation authority.</div>
              <div>Captures</div>
              <div>Raw captures and screenshots are used for verification, debugging, and provenance; they are not automatically public assets.</div>
              <div>Design</div>
              <div>The project design is original research interface work informed by historical references; it does not reproduce a corporate identity manual as a template.</div>
              <div>Takedown</div>
              <div>Questionable records should be moved to an empty image state or removed while source rights are reviewed.</div>
            </div>
          </div>
        </section>

        <section id="license" className="about-section about-hover-panel">
          <div className="about-section__num">08</div>
          <div>
            <p className="label-caps text-ink-soft">rights notice</p>
            <h2>No blanket reuse license is granted here</h2>
            <p>
              This notice describes license status for a learning and research
              prototype; it is not a permission grant. Interface code,
              project-authored writing, normalized index metadata, third-party
              source records, and images each require separate rights review.
              Original source terms remain authoritative.
            </p>
            <div className="license-grid">
              {licensePolicy.map((item) => (
                <div key={item.label} className="license-card about-hover-panel">
                  <p className="label-caps">{item.label}</p>
                  <h3>{item.status}</h3>
                  <p>{item.note}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="citation" className="about-section about-hover-panel">
          <div className="about-section__num">09</div>
          <div>
            <p className="label-caps text-ink-soft">citation note</p>
            <h2>How records should be cited</h2>
            <p>
              Citations should point readers back to the holding source first,
              then to this interface as a navigation and interpretation layer.
              When a date, creator, or rights statement is uncertain, the
              uncertainty should remain inside the citation note.
            </p>
            <div className="about-ledger">
              {citationFields.map(([label, body]) => (
                <div key={label} className="contents">
                  <strong>{label}</strong>
                  <span>{body}</span>
                </div>
              ))}
            </div>
            <div className="about-citation-box about-hover-panel">
              <h3>Working format</h3>
              <p>
                Creator if known. “Title or supplied title.” Date or date
                range. Holding source / collection. Source URL. Rights
                statement. Modern Graphic Design History record ID. Accessed
                day month year.
              </p>
            </div>
          </div>
        </section>

        <section id="limits" className="about-section about-section--last about-hover-panel">
          <div className="about-section__num">10</div>
          <div>
            <p className="label-caps text-ink-soft">claim boundaries</p>
            <h2>What this archive refuses</h2>
            <p>
              The archive refuses to treat availability as importance, image
              presence as permission, English search terms as global coverage,
              or a missing result as proof that a graphic history did not
              exist. A successful capture is evidence for a bounded source
              claim, not a total history.
            </p>
          </div>
        </section>
      </article>
    </div>
  );
}

export default function AboutPage() {
  return <ArchiveShell main={<AboutPageMain />} activeNav="about" mainScroll />;
}
