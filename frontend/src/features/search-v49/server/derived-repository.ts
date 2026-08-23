import "server-only";

import type { ArchiveRepository, ArchiveRepositoryProvider } from "@/lib/read-platform/repository";
import { resultError } from "@/lib/read-platform/pagination";
import type {
  ArchiveOverview, ArchiveSearchQuery, ArchiveVersionRef, FolderDetail, FolderQuery,
  FolderSummary, FolderTypeSummary, Page, PageRequest, ReadOptions, RelationTypeDefinition,
  RepoResult, ResearchClaim, ResearchCorpus, ResearchReleaseSelector, SearchHit,
  SemanticRelation, SurfaceDetail, SurfaceSummary, TraceAtlas, TraceGraph,
  TraceObjectQuery, TraceObjectSummary, VisualRegistrySelector,
} from "@/lib/read-platform/types";
import { pageRankedDocuments, parseSearchQuery, rankDocuments, SearchInputError, type SearchDocument } from "../core";
import { getSearchIndex, type SearchIndex } from "./index";

function versionFor(index: SearchIndex): ArchiveVersionRef {
  return {
    research: {
      apiVersion: "v1",
      researchReleaseId: index.manifest.release_id,
      researchManifestSha256: index.manifest.release_manifest_sha256,
      schemaVersion: "archive-research-release/v1",
    },
    visual: null,
    visualState: "UNAVAILABLE",
    visualReasonCodes: ["VISUAL_REGISTRY_UNAVAILABLE", "POSITIVE_VISUAL_RIGHTS_COUNT_ZERO"],
    takedownOverlaySha256: null,
  };
}

function summary(document: SearchDocument): SurfaceSummary {
  return {
    surfaceId: document.stableId,
    title: document.title,
    creditedLabels: [],
    displayDate: "Undated",
    year: null,
    placeLabel: "Unspecified",
    mediumLabel: "Not publicly specified",
    typeLabel: "Archive surface",
    sourceLabel: "Sealed v49 research release",
    publicationLayer: "active",
    deliveryState: "CITATION_ONLY",
  };
}

function abort<T>(options?: ReadOptions): RepoResult<T> | null {
  return options?.signal?.aborted ? resultError<T>("UNAVAILABLE", "request was cancelled") : null;
}

export class DerivedV49ArchiveRepository implements ArchiveRepository {
  readonly version: ArchiveVersionRef;
  constructor(private readonly index: SearchIndex) { this.version = versionFor(index); }
  private ok<T>(data: T): RepoResult<T> { return { ok: true, data, version: this.version }; }

  async getOverview(options?: ReadOptions): Promise<RepoResult<ArchiveOverview>> {
    return abort(options) ?? this.ok({ objectCount: this.index.documents.length, folderCount: 0, traceEligibleObjectCount: 0, positiveVisualRightsCount: 0 });
  }
  async listFolderTypes(options?: ReadOptions): Promise<RepoResult<readonly FolderTypeSummary[]>> { return abort(options) ?? this.ok([]); }
  async listFolders(_input: FolderQuery & PageRequest, options?: ReadOptions): Promise<RepoResult<Page<FolderSummary>>> { return abort(options) ?? this.ok({ nodes: [], pageInfo: { hasNextPage: false, nextCursor: null, totalExact: 0 } }); }
  async getFolder(_ref: { id: string } | { type: string; slug: string }, options?: ReadOptions): Promise<RepoResult<FolderDetail>> { return abort(options) ?? resultError("NOT_FOUND", "folder is not part of the sealed v49 public projection"); }
  async listFolderMembers(_folderId: string, _page: PageRequest, options?: ReadOptions): Promise<RepoResult<Page<SurfaceSummary>>> { return abort(options) ?? resultError("NOT_FOUND", "folder is not part of the sealed v49 public projection"); }
  async getSurface(surfaceId: string, options?: ReadOptions): Promise<RepoResult<SurfaceDetail>> {
    if (abort<SurfaceDetail>(options)) return abort<SurfaceDetail>(options)!;
    const document = this.index.byId.get(surfaceId);
    return document ? this.ok({ ...summary(document), citation: null, folderIds: [], description: null }) : resultError("NOT_FOUND", "surface is not part of the sealed v49 public projection");
  }
  async search(input: ArchiveSearchQuery & PageRequest, options?: ReadOptions): Promise<RepoResult<Page<SearchHit>>> {
    if (abort<Page<SearchHit>>(options)) return abort<Page<SearchHit>>(options)!;
    const scope = input.scope ?? "archive";
    if (!["archive", "trace", "relation", "all"].includes(scope)) return resultError("INVALID_ARGUMENT", "scope must be archive, trace, relation, or all");
    if (input.sort && input.sort !== "relevance") return resultError("INVALID_ARGUMENT", "the v49 fuzzy endpoint supports relevance order only");
    try {
      const query = parseSearchQuery(input.q);
      const ranked = scope === "trace" || scope === "relation" ? [] : rankDocuments(this.index.documents, query);
      const page = pageRankedDocuments({
        ranked, query, after: input.after, first: input.first,
        releaseId: this.index.manifest.release_id,
        manifestSha256: this.index.manifest.release_manifest_sha256,
        indexSha256: this.index.manifest.index_sha256,
        scope,
      });
      return this.ok({
        nodes: page.nodes.map((item) => ({
          kind: "archive" as const,
          route: `/surfaces/${encodeURIComponent(item.document.stableId)}`,
          highlight: item.document.title,
          surface: summary(item.document),
          explanation: item.explanation,
        })),
        pageInfo: page.pageInfo,
        searchMetadata: {
          algorithmVersion: this.index.manifest.search_algorithm_version,
          indexFormatVersion: this.index.manifest.index_format_version,
          indexSha256: this.index.manifest.index_sha256,
        },
      });
    } catch (error) {
      return error instanceof SearchInputError ? resultError(error.code, error.message) : resultError("INTEGRITY_FAILURE", "v49 search ranking failed its deterministic runtime contract");
    }
  }
  async getTraceAtlas(options?: ReadOptions): Promise<RepoResult<TraceAtlas>> { return abort(options) ?? this.ok({ namedUnits: [{ id: "active-trace-objects", label: "Active TRACE objects", totalExact: 0 }], totalExact: 0, message: "This public release has no verified TRACE evidence." }); }
  async listTraceObjects(_input: TraceObjectQuery & PageRequest, options?: ReadOptions): Promise<RepoResult<Page<TraceObjectSummary>>> { return abort(options) ?? this.ok({ nodes: [], pageInfo: { hasNextPage: false, nextCursor: null, totalExact: 0 } }); }
  async getTraceNeighborhood(_objectId: string, options?: ReadOptions): Promise<RepoResult<TraceGraph>> { return abort(options) ?? resultError("NOT_FOUND", "this public release has no TRACE-eligible object"); }
  async listRelationTypes(options?: ReadOptions): Promise<RepoResult<readonly RelationTypeDefinition[]>> { return abort(options) ?? this.ok([]); }
  async getRelationType(_id: string, options?: ReadOptions): Promise<RepoResult<RelationTypeDefinition>> { return abort(options) ?? resultError("NOT_FOUND", "relation type is not published in this public release"); }
  async getRelation(_id: string, options?: ReadOptions): Promise<RepoResult<SemanticRelation>> { return abort(options) ?? resultError("NOT_FOUND", "relation is not published in this public release"); }
  async getClaim(_id: string, options?: ReadOptions): Promise<RepoResult<ResearchClaim>> { return abort(options) ?? resultError("NOT_FOUND", "claim is not published in this public release"); }
  async getCorpus(_corpusVersion: string, options?: ReadOptions): Promise<RepoResult<ResearchCorpus>> { return abort(options) ?? resultError("NOT_FOUND", "corpus is not published in this public release"); }
}

export class DerivedV49ArchiveRepositoryProvider implements ArchiveRepositoryProvider {
  async open(input: { research: ResearchReleaseSelector; visual?: VisualRegistrySelector | null }, options?: ReadOptions): Promise<RepoResult<ArchiveRepository>> {
    if (abort<ArchiveRepository>(options)) return abort<ArchiveRepository>(options)!;
    if (input.visual) return resultError("RELEASE_VERSION_MISMATCH", "v49 has no compatible visual registry");
    let index: SearchIndex;
    try { index = getSearchIndex(); } catch { return resultError("INTEGRITY_FAILURE", "v49 derived search artifact failed validation"); }
    const exact = "alias" in input.research || (
      input.research.researchReleaseId === index.manifest.release_id
      && input.research.researchManifestSha256 === index.manifest.release_manifest_sha256
    );
    if (!exact) return resultError("RELEASE_NOT_FOUND", "requested exact research release pair is unavailable");
    const repository = new DerivedV49ArchiveRepository(index);
    return { ok: true, data: repository, version: repository.version };
  }
}
