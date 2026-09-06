"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ChevronDown, Search as SearchIcon, X } from "lucide-react";
import SiteNav from "@/components/site/SiteNav";
import { STARTERS } from "../lib/fixture";
import {
  activeFilterCount,
  EMPTY_STATE,
  hasQuery,
  parseSearch,
  runSearch,
  toParams,
  type SearchState,
} from "../lib/query";
import { suggestFor } from "../lib/suggest";
import SearchMobileFilters from "./SearchMobileFilters";
import SearchMobileResults from "./SearchMobileResults";
import SearchMobileSuggests from "./SearchMobileSuggests";
import styles from "./SearchMobile.module.css";

/* Mobile Search — a ticket window (~350px on a 390px screen), its own layout,
   not a shrink of the desktop card. URL-backed; Close is history.back(). */
export default function SearchMobile() {
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
  useEffect(() => inputRef.current?.focus(), []);

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

  const engaged = hasQuery(state);
  const { total, page, pageCount, pageIndex, results } = runSearch(state);
  const suggest = engaged && total > 0 ? suggestFor(state, results) : null;

  return (
    <div className={styles.page}>
      <SiteNav variant="mobile" active="search" />

      <div className={styles.backdrop}>
        <section className={styles.ticket} role="dialog" aria-label="Search the archive">
          <div className={styles.head}>
            <span className={styles.mark}>Search ;</span>
            <button type="button" className={styles.close} onClick={close} aria-label="Close search">
              <X size={18} strokeWidth={3} aria-hidden="true" />
            </button>
          </div>

          <div className={styles.field}>
            <span className={styles.lab}>Query ;</span>
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
            Filters ;
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

          {filtersOpen ? <SearchMobileFilters state={state} patch={patch} /> : null}

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
              <span className={styles.lab}>Try ;</span>
              <ul role="list">
                {STARTERS.map((s) => (
                  <li key={s}>
                    <button type="button" onClick={() => patch({ q: s })}>
                      {s}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {engaged ? (
            <div className={styles.scroll}>
              <SearchMobileResults
                page={page}
                total={total}
                pageIndex={pageIndex}
                pageCount={pageCount}
                onPage={(n) => sync({ ...state, after: n })}
              />
            </div>
          ) : null}

          {suggest && (suggest.lines.length || suggest.suggestions.length) ? (
            <div className={styles.suggestsSlot}>
              <SearchMobileSuggests
                lines={suggest.lines}
                suggestions={suggest.suggestions}
                onApply={(a) => sync({ ...state, ...a })}
              />
            </div>
          ) : null}
        </section>
      </div>
    </div>
  );
}
