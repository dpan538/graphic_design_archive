"use client";

import type { Suggestion } from "../lib/suggest";
import type { SearchState } from "../lib/query";
import styles from "./SystemSuggests.module.css";

/* A light contextual annotation — not a panel, not a chat box. One or two short
   sentences and a few terse tokens; fades in only when there is content. Label
   is exactly "System suggests"; no provider name / "AI" / model name. */
export default function SystemSuggests({
  lines,
  suggestions,
  onApply,
}: {
  lines: string[];
  suggestions: Suggestion[];
  onApply: (a: Partial<SearchState>) => void;
}) {
  if (lines.length === 0 && suggestions.length === 0) return null;

  return (
    <aside className={styles.note} aria-label="System suggests">
      <p className={styles.label}>System suggests</p>
      {lines.map((l) => (
        <p key={l} className={styles.line}>
          {l}
        </p>
      ))}
      {suggestions.length ? (
        <p className={styles.tokens}>
          {suggestions.map((s) => (
            <button
              key={s.label}
              type="button"
              className={styles.token}
              onClick={() => onApply(s.apply)}
            >
              {s.label}
            </button>
          ))}
        </p>
      ) : null}
    </aside>
  );
}
