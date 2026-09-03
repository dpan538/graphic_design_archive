/* Search — pure query parse + deterministic scored match + pagination.
 *
 * Moderate, not clever: normalise → tokenise → score each record over weighted
 * fields, with three tiers of term match (exact / prefix / substring), a bounded
 * fuzzy tier (edit distance) for typos, and a small related-term map + fuzzy
 * vocabulary match for associative recall. Deterministic; sorted by score then
 * stable id. No dependencies. */

import { RECORDS, YEAR_MAX, YEAR_MIN, type SearchRecord } from "./fixture";

export const PAGE_SIZE = 25;

export type SearchState = {
  q: string;
  yearFrom: number | null;
  yearTo: number | null;
  objectType: string | null;
  theme: string | null;
  movement: string | null;
  after: number;
};

export const EMPTY_STATE: SearchState = {
  q: "",
  yearFrom: null,
  yearTo: null,
  objectType: null,
  theme: null,
  movement: null,
  after: 0,
};

export function parseSearch(params: URLSearchParams): SearchState {
  const num = (k: string) => {
    const v = Number(params.get(k));
    return Number.isFinite(v) && v > 0 ? Math.round(v) : null;
  };
  return {
    q: (params.get("q") ?? "").trim(),
    yearFrom: num("yearFrom"),
    yearTo: num("yearTo"),
    objectType: params.get("objectType") || null,
    theme: params.get("theme") || null,
    movement: params.get("movement") || null,
    after: Math.max(0, Number(params.get("after")) || 0),
  };
}

export function toParams(s: SearchState): URLSearchParams {
  const p = new URLSearchParams();
  if (s.q) p.set("q", s.q);
  if (s.yearFrom) p.set("yearFrom", String(s.yearFrom));
  if (s.yearTo) p.set("yearTo", String(s.yearTo));
  if (s.objectType) p.set("objectType", s.objectType);
  if (s.theme) p.set("theme", s.theme);
  if (s.movement) p.set("movement", s.movement);
  if (s.after) p.set("after", String(s.after));
  return p;
}

export function hasQuery(s: SearchState): boolean {
  return Boolean(
    s.q || s.yearFrom || s.yearTo || s.objectType || s.theme || s.movement,
  );
}

export function activeFilterCount(s: SearchState): number {
  return (
    (s.yearFrom || s.yearTo ? 1 : 0) +
    (s.objectType ? 1 : 0) +
    (s.theme ? 1 : 0) +
    (s.movement ? 1 : 0)
  );
}

/* ---------------------------------------------------------------- matching */

const norm = (s: string) =>
  s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9\s-]/g, " ");

const words = (s: string) => norm(s).split(/[\s-]+/).filter(Boolean);

/** Bounded Levenshtein — returns a distance capped at `max + 1`. */
function editDistance(a: string, b: string, max: number): number {
  if (Math.abs(a.length - b.length) > max) return max + 1;
  let prev = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    const curr = [i];
    let best = i;
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      const v = Math.min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost);
      curr[j] = v;
      if (v < best) best = v;
    }
    if (best > max) return max + 1;
    prev = curr;
  }
  return prev[b.length];
}

type Tier = "exact" | "prefix" | "substr" | "fuzzy" | null;

function termVsWord(term: string, word: string): Tier {
  if (term === word) return "exact";
  if (word.length >= 3 && word.startsWith(term) && term.length >= 3) return "prefix";
  if (term.length >= 4 && word.includes(term)) return "substr";
  const max = term.length >= 7 ? 2 : term.length >= 4 ? 1 : 0;
  if (max && editDistance(term, word, max) <= max) return "fuzzy";
  return null;
}

const TIER_BONUS: Record<Exclude<Tier, null>, number> = {
  exact: 0,
  prefix: -1,
  substr: -2,
  fuzzy: -3,
};

/* Related-term expansion — small, hand-built, deterministic. A query term that
   matches a key contributes its expansions at reduced weight (associative). */
const RELATED: Record<string, string[]> = {
  swiss: ["swiss style", "grid", "helvetica", "typography"],
  helvetica: ["swiss style", "type specimen", "typography", "haas"],
  grid: ["swiss style", "typography"],
  bauhaus: ["new typography", "constructivism", "typography"],
  constructivist: ["constructivism", "poster", "politics"],
  psychedelic: ["music", "concert", "poster"],
  concert: ["music", "record sleeve"],
  gig: ["music", "poster", "punk"],
  punk: ["music", "flyer", "new wave"],
  olympic: ["pictogram", "wayfinding", "signage", "public information"],
  olympics: ["pictogram", "wayfinding", "signage", "public information"],
  pictogram: ["signage", "public information", "olympic"],
  wayfinding: ["signage", "public information"],
  jazz: ["music", "record sleeve"],
  festival: ["music", "culture", "poster"],
  election: ["politics", "public information"],
  war: ["politics", "propaganda"],
  airline: ["identity", "advertising"],
};

const FIELDS = (r: SearchRecord): [string, number][] => [
  [r.title, 5],
  [r.credited ?? "", 3],
  [r.objectType, 3],
  [r.themes.join(" "), 3],
  [r.movements.join(" "), 4],
  [r.place, 2],
  [String(r.year), 2],
];

const VOCAB = (r: SearchRecord): string[] =>
  [r.objectType, ...r.themes, ...r.movements].map((v) => v.toLowerCase());

export type MatchReason =
  | "Exact title"
  | "Matched title and year"
  | "Matched movement"
  | "Matched all query terms"
  | "Matched a related term"
  | "Matched spelling variation";

export type SearchResult = { record: SearchRecord; reason: MatchReason };

/* The reader only needs two states. Direct field hits (exact / all terms /
   title+year / movement) are "perfect"; fuzzy or associative hits are "partial".
   Presentation only — the underlying `reason` is unchanged. */
export type MatchGrade = "perfect" | "partial";

export function matchGrade(reason: MatchReason): MatchGrade {
  return reason === "Matched a related term" ||
    reason === "Matched spelling variation"
    ? "partial"
    : "perfect";
}

type Signal = {
  score: number;
  perTerm: boolean[];
  fuzzy: boolean;
  related: boolean;
  movementHit: boolean;
  yearHit: boolean;
  titleTermHit: boolean;
};

function scoreRecord(r: SearchRecord, terms: string[]): Signal {
  const fields = FIELDS(r).map(([text, w]) => [words(text), w] as [string[], number]);
  const vocab = VOCAB(r);
  const sig: Signal = {
    score: 0,
    perTerm: terms.map(() => false),
    fuzzy: false,
    related: false,
    movementHit: false,
    yearHit: false,
    titleTermHit: false,
  };

  terms.forEach((term, ti) => {
    let termScore = 0;

    fields.forEach(([fw, weight], fi) => {
      let bestTier: Tier = null;
      for (const w of fw) {
        const t = termVsWord(term, w);
        if (t && (!bestTier || TIER_BONUS[t] > TIER_BONUS[bestTier])) bestTier = t;
      }
      if (bestTier) {
        const s = Math.max(1, weight + TIER_BONUS[bestTier]);
        termScore += s;
        if (bestTier === "fuzzy") sig.fuzzy = true;
        if (fi === 0) sig.titleTermHit = true;
        if (fi === 4) sig.movementHit = true;
        if (fi === 6 && /^\d{4}$/.test(term)) sig.yearHit = true;
      }
    });

    // Associative — related terms, at reduced weight.
    const exp = RELATED[term];
    if (exp) {
      for (const phrase of exp) {
        const pw = phrase.split(" ");
        const hit = pw.every((p) =>
          fields.some(([fw]) => fw.some((w) => termVsWord(p, w))),
        );
        if (hit) {
          termScore += 2;
          sig.related = true;
        }
      }
    }

    // Associative — fuzzy match against a vocabulary value → the category counts.
    if (termScore === 0) {
      for (const v of vocab) {
        const vw = v.split(" ");
        if (vw.some((w) => { const t = termVsWord(term, w); return t === "fuzzy" || t === "prefix"; })) {
          termScore += 2;
          sig.related = true;
          break;
        }
      }
    }

    if (termScore > 0) sig.perTerm[ti] = true;
    sig.score += termScore;
  });

  return sig;
}

function reasonFor(r: SearchRecord, terms: string[], q: string, sig: Signal): MatchReason {
  if (q && norm(r.title).trim() === norm(q).trim()) return "Exact title";
  if (sig.yearHit && sig.titleTermHit) return "Matched title and year";
  if (sig.movementHit && !sig.fuzzy) return "Matched movement";
  const allExact = sig.perTerm.every(Boolean) && !sig.fuzzy && !sig.related;
  if (allExact) return "Matched all query terms";
  if (sig.related && !sig.fuzzy) return "Matched a related term";
  return "Matched spelling variation";
}

export function runSearch(s: SearchState): {
  results: SearchResult[];
  total: number;
  page: SearchResult[];
  pageCount: number;
  pageIndex: number;
} {
  const terms = words(s.q);
  const filtersOnly = terms.length === 0 && activeFilterCount(s) > 0;

  const scored = RECORDS.map((record) => {
    if (s.yearFrom && record.year < s.yearFrom) return null;
    if (s.yearTo && record.year > s.yearTo) return null;
    if (s.objectType && record.objectType !== s.objectType) return null;
    if (s.theme && !record.themes.includes(s.theme)) return null;
    if (s.movement && !record.movements.includes(s.movement)) return null;

    if (filtersOnly) {
      return { record, score: 1, reason: "Matched all query terms" as MatchReason };
    }
    if (terms.length === 0) return null;

    const sig = scoreRecord(record, terms);
    // Require at least one term to have landed somewhere.
    if (sig.score <= 0 || !sig.perTerm.some(Boolean)) return null;
    return { record, score: sig.score, reason: reasonFor(record, terms, s.q, sig) };
  }).filter((x): x is { record: SearchRecord; score: number; reason: MatchReason } => x !== null);

  scored.sort((a, b) => b.score - a.score || a.record.id.localeCompare(b.record.id));

  const results: SearchResult[] = scored.map(({ record, reason }) => ({ record, reason }));
  const pageCount = Math.max(1, Math.ceil(results.length / PAGE_SIZE));
  const pageIndex = Math.min(s.after, pageCount - 1);
  const page = results.slice(pageIndex * PAGE_SIZE, (pageIndex + 1) * PAGE_SIZE);

  return { results, total: results.length, page, pageCount, pageIndex };
}

export { YEAR_MIN, YEAR_MAX };
