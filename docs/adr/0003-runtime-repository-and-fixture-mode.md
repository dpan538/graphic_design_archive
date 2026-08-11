# ADR 0003: Runtime repository and fixture mode

- Status: Accepted for the v49 architecture baseline; implementation pending
- Date: 2026-08-10
- Scope: frontend data boundary and prototype operation

## Context

The v48 frontend statically imports the complete public payload, performs synchronous scans, and allows Search and TRACE components to fetch compact assets and decode them independently. This makes UI modules responsible for release discovery, storage format, caching, integrity, and taxonomy fallbacks.

The v49 frontend needs one asynchronous read contract that works with a production API, immutable releases, and a small prototype fixture without changing page components.

## Decision

All archive reads pass through an `ArchiveRepository`. Repository DTOs are stable read models; they do not expose PostgreSQL table or column names and are not aliases for the current `Surface` UI type.

`surfaceId` in that contract is the sealed public/legacy route identifier, not the internal canonical `archive_object_id`. Identity aliases, merges, splits, and withdrawals are resolved from the sealed release projection rather than mutable canonical tables.

An instance is always opened against one exact research-release pair and may also select one exact compatible visual-registry pair. Resolving either `current` is a provider concern, occurs only once, and cannot substitute for compatibility validation. If no compatible registry is selected or available, the repository remains usable in an explicit research-only mode with no visual locator. An explicitly incompatible selector fails without fallback.

```ts
type ResearchReleaseSelector =
  | { researchReleaseId: string; researchManifestSha256: string }
  | { alias: "current" };

type VisualRegistrySelector =
  | { visualRegistryVersion: string; visualRegistrySha256: string }
  | { alias: "current" };

interface ResearchReleaseRef {
  apiVersion: "v1";
  researchReleaseId: string;
  researchManifestSha256: string;
  schemaVersion: "archive-research-release/v1";
}

interface VisualRegistryRef {
  visualRegistryVersion: string;
  visualRegistrySha256: string;
  schemaVersion: "archive-visual-registry/v1";
}

interface ArchiveVersionRef {
  research: ResearchReleaseRef;
  visual: VisualRegistryRef | null;
  visualState: "NOT_SELECTED" | "UNAVAILABLE" | "COMPATIBLE";
  visualReasonCodes: readonly string[];
  takedownOverlaySha256: string | null;
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
  | "VISUAL_REGISTRY_NOT_FOUND"
  | "RELEASE_VERSION_MISMATCH"
  | "INTEGRITY_FAILURE"
  | "UNREGISTERED_RELATION"
  | "UNAVAILABLE";

type RepoResult<T> =
  | { ok: true; data: T; version: ArchiveVersionRef }
  | {
      ok: false;
      error: {
        code: RepositoryErrorCode;
        message: string;
        retryable: boolean;
        researchReleaseId?: string;
        visualRegistryVersion?: string;
      };
    };

interface ReadOptions {
  signal?: AbortSignal;
}

interface ArchiveRepositoryProvider {
  open(
    selector: {
      research: ResearchReleaseSelector;
      visual?: VisualRegistrySelector | null;
    },
    options?: ReadOptions,
  ): Promise<RepoResult<ArchiveRepository>>;
}

interface ArchiveRepository {
  readonly version: ArchiveVersionRef;

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
  getRelation(relationId: string, options?: ReadOptions):
    Promise<RepoResult<SemanticRelation>>;
  getClaim(claimId: string, options?: ReadOptions):
    Promise<RepoResult<ResearchClaim>>;
  getCorpus(corpusVersion: string, options?: ReadOptions):
    Promise<RepoResult<ResearchCorpus>>;
}
```

The concrete implementations are:

1. `HttpArchiveRepository`: calls exact research-pair-pinned `/api/v1` GET endpoints and supplies an atomic exact visual pair only when selected.
2. `ImmutableReleaseRepository`: always validates the sealed research manifest and, when selected, validates the sealed visual manifest, declared compatibility, and its assets/shards.
3. `FixtureArchiveRepository`: reads a small, versioned, schema-valid fixture research release and optional compatible visual registry.

All implementations must pass the same repository contract suite, including error mapping, cursor behavior, exact pair pins, research-only registry absence, explicit mismatch, cancellation, integrity failure, held-pixel non-disclosure, positive field allowlists, and unknown-relation rejection.

## Composition and mode selection

One server-side composition root selects `api`, `release`, or `fixture` from an allowlisted configuration. Page and component code receives the interface and cannot inspect the selected mode.

- Production fails at startup if `fixture` is selected.
- Missing or invalid configuration fails closed; there is no implicit fixture fallback.
- Browser bundles contain no PostgreSQL driver or credentials.
- UI components contain no `/data/*.json` paths, shard filename construction, compact decoders, or manifest parsing.
- The repository validates schemas and cross-version compatibility, maps errors, deduplicates requests, handles `AbortSignal`, and caches composed data by both exact pairs or research-only data by the exact research pair plus its visual-unavailable reason.
- `NOT_FOUND`, `UNAVAILABLE`, and `INTEGRITY_FAILURE` remain distinct; none collapse to `undefined`.

`SurfaceDetail` may project the rights-safe presentation bundle needed by the existing visual pages, but it is built from an empty positive allowlist. `BLOCKED`, `CITATION_ONLY`, `LINK_ONLY`, and `SOURCE_VIEWER` structurally omit pixel, thumbnail and image-service fields; only `REMOTE_IMAGE` may expose the v1 allowlisted remote pixel. Rights observations/assessments, provider-policy versions/evaluations, delivery decision, endpoint health and takedown state remain distinct. Large memberships are separate paginated calls. `FolderDetail` does not embed thousands of surface IDs. TRACE summaries are projections of eligible semantic relations/claims for one named corpus and a discriminated union of `active`, `review`, and `auxiliary`; eligibility is returned only for a named sealed-release metric, not as a universal canonical boolean.

## Fixture mode

The fixture is a complete miniature research release with an optional compatible visual registry, not a slice loaded from the 87 MiB v48 payload. It has fixed IDs/hashes such as `fixture-research-v1` and `fixture-visual-v1`, valid manifests, and 10–50 hand-audited operational archive objects. It covers:

- image permitted, denied, and absent;
- active, review, and auxiliary TRACE states;
- folder pagination and an empty result;
- deterministic Search results and a declared research corpus;
- all four epistemic claim classes plus relation/claim/TRACE distinction;
- unknown/missing/conflicting/stale rights evidence and takedown precedence;
- not found, invalid cursor, research/visual mismatch, compatibility failure, corrupt hash, held-pixel leakage, and unknown relation failures.

The fixture uses the same async `RepoResult`, DTO schemas, cursors, relation/predicate registry, rights rules, and pair-bound compatibility checks as production adapters. It cannot be used to certify v48 parity or release counts.

## Prototype build policy

During repository/API prototype work, full `next build`, full static route generation, `next dev`, browser automation, data export, and full-project TypeScript are prohibited acceptance steps. Prototype validation is limited to fixture schema validation, repository contract tests, focused unit tests, and narrowly scoped type checks that do not compile the whole application.

A full production build belongs only to a later release-candidate lane after data and frontend contract gates have independently passed. It is never required to prove the architecture baseline.

## Consequences

Existing visual pages can be migrated incrementally behind one stable boundary. The initial work is larger than replacing a fetch call because DTO schemas, repository adapters, and explicit loading/error states must exist first. That cost prevents each component from inventing a new data protocol.

## Follow-up boundary

This ADR does not remove the existing imports or fetches and does not modify any visual page. Their removal is a future implementation gate; the current fail-open relation fallback remains an explicit cutover blocker until replaced and tested.
