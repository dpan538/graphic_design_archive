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
type CurrentReleaseRow = { research_release_id: string | null; research_manifest_sha256: string | null };
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
  async listFolders(input: FolderQuery & PageRequest): Promise<RepoResult<Page<FolderSummary>>> { return pageByKey([], (item: FolderSummary) => item.id, this.version, input, "folders", input.type ?? "", "title"); }
  async getFolder(): Promise<RepoResult<FolderDetail>> { return notFound("folder projections are unavailable for this exact release"); }
  async listFolderMembers(): Promise<RepoResult<Page<SurfaceSummary>>> { return notFound("folder is not part of this sealed release"); }
  async getSurface(surfaceId: string, options?: ReadOptions): Promise<RepoResult<SurfaceDetail>> {
    const rows = await this.rows<SurfaceRow>("SELECT surface_id, title, publication_layer, object_urn FROM api_v1.sealed_surface WHERE research_release_id = $1 AND research_manifest_sha256 = $2 AND surface_id = $3", [this.version.research.researchReleaseId, this.version.research.researchManifestSha256, surfaceId], options);
    const row = rows.rows[0]; if (!row) return notFound("surface not found in exact sealed release");
    return this.success({ ...surface(row), citation: null, folderIds: [], description: null });
  }
  async search(input: ArchiveSearchQuery & PageRequest, options?: ReadOptions): Promise<RepoResult<Page<SearchHit>>> {
    const first = requireFirst<Page<SearchHit>>(input); if (typeof first !== "number") return first;
    const q = input.q.trim();
    if (!q || q.length > 120) return { ok: false, error: { code: "INVALID_ARGUMENT", message: "q must be a non-empty query of at most 120 characters", retryable: false } };
    const scope = input.scope ?? "all";
    if (!["archive", "trace", "relation", "all"].includes(scope)) return { ok: false, error: { code: "INVALID_ARGUMENT", message: "scope must be archive, trace, relation, or all", retryable: false } };
    const filter = JSON.stringify({ q: q.toLowerCase(), scope });
    const keyFor = (hit: SearchHit) => `${hit.surface.title}\u0000${hit.surface.surfaceId}`;
    if (scope === "trace" || scope === "relation") return pageByKey([], keyFor, this.version, input, "search", filter, "title");
    const rows = await this.rows<SurfaceRow>("SELECT surface_id, title, publication_layer, object_urn FROM api_v1.sealed_surface WHERE research_release_id = $1 AND research_manifest_sha256 = $2 AND strpos(lower(coalesce(title, '')), lower($3)) > 0 ORDER BY surface_id", [this.version.research.researchReleaseId, this.version.research.researchManifestSha256, q], options);
    const hits = rows.rows.map((row) => ({ kind: "archive" as const, route: `/surfaces/${encodeURIComponent(row.surface_id)}`, highlight: row.title ?? row.surface_id, surface: surface(row) }));
    return pageByKey(hits, keyFor, this.version, input, "search", filter, "title");
  }
  async getTraceAtlas(): Promise<RepoResult<TraceAtlas>> { return this.success({ namedUnits: [], totalExact: 0, message: "This release has no verified TRACE evidence." }); }
  async listTraceObjects(input: TraceObjectQuery & PageRequest): Promise<RepoResult<Page<TraceObjectSummary>>> { return pageByKey([], (item: TraceObjectSummary) => item.objectId, this.version, input, "trace-objects", input.layer ?? "active", "id"); }
  async getTraceNeighborhood(): Promise<RepoResult<TraceGraph>> { return notFound("object has no verified TRACE neighborhood in this release"); }
  async listRelationTypes(): Promise<RepoResult<readonly RelationTypeDefinition[]>> { return this.success([]); }
  async getRelationType(): Promise<RepoResult<RelationTypeDefinition>> { return notFound("relation type is not published in this sealed release"); }
  async getRelation(): Promise<RepoResult<SemanticRelation>> { return notFound("relation is not published in this sealed release"); }
  async getClaim(): Promise<RepoResult<ResearchClaim>> { return notFound("claim is not published in this sealed release"); }
  async getCorpus(): Promise<RepoResult<ResearchCorpus>> { return notFound("corpus is not published in this sealed release"); }
}

export class PostgresArchiveRepositoryProvider implements ArchiveRepositoryProvider {
  constructor(private readonly reader: PostgresReader) {}
  async open(input: { research: ResearchReleaseSelector; visual?: VisualRegistrySelector | null }, options?: ReadOptions): Promise<RepoResult<ArchiveRepository>> {
    if (input.visual) return { ok: false, error: { code: "RELEASE_VERSION_MISMATCH", message: "visual selection is not available in the Phase 2C core projection", retryable: false } };
    let pair: Exclude<ResearchReleaseSelector, { alias: "current" }>;
    if ("alias" in input.research) {
      const current = await this.reader.query<CurrentReleaseRow>("SELECT research_release_id, research_manifest_sha256 FROM api_v1.current_version_status WHERE channel = $1", ["public"], options?.signal);
      const row = current.rows[0];
      if (!row?.research_release_id || !row.research_manifest_sha256) return notFound("current sealed research release was not found");
      pair = { researchReleaseId: row.research_release_id, researchManifestSha256: row.research_manifest_sha256 };
    } else pair = input.research;
    const rows = await this.reader.query<DescriptorRow>("SELECT research_release_id, research_manifest_sha256, schema_version FROM api_v1.sealed_research_release_descriptor WHERE research_release_id = $1 AND research_manifest_sha256 = $2", [pair.researchReleaseId, pair.researchManifestSha256], options?.signal);
    const row = rows.rows[0]; if (!row) return { ok: false, error: { code: "RELEASE_NOT_FOUND", message: "sealed exact release pair was not found", retryable: false } };
    const version: ArchiveVersionRef = { research: { apiVersion: "v1", researchReleaseId: row.research_release_id, researchManifestSha256: row.research_manifest_sha256, schemaVersion: "archive-research-release/v1" }, ...noVisual };
    return { ok: true, data: new PostgresArchiveRepository(version, this.reader), version };
  }
}
