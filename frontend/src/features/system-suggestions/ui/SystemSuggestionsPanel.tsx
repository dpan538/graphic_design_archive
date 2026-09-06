"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type {
  ApprovedSuggestion,
  SystemSuggestionsReference,
  SystemSuggestionsResponse,
  SystemSuggestionSurface,
  TraceSuggestionContext,
} from "../types";
import styles from "./SystemSuggestionsPanel.module.css";

async function stateHash(serialized: string): Promise<string> {
  const bytes = new TextEncoder().encode(serialized);
  const digest = await window.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((value) => value.toString(16).padStart(2, "0")).join("");
}

/* the panel (release pass): a host names its state — a v2 REFERENCE (the
   reader's own ids; the server resolves the facts) or, for the frozen
   reference workspaces, a v1 context (answered deterministically). Every
   change of the reference is a new request; a response that is not the
   latest request's is dropped, so a slow answer never describes a state
   the page has left. Nothing here shows a provider, a status or a hash. */
export default function SystemSuggestionsPanel({
  surface,
  reference,
  shown,
  context,
  onAction,
  openInquiryDisclosure = false,
  tone = "light",
  maxActions,
  variant = "panel",
}: Readonly<{
  surface: Exclude<SystemSuggestionSurface, "SEARCH_RESULTS">;
  /* v2: the state's identifiers */
  reference?: SystemSuggestionsReference;
  /* v2: the counts the page shows, for the server to confirm */
  shown?: Readonly<Record<string, number>>;
  /* v1: the frozen reference workspaces' self-described context */
  context?: TraceSuggestionContext;
  onAction?: (suggestion: ApprovedSuggestion) => void;
  openInquiryDisclosure?: boolean;
  tone?: "light" | "canvas";
  maxActions?: number;
  variant?: "panel" | "block";
}>) {
  const serialized = useMemo(() => JSON.stringify(reference ? { reference, shown: shown ?? null } : { context: context ?? null }), [reference, shown, context]);
  const [response, setResponse] = useState<SystemSuggestionsResponse | null>(null);
  const sequence = useRef(0);

  useEffect(() => {
    const controller = new AbortController();
    const mine = sequence.current + 1;
    sequence.current = mine;
    setResponse(null);
    const payload = JSON.parse(serialized) as { reference?: SystemSuggestionsReference; shown?: Readonly<Record<string, number>> | null; context?: TraceSuggestionContext | null };
    if (!payload.reference && !payload.context) return () => controller.abort();
    const send = async (): Promise<SystemSuggestionsResponse | null> => {
      const body = payload.reference
        ? { schemaVersion: "gda-system-suggestions-request/v2", surface, reference: payload.reference, ...(payload.shown ? { shown: payload.shown } : {}) }
        : { schemaVersion: "gda-system-suggestions-request/v1", surface, stateHash: await stateHash(`${surface}\n${JSON.stringify(payload.context)}`), context: payload.context };
      const result = await fetch("/api/system-suggestions/v1", {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify(body),
        cache: "no-store",
        signal: controller.signal,
      });
      if (!result.ok) return null;
      const answer = await result.json() as SystemSuggestionsResponse;
      return answer.surface === surface ? answer : null;
    };
    void send()
      .then((answer) => {
        /* only the latest request may answer */
        if (!controller.signal.aborted && sequence.current === mine && answer) setResponse(answer);
      })
      .catch(() => {
        // the page remains complete when optional orientation is unavailable
      });
    return () => controller.abort();
  }, [serialized, surface]);

  return (
    <>
      {openInquiryDisclosure ? (
        <section className={styles.disclosure} data-open-inquiry-disclosure="fixed" aria-labelledby="open-inquiry-disclosure-title">
          <h2 id="open-inquiry-disclosure-title">Open inquiry</h2>
          <p>Evidence remains incomplete.</p>
          <p>This is not a validated historical association.</p>
        </section>
      ) : null}
      {response ? (
        <aside className={styles.panel} data-tone={tone} data-variant={variant} aria-label={`${surface.replaceAll("_", " ")} orientation`}>
          <h2>System suggests</h2>
          <p>{response.note}</p>
          {response.suggestions.length && onAction && (maxActions === undefined || maxActions > 0) ? (
            <div className={styles.actions}>
              {(maxActions === undefined ? response.suggestions : response.suggestions.slice(0, maxActions)).map((suggestion) => (
                <button type="button" key={suggestion.id} onClick={() => onAction(suggestion)}>{suggestion.label}</button>
              ))}
            </div>
          ) : null}
        </aside>
      ) : null}
    </>
  );
}
