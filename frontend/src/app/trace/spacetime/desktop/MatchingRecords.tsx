"use client";

import Link from "next/link";
import type { PublicSpacetimeRecordPage, PublicSpacetimeRecordSummary } from "@/features/trace-v49/spacetime/governed/types";
import {
  LOADING_RECORDS,
  LOAD_MORE,
  MATCHING_COUNT,
  MATCHING_OF,
  OPEN_RECORD,
  RECORDS_FAILED,
  RETRY,
} from "../lib/content";
import styles from "./MatchingRecords.module.css";

/* 05 — the matching records (§7h): the map's evidence — the public
   records of the selected period and geography, in the read API's
   order, twenty-five a page with Load more. Title, recorded date,
   stable ID, the object page. Nothing ranked, related or recommended. */

export interface MatchingRecordsProps {
  readonly geographyLabel: string;
  readonly periodLabel: string;
  readonly state: "idle" | "loading" | "ready" | "error";
  readonly records: readonly PublicSpacetimeRecordSummary[];
  readonly page: PublicSpacetimeRecordPage | null;
  readonly onLoadMore: () => void;
  readonly onRetry: () => void;
}

export default function MatchingRecords({ geographyLabel, periodLabel, state, records, page, onLoadMore, onRetry }: MatchingRecordsProps) {
  return (
    <section id="spacetime-matching-records" className={styles.records} aria-labelledby="matching-records-heading" aria-busy={state === "loading" || undefined} tabIndex={-1}>
      <div className={styles.head}>
        <h2 id="matching-records-heading" className={styles.scope}>{MATCHING_OF(geographyLabel, periodLabel)}</h2>
        {page ? <p className={`${styles.count} tnum`}>{MATCHING_COUNT(page.totalCount)}</p> : null}
      </div>
      {state === "error" ? (
        <p role="alert" className={styles.note}>
          {RECORDS_FAILED} <button type="button" className={styles.more} onClick={onRetry}>{RETRY}</button>
        </p>
      ) : state === "loading" && records.length === 0 ? (
        <p role="status" className={styles.note}>{LOADING_RECORDS}</p>
      ) : (
        <ol className={styles.list}>
          {records.map((record) => (
            <li key={record.stableId} className={styles.item}>
              <Link className={styles.title} href={`/surfaces/${encodeURIComponent(record.stableId)}`}>{record.title.trim() || record.stableId}</Link>
              <span className={`${styles.meta} tnum`}>{record.time.sourceDisplay} · {record.stableId}</span>
              <span className={styles.open} aria-hidden="true">{OPEN_RECORD} ↗</span>
            </li>
          ))}
        </ol>
      )}
      {page?.pageInfo.hasNextPage && state !== "error" ? (
        <button type="button" className={styles.more} onClick={onLoadMore} disabled={state === "loading"}>
          {state === "loading" ? LOADING_RECORDS : LOAD_MORE}
        </button>
      ) : null}
    </section>
  );
}
