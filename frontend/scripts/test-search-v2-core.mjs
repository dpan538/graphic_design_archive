import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import createJiti from "jiti";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(here, "..");
const jiti = createJiti(import.meta.url, {
  alias: { "@": join(frontendRoot, "src") },
});
const core = await jiti.import(join(frontendRoot, "src/features/search-v2/core.ts"));
const payload = JSON.parse(await readFile(join(frontendRoot, "generated/search-v2/documents.json"), "utf8"));
const manifest = JSON.parse(await readFile(join(frontendRoot, "generated/search-v2/manifest.json"), "utf8"));
const facets = JSON.parse(await readFile(join(frontendRoot, "generated/search-v2/facets.json"), "utf8"));
const documents = payload.documents.map(core.hydratePublicSearchDocument);
const byId = new Map(documents.map((document) => [document.stableId, document]));
let checks = 0;
const check = (action) => { action(); checks += 1; };
const run = (query, filters = {}) => core.rankPublicSearchDocuments(documents, core.normalizePublicSearchRequest({ query, filters }));

check(() => {
  assert.equal(manifest.document_count, 7995);
  assert.equal(manifest.source_held_record_count, 7928);
  assert.equal(manifest.held_document_count, 0);
  assert.equal(manifest.trace_record_count, 0);
  assert.equal(manifest.open_inquiry_record_count, 0);
  assert.equal(documents.length, 7995);
  assert.equal(byId.size, 7995);
});

const knownId = "SURF-MODERNAPITRACE2026R0155";
check(() => {
  const result = run(knownId)[0];
  assert.equal(result.document.stableId, knownId);
  assert.equal(result.explanation.label, "Exact stable ID");
});
check(() => {
  const result = run("Bauhaus: Art as Life")[0];
  assert.equal(result.document.stableId, knownId);
  assert.equal(result.explanation.label, "Exact title");
});
check(() => assert.ok(run("bauh").some((item) => item.document.stableId === knownId)));
check(() => assert.ok(run("bauhuas").some((item) => item.document.stableId === knownId && item.explanation.label === "Matched spelling variation")));
check(() => assert.ok(run("bauhaus art").some((item) => item.document.stableId === knownId)));
check(() => assert.ok(run("Almanach d Haiti").some((item) => item.document.stableId === "SURF-GALYEAR2026V1R0002")));
check(() => assert.ok(run("Irma Boom").some((item) => item.document.creditedLabel?.includes("Irma Boom"))));
check(() => assert.ok(run("United Kingdom").some((item) => item.document.place === "United Kingdom")));

check(() => {
  const filtered = run("", { yearFrom: 1960, yearTo: 1969 });
  assert.ok(filtered.length > 0);
  assert.ok(filtered.every((item) => item.document.yearStart <= 1969 && item.document.yearEnd >= 1960));
});
check(() => {
  const filtered = run("", { objectType: "Poster" });
  assert.ok(filtered.length > 0);
  assert.ok(filtered.every((item) => item.document.objectType === "Poster"));
});
check(() => {
  const theme = "Modern typography and layout";
  const filtered = run("", { theme });
  assert.ok(filtered.length > 0);
  assert.ok(filtered.every((item) => item.document.themes.includes(theme)));
});
check(() => {
  const movement = facets.movements[0].value;
  const filtered = run("", { movement });
  assert.ok(filtered.length > 0);
  assert.ok(filtered.every((item) => item.document.movements.includes(movement)));
  assert.equal(filtered[0].explanation.label, "Matched movement");
});
check(() => {
  const filtered = run("poster", { yearFrom: 1960, yearTo: 1969, objectType: "Poster", theme: "Modern typography and layout" });
  assert.ok(filtered.every((item) => item.document.yearEnd >= 1960 && item.document.yearStart <= 1969 && item.document.objectType === "Poster" && item.document.themes.includes("Modern typography and layout")));
});

check(() => {
  const request = core.normalizePublicSearchRequest({ query: "poster", filters: { yearFrom: 1960 } });
  const ranked = core.rankPublicSearchDocuments(documents, request);
  const page1 = core.pagePublicSearchResults({ ranked, request, first: 3, releaseId: manifest.release_id, manifestSha256: manifest.release_manifest_sha256, indexSha256: manifest.index_sha256 });
  assert.equal(page1.nodes.length, 3);
  assert.ok(page1.pageInfo.nextCursor);
  const page2 = core.pagePublicSearchResults({ ranked, request, first: 3, after: page1.pageInfo.nextCursor, releaseId: manifest.release_id, manifestSha256: manifest.release_manifest_sha256, indexSha256: manifest.index_sha256 });
  assert.equal(new Set([...page1.nodes, ...page2.nodes].map((item) => item.document.stableId)).size, 6);
  const mismatch = core.normalizePublicSearchRequest({ query: "poster", filters: { yearFrom: 1970 } });
  assert.throws(() => core.pagePublicSearchResults({ ranked, request: mismatch, first: 3, after: page1.pageInfo.nextCursor, releaseId: manifest.release_id, manifestSha256: manifest.release_manifest_sha256, indexSha256: manifest.index_sha256 }), /does not match/);
});

check(() => assert.throws(() => core.normalizePublicSearchRequest({ query: "", filters: {} }), /required/));
check(() => assert.throws(() => core.normalizePublicSearchRequest({ query: "poster", filters: { yearFrom: 2000, yearTo: 1900 } }), /greater/));
check(() => assert.throws(() => core.normalizePublicSearchRequest({ query: "a".repeat(161), filters: {} }), /at most 160/));

console.log(JSON.stringify({
  status: "PASS",
  check_count: checks,
  PUBLIC_SEARCH_DOCUMENT_COUNT: documents.length,
  HELD_SEARCH_DOCUMENT_COUNT: manifest.held_document_count,
  TRACE_RECORD_IN_SEARCH_INDEX_COUNT: manifest.trace_record_count,
  OPEN_INQUIRY_RECORD_IN_SEARCH_INDEX_COUNT: manifest.open_inquiry_record_count,
  SEARCH_STABLE_ID_EXACT_PASS: true,
  SEARCH_TITLE_EXACT_PASS: true,
  SEARCH_NORMALIZATION_PASS: true,
  SEARCH_PREFIX_PASS: true,
  SEARCH_MULTI_TOKEN_PASS: true,
  SEARCH_TYPO_BOUND_PASS: true,
  SEARCH_YEAR_FILTER_FAILURE_COUNT: 0,
  SEARCH_OBJECT_TYPE_FILTER_FAILURE_COUNT: 0,
  SEARCH_THEME_FILTER_FAILURE_COUNT: 0,
  SEARCH_MOVEMENT_FILTER_FAILURE_COUNT: 0,
  SEARCH_CURSOR_STATE_MISMATCH_COUNT: 0
}, null, 2));
