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
import { searchArchiveSurfaces, type ArchiveSearchResult } from "@/lib/archive-search-client";
import {
  assistantPageKey,
  loadAssistantMessages,
  saveAssistantMessages,
  type StoredAssistantMessage,
} from "@/lib/assistant-memory";
import type {
  AssistantModelState,
  QwenGenerationTiming,
  QwenAssistantSession,
  QwenChatMessage,
} from "@/lib/qwen35-adapter";
import { ImgBadge, StatusChip } from "../primitives";

export type SearchMode = "search" | "assistant";

export interface AssistantContext {
  surfaceId?: string;
  title?: string;
  dateText?: string;
  imageState?: string;
  rightsLabel?: string;
  sourceName?: string;
  creator?: string;
  objectType?: string;
}

type AssistantMessage = StoredAssistantMessage;
const ASSISTANT_COLD_START_NOTICE_MS = 3000;

interface AssistantTimingLog {
  mode: "send" | "research";
  status: "answered" | "no_evidence" | "unavailable" | "error";
  intent: string;
  candidateCount: number;
  hasEvidence: boolean;
  questionChars: number;
  evidenceChars: number;
  retrievalMs: number;
  prepareMs?: number;
  askMs?: number;
  totalMs: number;
  qwen?: QwenGenerationTiming;
}

interface AssistantEvidenceResponse {
  hasEvidence: boolean;
  candidateCount: number;
  contextText: string;
  fallbackAnswer?: string;
  requestPlan: { intent: string };
}

function nowMs() {
  return typeof performance !== "undefined" ? performance.now() : Date.now();
}

function shouldLogAssistantTiming() {
  if (typeof window === "undefined") return false;
  if (process.env.NODE_ENV !== "production") return true;
  try {
    return window.localStorage.getItem("archive-assistant-timing") === "1";
  } catch {
    return false;
  }
}

function logAssistantTiming(timing: AssistantTimingLog) {
  if (!shouldLogAssistantTiming()) return;
  const rounded = {
    ...timing,
    retrievalMs: Math.round(timing.retrievalMs),
    prepareMs:
      timing.prepareMs === undefined ? undefined : Math.round(timing.prepareMs),
    askMs: timing.askMs === undefined ? undefined : Math.round(timing.askMs),
    totalMs: Math.round(timing.totalMs),
    qwen: timing.qwen
      ? {
          ...timing.qwen,
          tokenizeMs: Math.round(timing.qwen.tokenizeMs),
          generateMs: Math.round(timing.qwen.generateMs),
          decodeMs: Math.round(timing.qwen.decodeMs),
          totalMs: Math.round(timing.qwen.totalMs),
        }
      : undefined,
  };
  const target = window as typeof window & {
    __archiveAssistantTimings?: AssistantTimingLog[];
  };
  target.__archiveAssistantTimings = [
    ...(target.__archiveAssistantTimings ?? []),
    timing,
  ].slice(-20);
  console.info("[archive-assistant timing]", rounded);
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
  const [assistantModel, setAssistantModel] = useState<AssistantModelState>({
    status: "idle",
  });
  const [researchMode, setResearchMode] = useState(false);
  const [pendingMode, setPendingMode] = useState<"send" | "research" | null>(null);
  const [loadedMemoryKey, setLoadedMemoryKey] = useState("");
  const sessionRef = useRef<QwenAssistantSession | null>(null);
  const sessionPromiseRef = useRef<Promise<QwenAssistantSession> | null>(null);
  const loadingRef = useRef(false);
  const [results, setResults] = useState<ArchiveSearchResult[]>([]);
  const [searchPending, setSearchPending] = useState(false);
  const trimmed = query.trim();
  const isAssistant = mode === "assistant";
  const pageKey = useMemo(
    () => assistantPageKey(assistantContext),
    [assistantContext],
  );

  useEffect(() => {
    let active = true;
    if (!trimmed) {
      setResults([]);
      setSearchPending(false);
      return () => {
        active = false;
      };
    }
    setSearchPending(true);
    const handle = window.setTimeout(() => {
      void searchArchiveSurfaces(trimmed, 30)
        .then((matches) => {
          if (active) setResults(matches);
        })
        .catch(() => {
          if (active) setResults([]);
        })
        .finally(() => {
          if (active) setSearchPending(false);
        });
    }, 120);
    return () => {
      active = false;
      window.clearTimeout(handle);
    };
  }, [trimmed]);

  const prepareQwen = useCallback(async () => {
    if (!isAssistant) return null;
    if (sessionRef.current) return sessionRef.current;

    if (!sessionPromiseRef.current) {
      loadingRef.current = true;
      setAssistantModel({ status: "loading", message: "Preparing" });
      sessionPromiseRef.current = import("@/lib/qwen35-adapter")
        .then(({ createQwenAssistantSession }) => createQwenAssistantSession((message) =>
          setAssistantModel({
            status: "loading",
            message: message ? "Preparing" : "",
          }),
        ))
        .then((session) => {
          sessionRef.current = session;
          setAssistantModel({
            status: "ready",
            model: session.model,
            message: "Ready",
          });
          return session;
        })
        .catch((error) => {
          setAssistantModel({
            status: "error",
            message:
              error instanceof Error
                ? error.message
                : "Assistant failed to initialize.",
          });
          throw error;
        })
        .finally(() => {
          loadingRef.current = false;
          sessionPromiseRef.current = null;
        });
    }

    try {
      return await sessionPromiseRef.current;
    } catch {
      return null;
    }
  }, [isAssistant]);

  const clearQwenSession = useCallback(async () => {
    sessionRef.current = null;
    sessionPromiseRef.current = null;
    loadingRef.current = false;
    const { resetQwenAssistantSession } = await import("@/lib/qwen35-adapter");
    await resetQwenAssistantSession();
  }, []);

  useEffect(() => {
    if (!isAssistant || sessionRef.current || loadingRef.current) return;
    const handle = window.setTimeout(() => {
      void prepareQwen();
    }, 250);
    return () => window.clearTimeout(handle);
  }, [isAssistant, prepareQwen]);

  useEffect(() => {
    if (!isAssistant) return;
    setMessages(loadAssistantMessages(pageKey));
    setLoadedMemoryKey(pageKey);
  }, [isAssistant, pageKey]);

  useEffect(() => {
    if (!isAssistant || loadedMemoryKey !== pageKey) return;
    saveAssistantMessages(pageKey, messages);
  }, [isAssistant, loadedMemoryKey, messages, pageKey]);

  const askAssistant = async () => {
    const question = draft.trim();
    if (!question || pendingMode) return;

    const modeLabel: "send" | "research" = researchMode ? "research" : "send";
    const totalStarted = nowMs();
    const retrievalStarted = nowMs();
    const evidenceResponse = await fetch("/api/archive-assistant-evidence", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        question,
        research: researchMode,
        context: assistantContext,
      }),
    });
    if (!evidenceResponse.ok) throw new Error(`Archive evidence unavailable (${evidenceResponse.status})`);
    const evidence = await evidenceResponse.json() as AssistantEvidenceResponse;
    const retrievalMs = nowMs() - retrievalStarted;
    const baseTiming = {
      mode: modeLabel,
      intent: evidence.requestPlan.intent,
      candidateCount: evidence.candidateCount,
      hasEvidence: evidence.hasEvidence,
      questionChars: question.length,
      evidenceChars: evidence.contextText.length,
      retrievalMs,
    };
    const userMessage: AssistantMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: question,
      mode: modeLabel,
    };
    setMessages((current) => [...current, userMessage]);
    setDraft("");

    const history: QwenChatMessage[] = messages.map(({ role, content }) => ({
      role,
      content,
    }));

    if (!researchMode) {
      const assistantMessageId = `assistant-${Date.now()}`;
      if (!evidence.hasEvidence) {
        setMessages((current) => [
          ...current,
          {
            id: assistantMessageId,
            role: "assistant",
            content:
              evidence.fallbackAnswer ??
              "I do not have enough archive evidence to answer that without guessing.",
            mode: modeLabel,
          },
        ]);
        logAssistantTiming({
          ...baseTiming,
          status: "no_evidence",
          totalMs: nowMs() - totalStarted,
        });
        return;
      }

      setPendingMode(modeLabel);
      let noticeShown = false;
      const noticeTimer = window.setTimeout(() => {
        noticeShown = true;
        setPendingMode(null);
        setMessages((current) => [
          ...current,
          {
            id: assistantMessageId,
            role: "assistant",
            content:
              "Local Qwen is preparing. I’ll replace this with a short archive answer when the model is ready.",
            mode: modeLabel,
          },
        ]);
      }, ASSISTANT_COLD_START_NOTICE_MS);

      const commitAssistantAnswer = (content: string) => {
        const message: AssistantMessage = {
          id: assistantMessageId,
          role: "assistant",
          content,
          mode: modeLabel,
        };
        setMessages((current) =>
          current.some((item) => item.id === assistantMessageId)
            ? current.map((item) =>
                item.id === assistantMessageId ? message : item,
              )
            : [...current, message],
        );
      };

      try {
        const prepareStarted = nowMs();
        const session = await prepareQwen();
        const prepareMs = nowMs() - prepareStarted;
        window.clearTimeout(noticeTimer);
        if (!session) {
          commitAssistantAnswer(
            "Local Qwen is unavailable in this browser, so I cannot give an assistant answer here.",
          );
          logAssistantTiming({
            ...baseTiming,
            status: "unavailable",
            prepareMs,
            totalMs: nowMs() - totalStarted,
          });
          return;
        }

        setAssistantModel((state) => ({
          ...state,
          status: "loading",
          message: "Thinking",
        }));
        let qwenTiming: QwenGenerationTiming | undefined;
        const askStarted = nowMs();
        const response = await session.ask(question, assistantContext ?? undefined, {
          history,
          fast: true,
          evidence: evidence.contextText,
          onTiming: (timing) => {
            qwenTiming = timing;
          },
        });
        const askMs = nowMs() - askStarted;
        commitAssistantAnswer(
          response ||
            "I do not have enough archive context to answer that without guessing.",
        );
        setAssistantModel((state) => ({
          ...state,
          status: "ready",
          message: "Ready",
        }));
        logAssistantTiming({
          ...baseTiming,
          status: "answered",
          prepareMs,
          askMs,
          totalMs: nowMs() - totalStarted,
          qwen: qwenTiming,
        });
      } catch (error) {
        window.clearTimeout(noticeTimer);
        void clearQwenSession();
        setAssistantModel({
          status: "idle",
          message: "Ready to retry",
        });
        commitAssistantAnswer(
          error instanceof Error
            ? `Local Qwen could not answer: ${error.message}`
            : "Local Qwen could not answer this request.",
        );
        logAssistantTiming({
          ...baseTiming,
          status: "error",
          totalMs: nowMs() - totalStarted,
        });
      } finally {
        window.clearTimeout(noticeTimer);
        if (!noticeShown) setPendingMode(null);
      }
      return;
    }

    setPendingMode(modeLabel);

    if (!evidence.hasEvidence) {
      setMessages((current) => [
        ...current,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: evidence.fallbackAnswer ?? "No matching archive evidence.",
          mode: modeLabel,
        },
      ]);
      logAssistantTiming({
        ...baseTiming,
        status: "no_evidence",
        totalMs: nowMs() - totalStarted,
      });
      setPendingMode(null);
      return;
    }

    const prepareStarted = nowMs();
    const session = await prepareQwen();
    const prepareMs = nowMs() - prepareStarted;
    if (!session) {
      setMessages((current) => [
        ...current,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content:
            "Local Qwen is not ready in this browser. Close heavy tabs, reload the page, then try Research again.",
          mode: modeLabel,
        },
      ]);
      logAssistantTiming({
        ...baseTiming,
        status: "unavailable",
        prepareMs,
        totalMs: nowMs() - totalStarted,
      });
      setPendingMode(null);
      return;
    }

    setAssistantModel((state) => ({
      ...state,
      status: "loading",
      message: researchMode ? "Researching" : "Thinking",
    }));
    try {
      let qwenTiming: QwenGenerationTiming | undefined;
      const askStarted = nowMs();
      const response = await session.ask(question, assistantContext ?? undefined, {
        history,
        research: researchMode,
        evidence: evidence.contextText,
        onTiming: (timing) => {
          qwenTiming = timing;
        },
      });
      const askMs = nowMs() - askStarted;
      setMessages((current) => [
        ...current,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: response || "No response.",
          mode: modeLabel,
        },
      ]);
      setAssistantModel((state) => ({ ...state, status: "ready", message: "Ready" }));
      logAssistantTiming({
        ...baseTiming,
        status: "answered",
        prepareMs,
        askMs,
        totalMs: nowMs() - totalStarted,
        qwen: qwenTiming,
      });
    } catch (error) {
      void clearQwenSession();
      setMessages((current) => [
        ...current,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content:
            error instanceof Error
              ? `Research stopped: ${error.message}`
              : "Research stopped because local Qwen failed.",
          mode: modeLabel,
        },
      ]);
      setAssistantModel({
        status: "idle",
        model: session.model,
        message: "Ready to retry",
      });
      logAssistantTiming({
        ...baseTiming,
        status: "error",
        prepareMs,
        totalMs: nowMs() - totalStarted,
      });
    } finally {
      setPendingMode(null);
    }
  };

  const handleAssistantSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void askAssistant();
  };

  const assistantBusy = assistantModel.status === "loading";
  const assistantReady = assistantModel.status !== "loading";

  if (isAssistant) {
    return (
      <div
        className="corner-card search-card search-card--assistant flex flex-col"
        style={{ maxHeight: "inherit", overflow: "hidden" }}
      >
        <div className="search-card__head">
          <button
            type="button"
            className="assistant-mode-toggle label-caps"
            data-active={researchMode}
            aria-pressed={researchMode}
            onClick={() => setResearchMode((value) => !value)}
          >
            <span className="assistant-mode-toggle__idle">
              {researchMode ? "Research" : "Assistant"}
            </span>
            <span className="assistant-mode-toggle__hover">
              {researchMode ? "Assistant" : "Research"}
            </span>
          </button>
          <button
            type="button"
            onClick={onClose}
            className="label-caps text-ink-soft hover:text-ink"
            aria-label="Close assistant"
          >
            close ×
          </button>
        </div>

        <div className="assistant-thread panel-scroll" aria-live="polite">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`assistant-message assistant-message--${message.role}`}
            >
              <div className="assistant-message__meta label-caps">
                {message.role === "user"
                  ? message.mode === "research"
                    ? "Research"
                    : "You"
                  : "Assistant"}
              </div>
              <div>{message.content}</div>
            </div>
          ))}
          {assistantBusy && pendingMode ? (
            <div className="assistant-message assistant-message--assistant">
              <div className="assistant-message__meta label-caps">Assistant</div>
              <div>{pendingMode === "research" ? "Researching..." : "Thinking..."}</div>
            </div>
          ) : null}
        </div>

        <form className="assistant-compose" onSubmit={handleAssistantSubmit}>
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Ask about this work..."
          />
          <div className="assistant-actions">
            <button
              type="submit"
              className="btn-turn"
              disabled={
                !assistantReady ||
                draft.trim() === "" ||
                (researchMode && assistantBusy)
              }
            >
              {researchMode && assistantBusy && pendingMode ? "Working" : "Send"}
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
          : searchPending
            ? "Searching compact archive index…"
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
      <Link
        href={`/search${trimmed ? `?q=${encodeURIComponent(trimmed)}` : ""}`}
        className="block border-t border-ink pt-2 mt-2 label-caps text-ink hover:bg-paper-2"
        style={{ fontSize: "0.6rem" }}
      >
        Open full archive + TRACE search →
      </Link>
    </div>
  );
}
