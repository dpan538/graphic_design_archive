/* System suggests — a contextual research annotation, not an AI feature.
 *
 * A very light hint: one or two short sentences describing the current result
 * set, plus a few terse action tokens. No first-person voice, no "I recommend",
 * no long paragraph. Absent by default; only returns content when the result
 * set carries enough context AND there is a legitimate deterministic
 * suggestion. The live version comes from the guidance provider; this is the
 * fail-closed static equivalent, styled identically. It never changes ranking,
 * never runs itself — each `apply` takes effect only on an explicit click. No
 * provider name / "AI" / model name anywhere.
 *
 * NB: eligibility thresholds below are frozen for this design round — only the
 * wording is being tuned. Provider config / parsing / schema is a later
 * engineering round. */

import type { SearchResult, SearchState } from "./query";

export type Suggestion = { label: string; apply: Partial<SearchState> };

const decadeSpan = (mid: number): [number, number] => {
  const from = Math.round(mid / 10) * 10 - 10;
  return [from, from + 20];
};

export function suggestFor(
  state: SearchState,
  results: SearchResult[],
): { lines: string[]; suggestions: Suggestion[] } {
  if (results.length < 4) return { lines: [], suggestions: [] };

  const years = results.map((r) => r.record.year).sort((a, b) => a - b);
  const span = years[years.length - 1] - years[0];

  const count = <T,>(pick: (r: SearchResult) => T | T[]) => {
    const m = new Map<T, number>();
    for (const r of results) {
      const v = pick(r);
      for (const x of Array.isArray(v) ? v : [v]) m.set(x, (m.get(x) ?? 0) + 1);
    }
    return [...m.entries()].sort((a, b) => b[1] - a[1])[0];
  };

  const topPlace = count((r) => r.record.place);
  const topTheme = count((r) => r.record.themes);
  const topType = count((r) => r.record.objectType);

  const lines: string[] = [];
  const suggestions: Suggestion[] = [];

  if (!state.yearFrom && !state.yearTo && span > 25) {
    const [from, to] = decadeSpan((years[0] + years[years.length - 1]) / 2);
    lines.push("The current results span several decades.");
    lines.push("Narrowing the year range may make them easier to scan.");
    suggestions.push({ label: `${from}–${to}`, apply: { yearFrom: from, yearTo: to, after: 0 } });
  } else if (topPlace && topPlace[1] >= 3 && topPlace[1] / results.length >= 0.4) {
    lines.push(`Most of these records are from ${topPlace[0]}.`);
  }

  if (!state.theme && topTheme && topTheme[1] >= 3 && topTheme[1] < results.length) {
    suggestions.push({ label: `Theme: ${topTheme[0]}`, apply: { theme: topTheme[0], after: 0 } });
  } else if (!state.objectType && topType && topType[1] >= 4 && topType[1] < results.length) {
    suggestions.push({ label: `${topType[0]}s`, apply: { objectType: topType[0], after: 0 } });
  }

  if (suggestions.length === 0) return { lines: [], suggestions: [] };

  return { lines: lines.slice(0, 2), suggestions: suggestions.slice(0, 3) };
}
