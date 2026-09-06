"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { SlidersHorizontal } from "lucide-react";
import SiteNavMobile from "@/components/site/mobile/SiteNavMobile";
import TopButton from "@/components/site/mobile/TopButton";
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
import { rememberDirectory, restoreDirectory } from "../lib/history";
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
        const restored = restoreDirectory(c);
        setState((s) => s ?? restored.state);
        setShown(restored.shown);
      })
      .catch(() => setFailed(true));
  }, []);
  useEffect(() => load(), [load]);

  const bounds = cat ?? FALLBACK_BOUNDS;
  const active = state ?? defaultState(bounds);
  const rows = useMemo(() => (cat && state ? filterRecords(cat.records, state) : []), [cat, state]);
  const groups = useMemo(() => groupByYear(rows.slice(0, shown)), [rows, shown]);
  useEffect(() => { if (cat && state) rememberDirectory(cat.releaseId, state, shown); }, [cat, state, shown]);
  const pristine = isPristine(active, bounds);
  const sum = summarize(active, bounds);
  const activeCount =
    (active.place ? 1 : 0) +
    (active.yearFrom > bounds.yearMin || active.yearTo < bounds.yearMax ? 1 : 0) +
    active.themes.length +
    (active.visual !== "all" ? 1 : 0);

  const patch = (p: Partial<FilterState>) => { setShown(PAGE); setState((s) => ({ ...(s ?? defaultState(bounds)), ...p })); };
  const reset = () => { setShown(PAGE); setState(defaultState(bounds)); };

  return (
    <div className={`${shell.shell} ${styles.page}`}>
      <a href="#directory" className="skip-link">
        Skip to directory
      </a>
      <SiteNavMobile active="index" />

      {/* the opening (owner, 2026-09-06): on the paper, twice the height of the
          old plate — the kicker, the readable count and the release total as two
          uncropped figures, and a guiding paragraph */}
      <header className={styles.opening}>
        <h1 className={styles.word}>Index</h1>
        {cat ? (
          <>
            {/* the two figures as one comparison: the readable share of the release */}
            <div className={styles.compare}>
              <p className={styles.figure}>
                <b className={styles.figureNum}>{cat.count.toLocaleString()}</b>
                <span className={styles.figureLabel}>reader-facing objects</span>
              </p>
              <p className={styles.figure} data-total="">
                <b className={styles.figureNum}>{cat.publicCount.toLocaleString()}</b>
                <span className={styles.figureLabel}>public records</span>
              </p>
              <span className={styles.share} aria-hidden="true">
                <i style={{ width: `${((cat.count / cat.publicCount) * 100).toFixed(1)}%` }} />
              </span>
            </div>
            <p className={styles.openingLine}>
              Browse the public archive by year, place, object type and theme. Each entry opens a record with its source and citation.
              The other {(cat.publicCount - cat.count).toLocaleString()} public records are catalogued but do not yet open as reader pages;
              every one stays reachable by its identifier.
            </p>
          </>
        ) : (
          <p className={styles.openingLine}>{failed ? "The directory couldn’t load." : "Loading the directory…"}</p>
        )}
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
      <TopButton />
    </div>
  );
}
