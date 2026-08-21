# v49 Read API catalog

This catalog describes the catch-all App Router route in `frontend/src/app/api/v1/[...path]/route.ts` and its server-only controller in `frontend/src/lib/read-platform/server/read-api-controller.ts` at the v49 API-contract closure tree. It does not add prospective endpoints from `READ_API_V1.md`. There are **18 actual public GET resource templates**. Every template also accepts HEAD and OPTIONS through the same handler boundary; POST, PUT, PATCH, and DELETE return 405 with `Allow: GET, HEAD, OPTIONS` and perform no database query.

All successful database-backed responses are release-pinned envelopes, use `Cache-Control: no-store`, and are read through `gda_v49_phase2a_api_reader`. Exact release requests carry `Archive-Research-Manifest-Sha256`; `current` resolves the public pointer through `api_v1.current_version_status`. The database adapter reads only `api_v1.sealed_research_release_descriptor` and `api_v1.sealed_surface`.

| Endpoint | Method | Handler / repository call | Parameters | Response | DB source | Role | Status codes | Pagination | Tests |
|---|---|---|---|---|---|---|---|---|---|
| `/api/v1/visual-registries/current` | GET/HEAD/OPTIONS | `dispatchReadApiRequest` (fixed fail-closed response) | none | visual registry unavailable problem | none | none | 404, 405 | none | `visual-registry-current` |
| `/api/v1/releases/{release}` | GET/HEAD/OPTIONS | `provider.open`; release metadata serializer | path `release`; exact pairs use manifest header | version envelope with `schemaVersion` | current status + sealed descriptor | API reader | 200, 404, 405, 503 | none | `current-release` |
| `/api/v1/releases/{release}/manifest` | GET/HEAD/OPTIONS | `provider.open`; release metadata serializer | path `release`; manifest header | same version envelope | current status + sealed descriptor | API reader | 200, 404, 405, 503 | none | `release-manifest` |
| `/api/v1/releases/{release}/archive/overview` | GET/HEAD/OPTIONS | `getOverview` | release pair | object/folder/TRACE/positive-rights counts | sealed descriptor | API reader | 200, 404, 405, 503 | none | `archive-overview` |
| `/api/v1/releases/{release}/folder-types` | GET/HEAD/OPTIONS | `listFolderTypes` | release pair | empty `FolderTypeSummary[]` for this release | sealed descriptor to bind release; no candidate read | API reader | 200, 404, 405, 503 | none | `folder-types` |
| `/api/v1/releases/{release}/folders` | GET/HEAD/OPTIONS | `listFolders` → `pageByKey` | `type?`, `first?`, `after?` | empty `Page<FolderSummary>` for this release | sealed descriptor; no candidate read | API reader | 200, 400, 404, 409, 405, 503 | keyset; default 50, max 100 | `folders` |
| `/api/v1/releases/{release}/folders/{id}/surfaces` | GET/HEAD/OPTIONS | `listFolderMembers` | folder `id`, `first?`, `after?` | not-found problem; no folder is published | sealed descriptor; no candidate read | API reader | 404, 405, 503 | parameters exist; resource is absent | `folder-members` |
| `/api/v1/releases/{release}/folders/{id}` | GET/HEAD/OPTIONS | `getFolder` | folder `id` | not-found problem | sealed descriptor; no candidate read | API reader | 404, 405, 503 | none | `folder-detail` |
| `/api/v1/releases/{release}/surfaces/{id}` | GET/HEAD/OPTIONS | `getSurface` | stable surface `id` | `SurfaceDetail` envelope | sealed surface exact pair | API reader | 200, 404, 405, 503 | none | `surface-detail`; held ID negative case |
| `/api/v1/releases/{release}/search` | GET/HEAD/OPTIONS | `search` → exact-pair query → `pageByKey` | `q` required; `scope?`; `first?`; `after?` | `Page<SearchHit>` | sealed surface exact pair | API reader | 200, 400, 404, 409, 405, 503 | keyset by title + NUL + stable ID; default 50, max 100 | full search edge matrix; 486-row exhaustive `Poster` reconciliation |
| `/api/v1/releases/{release}/trace/atlas` | GET/HEAD/OPTIONS | `getTraceAtlas` | release pair | zero-evidence `TraceAtlas` | sealed descriptor to bind release | API reader | 200, 404, 405, 503 | none | `trace-atlas` |
| `/api/v1/releases/{release}/trace/objects` | GET/HEAD/OPTIONS | `listTraceObjects` → `pageByKey` | `layer?`, `first?`, `after?` | empty `Page<TraceObjectSummary>` | sealed descriptor; no candidate read | API reader | 200, 400, 404, 409, 405, 503 | keyset; default 50, max 100 | `trace-objects` |
| `/api/v1/releases/{release}/trace/objects/{id}/neighborhood` | GET/HEAD/OPTIONS | `getTraceNeighborhood` | object `id` | not-found problem | sealed descriptor; accepted TRACE count is zero | API reader | 404, 405, 503 | none | `trace-neighborhood` |
| `/api/v1/releases/{release}/trace/relation-types` | GET/HEAD/OPTIONS | `listRelationTypes` | release pair | empty `RelationTypeDefinition[]` | sealed descriptor; approved relation registry is empty | API reader | 200, 404, 405, 503 | none | `relation-types` |
| `/api/v1/releases/{release}/trace/relation-types/{id}` | GET/HEAD/OPTIONS | `getRelationType` | relation type `id` | not-found problem | sealed descriptor; no unapproved relation coercion | API reader | 404, 405, 503 | none | `relation-type` |
| `/api/v1/releases/{release}/relations/{id}` | GET/HEAD/OPTIONS | `getRelation` | relation `id` | not-found problem | sealed descriptor; release relation count is zero | API reader | 404, 405, 503 | none | `relation-detail` |
| `/api/v1/releases/{release}/claims/{id}` | GET/HEAD/OPTIONS | `getClaim` | claim `id` | not-found problem | sealed descriptor; claims are not in this public projection | API reader | 404, 405, 503 | none | `claim-detail` |
| `/api/v1/releases/{release}/corpora/{version}` | GET/HEAD/OPTIONS | `getCorpus` | corpus `version` | not-found problem | sealed descriptor; corpus detail is not in this public projection | API reader | 404, 405, 503 | none | `corpus-detail` |

## Shared request rules

- `{release}=current` is resolved only from the public current pointer. Any other release token is an exact-pair lookup and requires a matching `Archive-Research-Manifest-Sha256` header.
- `first` must be an integer from 1 through 100. The default is 50. `page` is not an implemented parameter and is ignored; clients must use `after`.
- Search trims `q`, requires 1–120 characters, lowercases only for cursor identity, and performs a parameterized, case-insensitive literal substring lookup. `%` and `_` are literal characters, not SQL wildcards. `scope` is one of `archive`, `trace`, `relation`, or `all`; trace/relation scopes are valid empty results in this zero-TRACE/zero-relation release.
- Keyset cursors bind release ID, manifest digest, resource, normalized filter, ordering, and terminal key. Malformed/filter-mismatched cursors are 400; cross-release cursors are 409.
- Repeated `q` parameters use the first value because the handler calls `URLSearchParams.get`.

## Shared response and boundary rules

- Successful GET responses are `application/json` envelopes containing the exact release ID and manifest in both body and response headers. HEAD has the same status/headers and no body. OPTIONS returns 204.
- Public surfaces are citation-only. The response structurally omits pixels, locators, raw payloads, internal UUIDs, candidate state, held rows, and rights internals.
- A valid empty collection is a 200 response. A missing singleton is 404. Adapter/query failures remain 503 and are never hidden as empty arrays.
- The exhaustive closure result is 18/18 templates passed, 0 undocumented templates, 0 HTTP 5xx, and 0 held/quarantined exposures. Raw response evidence is in `docs/audits/v49-api-read-contract-closure/raw/api/api-contract-results.json`.
