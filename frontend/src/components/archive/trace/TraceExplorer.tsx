"use client";

import { useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
import ChronogeographicRoutes from "./ChronogeographicRoutes";
import TraceConstellationSystem from "./TraceConstellationSystem";
import TraceDiagrams from "./TraceDiagrams";
import TraceEvidenceTable from "./TraceEvidenceTable";
import styles from "./TraceExplorer.module.css";
import type { TraceSelection } from "./trace-taxonomy";
import type {
  ActiveCatalogItem,
  AtlasRegion,
  AuxiliaryPayload,
  CompactPayload,
  ReviewCatalogItem,
  TraceAtlas,
  TraceGraph,
  TraceLayer,
  TraceView,
} from "./trace-types";

function decodeCompact<T>(payload: CompactPayload): T[] {
  return payload.items.map((values) => {
    const result: Record<string, unknown> = {};
    payload.schema.forEach((field, index) => {
      const dictionary = payload.dictionaries[field];
      const value = values[index];
      result[field] = dictionary ? dictionary[Number(value)] : value;
    });
    return result as T;
  });
}

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`TRACE asset unavailable (${response.status})`);
  return response.json() as Promise<T>;
}

function contains(haystack: Array<string | number | null>, query: string) {
  const normalized = query.trim().toLocaleLowerCase();
  if (!normalized) return true;
  return haystack.some((value) => String(value ?? "").toLocaleLowerCase().includes(normalized));
}

function externalProps(href: string) {
  return href.startsWith("http")
    ? { target: "_blank", rel: "noreferrer" }
    : {};
}

export default function TraceExplorer() {
  const [atlas, setAtlas] = useState<TraceAtlas | null>(null);
  const [view, setView] = useState<TraceView>("atlas");
  const [layer, setLayer] = useState<TraceLayer>("active");
  const [catalog, setCatalog] = useState<ActiveCatalogItem[] | null>(null);
  const [review, setReview] = useState<ReviewCatalogItem[] | null>(null);
  const [auxiliary, setAuxiliary] = useState<AuxiliaryPayload | null>(null);
  const [graph, setGraph] = useState<TraceGraph | null>(null);
  const [traceSelection, setTraceSelection] = useState<TraceSelection | null>(null);
  const [reviewSelection, setReviewSelection] = useState<ReviewCatalogItem | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(true);
  const [query, setQuery] = useState("");
  const [regionMembers, setRegionMembers] = useState<string[]>([]);
  const [regionLabel, setRegionLabel] = useState("");
  const [decade, setDecade] = useState<number | "">("");
  const [medium, setMedium] = useState("");
  const [mobileDecade, setMobileDecade] = useState<number | null>(null);
  const [loading, setLoading] = useState("Loading frozen TRACE atlas…");
  const [error, setError] = useState("");
  const shardCache = useRef(new Map<string, Record<string, TraceGraph>>());
  const deepLinkHandled = useRef(false);
  const deferredQuery = useDeferredValue(query);

  useEffect(() => {
    let active = true;
    getJson<TraceAtlas>("/data/trace-v48/atlas.json")
      .then((value) => {
        if (!active) return;
        setAtlas(value);
        setMobileDecade(value.decades.at(-1) ?? null);
        setLoading("");
      })
      .catch((cause: unknown) => {
        if (!active) return;
        setError(cause instanceof Error ? cause.message : "TRACE atlas unavailable");
        setLoading("");
      });
    return () => {
      active = false;
    };
  }, []);

  async function ensureActiveCatalog() {
    if (catalog || !atlas) return catalog;
    setLoading("Loading active object index…");
    const payload = await getJson<CompactPayload>(atlas.assets.catalog);
    const items = decodeCompact<ActiveCatalogItem>(payload);
    setCatalog(items);
    setLoading("");
    return items;
  }

  async function ensureReviewCatalog() {
    if (review || !atlas) return review;
    setLoading("Loading isolated review index…");
    const payload = await getJson<CompactPayload>(atlas.assets.review);
    const items = decodeCompact<ReviewCatalogItem>(payload);
    setReview(items);
    setLoading("");
    return items;
  }

  async function ensureAuxiliary() {
    if (auxiliary || !atlas) return auxiliary;
    setLoading("Loading auxiliary media branch…");
    const payload = await getJson<AuxiliaryPayload>(atlas.assets.auxiliary);
    setAuxiliary(payload);
    setLoading("");
    return payload;
  }

  async function loadLayerData(next: TraceLayer) {
    setError("");
    try {
      if (next === "active") await ensureActiveCatalog();
      if (next === "review") await ensureReviewCatalog();
      if (next === "auxiliary") await ensureAuxiliary();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Layer unavailable");
      setLoading("");
    }
  }

  async function changeLayer(next: TraceLayer) {
    setLayer(next);
    setGraph(null);
    setTraceSelection(null);
    setReviewSelection(null);
    setQuery("");
    setRegionMembers([]);
    setRegionLabel("");
    setDecade("");
    setMedium("");
    setDrawerOpen(true);
    await loadLayerData(next);
  }

  async function selectActive(item: ActiveCatalogItem) {
    if (!atlas) return;
    setReviewSelection(null);
    setLoading(`Loading direct evidence for ${item.title}…`);
    setError("");
    try {
      let shard = shardCache.current.get(item.shard);
      if (!shard) {
        const payload = await getJson<{ objects: Record<string, TraceGraph> }>(
          `${atlas.assets.neighborhoodBase}${item.shard}.json`,
        );
        shard = payload.objects;
        shardCache.current.set(item.shard, shard);
      }
      const selected = shard[item.id];
      if (!selected) throw new Error("Object neighbourhood is not present in its declared shard");
      setGraph(selected);
      setTraceSelection(null);
      setDrawerOpen(false);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Object trace unavailable");
    } finally {
      setLoading("");
    }
  }

  useEffect(() => {
    if (!atlas || deepLinkHandled.current) return;
    const params = new URLSearchParams(window.location.search);
    const objectId = params.get("object");
    const linkedRegion = params.get("region");
    const linkedDecade = params.get("decade");
    if (!objectId && !linkedRegion) return;
    deepLinkHandled.current = true;
    setView("object");
    setLayer("active");
    void ensureActiveCatalog()
      .then((items) => {
        if (objectId) {
          const item = items?.find((candidate) => candidate.id === objectId);
          if (!item) throw new Error(`TRACE object ${objectId} is not present in the active catalog`);
          return selectActive(item);
        }
        if (linkedRegion) {
          setRegionLabel(linkedRegion);
          setRegionMembers([linkedRegion]);
          if (linkedDecade && Number.isFinite(Number(linkedDecade))) setDecade(Number(linkedDecade));
          setDrawerOpen(true);
        }
      })
      .catch((cause: unknown) => {
        setError(cause instanceof Error ? cause.message : "TRACE deep link unavailable");
        setLoading("");
      });
  }, [atlas]);

  function exploreCell(row: AtlasRegion, selectedDecade: number) {
    setView("object");
    void changeLayer("active").then(() => {
      setRegionLabel(row.region);
      setRegionMembers(row.members ?? [row.region]);
      setDecade(selectedDecade);
    });
  }

  const activeResults = useMemo(() => {
    if (!catalog || layer !== "active") return [];
    return catalog
      .filter((item) =>
        contains([item.id, item.title, item.year, item.region, item.source, item.mediumGroup], deferredQuery),
      )
      .filter((item) => !regionMembers.length || regionMembers.includes(item.region))
      .filter((item) => decade === "" || Math.floor(item.year / 10) * 10 === decade)
      .filter((item) => !medium || item.mediumGroup === medium)
      .slice(0, 60);
  }, [catalog, decade, deferredQuery, layer, medium, regionMembers]);

  const reviewResults = useMemo(() => {
    if (!review || layer !== "review") return [];
    return review
      .filter((item) => contains([item.id, item.surfaceId, item.title, item.year, item.region, item.source], deferredQuery))
      .slice(0, 60);
  }, [deferredQuery, layer, review]);

  const auxiliaryResults = useMemo(() => {
    if (!auxiliary || layer !== "auxiliary") return [];
    return auxiliary.items.filter((item) =>
      contains(
        [item.object.id, item.object.title, item.object.year, item.object.region, item.object.medium, item.object.source],
        deferredQuery,
      ),
    );
  }, [auxiliary, deferredQuery, layer]);

  if (loading && !atlas) {
    return <main className={styles.loading}>{loading}</main>;
  }
  if (!atlas) {
    return <main className={styles.loading}>{error || "TRACE atlas unavailable"}</main>;
  }

  return (
    <main
      className={styles.page}
      data-visual-fullscreen={view === "constellation" || (view === "object" && Boolean(graph))}
      data-drawer-open={view === "object" && drawerOpen}
    >
      <header className={styles.header}>
        <div>
          <p className={styles.eyebrow}>TRACE / frozen candidate v48</p>
          <h1>Evidence routes, locally readable and globally aggregated</h1>
          <p className={styles.intro}>
            TRACE follows documented source, creator, collection, date, place and medium relations.
            It does not infer historical influence from proximity or similarity.
          </p>
        </div>
        <dl className={styles.counts} aria-label="Frozen TRACE counts">
          <div><dt>Active</dt><dd>{atlas.counts.activeObjects.toLocaleString()}</dd></div>
          <div><dt>Auxiliary</dt><dd>{atlas.counts.auxiliaryObjects}</dd></div>
          <div><dt>Influence</dt><dd>{atlas.counts.influenceEdges}</dd></div>
        </dl>
      </header>

      <div className={styles.viewTabs} aria-label="TRACE view">
        <button type="button" aria-pressed={view === "atlas"} onClick={() => setView("atlas")}>
          Global atlas
        </button>
        <button type="button" aria-pressed={view === "constellation"} onClick={() => setView("constellation")}>
          Evidence constellation
        </button>
        <button
          type="button"
          aria-pressed={view === "object"}
          onClick={() => {
            setView("object");
            void changeLayer(layer);
          }}
        >
          Object trace
        </button>
      </div>

      {view === "atlas" ? (
        <AtlasView atlas={atlas} mobileDecade={mobileDecade} setMobileDecade={setMobileDecade} exploreCell={exploreCell} />
      ) : view === "constellation" ? (
        <TraceConstellationSystem atlas={atlas} />
      ) : (
        <section className={styles.objectView} aria-label="Object TRACE explorer">
          <div
            className={styles.objectWorkspace}
            data-drawer-open={drawerOpen}
            data-has-visual={Boolean(graph)}
          >
            <button
              type="button"
              className={styles.drawerToggle}
              aria-expanded={drawerOpen}
              aria-controls="trace-object-drawer"
              onClick={() => setDrawerOpen((value) => !value)}
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M4 5h16M4 12h10M4 19h16" />
                <path d={drawerOpen ? "m9 9-3 3 3 3" : "m6 9 3 3-3 3"} />
              </svg>
              <span>{drawerOpen ? "Collapse information" : "Open information"}</span>
            </button>

            <aside
              id="trace-object-drawer"
              className={styles.objectDrawer}
              data-open={drawerOpen}
              aria-hidden={!drawerOpen}
              inert={!drawerOpen}
              aria-label="TRACE object information and selection"
            >
              <div className={styles.drawerScroll}>
                <div className={styles.filters}>
                  <label>
                    Layer
                    <select value={layer} onChange={(event) => void changeLayer(event.target.value as TraceLayer)}>
                      <option value="active">Active main objects</option>
                      <option value="auxiliary">Auxiliary photo / print branch</option>
                      <option value="review">Authority review / hold</option>
                    </select>
                  </label>
                  <label className={styles.searchField}>
                    Search this layer
                    <input
                      type="search"
                      value={query}
                      onFocus={() => void loadLayerData(layer)}
                      onChange={(event) => setQuery(event.target.value)}
                      placeholder="Title, ID, place, source or medium"
                    />
                  </label>
                  {layer === "active" ? (
                    <>
                      <label>
                        Decade
                        <select value={decade} onChange={(event) => setDecade(event.target.value ? Number(event.target.value) : "")}>
                          <option value="">All decades</option>
                          {atlas.decades.map((value) => <option key={value} value={value}>{value}s</option>)}
                        </select>
                      </label>
                      <label>
                        Medium branch
                        <select value={medium} onChange={(event) => setMedium(event.target.value)}>
                          <option value="">All media</option>
                          {atlas.mediumGroups.map((item) => <option key={item.name} value={item.name}>{item.name}</option>)}
                        </select>
                      </label>
                    </>
                  ) : null}
                </div>

                <div className={styles.layerNote}>
                  {layer === "active" ? (
                    <span>{regionLabel ? `${regionLabel} · ` : ""}Active counts only. Select an object to load one evidence neighbourhood.</span>
                  ) : layer === "auxiliary" ? (
                    <span>11 source-documented, count-ineligible media adjuncts. No promotion and no influence inference.</span>
                  ) : (
                    <span>Authority-uncertain review records remain visible but are not mixed into active totals or graph edges.</span>
                  )}
                  {(regionLabel || decade !== "" || medium) && layer === "active" ? (
                    <button
                      type="button"
                      className={styles.clearButton}
                      onClick={() => {
                        setRegionLabel(""); setRegionMembers([]); setDecade(""); setMedium("");
                      }}
                    >
                      Clear filters
                    </button>
                  ) : null}
                </div>

                <div className={styles.results} role="region" aria-label={`${layer} TRACE results`}>
                  {loading ? <p>{loading}</p> : null}
                  {error ? <p className={styles.error}>{error}</p> : null}
                  {layer === "active" && !catalog ? <p>Focus the search field to load the compact active index.</p> : null}
                  {layer === "active" ? activeResults.map((item) => (
                    <button key={item.id} type="button" onClick={() => void selectActive(item)} aria-pressed={graph?.object.id === item.id}>
                      <strong>{item.title}</strong>
                      <span>{item.year} · {item.region}</span>
                      <span>{item.mediumGroup} · {item.tier.replaceAll("_", " ")}</span>
                    </button>
                  )) : null}
                  {layer === "auxiliary" ? auxiliaryResults.map((item) => (
                    <button
                      key={item.object.id}
                      type="button"
                      onClick={() => {
                        setGraph(item); setTraceSelection(null); setReviewSelection(null); setDrawerOpen(false);
                      }}
                      aria-pressed={graph?.object.id === item.object.id}
                    >
                      <strong>{item.object.title}</strong>
                      <span>{item.object.year} · {item.object.region}</span>
                      <span>{item.object.mediumGroup} · count ineligible</span>
                    </button>
                  )) : null}
                  {layer === "review" ? reviewResults.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => {
                        setReviewSelection(item); setGraph(null); setDrawerOpen(true);
                      }}
                      aria-pressed={reviewSelection?.id === item.id}
                    >
                      <strong>{item.title}</strong>
                      <span>{item.year ?? "undated"} · {item.region}</span>
                      <span>{item.authorityState.replaceAll("_", " ")}</span>
                    </button>
                  )) : null}
                </div>

                {graph ? (
                  <ObjectInfoPanel
                    graph={graph}
                    selection={traceSelection}
                    onSelect={setTraceSelection}
                  />
                ) : null}
                {reviewSelection ? <ReviewRecord item={reviewSelection} /> : null}
              </div>
            </aside>

            <div className={styles.graphArea}>
              {graph ? (
                <LocalTrace
                  atlas={atlas}
                  graph={graph}
                  selection={traceSelection}
                  onSelect={(selection) => {
                    setTraceSelection(selection);
                    setDrawerOpen(true);
                  }}
                />
              ) : null}
              {reviewSelection ? (
                <div className={styles.emptyState}>
                  <h2>Review record isolated</h2>
                  <p>This authority-hold record remains in the information drawer and does not generate an active TRACE graph.</p>
                </div>
              ) : null}
              {!graph && !reviewSelection ? (
                <div className={styles.emptyState}>
                  <h2>Select one record</h2>
                  <p>Open the information drawer to search. The page loads only one direct, evidence-labelled neighbourhood.</p>
                </div>
              ) : null}
            </div>
          </div>
        </section>
      )}
      <p className={styles.live} aria-live="polite">{loading || error}</p>
    </main>
  );
}

function AtlasView({
  atlas,
  mobileDecade,
  setMobileDecade,
  exploreCell,
}: {
  atlas: TraceAtlas;
  mobileDecade: number | null;
  setMobileDecade: (value: number) => void;
  exploreCell: (row: AtlasRegion, decade: number) => void;
}) {
  const maximum = Math.max(...atlas.regionMatrix.flatMap((row) => row.counts));
  const decadeIndex = mobileDecade === null ? -1 : atlas.decades.indexOf(mobileDecade);
  return (
    <section className={styles.atlas} aria-label="Active object time and geography atlas">
      <div className={styles.atlasStatement}>
        <h2>Active layer distribution</h2>
        <p>
          Counts use frozen object geography. Repository location, creator nationality and search terms are not substituted.
        </p>
      </div>
      <ChronogeographicRoutes atlas={atlas} exploreCell={exploreCell} />

      <div className={styles.mobileAtlas}>
        <label>
          Decade
          <select value={mobileDecade ?? ""} onChange={(event) => setMobileDecade(Number(event.target.value))}>
            {atlas.decades.map((value) => <option key={value} value={value}>{value}s</option>)}
          </select>
        </label>
        <ol>
          {atlas.regionMatrix
            .map((row) => ({ row, count: decadeIndex >= 0 ? row.counts[decadeIndex] : 0 }))
            .filter((item) => item.count)
            .sort((a, b) => b.count - a.count)
            .map(({ row, count }) => (
              <li key={row.region}>
                <button type="button" onClick={() => mobileDecade !== null && exploreCell(row, mobileDecade)}>
                  <span>{row.region}</span><strong>{count.toLocaleString()}</strong>
                </button>
              </li>
            ))}
        </ol>
      </div>

      <details className={styles.matrixFallback}>
        <summary>Exact region × decade count table</summary>
        <div className={styles.matrixWrap}>
          <table className={styles.matrix}>
            <caption>Active objects by normalized region and decade. Select a count to inspect matching objects.</caption>
            <thead><tr><th scope="col">Region</th>{atlas.decades.map((value) => <th key={value} scope="col">{String(value).slice(2)}s</th>)}<th scope="col">Total</th></tr></thead>
            <tbody>
              {atlas.regionMatrix.map((row) => (
                <tr key={row.region}>
                  <th scope="row">{row.region}</th>
                  {row.counts.map((count, index) => (
                    <td key={atlas.decades[index]}>
                      {count ? (
                        <button
                          type="button"
                          style={{
                            ["--trace-intensity" as string]: `${Math.round(
                              Math.max(8, (count / maximum) * 34),
                            )}%`,
                          }}
                          aria-label={`${row.region}, ${atlas.decades[index]}s: ${count} objects`}
                          onClick={() => exploreCell(row, atlas.decades[index])}
                        >
                          {count}
                        </button>
                      ) : <span aria-label={`${row.region}, ${atlas.decades[index]}s: 0 objects`}>—</span>}
                    </td>
                  ))}
                  <td>{row.total.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>

      <div className={styles.atlasLists}>
        <section>
          <h3>Evidence relation vocabulary</h3>
          <ul>{atlas.relationTypes.slice(0, 18).map((item) => <li key={item.label}><span>{item.label.replaceAll("_", " ")}</span><strong>{item.count.toLocaleString()}</strong></li>)}</ul>
        </section>
        <section>
          <h3>Source distribution</h3>
          <ul>{atlas.topSources.slice(0, 12).map((item) => <li key={item.name}><span>{item.name}</span><strong>{item.count.toLocaleString()}</strong></li>)}</ul>
        </section>
        <section>
          <h3>Medium display branches</h3>
          <ul>{atlas.mediumGroups.map((item) => <li key={item.name}><span>{item.name}</span><strong>{item.count.toLocaleString()}</strong></li>)}</ul>
          <p>Display filters only; they do not reclassify frozen objects.</p>
        </section>
      </div>
    </section>
  );
}

function LocalTrace({
  atlas,
  graph,
  selection,
  onSelect,
}: {
  atlas: TraceAtlas;
  graph: TraceGraph;
  selection: TraceSelection | null;
  onSelect: (selection: TraceSelection) => void;
}) {
  return (
    <article className={styles.localTrace} aria-label={`TRACE visualizations for ${graph.object.title}`}>
      <TraceDiagrams atlas={atlas} graph={graph} selection={selection} onSelect={onSelect} />
    </article>
  );
}

function ObjectInfoPanel({
  graph,
  selection,
  onSelect,
}: {
  graph: TraceGraph;
  selection: TraceSelection | null;
  onSelect: (selection: TraceSelection) => void;
}) {
  return (
    <article className={styles.objectInfoPanel}>
      <header className={styles.rootNode} data-layer={graph.object.layer}>
        <p>{graph.object.layer === "auxiliary" ? "Auxiliary TRACE node / not counted" : "Active object root"}</p>
        <h2>{graph.object.title}</h2>
        <dl>
          <div><dt>Date</dt><dd>{graph.object.year}</dd></div>
          <div><dt>Place</dt><dd>{graph.object.region}</dd></div>
          <div><dt>Medium</dt><dd>{graph.object.medium}</dd></div>
          <div><dt>TRACE tier</dt><dd>{graph.object.traceTier.replaceAll("_", " ")}</dd></div>
        </dl>
        <a href={graph.object.href} {...externalProps(graph.object.href)}>
          Open {graph.object.hrefKind === "object" ? "object page" : "official source page"}
        </a>
      </header>

      <p className={styles.noInfluence}>
        No documented <code>influenced_by</code> edge exists in the v48 freeze. These are evidence and association routes, not influence claims.
      </p>

      <TraceEvidenceTable graph={graph} selection={selection} onSelect={onSelect} />
    </article>
  );
}

function ReviewRecord({ item }: { item: ReviewCatalogItem }) {
  return (
    <article className={styles.reviewRecord}>
      <p>Authority review / count isolated</p>
      <h2>{item.title}</h2>
      <dl>
        <div><dt>Date</dt><dd>{item.year ?? "Undated"}</dd></div>
        <div><dt>Region</dt><dd>{item.region}</dd></div>
        <div><dt>Authority</dt><dd>{item.authorityState.replaceAll("_", " ")}</dd></div>
        <div><dt>TRACE</dt><dd>{item.traceState.replaceAll("_", " ")}</dd></div>
        <div><dt>Review route</dt><dd>{item.reviewRoute}</dd></div>
        <div><dt>Count policy</dt><dd>{item.countPolicy}</dd></div>
      </dl>
      <a href={item.href} {...externalProps(item.href)}>Open source page</a>
    </article>
  );
}
