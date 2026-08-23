import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import createJiti from "jiti";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(here, "..");
const repositoryRoot = join(frontendRoot, "..");
const jiti = createJiti(import.meta.url, {
  alias: {
    "@": join(frontendRoot, "src"),
    "server-only": join(here, "server-only-stub.mjs"),
  },
});
const core = await jiti.import(join(frontendRoot, "src/features/search-v49/core.ts"));
const server = await jiti.import(join(frontendRoot, "src/features/search-v49/server/derived-repository.ts"));

const payload = JSON.parse(await readFile(join(frontendRoot, "generated/search-v49/documents.json"), "utf8"));
const manifest = JSON.parse(await readFile(join(frontendRoot, "generated/search-v49/manifest.json"), "utf8"));
const documents = payload.documents.map(core.hydrateSearchDocument);
const byId = new Map(documents.map((document) => [document.stableId, document]));
const checks = [];
const pending = [];
function check(id, action) { const result = action(); if (result instanceof Promise) pending.push(result); checks.push(id); }
function search(query) { return core.rankDocuments(documents, core.parseSearchQuery(query)); }
function ids(query, count = 10) { return search(query).slice(0, count).map((item) => item.document.stableId); }

check("SEARCH-001 release boundary", () => {
  assert.equal(manifest.document_count, 7995);
  assert.equal(manifest.held_document_count, 7928);
  assert.equal(documents.length, 7995);
  assert.equal(byId.size, 7995);
  assert.deepEqual(manifest.public_fields, ["stableId", "title"]);
});

check("SEARCH-002 held records excluded", () => {
  const canonical = JSON.parse(requireText(join(repositoryRoot, "generated/public_surfaces_prefreeze_candidate_v48.json")));
  const held = canonical.surfaces.find((surface) => surface?.trace?.tier !== "source_verified");
  assert.ok(held?.surfaceId);
  assert.equal(byId.has(held.surfaceId), false);
});

const bauhausId = "SURF-MODERNAPITRACE2026R0155";
check("SEARCH-003 exact, prefix, typo", () => {
  assert.equal(ids("Bauhaus: Art as Life")[0], bauhausId);
  assert.ok(ids("bauh").includes(bauhausId));
  assert.ok(ids("bauhuas").includes(bauhausId));
});

check("SEARCH-004 stable identifier", () => {
  const result = search(bauhausId)[0];
  assert.equal(result.document.stableId, bauhausId);
  assert.equal(result.explanation.matchType, "identifier");
});

check("SEARCH-005 punctuation and whitespace", () => {
  assert.ok(ids("Bauhaus Art-as-Life").includes(bauhausId));
  assert.ok(ids("  bauhaus   art life ").includes(bauhausId));
});

check("SEARCH-006 safe Latin diacritic fallback", () => {
  assert.equal(ids("Almanach d Haiti")[0], "SURF-GALYEAR2026V1R0002");
  assert.equal(byId.get("SURF-GALYEAR2026V1R0002").title, "Almanach d'Haïti");
});

check("SEARCH-007 CJK substring", () => {
  assert.equal(ids("子宫")[0], "SURF-MDA2026V2R0448");
  assert.equal(ids("没有")[0], "SURF-MDA2026V2R0448");
});

check("SEARCH-008 no wildcard and punctuation-only", () => {
  assert.deepEqual(ids("%"), []);
  assert.deepEqual(ids("_"), []);
  assert.deepEqual(ids("!!!"), []);
});

check("SEARCH-009 no-result precision gate", () => {
  assert.deepEqual(ids("zzqxjv archival impossible token"), []);
  assert.deepEqual(ids("bauhaus zzqxjv"), []);
});

check("SEARCH-010 bounded edit policy", () => {
  assert.equal(core.boundedOsaDistance("bauhuas", "bauhaus", 1), 1);
  assert.equal(core.boundedOsaDistance("abc", "acb", 0), null);
  assert.equal(core.boundedOsaDistance("archive", "artichoke", 1), null);
});

check("SEARCH-011 query limits", () => {
  assert.equal(core.parseSearchQuery("界").primary, "界");
  assert.equal(Array.from(core.parseSearchQuery("a".repeat(160)).raw).length, 160);
  assert.throws(() => core.parseSearchQuery("a".repeat(161)), /1 to 160/);
  assert.throws(() => core.parseSearchQuery(" "), /1 to 160/);
  assert.throws(() => core.parseSearchQuery(Array.from({ length: 25 }, (_, i) => `t${i}`).join(" ")), /at most 24/);
});

check("SEARCH-012 deterministic order and display preservation", () => {
  const first = search("bauhaus").map((item) => [item.document.stableId, item.score]);
  const second = search("bauhaus").map((item) => [item.document.stableId, item.score]);
  assert.deepEqual(first, second);
  assert.equal(byId.get(bauhausId).title, "Bauhaus: Art as Life");
});

check("SEARCH-013 ranked cursor binding", () => {
  const query = core.parseSearchQuery("bauhaus");
  const ranked = core.rankDocuments(documents, query);
  const page1 = core.pageRankedDocuments({ ranked, query, first: 2, releaseId: manifest.release_id, manifestSha256: manifest.release_manifest_sha256, indexSha256: manifest.index_sha256, scope: "archive" });
  assert.equal(page1.nodes.length, 2);
  assert.ok(page1.pageInfo.nextCursor);
  const page2 = core.pageRankedDocuments({ ranked, query, first: 2, after: page1.pageInfo.nextCursor, releaseId: manifest.release_id, manifestSha256: manifest.release_manifest_sha256, indexSha256: manifest.index_sha256, scope: "archive" });
  assert.equal(new Set([...page1.nodes, ...page2.nodes].map((item) => item.document.stableId)).size, page1.nodes.length + page2.nodes.length);
  const other = core.parseSearchQuery("poster");
  assert.throws(() => core.pageRankedDocuments({ ranked, query: other, first: 2, after: page1.pageInfo.nextCursor, releaseId: manifest.release_id, manifestSha256: manifest.release_manifest_sha256, indexSha256: manifest.index_sha256, scope: "archive" }), /does not match/);
});

check("SEARCH-014 production provider exact-pair contract", async () => {
  const provider = new server.DerivedV49ArchiveRepositoryProvider();
  const current = await provider.open({ research: { alias: "current" } });
  assert.equal(current.ok, true);
  if (!current.ok) return;
  const result = await current.data.search({ q: "bauhuas", scope: "archive", sort: "relevance", first: 5 });
  assert.equal(result.ok, true);
  if (result.ok) {
    assert.ok(result.data.nodes.some((hit) => hit.surface.surfaceId === bauhausId));
    assert.equal(result.data.searchMetadata.indexSha256, manifest.index_sha256);
    assert.ok(result.data.nodes.every((hit) => hit.explanation?.algorithmVersion === manifest.search_algorithm_version));
  }
  const mismatch = await provider.open({ research: { researchReleaseId: manifest.release_id, researchManifestSha256: "0".repeat(64) } });
  assert.equal(mismatch.ok, false);
});

await Promise.all(pending);
console.log(`SEARCH_V49_TESTS=PASS CHECKS=${checks.length} DOCUMENTS=${documents.length}`);

function requireText(path) {
  return globalThis.process.getBuiltinModule("fs").readFileSync(path, "utf8");
}
