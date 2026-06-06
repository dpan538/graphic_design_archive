"use client";

import { FormEvent, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { fuzzySearchSurfaces } from "@/lib/archive-data";
import {
  createWebLLMSession,
  type WebLLMSession,
  type WebLLMState,
} from "@/lib/webllm-adapter";
import { ImgBadge, StatusChip } from "../primitives";

export type SearchMode = "search" | "assistant";

export interface AssistantContext {
  title?: string;
  dateText?: string;
  imageState?: string;
  rightsLabel?: string;
  sourceName?: string;
  creator?: string;
  objectType?: string;
}

/**
 * In-shell fuzzy search. Lives on the right (same width as the counts card),
 * not on a separate page. Deterministic, local-only (substring + subsequence).
 */
export default function SearchBox({
  mode = "search",
  assistantContext,
  onClose,
}: {
  mode?: SearchMode;
  assistantContext?: AssistantContext | null;
  onClose?: () => void;
}) {
  const [query, setQuery] = useState("");
  const [prompt, setPrompt] = useState("");
  const [answer, setAnswer] = useState("");
  const [webllm, setWebllm] = useState<WebLLMState>({ status: "idle" });
  const sessionRef = useRef<WebLLMSession | null>(null);
  const results = useMemo(() => fuzzySearchSurfaces(query), [query]);
  const trimmed = query.trim();
  const isAssistant = mode === "assistant";

  const loadWebLLM = async () => {
    setWebllm({ status: "loading", message: "Loading WebLLM runtime" });
    setAnswer("");
    try {
      const session = await createWebLLMSession((message) =>
        setWebllm({ status: "loading", message }),
      );
      sessionRef.current = session;
      setWebllm({
        status: "ready",
        model: session.model,
        message: "WebLLM ready",
      });
    } catch (error) {
      setWebllm({
        status: "error",
        message:
          error instanceof Error
            ? error.message
            : "WebLLM failed to initialize.",
      });
    }
  };

  const askAssistant = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const question = prompt.trim();
    if (!question || !sessionRef.current) return;
    setWebllm((state) => ({ ...state, status: "loading", message: "Thinking" }));
    setAnswer("");
    try {
      const response = await sessionRef.current.ask(question, assistantContext ?? undefined);
      setAnswer(response || "No response.");
      setWebllm((state) => ({ ...state, status: "ready", message: "WebLLM ready" }));
    } catch (error) {
      setWebllm({
        status: "error",
        model: sessionRef.current.model,
        message: error instanceof Error ? error.message : "Assistant request failed.",
      });
    }
  };

  return (
    <div
      className="corner-card search-card flex flex-col"
      style={{ maxHeight: "inherit", overflow: "hidden" }}
    >
      <div className="search-card__head">
        <span className="label-caps">{isAssistant ? "Assistant" : "Search"}</span>
        <button
          type="button"
          onClick={onClose}
          className="label-caps text-ink-soft hover:text-ink"
          aria-label={isAssistant ? "Close assistant" : "Close search"}
        >
          close ×
        </button>
      </div>

      {isAssistant ? (
        <>
          <section className="assistant-brief" aria-label="Assistant context">
            <div className="assistant-brief__status">
              <span className="label-caps">WebLLM</span>
              <span>{webllm.message ?? "Not loaded"}</span>
            </div>
            <h3>{assistantContext?.title ?? "Archive research assistant"}</h3>
            <dl>
              <div>
                <dt>Date</dt>
                <dd>{assistantContext?.dateText ?? "Current folder"}</dd>
              </div>
              <div>
                <dt>Image</dt>
                <dd>{assistantContext?.imageState ?? "Mixed"}</dd>
              </div>
              <div>
                <dt>Source</dt>
                <dd>{assistantContext?.sourceName ?? "Archive index"}</dd>
              </div>
            </dl>
          </section>

          <form className="assistant-compose" onSubmit={askAssistant}>
            <textarea
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              placeholder="Ask about this record, source trail, rights evidence, or packet structure."
              disabled={webllm.status !== "ready"}
            />
            <div className="assistant-actions">
              <button
                type="button"
                className="btn-turn"
                onClick={loadWebLLM}
                disabled={webllm.status === "loading"}
              >
                Load WebLLM
              </button>
              <button
                type="submit"
                className="btn-turn"
                disabled={webllm.status !== "ready" || prompt.trim() === ""}
              >
                Ask
              </button>
            </div>
          </form>

          {answer ? <div className="assistant-answer">{answer}</div> : null}
        </>
      ) : null}

      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={isAssistant ? "reference lookup..." : "title, creator, source..."}
        className="w-full bg-paper border-[1.5px] border-ink px-2 py-1.5 font-mono text-sm outline-none focus:bg-paper-2"
        autoComplete="off"
        // eslint-disable-next-line jsx-a11y/no-autofocus
        autoFocus
      />
      <div className="text-ink-soft mt-1.5" style={{ fontSize: "0.56rem" }}>
        {trimmed === ""
          ? isAssistant
            ? "Optional reference lookup over archive records."
            : "Fuzzy match over titles, creators, sources & tables"
          : `${results.length} ${results.length === 1 ? "match" : "matches"}`}
      </div>

      <div className="mt-1.5 -mx-1 px-1 overflow-y-auto panel-scroll flex-1 min-h-0">
        {trimmed !== "" && results.length === 0 ? (
          <p className="text-ink-soft py-2" style={{ fontSize: "0.66rem" }}>
            No matches for “{trimmed}”.
          </p>
        ) : (
          results.slice(0, 30).map(({ surface, field, snippet }) => (
            <Link
              key={surface.surfaceId}
              href={`/surfaces/${surface.surfaceId}`}
              className="block border-t border-line-soft py-1.5 hover:bg-paper-2"
            >
              <div className="flex items-center gap-2" style={{ fontSize: "0.56rem" }}>
                <StatusChip kind={surface.surfaceType} />
                <ImgBadge state={surface.image.state} />
                <span className="text-ink-soft">{surface.dateText}</span>
              </div>
              <div className="font-bold leading-tight" style={{ fontSize: "0.74rem" }}>
                {surface.title}
              </div>
              <div className="text-ink-soft" style={{ fontSize: "0.58rem" }}>
                <span className="label-caps">{field}</span> · {snippet}
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
