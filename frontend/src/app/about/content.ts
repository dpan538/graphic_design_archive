/* About page content. Data only — grounded in repository fact.
   Section order (owner-fixed): Purpose · Methodology · Visual rationale ·
   Scale · Contact & citation · Claim boundaries & rights.
   No release IDs, database versions, hashes, or build/deploy status on the
   public page. */

export const REPO_URL = "https://github.com/dpan538/graphic_design_archive";
export const SITE_URL = "https://mgdarchive.com";
export const PORTFOLIO_URL = "https://daipan.art";

/* ---- Masthead ---------------------------------------------------- */

export const openingStatement =
  "A verified, source-returnable archive for modern graphic design history.";

export const openingLead =
  "Modern Graphic Design Archive gathers graphic design from more than a hundred institutions and open collections, then cleans, classifies, and researches it into an archive you can read, locate, cite, and check against its sources. Nearly 16,000 objects are catalogued; 7,995 are public to read now.";

export const openingMeta =
  "In development since 2024 · 44 capture batches · 100+ sources · text and citation, no assumed imagery";

/* ---- 1 · Purpose ------------------------------------------------- */

export const purposeLead =
  "Verified means every public statement can be traced back to a source record and a review decision. Extensible means the archive grows in versioned steps — each research round adds to the record rather than overwriting it.";

export const audiences: { tone: string; title: string; body: string }[] = [
  {
    tone: "blue",
    title: "Design researchers",
    body: "Source-returnable records with explicit provenance, rights posture, and uncertainty, so a claim can be checked against the material it came from.",
  },
  {
    tone: "red",
    title: "Learners and educators",
    body: "A readable way into modern graphic design history that keeps the difference between evidence, description, and interpretation visible on the page.",
  },
  {
    tone: "green",
    title: "AI and agent research tools",
    body: "A stable, versioned, machine-readable surface with deterministic search and fail-closed evidence rules, suitable for automated reading and citation.",
  },
];

/* ---- 2 · Methodology ------------------------------------------- */

export const methodProse: string[] = [
  "The unit of work is a source-grounded record tied to a stable locator. Gathering is not publishing: a captured record first enters a candidate pool, and only passes review gates for source, rights, classification, completeness, and readable text before it becomes something you can read here.",
  "Coverage is weighted against imbalance rather than only counted, so the archive does not look finished merely because some regions and periods are easier to gather. No historical influence is ever inferred from proximity, a shared source, visual resemblance, or a shared period.",
];

export const pipelineStages: string[] = [
  "Source registry",
  "Capture batch",
  "Candidate pool",
  "Review gates",
  "Published record",
];

export const evidenceProtocol: { term: string; def: string }[] = [
  {
    term: "Evidence",
    def: "A statement directly recoverable from a source record, stable identifier, rights field, transcript, or preserved capture.",
  },
  {
    term: "Description",
    def: "A faithful normalization or paraphrase of source evidence. It may improve readability but cannot add new historical facts.",
  },
  {
    term: "Interpretation",
    def: "A claim about significance, influence, reception, or movement membership. It needs a direct citation or an explicit project-inference mark.",
  },
  {
    term: "Uncertainty",
    def: "A kept warning about date, authorship, place, script, rights status, or classification. Uncertainty is shown, not hidden.",
  },
];

export const designResearchNote =
  "The interface is treated as part of the method. Search finds individual objects by relevance; the Index browses the archive by classification and year; TRACE is a desktop research environment for validated associations and open inquiry. Because the archive holds no image-display rights, reading is built from text, citation, and internally drawn diagrams — never assumed object imagery.";

/* ---- 3 · Visual design rationale ---------------------------- */

export const rationaleLead =
  "The interface is designed the way a printed reference catalogue is set: colour used as a coding system, a heavy line holding the structure, and one clear idea per section. Three references were combined into a single language — not copied.";

export const visualReferences: {
  tone: "blue" | "red" | "yellow" | "green" | "teal" | "coral";
  title: string;
  meta: string;
  body: string;
}[] = [
  {
    tone: "red",
    title: "Alex Steinweiss",
    meta: "Invented the illustrated album cover · Columbia Records · 1940",
    body: "One concept per cover, a limited but luminous palette, expressive display lettering, and a single graphic device repeated with rhythm. Each section here is treated as a cover: a single idea, announced.",
  },
  {
    tone: "blue",
    title: "New York editorial illustration",
    meta: "New Yorker / New York Times idiom",
    body: "Flat, bright colour held by a confident black line, ordered density, warmth, and wit — with no gradient, shadow, or fake depth.",
  },
  {
    tone: "yellow",
    title: "Spot-colour printing",
    meta: "A few bright inks plus a black line block",
    body: "Colour is a coding system — each section owns one — and is also worn as a full block. It is never the only carrier of meaning; a label, a position, and the black line carry it too.",
  },
  {
    tone: "green",
    title: "A serif counterpoint",
    meta: "Baskervville, kept for the opening voice",
    body: "A quiet transitional serif is held for the opening statement and for emphasis — a counterweight to the bright colour and the heavy display type.",
  },
];

export const typeSystem: { role: string; face: string }[] = [
  { role: "Opening voice", face: "Baskervville — statement and emphasis" },
  { role: "Section titles", face: "LINE Seed JP ExtraBold" },
  { role: "Labels", face: "LINE Seed JP Bold" },
  { role: "Body", face: "Instrument Sans — 18px floor, 19px reading" },
  { role: "Figures", face: "Inter — tabular, in tables" },
];

/* ---- 4 · Scale (public-facing; no engineering internals) ---- */

export const scaleLead =
  "The project gathers distributed traces of graphic design — posters, print, publications, identities, ephemera — from more than a hundred institutional and open sources. Successive rounds of cleaning, classification, rights review, and research reduce a large raw pool to a verified core. What is public now is a fraction of what has been gathered; the rest is held until its evidence is complete.";

export const scaleFigures: { tone: string; value: string; label: string }[] = [
  { tone: "blue", value: "2024", label: "In development since" },
  { tone: "red", value: "44", label: "Capture batches" },
  { tone: "green", value: "100+", label: "Sources consulted" },
  { tone: "teal", value: "15,923", label: "Objects catalogued" },
  { tone: "yellow", value: "7,995", label: "Public to read now" },
  { tone: "coral", value: "7,928", label: "Held for continued review" },
  { tone: "blue", value: "1800s–2020s", label: "Span of the material" },
  { tone: "red", value: "90", label: "Object types recorded" },
];

export const scaleNote =
  "Coverage is deliberately uneven and weighted against imbalance: several world regions are still barely represented, and the archive says so on the page rather than hiding the gap.";

/* ---- 5 · Contact & citation ------------------------------- */

export const contact: {
  tone: string;
  label: string;
  links: { text: string; href?: string }[];
}[] = [
  {
    tone: "blue",
    label: "Project lead",
    links: [{ text: "Dai Pan (潘岱), Brisbane" }],
  },
  {
    tone: "red",
    label: "Email",
    links: [
      { text: "dpan53853@gmail.com", href: "mailto:dpan53853@gmail.com" },
      { text: "jarl555@qq.com", href: "mailto:jarl555@qq.com" },
    ],
  },
  {
    tone: "teal",
    label: "Portfolio",
    links: [{ text: "daipan.art", href: PORTFOLIO_URL }],
  },
  {
    tone: "coral",
    label: "Repository",
    links: [
      { text: "github.com/dpan538/graphic_design_archive", href: REPO_URL },
    ],
  },
];

export function buildCitations(accessDate: Date) {
  const longUS = accessDate.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const dayMonthYear = accessDate.toLocaleDateString("en-GB", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const mlaDate = accessDate.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  return [
    {
      tone: "blue",
      style: "APA",
      text: `Modern Graphic Design Archive. (2026). Modern Graphic Design Archive [Research archive]. ${SITE_URL}`,
    },
    {
      tone: "red",
      style: "MLA",
      text: `Modern Graphic Design Archive. 2026, mgdarchive.com. Accessed ${mlaDate}.`,
    },
    {
      tone: "green",
      style: "Chicago",
      text: `Modern Graphic Design Archive. 2026. Modern Graphic Design Archive. Accessed ${longUS}. ${SITE_URL}.`,
    },
    {
      tone: "teal",
      style: "Harvard",
      text: `Modern Graphic Design Archive (2026) Modern Graphic Design Archive. Available at: ${SITE_URL} (Accessed: ${dayMonthYear}).`,
    },
  ] as const;
}

export const citeHint =
  "For an individual object, cite the holding institution or source record first, then this project as the index layer. Access dates are filled in for today; adjust them to the date you consulted the archive.";

/* ---- 6 · Claim boundaries & rights ------------------------- */

export const claimBoundaries: {
  area: string;
  supports: string;
  notClaim: string;
}[] = [
  {
    area: "Historical relations",
    supports:
      "21 evidence-qualified pairwise generic associations, each tied to the evidence that qualifies it.",
    notClaim:
      "No causal, directional, hierarchical, chronological, identity, equivalence, or quantified relation. Zero typed historical relations are asserted.",
  },
  {
    area: "Inference",
    supports: "Normalization and classification of what sources actually record.",
    notClaim:
      "No inferred influence, no country guessed from a free-text place label, no inferred movement membership.",
  },
  {
    area: "Completeness",
    supports: "A bounded, source-verified core of the field.",
    notClaim:
      "Not global completeness, and not even uniform source density. Coverage is uneven by region and period; several regions are barely represented, and the exclusion universe is indeterminate.",
  },
  {
    area: "Visual rights",
    supports: "Text, metadata, citation, and internally drawn diagrams.",
    notClaim:
      "No right to display archive-object images. The archive holds zero positive visual-rights records, and no object image is assumed anywhere in the product.",
  },
  {
    area: "TRACE evidence",
    supports:
      "An evidence-bounded exploration of validated associations, kept separate from unresolved inquiry.",
    notClaim:
      "Not research closure. Open Inquiry lists 11 scoped, unresolved hypotheses that are explicitly not validated and generate no pairwise edges.",
  },
  {
    area: "System suggestions",
    supports:
      "Optional orientation only, shown under the label “System suggests” and assisted by DeepSeek V4 Flash.",
    notClaim:
      "It does not determine search ranking or results, archival metadata, public eligibility, TRACE associations, evidence status, Open Inquiry status, or any historical conclusion. Only a bounded public summary is sent, and a guidance failure never changes a result.",
  },
];

export const rightsProse =
  "Modern Graphic Design Archive is an index and research interface. Copyright, database rights, moral rights, trademarks, personality rights, cultural protocols, and access terms may remain with original creators, publishers, institutions, estates, communities, or source platforms. Project-authored text, data normalization, and this interface design are research outputs, and no blanket reuse licence is granted. Individual object images and scans remain governed by their holding source.";

export const footerNote = "Interface in progress · not yet public";
