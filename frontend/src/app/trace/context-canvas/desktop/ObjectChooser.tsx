"use client";

import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
import type { GovernedContextExampleOption, GovernedContextSampleOption } from "@/features/trace-v49/context/governed/types";
import {
  CHANGE_OBJECT,
  CHOOSE_TITLE,
  CONTEXTS_COUNT,
  EXAMPLES_TITLE,
  EXAMPLE_ROLE,
  LOAD_RECORD,
  OPEN_BY_ID,
  QA_NOTE,
  QA_TITLE,
  RECORD_ID_LABEL,
  RECORD_ID_NOTE,
  RECORD_ID_PLACEHOLDER,
  RECORD_ONLY,
  SEARCH_FAILED,
  SEARCH_HINT,
  SEARCH_LABEL,
  SEARCH_NONE,
  SEARCH_PLACEHOLDER,
  SEARCH_RESULTS,
  SEARCH_SEARCHING,
} from "../lib/content";
import styles from "./ObjectChooser.module.css";

/* 01 — choosing the object (§7g): the reader's way into the canvas. A
   search by title (reader-facing objects only; case and diacritics do
   not matter) or by public record ID; a few worked examples the reader
   picked from the data by fixed criteria; the exact public record ID
   behind a fold, for a researcher who knows it — every governed public
   record, record-only ones included. The projection's twelve
   deterministic samples are a QA tool: shown in development or with
   ?qa=1, under their own fold, and never called a reader's sample.
   Every choice is a link to ?record=, a plain navigation; the title is
   what a result is known by, the ID its second line. Keyboard: the
   search box, arrow down into the results, Enter opens. */

export interface ChooserResult {
  readonly stableId: string;
  readonly title: string;
  readonly readerFacing: boolean;
  readonly contexts: number;
}

export interface ObjectChooserProps {
  readonly examples: readonly GovernedContextExampleOption[];
  readonly qaSamples: readonly GovernedContextSampleOption[] | null;
  readonly cohort: string;
  readonly requestedId: string;
  readonly open: boolean;
  readonly standalone: boolean;
}

const SEARCH_URL = "/api/trace/v1/context-objects";
const hrefFor = (stableId: string) => `/trace/context-canvas?record=${encodeURIComponent(stableId)}`;

export default function ObjectChooser({ examples, qaSamples, cohort, requestedId, open: initiallyOpen, standalone }: ObjectChooserProps) {
  const [open, setOpen] = useState(initiallyOpen || standalone);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<readonly ChooserResult[] | null>(null);
  const [state, setState] = useState<"idle" | "searching" | "done" | "failed">("idle");
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const baseId = useId();
  const listId = `${baseId}-results`;

  /* the search: a short wait after typing, the last request wins */
  useEffect(() => {
    const trimmed = query.trim();
    const isId = /^surf/iu.test(trimmed);
    if (trimmed.length < 2 && !isId) {
      setResults(null);
      setState("idle");
      return;
    }
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setState("searching");
      try {
        const response = await fetch(`${SEARCH_URL}?q=${encodeURIComponent(trimmed)}`, { signal: controller.signal });
        if (!response.ok) throw new Error(String(response.status));
        const payload = (await response.json()) as { results: readonly ChooserResult[] };
        setResults(payload.results);
        setState("done");
      } catch (error) {
        if ((error as Error).name === "AbortError") return;
        setResults(null);
        setState("failed");
      }
    }, 180);
    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [query]);

  function onInputKey(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key !== "ArrowDown") return;
    const first = listRef.current?.querySelector<HTMLAnchorElement>("a");
    if (!first) return;
    event.preventDefault();
    first.focus();
  }

  function onListKey(event: KeyboardEvent<HTMLUListElement>) {
    if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
    const links = [...(listRef.current?.querySelectorAll<HTMLAnchorElement>("a") ?? [])];
    const index = links.findIndex((link) => link === document.activeElement);
    if (index < 0) return;
    event.preventDefault();
    if (event.key === "ArrowUp" && index === 0) inputRef.current?.focus();
    else links[Math.min(links.length - 1, Math.max(0, index + (event.key === "ArrowDown" ? 1 : -1)))]?.focus();
  }

  const heading = standalone ? CHOOSE_TITLE : CHANGE_OBJECT;

  return (
    <section className={styles.chooser} data-standalone={standalone ? "true" : "false"} aria-labelledby={`${baseId}-heading`}>
      {standalone ? (
        <h2 id={`${baseId}-heading`} className={styles.heading}>{heading}</h2>
      ) : (
        <h2 className={styles.headingRow}>
          <button
            id={`${baseId}-heading`}
            type="button"
            className={styles.toggle}
            aria-expanded={open}
            aria-controls={`${baseId}-body`}
            onClick={() => setOpen((current) => !current)}
          >
            <span aria-hidden="true">{open ? "−" : "+"}</span> {heading}
          </button>
        </h2>
      )}

      {open ? (
        <div id={`${baseId}-body`} className={styles.body}>
          <div className={styles.search}>
            <label htmlFor="context-object-search" className={styles.label}>{SEARCH_LABEL}</label>
            <input
              ref={inputRef}
              id="context-object-search"
              className={styles.input}
              type="search"
              value={query}
              placeholder={SEARCH_PLACEHOLDER}
              autoComplete="off"
              spellCheck={false}
              aria-describedby={`${baseId}-hint`}
              aria-controls={listId}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={onInputKey}
            />
            <p id={`${baseId}-hint`} className={styles.hint} aria-live="polite">
              {state === "idle" ? SEARCH_HINT
                : state === "searching" ? SEARCH_SEARCHING
                  : state === "failed" ? SEARCH_FAILED
                    : results && results.length > 0 ? SEARCH_RESULTS(results.length) : SEARCH_NONE(query.trim())}
            </p>
            {results && results.length > 0 ? (
              <ul id={listId} ref={listRef} role="list" className={styles.results} onKeyDown={onListKey}>
                {results.map((result) => (
                  <li key={result.stableId}>
                    <a className={styles.result} href={hrefFor(result.stableId)}>
                      <span className={styles.resultTitle}>{result.title.trim() || result.stableId}</span>
                      <span className={`${styles.resultMeta} tnum`}>
                        {result.stableId} · {CONTEXTS_COUNT(result.contexts)}{result.readerFacing ? "" : ` · ${RECORD_ONLY}`}
                      </span>
                    </a>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>

          {examples.length > 0 ? (
            <div className={styles.examples}>
              <h3 className={styles.label}>{EXAMPLES_TITLE}</h3>
              <ul role="list" className={styles.results}>
                {examples.map((example) => (
                  <li key={example.stableId}>
                    <a className={styles.result} href={hrefFor(example.stableId)} aria-current={example.stableId === requestedId ? "page" : undefined}>
                      <span className={styles.resultTitle}>{example.title.trim() || example.stableId}</span>
                      <span className={styles.resultRole}>{EXAMPLE_ROLE[example.role] ?? example.role}</span>
                      <span className={`${styles.resultMeta} tnum`}>{example.stableId}</span>
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <details className={styles.fold}>
            <summary className={styles.summary}>{OPEN_BY_ID}</summary>
            <form action="/trace/context-canvas" method="get" className={styles.form}>
              <label htmlFor={`${baseId}-record`} className={styles.label}>{RECORD_ID_LABEL}</label>
              <input
                id={`${baseId}-record`}
                className={`${styles.input} tnum`}
                name="record"
                defaultValue={requestedId}
                maxLength={80}
                pattern="SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*"
                autoComplete="off"
                spellCheck={false}
                placeholder={RECORD_ID_PLACEHOLDER}
              />
              <p className={styles.hint}>{RECORD_ID_NOTE}</p>
              <button type="submit" className={styles.button}>{LOAD_RECORD}</button>
            </form>
          </details>

          {qaSamples && qaSamples.length > 0 ? (
            <details className={styles.fold} data-qa="true">
              <summary className={styles.summary}>{QA_TITLE}</summary>
              <p className={styles.hint}>{QA_NOTE(String(qaSamples.length), cohort)}</p>
              <ol className={styles.qaList}>
                {qaSamples.map((sample) => (
                  <li key={sample.stableId}>
                    <a className={styles.qaLink} href={hrefFor(sample.stableId)}>
                      <span className={styles.resultTitle}>{sample.title.trim() || sample.stableId}</span>
                      <span className={`${styles.resultMeta} tnum`}>{sample.stableId}</span>
                    </a>
                  </li>
                ))}
              </ol>
            </details>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
