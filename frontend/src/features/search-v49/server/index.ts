import { SEARCH_UNICODE_VERSION, supportsSearchUnicode16 } from "@/features/search-v49/unicode16";
import "server-only";

import { createHash } from "node:crypto";
import documentsPayloadJson from "../../../../generated/search-v49/documents.json";
import manifestJson from "../../../../generated/search-v49/manifest.json";
import { hydrateSearchDocument, INDEX_FORMAT_VERSION, SEARCH_ALGORITHM_VERSION, type SearchDocument, type SearchDocumentTuple } from "../core";

type DocumentsPayload = {
  format: string;
  release_id: string;
  search_algorithm_version: string;
  schema: readonly string[];
  documents: readonly SearchDocumentTuple[];
};

export type SearchIndexManifest = {
  format: string;
  release_id: string;
  release_manifest_sha256: string;
  release_projection_sha256: string;
  canonical_input_sha256: string;
  search_algorithm_version: string;
  index_format_version: string;
  document_count: number;
  held_document_count: number;
  generated_at: string;
  source_sha: string;
  source_tree_hash: string;
  source_field_policy_hash: string;
  unicode_version: string;
  normalization_version: string;
  index_sha256: string;
  index_bytes: number;
  index_gzip_bytes: number;
  document_order: string;
  public_fields: readonly string[];
  runtime_bounds: {
    max_query_code_points: number;
    max_query_tokens: number;
    max_page_size: number;
    max_document_title_code_points: number;
    max_document_tokens: number;
    max_document_token_code_points: number;
    max_edit_distance: number;
  };
};

export interface SearchIndex {
  manifest: SearchIndexManifest;
  documents: readonly SearchDocument[];
  byId: ReadonlyMap<string, SearchDocument>;
}

let cached: SearchIndex | null = null;

export function getSearchIndex(): SearchIndex {
  if (cached) return cached;
  const payload = documentsPayloadJson as unknown as DocumentsPayload;
  const manifest = manifestJson as SearchIndexManifest;
  const serialized = `${JSON.stringify(payload)}\n`;
  const sha = createHash("sha256").update(serialized).digest("hex");
  const valid = payload.format === INDEX_FORMAT_VERSION
    && payload.search_algorithm_version === SEARCH_ALGORITHM_VERSION
    && payload.release_id === manifest.release_id
    && manifest.index_format_version === INDEX_FORMAT_VERSION
    && manifest.search_algorithm_version === SEARCH_ALGORITHM_VERSION
    && manifest.document_count === 7995
    && manifest.held_document_count === 7928
    && payload.documents.length === manifest.document_count
    && manifest.index_sha256 === sha
    && manifest.index_bytes === Buffer.byteLength(serialized)
    && manifest.unicode_version === SEARCH_UNICODE_VERSION && supportsSearchUnicode16()
    && manifest.public_fields.join("\u0000") === "stableId\u0000title"
    && manifest.runtime_bounds.max_query_code_points === 160
    && manifest.runtime_bounds.max_query_tokens === 24
    && manifest.runtime_bounds.max_page_size === 100
    && manifest.runtime_bounds.max_document_title_code_points === 1024
    && manifest.runtime_bounds.max_document_tokens === 128
    && manifest.runtime_bounds.max_document_token_code_points === 64
    && manifest.runtime_bounds.max_edit_distance === 2;
  if (!valid) throw new Error("v49 search artifact failed its release, checksum, count, Unicode, or field-policy gate");
  const documents = payload.documents.map(hydrateSearchDocument);
  const byId = new Map(documents.map((document) => [document.stableId, document]));
  if (byId.size !== documents.length) throw new Error("v49 search artifact contains duplicate stable IDs");
  cached = { manifest, documents, byId };
  return cached;
}
