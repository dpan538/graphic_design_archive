import type { ArchiveRepository, ArchiveRepositoryProvider } from "./repository";
import type {
  ArchiveOverview, ArchiveSearchQuery, ArchiveVersionRef, FolderDetail, FolderQuery, FolderSummary,
  FolderTypeSummary, Page, PageRequest, ReadOptions, RelationTypeDefinition, RepoResult,
  ResearchClaim, ResearchCorpus, ResearchReleaseSelector, SearchHit, SemanticRelation,
  SurfaceDetail, SurfaceSummary, TraceAtlas, TraceGraph, TraceObjectQuery, TraceObjectSummary,
  VisualRegistrySelector, RepositoryErrorCode,
} from "./types";

type Envelope<T> = { apiVersion: "v1"; researchReleaseId: string; researchManifestSha256: string; visualRegistryVersion: string | null; visualRegistrySha256: string | null; visualRegistryState: ArchiveVersionRef["visualState"]; visualReasonCodes: string[]; takedownOverlaySha256: string | null; data: T };
type Problem = { code?: string; detail?: string; title?: string };
const errorCode = (value: unknown): RepositoryErrorCode => typeof value === "string" && ["INVALID_ARGUMENT", "INVALID_CURSOR", "NOT_FOUND", "RELEASE_NOT_FOUND", "VISUAL_REGISTRY_NOT_FOUND", "RELEASE_VERSION_MISMATCH", "INTEGRITY_FAILURE", "UNREGISTERED_RELATION", "UNAVAILABLE"].includes(value) ? value as RepositoryErrorCode : "UNAVAILABLE";

function selectorPath(selector: ResearchReleaseSelector): string { return "alias" in selector ? "/api/v1/releases/current" : `/api/v1/releases/${encodeURIComponent(selector.researchReleaseId)}`; }
function signalError<T>(): RepoResult<T> { return { ok: false, error: { code: "UNAVAILABLE", message: "request was cancelled", retryable: true } }; }

export class HttpArchiveRepository implements ArchiveRepository {
  constructor(readonly version: ArchiveVersionRef, private readonly baseUrl = "") {}
  private releasePath() { return `/api/v1/releases/${encodeURIComponent(this.version.research.researchReleaseId)}`; }
  private async request<T>(path: string, options?: ReadOptions): Promise<RepoResult<T>> {
    if (options?.signal?.aborted) return signalError();
    const response = await fetch(`${this.baseUrl}${path}`, { signal: options?.signal, headers: { "Archive-Research-Manifest-Sha256": this.version.research.researchManifestSha256 } }).catch(() => null);
    if (!response) return { ok: false, error: { code: "UNAVAILABLE", message: "read API is unavailable", retryable: true } };
    if (!response.ok) { const problem = (await response.json().catch(() => ({}))) as Problem; return { ok: false, error: { code: errorCode(problem.code), message: problem.detail ?? problem.title ?? "read API request failed", retryable: response.status >= 500 } }; }
    const envelope = (await response.json()) as Envelope<T>;
    if (envelope.apiVersion !== "v1" || envelope.researchReleaseId !== this.version.research.researchReleaseId || envelope.researchManifestSha256 !== this.version.research.researchManifestSha256) return { ok: false, error: { code: "INTEGRITY_FAILURE", message: "response exact release pair does not match request", retryable: false } };
    return { ok: true, data: envelope.data, version: this.version };
  }
  getOverview(o?: ReadOptions) { return this.request<ArchiveOverview>(`${this.releasePath()}/archive/overview`, o); }
  listFolderTypes(o?: ReadOptions) { return this.request<readonly FolderTypeSummary[]>(`${this.releasePath()}/folder-types`, o); }
  listFolders(input: FolderQuery & PageRequest, o?: ReadOptions) { return this.request<Page<FolderSummary>>(`${this.releasePath()}/folders?${new URLSearchParams(clean(input))}`, o); }
  getFolder(ref: { id: string } | { type: string; slug: string }, o?: ReadOptions) { const id = "id" in ref ? ref.id : `${ref.type}/${ref.slug}`; return this.request<FolderDetail>(`${this.releasePath()}/folders/${encodeURIComponent(id)}`, o); }
  listFolderMembers(folderId: string, page: PageRequest, o?: ReadOptions) { return this.request<Page<SurfaceSummary>>(`${this.releasePath()}/folders/${encodeURIComponent(folderId)}/surfaces?${new URLSearchParams(clean(page))}`, o); }
  getSurface(surfaceId: string, o?: ReadOptions) { return this.request<SurfaceDetail>(`${this.releasePath()}/surfaces/${encodeURIComponent(surfaceId)}`, o); }
  search(input: ArchiveSearchQuery & PageRequest, o?: ReadOptions) { return this.request<Page<SearchHit>>(`${this.releasePath()}/search?${new URLSearchParams(clean(input))}`, o); }
  getTraceAtlas(o?: ReadOptions) { return this.request<TraceAtlas>(`${this.releasePath()}/trace/atlas`, o); }
  listTraceObjects(input: TraceObjectQuery & PageRequest, o?: ReadOptions) { return this.request<Page<TraceObjectSummary>>(`${this.releasePath()}/trace/objects?${new URLSearchParams(clean(input))}`, o); }
  getTraceNeighborhood(id: string, o?: ReadOptions) { return this.request<TraceGraph>(`${this.releasePath()}/trace/objects/${encodeURIComponent(id)}/neighborhood`, o); }
  listRelationTypes(o?: ReadOptions) { return this.request<readonly RelationTypeDefinition[]>(`${this.releasePath()}/trace/relation-types`, o); }
  getRelationType(id: string, o?: ReadOptions) { return this.request<RelationTypeDefinition>(`${this.releasePath()}/trace/relation-types/${encodeURIComponent(id)}`, o); }
  getRelation(id: string, o?: ReadOptions) { return this.request<SemanticRelation>(`${this.releasePath()}/relations/${encodeURIComponent(id)}`, o); }
  getClaim(id: string, o?: ReadOptions) { return this.request<ResearchClaim>(`${this.releasePath()}/claims/${encodeURIComponent(id)}`, o); }
  getCorpus(id: string, o?: ReadOptions) { return this.request<ResearchCorpus>(`${this.releasePath()}/corpora/${encodeURIComponent(id)}`, o); }
}
function clean(input: object) { return Object.fromEntries(Object.entries(input).filter(([, value]) => value !== undefined).map(([key, value]) => [key, String(value)])); }

export class HttpArchiveRepositoryProvider implements ArchiveRepositoryProvider {
  constructor(private readonly baseUrl = "") {}
  async open(input: { research: ResearchReleaseSelector; visual?: VisualRegistrySelector | null }, options?: ReadOptions): Promise<RepoResult<ArchiveRepository>> {
    if (input.visual) return { ok: false, error: { code: "RELEASE_VERSION_MISMATCH", message: "visual selector transport is not implemented in this core client", retryable: false } };
    const headers = "alias" in input.research ? undefined : { "Archive-Research-Manifest-Sha256": input.research.researchManifestSha256 };
    const descriptor = await fetch(`${this.baseUrl}${selectorPath(input.research)}`, { signal: options?.signal, headers }).catch(() => null);
    if (!descriptor?.ok) return { ok: false, error: { code: "UNAVAILABLE", message: "release descriptor is unavailable", retryable: true } };
    const body = await descriptor.json() as Envelope<{ schemaVersion?: "archive-research-release/v1" }>;
    const version: ArchiveVersionRef = { research: { apiVersion: "v1", researchReleaseId: body.researchReleaseId, researchManifestSha256: body.researchManifestSha256, schemaVersion: body.data.schemaVersion ?? "archive-research-release/v1" }, visual: null, visualState: body.visualRegistryState, visualReasonCodes: body.visualReasonCodes, takedownOverlaySha256: body.takedownOverlaySha256 };
    return { ok: true, data: new HttpArchiveRepository(version, this.baseUrl), version };
  }
}
