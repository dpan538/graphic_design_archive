"use client";

import YearInput from "@/components/site/YearInput";
import type { SearchState } from "../lib/query";
import type { SearchFacets } from "../lib/live";
import styles from "./SearchFilters.module.css";

/* 02 Filters — two abreast, three rows: [From][To] · [Type][Theme] ·
   [Movement][note]. The dictionaries and the year range are the live
   index's (lib/live.ts). */
export default function SearchFilters({
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
    <div className={styles.grid}>
      <label className={styles.field}>
        <span className={styles.label}>From</span>
        <YearInput
          disabled={!facets.live}
          className={styles.year}
          type="number"
          inputMode="numeric"
          placeholder={facets.live ? String(YEAR_MIN) : ""}
          value={state.yearFrom}
          min={YEAR_MIN}
          max={YEAR_MAX}
          onCommit={(value) => patch({ yearFrom: value })}
        />
      </label>

      <label className={styles.field}>
        <span className={styles.label}>To</span>
        <YearInput
          disabled={!facets.live}
          className={styles.year}
          type="number"
          inputMode="numeric"
          placeholder={facets.live ? String(YEAR_MAX) : ""}
          value={state.yearTo}
          min={YEAR_MIN}
          max={YEAR_MAX}
          onCommit={(value) => patch({ yearTo: value })}
        />
      </label>

      <label className={styles.field}>
        <span className={styles.label}>Object type</span>
        <select
          disabled={!facets.live}
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
          disabled={!facets.live}
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
          disabled={!facets.live}
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
