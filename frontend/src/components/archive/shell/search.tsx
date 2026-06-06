"use client";

import {
  FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import Link from "next/link";
import { fuzzySearchSurfaces } from "@/lib/archive-data";
import {
  createWebLLMSession,
  type WebLLMChatMessage,
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

interface AssistantMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  mode?: "send" | "research";
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
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<AssistantMessage[]>([]);
  const [webllm, setWebllm] = useState<WebLLMState>({ status: "idle" });
  const [pendingMode, setPendingMode] = useState<"send" | "research" | null>(null);
  const sessionRef = useRef<WebLLMSession | null>(null);
  const loadingRef = useRef(false);
  const results = useMemo(() => fuzzySearchSurfaces(query), [query]);
  const trimmed = query.trim();
  const isAssistant = mode === "assistant";

  const prepareWebLLM = useCallback(async () => {
    if (!isAssistant || sessionRef.current || loadingRef.current) return;
    loadingRef.current = true;
    setWebllm({ status: "loading", message: "Preparing WebLLM" });
    try {
      const session = await createWebLLMSession((message) =>
        setWebllm({ status: "loading", message }),
      );
      sessionRef.current = session;
      setWebllm({
        status: "ready",
        model: session.model,
        message: "Ready",
      });
    } catch (error) {
      setWebllm({
        status: "error",
        message:
          error instanceof Error
            ? error.message
            : "WebLLM failed to initialize.",
      });
    } finally {
      loadingRef.current = false;
    }
  }, [isAssistant]);

  useEffect(() => {
    if (isAssistant) void prepareWebLLM();
  }, [isAssistant, prepareWebLLM]);

  const askAssistant = async (research = false) => {
    const question = draft.trim();
    if (!question) return;
    if (!sessionRef.current) {
      await prepareWebLLM();
    }
    const session = sessionRef.current;
    if (!session) return;

    const modeLabel = research ? "research" : "send";
    const history: WebLLMChatMessage[] = messages.map(({ role, content }) => ({
      role,
      content,
    }));
    const userMessage: AssistantMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: question,
      mode: modeLabel,
    };
    setMessages((current) => [...current, userMessage]);
    setDraft("");
    setPendingMode(modeLabel);
    setWebllm((state) => ({
      ...state,
      status: "loading",
      message: research ? "Researching" : "Thinking",
    }));
    try {
      const response = await session.ask(question, assistantContext ?? undefined, {
        history,
        research,
      });
      setMessages((current) => [
        ...current,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: response || "No response.",
          mode: modeLabel,
        },
      ]);
      setWebllm((state) => ({ ...state, status: "ready", message: "Ready" }));
    } catch (error) {
      setWebllm({
        status: "error",
        model: session.model,
        message: error instanceof Error ? error.message : "Assistant request failed.",
      });
    } finally {
      setPendingMode(null);
    }
  };

  const handleAssistantSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void askAssistant(false);
  };

  const assistantBusy = webllm.status === "loading";
  const assistantReady = webllm.status === "ready";
  const assistantUnavailable = webllm.status === "error";
  const assistantStatus = webllm.message ?? (assistantReady ? "Ready" : "Preparing");

  if (isAssistant) {
    return (
      <div
        className="corner-card search-card search-card--assistant flex flex-col"
        style={{ maxHeight: "inherit", overflow: "hidden" }}
      >
        <div className="search-card__head">
          <span className="label-caps">Assistant</span>
          <button
            type="button"
            onClick={onClose}
            className="label-caps text-ink-soft hover:text-ink"
            aria-label="Close assistant"
          >
            close ×
          </button>
        </div>

        <section className="assistant-brief" aria-label="Assistant context">
          <div className="assistant-brief__status">
            <span className="label-caps">WebLLM</span>
            <span>{assistantStatus}</span>
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

        <div className="assistant-thread panel-scroll" aria-live="polite">
          {messages.length === 0 ? (
            <div className="assistant-empty">
              No messages yet.
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`assistant-message assistant-message--${message.role}`}
              >
                <div className="assistant-message__meta label-caps">
                  {message.role === "user"
                    ? message.mode === "research"
                      ? "Research"
                      : "You"
                    : "WebLLM"}
                </div>
                <div>{message.content}</div>
              </div>
            ))
          )}
        </div>

        <form className="assistant-compose" onSubmit={handleAssistantSubmit}>
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Ask about this work..."
            disabled={assistantUnavailable}
          />
          <div className="assistant-actions">
            <button
              type="submit"
              className="btn-turn"
              disabled={!assistantReady || draft.trim() === "" || assistantBusy}
            >
              Send
            </button>
            <button
              type="button"
              className="btn-turn"
              onClick={() => void askAssistant(true)}
              disabled={!assistantReady || draft.trim() === "" || assistantBusy}
            >
              {pendingMode === "research" ? "Researching" : "Research"}
            </button>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div
      className="corner-card search-card flex flex-col"
      style={{ maxHeight: "inherit", overflow: "hidden" }}
    >
      <div className="search-card__head">
        <span className="label-caps">Search</span>
        <button
          type="button"
          onClick={onClose}
          className="label-caps text-ink-soft hover:text-ink"
          aria-label="Close search"
        >
          close ×
        </button>
      </div>

      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="title, creator, source..."
        className="w-full bg-paper border-[1.5px] border-ink px-2 py-1.5 font-mono text-sm outline-none focus:bg-paper-2"
        autoComplete="off"
        // eslint-disable-next-line jsx-a11y/no-autofocus
        autoFocus
      />
      <div className="text-ink-soft mt-1.5" style={{ fontSize: "0.56rem" }}>
        {trimmed === ""
          ? "Fuzzy match over titles, creators, sources & tables"
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
