import { createHash } from "node:crypto";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const traceCatalogPath = resolve(root, "docs/api/trace/trace-api-catalog.v1.json");
const jsonPath = resolve(root, "docs/api/product-api-map.v1.json");
const markdownPath = resolve(root, "docs/api/PRODUCT_API_MAP.md");
const checkOnly = process.argv.includes("--check");
const traceCatalog = JSON.parse(readFileSync(traceCatalogPath, "utf8"));

const readRoute = "frontend/src/app/api/v1/[...path]/route.ts";
const readService = "frontend/src/lib/read-platform/server/read-api-controller.ts";
const readTest = "frontend/scripts/run-v49-api-read-contract-closure.mjs";
const readMethods = ["GET", "HEAD", "OPTIONS"];

const additions = [
  {
    api_id: "search.public-objects.v1", methods: readMethods, route: "/api/search/v1", product_area: "Global Search", availability: "DESKTOP_AND_MOBILE",
    request_summary: "Query text and/or yearFrom, yearTo, objectType, theme, movement; optional first 1..50 and release/state-bound after cursor; allowlisted query parameters only.",
    response_summary: "Public result DTOs, exact count, bounded page info, aggregate summaries, release/checksum identity, plain-language explanation, and audit-only scoring metadata.",
    source_route_path: "frontend/src/app/api/search/v1/route.ts", service_repository_path: "frontend/src/features/search-v2/service.server.ts", test_path: "frontend/scripts/test-search-v2-api.mjs",
    public_held_boundary: "PUBLIC_OBJECTS_ONLY; 7,995 source-verified documents; held, TRACE, Open Inquiry, raw source, and private notes excluded.", ai_involvement: "NONE", implementation_status: "IMPLEMENTED", known_limitation: "Relevance is the only product order; movement coverage is sparse and never inferred.",
  },
  {
    api_id: "search.facets.v1", methods: readMethods, route: "/api/search/v1/facets", product_area: "Global Search", availability: "DESKTOP_AND_MOBILE",
    request_summary: "No query parameters or body.", response_summary: "Release-bound year limits, 90 object types, 8 themes, 7 movements, counts, document total, and four deterministic starter queries.",
    source_route_path: "frontend/src/app/api/search/v1/facets/route.ts", service_repository_path: "frontend/src/features/search-v2/service.server.ts", test_path: "frontend/scripts/test-search-v2-api.mjs",
    public_held_boundary: "PUBLIC_DICTIONARIES_ONLY; values derive from the 7,995 public Search documents; held values excluded.", ai_involvement: "NONE", implementation_status: "IMPLEMENTED", known_limitation: "Source-distinct object-type labels remain distinct; no inferred alias collapse.",
  },
  {
    api_id: "guidance.system-suggestions.v1", methods: ["POST", "OPTIONS"], route: "/api/system-suggestions/v1", product_area: "Search and TRACE guidance", availability: "DESKTOP_AND_MOBILE",
    request_summary: "At most 16,384 bytes: surface, state hash, strict bounded public Search or TRACE context; server generates the allowed candidate list.",
    response_summary: "One or two bounded orientation sentences, zero to four approved structured suggestions, source class, prompt version, and safe provider status.",
    source_route_path: "frontend/src/app/api/system-suggestions/v1/route.ts", service_repository_path: "frontend/src/features/system-suggestions/service.server.ts", test_path: "frontend/scripts/test-system-suggestions.mjs",
    public_held_boundary: "BOUNDED_PUBLIC_SUMMARY_ONLY; no held record, private source text, internal note, user identity, secret, raw provider response, or reasoning.", ai_involvement: "GUIDANCE_ONLY", implementation_status: "IMPLEMENTED_OPTIONAL_FAIL_SAFE", known_limitation: "In-memory rate protection is process-local; guidance is non-persistent and optional.",
  },
  {
    api_id: "read.visual-registry-current.v1", methods: readMethods, route: "/api/v1/visual-registries/current", product_area: "Shared release infrastructure", availability: "DESKTOP_AND_MOBILE",
    request_summary: "No body; current visual-registry lookup.", response_summary: "Fail-closed 404 problem because no visual registry is selected for the fixture release.", source_route_path: readRoute, service_repository_path: readService, test_path: readTest,
    public_held_boundary: "NO_RECORD_PAYLOAD; fail-closed capability response.", ai_involvement: "NONE", implementation_status: "IMPLEMENTED_FAIL_CLOSED", known_limitation: "No visual registry is selected.",
  },
  ...[
    ["read.release.v1", "/api/v1/releases/{release}", "Release identity/schema envelope.", "Release alias or exact release ID; exact requests bind the manifest header.", "No public release listing endpoint."],
    ["read.release-manifest.v1", "/api/v1/releases/{release}/manifest", "Release identity/schema envelope.", "Release alias or exact release ID; exact requests bind the manifest header.", "Manifest response is the compact repository version envelope."],
    ["read.archive-overview.v1", "/api/v1/releases/{release}/archive/overview", "Public archive overview counts.", "Release identity only.", "Selected release only."],
    ["read.folder-types.v1", "/api/v1/releases/{release}/folder-types", "Public folder-type summaries.", "Release identity only.", "No caller-selected order."],
    ["read.folders.v1", "/api/v1/releases/{release}/folders", "Cursor page of public folders.", "Optional type, first, and release-bound after cursor.", "Repository-standard cursor pagination."],
    ["read.folder-detail.v1", "/api/v1/releases/{release}/folders/{folderId}", "One public folder detail.", "Stable public folder ID.", "Unknown folder returns 404."],
    ["read.folder-members.v1", "/api/v1/releases/{release}/folders/{folderId}/surfaces", "Cursor page of public object summaries in one folder.", "Stable folder ID plus optional first and after cursor.", "Public membership projection only."],
    ["read.surface-detail.v1", "/api/v1/releases/{release}/surfaces/{surfaceId}", "One public object detail used by Search result routes.", "Public stable surface ID.", "No image is implied by metadata availability."],
    ["read.legacy-search.v1", "/api/v1/releases/{release}/search", "Legacy release-scoped public Search result connection.", "q, scope, first, and after; deterministic relevance.", "Frozen v1 title/ID contract; Global Search v2 is /api/search/v1."],
    ["read.relation-detail.v1", "/api/v1/releases/{release}/relations/{relationId}", "One published relation or fail-closed 404.", "Stable published relation ID.", "No relation is inferred at request time."],
    ["read.claim-detail.v1", "/api/v1/releases/{release}/claims/{claimId}", "One published claim or fail-closed 404.", "Stable published claim ID.", "No claim is generated at request time."],
    ["read.corpus-detail.v1", "/api/v1/releases/{release}/corpora/{corpusVersion}", "One published corpus descriptor or fail-closed 404.", "Stable published corpus version.", "No unrestricted corpus payload."],
  ].map(([api_id, route, response_summary, request_summary, known_limitation]) => ({
    api_id, methods: readMethods, route, product_area: route.includes("surfaces") || route.endsWith("/search") || route.includes("folders") ? "Archive reading and object detail" : "Shared release infrastructure", availability: "DESKTOP_AND_MOBILE",
    request_summary, response_summary, source_route_path: readRoute, service_repository_path: readService, test_path: readTest,
    public_held_boundary: "PUBLISHED_RELEASE_PROJECTION_ONLY; held and review-only records fail closed.", ai_involvement: "NONE", implementation_status: "IMPLEMENTED_READ_ONLY", known_limitation,
  })),
];

const traceRoutes = traceCatalog.routes.map((route) => ({
  api_id: route.api_id,
  methods: route.method,
  route: route.route,
  product_area: route.group,
  availability: "DESKTOP_ONLY",
  request_summary: route.request_schema?.description ?? "Governed request documented by the bound TRACE catalog.",
  response_summary: route.response_schema?.description ?? "Governed response documented by the bound TRACE catalog.",
  source_route_path: route.source_route_path,
  service_repository_path: route.service_repository_path,
  test_path: route.test_path,
  public_held_boundary: route.route.includes("/controls/")
    ? "SYNTHETIC_RESEARCH_CONTROL_ONLY; never active product fact; held records excluded."
    : route.route.includes("open-inquiry")
      ? "OPEN_INQUIRY_ONLY; unresolved and isolated from validated products; held records excluded."
      : "GOVERNED_PUBLIC_TRACE_ONLY; held records excluded; evidence and product-state gates remain authoritative.",
  ai_involvement: "NONE",
  implementation_status: route.implementation_status,
  known_limitation: Array.isArray(route.limitations) ? route.limitations.join(" ") : String(route.limitations ?? "None recorded."),
}));

const frontendRequiredIds = new Set([
  "search.public-objects.v1", "search.facets.v1", "read.surface-detail.v1",
  "trace.f1.context.object-context.v1", "trace.f2.spacetime.periods.v1", "trace.f2.spacetime.atlas.v1", "trace.f2.spacetime.geography-records.v1",
  "trace.f3.validated.v2.associations.get", "trace.f3.validated.v2.capabilities.get", "trace.f3.validated.v2.categories.list",
  "trace.f3.validated.v2.exports.svg", "trace.f3.validated.v2.exports.manifest", "trace.f3.validated.v2.exports.png",
  "trace.f3.validated.v2.maps.create", "trace.f3.validated.v2.maps.get", "trace.f3.validated.v2.maps.actions", "trace.f3.validated.v2.vocabulary.get",
  "trace.f3.open-inquiry.v1.list", "trace.f3.open-inquiry.v1.detail",
]);

function frontendConsumptionClass(apiId) {
  if (frontendRequiredIds.has(apiId)) return "FRONTEND_REQUIRED_NOW";
  if (apiId === "guidance.system-suggestions.v1") return "FRONTEND_OPTIONAL";
  if (apiId.includes(".retired-")) return "RETIRED";
  if (apiId.includes(".v3.control.")) return "INTERNAL_RESEARCH_CONTROL";
  if (apiId.startsWith("trace.f3.validated.v3.") || apiId === "read.visual-registry-current.v1") return "FAIL_CLOSED";
  if (["read.release.v1", "read.release-manifest.v1", "read.archive-overview.v1", "trace.f3.validated.v2.root"].includes(apiId)) return "SERVER_SIDE_SUPPORT";
  return "LEGACY_COMPATIBILITY";
}

const routes = [...additions, ...traceRoutes]
  .map((route) => ({ ...route, frontend_consumption_class: frontendConsumptionClass(route.api_id) }))
  .sort((left, right) => left.route.localeCompare(right.route) || left.api_id.localeCompare(right.api_id));
const seen = new Set();
let duplicatePairs = 0;
for (const route of routes) for (const method of route.methods) {
  const key = `${method} ${route.route}`;
  if (seen.has(key)) duplicatePairs += 1;
  seen.add(key);
}
const routeFiles = [...new Set(routes.map((route) => route.source_route_path))];
const implementedApiFiles = [];
const walk = async (directory) => {
  const { readdir } = await import("node:fs/promises");
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = resolve(directory, entry.name);
    if (entry.isDirectory()) await walk(path);
    else if (entry.name === "route.ts") implementedApiFiles.push(path.slice(root.length + 1));
  }
};
await walk(resolve(root, "frontend/src/app/api"));
const summary = {
  logical_route_template_count: routes.length,
  method_route_pair_count: routes.reduce((count, route) => count + route.methods.length, 0),
  implemented_api_route_file_count: implementedApiFiles.length,
  implemented_product_api_uncatalogued_count: implementedApiFiles.filter((path) => !routeFiles.includes(path)).length,
  catalog_route_without_implementation_count: routes.filter((route) => !existsSync(resolve(root, route.source_route_path))).length,
  catalog_duplicate_method_route_count: duplicatePairs,
  catalog_source_path_missing_count: routes.filter((route) => !existsSync(resolve(root, route.service_repository_path))).length,
  catalog_test_path_missing_count: routes.filter((route) => !existsSync(resolve(root, route.test_path))).length,
  ai_none_route_count: routes.filter((route) => route.ai_involvement === "NONE").length,
  guidance_only_route_count: routes.filter((route) => route.ai_involvement === "GUIDANCE_ONLY").length,
  frontend_required_now_count: routes.filter((route) => route.frontend_consumption_class === "FRONTEND_REQUIRED_NOW").length,
  frontend_optional_count: routes.filter((route) => route.frontend_consumption_class === "FRONTEND_OPTIONAL").length,
  server_side_support_count: routes.filter((route) => route.frontend_consumption_class === "SERVER_SIDE_SUPPORT").length,
  internal_research_control_count: routes.filter((route) => route.frontend_consumption_class === "INTERNAL_RESEARCH_CONTROL").length,
  legacy_compatibility_count: routes.filter((route) => route.frontend_consumption_class === "LEGACY_COMPATIBILITY").length,
  retired_count: routes.filter((route) => route.frontend_consumption_class === "RETIRED").length,
  fail_closed_count: routes.filter((route) => route.frontend_consumption_class === "FAIL_CLOSED").length,
};
const payload = {
  schema_version: "gda-product-api-map/v1",
  catalog_version: "GLOBAL_SEARCH_SYSTEM_SUGGESTIONS_TRACE_20260829",
  generated_at: "2026-08-29T00:00:00Z",
  source_trace_catalog_sha256: createHash("sha256").update(readFileSync(traceCatalogPath)).digest("hex"),
  summary,
  routes,
};
const json = `${JSON.stringify(payload, null, 2)}\n`;
const escape = (value) => String(value).replaceAll("|", "\\|").replaceAll("\n", " ");
const table = routes.map((route) => `| ${route.methods.join(", ")} | \`${escape(route.route)}\` | ${route.frontend_consumption_class} | ${escape(route.product_area)} | ${route.availability} | ${escape(route.request_summary)} | ${escape(route.response_summary)} | \`${route.source_route_path}\` | \`${route.service_repository_path}\` | \`${route.test_path}\` | ${escape(route.public_held_boundary)} | ${route.ai_involvement} | ${route.implementation_status} | ${escape(route.known_limitation)} |`).join("\n");
const markdown = `# Product API map\n\nThis is the complete logical product API route table for Global Search, archive object/detail reading, shared System Suggestions, and all catalogued TRACE surfaces. The pre-existing exhaustive TRACE catalog remains the source for TRACE request/response detail; this map binds it into one cross-product inventory. The frontend-consumption class is a bounded handoff disposition, not a replacement for the API contract.\n\n## Integrity counters\n\n\`IMPLEMENTED_PRODUCT_API_UNCATALOGUED_COUNT=${summary.implemented_product_api_uncatalogued_count}\`\n\n\`CATALOG_ROUTE_WITHOUT_IMPLEMENTATION_COUNT=${summary.catalog_route_without_implementation_count}\`\n\n\`CATALOG_DUPLICATE_METHOD_ROUTE_COUNT=${summary.catalog_duplicate_method_route_count}\`\n\n\`CATALOG_SOURCE_PATH_MISSING_COUNT=${summary.catalog_source_path_missing_count}\`\n\n\`CATALOG_TEST_PATH_MISSING_COUNT=${summary.catalog_test_path_missing_count}\`\n\n\`PRODUCT_API_LOGICAL_ROUTE_TEMPLATE_COUNT=${summary.logical_route_template_count}\`\n\n\`PRODUCT_API_METHOD_ROUTE_PAIR_COUNT=${summary.method_route_pair_count}\`\n\n## Frontend-consumption counts\n\n\`FRONTEND_REQUIRED_NOW_COUNT=${summary.frontend_required_now_count}\`\n\n\`FRONTEND_OPTIONAL_COUNT=${summary.frontend_optional_count}\`\n\n\`SERVER_SIDE_SUPPORT_COUNT=${summary.server_side_support_count}\`\n\n\`INTERNAL_RESEARCH_CONTROL_COUNT=${summary.internal_research_control_count}\`\n\n\`LEGACY_COMPATIBILITY_COUNT=${summary.legacy_compatibility_count}\`\n\n\`RETIRED_COUNT=${summary.retired_count}\`\n\n\`FAIL_CLOSED_COUNT=${summary.fail_closed_count}\`\n\n## Complete route table\n\n| Method | Exact route | Frontend consumption | Product area | Desktop/mobile | Request summary | Response summary | Source route | Service/repository | Test | Public/held boundary | AI involvement | Status | Known limitation |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n${table}\n\n## Interpretation\n\n\`NONE\` means no model participates. \`GUIDANCE_ONLY\` appears only on \`POST /api/system-suggestions/v1\`; it cannot retrieve Search candidates, rank or include results, change public eligibility or metadata, or mutate TRACE/evidence state. Unsupported methods are fail-closed and are not product methods in this table.\n`;

if (checkOnly) {
  if (!existsSync(jsonPath) || readFileSync(jsonPath, "utf8") !== json) throw new Error("product-api-map.v1.json is stale");
  if (!existsSync(markdownPath) || readFileSync(markdownPath, "utf8") !== markdown) throw new Error("PRODUCT_API_MAP.md is stale");
  if (Object.values(summary).slice(3, 8).some((value) => value !== 0)) throw new Error(`product API integrity counters failed: ${JSON.stringify(summary)}`);
  console.log(JSON.stringify({ status: "PASS", ...summary }, null, 2));
} else {
  writeFileSync(jsonPath, json);
  writeFileSync(markdownPath, markdown);
  console.log(JSON.stringify({ status: "GENERATED", ...summary }, null, 2));
}
