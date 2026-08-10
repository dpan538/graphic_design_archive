# ADR 0003: Runtime repository and fixture mode

- Status: Accepted for the v49 architecture baseline; implementation pending
- Date: 2026-08-10
- Scope: frontend data boundary and prototype operation

## Context

The v48 frontend statically imports the complete public payload, performs synchronous scans, and allows Search and TRACE components to fetch compact assets and decode them independently. This makes UI modules responsible for release discovery, storage format, caching, integrity, and taxonomy fallbacks.

The v49 frontend needs one asynchronous read contract that works with a production API, immutable releases, and a small prototype fixture without changing page components.

## Decision

All archive reads pass through an `ArchiveRepository`. Repository DTOs are stable read models; they do not expose PostgreSQL table or column names and are not aliases for the current `Surface` UI type.

An instance is opened against one exact release. Resolving `current` is a provider concern and occurs only once.

```ts
type ReleaseSelector = { releaseId: string } | { alias: "current" };

interface ReleaseRef {
  apiVersion: "v1";
  releaseId: string;
  manifestSha256: string;
  schemaVersion: "archive-release/v1";
}

interface PageRequest {
  first?: number; // default 50, maximum 100
  after?: string;
}

interface Page<T> {
  nodes: readonly T[];
  pageInfo: {
    hasNextPage: boolean;
    nextCursor: string | null;
    totalExact?: number;
  };
}

type RepositoryErrorCode =
  | "INVALID_ARGUMENT"
  | "INVALID_CURSOR"
  | "NOT_FOUND"
  | "RELEASE_NOT_FOUND"
  | "RELEASE_VERSION_MISMATCH"
  | "INTEGRITY_FAILURE"
  | "UNREGISTERED_RELATION"
  | "UNAVAILABLE";

type RepoResult<T> =
  | { ok: true; data: T; release: ReleaseRef }
  | {
      ok: false;
      error: {
        code: RepositoryErrorCode;
        message: string;
        retryable: boolean;
        releaseId?: string;
      };
    };

interface ReadOptions {
  signal?: AbortSignal;
}

interface ArchiveRepositoryProvider {
  open(
    selector: ReleaseSelector,
    options?: ReadOptions,
  ): Promise<RepoResult<ArchiveRepository>>;
}

interface ArchiveRepository {
  readonly release: ReleaseRef;

  getOverview(options?: ReadOptions): Promise<RepoResult<ArchiveOverview>>;
  listFolderTypes(options?: ReadOptions):
    Promise<RepoResult<readonly FolderTypeSummary[]>>;
  listFolders(input: FolderQuery & PageRequest, options?: ReadOptions):
    Promise<RepoResult<Page<FolderSummary>>>;
  getFolder(ref: { id: string } | { type: string; slug: string },
    options?: ReadOptions): Promise<RepoResult<FolderDetail>>;
  listFolderMembers(folderId: string, page: PageRequest,
    options?: ReadOptions): Promise<RepoResult<Page<SurfaceSummary>>>;
  getSurface(surfaceId: string, options?: ReadOptions):
    Promise<RepoResult<SurfaceDetail>>;
  search(input: ArchiveSearchQuery & PageRequest, options?: ReadOptions):
    Promise<RepoResult<Page<SearchHit>>>;
  getTraceAtlas(options?: ReadOptions): Promise<RepoResult<TraceAtlas>>;
  listTraceObjects(input: TraceObjectQuery & PageRequest, options?: ReadOptions):
    Promise<RepoResult<Page<TraceObjectSummary>>>;
  getTraceNeighborhood(objectId: string, options?: ReadOptions):
    Promise<RepoResult<TraceGraph>>;
  listRelationTypes(options?: ReadOptions):
    Promise<RepoResult<readonly RelationTypeDefinition[]>>;
  getRelationType(id: string, options?: ReadOptions):
    Promise<RepoResult<RelationTypeDefinition>>;
}
```

The concrete implementations are:

1. `HttpArchiveRepository`: calls only release-pinned `/api/v1` GET endpoints.
2. `ImmutableReleaseRepository`: validates and reads a sealed manifest and its assets/shards.
3. `FixtureArchiveRepository`: reads a small, versioned, schema-valid fixture release.

All implementations must pass the same repository contract suite, including error mapping, cursor behavior, release pinning, cancellation, integrity failure, and unknown-relation rejection.

## Composition and mode selection

One server-side composition root selects `api`, `release`, or `fixture` from an allowlisted configuration. Page and component code receives the interface and cannot inspect the selected mode.

- Production fails at startup if `fixture` is selected.
- Missing or invalid configuration fails closed; there is no implicit fixture fallback.
- Browser bundles contain no PostgreSQL driver or credentials.
- UI components contain no `/data/*.json` paths, shard filename construction, compact decoders, or manifest parsing.
- The repository validates schemas, maps errors, deduplicates requests, handles `AbortSignal`, and caches by exact release.
- `NOT_FOUND`, `UNAVAILABLE`, and `INTEGRITY_FAILURE` remain distinct; none collapse to `undefined`.

`SurfaceDetail` may project the rights-safe presentation bundle needed by the existing visual pages, but large memberships are separate paginated calls. `FolderDetail` does not embed thousands of surface IDs. TRACE summaries are a discriminated union of `active`, `review`, and `auxiliary`, and always expose `countEligible`.

## Fixture mode

The fixture is a complete miniature release, not a slice loaded from the 87 MiB v48 payload. It has a fixed release ID such as `fixture-v1`, a valid manifest, and 10–50 hand-audited objects. It covers:

- image permitted, denied, and absent;
- active, review, and auxiliary TRACE states;
- folder pagination and an empty result;
- deterministic Search results;
- not found, invalid cursor, release mismatch, corrupt hash, and unknown relation failures.

The fixture uses the same async `RepoResult`, DTO schemas, cursors, and relation registry as production adapters. It cannot be used to certify v48 parity or release counts.

## Prototype build policy

During repository/API prototype work, full `next build`, full static route generation, `next dev`, browser automation, data export, and full-project TypeScript are prohibited acceptance steps. Prototype validation is limited to fixture schema validation, repository contract tests, focused unit tests, and narrowly scoped type checks that do not compile the whole application.

A full production build belongs only to a later release-candidate lane after data and frontend contract gates have independently passed. It is never required to prove the architecture baseline.

## Consequences

Existing visual pages can be migrated incrementally behind one stable boundary. The initial work is larger than replacing a fetch call because DTO schemas, repository adapters, and explicit loading/error states must exist first. That cost prevents each component from inventing a new data protocol.

## Follow-up boundary

This ADR does not remove the existing imports or fetches and does not modify any visual page. Their removal is a future implementation gate; the current fail-open relation fallback remains an explicit cutover blocker until replaced and tested.
