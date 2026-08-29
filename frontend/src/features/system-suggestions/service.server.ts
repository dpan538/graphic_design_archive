import "server-only";

import { approvedCandidates } from "./candidates.server";
import {
  DEEPSEEK_DEFAULT_BASE_URL,
  DEEPSEEK_DEFAULT_MODEL,
  DeepSeekGuidanceProvider,
  StaticFallbackProvider,
  SYSTEM_SUGGESTIONS_PROMPT_VERSION,
  type ProviderDraft,
} from "./providers.server";
import { parseSystemSuggestionsRequest } from "./schema.server";
import type { ApprovedSuggestion, SystemSuggestionsRequest, SystemSuggestionsResponse } from "./types";

type Environment = Readonly<Record<string, string | undefined>>;
type ServiceDependencies = { environment?: Environment; fetchImpl?: typeof fetch; timeoutMsForTest?: number };

class UnsafeProviderOutput extends Error {}

function environmentConfig(environment: Environment, timeoutMsForTest?: number) {
  const mode = environment.SYSTEM_SUGGESTIONS_PROVIDER?.trim().toLowerCase() || "auto";
  const rawTimeout = Number(environment.SYSTEM_SUGGESTIONS_TIMEOUT_MS ?? "2500");
  const timeoutMs = timeoutMsForTest ?? (Number.isFinite(rawTimeout) ? Math.min(5000, Math.max(250, Math.trunc(rawTimeout))) : 2500);
  const requestedBase = environment.DEEPSEEK_BASE_URL?.trim() || DEEPSEEK_DEFAULT_BASE_URL;
  const requestedModel = environment.DEEPSEEK_MODEL?.trim() || DEEPSEEK_DEFAULT_MODEL;
  return {
    mode: ["auto", "static", "off", "deepseek"].includes(mode) ? mode : "auto",
    apiKey: environment.DEEPSEEK_API_KEY?.trim() ?? "",
    baseUrl: requestedBase === DEEPSEEK_DEFAULT_BASE_URL ? requestedBase : DEEPSEEK_DEFAULT_BASE_URL,
    model: requestedModel === DEEPSEEK_DEFAULT_MODEL ? requestedModel : DEEPSEEK_DEFAULT_MODEL,
    timeoutMs,
  };
}

function safeDraft(draft: ProviderDraft, candidates: readonly ApprovedSuggestion[], request: SystemSuggestionsRequest): ProviderDraft {
  const note = draft.note.normalize("NFC").trim();
  const codePoints = Array.from(note).length;
  const sentenceCount = (note.match(/[.!?](?:\s|$)/g) ?? []).length;
  if (!note || codePoints > 320 || sentenceCount > 2 || /(?:https?:\/\/|www\.|\[[^\]]+\]\(|^#{1,6}\s)/im.test(note)) throw new UnsafeProviderOutput("unsafe note format");
  if (/\b(?:I|me|my|mine|we|our|ours)\b/i.test(note) || /\b(?:prove[ds]?|proven|establish(?:es|ed)?)\b.{0,48}\b(?:relation|association|caus|histor)/i.test(note)) throw new UnsafeProviderOutput("unsafe note claim");
  if (draft.suggestionIds.length > 4 || new Set(draft.suggestionIds).size !== draft.suggestionIds.length) throw new UnsafeProviderOutput("invalid suggestion count");
  if (request.surface === "SEARCH_RESULTS" && candidates.length >= 2 && draft.suggestionIds.length < 2) throw new UnsafeProviderOutput("Search guidance requires at least two approved suggestions when available");
  const allow = new Set(candidates.map((candidate) => candidate.id));
  if (draft.suggestionIds.some((id) => !allow.has(id))) throw new UnsafeProviderOutput("unapproved suggestion id");
  return { note, suggestionIds: draft.suggestionIds };
}

function responseFrom(request: SystemSuggestionsRequest, draft: ProviderDraft, candidates: readonly ApprovedSuggestion[], sourceClass: SystemSuggestionsResponse["sourceClass"], providerStatus: string): SystemSuggestionsResponse {
  const byId = new Map(candidates.map((candidate) => [candidate.id, candidate]));
  return {
    schemaVersion: "gda-system-suggestions-response/v1",
    surface: request.surface,
    stateHash: request.stateHash,
    note: draft.note,
    suggestions: draft.suggestionIds.map((id) => byId.get(id)).filter((candidate): candidate is ApprovedSuggestion => Boolean(candidate)),
    sourceClass,
    promptVersion: SYSTEM_SUGGESTIONS_PROMPT_VERSION,
    providerStatus,
  };
}

async function fallback(request: SystemSuggestionsRequest, candidates: readonly ApprovedSuggestion[], providerStatus: string): Promise<SystemSuggestionsResponse> {
  const provider = new StaticFallbackProvider();
  const draft = safeDraft(await provider.generate({ request, candidates }), candidates, request);
  return responseFrom(request, draft, candidates, "STATIC_FALLBACK", providerStatus);
}

export async function createSystemSuggestions(rawRequest: unknown, dependencies: ServiceDependencies = {}): Promise<SystemSuggestionsResponse> {
  const request = parseSystemSuggestionsRequest(rawRequest);
  const candidates = approvedCandidates(request);
  const environment = dependencies.environment ?? process.env;
  const config = environmentConfig(environment, dependencies.timeoutMsForTest);
  if (config.mode === "static" || config.mode === "off") return fallback(request, candidates, "PROVIDER_DISABLED");
  if (!config.apiKey) return fallback(request, candidates, "NO_KEY");
  const provider = new DeepSeekGuidanceProvider({
    apiKey: config.apiKey,
    baseUrl: config.baseUrl,
    model: config.model,
    timeoutMs: config.timeoutMs,
    fetchImpl: dependencies.fetchImpl ?? fetch,
  });
  try {
    const draft = safeDraft(await provider.generate({ request, candidates }), candidates, request);
    return responseFrom(request, draft, candidates, "MODEL", "MODEL_OK");
  } catch (error) {
    const status = error instanceof UnsafeProviderOutput || (error instanceof SyntaxError) ? "INVALID_RESPONSE"
      : error instanceof Error && error.name === "AbortError" ? "TIMEOUT"
      : "PROVIDER_ERROR";
    return fallback(request, candidates, status);
  }
}
