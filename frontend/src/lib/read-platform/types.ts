export const API_VERSION = "v1" as const;

export type DeliveryState = "BLOCKED" | "CITATION_ONLY" | "LINK_ONLY" | "SOURCE_VIEWER" | "REMOTE_IMAGE";
export type VisualState = "NOT_SELECTED" | "UNAVAILABLE" | "COMPATIBLE";
export type RepositoryErrorCode =
  | "INVALID_ARGUMENT" | "INVALID_CURSOR" | "NOT_FOUND" | "RELEASE_NOT_FOUND"
  | "VISUAL_REGISTRY_NOT_FOUND" | "RELEASE_VERSION_MISMATCH" | "INTEGRITY_FAILURE"
  | "UNREGISTERED_RELATION" | "UNAVAILABLE";

export interface ResearchReleaseRef {
  apiVersion: typeof API_VERSION;
  researchReleaseId: string;
  researchManifestSha256: string;
  schemaVersion: "archive-research-release/v1";
}

export interface VisualRegistryRef {
  visualRegistryVersion: string;
  visualRegistrySha256: string;
  schemaVersion: "archive-visual-registry/v1";
}

export interface ArchiveVersionRef {
  research: ResearchReleaseRef;
  visual: VisualRegistryRef | null;
  visualState: VisualState;
  visualReasonCodes: readonly string[];
  takedownOverlaySha256: string | null;
}

export type ResearchReleaseSelector =
  | { researchReleaseId: string; researchManifestSha256: string }
  | { alias: "current" };
export type VisualRegistrySelector =
  | { visualRegistryVersion: string; visualRegistrySha256: string }
  | { alias: "current" };
export interface ReadOptions { signal?: AbortSignal }
export interface PageRequest { first?: number; after?: string }
export interface Page<T> {
  nodes: readonly T[];
  pageInfo: { hasNextPage: boolean; nextCursor: string | null; totalExact?: number };
}
export type RepoResult<T> =
  | { ok: true; data: T; version: ArchiveVersionRef }
  | { ok: false; error: { code: RepositoryErrorCode; message: string; retryable: boolean } };

export interface ArchiveOverview { objectCount: number; folderCount: number; traceEligibleObjectCount: number; positiveVisualRightsCount: number }
export interface FolderTypeSummary { type: string; label: string; folderCount: number }
export interface FolderSummary { id: string; type: string; slug: string; title: string; scopeNote: string; memberCount: number }
export interface FolderDetail extends FolderSummary { relatedFolders: readonly FolderSummary[] }
export interface SurfaceSummary {
  surfaceId: string; title: string; creditedLabels: readonly string[]; displayDate: string;
  year: number | null; placeLabel: string; mediumLabel: string; typeLabel: string;
  sourceLabel: string; publicationLayer: "active" | "review" | "auxiliary";
  deliveryState: DeliveryState;
}
export interface SurfaceDetail extends SurfaceSummary {
  citation: { label: string; href: string } | null;
  folderIds: readonly string[];
  description: string | null;
}
export interface SearchHit { kind: "archive"; route: string; highlight: string; surface: SurfaceSummary }
export interface TraceAtlas { namedUnits: readonly { id: string; label: string; totalExact: number }[]; totalExact: 0; message: string }
export interface TraceObjectSummary { objectId: string; layer: "active" | "review" | "auxiliary"; corpusVersion: string; title: string }
export interface TraceGraph { objectId: string; nodes: readonly never[]; edges: readonly never[] }
export interface RelationTypeDefinition { id: string; label: string; family: string; evidencePolicy: string }
export interface SemanticRelation { id: string }
export interface ResearchClaim { id: string }
export interface ResearchCorpus { version: string; totalExact: number }
export interface FolderQuery { type?: string }
export interface ArchiveSearchQuery { q: string; scope?: "archive" | "trace" | "relation" | "all"; sort?: "title" }
export interface TraceObjectQuery { layer?: "active" | "review" | "auxiliary" }
