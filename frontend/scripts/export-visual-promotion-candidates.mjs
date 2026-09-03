import { readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/* Visual registry, batch 1 — the promotion CANDIDATES the census can put in
   front of a reviewer: remote-visual candidates whose endpoint verified and
   whose item rights are recorded as reviewed (Nasjonalmuseet, then Commons).
   This is a review sheet, not the registry: nothing here is displayable
   until a reviewer writes it into registry.json with its evidence. */

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(here, "..");
const repositoryRoot = join(frontendRoot, "..");
const inputPath = join(repositoryRoot, "generated/public_surfaces_prefreeze_candidate_v48.json");
const censusPath = join(frontendRoot, "generated/visual-availability-v49/census.json");
const endpointPath = join(frontendRoot, "generated/visual-availability-v49/endpoint-verification.json");
const outputPath = join(frontendRoot, "generated/visual-registry-v49/promotion-candidates-batch-1.json");

const [inputText, censusText, endpointText] = await Promise.all([readFile(inputPath, "utf8"), readFile(censusPath, "utf8"), readFile(endpointPath, "utf8")]);
const surfaces = new Map(JSON.parse(inputText).surfaces.map((s) => [s.surfaceId, s]));
const census = JSON.parse(censusText);
const endpoint = new Map(JSON.parse(endpointText).results.map((r) => [r.stableId, r]));
const ix = Object.fromEntries(census.schema.map((name, index) => [name, index]));
const ORDER = { "ms01.nasjonalmuseet.no": 1, "upload.wikimedia.org": 2, "framemark.vam.ac.uk": 3, "www.artic.edu": 4 };
const candidates = census.rows
  .filter((r) => r[ix.visual] === "REMOTE_VISUAL_CANDIDATE_VERIFIED" && r[ix.rightsReviewed] === 1 && r[ix.reading] === "INDEX_ELIGIBLE")
  .map((r) => {
    const s = surfaces.get(r[ix.stableId]);
    const probe = endpoint.get(r[ix.stableId]);
    return {
      stableId: r[ix.stableId],
      title: s.title,
      sourceName: s.sourceName,
      sourceUrl: s.sourceUrl,
      imageUrl: s.image?.url ?? null,
      host: r[ix.imageHost],
      imageState: r[ix.imageState],
      rightsState: r[ix.rightsState],
      licenceLabel: s.image?.licenseLabel ?? null,
      credit: s.image?.credit ?? null,
      rightsReviewed: true,
      endpoint: { status: probe?.status ?? null, contentType: probe?.contentType ?? null, checkedAt: probe?.pass === "retry" ? "retry pass" : "first pass" },
      decision: null,
    };
  })
  .sort((a, b) => (ORDER[a.host] ?? 9) - (ORDER[b.host] ?? 9) || a.stableId.localeCompare(b.stableId));
const byHost = {};
for (const c of candidates) byHost[c.host] = (byHost[c.host] ?? 0) + 1;
await writeFile(outputPath, `${JSON.stringify({ format: "gda-visual-promotion-candidates-v1", release_id: census.release_id, batch: 1, note: "Review sheet. A candidate becomes displayable only when written into registry.json with its evidence and a reviewer's decision.", count: candidates.length, by_host: byHost, candidates }, null, 2)}\n`);
console.log(JSON.stringify({ count: candidates.length, by_host: byHost }, null, 2));
