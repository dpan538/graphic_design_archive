"use client";

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
  const clampYear = (n: number) =>
    Math.min(YEAR_MAX, Math.max(YEAR_MIN, Math.round(n) || YEAR_MIN));
  return (
    <div className={styles.filters}>
      <div className={styles.year}>
        <input
          type="number"
          inputMode="numeric"
          placeholder={String(YEAR_MIN)}
          aria-label="From year"
          value={state.yearFrom ?? ""}
          onChange={(e) =>
            patch({ yearFrom: e.target.value ? clampYear(+e.target.value) : null })
          }
        />
        <span aria-hidden="true">—</span>
        <input
          type="number"
          inputMode="numeric"
          placeholder={String(YEAR_MAX)}
          aria-label="To year"
          value={state.yearTo ?? ""}
          onChange={(e) =>
            patch({ yearTo: e.target.value ? clampYear(+e.target.value) : null })
          }
        />
      </div>

      <select
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
