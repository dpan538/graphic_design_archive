import type {
  ArchiveOverview, ArchiveSearchQuery, ArchiveVersionRef, FolderDetail, FolderQuery,
  FolderSummary, FolderTypeSummary, Page, PageRequest, ReadOptions, RelationTypeDefinition,
  RepoResult, ResearchClaim, ResearchCorpus, ResearchReleaseSelector, SearchHit,
  SemanticRelation, SurfaceDetail, SurfaceSummary, TraceAtlas, TraceGraph,
  TraceObjectQuery, TraceObjectSummary, VisualRegistrySelector,
} from "./types";
import type { PublicContextDataset } from "@/features/trace-v49/context/governed/types";

export interface ArchiveRepository {
  readonly version: ArchiveVersionRef;
  getOverview(options?: ReadOptions): Promise<RepoResult<ArchiveOverview>>;
  listFolderTypes(options?: ReadOptions): Promise<RepoResult<readonly FolderTypeSummary[]>>;
  listFolders(input: FolderQuery & PageRequest, options?: ReadOptions): Promise<RepoResult<Page<FolderSummary>>>;
  getFolder(ref: { id: string } | { type: string; slug: string }, options?: ReadOptions): Promise<RepoResult<FolderDetail>>;
  listFolderMembers(folderId: string, page: PageRequest, options?: ReadOptions): Promise<RepoResult<Page<SurfaceSummary>>>;
  getSurface(surfaceId: string, options?: ReadOptions): Promise<RepoResult<SurfaceDetail>>;
  search(input: ArchiveSearchQuery & PageRequest, options?: ReadOptions): Promise<RepoResult<Page<SearchHit>>>;
  getTraceAtlas(options?: ReadOptions): Promise<RepoResult<TraceAtlas>>;
  listTraceObjects(input: TraceObjectQuery & PageRequest, options?: ReadOptions): Promise<RepoResult<Page<TraceObjectSummary>>>;
  getTraceNeighborhood(objectId: string, options?: ReadOptions): Promise<RepoResult<TraceGraph>>;
  getTraceContext?(objectId: string, options?: ReadOptions): Promise<RepoResult<PublicContextDataset>>;
  listRelationTypes(options?: ReadOptions): Promise<RepoResult<readonly RelationTypeDefinition[]>>;
  getRelationType(id: string, options?: ReadOptions): Promise<RepoResult<RelationTypeDefinition>>;
  getRelation(relationId: string, options?: ReadOptions): Promise<RepoResult<SemanticRelation>>;
  getClaim(claimId: string, options?: ReadOptions): Promise<RepoResult<ResearchClaim>>;
  getCorpus(corpusVersion: string, options?: ReadOptions): Promise<RepoResult<ResearchCorpus>>;
}

export interface ArchiveRepositoryProvider {
  open(input: { research: ResearchReleaseSelector; visual?: VisualRegistrySelector | null }, options?: ReadOptions): Promise<RepoResult<ArchiveRepository>>;
}
