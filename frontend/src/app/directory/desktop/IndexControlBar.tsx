"use client";

import { SlidersHorizontal } from "lucide-react";
import styles from "./IndexControlBar.module.css";

/* 02/03 — the only fixed chrome above the list. A Filter button (opens the
   drawer) + the active slice, dimension-coloured, + a zero-padded count.
   The list is what the reader sees first; filtering is a deliberate second act. */
export default function IndexControlBar({
  summary,
  count,
  pristine,
  filtersOpen,
  activeCount,
  onOpenFilters,
  onReset,
}: {
  summary: { region: string; years: string; themes: string; visual: string };
  count: number;
  pristine: boolean;
  filtersOpen: boolean;
  activeCount: number;
  onOpenFilters: () => void;
  onReset: () => void;
}) {
  return (
    <div className={styles.bar}>
      <button
        type="button"
        className={styles.filterBtn}
        aria-expanded={filtersOpen}
        onClick={onOpenFilters}
      >
        <SlidersHorizontal size={16} strokeWidth={3} aria-hidden="true" />
        Filter
        {activeCount > 0 ? <span className={styles.n}>{activeCount}</span> : null}
      </button>

      <p className={styles.slice}>
        <span className={styles.seg} data-accent="region">
          {summary.region}
        </span>
        <span className={styles.dot} aria-hidden="true">
          ·
        </span>
        <span>{summary.years}</span>
        <span className={styles.dot} aria-hidden="true">
          ·
        </span>
        <span className={styles.seg} data-accent="theme">
          {summary.themes}
        </span>
        <span className={styles.dot} aria-hidden="true">
          ·
        </span>
        <span>{summary.visual}</span>
      </p>

      <p className={styles.right}>
        <span className={styles.count}>
          {String(count).padStart(3, "0")} {count === 1 ? "object" : "objects"}
        </span>
        {!pristine ? (
          <button type="button" className={styles.reset} onClick={onReset}>
            Reset
          </button>
        ) : null}
      </p>
    </div>
  );
}
