import "server-only";

import type { ApprovedSuggestion, SystemSuggestionsRequest } from "./types";

export const DEEPSEEK_DEFAULT_BASE_URL = "https://api.deepseek.com";
export const DEEPSEEK_RESPONSES_PATH = "/responses";
export const DEEPSEEK_DEFAULT_MODEL = "deepseek-v4-flash";
export const SYSTEM_SUGGESTIONS_PROMPT_VERSION = "gda-navigation-guidance-v1";

export type ProviderDraft = { note: string; suggestionIds: readonly string[] };
export type GuidanceProvider = {
  readonly id: "STATIC_FALLBACK_PROVIDER" | "DEEPSEEK_GUIDANCE_PROVIDER";
  generate(input: { request: SystemSuggestionsRequest; candidates: readonly ApprovedSuggestion[] }): Promise<ProviderDraft>;
};

function fallbackNote(request: SystemSuggestionsRequest): string {
  if (request.surface === "SEARCH_RESULTS") {
    const context = request.context as { exactResultCount: number };
    if (context.exactResultCount === 0) return "No public objects match this Search. Broaden the text or remove one filter to continue.";
    return `${context.exactResultCount.toLocaleString("en-US")} public ${context.exactResultCount === 1 ? "object matches" : "objects match"}. Use a suggested refinement to examine a smaller part of the result set.`;
  }
  if (request.surface === "TRACE_CONTEXT") return "Review the current public context, then choose an available context action to continue.";
  if (request.surface === "TRACE_SPACETIME") return "Read the current period and geography together, then use an available selection to narrow the public aggregate view.";
  if (request.surface === "TRACE_VALIDATED_EXPLORATION") return "Continue from the current validated composition using only the available validated nodes and associations.";
  return "Review the stated evidence gap and source boundary before choosing an available inquiry action.";
}

export class StaticFallbackProvider implements GuidanceProvider {
  readonly id = "STATIC_FALLBACK_PROVIDER" as const;
  async generate({ request, candidates }: { request: SystemSuggestionsRequest; candidates: readonly ApprovedSuggestion[] }): Promise<ProviderDraft> {
    return { note: fallbackNote(request), suggestionIds: candidates.slice(0, 4).map((candidate) => candidate.id) };
  }
}

type DeepSeekProviderOptions = {
  apiKey: string;
  baseUrl: string;
  model: string;
  timeoutMs: number;
  fetchImpl: typeof fetch;
};

function providerText(payload: unknown): string | null {
  if (!payload || typeof payload !== "object") return null;
  const response = payload as { output_text?: unknown; output?: unknown };
  if (typeof response.output_text === "string") return response.output_text;
  if (!Array.isArray(response.output)) return null;
  for (const item of response.output) {
    if (!item || typeof item !== "object") continue;
    const content = (item as { content?: unknown }).content;
    if (!Array.isArray(content)) continue;
    for (const part of content) {
      if (part && typeof part === "object" && typeof (part as { text?: unknown }).text === "string") return (part as { text: string }).text;
    }
  }
  return null;
}

export class DeepSeekGuidanceProvider implements GuidanceProvider {
  readonly id = "DEEPSEEK_GUIDANCE_PROVIDER" as const;
  private readonly options: DeepSeekProviderOptions;

  constructor(options: DeepSeekProviderOptions) {
    this.options = options;
  }

  async generate({ request, candidates }: { request: SystemSuggestionsRequest; candidates: readonly ApprovedSuggestion[] }): Promise<ProviderDraft> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.options.timeoutMs);
    try {
      const response = await this.options.fetchImpl(`${this.options.baseUrl}${DEEPSEEK_RESPONSES_PATH}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.options.apiKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: this.options.model,
          store: false,
          max_output_tokens: 240,
          input: [
            {
              role: "system",
              content: [{ type: "input_text", text: "Write one or two short navigation sentences only. Select zero to four suggestion_ids from the supplied allowlist. Do not add facts, claims, identifiers, URLs, Markdown, or reasoning." }],
            },
            {
              role: "user",
              content: [{ type: "input_text", text: JSON.stringify({ prompt_version: SYSTEM_SUGGESTIONS_PROMPT_VERSION, surface: request.surface, public_context: request.context, allowed_suggestions: candidates.map(({ id, label }) => ({ id, label })) }) }],
            },
          ],
          text: {
            format: {
              type: "json_schema",
              name: "archive_navigation_guidance",
              strict: true,
              schema: {
                type: "object",
                additionalProperties: false,
                required: ["note", "suggestion_ids"],
                properties: {
                  note: { type: "string", maxLength: 320 },
                  suggestion_ids: { type: "array", maxItems: 4, uniqueItems: true, items: { type: "string", enum: candidates.map((candidate) => candidate.id) } },
                },
              },
            },
          },
        }),
        cache: "no-store",
        signal: controller.signal,
      });
      if (!response.ok) throw new Error("PROVIDER_HTTP_ERROR");
      const payload = await response.json();
      const text = providerText(payload);
      if (!text) throw new Error("PROVIDER_OUTPUT_MISSING");
      const parsed = JSON.parse(text) as unknown;
      if (!parsed || typeof parsed !== "object") throw new Error("PROVIDER_OUTPUT_INVALID");
      const result = parsed as { note?: unknown; suggestion_ids?: unknown };
      if (typeof result.note !== "string" || !Array.isArray(result.suggestion_ids) || result.suggestion_ids.some((id) => typeof id !== "string")) throw new Error("PROVIDER_OUTPUT_INVALID");
      return { note: result.note, suggestionIds: result.suggestion_ids as string[] };
    } finally {
      clearTimeout(timeout);
    }
  }
}
