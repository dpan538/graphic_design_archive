"use client";

import Link from "next/link";
import type { YearGroup } from "../lib/filter";
import styles from "./IndexMobileDirectory.module.css";

/* Mobile directory — pared to a reading list (ref: Vrints-Kolsteren, The Window
   Effect): no filing number, no dots. Year band → title (the link) → one plain
   line of themes · place · type. Same hierarchy as desktop, fewer marks. */
export default function IndexMobileDirectory({
  groups,
  total,
  pristine,
  onReset,
  shown,
  onMore,
  loading,
  failed,
  onRetry,
}: {
  groups: YearGroup[];
  total: number;
  pristine: boolean;
  onReset: () => void;
  shown?: number;
  onMore?: () => void;
  loading?: boolean;
  failed?: boolean;
  onRetry?: () => void;
}) {
  if (loading) {
    return (
      <div className={styles.directory} id="directory" aria-busy="true">
        <p className={styles.state}>Loading directory…</p>
      </div>
    );
  }
  if (failed) {
    return (
      <div className={styles.directory} id="directory" role="alert">
        <p className={styles.state}>The directory couldn’t load.</p>
        <button type="button" className={styles.stateBtn} onClick={onRetry}>
          Retry
        </button>
      </div>
    );
  }
  if (total === 0) {
    return (
      <div className={styles.directory} id="directory">
        <p className={styles.state}>No objects match this place, year and theme.</p>
        <p className={styles.stateHint}>Widen the year range or drop a filter.</p>
        {!pristine ? (
          <button type="button" className={styles.stateBtn} onClick={onReset}>
            Reset filters
          </button>
        ) : null}
      </div>
    );
  }

  return (
    <div className={styles.directory} id="directory">
      {groups.map((g) => (
        <section className={styles.group} key={g.year}>
          <h2 className={styles.year}>
            <span>{g.year}</span>
            <span className={styles.yearN}>
              {g.rows.length} {g.rows.length === 1 ? "record" : "records"}
            </span>
          </h2>
          <ol className={styles.rows} role="list">
            {g.rows.map((r) => (
              <li className={styles.row} key={r.id}>
                <Link className={styles.title} href={`/surfaces/${r.id}`}>
                  {r.title}
                </Link>
                <p className={styles.meta}>
                  {[
                    r.themes.join(", ") || null,
                    r.designer ?? "Designer not recorded",
                    r.place,
                    r.type,
                  ]
                    .filter(Boolean)
                    .join("  ·  ")}
                </p>
              </li>
            ))}
          </ol>
        </section>
      ))}
      {shown !== undefined && shown < total ? (
        <div className={styles.group}>
          <p className={styles.state}>
            {shown.toLocaleString()} of {total.toLocaleString()} records.
          </p>
          <button type="button" className={styles.stateBtn} onClick={onMore}>
            Show the next {Math.min(200, total - shown)}
          </button>
        </div>
      ) : null}
    </div>
  );
}
