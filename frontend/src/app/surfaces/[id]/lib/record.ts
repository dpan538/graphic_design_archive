/* Shared, non-visual record helpers — the only code the desktop/ and mobile/
   trees have in common (besides fixture.ts + fitLayout.ts). Pure functions and
   types; no JSX, no styles. */

import {
  DESCRIPTION_LONG,
  DESCRIPTION_SHORT,
  DESCRIPTION_XLONG,
  type DeliveryState,
  type ObjectRecord as Rec,
} from "./fixture";

export type { Rec };
export type Ratio = "portrait" | "landscape" | "square";
export type DescLen = "xlong" | "long" | "short" | "none";
export type LayoutId = 1 | 2 | 3 | 4 | 5;

export const hasImage = (d: DeliveryState) => d === "REMOTE_IMAGE";

export const RATIO_LABEL: Record<Ratio, string> = {
  portrait: "Portrait (2:3)",
  landscape: "Landscape (3:2)",
  square: "Square (1:1)",
};

export const descText = (len: DescLen): string | null =>
  len === "none"
    ? null
    : len === "short"
      ? DESCRIPTION_SHORT
      : len === "xlong"
        ? DESCRIPTION_XLONG
        : DESCRIPTION_LONG;

export const creditString = (rec: Rec) =>
  rec.creditedLabels.length ? rec.creditedLabels.join(", ") : "";

export const yearString = (rec: Rec) =>
  rec.year == null
    ? null
    : rec.yearEnd && rec.yearEnd !== rec.year
      ? `${rec.year}–${rec.yearEnd}`
      : String(rec.year);

export const altString = (rec: Rec) => {
  const c = creditString(rec);
  return `${rec.title}. ${rec.typeLabel}, ${rec.displayDate}, ${rec.placeLabel}${
    c ? ", " + c : ""
  }.`;
};

export const buildCitation = (rec: Rec) => {
  const c = creditString(rec);
  return `Modern Graphic Design Archive. “${rec.title}”${c ? ", " + c : ""}, ${
    rec.displayDate
  }. ${rec.placeLabel}. ${rec.typeLabel}. Record ${
    rec.surfaceId
  }. https://mgdarchive.com/surfaces/${rec.surfaceId}`;
};

export type Row = [string, string | null];

export function rowsFor(rec: Rec): {
  identity: Row[];
  classification: Row[];
  source: Row[];
} {
  return {
    identity: [
      ["Designer / studio", creditString(rec) || null],
      ["Date", rec.displayDate || null],
      ["Year", yearString(rec)],
      ["Place", rec.placeLabel || null],
      ["Medium", rec.mediumLabel || null],
      ["Object type", rec.typeLabel || null],
    ],
    classification: [
      ["Theme", rec.themes.join(" · ") || null],
      ["Movement", rec.movements.join(" · ") || null],
    ],
    source: [
      ["Source institution", rec.sourceRecord.institution],
      ["Original record", rec.sourceRecord.recordTitle],
      ["Source record URL", rec.sourceRecord.recordHref || null],
      ["Access", rec.sourceRecord.accessedText],
      ["Record status", rec.provenance.recordStatus],
      ["Release", rec.provenance.releaseLabel],
      ["Source verification", rec.provenance.sourceVerification],
      ["Last verified", rec.provenance.lastVerified],
    ],
  };
}
