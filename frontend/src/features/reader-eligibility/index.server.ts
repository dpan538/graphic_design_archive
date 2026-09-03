import "server-only";

import { createHash } from "node:crypto";
import eligibilityJson from "../../../generated/reader-eligibility-v49/eligibility.json";
import manifestJson from "../../../generated/reader-eligibility-v49/manifest.json";
import { getPublicSearchIndex } from "@/features/search-v2/index.server";

/* Reader eligibility — the governed projection that says which public
   records are reader-facing OBJECTS (the Index browses these) and which
   are RECORD-ONLY entries (a stable URL, source, citation and provenance,
   reachable by ID, not listed). Built by scripts/generate-reader-
   eligibility.mjs from the sealed release; verified here against the
   Search v2 projection it sits on. Never decided in the UI. */

export type ReaderEligibility = "INDEX_ELIGIBLE" | "RECORD_ONLY";
export type ReaderEligibilityReason = "TITLE_IS_SOURCE_IDENTIFIER" | "TITLE_NUMERIC_ONLY" | "TITLE_EMPTY" | null;

type Payload = {
  format: string;
  release_id: string;
  rules_version: string;
  schema: readonly string[];
  entries: readonly (readonly [string, ReaderEligibility, ReaderEligibilityReason])[];
};

type Manifest = {
  format: string;
  release_id: string;
  canonical_input_sha256: string;
  search_index_sha256: string;
  rules_version: string;
  counts: { public: number; index_eligible: number; record_only: number };
  eligibility_sha256: string;
  eligibility_bytes: number;
};

export type ReaderEligibilityIndex = {
  manifest: Manifest;
  byId: ReadonlyMap<string, { eligibility: ReaderEligibility; reason: ReaderEligibilityReason }>;
};

let cached: ReaderEligibilityIndex | null = null;

export function getReaderEligibilityIndex(): ReaderEligibilityIndex {
  if (cached) return cached;
  const payload = eligibilityJson as unknown as Payload;
  const manifest = manifestJson as unknown as Manifest;
  const search = getPublicSearchIndex();
  const serialized = `${JSON.stringify(payload)}\n`;
  const valid =
    payload.format === "gda-reader-eligibility-v1" &&
    payload.release_id === manifest.release_id &&
    manifest.release_id === search.manifest.release_id &&
    manifest.canonical_input_sha256 === search.manifest.canonical_input_sha256 &&
    manifest.search_index_sha256 === search.manifest.index_sha256 &&
    payload.rules_version === manifest.rules_version &&
    payload.entries.length === manifest.counts.public &&
    manifest.counts.public === search.manifest.document_count &&
    manifest.counts.index_eligible + manifest.counts.record_only === manifest.counts.public &&
    manifest.eligibility_sha256 === createHash("sha256").update(serialized).digest("hex") &&
    manifest.eligibility_bytes === Buffer.byteLength(serialized);
  if (!valid) throw new Error("reader eligibility artifact failed its release, checksum or count gate");
  const byId = new Map(payload.entries.map(([id, eligibility, reason]) => [id, { eligibility, reason }] as const));
  if (byId.size !== payload.entries.length) throw new Error("reader eligibility artifact contains duplicate stable IDs");
  for (const id of byId.keys()) {
    if (!search.byId.has(id)) throw new Error(`reader eligibility names ${id}, which is not a public document`);
  }
  cached = { manifest, byId };
  return cached;
}

/** A public record's eligibility; a record the projection does not name is
 * treated as record-only (fail closed). */
export function readerEligibilityOf(stableId: string): ReaderEligibility {
  return getReaderEligibilityIndex().byId.get(stableId)?.eligibility ?? "RECORD_ONLY";
}
