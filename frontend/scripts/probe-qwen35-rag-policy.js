#!/usr/bin/env node
/**
 * Build a small rights-aware multimodal RAG probe set for Qwen3.5-0.8B.
 *
 * This does not call a model. It verifies which public records may legally and
 * methodologically enter multimodal context before the runtime probe loads any
 * weights.
 */

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "..");
const PAYLOAD = path.join(ROOT, "generated", "public_surfaces_v1.json");

const TEXT_FIELDS = [
  "descriptionSummary",
  "sourceDescription",
  "sourceNotes",
  "sourceSubjects",
  "historicalContextNote",
  "classificationRationale",
  "uncertaintyNote",
  "citationBasis",
];

function textFor(surface) {
  return TEXT_FIELDS.map((key) => surface[key]).filter(Boolean).join("\n\n");
}

function imageState(surface) {
  return surface.image?.state || "IMG04";
}

function displayPolicy(surface) {
  return surface.rights?.displayPolicy || surface.rights?.display_policy || "";
}

function canPassImageToLocalModel(surface) {
  const state = imageState(surface);
  const policy = displayPolicy(surface);
  if (state === "IMG00" || state === "IMG04") return false;

  // First Qwen test is deliberately conservative: only openly displayable
  // images enter model context. IMG01/IMG02 may be visible in UI, but their
  // local-model use requires a separate rights decision.
  return state === "IMG03" && policy === "open_image_frame" && Boolean(surface.image?.url);
}

function probeReason(surface) {
  const state = imageState(surface);
  const policy = displayPolicy(surface);
  if (canPassImageToLocalModel(surface)) return "image_context_allowed_open_image_frame";
  if (state === "IMG00") return "image_context_blocked_img00_rights_empty";
  if (state === "IMG04") return "image_context_blocked_img04_no_image_field";
  if (state === "IMG01") return `image_context_blocked_img01_thumbnail_policy_${policy || "unknown"}`;
  if (state === "IMG02") return `image_context_blocked_img02_source_viewer_policy_${policy || "unknown"}`;
  return `image_context_blocked_${state}_${policy || "unknown_policy"}`;
}

function compactSurface(surface) {
  const text = textFor(surface).replace(/\s+/g, " ").trim();
  return {
    surfaceId: surface.surfaceId,
    displayNumber: surface.provisionalDisplayNumber,
    title: surface.title,
    dateStart: surface.dateStart,
    dateEnd: surface.dateEnd,
    sourceName: surface.sourceName,
    sourceUrl: surface.sourceUrl,
    imageState: imageState(surface),
    displayPolicy: displayPolicy(surface),
    imageUrlForModel: canPassImageToLocalModel(surface) ? surface.image?.url : null,
    imageContextDecision: probeReason(surface),
    textPreview: text.slice(0, 900),
    citationHint: `${surface.sourceName || "Unknown source"} · ${surface.sourceUrl || "no source URL"}`,
  };
}

function main() {
  const payload = JSON.parse(fs.readFileSync(PAYLOAD, "utf8"));
  const surfaces = payload.surfaces || [];
  const counts = {};
  const policyCounts = {};
  for (const surface of surfaces) {
    counts[imageState(surface)] = (counts[imageState(surface)] || 0) + 1;
    const key = `${imageState(surface)}:${displayPolicy(surface) || "none"}`;
    policyCounts[key] = (policyCounts[key] || 0) + 1;
  }

  const samples = [];
  for (const state of ["IMG00", "IMG01", "IMG02", "IMG03", "IMG04"]) {
    const candidate = surfaces.find((surface) => imageState(surface) === state);
    if (candidate) samples.push(compactSurface(candidate));
  }

  const openImageSamples = surfaces
    .filter(canPassImageToLocalModel)
    .slice(0, 5)
    .map(compactSurface);

  const blockedImageSamples = surfaces
    .filter((surface) => ["IMG01", "IMG02"].includes(imageState(surface)))
    .slice(0, 5)
    .map(compactSurface);

  const report = {
    generatedAt: new Date().toISOString(),
    modelTarget: "Qwen/Qwen3.5-0.8B",
    policy: {
      v0ImageModelContext: "Only IMG03 + open_image_frame images are passed to the local multimodal model.",
      img00: "Never fetch or pass image pixels; use metadata/source link only.",
      img01: "Thumbnail visible in UI, but withheld from model context until rights policy explicitly allows it.",
      img02: "Source viewer image visible in UI, but withheld from model context until rights policy explicitly allows it.",
      img03: "Open image may enter local model context.",
      img04: "No image field; text-only context.",
    },
    counts,
    policyCounts,
    modelImageInputEligible: surfaces.filter(canPassImageToLocalModel).length,
    samples,
    openImageSamples,
    blockedImageSamples,
  };

  const out = path.join(ROOT, "generated", "qwen35_rag_policy_probe_v0.json");
  fs.writeFileSync(out, `${JSON.stringify(report, null, 2)}\n`);
  console.log(JSON.stringify({
    out,
    imageStates: counts,
    modelImageInputEligible: report.modelImageInputEligible,
    samples: samples.map((sample) => ({
      surfaceId: sample.surfaceId,
      imageState: sample.imageState,
      decision: sample.imageContextDecision,
    })),
  }, null, 2));
}

main();
