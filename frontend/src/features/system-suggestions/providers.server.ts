import "server-only";

import { MAX_ACTIONS } from "./candidates.server";
import type { SurfaceFacts } from "./facts.server";
import type { ApprovedSuggestion, SystemSuggestionsRequest } from "./types";

export const DEEPSEEK_DEFAULT_BASE_URL = "https://api.deepseek.com";
export const DEEPSEEK_RESPONSES_PATH = "/responses";
export const DEEPSEEK_DEFAULT_MODEL = "deepseek-v4-flash";
/* the release pass prompt: the model composes from fact statements (facts.server.ts) */
export const SYSTEM_SUGGESTIONS_PROMPT_VERSION = "gda-system-suggests-facts-v2";
export const SYSTEM_SUGGESTIONS_MAX_WORDS = 45;
export const SYSTEM_SUGGESTIONS_MAX_SENTENCES = 2;
export const SYSTEM_SUGGESTIONS_MAX_OUTPUT_TOKENS = 512;
export const SYSTEM_SUGGESTIONS_LANGUAGE = "en";

/* ---- the frozen reference contracts (kept for the v1 contexts; never sent to a model) ---- */
export const SPACETIME_GUIDANCE_PROMPT_VERSION = "gda-spacetime-guidance-v1";
export const SPACETIME_GUIDANCE_MAX_WORDS = 60;
export const SPACETIME_GUIDANCE_MAX_SENTENCES = 3;
export const SPACETIME_GUIDANCE_MAX_ACTIONS = 2;
export const EXPLORATION_NARRATION_PROMPT_VERSION = "gda-exploration-narration-v1";
export const EXPLORATION_NARRATION_MAX_WORDS = 45;
export const EXPLORATION_NARRATION_MAX_SENTENCES = 2;
export const EXPLORATION_NARRATION_MAX_ACTIONS = 1;

export function spacetimeFallbackNote(context: { labels?: readonly string[]; counts?: Readonly<Record<string, number>> }): string {
  const labels = context.labels ?? [];
  const counts = context.counts ?? {};
  const period = labels[0] ?? "the selected period";
  const geography = labels[1];
  const fmt = (value: number) => value.toLocaleString("en-US");
  const ordinal = (rank: number) => ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth"][rank - 1] ?? `${fmt(rank)}th`;
  if (!geography || !(counts.selectedRecords > 0)) {
    return `The ${period} carry ${fmt(counts.publicDenominator ?? 0)} public records; select a place to read its share.`;
  }
  const rank = counts.selectedRank > 0 && counts.geographyCount > 0 ? `, ranking ${ordinal(counts.selectedRank)} among ${fmt(counts.geographyCount)} recorded geographies` : "";
  const first = `${geography} accounts for ${fmt(counts.selectedRecords)} of ${fmt(counts.publicDenominator ?? 0)} public records in the ${period}${rank}.`;
  const previousLabel = labels.find((label) => /^\d{4}s$/u.test(label) && label !== period);
  const share = counts.publicDenominator > 0 ? counts.selectedRecords / counts.publicDenominator : 0;
  const previousShare = counts.previousPeriodRecords > 0 ? counts.previousSelectedRecords / counts.previousPeriodRecords : null;
  const second = previousShare === null || !previousLabel
    ? ""
    : share > previousShare
      ? ` Its share of the public archive is larger here than in the ${previousLabel}.`
      : share < previousShare
        ? ` Its share of the public archive is smaller here than in the ${previousLabel}.`
        : ` Its share of the public archive is the same as in the ${previousLabel}.`;
  return `${first}${second}`;
}

export function explorationFallbackNote(context: { labels?: readonly string[]; counts?: Readonly<Record<string, number>> }): string {
  const labels = context.labels ?? [];
  const counts = context.counts ?? {};
  const terms = counts.visibleTerms ?? 0;
  const associations = counts.qualifiedAssociations ?? 0;
  const seed = labels[0];
  const others = labels.slice(1, 1 + Math.max(0, terms - 1)).filter((label) => label !== seed);
  const word = associations === 1 ? "qualified generic association" : "qualified generic associations";
  const number = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight"][associations] ?? String(associations);
  if (!seed || others.length === 0) return `This view contains ${terms} ${terms === 1 ? "term" : "terms"} and ${number} ${word}.`;
  const list = others.length === 1 ? others[0] : `${others.slice(0, -1).join(", ")} and ${others[others.length - 1]}`;
  const capital = seed.charAt(0).toUpperCase() + seed.slice(1);
  return `${capital} is shown here alongside ${list} through ${number} evidence-qualified generic ${associations === 1 ? "association" : "associations"}.`;
}

export function openInquiryFallbackNote(context: { labels?: readonly string[]; counts?: Readonly<Record<string, number>> }): string {
  const participants = context.counts?.participants ?? 0;
  const labels = (context.labels ?? []).slice(0, participants > 0 ? participants : undefined).filter((label) => label.length > 0);
  if (labels.length >= 2) {
    const list = `${labels.slice(0, -1).join(", ")} and ${labels[labels.length - 1]}`;
    return `This inquiry considers a bounded question between ${list}; it remains outside the validated graph because its evidence is incomplete.`;
  }
  return "This inquiry remains outside the validated graph because its evidence is incomplete.";
}

export function isExplorationNarration(request: SystemSuggestionsRequest): boolean {
  const counts = (request.context as { counts?: Readonly<Record<string, number>> }).counts ?? {};
  if (request.surface === "TRACE_VALIDATED_EXPLORATION") return (counts.visibleTerms ?? 0) > 0;
  if (request.surface === "TRACE_OPEN_INQUIRY") return (counts.participants ?? 0) > 0;
  return false;
}

/* the v1 deterministic notes, by surface */
export function legacyFallbackNote(request: SystemSuggestionsRequest): string {
  if (request.surface === "SEARCH_RESULTS") {
    const context = request.context as { exactResultCount: number };
    if (context.exactResultCount === 0) return "No public objects match this Search. Broaden the text or remove one filter to continue.";
    return `${context.exactResultCount.toLocaleString("en-US")} public ${context.exactResultCount === 1 ? "object matches" : "objects match"}. Use a suggested refinement to examine a smaller part of the result set.`;
  }
  if (request.surface === "TRACE_CONTEXT") return "Review the current public context, then choose an available context action to continue.";
  if (request.surface === "TRACE_SPACETIME") return spacetimeFallbackNote(request.context as { labels?: readonly string[]; counts?: Readonly<Record<string, number>> });
  if (request.surface === "TRACE_VALIDATED_EXPLORATION") {
    const context = request.context as { labels?: readonly string[]; counts?: Readonly<Record<string, number>> };
    if ((context.counts?.visibleTerms ?? 0) > 0) return explorationFallbackNote(context);
    return (context.counts?.validatedCompositions ?? 0) === 0
      ? "No validated composition is active in this release. No validated next action is available."
      : "Continue from the current validated composition using only the available validated nodes and associations.";
  }
  const inquiry = request.context as { labels?: readonly string[]; counts?: Readonly<Record<string, number>> };
  if ((inquiry.counts?.participants ?? 0) > 0) return openInquiryFallbackNote(inquiry);
  return "Review the stated evidence gap and source boundary before choosing an available inquiry action.";
}

/* ---- v2: the deterministic note from the facts ---- */
const countWords = (text: string): number => text.split(/\s+/).filter(Boolean).length;
export function factsFallbackNote(facts: SurfaceFacts): string {
  const text = (id: string) => facts.statements.find((item) => item.id === id)?.text ?? "";
  const join = (...parts: string[]) => parts.filter(Boolean).join(" ");
  switch (facts.surface) {
    case "SEARCH_RESULTS": {
      const first = text("S1");
      const second = text("S2");
      return second && countWords(join(first, second)) <= SYSTEM_SUGGESTIONS_MAX_WORDS ? join(first, second) : first;
    }
    case "TRACE_CONTEXT": {
      const first = text("C1");
      const dimension = facts.statements.find((item) => /^C[2-4]$/u.test(item.id) && !item.text.startsWith("No "))?.text ?? text("C2");
      return countWords(join(first, dimension)) <= SYSTEM_SUGGESTIONS_MAX_WORDS ? join(first, dimension) : first;
    }
    case "TRACE_VALIDATED_EXPLORATION": {
      if (facts.pairs.length === 1) return text("E3");
      const seedLine = text("E2");
      const count = facts.counts.qualifiedAssociations ?? 0;
      const number = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight"][count] ?? String(count);
      if (seedLine) return `${seedLine.replace(/\.$/u, "")} through ${number} evidence-qualified generic ${count === 1 ? "association" : "associations"}.`;
      return text("E1");
    }
    case "TRACE_OPEN_INQUIRY":
      return join(text("Q1"), text("Q3"));
    default:
      return "Guidance is unavailable for this state.";
  }
}

export type ProviderDraft = { note: string; suggestionIds: readonly string[]; usedFactIds: readonly string[] };
export type GuidanceInput = { facts: SurfaceFacts; candidates: readonly ApprovedSuggestion[] };
export type ProviderFailureStatus = "PROVIDER_ERROR" | "PROVIDER_RATE_LIMITED" | "PROVIDER_INCOMPLETE" | "PROVIDER_OUTPUT_MISSING" | "PROVIDER_OUTPUT_INVALID" | "TIMEOUT";
export class ProviderFailure extends Error {
  readonly status: ProviderFailureStatus;
  constructor(status: ProviderFailureStatus, message: string = status) {
    super(message);
    this.status = status;
  }
}
export type GuidanceProvider = {
  readonly id: "STATIC_FALLBACK_PROVIDER" | "DEEPSEEK_GUIDANCE_PROVIDER";
  generate(input: GuidanceInput): Promise<ProviderDraft>;
};

export class StaticFallbackProvider implements GuidanceProvider {
  readonly id = "STATIC_FALLBACK_PROVIDER" as const;
  async generate({ facts, candidates }: GuidanceInput): Promise<ProviderDraft> {
    /* the deterministic note with the program's own approved actions, within the surface's ceiling */
    return { note: factsFallbackNote(facts), suggestionIds: candidates.slice(0, MAX_ACTIONS[facts.surface]).map((candidate) => candidate.id), usedFactIds: facts.statements.map((item) => item.id) };
  }
}

/* ---- the instruction: compose from the statements, add nothing ---- */
const SHARED_RULES = [
  "You write the 'System suggests' note for one surface of the Modern Graphic Design Archive.",
  "You receive FACT STATEMENTS, each with an id, the labels and counts they use, and an allowlist of suggestions.",
  "Compose one sentence, at most two, at most forty-five words in total, plain prose, from the statements only: choose the statements that matter for this state, join or shorten them, vary their wording.",
  "Add nothing: no fact, label, number, source, evidence, record, date, place, person, cause, influence, sequence, importance, similarity, strength, confidence, likelihood or reason that the statements do not state.",
  "Never merge two pairings into one, never say a term is paired, associated, linked or connected with a term the statements do not pair it with, never turn a count of associations into a count of sources, records or objects.",
  "Never call an association weak, strong, similar, semantic or co-occurring. Never promise what a refinement will find. Never say that something set aside or not recorded is missing, absent, lost or never existed.",
  "Return used_fact_ids naming the statements you drew on and suggestion_ids only from the allowlist, zero when none helps. No Markdown, identifiers, URLs, disclaimers or reasoning in the note.",
].join(" ");
const SURFACE_RULES: Readonly<Record<string, string>> = {
  SEARCH_RESULTS: "Describe the current result set and, if one is worth it, which approved refinement narrows it. A zero-result Search means this query matched nothing here; it says nothing about the archive or history.",
  TRACE_CONTEXT: "Describe the object's recorded context: what stands on the canvas and what is set aside. Set aside is still recorded. A dimension not recorded in the projection is not a claim about the object's history.",
  TRACE_VALIDATED_EXPLORATION: "Narrate the pairing or pairings visible in this view; with several, prefer the ones the first term takes part in. Do not explain why any pairing exists, and do not instruct the reader.",
  TRACE_OPEN_INQUIRY: "Say what bounded question the inquiry considers between the listed terms and that its current evidence does not qualify it for the validated graph. Never frame it as likely, probable or possible.",
};
export function instructionFor(surface: string): string {
  return `${SHARED_RULES} ${SURFACE_RULES[surface] ?? ""}`.trim();
}

export type DeepSeekProviderOptions = {
  apiKey: string;
  baseUrl: string;
  model: string;
  timeoutMs: number;
  temperature: number;
  fetchImpl: typeof fetch;
};

export function modelConfigVersion(options: Pick<DeepSeekProviderOptions, "model" | "temperature">): string {
  return `${options.model}|reasoning=none|temperature=${options.temperature}|max_output_tokens=${SYSTEM_SUGGESTIONS_MAX_OUTPUT_TOKENS}`;
}

/* the response's assistant text: only message items' output_text parts; reasoning items are skipped;
   an errored, incomplete or empty response is a failure, never a note */
export function providerOutputText(payload: unknown): string {
  if (!payload || typeof payload !== "object") throw new ProviderFailure("PROVIDER_OUTPUT_INVALID", "response is not an object");
  const response = payload as { error?: unknown; status?: unknown; incomplete_details?: { reason?: unknown }; output?: unknown; output_text?: unknown };
  if (response.error) throw new ProviderFailure("PROVIDER_ERROR", "response carries an error");
  if (typeof response.status === "string" && response.status !== "completed") throw new ProviderFailure("PROVIDER_INCOMPLETE", `response status ${response.status}${typeof response.incomplete_details?.reason === "string" ? ` (${response.incomplete_details.reason})` : ""}`);
  const parts: string[] = [];
  if (Array.isArray(response.output)) {
    for (const item of response.output) {
      if (!item || typeof item !== "object") continue;
      const entry = item as { type?: unknown; role?: unknown; content?: unknown };
      if (entry.type === "reasoning") continue;
      if (entry.type !== undefined && entry.type !== "message") continue;
      if (entry.role !== undefined && entry.role !== "assistant") continue;
      if (!Array.isArray(entry.content)) continue;
      for (const part of entry.content) {
        if (!part || typeof part !== "object") continue;
        const piece = part as { type?: unknown; text?: unknown };
        if (piece.type !== undefined && piece.type !== "output_text") continue;
        if (typeof piece.text === "string") parts.push(piece.text);
      }
    }
  }
  let text = parts.join("").trim();
  if (!text && typeof response.output_text === "string") text = response.output_text.trim();
  if (!text) throw new ProviderFailure("PROVIDER_OUTPUT_MISSING", "response carries no assistant text");
  return text;
}

export function parseProviderDraft(text: string): ProviderDraft {
  let parsed: unknown;
  try { parsed = JSON.parse(text); } catch { throw new ProviderFailure("PROVIDER_OUTPUT_INVALID", "assistant text is not JSON"); }
  if (!parsed || typeof parsed !== "object") throw new ProviderFailure("PROVIDER_OUTPUT_INVALID", "assistant JSON is not an object");
  const result = parsed as { note?: unknown; suggestion_ids?: unknown; used_fact_ids?: unknown };
  if (typeof result.note !== "string") throw new ProviderFailure("PROVIDER_OUTPUT_INVALID", "note missing");
  const ids = (value: unknown, label: string): string[] => {
    if (value === undefined) return [];
    if (!Array.isArray(value) || value.some((id) => typeof id !== "string")) throw new ProviderFailure("PROVIDER_OUTPUT_INVALID", `${label} invalid`);
    return value as string[];
  };
  return { note: result.note, suggestionIds: ids(result.suggestion_ids, "suggestion_ids"), usedFactIds: ids(result.used_fact_ids, "used_fact_ids") };
}

export class DeepSeekGuidanceProvider implements GuidanceProvider {
  readonly id = "DEEPSEEK_GUIDANCE_PROVIDER" as const;
  private readonly options: DeepSeekProviderOptions;

  constructor(options: DeepSeekProviderOptions) {
    this.options = options;
  }

  /* the request body, for the tests to read and the live harness to record */
  body({ facts, candidates }: GuidanceInput): Record<string, unknown> {
    const suggestionIds = candidates.map((candidate) => candidate.id);
    const factIds = facts.statements.map((item) => item.id);
    const idList = (list: readonly string[], max: number) => (list.length ? { type: "array", maxItems: Math.min(max, list.length), uniqueItems: true, items: { type: "string", enum: list } } : { type: "array", maxItems: 0, items: { type: "string" } });
    return {
      model: this.options.model,
      store: false,
      max_output_tokens: SYSTEM_SUGGESTIONS_MAX_OUTPUT_TOKENS,
      temperature: this.options.temperature,
      reasoning: { effort: "none" },
      input: [
        { role: "system", content: [{ type: "input_text", text: instructionFor(facts.surface) }] },
        { role: "user", content: [{ type: "input_text", text: JSON.stringify({ prompt_version: SYSTEM_SUGGESTIONS_PROMPT_VERSION, surface: facts.surface, public_context: facts.publicContext, allowed_suggestions: candidates.map(({ id, label }) => ({ id, label })) }) }] },
      ],
      text: {
        format: {
          type: "json_schema",
          name: "archive_system_suggests",
          strict: true,
          schema: {
            type: "object",
            additionalProperties: false,
            required: ["note", "used_fact_ids", "suggestion_ids"],
            properties: {
              note: { type: "string", maxLength: 320 },
              used_fact_ids: idList(factIds, 12),
              suggestion_ids: idList(suggestionIds, 4),
            },
          },
        },
      },
    };
  }

  async generate(input: GuidanceInput): Promise<ProviderDraft> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.options.timeoutMs);
    try {
      let response: Response;
      try {
        response = await this.options.fetchImpl(`${this.options.baseUrl}${DEEPSEEK_RESPONSES_PATH}`, {
          method: "POST",
          headers: { Authorization: `Bearer ${this.options.apiKey}`, "Content-Type": "application/json" },
          body: JSON.stringify(this.body(input)),
          cache: "no-store",
          signal: controller.signal,
        });
      } catch (error) {
        if (error instanceof Error && error.name === "AbortError") throw new ProviderFailure("TIMEOUT");
        throw new ProviderFailure("PROVIDER_ERROR", "request failed");
      }
      if (response.status === 429) throw new ProviderFailure("PROVIDER_RATE_LIMITED", "429");
      if (!response.ok) throw new ProviderFailure("PROVIDER_ERROR", `http ${response.status}`);
      let payload: unknown;
      try { payload = await response.json(); } catch { throw new ProviderFailure("PROVIDER_OUTPUT_INVALID", "response body is not JSON"); }
      return parseProviderDraft(providerOutputText(payload));
    } finally {
      clearTimeout(timeout);
    }
  }
}
