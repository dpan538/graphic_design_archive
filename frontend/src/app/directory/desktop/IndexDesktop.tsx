"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import SiteNav from "@/components/site/SiteNav";
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
import { themeInk } from "../lib/palette";
import IndexControlBar from "./IndexControlBar";
import IndexFilterDrawer from "./IndexFilterDrawer";
import IndexDirectory, { type DirectoryStatus } from "./IndexDirectory";
import styles from "./IndexDesktop.module.css";

/* Index = browse / scan / compare (Search is a separate surface). The reader
   sees the filing directory first; filtering is a deliberate second act behind
   the drawer. Colour follows the archived folder-ink system (region blue, theme
   green, medium red, movement violet). */
export default function IndexDesktop() {
  const [cat, setCat] = useState<Catalogue | null>(null);
  const [state, setState] = useState<FilterState | null>(null);
  const [drawer, setDrawer] = useState(false);
  const [status, setStatus] = useState<DirectoryStatus>("loading");
  const [shown, setShown] = useState(PAGE);

  const load = useCallback(() => {
    setStatus("loading");
    fetchCatalogue()
      .then((c) => {
        setCat(c);
        setState((s) => s ?? defaultState(c));
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, []);

  useEffect(() => {
    /* ?state=loading|error holds a state for design review */
    const s = new URLSearchParams(window.location.search).get("state");
    if (s === "loading") return;
    if (s === "error") {
      setStatus("error");
      return;
    }
    load();
  }, [load]);

  const bounds = cat ?? FALLBACK_BOUNDS;
  const active = state ?? defaultState(bounds);
  const rows = useMemo(() => (cat && state ? filterRecords(cat.records, state) : []), [cat, state]);
  const groups = useMemo(() => groupByYear(rows.slice(0, shown)), [rows, shown]);
  useEffect(() => setShown(PAGE), [state]);
  const pristine = isPristine(active, bounds);
  const activeCount =
    (active.place ? 1 : 0) +
    (active.yearFrom > bounds.yearMin || active.yearTo < bounds.yearMax ? 1 : 0) +
    active.themes.length +
    (active.visual !== "all" ? 1 : 0);

  const patch = (p: Partial<FilterState>) => setState((s) => ({ ...(s ?? defaultState(bounds)), ...p }));
  const reset = () => setState(defaultState(bounds));
  const themes = cat?.themes ?? [];

  return (
    <div className={styles.page}>
      <a href="#directory" className="skip-link">
        Skip to directory
      </a>
      <SiteNav active="index" />

      <header className={styles.mast}>
        <div className={styles.mastInner}>
          <div className={styles.mastText}>
            <h1 className={styles.kicker}>Index</h1>
            <p className={styles.lede}>
              The archive as a working directory — every public record, filed by
              where it was made, when, and what it is about.
            </p>
            <p className={styles.intro}>
              <b>{(cat?.count ?? 5423).toLocaleString()}</b> reader-facing objects, of{" "}
              {(cat?.publicCount ?? 7995).toLocaleString()} public records. Open the filter to
              narrow by place, year or theme; the list holds year order. Select a
              title to open its record.
            </p>
            <p className={styles.note}>
              Record-only entries stay reachable by their ID. Places are filed as
              recorded at source; structured geography is still being verified.
            </p>
          </div>

          <details className={styles.legend} open>
            <summary className={styles.legendHead}>
              Theme key
              <span className={styles.legendNote}>A row ends in up to three theme dots. Hover a dot for its name.</span>
            </summary>
            <ul className={styles.legendList} role="list">
              {themes.map((t) => (
                <li key={t}>
                  <span
                    className={styles.legendDot}
                    style={{ background: themeInk(t) }}
                    aria-hidden="true"
                  />
                  {t}
                </li>
              ))}
            </ul>
          </details>
        </div>
        <div className={styles.stripe} aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
      </header>

      <IndexControlBar
        summary={summarize(active, bounds)}
        count={rows.length}
        pristine={pristine}
        filtersOpen={drawer}
        activeCount={activeCount}
        onOpenFilters={() => setDrawer(true)}
        onReset={reset}
      />

      <IndexDirectory
        groups={groups}
        total={rows.length}
        pristine={pristine}
        onReset={reset}
        status={status}
        onRetry={load}
        shown={Math.min(shown, rows.length)}
        onMore={() => setShown((n) => n + PAGE)}
      />

      <IndexFilterDrawer
        open={drawer}
        state={active}
        patch={patch}
        count={rows.length}
        total={cat?.count ?? 0}
        bounds={bounds}
        places={cat?.places ?? []}
        themes={themes}
        onClose={() => setDrawer(false)}
      />
    </div>
  );
}
