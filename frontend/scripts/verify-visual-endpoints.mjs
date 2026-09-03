import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/* Visual Availability Census, step 1 — endpoint verification of every
   public record whose Search delivery state is REMOTE_IMAGE (the current
   remote-visual candidates). A HEAD (GET with a one-byte range where HEAD
   is refused) against the recorded image URL, recording status, content
   type, length, CORS and cache headers. Network-dependent: the result is
   dated, and the census (generate-visual-availability.mjs) reads it as
   evidence, never as a rights decision. */

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(here, "..");
const repositoryRoot = join(frontendRoot, "..");
const inputPath = join(repositoryRoot, "generated/public_surfaces_prefreeze_candidate_v48.json");
const searchDocumentsPath = join(frontendRoot, "generated/search-v2/documents.json");
const outputPath = join(frontendRoot, "generated/visual-availability-v49/endpoint-verification.json");
/* --retry re-probes only the records that did not verify, one at a time
   with a pause, with a browser-like agent — separating "refuses automated
   clients / rate-limits bursts" from "the image is not there" */
const retry = process.argv.includes("--retry");
const CONCURRENCY = retry ? 1 : 6;
const DELAY_MS = retry ? 2500 : 0;
const TIMEOUT_MS = 20000;
const USER_AGENT = retry
  ? "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36 MGDA-census/1.0"
  : "MGDA visual-availability census/1.0 (research archive; read-only endpoint check)";

const [inputText, documentsText] = await Promise.all([readFile(inputPath, "utf8"), readFile(searchDocumentsPath, "utf8")]);
const surfaces = new Map(JSON.parse(inputText).surfaces.map((s) => [s.surfaceId, s]));
const documents = JSON.parse(documentsText);
const fieldIndex = Object.fromEntries(documents.schema.map((name, index) => [name, index]));
let targets = documents.documents
  .filter((tuple) => tuple[fieldIndex.deliveryState] === "REMOTE_IMAGE")
  .map((tuple) => {
    const surface = surfaces.get(tuple[fieldIndex.stableId]);
    return { stableId: tuple[fieldIndex.stableId], sourceLabel: tuple[fieldIndex.sourceLabel], url: surface?.image?.url ?? null, imageState: surface?.image?.state ?? null };
  });
let previous = null;
if (retry) {
  previous = JSON.parse(await readFile(outputPath, "utf8"));
  const failed = new Set(previous.results.filter((r) => !r.ok).map((r) => r.stableId));
  targets = targets.filter((t) => failed.has(t.stableId));
}

async function probe(url, method) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  const started = Date.now();
  try {
    const headers = { "user-agent": USER_AGENT, accept: "image/*,*/*;q=0.5" };
    if (method === "GET") headers.range = "bytes=0-0";
    const response = await fetch(url, { method, headers, redirect: "follow", signal: controller.signal });
    if (method === "GET") {
      try {
        await response.body?.cancel();
      } catch {}
    }
    return {
      method,
      status: response.status,
      finalUrl: response.url,
      contentType: response.headers.get("content-type"),
      contentLength: response.headers.get("content-length"),
      acao: response.headers.get("access-control-allow-origin"),
      cacheControl: response.headers.get("cache-control"),
      server: response.headers.get("server"),
      ms: Date.now() - started,
    };
  } catch (error) {
    return { method, status: null, error: String(error?.name === "AbortError" ? "timeout" : error?.message ?? error), ms: Date.now() - started };
  } finally {
    clearTimeout(timer);
  }
}

async function check(target) {
  if (!target.url) return { ...target, ok: false, error: "no image url recorded" };
  let result = await probe(target.url, "HEAD");
  if (result.status === null || result.status === 405 || result.status === 403 || result.status >= 500) {
    result = await probe(target.url, "GET");
  }
  const ok = (result.status === 200 || result.status === 206) && String(result.contentType ?? "").startsWith("image/");
  return { ...target, host: new URL(target.url).host, ...result, ok };
}

const results = [];
let cursor = 0;
await Promise.all(
  Array.from({ length: CONCURRENCY }, async () => {
    while (cursor < targets.length) {
      const target = targets[cursor++];
      const checked = await check(target);
      results.push(retry ? { ...checked, pass: "retry" } : checked);
      if (DELAY_MS) await new Promise((r) => setTimeout(r, DELAY_MS));
    }
  }),
);
if (previous) {
  const retried = new Map(results.map((r) => [r.stableId, r]));
  for (const r of previous.results) if (!retried.has(r.stableId)) results.push(r);
}
results.sort((a, b) => a.stableId.localeCompare(b.stableId));
const byHost = {};
for (const r of results) {
  const h = (byHost[r.host ?? "none"] ??= { checked: 0, ok: 0, statuses: {} });
  h.checked += 1;
  if (r.ok) h.ok += 1;
  const key = String(r.status ?? r.error ?? "error");
  h.statuses[key] = (h.statuses[key] ?? 0) + 1;
}
const payload = {
  format: "gda-visual-endpoint-verification-v1",
  checked_at: new Date().toISOString(),
  first_pass_at: previous?.first_pass_at ?? previous?.checked_at ?? new Date().toISOString(),
  retry_pass: retry,
  method: "HEAD, then GET with Range: bytes=0-0 where HEAD is refused; 20 s timeout; redirects followed",
  count: results.length,
  ok: results.filter((r) => r.ok).length,
  by_host: byHost,
  results,
};
await mkdir(dirname(outputPath), { recursive: true });
await writeFile(outputPath, `${JSON.stringify(payload, null, 2)}\n`);
console.log(JSON.stringify({ count: payload.count, ok: payload.ok, by_host: byHost }, null, 2));
