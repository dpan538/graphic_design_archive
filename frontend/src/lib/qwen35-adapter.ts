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
  Qwen3_5ForConditionalGeneration: {
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
}

export interface QwenAssistantSession {
  model: string;
  runtimeArtifact: string;
  ask: (
    prompt: string,
    context?: QwenAssistantContext,
    options?: QwenAskOptions,
  ) => Promise<string>;
}

export const QWEN35_MODEL_ID = "Qwen/Qwen3.5-0.8B";
export const QWEN35_RUNTIME_MODEL_ID = "onnx-community/Qwen3.5-0.8B-ONNX";

const QWEN35_DTYPE = {
  embed_tokens: "q4",
  vision_encoder: "fp16",
  decoder_model_merged: "q4",
};
const QWEN35_EXTERNAL_DATA = [
  { path: "embed_tokens_q4.onnx_data", data: "onnx/embed_tokens_q4.onnx_data" },
  { path: "vision_encoder_fp16.onnx_data", data: "onnx/vision_encoder_fp16.onnx_data" },
  {
    path: "decoder_model_merged_q4.onnx_data",
    data: "onnx/decoder_model_merged_q4.onnx_data",
  },
];
const ASSISTANT_FAST_MAX_NEW_TOKENS = 56;
const ASSISTANT_MAX_NEW_TOKENS = 48;
const RESEARCH_MAX_NEW_TOKENS = 180;

let cachedSession: Promise<QwenAssistantSession> | null = null;
let cachedSessionReady = false;

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
  return answer
    .replace(/<think>[\s\S]*?<\/think>/gi, "")
    .replace(/<think>/gi, "")
    .replace(/<\/think>/gi, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function systemMessage(options?: QwenAskOptions) {
  const researchInstruction = options?.fast
    ? "Fast assistant mode: answer like a helpful archive research aide, not a search result. Give one compact human sentence or two very short sentences, around 80-120 characters when possible. Make a useful suggestion, comparison, caveat, or next reading move from the supplied evidence. For first, earliest, most, or recommend questions, choose one candidate from evidence and say why it is only a current-archive judgment. If the evidence only has a weak or mismatched object, say that and suggest a better query direction. Do not list many records. Do not repeat folder metadata. If the question asks generally about the archive, introduce the archive and suggest how to explore it."
    : options?.research
    ? "Research mode: use a more developed structure with Evidence, Reading, and Next checks. Do not expose hidden reasoning."
    : "Assistant mode: give a concise archive reading or recommendation in at most two compact sentences.";
  return {
    role: "system" as const,
    content: [
      "Archive Box local assistant.",
      `Model identity: ${QWEN35_MODEL_ID}.`,
      "Archive identity: a rights-aware modern graphic design history archive index. It helps users read source-linked surfaces, compare folders, check image/rights state, and plan research routes.",
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
  const inputs = tokenizer.apply_chat_template(messages, {
    tokenize: true,
    add_generation_prompt: true,
    enable_thinking: false,
  });
  const inputTokenCount = inputs.input_ids?.dims?.at(-1) ?? 0;
  const outputs = await model.generate({
    ...inputs,
    max_new_tokens: maxNewTokens,
    do_sample: false,
    eos_token_id: tokenizer.eos_token_id,
  });
  const outputTokenCount = outputs?.dims?.at(-1) ?? 0;
  const generatedTokenCount = Math.max(0, outputTokenCount - inputTokenCount);
  const generatedData = outputs.data?.slice
    ? outputs.data.slice(inputTokenCount, outputTokenCount)
    : [];
  const generatedIds = generatedTokenCount
    ? Array.from(generatedData, Number)
    : [];
  return sanitizeAnswer(
    generatedIds.length
      ? tokenizer.decode(generatedIds, { skip_special_tokens: true }) || ""
      : "",
  );
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
    const model = await transformers.Qwen3_5ForConditionalGeneration.from_pretrained(
      QWEN35_RUNTIME_MODEL_ID,
      {
        dtype: QWEN35_DTYPE,
        device: "webgpu",
        use_external_data_format: false,
        session_options: {
          externalData: QWEN35_EXTERNAL_DATA,
        },
      },
    );

    const session: QwenAssistantSession = {
      model: QWEN35_MODEL_ID,
      runtimeArtifact: QWEN35_RUNTIME_MODEL_ID,
      ask: async (prompt, context, options) => {
        const history = (options?.history ?? []).slice(options?.fast ? -4 : -8);
        const messages = [
          systemMessage(options),
          ...history.map((message) => ({
            role: message.role,
            content: message.content,
          })),
          evidenceMessage(prompt, context, options),
        ];
        return runGeneration({
          tokenizer,
          model,
          messages,
          maxNewTokens: options?.fast
            ? ASSISTANT_FAST_MAX_NEW_TOKENS
            : options?.research
            ? RESEARCH_MAX_NEW_TOKENS
            : ASSISTANT_MAX_NEW_TOKENS,
        });
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
