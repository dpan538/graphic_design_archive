import "server-only";

import {
  normalizePublicSearchRequest,
  pagePublicSearchResults,
  rankPublicSearchDocuments,
  SearchInputError,
  type PublicSearchFilters,
  type PublicSearchRequest,
  type RankedPublicSearchDocument,
} from "./core";
import { getPublicSearchIndex, type PublicSearchFacetValue } from "./index.server";
import { getReaderEligibilityIndex, type ReaderEligibility } from "@/features/reader-eligibility/index.server";

export type PublicSearchServiceInput = {
  query?: string;
  filters?: PublicSearchFilters;
  first?: number;
  after?: string;
};

type AggregateValue = { value: string; count: number };

function assertDictionaryValue(value: string | undefined, values: readonly PublicSearchFacetValue[], field: string): void {
  if (value && !values.some((item) => item.value === value)) {
    throw new SearchInputError("INVALID_ARGUMENT", `${field} is not a public Search dictionary value`);
  }
}

function topValues(ranked: readonly RankedPublicSearchDocument[], getter: (item: RankedPublicSearchDocument) => readonly string[]): AggregateValue[] {
  const counts = new Map<string, number>();
  for (const item of ranked) for (const value of getter(item)) counts.set(value, (counts.get(value) ?? 0) + 1);
  return [...counts].map(([value, count]) => ({ value, count }))
    .sort((left, right) => right.count - left.count || (left.value < right.value ? -1 : left.value > right.value ? 1 : 0))
    .slice(0, 5);
}

function topDecades(ranked: readonly RankedPublicSearchDocument[]): AggregateValue[] {
  const counts = new Map<number, number>();
  for (const item of ranked) {
    const decade = Math.floor(item.document.yearStart / 10) * 10;
    counts.set(decade, (counts.get(decade) ?? 0) + 1);
  }
  return [...counts].map(([decade, count]) => ({ value: `${decade}s`, count }))
    .sort((left, right) => right.count - left.count || (left.value < right.value ? -1 : 1))
    .slice(0, 5);
}

export function validatePublicSearchRequest(input: PublicSearchServiceInput): PublicSearchRequest {
  const index = getPublicSearchIndex();
  const request = normalizePublicSearchRequest({ query: input.query, filters: input.filters });
  assertDictionaryValue(request.filters.objectType, index.facets.object_types, "objectType");
  assertDictionaryValue(request.filters.theme, index.facets.themes, "theme");
  assertDictionaryValue(request.filters.movement, index.facets.movements, "movement");
  return request;
}

/* The reader-facing rule (FRONTEND_DESIGN_DECISION §3b, owner 2026-09-03 and
   2026-09-06): normal Search — a query, filters, or both — answers from the
   READER-FACING objects only, the same 5,423 the Index files. A record-only
   entry (a public record whose title is its source identifier) is returned
   only when the reader typed that identifier, or the stable ID, in full: an
   exact record lookup, labelled as such. Ranking runs over every public
   document so an exact lookup can find it; the join happens after. */
const EXACT_LOOKUP_MATCH_TYPES: ReadonlySet<string> = new Set(["identifier", "exact_title", "normalized_title"]);
export const RECORD_ONLY_LABEL = "Record-only archive entry";

export function searchPublicObjects(input: PublicSearchServiceInput) {
  const index = getPublicSearchIndex();
  const request = validatePublicSearchRequest(input);
  const eligibility = getReaderEligibilityIndex();
  const eligibilityOf = (stableId: string): ReaderEligibility => eligibility.byId.get(stableId)?.eligibility ?? "RECORD_ONLY";
  const ranked = rankPublicSearchDocuments(index.documents, request).filter(
    (item) => eligibilityOf(item.document.stableId) === "INDEX_ELIGIBLE" || EXACT_LOOKUP_MATCH_TYPES.has(item.explanation.matchType),
  );
  const page = pagePublicSearchResults({
    ranked,
    request,
    first: input.first,
    after: input.after,
    releaseId: index.manifest.release_id,
    manifestSha256: index.manifest.release_manifest_sha256,
    indexSha256: index.manifest.index_sha256,
  });
  return {
    schemaVersion: "gda-public-object-search-response/v1",
    release: {
      id: index.manifest.release_id,
      manifestSha256: index.manifest.release_manifest_sha256,
      searchIndexSha256: index.manifest.index_sha256,
      algorithmVersion: index.manifest.search_algorithm_version,
    },
    query: {
      text: request.query,
      filters: request.filters,
      order: "RELEVANCE" as const,
    },
    stateHash: page.stateHash,
    results: page.nodes.map(({ document, explanation }) => ({
      objectId: document.stableId,
      readerEligibility: eligibilityOf(document.stableId),
      title: document.title,
      creditedLabel: document.creditedLabel,
      displayDate: document.displayDate,
      year: { start: document.yearStart, end: document.yearEnd },
      place: document.place,
      objectType: document.objectType,
      themes: document.themes,
      movements: document.movements,
      sourceLabel: document.sourceLabel,
      deliveryState: document.deliveryState,
      objectPageRoute: `/surfaces/${encodeURIComponent(document.stableId)}`,
      matchExplanation: eligibilityOf(document.stableId) === "RECORD_ONLY" ? `${explanation.label} · ${RECORD_ONLY_LABEL}` : explanation.label,
      audit: {
        score: explanation.score,
        matchType: explanation.matchType,
        matchedFields: explanation.matchedFields,
        signals: explanation.signals,
      },
    })),
    pageInfo: page.pageInfo,
    aggregateSummary: {
      exactResultCount: ranked.length,
      topDecades: topDecades(ranked),
      topObjectTypes: topValues(ranked, (item) => [item.document.objectType]),
      topThemes: topValues(ranked, (item) => item.document.themes),
      topMovements: topValues(ranked, (item) => item.document.movements),
    },
  };
}

export function publicSearchFacets() {
  const index = getPublicSearchIndex();
  return {
    schemaVersion: "gda-public-object-search-facets-response/v1",
    release: {
      id: index.manifest.release_id,
      manifestSha256: index.manifest.release_manifest_sha256,
      searchIndexSha256: index.manifest.index_sha256,
    },
    documentCount: index.manifest.document_count,
    /* what normal Search answers from: the reader-facing objects, as the Index */
    readerFacingCount: getReaderEligibilityIndex().manifest.counts.index_eligible,
    year: index.facets.year,
    objectTypes: index.facets.object_types,
    themes: index.facets.themes,
    movements: index.facets.movements,
    starterQueries: index.facets.starter_queries,
  };
}
