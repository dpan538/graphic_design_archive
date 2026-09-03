/* Content-fit layout — deterministic column assignment by content volume.
 *
 * The Object Page runs its parallel blocks (identity metadata grid, description
 * prose) at a column count chosen from how much content the record actually
 * carries: a sparse record is not stretched across four thin columns, and a
 * dense one is not crammed into one. The mapping is a pure function of the
 * record — the same record always resolves to the same layout. It never
 * measures the rendered DOM and never depends on viewport width; the plain
 * responsive breakpoints in object.module.css narrow these counts on small
 * screens, but the *content* decision is made here.
 */

import type { ObjectRecord } from "./fixture";

export type FitProfile = {
  /** identity metadata grid — 2 or 3 in practice (identity carries ≤ 6 fields) */
  metaCols: 2 | 3 | 4;
  /** running description text — 1 (single measure) to 4 */
  proseCols: 1 | 2 | 3 | 4;
  /** overall density hint; drives section spacing, not column count */
  density: "compact" | "regular" | "dense";
};

const len = (t: string | null | undefined) => (t ? t.trim().length : 0);

/** Identity fields that carry a value. Empty fields are omitted from the grid,
 *  not shown as "Not recorded", so the count reflects rendered cells. */
export function populatedIdentityCount(rec: ObjectRecord): number {
  const credited = rec.creditedLabels.length > 0 ? 1 : 0;
  const rest = [
    rec.displayDate,
    rec.year,
    rec.placeLabel,
    rec.mediumLabel,
    rec.typeLabel,
  ].filter((v) => v !== null && v !== undefined && String(v).trim() !== "").length;
  return credited + rest;
}

/** Columns for the identity grid. Identity has at most six fields, so the
 *  four-column branch only applies if the record model later grows; the guard
 *  keeps the mapping honest instead of producing a ragged 4 + 2 grid today. */
export function metaColumns(fieldCount: number): 2 | 3 | 4 {
  if (fieldCount >= 9) return 4;
  if (fieldCount >= 5) return 3;
  return 2;
}

/** Columns for running description text, by character length. Thresholds keep
 *  every column at roughly six or more lines within the 66rem frame, so no
 *  column degrades toward one word per line. */
export function proseColumns(text: string | null | undefined): 1 | 2 | 3 | 4 {
  const n = len(text);
  if (n >= 900) return 4;
  if (n >= 480) return 3;
  if (n >= 240) return 2;
  return 1;
}

/** One call for the whole record. `descOverride` lets a caller pass an already
 *  resolved description string (e.g. a short/long variant) instead of
 *  `rec.description`. */
export function fitProfile(
  rec: ObjectRecord,
  descOverride?: string | null,
): FitProfile {
  const fields = populatedIdentityCount(rec);
  const desc = descOverride === undefined ? rec.description : descOverride;
  const score = fields + Math.ceil(len(desc) / 120);
  return {
    metaCols: metaColumns(fields),
    proseCols: proseColumns(desc),
    density: score >= 11 ? "dense" : score >= 6 ? "regular" : "compact",
  };
}
