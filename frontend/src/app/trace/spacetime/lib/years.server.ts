import "server-only";
import data from "../../../../data/status-v49.json";

/* The period rail's columns (§7h): public records by recorded year,
   1800–2026, derived from the one frozen per-record status dataset of
   v49 (the homepage's Research status reads the same file) — tier 0 is
   a public record. The decade's own total stays the governed period's
   (INTERVAL_OVERLAP); the columns are the year-by-year texture under
   it. Nothing is typed in: the series is counted here and its total is
   checked against the projection's public cohort. */

export interface YearCount {
  readonly year: number;
  readonly count: number;
}

export const YEAR_FIRST = 1800;
export const YEAR_LAST = 2026;

type StatusRow = readonly number[];

export function publicRecordsByYear(expectedTotal: number): readonly YearCount[] {
  const rows = (data as unknown as { objects: readonly StatusRow[] }).objects;
  const counts = new Map<number, number>();
  let total = 0;
  for (const row of rows) {
    const year = row[0];
    const tier = row[2];
    if (tier !== 0) continue;
    if (!Number.isInteger(year) || year < YEAR_FIRST || year > YEAR_LAST) throw new Error("public record year outside the governed range");
    counts.set(year, (counts.get(year) ?? 0) + 1);
    total += 1;
  }
  if (total !== expectedTotal) throw new Error(`public records by year (${total}) differ from the projection's public cohort (${expectedTotal})`);
  return Object.freeze(Array.from({ length: YEAR_LAST - YEAR_FIRST + 1 }, (_, index) => Object.freeze({
    year: YEAR_FIRST + index,
    count: counts.get(YEAR_FIRST + index) ?? 0,
  })));
}
