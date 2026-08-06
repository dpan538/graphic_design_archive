import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import MobileResearchDashboard from "@/components/archive/about/MobileResearchDashboard";
import ProjectCitationPanel from "@/components/archive/about/ProjectCitationPanel";
import traceAtlas from "../../../public/data/trace-v48/atlas.json";

export const metadata = {
  title: "About and Methodology - Modern Graphic Design History",
  description:
    "Methodology, source strategy, evidence protocol, rights policy, and reproducible capture model for the Modern Graphic Design History archive index.",
};

const nav = [
  ["00", "Position", "#position"],
  ["01", "Object", "#object"],
  ["02", "Corpus", "#corpus"],
  ["03", "Capture", "#capture"],
  ["04", "Evidence", "#evidence"],
  ["05", "Coverage", "#coverage"],
  ["06", "Rights", "#rights"],
  ["07", "Surfaces", "#surfaces"],
  ["08", "Interface", "#interface"],
  ["09", "Reproducibility", "#reproducibility"],
  ["10", "Citation", "#citation"],
  ["11", "Limits", "#limits"],
];

const evidenceColumns = [
  ["01", "provenance"],
  ["02", "rights"],
  ["03", "image"],
  ["04", "text"],
  ["05", "coverage"],
  ["06", "limits"],
];

const publicDatasetStats = [
  ["Active objects", traceAtlas.counts.activeObjects.toLocaleString("en-US"), "Source-linked objects admitted to the frozen v48 active layer."],
  ["TRACE nodes", traceAtlas.counts.traceNodes.toLocaleString("en-US"), "Evidence nodes across documented research trees."],
  ["Evidence relations", traceAtlas.counts.traceEdges.toLocaleString("en-US"), "Typed, source-bounded TRACE edges; not inferred influence."],
  ["Research trees", String(traceAtlas.counts.activeTrees), "Active TRACE trees available for local and aggregate reading."],
  ["Source verified", traceAtlas.counts.sourceVerified.toLocaleString("en-US"), "Objects whose active evidence route reaches a verified source."],
  ["Metadata supported", traceAtlas.counts.metadataSupported.toLocaleString("en-US"), "Objects retained with a documented metadata evidence route."],
  ["Review / hold", traceAtlas.counts.reviewObjects.toLocaleString("en-US"), "Objects isolated from the active main layer for review."],
  ["TRACE auxiliary", String(traceAtlas.counts.auxiliaryObjects), "Non-counting photography or printmaking adjunct nodes."],
  ["Inferred influence", String(traceAtlas.counts.influenceEdges), "No historical influence edge is auto-generated."],
];

const sourceCoverageMetrics = [
  ["active_source_count", "104", "Distinct source_name values with at least one captured record."],
  ["candidate_source_count", "298", "Candidate or prospect sources; not counted as active coverage."],
  ["weighted_active_source_points", "103.85", "Active sources after region weighting; non-Western and local sources carry higher weights."],
  ["weighted_source_target", "200.00", "Initial launch target expressed as weighted source points."],
  ["source_pool_rate", "51.92%", "Weighted active source points divided by the weighted source target."],
  ["time_weighted_balance_rate", "43.50%", "Active-source balance across period bands."],
  ["source_coverage_rate_v1", "22.59%", "Main coverage rate: source_pool_rate multiplied by time balance."],
  ["region_weighted_balance_rate", "35.85%", "Diagnostic regional distribution balance."],
  ["strict_distribution_adjusted_source_coverage_rate", "8.10%", "Diagnostic only; additionally penalizes uneven regional distribution."],
];

const periodBalance = [
  ["pre_1930", "10 active sources", "467 records", "33.33% balance"],
  ["1930_1970", "26 active sources", "528 records", "37.14% balance"],
  ["1970_2000", "26 active sources", "291 records", "52.00% balance"],
  ["2000_2026", "25 active sources", "250 records", "50.00% balance"],
];

const weakestRegionDiagnostics = [
  ["Eastern Europe / Caucasus", "0 active", "2 candidates", "0.00% balance"],
  ["Latin America / Transregional", "0 active", "1 candidate", "0.00% balance"],
  ["Latin America and the Caribbean", "0 active", "3 candidates", "0.00% balance"],
  ["North America / Global digital", "0 active", "1 candidate", "0.00% balance"],
  ["Europe", "1 active", "2 candidates", "9.93% balance"],
  ["Global", "1 active", "3 candidates", "9.93% balance"],
  ["Mainland China", "1 active", "1 candidate", "9.93% balance"],
  ["Eastern Europe", "2 active", "21 candidates", "19.85% balance"],
];

const currentSources = [
  {
    name: "Gallica / BnF APIs",
    count: "239",
    image: "IMG02: 15 / IMG03: 224",
    route: "gallica.bnf.fr",
    role: "National-library SRU/IIIF source for French posters, advertising, typography, printing, periodicals, and public-domain visual documents.",
    fields:
      "SRU Dublin Core title, creator, date, description, format, relation, publisher, rights, ark identifier, and IIIF image or manifest links.",
    rights:
      "SRU dc:rights and the Gallica/BnF item page are the controlling evidence. Public-domain signals may support IMG03; otherwise IIIF remains source-hosted IMG02.",
  },
  {
    name: "Cooper Hewitt Collection GraphQL API",
    count: "137",
    image: "IMG02: 137",
    route: "collection.cooperhewitt.org",
    role: "Design-object records, collection metadata, object types, makers, dates, and image-route evidence for twentieth-century and contemporary design holdings.",
    fields:
      "GraphQL record fields and image endpoints require manual review in the current ledger before stronger rights or text claims are made.",
    rights:
      "Currently treated as source-hosted IMG02; the ledger explicitly marks the source role, fields, rights dependency, and text dependency as requiring manual review.",
  },
  {
    name: "Wikimedia Commons",
    count: "111",
    image: "IMG03: 111",
    route: "commons.wikimedia.org",
    role: "Open-license image supplement and discovery layer for poster/design-adjacent records. It is not treated as the original holding archive.",
    fields:
      "Page id, file description URL, imageinfo URL, extmetadata ObjectName, ImageDescription, Artist, Credit, Categories, LicenseShortName, and LicenseUrl.",
    rights:
      "Commons extmetadata license fields control admission. Only open-license records are admitted as IMG03 candidates, with uncertainty retained because metadata can be user supplied.",
  },
  {
    name: "Wellcome Collection Catalogue API",
    count: "89",
    image: "IMG00: 3 / IMG02: 81 / IMG03: 5",
    route: "wellcomecollection.org",
    role: "Public-health, exhibition, poster, print, and design-adjacent catalogue records with strong rights fields.",
    fields:
      "Catalogue work id, title, contributors, production date, description, subjects, thumbnail/IIIF/media links, and rights or license fields.",
    rights:
      "Wellcome item license/access fields control IMG02 or IMG03 assignment. Media availability alone is not sufficient.",
  },
  {
    name: "Georgia State University Library Digital Collections / CONTENTdm",
    count: "85",
    image: "IMG02: 85",
    route: "digitalcollections.library.gsu.edu",
    role: "Local/university CONTENTdm source for labor, civil-rights, theatre, newspaper, urban, and public print-culture records.",
    fields:
      "Collection alias/item id, singleitem fields, title, date, creator, description, subject, location, format/type, local rights statement, and IIIF imageUri.",
    rights:
      "Item-level local rights statement controls display. CONTENTdm imageUri or IIIF availability is source-hosted evidence, not an open reuse grant.",
  },
  {
    name: "Library of Congress loc.gov API",
    count: "50",
    image: "IMG01: 37 / IMG04: 13",
    route: "loc.gov",
    role: "Prints, posters, WPA/FSA material, trade cards, pamphlets, catalog records, and rights advisories.",
    fields:
      "loc.gov/PPOC id, title, contributor, date, notes, medium, repository, rights advisory, image/thumbnail fields, and item URL.",
    rights:
      "The item-level rights advisory is authoritative. The project makes no universal public-domain assumption for Library of Congress records.",
  },
  {
    name: "Art Institute of Chicago API",
    count: "45",
    image: "IMG00: 35 / IMG03: 9 / IMG04: 1",
    route: "artic.edu",
    role: "Museum object records for posters, prints, publications, dates, artist metadata, and IIIF image identifiers.",
    fields:
      "Artwork id, title, artist_display, date_display, place_of_origin, medium_display, classification_titles, image_id, and is_public_domain.",
    rights:
      "AIC is_public_domain and item-page evidence control promotion. IIIF image identifiers alone do not authorize display.",
  },
  {
    name: "V&A Collections API",
    count: "44",
    image: "IMG02: 25 / IMG04: 19",
    route: "collections.vam.ac.uk",
    role: "Design-object and collection metadata for posters, prints, ephemera, makers, object types, and collection context.",
    fields:
      "System number, title, artist/maker, date, object type, materials/techniques, collection, image fields, item URL, rights, and credit.",
    rights:
      "V&A item rights and image permission statements control display. Image presence is not treated as reuse permission.",
  },
  {
    name: "Princeton University Library Digital Collections / Figgy",
    count: "41",
    image: "IMG02: 41",
    route: "figgy.princeton.edu",
    role: "University-library Figgy/IIIF source for posters, broadsides, banners, advertising print, scanned visual resources, and ephemera.",
    fields:
      "Figgy catalog id, manifest label, metadata labels/values, date, extent/type, abstract/contents, manifest license, IIIF service, and image URL.",
    rights:
      "Manifest license and Princeton source page control display. Explicit public-domain or CC0 signals may promote; otherwise the record remains source-hosted IMG02.",
  },
  {
    name: "Te Papa Collections Online",
    count: "32",
    image: "IMG02: 32",
    route: "tepapa.govt.nz",
    role: "Aotearoa/New Zealand museum source for posters, protest graphics, music-publicity print, and public visual communication outside the dominant European/North American canon.",
    fields:
      "Object URL/id, title, created date, production/contributor metadata, object description, preview image URL, and media rights fields.",
    rights:
      "Preview images are treated as restricted/source-hosted IMG02 evidence. No local image copy or reuse claim is made.",
  },
  {
    name: "Internet Archive / text and periodical collections",
    count: "30",
    image: "IMG00: 29 / IMG03: 1",
    route: "archive.org",
    role: "Scanned books, manuals, periodicals, OCR, item metadata, and bibliography/context evidence.",
    fields:
      "Identifier, title, creator, date, metadata API file list, item URL, collection, description, OCR/text availability, and file evidence.",
    rights:
      "Collection and item metadata vary. OCR is a discovery layer; strong claims require page/image verification or a stable citation basis.",
  },
  {
    name: "NAIDOC Poster Gallery",
    count: "26",
    image: "IMG02: 26",
    route: "naidoc.org.au",
    role: "Official Indigenous Australian poster-gallery source for annual NAIDOC poster item records.",
    fields:
      "Poster item URL, title/year, poster title field, artist field, image alt text, source-hosted poster image/PDF links.",
    rights:
      "Treated as source-hosted IMG02 with cultural and rights caution. No local copy or open reuse claim is made.",
  },
  {
    name: "DigitalNZ",
    count: "21",
    image: "IMG03: 21",
    route: "digitalnz.org",
    role: "Aotearoa New Zealand aggregator for periodical, advertising, newspaper, and public visual communication records.",
    fields:
      "Record id, title, display_date/date, description, subject, collection/content partner, rights, usage, landing URL, and thumbnail URL.",
    rights:
      "DigitalNZ rights and usage fields plus the partner landing page control display. IMG03 requires open-enough item-level signals.",
  },
  {
    name: "The Met Open Access",
    count: "15",
    image: "IMG04: 15",
    route: "metmuseum.org",
    role: "Museum object records and public-domain/open-access comparison layer.",
    fields:
      "Object id, title, artist, object date, medium, classification, department, culture, object URL, and open-access/public-domain flags.",
    rights:
      "Met Open Access and public-domain fields are reviewed per item. Current blockers remain IMG04 where the image basis is insufficient.",
  },
  {
    name: "Cleveland Museum Open Access API",
    count: "12",
    image: "IMG03: 12",
    route: "clevelandart.org",
    role: "Open-access museum object records with lower-risk image examples and object metadata.",
    fields:
      "Accession/object id, title, creators, date, culture, type, technique, image URL, share/license fields.",
    rights:
      "Open-access/license fields are reviewed at item level before an image is treated as IMG03.",
  },
  {
    name: "Biblioteca Nacional Digital de Chile / Memoria Chilena",
    count: "3",
    image: "IMG02: 3",
    route: "bibliotecanacionaldigital.gob.cl",
    role: "National-library and memory-archive source for Chilean political poster, mural, and movement print culture.",
    fields:
      "Exact page URL, title, bibliographic description, source collection, date, thumbnail/source image URL.",
    rights:
      "Images are treated as source-hosted IMG02 unless an explicit open license is separately verified.",
  },
  {
    name: "Getty Research Portal",
    count: "3",
    image: "IMG04: 3",
    route: "portal.getty.edu",
    role: "Bibliographic and digitized design-history support records.",
    fields: "Portal title, URL, source institution, bibliographic metadata, and access link.",
    rights:
      "Portal and contributing-institution terms govern use. The source is used primarily as bibliographic/context evidence.",
  },
  {
    name: "South African History Archive",
    count: "3",
    image: "IMG02: 3",
    route: "saha.org.za",
    role: "Community/political archive source for anti-apartheid, Medu, labor, and resistance poster histories.",
    fields:
      "Exact page URL, title, date, subject, description, creator, format/access image notes, rights statement, and preview image URL.",
    rights:
      "SAHA item pages warn that copyright may be held by postermakers or organisations; images remain source-hosted IMG02 with no local copy.",
  },
  {
    name: "NAIDOC / AIATSIS",
    count: "2",
    image: "IMG04: 2",
    route: "aiatsis.gov.au",
    role: "Indigenous Australian authority/context source for NAIDOC poster history and collection-level poster routes.",
    fields: "Collection page URL, title, description, poster-history scope note, and source text excerpt.",
    rights:
      "Collection pages are retained as IMG04 unless reliable item-level poster image evidence is extracted and reviewed.",
  },
  {
    name: "Roots.sg / National Heritage Board Singapore",
    count: "2",
    image: "IMG02: 2",
    route: "roots.gov.sg",
    role: "Singapore national heritage source for multilingual signs, commercial objects, and everyday public graphic systems.",
    fields: "Object URL, title, image URL, collection name, date range, object type, and source description.",
    rights:
      "Object images are treated as source-hosted IMG02; no local copy or open reuse claim is made.",
  },
  {
    name: "Chinese Posters",
    count: "1",
    image: "IMG00: 1",
    route: "chineseposters.net",
    role: "Specialist poster-history source for Chinese political and campaign graphics.",
    fields:
      "Stable item or theme URL, title, date, creator/publisher if present, theme/category metadata, rights/source note.",
    rights:
      "Specialist archive terms control the record. The surface remains link-only unless item display permission is explicit.",
  },
];

const sourceDetails = new Map(currentSources.map((source) => [source.name, source]));
const activeSources = traceAtlas.topSources.map((source) => {
  const detail = sourceDetails.get(source.name);
  return {
    name: source.name,
    count: source.count.toLocaleString("en-US"),
    image: detail?.image ?? "object-level route",
    route: detail?.route ?? "source route recorded per object",
    role: detail?.role ?? "A major active v48 evidence provider. Object-level source, date, place, rights, and media fields remain controlling.",
    fields: detail?.fields ?? "Stable source identifier, title, date, object type, holding route, and record-specific evidence fields.",
    rights: detail?.rights ?? "Rights and image display are resolved per object. Provider membership alone never grants local display or reuse.",
  };
});

const productionStages = [
  ["Source registry", "Candidate institutions and repositories are classified by access method, source family, geography, period, rights clarity, and expected image/text path."],
  ["Capture batch", "Official APIs, OAI-PMH, IIIF, structured HTML, or browser capture are used in that order of preference; raw payloads are preserved before normalization."],
  ["Capture row", "A parsed row records source identifier, source URL, title, creator, date text, place, object type, rights text, image evidence, raw path, and access date."],
  ["Candidate pool", "Rows are checked for duplicate source locators, unstable routes, thin snippets, unresolved source ambiguity, and unsupported local display."],
  ["Review gates", "Source review, rights review, classification review, completeness scoring, and text-reading gates separate usable evidence from publication surfaces."],
  ["Surface generation", "Reviewed or staged records become sheets, cards, appendices, stubs, proposed cells, or unassigned research items through deterministic templates."],
];

const evidenceProtocol = [
  {
    title: "Evidence",
    body: "A statement directly recoverable from a source record, stable identifier, verified image, rights field, transcript, or preserved raw payload.",
  },
  {
    title: "Description",
    body: "A faithful normalization or paraphrase of source evidence; it may improve readability but cannot add new historical facts.",
  },
  {
    title: "Interpretation",
    body: "A claim about significance, influence, reception, movement membership, causality, comparative status, or historical consequence. It requires direct citation or explicit project-inference marking.",
  },
  {
    title: "Uncertainty",
    body: "A retained warning about date range, authorship, location, language/script, rights status, image parser status, or classification placement. Uncertainty is displayed rather than hidden.",
  },
];

const reviewGates = [
  ["Source URL", "The record has a stable landing page, source locator, or item URL, not only a search-result snippet."],
  ["Raw provenance", "The request, response, raw JSON/XML/HTML, IIIF manifest, OCR path, or parser context remains inspectable."],
  ["Identity", "The title or supplied label, source identifier, date/date_text, record family, and provider name are present."],
  ["Rights", "A rights note, rights field, source terms note, or item-level display decision exists before image promotion."],
  ["Image state", "IMG00-IMG04 is assigned independently of page size, folder type, or whether an image URL happens to be present."],
  ["Classification", "Region, theme, medium, and movement links distinguish exact, contextual, proposed, and unassigned placement."],
  ["Reading gate", "A full sheet requires enough grounded text to read as an archive record rather than only a table."],
  ["Completeness", "Main-sheet eligibility normally requires score >= 75 plus essential source, rights, date, classification, and citation gates."],
];

const imageStates = [
  ["IMG00", "Empty image frame with rights/source explanation and source link. Used when a visual object likely has an image but the project cannot display it safely."],
  ["IMG01", "Controlled thumbnail with credit and full source link. Used only under source-specific thumbnail constraints."],
  ["IMG02", "Source-hosted viewer, IIIF route, source-interface link, or non-local display behavior. No local copy is assumed."],
  ["IMG03", "Open/reusable image candidate with item-level evidence such as CC0, Public Domain Mark, explicit public domain, CC BY, or source-specific equivalent."],
  ["IMG04", "No image frame. Used for text, authority, bibliography, appendix, source dossier, or context-led surfaces."],
];

const sourceDependencyReferences = [
  ["Project GitHub repository", "https://github.com/dpan538/graphic_design_archive", "dpan538 / graphic_design_archive. GitHub-backed project repository for code, scripts, generated payloads, rulebooks, and frontend implementation; no blanket content or image reuse license is granted by this link."],
  ["Generated public payload", "frontend/public/data/public_surface_mock_v0.json", "Current static render payload for public surfaces, folders, source names, image states, rights labels, and tables."],
  ["Source dependency ledger", "data/source_dependency_ledger.csv", "Current major source dependencies, IMG-state distribution, reference fields, rights dependency, text dependency, and capture scripts."],
  ["Source coverage rate", "docs/capture/SOURCE_COVERAGE_RATE_v1.md", "Defines active source count, candidate source count, weighted target, period balance, and regional diagnostic coverage."],
  ["Production rulebook", "docs/methodology/ARCHIVE_PRODUCTION_RULEBOOK_v0.md", "Defines state transitions, promotion rules, IMG matrix, folder assignment, completeness gate, reading gate, and anti-patterns."],
  ["Image/text enrichment rules", "docs/methodology/IMAGE_AND_TEXT_ENRICHMENT_RULES_v0.md", "Defines image-state ladder, text layers, OCR limits, reading gate, evidence boundary, and editor-added text policy."],
  ["Surface generation pipeline", "docs/methodology/SURFACE_GENERATION_PIPELINE_v0.md", "Defines how registry, capture batches, review gates, surface payloads, folder aggregation, and search indexes are generated."],
  ["Rights strategy", "data/rights_strategy.csv", "Defines source-by-source rights/display policy for open APIs, reuse licenses, IIIF, aggregators, community archives, and web captures."],
];

const designReferences = [
  ["Design position", "The interface is best described as a civic ephemera index: a research-library system shaped by disposable public-information objects. It borrows from mid-century railway, postal, ticketing, permit, and instructional print, but uses those sources as archival grammar rather than nostalgic surface decoration."],
  ["Unité d’Habitation", "Le Corbusier’s Unité d’Habitation is used as a structural reference rather than an image motif: a legible frame, repeated yet differentiated units, communal circulation, and primary-color events held inside an otherwise disciplined concrete grid. On mobile this becomes modular information bays and short vertical routes, not an architectural imitation."],
  ["Open research library", "The base layer stays bright because the project is a reading room, not a sealed collection vault. Canvas, paper, surface, line, and Brown Black keep long text, source links, rights notes, and search behavior legible before any expressive color appears."],
  ["Japanese railway tickets", "The Japanese rail references in the research board, including Shonan Monorail Enoshima Line, Kawanishi-Noseguchi to Hirano extension material, Expo '70 rail tickets, and other commemorative passenger slips, inform the route-line diagrams, numbered gates, serial fields, pale ticket stock, yellow route bands, red overprints, and blue transit panels."],
  ["JR station stamp language", "The JR 150th station-stamp references, including Taura Station, Karuizawa Station, Niigata Station, and Nishi-Oyama Station, contribute the idea of a small public system rendered in two or three spot colors: local pictorial icons, station names, rough print texture, and clear geographic indexing."],
  ["Long Island Rail Road coupons", "The Long Island Rail Road World's Fair admission coupon reference supplies the coupon logic: cream stock, detachable panels, stamped red validation, dense rules, source-like serial numbers, and a layout where administrative proof is visually equal to destination."],
  ["Sports and aviation ticket stock", "The Yankee Stadium boxing tickets, Ohio Express Aviation ticket, and related admission references inform the ledger structure: oversized numbers, fare/date fields, box rules, overprint stamps, receipt-like repetition, and the idea that a record can be both a public object and an accounting object."],
  ["Postal stamp framing", "The road-safety stamp and contemporary stamp references supply perforated edges, small denomination fields, icon-first symbols, and compact framed scenes. In the interface this becomes badge, slip, and card behavior rather than literal stamp decoration."],
  ["Instructional booklet color", "The KTG Know the Game booklet covers and similar instructional print references support the high-contrast ephemera palette: grass green, process orange, station sky, signal yellow, brown-black line art, and strong single-purpose color blocks that can sit beside text without becoming navigation state."],
  ["Contemporary index cards", "The Crossreference cards, Trawelt tickets, ITYA stamp labels, and cyberspace-style terminal reference show how historical ephemera can be translated into contemporary modular UI: stacked cards, punched tabs, small command labels, ticket edges, and color-coded but still readable panels."],
  ["Four index axes", "Region, theme, movement, and medium are the only primary classification colors. They are deliberately separated from the ephemera palette so frontend navigation state never becomes confused with paper-stock, proof, ticket, or asset coloration."],
  ["Evidence columns", "The opening rail and repeated table logic establish six recurring categories: provenance, rights, image, text, coverage, and limits. A column can be empty, but the category remains visible; absence is part of the record rather than a layout failure."],
  ["Empty image frame", "The fixed image bay is a rights statement. IMG00 does not mean failure; it marks a visual object whose image evidence is expected but withheld, source-hosted, parser-incomplete, or rights-unclear. Absence is therefore rendered as evidence, not hidden as a broken asset."],
  ["Typography as boundary", "IBM Plex Sans carries readable explanation; IBM Plex Mono carries IDs, gates, counts, source names, and ledger labels. The distinction keeps authored prose separate from audit fields and prevents normalized text from pretending to be raw evidence."],
  ["Single Brown Black", "Brown Black replaces pure black everywhere. It reads like ticket ink on paper, softens the interface, and gives rules, text, icons, and shadows one shared material source."],
  ["Color as operation", "Color is assigned by job: index colors identify folder axes, ephemera colors build cards and slips, and readable variants are used when small text needs contrast. The palette is therefore a protocol for use, not a general mood board."],
];

const paletteGroups = [
  {
    title: "Library base",
    body: "Reading environment and the only black.",
    colors: [
      ["Canvas", "#FFFCF2"],
      ["Paper", "#F7F2E2"],
      ["Surface", "#EDE7D6"],
      ["Line", "#CFC6AF"],
      ["Brown Black", "#2E2925"],
    ],
  },
  {
    title: "Index axes",
    body: "Navigation and classification only.",
    colors: [
      ["Region", "#1F5FD1"],
      ["Theme", "#138B5E"],
      ["Movement", "#7466D6"],
      ["Medium", "#E83D3B"],
    ],
  },
  {
    title: "Ephemera stock",
    body: "Ticket, stamp, railway, proof, and card material colors.",
    colors: [
      ["Ticket Cream", "#E9DDBB"],
      ["Newsprint Grey", "#BFC2B8"],
      ["Cardboard Tan", "#C79255"],
      ["Ochre Stock", "#D7A94C"],
      ["Signal Yellow", "#F3D64E"],
      ["Process Orange", "#FF8A24"],
      ["Grass Stock", "#78C98D"],
      ["Olive Card", "#A9B15A"],
      ["Harbor Teal", "#287F82"],
      ["Grid Mint", "#9AD9C9"],
      ["Station Sky", "#69B5D6"],
      ["Railway Blue", "#2F74B7"],
      ["Transit Indigo", "#3B4D9B"],
      ["Register Pink", "#F239A6"],
      ["Ledger Mauve", "#C59BC7"],
      ["Copper Ink", "#B46A45"],
    ],
  },
];

const citationFields = [
  ["Required", "Title or supplied title, creator when known, date/date range, source name, stable source URL, access date, rights statement, and Modern Graphic Design History record ID."],
  ["Recommended", "Collection name, object type, place, language/script, image state, original identifier, capture script/adapter, and uncertainty note."],
  ["Project citation", "Modern Graphic Design History, Archive Box record, record ID, source name, source URL, accessed date, and rights/image-state note."],
  ["Image citation", "Cite the original holding institution or source page. Do not cite this interface as image owner unless a future record explicitly says so."],
];

const licensePolicy = [
  {
    label: "Interface and writing",
    status: "Prototype copyright retained",
    note: "The about-page text, palette system, research-library composition, and printed-ephemera interface design are project-authored research outputs and are not automatically open licensed.",
  },
  {
    label: "Project code",
    status: "GitHub-backed repository / no public license declared",
    note: "The project repository is dpan538/graphic_design_archive. The frontend package is marked private and no repository license is declared; treat code reuse as permission-required until a LICENSE file is added.",
  },
  {
    label: "Normalized metadata",
    status: "Source-cited research index",
    note: "Normalized titles, dates, routes, folders, and notes are produced for citation and navigation. Reuse must preserve source attribution and uncertainty.",
  },
  {
    label: "Images and scans",
    status: "Original source terms control",
    note: "Images, scans, thumbnails, IIIF canvases, and viewer captures remain governed by the holding institution, creator, publisher, collection, or item page.",
  },
  {
    label: "Open-source tools",
    status: "Tool-specific licenses",
    note: "Scrapy, Crawlee, Playwright, Browsertrix, pywb, ArchiveBox, and related tools keep their own licenses; those licenses do not transfer rights in captured source material.",
  },
  {
    label: "Future release",
    status: "License review required",
    note: "A public release should choose separate licenses for code and project-authored metadata while keeping third-party source terms and item-level rights separate.",
  },
];

function Ledger({ rows }: { rows: string[][] }) {
  return (
    <div className="about-ledger">
      {rows.map(([label, ...rest]) => (
        <div key={label} className="contents">
          <strong>{label}</strong>
          <span>{rest.join(" / ")}</span>
        </div>
      ))}
    </div>
  );
}

function PaletteSwatches() {
  return (
    <div className="about-palette-grid">
      {paletteGroups.map((group) => (
        <div key={group.title} className="about-palette about-hover-panel">
          <div className="about-palette__head">
            <h3>{group.title}</h3>
            <p>{group.body}</p>
          </div>
          <div className="about-palette__swatches">
            {group.colors.map(([name, value]) => (
              <div
                key={name}
                className="about-swatch"
                style={{ ["--swatch" as string]: value }}
              >
                <span aria-hidden="true" />
                <strong>{name}</strong>
                <code>{value}</code>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function Accordion({
  title,
  kicker,
  children,
  open = false,
}: {
  title: string;
  kicker?: string;
  children: React.ReactNode;
  open?: boolean;
}) {
  return (
    <details className="about-accordion about-hover-panel" open={open}>
      <summary>
        <span>{kicker}</span>
        <strong>{title}</strong>
      </summary>
      <div className="about-accordion__body">{children}</div>
    </details>
  );
}

function AboutPageMain() {
  return (
    <div className="about-shell">
      <aside className="about-nav" aria-label="About page sections">
        <a href="#position" className="about-nav__title">Method guide</a>
        {nav.map(([number, label, href]) => (
          <a key={href} href={href} className="about-nav__link">
            <span>{number}</span>
            {label}
          </a>
        ))}
      </aside>

      <article className="about-doc">
        <MobileResearchDashboard
          activeObjects={traceAtlas.counts.activeObjects}
          traceEdges={traceAtlas.counts.traceEdges}
          activeTrees={traceAtlas.counts.activeTrees}
          sourceVerified={traceAtlas.counts.sourceVerified}
          metadataSupported={traceAtlas.counts.metadataSupported}
          influenceEdges={traceAtlas.counts.influenceEdges}
          decades={traceAtlas.decades}
          decadeTotals={traceAtlas.decadeTotals}
          relationTypes={traceAtlas.relationTypes}
        />
        <header id="position" className="about-hero about-hover-panel">
          <div className="about-crumbs">
            <a href="/">Archive Box</a>
            <span>/</span>
            <span>About and Methodology</span>
          </div>
          <div className="about-rail" aria-label="Archive evidence columns">
            {evidenceColumns.map(([number, label]) => (
              <div key={label} className="about-hover-panel">
                <span>{number}</span>
                {label}
              </div>
            ))}
          </div>
          <p className="label-caps text-ink-soft">00 / methodological position</p>
          <h1>Modern Graphic Design History</h1>
          <p className="about-hero__desktop-copy">
            is a rights-aware archive index and research interface for studying
            modern graphic design through distributed, source-returnable
            evidence rather than through a single canonical image collection.
          </p>
          <p className="about-hero__desktop-copy">
            The project treats graphic design history as a problem of
            provenance, classification, access, rights, and representational
            imbalance. Its public pages are generated from structured source
            records, not composed as isolated essays or image plates.
          </p>
          <p className="about-hero__mobile-copy">
            A rights-aware research index for reading modern graphic design
            through objects, time, place, media, and recoverable source evidence.
          </p>
          <p className="about-hero__note">
            Data version: v48 · 15,923 active objects · frozen research snapshot.
            All claims remain bounded by source records, review gates, and the
            explicit no-inferred-influence rule.
          </p>
        </header>

        <section id="object" className="about-section about-hover-panel">
          <div className="about-section__num">01</div>
          <div>
            <p className="label-caps text-ink-soft">research object</p>
            <h2>The archive indexes evidence about graphic design, not possession of graphic design.</h2>
            <p>
              The unit of work is a source-grounded record: a poster, trade
              card, periodical issue, manual, catalogue, sign system, exhibition
              page, campaign graphic, institutional record, designer authority
              trace, or contextual text that can be tied to a stable source
              locator. The project does not treat image availability as
              historical importance, and it does not treat a retrieved image URL
              as permission to display or reuse an image.
            </p>
            <div className="about-method-grid">
              {evidenceProtocol.map((item) => (
                <div key={item.title} className="about-method about-hover-panel">
                  <h3>{item.title}</h3>
                  <p>{item.body}</p>
                </div>
              ))}
            </div>
            <Accordion title="Inclusion boundary" kicker="scope" open>
              <p>
                A record may enter the candidate pool when it has a recoverable
                source path and a defensible relation to graphic communication:
                typography, print, advertising, poster culture, identity
                systems, public information, publication design, exhibition
                graphics, interface culture, design education, or archive
                documentation. It may become public only after source, rights,
                classification, and citation gates make the record auditable.
              </p>
              <p>
                Exclusion is not a claim that a work is historically
                irrelevant. It normally means that the project cannot yet
                verify source identity, rights posture, citation basis, image
                behavior, or responsible classification.
              </p>
            </Accordion>
          </div>
        </section>

        <section id="corpus" className="about-section about-hover-panel">
          <div className="about-section__num">02</div>
          <div>
            <p className="label-caps text-ink-soft">corpus and source dependency</p>
            <h2>Current public data is a staged, source-led corpus.</h2>
            <p>
              The frozen v48 active layer contains 15,923 source-linked design
              objects. The register below lists its largest active evidence
              providers; it is a methodological disclosure of dependency, not
              an ownership claim over their materials.
            </p>
            <div className="about-stat-grid">
              {publicDatasetStats.map(([label, value, note]) => (
                <div key={label} className="about-stat about-hover-panel">
                  <span>{label}</span>
                  <strong>{value}</strong>
                  <p>{note}</p>
                </div>
              ))}
            </div>
            <Accordion title="Largest active source routes" kicker="source register">
              <div className="about-source-table">
                <div className="about-source-table__head">source</div>
                <div className="about-source-table__head">route / evidence</div>
                <div className="about-source-table__head">objects</div>
                {activeSources.map((source) => (
                  <details key={source.name} className="about-source-item">
                    <summary className="about-source-summary">
                      <strong>{source.name}</strong>
                      <span>{source.route} / {source.image}</span>
                      <span className="about-source-count">{source.count}</span>
                    </summary>
                    <div className="about-source-detail">
                      <div>
                        <strong>Coverage role</strong>
                        <p>{source.role}</p>
                      </div>
                      <div>
                        <strong>Rights dependency</strong>
                        <p>{source.rights}</p>
                      </div>
                      <div>
                        <strong>Reference fields</strong>
                        <p>{source.fields}</p>
                      </div>
                    </div>
                  </details>
                ))}
              </div>
            </Accordion>
          </div>
        </section>

        <section id="capture" className="about-section about-hover-panel">
          <div className="about-section__num">03</div>
          <div>
            <p className="label-caps text-ink-soft">capture and normalization</p>
            <h2>The pipeline preserves provenance before it creates interpretation.</h2>
            <p>
              Capture is not publication. A captured payload first becomes a
              candidate row; only after source review, rights review,
              duplicate/source-locator checks, folder assignment, completeness
              scoring, and reading gates can it become a public surface.
            </p>
            <div className="about-method-grid">
              {productionStages.map(([title, body]) => (
                <div key={title} className="about-method about-hover-panel">
                  <h3>{title}</h3>
                  <p>{body}</p>
                </div>
              ))}
            </div>
            <Accordion title="Production sequence" kicker="workflow" open>
              <p className="about-code-line">
                source registry -&gt; capture batches -&gt; raw payloads -&gt;
                capture rows -&gt; candidate pool -&gt; source review -&gt; rights
                review -&gt; completeness scoring -&gt; source records -&gt; surface
                assignment -&gt; folder/search generation -&gt; static rendering
              </p>
              <p>
                The frontend reads static JSON. It does not call remote
                archives, LLMs, or image services at runtime to invent content.
                Record fields, tables, rights labels, image states, and folder
                memberships are carried in the generated payload.
              </p>
            </Accordion>
          </div>
        </section>

        <section id="evidence" className="about-section about-hover-panel">
          <div className="about-section__num">04</div>
          <div>
            <p className="label-caps text-ink-soft">evidence protocol</p>
            <h2>Every public claim is assigned to a recoverable evidence layer.</h2>
            <p>
              Descriptive writing in this interface is a normalization layer.
              It can summarize, clarify, classify, and warn, but it cannot
              substitute for missing source evidence. OCR is treated as a
              discovery and snippet layer until verified against page images or
              a stable citation basis.
            </p>
            <div className="about-evidence">
              <span>source URL</span>
              <span>stable identifier</span>
              <span>raw capture</span>
              <span>access date</span>
              <span>date evidence</span>
              <span>rights basis</span>
              <span>image state</span>
              <span>parser status</span>
              <span>classification rationale</span>
              <span>uncertainty note</span>
              <span>citation basis</span>
              <span>capture script</span>
            </div>
            <Accordion title="Review gates for publication" kicker="gates" open>
              <Ledger rows={reviewGates} />
            </Accordion>
          </div>
        </section>

        <section id="coverage" className="about-section about-hover-panel">
          <div className="about-section__num">05</div>
          <div>
            <p className="label-caps text-ink-soft">coverage metrics</p>
            <h2>Coverage is weighted against imbalance, not only counted.</h2>
            <p>
              The source coverage metric separates active captured sources from
              candidate sources, then weights source breadth by region and
              period. This prevents the archive from looking complete merely
              because Western museum APIs or open image repositories are easier
              to harvest.
            </p>
            <div className="about-stat-grid about-stat-grid--compact">
              {sourceCoverageMetrics.map(([label, value, note]) => (
                <div key={label} className="about-stat about-hover-panel">
                  <span>{label}</span>
                  <strong>{value}</strong>
                  <p>{note}</p>
                </div>
              ))}
            </div>
            <Accordion title="Period balance" kicker="diagnostic">
              <Ledger rows={periodBalance} />
            </Accordion>
            <Accordion title="Weakest regional diagnostics" kicker="diagnostic">
              <Ledger rows={weakestRegionDiagnostics} />
            </Accordion>
          </div>
        </section>

        <section id="rights" className="about-section about-hover-panel">
          <div className="about-section__num">06</div>
          <div>
            <p className="label-caps text-ink-soft">rights and image policy</p>
            <h2>Image state is an evidence decision, not a layout preference.</h2>
            <p>
              The project indexes and links before it possesses. Unknown or
              ambiguous image rights default to non-display behavior. Open
              source software, public web access, thumbnails, IIIF services, or
              API image URLs do not by themselves grant reuse rights.
            </p>
            <Ledger rows={imageStates} />
            <Accordion title="Copyright and takedown posture" kicker="notice" open>
              <p>
                Modern Graphic Design History is an index and research
                interface. Copyright, neighbouring rights, database rights,
                trademark rights, personality rights, cultural protocols, and
                contractual access terms may remain with original creators,
                publishers, institutions, estates, communities, or source
                platforms.
              </p>
              <p>
                Questionable records should be downgraded to IMG00 or removed
                from public rendering while source rights are reviewed. Raw
                captures and screenshots are verification material, not
                automatically public assets.
              </p>
            </Accordion>
          </div>
        </section>

        <section id="surfaces" className="about-section about-hover-panel">
          <div className="about-section__num">07</div>
          <div>
            <p className="label-caps text-ink-soft">surface generation</p>
            <h2>Templates express record state.</h2>
            <p>
              A main sheet is not the default destination. Records may become
              main sheets, sub-sheets, appendices, text pages, cards, slips,
              bookmarks, fallback stubs, proposed-cell items, unassigned items,
              or deprecated rows according to evidence strength and publication
              role.
            </p>
            <Accordion title="Surface assignment rule" kicker="logic" open>
              <p>
                Main-sheet eligibility normally requires a stable identity,
                source URL, provider name, title or label, date/date_text,
                record family, rights state, IMG state, at least one folder or
                proposed/unassigned state, citation seed, and enough grounded
                text to read as an archive record. A strong image alone cannot
                promote a record.
              </p>
              <p>
                Thin but useful records can remain public as cards, support
                packets, appendices, or bookmarks. This keeps archival gaps
                visible without overstating evidentiary completeness.
              </p>
            </Accordion>
          </div>
        </section>

        <section id="interface" className="about-section about-hover-panel">
          <div className="about-section__num">08</div>
          <div>
            <p className="label-caps text-ink-soft">design research</p>
            <h2>Interface structure is part of the research method.</h2>
            <p>
              The design direction is a civic ephemera index: a contemporary
              research-library interface built from the logic of public,
              issued, numbered, stamped, routed, and discardable print. Its
              closest design lineage is not a museum archive skin, but the
              working modernism of railway tickets, station stamps, postal
              stamps, admission coupons, index cards, proof sheets, and
              instructional booklets.
            </p>
            <p>
              The research board points to specific source families: Japanese
              railway commemorative tickets and station-stamp graphics, Long
              Island Rail Road World's Fair coupons, Yankee Stadium and aviation
              ticket stock, road-safety postage stamps, KTG instructional
              booklet covers, and contemporary card/ticket experiments such as
              Crossreference, Trawelt, ITYA stamp labels, and cyberspace-style
              command panels. The interface translates those references into
              grid behavior, evidence columns, serial labels, route marks,
              perforation cues, validation stamps, and paper-stock color.
            </p>
            <p>
              Color is treated as a working protocol. Base colors preserve
              reading; four index colors identify folder axes; ephemera colors
              build cards, slips, badges, and evidence surfaces. These layers
              must remain distinct, because a classification color should never
              be mistaken for paper stock, proof, ticket, or asset coloration.
            </p>
            <PaletteSwatches />
            <Accordion title="Design research register" kicker="references">
              <div className="about-reference-grid">
                {designReferences.map(([title, body]) => (
                  <div key={title} className="about-reference about-hover-panel">
                    <h3>{title}</h3>
                    <p>{body}</p>
                  </div>
                ))}
              </div>
            </Accordion>
          </div>
        </section>

        <section id="reproducibility" className="about-section about-hover-panel">
          <div className="about-section__num">09</div>
          <div>
            <p className="label-caps text-ink-soft">reproducibility and open tools</p>
            <h2>Tooling is auditable infrastructure, not a permission system.</h2>
            <p>
              The stack privileges official APIs, preservation of raw payloads,
              transparent scripts, deterministic payload generation, and static
              rendering. Tool licenses govern software use only; captured
              source records keep their own terms.
            </p>
            <Accordion title="Project ledgers and rulebooks" kicker="references">
              <Ledger rows={sourceDependencyReferences} />
            </Accordion>
          </div>
        </section>

        <section id="citation" className="about-section about-hover-panel">
          <div className="about-section__num">10</div>
          <div>
            <p className="label-caps text-ink-soft">citation and license notice</p>
            <h2>Cite the holding source first, then this interface as an index layer.</h2>
            <p>
              Citations should preserve source authority, access date, rights
              statement, image state, uncertainty, and this project's record
              identifier. When a date, creator, or rights statement is
              uncertain, that uncertainty should remain in the citation note.
            </p>
            <Ledger rows={citationFields} />
            <ProjectCitationPanel />
            <Accordion title="License status" kicker="notice">
              <div className="license-grid">
                {licensePolicy.map((item) => (
                  <div key={item.label} className="license-card about-hover-panel">
                    <p className="label-caps">{item.label}</p>
                    <h3>{item.status}</h3>
                    <p>{item.note}</p>
                  </div>
                ))}
              </div>
            </Accordion>
          </div>
        </section>

        <section id="limits" className="about-section about-section--last about-hover-panel">
          <div className="about-section__num">11</div>
          <div>
            <p className="label-caps text-ink-soft">claim boundaries</p>
            <h2>The archive refuses false completeness.</h2>
            <p>
              The current prototype cannot claim global completeness, equal
              source density, uniform rights clarity, or final historical
              classification. It refuses to treat availability as importance,
              English search terms as global coverage, image presence as
              permission, or a missing result as proof that a design history did
              not exist.
            </p>
            <Accordion title="Known methodological limits" kicker="limits" open>
              <p>
                Active source coverage remains uneven by region and period.
                Some strong candidate areas still lack captured records; some
                captured records are source-hosted or link-only because rights
                evidence is incomplete; some OCR and catalogue descriptions are
                discovery aids rather than verified interpretive sources.
              </p>
              <p>
                These limits are retained as part of the archive's scholarly
                apparatus. A successful capture is evidence for a bounded
                source claim, not a total history.
              </p>
            </Accordion>
          </div>
        </section>
      </article>
    </div>
  );
}

export default function AboutPage() {
  return <ArchiveShell main={<AboutPageMain />} activeNav="about" mainScroll />;
}
