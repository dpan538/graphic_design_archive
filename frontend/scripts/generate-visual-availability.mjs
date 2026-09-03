import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/* Visual Availability Census (FRONTEND_DESIGN_DECISION.md §3c) over the
   sealed v49 public records. Four statuses are kept apart and never
   collapsed into one another:
     PUBLIC   public / held            (the Search v2 projection)
     READING  reader-facing / record-only   (reader-eligibility projection)
     VISUAL   this census
     EVIDENCE source verified / …      (trace.tier)
   The census reads governed fields (image state, rights state, display
   policy, review gate, licence label, credit) and the dated endpoint
   verification; it decides nothing about rights. MGDA_DISPLAYABLE_VISUAL is
   reserved for the visual registry — a record is displayable only when the
   registry says so, and the registry holds zero records in v49. */

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(here, "..");
const repositoryRoot = join(frontendRoot, "..");
const inputPath = join(repositoryRoot, "generated/public_surfaces_prefreeze_candidate_v48.json");
const searchDocumentsPath = join(frontendRoot, "generated/search-v2/documents.json");
const searchManifestPath = join(frontendRoot, "generated/search-v2/manifest.json");
const eligibilityPath = join(frontendRoot, "generated/reader-eligibility-v49/eligibility.json");
const endpointPath = join(frontendRoot, "generated/visual-availability-v49/endpoint-verification.json");
const outputDirectory = join(frontendRoot, "generated/visual-availability-v49");
const censusPath = join(outputDirectory, "census.json");
const manifestPath = join(outputDirectory, "manifest.json");
const checkOnly = process.argv.includes("--check");

const FORMAT = "gda-visual-availability-census-v1";
const VISUAL_REGISTRY_COUNT = 0; // v49: zero positive visual-rights records

/* what the source register (source/content.ts) records about each remote
   host's display terms — evidence for the promotion gate, not a decision */
const PROVIDER_TERMS = {
  "framemark.vam.ac.uk": { source: "V&A Collections API", terms: "V&A item rights and image-permission statements control display; image presence is not reuse permission.", embedding: "IIIF image service; item-level permission unresolved (rightsReviewed=false on every record)" },
  "ms01.nasjonalmuseet.no": { source: "Nasjonalmuseet Design collection / DigitaltMuseum", terms: "Display remains source-hosted and linked to the full object record; per-item licence carried by DigitaltMuseum.", embedding: "source image URL; open_candidate items reviewed (rightsReviewed=true); per-item licence and attribution still to be confirmed" },
  "www.artic.edu": { source: "Art Institute of Chicago API", terms: "AIC is_public_domain and item-page evidence control promotion; IIIF identifiers alone do not authorize display.", embedding: "IIIF image API; the endpoint refuses these requests (403) — remote embedding not available as recorded" },
  "upload.wikimedia.org": { source: "Wikimedia Commons (LOC-derived)", terms: "Commons licence fields control admission; only open-licence records are admitted; attribution and a source link are required.", embedding: "direct file URL; rate-limited for bursts (429); attribution required" },
};

const sha256 = (text) => createHash("sha256").update(text).digest("hex");

async function build() {
  const [inputText, documentsText, searchManifestText, eligibilityText, endpointText] = await Promise.all([
    readFile(inputPath, "utf8"),
    readFile(searchDocumentsPath, "utf8"),
    readFile(searchManifestPath, "utf8"),
    readFile(eligibilityPath, "utf8"),
    readFile(endpointPath, "utf8"),
  ]);
  const surfaces = new Map(JSON.parse(inputText).surfaces.map((s) => [s.surfaceId, s]));
  const documents = JSON.parse(documentsText);
  const searchManifest = JSON.parse(searchManifestText);
  const eligibility = new Map(JSON.parse(eligibilityText).entries.map((e) => [e[0], e[1]]));
  const endpoint = JSON.parse(endpointText);
  const endpointById = new Map(endpoint.results.map((r) => [r.stableId, r]));
  const fieldIndex = Object.fromEntries(documents.schema.map((name, index) => [name, index]));

  const rows = [];
  const count = (obj, key) => { obj[key] = (obj[key] ?? 0) + 1; };
  const byVisual = {};
  const byReadingVisual = {};
  const bySourceVisual = {};
  const remote = { total: 0, by_host: {}, gates: {} };
  const legacyImg03 = { public: 0, reader_facing: 0, remote_image: 0 };

  for (const tuple of documents.documents) {
    const stableId = tuple[fieldIndex.stableId];
    const s = surfaces.get(stableId);
    if (!s) throw new Error(`${stableId} missing from the canonical payload`);
    const delivery = tuple[fieldIndex.deliveryState];
    const reading = eligibility.get(stableId) ?? "RECORD_ONLY";
    const imageState = s.image?.state ?? null;
    const rightsState = s.rights?.state ?? null;
    const displayPolicy = s.rights?.displayPolicy ?? null;
    const rightsReviewed = s.reviewGates?.rightsReviewed === true;
    const licence = s.image?.licenseLabel ?? null;
    const credit = s.image?.credit ?? null;
    const imageUrl = s.image?.url ?? null;
    const sourceUrl = s.sourceUrl ?? null;
    const tier = s.trace?.tier ?? null;
    const probe = endpointById.get(stableId) ?? null;

    let visual;
    if (delivery === "REMOTE_IMAGE") visual = probe?.ok ? "REMOTE_VISUAL_CANDIDATE_VERIFIED" : "REMOTE_VISUAL_CANDIDATE_UNVERIFIED";
    else if (delivery === "SOURCE_VIEWER") visual = sourceUrl ? "SOURCE_VIEWER_AVAILABLE" : "NO_VALID_VISUAL_ROUTE";
    else if (delivery === "LINK_ONLY") visual = sourceUrl ? "SOURCE_LINK_ONLY" : "NO_VALID_VISUAL_ROUTE";
    else if (delivery === "CITATION_ONLY") visual = "CITATION_ONLY";
    else visual = "NO_VALID_VISUAL_ROUTE";

    const host = imageUrl ? new URL(imageUrl).host : null;
    const gate = delivery === "REMOTE_IMAGE"
      ? {
          endpoint_works: Boolean(probe?.ok),
          endpoint_status: probe?.status ?? null,
          provider_terms_recorded: Boolean(host && PROVIDER_TERMS[host]),
          item_rights_reviewed: rightsReviewed,
          attribution_recorded: Boolean(credit),
          registry_listed: false,
        }
      : null;
    if (gate) {
      remote.total += 1;
      const h = (remote.by_host[host ?? "none"] ??= { records: 0, endpoint_ok: 0, rights_reviewed: 0, attribution_recorded: 0, image_state: {}, reading: {} });
      h.records += 1;
      if (gate.endpoint_works) h.endpoint_ok += 1;
      if (gate.item_rights_reviewed) h.rights_reviewed += 1;
      if (gate.attribution_recorded) h.attribution_recorded += 1;
      count(h.image_state, imageState ?? "none");
      count(h.reading, reading);
      const passes = gate.endpoint_works && gate.provider_terms_recorded && gate.item_rights_reviewed && gate.attribution_recorded;
      count(remote.gates, passes ? "all_recorded_gates_pass_pending_registry" : !gate.endpoint_works ? "blocked_endpoint" : !gate.item_rights_reviewed ? "blocked_item_rights_unreviewed" : "blocked_terms_or_attribution");
    }
    if (imageState === "IMG03") {
      legacyImg03.public += 1;
      if (reading === "INDEX_ELIGIBLE") legacyImg03.reader_facing += 1;
      if (delivery === "REMOTE_IMAGE") legacyImg03.remote_image += 1;
    }

    count(byVisual, visual);
    count(byReadingVisual, `${reading} × ${visual}`);
    const sv = (bySourceVisual[tuple[fieldIndex.sourceLabel]] ??= {});
    count(sv, visual);
    rows.push([stableId, reading, visual, delivery, imageState, rightsState, displayPolicy, rightsReviewed ? 1 : 0, tier, host, gate ? (gate.endpoint_works ? 1 : 0) : null]);
  }

  const payload = {
    format: FORMAT,
    release_id: searchManifest.release_id,
    schema: ["stableId", "reading", "visual", "delivery", "imageState", "rightsState", "displayPolicy", "rightsReviewed", "tier", "imageHost", "endpointOk"],
    rows,
  };
  const serialized = `${JSON.stringify(payload)}\n`;
  const manifest = {
    format: `${FORMAT}-manifest`,
    release_id: searchManifest.release_id,
    canonical_input_sha256: sha256(inputText),
    search_index_sha256: searchManifest.index_sha256,
    endpoint_verification: { first_pass_at: endpoint.first_pass_at ?? endpoint.checked_at, last_pass_at: endpoint.checked_at, method: endpoint.method, checked: endpoint.count, ok: endpoint.ok },
    statuses: {
      MGDA_DISPLAYABLE_VISUAL: "listed in the v49 visual registry (positive rights) — reserved; the registry holds 0 records",
      REMOTE_VISUAL_CANDIDATE_VERIFIED: "Search delivery REMOTE_IMAGE and the recorded image endpoint returns an image (200/206, image/*)",
      REMOTE_VISUAL_CANDIDATE_UNVERIFIED: "Search delivery REMOTE_IMAGE but the endpoint refused, rate-limited or missed",
      SOURCE_VIEWER_AVAILABLE: "Search delivery SOURCE_VIEWER with a source record URL — 'View visual at source'",
      SOURCE_LINK_ONLY: "Search delivery LINK_ONLY with a source record URL",
      CITATION_ONLY: "Search delivery CITATION_ONLY — no visual route",
      NO_VALID_VISUAL_ROUTE: "no source URL and no image route",
    },
    counts: {
      public: rows.length,
      visual_registry_displayable: VISUAL_REGISTRY_COUNT,
      by_visual: byVisual,
      by_reading_x_visual: byReadingVisual,
      by_source_x_visual: bySourceVisual,
      priority_1_remote_image: remote,
      priority_2_legacy_img03: { canonical_total: 7370, ...legacyImg03, note: "the legacy IMG03 pool intersects the public projection in only the records counted here; the rest are HELD" },
      priority_3_source_viewer: byVisual.SOURCE_VIEWER_AVAILABLE ?? 0,
    },
    provider_terms: PROVIDER_TERMS,
    generated_at: new Date().toISOString().slice(0, 10) + "T00:00:00Z",
    census_sha256: sha256(serialized),
    census_bytes: Buffer.byteLength(serialized),
  };
  return { serialized, manifest };
}

const built = await build();
if (checkOnly) {
  const current = await readFile(censusPath, "utf8");
  if (current !== built.serialized) throw new Error("visual availability census is stale");
  console.log(JSON.stringify({ ok: true, counts: built.manifest.counts.by_visual }, null, 2));
} else {
  await mkdir(outputDirectory, { recursive: true });
  await writeFile(censusPath, built.serialized);
  await writeFile(manifestPath, `${JSON.stringify(built.manifest, null, 2)}\n`);
  console.log(JSON.stringify(built.manifest.counts, null, 2));
}
