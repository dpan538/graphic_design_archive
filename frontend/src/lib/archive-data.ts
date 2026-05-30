/**
 * Data layer over the static mock payload.
 *
 * Everything here reads from the imported mock JSON. There are no network
 * calls, no LLM calls, and no remote image loading. The frontend treats the
 * payload as the binding contract (see FRONTEND_FIELD_DECISIONS_v1.md).
 */

import mockRaw from "@/data/public_surface_mock_v0.json";
import type {
  Folder,
  FolderType,
  FolderTypeKey,
  ImageState,
  PublicSurfaceMock,
  Surface,
  SurfaceKind,
} from "@/types/archive";

const mock = mockRaw as unknown as PublicSurfaceMock;

export const FOLDER_TYPE_ORDER: FolderTypeKey[] = [
  "region",
  "theme",
  "medium",
  "movement",
];

export const IMG_STATES: ImageState[] = [
  "IMG00",
  "IMG01",
  "IMG02",
  "IMG03",
  "IMG04",
];

export function getMeta() {
  return mock.meta;
}

export function getFolderTypes(): FolderType[] {
  // Keep a stable, spec-defined order regardless of mock ordering.
  return [...mock.folderTypes].sort(
    (a, b) =>
      FOLDER_TYPE_ORDER.indexOf(a.type) - FOLDER_TYPE_ORDER.indexOf(b.type),
  );
}

export function getFolderType(type: string): FolderType | undefined {
  return mock.folderTypes.find((ft) => ft.type === type);
}

/**
 * Low-saturation archival inks, one per folder type. These replace the mock's
 * brighter hues for the museum/archive aesthetic. The mock colours remain in
 * the payload and are still surfaced (e.g. in the RIGHTS/CLASSIFICATION data).
 */
export const FOLDER_INK: Record<FolderTypeKey, string> = {
  region: "#2F5BEA",
  theme: "#33302b",
  medium: "#D94A38",
  movement: "#E2C044",
};

export function getFolderInk(type: string): string {
  return FOLDER_INK[type as FolderTypeKey] ?? "#1a1714";
}

/** Back-compat alias used by some components. */
export function getFolderColor(type: string): string {
  return getFolderInk(type);
}

export function isFolderTypeKey(value: string): value is FolderTypeKey {
  return (FOLDER_TYPE_ORDER as string[]).includes(value);
}

export function getFolders(): Folder[] {
  return mock.folders;
}

export function getFoldersByType(type: FolderTypeKey): Folder[] {
  return mock.folders
    .filter((f) => f.type === type)
    .sort((a, b) => a.title.localeCompare(b.title));
}

export function getFolder(
  type: string,
  slug: string,
): Folder | undefined {
  return mock.folders.find((f) => f.type === type && f.slug === slug);
}

export function getFolderById(folderId: string): Folder | undefined {
  return mock.folders.find((f) => f.folderId === folderId);
}

/** Resolve a route path for a folder id, or null if the folder is unknown. */
export function folderHref(folderId: string): string | null {
  const folder = getFolderById(folderId);
  return folder ? `/folders/${folder.type}/${folder.slug}` : null;
}

export function getSurfaces(): Surface[] {
  return mock.surfaces;
}

export function getSurface(id: string): Surface | undefined {
  return mock.surfaces.find((s) => s.surfaceId === id);
}

/** Surfaces that belong to a folder, resolved from the folder's surfaceIds. */
export function getSurfacesForFolder(folder: Folder): Surface[] {
  return folder.surfaceIds
    .map((id) => getSurface(id))
    .filter((s): s is Surface => Boolean(s));
}

// ---------------------------------------------------------------------------
// Chronology
// ---------------------------------------------------------------------------

export const UNDATED_KEY = "undated";
export const UNDATED_LABEL = "Undated / date under review";

/**
 * Chronological sort key per ARCHIVE_BOX_SYSTEM_SPEC time model:
 * earliest date, then latest date, then seq label. Undated sinks to the end.
 */
function sortKey(s: Surface): [number, number, string] {
  const start = s.dateStart ?? Number.POSITIVE_INFINITY;
  const end = s.dateEnd ?? Number.POSITIVE_INFINITY;
  return [start, end, s.seqLabel];
}

export function sortChronologically(surfaces: Surface[]): Surface[] {
  return [...surfaces].sort((a, b) => {
    const [as, ae, al] = sortKey(a);
    const [bs, be, bl] = sortKey(b);
    if (as !== bs) return as - bs;
    if (ae !== be) return ae - be;
    return al.localeCompare(bl);
  });
}

export function decadeKey(year: number | null): string {
  if (year === null || Number.isNaN(year)) return UNDATED_KEY;
  const decade = Math.floor(year / 10) * 10;
  return `${decade}s`;
}

export interface ChronologyGroup {
  key: string;
  label: string;
  /** Numeric sort hint; undated is pushed last. */
  order: number;
  surfaces: Surface[];
}

/**
 * Group chronologically sorted surfaces into decade buckets (1890s, 1910s,
 * ...) plus a trailing undated bucket.
 */
export function groupByDecade(surfaces: Surface[]): ChronologyGroup[] {
  const sorted = sortChronologically(surfaces);
  const groups = new Map<string, ChronologyGroup>();

  for (const surface of sorted) {
    const key = decadeKey(surface.dateStart);
    const existing = groups.get(key);
    if (existing) {
      existing.surfaces.push(surface);
      continue;
    }
    const isUndated = key === UNDATED_KEY;
    groups.set(key, {
      key,
      label: isUndated ? UNDATED_LABEL : key,
      order: isUndated ? Number.POSITIVE_INFINITY : surface.dateStart ?? 0,
      surfaces: [surface],
    });
  }

  return [...groups.values()].sort((a, b) => a.order - b.order);
}

export function dateSpanLabel(
  start: number | null,
  end: number | null,
): string {
  if (start === null && end === null) return UNDATED_LABEL;
  if (start !== null && end !== null) {
    return start === end ? `${start}` : `${start}–${end}`;
  }
  return `${start ?? end}`;
}

// ---------------------------------------------------------------------------
// Aggregation / counts
// ---------------------------------------------------------------------------

export interface SurfaceMix {
  sheet: number;
  card: number;
  fallback_stub: number;
}

export function surfaceMix(surfaces: Surface[]): SurfaceMix {
  const mix: SurfaceMix = { sheet: 0, card: 0, fallback_stub: 0 };
  for (const s of surfaces) {
    mix[s.surfaceType] = (mix[s.surfaceType] ?? 0) + 1;
  }
  return mix;
}

export type ImageDistribution = Record<ImageState, number>;

export function imageDistribution(surfaces: Surface[]): ImageDistribution {
  const dist: ImageDistribution = {
    IMG00: 0,
    IMG01: 0,
    IMG02: 0,
    IMG03: 0,
    IMG04: 0,
  };
  for (const s of surfaces) {
    dist[s.image.state] = (dist[s.image.state] ?? 0) + 1;
  }
  return dist;
}

/** Distinct source names across a surface set. */
export function sourceCount(surfaces: Surface[]): number {
  return new Set(surfaces.map((s) => s.sourceName)).size;
}

export interface GlobalCounts {
  folders: number;
  folderTypes: number;
  surfaces: number;
  sheets: number;
  cards: number;
  stubs: number;
  sources: number;
  imageReadySurfaces: number;
  imageCoveragePercent: number;
  imageCoverageHealthy: boolean;
  imageDistribution: ImageDistribution;
}

export function getGlobalCounts(): GlobalCounts {
  const surfaces = getSurfaces();
  const mix = surfaceMix(surfaces);
  const imageReadySurfaces = surfaces.filter((s) =>
    ["IMG01", "IMG02", "IMG03"].includes(s.image.state),
  ).length;
  const imageCoveragePercent =
    surfaces.length === 0 ? 0 : Math.round((imageReadySurfaces / surfaces.length) * 100);
  return {
    folders: getFolders().length,
    folderTypes: getFolderTypes().length,
    surfaces: surfaces.length,
    sheets: mix.sheet,
    cards: mix.card,
    stubs: mix.fallback_stub,
    sources: sourceCount(surfaces),
    imageReadySurfaces,
    imageCoveragePercent,
    imageCoverageHealthy: imageCoveragePercent >= 90,
    imageDistribution: imageDistribution(surfaces),
  };
}

export interface FolderTypeSummary {
  folderType: FolderType;
  folderCount: number;
  surfaceCount: number;
}

export function getFolderTypeSummaries(): FolderTypeSummary[] {
  return getFolderTypes().map((folderType) => {
    const folders = getFoldersByType(folderType.type);
    const surfaceIds = new Set<string>();
    for (const folder of folders) {
      for (const id of folder.surfaceIds) surfaceIds.add(id);
    }
    return {
      folderType,
      folderCount: folders.length,
      surfaceCount: surfaceIds.size,
    };
  });
}

/** Related folders resolved (and de-duplicated) from a folder's relatedFolderIds. */
export function getRelatedFolders(folder: Folder): Folder[] {
  return folder.relatedFolderIds
    .map((id) => getFolderById(id))
    .filter((f): f is Folder => Boolean(f));
}

// ---------------------------------------------------------------------------
// Search (deterministic, local-only, no LLM / network)
// ---------------------------------------------------------------------------

export interface SearchMatch {
  surface: Surface;
  /** Where the query matched, e.g. "Title", "Creator", "CLASSIFICATION". */
  field: string;
  /** Short surrounding snippet with the match. */
  snippet: string;
}

export interface SearchResult {
  surface: Surface;
  matches: SearchMatch[];
}

function makeSnippet(value: string, query: string): string {
  const idx = value.toLowerCase().indexOf(query.toLowerCase());
  if (idx === -1) return value.slice(0, 120);
  const start = Math.max(0, idx - 30);
  const end = Math.min(value.length, idx + query.length + 60);
  const prefix = start > 0 ? "…" : "";
  const suffix = end < value.length ? "…" : "";
  return `${prefix}${value.slice(start, end)}${suffix}`;
}

/**
 * Deterministic substring search over surface title, creator, date, place,
 * object type, medium, source name, folder titles, and every table row value.
 */
export function searchSurfaces(query: string): SearchResult[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];

  const results: SearchResult[] = [];

  for (const surface of getSurfaces()) {
    const matches: SearchMatch[] = [];

    const scalarFields: Array<[string, string]> = [
      ["Title", surface.title],
      ["Creator", surface.creator],
      ["Date", surface.dateText],
      ["Place", surface.placeText],
      ["Object type", surface.objectType],
      ["Medium", surface.medium],
      ["Source", surface.sourceName],
    ];

    for (const [field, value] of scalarFields) {
      if (value && value.toLowerCase().includes(q)) {
        matches.push({ surface, field, snippet: makeSnippet(value, query) });
      }
    }

    for (const folder of surface.folders) {
      if (folder.title.toLowerCase().includes(q)) {
        matches.push({
          surface,
          field: "Folder",
          snippet: makeSnippet(folder.title, query),
        });
      }
    }

    for (const table of surface.tables) {
      for (const [label, value] of table.rows) {
        const haystack = `${label}: ${value}`;
        if (haystack.toLowerCase().includes(q)) {
          matches.push({
            surface,
            field: table.kind,
            snippet: makeSnippet(haystack, query),
          });
        }
      }
    }

    if (matches.length > 0) {
      results.push({ surface, matches });
    }
  }

  // Stable ordering: more matches first, then chronological.
  return results.sort((a, b) => {
    if (b.matches.length !== a.matches.length) {
      return b.matches.length - a.matches.length;
    }
    const as = a.surface.dateStart ?? Number.POSITIVE_INFINITY;
    const bs = b.surface.dateStart ?? Number.POSITIVE_INFINITY;
    if (as !== bs) return as - bs;
    return a.surface.surfaceId.localeCompare(b.surface.surfaceId);
  });
}

// ---------------------------------------------------------------------------
// Fuzzy search (deterministic, local-only). Substring + subsequence scoring.
// ---------------------------------------------------------------------------

export interface FuzzyResult {
  surface: Surface;
  score: number;
  field: string;
  snippet: string;
}

function normalizedSearchText(value: string): string {
  return value.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").replace(/\s+/g, " ").trim();
}

/** Score a single term against text. Short terms are exact/prefix only. */
function termScore(text: string, term: string): number {
  const t = text.toLowerCase();
  const normalized = normalizedSearchText(text);
  const tokens = normalized.split(" ").filter(Boolean);
  const idx = t.indexOf(term);
  if (idx !== -1) {
    // earlier and whole-word-ish matches score higher
    const wordBonus = tokens.some((token) => token === term)
      ? 40
      : tokens.some((token) => token.startsWith(term))
        ? 18
        : 0;
    return 120 - Math.min(idx, 40) + (idx === 0 ? 20 : 0) + wordBonus;
  }
  if (term.length < 4) return 0;
  if (tokens.some((token) => token.startsWith(term))) return 84;

  // Conservative subsequence: only for longer terms, and only inside one token.
  if (term.length < 5) return 0;
  let ti = 0;
  for (const token of tokens) {
    ti = 0;
    for (let i = 0; i < token.length && ti < term.length; i++) {
      if (token[i] === term[ti]) ti++;
    }
    if (ti === term.length) return 26;
  }
  return 0;
}

/**
 * Fuzzy search over title, creator, date, place, object type, medium, source,
 * folder titles, and every table row value. A surface is returned only when
 * every query term matches at least one field (substring or subsequence).
 */
export function fuzzySearchSurfaces(query: string): FuzzyResult[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  const terms = q.split(/\s+/).filter(Boolean);
  if (terms.some((term) => term.length < 2)) return [];

  const results: FuzzyResult[] = [];

  for (const surface of getSurfaces()) {
    const fields: Array<[string, string, number]> = [
      ["Title", surface.title, 2.2],
      ["Creator", surface.creator, 1.4],
      ["Date", surface.dateText, 1],
      ["Place", surface.placeText, 1],
      ["Object type", surface.objectType, 1.1],
      ["Medium", surface.medium, 1.1],
      ["Source", surface.sourceName, 1],
    ];
    for (const f of surface.folders) fields.push(["Folder", f.title, 1.2]);
    if (q.length >= 4) {
      for (const tbl of surface.tables) {
        if (!["SOURCE", "NORMALIZED", "CLASSIFICATION", "CITATIONS"].includes(tbl.kind)) continue;
        for (const [label, value] of tbl.rows) {
          fields.push([tbl.kind, `${label}: ${value}`, 0.34]);
        }
      }
    }

    let total = 0;
    let best: { score: number; field: string; value: string } | null = null;
    let allTermsMatched = true;

    for (const term of terms) {
      let termBest = 0;
      for (const [field, value, weight] of fields) {
        if (!value) continue;
        const s = termScore(value, term) * weight;
        if (s > termBest) termBest = s;
        if (s > (best?.score ?? 0)) best = { score: s, field, value };
      }
      if (termBest === 0) {
        allTermsMatched = false;
        break;
      }
      total += termBest;
    }

    if (allTermsMatched && best) {
      const minimumScore = terms.length === 1 ? 78 : 58 * terms.length;
      if (total < minimumScore) continue;
      results.push({
        surface,
        score: total,
        field: best.field,
        snippet: makeSnippet(best.value, terms[0]),
      });
    }
  }

  return results.sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score;
    const as = a.surface.dateStart ?? Number.POSITIVE_INFINITY;
    const bs = b.surface.dateStart ?? Number.POSITIVE_INFINITY;
    if (as !== bs) return as - bs;
    return a.surface.surfaceId.localeCompare(b.surface.surfaceId);
  }).slice(0, 18);
}

// ---------------------------------------------------------------------------
// Static params helpers (for generateStaticParams)
// ---------------------------------------------------------------------------

export function allFolderTypeParams(): { type: FolderTypeKey }[] {
  return getFolderTypes().map((ft) => ({ type: ft.type }));
}

export function allFolderParams(): { type: FolderTypeKey; slug: string }[] {
  return getFolders().map((f) => ({ type: f.type, slug: f.slug }));
}

export function allSurfaceParams(): { id: string }[] {
  return getSurfaces().map((s) => ({ id: s.surfaceId }));
}

export const SURFACE_KIND_LABEL: Record<SurfaceKind, string> = {
  sheet: "Sheet",
  card: "Card",
  fallback_stub: "Fallback stub",
};
