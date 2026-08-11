#!/usr/bin/env node
/**
 * Runtime probe for Qwen3.5-0.8B.
 *
 * Modes:
 *   metadata  - import Transformers.js and report runtime/package info.
 *   load      - attempt to instantiate the model through a selected strategy.
 *               This may download large model assets and should be run only in
 *               a controlled environment.
 *
 * Load strategies:
 *   --strategy=pipeline-image-to-text
 *   --strategy=auto-image-text-to-text
 *   --strategy=qwen35-conditional-generation
 *
 * The script intentionally does not wire the model into the public UI.
 */

import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "..", "..");
const OUT = path.join(ROOT, "generated", "qwen35_runtime_probe_v0.json");
const BASE_MODEL_ID = "Qwen/Qwen3.5-0.8B";
const DEFAULT_RUNTIME_MODEL_ID = "onnx-community/Qwen3.5-0.8B-ONNX";
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

function arg(name, fallback = null) {
  const prefix = `${name}=`;
  const hit = process.argv.find((item) => item.startsWith(prefix));
  return hit ? hit.slice(prefix.length) : fallback;
}

function writeReport(report) {
  fs.writeFileSync(OUT, `${JSON.stringify(report, null, 2)}\n`);
  console.log(JSON.stringify(report.summary, null, 2));
}

async function main() {
  const mode = arg("--mode", "metadata");
  const strategy = arg("--strategy", "pipeline-image-to-text");
  const modelId = arg("--model", DEFAULT_RUNTIME_MODEL_ID);
  const started = Date.now();
  const report = {
    generatedAt: new Date().toISOString(),
    baseModelTarget: BASE_MODEL_ID,
    runtimeModelTarget: modelId,
    mode,
    strategy,
    result: "unknown",
    notes: [],
    timingsMs: {},
    summary: {},
  };
  const qwenLoadOptions = {
    dtype: QWEN35_DTYPE,
    device: "auto",
    use_external_data_format: false,
    session_options: {
      externalData: QWEN35_EXTERNAL_DATA,
    },
  };

  let transformers;
  try {
    transformers = await import("@huggingface/transformers");
    report.result = "transformers_import_ok";
    report.transformersExports = Object.keys(transformers).slice(0, 80);
    report.notes.push("Transformers.js imports successfully.");
  } catch (error) {
    report.result = "transformers_import_failed";
    report.error = String(error?.stack || error);
    report.summary = {
      result: report.result,
      out: OUT,
      error: String(error?.message || error),
    };
    writeReport(report);
    process.exitCode = 1;
    return;
  }

  report.timingsMs.import = Date.now() - started;

  const {
    env,
    pipeline,
    AutoProcessor,
    AutoModelForImageTextToText,
    Qwen3_5ForConditionalGeneration,
  } = transformers;
  if (env) {
    env.allowRemoteModels = mode === "load";
    env.allowLocalModels = true;
    env.useBrowserCache = false;
    env.useFSCache = true;
    env.cacheDir = path.join(ROOT, ".model-cache", "transformers");
    report.env = {
      allowRemoteModels: env.allowRemoteModels,
      allowLocalModels: env.allowLocalModels,
      useBrowserCache: env.useBrowserCache,
      useFSCache: env.useFSCache,
      cacheDir: env.cacheDir,
    };
  }

  if (mode !== "load") {
    report.result = "metadata_only_ok";
    report.summary = {
      result: report.result,
      baseModelTarget: BASE_MODEL_ID,
      runtimeModelTarget: modelId,
      out: OUT,
      next: "Run with --mode=load to attempt controlled model loading.",
    };
    writeReport(report);
    return;
  }

  try {
    const loadStarted = Date.now();
    let loaded;
    if (strategy === "pipeline-image-to-text") {
      if (typeof pipeline !== "function") {
        throw new Error("pipeline() is unavailable in this Transformers.js build.");
      }
      loaded = await pipeline("image-to-text", modelId, {
        ...qwenLoadOptions,
      });
    } else if (strategy === "auto-image-text-to-text") {
      if (!AutoProcessor || !AutoModelForImageTextToText) {
        throw new Error("AutoProcessor or AutoModelForImageTextToText is unavailable.");
      }
      const processor = await AutoProcessor.from_pretrained(modelId);
      const model = await AutoModelForImageTextToText.from_pretrained(modelId, qwenLoadOptions);
      loaded = {
        processorType: processor?.constructor?.name,
        modelType: model?.constructor?.name,
      };
    } else if (strategy === "qwen35-conditional-generation") {
      if (!AutoProcessor || !Qwen3_5ForConditionalGeneration) {
        throw new Error("AutoProcessor or Qwen3_5ForConditionalGeneration is unavailable.");
      }
      const processor = await AutoProcessor.from_pretrained(modelId);
      const model = await Qwen3_5ForConditionalGeneration.from_pretrained(modelId, qwenLoadOptions);
      loaded = {
        processorType: processor?.constructor?.name,
        modelType: model?.constructor?.name,
      };
    } else {
      throw new Error(`Unknown strategy: ${strategy}`);
    }
    report.timingsMs.load = Date.now() - loadStarted;
    report.result = "model_load_ok";
    report.loaded = {
      type: typeof loaded,
      constructorName: loaded?.constructor?.name,
      details: loaded && typeof loaded === "object" ? loaded : null,
    };
    report.summary = {
      result: report.result,
      baseModelTarget: BASE_MODEL_ID,
      runtimeModelTarget: modelId,
      strategy,
      importMs: report.timingsMs.import,
      loadMs: report.timingsMs.load,
      out: OUT,
    };
  } catch (error) {
    report.result = "pipeline_load_failed";
    report.error = String(error?.stack || error);
    report.summary = {
      result: report.result,
      baseModelTarget: BASE_MODEL_ID,
      runtimeModelTarget: modelId,
      strategy,
      importMs: report.timingsMs.import,
      out: OUT,
      error: String(error?.message || error),
    };
    process.exitCode = 1;
  }

  writeReport(report);
}

main();
