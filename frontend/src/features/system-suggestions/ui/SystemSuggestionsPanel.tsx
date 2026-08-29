"use client";

import { useEffect, useMemo, useState } from "react";
import type {
  ApprovedSuggestion,
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

export default function SystemSuggestionsPanel({
  surface,
  context,
  onAction,
  openInquiryDisclosure = false,
}: Readonly<{
  surface: Exclude<SystemSuggestionSurface, "SEARCH_RESULTS">;
  context: TraceSuggestionContext;
  onAction?: (suggestion: ApprovedSuggestion) => void;
  openInquiryDisclosure?: boolean;
}>) {
  const serializedContext = useMemo(() => JSON.stringify(context), [context]);
  const [response, setResponse] = useState<SystemSuggestionsResponse | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setResponse(null);
    void stateHash(`${surface}\n${serializedContext}`)
      .then(async (hash) => {
        const result = await fetch("/api/system-suggestions/v1", {
          method: "POST",
          headers: { Accept: "application/json", "Content-Type": "application/json" },
          body: JSON.stringify({
            schemaVersion: "gda-system-suggestions-request/v1",
            surface,
            stateHash: hash,
            context: JSON.parse(serializedContext),
          }),
          cache: "no-store",
          signal: controller.signal,
        });
        if (!result.ok) return null;
        const body = await result.json() as SystemSuggestionsResponse;
        return body.surface === surface && body.stateHash === hash ? body : null;
      })
      .then((body) => {
        if (!controller.signal.aborted && body) setResponse(body);
      })
      .catch(() => {
        // TRACE remains complete when optional orientation is unavailable.
      });
    return () => controller.abort();
  }, [serializedContext, surface]);

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
        <aside className={styles.panel} aria-label={`${surface.replaceAll("_", " ")} orientation`}>
          <h2>System suggests</h2>
          <p>{response.note}</p>
          {response.suggestions.length && onAction ? (
            <div className={styles.actions}>
              {response.suggestions.map((suggestion) => (
                <button type="button" key={suggestion.id} onClick={() => onAction(suggestion)}>{suggestion.label}</button>
              ))}
            </div>
          ) : null}
        </aside>
      ) : null}
    </>
  );
}
