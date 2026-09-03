"use client";

import { MOVEMENTS, OBJECT_TYPES, THEMES } from "../lib/fixture";
import { YEAR_MAX, YEAR_MIN, type SearchState } from "../lib/query";
import styles from "./SearchMobileFilters.module.css";

const clampYear = (n: number) =>
  Math.min(YEAR_MAX, Math.max(YEAR_MIN, Math.round(n) || YEAR_MIN));

/* Compact stacked filters. Year · Object type · Theme · Movement. */
export default function SearchMobileFilters({
  state,
  patch,
}: {
  state: SearchState;
  patch: (p: Partial<SearchState>) => void;
}) {
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
