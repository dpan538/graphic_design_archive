"use client";

import YearInput from "@/components/site/YearInput";
import type { SearchState } from "../lib/query";
import type { SearchFacets } from "../lib/live";
import styles from "./SearchMobileFilters.module.css";

/* Compact stacked filters. Year · Object type · Theme · Movement. The
   dictionaries and the year range are the live index's (lib/live.ts). */
export default function SearchMobileFilters({
  state,
  patch,
  facets,
}: {
  state: SearchState;
  patch: (p: Partial<SearchState>) => void;
  facets: SearchFacets;
}) {
  const YEAR_MIN = facets.yearMin;
  const YEAR_MAX = facets.yearMax;
  const OBJECT_TYPES = facets.objectTypes;
  const THEMES = facets.themes;
  const MOVEMENTS = facets.movements;
  return (
    <div className={styles.filters}>
      <div className={styles.year}>
        <YearInput
          disabled={!facets.live}
          type="number"
          inputMode="numeric"
          placeholder={facets.live ? String(YEAR_MIN) : ""}
          aria-label="From year"
          value={state.yearFrom}
          min={YEAR_MIN}
          max={YEAR_MAX}
          onCommit={(value) => patch({ yearFrom: value })}
        />
        <span aria-hidden="true">—</span>
        <YearInput
          disabled={!facets.live}
          type="number"
          inputMode="numeric"
          placeholder={facets.live ? String(YEAR_MAX) : ""}
          aria-label="To year"
          value={state.yearTo}
          min={YEAR_MIN}
          max={YEAR_MAX}
          onCommit={(value) => patch({ yearTo: value })}
        />
      </div>

      <select
          disabled={!facets.live}
        aria-label="Object type"
        value={state.objectType ?? ""}
        onChange={(e) => patch({ objectType: e.target.value || null })}
      >
        <option value="">Any object type</option>
        {OBJECT_TYPES.map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>

      <select
          disabled={!facets.live}
        aria-label="Theme"
        value={state.theme ?? ""}
        onChange={(e) => patch({ theme: e.target.value || null })}
      >
        <option value="">Any theme</option>
        {THEMES.map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>

      <select
          disabled={!facets.live}
        aria-label="Movement"
        value={state.movement ?? ""}
        onChange={(e) => patch({ movement: e.target.value || null })}
      >
        <option value="">Any movement (sparse)</option>
        {MOVEMENTS.map((m) => (
          <option key={m} value={m}>
            {m}
          </option>
        ))}
      </select>
    </div>
  );
}
