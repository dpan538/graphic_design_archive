import { createHash } from "node:crypto";
import type { SearchMatchExplanation, SearchMatchType } from "@/lib/read-platform/types";

export const SEARCH_ALGORITHM_VERSION = "v49-lexical-fuzzy-1";
export const INDEX_FORMAT_VERSION = "gda-search-documents-v1";
export const MAX_QUERY_CODE_POINTS = 160;
export const MAX_QUERY_TOKENS = 24;
export const MAX_PAGE_SIZE = 100;
export const DEFAULT_PAGE_SIZE = 25;
const CURSOR_VERSION = 1;

export type SearchDocumentTuple = readonly [stableId: string, title: string, primary: string, compatibility: string, latinFolded: string];

export interface SearchDocument {
  stableId: string;
  title: string;
  primary: string;
  compatibility: string;
  latinFolded: string;
  compactPrimary: string;
  compactCompatibility: string;
  compactLatinFolded: string;
  normalizedId: string;
  tokens: readonly string[];
  compatibilityTokens: readonly string[];
  latinFoldedTokens: readonly string[];
}

export interface RankedSearchDocument {
  document: SearchDocument;
  score: number;
  explanation: SearchMatchExplanation;
}

export interface ParsedSearchQuery {
  raw: string;
  primary: string;
  compatibility: string;
  latinFolded: string;
  compactPrimary: string;
  compactCompatibility: string;
  compactLatinFolded: string;
  tokens: readonly string[];
  compatibilityTokens: readonly string[];
  latinFoldedTokens: readonly string[];
}

type CursorPayload = {
  v: number;
  release: string;
  manifest: string;
  algorithm: string;
  format: string;
  index: string;
  query: string;
  scope: string;
  score: number;
  title: string;
  id: string;
};

export class SearchInputError extends Error {
  constructor(readonly code: "INVALID_ARGUMENT" | "INVALID_CURSOR", message: string) { super(message); }
}

export function caseFoldV1(value: string): string {
  return value.toLowerCase().replaceAll("ß", "ss").replaceAll("ς", "σ");
}

function collapseSeparators(value: string): string {
  return value
    .replace(/[\u00a0\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]/gu, " ")
    .replace(/[\u2010-\u2015\u2212_-]+/gu, " ")
    .replace(/[\u2018\u2019\u02bc'`]+/gu, " ")
    .replace(/[\\/]+/gu, " ")
    .replace(/[\p{P}\p{S}]+/gu, " ")
    .replace(/\s+/gu, " ")
    .trim();
}

export function normalizeSearchText(value: string, form: "NFC" | "NFKC" = "NFC"): string {
  return collapseSeparators(caseFoldV1(value.normalize(form)));
}

export function foldLatinDiacritics(value: string): string {
  let output = "";
  let latinStarter = false;
  for (const character of value.normalize("NFD")) {
    if (/\p{M}/u.test(character)) {
      if (!latinStarter) output += character;
      continue;
    }
    latinStarter = /\p{Script=Latin}/u.test(character);
    output += character;
  }
  return output.normalize("NFC");
}

const compact = (value: string) => value.replace(/\s+/gu, "");
const tokens = (value: string) => value ? value.split(" ").filter(Boolean) : [];
const compareCodePoints = (left: string, right: string) => left < right ? -1 : left > right ? 1 : 0;
const queryHash = (query: ParsedSearchQuery) => createHash("sha256").update([query.primary, query.compatibility, query.latinFolded].join("\u0000")).digest("hex");

export function hydrateSearchDocument(tuple: SearchDocumentTuple): SearchDocument {
  const [stableId, title, primary, compatibility, latinFolded] = tuple;
  return {
    stableId, title, primary, compatibility, latinFolded,
    compactPrimary: compact(primary), compactCompatibility: compact(compatibility), compactLatinFolded: compact(latinFolded),
    normalizedId: caseFoldV1(stableId.normalize("NFKC")),
    tokens: tokens(primary), compatibilityTokens: tokens(compatibility), latinFoldedTokens: tokens(latinFolded),
  };
}

export function parseSearchQuery(rawInput: string): ParsedSearchQuery {
  const raw = rawInput.trim();
  const length = Array.from(raw).length;
  if (!raw || length > MAX_QUERY_CODE_POINTS) throw new SearchInputError("INVALID_ARGUMENT", `q must contain 1 to ${MAX_QUERY_CODE_POINTS} Unicode code points`);
  const primary = normalizeSearchText(raw, "NFC");
  const compatibility = normalizeSearchText(raw, "NFKC");
  const latinFolded = foldLatinDiacritics(primary);
  const primaryTokens = tokens(primary);
  if (primaryTokens.length > MAX_QUERY_TOKENS) throw new SearchInputError("INVALID_ARGUMENT", `q must contain at most ${MAX_QUERY_TOKENS} search tokens`);
  return {
    raw, primary, compatibility, latinFolded,
    compactPrimary: compact(primary), compactCompatibility: compact(compatibility), compactLatinFolded: compact(latinFolded),
    tokens: primaryTokens, compatibilityTokens: tokens(compatibility), latinFoldedTokens: tokens(latinFolded),
  };
}

function editLimit(token: string): number {
  const length = Array.from(token).length;
  if (/\p{N}/u.test(token) || length < 4) return 0;
  return length <= 8 ? 1 : 2;
}

/** Bounded Optimal String Alignment distance: adjacent transposition counts as one edit. */
export function boundedOsaDistance(leftInput: string, rightInput: string, limit: number): number | null {
  if (limit <= 0) return leftInput === rightInput ? 0 : null;
  const left = Array.from(leftInput); const right = Array.from(rightInput);
  if (Math.abs(left.length - right.length) > limit) return null;
  let previousPrevious: number[] | null = null;
  let previous = Array.from({ length: right.length + 1 }, (_, index) => index);
  for (let i = 1; i <= left.length; i += 1) {
    const current = [i]; let rowMinimum = i;
    for (let j = 1; j <= right.length; j += 1) {
      const substitution = previous[j - 1] + (left[i - 1] === right[j - 1] ? 0 : 1);
      let value = Math.min(previous[j] + 1, current[j - 1] + 1, substitution);
      if (i > 1 && j > 1 && left[i - 1] === right[j - 2] && left[i - 2] === right[j - 1] && previousPrevious) {
        value = Math.min(value, previousPrevious[j - 2] + 1);
      }
      current[j] = value; rowMinimum = Math.min(rowMinimum, value);
    }
    if (rowMinimum > limit) return null;
    previousPrevious = previous; previous = current;
  }
  return previous[right.length] <= limit ? previous[right.length] : null;
}

type TokenMatch = { score: number; signal: string; typo: boolean };

function bestTokenMatch(queryToken: string, documentTokens: readonly string[]): TokenMatch | null {
  let best: TokenMatch | null = null;
  const onePointLatin = Array.from(queryToken).length === 1 && /^[\p{Script=Latin}\p{N}]$/u.test(queryToken);
  for (const documentToken of documentTokens) {
    let match: TokenMatch | null = null;
    if (documentToken === queryToken) match = { score: 1800, signal: "token_exact", typo: false };
    else if (!onePointLatin && documentToken.startsWith(queryToken)) match = { score: 1450, signal: "token_prefix", typo: false };
    else if ((Array.from(queryToken).length >= 2 || /[^\p{Script=Latin}\p{N}]/u.test(queryToken)) && documentToken.includes(queryToken)) match = { score: 1100, signal: "token_substring", typo: false };
    else {
      const limit = editLimit(queryToken);
      const distance = boundedOsaDistance(queryToken, documentToken, limit);
      if (distance && distance <= limit) match = { score: 900 - (distance * 180), signal: `osa_distance_${distance}`, typo: true };
    }
    if (match && (!best || match.score > best.score)) best = match;
  }
  return best;
}

function explain(query: ParsedSearchQuery, score: number, matchType: SearchMatchType, fields: readonly ("stableId" | "title")[], signals: readonly string[]): SearchMatchExplanation {
  return { algorithmVersion: SEARCH_ALGORITHM_VERSION, score, matchType, matchedFields: fields, signals, normalizedQuery: query.primary };
}

export function scoreDocument(document: SearchDocument, query: ParsedSearchQuery): RankedSearchDocument | null {
  const queryId = caseFoldV1(query.raw.normalize("NFKC"));
  if (queryId === document.normalizedId) {
    const score = 30000;
    return { document, score, explanation: explain(query, score, "identifier", ["stableId"], ["stable_id_exact"]) };
  }
  if (!query.primary) return null;
  if (query.raw === document.title) {
    const score = 29000;
    return { document, score, explanation: explain(query, score, "exact_title", ["title"], ["display_title_exact"]) };
  }
  const channelExact = document.primary === query.primary ? [28000, "primary_exact"] as const
    : document.compatibility === query.compatibility ? [27500, "compatibility_exact"] as const
      : document.latinFolded === query.latinFolded ? [27000, "latin_diacritic_exact"] as const : null;
  if (channelExact) return { document, score: channelExact[0], explanation: explain(query, channelExact[0], "normalized_title", ["title"], [channelExact[1]]) };

  const phrase = document.primary.startsWith(query.primary) ? [21000, "prefix" as const, "primary_prefix"] as const
    : document.compatibility.startsWith(query.compatibility) ? [20500, "prefix" as const, "compatibility_prefix"] as const
      : document.latinFolded.startsWith(query.latinFolded) ? [20000, "prefix" as const, "latin_diacritic_prefix"] as const
        : document.primary.includes(query.primary) ? [18500, "substring" as const, "primary_substring"] as const
          : document.compatibility.includes(query.compatibility) ? [18000, "substring" as const, "compatibility_substring"] as const
            : document.latinFolded.includes(query.latinFolded) ? [17500, "substring" as const, "latin_diacritic_substring"] as const : null;
  if (phrase) return { document, score: phrase[0], explanation: explain(query, phrase[0], phrase[1], ["title"], [phrase[2]]) };

  if (query.compactPrimary.length >= 2) {
    const compactMatch = document.compactPrimary.includes(query.compactPrimary) ? "primary_compact"
      : document.compactCompatibility.includes(query.compactCompatibility) ? "compatibility_compact"
        : document.compactLatinFolded.includes(query.compactLatinFolded) ? "latin_diacritic_compact" : null;
    if (compactMatch) {
      const score = 16500;
      return { document, score, explanation: explain(query, score, "substring", ["title"], [compactMatch]) };
    }
  }

  const tokenMatches: TokenMatch[] = [];
  for (let index = 0; index < query.tokens.length; index += 1) {
    const candidates = [
      bestTokenMatch(query.tokens[index], document.tokens),
      bestTokenMatch(query.compatibilityTokens[index] ?? query.tokens[index], document.compatibilityTokens),
      bestTokenMatch(query.latinFoldedTokens[index] ?? query.tokens[index], document.latinFoldedTokens),
    ].filter((value): value is TokenMatch => value !== null);
    if (!candidates.length) return null;
    tokenMatches.push(candidates.sort((left, right) => right.score - left.score || compareCodePoints(left.signal, right.signal))[0]);
  }
  if (!tokenMatches.length) return null;
  const typo = tokenMatches.some((match) => match.typo);
  const score = 6000 + tokenMatches.reduce((sum, match) => sum + match.score, 0) + (query.tokens.length > 1 ? 800 : 0);
  const matchType: SearchMatchType = typo ? "typo" : query.tokens.length > 1 ? "multi_token" : tokenMatches[0].signal === "token_prefix" ? "prefix" : "substring";
  return { document, score, explanation: explain(query, score, matchType, ["title"], tokenMatches.map((match) => match.signal)) };
}

export function rankDocuments(documents: readonly SearchDocument[], query: ParsedSearchQuery): RankedSearchDocument[] {
  const ranked: RankedSearchDocument[] = [];
  for (const document of documents) { const result = scoreDocument(document, query); if (result) ranked.push(result); }
  return ranked.sort((left, right) => right.score - left.score || compareCodePoints(left.document.primary, right.document.primary) || compareCodePoints(left.document.stableId, right.document.stableId));
}

function encodeCursor(payload: CursorPayload): string { return Buffer.from(JSON.stringify(payload), "utf8").toString("base64url"); }
function decodeCursor(value: string): CursorPayload {
  if (value.length > 2048) throw new SearchInputError("INVALID_CURSOR", "search cursor is too large");
  try {
    const payload = JSON.parse(Buffer.from(value, "base64url").toString("utf8")) as CursorPayload;
    if (!payload || typeof payload !== "object") throw new Error("shape");
    return payload;
  } catch { throw new SearchInputError("INVALID_CURSOR", "search cursor is malformed"); }
}

export function pageRankedDocuments(input: {
  ranked: readonly RankedSearchDocument[];
  query: ParsedSearchQuery;
  after?: string;
  first?: number;
  releaseId: string;
  manifestSha256: string;
  indexSha256: string;
  scope: string;
}) {
  const first = input.first ?? DEFAULT_PAGE_SIZE;
  if (!Number.isInteger(first) || first < 1 || first > MAX_PAGE_SIZE) throw new SearchInputError("INVALID_ARGUMENT", `first must be an integer from 1 to ${MAX_PAGE_SIZE}`);
  let start = 0;
  if (input.after) {
    const cursor = decodeCursor(input.after);
    const expected = {
      v: CURSOR_VERSION, release: input.releaseId, manifest: input.manifestSha256,
      algorithm: SEARCH_ALGORITHM_VERSION, format: INDEX_FORMAT_VERSION, index: input.indexSha256,
      query: queryHash(input.query), scope: input.scope,
    };
    for (const [key, value] of Object.entries(expected)) if (cursor[key as keyof CursorPayload] !== value) throw new SearchInputError("INVALID_CURSOR", "search cursor does not match this release, index, query, or scope");
    const terminal = input.ranked.findIndex((item) => item.score === cursor.score && item.document.primary === cursor.title && item.document.stableId === cursor.id);
    if (terminal < 0) throw new SearchInputError("INVALID_CURSOR", "search cursor terminal result is unavailable");
    start = terminal + 1;
  }
  const nodes = input.ranked.slice(start, start + first);
  const hasNextPage = start + nodes.length < input.ranked.length;
  const terminal = nodes.at(-1);
  const nextCursor = hasNextPage && terminal ? encodeCursor({
    v: CURSOR_VERSION, release: input.releaseId, manifest: input.manifestSha256,
    algorithm: SEARCH_ALGORITHM_VERSION, format: INDEX_FORMAT_VERSION, index: input.indexSha256,
    query: queryHash(input.query), scope: input.scope, score: terminal.score,
    title: terminal.document.primary, id: terminal.document.stableId,
  }) : null;
  return { nodes, pageInfo: { hasNextPage, nextCursor, totalExact: input.ranked.length } };
}
