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
check(noKey.suggestions.length >= 2 && noKey.suggestions.length <= 4, "Search fallback must return two to four approved refinements for this result set");
check(noKey.suggestions.every((item) => item.action.kind === "SET_SEARCH_FILTER" || item.action.kind === "REMOVE_SEARCH_FILTER"), "Search suggestions must contain structured hard-filter actions only");

let capturedUrl = "";
let capturedInit;
const selectedIds = noKey.suggestions.slice(0, 2).map((item) => item.id);
const model = await createSystemSuggestions(searchRequest, {
  environment: { DEEPSEEK_API_KEY: "server-secret-value", DEEPSEEK_BASE_URL: "https://unofficial.invalid", DEEPSEEK_MODEL: "wrong-model", SYSTEM_SUGGESTIONS_PROVIDER: "auto" },
  fetchImpl: async (url, init) => {
    capturedUrl = String(url);
    capturedInit = init;
    return Response.json({ output_text: JSON.stringify({ note: "Begin with the most common public result grouping. Then apply one approved refinement.", suggestion_ids: selectedIds }) });
  },
});
const providerBody = JSON.parse(String(capturedInit.body));
check(model.sourceClass === "MODEL" && model.providerStatus === "MODEL_OK", "valid provider output must be accepted as model guidance");
check(capturedUrl === "https://api.deepseek.com/responses" && providerBody.model === "deepseek-v4-flash", "provider must enforce the official endpoint and exact model");
check(providerBody.store === false && providerBody.tools === undefined && providerBody.text.format.strict === true, "provider request must disable storage/tools and require strict structured output");
check(capturedInit.headers.Authorization === "Bearer server-secret-value" && !JSON.stringify(providerBody).includes("server-secret-value"), "key must remain in the authorization header and outside the prompt body");
check(model.suggestions.map((item) => item.id).join() === selectedIds.join(), "model may select only pre-approved suggestion IDs");

const failureCases = [
  ["provider error", async () => new Response("", { status: 500 }), "PROVIDER_ERROR"],
  ["invalid JSON", async () => Response.json({ output_text: "not json" }), "INVALID_RESPONSE"],
  ["unknown suggestion", async () => Response.json({ output_text: JSON.stringify({ note: "Use an approved refinement.", suggestion_ids: ["invented-id"] }) }), "INVALID_RESPONSE"],
  ["too few Search suggestions", async () => Response.json({ output_text: JSON.stringify({ note: "Use an approved refinement.", suggestion_ids: [] }) }), "INVALID_RESPONSE"],
  ["unsafe URL", async () => Response.json({ output_text: JSON.stringify({ note: "Open https://example.com for more.", suggestion_ids: [] }) }), "INVALID_RESPONSE"],
];
for (const [label, fetchImpl, expectedStatus] of failureCases) {
  const response = await createSystemSuggestions(searchRequest, { environment: { DEEPSEEK_API_KEY: "server-secret-value" }, fetchImpl });
  check(response.sourceClass === "STATIC_FALLBACK" && response.providerStatus === expectedStatus, `${label} must fall back safely`);
}

const timedOut = await createSystemSuggestions(searchRequest, {
  environment: { DEEPSEEK_API_KEY: "server-secret-value" },
  timeoutMsForTest: 5,
  fetchImpl: async (_url, init) => new Promise((_resolve, reject) => init.signal.addEventListener("abort", () => reject(new DOMException("timed out", "AbortError")), { once: true })),
});
check(timedOut.sourceClass === "STATIC_FALLBACK" && timedOut.providerStatus === "TIMEOUT", "provider timeout must return fallback");

const trace = await createSystemSuggestions(traceRequest, { environment: { SYSTEM_SUGGESTIONS_PROVIDER: "static" } });
check(trace.surface === "TRACE_CONTEXT" && trace.suggestions.length === 1 && trace.suggestions[0].action.parameters.actionId === "EXPAND_THEME", "TRACE fallback must keep only surface-approved valid actions");
check(!JSON.stringify(trace).match(/DeepSeek|server-secret-value|reasoning|raw/i), "public response must not expose provider identity, secret, or raw reasoning");

assert.throws(() => parseSystemSuggestionsRequest({ ...searchRequest, heldRecords: [] }), SuggestionsInputError);
checks += 1;
assert.throws(() => parseSystemSuggestionsRequest({ ...traceRequest, context: { ...traceRequest.context, labels: Array(13).fill("label") } }), SuggestionsInputError);
checks += 1;
await assert.rejects(() => createSystemSuggestions({ ...searchRequest, stateHash: "00000000" }, { environment: {} }), SuggestionsInputError);
checks += 1;
await assert.rejects(() => createSystemSuggestions({ ...searchRequest, context: { ...searchRequest.context, exactResultCount: searchRequest.context.exactResultCount + 1 } }, { environment: {} }), SuggestionsInputError);
checks += 1;
await assert.rejects(() => createSystemSuggestions({ ...traceRequest, surface: "TRACE_OPEN_INQUIRY" }, { environment: {} }), SuggestionsInputError);
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
check(finalRateResponse.status === 429 && finalRateResponse.headers.get("Retry-After") === "60", "31st request in one minute must be rate limited");

const routeSource = readFileSync(new URL("../src/app/api/system-suggestions/v1/route.ts", import.meta.url), "utf8");
const providerSource = readFileSync(new URL("../src/features/system-suggestions/providers.server.ts", import.meta.url), "utf8");
check(routeSource.includes('runtime = "nodejs"') && providerSource.includes('import "server-only"'), "provider boundary must be Node-only and server-only");
check(!/NEXT_PUBLIC_/.test(providerSource), "provider implementation must not reference browser-public environment names");

console.log(`System Suggestions contract: ${checks} checks passed`);
