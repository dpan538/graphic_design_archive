"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import styles from "./SearchWorkspace.module.css";

type FacetValue = { value: string; count: number };
type StarterQuery = {
  id: string;
  label: string;
  query: string;
  filters: Readonly<Record<string, string | number>>;
};

export type SearchWorkspaceFacets = {
  documentCount: number;
  year: { min: number; max: number };
  objectTypes: readonly FacetValue[];
  themes: readonly FacetValue[];
  movements: readonly FacetValue[];
  starterQueries: readonly StarterQuery[];
};

type SearchResult = {
  objectId: string;
  title: string;
  creditedLabel: string | null;
  displayDate: string;
  year: { start: number; end: number };
  place: string;
  objectType: string;
  themes: readonly string[];
  movements: readonly string[];
  sourceLabel: string;
  deliveryState: string;
  objectPageRoute: string;
  matchExplanation: string;
};

type SearchResponse = {
  release: { algorithmVersion: string };
  query: { text: string };
  results: readonly SearchResult[];
  pageInfo: { hasNextPage: boolean; nextCursor: string | null; totalExact: number };
};

type SearchState = "idle" | "loading" | "ready" | "error";
type Draft = {
  query: string;
  yearFrom: string;
  yearTo: string;
  objectType: string;
  theme: string;
  movement: string;
};

const URL_FIELDS = ["q", "yearFrom", "yearTo", "objectType", "theme", "movement"] as const;

function userMessage(error: unknown): string {
  return error instanceof Error ? error.message : "The public Search service is unavailable.";
}

function starterHref(starter: StarterQuery): string {
  const parameters = new URLSearchParams();
  if (starter.query) parameters.set("q", starter.query);
  for (const [key, value] of Object.entries(starter.filters)) parameters.set(key, String(value));
  return `/search?${parameters.toString()}`;
}

function fallback(value: string | null | undefined): React.ReactNode {
  return value ? value : <span className={styles.missing}>Not recorded</span>;
}

export default function SearchWorkspace({ facets }: { facets: SearchWorkspaceFacets }) {
  const titleId = useId();
  const router = useRouter();
  const parameters = useSearchParams();
  const canonicalState = parameters.toString();
  const url = useMemo(() => new URLSearchParams(canonicalState), [canonicalState]);
  const current: Draft = useMemo(() => ({
    query: url.get("q") ?? "",
    yearFrom: url.get("yearFrom") ?? "",
    yearTo: url.get("yearTo") ?? "",
    objectType: url.get("objectType") ?? "",
    theme: url.get("theme") ?? "",
    movement: url.get("movement") ?? "",
  }), [url]);
  const after = url.get("after") ?? "";
  const hasCriteria = URL_FIELDS.some((field) => Boolean(url.get(field)?.trim()));
  const [draft, setDraft] = useState<Draft>(current);
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [state, setState] = useState<SearchState>(hasCriteria ? "loading" : "idle");
  const [error, setError] = useState("");
  const [retryVersion, setRetryVersion] = useState(0);
  const requestRef = useRef<AbortController | null>(null);
  const queryLength = Array.from(draft.query.trim()).length;

  const runSearch = useCallback(async (requestParameters: URLSearchParams, signal: AbortSignal) => {
    const apiParameters = new URLSearchParams();
    for (const field of URL_FIELDS) {
      const value = requestParameters.get(field)?.trim();
      if (value) apiParameters.set(field, value);
    }
    const cursor = requestParameters.get("after");
    if (cursor) apiParameters.set("after", cursor);
    apiParameters.set("first", "25");
    const result = await fetch(`/api/search/v1?${apiParameters.toString()}`, {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
      signal,
    });
    const body = await result.json().catch(() => null) as (SearchResponse & { detail?: string }) | null;
    if (!result.ok || !body) throw new Error(body?.detail ?? "The public Search service is temporarily unavailable.");
    return body;
  }, []);

  useEffect(() => {
    setDraft(current);
    requestRef.current?.abort();
    if (!hasCriteria) {
      setResponse(null);
      setState("idle");
      setError("");
      return;
    }
    const controller = new AbortController();
    requestRef.current = controller;
    setState("loading");
    setError("");
    void runSearch(new URLSearchParams(canonicalState), controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return;
        setResponse(result);
        setState("ready");
      })
      .catch((cause) => {
        if (controller.signal.aborted) return;
        setResponse(null);
        setState("error");
        setError(userMessage(cause));
      });
    return () => controller.abort();
  }, [canonicalState, current, hasCriteria, retryVersion, runSearch]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (queryLength > 160) return;
    const next = new URLSearchParams();
    if (draft.query.trim()) next.set("q", draft.query.trim());
    if (draft.yearFrom) next.set("yearFrom", draft.yearFrom);
    if (draft.yearTo) next.set("yearTo", draft.yearTo);
    if (draft.objectType) next.set("objectType", draft.objectType);
    if (draft.theme) next.set("theme", draft.theme);
    if (draft.movement) next.set("movement", draft.movement);
    const route = next.size ? `/search?${next.toString()}` : "/search";
    if (next.toString() === canonicalState) setRetryVersion((value) => value + 1);
    else router.push(route, { scroll: false });
  }

  function clear() {
    requestRef.current?.abort();
    router.push("/search", { scroll: false });
  }

  function nextPage() {
    const cursor = response?.pageInfo.nextCursor;
    if (!cursor) return;
    const next = new URLSearchParams(canonicalState);
    next.set("after", cursor);
    router.push(`/search?${next.toString()}`, { scroll: true });
  }

  return (
    <section className={`read-platform ${styles.workspace}`} aria-labelledby={titleId} aria-busy={state === "loading"}>
      <p className="read-platform__eyebrow">Public archive objects · {facets.documentCount.toLocaleString("en-US")} records</p>
      <h1 id={titleId}>Search the archive</h1>
      <p className={styles.intro}>Find public object pages by stable ID, title, credited designer or studio, and place. Refine the same Search by year, object type, theme, or movement.</p>

      <form onSubmit={submit} className={`read-platform__form ${styles.searchForm}`} role="search">
        <label htmlFor="archive-search">Object ID, title, credited name, or place</label>
        <div className={styles.queryRow}>
          <input
            id="archive-search"
            type="search"
            value={draft.query}
            onChange={(event) => setDraft((value) => ({ ...value, query: event.target.value }))}
            autoComplete="off"
            aria-describedby="search-help search-count"
          />
          <button type="submit" disabled={state === "loading" || queryLength > 160}>Search</button>
          {hasCriteria || Object.values(draft).some(Boolean) ? <button type="button" className={styles.secondaryButton} onClick={clear}>Clear</button> : null}
        </div>

        <fieldset className={styles.filters}>
          <legend>Refine results</legend>
          <div className={styles.filterGrid}>
            <label>
              Year range
              <span className={styles.yearInputs}>
                <input aria-label="Year from" inputMode="numeric" type="number" min={facets.year.min} max={facets.year.max} placeholder="From" value={draft.yearFrom} onChange={(event) => setDraft((value) => ({ ...value, yearFrom: event.target.value }))} />
                <input aria-label="Year to" inputMode="numeric" type="number" min={facets.year.min} max={facets.year.max} placeholder="To" value={draft.yearTo} onChange={(event) => setDraft((value) => ({ ...value, yearTo: event.target.value }))} />
              </span>
            </label>
            <label>
              Object type
              <select value={draft.objectType} onChange={(event) => setDraft((value) => ({ ...value, objectType: event.target.value }))}>
                <option value="">All object types</option>
                {facets.objectTypes.map((facet) => <option key={facet.value} value={facet.value}>{facet.value} ({facet.count.toLocaleString("en-US")})</option>)}
              </select>
            </label>
            <label>
              Theme
              <select value={draft.theme} onChange={(event) => setDraft((value) => ({ ...value, theme: event.target.value }))}>
                <option value="">All themes</option>
                {facets.themes.map((facet) => <option key={facet.value} value={facet.value}>{facet.value} ({facet.count.toLocaleString("en-US")})</option>)}
              </select>
            </label>
            <label>
              Movement
              <select value={draft.movement} onChange={(event) => setDraft((value) => ({ ...value, movement: event.target.value }))}>
                <option value="">All movements</option>
                {facets.movements.map((facet) => <option key={facet.value} value={facet.value}>{facet.value} ({facet.count.toLocaleString("en-US")})</option>)}
              </select>
            </label>
          </div>
          <div className={styles.formActions}>
            <button type="submit" disabled={state === "loading" || queryLength > 160}>Apply Search</button>
          </div>
        </fieldset>
        <span className={styles.help}>
          <small id="search-help">All selected filters apply together. Empty text is allowed when at least one filter is selected.</small>
          <small id="search-count" className={queryLength > 160 ? styles.invalid : undefined}>{queryLength}/160 characters</small>
        </span>
      </form>

      {!hasCriteria ? (
        <div>
          <p>Begin with a public collection value:</p>
          <ul className={styles.starters} aria-label="Curated Search starters">
            {facets.starterQueries.map((starter) => <li key={starter.id}><Link href={starterHref(starter)}>{starter.label}</Link></li>)}
          </ul>
        </div>
      ) : null}

      <div className={styles.status} aria-live="polite" aria-atomic="true">
        {state === "loading" ? <p>Searching public object records…</p> : null}
        {state === "error" ? <p role="alert">Search failed: {error}<button type="button" onClick={() => setRetryVersion((value) => value + 1)}>Retry</button></p> : null}
        {state === "ready" && response?.pageInfo.totalExact === 0 ? <p>No public objects match this Search. Remove a filter or try a shorter text fragment.</p> : null}
        {state === "ready" && response && response.pageInfo.totalExact > 0 ? <p>{response.pageInfo.totalExact.toLocaleString("en-US")} {response.pageInfo.totalExact === 1 ? "object" : "objects"} found{after ? " · later page" : ""}</p> : null}
      </div>

      <ol className={`read-platform__results ${styles.results}`}>
        {response?.results.map((result) => (
          <li key={result.objectId}>
            <Link className={styles.resultTitle} href={result.objectPageRoute}>{result.title}</Link>
            <div className={styles.meta}>
              <code>{result.objectId}</code>
              <span>{fallback(result.creditedLabel)}</span>
              <span>{fallback(result.displayDate)}</span>
              <span>{fallback(result.place)}</span>
            </div>
            <div className={styles.taxonomies}>
              <span>{fallback(result.objectType)}</span>
              {result.themes.map((theme) => <span key={theme}>{theme}</span>)}
              {result.movements.map((movement) => <span key={movement}>{movement}</span>)}
            </div>
            <p className={styles.reason}>{result.matchExplanation}</p>
          </li>
        ))}
      </ol>

      {state === "ready" && response && (after || response.pageInfo.hasNextPage) ? (
        <nav className={styles.pagination} aria-label="Search result pages">
          {after ? <button type="button" onClick={() => router.back()}>Previous page</button> : null}
          {response.pageInfo.hasNextPage ? <button type="button" onClick={nextPage}>Next page</button> : null}
          <span>25 objects maximum per page</span>
        </nav>
      ) : null}

      {response?.results.length ? <p className={styles.algorithm}>Results are ordered by deterministic relevance over public metadata. Search does not include TRACE research objects.</p> : null}
    </section>
  );
}
