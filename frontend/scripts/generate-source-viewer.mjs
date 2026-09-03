import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/* Source-viewer projection (FRONTEND_DESIGN_DECISION.md §3d, step 1): the
   holding source's record URL for every public record, projected from the
   sealed canonical payload so an Object page can always offer "View at
   source" — the one visual route every public record has, whatever the
   visual registry later decides. Carries the URL, the source document URL
   where one was captured, the capture's access date and the pipeline's
   source-URL review flag. No network; URLs are checked for shape only. */

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(here, "..");
const repositoryRoot = join(frontendRoot, "..");
const inputPath = join(repositoryRoot, "generated/public_surfaces_prefreeze_candidate_v48.json");
const searchDocumentsPath = join(frontendRoot, "generated/search-v2/documents.json");
const searchManifestPath = join(frontendRoot, "generated/search-v2/manifest.json");
const outputDirectory = join(frontendRoot, "generated/source-viewer-v49");
const projectionPath = join(outputDirectory, "source-viewer.json");
const manifestPath = join(outputDirectory, "manifest.json");
const checksumsPath = join(outputDirectory, "CHECKSUMS.sha256");
const checkOnly = process.argv.includes("--check");
const FORMAT = "gda-source-viewer-v1";
const sha256 = (text) => createHash("sha256").update(text).digest("hex");

function cleanUrl(value) {
  if (typeof value !== "string") return null;
  const text = value.trim();
  if (!text) return null;
  try {
    const url = new URL(text);
    if (url.protocol !== "https:" && url.protocol !== "http:") return null;
    return url.toString();
  } catch {
    return null;
  }
}

async function build() {
  const [inputText, documentsText, searchManifestText] = await Promise.all([
    readFile(inputPath, "utf8"),
    readFile(searchDocumentsPath, "utf8"),
    readFile(searchManifestPath, "utf8"),
  ]);
  const searchManifest = JSON.parse(searchManifestText);
  if (sha256(inputText) !== searchManifest.canonical_input_sha256) throw new Error("canonical payload does not match the Search v2 manifest");
  const surfaces = new Map(JSON.parse(inputText).surfaces.map((s) => [s.surfaceId, s]));
  const documents = JSON.parse(documentsText);
  const fieldIndex = Object.fromEntries(documents.schema.map((name, index) => [name, index]));
  const entries = [];
  const hosts = {};
  let withUrl = 0;
  let withDocument = 0;
  let reviewed = 0;
  let https = 0;
  for (const tuple of documents.documents) {
    const stableId = tuple[fieldIndex.stableId];
    const s = surfaces.get(stableId);
    if (!s) throw new Error(`${stableId} missing from the canonical payload`);
    const sourceUrl = cleanUrl(s.sourceUrl);
    const documentUrl = cleanUrl(s.sourceDocumentUrl);
    const accessDate = typeof s.accessDate === "string" && /^\d{4}-\d{2}-\d{2}$/.test(s.accessDate) ? s.accessDate : null;
    const urlReviewed = s.reviewGates?.sourceUrl === true ? 1 : 0;
    if (sourceUrl) {
      withUrl += 1;
      const host = new URL(sourceUrl).host;
      hosts[host] = (hosts[host] ?? 0) + 1;
      if (sourceUrl.startsWith("https:")) https += 1;
    }
    if (documentUrl) withDocument += 1;
    if (urlReviewed) reviewed += 1;
    entries.push([stableId, sourceUrl, documentUrl, accessDate, urlReviewed]);
  }
  const payload = { format: FORMAT, release_id: searchManifest.release_id, schema: ["stableId", "sourceUrl", "sourceDocumentUrl", "accessDate", "sourceUrlReviewed"], entries };
  const serialized = `${JSON.stringify(payload)}\n`;
  const manifest = {
    format: `${FORMAT}-manifest`,
    release_id: searchManifest.release_id,
    canonical_input_sha256: searchManifest.canonical_input_sha256,
    search_index_sha256: searchManifest.index_sha256,
    counts: { public: entries.length, with_source_url: withUrl, https: https, with_source_document_url: withDocument, source_url_reviewed: reviewed, hosts: Object.fromEntries(Object.entries(hosts).sort((a, b) => b[1] - a[1])) },
    generated_at: "2026-09-03T00:00:00Z",
    projection_sha256: sha256(serialized),
    projection_bytes: Buffer.byteLength(serialized),
  };
  const manifestSerialized = `${JSON.stringify(manifest, null, 2)}\n`;
  return { serialized, manifestSerialized, manifest, checksums: `${manifest.projection_sha256}  source-viewer.json\n${sha256(manifestSerialized)}  manifest.json\n` };
}

const built = await build();
if (checkOnly) {
  const current = await readFile(projectionPath, "utf8");
  if (current !== built.serialized) throw new Error("source-viewer projection is stale");
  console.log(JSON.stringify({ ok: true, counts: built.manifest.counts }, null, 2));
} else {
  await mkdir(outputDirectory, { recursive: true });
  await writeFile(projectionPath, built.serialized);
  await writeFile(manifestPath, built.manifestSerialized);
  await writeFile(checksumsPath, built.checksums);
  console.log(JSON.stringify(built.manifest.counts, null, 2));
}
