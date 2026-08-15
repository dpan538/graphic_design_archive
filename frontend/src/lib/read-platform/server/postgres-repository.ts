import "server-only";

import type { ArchiveRepository, ArchiveRepositoryProvider } from "../repository";
import type {
  ArchiveOverview, ArchiveSearchQuery, ArchiveVersionRef, FolderDetail, FolderQuery,
  FolderSummary, FolderTypeSummary, Page, PageRequest, ReadOptions, RelationTypeDefinition,
  RepoResult, ResearchClaim, ResearchCorpus, ResearchReleaseSelector, SearchHit,
  SemanticRelation, SurfaceDetail, SurfaceSummary, TraceAtlas, TraceGraph,
  TraceObjectQuery, TraceObjectSummary, VisualRegistrySelector,
} from "../types";
import { pageByKey, requireFirst } from "../pagination";

/** The application owns no database pool.  Its host injects a reader-only
 * parameterised executor; this keeps `pg` and any database URL out of client bundles. */
export interface PostgresReader {
  query<T extends Record<string, unknown>>(sql: string, values: readonly unknown[], signal?: AbortSignal): Promise<{ rows: readonly T[] }>;
}

type DescriptorRow = { research_release_id: string; research_manifest_sha256: string; schema_version: string; object_count: number; trace_eligible_object_count: number };
type SurfaceRow = { surface_id: string; title: string | null; publication_layer: "active"; object_urn: string };
const noVisual = { visual: null, visualState: "UNAVAILABLE" as const, visualReasonCodes: ["VISUAL_REGISTRY_NOT_SELECTED"], takedownOverlaySha256: null };
function unavailable<T>(message: string): RepoResult<T> { return { ok: false, error: { code: "UNAVAILABLE", message, retryable: false } }; }
function notFound<T>(message: string): RepoResult<T> { return { ok: false, error: { code: "NOT_FOUND", message, retryable: false } }; }
function surface(row: SurfaceRow): SurfaceSummary { return { surfaceId: row.surface_id, title: row.title ?? row.surface_id, creditedLabels: [], displayDate: "Undated", year: null, placeLabel: "Unspecified", mediumLabel: "Not publicly specified", typeLabel: "Archive surface", sourceLabel: "Sealed research release", publicationLayer: "active", deliveryState: "CITATION_ONLY" }; }

export class PostgresArchiveRepository implements ArchiveRepository {
  constructor(readonly version: ArchiveVersionRef, private readonly reader: PostgresReader) {}
  private async rows<T extends Record<string, unknown>>(sql: string, values: readonly unknown[], options?: ReadOptions) { return this.reader.query<T>(sql, values, options?.signal); }
  private success<T>(data: T): RepoResult<T> { return { ok: true, data, version: this.version }; }
  async getOverview(options?: ReadOptions): Promise<RepoResult<ArchiveOverview>> {
    const rows = await this.rows<DescriptorRow>("SELECT object_count, trace_eligible_object_count FROM api_v1.sealed_research_release_descriptor WHERE research_release_id = $1 AND research_manifest_sha256 = $2", [this.version.research.researchReleaseId, this.version.research.researchManifestSha256], options);
    const row = rows.rows[0]; if (!row) return notFound("sealed exact release was not found");
    return this.success({ objectCount: Number(row.object_count), folderCount: 0, traceEligibleObjectCount: Number(row.trace_eligible_object_count), positiveVisualRightsCount: 0 });
  }
  async listFolderTypes(): Promise<RepoResult<readonly FolderTypeSummary[]>> { return this.success([]); }
  async listFolders(_input: FolderQuery & PageRequest): Promise<RepoResult<Page<FolderSummary>>> { return this.success({ nodes: [], pageInfo: { hasNextPage: false, nextCursor: null, totalExact: 0 } }); }
  async getFolder(): Promise<RepoResult<FolderDetail>> { return notFound("folder projections are unavailable for this exact release"); }
  async listFolderMembers(): Promise<RepoResult<Page<SurfaceSummary>>> { return this.success({ nodes: [], pageInfo: { hasNextPage: false, nextCursor: null, totalExact: 0 } }); }
  async getSurface(surfaceId: string, options?: ReadOptions): Promise<RepoResult<SurfaceDetail>> {
    const rows = await this.rows<SurfaceRow>("SELECT surface_id, title, publication_layer, object_urn FROM api_v1.sealed_surface WHERE research_release_id = $1 AND research_manifest_sha256 = $2 AND surface_id = $3", [this.version.research.researchReleaseId, this.version.research.researchManifestSha256, surfaceId], options);
    const row = rows.rows[0]; if (!row) return notFound("surface not found in exact sealed release");
    return this.success({ ...surface(row), citation: null, folderIds: [], description: null });
  }
  async search(input: ArchiveSearchQuery & PageRequest, options?: ReadOptions): Promise<RepoResult<Page<SearchHit>>> {
    const first = requireFirst<Page<SearchHit>>(input); if (typeof first !== "number") return first;
    const q = input.q.trim(); if (!q) return unavailable("search query is required");
    const rows = await this.rows<SurfaceRow>("SELECT surface_id, title, publication_layer, object_urn FROM api_v1.sealed_surface WHERE research_release_id = $1 AND research_manifest_sha256 = $2 AND lower(coalesce(title, '')) LIKE lower($3) ORDER BY surface_id LIMIT $4", [this.version.research.researchReleaseId, this.version.research.researchManifestSha256, `%${q}%`, first + 1], options);
    const page = pageByKey(rows.rows.map((row) => ({ kind: "archive" as const, route: `/surfaces/${encodeURIComponent(row.surface_id)}`, highlight: row.title ?? row.surface_id, surface: surface(row) })), first, (hit) => hit.surface.surfaceId, { releaseId: this.version.research.researchReleaseId, manifest: this.version.research.researchManifestSha256, resource: "search", filter: q, sort: "surfaceId" });
    return this.success(page);
  }
  async getTraceAtlas(): Promise<RepoResult<TraceAtlas>> { return this.success({ namedUnits: [], totalExact: 0, message: "This release has no verified TRACE evidence." }); }
  async listTraceObjects(): Promise<RepoResult<Page<TraceObjectSummary>>> { return this.success({ nodes: [], pageInfo: { hasNextPage: false, nextCursor: null, totalExact: 0 } }); }
  async getTraceNeighborhood(): Promise<RepoResult<TraceGraph>> { return notFound("object has no verified TRACE neighborhood in this release"); }
  async listRelationTypes(): Promise<RepoResult<readonly RelationTypeDefinition[]>> { return this.success([]); }
  async getRelationType(): Promise<RepoResult<RelationTypeDefinition>> { return unavailable("relation registry is not available in this core projection"); }
  async getRelation(): Promise<RepoResult<SemanticRelation>> { return unavailable("relation projection is not available in this core projection"); }
  async getClaim(): Promise<RepoResult<ResearchClaim>> { return unavailable("claim projection is not available in this core projection"); }
  async getCorpus(): Promise<RepoResult<ResearchCorpus>> { return unavailable("corpus projection is not available in this core projection"); }
}

export class PostgresArchiveRepositoryProvider implements ArchiveRepositoryProvider {
  constructor(private readonly reader: PostgresReader) {}
  async open(input: { research: ResearchReleaseSelector; visual?: VisualRegistrySelector | null }, options?: ReadOptions): Promise<RepoResult<ArchiveRepository>> {
    if ("alias" in input.research) return unavailable("Postgres provider requires an exact research release pair");
    if (input.visual) return { ok: false, error: { code: "RELEASE_VERSION_MISMATCH", message: "visual selection is not available in the Phase 2C core projection", retryable: false } };
    const pair = input.research;
    const rows = await this.reader.query<DescriptorRow>("SELECT research_release_id, research_manifest_sha256, schema_version FROM api_v1.sealed_research_release_descriptor WHERE research_release_id = $1 AND research_manifest_sha256 = $2", [pair.researchReleaseId, pair.researchManifestSha256], options?.signal);
    const row = rows.rows[0]; if (!row) return { ok: false, error: { code: "RELEASE_NOT_FOUND", message: "sealed exact release pair was not found", retryable: false } };
    const version: ArchiveVersionRef = { research: { apiVersion: "v1", researchReleaseId: row.research_release_id, researchManifestSha256: row.research_manifest_sha256, schemaVersion: "archive-research-release/v1" }, ...noVisual };
    return { ok: true, data: new PostgresArchiveRepository(version, this.reader), version };
  }
}
