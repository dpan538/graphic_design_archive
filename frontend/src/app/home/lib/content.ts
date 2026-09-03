/* Homepage copy — final per FRONTEND_DESIGN_DECISION.md §2a / §7e. Data only;
   both the desktop and mobile trees read from here. No API. */

/* Two short paragraphs — body-text scale, not a display block. The name
   ("Modern Graphic Design Archive") is the visual focal point above them. */
export const IDENTITY_P1 =
  "A digital humanities research archive for modern graphic design history — built from verified records, explicit provenance, and evidence-bounded computational research.";
export const IDENTITY_P2 =
  "It is an extensible research infrastructure for locating, reading, and examining design-historical records, not a complete history of graphic design.";

/* Combined form, for contexts that want one string (metadata, mobile draft). */
export const IDENTITY = `${IDENTITY_P1} ${IDENTITY_P2}`;

/* A short pull-form of the identity line, for the compacted / heading state. */
export const IDENTITY_SHORT = "A digital humanities research archive for modern graphic design history.";

/* Desktop Identity's headline (left of the description block) and closing
   tagline (under "MGDA", on black) — both user-specified, not derived. */
/* Split so only the last word carries the italic — the rest is upright. */
export const IDENTITY_HEADLINE_LEAD = "Design history, verified and ";
export const IDENTITY_HEADLINE_ACCENT = "connected.";
/* The bridge between the ellipsis of spheres and the field they scatter
   into — it appears, then disperses to become the arrangement. */
export const IDENTITY_BRIDGE = "Where design history becomes traceable.";

/* Two stages, not one: the first line types out under MGDA, then gives way
   to the second as the reader keeps scrolling. */
export const IDENTITY_TAGLINE = "Read. Trace. Reframe.";
export const IDENTITY_TAGLINE_SETTLED = "A research archive for modern design.";

/* Act I's gallery. Laid out the way a museum collection grid actually is
   (ref: MoMA / The Met) — plate first, then creator, then title-and-date,
   then medium, then dimensions, in small type under a left-aligned image.
   The reader is meant to take it at face value and only then notice that
   every plate is empty.

   Honesty constraints, deliberately kept: no invented work titles and no
   invented attributions to named designers. The creator line uses the
   archive's own real convention for absent data ("Not recorded"), the type
   and medium are real vocabulary, and the dimensions are plain plausible
   measurements — nothing here claims to be a specific catalogued record.
   `ratio` drives each plate's aspect so the rows break like a real grid. */
export type GalleryCard = {
  type: string;
  year: string;
  medium: string;
  dims: string;
  ratio: string;
};
export const GALLERY_CARDS: GalleryCard[] = [
  { type: "Exhibition poster", year: "1962", medium: "Screenprint", dims: "101 × 64 cm", ratio: "3 / 4" },
  { type: "Book cover", year: "1948", medium: "Letterpress", dims: "21 × 14 cm", ratio: "4 / 5" },
  { type: "Type specimen", year: "1935", medium: "Letterpress", dims: "30 × 21 cm", ratio: "1 / 1" },
  { type: "Concert poster", year: "1967", medium: "Offset lithograph", dims: "84 × 59 cm", ratio: "2 / 3" },
  { type: "Magazine cover", year: "1955", medium: "Offset lithograph", dims: "33 × 25 cm", ratio: "4 / 5" },
  { type: "Record sleeve", year: "1969", medium: "Offset lithograph", dims: "31 × 31 cm", ratio: "1 / 1" },
  { type: "Travel poster", year: "1931", medium: "Lithograph", dims: "100 × 62 cm", ratio: "3 / 4" },
  { type: "Annual report", year: "1978", medium: "Offset lithograph", dims: "28 × 21 cm", ratio: "4 / 5" },
  { type: "Political poster", year: "1968", medium: "Screenprint", dims: "76 × 51 cm", ratio: "2 / 3" },
  { type: "Exhibition catalogue", year: "1959", medium: "Offset lithograph", dims: "24 × 17 cm", ratio: "4 / 5" },
  { type: "Packaging", year: "1964", medium: "Printed board", dims: "18 × 12 cm", ratio: "1 / 1" },
  { type: "Signage system", year: "1972", medium: "Enamel on steel", dims: "40 × 40 cm", ratio: "1 / 1" },
];

export const CONTRIBUTION_LEDGER: { value: string; label: string }[] = [
  { value: "40,000+", label: "candidate records examined" },
  { value: "15,923", label: "canonical records established" },
  { value: "7,995", label: "records currently published" },
];

export const CONTRIBUTION_SINCE = "Since 2024";

/* Kept for HomeMobile (unchanged this round). Desktop's split-screen build
   uses the two more specific paragraphs below instead. */
export const CONTRIBUTION_BODY =
  "Records were gathered across heterogeneous archives and collections, then reconciled, screened, and reviewed before entering the governed archive. Records that do not meet current evidence, publication, or rights conditions are held, not silently included.";

/* Desktop Contribution panel — two hedged paragraphs (HOMEPAGE_DESIGN_v1.md §4.1).
   Primary: methodology. Deliberately does not claim exhaustive manual review or
   expert art-historical review — the actual process is spot-check + semantic-level
   screening. */
export const CONTRIBUTION_METHOD =
  "Records move from candidate to canonical to published through reconciliation and screening — spot-checked and reviewed at a semantic level against evidence, publication, and rights conditions, not an exhaustive manual pass or an expert art-historical review. Records that do not clear that bar are held, not silently dropped.";

/* Secondary: source-coverage direction. Verified against
   docs/capture/NONMAINSTREAM_SOURCE_SUCCESS_REGISTRY_2026_V3.md — framed as an
   active infrastructure direction, since that registry pass is source-level and
   has not yet fed the published record set. Do not imply current published
   records already draw heavily from these sources. */
export const CONTRIBUTION_SOURCING =
  "Source discovery has actively extended into regions long under-covered by mainstream design archives — museums, libraries, cultural centres, and archives across Africa, Latin America and the Caribbean, MENA, Southeast Asia, Eastern Europe, and South and Central Asia. This is an ongoing infrastructure direction, not yet a completed share of the published archive.";

/* ---- Contribution, laid out against the Coreaxis reference: an explanatory
   white upper half (breadcrumb, title, intro, three columns) over a blue
   lower half (concept diagram left, numbered table right).
   Copy is deliberately fuller than before — the reference carries real
   paragraph weight in each column, and thin text was making the layout look
   unfinished. Every claim stays inside what §4.1 of the design doc allows:
   spot-check and semantic-level review, never exhaustive or expert. ---- */

/* Shorter, and it names the movement the section actually describes. The
   previous heading read like a methodology-paper subhead. The breadcrumb that
   sat above it is gone — it navigated nowhere and only cost vertical space. */
export const CONTRIBUTION_TITLE = "FROM SOURCE TO ARCHIVE";
/* Two lines at the section's measure — the three-line version left a wedge
   of empty space down the right of the white half. */
export const CONTRIBUTION_INTRO =
  "We reconcile design-historical records out of scattered institutional catalogues and under-documented regional collections, then publish only what evidence, rights, and publication conditions permit.";

export const CONTRIBUTION_COLUMNS: { title: string; body: string }[] = [
  {
    title: "Reconciliation & Screening",
    body: "Candidate records are gathered across heterogeneous catalogues, de-duplicated, and normalised into one schema. Conflicting dates, attributions, and object types are reconciled against their sources rather than silently averaged.",
  },
  {
    title: "Spot-Check & Semantic Review",
    body: "Records are reviewed at a semantic level and spot-checked by sampling — not exhaustively, and not as expert art-historical adjudication. The method is stated plainly so its limits are legible to anyone citing the archive.",
  },
  {
    title: "Governed Publication",
    body: "Publication is gated on evidence, rights, and visual-availability conditions assessed separately. Records that do not clear that bar are held in the canonical set rather than dropped, so absence stays visible and recoverable.",
  },
];

/* FIVE, and written to be read rather than catalogued. The earlier set was
   six sentence-long descriptions — accurate, but they scanned as a table of
   contents. These are claims; the body under each does the explaining. */
export const CONTRIBUTION_ROWS: { title: string; body: string }[] = [
  {
    title: "Governed, not accumulated",
    body: "Records enter through stated conditions. What is published, held, or excluded is decided by rule, and the rule is written down.",
  },
  {
    title: "Every record names its source",
    body: "Catalogues that disagree on date, attribution or object type are reconciled against their own sources — never averaged into a false consensus.",
  },
  {
    title: "Absence is a finding",
    body: "What the archive leaves out stays recorded, countable, and labelled unresolved. A gap is evidence about the record, not a hole in the work.",
  },
  {
    title: "Three gates, never one",
    body: "Metadata, rights and evidence are assessed separately. Clearing one never implies clearing another — a described record is not a cleared image.",
  },
  {
    title: "Bounded by evidence",
    body: "Association is offered only where evidence qualifies it, and stays generic and non-directional. No causal or quantitative claim is generated.",
  },
];

/* The closing paragraph: carries reproducibility, and reads the field. */
export const FIELD_DETAIL =
  "Releases are identified, hashed and re-derivable, so any result can be returned to and checked against the state that produced it. The field below plots the same records by how far each still sits from publication — absence drawn, not omitted.";
  "Releases are identified, hashed and re-derivable, so a result can be returned to, cited, and checked against the state that produced it. The field plots records against the distance still separating them from publication: marks on the plane are published, stems are records held pending evidence, rights, or reconciliation, and their height is how far from publishable they remain. Absence is drawn, not omitted — the archive states what it cannot yet show as precisely as what it can."

export const CONTRIBUTION_ITALIC = "Verified where verifiable. Held where not.";
/* Deleted: the former ABSENCE/UNCERTAINTY statement was too long to hold in
   mind. Its substance now lives as a contribution point instead. Each chart
   stage carries its own short line. */
export const HISTO_TAGLINE = "Built through research, not aggregation.";
export const FIELD_TAGLINE = "More than a collection. A research foundation.";
export const CONTRIBUTION_ORG = "Modern Graphic Design Archive";
export const CONTRIBUTION_YEAR = "2026";

/* The FULL per-year distribution — every year 1800–2026, no binning.
   Binning was hiding the real shape: at 3-year resolution the apparent peak
   was 960, but the true per-year maximum is 572 in 1979. Showing every year
   is both more honest and visually denser. */
/* Per-year, two tiers, both from the SAME frozen release.
   Source: the canonical candidate payload named by database/FROZEN_V49.md
   (sha256 b16bb015…). Eligibility uses v49's own migration rule
   (database/data-migrations/v48-to-v49/extract.py): a surface is eligible
   only where trace.tier == "source_verified"; metadata_supported and absent
   tiers are held.

   Verified against database/data-migrations/v48-to-v49/expected-baseline.json:
   all 15,923 surfaces parsed, tiers 7,995 / 2,971 / 4,957 — an exact match to
   the frozen counts. 7,995 + 2,971 + 4,957 = 15,923; held = 7,928.

   Both figures already appear in the ledger above the chart, so the chart and
   the rest of the site now cite one release. [year, canonical, public] */
export const YEAR_TIERS: [number, number, number][] = [[1800,3,1],[1801,1,1],[1802,1,1],[1803,1,1],[1804,3,3],[1805,2,2],[1806,1,0],[1807,2,1],[1808,2,0],[1809,3,2],[1810,1,0],[1811,1,0],[1812,6,0],[1813,2,2],[1814,2,0],[1815,3,1],[1816,1,0],[1817,2,2],[1818,1,0],[1819,2,1],[1820,2,2],[1821,1,0],[1822,1,1],[1823,2,1],[1824,2,0],[1825,1,1],[1826,1,1],[1827,1,0],[1828,4,2],[1829,3,2],[1830,6,2],[1831,5,4],[1832,5,2],[1833,3,3],[1834,3,1],[1835,3,2],[1836,1,0],[1837,4,2],[1838,1,0],[1839,1,0],[1840,10,2],[1841,5,4],[1842,7,2],[1843,5,3],[1844,5,4],[1845,3,2],[1846,64,5],[1847,107,0],[1848,62,0],[1849,5,3],[1850,16,2],[1851,5,3],[1852,6,4],[1853,12,8],[1854,6,3],[1855,10,7],[1856,5,1],[1857,9,4],[1858,8,6],[1859,10,8],[1860,14,7],[1861,9,5],[1862,21,6],[1863,18,5],[1864,16,7],[1865,42,8],[1866,19,8],[1867,29,11],[1868,11,8],[1869,15,12],[1870,24,7],[1871,9,8],[1872,14,8],[1873,5,3],[1874,16,2],[1875,8,6],[1876,9,5],[1877,13,7],[1878,10,7],[1879,27,5],[1880,30,9],[1881,50,7],[1882,21,5],[1883,25,1],[1884,16,5],[1885,26,4],[1886,13,2],[1887,28,6],[1888,12,1],[1889,34,5],[1890,46,19],[1891,45,7],[1892,21,5],[1893,27,12],[1894,50,16],[1895,58,29],[1896,78,40],[1897,55,25],[1898,49,22],[1899,67,32],[1900,131,13],[1901,56,33],[1902,41,23],[1903,47,20],[1904,30,21],[1905,52,9],[1906,34,12],[1907,31,12],[1908,15,5],[1909,39,13],[1910,56,20],[1911,38,7],[1912,51,30],[1913,54,20],[1914,56,16],[1915,44,19],[1916,43,23],[1917,43,11],[1918,80,31],[1919,71,8],[1920,97,47],[1921,48,8],[1922,52,26],[1923,25,6],[1924,62,36],[1925,90,28],[1926,41,21],[1927,80,33],[1928,70,27],[1929,72,23],[1930,137,62],[1931,79,19],[1932,63,17],[1933,66,38],[1934,43,10],[1935,91,18],[1936,118,41],[1937,117,13],[1938,78,23],[1939,102,23],[1940,96,37],[1941,61,14],[1942,105,19],[1943,96,11],[1944,93,28],[1945,60,18],[1946,71,43],[1947,79,51],[1948,55,32],[1949,110,15],[1950,94,37],[1951,95,47],[1952,48,13],[1953,93,10],[1954,69,34],[1955,74,52],[1956,92,66],[1957,71,14],[1958,84,49],[1959,93,60],[1960,89,34],[1961,88,51],[1962,84,40],[1963,63,18],[1964,75,41],[1965,850,805],[1966,88,21],[1967,173,91],[1968,202,143],[1969,201,152],[1970,373,235],[1971,152,70],[1972,135,104],[1973,129,106],[1974,147,89],[1975,136,101],[1976,109,93],[1977,119,96],[1978,156,114],[1979,119,87],[1980,403,359],[1981,71,36],[1982,249,212],[1983,79,36],[1984,231,211],[1985,54,26],[1986,218,201],[1987,291,277],[1988,361,326],[1989,228,207],[1990,147,91],[1991,173,145],[1992,96,32],[1993,87,32],[1994,74,34],[1995,90,25],[1996,75,16],[1997,95,26],[1998,75,12],[1999,101,28],[2000,138,94],[2001,110,80],[2002,95,56],[2003,107,76],[2004,128,77],[2005,112,46],[2006,110,48],[2007,106,42],[2008,156,60],[2009,140,66],[2010,118,53],[2011,109,46],[2012,125,35],[2013,132,33],[2014,267,19],[2015,120,44],[2016,99,32],[2017,124,25],[2018,102,27],[2019,125,37],[2020,162,47],[2021,125,31],[2022,150,23],[2023,192,19],[2024,132,31],[2025,183,6],[2026,58,2]];

export const YEAR_TOTALS = { canonical: 15923, public: 7995, held: 7928 };
export const YEAR_SCALE_MAX = 860;
export const YEAR_BINS_LABEL = "What we hold, and what is public · by year, 1800–2026";
/* The field is a different chart and needs its own name — it was inheriting
   the histogram's, which described data the field does not show. */
export const FIELD_LABEL = "Distance from publication · every canonical record";

/* Annotations that point at something rather than label it. */
export const HISTO_NOTES = [
  "Faint is every canonical object · solid is public to read now",
  "The unfilled height is what stays held — 7,928 objects, v49 frozen release",
];
export const FIELD_NOTES = [
  "Each dot is a record that cleared every gate",
  "Each stem is a record still held — taller means further from publishable",
  "The surface is the reconciled archive they all sit in",
];

/* Real, bounded aggregate data for the two Contribution visualisations
   (HOMEPAGE_DESIGN_v1.md §4.2 / §4.3) — not invented for display. */

/* 2D entry chart: period-band distribution, sourced from
   data/source_coverage_period_breakdown_v2.csv (`surface_count` column). */
export const PERIOD_DISTRIBUTION: { period: string; count: number }[] = [
  { period: "Pre-1930", count: 2406 },
  { period: "1930–1970", count: 3684 },
  { period: "1970–2000", count: 3283 },
  { period: "2000–2026", count: 3559 },
];

/* 3D scene: capture-batch stage structure, sourced from
   docs/capture/CAPTURE_RUN_MANIFEST_v1.md ("Stage Counts"; 44 batches total,
   deliberately a different dimension than the period distribution above). */
export const CAPTURE_BATCH_STAGES: { stage: string; count: number }[] = [
  { stage: "Public surface rebuild input", count: 18 },
  { stage: "Item image capture", count: 13 },
  { stage: "Capture records, unclassified", count: 9 },
  { stage: "Source profile / context", count: 2 },
  { stage: "Empty or pending", count: 2 },
];
export const CAPTURE_BATCH_TOTAL = 44;

/* Identity's scroll-mined phrases (HOMEPAGE_DESIGN_v1.md §3). Each `text` is a
   verbatim, exact substring of IDENTITY_P1, in left-to-right order — the
   recombined line introduces no new copy. */
export const IDENTITY_MARKS: { id: string; text: string; mark: "underline" | "circle" }[] = [
  { id: "verified", text: "verified records", mark: "underline" },
  { id: "provenance", text: "explicit provenance", mark: "circle" },
  { id: "evidence", text: "evidence-bounded computational research", mark: "underline" },
];
export const IDENTITY_ASSEMBLED =
  "Verified records. Explicit provenance. Evidence-bounded computational research.";

/* 03 · Enter the Archive. Three ways in, deliberately NOT numbered: Index,
   Search and TRACE are peers, not steps — an ordinal would imply a sequence
   the product does not have. One verb each, matching the section's own
   "Browse. Find. Explore." one-to-one. */
export const ENTER_TITLE = "Start with what you know.";
export const ENTRIES: {
  name: string;
  verb: string;
  when: string;
  line: string;
  href: string;
  note?: string;
}[] = [
  {
    name: "Index",
    verb: "Browse.",
    when: "When you know a period, region, or theme.",
    line: "Move through the public archive chronologically and through governed categories.",
    href: "/directory",
  },
  {
    name: "Search",
    verb: "Find.",
    when: "When you know a title, designer, place, or ID.",
    line: "Search the public archive directly from anywhere in MGDA.",
    href: "/search",
  },
  {
    name: "TRACE",
    verb: "Explore.",
    when: "When you have a research question rather than a single record.",
    line: "Use Context Canvas, Spacetime, and Exploration to examine governed research representations.",
    href: "/trace",
    note: "Desktop only",
  },
];


/* Read off database/FROZEN_V49.md rather than typed by hand: the anchor is
   `v49-data-api-closure-20260821`, and the object/eligible counts on this page
   come from the same manifest. If the release moves, these move with it. */
export const RELEASE = {
  version: "v49",
  anchor: "v49-data-api-closure-20260821",
  date: "21 August 2026",
  status: "Public research release",
  objects: 15923,
  eligible: 7995,
  held: 7928,
};

export const STATUS_TITLE = "A stable release, not a finished history.";
export const STATUS_INTRO =
  "MGDA publishes versioned research records and governed research interfaces while keeping uncertainty, missingness and unresolved evidence visible.";

export const STATUS_STABLE: { term: string; line: string }[] = [
  { term: "Public records and identifiers", line: "Bound to a versioned release." },
  { term: "Source and citation provenance", line: "Inspectable independently of MGDA." },
  { term: "Governed research interfaces", line: "Index, Search and TRACE read governed data; they do not generate archive facts at request time." },
];
export const STATUS_OPEN: { term: string; line: string }[] = [
  { term: "Historical coverage", line: "Incomplete. This is not a complete history of modern graphic design." },
  { term: "Unresolved research questions", line: "Held separately from validated structure, never folded into it." },
  { term: "Visual availability and rights", line: "A public record does not imply identical visual access for every object." },
  { term: "Future corrections and expansion", line: "New evidence may extend or reclassify records without rewriting cited releases." },
];
export const STATUS_EXITS: { label: string; href: string }[] = [
  { label: "How the archive is built", href: "/about" },
  { label: "Sources, rights and provenance", href: "/source" },
];

export const RESEARCH_STATUS =
  "MGDA is an active research infrastructure. Public inclusion, visual availability, and computational association are governed separately; absence, uncertainty, and unresolved evidence are retained rather than automatically inferred.";
