import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import createJiti from "jiti";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(here, "..");
const jiti = createJiti(import.meta.url, { alias: { "@": join(frontendRoot, "src"), "server-only": join(here, "server-only-stub.mjs") } });
const { searchPublicObjects } = await jiti.import(join(frontendRoot, "src/features/search-v2/service.server.ts"));
const { createSystemSuggestions } = await jiti.import(join(frontendRoot, "src/features/system-suggestions/service.server.ts"));
const { resetGuidanceCacheForTest, guidanceCacheStatsForTest } = await jiti.import(join(frontendRoot, "src/features/system-suggestions/cache.server.ts"));
const { parseSystemSuggestionsRequest, SuggestionsInputError } = await jiti.import(join(frontendRoot, "src/features/system-suggestions/schema.server.ts"));
const {
  handleSystemSuggestionsRequest,
  resetSystemSuggestionsRateLimitForTest,
  systemSuggestionsMethodNotAllowedResponse,
  systemSuggestionsOptionsResponse,
} = await jiti.import(join(frontendRoot, "src/features/system-suggestions/http.server.ts"));

let checks = 0;
const check = (condition, message) => { assert.ok(condition, message); checks += 1; };
const result = searchPublicObjects({ query: "poster", filters: { yearFrom: 1960, yearTo: 1969 }, first: 1 });
const searchRequest = {
  schemaVersion: "gda-system-suggestions-request/v1",
  surface: "SEARCH_RESULTS",
  stateHash: result.stateHash,
  context: {
    query: result.query.text,
    filters: result.query.filters,
    exactResultCount: result.pageInfo.totalExact,
    aggregates: {
      topDecades: result.aggregateSummary.topDecades,
      topObjectTypes: result.aggregateSummary.topObjectTypes,
      topThemes: result.aggregateSummary.topThemes,
      topMovements: result.aggregateSummary.topMovements,
    },
  },
};
const traceRequest = {
  schemaVersion: "gda-system-suggestions-request/v1",
  surface: "TRACE_CONTEXT",
  stateHash: "context_state_1234",
  context: {
    stateType: "CONTEXT_CANVAS",
    labels: ["Poster", "Modern typography and layout"],
    counts: { publicObjects: 12 },
    validActionIds: ["EXPAND_THEME", "NOT_A_REAL_ACTION"],
    evidenceClass: "PUBLIC_CONTEXT",
  },
};

let fetchedWithoutKey = false;
const noKey = await createSystemSuggestions(searchRequest, { environment: {}, fetchImpl: async () => { fetchedWithoutKey = true; throw new Error("must not fetch"); } });
check(noKey.sourceClass === "STATIC_FALLBACK" && noKey.providerStatus === "NO_KEY" && !fetchedWithoutKey, "missing key must return fallback without a provider request");
check(noKey.suggestions.length >= 1 && noKey.suggestions.length <= 2, "Search fallback returns at most two approved refinements for this result set");
check(noKey.contextFingerprint && noKey.stateHash === searchRequest.stateHash, "a verified v1 Search request answers with the server's fingerprint and echoes the page's state hash");
check(noKey.suggestions.every((item) => item.action.kind === "SET_SEARCH_FILTER" || item.action.kind === "REMOVE_SEARCH_FILTER"), "Search suggestions must contain structured hard-filter actions only");

let capturedUrl = "";
let capturedInit;
const selectedIds = noKey.suggestions.slice(0, 2).map((item) => item.id);
const model = await createSystemSuggestions(searchRequest, {
  environment: { DEEPSEEK_API_KEY: "server-secret-value", DEEPSEEK_BASE_URL: "https://unofficial.invalid", DEEPSEEK_MODEL: "wrong-model", SYSTEM_SUGGESTIONS_PROVIDER: "auto" },
  fetchImpl: async (url, init) => {
    capturedUrl = String(url);
    capturedInit = init;
    return Response.json({ status: "completed", output: [{ type: "reasoning", summary: [] }, { type: "message", role: "assistant", status: "completed", content: [{ type: "output_text", text: JSON.stringify({ note: `${noKey.note.split(". ")[0]}.`, used_fact_ids: ["S1"], suggestion_ids: selectedIds }) }] }] });
  },
});
const providerBody = JSON.parse(String(capturedInit.body));
check(model.sourceClass === "MODEL" && model.providerStatus === "MODEL_OK", "valid provider output must be accepted as model guidance");
check(providerBody.reasoning?.effort === "none" && providerBody.max_output_tokens === 512 && providerBody.temperature === 0 && providerBody.stream === undefined, "provider request must disable reasoning and streaming, bound the output and pin the sampling");
check(Array.isArray(providerBody.input) && providerBody.input[1].content[0].text.includes('"statements"') && !providerBody.input[1].content[0].text.includes("aggregates"), "the model receives fact statements, not the client's context");
check(model.usedFactIds.join() === "S1", "the model's used fact ids are returned");
check(capturedUrl === "https://api.deepseek.com/responses" && providerBody.model === "deepseek-v4-flash", "provider must enforce the official endpoint and exact model");
check(providerBody.store === false && providerBody.tools === undefined && providerBody.text.format.strict === true, "provider request must disable storage/tools and require strict structured output");
check(capturedInit.headers.Authorization === "Bearer server-secret-value" && !JSON.stringify(providerBody).includes("server-secret-value"), "key must remain in the authorization header and outside the prompt body");
check(model.suggestions.map((item) => item.id).join() === selectedIds.join(), "model may select only pre-approved suggestion IDs");

const completedText = text => Response.json({status:"completed", output:[{type:"message",role:"assistant",status:"completed",content:[{type:"output_text",text}]}]});
const failureCases = [
  ["provider error", async () => new Response("", { status: 500 }), "PROVIDER_ERROR"],
  ["invalid JSON", async () => completedText("not json"), "PROVIDER_OUTPUT_INVALID"],
  ["unknown suggestion", async () => completedText(JSON.stringify({ note: `${noKey.note.split(". ")[0]}.`, suggestion_ids: ["invented-id"], used_fact_ids: [] })), "INVALID_RESPONSE"],
  ["unsafe URL", async () => completedText(JSON.stringify({ note: "Open https://example.com for more.", suggestion_ids: [], used_fact_ids: [] })), "INVALID_RESPONSE"],
  ["reasoning only", async () => Response.json({ status: "completed", output: [{ type: "reasoning", summary: [{ type: "summary_text", text: "thinking" }] }] }), "PROVIDER_OUTPUT_MISSING"],
  ["incomplete", async () => Response.json({ status: "incomplete", incomplete_details: { reason: "max_output_tokens" }, output: [{ type: "message", role: "assistant", status: "completed", content: [{ type: "output_text", text: "{\"note\":\"" }] }] }), "PROVIDER_INCOMPLETE"],
  ["empty content", async () => Response.json({ status: "completed", output: [{ type: "message", role: "assistant", status: "completed", content: [] }] }), "PROVIDER_OUTPUT_MISSING"],
  ["rate limited", async () => new Response("", { status: 429 }), "PROVIDER_RATE_LIMITED"],
  ["unsupplied number", async () => completedText(JSON.stringify({ note: "About 1,000 public objects match this Search.", suggestion_ids: [], used_fact_ids: [] })), "INVALID_RESPONSE"],
  ["source count", async () => completedText(JSON.stringify({ note: `${noKey.note.split(". ")[0]} from one source.`, suggestion_ids: [], used_fact_ids: [] })), "INVALID_RESPONSE"],
];
for (const [label, fetchImpl, expectedStatus] of failureCases) {
  resetGuidanceCacheForTest();
  const response = await createSystemSuggestions(searchRequest, { environment: { DEEPSEEK_API_KEY: "server-secret-value" }, fetchImpl });
  check(response.sourceClass === "STATIC_FALLBACK" && response.providerStatus === expectedStatus, `${label} must fall back safely (got ${response.providerStatus})`);
}
/* zero suggestions is a legal model answer for Search */
resetGuidanceCacheForTest();
const zero = await createSystemSuggestions(searchRequest, { environment: { DEEPSEEK_API_KEY: "server-secret-value" }, fetchImpl: async () => completedText(JSON.stringify({ note: `${noKey.note.split(". ")[0]}.`, suggestion_ids: [], used_fact_ids: [] })) });
check(zero.sourceClass === "MODEL" && zero.suggestions.length === 0, "a model answer with zero suggestions is accepted for Search");
/* the cache: the same facts are not requested twice; a provider failure after a good answer serves the good answer */
resetGuidanceCacheForTest();
let fetches = 0;
const good = async () => { fetches += 1; return completedText(JSON.stringify({ note: `${noKey.note.split(". ")[0]}.`, suggestion_ids: [], used_fact_ids: [] })); };
const first = await createSystemSuggestions(searchRequest, { environment: { DEEPSEEK_API_KEY: "server-secret-value" }, fetchImpl: good });
const second = await createSystemSuggestions(searchRequest, { environment: { DEEPSEEK_API_KEY: "server-secret-value" }, fetchImpl: good });
check(first.providerStatus === "MODEL_OK" && second.providerStatus === "MODEL_OK_CACHED" && fetches === 1 && second.note === first.note, "the same facts answer from the cache without a second provider call");
const [mergedA, mergedB] = await Promise.all([
  createSystemSuggestions({ ...searchRequest, context: searchRequest.context }, { environment: { DEEPSEEK_API_KEY: "server-secret-value", DEEPSEEK_MODEL: "deepseek-v4-flash", SYSTEM_SUGGESTIONS_TEMPERATURE: "0.2" }, fetchImpl: good }),
  createSystemSuggestions({ ...searchRequest, context: searchRequest.context }, { environment: { DEEPSEEK_API_KEY: "server-secret-value", DEEPSEEK_MODEL: "deepseek-v4-flash", SYSTEM_SUGGESTIONS_TEMPERATURE: "0.2" }, fetchImpl: good }),
]);
check(fetches === 2 && mergedA.note === mergedB.note && guidanceCacheStatsForTest().merged === 1, "two simultaneous requests for the same facts and configuration share one provider call; another temperature is another key");
const afterFailure = await createSystemSuggestions(searchRequest, { environment: { DEEPSEEK_API_KEY: "server-secret-value" }, fetchImpl: async () => new Response("", { status: 500 }), now: () => Date.now() + 6 * 60_000 });
check(afterFailure.providerStatus === "LAST_GOOD_AFTER_PROVIDER_ERROR" && afterFailure.sourceClass === "MODEL" && afterFailure.note === first.note, "after the cache expires, a provider failure serves the last good note for the same facts");
resetGuidanceCacheForTest();

const timedOut = await createSystemSuggestions(searchRequest, {
  environment: { DEEPSEEK_API_KEY: "server-secret-value" },
  timeoutMsForTest: 5,
  fetchImpl: async (_url, init) => new Promise((_resolve, reject) => init.signal.addEventListener("abort", () => reject(new DOMException("timed out", "AbortError")), { once: true })),
});
check(timedOut.sourceClass === "STATIC_FALLBACK" && timedOut.providerStatus === "TIMEOUT", "provider timeout must return fallback");

const trace = await createSystemSuggestions(traceRequest, { environment: { SYSTEM_SUGGESTIONS_PROVIDER: "static" } });
check(trace.surface === "TRACE_CONTEXT" && trace.suggestions.length === 0 && trace.note.startsWith("Guidance is unavailable for this legacy state."), "Unverified legacy TRACE returns no factual note or actions");
let legacyFetched = false;
const legacy = await createSystemSuggestions(traceRequest, { environment: { DEEPSEEK_API_KEY: "server-secret-value" }, fetchImpl: async () => { legacyFetched = true; throw new Error("must not fetch"); } });
check(legacy.providerStatus === "LEGACY_CONTEXT_STATIC" && !legacyFetched, "a v1 TRACE context that describes its own facts is never sent to a model");
check(!JSON.stringify(trace).match(/DeepSeek|server-secret-value|reasoning|raw/i), "public response must not expose provider identity, secret, or raw reasoning");

assert.throws(() => parseSystemSuggestionsRequest({ ...searchRequest, heldRecords: [] }), SuggestionsInputError);
checks += 1;
assert.throws(() => parseSystemSuggestionsRequest({ ...traceRequest, context: { ...traceRequest.context, labels: Array(13).fill("label") } }), SuggestionsInputError);
checks += 1;
await assert.rejects(() => createSystemSuggestions({ ...searchRequest, stateHash: "00000000" }, { environment: {} }), SuggestionsInputError);
checks += 1;
await assert.rejects(() => createSystemSuggestions({ ...searchRequest, context: { ...searchRequest.context, exactResultCount: searchRequest.context.exactResultCount + 1 } }, { environment: {} }), SuggestionsInputError);
checks += 1;
check((await createSystemSuggestions({ ...traceRequest, surface: "TRACE_OPEN_INQUIRY" }, { environment: {} })).note.startsWith("Guidance is unavailable for this legacy state."), "unverified cross-surface legacy state has no factual description");
checks += 1;

check(systemSuggestionsOptionsResponse().status === 204, "OPTIONS must return 204");
check(systemSuggestionsMethodNotAllowedResponse().status === 405, "unsupported methods must return 405");
const oversized = await handleSystemSuggestionsRequest(new Request("http://local/api/system-suggestions/v1", { method: "POST", headers: { "content-length": "16385" }, body: "{}" }));
check(oversized.status === 413, "declared oversized body must return 413");

resetSystemSuggestionsRateLimitForTest();
const priorMode = process.env.SYSTEM_SUGGESTIONS_PROVIDER;
process.env.SYSTEM_SUGGESTIONS_PROVIDER = "static";
let finalRateResponse;
for (let index = 0; index < 31; index += 1) {
  finalRateResponse = await handleSystemSuggestionsRequest(new Request("http://local/api/system-suggestions/v1", { method: "POST", headers: { "content-type": "application/json", "x-forwarded-for": "192.0.2.10" }, body: JSON.stringify(traceRequest) }));
}
if (priorMode === undefined) delete process.env.SYSTEM_SUGGESTIONS_PROVIDER;
else process.env.SYSTEM_SUGGESTIONS_PROVIDER = priorMode;
check(finalRateResponse.status === 200 || finalRateResponse.status === 429, "missing Redis degrades safely; real shared quota is tested by verify:system-suggestions-final-v2");

const routeSource = readFileSync(new URL("../src/app/api/system-suggestions/v1/route.ts", import.meta.url), "utf8");
const providerSource = readFileSync(new URL("../src/features/system-suggestions/providers.server.ts", import.meta.url), "utf8");
check(routeSource.includes('runtime = "nodejs"') && providerSource.includes('import "server-only"'), "provider boundary must be Node-only and server-only");
check(!/NEXT_PUBLIC_/.test(providerSource), "provider implementation must not reference browser-public environment names");

console.log(`System Suggestions contract: ${checks} checks passed`);
