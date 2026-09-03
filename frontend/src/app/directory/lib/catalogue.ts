/* Index catalogue — the sealed v49 public projection's READER-FACING objects
   (reader-eligibility projection; record-only entries are reachable by ID).
   Built on the server from the governed Search v2 artifact (the same 7,995
   documents the Search API serves, release-bound and checksummed) and sent
   to the directory as one compact payload; decoded here into the rows the
   directory files. Client-safe: types, the decoder, and the fetch. */

export type IndexRecord = {
  id: string;
  n: number;
  year: number;
  yearEnd: number;
  title: string;
  designer: string | null;
  place: string;
  type: string;
  themes: string[];
  movement: string | null;
  source: string;
  date: string;
  /* visual access, from the release's delivery state (interim, §3c):
     source = viewable at the holding source · remote = remote visual
     candidate · citation = citation or link only */
  visual: VisualAccess;
};

export type VisualAccess = "source" | "remote" | "citation";

export type CatalogueBounds = { yearMin: number; yearMax: number };

export type Catalogue = CatalogueBounds & {
  releaseId: string;
  /* reader-facing objects (the Index's population) */
  count: number;
  /* every public record of the release, and how many are record-only */
  publicCount: number;
  recordOnlyCount: number;
  themes: string[];
  places: string[];
  records: IndexRecord[];
};

/* one row per record: [id, yearStart, yearEnd, title, credited, placeIdx,
   type, themeIdxs, movement, sourceIdx, displayDate, visual] */
export type CatalogueRow = readonly [
  string,
  number,
  number,
  string,
  string | null,
  number,
  string,
  readonly number[],
  string | null,
  number,
  string,
  VisualAccess,
];

export type CataloguePayload = {
  format: "gda-index-catalogue/v1";
  releaseId: string;
  count: number;
  publicCount: number;
  recordOnlyCount: number;
  yearMin: number;
  yearMax: number;
  themes: string[];
  places: string[];
  sources: string[];
  rows: CatalogueRow[];
};

export const CATALOGUE_URL = "/api/index/v1";

export function decodeCatalogue(p: CataloguePayload): Catalogue {
  if (p.format !== "gda-index-catalogue/v1" || p.rows.length !== p.count) {
    throw new Error("index catalogue payload failed its format or count check");
  }
  const records: IndexRecord[] = p.rows.map((r, i) => ({
    id: r[0],
    n: i + 1,
    year: r[1],
    yearEnd: r[2],
    title: r[3],
    designer: r[4],
    place: p.places[r[5]] ?? "",
    type: r[6],
    themes: r[7].map((t) => p.themes[t]).filter((t): t is string => typeof t === "string"),
    movement: r[8],
    source: p.sources[r[9]] ?? "",
    date: r[10],
    visual: r[11],
  }));
  return {
    releaseId: p.releaseId,
    count: p.count,
    publicCount: p.publicCount,
    recordOnlyCount: p.recordOnlyCount,
    yearMin: p.yearMin,
    yearMax: p.yearMax,
    themes: p.themes,
    places: p.places,
    records,
  };
}

export async function fetchCatalogue(signal?: AbortSignal): Promise<Catalogue> {
  const res = await fetch(CATALOGUE_URL, { signal });
  if (!res.ok) throw new Error(`index catalogue: HTTP ${res.status}`);
  return decodeCatalogue((await res.json()) as CataloguePayload);
}
