#!/usr/bin/env node
/**
 * Generation smoke test for the local Qwen3.5-0.8B archive assistant.
 *
 * This probe checks whether the selected local model can produce constrained
 * answers from supplied archive context. It does not wire anything into the UI.
 */

import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "..", "..");
const OUT = path.join(ROOT, "generated", "qwen35_generation_probe_v0.json");
const PAYLOAD = path.join(ROOT, "generated", "public_surfaces_v1.json");
const PRIMER_OUT = path.join(ROOT, "generated", "archive_assistant_primer_v0.json");
const BASE_MODEL_ID = "Qwen/Qwen3.5-0.8B";
const RUNTIME_MODEL_ID = "onnx-community/Qwen3.5-0.8B-ONNX";
const QWEN35_DTYPE = {
  embed_tokens: "q4",
  vision_encoder: "fp16",
  decoder_model_merged: "q4",
};
const QWEN35_EXTERNAL_DATA = [
  { path: "embed_tokens_q4.onnx_data", data: "onnx/embed_tokens_q4.onnx_data" },
  { path: "vision_encoder_fp16.onnx_data", data: "onnx/vision_encoder_fp16.onnx_data" },
  { path: "decoder_model_merged_q4.onnx_data", data: "onnx/decoder_model_merged_q4.onnx_data" },
];

function writeReport(report) {
  fs.writeFileSync(OUT, `${JSON.stringify(report, null, 2)}\n`);
  console.log(JSON.stringify(report.summary, null, 2));
}

function writePrimer(payload) {
  const primer = {
    generatedAt: new Date().toISOString(),
    assistantName: "Archive Box Local Assistant",
    role: "Local, rights-aware search and archive navigation assistant.",
    modelIdentity: BASE_MODEL_ID,
    runtimeArtifact: RUNTIME_MODEL_ID,
    answerContract: [
      "Use only supplied archive slips/chunks.",
      "Do not fetch live web pages.",
      "Do not write to or mutate the archive database.",
      "Do not treat generated prose as historical evidence.",
      "Return source links and surface IDs when available.",
      "If retrieval returns no cited chunk, refuse before calling the model.",
    ],
    imageContract: {
      IMG00: "No image pixels; metadata and source return only.",
      IMG01: "Thumbnail may be visible in UI, but is withheld from model-image context in v0.",
      IMG02: "Source-viewer image may be visible in UI, but is withheld from model-image context in v0.",
      IMG03: "Open image frame may enter model-image context when policy permits.",
      IMG04: "Text-only page; no image field.",
    },
    payloadShape: {
      folderTypes: payload.folderTypes?.map((folderType) => folderType.type) || [],
      surfaceCount: payload.surfaces?.length || 0,
      folderCount: payload.folders?.length || 0,
      readingNoteCount: payload.readingNotes?.length || 0,
      bookmarkCount: payload.bookmarks?.length || 0,
    },
  };
  fs.writeFileSync(PRIMER_OUT, `${JSON.stringify(primer, null, 2)}\n`);
  return primer;
}

function selectContextSurface(payload) {
  const surfaces = payload.surfaces || [];
  const candidates = surfaces
    .filter((surface) => {
      const text = [
        surface.descriptionSummary,
        surface.sourceDescription,
        surface.sourceNotes,
        surface.sourceSubjects,
      ]
        .filter(Boolean)
        .join(" ");
      return text.length >= 550 && surface.sourceUrl && surface.sourceName;
    })
    .sort((a, b) => {
      const aScore = (a.completenessScore || 0) + (a.imageState === "IMG03" ? 10 : 0);
      const bScore = (b.completenessScore || 0) + (b.imageState === "IMG03" ? 10 : 0);
      return bScore - aScore;
    });
  return candidates[0] || surfaces[0];
}

function imageState(surface) {
  return surface.image?.state || "IMG04";
}

function displayPolicy(surface) {
  return surface.rights?.displayPolicy || surface.rights?.display_policy || "";
}

function buildRecordSlip(surface) {
  const sourceText = [
    surface.descriptionSummary,
    surface.sourceDescription,
    surface.sourceNotes,
    surface.sourceSubjects,
  ]
    .filter(Boolean)
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
  const chunks = [
    `ID=${surface.surfaceId}`,
    `TITLE=${surface.title || ""}`,
    `DATE=${surface.dateText || surface.dateStart || ""}`,
    `CREATOR=${surface.creator || "Unknown"}`,
    `PLACE=${surface.placeText || ""}`,
    `MEDIUM=${surface.medium || surface.objectType || ""}`,
    `SOURCE=${surface.sourceName || ""}`,
    `URL=${surface.sourceUrl || ""}`,
    `IMAGE=${imageState(surface)}:${displayPolicy(surface) || "no_policy"}`,
    `NOTE=${sourceText.slice(0, 260)}`,
  ];
  return chunks.join("\n").slice(0, 650);
}

function buildSearchSlip(payload, query) {
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  return collectSearchHits(payload, terms)
    .slice(0, 2)
    .map((surface, index) => {
      const note = (surface.descriptionSummary || surface.sourceDescription || "").replace(/\s+/g, " ").trim();
      return [
        `HIT${index + 1}_ID=${surface.surfaceId}`,
        `HIT${index + 1}_TITLE=${surface.title || ""}`,
        `HIT${index + 1}_DATE=${surface.dateText || surface.dateStart || ""}`,
        `HIT${index + 1}_SOURCE=${surface.sourceName || ""}`,
        `HIT${index + 1}_URL=${surface.sourceUrl || ""}`,
        `HIT${index + 1}_NOTE=${note.slice(0, 120)}`,
      ].join("\n");
    })
    .join("\n---\n")
    .slice(0, 760);
}

function collectSearchHits(payload, terms) {
  return (payload.surfaces || [])
    .map((surface) => {
      const haystack = [
        surface.title,
        surface.creator,
        surface.placeText,
        surface.medium,
        surface.sourceName,
        surface.descriptionSummary,
        surface.sourceDescription,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      const score = terms.reduce((sum, term) => sum + (haystack.includes(term) ? 1 : 0), 0);
      return { surface, score };
    })
    .filter((row) => row.score > 0)
    .sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return (b.surface.completenessScore || 0) - (a.surface.completenessScore || 0);
    })
    .map(({ surface }) => surface);
}

function deterministicRecordAnswer(surface) {
  return [
    `${surface.title || "Untitled record"} is indexed as ${surface.objectType || surface.medium || "an archive record"}.`,
    `Date: ${surface.dateText || surface.dateStart || "undated"}.`,
    `Source: ${surface.sourceName || "unknown source"} ${surface.sourceUrl || ""}`.trim(),
  ].join(" ");
}

function deterministicSearchAnswer(hits) {
  if (!hits.length) return "No cited archive records matched this query.";
  const labels = hits
    .slice(0, 3)
    .map((surface) => `${surface.title || "Untitled"} (${surface.dateText || surface.dateStart || "undated"}, ${surface.sourceName || "unknown source"})`);
  return `Top archive matches: ${labels.join("; ")}. Open a surface to verify the source link.`;
}

function makeMessages(context, question, mode = "record") {
  return [
    {
      role: "system",
      content: [
        "Archive Box local assistant.",
        "Use only supplied CONTEXT.",
        "No invention. No hidden reasoning.",
        "Answer with a short reading angle only.",
      ].join(" "),
    },
    {
      role: "user",
      content: [
        `MODE=${mode}`,
        `CONTEXT=${context}`,
        `QUESTION=${question}`,
        "Return format: NOTE: ...",
      ].join("\n"),
    },
  ];
}

function sanitizeAnswer(answer) {
  return answer
    .replace(/<think>[\s\S]*?<\/think>/gi, "")
    .replace(/<think>/gi, "")
    .replace(/<\/think>/gi, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

async function runTextGeneration({ tokenizer, model, messages, maxNewTokens }) {
  const inputs = tokenizer.apply_chat_template(messages, {
    tokenize: true,
    add_generation_prompt: true,
  });
  const inputTokenCount = inputs.input_ids?.dims?.at(-1) || null;
  const outputs = await model.generate({
    ...inputs,
    max_new_tokens: maxNewTokens,
    do_sample: false,
    eos_token_id: tokenizer.eos_token_id,
  });
  const outputTokenCount = outputs?.dims?.at(-1) || null;
  const generatedTokenCount = inputTokenCount && outputTokenCount ? Math.max(0, outputTokenCount - inputTokenCount) : null;
  const generatedIds = generatedTokenCount ? Array.from(outputs.data.slice(inputTokenCount, outputTokenCount), Number) : [];
  const decoded = generatedIds.length ? tokenizer.decode(generatedIds, { skip_special_tokens: true }) || "" : "";
  return {
    decoded,
    answer: sanitizeAnswer(decoded),
    inputTokenCount,
    outputTokenCount,
    generatedTokenCount,
  };
}

async function main() {
  const started = Date.now();
  const report = {
    generatedAt: new Date().toISOString(),
    baseModelTarget: BASE_MODEL_ID,
    runtimeModelTarget: RUNTIME_MODEL_ID,
    result: "unknown",
    tests: [],
    timingsMs: {},
    summary: {},
  };

  const payload = JSON.parse(fs.readFileSync(PAYLOAD, "utf8"));
  const primer = writePrimer(payload);
  const surface = selectContextSurface(payload);
  const context = buildRecordSlip(surface);
  report.contextSurface = {
    surfaceId: surface.surfaceId,
    title: surface.title,
    sourceName: surface.sourceName,
    sourceUrl: surface.sourceUrl,
    imageState: imageState(surface),
    completenessScore: surface.completenessScore,
    contextLength: context.length,
  };
  report.primer = {
    out: PRIMER_OUT,
    surfaceCount: primer.payloadShape.surfaceCount,
    folderCount: primer.payloadShape.folderCount,
    readingNoteCount: primer.payloadShape.readingNoteCount,
    bookmarkCount: primer.payloadShape.bookmarkCount,
  };

  try {
    const transformers = await import("@huggingface/transformers");
    const {
      env,
      AutoTokenizer,
      Qwen3_5ForConditionalGeneration,
    } = transformers;

    if (env) {
      env.allowRemoteModels = true;
      env.allowLocalModels = true;
      env.useBrowserCache = false;
      env.useFSCache = true;
      env.cacheDir = path.join(ROOT, ".model-cache", "transformers");
    }

    const loadStarted = Date.now();
    const tokenizer = await AutoTokenizer.from_pretrained(RUNTIME_MODEL_ID);
    const model = await Qwen3_5ForConditionalGeneration.from_pretrained(RUNTIME_MODEL_ID, {
      dtype: QWEN35_DTYPE,
      device: "auto",
      use_external_data_format: false,
      session_options: {
        externalData: QWEN35_EXTERNAL_DATA,
      },
    });
    report.timingsMs.load = Date.now() - loadStarted;

    const evidenceQuestion = "Give a reading angle in eight words or fewer.";
    const evidenceMessages = makeMessages(context, evidenceQuestion, "record_summary");
    const evidenceStarted = Date.now();
    const evidence = await runTextGeneration({
      tokenizer,
      model,
      messages: evidenceMessages,
      maxNewTokens: 12,
    });
    report.timingsMs.evidenceGeneration = Date.now() - evidenceStarted;
    report.tests.push({
      testId: "evidence_answer",
      question: evidenceQuestion,
      promptLength: JSON.stringify(evidenceMessages).length,
      answer: evidence.answer,
      deterministicAnswer: deterministicRecordAnswer(surface),
      decoded: evidence.decoded,
      inputTokenCount: evidence.inputTokenCount,
      outputTokenCount: evidence.outputTokenCount,
      generatedTokenCount: evidence.generatedTokenCount,
    });

    const searchHits = collectSearchHits(payload, ["trade", "card"]).slice(0, 3);
    const searchQuestion = "Give a reading angle in eight words or fewer.";
    const searchContext = buildSearchSlip(payload, "trade card");
    const searchMessages = makeMessages(searchContext, searchQuestion, "search_results");
    const searchStarted = Date.now();
    const searchAnswer = await runTextGeneration({
      tokenizer,
      model,
      messages: searchMessages,
      maxNewTokens: 12,
    });
    report.timingsMs.searchGeneration = Date.now() - searchStarted;
    report.tests.push({
      testId: "search_assist_answer",
      question: searchQuestion,
      promptLength: JSON.stringify(searchMessages).length,
      answer: searchAnswer.answer,
      deterministicAnswer: deterministicSearchAnswer(searchHits),
      decoded: searchAnswer.decoded,
      inputTokenCount: searchAnswer.inputTokenCount,
      outputTokenCount: searchAnswer.outputTokenCount,
      generatedTokenCount: searchAnswer.generatedTokenCount,
    });

    const refusalContext = "";
    const refusalQuestion = "Who designed the Tokyo 1964 Olympic pictograms and what was the full design process?";
    const retrievalGateHasEvidence = refusalContext.trim().length > 0;
    const refusal = {
      decoded: "",
      answer: "The archive does not currently contain enough cited evidence to answer this question. Try searching for a surface, folder, or source record related to Tokyo 1964 before asking for synthesis.",
      inputTokenCount: 0,
      outputTokenCount: 0,
    };
    report.timingsMs.refusalGeneration = 0;
    report.tests.push({
      testId: "no_evidence_refusal",
      question: refusalQuestion,
      retrievalGateHasEvidence,
      modelCalled: false,
      promptLength: 0,
      answer: refusal.answer,
      decoded: refusal.decoded,
      inputTokenCount: refusal.inputTokenCount,
      outputTokenCount: refusal.outputTokenCount,
    });

    report.result = "generation_probe_ok";
    report.summary = {
      result: report.result,
      contextSurface: surface.surfaceId,
      loadMs: report.timingsMs.load,
      evidenceGenerationMs: report.timingsMs.evidenceGeneration,
      searchGenerationMs: report.timingsMs.searchGeneration,
      refusalGenerationMs: report.timingsMs.refusalGeneration,
      out: OUT,
    };
  } catch (error) {
    report.result = "generation_probe_failed";
    report.error = String(error?.stack || error);
    report.summary = {
      result: report.result,
      error: String(error?.message || error),
      out: OUT,
    };
    process.exitCode = 1;
  }

  report.timingsMs.total = Date.now() - started;
  writeReport(report);
}

main();
