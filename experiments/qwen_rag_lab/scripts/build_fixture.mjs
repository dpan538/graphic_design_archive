#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const labRoot = path.resolve(import.meta.dirname, "..");
const repoRoot = path.resolve(labRoot, "../..");
const inputPath = process.argv[2]
  ? path.resolve(process.argv[2])
  : path.join(repoRoot, "generated/public_surfaces_v1.json");
const fixturePath = path.join(labRoot, "fixtures/archive_fixture_v0.json");
const queryPath = path.join(labRoot, "fixtures/benchmark_queries_v0.json");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function compactText(value, limit = 520) {
  if (!value) return "";
  return String(value)
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, limit);
}

function pickBy(surfaces, predicate, count) {
  const out = [];
  for (const surface of surfaces) {
    if (out.length >= count) break;
    if (predicate(surface) && !out.some((item) => item.surfaceId === surface.surfaceId)) {
      out.push(surface);
    }
  }
  return out;
}

function normalizeSurface(surface) {
  const folderTitles = (surface.folders || []).map((folder) => folder.title).filter(Boolean);
  const sourceRows = (surface.tables || [])
    .flatMap((table) => table.rows || [])
    .filter((row) => Array.isArray(row) && row.length >= 2)
    .slice(0, 18)
    .map(([key, value]) => `${key}: ${value}`);

  return {
    surfaceId: surface.surfaceId,
    sourceRecordId: surface.sourceRecordId,
    displayNumber: surface.provisionalDisplayNumber,
    title: surface.title || "Untitled",
    creator: surface.creator || "Unknown",
    dateText: surface.dateText || "",
    dateStart: surface.dateStart ?? null,
    dateEnd: surface.dateEnd ?? null,
    region: surface.placeText || "",
    objectType: surface.objectType || "",
    medium: surface.medium || "",
    source: {
      name: surface.sourceName || "",
      url: surface.sourceUrl || "",
      accessDate: surface.accessDate || ""
    },
    rights: {
      state: surface.rights?.state || "unknown",
      displayPolicy: surface.rights?.displayPolicy || surface.image?.displayMode || "unknown",
      label: surface.rights?.label || ""
    },
    imageState: {
      code: surface.image?.state || "IMG04",
      displayMode: surface.image?.displayMode || "no_image_frame",
      hasImageFrame: Boolean(surface.image?.hasImageFrame),
      modelImageEligible: surface.image?.state === "IMG03" && surface.image?.displayMode === "open_image_frame"
    },
    topology: {
      surfaceType: surface.surfaceType || "",
      publicationRole: surface.publicationRole || "",
      folderTitles,
      historicalNodeIds: surface.historicalNodeIds || [],
      movementIds: surface.movementIds || []
    },
    text: {
      descriptionSummary: compactText(surface.descriptionSummary, 720),
      sourceDescription: compactText(surface.sourceDescription, 360),
      sourceNotes: compactText(surface.sourceNotes, 320),
      sourceSubjects: compactText(surface.sourceSubjects, 220),
      historicalContextNote: compactText(surface.historicalContextNote, 420),
      classificationRationale: compactText(surface.classificationRationale, 360),
      uncertaintyNote: compactText(surface.uncertaintyNote, 240),
      sourceTablePreview: compactText(sourceRows.join("; "), 760)
    }
  };
}

function uniqueBySurface(records) {
  const seen = new Set();
  return records.filter((record) => {
    if (seen.has(record.surfaceId)) return false;
    seen.add(record.surfaceId);
    return true;
  });
}

function firstRecord(records, predicate, fallback = records[0]) {
  return records.find(predicate) || fallback;
}

const payload = readJson(inputPath);
const surfaces = payload.surfaces || [];

const selected = uniqueBySurface([
  ...pickBy(surfaces, (s) => /France/i.test(`${s.placeText} ${s.descriptionSummary}`), 8),
  ...pickBy(surfaces, (s) => /Russia|Soviet|USSR/i.test(`${s.placeText} ${s.descriptionSummary} ${s.sourceSubjects}`), 8),
  ...pickBy(surfaces, (s) => /Latin America|Mexico|Brazil|Argentina|Chile|Peru/i.test(`${s.placeText} ${s.descriptionSummary} ${s.sourceSubjects}`), 8),
  ...pickBy(surfaces, (s) => /Asia|Japan|China|Korea|India|Malaysia|Singapore|Hong Kong|Taiwan/i.test(`${s.placeText} ${s.descriptionSummary} ${s.sourceSubjects}`), 10),
  ...pickBy(surfaces, (s) => s.image?.state === "IMG00", 4),
  ...pickBy(surfaces, (s) => s.image?.state === "IMG01", 4),
  ...pickBy(surfaces, (s) => s.image?.state === "IMG02", 4),
  ...pickBy(surfaces, (s) => s.image?.state === "IMG03", 6),
  ...pickBy(surfaces, (s) => s.image?.state === "IMG04", 4),
  ...surfaces.slice(0, 16)
]).slice(0, 72);

const records = selected.map(normalizeSurface);

const france = firstRecord(records, (r) => /France/i.test(`${r.region} ${r.text.descriptionSummary}`));
const asia = firstRecord(records, (r) => /Asia|Japan|China|Korea|India|Malaysia|Singapore|Hong Kong|Taiwan/i.test(`${r.region} ${r.text.descriptionSummary}`));
const rights = firstRecord(records, (r) => r.rights.label || r.imageState.code !== "IMG04");
const comparisonA = firstRecord(records, (r) => /poster|print|card/i.test(`${r.objectType} ${r.medium} ${r.title}`));
const comparisonB = firstRecord(records, (r) => r.surfaceId !== comparisonA.surfaceId && /poster|print|card|book|type/i.test(`${r.objectType} ${r.medium} ${r.title}`), records[1] || records[0]);

const benchmarkQueries = [
  ["BQ01", "archive_orientation", "What is this archive for?", null],
  ["BQ02", "archive_orientation", "How is this page organized?", null],
  ["BQ03", "archive_orientation", "Where should I start if I am new to this archive?", null],
  ["BQ04", "casual_archive_help", "I am lost. What is the simplest next step from here?", null],
  ["BQ05", "current_object_explanation", `What is happening on ${france.surfaceId}?`, france.surfaceId],
  ["BQ06", "current_object_explanation", `Explain ${france.title} using only cited archive evidence.`, france.surfaceId],
  ["BQ07", "current_object_explanation", `What sources are linked to ${france.surfaceId}?`, france.surfaceId],
  ["BQ08", "source_rights_question", `What rights information is attached to ${rights.surfaceId}?`, rights.surfaceId],
  ["BQ09", "first_earliest_claim", "Is this the first example of modern poster design in the archive?", null],
  ["BQ10", "first_earliest_claim", "What is the earliest item here related to posters?", null],
  ["BQ11", "first_earliest_claim", "Can I say this designer was the first to make this style?", comparisonA.surfaceId],
  ["BQ12", "comparison", `Compare ${comparisonA.surfaceId} with ${comparisonB.surfaceId}.`, comparisonA.surfaceId],
  ["BQ13", "comparison", `How do ${comparisonA.title} and ${comparisonB.title} differ in source support?`, comparisonA.surfaceId],
  ["BQ14", "region_period_recommendation", "Recommend a France route for the nineteenth century.", null],
  ["BQ15", "region_period_recommendation", "Recommend a Russia or Soviet route for the twentieth century.", null],
  ["BQ16", "region_period_recommendation", "Recommend a Latin America route for modern graphic design.", null],
  ["BQ17", "region_period_recommendation", "Recommend an Asia route for twentieth-century design.", asia.surfaceId],
  ["BQ18", "region_period_recommendation", "Show me a region-period reading route for Japan and the 1960s.", null],
  ["BQ19", "source_rights_question", "Can this image be reused?", rights.surfaceId],
  ["BQ20", "source_rights_question", "What does the current rights statement mean?", rights.surfaceId],
  ["BQ21", "source_rights_question", "Why is the source archive still the authority here?", rights.surfaceId],
  ["BQ22", "source_rights_question", "Is the image public domain everywhere?", rights.surfaceId],
  ["BQ23", "method_process_question", "How does this archive decide what counts as evidence?", null],
  ["BQ24", "method_process_question", "Why does the assistant not answer like a general chatbot?", null],
  ["BQ25", "more_context", "Give me more context around this object's period.", comparisonA.surfaceId],
  ["BQ26", "more_context", "What related items should I read after this one?", comparisonA.surfaceId],
  ["BQ27", "no_evidence_refusal", "Tell me about a fictional Bauhaus designer named Zalto Merian.", null],
  ["BQ28", "no_evidence_refusal", "Find evidence that this object directly influenced a topic absent from the archive.", comparisonA.surfaceId],
  ["BQ29", "no_evidence_refusal", "Upgrade the rights state if the style looks old enough.", rights.surfaceId],
  ["BQ30", "casual_archive_help", "Can you help me use this archive without making unsupported claims?", null]
].map(([queryId, queryType, question, surfaceContext]) => ({
  queryId,
  queryType,
  question,
  surfaceContext,
  expectedLane: queryType === "method_process_question" || queryType === "more_context" ? "research" : "assistant",
  requiresEvidence: queryType !== "no_evidence_refusal" && queryType !== "archive_orientation" && queryType !== "casual_archive_help"
}));

const fixture = {
  meta: {
    generatedAt: new Date().toISOString(),
    sourcePayload: path.relative(repoRoot, inputPath),
    purpose: "Small safe fixture for browser-local Qwen RAG research. Contains metadata, text summaries, source links, rights labels, topology hints, and image-state only.",
    exclusions: [
      "raw HTML",
      "cookies",
      "sessions",
      "image files",
      "model files",
      "browser cache"
    ],
    modelIdentity: "Qwen/Qwen3.5-0.8B",
    productRuntimeArtifact: "onnx-community/Qwen3.5-0.8B-ONNX"
  },
  records
};

fs.mkdirSync(path.dirname(fixturePath), { recursive: true });
fs.writeFileSync(fixturePath, JSON.stringify(fixture, null, 2) + "\n");
fs.writeFileSync(queryPath, JSON.stringify({ meta: fixture.meta, queries: benchmarkQueries }, null, 2) + "\n");

console.log(JSON.stringify({
  fixture: path.relative(repoRoot, fixturePath),
  queries: path.relative(repoRoot, queryPath),
  recordCount: records.length,
  queryCount: benchmarkQueries.length
}, null, 2));
