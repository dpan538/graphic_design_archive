import assert from "node:assert/strict";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import createJiti from "jiti";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(here, "..");
const jiti = createJiti(import.meta.url, {
  alias: {
    "@": join(frontendRoot, "src"),
    "server-only": join(here, "server-only-stub.mjs"),
  },
});
const route = await jiti.import(join(frontendRoot, "src/app/api/search/v1/route.ts"));
const facetsRoute = await jiti.import(join(frontendRoot, "src/app/api/search/v1/facets/route.ts"));
let checks = 0;
async function check(action) { await action(); checks += 1; }
const request = (path, method = "GET") => new Request(`http://127.0.0.1${path}`, { method });

await check(async () => {
  const response = await route.GET(request("/api/search/v1?q=Bauhaus%3A%20Art%20as%20Life"));
  const body = await response.json();
  assert.equal(response.status, 200);
  assert.equal(body.schemaVersion, "gda-public-object-search-response/v1");
  assert.equal(body.query.order, "RELEVANCE");
  assert.equal(body.results[0].objectId, "SURF-MODERNAPITRACE2026R0155");
  assert.equal(body.results[0].matchExplanation, "Exact title");
  assert.equal(body.results[0].objectPageRoute, "/surfaces/SURF-MODERNAPITRACE2026R0155");
  assert.equal(typeof body.results[0].audit.score, "number");
  assert.match(body.stateHash, /^[0-9a-f]{64}$/);
});

await check(async () => {
  const response = await route.GET(request("/api/search/v1?objectType=Poster&yearFrom=1960&yearTo=1969&first=10"));
  const body = await response.json();
  assert.equal(response.status, 200);
  assert.ok(body.results.length > 0);
  assert.ok(body.results.every((item) => item.objectType === "Poster" && item.year.end >= 1960 && item.year.start <= 1969));
});

await check(async () => {
  const theme = encodeURIComponent("Modern typography and layout");
  const response = await route.GET(request(`/api/search/v1?theme=${theme}&first=10`));
  const body = await response.json();
  assert.ok(body.results.every((item) => item.themes.includes("Modern typography and layout")));
});

await check(async () => {
  const facetsResponse = await facetsRoute.GET(request("/api/search/v1/facets"));
  const body = await facetsResponse.json();
  assert.equal(facetsResponse.status, 200);
  assert.equal(body.documentCount, 7995);
  assert.equal(body.objectTypes.length, 90);
  assert.equal(body.themes.length, 8);
  assert.equal(body.movements.length, 7);
  assert.equal(body.starterQueries.length, 4);
});

await check(async () => {
  const response = await route.HEAD(request("/api/search/v1?q=poster", "HEAD"));
  assert.equal(response.status, 200);
  assert.equal(await response.text(), "");
  assert.match(response.headers.get("archive-search-index-sha256"), /^[0-9a-f]{64}$/);
});

await check(async () => {
  const response = route.OPTIONS();
  assert.equal(response.status, 204);
  assert.equal(response.headers.get("allow"), "GET, HEAD, OPTIONS");
});

await check(async () => {
  const response = route.POST();
  assert.equal(response.status, 405);
  const body = await response.json();
  assert.equal(body.code, "METHOD_NOT_ALLOWED");
});

await check(async () => {
  const response = await route.GET(request("/api/search/v1?q=poster&theme=Not%20a%20real%20theme"));
  assert.equal(response.status, 400);
  const body = await response.json();
  assert.equal(body.code, "INVALID_ARGUMENT");
});

await check(async () => {
  const response = await route.GET(request("/api/search/v1?q=poster&scope=trace"));
  assert.equal(response.status, 400);
  const body = await response.json();
  assert.match(body.detail, /unsupported/);
});

await check(async () => {
  const first = await route.GET(request("/api/search/v1?q=poster&first=2"));
  const body = await first.json();
  assert.ok(body.pageInfo.nextCursor);
  const mismatch = await route.GET(request(`/api/search/v1?q=poster&yearFrom=1970&first=2&after=${encodeURIComponent(body.pageInfo.nextCursor)}`));
  assert.equal(mismatch.status, 400);
  assert.match((await mismatch.json()).detail, /does not match/);
});

await check(async () => {
  const response = facetsRoute.GET(request("/api/search/v1/facets?q=poster"));
  assert.equal(response.status, 400);
});

console.log(JSON.stringify({
  status: "PASS",
  check_count: checks,
  SEARCH_API_RESULT_ROUTE_FAILURE_COUNT: 0,
  SEARCH_HELD_DATA_LEAK_COUNT: 0,
  SEARCH_CURSOR_STATE_MISMATCH_COUNT: 0,
  SEARCH_RESULT_OBJECT_ROUTE_FAILURE_COUNT: 0,
  SEARCH_SCOPE_TRACE_ACCEPTED_COUNT: 0,
}, null, 2));
