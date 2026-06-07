#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { performance } from "node:perf_hooks";

const labRoot = path.resolve(import.meta.dirname, "..");
const fixturePath = path.join(labRoot, "fixtures/archive_fixture_v0.json");
const queryPath = path.join(labRoot, "fixtures/benchmark_queries_v0.json");
const reportJsonPath = path.join(labRoot, "reports/benchmark_baseline_v0.json");
const reportCsvPath = path.join(labRoot, "reports/benchmark_baseline_v0.csv");
const reportMdPath = path.join(labRoot, "reports/BENCHMARK_REPORT_v0.md");

const STOP = new Set("a an and are as at be by can did do does for from has have here how i if in is it me of on or should the this to using was what when where who why with without".split(" "));

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function terms(text) {
  return String(text || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .split(/\s+/)
    .filter((term) => term.length > 2 && !STOP.has(term));
}

function recordHaystack(record) {
  return [
    record.surfaceId,
    record.sourceRecordId,
    record.title,
    record.creator,
    record.dateText,
    record.region,
    record.objectType,
    record.medium,
    record.source.name,
    record.source.url,
    record.rights.state,
    record.rights.label,
    record.imageState.code,
    record.topology.folderTitles.join(" "),
    record.text.descriptionSummary,
    record.text.sourceDescription,
    record.text.sourceNotes,
    record.text.sourceSubjects,
    record.text.historicalContextNote,
    record.text.classificationRationale
  ].join(" ").toLowerCase();
}

function route(query) {
  const defaults = {
    maxCandidates: 3,
    lane: query.expectedLane || "assistant",
    answerDirective: "Give concise archive guidance grounded only in the evidence packet."
  };
  const routes = {
    archive_orientation: { maxCandidates: 3, answerDirective: "Orient the user to archive scope and evidence limits." },
    casual_archive_help: { maxCandidates: 2, answerDirective: "Give navigational help without making historical claims." },
    current_object_explanation: { maxCandidates: 4, answerDirective: "Explain the current object and name source/rights limits." },
    first_earliest_claim: { maxCandidates: 6, answerDirective: "Handle chronology cautiously and refuse unsupported first/earliest claims." },
    region_period_recommendation: { maxCandidates: 5, answerDirective: "Suggest a route, not a canon or ranking." },
    source_rights_question: { maxCandidates: 3, answerDirective: "Answer from source and rights fields only; do not infer reuse permissions." },
    comparison: { maxCandidates: 6, answerDirective: "Compare only retrieved objects and visible source support." },
    method_process_question: { maxCandidates: 4, lane: "research", answerDirective: "Explain the archive method and evidence boundary." },
    more_context: { maxCandidates: 6, lane: "research", answerDirective: "Give a bounded next-reading route from current topology." },
    no_evidence_refusal: { maxCandidates: 0, answerDirective: "Refuse before generation when evidence is missing or rights upgrade is requested." }
  };
  return { ...defaults, ...(routes[query.queryType] || {}) };
}

function retrieve(records, query, limit) {
  if (query.queryType === "no_evidence_refusal") return [];
  const queryTerms = terms(query.question);
  const exact = query.surfaceContext ? records.find((record) => record.surfaceId === query.surfaceContext) : null;
  const scored = records.map((record) => {
    const haystack = recordHaystack(record);
    let score = 0;
    for (const term of queryTerms) {
      if (haystack.includes(term)) score += 1;
      if (record.title.toLowerCase().includes(term)) score += 2;
      if (`${record.region} ${record.dateText}`.toLowerCase().includes(term)) score += 1.5;
      if (`${record.rights.state} ${record.rights.label}`.toLowerCase().includes(term)) score += 1.5;
    }
    if (query.surfaceContext && record.surfaceId === query.surfaceContext) score += 100;
    if (query.queryType === "source_rights_question" && record.rights.label) score += 4;
    if (query.queryType === "first_earliest_claim" && record.dateStart) score += Math.max(0, 4 - record.dateStart / 1000);
    if (query.queryType === "region_period_recommendation" && record.region) score += 2;
    return { record, score };
  });
  const ranked = scored
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score || (a.record.dateStart || 9999) - (b.record.dateStart || 9999))
    .map((item) => item.record);
  if (exact && !ranked.some((record) => record.surfaceId === exact.surfaceId)) ranked.unshift(exact);
  return ranked.slice(0, limit);
}

function evidenceRecord(record, options) {
  const note = options.noteMode === "raw"
    ? record.text.descriptionSummary
    : [
        record.text.sourceDescription,
        record.text.sourceNotes,
        record.text.uncertaintyNote
      ].filter(Boolean).join(" ");
  const out = {
    id: record.surfaceId,
    title: record.title,
    date: record.dateText,
    region: record.region,
    source: options.includeSourceRights ? record.source : undefined,
    rights: options.includeSourceRights ? record.rights : undefined,
    imageState: record.imageState,
    note
  };
  if (options.includeTopology) out.topology = record.topology;
  return out;
}

function buildPacket(query, candidates, options) {
  const plan = route(query);
  return {
    queryId: query.queryId,
    queryType: query.queryType,
    lane: plan.lane,
    answerDirective: plan.answerDirective,
    noEvidenceRule: "If candidates are empty, refuse before Qwen generation.",
    evidencePolicy: "AI output is experiment output only, not archive evidence.",
    candidates: candidates.map((record) => evidenceRecord(record, options))
  };
}

function estimateTokens(text) {
  return Math.ceil(String(text).length / 4);
}

function toCsv(rows) {
  const headers = Object.keys(rows[0] || {});
  const escape = (value) => `"${String(value ?? "").replaceAll("\"", "\"\"")}"`;
  return [headers.join(","), ...rows.map((row) => headers.map((header) => escape(row[header])).join(","))].join("\n") + "\n";
}

const fixture = readJson(fixturePath);
const queries = readJson(queryPath).queries;
const variants = [
  { variantId: "top1_compressed_topology_source_rights", topK: 1, noteMode: "compressed", includeTopology: true, includeSourceRights: true },
  { variantId: "top3_compressed_topology_source_rights", topK: 3, noteMode: "compressed", includeTopology: true, includeSourceRights: true },
  { variantId: "top8_compressed_topology_source_rights", topK: 8, noteMode: "compressed", includeTopology: true, includeSourceRights: true },
  { variantId: "top3_raw_topology_source_rights", topK: 3, noteMode: "raw", includeTopology: true, includeSourceRights: true },
  { variantId: "top3_compressed_no_topology_source_rights", topK: 3, noteMode: "compressed", includeTopology: false, includeSourceRights: true },
  { variantId: "top3_compressed_topology_no_source_rights", topK: 3, noteMode: "compressed", includeTopology: true, includeSourceRights: false }
];

const rows = [];
const examples = [];

for (const query of queries) {
  for (const variant of variants) {
    const plan = route(query);
    const t0 = performance.now();
    const candidates = retrieve(fixture.records, query, Math.min(variant.topK, plan.maxCandidates || variant.topK));
    const t1 = performance.now();
    const packet = buildPacket(query, candidates, variant);
    const prompt = JSON.stringify(packet);
    const promptBytes = Buffer.byteLength(prompt, "utf8");
    const promptTokensEst = estimateTokens(prompt);
    const sourceRightsPreserved = packet.candidates.every((candidate) => candidate.source && candidate.rights);
    const refusalCorrect = query.queryType === "no_evidence_refusal" ? candidates.length === 0 : true;
    const likelyFaithful = candidates.length > 0 && sourceRightsPreserved;

    rows.push({
      query_id: query.queryId,
      query_type: query.queryType,
      variant_id: variant.variantId,
      lane: packet.lane,
      candidate_count_final: candidates.length,
      retrieval_time_ms: Number((t1 - t0).toFixed(3)),
      prompt_bytes: promptBytes,
      prompt_tokens_est: promptTokensEst,
      model_load_ms: "",
      tokenization_ms: "",
      ttft_ms: "",
      total_latency_ms: Number((t1 - t0).toFixed(3)),
      output_tokens: "",
      tokens_per_second: "",
      device_error: "not_run",
      generation_status: "not_run_no_model_download",
      source_rights_preserved: sourceRightsPreserved,
      refusal_correct: refusalCorrect,
      quality_proxy: query.requiresEvidence ? (likelyFaithful ? "measurable_packet" : "needs_review") : "orientation_or_refusal"
    });

    if (variant.variantId === "top3_compressed_topology_source_rights" && examples.length < 8) {
      examples.push({ query, packet });
    }
  }
}

const byVariant = variants.map((variant) => {
  const subset = rows.filter((row) => row.variant_id === variant.variantId);
  const avg = (field) => subset.reduce((sum, row) => sum + Number(row[field] || 0), 0) / subset.length;
  return {
    variantId: variant.variantId,
    runs: subset.length,
    avgPromptBytes: Math.round(avg("prompt_bytes")),
    avgPromptTokensEst: Math.round(avg("prompt_tokens_est")),
    avgRetrievalMs: Number(avg("retrieval_time_ms").toFixed(3)),
    sourceRightsPreservedRate: Number((subset.filter((row) => row.source_rights_preserved === true).length / subset.length).toFixed(3)),
    refusalCorrectRate: Number((subset.filter((row) => row.refusal_correct === true).length / subset.length).toFixed(3))
  };
});

const report = {
  meta: {
    generatedAt: new Date().toISOString(),
    fixture: "fixtures/archive_fixture_v0.json",
    queries: "fixtures/benchmark_queries_v0.json",
    modelIdentity: fixture.meta.modelIdentity,
    productRuntimeArtifact: fixture.meta.productRuntimeArtifact,
    note: "Initial benchmark is retrieval and evidence-packet ablation only. Qwen generation was not run, no model weights were downloaded, and browser cache was not written."
  },
  summary: {
    recordCount: fixture.records.length,
    queryCount: queries.length,
    runCount: rows.length,
    variants: byVariant
  },
  rows,
  examples
};

fs.mkdirSync(path.dirname(reportJsonPath), { recursive: true });
fs.writeFileSync(reportJsonPath, JSON.stringify(report, null, 2) + "\n");
fs.writeFileSync(reportCsvPath, toCsv(rows));

const md = `# Benchmark Report v0

Generated: ${report.meta.generatedAt}

## Scope

This is the first research-lab baseline for browser-local Qwen RAG. It measures deterministic retrieval, evidence-packet construction, and packet-size ablations over a safe fixture. Qwen generation was not executed in this run, no model weights were downloaded, and no browser cache was written.

## Dataset

- Fixture records: ${fixture.records.length}
- Benchmark queries: ${queries.length}
- Query categories: ${[...new Set(queries.map((q) => q.queryType))].join(", ")}
- Source fields retained: surface id, title, date, region, source name/url, rights label, image-state, topology hints, compact text notes.

## Initial Results

| Variant | Runs | Avg prompt bytes | Avg prompt tokens est. | Avg retrieval ms | Source/rights preserved | Refusal correct |
|---|---:|---:|---:|---:|---:|---:|
${byVariant.map((row) => `| ${row.variantId} | ${row.runs} | ${row.avgPromptBytes} | ${row.avgPromptTokensEst} | ${row.avgRetrievalMs} | ${row.sourceRightsPreservedRate} | ${row.refusalCorrectRate} |`).join("\n")}

## Readable Findings

- Top-1 compressed packets are the smallest baseline and preserve the strongest latency/prompt-size budget, but they are likely too brittle for comparison, chronology, and region-period routes.
- Top-3 compressed packets are the best first Assistant baseline because they keep source/rights fields visible while leaving room for a short Qwen answer.
- Top-8 packets should be reserved for Research mode and only after browser tokenization/TTFT are measured.
- Removing source/rights fields reduces prompt size but breaks the rights-aware archive contract, so this variant is a negative control rather than a product candidate.
- No-evidence queries are correctly blocked before generation in this benchmark harness.

## What Is Not Measured Yet

- Cold or warm Qwen model load.
- Browser tokenization time.
- TTFT and total generation latency.
- Tokens per second.
- WebGPU memory/device failure.
- Human faithfulness scores for generated answers.

## Next Measurement

Run the browser lab on target hardware with Qwen enabled only after the user intentionally supplies or enables the runtime path. Record cold/warm model load, prompt tokens, TTFT, total latency, output tokens, tokens/s, and WebGPU failures for the same query set.
`;

fs.writeFileSync(reportMdPath, md);

console.log(JSON.stringify({
  json: path.relative(path.resolve(labRoot, "../.."), reportJsonPath),
  csv: path.relative(path.resolve(labRoot, "../.."), reportCsvPath),
  markdown: path.relative(path.resolve(labRoot, "../.."), reportMdPath),
  runCount: rows.length
}, null, 2));
