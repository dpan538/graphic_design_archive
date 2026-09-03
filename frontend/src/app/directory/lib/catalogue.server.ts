import "server-only";

import { getPublicSearchIndex } from "@/features/search-v2/index.server";
import { getReaderEligibilityIndex } from "@/features/reader-eligibility/index.server";
import type { CataloguePayload, CatalogueRow, VisualAccess } from "./catalogue";

const visualOf = (delivery: string): VisualAccess =>
  delivery === "REMOTE_IMAGE" ? "remote" : delivery === "SOURCE_VIEWER" ? "source" : "citation";

/* The catalogue payload, built once per process from the sealed Search v2
   artifact, limited to the READER-FACING objects the reader-eligibility
   projection admits (record-only entries keep their URL and are reachable
   by ID, but are not browsed). Places and sources are dictionaries; themes
   keep the facet order (by count). Records keep the artifact's document
   order. */

let cached: { payload: CataloguePayload; etag: string } | null = null;

export function getCataloguePayload(): { payload: CataloguePayload; etag: string } {
  if (cached) return cached;
  const index = getPublicSearchIndex();
  const eligibility = getReaderEligibilityIndex();
  const documents = index.documents.filter((d) => eligibility.byId.get(d.stableId)?.eligibility === "INDEX_ELIGIBLE");
  if (documents.length !== eligibility.manifest.counts.index_eligible) throw new Error("catalogue count disagrees with the reader-eligibility manifest");
  const themes = index.facets.themes.map((t) => t.value);
  const themeIdx = new Map(themes.map((t, i) => [t, i] as const));
  const places = Array.from(new Set(documents.map((d) => d.place))).sort((a, b) => a.localeCompare(b));
  const placeIdx = new Map(places.map((p, i) => [p, i] as const));
  const sources = Array.from(new Set(documents.map((d) => d.sourceLabel))).sort((a, b) => a.localeCompare(b));
  const sourceIdx = new Map(sources.map((s, i) => [s, i] as const));
  const rows: CatalogueRow[] = documents.map((d) => [
    d.stableId,
    d.yearStart,
    d.yearEnd,
    d.title,
    d.creditedLabel,
    placeIdx.get(d.place) ?? 0,
    d.objectType,
    d.themes.map((t) => themeIdx.get(t)).filter((i): i is number => typeof i === "number"),
    d.movements[0] ?? null,
    sourceIdx.get(d.sourceLabel) ?? 0,
    d.displayDate,
    visualOf(d.deliveryState),
  ]);
  const payload: CataloguePayload = {
    format: "gda-index-catalogue/v1",
    releaseId: index.manifest.release_id,
    count: documents.length,
    publicCount: index.manifest.document_count,
    recordOnlyCount: eligibility.manifest.counts.record_only,
    yearMin: index.facets.year.min,
    yearMax: index.facets.year.max,
    themes,
    places,
    sources,
    rows,
  };
  cached = { payload, etag: eligibility.manifest.eligibility_sha256.slice(0, 32) };
  return cached;
}
