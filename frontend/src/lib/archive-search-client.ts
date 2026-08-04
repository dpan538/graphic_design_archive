import type { ImageState, SurfaceKind } from "@/types/archive";

export interface ArchiveSearchSurface {
  surfaceId: string;
  title: string;
  creator: string;
  dateText: string;
  dateStart: number | null;
  placeText: string;
  objectType: string;
  medium: string;
  sourceName: string;
  surfaceType: SurfaceKind;
  image: { state: ImageState };
}

export interface ArchiveSearchResult {
  surface: ArchiveSearchSurface;
  score: number;
  field: string;
  snippet: string;
}

interface ArchiveSearchRecord extends ArchiveSearchSurface {
  folderText: string;
  tableText: string;
}

interface ArchiveSearchPayload {
  version: string;
  count: number;
  schema: string[];
  items: unknown[][];
}

let indexPromise: Promise<ArchiveSearchRecord[]> | null = null;

function decode(payload: ArchiveSearchPayload): ArchiveSearchRecord[] {
  const position = new Map(payload.schema.map((field, index) => [field, index]));
  const at = (values: unknown[], field: string) => values[position.get(field) ?? -1];
  return payload.items.map((values) => ({
    surfaceId: String(at(values, "surfaceId") ?? ""),
    title: String(at(values, "title") ?? ""),
    creator: String(at(values, "creator") ?? ""),
    dateText: String(at(values, "dateText") ?? ""),
    dateStart: at(values, "dateStart") == null ? null : Number(at(values, "dateStart")),
    placeText: String(at(values, "placeText") ?? ""),
    objectType: String(at(values, "objectType") ?? ""),
    medium: String(at(values, "medium") ?? ""),
    sourceName: String(at(values, "sourceName") ?? ""),
    surfaceType: String(at(values, "surfaceType") ?? "fallback_stub") as SurfaceKind,
    image: { state: String(at(values, "imageState") ?? "IMG00") as ImageState },
    folderText: String(at(values, "folderText") ?? ""),
    tableText: String(at(values, "tableText") ?? ""),
  }));
}

export function loadArchiveSearchIndex() {
  if (!indexPromise) {
    indexPromise = fetch("/data/archive-search-v1.json")
      .then((response) => {
        if (!response.ok) throw new Error(`Archive search index unavailable (${response.status})`);
        return response.json() as Promise<ArchiveSearchPayload>;
      })
      .then((payload) => {
        const records = decode(payload);
        if (records.length !== payload.count) throw new Error("Archive search index count mismatch");
        return records;
      });
  }
  return indexPromise;
}

function normalizedSearchText(value: string) {
  return value.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").replace(/\s+/g, " ").trim();
}

function termScore(text: string, term: string) {
  const lowered = text.toLowerCase();
  const tokens = normalizedSearchText(text).split(" ").filter(Boolean);
  const index = lowered.indexOf(term);
  if (index !== -1) {
    const wordBonus = tokens.some((token) => token === term)
      ? 40
      : tokens.some((token) => token.startsWith(term)) ? 18 : 0;
    return 120 - Math.min(index, 40) + (index === 0 ? 20 : 0) + wordBonus;
  }
  if (term.length < 4) return 0;
  if (tokens.some((token) => token.startsWith(term))) return 84;
  if (term.length < 5) return 0;
  for (const token of tokens) {
    let matched = 0;
    for (let index = 0; index < token.length && matched < term.length; index += 1) {
      if (token[index] === term[matched]) matched += 1;
    }
    if (matched === term.length) return 26;
  }
  return 0;
}

function makeSnippet(value: string, query: string) {
  const compact = value.replace(/\s+/g, " ").trim();
  if (compact.length <= 118) return compact;
  const index = compact.toLowerCase().indexOf(query.toLowerCase());
  const start = Math.max(0, index < 0 ? 0 : index - 38);
  return `${start ? "…" : ""}${compact.slice(start, start + 116)}${start + 116 < compact.length ? "…" : ""}`;
}

export async function searchArchiveSurfaces(query: string, limit = 18): Promise<ArchiveSearchResult[]> {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return [];
  const terms = normalized.split(/\s+/).filter(Boolean);
  if (terms.some((term) => term.length < 2)) return [];
  const records = await loadArchiveSearchIndex();
  const results: ArchiveSearchResult[] = [];

  for (const surface of records) {
    const fields: Array<[string, string, number]> = [
      ["Title", surface.title, 2.2],
      ["Creator", surface.creator, 1.4],
      ["Date", surface.dateText, 1],
      ["Place", surface.placeText, 1],
      ["Object type", surface.objectType, 1.1],
      ["Medium", surface.medium, 1.1],
      ["Source", surface.sourceName, 1],
      ["Folder", surface.folderText, 1.2],
    ];
    if (normalized.length >= 4) fields.push(["Metadata", surface.tableText, 0.34]);

    let total = 0;
    let best: { score: number; field: string; value: string } | null = null;
    let matched = true;
    for (const term of terms) {
      let termBest = 0;
      for (const [field, value, weight] of fields) {
        if (!value) continue;
        const score = termScore(value, term) * weight;
        if (score > termBest) termBest = score;
        if (score > (best?.score ?? 0)) best = { score, field, value };
      }
      if (!termBest) {
        matched = false;
        break;
      }
      total += termBest;
    }
    if (!matched || !best || total < (terms.length === 1 ? 78 : 58 * terms.length)) continue;
    results.push({
      surface,
      score: total,
      field: best.field,
      snippet: makeSnippet(best.value, terms[0]),
    });
  }

  return results.sort((left, right) =>
    right.score - left.score
    || (left.surface.dateStart ?? Number.POSITIVE_INFINITY) - (right.surface.dateStart ?? Number.POSITIVE_INFINITY)
    || left.surface.surfaceId.localeCompare(right.surface.surfaceId),
  ).slice(0, limit);
}
