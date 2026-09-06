"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ChevronDown, Search as SearchIcon, X } from "lucide-react";
import SiteNavMobile from "@/components/site/mobile/SiteNavMobile";
import shell from "@/components/site/mobile/MobileShell.module.css";
import { useSearchDialog } from "../lib/useSearchDialog";
import { useLiveSearch, useSearchFacets, useSearchGuidance } from "../lib/live";
import {
  activeFilterCount,
  EMPTY_STATE,
  hasQuery,
  parseSearch,
  toParams,
  type SearchState,
} from "../lib/query";
import SearchMobileFilters from "./SearchMobileFilters";
import SearchMobileResults from "./SearchMobileResults";
import SearchMobileSuggests from "./SearchMobileSuggests";
import { useSearchViewport } from "./useSearchViewport";
import styles from "./SearchMobile.module.css";

/* Mobile Search — the ticket window. Opened from the bar it is an OVERLAY on
   the page the reader is on (asOverlay: a scrim over the host page, the
   ticket on its own paper, the page's scroll locked); visited directly at
   /search it is a page with the bar. URL-backed; Close is history.back(). */
export default function SearchMobile({ asOverlay = false }: { asOverlay?: boolean }) {
  const router = useRouter();
  const params = useSearchParams();
  const inputRef = useRef<HTMLInputElement>(null);

  const urlState = useMemo(
    () => parseSearch(new URLSearchParams(params.toString())),
    [params],
  );
  const [state, setState] = useState<SearchState>(urlState);
  // Collapsed by default on the height-constrained ticket — the list comes first.
  const [filtersOpen, setFiltersOpen] = useState(false);
  useEffect(() => setState(urlState), [urlState]);
  /* the page focuses its field; the overlay does not, so opening it costs no
     keyboard animation on top of the layer itself */
  useEffect(() => {
    if (!asOverlay) inputRef.current?.focus();
  }, [asOverlay]);

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

  const viewportRef = useRef<HTMLDivElement>(null);
  useSearchViewport(viewportRef, asOverlay);
  const cardRef = useRef<HTMLElement>(null);
  useSearchDialog(cardRef, close);
  const engaged = hasQuery(state);
  /* the live public search API, its dictionaries and the shared guidance (lib/live.ts) */
  const [retryKey, setRetryKey] = useState(0);
  const live = useLiveSearch(state, engaged, retryKey);
  const facets = useSearchFacets();
  const guidance = useSearchGuidance(live);
  const { total, page, pageCount, pageIndex } = live;
  const starters = facets.starters.slice(0, 4);

  return (
    /* The overlay's own rules are written at double specificity, so the
       shell's paper and height can never win over the scrim whichever
       stylesheet loads last. It sits beneath the bar, which stays live. */
    <div ref={viewportRef} className={`${shell.shell} ${asOverlay ? styles.overlay : styles.page}`} data-search-overlay={asOverlay || undefined}>
      {asOverlay ? null : <SiteNavMobile active="search" />}

      <div className={styles.backdrop} onClick={asOverlay ? (event) => { if (event.target === event.currentTarget) close(); } : undefined}>
        <section ref={cardRef} className={styles.ticket} role={asOverlay ? "dialog" : undefined} aria-modal={asOverlay || undefined} aria-label="Search the archive">
          <div className={styles.head}>
            <span className={styles.mark}>Search</span>
            <button type="button" className={styles.close} onClick={close} aria-label="Close search">
              <X size={18} strokeWidth={3} aria-hidden="true" />
            </button>
          </div>

          <div className={styles.field}>
            <span className={styles.lab}>Query</span>
            <div className={styles.inputWrap}>
              <SearchIcon size={16} strokeWidth={3} aria-hidden="true" />
              <input
                ref={inputRef}
                className={styles.input}
                type="search"
                placeholder="Find an object…"
                value={state.q}
                aria-label="Search query"
                onChange={(e) => patch({ q: e.target.value })}
              />
              {state.q ? (
                <button
                  type="button"
                  className={styles.clr}
                  aria-label="Clear query"
                  onClick={() => patch({ q: "" })}
                >
                  <X size={14} strokeWidth={3} aria-hidden="true" />
                </button>
              ) : null}
            </div>
          </div>

          <button
            type="button"
            className={styles.filterToggle}
            aria-expanded={filtersOpen}
            onClick={() => setFiltersOpen((v) => !v)}
          >
            Filters
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

          {filtersOpen ? <SearchMobileFilters state={state} patch={patch} facets={facets} /> : null}

          {engaged ? (
            <div className={styles.qstate}>
              <span>
                <b>{total}</b> {total === 1 ? "result" : "results"}
              </span>
              <button type="button" className={styles.clear} onClick={reset}>
                Clear all
              </button>
            </div>
          ) : (
            <div className={styles.starters}>
              <span className={styles.lab}>Try</span>
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

          {engaged ? (
            <div className={styles.scroll} aria-busy={live.loading || undefined}>
              {live.error ? (
                <div role="status"><p className={styles.lab}>{live.error}</p><button type="button" onClick={() => setRetryKey((key) => key + 1)}>Retry Search</button></div>
              ) : live.stateHash === null ? null : (
                <SearchMobileResults
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
              <SearchMobileSuggests
                lines={[guidance.note]}
                suggestions={guidance.suggestions}
                onApply={(a) => sync({ ...state, ...a })}
              />
            </div>
          ) : null}
        </section>
      </div>
    </div>
  );
}
