"use client";

import Link from "next/link";
import { useDeferredValue, useEffect, useMemo, useState } from "react";
import { searchArchiveSurfaces, type ArchiveSearchResult } from "@/lib/archive-search-client";
import {
  TRACE_FAMILY_META,
  TRACE_TYPE_DEFINITIONS,
} from "../trace/trace-taxonomy";
import type {
  ActiveCatalogItem,
  CompactPayload,
  RelationFamily,
  TraceAtlas,
} from "../trace/trace-types";
import styles from "./SearchWorkspace.module.css";

type SearchScope = "all" | "archive" | "trace" | "relations";

function decodeCompact<T>(payload: CompactPayload): T[] {
  return payload.items.map((values) => {
    const result: Record<string, unknown> = {};
    payload.schema.forEach((field, index) => {
      const dictionary = payload.dictionaries[field];
      result[field] = dictionary ? dictionary[Number(values[index])] : values[index];
    });
    return result as T;
  });
}

function includesQuery(values: Array<string | number>, query: string) {
  const terms = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  if (!terms.length) return true;
  const text = values.join(" ").toLocaleLowerCase();
  return terms.every((term) => text.includes(term));
}

export default function SearchWorkspace() {
  const [atlas, setAtlas] = useState<TraceAtlas | null>(null);
  const [catalog, setCatalog] = useState<ActiveCatalogItem[]>([]);
  const [query, setQuery] = useState("");
  const [scope, setScope] = useState<SearchScope>("all");
  const [region, setRegion] = useState("");
  const [decade, setDecade] = useState("");
  const [medium, setMedium] = useState("");
  const [family, setFamily] = useState<RelationFamily | "">("");
  const [error, setError] = useState("");
  const [archiveResults, setArchiveResults] = useState<ArchiveSearchResult[]>([]);
  const [archivePending, setArchivePending] = useState(false);
  const deferredQuery = useDeferredValue(query);

  useEffect(() => {
    const initialQuery = new URLSearchParams(window.location.search).get("q");
    if (initialQuery) setQuery(initialQuery);
  }, []);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    fetch("/data/trace-v48/atlas.json", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`TRACE atlas unavailable (${response.status})`);
        return response.json() as Promise<TraceAtlas>;
      })
      .then(async (loadedAtlas) => {
        if (!active) return;
        setAtlas(loadedAtlas);
        const response = await fetch(loadedAtlas.assets.catalog, { signal: controller.signal });
        if (!response.ok) throw new Error(`TRACE catalog unavailable (${response.status})`);
        const payload = await response.json() as CompactPayload;
        if (active) setCatalog(decodeCompact<ActiveCatalogItem>(payload));
      })
      .catch((cause: unknown) => {
        if (active && !controller.signal.aborted) setError(cause instanceof Error ? cause.message : "Search data unavailable");
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, []);

  const regions = useMemo(() => Array.from(new Set(catalog.map((item) => item.region))).sort(), [catalog]);
  const media = useMemo(() => Array.from(new Set(catalog.map((item) => item.mediumGroup))).sort(), [catalog]);
  const decades = useMemo(() => Array.from(new Set(catalog.map((item) => Math.floor(item.year / 10) * 10))).sort((a, b) => a - b), [catalog]);

  const traceResults = useMemo(() => catalog.filter((item) =>
    includesQuery([item.id, item.title, item.year, item.region, item.source, item.mediumGroup, item.tier, item.tree], deferredQuery)
    && (!region || item.region === region)
    && (!decade || Math.floor(item.year / 10) * 10 === Number(decade))
    && (!medium || item.mediumGroup === medium),
  ), [catalog, decade, deferredQuery, medium, region]);

  useEffect(() => {
    let active = true;
    const normalized = deferredQuery.trim();
    if (!normalized || (scope !== "all" && scope !== "archive")) {
      setArchiveResults([]);
      setArchivePending(false);
      return () => {
        active = false;
      };
    }
    setArchivePending(true);
    void searchArchiveSurfaces(normalized, 120)
      .then((matches) => {
        if (active) setArchiveResults(matches);
      })
      .catch((cause: unknown) => {
        if (active) setError(cause instanceof Error ? cause.message : "Archive search unavailable");
      })
      .finally(() => {
        if (active) setArchivePending(false);
      });
    return () => {
      active = false;
    };
  }, [deferredQuery, scope]);

  const relationResults = useMemo(() => TRACE_TYPE_DEFINITIONS.filter((definition) =>
    includesQuery([
      definition.code,
      definition.label,
      definition.id,
      definition.definition,
      definition.evidenceRequirement,
      definition.allowedAssertion,
      definition.prohibitedInference,
    ], deferredQuery) && (!family || definition.family === family),
  ), [deferredQuery, family]);

  const showTrace = scope === "all" || scope === "trace";
  const showArchive = scope === "all" || scope === "archive";
  const showRelations = scope === "all" || scope === "relations";
  const total = (showTrace ? traceResults.length : 0)
    + (showArchive ? archiveResults.length : 0)
    + (showRelations ? relationResults.length : 0);

  function clearFilters() {
    setQuery("");
    setScope("all");
    setRegion("");
    setDecade("");
    setMedium("");
    setFamily("");
  }

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <p>SEARCH / ARCHIVE + TRACE</p>
          <h1>Search the evidence layer, not only the page index.</h1>
        </div>
        <dl>
          <div><dt>Active TRACE</dt><dd>{atlas?.counts.activeObjects.toLocaleString() ?? "…"}</dd></div>
          <div><dt>Relation types</dt><dd>{TRACE_TYPE_DEFINITIONS.length}</dd></div>
          <div><dt>Visible matches</dt><dd>{total.toLocaleString()}</dd></div>
        </dl>
      </header>

      <section className={styles.searchStage} aria-labelledby="search-workspace-title">
        <label className={styles.queryLabel}>
          <span id="search-workspace-title">Query</span>
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="object title, creator, source, place, medium, TRACE code…"
            autoComplete="off"
          />
        </label>
        <div className={styles.scopeControl} aria-label="Search scope">
          {(["all", "trace", "relations", "archive"] as const).map((value) => (
            <button key={value} type="button" aria-pressed={scope === value} onClick={() => setScope(value)}>{value}</button>
          ))}
        </div>
      </section>

      <section className={styles.filterRail} aria-label="Search filters">
        <label>Region<select value={region} onChange={(event) => setRegion(event.target.value)} disabled={!showTrace}><option value="">All regions</option>{regions.map((value) => <option key={value}>{value}</option>)}</select></label>
        <label>Decade<select value={decade} onChange={(event) => setDecade(event.target.value)} disabled={!showTrace}><option value="">All decades</option>{decades.map((value) => <option key={value} value={value}>{value}s</option>)}</select></label>
        <label>Medium group<select value={medium} onChange={(event) => setMedium(event.target.value)} disabled={!showTrace}><option value="">All media</option>{media.map((value) => <option key={value}>{value}</option>)}</select></label>
        <label>Relation family<select value={family} onChange={(event) => setFamily(event.target.value as RelationFamily | "")} disabled={!showRelations}><option value="">All families</option>{Object.entries(TRACE_FAMILY_META).map(([value, meta]) => <option key={value} value={value}>{meta.code} · {meta.label}</option>)}</select></label>
        <button type="button" onClick={clearFilters}>Clear</button>
      </section>

      {error ? <p className={styles.error}>{error}</p> : null}
      <section className={styles.results} aria-live="polite">
        {showTrace ? (
          <article>
            <header><p>Active TRACE objects</p><b>{traceResults.length.toLocaleString()}</b></header>
            <div className={styles.tableWrap}>
              <table>
                <thead><tr><th>Object</th><th>Year</th><th>Region</th><th>Medium</th><th>Source</th><th>Route</th></tr></thead>
                <tbody>
                  {traceResults.slice(0, 240).map((item) => (
                    <tr key={item.id}>
                      <td><Link href={`/trace?object=${encodeURIComponent(item.id)}`}>{item.title}</Link><small>{item.id}</small></td>
                      <td>{item.year}</td><td>{item.region}</td><td>{item.mediumGroup}</td><td>{item.source}</td>
                      <td><Link href={`/trace?object=${encodeURIComponent(item.id)}`}>Open three views</Link></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {traceResults.length > 240 ? <p className={styles.limitNote}>Showing the first 240 of {traceResults.length.toLocaleString()} matches. Refine by region, decade or medium.</p> : null}
          </article>
        ) : null}

        {showRelations ? (
          <article>
            <header><p>Normalized TRACE relation types</p><b>{relationResults.length}</b></header>
            <div className={styles.relationGrid}>
              {relationResults.map((definition) => (
                <Link key={definition.id} href={`/trace/types/${definition.id}`}>
                  <span>{definition.code} · {TRACE_FAMILY_META[definition.family].label}</span>
                  <strong>{definition.label}</strong>
                  <small>{definition.count.toLocaleString()} frozen v48 edges · {definition.status.replaceAll("_", " ")}</small>
                </Link>
              ))}
            </div>
          </article>
        ) : null}

        {showArchive ? (
          <article>
            <header><p>Published archive surfaces</p><b>{archivePending ? "…" : archiveResults.length}</b></header>
            {deferredQuery.trim() ? (
              <div className={styles.archiveGrid}>
                {archiveResults.map(({ surface, field, snippet }) => (
                  <Link key={surface.surfaceId} href={`/surfaces/${surface.surfaceId}`}>
                    <span>{surface.dateText} · {field}</span>
                    <strong>{surface.title}</strong>
                    <small>{snippet}</small>
                  </Link>
                ))}
              </div>
            ) : <p className={styles.emptyNote}>Enter a query to search the published archive surface index.</p>}
          </article>
        ) : null}
      </section>
    </main>
  );
}
