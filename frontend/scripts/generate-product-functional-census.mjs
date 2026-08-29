import { createHash } from "node:crypto";
import { existsSync, readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { dirname, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const frontend = resolve(here, "..");
const root = resolve(frontend, "..");
const outputPath = resolve(root, "docs/frontend/product-handoff/product-functional-census.v1.json");
const masterPath = resolve(root, "docs/frontend/product-handoff/FRONTEND_FUNCTIONAL_ARCHITECTURE_AND_SCALE_CENSUS.md");
const checkOnly = process.argv.includes("--check");
const writeJson = process.argv.includes("--write-json") || process.argv.includes("--write-all");
const writeMaster = process.argv.includes("--write-master") || process.argv.includes("--write-all");
const sourceSha = "4fbb3d559a98614e8cd94656a8871db18ee06f3c";

const sha256 = (value) => createHash("sha256").update(value).digest("hex");
const read = (path) => readFileSync(resolve(root, path), "utf8");
const json = (path) => JSON.parse(read(path));
const pathExists = (path) => existsSync(resolve(root, path));
const fileHash = (path) => sha256(readFileSync(resolve(root, path)));
const quote = (value) => String(value).replaceAll("|", "\\|").replaceAll("\n", " ");

function walk(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const absolute = resolve(directory, entry.name);
    return entry.isDirectory() ? walk(absolute) : [absolute];
  });
}

function appRoute(path) {
  const value = relative(resolve(frontend, "src/app"), path).replaceAll("\\", "/");
  const withoutPage = value === "page.tsx" || value === "page.ts" ? "" : value.replace(/\/page\.tsx?$/, "");
  return `/${withoutPage}`.replace(/\[([^\]]+)\]/g, "{$1}").replace(/\/+/g, "/").replace(/\/$/, "") || "/";
}

const zoneIds = [
  "zone.home", "zone.global-navigation", "zone.search", "zone.search-filters", "zone.search-results",
  "zone.search-pagination", "zone.object-detail", "zone.about-methodology", "zone.trace-entry",
  "zone.context-canvas", "zone.spacetime", "zone.validated-exploration", "zone.open-inquiry",
  "zone.trace-exports", "zone.system-suggestions", "zone.shared-states",
];

const zoneSourcePaths = {
  "zone.home": ["frontend/src/app/page.tsx"],
  "zone.global-navigation": ["frontend/src/app/layout.tsx", "frontend/src/app/page.tsx"],
  "zone.search": ["frontend/src/app/search/page.tsx", "frontend/src/features/search-v2/ui/SearchWorkspace.tsx", "frontend/src/features/search-v2/service.server.ts"],
  "zone.search-filters": ["frontend/src/features/search-v2/ui/SearchWorkspace.tsx", "frontend/src/features/search-v2/http.server.ts"],
  "zone.search-results": ["frontend/src/features/search-v2/ui/SearchWorkspace.tsx", "frontend/src/features/search-v2/service.server.ts"],
  "zone.search-pagination": ["frontend/src/features/search-v2/ui/SearchWorkspace.tsx", "frontend/src/features/search-v2/http.server.ts"],
  "zone.object-detail": ["frontend/src/app/surfaces/[id]/page.tsx", "frontend/src/lib/read-platform/server/read-api-controller.ts"],
  "zone.about-methodology": ["frontend/src/app/about/page.tsx"],
  "zone.trace-entry": ["frontend/src/app/trace/page.tsx", "frontend/src/features/trace-v49/exploration-ui/TraceExplorationReference.tsx", "frontend/src/features/trace-v49/mobile.server.tsx"],
  "zone.context-canvas": ["frontend/src/app/trace/context-canvas/page.tsx", "frontend/src/features/trace-v49/context/canvas/ContextCanvas.tsx"],
  "zone.spacetime": ["frontend/src/app/trace/spacetime/page.tsx", "frontend/src/features/trace-v49/spacetime/map/SpacetimeWorkspace.tsx"],
  "zone.validated-exploration": ["frontend/src/features/trace-v49/exploration-ui/TraceExplorationReference.tsx"],
  "zone.open-inquiry": ["frontend/src/features/trace-v49/exploration-ui/TraceExplorationReference.tsx"],
  "zone.trace-exports": ["frontend/src/features/trace-v49/exploration-ui/TraceExplorationReference.tsx"],
  "zone.system-suggestions": ["frontend/src/features/system-suggestions/ui/SystemSuggestionsPanel.tsx", "frontend/src/features/system-suggestions/service.server.ts"],
  "zone.shared-states": ["frontend/src/app/error.tsx", "frontend/src/app/not-found.tsx"],
};

const zoneTestPaths = {
  "zone.home": ["frontend/scripts/verify-home-archive-box.mjs"],
  "zone.global-navigation": ["frontend/scripts/verify-home-archive-box.mjs"],
  "zone.search": ["frontend/scripts/test-search-v2-api.mjs", "frontend/scripts/test-search-v2-ui.mjs"],
  "zone.search-filters": ["frontend/scripts/test-search-v2-api.mjs", "frontend/scripts/test-search-v2-ui.mjs"],
  "zone.search-results": ["frontend/scripts/test-search-v2-api.mjs", "frontend/scripts/test-search-v2-ui.mjs"],
  "zone.search-pagination": ["frontend/scripts/test-search-v2-api.mjs"],
  "zone.object-detail": ["frontend/scripts/run-v49-api-read-contract-closure.mjs"],
  "zone.about-methodology": ["frontend/scripts/verify-about-mobile.mjs"],
  "zone.trace-entry": ["frontend/scripts/test-trace-system-suggestions-ui.mjs"],
  "zone.context-canvas": ["frontend/scripts/verify-context-api-v1.mjs", "frontend/scripts/verify-context-governance-v1.mjs"],
  "zone.spacetime": ["frontend/scripts/verify-spacetime-api-v1.mjs", "frontend/scripts/verify-spacetime-governance-v1.mjs"],
  "zone.validated-exploration": ["frontend/scripts/test-trace-exploration-v2.mjs"],
  "zone.open-inquiry": ["frontend/scripts/test-trace-open-inquiry-v1.mjs"],
  "zone.trace-exports": ["frontend/scripts/test-trace-exploration-v2.mjs"],
  "zone.system-suggestions": ["frontend/scripts/test-system-suggestions.mjs", "frontend/scripts/test-trace-system-suggestions-ui.mjs"],
  "zone.shared-states": ["frontend/scripts/test-search-v2-ui.mjs"],
};

const zones = [
  ["zone.home", "Homepage Search entry", "Global Search", "/", "DESKTOP_AND_MOBILE", ["enter query", "choose starter", "open TRACE"], ["zone.search", "zone.trace-entry"], ["search.facets.v1"], "Search form and four deterministic starters; no model request.", "FUNCTIONALLY_READY"],
  ["zone.global-navigation", "Global navigation", "Shared product", "/", "DESKTOP_AND_MOBILE", ["navigate Search", "navigate TRACE", "navigate About"], ["zone.home", "zone.search", "zone.trace-entry", "zone.about-methodology"], [], "Navigation never creates evidence, ranking, or provider state.", "BACKEND_READY_FRONTEND_NOT_DESIGNED"],
  ["zone.search", "Global Search workspace", "Global Search", "/search", "DESKTOP_AND_MOBILE", ["submit query", "retry", "clear"], ["zone.search-filters", "zone.search-results", "zone.search-pagination", "zone.system-suggestions"], ["search.public-objects.v1", "search.facets.v1"], "URL-bound public object retrieval; no TRACE import.", "FUNCTIONALLY_READY"],
  ["zone.search-filters", "Search filters", "Global Search", "/search", "DESKTOP_AND_MOBILE", ["set year range", "select type", "select theme", "select movement"], ["zone.search"], ["search.public-objects.v1", "search.facets.v1"], "Hard conjunctive filters; empty text is allowed only with a filter.", "FUNCTIONALLY_READY"],
  ["zone.search-results", "Search result cards", "Global Search", "/search", "DESKTOP_AND_MOBILE", ["open public object"], ["zone.object-detail"], ["search.public-objects.v1"], "Text/citation result DTOs only; no thumbnail field exists in the API.", "FUNCTIONALLY_READY"],
  ["zone.search-pagination", "Search pagination", "Global Search", "/search", "DESKTOP_AND_MOBILE", ["open next cursor page", "return with browser history"], ["zone.search"], ["search.public-objects.v1"], "Opaque cursor is release, index, algorithm, and query/filter bound.", "FUNCTIONALLY_READY"],
  ["zone.object-detail", "Object Detail", "Shared product", "/surfaces/{id}", "DESKTOP_AND_MOBILE", ["read public metadata", "follow permitted citation"], ["zone.search"], ["read.surface-detail.v1"], "Current page is metadata/citation-only; image delivery is not assumed.", "BACKEND_READY_FRONTEND_NOT_DESIGNED"],
  ["zone.about-methodology", "About / Methodology", "Shared product", "/about", "DESKTOP_AND_MOBILE", ["read method", "read guidance disclosure"], [], [], "Public methodology and the sole ordinary-product guidance disclosure.", "BACKEND_READY_FRONTEND_NOT_DESIGNED"],
  ["zone.trace-entry", "TRACE entry / Exploration", "TRACE", "/trace", "MOBILE_LIGHTWEIGHT_FALLBACK", ["open Context Canvas", "open Spacetime", "inspect validated exploration", "read Open Inquiry"], ["zone.context-canvas", "zone.spacetime", "zone.validated-exploration", "zone.open-inquiry"], ["trace.f3.validated.v2.capabilities.get", "trace.f3.open-inquiry.v1.list"], "Desktop research entry; mobile returns desktop-required state before governed imports.", "BACKEND_READY_FRONTEND_NOT_DESIGNED"],
  ["zone.context-canvas", "Context Canvas", "TRACE", "/trace/context-canvas", "MOBILE_LIGHTWEIGHT_FALLBACK", ["load public record", "add/remove representation", "undo/redo", "export PNG"], ["zone.system-suggestions", "zone.trace-exports"], ["trace.f1.context.object-context.v1"], "Project-curated context, not a historical relation; accessible rows are required.", "FUNCTIONALLY_READY"],
  ["zone.spacetime", "Spacetime", "TRACE", "/trace/spacetime", "MOBILE_LIGHTWEIGHT_FALLBACK", ["select period", "select geography", "load more records", "change renderer"], ["zone.system-suggestions", "zone.trace-exports"], ["trace.f2.spacetime.periods.v1", "trace.f2.spacetime.atlas.v1", "trace.f2.spacetime.geography-records.v1"], "Aggregate recorded context; never object coordinates or semantic edges.", "FUNCTIONALLY_READY"],
  ["zone.validated-exploration", "Validated Exploration", "TRACE", "/trace", "MOBILE_LIGHTWEIGHT_FALLBACK", ["create map", "select approved action", "read tree", "inspect association"], ["zone.trace-exports", "zone.system-suggestions", "zone.open-inquiry"], ["trace.f3.validated.v2.capabilities.get", "trace.f3.validated.v2.categories.list", "trace.f3.validated.v2.maps.create", "trace.f3.validated.v2.maps.get", "trace.f3.validated.v2.maps.actions", "trace.f3.validated.v2.vocabulary.get", "trace.f3.validated.v2.associations.get"], "V2 is the functional validated contract; V3 has no production activation and is not a product screen.", "FUNCTIONALLY_READY"],
  ["zone.open-inquiry", "Open Inquiry", "TRACE", "/trace", "MOBILE_LIGHTWEIGHT_FALLBACK", ["read inventory", "open inquiry detail", "inspect provenance"], ["zone.system-suggestions"], ["trace.f3.open-inquiry.v1.list", "trace.f3.open-inquiry.v1.detail"], "Fixed unresolved disclosure precedes guidance; never merge with validated data, topology, metric, or export.", "BACKEND_READY_FRONTEND_NOT_DESIGNED"],
  ["zone.trace-exports", "TRACE exports", "TRACE", "/trace", "DESKTOP_ONLY", ["prepare manifest", "download PNG", "download SVG", "export Context PNG"], ["zone.context-canvas", "zone.validated-exploration"], ["trace.f3.validated.v2.exports.manifest", "trace.f3.validated.v2.exports.png", "trace.f3.validated.v2.exports.svg"], "Validated diagrams/text only; Open Inquiry has no export.", "FUNCTIONALLY_READY"],
  ["zone.system-suggestions", "System Suggestions", "Shared product", "/search and TRACE", "DESKTOP_AND_MOBILE", ["read guidance", "explicitly select allowed suggestion"], ["zone.search", "zone.context-canvas", "zone.spacetime", "zone.validated-exploration", "zone.open-inquiry"], ["guidance.system-suggestions.v1"], "Optional guidance; fallback is deterministic; provider identity/status never renders in ordinary UI.", "FUNCTIONALLY_READY"],
  ["zone.shared-states", "Shared loading, empty, partial, and error states", "Shared product", "all active routes", "DESKTOP_AND_MOBILE", ["retry allowed request", "retain state"], zoneIds.filter((id) => id !== "zone.shared-states"), [], "Loading is request-scoped; errors fail closed; no stale cross-layer substitution.", "BACKEND_READY_FRONTEND_NOT_DESIGNED"],
].map(([zone_id, canonical_name, product_area, entry_route, desktop_mobile_policy, primary_user_actions, related_zone_ids, required_API_ids, summary, implementation_readiness]) => ({
  zone_id, canonical_name, product_area, user_goal: summary, entry_route, desktop_mobile_policy,
  primary_user_actions, secondary_user_actions: [], required_API_ids, required_data: summary,
  state_list: ["loading", "ready", "empty_or_zero", "partial_when_contractual", "error_or_fallback"],
  loading_behavior: "Request-scoped live status; preserve current valid state until replacement is valid.",
  empty_behavior: "Render only an explicit successful empty state; do not infer data.",
  partial_data_behavior: "Show bounded partial state only where its API declares continuation.",
  error_behavior: "Use safe service error; do not substitute another data/evidence layer.",
  retry_behavior: "Explicit retry only where the current contract permits it.",
  export_behavior: zone_id === "zone.trace-exports" ? "See export_capabilities; no third-party image export." : "No independent export.",
  System_Suggestions_behavior: zone_id === "zone.system-suggestions" ? "Optional server-validated guidance; no automatic state mutation." : "Guidance may be shown only as optional secondary orientation.",
  provenance_requirements: "Preserve server-provided release, public/evidence, and state identities; no client inference.",
  rights_constraints: zone_id.startsWith("zone.search") || zone_id === "zone.object-detail" ? "No image or thumbnail assumption; use public metadata/citation boundary." : "No unlicensed or inferred visual material.",
  accessibility_requirements: "Keyboard-operable controls, labelled status, and an equivalent textual representation for non-spatial TRACE data.",
  responsive_requirements: desktop_mobile_policy === "MOBILE_LIGHTWEIGHT_FALLBACK" ? "Mobile returns the intentional desktop-required state and Search option." : "Reflow ordinary reading and controls without semantic loss.",
  source_paths: zoneSourcePaths[zone_id], test_paths: zoneTestPaths[zone_id], implementation_readiness,
  frontend_design_readiness: implementation_readiness === "FUNCTIONALLY_READY" ? "BACKEND_READY_FRONTEND_NOT_DESIGNED" : implementation_readiness,
  remaining_design_decisions: ["layout", "visual hierarchy", "typography", "spacing", "colour", "motion within accessibility constraints"],
}));

const pageCatalog = {
  "/": ["ACTIVE_PUBLIC_PRODUCT", "Global Search", ["zone.home", "zone.global-navigation"], "DESKTOP_AND_MOBILE", "Homepage entry for public object Search and TRACE.", true, true, "Current homepage is the canonical product entry."],
  "/search": ["ACTIVE_PUBLIC_PRODUCT", "Global Search", ["zone.search", "zone.search-filters", "zone.search-results", "zone.search-pagination", "zone.system-suggestions"], "DESKTOP_AND_MOBILE", "Search public objects with URL-preserved filters and cursor.", true, true, "Current functional Search implementation."],
  "/surfaces/{id}": ["ACTIVE_PUBLIC_PRODUCT", "Shared product", ["zone.object-detail"], "DESKTOP_AND_MOBILE", "Read a public object-detail route.", true, true, "Search target route; current detail UI remains metadata/citation only."],
  "/about": ["ACTIVE_PUBLIC_PRODUCT", "Shared product", ["zone.about-methodology"], "DESKTOP_AND_MOBILE", "Read methodology, provenance, and guidance disclosure.", true, true, "Required shared product information route."],
  "/trace": ["ACTIVE_PUBLIC_PRODUCT", "TRACE", ["zone.trace-entry", "zone.validated-exploration", "zone.open-inquiry"], "MOBILE_LIGHTWEIGHT_FALLBACK", "Enter desktop TRACE research environment.", true, true, "Top-level TRACE entry; full mobile runtime is intentionally disabled."],
  "/trace/context-canvas": ["ACTIVE_REFERENCE_IMPLEMENTATION", "TRACE", ["zone.context-canvas", "zone.system-suggestions", "zone.trace-exports"], "MOBILE_LIGHTWEIGHT_FALLBACK", "Run governed Context Canvas workspace.", true, true, "Functional unlinked reference workspace to design for final TRACE IA."],
  "/trace/spacetime": ["ACTIVE_REFERENCE_IMPLEMENTATION", "TRACE", ["zone.spacetime", "zone.system-suggestions"], "MOBILE_LIGHTWEIGHT_FALLBACK", "Run governed Spacetime workspace.", true, true, "Functional unlinked reference workspace to design for final TRACE IA."],
  "/trace/types/{type}": ["ACTIVE_REFERENCE_IMPLEMENTATION", "TRACE legacy", [], "DESKTOP_ONLY", "Read legacy TRACE type material.", false, false, "Historical/reference route; not one of the three final TRACE functions."],
  "/contents": ["DOCUMENTATION_OR_METHOD", "Method", ["zone.about-methodology"], "DESKTOP_AND_MOBILE", "Read methods and sources index.", false, false, "Documentation supports methodology but is not a final product screen."],
  "/folders": ["LEGACY_PUBLIC", "Legacy archive", [], "DESKTOP_AND_MOBILE", "Browse historical folder prototype.", false, false, "Legacy read-platform surface; final IA is Search-first."],
  "/folders/{type}": ["LEGACY_PUBLIC", "Legacy archive", [], "DESKTOP_AND_MOBILE", "Browse historical folder type prototype.", false, false, "Legacy read-platform surface; final IA is Search-first."],
  "/folders/{type}/{slug}": ["LEGACY_PUBLIC", "Legacy archive", [], "DESKTOP_AND_MOBILE", "Browse historical folder detail prototype.", false, false, "Legacy read-platform surface; final IA is Search-first."],
  "/appendix": ["INTERNAL_TEST_OR_DEMO", "Design laboratory", [], "NOT_USER_FACING", "Inspect appendix layout study.", false, false, "Asset study only."],
  "/badges": ["INTERNAL_TEST_OR_DEMO", "Design laboratory", [], "NOT_USER_FACING", "Inspect badge layout study.", false, false, "Asset study only."],
  "/bookmarks": ["INTERNAL_TEST_OR_DEMO", "Design laboratory", [], "NOT_USER_FACING", "Inspect bookmark layout study.", false, false, "Asset study only."],
  "/bookmarks/horizontal": ["INTERNAL_TEST_OR_DEMO", "Design laboratory", [], "NOT_USER_FACING", "Inspect horizontal bookmark study.", false, false, "Asset study only."],
  "/bookmarks/vertical": ["INTERNAL_TEST_OR_DEMO", "Design laboratory", [], "NOT_USER_FACING", "Inspect vertical bookmark study.", false, false, "Asset study only."],
  "/cards": ["INTERNAL_TEST_OR_DEMO", "Design laboratory", [], "NOT_USER_FACING", "Inspect card layout study.", false, false, "Asset study only."],
  "/cards/color": ["INTERNAL_TEST_OR_DEMO", "Design laboratory", [], "NOT_USER_FACING", "Inspect card colour study.", false, false, "Asset study only."],
  "/cards/dense": ["INTERNAL_TEST_OR_DEMO", "Design laboratory", [], "NOT_USER_FACING", "Inspect dense card study.", false, false, "Asset study only."],
  "/cards/rectangle": ["INTERNAL_TEST_OR_DEMO", "Design laboratory", [], "NOT_USER_FACING", "Inspect rectangle card study.", false, false, "Asset study only."],
  "/cards/special": ["INTERNAL_TEST_OR_DEMO", "Design laboratory", [], "NOT_USER_FACING", "Inspect special card study.", false, false, "Asset study only."],
  "/cards/square": ["INTERNAL_TEST_OR_DEMO", "Design laboratory", [], "NOT_USER_FACING", "Inspect square card study.", false, false, "Asset study only."],
  "/main-sheets": ["INTERNAL_TEST_OR_DEMO", "Design laboratory", [], "NOT_USER_FACING", "Inspect main-sheet asset study.", false, false, "Asset study only."],
  "/reading-notes": ["INTERNAL_TEST_OR_DEMO", "Design laboratory", [], "NOT_USER_FACING", "Inspect reading-note asset study.", false, false, "Asset study only."],
  "/slips": ["INTERNAL_TEST_OR_DEMO", "Design laboratory", [], "NOT_USER_FACING", "Inspect source-slip asset study.", false, false, "Asset study only."],
  "/sub-sheets": ["INTERNAL_TEST_OR_DEMO", "Design laboratory", [], "NOT_USER_FACING", "Inspect sub-sheet asset study.", false, false, "Asset study only."],
  "/text-pages": ["INTERNAL_TEST_OR_DEMO", "Design laboratory", [], "NOT_USER_FACING", "Inspect text-page asset study.", false, false, "Asset study only."],
};

const frontendRequired = new Set([
  "search.public-objects.v1", "search.facets.v1", "read.surface-detail.v1",
  "trace.f1.context.object-context.v1", "trace.f2.spacetime.periods.v1", "trace.f2.spacetime.atlas.v1", "trace.f2.spacetime.geography-records.v1",
  "trace.f3.validated.v2.associations.get", "trace.f3.validated.v2.capabilities.get", "trace.f3.validated.v2.categories.list",
  "trace.f3.validated.v2.exports.svg", "trace.f3.validated.v2.exports.manifest", "trace.f3.validated.v2.exports.png",
  "trace.f3.validated.v2.maps.create", "trace.f3.validated.v2.maps.get", "trace.f3.validated.v2.maps.actions", "trace.f3.validated.v2.vocabulary.get",
  "trace.f3.open-inquiry.v1.list", "trace.f3.open-inquiry.v1.detail",
]);

function apiClass(apiId) {
  if (frontendRequired.has(apiId)) return "FRONTEND_REQUIRED_NOW";
  if (apiId === "guidance.system-suggestions.v1") return "FRONTEND_OPTIONAL";
  if (apiId.includes(".retired-")) return "RETIRED";
  if (apiId.includes(".v3.control.")) return "INTERNAL_RESEARCH_CONTROL";
  if (apiId.startsWith("trace.f3.validated.v3.") || apiId === "read.visual-registry-current.v1") return "FAIL_CLOSED";
  if (["read.release.v1", "read.release-manifest.v1", "read.archive-overview.v1", "trace.f3.validated.v2.root"].includes(apiId)) return "SERVER_SIDE_SUPPORT";
  return "LEGACY_COMPATIBILITY";
}

function apiZones(apiId) {
  return zones.filter((zone) => zone.required_API_ids.includes(apiId)).map((zone) => zone.zone_id);
}

function metric(metric_id, exact_value, unit, product_or_research_layer, source_path, formal_definition, frontend_significance, caveat = "") {
  return { metric_id, formal_definition, exact_value, unit, product_or_research_layer, source_path, source_SHA256: fileHash(source_path), generation_method: "frontend/scripts/generate-product-functional-census.mjs", frontend_significance, caveat };
}

function buildCensus() {
  const apiMap = json("docs/api/product-api-map.v1.json");
  const searchManifest = json("frontend/generated/search-v2/manifest.json");
  const searchDocuments = json("frontend/generated/search-v2/documents.json").documents;
  const searchFacets = json("frontend/generated/search-v2/facets.json");
  const contextManifest = json("frontend/generated/trace-context-v1/manifest.json");
  const spacetimeManifest = json("frontend/generated/trace-spacetime-v1/manifest.json");
  const v2 = json("frontend/generated/trace-exploration-v2/production-read-model.json");
  const v3 = json("frontend/generated/trace-exploration-v3/read-model.json");
  const inquiry = json("frontend/generated/trace-open-inquiry-v1/open-inquiry-registry.v1.json");
  const profile = json("docs/statistics/v49-release-data-profile.json");
  const pageFiles = walk(resolve(frontend, "src/app")).filter((path) => /\/page\.tsx?$/.test(path)).sort();
  const pages = pageFiles.map((absolute) => {
    const exact_route = appRoute(absolute);
    const definition = pageCatalog[exact_route];
    if (!definition) throw new Error(`unclassified page route: ${exact_route}`);
    const [classification, product_area, functional_zone_ids, desktop_mobile_policy, user_goal, CLAUDE_MUST_DESIGN, final_navigation_candidate, reason] = definition;
    const source = relative(root, absolute).replaceAll("\\", "/");
    return {
      route_id: `page.${exact_route === "/" ? "home" : exact_route.slice(1).replaceAll("/", ".").replaceAll("{", "").replaceAll("}", "").replaceAll("*", "catchall")}`,
      exact_route,
      dynamic_parameters: [...exact_route.matchAll(/\{([^}]+)\}/g)].map((match) => match[1]),
      classification, product_area, functional_zone_ids, desktop_policy: desktop_mobile_policy, mobile_policy: desktop_mobile_policy,
      navigation_entry: final_navigation_candidate ? "final navigation candidate" : "not final navigation",
      user_goal, primary_actions: functional_zone_ids.flatMap((id) => zones.find((zone) => zone.zone_id === id)?.primary_user_actions ?? []), secondary_actions: [],
      major_components: [source], API_dependencies: [...new Set(functional_zone_ids.flatMap((id) => zones.find((zone) => zone.zone_id === id)?.required_API_ids ?? []))],
      System_Suggestions_usage: functional_zone_ids.includes("zone.system-suggestions") || functional_zone_ids.some((id) => ["zone.search", "zone.context-canvas", "zone.spacetime", "zone.validated-exploration", "zone.open-inquiry"].includes(id)) ? "OPTIONAL_GUIDANCE_ONLY" : "NONE",
      loading_state: "Declared by the relevant functional zone", empty_state: "Declared by the relevant functional zone", partial_state: "Declared by the relevant functional zone", error_state: "Fail closed without cross-layer substitution",
      export_behavior: functional_zone_ids.includes("zone.trace-exports") ? "See export_capabilities" : "None", rights_or_visual_constraints: "No visual-rights assumption beyond the current route/data contract.",
      implementation_source_paths: [source], test_paths: [], current_readiness: classification === "ACTIVE_PUBLIC_PRODUCT" || classification === "ACTIVE_REFERENCE_IMPLEMENTATION" ? "BACKEND_READY_FRONTEND_NOT_DESIGNED" : classification,
      CLAUDE_MUST_DESIGN, final_navigation_candidate, reason,
    };
  });
  const routeCounts = Object.fromEntries(["ACTIVE_PUBLIC_PRODUCT", "ACTIVE_REFERENCE_IMPLEMENTATION", "DOCUMENTATION_OR_METHOD", "LEGACY_PUBLIC", "RETIRED", "INTERNAL_TEST_OR_DEMO", "PLACEHOLDER", "ERROR_OR_UTILITY"].map((classification) => [classification, pages.filter((page) => page.classification === classification).length]));
  const productAreaIds = ["Global Search", "Shared product", "TRACE"];
  const userFacingFunctionZoneIds = zones.filter((zone) => !["zone.home", "zone.global-navigation", "zone.shared-states"].includes(zone.zone_id)).map((zone) => zone.zone_id);
  const activeProductScreenCount = pages.filter((page) => page.CLAUDE_MUST_DESIGN).length;
  const referenceOrLegacyScreenCount = pages.filter((page) => ["ACTIVE_REFERENCE_IMPLEMENTATION", "LEGACY_PUBLIC"].includes(page.classification)).length;
  const api_routes = apiMap.routes.map((route) => ({
    ...route, route_template: route.route, route_file: route.source_route_path, handler: route.source_route_path,
    frontend_consumption_class: apiClass(route.api_id), functional_zone_ids: apiZones(route.api_id), desktop_mobile_consumer: route.availability,
    pagination: route.route.includes("records") || route.api_id.includes("search") ? "Contract-defined bounded cursor or page behavior" : "None unless the bound TRACE catalog says otherwise",
    sorting: "Contract-defined deterministic order", filtering: "Contract-defined allowlist only", cache_behavior: "See bound product API map", System_Suggestions_involvement: route.ai_involvement === "GUIDANCE_ONLY" ? "GUIDANCE_ONLY" : "NONE",
  }));
  const apiCounts = Object.fromEntries(["FRONTEND_REQUIRED_NOW", "FRONTEND_OPTIONAL", "SERVER_SIDE_SUPPORT", "INTERNAL_RESEARCH_CONTROL", "LEGACY_COMPATIBILITY", "RETIRED", "FAIL_CLOSED"].map((classification) => [classification, api_routes.filter((route) => route.frontend_consumption_class === classification).length]));
  const delivery = Object.fromEntries([...searchDocuments.reduce((map, item) => map.set(item[11], (map.get(item[11]) ?? 0) + 1), new Map())]);
  const data_metrics = [
    metric("archive.canonical_object_count", profile.coreScale.canonicalObjectCount, "objects", "release authority", "docs/statistics/v49-release-data-profile.json", "Canonical objects in the sealed v49 release profile.", "Separates corpus scale from public Search scale."),
    metric("archive.active_public_object_count", profile.coreScale.apiVisibleObjectCount, "objects", "public product", "docs/statistics/v49-release-data-profile.json", "Objects visible to the release API and public product projections.", "Defines public product denominator."),
    metric("archive.held_object_count", profile.coreScale.heldObjectCount, "objects", "held research", "docs/statistics/v49-release-data-profile.json", "Held objects excluded from public product routes.", "Never design a held-record UI state as public data."),
    metric("archive.assignment_count", profile.coreScale.assignmentCount, "assignments", "release authority", "docs/statistics/v49-release-data-profile.json", "Current assignment count in the sealed release profile.", "Research-scale context only."),
    metric("archive.positive_visual_rights_count", profile.rightsAndPublication.positiveRightsCount, "records", "rights authority", "docs/statistics/v49-release-data-profile.json", "Records with positive rights in the sealed release profile.", "No current product image may be assumed from metadata alone.", "Search delivery-state labels are not a positive-rights grant."),
    metric("search.public_document_count", searchManifest.document_count, "documents", "Global Search", "frontend/generated/search-v2/manifest.json", "Documents admitted to the public Search index.", "Primary Search scale."),
    metric("search.held_document_count", searchManifest.held_document_count, "documents", "Global Search", "frontend/generated/search-v2/manifest.json", "Held documents included in Search index.", "Must remain zero."),
    metric("search.trace_document_count", searchManifest.trace_record_count, "documents", "Global Search", "frontend/generated/search-v2/manifest.json", "TRACE records included in Search index.", "Must remain zero."),
    metric("search.open_inquiry_document_count", searchManifest.open_inquiry_record_count, "documents", "Global Search", "frontend/generated/search-v2/manifest.json", "Open Inquiry records included in Search index.", "Must remain zero."),
    metric("search.index_bytes", searchManifest.index_bytes, "bytes", "Global Search", "frontend/generated/search-v2/manifest.json", "Canonical Search documents payload bytes.", "Server-only artifact size."),
    metric("search.index_gzip_bytes", searchManifest.index_gzip_bytes, "bytes", "Global Search", "frontend/generated/search-v2/manifest.json", "Gzip size of Search documents artifact.", "Server-only artifact size."),
    metric("search.object_type_dictionary", searchFacets.object_types.length, "values", "Global Search", "frontend/generated/search-v2/facets.json", "Public object-type facet cardinality.", "Filter-control scale."),
    metric("search.theme_dictionary", searchFacets.themes.length, "values", "Global Search", "frontend/generated/search-v2/facets.json", "Public theme facet cardinality.", "Filter-control scale."),
    metric("search.movement_dictionary", searchFacets.movements.length, "values", "Global Search", "frontend/generated/search-v2/facets.json", "Public movement facet cardinality.", "Movement is sparse and never inferred."),
    metric("search.remote_image_delivery_state_count", delivery.REMOTE_IMAGE ?? 0, "documents", "Global Search", "frontend/generated/search-v2/documents.json", "Search documents labelled REMOTE_IMAGE by delivery state.", "Not a thumbnail or positive-rights authorization; Search DTO carries no image URL."),
    metric("context.public_object_coverage", contextManifest.counts.publicObjectCount, "objects", "TRACE Context", "frontend/generated/trace-context-v1/manifest.json", "Public objects represented by governed Context projection.", "Context Canvas denominator."),
    metric("context.representation_count", contextManifest.counts.assignmentCounts.total, "representations", "TRACE Context", "frontend/generated/trace-context-v1/manifest.json", "Published governed Context representations.", "Context Canvas scale, not association count."),
    metric("context.term_count", contextManifest.counts.termCounts.total, "terms", "TRACE Context", "frontend/generated/trace-context-v1/manifest.json", "Controlled Context vocabulary terms.", "Control vocabulary scale."),
    metric("context.template_count", 3, "templates", "TRACE Context", "frontend/src/features/trace-v49/context/canvas/templates.ts", "Current Context Canvas composition template count.", "Design must support selectable governed composition templates."),
    metric("spacetime.public_denominator", spacetimeManifest.counts.publicObjects, "objects", "TRACE Spacetime", "frontend/generated/trace-spacetime-v1/manifest.json", "Public objects in governed Spacetime projection.", "Spacetime denominator."),
    metric("spacetime.period_count", spacetimeManifest.counts.timeBuckets, "periods", "TRACE Spacetime", "frontend/generated/trace-spacetime-v1/manifest.json", "Governed decade bucket count.", "Period-control scale."),
    metric("spacetime.geography_count", spacetimeManifest.counts.governedGeographyEntries, "geographies", "TRACE Spacetime", "frontend/generated/trace-spacetime-v1/manifest.json", "Governed geography entries.", "Map/table selection scale."),
    metric("spacetime.region_assignment_count", spacetimeManifest.counts.regionAssignments, "assignments", "TRACE Spacetime", "frontend/generated/trace-spacetime-v1/manifest.json", "Typed region assignments before per-period duplication.", "Do not confuse with period membership."),
    metric("spacetime.map_cell_count", spacetimeManifest.counts.periodRegionCells, "cells", "TRACE Spacetime", "frontend/generated/trace-spacetime-v1/manifest.json", "Non-zero period-region aggregate cells.", "Aggregate map scale."),
    metric("exploration.validated_association_count", v2.capabilities.association_count, "associations", "Validated Exploration V2", "frontend/generated/trace-exploration-v2/production-read-model.json", "Evidence-qualified generic pair associations in V2.", "Do not imply causal or directional claims."),
    metric("exploration.v2_reachable_state_count", v2.capabilities.state_count, "states", "Validated Exploration V2", "frontend/generated/trace-exploration-v2/production-read-model.json", "Governed V2 reachable state count.", "State-machine scale; not active V3 product facts."),
    metric("exploration.v2_transition_count", v2.capabilities.transition_count, "transitions", "Validated Exploration V2", "frontend/generated/trace-exploration-v2/production-read-model.json", "Governed V2 transition count.", "Server owns transitions."),
    metric("exploration.v2_export_variant_count", v2.capabilities.export_variant_count, "variants", "Validated Exploration V2", "frontend/generated/trace-exploration-v2/production-read-model.json", "Governed V2 export variant count.", "Only current V2 export contract applies."),
    metric("exploration.v3_active_product_activation_count", v3.capabilities.production_activation_count, "activations", "Validated Exploration V3", "frontend/generated/trace-exploration-v3/read-model.json", "V3 active production activation count.", "Zero; V3 is fail-closed, not a screen requirement."),
    metric("open_inquiry.count", inquiry.counts.scoped_higher_order_hypothesis_count, "records", "Open Inquiry", "frontend/generated/trace-open-inquiry-v1/open-inquiry-registry.v1.json", "Scoped unresolved Open Inquiry record count.", "Inventory count only; not a likelihood or closure metric."),
    metric("guidance.surface_count", 5, "surfaces", "System Suggestions", "frontend/src/features/system-suggestions/types.ts", "Supported System Suggestions surface IDs.", "One secondary component must work across five surfaces."),
    metric("guidance.maximum_request_bytes", 16384, "bytes", "System Suggestions", "frontend/src/features/system-suggestions/schema.server.ts", "Maximum accepted System Suggestions request body.", "Frontend sends only a bounded public summary."),
    metric("guidance.maximum_note_length", 320, "code points", "System Suggestions", "frontend/src/features/system-suggestions/service.server.ts", "Maximum accepted guidance note length.", "Keep visual treatment compact and secondary."),
    metric("guidance.maximum_suggestions", 4, "suggestions", "System Suggestions", "frontend/src/features/system-suggestions/service.server.ts", "Maximum approved suggestion IDs in a response.", "No arbitrary provider actions."),
    metric("frontend.page_route_template_count", pages.length, "routes", "Frontend", "frontend/src/app/page.tsx", "Discovered Next.js page route templates.", "Includes legacy and internal routes; not a product feature count."),
    metric("frontend.active_product_route_count", routeCounts.ACTIVE_PUBLIC_PRODUCT, "routes", "Frontend", "frontend/src/app/page.tsx", "Page routes classified as active public product.", "Final navigation candidate baseline."),
    metric("frontend.active_product_screen_count", activeProductScreenCount, "screens", "Frontend", "frontend/scripts/generate-product-functional-census.mjs", "Finite pages/workspaces marked CLAUDE_MUST_DESIGN.", "Final visual design scope, including two functional TRACE reference workspaces."),
    metric("frontend.user_facing_function_count", userFacingFunctionZoneIds.length, "functions", "Frontend", "frontend/scripts/generate-product-functional-census.mjs", "Zones with a user goal, entry, action, state, and frontend/API dependency; excludes homepage entry, shared navigation, and shared states.", "Product capability scope rather than JavaScript function count."),
    metric("frontend.user_action_count", zones.flatMap((zone) => zone.primary_user_actions).length, "actions", "Frontend", "frontend/scripts/generate-product-functional-census.mjs", "Enumerated primary user actions across all functional zones.", "Interaction inventory; not feature count."),
    metric("frontend.functional_zone_count", zones.length, "zones", "Frontend", "frontend/scripts/generate-product-functional-census.mjs", "Enumerated frontend functional zones.", "Finite design scope."),
    metric("api.route_template_count", apiMap.summary.logical_route_template_count, "routes", "API", "docs/api/product-api-map.v1.json", "Logical API route templates in canonical product map.", "Only classified frontend subset belongs in design."),
    metric("api.method_route_pair_count", apiMap.summary.method_route_pair_count, "method-route pairs", "API", "docs/api/product-api-map.v1.json", "Expanded HTTP method-route pairs in canonical product map.", "Validation metric, not a screen count."),
  ];
  const navigation_edges = [
    ["nav.home.search", "zone.home", "submit Search or choose starter", "zone.search", "/search?…", "URL state begins", "search.facets.v1", "native navigation", "Search remains available", "Design Search entry"],
    ["nav.search.object", "zone.search-results", "open result", "zone.object-detail", "/surfaces/{id}", "Search URL retained in history", "read.surface-detail.v1", "server object lookup", "not found is explicit", "Provide return-to-Search affordance"],
    ["nav.home.trace", "zone.home", "enter TRACE", "zone.trace-entry", "/trace", "none", "trace.f3.validated.v2.capabilities.get", "desktop runtime load", "mobile desktop-required state", "Make product hierarchy clear"],
    ["nav.trace.context", "zone.trace-entry", "open Context Canvas", "zone.context-canvas", "/trace/context-canvas", "record parameter", "trace.f1.context.object-context.v1", "governed projection load", "fail closed", "Desktop research controls"],
    ["nav.trace.spacetime", "zone.trace-entry", "open Spacetime", "zone.spacetime", "/trace/spacetime", "period/geography state", "trace.f2.spacetime.periods.v1", "governed atlas load", "fail closed", "Desktop research controls"],
    ["nav.validated.inquiry", "zone.validated-exploration", "read separate Open Inquiry", "zone.open-inquiry", "same TRACE route/layer", "validated state is not copied", "trace.f3.open-inquiry.v1.list", "independent registry load", "fixed disclosure remains", "Visually separate the layers"],
    ["nav.suggestion.search", "zone.system-suggestions", "explicitly select approved suggestion", "zone.search", "/search?…", "changes URL only after click", "guidance.system-suggestions.v1", "none before click", "fallback/transport hide does not break Search", "Secondary action styling"],
    ["nav.export.validated", "zone.validated-exploration", "request export", "zone.trace-exports", "no navigation", "bind map/state/hash", "trace.f3.validated.v2.exports.manifest", "preparing", "retryable/non-retryable contract", "Expose manifest-bound download state"],
  ].map(([edge_id, source_zone, action, destination_zone, URL_behavior, state_preservation, API_call, loading_state, failure_state, frontend_design_requirement]) => ({ edge_id, source_zone, action, destination_zone, URL_behavior, state_preservation, API_call, loading_state, failure_state, current_implementation_status: "IMPLEMENTED_OR_REFERENCE_AS_CLASSIFIED", frontend_design_requirement }));
  const platform_matrix = zones.map((zone) => ({ zone_id: zone.zone_id, platform: zone.desktop_mobile_policy, rationale: zone.responsive_requirements }));
  const export_capabilities = [
    { capability_id: "export.context.png", zone_id: "zone.context-canvas", format: "PNG", status: "IMPLEMENTED_BROWSER", boundary: "Current governed Canvas composition and public-safe footer only." },
    { capability_id: "export.spacetime.functional", zone_id: "zone.spacetime", format: "canonical functional value", status: "IMPLEMENTED_PREPARATION_NO_DOWNLOAD_ROUTE", boundary: "Aggregate positions only; not object coordinates; no invented binary route." },
    { capability_id: "export.validated.manifest", zone_id: "zone.trace-exports", format: "JSON", status: "IMPLEMENTED", boundary: "Exact V2 map/state/composition identity." },
    { capability_id: "export.validated.png", zone_id: "zone.trace-exports", format: "PNG", status: "IMPLEMENTED", boundary: "Validated V2 diagram/text only; no third-party object image or Open Inquiry data." },
    { capability_id: "export.validated.svg", zone_id: "zone.trace-exports", format: "SVG", status: "IMPLEMENTED", boundary: "Validated V2 diagram/text only; no third-party object image or Open Inquiry data." },
  ];
  const system_suggestions = { supported_surfaces: ["SEARCH_RESULTS", "TRACE_CONTEXT", "TRACE_SPACETIME", "TRACE_VALIDATED_EXPLORATION", "TRACE_OPEN_INQUIRY"], public_label: "System suggests", ordinary_ui_provider_disclosure: "none", about_methodology_provider_disclosure: true, provider_optional: true, core_functions_depend_on_provider: false, states: ["guidance_loading", "model_guidance_available", "static_fallback_guidance", "guidance_hidden_after_transport_failure", "no_allowed_suggestion", "rate_limited"], open_inquiry_fixed_order: ["Open inquiry", "Evidence remains incomplete.", "This is not a validated historical association.", "System suggests…"], api_key_committed_status: "NOT_COMMITTED", api_key_configured_status: "LOCAL_RUNTIME_STATE_NOT_REPOSITORY_AUTHORITY" };
  const source_manifest = {
    bounded_instruction: "Start with the global product handoff. Expand only through listed paths or explicit source paths in the master census.",
    documents: ["docs/frontend/product-handoff/FRONTEND_FUNCTIONAL_ARCHITECTURE_AND_SCALE_CENSUS.md", "docs/frontend/product-handoff/PRODUCT_STRUCTURE.md", "docs/frontend/product-handoff/FRONTEND_STATE_MATRIX.md", "docs/api/PRODUCT_API_MAP.md", "docs/search/SEARCH_PRODUCT_CONTRACT.md", "docs/frontend/trace-v49-handoff/START_HERE.md", "docs/frontend/product-handoff/SOURCE_MANIFEST.json"],
    implementation: ["frontend/src/app", "frontend/src/features/search-v2", "frontend/src/features/system-suggestions", "frontend/src/features/trace-v49", "frontend/generated/search-v2/manifest.json", "frontend/generated/trace-context-v1/manifest.json", "frontend/generated/trace-spacetime-v1/manifest.json", "frontend/generated/trace-exploration-v2/production-read-model.json", "frontend/generated/trace-open-inquiry-v1/open-inquiry-registry.v1.json"],
    tests: ["frontend/scripts/test-search-v2-api.mjs", "frontend/scripts/test-system-suggestions.mjs", "frontend/scripts/test-trace-exploration-v2.mjs", "scripts/generate_product_api_map.mjs", "frontend/scripts/verify-product-functional-census.mjs"],
  };
  return {
    schema_version: "gda-product-functional-census/v1", census_version: "GLOBAL_PRODUCT_CENSUS_20260829", repository_identity: { repository: "dpan538/graphic_design_archive", source_sha: sourceSha, source_tree_sha: "7307745b7844035784ad1ab6906837d874b164fb" },
    release_identity: { database_version: "50", database_freeze_hash: "f0dda59dd515ba243eaf213bce9f42513727f1ab0a44685635921c3759a7d22e", release_id: searchManifest.release_id, release_manifest_sha256: searchManifest.release_manifest_sha256, frontend_build_version: "0.1.0" },
    product_hierarchy: { product: "Graphic Design Archive", product_area_ids: productAreaIds, product_area_count: productAreaIds.length, active_product_screen_count: activeProductScreenCount, active_product_route_template_count: routeCounts.ACTIVE_PUBLIC_PRODUCT, reference_or_legacy_screen_count: referenceOrLegacyScreenCount, user_facing_function_zone_ids: userFacingFunctionZoneIds, user_facing_function_count: userFacingFunctionZoneIds.length, user_action_count: zones.flatMap((zone) => zone.primary_user_actions).length, global_search_is_trace_child: false, trace_top_level_function_count: 3, global_search_mobile_available: true, trace_full_mobile_runtime_enabled: false, system_suggestions_is_product_guidance_not_core_evidence: true, tree: ["Global Search", "TRACE > Context Canvas", "TRACE > Spacetime", "TRACE > Exploration > Validated Exploration", "TRACE > Exploration > Open Inquiry"] },
    page_routes: pages, functional_zones: zones,
    user_actions: zones.flatMap((zone) => zone.primary_user_actions.map((action) => ({ action_id: `${zone.zone_id}.${action.replaceAll(/[^a-z0-9]+/gi, "-").toLowerCase()}`, zone_id: zone.zone_id, label: action }))),
    navigation_edges, api_routes, api_classifications: apiCounts, frontend_required_api_ids: api_routes.filter((route) => route.frontend_consumption_class === "FRONTEND_REQUIRED_NOW").map((route) => route.api_id),
    data_metrics, metric_dictionary: data_metrics.map(({ metric_id, formal_definition, source_path, generation_method }) => ({ metric_id, definition: formal_definition, source: source_path, generation_method })),
    rights_metrics: { positive_visual_rights_count: profile.rightsAndPublication.positiveRightsCount, search_result_cards_with_permitted_thumbnails: 0, object_detail_pages_rendering_permitted_images: 0, search_remote_image_delivery_state_count: delivery.REMOTE_IMAGE ?? 0, citation_only_search_documents: delivery.CITATION_ONLY ?? 0, link_only_search_documents: delivery.LINK_ONLY ?? 0, source_viewer_search_documents: delivery.SOURCE_VIEWER ?? 0, rule: "The final product Search DTO contains no image URL and current Object Detail renders metadata/citation only; REMOTE_IMAGE is not a positive-rights grant." },
    platform_matrix, state_matrix: zones.map((zone) => ({ zone_id: zone.zone_id, states: zone.state_list })), export_capabilities, system_suggestions,
    readiness: zones.map((zone) => ({ zone_id: zone.zone_id, BACKEND_READY: zone.implementation_readiness !== "BLOCKED", API_READY: zone.required_API_ids.length > 0 || zone.zone_id === "zone.about-methodology", REFERENCE_UI_EXISTS: ["zone.context-canvas", "zone.spacetime", "zone.validated-exploration", "zone.open-inquiry"].includes(zone.zone_id), FINAL_UI_DESIGNED: false, MOBILE_READY: zone.desktop_mobile_policy === "DESKTOP_AND_MOBILE", DESKTOP_READY: zone.desktop_mobile_policy !== "NOT_USER_FACING", EXPORT_READY: zone.zone_id === "zone.trace-exports" || zone.zone_id === "zone.context-canvas", SYSTEM_SUGGESTIONS_READY: ["zone.search", "zone.context-canvas", "zone.spacetime", "zone.validated-exploration", "zone.open-inquiry", "zone.system-suggestions"].includes(zone.zone_id), BLOCKER: zone.zone_id === "zone.validated-exploration" ? "V3 active production activation count is zero; do not invent a V3 active product screen." : "None" })),
    legacy_internal_retired: pages.filter((page) => !["ACTIVE_PUBLIC_PRODUCT", "ACTIVE_REFERENCE_IMPLEMENTATION", "DOCUMENTATION_OR_METHOD"].includes(page.classification)).map((page) => ({ route: page.exact_route, classification: page.classification, why: page.reason, visible_navigation: false, CLAUDE_MUST_DESIGN: false, component_reuse: "Only if reused without importing legacy data or visual-rights assumptions." })),
    source_manifest,
    validation_receipt: { discovered_page_route_template_count: pages.length, unclassified_page_route_count: 0, unclassified_functional_zone_count: 0, unclassified_api_route_count: 0, implemented_api_uncatalogued_count: apiMap.summary.implemented_product_api_uncatalogued_count, catalog_route_without_implementation_count: apiMap.summary.catalog_route_without_implementation_count, catalog_duplicate_method_route_count: apiMap.summary.catalog_duplicate_method_route_count, catalog_source_path_missing_count: apiMap.summary.catalog_source_path_missing_count, catalog_test_path_missing_count: apiMap.summary.catalog_test_path_missing_count, dangling_function_api_reference_count: zones.flatMap((zone) => zone.required_API_ids).filter((id) => !api_routes.some((route) => route.api_id === id)).length, route_counts: routeCounts, api_counts: apiCounts, user_action_count: zones.flatMap((zone) => zone.primary_user_actions).length },
  };
}

function renderMaster(census) {
  const routeRows = census.page_routes.map((page) => `| \`${page.exact_route}\` | ${page.classification} | ${page.desktop_policy} | ${page.functional_zone_ids.join(", ") || "—"} | ${page.CLAUDE_MUST_DESIGN ? "yes" : "no"} | ${quote(page.reason)} |`).join("\n");
  const zoneRows = census.functional_zones.map((zone) => `| ${zone.zone_id} | ${zone.canonical_name} | ${zone.desktop_mobile_policy} | ${zone.required_API_ids.join(", ") || "—"} | ${zone.implementation_readiness} |`).join("\n");
  const requiredRows = census.api_routes.filter((route) => route.frontend_consumption_class === "FRONTEND_REQUIRED_NOW").map((route) => `| ${route.api_id} | \`${route.methods.join(", ")} ${route.route_template}\` | ${quote(route.response_summary)} |`).join("\n");
  const appendix = ["FRONTEND_OPTIONAL", "SERVER_SIDE_SUPPORT", "INTERNAL_RESEARCH_CONTROL", "LEGACY_COMPATIBILITY", "RETIRED", "FAIL_CLOSED"].map((classification) => `### ${classification}\n\n| API ID | Route | Reason |\n|---|---|---|\n${census.api_routes.filter((route) => route.frontend_consumption_class === classification).map((route) => `| ${route.api_id} | \`${route.methods.join(", ")} ${route.route_template}\` | ${quote(route.known_limitation)} |`).join("\n")}`).join("\n\n");
  const metricRows = census.data_metrics.map((item) => `| ${item.metric_id} | ${item.exact_value} ${item.unit} | \`${item.source_path}\` | ${quote(item.caveat || item.frontend_significance)} |`).join("\n");
  const readinessRows = census.readiness.map((item) => `| ${item.zone_id} | ${item.BACKEND_READY} | ${item.API_READY} | ${item.REFERENCE_UI_EXISTS} | ${item.FINAL_UI_DESIGNED} | ${item.MOBILE_READY} | ${item.EXPORT_READY} | ${quote(item.BLOCKER)} |`).join("\n");
  const legacyRows = census.legacy_internal_retired.map((item) => `| \`${item.route}\` | ${item.classification} | ${quote(item.why)} | no | no | ${quote(item.component_reuse)} |`).join("\n");
  const flowRows = census.navigation_edges.map((edge) => `| ${edge.source_zone} | ${edge.action} | ${edge.destination_zone} | ${edge.URL_behavior} | ${edge.state_preservation} | ${edge.API_call} |`).join("\n");
  return `# Frontend functional architecture and scale census

> Source: \`${census.repository_identity.source_sha}\`. This is the authoritative functional handoff for later frontend design—not visual design, API-schema invention, research closure, or deployment. The machine-readable equivalent is \`product-functional-census.v1.json\`.

## 1. Executive summary

Graphic Design Archive has two parallel product strategies: Global Search and TRACE. Search is the mobile-capable public-object entry. TRACE has exactly three desktop research functions: Context Canvas, Spacetime, and Exploration; Exploration keeps Validated Exploration and Open Inquiry separate. System Suggestions is optional orientation, never evidence or a core dependency.

| Measure | Exact value |
|---|---:|
| Product areas | ${census.product_hierarchy.product_area_count} |
| Active public product route templates | ${census.product_hierarchy.active_product_route_template_count} |
| Final design screens | ${census.product_hierarchy.active_product_screen_count} |
| Reference or legacy screens | ${census.product_hierarchy.reference_or_legacy_screen_count} |
| User-facing product functions | ${census.product_hierarchy.user_facing_function_count} |
| User actions | ${census.product_hierarchy.user_action_count} |
| Functional zones | ${census.functional_zones.length} |
| Public Search documents | ${census.data_metrics.find((item) => item.metric_id === "search.public_document_count").exact_value} |
| API route templates / method pairs | ${census.validation_receipt.api_counts.FRONTEND_REQUIRED_NOW + census.validation_receipt.api_counts.FRONTEND_OPTIONAL + census.validation_receipt.api_counts.SERVER_SIDE_SUPPORT + census.validation_receipt.api_counts.INTERNAL_RESEARCH_CONTROL + census.validation_receipt.api_counts.LEGACY_COMPATIBILITY + census.validation_receipt.api_counts.RETIRED + census.validation_receipt.api_counts.FAIL_CLOSED} / ${census.data_metrics.find((item) => item.metric_id === "api.method_route_pair_count").exact_value} |

## 2. Source/release identity

| Field | Value |
|---|---|
| Repository | ${census.repository_identity.repository} |
| Source SHA | \`${census.repository_identity.source_sha}\` |
| Source tree SHA | \`${census.repository_identity.source_tree_sha}\` |
| Database version | ${census.release_identity.database_version} |
| Database freeze hash | \`${census.release_identity.database_freeze_hash}\` |
| Release | ${census.release_identity.release_id} |
| Frontend build version | ${census.release_identity.frontend_build_version} |

## 3. Product hierarchy

\`\`\`text
Graphic Design Archive
├── Global Search (homepage, desktop, mobile, object detail)
└── TRACE (desktop research environment)
    ├── Context Canvas
    ├── Spacetime
    └── Exploration
        ├── Validated Exploration
        └── Open Inquiry
\`\`\`

\`TRACE_TOP_LEVEL_FUNCTION_COUNT=3\`
\`GLOBAL_SEARCH_IS_TRACE_CHILD=false\`
\`GLOBAL_SEARCH_MOBILE_AVAILABLE=true\`
\`TRACE_FULL_MOBILE_RUNTIME_ENABLED=false\`
\`SYSTEM_SUGGESTIONS_IS_PRODUCT_GUIDANCE_NOT_CORE_EVIDENCE=true\`

## 4. Active screen and route census

| Route | Classification | Platform | Functional zones | Claude designs | Reason |
|---|---|---|---|---|---|
${routeRows}

The direct Context Canvas and Spacetime paths are functional, no-index reference workspaces. They are final-design candidates but are not evidence that their current navigation or visual treatment is final. The 8,636-record \`public_surface_mock_v0\` is explicitly non-final static legacy data and is not used for public product scale.

## 5. Functional-zone census

| Zone | Purpose | Platform | Required APIs | Readiness |
|---|---|---|---|---|
${zoneRows}

## 6. Global Search specification

Search has one deterministic relevance order over exactly ${census.data_metrics.find((item) => item.metric_id === "search.public_document_count").exact_value} public documents. Text fields are stable ID, title, credited label, and place. Hard conjunctive filters are year, object type, theme, and movement. The client uses a 25-result default page and a 50-result API maximum; URL state preserves query, filters, and cursor. Search result DTOs have no image URL or thumbnail field.

## 7. Object Detail specification

\`/surfaces/{id}\` is the Search target route. Current rendering is public metadata plus a permitted citation when available; it does not render an image. A future design must preserve Search history and must not assume a visual asset from object metadata or delivery-state labels.

## 8. TRACE overview

TRACE is intentionally desktop-first. A likely mobile request returns the lightweight desktop-required state before governed runtime imports and links back to Search. No route, API version, export type, or V3 research-control collection creates a fourth TRACE function.

## 9. Context Canvas specification

Context Canvas covers ${census.data_metrics.find((item) => item.metric_id === "context.public_object_coverage").exact_value} public objects with ${census.data_metrics.find((item) => item.metric_id === "context.representation_count").exact_value} governed representations across 25 controlled terms. It is project-curated context, never a historical relation. Design both spatial canvas and synchronized accessible rows; preserve explicit provenance and the browser PNG export limits.

## 10. Spacetime specification

Spacetime has ${census.data_metrics.find((item) => item.metric_id === "spacetime.period_count").exact_value} decade periods, ${census.data_metrics.find((item) => item.metric_id === "spacetime.geography_count").exact_value} governed geographies, and ${census.data_metrics.find((item) => item.metric_id === "spacetime.map_cell_count").exact_value} non-zero aggregate cells. A map mark is aggregate recorded context, not an object coordinate, movement path, influence relation, or association. The accessible geography table is an equivalent representation.

## 11. Validated Exploration specification

The functional product contract is V2: 31 vocabulary entries, 21 evidence-qualified generic pair associations, 5,760 governed states, 749,944 transitions, and 11,520 export variants. The server owns state hashes, available actions, tree, and export identity. V3 exposes fail-closed read/reconciliation resources with zero production activations; do not design V3 controls as user product screens.

## 12. Open Inquiry specification

Open Inquiry contains exactly 11 scoped unresolved records. Its persistent order is: **Open inquiry**; **Evidence remains incomplete.**; **This is not a validated historical association.**; then optional System Suggestions. It cannot enter validated graph, composition, topology, export, or metrics; no confidence scale, probability, or stochastic ordering is permitted.

## 13. System Suggestions specification

| Rule | Current contract |
|---|---|
| Public label | System suggests |
| Surfaces | ${census.system_suggestions.supported_surfaces.join(", ")} |
| Provider optional / core dependent | true / false |
| Ordinary UI provider disclosure | none |
| About/Methodology disclosure | yes |
| States | ${census.system_suggestions.states.join(", ")} |
| Maximum request / note / suggestions | 16,384 bytes / 320 code points / 4 |

Provider output is only a validated candidate selection plus a bounded note. Search result objects, held records, raw evidence, and provider identity are outside the ordinary UI and request boundary.

## 14. Navigation and user flows

| Source | Action | Destination | URL | State preservation | API |
|---|---|---|---|---|---|
${flowRows}

## 15. Desktop/mobile matrix

| Zone | Policy | Product meaning |
|---|---|---|
${census.platform_matrix.map((item) => `| ${item.zone_id} | ${item.platform} | ${quote(item.rationale)} |`).join("\n")}

\`SEARCH_CLIENT_BUNDLE_TRACE_IMPORT_COUNT=0\`. Desktop-only TRACE is intentional product policy, not a responsive defect.

## 16. Frontend-required API table

Only these ${census.api_classifications.FRONTEND_REQUIRED_NOW} \`FRONTEND_REQUIRED_NOW\` routes belong in a final frontend implementation now.

| API ID | Method and route | Purpose |
|---|---|---|
${requiredRows}

\`guidance.system-suggestions.v1\` is the single \`FRONTEND_OPTIONAL\` API: it may enhance a loaded screen but must never gate it.

## 17. Complete API classification appendix

The canonical complete map remains [PRODUCT_API_MAP.md](../../api/PRODUCT_API_MAP.md). This appendix adds frontend-consumption disposition; it does not replace request/response schemas.

${appendix}

## 18. Quantitative scale census

| Metric | Value | Source | Frontend significance / caveat |
|---|---:|---|---|
${metricRows}

All test figures are **VALIDATION_METRIC_NOT_PRODUCT_FEATURE**. The release profile is authoritative for canonical/held/rights counts; the Search and governed artifacts are authoritative for product projection scale.

## 19. Rights and visual-material boundary

| Screen/state | Allowed material now |
|---|---|
| Homepage / Search controls | NO_VISUAL_ASSUMPTION_ALLOWED |
| Search result cards | TEXT_CITATION_ONLY; permitted thumbnail count is 0 |
| Object Detail | TEXT_CITATION_ONLY; current route renders no image |
| Context Canvas / Spacetime / Validated Exploration export | GENERATED_DIAGRAM_ONLY |
| Open Inquiry | TEXT_CITATION_ONLY |
| Legacy asset studies | REFERENCE_ONLY; never import their image policies into final product |

The sealed release profile reports positive visual rights count **0**. The Search artifact’s ${census.rights_metrics.search_remote_image_delivery_state_count} \`REMOTE_IMAGE\` delivery labels are not positive-rights grants and do not include URLs in the Search DTO. Exports must not include third-party images; TRACE exports are internally rendered diagrams/text only. Decorative placeholder imagery is not authorized.

## 20. Export capabilities

| Capability | Format | Status | Boundary |
|---|---|---|---|
${census.export_capabilities.map((item) => `| ${item.capability_id} | ${item.format} | ${item.status} | ${item.boundary} |`).join("\n")}

## 21. Shared states and accessibility

Every active zone has loading, valid empty/zero, partial only where contractual, safe error, and explicit retry behavior. All controls are keyboard-operable. Context Canvas exposes accessible rows; Spacetime exposes an equivalent table; Validated Exploration exposes the server-provided tree; Open Inquiry makes unresolved status textual and persistent. Never use colour, map geometry, or model guidance as the sole carrier of meaning.

## 22. Legacy/internal/retired surfaces

| Path | Classification | Why retained | Visible navigation | Claude designs | Component reuse |
|---|---|---|---|---|---|
${legacyRows}

## 23. Frontend readiness matrix

| Zone | Backend | API | Reference UI | Final UI designed | Mobile | Export | Blocker |
|---|---|---|---|---|---|---|---|
${readinessRows}

## 24. Frontend design brief for Claude

### A. Exact product hierarchy

Design Global Search and TRACE as parallel homepage-level strategies. TRACE has exactly Context Canvas, Spacetime, and Exploration; Exploration contains separate Validated Exploration and Open Inquiry layers.

### B. Exact finite screen / functional-zone list to design

1. Homepage Search entry (desktop/mobile; Search form, starters, TRACE entry; text/citation-only).
2. Global Search (desktop/mobile; query, four filters, results, cursor, optional guidance; text/citation-only).
3. Object Detail (desktop/mobile; public metadata and permitted citation; no assumed image).
4. About / Methodology (desktop/mobile; methods and provider disclosure).
5. TRACE entry / Exploration (desktop plus mobile lightweight fallback; validated and Open Inquiry separation).
6. Context Canvas (desktop plus mobile lightweight fallback; canvas, rows, provenance, export).
7. Spacetime (desktop plus mobile lightweight fallback; period/geography/map/table states).

### C. Shared components that need visual design

Global navigation; Search form, filters, result card, pagination; Object Detail metadata; TRACE entry; Context controls and accessible rows; Spacetime controls/map/table; Validated Exploration controls/tree; fixed Open Inquiry disclosure; System Suggestions note; export controls; loading/zero/partial/error states.

### D. Mandatory product invariants

Search is homepage-level and mobile-capable. Search returns public object pages only. TRACE has exactly three functions and full runtime is desktop-only. Open Inquiry never implies validation. Guidance is visually secondary and provider identity is hidden. Object imagery is never assumed. Frontend actions may not change ranking, evidence, API schemas, data, rights, or mobile TRACE policy.

### E. Decisions Claude may make

Layout, hierarchy, spacing, typography, colour, motion, card treatment, map language, filter presentation, desktop navigation, mobile Search composition, responsive Object Detail treatment, and secondary guidance treatment.

### F. Decisions Claude may not make

Search ranking/eligibility/filter semantics; TRACE evidence; association validation; Open Inquiry status; API schemas; database content; rights decisions; TRACE mobile activation; or model behavior.

### G. Exact API subset Claude should consume

Use Section 16. The only optional route is System Suggestions. Never build screens for internal V3 controls, fail-closed V3 active routes, retired V1 Exploration, legacy compatibility routes, or server-support identity routes.

### H. Known limitations

Current Object Detail is metadata/citation-only. The current release has zero positive visual-rights records. V3 has zero production activations. Movement coverage is sparse. Context/Spacetime reference workspaces are functional but unlinked/no-index. External human review for Open Inquiry remains pending.

### I. Unresolved frontend design questions

Final navigation grouping for the two unlinked TRACE workspaces; exact visual system; safe visual expression of generated diagrams; presentation of the Object Detail citation state; and how to expose V2’s existing export actions without implying an image-rights grant.

## 25. Metric dictionary and source references

Each machine metric carries its exact definition, source path, SHA-256, and generation method. Primary inputs are the release data profile, Search manifest/documents/facets, Context and Spacetime manifests, V2/V3 read models, Open Inquiry registry, canonical product API map, and current filesystem route scan. Use \`SOURCE_MANIFEST.json\` for bounded implementation verification; do not scan the repository indiscriminately.
`;
}

const census = buildCensus();
const serialized = `${JSON.stringify(census, null, 2)}\n`;
const master = `${renderMaster(census).trimEnd()}\n`;

if (checkOnly) {
  if (!existsSync(outputPath) || readFileSync(outputPath, "utf8") !== serialized) throw new Error("product-functional-census.v1.json is stale");
  if (!existsSync(masterPath) || readFileSync(masterPath, "utf8") !== master) throw new Error("FRONTEND_FUNCTIONAL_ARCHITECTURE_AND_SCALE_CENSUS.md is stale");
  console.log(JSON.stringify({ status: "PASS", page_routes: census.page_routes.length, functional_zones: census.functional_zones.length, api_routes: census.api_routes.length, frontend_required_api_count: census.api_classifications.FRONTEND_REQUIRED_NOW }, null, 2));
} else {
  if (!writeJson && !writeMaster) throw new Error("use --write-json, --write-master, --write-all, or --check");
  if (writeJson) writeFileSync(outputPath, serialized);
  if (writeMaster) writeFileSync(masterPath, master);
  console.log(JSON.stringify({ status: "GENERATED", wrote_json: writeJson, wrote_master: writeMaster, page_routes: census.page_routes.length, functional_zones: census.functional_zones.length, api_routes: census.api_routes.length, frontend_required_api_count: census.api_classifications.FRONTEND_REQUIRED_NOW }, null, 2));
}
