/* Index — pure filter / sort / summary. No React, no styles. Shared by the
   desktop and mobile trees. Records and year bounds come from the catalogue
   (lib/catalogue.ts); nothing here holds data of its own. */

import type { CatalogueBounds, IndexRecord, VisualAccess } from "./catalogue";

export type Order = "oldest" | "newest";

export type FilterState = {
  /* the place label as recorded at source (structured geography is still
     being verified — FRONTEND_DESIGN_DECISION.md §3); null = all places */
  place: string | null;
  yearFrom: number;
  yearTo: number;
  themes: string[]; // empty = all themes
  /* visual access (interim labels, §3c); "all" = no filter */
  visual: VisualAccess | "all";
  order: Order;
};

export const VISUAL_OPTIONS: [VisualAccess | "all", string][] = [
  ["all", "All"],
  ["source", "Viewable at source"],
  ["remote", "Remote visual candidate"],
  ["citation", "Citation / link only"],
];
export const visualLabel = (v: VisualAccess | "all") => VISUAL_OPTIONS.find(([k]) => k === v)?.[1] ?? "All";

export const FALLBACK_BOUNDS: CatalogueBounds = { yearMin: 1800, yearMax: 2026 };

export function defaultState(b: CatalogueBounds): FilterState {
  return { place: null, yearFrom: b.yearMin, yearTo: b.yearMax, themes: [], visual: "all", order: "oldest" };
}

export function isPristine(s: FilterState, b: CatalogueBounds): boolean {
  return s.place === null && s.yearFrom <= b.yearMin && s.yearTo >= b.yearMax && s.themes.length === 0 && s.visual === "all";
}

export function filterRecords(records: readonly IndexRecord[], s: FilterState): IndexRecord[] {
  const rows = records.filter((r) => {
    if (s.place && r.place !== s.place) return false;
    if (r.year < s.yearFrom || r.year > s.yearTo) return false;
    if (s.themes.length && !s.themes.some((t) => r.themes.includes(t))) return false;
    if (s.visual !== "all" && r.visual !== s.visual) return false;
    return true;
  });
  rows.sort((a, b) =>
    s.order === "oldest" ? a.year - b.year || a.title.localeCompare(b.title) : b.year - a.year || a.title.localeCompare(b.title),
  );
  return rows;
}

export type YearGroup = { year: number; rows: IndexRecord[] };

/** Group the (already sorted) rows by year, preserving order. */
export function groupByYear(rows: IndexRecord[]): YearGroup[] {
  const out: YearGroup[] = [];
  for (const r of rows) {
    const last = out[out.length - 1];
    if (last && last.year === r.year) last.rows.push(r);
    else out.push({ year: r.year, rows: [r] });
  }
  return out;
}

/** Editorial summary segments for the active-state line. */
export function summarize(s: FilterState, b: CatalogueBounds): { region: string; years: string; themes: string; visual: string } {
  return {
    region: s.place ?? "All places",
    years: s.yearFrom <= b.yearMin && s.yearTo >= b.yearMax ? "All years" : `${s.yearFrom}–${s.yearTo}`,
    themes: s.themes.length ? s.themes.join(", ") : "All themes",
    visual: s.visual === "all" ? "All visual access" : visualLabel(s.visual),
  };
}

/* year controls, derived from the catalogue's bounds */
export const decadesFor = (b: CatalogueBounds) =>
  Array.from({ length: Math.floor(b.yearMax / 10) - Math.floor(b.yearMin / 10) + 1 }, (_, i) => (Math.floor(b.yearMin / 10) + i) * 10);

export const erasFor = (b: CatalogueBounds): [string, number, number][] => [
  ["Before 1945", b.yearMin, 1944],
  ["1945–1979", 1945, 1979],
  ["1980–present", 1980, b.yearMax],
];

export const clampYearTo = (b: CatalogueBounds, n: number) => Math.min(b.yearMax, Math.max(b.yearMin, Math.round(n) || b.yearMin));

/* rows are filed in pages of this many, with a "show more" at the foot */
export const PAGE = 200;
