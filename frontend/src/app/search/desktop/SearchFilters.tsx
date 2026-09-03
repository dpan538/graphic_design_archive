"use client";

import { MOVEMENTS, OBJECT_TYPES, THEMES } from "../lib/fixture";
import { YEAR_MAX, YEAR_MIN, type SearchState } from "../lib/query";
import styles from "./SearchFilters.module.css";

const clampYear = (n: number) =>
  Math.min(YEAR_MAX, Math.max(YEAR_MIN, Math.round(n) || YEAR_MIN));

/* 02 Filters — two abreast, three rows: [From][To] · [Type][Theme] ·
   [Movement][note]. */
export default function SearchFilters({
  state,
  patch,
}: {
  state: SearchState;
  patch: (p: Partial<SearchState>) => void;
}) {
  return (
    <div className={styles.grid}>
      <label className={styles.field}>
        <span className={styles.label}>From</span>
        <input
          className={styles.year}
          type="number"
          inputMode="numeric"
          placeholder={String(YEAR_MIN)}
          value={state.yearFrom ?? ""}
          onChange={(e) =>
            patch({ yearFrom: e.target.value ? clampYear(+e.target.value) : null })
          }
        />
      </label>

      <label className={styles.field}>
        <span className={styles.label}>To</span>
        <input
          className={styles.year}
          type="number"
          inputMode="numeric"
          placeholder={String(YEAR_MAX)}
          value={state.yearTo ?? ""}
          onChange={(e) =>
            patch({ yearTo: e.target.value ? clampYear(+e.target.value) : null })
          }
        />
      </label>

      <label className={styles.field}>
        <span className={styles.label}>Object type</span>
        <select
          className={styles.select}
          value={state.objectType ?? ""}
          onChange={(e) => patch({ objectType: e.target.value || null })}
        >
          <option value="">Any</option>
          {OBJECT_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </label>

      <label className={styles.field}>
        <span className={styles.label}>Theme</span>
        <select
          className={styles.select}
          value={state.theme ?? ""}
          onChange={(e) => patch({ theme: e.target.value || null })}
        >
          <option value="">Any</option>
          {THEMES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </label>

      <label className={styles.field}>
        <span className={styles.label}>Movement</span>
        <select
          className={styles.select}
          value={state.movement ?? ""}
          onChange={(e) => patch({ movement: e.target.value || null })}
        >
          <option value="">Any (sparse)</option>
          {MOVEMENTS.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
