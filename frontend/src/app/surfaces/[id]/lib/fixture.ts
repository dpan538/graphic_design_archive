/* Object Page — the record type, and one sample record.
   Live pages build their record from the sealed projection (lib/fromDocument.ts);
   the sample below is kept for the type and for design review only. Shaped to
   the real read API `SurfaceDetail` DTO:
   surfaceId · title · creditedLabels[] · displayDate · year · placeLabel ·
   mediumLabel · typeLabel · sourceLabel · publicationLayer · deliveryState ·
   citation{label,href}|null · folderIds[] · description|null.
   No taxonomy is invented; every field maps to a real DTO field. */

export type DeliveryState =
  | "REMOTE_IMAGE"
  | "SOURCE_VIEWER"
  | "LINK_ONLY"
  | "CITATION_ONLY"
  | "BLOCKED";

/* the visual layer's mode (FRONTEND_DESIGN_DECISION.md §3d):
   displayable — the image is rendered in MGDA from the visual registry, with
     attribution and the original source;
   source-viewer — no image box; a clear "View at source" action;
   link / citation — a source record page or a citation basis only.
   Record-only pages render no visual layer at all. */
export type VisualMode = "displayable" | "source-viewer" | "link" | "citation";
export type VisualBlock = {
  mode: VisualMode;
  sourceUrl: string | null;
  sourceLabel: string;
  imageUrl?: string;
  attribution?: string;
  licence?: string;
};

export type ObjectRecord = {
  surfaceId: string;
  title: string;
  creditedLabels: string[];
  displayDate: string;
  year: number | null;
  yearEnd: number | null;
  placeLabel: string;
  mediumLabel: string;
  typeLabel: string;
  themes: string[];
  movements: string[];
  sourceLabel: string;
  publicationLayer: "active" | "review" | "auxiliary";
  deliveryState: DeliveryState;
  visual: VisualBlock;
  citation: { label: string; href: string } | null;
  sourceRecord: {
    institution: string;
    recordTitle: string;
    recordHref: string;
    accessedText: string;
  };
  provenance: {
    releaseLabel: string;
    recordStatus: string;
    sourceVerification: string;
    lastVerified: string;
  };
  description: string | null;
};

export const DESCRIPTION_LONG =
  "A single-colour lithographic poster produced for a municipal cultural programme. The composition sets a bold sans-serif headline against a wide field of flat colour, with a secondary block of programme text aligned to a strict left margin. The source record notes offset lithography on wove paper and a printed run tied to the exhibition dates. The credited studio is recorded on the sheet; no further attribution is given. This description is transcribed and normalized from the holding institution's catalogue entry and is not an interpretive or stylistic account written by the archive.";

export const DESCRIPTION_SHORT =
  "Single-colour lithographic exhibition poster; bold sans-serif headline over a flat colour field, with left-aligned programme text. Description normalized from the holding institution's catalogue entry.";

/* Exploration-only: a deliberately long transcription, to show the content-fit
   layout resolve the description to its widest (4-column) setting. */
export const DESCRIPTION_XLONG =
  DESCRIPTION_LONG +
  " The holding institution's entry further records that the sheet was one of a small series printed for the same programme, that the paper stock is consistent across the run, and that the trimmed dimensions fall within the standard civic-poster format used by the city's print office in this period. A later cataloguer's note, quoted verbatim in the source record, observes that the headline setting matches a typeface the studio used on other municipal commissions; the archive reproduces that observation without endorsing it as an attribution. No printer's imprint, edition statement, or commissioning-body mark is transcribed in the source record, and none has been added here.";

export const fixture: ObjectRecord = {
  surfaceId: "MGDA-004921",
  title: "Exhibition poster for a municipal cultural programme",
  creditedLabels: ["Atelier / studio recorded on the sheet"],
  displayDate: "1968",
  year: 1968,
  yearEnd: null,
  placeLabel: "Zürich",
  mediumLabel: "Offset lithograph on wove paper",
  typeLabel: "Poster",
  themes: ["Typography", "Public information"],
  movements: [], // ~1.4% of records carry a movement; this one does not
  sourceLabel: "Example Museum of Design — collection API",
  publicationLayer: "active",
  deliveryState: "REMOTE_IMAGE",
  visual: { mode: "source-viewer", sourceUrl: "https://example.org/record", sourceLabel: "Holding institution" },
  citation: {
    label: "Example Museum of Design, object 1968-0421.",
    href: "https://example.org/collection/1968-0421",
  },
  sourceRecord: {
    institution: "Example Museum of Design",
    recordTitle: "Plakat für ein städtisches Kulturprogramm",
    recordHref: "https://example.org/collection/1968-0421",
    accessedText: "Acquired via the collection API, 2026 capture batches",
  },
  provenance: {
    releaseLabel: "v49 — current public release (sealed)",
    recordStatus: "Public record · publication layer: active",
    sourceVerification: "Source-verified (trace.tier = source_verified)",
    lastVerified: "2026, with the v49 freeze",
  },
  description: DESCRIPTION_LONG,
};

/* Field label vocabulary — display labels only, values come from the record. */
export const FIELD_LABELS = {
  credited: "Designer / studio",
  displayDate: "Date",
  year: "Year",
  place: "Place",
  medium: "Medium",
  type: "Object type",
  theme: "Theme",
  movement: "Movement",
  stableId: "Stable ID",
  source: "Source",
  delivery: "Delivery state",
  layer: "Publication layer",
} as const;

/* Delivery-state wording, public: a state is a fact about the source record,
   never a viewable asset or a rights grant (the release holds zero positive
   visual-rights records). Provisional wording pending the owner's decision
   (design plan §9H). */
export const DELIVERY_LABEL: Record<DeliveryState, string> = {
  REMOTE_IMAGE: "Image held at the source — not displayed here",
  SOURCE_VIEWER: "Viewable at the holding institution — not displayed here",
  LINK_ONLY: "Source record by link only — no visual",
  CITATION_ONLY: "Citation only — no visual delivery",
  BLOCKED: "No visual delivery",
};

export const DELIVERY_HAS_IMAGE = (d: DeliveryState) => d === "REMOTE_IMAGE";
