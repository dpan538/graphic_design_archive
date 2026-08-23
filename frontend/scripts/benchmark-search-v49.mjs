import { createHash } from "node:crypto";
import { readFile, mkdir, writeFile } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { performance } from "node:perf_hooks";
import createJiti from "jiti";

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(here, "..");
const repositoryRoot = join(frontendRoot, "..");
const researchDirectory = join(repositoryRoot, "docs/research/search-v49-round1");
const auditDirectory = join(repositoryRoot, "docs/audits/v49-search-fuzzy-round1");
const jiti = createJiti(import.meta.url, { alias: { "@": join(frontendRoot, "src") } });
const core = await jiti.import(join(frontendRoot, "src/features/search-v49/core.ts"));

const readStarted = performance.now();
const documentsText = await readFile(join(frontendRoot, "generated/search-v49/documents.json"), "utf8");
const readMs = performance.now() - readStarted;
const parseStarted = performance.now();
const payload = JSON.parse(documentsText);
const parseMs = performance.now() - parseStarted;
const hydrateStarted = performance.now();
const documents = payload.documents.map(core.hydrateSearchDocument);
const hydrateMs = performance.now() - hydrateStarted;
const manifest = JSON.parse(await readFile(join(frontendRoot, "generated/search-v49/manifest.json"), "utf8"));
const coldQueryStarted = performance.now();
core.rankDocuments(documents, core.parseSearchQuery("bauhuas"));
const coldQueryMs = performance.now() - coldQueryStarted;

const hash = (value) => createHash("sha256").update(value).digest("hex");
const ordered = [...documents].sort((left, right) => hash(left.stableId).localeCompare(hash(right.stableId)));
const primaryCount = new Map();
const foldedCount = new Map();
const tokenOwners = new Map();
const prefixCount = new Map();
for (const document of documents) {
  primaryCount.set(document.primary, (primaryCount.get(document.primary) ?? 0) + 1);
  foldedCount.set(document.latinFolded, (foldedCount.get(document.latinFolded) ?? 0) + 1);
  for (const token of new Set(document.tokens)) {
    const owners = tokenOwners.get(token) ?? [];
    owners.push(document.stableId); tokenOwners.set(token, owners);
  }
  const codePoints = Array.from(document.primary);
  for (let length = 4; length <= Math.min(14, codePoints.length - 1); length += 1) {
    const prefix = codePoints.slice(0, length).join("");
    prefixCount.set(prefix, (prefixCount.get(prefix) ?? 0) + 1);
  }
}

const cases = [];
const seenCase = new Set();
function add(category, query, expectedId, notes = "") {
  const key = `${category}\u0000${query}\u0000${expectedId ?? ""}`;
  if (!query.trim() || seenCase.has(key)) return false;
  seenCase.add(key);
  const selector = Number.parseInt(hash(key).slice(0, 2), 16);
  cases.push({ id: `Q${String(cases.length + 1).padStart(3, "0")}`, category, query, expectedIds: expectedId ? [expectedId] : [], split: selector % 4 === 0 ? "tuning" : "held_out", notes });
  return true;
}
function fill(category, count, candidates) {
  const before = cases.length;
  for (const candidate of candidates) {
    if (cases.length - before >= count) break;
    add(category, candidate.query, candidate.expectedId, candidate.notes);
  }
  if (cases.length - before !== count) throw new Error(`${category}: expected ${count} benchmark cases, built ${cases.length - before}`);
}

const uniqueTitles = ordered.filter((document) => Array.from(document.title.trim()).length >= 6 && Array.from(document.title.trim()).length <= 160 && primaryCount.get(document.primary) === 1);
fill("exact_title", 30, uniqueTitles.map((document) => ({ query: document.title, expectedId: document.stableId })));
fill("stable_id", 20, ordered.map((document) => ({ query: document.stableId, expectedId: document.stableId })));
fill("case", 15, uniqueTitles.filter((document) => /\p{Ll}/u.test(document.title)).map((document) => ({ query: document.title.toUpperCase(), expectedId: document.stableId })));
fill("punctuation", 15, uniqueTitles.filter((document) => /[\p{P}\p{S}]/u.test(document.title) && document.primary.split(" ").length > 1).map((document) => ({ query: document.primary, expectedId: document.stableId })));
fill("whitespace", 15, uniqueTitles.filter((document) => document.primary.split(" ").length > 2).map((document) => ({ query: document.primary.split(" ").join("   "), expectedId: document.stableId })));
fill("latin_diacritic", 15, ordered.filter((document) => document.latinFolded !== document.primary && Array.from(document.latinFolded).length <= 160 && foldedCount.get(document.latinFolded) === 1).map((document) => ({ query: document.latinFolded, expectedId: document.stableId })));

const prefixes = [];
for (const document of ordered) {
  const points = Array.from(document.primary);
  for (let length = 4; length <= Math.min(14, points.length - 1); length += 1) {
    const query = points.slice(0, length).join("");
    if (prefixCount.get(query) === 1) { prefixes.push({ query, expectedId: document.stableId }); break; }
  }
}
fill("unique_prefix", 25, prefixes);

const middles = [];
for (const document of ordered.slice(0, 1200)) {
  const points = Array.from(document.primary);
  if (points.length < 12) continue;
  const start = Math.max(2, Math.floor(points.length / 3));
  const query = points.slice(start, Math.min(points.length - 2, start + 9)).join("").trim();
  if (Array.from(query).length < 5) continue;
  if (documents.filter((candidate) => candidate.primary.includes(query)).length === 1) middles.push({ query, expectedId: document.stableId });
}
fill("unique_middle_substring", 20, middles);

function uniqueTokens(minimumLength = 4) {
  const output = [];
  for (const document of ordered) for (const token of document.tokens) {
    if (/^\p{Script=Latin}+$/u.test(token) && Array.from(token).length >= minimumLength && tokenOwners.get(token)?.length === 1) output.push({ document, token });
  }
  return output;
}
const substitutions = uniqueTokens().map(({ document, token }) => {
  const points = Array.from(token); const index = Math.floor(points.length / 2); points[index] = points[index] === "x" ? "z" : "x";
  return { query: points.join(""), expectedId: document.stableId, notes: `source token=${token}` };
}).filter((candidate) => !tokenOwners.has(candidate.query));
fill("one_character_substitution", 20, substitutions);

const transpositions = uniqueTokens().flatMap(({ document, token }) => {
  const points = Array.from(token); let index = Math.floor(points.length / 2) - 1;
  while (index < points.length - 1 && points[index] === points[index + 1]) index += 1;
  if (index >= points.length - 1) return [];
  [points[index], points[index + 1]] = [points[index + 1], points[index]];
  return [{ query: points.join(""), expectedId: document.stableId, notes: `source token=${token}` }];
}).filter((candidate) => !tokenOwners.has(candidate.query));
fill("adjacent_transposition", 20, transpositions);

const tokenPairs = [];
for (const document of ordered.slice(0, 2000)) {
  const unique = [...new Set(document.tokens)].filter((token) => token.length >= 3);
  if (unique.length < 2) continue;
  const pair = [unique[0], unique.at(-1)];
  const owners = documents.filter((candidate) => pair.every((token) => candidate.tokens.includes(token)));
  if (owners.length === 1) tokenPairs.push({ document, pair });
}
fill("ordered_two_token", 15, tokenPairs.map(({ document, pair }) => ({ query: pair.join(" "), expectedId: document.stableId })));
fill("out_of_order_tokens", 15, tokenPairs.slice(20).map(({ document, pair }) => ({ query: [...pair].reverse().join(" "), expectedId: document.stableId })));
fill("incomplete_multi_token", 10, tokenPairs.slice(50).map(({ document, pair }) => ({ query: pair.map((token) => Array.from(token).slice(0, Math.min(4, Array.from(token).length)).join("")).join(" "), expectedId: document.stableId })));

for (const query of ["没有", "子宫", "闭嘴", "no uterus", "no opinion", "没有 子宫"]) add("real_cjk_bilingual", query, "SURF-MDA2026V2R0448");
for (let index = 0; index < 15; index += 1) add("verified_no_result", `zzqxjv${String(index).padStart(2, "0")} nonexistent`, null);
for (const query of ["a", "an", "art", "design", "poster", "the", "new", "1", "i", "de", "la", "modern", "book", "type", "x"]) add("ambiguous_short_manual", query, null, "excluded from mechanical relevance metrics");

if (cases.length !== 271) throw new Error(`benchmark case count must be 271, found ${cases.length}`);

function oldSearch(query) {
  const needle = query.trim().toLowerCase();
  if (!needle) return [];
  return documents.filter((document) => document.title.toLowerCase().includes(needle))
    .sort((left, right) => left.title.toLowerCase().localeCompare(right.title.toLowerCase()) || left.stableId.localeCompare(right.stableId));
}

for (const warm of cases.slice(0, 12)) { oldSearch(warm.query); core.rankDocuments(documents, core.parseSearchQuery(warm.query)); }
const oldDurations = []; const newDurations = []; const serializeDurations = [];
for (const testCase of cases) {
  const oldStarted = performance.now();
  const oldResults = oldSearch(testCase.query);
  const oldMs = performance.now() - oldStarted;
  const parsed = core.parseSearchQuery(testCase.query);
  const newStarted = performance.now();
  const newResults = core.rankDocuments(documents, parsed);
  const newMs = performance.now() - newStarted;
  const serializeStarted = performance.now();
  JSON.stringify(newResults.slice(0, 25).map((result) => ({ id: result.document.stableId, score: result.score, explanation: result.explanation })));
  const serializeMs = performance.now() - serializeStarted;
  testCase.oldTop10 = oldResults.slice(0, 10).map((document) => document.stableId);
  testCase.newTop10 = newResults.slice(0, 10).map((result) => result.document.stableId);
  testCase.oldCount = oldResults.length; testCase.newCount = newResults.length;
  testCase.oldMs = oldMs; testCase.newMs = newMs; testCase.serializeMs = serializeMs;
  oldDurations.push(oldMs); newDurations.push(newMs); serializeDurations.push(serializeMs);
}

function percentile(values, quantile) { const sorted = [...values].sort((a, b) => a - b); return sorted[Math.min(sorted.length - 1, Math.floor(quantile * sorted.length))]; }
function metrics(selected, key) {
  const positive = selected.filter((entry) => entry.expectedIds.length && entry.category !== "ambiguous_short_manual");
  const noResult = selected.filter((entry) => entry.category === "verified_no_result");
  let top1 = 0; let top5 = 0; let recall10 = 0; let reciprocal = 0;
  for (const entry of positive) {
    const ranking = entry[key];
    const position = ranking.findIndex((id) => entry.expectedIds.includes(id));
    if (position === 0) top1 += 1;
    if (position >= 0 && position < 5) top5 += 1;
    if (position >= 0) { recall10 += 1; reciprocal += 1 / (position + 1); }
  }
  const noResultCorrect = noResult.filter((entry) => entry[key].length === 0).length;
  return {
    positiveQueries: positive.length,
    top1: top1 / positive.length,
    top5: top5 / positive.length,
    recallAt10: recall10 / positive.length,
    mrrAt10: reciprocal / positive.length,
    noResultQueries: noResult.length,
    noResultPrecision: noResult.length ? noResultCorrect / noResult.length : null,
  };
}
function categoryRecovery(selected, categories, key) {
  const relevant = selected.filter((entry) => categories.includes(entry.category) && entry.expectedIds.length);
  return relevant.length ? relevant.filter((entry) => entry[key].some((id) => entry.expectedIds.includes(id))).length / relevant.length : null;
}

const heldOut = cases.filter((entry) => entry.split === "held_out");
const checksumsBefore = await readFile(join(frontendRoot, "generated/search-v49/CHECKSUMS.sha256"), "utf8");
const generationStarted = performance.now();
const generation = spawnSync(process.execPath, [join(here, "generate-search-v49.mjs")], { encoding: "utf8" });
const generationBuildMs = performance.now() - generationStarted;
if (generation.status !== 0) throw new Error(generation.stderr || generation.stdout);
const checksumsAfterFirst = await readFile(join(frontendRoot, "generated/search-v49/CHECKSUMS.sha256"), "utf8");
const secondGeneration = spawnSync(process.execPath, [join(here, "generate-search-v49.mjs")], { encoding: "utf8" });
if (secondGeneration.status !== 0) throw new Error(secondGeneration.stderr || secondGeneration.stdout);
const checksumsAfterSecond = await readFile(join(frontendRoot, "generated/search-v49/CHECKSUMS.sha256"), "utf8");
if (checksumsBefore !== checksumsAfterFirst || checksumsAfterFirst !== checksumsAfterSecond) throw new Error("search index rebuild is nondeterministic");
if (global.gc) global.gc();
const memory = process.memoryUsage();
const worst = [...cases].sort((left, right) => right.newMs - left.newMs).slice(0, 10).map((entry) => ({ id: entry.id, category: entry.category, query: entry.query, newMs: entry.newMs }));
const failures = heldOut.filter((entry) => entry.expectedIds.length && !entry.expectedIds.includes(entry.newTop10[0]))
  .sort((left, right) => right.newCount - left.newCount || right.newMs - left.newMs);
const supplemental = heldOut.filter((entry) => entry.expectedIds.length && entry.newTop10.length > 1)
  .sort((left, right) => right.newCount - left.newCount || right.newMs - left.newMs);
const ambiguousNoise = heldOut.filter((entry) => entry.category === "ambiguous_short_manual" && entry.newTop10.length)
  .sort((left, right) => right.newCount - left.newCount || right.newMs - left.newMs);
const failureCandidates = [...failures, ...supplemental.filter((entry) => !failures.includes(entry)), ...ambiguousNoise].slice(0, 25).map((entry) => ({
  id: entry.id, category: entry.category, query: entry.query, expectedIds: entry.expectedIds,
  observedTop5: entry.newTop10.slice(0, 5), expectedRank: entry.newTop10.findIndex((id) => entry.expectedIds.includes(id)) + 1,
  resultCount: entry.newCount, newMs: entry.newMs,
}));

const report = {
  schema: "gda-search-benchmark-v1",
  sourceSha: manifest.source_sha,
  sourceTreeHash: manifest.source_tree_hash,
  releaseId: manifest.release_id,
  releaseManifestSha256: manifest.release_manifest_sha256,
  indexSha256: manifest.index_sha256,
  algorithmVersion: manifest.search_algorithm_version,
  environment: { node: process.version, unicode: process.versions.unicode, platform: process.platform, arch: process.arch },
  corpus: { canonical: 15923, publicSearchable: documents.length, heldExcluded: manifest.held_document_count, indexedFields: manifest.public_fields },
  evaluation: { totalQueries: cases.length, tuningQueries: cases.length - heldOut.length, heldOutQueries: heldOut.length },
  old: metrics(heldOut, "oldTop10"),
  new: metrics(heldOut, "newTop10"),
  recovery: {
    prefixOld: categoryRecovery(heldOut, ["unique_prefix", "incomplete_multi_token"], "oldTop10"),
    prefixNew: categoryRecovery(heldOut, ["unique_prefix", "incomplete_multi_token"], "newTop10"),
    typoOld: categoryRecovery(heldOut, ["one_character_substitution", "adjacent_transposition"], "oldTop10"),
    typoNew: categoryRecovery(heldOut, ["one_character_substitution", "adjacent_transposition"], "newTop10"),
    multilingualOld: categoryRecovery(heldOut, ["latin_diacritic", "real_cjk_bilingual"], "oldTop10"),
    multilingualNew: categoryRecovery(heldOut, ["latin_diacritic", "real_cjk_bilingual"], "newTop10"),
  },
  performance: {
    readMs, parseMs, hydrateMs, coldQueryMs, generationBuildMs, indexRebuildDeterministic: true,
    candidateGeneration: { strategy: "fixed full public corpus", candidateCount: documents.length, measuredSeparateMs: 0 },
    oldComputeMs: { p50: percentile(oldDurations, .5), p95: percentile(oldDurations, .95), max: Math.max(...oldDurations) },
    newComputeMs: { p50: percentile(newDurations, .5), p95: percentile(newDurations, .95), max: Math.max(...newDurations) },
    serializationMs: { p50: percentile(serializeDurations, .5), p95: percentile(serializeDurations, .95), max: Math.max(...serializeDurations) },
    memory: { rssBytes: memory.rss, heapUsedBytes: memory.heapUsed },
    worst,
  },
  artifact: { bytes: manifest.index_bytes, gzipBytes: manifest.index_gzip_bytes, documentCount: manifest.document_count },
  failureCandidates,
};

const quoteTsv = (value) => String(value ?? "").replaceAll("\t", " ").replaceAll("\r", " ").replaceAll("\n", " ");
const header = ["query_id", "split", "category", "query", "expected_record_ids", "old_top10", "new_top10", "old_rank", "new_rank", "old_success", "new_success", "old_count", "new_count", "old_ms", "new_ms", "notes"];
const rows = cases.map((entry) => {
  const oldRank = entry.expectedIds.length ? entry.oldTop10.findIndex((id) => entry.expectedIds.includes(id)) + 1 : entry.oldTop10.length === 0 ? 0 : -1;
  const newRank = entry.expectedIds.length ? entry.newTop10.findIndex((id) => entry.expectedIds.includes(id)) + 1 : entry.newTop10.length === 0 ? 0 : -1;
  const oldSuccess = entry.expectedIds.length ? oldRank > 0 : entry.oldTop10.length === 0;
  const newSuccess = entry.expectedIds.length ? newRank > 0 : entry.newTop10.length === 0;
  return [entry.id, entry.split, entry.category, entry.query, entry.expectedIds.join(";"), entry.oldTop10.join(";"), entry.newTop10.join(";"), oldRank, newRank, oldSuccess, newSuccess, entry.oldCount, entry.newCount, entry.oldMs.toFixed(3), entry.newMs.toFixed(3), entry.notes || "none"].map(quoteTsv).join("\t");
});
await mkdir(researchDirectory, { recursive: true });
await mkdir(auditDirectory, { recursive: true });
await writeFile(join(researchDirectory, "03_SEARCH_QUALITY_COMPARISON.tsv"), `${header.join("\t")}\n${rows.join("\n")}\n`);
await writeFile(join(auditDirectory, "benchmark-results.json"), `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report, null, 2));
