"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ChevronDown, GripHorizontal, X } from "lucide-react";
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
import SearchInput from "./SearchInput";
import SearchFilters from "./SearchFilters";
import SearchResults from "./SearchResults";
import SystemSuggests from "./SystemSuggests";
import styles from "./SearchDesktop.module.css";

type Pos = { x: number; y: number };

/* The desktop Search window — a long perforated ticket, draggable, anchored
   top-right, never taller than the viewport (results scroll inside).
   State is URL-backed; Close is history.back(). */
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
      router.replace(qs ? `/search?${qs}` : "/search", { scroll: false });
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
  const { total, page, pageCount, pageIndex, results } = runSearch(state);
  const suggest = engaged && total > 0 ? suggestFor(state, results) : null;

  const panel = (
    <>
      <button
        type="button"
        className={styles.scrim}
        aria-label="Close search"
        onClick={close}
      />

      <section
        ref={cardRef}
        className={styles.ticket}
        role="dialog"
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

          {filtersOpen ? <SearchFilters state={state} patch={patch} /> : null}

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
        </div>

        {engaged ? (
          <div className={styles.scroll}>
            <SearchResults
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
            <SystemSuggests
              lines={suggest.lines}
              suggestions={suggest.suggestions}
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
