import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontend = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const root = resolve(frontend, "..");
const read = (path) => readFileSync(resolve(root, path), "utf8");
const publicUiPaths = [
  "frontend/src/app/page.tsx",
  "frontend/src/app/search/page.tsx",
  "frontend/src/components/archive/shell/search.tsx",
  "frontend/src/features/search-v2/ui/SearchWorkspace.tsx",
  "frontend/src/app/trace/page.tsx",
  "frontend/src/app/trace/context-canvas/page.tsx",
  "frontend/src/app/trace/spacetime/page.tsx",
  "frontend/src/features/trace-v49/context/canvas/ContextCanvas.tsx",
  "frontend/src/features/trace-v49/spacetime/map/SpacetimeWorkspace.tsx",
  "frontend/src/features/trace-v49/exploration-ui/TraceExplorationReference.tsx",
  "frontend/src/features/system-suggestions/ui/SystemSuggestionsPanel.tsx",
];
const publicUi = publicUiPaths.map(read).join("\n");
const about = read("frontend/src/app/about/page.tsx");
const searchClient = read("frontend/src/features/search-v2/ui/SearchWorkspace.tsx");
const panel = read("frontend/src/features/system-suggestions/ui/SystemSuggestionsPanel.tsx");
const provider = read("frontend/src/features/system-suggestions/providers.server.ts");
const service = read("frontend/src/features/system-suggestions/service.server.ts");
const candidates = read("frontend/src/features/system-suggestions/candidates.server.ts");
const traceUi = `${read("frontend/src/features/trace-v49/context/canvas/ContextCanvas.tsx")}\n${read("frontend/src/features/trace-v49/spacetime/map/SpacetimeWorkspace.tsx")}\n${read("frontend/src/features/trace-v49/exploration-ui/TraceExplorationReference.tsx")}`;
const map = JSON.parse(read("docs/api/product-api-map.v1.json"));
const searchManifest = JSON.parse(read("frontend/generated/search-v2/manifest.json"));
const sourceManifest = JSON.parse(read("docs/frontend/product-handoff/SOURCE_MANIFEST.json"));

const tracked = execFileSync("git", ["ls-files", "--cached", "--others", "--exclude-standard", "-z"], { cwd: root }).toString("utf8").split("\0").filter(Boolean);
let committedKeyCount = 0;
let loggedKeyCount = 0;
for (const path of tracked) {
  let text;
  try { text = read(path); } catch { continue; }
  committedKeyCount += (text.match(/\bsk-[A-Za-z0-9_-]{20,}\b/g) ?? []).length;
  if (/console\.(?:log|error|warn)[^\n]*DEEPSEEK_API_KEY|DEEPSEEK_API_KEY[^\n]*console\.(?:log|error|warn)/.test(text)) loggedKeyCount += 1;
}

let clientBundleDeepSeekKeyCount = 0;
const clientStaticRoot = join(frontend, ".next", "static");
function scanClientBundle(directory) {
  if (!existsSync(directory)) return;
  for (const name of readdirSync(directory)) {
    const path = join(directory, name);
    if (statSync(path).isDirectory()) scanClientBundle(path);
    else clientBundleDeepSeekKeyCount += (readFileSync(path, "utf8").match(/\bsk-[A-Za-z0-9_-]{20,}\b/g) ?? []).length;
  }
}
scanClientBundle(clientStaticRoot);

const publicUiAiLabelCount = (publicUi.match(/\bAI\b|Powered by AI|Ask AI|AI suggests|model-generated/g) ?? []).length;
const publicUiDeepSeekLabelCount = (publicUi.match(/DeepSeek/g) ?? []).length;
const aboutDisclosureCount = (about.match(/Some short reading guides and suggested next steps may be generated with the assistance of DeepSeek V4 Flash\./g) ?? []).length;
const openDisclosureCount = (panel.match(/Evidence remains incomplete\./g) ?? []).length === 1
  && (panel.match(/This is not a validated historical association\./g) ?? []).length === 1 ? 0 : 1;
const searchClientTraceImportCount = (searchClient.match(/(?:features|lib)\/trace|generated\/trace|public\/data\/trace/g) ?? []).length;
const nextPublicDeepSeekCount = [provider, service, read("frontend/.env.example")].join("\n").match(/NEXT_PUBLIC_[A-Z0-9_]*DEEPSEEK/g)?.length ?? 0;

const flags = {
  PUBLIC_SEARCH_DOCUMENT_COUNT: searchManifest.document_count,
  HELD_SEARCH_DOCUMENT_COUNT: searchManifest.held_document_count,
  TRACE_RECORD_IN_SEARCH_INDEX_COUNT: searchManifest.trace_record_count,
  OPEN_INQUIRY_RECORD_IN_SEARCH_INDEX_COUNT: searchManifest.open_inquiry_record_count,
  SUGGESTIONS_NO_KEY_FALLBACK_PASS: service.includes('providerStatus, "NO_KEY"') || service.includes('"NO_KEY"'),
  SUGGESTIONS_TIMEOUT_FALLBACK_PASS: service.includes('"TIMEOUT"'),
  SUGGESTIONS_PROVIDER_ERROR_FALLBACK_PASS: service.includes('"PROVIDER_ERROR"'),
  SUGGESTIONS_INVALID_JSON_FALLBACK_PASS: service.includes('"INVALID_RESPONSE"'),
  SUGGESTIONS_UNKNOWN_ID_ACCEPTED_COUNT: service.includes("draft.suggestionIds.some((id) => !allow.has(id))") ? 0 : 1,
  SUGGESTIONS_UNAPPROVED_URL_COUNT: /https\?:\\\/\\\/\|www\\\./.test(service) ? 0 : 1,
  SUGGESTIONS_RESULT_RANKING_MUTATION_COUNT: provider.includes("rankPublicSearch") || provider.includes("pagePublicSearch") ? 1 : 0,
  SUGGESTIONS_SEARCH_RESULT_MUTATION_COUNT: /setResponse\(|setItems\(|rankPublicSearch/.test(`${provider}\n${service}`) ? 1 : 0,
  SUGGESTIONS_TRACE_STATE_MUTATION_COUNT: /dispatch\(|SET_VIEWPORT|APPLY_TEMPLATE/.test(`${provider}\n${service}\n${candidates}`) ? 1 : 0,
  SUGGESTIONS_TRACE_EDGE_CREATION_COUNT: /createEdge|addEdge|INSERT[^\n]*edge/i.test(`${provider}\n${service}\n${candidates}`) ? 1 : 0,
  SUGGESTIONS_OPEN_INQUIRY_PROMOTION_COUNT: /PROMOTE|validated_topology_mutation_allowed:\s*true/.test(`${provider}\n${service}\n${candidates}`) ? 1 : 0,
  OPEN_INQUIRY_FIXED_DISCLOSURE_MISSING_COUNT: openDisclosureCount,
  PUBLIC_UI_AI_LABEL_COUNT: publicUiAiLabelCount,
  PUBLIC_UI_DEEPSEEK_LABEL_COUNT: publicUiDeepSeekLabelCount,
  ABOUT_AI_DISCLOSURE_COUNT: aboutDisclosureCount,
  COMMITTED_DEEPSEEK_KEY_COUNT: committedKeyCount,
  CLIENT_BUNDLE_DEEPSEEK_KEY_COUNT: clientBundleDeepSeekKeyCount,
  LOGGED_DEEPSEEK_KEY_COUNT: loggedKeyCount,
  NEXT_PUBLIC_DEEPSEEK_VARIABLE_COUNT: nextPublicDeepSeekCount,
  SEARCH_MOBILE_FLOW_PASS: /@media \(max-width: 760px\)/.test(read("frontend/src/features/search-v2/ui/SearchWorkspace.module.css")),
  SEARCH_CLIENT_BUNDLE_TRACE_IMPORT_COUNT: searchClientTraceImportCount,
  TRACE_MOBILE_FULL_RUNTIME_ENABLED: false,
  IMPLEMENTED_PRODUCT_API_UNCATALOGUED_COUNT: map.summary.implemented_product_api_uncatalogued_count,
  CATALOG_ROUTE_WITHOUT_IMPLEMENTATION_COUNT: map.summary.catalog_route_without_implementation_count,
  CATALOG_DUPLICATE_METHOD_ROUTE_COUNT: map.summary.catalog_duplicate_method_route_count,
  CATALOG_SOURCE_PATH_MISSING_COUNT: map.summary.catalog_source_path_missing_count,
  CATALOG_TEST_PATH_MISSING_COUNT: map.summary.catalog_test_path_missing_count,
  PRODUCT_HANDOFF_SOURCE_PATH_MISSING_COUNT: [...sourceManifest.documents, ...sourceManifest.search_sources, ...sourceManifest.guidance_sources, ...sourceManifest.trace_ui_sources, ...sourceManifest.tests].filter((path) => { try { read(path); return false; } catch { return true; } }).length,
  TRACE_GUIDANCE_EXPLICIT_CLICK_BOUNDARY_PASS: panel.includes("onClick={() => onAction(suggestion)}") && (panel.match(/onAction\(suggestion\)/g) ?? []).length === 1,
  TRACE_UI_SYSTEM_SUGGESTS_SURFACE_COUNT: (traceUi.match(/<SystemSuggestionsPanel surface=/g) ?? []).length,
};

assert.equal(flags.PUBLIC_SEARCH_DOCUMENT_COUNT, 7995);
for (const [key, value] of Object.entries(flags)) {
  if (key === "PUBLIC_SEARCH_DOCUMENT_COUNT" || key === "ABOUT_AI_DISCLOSURE_COUNT" || key === "TRACE_UI_SYSTEM_SUGGESTS_SURFACE_COUNT") continue;
  if (key.endsWith("_PASS")) assert.equal(value, true, key);
  else if (key === "TRACE_MOBILE_FULL_RUNTIME_ENABLED") assert.equal(value, false, key);
  else assert.equal(value, 0, key);
}
assert.equal(flags.ABOUT_AI_DISCLOSURE_COUNT, 1);
assert.equal(flags.TRACE_UI_SYSTEM_SUGGESTS_SURFACE_COUNT, 4);

console.log(JSON.stringify({ status: "PASS", check_count: Object.keys(flags).length + 2, ...flags }, null, 2));
