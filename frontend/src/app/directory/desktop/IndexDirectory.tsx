"use client";

import Link from "next/link";
import type { YearGroup } from "../lib/filter";
import { themeDots } from "../lib/palette";
import styles from "./IndexDirectory.module.css";

export type DirectoryStatus = "ready" | "loading" | "error";

/* 04 Object directory — a filing index. A running number, the year hung once per
   group, a dotted leader to the title (the only click target), the record line
   below, and up to three theme dots as a scan mark. */
export default function IndexDirectory({
  groups,
  total,
  pristine,
  onReset,
  status = "ready",
  onRetry,
  shown,
  onMore,
}: {
  groups: YearGroup[];
  total: number;
  pristine: boolean;
  onReset: () => void;
  status?: DirectoryStatus;
  onRetry?: () => void;
  /* rows are filed in pages; `shown` of `total` are on the page */
  shown?: number;
  onMore?: () => void;
}) {
  if (status === "loading") {
    return (
      <div className={styles.directory} id="directory" aria-busy="true">
        <p className={styles.state}>Loading directory…</p>
        <div className={styles.skeleton} aria-hidden="true">
          {Array.from({ length: 10 }).map((_, i) => (
            <span key={i} />
          ))}
        </div>
      </div>
    );
  }

  if (status === "error") {
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

  let n = 0;
  return (
    <div className={styles.directory} id="directory">
      {groups.map((g) => (
        <div className={styles.group} key={g.year}>
          <p className={styles.year}>
            {g.year}
            <span className={styles.yearN}>
              {g.rows.length} {g.rows.length === 1 ? "record" : "records"}
            </span>
          </p>
          <ol className={styles.rows} role="list">
            {g.rows.map((r) => {
              n += 1;
              const dots = themeDots(r);
              return (
                <li className={styles.row} key={r.id}>
                  <span className={styles.num}>{String(n).padStart(3, "0")}</span>
                  <div className={styles.entry}>
                    <p className={styles.line}>
                      <Link className={styles.title} href={`/surfaces/${r.id}`}>
                        {r.title}
                      </Link>
                      <span className={styles.leader} aria-hidden="true" />
                      <span
                        className={styles.dots}
                        role="img"
                        aria-label={
                          dots.length
                            ? `Themes: ${r.themes.join(", ")}`
                            : "No theme recorded"
                        }
                      >
                        {dots.map((d) => (
                          <span
                            key={d.theme}
                            className={styles.dot}
                            style={{ background: d.ink }}
                            title={d.theme}
                          />
                        ))}
                      </span>
                    </p>
                    <p className={styles.meta}>
                      {[r.designer ?? "Designer not recorded", r.place, r.type, r.date !== String(r.year) ? r.date : null]
                        .filter(Boolean)
                        .join("  ·  ")}
                    </p>
                  </div>
                </li>
              );
            })}
          </ol>
        </div>
      ))}
      {shown !== undefined && shown < total ? (
        <div className={styles.group}>
          <p className={styles.state}>
            {shown.toLocaleString()} of {total.toLocaleString()} records on the page.
          </p>
          <button type="button" className={styles.stateBtn} onClick={onMore}>
            Show the next {Math.min(200, total - shown)}
          </button>
        </div>
      ) : null}
    </div>
  );
}
