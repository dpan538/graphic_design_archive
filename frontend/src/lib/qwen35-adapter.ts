export type AssistantModelStatus = "idle" | "loading" | "ready" | "error";

export interface AssistantModelState {
  status: AssistantModelStatus;
  model?: string;
  message?: string;
}

export interface QwenAssistantContext {
  surfaceId?: string;
  title?: string;
  dateText?: string;
  imageState?: string;
  rightsLabel?: string;
  sourceName?: string;
  creator?: string;
  objectType?: string;
}

export interface QwenChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface QwenAskOptions {
  history?: QwenChatMessage[];
  research?: boolean;
  fast?: boolean;
  evidence?: string;
  onTiming?: (timing: QwenGenerationTiming) => void;
}

export interface QwenGenerationTiming {
  promptChars: number;
  inputTokens: number;
  generatedTokens: number;
  maxNewTokens: number;
  tokenizeMs: number;
  generateMs: number;
  decodeMs: number;
  totalMs: number;
}

interface TransformersEnv {
  allowRemoteModels?: boolean;
  allowLocalModels?: boolean;
  useBrowserCache?: boolean;
}

interface TransformersModule {
  env?: TransformersEnv;
  AutoTokenizer: {
    from_pretrained: (model: string) => Promise<QwenTokenizer>;
  };
  Qwen3_5ForCausalLM?: {
    from_pretrained: (
      model: string,
      options?: Record<string, unknown>,
    ) => Promise<QwenModel>;
  };
}

interface QwenTokenizer {
  eos_token_id?: number;
  apply_chat_template: (
    messages: { role: "system" | "user" | "assistant"; content: string }[],
    options: {
      tokenize: true;
      add_generation_prompt: true;
      enable_thinking?: boolean;
    },
  ) => Record<string, unknown> & {
    input_ids?: { dims?: number[] };
  };
  decode: (
    ids: number[],
    options?: { skip_special_tokens?: boolean },
  ) => string;
}

interface QwenModel {
  generate: (
    request: Record<string, unknown>,
  ) => Promise<{
    data?: ArrayLike<number | bigint> & { slice?: (start?: number, end?: number) => ArrayLike<number | bigint> };
    dims?: number[];
  }>;
  dispose?: () => Promise<unknown>;
}

export interface QwenAssistantSession {
  model: string;
  runtimeArtifact: string;
  runtimeMode: "causal-lm";
  dispose: () => Promise<void>;
  ask: (
    prompt: string,
    context?: QwenAssistantContext,
    options?: QwenAskOptions,
  ) => Promise<string>;
}

export const QWEN35_MODEL_ID = "Qwen/Qwen3.5-0.8B";
export const QWEN35_RUNTIME_MODEL_ID = "onnx-community/Qwen3.5-0.8B-ONNX";

const QWEN35_TEXT_DTYPE = {
  embed_tokens: "q4",
  decoder_model_merged: "q4",
};
const QWEN35_TEXT_EXTERNAL_DATA = [
  { path: "embed_tokens_q4.onnx_data", data: "onnx/embed_tokens_q4.onnx_data" },
  {
    path: "decoder_model_merged_q4.onnx_data",
    data: "onnx/decoder_model_merged_q4.onnx_data",
  },
];
const ASSISTANT_FAST_MAX_NEW_TOKENS = 44;
const ASSISTANT_MAX_NEW_TOKENS = 48;
const RESEARCH_MAX_NEW_TOKENS = 96;

let cachedSession: Promise<QwenAssistantSession> | null = null;
let cachedSessionReady = false;

function nowMs() {
  return typeof performance !== "undefined" ? performance.now() : Date.now();
}

function assertInteractiveRuntime() {
  if (
    typeof navigator !== "undefined" &&
    typeof window !== "undefined" &&
    !("gpu" in navigator)
  ) {
    throw new Error(
      "WebGPU is unavailable, so the local Qwen assistant is disabled to avoid CPU-only responses that take too long.",
    );
  }
}

function contextBlock(context?: QwenAssistantContext) {
  if (!context) return "No active archive object context.";
  return [
    `Surface ID: ${context.surfaceId ?? "unknown"}`,
    `Title: ${context.title ?? "unknown"}`,
    `Date: ${context.dateText ?? "unknown"}`,
    `Creator: ${context.creator ?? "unknown"}`,
    `Object type: ${context.objectType ?? "unknown"}`,
    `Image state: ${context.imageState ?? "unknown"}`,
    `Rights: ${context.rightsLabel ?? "unknown"}`,
    `Source: ${context.sourceName ?? "unknown"}`,
  ].join("\n");
}

function sanitizeAnswer(answer: string) {
  const cleaned = answer
    .replace(/<think>[\s\S]*?<\/think>/gi, "")
    .replace(/<think>/gi, "")
    .replace(/<\/think>/gi, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
  if (!cleaned) return "";
  if (/[.!?。！？)]$/.test(cleaned)) return cleaned;
  return `${cleaned}.`;
}

function qwenErrorMessage(error: unknown) {
  const raw =
    error instanceof Error
      ? error.message
      : typeof error === "string"
      ? error
      : "Qwen runtime error.";
  if (/webgpu|onnxruntime|OrtRun|GPUBuffer|buffer|memory|device/i.test(raw)) {
    return "Local Qwen hit a WebGPU memory error. I cleared the model session; reload the page or ask again after closing other heavy tabs.";
  }
  return raw;
}

function systemMessage(options?: QwenAskOptions) {
  const researchInstruction = options?.fast
    ? "Fast assistant mode: answer like a helpful archive research aide, not a search result. Give one complete sentence, normally under 32 words. Make a useful recommendation, caveat, comparison, or next reading move from the supplied candidate. For first, earliest, most, or recommend questions, choose one candidate from evidence and say it is only a current-archive lead. Do not list records. Do not repeat folder metadata. If evidence is weak, say the sharper search route."
    : options?.research
    ? "Research mode: use a more developed structure with Evidence, Reading, and Next checks. Do not expose hidden reasoning."
    : "Assistant mode: give a concise archive reading or recommendation in at most two compact sentences.";
  const fastExamples = options?.fast
    ? [
        "Fast answer examples:",
        "Q: when is the first advertising work in Russia? A: Start with the 1897 Kaplan school advertisement; it is the strongest Russia advertising lead here, but not proof of the historical first.",
        "Q: what should I check in 1970s France? A: Start with the strongest dated France candidate here, then verify the source page before treating it as representative.",
        "Q: what is this archive? A: Use it as a source map: design records show evidence, folders give routes, and rights states explain how far each image claim can go.",
      ].join(" ")
    : "";
  return {
    role: "system" as const,
    content: [
      "Archive Box local assistant.",
      `Model identity: ${QWEN35_MODEL_ID}.`,
      "Archive identity: a rights-aware modern graphic design history archive index. It helps users read source-linked design records, compare folders, check image/rights state, and plan research routes.",
      "Use only supplied archive evidence, active context, and conversation memory.",
      "The evidence may include REQUEST_PLAN. Treat it as answer-routing guidance, not archive content, and never quote the planner text.",
      "If evidence is absent or weak, say the archive does not currently contain enough evidence.",
      "For recommendations or superlatives, frame the answer as a current-archive navigation judgment, not an objective historical claim.",
      "Discussing metadata, source evidence, rights state, and archive navigation is allowed.",
      "Do not refuse as copyright infringement unless the user asks to copy, download, bypass rights, or reproduce protected content.",
      "Do not invent titles, artists, dates, or citations.",
      "Mention at most one surface ID or source name when it helps. Prefer advice over catalog prose.",
      "Never answer by merely restating the active folder or current record.",
      "Avoid phrases like 'is indexed here', 'reading angle', or 'current context'.",
      researchInstruction,
      fastExamples,
    ].join(" "),
  };
}

function evidenceMessage(
  prompt: string,
  context?: QwenAssistantContext,
  options?: QwenAskOptions,
) {
  return {
    role: "user" as const,
    content: [
      `ACTIVE_CONTEXT\n${contextBlock(context)}`,
      `ARCHIVE_EVIDENCE\n${options?.evidence || "No retrieved archive evidence."}`,
      `QUESTION\n${prompt}`,
    ]
      .filter(Boolean)
      .join("\n\n"),
  };
}

async function runGeneration({
  tokenizer,
  model,
  messages,
  maxNewTokens,
}: {
  tokenizer: QwenTokenizer;
  model: QwenModel;
  messages: { role: "system" | "user" | "assistant"; content: string }[];
  maxNewTokens: number;
}) {
  const started = nowMs();
  const promptChars = messages.reduce(
    (total, message) => total + message.content.length,
    0,
  );
  const tokenizeStarted = nowMs();
  const inputs = tokenizer.apply_chat_template(messages, {
    tokenize: true,
    add_generation_prompt: true,
    enable_thinking: false,
  });
  const tokenizeMs = nowMs() - tokenizeStarted;
  const inputTokenCount = inputs.input_ids?.dims?.at(-1) ?? 0;
  if (!inputs.input_ids || inputTokenCount <= 0) {
    throw new Error("Qwen tokenizer returned no input tokens.");
  }
  const generateStarted = nowMs();
  const outputs = await model.generate({
    ...inputs,
    max_new_tokens: maxNewTokens,
    do_sample: false,
    eos_token_id: tokenizer.eos_token_id,
  });
  const generateMs = nowMs() - generateStarted;
  const outputTokenCount = outputs?.dims?.at(-1) ?? 0;
  const generatedTokenCount = Math.max(0, outputTokenCount - inputTokenCount);
  const generatedData = outputs.data?.slice
    ? outputs.data.slice(inputTokenCount, outputTokenCount)
    : [];
  const generatedIds = generatedTokenCount
    ? Array.from(generatedData, Number)
    : [];
  const decodeStarted = nowMs();
  const answer = sanitizeAnswer(
    generatedIds.length
      ? tokenizer.decode(generatedIds, { skip_special_tokens: true }) || ""
      : "",
  );
  const decodeMs = nowMs() - decodeStarted;
  return {
    answer,
    timing: {
      promptChars,
      inputTokens: inputTokenCount,
      generatedTokens: generatedTokenCount,
      maxNewTokens,
      tokenizeMs,
      generateMs,
      decodeMs,
      totalMs: nowMs() - started,
    },
  };
}

export async function createQwenAssistantSession(
  onProgress?: (message: string) => void,
): Promise<QwenAssistantSession> {
  if (cachedSession) {
    onProgress?.(cachedSessionReady ? "Ready" : "Preparing");
    return cachedSession;
  }

  cachedSession = (async () => {
    assertInteractiveRuntime();
    onProgress?.("Preparing");
    const transformers = (await import("@huggingface/transformers")) as TransformersModule;
    if (transformers.env) {
      transformers.env.allowRemoteModels = true;
      transformers.env.allowLocalModels = false;
      transformers.env.useBrowserCache = true;
    }

    const tokenizer = await transformers.AutoTokenizer.from_pretrained(
      QWEN35_RUNTIME_MODEL_ID,
    );
    const ModelClass = transformers.Qwen3_5ForCausalLM;
    if (!ModelClass) {
      throw new Error(
        "Qwen text-only runtime is unavailable in this Transformers.js build.",
      );
    }
    const model = await ModelClass.from_pretrained(
      QWEN35_RUNTIME_MODEL_ID,
      {
        dtype: QWEN35_TEXT_DTYPE,
        device: "webgpu",
        use_external_data_format: false,
        session_options: {
          externalData: QWEN35_TEXT_EXTERNAL_DATA,
        },
      },
    );

    const session: QwenAssistantSession = {
      model: QWEN35_MODEL_ID,
      runtimeArtifact: QWEN35_RUNTIME_MODEL_ID,
      runtimeMode: "causal-lm",
      dispose: async () => {
        await model.dispose?.();
      },
      ask: async (prompt, context, options) => {
        const history = (options?.history ?? []).slice(
          options?.research ? -4 : options?.fast ? -2 : -4,
        );
        const messages = [
          systemMessage(options),
          ...history.map((message) => ({
            role: message.role,
            content: message.content,
          })),
          evidenceMessage(prompt, context, options),
        ];
        try {
          const result = await runGeneration({
            tokenizer,
            model,
            messages,
            maxNewTokens: options?.fast
              ? ASSISTANT_FAST_MAX_NEW_TOKENS
              : options?.research
              ? RESEARCH_MAX_NEW_TOKENS
              : ASSISTANT_MAX_NEW_TOKENS,
          });
          options?.onTiming?.(result.timing);
          return result.answer;
        } catch (error) {
          cachedSession = null;
          cachedSessionReady = false;
          await model.dispose?.();
          throw new Error(qwenErrorMessage(error));
        }
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

export async function resetQwenAssistantSession() {
  const sessionPromise = cachedSession;
  cachedSession = null;
  cachedSessionReady = false;
  if (!sessionPromise) return;
  try {
    const session = await sessionPromise;
    await session.dispose();
  } catch {
    // The session may already be in a failed WebGPU state.
  }
}
