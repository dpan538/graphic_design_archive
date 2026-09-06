import { SEARCH_UNICODE_VERSION, supportsSearchUnicode16 } from "@/features/search-v49/unicode16";
import "server-only";

import { createHash } from "node:crypto";
import documentsJson from "../../../generated/search-v2/documents.json";
import facetsJson from "../../../generated/search-v2/facets.json";
import manifestJson from "../../../generated/search-v2/manifest.json";
import {
  hydratePublicSearchDocument,
  PUBLIC_SEARCH_ALGORITHM_VERSION,
  PUBLIC_SEARCH_INDEX_FORMAT_VERSION,
  type PublicSearchDocument,
  type PublicSearchDocumentTuple,
} from "./core";

type DocumentsPayload = {
  format: string;
  release_id: string;
  search_algorithm_version: string;
  schema: readonly string[];
  documents: readonly PublicSearchDocumentTuple[];
};

export type PublicSearchFacetValue = { value: string; count: number };
export type PublicSearchFacets = {
  format: string;
  release_id: string;
  year: { min: number; max: number };
  object_types: readonly PublicSearchFacetValue[];
  themes: readonly PublicSearchFacetValue[];
  movements: readonly PublicSearchFacetValue[];
  starter_queries: readonly {
    id: string;
    label: string;
    query: string;
    filters: Readonly<Record<string, string | number>>;
  }[];
};

export type PublicSearchIndexManifest = {
  format: string;
  release_id: string;
  release_manifest_sha256: string;
  canonical_input_sha256: string;
  search_algorithm_version: string;
  index_format_version: string;
  document_count: number;
  source_held_record_count: number;
  held_document_count: number;
  trace_record_count: number;
  open_inquiry_record_count: number;
  generated_at: string;
  source_field_policy_hash: string;
  unicode_version: string;
  normalization_version: string;
  index_sha256: string;
  index_bytes: number;
  facets_sha256: string;
  facets_bytes: number;
  public_fields: readonly string[];
  searchable_fields: readonly string[];
  filterable_fields: readonly string[];
};

export type PublicSearchIndex = {
  manifest: PublicSearchIndexManifest;
  facets: PublicSearchFacets;
  documents: readonly PublicSearchDocument[];
  byId: ReadonlyMap<string, PublicSearchDocument>;
};

let cached: PublicSearchIndex | null = null;
const sha256 = (value: string) => createHash("sha256").update(value).digest("hex");

export function getPublicSearchIndex(): PublicSearchIndex {
  if (cached) return cached;
  const payload = documentsJson as unknown as DocumentsPayload;
  const facets = facetsJson as unknown as PublicSearchFacets;
  const manifest = manifestJson as PublicSearchIndexManifest;
  const serializedDocuments = `${JSON.stringify(payload)}\n`;
  const serializedFacets = `${JSON.stringify(facets)}\n`;
  const valid = payload.format === PUBLIC_SEARCH_INDEX_FORMAT_VERSION
    && payload.release_id === manifest.release_id
    && facets.release_id === manifest.release_id
    && payload.search_algorithm_version === PUBLIC_SEARCH_ALGORITHM_VERSION
    && manifest.search_algorithm_version === PUBLIC_SEARCH_ALGORITHM_VERSION
    && manifest.index_format_version === PUBLIC_SEARCH_INDEX_FORMAT_VERSION
    && manifest.document_count === 7995
    && manifest.source_held_record_count === 7928
    && manifest.held_document_count === 0
    && manifest.trace_record_count === 0
    && manifest.open_inquiry_record_count === 0
    && payload.documents.length === manifest.document_count
    && manifest.index_sha256 === sha256(serializedDocuments)
    && manifest.index_bytes === Buffer.byteLength(serializedDocuments)
    && manifest.facets_sha256 === sha256(serializedFacets)
    && manifest.facets_bytes === Buffer.byteLength(serializedFacets)
    && manifest.unicode_version === SEARCH_UNICODE_VERSION && supportsSearchUnicode16()
    && manifest.searchable_fields.join("\u0000") === "stable_id\u0000title\u0000credited_label\u0000place"
    && manifest.filterable_fields.join("\u0000") === "year_range\u0000object_type\u0000theme\u0000movement";
  if (!valid) throw new Error("public Search v2 artifact failed its release, checksum, count, Unicode, or field-policy gate");
  const documents = payload.documents.map(hydratePublicSearchDocument);
  const byId = new Map(documents.map((document) => [document.stableId, document]));
  if (byId.size !== documents.length) throw new Error("public Search v2 artifact contains duplicate stable IDs");
  cached = { manifest, facets, documents, byId };
  return cached;
}
