import { caseFold16, normalize16, isMark16, isLatin16, isNumber16, isLatinOrNumber16, isSeparator16 } from "@/features/search-v49/unicode16";
import { createHash } from "node:crypto";
import {
  boundedOsaDistance,
  caseFoldV1,
  foldLatinDiacritics,
  MAX_QUERY_CODE_POINTS,
  MAX_QUERY_TOKENS,
  normalizeSearchText,
  parseSearchQuery,
  SearchInputError,
  type ParsedSearchQuery,
} from "../search-v49/core";

export const PUBLIC_SEARCH_ALGORITHM_VERSION = "gda-public-object-relevance-v2";
export const PUBLIC_SEARCH_INDEX_FORMAT_VERSION = "gda-public-object-search-documents-v2";
export const PUBLIC_SEARCH_SCHEMA_VERSION = "gda-public-object-search-response/v1";
export const PUBLIC_SEARCH_DEFAULT_PAGE_SIZE = 25;
export const PUBLIC_SEARCH_MAX_PAGE_SIZE = 50;
const CURSOR_VERSION = 2;

export type SearchDeliveryState = "BLOCKED" | "CITATION_ONLY" | "LINK_ONLY" | "SOURCE_VIEWER" | "REMOTE_IMAGE";
export type PublicSearchDocumentTuple = readonly [
  stableId: string,
  title: string,
  creditedLabel: string | null,
  displayDate: string,
  yearStart: number,
  yearEnd: number,
  place: string,
  objectType: string,
  themes: readonly string[],
  movements: readonly string[],
  sourceLabel: string,
  deliveryState: SearchDeliveryState,
];

type SearchTextField = "title" | "creditedLabel" | "place";
type MatchType = "identifier" | "exact_title" | "normalized_title" | "field_exact" | "prefix" | "substring" | "multi_token" | "typo" | "filters";

type NormalizedField = {
  display: string;
  primary: string;
  compatibility: string;
  latinFolded: string;
  compactPrimary: string;
  compactCompatibility: string;
  compactLatinFolded: string;
  tokens: readonly string[];
  compatibilityTokens: readonly string[];
  latinFoldedTokens: readonly string[];
};

export type PublicSearchDocument = {
  stableId: string;
  normalizedId: string;
  title: string;
  creditedLabel: string | null;
  displayDate: string;
  yearStart: number;
  yearEnd: number;
  place: string;
  objectType: string;
  themes: readonly string[];
  movements: readonly string[];
  sourceLabel: string;
  deliveryState: SearchDeliveryState;
  fields: Readonly<Record<SearchTextField, NormalizedField | null>>;
};

export type PublicSearchFilters = {
  yearFrom?: number;
  yearTo?: number;
  objectType?: string;
  theme?: string;
  movement?: string;
};

export type PublicSearchRequest = {
  query: string;
  filters: PublicSearchFilters;
};

export type PublicSearchExplanation = {
  label: string;
  matchType: MatchType;
  matchedFields: readonly ("stableId" | SearchTextField)[];
  signals: readonly string[];
  score: number;
};

export type RankedPublicSearchDocument = {
  document: PublicSearchDocument;
  score: number;
  explanation: PublicSearchExplanation;
};

type CursorPayload = {
  v: number;
  release: string;
  manifest: string;
  algorithm: string;
  format: string;
  index: string;
  state: string;
  score: number;
  title: string;
  id: string;
};

const compareCodePoints = (left: string, right: string) => left < right ? -1 : left > right ? 1 : 0;
const compact = (value: string) => value.replace(/\s+/gu, "");
const splitTokens = (value: string) => value ? value.split(" ").filter(Boolean) : [];

function normalizedField(displayValue: string): NormalizedField | null {
  const display = displayValue.trim();
  if (!display) return null;
  const primary = normalizeSearchText(display, "NFC");
  const compatibility = normalizeSearchText(display, "NFKC");
  const latinFolded = foldLatinDiacritics(primary);
  return {
    display,
    primary,
    compatibility,
    latinFolded,
    compactPrimary: compact(primary),
    compactCompatibility: compact(compatibility),
    compactLatinFolded: compact(latinFolded),
    tokens: splitTokens(primary),
    compatibilityTokens: splitTokens(compatibility),
    latinFoldedTokens: splitTokens(latinFolded),
  };
}

export function hydratePublicSearchDocument(tuple: PublicSearchDocumentTuple): PublicSearchDocument {
  const [stableId, title, creditedLabel, displayDate, yearStart, yearEnd, place, objectType, themes, movements, sourceLabel, deliveryState] = tuple;
  return {
    stableId,
    normalizedId: caseFoldV1(normalize16(stableId, "NFKC")),
    title,
    creditedLabel,
    displayDate,
    yearStart,
    yearEnd,
    place,
    objectType,
    themes,
    movements,
    sourceLabel,
    deliveryState,
    fields: {
      title: normalizedField(title),
      creditedLabel: creditedLabel ? normalizedField(creditedLabel) : null,
      place: normalizedField(place),
    },
  };
}

function assertYear(value: number | undefined, name: string): void {
  if (value !== undefined && (!Number.isInteger(value) || value < 1000 || value > 3000)) {
    throw new SearchInputError("INVALID_ARGUMENT", `${name} must be an integer from 1000 to 3000`);
  }
}

export function normalizePublicSearchRequest(input: { query?: string; filters?: PublicSearchFilters }): PublicSearchRequest {
  const query = (input.query ?? "").trim();
  const codePoints = Array.from(query).length;
  if (codePoints > MAX_QUERY_CODE_POINTS) {
    throw new SearchInputError("INVALID_ARGUMENT", `q must contain at most ${MAX_QUERY_CODE_POINTS} Unicode code points`);
  }
  if (query) {
    const parsed = parseSearchQuery(query);
    if (parsed.tokens.length > MAX_QUERY_TOKENS) {
      throw new SearchInputError("INVALID_ARGUMENT", `q must contain at most ${MAX_QUERY_TOKENS} search tokens`);
    }
  }
  const filters = { ...(input.filters ?? {}) };
  assertYear(filters.yearFrom, "yearFrom");
  assertYear(filters.yearTo, "yearTo");
  if (filters.yearFrom !== undefined && filters.yearTo !== undefined && filters.yearFrom > filters.yearTo) {
    throw new SearchInputError("INVALID_ARGUMENT", "yearFrom must not be greater than yearTo");
  }
  for (const key of ["objectType", "theme", "movement"] as const) {
    const value = filters[key]?.trim();
    if (value && Array.from(value).length > 160) throw new SearchInputError("INVALID_ARGUMENT", `${key} is too long`);
    if (value) filters[key] = value;
    else delete filters[key];
  }
  if (!query && !Object.keys(filters).length) {
    throw new SearchInputError("INVALID_ARGUMENT", "q or at least one Search filter is required");
  }
  return { query, filters };
}

export function publicSearchStateHash(request: PublicSearchRequest): string {
  return createHash("sha256").update(JSON.stringify({
    q: request.query,
    yearFrom: request.filters.yearFrom ?? null,
    yearTo: request.filters.yearTo ?? null,
    objectType: request.filters.objectType ?? null,
    theme: request.filters.theme ?? null,
    movement: request.filters.movement ?? null,
  })).digest("hex");
}

export function matchesPublicSearchFilters(document: PublicSearchDocument, filters: PublicSearchFilters): boolean {
  const from = filters.yearFrom ?? Number.NEGATIVE_INFINITY;
  const to = filters.yearTo ?? Number.POSITIVE_INFINITY;
  if (document.yearEnd < from || document.yearStart > to) return false;
  if (filters.objectType && document.objectType !== filters.objectType) return false;
  if (filters.theme && !document.themes.includes(filters.theme)) return false;
  if (filters.movement && !document.movements.includes(filters.movement)) return false;
  return true;
}

function editLimit(token: string): number {
  const length = Array.from(token).length;
  if (Array.from(token).some(isNumber16) || length < 4) return 0;
  return length <= 8 ? 1 : 2;
}

type TokenMatch = { score: number; signal: string; field: SearchTextField; typo: boolean };

function tokenMatch(queryToken: string, documentToken: string): Omit<TokenMatch, "field"> | null {
  if (documentToken === queryToken) return { score: 1800, signal: "token_exact", typo: false };
  const onePointLatin = Array.from(queryToken).length === 1 && Array.from(queryToken).every(isLatinOrNumber16);
  if (!onePointLatin && documentToken.startsWith(queryToken)) return { score: 1450, signal: "token_prefix", typo: false };
  if ((Array.from(queryToken).length >= 2 || Array.from(queryToken).some(character => !isLatinOrNumber16(character))) && documentToken.includes(queryToken)) {
    return { score: 1100, signal: "token_substring", typo: false };
  }
  const limit = editLimit(queryToken);
  const distance = boundedOsaDistance(queryToken, documentToken, limit);
  return distance && distance <= limit ? { score: 900 - (distance * 180), signal: `osa_distance_${distance}`, typo: true } : null;
}

const FIELD_WEIGHT: Record<SearchTextField, number> = { title: 1, creditedLabel: 0.82, place: 0.72 };
const FIELD_ORDER: readonly SearchTextField[] = ["title", "creditedLabel", "place"];

function bestTokenMatch(query: ParsedSearchQuery, index: number, document: PublicSearchDocument): TokenMatch | null {
  let best: TokenMatch | null = null;
  for (const fieldName of FIELD_ORDER) {
    const field = document.fields[fieldName];
    if (!field) continue;
    const channels: readonly [string, readonly string[]][] = [
      [query.tokens[index], field.tokens],
      [query.compatibilityTokens[index] ?? query.tokens[index], field.compatibilityTokens],
      [query.latinFoldedTokens[index] ?? query.tokens[index], field.latinFoldedTokens],
    ];
    for (const [queryToken, documentTokens] of channels) {
      for (const documentToken of documentTokens) {
        const candidate = tokenMatch(queryToken, documentToken);
        if (!candidate) continue;
        const weighted = { ...candidate, score: Math.round(candidate.score * FIELD_WEIGHT[fieldName]), field: fieldName };
        if (!best || weighted.score > best.score || (weighted.score === best.score && compareCodePoints(weighted.field, best.field) < 0)) best = weighted;
      }
    }
  }
  return best;
}

function fieldExact(field: NormalizedField, query: ParsedSearchQuery): string | null {
  if (field.primary === query.primary) return "primary_exact";
  if (field.compatibility === query.compatibility) return "compatibility_exact";
  if (field.latinFolded === query.latinFolded) return "latin_diacritic_exact";
  return null;
}

function fieldPhrase(field: NormalizedField, query: ParsedSearchQuery): { type: "prefix" | "substring"; signal: string } | null {
  if (field.primary.startsWith(query.primary)) return { type: "prefix", signal: "primary_prefix" };
  if (field.compatibility.startsWith(query.compatibility)) return { type: "prefix", signal: "compatibility_prefix" };
  if (field.latinFolded.startsWith(query.latinFolded)) return { type: "prefix", signal: "latin_diacritic_prefix" };
  if (field.primary.includes(query.primary)) return { type: "substring", signal: "primary_substring" };
  if (field.compatibility.includes(query.compatibility)) return { type: "substring", signal: "compatibility_substring" };
  if (field.latinFolded.includes(query.latinFolded)) return { type: "substring", signal: "latin_diacritic_substring" };
  if (query.compactPrimary.length >= 2 && (
    field.compactPrimary.includes(query.compactPrimary)
    || field.compactCompatibility.includes(query.compactCompatibility)
    || field.compactLatinFolded.includes(query.compactLatinFolded)
  )) return { type: "substring", signal: "compact_substring" };
  return null;
}

function explanationLabel(matchType: MatchType, fields: readonly SearchTextField[], filters: PublicSearchFilters): string {
  if (matchType === "identifier") return "Exact stable ID";
  if ((matchType === "exact_title" || matchType === "normalized_title") && (filters.yearFrom !== undefined || filters.yearTo !== undefined)) return "Matched title and year";
  if (matchType === "exact_title" || matchType === "normalized_title") return "Exact title";
  if (matchType === "multi_token") return "Matched all query terms";
  if (matchType === "typo") return "Matched spelling variation";
  if (matchType === "filters" && filters.movement) return "Matched movement";
  if (matchType === "filters") return "Matched selected filters";
  if (fields.includes("title")) return "Matched title";
  if (fields.includes("creditedLabel")) return "Matched credited designer or studio";
  return "Matched place";
}

function scorePublicSearchDocument(document: PublicSearchDocument, query: ParsedSearchQuery, filters: PublicSearchFilters): RankedPublicSearchDocument | null {
  const queryId = caseFoldV1(normalize16(query.raw, "NFKC"));
  if (queryId === document.normalizedId) {
    const score = 30000;
    return { document, score, explanation: { label: "Exact stable ID", matchType: "identifier", matchedFields: ["stableId"], signals: ["stable_id_exact"], score } };
  }
  const title = document.fields.title!;
  if (query.raw === document.title) {
    const score = 29000;
    return { document, score, explanation: { label: explanationLabel("exact_title", ["title"], filters), matchType: "exact_title", matchedFields: ["title"], signals: ["display_title_exact"], score } };
  }
  const exactTitleSignal = fieldExact(title, query);
  if (exactTitleSignal) {
    const score = exactTitleSignal === "primary_exact" ? 28000 : exactTitleSignal === "compatibility_exact" ? 27500 : 27000;
    return { document, score, explanation: { label: explanationLabel("normalized_title", ["title"], filters), matchType: "normalized_title", matchedFields: ["title"], signals: [exactTitleSignal], score } };
  }
  for (const fieldName of ["creditedLabel", "place"] as const) {
    const field = document.fields[fieldName];
    if (!field) continue;
    const signal = fieldExact(field, query);
    if (signal) {
      const score = fieldName === "creditedLabel" ? 23500 : 22500;
      return { document, score, explanation: { label: explanationLabel("field_exact", [fieldName], filters), matchType: "field_exact", matchedFields: [fieldName], signals: [signal], score } };
    }
  }
  let bestPhrase: RankedPublicSearchDocument | null = null;
  for (const fieldName of FIELD_ORDER) {
    const field = document.fields[fieldName];
    if (!field) continue;
    const phrase = fieldPhrase(field, query);
    if (!phrase) continue;
    const base = phrase.type === "prefix" ? 21000 : 18500;
    const score = Math.round(base * FIELD_WEIGHT[fieldName]);
    const candidate: RankedPublicSearchDocument = {
      document,
      score,
      explanation: { label: explanationLabel(phrase.type, [fieldName], filters), matchType: phrase.type, matchedFields: [fieldName], signals: [phrase.signal], score },
    };
    if (!bestPhrase || candidate.score > bestPhrase.score) bestPhrase = candidate;
  }
  if (bestPhrase) return bestPhrase;

  const matches: TokenMatch[] = [];
  for (let index = 0; index < query.tokens.length; index += 1) {
    const match = bestTokenMatch(query, index, document);
    if (!match) return null;
    matches.push(match);
  }
  if (!matches.length) return null;
  const typo = matches.some((match) => match.typo);
  const matchedFields = [...new Set(matches.map((match) => match.field))].sort(compareCodePoints);
  const matchType: MatchType = typo ? "typo" : query.tokens.length > 1 ? "multi_token" : matches[0].signal === "token_prefix" ? "prefix" : "substring";
  const score = 6000 + matches.reduce((sum, match) => sum + match.score, 0) + (query.tokens.length > 1 ? 800 : 0);
  return {
    document,
    score,
    explanation: {
      label: explanationLabel(matchType, matchedFields, filters),
      matchType,
      matchedFields,
      signals: matches.map((match) => `${match.field}:${match.signal}`),
      score,
    },
  };
}

export function rankPublicSearchDocuments(documents: readonly PublicSearchDocument[], request: PublicSearchRequest): RankedPublicSearchDocument[] {
  const filtered = documents.filter((document) => matchesPublicSearchFilters(document, request.filters));
  const query = request.query ? parseSearchQuery(request.query) : null;
  const ranked = query
    ? filtered.map((document) => scorePublicSearchDocument(document, query, request.filters)).filter((item): item is RankedPublicSearchDocument => item !== null)
    : filtered.map((document) => ({
      document,
      score: 0,
      explanation: {
        label: explanationLabel("filters", [], request.filters),
        matchType: "filters" as const,
        matchedFields: [] as const,
        signals: ["hard_filters_only"],
        score: 0,
      },
    }));
  return ranked.sort((left, right) => right.score - left.score
    || compareCodePoints(left.document.fields.title!.primary, right.document.fields.title!.primary)
    || compareCodePoints(left.document.stableId, right.document.stableId));
}

function encodeCursor(payload: CursorPayload): string {
  return Buffer.from(JSON.stringify(payload), "utf8").toString("base64url");
}

function decodeCursor(value: string): CursorPayload {
  if (value.length > 2048) throw new SearchInputError("INVALID_CURSOR", "search cursor is too large");
  try {
    const payload = JSON.parse(Buffer.from(value, "base64url").toString("utf8")) as CursorPayload;
    if (!payload || typeof payload !== "object") throw new Error("shape");
    return payload;
  } catch {
    throw new SearchInputError("INVALID_CURSOR", "search cursor is malformed");
  }
}

export function pagePublicSearchResults(input: {
  ranked: readonly RankedPublicSearchDocument[];
  request: PublicSearchRequest;
  after?: string;
  first?: number;
  releaseId: string;
  manifestSha256: string;
  indexSha256: string;
}) {
  const first = input.first ?? PUBLIC_SEARCH_DEFAULT_PAGE_SIZE;
  if (!Number.isInteger(first) || first < 1 || first > PUBLIC_SEARCH_MAX_PAGE_SIZE) {
    throw new SearchInputError("INVALID_ARGUMENT", `first must be an integer from 1 to ${PUBLIC_SEARCH_MAX_PAGE_SIZE}`);
  }
  const state = publicSearchStateHash(input.request);
  let start = 0;
  if (input.after) {
    const cursor = decodeCursor(input.after);
    const expected = {
      v: CURSOR_VERSION,
      release: input.releaseId,
      manifest: input.manifestSha256,
      algorithm: PUBLIC_SEARCH_ALGORITHM_VERSION,
      format: PUBLIC_SEARCH_INDEX_FORMAT_VERSION,
      index: input.indexSha256,
      state,
    };
    for (const [key, value] of Object.entries(expected)) {
      if (cursor[key as keyof CursorPayload] !== value) throw new SearchInputError("INVALID_CURSOR", "search cursor does not match this release, index, query, or filter state");
    }
    const terminal = input.ranked.findIndex((item) => item.score === cursor.score
      && item.document.fields.title!.primary === cursor.title
      && item.document.stableId === cursor.id);
    if (terminal < 0) throw new SearchInputError("INVALID_CURSOR", "search cursor terminal result is unavailable");
    start = terminal + 1;
  }
  const nodes = input.ranked.slice(start, start + first);
  const hasNextPage = start + nodes.length < input.ranked.length;
  const terminal = nodes.at(-1);
  return {
    nodes,
    pageInfo: {
      hasNextPage,
      nextCursor: hasNextPage && terminal ? encodeCursor({
        v: CURSOR_VERSION,
        release: input.releaseId,
        manifest: input.manifestSha256,
        algorithm: PUBLIC_SEARCH_ALGORITHM_VERSION,
        format: PUBLIC_SEARCH_INDEX_FORMAT_VERSION,
        index: input.indexSha256,
        state,
        score: terminal.score,
        title: terminal.document.fields.title!.primary,
        id: terminal.document.stableId,
      }) : null,
      totalExact: input.ranked.length,
    },
    stateHash: state,
  };
}

export { SearchInputError };
