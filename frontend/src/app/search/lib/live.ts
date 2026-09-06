"use client";

/* Search — the live public search API behind the window (release pass,
   2026-09-06). The window's state model stays; the fixture is replaced by
   `/api/search/v1` (results, exact count, cursor paging), its facets
   endpoint (the dictionaries and the year range), and the shared System
   suggests endpoint (a v2 request naming the query and filters, with the
   count the window shows). A page index becomes a walk of cursors, cached
   per query. Every answer is checked against the request it was made for;
   a late answer for an earlier state is dropped. */

import { useEffect, useMemo, useRef, useState } from "react";
import { MOVEMENTS, OBJECT_TYPES, THEMES, YEAR_MAX, YEAR_MIN, type SearchRecord } from "./fixture";
import { PAGE_SIZE, type MatchReason, type SearchResult, type SearchState } from "./query";

export type SearchFacets = {
  objectTypes: string[];
  themes: string[];
  movements: string[];
  yearMin: number;
  yearMax: number;
  starters: string[];
  live: boolean;
};

const FALLBACK_FACETS: SearchFacets = { objectTypes: [...OBJECT_TYPES], themes: [...THEMES], movements: [...MOVEMENTS], yearMin: YEAR_MIN, yearMax: YEAR_MAX, starters: [], live: false };

type ApiResult = {
  objectId: string;
  title: string;
  creditedLabel: string | null;
  displayDate: string;
  year: { start: number; end: number };
  place: string;
  objectType: string;
  themes: string[];
  movements: string[];
  deliveryState: SearchRecord["deliveryState"];
  matchExplanation: string;
  audit?: { matchType?: string };
};
type ApiResponse = {
  query: { text: string; filters: { yearFrom?: number; yearTo?: number; objectType?: string; theme?: string; movement?: string } };
  stateHash: string;
  results: ApiResult[];
  pageInfo: { hasNextPage: boolean; nextCursor?: string | null; totalExact: number };
};

export type LiveSearch = {
  loading: boolean;
  error: string | null;
  total: number;
  results: SearchResult[];
  page: SearchResult[];
  pageCount: number;
  pageIndex: number;
  stateHash: string | null;
  filters: ApiResponse["query"]["filters"] | null;
  query: string;
};

function reasonOf(item: ApiResult): MatchReason {
  const type = (item.audit?.matchType ?? item.matchExplanation ?? "").toLowerCase();
  if (/exact/.test(type) && /title/.test(type)) return "Exact title";
  if (/fuzzy|spelling|variation/.test(type)) return "Matched spelling variation";
  if (/related|vocabulary|associat/.test(type)) return "Matched a related term";
  if (/movement/.test(type)) return "Matched movement";
  if (/year/.test(type)) return "Matched title and year";
  return "Matched all query terms";
}

function toResult(item: ApiResult): SearchResult {
  return {
    record: {
      id: item.objectId,
      title: item.title,
      credited: item.creditedLabel ?? null,
      displayDate: item.displayDate,
      year: item.year.start,
      place: item.place,
      objectType: item.objectType,
      themes: item.themes,
      movements: item.movements,
      deliveryState: item.deliveryState,
    },
    reason: reasonOf(item),
  };
}

export function apiFilters(state: SearchState): ApiResponse["query"]["filters"] {
  const filters: ApiResponse["query"]["filters"] = {};
  if (state.yearFrom) filters.yearFrom = state.yearFrom;
  if (state.yearTo) filters.yearTo = state.yearTo;
  if (state.objectType) filters.objectType = state.objectType;
  if (state.theme) filters.theme = state.theme;
  if (state.movement) filters.movement = state.movement;
  return filters;
}

function queryKey(state: SearchState): string {
  return JSON.stringify({ q: state.q, filters: apiFilters(state) });
}

async function fetchPage(state: SearchState, cursor: string | null, signal: AbortSignal): Promise<ApiResponse> {
  const params = new URLSearchParams();
  if (state.q) params.set("q", state.q);
  for (const [key, value] of Object.entries(apiFilters(state))) if (value !== undefined) params.set(key, String(value));
  params.set("first", String(PAGE_SIZE));
  if (cursor) params.set("after", cursor);
  const response = await fetch(`/api/search/v1?${params.toString()}`, { headers: { Accept: "application/json" }, cache: "no-store", signal });
  const body = await response.json().catch(() => null) as (ApiResponse & { detail?: string }) | null;
  if (!response.ok || !body) throw new Error(body?.detail ?? "The public Search service is temporarily unavailable.");
  return body;
}

export function useLiveSearch(state: SearchState, engaged: boolean): LiveSearch {
  const [live, setLive] = useState<LiveSearch>({ loading: false, error: null, total: 0, results: [], page: [], pageCount: 1, pageIndex: 0, stateHash: null, filters: null, query: "" });
  /* the cursors already walked, per query */
  const cursors = useRef<Map<string, (string | null)[]>>(new Map());
  const sequence = useRef(0);
  const key = queryKey(state);
  const pageIndex = Math.max(0, state.after);

  useEffect(() => {
    if (!engaged) { setLive((current) => ({ ...current, loading: false, error: null, total: 0, results: [], page: [], pageCount: 1, pageIndex: 0, stateHash: null, filters: null, query: "" })); return; }
    const controller = new AbortController();
    const mine = sequence.current + 1;
    sequence.current = mine;
    setLive((current) => ({ ...current, loading: true, error: null }));
    (async () => {
      const known = cursors.current.get(key) ?? [null];
      let index = 0;
      let cursor: string | null = known[0] ?? null;
      let body: ApiResponse | null = null;
      /* walk to the requested page through the cursors, remembering each */
      while (true) {
        body = await fetchPage(state, cursor, controller.signal);
        if (index >= pageIndex || !body.pageInfo.hasNextPage || !body.pageInfo.nextCursor) break;
        index += 1;
        cursor = body.pageInfo.nextCursor;
        if (known.length <= index) known.push(cursor);
      }
      cursors.current.set(key, known);
      if (controller.signal.aborted || sequence.current !== mine || !body) return;
      const total = body.pageInfo.totalExact;
      setLive({
        loading: false,
        error: null,
        total,
        results: body.results.map(toResult),
        page: body.results.map(toResult),
        pageCount: Math.max(1, Math.ceil(total / PAGE_SIZE)),
        pageIndex: index,
        stateHash: body.stateHash,
        filters: body.query.filters,
        query: body.query.text,
      });
    })().catch((error: unknown) => {
      if (controller.signal.aborted || sequence.current !== mine) return;
      setLive((current) => ({ ...current, loading: false, error: error instanceof Error ? error.message : "The public Search service is temporarily unavailable." }));
    });
    return () => controller.abort();
  }, [key, pageIndex, engaged, state]);

  return live;
}

export function useSearchFacets(): SearchFacets {
  const [facets, setFacets] = useState<SearchFacets>(FALLBACK_FACETS);
  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/search/v1/facets", { headers: { Accept: "application/json" }, cache: "no-store", signal: controller.signal })
      .then((response) => (response.ok ? response.json() : null))
      .then((body: { objectTypes?: { value: string }[]; themes?: { value: string }[]; movements?: { value: string }[]; year?: { min: number; max: number }; starterQueries?: string[] } | null) => {
        if (!body || controller.signal.aborted) return;
        setFacets({
          objectTypes: (body.objectTypes ?? []).map((item) => item.value),
          themes: (body.themes ?? []).map((item) => item.value),
          movements: (body.movements ?? []).map((item) => item.value),
          yearMin: body.year?.min ?? YEAR_MIN,
          yearMax: body.year?.max ?? YEAR_MAX,
          starters: body.starterQueries ?? [],
          live: true,
        });
      })
      .catch(() => {
        // the fixture dictionaries stand until the live facets answer
      });
    return () => controller.abort();
  }, []);
  return facets;
}

export type GuidanceSuggestion = { label: string; apply: Partial<SearchState> };
export type Guidance = { note: string; suggestions: GuidanceSuggestion[] };

type GuidanceResponse = {
  surface: string;
  stateHash: string;
  note: string;
  suggestions: { id: string; label: string; action: { kind: string; parameters: Record<string, string | number> } }[];
};

function applyOf(action: GuidanceResponse["suggestions"][number]["action"]): Partial<SearchState> | null {
  if (action.kind === "SET_SEARCH_FILTER") {
    const apply: Partial<SearchState> = { after: 0 };
    for (const [field, value] of Object.entries(action.parameters)) {
      if (field === "yearFrom" || field === "yearTo") apply[field] = Number(value);
      else if (field === "objectType" || field === "theme" || field === "movement") apply[field] = String(value);
    }
    return apply;
  }
  if (action.kind === "REMOVE_SEARCH_FILTER") {
    const field = String(action.parameters.field);
    if (field === "year") return { yearFrom: null, yearTo: null, after: 0 };
    if (field === "objectType" || field === "theme" || field === "movement") return { [field]: null, after: 0 };
  }
  return null;
}

/* the shared System suggests endpoint, asked once per verified result set;
   only the answer for the current state hash is shown */
export function useSearchGuidance(live: LiveSearch): Guidance | null {
  const [guidance, setGuidance] = useState<{ stateHash: string; value: Guidance } | null>(null);
  const request = useMemo(() => (live.stateHash && !live.loading && live.filters ? { query: live.query, filters: live.filters, total: live.total, stateHash: live.stateHash } : null), [live.stateHash, live.loading, live.filters, live.query, live.total]);
  useEffect(() => {
    if (!request) return;
    const controller = new AbortController();
    fetch("/api/system-suggestions/v1", {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({ schemaVersion: "gda-system-suggestions-request/v2", surface: "SEARCH_RESULTS", reference: { query: request.query, filters: request.filters }, shown: { exactResultCount: request.total } }),
      cache: "no-store",
      signal: controller.signal,
    })
      .then((response) => (response.ok ? response.json() : null))
      .then((body: GuidanceResponse | null) => {
        if (!body || controller.signal.aborted || body.surface !== "SEARCH_RESULTS" || body.stateHash !== request.stateHash) return;
        setGuidance({ stateHash: request.stateHash, value: { note: body.note, suggestions: body.suggestions.map((item) => ({ label: item.label, apply: applyOf(item.action) })).filter((item): item is GuidanceSuggestion => item.apply !== null).slice(0, 2) } });
      })
      .catch(() => {
        // Search remains complete without guidance
      });
    return () => controller.abort();
  }, [request]);
  return guidance && live.stateHash === guidance.stateHash ? guidance.value : null;
}
