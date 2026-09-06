"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ChevronDown, GripHorizontal, X } from "lucide-react";
import SiteNav from "@/components/site/SiteNav";
import { useSearchDialog } from "../lib/useSearchDialog";
import {
  activeFilterCount,
  EMPTY_STATE,
  hasQuery,
  parseSearch,
  toParams,
  type SearchState,
} from "../lib/query";
import { useLiveSearch, useSearchFacets, useSearchGuidance } from "../lib/live";
import SearchInput from "./SearchInput";
import SearchFilters from "./SearchFilters";
import SearchResults from "./SearchResults";
import SystemSuggests from "./SystemSuggests";
import styles from "./SearchDesktop.module.css";

type Pos = { x: number; y: number };

/* The desktop Search window — a long perforated ticket, draggable, anchored
   top-right, never taller than the viewport (results scroll inside).
   State is URL-backed; Close is history.back(). Results, counts and the
   dictionaries come from the live public search API (lib/live.ts); System
   suggests comes from the shared guidance endpoint, asked with the query,
   the filters and the count shown, never with the window's own reading. */
export default function SearchDesktop({ asModal = false }: { asModal?: boolean } = {}) {
  const router = useRouter();
  const params = useSearchParams();

  const urlState = useMemo(
    () => parseSearch(new URLSearchParams(params.toString())),
    [params],
  );
  const [state, setState] = useState<SearchState>(urlState);
  useEffect(() => setState(urlState), [urlState]);

  const sync = useCallback(
    (next: SearchState) => {
      setState(next);
      const qs = toParams(next).toString();
      /* the URL follows the state through the history API: no soft navigation, so the
         intercepting modal route never mounts a second window over the standalone page */
      if (typeof window !== "undefined") window.history.replaceState(window.history.state, "", qs ? `/search?${qs}` : "/search");
      else router.replace(qs ? `/search?${qs}` : "/search", { scroll: false });
    },
    [router],
  );
  const patch = (p: Partial<SearchState>) => sync({ ...state, ...p, after: p.after ?? 0 });
  const reset = () => sync(EMPTY_STATE);
  const close = () => {
    if (typeof window !== "undefined" && window.history.length > 1) window.history.back();
    else window.location.href = "/";
  };

  // Collapsed by default — keeps the panel short; the list comes first.
  const [filtersOpen, setFiltersOpen] = useState(false);

  // ---- drag ----
  const cardRef = useRef<HTMLElement>(null);
  useSearchDialog(cardRef, close);
  const grab = useRef<{ dx: number; dy: number } | null>(null);
  const [pos, setPos] = useState<Pos | null>(null);

  const onPointerDown = (e: React.PointerEvent) => {
    const el = cardRef.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    grab.current = { dx: e.clientX - r.left, dy: e.clientY - r.top };
    setPos({ x: r.left, y: r.top });
    (e.currentTarget as Element).setPointerCapture(e.pointerId);
    document.body.style.cursor = "grabbing";
  };
  const onPointerMove = (e: React.PointerEvent) => {
    if (!grab.current || !cardRef.current) return;
    const w = cardRef.current.offsetWidth;
    const x = Math.min(
      Math.max(8, e.clientX - grab.current.dx),
      window.innerWidth - Math.min(w, 260),
    );
    const y = Math.min(
      Math.max(8, e.clientY - grab.current.dy),
      window.innerHeight - 72,
    );
    setPos({ x, y });
  };
  const endDrag = (e: React.PointerEvent) => {
    grab.current = null;
    document.body.style.cursor = "";
    (e.currentTarget as Element).releasePointerCapture?.(e.pointerId);
  };

  const engaged = hasQuery(state);
  const [retryKey, setRetryKey] = useState(0);
  const live = useLiveSearch(state, engaged, retryKey);
  const facets = useSearchFacets();
  const guidance = useSearchGuidance(live);
  const { total, page, pageCount, pageIndex } = live;
  const starters = facets.starters.slice(0, 4);

  const panel = (
    <>
      <button
        type="button"
        className={styles.scrim}
        tabIndex={-1}
        aria-label="Close search"
        onClick={close}
      />

      <section
        ref={cardRef}
        className={styles.ticket}
        role="dialog"
        aria-modal="true"
        aria-label="Search the archive"
        style={pos ? { left: pos.x, top: pos.y, right: "auto" } : undefined}
      >
        <div
          className={styles.stub}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={endDrag}
          onPointerCancel={endDrag}
        >
          <span className={styles.mark}>Search ;</span>
          <GripHorizontal size={16} strokeWidth={2.5} aria-hidden="true" className={styles.grip} />
          <button
            type="button"
            className={styles.close}
            onClick={close}
            onPointerDown={(e) => e.stopPropagation()}
            aria-label="Close search"
          >
            <X size={18} strokeWidth={3} aria-hidden="true" />
          </button>
        </div>

        <div className={styles.fixed}>
          <SearchInput
            value={state.q}
            onChange={(q) => patch({ q })}
            onClear={() => patch({ q: "" })}
          />

          <button
            type="button"
            className={styles.filterToggle}
            aria-expanded={filtersOpen}
            onClick={() => setFiltersOpen((v) => !v)}
          >
            {filtersOpen ? "Hide filters" : "Filters"}
            {activeFilterCount(state) > 0 ? (
              <span className={styles.filterN}>{activeFilterCount(state)}</span>
            ) : null}
            <ChevronDown
              size={15}
              strokeWidth={3}
              aria-hidden="true"
              data-open={filtersOpen || undefined}
            />
          </button>

          {filtersOpen ? <SearchFilters state={state} patch={patch} facets={facets} /> : null}

          {engaged ? (
            <div className={styles.qstate}>
              <p className={styles.qsum}>
                <b>{total}</b> {total === 1 ? "result" : "results"}
                <span className={styles.qsep}>·</span>
                {[
                  state.q ? `“${state.q}”` : null,
                  state.objectType,
                  state.theme,
                  state.movement,
                  state.yearFrom || state.yearTo
                    ? `${state.yearFrom ?? "…"}–${state.yearTo ?? "…"}`
                    : null,
                ]
                  .filter(Boolean)
                  .join("  ·  ")}
              </p>
              <button type="button" className={styles.clear} onClick={reset}>
                Clear all
              </button>
            </div>
          ) : (
            <div className={styles.starters}>
              <p className={styles.startersLabel}>Try</p>
              <ul role="list">
                {starters.map((s) => (
                  <li key={s.label}>
                    <button type="button" onClick={() => sync({ ...EMPTY_STATE, ...s.apply })}>
                      {s.label}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {engaged ? (
          <div className={styles.scroll} aria-busy={live.loading || undefined}>
            {live.error ? (
              <div role="status"><p className={styles.qsum}>{live.error}</p><button type="button" onClick={() => setRetryKey((key) => key + 1)}>Retry Search</button></div>
            ) : live.stateHash === null ? null : (
              <SearchResults
                page={page}
                total={total}
                pageIndex={pageIndex}
                pageCount={pageCount}
                onPage={(n) => sync({ ...state, after: n })}
              />
            )}
          </div>
        ) : null}

        {guidance ? (
          <div className={styles.suggestsSlot}>
            <SystemSuggests
              lines={[guidance.note]}
              suggestions={guidance.suggestions}
              onApply={(a) => sync({ ...state, ...a })}
            />
          </div>
        ) : null}
      </section>
    </>
  );

  /* Opened over the page you were already on (the intercepting @modal route):
     the panel is position:fixed and brings its own scrim, so it needs no page
     chrome — and must not render a second SiteNav on top of the host page's. */
  if (asModal) return panel;

  return (
    <div className={styles.page}>
      <SiteNav active="search" />
      {panel}
    </div>
  );
}
