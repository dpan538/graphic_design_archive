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
  ask: (prompt: string, context?: WebLLMContext) => Promise<string>;
}

const WEBLLM_ESM_URL = "https://esm.run/@mlc-ai/web-llm";
const DEFAULT_WEBLLM_MODEL = "Llama-3.2-1B-Instruct-q4f16_1-MLC";

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
  if (typeof navigator !== "undefined" && !("gpu" in navigator)) {
    throw new Error("WebGPU is not available in this browser.");
  }

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

  return {
    model: DEFAULT_WEBLLM_MODEL,
    ask: async (prompt, context) => {
      const response = await engine.chat.completions.create({
        temperature: 0.2,
        messages: [
          {
            role: "system",
            content:
              "You are a research assistant inside a rights-aware graphic design archive. Be concise, distinguish source evidence from interpretation, and do not claim image rights upgrades.",
          },
          {
            role: "user",
            content: `Archive context:\n${contextBlock(context)}\n\nQuestion:\n${prompt}`,
          },
        ],
      });
      return response.choices?.[0]?.message?.content?.trim() || "";
    },
  };
}
