# v49 Read interface map

## Boundary map

```text
HTTP GET/HEAD/OPTIONS /api/v1/*
  → frontend/src/app/api/v1/[...path]/route.ts
    → frontend/src/lib/read-platform/server/read-api-controller.ts
      → dispatchReadApiRequest(request, path, provider)
      → ArchiveRepositoryProvider.open(research selector)
        → PostgresArchiveRepositoryProvider
          → api_v1.current_version_status (current only)
          → api_v1.sealed_research_release_descriptor (exact pair)
      → resource(repo, tail, url)
        → one ArchiveRepository read method
          → api_v1.sealed_surface or a deterministic fail-closed result
          → pageByKey for keyset collections/search
```

The HTTP route is server-only. `PostgresArchiveRepository` imports `server-only`, receives a parameterized `PostgresReader`, and owns no pool or database URL. The browser-facing `HttpArchiveRepositoryProvider` can call the HTTP API but cannot import or instantiate the PostgreSQL adapter. Existing server-rendered pages call `openCurrentReadRepository`, which opens the same `ArchiveRepository` abstraction. No browser code connects to PostgreSQL.

## Route/controller layer

| Exported symbol | File | Signature / role | Direct callers |
|---|---|---|---|
| `dispatchReadApiRequest` | `frontend/src/lib/read-platform/server/read-api-controller.ts` | `(Request, readonly string[], ArchiveRepositoryProvider?) => Promise<Response>`; method gate, selector, serializer, error mapping | Next handlers; exhaustive integration harness; runtime acceptance harness |
| `GET`, `HEAD`, `OPTIONS` | `frontend/src/app/api/v1/[...path]/route.ts` | App Router read handlers | Next.js App Router |
| `POST`, `PUT`, `PATCH`, `DELETE` | route file → controller response helper | fixed 405 negative-method handlers | Next.js App Router; 72-case negative matrix |
| `getArchiveRepositoryProvider` | `frontend/src/lib/read-platform/server/provider.ts` | server-only composition root; fixture is explicitly non-production | route handler; `openCurrentReadRepository` |

`resource` is a non-exported controller dispatch function. It is not a public API or reusable client interface.

## Data-access interfaces

`ArchiveRepository` contains 15 read methods. `ArchiveRepositoryProvider.open` and the named `pageByKey` helper make **17 internal read-interface operations** in the closure inventory.

| Interface / exported function | Signature summary | HTTP caller | PostgreSQL source / behavior |
|---|---|---|---|
| `ArchiveRepositoryProvider.open` | exact release pair or `current` selector → repository | every release route | current status + sealed descriptor |
| `getOverview` | `ReadOptions? → ArchiveOverview` | archive overview | sealed descriptor counts |
| `listFolderTypes` | `ReadOptions? → FolderTypeSummary[]` | folder types | valid empty, release pinned |
| `listFolders` | `FolderQuery & PageRequest → Page<FolderSummary>` | folders | valid empty through `pageByKey` |
| `getFolder` | ID or type/slug → `FolderDetail` | folder detail | deterministic 404 |
| `listFolderMembers` | folder ID + page → `Page<SurfaceSummary>` | folder members | deterministic 404; no published folders |
| `getSurface` | stable surface ID → `SurfaceDetail` | surface detail | exact-pair sealed surface |
| `search` | `ArchiveSearchQuery & PageRequest → Page<SearchHit>` | search | parameterized literal substring over sealed surface; `pageByKey` |
| `getTraceAtlas` | `ReadOptions? → TraceAtlas` | TRACE atlas | zero-evidence object |
| `listTraceObjects` | trace filter + page → page | TRACE objects | valid empty through `pageByKey` |
| `getTraceNeighborhood` | object ID → graph | TRACE neighborhood | deterministic 404 |
| `listRelationTypes` | `ReadOptions? → RelationTypeDefinition[]` | relation types | valid empty |
| `getRelationType` | relation type ID → definition | relation type detail | deterministic 404 |
| `getRelation` | relation ID → relation | relation detail | deterministic 404 |
| `getClaim` | claim ID → claim | claim detail | deterministic 404 |
| `getCorpus` | corpus version → corpus | corpus detail | deterministic 404 |
| `pageByKey<T>` | complete pinned result set + stable key + page/filter/order metadata → `RepoResult<Page<T>>` | folders, TRACE objects, search | in-memory stable keyset window; signed-by-content cursor fields (not cryptographic) |

The interface types are declared in `frontend/src/lib/read-platform/repository.ts` and `types.ts`. Server implementations are `server/fixture.ts` and `server/postgres-repository.ts`; the HTTP client implementation is `http-repository.ts`.

## `pageByKey` module contract

- Definition and named export: `frontend/src/lib/read-platform/pagination.ts`.
- Production import: named import in `frontend/src/lib/read-platform/server/postgres-repository.ts`.
- Production calls: empty folders, empty TRACE objects, fail-closed trace/relation search, and database-backed archive search.
- Runtime type before fix: `undefined`; the symbol was imported but not exported.
- Runtime type after fix: `function`.
- Test: `frontend/scripts/verify-page-by-key-module-contract.mjs` loads the exact production import path, verifies the named runtime export, a known terminal key, and an unknown-terminal-key `INVALID_CURSOR` result.

## Callers and server/client separation

| Consumer | Interface | Boundary |
|---|---|---|
| catch-all `/api/v1` route | provider + all repository methods | server-only |
| `openCurrentReadRepository` | provider `open(current)` | server-only page loader |
| search and TRACE read views | `HttpArchiveRepositoryProvider` | client-side HTTP only; no database import |
| server-rendered folder/surface/search/TRACE pages | `ArchiveRepository` | server-only repository abstraction |
| contract/runtime scripts | injected fixture or PostgreSQL provider | test-only server process |

Legacy helpers in `frontend/src/lib/archive-data.ts` are UI fixture helpers, not public `/api/v1` endpoints and not part of the v49 Read API contract.

## Error, cache, version, and permission contract

- `RepoResult` carries either exact-version data or a typed error. The route maps invalid arguments/cursors to 400, not-found variants to 404, release-version mismatch to 409, and actual infrastructure/unavailable failures to 503.
- `Cache-Control: no-store` and `Vary: Archive-Research-Manifest-Sha256` are applied by the route.
- Exact response identity is repeated in `Archive-Research-Release-Id` and `Archive-Research-Manifest-Sha256` headers.
- Application SQL is parameterized and executed as `gda_v49_phase2a_api_reader`. Direct raw/core/research/release access, DML, and DDL are denied.
