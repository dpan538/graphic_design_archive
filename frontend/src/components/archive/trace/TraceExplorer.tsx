"use client";

import { useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties } from "react";
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

const MOBILE_FEATURED_OBJECT_ID = "SURF-VAMYEARTRACEV2R0056";

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

function TraceViewIcon({ view }: { view: TraceView }) {
  if (view === "atlas") {
    return (
      <svg className={styles.viewTabIcon} viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <circle cx="12" cy="12" r="8.5" />
        <path d="M3.8 12h16.4M12 3.5c2.15 2.3 3.25 5.13 3.25 8.5S14.15 18.2 12 20.5M12 3.5C9.85 5.8 8.75 8.63 8.75 12s1.1 6.2 3.25 8.5" />
      </svg>
    );
  }

  if (view === "constellation") {
    return (
      <svg className={styles.viewTabIcon} viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <circle cx="6" cy="7" r="1.75" />
        <circle cx="15.75" cy="5.5" r="1.75" />
        <circle cx="12" cy="12" r="2.15" />
        <circle cx="6.5" cy="17.5" r="1.75" />
        <circle cx="18" cy="17" r="1.75" />
        <path d="m7.7 7.8 2.65 2.55m3.2-3.6-.9 3.15m1.15 3.05 2.65 2.45m-6.15-1.9-2.25 2.55" />
      </svg>
    );
  }

  return (
    <svg className={styles.viewTabIcon} viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <circle cx="5" cy="12" r="2" />
      <circle cx="18" cy="5" r="2" />
      <circle cx="18" cy="12" r="2" />
      <circle cx="18" cy="19" r="2" />
      <path d="M7 12h4m0 0c2.4 0 2.8-7 5-7m-5 7h5m-5 0c2.4 0 2.8 7 5 7" />
    </svg>
  );
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
  const [mobileViewMenuOpen, setMobileViewMenuOpen] = useState(false);
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

  async function changeView(next: TraceView) {
    setMobileViewMenuOpen(false);
    setView(next);
    if (next !== "object") return;

    const compactViewport = window.matchMedia("(max-width: 900px)").matches;
    if (!compactViewport) {
      await changeLayer(layer);
      return;
    }

    if (graph) {
      setDrawerOpen(false);
      return;
    }

    // Mobile opens with one real evidence neighbourhood. The searchable layer
    // remains available behind the drawer control, but it is not the first
    // screen: that desktop research list obscures the visual task on a phone.
    setLayer("active");
    setReviewSelection(null);
    setQuery("");
    setRegionMembers([]);
    setRegionLabel("");
    setDecade("");
    setMedium("");
    setDrawerOpen(false);
    try {
      await selectMobileActive();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Object trace unavailable");
      setLoading("");
      setDrawerOpen(true);
    }
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

  async function selectMobileActive(
    preferred?: (item: ActiveCatalogItem) => boolean,
  ) {
    const items = await ensureActiveCatalog();
    const selected = (preferred ? items?.find(preferred) : undefined)
      ?? items?.find((item) => item.id === MOBILE_FEATURED_OBJECT_ID)
      ?? items?.[0];
    if (!selected) throw new Error("The active TRACE catalog is empty");
    await selectActive(selected);
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
          const members = [linkedRegion];
          const linkedDecadeNumber = linkedDecade && Number.isFinite(Number(linkedDecade))
            ? Number(linkedDecade)
            : null;
          setRegionLabel(linkedRegion);
          setRegionMembers(members);
          if (linkedDecadeNumber !== null) setDecade(linkedDecadeNumber);
          if (window.matchMedia("(max-width: 900px)").matches) {
            const matched = items?.find((item) => (
              members.includes(item.region)
              && (linkedDecadeNumber === null || Math.floor(item.year / 10) * 10 === linkedDecadeNumber)
            ));
            if (matched) return selectActive(matched);
            return selectMobileActive();
          }
          setDrawerOpen(true);
        }
      })
      .catch((cause: unknown) => {
        setError(cause instanceof Error ? cause.message : "TRACE deep link unavailable");
        setLoading("");
      });
  }, [atlas]);

  function exploreCell(row: AtlasRegion, selectedDecade: number) {
    const compactViewport = window.matchMedia("(max-width: 900px)").matches;
    setView("object");
    void changeLayer("active").then(async () => {
      setRegionLabel(row.region);
      setRegionMembers(row.members ?? [row.region]);
      setDecade(selectedDecade);
      if (!compactViewport) return;

      const members = row.members ?? [row.region];
      await selectMobileActive((item) => (
        members.includes(item.region)
        && Math.floor(item.year / 10) * 10 === selectedDecade
      ));
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
      data-view={view}
      data-visual-fullscreen={view === "constellation" || (view === "object" && Boolean(graph))}
      data-drawer-open={view === "object" && drawerOpen}
    >
      <div
        className={styles.mobileViewPicker}
        data-open={mobileViewMenuOpen}
        onBlur={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget)) setMobileViewMenuOpen(false);
        }}
      >
        <button
          type="button"
          className={styles.mobileViewTrigger}
          aria-label={`Choose TRACE view; current ${view}`}
          aria-haspopup="menu"
          aria-expanded={mobileViewMenuOpen}
          onClick={() => setMobileViewMenuOpen((open) => !open)}
        >
          <TraceViewIcon view={view} />
        </button>
        <div className={styles.mobileViewMenu} role="menu" aria-label="Choose TRACE view">
          {(["atlas", "constellation", "object"] as TraceView[]).map((option) => (
            <button
              key={option}
              type="button"
              role="menuitemradio"
              aria-label={`Show ${option === "atlas" ? "global atlas" : option === "constellation" ? "evidence constellation" : "object trace"}`}
              aria-checked={view === option}
              onClick={() => {
                void changeView(option);
              }}
            >
              <TraceViewIcon view={option} />
            </button>
          ))}
        </div>
      </div>
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
        <button
          type="button"
          aria-label="Show global atlas"
          aria-pressed={view === "atlas"}
          onClick={() => void changeView("atlas")}
        >
          <TraceViewIcon view="atlas" />
          <span className={styles.viewTabDesktopLabel}>Global atlas</span>
          <span className={styles.viewTabMobileLabel}>Atlas</span>
        </button>
        <button
          type="button"
          aria-label="Show evidence constellation"
          aria-pressed={view === "constellation"}
          onClick={() => void changeView("constellation")}
        >
          <TraceViewIcon view="constellation" />
          <span className={styles.viewTabDesktopLabel}>Evidence constellation</span>
          <span className={styles.viewTabMobileLabel}>Evidence</span>
        </button>
        <button
          type="button"
          aria-label="Show object trace"
          aria-pressed={view === "object"}
          onClick={() => void changeView("object")}
        >
          <TraceViewIcon view="object" />
          <span className={styles.viewTabDesktopLabel}>Object trace</span>
          <span className={styles.viewTabMobileLabel}>Object</span>
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
              aria-label={drawerOpen ? "Collapse TRACE information and filters" : "Open TRACE information and filters"}
              aria-expanded={drawerOpen}
              aria-controls="trace-object-drawer"
              onClick={() => setDrawerOpen((value) => !value)}
            >
              <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                <path d="M4 6h5m4 0h7M4 12h10m4 0h2M4 18h2m4 0h10" />
                <circle cx="11" cy="6" r="2" />
                <circle cx="16" cy="12" r="2" />
                <circle cx="8" cy="18" r="2" />
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
  const [mobilePlaying, setMobilePlaying] = useState(false);
  const [mobileRegion, setMobileRegion] = useState(atlas.regionMatrix[0]?.region ?? "");
  const selectedMobileDecade = mobileDecade ?? atlas.decades.at(-1) ?? atlas.decades[0];
  const selectedMobileIndex = Math.max(0, atlas.decades.indexOf(selectedMobileDecade));
  const selectedMobileRow = atlas.regionMatrix.find((row) => row.region === mobileRegion)
    ?? atlas.regionMatrix[0];
  const selectedMobileCount = selectedMobileRow?.counts[selectedMobileIndex] ?? 0;
  const selectedRegionCount = atlas.regionMatrix.filter((row) => row.counts[selectedMobileIndex] > 0).length;
  const relationFamilyTotals = atlas.relationTypes.reduce<Record<string, number>>((totals, relation) => {
    if (relation.family !== "historical_influence") {
      totals[relation.family] = (totals[relation.family] ?? 0) + relation.count;
    }
    return totals;
  }, {});

  useEffect(() => {
    if (!mobilePlaying) return;
    const timer = window.setInterval(() => {
      const currentIndex = Math.max(0, atlas.decades.indexOf(selectedMobileDecade));
      setMobileDecade(atlas.decades[(currentIndex + 1) % atlas.decades.length]);
    }, 900);
    return () => window.clearInterval(timer);
  }, [atlas.decades, mobilePlaying, selectedMobileDecade, setMobileDecade]);

  useEffect(() => {
    if (selectedMobileRow?.counts[selectedMobileIndex]) return;
    const next = atlas.regionMatrix
      .map((row) => ({ row, count: row.counts[selectedMobileIndex] }))
      .sort((a, b) => b.count - a.count)[0];
    if (next?.row) setMobileRegion(next.row.region);
  }, [atlas.regionMatrix, selectedMobileIndex, selectedMobileRow]);

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
        <header className={styles.mobileAtlasHeader}>
          <div>
            <p>ACTIVE ARCHIVE / TIME × REGION</p>
            <h2>{selectedMobileDecade}s</h2>
          </div>
          <button
            type="button"
            className={styles.mobileAtlasPlay}
            aria-label={mobilePlaying ? "Pause archive development animation" : "Play archive development animation"}
            aria-pressed={mobilePlaying}
            onClick={() => setMobilePlaying((playing) => !playing)}
          >
            <span aria-hidden="true">{mobilePlaying ? "Ⅱ" : "▶"}</span>
          </button>
        </header>

        <dl className={styles.mobileAtlasMetrics}>
          <div><dt>Objects</dt><dd>{atlas.decadeTotals[selectedMobileIndex].toLocaleString()}</dd></div>
          <div><dt>Regions</dt><dd>{selectedRegionCount}</dd></div>
          <div><dt>TRACE edges</dt><dd>{atlas.counts.traceEdges.toLocaleString()}</dd></div>
        </dl>

        <div
          className={styles.mobileAtlasDots}
          style={{ "--mobile-atlas-columns": atlas.regionMatrix.length } as CSSProperties}
          role="img"
          aria-label="Dot matrix of active objects by decade and normalized region. Use the decade slider and region selector for an exact value."
        >
          {atlas.decades.flatMap((decade, index) => atlas.regionMatrix.map((row) => {
            const count = row.counts[index];
            const selected = decade === selectedMobileDecade && row.region === mobileRegion;
            return (
              <span
                key={`${decade}-${row.region}`}
                aria-hidden="true"
                data-decade-selected={decade === selectedMobileDecade}
                data-selected={selected}
                data-empty={!count}
                style={{ "--mobile-dot-purity": `${count ? Math.max(18, Math.round((count / maximum) * 100)) : 8}%` } as CSSProperties}
              />
            );
          }))}
        </div>

        <label className={styles.mobileAtlasTimeline}>
          <span>{atlas.decades[0]}</span>
          <input
            type="range"
            min={0}
            max={atlas.decades.length - 1}
            value={selectedMobileIndex}
            aria-label="Selected archive decade"
            onChange={(event) => {
              setMobilePlaying(false);
              setMobileDecade(atlas.decades[Number(event.target.value)]);
            }}
          />
          <span>{atlas.decades.at(-1)}</span>
        </label>

        <article className={styles.mobileAtlasSelection} aria-live="polite">
          <label>
            Region
            <select
              value={selectedMobileRow?.region ?? ""}
              onChange={(event) => {
                setMobilePlaying(false);
                setMobileRegion(event.target.value);
              }}
            >
              {atlas.regionMatrix.map((row) => (
                <option key={row.region} value={row.region}>{row.region}</option>
              ))}
            </select>
          </label>
          <strong>{selectedMobileCount.toLocaleString()}</strong>
          <span>active objects · {selectedMobileDecade}s</span>
          <button
            type="button"
            disabled={!selectedMobileCount || !selectedMobileRow}
            onClick={() => selectedMobileRow && exploreCell(selectedMobileRow, selectedMobileDecade)}
          >
            Open objects
          </button>
        </article>

        <div className={styles.mobileAtlasFamilies} aria-label="Documented relation-family totals">
          {[
            ["Source", relationFamilyTotals.source_provenance ?? 0],
            ["Time / place", relationFamilyTotals.time_place ?? 0],
            ["Medium / context", relationFamilyTotals.medium_context ?? 0],
          ].map(([label, value]) => (
            <span key={String(label)} style={{ "--family-share": `${(Number(value) / Math.max(1, atlas.counts.traceEdges)) * 100}%` } as CSSProperties}>
              <i aria-hidden="true" /><b>{label}</b><em>{Number(value).toLocaleString()}</em>
            </span>
          ))}
        </div>
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
