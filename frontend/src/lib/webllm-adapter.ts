export type WebLLMStatus = "idle" | "loading" | "ready" | "error";

export interface WebLLMState {
  status: WebLLMStatus;
  model?: string;
  message?: string;
}

export interface WebLLMContext {
  title?: string;
  dateText?: string;
  imageState?: string;
  rightsLabel?: string;
  sourceName?: string;
  creator?: string;
  objectType?: string;
}

export interface WebLLMChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface WebLLMAskOptions {
  history?: WebLLMChatMessage[];
  research?: boolean;
}

interface WebLLMModule {
  CreateMLCEngine: (
    model: string,
    options?: {
      initProgressCallback?: (report: { text?: string; progress?: number }) => void;
    },
  ) => Promise<WebLLMEngine>;
}

interface WebLLMEngine {
  chat: {
    completions: {
      create: (request: {
        messages: { role: "system" | "user" | "assistant"; content: string }[];
        temperature?: number;
      }) => Promise<{
        choices?: { message?: { content?: string } }[];
      }>;
    };
  };
}

export interface WebLLMSession {
  model: string;
  ask: (
    prompt: string,
    context?: WebLLMContext,
    options?: WebLLMAskOptions,
  ) => Promise<string>;
}

const WEBLLM_ESM_URL = "https://esm.run/@mlc-ai/web-llm";
const DEFAULT_WEBLLM_MODEL = "Llama-3.2-1B-Instruct-q4f16_1-MLC";
let cachedSession: Promise<WebLLMSession> | null = null;
let cachedSessionReady = false;

function contextBlock(context?: WebLLMContext) {
  if (!context) return "No active archive object context.";
  return [
    `Title: ${context.title ?? "unknown"}`,
    `Date: ${context.dateText ?? "unknown"}`,
    `Creator: ${context.creator ?? "unknown"}`,
    `Object type: ${context.objectType ?? "unknown"}`,
    `Image state: ${context.imageState ?? "unknown"}`,
    `Rights: ${context.rightsLabel ?? "unknown"}`,
    `Source: ${context.sourceName ?? "unknown"}`,
  ].join("\n");
}

export async function createWebLLMSession(
  onProgress?: (message: string) => void,
): Promise<WebLLMSession> {
  if (cachedSession) {
    onProgress?.(cachedSessionReady ? "Ready" : "Preparing WebLLM");
    return cachedSession;
  }

  if (typeof navigator !== "undefined" && !("gpu" in navigator)) {
    throw new Error("WebGPU is not available in this browser.");
  }

  cachedSession = (async () => {
    const webllm = (await import(
      /* webpackIgnore: true */ WEBLLM_ESM_URL
    )) as WebLLMModule;
    const engine = await webllm.CreateMLCEngine(DEFAULT_WEBLLM_MODEL, {
      initProgressCallback: (report) => {
        if (report.text) onProgress?.(report.text);
        else if (typeof report.progress === "number") {
          onProgress?.(`Loading ${(report.progress * 100).toFixed(0)}%`);
        }
      },
    });

    const session: WebLLMSession = {
      model: DEFAULT_WEBLLM_MODEL,
      ask: async (prompt, context, options) => {
        const researchInstruction = options?.research
          ? "Research mode is enabled: give a more developed answer with sections for Evidence, Interpretation, and Next checks. Do not expose private chain-of-thought."
          : "Answer conversationally and keep the response compact.";
        const history = (options?.history ?? []).slice(-8);
        const response = await engine.chat.completions.create({
          temperature: options?.research ? 0.25 : 0.2,
          messages: [
            {
              role: "system",
              content: [
                "You are WebLLM running as the archive assistant inside a rights-aware graphic design archive.",
                "Use only the supplied archive context and the user's question unless the user explicitly asks for broader interpretation.",
                "Distinguish source evidence from interpretation, name uncertainty, and do not claim image rights upgrades.",
                researchInstruction,
              ].join(" "),
            },
            {
              role: "user",
              content: `Active archive context:\n${contextBlock(context)}`,
            },
            ...history,
            {
              role: "user",
              content: prompt,
            },
          ],
        });
        return response.choices?.[0]?.message?.content?.trim() || "";
      },
    };
    cachedSessionReady = true;
    return session;
  })();

  try {
    return await cachedSession;
  } catch (error) {
    cachedSession = null;
    cachedSessionReady = false;
    throw error;
  }
}
