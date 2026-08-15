import "server-only";

import type { ArchiveRepository } from "../repository";
import { keysetPage, resultError } from "../pagination";
import type {
  ArchiveOverview, ArchiveSearchQuery, ArchiveVersionRef, FolderDetail, FolderQuery,
  FolderSummary, FolderTypeSummary, PageRequest, ReadOptions, RelationTypeDefinition,
  RepoResult, ResearchReleaseSelector, SearchHit, SurfaceDetail, SurfaceSummary,
  TraceAtlas, TraceObjectQuery, VisualRegistrySelector,
} from "../types";

export const FIXTURE_RELEASE_ID = "fixture-research-v1";
export const FIXTURE_MANIFEST_SHA256 = "8c9bd8a3d2b1fa60b95cf1278a7315e7af2f7bfe3b3fa7fcb7fc7a64c018497";
export const FIXTURE_CORPUS_VERSION = "fixture-corpus-v1";

const version: ArchiveVersionRef = {
  research: { apiVersion: "v1", researchReleaseId: FIXTURE_RELEASE_ID, researchManifestSha256: FIXTURE_MANIFEST_SHA256, schemaVersion: "archive-research-release/v1" },
  visual: null, visualState: "UNAVAILABLE", visualReasonCodes: ["VISUAL_REGISTRY_UNAVAILABLE", "POSITIVE_VISUAL_RIGHTS_COUNT_ZERO"], takedownOverlaySha256: null,
};

type FixtureSurface = SurfaceDetail & { folderIds: readonly string[] };
const regionNames = ["Africa", "Americas", "Asia", "Europe"] as const;
const fixtureSurfaces: readonly FixtureSurface[] = Array.from({ length: 32 }, (_, index) => {
  const number = index + 1;
  const region = regionNames[index % regionNames.length];
  const surfaceId = `fixture-surface-${String(number).padStart(2, "0")}`;
  return {
    surfaceId, title: `Fixture design record ${String(number).padStart(2, "0")}`,
    creditedLabels: [`Fixture designer ${((index % 8) + 1)}`], displayDate: String(1920 + index), year: 1920 + index,
    placeLabel: region, mediumLabel: index % 2 ? "Print" : "Poster", typeLabel: "Design object",
    sourceLabel: "Synthetic sealed fixture", publicationLayer: "active", deliveryState: "CITATION_ONLY",
    citation: { label: "Synthetic fixture citation", href: "/about" }, folderIds: [`region-${region.toLowerCase()}`],
    description: "A rights-safe miniature sealed-release record for repository and read API verification.",
  };
});
const folders: readonly FolderSummary[] = regionNames.map((region) => ({
  id: `region-${region.toLowerCase()}`, type: "region", slug: region.toLowerCase(), title: region,
  scopeNote: "Fixture region folder", memberCount: fixtureSurfaces.filter((surface) => surface.placeLabel === region).length,
}));

function abort<T>(options?: ReadOptions): RepoResult<T> | null {
  return options?.signal?.aborted ? resultError<T>("UNAVAILABLE", "request was cancelled") : null;
}
function ok<T>(data: T): RepoResult<T> { return { ok: true, data, version }; }
function exactSelector(selector: ResearchReleaseSelector): boolean {
  return "alias" in selector || (selector.researchReleaseId === FIXTURE_RELEASE_ID && selector.researchManifestSha256 === FIXTURE_MANIFEST_SHA256);
}

export class FixtureArchiveRepository implements ArchiveRepository {
  readonly version = version;
  async getOverview(options?: ReadOptions): Promise<RepoResult<ArchiveOverview>> {
    return abort(options) ?? ok({ objectCount: 32, folderCount: folders.length, traceEligibleObjectCount: 0, positiveVisualRightsCount: 0 });
  }
  async listFolderTypes(options?: ReadOptions): Promise<RepoResult<readonly FolderTypeSummary[]>> { return abort(options) ?? ok([{ type: "region", label: "Region", folderCount: folders.length }]); }
  async listFolders(input: FolderQuery & PageRequest, options?: ReadOptions) {
    if (abort(options)) return abort(options)!;
    if (input.type && input.type !== "region") return keysetPage([], (item: FolderSummary) => item.id, version, input, "folders", input.type, "title");
    return keysetPage(folders, (item) => `${item.title}\u0000${item.id}`, version, input, "folders", input.type ?? "", "title");
  }
  async getFolder(ref: { id: string } | { type: string; slug: string }, options?: ReadOptions): Promise<RepoResult<FolderDetail>> {
    if (abort(options)) return abort(options)!;
    const folder = "id" in ref ? folders.find((item) => item.id === ref.id) : folders.find((item) => item.type === ref.type && item.slug === ref.slug);
    return folder ? ok({ ...folder, relatedFolders: [] }) : resultError("NOT_FOUND", "folder is not part of this sealed release");
  }
  async listFolderMembers(folderId: string, page: PageRequest, options?: ReadOptions) {
    if (abort(options)) return abort(options)!;
    if (!folders.some((folder) => folder.id === folderId)) return resultError("NOT_FOUND", "folder is not part of this sealed release");
    const members = fixtureSurfaces.filter((surface) => surface.folderIds.includes(folderId));
    return keysetPage(members, (item) => `${item.title}\u0000${item.surfaceId}`, version, page, "folder-members", folderId, "title");
  }
  async getSurface(surfaceId: string, options?: ReadOptions) { if (abort(options)) return abort(options)!; const surface = fixtureSurfaces.find((item) => item.surfaceId === surfaceId); return surface ? ok(surface) : resultError("NOT_FOUND", "surface is not part of this sealed release"); }
  async search(input: ArchiveSearchQuery & PageRequest, options?: ReadOptions) {
    if (abort(options)) return abort(options)!;
    const query = input.q.trim().toLocaleLowerCase();
    if (!query || query.length > 120) return resultError("INVALID_ARGUMENT", "q must be a non-empty query of at most 120 characters");
    if (input.scope && input.scope !== "archive" && input.scope !== "all") return keysetPage([], (item: SearchHit) => item.surface.surfaceId, version, input, "search", JSON.stringify({ q: query, scope: input.scope }), "title");
    const hits: SearchHit[] = fixtureSurfaces.filter((surface) => [surface.title, ...surface.creditedLabels, surface.placeLabel, surface.mediumLabel].join(" ").toLocaleLowerCase().includes(query)).map((surface) => ({ kind: "archive", route: `/surfaces/${surface.surfaceId}`, highlight: surface.title, surface }));
    return keysetPage(hits, (item) => `${item.surface.title}\u0000${item.surface.surfaceId}`, version, input, "search", JSON.stringify({ q: query, scope: input.scope ?? "all" }), "title");
  }
  async getTraceAtlas(options?: ReadOptions): Promise<RepoResult<TraceAtlas>> { return abort(options) ?? ok({ namedUnits: [{ id: "active-trace-objects", label: "Active TRACE objects", totalExact: 0 }], totalExact: 0, message: "This release has no verified TRACE evidence." }); }
  async listTraceObjects(input: TraceObjectQuery & PageRequest, options?: ReadOptions) { if (abort(options)) return abort(options)!; return keysetPage([], (item) => item.objectId, version, input, "trace-objects", input.layer ?? "active", "id"); }
  async getTraceNeighborhood(_objectId: string, options?: ReadOptions) { return abort(options) ?? resultError("NOT_FOUND", "this release has no TRACE-eligible object for a neighborhood"); }
  async listRelationTypes(options?: ReadOptions): Promise<RepoResult<readonly RelationTypeDefinition[]>> { return abort(options) ?? ok([]); }
  async getRelationType(_id: string, options?: ReadOptions) { return abort(options) ?? resultError("NOT_FOUND", "relation type is not published in this sealed release"); }
  async getRelation(_id: string, options?: ReadOptions) { return abort(options) ?? resultError("NOT_FOUND", "relation is not published in this sealed release"); }
  async getClaim(_id: string, options?: ReadOptions) { return abort(options) ?? resultError("NOT_FOUND", "claim is not published in this sealed release"); }
  async getCorpus(corpusVersion: string, options?: ReadOptions) { return abort(options) ?? (corpusVersion === FIXTURE_CORPUS_VERSION ? ok({ version: FIXTURE_CORPUS_VERSION, totalExact: 32 }) : resultError("NOT_FOUND", "corpus is not part of this sealed release")); }
}

export class FixtureArchiveRepositoryProvider {
  async open(input: { research: ResearchReleaseSelector; visual?: VisualRegistrySelector | null }, options?: ReadOptions): Promise<RepoResult<ArchiveRepository>> {
    if (abort(options)) return abort(options)!;
    if (!exactSelector(input.research)) return resultError("RELEASE_NOT_FOUND", "requested research release is unavailable");
    if (input.visual) return resultError("RELEASE_VERSION_MISMATCH", "the fixture has no compatible visual registry");
    return ok(new FixtureArchiveRepository());
  }
}
