import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/* Reader eligibility — a governed projection over the sealed v49 public
   records (FRONTEND_DESIGN_DECISION.md §3b). Every public record is a legal,
   citable, reproducible archive record; not every public record is a
   reader-facing OBJECT. The Index browses reader-facing objects only; a
   record-only entry keeps its stable URL, source, citation and provenance,
   and is reachable by its ID.

   The rules are provenance-based, not guesses about the text:
     TITLE_IS_SOURCE_IDENTIFIER — the record's title equals one of its own
       source identifiers (sourceRecordId / sourceObjectKey / sourceLocator /
       surfaceId, or the source's system number carried in its source URL —
       the V&A "O#######" item number) and carries at most four letters;
     TITLE_NUMERIC_ONLY — the title carries no letters at all (a date or a
       number standing in for a title);
     TITLE_EMPTY.
   Everything else is INDEX_ELIGIBLE. Public eligibility and source
   verification are inherited from the Search v2 projection, which admits
   only trace.tier === source_verified records. */

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(here, "..");
const repositoryRoot = join(frontendRoot, "..");
const inputPath = join(repositoryRoot, "generated/public_surfaces_prefreeze_candidate_v48.json");
const searchDocumentsPath = join(frontendRoot, "generated/search-v2/documents.json");
const searchManifestPath = join(frontendRoot, "generated/search-v2/manifest.json");
const outputDirectory = join(frontendRoot, "generated/reader-eligibility-v49");
const eligibilityPath = join(outputDirectory, "eligibility.json");
const manifestPath = join(outputDirectory, "manifest.json");
const checksumsPath = join(outputDirectory, "CHECKSUMS.sha256");
const checkOnly = process.argv.includes("--check");

const FORMAT = "gda-reader-eligibility-v1";
const RULES_VERSION = "gda-reader-eligibility-rules-v1";
const GENERATED_AT = "2026-09-03T00:00:00Z";

const sha256 = (text) => createHash("sha256").update(text).digest("hex");
const normalise = (value) => String(value ?? "").replace(/[\s\-_./:]+/g, "").toLowerCase();
const letters = (text) => (String(text).match(/\p{L}/gu) ?? []).length;

function classify(document, surface) {
  const title = String(document.title ?? "").trim();
  const nt = normalise(title);
  if (!nt) return "TITLE_EMPTY";
  const identifiers = new Set(
    [surface.sourceRecordId, surface.sourceObjectKey, surface.sourceLocator, surface.surfaceId]
      .filter(Boolean)
      .map(normalise),
  );
  const systemNumber = /\/item\/(O\d+)/.exec(String(surface.sourceUrl ?? ""));
  if (systemNumber) identifiers.add(normalise(systemNumber[1]));
  if (identifiers.has(nt) && letters(title) <= 4) return "TITLE_IS_SOURCE_IDENTIFIER";
  if (letters(title) === 0) return "TITLE_NUMERIC_ONLY";
  return null;
}

async function build() {
  const [inputText, documentsText, searchManifestText] = await Promise.all([
    readFile(inputPath, "utf8"),
    readFile(searchDocumentsPath, "utf8"),
    readFile(searchManifestPath, "utf8"),
  ]);
  const input = JSON.parse(inputText);
  const documents = JSON.parse(documentsText);
  const searchManifest = JSON.parse(searchManifestText);
  const canonicalInputSha256 = sha256(inputText);
  if (canonicalInputSha256 !== searchManifest.canonical_input_sha256) {
    throw new Error("canonical payload does not match the Search v2 manifest's canonical_input_sha256");
  }
  const surfaces = new Map(input.surfaces.map((surface) => [surface.surfaceId, surface]));
  const fieldIndex = Object.fromEntries(documents.schema.map((name, index) => [name, index]));
  const entries = [];
  const byReason = {};
  const bySource = {};
  for (const tuple of documents.documents) {
    const document = { stableId: tuple[fieldIndex.stableId], title: tuple[fieldIndex.title], sourceLabel: tuple[fieldIndex.sourceLabel] };
    const surface = surfaces.get(document.stableId);
    if (!surface) throw new Error(`public document ${document.stableId} is missing from the canonical payload`);
    const reason = classify(document, surface);
    const eligibility = reason ? "RECORD_ONLY" : "INDEX_ELIGIBLE";
    entries.push([document.stableId, eligibility, reason]);
    if (reason) byReason[reason] = (byReason[reason] ?? 0) + 1;
    const source = (bySource[document.sourceLabel] ??= { public: 0, index_eligible: 0, record_only: 0 });
    source.public += 1;
    source[eligibility === "RECORD_ONLY" ? "record_only" : "index_eligible"] += 1;
  }
  const indexEligible = entries.filter((entry) => entry[1] === "INDEX_ELIGIBLE").length;
  const payload = {
    format: FORMAT,
    release_id: searchManifest.release_id,
    rules_version: RULES_VERSION,
    schema: ["stableId", "eligibility", "reason"],
    entries,
  };
  const serialized = `${JSON.stringify(payload)}\n`;
  const manifest = {
    format: `${FORMAT}-manifest`,
    release_id: searchManifest.release_id,
    release_manifest_sha256: searchManifest.release_manifest_sha256,
    canonical_input_sha256: canonicalInputSha256,
    search_index_sha256: searchManifest.index_sha256,
    rules_version: RULES_VERSION,
    rules: {
      eligibility_floor: ["public (Search v2 projection)", "trace.tier === source_verified (inherited)", "a human-readable title, by the provenance rules below"],
      TITLE_IS_SOURCE_IDENTIFIER: "title equals one of the record's own source identifiers (sourceRecordId, sourceObjectKey, sourceLocator, surfaceId, or the system number in its source URL) and carries at most four letters",
      TITLE_NUMERIC_ONLY: "title carries no letters",
      TITLE_EMPTY: "title is empty",
      note: "Rules read the record's own provenance fields; no rule inspects the text for 'meaningfulness'. Short real titles (PKZ, Mir, A-Z) stay INDEX_ELIGIBLE.",
    },
    counts: { public: entries.length, index_eligible: indexEligible, record_only: entries.length - indexEligible, by_reason: byReason, by_source: bySource },
    generated_at: GENERATED_AT,
    eligibility_sha256: sha256(serialized),
    eligibility_bytes: Buffer.byteLength(serialized),
  };
  const manifestSerialized = `${JSON.stringify(manifest, null, 2)}\n`;
  const checksums = `${manifest.eligibility_sha256}  eligibility.json\n${sha256(manifestSerialized)}  manifest.json\n`;
  return { serialized, manifestSerialized, checksums, manifest };
}

const built = await build();
if (checkOnly) {
  const [current, currentManifest] = await Promise.all([readFile(eligibilityPath, "utf8"), readFile(manifestPath, "utf8")]);
  if (current !== built.serialized) throw new Error("reader eligibility artifact is stale: eligibility.json differs");
  if (JSON.parse(currentManifest).eligibility_sha256 !== built.manifest.eligibility_sha256) throw new Error("reader eligibility artifact is stale: manifest differs");
  console.log(JSON.stringify({ ok: true, counts: built.manifest.counts }, null, 2));
} else {
  await mkdir(outputDirectory, { recursive: true });
  await writeFile(eligibilityPath, built.serialized);
  await writeFile(manifestPath, built.manifestSerialized);
  await writeFile(checksumsPath, built.checksums);
  console.log(JSON.stringify({ written: outputDirectory, counts: built.manifest.counts }, null, 2));
}
