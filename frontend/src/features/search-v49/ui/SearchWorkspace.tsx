"use client";

import Link from "next/link";
import { FormEvent, KeyboardEvent, useCallback, useEffect, useId, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { HttpArchiveRepositoryProvider } from "@/lib/read-platform/http-repository";
import type { SearchHit } from "@/lib/read-platform/types";
import styles from "./SearchWorkspace.module.css";

type SearchState = "idle" | "loading" | "ready" | "loading-more" | "error";

const matchLabels: Record<string, string> = {
  identifier: "Exact stable ID",
  exact_title: "Exact title",
  normalized_title: "Normalized title",
  prefix: "Title prefix",
  substring: "Title fragment",
  multi_token: "All query words",
  typo: "Spelling correction",
};

function message(error: unknown) { return error instanceof Error ? error.message : "The public search service is unavailable."; }

export default function SearchWorkspace() {
  const titleId = useId();
  const router = useRouter();
  const parameters = useSearchParams();
  const urlQuery = parameters.get("q") ?? "";
  const [input, setInput] = useState(urlQuery);
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [items, setItems] = useState<readonly SearchHit[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [algorithm, setAlgorithm] = useState("");
  const [state, setState] = useState<SearchState>(urlQuery.trim() ? "loading" : "idle");
  const [error, setError] = useState("");
  const requestRef = useRef<AbortController | null>(null);
  const queryLength = Array.from(input.trim()).length;

  const search = useCallback(async (query: string, after?: string) => {
    const trimmed = query.trim();
    requestRef.current?.abort();
    const controller = new AbortController();
    requestRef.current = controller;
    setState(after ? "loading-more" : "loading");
    setError("");
    try {
      const opened = await new HttpArchiveRepositoryProvider().open({ research: { alias: "current" } }, { signal: controller.signal });
      if (!opened.ok) throw new Error(opened.error.message);
      const result = await opened.data.search({ q: trimmed, scope: "archive", sort: "relevance", first: 25, after }, { signal: controller.signal });
      if (!result.ok) throw new Error(result.error.message);
      if (controller.signal.aborted) return;
      setSubmittedQuery(trimmed);
      setItems((current) => after ? [...current, ...result.data.nodes] : result.data.nodes);
      setNextCursor(result.data.pageInfo.nextCursor);
      setTotal(result.data.pageInfo.totalExact ?? result.data.nodes.length);
      setAlgorithm(result.data.searchMetadata?.algorithmVersion ?? "deterministic lexical search");
      setState("ready");
    } catch (cause) {
      if (controller.signal.aborted) return;
      setState("error");
      setError(message(cause));
      if (!after) { setItems([]); setNextCursor(null); setTotal(0); }
    }
  }, []);

  useEffect(() => {
    setInput(urlQuery);
    if (urlQuery.trim()) void search(urlQuery);
    else { requestRef.current?.abort(); setSubmittedQuery(""); setItems([]); setNextCursor(null); setTotal(0); setState("idle"); setError(""); }
    return () => requestRef.current?.abort();
  }, [urlQuery, search]);

  function submitQuery() {
    const trimmed = input.trim();
    if (!trimmed || queryLength > 160) return;
    const next = `/search?q=${encodeURIComponent(trimmed)}`;
    if (trimmed === urlQuery.trim()) void search(trimmed);
    else router.push(next, { scroll: false });
  }

  function submit(event: FormEvent) { event.preventDefault(); submitQuery(); }
  function submitOnEnter(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key !== "Enter" || event.nativeEvent.isComposing) return;
    event.preventDefault();
    submitQuery();
  }

  function clear() {
    requestRef.current?.abort();
    setInput("");
    router.push("/search", { scroll: false });
  }

  return (
    <section className={`read-platform ${styles.workspace}`} aria-labelledby={titleId}>
      <p className="read-platform__eyebrow">Sealed public archive · v49</p>
      <h1 id={titleId}>Search the archive</h1>
      <p className={styles.intro}>Search 7,995 rights-safe public records by title or stable ID. Matching is lexical, deterministic, and explainable.</p>
      <form onSubmit={submit} className={`read-platform__form ${styles.form}`} role="search">
        <label htmlFor="archive-search">Title or stable ID</label>
        <div>
          <input id="archive-search" type="search" value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={submitOnEnter} autoComplete="off" aria-describedby="search-help search-count" />
          <button type="submit" disabled={state === "loading" || !input.trim() || queryLength > 160}>{state === "loading" ? "Searching…" : "Search"}</button>
          {input ? <button type="button" className={styles.secondaryButton} onClick={clear}>Clear</button> : null}
        </div>
        <small id="search-help">Try an exact or partial title, punctuation variant, or a small spelling error. All query words must match.</small>
        <small id="search-count" className={queryLength > 160 ? styles.invalid : undefined}>{queryLength}/160 characters</small>
      </form>

      <div className={styles.status} aria-live="polite" aria-atomic="true">
        {state === "loading" ? <p>Searching the frozen public release…</p> : null}
        {state === "error" ? <p role="alert">Search failed: {error} Try again.</p> : null}
        {state === "ready" && total === 0 ? <p>No public v49 records match “{submittedQuery}”. Try a shorter title fragment or check the spelling.</p> : null}
        {(state === "ready" || state === "loading-more") && total > 0 ? <p>{total.toLocaleString("en-US")} {total === 1 ? "result" : "results"} for “{submittedQuery}”</p> : null}
      </div>

      <ol className={`read-platform__results ${styles.results}`}>
        {items.map((hit) => (
          <li key={hit.surface.surfaceId}>
            <Link href={hit.route}>{hit.surface.title}</Link>
            <div className={styles.meta}><code>{hit.surface.surfaceId}</code><span>{hit.surface.deliveryState.replaceAll("_", " ")}</span></div>
            {hit.explanation ? <p className={styles.reason}><strong>{matchLabels[hit.explanation.matchType] ?? hit.explanation.matchType}</strong> · score {hit.explanation.score}</p> : null}
          </li>
        ))}
      </ol>

      {nextCursor ? <button type="button" className={styles.loadMore} disabled={state === "loading-more"} onClick={() => void search(submittedQuery, nextCursor)}>{state === "loading-more" ? "Loading…" : "Load more results"}</button> : null}
      {algorithm && items.length ? <p className={styles.algorithm}>Ranked by {algorithm}. Results expose public metadata only; no images are authorised in v49.</p> : null}
    </section>
  );
}
