"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { SlidersHorizontal } from "lucide-react";
import SiteNavMobile from "@/components/site/mobile/SiteNavMobile";
import shell from "@/components/site/mobile/MobileShell.module.css";
import {
  defaultState,
  FALLBACK_BOUNDS,
  filterRecords,
  groupByYear,
  isPristine,
  PAGE,
  summarize,
  type FilterState,
} from "../lib/filter";
import { fetchCatalogue, type Catalogue } from "../lib/catalogue";
import IndexMobileSheet from "./IndexMobileFilters";
import IndexMobileDirectory from "./IndexMobileDirectory";
import styles from "./IndexMobile.module.css";

/* Mobile Index (390px baseline). The reader lands on the list; one control row
   carries Filter · slice · count. The filter set is a bottom sheet whose
   sections are collapsed by default, so it opens short. */
export default function IndexMobile() {
  const [cat, setCat] = useState<Catalogue | null>(null);
  const [state, setState] = useState<FilterState | null>(null);
  const [sheet, setSheet] = useState(false);
  const [failed, setFailed] = useState(false);
  const [shown, setShown] = useState(PAGE);

  const load = useCallback(() => {
    setFailed(false);
    fetchCatalogue()
      .then((c) => {
        setCat(c);
        setState((s) => s ?? defaultState(c));
      })
      .catch(() => setFailed(true));
  }, []);
  useEffect(() => load(), [load]);

  const bounds = cat ?? FALLBACK_BOUNDS;
  const active = state ?? defaultState(bounds);
  const rows = useMemo(() => (cat && state ? filterRecords(cat.records, state) : []), [cat, state]);
  const groups = useMemo(() => groupByYear(rows.slice(0, shown)), [rows, shown]);
  useEffect(() => setShown(PAGE), [state]);
  const pristine = isPristine(active, bounds);
  const sum = summarize(active, bounds);
  const activeCount =
    (active.place ? 1 : 0) +
    (active.yearFrom > bounds.yearMin || active.yearTo < bounds.yearMax ? 1 : 0) +
    active.themes.length +
    (active.visual !== "all" ? 1 : 0);

  const patch = (p: Partial<FilterState>) => setState((s) => ({ ...(s ?? defaultState(bounds)), ...p }));
  const reset = () => setState(defaultState(bounds));

  return (
    <div className={`${shell.shell} ${styles.page}`}>
      <a href="#directory" className="skip-link">
        Skip to directory
      </a>
      <SiteNavMobile active="index" />

      {/* the opening: one plate — the kicker, the count as a cropped numeral, the population line; no annotation */}
      <header className={styles.opening}>
        <h1 className={styles.kicker}>Index</h1>
        <span className={styles.openingNum} aria-hidden="true">{cat ? cat.count.toLocaleString() : ""}</span>
        <p className={styles.openingLine}>
          {cat ? (
            <>
              <b>{cat.count.toLocaleString()}</b> reader-facing objects · of {cat.publicCount.toLocaleString()} public records
            </>
          ) : failed ? "The directory couldn’t load." : "Loading the directory…"}
        </p>
      </header>
      <span className={styles.stripe} aria-hidden="true">
        <span />
        <span />
        <span />
      </span>

      <div className={styles.control}>
        <button
          type="button"
          className={styles.filterBtn}
          aria-expanded={sheet}
          onClick={() => setSheet(true)}
        >
          <SlidersHorizontal size={16} strokeWidth={3} aria-hidden="true" />
          Filter
          {activeCount > 0 ? <span className={styles.n}>{activeCount}</span> : null}
        </button>
        <span className={styles.slice}>
          {sum.region} · {sum.years} · {sum.themes} · {sum.visual}
        </span>
        <span className={styles.right}>
          <span className={styles.cnt}>{String(rows.length).padStart(3, "0")}</span>
          {!pristine ? (
            <button type="button" className={styles.reset} onClick={reset}>
              Reset
            </button>
          ) : null}
        </span>
      </div>

      <IndexMobileDirectory
        groups={groups}
        total={rows.length}
        pristine={pristine}
        onReset={reset}
        shown={Math.min(shown, rows.length)}
        onMore={() => setShown((n) => n + PAGE)}
        loading={!cat && !failed}
        failed={failed}
        onRetry={load}
      />

      <IndexMobileSheet
        open={sheet}
        state={active}
        patch={patch}
        count={rows.length}
        bounds={bounds}
        places={cat?.places ?? []}
        themes={cat?.themes ?? []}
        onClose={() => setSheet(false)}
      />
    </div>
  );
}
