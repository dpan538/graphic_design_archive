/* Shared data contract for 04 · Research Status. Every figure on the page is
   derived from this one frozen per-record dataset (v49). */
import data from "@/data/status-v49.json";

export type StatusObject = [
  year: number,
  place: number, // index into `ledger`
  tier: number, // 0 public (source_verified), 1 metadata_supported, 2 missing
  rights: number, // 0 viewer, 1 open, 2 review, 3 thumbnail, 4 other
  completeness: number,
  source: number, // 0–24 top sources, 25 other
  type: number, // 0–24 top types, 25 other
  span: number,
];
export type StatusData = {
  meta: { objects: number; sha256: string; sources: number; types: number; rights: number[] };
  bands: { place: string; total: number; public: number }[];
  sources: { name: string; count: number }[];
  types: { name: string; count: number }[];
  ledger: { place: string; total: number; public: number }[];
  objects: StatusObject[];
};
/* The JSON's `objects` is typed number[][] by the importer; the tuple shape
   is enforced by the extraction script, not inferable here. */
export const STATUS: StatusData = data as unknown as StatusData;

/* Height compression shared by the panorama: y ∝ records^EXP, so the 1965
   bulk capture does not flatten every other year. */
export const EXP = 0.6;
