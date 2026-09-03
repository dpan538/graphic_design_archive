"use client";

import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { matchGrade, type SearchResult } from "../lib/query";
import styles from "./SearchMobileResults.module.css";

const GRADE_LABEL = { perfect: "Perfect", partial: "Partial" } as const;

export default function SearchMobileResults({
  page,
  total,
  pageIndex,
  pageCount,
  onPage,
}: {
  page: SearchResult[];
  total: number;
  pageIndex: number;
  pageCount: number;
  onPage: (n: number) => void;
}) {
  if (total === 0) {
    return (
      <p className={styles.empty}>
        No public object matches. Try fewer terms or a wider year range.
      </p>
    );
  }

  return (
    <div className={styles.wrap}>
      <ol className={styles.list} role="list">
        {page.map(({ record: r, reason }) => (
          <li className={styles.row} key={r.id}>
            <div className={styles.head}>
              <Link className={styles.title} href={`/surfaces/${r.id}`}>
                {r.title}
              </Link>
              <span className={styles.chip} data-grade={matchGrade(reason)}>
                {GRADE_LABEL[matchGrade(reason)]}
              </span>
            </div>
            <p className={styles.meta}>
              {[r.credited ?? "Credit not recorded", r.displayDate, r.place, r.objectType]
                .filter(Boolean)
                .join("  ·  ")}
            </p>
          </li>
        ))}
      </ol>

      {pageCount > 1 ? (
        <div className={styles.pager}>
          <button type="button" disabled={pageIndex === 0} onClick={() => onPage(pageIndex - 1)}>
            <ChevronLeft size={15} strokeWidth={3} aria-hidden="true" /> Prev
          </button>
          <span>
            {pageIndex + 1} / {pageCount}
          </span>
          <button
            type="button"
            disabled={pageIndex + 1 >= pageCount}
            onClick={() => onPage(pageIndex + 1)}
          >
            Next <ChevronRight size={15} strokeWidth={3} aria-hidden="true" />
          </button>
        </div>
      ) : null}
    </div>
  );
}
