/* System Suggests live acceptance (release pass, 2026-09-06): the real
   DeepSeek provider on a fixed, public-safe set of cases — four surfaces ×
   five cases × three runs = 60 calls — through the real service (facts,
   gate, cache off per call), recording per call: surface, case id, context
   fingerprint, prompt and configuration version, MODEL or STATIC_FALLBACK,
   provider status and fallback reason, latency, token usage, the final
   note and the content review. HTTP 200 is not success: only a note that
   passed the gate counts as MODEL. The key is read from the environment
   and never printed; without a key the run is recorded as SKIPPED. A total
   call cap stops runaway tuning. Writes system-suggests-live-results.jsonl
   under docs/qa/system-suggestions-release-v1/. */
import { appendFileSync, mkdirSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(here, "..");
const outDir = join(frontendRoot, "..", "docs/qa/system-suggestions-release-v1");
mkdirSync(outDir, { recursive: true });
const ledger = join(outDir, "system-suggests-live-results.jsonl");
const require = createRequire(import.meta.url);
const jiti = require("jiti")(fileURLToPath(import.meta.url), { interopDefault: true, tryNative: false, alias: { "@": join(frontendRoot, "src"), "server-only": join(here, "server-only-marker.mjs") } });

const RUNS = Number(process.env.LIVE_RUNS ?? "3");
const TEMPERATURES = (process.env.LIVE_TEMPERATURES ?? "0").split(",").map((value) => value.trim()).filter(Boolean);
const CALL_CAP = Number(process.env.LIVE_CALL_CAP ?? "130");
const now = "2026-09-06";

const key = process.env.DEEPSEEK_API_KEY?.trim() ?? "";
if (!key) {
  writeFileSync(ledger, `${JSON.stringify({ format: "system-suggests-live-results/v1", generated: now, status: "SKIPPED", reason: "DEEPSEEK_API_KEY is not set in this environment; no live call was made", planned_calls: 4 * 5 * RUNS * TEMPERATURES.length })}\n`);
  console.log(`SYSTEM_SUGGESTS_LIVE=SKIPPED reason=no_key planned_calls=${4 * 5 * RUNS * TEMPERATURES.length}`);
  process.exit(0);
}

const svc = await jiti.import(join(frontendRoot, "src/features/system-suggestions/service.server.ts"));
const cache = await jiti.import(join(frontendRoot, "src/features/system-suggestions/cache.server.ts"));
const providers = await jiti.import(join(frontendRoot, "src/features/system-suggestions/providers.server.ts"));
const search = await jiti.import(join(frontendRoot, "src/features/search-v2/service.server.ts"));
const searchIndex = await jiti.import(join(frontendRoot, "src/features/search-v2/index.server.ts"));
const governed = await jiti.import(join(frontendRoot, "src/features/trace-v49/context/governed/index.server.ts"));
const exploration = await jiti.import(join(frontendRoot, "src/features/trace-v49/exploration-view/service.server.ts"));
const inquiries = await jiti.import(join(frontendRoot, "src/features/trace-v49/open-inquiry-v1/service.server.ts"));

/* ---- the fixed, public-safe cases: five per surface ---- */
const facets = search.publicSearchFacets();
const firstDocument = searchIndex.getPublicSearchIndex().documents[0];
const searchCases = [
  ["search-zero", { query: "zzqx-no-match", filters: {} }],
  ["search-single", { query: firstDocument.stableId, filters: {} }],
  ["search-multi", { query: "poster", filters: {} }],
  ["search-filters", { query: "poster", filters: { yearFrom: 1960, yearTo: 1969, objectType: facets.objectTypes[0].value } }],
  ["search-theme", { query: "", filters: { theme: facets.themes[0].value } }],
].map(([id, reference]) => ({ id, surface: "SEARCH_RESULTS", reference }));
const examples = governed.getGovernedContextExampleOptions();
const contextCases = examples.slice(0, 5).map((option, index) => {
  const dataset = governed.lookupGovernedContextDataset(option.stableId).data;
  const termIds = dataset.representations.map((item) => item.termId);
  const onCanvas = index % 2 === 0 ? termIds : termIds.slice(0, Math.max(0, termIds.length - 1));
  return { id: `context-${option.role}`, surface: "TRACE_CONTEXT", reference: { objectId: option.stableId, onCanvas } };
});
const points = exploration.listExplorationStartingPoints().data.starting_points;
const ladder = (label, steps) => { let view = exploration.createExplorationView({ vocabulary_id: points.find((point) => point.label === label).vocabulary_id }).data; for (let i = 0; i < steps; i += 1) { const next = exploration.applyExplorationViewAction(view.restore.map_id, { action: "MORE", expected_state_hash: view.restore.state_hash, template_id: view.restore.template_id, variant_id: view.restore.variant_id }); if (!next.ok) break; view = next.data; } return view; };
const explorationCases = [
  ["exploration-s2", ladder("design diplomacy", 0)],
  ["exploration-s3", ladder("design diplomacy", 1)],
  ["exploration-s4", ladder("design diplomacy", 2)],
  ["exploration-production", ladder("production", 1)],
  ["exploration-rejection", ladder("rejection", 0)],
].map(([id, view]) => ({ id, surface: "TRACE_VALIDATED_EXPLORATION", reference: { mapId: view.restore.map_id, stateId: view.restore.state_id } }));
const inquiryCases = inquiries.listOpenInquiries().data.data.items.slice(0, 5).map((item, index) => ({ id: `inquiry-${index + 1}`, surface: "TRACE_OPEN_INQUIRY", reference: { inquiryId: item.inquiry_id } }));
const cases = [...searchCases, ...contextCases, ...explorationCases, ...inquiryCases];

writeFileSync(ledger, "");
let calls = 0;
const rows = [];
for (const temperature of TEMPERATURES) {
  for (const item of cases) {
    for (let run = 1; run <= RUNS; run += 1) {
      if (calls >= CALL_CAP) break;
      cache.resetGuidanceCacheForTest();
      let usage = null;
      let httpStatus = null;
      const started = performance.now();
      const fetchImpl = async (url, init) => {
        const response = await fetch(url, init);
        httpStatus = response.status;
        const text = await response.text();
        try { usage = JSON.parse(text).usage ?? null; } catch { usage = null; }
        return new Response(text, { status: response.status, headers: response.headers });
      };
      calls += 1;
      let response;
      try {
        response = await svc.createSystemSuggestions({ schemaVersion: "gda-system-suggestions-request/v2", surface: item.surface, reference: item.reference }, { environment: { ...process.env, SYSTEM_SUGGESTIONS_TEMPERATURE: temperature }, fetchImpl });
      } catch (error) {
        response = { sourceClass: "ERROR", providerStatus: error.code ?? "EXCEPTION", note: error.message, suggestions: [] };
      }
      const latencyMs = Math.round(performance.now() - started);
      const row = {
        surface: item.surface, case_id: item.id, run, temperature,
        context_fingerprint: response.contextFingerprint ?? null,
        prompt_version: providers.SYSTEM_SUGGESTIONS_PROMPT_VERSION,
        config_version: providers.modelConfigVersion({ model: providers.DEEPSEEK_DEFAULT_MODEL, temperature: Number(temperature) }),
        source_class: response.sourceClass, provider_status: response.providerStatus, http_status: httpStatus,
        latency_ms: latencyMs, usage,
        note: response.note, suggestions: response.suggestions.map((suggestion) => suggestion.label), used_fact_ids: response.usedFactIds ?? [],
        content_review: response.sourceClass === "MODEL" ? "GATE_PASSED" : response.sourceClass === "STATIC_FALLBACK" ? `FALLBACK:${response.providerStatus}` : "ERROR",
      };
      rows.push(row);
      appendFileSync(ledger, `${JSON.stringify(row)}\n`);
      console.log(`${item.surface} ${item.id} #${run} t=${temperature} → ${row.source_class} ${row.provider_status} ${latencyMs}ms`);
    }
  }
}
const model = rows.filter((row) => row.source_class === "MODEL").length;
const latencies = rows.map((row) => row.latency_ms).sort((a, b) => a - b);
const percentile = (p) => latencies[Math.min(latencies.length - 1, Math.floor(p * latencies.length))] ?? 0;
const reasons = {};
for (const row of rows) if (row.source_class !== "MODEL") reasons[row.provider_status] = (reasons[row.provider_status] ?? 0) + 1;
console.log(`SYSTEM_SUGGESTS_LIVE=DONE calls=${rows.length} model_ok=${model} rate=${rows.length ? Math.round((model / rows.length) * 1000) / 10 : 0}% p50=${percentile(0.5)}ms p95=${percentile(0.95)}ms fallback_reasons=${JSON.stringify(reasons)}`);
