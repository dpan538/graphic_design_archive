import type { PublicSearchDocument } from "@/features/search-v2/core";
import type { SourceViewer } from "@/features/source-viewer/index.server";
import type { VisualRegistryEntry } from "@/features/visual-registry/index.server";
import type { ObjectRecord, VisualBlock } from "./fixture";

/* The object record, from the sealed v49 public projection — the same
   document the Search API serves (FRONTEND_DESIGN_DECISION.md §3). Only
   what the projection publishes is shown: title, credited label, date,
   place, object type, themes, movements, source collection and delivery
   state. Medium and description are not part of the public projection and
   are omitted (never "Unknown"); the source record URL comes from the
   source-viewer projection; an image comes only from the visual registry;
   every public document is a verified source in the current sealed
   release. */

export const RELEASE_LABEL = "v49 — current public release (sealed)";

export function visualBlockFor(d: PublicSearchDocument, viewer: SourceViewer, registry: VisualRegistryEntry | null): VisualBlock {
  if (registry) {
    return { mode: "displayable", sourceUrl: registry.sourceUrl || viewer.sourceUrl, sourceLabel: d.sourceLabel, imageUrl: registry.imageUrl, attribution: registry.attribution, licence: registry.licence };
  }
  const mode = d.deliveryState === "LINK_ONLY" ? "link" : d.deliveryState === "CITATION_ONLY" || d.deliveryState === "BLOCKED" ? "citation" : "source-viewer";
  return { mode, sourceUrl: viewer.sourceUrl, sourceLabel: d.sourceLabel };
}

export function recordFromDocument(d: PublicSearchDocument, viewer: SourceViewer, registry: VisualRegistryEntry | null): ObjectRecord {
  return {
    surfaceId: d.stableId,
    title: d.title,
    creditedLabels: d.creditedLabel ? [d.creditedLabel] : [],
    displayDate: d.displayDate,
    year: d.yearStart,
    yearEnd: d.yearEnd,
    placeLabel: d.place,
    mediumLabel: "",
    typeLabel: d.objectType,
    themes: [...d.themes],
    movements: [...d.movements],
    sourceLabel: d.sourceLabel,
    publicationLayer: "active",
    deliveryState: d.deliveryState,
    visual: visualBlockFor(d, viewer, registry),
    citation: null,
    sourceRecord: {
      institution: d.sourceLabel,
      recordTitle: d.title,
      recordHref: viewer.sourceUrl ?? "",
      accessedText: viewer.accessDate ? `Captured ${viewer.accessDate} · frozen snapshot at acquisition` : "2026 capture batches · frozen snapshot at acquisition",
    },
    provenance: {
      releaseLabel: RELEASE_LABEL,
      recordStatus: "Public record",
      sourceVerification: "Verified source",
      lastVerified: "2026, with the v49 freeze",
    },
    description: null,
  };
}
