import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const frontend = resolve(here, "..");
const root = resolve(frontend, "..");
const resolveRoot = (path) => resolve(root, path);
const jsonPath = resolveRoot("docs/frontend/product-handoff/product-functional-census.v1.json");
const masterPath = resolveRoot("docs/frontend/product-handoff/FRONTEND_FUNCTIONAL_ARCHITECTURE_AND_SCALE_CENSUS.md");
const read = (path) => readFileSync(resolveRoot(path), "utf8");
const sha256 = (path) => createHash("sha256").update(readFileSync(resolveRoot(path))).digest("hex");

try {
  execFileSync(process.execPath, [resolve(frontend, "scripts/generate-product-functional-census.mjs"), "--check"], { cwd: root, stdio: "pipe" });
} catch {
  console.error("PRODUCT_FUNCTIONAL_CENSUS_GENERATOR_CHECK=FAIL");
  process.exit(1);
}

const census = JSON.parse(readFileSync(jsonPath, "utf8"));
const master = readFileSync(masterPath, "utf8");
const apiMap = JSON.parse(read("docs/api/product-api-map.v1.json"));
const validPageClassifications = new Set([
  "ACTIVE_PUBLIC_PRODUCT", "ACTIVE_REFERENCE_IMPLEMENTATION", "DOCUMENTATION_OR_METHOD", "LEGACY_PUBLIC",
  "RETIRED", "INTERNAL_TEST_OR_DEMO", "PLACEHOLDER", "ERROR_OR_UTILITY",
]);
const validApiClassifications = new Set([
  "FRONTEND_REQUIRED_NOW", "FRONTEND_OPTIONAL", "SERVER_SIDE_SUPPORT", "INTERNAL_RESEARCH_CONTROL",
  "LEGACY_COMPATIBILITY", "RETIRED", "FAIL_CLOSED",
]);
const validPolicies = new Set(["DESKTOP_AND_MOBILE", "DESKTOP_ONLY", "MOBILE_LIGHTWEIGHT_FALLBACK", "NOT_USER_FACING"]);
const apiIds = new Set(census.api_routes.map((route) => route.api_id));
const zoneIds = new Set(census.functional_zones.map((zone) => zone.zone_id));
const metricById = new Map(census.data_metrics.map((metric) => [metric.metric_id, metric]));
const count = (items, predicate) => items.filter(predicate).length;
const pathCount = (paths) => count(paths, (path) => !existsSync(resolveRoot(path)));
const expectedMetric = (metricId, value) => metricById.get(metricId)?.exact_value !== value;

const report = {
  UNCLASSIFIED_PAGE_ROUTE_COUNT: count(census.page_routes, (page) => !validPageClassifications.has(page.classification)),
  UNCLASSIFIED_FUNCTIONAL_ZONE_COUNT: count(census.functional_zones, (zone) => !zone.zone_id || !zone.canonical_name || !zone.product_area || !zone.entry_route || !validPolicies.has(zone.desktop_mobile_policy)),
  UNCLASSIFIED_API_ROUTE_COUNT: count(census.api_routes, (route) => !validApiClassifications.has(route.frontend_consumption_class)),
  IMPLEMENTED_API_UNCATALOGUED_COUNT: census.validation_receipt.implemented_api_uncatalogued_count,
  CATALOG_ROUTE_WITHOUT_IMPLEMENTATION_COUNT: census.validation_receipt.catalog_route_without_implementation_count,
  CATALOG_DUPLICATE_METHOD_ROUTE_COUNT: census.validation_receipt.catalog_duplicate_method_route_count,
  DANGLING_FUNCTION_API_REFERENCE_COUNT: count(census.functional_zones.flatMap((zone) => zone.required_API_ids), (apiId) => !apiIds.has(apiId)),
  DANGLING_SOURCE_PATH_COUNT: 0,
  DANGLING_NAVIGATION_EDGE_COUNT: count(census.navigation_edges, (edge) => !zoneIds.has(edge.source_zone) || !zoneIds.has(edge.destination_zone) || !apiIds.has(edge.API_call)),
  HEADLINE_METRIC_WITHOUT_DEFINITION_COUNT: count(census.data_metrics, (metric) => !metric.metric_id || !metric.formal_definition || !metric.generation_method),
  HEADLINE_METRIC_WITHOUT_SOURCE_COUNT: count(census.data_metrics, (metric) => !metric.source_path || !metric.source_SHA256),
  HEADLINE_METRIC_RECONCILIATION_FAILURE_COUNT: 0,
  RIGHTS_ASSUMPTION_WITHOUT_SOURCE_COUNT: 0,
  MOBILE_POLICY_CONTRADICTION_COUNT: 0,
  SYSTEM_SUGGESTIONS_BOUNDARY_CONTRADICTION_COUNT: 0,
  MASTER_DOCUMENT_JSON_MISMATCH_COUNT: 0,
  FRONTEND_REQUIRED_API_WITHOUT_FUNCTION_ZONE_COUNT: count(census.api_routes, (route) => route.frontend_consumption_class === "FRONTEND_REQUIRED_NOW" && route.functional_zone_ids.length === 0),
  ACTIVE_PRODUCT_ROUTE_WITHOUT_DESIGN_DISPOSITION_COUNT: count(census.page_routes, (page) => page.classification === "ACTIVE_PUBLIC_PRODUCT" && (typeof page.CLAUDE_MUST_DESIGN !== "boolean" || typeof page.final_navigation_candidate !== "boolean")),
};

const sourcePaths = [
  ...census.page_routes.flatMap((page) => [...page.implementation_source_paths, ...page.test_paths]),
  ...census.functional_zones.flatMap((zone) => [...zone.source_paths, ...zone.test_paths]),
  ...census.api_routes.flatMap((route) => [route.route_file, route.handler, route.service_repository_path, route.test_path]),
  ...census.source_manifest.documents,
  ...census.source_manifest.implementation,
  ...census.source_manifest.tests,
];
report.DANGLING_SOURCE_PATH_COUNT = pathCount(sourcePaths);

for (const metric of census.data_metrics) {
  if (!existsSync(resolveRoot(metric.source_path)) || sha256(metric.source_path) !== metric.source_SHA256) report.HEADLINE_METRIC_RECONCILIATION_FAILURE_COUNT += 1;
}
for (const [metricId, expected] of [
  ["archive.canonical_object_count", 15923], ["archive.active_public_object_count", 7995], ["archive.held_object_count", 7928],
  ["search.public_document_count", 7995], ["search.held_document_count", 0], ["search.trace_document_count", 0], ["search.open_inquiry_document_count", 0],
  ["context.public_object_coverage", 7995], ["spacetime.public_denominator", 7995], ["exploration.validated_association_count", 21],
  ["open_inquiry.count", 11], ["guidance.surface_count", 5], ["api.route_template_count", 91], ["api.method_route_pair_count", 275],
]) if (expectedMetric(metricId, expected)) report.HEADLINE_METRIC_RECONCILIATION_FAILURE_COUNT += 1;
if (census.rights_metrics.positive_visual_rights_count !== 0 || census.rights_metrics.search_result_cards_with_permitted_thumbnails !== 0 || census.rights_metrics.object_detail_pages_rendering_permitted_images !== 0 || !metricById.has("archive.positive_visual_rights_count")) report.RIGHTS_ASSUMPTION_WITHOUT_SOURCE_COUNT += 1;

const searchWorkspace = read("frontend/src/features/search-v2/ui/SearchWorkspace.tsx");
if (census.product_hierarchy.global_search_mobile_available !== true || census.product_hierarchy.trace_full_mobile_runtime_enabled !== false || searchWorkspace.includes("trace-v49") || count(census.page_routes, (page) => !validPolicies.has(page.mobile_policy)) > 0) report.MOBILE_POLICY_CONTRADICTION_COUNT += 1;
const expectedSurfaces = ["SEARCH_RESULTS", "TRACE_CONTEXT", "TRACE_SPACETIME", "TRACE_VALIDATED_EXPLORATION", "TRACE_OPEN_INQUIRY"];
if (census.system_suggestions.public_label !== "System suggests" || census.system_suggestions.provider_optional !== true || census.system_suggestions.core_functions_depend_on_provider !== false || JSON.stringify(census.system_suggestions.supported_surfaces) !== JSON.stringify(expectedSurfaces)) report.SYSTEM_SUGGESTIONS_BOUNDARY_CONTRADICTION_COUNT += 1;

const masterNeedles = [
  census.repository_identity.source_sha,
  "## 1. Executive summary", "## 25. Metric dictionary and source references",
  "TRACE_TOP_LEVEL_FUNCTION_COUNT=3", "GLOBAL_SEARCH_IS_TRACE_CHILD=false", "TRACE_FULL_MOBILE_RUNTIME_ENABLED=false",
  "FRONTEND_REQUIRED_NOW", "NO_VISUAL_ASSUMPTION_ALLOWED", "System suggests",
  String(census.data_metrics.find((metric) => metric.metric_id === "search.public_document_count").exact_value),
];
if (masterNeedles.some((needle) => !master.includes(needle)) || apiMap.summary.logical_route_template_count !== census.api_routes.length || apiMap.routes.some((route) => census.api_routes.find((item) => item.api_id === route.api_id)?.frontend_consumption_class !== route.frontend_consumption_class)) report.MASTER_DOCUMENT_JSON_MISMATCH_COUNT += 1;

const failed = Object.entries(report).filter(([, value]) => value !== 0);
console.log(JSON.stringify({
  status: failed.length === 0 ? "PASS" : "FAIL",
  BUILD_GENERATED_PAGE_COUNT: census.page_routes.length,
  ACTIVE_PRODUCT_PAGE_ROUTE_COUNT: count(census.page_routes, (page) => page.classification === "ACTIVE_PUBLIC_PRODUCT"),
  REFERENCE_OR_LEGACY_PAGE_ROUTE_COUNT: count(census.page_routes, (page) => ["ACTIVE_REFERENCE_IMPLEMENTATION", "LEGACY_PUBLIC"].includes(page.classification)),
  INTERNAL_OR_UTILITY_PAGE_ROUTE_COUNT: count(census.page_routes, (page) => ["INTERNAL_TEST_OR_DEMO", "ERROR_OR_UTILITY"].includes(page.classification)),
  API_ROUTE_TEMPLATE_COUNT: census.api_routes.length,
  API_METHOD_ROUTE_PAIR_COUNT: apiMap.summary.method_route_pair_count,
  ...report,
}, null, 2));
if (failed.length > 0) process.exit(1);
