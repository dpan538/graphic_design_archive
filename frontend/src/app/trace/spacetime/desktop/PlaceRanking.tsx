"use client";

import type { SpacetimeRankedRow } from "@/features/trace-v49/spacetime/map";
import { NOT_PLOTTED_HINT, NOT_PLOTTED_MARK, RANKING_COLUMNS, RANKING_NOTE, SHARE_SHORT } from "../lib/content";
import styles from "./PlaceRanking.module.css";

/* 05 — the place ranking (§7h): the period's recorded geographies by
   records — Place · Records · Share of period · Rank — the map's equal
   as a table a researcher reads. A place without a safe map position
   carries a light "Not plotted" mark, its reason on hover; the mapping
   state is not a column. A row chosen is the place chosen: a mapped
   one focuses the map as well; the rest open the profile and the
   records and leave the map alone. */

export interface PlaceRankingProps {
  readonly rows: readonly SpacetimeRankedRow[];
  readonly selectedGeographyId: string | null;
  readonly busy: boolean;
  readonly onSelect: (geographyId: string) => void;
}

export default function PlaceRanking({ rows, selectedGeographyId, busy, onSelect }: PlaceRankingProps) {
  return (
    <section id="spacetime-place-ranking" className={styles.table} aria-labelledby="place-ranking-heading" tabIndex={-1}>
      <h2 id="place-ranking-heading" className={styles.note}>{RANKING_NOTE}</h2>
      <table className={styles.grid}>
        <thead>
          <tr>
            <th scope="col" className={styles.number}>{RANKING_COLUMNS.rank}</th>
            <th scope="col">{RANKING_COLUMNS.place}</th>
            <th scope="col" className={styles.number}>{RANKING_COLUMNS.records}</th>
            <th scope="col" className={styles.number}>{RANKING_COLUMNS.share}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ row, rank, share }) => {
            const selected = row.geographyId === selectedGeographyId;
            return (
              <tr key={row.id} data-selected={selected || undefined} data-state={row.mappingState}>
                <td className={`${styles.number} ${styles.rank} tnum`}>{rank}</td>
                <th scope="row">
                  <button
                    type="button"
                    className={styles.choose}
                    aria-pressed={selected}
                    disabled={busy}
                    onClick={() => onSelect(row.geographyId)}
                  >
                    {row.label}
                  </button>
                  {row.mappingState !== "mapped" ? (
                    <span className={styles.unplotted} title={NOT_PLOTTED_HINT}>{NOT_PLOTTED_MARK}</span>
                  ) : null}
                </th>
                <td className={`${styles.number} tnum`}>{row.recordCount.toLocaleString("en-US")}</td>
                <td className={`${styles.number} tnum`}>{SHARE_SHORT(share)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
