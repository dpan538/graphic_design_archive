import "server-only";

import { createHash } from "node:crypto";
import projectionJson from "../../../generated/source-viewer-v49/source-viewer.json";
import manifestJson from "../../../generated/source-viewer-v49/manifest.json";
import { getPublicSearchIndex } from "@/features/search-v2/index.server";

/* The source-viewer projection: every public record's source record URL,
   verified against the Search v2 projection it sits on (§3d step 1). */

export type SourceViewer = { sourceUrl: string | null; sourceDocumentUrl: string | null; accessDate: string | null; sourceUrlReviewed: boolean };

type Payload = { format: string; release_id: string; entries: readonly (readonly [string, string | null, string | null, string | null, 0 | 1])[] };
type Manifest = { release_id: string; canonical_input_sha256: string; search_index_sha256: string; counts: { public: number }; projection_sha256: string; projection_bytes: number };

let cached: ReadonlyMap<string, SourceViewer> | null = null;

export function getSourceViewerIndex(): ReadonlyMap<string, SourceViewer> {
  if (cached) return cached;
  const payload = projectionJson as unknown as Payload;
  const manifest = manifestJson as unknown as Manifest;
  const search = getPublicSearchIndex();
  const serialized = `${JSON.stringify(payload)}\n`;
  const valid =
    payload.format === "gda-source-viewer-v1" &&
    payload.release_id === manifest.release_id &&
    manifest.release_id === search.manifest.release_id &&
    manifest.canonical_input_sha256 === search.manifest.canonical_input_sha256 &&
    manifest.search_index_sha256 === search.manifest.index_sha256 &&
    payload.entries.length === manifest.counts.public &&
    manifest.counts.public === search.manifest.document_count &&
    manifest.projection_sha256 === createHash("sha256").update(serialized).digest("hex") &&
    manifest.projection_bytes === Buffer.byteLength(serialized);
  if (!valid) throw new Error("source-viewer projection failed its release, checksum or count gate");
  cached = new Map(payload.entries.map(([id, sourceUrl, sourceDocumentUrl, accessDate, reviewed]) => [id, { sourceUrl, sourceDocumentUrl, accessDate, sourceUrlReviewed: reviewed === 1 }] as const));
  return cached;
}

export function sourceViewerOf(stableId: string): SourceViewer {
  return getSourceViewerIndex().get(stableId) ?? { sourceUrl: null, sourceDocumentUrl: null, accessDate: null, sourceUrlReviewed: false };
}
