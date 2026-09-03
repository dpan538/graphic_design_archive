/* Source page content. Data only — grounded in the project's own source register
   and release record. Academic-reference register: it documents provenance,
   acquisition, rights, transformation, evidence status, and reproducibility.
   It does not restate project vision, audiences, Search/TRACE, claim boundaries,
   or the project-citation formats — those live on About. */

export const ABOUT_URL = "/about";
export const REPO_URL = "https://github.com/dpan538/graphic_design_archive";

/* ---- 1 · Source overview ---------------------------------------- */

export const overviewText =
  "Source documents the provenance, acquisition status, rights conditions, and research use of the materials incorporated into Modern Graphic Design Archive. It distinguishes original source material, scholarly evidence, project-normalized metadata, and internally generated research representations.";

export const overviewLayers: { n: string; label: string; note: string }[] = [
  {
    n: "1",
    label: "Original source",
    note: "Material as held, catalogued, or published by an external institution, author, or platform. Not stored or reproduced here except as evidence.",
  },
  {
    n: "2",
    label: "Archive metadata",
    note: "Project-normalized fields derived from a source record — a description of it, not a copy of it.",
  },
  {
    n: "3",
    label: "Research evidence",
    note: "Material used to support classification or an unresolved research inquiry, carried with its own status.",
  },
  {
    n: "4",
    label: "TRACE interpretation",
    note: "Validated associations and open inquiries produced by the project's research process. Downstream of, and never equal to, a source.",
  },
];

export const overviewNote =
  "These four layers are kept distinct throughout the archive. The presence of a source does not imply that a historical claim built on it has been validated.";

/* ---- 2 · Source register -------------------------------------- */

export type SourceEntry = {
  name: string;
  org: string;
  type: string;
  role: string[];
  identifier: string;
  coverage: string;
  material: string;
  acquired: string;
  rights: string;
  status: string;
  contribution?: string;
};

const CAPTURE_2026 = "2026 capture batches";
const META_ONLY =
  "Metadata used for description and citation; source object imagery is not reproduced.";

const archives: SourceEntry[] = [
  {
    name: "Gallica",
    org: "Bibliothèque nationale de France",
    type: "National library · SRU / IIIF API",
    role: ["Object metadata", "Creator attribution", "Dating"],
    identifier: "gallica.bnf.fr",
    coverage: "French posters, advertising, typography, printing, periodicals, public-domain visual documents.",
    material: "Catalogue records · IIIF image routes",
    acquired: CAPTURE_2026,
    rights:
      "SRU dc:rights and the Gallica / BnF item page are the controlling evidence. Public-domain signals may support an open-image state; otherwise imagery remains source-hosted.",
    status: "Verified source",
    contribution: "239 records",
  },
  {
    name: "Cooper Hewitt Collection API",
    org: "Smithsonian Design Museum",
    type: "Museum collection · GraphQL API",
    role: ["Object metadata", "Creator attribution", "Dating"],
    identifier: "collection.cooperhewitt.org",
    coverage: "Twentieth-century and contemporary design-object records: types, makers, dates.",
    material: "Collection metadata · image routes (manual review)",
    acquired: CAPTURE_2026,
    rights:
      "Treated as source-hosted imagery pending manual review; the ledger marks source role, fields, and rights dependency as requiring review.",
    status: "Verified source",
    contribution: "137 records",
  },
  {
    name: "Wikimedia Commons",
    org: "Wikimedia Foundation",
    type: "Open-license media repository · aggregator",
    role: ["Object metadata", "Open-image candidates", "Discovery"],
    identifier: "commons.wikimedia.org",
    coverage: "Poster and design-adjacent records; an open-license image supplement, not an original holding archive.",
    material: "extmetadata · licence fields · category-tree captures",
    acquired: CAPTURE_2026,
    rights:
      "Commons extmetadata licence fields control admission. Only open-license records are admitted as open-image candidates; uncertainty is retained because metadata can be user-supplied.",
    status: "Verified source",
    contribution: "Open-image expansions (authority-weighted, category-tree, region-balanced)",
  },
  {
    name: "Wellcome Collection Catalogue API",
    org: "Wellcome Trust",
    type: "Library / museum catalogue · API",
    role: ["Object metadata", "Rights reference", "Dating"],
    identifier: "wellcomecollection.org",
    coverage: "Public-health, exhibition, poster, print, and design-adjacent catalogue records with strong rights fields.",
    material: "Catalogue work records · thumbnail / IIIF routes",
    acquired: CAPTURE_2026,
    rights:
      "Wellcome item licence / access fields control image state. Media availability alone is not sufficient for reproduction.",
    status: "Verified source",
    contribution: "89 records",
  },
  {
    name: "GSU Library Digital Collections",
    org: "Georgia State University",
    type: "University digital collection · CONTENTdm",
    role: ["Object metadata", "Local rights reference"],
    identifier: "digitalcollections.library.gsu.edu",
    coverage: "Labor, civil-rights, theatre, newspaper, urban, and public print-culture records.",
    material: "singleitem fields · local rights statements · IIIF routes",
    acquired: CAPTURE_2026,
    rights:
      "The item-level local rights statement controls display. CONTENTdm / IIIF availability is source-hosted evidence, not an open reuse grant.",
    status: "Verified source",
    contribution: "85 records",
  },
  {
    name: "loc.gov API",
    org: "Library of Congress",
    type: "National library · API",
    role: ["Object metadata", "Rights advisory reference"],
    identifier: "loc.gov",
    coverage: "Prints, posters, WPA / FSA material, trade cards, pamphlets, catalogue records, rights advisories.",
    material: "PPOC records · rights advisories · image / thumbnail fields",
    acquired: CAPTURE_2026,
    rights:
      "The item-level rights advisory is authoritative. No universal public-domain assumption is made for Library of Congress records.",
    status: "Verified source",
    contribution: "50 records",
  },
  {
    name: "Art Institute of Chicago API",
    org: "Art Institute of Chicago",
    type: "Museum collection · API",
    role: ["Object metadata", "Creator attribution", "Dating"],
    identifier: "artic.edu",
    coverage: "Museum object records for posters, prints, and publications; artist metadata; IIIF identifiers.",
    material: "Artwork records · is_public_domain flag · IIIF identifiers",
    acquired: CAPTURE_2026,
    rights:
      "AIC is_public_domain and item-page evidence control promotion. IIIF identifiers alone do not authorize display.",
    status: "Verified source",
    contribution: "45 records",
  },
  {
    name: "V&A Collections API",
    org: "Victoria and Albert Museum",
    type: "Museum collection · API",
    role: ["Object metadata", "Creator attribution", "Object typing"],
    identifier: "collections.vam.ac.uk",
    coverage: "Design-object and collection metadata for posters, prints, ephemera, makers, and object types.",
    material: "System-number records · image fields · rights / credit",
    acquired: CAPTURE_2026,
    rights:
      "V&A item rights and image-permission statements control display. Image presence is not reuse permission.",
    status: "Verified source",
    contribution: "44 records",
  },
  {
    name: "Princeton University Library · Figgy",
    org: "Princeton University",
    type: "University digital collection · IIIF",
    role: ["Object metadata", "Dating"],
    identifier: "figgy.princeton.edu",
    coverage: "Posters, broadsides, banners, advertising print, scanned visual resources, ephemera.",
    material: "Catalogue records · manifest licences · IIIF services",
    acquired: CAPTURE_2026,
    rights:
      "Manifest licence and the Princeton source page control display. Explicit public-domain / CC0 signals may promote; otherwise imagery remains source-hosted.",
    status: "Verified source",
    contribution: "41 records",
  },
  {
    name: "Te Papa Collections Online",
    org: "Museum of New Zealand Te Papa Tongarewa",
    type: "Museum collection · API",
    role: ["Object metadata", "Regional coverage"],
    identifier: "tepapa.govt.nz",
    coverage: "Posters, protest graphics, music-publicity print, and public visual communication outside the European / North American canon.",
    material: "Object records · preview-image routes · media rights fields",
    acquired: CAPTURE_2026,
    rights:
      "Preview images are treated as restricted / source-hosted. No local copy or reuse claim is made.",
    status: "Verified source",
    contribution: "32 records",
  },
  {
    name: "Internet Archive",
    org: "Internet Archive",
    type: "Digital library · aggregator",
    role: ["Bibliographic evidence", "Context", "Discovery"],
    identifier: "archive.org",
    coverage: "Scanned books, manuals, periodicals, OCR text, and bibliographic context.",
    material: "Item metadata · file lists · OCR text",
    acquired: CAPTURE_2026,
    rights:
      "Collection and item terms vary. OCR is a discovery layer; strong claims require page / image verification or a stable citation basis.",
    status: "Verified source",
    contribution: "30 records",
  },
  {
    name: "NAIDOC Poster Gallery",
    org: "National NAIDOC Committee (Australia)",
    type: "Official poster gallery",
    role: ["Object metadata", "Cultural-context reference"],
    identifier: "naidoc.org.au",
    coverage: "Annual NAIDOC Indigenous Australian poster records.",
    material: "Poster item records · source-hosted image / PDF routes",
    acquired: CAPTURE_2026,
    rights:
      "Treated as source-hosted, with cultural and rights caution. No local copy or reuse claim is made.",
    status: "Verified source",
    contribution: "26 records",
  },
  {
    name: "DigitalNZ",
    org: "National Library of New Zealand",
    type: "National aggregator · API",
    role: ["Object metadata", "Discovery", "Regional coverage"],
    identifier: "digitalnz.org",
    coverage: "Periodical, advertising, newspaper, and public visual communication records from Aotearoa New Zealand.",
    material: "Aggregated records · rights / usage fields · thumbnails",
    acquired: CAPTURE_2026,
    rights:
      "DigitalNZ rights / usage fields plus the partner landing page control display. Open-image state requires open-enough item-level signals.",
    status: "Verified source",
    contribution: "21 records",
  },
  {
    name: "The Met Open Access",
    org: "The Metropolitan Museum of Art",
    type: "Museum collection · Open Access API",
    role: ["Object metadata", "Public-domain reference"],
    identifier: "metmuseum.org",
    coverage: "Museum object records and an open-access / public-domain comparison layer.",
    material: "Object records · open-access / public-domain flags",
    acquired: CAPTURE_2026,
    rights:
      "Met Open Access and public-domain fields are reviewed per item before an image is treated as open.",
    status: "Verified source",
    contribution: "15 records",
  },
  {
    name: "Cleveland Museum of Art Open Access API",
    org: "Cleveland Museum of Art",
    type: "Museum collection · Open Access API",
    role: ["Object metadata", "Open-image candidates"],
    identifier: "clevelandart.org",
    coverage: "Open-access museum object records with lower-risk image examples.",
    material: "Object records · share / licence fields",
    acquired: CAPTURE_2026,
    rights: "Open-access / licence fields are reviewed at item level before an image is treated as open.",
    status: "Verified source",
    contribution: "12 records",
  },
  {
    name: "Biblioteca Nacional Digital de Chile · Memoria Chilena",
    org: "Biblioteca Nacional de Chile",
    type: "National library / memory archive",
    role: ["Object metadata", "Regional coverage"],
    identifier: "bibliotecanacionaldigital.gob.cl",
    coverage: "Chilean political poster, mural, and movement print culture.",
    material: "Bibliographic records · source image routes",
    acquired: CAPTURE_2026,
    rights: "Images are treated as source-hosted unless an explicit open licence is separately verified.",
    status: "Verified source",
    contribution: "3 records",
  },
  {
    name: "Getty Research Portal",
    org: "Getty Research Institute",
    type: "Bibliographic portal",
    role: ["Bibliographic evidence", "Methodology reference"],
    identifier: "portal.getty.edu",
    coverage: "Bibliographic and digitized design-history support records.",
    material: "Bibliographic metadata · access links",
    acquired: CAPTURE_2026,
    rights: "Portal and contributing-institution terms govern use. Used primarily as bibliographic / context evidence.",
    status: "Reference only",
    contribution: "3 records",
  },
  {
    name: "South African History Archive",
    org: "South African History Archive (SAHA)",
    type: "Community / political archive",
    role: ["Object metadata", "Cultural-context reference"],
    identifier: "saha.org.za",
    coverage: "Anti-apartheid, Medu, labor, and resistance poster histories.",
    material: "Item pages · rights statements · preview-image routes",
    acquired: CAPTURE_2026,
    rights:
      "SAHA item pages warn that copyright may be held by postermakers or organisations; imagery remains source-hosted with no local copy.",
    status: "Verified source",
    contribution: "3 records",
  },
  {
    name: "AIATSIS",
    org: "Australian Institute of Aboriginal and Torres Strait Islander Studies",
    type: "Institutional authority / context",
    role: ["Cultural-context reference", "Authority"],
    identifier: "aiatsis.gov.au",
    coverage: "NAIDOC poster history and collection-level poster routes.",
    material: "Collection pages · scope notes · source text",
    acquired: CAPTURE_2026,
    rights: "Collection pages retained as context unless reliable item-level image evidence is extracted and reviewed.",
    status: "Reference only",
    contribution: "2 records",
  },
  {
    name: "Roots.sg",
    org: "National Heritage Board, Singapore",
    type: "National heritage collection",
    role: ["Object metadata", "Regional coverage"],
    identifier: "roots.gov.sg",
    coverage: "Multilingual signs, commercial objects, and everyday public graphic systems in Singapore.",
    material: "Object records · image routes · source descriptions",
    acquired: CAPTURE_2026,
    rights: "Object images are treated as source-hosted; no local copy or reuse claim is made.",
    status: "Verified source",
    contribution: "2 records",
  },
  {
    name: "chineseposters.net",
    org: "Stefan R. Landsberger collection / IISH",
    type: "Specialist poster archive",
    role: ["Object metadata", "Cultural-context reference"],
    identifier: "chineseposters.net",
    coverage: "Chinese political and campaign graphics.",
    material: "Item / theme records · rights notes",
    acquired: CAPTURE_2026,
    rights: "Specialist-archive terms control the record. The surface remains link-only unless item display permission is explicit.",
    status: "Verified source",
    contribution: "1 record",
  },
];

const scholarly: SourceEntry[] = [
  {
    name: "TRACE Open Inquiry register",
    org: "Modern Graphic Design Archive — Round 16B research",
    type: "Project research register",
    role: ["TRACE evidence"],
    identifier: "Internal registry · 11 scoped records",
    coverage: "Eleven scoped higher-order association hypotheses relevant to unresolved research inquiry.",
    material: "Structured hypothesis records with bounded scope, participants, and provenance",
    acquired: "2026 · Round 16B integration",
    rights: "Project research output. Records are read-only and carry explicit non-claim status.",
    status: "Open inquiry evidence",
  },
  {
    name: "Project methodology corpus",
    org: "Modern Graphic Design Archive",
    type: "Internal methodology documents",
    role: ["Methodology reference"],
    identifier: "Repository — docs/methodology/",
    coverage: "Production rulebook, evidence protocol, capture-period strategy, image / text enrichment rules.",
    material: "Written methodology and rulebook documents",
    acquired: "2026 · versioned with the release",
    rights: "Project-authored research output; no blanket reuse licence.",
    status: "Reference only",
  },
];

const datasets: SourceEntry[] = [
  {
    name: "Governed release projections",
    org: "Modern Graphic Design Archive",
    type: "Project-generated governed datasets",
    role: ["Object corpus", "TRACE data"],
    identifier: "Search v2 · Context v1 · Spacetime v1 · Exploration v2 · Open Inquiry v1",
    coverage: "The sealed public projection: 7,995 public documents; 16,106 context representations; 23 periods; 93 geographies; 21 validated associations; 11 open inquiries.",
    material: "Deterministic read models generated from the frozen database",
    acquired: "Generated with release v49",
    rights: "Project-generated. Machine-readable manifests are versioned and checksummed (see §7).",
    status: "Public record",
  },
  {
    name: "Controlled vocabularies",
    org: "Modern Graphic Design Archive",
    type: "Reference vocabularies",
    role: ["Classification reference"],
    identifier: "Object type · Theme · Movement · Geography · Period · Context term",
    coverage: "90 object types · 8 themes · 7 movements · 93 geographies · 23 decade periods · 25 context terms.",
    material: "Closed dictionaries bound to the release",
    acquired: "Fixed by the v49 projection",
    rights: "Project-defined. Values derive from public source records; no inferred aliases.",
    status: "Public record",
  },
  {
    name: "Unicode normalization (NFC / NFKC)",
    org: "Unicode Consortium",
    type: "Reference standard",
    role: ["Rights reference", "Methodology reference"],
    identifier: "Unicode Normalization Forms",
    coverage: "Applied to titles, credited labels, places, and identifiers for matching and exact lookup; display form is preserved.",
    material: "Normalization algorithm (standard)",
    acquired: "Standard, applied at index build",
    rights: "Open standard.",
    status: "Reference only",
  },
];

const design: SourceEntry[] = [
  {
    name: 'Alex Steinweiss — Columbia Records covers',
    org: 'Columbia Records, art director from 1939; the first illustrated album cover, 1940',
    type: 'Design-history precedent',
    role: ["Design reference"],
    identifier: 'Interface visual language only',
    coverage: 'One announced idea per cover; a limited, luminous palette; a single graphic device repeated with rhythm.',
    material: 'Historical precedent — not held or reproduced',
    acquired: "Cited as design influence",
    rights: 'Referenced for design methodology. Does not participate in archive object validation.',
    status: "Reference only",
  },
  {
    name: 'S. Neil Fujita — Columbia Records covers',
    org: 'Columbia Records, design director 1954–1960 (Time Out; Mingus Ah Um, 1959)',
    type: 'Design-history precedent',
    role: ["Design reference"],
    identifier: 'Interface visual language only',
    coverage: 'Colour as abstract field; painted blocks carrying the cover, with type set small beside them. The plates.',
    material: 'Historical precedent — not held or reproduced',
    acquired: "Cited as design influence",
    rights: 'Referenced for design methodology. Not an object-evidence source.',
    status: "Reference only",
  },
  {
    name: 'Jim Flora — Columbia Records covers',
    org: 'Columbia Records, 1942–1950 (the jazz covers of 1947)',
    type: 'Design-history precedent',
    role: ["Design reference"],
    identifier: 'Interface visual language only',
    coverage: "Cartoon-modern crowds: figures reduced to dots and lines, packed into a field. The homepage's field and crowd.",
    material: 'Historical precedent — not held or reproduced',
    acquired: "Cited as design influence",
    rights: 'Referenced for design methodology. Not an object-evidence source.',
    status: "Reference only",
  },
  {
    name: 'Postage stamp design, 1970s–2020s',
    org: 'SOZPHILEX 77 (Deutsche Post der DDR, 1977) · EFTA 50 years (Swiss Post, Demian Conrad, 2010) · HKSAR 25 (Hongkong Post, 2022)',
    type: 'Design-history precedent',
    role: ["Design reference"],
    identifier: 'Interface visual language only',
    coverage: 'Colour as a field, not a rule; one oversized figure cropped by its frame; a name set larger than its plate; a small line-drawn device.',
    material: 'Historical precedent — not held or reproduced',
    acquired: "Cited as design influence",
    rights: 'Referenced for design methodology. Does not participate in archive object validation.',
    status: "Reference only",
  },
  {
    name: 'Pictogram systems — Tokyo 1964, Munich 1972',
    org: 'Olympic design programmes (Tokyo 1964: Masaru Katsumi; Munich 1972: Otl Aicher)',
    type: 'Design-history precedent',
    role: ["Design reference"],
    identifier: 'Interface visual language only',
    coverage: 'Figures reduced to a head and a body on a grid; a crowd drawn as marks.',
    material: 'Historical precedent — not held or reproduced',
    acquired: "Cited as design influence",
    rights: 'Referenced for design methodology. Not an object-evidence source.',
    status: "Reference only",
  },
  {
    name: "The engraver's line — copperplate hatching, halftone, ruled loops",
    org: 'Print and security-printing tradition',
    type: 'Design-history precedent',
    role: ["Design reference"],
    identifier: 'Interface visual language only',
    coverage: "A circle rendered by lines, by dots, and by a lit engraving; white line on black. The homepage's opening studies.",
    material: 'Genre precedent — not held or reproduced',
    acquired: "Cited as design influence",
    rights: 'Referenced for design methodology. Not an object-evidence source.',
    status: "Reference only",
  },
  {
    name: 'LINE Seed JP, Instrument Sans and Baskervville (typefaces)',
    org: 'LY Corporation · Instrument · Baskervville project',
    type: 'Typographic precedent',
    role: ["Design reference"],
    identifier: 'Interface use only',
    coverage: "A heavy rounded grotesque for titles and numerals; a plain grotesque for reading on a 17px floor; a transitional serif for the wordmark's second line and set-apart statements.",
    material: 'Typefaces',
    acquired: "Cited as design influence",
    rights: 'Typefaces used under their own open licences (SIL Open Font License). Not an object-evidence source.',
    status: "Reference only",
  },
];

export const registerGroups: {
  key: string;
  title: string;
  blurb: string;
  entries: SourceEntry[];
}[] = [
  {
    key: "archives",
    title: "Archives & Collections",
    blurb:
      "Institutional catalogues and collections. Their metadata supports object description, attribution, and dating. Object imagery is not reproduced.",
    entries: archives,
  },
  {
    key: "scholarly",
    title: "Scholarly Research",
    blurb:
      "Research registers and methodology material. These support classification and unresolved inquiry; they do not validate a historical claim by their presence.",
    entries: scholarly,
  },
  {
    key: "datasets",
    title: "Datasets & Standards",
    blurb:
      "Project-generated governed datasets, controlled vocabularies, and reference standards that define how source material is projected.",
    entries: datasets,
  },
  {
    key: "design",
    title: "Design References",
    blurb:
      "Design-history and typographic precedents that shape the interface's visual language. They are not historical-evidence sources and take no part in archive object validation.",
    entries: design,
  },
];

/* ---- 3 · Provenance & acquisition ---------------------------- */

export const acquisitionChain: string[] = [
  "Source",
  "Acquisition",
  "Raw source-level record",
  "Normalization",
  "Review",
  "Public archive record",
];

export const acquisitionMethods: { method: string; note: string }[] = [
  { method: "Public API", note: "Official read APIs (SRU, REST, GraphQL) where a source provides one." },
  { method: "OAI-PMH / IIIF", note: "Harvesting endpoints and image manifests for catalogue and image routes." },
  { method: "Structured web capture", note: "Parsed capture of stable item pages where no API exists; raw payload preserved." },
  { method: "Dataset download", note: "Bulk open datasets and open-image sets, admitted only under item-level licence signals." },
  { method: "Repository / archive export", note: "Governed exports from the project's own frozen database." },
  { method: "Manual record entry", note: "Hand-entered records for targets with no machine-readable route; flagged for review." },
  { method: "Scholarly publication extraction", note: "Bibliographic and context evidence extracted from literature; not an object corpus." },
];

export const acquisitionNotes: string[] = [
  "Acquisition took place across 44 capture batches in 2026. Exact per-batch dates are recorded in the internal capture manifest.",
  "Sources are treated as frozen snapshots at acquisition time. A later change at a source does not automatically re-sync into the archive; a new capture and a new release are required.",
  "Every source carries a project role. A source used only as research evidence or design reference is marked as such and is not part of the object corpus.",
];

/* ---- 4 · Editorial / data transformation ------------------- */

export const transformationCategories: { name: string; example: string }[] = [
  { name: "Normalization", example: "Source place “München” → field: Place = München (form preserved; not expanded)." },
  { name: "Canonical ID assignment", example: "A stable public surface ID is assigned; the internal identifier is never exposed." },
  { name: "Date normalization", example: "Date text → numeric year bounds for interval comparison; prose dates are not inferred." },
  { name: "Deduplication & duplicate resolution", example: "Records sharing a source locator are merged or held; the decision is recorded." },
  { name: "Controlled-vocabulary mapping", example: "Source type strings → the closed object-type dictionary; distinct source values stay distinct." },
  { name: "Public / held filtering", example: "Records without complete source, rights, or citation evidence are held, not published." },
  { name: "Source-citation normalization", example: "Source citation fields are formatted consistently; the original identifier is retained." },
  { name: "Spelling normalization", example: "Unicode NFC / NFKC and safe diacritic folding for matching; display text is unchanged." },
];

export const transformationCaveat =
  "Transformation is not inference. Normalizing “München” to a Place field is description. Expanding a city to a country the source did not state, or asserting a movement the source did not record, is not permitted. Where the project adds an interpretation, it is marked as project inference, not presented as source content.";

/* ---- 5 · Rights & permissions ----------------------------- */

export const rightsIntro =
  "Rights are assessed per source and per kind of material. A source's descriptive metadata, the text it publishes, and any image it holds are three separate questions with three separate answers: a record can be fully citable while its image cannot be shown. The three columns set out what each assessment covers; the outcome for each source is carried in its register entry above.";

export const rightsGlobalVisual =
  "The presence of an image at an external source does not constitute reproduction permission within Modern Graphic Design Archive. Current archive object pages do not assume image-display rights.";

export const rightsColumns: { key: string; title: string; body: string }[] = [
  {
    key: "metadata",
    title: "Metadata",
    body: "Descriptive fields (title, credited label, date, place, object type) are used for description, search, and citation under each source's metadata terms or open-data licence. Normalized metadata is a project research output; reuse must preserve source attribution and any uncertainty.",
  },
  {
    key: "text",
    title: "Text & citation",
    body: "Source text is quoted only within each source's citation and quotation conditions. OCR and catalogue description are treated as discovery aids until verified against a page image or a stable citation basis.",
  },
  {
    key: "visual",
    title: "Visual material",
    body: "Image reproduction rights are assessed per item against the holding source. A public webpage is not a public-domain image, and accessible metadata is not image-reproduction permission. The current release holds zero positive visual-rights records; object pages show no image.",
  },
];

/* ---- 6 · Evidence & source status ------------------------ */

export const statusIntro =
  "Each entry in the register carries one status. It records how far the project has verified the source itself — its identity and the relevant record — and how it may be used, not whether anything built on it holds. A status is fixed with the release it belongs to; like any other change at a source, a change of status requires a new capture and a new release.";

export const evidenceStatusLegend: { status: string; meaning: string }[] = [
  { status: "Verified source", meaning: "Source identity and the relevant record have been directly verified." },
  { status: "Public record", meaning: "Eligible for public archive presentation in the current release." },
  { status: "Held", meaning: "Retained internally but excluded from the public projection pending complete evidence." },
  { status: "Open inquiry evidence", meaning: "Relevant to an unresolved research inquiry; explicitly not a validated result." },
  { status: "Reference only", meaning: "Used for methodology or design context, not as archive object evidence." },
];

export const evidenceStatusNote =
  "A source appearing in this register means the material exists and has been recorded. It does not mean that a TRACE association or historical relation built with it has been validated. Validation status is carried separately, in TRACE.";

/* ---- 7 · Version & reproducibility ---------------------- */

export const versionIntro =
  "The archive is published as sealed releases, and everything on this site — the register above, the object pages, the search index — belongs to one of them. The ledger names the current release; the integrity record beneath it gives the identifiers and digests that bind this page to that release, so that what is shown today can be checked against the sealed inputs later.";

export const versionRecord: { label: string; value: string }[] = [
  { label: "Archive release", value: "v49 — current public release (sealed)" },
  { label: "Source register version", value: "Compiled with the v49 release, 2026" },
  { label: "Last verified", value: "2026, with the v49 freeze" },
  { label: "Source treatment", value: "Frozen snapshots; no automatic re-sync" },
];

export const integrityRecord: { label: string; value: string }[] = [
  { label: "Release", value: "v49-api-contract-fresh-c" },
  { label: "Immutable source anchor", value: "v49-data-api-closure-20260821" },
  { label: "Canonical population input", value: "generated/public_surfaces_prefreeze_candidate_v48.json" },
  { label: "Input SHA-256", value: "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48" },
  { label: "Projection content digest", value: "e7ab41633b481d455bc3ceab3e2d0d2a1d5410b186b65bfb2697059182d1b49d" },
  { label: "Schema SHA-256", value: "df1e7741e59e5e6bf1ca80f2a33edfad1abb2fc6d95b57d4d6993b49917020dd" },
];

export const reproNote =
  "Machine-readable manifests for the search index, context, spacetime, exploration, and open-inquiry projections are versioned and checksummed in the project repository. The values above bind what is shown today to a fixed release so it can be re-checked later.";

/* ---- 8 · Source citation --------------------------------- */

export const citationPolicy =
  "Cite the original source first, with its most stable identifier (DOI, ISBN, archive catalogue ID, or collection ID). Then, where the archive's normalization is relied on, cite the archive provenance record. For how to cite the archive as a whole, see About.";

export const citationExample: { label: string; text: string }[] = [
  {
    label: "Original source",
    text: "[Institution or author]. [Title or collection]. [Stable identifier: DOI / ISBN / catalogue ID / collection ID]. Accessed [date].",
  },
  {
    label: "Archive provenance record",
    text: "Modern Graphic Design Archive. Source record [source name], release v49. https://mgdarchive.com/source",
  },
];
